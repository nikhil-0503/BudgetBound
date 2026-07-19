from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app import auth, models
from app.database import get_db
from app.services.gemini import gemini_service

router = APIRouter(prefix="/api/ai", tags=["AI Copilot"])


@router.post("/chat")
async def ai_chat(
    payload: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user),
):
    messages = payload.get("messages", [])
    try:
        return await gemini_service.chat_assistant(messages)
    except NotImplementedError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.post("/regenerate")
async def ai_regenerate(
    payload: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip_id = payload.get("trip_id")
    instruction = payload.get("instruction", "")
    
    if not trip_id:
        raise HTTPException(status_code=400, detail="trip_id is required")
        
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    try:
        return await gemini_service.regenerate_trip(trip, instruction)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain")
async def ai_explain(
    payload: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip_id = payload.get("trip_id")
    if not trip_id:
        raise HTTPException(status_code=400, detail="trip_id is required")
        
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    try:
        return await gemini_service.explain_itinerary(trip)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personalized-plan")
async def ai_personalized_plan(
    payload: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user),
):
    preferences = payload.get("preferences", {})
    keywords = preferences.get("keywords", "")
    budget = float(preferences.get("budget", 25000))
    days = int(preferences.get("days", 5))
    special = preferences.get("special", "")
    
    try:
        return await gemini_service.generate_personalized_plan(keywords, budget, days, special)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
