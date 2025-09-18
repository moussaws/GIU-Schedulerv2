// Type definitions for the GIU Staff Schedule Composer

export enum DayEnum {
  SATURDAY = 'saturday',
  SUNDAY = 'sunday',
  MONDAY = 'monday',
  TUESDAY = 'tuesday',
  WEDNESDAY = 'wednesday',
  THURSDAY = 'thursday'
}

export enum SlotTypeEnum {
  TUTORIAL = 'tutorial',
  LAB = 'lab'
}

export enum UserRole {
  ADMIN = 'admin',
  STAFF = 'staff'
}

export enum ScheduleStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  ARCHIVED = 'archived'
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface Course {
  id: number;
  code: string;
  name: string;
  description?: string;
  created_by: number;
  created_at: string;
  time_slots: TimeSlot[];
}

export interface TimeSlot {
  id: number;
  course_id: number;
  day: DayEnum;
  slot_number: number;
  slot_type: SlotTypeEnum;
  duration: number;
  created_at: string;
}

export interface TeachingAssistant {
  id: number;
  name: string;
  email: string;
  max_weekly_hours: number;
  is_active: boolean;
  created_at: string;
  availability: TAAvailability[];
}

export interface TAAvailability {
  id: number;
  ta_id: number;
  day: DayEnum;
  slot_number: number;
  is_available: boolean;
  preference_rank: number;
}

export interface SchedulingPolicies {
  tutorial_lab_independence: boolean;
  tutorial_lab_equal_count: boolean;
  tutorial_lab_number_matching: boolean;
  fairness_mode: boolean;
}

export interface Schedule {
  id: number;
  name: string;
  description?: string;
  policies: SchedulingPolicies;
  status: ScheduleStatus;
  success: boolean;
  message?: string;
  statistics?: Record<string, any>;
  created_by: number;
  created_at: string;
  updated_at?: string;
  assignments: ScheduleAssignment[];
}

export interface ScheduleAssignment {
  id: number;
  schedule_id: number;
  course_id: number;
  ta_id: number;
  time_slot_id: number;
  created_at: string;
  course: Course;
  ta: TeachingAssistant;
  time_slot: TimeSlot;
}

export interface TAWorkloadStats {
  ta_id: number;
  ta_name: string;
  current_hours: number;
  max_hours: number;
  utilization_rate: number;
  course_count: number;
}

export interface ScheduleStatistics {
  total_assignments: number;
  total_tas: number;
  total_courses: number;
  average_ta_workload: number;
  workload_variance: number;
  average_course_coverage: number;
  fully_covered_courses: number;
  conflicts_detected: number;
  policy_violations: number;
  success_rate: number;
  ta_workloads: TAWorkloadStats[];
}

export interface APIResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface ScheduleGenerationRequest {
  name: string;
  description?: string;
  policies: SchedulingPolicies;
  course_ids: number[];
  optimize: boolean;
}

export interface ScheduleExportRequest {
  format: 'grid' | 'list' | 'csv';
}

// Form types
export interface CourseFormData {
  code: string;
  name: string;
  description?: string;
}

export interface TAFormData {
  name: string;
  email: string;
  max_weekly_hours: number;
  is_active: boolean;
}

export interface TimeSlotFormData {
  day: DayEnum;
  slot_number: number;
  slot_type: SlotTypeEnum;
  duration: number;
}

export interface AvailabilityFormData {
  [key: string]: {
    is_available: boolean;
    preference_rank: number;
  };
}

// UI State types
export interface LoadingState {
  [key: string]: boolean;
}

export interface ErrorState {
  [key: string]: string | null;
}

export interface ModalState {
  isOpen: boolean;
  type?: string;
  data?: any;
}

// Grid types for schedule display
export interface ScheduleGridCell {
  day: DayEnum;
  slot_number: number;
  assignments: ScheduleAssignment[];
  conflicts?: boolean;
}

export interface ScheduleGridRow {
  slot_number: number;
  cells: ScheduleGridCell[];
}

export interface ConflictInfo {
  type: 'double_booking' | 'overcapacity' | 'policy_violation';
  ta_name?: string;
  slot?: string;
  courses?: string[];
  current_hours?: number;
  max_hours?: number;
  excess_hours?: number;
  message: string;
}