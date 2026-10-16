"""
recommendation.py - Two-stage explainable room recommendation engine.
Stage 1: Hard constraint filtering (capacity, facilities, room type, conflicts).
Stage 2: Multicriteria scoring & ranking with transparent evidence explanations.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from .availability import check_room_conflicts

def find_room_recommendations(
    date_str: str,
    start_hour: int,
    duration_hours: int,
    required_capacity: int,
    projector_required: bool = False,
    computers_required: bool = False,
    accessible_required: bool = False,
    preferred_type: Optional[str] = None,
    preferred_building: Optional[str] = None,
    rooms_df: pd.DataFrame = None,
    class_df: pd.DataFrame = None,
    events_df: pd.DataFrame = None,
    _recursion_depth: int = 0  # prevent infinite recursion in alternatives
) -> Dict[str, Any]:
    """
    Execute 2-stage recommendation engine.
    Returns:
        {
            'feasible_rooms': [...],
            'infeasible_rooms': [...],
            'top_recommendations': [...],
            'alternatives': [...]
        }
    """
    if rooms_df is None or class_df is None or events_df is None:
        raise ValueError("DataFrames must be provided to recommendation engine.")

    feasible_rooms = []
    infeasible_rooms = []

    # Stage 1: Hard Constraint Evaluation
    for _, room in rooms_df.iterrows():
        room_id = room['room_id']
        cap = int(room['capacity'])
        has_proj = int(room['projector']) == 1
        has_comp = int(room['computers']) == 1
        has_access = int(room['accessible']) == 1
        r_type = room['room_type']
        building = room['building']
        outlets = int(room.get('power_outlets', 0))

        failed_reasons = []

        # 1. Capacity constraint
        if cap < required_capacity:
            failed_reasons.append(f"Insufficient capacity ({cap} < {required_capacity} requested)")

        # 2. Facility constraints
        if projector_required and not has_proj:
            failed_reasons.append("Missing required digital projector")
        if computers_required and not has_comp:
            failed_reasons.append("Missing required computer workstations")
        if accessible_required and not has_access:
            failed_reasons.append("Lacks wheelchair accessibility")

        # 3. Room type constraint (if strict)
        if preferred_type and preferred_type != "Any" and r_type.lower() != preferred_type.lower():
            failed_reasons.append(f"Room type mismatch (is {r_type}, requested {preferred_type})")

        # 4. Schedule Conflict check
        is_free, conflicts = check_room_conflicts(
            room_id=room_id,
            date_str=date_str,
            start_hour=start_hour,
            duration_hours=duration_hours,
            class_df=class_df,
            events_df=events_df
        )

        if not is_free:
            conflict_descriptions = [
                f"{c['source']}: {c.get('course_code', c.get('event_type', 'Booking'))} "
                f"({c['start']}:00-{c['end']}:00)" for c in conflicts
            ]
            failed_reasons.append(f"Schedule conflict ({', '.join(conflict_descriptions)})")

        room_entry = {
            'room_id': room_id,
            'building': building,
            'floor': int(room['floor']),
            'room_type': r_type,
            'capacity': cap,
            'projector': has_proj,
            'computers': has_comp,
            'accessible': has_access,
            'power_outlets': outlets,
            'is_available': is_free,
            'conflicts': conflicts
        }

        if len(failed_reasons) == 0:
            feasible_rooms.append(room_entry)
        else:
            room_entry['rejection_reasons'] = failed_reasons
            infeasible_rooms.append(room_entry)

    # Stage 2: Multicriteria Scoring for Feasible Rooms
    scored_candidates = []
    for r in feasible_rooms:
        excess_cap = r['capacity'] - required_capacity
        # Linear decay: lose 0.5 points per excess seat, minimum 40
        cap_score = max(40.0, 100.0 - (excess_cap * 0.5))

        # Facilities bonus
        outlets_score = min(10.0, r['power_outlets'] * 0.5)
        facilities_score = 70.0 + outlets_score
        if r['accessible']:
            facilities_score += 10.0
        if r['projector']:
            facilities_score += 5.0
        if r['computers']:
            facilities_score += 5.0
        facilities_score = min(100.0, facilities_score)

        # Building preference score
        building_score = 80.0
        if preferred_building and preferred_building != "Any":
            if r['building'].lower() == preferred_building.lower():
                building_score = 100.0
            else:
                building_score = 60.0

        # Weighted composite: 50% capacity efficiency, 30% facilities, 20% location
        composite_score = (cap_score * 0.50) + (facilities_score * 0.30) + (building_score * 0.20)
        composite_score = round(min(100.0, max(0.0, composite_score)), 1)

        explanation = (
            f"Recommended because Room {r['room_id']} ({r['room_type']}) in {r['building']} Building "
            f"(Floor {r['floor']}) comfortably fits {required_capacity} attendees "
            f"(capacity: {r['capacity']} with {excess_cap} spare seats), "
            f"meets all facility requirements, and has zero schedule conflicts for "
            f"{date_str} from {start_hour}:00 to {start_hour + duration_hours}:00."
        )

        scored_candidates.append({
            **r,
            'score': composite_score,
            'capacity_score': round(cap_score, 1),
            'facilities_score': round(facilities_score, 1),
            'building_score': round(building_score, 1),
            'excess_capacity': excess_cap,
            'explanation': explanation
        })

    # Sort descending by composite score, then ascending by excess capacity
    scored_candidates.sort(key=lambda x: (x['score'], -x['excess_capacity']), reverse=True)

    # Assign tier labels to top candidates
    for i, candidate in enumerate(scored_candidates):
        if i == 0:
            candidate['match_tier'] = "Best Fit"
        elif i == 1:
            candidate['match_tier'] = "Strong Alternative"
        elif i == 2:
            candidate['match_tier'] = "Good Option"
        else:
            candidate['match_tier'] = "Feasible"

    top_3 = scored_candidates[:3]

    # If 0 feasible rooms, generate alternatives (only at top level to avoid infinite recursion)
    alternatives = []
    if len(scored_candidates) == 0 and _recursion_depth < 2:
        kwargs_base = dict(
            date_str=date_str, duration_hours=duration_hours,
            required_capacity=required_capacity,
            projector_required=projector_required,
            accessible_required=accessible_required,
            preferred_type=preferred_type, preferred_building=preferred_building,
            rooms_df=rooms_df, class_df=class_df, events_df=events_df,
            _recursion_depth=_recursion_depth + 1
        )

        # Alternative 1: Relax computer requirement
        if computers_required:
            alt = find_room_recommendations(start_hour=start_hour, computers_required=False, **kwargs_base)
            if alt['top_recommendations']:
                alternatives.append({
                    "suggestion": "Relax Computer Requirement: Workstations are scarce. If students bring personal laptops, rooms become available.",
                    "sample_room": alt['top_recommendations'][0]['room_id']
                })

        # Alternative 2: Shift start time +1 hour
        if start_hour + duration_hours + 1 <= 22:
            alt2 = find_room_recommendations(start_hour=start_hour + 1, computers_required=computers_required, **kwargs_base)
            if alt2['top_recommendations']:
                alternatives.append({
                    "suggestion": f"Shift start time to {start_hour + 1}:00 — {start_hour + 1 + duration_hours}:00: Several rooms open up right after the current peak slot.",
                    "sample_room": alt2['top_recommendations'][0]['room_id']
                })
        # Also try -1 hour
        elif start_hour > 8:
            alt2b = find_room_recommendations(start_hour=start_hour - 1, computers_required=computers_required, **kwargs_base)
            if alt2b['top_recommendations']:
                alternatives.append({
                    "suggestion": f"Try an earlier slot at {start_hour - 1}:00 — {start_hour - 1 + duration_hours}:00: More rooms available before peak hours.",
                    "sample_room": alt2b['top_recommendations'][0]['room_id']
                })

        # Alternative 3: Relax room type
        if preferred_type and preferred_type != "Any":
            alt3 = find_room_recommendations(start_hour=start_hour, computers_required=computers_required,
                                              preferred_type="Any", **{k: v for k, v in kwargs_base.items()
                                                                        if k != 'preferred_type'})
            if alt3['top_recommendations']:
                alternatives.append({
                    "suggestion": f"Open to all room types: A {alt3['top_recommendations'][0]['room_type']} room matches all other requirements.",
                    "sample_room": alt3['top_recommendations'][0]['room_id']
                })

    return {
        'feasible_rooms': scored_candidates,
        'infeasible_rooms': infeasible_rooms,
        'top_recommendations': top_3,
        'total_feasible': len(scored_candidates),
        'total_infeasible': len(infeasible_rooms),
        'alternatives': alternatives
    }
