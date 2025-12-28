"""Pydantic schemas for historical routes."""

from pydantic import BaseModel
from typing import Optional


class RouteStats(BaseModel):
    """Route statistics response model."""
    total_routes: int
    total_vehicles: int
    total_days: int
    total_distance_km: float
    avg_duration_minutes: int


class RoadUsage(BaseModel):
    """Road usage response model."""
    road_id: int
    road_name: str
    neighborhood: Optional[str] = None
    times_used: int
    length_m: float
    last_visited: Optional[str] = None


class NeighborhoodRoadStats(BaseModel):
    """Neighborhood road statistics response model."""
    neighborhood: str
    total_roads: int
    roads_used: int
    total_visits: int
    avg_visits: float
    total_length_km: float
    coverage_percent: float
