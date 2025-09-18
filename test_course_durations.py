#!/usr/bin/env python3
"""
Test script to validate course creation with 2-hour default durations.
Tests various scenarios to ensure calculations are correct.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_course_creation():
    """Test multiple course creation scenarios with different tutorial/lab combinations"""

    test_cases = [
        {
            "name": "6 tutorials, 0 labs",
            "data": {
                "code": "TEST101",
                "name": "Test Course - 6T 0L",
                "tutorials": 6,
                "labs": 0,
                "tutorial_duration": 2,
                "lab_duration": 2,
                "required_tas": 1
            },
            "expected_total_hours": 12  # 6 * 2 = 12
        },
        {
            "name": "4 tutorials, 2 labs",
            "data": {
                "code": "TEST102",
                "name": "Test Course - 4T 2L",
                "tutorials": 4,
                "labs": 2,
                "tutorial_duration": 2,
                "lab_duration": 2,
                "required_tas": 1
            },
            "expected_total_hours": 12  # (4 * 2) + (2 * 2) = 12
        },
        {
            "name": "0 tutorials, 6 labs",
            "data": {
                "code": "TEST103",
                "name": "Test Course - 0T 6L",
                "tutorials": 0,
                "labs": 6,
                "tutorial_duration": 2,
                "lab_duration": 2,
                "required_tas": 1
            },
            "expected_total_hours": 12  # 6 * 2 = 12
        },
        {
            "name": "8 tutorials, 4 labs",
            "data": {
                "code": "TEST104",
                "name": "Test Course - 8T 4L",
                "tutorials": 8,
                "labs": 4,
                "tutorial_duration": 2,
                "lab_duration": 2,
                "required_tas": 2
            },
            "expected_total_hours": 24  # (8 * 2) + (4 * 2) = 24
        },
        {
            "name": "1 tutorial, 1 lab",
            "data": {
                "code": "TEST105",
                "name": "Test Course - 1T 1L",
                "tutorials": 1,
                "labs": 1,
                "tutorial_duration": 2,
                "lab_duration": 2,
                "required_tas": 1
            },
            "expected_total_hours": 4  # (1 * 2) + (1 * 2) = 4
        }
    ]

    print("🧪 Testing Course Creation with 2-Hour Default Durations")
    print("=" * 60)

    # First, clear existing courses
    try:
        response = requests.get(f"{BASE_URL}/courses")
        if response.status_code == 200:
            existing_courses = response.json()
            for course in existing_courses:
                if course.get('code', '').startswith('TEST'):
                    requests.delete(f"{BASE_URL}/courses/{course['id']}")
            print("✅ Cleared existing test courses")
    except Exception as e:
        print(f"⚠️ Could not clear existing courses: {e}")

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 40)

        try:
            # Create the course
            response = requests.post(f"{BASE_URL}/courses", json=test_case['data'])

            if response.status_code == 200:
                course = response.json()

                # Calculate actual total hours
                actual_tutorial_hours = course['tutorials'] * course['tutorial_duration']
                actual_lab_hours = course['labs'] * course['lab_duration']
                actual_total_hours = actual_tutorial_hours + actual_lab_hours

                print(f"  📝 Course Code: {course['code']}")
                print(f"  📚 Tutorials: {course['tutorials']} × {course['tutorial_duration']}h = {actual_tutorial_hours}h")
                print(f"  🧪 Labs: {course['labs']} × {course['lab_duration']}h = {actual_lab_hours}h")
                print(f"  ⏱️  Total Hours: {actual_total_hours}h")
                print(f"  🎯 Expected: {test_case['expected_total_hours']}h")

                if actual_total_hours == test_case['expected_total_hours']:
                    print("  ✅ PASS - Hours calculation correct!")
                    results.append({"test": test_case['name'], "status": "PASS", "actual": actual_total_hours, "expected": test_case['expected_total_hours']})
                else:
                    print(f"  ❌ FAIL - Expected {test_case['expected_total_hours']}h, got {actual_total_hours}h")
                    results.append({"test": test_case['name'], "status": "FAIL", "actual": actual_total_hours, "expected": test_case['expected_total_hours']})

            else:
                print(f"  ❌ FAIL - HTTP {response.status_code}: {response.text}")
                results.append({"test": test_case['name'], "status": "FAIL", "error": f"HTTP {response.status_code}"})

        except Exception as e:
            print(f"  ❌ FAIL - Exception: {e}")
            results.append({"test": test_case['name'], "status": "FAIL", "error": str(e)})

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = len([r for r in results if r['status'] == 'PASS'])
    total = len(results)

    for result in results:
        if result['status'] == 'PASS':
            print(f"✅ {result['test']}")
        else:
            print(f"❌ {result['test']} - {result.get('error', 'Calculation mismatch')}")

    print(f"\n🎯 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Course duration calculations are working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    try:
        success = test_course_creation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test script failed: {e}")
        sys.exit(1)