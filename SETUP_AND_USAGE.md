# Trash Collection Route Optimization - Setup & Usage Guide

## Problem Fixed

### Issue
The `/api/neighborhoods` endpoint was returning a 500 error:
```
Failed to load neighborhoods: Failed to load neighborhood rotations data:
[Errno 2] No such file or directory: '...neighbor_days_rotations.csv'
```

### Solution
**Removed CSV dependency** - Updated the neighborhoods endpoint to query directly from the PostgreSQL database instead of loading from CSV files. This is:
- ✅ **Faster** - No file I/O overhead
- ✅ **More reliable** - Data already in database from setup scripts
- ✅ **Cleaner** - Single source of truth
- ✅ **Scalable** - Database queries are optimized

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                    (React + Leaflet)                         │
│                  http://localhost:5173                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
│                   http://localhost:8000                      │
│                                                              │
│  Routes:                                                     │
│  • GET  /api/neighborhoods     - List all neighborhoods     │
│  • POST /api/optimize/route    - Optimize collection route  │
│  • GET  /api/optimize/health   - Check OSRM status          │
│  • GET  /api/routes            - Historical routes          │
│  • GET  /api/routes/stats      - Route statistics           │
└────────────┬─────────────────────┬──────────────────────────┘
             │                     │
             ▼                     ▼
┌────────────────────┐   ┌──────────────────────┐
│   PostgreSQL       │   │   OSRM Server        │
│   + PostGIS        │   │   (Routing Engine)   │
│   Port 5432        │   │   Port 5001          │
└────────────────────┘   └──────────────────────┘
```

## Quick Start

### 1. Start Docker Services

```bash
cd /Users/eminsonlu/Projects/trash-collection/routes
docker-compose up -d
```

**First-time setup**: OSRM will process the Turkey OSM data (~15-25 minutes):
- Extracting: ~5-10 minutes
- Contracting: ~10-15 minutes
- Starting server: ~1 minute

Monitor progress:
```bash
docker-compose logs -f osrm
```

When you see `"running and waiting for requests"`, OSRM is ready!

### 2. Start Backend

```bash
cd /Users/eminsonlu/Projects/trash-collection/routes/backend
uvicorn main:app --reload
```

Backend will be available at: `http://localhost:8000`

### 3. Start Frontend

```bash
cd /Users/eminsonlu/Projects/trash-collection/routes/frontend
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## Using the Application

### Option 1: Web Interface (Recommended)

1. **Open browser**: Navigate to `http://localhost:5173`

2. **Click "Create Route"** in the navigation bar

3. **Select parameters**:
   - **Neighborhood**: Choose from dropdown (e.g., "ÜÇEVLER MAHALLESİ")
   - **Week Start Date**: Select a Monday
   - **Quick Mode**: Keep enabled for faster results

4. **Generate Route**: Click "Generate Optimized Route"

5. **View Results**:
   - **Map**: Interactive visualization with:
     - Blue "D" marker = Depot (starting point)
     - Green numbered markers = Containers (collection order)
     - Blue line = Optimized route path
   - **Statistics**: Total distance, container count
   - **Download**: Export GeoJSON for external use

### Option 2: API (For Developers)

#### Get Available Neighborhoods
```bash
curl http://localhost:8000/api/neighborhoods
```

**Response**:
```json
{
  "neighborhoods": [
    "19 MAYIS MAHALLESİ",
    "ÜÇEVLER MAHALLESİ",
    ...
  ]
}
```

#### Optimize a Route
```bash
curl -X POST http://localhost:8000/api/optimize/route \
  -H "Content-Type: application/json" \
  -d '{
    "neighborhood": "ÜÇEVLER MAHALLESİ",
    "week_start_date": "2025-01-06",
    "quick_mode": true
  }'
```

**Response**:
```json
{
  "neighborhood": "ÜÇEVLER MAHALLESİ",
  "week_start_date": "2025-01-06",
  "vehicle_type": "Small Garbage Truck",
  "vehicle_id": "small_garbage_truck_001",
  "schedule": [
    {
      "day": "Monday",
      "containers": 40,
      "distance_km": 5.636
    }
  ],
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Point",
          "coordinates": [28.9375, 40.1965]
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
          "coordinates": [28.9471, 40.2009]
        },
        "properties": {
          "type": "container",
          "container_id": 3233,
          "order": 1,
          "distance_from_previous_km": 0.95,
          "cumulative_distance_km": 0.95
        }
      },
      ...
    ]
  }
}
```

#### Check OSRM Health
```bash
curl http://localhost:8000/api/optimize/health
```

**Response**:
```json
{
  "status": "ok",
  "osrm": "available"
}
```

## Understanding the Results

### Route Optimization
- **Algorithm**: Nearest Neighbor (Greedy)
- **Depot**: `40.19654, 28.93751` (Nilüfer, Bursa)
- **Vehicle Capacity**: 40 containers per trip (default)
- **Distance Calculation**: Real driving distances via OSRM

### Example Route
For **ÜÇEVLER MAHALLESİ** with **Small Garbage Truck**:
- **Total Containers**: 40 (out of 206 small truck containers)
- **Total Distance**: 5.6 km
- **Optimization Time**: ~1-2 seconds with OSRM

### GeoJSON Features

Each optimized route includes:

1. **Depot Point**:
   ```json
   {
     "type": "depot",
     "name": "Depot"
   }
   ```

2. **Container Points** (one per stop):
   ```json
   {
     "type": "container",
     "container_id": 3233,
     "order": 1,
     "distance_from_previous_km": 0.95,
     "cumulative_distance_km": 0.95
   }
   ```

3. **Route Line**:
   ```json
   {
     "type": "route",
     "total_distance_km": 5.636,
     "total_containers": 40
   }
   ```

## Important Notes

### Multiple Vehicle Types

Some neighborhoods have containers for different vehicle types:
- **Large Garbage Truck**: Standard containers
- **Small Garbage Truck**: Smaller bins
- **Crane Vehicle**: Underground containers

The system optimizes routes per vehicle type. For example, ÜÇEVLER MAHALLESİ has:
- 393 Large Garbage Truck containers
- 206 Small Garbage Truck containers
- 66 Crane Vehicle containers

Each optimization targets one vehicle type.

### Vehicle Capacity

The default capacity is **40 containers per trip**. If a neighborhood has more containers than capacity:
- System optimizes the first 40 containers
- Response includes: `"requires_multiple_trips": true`
- Future enhancement: Support multiple trips

### Performance

**With OSRM** (recommended):
- Single route optimization: 1-2 seconds
- Distance queries: ~10-50ms each

**Without OSRM** (fallback):
- Uses Haversine formula (straight-line distance)
- Faster but less accurate
- Good for testing/development

## Troubleshooting

### 1. Neighborhoods Endpoint Error

**Symptom**: `500 Internal Server Error` on `/api/neighborhoods`

**Solution**: Already fixed! Endpoint now uses database instead of CSV files.

**Verify**:
```bash
curl http://localhost:8000/api/neighborhoods
# Should return list of neighborhoods
```

### 2. OSRM Not Available

**Symptom**: Route optimization returns straight-line distances

**Check OSRM**:
```bash
# Check if running
docker-compose ps osrm

# Check logs
docker-compose logs osrm

# Test OSRM directly
curl http://localhost:5001/health
# Should return: {"status":"Ok"}
```

**Restart OSRM**:
```bash
docker-compose restart osrm
```

### 3. No Containers Found

**Symptom**: `"No containers found for neighborhood 'X'"`

**Cause**: Selected neighborhood may not have containers for the vehicle type

**Solution**:
1. Check which neighborhoods have containers:
   ```bash
   curl http://localhost:8000/api/neighborhoods
   ```

2. Try a neighborhood with known containers:
   - ÜÇEVLER MAHALLESİ (393 containers)
   - DUMLUPINAR MAHALLESİ (689 containers)
   - BALKAN MAHALLESİ (367 containers)

### 4. Database Connection Failed

**Check PostgreSQL**:
```bash
docker-compose ps postgres
# Should show "Up"

# Test connection
docker-compose exec postgres psql -U admin -d trash_collection -c "SELECT COUNT(*) FROM neighborhoods;"
```

**Restart PostgreSQL**:
```bash
docker-compose restart postgres
```

### 5. Frontend Can't Connect to Backend

**Check CORS**: Verify backend has correct CORS settings in `app/config.py`:
```python
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000"
]
```

**Check Backend URL**: In frontend, verify `.env`:
```bash
VITE_API_URL=http://localhost:8000
```

## Next Steps

### Recommended Enhancements

1. **Multiple Trips**: Handle routes exceeding vehicle capacity
2. **Time Windows**: Add collection time constraints
3. **Better Algorithms**: Implement 2-opt or use OR-Tools
4. **Route Comparison**: Compare multiple optimization strategies
5. **Real-time Traffic**: Use OSRM traffic data
6. **Route Editing**: Drag-and-drop to reorder stops
7. **Mobile App**: React Native version for drivers

### Advanced Usage

**Batch Processing**:
```python
import requests

neighborhoods = ["ÜÇEVLER MAHALLESİ", "KONAK MAHALLESİ", "ODUNLUK MAHALLESİ"]

for neighborhood in neighborhoods:
    response = requests.post(
        "http://localhost:8000/api/optimize/route",
        json={
            "neighborhood": neighborhood,
            "week_start_date": "2025-01-06",
            "quick_mode": True
        }
    )
    route = response.json()
    print(f"{neighborhood}: {route['geojson']['features'][-1]['properties']['total_distance_km']} km")
```

## Support

### Documentation
- Backend API: `/Users/eminsonlu/Projects/trash-collection/routes/backend/ROUTE_OPTIMIZATION.md`
- Frontend: `/Users/eminsonlu/Projects/trash-collection/routes/frontend/FRONTEND_IMPLEMENTATION.md`

### Logs
```bash
# Backend logs
tail -f /path/to/backend.log

# Docker logs
docker-compose logs -f

# OSRM logs
docker-compose logs -f osrm
```

### Database Queries
```sql
-- Check neighborhoods with containers
SELECT
    n.neighborhood_name,
    COUNT(c.container_id) as container_count,
    c.vehicle_type
FROM neighborhoods n
LEFT JOIN containers c ON n.neighborhood_id = c.neighborhood_id
GROUP BY n.neighborhood_name, c.vehicle_type
HAVING COUNT(c.container_id) > 0
ORDER BY container_count DESC;
```

---

**System Status**: ✅ All endpoints working correctly!

**Last Updated**: 2025-12-28
