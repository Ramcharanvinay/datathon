"""
data_validation.py - Dataset validation, schema verification, and integrity checking.
"""

from typing import Dict, Any, List
import pandas as pd

def validate_datasets(rooms_df: pd.DataFrame, class_df: pd.DataFrame, 
                      events_df: pd.DataFrame, requests_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run full integrity validation on the four campus space datasets.
    Returns metrics, warnings, and relationship validation details.
    """
    report = {
        'total_rooms': len(rooms_df),
        'unique_rooms': rooms_df['room_id'].nunique(),
        'total_class_records': len(class_df),
        'total_event_records': len(events_df),
        'total_request_records': len(requests_df),
        'warnings': [],
        'missing_values': {},
        'foreign_key_checks': {},
        'time_integrity_checks': {}
    }

    # 1. Missing values check
    report['missing_values']['rooms'] = rooms_df.isnull().sum().to_dict()
    report['missing_values']['class_schedule'] = class_df.isnull().sum().to_dict()
    report['missing_values']['events'] = events_df.isnull().sum().to_dict()
    report['missing_values']['requests'] = requests_df.isnull().sum().to_dict()

    # 2. Foreign Key Checks (rooms.room_id in class_schedule and events)
    room_ids_set = set(rooms_df['room_id'])
    
    classes_room_diff = set(class_df['room_id']) - room_ids_set
    report['foreign_key_checks']['classes_unmatched_rooms'] = len(classes_room_diff)
    if classes_room_diff:
        report['warnings'].append(f"Found {len(classes_room_diff)} unknown room IDs in class_schedule.csv.")

    events_room_diff = set(events_df['room_id']) - room_ids_set
    report['foreign_key_checks']['events_unmatched_rooms'] = len(events_room_diff)
    if events_room_diff:
        report['warnings'].append(f"Found {len(events_room_diff)} unknown room IDs in events.csv.")

    # 3. Time interval sanity checks
    invalid_classes = class_df[class_df['duration_hours'] <= 0]
    invalid_events = events_df[events_df['duration_hours'] <= 0]
    invalid_requests = requests_df[requests_df['duration_hours'] <= 0]

    report['time_integrity_checks']['invalid_class_durations'] = len(invalid_classes)
    report['time_integrity_checks']['invalid_event_durations'] = len(invalid_events)
    report['time_integrity_checks']['invalid_request_durations'] = len(invalid_requests)

    # 4. Duplicate checks
    report['duplicates'] = {
        'rooms': rooms_df.duplicated(subset=['room_id']).sum(),
        'class_schedule': class_df.duplicated(subset=['schedule_id']).sum(),
        'events': events_df.duplicated(subset=['event_id']).sum(),
        'requests': requests_df.duplicated(subset=['request_id']).sum()
    }

    return report


def get_data_dictionary() -> List[Dict[str, str]]:
    """Return formal data dictionary for all four files."""
    return [
        {"Dataset": "rooms.csv", "Column": "room_id", "Type": "String", "Description": "Unique room identifier (R001-R120)"},
        {"Dataset": "rooms.csv", "Column": "building", "Type": "Categorical", "Description": "Campus building (East, West, South, North, Central)"},
        {"Dataset": "rooms.csv", "Column": "floor", "Type": "Integer", "Description": "Floor level (0 = Ground to 5)"},
        {"Dataset": "rooms.csv", "Column": "room_type", "Type": "Categorical", "Description": "Type: Classroom, Lab, Seminar, Study room, Auditorium"},
        {"Dataset": "rooms.csv", "Column": "capacity", "Type": "Integer", "Description": "Maximum student seating capacity (15 to 179)"},
        {"Dataset": "rooms.csv", "Column": "projector", "Type": "Boolean/Int", "Description": "1 if digital projector is equipped, 0 otherwise"},
        {"Dataset": "rooms.csv", "Column": "computers", "Type": "Boolean/Int", "Description": "1 if computer workstations installed, 0 otherwise"},
        {"Dataset": "rooms.csv", "Column": "accessible", "Type": "Boolean/Int", "Description": "1 if ADA wheelchair accessible, 0 otherwise"},
        {"Dataset": "rooms.csv", "Column": "power_outlets", "Type": "Integer", "Description": "Count of available electrical power points"},
        
        {"Dataset": "class_schedule.csv", "Column": "schedule_id", "Type": "String", "Description": "Unique recurring class schedule entry ID (S00001-S05000)"},
        {"Dataset": "class_schedule.csv", "Column": "room_id", "Type": "String", "Description": "Assigned room ID (FK -> rooms.room_id)"},
        {"Dataset": "class_schedule.csv", "Column": "course_code", "Type": "String", "Description": "Academic course code (e.g. CS040)"},
        {"Dataset": "class_schedule.csv", "Column": "weekday", "Type": "Categorical", "Description": "Day of week (Mon, Tue, Wed, Thu, Fri, Sat)"},
        {"Dataset": "class_schedule.csv", "Column": "start_hour", "Type": "Integer", "Description": "24-hr start hour (e.g. 9 for 09:00)"},
        {"Dataset": "class_schedule.csv", "Column": "duration_hours", "Type": "Integer", "Description": "Class length in hours (1, 2, or 3)"},
        {"Dataset": "class_schedule.csv", "Column": "expected_attendance", "Type": "Integer", "Description": "Enrolled student attendance estimate"},
        {"Dataset": "class_schedule.csv", "Column": "department", "Type": "Categorical", "Description": "Academic department (Mechanical, CSE, ECE, EEE, Management, Sciences)"},
        
        {"Dataset": "events.csv", "Column": "event_id", "Type": "String", "Description": "Unique scheduled event ID (EV00001-EV01800)"},
        {"Dataset": "events.csv", "Column": "room_id", "Type": "String", "Description": "Host room ID (FK -> rooms.room_id)"},
        {"Dataset": "events.csv", "Column": "event_type", "Type": "Categorical", "Description": "Type: Exam, Guest lecture, Club meeting, Seminar, Workshop"},
        {"Dataset": "events.csv", "Column": "start_time", "Type": "Timestamp", "Description": "Timestamp (YYYY-MM-DD HH:MM:SS, Aug-Nov 2025)"},
        {"Dataset": "events.csv", "Column": "duration_hours", "Type": "Integer", "Description": "Event duration in hours (1 to 4)"},
        {"Dataset": "events.csv", "Column": "expected_attendance", "Type": "Integer", "Description": "Registered attendee estimate"},
        {"Dataset": "events.csv", "Column": "actual_attendance", "Type": "Integer", "Description": "Audited actual attendance count"},
        
        {"Dataset": "room_requests.csv", "Column": "request_id", "Type": "String", "Description": "Unique unallocated demand request (Q00001-Q05000)"},
        {"Dataset": "room_requests.csv", "Column": "request_date", "Type": "Date", "Description": "Requested date (YYYY-MM-DD)"},
        {"Dataset": "room_requests.csv", "Column": "start_hour", "Type": "Integer", "Description": "Requested start hour (8 to 20)"},
        {"Dataset": "room_requests.csv", "Column": "duration_hours", "Type": "Integer", "Description": "Requested booking duration (1 to 4)"},
        {"Dataset": "room_requests.csv", "Column": "required_capacity", "Type": "Integer", "Description": "Number of people needing seats"},
        {"Dataset": "room_requests.csv", "Column": "projector_required", "Type": "Boolean/Int", "Description": "1 if projector is mandatory"},
        {"Dataset": "room_requests.csv", "Column": "computers_required", "Type": "Boolean/Int", "Description": "1 if PCs are mandatory"},
        {"Dataset": "room_requests.csv", "Column": "purpose", "Type": "Categorical", "Description": "Purpose: Class, Club meeting, Project work, Study group, Workshop"},
        {"Dataset": "room_requests.csv", "Column": "status", "Type": "Categorical", "Description": "Demand status: Approved, Waitlisted, Cancelled, Rejected"}
    ]
