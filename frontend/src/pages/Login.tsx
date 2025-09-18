import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { EyeIcon, EyeSlashIcon, CalendarDaysIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../hooks/useAuth';
import { LoginRequest } from '../types';
import toast from 'react-hot-toast';

const LoginPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginRequest>();

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to=\"/\" replace />;
  }

  const onSubmit = async (data: LoginRequest) => {
    setIsLoading(true);
    try {
      const success = await login(data);
      if (success) {
        // Navigation will be handled by the auth hook
      }
    } catch (error) {
      console.error('Login error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className=\"min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 py-12 px-4 sm:px-6 lg:px-8\">
      <div className=\"max-w-md w-full space-y-8\">
        {/* Header */}
        <div className=\"text-center\">
          <div className=\"mx-auto h-20 w-20 bg-white rounded-full flex items-center justify-center mb-6 shadow-lg\">
            <CalendarDaysIcon className=\"h-10 w-10 text-primary-600\" />
          </div>
          <h2 className=\"text-3xl font-bold text-white\">
            Welcome Back
          </h2>
          <p className=\"mt-2 text-sm text-primary-100\">
            Sign in to your GIU Staff Schedule Composer account
          </p>
        </div>

        {/* Login Form */}
        <div className=\"bg-white rounded-lg shadow-xl p-8\">
          <form className=\"space-y-6\" onSubmit={handleSubmit(onSubmit)}>
            <div>
              <label htmlFor=\"username\" className=\"form-label\">
                Username
              </label>
              <input
                id=\"username\"
                type=\"text\"
                autoComplete=\"username\"
                className={`form-input ${errors.username ? 'border-red-300' : ''}`}
                placeholder=\"Enter your username\"
                {...register('username', {
                  required: 'Username is required',
                  minLength: {
                    value: 3,
                    message: 'Username must be at least 3 characters'
                  }
                })}
              />
              {errors.username && (
                <p className=\"mt-2 text-sm text-red-600\">{errors.username.message}</p>
              )}
            </div>

            <div>
              <label htmlFor=\"password\" className=\"form-label\">
                Password
              </label>
              <div className=\"relative\">
                <input
                  id=\"password\"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete=\"current-password\"
                  className={`form-input pr-10 ${errors.password ? 'border-red-300' : ''}`}
                  placeholder=\"Enter your password\"
                  {...register('password', {
                    required: 'Password is required',
                    minLength: {
                      value: 6,
                      message: 'Password must be at least 6 characters'
                    }
                  })}
                />
                <button
                  type=\"button\"
                  className=\"absolute inset-y-0 right-0 pr-3 flex items-center\"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeSlashIcon className=\"h-5 w-5 text-gray-400\" />
                  ) : (
                    <EyeIcon className=\"h-5 w-5 text-gray-400\" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className=\"mt-2 text-sm text-red-600\">{errors.password.message}</p>
              )}
            </div>

            <div>
              <button
                type=\"submit\"
                disabled={isLoading}
                className=\"w-full btn-primary flex justify-center py-3 text-base\"
              >
                {isLoading ? (
                  <>
                    <div className=\"spinner mr-3\" />
                    Signing in...
                  </>
                ) : (
                  'Sign in'
                )}
              </button>
            </div>
          </form>

          {/* Demo credentials info */}
          <div className=\"mt-6 p-4 bg-gray-50 rounded-lg\">
            <h3 className=\"text-sm font-medium text-gray-700 mb-2\">Demo Credentials</h3>
            <div className=\"text-xs text-gray-600 space-y-1\">
              <div><strong>Admin:</strong> admin / admin123</div>
              <div><strong>Staff:</strong> staff / staff123</div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className=\"text-center\">
          <p className=\"text-sm text-primary-100\">
            GIU Staff Schedule Composer v1.0
          </p>
          <p className=\"text-xs text-primary-200 mt-1\">
            Built with ❤️ for efficient scheduling
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;