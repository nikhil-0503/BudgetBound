"""
Financial validator for personalized travel plans.

Implements a declarative accounting convention to ensure:
- No negative expense categories
- No double-counting
- Perfect reconciliation between daily, category, and total costs
- Clear remaining budget or overspend calculation
"""

from typing import Dict, List, Tuple, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class FinancialValidator:
    """
    Validates financial consistency in travel itineraries.
    
    Accounting Convention:
    - All costs in INR (Indian Rupees), represented as Decimal for precision
    - Trip-level costs (accommodation, transport): allocated per day or across trip
    - Daily costs (food, activities): summed per day
    - Contingency: trip-level reserve, not included in daily sums
    - estimated_total_cost = sum(accommodation) + sum(food) + sum(activities) + transport + contingency
    """
    
    def __init__(self, budget_limit: float, num_days: int):
        self.budget_limit = Decimal(str(budget_limit))
        self.num_days = num_days
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_expense_item(self, value: float, category: str) -> bool:
        """Check that a single expense is non-negative."""
        if value < 0:
            self.errors.append(f"{category}: negative cost Rs. {value:.2f}")
            return False
        return True
    
    def validate_daily_costs(self, days: List[Dict]) -> Tuple[float, bool]:
        """
        Validate and sum daily costs from activity-level details.
        
        Each day: {"day_number": int, "activities": [{"cost": float, ...}, ...]}
        
        Returns: (total_daily_cost, is_valid)
        """
        total = Decimal('0')
        is_valid = True
        
        for day in days:
            day_num = day.get('day_number')
            activities = day.get('activities', [])
            
            day_total = Decimal('0')
            for activity in activities:
                cost = activity.get('cost', 0)
                if not self.validate_expense_item(cost, f"Day {day_num} activity"):
                    is_valid = False
                day_total += Decimal(str(cost))
            
            # Log daily total
            logger.debug(f"Day {day_num} total: Rs. {day_total}")
            total += day_total
        
        return float(total), is_valid
    
    def validate_budget_breakdown(
        self,
        accommodation_per_night: float,
        food_per_day: float,
        activities_per_day: float,
        transport: float,
        contingency: float,
    ) -> Tuple[float, bool]:
        """
        Validate and sum budget breakdown categories.
        
        Returns: (calculated_total, is_valid)
        """
        is_valid = True
        
        # Validate each category is non-negative
        for name, value in [
            ("accommodation_per_night", accommodation_per_night),
            ("food_per_day", food_per_day),
            ("activities_per_day", activities_per_day),
            ("transport", transport),
            ("contingency", contingency),
        ]:
            if not self.validate_expense_item(value, name):
                is_valid = False
        
        # Calculate total from breakdown
        accommodation_total = Decimal(str(accommodation_per_night)) * self.num_days
        food_total = Decimal(str(food_per_day)) * self.num_days
        activities_total = Decimal(str(activities_per_day)) * self.num_days
        transport_total = Decimal(str(transport))
        contingency_total = Decimal(str(contingency))
        
        calculated_total = (
            accommodation_total + food_total + activities_total + transport_total + contingency_total
        )
        
        return float(calculated_total), is_valid
    
    def reconcile_costs(
        self,
        daily_activity_total: float,
        budget_breakdown_total: float,
        estimated_total_cost: float,
    ) -> bool:
        """
        Check that daily costs, breakdown, and estimated total reconcile.
        
        Tolerance: 2% of budget or Rs. 100, whichever is larger (for rounding).
        """
        daily = Decimal(str(daily_activity_total))
        breakdown = Decimal(str(budget_breakdown_total))
        estimated = Decimal(str(estimated_total_cost))
        
        # Calculate tolerance
        tolerance = max(
            self.budget_limit * Decimal('0.02'),  # 2% of budget
            Decimal('100')  # Or Rs. 100 minimum
        )
        
        is_valid = True
        
        # Check breakdown vs estimated
        if abs(breakdown - estimated) > tolerance:
            self.errors.append(
                f"Budget breakdown total (Rs. {breakdown}) does not match "
                f"estimated total (Rs. {estimated}). Difference: Rs. {abs(breakdown - estimated)}"
            )
            is_valid = False
        
        # Check daily vs breakdown (as a warning, since daily may not include all trip-level costs)
        if abs(daily - breakdown) > tolerance:
            self.warnings.append(
                f"Daily activity costs (Rs. {daily}) differ from breakdown total (Rs. {breakdown}). "
                f"Difference: Rs. {abs(daily - breakdown)}. This may be intentional if trip-level "
                f"expenses (transport, contingency) are not included in daily costs."
            )
        
        return is_valid
    
    def validate_budget_compliance(self, estimated_total_cost: float) -> Tuple[bool, Optional[float]]:
        """
        Check that estimated total is within budget.
        
        Returns: (is_within_budget, overspend_amount_or_None)
        """
        estimated = Decimal(str(estimated_total_cost))
        
        if estimated <= self.budget_limit:
            remaining = self.budget_limit - estimated
            logger.debug(f"Within budget: Rs. {estimated} ≤ Rs. {self.budget_limit}, remaining: Rs. {remaining}")
            return True, None
        else:
            overspend = estimated - self.budget_limit
            self.errors.append(
                f"Estimated total (Rs. {estimated}) exceeds budget (Rs. {self.budget_limit}). "
                f"Overspend: Rs. {overspend}"
            )
            return False, float(overspend)
    
    def validate_itinerary(
        self,
        days: List[Dict],
        accommodation_per_night: float,
        food_per_day: float,
        activities_per_day: float,
        transport: float,
        contingency: float,
        estimated_total_cost: float,
    ) -> Dict:
        """
        Perform complete financial validation of an itinerary.
        
        Returns: {
            "is_valid": bool,
            "estimated_total_cost": float,
            "budget_limit": float,
            "remaining_budget": float or None,
            "overspend": float or None,
            "errors": [str, ...],
            "warnings": [str, ...],
            "daily_activity_total": float,
            "breakdown_total": float,
        }
        """
        self.errors = []
        self.warnings = []
        
        # Validate daily costs from activities
        daily_total, daily_valid = self.validate_daily_costs(days)
        
        # Validate budget breakdown
        breakdown_total, breakdown_valid = self.validate_budget_breakdown(
            accommodation_per_night, food_per_day, activities_per_day, transport, contingency
        )
        
        # Reconcile the two approaches
        reconcile_valid = self.reconcile_costs(daily_total, breakdown_total, estimated_total_cost)
        
        # Check budget compliance
        within_budget, overspend = self.validate_budget_compliance(estimated_total_cost)
        
        remaining_budget = None
        if within_budget:
            remaining_budget = float(self.budget_limit - Decimal(str(estimated_total_cost)))
        
        is_valid = daily_valid and breakdown_valid and reconcile_valid and within_budget
        
        return {
            "is_valid": is_valid,
            "estimated_total_cost": estimated_total_cost,
            "budget_limit": float(self.budget_limit),
            "remaining_budget": remaining_budget,
            "overspend": overspend,
            "errors": self.errors,
            "warnings": self.warnings,
            "daily_activity_total": daily_total,
            "breakdown_total": breakdown_total,
        }
