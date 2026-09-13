# BudgetBound — Budget-First Travel Planning Platform

BudgetBound is a full-stack travel planning platform built around a **budget-first discovery model**.

Instead of asking users where they want to go first, BudgetBound flips the travel discovery equation:

1. **What is your budget?** (e.g., ₹15,000, ₹50,000)
2. **Where are you starting from?** (e.g., Bangalore, Delhi, Mumbai — with an interactive map picker)
3. **How many days do you have?** (e.g., 3 days, 5 days)
4. **What type of trip do you want?** (Beach, Adventure, Nature, Religious, Romantic, City Exploration, etc.)

Based on these constraints and a comfort slider (0–100), the platform scores and ranks destinations, generates a day-by-day itinerary, predicts hidden expenses (taxes, local transit, emergency reserve), compares planned vs. actual spending, and exports offline PDF itineraries.

---

## Key Features

| Module | Route | Description |
|--------|-------|-------------|
| **Dashboard** | `/dashboard` | Trip summaries, budget vs. estimated vs. actual charts, expense category breakdown |
| **Trip Flow** | `/planner` | Budget-first planner — set constraints, get the best destination, full cost breakdown, and itinerary |
| **Destination Discovery** | `/reverse-search` | Same planner UI in *discover* mode — returns top 5 ranked destinations without committing to a plan |
| **Destination Explorer** | `/explorer`, `/explorer/:id` | Paginated catalog with search, category filters, and detailed destination pages |
| **Budget Optimizer** | `/optimizer/:tripId` | Rules-based cost optimization (hotel downgrade, transit swap, itinerary trim, surplus upgrade) |
| **Expense Tracker** | `/expenses/:tripId` | Log transactions by category, compare against estimates, view difference stats |
| **AI Companion** | `/ai-companion` | Groq-powered travel chat assistant (other AI tabs are planned) |

---

## Comprehensive Feature Breakdown

### 1. User Authentication & Security
* **Secure Signup & Login**: Credentials-based signup and login flows with email validation.
* **JWT-Based Session Tracking**: Stateless authentication using JSON Web Tokens (`HS256`). A React interceptor automatically attaches authorization headers to all outgoing requests.
* **Bcrypt Password Cryptography**: Passwords are securely hashed with bcrypt inside the database using standard salt rounds.
* **Forgot Password Flow**: Simple 2-step password reset directly in the app (no email needed). Users verify their email and set a new password instantly. See `SIMPLIFIED_FORGOT_PASSWORD.md` for details.
* **Client-Side Auth Guards**: React Router middleware (`ProtectedRoute` and `AnonymousRoute`) keeps unauthenticated users out of private views (planner, dashboard, optimizer, expenses) and automatically redirects authenticated users away from the login/signup screens.
* **Auto-Session Cleanup**: Axios request/response interceptors automatically log the user out and redirect them to the login page on a `401 Unauthorized` status response.

### 2. Budget-First Travel Planner & Discovery (`/planner`)
* **Interactive Map Location Picker**: Visual starting-city selector powered by **Leaflet & React-Leaflet**. Users can search for a starting city or place a pin on the interactive map, which geocodes/reverse-geocodes their selection using the Nominatim OpenStreetMap API.
* **Weighted Scoring Recommendation Engine**: Ranks destinations by checking how well they match constraints using a multi-criteria scoring algorithm:
  * **35% Budget Fit**: Prefers destinations utilizing budget efficiently. Excludes over-budget destinations entirely unless show over-budget is checked (Hard Budget Constraint).
  * **25% Category Match**: Blends main category matching with sub-category affinities.
  * **12% User Rating**: Normalizes destination rating to a 5-star standard.
  * **20% Comfort Match**: Aligns comfort level expectations with the destination profile (Comfort slider has a dynamic and strong influence).
  * **8% Duration Match**: Checks constraints against the destination's recommended duration.
* **Pacing & Comfort Slider**: Adjusts a slider between 0 and 100 to dynamically shift lodging recommendations (Budget, Mid-Range, Luxury), transport styles (Train vs. Flight), activities per day, and cost multipliers.
* **Detailed Cost Estimator**: Calculates costs across multiple categories: base transport, lodging (hotel), meals (food), activity fees, local transport, booking taxes (12%), and emergency reserve buffers (8%).
* **Itinerary Generator**: Constructs day-by-day plans with morning, afternoon, and evening slots. Integrates with the Groq API (e.g. `gemma2-9b-it`, `llama-3.1-8b-instant`) to generate customized itineraries, with an offline static template fallback system.
* **Trip Saving & Database Commit**: Saves the generated trip details, calculated budget allocations, and day-by-day itineraries to the database.

### 3. Dynamic Analytics Dashboard (`/dashboard`)
* **Summary Analytics Cards**: Real-time stats showing Total Trips Planned, Total Planned Budget, Total Spent (Actual Expenses), and Net Savings.
* **Trip Budget Comparison (Recharts Bar Chart)**: Dynamic visualization showing the financial health of the user's top 6 trips by comparing the original starting budget, the estimated planning cost, and the actual logged expenses side-by-side.
* **Expense Categories Breakdown (Recharts Pie Chart)**: Clean color-coded pie chart showing aggregate spending distribution across Transport, Hotel, Food, Activities, Shopping, and Other categories.
* **Recent Trips Feed**: Chronological feed of the 5 most recent planned trips with quick-view statistics.

### 4. Interactive Destination Catalog (`/explorer`)
* **Live Search & Filter**: Real-time keyword filtering of destinations by name, state, or keywords.
* **Advanced Filters**: Quick-select filters based on categories (Beach, Nature, Adventure, Religious, City Exploration, Romantic) and locations.
* **Detailed Explorer Card Profile**: Cards showing ratings, recommend duration, category badges, and budget level tags.
* **Rich Destination Detail Page (`/explorer/:id`)**: Displays high-res visual assets, seasonal planning recommendations, base travel stats, geographic context, and a checklist of popular tourist attractions.

### 5. Rules-Based Budget Optimizer (`/optimizer/:tripId`)
* **Dynamic Target Estimation**: Calculates current trip estimates and compares them with the initial budget to highlight deficits or surpluses.
* **Actionable Cost-Cut Recommendations**:
  * *Lodging Tier Downgrades*: Swaps luxury resorts to mid-range hotels, or mid-range hotels to cozy local homestays/hostels (saving 35-50% on lodging).
  * *Transit Method Swap*: Replaces flights with AC sleeper trains for a budget-friendly transit alternative.
  * *Itinerary Trimming*: Lowers pre-booked activities by 50% to save on tickets and entry fees.
* **Actionable Comfort Upgrades**:
  * *Surplus Upgrades*: Suggests premium room/hotel upgrades if the trip estimated cost is significantly under budget.
* **One-Click Apply**: Previews exact cost differences and applies adjustments directly, updating database allocations in real-time.

### 6. Expense Ledger & Tracker (`/expenses/:tripId`)
* **Transaction Logging CRUD**: Record expenses with exact dates, amounts, categories, and custom notes.
* **Variance Analysis Graphs**: Compares the user's actual spending against the pre-calculated budget allocations for each category. If no expenses exist, displays the "Planned Budget Allocation" chart. If expenses exist, shows a comparison of "Planned vs. Actual Spend".
* **Variance Indicator Badge**: Shows real-time difference figures (under-budget vs. over-budget) to highlight categories causing budget leaks. Shows warning cards and Forecasts.

### 7. Groq AI Travel Companion Chatbot (`/ai-companion`)
* **Interactive AI Interface**: Direct chat window to ask travel questions, local guidelines, packing tips, or regional cuisines.
* **Groq Llama/Gemma Model Integration**: Utilizes fast AI inference through the Groq SDK, configurable to models like `gemma2-9b-it`, `llama-3.1-8b-instant`, or `llama-3.3-70b-versatile`.
* **Smart fallback architecture**: Backend automatically falls back to static template rendering when `GROQ_API_KEY` is not present, keeping the application fully functional.

### 8. High-Fidelity PDF Export Generator
* **Aesthetic PDF Document Layout**: Clean document formats built using ReportLab, sporting modern fonts and aligned grid components.
* **Budget Breakdown Charts**: Aligns estimated costs, taxes, and reserves in structured tables.
* **Day-by-Day Travel Guide**: Embeds detailed activity timelines (Morning, Afternoon, Evening) for offline travel support.
* **Disk-Free PDF Streaming**: Streams raw PDF bytes from system memory straight to the user's browser, eliminating disk clutter.

### 9. Multi-Adapter Database Fallback
* **Automatic Database Engine Selector**: Connects to a robust PostgreSQL server by default, but automatically registers a local SQLite database adapter (`budgetbound.db`) if PostgreSQL is offline or unreachable.
* **60 Pre-seeded Indian Destinations**: Seeding system that populates the database with 60 detailed destinations categorized across 6 primary travel types.

---

## Technical Stack

### Frontend
- **Framework:** React 19 with TypeScript (Vite 8)
- **Styling:** Tailwind CSS v4 with class-based dark mode and glassmorphism
- **Routing:** React Router v7 with inline `ProtectedRoute` / `AnonymousRoute` guards in `App.tsx`
- **Charts:** Recharts (budget comparison bars, expense category pie charts)
- **Maps:** Leaflet + React-Leaflet (interactive starting-city picker via OpenStreetMap/Nominatim)
- **Icons:** Lucide React
- **HTTP Client:** Axios with JWT request interceptors and 401 session handling

### Backend
- **Framework:** FastAPI (Python 3.11) on Uvicorn
- **Database:** PostgreSQL with automatic **SQLite fallback** (`budgetbound.db`) when PostgreSQL is unreachable
- **ORM:** SQLAlchemy 2.x
- **Auth:** JWT bearer tokens (HMAC-SHA256) + bcrypt password hashing via `passlib`
- **PDF Reports:** ReportLab (multi-page travel plan PDFs)
- **AI:** Groq API (`gemini.py` service) for itinerary generation and chat; template fallback when no API key is set

---

## Project Structure

```
BudgetBound/
├── docker-compose.yml          # PostgreSQL + backend + frontend orchestration
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── main.py                 # FastAPI entry point, CORS, auto-seed on startup
│   ├── requirements.txt
│   └── app/
│       ├── auth.py             # JWT signing, validation, password hashing
│       ├── config.py           # Pydantic settings (DB, JWT, env)
│       ├── database.py         # SQLAlchemy engine with PostgreSQL → SQLite fallback
│       ├── models.py           # User, Destination, Trip, Itinerary, Expense
│       ├── schemas.py          # Pydantic request/response schemas
│       ├── seed.py             # 60 pre-seeded Indian destinations
│       ├── routers/
│       │   ├── auth.py         # Register, login, profile
│       │   ├── destinations.py # Catalog, filters, detail
│       │   ├── expenses.py     # Expense CRUD and trip stats
│       │   ├── trips.py        # Planning, scoring, optimizer, PDF export
│       │   └── ai_placeholders.py # AI chat and planned AI endpoints
│       └── services/
│           ├── gemini.py       # Groq-powered itinerary + chat (active)
│           └── openai.py       # OpenAI interface stub for future integration
└── frontend/
    ├── Dockerfile              # Node build → Nginx static serve
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── App.tsx             # Routes and auth guards
        ├── main.tsx            # ThemeProvider wrapper
        ├── index.css           # Tailwind v4 + dark variant
        ├── components/
        │   ├── Layout.tsx              # Sidebar shell, nav, theme toggle
        │   ├── LocationPickerModal.tsx # Leaflet map + city search
        │   └── TripFlowGuide.tsx       # Step-by-step planner guide UI
        ├── context/
        │   ├── AuthContext.tsx
        │   └── ThemeContext.tsx
        ├── services/
        │   └── api.ts          # Axios instance (http://localhost:8000)
        └── pages/
            ├── LandingPage.tsx
            ├── Login.tsx / Register.tsx
            ├── Dashboard.tsx
            ├── BudgetPlanner.tsx       # Plan + discover modes (replaces standalone reverse search)
            ├── DestinationExplorer.tsx / DestinationDetail.tsx
            ├── BudgetOptimizer.tsx
            ├── ExpenseTracker.tsx
            └── AICompanion.tsx
```

---

## Core Algorithms

### 1. Weighted Destination Scoring

$$\text{Score} = 35\% \times \text{Budget Fit} + 25\% \times \text{Category Match} + 12\% \times \text{Rating} + 20\% \times \text{Comfort Match} + 8\% \times \text{Duration Suitability}$$

- **Budget Fit (35%):** Rewards destinations that use budget efficiently. Budget is enforced as a **hard constraint**—destinations over budget are filtered out.
- **Category Match (25%):** Blends main category (60%) with sub-category affinities from DB columns.
- **Rating (12%):** Normalized to 0–1 from a 5-star scale.
- **Comfort Match (20%):** Stronger alignment between comfort slider (0-100) and destination's comfort profile.
- **Duration Suitability (8%):** Suitability check compared with recommended trip days.

### 2. Regional Surcharges

Starting city and destination are mapped to region clusters (North, South, East, West). Multipliers are applied directly to base transport costs first, ensuring regional differences remain after minimum cost floors:

- **Same region:** 0.45× transport multiplier (55% discount)
- **South ↔ West (e.g. Chennai ↔ Goa):** 1.05× multiplier (medium-short haul)
- **North ↔ West (e.g. Delhi ↔ Goa), North ↔ East (e.g. Delhi ↔ Kolkata):** 1.25× multiplier (medium-long haul)
- **North ↔ South (e.g. Delhi ↔ Chennai), East ↔ West (e.g. Kolkata ↔ Mumbai):** 1.45× multiplier (long haul)

### 3. Rules-Based Budget Optimizer

- **Hotel Downgrade:** Luxury → Mid-Range → Budget (35–50% lodging savings)
- **Transit Swap:** Replace flights with trains for high-comfort trips
- **Itinerary Streamlining:** Halve daily activities to cut ticket costs
- **Surplus Upgrade:** Suggest luxury lodging when under budget

---

## Theme System

Class-based dark/light mode via `ThemeContext`:

```css
@variant dark (&:where(.dark, .dark *));
```

Selection persists in `localStorage` under the key `theme`. Recharts tooltips adapt background and text colors for both modes.

---

## AI Integration (Groq)

The backend uses the **Groq API** (not OpenAI) for AI features:

| Feature | Status | Notes |
|---------|--------|-------|
| **Itinerary generation** | Active | Used during trip planning; falls back to templates if `GROQ_API_KEY` is missing |
| **AI chat** (`/api/ai/chat`) | Active | Interactive travel companion in AI Companion page |
| **Trip regeneration** | Planned | Returns 501 |
| **Budget explanation** | Planned | Returns 501 |
| **Personalized planner** | Planned | Returns 501 |

Set `GROQ_API_KEY` in `backend/.env` to enable AI. Default model is `gemma2-9b-it`; override with `GROQ_MODEL`.

---

## Environment Variables

Create `backend/.env` with:

```env
# Database (PostgreSQL; falls back to SQLite if unreachable)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/budgetbound

# Auth
JWT_SECRET_KEY=your_secret_key_here

# Groq AI (optional — templates used when absent)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=gemma2-9b-it
```

The frontend API base URL is set in `frontend/src/services/api.ts` (`http://localhost:8000`).

---

## Installation & Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL (optional — SQLite fallback works out of the box)

### Local Development

**1. Backend**

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

On startup, the server creates tables, attempts PostgreSQL, falls back to `budgetbound.db` if needed, and seeds 60 destinations.

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

**2. Frontend** (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

### Docker Compose

```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | `http://localhost:3000` |
| Backend API / Docs | `http://localhost:8000` / `http://localhost:8000/docs` |
| PostgreSQL | `localhost:5432` |

---

## API Overview

| Prefix | Endpoints |
|--------|-----------|
| `/api/auth` | `POST /register`, `POST /login`, `POST /login-json`, `GET /me` |
| `/api/destinations` | `GET /`, `GET /states`, `GET /categories`, `GET /{id}` |
| `/api/trips` | `POST /plan`, `POST /`, `GET /`, `GET /{id}`, `DELETE /{id}`, `GET /reverse/search`, `POST /{id}/optimize`, `POST /{id}/optimize/apply`, `GET /{id}/pdf` |
| `/api/expenses` | `POST /`, `GET /trip/{trip_id}`, `PUT /{id}`, `DELETE /{id}`, `GET /trip/{trip_id}/stats` |
| `/api/ai` | `POST /chat`, `POST /regenerate`, `POST /explain`, `POST /personalized-plan` |
| `/api/dashboard` | `GET /stats` |

---

## Database Seed (60 Destinations)

Six categories, 10 destinations each:

| Category | Examples |
|----------|----------|
| **Beach** | North Goa, South Goa, Gokarna, Varkala, Havelock Island, Kovalam, Pondicherry |
| **Nature** | Munnar, Coorg, Ooty, Wayanad, Kodaikanal, Araku Valley |
| **Adventure** | Manali, Leh Ladakh, Rishikesh, Auli, Spiti Valley, Bir Billing, Gulmarg |
| **Religious** | Kedarnath, Varanasi, Haridwar, Amritsar, Tirupati, Rameshwaram |
| **City Exploration** | Mumbai, Delhi, Bengaluru, Hyderabad, Kolkata, Jaipur, Chandigarh, Chennai |
| **Romantic** | Srinagar, Udaipur, Darjeeling, Nainital, Alleppey Houseboat, Shimla |

Each destination includes expanded metadata: `budget_tier`, `recommended_duration`, `comfort_level`, and per-category affinity scores used by the scoring engine.
