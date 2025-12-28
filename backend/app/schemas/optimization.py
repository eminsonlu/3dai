"""Pydantic schemas for route optimization."""

from pydantic import BaseModel, Field
from typing import List


class RouteRequest(BaseModel):
    """Request model for route optimization."""
    neighborhood: str = Field(..., description="Neighborhood name")
    week_start_date: str = Field(..., description="Week start date (YYYY-MM-DD)")
    quick_mode: bool = Field(default=True, description="Use quick mode for faster results (5 iterations, 20 containers)")


class ScheduleDay(BaseModel):
    """Collection schedule day model."""
    date: str
    day_name: str
    start_hour: int
    end_hour: int
    start_time: str
    end_time: str


class RouteResponse(BaseModel):
    """Response model for optimized route."""
    neighborhood: str
    week_start_date: str
    vehicle_type: str
    vehicle_id: str
    schedule: List[dict]
    geojson: dict


class NeighborhoodList(BaseModel):
    """List of neighborhoods response."""
    neighborhoods: List[str]
