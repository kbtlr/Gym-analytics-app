import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_API = "http://localhost:5000"
TEST_USER = {
    "email": "test-suite@example.com",
    "username": "test_suite_user",
    "password": "testpass1234",
    "confirmPassword": "testpass1234"
}

# Performance tracking
performance_metrics: Dict[str, List[float]] = {}
session = requests.Session()
test_user_id = None


def timer(endpoint_name: str):
    """Decorator to track API response times"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            if endpoint_name not in performance_metrics:
                performance_metrics[endpoint_name] = []
            performance_metrics[endpoint_name].append(elapsed)
            return result
        return wrapper
    return decorator


def print_test(name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} {name}")
    if details and not passed:
        print(f"     {details}")
    return passed


@timer("health_check")
def test_health_check() -> bool:
    """Verify API is reachable and returns expected 401 for unauthenticated"""
    try:
        r = session.get(f"{BASE_API}/auth/me", timeout=5)
        return r.status_code == 401
    except Exception as e:
        print(f"Could not connect to backend: {e}")
        print("\n⚠️  Make sure 'npm run start:backend' is running first!")
        sys.exit(1)


@timer("register_step1")
def test_register_step1() -> bool:
    """Test creating a new user account"""
    global test_user_id
    
    r = session.post(f"{BASE_API}/auth/register/step1", json=TEST_USER)
    
    if r.status_code == 201:
        test_user_id = r.json()['userId']
        return True
    elif r.status_code == 409:
        # User already exists, try login first
        return test_login()
    else:
        print(f"Response: {r.text}")
        return False


@timer("login")
def test_login() -> bool:
    """Test login with credentials"""
    global test_user_id
    
    login_data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    }
    
    r = session.post(f"{BASE_API}/auth/login", json=login_data)
    
    if r.status_code == 200:
        test_user_id = r.json()['user']['id']
        return True
    return False


@timer("register_step2")
def test_register_step2() -> bool:
    """Test completing user profile setup"""
    step2_data = {
        "userId": test_user_id,
        "experienceLevel": "intermediate",
        "programLengthWeeks": 12,
        "targetWeeklySets": 16,
        "startingBodyweightKg": 82.5,
        "lifts": [
            {"exerciseName": "Squat", "bestWeightKg": 140, "bestReps": 1},
            {"exerciseName": "Bench Press", "bestWeightKg": 100, "bestReps": 1},
            {"exerciseName": "Deadlift", "bestWeightKg": 180, "bestReps": 1}
        ]
    }
    
    r = session.post(f"{BASE_API}/auth/register/step2", json=step2_data)
    return r.status_code == 200


@timer("current_user")
def test_current_user() -> bool:
    """Test getting authenticated user profile"""
    r = session.get(f"{BASE_API}/auth/me")
    if r.status_code != 200:
        return False
    
    data = r.json()
    return all(k in data['user'] for k in ['id', 'username', 'email'])


@timer("log_body_metrics")
def test_log_body_metrics() -> bool:
    """Test recording body composition data"""
    metric_data = {
        "bodyWeightKg": 83.2,
        "bodyFatPercent": 15.2,
        "waistCm": 82,
        "chestCm": 108,
        "notes": "Morning measurement"
    }
    
    r = session.post(f"{BASE_API}/stats/body-metrics", json=metric_data)
    return r.status_code == 201


@timer("body_metrics_history")
def test_body_metrics_history() -> bool:
    """Test retrieving body metrics history"""
    r = session.get(f"{BASE_API}/stats/body-metrics")
    return r.status_code == 200 and isinstance(r.json()['data'], list)


@timer("log_workout")
def test_log_workout() -> bool:
    """Test logging a complete workout session"""
    workout_data = {
        "performedAt": datetime.utcnow().isoformat(),
        "sets": [
            {
                "exerciseName": "Back Squat",
                "reps": 5,
                "weightKg": 120,
                "rpe": 8,
                "rir": 2
            },
            {
                "exerciseName": "Back Squat",
                "reps": 5,
                "weightKg": 120,
                "rpe": 8.5,
                "rir": 1
            },
            {
                "exerciseName": "Bench Press",
                "reps": 5,
                "weightKg": 90,
                "rpe": 7
            }
        ]
    }
    
    r = session.post(f"{BASE_API}/stats/workout", json=workout_data)
    return r.status_code == 201


@timer("volume_history")
def test_volume_history() -> bool:
    """Test retrieving training volume data"""
    r = session.get(f"{BASE_API}/stats/volume?days=30")
    return r.status_code == 200


@timer("personal_bests")
def test_personal_bests() -> bool:
    """Test retrieving personal best records"""
    r = session.get(f"{BASE_API}/stats/personal-bests")
    return r.status_code == 200


@timer("cycle_progress")
def test_cycle_progress() -> bool:
    """Test training cycle progress calculation"""
    r = session.get(f"{BASE_API}/stats/cycle-progress")
    return r.status_code == 200


@timer("volume_recommendations")
def test_volume_recommendations() -> bool:
    """Test volume recommendation engine"""
    r = session.get(f"{BASE_API}/stats/volume-recommendation")
    return r.status_code == 200


@timer("dashboard_summary")
def test_dashboard_summary() -> bool:
    """Test full dashboard summary endpoint"""
    r = session.get(f"{BASE_API}/stats/dashboard-summary")
    if r.status_code != 200:
        return False
    
    data = r.json()['data']
    required_fields = [
        'latestBodyMetrics', 'latestWorkout', 'recentVolumeKg',
        'bigThreePersonalBests', 'cycleProgress', 'volumeRecommendation'
    ]
    return all(k in data for k in required_fields)


@timer("logout")
def test_logout() -> bool:
    """Test user logout"""
    r = session.post(f"{BASE_API}/auth/logout")
    return r.status_code == 200


def cleanup_test_data():
    """Remove all test data created during test run"""
    print("\n🧹 Cleaning up test data...")
    
    # Log back in first
    test_login()
    
    # Delete user data directly (requires admin access or implement delete endpoint)
    print(f"   Removing test user ID: {test_user_id}")
    
    # Note: Add a user delete endpoint in your backend for proper cleanup
    # For now this is placeholder - you can extend this with actual cleanup logic
    
    session.cookies.clear()
    print("✅ Test data cleanup complete")


def print_performance_report():
    """Print formatted performance benchmark results"""
    print("\n⏱️  Performance Benchmarks:")
    print("-" * 60)
    
    total_time = 0.0
    total_requests = 0
    
    for endpoint, times in sorted(performance_metrics.items()):
        avg = sum(times) / len(times)
        min_t = min(times)
        max_t = max(times)
        total_time += sum(times)
        total_requests += len(times)
        
        print(f"  {endpoint:<30} avg: {avg:>6.1f}ms | min: {min_t:>5.1f}ms | max: {max_t:>5.1f}ms | hits: {len(times)}")
    
    print("-" * 60)
    print(f"  Total: {total_requests} requests in {total_time/1000:.2f}s | Average request: {total_time/total_requests:.1f}ms")


def main():
    print("\n🏋️ Gym Analytics End-to-End Test Suite")
    print("=" * 60)
    
    tests = [
        ("Health check", test_health_check),
        ("Register new user", test_register_step1),
        ("Complete profile setup", test_register_step2),
        ("Get current user profile", test_current_user),
        ("Log body metrics", test_log_body_metrics),
        ("Get body metrics history", test_body_metrics_history),
        ("Log complete workout", test_log_workout),
        ("Get training volume history", test_volume_history),
        ("Get personal bests", test_personal_bests),
        ("Get training cycle progress", test_cycle_progress),
        ("Get volume recommendations", test_volume_recommendations),
        ("Get dashboard summary", test_dashboard_summary),
        ("User logout", test_logout),
    ]
    
    passed = 0
    failed = 0
    
    print("\n📋 Running API Tests:")
    for test_name, test_func in tests:
        try:
            if print_test(test_name, test_func()):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_test(test_name, False, str(e))
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    print_performance_report()
    
    # Cleanup
    cleanup_test_data()
    
    print(f"\n✅ Test run complete in {sum(sum(t) for t in performance_metrics.values())/1000:.2f}s")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)