"""
Service layer to integrate the original scheduling algorithms with the web backend.
"""
import json
import sys
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

# Add the parent directory to Python path to import our scheduling algorithms
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from models import (
    Course as AlgoCourse, TA as AlgoTA, TimeSlot as AlgoTimeSlot,
    Day, SlotType, SchedulingPolicies as AlgoSchedulingPolicies
)
from scheduler import GIUScheduler

from app.models.database import (
    Course as CourseDB, TeachingAssistant as TADB, TimeSlot as TimeSlotDB,
    Schedule as ScheduleDB, ScheduleAssignment as ScheduleAssignmentDB,
    CourseTAAssignment, TAAvailability
)
from app.models.schemas import SchedulingPolicies, ScheduleStatistics, TAWorkloadStats


class SchedulerService:
    """Service to bridge web backend with scheduling algorithms."""

    def __init__(self, db: Session):
        self.db = db

    def generate_schedule(
        self,
        name: str,
        description: Optional[str],
        policies: SchedulingPolicies,
        course_ids: List[int],
        created_by_id: int,
        optimize: bool = True
    ) -> Dict[str, Any]:
        """Generate a new schedule using the scheduling algorithms."""

        # Convert database models to algorithm models
        algo_courses = []
        algo_tas = {}
        validation_errors = []

        for course_id in course_ids:
            # Get course from database
            db_course = self.db.query(CourseDB).filter(CourseDB.id == course_id).first()
            if not db_course:
                validation_errors.append(f"Course with ID {course_id} not found")
                continue

            # Convert time slots
            algo_slots = []
            for db_slot in db_course.time_slots:
                algo_slot = AlgoTimeSlot(
                    day=Day(db_slot.day),
                    slot_number=db_slot.slot_number,
                    slot_type=SlotType(db_slot.slot_type),
                    duration=db_slot.duration
                )
                algo_slots.append(algo_slot)

            # Validate course has time slots
            if not algo_slots:
                validation_errors.append(f"Course {db_course.code} has no time slots defined")
                continue

            # Convert assigned TAs
            assigned_tas = []
            for ta_assignment in db_course.ta_assignments:
                ta_id = ta_assignment.ta_id

                # Create or get TA from cache
                if ta_id not in algo_tas:
                    db_ta = ta_assignment.ta

                    # Get TA availability
                    availability = self.db.query(TAAvailability).filter(
                        TAAvailability.ta_id == ta_id
                    ).all()

                    available_slots = set()
                    preferred_slots = {}

                    for avail in availability:
                        if avail.is_available:
                            slot = AlgoTimeSlot(
                                day=Day(avail.day),
                                slot_number=avail.slot_number,
                                slot_type=SlotType.TUTORIAL,  # We'll add both tutorial and lab
                                duration=2
                            )
                            available_slots.add(slot)

                            # Also add lab version
                            lab_slot = AlgoTimeSlot(
                                day=Day(avail.day),
                                slot_number=avail.slot_number,
                                slot_type=SlotType.LAB,
                                duration=2
                            )
                            available_slots.add(lab_slot)

                            # Set preferences (lower rank = higher preference)
                            if avail.preference_rank <= 3:
                                preferred_slots[slot] = avail.preference_rank
                                preferred_slots[lab_slot] = avail.preference_rank

                    algo_ta = AlgoTA(
                        id=str(db_ta.id),
                        name=db_ta.name,
                        max_weekly_hours=db_ta.max_weekly_hours,
                        available_slots=available_slots,
                        preferred_slots=preferred_slots
                    )
                    algo_tas[ta_id] = algo_ta

                assigned_tas.append(algo_tas[ta_id])

            # Validate course has assigned TAs
            if not assigned_tas:
                validation_errors.append(f"Course {db_course.code} has no TAs assigned")
                continue

            # Create algorithm course
            algo_course = AlgoCourse(
                id=str(db_course.id),
                name=db_course.name,
                required_slots=algo_slots,
                assigned_tas=assigned_tas
            )
            algo_courses.append(algo_course)

        # Check for validation errors
        if validation_errors:
            return {
                'success': False,
                'message': f'Validation failed: {"; ".join(validation_errors)}',
                'schedule_id': None
            }

        if not algo_courses:
            return {
                'success': False,
                'message': 'No valid courses found after validation',
                'schedule_id': None
            }

        # Convert policies
        algo_policies = AlgoSchedulingPolicies(
            tutorial_lab_independence=policies.tutorial_lab_independence,
            tutorial_lab_equal_count=policies.tutorial_lab_equal_count,
            tutorial_lab_number_matching=policies.tutorial_lab_number_matching,
            fairness_mode=policies.fairness_mode
        )

        # Generate schedule
        scheduler = GIUScheduler(algo_policies)
        result = scheduler.create_schedule(algo_courses, optimize=optimize)

        # Validate scheduling result
        if not result:
            return {
                'success': False,
                'message': 'Scheduling algorithm failed to return a result',
                'schedule_id': None
            }

        if not hasattr(result, 'global_schedule') or not result.global_schedule:
            return {
                'success': False,
                'message': 'Scheduling algorithm returned empty result',
                'schedule_id': None
            }

        if not hasattr(result.global_schedule, 'assignments') or not result.global_schedule.assignments:
            # Still create the schedule record but mark it as having issues
            message = result.message if hasattr(result, 'message') else 'No assignments were generated'
            return {
                'success': False,
                'message': f'Schedule generation completed but no assignments created: {message}',
                'schedule_id': None,
                'unassigned_slots': len(getattr(result, 'unassigned_slots', [])),
                'policy_violations': len(getattr(result, 'policy_violations', []))
            }

        # Get statistics
        statistics = scheduler.get_schedule_statistics(result)

        # Save schedule to database
        db_schedule = ScheduleDB(
            name=name,
            description=description,
            policies_json=json.dumps(policies.dict()),
            success=result.success,
            message=result.message,
            statistics_json=json.dumps(statistics),
            created_by=created_by_id
        )

        self.db.add(db_schedule)
        self.db.commit()
        self.db.refresh(db_schedule)

        # Save assignments
        for assignment in result.global_schedule.assignments:
            # Find the corresponding database objects
            course_id = int(assignment.course.id)
            ta_id = int(assignment.ta.id)

            # Find the time slot in database
            time_slot = self.db.query(TimeSlotDB).filter(
                TimeSlotDB.course_id == course_id,
                TimeSlotDB.day == assignment.slot.day.value,
                TimeSlotDB.slot_number == assignment.slot.slot_number,
                TimeSlotDB.slot_type == assignment.slot.slot_type.value
            ).first()

            if time_slot:
                db_assignment = ScheduleAssignmentDB(
                    schedule_id=db_schedule.id,
                    course_id=course_id,
                    ta_id=ta_id,
                    time_slot_id=time_slot.id
                )
                self.db.add(db_assignment)

        self.db.commit()

        return {
            'success': result.success,
            'message': result.message,
            'schedule_id': db_schedule.id,
            'statistics': statistics,
            'unassigned_slots': len(result.unassigned_slots),
            'policy_violations': len(result.policy_violations)
        }

    def optimize_schedule(self, schedule_id: int) -> Dict[str, Any]:
        """Optimize an existing schedule."""
        db_schedule = self.db.query(ScheduleDB).filter(ScheduleDB.id == schedule_id).first()
        if not db_schedule:
            return {'success': False, 'message': 'Schedule not found'}

        # Get course IDs from existing assignments
        course_ids = list(set([
            assignment.course_id for assignment in db_schedule.assignments
        ]))

        # Parse policies
        policies = SchedulingPolicies.parse_obj(json.loads(db_schedule.policies_json))

        # Regenerate with optimization
        return self.generate_schedule(
            name=f"{db_schedule.name} (Optimized)",
            description=f"Optimized version of: {db_schedule.description}",
            policies=policies,
            course_ids=course_ids,
            created_by_id=db_schedule.created_by,
            optimize=True
        )

    def export_schedule(self, schedule_id: int, format_type: str = "grid") -> str:
        """Export schedule in specified format."""
        db_schedule = self.db.query(ScheduleDB).filter(ScheduleDB.id == schedule_id).first()
        if not db_schedule:
            raise ValueError("Schedule not found")

        # Rebuild the algorithm schedule from database
        result = self._rebuild_algorithm_result(db_schedule)

        # Use the original scheduler to export
        policies = SchedulingPolicies.parse_obj(json.loads(db_schedule.policies_json))
        algo_policies = AlgoSchedulingPolicies(**policies.dict())
        scheduler = GIUScheduler(algo_policies)

        return scheduler.export_schedule(result, format_type)

    def get_schedule_statistics(self, schedule_id: int) -> ScheduleStatistics:
        """Get comprehensive schedule statistics."""
        db_schedule = self.db.query(ScheduleDB).filter(ScheduleDB.id == schedule_id).first()
        if not db_schedule:
            raise ValueError("Schedule not found")

        if db_schedule.statistics_json:
            stats_data = json.loads(db_schedule.statistics_json)
        else:
            stats_data = {}

        # Calculate TA workload statistics
        ta_workloads = []
        ta_hours = {}

        for assignment in db_schedule.assignments:
            ta_id = assignment.ta_id
            if ta_id not in ta_hours:
                ta_hours[ta_id] = {
                    'ta': assignment.ta,
                    'hours': 0,
                    'courses': set()
                }
            ta_hours[ta_id]['hours'] += assignment.time_slot.duration
            ta_hours[ta_id]['courses'].add(assignment.course_id)

        for ta_id, data in ta_hours.items():
            ta = data['ta']
            workload = TAWorkloadStats(
                ta_id=ta_id,
                ta_name=ta.name,
                current_hours=data['hours'],
                max_hours=ta.max_weekly_hours,
                utilization_rate=data['hours'] / ta.max_weekly_hours if ta.max_weekly_hours > 0 else 0,
                course_count=len(data['courses'])
            )
            ta_workloads.append(workload)

        return ScheduleStatistics(
            total_assignments=len(db_schedule.assignments),
            total_tas=len(ta_hours),
            total_courses=len(set(a.course_id for a in db_schedule.assignments)),
            average_ta_workload=stats_data.get('average_ta_workload', 0),
            workload_variance=stats_data.get('workload_variance', 0),
            average_course_coverage=stats_data.get('average_course_coverage', 0),
            fully_covered_courses=stats_data.get('fully_covered_courses', 0),
            conflicts_detected=stats_data.get('conflicts_detected', 0),
            policy_violations=stats_data.get('policy_violations', 0),
            success_rate=stats_data.get('success_rate', 0),
            ta_workloads=ta_workloads
        )

    def _rebuild_algorithm_result(self, db_schedule: ScheduleDB):
        """Rebuild algorithm result from database schedule for export."""
        # This is a simplified version for export purposes
        # In a full implementation, you'd reconstruct the complete SchedulingResult
        from models import GlobalSchedule, ScheduleAssignment as AlgoAssignment

        assignments = []
        for db_assignment in db_schedule.assignments:
            algo_assignment = AlgoAssignment(
                ta=AlgoTA(
                    id=str(db_assignment.ta.id),
                    name=db_assignment.ta.name,
                    max_weekly_hours=db_assignment.ta.max_weekly_hours
                ),
                slot=AlgoTimeSlot(
                    day=Day(db_assignment.time_slot.day),
                    slot_number=db_assignment.time_slot.slot_number,
                    slot_type=SlotType(db_assignment.time_slot.slot_type),
                    duration=db_assignment.time_slot.duration
                ),
                course=AlgoCourse(
                    id=str(db_assignment.course.id),
                    name=db_assignment.course.name
                )
            )
            assignments.append(algo_assignment)

        global_schedule = GlobalSchedule(
            courses=[],  # Not needed for export
            assignments=assignments
        )

        # Create a mock result for export
        class MockResult:
            def __init__(self, global_schedule):
                self.global_schedule = global_schedule
                self.success = True
                self.message = "Exported from database"

        return MockResult(global_schedule)