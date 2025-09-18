import React from 'react';
import { useQuery } from 'react-query';
import {
  AcademicCapIcon,
  UserGroupIcon,
  CalendarDaysIcon,
  ChartBarIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import apiService from '../services/api';
import { Course, TeachingAssistant, Schedule } from '../types';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // Fetch dashboard data
  const { data: courses = [] } = useQuery<Course[]>('courses', apiService.getCourses);
  const { data: tas = [] } = useQuery<TeachingAssistant[]>('tas', apiService.getTAs);
  const { data: schedules = [] } = useQuery<Schedule[]>('schedules', apiService.getSchedules);

  // Calculate statistics
  const activeCourses = courses.filter(course => course.time_slots.length > 0);
  const activeTAs = tas.filter(ta => ta.is_active);
  const activeSchedules = schedules.filter(schedule => schedule.status === 'active');
  const draftSchedules = schedules.filter(schedule => schedule.status === 'draft');
  const successfulSchedules = schedules.filter(schedule => schedule.success);

  const stats = [
    {
      name: 'Total Courses',
      value: courses.length,
      subtext: `${activeCourses.length} with time slots`,
      icon: AcademicCapIcon,
      color: 'bg-blue-500',
      href: '/courses'
    },
    {
      name: 'Teaching Assistants',
      value: activeTAs.length,
      subtext: `${tas.length - activeTAs.length} inactive`,
      icon: UserGroupIcon,
      color: 'bg-green-500',
      href: '/teaching-assistants'
    },
    {
      name: 'Active Schedules',
      value: activeSchedules.length,
      subtext: `${draftSchedules.length} drafts`,
      icon: CalendarDaysIcon,
      color: 'bg-purple-500',
      href: '/schedules'
    },
    {
      name: 'Success Rate',
      value: schedules.length ? `${Math.round((successfulSchedules.length / schedules.length) * 100)}%` : '0%',
      subtext: `${successfulSchedules.length}/${schedules.length} successful`,
      icon: ChartBarIcon,
      color: 'bg-yellow-500',
      href: '/schedules'
    }
  ];

  const quickActions = [
    {
      name: 'Create New Course',
      description: 'Add a new course with time slots',
      href: '/courses',
      icon: AcademicCapIcon,
      color: 'bg-blue-500'
    },
    {
      name: 'Add Teaching Assistant',
      description: 'Register a new TA and set availability',
      href: '/teaching-assistants',
      icon: UserGroupIcon,
      color: 'bg-green-500'
    },
    {
      name: 'Generate Schedule',
      description: 'Create a new schedule with smart algorithms',
      href: '/schedules',
      icon: CalendarDaysIcon,
      color: 'bg-purple-500'
    }
  ];

  const recentSchedules = schedules
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  return (
    <div className=\"space-y-8\">
      {/* Welcome Header */}
      <div className=\"bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg shadow-sm p-6 text-white\">
        <div className=\"flex items-center justify-between\">
          <div>
            <h1 className=\"text-2xl font-bold\">
              Welcome back, {user?.username}! 👋
            </h1>
            <p className=\"text-primary-100 mt-2\">
              Here's an overview of your scheduling system
            </p>
          </div>
          <div className=\"hidden sm:block\">
            <CalendarDaysIcon className=\"h-16 w-16 text-primary-200\" />
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className=\"grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6\">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className=\"card hover:shadow-md transition-shadow cursor-pointer\"
            onClick={() => navigate(stat.href)}
          >
            <div className=\"card-body\">
              <div className=\"flex items-center\">
                <div className={`p-2 rounded-lg ${stat.color}`}>
                  <stat.icon className=\"h-6 w-6 text-white\" />
                </div>
                <div className=\"ml-4 flex-1\">
                  <p className=\"text-2xl font-bold text-gray-900\">{stat.value}</p>
                  <p className=\"text-sm text-gray-600\">{stat.name}</p>
                  <p className=\"text-xs text-gray-500 mt-1\">{stat.subtext}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className=\"grid grid-cols-1 lg:grid-cols-3 gap-8\">
        {/* Quick Actions */}
        <div className=\"lg:col-span-1\">
          <div className=\"card\">
            <div className=\"card-header\">
              <h2 className=\"text-lg font-semibold text-gray-900\">Quick Actions</h2>
            </div>
            <div className=\"card-body p-0\">
              <div className=\"space-y-1\">
                {quickActions.map((action, index) => (
                  <button
                    key={action.name}
                    onClick={() => navigate(action.href)}
                    className=\"w-full p-4 text-left hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-b-0\"
                  >
                    <div className=\"flex items-center space-x-3\">
                      <div className={`p-2 rounded-lg ${action.color}`}>
                        <action.icon className=\"h-5 w-5 text-white\" />
                      </div>
                      <div className=\"flex-1\">
                        <h3 className=\"font-medium text-gray-900\">{action.name}</h3>
                        <p className=\"text-sm text-gray-600\">{action.description}</p>
                      </div>
                      <PlusIcon className=\"h-5 w-5 text-gray-400\" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Recent Schedules */}
        <div className=\"lg:col-span-2\">
          <div className=\"card\">
            <div className=\"card-header flex items-center justify-between\">
              <h2 className=\"text-lg font-semibold text-gray-900\">Recent Schedules</h2>
              <button
                onClick={() => navigate('/schedules')}
                className=\"text-sm text-primary-600 hover:text-primary-700 font-medium\"
              >
                View all
              </button>
            </div>
            <div className=\"card-body p-0\">
              {recentSchedules.length === 0 ? (
                <div className=\"p-6 text-center\">
                  <CalendarDaysIcon className=\"mx-auto h-12 w-12 text-gray-400\" />
                  <h3 className=\"mt-2 text-sm font-medium text-gray-900\">No schedules yet</h3>
                  <p className=\"mt-1 text-sm text-gray-500\">
                    Get started by creating your first schedule.
                  </p>
                  <div className=\"mt-4\">
                    <button
                      onClick={() => navigate('/schedules')}
                      className=\"btn-primary\"
                    >
                      Create Schedule
                    </button>
                  </div>
                </div>
              ) : (
                <div className=\"space-y-1\">
                  {recentSchedules.map((schedule) => (
                    <div
                      key={schedule.id}
                      className=\"p-4 hover:bg-gray-50 transition-colors cursor-pointer border-b border-gray-100 last:border-b-0\"
                      onClick={() => navigate(`/schedules/${schedule.id}`)}
                    >
                      <div className=\"flex items-center justify-between\">
                        <div className=\"flex-1\">
                          <div className=\"flex items-center space-x-3\">
                            <h3 className=\"font-medium text-gray-900\">{schedule.name}</h3>
                            <span className={`status-indicator ${
                              schedule.success ? 'status-success' : 'status-error'
                            }`}>
                              {schedule.success ? (
                                <>
                                  <CheckCircleIcon className=\"h-4 w-4 mr-1\" />
                                  Success
                                </>
                              ) : (
                                <>
                                  <ExclamationTriangleIcon className=\"h-4 w-4 mr-1\" />
                                  Issues
                                </>
                              )}
                            </span>
                            <span className={`status-indicator ${
                              schedule.status === 'active' ? 'status-info' : 'status-warning'
                            }`}>
                              {schedule.status}
                            </span>
                          </div>
                          <p className=\"text-sm text-gray-600 mt-1\">{schedule.description || 'No description'}</p>
                          <div className=\"flex items-center space-x-4 text-xs text-gray-500 mt-2\">
                            <span className=\"flex items-center\">
                              <ClockIcon className=\"h-4 w-4 mr-1\" />
                              {new Date(schedule.created_at).toLocaleDateString()}
                            </span>
                            <span>{schedule.assignments.length} assignments</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className=\"card\">
        <div className=\"card-header\">
          <h2 className=\"text-lg font-semibold text-gray-900\">System Status</h2>
        </div>
        <div className=\"card-body\">
          <div className=\"grid grid-cols-1 md:grid-cols-3 gap-4\">
            <div className=\"text-center p-4 bg-green-50 rounded-lg\">
              <CheckCircleIcon className=\"h-8 w-8 text-green-500 mx-auto\" />
              <h3 className=\"mt-2 font-medium text-green-900\">API Status</h3>
              <p className=\"text-sm text-green-700\">All systems operational</p>
            </div>
            <div className=\"text-center p-4 bg-blue-50 rounded-lg\">
              <ChartBarIcon className=\"h-8 w-8 text-blue-500 mx-auto\" />
              <h3 className=\"mt-2 font-medium text-blue-900\">Performance</h3>
              <p className=\"text-sm text-blue-700\">Excellent response times</p>
            </div>
            <div className=\"text-center p-4 bg-purple-50 rounded-lg\">
              <CalendarDaysIcon className=\"h-8 w-8 text-purple-500 mx-auto\" />
              <h3 className=\"mt-2 font-medium text-purple-900\">Scheduler</h3>
              <p className=\"text-sm text-purple-700\">Ready for generation</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;