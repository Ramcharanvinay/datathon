"""
Unit tests for availability.py and conflict detection logic.
"""

import pytest
import pandas as pd
from src.availability import intervals_overlap, check_room_conflicts, parse_weekday_from_date

# Common empty DataFrames with proper columns (required for guard checks)
EMPTY_CLASS_DF = pd.DataFrame(columns=[
    'schedule_id', 'room_id', 'course_code', 'weekday',
    'start_hour', 'end_hour', 'duration_hours', 'department', 'expected_attendance'
])
EMPTY_EVENT_DF = pd.DataFrame(columns=[
    'event_id', 'room_id', 'event_type', 'event_date',
    'start_hour', 'end_hour', 'duration_hours', 'expected_attendance', 'actual_attendance'
])


def test_intervals_overlap():
    # Exactly overlapping
    assert intervals_overlap(9, 11, 10, 12) is True
    # Fully enclosed
    assert intervals_overlap(9, 14, 10, 12) is True
    # Enclosing
    assert intervals_overlap(10, 12, 9, 14) is True
    # Completely disjoint before
    assert intervals_overlap(8, 10, 10, 12) is False
    # Completely disjoint after
    assert intervals_overlap(12, 14, 10, 12) is False
    # Adjacent boundary — ends at 10:00, next starts at 10:00 -> NO overlap
    assert intervals_overlap(8, 10, 10, 12) is False
    assert intervals_overlap(10, 12, 8, 10) is False


def test_weekday_parsing():
    # 2025-08-04 was Monday
    assert parse_weekday_from_date("2025-08-04") == "Mon"
    # 2025-08-05 was Tuesday
    assert parse_weekday_from_date("2025-08-05") == "Tue"
    # 2025-08-08 was Friday
    assert parse_weekday_from_date("2025-08-08") == "Fri"
    # Invalid format returns empty string
    assert parse_weekday_from_date("not-a-date") == ""


def test_room_class_conflict():
    class_data = pd.DataFrame([{
        'schedule_id': 'S001',
        'room_id': 'R001',
        'course_code': 'CS101',
        'weekday': 'Mon',
        'start_hour': 10,
        'duration_hours': 2,
        'end_hour': 12,
        'department': 'CSE',
        'expected_attendance': 40
    }])

    # Conflicting interval on Monday 2025-08-04 (11:00-13:00 overlaps 10:00-12:00)
    is_free, conflicts = check_room_conflicts('R001', '2025-08-04', 11, 2, class_data, EMPTY_EVENT_DF)
    assert is_free is False
    assert len(conflicts) == 1
    assert conflicts[0]['course_code'] == 'CS101'

    # Non-conflicting adjacent interval on Monday (12:00-14:00 is adjacent to 10:00-12:00)
    is_free, conflicts = check_room_conflicts('R001', '2025-08-04', 12, 2, class_data, EMPTY_EVENT_DF)
    assert is_free is True
    assert len(conflicts) == 0

    # Non-conflicting weekday (Tuesday 2025-08-05 at 10:00-12:00)
    is_free, conflicts = check_room_conflicts('R001', '2025-08-05', 10, 2, class_data, EMPTY_EVENT_DF)
    assert is_free is True
    assert len(conflicts) == 0


def test_room_event_conflict():
    # Empty class df with proper column schema
    class_data = EMPTY_CLASS_DF.copy()
    events_data = pd.DataFrame([{
        'event_id': 'EV001',
        'room_id': 'R002',
        'event_type': 'Workshop',
        'event_date': '2025-09-10',
        'start_hour': 14,
        'duration_hours': 3,
        'end_hour': 17,
        'expected_attendance': 50,
        'actual_attendance': 45
    }])

    # Conflicting on same date 2025-09-10 during 15:00-16:00
    is_free, conflicts = check_room_conflicts('R002', '2025-09-10', 15, 1, class_data, events_data)
    assert is_free is False
    assert len(conflicts) == 1
    assert conflicts[0]['event_type'] == 'Workshop'

    # Different date 2025-09-11 — no conflict
    is_free, conflicts = check_room_conflicts('R002', '2025-09-11', 15, 1, class_data, events_data)
    assert is_free is True
    assert len(conflicts) == 0
