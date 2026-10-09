#!/usr/bin/env python3
"""
BudgetBound Functional Testing Script
Tests all major endpoints and features
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(test_name):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}Testing: {test_name}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")

def print_pass(message):
    print(f"{Colors.GREEN}✓ PASS: {message}{Colors.RESET}")

def print_fail(message):
    print(f"{Colors.RED}✗ FAIL: {message}{Colors.RESET}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ WARNING: {message}{Colors.RESET}")

def print_info(message):
    print(f"  {message}")

# Test Results Storage
test_results = {
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "issues": []
}

def record_pass():
    test_results["passed"] += 1

def record_fail(issue):
    test_results["failed"] += 1
    test_results["issues"].append(issue)

def record_warning():
    test_results["warnings"] += 1

# Global test user credentials
TEST_USER_EMAIL = f"test_user_{int(time.time())}@example.com"
TEST_USER_PASSWORD = "TestPass123!"
TEST_USER_NAME = "Functional Test User"
auth_token = None
test_trip_id = None

def test_health_check():
    """Test if backend is running"""
    print_test("Health Check")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_pass(f"Backend is online: {data.get('message')}")
            print_info(f"Version: {data.get('version')}")
            record_pass()
            return True
        else:
            print_fail(f"Unexpected status code: {response.status_code}")
            record_fail("Health check failed")
            return False
    except Exception as e:
        print_fail(f"Backend not reachable: {e}")
        record_fail("Backend connection failed")
        return False

def test_user_registration():
    """Test user registration"""
    print_test("User Registration")
    global auth_token
    
    payload = {
        "name": TEST_USER_NAME,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        
        if response.status_code in [200, 201]:  # Accept both 200 and 201
            data = response.json()
            auth_token = data.get("access_token")
            print_pass("User registration successful")
            print_info(f"User ID: {data.get('user', {}).get('id')}")
            print_info(f"Token received: {auth_token[:20]}...")
            record_pass()
            return True
        else:
            print_fail(f"Registration failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            record_fail("User registration failed")
            return False
    except Exception as e:
        print_fail(f"Registration error: {e}")
        record_fail("User registration error")
        return False

def test_duplicate_registration():
    """Test duplicate email handling"""
    print_test("Duplicate Registration Prevention")
    
    payload = {
        "name": TEST_USER_NAME,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        
        if response.status_code == 400:
            print_pass("Duplicate email correctly rejected")
            record_pass()
            return True
        else:
            print_fail(f"Duplicate allowed! Status: {response.status_code}")
            record_fail("Duplicate email not prevented")
            return False
    except Exception as e:
        print_fail(f"Test error: {e}")
        record_fail("Duplicate registration test error")
        return False

def test_user_login():
    """Test user login"""
    print_test("User Login")
    global auth_token
    
    payload = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login-json", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            print_pass("Login successful")
            print_info(f"Token: {auth_token[:20]}...")
            record_pass()
            return True
        else:
            print_fail(f"Login failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            record_fail("Login failed")
            return False
    except Exception as e:
        print_fail(f"Login error: {e}")
        record_fail("Login error")
        return False

def test_invalid_login():
    """Test invalid credentials"""
    print_test("Invalid Credentials Handling")
    
    payload = {
        "email": TEST_USER_EMAIL,
        "password": "WrongPassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login-json", json=payload)
        
        if response.status_code == 401:
            print_pass("Invalid credentials correctly rejected")
            record_pass()
            return True
        else:
            print_fail(f"Invalid credentials accepted! Status: {response.status_code}")
            record_fail("Invalid credentials accepted")
            return False
    except Exception as e:
        print_fail(f"Test error: {e}")
        record_fail("Invalid login test error")
        return False

def test_protected_route_without_auth():
    """Test accessing protected route without token"""
    print_test("Protected Route Authorization")
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/me")
        
        if response.status_code == 401:
            print_pass("Unauthorized access correctly blocked")
            record_pass()
            return True
        else:
            print_fail(f"Unauthorized access allowed! Status: {response.status_code}")
            record_fail("Authorization not enforced")
            return False
    except Exception as e:
        print_fail(f"Test error: {e}")
        record_fail("Protected route test error")
        return False

def test_get_user_profile():
    """Test fetching user profile"""
    print_test("Get User Profile")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_pass("Profile fetched successfully")
            print_info(f"Name: {data.get('name')}")
            print_info(f"Email: {data.get('email')}")
            print_info(f"Is Admin: {data.get('is_admin')}")
            record_pass()
            return True
        else:
            print_fail(f"Profile fetch failed: {response.status_code}")
            record_fail("Profile fetch failed")
            return False
    except Exception as e:
        print_fail(f"Profile fetch error: {e}")
        record_fail("Profile fetch error")
        return False

def test_get_destinations():
    """Test fetching destinations"""
    print_test("Get Destinations Catalog")
    
    try:
        response = requests.get(f"{BASE_URL}/api/destinations/")
        
        if response.status_code == 200:
            data = response.json()
            destinations = data.get("destinations", [])
            total = data.get("total", 0)
            print_pass(f"Destinations fetched successfully")
            print_info(f"Total destinations: {total}")
            print_info(f"Destinations in response: {len(destinations)}")
            
            if total > 0 and len(destinations) > 0:
                print_info(f"Sample: {destinations[0].get('name')}, {destinations[0].get('state')}")
                record_pass()
                return True
            else:
                print_warning("No destinations found in database")
                record_warning()
                return False
        else:
            print_fail(f"Destinations fetch failed: {response.status_code}")
            record_fail("Destinations fetch failed")
            return False
    except Exception as e:
        print_fail(f"Destinations fetch error: {e}")
        record_fail("Destinations fetch error")
        return False

def test_destination_detail():
    """Test fetching single destination"""
    print_test("Get Destination Detail")
    
    try:
        # First get a destination ID
        response = requests.get(f"{BASE_URL}/api/destinations/")
        destinations = response.json().get("destinations", [])
        
        if not destinations:
            print_warning("No destinations to test")
            record_warning()
            return False
        
        dest_id = destinations[0]["id"]
        
        # Fetch detail
        response = requests.get(f"{BASE_URL}/api/destinations/{dest_id}")
        
        if response.status_code == 200:
            data = response.json()
            print_pass("Destination detail fetched successfully")
            print_info(f"Name: {data.get('name')}")
            print_info(f"Category: {data.get('category')}")
            print_info(f"Rating: {data.get('rating')}")
            print_info(f"Avg Travel Cost: ₹{data.get('avg_travel_cost')}")
            record_pass()
            return True
        else:
            print_fail(f"Destination detail fetch failed: {response.status_code}")
            record_fail("Destination detail fetch failed")
            return False
    except Exception as e:
        print_fail(f"Destination detail error: {e}")
        record_fail("Destination detail error")
        return False

def test_trip_planning():
    """Test trip planning algorithm"""
    print_test("Trip Planning & Scoring Algorithm")
    
    global test_trip_id
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    payload = {
        "budget": 25000,
        "days": 4,
        "starting_city": "Bangalore",
        "travel_type": "Beach",
        "comfort_score": 60,
        "travelers_count": 2
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/trips/plan", json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_pass("Trip planning successful")
            print_info(f"Recommended: {data.get('destination', {}).get('name')}")
            print_info(f"Score: {data.get('value_score', 0):.2f}")
            
            # Access nested costs object
            costs = data.get('costs', {})
            print_info(f"Estimated Cost: ₹{costs.get('total_estimated_cost')}")
            print_info(f"Hotel Tier: {costs.get('hotel_tier')}")
            print_info(f"Transport: {costs.get('transport_mode')}")
            print_info(f"Days in itinerary: {len(data.get('itineraries', []))}")
            
            # Check cost breakdown
            if costs:
                print_info(f"Transport: ₹{costs.get('transport_cost')}")
                print_info(f"Hotel: ₹{costs.get('hotel_cost')}")
                print_info(f"Food: ₹{costs.get('food_cost')}")
                print_info(f"Activities: ₹{costs.get('activities_cost')}")
            
            record_pass()
            return True
        else:
            print_fail(f"Trip planning failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            record_fail("Trip planning failed")
            return False
    except Exception as e:
        print_fail(f"Trip planning error: {e}")
        record_fail("Trip planning error")
        return False

def test_save_trip():
    """Test saving a trip"""
    print_test("Save Trip to Database")
    
    global test_trip_id
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # First plan a trip
    plan_payload = {
        "budget": 15000,
        "days": 3,
        "starting_city": "Mumbai",
        "travel_type": "Nature",
        "comfort_score": 50,
        "travelers_count": 1
    }
    
    try:
        # Plan trip
        plan_response = requests.post(f"{BASE_URL}/api/trips/plan", json=plan_payload, headers=headers)
        
        if plan_response.status_code != 200:
            print_fail(f"Planning failed, cannot test save: {plan_response.status_code}")
            record_fail("Trip planning prerequisite failed")
            return False
            
        plan_data = plan_response.json()
        
        # Save trip - send the entire plan response as expected by the endpoint
        save_response = requests.post(f"{BASE_URL}/api/trips/", json=plan_data, headers=headers)
        
        if save_response.status_code == 200:
            data = save_response.json()
            test_trip_id = data.get("id")
            dest_name = data.get('destination', {}).get('name', 'Unknown') if data.get('destination') else 'Unknown'
            print_pass("Trip saved successfully")
            print_info(f"Trip ID: {test_trip_id}")
            print_info(f"Destination: {dest_name}")
            record_pass()
            return True
        else:
            print_fail(f"Trip save failed: {save_response.status_code}")
            print_info(f"Response: {save_response.text}")
            record_fail("Trip save failed")
            return False
    except Exception as e:
        print_fail(f"Trip save error: {e}")
        record_fail(f"Trip save error: {e}")
        return False

def test_get_user_trips():
    """Test fetching user's trips"""
    print_test("Get User Trips")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/trips/", headers=headers)
        
        if response.status_code == 200:
            trips = response.json()
            print_pass(f"User trips fetched successfully")
            print_info(f"Total trips: {len(trips)}")
            
            if trips:
                trip = trips[0]
                dest_name = trip.get('destination', {}).get('name', 'Unknown') if trip.get('destination') else 'Unknown'
                print_info(f"Sample trip: {dest_name} - ₹{trip.get('budget')}")
            
            record_pass()
            return True
        else:
            print_fail(f"Get trips failed: {response.status_code}")
            record_fail("Get trips failed")
            return False
    except Exception as e:
        print_fail(f"Get trips error: {e}")
        record_fail("Get trips error")
        return False

def test_dashboard_stats():
    """Test dashboard statistics"""
    print_test("Dashboard Analytics")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_pass("Dashboard stats fetched successfully")
            print_info(f"Total Trips: {data.get('total_trips')}")
            print_info(f"Planned Budget: ₹{data.get('planned_budget')}")
            print_info(f"Actual Expenses: ₹{data.get('actual_expenses')}")
            print_info(f"Savings: ₹{data.get('savings')}")
            print_info(f"Trips Planned: {data.get('trips_planned')}")
            print_info(f"Recent Trips: {len(data.get('recent_trips', []))}")
            record_pass()
            return True
        else:
            print_fail(f"Dashboard stats failed: {response.status_code}")
            record_fail("Dashboard stats failed")
            return False
    except Exception as e:
        print_fail(f"Dashboard stats error: {e}")
        record_fail("Dashboard stats error")
        return False

def test_expense_tracking():
    """Test expense tracking"""
    print_test("Expense Tracking")
    
    if not test_trip_id:
        print_warning("No trip ID available, skipping expense test")
        record_warning()
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    expense_payload = {
        "trip_id": test_trip_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "category": "Food",
        "amount": 850.50,
        "notes": "Dinner at beachfront restaurant"
    }
    
    try:
        # Add expense
        response = requests.post(f"{BASE_URL}/api/expenses/", json=expense_payload, headers=headers)
        
        if response.status_code in [200, 201]:  # Accept both 200 and 201
            expense_data = response.json()
            print_pass("Expense added successfully")
            print_info(f"Expense ID: {expense_data.get('id')}")
            print_info(f"Amount: ₹{expense_data.get('amount')}")
            
            # Get trip expenses
            get_response = requests.get(f"{BASE_URL}/api/expenses/trip/{test_trip_id}", headers=headers)
            
            if get_response.status_code == 200:
                expenses = get_response.json()
                print_pass(f"Trip expenses fetched: {len(expenses)} expense(s)")
                record_pass()
                return True
        else:
            print_fail(f"Expense tracking failed: {response.status_code}")
            record_fail("Expense tracking failed")
            return False
    except Exception as e:
        print_fail(f"Expense tracking error: {e}")
        record_fail("Expense tracking error")
        return False

def test_ai_chat():
    """Test AI chat functionality"""
    print_test("AI Chat Companion")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "What are some budget-friendly destinations in India for beach vacation?"
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/ai/chat", json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            reply = data.get("reply", "")
            print_pass("AI chat working")
            print_info(f"Reply length: {len(reply)} characters")
            print_info(f"Preview: {reply[:100]}...")
            record_pass()
            return True
        elif response.status_code in [501, 503]:
            print_warning("AI chat endpoint not configured (API key missing)")
            record_warning()
            return False
        else:
            print_fail(f"AI chat failed: {response.status_code}")
            print_info(f"Response: {response.text[:200]}")
            record_fail("AI chat failed")
            return False
    except Exception as e:
        print_fail(f"AI chat error: {e}")
        record_fail("AI chat error")
        return False

def test_reverse_search():
    """Test reverse search (budget-first discovery)"""
    print_test("Reverse Search (Budget-First Discovery)")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    params = {
        "budget": 30000,
        "days": 5,
        "starting_city": "Delhi",
        "travel_type": "Adventure",
        "comfort_score": 70,
        "travelers_count": 2,
        "limit": 5
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/trips/reverse/search", params=params, headers=headers)
        
        if response.status_code == 200:
            results = response.json()
            print_pass(f"Reverse search successful")
            print_info(f"Results returned: {len(results)}")
            
            for i, result in enumerate(results[:3], 1):
                dest = result.get('destination', {})
                dest_name = dest.get('name', 'Unknown')
                score = result.get('value_score', 0)
                cost = result.get('estimated_cost', 0)
                print_info(f"{i}. {dest_name} - Score: {score:.2f} - Cost: ₹{cost:.2f}")
            
            record_pass()
            return True
        else:
            print_fail(f"Reverse search failed: {response.status_code}")
            print_info(f"Response: {response.text[:200]}")
            record_fail("Reverse search failed")
            return False
    except Exception as e:
        print_fail(f"Reverse search error: {e}")
        record_fail(f"Reverse search error: {str(e)}")
        return False

def test_budget_optimizer():
    """Test budget optimizer"""
    print_test("Budget Optimizer")
    
    if not test_trip_id:
        print_warning("No trip ID available, skipping optimizer test")
        record_warning()
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.post(f"{BASE_URL}/api/trips/{test_trip_id}/optimize", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_pass("Budget optimizer working")
            print_info(f"Current estimate: ₹{data.get('current_estimate')}")
            print_info(f"Target budget: ₹{data.get('target_budget')}")
            print_info(f"Recommendations: {len(data.get('recommendations', []))}")
            
            for rec in data.get('recommendations', []):
                print_info(f"  - {rec.get('title')}: Save ₹{rec.get('savings')}")
            
            record_pass()
            return True
        else:
            print_fail(f"Budget optimizer failed: {response.status_code}")
            record_fail("Budget optimizer failed")
            return False
    except Exception as e:
        print_fail(f"Budget optimizer error: {e}")
        record_fail("Budget optimizer error")
        return False

def print_summary():
    """Print test summary"""
    print(f"\n\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}TEST SUMMARY{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    total_tests = test_results["passed"] + test_results["failed"] + test_results["warnings"]
    
    print(f"{Colors.GREEN}✓ Passed: {test_results['passed']}{Colors.RESET}")
    print(f"{Colors.RED}✗ Failed: {test_results['failed']}{Colors.RESET}")
    print(f"{Colors.YELLOW}⚠ Warnings: {test_results['warnings']}{Colors.RESET}")
    print(f"  Total Tests: {total_tests}")
    
    if test_results["passed"] == total_tests:
        print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED!{Colors.RESET}")
    elif test_results["failed"] == 0:
        print(f"\n{Colors.YELLOW}⚠ All tests passed with some warnings{Colors.RESET}")
    else:
        print(f"\n{Colors.RED}❌ Some tests failed{Colors.RESET}")
        print(f"\n{Colors.RED}Issues found:{Colors.RESET}")
        for issue in test_results["issues"]:
            print(f"  • {issue}")
    
    success_rate = (test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def main():
    """Run all functional tests"""
    print(f"\n{Colors.BLUE}╔═══════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BLUE}║     BudgetBound Functional Testing Suite                 ║{Colors.RESET}")
    print(f"{Colors.BLUE}╚═══════════════════════════════════════════════════════════╝{Colors.RESET}\n")
    
    print(f"Backend URL: {BASE_URL}")
    print(f"Test User: {TEST_USER_EMAIL}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run all tests
    if not test_health_check():
        print_fail("Backend is not running. Exiting tests.")
        return
    
    test_user_registration()
    test_duplicate_registration()
    test_user_login()
    test_invalid_login()
    test_protected_route_without_auth()
    test_get_user_profile()
    test_get_destinations()
    test_destination_detail()
    test_trip_planning()
    test_save_trip()
    test_get_user_trips()
    test_dashboard_stats()
    test_expense_tracking()
    test_ai_chat()
    test_reverse_search()
    test_budget_optimizer()
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    main()
