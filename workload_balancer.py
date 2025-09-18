from typing import List, Dict, Tuple, Set, Optional
from models import ScheduleAssignment, Course, TA, TimeSlot, SchedulingPolicies
from policy_validator import PolicyValidator
import statistics
from dataclasses import dataclass


@dataclass
class WorkloadStats:
    ta_id: str
    ta_name: str
    current_hours: int
    max_hours: int
    utilization_rate: float
    course_count: int
    assignments: List[ScheduleAssignment]


class WorkloadBalancer:
    def __init__(self, policies: SchedulingPolicies):
        self.policies = policies
        self.validator = PolicyValidator(policies)

    def balance_workloads(self, assignments: List[ScheduleAssignment], courses: List[Course]) -> Tuple[List[ScheduleAssignment], List[str]]:
        if not assignments:
            return assignments, []

        workload_stats = self._calculate_workload_stats(assignments)
        imbalance_score = self._calculate_imbalance_score(workload_stats)

        if imbalance_score < 2.0:
            return assignments, [f"Workloads already balanced (imbalance score: {imbalance_score:.2f})"]

        balanced_assignments, messages = self._rebalance_assignments(assignments, workload_stats, courses)

        new_stats = self._calculate_workload_stats(balanced_assignments)
        new_imbalance = self._calculate_imbalance_score(new_stats)

        improvement = imbalance_score - new_imbalance
        final_message = f"Workload balancing completed. Imbalance reduced from {imbalance_score:.2f} to {new_imbalance:.2f}"
        messages.append(final_message)

        return balanced_assignments, messages

    def _calculate_workload_stats(self, assignments: List[ScheduleAssignment]) -> List[WorkloadStats]:
        ta_workloads = {}

        for assignment in assignments:
            ta_id = assignment.ta.id
            if ta_id not in ta_workloads:
                ta_workloads[ta_id] = {
                    'ta': assignment.ta,
                    'assignments': [],
                    'courses': set()
                }
            ta_workloads[ta_id]['assignments'].append(assignment)
            ta_workloads[ta_id]['courses'].add(assignment.course.id)

        stats = []
        for ta_id, data in ta_workloads.items():
            ta = data['ta']
            assignments_list = data['assignments']
            current_hours = sum(a.slot.duration for a in assignments_list)
            utilization_rate = current_hours / ta.max_weekly_hours if ta.max_weekly_hours > 0 else 0

            stats.append(WorkloadStats(
                ta_id=ta_id,
                ta_name=ta.name,
                current_hours=current_hours,
                max_hours=ta.max_weekly_hours,
                utilization_rate=utilization_rate,
                course_count=len(data['courses']),
                assignments=assignments_list
            ))

        return stats

    def _calculate_imbalance_score(self, stats: List[WorkloadStats]) -> float:
        if len(stats) <= 1:
            return 0.0

        utilization_rates = [stat.utilization_rate for stat in stats]
        mean_utilization = statistics.mean(utilization_rates)

        if mean_utilization == 0:
            return 0.0

        variance = statistics.variance(utilization_rates) if len(utilization_rates) > 1 else 0
        std_dev = variance ** 0.5

        coefficient_of_variation = std_dev / mean_utilization if mean_utilization > 0 else 0

        return coefficient_of_variation * 10

    def _rebalance_assignments(self, assignments: List[ScheduleAssignment],
                             stats: List[WorkloadStats], courses: List[Course]) -> Tuple[List[ScheduleAssignment], List[str]]:

        messages = []
        rebalanced_assignments = assignments.copy()

        if not self.policies.fairness_mode:
            return rebalanced_assignments, ["Fairness mode disabled, no rebalancing performed"]

        overloaded_tas = [stat for stat in stats if stat.utilization_rate > 0.85]
        underloaded_tas = [stat for stat in stats if stat.utilization_rate < 0.65]

        if not overloaded_tas or not underloaded_tas:
            return rebalanced_assignments, ["No imbalance detected requiring redistribution"]

        transfer_count = 0

        for overloaded_stat in overloaded_tas:
            target_reduction = overloaded_stat.current_hours - int(overloaded_stat.max_hours * 0.8)

            if target_reduction <= 0:
                continue

            transferable_assignments = self._find_transferable_assignments(
                overloaded_stat.assignments, underloaded_tas
            )

            for assignment, target_ta_id in transferable_assignments:
                if target_reduction <= 0:
                    break

                target_ta = next(ta for stat in underloaded_tas for ta in [stat] if stat.ta_id == target_ta_id).assignments[0].ta

                if self._can_transfer_assignment(assignment, target_ta):
                    self._transfer_assignment(assignment, target_ta, rebalanced_assignments)
                    target_reduction -= assignment.slot.duration
                    transfer_count += 1

                    self._update_stats_after_transfer(stats, assignment, target_ta)

                    messages.append(f"Transferred {assignment.slot} from {assignment.ta.name} to {target_ta.name}")

        if transfer_count == 0:
            messages.append("No assignments could be transferred due to constraints")

        return rebalanced_assignments, messages

    def _find_transferable_assignments(self, assignments: List[ScheduleAssignment],
                                     underloaded_tas: List[WorkloadStats]) -> List[Tuple[ScheduleAssignment, str]]:
        transferable = []

        non_preferred_assignments = [a for a in assignments
                                   if a.slot not in a.ta.preferred_slots]

        preferred_assignments = [a for a in assignments
                               if a.slot in a.ta.preferred_slots]

        candidates = non_preferred_assignments + preferred_assignments

        for assignment in candidates:
            for underloaded_stat in underloaded_tas:
                if underloaded_stat.current_hours + assignment.slot.duration <= underloaded_stat.max_hours:
                    target_ta = next(ta for a in underloaded_stat.assignments for ta in [a.ta])
                    if assignment.slot in target_ta.available_slots:
                        transferable.append((assignment, underloaded_stat.ta_id))
                        break

        return transferable

    def _can_transfer_assignment(self, assignment: ScheduleAssignment, target_ta: TA) -> bool:
        if not target_ta.is_available_for_slot(assignment.slot):
            return False

        if target_ta.get_remaining_capacity() < assignment.slot.duration:
            return False

        temp_assignments = target_ta.current_assignments.get(assignment.course.id, []) + [assignment.slot]

        is_valid, violations = self.validator.validate_assignment(target_ta, assignment.course, temp_assignments)

        return is_valid

    def _transfer_assignment(self, assignment: ScheduleAssignment, target_ta: TA,
                           all_assignments: List[ScheduleAssignment]):
        for i, a in enumerate(all_assignments):
            if (a.ta.id == assignment.ta.id and
                a.slot == assignment.slot and
                a.course.id == assignment.course.id):
                all_assignments[i] = ScheduleAssignment(
                    ta=target_ta,
                    slot=assignment.slot,
                    course=assignment.course
                )
                break

        if assignment.course.id not in target_ta.current_assignments:
            target_ta.current_assignments[assignment.course.id] = []
        target_ta.current_assignments[assignment.course.id].append(assignment.slot)

        if assignment.course.id in assignment.ta.current_assignments:
            try:
                assignment.ta.current_assignments[assignment.course.id].remove(assignment.slot)
            except ValueError:
                pass

    def _update_stats_after_transfer(self, stats: List[WorkloadStats],
                                   assignment: ScheduleAssignment, target_ta: TA):
        for stat in stats:
            if stat.ta_id == assignment.ta.id:
                stat.current_hours -= assignment.slot.duration
                stat.utilization_rate = stat.current_hours / stat.max_hours if stat.max_hours > 0 else 0
                stat.assignments = [a for a in stat.assignments if a != assignment]

            elif stat.ta_id == target_ta.id:
                stat.current_hours += assignment.slot.duration
                stat.utilization_rate = stat.current_hours / stat.max_hours if stat.max_hours > 0 else 0

    def get_workload_report(self, assignments: List[ScheduleAssignment]) -> Dict[str, any]:
        stats = self._calculate_workload_stats(assignments)
        imbalance_score = self._calculate_imbalance_score(stats)

        if not stats:
            return {"error": "No assignments to analyze"}

        utilization_rates = [stat.utilization_rate for stat in stats]
        hours_distribution = [stat.current_hours for stat in stats]

        return {
            "total_tas": len(stats),
            "imbalance_score": round(imbalance_score, 2),
            "average_utilization": round(statistics.mean(utilization_rates), 2) if utilization_rates else 0,
            "utilization_std_dev": round(statistics.stdev(utilization_rates), 2) if len(utilization_rates) > 1 else 0,
            "min_hours": min(hours_distribution) if hours_distribution else 0,
            "max_hours": max(hours_distribution) if hours_distribution else 0,
            "median_hours": statistics.median(hours_distribution) if hours_distribution else 0,
            "overloaded_tas": len([s for s in stats if s.utilization_rate > 0.85]),
            "underloaded_tas": len([s for s in stats if s.utilization_rate < 0.65]),
            "balanced_tas": len([s for s in stats if 0.65 <= s.utilization_rate <= 0.85]),
            "ta_details": [
                {
                    "name": stat.ta_name,
                    "hours": stat.current_hours,
                    "max_hours": stat.max_hours,
                    "utilization": round(stat.utilization_rate, 2),
                    "courses": stat.course_count
                }
                for stat in sorted(stats, key=lambda s: s.utilization_rate, reverse=True)
            ]
        }

    def suggest_workload_improvements(self, assignments: List[ScheduleAssignment]) -> List[str]:
        stats = self._calculate_workload_stats(assignments)
        suggestions = []

        overloaded = [s for s in stats if s.utilization_rate > 0.9]
        severely_underloaded = [s for s in stats if s.utilization_rate < 0.4]

        for stat in overloaded:
            excess_hours = stat.current_hours - int(stat.max_hours * 0.85)
            suggestions.append(f"Consider reducing {stat.ta_name}'s workload by {excess_hours} hours")

        for stat in severely_underloaded:
            additional_capacity = int(stat.max_hours * 0.7) - stat.current_hours
            suggestions.append(f"{stat.ta_name} can take on {additional_capacity} more hours")

        imbalance_score = self._calculate_imbalance_score(stats)
        if imbalance_score > 3.0:
            suggestions.append("Consider enabling fairness mode to automatically balance workloads")

        if len(set(stat.course_count for stat in stats)) > 1:
            suggestions.append("Consider redistributing courses to balance diversity across TAs")

        return suggestions