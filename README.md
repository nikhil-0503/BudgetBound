# BudgetBound — Budget-First Travel Planning Platform

BudgetBound is a comprehensive, production-quality full-stack travel planning platform built to revolutionize the travel planning lifecycle by introducing a **budget-first discovery model**.

Instead of asking users where they want to go first, BudgetBound flips the travel discovery equation:
1. **What is your budget?** (e.g., ₹15,000, ₹50,000, etc.)
2. **Where are you starting from?** (e.g., Bangalore, Delhi, Mumbai, Kolkata, etc.)
3. **How many days do you have?** (e.g., 3 days, 5 days, etc.)
4. **What type of trip (Beach, Adventure, Nature, Religious, Romantic, etc.) do you want?**

Based on these constraints and a comfort slider (0-100), the platform dynamically evaluates, scores, and ranks destinations in its database to recommend the single best getaway. It then generates a complete day-by-day sightseeing itinerary, predicts hidden expenses (contingencies, taxes, local transit), compares planned vs actual spending in visual ledgers, and downloads offline PDF itineraries.

---

## 🛠️ Complete Technical Stack

### Frontend Architecture
* **Framework:** React 18 with TypeScript (Vite bundler).
* **Styling & Theme Engine:** Tailwind CSS v4 (incorporating custom class-based dark mode variants and glassmorphism styling).
* **Routing:** React Router v6 (`react-router-dom`) with Route Guards separating public anonymous pages from protected dashboard modules.
* **Data Visualizations:** Recharts (rendering comparison bar graphs and expense category pie charts adapting dynamically to dark/light theme properties).
* **Icons:** Lucide React.
* **API Client:** Axios wrapped with request interceptors to automatically attach JWT authorization headers from local cache.

### Backend Architecture
* **Framework:** FastAPI (Python 3.11/3.12) running under an asynchronous Uvicorn server.
* **Database & ORM:** PostgreSQL (production database) with a transparent **SQLite auto-fallback engine** (automatically creating `budgetbound.db` locally if the primary database is offline, ensuring zero-setup dev runnability). Managed via SQLAlchemy ORM.
* **Authentication:** Stateless JWT bearer tokens signed using HMAC-SHA256, alongside bcrypt password hashing via `passlib`.
* **Reporting:** ReportLab (generating dynamic, multi-page vector PDF travel plans containing tabular summaries, allocations, and day-by-day itineraries).

---

## 🗺️ Project Structure

Below is the directory map of the BudgetBound repository:

```
BudgetBound/
├── docker-compose.yml          # Multistage container orchestrator
├── README.md                   # Full platform guide and installation scripts
├── backend/
│   ├── Dockerfile              # Slim Python container configuration
│   ├── main.py                 # FastAPI app entry point (mounts, seeding, CORS)
│   ├── requirements.txt        # Backend dependencies list
│   └── app/
│       ├── auth.py             # JWT token signing, validation, and password hashing
│       ├── config.py           # Pydantic BaseSettings class loading ENV variables
│       ├── database.py         # SQLAlchemy engine setup and SQLite fallback fallback
│       ├── models.py           # Database tables schemas (User, Destination, Trip, Itinerary, etc.)
│       ├── schemas.py          # Pydantic schemas validating input/output JSON payloads
│       ├── seed.py             # Pre-seeding script containing 50 Indian destinations
│       ├── routers/
│       │   ├── auth.py         # Auth endpoints (Signup, Signin, Me profile)
│       │   ├── destinations.py # Destination Catalog endpoints (Pagination, filters, unique lists)
│       │   ├── expenses.py     # Expense Ledger endpoints (CRUD transactions, difference statistics)
│       │   ├── trips.py        # Core Plan generator, regional calculators, rules optimizer, and ReportLab PDF builder
│       │   └── ai_placeholders.py # Abstract endpoints routing to AI service boundaries
│       └── services/
│           └── openai.py       # OpenAI interface boundary class ready for future API keys hook
└── frontend/
    ├── Dockerfile              # Multi-stage build (Node build compile -> Nginx serve)
    ├── package.json
    ├── vite.config.ts          # Vite bundler configuration utilizing @tailwindcss/vite
    └── src/
        ├── App.tsx             # Route declarations wrapped with context provider hierarchies
        ├── index.css           # Tailwind v4 import and class-based variant definition
        ├── main.tsx            # Entry point rendering strict mode and ThemeProvider
        ├── components/
        │   ├── Layout.tsx      # Sidebar Shell structure with page headers and theme toggle
        │   └── ProtectedRoute.tsx # Route guards checking AuthContext status
        ├── context/
        │   ├── AuthContext.tsx # Context managing active JWT sessions
        │   └── ThemeContext.tsx# Context managing light/dark document classes
        ├── services/
        │   └── api.ts          # Axios wrapper instance pre-configured for /api calls
        └── pages/
            ├── LandingPage.tsx # SaaS homepage showcasing screenshots, testimonials, and features
            ├── Login.tsx       # Sign in card with validation errors
            ├── Register.tsx    # Sign up form
            ├── Dashboard.tsx   # Aggregations, Recharts comparators, and logged travel cards
            ├── BudgetPlanner.tsx # Main sliding form with gauges, itinerary checklists, and buffers
            ├── ReverseSearch.tsx # Value-ranking query panel outputting top 5 matching destinations
            ├── DestinationExplorer.tsx # Catalog grid implementing paging, category tags, and search
            ├── DestinationDetail.tsx # Detailed view containing base cost items and recommended schedules
            ├── BudgetOptimizer.tsx # Side-by-side comparative table executing rules-based optimizations
            ├── ExpenseTracker.tsx # Interactive transaction logs and estimation difference graphs
            └── AICompanion.tsx # LLM placeholder workspace (Chat, Planner, Regenerator, Explain)
```

---

## ⚡ Core Architectural Engines & Algorithms

### 1. Weighted Destination Scoring Matrix
To return the most logical destination, the backend scoring engine evaluates all pre-seeded locations using a weighted matrix:
$$\text{Score} = 40\% \times \text{Budget Fit} + 25\% \times \text{Category Match} + 15\% \times \text{Rating} + 10\% \times \text{Comfort Match} + 10\% \times \text{Duration Suitability}$$

1. **Budget Fit (40% weight):**
   * If the calculated trip cost $C$ is under the user's budget $B$, the fit score is $1.0 - \frac{B - C}{B}$ (encouraging destinations that maximize comfort close to the budget limits).
   * If the trip cost exceeds the budget, it is heavily penalized: $\max\left(0.0, 1.0 - \frac{C-B}{B} \times 4\right)$.
2. **Category Match (25% weight):**
   * Blends the main destination category match (60% weight) with the specific sub-category score (40% weight) loaded from database columns (e.g. `nature_score`, `adventure_score`). This allows multi-dimensional locations (like Rishikesh, which has both high `adventure` and `religious` profiles) to rise to the top dynamically.
3. **Rating (15% weight):**
   * Normalized rating: $\frac{\text{Rating}}{5.0}$.
4. **Comfort Match (10% weight):**
   * Computes differences between user comfort settings and destination baseline profiles: $1.0 - \frac{|\text{Comfort Slider} - \text{Comfort Level}|}{100}$.
5. **Duration Suitability (10% weight):**
   * Scores duration alignment: $1.0 - \frac{|\text{Requested Days} - \text{Recommended Duration}|}{5}$.

### 2. Regional Surcharges & Starting City Logic
To make the starting location impact travel recommendations, the platform implements a regional routing calculator. Destinations and starting cities are grouped into region clusters (North, South, East, West).
* **Intra-Region Travel:** If the starting city region matches the destination state region, transport base cost is discounted by **55%** (simulating shorter local drives, bus transits, or local trains).
* **Cross-Country Travel:** Opposite-region matches (e.g. North starting city to South destination) apply a **1.45x surcharge multiplier** on baseline transport costs.
* **Adjacent Region Travel:** Calculated at a standard **1.0x rate**.
* *Changing the starting city immediately recalculates travel costs, modifying the budget fit score, and recommending a different optimal destination.*

### 3. Rules-Based Budget Optimizer
Allows users to optimize an expensive trip by applying deterministic optimization policies:
* **Hotel Downgrade:** Reduces lodging category (Luxury $\rightarrow$ Mid-Range, Mid-Range $\rightarrow$ Budget), saving 35% to 50% on accommodation.
* **Transit Swap:** Swaps flights to trains for trips with high comfort scores, replacing transit costs with train estimates.
* **Itinerary Streamlining:** Reduces daily activity count by 50%, lowering tickets and entrance fees.
* **Surplus Upgrade:** If the trip is under-budget with remaining cash surplus, it suggests upgrading to luxury lodging.

---

## 🌓 Persistent Global Theme System

The application implements a custom class-based dark/light theme switcher backed by a React Context hook (`ThemeContext`):
* **Tailwind v4 Integration:** Enabled class-based listening by declaring the variant inside the CSS file:
  ```css
  @variant dark (&:where(.dark, .dark *));
  ```
* **Persistence:** User selections are saved to `localStorage` under the key `theme` with values `"light"` or `"dark"`. The selection is restored on application startup, and remains persistent after registrations, login sessions, and logouts.
* **Responsive Visuals:** Cards, inputs, layouts, and Recharts components adapt instantly. Recharts Tooltips read the theme state to dynamically adjust backgrounds and text styles (`#1e293b` vs `rgba(255,255,255,0.9)`), ensuring readability in both modes.

---

## 🚀 Step-by-Step Installation & Setup

### Method 1: Local Development (Bare Metal)

#### Prerequisites
* Node.js v18+
* Python 3.10+
* PostgreSQL (Optional, defaults to SQLite auto-fallback automatically)

#### 1. Start the Backend API
1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and source a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Launch the Uvicorn server:
   ```bash
   uvicorn main:app --reload
   ```
   * *Note: The server checks for PostgreSQL. If not found, it gracefully initializes a local SQLite file `budgetbound.db` and seeds all 50 destinations instantly.*

#### 2. Start the Frontend Client
1. Navigate to the `frontend/` directory in a new terminal window:
   ```bash
   cd frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Access the web application at `http://localhost:5173`.

---

### Method 2: Multi-Container Deployment (Docker Compose)

Deploy the entire stack—including PostgreSQL Database, FastAPI Backend, and React Frontend—using Docker:
```bash
docker-compose up --build
```
* **React Web Frontend:** `http://localhost:3000`
* **FastAPI documentation (Swagger Docs):** `http://localhost:8000/docs`
* **PostgreSQL Port:** `5432`

---

## 🔍 Database Seed Details (50 Destinations)
The seeding database covers scenic Indian locations distributed across 8 categories:
* **Beach:** North Goa, South Goa, Gokarna, Varkala, Havelock Island, Kovalam, Pondicherry, etc.
* **Nature:** Munnar, Coorg, Ooty, Wayanad, Kodaikanal, Araku Valley, Srinagar, etc.
* **Adventure:** Manali, Leh Ladakh, Rishikesh, Auli, Spiti Valley, Bir Billing, Gulmarg, etc.
* **Romantic:** Darjeeling, Nainital, Udaipur, Alleppey Houseboat, Shimla, Mount Abu, Kasauli, etc.
* **Religious:** Kedarnath, Varanasi, Haridwar, Rishikesh Temple, Amritsar, Tirupati, Rameshwaram, etc.
* **City Exploration:** Bengaluru, Mumbai, Delhi, Hyderabad, Kolkata, Jaipur, Chandigarh, etc.
* **Solo:** Hampi, Ziro Valley, Mcleodganj, Kasol, Gokarna Hostels, Pushkar, Vashisht, etc.
* **Family:** Mahabaleshwar, Lonavala, Ooty Family, South Goa Resorts, Mysore, Mount Abu Parks, etc.
