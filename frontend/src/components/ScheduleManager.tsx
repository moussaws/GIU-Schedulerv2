import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeftIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  DocumentArrowDownIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';
import ScheduleCalendar from './ScheduleCalendar';
import ScheduleGrid from './ScheduleGrid';
import { Schedule, ConflictInfo, DayEnum } from '../types';
import { apiService } from '../services/api';
import swapValidationService from '../services/swapValidation';
import toast from 'react-hot-toast';

interface ScheduleManagerProps {
  scheduleId?: number;
}

const ScheduleManager: React.FC<ScheduleManagerProps> = ({ scheduleId }) => {
  const params = useParams<{ id: string }>();
  const navigate = useNavigate();

  const id = scheduleId || (params.id ? parseInt(params.id) : null);

  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [conflicts, setConflicts] = useState<ConflictInfo[]>([]);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [viewMode, setViewMode] = useState<'calendar' | 'grid' | 'list'>('calendar');

  // Load schedule data
  useEffect(() => {
    if (!id) {
      setLoading(false);
      return;
    }

    const loadSchedule = async () => {
      try {
        setLoading(true);
        const [scheduleData, conflictsData] = await Promise.all([
          apiService.getSchedule(id),
          apiService.getScheduleConflicts(id)
        ]);

        setSchedule(scheduleData);
        setConflicts(conflictsData.conflicts || []);
      } catch (error) {
        console.error('Error loading schedule:', error);
        toast.error('Failed to load schedule');
        if (!scheduleId) {
          navigate('/schedules');
        }
      } finally {
        setLoading(false);
      }
    };

    loadSchedule();
  }, [id, navigate, scheduleId]);

  // Handle assignment swapping
  const handleAssignmentSwap = async (sourceId: string, destinationId: string): Promise<boolean> => {
    if (!schedule) return false;

    try {
      const sourceAssignmentId = parseInt(sourceId);
      const sourceAssignment = schedule.assignments.find(a => a.id === sourceAssignmentId);

      if (!sourceAssignment) {
        toast.error('Source assignment not found');
        return false;
      }

      // Parse destination (format: "day-slot")
      const [day, slotStr] = destinationId.split('-');
      const slot_number = parseInt(slotStr);

      const targetSlot = {
        day: day as DayEnum,
        slot_number
      };

      // Perform the swap
      const result = await apiService.swapAssignment(schedule.id, sourceAssignmentId, targetSlot);

      if (result.success) {
        toast.success('Assignment moved successfully');

        // Reload schedule to reflect changes
        const updatedSchedule = await apiService.getSchedule(schedule.id);
        const updatedConflicts = await apiService.getScheduleConflicts(schedule.id);

        setSchedule(updatedSchedule);
        setConflicts(updatedConflicts.conflicts || []);

        return true;
      } else {
        toast.error(result.message || 'Failed to move assignment');
        return false;
      }
    } catch (error: any) {
      console.error('Error swapping assignment:', error);
      if (error.response?.status === 409) {
        toast.error('TA already assigned to that time slot');
      } else if (error.response?.status === 404) {
        toast.error('Target time slot not available for this course');
      } else {
        toast.error('Failed to move assignment');
      }
      return false;
    }
  };

  // Validate swap before performing
  const handleValidateSwap = async (sourceId: string, destinationId: string): Promise<ConflictInfo[]> => {
    if (!schedule) return [];

    try {
      const sourceAssignmentId = parseInt(sourceId);
      const sourceAssignment = schedule.assignments.find(a => a.id === sourceAssignmentId);

      if (!sourceAssignment) return [];

      // Parse destination
      const [day, slotStr] = destinationId.split('-');
      const slot_number = parseInt(slotStr);

      const result = await apiService.validateSwap(
        schedule.id,
        sourceAssignmentId,
        { day, slot_number }
      );

      return [...(result.conflicts || []), ...(result.warnings || [])];
    } catch (error) {
      console.error('Error validating swap:', error);
      return [];
    }
  };

  // Optimize schedule
  const handleOptimizeSchedule = async () => {
    if (!schedule) return;

    try {
      setIsOptimizing(true);
      const result = await apiService.optimizeSchedule(schedule.id);

      if (result.success) {
        toast.success('Schedule optimized successfully');

        // Reload schedule
        const updatedSchedule = await apiService.getSchedule(schedule.id);
        const updatedConflicts = await apiService.getScheduleConflicts(schedule.id);

        setSchedule(updatedSchedule);
        setConflicts(updatedConflicts.conflicts || []);
      } else {
        toast.error(result.message || 'Failed to optimize schedule');
      }
    } catch (error) {
      console.error('Error optimizing schedule:', error);
      toast.error('Failed to optimize schedule');
    } finally {
      setIsOptimizing(false);
    }
  };

  // Export schedule
  const handleExportSchedule = async (format: 'grid' | 'list' | 'csv') => {
    if (!schedule) return;

    try {
      setIsExporting(true);
      const content = await apiService.exportSchedule(schedule.id, format);

      // Download file
      const blob = new Blob([content], {
        type: format === 'csv' ? 'text/csv' : 'text/plain'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `schedule_${schedule.id}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success(`Schedule exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Error exporting schedule:', error);
      toast.error('Failed to export schedule');
    } finally {
      setIsExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!schedule) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="mx-auto h-16 w-16 text-gray-400" />
        <h3 className="mt-4 text-lg font-medium text-gray-900">Schedule not found</h3>
        <p className="mt-2 text-gray-600">The requested schedule could not be loaded.</p>
        {!scheduleId && (
          <button
            onClick={() => navigate('/schedules')}
            className="mt-4 btn-primary"
          >
            Back to Schedules
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {!scheduleId && (
            <button
              onClick={() => navigate('/schedules')}
              className="p-2 rounded-lg hover:bg-gray-100"
            >
              <ArrowLeftIcon className="h-5 w-5 text-gray-600" />
            </button>
          )}
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{schedule.name}</h1>
            <div className="flex items-center space-x-4 mt-1">
              <p className="text-gray-600">{schedule.description}</p>
              <div className="flex items-center space-x-2">
                {schedule.success ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-600" />
                ) : (
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />
                )}
                <span className={`text-sm font-medium ${
                  schedule.success ? 'text-green-600' : 'text-yellow-600'
                }`}>
                  {schedule.success ? 'Generated Successfully' : 'Has Issues'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* View mode toggle */}
          <div className="flex rounded-md shadow-sm">
            <button
              onClick={() => setViewMode('calendar')}
              className={`px-3 py-2 text-sm font-medium rounded-l-md border ${
                viewMode === 'calendar'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              Calendar
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-2 text-sm font-medium border border-l-0 ${
                viewMode === 'grid'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              Grid
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-2 text-sm font-medium rounded-r-md border border-l-0 ${
                viewMode === 'list'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              List
            </button>
          </div>

          {/* Actions */}
          <button
            onClick={handleOptimizeSchedule}
            disabled={isOptimizing}
            className="btn-secondary flex items-center space-x-2"
          >
            <ArrowPathIcon className={`h-5 w-5 ${isOptimizing ? 'animate-spin' : ''}`} />
            <span>{isOptimizing ? 'Optimizing...' : 'Optimize'}</span>
          </button>

          <div className="relative">
            <button
              disabled={isExporting}
              className="btn-secondary flex items-center space-x-2 dropdown-toggle"
              onClick={() => handleExportSchedule('grid')}
            >
              <DocumentArrowDownIcon className="h-5 w-5" />
              <span>{isExporting ? 'Exporting...' : 'Export'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Conflicts summary */}
      {conflicts.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 mr-3 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800">
                {conflicts.length} conflict{conflicts.length !== 1 ? 's' : ''} detected
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <ul className="list-disc list-inside space-y-1">
                  {conflicts.slice(0, 3).map((conflict, index) => (
                    <li key={index}>
                      {conflict.type === 'double_booking' &&
                        `${conflict.ta_name} is double-booked at ${conflict.slot}`}
                      {conflict.type === 'overcapacity' &&
                        `${conflict.ta_name} exceeds capacity by ${conflict.excess_hours} hours`}
                      {conflict.type === 'policy_violation' && conflict.message}
                    </li>
                  ))}
                  {conflicts.length > 3 && (
                    <li>... and {conflicts.length - 3} more</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="text-2xl font-bold text-gray-900">
            {schedule.assignments.length}
          </div>
          <div className="text-sm text-gray-600">Total Assignments</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-2xl font-bold text-gray-900">
            {new Set(schedule.assignments.map(a => a.ta_id)).size}
          </div>
          <div className="text-sm text-gray-600">Teaching Assistants</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-2xl font-bold text-gray-900">
            {new Set(schedule.assignments.map(a => a.course_id)).size}
          </div>
          <div className="text-sm text-gray-600">Courses</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-2xl font-bold text-gray-900">
            {conflicts.length}
          </div>
          <div className="text-sm text-gray-600">Conflicts</div>
        </div>
      </div>

      {/* Main content */}
      {schedule.assignments.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="text-center py-12">
            <ExclamationTriangleIcon className="mx-auto h-16 w-16 text-yellow-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">No Assignments Generated</h3>
            <div className="mt-2 text-gray-600">
              <p>The schedule was created but no assignments were generated.</p>
              <p className="mt-2">This usually means:</p>
              <ul className="mt-2 text-left max-w-md mx-auto">
                <li>• No TAs are assigned to the selected courses</li>
                <li>• No time slots are defined for the courses</li>
                <li>• TAs have no availability that matches course time slots</li>
                <li>• Scheduling conflicts prevent any valid assignments</li>
              </ul>
            </div>
            <div className="mt-6 space-x-3">
              <button
                onClick={handleOptimizeSchedule}
                disabled={isOptimizing}
                className="btn-primary"
              >
                {isOptimizing ? 'Optimizing...' : 'Try Optimization'}
              </button>
              <button
                onClick={() => navigate('/courses')}
                className="btn-secondary"
              >
                Check Course Setup
              </button>
            </div>
          </div>
        </div>
      ) : viewMode === 'calendar' ? (
        <ScheduleCalendar
          schedule={schedule}
          onAssignmentSwap={handleAssignmentSwap}
          onValidateSwap={handleValidateSwap}
          isEditable={true}
        />
      ) : viewMode === 'grid' ? (
        <ScheduleGrid
          assignments={schedule.assignments}
        />
      ) : (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-4 border-b">
            <h3 className="text-lg font-semibold">Assignment List</h3>
          </div>
          <div className="divide-y divide-gray-200">
            {schedule.assignments.map((assignment) => (
              <div key={assignment.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`
                      inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
                      ${assignment.time_slot.slot_type === 'tutorial'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-green-100 text-green-800'
                      }
                    `}>
                      {assignment.time_slot.slot_type.toUpperCase()}
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">
                        {assignment.course.name} ({assignment.course.code})
                      </div>
                      <div className="text-sm text-gray-600">
                        {assignment.ta.name}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {assignment.time_slot.day.charAt(0).toUpperCase() + assignment.time_slot.day.slice(1)}
                    </div>
                    <div className="text-sm text-gray-600">
                      Slot {assignment.time_slot.slot_number}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ScheduleManager;