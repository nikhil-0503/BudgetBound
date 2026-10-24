# BudgetBound: Member 1 Responsibility & Explanation Guide

**Member:** 1 (Trip Planning & Budget Intelligence)  
**Complexity Score:** 13.4/42.6 (31.4% of total workload)  
**Responsibility Tier:** Lead ownership of trip planning logic and budget optimization algorithms  
**Owned Features:** 7 features + 3 algorithms

---

## Owned Features Overview

| # | Feature | Backend Files | Frontend Files | Complexity | Status |
|---|---------|---|---|-----------|--------|
| 1 | Interactive Trip Planner | `trips.py` (create/update/get) | BudgetPlanner.tsx, CustomPlannerItinerary.tsx, LocationPickerModal.tsx, TripFlowGuide.tsx | 3 | ✅ Full |
| 2 | Budget Optimizer (Algorithm) | `multistop_calculator.py` (200+ lines) | BudgetOptimizer.tsx, BudgetAllocationEditor.tsx, BudgetHealthMeter.tsx | 5 | ✅ Full |
| 3 | Trip Comparison | `trip_comparison.py`, `multistop_calculator.py` | CompareDestinations.tsx, SavedTrips.tsx | 4 | ✅ Full |
| 5 | Weather & Climate Data | `destination_database.py` (fetch/cache) | DestinationDetail.tsx, DestinationExplorer.tsx | 2 | ✅ Full |
| 8 | Carbon Footprint Calculator | `multistop_calculator.py` (CO₂ model) | BudgetOptimizer.tsx, BudgetPlanner.tsx | 3 | ✅ Full |
| 9 | Multi-Stop Trip Planner | `trips.py`, `multistop_calculator.py` (TSP) | MultiStopPlanner.tsx, CompareDestinations.tsx | 5 | ✅ Full |
| 10 | Packing Checklist | `destination_database.py` (AI generation) | DestinationDetail.tsx, TripChecklist.tsx (Member 3) | 2 | ✅ Full |
| **Total** | | | | **24.4** | |

---

## Frontend Files Owned

**Pages:**
| File | Location | LOC | Purpose |
|------|----------|-----|---------|
| BudgetPlanner.tsx | `frontend/src/pages/BudgetPlanner.tsx` | 1477 | Dual-mode trip planner (discover/plan, location picker, cost calculation, itinerary editor) |
| BudgetOptimizer.tsx | `frontend/src/pages/BudgetOptimizer.tsx` | 396 | Cost-cut/upgrade recommendations, side-by-side allocation comparison |
| MultiStopPlanner.tsx | `frontend/src/pages/MultiStopPlanner.tsx` | 453 | Multi-city route optimizer with TSP solver visualization |
| CompareDestinations.tsx | `frontend/src/pages/CompareDestinations.tsx` | 747 | Side-by-side destination comparison, cost analysis, travel metrics |
| DestinationDetail.tsx | `frontend/src/pages/DestinationDetail.tsx` | 345 | Individual destination info, weather, packing recommendations, cost breakdown |
| ReverseSearch.tsx | `frontend/src/pages/ReverseSearch.tsx` | 399 | Reverse trip finder (budget → destinations matching algorithm) |
| SavedTrips.tsx | `frontend/src/pages/SavedTrips.tsx` | 609 | Trip history, filtering, sorting, comparison access |

**Components:**
| File | Location | LOC | Purpose |
|------|----------|-----|---------|
| CustomPlannerItinerary.tsx | `frontend/src/components/CustomPlannerItinerary.tsx` | 532 | Day-by-day itinerary editor with activity input |
| TimelineItinerary.tsx | `frontend/src/components/TimelineItinerary.tsx` | 152 | Visual timeline display of trip activities |
| BudgetAllocationEditor.tsx | `frontend/src/components/BudgetAllocationEditor.tsx` | 289 | Interactive budget slider controls for category allocation |
| BudgetHealthMeter.tsx | `frontend/src/components/BudgetHealthMeter.tsx` | 128 | Visual health indicator (on-track status gauge) |
| LocationPickerModal.tsx | `frontend/src/components/LocationPickerModal.tsx` | 208 | Destination selection with map integration |
| TripFlowGuide.tsx | `frontend/src/components/TripFlowGuide.tsx` | 71 | Step-by-step trip creation wizard |

**Total Frontend LOC for Member 1:** 5,806 lines
**Frontend Components (Key UI Elements):**
- `BudgetPlanner.tsx` uses 25+ React hooks (useState, useEffect, useCallback, useContext, useReducer, useRef)
- `CompareDestinations.tsx` integrates complex cost comparison logic and analytics
- Interactive charts, sliders, modals, and map components
- All components make API calls to backend trip/destination/optimizer services

---

## Core Responsibilities

### 1. Trip Planner (Feature 1)
**What you own:** End-to-end trip creation, retrieval, and modification logic

**Key Files:**
- `backend/app/routers/trips.py` — API layer (lines 1–150)
- `backend/app/models.py` — Trip & Itinerary models (lines 120–370)
- `backend/app/database.py` — CRUD functions for trips
- `backend/app/schemas.py` — Pydantic validation schemas

**What you need to explain:**
- How trip data flows from frontend form → API → database
- Trip validation rules (dates, budget, travelers)
- Cascading creation (Trip + Itineraries)
- Date range constraints and error handling

**Code Reference:**
```python
# backend/app/routers/trips.py - create_trip()
@router.post("/trips")
async def create_trip(trip_data: TripCreate, db: Session = Depends(get_db)):
    # Validate: start_date <= end_date
    # Validate: budget >= 0
    # Validate: traveler_count >= 1
    trip = db.create_trip(trip_data)
    return trip
```

**Frontend Implementation (BudgetPlanner.tsx):**

```typescript
// frontend/src/pages/BudgetPlanner.tsx
// ~1200 LOC, 25+ hooks

export function BudgetPlanner() {
  // State management
  const [mode, setMode] = useState<"discover" | "plan">("discover");
  const [tripData, setTripData] = useState<TripCreate>({...});
  const [locations, setLocations] = useState<Destination[]>([]);
  const [estimatedCost, setEstimatedCost] = useState<number>(0);
  
  // API integration
  const { mutate: createTrip, isLoading } = useMutation(
    (data: TripCreate) => api.post("/trips", data),
    { onSuccess: (data) => navigate(`/trip/${data.id}`) }
  );
  
  // UI flow
  return (
    <div className="budget-planner">
      <Tabs value={mode} onChange={setMode}>
        {/* Mode 1: Discover - Browse destinations, auto-estimate costs */}
        <Discover 
          onSelectDestinations={(dests) => setLocations(dests)}
          onEstimateCost={(cost) => setEstimatedCost(cost)}
        />
        
        {/* Mode 2: Plan - Create structured trip with itinerary */}
        <Plan 
          tripData={tripData}
          onChange={setTripData}
          onSubmit={() => createTrip(tripData)}
          isLoading={isLoading}
        />
      </Tabs>
    </div>
  );
}
```

Key features you implemented:
- Location picker with autocomplete (calls `/destinations` API)
- Cost calculator preview (calls `/trips/estimate-cost`)
- Multi-step form with validation
- Real-time budget preview
- Itinerary day-by-day editor

**Viva Questions (Sample):**
1. What happens if a user creates a trip with start_date > end_date?
2. How are itineraries linked to trips in the database?
3. What cascade rules apply when deleting a trip?
4. Explain the TripCreate schema and its validation.
5. How does the frontend handle the multi-step trip creation form?
6. What hooks does BudgetPlanner use and why? (useState, useEffect, useReducer, useCallback, etc.)
7. How do you handle loading states and errors in the frontend?

---

### 2. Budget Optimizer (Feature 2 - Algorithm)
**What you own:** The complex optimization algorithm that redistributes budget across categories

**Importance:** This is a core algorithmic feature that requires explanation of mathematical reasoning

**Key Files:**
- `backend/app/services/multistop_calculator.py` (lines 1–200)
- `backend/app/routers/trips.py` (lines 200–280, calls optimizer)
- `backend/app/services/explainability.py` (generates explanations)

**Algorithm Explanation:**

**Problem Statement:**
- User has a total trip budget (e.g., $5000)
- User has initial expense estimates (food: $1500, accommodation: $2000, activities: $1000, transport: $500)
- User has preferences (e.g., prefers to spend more on activities, less on food)
- **Goal:** Redistribute budget while respecting constraints and preferences

**Mathematical Model:**
```
Inputs:
  B = total budget ($5000)
  C = categories {accommodation, food, transport, activities, misc}
  O_i = original estimate for category i
  P_i = preference weight for category i (0-1, sum=1)
  min_i = minimum required spend for category i (e.g., transport >= $200)
  max_i = maximum allowed spend for category i

Objective:
  Minimize: Σ P_i * |O_i - X_i| / max(1, O_i)
    where X_i = optimized spend for category i
    (deviation = how far we deviate from original preference)

Constraints:
  1. Σ X_i = B (total spend = budget)
  2. X_i ≥ min_i (lower bounds)
  3. X_i ≤ max_i (upper bounds)
  4. X_i ≥ 0 (non-negative)

Solution Method:
  Linear programming (scipy.optimize.linprog)
  Alternative: Simple proportional allocation with constraint satisfaction
```

**Example:**
```
User Budget: $5000
Categories & Estimates:
  - Accommodation: $2000 (40%)
  - Food: $1500 (30%)
  - Transport: $500 (10%)
  - Activities: $1000 (20%)

User Preferences: Wants more activities, less food
Optimization Output:
  - Accommodation: $1900 (38%) ← reduced slightly
  - Food: $1200 (24%) ← reduced per preference
  - Transport: $600 (12%) ← maintained
  - Activities: $1300 (26%) ← increased per preference
  Total: $5000 ✓
```

**Code Reference:**
```python
# backend/app/services/multistop_calculator.py
def calculate_optimized_budget(expenses, budget, preferences):
    """
    expenses = [Expense objects grouped by category]
    budget = total trip budget
    preferences = {category: preference_weight}
    
    Returns: optimized_allocation[category] = amount
    """
    # 1. Extract original estimates per category
    original = {cat: sum([e.amount for e in expenses if e.category==cat]) for cat in categories}
    
    # 2. Define constraints
    # 3. Setup linear program
    # 4. Solve
    # 5. Return solution
```

**What you need to explain:**
- Why linear programming is appropriate for this problem
- How constraints are enforced (minimum accommodation, etc.)
- The optimization objective (minimize deviation from preferences)
- Edge cases (what if min_i > budget? what if budget too small?)
- How to generate user-friendly explanation ("We reduced food by 20% to increase activities")

**Frontend Implementation (BudgetOptimizer.tsx):**

```typescript
// frontend/src/pages/BudgetOptimizer.tsx
// ~450 LOC, 12+ hooks

export function BudgetOptimizer({ tripId }: { tripId: number }) {
  const [originalBudget, setOriginalBudget] = useState<BudgetAllocation>({...});
  const [optimizedBudget, setOptimizedBudget] = useState<BudgetAllocation>({...});
  const [recommendations, setRecommendations] = useState<string[]>([]);
  
  // Fetch original allocation
  useEffect(() => {
    api.get(`/trips/${tripId}/budget`).then(setOriginalBudget);
  }, [tripId]);
  
  // Call optimization endpoint
  const { mutate: runOptimizer } = useMutation(
    () => api.post(`/trips/${tripId}/optimize-budget`, { preferences }),
    { onSuccess: (data) => {
      setOptimizedBudget(data.allocation);
      setRecommendations(data.explanation);
    } }
  );
  
  // UI: Side-by-side comparison
  return (
    <div className="budget-optimizer">
      <div className="comparison">
        <BudgetColumn title="Original" data={originalBudget} />
        <BudgetColumn title="Optimized" data={optimizedBudget} />
      </div>
      
      {/* Interactive sliders to adjust preferences */}
      <PreferenceSliders onChange={runOptimizer} />
      
      {/* Recommendation explanations */}
      <RecommendationsList items={recommendations} />
      
      {/* Charts showing allocation changes */}
      <AllocationChart original={originalBudget} optimized={optimizedBudget} />
    </div>
  );
}
```

Key features:
- Side-by-side budget comparison view
- Interactive preference sliders (accommodation, food, activities, etc.)
- Real-time optimization API calls
- Visual charts (pie, bar) showing cost distribution
- Recommendation explanations from backend

**Viva Questions (Sample):**
1. Explain the optimization objective. Why minimize deviation?
2. What happens if the budget is less than the sum of all minimum requirements?
3. How would you handle a preference for a category that's infeasible?
4. Can the optimizer guarantee a feasible solution? When would it fail?
5. How is this different from simple proportional allocation?
6. How do you visualize the optimization results in the frontend?
7. What happens when the user adjusts preference sliders? (state update, API call flow)

---

### 3. Trip Comparison (Feature 3)
**What you own:** Side-by-side analysis of multiple trips to identify spending patterns

**Key Files:**
- `backend/app/routers/trip_comparison.py` (full file)
- `backend/app/services/multistop_calculator.py` (lines 300–400, comparison logic)

**What comparison includes:**
- Total cost per trip
- Cost per person (total / travelers)
- Cost per day (total / duration)
- Category breakdown (food $, transport $, etc.)
- Spending variance analysis
- Identification of outliers (most/least expensive categories)

**Code Reference:**
```python
# backend/app/routers/trip_comparison.py
def compare_trips(trip_ids: list, db: Session):
    """
    Accepts: [trip_id_1, trip_id_2, trip_id_3]
    Returns:
      {
        "trips": [
          {
            "trip_id": 1,
            "name": "Paris",
            "total_cost": 5000,
            "cost_per_person": 1250,
            "cost_per_day": 250,
            "by_category": {...}
          },
          ...
        ],
        "summary": {
          "most_expensive": "Paris ($5000)",
          "least_expensive": "Barcelona ($3000)",
          "average": 4000,
          "variance": 1000
        }
      }
    """
```

**What you need to explain:**
- Data aggregation logic (how you sum expenses per trip)
- Per-person cost calculation (why it matters)
- Per-day cost calculation (enables destination comparison fairness)
- Variance analysis (statistical reasoning)
- Use case: helping users decide between trips or learn spending patterns

**Viva Questions (Sample):**
1. Why is cost-per-day more useful than total cost for comparison?
2. How do you handle trips of different duration in comparison?
3. What if two trips have different numbers of travelers?
4. How would you identify a "suspicious" trip with unusual spending?
5. How is comparison data stored/retrieved?

---

### 4. Weather & Climate Data (Feature 5)
**What you own:** Weather fetching, caching, and packing recommendations based on climate

**Key Files:**
- `backend/app/routers/destinations.py` (lines 250–350, weather endpoint)
- `backend/app/services/destination_database.py` (lines 300–400, weather fetch logic)

**Weather Data Flow:**
```
User views destination detail
  ↓
Frontend calls: GET /api/destinations/{dest_id}/weather
  ↓
Backend checks cache (WeatherCache model)
  ├─ If cached & fresh (<24h): return cached data
  └─ If expired: fetch from OpenWeatherMap API
       ↓
       API returns: {temp, feels_like, humidity, wind, precipitation}
       ↓
       Backend caches result + timestamp
       ↓
       Return to frontend
```

**External API:**
- **Provider:** OpenWeatherMap (free tier)
- **Endpoint:** `https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}`
- **Response:** Temperature (°C/°F), humidity (%), wind speed (m/s), precipitation (mm), cloudiness (%)

**Caching Strategy:**
```python
# backend/app/models.py - WeatherCache model
class WeatherCache(Base):
    destination_id = Column(Integer, ForeignKey("destination.id"))
    weather_json = Column(JSON)  # Entire API response
    timestamp = Column(DateTime, default=datetime.utcnow)
    
# Cache validation logic:
cached_data = db.query(WeatherCache).filter_by(dest_id=123).first()
if cached_data and (datetime.utcnow() - cached_data.timestamp).hours < 24:
    return cached_data.weather_json  # Fresh
else:
    # Fetch new data
```

**Code Reference:**
```python
# backend/app/services/destination_database.py
def fetch_weather_data(destination):
    """
    destination = Destination model with latitude, longitude
    Returns: weather dict with temp, humidity, wind, etc.
    """
    cache = db.query(WeatherCache).filter_by(destination_id=destination.id).first()
    
    if cache and fresh(cache.timestamp):
        return cache.weather_json
    
    # Fetch from API
    response = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather",
        params={"lat": destination.latitude, "lon": destination.longitude, "appid": API_KEY}
    )
    data = response.json()
    
    # Cache it
    db.create(WeatherCache, destination_id=destination.id, weather_json=data)
    
    return data
```

**What you need to explain:**
- Why caching is important (rate limits, performance)
- How 24-hour cache expiry is enforced
- Fallback behavior if API is down (serve stale cache)
- Security: API key management
- Weather-to-packing logic (below)

**Packing Recommendations Logic:**
```
Weather Data → Packing List:
  - If temp < 10°C: jacket, gloves, hat, thermal layers
  - If temp > 25°C: sunscreen, light clothing, hat, sunglasses
  - If humidity > 70% & temp > 20°C: moisture-wicking fabrics
  - If wind > 30 km/h: windbreaker
  - If precipitation > 5mm: raincoat, umbrella, waterproof bag
  - If tropical climate: insect repellent, quick-dry clothing
```

**Viva Questions (Sample):**
1. Why cache weather data? What's the tradeoff between freshness and performance?
2. How does the system handle API downtime?
3. What's the logic for generating packing recommendations from weather?
4. How would you handle destinations with extreme weather variability?
5. What privacy concerns exist with using latitude/longitude data?

---

### 5. Carbon Footprint Calculator (Feature 8)
**What you own:** CO₂ emission estimation and offset recommendations

**Key Files:**
- `backend/app/services/multistop_calculator.py` (lines 500–600, CO₂ calculation)
- `backend/app/routers/trips.py` (lines 350–450, carbon endpoint)

**Algorithm: CO₂ Emissions Calculation**

**Emission Factors (kg CO₂ per km):**
```
Flight (domestic):     0.255 kg CO₂/km per passenger
Flight (international): 0.195 kg CO₂/km per passenger (includes radiative forcing)
Car (average):         0.192 kg CO₂/km per vehicle
Train (average):       0.041 kg CO₂/km per passenger
Bus (average):         0.089 kg CO₂/km per passenger
```

**Calculation Method:**
```python
def estimate_co2_emissions(trip):
    """
    trip = Trip object with transport modes and distances
    
    Algorithm:
      For each transport segment:
        1. Determine transport mode (flight, car, train, bus)
        2. Get distance (from origin to destination coordinates)
        3. Lookup emission factor
        4. Calculate: emissions = distance * emission_factor / number_of_passengers
        5. Sum all segments
    
    Returns: total_kg_co2, breakdown_by_mode
    """
    total_co2 = 0
    breakdown = {}
    
    for segment in trip.transport_segments:
        distance = haversine(segment.origin, segment.destination)
        factor = EMISSION_FACTORS[segment.mode]
        co2 = distance * factor / segment.passengers
        
        total_co2 += co2
        breakdown[segment.mode] = breakdown.get(segment.mode, 0) + co2
    
    return total_co2, breakdown
```

**Example Calculation:**
```
Trip: London → Paris (flight) + Paris stay + Paris → Amsterdam (train)

Segment 1: Flight London-Paris
  - Distance: 340 km
  - Emission factor: 0.255 kg CO₂/km (short-haul)
  - Passengers: 2
  - CO₂ = 340 * 0.255 / 2 = 43.35 kg CO₂

Segment 2: Train Paris-Amsterdam
  - Distance: 510 km
  - Emission factor: 0.041 kg CO₂/km
  - Passengers: 2
  - CO₂ = 510 * 0.041 / 2 = 10.455 kg CO₂

Total: 53.805 kg CO₂
```

**Carbon Offset Recommendations:**
```python
def calculate_offsets(total_kg_co2):
    """
    Returns: list of offset options
    """
    offsets = {
        "tree_planting": {
            "trees_needed": total_kg_co2 / 20,  # 1 tree ≈ 20 kg CO₂/year
            "cost_per_tree": 10,  # USD
            "total_cost": (total_kg_co2 / 20) * 10
        },
        "renewable_energy": {
            "kWh_equivalent": total_kg_co2 * 0.45,  # 1 kWh ≈ 2.2 kg CO₂
            "cost_per_kWh": 0.15,
            "total_cost": total_kg_co2 * 0.45 * 0.15
        },
        "verified_credits": {
            "credits_needed": total_kg_co2 / 1000,
            "cost_per_credit": 25,
            "total_cost": (total_kg_co2 / 1000) * 25
        }
    }
    return offsets
```

**What you need to explain:**
- Source of emission factors (IPCC, EPA, etc.)
- Why radiative forcing is considered for flights
- Why passengers matter (shared transport = lower per-person emissions)
- Offset calculation methods (trees, renewable energy, carbon credits)
- Environmental impact: helping users reduce footprint

**Viva Questions (Sample):**
1. Why is the emission factor for flights higher than trains?
2. Explain radiative forcing and why it's added to flight emissions.
3. How do you calculate haversine distance? Why not use road distance?
4. What's the uncertainty in CO₂ estimates? How accurate is this model?
5. How would you incorporate renewable energy usage in offset calculation?
6. Is the model appropriate for all countries (varying electricity mixes)?

---

### 6. Multi-Stop Trip Planner (Feature 9 - Algorithm)
**What you own:** Complex route optimization for multi-destination trips (Traveling Salesman Problem)

**Importance:** This is an advanced algorithmic feature requiring careful explanation

**Key Files:**
- `backend/app/routers/trips.py` (lines 500–650, multistop endpoints)
- `backend/app/services/multistop_calculator.py` (lines 600–800, TSP solver)

**Problem Statement:**
- User wants to visit multiple destinations (e.g., London → Paris → Amsterdam → Brussels)
- Budget is fixed ($10,000)
- Trip duration is fixed (14 days)
- **Goal:** Find optimal order to minimize travel cost and maximize experience

**Algorithm: Traveling Salesman Problem (TSP)**

**Exact Problem Formulation:**
```
Given:
  - n destinations (cities)
  - Distance matrix D (n × n) where D[i][j] = haversine distance
  - Cost matrix C (n × n) where C[i][j] = travel cost (flight/train/etc)
  - Duration per stop (days_i for destination i)
  - Budget B (total trip budget)

Objective:
  Find permutation π of destinations that:
    1. Minimizes total travel cost: Σ C[π[i]][π[i+1]]
    2. Satisfies: Σ duration[i] ≤ trip_length
    3. Satisfies: total_cost ≤ B

NP-Hard: Optimal solution requires checking (n-1)! permutations
         For n=10, that's 362,880 solutions
```

**Solution Method: Nearest Neighbor + 2-Opt Heuristic**

```python
def calculate_optimal_route(origin, destinations, budget, trip_days):
    """
    Heuristic approach (not optimal, but fast):
    
    Step 1: Nearest Neighbor Construction
      1. Start at origin
      2. Repeat: Go to nearest unvisited destination
      3. Mark as visited
      Returns: initial_tour
    
    Step 2: Local Improvement (2-Opt)
      1. For each pair of edges in tour:
        - Try swapping them (reverse segment)
        - If cost decreases: accept swap
      2. Repeat until no improvement
      Returns: improved_tour
    
    Step 3: Cost Check
      - Calculate total cost for tour
      - If cost > budget: remove least valuable stop
      - Repeat until feasible
    """
    
    # Implementation
    current_location = origin
    visited = set()
    tour = [origin]
    
    # Nearest neighbor
    while len(visited) < len(destinations):
        nearest = min(
            [d for d in destinations if d not in visited],
            key=lambda d: haversine(current_location, d)
        )
        tour.append(nearest)
        visited.add(nearest)
        current_location = nearest
    
    # 2-opt improvement
    improved = True
    while improved:
        improved = False
        for i in range(1, len(tour)-1):
            for j in range(i+1, len(tour)):
                # Try reversing segment [i:j]
                new_tour = tour[:i] + tour[i:j][::-1] + tour[j:]
                if cost(new_tour) < cost(tour):
                    tour = new_tour
                    improved = True
    
    return tour
```

**Example:**
```
Trip: Start in London, visit Paris, Amsterdam, Brussels
Days: 14 total, spend 3-4 days at each city
Budget: $5000

Distances (km):
  London - Paris: 340
  London - Amsterdam: 358
  London - Brussels: 315
  Paris - Amsterdam: 510
  Paris - Brussels: 300
  Amsterdam - Brussels: 210

Nearest Neighbor Output:
  1. London (start)
  2. Brussels (315 km, closest)
  3. Amsterdam (210 km from Brussels)
  4. Paris (510 km from Amsterdam)
  Total distance: 315 + 210 + 510 = 1035 km

2-Opt Check:
  - Try: London → Paris → Amsterdam → Brussels
    Distance: 340 + 510 + 210 = 1060 km (worse, keep original)
  - Try: London → Amsterdam → Paris → Brussels
    Distance: 358 + 510 + 300 = 1168 km (worse, keep original)
  
Final Tour: London → Brussels → Amsterdam → Paris (1035 km, optimal)

Cost Allocation (Budget: $5000):
  - Transport cost: $600 (flights/trains)
  - Accommodation ($100/night × 12 nights): $1200
  - Food & Activities: $3200
  Total: $5000 ✓
```

**What you need to explain:**
- Why TSP is NP-hard (exponential growth)
- Why heuristic approach is necessary (speed vs optimality tradeoff)
- Nearest Neighbor algorithm and its limitations
- 2-Opt improvement step (edge swapping)
- Budget feasibility check and constraint satisfaction
- Real-world applicability vs perfect optimization

**Viva Questions (Sample):**
1. What's the time complexity of your TSP solver?
2. Why is Nearest Neighbor not optimal? Give a counterexample.
3. Explain 2-Opt improvement. How does it work?
4. Can your algorithm guarantee a solution under budget?
5. How would you solve TSP for 20 destinations (vs 10)?
6. What happens if no feasible tour exists (budget too small)?
7. How does adding time windows (must visit city X at specific days) change the problem?

---

### 7. Packing Checklist (Feature 10)
**What you own:** AI-generated packing lists based on trip context and weather

**Key Files:**
- `backend/app/routers/trips.py` (lines 700–800, packing endpoint)
- `backend/app/services/destination_database.py` (lines 400–500, AI generation)
- `backend/app/services/gemini.py` or `openai.py` (LLM integration)

**Packing List Generation Process:**

```python
def generate_packing_list(trip):
    """
    Inputs:
      - trip duration (days)
      - destination (location, climate)
      - trip dates (season)
      - activities (hiking, beach, cultural, etc.)
      - travelers (solo, family, couple)
      - weather forecast
    
    Process:
      1. Fetch weather data for destination
      2. Determine season and climate
      3. Extract activities from trip itinerary
      4. Construct LLM prompt with all context
      5. Call Gemini/OpenAI
      6. Parse response into structured items
      7. Categorize items (clothing, toiletries, electronics, etc.)
      8. Estimate total weight
      9. Store in database
    """
    
    weather = fetch_weather_data(trip.destination)
    activities = extract_activities(trip.itinerary)
    
    prompt = f"""
    Generate a packing list for a {trip.duration}-day trip to {trip.destination.name}
    in {trip.start_date.month} (season: {get_season(trip.start_date)}).
    
    Weather: Temperature {weather.temp}°C, {weather.humidity}% humidity, {weather.precipitation}mm rain
    
    Activities: {', '.join(activities)}
    
    Travelers: {trip.traveler_count} people
    
    Generate a comprehensive packing list with items grouped by category.
    Format: JSON with items, categories, quantities, and weight estimates.
    Include essentials, weather-appropriate clothing, and activity-specific gear.
    """
    
    response = llm.generate_text(prompt, temperature=0.3)
    packing_list = parse_json(response)
    
    return packing_list
```

**Example Output:**
```json
{
  "categories": [
    {
      "name": "Clothing",
      "items": [
        {"name": "T-shirt", "quantity": 5, "weight_kg": 0.3},
        {"name": "Jeans", "quantity": 2, "weight_kg": 0.6},
        {"name": "Jacket", "quantity": 1, "weight_kg": 0.8},
        {"name": "Socks", "quantity": 7, "weight_kg": 0.2},
        {"name": "Underwear", "quantity": 7, "weight_kg": 0.15}
      ]
    },
    {
      "name": "Toiletries",
      "items": [
        {"name": "Toothbrush", "quantity": 1, "weight_kg": 0.05},
        {"name": "Toothpaste", "quantity": 1, "weight_kg": 0.1},
        {"name": "Sunscreen (SPF 50)", "quantity": 1, "weight_kg": 0.2}
      ]
    },
    {
      "name": "Electronics",
      "items": [
        {"name": "Phone charger", "quantity": 1, "weight_kg": 0.1},
        {"name": "Power bank", "quantity": 1, "weight_kg": 0.3}
      ]
    },
    {
      "name": "Activity-Specific",
      "items": [
        {"name": "Hiking boots", "quantity": 1, "weight_kg": 1.0},
        {"name": "Swimsuit", "quantity": 2, "weight_kg": 0.3}
      ]
    }
  ],
  "total_weight_kg": 5.2,
  "recommendations": "Pack light shoes for urban areas to save weight"
}
```

**What you need to explain:**
- How prompt engineering works (what context you provide to LLM)
- Temperature setting (0.3 for deterministic packing vs 0.7 for creative suggestions)
- Parsing LLM output (from text to structured JSON)
- Fallback behavior if LLM fails
- Weight estimation accuracy
- How to make suggestions personalized (family vs solo traveler)

**Viva Questions (Sample):**
1. How do you ensure the packing list is appropriate for the destination climate?
2. Why use temperature=0.3 for packing lists vs other features?
3. How would you handle invalid JSON responses from the LLM?
4. Can you update a packing list if weather changes before the trip?
5. How would you prevent hallucinated items (e.g., "giraffe repellent")?
6. What's the user experience for checking off items as packed?

---

## Key Algorithms Summary

| Algorithm | Location | Complexity | Use Case |
|-----------|----------|-----------|----------|
| Budget Optimization | `multistop_calculator.py:calculate_optimized_budget()` | O(n) → O(n²) with solver | Redistribute budget across categories |
| Traveling Salesman Problem | `multistop_calculator.py:calculate_optimal_route()` | Heuristic O(n²) | Multi-stop route optimization |
| CO₂ Emission Calculation | `multistop_calculator.py:estimate_co2_emissions()` | O(n) | Carbon footprint estimation |
| Trip Comparison | `multistop_calculator.py:compare_trip_costs()` | O(n·m) | Aggregate expenses across trips |
| Weather Caching | `destination_database.py:fetch_weather_data()` | O(1) with cache | Fetch and cache weather for 24h |
| Packing List Generation | `destination_database.py:generate_packing_list()` | O(1) API call | AI-generate checklist from context |

---

## Viva Preparation Checklist

**Before your viva, be able to explain:**

1. ✓ Trip planner data flow (frontend → API → database)
2. ✓ Budget optimizer algorithm (linear programming, constraints, objective)
3. ✓ Why trip comparison matters (per-person, per-day metrics)
4. ✓ Weather data caching strategy (24h expiry, API fallback)
5. ✓ Carbon footprint calculation (emission factors, passenger count)
6. ✓ TSP solver (nearest neighbor + 2-opt, why not optimal)
7. ✓ Packing list generation (LLM prompt engineering, JSON parsing)
8. ✓ Error handling in all features (budget infeasibility, API downtime, JSON parsing)
9. ✓ Database model relationships (Trip → Expense → BudgetAlert)
10. ✓ API endpoint design (RESTful conventions, request/response schemas)

---

## Code Reading Exercise

**Before your viva, read and understand:**
1. `backend/app/routers/trips.py` (lines 1–150) — Trip CRUD
2. `backend/app/services/multistop_calculator.py` (lines 1–600) — All algorithms
3. `backend/app/services/destination_database.py` (lines 300–500) — Weather + Packing
4. `backend/app/models.py` (Trip, Itinerary, Expense, Destination models)

---

## Common Viva Traps & How to Avoid

| Trap | How to Avoid |
|------|-------------|
| "What if budget is negative?" | Show validation: `assert budget > 0` in create_trip() |
| "Does optimizer always find solution?" | Explain constraints: if infeasible, return error + suggest larger budget |
| "How accurate are CO₂ factors?" | Cite source (IPCC/EPA), mention ±10% uncertainty |
| "Why not use GPS for distance?" | Explain haversine is good enough, GPS adds complexity |
| "Does LLM always generate valid JSON?" | Show error handling: try/except with fallback template |
| "How many destinations can TSP handle?" | Honest answer: ~15 efficient, 20+ gets slow, heuristic needed |

---

## Suggested Talking Points

**When asked "Tell us about your features":**

"I was responsible for trip planning and budget intelligence features. The core is the **Budget Optimizer**, a linear programming algorithm that redistributes trip budget across expense categories while respecting user preferences and constraints. I also implemented **Multi-Stop Trip Planning**, which solves a simplified TSP using nearest neighbor + 2-opt heuristic to find efficient routes for multi-city trips.

Beyond algorithms, I built practical features: **Carbon Footprint Calculation** to estimate emissions and suggest offsets, **Weather Data** caching strategy for performance, and **Packing Checklist** generation using LLMs. I also contributed **Trip Comparison** for users to analyze spending patterns across multiple trips.

The complexity came from balancing mathematical rigor (algorithms) with practical constraints (budget feasibility, API rate limits, caching strategies). All features are integrated with the Trip model and expense tracking system."

---

**End of Member 1 Guide**
