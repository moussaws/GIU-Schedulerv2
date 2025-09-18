#!/usr/bin/env python3
"""
Example usage of the GIU Staff Schedule Composer system.

This example demonstrates how to:
1. Create courses with required slots
2. Define TAs with availability and preferences
3. Apply different scheduling policies
4. Generate and optimize schedules
5. Handle conflicts and view results
"""

from models import (Course, TA, TimeSlot, Day, SlotType, SchedulingPolicies)
from scheduler import GIUScheduler


def create_sample_data():
    """Create sample courses and TAs for demonstration."""

    # Create time slots (including Saturday)
    slots = {
        'sat_1_tut': TimeSlot(Day.SATURDAY, 1, SlotType.TUTORIAL),
        'sat_1_lab': TimeSlot(Day.SATURDAY, 1, SlotType.LAB),
        'sun_1_tut': TimeSlot(Day.SUNDAY, 1, SlotType.TUTORIAL),
        'sun_1_lab': TimeSlot(Day.SUNDAY, 1, SlotType.LAB),
        'sun_2_tut': TimeSlot(Day.SUNDAY, 2, SlotType.TUTORIAL),
        'sun_2_lab': TimeSlot(Day.SUNDAY, 2, SlotType.LAB),
        'mon_1_tut': TimeSlot(Day.MONDAY, 1, SlotType.TUTORIAL),
        'mon_1_lab': TimeSlot(Day.MONDAY, 1, SlotType.LAB),
        'mon_2_tut': TimeSlot(Day.MONDAY, 2, SlotType.TUTORIAL),
        'tue_1_tut': TimeSlot(Day.TUESDAY, 1, SlotType.TUTORIAL),
        'tue_2_lab': TimeSlot(Day.TUESDAY, 2, SlotType.LAB),
        'wed_1_tut': TimeSlot(Day.WEDNESDAY, 1, SlotType.TUTORIAL),
        'wed_2_lab': TimeSlot(Day.WEDNESDAY, 2, SlotType.LAB),
    }

    # Create TAs
    ahmed = TA(
        id="ta_001",
        name="Ahmed Hassan",
        max_weekly_hours=8,
        available_slots={
            slots['sat_1_tut'], slots['sat_1_lab'], slots['sun_1_tut'],
            slots['sun_1_lab'], slots['sun_2_tut'], slots['mon_1_tut'],
            slots['mon_1_lab'], slots['tue_1_tut']
        },
        preferred_slots={
            slots['sat_1_tut']: 1,  # Highest preference
            slots['sun_1_tut']: 2,
            slots['mon_1_tut']: 3,
            slots['sat_1_lab']: 4
        }
    )

    sara = TA(
        id="ta_002",
        name="Sara Mohamed",
        max_weekly_hours=6,
        available_slots={
            slots['sun_2_tut'], slots['sun_2_lab'], slots['tue_1_tut'],
            slots['tue_2_lab'], slots['wed_1_tut'], slots['wed_2_lab']
        },
        preferred_slots={
            slots['tue_1_tut']: 1,
            slots['tue_2_lab']: 1,  # Equal preference
            slots['wed_1_tut']: 2
        }
    )

    omar = TA(
        id="ta_003",
        name="Omar Ali",
        max_weekly_hours=10,
        available_slots={
            slots['sun_1_tut'], slots['mon_1_lab'], slots['mon_2_tut'],
            slots['tue_1_tut'], slots['wed_1_tut'], slots['wed_2_lab']
        },
        preferred_slots={
            slots['mon_2_tut']: 1,
            slots['wed_1_tut']: 2
        }
    )

    # Create courses
    cs101 = Course(
        id="cs101",
        name="Introduction to Programming",
        required_slots=[
            slots['sat_1_tut'], slots['sat_1_lab'],
            slots['sun_1_tut'], slots['sun_1_lab']
        ],
        assigned_tas=[ahmed, omar]
    )

    cs201 = Course(
        id="cs201",
        name="Data Structures",
        required_slots=[
            slots['sun_2_tut'], slots['sun_2_lab'],
            slots['tue_1_tut'], slots['tue_2_lab']
        ],
        assigned_tas=[sara, omar]
    )

    cs301 = Course(
        id="cs301",
        name="Advanced Algorithms",
        required_slots=[
            slots['mon_2_tut'], slots['wed_1_tut'], slots['wed_2_lab']
        ],
        assigned_tas=[ahmed, sara, omar]
    )

    return [cs101, cs201, cs301], [ahmed, sara, omar]


def demonstrate_basic_scheduling():
    """Demonstrate basic scheduling without policies."""
    print("=== Basic Scheduling Demo ===")

    courses, tas = create_sample_data()

    # Default policies (independence OFF, no specific policies)
    policies = SchedulingPolicies()  # All defaults: independence=False, others=False

    scheduler = GIUScheduler(policies)
    result = scheduler.create_schedule(courses, optimize=False)

    print(f"Schedule Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Message: {result.message}")
    print(f"Total Assignments: {len(result.global_schedule.assignments)}")
    print(f"Unassigned Slots: {len(result.unassigned_slots)}")

    if result.global_schedule.assignments:
        print("\nAssignments:")
        for assignment in result.global_schedule.assignments:
            print(f"  {assignment}")

    print("\n" + "="*60 + "\n")
    return result


def demonstrate_policy_enforcement():
    """Demonstrate scheduling with different policies."""
    print("=== Policy Enforcement Demo ===")

    courses, tas = create_sample_data()

    # Independence ON - allow arbitrary combinations
    print("Testing Independence Policy ON:")
    policies = SchedulingPolicies(tutorial_lab_independence=True)
    scheduler = GIUScheduler(policies)
    result = scheduler.create_schedule(courses)
    print(f"Independence ON - Status: {'SUCCESS' if result.success else 'FAILED'}")

    # Equal count policy (independence OFF)
    print("\nTesting Equal Count Policy:")
    policies = SchedulingPolicies(
        tutorial_lab_independence=False,
        tutorial_lab_equal_count=True,
        fairness_mode=True
    )

    scheduler = GIUScheduler(policies)
    result = scheduler.create_schedule(courses)

    print(f"Equal Count Policy - Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Message: {result.message}")

    if result.policy_violations:
        print("Policy Violations:")
        for violation in result.policy_violations:
            print(f"  - {violation}")

    # Number matching policy (independence OFF)
    print("\nTesting Number Matching Policy:")
    policies = SchedulingPolicies(
        tutorial_lab_independence=False,
        tutorial_lab_number_matching=True
    )
    scheduler.update_policies(policies)

    result2 = scheduler.create_schedule(courses)
    print(f"Number Matching Policy - Status: {'SUCCESS' if result2.success else 'FAILED'}")

    print("\n" + "="*60 + "\n")
    return result


def demonstrate_conflict_resolution():
    """Demonstrate conflict detection and resolution."""
    print("=== Conflict Resolution Demo ===")

    courses, tas = create_sample_data()

    # Create a scenario with potential conflicts
    # Reduce TA availability to force conflicts
    for ta in tas:
        ta.max_weekly_hours = 4  # Reduce capacity

    policies = SchedulingPolicies(fairness_mode=False)
    scheduler = GIUScheduler(policies)

    result = scheduler.create_schedule(courses, optimize=False)
    print(f"Initial Schedule - Status: {'SUCCESS' if result.success else 'FAILED'}")

    if not result.success:
        print("Attempting automatic conflict resolution...")
        resolved_result = scheduler.resolve_conflicts(result, auto_resolve=True)
        print(f"Resolved Schedule - Status: {'SUCCESS' if resolved_result.success else 'FAILED'}")
        print(f"Resolution Message: {resolved_result.message}")

    print("\n" + "="*60 + "\n")
    return result


def demonstrate_optimization():
    """Demonstrate workload balancing and optimization."""
    print("=== Workload Optimization Demo ===")

    courses, tas = create_sample_data()

    policies = SchedulingPolicies(fairness_mode=True)
    scheduler = GIUScheduler(policies)

    # Schedule without optimization
    result_basic = scheduler.create_schedule(courses, optimize=False)
    stats_basic = scheduler.get_schedule_statistics(result_basic)

    print("Without Optimization:")
    print(f"  Imbalance Score: {stats_basic['workload_balance']['imbalance_score']}")
    print(f"  Overloaded TAs: {stats_basic['workload_balance']['overloaded_tas']}")
    print(f"  Underloaded TAs: {stats_basic['workload_balance']['underloaded_tas']}")

    # Schedule with optimization
    result_optimized = scheduler.create_schedule(courses, optimize=True)
    stats_optimized = scheduler.get_schedule_statistics(result_optimized)

    print("\nWith Optimization:")
    print(f"  Imbalance Score: {stats_optimized['workload_balance']['imbalance_score']}")
    print(f"  Overloaded TAs: {stats_optimized['workload_balance']['overloaded_tas']}")
    print(f"  Underloaded TAs: {stats_optimized['workload_balance']['underloaded_tas']}")

    # Show improvement suggestions
    suggestions = scheduler.suggest_improvements(result_optimized)
    if suggestions:
        print("\nImprovement Suggestions:")
        for suggestion in suggestions[:3]:  # Show first 3
            print(f"  - {suggestion}")

    print("\n" + "="*60 + "\n")
    return result_optimized


def demonstrate_export_formats():
    """Demonstrate different export formats."""
    print("=== Export Formats Demo ===")

    courses, tas = create_sample_data()
    scheduler = GIUScheduler()
    result = scheduler.create_schedule(courses)

    if result.success:
        print("Grid Format:")
        print(scheduler.export_schedule(result, "grid"))

        print("\n\nList Format:")
        print(scheduler.export_schedule(result, "list"))

        print("\n\nCSV Format (first 5 lines):")
        csv_output = scheduler.export_schedule(result, "csv")
        for line in csv_output.split('\n')[:5]:
            print(line)

    print("\n" + "="*60 + "\n")


def main():
    """Run all demonstrations."""
    print("GIU Staff Schedule Composer - Algorithm Demonstration")
    print("=" * 60)
    print()

    try:
        # Run demonstrations
        demonstrate_basic_scheduling()
        demonstrate_policy_enforcement()
        demonstrate_conflict_resolution()
        result = demonstrate_optimization()
        demonstrate_export_formats()

        print("=== Summary ===")
        print("All scheduling algorithms demonstrated successfully!")
        print("The system supports:")
        print("- Course-scoped scheduling with global merging")
        print("- Multiple policy enforcement options")
        print("- Automatic conflict detection and resolution")
        print("- Workload balancing and fairness optimization")
        print("- Multiple export formats")
        print("- Comprehensive statistics and suggestions")

    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()