from typing import List, Dict, Optional, Tuple
from models import Course, TA, TimeSlot, ScheduleAssignment, SchedulingPolicies
from policy_validator import PolicyValidator
import random


class CourseScheduler:
    def __init__(self, policies: SchedulingPolicies):
        self.policies = policies
        self.validator = PolicyValidator(policies)

    def schedule_course(self, course: Course) -> Tuple[List[ScheduleAssignment], List[str]]:
        if not course.assigned_tas or not course.required_slots:
            return [], ["No TAs assigned or no slots defined for course"]

        assignments = []
        violations = []
        unassigned_slots = course.required_slots.copy()

        if self.policies.fairness_mode:
            assignments, violations = self._schedule_with_fairness(course, unassigned_slots)
        else:
            assignments, violations = self._schedule_greedy(course, unassigned_slots)

        if unassigned_slots:
            violations.append(f"Could not assign {len(unassigned_slots)} slots: {[str(slot) for slot in unassigned_slots]}")

        return assignments, violations

    def _schedule_greedy(self, course: Course, unassigned_slots: List[TimeSlot]) -> Tuple[List[ScheduleAssignment], List[str]]:
        assignments = []
        violations = []

        for ta in course.assigned_tas:
            max_assignable_hours = ta.get_remaining_capacity()
            if max_assignable_hours < 2:  # Need at least 2 hours for one slot
                continue

            max_assignable_slots = max_assignable_hours // 2

            valid_combinations = self.validator.get_valid_slot_combinations(ta, course, max_assignable_slots)

            if not valid_combinations:
                continue

            best_combination = self._select_best_combination(ta, valid_combinations)

            assigned_slots = []
            for slot in best_combination:
                if slot in unassigned_slots:
                    assignments.append(ScheduleAssignment(ta=ta, slot=slot, course=course))
                    assigned_slots.append(slot)
                    unassigned_slots.remove(slot)

            if assigned_slots:
                is_valid, slot_violations = self.validator.validate_assignment(ta, course, assigned_slots)
                if not is_valid:
                    violations.extend(slot_violations)

            ta.current_assignments[course.id] = assigned_slots

        return assignments, violations

    def _schedule_with_fairness(self, course: Course, unassigned_slots: List[TimeSlot]) -> Tuple[List[ScheduleAssignment], List[str]]:
        assignments = []
        violations = []

        available_tas = [ta for ta in course.assigned_tas if ta.get_remaining_capacity() >= 2]

        if not available_tas:
            return assignments, ["No TAs with available capacity"]

        target_hours_per_ta = course.get_total_hours() // len(available_tas)

        assignments_per_ta = {ta.id: [] for ta in available_tas}

        sorted_slots = self._sort_slots_by_difficulty(unassigned_slots, available_tas)

        for slot in sorted_slots:
            if slot not in unassigned_slots:
                continue

            eligible_tas = [ta for ta in available_tas
                          if ta.is_available_for_slot(slot) and
                          len(assignments_per_ta[ta.id]) * 2 < target_hours_per_ta + 2]

            if not eligible_tas:
                eligible_tas = [ta for ta in available_tas if ta.is_available_for_slot(slot)]

            if not eligible_tas:
                continue

            chosen_ta = min(eligible_tas, key=lambda ta: len(assignments_per_ta[ta.id]))

            assignment = ScheduleAssignment(ta=chosen_ta, slot=slot, course=course)
            assignments.append(assignment)
            assignments_per_ta[chosen_ta.id].append(slot)
            unassigned_slots.remove(slot)

        for ta in available_tas:
            assigned_slots = assignments_per_ta[ta.id]
            if assigned_slots:
                is_valid, slot_violations = self.validator.validate_assignment(ta, course, assigned_slots)
                if not is_valid:
                    violations.extend(slot_violations)
                ta.current_assignments[course.id] = assigned_slots

        return assignments, violations

    def _select_best_combination(self, ta: TA, combinations: List[List[TimeSlot]]) -> List[TimeSlot]:
        if not combinations:
            return []

        def score_combination(combo: List[TimeSlot]) -> float:
            score = 0.0
            for slot in combo:
                if slot in ta.preferred_slots:
                    preference_rank = ta.preferred_slots[slot]
                    score += max(0, 10 - preference_rank)
                else:
                    score += 5

            # Bonus for larger combinations to prefer assigning more slots
            bonus = len(combo) * 0.5
            return score + bonus

        return max(combinations, key=score_combination)

    def _sort_slots_by_difficulty(self, slots: List[TimeSlot], tas: List[TA]) -> List[TimeSlot]:
        def difficulty_score(slot: TimeSlot) -> int:
            available_count = sum(1 for ta in tas if ta.is_available_for_slot(slot))
            return -available_count

        return sorted(slots, key=difficulty_score)

    def optimize_assignments(self, course: Course, assignments: List[ScheduleAssignment]) -> List[ScheduleAssignment]:
        if not self.policies.fairness_mode:
            return assignments

        ta_workloads = {}
        for assignment in assignments:
            ta_id = assignment.ta.id
            ta_workloads[ta_id] = ta_workloads.get(ta_id, 0) + assignment.slot.duration

        if not ta_workloads:
            return assignments

        mean_workload = sum(ta_workloads.values()) / len(ta_workloads)
        std_dev = (sum((w - mean_workload) ** 2 for w in ta_workloads.values()) / len(ta_workloads)) ** 0.5

        if std_dev <= 1.0:
            return assignments

        improved_assignments = self._rebalance_assignments(assignments, ta_workloads, mean_workload)
        return improved_assignments

    def _rebalance_assignments(self, assignments: List[ScheduleAssignment],
                             workloads: Dict[str, int], target: float) -> List[ScheduleAssignment]:
        overloaded = [(ta_id, load) for ta_id, load in workloads.items() if load > target + 2]
        underloaded = [(ta_id, load) for ta_id, load in workloads.items() if load < target - 2]

        if not overloaded or not underloaded:
            return assignments

        new_assignments = assignments.copy()
        random.shuffle(new_assignments)

        for over_ta_id, _ in overloaded:
            for under_ta_id, _ in underloaded:
                over_assignments = [a for a in new_assignments if a.ta.id == over_ta_id]

                for assignment in over_assignments:
                    under_ta = next((ta for ta in assignment.course.assigned_tas if ta.id == under_ta_id), None)
                    if under_ta and under_ta.is_available_for_slot(assignment.slot):
                        assignment.ta = under_ta
                        workloads[over_ta_id] -= assignment.slot.duration
                        workloads[under_ta_id] += assignment.slot.duration
                        break

                if abs(workloads[over_ta_id] - target) <= 2:
                    break

        return new_assignments