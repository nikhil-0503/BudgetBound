import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Profile & Preferences
    photo_url = Column(String, nullable=True)
    default_budget = Column(Float, nullable=True)
    preferred_travel_style = Column(String, nullable=True)
    preferred_comfort_level = Column(Integer, nullable=True)
    default_starting_city = Column(String, nullable=True)
    preferred_theme = Column(String, default="light", nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Relationships
    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    multistop_trips = relationship("MultiStopTrip", back_populates="user", cascade="all, delete-orphan")

class Destination(Base):
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    state = Column(String, nullable=False)
    avg_travel_cost = Column(Float, nullable=False)  # travel cost per person (base flight/train)
    avg_hotel_cost = Column(Float, nullable=False)   # mid-tier hotel cost per night
    avg_food_cost = Column(Float, nullable=False)    # food cost per day per person
    avg_activity_cost = Column(Float, nullable=False) # cost per activity
    rating = Column(Float, default=4.0)
    category = Column(String, nullable=False)        # Nature, Adventure, Family, etc.
    best_season = Column(String, nullable=False)
    description = Column(String, nullable=False)
    attractions = Column(JSON, nullable=False)        # list of strings (sample attractions)

    # Expanded metadata
    budget_tier = Column(String, nullable=True)        # Budget, Mid-range, Premium
    recommended_duration = Column(Integer, nullable=True)
    comfort_level = Column(Integer, nullable=True)     # 0 to 100
    adventure_score = Column(Float, default=0.0)
    nature_score = Column(Float, default=0.0)
    family_score = Column(Float, default=0.0)
    romantic_score = Column(Float, default=0.0)
    religious_score = Column(Float, default=0.0)
    beach_score = Column(Float, default=0.0)
    city_score = Column(Float, default=0.0)
    solo_score = Column(Float, default=0.0)

    # Relationships
    trips = relationship("Trip", back_populates="destination")

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=False)
    budget = Column(Float, nullable=False)
    days = Column(Integer, nullable=False)
    travelers_count = Column(Integer, default=1)
    travel_type = Column(String, nullable=False)     # category
    comfort_score = Column(Integer, default=50)      # 0 to 100
    total_estimated_cost = Column(Float, nullable=False)
    hotel_tier = Column(String, nullable=False)      # Budget, Mid, Luxury
    transport_mode = Column(String, nullable=False)  # Train, Flight
    status = Column(String, default="Planned", nullable=False)
    start_date = Column(String, nullable=True)       # YYYY-MM-DD
    is_public = Column(Boolean, default=False, nullable=False)
    share_token = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="trips")
    destination = relationship("Destination", back_populates="trips")
    itineraries = relationship("Itinerary", back_populates="trip", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="trip", cascade="all, delete-orphan")
    budget_allocation = relationship("BudgetAllocation", uselist=False, back_populates="trip", cascade="all, delete-orphan")
    packing_items = relationship("PackingItem", back_populates="trip", cascade="all, delete-orphan")
    documents = relationship("TravelDocument", back_populates="trip", cascade="all, delete-orphan")

class Itinerary(Base):
    __tablename__ = "itineraries"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    day_number = Column(Integer, nullable=False)
    activities = Column(JSON, nullable=False)        # list of objects: [{"time": "Morning", "title": "...", "cost": 0}]
    description = Column(String, nullable=True)

    # Relationships
    trip = relationship("Trip", back_populates="itineraries")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    date = Column(String, nullable=False)             # YYYY-MM-DD
    category = Column(String, nullable=False)        # Transport, Hotel, Food, Activities, Shopping, Other
    amount = Column(Float, nullable=False)
    notes = Column(String, nullable=True)

    # Relationships
    trip = relationship("Trip", back_populates="expenses")

class BudgetAllocation(Base):
    __tablename__ = "budget_allocations"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    transport_cost = Column(Float, nullable=False)
    hotel_cost = Column(Float, nullable=False)
    food_cost = Column(Float, nullable=False)
    activities_cost = Column(Float, nullable=False)
    emergency_reserve = Column(Float, nullable=False)
    local_transport_cost = Column(Float, nullable=False)
    taxes_fees_cost = Column(Float, nullable=False)

    # Relationships
    trip = relationship("Trip", back_populates="budget_allocation")

class PackingItem(Base):
    __tablename__ = "packing_items"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    checked = Column(Boolean, default=False, nullable=False)

    # Relationships
    trip = relationship("Trip", back_populates="packing_items")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")

class TravelDocument(Base):
    __tablename__ = "travel_documents"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    filesize = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    trip = relationship("Trip", back_populates="documents")

class MultiStopTrip(Base):
    __tablename__ = "multistop_trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trip_name = Column(String, nullable=False)
    total_budget = Column(Float, nullable=False)
    total_days = Column(Integer, nullable=False)
    destinations_str = Column(String, nullable=False) # e.g. "Delhi -> Agra"
    raw_json = Column(JSON, nullable=False)           # Stores the exact complex schema from AI
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="multistop_trips")
