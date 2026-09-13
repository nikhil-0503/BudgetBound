from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app import models, schemas, auth
from app.database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str
    confirm_password: str

@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )
    
    # Hash password and create user
    hashed_password = auth.get_password_hash(user_in.password)
    db_user = models.User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Generate JWT
    access_token = auth.create_access_token(data={"sub": db_user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }

@router.post("/login", response_model=schemas.Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Authenticate user. OAuth2PasswordRequestForm uses 'username' for email.
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT
    access_token = auth.create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

# Also support JSON payload login (convenient for API requests from React without Form data)
@router.post("/login-json", response_model=schemas.Token)
def login_user_json(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not auth.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT
    access_token = auth.create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.get("/profile")
def get_user_profile_details(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trips = db.query(models.Trip).filter(models.Trip.user_id == current_user.id).all()
    
    trips_completed = sum([1 for t in trips if t.status == "Completed"])
    total_budget_planned = sum([t.budget for t in trips])
    
    total_savings = 0.0
    for t in trips:
        actual_spent = sum([e.amount for e in t.expenses])
        total_savings += max(0.0, t.budget - actual_spent)
        
    from collections import Counter
    styles = [t.travel_type for t in trips if t.travel_type]
    fav_style = Counter(styles).most_common(1)[0][0] if styles else "—"

    return {
        "user": current_user,
        "stats": {
            "trips_completed": trips_completed,
            "total_budget_planned": round(total_budget_planned, 2),
            "total_savings": round(total_savings, 2),
            "favorite_trip_type": fav_style
        }
    }

@router.put("/profile", response_model=schemas.UserOut)
def update_user_profile_details(
    payload: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if payload.name is not None:
        current_user.name = payload.name
    if payload.photo_url is not None:
        current_user.photo_url = payload.photo_url
    if payload.default_budget is not None:
        current_user.default_budget = payload.default_budget
    if payload.preferred_travel_style is not None:
        current_user.preferred_travel_style = payload.preferred_travel_style
    if payload.preferred_comfort_level is not None:
        current_user.preferred_comfort_level = payload.preferred_comfort_level
    if payload.default_starting_city is not None:
        current_user.default_starting_city = payload.default_starting_city
    if payload.preferred_theme is not None:
        current_user.preferred_theme = payload.preferred_theme

    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Verify user exists by email (first step of password reset)"""
    user = db.query(models.User).filter(models.User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address."
        )
    
    return {
        "message": f"Account found. You can now reset your password.",
        "email": user.email
    }

@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password directly by email (no token needed)"""
    
    # Find user
    user = db.query(models.User).filter(models.User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address."
        )
    
    # Validate passwords match
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )
    
    # Validate password length
    if not request.new_password or len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )
    
    # Update password
    hashed_password = auth.get_password_hash(request.new_password)
    user.hashed_password = hashed_password
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Password reset successfully. You can now log in with your new password.",
        "email": user.email
    }
