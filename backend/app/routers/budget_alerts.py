"""
Budget Alerts System - Real-time budget monitoring and alerts
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app import models, auth
from app.database import get_db

router = APIRouter(prefix="/api/budget-alerts", tags=["Budget Alerts"])


@router.get("/trip/{trip_id}", response_model=Dict[str, Any])
def get_trip_budget_alerts(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get budget alerts and warnings for a specific trip
    """
    
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Get expenses
    expenses = db.query(models.Expense).filter(models.Expense.trip_id == trip_id).all()
    
    # Calculate by category
    category_spending = {
        "Transport": 0.0,
        "Hotel": 0.0,
        "Food": 0.0,
        "Activities": 0.0,
        "Shopping": 0.0,
        "Other": 0.0
    }
    
    for expense in expenses:
        cat = expense.category if expense.category in category_spending else "Other"
        category_spending[cat] += expense.amount
    
    total_spent = sum(category_spending.values())
    
    # Get budget allocation
    alloc = trip.budget_allocation
    
    alerts = []
    warnings = []
    tips = []
    
    # Overall budget check
    budget_used_pct = (total_spent / trip.budget) * 100 if trip.budget > 0 else 0
    
    if budget_used_pct > 100:
        alerts.append({
            "type": "critical",
            "category": "Overall Budget",
            "message": f"You've exceeded your budget by ₹{round(total_spent - trip.budget, 2)}",
            "percentage": round(budget_used_pct, 1)
        })
    elif budget_used_pct > 90:
        alerts.append({
            "type": "warning",
            "category": "Overall Budget",
            "message": f"You've used {round(budget_used_pct, 1)}% of your budget",
            "percentage": round(budget_used_pct, 1)
        })
    elif budget_used_pct > 75:
        warnings.append({
            "type": "caution",
            "category": "Overall Budget",
            "message": f"You've used {round(budget_used_pct, 1)}% of your budget",
            "percentage": round(budget_used_pct, 1)
        })
    
    # Category-wise alerts
    if alloc:
        category_limits = {
            "Transport": alloc.transport_cost + alloc.local_transport_cost,
            "Hotel": alloc.hotel_cost,
            "Food": alloc.food_cost,
            "Activities": alloc.activities_cost,
            "Other": alloc.taxes_fees_cost + alloc.emergency_reserve
        }
        
        for category, limit in category_limits.items():
            spent = category_spending.get(category, 0)
            if limit > 0:
                pct = (spent / limit) * 100
                
                if pct > 100:
                    alerts.append({
                        "type": "critical",
                        "category": category,
                        "message": f"{category} budget exceeded by ₹{round(spent - limit, 2)}",
                        "percentage": round(pct, 1),
                        "spent": spent,
                        "limit": limit
                    })
                elif pct > 90:
                    warnings.append({
                        "type": "warning",
                        "category": category,
                        "message": f"{category} budget {round(pct, 1)}% used",
                        "percentage": round(pct, 1),
                        "spent": spent,
                        "limit": limit
                    })
    
    # Generate savings tips
    if len(expenses) > 0:
        # Calculate daily burn rate
        expense_dates = [datetime.strptime(e.date, "%Y-%m-%d") for e in expenses]
        days_active = len(set(e.date for e in expenses))
        
        if days_active > 0:
            daily_avg = total_spent / days_active
            
            if daily_avg > (trip.budget / trip.days) * 1.2:
                tips.append({
                    "type": "saving",
                    "message": f"Your daily spending (₹{round(daily_avg, 2)}) is higher than planned. Consider budget meals.",
                    "impact": "high"
                })
        
        # Check for expensive categories
        if category_spending["Shopping"] > trip.budget * 0.2:
            tips.append({
                "type": "saving",
                "message": "Shopping expenses are high. Stick to planned souvenirs only.",
                "impact": "medium"
            })
        
        if category_spending["Food"] > trip.budget * 0.3:
            tips.append({
                "type": "saving",
                "message": "Food costs are high. Try local eateries instead of restaurants.",
                "impact": "medium"
            })
    
    # Positive feedback
    if budget_used_pct < 75 and len(expenses) > 5:
        tips.append({
            "type": "positive",
            "message": "Great job! You're staying well within budget!",
            "impact": "info"
        })
    
    return {
        "trip_id": trip_id,
        "destination": trip.destination.name,
        "budget": trip.budget,
        "total_spent": round(total_spent, 2),
        "remaining_budget": round(trip.budget - total_spent, 2),
        "budget_used_percentage": round(budget_used_pct, 1),
        "status": "critical" if budget_used_pct > 100 else "warning" if budget_used_pct > 90 else "good",
        "alerts": alerts,
        "warnings": warnings,
        "tips": tips,
        "category_spending": {k: round(v, 2) for k, v in category_spending.items()}
    }


@router.get("/user/summary", response_model=Dict[str, Any])
def get_user_budget_summary(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get overall budget summary for all user trips
    """
    
    trips = db.query(models.Trip).filter(
        models.Trip.user_id == current_user.id,
        models.Trip.status.in_(["Planned", "In Progress"])
    ).all()
    
    total_budget = sum(t.budget for t in trips)
    total_estimated = sum(t.total_estimated_cost for t in trips)
    
    trips_over_budget = 0
    trips_at_risk = 0
    
    for trip in trips:
        expenses = db.query(models.Expense).filter(models.Expense.trip_id == trip.id).all()
        spent = sum(e.amount for e in expenses)
        
        if spent > trip.budget:
            trips_over_budget += 1
        elif spent > trip.budget * 0.9:
            trips_at_risk += 1
    
    return {
        "total_trips": len(trips),
        "total_budget_allocated": round(total_budget, 2),
        "total_estimated_cost": round(total_estimated, 2),
        "trips_over_budget": trips_over_budget,
        "trips_at_risk": trips_at_risk,
        "overall_status": "critical" if trips_over_budget > 0 else "warning" if trips_at_risk > 0 else "good"
    }


@router.post("/set-limit", response_model=Dict[str, Any])
def set_spending_limit(
    trip_id: int,
    category: str,
    limit: float,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set custom spending limit for a category
    """
    
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if not trip.budget_allocation:
        raise HTTPException(status_code=400, detail="Trip has no budget allocation")
    
    alloc = trip.budget_allocation
    
    # Update the allocation
    if category == "Transport":
        alloc.transport_cost = limit
    elif category == "Hotel":
        alloc.hotel_cost = limit
    elif category == "Food":
        alloc.food_cost = limit
    elif category == "Activities":
        alloc.activities_cost = limit
    else:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    db.commit()
    
    return {
        "trip_id": trip_id,
        "category": category,
        "new_limit": limit,
        "message": f"{category} limit updated successfully"
    }
