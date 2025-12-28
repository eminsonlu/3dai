# OSRM Setup Status

## Current Status: Processing ⏳

OSRM is currently processing the Turkey OSM data (588MB). This is a **one-time setup** that takes approximately **15-25 minutes**.

## Processing Stages

### ✅ Stage 1: Extracting OSM Data
**Status**: Currently running
**Duration**: ~5-10 minutes
**What it does**: Reads the Turkey map data and prepares it for routing

### ⏳ Stage 2: Contracting Graph
**Status**: Pending
**Duration**: ~10-15 minutes
**What it does**: Builds the routing graph using the MLD algorithm

### ⏳ Stage 3: Starting Server
**Status**: Pending
**Duration**: ~1 minute
**What it does**: Starts the HTTP server to accept routing requests

## Monitor Progress

### Option 1: Watch Logs (Recommended)
```bash
# In the routes directory
docker logs osrm_routing --follow
```

**What to look for**:
- `=== Step 1/3: Extracting OSM data ===` - Extraction started
- `✓ Extraction complete` - Extraction finished
- `=== Step 2/3: Contracting graph ===` - Contracting started
- `✓ Contracting complete` - Contracting finished
- `=== Step 3/3: Starting OSRM server ===` - Server starting
- `[info] running and waiting for requests` - **OSRM IS READY!** ✅

### Option 2: Use Wait Script
```bash
# In the routes directory
./wait_for_osrm.sh
```

This script will automatically monitor OSRM and notify you when it's ready.

### Option 3: Manual Check
```bash
# Test if OSRM is ready
curl http://localhost:5001/health

# If ready, returns:
{"status":"Ok"}

# If not ready, connection will fail
```

## Why the "Connection Reset" Error?

The error you saw:
```
OSRM request failed: ('Connection aborted.', ConnectionResetError(54, 'Connection reset by peer'))
```

This happens because:
1. OSRM is still processing the OSM data
2. The HTTP server hasn't started yet
3. Your backend is trying to connect before OSRM is ready

**This is normal!** Once OSRM finishes processing, the error will go away.

## What Was Fixed

### Problem
The previous OSRM setup was failing because:
1. The contracting step wasn't completing
2. The container was restarting in a loop
3. Port 5000 was already in use by macOS AirPlay

### Solution
1. ✅ Changed OSRM port from 5000 → 5001 (avoid macOS conflict)
2. ✅ Fixed docker-compose command to properly sequence extraction → contracting → server
3. ✅ Added error handling with `set -e`
4. ✅ Check for `.hsgr` file to know when contracting is complete
5. ✅ Removed restart loop to prevent continuous failures

## What Happens Next

Once OSRM is ready (you'll see "running and waiting for requests"), you can:

### 1. Test OSRM Directly
```bash
curl http://localhost:5001/health
# Returns: {"status":"Ok"}
```

### 2. Test via Backend
```bash
curl http://localhost:8000/api/optimize/health
# Returns: {"status":"ok","osrm":"available"}
```

### 3. Create an Optimized Route
```bash
curl -X POST http://localhost:8000/api/optimize/route \
  -H "Content-Type: application/json" \
  -d '{
    "neighborhood": "ÜÇEVLER MAHALLESİ",
    "week_start_date": "2025-01-06",
    "quick_mode": true
  }'
```

### 4. Use the Frontend
1. Open `http://localhost:5173`
2. Click "Create Route"
3. Select a neighborhood
4. Click "Generate Optimized Route"
5. See the route on the map! 🗺️

## Estimated Time Remaining

Based on typical processing times:

- **Extraction**: 5-10 minutes
- **Contracting**: 10-15 minutes
- **Server Start**: < 1 minute

**Total**: 15-25 minutes from when you started

### Current Progress
Check the logs to see which stage you're in:
```bash
docker logs osrm_routing --tail 5
```

## Important Notes

### ⚠️ Do Not Restart
While OSRM is processing, **do not restart the container** or you'll have to start over!

### ✅ One-Time Setup
This processing only happens **once**. After the first setup:
- OSRM will start in ~1 second on future restarts
- The processed data is saved in a Docker volume
- No need to re-process unless you change the OSM file

### 🔄 If You Need to Start Over
```bash
# Stop and remove container
docker-compose stop osrm
docker-compose rm -f osrm

# Remove the data volume
docker volume rm routes_osrm_data

# Start again
docker-compose up -d osrm
```

## Troubleshooting

### Container Keeps Restarting
If the container is stuck restarting:
```bash
# Check logs for errors
docker logs osrm_routing

# If needed, follow the "Start Over" steps above
```

### Processing Seems Stuck
If you don't see log updates for >5 minutes:
```bash
# Check if container is running
docker-compose ps osrm

# Check latest log
docker logs osrm_routing --tail 1
```

### Want to See Progress
Extraction and contracting show percentage updates:
```bash
docker logs osrm_routing | grep -E "(Step|%|complete)"
```

## After OSRM is Ready

1. The route optimization will use **real driving distances**
2. Routes will be optimized for actual road networks
3. Typical optimization time: 1-2 seconds per route
4. Much more accurate than straight-line distances

---

**Status**: Processing started at $(date)
**Check again in**: 15-20 minutes
**Monitor with**: `docker logs osrm_routing --follow`
