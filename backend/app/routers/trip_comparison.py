"""
Trip Comparison Feature - Compare multiple trip plans side by side
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app import models, auth
from app.database import get_db
from app.routers.trips import calculate_costs

router = APIRouter(prefix="/api/trips/compare", tags=["Trip Comparison"])


@router.post("/", response_model=Dict[str, Any])
def compare_trips(
    destination_ids: List[int],
    budget: float,
    days: int,
    starting_city: str,
    travelers_count: int = 1,
    comfort_score: int = 50,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compare multiple destinations side-by-side
    Returns detailed comparison of costs, savings, and features
    """
    
    if len(destination_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 destinations can be compared at once")
    
    if len(destination_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 destinations required for comparison")
    
    destinations = db.query(models.Destination).filter(
        models.Destination.id.in_(destination_ids)
    ).all()
    
    if len(destinations) != len(destination_ids):
        raise HTTPException(status_code=404, detail="One or more destinations not found")
    
    comparison_results = []
    
    for dest in destinations:
        costs = calculate_costs(dest, days, travelers_count, comfort_score, starting_city)
        
        savings = budget - costs["total_estimated_cost"]
        within_budget = costs["total_estimated_cost"] <= budget
        
        comparison_results.append({
            "destination": {
                "id": dest.id,
                "name": dest.name,
                "state": dest.state,
                "category": dest.category,
                "rating": dest.rating,
                "best_season": dest.best_season
            },
            "costs": {
                "total": costs["total_estimated_cost"],
                "transport": costs["transport_cost"],
                "hotel": costs["hotel_cost"],
                "food": costs["food_cost"],
                "activities": costs["activities_cost"],
                "local_transport": costs["local_transport_cost"],
                "taxes_fees": costs["taxes_fees_cost"],
                "emergency_reserve": costs["emergency_reserve"]
            },
            "hotel_tier": costs["hotel_tier"],
            "transport_mode": costs["transport_mode"],
            "savings": round(savings, 2),
            "within_budget": within_budget,
            "budget_utilization": round((costs["total_estimated_cost"] / budget) * 100, 1),
            "pros": generate_pros(dest, costs, budget),
            "cons": generate_cons(dest, costs, budget)
        })
    
    # Sort by total cost (cheapest first)
    comparison_results.sort(key=lambda x: x["costs"]["total"])
    
    # Add recommendations
    cheapest = comparison_results[0]
    best_value = max(comparison_results, key=lambda x: x["destination"]["rating"] / (x["costs"]["total"] / 1000))
    most_expensive = comparison_results[-1]
    
    return {
        "comparison": comparison_results,
        "summary": {
            "budget": budget,
            "days": days,
            "travelers": travelers_count,
            "comfort_level": comfort_score,
            "starting_city": starting_city
        },
        "recommendations": {
            "cheapest": cheapest["destination"]["name"],
            "cheapest_cost": cheapest["costs"]["total"],
            "best_value": best_value["destination"]["name"],
            "best_value_rating": best_value["destination"]["rating"],
            "most_expensive": most_expensive["destination"]["name"],
            "most_expensive_cost": most_expensive["costs"]["total"],
            "price_difference": round(most_expensive["costs"]["total"] - cheapest["costs"]["total"], 2)
        }
    }


def generate_pros(dest: models.Destination, costs: Dict, budget: float) -> List[str]:
    """Generate pros for a destination"""
    pros = []
    
    if costs["total_estimated_cost"] <= budget * 0.8:
        pros.append("Well within budget - plenty of savings")
    
    if dest.rating >= 4.5:
        pros.append(f"Highly rated ({dest.rating}/5 stars)")
    
    if costs["hotel_tier"] == "Luxury":
        pros.append("Luxury accommodation included")
    
    if costs["transport_mode"] == "Flight":
        pros.append("Fast travel via flight")
    
    if dest.comfort_level and dest.comfort_level >= 70:
        pros.append("High comfort destination")
    
    return pros[:3]  # Return top 3 pros


def generate_cons(dest: models.Destination, costs: Dict, budget: float) -> List[str]:
    """Generate cons for a destination"""
    cons = []
    
    if costs["total_estimated_cost"] > budget:
        cons.append(f"Over budget by ₹{round(costs['total_estimated_cost'] - budget, 2)}")
    
    if costs["hotel_tier"] == "Budget":
        cons.append("Basic accommodation only")
    
    if costs["transport_mode"] == "Train":
        cons.append("Longer travel time (train)")
    
    if dest.comfort_level and dest.comfort_level < 50:
        cons.append("Lower comfort amenities")
    
    if costs["total_estimated_cost"] > budget * 0.95:
        cons.append("Uses almost entire budget")
    
    return cons[:3]  # Return top 3 cons


@router.get("/saved", response_model=List[Dict[str, Any]])
def compare_saved_trips(
    trip_ids: List[int] = Query(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compare multiple saved trips
    """
    
    if len(trip_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 trips can be compared at once")
    
    trips = db.query(models.Trip).filter(
        models.Trip.id.in_(trip_ids),
        models.Trip.user_id == current_user.id
    ).all()
    
    if len(trips) != len(trip_ids):
        raise HTTPException(status_code=404, detail="One or more trips not found")
    
    comparison_results = []
    
    for trip in trips:
        # Get actual expenses
        expenses = db.query(models.Expense).filter(models.Expense.trip_id == trip.id).all()
        actual_spent = sum(e.amount for e in expenses)
        
        comparison_results.append({
            "trip_id": trip.id,
            "destination": (trip.destination or trip.custom_destination).name,
            "state": (trip.destination or trip.custom_destination).state,
            "budget": trip.budget,
            "estimated_cost": trip.total_estimated_cost,
            "actual_spent": round(actual_spent, 2),
            "savings": round(trip.budget - actual_spent, 2),
            "days": trip.days,
            "status": trip.status,
            "hotel_tier": trip.hotel_tier,
            "transport_mode": trip.transport_mode,
            "created_at": trip.created_at.isoformat()
        })
    
    return comparison_results
