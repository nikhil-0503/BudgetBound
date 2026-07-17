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

import uuid

def calculate_weather_intelligence(dest, month: int = None):
    if month is None:
        month = datetime.datetime.now().month
        
    best_season_str = dest.best_season or "October to March"
    
    # 1. Check is_in_best_season
    months_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }
    s = best_season_str.lower()
    words = []
    for m in months_map.keys():
        if m in s:
            words.append((s.find(m), months_map[m]))
    words.sort()
    
    in_best = True
    if len(words) >= 2:
        start_m = words[0][1]
        end_m = words[-1][1]
        if start_m <= end_m:
            in_best = start_m <= month <= end_m
        else:
            in_best = month >= start_m or month <= end_m
    elif len(words) == 1:
        in_best = month == words[0][1]

    # 2. Determine season name
    if month in [12, 1, 2]:
        season = "Winter"
    elif month in [3, 4, 5]:
        season = "Summer"
    elif month in [6, 7, 8, 9]:
        season = "Monsoon"
    else:
        season = "Post-Monsoon"

    # 3. Determine weather details based on season & category
    cat = (dest.category or "").lower()
    
    if season == "Winter":
        if "nature" in cat or "hills" in cat or "trek" in cat:
            temp = "5°C – 15°C"
            crowd = "High"
            rain = "5% - 10%"
        else:
            temp = "18°C – 26°C"
            crowd = "High"
            rain = "0% - 5%"
    elif season == "Summer":
        if "nature" in cat or "hills" in cat or "trek" in cat:
            temp = "15°C – 22°C"
            crowd = "High"
            rain = "5% - 15%"
        else:
            temp = "32°C – 42°C"
            crowd = "Low"
            rain = "0% - 10%"
    elif season == "Monsoon":
        if "nature" in cat or "hills" in cat or "trek" in cat:
            temp = "18°C – 24°C"
            crowd = "Low"
            rain = "85% - 98%"
        else:
            temp = "26°C – 32°C"
            crowd = "Medium"
            rain = "70% - 90%"
    else: # Post-Monsoon
        temp = "22°C – 28°C"
        crowd = "Medium"
        rain = "10% - 25%"

    # 4. Rating
    if in_best:
        rating = "Excellent" if season in ["Winter", "Post-Monsoon"] else "Good"
    else:
        if season == "Monsoon" and "beach" in cat:
            rating = "Avoid"
        elif season == "Summer" and ("city" in cat or "religious" in cat or "historic" in cat):
            rating = "Fair"
        else:
            rating = "Fair"

    # 5. Recommendation
    if rating == "Excellent":
        rec = "Perfect time to visit! Enjoy best sightseeing views, clear skies, and fully open outdoor trails."
    elif rating == "Good":
        rec = "Great conditions for travel. Sightseeing and activities are fully functional. Crowd is moderate."
    elif rating == "Fair":
        if season == "Summer":
            rec = "Warm weather. Best for morning/evening sightseeing. Stay hydrated and pack light clothes."
        else:
            rec = "Moderate weather with occasional showers. Good for relaxed, budget travel."
    else: # Avoid
        rec = "Off-season. Severe rain and high beach tides. Water sports and beach shacks are closed."

    if season == "Monsoon" and rating != "Avoid":
        rec = "Excellent for lush greenery and active waterfalls. Beautiful landscapes, but carry rain protection."

    return {
        "current_season": season,
        "best_season": best_season_str,
        "season_rating": rating,
        "crowd_level": crowd,
        "temperature_range": temp,
        "rain_probability": rain,
        "recommendation": rec
    }

def calculate_carbon_footprint(transport_mode: str, transport_cost: float):
    # Determine CO2 based on mode
    # Flight: 0.14 kg CO2 per km. Cost per km average = 6.0 INR -> 0.023 kg per INR.
    # Train: 0.015 kg CO2 per km. Cost per km average = 1.5 INR -> 0.010 kg per INR.
    if transport_mode == "Flight":
        co2 = round(transport_cost * 0.042, 1)
        score = 30 if co2 >= 100 else 65
        rating = "High Impact" if co2 >= 100 else "Moderate"
        alt_savings = round(co2 * 0.90, 1)  # Train would save 90%
    else:
        co2 = round(transport_cost * 0.012, 1)
        score = 92
        rating = "Eco Friendly"
        # Flight would cost 10x
        alt_savings = round(co2 * 9.0, 1)  # Train saves X vs flight
        
    return {
        "transport_mode": transport_mode,
        "co2_emissions": co2,
        "carbon_rating": rating,
        "eco_score": score,
        "alternative_savings": alt_savings
    }

def generate_default_packing_list(category: str, season: str, duration: int, comfort: int) -> List[str]:
    items = [
        "Toothbrush & Paste",
        "Government ID Card",
        "Phone Chargers",
        "Cash & Debit Cards",
        "First-aid medical kit"
    ]
    
    # Category
    cat_lower = category.lower()
    if "beach" in cat_lower:
        items.extend(["Swimwear", "Sunscreen SPF 50+", "Beach Slippers", "Sun Hat", "Sunglasses"])
    elif "nature" in cat_lower or "adventure" in cat_lower or "trek" in cat_lower:
        items.extend(["Trekking Shoes", "Windcheater Jacket", "Reusable Water Bottle", "High Capacity Power Bank", "Hand Sanitizer"])
    elif "religious" in cat_lower or "temple" in cat_lower:
        items.extend(["Traditional Clothing", "Comfortable Slip-on Shoes", "Scarf / Shawl", "Sanitizer Wipes"])
    else: # City/Solo/Family/Others
        items.extend(["Comfortable Sneakers", "Travel Pillow", "Small Backpack"])
        
    # Season
    season_lower = season.lower()
    if "monsoon" in season_lower:
        items.extend(["Umbrella", "Waterproof Bag Cover", "Ziplock bags for electronics"])
    elif "winter" in season_lower:
        items.extend(["Heavy Warm Sweater", "Thermals", "Lip Balm & Cold Cream"])
    elif "summer" in season_lower:
        items.extend(["Light Cotton T-shirts", "Sunglasses", "Cap / Visor", "Deodorant"])
        
    # Duration
    if duration >= 5:
        items.extend(["Laundry Bag", "Extra pair of socks", "Travel-size detergent"])
        
    # Comfort Level
    if comfort < 30:
        items.extend(["Quick-dry Travel Towel", "Waterproof pouch", "Sleeping sheet liner"])
    elif comfort > 75:
        items.extend(["Eye sleeping mask", "Noise-cancelling headphones"])
        
    # Unique items
    return list(dict.fromkeys(items))

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

    # Expanded regional multiplier matrix — geographically calibrated haul distances.
    # Multiplier is applied to the base cost BEFORE flooring so cheap destinations
    # still reflect regional distance differences.
    multiplier = 1.0
    if start_region != "Unknown" and dest_region != "Unknown":
        if start_region == dest_region:
            multiplier = 0.45   # same region — short haul, heavy discount
        else:
            # Long haul: North↔South (Delhi↔Chennai ~2200km), East↔West (Kolkata↔Mumbai ~2000km)
            long_haul = (
                {start_region, dest_region} == {"North", "South"} or
                {start_region, dest_region} == {"East", "West"}
            )
            # Medium-long: North↔West (Delhi↔Goa ~1900km), North↔East (Delhi↔Kolkata ~1500km)
            medium_long = (
                {start_region, dest_region} == {"North", "West"} or
                {start_region, dest_region} == {"North", "East"}
            )
            # Medium: South↔West (Chennai↔Goa ~1000km), South↔East (Chennai↔Kolkata ~1700km)
            medium = (
                {start_region, dest_region} == {"South", "West"} or
                {start_region, dest_region} == {"South", "East"}
            )
            if long_haul:
                multiplier = 1.45   # Delhi↔Chennai, Kolkata↔Goa — farthest routes
            elif medium_long:
                multiplier = 1.25   # Delhi↔Goa, Delhi↔Kolkata
            elif medium:
                multiplier = 1.05   # Chennai↔Goa, Chennai↔Kolkata — shorter routes
            else:
                multiplier = 1.0    # fallback for any unmatched pair

    if comfort_score < 50:
        transport_mode = "Train"
        # Apply multiplier to base before flooring so regional distance is preserved
        base_train = dest.avg_travel_cost * 0.45 * multiplier
        transport_cost = max(600.0, base_train) * travelers
    else:
        transport_mode = "Flight"
        # Apply multiplier to base before flooring
        base_flight = dest.avg_travel_cost * 1.25 * multiplier
        transport_cost = max(2500.0, base_flight) * travelers

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

def calculate_score_breakdown(
    dest: models.Destination,
    costs: dict,
    budget: float,
    days: int,
    travel_type: str,
    comfort_score: int
) -> dict:
    # 1. Budget Fit (35%) — still the primary driver but comfort gets more room
    total_cost = costs["total_estimated_cost"]
    diff = abs(budget - total_cost) / budget
    if total_cost <= budget:
        budget_fit = 1.0 - diff  # closer to budget limit means higher resource utilisation
    else:
        budget_fit = max(0.0, 1.0 - diff * 4.0)  # heavy penalty if over budget

    # 2. Category Match (25%) — unchanged
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

    # 3. Rating Match (12%) — slightly reduced to make room for comfort
    rating_match = (dest.rating or 4.0) / 5.0

    # 4. Comfort Match (20%) — doubled from 10% so slider meaningfully reorders results.
    # A destination whose comfort_level is far from the user's comfort_score is penalised.
    comfort_match = 1.0 - abs(comfort_score - (dest.comfort_level or 50)) / 100.0

    # 5. Duration Suitability (8%) — minor factor
    rec_dur = dest.recommended_duration or 4
    duration_suitability = max(0.0, 1.0 - abs(days - rec_dur) / 5.0)

    # Weights: 35 + 25 + 12 + 20 + 8 = 100%
    weighted_score = (
        0.35 * budget_fit +
        0.25 * cat_match +
        0.12 * rating_match +
        0.20 * comfort_match +
        0.08 * duration_suitability
    ) * 100.0
    
    # Generate explanations
    # Each explanation includes the actual computed score so every destination
    # produces a different, specific explanation rather than generic template text.
    explanations = []

    # 1. Budget fit explanation
    budget_fit_pct = round(budget_fit * 100, 1)
    estimated_cost = costs["total_estimated_cost"]
    savings_amt = round(budget - estimated_cost, 0)
    if budget_fit >= 0.90:
        explanations.append(
            f"Excellent budget fit ({budget_fit_pct}%) — estimated cost ₹{estimated_cost:,.0f} leaves ₹{savings_amt:,.0f} unspent."
        )
    elif budget_fit >= 0.75:
        explanations.append(
            f"Good budget fit ({budget_fit_pct}%) — estimated ₹{estimated_cost:,.0f} uses most of your ₹{budget:,.0f} budget efficiently."
        )
    elif budget_fit >= 0.50:
        explanations.append(
            f"Moderate budget fit ({budget_fit_pct}%) — estimated ₹{estimated_cost:,.0f} is close to your ₹{budget:,.0f} budget limit."
        )
    else:
        explanations.append(
            f"Low budget fit ({budget_fit_pct}%) — estimated ₹{estimated_cost:,.0f} against ₹{budget:,.0f} budget. Consider adjusting days or comfort."
        )

    # 2. Travel type / category match explanation
    type_pct = round(cat_match * 100, 1)
    dest_cat = dest.category
    if cat_match >= 0.80:
        explanations.append(
            f"Strong {travel_type} match ({type_pct}%) — {dest.name} is categorised as {dest_cat} and scores highly for your travel style."
        )
    elif cat_match >= 0.55:
        explanations.append(
            f"Good {travel_type} alignment ({type_pct}%) — {dest.name} is a {dest_cat} destination with relevant attractions for your style."
        )
    else:
        explanations.append(
            f"Partial {travel_type} match ({type_pct}%) — {dest.name} is primarily a {dest_cat} destination but has activities that suit your interests."
        )

    # 3. Comfort match explanation
    comfort_match_pct = round(comfort_match * 100, 1)
    dest_comfort = dest.comfort_level or 50
    gap = abs(comfort_score - dest_comfort)
    if comfort_match >= 0.90:
        explanations.append(
            f"Comfort alignment is excellent ({comfort_match_pct}%) — your comfort preference ({comfort_score}/100) closely matches this destination's standard ({dest_comfort}/100)."
        )
    elif comfort_match >= 0.75:
        explanations.append(
            f"Good comfort match ({comfort_match_pct}%) — your preference ({comfort_score}/100) is {gap} points from the destination comfort level ({dest_comfort}/100)."
        )
    else:
        explanations.append(
            f"Comfort mismatch ({comfort_match_pct}%) — your preference is {comfort_score}/100 but this destination is rated {dest_comfort}/100. Adjust comfort score for better fits."
        )

    # 4. Rating explanation
    rating_val = dest.rating or 4.0
    if rating_val >= 4.5:
        explanations.append(
            f"Top-rated destination — {dest.name} holds a {rating_val}/5.0 visitor rating, placing it in the top tier of all destinations."
        )
    elif rating_val >= 4.0:
        explanations.append(
            f"Highly rated — {dest.name} has a strong {rating_val}/5.0 visitor rating based on traveler feedback."
        )
    else:
        explanations.append(
            f"Moderately rated — {dest.name} has a {rating_val}/5.0 visitor rating. Fewer reviews or a niche appeal destination."
        )

    # 5. Duration suitability explanation
    dur_pct = round(duration_suitability * 100, 1)
    if duration_suitability >= 0.90:
        explanations.append(
            f"Ideal trip length — your {days}-day plan perfectly matches the recommended {rec_dur}-day itinerary for {dest.name} ({dur_pct}% suitability)."
        )
    elif days < rec_dur:
        explanations.append(
            f"Short trip alert ({dur_pct}%) — {dest.name} is best explored in {rec_dur} days; your {days}-day plan may miss some key attractions."
        )
    else:
        explanations.append(
            f"Extended stay ({dur_pct}%) — {dest.name} is ideally visited in {rec_dur} days; your {days}-day plan gives extra relaxation time."
        )

    return {
        "value_score": round(weighted_score, 2),
        "budget_compatibility": round(budget_fit * 100, 1),
        "trip_type_match": round(cat_match * 100, 1),
        "comfort_match": round(comfort_match * 100, 1),
        "destination_rating": round(rating_match * 100, 1),
        "duration_suitability": round(duration_suitability * 100, 1),
        "explanations": explanations
    }

def calculate_weighted_score(
    dest: models.Destination,
    costs: dict,
    budget: float,
    days: int,
    travel_type: str,
    comfort_score: int
) -> float:
    breakdown = calculate_score_breakdown(dest, costs, budget, days, travel_type, comfort_score)
    return breakdown["value_score"]


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
        under_budget = costs["total_estimated_cost"] <= req.budget

        matched_plans.append({
            "destination": dest,
            "costs": costs,
            "value_score": score,
            "savings": round(req.budget - costs["total_estimated_cost"], 2),
            "under_budget": under_budget
        })

    # --- Strict budget enforcement ---
    if req.destination_id is not None:
        # A specific destination was requested — check if it fits the budget
        selected_plan = matched_plans[0]
        if not selected_plan["under_budget"]:
            est = round(selected_plan["costs"]["total_estimated_cost"], 2)
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Selected destination '{selected_plan['destination'].name}' exceeds your budget. "
                    f"Estimated cost: INR {est:,.0f} vs your budget of INR {req.budget:,.0f}. "
                    f"Try increasing your budget or reducing duration/comfort level."
                )
            )
    else:
        # Full catalog mode — only consider under-budget destinations
        under_budget_plans = [p for p in matched_plans if p["under_budget"]]

        if not under_budget_plans:
            # No destination fits — find the closest one for a helpful message
            matched_plans.sort(key=lambda x: x["costs"]["total_estimated_cost"])
            cheapest = matched_plans[0]
            cheapest_cost = round(cheapest["costs"]["total_estimated_cost"], 2)
            raise HTTPException(
                status_code=422,
                detail=(
                    f"No destination found within your budget of INR {req.budget:,.0f}. "
                    f"The most affordable option ({cheapest['destination'].name}) costs approximately "
                    f"INR {cheapest_cost:,.0f}. Try increasing your budget, reducing trip duration, "
                    f"or lowering your comfort score."
                )
            )

        # Sort under-budget destinations by value score (best fit first)
        under_budget_plans.sort(key=lambda x: x["value_score"], reverse=True)
        selected_plan = under_budget_plans[0]

    # --- Generate all plan components ---
    dest = selected_plan["destination"]

    # 1. Daily itinerary
    itineraries = generate_itinerary_days(dest, req.days, req.comfort_score, req.travel_type)

    # 2. Weather intelligence
    dest.weather_intelligence = calculate_weather_intelligence(dest, None)

    # 3. Carbon footprint
    carbon_intel = calculate_carbon_footprint(
        selected_plan["costs"]["transport_mode"],
        selected_plan["costs"]["transport_cost"]
    )

    # 4. Score breakdown (explainability) — MUST be computed before return
    breakdown = calculate_score_breakdown(
        dest,
        selected_plan["costs"],
        req.budget,
        req.days,
        req.travel_type,
        req.comfort_score
    )

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
        "travel_type": req.travel_type,
        "breakdown": breakdown,
        "carbon_footprint": carbon_intel
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
        transport_mode=costs["transport_mode"],
        status=trip_data.get("status", "Planned"),
        start_date=trip_data.get("start_date"),
        is_public=False,
        share_token=uuid.uuid4().hex
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

    # Generate default checklist items
    month_val = None
    if db_trip.start_date:
        try:
            month_val = int(db_trip.start_date.split("-")[1])
        except Exception:
            pass

    dest = db.query(models.Destination).filter(models.Destination.id == db_trip.destination_id).first()
    weather_intel = calculate_weather_intelligence(dest, month_val)
    season_name = weather_intel["current_season"]

    default_packing_items = generate_default_packing_list(
        category=dest.category,
        season=season_name,
        duration=db_trip.days,
        comfort=db_trip.comfort_score
    )

    for item_name in default_packing_items:
        db_item = models.PackingItem(
            trip_id=db_trip.id,
            name=item_name,
            checked=False
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_trip)

    # Log Trip creation notification
    notif_msg = f"Your trip to {dest.name} has been planned successfully."
    if db_trip.start_date:
        notif_msg = f"Your trip to {dest.name} starts on {db_trip.start_date}."
    db.add(models.Notification(
        user_id=current_user.id,
        type="Upcoming Trip",
        message=notif_msg
    ))
    db.commit()
    return db_trip

def auto_update_trip_status(trip: models.Trip, db: Session):
    if not trip.status:
        trip.status = "Planned"
        db.commit()
        db.refresh(trip)
        
    if trip.status in ["Planned", "In Progress"] and trip.start_date:
        try:
            start_dt = datetime.datetime.strptime(trip.start_date, "%Y-%m-%d").date()
            today = datetime.date.today()
            end_dt = start_dt + datetime.timedelta(days=trip.days)
            
            new_status = trip.status
            if today >= end_dt:
                new_status = "Completed"
            elif today >= start_dt:
                new_status = "In Progress"
                
            if new_status != trip.status:
                trip.status = new_status
                db.commit()
                db.refresh(trip)
        except Exception:
            pass

def attach_trip_intelligence(t: models.Trip, db: Session):
    auto_update_trip_status(t, db)
    actual_spent = sum([e.amount for e in t.expenses])
    t.actual_spending = round(actual_spent, 2)
    t.savings = round(max(0.0, t.budget - actual_spent), 2)
    
    month_val = None
    if t.start_date:
        try:
            month_val = int(t.start_date.split("-")[1])
        except Exception:
            pass
    t.destination.weather_intelligence = calculate_weather_intelligence(t.destination, month_val)
    
    cost_val = t.budget_allocation.transport_cost if t.budget_allocation else (t.total_estimated_cost * 0.25)
    t.carbon_footprint = calculate_carbon_footprint(t.transport_mode, cost_val)

@router.get("/", response_model=List[schemas.TripOut])
def get_user_trips(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trips = db.query(models.Trip).filter(models.Trip.user_id == current_user.id).order_by(models.Trip.created_at.desc()).all()
    for t in trips:
        attach_trip_intelligence(t, db)
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
        
    attach_trip_intelligence(trip, db)
    return trip

@router.put("/{trip_id}", response_model=schemas.TripOut)
def update_trip(
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
        
    if "budget" in payload:
        trip.budget = float(payload["budget"])
    if "days" in payload:
        trip.days = int(payload["days"])
    if "travelers_count" in payload:
        trip.travelers_count = int(payload["travelers_count"])
    if "travel_type" in payload:
        trip.travel_type = payload["travel_type"]
    if "comfort_score" in payload:
        trip.comfort_score = int(payload["comfort_score"])
    if "status" in payload:
        trip.status = payload["status"]
    if "start_date" in payload:
        trip.start_date = payload["start_date"]
        
    db.commit()
    db.refresh(trip)
    
    attach_trip_intelligence(trip, db)
    return trip

@router.patch("/{trip_id}/status", response_model=schemas.TripOut)
def update_trip_status_endpoint(
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
        
    status_val = payload.get("status")
    if not status_val:
        raise HTTPException(status_code=400, detail="Status value is required")
        
    valid_statuses = ["Draft", "Planned", "In Progress", "Completed", "Cancelled"]
    if status_val not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status value. Must be one of {valid_statuses}")
        
    trip.status = status_val
    db.commit()
    db.refresh(trip)
    
    attach_trip_intelligence(trip, db)
    return trip

@router.post("/{trip_id}/duplicate", response_model=schemas.TripOut)
def duplicate_trip(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    orig = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not orig:
        raise HTTPException(status_code=404, detail="Trip to duplicate not found")
        
    dup_trip = models.Trip(
        user_id=current_user.id,
        destination_id=orig.destination_id,
        budget=orig.budget,
        days=orig.days,
        travelers_count=orig.travelers_count,
        travel_type=orig.travel_type,
        comfort_score=orig.comfort_score,
        total_estimated_cost=orig.total_estimated_cost,
        hotel_tier=orig.hotel_tier,
        transport_mode=orig.transport_mode,
        status="Draft",
        start_date=orig.start_date,
        is_public=False,
        share_token=uuid.uuid4().hex
    )
    db.add(dup_trip)
    db.commit()
    db.refresh(dup_trip)
    
    if orig.budget_allocation:
        dup_alloc = models.BudgetAllocation(
            trip_id=dup_trip.id,
            transport_cost=orig.budget_allocation.transport_cost,
            hotel_cost=orig.budget_allocation.hotel_cost,
            food_cost=orig.budget_allocation.food_cost,
            activities_cost=orig.budget_allocation.activities_cost,
            local_transport_cost=orig.budget_allocation.local_transport_cost,
            taxes_fees_cost=orig.budget_allocation.taxes_fees_cost,
            emergency_reserve=orig.budget_allocation.emergency_reserve
        )
        db.add(dup_alloc)
        
    for it in orig.itineraries:
        dup_it = models.Itinerary(
            trip_id=dup_trip.id,
            day_number=it.day_number,
            activities=it.activities,
            description=it.description
        )
        db.add(dup_it)
        
    # Duplicate packing checklist
    for item in orig.packing_items:
        dup_item = models.PackingItem(
            trip_id=dup_trip.id,
            name=item.name,
            checked=item.checked
        )
        db.add(dup_item)
        
    db.commit()
    db.refresh(dup_trip)
    
    attach_trip_intelligence(dup_trip, db)
    return dup_trip

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

@router.get("/{trip_id}/checklist", response_model=List[schemas.PackingItemOut])
def get_trip_checklist(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip.packing_items

@router.post("/{trip_id}/checklist", response_model=schemas.PackingItemOut)
def add_checklist_item(
    trip_id: int,
    payload: dict,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Item name is required")
        
    db_item = models.PackingItem(
        trip_id=trip_id,
        name=name,
        checked=False
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/{trip_id}/checklist/{item_id}", response_model=schemas.PackingItemOut)
def toggle_checklist_item(
    trip_id: int,
    item_id: int,
    payload: dict,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    item = db.query(models.PackingItem).filter(models.PackingItem.id == item_id, models.PackingItem.trip_id == trip_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Packing item not found")
        
    if "checked" in payload:
        item.checked = bool(payload["checked"])
    if "name" in payload:
        item.name = payload["name"]
        
    db.commit()
    db.refresh(item)

    # Check for checklist completion notification
    all_items = db.query(models.PackingItem).filter(models.PackingItem.trip_id == trip_id).all()
    if all_items:
        total_items = len(all_items)
        packed_items = sum([1 for pi in all_items if pi.checked])
        if packed_items == total_items:
            comp_msg = f"Congratulations! Your packing checklist for trip to {trip.destination.name} is 100% complete."
            exists = db.query(models.Notification).filter(
                models.Notification.user_id == current_user.id,
                models.Notification.message == comp_msg
            ).first()
            if not exists:
                db.add(models.Notification(
                    user_id=current_user.id,
                    type="Checklist Completed",
                    message=comp_msg
                ))
                db.commit()
        elif packed_items == 1:
            # Packing started
            start_msg = f"Packing checklist for your trip to {trip.destination.name} has been initiated."
            exists = db.query(models.Notification).filter(
                models.Notification.user_id == current_user.id,
                models.Notification.message == start_msg
            ).first()
            if not exists:
                db.add(models.Notification(
                    user_id=current_user.id,
                    type="Packing Reminder",
                    message=start_msg
                ))
                db.commit()
    return item

@router.delete("/{trip_id}/checklist/{item_id}", status_code=204)
def delete_checklist_item(
    trip_id: int,
    item_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    item = db.query(models.PackingItem).filter(models.PackingItem.id == item_id, models.PackingItem.trip_id == trip_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Packing item not found")
        
    db.delete(item)
    db.commit()
    return None

@router.post("/{trip_id}/share/toggle", response_model=schemas.TripOut)
def toggle_trip_share(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    trip.is_public = not trip.is_public
    if not trip.share_token:
        trip.share_token = uuid.uuid4().hex
        
    db.commit()
    db.refresh(trip)
    
    # Log public share setting updates
    if trip.is_public:
        share_msg = f"Your travel plan to {trip.destination.name} is now public and shared successfully."
        db.add(models.Notification(
            user_id=current_user.id,
            type="Trip Shared Successfully",
            message=share_msg
        ))
        db.commit()
        
    attach_trip_intelligence(trip, db)
    return trip

@router.get("/share/{share_token}", response_model=schemas.TripOut)
def get_shared_trip_details(
    share_token: str,
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(
        models.Trip.share_token == share_token,
        models.Trip.is_public == True
    ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Shared trip not found or this trip is set to private.")
        
    # Auto-update status
    if trip.status in ["Planned", "In Progress"] and trip.start_date:
        try:
            start_dt = datetime.datetime.strptime(trip.start_date, "%Y-%m-%d").date()
            today = datetime.date.today()
            end_dt = start_dt + datetime.timedelta(days=trip.days)
            
            new_status = trip.status
            if today >= end_dt:
                new_status = "Completed"
            elif today >= start_dt:
                new_status = "In Progress"
                
            if new_status != trip.status:
                trip.status = new_status
                db.commit()
                db.refresh(trip)
        except Exception:
            pass
            
    # Calculate spending/savings
    actual_spent = sum([e.amount for e in trip.expenses])
    trip.actual_spending = round(actual_spent, 2)
    trip.savings = round(max(0.0, trip.budget - actual_spent), 2)
    
    # Calculate weather intelligence
    month_val = None
    if trip.start_date:
        try:
            month_val = int(trip.start_date.split("-")[1])
        except Exception:
            pass
    trip.destination.weather_intelligence = calculate_weather_intelligence(trip.destination, month_val)
    
    # Calculate carbon footprint
    cost_val = trip.budget_allocation.transport_cost if trip.budget_allocation else (trip.total_estimated_cost * 0.25)
    trip.carbon_footprint = calculate_carbon_footprint(trip.transport_mode, cost_val)
    
    return trip



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
    if not destinations:
        raise HTTPException(
            status_code=404,
            detail="Destination dataset is empty. Please seed the database first."
        )

    comfort = comfort_score or 50
    city = starting_city or ""

    all_scored = []
    for dest in destinations:
        costs = calculate_costs(dest, days, travelers_count, comfort, city)
        est_cost = costs["total_estimated_cost"]
        score = calculate_weighted_score(dest, costs, budget, days, travel_type, comfort)
        budget_fit_pct = round((est_cost / budget) * 100, 1)
        breakdown = calculate_score_breakdown(dest, costs, budget, days, travel_type, comfort)
        all_scored.append({
            "destination": dest,
            "estimated_cost": est_cost,
            "budget_fit": budget_fit_pct,
            "rating": dest.rating,
            "value_score": score,
            "breakdown": breakdown
        })

    # --- HARD BUDGET CONSTRAINT ---
    # Step 1: Keep only destinations whose estimated cost is within budget.
    under_budget = [s for s in all_scored if s["estimated_cost"] <= budget]

    # Step 2: If nothing fits, return a 422 with the cheapest available option.
    if not under_budget:
        all_scored.sort(key=lambda x: x["estimated_cost"])
        cheapest = all_scored[0]
        cheapest_cost = round(cheapest["estimated_cost"], 0)
        raise HTTPException(
            status_code=422,
            detail=(
                f"No destination found within your selected budget of ₹{budget:,.0f}. "
                f"The most affordable option is {cheapest['destination'].name} "
                f"at approximately ₹{cheapest_cost:,.0f}. "
                f"Try increasing your budget, reducing trip duration, or lowering comfort score."
            )
        )

    # Step 3: Rank the under-budget destinations by value_score.
    under_budget.sort(key=lambda x: x["value_score"], reverse=True)
    return under_budget[:8]

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
        
        act_data = [[
            Paragraph("Time Slot", header_col_style), 
            Paragraph("Duration", header_col_style), 
            Paragraph("Category", header_col_style), 
            Paragraph("Activity Title", header_col_style), 
            Paragraph("Estimated Expense", header_col_style)
        ]]
        
        activities = it.activities if isinstance(it.activities, list) else []
        for act in activities:
            cost_val = act.get('cost', 0.0)
            cost_str = f"INR {cost_val:,.2f}" if cost_val > 0 else "Included / Free"
            
            time_val = act.get('time', 'Morning')
            if time_val == 'Morning':
                time_val = '08:00'
            elif time_val == 'Afternoon':
                time_val = '13:00'
            elif time_val == 'Evening':
                time_val = '17:00'
            elif time_val == 'Night':
                time_val = '20:00'
                
            title = act.get('title', 'Leisure time')
            
            category = act.get('category')
            if not category:
                title_lower = str(title).lower()
                if 'hotel' in title_lower or 'check-in' in title_lower:
                    category = 'Hotel'
                elif 'lunch' in title_lower or 'dinner' in title_lower or 'food' in title_lower or 'breakfast' in title_lower or 'dine' in title_lower or 'restaurant' in title_lower:
                    category = 'Food'
                elif 'travel' in title_lower or 'arrival' in title_lower or 'departure' in title_lower or 'flight' in title_lower or 'train' in title_lower or 'cab' in title_lower:
                    category = 'Travel'
                else:
                    category = 'Attraction'
                    
            duration = act.get('duration') or "2.0h"
            
            act_data.append([
                Paragraph(time_val, body_style),
                Paragraph(duration, body_style),
                Paragraph(category, body_style),
                Paragraph(title, body_style),
                Paragraph(cost_str, body_style)
            ])
            
        t_act = Table(act_data, colWidths=[70, 70, 75, 205, 120])
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

@router.put("/{trip_id}/allocations", response_model=schemas.TripOut)
def update_trip_allocations(
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
        raise HTTPException(status_code=400, detail="Trip does not have budget allocation")

    # Categories from allocation editor
    alloc.transport_cost = float(payload.get("transport_cost", alloc.transport_cost))
    alloc.hotel_cost = float(payload.get("hotel_cost", alloc.hotel_cost))
    alloc.food_cost = float(payload.get("food_cost", alloc.food_cost))
    alloc.activities_cost = float(payload.get("activities_cost", alloc.activities_cost))
    alloc.emergency_reserve = float(payload.get("emergency_reserve", alloc.emergency_reserve))
    
    # Reset helper columns to 0.0 if custom edit is applied
    alloc.local_transport_cost = float(payload.get("local_transport_cost", 0.0))
    alloc.taxes_fees_cost = float(payload.get("taxes_fees_cost", 0.0))

    # Recalculate trip total estimated cost
    trip.total_estimated_cost = round(
        alloc.transport_cost + alloc.hotel_cost + alloc.food_cost +
        alloc.activities_cost + alloc.emergency_reserve +
        alloc.local_transport_cost + alloc.taxes_fees_cost,
        2
    )

    db.commit()
    db.refresh(trip)
    return trip

@router.post("/{trip_id}/allocations/reset", response_model=schemas.TripOut)
def reset_trip_allocations(
    trip_id: int,
    payload: Optional[dict] = None,
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
        raise HTTPException(status_code=400, detail="Trip does not have budget allocation")

    starting_city = ""
    if payload:
        starting_city = payload.get("starting_city", "")

    # Re-calculate default costs
    dest = trip.destination
    costs = calculate_costs(
        dest=dest,
        days=trip.days,
        travelers=trip.travelers_count,
        comfort_score=trip.comfort_score,
        starting_city=starting_city
    )

    # Apply default values
    alloc.transport_cost = costs["transport_cost"]
    alloc.hotel_cost = costs["hotel_cost"]
    alloc.food_cost = costs["food_cost"]
    alloc.activities_cost = costs["activities_cost"]
    alloc.local_transport_cost = costs["local_transport_cost"]
    alloc.taxes_fees_cost = costs["taxes_fees_cost"]
    alloc.emergency_reserve = costs["emergency_reserve"]

    trip.total_estimated_cost = costs["total_estimated_cost"]

    db.commit()
    db.refresh(trip)
    return trip

