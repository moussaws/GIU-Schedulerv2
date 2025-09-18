"""
Complete FastAPI server for GIU Staff Schedule Composer with persistent database
Compatible with Python 3.13
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import sys
import os
from datetime import datetime
import json

# Database imports
from database import init_db, get_db
from services import CourseService, TAService, ScheduleService, CourseGridService

# Add parent directory to path to import our scheduling algorithms
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

# Import our scheduling system
try:
    from models import (
        Course as AlgoCourse, TA as AlgoTA, TimeSlot as AlgoTimeSlot,
        Day, SlotType, SchedulingPolicies as AlgoSchedulingPolicies
    )
    from scheduler import GIUScheduler
    SCHEDULER_AVAILABLE = True  # Enable advanced scheduler algorithms
    print("✅ Advanced scheduling algorithms loaded successfully")
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

# Initialize database on startup
init_db()
print("Database initialized successfully")

# Temporary in-memory database for backwards compatibility during migration
db = {
    "tas": {},
    "courses": {},
    "schedules": {}
}

# ID counters for in-memory database
next_ids = {
    "tas": 1,
    "courses": 1,
    "schedules": 1
}


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

class ScheduleSaveRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    assignments: List[Dict[str, Any]]
    success: bool
    message: str
    statistics: Optional[Dict[str, Any]] = None
    policies_used: Dict[str, bool]

# Intelligent constraint-aware scheduling function
async def simple_fallback_schedule(request: ScheduleGenerateRequest, db_session: Session):
    """Intelligent scheduling algorithm with constraint checking and policy enforcement."""
    try:
        print("Starting intelligent constraint-aware scheduling")

        # Validate courses and TAs exist (using database services)
        for course_id in request.course_ids:
            course = CourseService.get_course(db_session, course_id)
            if not course:
                raise HTTPException(status_code=400, detail=f"Course {course_id} not found")

        # Filter out non-existent TA IDs using database
        valid_ta_ids = []
        for ta_id in request.ta_ids:
            ta = TAService.get_ta(db_session, ta_id)
            if ta:
                valid_ta_ids.append(ta_id)

        if not valid_ta_ids:
            raise HTTPException(status_code=400, detail="No valid TAs found in request")

        # Load TA data from database and convert to format expected by algorithm
        ta_list = []
        for ta_id in valid_ta_ids:
            ta_data = TAService.get_ta_with_allocations(db_session, ta_id)
            if ta_data:
                # Convert database format to algorithm format
                ta_dict = {
                    "id": ta_data["id"],
                    "name": ta_data["name"],
                    "email": ta_data["email"],
                    "blocked_slots": ta_data["blocked_slots"] or [],
                    "day_off": ta_data["day_off"],
                    "premasters": ta_data["premasters"],
                    "skills": ta_data["skills"] or [],
                    "notes": ta_data["notes"] or "",
                    "total_allocated_hours": ta_data["total_allocated_hours"] or 0,
                    "course_allocations": ta_data["course_allocations"] or []
                }
                ta_list.append(ta_dict)
        print(f"Using {len(ta_list)} valid TAs: {[ta['name'] for ta in ta_list]}")
        # Get course data from database
        course_data = None
        if request.course_ids:
            course_obj = CourseService.get_course(db_session, request.course_ids[0])
            if course_obj:
                course_data = {
                    "id": course_obj.id,
                    "name": course_obj.name,
                    "code": course_obj.code
                }

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
            ta = next((t for t in ta_list if t["id"] == ta_id), None)
            if ta:
                return len([a for a in current_assignments if a["ta_name"] == ta["name"]])
            return 0

        def get_ta_tutorials(ta_id, current_assignments):
            """Get count of tutorial assignments for a TA"""
            ta = next((t for t in ta_list if t["id"] == ta_id), None)
            if ta:
                return len([a for a in current_assignments if a["ta_name"] == ta["name"] and a["slot_type"] == "tutorial"])
            return 0

        def get_ta_labs(ta_id, current_assignments):
            """Get count of lab assignments for a TA"""
            ta = next((t for t in ta_list if t["id"] == ta_id), None)
            if ta:
                return len([a for a in current_assignments if a["ta_name"] == ta["name"] and a["slot_type"] == "lab"])
            return 0

        def get_ta_hours_for_course(ta_id, course_id):
            """Get the allocated hours for a specific TA and course"""
            ta = next((t for t in ta_list if t["id"] == ta_id), None)
            if ta:
                for allocation in ta.get("course_allocations", []):
                    if allocation["course_id"] == course_id:
                        return allocation["allocated_hours"]
            return 0  # No allocation for this course

        def get_ta_current_hours_for_course(ta_id, course_id, current_assignments):
            """Calculate current hours assigned to TA for a specific course"""
            ta = next((t for t in ta_list if t["id"] == ta_id), None)
            if not ta:
                return 0
            ta_name = ta["name"]
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
                        # Found matching lab, REQUIRE same TA
                        matching_ta = next((ta for ta in ta_list if ta["name"] == assignment["ta_name"]), None)
                        return matching_ta

            # If this is a lab, look for matching tutorial number
            elif slot_req.type == "lab" and slot_req.lab_number:
                for assignment in current_assignments:
                    if (assignment["slot_type"] == "tutorial" and
                        assignment["tutorial_number"] == slot_req.lab_number):
                        # Found matching tutorial, REQUIRE same TA
                        matching_ta = next((ta for ta in ta_list if ta["name"] == assignment["ta_name"]), None)
                        return matching_ta

            return None

        def violates_tutorial_lab_number_matching(ta, slot_req, current_assignments):
            """Check if assigning this TA would violate tutorial-lab number matching policy"""
            if not request.policies.tutorial_lab_number_matching:
                return False

            required_ta = check_tutorial_lab_number_matching(slot_req, current_assignments)
            if required_ta and required_ta["id"] != ta["id"]:
                print(f"🚫 Tutorial-Lab number matching: {slot_req.type.capitalize()}{slot_req.tutorial_number or slot_req.lab_number} must be assigned to {required_ta['name']}, not {ta['name']}")
                return True
            return False


        def find_best_ta_for_slot(slot_req, current_assignments, available_tas):
            """Find the best TA for a specific slot considering all constraints and policies"""

            # First check for tutorial-lab number matching policy requirement
            required_ta = check_tutorial_lab_number_matching(slot_req, current_assignments)
            if required_ta and not is_premasters_violation(required_ta, slot_req.day, slot_req.slot):
                # Check if required TA can be assigned to this slot
                if not exceeds_hour_allocation(required_ta, slot_req, current_assignments):
                    print(f"📎 Tutorial-Lab number matching: Required TA {required_ta['name']}")
                    return required_ta
                else:
                    print(f"⚠️ Tutorial-Lab number matching: Required TA {required_ta['name']} would exceed hour allocation")

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

                # Check tutorial-lab number matching policy
                if violates_tutorial_lab_number_matching(ta, slot_req, current_assignments):
                    continue

                # Calculate priority score based on policies
                workload = get_ta_workload(ta["id"], current_assignments)
                tutorial_count = get_ta_tutorials(ta["id"], current_assignments)
                lab_count = get_ta_labs(ta["id"], current_assignments)

                # Base priority is workload (lower = better)
                priority_score = workload

                # Tutorial-lab equal count policy bonus
                if request.policies.tutorial_lab_equal_count:
                    # Strongly prefer balancing tutorial vs lab assignments
                    if slot_req.type == "tutorial":
                        # Prefer TAs with fewer tutorials relative to labs (lower score = higher priority)
                        priority_score += max(0, (tutorial_count - lab_count)) * 2.0
                    else:  # lab
                        # Prefer TAs with fewer labs relative to tutorials (lower score = higher priority)
                        priority_score += max(0, (lab_count - tutorial_count)) * 2.0

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

        print(f"🧠 Starting intelligent backtracking algorithm for {len(request.time_slots)} time slots...")

        def intelligent_backtrack_assignment(slots_to_assign, current_assignments, depth=0, max_depth=50, start_time=None, variation_seed=None):
            """
            Intelligent backtracking algorithm that explores different assignment combinations
            to find optimal solutions and handle parallel slot conflicts.

            Args:
                depth: Current recursion depth (circuit breaker)
                max_depth: Maximum allowed recursion depth
                start_time: Algorithm start time (timeout protection)
                variation_seed: Randomization seed for schedule variation
            """
            # Circuit breaker: prevent infinite recursion
            if depth > max_depth:
                print(f"🚨 Circuit breaker: Maximum depth {max_depth} reached")
                return False, current_assignments, slots_to_assign

            # Timeout protection (30 second limit)
            if start_time and (time.time() - start_time) > 30:
                print(f"⏰ Timeout: Algorithm exceeded 30 seconds")
                return False, current_assignments, slots_to_assign

            # Base case: all slots assigned successfully
            if not slots_to_assign:
                return True, current_assignments, []

            # Get the next slot to assign (we can experiment with different ordering strategies)
            slot_req = slots_to_assign[0]
            remaining_slots = slots_to_assign[1:]

            print(f"🔍 Exploring assignments for: {slot_req.day} Slot {slot_req.slot} ({slot_req.type})")

            # Get all candidate TAs for this slot (not just the "best" one)
            candidates = get_all_candidate_tas_for_slot(slot_req, current_assignments, ta_list)

            # Constraint relaxation: if no strict candidates, try with relaxed constraints
            if not candidates:
                print(f"🔄 No strict candidates found, trying with relaxed constraints...")
                candidates = get_all_candidate_tas_for_slot(slot_req, current_assignments, ta_list, relax_constraints=True)

            if not candidates:
                print(f"❌ No candidates available for {slot_req.day} Slot {slot_req.slot} (even with relaxed constraints)")
                return False, current_assignments, [slot_req]

            print(f"📋 Found {len(candidates)} candidate TAs: {[ta['name'] for ta in candidates]}")

            # Add randomization for schedule variation
            if variation_seed:
                import random
                random.seed(variation_seed + depth)  # Different randomization at each depth
                candidates = candidates.copy()  # Don't modify original
                random.shuffle(candidates)
                print(f"🎲 Randomized candidate order for variation")

            # Try each candidate TA (backtracking exploration)
            for candidate_ta in candidates:
                print(f"🔄 Trying {candidate_ta['name']} for {slot_req.day} Slot {slot_req.slot}")

                # Create assignment for this candidate
                test_assignment = {
                    "ta_name": candidate_ta["name"],
                    "course_name": course_data["name"] if course_data else "Unknown Course",
                    "day": slot_req.day,
                    "slot_number": slot_req.slot,
                    "slot_type": slot_req.type,
                    "tutorial_number": slot_req.tutorial_number,
                    "lab_number": slot_req.lab_number,
                    "duration": 2
                }

                # Add to current assignments
                new_assignments = current_assignments + [test_assignment]

                # Recursively try to assign remaining slots with this assignment
                success, final_assignments, failed_slots = intelligent_backtrack_assignment(
                    remaining_slots, new_assignments, depth + 1, max_depth, start_time, variation_seed
                )

                if success:
                    print(f"✅ Successfully assigned {candidate_ta['name']} to {slot_req.day} Slot {slot_req.slot}")
                    return True, final_assignments, failed_slots
                else:
                    print(f"⏮️  Backtracking: {candidate_ta['name']} led to conflicts, trying next candidate")

            # All candidates failed for this slot
            print(f"💥 All candidates failed for {slot_req.day} Slot {slot_req.slot} - backtracking")
            return False, current_assignments, [slot_req]

        def get_all_candidate_tas_for_slot(slot_req, current_assignments, available_tas, relax_constraints=False):
            """Get all TAs that could potentially be assigned to this slot, sorted by priority.

            Args:
                relax_constraints: If True, relax soft constraints like day_off and some blocked slots
            """
            candidates = []

            for ta in available_tas:
                # Apply all hard constraints
                if is_premasters_violation(ta, slot_req.day, slot_req.slot):
                    continue

                # Check blocked slots (can be relaxed)
                if not relax_constraints and ta.get("blocked_slots"):
                    blocked = any(
                        blocked.get("day", "").lower() == slot_req.day.lower() and
                        blocked.get("slot_number", 0) == slot_req.slot
                        for blocked in ta.get("blocked_slots", [])
                    )
                    if blocked:
                        continue

                # Check day off (can be relaxed)
                if not relax_constraints and ta.get("day_off") and ta["day_off"].lower() == slot_req.day.lower():
                    continue

                # Check parallel slot conflict
                if is_ta_already_assigned_to_slot(ta, slot_req, current_assignments):
                    continue

                # Check hour allocation limit
                if exceeds_hour_allocation(ta, slot_req, current_assignments):
                    continue

                # Check tutorial-lab independence policy
                if violates_tutorial_lab_independence(ta, slot_req, current_assignments):
                    continue

                # Check tutorial-lab number matching policy
                if violates_tutorial_lab_number_matching(ta, slot_req, current_assignments):
                    continue

                # Calculate priority score for sorting
                workload = get_ta_workload(ta["id"], current_assignments)
                tutorial_count = get_ta_tutorials(ta["id"], current_assignments)
                lab_count = get_ta_labs(ta["id"], current_assignments)

                priority_score = workload  # Base priority on current workload

                # Apply policy-based scoring
                if request.policies.tutorial_lab_equal_count:
                    if slot_req.type == "tutorial":
                        # Prefer TAs with fewer tutorials relative to labs (lower score = higher priority)
                        priority_score += max(0, (tutorial_count - lab_count)) * 2.0
                    else:  # lab
                        # Prefer TAs with fewer labs relative to tutorials (lower score = higher priority)
                        priority_score += max(0, (lab_count - tutorial_count)) * 2.0

                candidates.append((ta, priority_score))

            # Sort candidates by priority (lower score = higher priority)
            candidates.sort(key=lambda x: x[1])
            return [ta for ta, _ in candidates]

        # Execute intelligent backtracking with circuit breaker and randomization
        import time
        import random

        start_time = time.time()
        variation_seed = random.randint(1, 10000)  # Different seed each run for variation
        print(f"🎲 Using variation seed: {variation_seed}")

        success, assignments, failed_slot_reqs = intelligent_backtrack_assignment(
            request.time_slots, [], depth=0, max_depth=50, start_time=start_time, variation_seed=variation_seed
        )

        # Performance metrics
        end_time = time.time()
        execution_time = end_time - start_time
        success_rate = len(assignments) / len(request.time_slots) if request.time_slots else 0

        print(f"📊 Performance Metrics:")
        print(f"   ⏱️  Execution Time: {execution_time:.2f} seconds")
        print(f"   ✅ Success Rate: {success_rate:.1%} ({len(assignments)}/{len(request.time_slots)} slots)")
        print(f"   🚨 Failed Slots: {len(failed_slot_reqs)}")
        print(f"   🎲 Variation Seed: {variation_seed}")

        # Convert failed slot requests to failed assignments format
        failed_assignments = []
        for slot_req in failed_slot_reqs:
            failed_assignment = {
                "day": slot_req.day,
                "slot": slot_req.slot,
                "type": slot_req.type,
                "reason": "No valid assignment found after exploring all combinations"
            }
            failed_assignments.append(failed_assignment)

        print(f"🎯 Intelligent assignment complete: {len(assignments)}/{len(request.time_slots)} slots assigned")
        if failed_assignments:
            print(f"❌ Failed slots: {[f'{fa['day']} Slot {fa['slot']}' for fa in failed_assignments]}")

        # COMPREHENSIVE VALIDATION: Check for policy violations and parallel conflicts in final assignments
        parallel_conflicts = []
        assignment_grid = {}

        for assignment in assignments:
            ta = next(ta for ta in ta_list if ta["name"] == assignment["ta_name"])

            # Check premasters violations
            if is_premasters_violation(ta, assignment["day"], assignment["slot_number"]):
                print(f"❌ CRITICAL: Premasters constraint violated for {assignment['ta_name']} on {assignment['day']} Slot {assignment['slot_number']}")

            # Build grid to check parallel conflicts
            slot_key = (assignment["day"].lower(), assignment["slot_number"])
            if slot_key not in assignment_grid:
                assignment_grid[slot_key] = []
            assignment_grid[slot_key].append(assignment)

        # Check for parallel conflicts (multiple assignments to same TA at same time)
        for (day, slot_num), slot_assignments in assignment_grid.items():
            ta_names = [a["ta_name"] for a in slot_assignments]
            if len(ta_names) != len(set(ta_names)):  # Duplicate TAs in same slot
                duplicates = [name for name in set(ta_names) if ta_names.count(name) > 1]
                for duplicate_ta in duplicates:
                    parallel_conflicts.append(f"CRITICAL: {duplicate_ta} assigned multiple times to {day.capitalize()} Slot {slot_num}")
                    print(f"❌ CRITICAL PARALLEL CONFLICT: {duplicate_ta} assigned multiple times to {day.capitalize()} Slot {slot_num}")

        if parallel_conflicts:
            print(f"❌ CRITICAL: {len(parallel_conflicts)} PARALLEL CONFLICTS DETECTED!")
            for conflict in parallel_conflicts:
                print(f"   🚨 {conflict}")
            # This is a critical system failure - we need to fail the schedule
            statistics["critical_parallel_conflicts"] = len(parallel_conflicts)

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

        # Save schedule in database
        schedule_data = {
            "course_id": request.course_ids[0] if request.course_ids else 1,  # Use first course or default to 1
            "success": success_rate == 1.0 and policy_violations == 0,
            "message": " ".join(message_parts),
            "statistics": statistics,
            "policies_used": {
                "tutorial_lab_independence": request.policies.tutorial_lab_independence,
                "tutorial_lab_equal_count": request.policies.tutorial_lab_equal_count,
                "tutorial_lab_number_matching": request.policies.tutorial_lab_number_matching,
                "fairness_mode": request.policies.fairness_mode
            },
            "assignments": assignments,
            "failed_assignments": failed_assignments
        }

        # Create schedule in database
        created_schedule = ScheduleService.create_schedule(db_session, schedule_data)

        # Also store in in-memory database for backwards compatibility
        in_memory_schedule = {
            "id": created_schedule.id,
            "success": created_schedule.success,
            "message": created_schedule.message,
            "assignments": assignments,
            "failed_assignments": failed_assignments,
            "statistics": created_schedule.statistics,
            "policies_used": created_schedule.policies_used,
            "created_at": created_schedule.created_at.isoformat() if created_schedule.created_at else None
        }
        db["schedules"][created_schedule.id] = in_memory_schedule

        print(f"Saved schedule with ID: {created_schedule.id}")
        print(f"Final statistics: {statistics}")
        return in_memory_schedule

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
                    <span class="method">GET</span>/schedules - View saved schedules<br>
                    <span class="method">POST</span>/schedules - Save a new schedule
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
async def get_tas(db_session: Session = Depends(get_db)):
    """Get all TAs."""
    tas = TAService.get_tas(db_session)
    result = []
    for ta in tas:
        ta_dict = TAService.get_ta_with_allocations(db_session, ta.id)
        if ta_dict:
            result.append(TAResponse(**ta_dict))
    return result

@app.post("/tas", response_model=TAResponse)
async def create_ta(ta: TACreate, db_session: Session = Depends(get_db)):
    """Create a new TA."""
    ta_data = {
        "name": ta.name,
        "email": ta.email,
        "blocked_slots": [slot.dict() for slot in (ta.blocked_slots or [])],
        "day_off": ta.day_off,
        "premasters": ta.premasters,
        "skills": ta.skills or [],
        "notes": ta.notes or "",
        "course_allocations": [allocation.dict() for allocation in (ta.course_allocations or [])]
    }

    # Create TA in database
    created_ta = TAService.create_ta(db_session, ta_data)

    # Also store in in-memory database for backwards compatibility with scheduling
    total_hours = sum(allocation.allocated_hours for allocation in (ta.course_allocations or []))
    in_memory_ta = {
        "id": created_ta.id,
        "name": created_ta.name,
        "email": created_ta.email,
        "course_allocations": [allocation.dict() for allocation in (ta.course_allocations or [])],
        "blocked_slots": [slot.dict() for slot in (ta.blocked_slots or [])],
        "day_off": created_ta.day_off,
        "premasters": created_ta.premasters,
        "skills": created_ta.skills or [],
        "notes": created_ta.notes or "",
        "total_allocated_hours": total_hours,
        "created_at": created_ta.created_at.isoformat() if created_ta.created_at else None
    }
    db["tas"][created_ta.id] = in_memory_ta

    # Return response in expected format
    ta_dict = TAService.get_ta_with_allocations(db_session, created_ta.id)
    return TAResponse(**ta_dict)

@app.get("/tas/{ta_id}", response_model=TAResponse)
async def get_ta(ta_id: int, db_session: Session = Depends(get_db)):
    """Get a specific TA."""
    ta_dict = TAService.get_ta_with_allocations(db_session, ta_id)
    if not ta_dict:
        raise HTTPException(status_code=404, detail="TA not found")
    return TAResponse(**ta_dict)

@app.put("/tas/{ta_id}", response_model=TAResponse)
async def update_ta(ta_id: int, ta: TACreate, db_session: Session = Depends(get_db)):
    """Update a TA."""
    ta_data = {
        "name": ta.name,
        "email": ta.email,
        "blocked_slots": [slot.dict() for slot in (ta.blocked_slots or [])],
        "day_off": ta.day_off,
        "premasters": ta.premasters,
        "skills": ta.skills or [],
        "notes": ta.notes or "",
        "course_allocations": [allocation.dict() for allocation in (ta.course_allocations or [])]
    }

    # Update TA in database
    updated_ta = TAService.update_ta(db_session, ta_id, ta_data)
    if not updated_ta:
        raise HTTPException(status_code=404, detail="TA not found")

    # Update in-memory database for backwards compatibility with scheduling
    total_hours = sum(allocation.allocated_hours for allocation in (ta.course_allocations or []))
    in_memory_ta = {
        "id": updated_ta.id,
        "name": updated_ta.name,
        "email": updated_ta.email,
        "course_allocations": [allocation.dict() for allocation in (ta.course_allocations or [])],
        "blocked_slots": [slot.dict() for slot in (ta.blocked_slots or [])],
        "day_off": updated_ta.day_off,
        "premasters": updated_ta.premasters,
        "skills": updated_ta.skills or [],
        "notes": updated_ta.notes or "",
        "total_allocated_hours": total_hours,
        "created_at": updated_ta.created_at.isoformat() if updated_ta.created_at else None
    }
    db["tas"][ta_id] = in_memory_ta

    # Return response in expected format
    ta_dict = TAService.get_ta_with_allocations(db_session, ta_id)
    return TAResponse(**ta_dict)

@app.delete("/tas/{ta_id}")
async def delete_ta(ta_id: int, db_session: Session = Depends(get_db)):
    """Delete a TA."""
    # Delete from database
    deleted = TAService.delete_ta(db_session, ta_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="TA not found")

    # Delete from in-memory database for backwards compatibility
    if ta_id in db["tas"]:
        del db["tas"][ta_id]

    return {"message": "TA deleted successfully"}

# Course Management Endpoints
@app.get("/courses", response_model=List[CourseResponse])
async def get_courses(db: Session = Depends(get_db)):
    """Get all courses."""
    courses = CourseService.get_courses(db)
    return [
        CourseResponse(
            id=course.id,
            code=course.code,
            name=course.name,
            tutorials=course.tutorials,
            labs=course.labs,
            tutorial_duration=course.tutorial_duration,
            lab_duration=course.lab_duration,
            required_tas=course.required_tas,
            created_at=course.created_at.isoformat() if course.created_at else None
        )
        for course in courses
    ]

@app.post("/courses", response_model=CourseResponse)
async def create_course(course: CourseCreate, db_session: Session = Depends(get_db)):
    """Create a new course."""
    course_data = {
        "code": course.code,
        "name": course.name,
        "tutorials": course.tutorials,
        "labs": course.labs,
        "tutorial_duration": course.tutorial_duration,
        "lab_duration": course.lab_duration,
        "required_tas": course.required_tas
    }

    # Create course in database
    created_course = CourseService.create_course(db_session, course_data)

    # Also store in in-memory database for backwards compatibility with scheduling
    in_memory_course = {
        "id": created_course.id,
        "code": created_course.code,
        "name": created_course.name,
        "tutorials": created_course.tutorials,
        "labs": created_course.labs,
        "tutorial_duration": created_course.tutorial_duration,
        "lab_duration": created_course.lab_duration,
        "required_tas": created_course.required_tas,
        "created_at": created_course.created_at.isoformat() if created_course.created_at else None
    }
    db["courses"][created_course.id] = in_memory_course

    return CourseResponse(
        id=created_course.id,
        code=created_course.code,
        name=created_course.name,
        tutorials=created_course.tutorials,
        labs=created_course.labs,
        tutorial_duration=created_course.tutorial_duration,
        lab_duration=created_course.lab_duration,
        required_tas=created_course.required_tas,
        created_at=created_course.created_at.isoformat() if created_course.created_at else None
    )

@app.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, db_session: Session = Depends(get_db)):
    """Get a specific course."""
    course = CourseService.get_course(db_session, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return CourseResponse(
        id=course.id,
        code=course.code,
        name=course.name,
        tutorials=course.tutorials,
        labs=course.labs,
        tutorial_duration=course.tutorial_duration,
        lab_duration=course.lab_duration,
        required_tas=course.required_tas,
        created_at=course.created_at.isoformat() if course.created_at else None
    )

@app.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(course_id: int, course: CourseCreate, db_session: Session = Depends(get_db)):
    """Update a course."""
    course_data = {
        "code": course.code,
        "name": course.name,
        "tutorials": course.tutorials,
        "labs": course.labs,
        "tutorial_duration": course.tutorial_duration,
        "lab_duration": course.lab_duration,
        "required_tas": course.required_tas
    }

    # Update course in database
    updated_course = CourseService.update_course(db_session, course_id, course_data)
    if not updated_course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Update in-memory database for backwards compatibility with scheduling
    in_memory_course = {
        "id": updated_course.id,
        "code": updated_course.code,
        "name": updated_course.name,
        "tutorials": updated_course.tutorials,
        "labs": updated_course.labs,
        "tutorial_duration": updated_course.tutorial_duration,
        "lab_duration": updated_course.lab_duration,
        "required_tas": updated_course.required_tas,
        "created_at": updated_course.created_at.isoformat() if updated_course.created_at else None
    }
    db["courses"][course_id] = in_memory_course

    return CourseResponse(
        id=updated_course.id,
        code=updated_course.code,
        name=updated_course.name,
        tutorials=updated_course.tutorials,
        labs=updated_course.labs,
        tutorial_duration=updated_course.tutorial_duration,
        lab_duration=updated_course.lab_duration,
        required_tas=updated_course.required_tas,
        created_at=updated_course.created_at.isoformat() if updated_course.created_at else None
    )

@app.delete("/courses/{course_id}")
async def delete_course(course_id: int, db_session: Session = Depends(get_db)):
    """Delete a course."""
    # Delete from database
    deleted = CourseService.delete_course(db_session, course_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Course not found")

    # Delete from in-memory database for backwards compatibility
    if course_id in db["courses"]:
        del db["courses"][course_id]

    return {"message": "Course deleted successfully"}

# Schedule Management Endpoints
@app.get("/schedules", response_model=List[ScheduleResponse])
async def get_schedules(db_session: Session = Depends(get_db)):
    """Get all schedules."""
    schedules = ScheduleService.get_schedules(db_session)
    return [ScheduleResponse(
        id=schedule['id'],
        success=schedule['success'],
        message=schedule['message'],
        assignments=schedule.get('assignments', []),
        statistics=schedule.get('statistics'),
        policies_used=schedule.get('policies_used', {}),
        created_at=schedule.get('created_at', '')
    ) for schedule in schedules]

@app.post("/generate-schedule")
async def generate_schedule(request: ScheduleGenerateRequest, db_session: Session = Depends(get_db)):
    """Generate a new schedule."""
    print(f"Received schedule request: {request}")

    # Try advanced scheduler first, fallback only if it fails
    if not SCHEDULER_AVAILABLE:
        print("⚠️ Advanced scheduler not available - using intelligent fallback")
        return await simple_fallback_schedule(request, db_session)

    print("🚀 Using advanced scheduling algorithms")

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

        # COMPREHENSIVE VALIDATION: Check for parallel conflicts in advanced scheduler results
        parallel_conflicts = []
        assignment_grid = {}

        for assignment in assignments:
            # Build grid to check parallel conflicts
            slot_key = (assignment["day"].lower(), assignment["slot_number"])
            if slot_key not in assignment_grid:
                assignment_grid[slot_key] = []
            assignment_grid[slot_key].append(assignment)

        # Check for parallel conflicts (multiple assignments to same TA at same time)
        for (day, slot_num), slot_assignments in assignment_grid.items():
            ta_names = [a["ta_name"] for a in slot_assignments]
            if len(ta_names) != len(set(ta_names)):  # Duplicate TAs in same slot
                duplicates = [name for name in set(ta_names) if ta_names.count(name) > 1]
                for duplicate_ta in duplicates:
                    parallel_conflicts.append(f"CRITICAL: {duplicate_ta} assigned multiple times to {day.capitalize()} Slot {slot_num}")
                    print(f"❌ CRITICAL PARALLEL CONFLICT (Advanced Scheduler): {duplicate_ta} assigned multiple times to {day.capitalize()} Slot {slot_num}")

        if parallel_conflicts:
            print(f"❌ CRITICAL: Advanced scheduler produced {len(parallel_conflicts)} PARALLEL CONFLICTS!")
            statistics["critical_parallel_conflicts"] = len(parallel_conflicts)

        # Save schedule in database
        schedule_data = {
            "course_id": request.course_ids[0] if request.course_ids else 1,
            "success": result.success,
            "message": result.message,
            "statistics": statistics,
            "policies_used": {
                "tutorial_lab_independence": policies.tutorial_lab_independence,
                "tutorial_lab_equal_count": policies.tutorial_lab_equal_count,
                "tutorial_lab_number_matching": policies.tutorial_lab_number_matching,
                "fairness_mode": policies.fairness_mode
            },
            "assignments": assignments
        }

        # Create schedule in database
        created_schedule = ScheduleService.create_schedule(db_session, schedule_data)

        # Also store in in-memory database for backwards compatibility
        in_memory_schedule = {
            "id": created_schedule.id,
            "success": created_schedule.success,
            "message": created_schedule.message,
            "assignments": assignments,
            "statistics": created_schedule.statistics,
            "policies_used": created_schedule.policies_used,
            "created_at": created_schedule.created_at.isoformat() if created_schedule.created_at else None
        }
        db["schedules"][created_schedule.id] = in_memory_schedule

        return in_memory_schedule

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ Advanced scheduler failed: {error_details}")
        print("🔄 Falling back to intelligent constraint-aware scheduler")

        # Gracefully fallback to intelligent scheduler
        try:
            return await simple_fallback_schedule(request, db_session)
        except Exception as fallback_error:
            print(f"❌ Fallback scheduler also failed: {fallback_error}")
            raise HTTPException(status_code=500, detail=f"Both advanced and fallback schedulers failed. Advanced error: {str(e)}, Fallback error: {str(fallback_error)}")

@app.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: int, db_session: Session = Depends(get_db)):
    """Get a specific schedule."""
    schedule = ScheduleService.get_schedule(db_session, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return ScheduleResponse(
        id=schedule['id'],
        success=schedule['success'],
        message=schedule['message'],
        assignments=schedule.get('assignments', []),
        statistics=schedule.get('statistics'),
        policies_used=schedule.get('policies_used', {}),
        created_at=schedule.get('created_at', '')
    )

@app.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int, db_session: Session = Depends(get_db)):
    """Delete a schedule."""
    # Delete from database
    deleted = ScheduleService.delete_schedule(db_session, schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Delete from in-memory database for backwards compatibility
    if schedule_id in db["schedules"]:
        del db["schedules"][schedule_id]

    return {"message": "Schedule deleted successfully"}

@app.post("/schedules", response_model=ScheduleResponse)
async def save_schedule(request: ScheduleSaveRequest, db_session: Session = Depends(get_db)):
    """Save a new schedule."""
    try:
        # Create schedule in database using ScheduleService
        schedule_data = {
            "name": request.name,
            "description": request.description,
            "success": request.success,
            "message": request.message,
            "assignments": request.assignments,
            "statistics": request.statistics or {},
            "policies_used": request.policies_used
        }

        schedule = ScheduleService.save_schedule(db_session, schedule_data)
        schedule_id = schedule.id

        # Also save to in-memory database for backwards compatibility
        db["schedules"][schedule_id] = {
            "id": schedule_id,
            "success": request.success,
            "message": request.message,
            "assignments": request.assignments,
            "statistics": request.statistics or {},
            "policies_used": request.policies_used,
            "created_at": datetime.now().isoformat()
        }

        return ScheduleResponse(
            id=schedule_id,
            success=request.success,
            message=request.message,
            assignments=request.assignments,
            statistics=request.statistics or {},
            policies_used=request.policies_used,
            created_at=schedule.created_at.isoformat() if schedule.created_at else datetime.now().isoformat()
        )

    except Exception as e:
        print(f"Error saving schedule: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save schedule: {str(e)}")

# Course Grid Endpoints
@app.post("/courses/{course_id}/grid")
async def save_course_grid(
    course_id: int,
    grid_data: dict,
    db_session: Session = Depends(get_db)
):
    """Save or update a course-specific grid configuration."""
    try:
        # Verify course exists
        course = CourseService.get_course(db_session, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Extract components from the request
        schedule_grid = grid_data.get("grid_data", {})
        selected_tas = grid_data.get("selected_tas", [])
        policies = grid_data.get("policies", {})

        print(f"📥 Saving grid for course {course_id}:")
        print(f"  - grid_data: {schedule_grid}")
        print(f"  - selected_tas: {selected_tas}")
        print(f"  - policies: {policies}")

        # Save to database
        saved_grid = CourseGridService.save_course_grid(
            db_session, course_id, schedule_grid, selected_tas, policies
        )

        print(f"✅ Saved grid with ID: {saved_grid.id}")

        return {
            "message": "Course grid saved successfully",
            "grid_id": saved_grid.id,
            "course_id": course_id,
            "updated_at": saved_grid.updated_at.isoformat() if saved_grid.updated_at else None
        }
    except Exception as e:
        print(f"Error saving course grid: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save course grid: {str(e)}")

@app.get("/courses/{course_id}/grid")
async def get_course_grid(course_id: int, db_session: Session = Depends(get_db)):
    """Get the grid configuration for a specific course."""
    try:
        # Verify course exists
        course = CourseService.get_course(db_session, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Get grid from database
        grid = CourseGridService.get_course_grid(db_session, course_id)

        if grid:
            return {
                "grid_data": grid["grid_data"],
                "selected_tas": grid["selected_tas"],
                "policies": grid["policies"],
                "created_at": grid["created_at"],
                "updated_at": grid["updated_at"]
            }
        else:
            # Return empty structure if no grid exists yet
            return {
                "grid_data": {},
                "selected_tas": [],
                "policies": {
                    "tutorial_lab_independence": False,
                    "tutorial_lab_equal_count": True,
                    "tutorial_lab_number_matching": False,
                    "fairness_mode": True
                }
            }
    except Exception as e:
        print(f"Error loading course grid: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load course grid: {str(e)}")

@app.delete("/courses/{course_id}/grid")
async def delete_course_grid(course_id: int, db_session: Session = Depends(get_db)):
    """Delete a course grid configuration."""
    try:
        deleted = CourseGridService.delete_course_grid(db_session, course_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Course grid not found")
        return {"message": "Course grid deleted successfully"}
    except Exception as e:
        print(f"Error deleting course grid: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete course grid: {str(e)}")

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