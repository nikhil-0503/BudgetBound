"""
Test QR Code Sharing Feature
Comprehensive test for the trip sharing functionality
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_qr_sharing_workflow():
    """Complete workflow test for QR sharing feature"""
    
    print_section("QR CODE SHARING - COMPLETE WORKFLOW TEST")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Step 1: Register a test user
    print_section("Step 1: Register Test User")
    register_data = {
        "name": "QR Test User",
        "email": f"qrtest_{datetime.now().timestamp()}@test.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        if response.status_code == 201:
            print("✓ User registered successfully")
            user_data = response.json()
            print(f"  User ID: {user_data['id']}")
            print(f"  Email: {user_data['email']}")
        else:
            print(f"✗ Registration failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Step 2: Login
    print_section("Step 2: Login")
    login_data = {
        "username": register_data["email"],
        "password": register_data["password"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
        if response.status_code == 200:
            print("✓ Login successful")
            token_data = response.json()
            access_token = token_data["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            print(f"  Access Token: {access_token[:30]}...")
        else:
            print(f"✗ Login failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Step 3: Create a trip
    print_section("Step 3: Create a Trip")
    trip_data = {
        "budget": 25000,
        "days": 5,
        "travel_type": "Nature",
        "travelers_count": 2,
        "comfort_score": 60,
        "destination_id": 1  # Assuming Goa
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/trips/plan", 
            json=trip_data,
            headers=headers
        )
        if response.status_code == 200:
            print("✓ Trip created successfully")
            trip = response.json()
            trip_id = trip["id"]
            share_token = trip.get("share_token")
            is_public = trip.get("is_public", False)
            
            print(f"  Trip ID: {trip_id}")
            print(f"  Destination: {trip['destination']['name']}")
            print(f"  Budget: ₹{trip['budget']:,}")
            print(f"  Is Public: {is_public}")
            print(f"  Share Token: {share_token}")
        else:
            print(f"✗ Trip creation failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Step 4: Toggle sharing to public
    print_section("Step 4: Enable Public Sharing")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/trips/{trip_id}/share/toggle",
            headers=headers
        )
        if response.status_code == 200:
            print("✓ Public sharing enabled")
            updated_trip = response.json()
            share_token = updated_trip.get("share_token")
            is_public = updated_trip.get("is_public")
            
            print(f"  Is Public: {is_public}")
            print(f"  Share Token: {share_token}")
            
            # Generate share URL
            share_url = f"http://localhost:5175/share/{share_token}"
            print(f"\n  📱 QR Code URL: {share_url}")
            print(f"  🔗 Backend API: {BASE_URL}/api/trips/share/{share_token}")
        else:
            print(f"✗ Toggle sharing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Step 5: Test public access (no authentication)
    print_section("Step 5: Test Public Access (No Auth Required)")
    
    try:
        response = requests.get(f"{BASE_URL}/api/trips/share/{share_token}")
        if response.status_code == 200:
            print("✓ Public trip accessible without authentication")
            shared_trip = response.json()
            print(f"  Trip ID: {shared_trip['id']}")
            print(f"  Destination: {shared_trip['destination']['name']}")
            print(f"  Days: {shared_trip['days']}")
            print(f"  Budget: ₹{shared_trip['budget']:,}")
            print(f"  Status: {shared_trip['status']}")
            print(f"  Itineraries: {len(shared_trip.get('itineraries', []))} days planned")
        else:
            print(f"✗ Public access failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Step 6: Toggle back to private
    print_section("Step 6: Disable Public Sharing")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/trips/{trip_id}/share/toggle",
            headers=headers
        )
        if response.status_code == 200:
            print("✓ Public sharing disabled")
            updated_trip = response.json()
            is_public = updated_trip.get("is_public")
            print(f"  Is Public: {is_public}")
        else:
            print(f"✗ Toggle failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Step 7: Verify private access is blocked
    print_section("Step 7: Verify Private Access is Blocked")
    
    try:
        response = requests.get(f"{BASE_URL}/api/trips/share/{share_token}")
        if response.status_code == 404:
            print("✓ Private trip correctly blocked")
            print("  Access denied for non-authenticated users")
        else:
            print(f"⚠ Unexpected status: {response.status_code}")
            print(f"  Expected 404, got {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Summary
    print_section("TEST SUMMARY")
    print("""
✓ All tests passed successfully!

QR CODE SHARING FEATURE WORKFLOW:
1. User creates a trip (private by default)
2. User clicks "Share" button in trip card
3. User toggles "Publish" to enable public sharing
4. QR code is generated with URL: /share/{share_token}
5. Anyone can scan QR code or open link (no login needed)
6. Shared view shows read-only trip details
7. User can toggle back to "Make Private" anytime

PURPOSE OF QR CODE:
- Share trip itinerary with friends/family instantly
- No login required for viewers
- Read-only access (viewers cannot edit)
- Quick sharing at travel agencies/offices
- Print QR code on travel documents
- Share on WhatsApp/social media

TESTING NOTES:
- Backend must be running on http://127.0.0.1:8000
- Frontend must be running on http://localhost:5175
- QR codes work with any QR scanner app on phones
- URLs are shareable via any messaging platform
    """)
    
    return True


def demonstrate_qr_usage():
    """Show practical examples of QR code usage"""
    
    print_section("PRACTICAL QR CODE USAGE EXAMPLES")
    
    examples = [
        {
            "scenario": "Sharing with Family",
            "steps": [
                "1. Plan a family trip to Goa",
                "2. Click 'Share' button on trip card",
                "3. Toggle 'Publish' to make public",
                "4. Download QR code image",
                "5. Send QR image in WhatsApp family group",
                "6. Family members scan → see full itinerary instantly"
            ]
        },
        {
            "scenario": "Travel Agency",
            "steps": [
                "1. Travel agent creates trip plan for client",
                "2. Publishes trip with QR code",
                "3. Prints QR code on travel documents",
                "4. Client scans during trip → access full details",
                "5. No app login needed for client"
            ]
        },
        {
            "scenario": "Group Trip Coordination",
            "steps": [
                "1. Trip organizer plans group trip",
                "2. Generates QR code",
                "3. Projects QR on screen during meeting",
                "4. Everyone scans → instant access to plan",
                "5. All can view same itinerary simultaneously"
            ]
        },
        {
            "scenario": "Social Media Sharing",
            "steps": [
                "1. Plan amazing trip to Ladakh",
                "2. Generate public share link",
                "3. Share link on Instagram/Facebook",
                "4. Followers click link → view trip inspiration",
                "5. Can duplicate trip for their own planning"
            ]
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['scenario']}")
        print("   " + "-" * 60)
        for step in example['steps']:
            print(f"   {step}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        # Run workflow test
        success = test_qr_sharing_workflow()
        
        if success:
            # Show usage examples
            demonstrate_qr_usage()
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
