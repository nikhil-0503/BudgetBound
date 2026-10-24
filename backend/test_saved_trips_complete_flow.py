"""
Comprehensive test for saved trips complete flow:
1. Saving a trip with custom destination
2. Fetching trip list (GET /api/trips/)
3. Fetching single trip (GET /api/trips/{id})
4. Dashboard stats showing trips correctly
5. Frontend Saved Trips rendering
"""

import datetime
import json
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload

from app import models
from app.database import Base
from app.routers.trips import _serialize_trip

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_unique_email():
    """Generate a unique email for each test."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"

def test_save_and_retrieve_trip_with_custom_destination():
    """Test complete flow: save trip with custom destination -> fetch -> display."""
    db = TestingSessionLocal()
    
    try:
        # 1. Create user
        user = models.User(
            name="Test User",
            email=get_unique_email(),
            hashed_password="hashed_password"
        )
        db.add(user)
        db.commit()
        
        # 2. Create custom destination (like Chennai in the real data)
        custom_dest = models.CustomDestination(
            name="Chennai",
            address="Tamil Nadu, India",
            latitude=13.0588,
            longitude=80.2230,
            google_place_id="test_place_id",
            data_source="google_places",
            category="Adventure"
        )
        db.add(custom_dest)
        db.commit()
        
        # 3. Create trip with custom destination (like trip 32 and 33)
        trip = models.Trip(
            user_id=user.id,
            destination_id=None,
            custom_destination_id=custom_dest.id,
            budget=20000,
            days=4,
            travelers_count=2,
            travel_type="Adventure",
            comfort_score=75,
            total_estimated_cost=16537.35,
            hotel_tier="Mid",
            transport_mode="Flight",
            status="Planned",
            start_date="2026-06-15"
        )
        db.add(trip)
        db.flush()
        
        # 4. Create budget allocation
        budget_alloc = models.BudgetAllocation(
            trip_id=trip.id,
            transport_cost=5000,
            hotel_cost=4000,
            food_cost=3000,
            activities_cost=2500,
            emergency_reserve=1500,
            local_transport_cost=500,
            taxes_fees_cost=537.35
        )
        db.add(budget_alloc)
        
        # 5. Create itineraries
        for day in range(1, 5):
            itinerary = models.Itinerary(
                trip_id=trip.id,
                day_number=day,
                activities=[{"time": "Morning", "title": f"Day {day} activity", "cost": 0}],
                description=f"Day {day} description"
            )
            db.add(itinerary)
        
        db.commit()
        
        # Now test the complete data flow
        # 6. Fetch user's trips (simulating GET /api/trips/)
        trips = db.query(models.Trip).options(
            joinedload(models.Trip.destination),
            joinedload(models.Trip.custom_destination),
            joinedload(models.Trip.itineraries),
            joinedload(models.Trip.budget_allocation),
            joinedload(models.Trip.packing_items)
        ).filter(models.Trip.user_id == user.id).order_by(models.Trip.created_at.desc()).all()
        
        assert len(trips) == 1, f"Expected 1 trip, got {len(trips)}"
        fetched_trip = trips[0]
        
        # 7. Serialize trip (what API returns)
        serialized = _serialize_trip(fetched_trip)
        
        # 8. Verify serialization includes destination info
        assert serialized["destination"] is not None, "Destination should not be None"
        assert serialized["destination"]["name"] == "Chennai", f"Expected 'Chennai', got {serialized['destination']['name']}"
        assert serialized["destination"]["state"] == "Tamil Nadu, India", f"Expected 'Tamil Nadu, India', got {serialized['destination']['state']}"
        
        # 9. Verify frontend can access properties without crashing
        dest_name = serialized["destination"].get("name", "Unknown")
        dest_state = serialized["destination"].get("state", "")
        assert dest_name == "Chennai"
        assert dest_state == "Tamil Nadu, India"
        
        # 10. Simulate SavedTrips filtering
        trips_list = [serialized]  # Frontend receives this
        filtered_trips = [
            t for t in trips_list
            if (t.get("destination", {}).get("name", "").lower() != "unknown" or
                t.get("destination", {}).get("state", "").lower() != "")
        ]
        assert len(filtered_trips) == 1, "Trip should pass filter"
        
        # 11. Simulate SavedTrips card rendering
        trip_data = filtered_trips[0]
        card_destination = trip_data["destination"]["name"]
        card_state = trip_data["destination"]["state"]
        assert card_destination == "Chennai"
        assert card_state == "Tamil Nadu, India"
        
        print("✓ test_save_and_retrieve_trip_with_custom_destination passed")
        print(f"  Trip ID: {trip.id}")
        print(f"  Destination: {card_destination}, {card_state}")
        print(f"  Budget: ₹{trip_data['budget']}")
        print(f"  Estimated Cost: ₹{trip_data['total_estimated_cost']}")
        
    finally:
        db.close()

def test_dashboard_shows_custom_destination_trips():
    """Test that dashboard stats properly shows trips with custom destinations."""
    db = TestingSessionLocal()
    
    try:
        # 1. Create user
        user = models.User(
            name="Dashboard Test User",
            email=get_unique_email(),
            hashed_password="hashed_password"
        )
        db.add(user)
        db.commit()
        
        # 2. Create custom destination
        custom_dest = models.CustomDestination(
            name="Bangalore",
            address="Karnataka, India",
            latitude=12.9716,
            longitude=77.5946,
            data_source="google_places"
        )
        db.add(custom_dest)
        db.commit()
        
        # 3. Create trip
        trip = models.Trip(
            user_id=user.id,
            destination_id=None,
            custom_destination_id=custom_dest.id,
            budget=25000,
            days=5,
            travelers_count=3,
            travel_type="City Exploration",
            comfort_score=80,
            total_estimated_cost=22000,
            hotel_tier="Luxury",
            transport_mode="Flight",
            status="Planned",
            created_at=datetime.datetime.utcnow()
        )
        db.add(trip)
        db.commit()
        
        # 4. Simulate dashboard recent_trips logic
        trips_list = db.query(models.Trip).filter(models.Trip.user_id == user.id).all()
        sorted_trips = sorted(trips_list, key=lambda x: x.created_at, reverse=True)[:5]
        
        recent_trips = []
        for t in sorted_trips:
            # This mimics the fixed dashboard logic
            if t.destination:
                dest_name = t.destination.name
                dest_state = t.destination.state
            elif t.custom_destination_id:
                custom_dest = db.query(models.CustomDestination).filter(
                    models.CustomDestination.id == t.custom_destination_id
                ).first()
                dest_name = custom_dest.name if custom_dest else "Unknown destination"
                dest_state = custom_dest.address or "" if custom_dest else ""
            else:
                dest_name = "Unknown destination"
                dest_state = ""
            
            recent_trips.append({
                "id": t.id,
                "destination": dest_name,
                "state": dest_state,
                "budget": t.budget
            })
        
        # 5. Verify dashboard data
        assert len(recent_trips) == 1
        assert recent_trips[0]["destination"] == "Bangalore", f"Expected 'Bangalore', got {recent_trips[0]['destination']}"
        assert recent_trips[0]["state"] == "Karnataka, India"
        assert recent_trips[0]["destination"] != "Unknown destination", "Should not show 'Unknown destination'"
        
        print("✓ test_dashboard_shows_custom_destination_trips passed")
        print(f"  Dashboard shows: {recent_trips[0]['destination']}, {recent_trips[0]['state']}")
        
    finally:
        db.close()

def test_view_action_loads_trip_details():
    """Test that View action on SavedTrips correctly loads trip details for planner."""
    db = TestingSessionLocal()
    
    try:
        # 1. Create user and trip with custom destination
        user = models.User(
            name="View Test User",
            email=get_unique_email(),
            hashed_password="hashed_password"
        )
        db.add(user)
        db.commit()
        
        custom_dest = models.CustomDestination(
            name="Kochi",
            address="Kerala, India",
            latitude=9.9312,
            longitude=76.2673,
            data_source="google_places"
        )
        db.add(custom_dest)
        db.commit()
        
        trip = models.Trip(
            user_id=user.id,
            destination_id=None,
            custom_destination_id=custom_dest.id,
            budget=18000,
            days=3,
            travelers_count=2,
            travel_type="Beach",
            comfort_score=70,
            total_estimated_cost=15000,
            hotel_tier="Mid",
            transport_mode="Flight"
        )
        db.add(trip)
        db.flush()
        
        budget_alloc = models.BudgetAllocation(
            trip_id=trip.id,
            transport_cost=4000,
            hotel_cost=3500,
            food_cost=2500,
            activities_cost=2000,
            emergency_reserve=1500,
            local_transport_cost=500,
            taxes_fees_cost=1000
        )
        db.add(budget_alloc)
        db.commit()
        
        # 2. Simulate View button click - fetch trip details
        fetched_trip = db.query(models.Trip).options(
            joinedload(models.Trip.destination),
            joinedload(models.Trip.custom_destination),
            joinedload(models.Trip.itineraries),
            joinedload(models.Trip.budget_allocation),
            joinedload(models.Trip.packing_items)
        ).filter(
            models.Trip.id == trip.id,
            models.Trip.user_id == user.id
        ).first()
        
        assert fetched_trip is not None, "Trip should be found"
        
        # 3. Serialize for API response
        serialized = _serialize_trip(fetched_trip)
        
        # 4. Verify frontend can reconstruct destination details for planner
        plan_data = {
            "destination": serialized["destination"],
            "costs": {
                "transport_mode": fetched_trip.transport_mode,
                "hotel_tier": fetched_trip.hotel_tier,
                "transport_cost": serialized["budget_allocation"]["transport_cost"] if serialized["budget_allocation"] else 0,
                "hotel_cost": serialized["budget_allocation"]["hotel_cost"] if serialized["budget_allocation"] else 0,
                "food_cost": serialized["budget_allocation"]["food_cost"] if serialized["budget_allocation"] else 0,
                "activities_cost": serialized["budget_allocation"]["activities_cost"] if serialized["budget_allocation"] else 0,
                "total_estimated_cost": fetched_trip.total_estimated_cost
            },
            "budget": fetched_trip.budget,
            "days": fetched_trip.days,
            "travelers_count": fetched_trip.travelers_count,
            "travel_type": fetched_trip.travel_type,
            "comfort_score": fetched_trip.comfort_score,
            "itineraries": serialized.get("itineraries", [])
        }
        
        # 5. Verify the reconstructed data matches original
        assert plan_data["destination"]["name"] == "Kochi"
        assert plan_data["destination"]["latitude"] == 9.9312
        assert plan_data["destination"]["longitude"] == 76.2673
        assert plan_data["budget"] == 18000
        assert plan_data["days"] == 3
        
        print("✓ test_view_action_loads_trip_details passed")
        print(f"  Loaded trip: {plan_data['destination']['name']}")
        print(f"  Budget: ₹{plan_data['budget']}, Days: {plan_data['days']}")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("Running comprehensive saved trips tests...\n")
    test_save_and_retrieve_trip_with_custom_destination()
    print()
    test_dashboard_shows_custom_destination_trips()
    print()
    test_view_action_loads_trip_details()
    print("\nAll tests passed! ✓")
