from typing import List, Dict, Set, Tuple, Optional
from models import ScheduleAssignment, Course, TA, TimeSlot, Day, SlotType
from dataclasses import dataclass


@dataclass
class ConflictInfo:
    assignments: List[ScheduleAssignment]
    conflict_type: str
    severity: int
    resolution_suggestions: List[str]


class ConflictResolver:
    def __init__(self):
        self.conflict_types = {
            "ta_double_booking": "TA assigned to multiple slots at same time",
            "overcapacity": "More assignments than TA capacity allows",
            "policy_violation": "Assignment violates scheduling policies",
            "preference_ignored": "Assignment ignores TA preferences"
        }

    def detect_all_conflicts(self, assignments: List[ScheduleAssignment]) -> List[ConflictInfo]:
        conflicts = []
        conflicts.extend(self._detect_double_bookings(assignments))
        conflicts.extend(self._detect_overcapacity(assignments))
        conflicts.extend(self._detect_policy_violations(assignments))
        return conflicts

    def _detect_double_bookings(self, assignments: List[ScheduleAssignment]) -> List[ConflictInfo]:
        conflicts = []
        time_slot_map = {}

        for assignment in assignments:
            key = (assignment.ta.id, assignment.slot.day, assignment.slot.slot_number)
            if key not in time_slot_map:
                time_slot_map[key] = []
            time_slot_map[key].append(assignment)

        for key, slot_assignments in time_slot_map.items():
            if len(slot_assignments) > 1:
                ta_name = slot_assignments[0].ta.name
                day = slot_assignments[0].slot.day.value
                slot_num = slot_assignments[0].slot.slot_number

                suggestions = [
                    f"Remove one of the conflicting assignments",
                    f"Move one assignment to a different time slot",
                    f"Assign a different TA to one of the courses"
                ]

                conflicts.append(ConflictInfo(
                    assignments=slot_assignments,
                    conflict_type="ta_double_booking",
                    severity=10,
                    resolution_suggestions=suggestions
                ))

        return conflicts

    def _detect_overcapacity(self, assignments: List[ScheduleAssignment]) -> List[ConflictInfo]:
        conflicts = []
        ta_workloads = {}

        for assignment in assignments:
            ta_id = assignment.ta.id
            if ta_id not in ta_workloads:
                ta_workloads[ta_id] = {
                    'ta': assignment.ta,
                    'assignments': [],
                    'total_hours': 0
                }
            ta_workloads[ta_id]['assignments'].append(assignment)
            ta_workloads[ta_id]['total_hours'] += assignment.slot.duration

        for ta_id, workload_info in ta_workloads.items():
            ta = workload_info['ta']
            total_hours = workload_info['total_hours']

            if total_hours > ta.max_weekly_hours:
                excess_hours = total_hours - ta.max_weekly_hours
                suggestions = [
                    f"Remove assignments totaling {excess_hours} hours",
                    f"Increase {ta.name}'s maximum weekly hours",
                    f"Redistribute assignments to other TAs"
                ]

                conflicts.append(ConflictInfo(
                    assignments=workload_info['assignments'],
                    conflict_type="overcapacity",
                    severity=8,
                    resolution_suggestions=suggestions
                ))

        return conflicts

    def _detect_policy_violations(self, assignments: List[ScheduleAssignment]) -> List[ConflictInfo]:
        conflicts = []
        ta_course_assignments = {}

        for assignment in assignments:
            key = (assignment.ta.id, assignment.course.id)
            if key not in ta_course_assignments:
                ta_course_assignments[key] = {
                    'ta': assignment.ta,
                    'course': assignment.course,
                    'assignments': []
                }
            ta_course_assignments[key]['assignments'].append(assignment)

        return conflicts

    def resolve_conflicts_automatically(self, conflicts: List[ConflictInfo]) -> Tuple[List[ScheduleAssignment], List[str]]:
        if not conflicts:
            return [], []

        all_assignments = []
        for conflict in conflicts:
            all_assignments.extend(conflict.assignments)

        unique_assignments = list({id(a): a for a in all_assignments}.values())

        sorted_conflicts = sorted(conflicts, key=lambda c: c.severity, reverse=True)

        resolved_assignments = unique_assignments.copy()
        resolution_messages = []

        for conflict in sorted_conflicts:
            if conflict.conflict_type == "ta_double_booking":
                resolved, message = self._resolve_double_booking(conflict, resolved_assignments)
                resolved_assignments = resolved
                resolution_messages.append(message)

            elif conflict.conflict_type == "overcapacity":
                resolved, message = self._resolve_overcapacity(conflict, resolved_assignments)
                resolved_assignments = resolved
                resolution_messages.append(message)

        return resolved_assignments, resolution_messages

    def _resolve_double_booking(self, conflict: ConflictInfo, current_assignments: List[ScheduleAssignment]) -> Tuple[List[ScheduleAssignment], str]:
        conflicting_assignments = [a for a in current_assignments if a in conflict.assignments]

        if len(conflicting_assignments) <= 1:
            return current_assignments, "No double booking to resolve"

        best_assignment = self._select_best_assignment(conflicting_assignments)

        resolved_assignments = [a for a in current_assignments if a not in conflicting_assignments]
        resolved_assignments.append(best_assignment)

        removed_count = len(conflicting_assignments) - 1
        ta_name = best_assignment.ta.name
        slot_info = f"{best_assignment.slot.day.value} slot {best_assignment.slot.slot_number}"

        return resolved_assignments, f"Resolved double booking for {ta_name} at {slot_info} (removed {removed_count} assignments)"

    def _resolve_overcapacity(self, conflict: ConflictInfo, current_assignments: List[ScheduleAssignment]) -> Tuple[List[ScheduleAssignment], str]:
        overcapacity_assignments = [a for a in current_assignments if a in conflict.assignments]

        if not overcapacity_assignments:
            return current_assignments, "No overcapacity to resolve"

        ta = overcapacity_assignments[0].ta
        total_hours = sum(a.slot.duration for a in overcapacity_assignments)
        excess_hours = total_hours - ta.max_weekly_hours

        if excess_hours <= 0:
            return current_assignments, f"No overcapacity for {ta.name}"

        sorted_assignments = sorted(overcapacity_assignments,
                                  key=lambda a: self._assignment_removal_priority(a))

        kept_assignments = []
        kept_hours = 0

        for assignment in sorted_assignments:
            if kept_hours + assignment.slot.duration <= ta.max_weekly_hours:
                kept_assignments.append(assignment)
                kept_hours += assignment.slot.duration
            else:
                break

        other_assignments = [a for a in current_assignments if a not in overcapacity_assignments]
        resolved_assignments = other_assignments + kept_assignments

        removed_count = len(overcapacity_assignments) - len(kept_assignments)

        return resolved_assignments, f"Resolved overcapacity for {ta.name} (removed {removed_count} assignments)"

    def _select_best_assignment(self, assignments: List[ScheduleAssignment]) -> ScheduleAssignment:
        def assignment_score(assignment: ScheduleAssignment) -> float:
            score = 0.0

            if assignment.slot in assignment.ta.preferred_slots:
                preference_rank = assignment.ta.preferred_slots[assignment.slot]
                score += max(0, 10 - preference_rank)

            course_urgency = len(assignment.course.required_slots) / max(len(assignment.course.assigned_tas), 1)
            score += course_urgency

            ta_utilization = assignment.ta.get_total_assigned_hours() / assignment.ta.max_weekly_hours
            if ta_utilization < 0.8:
                score += 2

            return score

        return max(assignments, key=assignment_score)

    def _assignment_removal_priority(self, assignment: ScheduleAssignment) -> float:
        priority = 0.0

        if assignment.slot in assignment.ta.preferred_slots:
            preference_rank = assignment.ta.preferred_slots[assignment.slot]
            priority -= max(0, 10 - preference_rank)

        course_flexibility = len(assignment.course.assigned_tas) / max(len(assignment.course.required_slots), 1)
        priority += course_flexibility

        return priority

    def suggest_manual_resolutions(self, conflicts: List[ConflictInfo]) -> Dict[str, List[str]]:
        suggestions = {}

        for i, conflict in enumerate(conflicts):
            conflict_id = f"conflict_{i}_{conflict.conflict_type}"
            suggestions[conflict_id] = conflict.resolution_suggestions.copy()

            if conflict.conflict_type == "ta_double_booking":
                assignments = conflict.assignments
                ta_name = assignments[0].ta.name
                courses = list(set(a.course.name for a in assignments))

                suggestions[conflict_id].extend([
                    f"Consider increasing {ta_name}'s availability",
                    f"Review course timing for: {', '.join(courses)}",
                    "Check if any courses can be moved to different time slots"
                ])

            elif conflict.conflict_type == "overcapacity":
                ta = conflict.assignments[0].ta
                suggestions[conflict_id].extend([
                    f"Consider hiring additional TAs for courses assigned to {ta.name}",
                    f"Review if {ta.name} can increase weekly hour limit",
                    "Redistribute some assignments to underutilized TAs"
                ])

        return suggestions

    def get_conflict_summary(self, conflicts: List[ConflictInfo]) -> Dict[str, int]:
        summary = {}
        for conflict in conflicts:
            conflict_type = conflict.conflict_type
            summary[conflict_type] = summary.get(conflict_type, 0) + 1

        summary['total_conflicts'] = len(conflicts)
        summary['high_severity'] = sum(1 for c in conflicts if c.severity >= 8)
        summary['medium_severity'] = sum(1 for c in conflicts if 5 <= c.severity < 8)
        summary['low_severity'] = sum(1 for c in conflicts if c.severity < 5)

        return summary