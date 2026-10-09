#!/usr/bin/env python3
"""
Test Groq API connectivity
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv('backend/.env')

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")  # Try an available model
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

print("="*60)
print("Testing Groq API Connection")
print("="*60)
print(f"API Key: {GROQ_API_KEY[:20]}...{GROQ_API_KEY[-10:]}")
print(f"Model: {GROQ_MODEL}")
print(f"API URL: {GROQ_API_URL}")
print("="*60)

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json",
}

payload = {
    "model": GROQ_MODEL,
    "messages": [
        {"role": "user", "content": "Say hello in one word"}
    ],
    "max_tokens": 10
}

try:
    print("\n🔄 Sending test request...")
    with httpx.Client(timeout=30.0) as client:
        response = client.post(GROQ_API_URL, headers=headers, json=payload)
        
    print(f"\n📊 Response Status: {response.status_code}")
    print(f"📄 Response Headers:")
    for key, value in response.headers.items():
        if key.lower() in ['content-type', 'x-ratelimit-remaining', 'x-ratelimit-limit']:
            print(f"   {key}: {value}")
    
    if response.status_code == 200:
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        print(f"\n✅ SUCCESS!")
        print(f"💬 AI Response: '{reply}'")
        print(f"\n✅ Groq API is working correctly!")
    else:
        print(f"\n❌ FAILED!")
        print(f"📄 Response Body:")
        print(response.text)
        
        if response.status_code == 401:
            print("\n🔑 Authentication Error - API key is invalid or expired")
        elif response.status_code == 404:
            print("\n🔍 Model Not Found - The model may not exist or be unavailable")
            print(f"   Tried model: {GROQ_MODEL}")
        elif response.status_code == 429:
            print("\n⏱️ Rate Limit Exceeded - Too many requests")
        elif response.status_code == 500:
            print("\n🔧 Server Error - Groq API is experiencing issues")
            
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"   Type: {type(e).__name__}")

print("\n" + "="*60)
