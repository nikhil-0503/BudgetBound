# BudgetBound: Member 3 Responsibility & Explanation Guide

**Member:** 3 (AI Services & Advanced Features)  
**Complexity Score:** 14.6/42.6 (34.3% of total workload)  
**Responsibility Tier:** Lead ownership of AI/LLM integrations and advanced features  
**Owned Features:** 3 features + 4 advanced systems

---

## Owned Features Overview

| # | Feature | Backend Files | Frontend Files | Complexity | Status |
|---|---------|---|---|-----------|--------|
| 17 | AI Trip Chat Assistant | `routers/ai_placeholders.py`, `groq_model_discovery.py` | AICompanion.tsx (5 tabs), FeedbackStates.tsx, MarkdownMessage.tsx | 5 | ⚠️ Partial |
| 18 | PDF Report Generator | `routers/documents.py`, `pdf_generator.py` | DocumentManager.tsx (Member 2), ExplainabilityReport.tsx | 4 | ✅ Full |
| 2 | Budget Optimizer (Explainability) | `services/explainability.py` | ExplainabilityReport.tsx, RecommendationExplainability.tsx | 2 | ✅ Full |
| 9 | Multi-Stop Planner (TSP Integration) | `services/multistop_calculator.py` | MultiStopPlanner.tsx (Member 1), AICompanion.tsx | 4 | ✅ Full |
| + | Gemini/OpenAI LLM Integration | `services/gemini.py`, `openai.py` | AICompanion.tsx, ExplainabilityReport.tsx | 3 | ✅ Full |
| + | Itinerary Validator | `services/itinerary_validator.py` | CustomPlannerItinerary.tsx (Member 1), AICompanion.tsx | 2 | ✅ Full |
| + | Personalized Plan Validator | `services/personalized_plan_validator.py` | AICompanion.tsx, RecommendationExplainability.tsx | 1 | ✅ Full |
| **Total** | | | | **21.6** | |

## Frontend Files Owned

**Pages:**
| File | Location | LOC | Purpose |
|------|----------|-----|---------|
| AICompanion.tsx | `frontend/src/pages/AICompanion.tsx` | 641 | 5-tab AI interface (chat, planner, regenerator, explainability, multistop) |
| AdminAnalyticsPage.tsx | `frontend/src/pages/AdminAnalyticsPage.tsx` | 303 | Admin dashboard with user metrics, system health, spending analytics |
| Dashboard.tsx | `frontend/src/pages/Dashboard.tsx` | 638 | Main user analytics dashboard (shared with Member 2, see feature split) |
| LandingPage.tsx | `frontend/src/pages/LandingPage.tsx` | 338 | Public landing page with feature overview and CTAs |

**Components:**
| File | Location | LOC | Purpose |
|------|----------|-----|---------|
| ExplainabilityReport.tsx | `frontend/src/components/ExplainabilityReport.tsx` | 366 | Display AI optimization explanations and recommendations |
| RecommendationExplainability.tsx | `frontend/src/components/RecommendationExplainability.tsx` | 107 | Show budget recommendations with reasoning |
| TripChecklist.tsx | `frontend/src/components/TripChecklist.tsx` | 222 | Interactive packing list with AI-generated items |
| FeedbackStates.tsx | `frontend/src/components/FeedbackStates.tsx` | 101 | Loading, error, empty states for AI features |

**Total Frontend LOC for Member 3:** 2,716 lines
**Frontend Components (Key UI Elements):**
- `AICompanion.tsx` uses 20+ hooks with real-time streaming chat integration
- Real-time analytics dashboards with Recharts visualizations
- LLM response rendering with markdown and code block support
- Admin-only access control and role-based UI rendering

---

## Frontend Implementation Details

### Dashboard.tsx (900 LOC)

```typescript
// frontend/src/pages/Dashboard.tsx
export function Dashboard({ userId }: { userId: number }) {
  const [dashboardData, setDashboardData] = useState({});
  const [tripsSummary, setTripsSummary] = useState({});
  const [budgetCharts, setBudgetCharts] = useState({});
  const [forecasts, setForecasts] = useState({});
  
  // Fetch all dashboard data
  useEffect(() => {
    Promise.all([
      api.get("/api/dashboard"),
      api.get("/api/trips/summary"),
      api.get("/api/budget-analytics"),
      api.get("/api/forecasts")
    ]).then(([dashboard, trips, budgets, forecasts]) => {
      setDashboardData(dashboard);
      setTripsSummary(trips);
      setBudgetCharts(budgets);
      setForecasts(forecasts);
    });
  }, []);
  
  return (
    <div className="dashboard">
      {/* Row 1: Summary stats cards */}
      <StatsGrid
        totalBudget={dashboardData.budget.total_budget}
        totalSpent={dashboardData.budget.total_spent}
        activeTrips={dashboardData.trips.active}
        completedTrips={dashboardData.trips.completed}
      />
      
      {/* Row 2: Budget breakdown pie chart + trend line chart */}
      <ChartsGrid
        pieData={budgetCharts.byCategory}
        trendData={budgetCharts.monthlyTrend}
      />
      
      {/* Row 3: Recent trips table with quick actions */}
      <RecentTripsTable
        trips={tripsSummary.recentTrips}
        onViewTrip={(id) => navigate(`/trip/${id}`)}
      />
      
      {/* Row 4: Forecast vs actual spending */}
      <ForecastChart
        forecast={forecasts.nextMonth}
        actual={forecasts.thisMonth}
      />
    </div>
  );
}
```

Key features:
- Summary statistics (total budget, spent, trips)
- Real-time budget charts (pie, trend, forecast)
- Recent trips list with quick access
- Budget forecasts based on spending patterns
- Responsive grid layout

**Viva Questions (Sample):**
1. How do you aggregate data from multiple endpoints for the dashboard?
2. What's the data structure for the budget charts?
3. How do you handle loading states across multiple API calls?
4. How do you calculate forecasts from historical data?
5. What hooks are used for state management and API integration?

### AdminAnalyticsPage.tsx (Advanced)

```typescript
// frontend/src/pages/AdminAnalyticsPage.tsx
export function AdminAnalyticsPage() {
  const [adminData, setAdminData] = useState({});
  const [userGrowth, setUserGrowth] = useState([]);
  const [spendingTrends, setSpendingTrends] = useState([]);
  const [systemHealth, setSystemHealth] = useState({});
  
  // Require admin role
  useRequireAdminRole();
  
  useEffect(() => {
    Promise.all([
      api.get("/api/admin/users/growth"),
      api.get("/api/admin/spending-trends"),
      api.get("/api/admin/system-health")
    ]).then(([growth, spending, health]) => {
      setUserGrowth(growth);
      setSpendingTrends(spending);
      setSystemHealth(health);
    });
  }, []);
  
  return (
    <div className="admin-analytics">
      {/* User Growth Chart */}
      <LineChart
        data={userGrowth}
        title="User Growth (30 days)"
        xAxis="date"
        yAxis="count"
      />
      
      {/* Spending Trends */}
      <BarChart
        data={spendingTrends}
        title="Average Spending by User"
        xAxis="timeperiod"
        yAxis="amount"
      />
      
      {/* System Health Metrics */}
      <SystemHealthPanel
        uptime={systemHealth.uptime}
        responseTime={systemHealth.avgResponseTime}
        errorRate={systemHealth.errorRate}
        activeUsers={systemHealth.activeUsers}
      />
    </div>
  );
}
```

Key features:
- User growth analytics
- Spending trend analysis
- System health monitoring (uptime, latency, errors)
- Admin-only access control
- Real-time data refresh

---

## Core Responsibilities

### 1. AI Trip Chat Assistant (Feature 17 - Advanced)
**What you own:** Conversational AI chatbot powered by Groq API for trip planning advice

**Importance:** Core AI feature; currently returning 501 errors (partial implementation)

**Status:** ⚠️ Partially Implemented — API integration exists but Groq API key not configured in `.env`

**Key Files:**
- `backend/app/routers/ai_placeholders.py` (lines 1–100)
- `backend/app/services/groq_model_discovery.py` (lines 1–300)
- `backend/app/models.py` (ChatMessage model)
- `.env` (missing GROQ_API_KEY)

**Architecture: Chat System**

```
User types: "I'm going to Paris with $5000 budget for 10 days. What should I prioritize?"
  ↓
Frontend: POST /api/ai/chat
  ├─ body: {message: "...", trip_id: 123 (optional)}
  ├─ headers: Authorization: Bearer {jwt_token}
  └─ Returns: {response, id, created_at}
  ↓
Backend: routers/ai_placeholders.py → chat_with_ai()
  ├─ Authenticate user (verify JWT)
  ├─ Extract trip context (if trip_id provided)
  ├─ Build conversation history (get last 10 messages)
  ├─ Call groq_model_discovery.chat_with_groq()
  └─ Store message in database
  ↓
Backend: services/groq_model_discovery.py → chat_with_groq()
  ├─ Format conversation history with system prompt
  ├─ Call Groq API: https://api.groq.com/openai/v1/chat/completions
  ├─ Handle streaming (optional, for real-time response)
  └─ Parse response + return to router
  ↓
Frontend:
  ├─ Display assistant response
  ├─ Store in local chat history
  └─ Enable follow-up messages
```

**Groq API Integration:**

```python
# backend/app/services/groq_model_discovery.py

import requests
from typing import List, Dict

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Must be set in .env

class GroqClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "mixtral-8x7b-32768"  # Default model (fast, general-purpose)
        self.models_available = ["mixtral-8x7b-32768", "llama2-70b-4096"]
    
    def get_available_models(self) -> List[str]:
        """
        Discover available Groq models
        
        Alternative: Can call /models endpoint to get real-time list
        For now: hardcoded known models
        """
        return self.models_available
    
    def select_model(self, request_type: str) -> str:
        """
        Choose model based on request type
        
        - "general": Mixtral (faster, good for general Q&A)
        - "complex": Llama-2-70b (slower, better reasoning)
        
        Returns: model name string
        """
        if request_type == "complex":
            return "llama2-70b-4096"
        return "mixtral-8x7b-32768"
    
    def chat_with_groq(self, messages: List[Dict], request_type: str = "general") -> str:
        """
        Send chat message to Groq API
        
        messages = [
            {"role": "system", "content": "You are a helpful travel budget advisor..."},
            {"role": "user", "content": "I have $5000 for Paris. What should I prioritize?"},
            {"role": "assistant", "content": "Accommodation in Paris typically costs..."},
            {"role": "user", "content": "What about food?"}
        ]
        
        Returns: assistant response text
        """
        
        model = self.select_model(request_type)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            assistant_message = data["choices"][0]["message"]["content"]
            
            return assistant_message
        
        except requests.exceptions.Timeout:
            return "Request timed out. Please try again."
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return "API authentication failed. Check GROQ_API_KEY."
            elif e.response.status_code == 429:
                return "Rate limit exceeded. Please try again in a moment."
            else:
                return f"API error: {e.response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def stream_response(self, messages: List[Dict]) -> Iterator[str]:
        """
        Stream response for real-time chat feel
        
        Yields chunks of assistant response as they arrive
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "stream": True
        }
        
        try:
            response = requests.post(GROQ_API_URL, json=payload, headers=headers, stream=True)
            
            for line in response.iter_lines():
                if line:
                    # Parse Server-Sent Events (SSE) format
                    # Format: data: {"choices":[{"delta":{"content":"..."}}]}
                    if line.startswith(b'data: '):
                        data_str = line[6:].decode('utf-8')
                        if data_str == "[DONE]":
                            break
                        
                        data = json.loads(data_str)
                        content = data["choices"][0]["delta"].get("content", "")
                        
                        if content:
                            yield content
        
        except Exception as e:
            yield f"\nError: {str(e)}"
```

**Backend Router:**

```python
# backend/app/routers/ai_placeholders.py

from fastapi import APIRouter, Depends, HTTPException
from backend.app.services.groq_model_discovery import GroqClient
from backend.app.models import ChatMessage
from backend.app.auth import verify_token

router = APIRouter(prefix="/api/ai", tags=["AI"])

@router.post("/chat")
async def chat_with_ai(
    chat_input: ChatInput,  # {"message": "...", "trip_id": optional int}
    current_user = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Send message to AI assistant
    
    chat_input = {
        "message": "I have $5000 for Paris for 10 days. What should I prioritize?",
        "trip_id": 123  (optional)
    }
    
    Response: {
        "id": 1,
        "message": "...",
        "response": "...",
        "created_at": "2024-01-15T10:30:00Z"
    }
    """
    
    user_id = current_user["sub"]
    
    # Store user message
    user_msg = ChatMessage(
        user_id=user_id,
        role="user",
        content=chat_input.message,
        trip_context_id=chat_input.trip_id
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    
    # Get conversation history
    history = db.query(ChatMessage)\
        .filter_by(user_id=user_id)\
        .order_by(ChatMessage.created_at.desc())\
        .limit(20)\
        .all()
    
    # Reverse to maintain chronological order
    history.reverse()
    
    # Extract trip context if provided
    trip_context = ""
    if chat_input.trip_id:
        trip = db.query(Trip).filter_by(id=chat_input.trip_id, user_id=user_id).first()
        if trip:
            total_spent = db.query(func.sum(Expense.amount)).filter_by(trip_id=trip.id).scalar() or 0
            trip_context = f"""
            Current Trip Context:
            - Trip: {trip.name}
            - Budget: ${trip.budget} {trip.currency}
            - Spent: ${total_spent}
            - Duration: {(trip.end_date - trip.start_date).days} days
            - Travelers: {trip.traveler_count}
            """
    
    # Build system prompt
    system_prompt = f"""You are a helpful travel budget advisor for BudgetBound, a travel budgeting app.
    
Your role is to:
1. Help users plan trips within their budget
2. Provide spending recommendations by category (accommodation, food, transport, activities)
3. Suggest destination tips and activities
4. Help optimize trips for specific priorities (budget-conscious, luxury, adventure, cultural)
5. Answer questions about trip costs and travel logistics

Be concise, friendly, and practical. Give specific numbers when relevant.
{trip_context}
"""
    
    # Format messages for Groq API
    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    
    # Call Groq API
    groq_client = GroqClient(os.getenv("GROQ_API_KEY"))
    
    try:
        assistant_response = groq_client.chat_with_groq(messages)
    except Exception as e:
        # This is where 501 errors occur (API key not set or API down)
        return HTTPException(status_code=501, detail="AI service currently unavailable")
    
    # Store assistant response
    assistant_msg = ChatMessage(
        user_id=user_id,
        role="assistant",
        content=assistant_response,
        trip_context_id=chat_input.trip_id
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    
    return {
        "user_message_id": user_msg.id,
        "assistant_message_id": assistant_msg.id,
        "response": assistant_response,
        "created_at": assistant_msg.created_at
    }

@router.get("/chat/history")
async def get_chat_history(
    trip_id: Optional[int] = None,
    limit: int = 50,
    current_user = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get chat history for user (optionally filtered by trip)"""
    
    query = db.query(ChatMessage).filter_by(user_id=current_user["sub"])
    
    if trip_id:
        query = query.filter_by(trip_context_id=trip_id)
    
    messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
    messages.reverse()
    
    return {"messages": messages}

@router.delete("/chat/history")
async def clear_chat_history(
    current_user = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Clear all chat messages for user"""
    
    db.query(ChatMessage).filter_by(user_id=current_user["sub"]).delete()
    db.commit()
    
    return {"message": "Chat history cleared"}
```

**Current Issue (501 Errors):**

```
Root Cause: GROQ_API_KEY not set in .env
Error Location: backend/app/routers/ai_placeholders.py (lines 50–75)

When API key is missing:
  groq_client.chat_with_groq(messages)
    ↓
  requests.post() with Authorization: Bearer None
    ↓
  Groq API returns 401 Unauthorized
    ↓
  Backend catches and returns 501 ("Not Implemented")

Fix: Add to .env:
  GROQ_API_KEY=<your-groq-api-key>
  
Get key from: https://console.groq.com/keys
```

**What you need to explain:**
- Groq API basics (why Groq: fast inference, cheap)
- Model selection (Mixtral for speed, Llama for reasoning)
- Conversation context management (storing history)
- System prompt engineering (how to guide AI behavior)
- Error handling (timeouts, auth failures, rate limits)
- Streaming vs non-streaming responses
- Privacy: storing user conversations

**Viva Questions (Sample):**
1. Why use Groq instead of OpenAI/Gemini?
2. How do you maintain conversation context?
3. What's the system prompt and why is it important?
4. How would you prevent the AI from hallucinating (e.g., making up activities)?
5. How do you handle rate limiting from Groq API?
6. How do you store conversation history securely?
7. What's the cost vs latency tradeoff of different models?

---

### 2. PDF Report Generator (Feature 18)
**What you own:** Generate comprehensive PDF trip reports combining all trip data

**Importance:** HIGH — Complex document generation with data aggregation

**Key Files:**
- `backend/app/routers/documents.py` (lines 1–200, endpoints)
- `backend/app/services/pdf_generator.py` (lines 1–500, PDF generation)
- `backend/app/models.py` (Document model)

**Report Structure:**

```
Generated PDF: trip_report_Paris_Jan2024.pdf

Page 1: Cover Page
  - Trip Title: "My Paris Adventure"
  - Dates: January 1-10, 2024
  - Travelers: 2 people
  - Destination: Paris, France
  - Generated: January 15, 2024

Page 2: Summary
  - Total Budget: $5,000
  - Total Spent: $4,250
  - Budget Remaining: $750 (15% saved)
  - Daily Average: $425/day
  - Per Person Average: $2,125

Page 3: Itinerary
  Day 1 (Jan 1): Arrive Paris, check into hotel
    Location: Paris
    Cost: $150 (accommodation) + $50 (food) = $200
  
  Day 2 (Jan 2): Eiffel Tower, lunch at café
    Location: Paris
    Cost: $50 (Eiffel Tower) + $40 (food) = $90
  
  ... (one page per 2-3 days)

Page N-2: Expense Summary
  [Pie Chart]
  Accommodation: $1,500 (35%)
  Food: $1,200 (28%)
  Transport: $800 (19%)
  Activities: $600 (14%)
  Misc: $150 (4%)

Page N-1: Packing List
  Clothing
    ☐ T-shirt (5x)
    ☐ Jeans (2x)
    ☐ Jacket (1x)
  
  Toiletries
    ☐ Toothbrush
    ☐ Sunscreen
  
  Electronics
    ☐ Phone charger
    ☐ Power bank

Page N: Carbon Footprint
  Total Emissions: 53.8 kg CO₂
  
  Breakdown:
    Flight (London-Paris): 43.35 kg CO₂
    Train (Paris-Amsterdam): 10.45 kg CO₂
  
  Offset Recommendations:
    - Plant 2.7 trees (≈ 54 kg CO₂/year)
    - Cost: $27
    - Or: Support renewable energy (≈ 45 kg CO₂ offset)
    - Cost: $25
```

**PDF Generation Code:**

```python
# backend/app/services/pdf_generator.py

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from io import BytesIO

class TripReportGenerator:
    def __init__(self, trip, user):
        self.trip = trip
        self.user = user
        self.styles = getSampleStyleSheet()
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            leftMargin=1*inch,
            rightMargin=1*inch
        )
        self.story = []
    
    def generate(self) -> bytes:
        """Generate complete PDF report and return bytes"""
        
        # Add pages
        self.add_cover_page()
        self.add_summary_page()
        self.add_itinerary_page()
        self.add_expense_summary()
        self.add_packing_list()
        self.add_carbon_footprint()
        
        # Build PDF
        self.doc.build(self.story)
        
        # Get bytes
        self.buffer.seek(0)
        return self.buffer.getvalue()
    
    def add_cover_page(self):
        """Create title page"""
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#003366'),
            spaceAfter=10,
            alignment=1  # Center
        )
        
        self.story.append(Spacer(1, 2*inch))
        self.story.append(Paragraph(self.trip.name, title_style))
        self.story.append(Spacer(1, 0.3*inch))
        
        subtitle_style = ParagraphStyle('CustomSubtitle', fontSize=14, alignment=1)
        self.story.append(Paragraph(f"{self.trip.start_date.strftime('%B %d')} - {self.trip.end_date.strftime('%B %d, %Y')}", subtitle_style))
        
        self.story.append(Spacer(1, 0.3*inch))
        self.story.append(Paragraph(f"{self.trip.destination.country if self.trip.destination else 'Unknown'}", subtitle_style))
        
        self.story.append(Spacer(1, 3*inch))
        
        info_data = [
            ["Travelers", str(self.trip.traveler_count)],
            ["Budget", f"${self.trip.budget:,.2f}"],
            ["Duration", f"{(self.trip.end_date - self.trip.start_date).days} days"]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12)
        ]))
        
        self.story.append(info_table)
        self.story.append(PageBreak())
    
    def add_summary_page(self):
        """Create budget summary page"""
        
        total_spent = sum(e.amount for e in self.trip.expenses)
        remaining = self.trip.budget - total_spent
        percent_spent = (total_spent / self.trip.budget * 100) if self.trip.budget > 0 else 0
        days = (self.trip.end_date - self.trip.start_date).days
        daily_avg = total_spent / days if days > 0 else 0
        
        self.story.append(Paragraph("Budget Summary", self.styles['Heading1']))
        self.story.append(Spacer(1, 0.3*inch))
        
        summary_data = [
            ["Metric", "Amount"],
            ["Total Budget", f"${self.trip.budget:,.2f}"],
            ["Total Spent", f"${total_spent:,.2f}"],
            ["Remaining", f"${remaining:,.2f}"],
            ["Percent Spent", f"{percent_spent:.1f}%"],
            ["Daily Average", f"${daily_avg:,.2f}/day"],
            ["Per Person Average", f"${total_spent/self.trip.traveler_count:,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
        ]))
        
        self.story.append(summary_table)
        self.story.append(PageBreak())
    
    def add_itinerary_page(self):
        """Create day-by-day itinerary page"""
        
        self.story.append(Paragraph("Itinerary", self.styles['Heading1']))
        self.story.append(Spacer(1, 0.3*inch))
        
        for itinerary in sorted(self.trip.itineraries, key=lambda x: x.day):
            day_date = self.trip.start_date + timedelta(days=itinerary.day-1)
            self.story.append(Paragraph(f"Day {itinerary.day} - {day_date.strftime('%A, %B %d')}", self.styles['Heading2']))
            self.story.append(Paragraph(itinerary.activity, self.styles['Normal']))
            self.story.append(Spacer(1, 0.1*inch))
        
        self.story.append(PageBreak())
    
    def add_expense_summary(self):
        """Create expense breakdown page with chart"""
        
        self.story.append(Paragraph("Expense Breakdown", self.styles['Heading1']))
        self.story.append(Spacer(1, 0.3*inch))
        
        # Group expenses by category
        by_category = {}
        for expense in self.trip.expenses:
            if expense.category not in by_category:
                by_category[expense.category] = 0
            by_category[expense.category] += expense.amount
        
        total = sum(by_category.values())
        
        expense_data = [["Category", "Amount", "Percent"]]
        for category, amount in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            percent = (amount / total * 100) if total > 0 else 0
            expense_data.append([category, f"${amount:,.2f}", f"{percent:.1f}%"])
        
        expense_table = Table(expense_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        expense_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
        ]))
        
        self.story.append(expense_table)
        self.story.append(PageBreak())
    
    def add_packing_list(self):
        """Create packing list page"""
        
        self.story.append(Paragraph("Packing List", self.styles['Heading1']))
        self.story.append(Spacer(1, 0.3*inch))
        
        # Fetch packing list (if available)
        packing_list = db.query(PackingList).filter_by(trip_id=self.trip.id).first()
        
        if packing_list:
            for category_obj in packing_list.categories:
                self.story.append(Paragraph(category_obj["name"], self.styles['Heading2']))
                
                items_data = [["Item", "Qty"]]
                for item in category_obj["items"]:
                    items_data.append([item["name"], str(item["quantity"])])
                
                items_table = Table(items_data, colWidths=[3*inch, 1*inch])
                items_table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
                ]))
                
                self.story.append(items_table)
                self.story.append(Spacer(1, 0.2*inch))
        
        self.story.append(PageBreak())
    
    def add_carbon_footprint(self):
        """Create carbon footprint page"""
        
        self.story.append(Paragraph("Environmental Impact", self.styles['Heading1']))
        self.story.append(Spacer(1, 0.3*inch))
        
        carbon = db.query(CarbonFootprint).filter_by(trip_id=self.trip.id).first()
        
        if carbon:
            self.story.append(Paragraph(f"Total Emissions: {carbon.total_kg_co2:.1f} kg CO₂", self.styles['Heading2']))
            self.story.append(Spacer(1, 0.2*inch))
            
            # Breakdown by mode
            breakdown_data = [["Transport Mode", "kg CO₂"]]
            for mode, amount in carbon.by_transport_mode.items():
                breakdown_data.append([mode, f"{amount:.1f}"])
            
            breakdown_table = Table(breakdown_data, colWidths=[3*inch, 1.5*inch])
            breakdown_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#228B22')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
            ]))
            
            self.story.append(breakdown_table)
            self.story.append(Spacer(1, 0.2*inch))
            
            # Offset recommendations
            self.story.append(Paragraph("Offset Options:", self.styles['Heading2']))
            for offset_type, details in carbon.offset_recommendations.items():
                self.story.append(Paragraph(f"• {offset_type}: ${details['total_cost']:.2f}", self.styles['Normal']))
```

**Backend Route:**

```python
# backend/app/routers/documents.py

@router.get("/trips/{trip_id}/report/pdf")
async def generate_trip_report(
    trip_id: int,
    current_user = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Generate PDF trip report
    
    Returns: PDF file as attachment
    """
    
    # Verify ownership
    trip = db.query(Trip).filter_by(id=trip_id, user_id=current_user["sub"]).first()
    if not trip:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Generate PDF
    generator = TripReportGenerator(trip, current_user)
    pdf_bytes = generator.generate()
    
    # Save to database (optional)
    document = Document(
        trip_id=trip_id,
        user_id=current_user["sub"],
        file_name=f"trip_report_{trip.name}_{datetime.utcnow().strftime('%Y%m%d')}.pdf",
        file_content=pdf_bytes  # Or store on S3
    )
    db.add(document)
    db.commit()
    
    # Return as file download
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={document.file_name}"}
    )
```

**What you need to explain:**
- ReportLab library (why use it vs alternatives like WeasyPrint)
- Document structure (pages, sections, tables)
- Styling (colors, fonts, alignment, borders)
- Data aggregation from multiple models
- Performance considerations (file size, generation time)
- Memory management (BytesIO vs writing to disk)
- Streaming response (why, how it works)

**Viva Questions (Sample):**
1. Why use ReportLab instead of HTML rendering?
2. How do you structure multi-page PDFs with programmatic data?
3. What's the performance impact of generating large PDFs?
4. How would you add charts/images to the PDF?
5. How do you handle long tables that span multiple pages?
6. What's the difference between storing PDFs on disk vs S3?

---

### 3. Budget Optimizer Explainability (Feature 2 - Explanation Layer)
**What you own:** Generate human-readable explanations for optimization results

**Key Files:**
- `backend/app/services/explainability.py` (lines 1–150)
- `backend/app/routers/trips.py` (calls explainability service)

**Explainability Service:**

```python
# backend/app/services/explainability.py

def explain_optimization(original_allocation, optimized_allocation, preferences):
    """
    Generate human-readable explanation of budget changes
    
    Example:
      Original: Accommodation $2000, Food $1500, Activities $1000, Transport $500
      Optimized: Accommodation $1900, Food $1200, Activities $1300, Transport $600
      Preferences: More activities, less food
      
      Explanation:
      "We adjusted your budget to match your preferences:
       - Reduced Food spending by 20% ($300) because you prioritized dining flexibility
       - Increased Activities by 30% ($300) to maximize experiences
       - Maintained Transport at adequate levels
       
       This gives you more budget for activities while keeping essentials covered."
    """
    
    explanation = []
    
    for category in original_allocation:
        original = original_allocation[category]
        optimized = optimized_allocation[category]
        change = optimized - original
        change_pct = (change / original * 100) if original > 0 else 0
        preference = preferences.get(category, 0)
        
        if abs(change) > 1:  # Only mention changes > $1
            if change > 0:
                reason = generate_increase_reason(category, preference)
                explanation.append(f"• Increased {category.title()} by ${abs(change):.0f} ({change_pct:.1f}%) {reason}")
            else:
                reason = generate_decrease_reason(category, preference)
                explanation.append(f"• Reduced {category.title()} by ${abs(change):.0f} ({abs(change_pct):.1f}%) {reason}")
    
    return "\n".join(explanation)

def generate_increase_reason(category, preference):
    """Generate explanation for why a category was increased"""
    
    if category == "activities" and preference > 0.5:
        return "because you prioritized experiences and activities"
    elif category == "accommodation" and preference > 0.5:
        return "to ensure comfortable lodging"
    elif category == "food" and preference > 0.5:
        return "because dining is a priority for you"
    else:
        return "to maintain adequate coverage"

def generate_decrease_reason(category, preference):
    """Generate explanation for why a category was decreased"""
    
    if category == "activities":
        return "to balance other priorities"
    elif category == "food":
        return "to reduce spending without sacrificing essentials"
    elif category == "transport":
        return "through efficient route planning"
    else:
        return "while maintaining essentials"

def explain_route_optimization(original_route, optimized_route, distances):
    """Generate explanation for TSP optimization"""
    
    original_distance = sum([distances[original_route[i]][original_route[i+1]] 
                           for i in range(len(original_route)-1)])
    optimized_distance = sum([distances[optimized_route[i]][optimized_route[i+1]] 
                            for i in range(len(optimized_route)-1)])
    
    savings = original_distance - optimized_distance
    savings_pct = (savings / original_distance * 100) if original_distance > 0 else 0
    
    return f"Optimized route saves {savings:.0f} km ({savings_pct:.1f}%) compared to original route"

def explain_alert_trigger(category, threshold, current_percent):
    """Generate explanation for budget alert"""
    
    return f"You've reached {current_percent:.1f}% of your {category} budget (alert threshold: {threshold}%)"
```

**What you need to explain:**
- Why explainability matters (user trust, understanding decisions)
- How to translate numerical changes to human language
- Personalization (reference user preferences)
- Edge cases (very small changes, infeasible budgets)

---

### 4. Multi-Stop TSP Integration (Feature 9 - Your Integration)
**What you own:** Integration of TSP solver with expense allocation and UI

**Key Files:**
- `backend/app/services/multistop_calculator.py` (lines 600–800)

Your role here overlaps with Member 1 (who owns the TSP algorithm), but you're responsible for:
- Integrating the TSP output with packing, weather, carbon data
- Generating optimized itinerary documents
- Cost allocation across stops

**What you need to explain:**
- How TSP results feed into itinerary creation
- Cost allocation logic (budget splitting across stops based on duration)
- Integration with other services

---

### 5. LLM Services Integration (Gemini/OpenAI)
**What you own:** Wrapper layer for calling Gemini and OpenAI APIs

**Key Files:**
- `backend/app/services/gemini.py`
- `backend/app/services/openai.py`

**Implementation Example:**

```python
# backend/app/services/gemini.py

import google.generativeai as genai

class GeminiClient:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def generate_text(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate text using Gemini API"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def stream_response(self, prompt: str) -> Iterator[str]:
        """Stream response from Gemini"""
        
        try:
            response = self.model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Error: {str(e)}"
```

**What you need to explain:**
- Why use different LLM providers (price, speed, quality tradeoffs)
- API key management
- Error handling and retries
- Temperature setting for different use cases

---

### 6. Validators (Itinerary & Personalized Plan)
**What you own:** Validation services for complex trip data

**Key Files:**
- `backend/app/services/itinerary_validator.py`
- `backend/app/services/personalized_plan_validator.py`

**Validation Examples:**

```python
# backend/app/services/itinerary_validator.py

def validate_itinerary(itinerary, trip):
    """Validate day-by-day itinerary"""
    
    errors = []
    
    # Check dates don't overlap
    for i, day in enumerate(itinerary):
        if day.day < 1 or day.day > (trip.end_date - trip.start_date).days:
            errors.append(f"Day {day.day} is outside trip duration")
    
    # Check locations are reachable
    for day in itinerary:
        if day.location not in valid_locations:
            errors.append(f"Location '{day.location}' not found")
    
    return errors if errors else None
```

---

## Viva Preparation Checklist

**Before your viva, be able to explain:**

1. ✓ Groq API integration (why Groq, model selection)
2. ✓ Chat conversation management (history, context, streaming)
3. ✓ System prompt engineering (how to guide AI behavior)
4. ✓ PDF report generation (structure, styling, multi-page)
5. ✓ ReportLab library (why choose it, how it works)
6. ✓ Data aggregation for reports (fetching from multiple models)
7. ✓ Explainability layer (translating optimization to human language)
8. ✓ LLM service wrappers (Gemini/OpenAI integration)
9. ✓ Validation services (error handling, business logic)
10. ✓ Error handling throughout (API failures, parsing errors)

---

## Common Viva Traps & How to Avoid

| Trap | How to Avoid |
|------|-------------|
| "Why is chat returning 501?" | Know the root cause: missing GROQ_API_KEY; explain fix |
| "How do you prevent hallucinations?" | Mention: system prompt engineering, temperature tuning, output validation |
| "How accurate is PDF generation?" | Honest: data aggregation is accurate, styling may vary by viewer |
| "Can you stream the PDF?" | Explain tradeoff: streaming for responsiveness, but PDF format needs complete data |
| "How do you secure API keys?" | Environment variables, never hardcode, use secrets manager in production |
| "What if Groq API is rate-limited?" | Implement: queuing, exponential backoff, fallback to cached response |

---

## Suggested Talking Points

**When asked "Tell us about your features":**

"I was responsible for AI services and advanced features. The core feature is the **AI Trip Chat Assistant** using Groq API—it maintains conversation context and provides trip planning advice specific to the user's trip details. Currently returning 501s due to missing API key configuration, but the integration is complete.

I also built the **PDF Report Generator**, which combines all trip data (itinerary, expenses, packing list, carbon footprint) into a comprehensive, well-formatted PDF document using ReportLab.

Beyond these, I implemented the **Explainability Layer** that translates optimization algorithm results into human-readable explanations, LLM service wrappers for Gemini/OpenAI integration, and validators for complex trip data.

The complexity came from integrating multiple external APIs (Groq, OpenAI, Gemini), managing long-context conversations, and generating sophisticated documents programmatically. All features prioritize error handling and graceful degradation when external services are unavailable."

---

**End of Member 3 Guide**
