# GIU Staff Schedule Composer - Web App Architecture

## 🏗️ System Architecture

### Technology Stack
- **Backend**: FastAPI (Python)
  - Fast, modern framework with automatic API documentation
  - Async support for better performance
  - Built-in data validation with Pydantic

- **Database**: SQLite (development) → PostgreSQL (production)
  - SQLite: Easy setup, no configuration needed
  - PostgreSQL: Production-ready, supports concurrent users

- **Frontend**: React + TypeScript
  - Modern, component-based UI
  - Strong typing for better maintainability
  - Excellent ecosystem and tooling

- **Styling**: Tailwind CSS
  - Utility-first CSS framework
  - Responsive design out of the box
  - Fast development, consistent styling

### Database Schema

#### Core Tables
1. **users**
   - id, username, email, password_hash, role, created_at

2. **courses**
   - id, code, name, description, created_by, created_at

3. **teaching_assistants**
   - id, name, email, max_weekly_hours, created_at

4. **time_slots**
   - id, course_id, day, slot_number, slot_type, duration

5. **ta_availability**
   - id, ta_id, day, slot_number, is_available, preference_rank

6. **course_ta_assignments**
   - id, course_id, ta_id, assigned_at

7. **schedules**
   - id, name, policies_json, status, created_by, created_at

8. **schedule_assignments**
   - id, schedule_id, course_id, ta_id, time_slot_id

### API Endpoints Structure

#### Authentication
- POST /auth/login
- POST /auth/logout
- GET /auth/me

#### Courses Management
- GET /courses - List all courses
- POST /courses - Create course
- GET /courses/{id} - Get course details
- PUT /courses/{id} - Update course
- DELETE /courses/{id} - Delete course
- POST /courses/{id}/slots - Add time slots
- POST /courses/{id}/assign-ta - Assign TA to course

#### TAs Management
- GET /tas - List all TAs
- POST /tas - Create TA
- GET /tas/{id} - Get TA details
- PUT /tas/{id} - Update TA
- DELETE /tas/{id} - Delete TA
- POST /tas/{id}/availability - Set availability

#### Scheduling
- GET /schedules - List all schedules
- POST /schedules/generate - Generate new schedule
- GET /schedules/{id} - Get schedule details
- POST /schedules/{id}/optimize - Optimize existing schedule
- POST /schedules/{id}/resolve-conflicts - Resolve conflicts
- GET /schedules/{id}/export - Export schedule

### Frontend Architecture

#### Page Structure
1. **Dashboard** - Overview of courses, TAs, recent schedules
2. **Courses** - Manage courses and time slots
3. **Teaching Assistants** - Manage TAs and their availability
4. **Scheduling** - Generate and manage schedules
5. **Settings** - Policy configuration, user management

#### Component Hierarchy
```
App
├── Layout
│   ├── Header
│   ├── Sidebar
│   └── Footer
├── Pages
│   ├── Dashboard
│   ├── Courses
│   │   ├── CourseList
│   │   ├── CourseForm
│   │   └── TimeSlotManager
│   ├── TeachingAssistants
│   │   ├── TAList
│   │   ├── TAForm
│   │   └── AvailabilityMatrix
│   ├── Scheduling
│   │   ├── ScheduleList
│   │   ├── ScheduleGenerator
│   │   ├── ScheduleViewer
│   │   └── PolicyConfig
│   └── Settings
└── Components
    ├── UI (buttons, forms, modals)
    ├── Charts
    └── Schedule Grid
```

## 🎨 UI/UX Design Principles

### Design Goals
- **Simplicity**: Clean, uncluttered interface
- **Efficiency**: Quick access to common tasks
- **Clarity**: Clear visual hierarchy and information architecture
- **Responsiveness**: Works well on desktop and tablet

### Color Scheme
- **Primary**: Blue (#3B82F6) - Professional, trustworthy
- **Secondary**: Green (#10B981) - Success, positive actions
- **Accent**: Orange (#F59E0B) - Warnings, important actions
- **Neutral**: Gray scale for text and backgrounds
- **Error**: Red (#EF4444) - Errors, conflicts

### Key UI Components
1. **Schedule Grid**: Interactive weekly calendar view
2. **Drag & Drop**: Intuitive TA assignment
3. **Status Indicators**: Visual feedback for conflicts/success
4. **Quick Actions**: Common tasks accessible with 1-2 clicks
5. **Progressive Disclosure**: Show details on demand

### User Workflows
1. **Setup Flow**: Courses → TAs → Availability → Generate Schedule
2. **Quick Schedule**: Use existing data, generate with one click
3. **Conflict Resolution**: Visual conflict highlighting with suggested fixes
4. **Export/Share**: Multiple format options, sharing links

## 🚀 Development Phases

### Phase 1: Backend API (Week 1)
- Database setup and models
- Authentication system
- Core CRUD APIs
- Integration with scheduling algorithms

### Phase 2: Frontend Core (Week 2)
- React app setup
- Basic layout and navigation
- Course and TA management pages
- API integration

### Phase 3: Scheduling Interface (Week 3)
- Schedule generation interface
- Schedule visualization
- Policy configuration
- Conflict resolution UI

### Phase 4: Polish & Deploy (Week 4)
- UI/UX refinements
- Testing and bug fixes
- Documentation
- Deployment setup

## 🔧 Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Quick Start
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend setup
cd frontend
npm install
npm start
```

### Environment Variables
```bash
# Backend (.env)
DATABASE_URL=sqlite:///./scheduler.db
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000

# Frontend (.env)
REACT_APP_API_URL=http://localhost:8000
```

This architecture provides a solid foundation for a scalable, maintainable web application that can grow with your needs.