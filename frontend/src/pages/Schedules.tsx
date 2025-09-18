import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CalendarDaysIcon,
  PlusIcon,
  Cog6ToothIcon,
  EyeIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import {
  Schedule,
  SchedulingPolicies,
  Course,
  ScheduleGenerationRequest
} from '../types';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';

const SchedulesPage: React.FC = () => {
  const navigate = useNavigate();
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  // Generation form state
  const [generationForm, setGenerationForm] = useState({
    name: '',
    description: '',
    course_ids: [] as number[],
    policies: {
      tutorial_lab_independence: false,
      tutorial_lab_equal_count: false,
      tutorial_lab_number_matching: false,
      fairness_mode: false
    } as SchedulingPolicies,
    optimize: true
  });

  // Load schedules and courses
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [schedulesData, coursesData] = await Promise.all([
          apiService.getSchedules(),
          apiService.getCourses()
        ]);
        setSchedules(schedulesData);
        setCourses(coursesData);
      } catch (error) {
        console.error('Error loading data:', error);
        toast.error('Failed to load schedules');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Handle schedule generation
  const handleGenerateSchedule = async () => {
    if (!generationForm.name.trim()) {
      toast.error('Schedule name is required');
      return;
    }

    if (generationForm.course_ids.length === 0) {
      toast.error('Please select at least one course');
      return;
    }

    try {
      setIsGenerating(true);
      const request: ScheduleGenerationRequest = {
        name: generationForm.name.trim(),
        description: generationForm.description.trim(),
        policies: generationForm.policies,
        course_ids: generationForm.course_ids,
        optimize: generationForm.optimize
      };

      const result = await apiService.generateSchedule(request);

      if (result.success) {
        // Check if we actually have assignments
        const scheduleId = result.data?.schedule_id;
        if (scheduleId) {
          // Get the new schedule to check assignments
          try {
            const newSchedule = await apiService.getSchedule(scheduleId);
            if (newSchedule.assignments && newSchedule.assignments.length > 0) {
              toast.success('Schedule generated successfully!');
            } else {
              toast.error('Schedule generated with some issues. Check the results below.');
            }
          } catch (error) {
            toast.success('Schedule generated successfully!');
          }
        } else {
          toast.success('Schedule generated successfully!');
        }

        setShowGenerateModal(false);

        // Reset form
        setGenerationForm({
          name: '',
          description: '',
          course_ids: [],
          policies: {
            tutorial_lab_independence: false,
            tutorial_lab_equal_count: false,
            tutorial_lab_number_matching: false,
            fairness_mode: false
          },
          optimize: true
        });

        // Refresh schedules list
        const updatedSchedules = await apiService.getSchedules();
        setSchedules(updatedSchedules);

        // Navigate to the new schedule
        if (result.data?.schedule_id) {
          navigate(`/schedules/${result.data.schedule_id}`);
        }
      } else {
        // Show specific error message with details
        const errorMessage = result.message || 'Failed to generate schedule';
        if (result.data?.unassigned_slots > 0 || result.data?.policy_violations > 0) {
          toast.error(`${errorMessage}. Unassigned slots: ${result.data.unassigned_slots || 0}, Policy violations: ${result.data.policy_violations || 0}`);
        } else {
          toast.error(errorMessage);
        }
      }
    } catch (error: any) {
      console.error('Error generating schedule:', error);
      toast.error(error.response?.data?.detail || 'Failed to generate schedule');
    } finally {
      setIsGenerating(false);
    }
  };

  // Handle schedule deletion
  const handleDeleteSchedule = async (scheduleId: number) => {
    if (!confirm('Are you sure you want to delete this schedule?')) {
      return;
    }

    try {
      const result = await apiService.deleteSchedule(scheduleId);
      if (result.success) {
        toast.success('Schedule deleted successfully');
        setSchedules(schedules.filter(s => s.id !== scheduleId));
      } else {
        toast.error(result.message || 'Failed to delete schedule');
      }
    } catch (error) {
      console.error('Error deleting schedule:', error);
      toast.error('Failed to delete schedule');
    }
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Schedules</h1>
          <p className="text-gray-600">Generate and manage teaching schedules</p>
        </div>
        <button
          onClick={() => setShowGenerateModal(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <PlusIcon className="h-5 w-5" />
          <span>Generate Schedule</span>
        </button>
      </div>

      {/* Schedules list */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Generated Schedules</h3>
        </div>

        {schedules.length === 0 ? (
          <div className="text-center py-12">
            <CalendarDaysIcon className="mx-auto h-16 w-16 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">No schedules yet</h3>
            <p className="mt-2 text-gray-600">
              Generate your first schedule to get started
            </p>
            <button
              onClick={() => setShowGenerateModal(true)}
              className="mt-4 btn-primary"
            >
              Generate Schedule
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {schedules.map((schedule) => (
              <div key={schedule.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      {schedule.success ? (
                        <CheckCircleIcon className="h-8 w-8 text-green-600" />
                      ) : (
                        <ExclamationTriangleIcon className="h-8 w-8 text-yellow-600" />
                      )}
                    </div>
                    <div>
                      <h4 className="text-lg font-medium text-gray-900">
                        {schedule.name}
                      </h4>
                      <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                        <span className="flex items-center">
                          <ClockIcon className="h-4 w-4 mr-1" />
                          {formatDate(schedule.created_at)}
                        </span>
                        <span>
                          {schedule.assignments.length} assignments
                        </span>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          schedule.success
                            ? 'bg-green-100 text-green-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {schedule.success ? 'Complete' : 'Has Issues'}
                        </span>
                      </div>
                      {schedule.description && (
                        <p className="mt-1 text-sm text-gray-600">
                          {schedule.description}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => navigate(`/schedules/${schedule.id}`)}
                      className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50"
                      title="View Schedule"
                    >
                      <EyeIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleDeleteSchedule(schedule.id)}
                      className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                      title="Delete Schedule"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Generate Schedule Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Generate New Schedule
            </h3>

            <div className="space-y-4">
              {/* Basic Info */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Schedule Name *
                </label>
                <input
                  type="text"
                  value={generationForm.name}
                  onChange={(e) => setGenerationForm(prev => ({...prev, name: e.target.value}))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Fall 2024 Schedule"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={generationForm.description}
                  onChange={(e) => setGenerationForm(prev => ({...prev, description: e.target.value}))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                  placeholder="Optional description"
                />
              </div>

              {/* Course Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Courses *
                </label>
                <div className="max-h-32 overflow-y-auto border border-gray-300 rounded-md p-2">
                  {courses.map(course => (
                    <label key={course.id} className="flex items-center space-x-2 py-1">
                      <input
                        type="checkbox"
                        checked={generationForm.course_ids.includes(course.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setGenerationForm(prev => ({
                              ...prev,
                              course_ids: [...prev.course_ids, course.id]
                            }));
                          } else {
                            setGenerationForm(prev => ({
                              ...prev,
                              course_ids: prev.course_ids.filter(id => id !== course.id)
                            }));
                          }
                        }}
                      />
                      <span className="text-sm">{course.code} - {course.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Policies */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Cog6ToothIcon className="h-4 w-4 inline mr-1" />
                  Scheduling Policies
                </label>
                <div className="space-y-2">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={generationForm.policies.tutorial_lab_independence}
                      onChange={(e) => setGenerationForm(prev => ({
                        ...prev,
                        policies: {...prev.policies, tutorial_lab_independence: e.target.checked}
                      }))}
                    />
                    <span className="text-sm">Tutorial-Lab Independence</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={generationForm.policies.tutorial_lab_equal_count}
                      onChange={(e) => setGenerationForm(prev => ({
                        ...prev,
                        policies: {...prev.policies, tutorial_lab_equal_count: e.target.checked}
                      }))}
                    />
                    <span className="text-sm">Equal Count Policy</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={generationForm.policies.tutorial_lab_number_matching}
                      onChange={(e) => setGenerationForm(prev => ({
                        ...prev,
                        policies: {...prev.policies, tutorial_lab_number_matching: e.target.checked}
                      }))}
                    />
                    <span className="text-sm">Number Matching</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={generationForm.policies.fairness_mode}
                      onChange={(e) => setGenerationForm(prev => ({
                        ...prev,
                        policies: {...prev.policies, fairness_mode: e.target.checked}
                      }))}
                    />
                    <span className="text-sm">Fairness Mode</span>
                  </label>
                </div>
              </div>

              {/* Optimization */}
              <div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={generationForm.optimize}
                    onChange={(e) => setGenerationForm(prev => ({...prev, optimize: e.target.checked}))}
                  />
                  <span className="text-sm font-medium">Apply optimization algorithms</span>
                </label>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowGenerateModal(false)}
                className="btn-secondary"
                disabled={isGenerating}
              >
                Cancel
              </button>
              <button
                onClick={handleGenerateSchedule}
                disabled={isGenerating}
                className="btn-primary"
              >
                {isGenerating ? 'Generating...' : 'Generate'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SchedulesPage;