# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "sqlalchemy",
#     "psycopg2-binary",
#     "python-dotenv",
# ]
# ///

"""Verify routes in database."""

from db import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM routes'))
    count = result.scalar()
    print(f'✓ Total routes in database: {count}')

    result = conn.execute(text('SELECT vehicle_id, COUNT(*) as route_count FROM routes GROUP BY vehicle_id ORDER BY route_count DESC LIMIT 5'))
    print('\nTop 5 vehicles by route count:')
    for row in result:
        print(f'  Vehicle {row.vehicle_id}: {row.route_count} routes')

    result = conn.execute(text('SELECT AVG(duration_minutes) as avg_duration, AVG(total_distance_km) as avg_distance FROM routes'))
    row = result.fetchone()
    print(f'\nAverage route duration: {row.avg_duration:.1f} minutes')
    print(f'Average route distance: {row.avg_distance:.1f} km')
