#!/usr/bin/env python3
"""
Integration test to verify GET /api/trips/ returns valid TripOut responses.
Tests the actual endpoint with database trips.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app import models, schemas
from app.routers.trips import get_user_trips
from datetime import datetime, timedelta
from unittest.mock import Mock

def test_get_user_trips_endpoint():
    """Test that GET /api/trips/ returns valid serialized trips"""
    print("\n" + "=" * 70)
    print("Testing GET /api/trips/ endpoint with database trips")
    print("=" * 70)
    
    db = SessionLocal()
    
    # Clear and create test data
    db.query(models.Trip).delete()
    db.query(models.User).delete()
    db.commit()
    
    # Create test user
    user = models.User(
        name="Test User",
        email="test@example.com",
        hashed_password="test_hash"
    )
    db.add(user)
    db.flush()
    user_id = user.id
    
    # Create destination
    dest = models.Destination(
        name="Chennai",
        state="Tamil Nadu",
        category="Beach",
        avg_travel_cost=5000,
        avg_hotel_cost=2000,
        avg_food_cost=500,
        avg_activity_cost=300,
        rating=4.5,
        best_season="January",
        description="Beach city",
        attractions=["Marina Beach"],
        budget_tier="Budget",
        recommended_duration=3,
        comfort_level=3
    )
    db.add(dest)
    db.flush()
    dest_id = dest.id
    
    # Create trip1
    trip1 = models.Trip(
        user_id=user_id,
        destination_id=dest_id,
        budget=50000,
        days=5,
        travelers_count=2,
        travel_type="Beach",
        comfort_score=70,
        total_estimated_cost=45000,
        hotel_tier="3-star",
        transport_mode="Flight",
        status="Planned",
        created_at=datetime.now()
    )
    db.add(trip1)
    db.flush()
    trip1_id = trip1.id
    
    # Create budget allocation for trip1
    ba1 = models.BudgetAllocation(
        trip_id=trip1_id,
        transport_cost=10000,
        hotel_cost=15000,
        food_cost=5000,
        activities_cost=3000,
        local_transport_cost=2000,
        taxes_fees_cost=5000,
        emergency_reserve=5000
    )
    db.add(ba1)
    
    # Create trip2
    trip2 = models.Trip(
        user_id=user_id,
        destination_id=dest_id,
        budget=60000,
        days=7,
        travelers_count=3,
        travel_type="Adventure",
        comfort_score=50,
        total_estimated_cost=55000,
        hotel_tier="2-star",
        transport_mode="Train",
        status="Planned",
        created_at=datetime.now() - timedelta(hours=1)
    )
    db.add(trip2)
    db.flush()
    trip2_id = trip2.id
    
    # Create budget allocation for trip2
    ba2 = models.BudgetAllocation(
        trip_id=trip2_id,
        transport_cost=8000,
        hotel_cost=18000,
        food_cost=7000,
        activities_cost=5000,
        local_transport_cost=2000,
        taxes_fees_cost=8000,
        emergency_reserve=7000
    )
    db.add(ba2)
    
    db.commit()
    
    print(f"✓ Created test user: {user_id}")
    print(f"✓ Created test destination: {dest_id}")
    print(f"✓ Created trips: {trip1_id}, {trip2_id}")
    
    # Now test the endpoint
    db2 = SessionLocal()
    
    # Mock current user
    mock_user = Mock()
    mock_user.id = user_id
    
    print("\nCalling get_user_trips()...")
    
    # Call the endpoint function directly
    result = get_user_trips(current_user=mock_user, db=db2)
    
    print(f"\n✓ get_user_trips() returned {len(result)} trips")
    
    # Verify each trip can be validated as TripOut
    for i, trip_dict in enumerate(result):
        print(f"\nTrip {i+1} (ID: {trip_dict.get('id')}):")
        print(f"  - Destination: {trip_dict.get('destination', {}).get('name', 'MISSING')}")
        print(f"  - Transport Mode: {trip_dict.get('transport_mode', 'MISSING')}")
        print(f"  - Status: {trip_dict.get('status', 'MISSING')}")
        
        # Validate carbon_footprint fields
        cf = trip_dict.get("carbon_footprint")
        if cf:
            print(f"  - Carbon Footprint:")
            print(f"    • transport_mode: {cf.get('transport_mode', 'MISSING')}")
            print(f"    • co2_emissions: {cf.get('co2_emissions', 'MISSING')}")
            print(f"    • carbon_rating: {cf.get('carbon_rating', 'MISSING')}")
            print(f"    • eco_score: {cf.get('eco_score', 'MISSING')}")
            print(f"    • alternative_savings: {cf.get('alternative_savings', 'MISSING')}")
            
            # Verify all required fields are present
            required_fields = ["transport_mode", "co2_emissions", "carbon_rating", "eco_score", "alternative_savings"]
            for field in required_fields:
                if field not in cf:
                    raise ValueError(f"Missing required field in carbon_footprint: {field}")
        else:
            print(f"  - Carbon Footprint: None")
        
        # Try to validate as TripOut schema
        try:
            validated = schemas.TripOut(**trip_dict)
            print(f"  ✓ Validated as TripOut schema")
        except Exception as e:
            print(f"  ✗ Schema validation failed: {e}")
            print(f"  Trip data: {trip_dict}")
            raise
    
    db2.close()
    db.close()
    
    print("\n" + "=" * 70)
    print("✓ GET /api/trips/ integration test PASSED")
    print("=" * 70)
    print("\nResults:")
    print(f"  • {len(result)} trips returned successfully")
    print("  • All trips have required fields")
    print("  • All carbon_footprint objects have correct schema")
    print("  • All trips validate as TripOut schema")

def main():
    try:
        test_get_user_trips_endpoint()
        return 0
    except Exception as e:
        print(f"\n✗ Integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
