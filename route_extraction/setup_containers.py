# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "sqlalchemy",
#     "psycopg2-binary",
#     "python-dotenv",
#     "pandas",
# ]
# ///

"""
Setup containers table and link to neighborhoods using spatial matching.
"""

import pandas as pd
from pathlib import Path
from sqlalchemy import text
from db import get_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / 'NB_hackathon_2025-main' / 'Nilufer_bin_collection_dataset'


def create_containers_table(engine):
    """Create containers table with spatial column."""
    logger.info("Creating containers table...")

    with engine.connect() as conn:
        # Drop existing table
        conn.execute(text("""
            DROP TABLE IF EXISTS containers CASCADE;
        """))

        # Create containers table
        conn.execute(text("""
            CREATE TABLE containers (
                container_id SERIAL PRIMARY KEY,
                neighborhood_id INTEGER REFERENCES neighborhoods(neighborhood_id),
                latitude DOUBLE PRECISION NOT NULL,
                longitude DOUBLE PRECISION NOT NULL,
                location GEOGRAPHY(POINT, 4326),
                vehicle_type VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX idx_container_neighborhood ON containers(neighborhood_id);
            CREATE INDEX idx_container_location ON containers USING GIST(location);
            CREATE INDEX idx_container_coords ON containers(latitude, longitude);
        """))

        conn.commit()

    logger.info("✓ Containers table created")


def load_containers_from_csv():
    """Load container points from CSV."""
    logger.info("Loading containers from CSV...")

    containers_df = pd.read_csv(DATA_DIR / 'container_points.csv')

    logger.info(f"✓ Loaded {len(containers_df)} containers")
    return containers_df


def find_neighborhood_for_container(engine, lat, lon):
    """
    Find neighborhood for a container using spatial query.
    Uses neighborhoods table with addresses to determine neighborhood.
    """
    with engine.connect() as conn:
        # First try: Find nearest address within 200m
        result = conn.execute(text("""
            SELECT n.neighborhood_id, n.neighborhood_name
            FROM addresses a
            JOIN neighborhoods n ON a.neighborhood_id = n.neighborhood_id
            WHERE a.building_latitude IS NOT NULL
              AND a.building_longitude IS NOT NULL
              AND ST_DWithin(
                ST_SetSRID(ST_MakePoint(a.building_longitude, a.building_latitude), 4326)::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                200
              )
            ORDER BY ST_Distance(
                ST_SetSRID(ST_MakePoint(a.building_longitude, a.building_latitude), 4326)::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
            )
            LIMIT 1
        """), {'lat': lat, 'lon': lon})

        row = result.fetchone()
        if row:
            return row.neighborhood_id, row.neighborhood_name

        # Second try: Find nearest road within 500m
        result = conn.execute(text("""
            SELECT r.neighborhood_id, n.neighborhood_name
            FROM roads r
            JOIN neighborhoods n ON r.neighborhood_id = n.neighborhood_id
            WHERE r.neighborhood_id IS NOT NULL
              AND ST_DWithin(
                r.road_line::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                500
              )
            ORDER BY ST_Distance(
                r.road_line::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
            )
            LIMIT 1
        """), {'lat': lat, 'lon': lon})

        row = result.fetchone()
        if row:
            return row.neighborhood_id, row.neighborhood_name

    return None, None


def insert_containers(engine, containers_df):
    """Insert containers into database with neighborhood matching."""
    logger.info("Inserting containers and matching to neighborhoods...")

    batch_size = 100
    total = len(containers_df)
    matched_count = 0
    unmatched_count = 0

    with engine.connect() as conn:
        for i in range(0, total, batch_size):
            batch = containers_df.iloc[i:i+batch_size]

            for idx, row in batch.iterrows():
                lat = row['Enlem']
                lon = row['Boylam']
                vehicle_type = row['vehicle_type']

                # Find neighborhood using spatial query
                neighborhood_id, neighborhood_name = find_neighborhood_for_container(engine, lat, lon)

                if neighborhood_id:
                    matched_count += 1
                else:
                    unmatched_count += 1

                # Insert container
                conn.execute(text("""
                    INSERT INTO containers (
                        neighborhood_id,
                        latitude,
                        longitude,
                        location,
                        vehicle_type
                    )
                    VALUES (
                        :neighborhood_id,
                        :latitude,
                        :longitude,
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                        :vehicle_type
                    )
                """), {
                    'neighborhood_id': neighborhood_id,
                    'latitude': lat,
                    'longitude': lon,
                    'lat': lat,
                    'lon': lon,
                    'vehicle_type': vehicle_type
                })

            conn.commit()

            progress = ((i + len(batch)) / total) * 100
            logger.info(f"  Progress: {progress:.1f}% ({i + len(batch)}/{total}) - Matched: {matched_count}, Unmatched: {unmatched_count}")

    logger.info(f"✓ Inserted {total} containers")
    logger.info(f"  Matched to neighborhoods: {matched_count}")
    logger.info(f"  Unmatched: {unmatched_count}")


def show_summary(engine):
    """Show summary statistics."""
    logger.info("\n" + "=" * 60)
    logger.info("CONTAINERS SUMMARY")
    logger.info("=" * 60)

    with engine.connect() as conn:
        # Total containers
        result = conn.execute(text("SELECT COUNT(*) FROM containers"))
        logger.info(f"Total containers: {result.fetchone()[0]:,}")

        # Matched vs unmatched
        result = conn.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE neighborhood_id IS NOT NULL) as matched,
                COUNT(*) FILTER (WHERE neighborhood_id IS NULL) as unmatched
            FROM containers
        """))
        row = result.fetchone()
        logger.info(f"Matched to neighborhoods: {row.matched:,}")
        logger.info(f"Unmatched: {row.unmatched:,}")

        # Containers by neighborhood (top 5)
        logger.info("\nTop 5 Neighborhoods by Container Count:")
        result = conn.execute(text("""
            SELECT
                n.neighborhood_name,
                COUNT(c.container_id) as container_count,
                c.vehicle_type
            FROM containers c
            JOIN neighborhoods n ON c.neighborhood_id = n.neighborhood_id
            GROUP BY n.neighborhood_name, c.vehicle_type
            ORDER BY container_count DESC
            LIMIT 5
        """))
        for row in result:
            logger.info(f"  {row.neighborhood_name}: {row.container_count} containers ({row.vehicle_type})")

        # Containers by vehicle type
        logger.info("\nContainers by Vehicle Type:")
        result = conn.execute(text("""
            SELECT
                vehicle_type,
                COUNT(*) as count
            FROM containers
            GROUP BY vehicle_type
            ORDER BY count DESC
        """))
        for row in result:
            logger.info(f"  {row.vehicle_type}: {row.count:,}")


def main():
    """Main setup function."""
    logger.info("=" * 60)
    logger.info("SETTING UP CONTAINERS DATABASE")
    logger.info("=" * 60)
    logger.info("")

    engine = get_engine()

    # Step 1: Create table
    create_containers_table(engine)

    # Step 2: Load containers from CSV
    containers_df = load_containers_from_csv()

    # Step 3: Insert containers with neighborhood matching
    insert_containers(engine, containers_df)

    # Step 4: Show summary
    show_summary(engine)

    logger.info("\n" + "=" * 60)
    logger.info("✓ SETUP COMPLETE!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
