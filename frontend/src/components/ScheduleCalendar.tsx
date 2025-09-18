import React, { useState, useCallback, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from 'react-beautiful-dnd';
import {
  DayEnum,
  SlotTypeEnum,
  ScheduleAssignment,
  Schedule,
  ConflictInfo,
  SchedulingPolicies
} from '../types';
import {
  ExclamationTriangleIcon,
  ClockIcon,
  UserIcon,
  BookOpenIcon
} from '@heroicons/react/24/outline';

interface ScheduleCalendarProps {
  schedule: Schedule;
  onAssignmentSwap: (sourceId: string, destinationId: string) => Promise<boolean>;
  onValidateSwap?: (sourceId: string, destinationId: string) => Promise<ConflictInfo[]>;
  isEditable?: boolean;
}

interface CalendarCell {
  id: string;
  day: DayEnum;
  slot_number: number;
  assignments: ScheduleAssignment[];
  conflicts: ConflictInfo[];
}

interface AssignmentDragItem {
  id: string;
  assignment: ScheduleAssignment;
  sourceCell: string;
}

const DAYS = [
  DayEnum.SATURDAY,
  DayEnum.SUNDAY,
  DayEnum.MONDAY,
  DayEnum.TUESDAY,
  DayEnum.WEDNESDAY,
  DayEnum.THURSDAY
];

const SLOTS = [1, 2, 3, 4, 5];

const ScheduleCalendar: React.FC<ScheduleCalendarProps> = ({
  schedule,
  onAssignmentSwap,
  onValidateSwap,
  isEditable = true
}) => {
  const [calendarData, setCalendarData] = useState<CalendarCell[][]>([]);
  const [draggedItem, setDraggedItem] = useState<AssignmentDragItem | null>(null);
  const [previewConflicts, setPreviewConflicts] = useState<ConflictInfo[]>([]);
  const [isValidating, setIsValidating] = useState(false);

  // Initialize calendar grid
  useEffect(() => {
    const grid: CalendarCell[][] = [];

    for (let slot = 1; slot <= 5; slot++) {
      const row: CalendarCell[] = [];
      for (const day of DAYS) {
        const cellId = `${day}-${slot}`;
        const assignments = schedule.assignments.filter(
          a => a.time_slot.day === day && a.time_slot.slot_number === slot
        );

        row.push({
          id: cellId,
          day,
          slot_number: slot,
          assignments,
          conflicts: []
        });
      }
      grid.push(row);
    }

    setCalendarData(grid);
  }, [schedule]);

  // Validate swap during drag preview
  const handleDragUpdate = useCallback(async (dragUpdate: any) => {
    if (!onValidateSwap || !dragUpdate.destination) {
      setPreviewConflicts([]);
      return;
    }

    const sourceId = dragUpdate.draggableId;
    const destinationId = dragUpdate.destination.droppableId;

    if (sourceId === destinationId) {
      setPreviewConflicts([]);
      return;
    }

    setIsValidating(true);
    try {
      const conflicts = await onValidateSwap(sourceId, destinationId);
      setPreviewConflicts(conflicts);
    } catch (error) {
      console.error('Error validating swap:', error);
      setPreviewConflicts([]);
    } finally {
      setIsValidating(false);
    }
  }, [onValidateSwap]);

  // Handle drag end
  const handleDragEnd = useCallback(async (result: DropResult) => {
    setPreviewConflicts([]);
    setDraggedItem(null);

    if (!result.destination || result.source.droppableId === result.destination.droppableId) {
      return;
    }

    const sourceId = result.draggableId;
    const destinationId = result.destination.droppableId;

    try {
      const success = await onAssignmentSwap(sourceId, destinationId);
      if (!success) {
        // Revert UI if swap failed
        console.error('Swap failed');
      }
    } catch (error) {
      console.error('Error performing swap:', error);
    }
  }, [onAssignmentSwap]);

  // Format time slot display
  const formatTimeSlot = (slot: number): string => {
    const startTime = 8 + (slot - 1) * 2; // 8 AM start, 2-hour slots
    const endTime = startTime + 2;
    return `${startTime}:00 - ${endTime}:00`;
  };

  // Get slot type badge color
  const getSlotTypeBadge = (type: SlotTypeEnum): string => {
    return type === SlotTypeEnum.TUTORIAL
      ? 'bg-blue-100 text-blue-800 border-blue-200'
      : 'bg-green-100 text-green-800 border-green-200';
  };

  // Render assignment card
  const renderAssignment = (assignment: ScheduleAssignment, index: number, cellId: string) => {
    const dragId = `${assignment.id}`;

    return (
      <Draggable
        key={dragId}
        draggableId={dragId}
        index={index}
        isDragDisabled={!isEditable}
      >
        {(provided, snapshot) => (
          <div
            ref={provided.innerRef}
            {...provided.draggableProps}
            {...provided.dragHandleProps}
            className={`
              p-3 mb-2 bg-white rounded-lg border shadow-sm transition-all duration-200
              ${snapshot.isDragging ? 'shadow-lg ring-2 ring-blue-300 bg-blue-50' : 'hover:shadow-md'}
              ${isEditable ? 'cursor-grab active:cursor-grabbing' : 'cursor-default'}
            `}
          >
            <div className="flex items-start justify-between mb-2">
              <span className={`
                inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border
                ${getSlotTypeBadge(assignment.time_slot.slot_type)}
              `}>
                {assignment.time_slot.slot_type.toUpperCase()}
              </span>
              <span className="text-xs text-gray-500">
                {assignment.time_slot.duration}h
              </span>
            </div>

            <div className="space-y-1">
              <div className="flex items-center text-sm font-medium text-gray-900">
                <BookOpenIcon className="h-4 w-4 mr-1 text-gray-400" />
                {assignment.course.code}
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <UserIcon className="h-4 w-4 mr-1 text-gray-400" />
                {assignment.ta.name}
              </div>
            </div>
          </div>
        )}
      </Draggable>
    );
  };

  // Render calendar cell
  const renderCalendarCell = (cell: CalendarCell, dayIndex: number, slotIndex: number) => {
    const isHighlighted = previewConflicts.length > 0 &&
      previewConflicts.some(c => c.slot?.includes(`${cell.day}`));

    return (
      <Droppable
        key={cell.id}
        droppableId={cell.id}
        isDropDisabled={!isEditable}
      >
        {(provided, snapshot) => (
          <div
            ref={provided.innerRef}
            {...provided.droppableProps}
            className={`
              min-h-[120px] p-2 border border-gray-200 transition-colors duration-200
              ${snapshot.isDraggingOver ? 'bg-blue-50 border-blue-300' : 'bg-gray-50'}
              ${isHighlighted ? 'bg-yellow-50 border-yellow-300' : ''}
              ${cell.conflicts.length > 0 ? 'bg-red-50 border-red-300' : ''}
            `}
          >
            {/* Cell conflicts indicator */}
            {cell.conflicts.length > 0 && (
              <div className="flex items-center mb-2 text-red-600">
                <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                <span className="text-xs font-medium">
                  {cell.conflicts.length} conflict{cell.conflicts.length !== 1 ? 's' : ''}
                </span>
              </div>
            )}

            {/* Assignment cards */}
            <div className="space-y-1">
              {cell.assignments.map((assignment, index) =>
                renderAssignment(assignment, index, cell.id)
              )}
            </div>

            {/* Drop zone placeholder */}
            {provided.placeholder}

            {/* Empty cell message */}
            {cell.assignments.length === 0 && (
              <div className="flex items-center justify-center h-16 text-gray-400 text-sm">
                {isEditable ? 'Drop assignment here' : 'No assignments'}
              </div>
            )}
          </div>
        )}
      </Droppable>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Calendar header */}
      <div className="p-4 border-b bg-gray-50">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Schedule: {schedule.name}
          </h3>
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <div className="flex items-center">
              <ClockIcon className="h-4 w-4 mr-1" />
              {schedule.assignments.length} assignments
            </div>
            {isValidating && (
              <div className="flex items-center text-blue-600">
                <div className="animate-spin h-4 w-4 border-2 border-blue-300 border-t-blue-600 rounded-full mr-1"></div>
                Validating...
              </div>
            )}
          </div>
        </div>

        {/* Preview conflicts */}
        {previewConflicts.length > 0 && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <div className="flex items-start">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 mr-2 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-yellow-800">
                  Potential conflicts detected:
                </h4>
                <ul className="mt-1 text-sm text-yellow-700 space-y-1">
                  {previewConflicts.map((conflict, index) => (
                    <li key={index}>• {conflict.message}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Calendar grid */}
      <DragDropContext
        onDragEnd={handleDragEnd}
        onDragUpdate={handleDragUpdate}
      >
        <div className="overflow-x-auto">
          <div className="min-w-[800px]">
            {/* Day headers */}
            <div className="grid grid-cols-7 bg-gray-100">
              <div className="p-3 font-medium text-gray-700 border-r border-gray-200">
                Time
              </div>
              {DAYS.map(day => (
                <div key={day} className="p-3 font-medium text-gray-700 text-center border-r border-gray-200 last:border-r-0">
                  {day.charAt(0).toUpperCase() + day.slice(1)}
                </div>
              ))}
            </div>

            {/* Calendar rows */}
            {SLOTS.map((slot, slotIndex) => (
              <div key={slot} className="grid grid-cols-7 border-b border-gray-200 last:border-b-0">
                {/* Time column */}
                <div className="p-3 bg-gray-50 border-r border-gray-200 flex flex-col justify-center">
                  <div className="font-medium text-gray-900">Slot {slot}</div>
                  <div className="text-sm text-gray-500">{formatTimeSlot(slot)}</div>
                </div>

                {/* Day columns */}
                {DAYS.map((day, dayIndex) => {
                  const cell = calendarData[slotIndex]?.[dayIndex];
                  return cell ? renderCalendarCell(cell, dayIndex, slotIndex) : null;
                })}
              </div>
            ))}
          </div>
        </div>
      </DragDropContext>

      {/* Legend */}
      <div className="p-4 border-t bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6 text-sm">
            <div className="flex items-center">
              <div className="w-4 h-4 bg-blue-100 border border-blue-200 rounded mr-2"></div>
              <span className="text-gray-600">Tutorial</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-green-100 border border-green-200 rounded mr-2"></div>
              <span className="text-gray-600">Lab</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-red-100 border border-red-200 rounded mr-2"></div>
              <span className="text-gray-600">Conflicts</span>
            </div>
          </div>
          {isEditable && (
            <div className="text-sm text-gray-500">
              Drag and drop assignments to reschedule
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScheduleCalendar;