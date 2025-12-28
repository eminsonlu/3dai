"""Route optimization endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from app.models import get_db
from app.schemas.optimization import RouteRequest, RouteResponse
from app.services.route_optimizer import RouteOptimizer, Container, DEPOT_LOCATION

router = APIRouter(prefix="/api/optimize", tags=["optimization"])


@router.post("/route", response_model=RouteResponse)
async def optimize_route(request: RouteRequest, db: Session = Depends(get_db)):
    """
    Optimize collection route for a neighborhood.

    Args:
        request: Route optimization request with neighborhood and parameters
        db: Database session

    Returns:
        Optimized route with stops and statistics

    Raises:
        HTTPException: If neighborhood not found or optimization fails
    """
    # 1. Get neighborhood info
    neighborhood_query = text("""
        SELECT
            neighborhood_id,
            neighborhood_name,
            garbage_truck_type
        FROM neighborhoods
        WHERE neighborhood_name = :name
        LIMIT 1
    """)

    result = db.execute(neighborhood_query, {"name": request.neighborhood})
    neighborhood_row = result.fetchone()

    if not neighborhood_row:
        raise HTTPException(
            status_code=404,
            detail=f"Neighborhood '{request.neighborhood}' not found"
        )

    neighborhood_id = neighborhood_row.neighborhood_id
    vehicle_type = neighborhood_row.garbage_truck_type or "Large Garbage Truck"

    # 2. Get containers for this neighborhood
    containers_query = text("""
        SELECT
            container_id,
            latitude,
            longitude,
            vehicle_type
        FROM containers
        WHERE neighborhood_id = :neighborhood_id
          AND vehicle_type = :vehicle_type
        ORDER BY container_id
    """)

    result = db.execute(containers_query, {
        "neighborhood_id": neighborhood_id,
        "vehicle_type": vehicle_type
    })

    container_rows = result.fetchall()

    if not container_rows:
        raise HTTPException(
            status_code=404,
            detail=f"No containers found for neighborhood '{request.neighborhood}'"
        )

    # 3. Convert to Container objects
    containers = [
        Container(
            container_id=row.container_id,
            latitude=row.latitude,
            longitude=row.longitude,
            vehicle_type=row.vehicle_type
        )
        for row in container_rows
    ]

    # 4. Run optimization
    try:
        optimizer = RouteOptimizer()
        route_result = optimizer.optimize_route(
            neighborhood=request.neighborhood,
            containers=containers,
            vehicle_capacity=40  # Default capacity
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Route optimization failed: {str(e)}"
        )

    # 5. Build schedule (simplified for now)
    schedule = [{
        "day": "Monday",
        "containers": len(route_result.stops),
        "distance_km": route_result.total_distance_km
    }]

    # 6. Build GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    # Add depot as first feature
    geojson["features"].append({
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [DEPOT_LOCATION["lon"], DEPOT_LOCATION["lat"]]
        },
        "properties": {
            "type": "depot",
            "name": "Depot"
        }
    })

    # Add container stops
    for stop in route_result.stops:
        geojson["features"].append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [stop.longitude, stop.latitude]
            },
            "properties": {
                "type": "container",
                "container_id": stop.container_id,
                "order": stop.order,
                "distance_from_previous_km": round(stop.distance_from_previous, 3),
                "cumulative_distance_km": round(stop.cumulative_distance, 3)
            }
        })

    # Add route line if we have stops
    if route_result.stops:
        # Build route geometry from OSRM segments
        route_coordinates = []

        # Collect all geometry segments
        for stop in route_result.stops:
            if stop.geometry_to_here:
                # Add the OSRM route geometry for this segment
                route_coordinates.extend(stop.geometry_to_here)
            else:
                # Fallback: add straight line if no geometry
                if not route_coordinates:
                    route_coordinates.append([DEPOT_LOCATION["lon"], DEPOT_LOCATION["lat"]])
                route_coordinates.append([stop.longitude, stop.latitude])

        # Add return to depot (straight line for now)
        if route_result.stops:
            last_stop = route_result.stops[-1]
            if route_coordinates:
                # Only add if not already at this position
                last_coord = route_coordinates[-1]
                if last_coord != [last_stop.longitude, last_stop.latitude]:
                    route_coordinates.append([last_stop.longitude, last_stop.latitude])
            route_coordinates.append([DEPOT_LOCATION["lon"], DEPOT_LOCATION["lat"]])

        geojson["features"].append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": route_coordinates
            },
            "properties": {
                "type": "route",
                "total_distance_km": round(route_result.total_distance_km, 3),
                "total_containers": route_result.total_containers
            }
        })

    return RouteResponse(
        neighborhood=request.neighborhood,
        week_start_date=request.week_start_date,
        vehicle_type=vehicle_type,
        vehicle_id=f"{vehicle_type.replace(' ', '_').lower()}_001",
        schedule=schedule,
        geojson=geojson
    )


@router.get("/health")
async def check_osrm_health():
    """
    Check if OSRM service is available.

    Returns:
        Health status of OSRM service
    """
    import requests

    try:
        # OSRM doesn't have /health, so test with a simple route query
        # Test route: Depot to nearby point
        test_url = "http://localhost:5001/route/v1/driving/28.9375,40.1965;28.9376,40.1966?overview=false"
        response = requests.get(test_url, timeout=2)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "Ok":
                return {"status": "ok", "osrm": "available"}

        return {"status": "degraded", "osrm": "unavailable"}
    except Exception as e:
        return {"status": "error", "osrm": "unavailable", "error": str(e)}
