# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "sqlalchemy",
#     "psycopg2-binary",
#     "python-dotenv",
# ]
# ///

"""Map-matching utilities - snap GPS points to roads."""

from sqlalchemy import text
from db import get_engine


def snap_point_to_road(lat, lon, conn, max_distance_m=50):
    """
    Snap a GPS point to nearest road.

    Args:
        lat: Latitude
        lon: Longitude
        conn: Database connection
        max_distance_m: Maximum distance to search for roads (meters)

    Returns:
        dict with snapped point info or None if too far from roads
    """
    result = conn.execute(text("""
            SELECT
                road_id,
                road_name,
                neighborhood,
                ST_Distance(
                    road_line::geography,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                ) as distance_m,
                ST_AsText(
                    ST_ClosestPoint(
                        road_line,
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
                    )
                ) as snapped_point
            FROM roads
            WHERE ST_DWithin(
                road_line::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                :max_dist
            )
            ORDER BY distance_m
            LIMIT 1
    """), {
        'lat': lat,
        'lon': lon,
        'max_dist': max_distance_m
    })

    row = result.fetchone()

    if not row:
        return None

    # Parse WKT POINT(lon lat)
    wkt = row.snapped_point
    coords = wkt.replace('POINT(', '').replace(')', '').split()
    snapped_lon = float(coords[0])
    snapped_lat = float(coords[1])

    return {
        'road_id': row.road_id,
        'road_name': row.road_name,
        'neighborhood': row.neighborhood,
        'distance_m': row.distance_m,
        'original_lat': lat,
        'original_lon': lon,
        'snapped_lat': snapped_lat,
        'snapped_lon': snapped_lon
    }


def snap_route_to_roads(gps_points, conn, max_distance_m=50, sample_interval=10):
    """
    Snap GPS points in a route to roads (with sampling for performance).

    Args:
        gps_points: List of dicts with 'lat' and 'lon' keys
        conn: Database connection
        max_distance_m: Maximum distance threshold
        sample_interval: Process every Nth point (default 10 for performance)

    Returns:
        List of snapped points with road info
    """
    snapped_points = []
    roads_used = set()

    # Sample points for performance - take every Nth point plus first and last
    sampled_indices = list(range(0, len(gps_points), sample_interval))
    if len(gps_points) - 1 not in sampled_indices:
        sampled_indices.append(len(gps_points) - 1)

    for idx in sampled_indices:
        point = gps_points[idx]
        snapped = snap_point_to_road(
            point['lat'],
            point['lon'],
            conn,
            max_distance_m
        )

        if snapped:
            snapped_points.append(snapped)
            roads_used.add(snapped['road_id'])
        else:
            # Keep original point if no nearby road
            snapped_points.append({
                'road_id': None,
                'road_name': None,
                'neighborhood': None,
                'distance_m': None,
                'original_lat': point['lat'],
                'original_lon': point['lon'],
                'snapped_lat': point['lat'],
                'snapped_lon': point['lon']
            })

    return snapped_points, list(roads_used)


def update_road_usage(road_ids, visit_time, conn):
    """
    Update usage statistics for roads.

    Args:
        road_ids: List of road IDs that were used
        visit_time: Timestamp of visit
        conn: Database connection
    """
    if not road_ids:
        return

    for road_id in road_ids:
        conn.execute(text("""
            UPDATE roads
            SET times_used = times_used + 1,
                last_visited = :visit_time
            WHERE road_id = :road_id
        """), {
            'road_id': road_id,
            'visit_time': visit_time
        })
    conn.commit()


if __name__ == "__main__":
    # Test map-matching
    print("Testing map-matching...")

    # Test point in Bursa
    test_lat = 40.2250
    test_lon = 28.8900

    engine = get_engine()
    with engine.connect() as conn:
        result = snap_point_to_road(test_lat, test_lon, conn)

        if result:
            print(f"✓ Snapped to road: {result['road_name']}")
            print(f"  Neighborhood: {result['neighborhood']}")
            print(f"  Distance: {result['distance_m']:.1f}m")
            print(f"  Original: ({result['original_lat']}, {result['original_lon']})")
            print(f"  Snapped: ({result['snapped_lat']}, {result['snapped_lon']})")
        else:
            print("✗ No road found nearby")
