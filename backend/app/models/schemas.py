from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DayEnum(str, Enum):
    SATURDAY = "saturday"
    SUNDAY = "sunday"
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"


class SlotTypeEnum(str, Enum):
    TUTORIAL = "tutorial"
    LAB = "lab"


class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"


class ScheduleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


# Base schemas
class TimeSlotBase(BaseModel):
    day: DayEnum
    slot_number: int
    slot_type: SlotTypeEnum
    duration: int = 2

    @field_validator('slot_number')
    @classmethod
    def validate_slot_number(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Slot number must be between 1 and 5')
        return v


class TimeSlotCreate(TimeSlotBase):
    course_id: int


class TimeSlot(TimeSlotBase):
    id: int
    course_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Course schemas
class CourseBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class Course(CourseBase):
    id: int
    created_by: int
    created_at: datetime
    time_slots: List[TimeSlot] = []

    class Config:
        from_attributes = True


# TA schemas
class TAAvailabilityBase(BaseModel):
    day: DayEnum
    slot_number: int
    is_available: bool = True
    preference_rank: int = 5

    @field_validator('slot_number')
    @classmethod
    def validate_slot_number(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Slot number must be between 1 and 5')
        return v

    @field_validator('preference_rank')
    @classmethod
    def validate_preference_rank(cls, v):
        if v < 1 or v > 10:
            raise ValueError('Preference rank must be between 1 and 10')
        return v


class TAAvailabilityCreate(TAAvailabilityBase):
    ta_id: int


class TAAvailability(TAAvailabilityBase):
    id: int
    ta_id: int

    class Config:
        from_attributes = True


class TeachingAssistantBase(BaseModel):
    name: str
    email: EmailStr
    max_weekly_hours: int = 10
    is_active: bool = True


class TeachingAssistantCreate(TeachingAssistantBase):
    pass


class TeachingAssistantUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    max_weekly_hours: Optional[int] = None
    is_active: Optional[bool] = None


class TeachingAssistant(TeachingAssistantBase):
    id: int
    created_at: datetime
    availability: List[TAAvailability] = []

    class Config:
        from_attributes = True


# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.STAFF
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserInDB(User):
    password_hash: str


# Schedule schemas
class SchedulingPolicies(BaseModel):
    tutorial_lab_independence: bool = False
    tutorial_lab_equal_count: bool = False
    tutorial_lab_number_matching: bool = False
    fairness_mode: bool = False


class ScheduleAssignmentBase(BaseModel):
    course_id: int
    ta_id: int
    time_slot_id: int


class ScheduleAssignmentCreate(ScheduleAssignmentBase):
    schedule_id: int


class ScheduleAssignment(ScheduleAssignmentBase):
    id: int
    schedule_id: int
    created_at: datetime
    course: Course
    ta: TeachingAssistant
    time_slot: TimeSlot

    class Config:
        from_attributes = True


class ScheduleBase(BaseModel):
    name: str
    description: Optional[str] = None
    policies: SchedulingPolicies
    status: ScheduleStatus = ScheduleStatus.DRAFT


class ScheduleCreate(ScheduleBase):
    course_ids: List[int]  # Courses to include in schedule generation


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ScheduleStatus] = None


class Schedule(ScheduleBase):
    id: int
    success: bool
    message: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    assignments: List[ScheduleAssignment] = []

    class Config:
        from_attributes = True


# Course-TA Assignment schemas
class CourseTAAssignmentCreate(BaseModel):
    course_id: int
    ta_id: int


class CourseTAAssignment(BaseModel):
    id: int
    course_id: int
    ta_id: int
    assigned_at: datetime
    course: Course
    ta: TeachingAssistant

    class Config:
        from_attributes = True


# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# API Response schemas
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class ScheduleGenerationRequest(BaseModel):
    name: str
    description: Optional[str] = None
    policies: SchedulingPolicies
    course_ids: List[int]
    optimize: bool = True


class ScheduleExportRequest(BaseModel):
    format: str = "grid"  # grid, list, csv

    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        if v not in ['grid', 'list', 'csv']:
            raise ValueError('Format must be one of: grid, list, csv')
        return v


# Statistics schemas
class TAWorkloadStats(BaseModel):
    ta_id: int
    ta_name: str
    current_hours: int
    max_hours: int
    utilization_rate: float
    course_count: int


class ScheduleStatistics(BaseModel):
    total_assignments: int
    total_tas: int
    total_courses: int
    average_ta_workload: float
    workload_variance: float
    average_course_coverage: float
    fully_covered_courses: int
    conflicts_detected: int
    policy_violations: int
    success_rate: float
    ta_workloads: List[TAWorkloadStats]