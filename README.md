# GIU Staff Schedule Composer - Scheduling Algorithms

This repository contains the complete implementation of scheduling algorithms for the GIU Staff Schedule Composer system, as specified in your requirements document.

## 🏗️ System Architecture

The system implements a layered architecture with the following key components:

### Core Models (`models.py`)
- **TimeSlot**: Represents tutorial/lab slots with day, time, and duration
- **TA**: Teaching Assistant with availability, preferences, and capacity
- **Course**: Course with required slots and assigned TAs
- **SchedulingPolicies**: Configuration for different assignment rules
- **GlobalSchedule**: Complete schedule across all courses

### Scheduling Engine
- **PolicyValidator** (`policy_validator.py`): Enforces scheduling policies
- **CourseScheduler** (`course_scheduler.py`): Handles individual course scheduling
- **GlobalScheduler** (`global_scheduler.py`): Merges course schedules globally
- **ConflictResolver** (`conflict_resolver.py`): Detects and resolves conflicts
- **WorkloadBalancer** (`workload_balancer.py`): Balances TA workloads

### Main Interface
- **GIUScheduler** (`scheduler.py`): High-level API for the entire system

## 🎯 Core Features Implemented

### 1. Course-Scoped Scheduling
✅ Each course maintains its own mini-schedule
✅ Admin defines slots per course (day + slot number 1-5)
✅ **Saturday-Thursday** support (6-day week)
✅ Tutorial and lab slot types supported
✅ Fixed 2-hour duration for all slots
✅ Auto-composition of global schedule from all courses

### 2. TA Assignment & Workload Logic
✅ TAs have desired/available slots (preferences)
✅ Maximum weekly hours capacity
✅ Existing commitments tracking across courses
✅ Scheduler balances hours within and across courses

### 3. Policy Options
✅ **Tutorial-Lab Independence** (default OFF): When ON, arbitrary slot mix allowed
✅ **Tutorial-Lab Equal Count** (default OFF): Equal number of tutorials and labs per TA
✅ **Tutorial-Lab Number Matching** (default OFF): Tutorial N paired with Lab N
✅ Policies are independent toggles that can be combined

### 4. Auto-Schedule Generation
✅ Course-level assignment based on availability, preferences, and capacity
✅ Policy enforcement during assignment
✅ Global schedule merging with conflict detection
✅ Automatic conflict resolution with manual override options

### 5. Advanced Features
✅ **Workload Balancing**: Fairness mode equalizes TA workloads
✅ **Conflict Detection**: Automatic detection of double-booking and overcapacity
✅ **Optimization**: Multi-pass optimization for better assignments
✅ **Preference Ranking**: TAs can rank slot preferences (1=highest)
✅ **Statistics & Analytics**: Comprehensive scheduling statistics
✅ **Export Formats**: Grid, list, and CSV export options

## 🚀 Usage

### Basic Usage
```python
from models import Course, TA, TimeSlot, Day, SlotType, SchedulingPolicies
from scheduler import GIUScheduler

# Create time slots
slot1 = TimeSlot(Day.SUNDAY, 1, SlotType.TUTORIAL)
slot2 = TimeSlot(Day.SUNDAY, 1, SlotType.LAB)

# Create TA with availability and preferences
ta = TA(
    id="ta_001",
    name="Ahmed Hassan",
    max_weekly_hours=8,
    available_slots={slot1, slot2},
    preferred_slots={slot1: 1, slot2: 2}  # 1 = highest preference
)

# Create course with required slots
course = Course(
    id="cs101",
    name="Introduction to Programming",
    required_slots=[slot1, slot2],
    assigned_tas=[ta]
)

# Configure scheduling policies
policies = SchedulingPolicies(
    tutorial_lab_equal_count=True,
    fairness_mode=True
)

# Create scheduler and generate schedule
scheduler = GIUScheduler(policies)
result = scheduler.create_schedule([course])

# Check results
if result.success:
    print("✓ Schedule created successfully!")
    print(scheduler.export_schedule(result, format="grid"))
else:
    print(f"⚠️ Scheduling issues: {result.message}")
```

### Policy Configuration Examples
```python
# Default (independence OFF, no specific policies)
policies = SchedulingPolicies()  # Allows any valid assignment

# Independent assignment (arbitrary slot combinations)
policies = SchedulingPolicies(
    tutorial_lab_independence=True
)

# Equal count requirement (independence must be OFF)
policies = SchedulingPolicies(
    tutorial_lab_independence=False,
    tutorial_lab_equal_count=True
)

# Number matching requirement (independence must be OFF)
policies = SchedulingPolicies(
    tutorial_lab_independence=False,
    tutorial_lab_number_matching=True
)

# Combined policies (strongest constraints)
policies = SchedulingPolicies(
    tutorial_lab_independence=False,
    tutorial_lab_equal_count=True,
    tutorial_lab_number_matching=True
)

# Fairness optimization (works with any policy combination)
policies = SchedulingPolicies(
    fairness_mode=True
)
```

### Advanced Features
```python
# Get detailed statistics
stats = scheduler.get_schedule_statistics(result)
print(f"Success rate: {stats['success_rate']:.2f}")
print(f"Workload balance score: {stats['workload_balance']['imbalance_score']}")

# Get improvement suggestions
suggestions = scheduler.suggest_improvements(result)
for suggestion in suggestions:
    print(f"💡 {suggestion}")

# Resolve conflicts manually
if not result.success:
    resolved = scheduler.resolve_conflicts(result, auto_resolve=True)
    print(f"Conflicts resolved: {resolved.message}")
```

## 🧪 Testing

Run the included tests to verify the system:

```bash
# Simple verification tests
python3 simple_test.py

# Comprehensive demonstration
python3 example.py

# Debug specific scenarios
python3 debug_test.py
```

## 📊 Algorithm Performance

The scheduling algorithms implement several optimization strategies:

### 1. Greedy Assignment
- **Strategy**: Assign best combinations first based on preferences
- **Time Complexity**: O(n×m×c) where n=TAs, m=slots, c=combinations
- **Use Case**: Fast scheduling for small-medium datasets

### 2. Fairness-Based Assignment
- **Strategy**: Balance workloads across all TAs
- **Time Complexity**: O(s×log(t)) where s=slots, t=TAs
- **Use Case**: When workload equality is priority

### 3. Conflict Resolution
- **Strategy**: Multi-stage conflict detection and resolution
- **Conflicts Handled**: Double-booking, overcapacity, policy violations
- **Resolution**: Automatic with manual override options

### 4. Policy Enforcement
- **Real-time Validation**: Policies checked during assignment
- **Constraint Satisfaction**: Backtracking for complex policy combinations
- **Flexibility**: Toggle policies independently

## 📈 Success Example (from Specification)

**Scenario**: Course A requires 6 slots (4 tutorials, 2 labs)
- **TA Ahmed**: max 8 hrs/week, prefers Sun–Tue
- **TA Sara**: max 6 hrs/week, day off Monday
- **Policy**: Equal Count ON, Number Matching OFF

**Result**:
- Ahmed gets 2 tutorials + 2 labs (8 hours total)
- Sara gets 2 tutorials (4 hours total)
- Global schedule ensures no conflicts with other courses
- All policies satisfied ✅

## 🎛️ Configuration Options

| Feature | Description | Default |
|---------|-------------|---------|
| `tutorial_lab_independence` | Allow any slot combination | `False` |
| `tutorial_lab_equal_count` | Require equal tutorials/labs | `False` |
| `tutorial_lab_number_matching` | Pair Tutorial N with Lab N | `False` |
| `fairness_mode` | Balance workloads equally | `False` |

## 🚧 Future Enhancements

The system architecture supports easy extension for:
- Room/location constraints
- Multi-semester scheduling
- Dynamic capacity adjustment
- Machine learning preference prediction
- Real-time schedule updates
- Integration with university systems

---

**System Status**: ✅ **Fully Operational**
All core algorithms implemented and tested according to specification.