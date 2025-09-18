from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_database
from app.core.auth import get_current_active_user
from app.services.scheduler_service import SchedulerService
from app.models.database import User, Schedule as ScheduleDB
from app.models.schemas import (
    Schedule, ScheduleCreate, ScheduleUpdate, ScheduleGenerationRequest,
    ScheduleExportRequest, ScheduleStatistics, APIResponse
)

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.get("/", response_model=List[Schedule])
async def list_schedules(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get all schedules."""
    schedules = db.query(ScheduleDB).offset(skip).limit(limit).all()
    return schedules


@router.get("/{schedule_id}", response_model=Schedule)
async def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get schedule by ID."""
    schedule = db.query(ScheduleDB).filter(ScheduleDB.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    return schedule


@router.post("/generate", response_model=APIResponse)
async def generate_schedule(
    request: ScheduleGenerationRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Generate a new schedule using the scheduling algorithms."""
    try:
        scheduler_service = SchedulerService(db)
        result = scheduler_service.generate_schedule(
            name=request.name,
            description=request.description,
            policies=request.policies,
            course_ids=request.course_ids,
            created_by_id=current_user.id,
            optimize=request.optimize
        )

        return APIResponse(
            success=result['success'],
            message=result['message'],
            data={
                'schedule_id': result['schedule_id'],
                'statistics': result.get('statistics'),
                'unassigned_slots': result.get('unassigned_slots', 0),
                'policy_violations': result.get('policy_violations', 0)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating schedule: {str(e)}"
        )


@router.post("/{schedule_id}/optimize", response_model=APIResponse)
async def optimize_schedule(
    schedule_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Optimize an existing schedule."""
    # Verify schedule exists
    schedule = db.query(ScheduleDB).filter(ScheduleDB.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )

    try:
        scheduler_service = SchedulerService(db)
        result = scheduler_service.optimize_schedule(schedule_id)

        return APIResponse(
            success=result['success'],
            message=result['message'],
            data={
                'optimized_schedule_id': result['schedule_id'],
                'statistics': result.get('statistics')
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error optimizing schedule: {str(e)}"
        )


@router.get("/{schedule_id}/statistics", response_model=ScheduleStatistics)
async def get_schedule_statistics(
    schedule_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed statistics for a schedule."""
    try:
        scheduler_service = SchedulerService(db)
        statistics = scheduler_service.get_schedule_statistics(schedule_id)
        return statistics
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statistics: {str(e)}"
        )


@router.post("/{schedule_id}/export")
async def export_schedule(
    schedule_id: int,
    export_request: ScheduleExportRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Export schedule in specified format."""
    # Verify schedule exists
    schedule = db.query(ScheduleDB).filter(ScheduleDB.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )

    try:
        scheduler_service = SchedulerService(db)
        exported_content = scheduler_service.export_schedule(
            schedule_id, export_request.format
        )

        # Determine content type based on format
        content_type = "text/plain"
        if export_request.format == "csv":
            content_type = "text/csv"

        from fastapi import Response
        return Response(
            content=exported_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=schedule_{schedule_id}.{export_request.format}"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting schedule: {str(e)}"
        )


@router.put("/{schedule_id}", response_model=APIResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Update schedule metadata."""
    schedule = db.query(ScheduleDB).filter(ScheduleDB.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )

    # Update fields
    update_data = schedule_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)

    return APIResponse(
        success=True,
        message="Schedule updated successfully"
    )


@router.delete("/{schedule_id}", response_model=APIResponse)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Delete schedule."""
    schedule = db.query(ScheduleDB).filter(ScheduleDB.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )

    # Check permissions - only creator or admin can delete
    if schedule.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this schedule"
        )

    db.delete(schedule)
    db.commit()

    return APIResponse(
        success=True,
        message="Schedule deleted successfully"
    )


@router.get("/{schedule_id}/conflicts")
async def get_schedule_conflicts(
    schedule_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get conflicts in a schedule."""
    schedule = db.query(ScheduleDB).filter(ScheduleDB.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )

    # Analyze conflicts
    conflicts = []
    assignments = schedule.assignments

    # Check for TA double-booking
    ta_slots = {}
    for assignment in assignments:
        ta_id = assignment.ta_id
        slot_key = (assignment.time_slot.day, assignment.time_slot.slot_number)

        if ta_id not in ta_slots:
            ta_slots[ta_id] = {}

        if slot_key in ta_slots[ta_id]:
            conflicts.append({
                "type": "double_booking",
                "ta_name": assignment.ta.name,
                "slot": f"{assignment.time_slot.day} slot {assignment.time_slot.slot_number}",
                "courses": [ta_slots[ta_id][slot_key], assignment.course.name]
            })
        else:
            ta_slots[ta_id][slot_key] = assignment.course.name

    # Check for TA overcapacity
    ta_workloads = {}
    for assignment in assignments:
        ta_id = assignment.ta_id
        if ta_id not in ta_workloads:
            ta_workloads[ta_id] = {
                'ta': assignment.ta,
                'hours': 0
            }
        ta_workloads[ta_id]['hours'] += assignment.time_slot.duration

    for ta_id, data in ta_workloads.items():
        if data['hours'] > data['ta'].max_weekly_hours:
            conflicts.append({
                "type": "overcapacity",
                "ta_name": data['ta'].name,
                "current_hours": data['hours'],
                "max_hours": data['ta'].max_weekly_hours,
                "excess_hours": data['hours'] - data['ta'].max_weekly_hours
            })

    return {
        "schedule_id": schedule_id,
        "total_conflicts": len(conflicts),
        "conflicts": conflicts
    }


@router.post("/{schedule_id}/swap", response_model=APIResponse)
async def swap_assignments(
    schedule_id: int,
    swap_request: dict,  # {"source_assignment_id": int, "target_slot": {"day": str, "slot_number": int}}
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Swap an assignment to a different time slot."""
    from app.models.database import ScheduleAssignment as ScheduleAssignmentDB, TimeSlot as TimeSlotDB

    schedule = db.query(ScheduleDB).filter(ScheduleDB.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )

    source_assignment_id = swap_request.get("source_assignment_id")
    target_slot = swap_request.get("target_slot")

    if not source_assignment_id or not target_slot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_assignment_id and target_slot are required"
        )

    # Get source assignment
    source_assignment = db.query(ScheduleAssignmentDB).filter(
        ScheduleAssignmentDB.id == source_assignment_id,
        ScheduleAssignmentDB.schedule_id == schedule_id
    ).first()

    if not source_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source assignment not found"
        )

    # Find target time slot in the same course
    target_time_slot = db.query(TimeSlotDB).filter(
        TimeSlotDB.course_id == source_assignment.course_id,
        TimeSlotDB.day == target_slot["day"],
        TimeSlotDB.slot_number == target_slot["slot_number"],
        TimeSlotDB.slot_type == source_assignment.time_slot.slot_type
    ).first()

    if not target_time_slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target time slot not found for this course and slot type"
        )

    # Check for conflicts
    existing_assignment = db.query(ScheduleAssignmentDB).filter(
        ScheduleAssignmentDB.schedule_id == schedule_id,
        ScheduleAssignmentDB.ta_id == source_assignment.ta_id,
        ScheduleAssignmentDB.time_slot_id == target_time_slot.id
    ).first()

    if existing_assignment and existing_assignment.id != source_assignment.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="TA already assigned to target slot"
        )

    try:
        # Perform the swap
        source_assignment.time_slot_id = target_time_slot.id
        db.commit()
        db.refresh(source_assignment)

        return APIResponse(
            success=True,
            message="Assignment swapped successfully",
            data={"assignment_id": source_assignment.id}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error swapping assignment: {str(e)}"
        )


@router.post("/{schedule_id}/validate-swap")
async def validate_swap(
    schedule_id: int,
    validation_request: dict,  # {"source_assignment_id": int, "target_slot": {"day": str, "slot_number": int}}
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Validate a potential swap without performing it."""
    from app.models.database import ScheduleAssignment as ScheduleAssignmentDB, TimeSlot as TimeSlotDB

    schedule = db.query(ScheduleDB).filter(ScheduleDB.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )

    source_assignment_id = validation_request.get("source_assignment_id")
    target_slot = validation_request.get("target_slot")

    if not source_assignment_id or not target_slot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_assignment_id and target_slot are required"
        )

    # Get source assignment
    source_assignment = db.query(ScheduleAssignmentDB).filter(
        ScheduleAssignmentDB.id == source_assignment_id,
        ScheduleAssignmentDB.schedule_id == schedule_id
    ).first()

    if not source_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source assignment not found"
        )

    conflicts = []
    warnings = []

    # Check for double booking
    existing_assignment = db.query(ScheduleAssignmentDB).filter(
        ScheduleAssignmentDB.schedule_id == schedule_id,
        ScheduleAssignmentDB.ta_id == source_assignment.ta_id
    ).join(TimeSlotDB).filter(
        TimeSlotDB.day == target_slot["day"],
        TimeSlotDB.slot_number == target_slot["slot_number"]
    ).first()

    if existing_assignment and existing_assignment.id != source_assignment.id:
        conflicts.append({
            "type": "double_booking",
            "ta_name": source_assignment.ta.name,
            "slot": f"{target_slot['day']} slot {target_slot['slot_number']}",
            "message": f"{source_assignment.ta.name} is already assigned to {existing_assignment.course.name} at this time"
        })

    # Check workload
    ta_assignments = db.query(ScheduleAssignmentDB).filter(
        ScheduleAssignmentDB.schedule_id == schedule_id,
        ScheduleAssignmentDB.ta_id == source_assignment.ta_id
    ).all()

    total_hours = sum(assignment.time_slot.duration for assignment in ta_assignments)
    if total_hours > source_assignment.ta.max_weekly_hours:
        excess = total_hours - source_assignment.ta.max_weekly_hours
        conflicts.append({
            "type": "overcapacity",
            "ta_name": source_assignment.ta.name,
            "current_hours": total_hours,
            "max_hours": source_assignment.ta.max_weekly_hours,
            "message": f"{source_assignment.ta.name} would exceed capacity by {excess} hours"
        })

    # Check TA availability
    from app.models.database import TAAvailability
    availability = db.query(TAAvailability).filter(
        TAAvailability.ta_id == source_assignment.ta_id,
        TAAvailability.day == target_slot["day"],
        TAAvailability.slot_number == target_slot["slot_number"]
    ).first()

    if not availability or not availability.is_available:
        warnings.append({
            "type": "availability",
            "ta_name": source_assignment.ta.name,
            "slot": f"{target_slot['day']} slot {target_slot['slot_number']}",
            "message": f"{source_assignment.ta.name} may not be available for this slot"
        })
    elif availability.preference_rank > 3:
        warnings.append({
            "type": "preference",
            "ta_name": source_assignment.ta.name,
            "slot": f"{target_slot['day']} slot {target_slot['slot_number']}",
            "message": f"{source_assignment.ta.name} has low preference for this slot (rank {availability.preference_rank})"
        })

    return {
        "is_valid": len(conflicts) == 0,
        "conflicts": conflicts,
        "warnings": warnings
    }