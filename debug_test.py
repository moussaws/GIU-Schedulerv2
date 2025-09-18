#!/usr/bin/env python3
"""
Debug test to understand why scheduling is failing.
"""

from models import (Course, TA, TimeSlot, Day, SlotType, SchedulingPolicies)
from policy_validator import PolicyValidator
from course_scheduler import CourseScheduler


def debug_simple_case():
    """Debug the simple scheduling case step by step."""
    print("=== Debug Simple Case ===")

    # Create simple slots
    slot1 = TimeSlot(Day.SUNDAY, 1, SlotType.TUTORIAL)
    slot2 = TimeSlot(Day.MONDAY, 1, SlotType.LAB)

    # Create TA
    ta = TA(
        id="ta_001",
        name="Test TA",
        max_weekly_hours=10,
        available_slots={slot1, slot2},
        preferred_slots={slot1: 1, slot2: 2}
    )

    # Create course
    course = Course(
        id="test_course",
        name="Test Course",
        required_slots=[slot1, slot2],
        assigned_tas=[ta]
    )

    print(f"TA capacity: {ta.get_remaining_capacity()} hours")
    print(f"TA is available for slot1: {ta.is_available_for_slot(slot1)}")
    print(f"TA is available for slot2: {ta.is_available_for_slot(slot2)}")

    # Test policy validator
    policies = SchedulingPolicies()
    validator = PolicyValidator(policies)

    max_slots = ta.get_remaining_capacity() // 2
    print(f"Max assignable slots: {max_slots}")

    valid_combinations = validator.get_valid_slot_combinations(ta, course, max_slots)
    print(f"Valid combinations: {len(valid_combinations)}")
    for i, combo in enumerate(valid_combinations):
        print(f"  Combo {i}: {[str(slot) for slot in combo]}")

    # Test course scheduler
    scheduler = CourseScheduler(policies)
    assignments, violations = scheduler.schedule_course(course)

    print(f"Assignments: {len(assignments)}")
    for assignment in assignments:
        print(f"  {assignment}")

    print(f"Violations: {violations}")

    return assignments, violations


if __name__ == "__main__":
    debug_simple_case()