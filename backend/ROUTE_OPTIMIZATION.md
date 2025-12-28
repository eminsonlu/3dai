# Route Optimization System

## Overview

This system optimizes trash collection routes using:
- **Nearest Neighbor Algorithm** (Greedy approach)
- **OSRM (Open Source Routing Machine)** for real-world driving distances
- **Vehicle capacity constraints**
- **Multiple trip support**

## Architecture

```
┌─────────────────┐
│   Frontend      │
│   (React)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│   FastAPI       │─────▶│   PostgreSQL    │
│   Backend       │      │   + PostGIS     │
└────────┬────────┘      └─────────────────┘
         │
         ▼
┌─────────────────┐
│   OSRM Server   │
│   (Port 5001)   │
└─────────────────┘
```

## Setup Instructions

### 1. Start Services

```bash
# Navigate to routes directory
cd /Users/eminsonlu/Projects/trash-collection/routes

# Start Docker services
docker-compose up -d
```

**Note**: The first time you run this, OSRM will:
1. Extract the Turkey OSM data (~5-10 minutes)
2. Contract the graph (~10-15 minutes)
3. Start the routing server

You can monitor progress with:
```bash
docker-compose logs -f osrm
```

### 2. Verify Services

Check PostgreSQL:
```bash
docker-compose ps postgres
# Should show "Up"
```

Check OSRM:
```bash
curl http://localhost:5001/health
# Should return: {"status":"Ok"}
```

Check API:
```bash
curl http://localhost:8000/api/optimize/health
# Should return: {"status":"ok","osrm":"available"}
```

### 3. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
# or using uv:
uv sync
```

## API Usage

### Optimize Route for Neighborhood

**Endpoint**: `POST /api/optimize/route`

**Request**:
```json
{
  "neighborhood": "19 MAYIS MAHALLESİ",
  "week_start_date": "2025-01-06",
  "quick_mode": true
}
```

**Response**:
```json
{
  "neighborhood": "19 MAYIS MAHALLESİ",
  "week_start_date": "2025-01-06",
  "vehicle_type": "Large Garbage Truck",
  "vehicle_id": "large_garbage_truck_001",
  "schedule": [
    {
      "day": "Monday",
      "containers": 40,
      "distance_km": 12.5
    }
  ],
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Point",
          "coordinates": [28.93751, 40.19654]
        },
        "properties": {
          "type": "depot",
          "name": "Depot"
        }
      },
      {
        "type": "Feature",
        "geometry": {
          "type": "Point",
          "coordinates": [28.9385, 40.1975]
        },
        "properties": {
          "type": "container",
          "container_id": 123,
          "order": 1,
          "distance_from_previous_km": 0.85,
          "cumulative_distance_km": 0.85
        }
      }
    ]
  }
}
```

### Example Using cURL

```bash
curl -X POST http://localhost:8000/api/optimize/route \
  -H "Content-Type: application/json" \
  -d '{
    "neighborhood": "19 MAYIS MAHALLESİ",
    "week_start_date": "2025-01-06"
  }'
```

### Example Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/optimize/route",
    json={
        "neighborhood": "19 MAYIS MAHALLESİ",
        "week_start_date": "2025-01-06",
        "quick_mode": True
    }
)

route = response.json()
print(f"Total distance: {route['geojson']['features'][-1]['properties']['total_distance_km']} km")
```

## Algorithm Details

### Nearest Neighbor (Greedy)

The algorithm works as follows:

1. **Start at depot**: `(40.19654, 28.93751)`
2. **Find nearest container**: Calculate distance to all unvisited containers
3. **Visit it**: Add to route, mark as visited
4. **Repeat**: From current location, find next nearest unvisited container
5. **Return to depot**: After visiting all containers

### Vehicle Capacity

- Default capacity: **40 containers** per trip
- If neighborhood has more containers:
  - `requires_multiple_trips: true`
  - `trip_count: Math.ceil(containers / capacity)`
  - Currently optimizes first trip only (can be extended)

### Distance Calculation

- **Primary**: OSRM driving distance (meters → km)
- **Fallback**: Haversine formula if OSRM unavailable
- **Caching**: Consider implementing for repeated queries

## Database Schema

### Containers Table
```sql
SELECT
    container_id,
    latitude,
    longitude,
    vehicle_type,
    neighborhood_id
FROM containers
WHERE neighborhood_id = X
  AND vehicle_type = 'Large Garbage Truck';
```

### Neighborhoods Table
```sql
SELECT
    neighborhood_id,
    neighborhood_name,
    garbage_truck_type,
    total_containers
FROM neighborhoods
WHERE neighborhood_name = 'X';
```

## Performance Considerations

### OSRM Performance
- Single distance query: ~10-50ms
- For 55 containers: ~55 queries per iteration
- Total queries: ~1,500 (55 × 54 / 2)
- Estimated time: **15-45 seconds**

### Optimization Ideas

1. **Batch Distance Requests**:
   - Use OSRM Table API instead of Route API
   - Single request for distance matrix
   - Reduces from 1,500 to 1 request

2. **Caching**:
   - Cache distance calculations
   - Reuse for similar neighborhoods

3. **Better Algorithms**:
   - 2-opt improvement
   - Genetic algorithms
   - Simulated annealing

## Example Workflow

### Complete Optimization Flow

```bash
# 1. Get available neighborhoods
curl http://localhost:8000/api/neighborhoods

# 2. Optimize route for selected neighborhood
curl -X POST http://localhost:8000/api/optimize/route \
  -H "Content-Type: application/json" \
  -d '{
    "neighborhood": "19 MAYIS MAHALLESİ",
    "week_start_date": "2025-01-06"
  }' > route.json

# 3. Visualize on map (GeoJSON in response)
# Use the geojson field in route.json with your frontend
```

## Troubleshooting

### OSRM Not Available

```bash
# Check OSRM logs
docker-compose logs osrm

# Restart OSRM
docker-compose restart osrm

# Check health
curl http://localhost:5000/health
```

### No Containers Found

```sql
-- Check containers in database
SELECT
    n.neighborhood_name,
    COUNT(c.container_id) as container_count,
    c.vehicle_type
FROM neighborhoods n
LEFT JOIN containers c ON n.neighborhood_id = c.neighborhood_id
GROUP BY n.neighborhood_name, c.vehicle_type;
```

### Slow Performance

- Use `quick_mode: true` for testing
- Implement distance matrix caching
- Consider pre-computing routes offline

## Next Steps

1. **Multiple Trips**: Extend algorithm to handle multiple trips
2. **Time Windows**: Add collection time constraints
3. **Traffic**: Use OSRM traffic data
4. **Better Algorithms**: Implement 2-opt or OR-Tools
5. **Route Validation**: Verify routes are actually drivable
6. **Visualization**: Create interactive map view

## References

- [OSRM Documentation](http://project-osrm.org/)
- [Nearest Neighbor Algorithm](https://en.wikipedia.org/wiki/Nearest_neighbour_algorithm)
- [Vehicle Routing Problem](https://en.wikipedia.org/wiki/Vehicle_routing_problem)
