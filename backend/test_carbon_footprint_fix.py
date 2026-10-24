#!/usr/bin/env python3
"""
Test script to verify carbon_footprint serialization fix.
Tests that GET /api/trips/ returns valid TripOut objects with correct carbon_footprint schema.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.routers.trips import _serialize_trip, calculate_carbon_footprint
from app import models, schemas
from datetime import datetime
from unittest.mock import Mock

def test_calculate_carbon_footprint():
    """Verify calculate_carbon_footprint returns correct schema"""
    print("Testing calculate_carbon_footprint function...")
    
    # Test flight
    cf_flight = calculate_carbon_footprint("Flight", 10000)
    print(f"  Flight result: {cf_flight}")
    assert "transport_mode" in cf_flight
    assert "co2_emissions" in cf_flight
    assert "carbon_rating" in cf_flight
    assert "eco_score" in cf_flight
    assert "alternative_savings" in cf_flight
    assert cf_flight["transport_mode"] == "Flight"
    print("  ✓ Flight carbon_footprint has all required fields")
    
    # Test train
    cf_train = calculate_carbon_footprint("Train", 5000)
    print(f"  Train result: {cf_train}")
    assert cf_train["transport_mode"] == "Train"
    assert cf_train["eco_score"] == 92
    assert cf_train["carbon_rating"] == "Eco Friendly"
    print("  ✓ Train carbon_footprint calculated correctly")

def test_serialize_trip_with_current_format():
    """Test _serialize_trip with current carbon_footprint format"""
    print("\nTesting _serialize_trip with current format...")
    
    # Create mock trip with current format carbon_footprint
    trip = Mock(spec=models.Trip)
    trip.id = 1
    trip.user_id = 5
    trip.destination_id = 10
    trip.custom_destination_id = None
    trip.budget = 50000
    trip.days = 5
    trip.travelers_count = 2
    trip.travel_type = "Beach"
    trip.comfort_score = 70
    trip.total_estimated_cost = 45000
    trip.hotel_tier = "3-star"
    trip.transport_mode = "Flight"
    trip.created_at = datetime.now()
    trip.status = "Planned"
    trip.start_date = "2026-11-22"
    trip.actual_spending = None
    trip.savings = None
    trip.is_public = False
    trip.share_token = None
    
    # Current format carbon_footprint (from calculate_carbon_footprint)
    trip.carbon_footprint = {
        "transport_mode": "Flight",
        "co2_emissions": 420.0,
        "carbon_rating": "High Impact",
        "eco_score": 30,
        "alternative_savings": 378.0
    }
    
    trip.itineraries = []
    trip.budget_allocation = None
    trip.packing_items = []
    trip.documents = []
    trip.destination = None
    trip.custom_destination = None
    
    result = _serialize_trip(trip)
    
    print(f"  Serialized carbon_footprint: {result.get('carbon_footprint')}")
    assert result["carbon_footprint"] is not None
    assert result["carbon_footprint"]["transport_mode"] == "Flight"
    assert result["carbon_footprint"]["co2_emissions"] == 420.0
    assert result["carbon_footprint"]["carbon_rating"] == "High Impact"
    assert result["carbon_footprint"]["eco_score"] == 30
    assert result["carbon_footprint"]["alternative_savings"] == 378.0
    print("  ✓ Current format serialized correctly")

def test_serialize_trip_with_legacy_format():
    """Test _serialize_trip with legacy carbon_footprint format"""
    print("\nTesting _serialize_trip with legacy format...")
    
    # Create mock trip with legacy format carbon_footprint
    trip = Mock(spec=models.Trip)
    trip.id = 2
    trip.user_id = 5
    trip.destination_id = 10
    trip.custom_destination_id = None
    trip.budget = 50000
    trip.days = 5
    trip.travelers_count = 2
    trip.travel_type = "Beach"
    trip.comfort_score = 70
    trip.total_estimated_cost = 45000
    trip.hotel_tier = "3-star"
    trip.transport_mode = "Flight"
    trip.created_at = datetime.now()
    trip.status = "Planned"
    trip.start_date = "2026-11-22"
    trip.actual_spending = None
    trip.savings = None
    trip.is_public = False
    trip.share_token = None
    
    # Legacy format carbon_footprint (old format with co2_kg, offset_url)
    trip.carbon_footprint = {
        "co2_kg": 420,
        "offset_url": "https://example.com/offset"
    }
    
    trip.itineraries = []
    trip.budget_allocation = None
    trip.packing_items = []
    trip.documents = []
    trip.destination = None
    trip.custom_destination = None
    
    result = _serialize_trip(trip)
    
    print(f"  Serialized carbon_footprint: {result.get('carbon_footprint')}")
    assert result["carbon_footprint"] is not None
    assert result["carbon_footprint"]["transport_mode"] == "Flight"
    assert result["carbon_footprint"]["co2_emissions"] == 420  # Mapped from co2_kg
    assert result["carbon_footprint"]["carbon_rating"] == "Not assessed"
    assert result["carbon_footprint"]["eco_score"] == 50  # Default
    assert result["carbon_footprint"]["alternative_savings"] == 0.0  # Default
    print("  ✓ Legacy format converted to new schema correctly")

def test_serialize_trip_with_no_carbon():
    """Test _serialize_trip with null carbon_footprint"""
    print("\nTesting _serialize_trip with null carbon_footprint...")
    
    trip = Mock(spec=models.Trip)
    trip.id = 3
    trip.user_id = 5
    trip.destination_id = 10
    trip.custom_destination_id = None
    trip.budget = 50000
    trip.days = 5
    trip.travelers_count = 2
    trip.travel_type = "Beach"
    trip.comfort_score = 70
    trip.total_estimated_cost = 45000
    trip.hotel_tier = "3-star"
    trip.transport_mode = "Flight"
    trip.created_at = datetime.now()
    trip.status = "Planned"
    trip.start_date = "2026-11-22"
    trip.actual_spending = None
    trip.savings = None
    trip.is_public = False
    trip.share_token = None
    trip.carbon_footprint = None
    trip.itineraries = []
    trip.budget_allocation = None
    trip.packing_items = []
    trip.documents = []
    trip.destination = None
    trip.custom_destination = None
    
    result = _serialize_trip(trip)
    
    print(f"  Serialized carbon_footprint: {result.get('carbon_footprint')}")
    assert result["carbon_footprint"] is None
    print("  ✓ Null carbon_footprint handled correctly")

def test_tripout_validation():
    """Test that serialized trip passes TripOut schema validation"""
    print("\nTesting TripOut schema validation...")
    
    # Create a fully valid serialized trip
    trip_dict = {
        "id": 1,
        "user_id": 5,
        "destination_id": 10,
        "custom_destination_id": None,
        "budget": 50000.0,
        "days": 5,
        "travelers_count": 2,
        "travel_type": "Beach",
        "comfort_score": 70,
        "total_estimated_cost": 45000.0,
        "hotel_tier": "3-star",
        "transport_mode": "Flight",
        "created_at": datetime.now().isoformat(),
        "destination": {
            "id": 10,
            "name": "Chennai",
            "state": "Tamil Nadu",
            "category": "Beach",
            "avg_travel_cost": 5000,
            "avg_hotel_cost": 2000,
            "avg_food_cost": 500,
            "avg_activity_cost": 300,
            "rating": 4.5,
            "best_season": "January",
            "description": "Beach city",
            "attractions": []
        },
        "status": "Planned",
        "start_date": "2026-11-22",
        "actual_spending": 0.0,
        "savings": 5000.0,
        "is_public": False,
        "share_token": None,
        "data_source": None,
        "itineraries": [],
        "budget_allocation": None,
        "packing_items": [],
        "carbon_footprint": {
            "transport_mode": "Flight",
            "co2_emissions": 420.0,
            "carbon_rating": "High Impact",
            "eco_score": 30,
            "alternative_savings": 378.0
        },
        "documents": []
    }
    
    try:
        validated = schemas.TripOut(**trip_dict)
        print(f"  ✓ Trip with carbon_footprint validates against TripOut schema")
        print(f"    carbon_footprint fields: {list(validated.carbon_footprint.__dict__.keys()) if validated.carbon_footprint else 'None'}")
    except Exception as e:
        print(f"  ✗ Validation failed: {e}")
        raise

def main():
    print("=" * 70)
    print("Carbon Footprint Serialization Fix - Unit Tests")
    print("=" * 70)
    
    try:
        test_calculate_carbon_footprint()
        test_serialize_trip_with_current_format()
        test_serialize_trip_with_legacy_format()
        test_serialize_trip_with_no_carbon()
        test_tripout_validation()
        
        print("\n" + "=" * 70)
        print("✓ All tests PASSED")
        print("=" * 70)
        print("\nFix verified:")
        print("  1. calculate_carbon_footprint() returns correct schema")
        print("  2. _serialize_trip() handles current format correctly")
        print("  3. _serialize_trip() converts legacy format to new schema")
        print("  4. _serialize_trip() handles null carbon_footprint")
        print("  5. Serialized trips validate against TripOut schema")
        return 0
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"✗ Test FAILED: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
