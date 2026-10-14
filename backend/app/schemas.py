from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime
    photo_url: Optional[str] = None
    default_budget: Optional[float] = None
    preferred_travel_style: Optional[str] = None
    preferred_comfort_level: Optional[int] = None
    default_starting_city: Optional[str] = None
    preferred_theme: str = "light"
    is_admin: bool = False

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    photo_url: Optional[str] = None
    default_budget: Optional[float] = None
    preferred_travel_style: Optional[str] = None
    preferred_comfort_level: Optional[int] = None
    default_starting_city: Optional[str] = None
    preferred_theme: Optional[str] = None

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

class TokenData(BaseModel):
    email: Optional[str] = None

# Destination Schemas
class DestinationBase(BaseModel):
    name: str
    state: str
    avg_travel_cost: float
    avg_hotel_cost: float
    avg_food_cost: float
    avg_activity_cost: float
    rating: float
    category: str
    best_season: str
    description: str
    attractions: List[str]
    
    # Expanded fields
    budget_tier: Optional[str] = "Mid-range"
    recommended_duration: Optional[int] = 3
    comfort_level: Optional[int] = 50
    adventure_score: Optional[float] = 0.0
    nature_score: Optional[float] = 0.0
    family_score: Optional[float] = 0.0
    romantic_score: Optional[float] = 0.0
    religious_score: Optional[float] = 0.0
    beach_score: Optional[float] = 0.0
    city_score: Optional[float] = 0.0
    solo_score: Optional[float] = 0.0

class WeatherIntelligenceOut(BaseModel):
    current_season: str
    best_season: str
    season_rating: str
    crowd_level: str
    temperature_range: str
    rain_probability: str
    recommendation: str

class DestinationOut(DestinationBase):
    id: int
    weather_intelligence: Optional[WeatherIntelligenceOut] = None

    class Config:
        from_attributes = True

class DestinationListOut(BaseModel):
    total: int
    destinations: List[DestinationOut]

# Budget Allocation Schemas
class BudgetAllocationBase(BaseModel):
    transport_cost: float
    hotel_cost: float
    food_cost: float
    activities_cost: float
    emergency_reserve: float
    local_transport_cost: float
    taxes_fees_cost: float

class BudgetAllocationOut(BudgetAllocationBase):
    id: int
    trip_id: int

    class Config:
        from_attributes = True

# Itinerary Schemas
class ItineraryActivity(BaseModel):
    time: str
    title: str
    cost: float

class ItineraryBase(BaseModel):
    day_number: int
    activities: List[ItineraryActivity]
    description: Optional[str] = None

class ItineraryOut(ItineraryBase):
    id: int
    trip_id: int

    class Config:
        from_attributes = True

# Expense Schemas
class ExpenseBase(BaseModel):
    date: str
    category: str
    amount: float
    notes: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    trip_id: int

class ExpenseOut(ExpenseCreate):
    id: int
    trip_id: int

    class Config:
        from_attributes = True

# Trip Plan Request (from slider & planner)
class TripPlanRequest(BaseModel):
    starting_city: str
    budget: float
    days: int
    travel_type: str
    travelers_count: int = 1
    comfort_score: int = 50
    destination_id: Optional[int] = None

class PackingItemOut(BaseModel):
    id: int
    trip_id: int
    name: str
    checked: bool

    class Config:
        from_attributes = True

class CarbonFootprintOut(BaseModel):
    transport_mode: str
    co2_emissions: float
    carbon_rating: str
    eco_score: int
    alternative_savings: float

class NotificationOut(BaseModel):
    id: int
    user_id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TravelDocumentOut(BaseModel):
    id: int
    trip_id: int
    category: str
    filename: str
    filepath: str
    filesize: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

# Trip Output Schemas
class TripOut(BaseModel):
    id: int
    user_id: int
    destination_id: int
    budget: float
    days: int
    travelers_count: int
    travel_type: str
    comfort_score: int
    total_estimated_cost: float
    hotel_tier: str
    transport_mode: str
    created_at: datetime
    destination: DestinationOut
    itineraries: List[ItineraryOut] = []
    budget_allocation: Optional[BudgetAllocationOut] = None
    status: str = "Planned"
    start_date: Optional[str] = None
    actual_spending: Optional[float] = 0.0
    savings: Optional[float] = 0.0
    is_public: bool = False
    share_token: Optional[str] = None
    packing_items: List[PackingItemOut] = []
    carbon_footprint: Optional[CarbonFootprintOut] = None
    documents: List[TravelDocumentOut] = []

    class Config:
        from_attributes = True

class ScoreBreakdown(BaseModel):
    budget_compatibility: float
    trip_type_match: float
    comfort_match: float
    destination_rating: float
    duration_suitability: float
    explanations: List[str]

# Reverse Search response
class DestinationSearchScore(BaseModel):
    destination: DestinationOut
    estimated_cost: float
    budget_fit: float
    rating: float
    value_score: float
    breakdown: Optional[ScoreBreakdown] = None


# Optimizer Schemas
class OptimizationOption(BaseModel):
    action_key: str
    label: str
    cost_difference: float
    new_allocation: BudgetAllocationBase
    description: str

class OptimizationResponse(BaseModel):
    current_cost: float
    budget: float
    allocations: BudgetAllocationBase
    options: List[OptimizationOption]

# MultiStopTrip Schemas
class MultiStopTripBase(BaseModel):
    trip_name: str
    total_budget: float
    total_days: int
    destinations_str: str

class MultiStopTripCreate(MultiStopTripBase):
    raw_json: Any

class MultiStopTripOut(MultiStopTripBase):
    id: int
    user_id: int
    created_at: datetime
    raw_json: Any

    class Config:
        from_attributes = True


# ============================================================================
# PERSONALIZED PLANNER SCHEMAS
# ============================================================================

class Requirement(BaseModel):
    """Parsed user requirement (extracted from special/preferences field)"""
    key: str  # e.g., "cuisine:bengali", "activity:river_cruise", "comfort:luxury"
    value: str  # e.g., "bengali", "river_cruise", "luxury"
    category: str  # "cuisine", "activity", "comfort", "dietary", "travel_style"
    mandatory: bool = True
    coverage_status: Optional[str] = None  # "covered", "partial", "not_covered"


class PersonalizedPlanActivity(BaseModel):
    """An activity within a day"""
    time: str  # "Morning", "Afternoon", "Evening"
    start_time: Optional[str] = None  # "08:00 AM" format
    title: str  # Specific activity title (not generic)
    description: str  # 1-2 sentence description
    cost: float = 0.0  # Non-negative INR amount
    duration: Optional[str] = None  # "2-3 hours"
    location: Optional[str] = None  # Specific neighborhood/landmark
    category: Optional[str] = None  # "transport", "food", "activity", "accommodation"
    fulfills_requirements: Optional[List[str]] = []  # Which requirements this activity fulfills


class PersonalizedPlanDay(BaseModel):
    """A single day in the itinerary"""
    day_number: int  # 1, 2, 3, ...
    title: str  # Unique, descriptive day title (not generic)
    description: str  # 1-2 sentence day overview
    activities: List[PersonalizedPlanActivity]
    total_cost: float = 0.0  # Sum of all activity costs
    
    class Config:
        json_schema_extra = {
            "example": {
                "day_number": 1,
                "title": "Day 1 - Arrival & South Kolkata Heritage",
                "description": "Arrive in Kolkata, check in to your hotel, and explore the South Kolkata heritage district including Victoria Memorial.",
                "activities": [],
                "total_cost": 3600.0
            }
        }


class BudgetBreakdown(BaseModel):
    """Itemized budget allocation"""
    accommodation_per_night: float
    food_per_day: float
    activities_per_day: float
    transport: float
    contingency: float
    
    def total(self) -> float:
        """Calculate total"""
        return self.accommodation_per_night * 3 + self.food_per_day * 3 + self.activities_per_day * 3 + self.transport + self.contingency


class PersonalizedPlanRequest(BaseModel):
    """Request to generate a personalized itinerary"""
    keywords: str = Field(..., min_length=1, max_length=100, description="Destination name or keywords")
    budget: float = Field(..., gt=0, le=1000000, description="Maximum budget in INR")
    days: int = Field(..., ge=1, le=60, description="Number of days for the trip")
    special: Optional[str] = Field(None, max_length=500, description="User preferences and special requirements")
    
    class Config:
        json_schema_extra = {
            "example": {
                "keywords": "Kolkata",
                "budget": 25000.0,
                "days": 2,
                "special": "Bengali food, river cruise, budget travel"
            }
        }


class PersonalizedPlanResponse(BaseModel):
    """Generated personalized itinerary response - enforces canonical schema for Groq structured outputs."""
    plan_name: str
    destination: str
    num_days: int
    estimated_total_cost: float
    budget_limit: float
    summary: str
    budget_breakdown: BudgetBreakdown
    days: List[PersonalizedPlanDay]
    remaining_budget: float
    
    # Requirement tracking
    requirements_extracted: List[Requirement] = []
    requirements_coverage: Optional[dict] = None  # {"requirement_key": "covered"|"partial"|"not_covered"}
    
    # Data quality & validation
    validation_warnings: List[str] = []
    data_source: str = "llm"  # "llm" or "fallback"
    generation_timestamp: Optional[datetime] = None
    
    # Quality scores (set after validation)
    semantic_score: float = 0.0  # 0-100, based on destination relevance
    feasibility_score: float = 0.0  # 0-100, based on schedule coherence
    requirement_coverage_score: float = 0.0  # 0-100
    
    @staticmethod
    def json_schema_for_groq() -> dict:
        """
        Returns JSON schema for Groq structured outputs (response_format.type = "json_schema").
        Enforces canonical structure with additionalProperties: false for strict validation.
        """
        return {
            "type": "object",
            "properties": {
                "plan_name": {"type": "string", "description": "Name of the customized travel plan"},
                "destination": {"type": "string", "description": "Primary destination name"},
                "num_days": {"type": "integer", "minimum": 1, "description": "Number of days in the plan"},
                "estimated_total_cost": {"type": "number", "minimum": 0, "description": "Total estimated cost in destination currency"},
                "budget_limit": {"type": "number", "minimum": 0, "description": "User's budget limit"},
                "summary": {"type": "string", "description": "Brief summary of the personalized plan"},
                "budget_breakdown": {
                    "type": "object",
                    "properties": {
                        "accommodation_per_night": {"type": "number", "minimum": 0},
                        "food_per_day": {"type": "number", "minimum": 0},
                        "activities_per_day": {"type": "number", "minimum": 0},
                        "transport": {"type": "number", "minimum": 0},
                        "contingency": {"type": "number", "minimum": 0}
                    },
                    "required": ["accommodation_per_night", "food_per_day", "activities_per_day", "transport", "contingency"],
                    "additionalProperties": False
                },
                "days": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day_number": {"type": "integer", "minimum": 1},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "activities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "time": {"type": "string", "enum": ["Morning", "Afternoon", "Evening"]},
                                        "start_time": {"type": ["string", "null"]},
                                        "title": {"type": "string"},
                                        "description": {"type": "string"},
                                        "cost": {"type": "number", "minimum": 0},
                                        "duration": {"type": ["string", "null"]},
                                        "location": {"type": ["string", "null"]},
                                        "category": {"type": ["string", "null"]},
                                        "fulfills_requirements": {"type": "array", "items": {"type": "string"}}
                                    },
                                    "required": ["time", "title", "description", "cost", "start_time", "duration", "location", "category", "fulfills_requirements"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["day_number", "title", "description", "activities"],
                        "additionalProperties": False
                    }
                },
                "remaining_budget": {"type": "number", "minimum": 0, "description": "Budget remaining after plan"}
            },
            "required": [
                "plan_name", "destination", "num_days", "estimated_total_cost",
                "budget_limit", "summary", "budget_breakdown", "days", "remaining_budget"
            ],
            "additionalProperties": False
        }
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan_name": "Customized 2-day trip to Kolkata for food lovers",
                "destination": "Kolkata",
                "num_days": 2,
                "estimated_total_cost": 24000.0,
                "budget_limit": 25000.0,
                "summary": "A culturally rich 2-day exploration of Kolkata focusing on Bengali cuisine and riverside experiences.",
                "budget_breakdown": {
                    "accommodation_per_night": 7500.0,
                    "food_per_day": 4000.0,
                    "activities_per_day": 2000.0,
                    "transport": 2000.0,
                    "contingency": 1500.0
                },
                "days": [],
                "remaining_budget": 1000.0,
                "requirements_extracted": [],
                "requirements_coverage": {},
                "validation_warnings": [],
                "data_source": "llm",
                "semantic_score": 85.0,
                "feasibility_score": 100.0,
                "requirement_coverage_score": 100.0
            }
        }


class PersonalizedPlanValidationResult(BaseModel):
    """Result of validating a generated personalized plan"""
    is_valid: bool
    score: float  # 0-100
    errors: List[str] = []  # Critical issues that prevent validity
    warnings: List[str] = []  # Non-critical issues
    checks_passed: dict = {}  # {"day_count": True, "budget_ok": True, ...}
    
    # Requirement coverage
    requirements_met: int = 0
    requirements_total: int = 0
    
    # Semantic quality
    semantic_score: float = 0.0  # 0-100, based on destination relevance
    feasibility_score: float = 0.0  # 0-100, based on schedule coherence
    requirement_coverage_score: float = 0.0  # 0-100


# ========== EXPLAINABILITY SCHEMAS ==========

class CostExplanation(BaseModel):
    """Explanation for a single cost category"""
    category: str  # "Accommodation", "Transport", "Food", etc.
    selected_option: str  # e.g., "Flight", "Mid-Range Hotel"
    selected_cost: float
    estimated_cost: float
    allocation_percentage: float
    
    # Decision factors that influenced this choice
    decision_factors: List[str]  # e.g., ["Comfort score: 75/100", "Trip duration: 5 days"]
    
    # Alternatives with cost differences (if available)
    alternatives: Optional[List[dict]] = None  # [{"option": "Train", "cost": 5000, "savings": 3000}, ...]
    
    # Natural language explanation
    explanation: str

class FinancialSummary(BaseModel):
    """Overall financial breakdown"""
    total_budget: float
    total_estimated_cost: float
    remaining_budget: float
    contingency_included: bool
    contingency_amount: float
    contingency_percentage: float

class TripMetadata(BaseModel):
    """Metadata about the trip to ground explanations"""
    destination_name: str
    destination_state: str
    trip_duration_days: int
    traveler_count: int
    comfort_score: int
    travel_type: str
    starting_city: Optional[str] = None
    destination_category: str

class ExplainabilityResponse(BaseModel):
    """Structured response for trip explainability analysis"""
    trip_id: int
    trip_metadata: TripMetadata
    financial_summary: FinancialSummary
    
    # Detailed cost explanations by category
    cost_explanations: List[CostExplanation]
    
    # AI-generated summary and insights (grounded in facts)
    ai_summary: Optional[str] = None
    
    # Recommendations with quantified savings
    recommendations: List[dict] = []  # [{"action": "...", "savings": 5000, "trade_offs": [...]}]
    
    # Data quality indicators
    has_alternative_prices: bool  # Whether alternative cost estimates are available
    missing_decision_data: List[str] = []  # Fields that couldn't be determined
    data_source: str  # "calculated" or "fallback"
