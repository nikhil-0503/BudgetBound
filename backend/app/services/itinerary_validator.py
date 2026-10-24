"""
Reusable, destination-agnostic itinerary quality validation.

Checks for:
- Structural validity (day count, numbering, titles, activities)
- Financial consistency (costs, reconciliation, budget compliance)
- Semantic quality (specificity, not placeholders, variety, coherence)
- Requirement fulfillment
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class ItineraryValidator:
    """
    Validates itinerary structure, quality, and requirement fulfillment.
    
    Uses only generic checks; does not depend on destination-specific rules.
    """
    
    # Generic placeholder patterns that indicate low-quality content
    PLACEHOLDER_PATTERNS = [
        r'\bTBD\b',
        r'\bTBA\b',
        r'orientation tour',
        r'local restaurant',
        r'favorite spot',
        r'main attraction',
        r'scenic viewpoint',
        r'last-minute shopping',
        r'explore (?!the|your)',
        r'sightseeing',
        r'local market',
        r'local lunch',
        r'local food',
        r'local experience',
        r'local area',
        r'day \d+ - day \d+',  # Redundant heading format
    ]
    
    MINIMUM_ACTIVITY_UNIQUENESS = 0.7  # At least 70% of activities should be unique
    MINIMUM_DAY_TITLE_LENGTH = 15  # At least 15 characters for a descriptive title
    
    def __init__(self, destination: str, num_days: int, requirements: Optional[List] = None):
        self.destination = destination
        self.num_days = num_days
        self.requirements = requirements or []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed: Dict[str, bool] = {}
    
    # ===== STRUCTURAL CHECKS =====
    
    def check_day_count(self, days: List[Dict]) -> bool:
        """Verify that the number of days matches the requested duration."""
        actual = len(days)
        if actual != self.num_days:
            self.errors.append(
                f"Day count mismatch: expected {self.num_days}, got {actual}"
            )
            self.checks_passed['day_count'] = False
            return False
        self.checks_passed['day_count'] = True
        return True
    
    def check_day_numbering(self, days: List[Dict]) -> bool:
        """Verify days are numbered 1, 2, 3, ... without gaps or duplicates."""
        day_numbers = [d.get('day_number') for d in days]
        
        # Check for duplicates
        if len(day_numbers) != len(set(day_numbers)):
            self.errors.append("Duplicate day numbers found")
            self.checks_passed['day_numbering'] = False
            return False
        
        # Check for continuous sequence
        expected = list(range(1, self.num_days + 1))
        if day_numbers != expected:
            self.errors.append(
                f"Day numbering not continuous: got {day_numbers}, expected {expected}"
            )
            self.checks_passed['day_numbering'] = False
            return False
        
        self.checks_passed['day_numbering'] = True
        return True
    
    def check_day_titles(self, days: List[Dict]) -> bool:
        """Verify day titles are unique, descriptive, and not generic."""
        titles = [d.get('title', '') for d in days]
        
        # Check for duplicates
        if len(titles) != len(set(titles)):
            self.errors.append("Duplicate day titles found")
            self.checks_passed['day_titles'] = False
            return False
        
        is_valid = True
        
        # Check each title for issues
        for title in titles:
            # Check for redundant heading format: "DAY 01 - Day 1 - ..."
            if re.search(r'day\s+\d+.*day\s+\d+', title, re.IGNORECASE):
                self.warnings.append(f"Redundant day title format: '{title}'")
                is_valid = False
            
            # Check minimum length
            if len(title) < self.MINIMUM_DAY_TITLE_LENGTH:
                self.warnings.append(
                    f"Day title too short or generic: '{title}' ({len(title)} chars, min {self.MINIMUM_DAY_TITLE_LENGTH})"
                )
                is_valid = False
        
        self.checks_passed['day_titles'] = is_valid
        return is_valid
    
    def check_activity_presence(self, days: List[Dict]) -> bool:
        """Verify each day has at least one activity."""
        days_without_activities = []
        for day in days:
            activities = day.get('activities', [])
            if not activities or len(activities) == 0:
                days_without_activities.append(day.get('day_number'))
        
        if days_without_activities:
            self.errors.append(f"Days without activities: {days_without_activities}")
            self.checks_passed['activity_presence'] = False
            return False
        
        self.checks_passed['activity_presence'] = True
        return True
    
    # ===== FINANCIAL CHECKS =====
    
    def check_nonnegative_costs(self, days: List[Dict]) -> bool:
        """Verify all activity costs are non-negative."""
        negative_found = []
        for day in days:
            for activity in day.get('activities', []):
                cost = activity.get('cost', 0)
                if cost < 0:
                    negative_found.append({
                        'day': day.get('day_number'),
                        'activity': activity.get('title'),
                        'cost': cost
                    })
        
        if negative_found:
            self.errors.append(f"Negative activity costs found: {negative_found}")
            self.checks_passed['nonnegative_costs'] = False
            return False
        
        self.checks_passed['nonnegative_costs'] = True
        return True
    
    # ===== SEMANTIC CHECKS =====
    
    def check_for_placeholders(self, days: List[Dict]) -> bool:
        """Check for generic placeholder text indicating low-quality content."""
        placeholder_count = 0
        
        for day in days:
            for activity in day.get('activities', []):
                title = activity.get('title', '').lower()
                description = activity.get('description', '').lower()
                location = activity.get('location', '').lower()
                
                full_text = f"{title} {description} {location}"
                
                for pattern in self.PLACEHOLDER_PATTERNS:
                    if re.search(pattern, full_text, re.IGNORECASE):
                        placeholder_count += 1
                        self.warnings.append(
                            f"Placeholder detected in activity: '{activity.get('title')}' "
                            f"(matched pattern: {pattern})"
                        )
                        break  # Count once per activity
        
        # Allow some generic text, but flag if excessive
        max_allowed = max(2, self.num_days)  # Allow ~2 per day
        is_valid = placeholder_count <= max_allowed
        
        if not is_valid:
            self.warnings.append(
                f"High placeholder count ({placeholder_count}): content may be too generic"
            )
        
        self.checks_passed['placeholder_check'] = is_valid
        return is_valid
    
    def check_activity_variety(self, days: List[Dict]) -> bool:
        """Check that activities vary across days (not repetitive templates)."""
        all_titles = []
        for day in days:
            for activity in day.get('activities', []):
                all_titles.append(activity.get('title', '').lower())
        
        if not all_titles:
            self.checks_passed['activity_variety'] = True
            return True
        
        unique_ratio = len(set(all_titles)) / len(all_titles)
        is_valid = unique_ratio >= self.MINIMUM_ACTIVITY_UNIQUENESS
        
        if not is_valid:
            self.warnings.append(
                f"Low activity variety: {unique_ratio*100:.0f}% unique titles "
                f"(minimum {self.MINIMUM_ACTIVITY_UNIQUENESS*100:.0f}% required)"
            )
        
        self.checks_passed['activity_variety'] = is_valid
        return is_valid
    
    def check_activity_specificity(self, days: List[Dict]) -> bool:
        """Check that activities include specific details (not vague descriptions)."""
        low_specificity = []
        
        for day in days:
            for activity in day.get('activities', []):
                title = activity.get('title', '')
                location = activity.get('location', '')
                description = activity.get('description', '')
                
                # Specificity indicators: proper nouns, specific numbers, place names
                has_location = len(location) > 0 and location.lower() not in ['local', 'city', 'area']
                has_description = len(description) > 10  # More than just a few words
                has_details = any(
                    keyword in title.lower() for keyword in ['restaurant', 'temple', 'museum', 'market', 'fort', 'river', 'beach', 'park']
                )
                
                if not (has_location and has_description and (has_details or len(title) > 20)):
                    low_specificity.append(activity.get('title'))
        
        if low_specificity:
            self.warnings.append(
                f"Low specificity detected in {len(low_specificity)} activities: "
                f"{low_specificity[:3]}{'...' if len(low_specificity) > 3 else ''}"
            )
            is_valid = len(low_specificity) <= self.num_days  # Allow some vague activities
        else:
            is_valid = True
        
        self.checks_passed['activity_specificity'] = is_valid
        return is_valid
    
    def check_activity_timing(self, days: List[Dict]) -> bool:
        """Check that activity times are coherent (morning → afternoon → evening)."""
        time_order = ['morning', 'afternoon', 'evening']
        time_sequence_issues = []
        
        for day in days:
            day_times = [a.get('time', '').lower() for a in day.get('activities', [])]
            
            # Check if times follow logical order
            prev_idx = -1
            for i, time_str in enumerate(day_times):
                current_idx = -1
                for j, time_val in enumerate(time_order):
                    if time_val in time_str:
                        current_idx = j
                        break
                
                if current_idx >= 0 and current_idx < prev_idx:
                    time_sequence_issues.append(f"Day {day.get('day_number')}: time reversal")
                    break
                
                if current_idx >= 0:
                    prev_idx = current_idx
        
        if time_sequence_issues:
            self.warnings.append(f"Time sequencing issues: {time_sequence_issues}")
            is_valid = False
        else:
            is_valid = True
        
        self.checks_passed['activity_timing'] = is_valid
        return is_valid
    
    # ===== REQUIREMENT CHECKS =====
    
    def check_requirement_coverage(self, days: List[Dict], requirements: Optional[List] = None) -> Tuple[int, int]:
        """
        Check if itinerary covers extracted user requirements.
        
        Returns: (requirements_met, requirements_total)
        """
        if requirements:
            self.requirements = requirements
        
        if not self.requirements:
            self.checks_passed['requirement_coverage'] = True
            return (0, 0)
        
        met = 0
        total = len(self.requirements)
        
        # Build searchable text from itinerary
        itinerary_text = self._build_itinerary_text(days)
        
        for req in self.requirements:
            # Get search terms from requirement (handles both dict and Pydantic)
            search_terms = self._get_search_terms(req)
            
            # Check if any search term appears in itinerary
            found = False
            for term in search_terms:
                if term.lower() in itinerary_text.lower():
                    found = True
                    met += 1
                    break
            
            # Check if mandatory (handle both dict and Pydantic)
            is_mandatory = getattr(req, 'mandatory', False) if not isinstance(req, dict) else req.get('mandatory', False)
            
            req_value = getattr(req, 'value', None) if not isinstance(req, dict) else req.get('value')
            req_category = getattr(req, 'category', None) if not isinstance(req, dict) else req.get('category')
            
            if not found and is_mandatory:
                self.errors.append(
                    f"Mandatory requirement not satisfied: {req_value} ({req_category})"
                )
            elif not found:
                self.warnings.append(
                    f"Optional requirement not satisfied: {req_value} ({req_category})"
                )
        
        is_valid = met == total  # All requirements met
        self.checks_passed['requirement_coverage'] = is_valid
        return (met, total)
    
    def _build_itinerary_text(self, days: List[Dict]) -> str:
        """Build a searchable text representation of the itinerary."""
        parts = []
        for day in days:
            parts.append(day.get('title', ''))
            parts.append(day.get('description', ''))
            for activity in day.get('activities', []):
                parts.append(activity.get('title', ''))
                parts.append(activity.get('description', ''))
                parts.append(activity.get('location', ''))
        return ' '.join(parts)
    
    def _get_search_terms(self, requirement) -> List[str]:
        """Extract searchable terms from a requirement (dict or Pydantic model)."""
        # Handle both dict and Pydantic Requirement objects
        if hasattr(requirement, 'value'):
            value = requirement.value
            category = requirement.category
        else:
            value = requirement.get('value', '')
            category = requirement.get('category', '')
        
        terms = [value, value.replace('_', ' ')]
        
        # Add category-specific aliases
        if category == 'cuisine':
            terms.extend([value.replace('cuisine:', ''), f"{value} cuisine", f"{value} food"])
        elif category == 'activity':
            terms.extend([value.replace('activity:', '')])
        elif category == 'comfort':
            if value == 'luxury' or value == 'premium':
                terms.extend(['premium', 'luxury', 'upscale', 'fancy'])
            elif value == 'budget':
                terms.extend(['budget', 'economical', 'affordable'])
        
        return terms
    
    # ===== MAIN VALIDATION =====
    
    def validate(self, days: List[Dict], requirements: Optional[List] = None) -> Dict:
        """
        Perform comprehensive itinerary validation.
        
        Returns validation result dictionary with structure, financial, semantic,
        and requirement checks.
        """
        if requirements:
            self.requirements = requirements
        
        self.errors = []
        self.warnings = []
        self.checks_passed = {}
        
        # Structural checks
        struct_valid = (
            self.check_day_count(days) and
            self.check_day_numbering(days) and
            self.check_day_titles(days) and
            self.check_activity_presence(days)
        )
        
        # Financial checks
        financial_valid = self.check_nonnegative_costs(days)
        
        # Semantic checks
        semantic_valid = (
            self.check_for_placeholders(days) and
            self.check_activity_variety(days) and
            self.check_activity_specificity(days) and
            self.check_activity_timing(days)
        )
        
        # Requirement checks
        req_met, req_total = self.check_requirement_coverage(days)
        
        # Overall validity
        is_valid = struct_valid and financial_valid and (not self.errors)
        
        # Calculate quality scores
        semantic_score = self._calculate_semantic_score()
        feasibility_score = self._calculate_feasibility_score()
        requirement_score = (req_met / req_total * 100) if req_total > 0 else 100.0
        
        return {
            'is_valid': is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'checks_passed': self.checks_passed,
            'requirements_met': req_met,
            'requirements_total': req_total,
            'semantic_score': semantic_score,
            'feasibility_score': feasibility_score,
            'requirement_score': requirement_score,
            'overall_score': (semantic_score + feasibility_score + requirement_score) / 3.0 if is_valid else 0.0,
        }
    
    def _calculate_semantic_score(self) -> float:
        """Score based on content quality and specificity."""
        score = 100.0
        if not self.checks_passed.get('placeholder_check', True):
            score -= 30
        if not self.checks_passed.get('activity_variety', True):
            score -= 20
        if not self.checks_passed.get('activity_specificity', True):
            score -= 15
        return max(0.0, score)
    
    def _calculate_feasibility_score(self) -> float:
        """Score based on structural and temporal validity."""
        score = 100.0
        if not self.checks_passed.get('day_count', True):
            score -= 20
        if not self.checks_passed.get('day_numbering', True):
            score -= 15
        if not self.checks_passed.get('activity_presence', True):
            score -= 20
        if not self.checks_passed.get('activity_timing', True):
            score -= 10
        return max(0.0, score)
