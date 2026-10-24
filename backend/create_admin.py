#!/usr/bin/env python3
"""
Script to create or promote an admin user in BudgetBound
Run this from the backend directory: python create_admin.py
"""
import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, engine
from app.models import User
from app.auth import get_password_hash

def create_admin():
    """Create or promote an admin user"""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    print("\n" + "="*60)
    print("BudgetBound Admin Account Setup")
    print("="*60 + "\n")
    
    # Get user input
    email = input("Enter admin email (or leave blank for admin@budgetbound.com): ").strip()
    if not email:
        email = "admin@budgetbound.com"
    
    name = input("Enter admin name (or leave blank for 'Admin User'): ").strip()
    if not name:
        name = "Admin User"
    
    password = input("Enter admin password (minimum 8 characters): ").strip()
    if len(password) < 8:
        print("❌ Password too short! Must be at least 8 characters.")
        return False
    
    confirm_password = input("Confirm password: ").strip()
    if password != confirm_password:
        print("❌ Passwords do not match!")
        return False
    
    # Create database session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            print(f"\n✓ User '{email}' already exists.")
            print(f"  Current admin status: {'🔐 ADMIN' if existing_user.is_admin else '👤 Regular User'}")
            
            promote = input("\nPromote this user to admin? (yes/no): ").strip().lower()
            if promote == 'yes':
                existing_user.is_admin = True
                db.commit()
                print(f"✅ User '{email}' is now an ADMIN!")
                return True
            else:
                print("Cancelled.")
                return False
        
        # Create new admin user
        hashed_pwd = get_password_hash(password)
        new_admin = User(
            name=name,
            email=email,
            hashed_password=hashed_pwd,
            is_admin=True,
            preferred_theme="light"
        )
        
        db.add(new_admin)
        db.commit()
        
        print(f"\n✅ Admin account created successfully!")
        print(f"   Email: {email}")
        print(f"   Name: {name}")
        print(f"   Status: 🔐 ADMIN")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = create_admin()
    if success:
        print("\n" + "="*60)
        print("Next steps:")
        print("1. Start your backend server: python -m uvicorn app.main:app --reload")
        print("2. Start your frontend: npm run dev")
        print("3. Go to: http://localhost:3000/login")
        print("4. Login with the credentials above")
        print("5. Navigate to: http://localhost:3000/admin")
        print("="*60 + "\n")
    sys.exit(0 if success else 1)
