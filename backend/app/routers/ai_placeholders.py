from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from app import auth, models
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
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Trip regeneration via natural language is coming soon.",
    )


@router.post("/explain")
async def ai_explain(
    payload: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Budget explanation AI is coming soon.",
    )


@router.post("/personalized-plan")
async def ai_personalized_plan(
    payload: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Personalized AI planner is coming soon.",
    )
