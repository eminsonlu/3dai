# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas",
#     "sqlalchemy",
#     "psycopg2-binary",
#     "python-dotenv",
#     "geopandas",
#     "shapely",
# ]
# ///

"""Load road network into database."""

import json
import logging
from sqlalchemy import text
from db import get_engine
from config import DATA_DIR

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROADS_FILE = DATA_DIR / "Yol-2025-12-16_13-38-47.json"


def create_roads_table(engine):
    """Create roads table with PostGIS support."""
    logger.info("Creating roads table...")

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS roads (
                road_id SERIAL PRIMARY KEY,
                road_name VARCHAR(200),
                neighborhood VARCHAR(100),
                length_m DECIMAL(10,2),
                width_m DECIMAL(10,2),
                land_value DECIMAL(15,2),
                road_line GEOMETRY(LINESTRING, 4326),

                -- Usage tracking
                times_used INTEGER DEFAULT 0,
                last_visited TIMESTAMP,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_roads_line
            ON roads USING GIST(road_line);
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_roads_neighborhood
            ON roads(neighborhood);
        """))

        conn.commit()
    logger.info("✓ Roads table created")


def load_roads(engine):
    """Load roads from JSON file."""
    logger.info(f"Loading roads from {ROADS_FILE}...")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM roads"))
        count = result.scalar()

    if count > 0:
        logger.info(f"✓ Roads already loaded ({count} roads)")
        return

    with open(ROADS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    features = data['features']
    logger.info(f"Found {len(features)} road features")

    inserted = 0
    with engine.connect() as conn:
        for feature in features:
            props = feature['properties']
            geom = feature['geometry']

            length_str = props.get('Yol Uzunluğu(m)', '0')
            length = float(length_str.replace(',', '.')) if length_str else 0

            width_str = props.get('Genişlik(m)', '0')
            if width_str and width_str != '0':
                width = float(width_str)
                # Cap unreasonable values (likely data errors)
                if width > 100:
                    width = 7  # Default for unreasonable values
            else:
                width = 7  # Default width

            land_value_str = props.get('2025 Arsa Birim Değeri (₺)', '0')
            land_value = float(land_value_str.replace(',', '.')) if land_value_str else 0

            coords = geom['coordinates']
            wkt_coords = ', '.join([f"{lon} {lat}" for lon, lat in coords])
            linestring_wkt = f"LINESTRING({wkt_coords})"

            conn.execute(text("""
                INSERT INTO roads (road_name, neighborhood, length_m, width_m, land_value, road_line)
                VALUES (:name, :neighborhood, :length, :width, :value, ST_GeomFromText(:wkt, 4326))
            """), {
                'name': props.get('Yol Adı', 'İsimsiz'),
                'neighborhood': props.get('İdari Mahalle Adı', ''),
                'length': length,
                'width': width,
                'value': land_value,
                'wkt': linestring_wkt
            })

            inserted += 1
            if inserted % 500 == 0:
                logger.info(f"  Inserted {inserted} roads...")

        conn.commit()

    logger.info(f"✓ Loaded {inserted} roads to database")


def main():
    """Main execution."""
    logger.info("=" * 50)
    logger.info("Road Network Loading")
    logger.info("=" * 50)

    engine = get_engine()

    create_roads_table(engine)
    load_roads(engine)

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total_roads,
                COUNT(DISTINCT neighborhood) as total_neighborhoods,
                SUM(length_m) as total_length_km
            FROM roads
        """))
        row = result.fetchone()

        logger.info("\n" + "=" * 50)
        logger.info("Road Network Statistics")
        logger.info("=" * 50)
        logger.info(f"Total roads: {row.total_roads}")
        logger.info(f"Neighborhoods: {row.total_neighborhoods}")
        logger.info(f"Total length: {row.total_length_km/1000:.1f} km")
        logger.info("=" * 50)


if __name__ == "__main__":
    main()
