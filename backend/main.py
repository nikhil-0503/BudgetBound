from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
import os
from dotenv import load_dotenv

# CRITICAL: Load .env BEFORE anything else
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=False)

from app import models, seed, auth
from app.database import engine, get_db
from app.routers import auth as auth_router, destinations, destinations_live, trips, expenses, ai_placeholders, notifications, documents, admin_analytics, trip_comparison, budget_alerts, currency_converter, weather
import os
os.makedirs("uploads", exist_ok=True)

# Setup Logging - Configure root logger to propagate all INFO+ events
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG to see all diagnostics
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("budgetbound.api")

# Explicitly configure app-level loggers
for logger_name in ["app.services", "app.services.gemini", "budgetbound"]:
    app_logger = logging.getLogger(logger_name)
    app_logger.setLevel(logging.DEBUG)  # Changed to DEBUG

# Create tables in Database (if they don't exist)
try:
    models.Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")
    # Schema migration: Add new columns if missing
    from sqlalchemy import text
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE trips ADD COLUMN status VARCHAR DEFAULT 'Planned'"))
            logger.info("Database migration: Added status column.")
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE trips ADD COLUMN start_date VARCHAR"))
            logger.info("Database migration: Added start_date column.")
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE trips ADD COLUMN is_public BOOLEAN DEFAULT 0"))
            logger.info("Database migration: Added is_public column.")
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE trips ADD COLUMN share_token VARCHAR"))
            logger.info("Database migration: Added share_token column.")
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE trips ADD COLUMN custom_destination_id INTEGER REFERENCES custom_destinations(id)"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE custom_destinations ADD COLUMN category VARCHAR"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE custom_destinations ADD COLUMN geoapify_place_id VARCHAR"))
            logger.info("Database migration: Added geoapify_place_id column to custom_destinations.")
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE trips ADD COLUMN geoapify_place_id VARCHAR"))
            logger.info("Database migration: Added geoapify_place_id column to trips.")
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE trips ADD COLUMN data_source VARCHAR"))
            logger.info("Database migration: Added data_source column to trips.")
        except Exception:
            pass
        if engine.dialect.name == "sqlite":
            raw = engine.raw_connection()
            try:
                raw.execute("PRAGMA foreign_keys=OFF")
                cur = raw.cursor()
                create_sql = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='trips'").fetchone()[0]
                if "destination_id INTEGER NOT NULL" in create_sql:
                    indexes = [row[0] for row in cur.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='trips' AND sql IS NOT NULL").fetchall()]
                    columns = [row[1] for row in cur.execute("PRAGMA table_info(trips)").fetchall()]
                    rebuilt = create_sql.replace("CREATE TABLE trips", "CREATE TABLE trips_new", 1).replace("destination_id INTEGER NOT NULL", "destination_id INTEGER", 1)
                    cur.execute("BEGIN")
                    cur.execute(rebuilt)
                    quoted = ", ".join(f'"{column}"' for column in columns)
                    cur.execute(f"INSERT INTO trips_new ({quoted}) SELECT {quoted} FROM trips")
                    cur.execute("DROP TABLE trips")
                    cur.execute("ALTER TABLE trips_new RENAME TO trips")
                    for index_sql in indexes:
                        cur.execute(index_sql)
                    raw.commit()
            except Exception:
                raw.rollback()
                logger.exception("Could not migrate legacy SQLite Trip destination reference")
            finally:
                raw.execute("PRAGMA foreign_keys=ON")
                raw.close()
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS packing_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trip_id INTEGER NOT NULL,
                    name VARCHAR NOT NULL,
                    checked BOOLEAN DEFAULT 0 NOT NULL,
                    FOREIGN KEY(trip_id) REFERENCES trips(id) ON DELETE CASCADE
                )
            """))
            logger.info("Database migration: Created packing_items table.")
        except Exception as ex:
            logger.error(f"Database migration error creating packing_items: {ex}")
            pass
        # User preferences migrations
        for col, default_val in [
            ("photo_url", "VARCHAR"),
            ("default_budget", "FLOAT"),
            ("preferred_travel_style", "VARCHAR"),
            ("preferred_comfort_level", "INTEGER"),
            ("default_starting_city", "VARCHAR"),
            ("preferred_theme", "VARCHAR DEFAULT 'light'"),
            ("is_admin", "BOOLEAN DEFAULT 0")
        ]:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {default_val}"))
                logger.info(f"Database migration: Added user column {col}.")
            except Exception:
                pass
        # Notifications table migration
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type VARCHAR NOT NULL,
                    message VARCHAR NOT NULL,
                    is_read BOOLEAN DEFAULT 0 NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            logger.info("Database migration: Created notifications table.")
        except Exception as ex:
            logger.error(f"Database migration error creating notifications: {ex}")
            pass
        # Travel documents table migration
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS travel_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trip_id INTEGER NOT NULL,
                    category VARCHAR NOT NULL,
                    filename VARCHAR NOT NULL,
                    filepath VARCHAR NOT NULL,
                    filesize INTEGER NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY(trip_id) REFERENCES trips(id) ON DELETE CASCADE
                )
            """))
            logger.info("Database migration: Created travel_documents table.")
        except Exception as ex:
            logger.error(f"Database migration error creating travel_documents: {ex}")
            pass
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
app.include_router(destinations_live.router)  # New live Geoapify destinations
app.include_router(trips.router)
app.include_router(expenses.router)
app.include_router(ai_placeholders.router)
app.include_router(notifications.router)
app.include_router(documents.router)
app.include_router(admin_analytics.router)
app.include_router(trip_comparison.router)
app.include_router(budget_alerts.router)
app.include_router(currency_converter.router)
app.include_router(weather.router)

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
    import datetime

    # Total Trips
    trips_list = db.query(models.Trip).filter(models.Trip.user_id == current_user.id).all()
    
    # Auto-update status for "Planned" and "In Progress" based on dates
    for t in trips_list:
        if not t.status:
            t.status = "Planned"
            db.commit()
            db.refresh(t)

        if t.status in ["Planned", "In Progress"] and t.start_date:
            try:
                start_dt = datetime.datetime.strptime(t.start_date, "%Y-%m-%d").date()
                today = datetime.date.today()
                end_dt = start_dt + datetime.timedelta(days=t.days)
                
                new_status = t.status
                if today >= end_dt:
                    new_status = "Completed"
                elif today >= start_dt:
                    new_status = "In Progress"
                    
                if new_status != t.status:
                    t.status = new_status
                    db.commit()
                    db.refresh(t)
            except Exception:
                pass

    total_trips = len(trips_list)

    # Planned Budget
    planned_budget = sum([t.budget for t in trips_list])
    
    # Actual expenses for all trips
    trip_ids = [t.id for t in trips_list]
    all_expenses = db.query(models.Expense).filter(models.Expense.trip_id.in_(trip_ids)).all() if trip_ids else []
    actual_expenses = sum([e.amount for e in all_expenses])

    # Savings = planned budget - actual expenses
    savings = max(0.0, planned_budget - actual_expenses)

    # Status counts
    trips_planned = len([t for t in trips_list if t.status == "Planned"])
    trips_in_progress = len([t for t in trips_list if t.status == "In Progress"])
    trips_completed = len([t for t in trips_list if t.status == "Completed"])
    trips_cancelled = len([t for t in trips_list if t.status == "Cancelled"])
    trips_draft = len([t for t in trips_list if t.status == "Draft"])

    # Recent Trips (limit 5)
    recent_trips = []
    # Sort trips by created_at desc
    sorted_trips = sorted(trips_list, key=lambda x: x.created_at, reverse=True)[:5]
    for t in sorted_trips:
        # Handle destination - prefer actual destination, then custom destination
        if t.destination:
            dest_name = t.destination.name
            dest_state = t.destination.state
        elif t.custom_destination_id:
            custom_dest = db.query(models.CustomDestination).filter(
                models.CustomDestination.id == t.custom_destination_id
            ).first()
            dest_name = custom_dest.name if custom_dest else "Unknown destination"
            dest_state = custom_dest.address or "" if custom_dest else ""
        else:
            dest_name = "Unknown destination"
            dest_state = ""
        
        recent_trips.append({
            "id": t.id,
            "destination": dest_name,
            "state": dest_state,
            "budget": t.budget,
            "estimated_cost": t.total_estimated_cost,
            "days": t.days,
            "category": t.travel_type,
            "date": t.created_at.strftime("%Y-%m-%d"),
            "status": t.status,
            "start_date": t.start_date
        })

    # Upcoming Trips (limit 5)
    upcoming_raw = [t for t in trips_list if t.status == "Planned"]
    upcoming_trips = []
    sorted_upcoming = sorted(upcoming_raw, key=lambda x: x.start_date or "9999-12-31")[:5]
    for t in sorted_upcoming:
        # Handle destination - prefer actual destination, then custom destination
        if t.destination:
            dest_name = t.destination.name
            dest_state = t.destination.state
        elif t.custom_destination_id:
            custom_dest = db.query(models.CustomDestination).filter(
                models.CustomDestination.id == t.custom_destination_id
            ).first()
            dest_name = custom_dest.name if custom_dest else "Unknown destination"
            dest_state = custom_dest.address or "" if custom_dest else ""
        else:
            dest_name = "Unknown destination"
            dest_state = ""
        
        upcoming_trips.append({
            "id": t.id,
            "destination": dest_name,
            "state": dest_state,
            "budget": t.budget,
            "estimated_cost": t.total_estimated_cost,
            "days": t.days,
            "category": t.travel_type,
            "status": t.status,
            "start_date": t.start_date
        })

    # Chart 1: Budget Usage (Compare Budget vs Estimated vs Actual for each trip)
    budget_usage_chart = []
    for t in sorted(trips_list, key=lambda x: x.created_at)[:6]: # oldest to newest (limit 6)
        trip_expenses = [e.amount for e in all_expenses if e.trip_id == t.id]
        
        # Handle destination - prefer actual destination, then custom destination
        if t.destination:
            chart_name = t.destination.name
        elif t.custom_destination_id:
            custom_dest = db.query(models.CustomDestination).filter(
                models.CustomDestination.id == t.custom_destination_id
            ).first()
            chart_name = custom_dest.name if custom_dest else "Unknown destination"
        else:
            chart_name = "Unknown destination"
        
        budget_usage_chart.append({
            "name": chart_name,
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
        "trips_planned": trips_planned,
        "trips_in_progress": trips_in_progress,
        "trips_completed": trips_completed,
        "trips_cancelled": trips_cancelled,
        "trips_draft": trips_draft,
        "recent_trips": recent_trips,
        "upcoming_trips": upcoming_trips,
        "budget_usage_chart": budget_usage_chart,
        "category_chart": category_chart
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
