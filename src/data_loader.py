"""
data_loader.py - Robust data loading and parsing for CampusSpace.
Reads rooms, class schedules, events, and room requests.
"""

import os
from typing import Dict, Any, Tuple
import pandas as pd

def get_data_dir() -> str:
    """Return absolute path to the data directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    return os.path.join(parent_dir, 'data')

def load_all_datasets(data_dir: str = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load all 4 CSV datasets and return cleaned DataFrames:
    rooms_df, class_schedule_df, events_df, requests_df
    """
    if data_dir is None:
        data_dir = get_data_dir()

    rooms_path = os.path.join(data_dir, 'rooms.csv')
    classes_path = os.path.join(data_dir, 'class_schedule.csv')
    events_path = os.path.join(data_dir, 'events.csv')
    requests_path = os.path.join(data_dir, 'room_requests.csv')

    # Verify existence
    for path, name in [(rooms_path, 'rooms.csv'), 
                       (classes_path, 'class_schedule.csv'), 
                       (events_path, 'events.csv'), 
                       (requests_path, 'room_requests.csv')]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing required dataset file: {name} at {path}")

    # 1. Load Rooms
    rooms_df = pd.read_csv(rooms_path)
    rooms_df['capacity'] = pd.to_numeric(rooms_df['capacity'], errors='coerce').fillna(0).astype(int)
    rooms_df['projector'] = pd.to_numeric(rooms_df['projector'], errors='coerce').fillna(0).astype(int)
    rooms_df['computers'] = pd.to_numeric(rooms_df['computers'], errors='coerce').fillna(0).astype(int)
    rooms_df['accessible'] = pd.to_numeric(rooms_df['accessible'], errors='coerce').fillna(0).astype(int)
    rooms_df['power_outlets'] = pd.to_numeric(rooms_df['power_outlets'], errors='coerce').fillna(0).astype(int)
    rooms_df['floor'] = pd.to_numeric(rooms_df['floor'], errors='coerce').fillna(0).astype(int)

    # 2. Load Class Schedule
    class_df = pd.read_csv(classes_path)
    class_df['start_hour'] = pd.to_numeric(class_df['start_hour'], errors='coerce').fillna(0).astype(int)
    class_df['duration_hours'] = pd.to_numeric(class_df['duration_hours'], errors='coerce').fillna(1).astype(int)
    class_df['end_hour'] = class_df['start_hour'] + class_df['duration_hours']
    class_df['expected_attendance'] = pd.to_numeric(class_df['expected_attendance'], errors='coerce').fillna(0).astype(int)
    class_df['weekday'] = class_df['weekday'].astype(str).str.strip().str.capitalize().str[:3]

    # 3. Load Events
    events_df = pd.read_csv(events_path)
    events_df['start_time_dt'] = pd.to_datetime(events_df['start_time'], errors='coerce')
    events_df['event_date'] = events_df['start_time_dt'].dt.strftime('%Y-%m-%d')
    events_df['start_hour'] = events_df['start_time_dt'].dt.hour
    events_df['duration_hours'] = pd.to_numeric(events_df['duration_hours'], errors='coerce').fillna(1).astype(int)
    events_df['end_hour'] = events_df['start_hour'] + events_df['duration_hours']
    events_df['expected_attendance'] = pd.to_numeric(events_df['expected_attendance'], errors='coerce').fillna(0).astype(int)
    events_df['actual_attendance'] = pd.to_numeric(events_df['actual_attendance'], errors='coerce').fillna(0).astype(int)
    events_df['weekday'] = events_df['start_time_dt'].dt.strftime('%a')

    # 4. Load Room Requests
    requests_df = pd.read_csv(requests_path)
    requests_df['request_date'] = pd.to_datetime(requests_df['request_date'], errors='coerce').dt.strftime('%Y-%m-%d')
    requests_df['start_hour'] = pd.to_numeric(requests_df['start_hour'], errors='coerce').fillna(0).astype(int)
    requests_df['duration_hours'] = pd.to_numeric(requests_df['duration_hours'], errors='coerce').fillna(1).astype(int)
    requests_df['end_hour'] = requests_df['start_hour'] + requests_df['duration_hours']
    requests_df['required_capacity'] = pd.to_numeric(requests_df['required_capacity'], errors='coerce').fillna(0).astype(int)
    requests_df['projector_required'] = pd.to_numeric(requests_df['projector_required'], errors='coerce').fillna(0).astype(int)
    requests_df['computers_required'] = pd.to_numeric(requests_df['computers_required'], errors='coerce').fillna(0).astype(int)
    requests_df['status'] = requests_df['status'].astype(str).str.strip().str.capitalize()
    requests_df['purpose'] = requests_df['purpose'].astype(str).str.strip()

    return rooms_df, class_df, events_df, requests_df
