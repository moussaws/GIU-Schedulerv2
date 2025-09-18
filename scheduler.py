from typing import List, Dict, Optional, Tuple
from models import (Course, TA, TimeSlot, Day, SlotType, SchedulingPolicies,
                   SchedulingResult, GlobalSchedule, ScheduleAssignment)
from global_scheduler import GlobalScheduler
from workload_balancer import WorkloadBalancer
from conflict_resolver import ConflictResolver


class GIUScheduler:
    """
    Main interface for the GIU Staff Schedule Composer system.

    This class provides a high-level API for creating and managing course schedules
    with TA assignments, policy enforcement, and conflict resolution.
    """

    def __init__(self, policies: Optional[SchedulingPolicies] = None):
        self.policies = policies or SchedulingPolicies()
        self.global_scheduler = GlobalScheduler(self.policies)
        self.workload_balancer = WorkloadBalancer(self.policies)
        self.conflict_resolver = ConflictResolver()

    def create_schedule(self, courses: List[Course],
                       optimize: bool = True) -> SchedulingResult:
        """
        Create a global schedule for all courses.

        Args:
            courses: List of courses with assigned TAs and required slots
            optimize: Whether to apply workload balancing and optimization

        Returns:
            SchedulingResult containing the global schedule and metadata
        """
        if not courses:
            return SchedulingResult(
                global_schedule=GlobalSchedule(courses=[]),
                success=False,
                message="No courses provided"
            )

        result = self.global_scheduler.schedule_all_courses(courses)

        if optimize and result.success:
            result = self._optimize_schedule(result)

        return result

    def _optimize_schedule(self, result: SchedulingResult) -> SchedulingResult:
        """Apply optimization algorithms to improve the schedule."""
        if not result.global_schedule.assignments:
            return result

        balanced_assignments, balance_messages = self.workload_balancer.balance_workloads(
            result.global_schedule.assignments,
            result.global_schedule.courses
        )

        optimized_schedule = GlobalSchedule(
            courses=result.global_schedule.courses,
            assignments=balanced_assignments
        )

        new_conflicts = optimized_schedule.detect_conflicts()

        optimization_message = "; ".join(balance_messages) if balance_messages else "No optimization needed"

        return SchedulingResult(
            global_schedule=optimized_schedule,
            success=len(new_conflicts) == 0 and len(result.unassigned_slots) == 0,
            message=f"{result.message}; {optimization_message}",
            unassigned_slots=result.unassigned_slots,
            policy_violations=result.policy_violations
        )

    def resolve_conflicts(self, result: SchedulingResult,
                         auto_resolve: bool = True) -> SchedulingResult:
        """
        Resolve conflicts in an existing schedule.

        Args:
            result: Existing scheduling result with potential conflicts
            auto_resolve: Whether to automatically resolve conflicts

        Returns:
            Updated scheduling result with conflicts resolved
        """
        if result.success:
            return result

        conflicts = self.conflict_resolver.detect_all_conflicts(result.global_schedule.assignments)

        if auto_resolve:
            resolved_assignments, resolution_messages = self.conflict_resolver.resolve_conflicts_automatically(conflicts)

            resolved_schedule = GlobalSchedule(
                courses=result.global_schedule.courses,
                assignments=resolved_assignments
            )

            remaining_conflicts = resolved_schedule.detect_conflicts()

            success = len(remaining_conflicts) == 0 and len(result.unassigned_slots) == 0
            message = f"{result.message}; {'; '.join(resolution_messages)}"

            return SchedulingResult(
                global_schedule=resolved_schedule,
                success=success,
                message=message,
                unassigned_slots=result.unassigned_slots,
                policy_violations=result.policy_violations
            )
        else:
            manual_suggestions = self.conflict_resolver.suggest_manual_resolutions(conflicts)
            conflict_summary = self.conflict_resolver.get_conflict_summary(conflicts)

            message = f"{result.message}; {conflict_summary['total_conflicts']} conflicts detected"

            return SchedulingResult(
                global_schedule=result.global_schedule,
                success=False,
                message=message,
                unassigned_slots=result.unassigned_slots,
                policy_violations=result.policy_violations + [str(manual_suggestions)]
            )

    def update_policies(self, new_policies: SchedulingPolicies):
        """Update scheduling policies and recreate schedulers."""
        self.policies = new_policies
        self.global_scheduler = GlobalScheduler(self.policies)
        self.workload_balancer = WorkloadBalancer(self.policies)

    def get_schedule_statistics(self, result: SchedulingResult) -> Dict[str, any]:
        """Get comprehensive statistics about a schedule."""
        basic_stats = self.global_scheduler.get_schedule_statistics(result)
        workload_report = self.workload_balancer.get_workload_report(result.global_schedule.assignments)

        return {
            **basic_stats,
            "workload_balance": workload_report,
            "success_rate": len(result.global_schedule.assignments) / max(
                sum(len(course.required_slots) for course in result.global_schedule.courses), 1
            ),
            "policies_active": {
                "tutorial_lab_independence": self.policies.tutorial_lab_independence,
                "tutorial_lab_equal_count": self.policies.tutorial_lab_equal_count,
                "tutorial_lab_number_matching": self.policies.tutorial_lab_number_matching,
                "fairness_mode": self.policies.fairness_mode
            }
        }

    def suggest_improvements(self, result: SchedulingResult) -> List[str]:
        """Generate suggestions for improving the schedule."""
        suggestions = []

        if not result.success:
            suggestions.append("Schedule has conflicts or unassigned slots - consider resolving these first")

        if result.unassigned_slots:
            suggestions.extend([
                f"Consider adding more TAs to courses with unassigned slots",
                f"Review TA availability for conflicting time periods",
                f"Consider adjusting course timing requirements"
            ])

        workload_suggestions = self.workload_balancer.suggest_workload_improvements(
            result.global_schedule.assignments
        )
        suggestions.extend(workload_suggestions)

        stats = self.get_schedule_statistics(result)
        if stats.get("success_rate", 0) < 0.8:
            suggestions.append("Consider hiring additional TAs to improve coverage")

        if stats.get("workload_balance", {}).get("imbalance_score", 0) > 3:
            suggestions.append("Enable fairness mode to better balance TA workloads")

        return suggestions

    def export_schedule(self, result: SchedulingResult, format_type: str = "grid") -> str:
        """
        Export schedule in different formats.

        Args:
            result: Scheduling result to export
            format_type: "grid", "list", or "csv"

        Returns:
            Formatted schedule string
        """
        if format_type == "grid":
            return self._export_as_grid(result)
        elif format_type == "list":
            return self._export_as_list(result)
        elif format_type == "csv":
            return self._export_as_csv(result)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

    def _export_as_grid(self, result: SchedulingResult) -> str:
        """Export schedule as a visual grid."""
        grid = result.global_schedule.get_schedule_grid()

        output = ["GIU Staff Schedule Composer - Weekly Grid\n"]
        output.append("=" * 60)

        days = [Day.SATURDAY, Day.SUNDAY, Day.MONDAY, Day.TUESDAY, Day.WEDNESDAY, Day.THURSDAY]
        slots = range(1, 6)

        output.append(f"{'Time':<12} " + " | ".join(f"{day.value.title():<12}" for day in days))
        output.append("-" * 80)

        for slot_num in slots:
            row = [f"Slot {slot_num}"]

            for day in days:
                key = (day, slot_num)
                if key in grid:
                    assignments = grid[key]
                    cell_content = "; ".join(f"{a.ta.name}({a.course.name})" for a in assignments[:2])
                    if len(assignments) > 2:
                        cell_content += "..."
                else:
                    cell_content = "-"
                row.append(f"{cell_content:<12}"[:12])

            output.append(" | ".join(row))

        return "\n".join(output)

    def _export_as_list(self, result: SchedulingResult) -> str:
        """Export schedule as a detailed list."""
        output = ["GIU Staff Schedule Composer - Assignment List\n"]
        output.append("=" * 50)

        by_course = {}
        for assignment in result.global_schedule.assignments:
            course_id = assignment.course.id
            if course_id not in by_course:
                by_course[course_id] = []
            by_course[course_id].append(assignment)

        for course_id, assignments in by_course.items():
            course_name = assignments[0].course.name
            output.append(f"\n{course_name} ({course_id}):")
            output.append("-" * 30)

            for assignment in sorted(assignments, key=lambda a: (a.slot.day.value, a.slot.slot_number)):
                output.append(f"  {assignment.slot} -> {assignment.ta.name}")

        return "\n".join(output)

    def _export_as_csv(self, result: SchedulingResult) -> str:
        """Export schedule as CSV format."""
        output = ["Course,TA,Day,Slot,Type,Duration"]

        for assignment in result.global_schedule.assignments:
            row = [
                assignment.course.name,
                assignment.ta.name,
                assignment.slot.day.value,
                str(assignment.slot.slot_number),
                assignment.slot.slot_type.value,
                str(assignment.slot.duration)
            ]
            output.append(",".join(row))

        return "\n".join(output)