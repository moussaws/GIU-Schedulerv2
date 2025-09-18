# 🎓 GIU Staff Schedule Composer - Web Application

A complete, production-ready web application for intelligent teaching assistant scheduling at GIU. Built with modern technologies and featuring a beautiful, intuitive user interface.

![GIU Scheduler](https://img.shields.io/badge/Status-Production%20Ready-success)
![Backend](https://img.shields.io/badge/Backend-FastAPI-blue)
![Frontend](https://img.shields.io/badge/Frontend-React%20TypeScript-blue)
![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-orange)

## ✨ Features

### 🎯 **Core Scheduling**
- **Smart Algorithm Integration**: Your original scheduling algorithms exposed via REST API
- **Saturday-Thursday Support**: Full 6-day academic week scheduling
- **Policy Enforcement**: All 4 policy combinations (Independence, Equal Count, Number Matching, Fairness)
- **Conflict Resolution**: Automatic detection and resolution of scheduling conflicts
- **Multi-format Export**: Grid, List, and CSV export options

### 🎨 **Beautiful UI/UX**
- **Modern Design**: Clean, professional interface built with Tailwind CSS
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile
- **Intuitive Navigation**: Easy-to-use sidebar navigation with clear sections
- **Real-time Feedback**: Toast notifications and loading states
- **Interactive Dashboard**: Statistics, quick actions, and system status

### 🔐 **Security & Authentication**
- **JWT Authentication**: Secure token-based authentication
- **Role-based Access**: Admin and Staff user roles
- **Protected Routes**: Secure API endpoints with proper authorization
- **Input Validation**: Comprehensive validation using Pydantic

### 📊 **Data Management**
- **Course Management**: Create courses with time slots and requirements
- **TA Management**: Manage teaching assistants with availability matrix
- **Schedule Management**: Generate, optimize, and manage multiple schedules
- **Statistics & Analytics**: Comprehensive scheduling statistics and insights

## 🏗️ **Architecture**

### Backend (FastAPI)
```
backend/
├── app/
│   ├── api/          # REST API endpoints
│   ├── models/       # Database models & schemas
│   ├── services/     # Business logic layer
│   ├── core/         # Authentication & security
│   └── db/           # Database configuration
├── main.py           # FastAPI application
└── requirements.txt  # Python dependencies
```

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── components/   # Reusable UI components
│   ├── pages/        # Application pages
│   ├── services/     # API service layer
│   ├── hooks/        # Custom React hooks
│   ├── types/        # TypeScript definitions
│   └── utils/        # Utility functions
├── public/          # Static assets
└── package.json     # Node dependencies
```

### Database Schema
- **Users**: Authentication and authorization
- **Courses**: Course information with time slots
- **Teaching Assistants**: TA profiles with availability
- **Schedules**: Generated schedules with assignments
- **Relationships**: Proper foreign key relationships

## 🚀 **Quick Start**

### Prerequisites
- Python 3.8+
- Node.js 16+
- Docker & Docker Compose (for deployment)

### Development Setup

1. **Start Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

2. **Start Frontend**
```bash
cd frontend
npm install
npm start
```

3. **Access Application**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Backend API: http://localhost:8000

### Docker Deployment
```bash
# Quick start with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🎛️ **API Endpoints**

### Authentication
- `POST /auth/login` - User authentication
- `GET /auth/me` - Get current user info
- `POST /auth/register` - Register new user

### Courses
- `GET /courses` - List all courses
- `POST /courses` - Create new course
- `POST /courses/{id}/slots` - Add time slots
- `POST /courses/{id}/assign-ta` - Assign TA to course

### Teaching Assistants
- `GET /tas` - List all TAs
- `POST /tas` - Create new TA
- `POST /tas/{id}/availability` - Set TA availability

### Schedules
- `POST /schedules/generate` - Generate new schedule
- `GET /schedules/{id}` - Get schedule details
- `POST /schedules/{id}/optimize` - Optimize existing schedule
- `POST /schedules/{id}/export` - Export schedule

## 🎨 **User Interface**

### Dashboard
- **System Overview**: Key metrics and statistics
- **Quick Actions**: Fast access to common tasks
- **Recent Schedules**: Latest scheduling activities
- **System Status**: Health monitoring

### Course Management
- **Course Creation**: Easy course setup with time slots
- **TA Assignment**: Drag-and-drop TA assignment
- **Requirements Setup**: Define course scheduling needs

### TA Management
- **Profile Management**: Complete TA information
- **Availability Matrix**: Visual availability setting
- **Workload Tracking**: Monitor TA assignments and hours

### Schedule Generation
- **Policy Configuration**: Visual policy toggles
- **Generation Wizard**: Step-by-step schedule creation
- **Conflict Resolution**: Interactive conflict management
- **Statistics Dashboard**: Comprehensive scheduling metrics

### Schedule Viewer
- **Weekly Grid**: Interactive schedule visualization
- **Export Options**: Multiple format downloads
- **Conflict Highlighting**: Visual conflict indicators

## 🔧 **Configuration**

### Environment Variables

**Backend (.env)**
```bash
DATABASE_URL=sqlite:///./scheduler.db
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000
```

**Frontend (.env)**
```bash
REACT_APP_API_URL=http://localhost:8000
```

### Policy Defaults
- Tutorial-Lab Independence: `OFF` (as specified)
- Tutorial-Lab Equal Count: `OFF`
- Tutorial-Lab Number Matching: `OFF`
- Fairness Mode: `OFF`

## 📊 **Database Support**

### Development
- **SQLite**: Zero-configuration, file-based database
- **Automatic Setup**: Tables created automatically
- **Perfect for Testing**: No external dependencies

### Production
- **PostgreSQL**: Robust, scalable database
- **Connection Pooling**: Optimized performance
- **Migration Support**: Schema versioning with Alembic

## 🐳 **Deployment Options**

### Docker Compose (Recommended)
- **Complete Stack**: Backend + Frontend + Database + Nginx
- **Load Balancing**: Multiple backend workers
- **SSL Support**: HTTPS configuration ready
- **Health Checks**: Automatic service monitoring

### Manual Deployment
- **Flexible Setup**: Individual service deployment
- **Custom Configuration**: Tailored to your infrastructure
- **Scalable**: Easy horizontal scaling

## 🔐 **Security Features**

- **JWT Authentication**: Stateless, secure token system
- **Password Hashing**: bcrypt with salt
- **Input Validation**: Comprehensive request validation
- **CORS Configuration**: Proper cross-origin setup
- **SQL Injection Protection**: SQLAlchemy ORM
- **XSS Protection**: React built-in protections

## 📈 **Performance Features**

- **Async Backend**: FastAPI with async/await
- **Connection Pooling**: Database optimization
- **Static Asset Caching**: Nginx optimization
- **Gzip Compression**: Reduced bandwidth usage
- **React Optimization**: Code splitting and lazy loading

## 🎯 **Demo Credentials**

For testing and demonstration:
- **Admin**: `admin` / `admin123`
- **Staff**: `staff` / `staff123`

## 📚 **Documentation**

- **API Documentation**: Auto-generated with FastAPI (Swagger UI)
- **Type Safety**: Full TypeScript support
- **Code Comments**: Comprehensive inline documentation
- **Deployment Guide**: Complete setup instructions

## 🌟 **What Makes This Special**

### 1. **Algorithm Integration**
- Your original scheduling algorithms are perfectly integrated
- All policies work exactly as specified
- Saturday-Thursday support implemented
- Performance optimized for web use

### 2. **Production Ready**
- Docker containerization
- Database migrations
- Security best practices
- Monitoring and health checks
- Proper error handling

### 3. **User Experience**
- Intuitive, modern interface
- Responsive design
- Real-time feedback
- Accessibility considerations
- Professional appearance

### 4. **Scalability**
- Microservices architecture
- Database-agnostic design
- Horizontal scaling support
- Performance monitoring

## 📞 **Support & Maintenance**

### Health Monitoring
- Backend: `/health` endpoint
- Database: Connection monitoring
- Frontend: Nginx health checks

### Logging
```bash
# View logs
docker-compose logs backend
docker-compose logs frontend

# Follow in real-time
docker-compose logs -f
```

### Updates
```bash
# Update application
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

---

## 🎉 **Result Summary**

You now have a **complete, production-ready web application** that includes:

✅ **Backend API** with your scheduling algorithms integrated
✅ **Beautiful React frontend** with modern UI/UX
✅ **Database layer** with proper relationships
✅ **Authentication system** with role-based access
✅ **Docker deployment** configuration
✅ **Complete documentation** and setup guides

The system is ready to deploy and use immediately. It maintains all your original algorithm functionality while providing a professional web interface that any university can use for TA scheduling.

**Status**: 🟢 **Production Ready**