from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_database
from app.core.auth import get_current_active_user, get_admin_user
from app.models.database import User, TeachingAssistant as TADB, TAAvailability as TAAvailabilityDB
from app.models.schemas import (
    TeachingAssistant, TeachingAssistantCreate, TeachingAssistantUpdate,
    TAAvailability, TAAvailabilityCreate, APIResponse
)

router = APIRouter(prefix="/tas", tags=["Teaching Assistants"])


@router.get("/", response_model=List[TeachingAssistant])
async def list_teaching_assistants(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get all teaching assistants."""
    query = db.query(TADB)
    if active_only:
        query = query.filter(TADB.is_active == True)

    tas = query.offset(skip).limit(limit).all()
    return tas


@router.get("/{ta_id}", response_model=TeachingAssistant)
async def get_teaching_assistant(
    ta_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get teaching assistant by ID."""
    ta = db.query(TADB).filter(TADB.id == ta_id).first()
    if not ta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teaching assistant not found"
        )
    return ta


@router.post("/", response_model=APIResponse)
async def create_teaching_assistant(
    ta_data: TeachingAssistantCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new teaching assistant."""
    # Check if email already exists
    existing_ta = db.query(TADB).filter(TADB.email == ta_data.email).first()
    if existing_ta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    db_ta = TADB(
        name=ta_data.name,
        email=ta_data.email,
        max_weekly_hours=ta_data.max_weekly_hours,
        is_active=ta_data.is_active
    )

    db.add(db_ta)
    db.commit()
    db.refresh(db_ta)

    return APIResponse(
        success=True,
        message="Teaching assistant created successfully",
        data={"ta_id": db_ta.id}
    )


@router.put("/{ta_id}", response_model=APIResponse)
async def update_teaching_assistant(
    ta_id: int,
    ta_data: TeachingAssistantUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Update teaching assistant."""
    ta = db.query(TADB).filter(TADB.id == ta_id).first()
    if not ta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teaching assistant not found"
        )

    # Check email uniqueness if being updated
    if ta_data.email and ta_data.email != ta.email:
        existing_ta = db.query(TADB).filter(TADB.email == ta_data.email).first()
        if existing_ta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Update fields
    update_data = ta_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ta, field, value)

    db.commit()
    db.refresh(ta)

    return APIResponse(
        success=True,
        message="Teaching assistant updated successfully"
    )


@router.delete("/{ta_id}", response_model=APIResponse)
async def delete_teaching_assistant(
    ta_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_admin_user)
):
    """Delete teaching assistant (admin only)."""
    ta = db.query(TADB).filter(TADB.id == ta_id).first()
    if not ta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teaching assistant not found"
        )

    # Soft delete by setting inactive
    ta.is_active = False
    db.commit()

    return APIResponse(
        success=True,
        message="Teaching assistant deactivated successfully"
    )


@router.post("/{ta_id}/availability", response_model=APIResponse)
async def set_ta_availability(
    ta_id: int,
    availability_data: List[TAAvailabilityCreate],
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Set teaching assistant availability for multiple time slots."""
    # Verify TA exists
    ta = db.query(TADB).filter(TADB.id == ta_id).first()
    if not ta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teaching assistant not found"
        )

    # Delete existing availability
    db.query(TAAvailabilityDB).filter(TAAvailabilityDB.ta_id == ta_id).delete()

    # Add new availability
    for avail_data in availability_data:
        db_availability = TAAvailabilityDB(
            ta_id=ta_id,
            day=avail_data.day,
            slot_number=avail_data.slot_number,
            is_available=avail_data.is_available,
            preference_rank=avail_data.preference_rank
        )
        db.add(db_availability)

    db.commit()

    return APIResponse(
        success=True,
        message=f"Availability updated for {len(availability_data)} time slots"
    )


@router.get("/{ta_id}/availability", response_model=List[TAAvailability])
async def get_ta_availability(
    ta_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get teaching assistant availability."""
    availability = db.query(TAAvailabilityDB).filter(
        TAAvailabilityDB.ta_id == ta_id
    ).all()
    return availability


@router.put("/{ta_id}/availability/{availability_id}", response_model=APIResponse)
async def update_ta_availability_slot(
    ta_id: int,
    availability_id: int,
    availability_data: TAAvailabilityCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Update specific availability slot."""
    availability = db.query(TAAvailabilityDB).filter(
        TAAvailabilityDB.id == availability_id,
        TAAvailabilityDB.ta_id == ta_id
    ).first()

    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability slot not found"
        )

    # Update fields
    availability.day = availability_data.day
    availability.slot_number = availability_data.slot_number
    availability.is_available = availability_data.is_available
    availability.preference_rank = availability_data.preference_rank

    db.commit()

    return APIResponse(
        success=True,
        message="Availability slot updated successfully"
    )


@router.delete("/{ta_id}/availability/{availability_id}", response_model=APIResponse)
async def delete_ta_availability_slot(
    ta_id: int,
    availability_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Delete specific availability slot."""
    availability = db.query(TAAvailabilityDB).filter(
        TAAvailabilityDB.id == availability_id,
        TAAvailabilityDB.ta_id == ta_id
    ).first()

    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability slot not found"
        )

    db.delete(availability)
    db.commit()

    return APIResponse(
        success=True,
        message="Availability slot deleted successfully"
    )