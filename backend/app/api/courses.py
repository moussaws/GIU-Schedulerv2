from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_database
from app.core.auth import get_current_active_user, get_admin_user
from app.models.database import User, Course as CourseDB, TimeSlot as TimeSlotDB, CourseTAAssignment
from app.models.schemas import (
    Course, CourseCreate, CourseUpdate, TimeSlot, TimeSlotCreate,
    CourseTAAssignmentCreate, APIResponse
)

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/", response_model=List[Course])
async def list_courses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get all courses."""
    courses = db.query(CourseDB).offset(skip).limit(limit).all()
    return courses


@router.get("/{course_id}", response_model=Course)
async def get_course(
    course_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get course by ID."""
    course = db.query(CourseDB).filter(CourseDB.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course


@router.post("/", response_model=APIResponse)
async def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new course."""
    # Check if course code already exists
    existing_course = db.query(CourseDB).filter(CourseDB.code == course_data.code).first()
    if existing_course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course code already exists"
        )

    db_course = CourseDB(
        code=course_data.code,
        name=course_data.name,
        description=course_data.description,
        created_by=current_user.id
    )

    db.add(db_course)
    db.commit()
    db.refresh(db_course)

    return APIResponse(
        success=True,
        message="Course created successfully",
        data={"course_id": db_course.id}
    )


@router.put("/{course_id}", response_model=APIResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Update course."""
    course = db.query(CourseDB).filter(CourseDB.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Update fields
    update_data = course_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)

    db.commit()
    db.refresh(course)

    return APIResponse(
        success=True,
        message="Course updated successfully"
    )


@router.delete("/{course_id}", response_model=APIResponse)
async def delete_course(
    course_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_admin_user)
):
    """Delete course (admin only)."""
    course = db.query(CourseDB).filter(CourseDB.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    db.delete(course)
    db.commit()

    return APIResponse(
        success=True,
        message="Course deleted successfully"
    )


@router.post("/{course_id}/slots", response_model=APIResponse)
async def add_time_slot(
    course_id: int,
    slot_data: TimeSlotCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Add time slot to course."""
    # Verify course exists
    course = db.query(CourseDB).filter(CourseDB.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check if slot already exists
    existing_slot = db.query(TimeSlotDB).filter(
        TimeSlotDB.course_id == course_id,
        TimeSlotDB.day == slot_data.day,
        TimeSlotDB.slot_number == slot_data.slot_number,
        TimeSlotDB.slot_type == slot_data.slot_type
    ).first()

    if existing_slot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time slot already exists for this course"
        )

    db_slot = TimeSlotDB(
        course_id=course_id,
        day=slot_data.day,
        slot_number=slot_data.slot_number,
        slot_type=slot_data.slot_type,
        duration=slot_data.duration
    )

    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)

    return APIResponse(
        success=True,
        message="Time slot added successfully",
        data={"slot_id": db_slot.id}
    )


@router.delete("/{course_id}/slots/{slot_id}", response_model=APIResponse)
async def delete_time_slot(
    course_id: int,
    slot_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Delete time slot from course."""
    slot = db.query(TimeSlotDB).filter(
        TimeSlotDB.id == slot_id,
        TimeSlotDB.course_id == course_id
    ).first()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot not found"
        )

    db.delete(slot)
    db.commit()

    return APIResponse(
        success=True,
        message="Time slot deleted successfully"
    )


@router.post("/{course_id}/assign-ta", response_model=APIResponse)
async def assign_ta_to_course(
    course_id: int,
    assignment_data: CourseTAAssignmentCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Assign TA to course."""
    # Verify course exists
    course = db.query(CourseDB).filter(CourseDB.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check if assignment already exists
    existing_assignment = db.query(CourseTAAssignment).filter(
        CourseTAAssignment.course_id == course_id,
        CourseTAAssignment.ta_id == assignment_data.ta_id
    ).first()

    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TA already assigned to this course"
        )

    db_assignment = CourseTAAssignment(
        course_id=course_id,
        ta_id=assignment_data.ta_id
    )

    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)

    return APIResponse(
        success=True,
        message="TA assigned to course successfully",
        data={"assignment_id": db_assignment.id}
    )


@router.delete("/{course_id}/unassign-ta/{ta_id}", response_model=APIResponse)
async def unassign_ta_from_course(
    course_id: int,
    ta_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Remove TA assignment from course."""
    assignment = db.query(CourseTAAssignment).filter(
        CourseTAAssignment.course_id == course_id,
        CourseTAAssignment.ta_id == ta_id
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TA assignment not found"
        )

    db.delete(assignment)
    db.commit()

    return APIResponse(
        success=True,
        message="TA unassigned from course successfully"
    )