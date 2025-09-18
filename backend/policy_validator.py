from typing import List, Dict, Tuple
from models import Course, TA, TimeSlot, SchedulingPolicies, SlotType


class PolicyValidator:
    def __init__(self, policies: SchedulingPolicies):
        self.policies = policies

    def validate_assignment(self, ta: TA, course: Course, proposed_slots: List[TimeSlot]) -> Tuple[bool, List[str]]:
        violations = []

        # If independence is OFF, then policies can be applied
        if not self.policies.tutorial_lab_independence:
            if self.policies.tutorial_lab_equal_count:
                violations.extend(self._check_equal_count_policy(proposed_slots))

            if self.policies.tutorial_lab_number_matching:
                violations.extend(self._check_number_matching_policy(proposed_slots))

        return len(violations) == 0, violations

    def _check_equal_count_policy(self, slots: List[TimeSlot]) -> List[str]:
        violations = []
        tutorial_count = sum(1 for slot in slots if slot.slot_type == SlotType.TUTORIAL)
        lab_count = sum(1 for slot in slots if slot.slot_type == SlotType.LAB)

        if tutorial_count != lab_count:
            violations.append(f"Equal count policy violation: {tutorial_count} tutorials vs {lab_count} labs")

        return violations

    def _check_number_matching_policy(self, slots: List[TimeSlot]) -> List[str]:
        violations = []
        tutorial_numbers = set()
        lab_numbers = set()

        for slot in slots:
            if slot.slot_type == SlotType.TUTORIAL:
                tutorial_numbers.add(slot.slot_number)
            else:
                lab_numbers.add(slot.slot_number)

        unmatched_tutorials = tutorial_numbers - lab_numbers
        unmatched_labs = lab_numbers - tutorial_numbers

        if unmatched_tutorials:
            violations.append(f"Number matching policy violation: tutorials {unmatched_tutorials} have no matching labs")

        if unmatched_labs:
            violations.append(f"Number matching policy violation: labs {unmatched_labs} have no matching tutorials")

        return violations

    def get_valid_slot_combinations(self, ta: TA, course: Course, max_slots: int) -> List[List[TimeSlot]]:
        available_slots = [slot for slot in course.required_slots if ta.is_available_for_slot(slot)]

        if not available_slots:
            return []

        # If independence is ON, allow arbitrary combinations
        if self.policies.tutorial_lab_independence:
            return self._generate_independent_combinations(available_slots, max_slots)

        # If independence is OFF, apply specific policies
        combinations = []

        # Check which policies are enabled
        equal_count_enabled = self.policies.tutorial_lab_equal_count
        number_matching_enabled = self.policies.tutorial_lab_number_matching

        if equal_count_enabled and number_matching_enabled:
            # Both policies enabled: generate combinations that satisfy BOTH constraints
            equal_count_combinations = self._generate_equal_count_combinations(available_slots, max_slots)
            # Filter equal count combinations to only include those that also satisfy number matching
            for combo in equal_count_combinations:
                violations = self._check_number_matching_policy(combo)
                if not violations:  # No violations means it satisfies the policy
                    combinations.append(combo)
        elif equal_count_enabled:
            # Only equal count policy enabled
            combinations.extend(self._generate_equal_count_combinations(available_slots, max_slots))
        elif number_matching_enabled:
            # Only number matching policy enabled
            combinations.extend(self._generate_number_matching_combinations(available_slots, max_slots))
        else:
            # No specific policies enabled, allow independent combinations
            combinations = self._generate_independent_combinations(available_slots, max_slots)

        return combinations

    def _has_parallel_conflicts(self, slots: List[TimeSlot]) -> bool:
        """Check if any slots in the combination conflict (same day and slot number)"""
        slot_keys = set()
        for slot in slots:
            key = (slot.day, slot.slot_number)
            if key in slot_keys:
                return True  # Conflict found
            slot_keys.add(key)
        return False

    def _generate_independent_combinations(self, available_slots: List[TimeSlot], max_slots: int) -> List[List[TimeSlot]]:
        from itertools import combinations

        valid_combinations = []
        for r in range(1, min(max_slots + 1, len(available_slots) + 1)):
            for combo in combinations(available_slots, r):
                combo_list = list(combo)
                # Only add combinations that don't have parallel slot conflicts
                if not self._has_parallel_conflicts(combo_list):
                    valid_combinations.append(combo_list)

        return valid_combinations

    def _generate_equal_count_combinations(self, available_slots: List[TimeSlot], max_slots: int) -> List[List[TimeSlot]]:
        from itertools import combinations

        tutorials = [slot for slot in available_slots if slot.slot_type == SlotType.TUTORIAL]
        labs = [slot for slot in available_slots if slot.slot_type == SlotType.LAB]

        valid_combinations = []
        max_pairs = min(len(tutorials), len(labs), max_slots // 2)

        for pair_count in range(1, max_pairs + 1):
            for tutorial_combo in combinations(tutorials, pair_count):
                for lab_combo in combinations(labs, pair_count):
                    combination = list(tutorial_combo) + list(lab_combo)
                    if len(combination) <= max_slots and not self._has_parallel_conflicts(combination):
                        valid_combinations.append(combination)

        return valid_combinations

    def _generate_number_matching_combinations(self, available_slots: List[TimeSlot], max_slots: int) -> List[List[TimeSlot]]:
        tutorials = {slot.slot_number: slot for slot in available_slots if slot.slot_type == SlotType.TUTORIAL}
        labs = {slot.slot_number: slot for slot in available_slots if slot.slot_type == SlotType.LAB}

        matching_numbers = set(tutorials.keys()) & set(labs.keys())

        if not matching_numbers:
            return []

        from itertools import combinations

        valid_combinations = []
        max_pairs = min(len(matching_numbers), max_slots // 2)

        for pair_count in range(1, max_pairs + 1):
            for number_combo in combinations(matching_numbers, pair_count):
                combination = []
                for number in number_combo:
                    combination.extend([tutorials[number], labs[number]])

                if len(combination) <= max_slots and not self._has_parallel_conflicts(combination):
                    valid_combinations.append(combination)

        return valid_combinations