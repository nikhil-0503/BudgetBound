from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging

from app import models, seed, auth
from app.database import engine, get_db
from app.routers import auth as auth_router, destinations, trips, expenses, ai_placeholders

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("budgetbound.api")

# Create tables in Database (if they don't exist)
try:
    models.Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")
except Exception as e:
    logger.error(f"Error initializing database tables: {e}")

# Seed destinations automatically on startup
db_session = next(get_db())
try:
    seed.seed_destinations(db_session)
finally:
    db_session.close()

app = FastAPI(
    title="BudgetBound API",
    description="Backend API for the budget-first travel planning platform",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router.router)
app.include_router(destinations.router)
app.include_router(trips.router)
app.include_router(expenses.router)
app.include_router(ai_placeholders.router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Welcome to the BudgetBound API",
        "version": "1.0.0"
    }

@app.get("/api/dashboard/stats")
def get_dashboard_stats(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Total Trips
    trips_list = db.query(models.Trip).filter(models.Trip.user_id == current_user.id).all()
    total_trips = len(trips_list)

    # Planned Budget
    planned_budget = sum([t.budget for t in trips_list])
    
    # Actual expenses for all trips
    trip_ids = [t.id for t in trips_list]
    all_expenses = db.query(models.Expense).filter(models.Expense.trip_id.in_(trip_ids)).all() if trip_ids else []
    actual_expenses = sum([e.amount for e in all_expenses])

    # Estimated expenses (total_estimated_cost of all trips)
    total_estimated = sum([t.total_estimated_cost for t in trips_list])

    # Savings = planned budget - actual expenses (for trips that have expenses, or budget - estimated if no expenses yet)
    # Let's define overall savings as: (Sum of budgets for all trips) - (Sum of actual expenses for categories logged + Estimated remaining)
    # For simplicity of display: Planned Budget - Actual Expenses
    savings = max(0.0, planned_budget - actual_expenses)

    # Recent Trips (limit 5)
    # We want to format them for easy display
    recent_trips = []
    # Sort trips by created_at desc
    sorted_trips = sorted(trips_list, key=lambda x: x.created_at, reverse=True)[:5]
    for t in sorted_trips:
        recent_trips.append({
            "id": t.id,
            "destination": t.destination.name,
            "state": t.destination.state,
            "budget": t.budget,
            "estimated_cost": t.total_estimated_cost,
            "days": t.days,
            "category": t.travel_type,
            "date": t.created_at.strftime("%Y-%m-%d")
        })

    # Chart 1: Budget Usage (Compare Budget vs Estimated vs Actual for each trip)
    budget_usage_chart = []
    for t in sorted(trips_list, key=lambda x: x.created_at)[:6]: # oldest to newest (limit 6)
        trip_expenses = [e.amount for e in all_expenses if e.trip_id == t.id]
        budget_usage_chart.append({
            "name": t.destination.name,
            "budget": t.budget,
            "estimated": t.total_estimated_cost,
            "actual": sum(trip_expenses)
        })

    # Chart 2: Expense Categories distribution across all trips
    expense_categories = {
        "Transport": 0.0,
        "Hotel": 0.0,
        "Food": 0.0,
        "Activities": 0.0,
        "Shopping": 0.0,
        "Other": 0.0
    }
    for e in all_expenses:
        cat = e.category
        if cat in expense_categories:
            expense_categories[cat] += e.amount
        else:
            expense_categories["Other"] += e.amount

    category_chart = [
        {"name": k, "value": round(v, 2)} for k, v in expense_categories.items() if v > 0
    ]
    # If empty, add placeholder values for chart aesthetic
    if not category_chart:
        category_chart = [
            {"name": "Transport", "value": 0.0},
            {"name": "Hotel", "value": 0.0},
            {"name": "Food", "value": 0.0},
            {"name": "Activities", "value": 0.0},
            {"name": "Shopping", "value": 0.0},
            {"name": "Other", "value": 0.0}
        ]

    return {
        "total_trips": total_trips,
        "planned_budget": round(planned_budget, 2),
        "actual_expenses": round(actual_expenses, 2),
        "savings": round(savings, 2),
        "recent_trips": recent_trips,
        "budget_usage_chart": budget_usage_chart,
        "category_chart": category_chart
    }
