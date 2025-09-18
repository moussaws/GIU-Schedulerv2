from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, Float, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    STAFF = "staff"


class DayEnum(str, enum.Enum):
    SATURDAY = "saturday"
    SUNDAY = "sunday"
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"


class SlotTypeEnum(str, enum.Enum):
    TUTORIAL = "tutorial"
    LAB = "lab"


class ScheduleStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STAFF)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    created_courses = relationship("Course", back_populates="created_by_user")
    created_schedules = relationship("Schedule", back_populates="created_by_user")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    created_by_user = relationship("User", back_populates="created_courses")
    time_slots = relationship("TimeSlot", back_populates="course", cascade="all, delete-orphan")
    ta_assignments = relationship("CourseTAAssignment", back_populates="course", cascade="all, delete-orphan")
    schedule_assignments = relationship("ScheduleAssignment", back_populates="course")


class TeachingAssistant(Base):
    __tablename__ = "teaching_assistants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    max_weekly_hours = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    availability = relationship("TAAvailability", back_populates="ta", cascade="all, delete-orphan")
    course_assignments = relationship("CourseTAAssignment", back_populates="ta", cascade="all, delete-orphan")
    schedule_assignments = relationship("ScheduleAssignment", back_populates="ta")


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    day = Column(Enum(DayEnum), nullable=False)
    slot_number = Column(Integer, nullable=False)  # 1-5
    slot_type = Column(Enum(SlotTypeEnum), nullable=False)
    duration = Column(Integer, default=2)  # hours
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    course = relationship("Course", back_populates="time_slots")
    schedule_assignments = relationship("ScheduleAssignment", back_populates="time_slot")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('course_id', 'day', 'slot_number', 'slot_type', name='unique_slot'),
    )


class TAAvailability(Base):
    __tablename__ = "ta_availability"

    id = Column(Integer, primary_key=True, index=True)
    ta_id = Column(Integer, ForeignKey("teaching_assistants.id"), nullable=False)
    day = Column(Enum(DayEnum), nullable=False)
    slot_number = Column(Integer, nullable=False)  # 1-5
    is_available = Column(Boolean, default=True)
    preference_rank = Column(Integer, default=5)  # 1=highest, 5=lowest preference

    # Relationships
    ta = relationship("TeachingAssistant", back_populates="availability")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('ta_id', 'day', 'slot_number', name='unique_availability'),
    )


class CourseTAAssignment(Base):
    __tablename__ = "course_ta_assignments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    ta_id = Column(Integer, ForeignKey("teaching_assistants.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    course = relationship("Course", back_populates="ta_assignments")
    ta = relationship("TeachingAssistant", back_populates="course_assignments")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('course_id', 'ta_id', name='unique_course_ta'),
    )


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    policies_json = Column(Text)  # Store SchedulingPolicies as JSON
    status = Column(Enum(ScheduleStatus), default=ScheduleStatus.DRAFT)
    success = Column(Boolean, default=False)
    message = Column(Text)
    statistics_json = Column(Text)  # Store schedule statistics as JSON
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    created_by_user = relationship("User", back_populates="created_schedules")
    assignments = relationship("ScheduleAssignment", back_populates="schedule", cascade="all, delete-orphan")


class ScheduleAssignment(Base):
    __tablename__ = "schedule_assignments"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    ta_id = Column(Integer, ForeignKey("teaching_assistants.id"), nullable=False)
    time_slot_id = Column(Integer, ForeignKey("time_slots.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    schedule = relationship("Schedule", back_populates="assignments")
    course = relationship("Course", back_populates="schedule_assignments")
    ta = relationship("TeachingAssistant", back_populates="schedule_assignments")
    time_slot = relationship("TimeSlot", back_populates="schedule_assignments")

    # Unique constraint - one TA per time slot per schedule
    __table_args__ = (
        UniqueConstraint('schedule_id', 'ta_id', 'time_slot_id', name='unique_schedule_ta_slot'),
    )