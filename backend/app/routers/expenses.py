from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app import models, schemas, auth
from app.database import get_db

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])

@router.post("/", response_model=schemas.ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    trip_id: int,
    expense_in: schemas.ExpenseCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Verify trip belongs to user
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    db_expense = models.Expense(
        trip_id=trip_id,
        date=expense_in.date,
        category=expense_in.category,
        amount=expense_in.amount,
        notes=expense_in.notes
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    
    # Check overspending limits
    check_expense_limit_and_notify(trip, expense_in.category, db)
    return db_expense

def check_expense_limit_and_notify(trip: models.Trip, category: str, db: Session):
    alloc = trip.budget_allocation
    if not alloc:
        return
        
    category_map = {
        "Transport": alloc.transport_cost + alloc.local_transport_cost,
        "Hotel": alloc.hotel_cost,
        "Food": alloc.food_cost,
        "Activities": alloc.activities_cost,
        "Other": alloc.taxes_fees_cost + alloc.emergency_reserve
    }
    
    allocated_limit = category_map.get(category)
    if allocated_limit is None or allocated_limit <= 0:
        return
        
    # Get total spent in this category
    total_spent = sum([e.amount for e in trip.expenses if e.category == category])
    
    if total_spent > allocated_limit:
        message = f"You have exceeded your {category} budget of ₹{allocated_limit:.2f} for your trip to {trip.destination.name}. Total spent: ₹{total_spent:.2f}."
        exists = db.query(models.Notification).filter(
            models.Notification.user_id == trip.user_id,
            models.Notification.message == message
        ).first()
        if not exists:
            db_notif = models.Notification(
                user_id=trip.user_id,
                type="Overspending Alert",
                message=message
            )
            db.add(db_notif)
            db.commit()
    elif total_spent > (allocated_limit * 0.90):
        message = f"You are approaching your {category} budget limit (₹{allocated_limit:.2f}) for your trip to {trip.destination.name}. Current spending: ₹{total_spent:.2f}."
        exists = db.query(models.Notification).filter(
            models.Notification.user_id == trip.user_id,
            models.Notification.message == message
        ).first()
        if not exists:
            db_notif = models.Notification(
                user_id=trip.user_id,
                type="Budget Warning",
                message=message
            )
            db.add(db_notif)
            db.commit()

@router.get("/trip/{trip_id}", response_model=List[schemas.ExpenseOut])
def get_trip_expenses(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Verify trip belongs to user
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return db.query(models.Expense).filter(models.Expense.trip_id == trip_id).all()

@router.put("/{expense_id}", response_model=schemas.ExpenseOut)
def update_expense(
    expense_id: int,
    expense_in: schemas.ExpenseCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    # Verify ownership through the trip relation
    trip = db.query(models.Trip).filter(
        models.Trip.id == db_expense.trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db_expense.date = expense_in.date
    db_expense.category = expense_in.category
    db_expense.amount = expense_in.amount
    db_expense.notes = expense_in.notes
    
    db.commit()
    db.refresh(db_expense)
    
    # Check limits
    check_expense_limit_and_notify(trip, expense_in.category, db)
    return db_expense

@router.delete("/{expense_id}", status_code=204)
def delete_expense(
    expense_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    trip = db.query(models.Trip).filter(
        models.Trip.id == db_expense.trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(db_expense)
    db.commit()
    return None

@router.get("/trip/{trip_id}/stats")
def get_expense_stats(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Verify trip
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    alloc = trip.budget_allocation
    expenses = db.query(models.Expense).filter(models.Expense.trip_id == trip_id).all()

    # Sum of actual expenses by category
    actuals = {
        "Transport": 0.0,
        "Hotel": 0.0,
        "Food": 0.0,
        "Activities": 0.0,
        "Shopping": 0.0,
        "Other": 0.0
    }
    for exp in expenses:
        cat = exp.category
        if cat not in actuals:
            cat = "Other"
        actuals[cat] += exp.amount

    # Map estimated budget allocations
    # Note: Transport in estimate includes long-distance transport and local transport
    estimates = {
        "Transport": alloc.transport_cost + alloc.local_transport_cost if alloc else 0.0,
        "Hotel": alloc.hotel_cost if alloc else 0.0,
        "Food": alloc.food_cost if alloc else 0.0,
        "Activities": alloc.activities_cost if alloc else 0.0,
        "Shopping": 0.0, # default 0 estimate for shopping
        "Other": alloc.taxes_fees_cost + alloc.emergency_reserve if alloc else 0.0
    }

    # Combined stats formatted for charts
    chart_data = []
    for cat in ["Transport", "Hotel", "Food", "Activities", "Shopping", "Other"]:
        chart_data.append({
            "category": cat,
            "estimated": round(estimates[cat], 2),
            "actual": round(actuals[cat], 2),
            "difference": round(estimates[cat] - actuals[cat], 2)
        })

    total_estimated = sum(estimates.values())
    total_actual = sum(actuals.values())
    savings = round(total_estimated - total_actual, 2)

    # Predictions
    unique_dates = set(exp.date for exp in expenses)
    active_days = len(unique_dates)
    burn_rate = total_actual / active_days if active_days > 0 else 0.0

    if active_days == 0:
        projected_final_spend = trip.total_estimated_cost
    else:
        remaining_days = max(0, trip.days - active_days)
        projected_final_spend = total_actual + (remaining_days * burn_rate)

    if projected_final_spend <= trip.budget:
        prediction_status = "Likely to stay within budget"
    else:
        prediction_status = "Potential overspend"

    return {
        "total_estimated": round(total_estimated, 2),
        "total_actual": round(total_actual, 2),
        "savings": savings,
        "categories": chart_data,
        "remaining_budget": round(trip.budget - total_actual, 2),
        "daily_burn_rate": round(burn_rate, 2),
        "projected_final_spend": round(projected_final_spend, 2),
        "prediction_status": prediction_status,
        "estimated_overspend": round(max(0.0, projected_final_spend - trip.budget), 2),
        "estimated_savings": round(max(0.0, trip.budget - projected_final_spend), 2),
        "budget": trip.budget,
        "days": trip.days
    }
