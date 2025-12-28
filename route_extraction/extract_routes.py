# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas",
#     "sqlalchemy",
#     "psycopg2-binary",
#     "python-dotenv",
# ]
# ///

"""Extract vehicle routes from GPS data."""

import pandas as pd
import logging
from sqlalchemy import text
from db import get_engine
from config import GPS_DATA_PATH, FLEET_DATA_PATH, MIN_ROUTE_DURATION_MINUTES, MIN_ROUTE_DISTANCE_KM
from utils import parse_datetime, calculate_distance, create_linestring_wkt
from map_matching import snap_route_to_roads, update_road_usage

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def load_fleet_data(engine):
    """Load fleet data into database."""
    logger.info("Loading fleet data...")
    fleet_df = pd.read_csv(FLEET_DATA_PATH)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM vehicles"))
        count = result.scalar()

    if count == 0:
        fleet_df.to_sql('vehicles', engine, if_exists='append', index=False)
        logger.info(f"✓ Loaded {len(fleet_df)} vehicles")
    else:
        logger.info(f"✓ Vehicles already loaded ({count} vehicles)")


def load_gps_data():
    """Load and prepare GPS data."""
    logger.info(f"Loading GPS data from {GPS_DATA_PATH}...")
    df = pd.read_csv(GPS_DATA_PATH)

    df['timestamp'] = df.apply(lambda row: parse_datetime(row['Tarih'], row['Saat']), axis=1)
    df = df.dropna(subset=['timestamp'])
    df = df.sort_values(['vehicle_id', 'timestamp'])

    logger.info(f"✓ Loaded {len(df)} GPS points")
    return df


def extract_routes_for_vehicle(df_vehicle, vehicle_id):
    """Extract routes for a single vehicle."""
    routes = []
    current_route = None

    for _, row in df_vehicle.iterrows():
        timestamp = row['timestamp']
        description = row['Açıklama']

        if description == 'Kontak Açıldı':
            current_route = {
                'vehicle_id': vehicle_id,
                'start_time': timestamp,
                'start_lat': row['Enlem'],
                'start_lon': row['Boylam'],
                'route_date': timestamp.date(),
                'gps_points': []
            }

        if current_route is not None:
            current_route['gps_points'].append({
                'lat': row['Enlem'],
                'lon': row['Boylam'],
                'timestamp': timestamp
            })

        if description == 'Kontak Kapandı' and current_route is not None:
            current_route['end_time'] = timestamp
            current_route['end_lat'] = row['Enlem']
            current_route['end_lon'] = row['Boylam']

            duration = (current_route['end_time'] - current_route['start_time']).total_seconds() / 60
            current_route['duration_minutes'] = int(duration)

            distance = calculate_route_distance(current_route['gps_points'])
            current_route['total_distance_km'] = distance

            if duration >= MIN_ROUTE_DURATION_MINUTES and distance >= MIN_ROUTE_DISTANCE_KM:
                routes.append(current_route)

            current_route = None

    return routes


def calculate_route_distance(gps_points):
    """Calculate total route distance."""
    if len(gps_points) < 2:
        return 0.0

    total_distance = 0.0
    for i in range(len(gps_points) - 1):
        dist = calculate_distance(
            gps_points[i]['lat'], gps_points[i]['lon'],
            gps_points[i + 1]['lat'], gps_points[i + 1]['lon']
        )
        total_distance += dist

    return round(total_distance, 2)


def process_route_with_map_matching(route, conn):
    """
    Apply map-matching to route and update road usage.

    Args:
        route: Route dict with gps_points
        conn: Database connection

    Returns:
        Updated route dict with snapped points and road info
    """
    # Snap GPS points to roads
    snapped_points, roads_used = snap_route_to_roads(route['gps_points'], conn)

    # Update route with snapped points
    route['snapped_points'] = snapped_points
    route['roads_used'] = roads_used
    route['roads_count'] = len(roads_used)

    # Calculate distance using snapped points
    snapped_gps = [
        {'lat': p['snapped_lat'], 'lon': p['snapped_lon']}
        for p in snapped_points
    ]
    route['snapped_distance_km'] = calculate_route_distance(snapped_gps)

    # Update road usage statistics
    update_road_usage(roads_used, route['start_time'], conn)

    return route


def save_routes(routes, engine):
    """Save routes to database."""
    if not routes:
        logger.warning("No routes to save")
        return

    routes_data = []
    for route in routes:
        # Use snapped points if available, otherwise original
        if 'snapped_points' in route:
            # Snapped points have snapped_lat/lon keys
            gps_for_line = [
                {'lat': p['snapped_lat'], 'lon': p['snapped_lon']}
                for p in route['snapped_points']
            ]
        else:
            # Original GPS points have lat/lon keys
            gps_for_line = [
                {'lat': p['lat'], 'lon': p['lon']}
                for p in route['gps_points']
            ]

        routes_data.append({
            'vehicle_id': route['vehicle_id'],
            'route_date': route['route_date'],
            'start_time': route['start_time'],
            'end_time': route['end_time'],
            'duration_minutes': route['duration_minutes'],
            'start_lat': route['start_lat'],
            'start_lon': route['start_lon'],
            'end_lat': route['end_lat'],
            'end_lon': route['end_lon'],
            'route_line': create_linestring_wkt(gps_for_line),
            'total_distance_km': route.get('snapped_distance_km', calculate_route_distance(route['gps_points']))
        })

    routes_df = pd.DataFrame(routes_data)
    routes_df.to_sql('routes', engine, if_exists='append', index=False)
    logger.info(f"✓ Saved {len(routes_data)} routes")


def main():
    """Main execution."""
    import sys

    # Check for --no-map-matching flag
    enable_map_matching = '--no-map-matching' not in sys.argv

    logger.info("=" * 50)
    logger.info("Route Extraction Started")
    if not enable_map_matching:
        logger.info("Map-matching: DISABLED (fast mode)")
    logger.info("=" * 50)

    engine = get_engine()

    load_fleet_data(engine)

    df = load_gps_data()

    all_routes = []
    vehicles = df['vehicle_id'].unique()

    logger.info(f"\nProcessing {len(vehicles)} vehicles...")

    if enable_map_matching:
        # Create a single database connection for map-matching
        with engine.connect() as map_conn:
            for vehicle_id in vehicles:
                df_vehicle = df[df['vehicle_id'] == vehicle_id]
                routes = extract_routes_for_vehicle(df_vehicle, vehicle_id)

                # Apply map-matching to each route
                logger.info(f"  Vehicle {vehicle_id}: {len(routes)} routes extracted")
                if routes:
                    logger.info(f"    Applying map-matching...")
                    matched_routes = []
                    for i, route in enumerate(routes, 1):
                        try:
                            logger.info(f"      Route {i}/{len(routes)} ({len(route['gps_points'])} points)...")
                            matched_route = process_route_with_map_matching(route, map_conn)
                            matched_routes.append(matched_route)
                        except Exception as e:
                            logger.warning(f"    Map-matching failed for route {i}: {e}")
                            matched_routes.append(route)

                    all_routes.extend(matched_routes)
                    logger.info(f"    ✓ Map-matching complete")
    else:
        # Fast mode - no map-matching
        for vehicle_id in vehicles:
            df_vehicle = df[df['vehicle_id'] == vehicle_id]
            routes = extract_routes_for_vehicle(df_vehicle, vehicle_id)
            logger.info(f"  Vehicle {vehicle_id}: {len(routes)} routes extracted")
            all_routes.extend(routes)

    logger.info(f"\nTotal routes extracted: {len(all_routes)}")
    save_routes(all_routes, engine)

    logger.info("\n" + "=" * 50)
    logger.info("✓ Route extraction completed!")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
