# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas",
#     "sqlalchemy",
#     "psycopg2-binary",
#     "python-dotenv",
# ]
# ///

"""Analyze road usage from collected routes."""

import pandas as pd
import logging
from sqlalchemy import text
from db import get_engine

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def get_most_used_roads(limit=20):
    """Get most used roads overall."""
    engine = get_engine()

    query = text("""
        SELECT
            road_id,
            road_name,
            neighborhood,
            times_used,
            length_m,
            last_visited
        FROM roads
        WHERE times_used > 0
        ORDER BY times_used DESC
        LIMIT :limit
    """)

    df = pd.read_sql(query, engine, params={'limit': limit})
    return df


def get_road_usage_by_neighborhood():
    """Get road usage statistics by neighborhood."""
    engine = get_engine()

    query = text("""
        SELECT
            neighborhood,
            COUNT(*) as total_roads,
            SUM(CASE WHEN times_used > 0 THEN 1 ELSE 0 END) as roads_used,
            SUM(times_used) as total_visits,
            ROUND(AVG(CASE WHEN times_used > 0 THEN times_used ELSE NULL END)::numeric, 1) as avg_visits,
            ROUND((SUM(length_m) / 1000.0)::numeric, 2) as total_length_km,
            ROUND(
                ((SUM(CASE WHEN times_used > 0 THEN 1 ELSE 0 END)::float / COUNT(*)::float) * 100)::numeric,
                1
            ) as coverage_percent
        FROM roads
        GROUP BY neighborhood
        ORDER BY total_visits DESC
    """)

    df = pd.read_sql(query, engine)
    return df


def get_most_used_roads_in_neighborhood(neighborhood, limit=10):
    """Get most used roads in a specific neighborhood."""
    engine = get_engine()

    query = text("""
        SELECT
            road_id,
            road_name,
            times_used,
            length_m,
            last_visited
        FROM roads
        WHERE neighborhood = :neighborhood
            AND times_used > 0
        ORDER BY times_used DESC
        LIMIT :limit
    """)

    df = pd.read_sql(query, engine, params={
        'neighborhood': neighborhood,
        'limit': limit
    })
    return df


def get_unused_roads():
    """Get roads that have never been used."""
    engine = get_engine()

    query = text("""
        SELECT
            neighborhood,
            COUNT(*) as unused_roads,
            ROUND(SUM(length_m) / 1000.0, 2) as unused_length_km
        FROM roads
        WHERE times_used = 0
        GROUP BY neighborhood
        ORDER BY unused_roads DESC
    """)

    df = pd.read_sql(query, engine)
    return df


def main():
    """Generate road usage report."""
    logger.info("=" * 60)
    logger.info("Road Usage Analysis Report")
    logger.info("=" * 60)

    # Overall most used roads
    logger.info("\n📊 Top 20 Most Used Roads")
    logger.info("-" * 60)
    most_used = get_most_used_roads(20)
    for _, row in most_used.iterrows():
        logger.info(f"{row['road_name']:30s} ({row['neighborhood']:15s}): {row['times_used']:4d} times")

    # Usage by neighborhood
    logger.info("\n🏘️  Road Usage by Neighborhood")
    logger.info("-" * 60)
    logger.info(f"{'Neighborhood':20s} {'Total':>6s} {'Used':>6s} {'Visits':>7s} {'Coverage':>9s}")
    logger.info("-" * 60)

    by_neighborhood = get_road_usage_by_neighborhood()
    for _, row in by_neighborhood.head(20).iterrows():
        logger.info(
            f"{row['neighborhood']:20s} "
            f"{row['total_roads']:6.0f} "
            f"{row['roads_used']:6.0f} "
            f"{row['total_visits']:7.0f} "
            f"{row['coverage_percent']:8.1f}%"
        )

    # Top 5 neighborhoods by coverage
    logger.info("\n🎯 Top 5 Neighborhoods by Coverage")
    logger.info("-" * 60)
    top_coverage = by_neighborhood.nlargest(5, 'coverage_percent')
    for _, row in top_coverage.iterrows():
        logger.info(
            f"{row['neighborhood']:20s}: {row['coverage_percent']:5.1f}% coverage "
            f"({row['roads_used']:.0f}/{row['total_roads']:.0f} roads)"
        )

    # Unused roads
    logger.info("\n❌ Neighborhoods with Most Unused Roads")
    logger.info("-" * 60)
    unused = get_unused_roads()
    for _, row in unused.head(10).iterrows():
        logger.info(
            f"{row['neighborhood']:20s}: {row['unused_roads']:4.0f} roads unused "
            f"({row['unused_length_km']:.1f} km)"
        )

    # Example: Most used roads in a specific neighborhood
    if not by_neighborhood.empty:
        top_neighborhood = by_neighborhood.iloc[0]['neighborhood']
        logger.info(f"\n🔍 Most Used Roads in {top_neighborhood}")
        logger.info("-" * 60)
        neighborhood_roads = get_most_used_roads_in_neighborhood(top_neighborhood, 10)
        for _, row in neighborhood_roads.iterrows():
            logger.info(
                f"{row['road_name']:30s}: {row['times_used']:4d} times, "
                f"{row['length_m']:.0f}m"
            )

    logger.info("\n" + "=" * 60)
    logger.info("✓ Analysis Complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
