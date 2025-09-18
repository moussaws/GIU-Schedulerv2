import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

const TAManagement = () => {
  const [tas, setTas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingTA, setEditingTA] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    max_hours: 8,
    preferred_courses: '',
    skills: ''
  });

  useEffect(() => {
    loadTAs();
  }, []);

  const loadTAs = async () => {
    setLoading(true);
    try {
      const response = await api.get('/tas');
      setTas(response.data);
    } catch (error) {
      toast.error('Failed to load TAs');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        preferred_courses: formData.preferred_courses.split(',').map(c => c.trim()).filter(c => c),
        skills: formData.skills.split(',').map(s => s.trim()).filter(s => s)
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
      setFormData({ name: '', email: '', max_hours: 8, preferred_courses: '', skills: '' });
      loadTAs();
    } catch (error) {
      toast.error(editingTA ? 'Failed to update TA' : 'Failed to add TA');
    }
  };

  const handleEdit = (ta) => {
    setEditingTA(ta);
    setFormData({
      name: ta.name,
      email: ta.email,
      max_hours: ta.max_hours,
      preferred_courses: ta.preferred_courses?.join(', ') || '',
      skills: ta.skills?.join(', ') || ''
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this TA?')) {
      try {
        await api.delete(`/tas/${id}`);
        toast.success('TA deleted successfully');
        loadTAs();
      } catch (error) {
        toast.error('Failed to delete TA');
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Teaching Assistants</h1>
        <button
          onClick={() => {
            setShowForm(true);
            setEditingTA(null);
            setFormData({ name: '', email: '', max_hours: 8, preferred_courses: '', skills: '' });
          }}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg"
        >
          Add New TA
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-lg font-semibold mb-4">
            {editingTA ? 'Edit TA' : 'Add New TA'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Hours per Week</label>
              <input
                type="number"
                min="1"
                max="20"
                value={formData.max_hours}
                onChange={(e) => setFormData({ ...formData, max_hours: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Courses (comma-separated)</label>
              <input
                type="text"
                value={formData.preferred_courses}
                onChange={(e) => setFormData({ ...formData, preferred_courses: e.target.value })}
                placeholder="CS101, CS102, MATH201"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Skills (comma-separated)</label>
              <input
                type="text"
                value={formData.skills}
                onChange={(e) => setFormData({ ...formData, skills: e.target.value })}
                placeholder="Python, Java, Mathematics"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div className="flex space-x-4">
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
                }}
                className="bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-2 px-4 rounded-lg"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Current TAs</h2>
        </div>
        <div className="p-6">
          {loading ? (
            <div className="text-center py-4">Loading...</div>
          ) : tas.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No TAs added yet. Click "Add New TA" to get started.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Max Hours</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Preferred Courses</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {tas.map((ta) => (
                    <tr key={ta.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{ta.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{ta.email}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{ta.max_hours}h</td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {ta.preferred_courses?.slice(0, 2).join(', ')}
                        {ta.preferred_courses?.length > 2 && '...'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <button
                          onClick={() => handleEdit(ta)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(ta.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TAManagement;