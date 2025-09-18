import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  AcademicCapIcon,
  UserGroupIcon,
  CalendarDaysIcon,
  Cog6ToothIcon,
  Bars3Icon,
  XMarkIcon,
  BellIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../hooks/useAuth';
import clsx from 'clsx';

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Courses', href: '/courses', icon: AcademicCapIcon },
  { name: 'Teaching Assistants', href: '/teaching-assistants', icon: UserGroupIcon },
  { name: 'Schedules', href: '/schedules', icon: CalendarDaysIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

const Layout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className=\"h-screen flex overflow-hidden bg-gray-100\">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className=\"fixed inset-0 flex z-40 lg:hidden\">
          <div className=\"fixed inset-0 bg-gray-600 bg-opacity-75\" onClick={() => setSidebarOpen(false)} />
          <div className=\"relative flex-1 flex flex-col max-w-xs w-full bg-white\">
            <div className=\"absolute top-0 right-0 -mr-12 pt-2\">
              <button
                type=\"button\"
                className=\"ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white\"
                onClick={() => setSidebarOpen(false)}
              >
                <XMarkIcon className=\"h-6 w-6 text-white\" />
              </button>
            </div>
            <SidebarContent />
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className=\"hidden lg:flex lg:flex-shrink-0\">
        <div className=\"flex flex-col w-64\">
          <SidebarContent />
        </div>
      </div>

      {/* Main content */}
      <div className=\"flex flex-col w-0 flex-1 h-full\">
        {/* Top navigation */}
        <div className=\"relative z-10 flex-shrink-0 flex h-16 bg-white shadow border-b border-gray-200\">
          <button
            type=\"button\"
            className=\"px-4 border-r border-gray-200 text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 lg:hidden\"
            onClick={() => setSidebarOpen(true)}
          >
            <Bars3Icon className=\"h-6 w-6\" />
          </button>

          <div className=\"flex-1 px-4 flex justify-between items-center\">
            <div className=\"flex-1\">
              <h1 className=\"text-xl font-semibold text-gray-900\">
                {navigation.find(item => item.href === location.pathname)?.name || 'GIU Staff Schedule Composer'}
              </h1>
            </div>

            <div className=\"ml-4 flex items-center md:ml-6\">
              {/* Notifications */}
              <button
                type=\"button\"
                className=\"bg-white p-1 rounded-full text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500\"
              >
                <BellIcon className=\"h-6 w-6\" />
              </button>

              {/* Profile dropdown */}
              <div className=\"ml-3 relative\">
                <div className=\"flex items-center space-x-3\">
                  <div className=\"text-right hidden sm:block\">
                    <div className=\"text-sm font-medium text-gray-700\">{user?.username}</div>
                    <div className=\"text-xs text-gray-500\">{user?.role}</div>
                  </div>

                  <button
                    type=\"button\"
                    className=\"bg-white flex text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500\"
                    onClick={handleLogout}
                  >
                    <UserCircleIcon className=\"h-8 w-8 text-gray-400\" />
                  </button>

                  <button
                    onClick={handleLogout}
                    className=\"text-gray-400 hover:text-gray-500 p-2 rounded-md\"
                    title=\"Logout\"
                  >
                    <ArrowRightOnRectangleIcon className=\"h-5 w-5\" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className=\"flex-1 overflow-y-auto focus:outline-none scrollbar-thin\">
          <div className=\"py-6\">
            <div className=\"max-w-7xl mx-auto px-4 sm:px-6 md:px-8\">
              <Outlet />
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className=\"bg-gray-800 border-t border-gray-300 flex-shrink-0\">
          <div className=\"max-w-7xl mx-auto px-4 sm:px-6 md:px-8 py-6\">
            <div className=\"text-center text-base text-white font-medium\">
              Made with ❤️ by Moussa
            </div>
          </div>
        </footer>
      </div>
    </div>
  );

  function SidebarContent() {
    return (
      <div className=\"flex flex-col h-0 flex-1 border-r border-gray-200 bg-white\">
        <div className=\"flex-1 flex flex-col pt-5 pb-4 overflow-y-auto\">
          <div className=\"flex items-center flex-shrink-0 px-4\">
            <div className=\"flex items-center space-x-3\">
              <div className=\"bg-primary-600 rounded-lg p-2\">
                <CalendarDaysIcon className=\"h-8 w-8 text-white\" />
              </div>
              <div className=\"text-xl font-bold text-gray-900\">
                GIU Scheduler
              </div>
            </div>
          </div>

          <nav className=\"mt-8 flex-1 px-2 space-y-1\">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <a
                  key={item.name}
                  href={item.href}
                  onClick={(e) => {
                    e.preventDefault();
                    navigate(item.href);
                    setSidebarOpen(false);
                  }}
                  className={clsx(
                    isActive
                      ? 'bg-primary-100 border-primary-500 text-primary-700'
                      : 'border-transparent text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                    'group flex items-center px-2 py-2 text-sm font-medium border-l-4 cursor-pointer transition-colors'
                  )}
                >
                  <item.icon
                    className={clsx(
                      isActive
                        ? 'text-primary-500'
                        : 'text-gray-400 group-hover:text-gray-500',
                      'mr-3 h-6 w-6'
                    )}
                  />
                  {item.name}
                </a>
              );
            })}
          </nav>
        </div>

        <div className=\"flex-shrink-0 flex border-t border-gray-200 p-4\">
          <div className=\"text-xs text-gray-500 text-center w-full\">
            <div>GIU Staff Schedule Composer</div>
            <div>Version 1.0</div>
          </div>
        </div>
      </div>
    );
  }
};