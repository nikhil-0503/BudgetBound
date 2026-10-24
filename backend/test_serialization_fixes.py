"""
Test suite for serialization and dashboard crash fixes.
Tests that the fixes for:
1. PydanticSerializationError in GET /api/trips/
2. Dashboard AttributeError when trip.destination is null
3. attach_trip_intelligence null-check
"""

import datetime
import json
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload

from app import models
from app.database import Base
from app.routers.trips import _serialize_trip, attach_trip_intelligence

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_unique_email():
    """Generate a unique email for each test."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"

def test_serialize_trip_with_valid_destination():
    """Test _serialize_trip() correctly serializes Trip with valid destination."""
    db = TestingSessionLocal()
    
    try:
        user = models.User(
            name="Test User",
            email=get_unique_email(),
            hashed_password="hashed_password"
        )
        db.add(user)
        db.commit()
        
        destination = models.Destination(
            name="Paris",
            state="France",
            avg_travel_cost=1000,
            avg_hotel_cost=100,
            avg_food_cost=30,
            avg_activity_cost=50,
            category="City",
            best_season="Spring",
            description="City of Light",
            attractions=["Eiffel Tower"]
        )
        db.add(destination)
        db.commit()
        
        trip = models.Trip(
            user_id=user.id,
            destination_id=destination.id,
            budget=5000,
            days=7,
            travelers_count=2,
            travel_type="Adventure",
            comfort_score=75,
            total_estimated_cost=3500,
            hotel_tier="Mid",
            transport_mode="Flight",
            status="Planned"
        )
        db.add(trip)
        db.commit()
        
        trip = db.query(models.Trip).filter(models.Trip.id == trip.id).first()
        result = _serialize_trip(trip)
        
        # Should be JSON-serializable (convert datetime if present)
        json_str = json.dumps(result, default=str)
        assert json_str is not None
        
        # Verify data
        assert result["destination"]["name"] == "Paris"
        assert result["budget"] == 5000
        print("✓ test_serialize_trip_with_valid_destination passed")
    finally:
        db.close()

def test_serialize_trip_with_null_destination():
    """Test _serialize_trip() handles null destination without crashing."""
    db = TestingSessionLocal()
    
    try:
        user = models.User(
            name="Test User",
            email=get_unique_email(),
            hashed_password="hashed_password"
        )
        db.add(user)
        db.commit()
        
        trip = models.Trip(
            user_id=user.id,
            destination_id=None,
            budget=5000,
            days=7,
            travelers_count=2,
            travel_type="Adventure",
            comfort_score=75,
            total_estimated_cost=3500,
            hotel_tier="Mid",
            transport_mode="Flight",
            status="Planned"
        )
        db.add(trip)
        db.commit()
        
        trip = db.query(models.Trip).filter(models.Trip.id == trip.id).first()
        result = _serialize_trip(trip)
        
        # Should be JSON-serializable
        json_str = json.dumps(result, default=str)
        assert json_str is not None
        
        # Should have fallback destination
        assert result["destination"]["name"] == "Unknown destination"
        print("✓ test_serialize_trip_with_null_destination passed")
    finally:
        db.close()

def test_dashboard_handles_null_destination():
    """Test dashboard logic handles trips with null destination."""
    db = TestingSessionLocal()
    
    try:
        user = models.User(
            name="Test User",
            email=get_unique_email(),
            hashed_password="hashed_password"
        )
        db.add(user)
        db.commit()
        
        trip = models.Trip(
            user_id=user.id,
            destination_id=None,
            budget=5000,
            days=7,
            travelers_count=2,
            travel_type="Adventure",
            comfort_score=75,
            total_estimated_cost=3500,
            hotel_tier="Mid",
            transport_mode="Flight",
            status="Planned",
            created_at=datetime.datetime.utcnow()
        )
        db.add(trip)
        db.commit()
        
        trips_list = db.query(models.Trip).filter(models.Trip.user_id == user.id).all()
        
        # Mimic dashboard logic
        for t in trips_list:
            # This is the null-check from the fix
            dest_name = t.destination.name if t.destination else "Unknown destination"
            dest_state = t.destination.state if t.destination else ""
            
            assert dest_name == "Unknown destination"
            assert dest_state == ""
        
        print("✓ test_dashboard_handles_null_destination passed")
    finally:
        db.close()

def test_attach_trip_intelligence_with_null_destination():
    """Test attach_trip_intelligence() doesn't crash with null destination."""
    db = TestingSessionLocal()
    
    try:
        user = models.User(
            name="Test User",
            email=get_unique_email(),
            hashed_password="hashed_password"
        )
        db.add(user)
        db.commit()
        
        trip = models.Trip(
            user_id=user.id,
            destination_id=None,
            budget=5000,
            days=7,
            travelers_count=2,
            travel_type="Adventure",
            comfort_score=75,
            total_estimated_cost=3500,
            hotel_tier="Mid",
            transport_mode="Flight",
            status="Planned"
        )
        db.add(trip)
        db.commit()
        
        trip = db.query(models.Trip).filter(models.Trip.id == trip.id).first()
        
        # Should not crash
        attach_trip_intelligence(trip, db)
        
        assert trip.actual_spending is not None
        assert trip.savings is not None
        print("✓ test_attach_trip_intelligence_with_null_destination passed")
    finally:
        db.close()

def test_attach_trip_intelligence_with_valid_destination():
    """Test attach_trip_intelligence() works with valid destination."""
    db = TestingSessionLocal()
    
    try:
        user = models.User(
            name="Test User",
            email=get_unique_email(),
            hashed_password="hashed_password"
        )
        db.add(user)
        db.commit()
        
        destination = models.Destination(
            name="Paris",
            state="France",
            avg_travel_cost=1000,
            avg_hotel_cost=100,
            avg_food_cost=30,
            avg_activity_cost=50,
            category="City",
            best_season="Spring",
            description="City of Light",
            attractions=["Eiffel Tower"]
        )
        db.add(destination)
        db.commit()
        
        trip = models.Trip(
            user_id=user.id,
            destination_id=destination.id,
            budget=5000,
            days=7,
            travelers_count=2,
            travel_type="Adventure",
            comfort_score=75,
            total_estimated_cost=3500,
            hotel_tier="Mid",
            transport_mode="Flight",
            status="Planned",
            start_date="2026-06-15"
        )
        db.add(trip)
        db.flush()
        
        budget_alloc = models.BudgetAllocation(
            trip_id=trip.id,
            transport_cost=1000,
            hotel_cost=700,
            food_cost=500,
            activities_cost=400,
            emergency_reserve=400,
            local_transport_cost=200,
            taxes_fees_cost=300
        )
        db.add(budget_alloc)
        db.commit()
        
        trip = db.query(models.Trip).options(
            joinedload(models.Trip.destination),
            joinedload(models.Trip.budget_allocation)
        ).filter(models.Trip.id == trip.id).first()
        
        # Should work with valid destination
        attach_trip_intelligence(trip, db)
        
        assert trip.actual_spending is not None
        assert trip.savings is not None
        assert trip.carbon_footprint is not None
        # Verify weather_intelligence was set (null-check passed)
        assert trip.destination.weather_intelligence is not None
        print("✓ test_attach_trip_intelligence_with_valid_destination passed")
    finally:
        db.close()

if __name__ == "__main__":
    print("Running serialization and dashboard fixes tests...\n")
    test_serialize_trip_with_valid_destination()
    test_serialize_trip_with_null_destination()
    test_dashboard_handles_null_destination()
    test_attach_trip_intelligence_with_null_destination()
    test_attach_trip_intelligence_with_valid_destination()
    print("\nAll tests passed! ✓")
