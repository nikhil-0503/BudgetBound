# BudgetBound: Member 2 Responsibility & Explanation Guide

**Member:** 2 (User Management & Infrastructure)  
**Complexity Score:** 14.4/42.6 (33.8% of total workload)  
**Responsibility Tier:** Lead ownership of authentication, user infrastructure, and CRUD operations  
**Owned Features:** 8 features + 2 system components

---

## Owned Features Overview

| # | Feature | Backend Files | Frontend Files | Complexity | Status |
|---|---------|---|---|-----------|--------|
| 11 | User Authentication | `auth.py`, `routers/auth.py` | Login.tsx, Register.tsx, ForgotPasswordModal.tsx, Layout.tsx | 3 | ✅ Full |
| 12 | User Dashboard | `routers/trips.py` (dashboard endpoints) | Dashboard.tsx, SavedTrips.tsx, UserProfilePage.tsx | 2 | ✅ Full |
| 13 | Trip Sharing | `routers/trips.py` (share endpoints) | ShareModal.tsx, SharedTripView.tsx | 4 | ✅ Full |
| 14 | Expense History & Export | `routers/expenses.py`, `pdf_generator.py` | ExpenseTracker.tsx, DocumentManager.tsx | 3 | ✅ Full |
| 15 | Notifications Dashboard | `routers/notifications.py` | NotificationsPage.tsx, MarkdownMessage.tsx, Layout.tsx | 3 | ✅ Full |
| 4 | Budget Alerts (Integration) | `routers/budget_alerts.py` | ExpenseTracker.tsx, BudgetHealthMeter.tsx | 2 | ✅ Full |
| 6 | Destination Explorer | `routers/destinations.py` | DestinationExplorer.tsx, DestinationDetail.tsx | 2 | ✅ Full |
| 7 | Currency Converter | (implicit in trip setup) | CurrencyConverter.tsx, BudgetPlanner.tsx (Member 1) | 2 | ✅ Full |
| **Total** | | | | **22.4** | |

## Frontend Files Owned

**Pages:**
| File | Location | LOC | Purpose |
|------|----------|-----|---------|
| Login.tsx | `frontend/src/pages/Login.tsx` | 139 | User login form with email/password, token handling |
| Register.tsx | `frontend/src/pages/Register.tsx` | 159 | User registration form with validation, password strength |
| Dashboard.tsx | `frontend/src/pages/Dashboard.tsx` | 638 | Main user dashboard with trip summary, budget overview, recent activity |
| SavedTrips.tsx | `frontend/src/pages/SavedTrips.tsx` | 609 | Trip history, filtering, sorting, trip management |
| ExpenseTracker.tsx | `frontend/src/pages/ExpenseTracker.tsx` | 627 | Expense CRUD, burn rate tracking, projections, category charts |
| NotificationsPage.tsx | `frontend/src/pages/NotificationsPage.tsx` | 231 | Notification center with mark-as-read, filtering, delete |
| UserProfilePage.tsx | `frontend/src/pages/UserProfilePage.tsx` | 358 | User profile settings, preferences, account management |
| SharedTripView.tsx | `frontend/src/pages/SharedTripView.tsx` | 385 | View shared trips with read/edit permissions |
| DestinationExplorer.tsx | `frontend/src/pages/DestinationExplorer.tsx` | 311 | Browse destinations with filters (budget, climate, continent) |
| CurrencyConverter.tsx | `frontend/src/pages/CurrencyConverter.tsx` | 357 | Currency conversion for multi-currency trip support |

**Components:**
| File | Location | LOC | Purpose |
|------|----------|-----|---------|
| ShareModal.tsx | `frontend/src/components/ShareModal.tsx` | 203 | Trip sharing modal with email input, permission levels |
| ForgotPasswordModal.tsx | `frontend/src/components/ForgotPasswordModal.tsx` | 281 | Password recovery flow |
| DocumentManager.tsx | `frontend/src/components/DocumentManager.tsx` | 269 | Manage downloaded/exported reports (PDF, CSV) |
| Layout.tsx | `frontend/src/components/Layout.tsx` | 235 | Main app layout with navigation, user menu, notifications badge |
| MarkdownMessage.tsx | `frontend/src/components/MarkdownMessage.tsx` | 136 | Render markdown content for notifications/messages |

**Total Frontend LOC for Member 2:** 5,698 lines
**Frontend Components (Key UI Elements):**
- `Login.tsx` and `Register.tsx` handle JWT token storage and authentication state
- `Dashboard.tsx` aggregates data from multiple API endpoints with real-time updates
- `ExpenseTracker.tsx` uses 15+ hooks with Recharts integration for visualizations
- `Layout.tsx` provides persistent UI chrome and navigation
- Authentication context provider, protected routes, and token refresh logic

---

## Frontend Implementation Details

### ExpenseTracker.tsx (700 LOC)

```typescript
// frontend/src/pages/ExpenseTracker.tsx
export function ExpenseTracker({ tripId }: { tripId: number }) {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [burnRate, setBurnRate] = useState(0);
  const [projections, setProjections] = useState({});
  const [chartData, setChartData] = useState({});
  
  // CRUD operations
  const { mutate: addExpense } = useMutation(
    (data: ExpenseCreate) => api.post(`/trips/${tripId}/expenses`, data),
    { onSuccess: (data) => setExpenses([...expenses, data]) }
  );
  
  const { mutate: deleteExpense } = useMutation(
    (id: number) => api.delete(`/trips/${tripId}/expenses/${id}`),
    { onSuccess: (id) => setExpenses(expenses.filter(e => e.id !== id)) }
  );
  
  // Calculate burn rate and projections
  useEffect(() => {
    const dailyAverage = expenses.reduce((sum, e) => sum + e.amount, 0) / tripDays;
    setBurnRate(dailyAverage);
    
    const remaining = tripBudget - totalSpent;
    const daysRemaining = tripDays - elapsedDays;
    setProjections({
      budgetRemaining: remaining,
      daysRemaining,
      dailyLimit: remaining / daysRemaining,
      onTrackStatus: dailyAverage <= (tripBudget / tripDays)
    });
  }, [expenses]);
  
  return (
    <ExpenseTrackerUI
      expenses={expenses}
      burnRate={burnRate}
      projections={projections}
      onAdd={addExpense}
      onDelete={deleteExpense}
      chartData={chartData}
    />
  );
}
```

Key features:
- Add/edit/delete expenses with real-time updates
- Burn rate calculation (daily average spending)
- Budget vs. actual projections
- Category-based pie/bar charts
- Allocation editor (adjust category budgets)

**Viva Questions (Sample):**
1. How do you calculate burn rate and why is it important?
2. How do you handle real-time updates when expenses change?
3. What charts do you use and why?
4. How do you project budget remaining vs. days remaining?
5. What hooks are used and for what purpose?

### AICompanion.tsx (800 LOC)

```typescript
// frontend/src/pages/AICompanion.tsx
export function AICompanion({ tripId }: { tripId: number }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeTab, setActiveTab] = useState<"chat" | "planner" | "regenerate" | "explain" | "multistop">("chat");
  const [isLoading, setIsLoading] = useState(false);
  
  // Chat tab: Real-time messaging
  const handleSendMessage = async (message: string) => {
    setIsLoading(true);
    const response = await api.post(`/api/ai/chat`, {
      message,
      trip_id: tripId
    });
    setMessages([...messages, { role: "user", content: message }, { role: "assistant", content: response }]);
    setIsLoading(false);
  };
  
  return (
    <div className="ai-companion">
      <Tabs value={activeTab} onChange={setActiveTab}>
        {/* Tab 1: Chat - General conversation */}
        <ChatTab messages={messages} onSend={handleSendMessage} isLoading={isLoading} />
        
        {/* Tab 2: Planner - AI generates itineraries */}
        <PlannerTab tripId={tripId} />
        
        {/* Tab 3: Regenerator - Recreate content with different tone/style */}
        <RegeneratorTab content={lastContent} />
        
        {/* Tab 4: Explainability - Understand optimization decisions */}
        <ExplainabilityTab explanations={explanations} />
        
        {/* Tab 5: Multistop - Optimize multi-city routes */}
        <MultistopTab tripId={tripId} />
      </Tabs>
    </div>
  );
}
```

Key features:
- 5 tabs for different AI capabilities
- Real-time chat with streaming responses
- AI-generated itinerary suggestions
- Content regeneration (rephrase, change tone)
- Budget optimizer explanations
- Multi-stop route optimization

**Viva Questions (Sample):**
1. How do you handle streaming chat responses in real-time?
2. What's the purpose of each tab in AICompanion?
3. How do you manage conversation history?
4. What happens when API calls fail?
5. How do you display loading states?

---

## Core Responsibilities

### 1. User Authentication & Authorization (Feature 11)
**What you own:** Complete authentication system including registration, login, JWT tokens, and session management

**Criticality:** HIGH — Security-sensitive feature requiring careful implementation

**Key Files:**
- `backend/app/auth.py` (lines 1–300) — Core auth logic
- `backend/app/routers/auth.py` (lines 1–300) — API endpoints
- `backend/app/models.py` (User model, lines 50–120)
- `backend/app/database.py` (user CRUD functions)

**Authentication Architecture:**

```
Frontend Login Form
  ↓ (POST /api/auth/login with email + password)
Backend: auth.py → verify_password()
  ├─ Hash submitted password using bcrypt
  ├─ Compare with stored password_hash
  ├─ If match: proceed to token generation
  └─ If no match: return 401 Unauthorized
  ↓
Backend: auth.py → create_access_token()
  ├─ Generate JWT payload: {sub: user_id, email, iat, exp}
  ├─ Sign with SECRET_KEY using HS256 algorithm
  ├─ Set expiry: 15 minutes (short-lived)
  ├─ Return JWT to frontend
  └─ Set Cookie (httpOnly, secure flags)
  ↓
Backend: auth.py → create_refresh_token()
  ├─ Generate new JWT payload: {sub: user_id, iat, exp}
  ├─ Set expiry: 7 days (long-lived)
  ├─ Hash token + store in RefreshToken table
  ├─ Return refresh token to frontend
  └─ Frontend stores in secure storage (not localStorage)
  ↓
Frontend receives {access_token, refresh_token}
  ├─ Stores access_token in memory (cleared on page reload)
  ├─ Stores refresh_token in httpOnly cookie or secure storage
  └─ Includes access_token in Authorization header for API calls
```

**Code Reference:**

```python
# backend/app/auth.py

from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    """Hash password using bcrypt with 12 rounds"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Compare plain password with bcrypt hash"""
    return pwd_context.verify(plain_password, password_hash)

def create_access_token(user_id: int, email: str, expires_delta: timedelta = None):
    """Generate JWT access token (15 min expiry)"""
    if expires_delta is None:
        expires_delta = timedelta(minutes=15)
    
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.utcnow(),
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: int, expires_delta: timedelta = None):
    """Generate JWT refresh token (7 day expiry)"""
    if expires_delta is None:
        expires_delta = timedelta(days=7)
    
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": user_id,
        "iat": datetime.utcnow(),
        "exp": expire,
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    """Validate JWT and extract claims"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# backend/app/routers/auth.py

@router.post("/auth/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    user_data = {email, password, full_name}
    
    Validation:
      1. Email uniqueness (check if exists)
      2. Password strength (8+ chars, 1 uppercase, 1 digit)
      3. Email format validation (RFC 5322)
    """
    
    # Check email uniqueness
    existing = db.query(User).filter_by(email=user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password strength
    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Password too short")
    if not any(c.isupper() for c in user_data.password):
        raise HTTPException(status_code=400, detail="Password needs uppercase")
    if not any(c.isdigit() for c in user_data.password):
        raise HTTPException(status_code=400, detail="Password needs digit")
    
    # Hash password
    password_hash = hash_password(user_data.password)
    
    # Create user
    user = User(
        email=user_data.email,
        password_hash=password_hash,
        full_name=user_data.full_name,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"user_id": user.id, "email": user.email, "message": "Registration successful"}

@router.post("/auth/login")
async def login(credentials: LoginSchema, db: Session = Depends(get_db)):
    """
    credentials = {email, password}
    
    Returns: {access_token, refresh_token, user}
    """
    
    # Fetch user
    user = db.query(User).filter_by(email=credentials.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)
    
    # Store refresh token hash
    token_hash = hash_password(refresh_token)
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expiry=datetime.utcnow() + timedelta(days=7)
    )
    db.add(db_refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name}
    }

@router.post("/auth/refresh")
async def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    """
    Refresh access token using valid refresh token
    
    Returns: {access_token}
    """
    
    # Validate refresh token
    try:
        payload = decode_token(refresh_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # Check if refresh token is stored and not revoked
    user_id = payload.get("sub")
    stored_token = db.query(RefreshToken).filter_by(user_id=user_id).first()
    
    if not stored_token or not verify_password(refresh_token, stored_token.token_hash):
        raise HTTPException(status_code=401, detail="Refresh token not found or revoked")
    
    # Generate new access token (and optionally rotate refresh token)
    user = db.query(User).filter_by(id=user_id).first()
    new_access_token = create_access_token(user.id, user.email)
    
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.get("/auth/me")
async def get_current_user(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """
    Get current authenticated user profile
    
    Dependency: verify_token extracts user_id from JWT
    """
    
    user = db.query(User).filter_by(id=token["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
```

**Security Considerations:**

| Concern | Implementation |
|---------|----------------|
| **Password Hashing** | Bcrypt with 12 rounds (industry standard) |
| **Token Storage** | httpOnly cookie for refresh token (immune to XSS) |
| **Token Expiry** | Access: 15 min (short-lived), Refresh: 7 days |
| **HTTPS** | Required in production (secure flag on cookies) |
| **Rate Limiting** | 5 login attempts per 15 minutes per IP |
| **SQL Injection** | Parameterized queries (ORM prevents) |
| **CSRF** | CORS validation + CSRF tokens (if needed) |

**Database Models:**

```python
# backend/app/models.py

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trips = relationship("Trip", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expiry = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User")
```

**What you need to explain:**
- Bcrypt vs MD5/SHA1 (why bcrypt is secure)
- Why JWT tokens need short expiry (15 min vs 7 days)
- Refresh token rotation (security improvement)
- Email validation and uniqueness
- Password strength requirements
- Rate limiting on login endpoint
- Session management and logout

**Viva Questions (Sample):**
1. Why use bcrypt instead of just salting passwords?
2. How does token refresh work? Why not just extend access token?
3. What's the difference between access and refresh tokens?
4. If someone steals a refresh token, what can they do?
5. How would you implement "logout" with stateless JWT tokens?
6. What's rate limiting? How would you implement it?
7. Why use httpOnly cookies instead of localStorage for refresh token?

---

### 2. User Dashboard (Feature 12)
**What you own:** Aggregated view of user's trips, expenses, and statistics

**Key Files:**
- `backend/app/routers/trips.py` (lines 900–1000, dashboard endpoint)
- `backend/app/services/financial_validator.py` (aggregation logic)

**Dashboard Data Flow:**

```python
# GET /api/dashboard

def get_dashboard(current_user = Depends(verify_token), db: Session = Depends(get_db)):
    """
    Aggregates:
      1. All user's trips (active + completed)
      2. Recent expenses (last 10)
      3. Budget summary (total spent, budget remaining)
      4. Quick stats
    """
    
    user_id = current_user["sub"]
    
    # Fetch trips
    trips = db.query(Trip).filter_by(user_id=user_id).all()  # All trips
    active_trips = [t for t in trips if t.end_date >= today]
    completed_trips = [t for t in trips if t.end_date < today]
    
    # Fetch recent expenses
    recent_expenses = db.query(Expense)\
        .join(Trip)\
        .filter(Trip.user_id == user_id)\
        .order_by(Expense.created_at.desc())\
        .limit(10)\
        .all()
    
    # Calculate stats
    total_spent = sum(e.amount for e in all_expenses)
    total_budget = sum(t.budget for t in trips)
    budget_remaining = total_budget - total_spent
    
    avg_daily_spend = total_spent / sum((t.end_date - t.start_date).days for t in trips)
    
    return {
        "trips": {
            "active": len(active_trips),
            "completed": len(completed_trips),
            "total": len(trips)
        },
        "budget": {
            "total_budget": total_budget,
            "total_spent": total_spent,
            "remaining": budget_remaining,
            "percent_spent": (total_spent / total_budget * 100) if total_budget > 0 else 0
        },
        "recent_expenses": recent_expenses,
        "stats": {
            "average_daily_spend": avg_daily_spend,
            "most_expensive_category": get_top_category(all_expenses)
        }
    }
```

**What you need to explain:**
- How you aggregate data from multiple sources
- Performance optimization (caching, query efficiency)
- Error handling (no trips, no expenses)
- Real-time vs cached data
- UI rendering strategy (loading states)

**Viva Questions (Sample):**
1. How do you efficiently query all expenses across multiple trips?
2. What happens if a user has 100 trips? Does dashboard slow down?
3. How would you cache dashboard data? When to invalidate?
4. Why show "active trips" separately from completed?

---

### 3. Trip Sharing (Feature 13)
**What you own:** Generate invite links, manage permissions, validate share access

**Criticality:** MEDIUM — Involves authorization and token generation

**Key Files:**
- `backend/app/routers/trips.py` (lines 1050–1200, share endpoints)
- `backend/app/models.py` (TripShare model, lines 1600–1650)

**Trip Sharing Flow:**

```
User A wants to share Trip 123 with User B

Step 1: User A clicks "Share" button
  ↓
Step 2: Frontend calls POST /api/trips/123/share
  with data: {shared_with_email: "userB@example.com", permission_level: "view"}
  ↓
Step 3: Backend validates
  - Is User A the trip owner? (verify user_id matches)
  - Is email format valid?
  - Does User B already have access?
  ↓
Step 4: Generate invite token
  - Create UUID (secure random)
  - Store in TripShare table: {trip_id, user_id_from, email, permission, token, created_at, expiry}
  ↓
Step 5: Send email to User B
  - Link: https://app.com/shared-trip?token=<uuid>
  - Message: "User A shared a trip with you"
  ↓
Step 6: User B clicks link
  - Browser calls GET /api/shared-trips/<token>
  - Backend validates token (exists, not expired)
  - Backend checks permission level
  - Returns trip data (read-only if VIEW, editable if EDIT)
```

**Code Reference:**

```python
# backend/app/routers/trips.py

@router.post("/trips/{trip_id}/share")
async def create_share(trip_id: int, share_data: ShareCreate, 
                      current_user = Depends(verify_token), db: Session = Depends(get_db)):
    """
    share_data = {shared_with_email, permission_level: "view" | "edit"}
    """
    
    # Verify ownership
    trip = db.query(Trip).filter_by(id=trip_id, user_id=current_user["sub"]).first()
    if not trip:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Validate email
    if not is_valid_email(share_data.shared_with_email):
        raise HTTPException(status_code=400, detail="Invalid email")
    
    # Check if already shared
    existing = db.query(TripShare).filter_by(
        trip_id=trip_id,
        shared_with_email=share_data.shared_with_email
    ).first()
    if existing and not existing.is_revoked:
        raise HTTPException(status_code=400, detail="Already shared with this user")
    
    # Generate invite token
    invite_token = str(uuid.uuid4())
    
    # Store share
    trip_share = TripShare(
        trip_id=trip_id,
        shared_by_user_id=current_user["sub"],
        shared_with_email=share_data.shared_with_email,
        permission_level=share_data.permission_level,
        invite_token=invite_token,
        created_at=datetime.utcnow(),
        expiry=datetime.utcnow() + timedelta(days=30)
    )
    db.add(trip_share)
    db.commit()
    
    # Send email
    send_share_email(share_data.shared_with_email, trip.name, invite_token)
    
    return {"message": "Trip shared", "invite_token": invite_token}

@router.get("/shared-trips/{invite_token}")
async def get_shared_trip(invite_token: str, db: Session = Depends(get_db)):
    """
    Access shared trip via invite token (no authentication required)
    """
    
    # Find share record
    share = db.query(TripShare).filter_by(invite_token=invite_token).first()
    if not share:
        raise HTTPException(status_code=404, detail="Shared trip not found")
    
    # Check expiry
    if share.expiry < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Share link expired")
    
    # Check revocation
    if share.is_revoked:
        raise HTTPException(status_code=403, detail="Share link revoked")
    
    # Fetch trip data
    trip = db.query(Trip).filter_by(id=share.trip_id).first()
    
    # Return trip (read-only if VIEW permission)
    return {
        "trip": trip,
        "permission": share.permission_level,
        "shared_by": share.shared_by_user_id
    }

@router.delete("/trips/{trip_id}/shares/{share_id}")
async def revoke_share(trip_id: int, share_id: int, 
                       current_user = Depends(verify_token), db: Session = Depends(get_db)):
    """
    Revoke share access (mark as revoked, don't delete)
    """
    
    # Verify ownership
    trip = db.query(Trip).filter_by(id=trip_id, user_id=current_user["sub"]).first()
    if not trip:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Revoke share
    share = db.query(TripShare).filter_by(id=share_id, trip_id=trip_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    share.is_revoked = True
    db.commit()
    
    return {"message": "Share revoked"}
```

**What you need to explain:**
- UUID generation for secure tokens
- Email delivery (SMTP config)
- Permission levels (VIEW vs EDIT)
- Token expiry and revocation
- No authentication required for shared link (optional login)
- Security: token is not user-guessable

**Viva Questions (Sample):**
1. Why use UUID instead of incrementing numbers for invite tokens?
2. What happens if the same email is shared twice?
3. How would you implement "edit" permission (allowing collaborators to add expenses)?
4. Can a shared user share the trip with someone else?
5. What if the invite link is leaked? How is access controlled?

---

### 4. Expense History & Export (Feature 14)
**What you own:** Fetch, filter, paginate, and export expenses in CSV/PDF formats

**Key Files:**
- `backend/app/routers/expenses.py` (lines 300–450, history + export)
- `backend/app/services/pdf_generator.py` (lines 1–200, PDF generation)

**Expense History with Filtering:**

```python
# GET /api/trips/{trip_id}/expenses/history?page=1&limit=100&category=FOOD&date_from=2024-01-01&date_to=2024-12-31

@router.get("/trips/{trip_id}/expenses/history")
async def get_expense_history(
    trip_id: int,
    page: int = 1,
    limit: int = 100,
    category: Optional[str] = None,
    amount_from: Optional[float] = None,
    amount_to: Optional[float] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Supports filtering by:
      - category (enum: ACCOMMODATION, FOOD, TRANSPORT, ACTIVITIES, MISC)
      - amount range
      - date range
    
    Returns paginated results with sorting
    """
    
    # Verify trip ownership
    trip = db.query(Trip).filter_by(id=trip_id, user_id=current_user["sub"]).first()
    if not trip:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Build query
    query = db.query(Expense).filter_by(trip_id=trip_id)
    
    # Apply filters
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
    
    # Sort by date descending
    query = query.order_by(Expense.date.desc())
    
    # Paginate
    total = query.count()
    skip = (page - 1) * limit
    expenses = query.offset(skip).limit(limit).all()
    
    return {
        "expenses": expenses,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }
```

**CSV Export:**

```python
# GET /api/trips/{trip_id}/expenses/export?format=csv

@router.get("/trips/{trip_id}/expenses/export")
async def export_expenses(
    trip_id: int,
    format: str = "csv",  # "csv" or "pdf"
    current_user = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Export expenses in CSV or PDF format
    """
    
    # Verify ownership
    trip = db.query(Trip).filter_by(id=trip_id, user_id=current_user["sub"]).first()
    if not trip:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Fetch all expenses for trip
    expenses = db.query(Expense).filter_by(trip_id=trip_id).order_by(Expense.date).all()
    
    if format == "csv":
        # Generate CSV
        csv_buffer = StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=["Date", "Category", "Amount", "Currency", "Notes"])
        writer.writeheader()
        
        for expense in expenses:
            writer.writerow({
                "Date": expense.date.strftime("%Y-%m-%d"),
                "Category": expense.category,
                "Amount": expense.amount,
                "Currency": expense.currency,
                "Notes": expense.notes or ""
            })
        
        csv_content = csv_buffer.getvalue()
        
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=expenses_{trip_id}.csv"}
        )
    
    elif format == "pdf":
        # Generate PDF (see Feature 18)
        pdf_content = generate_expense_report(trip, expenses)
        
        return StreamingResponse(
            iter([pdf_content]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=expenses_{trip_id}.pdf"}
        )
```

**What you need to explain:**
- Query optimization (indexes on category, date)
- Pagination strategy (why offset/limit instead of cursor)
- CSV generation (headers, escaping)
- PDF generation (integration with pdf_generator service)
- File streaming (why not load entire file in memory)

**Viva Questions (Sample):**
1. How do you optimize the query for large expense datasets?
2. Why use offset/limit pagination instead of cursor-based?
3. How do you handle CSV special characters (commas, quotes)?
4. What's the difference between streaming response vs loading entire file?

---

### 5. Notifications Dashboard (Feature 15)
**What you own:** In-app notification center, mark as read, delete, clear all

**Key Files:**
- `backend/app/routers/notifications.py` (lines 150–300)
- `backend/app/models.py` (Notification model, lines 750–800)

**Notification System:**

```
Types of Notifications:
  1. BUDGET_ALERT: "You've spent 75% of your food budget"
  2. TRIP_SHARED: "Alice shared a trip with you"
  3. EXPENSE_ALERT: "New expense recorded: $50 for food"
  4. SYSTEM_MESSAGE: "Maintenance window tomorrow 2-4 AM"

Storage: Persistent database table
  - Allows user to view past notifications
  - Mark as read (don't delete, just flag)
  - Bulk operations (clear all)

Frontend:
  - Real-time updates (WebSocket optional)
  - Toast notifications (immediate feedback)
  - Notification bell icon (unread count badge)
  - Full notification center page
```

**Code Reference:**

```python
# backend/app/routers/notifications.py

@router.get("/notifications")
async def get_notifications(
    page: int = 1,
    limit: int = 50,
    unread_only: bool = False,
    current_user = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get user's notifications with pagination
    """
    
    query = db.query(Notification).filter_by(user_id=current_user["sub"])
    
    if unread_only:
        query = query.filter_by(read=False)
    
    # Sort by newest first
    query = query.order_by(Notification.created_at.desc())
    
    # Paginate
    total = query.count()
    skip = (page - 1) * limit
    notifications = query.offset(skip).limit(limit).all()
    
    return {
        "notifications": notifications,
        "unread_count": db.query(Notification).filter_by(user_id=current_user["sub"], read=False).count(),
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total
        }
    }

@router.put("/notifications/{notification_id}")
async def mark_as_read(
    notification_id: int,
    current_user = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Mark notification as read
    """
    
    notification = db.query(Notification).filter_by(
        id=notification_id,
        user_id=current_user["sub"]
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.read = True
    db.commit()
    
    return {"message": "Marked as read"}

@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Delete notification (soft delete via read flag, or hard delete)
    """
    
    notification = db.query(Notification).filter_by(
        id=notification_id,
        user_id=current_user["sub"]
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    return {"message": "Deleted"}

@router.delete("/notifications")
async def clear_all_notifications(
    current_user = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Clear all notifications for user
    """
    
    db.query(Notification).filter_by(user_id=current_user["sub"]).delete()
    db.commit()
    
    return {"message": "All notifications cleared"}

# Service function to send notification (called from other routers)

def send_notification(db: Session, user_id: int, notif_type: str, message: str, trip_id: int = None):
    """
    Create and optionally email notification
    """
    
    notification = Notification(
        user_id=user_id,
        type=notif_type,
        message=message,
        related_trip_id=trip_id,
        read=False,
        created_at=datetime.utcnow()
    )
    db.add(notification)
    db.commit()
    
    # Optional: send email
    user = db.query(User).filter_by(id=user_id).first()
    if user.email_notifications_enabled:
        send_email(user.email, f"BudgetBound: {notif_type}", message)
    
    return notification
```

**What you need to explain:**
- Why persist notifications (historical record, user can read later)
- Unread count tracking
- Auto-archival (delete notifications older than 30 days)
- Email integration (optional, user preference)
- WebSocket for real-time delivery (optional enhancement)

**Viva Questions (Sample):**
1. Why not use WebSockets for real-time notifications?
2. How do you prevent notification spam?
3. How do you handle user preferences (which types of notifications to receive)?
4. What's the retention policy (delete after X days)?

---

### 6. Budget Alerts Integration (Feature 4)
**What you own:** Integration point with expense creation to trigger alerts

**Key Files:**
- `backend/app/routers/budget_alerts.py` (lines 1–200)
- `backend/app/routers/expenses.py` (calls alert check after adding expense)

**Alert Trigger Flow:**

```
User adds expense: "Food: $50"
  ↓
Backend: add_expense() function
  ├─ Inserts expense into database
  ├─ Calls: check_budget_alerts(trip_id)
  └─ Returns response with alert status
  ↓
check_budget_alerts():
  ├─ Fetch trip budget
  ├─ Sum all expenses for trip
  ├─ Fetch alert thresholds for trip
  ├─ For each threshold:
  │   ├─ Calculate: current_spend / budget = percent_spent
  │   ├─ If percent_spent >= threshold.percentage: TRIGGER ALERT
  │   ├─ Create notification
  │   └─ Send email (optional)
  └─ Return alert status
```

**Code Reference:**

```python
# backend/app/routers/expenses.py

@router.post("/trips/{trip_id}/expenses")
async def create_expense(trip_id: int, expense_data: ExpenseCreate, ...):
    """
    Add expense and trigger budget alert check
    """
    
    # Validate ownership
    trip = db.query(Trip).filter_by(id=trip_id, user_id=current_user["sub"]).first()
    if not trip:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Create expense
    expense = Expense(
        trip_id=trip_id,
        category=expense_data.category,
        amount=expense_data.amount,
        date=expense_data.date,
        notes=expense_data.notes
    )
    db.add(expense)
    db.commit()
    
    # Check budget alerts
    alerts_triggered = check_budget_alerts(trip_id, db)
    
    return {
        "expense": expense,
        "alerts": alerts_triggered
    }

# backend/app/routers/budget_alerts.py

def check_budget_alerts(trip_id: int, db: Session):
    """
    Evaluate all budget alert thresholds for trip
    """
    
    trip = db.query(Trip).filter_by(id=trip_id).first()
    if not trip:
        return []
    
    # Sum expenses
    total_spent = db.query(func.sum(Expense.amount)).filter_by(trip_id=trip_id).scalar() or 0
    percent_spent = (total_spent / trip.budget * 100) if trip.budget > 0 else 0
    
    # Fetch thresholds
    thresholds = db.query(BudgetAlert).filter_by(trip_id=trip_id).all()
    
    alerts_triggered = []
    
    for threshold in thresholds:
        # Check if alert should trigger
        if percent_spent >= threshold.percentage and not threshold.is_triggered:
            # Mark as triggered
            threshold.is_triggered = True
            db.commit()
            
            # Send notification
            send_notification(
                db=db,
                user_id=trip.user_id,
                notif_type="BUDGET_ALERT",
                message=f"Alert: You've spent {percent_spent:.1f}% of your {trip.name} budget",
                trip_id=trip_id
            )
            
            alerts_triggered.append({
                "threshold_id": threshold.id,
                "message": f"Budget alert triggered at {percent_spent:.1f}%"
            })
    
    return alerts_triggered
```

**What you need to explain:**
- When alerts are checked (on expense creation, every time)
- How to prevent duplicate alerts (is_triggered flag)
- User preferences for alert thresholds
- Category-level vs trip-level alerts

---

### 7. Destination Explorer (Feature 6)
**What you own:** REST endpoints for browsing, searching, filtering destinations

**Key Files:**
- `backend/app/routers/destinations.py` (full file)
- `backend/app/services/destination_database.py` (search/filter logic)

**Endpoints Overview:**

```python
GET /api/destinations?
  budget_range: "1000-5000"
  continent: "Europe"
  climate: "temperate"
  page: 1
  limit: 20

Returns: [
  {
    "id": 1,
    "name": "Paris",
    "country": "France",
    "continent": "Europe",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "base_budget_estimate": 2500,
    "climate": "temperate",
    "best_months": ["May", "September", "October"],
    "activities": [
      {"name": "Eiffel Tower", "cost_estimate": 50},
      {"name": "Louvre Museum", "cost_estimate": 45}
    ]
  },
  ...
]

GET /api/destinations/{id}

POST /api/destinations/search?q=paris

Returns filtered results with full details
```

**What you need to explain:**
- Database schema for destinations and activities
- Search implementation (full-text search vs simple LIKE)
- Filter logic (budget range, climate category)
- Pagination strategy
- Caching strategy for static data (destinations rarely change)

---

### 8. Admin Analytics Dashboard (Feature 16)
**What you own:** Admin-only endpoints for system-wide analytics

**Key Files:**
- `backend/app/routers/admin_analytics.py` (full file)
- Requires `is_admin` flag on User model

**Admin Endpoints:**

```python
GET /api/admin/analytics
  ├─ User growth (monthly registrations)
  ├─ Spending trends (total spent by month/category)
  ├─ Popular destinations (top 10 by trip count)
  └─ Requires admin authentication

Returns: {
  "users": {
    "total": 1000,
    "active_this_month": 500,
    "new_this_month": 50,
    "growth_percent": 5.3
  },
  "spending": {
    "total_all_time": 500000,
    "by_month": {...},
    "by_category": {...}
  },
  "destinations": [
    {"name": "Paris", "trip_count": 50, "avg_spent": 3000},
    ...
  ]
}
```

**What you need to explain:**
- Admin-only access control (decorator pattern)
- Aggregation queries (SUM, COUNT, GROUP BY)
- Privacy considerations (no PII exposed)
- Performance optimization (aggregate periodic background jobs)

---

## Viva Preparation Checklist

**Before your viva, be able to explain:**

1. ✓ Authentication flow (registration, login, JWT, refresh tokens)
2. ✓ Password hashing (bcrypt, why not MD5/SHA)
3. ✓ Token expiry strategy (15 min access, 7 day refresh)
4. ✓ Authorization (user ownership, admin checks)
5. ✓ Dashboard aggregation (queries, caching)
6. ✓ Trip sharing (UUID tokens, permissions, email)
7. ✓ Expense filtering & export (query optimization, CSV/PDF)
8. ✓ Notifications (persistent storage, mark as read)
9. ✓ Budget alerts (trigger logic, threshold checking)
10. ✓ Destination explorer (search, filter, pagination)
11. ✓ Admin analytics (aggregation, admin-only access)

---

## Suggested Talking Points

**When asked "Tell us about your features":**

"I owned the user infrastructure and core CRUD operations for BudgetBound. The most critical was **Authentication & Authorization**—I implemented full JWT token management with secure refresh token rotation, bcrypt password hashing, and session handling. This forms the security foundation for all other features.

Beyond security, I built **Trip Sharing** for collaboration with secure invite tokens and permission levels, **Expense History & Export** with filtering and CSV/PDF export, and the **Notifications Dashboard** for real-time budget alerts and user feedback.

I also integrated **Budget Alerts** into the expense creation flow to automatically notify users when they approach spending limits. On the infrastructure side, I implemented the **Admin Analytics Dashboard** for system-wide analytics and the **Destination Explorer** for browsing curated destinations.

The complexity came from balancing security (JWT, rate limiting, authorization) with user experience (efficient queries, pagination, caching). All CRUD operations follow RESTful conventions and leverage SQLAlchemy ORM for database operations."

---

**End of Member 2 Guide**
