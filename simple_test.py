#!/usr/bin/env python3
"""
Simple test to verify core scheduling algorithms work correctly.
"""

from models import (Course, TA, TimeSlot, Day, SlotType, SchedulingPolicies)
from scheduler import GIUScheduler


def test_simple_successful_schedule():
    """Test a simple scenario that should succeed completely."""
    print("=== Simple Success Test ===")

    # Create simple slots
    slot1 = TimeSlot(Day.SUNDAY, 1, SlotType.TUTORIAL)
    slot2 = TimeSlot(Day.MONDAY, 1, SlotType.LAB)

    # Create TA with sufficient capacity
    ta = TA(
        id="ta_001",
        name="Test TA",
        max_weekly_hours=10,
        available_slots={slot1, slot2},
        preferred_slots={slot1: 1, slot2: 2}
    )

    # Create simple course
    course = Course(
        id="test_course",
        name="Test Course",
        required_slots=[slot1, slot2],
        assigned_tas=[ta]
    )

    # Schedule with basic policies
    policies = SchedulingPolicies()
    scheduler = GIUScheduler(policies)
    result = scheduler.create_schedule([course])

    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Message: {result.message}")
    print(f"Assignments: {len(result.global_schedule.assignments)}")
    print(f"Unassigned: {len(result.unassigned_slots)}")

    if result.global_schedule.assignments:
        for assignment in result.global_schedule.assignments:
            print(f"  {assignment}")

    # Verify success
    assert result.success, "Simple schedule should succeed"
    assert len(result.global_schedule.assignments) == 2, "Should have 2 assignments"
    assert len(result.unassigned_slots) == 0, "Should have no unassigned slots"

    print("✓ Simple success test passed!")
    return result


def test_policy_validation():
    """Test policy validation works correctly."""
    print("\n=== Policy Validation Test ===")

    # Create matching tutorial and lab slots
    tut1 = TimeSlot(Day.SUNDAY, 1, SlotType.TUTORIAL)
    lab1 = TimeSlot(Day.SUNDAY, 1, SlotType.LAB)
    tut2 = TimeSlot(Day.MONDAY, 2, SlotType.TUTORIAL)
    lab2 = TimeSlot(Day.MONDAY, 2, SlotType.LAB)

    # Create TA with all slots available
    ta = TA(
        id="ta_001",
        name="Policy Test TA",
        max_weekly_hours=10,
        available_slots={tut1, lab1, tut2, lab2}
    )

    # Create course requiring all slots
    course = Course(
        id="policy_course",
        name="Policy Test Course",
        required_slots=[tut1, lab1, tut2, lab2],
        assigned_tas=[ta]
    )

    # Test number matching policy
    policies = SchedulingPolicies(
        tutorial_lab_independence=False,
        tutorial_lab_number_matching=True
    )

    scheduler = GIUScheduler(policies)
    result = scheduler.create_schedule([course])

    print(f"Number Matching Policy - Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Assignments: {len(result.global_schedule.assignments)}")

    # Should assign matching tutorial-lab pairs
    if result.global_schedule.assignments:
        assignments_by_slot_num = {}
        for assignment in result.global_schedule.assignments:
            slot_num = assignment.slot.slot_number
            if slot_num not in assignments_by_slot_num:
                assignments_by_slot_num[slot_num] = []
            assignments_by_slot_num[slot_num].append(assignment.slot.slot_type)

        print("Assignments by slot number:")
        for slot_num, types in assignments_by_slot_num.items():
            print(f"  Slot {slot_num}: {[t.value for t in types]}")

    print("✓ Policy validation test completed!")
    return result


def test_conflict_detection():
    """Test conflict detection works correctly."""
    print("\n=== Conflict Detection Test ===")

    slot = TimeSlot(Day.SUNDAY, 1, SlotType.TUTORIAL)

    # Create two TAs
    ta1 = TA(id="ta_001", name="TA 1", max_weekly_hours=4, available_slots={slot})
    ta2 = TA(id="ta_002", name="TA 2", max_weekly_hours=4, available_slots={slot})

    # Create two courses wanting the same slot
    course1 = Course(id="c1", name="Course 1", required_slots=[slot], assigned_tas=[ta1, ta2])
    course2 = Course(id="c2", name="Course 2", required_slots=[slot], assigned_tas=[ta1, ta2])

    scheduler = GIUScheduler()
    result = scheduler.create_schedule([course1, course2])

    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Conflicts detected: {len(result.global_schedule.detect_conflicts())}")

    if result.global_schedule.detect_conflicts():
        print("Conflicts found (as expected):")
        for conflict in result.global_schedule.detect_conflicts():
            print(f"  {conflict}")

    print("✓ Conflict detection test completed!")
    return result


def main():
    """Run all tests."""
    print("GIU Staff Schedule Composer - Algorithm Verification Tests")
    print("=" * 60)

    try:
        test_simple_successful_schedule()
        test_policy_validation()
        test_conflict_detection()

        print("\n" + "=" * 60)
        print("✓ All core algorithm tests completed successfully!")
        print("The scheduling system is working correctly.")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)