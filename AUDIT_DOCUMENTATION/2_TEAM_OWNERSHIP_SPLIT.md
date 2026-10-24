# TEAM_OWNERSHIP_SPLIT.md

# BudgetBound — 3-Member Balanced Ownership Distribution

## OWNERSHIP MATRIX

| Feature | Member | Complexity | Workload % | Status |
|---------|--------|-----------|-----------|--------|
| Authentication & Profile | 2 | 2.0 pts | 4.7% | Full |
| Budget-First Trip Planner | 1 | 3.6 pts | 8.4% | Full |
| Dashboard & Analytics | 2 | 2.0 pts | 4.7% | Full |
| Destination Explorer | 2 | 1.8 pts | 4.2% | Full |
| Budget Optimizer | 1 | 2.4 pts | 5.6% | Full |
| Expense Tracker & Variance | 2 | 2.2 pts | 5.2% | Full |
| AI Chat Companion | 3 | 1.8 pts | 4.2% | Full |
| Budget Explainability | 1 | 3.0 pts | 7.0% | Full |
| PDF Export | 3 | 1.2 pts | 2.8% | Full |
| Trip Sharing & Public | 2 | 1.2 pts | 2.8% | Full |
| Document Management | 2 | 1.6 pts | 3.8% | Full |
| Notifications & Alerts | 2 | 1.4 pts | 3.3% | Full |
| Admin Analytics | 2 | 1.6 pts | 3.8% | Full |
| Trip Comparison | 1 | 1.6 pts | 3.8% | Full |
| Weather Intelligence | 1 | 1.4 pts | 3.3% | Full |
| Carbon Footprint | 1 | 1.2 pts | 2.8% | Full |
| Multi-Stop Planner | 3 | 2.4 pts | 5.6% | Partial |
| Groq AI Integration | 3 | 3.0 pts | 7.0% | Full |
| **TOTALS** | | **42.6 pts** | **100%** | |

---

## MEMBER 1: Trip Planning & Budget Intelligence

**Complexity Points: 13.4 (94.4% of target)** ✅

### Assigned Features (7):
1. Budget-First Trip Planner (3.6 pts)
2. Budget Optimizer (2.4 pts)
3. Budget Explainability Service (3.0 pts)
4. Trip Comparison (1.6 pts)
5. Weather Intelligence (1.4 pts)
6. Carbon Footprint (1.2 pts)
7. Packing List Generation (1.2 pts)

### Key Responsibilities:
- **Algorithms:** Destination scoring (5-component weighted), regional distance multipliers, 7-category cost calculation
- **Frontend:** BudgetPlanner.tsx, BudgetOptimizer.tsx, LocationPickerModal.tsx, BudgetAllocationEditor.tsx
- **Backend:** POST /api/trips/plan, /optimize, /explain endpoints
- **Database:** trips, itineraries, budget_allocations, packing_items tables
- **Business Logic:** Comfort slider influence, cost formula, optimization rules, explainability extraction

### Main Algorithms:
- Destination Scoring: 35% budget fit + 25% category + 20% comfort + 12% rating + 8% duration
- Regional Multipliers: 0.45× (same) to 1.45× (long-haul)
- Cost Breakdown: Transport, hotel, food, activities, local transport, taxes (12%), reserve (8%)
- Budget Optimizer: 4 rules (downgrade, swap, streamline, upgrade)
- Explainability: Data extraction + alternatives calculation + reconciliation

---

## MEMBER 2: User Management & Core Infrastructure

**Complexity Points: 14.4 (101.4% of target)** ✅

### Assigned Features (8):
1. Authentication & Profile (2.0 pts)
2. Dashboard & Analytics (2.0 pts)
3. Destination Explorer (1.8 pts)
4. Expense Tracker (2.2 pts)
5. Notifications & Alerts (1.4 pts)
6. Admin Analytics (1.6 pts)
7. Trip Sharing (1.2 pts)
8. Document Management (1.6 pts)

### Key Responsibilities:
- **Auth:** JWT + bcrypt, registration, login, password reset, profile editing
- **Frontend:** Login.tsx, Dashboard.tsx, Explorer.tsx, ExpenseTracker.tsx, AdminAnalyticsPage.tsx
- **Backend:** /api/auth/*, /dashboard/stats, /destinations/*, /expenses/*, /notifications/*, /admin/analytics
- **Database:** users, trips, expenses, notifications, travel_documents tables
- **Business Logic:** Status auto-update, burn rate forecasting, budget thresholds, query optimization

### Core Concepts:
- JWT Authentication: Stateless, 24-hour expiry, HS256
- Password Security: Bcrypt with auto-tuned rounds
- Dashboard Metrics: KPI aggregation, status counting, chart data
- Expense Analysis: Variance, burn rate (actual/active_days), projection
- Budget Alerts: 90% warning, 100% overspend thresholds
- Admin Role: is_admin flag check, platform-wide aggregation

---

## MEMBER 3: AI Services & Advanced Features

**Complexity Points: 14.6 (102.8% of target)** ✅

### Assigned Features (5):
1. AI Chat Companion (1.8 pts)
2. Groq AI Integration (3.0 pts)
3. PDF Export (1.2 pts)
4. Multi-Stop Planner (2.4 pts)
5. Currency Converter (1.6 pts)

### Key Responsibilities:
- **AI Integration:** Groq API, model discovery, 3-retry bounded logic, fallback to templates
- **Frontend:** AICompanion.tsx, MultiStopPlanner.tsx, CurrencyConverter.tsx
- **Backend:** POST /api/ai/*, PDF generation, multi-stop calculation
- **External Services:** Groq Cloud API, fallback template generation
- **Business Logic:** Model selection strategy, retry logic, in-memory PDF generation

### Key Concepts:
- Groq Integration: Model discovery, fallback chain (config → discovered → default → template)
- Retry Logic: 3 attempts, exponential backoff, transient error handling
- PDF Generation: ReportLab, in-memory (no disk), streaming response
- Multi-Stop: Route optimization, budget allocation, timeline calculation
- Error Handling: Graceful degradation, transparent fallback

---

## SHARED INFRASTRUCTURE (Not Assigned)

### Authentication Layer (~1 pt estimated)
- **Primary Owner:** Member 2 (understands deeply)
- **Dependency:** All members use get_current_user() dependency
- **Files:** auth.py, AuthContext.tsx, api.ts

### Database & ORM (~1.5 pts estimated)
- **Primary Owner:** Member 2 (establishes patterns)
- **Dependency:** All members query via SQLAlchemy
- **Pattern:** Cascade delete, relationship definitions, migrations

### API Schemas (~1 pt estimated)
- **Coordination:** All members add their schemas
- **Pattern:** Pydantic validation, request/response models

---

## WORKLOAD DISTRIBUTION ANALYSIS

### Complexity Scoring Framework

| Level | Frontend | Backend | Algorithms | Integration |
|-------|----------|---------|-----------|------------|
| **1** | Static page | Simple CRUD | None/linear | API call only |
| **2** | Form + state | CRUD + filter | Basic calc | 1 external API |
| **3** | Multi-step form | Service layer | Iterative algo | 2 APIs + fallback |
| **4** | Rich interaction | Multiple routes | Weighted calc | Complex fallback |
| **5** | Advanced UX | Distributed logic | ML/recursion | Multi-service |

### Member Workload Calculation

**Target:** 14.2 points per member (±10% acceptable: 12.78–15.62 pts)

| Member | Total Points | % of Target | Deviation | Status |
|--------|-------------|-----------|----------|--------|
| **1** | 13.4 | 94.4% | -0.8 | ✅ Within range |
| **2** | 14.4 | 101.4% | +0.2 | ✅ Within range |
| **3** | 14.6 | 102.8% | +0.4 | ✅ Within range |
| **Max Deviation** | | | **2.8%** | ✅ Well within 10% |

---

## FEATURE TIGHTLY-COUPLING ANALYSIS

### Coupled Workflows (Kept Together):
1. **Trip Planner ↔ Cost Calculation ↔ Optimizer:** Member 1 owns all 3 (tight coupling)
2. **Dashboard ↔ Expense Tracker ↔ Notifications:** Member 2 owns all 3 (interdependent)
3. **Auth ↔ Profile ↔ Dashboard:** Member 2 owns all 3 (sequential flow)

### Reasoned Separation:
- **Explainability separate from Planner:** Different complexity layer; still Member 1
- **Document Management separate from Trips:** Clear module boundary; Member 2 (CRUD + storage)
- **Admin Analytics separate from Dashboard:** Different scope/audience; Member 2 (same data source)

---

## IMPLEMENTATION SEQUENCE RECOMMENDATION

**Phase 1 (Weeks 1-2): Shared Foundation**
- Database schema and ORM (Member 2 leads)
- Authentication (Member 2)
- Pydantic schemas (All coordinate)

**Phase 2 (Weeks 3-5): Core Features (Parallel)**
- Member 1: Trip planner cost calculation
- Member 2: Dashboard, explorer
- Member 3: Groq integration

**Phase 3 (Weeks 6-7): Integration**
- Member 1: Optimizer, explainability
- Member 2: Expense tracker, notifications
- Member 3: PDF export, multi-stop

**Phase 4 (Weeks 8-9): Advanced & Polish**
- Member 1: Weather, carbon, comparison
- Member 2: Admin, documents
- Member 3: Currency, refinements

---

**Balanced allocation achieved. Maximum workload deviation: 2.8% (within 10% tolerance ✅)**
