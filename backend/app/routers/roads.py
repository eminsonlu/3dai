"""Road analytics endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from app.models import get_db
from app.schemas.route import RoadUsage, NeighborhoodRoadStats

router = APIRouter(prefix="/api/roads", tags=["roads"])


@router.get("/most-used", response_model=List[RoadUsage])
async def get_most_used_roads(limit: int = 20, db: Session = Depends(get_db)):
    """Get most used roads.

    Args:
        limit: Maximum number of roads to return
        db: Database session

    Returns:
        List of most used roads with usage statistics
    """
    query = text("""
        SELECT
            road_id,
            road_name,
            neighborhood,
            times_used,
            length_m,
            last_visited
        FROM roads
        WHERE times_used > 0
        ORDER BY times_used DESC
        LIMIT :limit
    """)

    result = db.execute(query, {"limit": limit})
    rows = result.fetchall()

    return [
        RoadUsage(
            road_id=row.road_id,
            road_name=row.road_name,
            neighborhood=row.neighborhood,
            times_used=row.times_used,
            length_m=float(row.length_m) if row.length_m else 0,
            last_visited=row.last_visited.isoformat() if row.last_visited else None,
        )
        for row in rows
    ]


@router.get("/usage-by-neighborhood", response_model=List[NeighborhoodRoadStats])
async def get_road_usage_by_neighborhood(db: Session = Depends(get_db)):
    """Get road usage statistics by neighborhood.

    Args:
        db: Database session

    Returns:
        List of road usage statistics grouped by neighborhood
    """
    query = text("""
        SELECT
            neighborhood,
            COUNT(*) as total_roads,
            SUM(CASE WHEN times_used > 0 THEN 1 ELSE 0 END) as roads_used,
            SUM(times_used) as total_visits,
            ROUND(AVG(CASE WHEN times_used > 0 THEN times_used ELSE NULL END)::numeric, 1) as avg_visits,
            ROUND((SUM(length_m) / 1000.0)::numeric, 2) as total_length_km,
            ROUND(
                ((SUM(CASE WHEN times_used > 0 THEN 1 ELSE 0 END)::float / COUNT(*)::float) * 100)::numeric,
                1
            ) as coverage_percent
        FROM roads
        GROUP BY neighborhood
        ORDER BY total_visits DESC
    """)

    result = db.execute(query)
    rows = result.fetchall()

    return [
        NeighborhoodRoadStats(
            neighborhood=row.neighborhood,
            total_roads=row.total_roads,
            roads_used=row.roads_used,
            total_visits=row.total_visits,
            avg_visits=float(row.avg_visits) if row.avg_visits else 0,
            total_length_km=float(row.total_length_km) if row.total_length_km else 0,
            coverage_percent=float(row.coverage_percent) if row.coverage_percent else 0,
        )
        for row in rows
    ]


@router.get("/neighborhood/{neighborhood}", response_model=List[RoadUsage])
async def get_neighborhood_roads(neighborhood: str, db: Session = Depends(get_db)):
    """Get most used roads in a neighborhood.

    Args:
        neighborhood: Neighborhood name
        db: Database session

    Returns:
        List of most used roads in the specified neighborhood
    """
    query = text("""
        SELECT
            road_id,
            road_name,
            times_used,
            length_m,
            last_visited
        FROM roads
        WHERE neighborhood = :neighborhood
            AND times_used > 0
        ORDER BY times_used DESC
        LIMIT 20
    """)

    result = db.execute(query, {"neighborhood": neighborhood})
    rows = result.fetchall()

    return [
        RoadUsage(
            road_id=row.road_id,
            road_name=row.road_name,
            neighborhood=None,  # Not needed in this context
            times_used=row.times_used,
            length_m=float(row.length_m) if row.length_m else 0,
            last_visited=row.last_visited.isoformat() if row.last_visited else None,
        )
        for row in rows
    ]
