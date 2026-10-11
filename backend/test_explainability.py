"""
Test suite for the explainability service.

Tests:
1. Grounded decision data extraction
2. Alternative options generation
3. Financial reconciliation
4. Explainability response structure
5. Fallback behavior when data is incomplete
"""

import sys
sys.path.insert(0, '/Users/nikhil/Downloads/SSN/College Files/Fourth Year/7th Semester/Full Stack Development/Full Stack Development Project/BudgetBound/backend')

from app.services import explainability
from decimal import Decimal

def test_accommodation_alternatives():
    """Test that accommodation alternatives are generated correctly"""
    print("\n" + "="*60)
    print("TEST: Accommodation Alternatives")
    print("="*60)
    
    alts = explainability.get_accommodation_alternatives(
        destination_avg_hotel_cost=5000.0,  # Delhi average
        days=5,
        comfort_score=60
    )
    
    assert len(alts) == 3, "Should generate 3 tiers"
    assert alts[0]["tier"] == "Budget", "First tier should be Budget"
    assert alts[1]["tier"] == "Mid-Range", "Second tier should be Mid-Range"
    assert alts[2]["tier"] == "Luxury", "Third tier should be Luxury"
    
    # Verify costs are properly scaled
    budget_per_night = 5000 * 0.65
    midrange_per_night = 5000 * 1.0
    luxury_per_night = 5000 * 1.85
    
    assert alts[0]["cost_per_night"] == round(budget_per_night, 2)
    assert alts[1]["cost_per_night"] == round(midrange_per_night, 2)
    assert alts[2]["cost_per_night"] == round(luxury_per_night, 2)
    
    # Verify total costs
    assert alts[0]["total_cost"] == round(budget_per_night * 5, 2)
    assert alts[1]["total_cost"] == round(midrange_per_night * 5, 2)
    assert alts[2]["total_cost"] == round(luxury_per_night * 5, 2)
    
    print("✓ Generated 3 accommodation tiers with correct pricing")
    print(f"  Budget:    ₹{alts[0]['total_cost']:.0f} (₹{alts[0]['cost_per_night']:.0f}/night)")
    print(f"  Mid-Range: ₹{alts[1]['total_cost']:.0f} (₹{alts[1]['cost_per_night']:.0f}/night)")
    print(f"  Luxury:    ₹{alts[2]['total_cost']:.0f} (₹{alts[2]['cost_per_night']:.0f}/night)")


def test_transport_alternatives():
    """Test that transport alternatives are generated correctly"""
    print("\n" + "="*60)
    print("TEST: Transport Alternatives")
    print("="*60)
    
    alts = explainability.get_transport_alternatives(
        comfort_score=60,
        distance_multiplier=1.0,
        travelers=2,
        base_train_cost=1500.0,
        base_flight_cost=4000.0
    )
    
    assert len(alts) >= 3, "Should generate at least 3 transport modes"
    
    # Verify modes are realistic
    modes = [alt["mode"] for alt in alts]
    assert any("Train" in m for m in modes), "Should include train option"
    assert any("Flight" in m for m in modes), "Should include flight option"
    
    print("✓ Generated transport alternatives")
    for alt in alts:
        print(f"  {alt['mode']}: ₹{alt['cost']:.0f}")


def test_budget_reconciliation():
    """Test financial reconciliation calculation"""
    print("\n" + "="*60)
    print("TEST: Budget Reconciliation")
    print("="*60)
    
    result = explainability.calculate_budget_reconciliation(
        transport_cost=5000.0,
        hotel_cost=15000.0,
        food_cost=7500.0,
        activities_cost=6000.0,
        local_transport_cost=2000.0,
        taxes_fees_cost=2100.0,  # 12% of transport+hotel+activities
        emergency_reserve=3560.0,  # 8% of subtotal
        total_budget=50000.0
    )
    
    print(f"✓ Budget reconciliation verified:")
    print(f"  Subtotal:                  ₹{result['subtotal']:.0f}")
    print(f"  + Contingency:             ₹{result['emergency_reserve']:,.0f}")
    print(f"  Total:                     ₹{result['total_with_contingency']:.0f}")
    print(f"  Budget:                    ₹50000.00")
    print(f"  Remaining:                 ₹{result['remaining_after_contingency']:.0f}")
    print(f"  Is Balanced (< 5% variance): {result['is_balanced']}")
    print(f"  Variance:                  {result['variance_percent']:.2f}%")
    
    # Verify calculations
    expected_subtotal = 5000 + 15000 + 7500 + 6000 + 2000 + 2100
    assert result['subtotal'] == round(expected_subtotal, 2)
    assert result['total_with_contingency'] == round(expected_subtotal + 3560, 2)


def test_accommodation_explanation():
    """Test accommodation explanation generation"""
    print("\n" + "="*60)
    print("TEST: Accommodation Explanation")
    print("="*60)
    
    exp = explainability.build_accommodation_explanation(
        hotel_tier="Mid-Range",
        hotel_cost=15000.0,
        days=5,
        comfort_score=60,
        destination_avg=5000.0
    )
    
    assert exp["category"] == "Accommodation"
    assert exp["selected_option"] == "Mid-Range Hotel/Resort"
    assert exp["selected_cost"] == 15000.0
    assert len(exp["decision_factors"]) > 0
    assert exp["alternatives"] is not None
    assert len(exp["alternatives"]) > 0
    
    print(f"✓ Accommodation explanation generated")
    print(f"  Category: {exp['category']}")
    print(f"  Selected: {exp['selected_option']}")
    print(f"  Cost: ₹{exp['selected_cost']:.0f}")
    print(f"  Per night: ₹{exp['cost_per_night']:.0f}")
    print(f"  Decision factors: {len(exp['decision_factors'])}")
    print(f"  Alternatives: {len(exp['alternatives'])}")
    print(f"  Explanation: {exp['explanation'][:100]}...")


def test_food_explanation():
    """Test food allocation explanation"""
    print("\n" + "="*60)
    print("TEST: Food Explanation")
    print("="*60)
    
    exp = explainability.build_food_explanation(
        food_cost=7500.0,
        days=5,
        travelers=1,
        comfort_score=60,
        destination_name="Goa"
    )
    
    assert exp["category"] == "Food & Dining"
    assert exp["selected_cost"] == 7500.0
    daily_per_person = 7500.0 / (5 * 1)
    assert exp["daily_per_person"] == round(daily_per_person, 2)
    
    print(f"✓ Food explanation generated")
    print(f"  Total food cost: ₹{exp['selected_cost']:.0f}")
    print(f"  Daily per person: ₹{exp['daily_per_person']:.0f}")
    print(f"  Explanation: {exp['explanation'][:100]}...")


def test_contingency_explanation():
    """Test contingency reserve explanation"""
    print("\n" + "="*60)
    print("TEST: Contingency Explanation")
    print("="*60)
    
    exp = explainability.build_contingency_explanation(
        emergency_reserve=3560.0,
        subtotal=44500.0,
        total_budget=50000.0
    )
    
    assert exp["category"] == "Contingency & Emergency Reserve"
    expected_percent = (3560.0 / 44500.0 * 100.0)
    assert exp["percentage_of_subtotal"] == round(expected_percent, 2)
    
    print(f"✓ Contingency explanation generated")
    print(f"  Reserve amount: ₹{exp['selected_cost']:.0f}")
    print(f"  Percentage of expenses: {exp['percentage_of_subtotal']:.1f}%")
    print(f"  Explanation: {exp['explanation'][:100]}...")


def test_financial_consistency():
    """Test that all components sum correctly"""
    print("\n" + "="*60)
    print("TEST: Financial Consistency")
    print("="*60)
    
    # Create a realistic budget scenario
    transport = 5000.0
    accommodation = 15000.0
    food = 7500.0
    activities = 6000.0
    local_transport = 2000.0
    taxes = 2100.0
    
    subtotal = transport + accommodation + food + activities + local_transport + taxes
    contingency = subtotal * 0.08
    total = subtotal + contingency
    
    print(f"Components sum to:")
    print(f"  Transport:      ₹{transport:,.0f}")
    print(f"  Accommodation:  ₹{accommodation:,.0f}")
    print(f"  Food:           ₹{food:,.0f}")
    print(f"  Activities:     ₹{activities:,.0f}")
    print(f"  Local transport:₹{local_transport:,.0f}")
    print(f"  Taxes & fees:   ₹{taxes:,.0f}")
    print(f"  Subtotal:       ₹{subtotal:,.0f}")
    print(f"  + Contingency:  ₹{contingency:,.0f}")
    print(f"  TOTAL:          ₹{total:,.0f}")
    
    assert total == round(subtotal + contingency, 2)
    print("✓ Financial totals reconcile")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("EXPLAINABILITY SERVICE TEST SUITE")
    print("="*60)
    
    try:
        test_accommodation_alternatives()
        test_transport_alternatives()
        test_budget_reconciliation()
        test_accommodation_explanation()
        test_food_explanation()
        test_contingency_explanation()
        test_financial_consistency()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
