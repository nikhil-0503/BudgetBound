import requests
import sys

BASE_URL = "http://localhost:8000"

def verify():
    print("1. Logging in...")
    email = "pdf_test_user@example.com"
    password = "password123"
    login_url = f"{BASE_URL}/api/auth/login-json"
    try:
        r = requests.post(login_url, json={"email": email, "password": password})
        if r.status_code != 200:
            print(f"Login failed: {r.status_code} - {r.text}")
            sys.exit(1)
        token = r.json().get("access_token")
        print("Login successful.")
    except Exception as e:
        print(f"Login connection failed: {e}")
        sys.exit(1)
        
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n2. Testing AI Chat Assistant (/api/ai/chat)...")
    chat_url = f"{BASE_URL}/api/ai/chat"
    chat_data = {"messages": [{"role": "user", "content": "Suggest 3 budget activities in Bangalore under 500 INR each."}]}
    try:
        r = requests.post(chat_url, json=chat_data, headers=headers)
        if r.status_code != 200:
            print(f"Chat failed: {r.status_code} - {r.text}")
            sys.exit(1)
        resp = r.json()
        print("Chat response obtained:")
        print(resp.get("reply", "")[:200] + "...")
    except Exception as e:
        print(f"Chat request failed: {e}")
        sys.exit(1)

    print("\n3. Testing AI Personalized Planner (/api/ai/personalized-plan)...")
    plan_url = f"{BASE_URL}/api/ai/personalized-plan"
    plan_data = {
        "preferences": {
            "keywords": "Kashmir lakes",
            "budget": 20000.0,
            "days": 3,
            "special": "vegetarian food only"
        }
    }
    try:
        r = requests.post(plan_url, json=plan_data, headers=headers)
        if r.status_code != 200:
            print(f"Personalized plan failed: {r.status_code} - {r.text}")
            sys.exit(1)
        planned = r.json()
        print("Personalized planner response obtained successfully:")
        print(f"Plan Name: {planned.get('plan_name')}")
        print(f"Estimated Cost: {planned.get('estimated_cost')}")
        print(f"Days: {len(planned.get('days', []))}")
    except Exception as e:
        sys.exit(1)

    # Let's find a trip to test regenerator and explainer
    print("\n4. Getting user trips...")
    trips_url = f"{BASE_URL}/api/trips/"
    try:
        r = requests.get(trips_url, headers=headers)
        trips = r.json()
        if not trips:
            print("No trips found to test regenerate and explain. Please run verify_pdf first.")
            sys.exit(1)
        trip_id = trips[0]["id"]
        print(f"Testing with Trip ID: {trip_id}")
    except Exception as e:
        sys.exit(1)
        
    print("\n5. Testing AI Explainability (/api/ai/explain)...")
    explain_url = f"{BASE_URL}/api/ai/explain"
    try:
        r = requests.post(explain_url, json={"trip_id": trip_id}, headers=headers)
        if r.status_code != 200:
            print(f"Explain failed: {r.status_code} - {r.text}")
            sys.exit(1)
        explained = r.json()
        print("Explain response obtained:")
        print(explained.get("explanation", "")[:200] + "...")
    except Exception as e:
        sys.exit(1)
        
    print("\n6. Testing AI Trip Regenerator (/api/ai/regenerate)...")
    regen_url = f"{BASE_URL}/api/ai/regenerate"
    regen_data = {
        "trip_id": trip_id,
        "instruction": "save money, use train transport and cheaper lodging"
    }
    try:
        r = requests.post(regen_url, json=regen_data, headers=headers)
        if r.status_code != 200:
            print(f"Regenerate failed: {r.status_code} - {r.text}")
            sys.exit(1)
        regenerated = r.json()
        print("Regenerator response obtained successfully:")
        print(f"Estimated Accommodation: {regenerated.get('costs', {}).get('hotel_cost')}")
        print(f"New Total Cost: {regenerated.get('costs', {}).get('total_estimated_cost')}")
    except Exception as e:
        sys.exit(1)

    print("\n7. Testing applying regeneration (PUT /api/trips/{trip_id})...")
    put_url = f"{BASE_URL}/api/trips/{trip_id}"
    try:
        r = requests.put(put_url, json=regenerated, headers=headers)
        if r.status_code != 200:
            print(f"Applying regeneration failed: {r.status_code} - {r.text}")
            sys.exit(1)
        print("PUT request successful. Trip updated in database.")
    except Exception as e:
        sys.exit(1)

    print("\nSUCCESS: All AI Copilot features successfully verified!")

if __name__ == "__main__":
    verify()
