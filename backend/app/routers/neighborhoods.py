"""Neighborhoods endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import get_db
from app.schemas.optimization import NeighborhoodList

router = APIRouter(prefix="/api", tags=["neighborhoods"])


@router.get("/neighborhoods", response_model=NeighborhoodList)
async def get_neighborhoods(db: Session = Depends(get_db)):
    """Get list of available neighborhoods from database.

    Args:
        db: Database session

    Returns:
        List of available neighborhood names

    Raises:
        HTTPException: If neighborhoods cannot be loaded
    """
    try:
        query = text("""
            SELECT DISTINCT neighborhood_name
            FROM neighborhoods
            WHERE neighborhood_name IS NOT NULL
            ORDER BY neighborhood_name
        """)

        result = db.execute(query)
        rows = result.fetchall()

        neighborhoods = [row.neighborhood_name for row in rows]

        return NeighborhoodList(neighborhoods=neighborhoods)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load neighborhoods: {str(e)}"
        )
