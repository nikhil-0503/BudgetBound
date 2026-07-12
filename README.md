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

$$\text{Score} = 40\% \times \text{Budget Fit} + 25\% \times \text{Category Match} + 15\% \times \text{Rating} + 10\% \times \text{Comfort Match} + 10\% \times \text{Duration Suitability}$$

- **Budget Fit (40%):** Rewards destinations that use budget efficiently; heavily penalizes over-budget options
- **Category Match (25%):** Blends main category (60%) with sub-category scores from DB columns (`nature_score`, `adventure_score`, etc.)
- **Rating (15%):** Normalized to 0–1 from a 5-star scale
- **Comfort Match (10%):** Alignment between user comfort slider and destination `comfort_level`
- **Duration Suitability (10%):** Alignment with `recommended_duration`

### 2. Regional Surcharges

Starting city and destination are mapped to region clusters (North, South, East, West):

- **Same region:** 0.45× transport multiplier (55% discount)
- **Opposite regions** (e.g. North ↔ South): 1.45× surcharge
- **Adjacent regions:** 1.0× standard rate

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
