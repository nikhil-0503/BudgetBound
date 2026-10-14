from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter
import csv
import io
from typing import List

from app import models, schemas, auth
from app.database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin/analytics", tags=["Admin Analytics"])

class PasswordReset(BaseModel):
    user_id: int
    new_password: str

def get_current_admin(current_user: models.User = Depends(auth.get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required."
        )
    return current_user

@router.get("/")
def get_admin_analytics(
    time_filter: str = "all",
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    # Fetch all data for in-memory analytics
    users = db.query(models.User).all()
    trips = db.query(models.Trip).all()
    expenses = db.query(models.Expense).all()
    
    import datetime
    now = datetime.datetime.utcnow()
    if time_filter == "30days":
        cutoff = now - datetime.timedelta(days=30)
        trips = [t for t in trips if t.created_at >= cutoff]
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        expenses = [e for e in expenses if e.date >= cutoff_str]
    elif time_filter == "6months":
        cutoff = now - datetime.timedelta(days=180)
        trips = [t for t in trips if t.created_at >= cutoff]
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        expenses = [e for e in expenses if e.date >= cutoff_str]
        
    total_users = len(users)
    total_trips = len(trips)
    
    completed_trips = sum([1 for t in trips if t.status == "Completed"])
    total_budget = sum([t.budget for t in trips])
    avg_budget = round(total_budget / total_trips, 2) if total_trips > 0 else 0.0
    
    # Build a lookup of filtered expenses by trip_id for consistent date-scoped savings
    filtered_expense_map: dict = {}
    for e in expenses:
        filtered_expense_map.setdefault(e.trip_id, []).append(e.amount)
    
    # avg_savings: use only the filtered expenses for trips in the filtered set
    trip_ids_in_scope = {t.id for t in trips}
    total_savings = 0.0
    for t in trips:
        # Savings = projected savings if you stick to estimated cost
        total_savings += max(0.0, t.budget - t.total_estimated_cost)
    avg_savings = round(total_savings / total_trips, 2) if total_trips > 0 else 0.0
    
    # Comfort level
    avg_comfort = round(sum([t.comfort_score for t in trips]) / total_trips, 1) if total_trips > 0 else 50.0

    # Counter-based metrics
    dest_names = [t.destination.name for t in trips if t.destination]
    categories = [t.destination.category for t in trips if t.destination]
    
    dest_counter = Counter(dest_names)
    cat_counter = Counter(categories)
    
    popular_dest = dest_counter.most_common(1)[0][0] if dest_counter else "-"
    popular_cat = cat_counter.most_common(1)[0][0] if cat_counter else "-"
    
    # Top 10 Destinations
    top_destinations = [{"name": name, "count": count} for name, count in dest_counter.most_common(10)]
    
    # Monthly creation trends - formatted as 'Mon YYYY' for chart readability
    creation_months: dict = {}
    for t in trips:
        m_str = t.created_at.strftime("%Y-%m")
        creation_months[m_str] = creation_months.get(m_str, 0) + 1
    monthly_creation = [
        {"month": datetime.datetime.strptime(m, "%Y-%m").strftime("%b %Y"), "count": creation_months[m]}
        for m in sorted(creation_months.keys())
    ]

    # Monthly expense trends - use filtered expenses only, formatted as 'Mon YYYY'
    expense_months: dict = {}
    for e in expenses:
        try:
            m_str = e.date[:7]  # YYYY-MM
            expense_months[m_str] = expense_months.get(m_str, 0.0) + e.amount
        except Exception:
            pass
    monthly_expenses = [
        {"month": datetime.datetime.strptime(m, "%Y-%m").strftime("%b %Y"), "amount": round(expense_months[m], 2)}
        for m in sorted(expense_months.keys())
    ]

    return {
        "total_users": total_users,
        "total_trips": total_trips,
        "completed_trips": completed_trips,
        "avg_budget": avg_budget,
        "avg_savings": avg_savings,
        "popular_destination": popular_dest,
        "popular_category": popular_cat,
        "avg_comfort": avg_comfort,
        "top_destinations": top_destinations,
        "monthly_creation": monthly_creation,
        "monthly_expenses": monthly_expenses
    }

@router.get("/users-login-details")
def get_users_login_details(
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get login details of all users. Admin only."""
    users = db.query(models.User).all()
    
    user_details = []
    for user in users:
        trip_count = db.query(models.Trip).filter(models.Trip.user_id == user.id).count()
        user_details.append({
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else None,
            "is_admin": user.is_admin,
            "trips_count": trip_count,
            "photo_url": user.photo_url,
            "preferred_theme": user.preferred_theme,
            "default_budget": user.default_budget
        })
    
    return {
        "total_users": len(user_details),
        "users": user_details
    }

@router.post("/reset-user-password")
def reset_user_password(
    password_reset: PasswordReset,
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin can reset a user's password to a new value."""
    user = db.query(models.User).filter(models.User.id == password_reset.user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    
    # Prevent admin from resetting their own password via this endpoint
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reset your own password via admin endpoint. Use profile update instead."
        )
    
    # Hash and update password
    hashed_password = auth.get_password_hash(password_reset.new_password)
    user.hashed_password = hashed_password
    db.commit()
    db.refresh(user)
    
    return {
        "message": f"Password reset successfully for user {user.email}",
        "user_id": user.id,
        "email": user.email
    }

@router.get("/export-csv")
def export_trips_csv(
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    trips = db.query(models.Trip).all()
    
    # Generate CSV stream
    f = io.StringIO()
    writer = csv.writer(f)
    writer.writerow([
        "Trip ID", "User ID", "User Name", "User Email", 
        "Destination Name", "Destination Category", "Budget (INR)", 
        "Days", "Travelers Count", "Transport Mode", "Hotel Tier", "Status", "Created At"
    ])
    
    for t in trips:
        writer.writerow([
            t.id, t.user_id, t.user.name, t.user.email,
            t.destination.name if t.destination else "-",
            t.destination.category if t.destination else "-",
            t.budget, t.days, t.travelers_count, t.transport_mode, t.hotel_tier, t.status,
            t.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])
    
    f.seek(0)
    csv_bytes = f.read().encode("utf-8")
    
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=budgetbound_global_trips_report.csv"}
    )
