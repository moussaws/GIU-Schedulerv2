from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - supports both local development and production deployment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/giu_scheduler")

# For development, allow SQLite fallback
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    tutorials = Column(Integer, default=0)
    labs = Column(Integer, default=0)
    tutorial_duration = Column(Integer, default=2)
    lab_duration = Column(Integer, default=2)
    required_tas = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    ta_allocations = relationship("TAAllocation", back_populates="course")
    schedules = relationship("Schedule", back_populates="course")

class TA(Base):
    __tablename__ = "tas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(200), unique=True, index=True)
    blocked_slots = Column(JSON, default=list)  # [{"day": "monday", "slot_number": 1, "reason": "obligation"}]
    day_off = Column(String(20), nullable=True)  # Day of week
    premasters = Column(Boolean, default=False)
    skills = Column(JSON, default=list)  # ["python", "java", "web"]
    notes = Column(Text, default="")
    total_allocated_hours = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    course_allocations = relationship("TAAllocation", back_populates="ta")
    assignments = relationship("Assignment", back_populates="ta")

class TAAllocation(Base):
    __tablename__ = "ta_allocations"

    id = Column(Integer, primary_key=True, index=True)
    ta_id = Column(Integer, ForeignKey("tas.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    allocated_hours = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    ta = relationship("TA", back_populates="course_allocations")
    course = relationship("Course", back_populates="ta_allocations")

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    success = Column(Boolean, default=False)
    message = Column(Text, default="")
    statistics = Column(JSON, default=dict)  # {"success_rate": 1.0, "workload_distribution": {}}
    policies_used = Column(JSON, default=dict)  # Policy settings used
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    course = relationship("Course", back_populates="schedules")
    assignments = relationship("Assignment", back_populates="schedule")

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    ta_id = Column(Integer, ForeignKey("tas.id"), nullable=False)
    day = Column(String(20), nullable=False)  # "monday", "tuesday", etc.
    slot_number = Column(Integer, nullable=False)  # 1, 2, 3, 4, 5
    slot_type = Column(String(20), nullable=False)  # "tutorial", "lab"
    tutorial_number = Column(Integer, nullable=True)  # T1, T2, etc.
    lab_number = Column(Integer, nullable=True)  # L1, L2, etc.
    duration = Column(Integer, default=2)  # Hours
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    schedule = relationship("Schedule", back_populates="assignments")
    ta = relationship("TA", back_populates="assignments")

class CourseGrid(Base):
    """Store course-specific schedule grids and configurations"""
    __tablename__ = "course_grids"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, unique=True)
    grid_data = Column(JSON, nullable=False)  # The schedule grid structure
    selected_tas = Column(JSON, default=list)  # List of TA IDs selected for this course
    policies = Column(JSON, default=dict)  # Policy settings for this course
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    course = relationship("Course")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database tables created successfully!")