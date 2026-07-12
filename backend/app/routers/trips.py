import io
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status, Query
# pyrefly: ignore [missing-import]
from fastapi.responses import StreamingResponse
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from typing import List, Optional
import datetime

from app import models, schemas, auth
from app.database import get_db
from app.services.gemini import gemini_service

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

router = APIRouter(prefix="/api/trips", tags=["Trips"])

def get_region(text: str) -> str:
    t = text.lower().strip()
    
    north = ["delhi", "gurgaon", "noida", "chandigarh", "amritsar", "srinagar", "jaipur", "dehradun", "lucknow", "punjab", "haryana", "uttarakhand", "himachal", "jammu", "kashmir", "uttar pradesh", "rajasthan", "ladakh", "shimla", "manali", "rishikesh", "auli", "spiti", "kedarnath", "haridwar", "nainital"]
    south = ["bangalore", "bengaluru", "chennai", "hyderabad", "kochi", "madurai", "tirupati", "coimbatore", "karnataka", "kerala", "tamil nadu", "andhra", "telangana", "pondicherry", "munnar", "coorg", "ooty", "wayanad", "alleppey", "kodaikanal", "araku", "kovalam", "varkala", "rameshwaram"]
    west = ["mumbai", "pune", "ahmedabad", "goa", "alibaug", "maharashtra", "gujarat", "daman", "shirdi", "gokarna", "mount abu"]
    east = ["kolkata", "darjeeling", "puri", "bhubaneswar", "guwahati", "west bengal", "odisha", "sikkim", "arunachal", "andaman", "nicobar", "tawang", "yumthang", "havelock"]
    
    for item in north:
        if item in t:
            return "North"
    for item in south:
        if item in t:
            return "South"
    for item in west:
        if item in t:
            return "West"
    for item in east:
        if item in t:
            return "East"
            
    return "Unknown"

def calculate_costs(dest: models.Destination, days: int, travelers: int, comfort_score: int, starting_city: str = ""):
    # 1. Transport Mode & Cost (influenced by starting city region)
    start_region = get_region(starting_city)
    dest_region = get_region(dest.state)
    
    multiplier = 1.0
    if start_region != "Unknown" and dest_region != "Unknown":
        if start_region == dest_region:
            multiplier = 0.45  # regional travel discount
        elif (start_region == "North" and dest_region == "South") or (start_region == "South" and dest_region == "North") or \
             (start_region == "East" and dest_region == "West") or (start_region == "West" and dest_region == "East"):
            multiplier = 1.45  # long range surcharge
        else:
            multiplier = 1.0   # adjacent region standard rate

    if comfort_score < 50:
        transport_mode = "Train"
        transport_cost = max(1000.0, dest.avg_travel_cost * 0.45) * travelers * multiplier
    else:
        transport_mode = "Flight"
        transport_cost = max(4000.0, dest.avg_travel_cost * 1.25) * travelers * multiplier

    # 2. Hotel Tier & Cost
    if comfort_score < 30:
        hotel_tier = "Budget"
        hotel_cost_per_night = dest.avg_hotel_cost * 0.65
    elif comfort_score <= 70:
        hotel_tier = "Mid-Range"
        hotel_cost_per_night = dest.avg_hotel_cost * 1.0
    else:
        hotel_tier = "Luxury"
        hotel_cost_per_night = dest.avg_hotel_cost * 1.85
        
    hotel_cost = hotel_cost_per_night * days

    # 3. Food Cost
    food_factor = 0.7 + (comfort_score / 150.0)
    food_cost = dest.avg_food_cost * days * travelers * food_factor

    # 4. Activities Cost
    activities_per_day = 1 if comfort_score < 30 else (2 if comfort_score <= 70 else 3)
    activity_factor = 0.8 + (comfort_score / 200.0)
    activities_cost = dest.avg_activity_cost * travelers * (days - 1) * activities_per_day * activity_factor

    # 5. Local Transport Cost
    local_transport_cost = 400.0 * days * travelers * (0.8 + comfort_score / 150.0)

    # 6. Taxes & Fees (12% of subtotal parts)
    taxes_fees_cost = (transport_cost + hotel_cost + activities_cost) * 0.12

    # Subtotal
    subtotal = transport_cost + hotel_cost + food_cost + activities_cost + local_transport_cost + taxes_fees_cost

    # Emergency Reserve (8% of subtotal)
    emergency_reserve = subtotal * 0.08

    total_cost = subtotal + emergency_reserve

    return {
        "transport_mode": transport_mode,
        "hotel_tier": hotel_tier,
        "transport_cost": round(transport_cost, 2),
        "hotel_cost": round(hotel_cost, 2),
        "food_cost": round(food_cost, 2),
        "activities_cost": round(activities_cost, 2),
        "local_transport_cost": round(local_transport_cost, 2),
        "taxes_fees_cost": round(taxes_fees_cost, 2),
        "emergency_reserve": round(emergency_reserve, 2),
        "total_estimated_cost": round(total_cost, 2),
    }

def calculate_weighted_score(
    dest: models.Destination,
    costs: dict,
    budget: float,
    days: int,
    travel_type: str,
    comfort_score: int
) -> float:
    # 1. Budget Fit (40%)
    total_cost = costs["total_estimated_cost"]
    diff = abs(budget - total_cost) / budget
    if total_cost <= budget:
        budget_fit = 1.0 - diff  # closer to budget limit is higher utility
    else:
        budget_fit = max(0.0, 1.0 - diff * 4.0)  # penalize heavily if exceeding budget
        
    # 2. Category Match (25%)
    main_match = 1.0 if dest.category.lower() == travel_type.lower() else 0.0
    sub_score = 0.0
    t_type = travel_type.lower()
    if "nature" in t_type:
        sub_score = getattr(dest, "nature_score", 0.0) or 0.0
    elif "adventure" in t_type:
        sub_score = getattr(dest, "adventure_score", 0.0) or 0.0
    elif "family" in t_type:
        sub_score = getattr(dest, "family_score", 0.0) or 0.0
    elif "romantic" in t_type:
        sub_score = getattr(dest, "romantic_score", 0.0) or 0.0
    elif "religious" in t_type:
        sub_score = getattr(dest, "religious_score", 0.0) or 0.0
    elif "beach" in t_type:
        sub_score = getattr(dest, "beach_score", 0.0) or 0.0
    elif "city" in t_type:
        sub_score = getattr(dest, "city_score", 0.0) or 0.0
    elif "solo" in t_type:
        sub_score = getattr(dest, "solo_score", 0.0) or 0.0
        
    cat_match = 0.6 * main_match + 0.4 * (sub_score / 100.0)
    
    # 3. Rating Match (15%)
    rating_match = (dest.rating or 4.0) / 5.0
    
    # 4. Comfort Match (10%)
    comfort_match = 1.0 - abs(comfort_score - (dest.comfort_level or 50)) / 100.0
    
    # 5. Duration Suitability (10%)
    rec_dur = dest.recommended_duration or 4
    duration_suitability = max(0.0, 1.0 - abs(days - rec_dur) / 5.0)
    
    # Combined score
    weighted_score = (
        0.40 * budget_fit +
        0.25 * cat_match +
        0.15 * rating_match +
        0.10 * comfort_match +
        0.10 * duration_suitability
    ) * 100.0
    
    return round(weighted_score, 2)

def generate_itinerary_days(dest: models.Destination, days: int, comfort_score: int, travel_type: str = ""):
    # --- Try Gemini first ---
    attractions = dest.attractions if isinstance(dest.attractions, list) else []
    if not attractions:
        attractions = ["Local Market", "Town Square", "Scenic Viewpoint", "Historical Museum"]

    ai_result = gemini_service.generate_itinerary(
        destination_name=dest.name,
        state=dest.state,
        category=dest.category,
        attractions=attractions,
        travel_type=travel_type or dest.category,
        days=days,
        comfort_score=comfort_score,
        avg_food_cost=dest.avg_food_cost,
        avg_activity_cost=dest.avg_activity_cost,
    )
    if ai_result is not None:
        return ai_result

    # --- Template fallback (original logic) ---
    itineraries = []
    attr_count = len(attractions)

    for day in range(1, days + 1):
        day_activities = []
        if day == 1:
            day_activities.append({
                "time": "Morning",
                "title": "Arrival & Hotel Check-in",
                "cost": 0.0
            })
            day_activities.append({
                "time": "Afternoon",
                "title": f"Explore surrounding area & lunch in {dest.name}",
                "cost": round(dest.avg_food_cost * 0.4, 2)
            })
            day_activities.append({
                "time": "Evening",
                "title": f"Stroll at {attractions[0 % attr_count]}",
                "cost": 0.0
            })
            description = "Welcome to your destination. Check in, unpack, and enjoy a light orientation walk."
        elif day == days:
            day_activities.append({
                "time": "Morning",
                "title": "Souvenir Shopping at local bazaars",
                "cost": round(dest.avg_activity_cost * 0.5, 2)
            })
            day_activities.append({
                "time": "Afternoon",
                "title": "Hotel Check-out & Lunch",
                "cost": round(dest.avg_food_cost * 0.4, 2)
            })
            day_activities.append({
                "time": "Evening",
                "title": "Departure back home",
                "cost": 0.0
            })
            description = "Last day of trip. Pick up local souvenirs, pack your bags, check out, and head home."
        else:
            activities_per_day = 1 if comfort_score < 30 else (2 if comfort_score <= 70 else 3)
            times = ["Morning", "Afternoon", "Evening"]
            idx_offset = (day - 2) * 2

            for i in range(activities_per_day):
                time_slot = times[i % 3]
                attr_name = attractions[(idx_offset + i) % attr_count]
                day_activities.append({
                    "time": time_slot,
                    "title": f"Sightseeing at {attr_name}",
                    "cost": round(dest.avg_activity_cost * 0.8, 2)
                })

            description = f"Full day of adventure and sightseeing in {dest.name}. Experiencing major attractions."

        itineraries.append({
            "day_number": day,
            "activities": day_activities,
            "description": description
        })
    return itineraries

@router.post("/plan")
def generate_trip_plan(req: schemas.TripPlanRequest, db: Session = Depends(get_db)):
    # Fetch either the selected destination or the full catalog to rank dynamically
    query = db.query(models.Destination)
    if req.destination_id is not None:
        query = query.filter(models.Destination.id == req.destination_id)

    destinations = query.all()
    if not destinations:
        if req.destination_id is not None:
            raise HTTPException(status_code=404, detail="Selected destination not found in database.")
        raise HTTPException(status_code=404, detail="No destinations found in database. Seed database first.")

    matched_plans = []
    for dest in destinations:
        costs = calculate_costs(dest, req.days, req.travelers_count, req.comfort_score, req.starting_city)
        score = calculate_weighted_score(dest, costs, req.budget, req.days, req.travel_type, req.comfort_score)
        
        matched_plans.append({
            "destination": dest,
            "costs": costs,
            "value_score": score,
            "savings": round(req.budget - costs["total_estimated_cost"], 2),
            "under_budget": costs["total_estimated_cost"] <= req.budget
        })

    # Sort only when we are evaluating the full catalog
    if req.destination_id is None:
        matched_plans.sort(key=lambda x: x["value_score"], reverse=True)

    selected_plan = matched_plans[0]

    # Generate daily itinerary
    dest = selected_plan["destination"]
    itineraries = generate_itinerary_days(dest, req.days, req.comfort_score, req.travel_type)

    return {
        "destination": dest,
        "costs": selected_plan["costs"],
        "savings": selected_plan["savings"],
        "value_score": selected_plan["value_score"],
        "under_budget": selected_plan["under_budget"],
        "itineraries": itineraries,
        "budget": req.budget,
        "days": req.days,
        "travelers_count": req.travelers_count,
        "comfort_score": req.comfort_score,
        "travel_type": req.travel_type
    }

@router.post("/", response_model=schemas.TripOut)
def save_trip(
    trip_data: dict, # Accepts raw dict representing output of /plan
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Extract destination_id
    dest_id = trip_data["destination"]["id"]
    costs = trip_data["costs"]

    # Create Trip
    db_trip = models.Trip(
        user_id=current_user.id,
        destination_id=dest_id,
        budget=trip_data["budget"],
        days=trip_data["days"],
        travelers_count=trip_data["travelers_count"],
        travel_type=trip_data["travel_type"],
        comfort_score=trip_data["comfort_score"],
        total_estimated_cost=costs["total_estimated_cost"],
        hotel_tier=costs["hotel_tier"],
        transport_mode=costs["transport_mode"]
    )
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)

    # Save Budget Allocation
    db_allocation = models.BudgetAllocation(
        trip_id=db_trip.id,
        transport_cost=costs["transport_cost"],
        hotel_cost=costs["hotel_cost"],
        food_cost=costs["food_cost"],
        activities_cost=costs["activities_cost"],
        local_transport_cost=costs["local_transport_cost"],
        taxes_fees_cost=costs["taxes_fees_cost"],
        emergency_reserve=costs["emergency_reserve"]
    )
    db.add(db_allocation)

    # Save Itinerary days
    for it_day in trip_data["itineraries"]:
        db_itinerary = models.Itinerary(
            trip_id=db_trip.id,
            day_number=it_day["day_number"],
            activities=it_day["activities"],
            description=it_day.get("description", "")
        )
        db.add(db_itinerary)

    db.commit()
    db.refresh(db_trip)
    return db_trip

@router.get("/", response_model=List[schemas.TripOut])
def get_user_trips(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trips = db.query(models.Trip).filter(models.Trip.user_id == current_user.id).order_by(models.Trip.created_at.desc()).all()
    return trips

@router.get("/{trip_id}", response_model=schemas.TripOut)
def get_trip_details(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@router.delete("/{trip_id}", status_code=204)
def delete_trip(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db.delete(trip)
    db.commit()
    return None

@router.get("/reverse/search", response_model=List[schemas.DestinationSearchScore])
def reverse_travel_search(
    budget: float = Query(...),
    days: int = Query(...),
    travel_type: str = Query(...),
    travelers_count: int = Query(1),
    starting_city: Optional[str] = Query("Your City"),
    comfort_score: Optional[int] = Query(50),
    db: Session = Depends(get_db)
):
    # Fetch all destinations
    destinations = db.query(models.Destination).all()
    
    scored = []
    for dest in destinations:
        costs = calculate_costs(dest, days, travelers_count, comfort_score or 50, starting_city or "")
        est_cost = costs["total_estimated_cost"]

        # Calculate using the shared scoring engine
        score = calculate_weighted_score(dest, costs, budget, days, travel_type, comfort_score or 50)

        # Budget fit percentage for display
        budget_fit_pct = round((est_cost / budget) * 100, 1)

        scored.append({
            "destination": dest,
            "estimated_cost": est_cost,
            "budget_fit": budget_fit_pct,
            "rating": dest.rating,
            "value_score": score
        })

    # Sort by value_score descending
    scored.sort(key=lambda x: x["value_score"], reverse=True)
    return scored[:5]

@router.post("/{trip_id}/optimize", response_model=schemas.OptimizationResponse)
def optimize_trip(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    dest = trip.destination
    alloc = trip.budget_allocation
    if not alloc:
        raise HTTPException(status_code=400, detail="Trip does not have budget allocation")

    options = []

    # Option 1: Reduce Hotel Cost (Switch hotel tier down)
    if trip.hotel_tier == "Luxury":
        # New hotel cost at Mid-range
        new_hotel_cost = dest.avg_hotel_cost * 1.0 * trip.days
        diff = alloc.hotel_cost - new_hotel_cost
        if diff > 100:
            options.append(
                schemas.OptimizationOption(
                    action_key="reduce_hotel",
                    label="Downgrade Hotel to Mid-Range",
                    cost_difference=-diff,
                    description="Switch accommodation from luxury resort to a highly rated 3-star hotel.",
                    new_allocation=schemas.BudgetAllocationBase(
                        transport_cost=alloc.transport_cost,
                        hotel_cost=new_hotel_cost,
                        food_cost=alloc.food_cost,
                        activities_cost=alloc.activities_cost,
                        local_transport_cost=alloc.local_transport_cost,
                        taxes_fees_cost=alloc.taxes_fees_cost * 0.9, # reduced taxes
                        emergency_reserve=alloc.emergency_reserve * 0.95,
                        emergency_reserve_cost=alloc.emergency_reserve * 0.95 # legacy helper support
                    )
                )
            )
    elif trip.hotel_tier == "Mid-Range":
        # New hotel cost at Budget
        new_hotel_cost = dest.avg_hotel_cost * 0.65 * trip.days
        diff = alloc.hotel_cost - new_hotel_cost
        if diff > 100:
            options.append(
                schemas.OptimizationOption(
                    action_key="reduce_hotel",
                    label="Switch to Budget Hotel / Homestay",
                    cost_difference=-diff,
                    description="Opt for cozy local homestays or premium hostels instead of mid-tier hotels.",
                    new_allocation=schemas.BudgetAllocationBase(
                        transport_cost=alloc.transport_cost,
                        hotel_cost=new_hotel_cost,
                        food_cost=alloc.food_cost,
                        activities_cost=alloc.activities_cost,
                        local_transport_cost=alloc.local_transport_cost,
                        taxes_fees_cost=alloc.taxes_fees_cost * 0.85,
                        emergency_reserve=alloc.emergency_reserve * 0.92
                    )
                )
            )

    # Option 2: Switch flight to train (Reduce Travel Cost)
    if trip.transport_mode == "Flight":
        new_train_cost = max(1000.0, dest.avg_travel_cost * 0.4) * trip.travelers_count
        diff = alloc.transport_cost - new_train_cost
        if diff > 100:
            options.append(
                schemas.OptimizationOption(
                    action_key="reduce_travel",
                    label="Switch Transport from Flight to Train",
                    cost_difference=-diff,
                    description="Travel by AC Sleeper trains instead of flights. Adds travel time but heavily cuts costs.",
                    new_allocation=schemas.BudgetAllocationBase(
                        transport_cost=new_train_cost,
                        hotel_cost=alloc.hotel_cost,
                        food_cost=alloc.food_cost,
                        activities_cost=alloc.activities_cost,
                        local_transport_cost=alloc.local_transport_cost,
                        taxes_fees_cost=alloc.taxes_fees_cost * 0.7,
                        emergency_reserve=alloc.emergency_reserve * 0.9
                    )
                )
            )

    # Option 3: Increase Comfort (Upgrade hotel if they have lots of savings)
    current_savings = trip.budget - trip.total_estimated_cost
    if current_savings > 3000.0:
        if trip.hotel_tier == "Budget":
            new_hotel_cost = dest.avg_hotel_cost * 1.0 * trip.days
            diff = new_hotel_cost - alloc.hotel_cost
            options.append(
                schemas.OptimizationOption(
                    action_key="increase_comfort",
                    label="Upgrade Hotel to Mid-Range",
                    cost_difference=diff,
                    description="Upgrade your accommodation for better services, private pool and complimentary breakfast.",
                    new_allocation=schemas.BudgetAllocationBase(
                        transport_cost=alloc.transport_cost,
                        hotel_cost=new_hotel_cost,
                        food_cost=alloc.food_cost * 1.1, # slightly better meals
                        activities_cost=alloc.activities_cost,
                        local_transport_cost=alloc.local_transport_cost,
                        taxes_fees_cost=alloc.taxes_fees_cost * 1.15,
                        emergency_reserve=alloc.emergency_reserve * 1.05
                    )
                )
            )
        elif trip.hotel_tier == "Mid-Range":
            new_hotel_cost = dest.avg_hotel_cost * 1.85 * trip.days
            diff = new_hotel_cost - alloc.hotel_cost
            options.append(
                schemas.OptimizationOption(
                    action_key="increase_comfort",
                    label="Upgrade Hotel to Premium Luxury Resort",
                    cost_difference=diff,
                    description="Immerse in luxury. Premium room upgrades, spa sessions, and infinity pools.",
                    new_allocation=schemas.BudgetAllocationBase(
                        transport_cost=alloc.transport_cost,
                        hotel_cost=new_hotel_cost,
                        food_cost=alloc.food_cost * 1.3,
                        activities_cost=alloc.activities_cost,
                        local_transport_cost=alloc.local_transport_cost,
                        taxes_fees_cost=alloc.taxes_fees_cost * 1.35,
                        emergency_reserve=alloc.emergency_reserve * 1.2
                    )
                )
            )

    # Option 4: Cut down activities
    if alloc.activities_cost > 1000.0:
        new_act = alloc.activities_cost * 0.5
        diff = alloc.activities_cost - new_act
        options.append(
            schemas.OptimizationOption(
                action_key="reduce_activities",
                label="Streamline Activities Schedule",
                cost_difference=-diff,
                description="Reduce pre-booked activities by 50%. Focus on free natural sights and self-guided exploration.",
                new_allocation=schemas.BudgetAllocationBase(
                    transport_cost=alloc.transport_cost,
                    hotel_cost=alloc.hotel_cost,
                    food_cost=alloc.food_cost,
                    activities_cost=new_act,
                    local_transport_cost=alloc.local_transport_cost,
                    taxes_fees_cost=alloc.taxes_fees_cost * 0.95,
                    emergency_reserve=alloc.emergency_reserve * 0.95
                )
            )
        )

    # Format current allocations to match BaseSchema
    current_alloc = schemas.BudgetAllocationBase(
        transport_cost=alloc.transport_cost,
        hotel_cost=alloc.hotel_cost,
        food_cost=alloc.food_cost,
        activities_cost=alloc.activities_cost,
        emergency_reserve=alloc.emergency_reserve,
        local_transport_cost=alloc.local_transport_cost,
        taxes_fees_cost=alloc.taxes_fees_cost
    )

    return {
        "current_cost": trip.total_estimated_cost,
        "budget": trip.budget,
        "allocations": current_alloc,
        "options": options
    }

@router.post("/{trip_id}/optimize/apply")
def apply_optimization(
    trip_id: int,
    payload: dict,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    alloc = trip.budget_allocation
    if not alloc:
        raise HTTPException(status_code=400, detail="Budget allocation not found")

    dest = trip.destination
    action_key = payload.get("action_key")

    if action_key == "reduce_hotel":
        if trip.hotel_tier == "Luxury":
            trip.hotel_tier = "Mid-Range"
            alloc.hotel_cost = dest.avg_hotel_cost * 1.0 * trip.days
        elif trip.hotel_tier == "Mid-Range":
            trip.hotel_tier = "Budget"
            alloc.hotel_cost = dest.avg_hotel_cost * 0.65 * trip.days
        alloc.taxes_fees_cost *= 0.9
        alloc.emergency_reserve *= 0.95
    elif action_key == "reduce_travel":
        if trip.transport_mode == "Flight":
            trip.transport_mode = "Train"
            alloc.transport_cost = max(1000.0, dest.avg_travel_cost * 0.4) * trip.travelers_count
        alloc.taxes_fees_cost *= 0.75
        alloc.emergency_reserve *= 0.9
    elif action_key == "increase_comfort":
        if trip.hotel_tier == "Budget":
            trip.hotel_tier = "Mid-Range"
            alloc.hotel_cost = dest.avg_hotel_cost * 1.0 * trip.days
            alloc.food_cost *= 1.1
        elif trip.hotel_tier == "Mid-Range":
            trip.hotel_tier = "Luxury"
            alloc.hotel_cost = dest.avg_hotel_cost * 1.85 * trip.days
            alloc.food_cost *= 1.3
        alloc.taxes_fees_cost *= 1.2
        alloc.emergency_reserve *= 1.15
    elif action_key == "reduce_activities":
        alloc.activities_cost *= 0.5
        alloc.taxes_fees_cost *= 0.95
        alloc.emergency_reserve *= 0.95

    trip.total_estimated_cost = round(
        alloc.transport_cost + alloc.hotel_cost + alloc.food_cost +
        alloc.activities_cost + alloc.local_transport_cost +
        alloc.taxes_fees_cost + alloc.emergency_reserve,
        2
    )

    db.commit()
    return {
        "status": "success",
        "message": "Optimization applied successfully",
        "new_cost": trip.total_estimated_cost
    }

@router.get("/{trip_id}/pdf")
def download_trip_pdf(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Generate PDF in memory
    buffer = io.BytesIO()
    
    # 0.5 inch margins
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=36, 
        leftMargin=36, 
        topMargin=36, 
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#6d28d9'), # violet-700
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=colors.HexColor('#1f2937'), # gray-800
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4b5563') # gray-600
    )

    bold_body_style = ParagraphStyle(
        'DocBoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    header_col_style = ParagraphStyle(
        'HeadCol',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    story = []
    
    # 1. Header Details
    story.append(Paragraph(f"BudgetBound Travel Plan — {trip.destination.name}", title_style))
    story.append(Paragraph(f"Generated for {current_user.name} on {datetime.date.today().strftime('%B %d, %Y')}", body_style))
    story.append(Spacer(1, 15))
    
    # 2. Trip Summary Table
    summary_data = [
        [Paragraph("Destination", bold_body_style), Paragraph(f"{trip.destination.name}, {trip.destination.state}", body_style),
         Paragraph("Duration", bold_body_style), Paragraph(f"{trip.days} Days", body_style)],
        [Paragraph("Starting Budget", bold_body_style), Paragraph(f"INR {trip.budget:,.2f}", body_style),
         Paragraph("Estimated Cost", bold_body_style), Paragraph(f"INR {trip.total_estimated_cost:,.2f}", body_style)],
        [Paragraph("Comfort Score", bold_body_style), Paragraph(f"{trip.comfort_score}/100", body_style),
         Paragraph("Travelers", bold_body_style), Paragraph(f"{trip.travelers_count} traveler(s)", body_style)],
        [Paragraph("Hotel Quality", bold_body_style), Paragraph(f"{trip.hotel_tier}", body_style),
         Paragraph("Transport Mode", bold_body_style), Paragraph(f"{trip.transport_mode}", body_style)]
    ]
    
    t_summary = Table(summary_data, colWidths=[110, 160, 110, 160])
    t_summary.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f9fafb')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#f9fafb')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 20))
    
    # 3. Budget Allocation Breakdown
    story.append(Paragraph("Estimated Cost Allocation Breakdown", subtitle_style))
    alloc = trip.budget_allocation
    
    alloc_data = [
        [Paragraph("Category", header_col_style), Paragraph("Estimated Cost", header_col_style)],
        [Paragraph("Transportation", body_style), Paragraph(f"INR {alloc.transport_cost:,.2f}", body_style)],
        [Paragraph("Accommodation (Hotel)", body_style), Paragraph(f"INR {alloc.hotel_cost:,.2f}", body_style)],
        [Paragraph("Food & Dining", body_style), Paragraph(f"INR {alloc.food_cost:,.2f}", body_style)],
        [Paragraph("Activities & Entry Fees", body_style), Paragraph(f"INR {alloc.activities_cost:,.2f}", body_style)],
        [Paragraph("Local Travel / Cabs", body_style), Paragraph(f"INR {alloc.local_transport_cost:,.2f}", body_style)],
        [Paragraph("Taxes & Booking Fees", body_style), Paragraph(f"INR {alloc.taxes_fees_cost:,.2f}", body_style)],
        [Paragraph("Emergency Reserve", body_style), Paragraph(f"INR {alloc.emergency_reserve:,.2f}", body_style)],
        [Paragraph("Total Estimated Trip Cost", bold_body_style), Paragraph(f"INR {trip.total_estimated_cost:,.2f}", bold_body_style)]
    ]
    t_alloc = Table(alloc_data, colWidths=[270, 270])
    t_alloc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#6d28d9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#f3f4f6')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_alloc)
    story.append(Spacer(1, 20))
    
    # 4. Daily Itinerary Section
    story.append(Paragraph("Daily Itinerary Plan", subtitle_style))
    
    itineraries = sorted(trip.itineraries, key=lambda x: x.day_number)
    for it in itineraries:
        day_story = []
        day_story.append(Paragraph(f"Day {it.day_number} Plan — {it.description or ''}", bold_body_style))
        day_story.append(Spacer(1, 5))
        
        act_data = [[Paragraph("Time Slot", header_col_style), Paragraph("Activity Title", header_col_style), Paragraph("Estimated Expense", header_col_style)]]
        
        activities = it.activities if isinstance(it.activities, list) else []
        for act in activities:
            cost_val = act.get('cost', 0.0)
            cost_str = f"INR {cost_val:,.2f}" if cost_val > 0 else "Included / Free"
            act_data.append([
                Paragraph(act.get('time', 'Morning'), body_style),
                Paragraph(act.get('title', 'Leisure time'), body_style),
                Paragraph(cost_str, body_style)
            ])
            
        t_act = Table(act_data, colWidths=[100, 310, 130])
        t_act.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4b5563')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        
        day_story.append(t_act)
        day_story.append(Spacer(1, 12))
        
        story.append(KeepTogether(day_story))

    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=budgetbound_{trip.destination.name.replace(' ', '_').lower()}.pdf"}
    )
