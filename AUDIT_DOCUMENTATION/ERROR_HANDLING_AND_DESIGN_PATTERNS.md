# BudgetBound: Error Handling, Exception Handling & Design Patterns

Comprehensive documentation of all error handling strategies, exception patterns, and design patterns used throughout the BudgetBound project (backend + frontend).

---

## Table of Contents

1. [Backend Error Handling](#backend-error-handling)
2. [Frontend Error Handling](#frontend-error-handling)
3. [Design Patterns](#design-patterns)
4. [Exception Handling Examples](#exception-handling-examples)
5. [Error Recovery Strategies](#error-recovery-strategies)

---

## Backend Error Handling

### 1. **HTTP Exception Handling (FastAPI)**

#### Pattern: HTTPException for API Responses

```python
# backend/app/routers/auth.py
from fastapi import HTTPException, status

# Example 1: User already exists (400 Bad Request)
existing_user = db.query(models.User).filter(models.User.email == user_in.email).first()
if existing_user:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="A user with this email address already exists."
    )

# Example 2: Authentication failure (401 Unauthorized)
if not user or not auth.verify_password(credentials.password, user.hashed_password):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Example 3: Resource not found (404 Not Found)
raise HTTPException(
    status_code=404,
    detail="Selected destination not found in database."
)

# Example 4: Business logic violation (422 Unprocessable Entity)
raise HTTPException(
    status_code=422,
    detail=(
        f"'{dest_obj.name}' for {req.days} days exceeds your budget of ₹{req.budget:,.0f} "
        f"(estimated ₹{est:,.0f})."
    )
)

# Example 5: Admin access required (403 Forbidden)
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Admin access required."
)
```

**HTTP Status Codes Used:**
- `200` — OK (successful request)
- `201` — Created (resource created)
- `400` — Bad Request (validation error)
- `401` — Unauthorized (auth failure)
- `403` — Forbidden (insufficient permissions)
- `404` — Not Found (resource missing)
- `422` — Unprocessable Entity (business logic violation)
- `500` — Internal Server Error

---

### 2. **JWT Token Validation**

#### Pattern: Try-Except with Custom Exception

```python
# backend/app/auth.py
from jose import JWTError, jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Attempt JWT decoding
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        
        # Check if required field is present
        if email is None:
            raise credentials_exception
            
    except JWTError:  # Catch JWT-specific errors (expired, invalid signature, etc.)
        raise credentials_exception
    
    # Database lookup
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user
```

**Error Cases Handled:**
- Token expired
- Invalid signature
- Malformed token
- Missing claims
- User not found in database

---

### 3. **Database Connection Fallback**

#### Pattern: Graceful Degradation

```python
# backend/app/database.py
from sqlalchemy.exc import OperationalError

engine = None
is_sqlite = False

try:
    # Attempt to initialize PostgreSQL engine
    if settings.DATABASE_URL.startswith("postgresql"):
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5}  # Short timeout
        )
        # Test connection
        with engine.connect() as conn:
            logger.info("Successfully connected to PostgreSQL database.")
    else:
        raise ValueError("Not a PostgreSQL URL")
        
except (OperationalError, Exception) as e:
    logger.warning(
        f"PostgreSQL connection failed: {e}. "
        f"Falling back to SQLite database at {settings.SQLITE_FALLBACK_URL}"
    )
    is_sqlite = True
    engine = create_engine(
        settings.SQLITE_FALLBACK_URL,
        connect_args={"check_same_thread": False}
    )
```

**Fallback Strategy:**
- Primary: PostgreSQL (production database)
- Fallback: SQLite (development/local database)
- Graceful: System continues with reduced features instead of crashing

---

### 4. **Database Session Management**

#### Pattern: Context Manager (Finally Block)

```python
# backend/app/database.py
def get_db():
    db = SessionLocal()
    try:
        yield db  # Session available to route handler
    finally:
        db.close()  # Always close connection, even if exception occurs
```

**Why Finally Block:**
- Ensures database connection is released
- Prevents connection leaks
- Executes regardless of success or failure

---

### 5. **Financial Validation**

#### Pattern: Validation Object with Error Accumulation

```python
# backend/app/services/financial_validator.py
class FinancialValidator:
    def __init__(self, budget_limit: float, num_days: int):
        self.budget_limit = Decimal(str(budget_limit))
        self.num_days = num_days
        self.errors: List[str] = []  # Accumulate errors
        self.warnings: List[str] = []  # Non-critical issues

    def validate_expense_item(self, value: float, category: str) -> bool:
        """Check that a single expense is non-negative."""
        if value < 0:
            self.errors.append(f"{category}: negative cost Rs. {value:.2f}")
            return False
        return True

    def validate_daily_costs(self, days: List[Dict]) -> Tuple[float, bool]:
        """Validate and sum daily costs, collecting errors."""
        total = Decimal('0')
        is_valid = True
        
        for day in days:
            day_num = day.get('day_number')
            activities = day.get('activities', [])
            
            for activity in activities:
                cost = activity.get('cost', 0)
                try:
                    cost = float(cost)
                except (TypeError, ValueError):
                    self.errors.append(
                        f"Day {day_num}: invalid cost format '{cost}'"
                    )
                    is_valid = False
                    continue
                
                if cost < 0:
                    self.errors.append(
                        f"Day {day_num}: negative cost {cost}"
                    )
                    is_valid = False

        return (float(total), is_valid)
```

**Benefits:**
- Collects all validation errors at once (vs. failing on first error)
- User sees complete list of issues
- Distinguishes between errors (critical) and warnings (non-critical)

---

### 6. **Itinerary Validation**

#### Pattern: Try-Except with Contextual Error Messages

```python
# backend/app/services/multistop_calculator.py
def validate_itinerary_structure(itinerary, stops):
    """Validate itinerary against stops."""
    errors = []
    warnings = []
    
    legs = itinerary.get("legs", [])
    if len(legs) != len(stops):
        errors.append(f"Expected {len(stops)} legs, got {len(legs)}")
        return _validation_result(False, errors, warnings)
    
    for i, (leg, dest) in enumerate(zip(legs, stops)):
        # Validate activities have costs
        for act in leg.get("activities", []):
            if not act.get("title"):
                errors.append(
                    f"Stop '{dest}' Day {i}: activity missing title"
                )
                continue
            
            if "cost" not in act:
                errors.append(
                    f"Stop '{dest}' Day {i} '{act.get('title')}': missing cost"
                )
                continue
            
            # Type conversion with error handling
            cost = act.get("cost", 0)
            try:
                cost = float(cost)
            except (TypeError, ValueError):
                errors.append(
                    f"Stop '{dest}': invalid cost format '{cost}'"
                )
```

---

### 7. **Database Migration with Error Suppression**

#### Pattern: Try-Except for Non-Critical Operations

```python
# backend/main.py
from sqlalchemy import text

with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE trips ADD COLUMN status VARCHAR DEFAULT 'Planned'"))
        logger.info("Database migration: Added status column.")
    except Exception:
        pass  # Column likely already exists
    
    try:
        conn.execute(text("ALTER TABLE trips ADD COLUMN start_date VARCHAR"))
        logger.info("Database migration: Added start_date column.")
    except Exception:
        pass  # Column likely already exists
    
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
```

**Rationale:**
- Non-critical failures shouldn't crash the application
- Migrations may partially fail if columns already exist
- Logging provides debugging information

---

### 8. **Date Parsing with Fallback**

#### Pattern: Try-Except with Default Values

```python
# backend/main.py
if db_trip.start_date:
    try:
        month_val = int(db_trip.start_date.split("-")[1])
    except Exception:
        # If parsing fails, use current month as default
        month_val = datetime.datetime.now().month
```

---

## Frontend Error Handling

### 1. **Authentication Context with Error State**

#### Pattern: Try-Catch with Error State Management

```typescript
// frontend/src/context/AuthContext.tsx
const fetchUser = async () => {
  const storedToken = localStorage.getItem('token');
  if (storedToken) {
    try {
      const response = await api.get('/api/auth/me');
      setUser(response.data);
    } catch (err) {
      console.error("Token verification failed", err);
      logout();  // Invalidate session on failure
    }
  }
  setLoading(false);
};

const login = async (email: string, password: string) => {
  setLoading(true);
  setError(null);  // Clear previous errors
  try {
    const response = await api.post('/api/auth/login-json', { email, password });
    const { access_token, user } = response.data;
    
    localStorage.setItem('token', access_token);
    setToken(access_token);
    setUser(user);
  } catch (err: any) {
    const errorMsg = err.response?.data?.detail || "Login failed";
    setError(errorMsg);
    throw new Error(errorMsg);
  } finally {
    setLoading(false);
  }
};

const logout = () => {
  localStorage.removeItem('token');
  setToken(null);
  setUser(null);
  setError(null);
};
```

**State Management:**
- `error`: Current error message (or null)
- `loading`: Request in progress
- `clearError()`: Manual error dismissal

---

### 2. **Protected Routes with Error Boundaries**

#### Pattern: Conditional Rendering Based on Auth State

```typescript
// frontend/src/App.tsx
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <RouteFallbackLoader />;  // Loading state
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;  // Redirect on auth failure
  }

  return <Layout>{children}</Layout>;
};
```

**Error Handling:**
- Show loader while auth state is being determined
- Redirect unauthenticated users to login
- Authenticated users see protected content

---

### 3. **API Error Interceptor**

#### Pattern: Centralized Error Handling

```typescript
// frontend/src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000'
});

// Request interceptor: Add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

**Centralized Benefits:**
- Consistent error handling across all API calls
- Automatic token refresh/logout on auth failure
- Single place to modify error behavior

---

### 4. **Component Error Handling**

#### Pattern: Try-Catch in Async Handlers

```typescript
// frontend/src/pages/BudgetPlanner.tsx
const handleSubmit = async (formData: TripCreate) => {
  try {
    setLoading(true);
    setError(null);
    
    const response = await api.post('/api/trips', formData);
    
    // Success handling
    setTripId(response.data.id);
    navigate(`/trip/${response.data.id}`);
  } catch (err: any) {
    const errorMsg = err.response?.data?.detail || "Failed to create trip";
    setError(errorMsg);
    console.error("Trip creation error:", err);
  } finally {
    setLoading(false);
  }
};

return (
  <form onSubmit={handleSubmit}>
    {error && <ErrorAlert message={error} onClose={() => setError(null)} />}
    <input type="text" placeholder="Trip name" />
    <button disabled={loading}>
      {loading ? 'Creating...' : 'Create Trip'}
    </button>
  </form>
);
```

---

### 5. **Data Validation Before API Call**

#### Pattern: Client-Side Validation

```typescript
// frontend/src/pages/ExpenseTracker.tsx
const handleAddExpense = (expense: ExpenseCreate) => {
  // Validation
  if (!expense.category) {
    setError("Please select a category");
    return;
  }
  
  if (expense.amount <= 0) {
    setError("Amount must be positive");
    return;
  }
  
  if (!expense.date) {
    setError("Please select a date");
    return;
  }
  
  // If all validations pass, make API call
  mutate(expense);
};
```

**Benefits:**
- Prevents unnecessary API calls
- Provides immediate feedback to user
- Reduces server load

---

## Design Patterns

### 1. **Dependency Injection (FastAPI)**

#### Pattern: Function Dependencies

```python
# backend/app/routers/trips.py
@router.get("/trips/{trip_id}")
async def get_trip(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Dependencies are injected by FastAPI."""
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id  # User-scoped query
    ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return trip
```

**Benefits:**
- Automatic dependency resolution
- Easy testing (mock dependencies)
- Clear function signatures
- User-scoped access control

---

### 2. **Strategy Pattern (Algorithm Selection)**

#### Pattern: Weather Intelligence Based on Season

```python
# backend/app/routers/trips.py
def calculate_weather_intelligence(dest, month: int = None):
    """Strategy pattern: select weather data based on destination category and season."""
    
    # Determine season
    if month in [12, 1, 2]:
        season = "Winter"
    elif month in [3, 4, 5]:
        season = "Summer"
    elif month in [6, 7, 8, 9]:
        season = "Monsoon"
    else:
        season = "Post-Monsoon"

    # Strategy: Select weather params based on (season, category)
    cat = (dest.category or "").lower()
    
    if season == "Winter":
        if "nature" in cat or "trek" in cat:
            return {"temp": "5°C – 15°C", "crowd": "High", "rain": "5% - 10%"}
        else:
            return {"temp": "18°C – 26°C", "crowd": "High", "rain": "0% - 5%"}
    elif season == "Summer":
        if "nature" in cat or "trek" in cat:
            return {"temp": "15°C – 22°C", "crowd": "High", "rain": "5% - 15%"}
        else:
            return {"temp": "32°C – 42°C", "crowd": "Low", "rain": "0% - 10%"}
    # ... more strategies
```

---

### 3. **Service Layer Pattern**

#### Pattern: Business Logic Separation

```python
# backend/app/services/financial_validator.py
class FinancialValidator:
    """Service: encapsulates financial validation logic."""
    
    def validate(self) -> Dict[str, Any]:
        """Main validation orchestrator."""
        errors = []
        warnings = []
        
        # Delegate to specific validators
        if not self.validate_expense_item(value, category):
            # Error already added
            pass
        
        if not self.validate_daily_costs(days):
            # Error already added
            pass
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

# Usage in router:
validator = FinancialValidator(budget, days)
result = validator.validate()
```

**Benefits:**
- Separates business logic from HTTP handling
- Reusable across multiple routes
- Easier to test

---

### 4. **Factory Pattern (Object Creation)**

#### Pattern: Trip Creation with Nested Objects

```python
# backend/app/routers/trips.py
@router.post("/trips", response_model=schemas.TripResponse)
async def create_trip(trip_data: schemas.TripCreate, db: Session = Depends(get_db)):
    """Factory: creates Trip with related Itineraries."""
    
    # Create parent
    db_trip = models.Trip(
        name=trip_data.name,
        destination_id=trip_data.destination_id,
        budget=trip_data.budget,
        days=trip_data.days
    )
    db.add(db_trip)
    db.flush()  # Get trip ID before creating children
    
    # Create children (itineraries)
    for i, itinerary_data in enumerate(trip_data.itineraries):
        db_itinerary = models.Itinerary(
            trip_id=db_trip.id,
            day_number=i + 1,
            activities=itinerary_data.activities
        )
        db.add(db_itinerary)
    
    db.commit()
    db.refresh(db_trip)
    return db_trip
```

---

### 5. **Observer Pattern (React Hooks)**

#### Pattern: State Change Listeners

```typescript
// frontend/src/context/AuthContext.tsx
useEffect(() => {
  // Observer: runs when token changes
  const storedToken = localStorage.getItem('token');
  if (storedToken) {
    try {
      const response = api.get('/api/auth/me');
      setUser(response.data);
    } catch (err) {
      logout();
    }
  }
}, []);  // Dependency array: triggers on mount
```

**Benefits:**
- Automatic re-fetching when dependencies change
- Clean separation of concerns
- Predictable side effects

---

### 6. **Validation Object Pattern**

#### Pattern: Encapsulated Validation State

```python
# backend/app/schemas.py
class PersonalizedPlanValidation(BaseModel):
    """Validation result object."""
    is_valid: bool
    score: float  # 0-100
    errors: List[str] = []  # Critical issues
    warnings: List[str] = []  # Non-critical issues
    checks_passed: dict = {}  # {"day_count": True, ...}
```

---

### 7. **Builder Pattern (Trip Construction)**

#### Pattern: Fluent API for Complex Objects

```python
# Conceptual example (not implemented, but good for Trip creation)
trip_builder = TripBuilder()
    .with_destination("Paris")
    .with_budget(5000)
    .with_days(7)
    .with_comfort_level(75)
    .build()
```

---

## Exception Handling Examples

### Example 1: Multi-Level Exception Handling

```python
# Backend: Trip creation with multiple validation layers
@router.post("/trips", response_model=schemas.TripResponse)
async def create_trip(
    trip_data: schemas.TripCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Error handling flow:
    1. Schema validation (FastAPI automatic)
    2. Business logic validation
    3. Database constraints
    4. HTTP response
    """
    
    # Level 1: Destination exists
    dest = db.query(models.Destination).filter_by(id=trip_data.destination_id).first()
    if not dest:
        raise HTTPException(
            status_code=404,
            detail="Destination not found"
        )
    
    # Level 2: Budget feasibility
    estimated_cost = dest.avg_travel_cost + (dest.avg_hotel_cost * trip_data.days)
    if trip_data.budget < estimated_cost:
        raise HTTPException(
            status_code=422,
            detail=f"Budget {trip_data.budget} too low for {trip_data.days} days (estimated {estimated_cost})"
        )
    
    # Level 3: Create trip
    try:
        db_trip = models.Trip(**trip_data.dict())
        db.add(db_trip)
        db.commit()
        db.refresh(db_trip)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Failed to create trip. Database error."
        )
    
    return db_trip
```

---

### Example 2: Frontend Error Recovery

```typescript
// Frontend: Fetch with automatic retry
async function fetchWithRetry(url: string, maxRetries: number = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return response.json();
      }
      
      if (response.status === 401) {
        // Auth failure is not retryable
        throw new Error("Unauthorized");
      }
      
      // Other errors: retry with exponential backoff
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
        continue;
      }
    } catch (err) {
      if (i === maxRetries - 1) {
        throw err;  // Final attempt failed
      }
    }
  }
}
```

---

## Error Recovery Strategies

### 1. **Database Connection Recovery**

```python
# Automatic fallback from PostgreSQL to SQLite
is_sqlite = False

try:
    engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})
    with engine.connect() as conn:
        logger.info("PostgreSQL connected")
except Exception as e:
    logger.warning(f"PostgreSQL failed: {e}. Using SQLite fallback.")
    is_sqlite = True
    engine = create_engine(SQLITE_FALLBACK_URL)
```

---

### 2. **Token Refresh Strategy**

```typescript
// Automatic token refresh on 401
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Attempt to refresh token
        const response = await api.post('/api/auth/refresh');
        localStorage.setItem('token', response.data.access_token);
        
        // Retry original request
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);
```

---

### 3. **Validation Error Recovery**

```python
# Accumulate all errors instead of failing on first one
validator = FinancialValidator(budget, days)
result = validator.validate()

if not result["is_valid"]:
    # Return all errors to client
    raise HTTPException(
        status_code=422,
        detail={
            "errors": result["errors"],
            "warnings": result["warnings"]
        }
    )
```

---

## Summary Table

| Pattern | Location | Purpose |
|---------|----------|---------|
| HTTPException | Backend routers | API error responses |
| Try-Except-Finally | Database, Auth | Resource cleanup |
| Validation Objects | Services | Error accumulation |
| Dependency Injection | FastAPI | Clean code architecture |
| Strategy Pattern | Weather calc | Algorithm selection |
| Service Layer | Financial validator | Business logic separation |
| Error State | Frontend context | Error UI display |
| API Interceptor | Frontend API client | Centralized error handling |
| Protected Routes | Frontend router | Auth-based access control |

---

## Best Practices

✅ **Do:**
- Use specific HTTP status codes
- Collect all validation errors before responding
- Log errors with context for debugging
- Provide clear, actionable error messages
- Gracefully degrade (fallback to SQLite)
- Clean up resources in finally blocks
- Separate business logic from HTTP handling

❌ **Don't:**
- Silently catch exceptions without logging
- Return generic "Error" messages
- Leave database connections open
- Expose internal errors to API clients
- Mix error handling with business logic
- Use bare `except` clauses
- Ignore database migration failures
