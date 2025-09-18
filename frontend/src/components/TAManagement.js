import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

const TAManagement = () => {
  const [tas, setTas] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingTA, setEditingTA] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    course_allocations: [],
    blocked_slots: [],
    day_off: '',
    premasters: false,
    skills: '',
    notes: ''
  });

  const days = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday']; // Friday excluded - weekend

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [tasRes, coursesRes] = await Promise.all([
        api.get('/tas'),
        api.get('/courses')
      ]);
      setTas(tasRes.data);
      setCourses(coursesRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: formData.name,
        email: `${formData.name.toLowerCase().replace(/\s+/g, '.')}@email.com`,
        course_allocations: formData.course_allocations,
        blocked_slots: formData.blocked_slots,
        day_off: formData.day_off || null,
        premasters: formData.premasters,
        skills: formData.skills.split(',').map(s => s.trim()).filter(s => s),
        notes: formData.notes
      };

      if (editingTA) {
        await api.put(`/tas/${editingTA.id}`, payload);
        toast.success('TA updated successfully');
      } else {
        await api.post('/tas', payload);
        toast.success('TA added successfully');
      }

      setShowForm(false);
      setEditingTA(null);
      resetForm();
      loadData();
    } catch (error) {
      toast.error(editingTA ? 'Failed to update TA' : 'Failed to add TA');
      console.error(error);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      course_allocations: [],
      blocked_slots: [],
      day_off: '',
      premasters: false,
      skills: '',
      notes: ''
    });
  };

  const handleEdit = (ta) => {
    setEditingTA(ta);
    setFormData({
      name: ta.name,
      course_allocations: ta.course_allocations || [],
      blocked_slots: ta.blocked_slots || [],
      day_off: ta.day_off || '',
      premasters: ta.premasters || false,
      skills: ta.skills?.join(', ') || '',
      notes: ta.notes || ''
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this TA?')) {
      try {
        await api.delete(`/tas/${id}`);
        toast.success('TA deleted successfully');
        loadData();
      } catch (error) {
        toast.error('Failed to delete TA');
      }
    }
  };

  const addCourseAllocation = () => {
    if (courses.length === 0) {
      toast.error('Please add courses first');
      return;
    }
    setFormData(prev => ({
      ...prev,
      course_allocations: [
        ...prev.course_allocations,
        { course_id: courses[0].id, allocated_hours: 2 }
      ]
    }));
  };

  const removeCourseAllocation = (index) => {
    setFormData(prev => ({
      ...prev,
      course_allocations: prev.course_allocations.filter((_, i) => i !== index)
    }));
  };

  const updateCourseAllocation = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      course_allocations: prev.course_allocations.map((allocation, i) =>
        i === index ? { ...allocation, [field]: value } : allocation
      )
    }));
  };

  const addBlockedSlot = () => {
    setFormData(prev => ({
      ...prev,
      blocked_slots: [
        ...prev.blocked_slots,
        { day: 'saturday', slot_number: 1, reason: 'Other obligation' }
      ]
    }));
  };

  const removeBlockedSlot = (index) => {
    setFormData(prev => ({
      ...prev,
      blocked_slots: prev.blocked_slots.filter((_, i) => i !== index)
    }));
  };

  const updateBlockedSlot = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      blocked_slots: prev.blocked_slots.map((slot, i) =>
        i === index ? { ...slot, [field]: value } : slot
      )
    }));
  };

  const getCourseName = (courseId) => {
    const course = courses.find(c => c.id === courseId);
    return course ? `${course.code} - ${course.name}` : `Course ${courseId}`;
  };

  const getTotalAllocatedHours = (allocations) => {
    return allocations.reduce((total, allocation) => total + allocation.allocated_hours, 0);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Teaching Assistant Management</h1>
        <button
          onClick={() => {
            setShowForm(true);
            setEditingTA(null);
            resetForm();
          }}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg"
        >
          Add New TA
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-lg font-semibold mb-4">
            {editingTA ? 'Edit Teaching Assistant' : 'Add New Teaching Assistant'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Information */}
            <div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter TA name"
                />
              </div>
            </div>

            {/* Course Allocations */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <label className="block text-sm font-medium text-gray-700">
                  Course Hour Allocations
                  {formData.course_allocations.length > 0 && (
                    <span className="ml-2 text-blue-600 font-semibold">
                      (Total: {getTotalAllocatedHours(formData.course_allocations)}h/week)
                    </span>
                  )}
                </label>
                <button
                  type="button"
                  onClick={addCourseAllocation}
                  className="bg-green-600 hover:bg-green-700 text-white font-medium py-1 px-3 rounded text-sm"
                >
                  Add Course
                </button>
              </div>

              <div className="space-y-3 max-h-48 overflow-y-auto">
                {formData.course_allocations.map((allocation, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                    <div className="flex-1">
                      <select
                        value={allocation.course_id}
                        onChange={(e) => updateCourseAllocation(index, 'course_id', parseInt(e.target.value))}
                        className="w-full px-3 py-1 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                      >
                        {courses.map(course => (
                          <option key={course.id} value={course.id}>
                            {course.code} - {course.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="w-24">
                      <input
                        type="number"
                        min="1"
                        max="25"
                        value={allocation.allocated_hours}
                        onChange={(e) => updateCourseAllocation(index, 'allocated_hours', parseInt(e.target.value))}
                        className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500 text-center"
                      />
                    </div>
                    <span className="text-sm text-gray-600">hours</span>
                    <button
                      type="button"
                      onClick={() => removeCourseAllocation(index)}
                      className="text-red-500 hover:text-red-700 p-1"
                    >
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
                {formData.course_allocations.length === 0 && (
                  <p className="text-gray-500 text-sm py-3 text-center bg-gray-50 rounded-lg">
                    No course allocations yet. Click "Add Course" to assign hours to specific courses.
                  </p>
                )}
              </div>
            </div>

            {/* Blocked Time Slots */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <label className="block text-sm font-medium text-gray-700">
                  Blocked Time Slots
                  <span className="text-xs text-gray-500 block">Times when TA is unavailable due to other obligations</span>
                </label>
                <button
                  type="button"
                  onClick={addBlockedSlot}
                  className="bg-red-600 hover:bg-red-700 text-white font-medium py-1 px-3 rounded text-sm"
                >
                  Add Blocked Slot
                </button>
              </div>

              <div className="space-y-3 max-h-48 overflow-y-auto">
                {formData.blocked_slots.map((slot, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 bg-red-50 rounded-lg">
                    <div className="w-32">
                      <select
                        value={slot.day}
                        onChange={(e) => updateBlockedSlot(index, 'day', e.target.value)}
                        className="w-full px-3 py-1 border border-gray-300 rounded focus:ring-red-500 focus:border-red-500"
                      >
                        {days.map(day => (
                          <option key={day} value={day}>
                            {day.charAt(0).toUpperCase() + day.slice(1)}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="w-20">
                      <input
                        type="number"
                        min="1"
                        max="8"
                        value={slot.slot_number}
                        onChange={(e) => updateBlockedSlot(index, 'slot_number', parseInt(e.target.value))}
                        className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-red-500 focus:border-red-500 text-center"
                      />
                    </div>
                    <span className="text-sm text-gray-600">Slot</span>
                    <div className="flex-1">
                      <input
                        type="text"
                        value={slot.reason}
                        onChange={(e) => updateBlockedSlot(index, 'reason', e.target.value)}
                        placeholder="Reason (e.g., Other course, Meeting)"
                        className="w-full px-3 py-1 border border-gray-300 rounded focus:ring-red-500 focus:border-red-500"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => removeBlockedSlot(index)}
                      className="text-red-500 hover:text-red-700 p-1"
                    >
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
                {formData.blocked_slots.length === 0 && (
                  <p className="text-gray-500 text-sm py-3 text-center bg-gray-50 rounded-lg">
                    No blocked slots. Add times when this TA is unavailable.
                  </p>
                )}
              </div>
            </div>

            {/* Day Off and Premasters */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Day Off
                  <span className="text-xs text-gray-500 block">Day when TA is completely unavailable</span>
                </label>
                <select
                  value={formData.day_off}
                  onChange={(e) => setFormData({ ...formData, day_off: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">No specific day off</option>
                  {days.map(day => (
                    <option key={day} value={day}>
                      {day.charAt(0).toUpperCase() + day.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Schedule Restrictions
                  <span className="text-xs text-gray-500 block">Special scheduling constraints</span>
                </label>
                <div className="flex items-center space-x-3 pt-2">
                  <input
                    type="checkbox"
                    id="premasters"
                    checked={formData.premasters}
                    onChange={(e) => setFormData({ ...formData, premasters: e.target.checked })}
                    className="w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500 focus:ring-2"
                  />
                  <label htmlFor="premasters" className="text-sm font-medium text-gray-700">
                    Premasters Student
                    <span className="text-xs text-purple-600 block">Can only take slots 1-2 on Saturday (free other days)</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Skills and Notes */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Skills (comma-separated)</label>
                <input
                  type="text"
                  value={formData.skills}
                  onChange={(e) => setFormData({ ...formData, skills: e.target.value })}
                  placeholder="Python, Java, Mathematics, etc."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <input
                  type="text"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Additional notes about this TA"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex space-x-4 pt-4 border-t border-gray-200">
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg"
              >
                {editingTA ? 'Update TA' : 'Add TA'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditingTA(null);
                  resetForm();
                }}
                className="bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-2 px-4 rounded-lg"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* TA List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Teaching Assistants ({tas.length})</h2>
        </div>
        <div className="p-6">
          {loading ? (
            <div className="text-center py-4">Loading...</div>
          ) : tas.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No TAs added yet. Click "Add New TA" to get started.
            </div>
          ) : (
            <div className="space-y-4">
              {tas.map((ta) => (
                <div key={ta.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{ta.name}</h3>
                      <p className="text-gray-600">{ta.email}</p>
                      {ta.notes && (
                        <p className="text-sm text-gray-500 mt-1">{ta.notes}</p>
                      )}
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleEdit(ta)}
                        className="text-blue-600 hover:text-blue-900 px-3 py-1 rounded hover:bg-blue-50"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(ta.id)}
                        className="text-red-600 hover:text-red-900 px-3 py-1 rounded hover:bg-red-50"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Course Allocations */}
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">
                        Course Allocations ({ta.total_allocated_hours}h total)
                      </h4>
                      {ta.course_allocations && ta.course_allocations.length > 0 ? (
                        <div className="space-y-1">
                          {ta.course_allocations.map((allocation, index) => (
                            <div key={index} className="text-sm bg-blue-50 p-2 rounded">
                              <div className="font-medium">{getCourseName(allocation.course_id)}</div>
                              <div className="text-blue-600">{allocation.allocated_hours} hours/week</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-500 text-sm">No course allocations</p>
                      )}
                    </div>

                    {/* Blocked Slots */}
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">
                        Blocked Slots ({ta.blocked_slots ? ta.blocked_slots.length : 0})
                      </h4>
                      {ta.blocked_slots && ta.blocked_slots.length > 0 ? (
                        <div className="space-y-1">
                          {ta.blocked_slots.map((slot, index) => (
                            <div key={index} className="text-sm bg-red-50 p-2 rounded">
                              <div className="font-medium capitalize">
                                {slot.day} - Slot {slot.slot_number}
                              </div>
                              <div className="text-red-600 text-xs">{slot.reason}</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-500 text-sm">No blocked slots</p>
                      )}
                    </div>

                    {/* Day Off */}
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Day Off</h4>
                      {ta.day_off ? (
                        <div className="text-sm bg-orange-50 p-2 rounded">
                          <div className="font-medium capitalize text-orange-900">
                            {ta.day_off}
                          </div>
                          <div className="text-orange-600 text-xs">Completely unavailable</div>
                        </div>
                      ) : (
                        <p className="text-gray-500 text-sm">No specific day off</p>
                      )}

                      {/* Premasters Status */}
                      {ta.premasters && (
                        <div className="text-sm bg-purple-50 p-2 rounded mt-2">
                          <div className="font-medium text-purple-900">Premasters Student</div>
                          <div className="text-purple-600 text-xs">Saturday slots 1-2 only (free other days)</div>
                        </div>
                      )}
                    </div>

                    {/* Skills */}
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Skills</h4>
                      {ta.skills && ta.skills.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {ta.skills.map((skill, index) => (
                            <span key={index} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              {skill}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-500 text-sm">No skills listed</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TAManagement;