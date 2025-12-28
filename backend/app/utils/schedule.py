"""Schedule creation utilities."""

from datetime import datetime, timedelta
from typing import List


def create_schedule_for_week(week_start: datetime, collection_days: List[str]) -> List[dict]:
    """Create collection schedule for the week based on actual collection days.

    Args:
        week_start: Start date of the week
        collection_days: List of day names for collection (e.g., ['Monday', 'Wednesday'])

    Returns:
        List of schedule dictionaries with date, day_name, and time information
    """
    day_map = {
        'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
        'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
    }

    default_start_hour = 6
    default_end_hour = 14

    schedule = []
    for day_name in collection_days:
        day_name = day_name.strip()
        if day_name not in day_map:
            continue

        target_weekday = day_map[day_name]
        days_ahead = target_weekday - week_start.weekday()
        if days_ahead < 0:
            days_ahead += 7

        collection_date = week_start + timedelta(days=days_ahead)

        schedule.append({
            'date': collection_date.strftime('%Y-%m-%d'),
            'day_name': day_name,
            'start_hour': default_start_hour,
            'end_hour': default_end_hour,
            'start_time': f"{default_start_hour:02d}:00",
            'end_time': f"{default_end_hour:02d}:00"
        })

    return schedule
