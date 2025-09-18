import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import LoginPage from './pages/Login';
import Dashboard from './pages/Dashboard';
import CoursesPage from './pages/Courses';
import TeachingAssistantsPage from './pages/TeachingAssistants';
import SchedulesPage from './pages/Schedules';
import ScheduleViewerPage from './pages/ScheduleViewer';
import SettingsPage from './pages/Settings';
import { useAuth } from './hooks/useAuth';
import './index.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Skip authentication for demo
  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className=\"min-h-screen bg-gray-50\">
          <Routes>
            <Route path=\"/login\" element={<LoginPage />} />

            <Route path=\"/\" element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }>
              <Route index element={<Dashboard />} />
              <Route path=\"courses\" element={<CoursesPage />} />
              <Route path=\"teaching-assistants\" element={<TeachingAssistantsPage />} />
              <Route path=\"schedules\" element={<SchedulesPage />} />
              <Route path=\"schedules/:id\" element={<ScheduleViewerPage />} />
              <Route path=\"settings\" element={<SettingsPage />} />
            </Route>
          </Routes>
        </div>
      </Router>

      <Toaster
        position=\"top-right\"
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
    </QueryClientProvider>
  );
};

export default App;