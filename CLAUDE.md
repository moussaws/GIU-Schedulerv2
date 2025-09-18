# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the GIU Staff Schedule Composer - a complete scheduling system for Teaching Assistant assignments. The project consists of:

1. **Core Python scheduling algorithms** (root directory) - The main scheduling engine
2. **FastAPI backend** (`backend/`) - Web API and database layer
3. **React TypeScript frontend** (`frontend/`) - Modern web interface
4. **Docker deployment** - Production-ready containerization with PostgreSQL and Nginx

## Development Commands

### Testing the Core Algorithms
```bash
# Run comprehensive demonstration
python3 example.py

# Simple verification tests
python3 simple_test.py

# Policy-specific tests
python3 policy_test.py

# Debug specific scenarios
python3 debug_test.py

# Course duration testing
python3 test_course_durations.py

# Debug policy issues
python3 debug_policy_issue.py
```

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start development server
uvicorn main:app --reload

# Access API docs at http://localhost:8000/docs
```

### Frontend Development
```bash
cd frontend
npm install
npm start     # Runs on port 3000 with proxy to backend on port 8001
npm run build # Production build
npm test      # Run tests
```

### Docker Deployment
```bash
# Start full stack (backend, frontend, PostgreSQL, Nginx)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Backend runs on port 8000
# Frontend runs on port 3000
# Nginx proxy available on port 80/443
# PostgreSQL on port 5432
```

## Architecture

### Core Scheduling Engine (Root Directory)
- **GIUScheduler** (`scheduler.py`) - Main API interface
- **Models** (`models.py`) - Core data structures (TA, Course, TimeSlot, etc.)
- **GlobalScheduler** (`global_scheduler.py`) - Coordinates course scheduling
- **PolicyValidator** (`policy_validator.py`) - Enforces scheduling policies
- **ConflictResolver** (`conflict_resolver.py`) - Handles scheduling conflicts
- **WorkloadBalancer** (`workload_balancer.py`) - Balances TA workloads

### Backend API Structure (`backend/`)
- **FastAPI app** (`main.py`) - Application entry point
- **Database models** (`app/models/database.py`) - SQLAlchemy models
- **API endpoints** (`app/api/`) - REST API routes
- **Scheduler service** (`app/services/scheduler_service.py`) - Integration with core algorithms
- **Authentication** (`app/core/auth.py`) - JWT-based auth system

### Frontend Structure (`frontend/src/`)
- **TypeScript React app** with modern component architecture
- **Pages** - Main application screens (Dashboard, Courses, TAs, Schedules)
- **Components** - Reusable UI components with Tailwind CSS
  - **ScheduleCalendar** - Interactive drag-and-drop calendar view
  - **ScheduleManager** - Complete schedule management with editing
- **Services** (`services/api.ts`) - API integration layer
  - **swapValidation.ts** - Client-side rule validation for TA swapping
- **Types** (`types/index.ts`) - TypeScript definitions

## Key Concepts

### Scheduling Policies
Four main policy options that can be combined:
- **Tutorial-Lab Independence** (default OFF) - Allow arbitrary slot combinations
- **Tutorial-Lab Equal Count** (default OFF) - Equal tutorials/labs per TA
- **Tutorial-Lab Number Matching** (default OFF) - Pair Tutorial N with Lab N
- **Fairness Mode** (default OFF) - Balance workloads across TAs

### Time System
- **6-day week**: Saturday through Thursday
- **5 slots per day**: Numbered 1-5
- **2-hour duration**: All slots are fixed 2 hours
- **Slot types**: Tutorial or Lab

### Core Data Flow
1. Create Courses with required TimeSlots
2. Define TAs with availability and preferences
3. Assign TAs to Courses
4. Generate schedule using GIUScheduler with policies
5. Resolve conflicts and optimize workloads

## API Access Points

### Backend API (port 8000)
- **Health**: `/health` - System status
- **Auth**: `/auth/login`, `/auth/me` - Authentication
- **Courses**: `/courses` - Course management
- **TAs**: `/tas` - Teaching assistant management
- **Schedules**: `/schedules/generate` - Schedule generation
  - **Swap**: `/schedules/{id}/swap` - Assignment swapping
  - **Validate**: `/schedules/{id}/validate-swap` - Swap validation
  - **Conflicts**: `/schedules/{id}/conflicts` - Conflict detection
- **API Docs**: `/docs` - Swagger documentation

### Frontend (port 3000)
- **Dashboard**: Overview and quick actions
- **Courses**: Manage courses and time slots
- **Teaching Assistants**: Manage TAs and availability
- **Schedules**: Generate, view, and edit schedules with drag-and-drop calendar
- **Settings**: Policy configuration

## Database Configuration

### Development (SQLite)
- Automatic setup, no configuration needed
- Database file: `backend/scheduler.db`

### Production (PostgreSQL)
- Configured via Docker Compose
- Connection string in environment variables
- Migrations handled by Alembic

## Environment Setup

### Backend Environment (`.env`)
```bash
DATABASE_URL=sqlite:///./scheduler.db
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000
```

### Frontend Environment (`.env`)
```bash
REACT_APP_API_URL=http://localhost:8000
```

### Docker Environment Variables
- **PostgreSQL**: Database runs in container with credentials in docker-compose.yml
- **Backend**: Uses PostgreSQL connection in production Docker setup
- **Frontend**: Proxy configured to backend port 8001 in development

## Core Integration Points

### Frontend-Backend Integration
- **Proxy Configuration**: Frontend package.json has `"proxy": "http://localhost:8001"` for development
- **API Service**: Frontend uses `services/api.ts` for all backend communication
- **Real-time Updates**: React Query for caching and state management
- **Drag & Drop**: React Beautiful DND for schedule calendar interactions

### Backend-Core Algorithm Integration
- **Direct Import**: Backend imports core scheduling modules from root directory
- **Service Layer**: `scheduler_service.py` bridges FastAPI and core algorithms
- **Data Transformation**: Backend models map to core algorithm data structures
- **Policy Configuration**: Scheduling policies configured via API and passed to core engine

### Database Architecture
- **Development**: SQLite for simple setup (`scheduler.db`)
- **Production**: PostgreSQL with Docker Compose
- **Migrations**: Alembic handles database schema versioning
- **Models**: SQLAlchemy models in `backend/app/models/database.py`

## Important Implementation Notes

- The core scheduling algorithms are in the root directory and are imported by the backend
- All scheduling policies default to OFF as specified in the requirements
- The system supports the full Saturday-Thursday academic week (6 days)
- Workload balancing and conflict resolution are built into the scheduling engine
- Frontend provides real-time drag-and-drop schedule editing with validation
- Docker deployment includes full production stack with reverse proxy