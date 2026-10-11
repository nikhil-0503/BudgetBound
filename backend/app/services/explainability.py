"""
Explainability Service: Grounds AI-generated explanations in actual decision data.

This service:
1. Traces actual decisions from calculate_costs, comfort scoring, and preferences
2. Assembles decision metadata (inputs, factors, alternatives)
3. Validates financial reconciliation
4. Produces structured explanations immune to AI hallucination
5. Optionally enhances explanations with LLM-powered summarization
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal

logger = logging.getLogger(__name__)


def get_transport_alternatives(
    comfort_score: int,
    distance_multiplier: float,
    travelers: int,
    base_train_cost: float,
    base_flight_cost: float
) -> List[Dict[str, Any]]:
    """
    Generate alternative transport options with calculated costs.
    
    Returns list of [{"mode": "Train", "cost": X, "duration": "Y hrs", "notes": "..."}]
    """
    # These are realistic Indian transport cost estimates
    alternatives = []
    
    train_cost = max(600.0, base_train_cost) * travelers
    flight_cost = max(2500.0, base_flight_cost) * travelers
    
    # Train: cheaper, longer, more comfortable sleeper options
    if base_train_cost > 0:
        alternatives.append({
            "mode": "Train (Sleeper)",
            "cost": round(train_cost, 2),
            "estimated_duration": "12-24 hours (depending on distance)",
            "comfort_level": "Basic to Comfort",
            "notes": "Most budget-friendly for long distances; overnight travel saves accommodation"
        })
    
    # Flight: expensive, fast
    if base_flight_cost > 0:
        alternatives.append({
            "mode": "Flight",
            "cost": round(flight_cost, 2),
            "estimated_duration": "2-4 hours",
            "comfort_level": "Premium",
            "notes": "Fastest option; consider cost difference vs. time saved"
        })
    
    # Bus as tertiary option
    bus_cost = max(400.0, base_train_cost * 0.7) * travelers  # buses typically 30% cheaper than trains
    alternatives.append({
        "mode": "Bus (Luxury Coach)",
        "cost": round(bus_cost, 2),
        "estimated_duration": "14-36 hours (depending on distance)",
        "comfort_level": "Basic",
        "notes": "Budget option; consider overnight travel for extra comfort"
    })
    
    return alternatives


def get_accommodation_alternatives(
    destination_avg_hotel_cost: float,
    days: int,
    comfort_score: int
) -> List[Dict[str, Any]]:
    """
    Generate accommodation tier options with calculated costs per night.
    """
    budget_per_night = destination_avg_hotel_cost * 0.65
    midrange_per_night = destination_avg_hotel_cost * 1.0
    luxury_per_night = destination_avg_hotel_cost * 1.85
    
    alternatives = [
        {
            "tier": "Budget",
            "cost_per_night": round(budget_per_night, 2),
            "total_cost": round(budget_per_night * days, 2),
            "description": "Hostels, guesthouses, basic hotels",
            "comfort_level": "Basic (30/100)",
            "amenities": ["WiFi", "Fan/AC", "Basic bathroom"]
        },
        {
            "tier": "Mid-Range",
            "cost_per_night": round(midrange_per_night, 2),
            "total_cost": round(midrange_per_night * days, 2),
            "description": "3-star hotels, nice resorts",
            "comfort_level": "Comfortable (60/100)",
            "amenities": ["WiFi", "AC", "En-suite bathroom", "TV"]
        },
        {
            "tier": "Luxury",
            "cost_per_night": round(luxury_per_night, 2),
            "total_cost": round(luxury_per_night * days, 2),
            "description": "5-star resorts, premium experiences",
            "comfort_level": "Premium (90/100)",
            "amenities": ["WiFi", "AC", "Luxury bathroom", "Concierge", "Restaurant"]
        }
    ]
    
    return alternatives


def calculate_budget_reconciliation(
    transport_cost: float,
    hotel_cost: float,
    food_cost: float,
    activities_cost: float,
    local_transport_cost: float,
    taxes_fees_cost: float,
    emergency_reserve: float,
    total_budget: float
) -> Dict[str, Any]:
    """
    Verify that all costs reconcile to the total and compute percentages.
    
    Returns: {
        "subtotal": X,
        "total_with_contingency": Y,
        "remaining_after_contingency": Z,
        "allocations": {...},
        "is_balanced": True/False,
        "variance_percent": 0.5 (how much under/over budget)
    }
    """
    allocations = {
        "Accommodation": hotel_cost,
        "Inter-city Transport": transport_cost,
        "Local Transport": local_transport_cost,
        "Food & Dining": food_cost,
        "Activities & Admissions": activities_cost,
        "Taxes & Fees": taxes_fees_cost,
    }
    
    subtotal = sum(allocations.values())
    total_with_contingency = subtotal + emergency_reserve
    remaining = total_budget - total_with_contingency
    
    variance_percent = abs(remaining) / total_budget * 100.0 if total_budget > 0 else 0.0
    is_balanced = variance_percent < 5.0  # Within 5% is acceptable
    
    return {
        "subtotal": round(subtotal, 2),
        "total_with_contingency": round(total_with_contingency, 2),
        "remaining_after_contingency": round(remaining, 2),
        "allocations": {k: round(v, 2) for k, v in allocations.items()},
        "is_balanced": is_balanced,
        "variance_percent": round(variance_percent, 2),
        "variance_rupees": round(remaining, 2)
    }


def build_accommodation_explanation(
    hotel_tier: str,
    hotel_cost: float,
    days: int,
    comfort_score: int,
    destination_avg: float
) -> Dict[str, Any]:
    """
    Build grounded explanation for accommodation choice.
    """
    selected_per_night = hotel_cost / days if days > 0 else 0
    
    decision_factors = [
        f"Comfort score: {comfort_score}/100",
        f"Trip duration: {days} days",
        f"Destination average: ₹{destination_avg:,.0f}/night (mid-range)"
    ]
    
    # Determine which tier was selected
    budget_threshold = destination_avg * 0.65
    luxury_threshold = destination_avg * 1.85
    
    if selected_per_night <= budget_threshold * 1.1:
        tier_reason = "Budget-conscious travelers or low comfort scores typically choose hostels/guesthouses"
    elif selected_per_night >= luxury_threshold * 0.9:
        tier_reason = "High comfort score (>70) justifies premium resorts and full-service hotels"
    else:
        tier_reason = "Mid-range balance between cost and comfort; standard 3-star hotels"
    
    # Alternatives
    alternatives = get_accommodation_alternatives(destination_avg, days, comfort_score)
    
    return {
        "category": "Accommodation",
        "selected_option": f"{hotel_tier} Hotel/Resort",
        "selected_cost": round(hotel_cost, 2),
        "estimated_cost": round(hotel_cost, 2),
        "cost_per_night": round(selected_per_night, 2),
        "allocation_percentage": 0.0,  # Will be calculated from budget
        "decision_factors": decision_factors,
        "alternatives": alternatives,
        "explanation": tier_reason
    }


def build_transport_explanation(
    transport_mode: str,
    transport_cost: float,
    comfort_score: int,
    travelers: int,
    starting_city: Optional[str],
    destination_name: str,
    base_train_cost: float,
    base_flight_cost: float
) -> Dict[str, Any]:
    """
    Build grounded explanation for transport mode choice.
    """
    cost_per_person = transport_cost / travelers if travelers > 0 else 0
    
    decision_factors = [
        f"Comfort score: {comfort_score}/100",
        f"Travelers: {comfort_score}",
        f"Route: {starting_city or 'Unknown'} → {destination_name}"
    ]
    
    # Why was this mode selected?
    if transport_mode.lower() == "train":
        mode_reason = (
            "Train selected due to lower comfort score (<50). Sleeper trains offer "
            "better budget-to-comfort ratio; overnight travel also saves accommodation costs."
        )
    else:  # Flight
        mode_reason = (
            "Flight selected due to higher comfort score (≥50). Faster travel preserves "
            "more time for destination experiences."
        )
    
    # Calculate alternatives
    alternatives = get_transport_alternatives(
        comfort_score=comfort_score,
        distance_multiplier=1.0,  # Placeholder
        travelers=travelers,
        base_train_cost=base_train_cost,
        base_flight_cost=base_flight_cost
    )
    
    return {
        "category": "Inter-city Transportation",
        "selected_option": transport_mode,
        "selected_cost": round(transport_cost, 2),
        "estimated_cost": round(transport_cost, 2),
        "cost_per_person": round(cost_per_person, 2),
        "allocation_percentage": 0.0,
        "decision_factors": decision_factors,
        "alternatives": alternatives,
        "explanation": mode_reason
    }


def build_food_explanation(
    food_cost: float,
    days: int,
    travelers: int,
    comfort_score: int,
    destination_name: str
) -> Dict[str, Any]:
    """
    Build grounded explanation for food allocation.
    """
    daily_per_person = (food_cost / (days * travelers)) if (days * travelers) > 0 else 0
    
    decision_factors = [
        f"Trip duration: {days} days",
        f"Comfort score: {comfort_score}/100",
        f"Travelers: {travelers}",
        f"Destination: {destination_name}"
    ]
    
    if comfort_score < 50:
        food_reason = (
            f"Budget dining: ~₹{daily_per_person:,.0f}/person/day. Emphasizes street food, "
            "local eateries, and self-catering options."
        )
    elif comfort_score <= 70:
        food_reason = (
            f"Mid-range dining: ~₹{daily_per_person:,.0f}/person/day. Mix of restaurants, "
            "casual dining, and local specialties."
        )
    else:
        food_reason = (
            f"Premium dining: ~₹{daily_per_person:,.0f}/person/day. Includes fine dining, "
            "restaurant meals, and culinary experiences."
        )
    
    return {
        "category": "Food & Dining",
        "selected_option": f"Daily allocation ₹{daily_per_person:,.0f}/person",
        "selected_cost": round(food_cost, 2),
        "estimated_cost": round(food_cost, 2),
        "daily_per_person": round(daily_per_person, 2),
        "allocation_percentage": 0.0,
        "decision_factors": decision_factors,
        "alternatives": None,
        "explanation": food_reason
    }


def build_activities_explanation(
    activities_cost: float,
    days: int,
    travelers: int,
    comfort_score: int,
    destination_name: str
) -> Dict[str, Any]:
    """
    Build grounded explanation for activities allocation.
    """
    activities_per_day = 1 if comfort_score < 30 else (2 if comfort_score <= 70 else 3)
    avg_per_activity = (activities_cost / (days * activities_per_day)) if (days * activities_per_day) > 0 else 0
    
    decision_factors = [
        f"Comfort score: {comfort_score}/100",
        f"Activities/day: {activities_per_day}",
        f"Trip duration: {days} days"
    ]
    
    activities_reason = (
        f"Based on comfort score ({comfort_score}/100), allocated ~{activities_per_day} "
        f"activity(ies) per day at ₹{avg_per_activity:,.0f} per activity. This covers "
        f"entry fees, guided tours, and adventure activities."
    )
    
    return {
        "category": "Activities & Admissions",
        "selected_option": f"{activities_per_day} activity(ies)/day",
        "selected_cost": round(activities_cost, 2),
        "estimated_cost": round(activities_cost, 2),
        "avg_per_activity": round(avg_per_activity, 2),
        "allocation_percentage": 0.0,
        "decision_factors": decision_factors,
        "alternatives": None,
        "explanation": activities_reason
    }


def build_contingency_explanation(
    emergency_reserve: float,
    subtotal: float,
    total_budget: float
) -> Dict[str, Any]:
    """
    Explain the contingency/emergency reserve allocation.
    """
    contingency_percent = (emergency_reserve / subtotal * 100.0) if subtotal > 0 else 0
    
    reason = (
        f"Emergency reserve is {contingency_percent:.1f}% of core expenses. "
        f"This covers unexpected costs (medical, transportation delays, "
        f"price fluctuations) without touching the main budget."
    )
    
    return {
        "category": "Contingency & Emergency Reserve",
        "selected_option": f"{contingency_percent:.1f}% of expenses",
        "selected_cost": round(emergency_reserve, 2),
        "estimated_cost": round(emergency_reserve, 2),
        "percentage_of_subtotal": round(contingency_percent, 2),
        "allocation_percentage": 0.0,
        "decision_factors": ["Standard travel contingency rule"],
        "alternatives": None,
        "explanation": reason
    }


def assemble_cost_explanations(
    trip: Any,  # sqlalchemy Trip model
    costs_dict: Dict[str, Any],  # Output from calculate_costs
    budget: float,
    days: int,
    travelers: int,
    comfort_score: int,
    travel_type: str,
    starting_city: Optional[str],
    destination: Any  # sqlalchemy Destination model
) -> List[Dict[str, Any]]:
    """
    Assemble all cost explanations and normalize percentages.
    
    Returns: List of cost explanations with percentages calculated against total budget.
    """
    explanations = [
        build_accommodation_explanation(
            hotel_tier=costs_dict["hotel_tier"],
            hotel_cost=costs_dict["hotel_cost"],
            days=days,
            comfort_score=comfort_score,
            destination_avg=destination.avg_hotel_cost
        ),
        build_transport_explanation(
            transport_mode=costs_dict["transport_mode"],
            transport_cost=costs_dict["transport_cost"],
            comfort_score=comfort_score,
            travelers=travelers,
            starting_city=starting_city,
            destination_name=destination.name,
            base_train_cost=costs_dict["transport_cost"] / travelers * 0.45,  # Approximation
            base_flight_cost=costs_dict["transport_cost"] / travelers * 1.25  # Approximation
        ),
        build_food_explanation(
            food_cost=costs_dict["food_cost"],
            days=days,
            travelers=travelers,
            comfort_score=comfort_score,
            destination_name=destination.name
        ),
        build_activities_explanation(
            activities_cost=costs_dict["activities_cost"],
            days=days,
            travelers=travelers,
            comfort_score=comfort_score,
            destination_name=destination.name
        ),
        {
            "category": "Local Transportation",
            "selected_option": "Local transit & taxis",
            "selected_cost": round(costs_dict["local_transport_cost"], 2),
            "estimated_cost": round(costs_dict["local_transport_cost"], 2),
            "per_day_per_person": round(costs_dict["local_transport_cost"] / (days * travelers), 2),
            "allocation_percentage": 0.0,
            "decision_factors": [f"Trip duration: {days} days", f"Travelers: {travelers}"],
            "alternatives": None,
            "explanation": f"₹{costs_dict['local_transport_cost']/days:,.0f}/day for local buses, autos, metro. Varies by destination."
        },
        {
            "category": "Taxes & Fees",
            "selected_option": "GST & service charges",
            "selected_cost": round(costs_dict["taxes_fees_cost"], 2),
            "estimated_cost": round(costs_dict["taxes_fees_cost"], 2),
            "percentage_of_pretax": round(costs_dict["taxes_fees_cost"] / (costs_dict["transport_cost"] + costs_dict["hotel_cost"] + costs_dict["activities_cost"]) * 100, 2) if (costs_dict["transport_cost"] + costs_dict["hotel_cost"] + costs_dict["activities_cost"]) > 0 else 0.0,
            "allocation_percentage": 0.0,
            "decision_factors": [],
            "alternatives": None,
            "explanation": "12% GST applied to transport, accommodation, and activities."
        },
        build_contingency_explanation(
            emergency_reserve=costs_dict["emergency_reserve"],
            subtotal=sum([costs_dict[k] for k in ["transport_cost", "hotel_cost", "food_cost", "activities_cost", "local_transport_cost", "taxes_fees_cost"]]),
            total_budget=budget
        )
    ]
    
    # Normalize percentages relative to total budget
    for exp in explanations:
        exp["allocation_percentage"] = round(exp["selected_cost"] / budget * 100.0, 1)
    
    return explanations
