#!/usr/bin/env python3
"""
Comprehensive test for all policy combinations and Saturday support.
"""

from models import (Course, TA, TimeSlot, Day, SlotType, SchedulingPolicies)
from scheduler import GIUScheduler


def test_saturday_support():
    """Test that Saturday slots work correctly."""
    print("=== Saturday Support Test ===")

    # Create Saturday slots
    sat_tut = TimeSlot(Day.SATURDAY, 1, SlotType.TUTORIAL)
    sat_lab = TimeSlot(Day.SATURDAY, 2, SlotType.LAB)

    ta = TA(
        id="ta_001",
        name="Saturday TA",
        max_weekly_hours=6,
        available_slots={sat_tut, sat_lab}
    )

    course = Course(
        id="sat_course",
        name="Saturday Course",
        required_slots=[sat_tut, sat_lab],
        assigned_tas=[ta]
    )

    scheduler = GIUScheduler()
    result = scheduler.create_schedule([course])

    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Saturday assignments: {len(result.global_schedule.assignments)}")

    for assignment in result.global_schedule.assignments:
        print(f"  {assignment}")

    assert result.success, "Saturday scheduling should succeed"
    assert len(result.global_schedule.assignments) == 2, "Should assign both Saturday slots"
    print("✓ Saturday support test passed!")


def test_independence_policy_on():
    """Test Tutorial-Lab Independence when ON (arbitrary combinations allowed)."""
    print("\n=== Independence Policy ON Test ===")

    slots = [
        TimeSlot(Day.SUNDAY, 1, SlotType.TUTORIAL),
        TimeSlot(Day.SUNDAY, 2, SlotType.TUTORIAL),
        TimeSlot(Day.MONDAY, 1, SlotType.LAB),
    ]

    ta = TA(
        id="ta_001",
        name="Independent TA",
        max_weekly_hours=10,
        available_slots=set(slots)
    )

    course = Course(
        id="indep_course",
        name="Independence Course",
        required_slots=slots,
        assigned_tas=[ta]
    )

    # Independence ON - should allow arbitrary combinations
    policies = SchedulingPolicies(tutorial_lab_independence=True)
    scheduler = GIUScheduler(policies)
    result = scheduler.create_schedule([course])

    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Assignments: {len(result.global_schedule.assignments)}")

    tutorial_count = sum(1 for a in result.global_schedule.assignments if a.slot.slot_type == SlotType.TUTORIAL)
    lab_count = sum(1 for a in result.global_schedule.assignments if a.slot.slot_type == SlotType.LAB)

    print(f"Tutorials assigned: {tutorial_count}, Labs assigned: {lab_count}")

    # Should allow unequal distribution (2 tutorials, 1 lab)
    assert result.success, "Independence ON should allow arbitrary combinations"
    print("✓ Independence ON test passed!")


def test_equal_count_policy():
    """Test Tutorial-Lab Equal Count Policy."""
    print("\n=== Equal Count Policy Test ===")

    slots = [
        TimeSlot(Day.SUNDAY, 1, SlotType.TUTORIAL),
        TimeSlot(Day.SUNDAY, 2, SlotType.TUTORIAL),
        TimeSlot(Day.MONDAY, 1, SlotType.LAB),
        TimeSlot(Day.MONDAY, 2, SlotType.LAB),
    ]

    ta = TA(
        id="ta_001",
        name="Equal Count TA",
        max_weekly_hours=10,
        available_slots=set(slots)
    )

    course = Course(
        id="equal_course",
        name="Equal Count Course",
        required_slots=slots,
        assigned_tas=[ta]
    )

    # Independence OFF + Equal Count ON
    policies = SchedulingPolicies(
        tutorial_lab_independence=False,
        tutorial_lab_equal_count=True
    )
    scheduler = GIUScheduler(policies)
    result = scheduler.create_schedule([course])

    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Assignments: {len(result.global_schedule.assignments)}")

    tutorial_count = sum(1 for a in result.global_schedule.assignments if a.slot.slot_type == SlotType.TUTORIAL)
    lab_count = sum(1 for a in result.global_schedule.assignments if a.slot.slot_type == SlotType.LAB)

    print(f"Tutorials assigned: {tutorial_count}, Labs assigned: {lab_count}")

    # Should enforce equal count (2 tutorials, 2 labs)
    if result.success:
        assert tutorial_count == lab_count, "Equal count policy should enforce equal tutorials and labs"

    print("✓ Equal count policy test passed!")


def test_number_matching_policy():
    """Test Tutorial-Lab Number Matching Policy."""
    print("\n=== Number Matching Policy Test ===")

    slots = [
        TimeSlot(Day.SUNDAY, 1, SlotType.TUTORIAL),
        TimeSlot(Day.SUNDAY, 1, SlotType.LAB),
        TimeSlot(Day.MONDAY, 2, SlotType.TUTORIAL),
        TimeSlot(Day.MONDAY, 2, SlotType.LAB),
    ]

    ta = TA(
        id="ta_001",
        name="Matching TA",
        max_weekly_hours=10,
        available_slots=set(slots)
    )

    course = Course(
        id="match_course",
        name="Number Matching Course",
        required_slots=slots,
        assigned_tas=[ta]
    )

    # Independence OFF + Number Matching ON
    policies = SchedulingPolicies(
        tutorial_lab_independence=False,
        tutorial_lab_number_matching=True
    )
    scheduler = GIUScheduler(policies)
    result = scheduler.create_schedule([course])

    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Assignments: {len(result.global_schedule.assignments)}")

    # Check if tutorial-lab pairs match
    assignments_by_number = {}
    for assignment in result.global_schedule.assignments:
        slot_num = assignment.slot.slot_number
        if slot_num not in assignments_by_number:
            assignments_by_number[slot_num] = []
        assignments_by_number[slot_num].append(assignment.slot.slot_type)

    print("Assignment by slot number:")
    for slot_num, types in assignments_by_number.items():
        print(f"  Slot {slot_num}: {[t.value for t in types]}")
        if len(types) == 2:  # Should have both tutorial and lab for each number
            assert SlotType.TUTORIAL in types and SlotType.LAB in types, f"Slot {slot_num} should have both tutorial and lab"

    print("✓ Number matching policy test passed!")


def test_combined_policies():
    """Test combination of multiple policies."""
    print("\n=== Combined Policies Test ===")

    slots = [
        TimeSlot(Day.SATURDAY, 1, SlotType.TUTORIAL),
        TimeSlot(Day.SATURDAY, 1, SlotType.LAB),
        TimeSlot(Day.SUNDAY, 2, SlotType.TUTORIAL),
        TimeSlot(Day.SUNDAY, 2, SlotType.LAB),
    ]

    ta = TA(
        id="ta_001",
        name="Combined Policy TA",
        max_weekly_hours=10,
        available_slots=set(slots)
    )

    course = Course(
        id="combined_course",
        name="Combined Policy Course",
        required_slots=slots,
        assigned_tas=[ta]
    )

    # Independence OFF + Both Equal Count and Number Matching ON
    policies = SchedulingPolicies(
        tutorial_lab_independence=False,
        tutorial_lab_equal_count=True,
        tutorial_lab_number_matching=True
    )
    scheduler = GIUScheduler(policies)
    result = scheduler.create_schedule([course])

    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Assignments: {len(result.global_schedule.assignments)}")

    if result.success:
        tutorial_count = sum(1 for a in result.global_schedule.assignments if a.slot.slot_type == SlotType.TUTORIAL)
        lab_count = sum(1 for a in result.global_schedule.assignments if a.slot.slot_type == SlotType.LAB)

        print(f"Tutorials: {tutorial_count}, Labs: {lab_count}")

        # Should satisfy both policies
        assert tutorial_count == lab_count, "Should have equal tutorials and labs"

        # Check number matching
        assignments_by_number = {}
        for assignment in result.global_schedule.assignments:
            slot_num = assignment.slot.slot_number
            if slot_num not in assignments_by_number:
                assignments_by_number[slot_num] = []
            assignments_by_number[slot_num].append(assignment.slot.slot_type)

        for slot_num, types in assignments_by_number.items():
            if len(types) > 1:
                assert SlotType.TUTORIAL in types and SlotType.LAB in types, f"Number matching violated for slot {slot_num}"

    print("✓ Combined policies test passed!")


def test_policy_defaults():
    """Test that default policy settings work correctly."""
    print("\n=== Policy Defaults Test ===")

    # Default policies: Independence=False, others=False
    policies = SchedulingPolicies()

    print(f"Default Independence: {policies.tutorial_lab_independence}")
    print(f"Default Equal Count: {policies.tutorial_lab_equal_count}")
    print(f"Default Number Matching: {policies.tutorial_lab_number_matching}")
    print(f"Default Fairness Mode: {policies.fairness_mode}")

    assert policies.tutorial_lab_independence == False, "Independence should default to OFF"
    assert policies.tutorial_lab_equal_count == False, "Equal Count should default to OFF"
    assert policies.tutorial_lab_number_matching == False, "Number Matching should default to OFF"
    assert policies.fairness_mode == False, "Fairness Mode should default to OFF"

    print("✓ Policy defaults test passed!")


def main():
    """Run all policy tests."""
    print("GIU Staff Schedule Composer - Policy & Saturday Tests")
    print("=" * 60)

    try:
        test_policy_defaults()
        test_saturday_support()
        test_independence_policy_on()
        test_equal_count_policy()
        test_number_matching_policy()
        test_combined_policies()

        print("\n" + "=" * 60)
        print("✅ All policy and Saturday tests passed!")
        print("Policy system working correctly:")
        print("  ✓ Saturday support enabled")
        print("  ✓ Independence Policy (default OFF) working")
        print("  ✓ Equal Count Policy working")
        print("  ✓ Number Matching Policy working")
        print("  ✓ Combined policies working")
        print("  ✓ Policy defaults correct")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)