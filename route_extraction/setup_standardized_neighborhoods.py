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
Setup standardized neighborhoods and addresses tables.
Handles different naming formats across CSV files.
"""

import pandas as pd
from pathlib import Path
from sqlalchemy import text
from db import get_engine
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / 'NB_hackathon_2025-main' / 'Nilufer_bin_collection_dataset'


def normalize_neighborhood_name(name: str) -> str:
    """
    Normalize neighborhood name to standard format.
    Converts: "19 Mayıs Mh." → "19 MAYIS MAHALLESİ"
    """
    # Remove common suffixes and clean
    name = str(name).strip()
    name = name.replace(' Mh.', '').replace(' MH.', '')
    name = name.replace(' MAHALLESİ', '').replace(' MAHALLES\u0130', '')

    # Convert to uppercase and normalize Turkish characters
    name = name.upper()
    name = name.replace('İ', 'I').replace('Ş', 'S').replace('Ğ', 'G')
    name = name.replace('Ü', 'U').replace('Ö', 'O').replace('Ç', 'C')

    # Add standard suffix
    if not name.endswith('MAHALLESİ'):
        name = name + ' MAHALLESİ'

    return name.strip()


def create_tables(engine):
    """Create neighborhoods and addresses tables."""
    logger.info("Creating database tables...")

    with engine.connect() as conn:
        # Drop existing tables
        conn.execute(text("""
            DROP TABLE IF EXISTS addresses CASCADE;
            DROP TABLE IF EXISTS neighborhoods CASCADE;
        """))

        # Create neighborhoods table
        conn.execute(text("""
            CREATE TABLE neighborhoods (
                neighborhood_id SERIAL PRIMARY KEY,
                neighborhood_name VARCHAR(200) UNIQUE NOT NULL,
                neighborhood_name_normalized VARCHAR(200) NOT NULL,
                neighborhood_id_external INTEGER,
                population INTEGER,
                neighborhood_type VARCHAR(50),
                garbage_truck_type VARCHAR(100),
                days_collected_per_week INTEGER,
                collection_days VARCHAR(200),
                uses_crane BOOLEAN DEFAULT FALSE,
                crane_rotation_days INTEGER DEFAULT 0,
                underground_containers INTEGER DEFAULT 0,
                container_770lt INTEGER DEFAULT 0,
                container_400lt INTEGER DEFAULT 0,
                plastic_containers INTEGER DEFAULT 0,
                total_containers INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX idx_neighborhood_name ON neighborhoods(neighborhood_name);
            CREATE INDEX idx_neighborhood_normalized ON neighborhoods(neighborhood_name_normalized);
        """))

        # Create addresses/buildings table
        conn.execute(text("""
            CREATE TABLE addresses (
                address_id SERIAL PRIMARY KEY,
                neighborhood_id INTEGER REFERENCES neighborhoods(neighborhood_id),
                city VARCHAR(100),
                district VARCHAR(100),
                street VARCHAR(200),
                street_id INTEGER,
                street_latitude DOUBLE PRECISION,
                street_longitude DOUBLE PRECISION,
                building_number VARCHAR(50),
                building_id BIGINT,
                uavt_code BIGINT,
                building_latitude DOUBLE PRECISION,
                building_longitude DOUBLE PRECISION,
                coordinate_source VARCHAR(50),
                block_name VARCHAR(200),
                site_name VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX idx_address_neighborhood ON addresses(neighborhood_id);
            CREATE INDEX idx_address_coordinates ON addresses(building_latitude, building_longitude);
        """))

        conn.commit()

    logger.info("✓ Tables created successfully")


def load_and_merge_neighborhood_data():
    """Load and merge neighborhood data from all CSV files."""
    logger.info("Loading neighborhood data from CSV files...")

    # 1. Load mahalle_nufus.csv
    logger.info("  Reading mahalle_nufus.csv...")
    nufus_df = pd.read_csv(DATA_DIR / 'mahalle_nufus.csv', sep=';', encoding='utf-8-sig')
    nufus_df.columns = nufus_df.columns.str.strip()
    nufus_df['mahalle'] = nufus_df['mahalle'].str.strip()

    # 2. Load neighbor_days_rotations.csv
    logger.info("  Reading neighbor_days_rotations.csv...")
    rotations_df = pd.read_csv(DATA_DIR / 'neighbor_days_rotations.csv', sep=';', encoding='utf-8-sig')
    rotations_df.columns = rotations_df.columns.str.strip()
    rotations_df['MAHALLE ADI'] = rotations_df['MAHALLE ADI'].str.strip()

    # 2b. Load container_counts.csv
    logger.info("  Reading container_counts.csv...")
    container_counts_df = pd.read_csv(DATA_DIR / 'container_counts.csv', sep=';', encoding='utf-8-sig')
    container_counts_df.columns = container_counts_df.columns.str.strip()
    container_counts_df['MAHALLE'] = container_counts_df['MAHALLE'].str.strip()

    # 3. Load unique neighborhoods from address_data.csv
    logger.info("  Reading address_data.csv...")
    address_df = pd.read_csv(
        DATA_DIR / 'address_data.csv',
        dtype={'neighborhood_id': str},  # Read as string to handle mixed types
        low_memory=False
    )
    address_neighborhoods = address_df[['neighborhood', 'neighborhood_id']].drop_duplicates()

    # Create mapping dictionary for neighborhoods
    neighborhoods = {}

    # Process mahalle_nufus data
    for _, row in nufus_df.iterrows():
        name = row['mahalle']
        normalized = normalize_neighborhood_name(name)

        if normalized not in neighborhoods:
            neighborhoods[normalized] = {
                'name': name,
                'normalized': normalized,
                'population': int(float(str(row['nufus']).replace('.', '')) * 1000) if pd.notna(row['nufus']) else None,
                'external_id': None,
                'type': None,
                'truck_type': None,
                'days_per_week': None,
                'collection_days': None,
                'uses_crane': False,
                'crane_rotation_days': 0,
                'underground_containers': 0,
                'container_770lt': 0,
                'container_400lt': 0,
                'plastic_containers': 0,
                'total_containers': 0
            }

    # Process rotations data
    for _, row in rotations_df.iterrows():
        name = row['MAHALLE ADI']
        normalized = normalize_neighborhood_name(name)

        if normalized not in neighborhoods:
            neighborhoods[normalized] = {
                'name': name,
                'normalized': normalized,
                'population': None,
                'external_id': None,
                'type': None,
                'truck_type': None,
                'days_per_week': None,
                'collection_days': None,
                'uses_crane': False,
                'crane_rotation_days': 0,
                'underground_containers': 0,
                'container_770lt': 0,
                'container_400lt': 0,
                'plastic_containers': 0,
                'total_containers': 0
            }

        neighborhoods[normalized].update({
            'truck_type': row['Garbage Truck Type'] if pd.notna(row['Garbage Truck Type']) else None,
            'days_per_week': int(row['Days Collected Per Week']) if pd.notna(row['Days Collected Per Week']) else None,
            'collection_days': row['Collection Frequency (Truck Type)'] if pd.notna(row['Collection Frequency (Truck Type)']) else None,
            'uses_crane': str(row['Is Crane Used']).upper() == 'TRUE',
            'crane_rotation_days': int(row['Crane rotation days']) if pd.notna(row['Crane rotation days']) else 0
        })

    # Process container_counts data
    for _, row in container_counts_df.iterrows():
        name = row['MAHALLE']
        normalized = normalize_neighborhood_name(name)

        # Helper function to safely get int value from potentially empty/NaN cells
        def safe_container_int(value):
            if pd.isna(value) or value == '':
                return 0
            try:
                return int(float(str(value)))
            except (ValueError, TypeError):
                return 0

        if normalized in neighborhoods:
            neighborhoods[normalized].update({
                'underground_containers': safe_container_int(row.get('YERALTI KONTEYNER', 0)),
                'container_770lt': safe_container_int(row.get('770 LT KONTEYNER', 0)),
                'container_400lt': safe_container_int(row.get('400 LT KONTEYNER', 0)),
                'plastic_containers': safe_container_int(row.get('PLASTİK', 0)),
                'total_containers': safe_container_int(row.get('TOPLAM', 0))
            })

    # Process address data - match neighborhoods
    for _, row in address_neighborhoods.iterrows():
        addr_name = row['neighborhood']
        addr_id = row['neighborhood_id']
        normalized = normalize_neighborhood_name(addr_name)

        # Convert to int only if it's numeric, otherwise skip
        try:
            addr_id_int = int(addr_id) if pd.notna(addr_id) and str(addr_id).isdigit() else None
        except (ValueError, TypeError):
            addr_id_int = None

        if normalized in neighborhoods and addr_id_int is not None:
            neighborhoods[normalized]['external_id'] = addr_id_int
        else:
            # Try fuzzy matching
            for key in neighborhoods.keys():
                if key.split()[0] in normalized or normalized.split()[0] in key:
                    if addr_id_int is not None:
                        neighborhoods[key]['external_id'] = addr_id_int
                    break

    logger.info(f"✓ Loaded {len(neighborhoods)} unique neighborhoods")
    return neighborhoods


def insert_neighborhoods(engine, neighborhoods):
    """Insert neighborhoods into database."""
    logger.info("Inserting neighborhoods into database...")

    neighborhood_map = {}  # Map normalized name to neighborhood_id

    with engine.connect() as conn:
        for normalized_name, data in neighborhoods.items():
            result = conn.execute(text("""
                INSERT INTO neighborhoods (
                    neighborhood_name,
                    neighborhood_name_normalized,
                    neighborhood_id_external,
                    population,
                    garbage_truck_type,
                    days_collected_per_week,
                    collection_days,
                    uses_crane,
                    crane_rotation_days,
                    underground_containers,
                    container_770lt,
                    container_400lt,
                    plastic_containers,
                    total_containers
                )
                VALUES (
                    :name, :normalized, :external_id, :population,
                    :truck_type, :days_per_week, :collection_days,
                    :uses_crane, :crane_rotation_days,
                    :underground, :c770lt, :c400lt, :plastic, :total
                )
                ON CONFLICT (neighborhood_name) DO UPDATE
                SET population = EXCLUDED.population,
                    garbage_truck_type = EXCLUDED.garbage_truck_type,
                    days_collected_per_week = EXCLUDED.days_collected_per_week,
                    collection_days = EXCLUDED.collection_days,
                    underground_containers = EXCLUDED.underground_containers,
                    container_770lt = EXCLUDED.container_770lt,
                    container_400lt = EXCLUDED.container_400lt,
                    plastic_containers = EXCLUDED.plastic_containers,
                    total_containers = EXCLUDED.total_containers
                RETURNING neighborhood_id
            """), {
                'name': data['name'],
                'normalized': data['normalized'],
                'external_id': data['external_id'],
                'population': data['population'],
                'truck_type': data['truck_type'],
                'days_per_week': data['days_per_week'],
                'collection_days': data['collection_days'],
                'uses_crane': data['uses_crane'],
                'crane_rotation_days': data['crane_rotation_days'],
                'underground': data['underground_containers'],
                'c770lt': data['container_770lt'],
                'c400lt': data['container_400lt'],
                'plastic': data['plastic_containers'],
                'total': data['total_containers']
            })

            neighborhood_id = result.fetchone()[0]
            neighborhood_map[data['normalized']] = neighborhood_id

        conn.commit()

    logger.info(f"✓ Inserted {len(neighborhoods)} neighborhoods")
    return neighborhood_map


def insert_addresses(engine, neighborhood_map):
    """Insert addresses/buildings into database."""
    logger.info("Inserting addresses into database...")

    # Load address data with proper dtypes for mixed columns
    address_df = pd.read_csv(
        DATA_DIR / 'address_data.csv',
        dtype={
            'neighborhood_id': str,
            'street_id': str,
            'building_id': str,
            'uavt_code': str
        },
        low_memory=False
    )

    # Create normalized neighborhood column for matching
    address_df['neighborhood_normalized'] = address_df['neighborhood'].apply(normalize_neighborhood_name)

    # Match with neighborhood_id
    address_df['neighborhood_db_id'] = address_df['neighborhood_normalized'].map(neighborhood_map)

    # Count matched vs unmatched
    matched = address_df['neighborhood_db_id'].notna().sum()
    total = len(address_df)
    logger.info(f"  Matched {matched}/{total} addresses to neighborhoods")

    # Insert in batches
    batch_size = 1000
    with engine.connect() as conn:
        for i in range(0, len(address_df), batch_size):
            batch = address_df.iloc[i:i+batch_size]

            for _, row in batch.iterrows():
                if pd.notna(row['neighborhood_db_id']):
                    # Helper function to safely convert to int
                    def safe_int(value):
                        if pd.isna(value) or value == 'Other':
                            return None
                        try:
                            return int(float(str(value)))
                        except (ValueError, TypeError):
                            return None

                    # Helper function to safely convert to float
                    def safe_float(value):
                        if pd.isna(value):
                            return None
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            return None

                    conn.execute(text("""
                        INSERT INTO addresses (
                            neighborhood_id, city, district, street, street_id,
                            street_latitude, street_longitude, building_number,
                            building_id, uavt_code, building_latitude, building_longitude,
                            coordinate_source, block_name, site_name
                        )
                        VALUES (
                            :neighborhood_id, :city, :district, :street, :street_id,
                            :street_lat, :street_lon, :building_number,
                            :building_id, :uavt_code, :building_lat, :building_lon,
                            :coordinate_source, :block_name, :site_name
                        )
                    """), {
                        'neighborhood_id': int(row['neighborhood_db_id']),
                        'city': row['city'] if pd.notna(row['city']) else None,
                        'district': row['district'] if pd.notna(row['district']) else None,
                        'street': row['street'] if pd.notna(row['street']) else None,
                        'street_id': safe_int(row['street_id']),
                        'street_lat': safe_float(row['street_latitude']),
                        'street_lon': safe_float(row['street_longitude']),
                        'building_number': row['building_number'] if pd.notna(row['building_number']) else None,
                        'building_id': safe_int(row['building_id']),
                        'uavt_code': safe_int(row['uavt_code']),
                        'building_lat': safe_float(row['building_latitude']),
                        'building_lon': safe_float(row['building_longitude']),
                        'coordinate_source': row['coordinate_source'] if pd.notna(row['coordinate_source']) else None,
                        'block_name': row['block_name'] if pd.notna(row['block_name']) else None,
                        'site_name': row['site_name'] if pd.notna(row['site_name']) else None
                    })

            conn.commit()
            logger.info(f"  Inserted batch {i//batch_size + 1}/{(len(address_df) + batch_size - 1)//batch_size}")

    logger.info(f"✓ Inserted {matched} addresses")


def update_roads_table(engine):
    """Update roads table to link with neighborhoods."""
    logger.info("Updating roads table with neighborhood relations...")

    with engine.connect() as conn:
        # Add neighborhood_id column if not exists
        conn.execute(text("""
            ALTER TABLE roads
            ADD COLUMN IF NOT EXISTS neighborhood_id INTEGER REFERENCES neighborhoods(neighborhood_id);
        """))

        # Update roads using neighborhood_name_normalized matching
        conn.execute(text("""
            UPDATE roads r
            SET neighborhood_id = n.neighborhood_id
            FROM neighborhoods n
            WHERE r.neighborhood = n.neighborhood_name_normalized
               OR r.neighborhood || ' MAHALLESİ' = n.neighborhood_name_normalized;
        """))

        conn.commit()

        # Check stats
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(neighborhood_id) as matched
            FROM roads
        """))
        stats = result.fetchone()
        logger.info(f"✓ Updated roads: {stats.matched}/{stats.total} matched")


def show_summary(engine):
    """Show summary statistics."""
    logger.info("\n" + "=" * 60)
    logger.info("DATABASE SUMMARY")
    logger.info("=" * 60)

    with engine.connect() as conn:
        # Neighborhoods count
        result = conn.execute(text("SELECT COUNT(*) FROM neighborhoods"))
        logger.info(f"Neighborhoods: {result.fetchone()[0]}")

        # Addresses count
        result = conn.execute(text("SELECT COUNT(*) FROM addresses"))
        logger.info(f"Addresses: {result.fetchone()[0]}")

        # Sample neighborhoods
        logger.info("\nSample Neighborhoods:")
        result = conn.execute(text("""
            SELECT
                neighborhood_name,
                population,
                garbage_truck_type,
                days_collected_per_week,
                total_containers
            FROM neighborhoods
            ORDER BY population DESC NULLS LAST
            LIMIT 5
        """))
        for row in result:
            logger.info(f"  {row.neighborhood_name}: {row.population:,} people, {row.total_containers} containers, {row.garbage_truck_type}, {row.days_collected_per_week} days/week")


def main():
    """Main setup function."""
    logger.info("=" * 60)
    logger.info("STANDARDIZING NEIGHBORHOODS DATABASE")
    logger.info("=" * 60)
    logger.info("")

    engine = get_engine()

    # Step 1: Create tables
    create_tables(engine)

    # Step 2: Load and merge neighborhood data
    neighborhoods = load_and_merge_neighborhood_data()

    # Step 3: Insert neighborhoods
    neighborhood_map = insert_neighborhoods(engine, neighborhoods)

    # Step 4: Insert addresses
    insert_addresses(engine, neighborhood_map)

    # Step 5: Update roads table
    update_roads_table(engine)

    # Step 6: Show summary
    show_summary(engine)

    logger.info("\n" + "=" * 60)
    logger.info("✓ SETUP COMPLETE!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
