#!/bin/bash

# Script to wait for OSRM to be ready
# Usage: ./wait_for_osrm.sh

echo "⏳ Waiting for OSRM to finish processing..."
echo ""
echo "OSRM Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

while true; do
    # Check if server is ready
    if curl -s http://localhost:5001/health > /dev/null 2>&1; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ OSRM is ready!"
        echo ""
        echo "You can now:"
        echo "  • Use the route optimization API"
        echo "  • Test with: curl http://localhost:5001/health"
        echo "  • Create routes in the frontend"
        echo ""
        break
    fi

    # Show latest log line
    LAST_LINE=$(docker logs osrm_routing 2>&1 | tail -1)

    # Check processing phase
    if echo "$LAST_LINE" | grep -q "Extracting"; then
        echo "📦 Phase 1/3: Extracting OSM data..."
    elif echo "$LAST_LINE" | grep -q "Contracting"; then
        echo "⚙️  Phase 2/3: Contracting graph..."
    elif echo "$LAST_LINE" | grep -q "Starting OSRM server"; then
        echo "🚀 Phase 3/3: Starting server..."
    elif echo "$LAST_LINE" | grep -q "info"; then
        # Show percentage if available
        if echo "$LAST_LINE" | grep -qE "[0-9]+%"; then
            PERCENT=$(echo "$LAST_LINE" | grep -oE "[0-9]+%" | tail -1)
            echo "⚙️  Processing: $PERCENT"
        else
            echo "⚙️  Processing: $(echo "$LAST_LINE" | sed 's/\[info\] //')"
        fi
    fi

    sleep 5
done
