from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum


class SlotType(Enum):
    TUTORIAL = "tutorial"
    LAB = "lab"


class Day(Enum):
    SATURDAY = "saturday"
    SUNDAY = "sunday"
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"


@dataclass
class TimeSlot:
    day: Day
    slot_number: int  # 1-5
    slot_type: SlotType
    duration: int = 2  # Fixed 2 hours

    def __str__(self) -> str:
        return f"{self.day.value.capitalize()} Slot {self.slot_number} ({self.slot_type.value})"

    def __hash__(self) -> int:
        return hash((self.day, self.slot_number, self.slot_type))


@dataclass
class TA:
    id: str
    name: str
    max_weekly_hours: int
    available_slots: Set[TimeSlot] = field(default_factory=set)
    preferred_slots: Dict[TimeSlot, int] = field(default_factory=dict)  # slot -> preference rank (1=highest)
    current_assignments: Dict[str, List[TimeSlot]] = field(default_factory=dict)  # course_id -> slots

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        return isinstance(other, TA) and self.id == other.id

    def get_total_assigned_hours(self) -> int:
        total = 0
        for slots in self.current_assignments.values():
            total += sum(slot.duration for slot in slots)
        return total

    def get_remaining_capacity(self) -> int:
        return self.max_weekly_hours - self.get_total_assigned_hours()

    def is_available_for_slot(self, slot: TimeSlot) -> bool:
        return slot in self.available_slots and not self.has_conflict(slot)

    def has_conflict(self, slot: TimeSlot) -> bool:
        for assigned_slots in self.current_assignments.values():
            for assigned_slot in assigned_slots:
                if assigned_slot.day == slot.day and assigned_slot.slot_number == slot.slot_number:
                    return True
        return False


@dataclass
class Course:
    id: str
    name: str
    required_slots: List[TimeSlot] = field(default_factory=list)
    assigned_tas: List[TA] = field(default_factory=list)
    schedule: Dict[TimeSlot, Optional[TA]] = field(default_factory=dict)

    def get_tutorial_slots(self) -> List[TimeSlot]:
        return [slot for slot in self.required_slots if slot.slot_type == SlotType.TUTORIAL]

    def get_lab_slots(self) -> List[TimeSlot]:
        return [slot for slot in self.required_slots if slot.slot_type == SlotType.LAB]

    def get_total_hours(self) -> int:
        return sum(slot.duration for slot in self.required_slots)


@dataclass
class SchedulingPolicies:
    tutorial_lab_independence: bool = False  # Default OFF - policies can be applied
    tutorial_lab_equal_count: bool = False  # Each TA has equal tutorials and labs
    tutorial_lab_number_matching: bool = False  # Tutorial N paired with Lab N
    fairness_mode: bool = False  # Equalize workloads across all TAs


@dataclass
class ScheduleAssignment:
    ta: TA
    slot: TimeSlot
    course: Course

    def __str__(self) -> str:
        return f"{self.ta.name} -> {self.slot} ({self.course.name})"


@dataclass
class GlobalSchedule:
    courses: List[Course]
    assignments: List[ScheduleAssignment] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)

    def get_schedule_grid(self) -> Dict[Tuple[Day, int], List[ScheduleAssignment]]:
        grid = {}
        for assignment in self.assignments:
            key = (assignment.slot.day, assignment.slot.slot_number)
            if key not in grid:
                grid[key] = []
            grid[key].append(assignment)
        return grid

    def detect_conflicts(self) -> List[str]:
        conflicts = []
        grid = self.get_schedule_grid()

        for (day, slot_num), assignments in grid.items():
            ta_count = {}
            for assignment in assignments:
                ta_id = assignment.ta.id
                if ta_id in ta_count:
                    conflicts.append(f"TA {assignment.ta.name} has multiple assignments at {day.value} slot {slot_num}")
                ta_count[ta_id] = ta_count.get(ta_id, 0) + 1

        return conflicts


@dataclass
class SchedulingResult:
    global_schedule: GlobalSchedule
    success: bool
    message: str
    unassigned_slots: List[Tuple[Course, TimeSlot]] = field(default_factory=list)
    policy_violations: List[str] = field(default_factory=list)