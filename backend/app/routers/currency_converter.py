"""
Currency Converter for International Trips
Uses live exchange rates from exchangerate-api.com
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from app import models, auth
from app.database import get_db

router = APIRouter(prefix="/api/currency", tags=["Currency Converter"])

# Cache for exchange rates (to avoid hitting API limits)
_rate_cache = {
    "rates": {},
    "last_updated": None,
    "base": "INR"
}

# Fallback static rates if API fails
FALLBACK_RATES = {
    "INR": 1.0,
    "USD": 0.012,
    "EUR": 0.011,
    "GBP": 0.0095,
    "AED": 0.044,
    "THB": 0.41,
    "SGD": 0.016,
    "MYR": 0.054,
    "IDR": 190,
    "VND": 305,
    "NPR": 1.60,
    "LKR": 3.48,
    "TRY": 0.41,
    "QAR": 0.044,
    "OMR": 0.0046,
    "JPY": 1.85,
    "AUD": 0.019,
    "CAD": 0.017
}

async def fetch_exchange_rates(base: str = "INR") -> Dict[str, float]:
    """
    Fetch live exchange rates from exchangerate-api.com
    Cache results for 1 hour to avoid API limits
    """
    
    # Check cache (refresh every hour)
    if (_rate_cache["rates"] and 
        _rate_cache["last_updated"] and 
        _rate_cache["base"] == base and
        datetime.now() - _rate_cache["last_updated"] < timedelta(hours=1)):
        return _rate_cache["rates"]
    
    try:
        # Free tier API endpoint (no API key required)
        url = f"https://api.exchangerate-api.com/v4/latest/{base}"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            rates = data.get("rates", {})
            
            # Update cache
            _rate_cache["rates"] = rates
            _rate_cache["last_updated"] = datetime.now()
            _rate_cache["base"] = base
            
            return rates
    
    except Exception as e:
        print(f"Error fetching exchange rates: {e}")
        # Return fallback rates if API fails
        return FALLBACK_RATES

# Country to currency mapping
COUNTRY_CURRENCY = {
    "India": "INR",
    "UAE": "AED",
    "Thailand": "THB",
    "Singapore": "SGD",
    "Malaysia": "MYR",
    "Indonesia": "IDR",
    "Vietnam": "VND",
    "Nepal": "NPR",
    "Sri Lanka": "LKR",
    "Turkey": "TRY",
    "Qatar": "QAR",
    "Oman": "OMR",
    "France": "EUR",
    "UK": "GBP",
    "Italy": "EUR",
    "Spain": "EUR",
    "Netherlands": "EUR",
    "Austria": "EUR",
    "Portugal": "EUR",
    "Greece": "EUR",
    "Czech Republic": "EUR",
    "Cambodia": "USD",
    "Laos": "USD",
    "Jordan": "USD",
    "Israel": "USD",
    "Lebanon": "USD",
    "Azerbaijan": "USD",
    "Iceland": "EUR",
    "Japan": "JPY",
    "Australia": "AUD",
    "Canada": "CAD"
}


@router.get("/convert", response_model=Dict[str, Any])
async def convert_currency(
    amount: float = Query(..., description="Amount to convert"),
    from_currency: str = Query("INR", description="Source currency code"),
    to_currency: str = Query(..., description="Target currency code")
):
    """
    Convert amount from one currency to another using live exchange rates
    """
    
    # Fetch live rates
    rates = await fetch_exchange_rates(from_currency)
    
    if to_currency not in rates:
        raise HTTPException(status_code=400, detail=f"Currency {to_currency} not supported")
    
    # Convert amount
    converted_amount = amount * rates[to_currency]
    
    return {
        "original_amount": amount,
        "original_currency": from_currency,
        "converted_amount": round(converted_amount, 2),
        "converted_currency": to_currency,
        "exchange_rate": round(rates[to_currency], 6),
        "last_updated": _rate_cache["last_updated"].isoformat() if _rate_cache["last_updated"] else None
    }


@router.get("/trip/{trip_id}", response_model=Dict[str, Any])
async def get_trip_currency_info(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get currency information for a specific trip using live exchange rates
    """
    
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    destination_state = trip.destination.state
    
    # Determine if international trip
    is_international = destination_state not in [
        "Goa", "Kerala", "Karnataka", "Tamil Nadu", "Maharashtra", "Rajasthan",
        "Uttarakhand", "Himachal Pradesh", "Jammu & Kashmir", "Andaman & Nicobar",
        "Delhi", "Gujarat", "Madhya Pradesh", "Odisha", "West Bengal", "Sikkim",
        "Arunachal Pradesh", "Meghalaya", "Assam", "Punjab", "Haryana", "Bihar",
        "Uttar Pradesh", "Telangana", "Andhra Pradesh", "Lakshadweep", "Daman & Diu"
    ]
    
    if not is_international:
        return {
            "trip_id": trip_id,
            "destination": trip.destination.name,
            "is_international": False,
            "currency": "INR",
            "budget_inr": trip.budget,
            "estimated_cost_inr": trip.total_estimated_cost,
            "message": "Domestic trip - No currency conversion needed"
        }
    
    # Get currency for destination
    local_currency = COUNTRY_CURRENCY.get(destination_state, "USD")
    
    # Fetch live rates
    rates = await fetch_exchange_rates("INR")
    exchange_rate = rates.get(local_currency, FALLBACK_RATES.get(local_currency, 1.0))
    
    # Convert budget and costs
    budget_local = trip.budget * exchange_rate
    cost_local = trip.total_estimated_cost * exchange_rate
    
    # Daily budget
    daily_budget_inr = trip.budget / trip.days
    daily_budget_local = daily_budget_inr * exchange_rate
    
    return {
        "trip_id": trip_id,
        "destination": trip.destination.name,
        "country": destination_state,
        "is_international": True,
        "local_currency": local_currency,
        "exchange_rate": round(exchange_rate, 6),
        "budget_inr": trip.budget,
        "budget_local": round(budget_local, 2),
        "estimated_cost_inr": trip.total_estimated_cost,
        "estimated_cost_local": round(cost_local, 2),
        "daily_budget_inr": round(daily_budget_inr, 2),
        "daily_budget_local": round(daily_budget_local, 2),
        "currency_tips": generate_currency_tips(local_currency, destination_state),
        "last_updated": _rate_cache["last_updated"].isoformat() if _rate_cache["last_updated"] else None
    }


def generate_currency_tips(currency: str, country: str) -> list:
    """Generate helpful currency tips for travelers"""
    tips = []
    
    if currency == "AED":
        tips = [
            "Most places accept cards, but keep some cash for taxis and small shops",
            "Exchange currency at airports or licensed exchange houses",
            "ATMs widely available with good exchange rates"
        ]
    elif currency == "THB":
        tips = [
            "Exchange money at Super Rich or local exchange booths for best rates",
            "Many places accept cash only, especially street food",
            "Notify your bank before traveling to avoid card blocks"
        ]
    elif currency == "EUR":
        tips = [
            "Cards widely accepted throughout Europe",
            "Exchange at local banks for better rates than airports",
            "Watch out for dynamic currency conversion fees"
        ]
    elif currency == "SGD":
        tips = [
            "Singapore is very card-friendly, minimal cash needed",
            "Use local banks or ATMs for best exchange rates",
            "Hawker centers may prefer cash"
        ]
    else:
        tips = [
            "Research local payment customs before traveling",
            "Use ATMs for better exchange rates than currency exchange counters",
            "Always inform your bank about international travel"
        ]
    
    return tips


@router.get("/rates", response_model=Dict[str, Any])
async def get_exchange_rates_endpoint(
    base: str = Query("INR", description="Base currency")
):
    """
    Get all live exchange rates for a base currency
    """
    
    rates = await fetch_exchange_rates(base)
    
    return {
        "base_currency": base,
        "rates": rates,
        "last_updated": _rate_cache["last_updated"].isoformat() if _rate_cache["last_updated"] else None,
        "supported_currencies": list(rates.keys()),
        "source": "exchangerate-api.com"
    }


@router.post("/estimate-forex", response_model=Dict[str, Any])
async def estimate_forex_needed(
    trip_id: int,
    days_abroad: int,
    card_usage_percentage: int = Query(70, ge=0, le=100),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Estimate how much foreign currency to carry for a trip using live rates
    """
    
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    destination_state = trip.destination.state
    local_currency = COUNTRY_CURRENCY.get(destination_state, "USD")
    
    # Fetch live rates
    rates = await fetch_exchange_rates("INR")
    exchange_rate = rates.get(local_currency, FALLBACK_RATES.get(local_currency, 1.0))
    
    # Calculate cash needs
    daily_budget = trip.budget / trip.days
    cash_percentage = 100 - card_usage_percentage
    
    cash_needed_inr = (daily_budget * days_abroad * cash_percentage) / 100
    cash_needed_local = cash_needed_inr * exchange_rate
    
    return {
        "trip_id": trip_id,
        "destination": trip.destination.name,
        "local_currency": local_currency,
        "exchange_rate": round(exchange_rate, 6),
        "days_abroad": days_abroad,
        "card_usage": f"{card_usage_percentage}%",
        "cash_usage": f"{cash_percentage}%",
        "recommended_cash_inr": round(cash_needed_inr, 2),
        "recommended_cash_local": round(cash_needed_local, 2),
        "daily_cash_local": round(cash_needed_local / days_abroad, 2),
        "recommendations": [
            f"Carry approximately {local_currency} {round(cash_needed_local, 2)} in local currency",
            f"Keep {card_usage_percentage}% expenses for card payments",
            "Always carry small denominations for tips and street purchases",
            "Have backup payment method (extra card) for emergencies"
        ],
        "last_updated": _rate_cache["last_updated"].isoformat() if _rate_cache["last_updated"] else None
    }
