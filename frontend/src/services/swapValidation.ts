import {
  ScheduleAssignment,
  ConflictInfo,
  SchedulingPolicies,
  TeachingAssistant,
  DayEnum,
  SlotTypeEnum
} from '../types';

interface SwapValidationResult {
  isValid: boolean;
  conflicts: ConflictInfo[];
  warnings: ConflictInfo[];
}

interface SwapContext {
  sourceAssignment: ScheduleAssignment;
  targetSlot: {
    day: DayEnum;
    slot_number: number;
  };
  allAssignments: ScheduleAssignment[];
  policies: SchedulingPolicies;
  allTAs: TeachingAssistant[];
}

class SwapValidationService {
  /**
   * Validates if a TA assignment can be swapped to a different time slot
   */
  validateSwap(context: SwapContext): SwapValidationResult {
    const conflicts: ConflictInfo[] = [];
    const warnings: ConflictInfo[] = [];

    // Check basic availability conflicts
    this.checkDoubleBookingConflicts(context, conflicts);

    // Check workload capacity
    this.checkWorkloadConflicts(context, conflicts);

    // Check policy violations
    this.checkPolicyViolations(context, conflicts, warnings);

    // Check TA availability preferences
    this.checkAvailabilityPreferences(context, warnings);

    return {
      isValid: conflicts.length === 0,
      conflicts,
      warnings
    };
  }

  /**
   * Check for double-booking conflicts
   */
  private checkDoubleBookingConflicts(context: SwapContext, conflicts: ConflictInfo[]): void {
    const { sourceAssignment, targetSlot, allAssignments } = context;

    // Check if TA is already assigned to the target slot
    const existingAssignment = allAssignments.find(assignment =>
      assignment.ta_id === sourceAssignment.ta_id &&
      assignment.time_slot.day === targetSlot.day &&
      assignment.time_slot.slot_number === targetSlot.slot_number &&
      assignment.id !== sourceAssignment.id
    );

    if (existingAssignment) {
      conflicts.push({
        type: 'double_booking',
        ta_name: sourceAssignment.ta.name,
        slot: `${targetSlot.day} slot ${targetSlot.slot_number}`,
        courses: [sourceAssignment.course.name, existingAssignment.course.name],
        message: `${sourceAssignment.ta.name} is already assigned to ${existingAssignment.course.name} at ${targetSlot.day} slot ${targetSlot.slot_number}`
      });
    }
  }

  /**
   * Check for workload capacity conflicts
   */
  private checkWorkloadConflicts(context: SwapContext, conflicts: ConflictInfo[]): void {
    const { sourceAssignment, allAssignments } = context;

    // Calculate current workload for the TA
    const taAssignments = allAssignments.filter(a => a.ta_id === sourceAssignment.ta_id);
    const currentHours = taAssignments.reduce((total, assignment) =>
      total + assignment.time_slot.duration, 0
    );

    if (currentHours > sourceAssignment.ta.max_weekly_hours) {
      const excessHours = currentHours - sourceAssignment.ta.max_weekly_hours;
      conflicts.push({
        type: 'overcapacity',
        ta_name: sourceAssignment.ta.name,
        current_hours: currentHours,
        max_hours: sourceAssignment.ta.max_weekly_hours,
        excess_hours: excessHours,
        message: `${sourceAssignment.ta.name} would exceed capacity by ${excessHours} hours (${currentHours}/${sourceAssignment.ta.max_weekly_hours})`
      });
    }
  }

  /**
   * Check for policy violations
   */
  private checkPolicyViolations(
    context: SwapContext,
    conflicts: ConflictInfo[],
    warnings: ConflictInfo[]
  ): void {
    const { sourceAssignment, targetSlot, allAssignments, policies } = context;

    if (policies.tutorial_lab_independence) {
      // Independence mode - no specific constraints
      return;
    }

    // Get all assignments for this TA
    const taAssignments = allAssignments.filter(a => a.ta_id === sourceAssignment.ta_id);

    // Simulate the swap
    const simulatedAssignments = taAssignments.map(assignment => {
      if (assignment.id === sourceAssignment.id) {
        return {
          ...assignment,
          time_slot: {
            ...assignment.time_slot,
            day: targetSlot.day,
            slot_number: targetSlot.slot_number
          }
        };
      }
      return assignment;
    });

    this.checkEqualCountPolicy(simulatedAssignments, sourceAssignment.ta.name, policies, conflicts);
    this.checkNumberMatchingPolicy(simulatedAssignments, sourceAssignment.ta.name, policies, conflicts);
  }

  /**
   * Check tutorial-lab equal count policy
   */
  private checkEqualCountPolicy(
    assignments: ScheduleAssignment[],
    taName: string,
    policies: SchedulingPolicies,
    conflicts: ConflictInfo[]
  ): void {
    if (!policies.tutorial_lab_equal_count) return;

    const tutorialCount = assignments.filter(a => a.time_slot.slot_type === SlotTypeEnum.TUTORIAL).length;
    const labCount = assignments.filter(a => a.time_slot.slot_type === SlotTypeEnum.LAB).length;

    if (tutorialCount !== labCount) {
      conflicts.push({
        type: 'policy_violation',
        ta_name: taName,
        message: `Equal count policy violation: ${taName} would have ${tutorialCount} tutorials and ${labCount} labs`
      });
    }
  }

  /**
   * Check tutorial-lab number matching policy
   */
  private checkNumberMatchingPolicy(
    assignments: ScheduleAssignment[],
    taName: string,
    policies: SchedulingPolicies,
    conflicts: ConflictInfo[]
  ): void {
    if (!policies.tutorial_lab_number_matching) return;

    const tutorials = assignments.filter(a => a.time_slot.slot_type === SlotTypeEnum.TUTORIAL);
    const labs = assignments.filter(a => a.time_slot.slot_type === SlotTypeEnum.LAB);

    for (const tutorial of tutorials) {
      const matchingLab = labs.find(lab =>
        lab.time_slot.slot_number === tutorial.time_slot.slot_number
      );

      if (!matchingLab) {
        conflicts.push({
          type: 'policy_violation',
          ta_name: taName,
          message: `Number matching policy violation: Tutorial ${tutorial.time_slot.slot_number} requires matching Lab ${tutorial.time_slot.slot_number} for ${taName}`
        });
      }
    }

    for (const lab of labs) {
      const matchingTutorial = tutorials.find(tutorial =>
        tutorial.time_slot.slot_number === lab.time_slot.slot_number
      );

      if (!matchingTutorial) {
        conflicts.push({
          type: 'policy_violation',
          ta_name: taName,
          message: `Number matching policy violation: Lab ${lab.time_slot.slot_number} requires matching Tutorial ${lab.time_slot.slot_number} for ${taName}`
        });
      }
    }
  }

  /**
   * Check TA availability preferences (warnings only)
   */
  private checkAvailabilityPreferences(context: SwapContext, warnings: ConflictInfo[]): void {
    const { sourceAssignment, targetSlot } = context;

    // Check if TA has availability for the target slot
    const hasAvailability = sourceAssignment.ta.availability?.some(avail =>
      avail.day === targetSlot.day &&
      avail.slot_number === targetSlot.slot_number &&
      avail.is_available
    );

    if (!hasAvailability) {
      warnings.push({
        type: 'policy_violation',
        ta_name: sourceAssignment.ta.name,
        slot: `${targetSlot.day} slot ${targetSlot.slot_number}`,
        message: `${sourceAssignment.ta.name} may not be available for ${targetSlot.day} slot ${targetSlot.slot_number}`
      });
    }

    // Check preference ranking
    const preference = sourceAssignment.ta.availability?.find(avail =>
      avail.day === targetSlot.day &&
      avail.slot_number === targetSlot.slot_number
    );

    if (preference && preference.preference_rank > 3) {
      warnings.push({
        type: 'policy_violation',
        ta_name: sourceAssignment.ta.name,
        slot: `${targetSlot.day} slot ${targetSlot.slot_number}`,
        message: `${sourceAssignment.ta.name} has low preference (${preference.preference_rank}) for ${targetSlot.day} slot ${targetSlot.slot_number}`
      });
    }
  }

  /**
   * Validate multiple swaps (for bulk operations)
   */
  validateMultipleSwaps(swaps: SwapContext[]): SwapValidationResult {
    const allConflicts: ConflictInfo[] = [];
    const allWarnings: ConflictInfo[] = [];

    for (const swap of swaps) {
      const result = this.validateSwap(swap);
      allConflicts.push(...result.conflicts);
      allWarnings.push(...result.warnings);
    }

    // Check for inter-swap conflicts
    this.checkInterSwapConflicts(swaps, allConflicts);

    return {
      isValid: allConflicts.length === 0,
      conflicts: allConflicts,
      warnings: allWarnings
    };
  }

  /**
   * Check for conflicts between multiple swaps
   */
  private checkInterSwapConflicts(swaps: SwapContext[], conflicts: ConflictInfo[]): void {
    for (let i = 0; i < swaps.length; i++) {
      for (let j = i + 1; j < swaps.length; j++) {
        const swap1 = swaps[i];
        const swap2 = swaps[j];

        // Check if two swaps would result in same TA at same slot
        if (swap1.sourceAssignment.ta_id === swap2.sourceAssignment.ta_id &&
            swap1.targetSlot.day === swap2.targetSlot.day &&
            swap1.targetSlot.slot_number === swap2.targetSlot.slot_number) {
          conflicts.push({
            type: 'double_booking',
            ta_name: swap1.sourceAssignment.ta.name,
            slot: `${swap1.targetSlot.day} slot ${swap1.targetSlot.slot_number}`,
            message: `Multiple swaps would assign ${swap1.sourceAssignment.ta.name} to the same slot`
          });
        }
      }
    }
  }

  /**
   * Get swap recommendations for optimization
   */
  getSwapRecommendations(
    assignments: ScheduleAssignment[],
    policies: SchedulingPolicies
  ): { source: ScheduleAssignment; target: ScheduleAssignment; benefit: string }[] {
    const recommendations: { source: ScheduleAssignment; target: ScheduleAssignment; benefit: string }[] = [];

    // Find assignments that could benefit from swapping
    for (let i = 0; i < assignments.length; i++) {
      for (let j = i + 1; j < assignments.length; j++) {
        const assignment1 = assignments[i];
        const assignment2 = assignments[j];

        // Skip same TA assignments
        if (assignment1.ta_id === assignment2.ta_id) continue;

        // Check if swapping would improve preferences
        const improvement = this.calculateSwapBenefit(assignment1, assignment2, assignments, policies);
        if (improvement.beneficial) {
          recommendations.push({
            source: assignment1,
            target: assignment2,
            benefit: improvement.reason
          });
        }
      }
    }

    return recommendations.slice(0, 10); // Limit to top 10 recommendations
  }

  /**
   * Calculate if swapping two assignments would be beneficial
   */
  private calculateSwapBenefit(
    assignment1: ScheduleAssignment,
    assignment2: ScheduleAssignment,
    allAssignments: ScheduleAssignment[],
    policies: SchedulingPolicies
  ): { beneficial: boolean; reason: string } {
    // Check preference improvements
    const ta1Pref1 = this.getTAPreference(assignment1.ta, assignment1.time_slot);
    const ta1Pref2 = this.getTAPreference(assignment1.ta, assignment2.time_slot);
    const ta2Pref1 = this.getTAPreference(assignment2.ta, assignment1.time_slot);
    const ta2Pref2 = this.getTAPreference(assignment2.ta, assignment2.time_slot);

    const currentTotalPref = ta1Pref1 + ta2Pref2;
    const swappedTotalPref = ta1Pref2 + ta2Pref1;

    if (swappedTotalPref < currentTotalPref) {
      return {
        beneficial: true,
        reason: `Improves preference matching (${currentTotalPref} → ${swappedTotalPref})`
      };
    }

    // Check workload balancing
    const ta1Workload = this.calculateTAWorkload(assignment1.ta_id, allAssignments);
    const ta2Workload = this.calculateTAWorkload(assignment2.ta_id, allAssignments);
    const workloadDiff = Math.abs(ta1Workload - ta2Workload);

    if (workloadDiff > 2) { // 2+ hour difference
      const lessLoadedTA = ta1Workload < ta2Workload ? assignment1.ta : assignment2.ta;
      return {
        beneficial: true,
        reason: `Balances workload (difference: ${workloadDiff} hours)`
      };
    }

    return { beneficial: false, reason: '' };
  }

  /**
   * Get TA preference for a time slot (lower is better, 0 if not found)
   */
  private getTAPreference(ta: TeachingAssistant, timeSlot: any): number {
    const availability = ta.availability?.find(avail =>
      avail.day === timeSlot.day && avail.slot_number === timeSlot.slot_number
    );
    return availability?.preference_rank || 5; // Default to lowest preference if not found
  }

  /**
   * Calculate total workload for a TA
   */
  private calculateTAWorkload(taId: number, assignments: ScheduleAssignment[]): number {
    return assignments
      .filter(a => a.ta_id === taId)
      .reduce((total, a) => total + a.time_slot.duration, 0);
  }
}

export default new SwapValidationService();