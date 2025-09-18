from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json

app = FastAPI(title="GIU Scheduler API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample data storage (in-memory for demo)
schedules_db = []
courses_db = []
tas_db = []

# Basic models
class SchedulingPolicies(BaseModel):
    tutorial_lab_independence: bool = False
    tutorial_lab_equal_count: bool = False
    tutorial_lab_number_matching: bool = False
    fairness_mode: bool = False

class TimeSlot(BaseModel):
    id: int
    course_id: int
    day: str
    slot_number: int
    slot_type: str
    duration: int = 2
    created_at: str = "2024-01-01T00:00:00"

class Course(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    created_by: int = 1
    created_at: str = "2024-01-01T00:00:00"
    time_slots: List[TimeSlot] = []

class TeachingAssistant(BaseModel):
    id: int
    name: str
    email: str
    max_weekly_hours: int
    is_active: bool = True
    created_at: str = "2024-01-01T00:00:00"
    availability: List[Dict] = []

class ScheduleAssignment(BaseModel):
    id: int
    schedule_id: int
    course_id: int
    ta_id: int
    time_slot_id: int
    created_at: str = "2024-01-01T00:00:00"
    course: Course
    ta: TeachingAssistant
    time_slot: TimeSlot

class Schedule(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    policies: SchedulingPolicies
    status: str = "active"
    success: bool = True
    message: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None
    created_by: int = 1
    created_at: str = "2024-01-01T00:00:00"
    updated_at: Optional[str] = None
    assignments: List[ScheduleAssignment] = []

class ScheduleGenerationRequest(BaseModel):
    name: str
    description: Optional[str] = None
    policies: SchedulingPolicies
    course_ids: List[int]
    optimize: bool = True

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# Initialize sample data
def init_sample_data():
    # Add sample courses
    sample_course = Course(
        id=1,
        code="CS101",
        name="Introduction to Programming",
        description="Basic programming course",
        time_slots=[
            TimeSlot(id=1, course_id=1, day="sunday", slot_number=1, slot_type="tutorial"),
            TimeSlot(id=2, course_id=1, day="sunday", slot_number=2, slot_type="lab"),
            TimeSlot(id=3, course_id=1, day="monday", slot_number=1, slot_type="tutorial"),
            TimeSlot(id=4, course_id=1, day="monday", slot_number=2, slot_type="lab"),
        ]
    )
    courses_db.append(sample_course)

    # Add sample TAs
    sample_ta1 = TeachingAssistant(
        id=1,
        name="Ahmed Hassan",
        email="ahmed@giu.edu.eg",
        max_weekly_hours=8
    )
    sample_ta2 = TeachingAssistant(
        id=2,
        name="Sara Ali",
        email="sara@giu.edu.eg",
        max_weekly_hours=6
    )
    tas_db.extend([sample_ta1, sample_ta2])

    # Add sample schedule
    assignments = [
        ScheduleAssignment(
            id=1,
            schedule_id=1,
            course_id=1,
            ta_id=1,
            time_slot_id=1,
            course=sample_course,
            ta=sample_ta1,
            time_slot=sample_course.time_slots[0]
        ),
        ScheduleAssignment(
            id=2,
            schedule_id=1,
            course_id=1,
            ta_id=1,
            time_slot_id=2,
            course=sample_course,
            ta=sample_ta1,
            time_slot=sample_course.time_slots[1]
        ),
        ScheduleAssignment(
            id=3,
            schedule_id=1,
            course_id=1,
            ta_id=2,
            time_slot_id=3,
            course=sample_course,
            ta=sample_ta2,
            time_slot=sample_course.time_slots[2]
        )
    ]

    sample_schedule = Schedule(
        id=1,
        name="Fall 2024 Schedule",
        description="Main schedule for fall semester",
        policies=SchedulingPolicies(),
        assignments=assignments
    )
    schedules_db.append(sample_schedule)

# API Routes
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.get("/courses", response_model=List[Course])
async def get_courses():
    return courses_db

@app.get("/tas", response_model=List[TeachingAssistant])
async def get_tas():
    return tas_db

@app.get("/schedules", response_model=List[Schedule])
async def get_schedules():
    return schedules_db

@app.get("/schedules/{schedule_id}", response_model=Schedule)
async def get_schedule(schedule_id: int):
    schedule = next((s for s in schedules_db if s.id == schedule_id), None)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule

@app.post("/schedules/generate", response_model=APIResponse)
async def generate_schedule(request: ScheduleGenerationRequest):
    # Simple schedule generation
    new_id = len(schedules_db) + 1
    new_schedule = Schedule(
        id=new_id,
        name=request.name,
        description=request.description,
        policies=request.policies,
        assignments=[]  # For demo, empty assignments
    )
    schedules_db.append(new_schedule)

    return APIResponse(
        success=True,
        message="Schedule generated successfully",
        data={"schedule_id": new_id}
    )

@app.post("/schedules/{schedule_id}/swap", response_model=APIResponse)
async def swap_assignment(schedule_id: int, swap_data: dict):
    return APIResponse(
        success=True,
        message="Assignment swapped successfully"
    )

@app.post("/schedules/{schedule_id}/validate-swap")
async def validate_swap(schedule_id: int, validation_data: dict):
    return {
        "is_valid": True,
        "conflicts": [],
        "warnings": []
    }

@app.get("/schedules/{schedule_id}/conflicts")
async def get_conflicts(schedule_id: int):
    return {
        "schedule_id": schedule_id,
        "total_conflicts": 0,
        "conflicts": []
    }

@app.post("/schedules/{schedule_id}/export")
async def export_schedule(schedule_id: int, export_data: dict):
    format_type = export_data.get("format", "grid")

    if format_type == "csv":
        content = "TA,Course,Day,Slot,Type\nAhmed Hassan,CS101,Sunday,1,Tutorial\n"
    elif format_type == "list":
        content = "Schedule Export\n\nAssignments:\n- Ahmed Hassan: CS101 Tutorial on Sunday Slot 1\n"
    else:
        content = "Schedule Grid\n\n   | Sun | Mon | Tue\n1  | CS101T |     |\n2  | CS101L |     |\n"

    from fastapi.responses import Response
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=schedule_{schedule_id}.{format_type}"}
    )

# Initialize on startup
@app.on_event("startup")
async def startup():
    init_sample_data()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)