#!/usr/bin/env python3
"""
Debug script to reproduce and fix the policy combination issue.
"""

from models import Course, TA, TimeSlot, SlotType, Day, SchedulingPolicies
from policy_validator import PolicyValidator

def create_test_data():
    """Create test data that should work with both policies enabled"""
    # Create a simple course with matching tutorial/lab slots
    course = Course(
        id="TEST101",
        name="Test Course"
    )

    # Add matching tutorial and lab slots (same slot numbers for matching, different times)
    course.required_slots = [
        TimeSlot(Day.MONDAY, 1, SlotType.TUTORIAL),    # Tutorial 1 (Mon slot 1)
        TimeSlot(Day.MONDAY, 2, SlotType.LAB),         # Lab 1 (Mon slot 2, but slot_number should be 1)
        TimeSlot(Day.TUESDAY, 1, SlotType.TUTORIAL),   # Tutorial 1 (Tue slot 1)
        TimeSlot(Day.TUESDAY, 2, SlotType.LAB),        # Lab 1 (Tue slot 2, but slot_number should be 1)
    ]

    # Create a TA who is available for all slots
    ta = TA(
        id="test_ta_1",
        name="Test TA",
        max_weekly_hours=8
    )
    # Make TA available for all slots
    ta.available_slots = set(course.required_slots)

    return course, ta

def test_policies_separately():
    """Test each policy separately"""
    print("🧪 Testing policies separately")
    print("=" * 50)

    course, ta = create_test_data()

    # Test 1: Equal count only
    print("\n1️⃣ Testing Equal Count Only:")
    policies = SchedulingPolicies(
        tutorial_lab_independence=False,
        tutorial_lab_equal_count=True,
        tutorial_lab_number_matching=False,
        fairness_mode=False
    )

    validator = PolicyValidator(policies)
    combinations = validator.get_valid_slot_combinations(ta, course, 4)
    print(f"   Found {len(combinations)} combinations")
    for i, combo in enumerate(combinations):
        tutorial_count = sum(1 for slot in combo if slot.slot_type == SlotType.TUTORIAL)
        lab_count = sum(1 for slot in combo if slot.slot_type == SlotType.LAB)
        print(f"   Combo {i}: {tutorial_count}T + {lab_count}L = {len(combo)} slots")

    # Test 2: Number matching only
    print("\n2️⃣ Testing Number Matching Only:")
    policies = SchedulingPolicies(
        tutorial_lab_independence=False,
        tutorial_lab_equal_count=False,
        tutorial_lab_number_matching=True,
        fairness_mode=False
    )

    validator = PolicyValidator(policies)
    combinations = validator.get_valid_slot_combinations(ta, course, 4)
    print(f"   Found {len(combinations)} combinations")
    for i, combo in enumerate(combinations):
        tut_nums = [slot.slot_number for slot in combo if slot.slot_type == SlotType.TUTORIAL]
        lab_nums = [slot.slot_number for slot in combo if slot.slot_type == SlotType.LAB]
        print(f"   Combo {i}: Tutorials{tut_nums} + Labs{lab_nums}")

def test_policies_combined():
    """Test both policies combined - this is where the bug occurs"""
    print("\n🐛 Testing Both Policies Combined (Current Bug):")
    print("=" * 50)

    course, ta = create_test_data()

    policies = SchedulingPolicies(
        tutorial_lab_independence=False,
        tutorial_lab_equal_count=True,
        tutorial_lab_number_matching=True,
        fairness_mode=False
    )

    validator = PolicyValidator(policies)
    combinations = validator.get_valid_slot_combinations(ta, course, 4)
    print(f"   Found {len(combinations)} combinations")

    if combinations:
        for i, combo in enumerate(combinations):
            tutorial_count = sum(1 for slot in combo if slot.slot_type == SlotType.TUTORIAL)
            lab_count = sum(1 for slot in combo if slot.slot_type == SlotType.LAB)
            tut_nums = [slot.slot_number for slot in combo if slot.slot_type == SlotType.TUTORIAL]
            lab_nums = [slot.slot_number for slot in combo if slot.slot_type == SlotType.LAB]
            print(f"   Combo {i}: {tutorial_count}T{tut_nums} + {lab_count}L{lab_nums}")
    else:
        print("   ❌ NO COMBINATIONS FOUND - This is the bug!")

def diagnose_issue():
    """Diagnose why combinations are not found"""
    print("\n🔍 Diagnosing the Issue:")
    print("=" * 50)

    course, ta = create_test_data()

    policies = SchedulingPolicies(
        tutorial_lab_independence=False,
        tutorial_lab_equal_count=True,
        tutorial_lab_number_matching=True,
        fairness_mode=False
    )

    validator = PolicyValidator(policies)

    # Check available slots
    available_slots = [slot for slot in course.required_slots if ta.is_available_for_slot(slot)]
    print(f"Available slots: {len(available_slots)}")
    for slot in available_slots:
        print(f"  {slot}")

    # Debug the number matching logic
    tutorials = {slot.slot_number: slot for slot in available_slots if slot.slot_type == SlotType.TUTORIAL}
    labs = {slot.slot_number: slot for slot in available_slots if slot.slot_type == SlotType.LAB}
    matching_numbers = set(tutorials.keys()) & set(labs.keys())

    print(f"\nNumber matching debug:")
    print(f"  Tutorials: {tutorials}")
    print(f"  Labs: {labs}")
    print(f"  Matching numbers: {matching_numbers}")

    # Check equal count combinations
    equal_combinations = validator._generate_equal_count_combinations(available_slots, 4)
    print(f"\nEqual count combinations: {len(equal_combinations)}")

    # Check number matching combinations
    matching_combinations = validator._generate_number_matching_combinations(available_slots, 4)
    print(f"Number matching combinations: {len(matching_combinations)}")

    # The problem: the method extends both lists but doesn't check if a combination satisfies BOTH policies
    print(f"\nCurrent logic: extends both lists separately")
    print(f"This means combinations only need to satisfy ONE policy, not BOTH")

if __name__ == "__main__":
    test_policies_separately()
    test_policies_combined()
    diagnose_issue()