"""
Unit tests for recommendation.py ranking and filtering logic.
"""

import pytest
import pandas as pd
from src.recommendation import find_room_recommendations

def test_capacity_filtering():
    rooms = pd.DataFrame([
        {'room_id': 'R01', 'building': 'East', 'floor': 1, 'room_type': 'Classroom', 'capacity': 20,
         'projector': 1, 'computers': 0, 'accessible': 1, 'power_outlets': 10},
        {'room_id': 'R02', 'building': 'East', 'floor': 1, 'room_type': 'Classroom', 'capacity': 60,
         'projector': 1, 'computers': 0, 'accessible': 1, 'power_outlets': 10},
    ])
    classes = pd.DataFrame(columns=['schedule_id', 'room_id', 'course_code', 'weekday',
                                     'start_hour', 'end_hour', 'duration_hours', 'department', 'expected_attendance'])
    events = pd.DataFrame(columns=['event_id', 'room_id', 'event_type', 'event_date',
                                    'start_hour', 'end_hour', 'duration_hours', 'expected_attendance', 'actual_attendance'])

    result = find_room_recommendations(
        date_str="2025-09-01",
        start_hour=10,
        duration_hours=2,
        required_capacity=50,
        rooms_df=rooms,
        class_df=classes,
        events_df=events
    )

    assert result['total_feasible'] == 1
    assert result['top_recommendations'][0]['room_id'] == 'R02'
    assert result['infeasible_rooms'][0]['room_id'] == 'R01'
    assert 'Insufficient capacity' in result['infeasible_rooms'][0]['rejection_reasons'][0]


def test_facility_filtering():
    rooms = pd.DataFrame([
        {'room_id': 'R01', 'building': 'West', 'floor': 2, 'room_type': 'Lab', 'capacity': 40,
         'projector': 0, 'computers': 1, 'accessible': 1, 'power_outlets': 8},
        {'room_id': 'R02', 'building': 'West', 'floor': 2, 'room_type': 'Lab', 'capacity': 40,
         'projector': 1, 'computers': 1, 'accessible': 1, 'power_outlets': 8},
    ])
    classes = pd.DataFrame(columns=['schedule_id', 'room_id', 'course_code', 'weekday',
                                     'start_hour', 'end_hour', 'duration_hours', 'department', 'expected_attendance'])
    events = pd.DataFrame(columns=['event_id', 'room_id', 'event_type', 'event_date',
                                    'start_hour', 'end_hour', 'duration_hours', 'expected_attendance', 'actual_attendance'])

    result = find_room_recommendations(
        date_str="2025-09-01",
        start_hour=14,
        duration_hours=1,
        required_capacity=30,
        projector_required=True,
        rooms_df=rooms,
        class_df=classes,
        events_df=events
    )

    assert result['total_feasible'] == 1
    assert result['top_recommendations'][0]['room_id'] == 'R02'
    assert "Missing required digital projector" in result['infeasible_rooms'][0]['rejection_reasons'][0]


def test_scheduling_conflict():
    """Test that a room with a confirmed schedule conflict is correctly rejected."""
    rooms = pd.DataFrame([
        {'room_id': 'R01', 'building': 'North', 'floor': 1, 'room_type': 'Classroom', 'capacity': 30,
         'projector': 1, 'computers': 0, 'accessible': 1, 'power_outlets': 5},
        {'room_id': 'R02', 'building': 'North', 'floor': 1, 'room_type': 'Classroom', 'capacity': 30,
         'projector': 1, 'computers': 0, 'accessible': 1, 'power_outlets': 5},
    ])
    # R01 has a Mon 10-12 class; R02 is free all day
    classes = pd.DataFrame([{
        'schedule_id': 'S01', 'room_id': 'R01', 'course_code': 'MATH101',
        'weekday': 'Mon', 'start_hour': 10, 'duration_hours': 2, 'end_hour': 12,
        'department': 'Sciences', 'expected_attendance': 25
    }])
    events = pd.DataFrame(columns=['event_id', 'room_id', 'event_type', 'event_date',
                                    'start_hour', 'end_hour', 'duration_hours', 'expected_attendance', 'actual_attendance'])

    # 2025-09-01 was a Monday — request overlaps class
    result = find_room_recommendations(
        date_str="2025-09-01",
        start_hour=10,
        duration_hours=2,
        required_capacity=20,
        rooms_df=rooms,
        class_df=classes,
        events_df=events
    )

    # R01 is rejected due to conflict; R02 is free
    assert result['total_feasible'] == 1
    assert result['top_recommendations'][0]['room_id'] == 'R02'
    conflict_rooms = [r for r in result['infeasible_rooms'] if r['room_id'] == 'R01']
    assert len(conflict_rooms) == 1
    assert any('Schedule conflict' in reason for reason in conflict_rooms[0]['rejection_reasons'])


def test_empty_state_and_alternatives():
    """Test that when NO room is feasible due to computers_required=True, alternatives are suggested.
    Scenario: 2 rooms, both have computers=0 (failing hard constraint).
    One room (R01) is also blocked by schedule Mon 10-12.
    R02 is free on schedule — so relaxing computers_required=False should find R02 as alternative.
    """
    rooms = pd.DataFrame([
        {'room_id': 'R01', 'building': 'North', 'floor': 1, 'room_type': 'Classroom', 'capacity': 30,
         'projector': 1, 'computers': 0, 'accessible': 1, 'power_outlets': 5},
        {'room_id': 'R02', 'building': 'North', 'floor': 1, 'room_type': 'Classroom', 'capacity': 30,
         'projector': 1, 'computers': 0, 'accessible': 1, 'power_outlets': 5},
    ])
    # Only R01 is busy Mon 10-12; R02 is free
    classes = pd.DataFrame([
        {'schedule_id': 'S01', 'room_id': 'R01', 'course_code': 'CS101', 'weekday': 'Mon',
         'start_hour': 10, 'duration_hours': 2, 'end_hour': 12, 'department': 'CSE', 'expected_attendance': 25},
    ])
    events = pd.DataFrame(columns=['event_id', 'room_id', 'event_type', 'event_date',
                                    'start_hour', 'end_hour', 'duration_hours', 'expected_attendance', 'actual_attendance'])

    # computers_required=True: both rooms have computers=0 -> both fail hard constraint
    # But when we relax computers_required=False, R02 (schedule-free) becomes feasible
    result = find_room_recommendations(
        date_str="2025-09-01",   # Monday
        start_hour=10,
        duration_hours=2,
        required_capacity=20,
        computers_required=True,
        rooms_df=rooms,
        class_df=classes,
        events_df=events
    )

    assert result['total_feasible'] == 0
    assert len(result['infeasible_rooms']) == 2
    # Alternatives should suggest relaxing the computer constraint (R02 is free schedule-wise)
    assert len(result['alternatives']) > 0
    # The alternative should mention relaxing computers
    assert any('computer' in alt['suggestion'].lower() or 'workstation' in alt['suggestion'].lower()
               for alt in result['alternatives'])
