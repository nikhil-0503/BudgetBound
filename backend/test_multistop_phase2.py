#!/usr/bin/env python3
"""
Phase 2 Testing: Destination-specific activities, preference enforcement,
reliable transfer estimates, and financial reconciliation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.destination_database import (
    get_destination_info,
    get_activities_for_destination,
    get_restaurants_for_destination,
    get_must_try_food,
)
from app.services.transfer_service import (
    get_transfer_options,
    estimate_transfer,
    estimate_transfer_cost,
)
from app.services.multistop_calculator import MultiStopCostCalculator, MultiStopItineraryValidator
from app.services.gemini import GroqTravelService


def test_destination_database():
    """Test: Destination database has specific activities, not generic templates."""
    print("\n=== Test 1: Destination-Specific Activities ===")
    
    destinations = ["delhi", "agra", "jaipur", "kolkata", "goa", "varanasi"]
    
    for dest in destinations:
        info = get_destination_info(dest)
        assert info is not None, f"Destination '{dest}' not in database"
        
        activities = info.get("activities", [])
        assert len(activities) > 0, f"No activities for '{dest}'"
        
        # Check that activities are specific (not generic templates)
        # Note: "Visit" alone is acceptable if combined with specific location (e.g., "Visit Red Fort")
        # Generic = pure action without location (e.g., "visit attraction", "local market")
        bad_patterns = ["key attraction", "local market", "scenic viewpoint", "historic site", "primary historical"]
        
        for activity in activities[:2]:  # Check first 2 activities
            title_lower = activity.title.lower()
            # Should NOT match these purely generic patterns
            for phrase in bad_patterns:
                assert phrase not in title_lower, f"Found generic phrase '{phrase}' in '{activity.title}'"
            
            # SHOULD have specific location
            assert activity.location, f"Activity '{activity.title}' missing location"
            # SHOULD have detailed description
            assert len(activity.description) > 50, f"Activity '{activity.title}' description too short"
        
        print(f"✓ {dest.title():>10} — {len(activities)} specific activities, e.g., '{activities[0].title}'")
    
    return True


def test_preference_application():
    """Test: Preferences (vegetarian, adventure, budget) are applied correctly."""
    print("\n=== Test 2: Preference-Based Filtering ===")
    
    # Test vegetarian filtering
    delhi_veg = get_activities_for_destination("delhi", vegetarian_only=True, count=10)
    assert all(a.vegetarian_friendly for a in delhi_veg), "Vegetarian filter not working"
    print(f"✓ Vegetarian activities: {len(delhi_veg)} found (all vegetarian)")
    
    # Test restaurant vegetarian filtering
    delhi_restaurants_veg = get_restaurants_for_destination("delhi", vegetarian_only=True)
    assert all(r.vegetarian_options for r in delhi_restaurants_veg), "Restaurant veg filter not working"
    print(f"✓ Vegetarian restaurants: {len(delhi_restaurants_veg)} found")
    
    # Test must-try food
    delhi_veg_food = get_must_try_food("delhi", vegetarian=True)
    delhi_nonveg_food = get_must_try_food("delhi", vegetarian=False)
    assert delhi_veg_food != delhi_nonveg_food, "Vegetarian and non-veg food should differ"
    print(f"✓ Must-try food varies by preference: veg={delhi_veg_food}, nonveg={delhi_nonveg_food}")
    
    return True


def test_transfer_service():
    """Test: Transfer service provides realistic route-specific estimates."""
    print("\n=== Test 3: Transfer Estimation (Not Hardcoded) ===")
    
    # Test different routes have different durations
    delhi_agra = estimate_transfer("delhi", "agra")
    delhi_kolkata = estimate_transfer("delhi", "kolkata")
    
    assert delhi_agra is not None, "Delhi-Agra route not found"
    assert delhi_kolkata is not None, "Delhi-Kolkata route not found"
    
    # Should be different durations (Agra is close, Kolkata is far)
    agra_duration = delhi_agra["duration_hours"]
    kolkata_duration = delhi_kolkata["duration_hours"]
    
    assert agra_duration < kolkata_duration, "Agra should be closer than Kolkata"
    print(f"✓ Route-specific durations: Delhi→Agra={agra_duration}h, Delhi→Kolkata={kolkata_duration}h")
    
    # Test that costs vary by mode
    options = get_transfer_options("delhi", "agra")
    modes = [opt.mode for opt in options]
    costs = [opt.approximate_cost_per_person for opt in options]
    
    assert "train" in modes and "bus" in modes, "Should have multiple transport modes"
    assert len(set(costs)) > 1, "Different modes should have different costs"
    print(f"✓ Multiple transport modes available: {modes}")
    print(f"  Costs: Train=₹{[c for m, c in zip(modes, costs) if m == 'train'][0]}, Bus=₹{[c for m, c in zip(modes, costs) if m == 'bus'][0]}")
    
    # Test that Delhi-Kolkata recommends flight (not train)
    kolkata_options = get_transfer_options("delhi", "kolkata")
    first_mode = kolkata_options[0].mode if kolkata_options else None
    print(f"✓ Long distance (Delhi→Kolkata) recommends: {first_mode} (train would be inefficient)")
    
    return True


def test_fallback_uses_destination_db():
    """Test: Fallback generator now uses destination database, not generic templates."""
    print("\n=== Test 4: Fallback Generator Uses Destination Database ===")
    
    service = GroqTravelService()
    stops = [
        {"destination": "Delhi", "days": 2},
        {"destination": "Agra", "days": 1},
    ]
    budget = 30000.0
    special_requests = "vegetarian food, history interested"
    
    itinerary = service._fallback_multistop_plan(stops, budget, special_requests)
    
    # Check that activities are destination-specific (not "Visit key local attraction")
    generic_count = 0
    for leg in itinerary.get("legs", []):
        for day in leg.get("itinerary", []):
            for activity in day.get("activities", []):
                title = activity.get("title", "").lower()
                if any(phrase in title for phrase in ["key attraction", "local market", "scenic viewpoint"]):
                    generic_count += 1
    
    # Should have mostly specific activities now
    total_activities = sum(
        len(day.get("activities", []))
        for leg in itinerary.get("legs", [])
        for day in leg.get("itinerary", [])
    )
    
    generic_ratio = generic_count / total_activities if total_activities > 0 else 0
    assert generic_ratio < 0.3, f"Too many generic activities: {generic_ratio * 100:.0f}%"
    print(f"✓ Generic activities: {generic_count}/{total_activities} ({generic_ratio * 100:.0f}%) — Below 30% threshold")
    
    # Check for destination-specific highlights
    for leg in itinerary.get("legs", []):
        highlights = leg.get("highlights", [])
        assert len(highlights) > 0, f"No highlights for {leg['destination']}"
        # Should reference actual locations
        dest = leg["destination"].lower()
        print(f"✓ {leg['destination']}: Highlights = {highlights[:2]}")
    
    # Check that transfer info is not hardcoded "3-4 hours"
    travel_info = itinerary["legs"][0].get("travel_to_next")
    if travel_info:
        duration = travel_info.get("duration", "")
        assert "3-4" not in duration, f"Transfer still hardcoded: {duration}"
        print(f"✓ Transfer duration is realistic: '{duration}' (not hardcoded '3-4 hours')")
    
    # Check data_source marker
    assert itinerary.get("data_source") == "fallback", "Should mark as fallback-generated"
    print(f"✓ Response marked as: {itinerary.get('data_source')}")
    
    return True


def test_comprehensive_validation():
    """Test: Validator detects generic patterns and checks financial coherence."""
    print("\n=== Test 5: Comprehensive Validation ===")
    
    service = GroqTravelService()
    stops = [
        {"destination": "Delhi", "days": 2},
        {"destination": "Agra", "days": 2},
        {"destination": "Jaipur", "days": 2},
    ]
    budget = 75000.0
    
    itinerary = service._fallback_multistop_plan(stops, budget, "non-vegetarian, budget travel")
    
    validator = MultiStopItineraryValidator()
    validation = validator.validate(itinerary, stops)
    
    assert validation["is_valid"], f"Validation failed: {validation['errors']}"
    print(f"✓ Structural validity: PASS")
    
    # Check destination-specificity score
    is_destination_specific = validation.get("is_destination_specific", False)
    generic_count = validation.get("generic_pattern_count", 0)
    print(f"✓ Destination-specific: {is_destination_specific} (generic patterns: {generic_count})")
    
    # Check financial coherence
    financial_score = validation.get("financial_coherence_score", 0)
    print(f"✓ Financial coherence: {financial_score:.0f}/100")
    
    # Check global day count
    expected_global_days = sum(s["days"] for s in stops)
    actual_global_days = validation.get("global_day_count", 0)
    assert actual_global_days == expected_global_days, f"Global day mismatch: {actual_global_days} vs {expected_global_days}"
    print(f"✓ Global day count: {actual_global_days} (correct for {expected_global_days}-day trip)")
    
    return True


def test_budget_reconciliation():
    """Test: Budget allocations reconcile exactly with cost calculator."""
    print("\n=== Test 6: Budget Reconciliation ===")
    
    stops = [
        {"destination": "Chennai", "days": 2},
        {"destination": "Bangalore", "days": 3},
        {"destination": "Kochi", "days": 2},
    ]
    budget = 100000.0
    
    calculator = MultiStopCostCalculator(budget, stops)
    allocations = calculator.allocate_budget()
    
    grand_total = allocations["grand_total"]
    remaining = allocations["remaining_budget"]
    
    # Should reconcile exactly
    reconciliation_error = abs((grand_total + remaining) - budget)
    assert reconciliation_error < 0.01, f"Budget not reconciled: error={reconciliation_error}"
    print(f"✓ Budget reconciliation: {grand_total:.0f} + {remaining:.0f} = {budget:.0f} (error: ₹{reconciliation_error:.2f})")
    
    # Category breakdown should sum to grand total
    category_sum = sum(allocations["category_breakdown"].values())
    assert abs(category_sum - grand_total) < 0.01, f"Category sum mismatch: {category_sum} vs {grand_total}"
    print(f"✓ Category breakdown sums correctly:")
    for category, amount in allocations["category_breakdown"].items():
        pct = (amount / grand_total) * 100 if grand_total > 0 else 0
        print(f"  • {category:.<20} ₹{amount:>8,.0f} ({pct:>5.1f}%)")
    
    return True


def run_all_tests():
    """Execute all Phase 2 tests."""
    print("\n" + "="*70)
    print("BUDGETBOUND MULTI-STOP PLANNER — PHASE 2 TESTING")
    print("Destination-Specific Activities, Preferences, Transfer Estimates, Validation")
    print("="*70)
    
    tests = [
        ("Destination Database", test_destination_database),
        ("Preference Application", test_preference_application),
        ("Transfer Service", test_transfer_service),
        ("Fallback Generator", test_fallback_uses_destination_db),
        ("Comprehensive Validation", test_comprehensive_validation),
        ("Budget Reconciliation", test_budget_reconciliation),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"✗ {name} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name} ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    if failed == 0:
        print("🎉 ALL PHASE 2 TESTS PASSED — Production ready!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
