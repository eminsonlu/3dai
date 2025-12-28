# Route Extraction with Map-Matching

Extract vehicle routes from GPS data with map-matching to actual roads.

## Features

✓ Extract routes (engine on → off, >= 15 min)
✓ **Map-matching**: Snap GPS points to actual roads
✓ **Road usage tracking**: Which roads are used most
✓ Accurate distance calculation

## Setup

```bash
# 1. Start database
cd ../
docker-compose up -d

# 2. Load road network
cd route_extraction
uv run load_roads.py

# 3. Test map-matching
uv run map_matching.py
```

## Extract Routes

```bash
# Extract routes with map-matching
uv run extract_routes.py
```

This will:
1. Extract routes from GPS data
2. Snap each GPS point to nearest road
3. Track which roads are used
4. Save map-matched routes to database

## Analyze Road Usage

```bash
# Generate road usage report
uv run analyze_road_usage.py
```

Shows:
- Most used roads
- Road usage by neighborhood
- Coverage statistics
- Unused roads

## Files

- `load_roads.py` - Load road network to database
- `map_matching.py` - Map-matching utilities
- `extract_routes.py` - Main extraction (updated with map-matching)
- `analyze_road_usage.py` - Road usage analysis
- `db.py` - Database connection
- `config.py` - Configuration
- `utils.py` - Helper functions

## How Map-Matching Works

```
GPS Point (40.2250, 28.8900)
    ↓
Find nearest road (within 50m)
    ↓
Snap to closest point on that road
    ↓
Snapped Point (40.2251, 28.8902) on "Ayçiçeği Street"
    ↓
Update road usage counter
```

## Database Tables

### roads
- road_id, road_name, neighborhood
- road_line (geometry)
- times_used (counter)
- last_visited (timestamp)

### routes
- Updated with map-matched GPS paths
- More accurate distances

## API Endpoints (Backend)

After running extraction:

- `GET /api/roads/most-used` - Top 20 most used roads
- `GET /api/roads/usage-by-neighborhood` - Usage by area
- `GET /api/roads/neighborhood/{name}` - Roads in neighborhood
