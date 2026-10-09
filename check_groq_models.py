#!/usr/bin/env python3
"""
Check available Groq models
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv('backend/.env')

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"

print("="*60)
print("Checking Available Groq Models")
print("="*60)

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json",
}

try:
    with httpx.Client(timeout=30.0) as client:
        response = client.get(GROQ_MODELS_URL, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        models = data.get("data", [])
        
        print(f"\n✅ Found {len(models)} available models:\n")
        
        for model in models:
            model_id = model.get("id", "unknown")
            print(f"  • {model_id}")
            
        print("\n" + "="*60)
        print("💡 Recommended models for chat:")
        print("  • llama-3.3-70b-versatile")
        print("  • llama-3.1-70b-versatile")
        print("  • llama3-70b-8192")
        print("  • gemma2-9b-it")
        print("  • mixtral-8x7b-32768")
        
    else:
        print(f"\n❌ Failed to fetch models: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n" + "="*60)
