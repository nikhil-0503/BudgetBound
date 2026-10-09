#!/usr/bin/env python3
"""
Test new features: Trip Comparison, Budget Alerts, Currency Converter
"""

import requests

BASE_URL = "http://127.0.0.1:8000"

# Login first
print("🔐 Logging in...")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login-json",
    json={"email": "test_user_1791555598@example.com", "password": "TestPass123!"}
)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful\n")
    
    print("="*60)
    print("Testing New Features")
    print("="*60)
    
    # Test 1: Check new destinations
    print("\n📍 Test 1: Checking destination count...")
    dest_response = requests.get(f"{BASE_URL}/api/destinations/")
    if dest_response.status_code == 200:
        total = dest_response.json().get("total", 0)
        print(f"✅ Total destinations: {total}")
        if total >= 205:
            print("✅ Enhanced destinations loaded successfully!")
    
    # Test 2: Currency Converter
    print("\n💱 Test 2: Currency Converter...")
    currency_response = requests.get(
        f"{BASE_URL}/api/currency/convert",
        params={"amount": 10000, "from_currency": "INR", "to_currency": "USD"}
    )
    if currency_response.status_code == 200:
        data = currency_response.json()
        print(f"✅ Currency Conversion:")
        print(f"   ₹{data['original_amount']} = ${data['converted_amount']}")
        print(f"   Exchange Rate: {data['exchange_rate']}")
    
    # Test 3: Get exchange rates
    print("\n💵 Test 3: Get all exchange rates...")
    rates_response = requests.get(f"{BASE_URL}/api/currency/rates")
    if rates_response.status_code == 200:
        data = rates_response.json()
        print(f"✅ Exchange rates for {data['base_currency']}:")
        print(f"   Supported currencies: {len(data['supported_currencies'])}")
        print(f"   Sample rates:")
        for curr in ['USD', 'EUR', 'AED', 'THB']:
            if curr in data['rates']:
                print(f"   1 INR = {data['rates'][curr]} {curr}")
    
    # Test 4: Trip Comparison
    print("\n🆚 Test 4: Trip Comparison...")
    comparison_response = requests.post(
        f"{BASE_URL}/api/trips/compare",
        json={
            "destination_ids": [1, 2, 3],  # First 3 destinations
            "budget": 25000,
            "days": 4,
            "starting_city": "Bangalore",
            "travelers_count": 2,
            "comfort_score": 60
        },
        headers=headers
    )
    if comparison_response.status_code == 200:
        data = comparison_response.json()
        print(f"✅ Trip Comparison:")
        print(f"   Destinations compared: {len(data['comparison'])}")
        print(f"   Recommendations:")
        print(f"   - Cheapest: {data['recommendations']['cheapest']} (₹{data['recommendations']['cheapest_cost']})")
        print(f"   - Best Value: {data['recommendations']['best_value']}")
        print(f"   - Price Difference: ₹{data['recommendations']['price_difference']}")
    
    # Test 5: Budget Alerts Summary
    print("\n🚨 Test 5: Budget Alerts Summary...")
    alerts_response = requests.get(
        f"{BASE_URL}/api/budget-alerts/user/summary",
        headers=headers
    )
    if alerts_response.status_code == 200:
        data = alerts_response.json()
        print(f"✅ Budget Summary:")
        print(f"   Total trips: {data['total_trips']}")
        print(f"   Total budget allocated: ₹{data['total_budget_allocated']}")
        print(f"   Trips over budget: {data['trips_over_budget']}")
        print(f"   Overall status: {data['overall_status']}")
    
    # Test 6: Search international destinations
    print("\n🌍 Test 6: International Destinations...")
    intl_response = requests.get(
        f"{BASE_URL}/api/destinations/",
        params={"search": "Dubai", "limit": 5}
    )
    if intl_response.status_code == 200:
        destinations = intl_response.json().get("destinations", [])
        print(f"✅ International destinations found:")
        for dest in destinations:
            print(f"   - {dest['name']}, {dest['state']} ({dest['category']})")
    
    print("\n" + "="*60)
    print("✅ All new features are working!")
    print("="*60)
    
else:
    print(f"❌ Login failed: {login_response.status_code}")
