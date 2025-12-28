# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas",
# ]
# ///

"""Utility functions for route extraction."""

from datetime import datetime
from math import radians, sin, cos, sqrt, atan2


def parse_datetime(date_str, time_str):
    """
    Parse Turkish date/time format to datetime.

    Args:
        date_str: Date in format DD.MM.YYYY
        time_str: Time in format HH:MM:SS
    """
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M:%S")
        return dt
    except:
        return None


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two GPS points using Haversine formula.

    Returns distance in kilometers.
    """
    R = 6371  # Earth radius in km

    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def create_linestring_wkt(gps_points):
    """
    Create WKT LineString from GPS points.

    Args:
        gps_points: List of dicts with 'lat' and 'lon' keys
    """
    if len(gps_points) < 2:
        return None

    coords = [f"{point['lon']} {point['lat']}" for point in gps_points]
    return f"LINESTRING({', '.join(coords)})"
