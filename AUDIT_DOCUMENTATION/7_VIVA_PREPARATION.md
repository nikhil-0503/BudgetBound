# BudgetBound: Viva Preparation Guide

**Document:** 7_VIVA_PREPARATION.md  
**Created:** October 2026  
**Purpose:** 30 technical Q&A with code references to prepare for final year project viva  
**Duration:** ~90 minutes viva (typical university exam)

---

## Part 1: General Project Questions (10 Q&A)

### Q1: What is BudgetBound and what problem does it solve?

**Answer:**
BudgetBound is a full-stack travel budgeting application that helps users plan trips within financial constraints. The core problem: travelers struggle to estimate costs, allocate budgets across categories, and track spending during trips.

Key problems we solve:
1. **Budget uncertainty**: Users don't know how much to allocate (accommodation vs food vs activities)
2. **Overspending**: No real-time alerts when approaching/exceeding limits
3. **Multi-stop complexity**: Optimizing routes and costs for multi-city trips
4. **Post-trip analysis**: Difficulty comparing spending patterns across trips
5. **Sustainability**: Lack of awareness about environmental impact of travel

**Features:** 18 features across 3 categories: Trip Planning (7), User Management (8), AI Services (3)

**Tech Stack:**
- Frontend: React/TypeScript, axios, React Router
- Backend: Python FastAPI, SQLAlchemy ORM, PostgreSQL
- AI: Groq, Gemini, OpenAI APIs
- Deployment: Docker, optional Kubernetes

---

### Q2: What are the 18 features and how are they categorized?

**Answer:**

**Trip Planning (7 features - Member 1):**
1. Interactive Trip Planner
2. Budget Optimizer (algorithm)
3. Expense Tracker
4. Trip Comparison
5. Weather & Climate Data
6. Carbon Footprint Calculator
7. Multi-Stop Trip Planner (TSP)
8. Packing Checklist (AI-generated)

**User Management (8 features - Member 2):**
9. User Authentication (JWT)
10. User Dashboard
11. Trip Sharing (with permissions)
12. Expense History & Export (CSV/PDF)
13. Notifications Dashboard
14. Budget Alerts (real-time)
15. Destination Explorer
16. Admin Analytics Dashboard

**AI & Advanced (3 features - Member 3):**
17. AI Trip Chat Assistant (Groq)
18. PDF Report Generator

**Status:** 16 fully implemented, 2 returning 501 errors (AI Chat partially)

---

### Q3: What is the database schema? How many models and relationships?

**Answer:**

**10 Core Database Models:**
1. `User` — user accounts, auth
2. `Trip` — trip records
3. `Itinerary` — day-by-day activities
4. `Expense` — recorded spending
5. `BudgetAlert` — spending thresholds
6. `Notification` — in-app messages
7. `Destination` — curated destinations
8. `Activity` — destination activities
9. `TripShare` — collaboration/sharing
10. `ChatMessage` — AI conversation history
11. `CarbonFootprint` — emissions tracking
12. `PackingList` — AI-generated checklists
13. `WeatherCache` — weather data cache
14. `Document` — exported reports
15. `RefreshToken` — JWT rotation
16. `MultiStopItinerary` — multi-city routes

**Key Relationships:**
```
User (1) ─── (M) Trip ─── (M) Expense
            ├── (M) Notification
            ├── (M) ChatMessage
            ├── (M) TripShare
            └── (M) RefreshToken

Trip (1) ─── (1) Destination ─── (M) Activity
    ├── (M) Itinerary
    ├── (M) BudgetAlert
    ├── (1) CarbonFootprint
    ├── (1) PackingList
    └── (1) MultiStopItinerary
```

---

### Q4: What's the architecture pattern? Layers? Separation of concerns?

**Answer:**

**4-Layer Architecture:**

```
Layer 1: Frontend (React)
  ├─ Pages (TripPlanner.tsx, Dashboard.tsx, etc.)
  ├─ Components (TripCard, ExpenseForm, etc.)
  ├─ Services (api.ts, auth.ts)
  └─ Hooks (useAuth, useTrip, etc.)

Layer 2: API / Routers (FastAPI)
  ├─ auth.py (register, login, JWT)
  ├─ trips.py (CRUD trips, optimization, comparison)
  ├─ expenses.py (track spending, export)
  ├─ destinations.py (explorer, weather)
  ├─ notifications.py (alerts, messages)
  ├─ documents.py (PDF generation)
  ├─ admin_analytics.py (system analytics)
  ├─ ai_placeholders.py (Groq chat)
  └─ [10 routers total]

Layer 3: Services (Business Logic)
  ├─ multistop_calculator.py (optimizer, TSP, carbon)
  ├─ destination_database.py (weather, activities, packing)
  ├─ financial_validator.py (expense validation, alerts)
  ├─ pdf_generator.py (report generation)
  ├─ gemini.py, openai.py (LLM wrappers)
  ├─ groq_model_discovery.py (Groq integration)
  ├─ explainability.py (explain optimization)
  ├─ itinerary_validator.py (validation)
  └─ [8 services total]

Layer 4: Data / Database
  ├─ models.py (SQLAlchemy models, 16 tables)
  ├─ database.py (connection, CRUD functions)
  ├─ schemas.py (Pydantic validation)
  └─ PostgreSQL (production DB)
```

**Separation of Concerns:**
- Routers: Request validation, authentication, response formatting
- Services: Business logic, algorithms, external API calls
- Database: ORM models, CRUD operations, relationships
- Frontend: UI state, user interaction, API integration

---

### Q5: What's the deployment pipeline? How is the app deployed?

**Answer:**

**Deployment Architecture:**

```
Development:
  - Local: npm run dev (React) + python -m uvicorn (FastAPI)
  - Git: GitHub for version control

Staging:
  - Docker: Dockerfile in backend/
  - docker-compose.yml for multi-container local testing

Production:
  - Backend: Docker image → Kubernetes pod (or Docker on EC2/DigitalOcean)
  - Frontend: React build → S3 + CloudFront (or nginx)
  - Database: Managed PostgreSQL (AWS RDS, Heroku Postgres, etc.)
  - Secrets: Environment variables (GROQ_API_KEY, DATABASE_URL, etc.)

CI/CD (Optional):
  - GitHub Actions: Run tests → Build Docker image → Push to registry
  - Automated deployment on main branch push

Monitoring:
  - Logs: CloudWatch, Papertrail, or ELK
  - Uptime: StatusPage.io or similar
  - Errors: Sentry or Rollbar
```

---

### Q6: What are the main algorithms? Which are most complex?

**Answer:**

**5 Key Algorithms:**

1. **Budget Optimizer (Linear Programming)** — Complexity: 5/5
   - Redistributes budget across categories
   - Constraints: sum = budget, lower/upper bounds per category
   - Solver: scipy.optimize.linprog
   - Objective: minimize deviation from user preferences

2. **Traveling Salesman Problem (TSP)** — Complexity: 5/5
   - Finds optimal route for multi-city trips
   - Algorithm: Nearest neighbor + 2-opt heuristic
   - Time complexity: O(n²) heuristic (vs O(n!) exact)
   - Returns: ordered destinations, total cost, per-leg breakdown

3. **Carbon Footprint Calculation** — Complexity: 3/5
   - Estimates CO₂ emissions by transport mode
   - Formula: distance_km × emission_factor / passengers
   - Provides offset recommendations (trees, renewable energy)
   - Example: Flight 340km = 43.35 kg CO₂ per person

4. **Trip Comparison** — Complexity: 3/5
   - Aggregates expenses across multiple trips
   - Calculates: per-person cost, per-day cost, category breakdown, variance
   - Enables spending pattern analysis

5. **Weather-Based Packing Generator** — Complexity: 2/5
   - Uses Gemini/OpenAI API with trip context
   - Generates JSON: {items, categories, weights, recommendations}
   - Temperature setting: 0.3 for determinism

---

### Q7: How is authentication and authorization implemented?

**Answer:**

**Authentication Flow:**

1. **Registration:**
   - User submits email + password
   - Server validates password strength (8+ chars, 1 uppercase, 1 digit)
   - Server hashes password using bcrypt (12 rounds)
   - Server stores in User table

2. **Login:**
   - User submits email + password
   - Server fetches user by email
   - Server verifies password: `bcrypt.verify(submitted, stored_hash)`
   - If match: generate tokens

3. **Token Generation:**
   - Access token: JWT with {sub: user_id, email, iat, exp}
     - Expiry: 15 minutes (short-lived, can't steal for long)
     - Signed with SECRET_KEY using HS256
   - Refresh token: JWT with {sub: user_id, iat, exp, type: "refresh"}
     - Expiry: 7 days
     - Hashed in database (can't brute-force if stolen)

4. **Token Usage:**
   - Frontend stores access token in memory (cleared on reload)
   - Frontend stores refresh token in httpOnly cookie (immune to XSS)
   - Frontend includes access token in Authorization header for API calls
   - Server decodes token: `jwt.decode(token, SECRET_KEY, algorithms=["HS256"])`

5. **Token Refresh:**
   - When access token expires: client sends refresh token
   - Server validates refresh token + checks it hasn't been revoked
   - Server issues new access token
   - Server revokes old refresh token (optional: rotate)

**Authorization (Permission Checking):**

```python
# Example: verify user owns trip before allowing modification
@router.put("/trips/{trip_id}")
async def update_trip(trip_id, ..., current_user = Depends(verify_token)):
    trip = db.query(Trip).filter_by(id=trip_id, user_id=current_user["sub"]).first()
    if not trip:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Proceed with update
```

**Security Measures:**
- bcrypt with 12 rounds (makes brute force expensive)
- Short-lived access tokens (15 min)
- httpOnly cookies (prevent XSS theft)
- Refresh token hashing (prevent database leak exploitation)
- Rate limiting on login endpoint (prevent brute force)

---

### Q8: How do you handle errors and edge cases?

**Answer:**

**Error Handling Strategy:**

1. **Input Validation (Pydantic):**
   ```python
   class TripCreate(BaseModel):
       name: str = Field(..., min_length=1, max_length=255)
       budget: float = Field(..., gt=0)  # Budget must be > 0
       start_date: date
       end_date: date
       
       @validator('end_date')
       def validate_dates(cls, v, values):
           if 'start_date' in values and v < values['start_date']:
               raise ValueError('end_date must be after start_date')
           return v
   ```

2. **Business Logic Validation (Services):**
   ```python
   # Check budget optimizer feasibility
   if sum(min_per_category) > total_budget:
       raise ValueError(f"Budget ${total_budget} too small; minimum ${sum(min_per_category)} required")
   
   # Check TSP has at least 2 destinations
   if len(destinations) < 2:
       raise ValueError("Need at least 2 destinations for multi-stop trip")
   ```

3. **API Error Handling:**
   ```python
   @router.get("/trips/{trip_id}")
   async def get_trip(trip_id: int, ...):
       trip = db.query(Trip).filter_by(id=trip_id).first()
       if not trip:
           raise HTTPException(status_code=404, detail="Trip not found")
       return trip
   ```

4. **External API Resilience:**
   ```python
   # Groq API call with fallback
   try:
       response = requests.post(GROQ_API_URL, ...)
       return response.json()
   except requests.Timeout:
       return "AI service temporarily unavailable"
   except requests.HTTPError as e:
       if e.response.status_code == 429:
           return "Rate limit exceeded, please retry"
       else:
           return f"Error: {e.response.status_code}"
   ```

5. **Database Constraints:**
   - Unique email on User table
   - Foreign key constraints (Trip.destination_id → Destination.id)
   - Not null constraints on required fields

6. **Edge Cases:**
   - User with no trips (dashboard shows empty state)
   - Trip with no expenses (optimizer returns error: no data)
   - Weather API down (use cached data, serve with warning)
   - Destination with no activities (return empty list)
   - LLM API returns invalid JSON (fallback to template response)

---

### Q9: What's the code quality? Do you have tests?

**Answer:**

**Code Quality Measures:**
- Linting: flake8 for Python, ESLint for TypeScript
- Type hints: Python type annotations throughout
- Docstrings: Function docstrings explaining parameters and returns
- Code organization: 4-layer architecture (clean separation)

**Testing:**
- Unit tests: Limited (minimal test suite present)
- Integration tests: Not visible in codebase
- Manual testing: All endpoints tested via Postman/curl
- Recommended: Add pytest for backend, Jest for frontend

**Best Practices Used:**
- ORM (SQLAlchemy) for SQL injection prevention
- Parameterized queries (not string concatenation)
- Environment variables for secrets (no hardcoded keys)
- Hashing for passwords (bcrypt, not plaintext)
- JWT validation on every protected endpoint
- CORS configured appropriately
- Pagination on large datasets (prevent DoS)

---

### Q10: What was the most challenging part of the project?

**Answer:**

**Top 3 Challenges:**

1. **Algorithm Design (Budget Optimizer & TSP):**
   - Challenge: Optimizing budget redistribution with multiple constraints
   - Solution: Linear programming (scipy.optimize.linprog)
   - Lesson: Understand mathematical foundations before coding

2. **AI Integration & Error Handling:**
   - Challenge: External APIs fail, return unexpected formats, rate limit
   - Solution: Error handling, fallbacks, caching, retry logic
   - Lesson: Never trust external services; always have a plan B

3. **Data Aggregation & Performance:**
   - Challenge: Dashboard aggregates data from multiple tables; query performance
   - Solution: Pagination, caching, indexed queries, ORM optimization
   - Lesson: Profile before optimizing; N+1 query problem is real

---

## Part 2: Member-Specific Deep Dives (20 Q&A)

### MEMBER 1: Trip Planning & Budget Intelligence

**Q11: Explain the budget optimizer algorithm in detail.**

**Answer:**
[See Member 1 Guide, Feature 2 section - Budget Optimizer]

The optimizer uses linear programming to redistribute budget across categories (accommodation, food, transport, activities, misc) while respecting constraints and user preferences.

**Mathematical Model:**
- Objective: Minimize Σ(preference_weight[i] * deviation[i])
- Constraints: sum = budget, lower/upper bounds, non-negative
- Solver: scipy.optimize.linprog
- Input: expenses[], budget, preferences[]
- Output: optimized_allocation[]

**Example:**
- Original: Accommodation $2000, Food $1500, Transport $500, Activities $1000
- Preferences: More activities, less food
- Optimized: Accommodation $1900, Food $1200, Transport $600, Activities $1300
- Savings realized: Flexibility without exceeding budget

**Error Handling:**
- If budget < minimum required: return error with suggested budget
- If constraints infeasible: return best approximation + warning

**Viva Tip:** Be ready to draw the constraint space (3D polytope) or explain why linear programming is appropriate vs greedy algorithms.

---

**Q12: How does the multi-stop TSP solver work? What's the time complexity?**

**Answer:**
[See Member 1 Guide, Feature 9 section - Multi-Stop TSP]

**Problem:** Find optimal order to visit N destinations, minimizing travel cost/distance.

**Algorithm (Heuristic):**

1. **Nearest Neighbor Construction:** O(n²)
   - Start at origin
   - Repeat: pick closest unvisited destination
   - Until all visited
   - Returns: initial tour

2. **2-Opt Local Improvement:** O(n²) per iteration
   - For each pair of edges: try swapping (reversing segment)
   - If cost decreases: accept, restart
   - Until no improvement possible
   - Returns: locally-optimal tour

**Total Complexity:** O(n²·k) where k = improvement iterations (typically small)

**Why Not Exact (Brute Force)?**
- Exact TSP is NP-hard: (n-1)! permutations
- For n=10: 362,880 solutions (feasible)
- For n=20: 121 quadrillion (infeasible)
- Heuristic is good enough: 80–95% optimal in practice

**Example:**
- Destinations: London, Paris, Amsterdam, Brussels
- Nearest Neighbor: London → Brussels (315km) → Amsterdam (210km) → Paris (510km) = 1035km
- 2-Opt: (try swaps) → final: same or better
- Output: ordered list, cost breakdown per leg

**Viva Tip:** Be able to explain why heuristic is necessary, draw a small example tour, explain 2-opt edge swap.

---

**Q13: How does the trip comparison feature work?**

**Answer:**
[See Member 1 Guide, Feature 3 section - Trip Comparison]

Aggregates expenses across multiple trips to enable spending pattern analysis.

**Metrics Calculated:**
- Total cost: sum of all expenses per trip
- Cost per person: total / traveler_count
- Cost per day: total / duration_days
- Category breakdown: {category: amount, percent}
- Variance: spread across trips

**Use Cases:**
- "My Paris trip was more expensive than Barcelona"
- "I spend more on food than accommodation"
- "3-day trip costs more per day than 10-day trip (economies of scale)"

**Database Query:**
```python
for trip_id in trip_list:
    expenses = db.query(Expense).filter_by(trip_id=trip_id).all()
    total = sum(e.amount for e in expenses)
    per_person = total / trip.traveler_count
    per_day = total / trip.duration_days
    by_category = group_by_category(expenses)
    results.append({trip_id, total, per_person, per_day, by_category})
```

---

**Q14: Explain CO₂ emission calculation with a real example.**

**Answer:**
[See Member 1 Guide, Feature 8 section - Carbon Footprint Calculator]

**Emission Factors (kg CO₂ per km):**
- Flight (domestic): 0.255
- Flight (international): 0.195 (includes radiative forcing)
- Car: 0.192
- Train: 0.041
- Bus: 0.089

**Formula:** CO₂ = distance_km × emission_factor / number_of_passengers

**Example Trip: London → Paris → Amsterdam**

1. Flight London-Paris (340 km, 2 passengers)
   - CO₂ = 340 × 0.255 / 2 = 43.35 kg CO₂

2. Train Paris-Amsterdam (510 km, 2 passengers)
   - CO₂ = 510 × 0.041 / 2 = 10.455 kg CO₂

3. Total: 53.805 kg CO₂

**Offset Options:**
- **Trees:** 53.8 kg CO₂ ÷ 20 kg CO₂/tree/year = 2.7 trees needed
- **Renewable Energy:** 53.8 kg CO₂ × 0.45 kWh/kg = 24.2 kWh equivalent
- **Carbon Credits:** 53.8 kg CO₂ ÷ 1000 = 0.054 credits

**Viva Tip:** Know why radiative forcing is added to flight emissions (high-altitude aerosol effects amplify warming), why passenger count matters (shared transport = lower per-person), and acknowledge uncertainty in estimates.

---

**Q15: How do you generate packing lists using AI? What's the prompt structure?**

**Answer:**
[See Member 1 Guide, Feature 10 section - Packing Checklist]

**Process:**

1. **Gather Context:**
   - Trip duration (days)
   - Destination (climate, country)
   - Trip dates (season)
   - Activities (hiking, beach, cultural)
   - Travelers (solo, family)
   - Weather forecast

2. **Construct Prompt:**
   ```
   Generate a packing list for a 10-day trip to Paris in May (Spring).
   
   Weather: 15–20°C, 60% humidity, 5mm rain
   Activities: Cultural (museums, walking), dining out
   Travelers: 2 people
   
   Format: JSON with items grouped by category (clothing, toiletries, electronics, activity-specific).
   Include quantities and weight estimates.
   ```

3. **LLM Call:**
   - Model: Gemini 1.5 Pro or GPT-4
   - Temperature: 0.3 (deterministic, not creative)
   - Max tokens: 1000

4. **Parse Response:**
   ```json
   {
     "categories": [
       {
         "name": "Clothing",
         "items": [
           {"name": "T-shirt", "quantity": 5, "weight_kg": 0.3},
           {"name": "Light jacket", "quantity": 1, "weight_kg": 0.4}
         ]
       }
     ],
     "total_weight_kg": 5.2
   }
   ```

5. **Fallback:**
   - If JSON parsing fails: return template-based packing list
   - If API down: use cached generic list for destination/season

---

### MEMBER 2: User Management & Infrastructure

**Q16: Walk me through the authentication flow from login to authenticated API call.**

**Answer:**
[See Member 2 Guide, Feature 11 section - User Authentication]

**Step-by-Step:**

1. **User Enters Credentials:**
   - Frontend: email + password in login form

2. **Frontend POST to Backend:**
   ```
   POST /api/auth/login
   Content-Type: application/json
   
   {
     "email": "user@example.com",
     "password": "SecurePassword123"
   }
   ```

3. **Backend Verification:**
   - Fetch user by email: `db.query(User).filter_by(email="...").first()`
   - Hash submitted password: `bcrypt.hash(password_submitted)`
   - Compare with stored hash: `bcrypt.verify(password_submitted, user.password_hash)`
   - If mismatch: return 401 Unauthorized

4. **Token Generation:**
   - Access Token: `jwt.encode({sub: 1, email: "...", iat: now, exp: now+15min}, SECRET_KEY, HS256)`
   - Refresh Token: `jwt.encode({sub: 1, iat: now, exp: now+7days, type: "refresh"}, SECRET_KEY, HS256)`

5. **Backend Returns:**
   ```json
   {
     "access_token": "eyJhbGc...",
     "refresh_token": "eyJhbGc...",
     "token_type": "bearer",
     "user": {"id": 1, "email": "user@example.com", "full_name": "John Doe"}
   }
   ```

6. **Frontend Storage:**
   - Access Token → Memory (cleared on page reload)
   - Refresh Token → httpOnly Cookie (survives reload)

7. **Authenticated API Call:**
   ```
   GET /api/trips
   Authorization: Bearer eyJhbGc...
   ```

8. **Backend Validation (on every call):**
   - Extract token from header: `Authorization: Bearer {token}`
   - Decode: `jwt.decode(token, SECRET_KEY, algorithms=["HS256"])`
   - Extract user_id from payload: `payload["sub"]`
   - Fetch user: `db.query(User).filter_by(id=user_id).first()`
   - Proceed with request using `current_user`

9. **Token Expiry:**
   - After 15 min: access token expires → 401 Unauthorized
   - Frontend catches 401 → sends refresh token
   - Backend validates refresh token → issues new access token
   - Frontend retries original request with new access token

---

**Q17: How does trip sharing work? Explain the permission model.**

**Answer:**
[See Member 2 Guide, Feature 13 section - Trip Sharing]

**Sharing Flow:**

1. **Initiator (User A) Shares Trip:**
   ```
   POST /api/trips/123/share
   {
     "shared_with_email": "userB@example.com",
     "permission_level": "view"  // or "edit"
   }
   ```

2. **Backend Validation:**
   - Verify User A owns Trip 123 (Trip.user_id == current_user.id)
   - Validate email format
   - Check not already shared (or overwrite)

3. **Generate Invite Token:**
   - UUID: `token = str(uuid.uuid4())`  # 128-bit random
   - Store: `TripShare(trip_id=123, shared_by_user_id=A, shared_with_email="B", permission_level="view", invite_token=token)`

4. **Send Email:**
   - Link: `https://app.com/shared-trip?token={uuid}`
   - Message: "User A shared Trip 123 with you"

5. **Recipient (User B) Accepts:**
   - Clicks link → Browser calls `GET /api/shared-trips/{token}`
   - Backend:
     - Looks up TripShare by token
     - Checks token not expired (30-day default)
     - Checks not revoked
     - Returns Trip data based on permission_level

6. **Permission Levels:**
   - **VIEW:** Read-only trip data (see expenses, itinerary)
   - **EDIT:** Can add/modify expenses, notes (collaborate)

7. **Revocation:**
   - User A: `DELETE /api/trips/123/shares/{share_id}`
   - Backend: `TripShare.is_revoked = True`
   - Next access: 403 Forbidden

**Security:**
- UUID is 128-bit random (not guessable)
- Token stored in database (not hardcoded)
- Expiry prevents indefinite access
- No authentication required for shared link (public, but with token)

---

**Q18: Explain the notification system. How are alerts triggered?**

**Answer:**
[See Member 2 Guide, Feature 15 section - Notifications Dashboard]

**Types of Notifications:**
- BUDGET_ALERT: "You've spent 75% of food budget"
- TRIP_SHARED: "Alice shared a trip with you"
- EXPENSE_ALERT: "New expense recorded: $50 food"
- SYSTEM_MESSAGE: "Maintenance window tomorrow"

**Budget Alert Trigger Flow:**

1. **User Adds Expense:**
   ```
   POST /api/trips/123/expenses
   {
     "category": "FOOD",
     "amount": 50,
     "date": "2024-01-15"
   }
   ```

2. **Backend Creates Expense:**
   - Insert into database
   - Calculate current spending: `total_spent = SUM(expenses)`
   - Calculate percentage: `percent_spent = total_spent / trip.budget * 100`

3. **Check Alert Thresholds:**
   - Fetch all BudgetAlert records for trip: `db.query(BudgetAlert).filter_by(trip_id=123).all()`
   - For each threshold (e.g., 50%, 75%, 100%):
     - If `percent_spent >= threshold` AND `not already_triggered`:
       - Mark as triggered: `BudgetAlert.is_triggered = True`
       - Create notification: `Notification(type="BUDGET_ALERT", message="...", user_id=...)`
       - (Optional) Send email

4. **Frontend Receives Alert:**
   - Toast notification: "Alert: You've spent 75% of budget"
   - Notification bell badge increments
   - User can view in notification center

**Database:**
```python
# Notification model
class Notification(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)  # BUDGET_ALERT, TRIP_SHARED, etc.
    message = Column(String)
    related_trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Preventing Duplicate Alerts:**
- Use `is_triggered` flag on BudgetAlert
- Only create notification if flag transitions from False → True
- Prevents spam (user sees alert once per threshold, not every expense)

---

**Q19: How do you handle pagination and filtering for large datasets?**

**Answer:**
[See Member 2 Guide, Feature 14 section - Expense History & Export]

**Pagination (Offset/Limit):**

1. **Request:**
   ```
   GET /api/trips/123/expenses/history?page=2&limit=50
   ```

2. **Backend Calculation:**
   ```python
   page = 2
   limit = 50
   skip = (page - 1) * limit = 50
   
   expenses = db.query(Expense)\
       .filter_by(trip_id=123)\
       .offset(skip)\
       .limit(limit)\
       .all()
   ```

3. **Response:**
   ```json
   {
     "expenses": [...50 items...],
     "pagination": {
       "page": 2,
       "limit": 50,
       "total": 237,
       "pages": 5  // ceil(237 / 50)
     }
   }
   ```

**Filtering (WHERE Clauses):**

```python
# Multi-filter support
@router.get("/trips/{trip_id}/expenses/history")
async def get_expense_history(
    trip_id: int,
    page: int = 1,
    limit: int = 100,
    category: Optional[str] = None,        # FOOD, TRANSPORT, etc.
    amount_from: Optional[float] = None,
    amount_to: Optional[float] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    ...
):
    query = db.query(Expense).filter_by(trip_id=trip_id)
    
    if category:
        query = query.filter_by(category=category)
    if amount_from is not None:
        query = query.filter(Expense.amount >= amount_from)
    if amount_to is not None:
        query = query.filter(Expense.amount <= amount_to)
    if date_from:
        query = query.filter(Expense.date >= date_from)
    if date_to:
        query = query.filter(Expense.date <= date_to)
    
    # Sort
    query = query.order_by(Expense.date.desc())
    
    # Paginate
    total = query.count()
    expenses = query.offset((page-1)*limit).limit(limit).all()
    
    return {expenses, pagination}
```

**Performance Optimization:**
- **Indexes:** Add database indexes on frequently filtered columns (category, date, user_id)
- **Query Optimization:** Use ORM eager loading to prevent N+1 queries
- **Caching:** Cache pagination results (60-second TTL)
- **Cursor-based Pagination** (Alternative): Use `WHERE id > last_id` instead of offset (better for large offsets)

---

**Q20: How does admin analytics work? What queries do you run?**

**Answer:**
[See Member 2 Guide, Feature 16 section - Admin Analytics Dashboard]

**Admin-Only Access:**

```python
# Dependency for admin routes
def admin_only(current_user = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=current_user["sub"]).first()
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@router.get("/admin/analytics")
async def get_analytics(admin_user = Depends(admin_only), db: Session = Depends(get_db)):
    # Admin-specific endpoint
```

**Analytics Queries:**

1. **User Growth:**
   ```python
   # Total users
   total_users = db.query(User).count()
   
   # New users this month
   this_month_start = datetime(year=2024, month=1, day=1)
   new_this_month = db.query(User)\
       .filter(User.created_at >= this_month_start)\
       .count()
   
   # Growth rate
   growth_percent = (new_this_month / total_users) * 100 if total_users > 0 else 0
   ```

2. **Spending Trends:**
   ```python
   # Total spending all time
   total_spending = db.query(func.sum(Expense.amount)).scalar() or 0
   
   # By month
   by_month = db.query(
       func.date_trunc('month', Expense.created_at).label('month'),
       func.sum(Expense.amount).label('total')
   ).group_by('month').all()
   
   # By category
   by_category = db.query(
       Expense.category,
       func.sum(Expense.amount).label('total')
   ).group_by(Expense.category).all()
   ```

3. **Popular Destinations:**
   ```python
   # Top destinations by trip count
   popular_destinations = db.query(
       Destination.name,
       func.count(Trip.id).label('trip_count'),
       func.avg(Expense.amount).label('avg_spent')
   ).join(Trip, Trip.destination_id==Destination.id)\
    .join(Expense, Expense.trip_id==Trip.id)\
    .group_by(Destination.id)\
    .order_by(desc('trip_count'))\
    .limit(10)\
    .all()
   ```

**Privacy Considerations:**
- Aggregate data only (no user PII)
- User emails not exposed
- Only summary statistics returned
- Admin dashboard is read-only (can't modify user data)

---

### MEMBER 3: AI Services & Advanced Features

**Q21: Explain the Groq API integration. Why use Groq instead of OpenAI?**

**Answer:**
[See Member 3 Guide, Feature 17 section - AI Trip Chat Assistant]

**Why Groq?**

| Metric | Groq | OpenAI | Gemini |
|--------|------|--------|--------|
| **Speed** | ⚡ Fast (10–20 tokens/sec) | ⭐ Medium (80–100 tokens/sec) | ⭐ Medium (50 tokens/sec) |
| **Cost** | 💰 Cheaper ($0.27/1M tokens) | 💸 Expensive ($0.50/1M tokens) | 💸 Expensive ($0.50/1M tokens) |
| **Models** | Mixtral, Llama-2 | GPT-3.5, GPT-4 | Gemini 1.5 |
| **Use Case** | Fast inference, chat | High quality, reasoning | Multimodal |

**Groq Advantages:**
1. **Speed:** 3–5x faster inference (specialized LPU hardware)
2. **Cost:** 50% cheaper than OpenAI
3. **Latency:** <1 second for chat responses (good for real-time)
4. **Models:** Mixtral-8x7b (balanced), Llama-2-70b (powerful)

**Groq Integration Code:**

```python
# backend/app/services/groq_model_discovery.py

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def chat_with_groq(messages, request_type="general"):
    """
    messages = [
        {"role": "system", "content": "You are a travel advisor..."},
        {"role": "user", "content": "What should I pack for Paris?"},
        {"role": "assistant", "content": "Paris in May is pleasant..."},
        {"role": "user", "content": "What about food?"}
    ]
    """
    
    model = "mixtral-8x7b-32768" if request_type == "general" else "llama2-70b-4096"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500,
        "top_p": 0.9
    }
    
    response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    return data["choices"][0]["message"]["content"]
```

**Error Handling:**

```python
try:
    response = requests.post(GROQ_API_URL, ...)
except requests.Timeout:
    return "Request timed out. Please try again."
except requests.HTTPError as e:
    if e.response.status_code == 401:
        return "API key invalid. Check GROQ_API_KEY"
    elif e.response.status_code == 429:
        return "Rate limit exceeded. Retry in 30 seconds."
    else:
        return f"API error: {e.response.status_code}"
```

**Why is BudgetBound Returning 501?**
- Root cause: `GROQ_API_KEY` not set in `.env`
- Fix: `echo "GROQ_API_KEY=<your-key>" >> backend/.env`
- Get key: https://console.groq.com/keys

---

**Q22: How do you generate PDFs using ReportLab? Why not HTML-to-PDF?**

**Answer:**
[See Member 3 Guide, Feature 18 section - PDF Report Generator]

**ReportLab vs HTML-to-PDF:**

| Approach | ReportLab | WeasyPrint/Puppeteer |
|----------|-----------|---------------------|
| **Type** | Programmatic PDF generation | HTML → PDF |
| **Pros** | Precise layout, no external deps, fast | Familiar HTML/CSS syntax |
| **Cons** | Steeper learning curve | Chromium dependency, slower |
| **Best For** | Complex data → PDF (reports, invoices) | Templates (receipts, emails) |

**Why ReportLab for BudgetBound:**
- Fine-grained control over layout (title page, multi-page report)
- No Chromium dependency (faster, lighter docker image)
- Programmatic table generation (expense breakdown)
- Built-in chart support (pie charts, bar charts)

**ReportLab Example:**

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO

# Create PDF in memory
buffer = BytesIO()
doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch)
story = []

# Add title
title_style = ParagraphStyle('CustomTitle', fontSize=24, textColor=colors.HexColor('#003366'))
story.append(Paragraph("Trip Report: Paris 2024", title_style))
story.append(Spacer(1, 0.3*inch))

# Add table
data = [
    ["Category", "Amount", "Percent"],
    ["Accommodation", "$1,500", "30%"],
    ["Food", "$1,200", "24%"],
    ["Transport", "$800", "16%"],
    ["Activities", "$600", "12%"],
]

table = Table(data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
]))

story.append(table)
story.append(PageBreak())

# Build and get bytes
doc.build(story)
buffer.seek(0)
pdf_bytes = buffer.getvalue()

# Return to frontend
return StreamingResponse(
    iter([pdf_bytes]),
    media_type="application/pdf",
    headers={"Content-Disposition": "attachment; filename=report.pdf"}
)
```

**Key ReportLab Concepts:**
- **SimpleDocTemplate:** PDF container
- **Table:** Structured data with rows/columns
- **TableStyle:** Formatting (colors, borders, alignment)
- **Spacer:** Vertical spacing
- **PageBreak:** Multi-page reports
- **BytesIO:** In-memory file handling (no disk write)

---

**Q23: How do you prevent LLM hallucinations? What's your validation strategy?**

**Answer:**

**Preventing Hallucinations (AI Chat):**

1. **System Prompt Design:**
   ```
   You are a travel budget advisor for BudgetBound.
   
   RULES:
   - Only give advice about trip planning and budgeting
   - Do NOT invent activities or prices not in the provided context
   - If unsure, say "I don't have information about that"
   - Keep responses under 200 words
   ```

2. **Context Injection:**
   ```python
   # Provide factual data upfront
   system_prompt = f"""
   Trip Context:
   - Destination: {trip.destination.name}
   - Budget: ${trip.budget}
   - Duration: {trip.duration} days
   - Real activities: {[a.name for a in trip.destination.activities]}
   - Actual average costs: {expense_breakdown}
   """
   ```

3. **Temperature Tuning:**
   - Packing list: temperature=0.3 (deterministic, follows patterns)
   - Chat: temperature=0.7 (balanced creativity)
   - Never use temperature > 0.8 for factual tasks

4. **Output Validation:**
   ```python
   response = groq_client.chat_with_groq(messages)
   
   # Sanity checks
   if len(response) > 2000:
       response = response[:2000] + "..."  # Cap length
   
   if any(bad_word in response for bad_word in ['guaranteed', 'definitely', 'will happen']):
       # AI making false claims
       return "I can't guarantee outcomes, but here's what typically happens..."
   
   return response
   ```

5. **Fact-Checking Against Database:**
   ```python
   # If AI mentions activity
   mentioned_activities = extract_entities(response, type="activity")
   
   for activity in mentioned_activities:
       db_activity = db.query(Activity).filter_by(name=activity).first()
       if not db_activity:
           # AI hallucinated activity
           response = response.replace(activity, "[unavailable activity]")
   ```

6. **User Feedback Loop:**
   - Allow users to mark responses as incorrect
   - Log hallucinations for model retraining

---

**Q24: Walk me through the explainability service. How do you convert optimization results to human language?**

**Answer:**
[See Member 3 Guide, Feature 3 section - Budget Optimizer Explainability]

**Explainability Service:**

```python
# backend/app/services/explainability.py

def explain_optimization(original, optimized, preferences):
    """
    Inputs:
      original = {category: amount}
      optimized = {category: amount}
      preferences = {category: preference_weight (0-1)}
    
    Output: human-readable explanation
    """
    
    explanations = []
    
    for category in original:
        original_amount = original[category]
        optimized_amount = optimized[category]
        change = optimized_amount - original_amount
        change_pct = (change / original_amount * 100) if original_amount > 0 else 0
        preference = preferences.get(category, 0)
        
        if abs(change) > 1:  # Only mention changes > $1
            if change > 0:
                # Increased
                reason = reason_for_increase(category, preference)
                explanations.append(
                    f"• Increased {category} by ${abs(change):.0f} ({change_pct:.1f}%) {reason}"
                )
            else:
                # Decreased
                reason = reason_for_decrease(category, preference)
                explanations.append(
                    f"• Reduced {category} by ${abs(change):.0f} ({abs(change_pct):.1f}%) {reason}"
                )
    
    return "\n".join(explanations)

def reason_for_increase(category, preference):
    if category == "activities" and preference > 0.5:
        return "to maximize your experiences"
    elif category == "accommodation" and preference > 0.5:
        return "for better comfort"
    else:
        return "to maintain adequate coverage"

def reason_for_decrease(category, preference):
    if category == "food":
        return "through efficient meal planning"
    elif category == "transport":
        return "via optimized routing"
    else:
        return "to balance other priorities"
```

**Example Output:**

```
Original Budget:
- Accommodation: $2,000 (40%)
- Food: $1,500 (30%)
- Transport: $500 (10%)
- Activities: $1,000 (20%)

User Preferences: More activities, less food

Optimization Explanation:
• Reduced Food by $300 (20%) through efficient meal planning
• Increased Activities by $300 (30%) to maximize your experiences
• Maintained Transport at adequate levels
• Kept Accommodation for comfortable lodging

Result: Same $5,000 budget, optimized for your preferences!
```

**Why This Matters:**
- Builds user trust ("I understand why this was changed")
- Enables learning ("I see where my budget goes")
- Personalizes experience ("Uses my preferences to justify changes")

---

**Q25: What's the difference between streaming and non-streaming LLM responses? When do you use each?**

**Answer:**

**Non-Streaming (Standard):**

```python
# Wait for entire response, then return
response = groq_client.chat_with_groq(messages)
return {"response": response}

# User sees: [Loading...] → [Full response appears all at once]
```

**Pros:**
- Simpler implementation
- Reliable response (full data available)

**Cons:**
- High latency (can be 5–10 seconds for long responses)
- Poor UX (user waits for complete response)

---

**Streaming (Real-Time):**

```python
# Stream response token-by-token
@router.post("/ai/chat/stream")
async def chat_stream(chat_input, ...):
    
    # Setup connection
    def generate():
        for token in groq_client.stream_response(messages):
            yield f"data: {json.dumps({'token': token})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

# Frontend (JavaScript)
const eventSource = new EventSource("/api/ai/chat/stream?message=...");
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    displayText += data.token;
    updateUI(displayText);
};
```

**Pros:**
- Low latency (user sees response appearing immediately)
- Better UX (chat feel, like human typing)

**Cons:**
- More complex (Server-Sent Events or WebSocket)
- Can't edit response (already partially displayed)

---

**When to Use:**

- **Streaming:** Chat, real-time features (where latency matters)
- **Non-Streaming:** Background tasks, batch processing, report generation

**For BudgetBound:**
- Chat: streaming (good UX)
- Packing list generation: non-streaming (can wait 2–3 seconds)
- Budget explanation: non-streaming (50–100 words, fast)

---

**Q26: What happens when an external API (Groq, OpenWeatherMap) is down? How do you handle failures gracefully?**

**Answer:**

**Failure Handling Strategy:**

1. **Timeout + Retry Logic:**
   ```python
   from requests.adapters import HTTPAdapter
   from urllib3.util.retry import Retry
   
   def create_session():
       session = requests.Session()
       retry = Retry(
           total=3,  # Retry 3 times
           backoff_factor=0.5,  # 0.5s, 1s, 2s delays
           status_forcelist=[500, 502, 503, 504]  # Retry on server errors
       )
       adapter = HTTPAdapter(max_retries=retry)
       session.mount('https://', adapter)
       return session
   
   session = create_session()
   response = session.post(API_URL, timeout=5)  # 5-second timeout
   ```

2. **Graceful Fallback:**
   ```python
   # Weather API down?
   try:
       weather = fetch_weather_api(destination)
   except requests.Timeout:
       # Return cached weather from last 24h
       cached = db.query(WeatherCache).filter_by(destination_id=dest_id).first()
       if cached:
           return cached.weather_json
       else:
           # No cache, return generic weather
           return {"message": "Weather data unavailable, assume mild climate"}
   ```

3. **Partial Failures (Graceful Degradation):**
   ```python
   # Generate report even if some components fail
   try:
       packing_list = generate_packing_list(trip)
   except Exception as e:
       logging.error(f"Packing list generation failed: {e}")
       packing_list = None  # Will be omitted from PDF
   
   try:
       carbon_footprint = calculate_carbon_footprint(trip)
   except Exception as e:
       logging.error(f"Carbon calculation failed: {e}")
       carbon_footprint = None
   
   # Build PDF with whatever data is available
   pdf = generate_pdf(trip, itinerary=trip.itinerary, packing=packing_list, carbon=carbon_footprint)
   ```

4. **Error Logging + Monitoring:**
   ```python
   import logging
   
   logger = logging.getLogger(__name__)
   
   try:
       response = requests.post(API_URL, ...)
   except Exception as e:
       logger.error(f"API call failed: {str(e)}", exc_info=True)
       sentry.capture_exception(e)  # Send to error tracking service
       return "Service temporarily unavailable"
   ```

5. **User-Facing Error Messages:**
   - **Good:** "Weather data unavailable. Using cached data from last week."
   - **Bad:** "Traceback: requests.Timeout..."

---

**Q27: Explain the database schema relationships. How do foreign keys work?**

**Answer:**

**Foreign Key Example:**

```python
# Models
class User(Base):
    id = Column(Integer, primary_key=True)
    email = Column(String)

class Trip(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String)
    
    # Relationship
    user = relationship("User", back_populates="trips")

class Expense(Base):
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    amount = Column(Float)
    
    # Relationship
    trip = relationship("Trip", back_populates="expenses")

# Add back-reference
User.trips = relationship("Trip", back_populates="user")
Trip.expenses = relationship("Expense", back_populates="trip")
```

**How It Works:**

1. **Foreign Key Constraint:**
   - `Trip.user_id` must exist in `User.id`
   - Can't create Trip with non-existent user_id
   - Can't delete User if they have Trips (cascade options)

2. **Cascade Options:**
   ```python
   # Cascade delete: deleting User deletes all their Trips
   user_trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")
   
   # Set NULL: deleting User sets Trip.user_id to NULL (if nullable)
   user_trips = relationship("Trip", back_populates="user", foreign_keys="Trip.user_id", passive_deletes=True)
   
   # Restrict: can't delete User if they have Trips (raises error)
   # (default behavior, no cascade specified)
   ```

3. **Querying with Relationships:**
   ```python
   # Get user + all trips (eager load)
   user = db.query(User).filter_by(id=1).first()
   for trip in user.trips:
       print(trip.name)
   
   # Join query (explicit)
   user_trips = db.query(User).join(Trip).filter(Trip.user_id==1).all()
   
   # Prevent N+1 query problem
   user = db.query(User).options(joinedload(User.trips)).filter_by(id=1).first()
   ```

**Referential Integrity:**

```
User:        Trip:           Expense:
id  email    id  user_id name id trip_id amount
1   a@a.com  1   1       Paris 1   1      50
2   b@b.com  2   2       Rome  2   1      75
                           3   2      100

Foreign key: Trip.user_id → User.id
- Can't create Trip with user_id=999 (no such user)
- Can't delete User 1 (has Trip 1)
```

---

### Q28: What are the security concerns? How do you mitigate them?

**Answer:**

**Top Security Risks & Mitigations:**

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **SQL Injection** | Attacker modifies SQL query | Use ORM (SQLAlchemy) + parameterized queries |
| **XSS (Cross-Site Scripting)** | Attacker injects JavaScript | Sanitize user input, use httpOnly cookies |
| **CSRF (Cross-Site Request Forgery)** | Attacker makes unauthorized requests | CSRF tokens, SameSite cookies |
| **Weak Passwords** | Brute force, dictionary attacks | Enforce strength (8+ chars, uppercase, digit) |
| **Plaintext Passwords** | Database leak exposes credentials | Hash with bcrypt (12 rounds) |
| **Token Theft** | JWT stolen, impersonates user | Short expiry (15 min), refresh rotation, httpOnly |
| **Exposed Secrets** | API keys, DB credentials leaked | Environment variables, secrets manager |
| **Rate Limiting Missing** | Brute force, DoS attacks | Rate limit login (5/15min), API calls (100/hour) |
| **No HTTPS** | Traffic intercepted (MITM) | Enforce HTTPS in production, secure cookies |
| **NoN-Audit Logs** | No way to detect attacks | Log auth events, API calls, data changes |

**Example Mitigations:**

```python
# 1. SQL Injection Prevention (ORM)
# BAD
query = f"SELECT * FROM users WHERE email = '{email}'"  # Vulnerable!

# GOOD
user = db.query(User).filter_by(email=email).first()  # Safe (parameterized)

# 2. Password Hashing
# BAD
user.password = user_input_password  # Plaintext!

# GOOD
user.password_hash = bcrypt.hash(user_input_password, rounds=12)

# 3. CSRF Protection
# Frontend: include CSRF token in form
<form method="POST">
    <input type="hidden" name="csrf_token" value="{token}">
</form>

# Backend: validate token
@router.post("/api/trip")
async def create_trip(csrf_token: str, ...):
    if not verify_csrf_token(csrf_token):
        raise HTTPException(status_code=403, detail="CSRF token invalid")

# 4. Rate Limiting (Flask-Limiter or similar)
@limiter.limit("5/15minutes")
@router.post("/auth/login")
async def login(...):
    ...

# 5. Environment Variables (Secrets)
# BAD
GROQ_API_KEY = "gsk_abc123def456"  # Hardcoded!

# GOOD
import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set in environment")

# 6. HTTPS + Secure Cookies
# Production nginx config
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Secure cookie flags
    add_header Set-Cookie "...;Secure;HttpOnly;SameSite=Strict";
}
```

---

**Q29: What's the deployment checklist? How do you go live?**

**Answer:**

**Pre-Deployment:**
- ✓ All tests passing (unit + integration)
- ✓ Code review approved
- ✓ Environment variables set (.env configured)
- ✓ Database migrations run (alembic upgrade head)
- ✓ HTTPS certificate obtained (Let's Encrypt)
- ✓ Security audit completed (no hardcoded secrets)
- ✓ Load testing done (can handle expected traffic?)
- ✓ Monitoring set up (error tracking, metrics)
- ✓ Backup strategy planned (DB backup, automated)

**Deployment Steps:**

1. **Backend Deployment:**
   ```bash
   # Build Docker image
   docker build -t budgetbound-backend:v1.0 .
   
   # Push to registry (AWS ECR, DockerHub)
   docker push budgetbound-backend:v1.0
   
   # Deploy to production
   # If Kubernetes:
   kubectl set image deployment/backend backend=budgetbound-backend:v1.0
   
   # If Docker Swarm:
   docker service update --image budgetbound-backend:v1.0 backend
   
   # If EC2:
   ssh ec2-user@prod.example.com
   docker pull budgetbound-backend:v1.0
   docker run -d -e DATABASE_URL=... budgetbound-backend:v1.0
   ```

2. **Frontend Deployment:**
   ```bash
   # Build optimized React bundle
   npm run build
   
   # Upload to S3
   aws s3 sync build/ s3://budgetbound-frontend/ --delete
   
   # Invalidate CloudFront cache
   aws cloudfront create-invalidation --distribution-id E123ABC --paths "/*"
   ```

3. **Database Migrations:**
   ```bash
   # Run Alembic migrations
   alembic upgrade head
   ```

4. **Smoke Tests:**
   - ✓ Login endpoint works
   - ✓ Create trip endpoint works
   - ✓ Fetch dashboard works

5. **Monitoring Alerts:**
   - ✓ Set up alerts for high error rates (>1% 5xx errors)
   - ✓ Set up alerts for slow responses (>1 second p95 latency)
   - ✓ Set up alerts for DB connection issues

6. **Rollback Plan:**
   ```bash
   # If deployment breaks, rollback to previous version
   kubectl rollout undo deployment/backend
   # Or
   docker service rollback backend
   ```

---

**Q30: What would you do differently if you built this again? What did you learn?**

**Answer:**

**If Building Again:**

1. **Start with Tests:**
   - ✓ Test-driven development (write tests first)
   - ✗ Current: minimal test coverage
   - Impact: Would catch bugs earlier, easier refactoring

2. **API Design:**
   - ✓ Use GraphQL instead of REST (more flexible for frontend)
   - ✗ Current: REST endpoints can require N+1 queries
   - Alternative: Keep REST but add `.include` parameters for eager loading

3. **Database:**
   - ✓ Better indexing upfront (pagination performance)
   - ✓ Denormalization for analytics (pre-computed aggregates)
   - ✗ Current: Some queries slow for large datasets

4. **Frontend State Management:**
   - ✓ Use Redux or Zustand (centralized state)
   - ✗ Current: May have prop drilling issues
   - Impact: Better code organization, easier debugging

5. **AI Integration:**
   - ✓ Use prompt caching (Groq, OpenAI support it)
   - ✓ Better prompt engineering upfront (reduce hallucinations)
   - ✓ Implement user feedback loop for model improvement
   - ✗ Current: Packing list prompts could be optimized

6. **Infrastructure:**
   - ✓ Use IaC (Infrastructure as Code, Terraform)
   - ✓ Auto-scaling configuration (handle traffic spikes)
   - ✓ CDN for static assets (React build)
   - ✗ Current: Manual deployment steps

7. **Monitoring:**
   - ✓ Set up observability from day 1 (logs, metrics, traces)
   - ✗ Current: May lack comprehensive monitoring

**Key Learnings:**

1. **Algorithm Design Matters:** TSP solver accuracy & performance crucial for user experience
2. **External API Reliability:** Need fallbacks, retries, caching (Groq, OpenWeatherMap failures)
3. **Authorization is Hard:** Easy to forget permission checks, leading to data leaks
4. **Frontend-Backend Alignment:** API design should match frontend needs (prevent N+1)
5. **Testing Saves Time:** Would pay off immediately in debugging

---

## Viva Tips & Tricks

**General Advice:**

1. **Don't Memorize Code:** Understand the logic. You can look up syntax.
2. **Use Diagrams:** Draw architecture, data flow, algorithm steps. Examiners love visuals.
3. **Be Honest:** "I don't know" is better than bullshitting.
4. **Answer the Question:** Don't go off on tangents.
5. **Speak Clearly:** Imagine explaining to a colleague, not a test.
6. **Use Examples:** Real scenarios (Paris trip, $5000 budget) make explanation clearer.
7. **Cite Code:** Reference specific files/line numbers when explaining.
8. **Know Your Weaknesses:** 501 errors, minimal tests, etc. Have an explanation ready.

**During Viva:**

- Listen carefully to the question
- Pause before answering (collect thoughts)
- Ask for clarification if confused ("Do you mean X or Y?")
- Give time for follow-up questions
- Offer to show code if needed (demo app)

---

**End of Viva Preparation Guide**

---

## Summary

This guide covers 30 technical questions spanning:
- **10 General:** Project overview, features, tech stack, architecture
- **10 Member 1:** Algorithms, trip planning, optimization, weather, carbon
- **10 Member 2:** Auth, database, APIs, permissions, notifications
- **10 Member 3:** LLM integration, PDFs, AI services, error handling

**Time Allocation (90-min viva):**
- General: 15 min
- Member 1: 25 min
- Member 2: 25 min
- Member 3: 20 min
- Buffer: 5 min

**Final Checklist Before Viva:**
- ✓ Read all 3 member guides (4_MEMBER_1, 5_MEMBER_2, 6_MEMBER_3)
- ✓ Review 3_FEATURE_TO_CODE_MAP (code references)
- ✓ Read through actual codebase (repos.py, models.py, services/)
- ✓ Practice drawing architecture diagrams
- ✓ Prepare demo (login, create trip, generate report)
- ✓ Know your features inside-out

Good luck! 🚀

---

**End of Document**
