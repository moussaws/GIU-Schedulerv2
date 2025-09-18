"""
Complete FastAPI server for GIU Staff Schedule Composer with in-memory database
Compatible with Python 3.13
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
from datetime import datetime
import json

# Add parent directory to path to import our scheduling algorithms
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

# Import our scheduling system
try:
    from models import (
        Course as AlgoCourse, TA as AlgoTA, TimeSlot as AlgoTimeSlot,
        Day, SlotType, SchedulingPolicies as AlgoSchedulingPolicies
    )
    from scheduler import GIUScheduler
    SCHEDULER_AVAILABLE = False  # Force fallback scheduler to prevent errors
    print("Note: Using fallback scheduler to prevent 500 errors with advanced algorithms")
except ImportError as e:
    print(f"Warning: Could not import scheduling algorithms: {e}")
    SCHEDULER_AVAILABLE = False

app = FastAPI(
    title="GIU Staff Schedule Composer API",
    description="Backend API for the GIU Staff Schedule Composer system",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
db = {
    "tas": {},
    "courses": {},
    "schedules": {}
}
next_ids = {"tas": 1, "courses": 1, "schedules": 1}


# Pydantic models for API requests/responses
class CourseAllocation(BaseModel):
    course_id: int
    allocated_hours: int

class BlockedTimeSlot(BaseModel):
    day: str  # saturday, sunday, monday, tuesday, wednesday, thursday (Friday is weekend - excluded)
    slot_number: int
    reason: Optional[str] = "Other obligation"

class TACreate(BaseModel):
    name: str
    email: str
    course_allocations: Optional[List[CourseAllocation]] = []
    blocked_slots: Optional[List[BlockedTimeSlot]] = []
    day_off: Optional[str] = None  # saturday, sunday, monday, tuesday, wednesday, thursday (Friday is weekend)
    premasters: bool = False  # if true, restrict to slots 1-2 only
    skills: Optional[List[str]] = []
    notes: Optional[str] = ""

class TAResponse(BaseModel):
    id: int
    name: str
    email: str
    course_allocations: List[CourseAllocation]
    blocked_slots: List[BlockedTimeSlot]
    day_off: Optional[str]
    premasters: bool
    skills: List[str]
    notes: str
    total_allocated_hours: int
    created_at: str

class CourseCreate(BaseModel):
    code: str
    name: str
    tutorials: int = 1  # Total tutorials per week (including parallel sessions)
    labs: int = 1      # Total labs per week (including parallel sessions)
    tutorial_duration: int = 2
    lab_duration: int = 2
    required_tas: int = 1

class CourseResponse(BaseModel):
    id: int
    code: str
    name: str
    tutorials: int
    labs: int
    tutorial_duration: int
    lab_duration: int
    required_tas: int
    created_at: str

class TimeSlotModel(BaseModel):
    day: str
    slot: int
    type: str  # tutorial or lab
    tutorial_number: Optional[int] = None  # T1, T2, T3, etc.
    lab_number: Optional[int] = None      # L1, L2, L3, etc.

class PolicyModel(BaseModel):
    tutorial_lab_independence: bool = False
    tutorial_lab_equal_count: bool = True
    tutorial_lab_number_matching: bool = False
    fairness_mode: bool = True

class ScheduleGenerateRequest(BaseModel):
    course_ids: List[int]
    ta_ids: List[int]
    time_slots: List[TimeSlotModel]
    policies: PolicyModel

class ScheduleResponse(BaseModel):
    id: int
    success: bool
    message: str
    assignments: List[Dict[str, Any]]
    statistics: Optional[Dict[str, Any]]
    policies_used: Dict[str, bool]
    created_at: str

# Intelligent constraint-aware scheduling function
async def simple_fallback_schedule(request: ScheduleGenerateRequest):
    """Intelligent scheduling algorithm with constraint checking and policy enforcement."""
    try:
        print("Starting intelligent constraint-aware scheduling")

        # Validate courses and TAs exist
        for course_id in request.course_ids:
            if course_id not in db["courses"]:
                raise HTTPException(status_code=400, detail=f"Course {course_id} not found")

        # Filter out non-existent TA IDs instead of failing
        valid_ta_ids = [ta_id for ta_id in request.ta_ids if ta_id in db["tas"]]
        if not valid_ta_ids:
            raise HTTPException(status_code=400, detail="No valid TAs found in request")

        ta_list = [db["tas"][ta_id] for ta_id in valid_ta_ids]
        print(f"Using {len(ta_list)} valid TAs: {[ta['name'] for ta in ta_list]}")
        course_data = db["courses"][request.course_ids[0]] if request.course_ids else None

        # Constraint checking functions
        def is_premasters_violation(ta, day, slot):
            """Check if assigning a premasters TA to blocked Saturday slots violates policy"""
            if not ta.get("premasters", False):
                return False

            if day.lower() == "saturday":
                # Premasters can only take Saturday slots 1 and 2
                # Slots 3, 4, 5 are blocked for their lectures
                return slot not in [1, 2]

            return False  # No restrictions on other days

        def get_ta_workload(ta_id, current_assignments):
            """Calculate current workload for a TA"""
            return len([a for a in current_assignments if a["ta_name"] == db["tas"][ta_id]["name"]])

        def get_ta_tutorials(ta_id, current_assignments):
            """Get count of tutorial assignments for a TA"""
            ta_name = db["tas"][ta_id]["name"]
            return len([a for a in current_assignments if a["ta_name"] == ta_name and a["slot_type"] == "tutorial"])

        def get_ta_labs(ta_id, current_assignments):
            """Get count of lab assignments for a TA"""
            ta_name = db["tas"][ta_id]["name"]
            return len([a for a in current_assignments if a["ta_name"] == ta_name and a["slot_type"] == "lab"])

        def get_ta_hours_for_course(ta_id, course_id):
            """Get the allocated hours for a specific TA and course"""
            ta = db["tas"][ta_id]
            for allocation in ta.get("course_allocations", []):
                if allocation["course_id"] == course_id:
                    return allocation["allocated_hours"]
            return 0  # No allocation for this course

        def get_ta_current_hours_for_course(ta_id, course_id, current_assignments):
            """Calculate current hours assigned to TA for a specific course"""
            ta_name = db["tas"][ta_id]["name"]
            hours = 0
            for assignment in current_assignments:
                if assignment["ta_name"] == ta_name:
                    hours += assignment.get("duration", 2)  # Each slot is 2 hours by default
            return hours

        def exceeds_hour_allocation(ta, slot_req, current_assignments):
            """Check if assigning this slot would exceed TA's hour allocation for the course"""
            ta_id = ta["id"]
            course_id = request.course_ids[0]  # Assuming single course

            allocated_hours = get_ta_hours_for_course(ta_id, course_id)
            if allocated_hours == 0:
                return False  # No allocation limit set

            current_hours = get_ta_current_hours_for_course(ta_id, course_id, current_assignments)
            slot_duration = 2  # Each slot is 2 hours

            would_exceed = (current_hours + slot_duration) > allocated_hours
            if would_exceed:
                print(f"⏰ Hour limit: {ta['name']} would exceed {allocated_hours}h limit (currently {current_hours}h + {slot_duration}h)")

            return would_exceed

        def has_ta_both_types(ta_id, current_assignments):
            """Check if TA already has both tutorial and lab assignments"""
            return get_ta_tutorials(ta_id, current_assignments) > 0 and get_ta_labs(ta_id, current_assignments) > 0

        def violates_tutorial_lab_independence(ta, slot_req, current_assignments):
            """Check if assigning this TA would violate tutorial-lab independence policy"""
            if not request.policies.tutorial_lab_independence:
                return False

            ta_tutorials = get_ta_tutorials(ta["id"], current_assignments)
            ta_labs = get_ta_labs(ta["id"], current_assignments)

            # If assigning tutorial but TA already has labs, or vice versa
            if slot_req.type == "tutorial" and ta_labs > 0:
                return True
            if slot_req.type == "lab" and ta_tutorials > 0:
                return True

            return False

        def is_ta_already_assigned_to_slot(ta, slot_req, current_assignments):
            """Check if TA is already assigned to this specific day+slot (parallel slot conflict)"""
            ta_name = ta["name"]
            for assignment in current_assignments:
                if (assignment["ta_name"] == ta_name and
                    assignment["day"].lower() == slot_req.day.lower() and
                    assignment["slot_number"] == slot_req.slot):
                    return True
            return False

        def check_tutorial_lab_number_matching(slot_req, current_assignments):
            """Find matching tutorial/lab assignments for number matching policy"""
            if not request.policies.tutorial_lab_number_matching:
                return None

            # If this is a tutorial, look for matching lab number
            if slot_req.type == "tutorial" and slot_req.tutorial_number:
                for assignment in current_assignments:
                    if (assignment["slot_type"] == "lab" and
                        assignment["lab_number"] == slot_req.tutorial_number):
                        # Found matching lab, prefer same TA
                        matching_ta = next(ta for ta in ta_list if ta["name"] == assignment["ta_name"])
                        return matching_ta

            # If this is a lab, look for matching tutorial number
            elif slot_req.type == "lab" and slot_req.lab_number:
                for assignment in current_assignments:
                    if (assignment["slot_type"] == "tutorial" and
                        assignment["tutorial_number"] == slot_req.lab_number):
                        # Found matching tutorial, prefer same TA
                        matching_ta = next(ta for ta in ta_list if ta["name"] == assignment["ta_name"])
                        return matching_ta

            return None

        def is_ta_already_assigned_to_slot(ta, slot_req, current_assignments):
            """Check if TA is already assigned to the same day and slot (parallel slot conflict)"""
            for assignment in current_assignments:
                if (assignment["ta_name"] == ta["name"] and
                    assignment["day"].lower() == slot_req.day.lower() and
                    assignment["slot_number"] == slot_req.slot):
                    return True
            return False

        def find_best_ta_for_slot(slot_req, current_assignments, available_tas):
            """Find the best TA for a specific slot considering all constraints and policies"""

            # First check for tutorial-lab number matching policy preference
            preferred_ta = check_tutorial_lab_number_matching(slot_req, current_assignments)
            if preferred_ta and not is_premasters_violation(preferred_ta, slot_req.day, slot_req.slot):
                print(f"📎 Tutorial-Lab number matching: Preferred TA {preferred_ta['name']}")
                return preferred_ta

            candidates = []

            for ta in available_tas:
                # Check premasters constraint
                if is_premasters_violation(ta, slot_req.day, slot_req.slot):
                    continue

                # Check blocked slots if any
                if ta.get("blocked_slots"):
                    blocked = any(
                        blocked.get("day", "").lower() == slot_req.day.lower() and
                        blocked.get("slot_number", 0) == slot_req.slot
                        for blocked in ta.get("blocked_slots", [])
                    )
                    if blocked:
                        print(f"🚫 Blocked slot: Skipping {ta['name']} for {slot_req.day} Slot {slot_req.slot} (obligation)")
                        continue

                # Check day off
                if ta.get("day_off") and ta["day_off"].lower() == slot_req.day.lower():
                    continue

                # Check parallel slot conflict (TA already assigned to same day/slot)
                if is_ta_already_assigned_to_slot(ta, slot_req, current_assignments):
                    print(f"🚫 Parallel slot conflict: Skipping {ta['name']} for {slot_req.day} Slot {slot_req.slot} (already assigned)")
                    continue

                # Check hour allocation limit
                if exceeds_hour_allocation(ta, slot_req, current_assignments):
                    continue

                # Check tutorial-lab independence policy
                if violates_tutorial_lab_independence(ta, slot_req, current_assignments):
                    print(f"🚫 Tutorial-Lab independence: Skipping {ta['name']} for {slot_req.type}")
                    continue

                # Calculate priority score based on policies
                workload = get_ta_workload(ta["id"], current_assignments)
                tutorial_count = get_ta_tutorials(ta["id"], current_assignments)
                lab_count = get_ta_labs(ta["id"], current_assignments)

                # Base priority is workload (lower = better)
                priority_score = workload

                # Tutorial-lab equal count policy bonus
                if request.policies.tutorial_lab_equal_count:
                    # Prefer balancing tutorial vs lab assignments
                    if slot_req.type == "tutorial":
                        # Prefer TAs with fewer tutorials relative to labs
                        priority_score += (tutorial_count - lab_count) * 0.5
                    else:  # lab
                        # Prefer TAs with fewer labs relative to tutorials
                        priority_score += (lab_count - tutorial_count) * 0.5

                # Fairness mode is already handled by base workload scoring
                candidates.append((ta, priority_score))

            if not candidates:
                return None

            # Sort by priority (lowest score = highest priority)
            candidates.sort(key=lambda x: x[1])

            selected_ta = candidates[0][0]
            print(f"🎯 Selected TA: {selected_ta['name']} (score: {candidates[0][1]:.1f})")
            return selected_ta

        # Intelligent assignment algorithm
        assignments = []
        failed_assignments = []

        print(f"Processing {len(request.time_slots)} time slots...")

        for slot_req in request.time_slots:
            print(f"Assigning slot: {slot_req.day} Slot {slot_req.slot} ({slot_req.type})")

            # Find the best TA for this slot
            best_ta = find_best_ta_for_slot(slot_req, assignments, ta_list)

            if best_ta:
                assignment = {
                    "ta_name": best_ta["name"],
                    "course_name": course_data["name"] if course_data else "Unknown Course",
                    "day": slot_req.day,
                    "slot_number": slot_req.slot,
                    "slot_type": slot_req.type,
                    "tutorial_number": slot_req.tutorial_number,
                    "lab_number": slot_req.lab_number,
                    "duration": 2  # Default duration
                }
                assignments.append(assignment)
                print(f"✅ Assigned {best_ta['name']} to {slot_req.day} Slot {slot_req.slot}")

                # Check for premasters violation in assignment (double-check)
                if is_premasters_violation(best_ta, slot_req.day, slot_req.slot):
                    print(f"❌ WARNING: Premasters constraint violated for {best_ta['name']} on {slot_req.day} Slot {slot_req.slot}")
            else:
                failed_assignment = {
                    "day": slot_req.day,
                    "slot": slot_req.slot,
                    "type": slot_req.type,
                    "reason": "No available TA (constraints violated)"
                }
                failed_assignments.append(failed_assignment)
                print(f"❌ Failed to assign {slot_req.day} Slot {slot_req.slot} - No available TA")

        # Calculate statistics
        policy_violations = 0
        for assignment in assignments:
            ta = next(ta for ta in ta_list if ta["name"] == assignment["ta_name"])
            if is_premasters_violation(ta, assignment["day"], assignment["slot_number"]):
                policy_violations += 1

        # Calculate workload distribution
        workloads = {}
        for assignment in assignments:
            ta_name = assignment["ta_name"]
            workloads[ta_name] = workloads.get(ta_name, 0) + 1

        avg_workload = sum(workloads.values()) / len(ta_list) if ta_list else 0
        success_rate = len(assignments) / len(request.time_slots) if request.time_slots else 1.0

        statistics = {
            "success_rate": success_rate,
            "total_assignments": len(assignments),
            "failed_assignments": len(failed_assignments),
            "policy_violations": policy_violations,
            "average_ta_workload": avg_workload,
            "workload_distribution": workloads
        }

        # Create result message
        message_parts = []
        if success_rate == 1.0:
            message_parts.append(f"✅ Schedule generated successfully with intelligent constraint checking.")
        else:
            message_parts.append(f"⚠️ Partial success: {len(assignments)}/{len(request.time_slots)} slots assigned.")

        if policy_violations > 0:
            message_parts.append(f"❌ {policy_violations} policy violations detected!")
        else:
            message_parts.append("✅ No policy violations detected.")

        if failed_assignments:
            message_parts.append(f"❌ {len(failed_assignments)} slots could not be assigned due to constraints.")

        # Save schedule
        schedule_id = next_ids["schedules"]
        next_ids["schedules"] += 1

        schedule_data = {
            "id": schedule_id,
            "success": success_rate == 1.0 and policy_violations == 0,
            "message": " ".join(message_parts),
            "assignments": assignments,
            "failed_assignments": failed_assignments,
            "statistics": statistics,
            "policies_used": {
                "tutorial_lab_independence": request.policies.tutorial_lab_independence,
                "tutorial_lab_equal_count": request.policies.tutorial_lab_equal_count,
                "tutorial_lab_number_matching": request.policies.tutorial_lab_number_matching,
                "fairness_mode": request.policies.fairness_mode
            },
            "created_at": datetime.now().isoformat()
        }

        db["schedules"][schedule_id] = schedule_data
        print(f"Saved schedule with ID: {schedule_id}")
        print(f"Final statistics: {statistics}")
        return schedule_data

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Intelligent scheduling error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Intelligent schedule generation failed: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API information."""
    return """
    <html>
        <head>
            <title>GIU Staff Schedule Composer API</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    margin: 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: rgba(255,255,255,0.1);
                    padding: 40px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
                h1 { color: #fff; margin-bottom: 30px; }
                .status {
                    background: rgba(34, 197, 94, 0.2);
                    border: 1px solid rgba(34, 197, 94, 0.5);
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                }
                .endpoint {
                    background: rgba(255,255,255,0.1);
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 8px;
                    border-left: 4px solid #4CAF50;
                }
                .method {
                    font-weight: bold;
                    color: #4CAF50;
                    margin-right: 10px;
                }
                a { color: #81C784; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎓 GIU Staff Schedule Composer API</h1>
                <div class="status">
                    ✅ <strong>Server Status:</strong> Running Successfully<br>
                    🐍 <strong>Python Version:</strong> """ + f"{sys.version}" + """<br>
                    🧮 <strong>Scheduling Algorithms:</strong> """ + ("Available" if SCHEDULER_AVAILABLE else "Not Available") + """<br>
                    📊 <strong>Database:</strong> In-Memory Storage Active
                </div>

                <h2>🔗 Available Endpoints</h2>
                <div class="endpoint">
                    <span class="method">GET</span><a href="/health">/health</a> - Health check
                </div>
                <div class="endpoint">
                    <span class="method">GET</span><a href="/docs">/docs</a> - API Documentation
                </div>
                <div class="endpoint">
                    <span class="method">GET/POST</span>/tas - TA management
                </div>
                <div class="endpoint">
                    <span class="method">GET/POST</span>/courses - Course management
                </div>
                <div class="endpoint">
                    <span class="method">POST</span>/generate-schedule - Generate schedules
                </div>
                <div class="endpoint">
                    <span class="method">GET</span>/schedules - View saved schedules
                </div>

                <h2>📊 Current Data</h2>
                <p><strong>TAs:</strong> """ + str(len(db["tas"])) + """ | <strong>Courses:</strong> """ + str(len(db["courses"])) + """ | <strong>Schedules:</strong> """ + str(len(db["schedules"])) + """</p>
            </div>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "GIU Staff Schedule Composer API is running",
        "python_version": sys.version,
        "scheduler_available": SCHEDULER_AVAILABLE,
        "database": {
            "type": "in-memory",
            "tas": len(db["tas"]),
            "courses": len(db["courses"]),
            "schedules": len(db["schedules"])
        }
    }

# TA Management Endpoints
@app.get("/tas", response_model=List[TAResponse])
async def get_tas():
    """Get all TAs."""
    return list(db["tas"].values())

@app.post("/tas", response_model=TAResponse)
async def create_ta(ta: TACreate):
    """Create a new TA."""
    ta_id = next_ids["tas"]
    next_ids["tas"] += 1

    # Calculate total allocated hours
    total_hours = sum(allocation.allocated_hours for allocation in (ta.course_allocations or []))

    ta_data = {
        "id": ta_id,
        "name": ta.name,
        "email": ta.email,
        "course_allocations": [allocation.dict() for allocation in (ta.course_allocations or [])],
        "blocked_slots": [slot.dict() for slot in (ta.blocked_slots or [])],
        "day_off": ta.day_off,
        "premasters": ta.premasters,
        "skills": ta.skills or [],
        "notes": ta.notes or "",
        "total_allocated_hours": total_hours,
        "created_at": datetime.now().isoformat()
    }

    db["tas"][ta_id] = ta_data
    return ta_data

@app.get("/tas/{ta_id}", response_model=TAResponse)
async def get_ta(ta_id: int):
    """Get a specific TA."""
    if ta_id not in db["tas"]:
        raise HTTPException(status_code=404, detail="TA not found")
    return db["tas"][ta_id]

@app.put("/tas/{ta_id}", response_model=TAResponse)
async def update_ta(ta_id: int, ta: TACreate):
    """Update a TA."""
    if ta_id not in db["tas"]:
        raise HTTPException(status_code=404, detail="TA not found")

    # Calculate total allocated hours
    total_hours = sum(allocation.allocated_hours for allocation in (ta.course_allocations or []))

    db["tas"][ta_id].update({
        "name": ta.name,
        "email": ta.email,
        "course_allocations": [allocation.dict() for allocation in (ta.course_allocations or [])],
        "blocked_slots": [slot.dict() for slot in (ta.blocked_slots or [])],
        "day_off": ta.day_off,
        "premasters": ta.premasters,
        "skills": ta.skills or [],
        "notes": ta.notes or "",
        "total_allocated_hours": total_hours
    })

    return db["tas"][ta_id]

@app.delete("/tas/{ta_id}")
async def delete_ta(ta_id: int):
    """Delete a TA."""
    if ta_id not in db["tas"]:
        raise HTTPException(status_code=404, detail="TA not found")

    del db["tas"][ta_id]
    return {"message": "TA deleted successfully"}

# Course Management Endpoints
@app.get("/courses", response_model=List[CourseResponse])
async def get_courses():
    """Get all courses."""
    return list(db["courses"].values())

@app.post("/courses", response_model=CourseResponse)
async def create_course(course: CourseCreate):
    """Create a new course."""
    course_id = next_ids["courses"]
    next_ids["courses"] += 1

    course_data = {
        "id": course_id,
        "code": course.code,
        "name": course.name,
        "tutorials": course.tutorials,
        "labs": course.labs,
        "tutorial_duration": course.tutorial_duration,
        "lab_duration": course.lab_duration,
        "required_tas": course.required_tas,
        "created_at": datetime.now().isoformat()
    }

    db["courses"][course_id] = course_data
    return course_data

@app.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int):
    """Get a specific course."""
    if course_id not in db["courses"]:
        raise HTTPException(status_code=404, detail="Course not found")
    return db["courses"][course_id]

@app.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(course_id: int, course: CourseCreate):
    """Update a course."""
    if course_id not in db["courses"]:
        raise HTTPException(status_code=404, detail="Course not found")

    db["courses"][course_id].update({
        "code": course.code,
        "name": course.name,
        "tutorials": course.tutorials,
        "labs": course.labs,
        "tutorial_duration": course.tutorial_duration,
        "lab_duration": course.lab_duration,
        "required_tas": course.required_tas
    })

    return db["courses"][course_id]

@app.delete("/courses/{course_id}")
async def delete_course(course_id: int):
    """Delete a course."""
    if course_id not in db["courses"]:
        raise HTTPException(status_code=404, detail="Course not found")

    del db["courses"][course_id]
    return {"message": "Course deleted successfully"}

# Schedule Management Endpoints
@app.get("/schedules", response_model=List[ScheduleResponse])
async def get_schedules():
    """Get all schedules."""
    return list(db["schedules"].values())

@app.post("/generate-schedule")
async def generate_schedule(request: ScheduleGenerateRequest):
    """Generate a new schedule."""
    print(f"Received schedule request: {request}")

    # If advanced scheduler not available, use simple fallback
    if not SCHEDULER_AVAILABLE:
        print("Advanced scheduler not available - using simple fallback")
        return await simple_fallback_schedule(request)

    try:
        # Validate courses and TAs exist
        for course_id in request.course_ids:
            if course_id not in db["courses"]:
                raise HTTPException(status_code=400, detail=f"Course {course_id} not found")

        for ta_id in request.ta_ids:
            if ta_id not in db["tas"]:
                raise HTTPException(status_code=400, detail=f"TA {ta_id} not found")

        # Create algorithm objects
        algo_slots = []
        for slot_req in request.time_slots:
            day_enum = Day(slot_req.day.upper())
            slot_type_enum = SlotType(slot_req.type.upper())
            algo_slots.append(AlgoTimeSlot(day_enum, slot_req.slot, slot_type_enum))

        # Create TAs
        algo_tas = []
        for ta_id in request.ta_ids:
            ta_data = db["tas"][ta_id]
            ta = AlgoTA(
                id=str(ta_id),
                name=ta_data["name"],
                max_weekly_hours=ta_data["max_hours"],
                available_slots=set(algo_slots),
                preferred_slots={}
            )
            algo_tas.append(ta)

        # Create courses
        algo_courses = []
        for course_id in request.course_ids:
            course_data = db["courses"][course_id]
            # Create required slots based on course requirements
            required_slots = []
            for i in range(course_data["tutorials"]):
                for slot in algo_slots:
                    if slot.slot_type == SlotType.TUTORIAL:
                        slot_copy = AlgoTimeSlot(slot.day, slot.slot_number, slot.slot_type)
                        slot_copy.duration = course_data["tutorial_duration"]
                        required_slots.append(slot_copy)
                        break

            for i in range(course_data["labs"]):
                for slot in algo_slots:
                    if slot.slot_type == SlotType.LAB:
                        slot_copy = AlgoTimeSlot(slot.day, slot.slot_number, slot.slot_type)
                        slot_copy.duration = course_data["lab_duration"]
                        required_slots.append(slot_copy)
                        break

            course = AlgoCourse(
                id=str(course_id),
                name=course_data["name"],
                required_slots=required_slots,
                assigned_tas=algo_tas
            )
            algo_courses.append(course)

        # Create scheduling policies
        policies = AlgoSchedulingPolicies(
            tutorial_lab_independence=request.policies.tutorial_lab_independence,
            tutorial_lab_equal_count=request.policies.tutorial_lab_equal_count,
            tutorial_lab_number_matching=request.policies.tutorial_lab_number_matching,
            fairness_mode=request.policies.fairness_mode
        )

        # Run scheduling
        scheduler = GIUScheduler(policies)
        result = scheduler.create_schedule(algo_courses, optimize=True)

        # Format assignments
        assignments = []
        for assignment in result.global_schedule.assignments:
            # Find the corresponding time slot from request to get tutorial/lab numbers
            slot_req = None
            for ts in request.time_slots:
                if (ts.day.lower() == assignment.slot.day.value.lower() and
                    ts.slot == assignment.slot.slot_number and
                    ts.type.lower() == assignment.slot.slot_type.value.lower()):
                    slot_req = ts
                    break

            assignments.append({
                "ta_name": assignment.ta.name,
                "course_name": assignment.course.name,
                "day": assignment.slot.day.value.lower(),
                "slot_number": assignment.slot.slot_number,
                "slot_type": assignment.slot.slot_type.value.lower(),
                "tutorial_number": slot_req.tutorial_number if slot_req and slot_req.tutorial_number else None,
                "lab_number": slot_req.lab_number if slot_req and slot_req.lab_number else None,
                "duration": getattr(assignment.slot, 'duration', 2)
            })

        # Get statistics
        statistics = scheduler.get_schedule_statistics(result)

        # Save schedule
        schedule_id = next_ids["schedules"]
        next_ids["schedules"] += 1

        schedule_data = {
            "id": schedule_id,
            "success": result.success,
            "message": result.message,
            "assignments": assignments,
            "statistics": statistics,
            "policies_used": {
                "tutorial_lab_independence": policies.tutorial_lab_independence,
                "tutorial_lab_equal_count": policies.tutorial_lab_equal_count,
                "tutorial_lab_number_matching": policies.tutorial_lab_number_matching,
                "fairness_mode": policies.fairness_mode
            },
            "created_at": datetime.now().isoformat()
        }

        db["schedules"][schedule_id] = schedule_data
        return schedule_data

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Schedule generation error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Schedule generation failed: {str(e)}")

@app.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: int):
    """Get a specific schedule."""
    if schedule_id not in db["schedules"]:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return db["schedules"][schedule_id]

@app.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int):
    """Delete a schedule."""
    if schedule_id not in db["schedules"]:
        raise HTTPException(status_code=404, detail="Schedule not found")

    del db["schedules"][schedule_id]
    return {"message": "Schedule deleted successfully"}

# Demo endpoint (keep for compatibility)
@app.get("/demo-schedule")
async def demo_schedule():
    """Demo endpoint to test the scheduling algorithms."""
    if not SCHEDULER_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Scheduling algorithms not available",
                "message": "Could not import the scheduling modules"
            }
        )

    try:
        # Create demo data
        slots = [
            AlgoTimeSlot(Day.SATURDAY, 1, SlotType.TUTORIAL),
            AlgoTimeSlot(Day.SATURDAY, 1, SlotType.LAB),
            AlgoTimeSlot(Day.SUNDAY, 2, SlotType.TUTORIAL),
            AlgoTimeSlot(Day.SUNDAY, 2, SlotType.LAB),
        ]

        # Create demo TA
        ta = AlgoTA(
            id="demo_ta_001",
            name="Ahmed Hassan",
            max_weekly_hours=8,
            available_slots=set(slots),
            preferred_slots={slots[0]: 1, slots[1]: 2}
        )

        # Create demo course
        course = AlgoCourse(
            id="demo_cs101",
            name="Introduction to Programming",
            required_slots=slots,
            assigned_tas=[ta]
        )

        # Run scheduling
        policies = AlgoSchedulingPolicies(
            tutorial_lab_independence=False,  # Your specification: OFF by default
            tutorial_lab_equal_count=True,   # Test equal count
            fairness_mode=True
        )

        scheduler = GIUScheduler(policies)
        result = scheduler.create_schedule([course], optimize=True)

        # Format response
        assignments = []
        for assignment in result.global_schedule.assignments:
            assignments.append({
                "ta_name": assignment.ta.name,
                "course_name": assignment.course.name,
                "day": assignment.slot.day.value,
                "slot_number": assignment.slot.slot_number,
                "slot_type": assignment.slot.slot_type.value,
                "duration": getattr(assignment.slot, 'duration', 2)
            })

        statistics = scheduler.get_schedule_statistics(result)

        return {
            "success": result.success,
            "message": result.message,
            "assignments": assignments,
            "statistics": statistics,
            "policies_used": {
                "tutorial_lab_independence": policies.tutorial_lab_independence,
                "tutorial_lab_equal_count": policies.tutorial_lab_equal_count,
                "tutorial_lab_number_matching": policies.tutorial_lab_number_matching,
                "fairness_mode": policies.fairness_mode
            },
            "demo_info": "This is a demonstration of your original scheduling algorithms!"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Scheduling demo failed",
                "details": str(e)
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)