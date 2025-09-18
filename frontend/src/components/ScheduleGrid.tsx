import React from 'react';
import { Assignment, TeachingAssistant } from '../types';

interface ScheduleGridProps {
  assignments: Assignment[];
  tas?: TeachingAssistant[];
}

const ScheduleGrid: React.FC<ScheduleGridProps> = ({ assignments, tas = [] }) => {
  const days = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday'];
  const slots = [1, 2, 3, 4, 5];

  const taColors = [
    'bg-blue-100 border-blue-300 text-blue-800',
    'bg-green-100 border-green-300 text-green-800',
    'bg-purple-100 border-purple-300 text-purple-800',
    'bg-red-100 border-red-300 text-red-800',
    'bg-yellow-100 border-yellow-300 text-yellow-800',
    'bg-pink-100 border-pink-300 text-pink-800',
    'bg-indigo-100 border-indigo-300 text-indigo-800',
    'bg-orange-100 border-orange-300 text-orange-800'
  ];

  // Get TA color based on TA ID
  const getTAColor = (taId: number) => {
    const taIds = [...new Set(assignments.map(a => a.ta_id))].sort();
    const index = taIds.indexOf(taId);
    if (index === -1) return taColors[0];
    return taColors[index % taColors.length];
  };

  // Get TA name by ID
  const getTAName = (taId: number) => {
    const ta = tas.find(t => t.id === taId);
    return ta ? ta.name : `TA ${taId}`;
  };

  // Group assignments by day and slot
  const getAssignmentsForSlot = (day: string, slot: number) => {
    return assignments.filter(assignment =>
      assignment.day.toLowerCase() === day.toLowerCase() &&
      assignment.slot_number === slot
    );
  };

  return (
    <div className="bg-white rounded-lg shadow border overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold">📅 Schedule Calendar View</h3>
        <p className="text-sm text-gray-600 mt-1">Weekly schedule showing all assignments</p>
      </div>

      <div className="p-6">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr>
                <th className="px-4 py-2 text-left text-sm font-medium text-gray-500 border-b">Day / Slot</th>
                {slots.map(slot => (
                  <th key={slot} className="px-4 py-2 text-center text-sm font-medium text-gray-500 border-b min-w-[150px]">
                    Slot {slot}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {days.map(day => (
                <tr key={day} className="border-b">
                  <td className="px-4 py-3 font-medium text-gray-900 capitalize bg-gray-50 border-r">
                    {day}
                  </td>
                  {slots.map(slot => (
                    <td key={`${day}-${slot}`} className="px-2 py-2 border-r">
                      <div className="min-h-[100px] border-2 border-solid border-gray-200 rounded-lg p-2 space-y-1">
                        {getAssignmentsForSlot(day, slot).map((assignment, index) => {
                          const taColorClass = getTAColor(assignment.ta_id);

                          return (
                            <div
                              key={index}
                              className={`relative rounded p-2 text-xs border ${taColorClass}`}
                            >
                              <div className="font-medium">
                                {assignment.slot_type === 'tutorial' && assignment.tutorial_number != null
                                  ? `T${assignment.tutorial_number}`
                                  : assignment.slot_type === 'lab' && assignment.lab_number != null
                                  ? `L${assignment.lab_number}`
                                  : assignment.slot_type === 'tutorial' ? 'Tutorial' : 'Lab'}
                              </div>
                              <div className="text-xs opacity-90">
                                {assignment.slot_type === 'tutorial' ? 'Tutorial' : 'Lab'}
                              </div>
                              <div className="font-semibold text-xs mt-1">
                                {getTAName(assignment.ta_id)}
                              </div>
                              {assignment.course && (
                                <div className="text-xs opacity-75 mt-1">
                                  {assignment.course.code}
                                </div>
                              )}
                            </div>
                          );
                        })}
                        {getAssignmentsForSlot(day, slot).length === 0 && (
                          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                            Empty
                          </div>
                        )}
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ScheduleGrid;