"""
Validation and quality checking for personalized travel plans.

Checks:
- Structural correctness (day count, numbering, fields)
- Financial soundness (costs non-negative, totals reconcile)
- Requirement coverage (user requirements met)
- Semantic quality (activities relevant to destination, coherent schedule)
"""

from typing import List, Dict, Tuple, Optional
import re
from app.schemas import PersonalizedPlanResponse, PersonalizedPlanValidationResult, Requirement


class PersonalizedPlanValidator:
    """Validates generated personalized plans for quality and correctness."""
    
    # Placeholder words that indicate generic content
    GENERIC_PLACEHOLDERS = [
        "local restaurant", "favorite restaurant", "favorite spot",
        "main attraction", "orientation tour", "scenic viewpoint",
        "last-minute shopping", "explore", "sightseeing", "local market",
        "local lunch", "local food", "local experience", "local area"
    ]
    
    def __init__(self, plan: PersonalizedPlanResponse):
        """Initialize validator with a plan."""
        self.plan = plan
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed: Dict[str, bool] = {}
    
    def validate(self) -> PersonalizedPlanValidationResult:
        """
        Run all validation checks and return overall result.
        
        Returns:
            PersonalizedPlanValidationResult with all check results
        """
        # Structural checks
        self._check_day_count()
        self._check_day_numbering()
        self._check_day_titles()
        self._check_activity_presence()
        
        # Financial checks
        self._check_activity_costs()
        self._check_budget_reconciliation()
        self._check_budget_limit()
        
        # Semantic checks
        self._check_for_placeholders()
        self._check_activity_variety()
        self._check_activity_timing()
        
        # Requirement coverage
        requirements_met, requirements_total = self._check_requirement_coverage()
        
        # Calculate quality scores
        semantic_score = self._calculate_semantic_score()
        feasibility_score = self._calculate_feasibility_score()
        requirement_coverage_score = self._calculate_requirement_coverage_score(requirements_met, requirements_total)
        
        # Determine overall validity
        is_valid = len(self.errors) == 0
        
        # Calculate composite score (0-100)
        composite_score = (semantic_score + feasibility_score + requirement_coverage_score) / 3.0 if is_valid else 0.0
        
        return PersonalizedPlanValidationResult(
            is_valid=is_valid,
            score=composite_score,
            errors=self.errors,
            warnings=self.warnings,
            checks_passed=self.checks_passed,
            requirements_met=requirements_met,
            requirements_total=requirements_total,
            semantic_score=semantic_score,
            feasibility_score=feasibility_score,
            requirement_coverage_score=requirement_coverage_score,
        )
    
    # ========== STRUCTURAL CHECKS ==========
    
    def _check_day_count(self) -> None:
        """Check that the number of days matches the requested duration."""
        expected = self.plan.num_days
        actual = len(self.plan.days)
        
        if actual != expected:
            self.errors.append(f"Day count mismatch: expected {expected}, got {actual}")
            self.checks_passed["day_count"] = False
        else:
            self.checks_passed["day_count"] = True
    
    def _check_day_numbering(self) -> None:
        """Check that days are numbered 1, 2, 3, ... without gaps or duplicates."""
        day_numbers = [day.day_number for day in self.plan.days]
        
        # Check for duplicates
        if len(day_numbers) != len(set(day_numbers)):
            self.errors.append("Duplicate day numbers found")
            self.checks_passed["day_numbering"] = False
            return
        
        # Check for continuous sequence starting from 1
        expected_numbers = list(range(1, self.plan.num_days + 1))
        if day_numbers != expected_numbers:
            self.errors.append(f"Day numbering not continuous: got {day_numbers}, expected {expected_numbers}")
            self.checks_passed["day_numbering"] = False
        else:
            self.checks_passed["day_numbering"] = True
    
    def _check_day_titles(self) -> None:
        """Check that day titles are unique and not generic."""
        titles = [day.title for day in self.plan.days]
        
        # Check for duplicates
        if len(titles) != len(set(titles)):
            self.errors.append("Duplicate day titles found")
            self.checks_passed["day_titles"] = False
            return
        
        # Check for generic titles (e.g., "Day 1 — Day 1", "DAY 01 — Day 1")
        generic_count = 0
        for title in titles:
            if re.search(r"day\s+\d+.*day\s+\d+|DAY\s+\d+.*DAY\s+\d+", title, re.IGNORECASE):
                generic_count += 1
                self.warnings.append(f"Generic title format: '{title}'")
        
        if generic_count > 0:
            self.checks_passed["day_titles"] = False
        else:
            self.checks_passed["day_titles"] = True
    
    def _check_activity_presence(self) -> None:
        """Check that each day has activities."""
        days_without_activities = [day.day_number for day in self.plan.days if not day.activities]
        
        if days_without_activities:
            self.errors.append(f"Days without activities: {days_without_activities}")
            self.checks_passed["activity_presence"] = False
        else:
            self.checks_passed["activity_presence"] = True
    
    # ========== FINANCIAL CHECKS ==========
    
    def _check_activity_costs(self) -> None:
        """Check that all activity costs are non-negative."""
        negative_activities = []
        
        for day in self.plan.days:
            for activity in day.activities:
                if activity.cost < 0:
                    negative_activities.append({
                        "day": day.day_number,
                        "activity": activity.title,
                        "cost": activity.cost
                    })
        
        if negative_activities:
            self.errors.append(f"Negative activity costs found: {negative_activities}")
            self.checks_passed["activity_costs"] = False
        else:
            self.checks_passed["activity_costs"] = True
    
    def _check_budget_reconciliation(self) -> None:
        """Check that daily totals and breakdown reconcile with estimated total."""
        # Sum all activity costs
        total_activity_costs = 0.0
        for day in self.plan.days:
            for activity in day.activities:
                total_activity_costs += activity.cost
        
        # Compare with estimated_total_cost
        tolerance = max(self.plan.budget_limit * 0.02, 100.0)  # 2% or Rs. 100
        
        if abs(total_activity_costs - self.plan.estimated_total_cost) > tolerance:
            self.warnings.append(
                f"Activity costs (Rs. {total_activity_costs:.2f}) differ from estimated total "
                f"(Rs. {self.plan.estimated_total_cost:.2f}) by more than tolerance (Rs. {tolerance:.2f})"
            )
        
        # Check budget breakdown sums correctly
        breakdown = self.plan.budget_breakdown
        breakdown_total = (
            breakdown.accommodation_per_night * self.plan.num_days +
            breakdown.food_per_day * self.plan.num_days +
            breakdown.activities_per_day * self.plan.num_days +
            breakdown.transport +
            breakdown.contingency
        )
        
        if abs(breakdown_total - self.plan.estimated_total_cost) > tolerance:
            self.errors.append(
                f"Budget breakdown (Rs. {breakdown_total:.2f}) doesn't match estimated total "
                f"(Rs. {self.plan.estimated_total_cost:.2f})"
            )
            self.checks_passed["budget_reconciliation"] = False
        else:
            self.checks_passed["budget_reconciliation"] = True
    
    def _check_budget_limit(self) -> None:
        """Check that estimated total does not exceed budget limit."""
        if self.plan.estimated_total_cost > self.plan.budget_limit:
            self.errors.append(
                f"Estimated total (Rs. {self.plan.estimated_total_cost:.2f}) exceeds budget limit "
                f"(Rs. {self.plan.budget_limit:.2f})"
            )
            self.checks_passed["budget_limit"] = False
        else:
            self.checks_passed["budget_limit"] = True
    
    # ========== SEMANTIC CHECKS ==========
    
    def _check_for_placeholders(self) -> None:
        """Check for generic placeholder text in activities."""
        placeholder_count = 0
        
        for day in self.plan.days:
            for activity in day.activities:
                title_lower = activity.title.lower()
                location_lower = (activity.location or "").lower()
                description_lower = activity.description.lower()
                
                for placeholder in self.GENERIC_PLACEHOLDERS:
                    if placeholder in title_lower or placeholder in location_lower or placeholder in description_lower:
                        placeholder_count += 1
                        self.warnings.append(f"Generic placeholder '{placeholder}' found in: {activity.title}")
        
        if placeholder_count > (self.plan.num_days * 2):  # Allow some generic text
            self.checks_passed["placeholder_check"] = False
        else:
            self.checks_passed["placeholder_check"] = True
    
    def _check_activity_variety(self) -> None:
        """Check that activities vary across days (no repetitive templates)."""
        # Collect activity titles
        all_titles = []
        for day in self.plan.days:
            for activity in day.activities:
                all_titles.append(activity.title.lower())
        
        # Check if more than 50% are similar/duplicated
        unique_ratio = len(set(all_titles)) / len(all_titles) if all_titles else 1.0
        
        if unique_ratio < 0.7:  # Less than 70% unique
            self.warnings.append(f"Low activity variety: only {unique_ratio*100:.0f}% unique titles")
            self.checks_passed["activity_variety"] = False
        else:
            self.checks_passed["activity_variety"] = True
    
    def _check_activity_timing(self) -> None:
        """Check that activity times are coherent and don't overlap."""
        time_sequence = ["morning", "afternoon", "evening"]
        
        for day in self.plan.days:
            day_times = [activity.time.lower() for activity in day.activities]
            
            # Check if times are in logical order
            for i in range(len(day_times) - 1):
                current_idx = time_sequence.index(day_times[i]) if day_times[i] in time_sequence else -1
                next_idx = time_sequence.index(day_times[i + 1]) if day_times[i + 1] in time_sequence else -1
                
                if current_idx > next_idx:
                    self.warnings.append(f"Day {day.day_number}: times not in logical order")
        
        self.checks_passed["activity_timing"] = True  # Non-blocking warning
    
    # ========== REQUIREMENT COVERAGE ==========
    
    def _check_requirement_coverage(self) -> Tuple[int, int]:
        """
        Check if generated plan covers user requirements.
        
        Returns:
            Tuple of (requirements_met, requirements_total)
        """
        if not self.plan.requirements_extracted:
            return (0, 0)
        
        requirements_met = 0
        requirements_total = len(self.plan.requirements_extracted)
        
        # Check each requirement
        for requirement in self.plan.requirements_extracted:
            if self._check_requirement_in_itinerary(requirement):
                requirements_met += 1
                requirement.coverage_status = "covered"
            else:
                if requirement.mandatory:
                    self.errors.append(f"Mandatory requirement not met: {requirement.key}")
                else:
                    self.warnings.append(f"Optional requirement not met: {requirement.key}")
                requirement.coverage_status = "not_covered"
        
        self.checks_passed["requirements"] = (requirements_met == requirements_total)
        return (requirements_met, requirements_total)
    
    def _check_requirement_in_itinerary(self, requirement: Requirement) -> bool:
        """Check if a specific requirement is satisfied in the itinerary."""
        # Convert requirement to searchable terms
        search_terms = self._get_search_terms_for_requirement(requirement)
        
        # Search through all activities and descriptions
        for day in self.plan.days:
            day_text = (day.title + " " + day.description).lower()
            
            for activity in day.activities:
                activity_text = (
                    activity.title + " " +
                    activity.description + " " +
                    (activity.location or "")
                ).lower()
                
                # Check if any search term appears
                for term in search_terms:
                    if term in activity_text or term in day_text:
                        return True
        
        # Also check plan summary
        if self.plan.summary:
            for term in search_terms:
                if term in self.plan.summary.lower():
                    return True
        
        return False
    
    def _get_search_terms_for_requirement(self, requirement: Requirement) -> List[str]:
        """Get searchable terms for a requirement."""
        terms = [requirement.value, requirement.value.replace("_", " ")]
        
        # Add aliases for common cuisine requirements
        if requirement.key == "cuisine:bengali":
            terms.extend(["bengal", "bengali cuisine", "bengali food", "luchi", "fish curry"])
        elif requirement.key == "cuisine:south_indian":
            terms.extend(["south india", "south indian cuisine", "south indian food", "dosa", "idli", "sambar", "spice market"])
        elif requirement.key == "cuisine:north_indian":
            terms.extend(["north india", "north indian cuisine", "north indian food", "biryani", "tandoori", "naan"])
        elif requirement.key == "cuisine:seafood":
            terms.extend(["fish", "prawn", "shrimp", "shellfish", "coastal", "fishing"])
        elif requirement.key == "cuisine:vegetarian":
            terms.extend(["veg", "vegetable", "plant-based", "dal", "paneer"])
        
        # Add aliases for common activity requirements
        elif requirement.key == "activity:river_cruise":
            terms.extend(["river", "cruise", "boat", "hooghly", "ganges", "ferry"])
        elif requirement.key == "activity:trekking":
            terms.extend(["trek", "hike", "hiking", "trail", "mountain", "peak"])
        elif requirement.key == "activity:heritage":
            terms.extend(["heritage", "historic", "monument", "archaeology", "fort", "palace"])
        
        # Add aliases for comfort requirements
        elif requirement.key == "comfort:luxury":
            terms.extend(["luxury", "premium", "upscale", "fancy", "5-star", "deluxe"])
        elif requirement.key == "comfort:budget":
            terms.extend(["budget", "affordable", "economical", "backpack"])
        
        return terms
    
    # ========== SCORING ==========
    
    def _calculate_semantic_score(self) -> float:
        """Calculate semantic quality score (0-100)."""
        if not self.checks_passed.get("placeholder_check", True):
            return 40.0
        if not self.checks_passed.get("activity_variety", True):
            return 50.0
        if not self.checks_passed.get("day_titles", True):
            return 60.0
        return 85.0
    
    def _calculate_feasibility_score(self) -> float:
        """Calculate feasibility/structural score (0-100)."""
        score = 100.0
        
        if not self.checks_passed.get("day_count", True):
            score -= 20
        if not self.checks_passed.get("day_numbering", True):
            score -= 15
        if not self.checks_passed.get("activity_timing", True):
            score -= 5
        if not self.checks_passed.get("activity_presence", True):
            score -= 20
        
        return max(0.0, score)
    
    def _calculate_requirement_coverage_score(self, met: int, total: int) -> float:
        """Calculate requirement coverage score (0-100)."""
        if total == 0:
            return 100.0  # No requirements, so full score
        return (met / total) * 100.0
