"""
Comprehensive Testing Framework for GIU Scheduling Algorithms
============================================================

This module provides extensive testing of scheduling algorithms with various hard cases,
constraint scenarios, and edge cases to evaluate performance and identify improvements.
"""

import json
import time
import random
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import requests

@dataclass
class TestResult:
    test_name: str
    success: bool
    execution_time: float
    assignments_count: int
    failed_slots: List[str]
    constraint_violations: List[str]
    workload_balance_score: float
    notes: str

@dataclass
class TestCase:
    name: str
    description: str
    tas: List[Dict[str, Any]]
    time_slots: List[Dict[str, Any]]
    policies: Dict[str, Any]
    expected_difficulty: str  # "easy", "medium", "hard", "extreme"

class SchedulingTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results: List[TestResult] = []

    def run_comprehensive_tests(self):
        """Run all test categories"""
        print("🧪 Starting Comprehensive Scheduling Algorithm Testing")
        print("=" * 60)

        # Test Categories
        self.test_basic_scenarios()
        self.test_constraint_violations()
        self.test_edge_cases()
        self.test_workload_balancing()
        self.test_scalability()
        self.test_randomized_scenarios()

        # Generate report
        self.generate_comprehensive_report()

    def test_basic_scenarios(self):
        """Test basic scheduling scenarios"""
        print("\n📋 Testing Basic Scenarios")
        print("-" * 30)

        # Test 1: Simple balanced scenario
        test_case = TestCase(
            name="Simple Balanced",
            description="6 TAs, 32 slots, balanced workload",
            tas=self.create_balanced_tas(6),
            time_slots=self.create_standard_slots(16, 16),
            policies={"premasters_cannot_teach_saturday": True, "tutorial_lab_independence": True},
            expected_difficulty="easy"
        )
        self.run_test_case(test_case)

        # Test 2: Minimal resources
        test_case = TestCase(
            name="Minimal Resources",
            description="4 TAs, 32 slots, tight resources",
            tas=self.create_balanced_tas(4),
            time_slots=self.create_standard_slots(16, 16),
            policies={"premasters_cannot_teach_saturday": True, "tutorial_lab_independence": True},
            expected_difficulty="medium"
        )
        self.run_test_case(test_case)

    def test_constraint_violations(self):
        """Test scenarios with various constraint violations"""
        print("\n⚠️  Testing Constraint Violation Scenarios")
        print("-" * 40)

        # Test 3: All TAs have Thursday off
        tas = self.create_balanced_tas(6)
        for ta in tas:
            ta["day_off"] = "thursday"

        test_case = TestCase(
            name="All TAs Thursday Off",
            description="All TAs unavailable on Thursday",
            tas=tas,
            time_slots=self.create_standard_slots(16, 16),
            policies={"premasters_cannot_teach_saturday": True, "tutorial_lab_independence": True},
            expected_difficulty="hard"
        )
        self.run_test_case(test_case)

        # Test 4: Excessive premasters TAs
        tas = self.create_balanced_tas(8)
        for i, ta in enumerate(tas):
            if i < 6:  # 6 out of 8 are premasters
                ta["premasters"] = True

        test_case = TestCase(
            name="Excessive Premasters",
            description="6/8 TAs are premasters (cannot teach Saturday)",
            tas=tas,
            time_slots=self.create_weekend_heavy_slots(),
            policies={"premasters_cannot_teach_saturday": True, "tutorial_lab_independence": True},
            expected_difficulty="hard"
        )
        self.run_test_case(test_case)

        # Test 5: Conflicting blocked slots
        tas = self.create_balanced_tas(5)
        # Create overlapping blocked slots for multiple TAs
        tas[0]["blocked_slots"] = [{"day": "monday", "slot": 1}, {"day": "monday", "slot": 2}]
        tas[1]["blocked_slots"] = [{"day": "monday", "slot": 1}, {"day": "tuesday", "slot": 1}]
        tas[2]["blocked_slots"] = [{"day": "monday", "slot": 2}, {"day": "tuesday", "slot": 2}]

        test_case = TestCase(
            name="Overlapping Blocked Slots",
            description="Multiple TAs with overlapping blocked time slots",
            tas=tas,
            time_slots=self.create_standard_slots(16, 16),
            policies={"premasters_cannot_teach_saturday": True, "tutorial_lab_independence": True},
            expected_difficulty="hard"
        )
        self.run_test_case(test_case)

    def test_edge_cases(self):
        """Test edge cases and extreme scenarios"""
        print("\n🔥 Testing Edge Cases and Extreme Scenarios")
        print("-" * 45)

        # Test 6: Single TA for many slots
        test_case = TestCase(
            name="Single TA Overload",
            description="1 TA for 20 slots (impossible)",
            tas=self.create_balanced_tas(1),
            time_slots=self.create_standard_slots(10, 10),
            policies={"premasters_cannot_teach_saturday": True, "tutorial_lab_independence": True},
            expected_difficulty="extreme"
        )
        self.run_test_case(test_case)

        # Test 7: Large scale scenario
        test_case = TestCase(
            name="Large Scale",
            description="15 TAs, 80 slots, complex constraints",
            tas=self.create_complex_tas(15),
            time_slots=self.create_standard_slots(40, 40),
            policies={"premasters_cannot_teach_saturday": True, "tutorial_lab_independence": True},
            expected_difficulty="hard"
        )
        self.run_test_case(test_case)

        # Test 8: No valid assignments
        tas = self.create_balanced_tas(3)
        for ta in tas:
            ta["premasters"] = True  # All premasters
            ta["day_off"] = "saturday"  # All have Saturday off

        # Only Saturday slots
        time_slots = []
        for i in range(1, 17):
            time_slots.extend([
                {"day": "saturday", "slot": 1, "type": "tutorial", "tutorial_number": i, "lab_number": None},
                {"day": "saturday", "slot": 2, "type": "lab", "tutorial_number": None, "lab_number": i}
            ])

        test_case = TestCase(
            name="Impossible Assignment",
            description="All TAs unavailable for all available slots",
            tas=tas,
            time_slots=time_slots,
            policies={"premasters_cannot_teach_saturday": True, "tutorial_lab_independence": True},
            expected_difficulty="extreme"
        )
        self.run_test_case(test_case)

    def test_workload_balancing(self):
        """Test workload balancing scenarios"""
        print("\n⚖️  Testing Workload Balancing")
        print("-" * 35)

        # Test 9: Uneven TA capabilities
        tas = []
        # Create TAs with very different hour allocations
        for i in range(6):
            if i < 2:
                hours = 20  # High capacity TAs
            elif i < 4:
                hours = 8   # Medium capacity TAs
            else:
                hours = 4   # Low capacity TAs

            tas.append({
                "id": i + 1,
                "name": f"TA_{i+1}",
                "email": f"ta{i+1}@email.com",
                "course_allocations": [{"course_id": 1, "allocated_hours": hours}],
                "blocked_slots": [],
                "day_off": None,
                "premasters": False,
                "skills": [],
                "notes": ""
            })

        test_case = TestCase(
            name="Uneven Capacities",
            description="TAs with very different hour allocations",
            tas=tas,
            time_slots=self.create_standard_slots(16, 16),
            policies={"premasters_cannot_teach_saturday": True, "tutorial_lab_independence": True},
            expected_difficulty="medium"
        )
        self.run_test_case(test_case)

    def test_scalability(self):
        """Test algorithm scalability"""
        print("\n📈 Testing Scalability")
        print("-" * 25)

        # Test different scales
        scales = [
            (5, 20, "Small Scale"),
            (10, 40, "Medium Scale"),
            (20, 80, "Large Scale")
        ]

        for ta_count, slot_count, scale_name in scales:
            test_case = TestCase(
                name=f"Scalability: {scale_name}",
                description=f"{ta_count} TAs, {slot_count} slots",
                tas=self.create_balanced_tas(ta_count),
                time_slots=self.create_standard_slots(slot_count // 2, slot_count // 2),
                policies={"premasters_cannot_teach_saturday": True, "tutorial_lab_independence": True},
                expected_difficulty="medium"
            )
            self.run_test_case(test_case)

    def test_randomized_scenarios(self):
        """Test with randomized scenarios"""
        print("\n🎲 Testing Randomized Scenarios")
        print("-" * 35)

        for i in range(5):
            random.seed(i + 42)  # Reproducible randomness

            ta_count = random.randint(4, 12)
            tutorial_count = random.randint(8, 24)
            lab_count = random.randint(8, 24)

            tas = self.create_random_tas(ta_count)
            time_slots = self.create_standard_slots(tutorial_count, lab_count)

            test_case = TestCase(
                name=f"Random Scenario {i+1}",
                description=f"Random: {ta_count} TAs, {tutorial_count+lab_count} slots",
                tas=tas,
                time_slots=time_slots,
                policies={"premasters_cannot_teach_saturday": True, "tutorial_lab_independence": True},
                expected_difficulty="medium"
            )
            self.run_test_case(test_case)

    def run_test_case(self, test_case: TestCase):
        """Run a single test case"""
        print(f"  Running: {test_case.name}")

        start_time = time.time()

        try:
            # Use existing TA IDs (1-6) instead of creating new ones
            available_ta_ids = [1, 2, 3, 4, 5, 6]
            selected_ta_ids = available_ta_ids[:min(len(test_case.tas), len(available_ta_ids))]

            # Prepare request data
            request_data = {
                "course_ids": [1],
                "ta_ids": selected_ta_ids,
                "time_slots": test_case.time_slots,
                "policies": test_case.policies
            }

            # Make API request
            response = requests.post(
                f"{self.base_url}/generate-schedule",
                json=request_data,
                timeout=30
            )

            execution_time = time.time() - start_time

            if response.status_code == 200:
                result_data = response.json()

                success = result_data.get("success", False)
                assignments = result_data.get("assignments", [])
                failed_slots = result_data.get("failed_requirements", [])

                # Calculate metrics
                workload_balance = self.calculate_workload_balance(assignments, test_case.tas)
                constraint_violations = self.check_constraint_violations(assignments, test_case.tas, test_case.policies)

                result = TestResult(
                    test_name=test_case.name,
                    success=success,
                    execution_time=execution_time,
                    assignments_count=len(assignments),
                    failed_slots=[str(slot) for slot in failed_slots],
                    constraint_violations=constraint_violations,
                    workload_balance_score=workload_balance,
                    notes=f"Expected: {test_case.expected_difficulty}, {test_case.description}"
                )

                print(f"    ✅ Success: {success}, Time: {execution_time:.2f}s, Assignments: {len(assignments)}")

            else:
                result = TestResult(
                    test_name=test_case.name,
                    success=False,
                    execution_time=execution_time,
                    assignments_count=0,
                    failed_slots=[],
                    constraint_violations=[f"HTTP Error: {response.status_code}"],
                    workload_balance_score=0.0,
                    notes=f"API Error: {response.text}"
                )
                print(f"    ❌ API Error: {response.status_code}")

        except Exception as e:
            execution_time = time.time() - start_time
            result = TestResult(
                test_name=test_case.name,
                success=False,
                execution_time=execution_time,
                assignments_count=0,
                failed_slots=[],
                constraint_violations=[f"Exception: {str(e)}"],
                workload_balance_score=0.0,
                notes=f"Exception: {str(e)}"
            )
            print(f"    💥 Exception: {str(e)}")

        self.results.append(result)

    def calculate_workload_balance(self, assignments: List[Dict], tas: List[Dict]) -> float:
        """Calculate workload balance score (0-1, higher is better)"""
        if not assignments:
            return 0.0

        # Calculate hours per TA
        ta_hours = {}
        for assignment in assignments:
            ta_name = assignment.get("ta_name", "")
            duration = assignment.get("duration", 2)
            ta_hours[ta_name] = ta_hours.get(ta_name, 0) + duration

        if not ta_hours:
            return 0.0

        hours_list = list(ta_hours.values())
        if len(hours_list) <= 1:
            return 1.0

        # Calculate coefficient of variation (lower is better balance)
        mean_hours = sum(hours_list) / len(hours_list)
        variance = sum((h - mean_hours) ** 2 for h in hours_list) / len(hours_list)
        std_dev = variance ** 0.5

        if mean_hours == 0:
            return 0.0

        cv = std_dev / mean_hours
        # Convert to 0-1 score (1 is perfect balance)
        balance_score = max(0, 1 - cv)

        return balance_score

    def check_constraint_violations(self, assignments: List[Dict], tas: List[Dict], policies: Dict) -> List[str]:
        """Check for constraint violations in assignments"""
        violations = []

        for assignment in assignments:
            ta_name = assignment.get("ta_name", "")
            day = assignment.get("day", "")
            slot = assignment.get("slot_number", 0)

            # Find TA data
            ta_data = next((ta for ta in tas if ta["name"] == ta_name), None)
            if not ta_data:
                continue

            # Check day off violations
            if ta_data.get("day_off") == day:
                violations.append(f"{ta_name} assigned on day off ({day})")

            # Check blocked slots
            blocked_slots = ta_data.get("blocked_slots", [])
            for blocked in blocked_slots:
                if blocked.get("day") == day and blocked.get("slot") == slot:
                    violations.append(f"{ta_name} assigned to blocked slot ({day} slot {slot})")

            # Check premasters Saturday violation
            if (policies.get("premasters_cannot_teach_saturday", False) and
                ta_data.get("premasters", False) and day == "saturday"):
                violations.append(f"Premasters TA {ta_name} assigned to Saturday")

        return violations

    def create_balanced_tas(self, count: int) -> List[Dict]:
        """Create balanced TAs for testing"""
        tas = []
        days_off = ["monday", "tuesday", "wednesday", "thursday", None]

        for i in range(count):
            tas.append({
                "id": i + 1,
                "name": f"TA_{i+1}",
                "email": f"ta{i+1}@email.com",
                "course_allocations": [{"course_id": 1, "allocated_hours": 12}],
                "blocked_slots": [],
                "day_off": days_off[i % len(days_off)],
                "premasters": i % 3 == 0,  # Every 3rd TA is premasters
                "skills": [],
                "notes": ""
            })

        return tas

    def create_complex_tas(self, count: int) -> List[Dict]:
        """Create complex TAs with various constraints"""
        tas = []
        days_off = ["monday", "tuesday", "wednesday", "thursday", None]

        for i in range(count):
            # Vary hour allocations
            if i < count // 3:
                hours = 20
            elif i < 2 * count // 3:
                hours = 12
            else:
                hours = 8

            # Add some blocked slots randomly
            blocked_slots = []
            if i % 4 == 0:  # Every 4th TA has blocked slots
                blocked_slots = [
                    {"day": "monday", "slot": 1},
                    {"day": "wednesday", "slot": 2}
                ]

            tas.append({
                "id": i + 1,
                "name": f"TA_{i+1}",
                "email": f"ta{i+1}@email.com",
                "course_allocations": [{"course_id": 1, "allocated_hours": hours}],
                "blocked_slots": blocked_slots,
                "day_off": days_off[i % len(days_off)],
                "premasters": i % 2 == 0,  # Half are premasters
                "skills": ["tutorial"] if i % 3 == 0 else ["lab"] if i % 3 == 1 else [],
                "notes": ""
            })

        return tas

    def create_random_tas(self, count: int) -> List[Dict]:
        """Create random TAs for testing"""
        tas = []
        days_off = ["monday", "tuesday", "wednesday", "thursday", None]

        for i in range(count):
            hours = random.choice([4, 8, 12, 16, 20])
            day_off = random.choice(days_off)
            premasters = random.choice([True, False])

            blocked_slots = []
            if random.random() < 0.3:  # 30% chance of blocked slots
                blocked_slots = [
                    {"day": random.choice(["monday", "tuesday", "wednesday", "thursday", "saturday", "sunday"]),
                     "slot": random.randint(1, 4)}
                ]

            tas.append({
                "id": i + 1,
                "name": f"TA_{i+1}",
                "email": f"ta{i+1}@email.com",
                "course_allocations": [{"course_id": 1, "allocated_hours": hours}],
                "blocked_slots": blocked_slots,
                "day_off": day_off,
                "premasters": premasters,
                "skills": random.choice([[], ["tutorial"], ["lab"], ["tutorial", "lab"]]),
                "notes": ""
            })

        return tas

    def create_standard_slots(self, tutorial_count: int, lab_count: int) -> List[Dict]:
        """Create standard time slots"""
        days = ["saturday", "sunday", "monday", "tuesday", "wednesday", "thursday"]
        slots = [1, 2, 3, 4]

        time_slots = []
        tutorial_num = 1
        lab_num = 1

        # Add tutorials
        for _ in range(tutorial_count):
            day = random.choice(days)
            slot = random.choice(slots)
            time_slots.append({
                "day": day,
                "slot": slot,
                "type": "tutorial",
                "tutorial_number": tutorial_num,
                "lab_number": None
            })
            tutorial_num += 1

        # Add labs
        for _ in range(lab_count):
            day = random.choice(days)
            slot = random.choice(slots)
            time_slots.append({
                "day": day,
                "slot": slot,
                "type": "lab",
                "tutorial_number": None,
                "lab_number": lab_num
            })
            lab_num += 1

        return time_slots

    def create_weekend_heavy_slots(self) -> List[Dict]:
        """Create slots heavily concentrated on weekends"""
        time_slots = []
        tutorial_num = 1
        lab_num = 1

        # Most slots on Saturday/Sunday
        weekend_days = ["saturday", "sunday"]
        weekday_days = ["monday", "tuesday", "wednesday", "thursday"]

        # 80% weekend, 20% weekday
        for i in range(32):
            if i < 26:  # 26 weekend slots
                day = random.choice(weekend_days)
            else:  # 6 weekday slots
                day = random.choice(weekday_days)

            slot = random.choice([1, 2, 3, 4])

            if i % 2 == 0:  # Tutorial
                time_slots.append({
                    "day": day,
                    "slot": slot,
                    "type": "tutorial",
                    "tutorial_number": tutorial_num,
                    "lab_number": None
                })
                tutorial_num += 1
            else:  # Lab
                time_slots.append({
                    "day": day,
                    "slot": slot,
                    "type": "lab",
                    "tutorial_number": None,
                    "lab_number": lab_num
                })
                lab_num += 1

        return time_slots

    def generate_comprehensive_report(self):
        """Generate comprehensive test report with improvement recommendations"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE SCHEDULING ALGORITHM TEST REPORT")
        print("=" * 80)

        # Summary statistics
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        avg_execution_time = sum(r.execution_time for r in self.results) / total_tests if total_tests > 0 else 0

        print(f"\n📈 SUMMARY STATISTICS")
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
        print(f"Failed: {total_tests - successful_tests} ({(total_tests-successful_tests)/total_tests*100:.1f}%)")
        print(f"Average Execution Time: {avg_execution_time:.2f}s")

        # Detailed results
        print(f"\n📋 DETAILED TEST RESULTS")
        print("-" * 80)

        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{status} {result.test_name}")
            print(f"   Time: {result.execution_time:.2f}s | Assignments: {result.assignments_count} | Balance: {result.workload_balance_score:.2f}")

            if result.constraint_violations:
                print(f"   Violations: {', '.join(result.constraint_violations[:3])}{'...' if len(result.constraint_violations) > 3 else ''}")

            if result.failed_slots:
                print(f"   Failed Slots: {len(result.failed_slots)}")

            print(f"   Notes: {result.notes}")
            print()

        # Performance analysis
        self.analyze_performance()

        # Generate improvement recommendations
        self.generate_improvement_recommendations()

    def analyze_performance(self):
        """Analyze algorithm performance"""
        print(f"\n🔍 PERFORMANCE ANALYSIS")
        print("-" * 40)

        # Execution time analysis
        times = [r.execution_time for r in self.results]
        if times:
            print(f"Execution Time - Min: {min(times):.2f}s, Max: {max(times):.2f}s, Avg: {sum(times)/len(times):.2f}s")

        # Success rate by difficulty
        difficulty_stats = {}
        for result in self.results:
            difficulty = "unknown"
            if "easy" in result.notes.lower():
                difficulty = "easy"
            elif "medium" in result.notes.lower():
                difficulty = "medium"
            elif "hard" in result.notes.lower():
                difficulty = "hard"
            elif "extreme" in result.notes.lower():
                difficulty = "extreme"

            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {"total": 0, "success": 0}

            difficulty_stats[difficulty]["total"] += 1
            if result.success:
                difficulty_stats[difficulty]["success"] += 1

        print(f"\nSuccess Rate by Difficulty:")
        for difficulty, stats in difficulty_stats.items():
            rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
            print(f"  {difficulty.capitalize()}: {stats['success']}/{stats['total']} ({rate:.1f}%)")

        # Workload balance analysis
        balance_scores = [r.workload_balance_score for r in self.results if r.success]
        if balance_scores:
            avg_balance = sum(balance_scores) / len(balance_scores)
            print(f"\nWorkload Balance - Average: {avg_balance:.2f} (0=poor, 1=perfect)")

    def generate_improvement_recommendations(self):
        """Generate comprehensive improvement recommendations"""
        print(f"\n🚀 IMPROVEMENT RECOMMENDATIONS")
        print("=" * 50)

        recommendations = []

        # Analyze failure patterns
        failed_results = [r for r in self.results if not r.success]
        constraint_violations = []
        for result in failed_results:
            constraint_violations.extend(result.constraint_violations)

        # High-priority improvements
        print(f"\n🔥 HIGH PRIORITY IMPROVEMENTS:")

        if any("Exception" in v for v in constraint_violations):
            recommendations.append({
                "priority": "HIGH",
                "category": "Robustness",
                "issue": "Algorithm crashes with exceptions",
                "recommendation": "Add comprehensive error handling and input validation",
                "implementation": "Wrap assignment logic in try-catch blocks, validate inputs"
            })

        # Medium-priority improvements
        print(f"\n⚡ MEDIUM PRIORITY IMPROVEMENTS:")

        avg_balance = sum(r.workload_balance_score for r in self.results if r.success) / max(1, len([r for r in self.results if r.success]))
        if avg_balance < 0.7:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Workload Balancing",
                "issue": f"Poor workload balance (avg: {avg_balance:.2f})",
                "recommendation": "Improve workload balancing algorithm with better scoring",
                "implementation": "Add workload variance penalties to scoring function"
            })

        # Performance improvements
        slow_tests = [r for r in self.results if r.execution_time > 5.0]
        if slow_tests:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Performance",
                "issue": f"{len(slow_tests)} tests took >5 seconds",
                "recommendation": "Optimize algorithm for larger datasets",
                "implementation": "Add memoization, improve search pruning, parallel processing"
            })

        # Low-priority improvements
        print(f"\n💡 ENHANCEMENT OPPORTUNITIES:")

        recommendations.extend([
            {
                "priority": "LOW",
                "category": "Algorithm Variety",
                "issue": "Single algorithm approach",
                "recommendation": "Implement multiple scheduling algorithms",
                "implementation": "Add genetic algorithm, simulated annealing, constraint programming"
            },
            {
                "priority": "LOW",
                "category": "Randomization",
                "issue": "Deterministic results",
                "recommendation": "Add randomization for different solutions",
                "implementation": "Add random seed parameter, shuffle candidate selection"
            },
            {
                "priority": "LOW",
                "category": "Optimization",
                "issue": "Local optima",
                "recommendation": "Add post-processing optimization",
                "implementation": "Implement hill-climbing, swap optimization passes"
            }
        ])

        # Print recommendations
        for rec in recommendations:
            print(f"\n{rec['priority']} - {rec['category']}: {rec['issue']}")
            print(f"  → {rec['recommendation']}")
            print(f"  Implementation: {rec['implementation']}")

        # Save detailed report
        self.save_detailed_report(recommendations)

    def save_detailed_report(self, recommendations: List[Dict]):
        """Save detailed report to file"""
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": len(self.results),
                "successful_tests": sum(1 for r in self.results if r.success),
                "average_execution_time": sum(r.execution_time for r in self.results) / len(self.results)
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "assignments_count": r.assignments_count,
                    "workload_balance_score": r.workload_balance_score,
                    "constraint_violations": r.constraint_violations,
                    "notes": r.notes
                }
                for r in self.results
            ],
            "recommendations": recommendations
        }

        with open("/Users/moussa/Documents/claude-giu/backend/scheduling_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n💾 Detailed report saved to: scheduling_test_report.json")

if __name__ == "__main__":
    tester = SchedulingTester()
    tester.run_comprehensive_tests()