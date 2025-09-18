import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  User, Course, TeachingAssistant, Schedule, ScheduleStatistics,
  APIResponse, Token, LoginRequest, CourseFormData, TAFormData,
  TimeSlotFormData, ScheduleGenerationRequest, ScheduleExportRequest,
  TAAvailability, SchedulingPolicies
} from '../types';

class APIService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Simple interceptor for demo - no auth needed
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<Token> {
    const response = await this.api.post<Token>('/auth/login', credentials);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get<User>('/auth/me');
    return response.data;
  }

  async register(userData: any): Promise<APIResponse> {
    const response = await this.api.post<APIResponse>('/auth/register', userData);
    return response.data;
  }

  // Courses
  async getCourses(): Promise<Course[]> {
    const response = await this.api.get<Course[]>('/courses');
    return response.data;
  }

  async getCourse(id: number): Promise<Course> {
    const response = await this.api.get<Course>(`/courses/${id}`);
    return response.data;
  }

  async createCourse(courseData: CourseFormData): Promise<APIResponse> {
    const response = await this.api.post<APIResponse>('/courses', courseData);
    return response.data;
  }

  async updateCourse(id: number, courseData: Partial<CourseFormData>): Promise<APIResponse> {
    const response = await this.api.put<APIResponse>(`/courses/${id}`, courseData);
    return response.data;
  }

  async deleteCourse(id: number): Promise<APIResponse> {
    const response = await this.api.delete<APIResponse>(`/courses/${id}`);
    return response.data;
  }

  async addTimeSlot(courseId: number, slotData: TimeSlotFormData): Promise<APIResponse> {
    const response = await this.api.post<APIResponse>(
      `/courses/${courseId}/slots`,
      { ...slotData, course_id: courseId }
    );
    return response.data;
  }

  async deleteTimeSlot(courseId: number, slotId: number): Promise<APIResponse> {
    const response = await this.api.delete<APIResponse>(`/courses/${courseId}/slots/${slotId}`);
    return response.data;
  }

  async assignTAToCourse(courseId: number, taId: number): Promise<APIResponse> {
    const response = await this.api.post<APIResponse>(
      `/courses/${courseId}/assign-ta`,
      { course_id: courseId, ta_id: taId }
    );
    return response.data;
  }

  async unassignTAFromCourse(courseId: number, taId: number): Promise<APIResponse> {
    const response = await this.api.delete<APIResponse>(`/courses/${courseId}/unassign-ta/${taId}`);
    return response.data;
  }

  // Teaching Assistants
  async getTAs(): Promise<TeachingAssistant[]> {
    const response = await this.api.get<TeachingAssistant[]>('/tas');
    return response.data;
  }

  async getTA(id: number): Promise<TeachingAssistant> {
    const response = await this.api.get<TeachingAssistant>(`/tas/${id}`);
    return response.data;
  }

  async createTA(taData: TAFormData): Promise<APIResponse> {
    const response = await this.api.post<APIResponse>('/tas', taData);
    return response.data;
  }

  async updateTA(id: number, taData: Partial<TAFormData>): Promise<APIResponse> {
    const response = await this.api.put<APIResponse>(`/tas/${id}`, taData);
    return response.data;
  }

  async deleteTA(id: number): Promise<APIResponse> {
    const response = await this.api.delete<APIResponse>(`/tas/${id}`);
    return response.data;
  }

  async getTAAvailability(taId: number): Promise<TAAvailability[]> {
    const response = await this.api.get<TAAvailability[]>(`/tas/${taId}/availability`);
    return response.data;
  }

  async setTAAvailability(taId: number, availability: any[]): Promise<APIResponse> {
    const response = await this.api.post<APIResponse>(`/tas/${taId}/availability`, availability);
    return response.data;
  }

  // Schedules
  async getSchedules(): Promise<Schedule[]> {
    const response = await this.api.get<Schedule[]>('/schedules');
    return response.data;
  }

  async getSchedule(id: number): Promise<Schedule> {
    const response = await this.api.get<Schedule>(`/schedules/${id}`);
    return response.data;
  }

  async generateSchedule(request: ScheduleGenerationRequest): Promise<APIResponse> {
    const response = await this.api.post<APIResponse>('/schedules/generate', request);
    return response.data;
  }

  async optimizeSchedule(scheduleId: number): Promise<APIResponse> {
    const response = await this.api.post<APIResponse>(`/schedules/${scheduleId}/optimize`);
    return response.data;
  }

  async getScheduleStatistics(scheduleId: number): Promise<ScheduleStatistics> {
    const response = await this.api.get<ScheduleStatistics>(`/schedules/${scheduleId}/statistics`);
    return response.data;
  }

  async exportSchedule(scheduleId: number, format: 'grid' | 'list' | 'csv'): Promise<string> {
    const response = await this.api.post(
      `/schedules/${scheduleId}/export`,
      { format },
      { responseType: 'text' }
    );
    return response.data;
  }

  async updateSchedule(id: number, scheduleData: any): Promise<APIResponse> {
    const response = await this.api.put<APIResponse>(`/schedules/${id}`, scheduleData);
    return response.data;
  }

  async deleteSchedule(id: number): Promise<APIResponse> {
    const response = await this.api.delete<APIResponse>(`/schedules/${id}`);
    return response.data;
  }

  async getScheduleConflicts(scheduleId: number): Promise<any> {
    const response = await this.api.get(`/schedules/${scheduleId}/conflicts`);
    return response.data;
  }

  async swapAssignment(
    scheduleId: number,
    sourceAssignmentId: number,
    targetSlot: { day: string; slot_number: number }
  ): Promise<APIResponse> {
    const response = await this.api.post<APIResponse>(
      `/schedules/${scheduleId}/swap`,
      {
        source_assignment_id: sourceAssignmentId,
        target_slot: targetSlot
      }
    );
    return response.data;
  }

  async validateSwap(
    scheduleId: number,
    sourceAssignmentId: number,
    targetSlot: { day: string; slot_number: number }
  ): Promise<any> {
    const response = await this.api.post(
      `/schedules/${scheduleId}/validate-swap`,
      {
        source_assignment_id: sourceAssignmentId,
        target_slot: targetSlot
      }
    );
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; message: string }> {
    const response = await this.api.get('/health');
    return response.data;
  }
}

export const apiService = new APIService();
export default apiService;