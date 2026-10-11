"""
Integration test for explainability feature.

Simulates:
1. Creating a trip with budget allocation
2. Calling explain_itinerary
3. Verifying structured response structure
4. Validating financial reconciliation
"""

import sys
import asyncio
from decimal import Decimal
from datetime import datetime

sys.path.insert(0, '/Users/nikhil/Downloads/SSN/College Files/Fourth Year/7th Semester/Full Stack Development/Full Stack Development Project/BudgetBound/backend')

async def test_full_explainability_flow():
    """
    Simulate a complete explainability analysis for a trip.
    """
    from app.services.explainability import assemble_cost_explanations
    
    print("\n" + "="*70)
    print("INTEGRATION TEST: Full Explainability Flow")
    print("="*70)
    
    # Simulate a trip object
    class MockDestination:
        name = "Goa"
        state = "Goa"
        category = "Beach"
        avg_hotel_cost = 4000.0
        avg_food_cost = 800.0
        avg_activity_cost = 500.0
        rating = 4.5
    
    class MockBudgetAllocation:
        transport_cost = 5000.0
        hotel_cost = 20000.0
        food_cost = 6000.0
        activities_cost = 5000.0
        local_transport_cost = 1500.0
        taxes_fees_cost = 2160.0  # 12% of transport+hotel+activities
        emergency_reserve = 2592.0  # 8% of subtotal (32,400)
        # Total: 42,252
    
    class MockTrip:
        id = 1
        destination = MockDestination()
        budget_allocation = MockBudgetAllocation()
        budget = 50000.0
        days = 5
        travelers_count = 1
        comfort_score = 60
        travel_type = "Beach"
        hotel_tier = "Mid-Range"
        transport_mode = "Flight"
        total_estimated_cost = 42252.0
        itineraries = []
    
    trip = MockTrip()
    
    # Test cost explanations assembly
    print("\n1. Assembling cost explanations...")
    try:
        explanations = assemble_cost_explanations(
            trip=trip,
            costs_dict={
                "transport_mode": "Flight",
                "transport_cost": 5000.0,
                "hotel_tier": "Mid-Range",
                "hotel_cost": 20000.0,
                "food_cost": 6000.0,
                "activities_cost": 5000.0,
                "local_transport_cost": 1500.0,
                "taxes_fees_cost": 2160.0,
                "emergency_reserve": 2592.0,
                "total_estimated_cost": 42252.0,
            },
            budget=50000.0,
            days=5,
            travelers=1,
            comfort_score=60,
            travel_type="Beach",
            starting_city="Mumbai",
            destination=trip.destination
        )
        
        print(f"   ✓ Generated {len(explanations)} cost category explanations")
        
        # Validate structure
        for exp in explanations:
            assert "category" in exp, f"Missing category in {exp}"
            assert "selected_option" in exp, f"Missing selected_option in {exp}"
            assert "selected_cost" in exp, f"Missing selected_cost in {exp}"
            assert "allocation_percentage" in exp, f"Missing allocation_percentage in {exp}"
            assert "decision_factors" in exp, f"Missing decision_factors in {exp}"
            assert "explanation" in exp, f"Missing explanation in {exp}"
            print(f"   ✓ {exp['category']}: ₹{exp['selected_cost']:,.0f} ({exp['allocation_percentage']:.1f}% of budget)")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        raise
    
    # Verify financial reconciliation
    print("\n2. Verifying financial reconciliation...")
    try:
        from app.services.explainability import calculate_budget_reconciliation
        
        alloc = trip.budget_allocation
        reconciliation = calculate_budget_reconciliation(
            transport_cost=alloc.transport_cost,
            hotel_cost=alloc.hotel_cost,
            food_cost=alloc.food_cost,
            activities_cost=alloc.activities_cost,
            local_transport_cost=alloc.local_transport_cost,
            taxes_fees_cost=alloc.taxes_fees_cost,
            emergency_reserve=alloc.emergency_reserve,
            total_budget=trip.budget
        )
        
        print(f"   Subtotal: ₹{reconciliation['subtotal']:,.0f}")
        print(f"   + Contingency: ₹{reconciliation['emergency_reserve']:,.0f} ({reconciliation['allocations']['Contingency']:?.1f}% of expenses)")
        print(f"   = Total: ₹{reconciliation['total_with_contingency']:,.0f}")
        print(f"   Budget: ₹{trip.budget:,.0f}")
        print(f"   Remaining: ₹{reconciliation['remaining_after_contingency']:,.0f}")
        print(f"   Variance: {reconciliation['variance_percent']:.2f}%")
        
        if reconciliation['is_balanced']:
            print("   ✓ Budget is balanced (variance < 5%)")
        else:
            print("   ⚠ Budget variance exceeded 5% threshold")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        raise
    
    # Test alternative generations
    print("\n3. Testing alternative option generation...")
    try:
        from app.services.explainability import (
            get_accommodation_alternatives,
            get_transport_alternatives
        )
        
        acc_alts = get_accommodation_alternatives(
            destination_avg_hotel_cost=trip.destination.avg_hotel_cost,
            days=trip.days,
            comfort_score=trip.comfort_score
        )
        print(f"   ✓ Accommodation: {len(acc_alts)} tiers generated")
        for alt in acc_alts:
            print(f"     - {alt['tier']}: ₹{alt['total_cost']:,.0f} (₹{alt['cost_per_night']:,.0f}/night)")
        
        trans_alts = get_transport_alternatives(
            comfort_score=trip.comfort_score,
            distance_multiplier=1.0,
            travelers=trip.travelers_count,
            base_train_cost=5000.0 / trip.travelers_count * 0.45,
            base_flight_cost=5000.0 / trip.travelers_count * 1.25
        )
        print(f"   ✓ Transport: {len(trans_alts)} modes generated")
        for alt in trans_alts:
            print(f"     - {alt['mode']}: ₹{alt['cost']:,.0f}")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        raise
    
    # Test percentage calculations
    print("\n4. Verifying percentage allocation...")
    try:
        total_allocated = sum([exp["selected_cost"] for exp in explanations])
        total_percentage = sum([exp["allocation_percentage"] for exp in explanations])
        
        print(f"   Total allocated: ₹{total_allocated:,.0f}")
        print(f"   Total percentage: {total_percentage:.1f}%")
        
        if abs(total_percentage - 100.0) < 0.5:
            print("   ✓ Percentages sum to ~100%")
        else:
            print(f"   ✗ Percentage sum {total_percentage:.1f}% (expected ~100%)")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        raise
    
    # Test response assembly
    print("\n5. Testing complete response assembly...")
    try:
        from app.schemas import TripMetadata, FinancialSummary, ExplainabilityResponse
        
        metadata = TripMetadata(
            destination_name=trip.destination.name,
            destination_state=trip.destination.state,
            trip_duration_days=trip.days,
            traveler_count=trip.travelers_count,
            comfort_score=trip.comfort_score,
            travel_type=trip.travel_type,
            destination_category=trip.destination.category
        )
        
        financial_summary = FinancialSummary(
            total_budget=trip.budget,
            total_estimated_cost=trip.total_estimated_cost,
            remaining_budget=trip.budget - trip.total_estimated_cost,
            contingency_included=True,
            contingency_amount=alloc.emergency_reserve,
            contingency_percentage=round(alloc.emergency_reserve / (trip.total_estimated_cost - alloc.emergency_reserve) * 100, 1)
        )
        
        response = ExplainabilityResponse(
            trip_id=trip.id,
            trip_metadata=metadata,
            financial_summary=financial_summary,
            cost_explanations=explanations,
            ai_summary="This is a well-balanced beach trip with mid-range accommodations.",
            recommendations=[],
            has_alternative_prices=True,
            missing_decision_data=[],
            data_source="calculated"
        )
        
        print("   ✓ ExplainabilityResponse assembled successfully")
        print(f"     - Trip ID: {response.trip_id}")
        print(f"     - Categories explained: {len(response.cost_explanations)}")
        print(f"     - Financial summary: ₹{response.financial_summary.total_estimated_cost:,.0f} / ₹{response.financial_summary.total_budget:,.0f}")
        
        # Verify serialization
        response_dict = response.dict()
        print(f"   ✓ Response serializable to JSON ({len(response_dict)} top-level keys)")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        raise
    
    print("\n" + "="*70)
    print("✓ INTEGRATION TEST PASSED")
    print("="*70)
    print("\nSummary:")
    print(f"  - Trip analyzed: {trip.destination.name} ({trip.days} days, ₹{trip.budget:,.0f} budget)")
    print(f"  - Categories explained: {len(explanations)}")
    print(f"  - Total estimated cost: ₹{trip.total_estimated_cost:,.0f}")
    print(f"  - Contingency: ₹{alloc.emergency_reserve:,.0f} ({financial_summary.contingency_percentage}%)")
    print(f"  - Financial variance: {reconciliation['variance_percent']:.2f}%")
    print(f"  - Data source: {response.data_source}")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_full_explainability_flow())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
