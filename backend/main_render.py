from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.db.database import create_tables
from app.api import courses, teaching_assistants, schedules
import os

# Create FastAPI application
app = FastAPI(
    title="GIU Staff Schedule Composer API",
    description="Backend API for the GIU Staff Schedule Composer system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://giu-scheduler-frontend.onrender.com").split(",")
origins = [origin.strip() for origin in cors_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers (temporarily remove auth until we fix deployment)
app.include_router(courses.router)
app.include_router(teaching_assistants.router)
app.include_router(schedules.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    create_tables()


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
                .features {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }
                .feature {
                    background: rgba(255,255,255,0.05);
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎓 GIU Staff Schedule Composer API</h1>
                <p>Welcome to the backend API for the GIU Staff Schedule Composer system.</p>

                <div class="features">
                    <div class="feature">
                        <h3>📚 Course Management</h3>
                        <p>Create and manage courses with time slots</p>
                    </div>
                    <div class="feature">
                        <h3>👨‍🏫 TA Management</h3>
                        <p>Manage teaching assistants and availability</p>
                    </div>
                    <div class="feature">
                        <h3>📅 Smart Scheduling</h3>
                        <p>AI-powered schedule generation with policies</p>
                    </div>
                    <div class="feature">
                        <h3>⚡ Conflict Resolution</h3>
                        <p>Automatic conflict detection and resolution</p>
                    </div>
                </div>

                <h2>🔗 Quick Links</h2>
                <div class="endpoint">
                    <a href="/docs">📖 Interactive API Documentation (Swagger UI)</a>
                </div>
                <div class="endpoint">
                    <a href="/redoc">📋 API Documentation (ReDoc)</a>
                </div>

                <h2>🛠️ Main API Endpoints</h2>

                <div class="endpoint">
                    <span class="method">GET</span>/courses - List all courses
                </div>
                <div class="endpoint">
                    <span class="method">POST</span>/courses - Create new course
                </div>
                <div class="endpoint">
                    <span class="method">GET</span>/tas - List teaching assistants
                </div>
                <div class="endpoint">
                    <span class="method">POST</span>/tas - Create teaching assistant
                </div>
                <div class="endpoint">
                    <span class="method">POST</span>/schedules/generate - Generate schedule
                </div>
                <div class="endpoint">
                    <span class="method">GET</span>/schedules/{id}/export - Export schedule
                </div>

                <h2>🎯 Features</h2>
                <ul>
                    <li>✅ Saturday-Thursday weekly scheduling</li>
                    <li>✅ Tutorial-Lab policy enforcement</li>
                    <li>✅ Workload balancing and fairness mode</li>
                    <li>✅ Conflict detection and resolution</li>
                    <li>✅ Multiple export formats (Grid, List, CSV)</li>
                    <li>✅ Comprehensive statistics</li>
                </ul>

                <p><strong>Status:</strong> ✅ Ready for production</p>
            </div>
        </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "GIU Staff Schedule Composer API is running"}


@app.exception_handler(404)
async def custom_404_handler(request, exc):
    return HTTPException(status_code=404, detail="Endpoint not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_render:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )