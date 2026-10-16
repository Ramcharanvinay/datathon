"""
availability.py - Time-conflict checking and room availability evaluation.
"""

from datetime import datetime
from typing import Tuple, List, Dict, Any
import pandas as pd

def parse_weekday_from_date(date_str: str) -> str:
    """Extract 3-letter weekday from YYYY-MM-DD (e.g., 'Mon', 'Tue')."""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%a')
    except Exception:
        return ""

def intervals_overlap(start1: float, end1: float, start2: float, end2: float) -> bool:
    """
    Standard open overlap check:
    existing_start < requested_end AND existing_end > requested_start
    Adjacent intervals where one ends when the other begins DO NOT conflict.
    """
    return (start1 < end2) and (end1 > start2)

def check_room_conflicts(room_id: str, date_str: str, start_hour: float,
                         duration_hours: float, class_df: pd.DataFrame,
                         events_df: pd.DataFrame) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Check if a specific room has conflicts on a given date during [start_hour, start_hour + duration_hours].
    Checks recurring classes for that weekday and specific dated events.
    """
    if duration_hours <= 0 or start_hour < 0 or start_hour >= 24:
        return False, [{"type": "Invalid Interval", "description": "Invalid requested time interval."}]

    end_hour = start_hour + duration_hours
    conflicts = []

    # 1. Weekly Class Schedule check — guard against empty or unstructured DataFrames
    weekday = parse_weekday_from_date(date_str)
    if weekday and not class_df.empty and 'room_id' in class_df.columns and 'weekday' in class_df.columns:
        room_classes = class_df[(class_df['room_id'] == room_id) & (class_df['weekday'] == weekday)]
        for _, row in room_classes.iterrows():
            c_start = row['start_hour']
            c_end = row['end_hour']
            if intervals_overlap(c_start, c_end, start_hour, end_hour):
                conflicts.append({
                    "source": "Class Schedule",
                    "identifier": row.get('schedule_id', 'Class'),
                    "course_code": row.get('course_code', 'N/A'),
                    "department": row.get('department', 'N/A'),
                    "start": c_start,
                    "end": c_end,
                    "weekday": weekday,
                    "expected_attendance": row.get('expected_attendance', 0)
                })

    # 2. One-off Events check — guard against empty or unstructured DataFrames
    if not events_df.empty and 'event_date' in events_df.columns and 'room_id' in events_df.columns:
        room_events = events_df[(events_df['room_id'] == room_id) & (events_df['event_date'] == date_str)]
        for _, row in room_events.iterrows():
            e_start = row['start_hour']
            e_end = row['end_hour']
            if intervals_overlap(e_start, e_end, start_hour, end_hour):
                conflicts.append({
                    "source": "Campus Event",
                    "identifier": row.get('event_id', 'Event'),
                    "event_type": row.get('event_type', 'N/A'),
                    "start": e_start,
                    "end": e_end,
                    "date": date_str,
                    "expected_attendance": row.get('expected_attendance', 0),
                    "actual_attendance": row.get('actual_attendance', 0)
                })

    is_available = len(conflicts) == 0
    return is_available, conflicts


def get_room_day_timeline(room_id: str, date_str: str,
                          class_df: pd.DataFrame, events_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Get all booked/scheduled slots for a room on a given day to render timeline visual.
    """
    weekday = parse_weekday_from_date(date_str)
    bookings = []

    # Classes — guard against empty DataFrames
    if weekday and not class_df.empty and 'room_id' in class_df.columns:
        room_classes = class_df[(class_df['room_id'] == room_id) & (class_df['weekday'] == weekday)]
        for _, row in room_classes.iterrows():
            bookings.append({
                "source": "Class",
                "label": f"{row.get('course_code', 'Class')} ({row.get('department', '')})",
                "start": row['start_hour'],
                "end": row['end_hour'],
                "type": "Class"
            })

    # Events — guard against empty DataFrames
    if not events_df.empty and 'event_date' in events_df.columns and 'room_id' in events_df.columns:
        room_events = events_df[(events_df['room_id'] == room_id) & (events_df['event_date'] == date_str)]
        for _, row in room_events.iterrows():
            bookings.append({
                "source": "Event",
                "label": f"{row.get('event_type', 'Event')}",
                "start": row['start_hour'],
                "end": row['end_hour'],
                "type": "Event"
            })

    bookings.sort(key=lambda x: x['start'])
    return bookings
