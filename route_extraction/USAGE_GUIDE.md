# Map-Matching & Road Usage Analysis - Usage Guide

## Quick Start

### Step 1: Load Road Network

```bash
cd routes/route_extraction
uv run load_roads.py
```

**Output:**
- Creates `roads` table in database
- Loads 5,579 road segments
- Sets up spatial indexes

### Step 2: Extract Routes with Map-Matching

```bash
uv run extract_routes.py
```

**What happens:**
1. Extracts routes from GPS data
2. For each GPS point:
   - Finds nearest road (within 50m)
   - Snaps point to that road
   - Records which road was used
3. Saves map-matched routes
4. Updates road usage counters

**Output:**
- Routes saved to `routes` table
- Road usage statistics updated

### Step 3: Analyze Road Usage

```bash
uv run analyze_road_usage.py
```

**Shows:**
- Top 20 most used roads
- Road usage by neighborhood
- Coverage percentages
- Unused roads

---

## Example Output

### Most Used Roads
```
📊 Top 20 Most Used Roads
------------------------------------------------------------
ANADOLU                        (19 MAYIS      ):   45 times
AYÇİÇEĞİ                       (19 MAYIS      ):   38 times
AZİZ NESİN                     (19 MAYIS      ):   32 times
```

### Neighborhood Analysis
```
🏘️  Road Usage by Neighborhood
------------------------------------------------------------
Neighborhood          Total   Used Visits Coverage
------------------------------------------------------------
19 MAYIS                89     67    428    75.3%
BEŞEVLER               145     98    672    67.6%
ALTINŞEHIR             112     84    591    75.0%
```

### Coverage Leaders
```
🎯 Top 5 Neighborhoods by Coverage
------------------------------------------------------------
ATLAS               : 92.5% coverage (37/40 roads)
19 MAYIS            : 75.3% coverage (67/89 roads)
ALTINŞEHIR          : 75.0% coverage (84/112 roads)
```

---

## API Endpoints

Start backend and use these endpoints:

### Get Most Used Roads
```bash
curl http://localhost:8000/api/roads/most-used?limit=20
```

**Response:**
```json
[
  {
    "road_id": 123,
    "road_name": "ANADOLU",
    "neighborhood": "19 MAYIS",
    "times_used": 45,
    "length_m": 732.03,
    "last_visited": "2025-12-19T14:30:00"
  }
]
```

### Get Neighborhood Usage
```bash
curl http://localhost:8000/api/roads/usage-by-neighborhood
```

**Response:**
```json
[
  {
    "neighborhood": "19 MAYIS",
    "total_roads": 89,
    "roads_used": 67,
    "total_visits": 428,
    "avg_visits": 6.4,
    "total_length_km": 12.5,
    "coverage_percent": 75.3
  }
]
```

### Get Roads in Neighborhood
```bash
curl http://localhost:8000/api/roads/neighborhood/19%20MAYIS
```

---

## How Map-Matching Works

### Before Map-Matching
```
GPS points may drift off roads:

     Road ════════════════
          ↓ (drift)
          • GPS point (off-road)
```

### After Map-Matching
```
GPS points snapped to actual roads:

     Road ══•═════•══════•══
           ↑     ↑      ↑
        Snapped points
```

### Benefits
- ✓ Routes follow actual streets
- ✓ Fix GPS errors
- ✓ Accurate road usage tracking
- ✓ Better distance calculation
- ✓ Know which roads are used

---

## Database Schema

### roads table
```sql
road_id           SERIAL PRIMARY KEY
road_name         VARCHAR(200)
neighborhood      VARCHAR(100)
length_m          DECIMAL(10,2)
width_m           DECIMAL(5,2)
road_line         GEOMETRY(LINESTRING, 4326)
times_used        INTEGER          -- Counter!
last_visited      TIMESTAMP        -- Last visit time
```

### routes table
```sql
route_id          SERIAL PRIMARY KEY
vehicle_id        INTEGER
route_date        DATE
start_time        TIMESTAMP
end_time          TIMESTAMP
route_line        GEOMETRY(LINESTRING, 4326)  -- Map-matched!
total_distance_km DECIMAL(10,2)               -- Accurate!
```

---

## Configuration

Edit `.env`:

```bash
# Map-matching settings
MIN_ROUTE_DURATION_MINUTES=15    # Minimum route duration
MIN_ROUTE_DISTANCE_KM=5.0        # Minimum route distance
```

---

## Use Cases

### 1. Find Most Used Streets
"Which roads do our trucks use most often?"

### 2. Identify Coverage Gaps
"Which neighborhoods have poor road coverage?"

### 3. Optimize Future Routes
"Avoid overused roads, visit unused areas"

### 4. Plan Maintenance
"Which roads need more attention from heavy truck usage?"

### 5. Service Level Reporting
"How well are we covering all neighborhoods?"

---

## Troubleshooting

### Map-matching fails
**Problem:** No roads found nearby
**Solution:** GPS point too far from roads (>50m threshold)
- Check GPS data quality
- Adjust threshold in `map_matching.py` if needed

### Slow performance
**Problem:** Map-matching takes too long
**Solution:**
- Spatial indexes should be created (check with `\d roads` in psql)
- Process fewer vehicles at once
- Consider batching

### Wrong roads matched
**Problem:** GPS points snapped to wrong road
**Solution:**
- Roads may be too close together
- Review threshold distance (50m default)
- Inspect specific problem areas

---

## Tips

1. **Run load_roads.py only once** - roads table is static
2. **Clear routes before re-extracting:**
   ```sql
   DELETE FROM routes;
   UPDATE roads SET times_used = 0, last_visited = NULL;
   ```
3. **Monitor progress** - extraction logs show map-matching status
4. **Check spatial indexes** - essential for performance
5. **Verify results** - compare route distances before/after matching

---

## Next Steps

After running map-matching:

1. **Visualize on map** - See routes following actual roads
2. **Compare distances** - Original vs map-matched
3. **Analyze patterns** - Which roads always used vs sometimes
4. **Generate reports** - Coverage reports by neighborhood
5. **Plan optimization** - Use road usage data for better routing

---

**Questions?** Check the code comments or run scripts with `-h` flag!
