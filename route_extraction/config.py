# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "python-dotenv",
# ]
# ///

"""Configuration management."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv('DATA_DIR', '../../NB_hackathon_2025-main/Nilufer_bin_collection_dataset'))
GPS_DATA_PATH = DATA_DIR / os.getenv('GPS_DATA_FILE', 'all_merged_data.csv')
FLEET_DATA_PATH = DATA_DIR / os.getenv('FLEET_DATA_FILE', 'fleet.csv')

MIN_ROUTE_DURATION_MINUTES = int(os.getenv('MIN_ROUTE_DURATION_MINUTES', '15'))
MIN_ROUTE_DISTANCE_KM = float(os.getenv('MIN_ROUTE_DISTANCE_KM', '5.0'))
