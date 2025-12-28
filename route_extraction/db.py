# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "sqlalchemy",
#     "psycopg2-binary",
#     "python-dotenv",
# ]
# ///

"""Database connection and session management."""

import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'trash_collection')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin123')

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_engine():
    """Get SQLAlchemy engine."""
    return create_engine(DB_URL)


def test_connection():
    """Test database connection."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            print("✓ Database connection successful!")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
