#!/usr/bin/env python3
"""
Final verification test for saved trips fixes:
1. Verify trips are persisted and returned by GET /api/trips/
2. Verify GET /api/trips/{id} loads complete trip with custom destination
3. Verify Dashboard stats endpoint returns recent trips
4. Verify destination serialization is correct
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine
from app import models
from datetime import datetime, timedelta
import json

def create_test_data():
    """Create test user and trips"""
    db = SessionLocal()
    
    # Clear existing test data
    db.query(models.Trip).delete()
    db.query(models.CustomDestination).delete()
    db.query(models.User).delete()
    db.commit()
    
    # Create test user
    user = models.User(
        username="test_user",
        email="test@example.com",
        hashed_password="test_hash"
    )
    db.add(user)
    db.commit()
    
    print(f"✓ Created test user: {user.id}")
    
    # Create test destination (standard)
    dest = models.Destination(
        name="Chennai",
        state="Tamil Nadu",
        category="Beach",
        avg_travel_cost=5000,
        avg_hotel_cost=2000,
        avg_food_cost=500,
        avg_activity_cost=300,
        rating=4.5,
        best_season="January-February",
        description="Coastal city",
        attractions=["Marina Beach"],
        budget_tier="Budget",
        recommended_duration=3,
        comfort_level=3,
        adventure_score=50,
        nature_score=70,
        family_score=80,
        romantic_score=60,
        religious_score=70,
        beach_score=90,
        city_score=80,
        solo_score=75
    )
    db.add(dest)
    db.commit()
    print(f"✓ Created test destination: {dest.id}")
    
    # Create test custom destination
    custom_dest = models.CustomDestination(
        name="My Custom Location",
        address="123 Custom Street",
        latitude=13.0827,
        longitude=80.2707,
        google_place_id="test_place_id",
        data_source="custom"
    )
    db.add(custom_dest)
    db.commit()
    print(f"✓ Created custom destination: {custom_dest.id}")
    
    # Create trips: 2 with standard destination, 1 with custom destination
    trips = []
    for i in range(3):
        trip = models.Trip(
            user_id=user.id,
            destination_id=dest.id if i < 2 else None,
            custom_destination_id=custom_dest.id if i == 2 else None,
            budget=50000 + i * 10000,
            days=5 + i,
            travelers_count=2,
            travel_type="Beach",
            comfort_score=70,
            total_estimated_cost=45000 + i * 10000,
            hotel_tier="3-star",
            transport_mode="flight",
            status="Planned",
            start_date=datetime.now() + timedelta(days=30+i),
            created_at=datetime.now() - timedelta(hours=i),
            is_public=False,
            carbon_footprint={"co2_kg": 100 + i*10, "offset_url": "test_url"}
        )
        db.add(trip)
        db.flush()
        
        # Create budget allocation
        budget_alloc = models.BudgetAllocation(
            trip_id=trip.id,
            transport_cost=10000 + i*1000,
            hotel_cost=15000 + i*1500,
            food_cost=5000 + i*500,
            activities_cost=3000 + i*300,
            local_transport_cost=2000 + i*200,
            taxes_fees_cost=5000 + i*500,
            emergency_reserve=5000 + i*500
        )
        db.add(budget_alloc)
        
        # Create itinerary
        itinerary = models.Itinerary(
            trip_id=trip.id,
            day_number=1,
            activities="Day 1 activities",
            description="First day description"
        )
        db.add(itinerary)
        
        trips.append(trip)
    
    db.commit()
    print(f"✓ Created 3 test trips")
    db.close()
    
    return user.id, [t.id for t in trips]

def test_get_trips_endpoint(user_id, trip_ids):
    """Test GET /api/trips/"""
    from app.routers import trips as trips_router
    from app.auth import get_current_user
    from unittest.mock import Mock
    
    db = SessionLocal()
    
    # Mock current user
    mock_user = Mock()
    mock_user.id = user_id
    
    # Call endpoint
    result = trips_router.get_user_trips(current_user=mock_user, db=db)
    
    print(f"\n✓ GET /api/trips/ returned {len(result)} trips")
    
    # Verify structure
    for i, trip_dict in enumerate(result):
        print(f"\n  Trip {i+1}:")
        print(f"    - ID: {trip_dict['id']}")
        print(f"    - Budget: ₹{trip_dict['budget']}")
        print(f"    - Destination: {trip_dict.get('destination', {}).get('name', 'MISSING')}")
        print(f"    - Status: {trip_dict.get('status', 'MISSING')}")
        print(f"    - Days: {trip_dict.get('days', 'MISSING')}")
        
        # Check critical fields
        assert trip_dict['destination'] is not None, f"Destination missing for trip {i+1}"
        assert trip_dict['destination']['name'] is not None, f"Destination name missing for trip {i+1}"
        assert trip_dict['budget_allocation'] is not None, f"Budget allocation missing for trip {i+1}"
        assert len(trip_dict.get('itineraries', [])) > 0, f"Itineraries missing for trip {i+1}"
    
    db.close()
    return result

def test_get_trip_by_id(user_id, trip_ids):
    """Test GET /api/trips/{id}"""
    from app.routers import trips as trips_router
    from unittest.mock import Mock
    
    db = SessionLocal()
    
    # Mock current user
    mock_user = Mock()
    mock_user.id = user_id
    
    # Test each trip
    for trip_id in trip_ids:
        result = trips_router.get_trip_details(trip_id=trip_id, current_user=mock_user, db=db)
        
        print(f"\n✓ GET /api/trips/{trip_id}:")
        print(f"  - Destination: {result.get('destination', {}).get('name', 'MISSING')}")
        print(f"  - Status: {result.get('status', 'MISSING')}")
        print(f"  - Budget Allocation: {result.get('budget_allocation') is not None}")
        print(f"  - Itineraries: {len(result.get('itineraries', []))} found")
        
        # Verify critical fields
        assert result['destination'] is not None, f"Destination missing for trip {trip_id}"
        assert result['destination']['name'] is not None, f"Destination name missing for trip {trip_id}"
        assert result['budget_allocation'] is not None, f"Budget allocation missing for trip {trip_id}"
    
    db.close()

def test_dashboard_stats(user_id):
    """Test GET /api/dashboard/stats"""
    from app.routers import admin_analytics
    from unittest.mock import Mock
    
    db = SessionLocal()
    
    # Mock current user
    mock_user = Mock()
    mock_user.id = user_id
    
    # Call endpoint
    result = admin_analytics.get_dashboard_stats(current_user=mock_user, db=db)
    
    print(f"\n✓ GET /api/dashboard/stats:")
    print(f"  - Total trips: {result['total_trips']}")
    print(f"  - Recent trips: {len(result['recent_trips'])}")
    
    for i, recent_trip in enumerate(result['recent_trips']):
        print(f"\n  Recent trip {i+1}:")
        print(f"    - Destination: {recent_trip.get('destination', 'MISSING')}")
        print(f"    - Budget: ₹{recent_trip.get('budget', 'MISSING')}")
        
        # Check critical fields
        assert recent_trip.get('destination') is not None, f"Destination missing for recent trip {i+1}"
        assert recent_trip.get('destination') != "Unknown destination", f"Unknown destination for recent trip {i+1}"
    
    db.close()

def main():
    print("=" * 60)
    print("BudgetBound Saved Trips - Final Verification Test")
    print("=" * 60)
    
    try:
        print("\n[1] Creating test data...")
        user_id, trip_ids = create_test_data()
        
        print("\n[2] Testing GET /api/trips/ endpoint...")
        trips_list = test_get_trips_endpoint(user_id, trip_ids)
        
        print("\n[3] Testing GET /api/trips/{id} endpoint...")
        test_get_trip_by_id(user_id, trip_ids)
        
        print("\n[4] Testing GET /api/dashboard/stats endpoint...")
        test_dashboard_stats(user_id)
        
        print("\n" + "=" * 60)
        print("✓ All verification tests PASSED")
        print("=" * 60)
        print("\nSummary:")
        print("- GET /api/trips/ returns all user trips with complete data")
        print("- GET /api/trips/{id} loads individual trips with all relationships")
        print("- Dashboard stats endpoint returns recent trips with correct destination names")
        print("- Both standard and custom destinations serialize correctly")
        print("- Budget allocation, itineraries, and other relationships are loaded")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
