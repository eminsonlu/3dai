# Backend API

Unified FastAPI backend for trash collection routes - serving both historical route data and ACO-based route optimization.

## Features

- **Historical Routes**: View and analyze past collection routes
- **Route Optimization**: Generate optimized routes using Ant Colony Optimization (ACO)
- **Road Usage Analytics**: Track most-used roads by neighborhood
- **Auto-Configuration**: Vehicle type and schedule determined from CSV data

## Setup

Install dependencies using `uv`:

```bash
cd routes/backend
uv pip install -r requirements.txt
```

## Run

```bash
cd routes/backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

Or for development with auto-reload:

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: `http://localhost:8000`

## API Endpoints

### General
- `GET /` - Health check

### Historical Routes
- `GET /api/routes` - Get all historical routes as GeoJSON
- `GET /api/routes/stats` - Get route statistics

### Road Analytics
- `GET /api/roads/most-used` - Get most frequently used roads
- `GET /api/roads/usage-by-neighborhood` - Road usage by neighborhood
- `GET /api/roads/neighborhood/{neighborhood}` - Most used roads in specific neighborhood

### Route Optimization (ACO)
- `GET /api/neighborhoods` - Get list of available neighborhoods
- `POST /api/optimize-route` - Generate optimized route for a neighborhood

## Example: Optimize Route

```bash
curl -X POST http://localhost:8000/api/optimize-route \
  -H "Content-Type: application/json" \
  -d '{
    "neighborhood": "19 MAYIS MAHALLESİ",
    "week_start_date": "2025-12-30"
  }'
```

The API automatically:
- Determines vehicle type from `neighbor_days_rotations.csv`
- Loads collection schedule for the neighborhood
- Selects top 100 priority containers if needed
- Runs ACO optimization
- Returns GeoJSON with optimized route and schedule
