import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import ScheduleGrid from './ScheduleGrid';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

const ScheduleViewer = () => {
  const [schedules, setSchedules] = useState([]);
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('table'); // 'table', 'calendar', or 'grid'

  useEffect(() => {
    loadSchedules();
  }, []);

  const loadSchedules = async () => {
    setLoading(true);
    try {
      const response = await api.get('/schedules');
      setSchedules(response.data);
    } catch (error) {
      toast.error('Failed to load schedules');
    } finally {
      setLoading(false);
    }
  };


  const deleteSchedule = async (scheduleId) => {
    if (window.confirm('Are you sure you want to delete this schedule?')) {
      try {
        await api.delete(`/schedules/${scheduleId}`);
        toast.success('Schedule deleted successfully');
        loadSchedules();
        if (selectedSchedule && selectedSchedule.id === scheduleId) {
          setSelectedSchedule(null);
        }
      } catch (error) {
        toast.error('Failed to delete schedule');
      }
    }
  };

  const getDayColor = (day) => {
    const colors = {
      saturday: 'bg-red-100 text-red-800',
      sunday: 'bg-orange-100 text-orange-800',
      monday: 'bg-yellow-100 text-yellow-800',
      tuesday: 'bg-green-100 text-green-800',
      wednesday: 'bg-blue-100 text-blue-800',
      thursday: 'bg-purple-100 text-purple-800'
    };
    return colors[day.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  const getTypeColor = (type) => {
    return type === 'tutorial'
      ? 'bg-blue-100 text-blue-800'
      : 'bg-green-100 text-green-800';
  };

  const getScheduleName = (schedule) => {
    if (!schedule.message) {
      return `Schedule #${schedule.id}`;
    }

    const message = schedule.message;

    // If it starts with ✅ or ⚠️, it's auto-generated
    if (message.startsWith('✅') || message.startsWith('⚠️')) {
      return `Schedule #${schedule.id}`;
    }

    // New format: "Schedule Name - Course Name | Optional Message"
    // Extract the full display name (schedule name + course name)
    const pipeIndex = message.indexOf(' | ');
    let displayText = '';

    if (pipeIndex > 0) {
      // Get everything before the pipe
      displayText = message.substring(0, pipeIndex).trim();
    } else {
      // No pipe, use the entire message
      displayText = message.trim();
    }

    // If we got a valid display text, use it
    if (displayText && displayText.length > 0 && /[a-zA-Z0-9]/.test(displayText)) {
      return displayText;
    }

    // Fallback to default format
    return `Schedule #${schedule.id}`;
  };

  const renderCalendarView = () => {
    if (!selectedSchedule) return null;

    const days = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday'];
    const slots = [1, 2, 3, 4, 5, 6, 7, 8];

    const getAssignmentsForSlot = (day, slot) => {
      return selectedSchedule.assignments.filter(
        assignment => assignment.day.toLowerCase() === day && assignment.slot_number === slot
      );
    };

    return (
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-gray-50">
              <th className="border border-gray-300 px-4 py-2 text-left font-medium">Slot</th>
              {days.map(day => (
                <th key={day} className="border border-gray-300 px-4 py-2 text-center font-medium capitalize">
                  {day}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {slots.map(slot => (
              <tr key={slot}>
                <td className="border border-gray-300 px-4 py-2 font-medium bg-gray-50">
                  Slot {slot}
                </td>
                {days.map(day => {
                  const assignments = getAssignmentsForSlot(day, slot);
                  return (
                    <td key={`${day}-${slot}`} className="border border-gray-300 px-2 py-2 min-h-16">
                      <div className="space-y-1">
                        {assignments.map((assignment, index) => (
                          <div
                            key={index}
                            className={`text-xs p-2 rounded ${getTypeColor(assignment.slot_type)} font-medium`}
                          >
                            <div className="font-bold">{assignment.ta_name}</div>
                            <div>{assignment.course_name}</div>
                            <div className="opacity-75">{assignment.slot_type} ({assignment.duration}h)</div>
                          </div>
                        ))}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">View Schedules</h1>
        {selectedSchedule && (
          <div className="flex space-x-2">
            <button
              onClick={() => {
                if (viewMode === 'table') setViewMode('calendar');
                else if (viewMode === 'calendar') setViewMode('grid');
                else setViewMode('table');
              }}
              className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-lg"
            >
              {viewMode === 'table' ? 'Calendar View' :
               viewMode === 'calendar' ? 'Grid View' : 'Table View'}
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Schedule List */}
        <div className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-lg font-semibold mb-4">Saved Schedules</h2>
          {loading ? (
            <div className="text-center py-4">Loading...</div>
          ) : schedules.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No schedules found. Generate a schedule first.
            </div>
          ) : (
            <div className="space-y-2">
              {schedules.map((schedule) => (
                <div
                  key={schedule.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedSchedule && selectedSchedule.id === schedule.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedSchedule(schedule)}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium">{getScheduleName(schedule)}</div>
                      <div className="text-sm text-gray-500">
                        {new Date(schedule.created_at).toLocaleDateString()}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        {schedule.assignments.length} assignments
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteSchedule(schedule.id);
                      }}
                      className="text-red-500 hover:text-red-700 text-sm"
                    >
                      Delete
                    </button>
                  </div>

                </div>
              ))}
            </div>
          )}
        </div>

        {/* Schedule Details */}
        <div className="lg:col-span-2">
          {selectedSchedule ? (
            <div className="bg-white rounded-lg shadow border">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-semibold text-gray-900">
                    {getScheduleName(selectedSchedule)} Details
                  </h2>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    selectedSchedule.success
                      ? 'bg-green-100 text-green-800'
                      : selectedSchedule.assignments.length > 0
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {selectedSchedule.success ? '✅ Success' :
                     selectedSchedule.assignments.length > 0 ? '⚠️ Partial' : '❌ Failed'}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Created: {new Date(selectedSchedule.created_at).toLocaleString()}
                </p>
              </div>

              <div className="p-6">

                {selectedSchedule.statistics && (
                  <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-blue-50 p-3 rounded">
                      <div className="text-2xl font-bold text-blue-600">
                        {Math.round(selectedSchedule.statistics.success_rate * 100)}%
                      </div>
                      <div className="text-sm text-gray-600">Success Rate</div>
                    </div>
                    <div className="bg-green-50 p-3 rounded">
                      <div className="text-2xl font-bold text-green-600">
                        {selectedSchedule.statistics.total_assignments}
                      </div>
                      <div className="text-sm text-gray-600">Assignments</div>
                    </div>
                    <div className="bg-orange-50 p-3 rounded">
                      <div className="text-2xl font-bold text-orange-600">
                        {selectedSchedule.statistics.policy_violations || 0}
                      </div>
                      <div className="text-sm text-gray-600">Violations</div>
                    </div>
                  </div>
                )}

                {selectedSchedule.assignments && selectedSchedule.assignments.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">
                      📅 Schedule Assignments ({viewMode} view)
                    </h3>

                    {viewMode === 'calendar' ? (
                      renderCalendarView()
                    ) : viewMode === 'grid' ? (
                      <ScheduleGrid assignments={selectedSchedule.assignments} />
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">TA</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Course</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Day</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Slot</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {selectedSchedule.assignments.map((assignment, index) => (
                              <tr key={index}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                  {assignment.ta_name}
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-900">
                                  {assignment.course_name}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getDayColor(assignment.day)}`}>
                                    {assignment.day}
                                  </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {assignment.slot_number}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getTypeColor(assignment.slot_type)}`}>
                                    {assignment.slot_type}
                                  </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {assignment.duration}h
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}

                {selectedSchedule.policies_used && (
                  <div className="mt-6">
                    <h3 className="font-semibold text-gray-900 mb-2">⚙️ Policies Applied:</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex items-center space-x-2">
                        <span className={selectedSchedule.policies_used.tutorial_lab_independence ? 'text-green-600' : 'text-red-600'}>
                          {selectedSchedule.policies_used.tutorial_lab_independence ? '✅' : '❌'}
                        </span>
                        <span>Tutorial-Lab Independence</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={selectedSchedule.policies_used.tutorial_lab_equal_count ? 'text-green-600' : 'text-red-600'}>
                          {selectedSchedule.policies_used.tutorial_lab_equal_count ? '✅' : '❌'}
                        </span>
                        <span>Equal Count Policy</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={selectedSchedule.policies_used.tutorial_lab_number_matching ? 'text-green-600' : 'text-red-600'}>
                          {selectedSchedule.policies_used.tutorial_lab_number_matching ? '✅' : '❌'}
                        </span>
                        <span>Number Matching</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={selectedSchedule.policies_used.fairness_mode ? 'text-green-600' : 'text-red-600'}>
                          {selectedSchedule.policies_used.fairness_mode ? '✅' : '❌'}
                        </span>
                        <span>Fairness Mode</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow border p-12 text-center">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Schedule Selected</h3>
              <p className="text-gray-500">
                Select a schedule from the list to view its details, assignments, and statistics.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScheduleViewer;