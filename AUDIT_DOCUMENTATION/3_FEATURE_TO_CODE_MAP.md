# BudgetBound: Feature-to-Code Dependency Map

**Document:** 3_FEATURE_TO_CODE_MAP.md  
**Created:** October 2026  
**Purpose:** Complete code tracing for all 18 BudgetBound features, mapping UI → API → backend → database  
**Status:** Reference for implementation verification and viva preparation

---

## Table of Contents

1. [Trip Planning Features](#trip-planning-features)
2. [User Management Features](#user-management-features)
3. [AI & Intelligence Features](#ai--intelligence-features)
4. [Analytics & Admin Features](#analytics--admin-features)
5. [Code Dependency Graph](#code-dependency-graph)

---

## Trip Planning Features

### Feature 1: Interactive Trip Planner

**Description:** Multi-step wizard for creating trips with destinations, dates, budget, travelers, and itineraries.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/pages/TripPlanner.tsx`
- `frontend/src/components/TripWizard.tsx` (multi-step form)

**API Endpoints:**
- `POST /api/trips` → Create trip
- `GET /api/trips/{trip_id}` → Retrieve trip
- `PUT /api/trips/{trip_id}` → Update trip
- `GET /api/trips` → List user trips

**Backend Router:**
- `backend/app/routers/trips.py` (lines 1–150)
  - `create_trip()` → Validates input, calls database layer
  - `update_trip()` → Updates trip fields
  - `get_trip()` → Retrieves single trip
  - `list_trips()` → Returns paginated user trips

**Database Models:**
- `backend/app/models.py`
  - `Trip` model (lines 120–180)
    - Fields: `id`, `user_id`, `name`, `description`, `start_date`, `end_date`, `budget`, `currency`, `traveler_count`, `destination_id`, `created_at`, `updated_at`
  - `Itinerary` model (lines 320–370)
    - Fields: `id`, `trip_id`, `day`, `activity`, `cost`, `location`

**Database Layer:**
- `backend/app/database.py`
  - `create_trip(db, user_id, trip_data)` → Inserts Trip record
  - `get_trip(db, trip_id)` → Fetches Trip + related Itineraries
  - `update_trip(db, trip_id, updates)` → Commits updates

**Key Logic:**
- Validates date ranges (start ≤ end)
- Validates budget ≥ 0
- Validates traveler_count ≥ 1
- Cascades to Itinerary creation

---

### Feature 2: Budget Optimizer (Algorithm)

**Description:** ML-backed optimization to redistribute budget across expense categories while respecting constraints.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/pages/BudgetOptimizer.tsx`
- `frontend/src/components/OptimizerPanel.tsx` (UI controls)

**API Endpoints:**
- `POST /api/trips/{trip_id}/optimize` → Run optimization

**Backend Router:**
- `backend/app/routers/trips.py` (lines 200–280)
  - `optimize_budget()` → Orchestrates optimization, calls service layer

**Backend Service Layer:**
- `backend/app/services/multistop_calculator.py` (lines 1–200)
  - `calculate_optimized_budget()` → Core optimization algorithm
    - Linear programming model using constraints
    - Objective: Minimize deviation from user preferences
    - Returns: Optimized allocation dict

**Algorithm Details:**
```
Input: expenses[], budget, preferences[]
Constraints:
  - sum(optimized_expenses) = budget
  - each category ≥ lower_bound
  - each category ≤ upper_bound
  - food_budget > 0
  - accommodation_budget > 0
Optimization:
  - Minimize: Σ(preference_weight[i] * deviation[i])
  - Deviation[i] = |original[i] - optimized[i]| / max(1, original[i])
Output: optimized_allocation[], explanation[]
```

**Database Models:**
- `backend/app/models.py`
  - `Expense` model (lines 400–450)
    - Fields: `id`, `trip_id`, `category`, `amount`, `date`, `notes`

**Key Logic:**
- Fetches all trip expenses
- Groups by category (accommodation, food, transport, activities, misc)
- Runs linear solver (SciPy)
- Validates feasibility (budget ≥ minimum requirements)
- Generates human-readable explanation

---

### Feature 3: Expense Tracker

**Description:** Record, categorize, and track trip expenses with real-time budget alerts.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/pages/ExpenseTracker.tsx`
- `frontend/src/components/ExpenseForm.tsx` (add/edit)
- `frontend/src/components/ExpenseList.tsx` (view)

**API Endpoints:**
- `POST /api/trips/{trip_id}/expenses` → Add expense
- `GET /api/trips/{trip_id}/expenses` → List expenses
- `PUT /api/trips/{trip_id}/expenses/{expense_id}` → Edit expense
- `DELETE /api/trips/{trip_id}/expenses/{expense_id}` → Delete expense
- `GET /api/trips/{trip_id}/expenses/summary` → Category breakdown

**Backend Router:**
- `backend/app/routers/expenses.py` (lines 1–250)
  - `create_expense()` → Validates, saves, triggers alert check
  - `get_expenses()` → Returns paginated list with category filter
  - `update_expense()` → Modifies expense, re-runs alerts
  - `delete_expense()` → Removes expense
  - `get_expense_summary()` → Aggregates by category, calculates %spent

**Backend Service Layer:**
- `backend/app/services/financial_validator.py` (lines 50–150)
  - `validate_expense()` → Checks category, amount ≥ 0, date validity
  - `get_category_breakdown()` → Groups expenses, calculates totals

**Database Models:**
- `backend/app/models.py`
  - `Expense` model (lines 400–450)
    - Enum Categories: ACCOMMODATION, FOOD, TRANSPORT, ACTIVITIES, MISC
    - Fields: `id`, `trip_id`, `category`, `amount`, `currency`, `date`, `notes`, `created_at`

**Database Layer:**
- `backend/app/database.py`
  - `add_expense(db, trip_id, expense_data)` → Inserts Expense
  - `get_expenses(db, trip_id, category_filter)` → Fetches with WHERE clauses
  - `delete_expense(db, expense_id)` → Removes record

**Key Logic:**
- Validates category in enum
- Validates amount > 0
- Validates date ≤ today
- Cascades to Budget Alert trigger (see Feature 4)

---

### Feature 4: Budget Alerts (Real-Time)

**Description:** Push/email alerts when spending approaches or exceeds category/total limits.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/components/AlertNotification.tsx` (toast UI)
- `frontend/src/pages/AlertSettings.tsx` (threshold config)

**API Endpoints:**
- `GET /api/trips/{trip_id}/budget-alerts` → List alert thresholds
- `POST /api/trips/{trip_id}/budget-alerts` → Set threshold
- `PUT /api/trips/{trip_id}/budget-alerts/{alert_id}` → Edit threshold
- `DELETE /api/trips/{trip_id}/budget-alerts/{alert_id}` → Remove threshold

**Backend Router:**
- `backend/app/routers/budget_alerts.py` (lines 1–200)
  - `create_alert_threshold()` → Validates, saves threshold
  - `check_alert_condition()` → Triggered by expense creation
  - `get_alert_history()` → Returns past alerts
  - `send_alert()` → Orchestrates notification

**Backend Service Layer:**
- `backend/app/services/financial_validator.py` (lines 150–250)
  - `evaluate_budget_alert()` → Compares current spend vs threshold
    - If (current_spend / budget) ≥ threshold → trigger alert
    - If current_spend > budget → trigger "over budget" alert

**Notification Service:**
- `backend/app/routers/notifications.py` (lines 1–150)
  - `send_notification()` → Dispatches to email/push
  - Email template: `backend/templates/budget_alert_email.txt`

**Database Models:**
- `backend/app/models.py`
  - `BudgetAlert` model (lines 550–600)
    - Fields: `id`, `trip_id`, `user_id`, `category`, `threshold_percentage`, `is_triggered`, `created_at`
  - `Notification` model (lines 750–800)
    - Fields: `id`, `user_id`, `type`, `message`, `read`, `created_at`

**Key Logic:**
- Stores thresholds as percentage (0–100)
- Checks on every expense creation/update
- Prevents duplicate alerts (per threshold per hour)
- Supports category-level + trip-level thresholds

---

### Feature 5: Trip Comparison

**Description:** Side-by-side cost analysis of multiple trips with breakdown by category.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/pages/TripComparison.tsx`
- `frontend/src/components/ComparisonChart.tsx` (visual breakdown)

**API Endpoints:**
- `POST /api/trips/compare` → Compare multiple trips
- `GET /api/trips/compare/{comparison_id}` → Retrieve saved comparison

**Backend Router:**
- `backend/app/routers/trip_comparison.py` (lines 1–200)
  - `compare_trips()` → Accepts trip IDs, returns structured comparison
  - `save_comparison()` → Stores comparison result
  - `get_comparison()` → Retrieves comparison

**Backend Service Layer:**
- `backend/app/services/multistop_calculator.py` (lines 300–400)
  - `compare_trip_costs()` → Aggregates expenses per trip, calculates metrics
    - Cost per person
    - Cost per day
    - Category breakdown
    - Total variance

**Database Models:**
- `backend/app/models.py`
  - `TripComparison` model (lines 650–700)
    - Fields: `id`, `user_id`, `trip_ids` (JSON array), `results` (JSON), `created_at`

**Key Logic:**
- Fetches all expenses for each trip
- Groups by category
- Calculates per-person, per-day metrics
- Identifies most/least expensive categories
- Generates variance analysis

---

### Feature 6: Destination Explorer

**Description:** Browse curated destination database with pre-filled budget estimates and activity recommendations.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/pages/DestinationExplorer.tsx`
- `frontend/src/components/DestinationCard.tsx` (browsable items)
- `frontend/src/components/DestinationFilters.tsx` (search/filter)

**API Endpoints:**
- `GET /api/destinations` → List destinations with filters
- `GET /api/destinations/{destination_id}` → Get destination details
- `GET /api/destinations/search` → Full-text search

**Backend Router:**
- `backend/app/routers/destinations.py` (lines 1–250)
  - `list_destinations()` → Returns paginated list with filters (budget_range, continent, climate, culture)
  - `get_destination()` → Returns full destination profile
  - `search_destinations()` → Full-text search on name, description, tags

**Backend Service Layer:**
- `backend/app/services/destination_database.py` (lines 1–300)
  - `load_destination_database()` → Reads/caches destination data (CSV or DB)
  - `calculate_estimate_budget()` → Estimates 7-day trip cost
    - Formula: base_cost + (travelers-1)*per_person_discount
  - `get_recommended_activities()` → Returns activity suggestions
  - `get_best_time_to_visit()` → Returns climate/weather info

**Database Models:**
- `backend/app/models.py`
  - `Destination` model (lines 850–950)
    - Fields: `id`, `name`, `country`, `continent`, `description`, `latitude`, `longitude`, `base_budget_estimate`, `currency`, `best_months`, `climate`, `languages`, `created_at`
  - `Activity` model (lines 1050–1100)
    - Fields: `id`, `destination_id`, `name`, `cost_estimate`, `duration_hours`, `category` (hiking, cultural, food, water, etc.)

**Database Layer:**
- `backend/app/database.py`
  - `get_destination(db, destination_id)` → Fetches destination + activities
  - `search_destinations(db, query)` → Full-text search
  - `filter_destinations(db, budget_range, continent, climate)` → WHERE clause filtering

**Key Logic:**
- Pre-populated destination data (50+ destinations)
- Budget estimates based on traveler count
- Seasonal recommendations
- Activity categorization
- Search via name, country, continent

---

### Feature 7: Weather & Climate Data

**Description:** Display historical/forecast weather for trip destinations; integrate with trip dates.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/components/WeatherWidget.tsx` (trip planner sidebar)
- `frontend/src/pages/DestinationExplorer.tsx` (destination detail)

**API Endpoints:**
- `GET /api/destinations/{destination_id}/weather` → Get weather data

**Backend Router:**
- `backend/app/routers/destinations.py` (lines 250–350)
  - `get_weather()` → Calls weather service

**Backend Service Layer:**
- `backend/app/services/destination_database.py` (lines 300–400)
  - `fetch_weather_data()` → Integrates with OpenWeatherMap API (cached for 24h)
  - `get_packing_suggestions()` → Generates packing list based on weather
    - Rain: raincoat, umbrella
    - Cold: jacket, boots
    - Hot: sunscreen, hat, light clothing
    - Tropical: insect repellent, quick-dry clothing

**External APIs:**
- OpenWeatherMap API: `https://api.openweathermap.org/data/2.5/weather`
  - Cached locally to avoid rate limits
  - Returns: temp, feels_like, humidity, wind_speed, precipitation, cloudiness

**Database Models:**
- `backend/app/models.py`
  - `WeatherCache` model (lines 1150–1180)
    - Fields: `id`, `destination_id`, `weather_json`, `timestamp` (auto-refresh after 24h)

**Key Logic:**
- Fetches OpenWeatherMap data for destination coordinates
- Caches response for 24 hours
- Matches trip dates to historical climate norms
- Generates packing checklist from weather conditions

---

### Feature 8: Carbon Footprint Calculator

**Description:** Estimates CO₂ emissions for trip transportation and provides carbon offset recommendations.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/components/CarbonFootprintWidget.tsx` (trip planner)
- `frontend/src/pages/EnvironmentalImpact.tsx` (detailed report)

**API Endpoints:**
- `POST /api/trips/{trip_id}/carbon-footprint` → Calculate emissions
- `GET /api/trips/{trip_id}/carbon-footprint` → Retrieve calculation

**Backend Router:**
- `backend/app/routers/trips.py` (lines 350–450)
  - `calculate_carbon_footprint()` → Calls carbon service

**Backend Service Layer:**
- `backend/app/services/multistop_calculator.py` (lines 500–600)
  - `estimate_co2_emissions()` → Calculates by transport mode
    - Flight: kg_CO2 = distance_km * 0.255 / passengers
    - Car: kg_CO2 = distance_km * 0.192
    - Train: kg_CO2 = distance_km * 0.041
    - Bus: kg_CO2 = distance_km * 0.089
  - `calculate_offsets()` → Returns offset recommendations
    - Tree planting (1 tree ≈ 20 kg CO2/year)
    - Renewable energy credits (kg CO2 → kWh offset)

**Database Models:**
- `backend/app/models.py`
  - `CarbonFootprint` model (lines 1200–1250)
    - Fields: `id`, `trip_id`, `total_kg_co2`, `by_transport_mode` (JSON), `offset_recommendations` (JSON), `created_at`

**Key Logic:**
- Estimates based on transport mode and distance
- Provides offset options (trees, renewable credits, donations)
- Stores calculation with trip for historical tracking

---

### Feature 9: Multi-Stop Trip Planner

**Description:** Create itineraries visiting multiple destinations with optimized routing and cost allocation.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/pages/MultiStopPlanner.tsx`
- `frontend/src/components/RouteOptimizer.tsx` (interactive map)

**API Endpoints:**
- `POST /api/trips/{trip_id}/multistop` → Create multi-stop itinerary
- `GET /api/trips/{trip_id}/multistop` → Retrieve itinerary
- `POST /api/trips/{trip_id}/multistop/optimize` → Optimize route

**Backend Router:**
- `backend/app/routers/trips.py` (lines 500–650)
  - `create_multistop_itinerary()` → Validates stops, creates itinerary
  - `optimize_multistop_route()` → Calls optimization service

**Backend Service Layer:**
- `backend/app/services/multistop_calculator.py` (lines 600–800)
  - `calculate_optimal_route()` → Traveling Salesman Problem solver
    - Input: origin, stops[], budget, preferences
    - Algorithm: Nearest neighbor heuristic + local 2-opt improvement
    - Output: ordered_stops[], total_cost, per_leg_cost[]
  - `calculate_leg_costs()` → Breaks down cost per stop
    - Transport between stops
    - Accommodation at each stop
    - Estimated activities/meals

**Database Models:**
- `backend/app/models.py`
  - `MultiStopItinerary` model (lines 1300–1350)
    - Fields: `id`, `trip_id`, `stops` (JSON array), `optimized_order` (JSON), `total_cost`, `created_at`
  - `Stop` model (lines 1400–1450)
    - Fields: `id`, `itinerary_id`, `destination_id`, `order`, `days`, `estimated_cost`

**Key Logic:**
- Validates stop sequence (no time overlap)
- Calculates transport between stops (via haversine distance)
- Allocates budget proportionally to trip duration
- Solves TSP for optimal ordering
- Generates detailed leg-by-leg breakdown

---

### Feature 10: Packing Checklist

**Description:** AI-generated packing lists based on trip duration, climate, activities, and weather.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/pages/PackingChecklist.tsx`
- `frontend/src/components/ChecklistItem.tsx` (interactive checklist)

**API Endpoints:**
- `GET /api/trips/{trip_id}/packing-list` → Generate packing list
- `PUT /api/trips/{trip_id}/packing-list/{item_id}` → Toggle item packed

**Backend Router:**
- `backend/app/routers/trips.py` (lines 700–800)
  - `generate_packing_list()` → Calls AI service

**Backend Service Layer:**
- `backend/app/services/destination_database.py` (lines 400–500)
  - `generate_packing_list()` → AI-based generation
    - Calls Gemini/OpenAI with trip context
    - Prompt: "For a [duration]-day trip to [destination] in [months] with activities [list], generate a packing list"
    - Returns: items[], categories, weight_estimate

**AI Service Integration:**
- `backend/app/services/gemini.py` OR `backend/app/services/openai.py`
  - `generate_text()` → Calls LLM API
  - Model: Gemini 1.5 Pro or GPT-4
  - Temperature: 0.3 (deterministic)

**Database Models:**
- `backend/app/models.py`
  - `PackingList` model (lines 1500–1550)
    - Fields: `id`, `trip_id`, `items` (JSON array), `generated_at`
  - PackingItem (nested): `name`, `category`, `quantity`, `is_packed`, `weight_kg`

**Key Logic:**
- Fetches trip duration, destination, dates, selected activities
- Fetches destination weather data
- Constructs LLM prompt with all context
- Parses JSON response into items with categories
- Stores for persistence

---

## User Management Features

### Feature 11: User Authentication

**Description:** Register, login, logout with JWT tokens and refresh token rotation.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/pages/Login.tsx`
- `frontend/src/pages/Register.tsx`
- `frontend/src/components/AuthContext.tsx` (JWT storage/refresh)

**API Endpoints:**
- `POST /api/auth/register` → Create user account
- `POST /api/auth/login` → Issue JWT + refresh token
- `POST /api/auth/refresh` → Refresh access token
- `POST /api/auth/logout` → Revoke tokens
- `GET /api/auth/me` → Current user profile

**Backend Router:**
- `backend/app/routers/auth.py` (lines 1–300)
  - `register()` → Validates email, hashes password, creates user
  - `login()` → Verifies credentials, returns JWT + refresh token
  - `refresh_token()` → Validates refresh token, issues new access token
  - `logout()` → Adds token to blacklist (optional)
  - `get_current_user()` → Dependency for protected routes

**Backend Auth Layer:**
- `backend/app/auth.py` (lines 1–200)
  - `hash_password()` → bcrypt hashing (12 rounds)
  - `verify_password()` → bcrypt comparison
  - `create_access_token()` → JWT encoding (exp: 15 min)
  - `create_refresh_token()` → JWT encoding (exp: 7 days)
  - `decode_token()` → JWT validation + claims extraction

**Database Models:**
- `backend/app/models.py`
  - `User` model (lines 50–120)
    - Fields: `id`, `email`, `password_hash`, `full_name`, `created_at`, `updated_at`, `is_active`
  - `RefreshToken` model (lines 150–180)
    - Fields: `id`, `user_id`, `token_hash`, `expiry`, `is_revoked`

**Database Layer:**
- `backend/app/database.py`
  - `create_user(db, email, password_hash, full_name)` → Inserts User
  - `get_user_by_email(db, email)` → Fetches by email
  - `create_refresh_token(db, user_id, token_hash)` → Stores refresh token

**Key Logic:**
- Email uniqueness validation
- Password strength validation (8+ chars, 1 uppercase, 1 digit)
- JWT payload: `{sub: user_id, email, iat, exp}`
- Refresh token rotation (old token revoked when new issued)
- Rate limiting on login endpoint (5 attempts/15 min)

---

### Feature 12: User Dashboard

**Description:** Overview of all trips, recent expenses, budget summary, and quick actions.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/pages/Dashboard.tsx` (main page)
- `frontend/src/components/TripCard.tsx` (trip grid)
- `frontend/src/components/BudgetSummary.tsx` (total spent)
- `frontend/src/components/RecentExpenses.tsx` (latest transactions)

**API Endpoints:**
- `GET /api/dashboard` → Aggregate dashboard data
- `GET /api/dashboard/stats` → Quick stats (total spent, trips, etc.)

**Backend Router:**
- `backend/app/routers/trips.py` (lines 900–1000)
  - `get_dashboard()` → Orchestrates aggregation
    - Calls `get_user_trips()`
    - Calls `get_recent_expenses()`
    - Calls `get_budget_summary()`
    - Returns combined response

**Backend Service Layer:**
- `backend/app/services/financial_validator.py` (lines 250–350)
  - `calculate_dashboard_stats()` → Aggregates across all trips
    - Total spent: Σ all expenses across trips
    - Active trips: COUNT where end_date ≥ today
    - Completed trips: COUNT where end_date < today
    - Average daily spend per trip

**Database Layer:**
- `backend/app/database.py`
  - `get_user_trips(db, user_id)` → Fetches all User's trips
  - `get_recent_expenses(db, user_id, limit=10)` → Latest expenses across trips
  - `get_total_spent(db, user_id)` → SUM(expenses) for user

**Key Logic:**
- Aggregates data from multiple trips
- Calculates running totals
- Identifies active trips (end_date ≥ today)
- Caches summary for 30 min (background refresh)

---

### Feature 13: Trip Sharing

**Description:** Share trip details with collaborators via invite links; read-only or edit permissions.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/components/ShareModal.tsx` (invite interface)
- `frontend/src/pages/SharedTrip.tsx` (access shared trip)

**API Endpoints:**
- `POST /api/trips/{trip_id}/share` → Generate invite link
- `GET /api/trips/{trip_id}/shares` → List shared users
- `DELETE /api/trips/{trip_id}/shares/{share_id}` → Revoke access
- `GET /api/shared-trips/{invite_token}` → Access shared trip

**Backend Router:**
- `backend/app/routers/trips.py` (lines 1050–1200)
  - `create_share()` → Generates invite link + permissions
  - `get_shares()` → Lists all shares for trip
  - `revoke_share()` → Deletes share record
  - `get_shared_trip()` → Validates token, returns trip data

**Backend Auth Layer:**
- `backend/app/auth.py` (lines 200–300)
  - `generate_invite_token()` → Creates secure token (UUID)
  - `verify_invite_token()` → Validates token, extracts trip_id + permissions

**Database Models:**
- `backend/app/models.py`
  - `TripShare` model (lines 1600–1650)
    - Fields: `id`, `trip_id`, `shared_by_user_id`, `shared_with_email`, `permission_level` (view/edit), `invite_token`, `created_at`, `expiry`

**Database Layer:**
- `backend/app/database.py`
  - `create_share(db, trip_id, user_id, email, permission, token)` → Inserts TripShare
  - `get_shares(db, trip_id)` → Fetches all shares
  - `revoke_share(db, share_id)` → Deletes share
  - `get_share_by_token(db, token)` → Fetches share via token

**Key Logic:**
- Token generation: secure random UUID
- Permission levels: VIEW (read-only), EDIT (modify expenses/notes)
- Expiry: optional (default no expiry)
- Email sent with invite link
- Shared user must be logged in to view

---

### Feature 14: Expense History & Export

**Description:** View all expenses with filtering, sorting; export to CSV/PDF.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/pages/ExpenseHistory.tsx`
- `frontend/src/components/ExportButton.tsx` (download controls)

**API Endpoints:**
- `GET /api/trips/{trip_id}/expenses/history` → Paginated expense list with filters
- `GET /api/trips/{trip_id}/expenses/export` → Export as CSV/PDF

**Backend Router:**
- `backend/app/routers/expenses.py` (lines 300–400)
  - `get_expense_history()` → Supports filtering (date range, category, amount range)
  - `export_expenses()` → Calls PDF/CSV generator

**Backend Service Layer:**
- `backend/app/services/pdf_generator.py` (lines 1–200)
  - `generate_expense_report()` → Creates PDF with:
    - Header: trip name, dates, total budget, total spent
    - Table: date, category, amount, notes
    - Summary: per-category breakdown, pie chart
    - Footer: export date, user name
  - `generate_csv_export()` → Creates CSV from expense records

**Utility Functions:**
- `backend/app/routers/expenses.py` (lines 400–450)
  - `build_csv_row()` → Formats expense for CSV
  - `apply_expense_filters()` → Date range, category, amount queries

**Database Layer:**
- `backend/app/database.py`
  - `get_expenses_paginated(db, trip_id, page, limit, filters)` → Applies WHERE clauses for filtering

**Key Logic:**
- Supports multi-select filtering (date range, categories, amount range)
- Sorts by date (desc), amount, category
- PDF generation: ReportLab or weasyprint
- CSV headers: Date, Category, Amount, Currency, Notes
- Supports pagination (100 items/page)

---

### Feature 15: Notifications Dashboard

**Description:** In-app notification center for budget alerts, trip updates, and system messages.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/components/NotificationBell.tsx` (icon)
- `frontend/src/pages/NotificationCenter.tsx` (full page)
- `frontend/src/components/NotificationStack.tsx` (toast queue)

**API Endpoints:**
- `GET /api/notifications` → List user notifications
- `PUT /api/notifications/{notification_id}` → Mark as read
- `DELETE /api/notifications/{notification_id}` → Delete notification
- `DELETE /api/notifications` → Clear all

**Backend Router:**
- `backend/app/routers/notifications.py` (lines 150–300)
  - `get_notifications()` → Returns paginated list
  - `mark_as_read()` → Updates read flag
  - `delete_notification()` → Removes notification
  - `clear_all()` → Deletes all for user

**Backend Service Layer:**
- `backend/app/routers/notifications.py` (lines 300–400)
  - `send_notification()` → Creates notification record + optional email
  - `send_bulk_notifications()` → Batch create for multiple users

**Database Models:**
- `backend/app/models.py`
  - `Notification` model (lines 750–800)
    - Fields: `id`, `user_id`, `type` (alert, update, system), `message`, `related_trip_id` (nullable), `read`, `created_at`

**Database Layer:**
- `backend/app/database.py`
  - `create_notification(db, user_id, type, message, trip_id)` → Inserts notification
  - `get_notifications(db, user_id, limit)` → Fetches paginated
  - `mark_read(db, notification_id)` → Updates read flag

**Key Logic:**
- Triggered by: expense creation (budget alert), trip shared, admin broadcasts
- Types: BUDGET_ALERT, TRIP_SHARED, SYSTEM_MESSAGE, EXPENSE_ALERT
- Persistent storage + optional email
- WebSocket support (optional real-time delivery)
- Auto-archive after 30 days

---

### Feature 16: Admin Analytics Dashboard

**Description:** System-wide analytics for admins: user growth, spending trends, popular destinations.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/pages/AdminDashboard.tsx` (admin-only page)
- `frontend/src/components/AnalyticsCharts.tsx` (charts/graphs)

**API Endpoints:**
- `GET /api/admin/analytics` → All analytics (requires admin role)
- `GET /api/admin/analytics/users` → User statistics
- `GET /api/admin/analytics/spending` → Spending trends
- `GET /api/admin/analytics/destinations` → Popular destinations

**Backend Router:**
- `backend/app/routers/admin_analytics.py` (lines 1–300)
  - `get_analytics()` → Orchestrates all analytics calls
  - `get_user_stats()` → COUNT users, registrations/month, active users
  - `get_spending_trends()` → SUM expenses by month, category
  - `get_popular_destinations()` → TOP destinations by trip count
  - Requires @admin_only decorator (verifies admin role on User)

**Backend Auth Layer:**
- `backend/app/auth.py` (lines 300–350)
  - `admin_only()` → Dependency for admin routes
    - Checks `User.is_admin` flag
    - Raises 403 if not admin

**Backend Service Layer:**
- `backend/app/services/financial_validator.py` (lines 350–450)
  - `calculate_analytics()` → Aggregates across all users
    - User growth: month-over-month COUNT
    - Spending by category: SUM expenses, GROUP BY category
    - Destination popularity: COUNT trips, GROUP BY destination

**Database Queries:**
- `backend/app/database.py`
  - `get_all_expenses(db)` → Fetches all expenses (for admins)
  - `get_all_trips(db)` → Fetches all trips
  - `get_all_users(db)` → Fetches all users

**Key Logic:**
- Admin role check on every endpoint
- Aggregates across all users (privacy concern: no PII exposed)
- Time-based grouping (day, month, year)
- Caches analytics for 1 hour
- Supports date range filtering

---

## AI & Intelligence Features

### Feature 17: AI Trip Chat Assistant (Advanced)

**Description:** Conversational AI chat for trip planning, budget advice, destination Q&A, and itinerary suggestions using Groq API.

**Status:** ⚠️ Partially Implemented (501 errors)

**Frontend Entry Points:**
- `frontend/src/pages/TripChat.tsx`
- `frontend/src/components/ChatWindow.tsx` (conversation UI)
- `frontend/src/components/ChatInput.tsx` (input + send)

**API Endpoints:**
- `POST /api/ai/chat` → Send message, receive response
- `GET /api/ai/chat/history` → Get chat history
- `DELETE /api/ai/chat/history` → Clear history

**Backend Router:**
- `backend/app/routers/ai_placeholders.py` (lines 1–100)
  - `chat_with_ai()` → Attempts to call Groq, returns 501 if API fails
  - `get_chat_history()` → Retrieves conversation
  - `clear_chat_history()` → Deletes messages

**Backend Service Layer:**
- `backend/app/services/groq_model_discovery.py` (lines 1–200)
  - `get_available_models()` → Discovers Groq models via API
  - `select_model()` → Chooses model based on request type
    - Model: Mixtral-8x7b-32768 (fast, general-purpose) or Llama-2-70b (complex reasoning)
  - `chat_with_groq()` → Calls Groq Chat API
    - Prompt context: trip details, expenses, destination info
    - Temperature: 0.7 (balanced creativity)

**Groq API Integration:**
- `backend/app/services/groq_model_discovery.py` (lines 200–300)
  - `GroqClient` class
  - Methods: `list_models()`, `send_message()`, `stream_response()`
  - Rate limiting: 30 requests/minute

**Database Models:**
- `backend/app/models.py`
  - `ChatMessage` model (lines 1700–1750)
    - Fields: `id`, `user_id`, `role` (user/assistant), `content`, `trip_context_id` (nullable), `created_at`

**Database Layer:**
- `backend/app/database.py`
  - `save_chat_message(db, user_id, role, content)` → Stores message
  - `get_chat_history(db, user_id, limit=50)` → Retrieves conversation
  - `clear_chat_history(db, user_id)` → Deletes all messages

**Current Error:**
- Returns HTTP 501 ("Not Implemented") when Groq API not accessible
- Root cause: Groq API key not configured in `.env`
- Error file: `backend/app/routers/ai_placeholders.py` lines 50–75

**Key Logic (Design Intent):**
- Maintains conversation context across turns
- Extracts trip context from user's active trip (if any)
- Sends structured prompt to Groq
- Streams responses for real-time chat feel
- Logs conversation for analytics

---

### Feature 18: PDF Report Generator

**Description:** Generate comprehensive PDF trip reports with expenses, packing lists, carbon footprint, and itinerary.

**Status:** ✅ Fully Implemented

**Frontend Entry Points:**
- `frontend/src/components/ExportButton.tsx` (trip-level)
- `frontend/src/pages/TripDetails.tsx` (download link)

**API Endpoints:**
- `GET /api/trips/{trip_id}/report/pdf` → Generate PDF report
- `GET /api/trips/{trip_id}/report/preview` → Preview report

**Backend Router:**
- `backend/app/routers/documents.py` (lines 1–200)
  - `generate_trip_report()` → Orchestrates PDF generation
  - `preview_report()` → Returns HTML preview

**Backend Service Layer:**
- `backend/app/services/pdf_generator.py` (lines 200–400)
  - `create_trip_report()` → Combines all sections
    - Section 1: Trip header (name, dates, travelers, budget)
    - Section 2: Itinerary (day-by-day breakdown)
    - Section 3: Expenses (category breakdown, total spent)
    - Section 4: Packing list (by category)
    - Section 5: Carbon footprint (emissions, offsets)
    - Section 6: Trip comparison (if multi-trip saved)
  - `generate_pdf()` → Uses ReportLab or WeasyPrint
    - Page size: A4
    - Margins: 1 inch
    - Fonts: Helvetica (body), Helvetica-Bold (headers)
    - Colors: Blue headers, grey tables, green highlights for savings

**PDF Libraries:**
- `backend/app/services/pdf_generator.py` (lines 400–500)
  - Library: ReportLab or WeasyPrint
  - Functions:
    - `create_document()` → Initialize PDF canvas
    - `add_header()` → Title + trip info
    - `add_table()` → Formatted data table
    - `add_chart()` → Expense pie chart
    - `finalize_pdf()` → Outputs bytes

**Database Models:**
- `backend/app/models.py`
  - `Document` model (lines 1800–1850)
    - Fields: `id`, `trip_id`, `user_id`, `file_name`, `s3_key` (if stored in S3), `created_at`

**Database Layer:**
- `backend/app/database.py`
  - `save_document(db, trip_id, user_id, filename, file_content)` → Stores metadata (file may be on disk or S3)

**Key Logic:**
- Fetches trip + all related data (expenses, itinerary, packing list, carbon)
- Combines into single report
- Generates charts/visualizations
- Outputs as byte stream (downloadable)
- Optional: stores on S3 for retrieval

---

## Analytics & Admin Features

### Additional Features (Reference)

**Feature: System Health & Monitoring**
- Not a user-facing feature
- Backend monitoring: error logs, API latency, database query times
- Stored in `backend/logs/app.log`

**Feature: Database Migrations**
- Not a user-facing feature
- Alembic migrations in `backend/alembic/versions/`
- Run on deployment

---

## Code Dependency Graph

### Model Relationships

```
User (1) ─────────── (M) Trip
  ↓
  ├─ (1) ─── (M) Notification
  ├─ (1) ─── (M) ChatMessage
  ├─ (1) ─── (M) TripShare
  └─ (1) ─── (M) RefreshToken

Trip (1) ─────────── (M) Expense
 ├─ (1) ─── (M) Itinerary
 ├─ (1) ─── (M) BudgetAlert
 ├─ (1) ─── (M) Document
 └─ (1) ─── (1) Destination (foreign key)

Destination (1) ─────────── (M) Activity
  └─ (1) ─── (1) WeatherCache

TripComparison (M) ─────────── (M) Trip (JSON array of trip_ids)

MultiStopItinerary (1) ─────────── (M) Stop
  └─ Stop (M) ─────────── (1) Destination
```

### API Router Dependencies

```
auth.py
  ├─ Uses: User model, RefreshToken model, auth.py (hash, verify, JWT)
  └─ Called by: Frontend login, register, refresh endpoints

trips.py
  ├─ Uses: Trip, Itinerary, Expense, CarbonFootprint, MultiStopItinerary models
  ├─ Calls: multistop_calculator.py (optimize, compare, carbon)
  ├─ Calls: destination_database.py (weather, packing, activities)
  └─ Called by: Frontend trip CRUD, planner, optimizer

expenses.py
  ├─ Uses: Expense model
  ├─ Calls: financial_validator.py (category validation, alerts)
  ├─ Calls: pdf_generator.py (export to CSV/PDF)
  └─ Called by: Frontend expense CRUD, history, export

destinations.py
  ├─ Uses: Destination, Activity, WeatherCache models
  ├─ Calls: destination_database.py (budget estimate, activities, weather)
  └─ Called by: Frontend explorer, destination details

budget_alerts.py
  ├─ Uses: BudgetAlert, Notification models
  ├─ Calls: financial_validator.py (evaluate condition)
  ├─ Calls: notifications.py (send alert)
  └─ Triggered by: expenses.py (on expense creation)

notifications.py
  ├─ Uses: Notification model
  ├─ Calls: email service (optional)
  └─ Called by: budget_alerts.py, trips.py (share), admin_analytics.py

documents.py
  ├─ Uses: Document model
  ├─ Calls: pdf_generator.py (generate report)
  └─ Called by: Frontend export report

admin_analytics.py
  ├─ Uses: User, Trip, Expense models (read-only)
  ├─ Calls: financial_validator.py (analytics aggregation)
  └─ Requires: admin_only decorator from auth.py

ai_placeholders.py
  ├─ Uses: ChatMessage model
  ├─ Calls: groq_model_discovery.py (chat API)
  └─ Called by: Frontend chat input
```

### Service Layer Dependencies

```
multistop_calculator.py
  ├─ Functions: calculate_optimized_budget(), compare_trip_costs(), calculate_optimal_route(), estimate_co2_emissions()
  ├─ Uses: Expense, Trip, Destination models (read-only)
  └─ Called by: trips.py (optimize, compare, carbon)

destination_database.py
  ├─ Functions: load_destination_database(), calculate_estimate_budget(), get_recommended_activities(), fetch_weather_data(), generate_packing_list()
  ├─ Uses: Destination, Activity, WeatherCache models
  ├─ Calls: OpenWeatherMap API (external)
  ├─ Calls: Gemini/OpenAI API (packing list generation)
  └─ Called by: destinations.py (explorer), trips.py (weather, packing)

financial_validator.py
  ├─ Functions: validate_expense(), get_category_breakdown(), evaluate_budget_alert(), calculate_analytics()
  ├─ Uses: Expense, BudgetAlert models
  └─ Called by: expenses.py (validation), budget_alerts.py (alert check), admin_analytics.py (aggregation)

pdf_generator.py
  ├─ Functions: create_trip_report(), generate_expense_report(), generate_csv_export(), generate_pdf()
  ├─ Uses: Trip, Expense, Itinerary, PackingList, CarbonFootprint models
  └─ Called by: documents.py (report generation), expenses.py (export)

gemini.py / openai.py
  ├─ Functions: generate_text(), stream_response()
  ├─ External: Gemini API / OpenAI API
  └─ Called by: destination_database.py (packing list), ai_placeholders.py (chat)

groq_model_discovery.py
  ├─ Functions: get_available_models(), chat_with_groq(), stream_response()
  ├─ External: Groq API
  └─ Called by: ai_placeholders.py (chat)

explainability.py
  ├─ Functions: explain_optimization(), explain_route(), explain_alerts()
  ├─ Uses: Trip, Expense, Optimization results
  └─ Called by: trips.py (when returning optimizer results)

itinerary_validator.py
  ├─ Functions: validate_itinerary(), check_date_conflicts(), check_location_feasibility()
  ├─ Uses: Itinerary, Destination models
  └─ Called by: trips.py (on itinerary creation/update)

personalized_plan_validator.py
  ├─ Functions: validate_plan(), suggest_alternatives(), check_feasibility()
  ├─ Uses: Trip, Expense models
  └─ Called by: trips.py (plan validation)
```

### Database Layer Dependencies

```
database.py
  ├─ Connection pool: SQLAlchemy engine
  ├─ Session management: SQLAlchemy Session
  ├─ CRUD functions:
  │   ├─ create_user(), get_user_by_email(), get_user()
  │   ├─ create_trip(), get_trip(), update_trip(), get_user_trips()
  │   ├─ add_expense(), get_expenses(), get_expenses_paginated()
  │   ├─ create_share(), get_shares(), get_share_by_token()
  │   ├─ get_destination(), search_destinations(), filter_destinations()
  │   ├─ create_notification(), get_notifications(), mark_read()
  │   └─ [50+ total CRUD functions]
  └─ Called by: All routers and services
```

---

## Summary

This document traces all 18 BudgetBound features from frontend UI through API endpoints, backend routers, service layers, database models, and external integrations. Use it for:

1. **Implementation verification:** Confirm each feature's code paths match design
2. **Debugging:** Trace errors back to specific files and line ranges
3. **Team allocation:** Reference this map to understand feature dependencies
4. **Viva preparation:** Study the code paths to explain technical decisions

**Next:** See `4_MEMBER_1_EXPLANATION_GUIDE.md` for Member 1's detailed feature breakdown and algorithms.

---

**End of Document**
