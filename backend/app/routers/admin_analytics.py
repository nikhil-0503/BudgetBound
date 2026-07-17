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

router = APIRouter(prefix="/api/admin/analytics", tags=["Admin Analytics"])

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
        # Use filtered expenses if available, otherwise 0 spent (no logged expenses in period)
        if t.id in filtered_expense_map:
            actual_spent = sum(filtered_expense_map[t.id])
        else:
            actual_spent = 0.0
        total_savings += max(0.0, t.budget - actual_spent)
    avg_savings = round(total_savings / total_trips, 2) if total_trips > 0 else 0.0
    
    # Comfort level
    avg_comfort = round(sum([t.comfort_score for t in trips]) / total_trips, 1) if total_trips > 0 else 50.0

    # Counter-based metrics
    dest_names = [t.destination.name for t in trips if t.destination]
    categories = [t.destination.category for t in trips if t.destination]
    
    dest_counter = Counter(dest_names)
    cat_counter = Counter(categories)
    
    popular_dest = dest_counter.most_common(1)[0][0] if dest_counter else "—"
    popular_cat = cat_counter.most_common(1)[0][0] if cat_counter else "—"
    
    # Top 10 Destinations
    top_destinations = [{"name": name, "count": count} for name, count in dest_counter.most_common(10)]
    
    # Monthly creation trends — formatted as 'Mon YYYY' for chart readability
    creation_months: dict = {}
    for t in trips:
        m_str = t.created_at.strftime("%Y-%m")
        creation_months[m_str] = creation_months.get(m_str, 0) + 1
    monthly_creation = [
        {"month": datetime.datetime.strptime(m, "%Y-%m").strftime("%b %Y"), "count": creation_months[m]}
        for m in sorted(creation_months.keys())
    ]

    # Monthly expense trends — use filtered expenses only, formatted as 'Mon YYYY'
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
            t.destination.name if t.destination else "—",
            t.destination.category if t.destination else "—",
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
