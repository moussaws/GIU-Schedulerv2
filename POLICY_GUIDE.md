# GIU Staff Schedule Composer - Policy Guide

## 📋 Policy System Overview

The GIU Staff Schedule Composer implements a flexible policy system that allows administrators to control how Teaching Assistants (TAs) are assigned to tutorial and lab sessions. This guide explains how each policy works and how they can be combined.

## 🎛️ Policy Options

### 1. Tutorial-Lab Independence Policy
- **Default**: `False` (OFF)
- **Description**: Controls whether TAs can be assigned arbitrary combinations of tutorials and labs
- **When ON (`True`)**: TAs can have any mix of slots (e.g., 3 labs + 2 tutorials, or 4 tutorials + 2 labs)
- **When OFF (`False`)**: Other specific policies can be applied to control slot assignments

### 2. Tutorial-Lab Equal Count Policy
- **Default**: `False` (OFF)
- **Description**: Requires each TA to teach equal numbers of tutorials and labs
- **Prerequisite**: Tutorial-Lab Independence must be OFF
- **Example**: If a TA is assigned to a course, they must have equal tutorials and labs (e.g., 2 tutorials + 2 labs)

### 3. Tutorial-Lab Number Matching Policy
- **Default**: `False` (OFF)
- **Description**: Strongest rule - requires tutorial slots to be paired with same-numbered lab slots
- **Prerequisite**: Tutorial-Lab Independence must be OFF
- **Example**: TA teaching Tutorial 1 must also teach Lab 1; TA teaching Tutorial 2 must also teach Lab 2

### 4. Fairness Mode
- **Default**: `False` (OFF)
- **Description**: Attempts to equalize workloads across all TAs
- **Works with**: Any combination of the above policies

## 📅 Schedule Support

### Days of the Week
The system supports a **6-day academic week**:
- Saturday
- Sunday
- Monday
- Tuesday
- Wednesday
- Thursday

### Time Slots
- **Slot Numbers**: 1-5 per day
- **Duration**: Fixed 2 hours per slot
- **Types**: Tutorial or Lab

## 🔧 Policy Combinations

### Valid Policy Combinations

1. **Default Mode** (No specific constraints)
```python
policies = SchedulingPolicies()
# Independence=False, Equal Count=False, Number Matching=False
# Result: Flexible assignment with no special constraints
```

2. **Independence Mode** (Complete flexibility)
```python
policies = SchedulingPolicies(tutorial_lab_independence=True)
# Result: TAs can have any combination of tutorials and labs
```

3. **Equal Count Mode** (Balanced assignments)
```python
policies = SchedulingPolicies(
    tutorial_lab_independence=False,
    tutorial_lab_equal_count=True
)
# Result: Each TA gets equal tutorials and labs
```

4. **Number Matching Mode** (Paired slots)
```python
policies = SchedulingPolicies(
    tutorial_lab_independence=False,
    tutorial_lab_number_matching=True
)
# Result: Tutorial N paired with Lab N for each TA
```

5. **Combined Strict Mode** (Maximum constraints)
```python
policies = SchedulingPolicies(
    tutorial_lab_independence=False,
    tutorial_lab_equal_count=True,
    tutorial_lab_number_matching=True
)
# Result: Equal count AND number matching both enforced
```

6. **Any Mode + Fairness** (Workload balancing)
```python
policies = SchedulingPolicies(
    # ... any combination above ...
    fairness_mode=True
)
# Result: Previous constraints + balanced workloads
```

### Invalid Combinations

❌ **Independence ON + Other Policies**
```python
# This combination is logically inconsistent
policies = SchedulingPolicies(
    tutorial_lab_independence=True,    # Allow arbitrary combinations
    tutorial_lab_equal_count=True      # But require equal count
)
# Result: Independence takes precedence, equal count is ignored
```

## 💡 Policy Examples

### Example 1: University with Flexible Assignment
```python
# Allow TAs to teach any combination of tutorials/labs
policies = SchedulingPolicies(tutorial_lab_independence=True)

# Possible assignments:
# - TA1: 3 Tutorials, 1 Lab
# - TA2: 2 Tutorials, 2 Labs
# - TA3: 1 Tutorial, 3 Labs
```

### Example 2: University with Balanced Workload Requirements
```python
# Require equal tutorials and labs per TA
policies = SchedulingPolicies(
    tutorial_lab_independence=False,
    tutorial_lab_equal_count=True
)

# Possible assignments:
# - TA1: 2 Tutorials, 2 Labs
# - TA2: 1 Tutorial, 1 Lab
# - TA3: 3 Tutorials, 3 Labs
```

### Example 3: University with Strict Pairing Requirements
```python
# Require tutorial-lab number matching
policies = SchedulingPolicies(
    tutorial_lab_independence=False,
    tutorial_lab_number_matching=True
)

# Possible assignments:
# - TA1: Tutorial 1 + Lab 1, Tutorial 3 + Lab 3
# - TA2: Tutorial 2 + Lab 2
# - TA3: Tutorial 4 + Lab 4, Tutorial 5 + Lab 5
```

### Example 4: University with Maximum Constraints
```python
# Require both equal count AND number matching
policies = SchedulingPolicies(
    tutorial_lab_independence=False,
    tutorial_lab_equal_count=True,
    tutorial_lab_number_matching=True,
    fairness_mode=True
)

# Possible assignments:
# - TA1: Tutorial 1 + Lab 1, Tutorial 2 + Lab 2 (2T, 2L, balanced workload)
# - TA2: Tutorial 3 + Lab 3 (1T, 1L, balanced workload)
# - TA3: Tutorial 4 + Lab 4, Tutorial 5 + Lab 5 (2T, 2L, balanced workload)
```

## 🧪 Testing Policies

Use the included test files to verify policy behavior:

```bash
# Test all policy combinations
python3 policy_test.py

# Test complete system with policies
python3 example.py

# Simple verification tests
python3 simple_test.py
```

## 📊 Policy Enforcement

### During Scheduling
- Policies are enforced in real-time during the assignment process
- Invalid combinations are detected and reported
- Policy violations are logged for administrator review

### Validation Process
1. **Slot Combination Generation**: Only valid combinations per policy are considered
2. **Assignment Validation**: Each assignment is checked against active policies
3. **Conflict Resolution**: Policy violations are treated as conflicts to be resolved
4. **Final Verification**: Complete schedule is validated before finalization

## 🎯 Policy Recommendations

### For Small Departments (≤ 3 TAs)
- Use **Independence Mode** for maximum flexibility
- Enable **Fairness Mode** to balance workloads

### For Medium Departments (4-10 TAs)
- Use **Equal Count Mode** to ensure fair distribution
- Enable **Fairness Mode** for workload balancing

### For Large Departments (10+ TAs)
- Use **Combined Strict Mode** for maximum organization
- Enable **Fairness Mode** and carefully monitor assignments

### For Departments with Course Continuity Requirements
- Use **Number Matching Mode** to maintain tutorial-lab consistency
- Consider instructor preferences in slot assignments

---

This policy system provides the flexibility needed for different institutional requirements while maintaining the ability to enforce specific constraints when needed.