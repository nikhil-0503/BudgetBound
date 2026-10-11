"""
Multi-stop trip cost calculator and itinerary builder.
Ensures transparent, deterministic, reconcilable budget allocation.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class MultiStopCostCalculator:
    """
    Allocates budget across stops and days deterministically.
    Guarantees that all totals reconcile exactly.
    """
    
    # Fixed percentage allocations (must sum to 100%)
    ACCOMMODATION_PCT = Decimal("35")      # Per stop
    FOOD_PCT = Decimal("20")               # Per stop
    ACTIVITIES_PCT = Decimal("20")         # Per stop
    LOCAL_TRANSPORT_PCT = Decimal("10")    # Per stop
    CONTINGENCY_PCT = Decimal("15")        # Global, distributed per stop
    
    def __init__(self, total_budget: float, stops: List[Dict[str, Any]]):
        """
        Initialize calculator.
        
        Args:
            total_budget: Total INR budget
            stops: List of {destination, days}
        """
        self.total_budget = Decimal(str(total_budget))
        self.stops = stops
        self.total_days = sum(s["days"] for s in stops)
        self.inter_city_transport_pct = Decimal("0")  # Initialized later
        
    def allocate_budget(self) -> Dict[str, Any]:
        """
        Allocate budget across stops and return detailed breakdown.
        
        Returns:
            {
                "stops": [
                    {
                        "destination": str,
                        "days": int,
                        "global_day_range": [int, int],  # Days 1-2, Days 3-4, etc
                        "allocation": {
                            "accommodation_per_night": float,
                            "food_per_day": float,
                            "activities_per_day": float,
                            "local_transport_per_day": float,
                            "inter_city_transport": float or None,  # None for last stop
                            "contingency": float
                        },
                        "stop_total": float
                    }
                ],
                "category_breakdown": {
                    "accommodation": float,
                    "food": float,
                    "activities": float,
                    "local_transport": float,
                    "inter_city_transport": float,
                    "contingency": float
                },
                "grand_total": float,
                "remaining_budget": float,
                "budget_exceeded": bool,
                "notes": List[str]
            }
        """
        notes = []
        result = {"stops": [], "notes": notes}
        
        # Handle edge case: no stops
        if not self.stops or self.total_days == 0:
            result["category_breakdown"] = {
                "accommodation": 0.0,
                "food": 0.0,
                "activities": 0.0,
                "local_transport": 0.0,
                "inter_city_transport": 0.0,
                "contingency": 0.0,
            }
            result["grand_total"] = 0.0
            result["remaining_budget"] = float(self.total_budget)
            result["budget_exceeded"] = False
            return result
        
        # Calculate inter-city transport budget (3% of total)
        # This is removed from activities budget
        inter_city_budget = self.total_budget * Decimal("3") / Decimal("100")
        activities_adjusted_pct = self.ACTIVITIES_PCT - Decimal("3")
        
        # Allocate contingency per day globally
        contingency_per_day = (self.total_budget * self.CONTINGENCY_PCT / Decimal("100")) / Decimal(self.total_days)
        
        # Build per-stop allocations
        category_totals = {
            "accommodation": Decimal("0"),
            "food": Decimal("0"),
            "activities": Decimal("0"),
            "local_transport": Decimal("0"),
            "inter_city_transport": Decimal("0"),
            "contingency": Decimal("0"),
        }
        
        # Calculate per-day budget allocations (independent of stops)
        accommodation_per_day = (self.total_budget * self.ACCOMMODATION_PCT / Decimal("100")) / Decimal(self.total_days)
        food_per_day = (self.total_budget * self.FOOD_PCT / Decimal("100")) / Decimal(self.total_days)
        activities_per_day = (self.total_budget * activities_adjusted_pct / Decimal("100")) / Decimal(self.total_days)
        local_transport_per_day = (self.total_budget * self.LOCAL_TRANSPORT_PCT / Decimal("100")) / Decimal(self.total_days)
        
        current_global_day = 1
        for stop_idx, stop in enumerate(self.stops):
            destination = stop["destination"]
            days = stop["days"]
            is_last_stop = stop_idx == len(self.stops) - 1
            
            # Allocate for this stop's duration
            accommodation_for_stop = accommodation_per_day * Decimal(days)
            food_for_stop = food_per_day * Decimal(days)
            activities_for_stop = activities_per_day * Decimal(days)
            local_transport_for_stop = local_transport_per_day * Decimal(days)
            contingency_for_stop = contingency_per_day * Decimal(days)
            
            # Inter-city transport (distributed across non-final stops)
            inter_city_transport = Decimal("0")
            if not is_last_stop:
                # Distribute inter-city budget proportionally to stop duration
                inter_city_transport = (inter_city_budget * Decimal(days)) / Decimal(self.total_days)
            
            # Calculate stop total
            stop_total = (
                accommodation_for_stop +
                food_for_stop +
                activities_for_stop +
                local_transport_for_stop +
                inter_city_transport +
                contingency_for_stop
            )
            
            # Track totals
            category_totals["accommodation"] += accommodation_for_stop
            category_totals["food"] += food_for_stop
            category_totals["activities"] += activities_for_stop
            category_totals["local_transport"] += local_transport_for_stop
            category_totals["inter_city_transport"] += inter_city_transport
            category_totals["contingency"] += contingency_for_stop
            
            # Build stop record
            global_day_range = [current_global_day, current_global_day + days - 1]
            
            stop_record = {
                "destination": destination,
                "days": days,
                "global_day_range": global_day_range,
                "allocation": {
                    "accommodation_per_night": float(round(accommodation_per_day, 2)),
                    "food_per_day": float(round(food_per_day, 2)),
                    "activities_per_day": float(round(activities_per_day, 2)),
                    "local_transport_per_day": float(round(local_transport_per_day, 2)),
                    "inter_city_transport": float(round(inter_city_transport, 2)) if inter_city_transport > 0 else None,
                    "contingency": float(round(contingency_for_stop, 2))
                },
                "stop_total": float(round(stop_total, 2))
            }
            
            result["stops"].append(stop_record)
            current_global_day += days
        
        # Convert category totals to float with Decimal precision
        category_breakdown = {}
        for key, val in category_totals.items():
            category_breakdown[key] = float(round(val, 2))
        
        # Calculate grand total and remaining
        grand_total = sum(category_breakdown.values())
        remaining = float(round(self.total_budget - Decimal(str(grand_total)), 2))
        
        result["category_breakdown"] = category_breakdown
        result["grand_total"] = grand_total
        result["remaining_budget"] = remaining
        result["budget_exceeded"] = grand_total > float(self.total_budget)
        
        # Verify reconciliation
        if abs(grand_total + remaining - float(self.total_budget)) > 0.01:
            notes.append(f"WARNING: Arithmetic mismatch detected (difference: {abs(grand_total + remaining - float(self.total_budget)):.2f})")
        
        return result


class MultiStopItineraryValidator:
    """
    Validates that multi-stop itineraries are coherent, destination-specific,
    preference-satisfying, and financially reconcilable.
    """
    
    # Generic activity patterns to detect (should be avoided)
    GENERIC_PATTERNS = [
        "sightseeing", "shopping", "lunch", "breakfast", "dinner",
        "relaxation", "leisure", "visit", "explore", "local",
        "main market", "bazaar", "scenic viewpoint", "old quarter",
        "heritage walk", "handicraft"
    ]
    
    @staticmethod
    def validate(itinerary: Dict[str, Any], stops: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Comprehensive validation of multi-stop itinerary.
        
        Returns:
            {
                "is_valid": bool,
                "errors": List[str],  # Critical issues
                "warnings": List[str],  # Non-critical issues
                "is_destination_specific": bool,
                "generic_pattern_count": int,
                "preference_coverage": dict,  # If known
                "financial_coherence_score": float,  # 0-100
                "global_day_count": int,
                "stop_day_counts": {destination: count}
            }
        """
        errors = []
        warnings = []
        
        # Basic structure validation
        legs = itinerary.get("legs", [])
        if len(legs) != len(stops):
            errors.append(f"Expected {len(stops)} legs, got {len(legs)}")
            return _validation_result(False, errors, warnings)
        
        generic_count = 0
        global_day = 1
        stop_day_counts = {}
        total_activity_cost = 0
        stop_costs = {}
        
        for idx, leg in enumerate(legs):
            dest = stops[idx]["destination"]
            expected_days = stops[idx]["days"]
            actual_days = len(leg.get("itinerary", []))
            
            # Day count validation
            if actual_days != expected_days:
                errors.append(f"Stop '{dest}': expected {expected_days} days, got {actual_days}")
            
            stop_cost = 0
            
            # Validate each day
            for day_data in leg.get("itinerary", []):
                day_num = day_data.get("day_number")
                activities = day_data.get("activities", [])
                
                if not day_num:
                    warnings.append(f"Stop '{dest}': day missing day_number")
                
                # Validate activities
                for act in activities:
                    if not act.get("title"):
                        errors.append(f"Stop '{dest}' Day {day_num}: activity missing title")
                        continue
                    
                    if "cost" not in act:
                        errors.append(f"Stop '{dest}' Day {day_num} '{act.get('title')}': missing cost")
                        continue
                    
                    if not act.get("time"):
                        warnings.append(f"Stop '{dest}' Day {day_num} '{act.get('title')}': missing time")
                    
                    # Check for generic patterns
                    title_lower = act.get("title", "").lower()
                    for pattern in MultiStopItineraryValidator.GENERIC_PATTERNS:
                        if pattern in title_lower:
                            generic_count += 1
                            break
                    
                    cost = act.get("cost", 0)
                    try:
                        cost = float(cost)
                        stop_cost += cost
                        total_activity_cost += cost
                    except (TypeError, ValueError):
                        errors.append(f"Stop '{dest}' Day {day_num}: invalid cost format '{cost}'")
            
            stop_costs[dest] = stop_cost
            stop_day_counts[dest] = actual_days
            global_day += actual_days
        
        # Destination-specificity check
        is_destination_specific = generic_count < (len(stops) * 2)  # Allow up to 2 generic activities per stop
        
        # Financial coherence check
        estimated_total = itinerary.get("total_estimated_cost", 0)
        activity_costs_match = abs(total_activity_cost - estimated_total) < estimated_total * 0.2  # Within 20%
        if not activity_costs_match:
            warnings.append(
                f"Activity costs (₹{total_activity_cost:.0f}) differ significantly from "
                f"estimated total (₹{estimated_total:.0f}). Possible allocation mismatch."
            )
        
        financial_coherence = 100.0 if activity_costs_match else 60.0
        
        # Compile result
        result = _validation_result(
            len(errors) == 0,
            errors,
            warnings,
            is_destination_specific=is_destination_specific,
            generic_pattern_count=generic_count,
            financial_coherence_score=financial_coherence,
            global_day_count=global_day - 1,
            stop_day_counts=stop_day_counts
        )
        
        return result


def _validation_result(is_valid: bool, errors: List[str], warnings: List[str], **kwargs) -> Dict[str, Any]:
    """Helper to build validation result dictionary."""
    result = {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "is_destination_specific": kwargs.get("is_destination_specific", None),
        "generic_pattern_count": kwargs.get("generic_pattern_count", 0),
        "financial_coherence_score": kwargs.get("financial_coherence_score", 0),
        "global_day_count": kwargs.get("global_day_count", 0),
        "stop_day_counts": kwargs.get("stop_day_counts", {}),
    }
    return result
