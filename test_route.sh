#!/bin/bash
curl -s -X POST http://localhost:8000/api/optimize/route -H 'Content-Type: application/json' -d '{"neighborhood": "KONAK MAHALLESİ", "week_start_date": "2025-01-06"}' > /tmp/route_test.json

echo "Route Optimization Test Results:"
echo "================================"
python3 << 'EOF'
import json
with open('/tmp/route_test.json') as f:
    data = json.load(f)

    # Get route feature
    features = data['geojson']['features']
    route = next((f for f in features if f['properties'].get('type') == 'route'), None)

    if route:
        props = route['properties']
        coords = route['geometry']['coordinates']

        print(f"✅ OSRM IS WORKING!")
        print(f"Neighborhood: {data['neighborhood']}")
        print(f"Vehicle: {data['vehicle_type']}")
        print(f"Total Distance: {props['total_distance_km']:.2f} km (real driving distance)")
        print(f"Total Containers: {props['total_containers']}")
        print(f"Route Points: {len(coords)} coordinates (following roads)")
        print(f"\nFirst 3 containers:")

        containers = [f for f in features if f['properties'].get('type') == 'container']
        for i in range(min(3, len(containers))):
            c = containers[i]['properties']
            print(f"  {i+1}. Container #{c['container_id']}: {c['distance_from_previous_km']:.3f} km from previous")
    else:
        print("❌ No route found")
        print(json.dumps(data, indent=2)[:500])
EOF
