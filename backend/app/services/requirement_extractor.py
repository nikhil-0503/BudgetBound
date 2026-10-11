"""
Requirement extractor for personalized travel planning.

Converts unstructured user input (special/preferences field) into structured requirements.
"""

from typing import List, Dict, Tuple
import re
from app.schemas import Requirement


class RequirementExtractor:
    """
    Extracts and parses user requirements from free-form text.
    
    Maps user input to structured requirements and provides activity templates
    that satisfy those requirements.
    """
    
    # Mapping of keywords to structured requirement keys
    CUISINE_KEYWORDS = {
        "bengali": "cuisine:bengali",
        "south indian": "cuisine:south_indian",
        "north indian": "cuisine:north_indian",
        "chinese": "cuisine:chinese",
        "continental": "cuisine:continental",
        "seafood": "cuisine:seafood",
        "vegetarian": "cuisine:vegetarian",
        "vegan": "cuisine:vegan",
        "thai": "cuisine:thai",
        "mexican": "cuisine:mexican",
        "italian": "cuisine:italian",
        "japanese": "cuisine:japanese",
        "non-vegetarian": "cuisine:non_vegetarian",
        "meat": "cuisine:meat",
    }
    
    COMFORT_KEYWORDS = {
        "luxury": "comfort:luxury",
        "premium": "comfort:premium",
        "fancy": "comfort:luxury",
        "upscale": "comfort:premium",
        "deluxe": "comfort:luxury",
        "budget": "comfort:budget",
        "budget travel": "comfort:budget",
        "backpacker": "comfort:budget",
        "mid-range": "comfort:mid_range",
        "comfortable": "comfort:mid_range",
    }
    
    ACTIVITY_KEYWORDS = {
        "river cruise": "activity:river_cruise",
        "water sports": "activity:water_sports",
        "trekking": "activity:trekking",
        "hiking": "activity:hiking",
        "adventure": "activity:adventure",
        "beach": "activity:beach",
        "heritage": "activity:heritage",
        "museums": "activity:museums",
        "shopping": "activity:shopping",
        "nightlife": "activity:nightlife",
        "spa": "activity:spa",
        "yoga": "activity:yoga",
        "meditation": "activity:meditation",
        "cooking class": "activity:cooking_class",
        "cultural": "activity:cultural",
    }
    
    TRAVEL_STYLE_KEYWORDS = {
        "delicious food": "travel_style:food_lover",
        "food lover": "travel_style:food_lover",
        "culinary": "travel_style:food_lover",
        "fancy travel": "travel_style:luxury_travel",
        "adventure travel": "travel_style:adventure",
        "cultural tour": "travel_style:cultural",
        "solo travel": "travel_style:solo",
        "family": "travel_style:family",
        "couple": "travel_style:romantic",
        "romantic": "travel_style:romantic",
        "group travel": "travel_style:group",
    }
    
    OTHER_KEYWORDS = {
        "slow travel": "pace:slow",
        "fast-paced": "pace:fast",
        "off-season": "timing:off_season",
        "peak season": "timing:peak_season",
    }
    
    def __init__(self):
        """Initialize extractor with all keyword mappings."""
        self.all_keywords = {
            **self.CUISINE_KEYWORDS,
            **self.COMFORT_KEYWORDS,
            **self.ACTIVITY_KEYWORDS,
            **self.TRAVEL_STYLE_KEYWORDS,
            **self.OTHER_KEYWORDS,
        }
    
    def extract(self, text: str) -> List[Requirement]:
        """
        Extract structured requirements from user input text.
        
        Args:
            text: User's free-form preference/special requirements text
            
        Returns:
            List of Requirement objects
        """
        if not text or not text.strip():
            return []
        
        requirements: List[Requirement] = []
        text_lower = text.lower().strip()
        
        # Track which phrases we've matched to avoid duplicates
        matched_phrases: Dict[str, bool] = {}
        
        # Check each keyword phrase (longest first to avoid partial matches)
        for phrase in sorted(self.all_keywords.keys(), key=len, reverse=True):
            if phrase in text_lower and phrase not in matched_phrases:
                # Extract the requirement key
                req_key = self.all_keywords[phrase]
                category, value = req_key.split(":", 1)
                
                # Determine if this is a mandatory or optional requirement
                # Heuristic: if user explicitly says "please", "must", "need", it's mandatory
                mandatory = self._is_mandatory(text_lower, phrase)
                
                # Check if this requirement is already in the list (avoid duplicates within same category)
                existing = next((r for r in requirements if r.category == category), None)
                if not existing:
                    requirements.append(Requirement(
                        key=req_key,
                        value=value,
                        category=category,
                        mandatory=mandatory,
                        coverage_status=None
                    ))
                
                matched_phrases[phrase] = True
        
        return requirements
    
    def get_activity_hints(self, requirements: List[Requirement]) -> Dict[str, List[str]]:
        """
        Generate activity suggestions based on extracted requirements.
        
        Returns: {
            "cuisine": ["Bengali restaurant", "Fish curry", ...],
            "activity": ["River cruise", "Heritage tour", ...],
            "comfort": ["Luxury hotel", "Premium transport", ...],
            ...
        }
        """
        hints: Dict[str, List[str]] = {}
        
        for req in requirements:
            category = req.category
            value = req.value
            
            if category not in hints:
                hints[category] = []
            
            # Map requirements to specific activity suggestions
            if category == 'cuisine':
                suggestions = self._get_cuisine_activities(value)
            elif category == 'activity':
                suggestions = self._get_activity_suggestions(value)
            elif category == 'comfort':
                suggestions = self._get_comfort_activities(value)
            elif category == 'travel_style':
                suggestions = self._get_travel_style_activities(value)
            else:
                suggestions = []
            
            hints[category].extend(suggestions)
        
        return hints
    
    def _get_cuisine_activities(self, cuisine: str) -> List[str]:
        """Generate dining/activity suggestions for a cuisine."""
        cuisine_map = {
            'bengali': ['Breakfast with luchi-alur dom', 'Fish curry tasting', 'Bengali sweets workshop', 'River fish market visit'],
            'seafood': ['Seafood restaurant visit', 'Fish market tour', 'Coastal fishing community', 'Seafood cooking class'],
            'vegetarian': ['Vegetarian restaurant', 'Temple food experience', 'Organic market visit', 'Vegetarian cooking class'],
            'north_indian': ['North Indian restaurant', 'Street food tour', 'Food market exploration'],
            'south_indian': ['South Indian restaurant', 'Spice market visit', 'Dosa tasting'],
        }
        return cuisine_map.get(cuisine, [f'{cuisine.replace("_", " ").title()} dining experience'])
    
    def _get_activity_suggestions(self, activity: str) -> List[str]:
        """Generate activity suggestions."""
        activity_map = {
            'river_cruise': ['Sunset river cruise', 'Morning river tour', 'Boat ride with breakfast'],
            'trekking': ['Day trek', 'Guided mountain hike', 'Peak sunrise trek'],
            'beach': ['Beach time', 'Beach walk', 'Beach sunset activity'],
            'heritage': ['Heritage walk', 'Historical site visit', 'Architecture tour'],
            'shopping': ['Local market exploration', 'Artisan shopping', 'Street shopping'],
        }
        return activity_map.get(activity, [f'{activity.replace("_", " ").title()} experience'])
    
    def _get_comfort_activities(self, comfort: str) -> List[str]:
        """Generate comfort level activity suggestions."""
        comfort_map = {
            'luxury': ['5-star dining', 'Spa and wellness', 'Premium hotel stay'],
            'budget': ['Street food experience', 'Budget-friendly restaurants', 'Local transit'],
            'mid_range': ['Mid-range dining', 'Comfortable hotel', 'Organized tours'],
        }
        return comfort_map.get(comfort, [])
    
    def _get_travel_style_activities(self, style: str) -> List[str]:
        """Generate travel style activity suggestions."""
        style_map = {
            'food_lover': ['Food market tour', 'Restaurant hopping', 'Street food tasting', 'Cooking class'],
            'adventure': ['Outdoor activities', 'Trekking', 'Water sports', 'Adventure tour'],
            'cultural': ['Museum visits', 'Temple tours', 'Cultural performances', 'Local community visits'],
            'luxury_travel': ['Premium accommodations', 'Fine dining', 'Private transport'],
            'family': ['Family-friendly attractions', 'Parks', 'Educational activities'],
        }
        return style_map.get(style, [])
    
    
    def _is_mandatory(self, text: str, phrase: str) -> bool:
        """
        Determine if a requirement is mandatory based on context.
        
        Args:
            text: The full text (lowercase)
            phrase: The requirement phrase that was matched
            
        Returns:
            True if requirement appears mandatory, False if optional
        """
        # Find the phrase in the text
        idx = text.find(phrase)
        if idx < 0:
            return True  # Default to mandatory
        
        # Look at surrounding context (50 chars before and after)
        context_start = max(0, idx - 50)
        context = text[context_start:idx + len(phrase) + 50]
        
        # Mandatory indicators
        mandatory_words = ["must", "need", "require", "essential", "important", "cannot miss"]
        for word in mandatory_words:
            if word in context:
                return True
        
        # Optional indicators
        optional_words = ["prefer", "like", "enjoy", "interested", "would like", "possibly"]
        for word in optional_words:
            if word in context:
                return False
        
        # Default to mandatory for explicit requirements
        return True
    
    def format_for_prompt(self, requirements: List[Requirement]) -> str:
        """
        Format extracted requirements for inclusion in LLM prompt.
        
        Args:
            requirements: List of extracted requirements
            
        Returns:
            Formatted requirement string for prompt
        """
        if not requirements:
            return "No specific requirements"
        
        mandatory = [r for r in requirements if r.mandatory]
        optional = [r for r in requirements if not r.mandatory]
        
        lines = []
        if mandatory:
            lines.append("MANDATORY REQUIREMENTS (must be included):")
            for req in mandatory:
                lines.append(f"  - {req.category.upper()}: {req.value.replace('_', ' ')}")
        
        if optional:
            lines.append("OPTIONAL PREFERENCES (include if feasible):")
            for req in optional:
                lines.append(f"  - {req.category.upper()}: {req.value.replace('_', ' ')}")
        
        return "\n".join(lines)


def extract_requirements(text: str) -> List[Requirement]:
    """Convenience function to extract requirements from text."""
    extractor = RequirementExtractor()
    return extractor.extract(text)


def format_requirements_for_prompt(text: str) -> str:
    """Convenience function to format requirements for prompt."""
    extractor = RequirementExtractor()
    requirements = extractor.extract(text)
    return extractor.format_for_prompt(requirements)
