#!/usr/bin/env python3
"""
Test AI Chat endpoint
"""

import requests

BASE_URL = "http://127.0.0.1:8000"

# First login to get token
print("🔐 Logging in...")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login-json",
    json={"email": "test_user_1791555598@example.com", "password": "TestPass123!"}
)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"✅ Login successful\n")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "What are the top 3 budget-friendly beach destinations in India?"
            }
        ]
    }
    
    print("💬 Testing AI Chat...")
    print(f"Request: {payload['messages'][0]['content']}\n")
    
    response = requests.post(
        f"{BASE_URL}/api/ai/chat",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        reply = data.get("reply", "")
        print(f"\n✅ AI Chat Working!\n")
        print(f"Response:\n{reply}")
    else:
        print(f"\n❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")
else:
    print(f"❌ Login failed: {login_response.status_code}")
