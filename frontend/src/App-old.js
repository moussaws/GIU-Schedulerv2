import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import toast, { Toaster } from 'react-hot-toast';
import './index.css';

// Simple API service
const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// Simple Layout Component
const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <div className="flex items-center space-x-3">
                <div className="bg-blue-600 rounded-lg p-2">
                  <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="text-xl font-bold text-gray-900">
                  GIU Staff Schedule Composer
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Backend Status:</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                ✅ Connected
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const [backendStatus, setBackendStatus] = useState(null);
  const [demoResult, setDemoResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check backend health
    const checkHealth = async () => {
      try {
        const response = await api.get('/health');
        setBackendStatus(response.data);
        toast.success('Connected to backend successfully!');
      } catch (error) {
        toast.error('Could not connect to backend');
      }
    };
    checkHealth();
  }, []);

  const testScheduling = async () => {
    setLoading(true);
    try {
      const response = await api.get('/demo-schedule');
      setDemoResult(response.data);
      toast.success('Scheduling test completed!');
    } catch (error) {
      toast.error('Scheduling test failed');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg shadow-sm p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Welcome to GIU Scheduler! 🎓</h1>
            <p className="text-blue-100 mt-2">
              Your intelligent teaching assistant scheduling system is ready
            </p>
          </div>
          <div className="hidden sm:block">
            <svg className="h-16 w-16 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">Backend Status</h3>
              <p className="text-sm text-gray-600">
                {backendStatus ? `✅ Healthy` : '⏳ Checking...'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">Scheduling Engine</h3>
              <p className="text-sm text-gray-600">
                {backendStatus?.scheduler_available ? '✅ Available' : '❌ Not Available'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <svg className="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">Features</h3>
              <p className="text-sm text-gray-600">Saturday-Thursday, Policies</p>
            </div>
          </div>
        </div>
      </div>

      {/* Test Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h2 className="text-lg font-semibold text-gray-900">🧪 Test Your Scheduling Algorithms</h2>
        </div>
        <div className="p-6">
          <p className="text-gray-600 mb-4">
            Test your original scheduling algorithms with a sample scenario including Saturday-Thursday support and policy enforcement.
          </p>
          <button
            onClick={testScheduling}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center space-x-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Testing...
              </>
            ) : (
              <>
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Run Demo Scheduling
              </>
            )}
          </button>
        </div>
      </div>

      {/* Demo Results */}
      {demoResult && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h2 className="text-lg font-semibold text-gray-900">
              📊 Scheduling Results
              {demoResult.success ? (
                <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  ✅ Success
                </span>
              ) : demoResult.assignments && demoResult.assignments.length > 0 ? (
                <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  ⚠️ Partial Success
                </span>
              ) : (
                <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  ❌ Failed
                </span>
              )}
            </h2>
          </div>
          <div className="p-6 space-y-4">
            <p className="text-gray-700">
              <strong>Message:</strong> {demoResult.message}
            </p>

            {demoResult.assignments && demoResult.assignments.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">📅 Schedule Assignments:</h3>
                <div className="space-y-2">
                  {demoResult.assignments.map((assignment, index) => (
                    <div key={index} className="bg-blue-50 p-3 rounded border-l-4 border-blue-500">
                      <div className="font-medium text-blue-900">
                        {assignment.ta_name} → {assignment.course_name}
                      </div>
                      <div className="text-sm text-blue-700">
                        {assignment.day.charAt(0).toUpperCase() + assignment.day.slice(1)} |
                        Slot {assignment.slot_number} |
                        {assignment.slot_type} |
                        {assignment.duration}h
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {demoResult.policies_used && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">⚙️ Policies Applied:</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>Tutorial-Lab Independence: {demoResult.policies_used.tutorial_lab_independence ? '✅ ON' : '❌ OFF'}</div>
                  <div>Equal Count Policy: {demoResult.policies_used.tutorial_lab_equal_count ? '✅ ON' : '❌ OFF'}</div>
                  <div>Number Matching: {demoResult.policies_used.tutorial_lab_number_matching ? '✅ ON' : '❌ OFF'}</div>
                  <div>Fairness Mode: {demoResult.policies_used.fairness_mode ? '✅ ON' : '❌ OFF'}</div>
                </div>
              </div>
            )}

            {demoResult.statistics && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">📈 Performance Statistics:</h3>
                <div className="bg-gray-50 p-3 rounded border">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>Success Rate: {Math.round(demoResult.statistics.success_rate * 100)}%</div>
                    <div>Total Assignments: {demoResult.statistics.total_assignments}</div>
                    <div>Policy Violations: {demoResult.statistics.policy_violations || 0}</div>
                    <div>Average TA Workload: {demoResult.statistics.average_ta_workload}h</div>
                  </div>
                </div>
              </div>
            )}

            <div className="bg-green-50 p-3 rounded border border-green-200">
              <p className="text-green-800 font-medium">🎉 {demoResult.demo_info}</p>
            </div>
          </div>
        </div>
      )}

      {/* Info */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">🎯 System Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="text-green-500">✅</span>
              <span>Saturday-Thursday Week Support</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-500">✅</span>
              <span>Tutorial-Lab Independence (Default OFF)</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-500">✅</span>
              <span>Equal Count Policy</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-500">✅</span>
              <span>Number Matching Policy</span>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="text-green-500">✅</span>
              <span>Fairness Mode & Workload Balancing</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-500">✅</span>
              <span>Conflict Detection & Resolution</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-500">✅</span>
              <span>Statistics & Performance Metrics</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-500">✅</span>
              <span>Export in Multiple Formats</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const App = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={
            <Layout>
              <Dashboard />
            </Layout>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            style: {
              background: '#10B981',
            },
          },
          error: {
            style: {
              background: '#EF4444',
            },
          },
        }}
      />
    </Router>
  );
};

export default App;