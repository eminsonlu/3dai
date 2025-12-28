"""Historical routes endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import get_db
from app.schemas.geojson import GeoJSONFeature, GeoJSONFeatureCollection
from app.schemas.route import RouteStats

router = APIRouter(prefix="/api", tags=["routes"])


@router.get("/routes", response_model=GeoJSONFeatureCollection)
async def get_routes(db: Session = Depends(get_db)):
    """Get all routes as GeoJSON.

    Args:
        db: Database session

    Returns:
        GeoJSON FeatureCollection of all routes
    """
    query = text("""
        SELECT
            r.route_id,
            r.vehicle_id,
            r.route_date,
            r.start_time,
            r.end_time,
            r.duration_minutes,
            r.total_distance_km,
            ST_AsGeoJSON(r.route_line) as geometry,
            v.vehicle_name,
            v.vehicle_type
        FROM routes r
        LEFT JOIN vehicles v ON r.vehicle_id = v.vehicle_id
        ORDER BY r.start_time DESC
    """)

    result = db.execute(query)
    rows = result.fetchall()

    features = []
    for row in rows:
        if row.geometry:
            feature = GeoJSONFeature(
                type="Feature",
                geometry=eval(row.geometry),  # Parse GeoJSON string
                properties={
                    "route_id": row.route_id,
                    "vehicle_id": row.vehicle_id,
                    "vehicle_name": row.vehicle_name,
                    "vehicle_type": row.vehicle_type,
                    "route_date": row.route_date.isoformat(),
                    "start_time": row.start_time.isoformat(),
                    "end_time": row.end_time.isoformat(),
                    "duration_minutes": row.duration_minutes,
                    "total_distance_km": float(row.total_distance_km) if row.total_distance_km else 0,
                }
            )
            features.append(feature)

    return GeoJSONFeatureCollection(features=features)


@router.get("/routes/stats", response_model=RouteStats)
async def get_route_stats(db: Session = Depends(get_db)):
    """Get route statistics.

    Args:
        db: Database session

    Returns:
        Route statistics including total routes, vehicles, days, distance, and duration
    """
    query = text("""
        SELECT
            COUNT(*) as total_routes,
            COUNT(DISTINCT vehicle_id) as total_vehicles,
            COUNT(DISTINCT route_date) as total_days,
            SUM(total_distance_km) as total_distance,
            AVG(duration_minutes) as avg_duration
        FROM routes
    """)

    result = db.execute(query)
    row = result.fetchone()

    return RouteStats(
        total_routes=row.total_routes,
        total_vehicles=row.total_vehicles,
        total_days=row.total_days,
        total_distance_km=float(row.total_distance) if row.total_distance else 0,
        avg_duration_minutes=int(row.avg_duration) if row.avg_duration else 0,
    )
