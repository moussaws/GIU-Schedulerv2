"""Database service functions for the scheduler application."""

from sqlalchemy.orm import Session
from database import Course, TA, TAAllocation, Schedule, Assignment, CourseGrid, get_db
from typing import List, Dict, Optional
import json

class CourseService:
    @staticmethod
    def create_course(db: Session, course_data: dict) -> Course:
        """Create a new course."""
        course = Course(**course_data)
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def get_course(db: Session, course_id: int) -> Optional[Course]:
        """Get a course by ID."""
        return db.query(Course).filter(Course.id == course_id).first()

    @staticmethod
    def get_courses(db: Session) -> List[Course]:
        """Get all courses."""
        return db.query(Course).all()

    @staticmethod
    def update_course(db: Session, course_id: int, course_data: dict) -> Optional[Course]:
        """Update a course."""
        course = db.query(Course).filter(Course.id == course_id).first()
        if course:
            for key, value in course_data.items():
                setattr(course, key, value)
            db.commit()
            db.refresh(course)
        return course

    @staticmethod
    def delete_course(db: Session, course_id: int) -> bool:
        """Delete a course."""
        course = db.query(Course).filter(Course.id == course_id).first()
        if course:
            db.delete(course)
            db.commit()
            return True
        return False

class TAService:
    @staticmethod
    def create_ta(db: Session, ta_data: dict) -> TA:
        """Create a new TA."""
        # Handle course allocations separately
        course_allocations = ta_data.pop('course_allocations', [])

        ta = TA(**ta_data)
        db.add(ta)
        db.flush()  # Get the TA ID

        # Add course allocations
        total_hours = 0
        for allocation in course_allocations:
            ta_allocation = TAAllocation(
                ta_id=ta.id,
                course_id=allocation['course_id'],
                allocated_hours=allocation['allocated_hours']
            )
            db.add(ta_allocation)
            total_hours += allocation['allocated_hours']

        ta.total_allocated_hours = total_hours
        db.commit()
        db.refresh(ta)
        return ta

    @staticmethod
    def get_ta(db: Session, ta_id: int) -> Optional[TA]:
        """Get a TA by ID."""
        return db.query(TA).filter(TA.id == ta_id).first()

    @staticmethod
    def get_tas(db: Session) -> List[TA]:
        """Get all TAs."""
        return db.query(TA).all()

    @staticmethod
    def update_ta(db: Session, ta_id: int, ta_data: dict) -> Optional[TA]:
        """Update a TA."""
        ta = db.query(TA).filter(TA.id == ta_id).first()
        if not ta:
            return None

        # Handle course allocations separately
        course_allocations = ta_data.pop('course_allocations', None)

        # Update TA fields
        for key, value in ta_data.items():
            setattr(ta, key, value)

        # Update course allocations if provided
        if course_allocations is not None:
            # Delete existing allocations
            db.query(TAAllocation).filter(TAAllocation.ta_id == ta_id).delete()

            # Add new allocations
            total_hours = 0
            for allocation in course_allocations:
                ta_allocation = TAAllocation(
                    ta_id=ta.id,
                    course_id=allocation['course_id'],
                    allocated_hours=allocation['allocated_hours']
                )
                db.add(ta_allocation)
                total_hours += allocation['allocated_hours']

            ta.total_allocated_hours = total_hours

        db.commit()
        db.refresh(ta)
        return ta

    @staticmethod
    def delete_ta(db: Session, ta_id: int) -> bool:
        """Delete a TA."""
        ta = db.query(TA).filter(TA.id == ta_id).first()
        if ta:
            # Delete allocations first
            db.query(TAAllocation).filter(TAAllocation.ta_id == ta_id).delete()
            db.delete(ta)
            db.commit()
            return True
        return False

    @staticmethod
    def get_ta_with_allocations(db: Session, ta_id: int) -> Optional[dict]:
        """Get TA with course allocations in the format expected by the API."""
        ta = db.query(TA).filter(TA.id == ta_id).first()
        if not ta:
            return None

        allocations = db.query(TAAllocation).filter(TAAllocation.ta_id == ta_id).all()

        return {
            "id": ta.id,
            "name": ta.name,
            "email": ta.email,
            "blocked_slots": ta.blocked_slots,
            "day_off": ta.day_off,
            "premasters": ta.premasters,
            "skills": ta.skills,
            "notes": ta.notes,
            "total_allocated_hours": ta.total_allocated_hours,
            "course_allocations": [
                {
                    "course_id": alloc.course_id,
                    "allocated_hours": alloc.allocated_hours
                }
                for alloc in allocations
            ],
            "created_at": ta.created_at.isoformat() if ta.created_at else None
        }

class ScheduleService:
    @staticmethod
    def create_schedule(db: Session, schedule_data: dict) -> Schedule:
        """Create a new schedule with assignments."""
        # Extract assignments
        assignments_data = schedule_data.pop('assignments', [])
        failed_assignments = schedule_data.pop('failed_assignments', [])

        # Create schedule
        schedule = Schedule(**schedule_data)
        db.add(schedule)
        db.flush()  # Get the schedule ID

        # Create assignments
        for assignment_data in assignments_data:
            # Find TA by name
            ta = db.query(TA).filter(TA.name == assignment_data['ta_name']).first()
            if ta:
                assignment = Assignment(
                    schedule_id=schedule.id,
                    ta_id=ta.id,
                    day=assignment_data['day'],
                    slot_number=assignment_data['slot_number'],
                    slot_type=assignment_data['slot_type'],
                    tutorial_number=assignment_data.get('tutorial_number'),
                    lab_number=assignment_data.get('lab_number'),
                    duration=assignment_data.get('duration', 2)
                )
                db.add(assignment)

        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def get_schedule(db: Session, schedule_id: int) -> Optional[dict]:
        """Get a schedule with assignments."""
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            return None

        assignments = db.query(Assignment).filter(Assignment.schedule_id == schedule_id).all()

        return {
            "id": schedule.id,
            "success": schedule.success,
            "message": schedule.message,
            "statistics": schedule.statistics,
            "policies_used": schedule.policies_used,
            "assignments": [
                {
                    "ta_name": assignment.ta.name,
                    "course_name": schedule.course.name if schedule.course else "Unknown",
                    "day": assignment.day,
                    "slot": assignment.slot_number,
                    "slot_number": assignment.slot_number,
                    "slot_type": assignment.slot_type,
                    "tutorial_number": assignment.tutorial_number,
                    "lab_number": assignment.lab_number,
                    "duration": assignment.duration
                }
                for assignment in assignments
            ],
            "failed_assignments": [],  # Could be stored separately if needed
            "created_at": schedule.created_at.isoformat() if schedule.created_at else None
        }

    @staticmethod
    def get_schedules(db: Session) -> List[dict]:
        """Get all schedules with assignments."""
        schedules = db.query(Schedule).all()
        result = []

        for schedule in schedules:
            # Get assignments for this schedule
            assignments = db.query(Assignment).filter(Assignment.schedule_id == schedule.id).all()

            schedule_data = {
                "id": schedule.id,
                "success": schedule.success,
                "message": schedule.message,
                "statistics": schedule.statistics,
                "policies_used": schedule.policies_used,
                "assignments": [
                    {
                        "ta_name": assignment.ta.name,
                        "course_name": schedule.course.name if schedule.course else "Unknown",
                        "day": assignment.day,
                        "slot": assignment.slot_number,
                        "slot_number": assignment.slot_number,
                        "slot_type": assignment.slot_type,
                        "tutorial_number": assignment.tutorial_number,
                        "lab_number": assignment.lab_number,
                        "duration": assignment.duration
                    }
                    for assignment in assignments
                ],
                "created_at": schedule.created_at.isoformat() if schedule.created_at else None
            }
            result.append(schedule_data)

        return result

    @staticmethod
    def save_schedule(db: Session, schedule_data: dict) -> Schedule:
        """Save a new schedule from the frontend."""
        # Extract and format the data
        assignments_data = schedule_data.get('assignments', [])

        # Get the first course_id from assignments or default to 1
        course_id = 1  # Default course ID
        if assignments_data:
            # Try to find a course for the first assignment
            first_assignment = assignments_data[0]
            course_code = first_assignment.get('course_code')
            if course_code:
                course = db.query(Course).filter(Course.code == course_code).first()
                if course:
                    course_id = course.id

        # Create the schedule record with the required course_id
        # Use the name in the message field since name field doesn't exist
        schedule_name = schedule_data.get('name', 'Unnamed Schedule')

        # Get course name for display
        course = db.query(Course).filter(Course.id == course_id).first()
        course_name = course.name if course else "Unknown Course"

        # Format: "Schedule Name - Course Name"
        message = f"{schedule_name} - {course_name}"

        # Add original message if it exists
        if schedule_data.get('message'):
            message += f" | {schedule_data.get('message')}"

        schedule = Schedule(
            course_id=course_id,
            success=schedule_data.get('success', False),
            message=message,
            statistics=schedule_data.get('statistics'),
            policies_used=schedule_data.get('policies_used', {})
        )
        db.add(schedule)
        db.flush()  # Get the schedule ID

        # Create assignments
        for assignment_data in assignments_data:
            # Find TA by name
            ta = db.query(TA).filter(TA.name == assignment_data.get('ta_name')).first()
            if ta:
                assignment = Assignment(
                    schedule_id=schedule.id,
                    ta_id=ta.id,
                    day=assignment_data.get('day'),
                    slot_number=assignment_data.get('slot_number'),
                    slot_type=assignment_data.get('slot_type'),
                    tutorial_number=assignment_data.get('tutorial_number'),
                    lab_number=assignment_data.get('lab_number'),
                    duration=assignment_data.get('duration', 2)
                )
                db.add(assignment)

        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def delete_schedule(db: Session, schedule_id: int) -> bool:
        """Delete a schedule."""
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if schedule:
            # Delete assignments first
            db.query(Assignment).filter(Assignment.schedule_id == schedule_id).delete()
            db.delete(schedule)
            db.commit()
            return True
        return False

class CourseGridService:
    @staticmethod
    def save_course_grid(db: Session, course_id: int, grid_data: dict, selected_tas: list = None, policies: dict = None) -> CourseGrid:
        """Save or update a course-specific grid configuration."""
        # Check if grid already exists for this course
        existing_grid = db.query(CourseGrid).filter(CourseGrid.course_id == course_id).first()

        if existing_grid:
            # Update existing grid
            existing_grid.grid_data = grid_data
            existing_grid.selected_tas = selected_tas or []
            existing_grid.policies = policies or {}
            db.commit()
            db.refresh(existing_grid)
            return existing_grid
        else:
            # Create new grid
            new_grid = CourseGrid(
                course_id=course_id,
                grid_data=grid_data,
                selected_tas=selected_tas or [],
                policies=policies or {}
            )
            db.add(new_grid)
            db.commit()
            db.refresh(new_grid)
            return new_grid

    @staticmethod
    def get_course_grid(db: Session, course_id: int) -> Optional[dict]:
        """Get the grid configuration for a specific course."""
        grid = db.query(CourseGrid).filter(CourseGrid.course_id == course_id).first()
        if grid:
            return {
                "id": grid.id,
                "course_id": grid.course_id,
                "grid_data": grid.grid_data,
                "selected_tas": grid.selected_tas,
                "policies": grid.policies,
                "created_at": grid.created_at.isoformat() if grid.created_at else None,
                "updated_at": grid.updated_at.isoformat() if grid.updated_at else None
            }
        return None

    @staticmethod
    def delete_course_grid(db: Session, course_id: int) -> bool:
        """Delete a course grid."""
        grid = db.query(CourseGrid).filter(CourseGrid.course_id == course_id).first()
        if grid:
            db.delete(grid)
            db.commit()
            return True
        return False