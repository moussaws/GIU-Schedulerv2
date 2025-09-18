import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

const VisualScheduleBuilder = () => {
  const [courses, setCourses] = useState([]);
  const [tas, setTas] = useState([]);
  const [selectedCourses, setSelectedCourses] = useState([]);
  const [selectedTAs, setSelectedTAs] = useState([]);
  const [scheduleGrid, setScheduleGrid] = useState({});
  const [policies, setPolicies] = useState({
    tutorial_lab_independence: false,
    tutorial_lab_equal_count: true,
    tutorial_lab_number_matching: false,
    fairness_mode: true
  });
  const [loading, setLoading] = useState(false);
  const [schedule, setSchedule] = useState(null);
  const [showAddSlotDialog, setShowAddSlotDialog] = useState(false);
  const [selectedCell, setSelectedCell] = useState(null);
  const [selectedAssignment, setSelectedAssignment] = useState(null);
  const [workloadIssues, setWorkloadIssues] = useState([]);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [scheduleName, setScheduleName] = useState('');
  const [saving, setSaving] = useState(false);

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

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadSavedGrid();
  }, [selectedCourses]);

  const normalizeGridData = (gridData) => {
    const normalizedGrid = {};
    days.forEach(day => {
      normalizedGrid[day] = {};
      slots.forEach(slot => {
        if (gridData[day] && gridData[day][slot] && Array.isArray(gridData[day][slot])) {
          normalizedGrid[day][slot] = gridData[day][slot];
        } else {
          normalizedGrid[day][slot] = [];
        }
      });
    });
    return normalizedGrid;
  };

  const loadSavedGrid = async () => {
    console.log('loadSavedGrid called with selectedCourses:', selectedCourses);
    if (selectedCourses.length !== 1) {
      console.log('Not exactly 1 course selected, initializing empty grid');
      initializeGrid();
      return;
    }

    const courseId = selectedCourses[0];
    console.log('Loading grid for course ID:', courseId);
    try {
      const response = await api.get(`/courses/${courseId}/grid`);
      const gridData = response.data;
      console.log('Received grid data:', gridData);

      if (gridData.grid_data && Object.keys(gridData.grid_data).length > 0) {
        const normalizedGrid = normalizeGridData(gridData.grid_data);
        setScheduleGrid(normalizedGrid);
        console.log('✅ Loaded and normalized schedule grid from database for course:', courseId);
      } else {
        console.log('⚠️ Grid data empty, initializing new grid');
        initializeGrid();
      }

      if (gridData.selected_tas && gridData.selected_tas.length > 0) {
        setSelectedTAs(gridData.selected_tas);
        console.log('✅ Loaded saved selected TAs from database for course:', courseId, gridData.selected_tas);
      }

      if (gridData.policies) {
        setPolicies(gridData.policies);
        console.log('✅ Loaded saved policies from database for course:', courseId);
      }
    } catch (error) {
      if (error.response?.status === 404) {
        console.log('❌ No saved grid found for course:', courseId);
        initializeGrid();
      } else {
        console.error('❌ Error loading saved grid data:', error);
        toast.error('Failed to load saved grid data');
        initializeGrid();
      }
    }
  };

  const saveGrid = async () => {
    if (selectedCourses.length !== 1) {
      console.log('Cannot save grid: exactly one course must be selected');
      return;
    }

    const courseId = selectedCourses[0];
    try {
      const payload = {
        grid_data: scheduleGrid,
        selected_tas: selectedTAs,
        policies: policies
      };

      await api.post(`/courses/${courseId}/grid`, payload);
      console.log('Grid data saved to database for course:', courseId);
    } catch (error) {
      console.error('Error saving grid data:', error);
      toast.error('Failed to save grid data');
    }
  };

  const loadData = async () => {
    try {
      const [coursesRes, tasRes] = await Promise.all([
        api.get('/courses'),
        api.get('/tas')
      ]);
      setCourses(coursesRes.data);
      setTas(tasRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    }
  };

  const initializeGrid = () => {
    const grid = {};
    days.forEach(day => {
      grid[day] = {};
      slots.forEach(slot => {
        grid[day][slot] = [];
      });
    });
    setScheduleGrid(grid);
  };

  const getTAColor = (taId) => {
    const index = selectedTAs.indexOf(taId);
    if (index === -1) return taColors[0];
    return taColors[index % taColors.length];
  };

  const getTAName = (taId) => {
    const ta = tas.find(t => t.id === taId);
    return ta ? ta.name : `TA ${taId}`;
  };

  const getCourseName = (courseId) => {
    const course = courses.find(c => c.id === courseId);
    return course ? course.code : `Course ${courseId}`;
  };

  const getMaxTutorials = () => {
    if (selectedCourses.length === 0) return 0;
    const selectedCourseData = courses.filter(c => selectedCourses.includes(c.id));
    if (selectedCourseData.length === 0) return 0;
    return Math.max(...selectedCourseData.map(c => c.tutorials || 0));
  };

  const getMaxLabs = () => {
    if (selectedCourses.length === 0) return 0;
    const selectedCourseData = courses.filter(c => selectedCourses.includes(c.id));
    if (selectedCourseData.length === 0) return 0;
    return Math.max(...selectedCourseData.map(c => c.labs || 0));
  };

  // Helper functions to track used tutorial/lab numbers
  const getUsedTutorialNumbers = () => {
    const usedNumbers = new Set();
    days.forEach(day => {
      slots.forEach(slot => {
        const slotsInCell = scheduleGrid[day]?.[slot] || [];
        slotsInCell.forEach(slotData => {
          if (slotData.type === 'tutorial' && slotData.tutorial_number) {
            usedNumbers.add(slotData.tutorial_number);
          }
        });
      });
    });
    return Array.from(usedNumbers);
  };

  const getUsedLabNumbers = () => {
    const usedNumbers = new Set();
    days.forEach(day => {
      slots.forEach(slot => {
        const slotsInCell = scheduleGrid[day]?.[slot] || [];
        slotsInCell.forEach(slotData => {
          if (slotData.type === 'lab' && slotData.lab_number) {
            usedNumbers.add(slotData.lab_number);
          }
        });
      });
    });
    return Array.from(usedNumbers);
  };

  const getAvailableTutorialNumbers = () => {
    const maxTutorials = getMaxTutorials();
    const usedNumbers = getUsedTutorialNumbers();
    const availableNumbers = [];

    for (let i = 1; i <= maxTutorials; i++) {
      if (!usedNumbers.includes(i)) {
        availableNumbers.push(i);
      }
    }
    return availableNumbers;
  };

  const getAvailableLabNumbers = () => {
    const maxLabs = getMaxLabs();
    const usedNumbers = getUsedLabNumbers();
    const availableNumbers = [];

    for (let i = 1; i <= maxLabs; i++) {
      if (!usedNumbers.includes(i)) {
        availableNumbers.push(i);
      }
    }
    return availableNumbers;
  };

  const handleCellClick = (day, slot) => {
    if (selectedCourses.length === 0) {
      toast.error('Please select courses first');
      return;
    }
    setSelectedCell({ day, slot });
    setShowAddSlotDialog(true);
  };

  const addSlotToCell = (slotData) => {
    if (!selectedCell) return;

    const { day, slot } = selectedCell;
    setScheduleGrid(prev => {
      const newGrid = {
        ...prev,
        [day]: {
          ...prev[day],
          [slot]: [...prev[day][slot], { ...slotData, id: Date.now(), manual: true }]
        }
      };
      return newGrid;
    });
    setShowAddSlotDialog(false);
    setSelectedCell(null);
  };

  const removeSlotFromCell = (day, slot, slotId) => {
    setScheduleGrid(prev => {
      const newGrid = {
        ...prev,
        [day]: {
          ...prev[day],
          [slot]: prev[day][slot].filter(s => s.id !== slotId)
        }
      };
      return newGrid;
    });
  };

  const calculateTAWorkload = (taId, currentSchedule = schedule) => {
    if (!currentSchedule?.assignments) return 0;
    return currentSchedule.assignments
      .filter(assignment => tas.find(t => t.name === assignment.ta_name)?.id === taId)
      .reduce((total, assignment) => total + (assignment.duration || 2), 0);
  };

  const checkConstraintViolations = (taId, day, slot, assignmentType) => {
    const ta = tas.find(t => t.id === taId);
    if (!ta) return ['TA not found'];

    const violations = [];

    if (ta.blocked_slots?.some(blocked =>
      blocked.day === day && blocked.slot_number === slot
    )) {
      violations.push('TA has blocked this time slot');
    }

    if (ta.day_off === day) {
      violations.push('TA has this day off');
    }

    // Check for time slot conflicts in the schedule
    const conflictingAssignments = schedule?.assignments?.filter(assignment =>
      tas.find(t => t.name === assignment.ta_name)?.id === taId &&
      assignment.day === day &&
      assignment.slot_number === slot
    ) || [];

    if (conflictingAssignments.length > 0) {
      violations.push('TA already has assignment in this time slot');
    }

    // Also check visual grid for conflicts
    if (scheduleGrid[day] && scheduleGrid[day][slot]) {
      const gridConflicts = scheduleGrid[day][slot].filter(gridAssignment =>
        gridAssignment.ta_name === ta.name
      );
      if (gridConflicts.length > 0) {
        violations.push('TA already assigned in this time slot (grid)');
      }
    }

    const currentWorkload = calculateTAWorkload(taId);
    if (currentWorkload >= 20) {
      violations.push('TA would exceed maximum weekly hours (20h)');
    }

    const dailyAssignments = schedule?.assignments?.filter(assignment =>
      tas.find(t => t.name === assignment.ta_name)?.id === taId && assignment.day === day
    ) || [];

    const dailyHours = dailyAssignments.reduce((total, assignment) =>
      total + (assignment.duration || 2), 0
    );

    if (dailyHours + 2 > 4) {
      violations.push('TA would exceed daily limit (4h)');
    }

    return violations;
  };

  const scoreAssignmentOption = (taId, day, slot, assignmentType, currentAssignment = null) => {
    const violations = checkConstraintViolations(taId, day, slot, assignmentType);
    if (violations.length > 0) return { score: 0, violations };

    let score = 100;
    const ta = tas.find(t => t.id === taId);
    const currentWorkload = calculateTAWorkload(taId);

    score -= Math.abs(currentWorkload - 10) * 2;

    if (ta?.skills?.includes(assignmentType)) score += 10;

    if (ta?.premasters && assignmentType === 'tutorial') score += 5;

    const dayIndex = days.indexOf(day);
    const slotIndex = slots.indexOf(slot);
    if (dayIndex < 2 || slotIndex === 0) score -= 5;

    const existingAssignments = schedule?.assignments?.filter(assignment =>
      tas.find(t => t.name === assignment.ta_name)?.id === taId
    ) || [];

    const hasNearbyAssignments = existingAssignments.some(assignment => {
      const assignmentDayIndex = days.indexOf(assignment.day);
      const assignmentSlotIndex = slots.indexOf(assignment.slot_number);
      return Math.abs(assignmentDayIndex - dayIndex) <= 1 &&
             Math.abs(assignmentSlotIndex - slotIndex) <= 1;
    });

    if (hasNearbyAssignments) score += 15;

    return { score, violations: [] };
  };

  const findBestSwapSuggestions = (targetAssignment, reason = 'general') => {
    const suggestions = [];

    selectedTAs.forEach(taId => {
      const ta = tas.find(t => t.id === taId);
      if (!ta || ta.name === targetAssignment.ta_name) return;

      const evaluation = scoreAssignmentOption(
        taId,
        targetAssignment.day,
        targetAssignment.slot_number,
        targetAssignment.slot_type
      );

      if (evaluation.score > 0) {
        suggestions.push({
          ta: ta,
          score: evaluation.score,
          violations: evaluation.violations,
          reason: reason,
          benefits: generateSwapBenefits(targetAssignment, ta, evaluation.score),
          originalTA: targetAssignment.ta_name
        });
      }
    });

    return suggestions
      .sort((a, b) => b.score - a.score)
      .slice(0, 3);
  };

  const generateSwapBenefits = (assignment, newTA, score) => {
    const benefits = [];
    const originalTA = tas.find(t => t.name === assignment.ta_name);
    const originalWorkload = calculateTAWorkload(originalTA?.id);
    const newWorkload = calculateTAWorkload(newTA.id);

    if (originalWorkload > newWorkload + 2) {
      benefits.push('Better workload balance');
    }

    if (newTA.skills?.includes(assignment.slot_type)) {
      benefits.push(`${newTA.name} specializes in ${assignment.slot_type}s`);
    }

    if (score > 80) {
      benefits.push('Excellent fit based on constraints');
    } else if (score > 60) {
      benefits.push('Good fit with minor optimizations');
    }

    if (newTA.premasters && assignment.slot_type === 'tutorial') {
      benefits.push('Pre-masters student ideal for tutorials');
    }

    return benefits.length > 0 ? benefits : ['Alternative assignment option'];
  };

  const findWorkloadIssues = () => {
    const issues = [];
    const workloads = {};

    selectedTAs.forEach(taId => {
      const ta = tas.find(t => t.id === taId);
      if (!ta) return;

      const workload = calculateTAWorkload(taId);
      workloads[taId] = { ta, workload };

      if (workload > 16) {
        issues.push({
          type: 'overloaded',
          ta: ta,
          workload: workload,
          suggestions: findOverloadSolutions(taId)
        });
      } else if (workload < 6) {
        issues.push({
          type: 'underutilized',
          ta: ta,
          workload: workload,
          suggestions: findUnderutilizedSolutions(taId)
        });
      }
    });

    const avgWorkload = Object.values(workloads).reduce((sum, { workload }) => sum + workload, 0) / Object.keys(workloads).length;
    const imbalanced = Object.values(workloads).filter(({ workload }) => Math.abs(workload - avgWorkload) > 4);

    if (imbalanced.length > 0) {
      issues.push({
        type: 'imbalanced',
        message: 'Significant workload imbalance detected',
        suggestions: findBalancingSuggestions(workloads, avgWorkload)
      });
    }

    return issues;
  };

  const findOverloadSolutions = (overloadedTAId) => {
    const assignments = schedule?.assignments?.filter(assignment =>
      tas.find(t => t.name === assignment.ta_name)?.id === overloadedTAId
    ) || [];

    return assignments
      .map(assignment => ({
        assignment,
        alternatives: findBestSwapSuggestions(assignment, 'reducing_overload')
      }))
      .filter(({ alternatives }) => alternatives.length > 0)
      .slice(0, 2);
  };

  const findUnderutilizedSolutions = (underutilizedTAId) => {
    const ta = tas.find(t => t.id === underutilizedTAId);
    const opportunities = [];

    schedule?.assignments?.forEach(assignment => {
      const currentTA = tas.find(t => t.name === assignment.ta_name);
      if (!currentTA || currentTA.id === underutilizedTAId) return;

      const evaluation = scoreAssignmentOption(
        underutilizedTAId,
        assignment.day,
        assignment.slot_number,
        assignment.slot_type
      );

      if (evaluation.score > 70) {
        opportunities.push({
          assignment,
          score: evaluation.score,
          benefit: `Could take over from ${assignment.ta_name}`
        });
      }
    });

    return opportunities.slice(0, 3);
  };

  const findBalancingSuggestions = (workloads, avgWorkload) => {
    const suggestions = [];
    const overloaded = Object.values(workloads).filter(({ workload }) => workload > avgWorkload + 2);
    const underloaded = Object.values(workloads).filter(({ workload }) => workload < avgWorkload - 2);

    overloaded.forEach(({ ta: overloadedTA }) => {
      underloaded.forEach(({ ta: underloadedTA }) => {
        const swapOpportunities = schedule?.assignments?.filter(assignment =>
          assignment.ta_name === overloadedTA.name
        ).map(assignment => {
          const evaluation = scoreAssignmentOption(
            underloadedTA.id,
            assignment.day,
            assignment.slot_number,
            assignment.slot_type
          );

          if (evaluation.score > 60) {
            return {
              from: overloadedTA.name,
              to: underloadedTA.name,
              assignment: assignment,
              score: evaluation.score
            };
          }
          return null;
        }).filter(Boolean);

        if (swapOpportunities.length > 0) {
          suggestions.push({
            type: 'balance_swap',
            opportunities: swapOpportunities.slice(0, 2)
          });
        }
      });
    });

    return suggestions.slice(0, 3);
  };

  const handleAssignmentClick = (assignment) => {
    // Automatically enable swap mode when an assignment is clicked
    // This replaces the old suggestion system with direct swap functionality
    console.log('Assignment clicked, enabling swap mode for:', assignment);
  };

  const handleSwapApproval = (suggestion) => {
    const updatedSchedule = {
      ...schedule,
      assignments: schedule.assignments.map(assignment => {
        if (assignment === selectedAssignment) {
          return {
            ...assignment,
            ta_name: suggestion.ta.name
          };
        }
        return assignment;
      })
    };

    setSchedule(updatedSchedule);
    syncScheduleToGrid(updatedSchedule);

    setSelectedAssignment(null);
    toast.success(`Assignment swapped to ${suggestion.ta.name}`);
  };

  const analyzeWorkload = () => {
    const issues = findWorkloadIssues();
    setWorkloadIssues(issues);
    if (issues.length === 0) {
      toast.success('No workload issues detected - schedule looks balanced!');
    } else {
      toast('⚠️ Workload analysis complete - see suggestions below', {
        icon: '📊'
      });
    }
  };

  const autoOptimizeSchedule = () => {
    const issues = findWorkloadIssues();
    let optimizations = 0;
    const scheduledOptimizations = [];

    issues.forEach(issue => {
      if (issue.type === 'overloaded' && issue.suggestions.length > 0) {
        const bestSuggestion = issue.suggestions[0];
        if (bestSuggestion.alternatives.length > 0) {
          const bestAlternative = bestSuggestion.alternatives[0];

          scheduledOptimizations.push({
            originalAssignment: bestSuggestion.assignment,
            newTA: bestAlternative.ta
          });
          optimizations++;
        }
      }
    });

    if (optimizations > 0) {
      // Update schedule
      const updatedSchedule = {
        ...schedule,
        assignments: schedule.assignments.map(assignment => {
          const optimization = scheduledOptimizations.find(opt => opt.originalAssignment === assignment);
          if (optimization) {
            return {
              ...assignment,
              ta_name: optimization.newTA.name
            };
          }
          return assignment;
        })
      };

      setSchedule(updatedSchedule);
      syncScheduleToGrid(updatedSchedule);

      toast.success(`Applied ${optimizations} automatic optimizations`);
      setWorkloadIssues([]);
    } else {
      toast('No automatic optimizations available', { icon: '🤖' });
    }
  };

  const handleCourseToggle = (courseId) => {
    setSelectedCourses(prev => {
      const newSelection = prev.includes(courseId)
        ? prev.filter(id => id !== courseId)
        : [...prev, courseId];
      return newSelection;
    });
  };

  const handleTAToggle = (taId) => {
    setSelectedTAs(prev => {
      const newSelection = prev.includes(taId)
        ? prev.filter(id => id !== taId)
        : [...prev, taId];
      return newSelection;
    });
  };

  const handlePolicyToggle = (policyKey) => {
    setPolicies(prev => ({
      ...prev,
      [policyKey]: !prev[policyKey]
    }));
  };

  const convertGridToTimeSlots = () => {
    const timeSlots = [];
    days.forEach(day => {
      slots.forEach(slot => {
        const slotsInCell = scheduleGrid[day][slot];
        slotsInCell.forEach(slotData => {
          timeSlots.push({
            day: day,
            slot: slot,
            type: slotData.type || slotData.slot_type, // Support both manual (type) and generated (slot_type) formats
            tutorial_number: slotData.tutorial_number || null,
            lab_number: slotData.lab_number || null
          });
        });
      });
    });
    return timeSlots;
  };

  const syncScheduleToGrid = (scheduleData) => {
    // Simple approach: Replace the entire grid with generated assignments
    // This fixes the duplicate slot issue by starting fresh
    console.log('🔄 Syncing schedule to grid (clean replacement)');
    console.log('New assignments to sync:', scheduleData.assignments);

    const newGrid = {};
    days.forEach(day => {
      newGrid[day] = {};
      slots.forEach(slot => {
        newGrid[day][slot] = [];
      });
    });

    if (scheduleData.assignments) {
      scheduleData.assignments.forEach(assignment => {
        const day = assignment.day.toLowerCase();
        const slot = assignment.slot_number;
        if (newGrid[day] && newGrid[day][slot]) {
          newGrid[day][slot].push({
            id: `${assignment.ta_name}-${day}-${slot}-${assignment.slot_type}`,
            ta_name: assignment.ta_name,
            slot_type: assignment.slot_type,
            tutorial_number: assignment.tutorial_number,
            lab_number: assignment.lab_number,
            duration: assignment.duration || 2
          });
        }
      });
    }

    setScheduleGrid(newGrid);
  };

  const generateSchedule = async () => {
    if (selectedCourses.length === 0) {
      toast.error('Please select at least one course');
      return;
    }
    if (selectedTAs.length === 0) {
      toast.error('Please select at least one TA');
      return;
    }

    const timeSlots = convertGridToTimeSlots();
    if (timeSlots.length === 0) {
      toast.error('Please add some time slots to the schedule grid');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        course_ids: selectedCourses,
        ta_ids: selectedTAs,
        time_slots: timeSlots,
        policies: policies
      };

      const response = await api.post('/generate-schedule', payload);
      setSchedule(response.data);

      // Sync the schedule assignments to the visual grid
      syncScheduleToGrid(response.data);

      if (response.data.success) {
        toast.success('Schedule generated successfully!');
      } else {
        toast('Schedule generated with some issues. Check the results below.', { icon: '⚠️' });
      }
    } catch (error) {
      toast.error('Failed to generate schedule');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const clearGrid = async () => {
    if (selectedCourses.length === 1) {
      const courseId = selectedCourses[0];
      try {
        await api.delete(`/courses/${courseId}/grid`);
        console.log('Cleared grid data from database for course:', courseId);
      } catch (error) {
        console.error('Error clearing grid data from database:', error);
      }
    }

    initializeGrid();
    setSelectedCourses([]);
    setSelectedTAs([]);
    toast.success('Course schedule cleared');
  };

  const manualSave = async () => {
    if (selectedCourses.length !== 1) {
      toast.error('Please select exactly one course to save the schedule');
      return;
    }

    await saveGrid();
    toast.success('Course schedule saved successfully!');
  };

  const handleSaveSchedule = async () => {
    if (!scheduleName.trim()) {
      toast.error('Please enter a schedule name');
      return;
    }

    setSaving(true);
    try {
      // Save the schedule to the database
      const response = await api.post('/schedules', {
        name: scheduleName,
        description: `Generated schedule for ${selectedCourses.length} course(s)`,
        assignments: schedule.assignments,
        success: schedule.success,
        message: schedule.message,
        statistics: schedule.statistics,
        policies_used: policies
      });

      if (response.data) {
        toast.success('Schedule saved successfully!');
        setShowSaveModal(false);
        setScheduleName('');
      }
    } catch (error) {
      console.error('Error saving schedule:', error);
      toast.error('Failed to save schedule');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">📅 Visual Schedule Builder</h1>
        <div className="flex space-x-3">
          <button
            onClick={manualSave}
            className="bg-green-500 hover:bg-green-600 text-white font-medium py-2 px-4 rounded-lg flex items-center space-x-2"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span>Save Course Schedule</span>
          </button>
          <button
            onClick={clearGrid}
            className="bg-gray-500 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-lg"
          >
            Clear Grid
          </button>
          <button
            onClick={generateSchedule}
            disabled={loading || selectedCourses.length === 0 || selectedTAs.length === 0}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium py-2 px-4 rounded-lg flex items-center space-x-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Generating...</span>
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>Generate Schedule</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Course, TA Selection and Policies */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-lg font-semibold mb-4">Select Courses</h2>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {courses?.map(course => (
              <label key={course.id} className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={selectedCourses.includes(course.id)}
                  onChange={() => handleCourseToggle(course.id)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="font-medium">{course.code}</div>
                  <div className="text-sm text-gray-500">{course.name} ({course.tutorials || 0}T + {course.labs || 0}L)</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-lg font-semibold mb-4">Select TAs</h2>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {tas?.map((ta, index) => (
              <label key={ta.id} className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={selectedTAs.includes(ta.id)}
                  onChange={() => handleTAToggle(ta.id)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <div className="flex items-center space-x-2">
                  <div className={`w-4 h-4 rounded ${getTAColor(ta.id)?.split(' ')[0] || 'bg-gray-100'}`}></div>
                  <div>
                    <div className="font-medium">{ta.name}</div>
                    <div className="text-sm text-gray-500">
                      {ta.total_allocated_hours || 0}h/week
                      {ta.premasters && <span className="text-purple-600 ml-1">(Premasters)</span>}
                    </div>
                  </div>
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-lg font-semibold mb-4">📋 Scheduling Policies</h2>
          <div className="space-y-3">
            <label className="flex items-start space-x-3">
              <input
                type="checkbox"
                checked={policies.tutorial_lab_independence}
                onChange={() => handlePolicyToggle('tutorial_lab_independence')}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mt-1"
              />
              <div>
                <div className="font-medium text-sm">Tutorial-Lab Independence</div>
                <div className="text-xs text-gray-500">TAs cannot teach both tutorials and labs</div>
              </div>
            </label>

            <label className="flex items-start space-x-3">
              <input
                type="checkbox"
                checked={policies.tutorial_lab_equal_count}
                onChange={() => handlePolicyToggle('tutorial_lab_equal_count')}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mt-1"
              />
              <div>
                <div className="font-medium text-sm">Equal Tutorial-Lab Count</div>
                <div className="text-xs text-gray-500">Balance tutorial and lab assignments equally</div>
              </div>
            </label>

            <label className="flex items-start space-x-3">
              <input
                type="checkbox"
                checked={policies.tutorial_lab_number_matching}
                onChange={() => handlePolicyToggle('tutorial_lab_number_matching')}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mt-1"
              />
              <div>
                <div className="font-medium text-sm">Tutorial-Lab Number Matching</div>
                <div className="text-xs text-gray-500">Match T1 with L1, T2 with L2, etc.</div>
              </div>
            </label>

            <label className="flex items-start space-x-3">
              <input
                type="checkbox"
                checked={policies.fairness_mode}
                onChange={() => handlePolicyToggle('fairness_mode')}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mt-1"
              />
              <div>
                <div className="font-medium text-sm">⚖️ Fairness Mode</div>
                <div className="text-xs text-gray-500">Distribute workload evenly among TAs</div>
              </div>
            </label>

            <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 mt-4">
              <div className="text-sm font-medium text-orange-800 flex items-center">
                <svg className="h-4 w-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                Premasters Constraint
              </div>
              <div className="text-xs text-orange-700 mt-1">
                Premasters students can only work Saturday slots 1&2. Slots 3,4,5 blocked for lectures.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Schedule Grid */}
      <div className="bg-white rounded-lg shadow border overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Weekly Schedule Grid</h2>
          <p className="text-sm text-gray-600 mt-1">Click on any cell to add tutorial/lab slots. Multiple slots can be added to the same cell for parallel sessions.</p>
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
                        <div
                          onClick={() => handleCellClick(day, slot)}
                          className="min-h-[100px] border-2 border-dashed border-gray-300 rounded-lg p-2 cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors space-y-1"
                        >
                          {scheduleGrid[day]?.[slot]?.map(slotData => (
                            <div
                              key={slotData.id}
                              className="relative bg-blue-100 border border-blue-300 rounded p-2 text-xs group"
                            >
                              <div className="font-medium text-blue-800">
                                {(slotData.type === 'tutorial' || slotData.slot_type === 'tutorial') ? (slotData.tutorial_number != null ? `T${slotData.tutorial_number}` : 'Tutorial') : (slotData.lab_number != null ? `L${slotData.lab_number}` : 'Lab')}
                              </div>
                              <div className="text-blue-600">
                                {(slotData.type === 'tutorial' || slotData.slot_type === 'tutorial') ? 'Tutorial' : 'Lab'}
                              </div>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  removeSlotFromCell(day, slot, slotData.id);
                                }}
                                className="absolute top-0 right-0 -mt-1 -mr-1 bg-red-500 text-white rounded-full w-4 h-4 text-xs opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                              >
                                ×
                              </button>
                            </div>
                          ))}
                          {(!scheduleGrid[day]?.[slot] || scheduleGrid[day][slot].length === 0) && (
                            <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                              Click to add
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

      {/* Add Slot Dialog */}
      {showAddSlotDialog && selectedCell && (
        <AddSlotDialog
          selectedCell={selectedCell}
          courses={courses.filter(c => selectedCourses.includes(c.id))}
          availableTutorialNumbers={getAvailableTutorialNumbers()}
          availableLabNumbers={getAvailableLabNumbers()}
          onAddSlot={addSlotToCell}
          onClose={() => {
            setShowAddSlotDialog(false);
            setSelectedCell(null);
          }}
        />
      )}

      {/* Schedule Results */}
      {schedule && (
        <>
          <ScheduleResults
            schedule={schedule}
            tas={tas}
            getTAColor={getTAColor}
            scheduleGrid={scheduleGrid}
            policies={policies}
            onManualSwap={(updatedSchedule) => {
              setSchedule(updatedSchedule);
              // Note: Don't call syncScheduleToGrid here since executeSwap already updates the visual grid
            }}
            setScheduleGrid={setScheduleGrid}
            onSaveSchedule={() => setShowSaveModal(true)}
          />


        </>
      )}

      {/* Save Schedule Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold mb-4">Save Schedule</h3>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Schedule Name
              </label>
              <input
                type="text"
                value={scheduleName}
                onChange={(e) => setScheduleName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter schedule name..."
                autoFocus
              />
            </div>

            <div className="flex space-x-3">
              <button
                onClick={handleSaveSchedule}
                disabled={saving || !scheduleName.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-lg flex-1"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button
                onClick={() => {
                  setShowSaveModal(false);
                  setScheduleName('');
                }}
                className="bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-2 px-4 rounded-lg"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Add Slot Dialog Component
const AddSlotDialog = ({ selectedCell, courses, availableTutorialNumbers, availableLabNumbers, onAddSlot, onClose }) => {
  const [slotType, setSlotType] = useState('tutorial');
  const [tutorialNumber, setTutorialNumber] = useState(availableTutorialNumbers[0] || 1);
  const [labNumber, setLabNumber] = useState(availableLabNumbers[0] || 1);

  const handleAdd = () => {
    const slotData = {
      type: slotType,
      tutorial_number: slotType === 'tutorial' ? tutorialNumber : null,
      lab_number: slotType === 'lab' ? labNumber : null
    };
    onAddSlot(slotData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96">
        <h3 className="text-lg font-semibold mb-4">
          Add Slot to {selectedCell.day.charAt(0).toUpperCase() + selectedCell.day.slice(1)} - Slot {selectedCell.slot}
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
            <select
              value={slotType}
              onChange={(e) => setSlotType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="tutorial">Tutorial</option>
              <option value="lab">Lab</option>
            </select>
          </div>

          {slotType === 'tutorial' && availableTutorialNumbers.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Tutorial Number</label>
              <select
                value={tutorialNumber}
                onChange={(e) => setTutorialNumber(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              >
                {availableTutorialNumbers.map((num) => (
                  <option key={num} value={num}>T{num}</option>
                ))}
              </select>
            </div>
          )}

          {slotType === 'tutorial' && availableTutorialNumbers.length === 0 && (
            <div className="text-sm text-orange-600 bg-orange-50 p-3 rounded-lg">
              ⚠️ All tutorial numbers are already in use
            </div>
          )}

          {slotType === 'lab' && availableLabNumbers.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Lab Number</label>
              <select
                value={labNumber}
                onChange={(e) => setLabNumber(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              >
                {availableLabNumbers.map((num) => (
                  <option key={num} value={num}>L{num}</option>
                ))}
              </select>
            </div>
          )}

          {slotType === 'lab' && availableLabNumbers.length === 0 && (
            <div className="text-sm text-orange-600 bg-orange-50 p-3 rounded-lg">
              ⚠️ All lab numbers are already in use
            </div>
          )}
        </div>

        <div className="flex space-x-3 mt-6">
          <button
            onClick={handleAdd}
            disabled={(slotType === 'tutorial' && availableTutorialNumbers.length === 0) ||
                     (slotType === 'lab' && availableLabNumbers.length === 0)}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-lg flex-1"
          >
            Add Slot
          </button>
          <button
            onClick={onClose}
            className="bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-2 px-4 rounded-lg"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

// Schedule Results Component
const ScheduleResults = ({ schedule, tas, getTAColor, scheduleGrid, policies, onManualSwap, setScheduleGrid, onSaveSchedule }) => {
  const days = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday'];
  const slots = [1, 2, 3, 4, 5];
  const [swapMode, setSwapMode] = useState(false);
  const [selectedForSwap, setSelectedForSwap] = useState(null);
  const [swapCandidates, setSwapCandidates] = useState([]);

  const getTAById = (taName) => {
    return tas.find(t => t.name === taName);
  };

  // Use the scheduleGrid passed from parent component
  const scheduleDisplayGrid = scheduleGrid || {};

  // Check if TA is blocked during a specific slot
  const isSlotBlocked = (taName, day, slotNumber) => {
    const ta = getTAById(taName);
    if (!ta || !ta.blocked_slots || !day || slotNumber === undefined) return false;

    return ta.blocked_slots.some(blockedSlot =>
      blockedSlot.day && blockedSlot.day.toLowerCase() === day.toLowerCase() &&
      blockedSlot.slot_number === slotNumber
    );
  };

  // Check if TA has day off
  const hasDayOff = (taName, day) => {
    const ta = getTAById(taName);
    if (!ta || !ta.day_off || !day) return false;
    return ta.day_off.toLowerCase() === day.toLowerCase();
  };

  // Validate if swap is allowed based on constraints
  const validateSwap = (assignment1, assignment2) => {
    console.log(`🔍 Validating swap: ${assignment1.ta_name} (${assignment1.day} slot ${assignment1.slot_number}) <-> ${assignment2.ta_name} (${assignment2.day} slot ${assignment2.slot_number})`);

    // Basic validation - ensure we have valid assignment objects
    if (!assignment1 || !assignment2) return { valid: false, reason: 'Invalid assignment data' };
    if (!assignment1.ta_name || !assignment2.ta_name) return { valid: false, reason: 'Missing TA name' };
    if (!assignment1.day || !assignment2.day) return { valid: false, reason: 'Missing assignment day' };
    if (assignment1.slot_number === undefined || assignment2.slot_number === undefined) return { valid: false, reason: 'Missing slot number' };

    // Don't allow swapping assignment with itself
    if (assignment1.ta_name === assignment2.ta_name) {
      return { valid: false, reason: 'Cannot swap assignment with itself' };
    }

    // Try to find TA data - but be permissive if not found
    const ta1 = getTAById(assignment1.ta_name);
    const ta2 = getTAById(assignment2.ta_name);

    // Only check constraints if we have TA data - otherwise allow the swap
    // This makes the system more robust when TA data is incomplete

    // Check if ta1 would be blocked in assignment2's slot
    if (ta1 && isSlotBlocked(assignment1.ta_name, assignment2.day, assignment2.slot_number)) {
      return { valid: false, reason: `${assignment1.ta_name} is blocked during ${assignment2.day} slot ${assignment2.slot_number}` };
    }

    // Check if ta2 would be blocked in assignment1's slot
    if (ta2 && isSlotBlocked(assignment2.ta_name, assignment1.day, assignment1.slot_number)) {
      return { valid: false, reason: `${assignment2.ta_name} is blocked during ${assignment1.day} slot ${assignment1.slot_number}` };
    }

    // Check day off constraints
    if (ta1 && hasDayOff(assignment1.ta_name, assignment2.day)) {
      return { valid: false, reason: `${assignment1.ta_name} has day off on ${assignment2.day}` };
    }
    if (ta2 && hasDayOff(assignment2.ta_name, assignment1.day)) {
      return { valid: false, reason: `${assignment2.ta_name} has day off on ${assignment1.day}` };
    }

    // Check premasters constraints (Saturday slots 3,4,5 are blocked for premasters)
    if (ta1 && ta1.premasters && assignment2.day.toLowerCase() === 'saturday' && assignment2.slot_number > 2) {
      return { valid: false, reason: `${assignment1.ta_name} is premasters and cannot take Saturday slot ${assignment2.slot_number} (lectures conflict)` };
    }
    if (ta2 && ta2.premasters && assignment1.day.toLowerCase() === 'saturday' && assignment1.slot_number > 2) {
      return { valid: false, reason: `${assignment2.ta_name} is premasters and cannot take Saturday slot ${assignment1.slot_number} (lectures conflict)` };
    }

    // INTELLIGENT SWAP SIMULATION: Create post-swap state and validate it
    console.log('🧠 Running intelligent swap simulation...');

    if (!schedule || !schedule.assignments) {
      console.log('⚠️ No schedule data available for swap validation');
      return { valid: false, reason: 'No schedule data available' };
    }

    // Additional validation - ensure both assignments exist in the schedule
    const assignment1Exists = schedule.assignments.some(a => assignmentMatches(a, assignment1));
    const assignment2Exists = schedule.assignments.some(a => assignmentMatches(a, assignment2));

    if (!assignment1Exists || !assignment2Exists) {
      console.log('⚠️ One or both assignments not found in schedule');
      return { valid: false, reason: 'Assignment not found in current schedule' };
    }

    // Simulate the post-swap assignment state
    const simulatedAssignments = schedule.assignments.map(assignment => {
      // If this assignment matches assignment1, replace with assignment2's TA
      if (assignmentMatches(assignment, assignment1)) {
        return { ...assignment, ta_name: assignment2.ta_name };
      }
      // If this assignment matches assignment2, replace with assignment1's TA
      if (assignmentMatches(assignment, assignment2)) {
        return { ...assignment, ta_name: assignment1.ta_name };
      }
      // Otherwise keep assignment unchanged
      return assignment;
    });

    console.log(`📊 Simulated ${simulatedAssignments.length} assignments after swap`);

    // Validate the simulated post-swap state for conflicts
    const conflicts = [];
    const taSlotMap = {}; // Track what each TA is assigned to by slot type

    simulatedAssignments.forEach(assignment => {
      const key = `${assignment.ta_name}-${assignment.day.toLowerCase()}-${assignment.slot_number}-${assignment.slot_type}`;
      if (!taSlotMap[key]) {
        taSlotMap[key] = [];
      }
      taSlotMap[key].push(assignment);
    });

    // Check for parallel conflicts in the simulated state (multiple of same type at same time)
    Object.entries(taSlotMap).forEach(([key, assignments]) => {
      if (assignments.length > 1) {
        const [taName, day, slot, slotType] = key.split('-');

        if (slotType === 'tutorial') {
          const tutNumbers = assignments.map(t => t.tutorial_number).filter(n => n != null).join(', ');
          conflicts.push(`${taName} would have ${assignments.length} tutorials (${tutNumbers}) simultaneously at ${day} slot ${slot}`);
        } else if (slotType === 'lab') {
          const labNumbers = assignments.map(l => l.lab_number).filter(n => n != null).join(', ');
          conflicts.push(`${taName} would have ${assignments.length} labs (${labNumbers}) simultaneously at ${day} slot ${slot}`);
        }
      }
    });

    // Additional post-swap validation: Check day off constraints
    const postSwapViolations = [];

    // Group assignments by TA for day off validation
    const taAssignments = {};
    simulatedAssignments.forEach(assignment => {
      if (!taAssignments[assignment.ta_name]) {
        taAssignments[assignment.ta_name] = [];
      }
      taAssignments[assignment.ta_name].push(assignment);
    });

    // Check day off violations in post-swap state
    Object.entries(taAssignments).forEach(([taName, assignments]) => {
      const ta = tas.find(t => t.name === taName);
      if (ta && ta.day_off) {
        const dayOffViolations = assignments.filter(a => a.day.toLowerCase() === ta.day_off.toLowerCase());
        if (dayOffViolations.length > 0) {
          postSwapViolations.push(`${taName} would be assigned on their day off (${ta.day_off})`);
        }
      }

      // Check blocked slots in post-swap state
      if (ta && ta.blocked_slots && ta.blocked_slots.length > 0) {
        assignments.forEach(assignment => {
          const isBlocked = ta.blocked_slots.some(blocked =>
            blocked.day.toLowerCase() === assignment.day.toLowerCase() &&
            blocked.slot_number === assignment.slot_number
          );
          if (isBlocked) {
            postSwapViolations.push(`${taName} would be assigned to a blocked slot: ${assignment.day} slot ${assignment.slot_number}`);
          }
        });
      }
    });

    if (conflicts.length > 0 || postSwapViolations.length > 0) {
      const allViolations = [...conflicts, ...postSwapViolations];
      console.log(`❌ Swap simulation found ${allViolations.length} violations:`, allViolations);
      return {
        valid: false,
        reason: `Swap would create violations: ${allViolations[0]}` // Show first violation
      };
    }

    console.log('✅ Swap simulation passed - no conflicts or violations detected');

    // If we get here, the swap is valid
    console.log(`✅ Swap validation passed: ${assignment1.ta_name} <-> ${assignment2.ta_name}`);
    return { valid: true };
  };

  // Find related lab/tutorial for matching policy
  const findRelatedAssignment = (assignment) => {
    if (!policies.tutorial_lab_number_matching) return null;

    const targetType = assignment.slot_type === 'tutorial' ? 'lab' : 'tutorial';
    const targetNumber = assignment.slot_type === 'tutorial' ? assignment.tutorial_number : assignment.lab_number;

    return schedule.assignments.find(a =>
      a.slot_type === targetType &&
      (targetType === 'lab' ? a.lab_number : a.tutorial_number) === targetNumber &&
      a.ta_name === assignment.ta_name
    );
  };

  // Execute manual swap
  const executeSwap = (assignment1, assignment2) => {
    const validation = validateSwap(assignment1, assignment2);
    if (!validation.valid) {
      toast.error(validation.reason);
      return;
    }

    let swaps = [{ assignment1, assignment2 }];

    // Handle tutorial/lab matching policy
    if (policies.tutorial_lab_number_matching) {
      const related1 = findRelatedAssignment(assignment1);
      const related2 = findRelatedAssignment(assignment2);

      if (related1 && related2) {
        // Validate related swaps too
        const relatedValidation = validateSwap(related1, related2);
        if (!relatedValidation.valid) {
          toast.error(`Cannot swap related assignments: ${relatedValidation.reason}`);
          return;
        }
        swaps.push({ assignment1: related1, assignment2: related2 });
      }
    }

    // Apply all swaps
    const updatedSchedule = {
      ...schedule,
      assignments: schedule.assignments.map(assignment => {
        for (const swap of swaps) {
          if (assignment === swap.assignment1) {
            return { ...assignment, ta_name: swap.assignment2.ta_name };
          }
          if (assignment === swap.assignment2) {
            return { ...assignment, ta_name: swap.assignment1.ta_name };
          }
        }
        return assignment;
      })
    };

    // Update the schedule state
    onManualSwap(updatedSchedule);

    // Update the visual grid to reflect the swap
    // eslint-disable-next-line no-undef
    setScheduleGrid(prevGrid => {
      const newGrid = { ...prevGrid };

      console.log('🔄 Updating visual grid after swap');
      console.log('Before swap grid:', JSON.stringify(prevGrid, null, 2));

      // For each swap, update the visual grid
      swaps.forEach(swap => {
        const { assignment1, assignment2 } = swap;
        console.log(`🔄 Processing swap: ${assignment1.ta_name} <-> ${assignment2.ta_name}`);

        // Find and update assignment1's visual representation
        if (newGrid[assignment1.day] && newGrid[assignment1.day][assignment1.slot_number]) {
          newGrid[assignment1.day][assignment1.slot_number] = newGrid[assignment1.day][assignment1.slot_number].map(gridAssignment => {
            if (gridAssignment.ta_name === assignment1.ta_name &&
                gridAssignment.slot_type === assignment1.slot_type &&
                gridAssignment.tutorial_number === assignment1.tutorial_number &&
                gridAssignment.lab_number === assignment1.lab_number) {
              return { ...gridAssignment, ta_name: assignment2.ta_name };
            }
            return gridAssignment;
          });
        }

        // Find and update assignment2's visual representation
        if (newGrid[assignment2.day] && newGrid[assignment2.day][assignment2.slot_number]) {
          newGrid[assignment2.day][assignment2.slot_number] = newGrid[assignment2.day][assignment2.slot_number].map(gridAssignment => {
            if (gridAssignment.ta_name === assignment2.ta_name &&
                gridAssignment.slot_type === assignment2.slot_type &&
                gridAssignment.tutorial_number === assignment2.tutorial_number &&
                gridAssignment.lab_number === assignment2.lab_number) {
              return { ...gridAssignment, ta_name: assignment1.ta_name };
            }
            return gridAssignment;
          });
        }
      });

      console.log('After swap grid:', JSON.stringify(newGrid, null, 2));
      return newGrid;
    });

    setSwapMode(false);
    setSelectedForSwap(null);
    setSwapCandidates([]);

    const swapCount = swaps.length;
    toast.success(`Successfully swapped ${swapCount} assignment${swapCount > 1 ? 's' : ''}`);
  };

  // Helper function to check if assignment matches (uniquely identifies assignments by position, not TA)
  const assignmentMatches = (a1, a2) => {
    return a1.day === a2.day &&
           a1.slot_number === a2.slot_number &&
           a1.slot_type === a2.slot_type &&
           a1.tutorial_number === a2.tutorial_number &&
           a1.lab_number === a2.lab_number;
  };

  // Helper function for exact assignment matching (including TA name)
  const exactAssignmentMatches = (a1, a2) => {
    return a1.ta_name === a2.ta_name &&
           a1.day === a2.day &&
           a1.slot_number === a2.slot_number &&
           a1.slot_type === a2.slot_type &&
           a1.tutorial_number === a2.tutorial_number &&
           a1.lab_number === a2.lab_number;
  };

  // Handle assignment selection for swap
  const handleSwapSelection = (assignment) => {
    if (!selectedForSwap) {
      // First selection - choose assignment to swap
      setSelectedForSwap(assignment);

      // Find valid swap candidates
      console.log('🔍 Looking for swap candidates for:', assignment);
      console.log('📋 Total assignments in schedule:', schedule.assignments.length);

      const candidates = schedule.assignments.filter(a => {
        if (exactAssignmentMatches(a, assignment)) {
          console.log(`❌ Skipping self-match: ${a.ta_name} (${a.slot_type})`);
          return false;
        }
        const validation = validateSwap(assignment, a);
        console.log(`🔄 Checking swap ${assignment.ta_name} (${assignment.slot_type}) <-> ${a.ta_name} (${a.slot_type}):`, validation);
        return validation.valid;
      });

      console.log(`✅ Found ${candidates.length} valid swap candidates for ${assignment.ta_name}:`, candidates);

      // Debug: Let's see what assignments were evaluated
      const allAssignments = schedule.assignments.filter(a => !exactAssignmentMatches(a, assignment));
      console.log(`📊 Evaluated ${allAssignments.length} potential swap targets:`, allAssignments.map(a => `${a.ta_name} (${a.day} slot ${a.slot_number})`));

      setSwapCandidates(candidates);

      if (candidates.length === 0) {
        // Find out why no swaps are available by checking constraints with other TAs
        const constraintReasons = [];
        schedule.assignments.forEach(a => {
          if (!exactAssignmentMatches(a, assignment)) {
            const validation = validateSwap(assignment, a);
            if (!validation.valid && validation.reason) {
              const reason = validation.reason;
              // Filter out generic self-comparison messages and focus on meaningful constraints
              if (!reason.includes("Cannot swap assignment with itself") &&
                  !constraintReasons.includes(reason)) {
                constraintReasons.push(reason);
              }
            }
          }
        });

        let message = `Selected ${assignment.slot_type} ${assignment.slot_type === 'tutorial' ? (assignment.tutorial_number != null ? 'T' + assignment.tutorial_number : 'Tutorial') : (assignment.lab_number != null ? 'L' + assignment.lab_number : 'Lab')} (${assignment.ta_name}). No valid swap targets.`;

        if (constraintReasons.length > 0) {
          // Prioritize meaningful constraint reasons
          const prioritizedReasons = constraintReasons.sort((a, b) => {
            // Prioritize specific time/availability constraints over generic ones
            if (a.includes('blocked') || a.includes('day off')) return -1;
            if (b.includes('blocked') || b.includes('day off')) return 1;
            return 0;
          });

          message += ` Most common issue: ${prioritizedReasons[0]}`;
          if (constraintReasons.length > 1) {
            message += ` (${constraintReasons.length} total issues found)`;
          }
        } else {
          // If no specific constraint reasons, provide more helpful debugging
          message += ` This might indicate a complex constraint scenario.`;
        }

        message += ' Click again to deselect.';
        toast(message, { icon: '⚠️' });
      } else {
        toast(`Selected ${assignment.slot_type} ${assignment.slot_type === 'tutorial' ? (assignment.tutorial_number != null ? 'T' + assignment.tutorial_number : 'Tutorial') : (assignment.lab_number != null ? 'L' + assignment.lab_number : 'Lab')} (${assignment.ta_name}). Found ${candidates.length} valid targets.`, { icon: 'ℹ️' });
      }
    } else if (exactAssignmentMatches(selectedForSwap, assignment)) {
      // Clicking the same assignment again - deselect
      setSelectedForSwap(null);
      setSwapCandidates([]);
      toast('Selection cancelled.', { icon: '❌' });
    } else {
      // Second selection - execute swap
      const candidateFound = swapCandidates.find(c => assignmentMatches(c, assignment));
      if (candidateFound) {
        executeSwap(selectedForSwap, assignment);
      } else {
        // Provide detailed explanation of why the swap is invalid
        const validation = validateSwap(selectedForSwap, assignment);
        const reason = validation.reason || 'Unknown constraint violation';
        toast.error(`Invalid swap: ${reason}`);
      }

      // Reset swap state
      setSelectedForSwap(null);
      setSwapCandidates([]);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow border">
      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-900">
          📊 Generated Schedule Results
          {schedule.success ? (
            <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              ✅ Success
            </span>
          ) : (
            <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
              ⚠️ Partial Success
            </span>
          )}
        </h2>
        <div className="flex space-x-3">
          {!swapMode && onSaveSchedule && (
            <button
              onClick={onSaveSchedule}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center"
            >
              💾 Save Schedule
            </button>
          )}
          {swapMode && (
            <button
              onClick={() => {
                setSwapMode(false);
                setSelectedForSwap(null);
                setSwapCandidates([]);
              }}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center"
            >
              ❌ Cancel Swap
            </button>
          )}
        </div>
      </div>

      <div className="p-6 space-y-4">
        <p className="text-gray-700">
          <strong>Result:</strong> {schedule.message}
        </p>

        {swapMode && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-orange-900 mb-2">🔄 Manual Swap Mode</h4>
            <p className="text-sm text-orange-700">
              {selectedForSwap ? (
                <>
                  Selected: <strong>{selectedForSwap.slot_type} {selectedForSwap.slot_type === 'tutorial' ? 'T' + selectedForSwap.tutorial_number : 'L' + selectedForSwap.lab_number}</strong> ({selectedForSwap.ta_name})
                  <br />
                  Now click on any <span className="font-medium text-green-700">highlighted green</span> assignment to swap with.
                </>
              ) : (
                'Click on any assignment to start a swap. Valid swap targets will be highlighted.'
              )}
            </p>
            {policies.tutorial_lab_number_matching && (
              <p className="text-xs text-orange-600 mt-2">
                ⚠️ Tutorial/Lab matching policy is enabled - related assignments will be swapped together.
              </p>
            )}
          </div>
        )}

        {schedule.assignments && schedule.assignments.length > 0 && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">📅 Visual Schedule Grid with TA Assignments:</h3>
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
                            {scheduleDisplayGrid[day] && scheduleDisplayGrid[day][slot] ? scheduleDisplayGrid[day][slot].map((assignment, index) => {
                              const ta = getTAById(assignment.ta_name);
                              const taColorClass = ta ? getTAColor(ta.id) : 'bg-gray-100 border-gray-300 text-gray-800';

                              // Determine visual state for swap mode
                              // Create a full assignment structure for proper matching
                              const fullAssignment = {
                                ta_name: assignment.ta_name,
                                day: day,
                                slot_number: slot,
                                slot_type: assignment.slot_type,
                                tutorial_number: assignment.tutorial_number,
                                lab_number: assignment.lab_number,
                                duration: assignment.duration || 2
                              };

                              const isSelected = swapMode && selectedForSwap && exactAssignmentMatches(selectedForSwap, fullAssignment);
                              const candidateMatch = swapMode && selectedForSwap && swapCandidates.find(c => assignmentMatches(c, fullAssignment));
                              const isSwapCandidate = !!candidateMatch;
                              const isDisabledForSwap = swapMode && selectedForSwap && !isSwapCandidate && !isSelected;

                              // Debug logging for candidate matching
                              if (swapMode && selectedForSwap && !isSelected) {
                                console.log(`🔍 Checking visual assignment:`, fullAssignment);
                                console.log(`✅ Is swap candidate: ${isSwapCandidate}`);
                                if (!isSwapCandidate && swapCandidates.length > 0) {
                                  console.log(`❌ Not found in candidates. First few candidates:`, swapCandidates.slice(0, 3));
                                }
                              }

                              let visualClass = taColorClass;
                              if (swapMode) {
                                if (isSelected) {
                                  visualClass = 'bg-blue-500 border-blue-600 text-white';
                                } else if (isSwapCandidate) {
                                  visualClass = 'bg-green-400 border-green-500 text-white hover:bg-green-500';
                                } else if (isDisabledForSwap) {
                                  visualClass = 'bg-gray-300 border-gray-400 text-gray-600 opacity-50';
                                }
                              }

                              return (
                                <div
                                  key={index}
                                  onClick={() => {
                                    if (swapMode) {
                                      // Create properly structured assignment object for swap validation
                                      const swapAssignment = {
                                        ta_name: assignment.ta_name,
                                        day: day,
                                        slot_number: slot,
                                        slot_type: assignment.slot_type,
                                        tutorial_number: assignment.tutorial_number,
                                        lab_number: assignment.lab_number,
                                        duration: assignment.duration || 2
                                      };
                                      handleSwapSelection(swapAssignment);
                                    } else {
                                      // Automatically enable swap mode and start swap selection
                                      const swapAssignment = {
                                        ta_name: assignment.ta_name,
                                        day: day,
                                        slot_number: slot,
                                        slot_type: assignment.slot_type,
                                        tutorial_number: assignment.tutorial_number,
                                        lab_number: assignment.lab_number,
                                        duration: assignment.duration || 2
                                      };

                                      if (!swapMode) {
                                        setSwapMode(true);
                                        toast('Swap mode enabled. Click another assignment to swap.', { icon: '🔄' });
                                      }

                                      handleSwapSelection(swapAssignment);
                                    }
                                  }}
                                  className={`relative rounded p-2 text-xs border cursor-pointer hover:shadow-lg transition-all ${visualClass.replace('border-', 'border-').replace('bg-', 'bg-').replace('text-', 'text-')} ${
                                    isDisabledForSwap ? 'cursor-not-allowed' : ''
                                  }`}
                                >
                                  {swapMode && (
                                    <div className="absolute top-0 right-0 -mt-1 -mr-1">
                                      {isSelected && <span className="text-white text-xs">🔵</span>}
                                      {isSwapCandidate && <span className="text-white text-xs">✅</span>}
                                      {isDisabledForSwap && <span className="text-gray-500 text-xs">❌</span>}
                                    </div>
                                  )}
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
                                    {assignment.ta_name}
                                  </div>
                                </div>
                              );
                            }) : (
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
        )}

        {schedule.statistics && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-2xl font-bold text-blue-600">{Math.round(schedule.statistics.success_rate * 100)}%</div>
              <div className="text-sm text-gray-600">Success Rate</div>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-2xl font-bold text-green-600">{schedule.statistics.total_assignments}</div>
              <div className="text-sm text-gray-600">Total Assignments</div>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-2xl font-bold text-orange-600">{schedule.statistics.policy_violations || 0}</div>
              <div className="text-sm text-gray-600">Policy Violations</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VisualScheduleBuilder;