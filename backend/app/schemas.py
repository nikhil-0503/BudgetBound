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

    class Config:
        from_attributes = True

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

class DestinationOut(DestinationBase):
    id: int

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
class ExpenseCreate(BaseModel):
    date: str
    category: str
    amount: float
    notes: Optional[str] = None

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

    class Config:
        from_attributes = True

# Reverse Search response
class DestinationSearchScore(BaseModel):
    destination: DestinationOut
    estimated_cost: float
    budget_fit: float
    rating: float
    value_score: float

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
