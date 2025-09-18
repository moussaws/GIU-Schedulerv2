import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import ScheduleGrid from './ScheduleGrid';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

const ScheduleBuilder = () => {
  const [courses, setCourses] = useState([]);
  const [tas, setTas] = useState([]);
  const [selectedCourses, setSelectedCourses] = useState([]);
  const [selectedTAs, setSelectedTAs] = useState([]);
  const [policies, setPolicies] = useState({
    tutorial_lab_independence: false,
    tutorial_lab_equal_count: true,
    tutorial_lab_number_matching: false,
    fairness_mode: true
  });
  const [timeSlots, setTimeSlots] = useState([
    { day: 'saturday', slot: 1, type: 'tutorial', tutorial_number: 1, lab_number: null },
    { day: 'saturday', slot: 1, type: 'lab', tutorial_number: null, lab_number: 1 },
    { day: 'sunday', slot: 1, type: 'tutorial', tutorial_number: 2, lab_number: null },
    { day: 'sunday', slot: 1, type: 'lab', tutorial_number: null, lab_number: 2 },
    { day: 'monday', slot: 1, type: 'tutorial', tutorial_number: 3, lab_number: null },
    { day: 'monday', slot: 1, type: 'lab', tutorial_number: null, lab_number: 3 },
    { day: 'tuesday', slot: 1, type: 'tutorial', tutorial_number: 4, lab_number: null },
    { day: 'tuesday', slot: 1, type: 'lab', tutorial_number: null, lab_number: 4 },
    { day: 'wednesday', slot: 1, type: 'tutorial', tutorial_number: 5, lab_number: null },
    { day: 'wednesday', slot: 1, type: 'lab', tutorial_number: null, lab_number: 5 },
    { day: 'thursday', slot: 1, type: 'tutorial', tutorial_number: 6, lab_number: null },
    { day: 'thursday', slot: 1, type: 'lab', tutorial_number: null, lab_number: 6 }
  ]);
  const [loading, setLoading] = useState(false);
  const [schedule, setSchedule] = useState(null);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [scheduleName, setScheduleName] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [coursesRes, tasRes] = await Promise.all([
        api.get('/courses'),
        api.get('/tas')
      ]);
      setCourses(coursesRes.data);
      setTas(tasRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    }
  };

  const handleCourseToggle = (courseId) => {
    setSelectedCourses(prev =>
      prev.includes(courseId)
        ? prev.filter(id => id !== courseId)
        : [...prev, courseId]
    );
  };

  const handleTAToggle = (taId) => {
    setSelectedTAs(prev =>
      prev.includes(taId)
        ? prev.filter(id => id !== taId)
        : [...prev, taId]
    );
  };

  const addTimeSlot = () => {
    setTimeSlots(prev => [...prev, { day: 'saturday', slot: 1, type: 'tutorial', tutorial_number: null, lab_number: null }]);
  };

  const removeTimeSlot = (index) => {
    setTimeSlots(prev => prev.filter((_, i) => i !== index));
  };

  const updateTimeSlot = (index, field, value) => {
    setTimeSlots(prev => prev.map((slot, i) => {
      if (i === index) {
        const updatedSlot = { ...slot, [field]: value };
        // Reset numbers when type changes
        if (field === 'type') {
          if (value === 'tutorial') {
            updatedSlot.tutorial_number = 1;
            updatedSlot.lab_number = null;
          } else {
            updatedSlot.tutorial_number = null;
            updatedSlot.lab_number = 1;
          }
        }
        return updatedSlot;
      }
      return slot;
    }));
  };

  // Helper function to get max tutorials/labs from selected courses
  const getMaxTutorials = () => {
    if (selectedCourses.length === 0) return 0;
    const selectedCourseData = courses.filter(c => selectedCourses.includes(c.id));
    return Math.max(...selectedCourseData.map(c => c.tutorials), 0);
  };

  const getMaxLabs = () => {
    if (selectedCourses.length === 0) return 0;
    const selectedCourseData = courses.filter(c => selectedCourses.includes(c.id));
    return Math.max(...selectedCourseData.map(c => c.labs), 0);
  };

  const generateSchedule = async () => {
    if (selectedCourses.length === 0) {
      toast.error('Please select at least one course');
      return;
    }
    if (selectedTAs.length === 0) {
      toast.error('Please select at least one TA');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        course_ids: selectedCourses,
        ta_ids: selectedTAs,
        time_slots: timeSlots,
        policies: policies
      };

      const response = await api.post('/generate-schedule', payload);
      setSchedule(response.data);

      if (response.data.success) {
        toast.success('Schedule generated successfully!');
      } else {
        toast.warning('Schedule generated with some issues. Check the results below.');
      }
    } catch (error) {
      toast.error('Failed to generate schedule');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const exportSchedule = async (format) => {
    if (!schedule) {
      toast.error('No schedule to export');
      return;
    }

    try {
      const response = await api.post(`/export-schedule/${format}`, {
        schedule: schedule,
        format: format
      }, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `schedule.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success(`Schedule exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error(`Failed to export schedule as ${format}`);
    }
  };

  const saveSchedule = async () => {
    if (!scheduleName.trim()) {
      toast.error('Please enter a schedule name');
      return;
    }

    setSaving(true);
    try {
      const response = await api.post('/save-schedule', {
        name: scheduleName.trim(),
        schedule: schedule
      });

      if (response.data.success) {
        toast.success('Schedule saved successfully!');
        setShowSaveModal(false);
        setScheduleName('');
      } else {
        toast.error(response.data.message || 'Failed to save schedule');
      }
    } catch (error) {
      toast.error('Failed to save schedule');
      console.error(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Generate Schedule</h1>
        <button
          onClick={generateSchedule}
          disabled={loading || selectedCourses.length === 0 || selectedTAs.length === 0}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium py-2 px-4 rounded-lg flex items-center space-x-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Generating...</span>
            </>
          ) : (
            <>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>Generate Schedule</span>
            </>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Course Selection */}
        <div className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-lg font-semibold mb-4">Select Courses</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {courses.map(course => (
              <label key={course.id} className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={selectedCourses.includes(course.id)}
                  onChange={() => handleCourseToggle(course.id)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="font-medium">{course.code}</div>
                  <div className="text-sm text-gray-500">{course.name}</div>
                </div>
              </label>
            ))}
          </div>
          {courses.length === 0 && (
            <div className="text-gray-500 text-sm">No courses available. Add courses first.</div>
          )}
        </div>

        {/* TA Selection */}
        <div className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-lg font-semibold mb-4">Select TAs</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {tas.map(ta => (
              <label key={ta.id} className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={selectedTAs.includes(ta.id)}
                  onChange={() => handleTAToggle(ta.id)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="font-medium">{ta.name}</div>
                  <div className="text-sm text-gray-500">{ta.max_hours}h/week</div>
                </div>
              </label>
            ))}
          </div>
          {tas.length === 0 && (
            <div className="text-gray-500 text-sm">No TAs available. Add TAs first.</div>
          )}
        </div>

        {/* Policies */}
        <div className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-lg font-semibold mb-4">Scheduling Policies</h2>
          <div className="space-y-3">
            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={policies.tutorial_lab_independence}
                onChange={(e) => setPolicies(prev => ({
                  ...prev,
                  tutorial_lab_independence: e.target.checked
                }))}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <div>
                <div className="font-medium">Tutorial-Lab Independence</div>
                <div className="text-sm text-gray-500">Same TA can't do both tutorial & lab for same course</div>
              </div>
            </label>

            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={policies.tutorial_lab_equal_count}
                onChange={(e) => setPolicies(prev => ({
                  ...prev,
                  tutorial_lab_equal_count: e.target.checked
                }))}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <div>
                <div className="font-medium">Equal Count Policy</div>
                <div className="text-sm text-gray-500">Balance tutorial and lab assignments</div>
              </div>
            </label>

            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={policies.tutorial_lab_number_matching}
                onChange={(e) => setPolicies(prev => ({
                  ...prev,
                  tutorial_lab_number_matching: e.target.checked
                }))}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <div>
                <div className="font-medium">Number Matching</div>
                <div className="text-sm text-gray-500">Match tutorial and lab section numbers</div>
              </div>
            </label>

            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={policies.fairness_mode}
                onChange={(e) => setPolicies(prev => ({
                  ...prev,
                  fairness_mode: e.target.checked
                }))}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <div>
                <div className="font-medium">Fairness Mode</div>
                <div className="text-sm text-gray-500">Ensure fair workload distribution</div>
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* Time Slots */}
      <div className="bg-white rounded-lg shadow border p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Available Time Slots</h2>
          <button
            onClick={addTimeSlot}
            className="bg-green-600 hover:bg-green-700 text-white font-medium py-1 px-3 rounded text-sm"
          >
            Add Slot
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {timeSlots.map((slot, index) => (
            <div key={index} className="border rounded-lg p-4 space-y-3">
              <div className="flex justify-between items-start">
                <span className="font-medium">Slot {index + 1}</span>
                <button
                  onClick={() => removeTimeSlot(index)}
                  className="text-red-500 hover:text-red-700 text-sm"
                >
                  Remove
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Day</label>
                <select
                  value={slot.day}
                  onChange={(e) => updateTimeSlot(index, 'day', e.target.value)}
                  className="w-full px-3 py-1 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  <option value="saturday">Saturday</option>
                  <option value="sunday">Sunday</option>
                  <option value="monday">Monday</option>
                  <option value="tuesday">Tuesday</option>
                  <option value="wednesday">Wednesday</option>
                  <option value="thursday">Thursday</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Slot Number</label>
                <input
                  type="number"
                  min="1"
                  max="8"
                  value={slot.slot}
                  onChange={(e) => updateTimeSlot(index, 'slot', parseInt(e.target.value))}
                  className="w-full px-3 py-1 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={slot.type}
                  onChange={(e) => updateTimeSlot(index, 'type', e.target.value)}
                  className="w-full px-3 py-1 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  <option value="tutorial">Tutorial</option>
                  <option value="lab">Lab</option>
                </select>
              </div>

              {/* Tutorial/Lab Number Selection */}
              {slot.type === 'tutorial' && getMaxTutorials() > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tutorial Number</label>
                  <select
                    value={slot.tutorial_number || 1}
                    onChange={(e) => updateTimeSlot(index, 'tutorial_number', parseInt(e.target.value))}
                    className="w-full px-3 py-1 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500 text-sm"
                  >
                    {[...Array(getMaxTutorials())].map((_, i) => (
                      <option key={i + 1} value={i + 1}>T{i + 1}</option>
                    ))}
                  </select>
                </div>
              )}

              {slot.type === 'lab' && getMaxLabs() > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Lab Number</label>
                  <select
                    value={slot.lab_number || 1}
                    onChange={(e) => updateTimeSlot(index, 'lab_number', parseInt(e.target.value))}
                    className="w-full px-3 py-1 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500 text-sm"
                  >
                    {[...Array(getMaxLabs())].map((_, i) => (
                      <option key={i + 1} value={i + 1}>L{i + 1}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Schedule Results */}
      {schedule && (
        <div className="bg-white rounded-lg shadow border">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">
              📊 Generated Schedule
              {schedule.success ? (
                <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  ✅ Success
                </span>
              ) : schedule.assignments && schedule.assignments.length > 0 ? (
                <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  ⚠️ Partial Success
                </span>
              ) : (
                <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  ❌ Failed
                </span>
              )}
            </h2>
            <div className="flex space-x-2">
              <button
                onClick={() => setShowSaveModal(true)}
                className="bg-purple-600 hover:bg-purple-700 text-white font-medium py-1 px-3 rounded text-sm"
              >
                💾 Save Schedule
              </button>
              <button
                onClick={() => exportSchedule('xlsx')}
                className="bg-green-600 hover:bg-green-700 text-white font-medium py-1 px-3 rounded text-sm"
              >
                Export Excel
              </button>
              <button
                onClick={() => exportSchedule('csv')}
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-1 px-3 rounded text-sm"
              >
                Export CSV
              </button>
            </div>
          </div>

          <div className="p-6 space-y-4">
            <p className="text-gray-700">
              <strong>Result:</strong> {schedule.message}
            </p>

            {schedule.assignments && schedule.assignments.length > 0 && (
              <div>
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-semibold text-gray-900">📅 Schedule View:</h3>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setViewMode('grid')}
                      className={`px-3 py-1 rounded text-sm ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
                    >
                      📅 Grid View
                    </button>
                    <button
                      onClick={() => setViewMode('table')}
                      className={`px-3 py-1 rounded text-sm ${viewMode === 'table' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
                    >
                      📋 Table View
                    </button>
                  </div>
                </div>

                {viewMode === 'grid' ? (
                  <ScheduleGrid assignments={schedule.assignments} tas={tas} />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">TA</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Course</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Day</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Slot</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type & Number</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {schedule.assignments.map((assignment, index) => (
                          <tr key={index}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {assignment.ta_name}
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-900">
                              {assignment.course_name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                              {assignment.day}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {assignment.slot_number}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                              {assignment.slot_type === 'tutorial' && assignment.tutorial_number != null
                                ? `Tutorial T${assignment.tutorial_number}`
                                : assignment.slot_type === 'lab' && assignment.lab_number != null
                                ? `Lab L${assignment.lab_number}`
                                : assignment.slot_type === 'tutorial' ? 'Tutorial' : 'Lab'}
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

            {schedule.statistics && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-2xl font-bold text-blue-600">{Math.round(schedule.statistics.success_rate * 100)}%</div>
                  <div className="text-sm text-gray-600">Success Rate</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-2xl font-bold text-green-600">{schedule.statistics.total_assignments}</div>
                  <div className="text-sm text-gray-600">Total Assignments</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-2xl font-bold text-orange-600">{schedule.statistics.policy_violations || 0}</div>
                  <div className="text-sm text-gray-600">Policy Violations</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-2xl font-bold text-purple-600">{schedule.statistics.average_ta_workload}h</div>
                  <div className="text-sm text-gray-600">Avg TA Workload</div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Save Schedule Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              💾 Save Schedule
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Schedule Name *
                </label>
                <input
                  type="text"
                  value={scheduleName}
                  onChange={(e) => setScheduleName(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="e.g., Fall 2024 Final Schedule"
                  autoFocus
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowSaveModal(false);
                  setScheduleName('');
                }}
                className="bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-2 px-4 rounded"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={saveSchedule}
                disabled={saving || !scheduleName.trim()}
                className="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 text-white font-medium py-2 px-4 rounded"
              >
                {saving ? 'Saving...' : 'Save Schedule'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScheduleBuilder;