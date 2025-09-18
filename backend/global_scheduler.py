from typing import List, Dict, Tuple, Set
from models import Course, TA, GlobalSchedule, ScheduleAssignment, SchedulingResult, SchedulingPolicies, Day
from course_scheduler import CourseScheduler


class GlobalScheduler:
    def __init__(self, policies: SchedulingPolicies):
        self.policies = policies
        self.course_scheduler = CourseScheduler(policies)

    def schedule_all_courses(self, courses: List[Course]) -> SchedulingResult:
        if not courses:
            return SchedulingResult(
                global_schedule=GlobalSchedule(courses=[]),
                success=False,
                message="No courses provided"
            )

        all_assignments = []
        all_violations = []
        unassigned_slots = []

        self._reset_ta_assignments(courses)

        sorted_courses = self._sort_courses_by_priority(courses)

        for course in sorted_courses:
            course_assignments, violations = self.course_scheduler.schedule_course(course)
            all_assignments.extend(course_assignments)
            all_violations.extend(violations)

            for slot in course.required_slots:
                if not any(assignment.slot == slot for assignment in course_assignments):
                    unassigned_slots.append((course, slot))

        global_schedule = GlobalSchedule(courses=courses, assignments=all_assignments)
        conflicts = global_schedule.detect_conflicts()

        success = len(conflicts) == 0 and len(unassigned_slots) == 0

        if conflicts:
            resolved_assignments, resolution_message = self._resolve_conflicts(all_assignments, conflicts)
            global_schedule.assignments = resolved_assignments
            all_violations.append(resolution_message)

        message = self._generate_summary_message(len(all_assignments), len(unassigned_slots), len(conflicts))

        return SchedulingResult(
            global_schedule=global_schedule,
            success=success,
            message=message,
            unassigned_slots=unassigned_slots,
            policy_violations=all_violations
        )

    def _reset_ta_assignments(self, courses: List[Course]):
        all_tas = set()
        for course in courses:
            all_tas.update(course.assigned_tas)

        for ta in all_tas:
            ta.current_assignments.clear()

    def _sort_courses_by_priority(self, courses: List[Course]) -> List[Course]:
        def priority_score(course: Course) -> Tuple[int, int, int]:
            total_slots = len(course.required_slots)
            available_tas = len([ta for ta in course.assigned_tas if ta.get_remaining_capacity() >= 2])
            difficulty_ratio = total_slots / max(available_tas, 1)

            return (
                -difficulty_ratio,
                -total_slots,
                -len(course.assigned_tas)
            )

        return sorted(courses, key=priority_score)

    def _resolve_conflicts(self, assignments: List[ScheduleAssignment], conflicts: List[str]) -> Tuple[List[ScheduleAssignment], str]:
        conflict_groups = self._group_conflicting_assignments(assignments)

        resolved_assignments = []
        removed_count = 0

        for group in conflict_groups:
            if len(group) > 1:
                best_assignment = self._select_best_assignment_from_conflict(group)
                resolved_assignments.append(best_assignment)
                removed_count += len(group) - 1
            else:
                resolved_assignments.append(group[0])

        non_conflicting = [a for a in assignments if not any(a in group for group in conflict_groups)]
        resolved_assignments.extend(non_conflicting)

        message = f"Resolved {len(conflict_groups)} conflicts by removing {removed_count} assignments"
        return resolved_assignments, message

    def _group_conflicting_assignments(self, assignments: List[ScheduleAssignment]) -> List[List[ScheduleAssignment]]:
        conflict_groups = []
        processed = set()

        for i, assignment1 in enumerate(assignments):
            if i in processed:
                continue

            group = [assignment1]
            processed.add(i)

            for j, assignment2 in enumerate(assignments[i + 1:], i + 1):
                if j in processed:
                    continue

                if self._assignments_conflict(assignment1, assignment2):
                    group.append(assignment2)
                    processed.add(j)

            if len(group) > 1:
                conflict_groups.append(group)

        return conflict_groups

    def _assignments_conflict(self, a1: ScheduleAssignment, a2: ScheduleAssignment) -> bool:
        return (a1.ta.id == a2.ta.id and
                a1.slot.day == a2.slot.day and
                a1.slot.slot_number == a2.slot.slot_number)

    def _select_best_assignment_from_conflict(self, conflicting_assignments: List[ScheduleAssignment]) -> ScheduleAssignment:
        def assignment_score(assignment: ScheduleAssignment) -> float:
            score = 0.0

            if assignment.slot in assignment.ta.preferred_slots:
                preference_rank = assignment.ta.preferred_slots[assignment.slot]
                score += max(0, 10 - preference_rank)

            course_priority = 1.0 / max(len(assignment.course.assigned_tas), 1)
            score += course_priority

            ta_workload_ratio = assignment.ta.get_total_assigned_hours() / assignment.ta.max_weekly_hours
            if ta_workload_ratio < 0.8:
                score += 2

            return score

        return max(conflicting_assignments, key=assignment_score)

    def _generate_summary_message(self, assigned_count: int, unassigned_count: int, conflict_count: int) -> str:
        parts = [f"Assigned {assigned_count} slots"]

        if unassigned_count > 0:
            parts.append(f"{unassigned_count} unassigned")

        if conflict_count > 0:
            parts.append(f"{conflict_count} conflicts resolved")

        return ", ".join(parts)

    def get_schedule_statistics(self, result: SchedulingResult) -> Dict[str, any]:
        if not result.global_schedule.assignments:
            return {"total_assignments": 0}

        ta_workloads = {}
        course_coverage = {}

        for assignment in result.global_schedule.assignments:
            ta_id = assignment.ta.id
            course_id = assignment.course.id

            ta_workloads[ta_id] = ta_workloads.get(ta_id, 0) + assignment.slot.duration

            if course_id not in course_coverage:
                course_coverage[course_id] = {"assigned": 0, "total": len(assignment.course.required_slots)}
            course_coverage[course_id]["assigned"] += 1

        avg_workload = sum(ta_workloads.values()) / len(ta_workloads) if ta_workloads else 0
        workload_variance = sum((w - avg_workload) ** 2 for w in ta_workloads.values()) / len(ta_workloads) if ta_workloads else 0

        coverage_rates = [info["assigned"] / info["total"] for info in course_coverage.values()]
        avg_coverage = sum(coverage_rates) / len(coverage_rates) if coverage_rates else 0

        return {
            "total_assignments": len(result.global_schedule.assignments),
            "total_tas": len(ta_workloads),
            "total_courses": len(course_coverage),
            "average_ta_workload": avg_workload,
            "workload_variance": workload_variance,
            "average_course_coverage": avg_coverage,
            "fully_covered_courses": sum(1 for rate in coverage_rates if rate >= 1.0),
            "conflicts_detected": len(result.global_schedule.conflicts),
            "policy_violations": len(result.policy_violations)
        }

    def optimize_global_schedule(self, result: SchedulingResult) -> SchedulingResult:
        if not result.success:
            return result

        optimized_assignments = self._balance_workloads(result.global_schedule.assignments)

        optimized_schedule = GlobalSchedule(
            courses=result.global_schedule.courses,
            assignments=optimized_assignments
        )

        new_conflicts = optimized_schedule.detect_conflicts()

        return SchedulingResult(
            global_schedule=optimized_schedule,
            success=len(new_conflicts) == 0,
            message=f"Optimized schedule: {result.message}",
            unassigned_slots=result.unassigned_slots,
            policy_violations=result.policy_violations
        )

    def _balance_workloads(self, assignments: List[ScheduleAssignment]) -> List[ScheduleAssignment]:
        if not self.policies.fairness_mode:
            return assignments

        ta_assignments = {}
        for assignment in assignments:
            ta_id = assignment.ta.id
            if ta_id not in ta_assignments:
                ta_assignments[ta_id] = []
            ta_assignments[ta_id].append(assignment)

        workloads = {ta_id: sum(a.slot.duration for a in assigns)
                    for ta_id, assigns in ta_assignments.items()}

        if not workloads:
            return assignments

        mean_workload = sum(workloads.values()) / len(workloads)

        balanced_assignments = []
        for ta_id, assigns in ta_assignments.items():
            current_workload = workloads[ta_id]
            if current_workload > mean_workload + 2:
                sorted_assigns = sorted(assigns, key=lambda a: a.slot in a.ta.preferred_slots, reverse=False)
                target_assigns = []
                current_hours = 0
                for assign in sorted_assigns:
                    if current_hours + assign.slot.duration <= mean_workload + 2:
                        target_assigns.append(assign)
                        current_hours += assign.slot.duration
                    else:
                        break
                balanced_assignments.extend(target_assigns)
            else:
                balanced_assignments.extend(assigns)

        return balanced_assignments