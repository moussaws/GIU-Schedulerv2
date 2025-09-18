"""
Simple FastAPI server for GIU Staff Schedule Composer
Compatible with Python 3.13
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import sys
import os

# Add parent directory to path to import our scheduling algorithms
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

# Import our scheduling system
try:
    from models import (
        Course as AlgoCourse, TA as AlgoTA, TimeSlot as AlgoTimeSlot,
        Day, SlotType, SchedulingPolicies as AlgoSchedulingPolicies
    )
    from scheduler import GIUScheduler
    SCHEDULER_AVAILABLE = True
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
                    🧮 <strong>Scheduling Algorithms:</strong> """ + ("Available" if SCHEDULER_AVAILABLE else "Not Available") + """
                </div>

                <h2>🔗 Available Endpoints</h2>
                <div class="endpoint">
                    <span class="method">GET</span><a href="/health">/health</a> - Health check
                </div>
                <div class="endpoint">
                    <span class="method">GET</span><a href="/docs">/docs</a> - API Documentation (Swagger UI)
                </div>
                <div class="endpoint">
                    <span class="method">GET</span><a href="/demo-schedule">/demo-schedule</a> - Demo scheduling
                </div>

                <h2>🎯 Features Ready</h2>
                <ul>
                    <li>✅ FastAPI server running</li>
                    <li>✅ CORS configured for frontend</li>
                    <li>✅ Health monitoring</li>
                    <li>""" + ("✅" if SCHEDULER_AVAILABLE else "❌") + """ Original scheduling algorithms</li>
                    <li>✅ Saturday-Thursday week support</li>
                    <li>✅ Policy enforcement</li>
                </ul>

                <p><strong>Next Steps:</strong></p>
                <ol>
                    <li>Visit <a href="/docs">/docs</a> for interactive API testing</li>
                    <li>Try <a href="/demo-schedule">/demo-schedule</a> to test scheduling</li>
                    <li>Start the React frontend on port 3000</li>
                </ol>
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
        "scheduler_available": SCHEDULER_AVAILABLE
    }

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
                "duration": assignment.slot.duration
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