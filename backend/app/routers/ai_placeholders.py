from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from app import auth, models
from app.services.openai import ai_travel_service

router = APIRouter(prefix="/api/ai", tags=["AI Copilot Placeholders"])

@router.post("/regenerate")
async def ai_regenerate(
    payload: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        trip_id = payload.get("trip_id")
        instruction = payload.get("instruction")
        result = await ai_travel_service.regenerate_trip(trip_id, instruction)
        return result
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

@router.post("/explain")
async def ai_explain(
    payload: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        trip_id = payload.get("trip_id")
        result = await ai_travel_service.explain_budget_choices(trip_id)
        return result
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

@router.post("/chat")
async def ai_chat(
    payload: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        messages = payload.get("messages", [])
        result = await ai_travel_service.chat_assistant(messages)
        return result
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

@router.post("/personalized-plan")
async def ai_personalized_plan(
    payload: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        preferences = payload.get("preferences", {})
        result = await ai_travel_service.generate_personalized_plan(preferences)
        return result
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
