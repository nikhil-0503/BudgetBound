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
        # Get regenerated data from LLM
        regenerated = await gemini_service.regenerate_trip(trip, instruction)
        
        # ===== UPDATE TRIP IN DATABASE =====
        
        # Update budget allocation
        if "costs" in regenerated:
            costs = regenerated["costs"]
            
            # Get or create budget allocation
            if not trip.budget_allocation:
                trip.budget_allocation = models.BudgetAllocation(trip_id=trip.id)
            
            # Update all cost fields
            trip.budget_allocation.transport_cost = costs.get("transport_cost", 0.0)
            trip.budget_allocation.hotel_cost = costs.get("hotel_cost", 0.0)
            trip.budget_allocation.food_cost = costs.get("food_cost", 0.0)
            trip.budget_allocation.activities_cost = costs.get("activities_cost", 0.0)
            trip.budget_allocation.local_transport_cost = costs.get("local_transport_cost", 0.0)
            trip.budget_allocation.taxes_fees_cost = costs.get("taxes_fees_cost", 0.0)
            trip.budget_allocation.emergency_reserve = costs.get("emergency_reserve", 0.0)
            
            # Update trip-level fields
            trip.total_estimated_cost = costs.get("total_estimated_cost", trip.total_estimated_cost)
            trip.transport_mode = costs.get("transport_mode", trip.transport_mode)
            trip.hotel_tier = costs.get("hotel_tier", trip.hotel_tier)
        
        # Update itineraries
        if "itineraries" in regenerated:
            # Delete old itineraries
            db.query(models.Itinerary).filter(models.Itinerary.trip_id == trip.id).delete()
            
            # Create new itineraries
            for itinerary_data in regenerated["itineraries"]:
                new_itinerary = models.Itinerary(
                    trip_id=trip.id,
                    day_number=itinerary_data.get("day_number"),
                    description=itinerary_data.get("description"),
                    activities=itinerary_data.get("activities", [])
                )
                db.add(new_itinerary)
        
        # Save all changes to database
        db.commit()
        
        # Return regenerated data (same structure frontend expects)
        return regenerated
        
    except Exception as e:
        db.rollback()
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


@router.get("/diagnostics")
def ai_diagnostics(current_user: models.User = Depends(auth.get_current_user)):
    """Get AI service diagnostics including model discovery status."""
    from app.services.groq_model_discovery import get_model_discovery
    
    discovery = get_model_discovery()
    model_id, discovery_error = discovery.get_selected_model()
    
    # Get service stats
    stats = gemini_service._request_stats if hasattr(gemini_service, '_request_stats') else {}
    
    return {
        "groq_api_key_configured": bool(gemini_service.api_key),
        "selected_model": model_id,
        "service_available": gemini_service.is_available,
        "fallback_reason": gemini_service._fallback_reason,
        "model_discovery_error": discovery_error,
        "request_stats": stats
    }


@router.post("/personalized-plan")
async def ai_personalized_plan(
    payload: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Generate a personalized travel itinerary based on user preferences.
    
    Request format:
    {
      "preferences": {
        "keywords": "Kolkata",
        "budget": 25000,
        "days": 2,
        "special": "Bengali food, river cruise"
      }
    }
    
    Returns PersonalizedPlanResponse with itinerary, budget breakdown, and requirement coverage.
    """
    from app.services.requirement_extractor import extract_requirements
    from app.schemas import PersonalizedPlanRequest
    
    try:
        # Extract and validate preferences
        preferences = payload.get("preferences", {})
        
        # Validate using Pydantic
        try:
            request = PersonalizedPlanRequest(
                keywords=preferences.get("keywords", ""),
                budget=float(preferences.get("budget", 25000)),
                days=int(preferences.get("days", 5)),
                special=preferences.get("special", "")
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request parameters: {str(e)}"
            )
        
        # Extract and validate requirements
        requirements = extract_requirements(request.special or "")
        
        # Log request
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Personalized plan request: destination={request.keywords}, "
            f"budget={request.budget}, days={request.days}, "
            f"requirements_extracted={len(requirements)}"
        )
        
        # Generate plan
        result = await gemini_service.generate_personalized_plan(
            keywords=request.keywords,
            budget=request.budget,
            days=request.days,
            special=request.special or ""
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Error generating personalized plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate personalized plan: {str(e)}"
        )


@router.post("/multistop-plan")
async def ai_multistop_plan(
    payload: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user),
):
    """Generate an AI-powered multi-stop trip itinerary."""
    import logging
    logger = logging.getLogger(__name__)
    
    stops = payload.get("stops", [])
    budget = float(payload.get("budget", 50000))
    special = payload.get("special", "")

    logger.info(f"Multi-stop request - stops={len(stops)}, budget={budget}, user={current_user.id}")

    if not stops or len(stops) < 2:
        raise HTTPException(status_code=400, detail="At least 2 stops are required.")
    if len(stops) > 6:
        raise HTTPException(status_code=400, detail="Maximum 6 stops are allowed.")
    for s in stops:
        if not s.get("destination", "").strip():
            raise HTTPException(status_code=400, detail="Each stop must have a destination name.")
        if int(s.get("days", 0)) < 1:
            raise HTTPException(status_code=400, detail="Each stop must have at least 1 day.")

    try:
        logger.info("Calling generate_multistop_plan...")
        result = await gemini_service.generate_multistop_plan(stops, budget, special)
        logger.info(f"Generated result keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
        return result
    except Exception as e:
        logger.exception(f"Error in generate_multistop_plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
