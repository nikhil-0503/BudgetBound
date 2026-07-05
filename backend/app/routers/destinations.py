from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/destinations", tags=["Destinations"])

@router.get("/", response_model=schemas.DestinationListOut)
def get_destinations(
    category: Optional[str] = None,
    state: Optional[str] = None,
    min_rating: Optional[float] = None,
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 9,
    db: Session = Depends(get_db)
):
    query = db.query(models.Destination)
    
    if category:
        query = query.filter(models.Destination.category == category)
    if state:
        query = query.filter(models.Destination.state.ilike(f"%{state}%"))
    if min_rating:
        query = query.filter(models.Destination.rating >= min_rating)
        
    daily_cost = models.Destination.avg_hotel_cost + models.Destination.avg_food_cost
    if min_budget is not None:
        query = query.filter(daily_cost >= min_budget)
    if max_budget is not None:
        query = query.filter(daily_cost <= max_budget)
        
    if search:
        query = query.filter(
            models.Destination.name.ilike(f"%{search}%") | 
            models.Destination.description.ilike(f"%{search}%") |
            models.Destination.state.ilike(f"%{search}%")
        )
        
    total = query.count()
    destinations = query.offset((page - 1) * limit).limit(limit).all()
    
    return {
        "total": total,
        "destinations": destinations
    }

@router.get("/states", response_model=List[str])
def get_unique_states(db: Session = Depends(get_db)):
    states = db.query(models.Destination.state).distinct().all()
    return sorted([s[0] for s in states if s[0]])

@router.get("/categories", response_model=List[str])
def get_unique_categories(db: Session = Depends(get_db)):
    categories = db.query(models.Destination.category).distinct().all()
    return sorted([c[0] for c in categories if c[0]])

@router.get("/{destination_id}", response_model=schemas.DestinationOut)
def get_destination(destination_id: int, db: Session = Depends(get_db)):
    destination = db.query(models.Destination).filter(models.Destination.id == destination_id).first()
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    return destination
