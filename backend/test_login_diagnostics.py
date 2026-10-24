#!/usr/bin/env python3
"""
Login diagnostics - Test the entire authentication flow
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app import models, auth, schemas
from datetime import datetime, timedelta
from app.config import settings

def test_user_exists():
    """Check if test user exists"""
    print("\n" + "=" * 70)
    print("1. CHECKING EXISTING USERS")
    print("=" * 70)
    
    db = SessionLocal()
    users = db.query(models.User).all()
    print(f"\n✓ Total users in database: {len(users)}")
    
    for user in users:
        print(f"  - ID: {user.id}")
        print(f"    Name: {user.name}")
        print(f"    Email: {user.email}")
        print(f"    Created: {user.created_at}")
    
    db.close()
    return len(users) > 0

def test_password_verification():
    """Test password hashing and verification"""
    print("\n" + "=" * 70)
    print("2. TESTING PASSWORD HASHING & VERIFICATION")
    print("=" * 70)
    
    test_password = "test_password_123"
    
    # Hash a password
    hashed = auth.get_password_hash(test_password)
    print(f"\n✓ Hashed password: {hashed[:50]}...")
    
    # Verify it
    is_valid = auth.verify_password(test_password, hashed)
    print(f"✓ Password verification: {'PASS' if is_valid else 'FAIL'}")
    
    # Test wrong password
    is_wrong = auth.verify_password("wrong_password", hashed)
    print(f"✓ Wrong password rejected: {'PASS' if not is_wrong else 'FAIL'}")
    
    return is_valid and not is_wrong

def test_jwt_creation():
    """Test JWT token creation and decoding"""
    print("\n" + "=" * 70)
    print("3. TESTING JWT TOKEN CREATION & DECODING")
    print("=" * 70)
    
    from jose import jwt, JWTError
    
    test_email = "test@example.com"
    
    # Create token
    token = auth.create_access_token(data={"sub": test_email})
    print(f"\n✓ Created JWT token: {token[:50]}...")
    
    # Decode token
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        decoded_email = payload.get("sub")
        print(f"✓ Decoded email: {decoded_email}")
        print(f"✓ Token contains exp claim: {'exp' in payload}")
        print(f"✓ Token email matches: {'PASS' if decoded_email == test_email else 'FAIL'}")
        return decoded_email == test_email
    except JWTError as e:
        print(f"✗ JWT decode failed: {e}")
        return False

def test_database_user_query():
    """Test querying user from database"""
    print("\n" + "=" * 70)
    print("4. TESTING USER QUERY FROM DATABASE")
    print("=" * 70)
    
    db = SessionLocal()
    
    # Find first user
    user = db.query(models.User).first()
    
    if not user:
        print("\n✗ No users found in database")
        db.close()
        return False
    
    print(f"\n✓ Found user: {user.name} ({user.email})")
    print(f"✓ User ID: {user.id}")
    print(f"✓ Hashed password exists: {bool(user.hashed_password)}")
    print(f"✓ Password hash length: {len(user.hashed_password)}")
    
    db.close()
    return True

def test_login_flow():
    """Test the complete login flow"""
    print("\n" + "=" * 70)
    print("5. TESTING COMPLETE LOGIN FLOW")
    print("=" * 70)
    
    db = SessionLocal()
    
    # Create a test user with known password
    test_email = "login_test@example.com"
    test_password = "TestPassword123!"
    
    # Check if user exists
    existing = db.query(models.User).filter(models.User.email == test_email).first()
    if existing:
        db.delete(existing)
        db.commit()
        print(f"\n✓ Cleaned up old test user")
    
    # Create new test user
    hashed_pw = auth.get_password_hash(test_password)
    new_user = models.User(
        name="Login Test User",
        email=test_email,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    print(f"\n✓ Created test user: {new_user.email}")
    print(f"✓ User ID: {new_user.id}")
    
    # Simulate login
    print(f"\n→ Attempting login with email: {test_email}")
    
    # Query user
    queried_user = db.query(models.User).filter(models.User.email == test_email).first()
    
    if not queried_user:
        print(f"✗ User not found during login query")
        db.close()
        return False
    
    print(f"✓ User found: {queried_user.name}")
    
    # Verify password
    is_valid = auth.verify_password(test_password, queried_user.hashed_password)
    print(f"✓ Password verification: {'PASS' if is_valid else 'FAIL'}")
    
    if is_valid:
        # Create token
        token = auth.create_access_token(data={"sub": queried_user.email})
        print(f"✓ JWT token created: {token[:50]}...")
        
        # Decode and verify token
        from jose import jwt
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        print(f"✓ Token validated: email={payload.get('sub')}")
        
        print(f"\n✓ LOGIN FLOW SUCCESSFUL")
        db.close()
        return True
    else:
        print(f"✗ Password verification failed")
        db.close()
        return False

def test_endpoint_schema():
    """Test that response schemas are correct"""
    print("\n" + "=" * 70)
    print("6. TESTING RESPONSE SCHEMAS")
    print("=" * 70)
    
    db = SessionLocal()
    user = db.query(models.User).first()
    
    if not user:
        print("\n✗ No users to test")
        db.close()
        return False
    
    print(f"\n✓ Found user: {user.email}")
    
    # Try to create UserOut schema
    try:
        user_out = schemas.UserOut.model_validate(user, from_attributes=True)
        print(f"✓ UserOut schema validates: {user_out.email}")
    except Exception as e:
        print(f"✗ UserOut schema error: {e}")
        db.close()
        return False
    
    # Try to create Token schema
    token = auth.create_access_token(data={"sub": user.email})
    try:
        token_response = schemas.Token(
            access_token=token,
            token_type="bearer",
            user=user_out
        )
        print(f"✓ Token schema validates")
        print(f"  - Token length: {len(token_response.access_token)}")
        print(f"  - Token type: {token_response.token_type}")
        print(f"  - User: {token_response.user.email}")
    except Exception as e:
        print(f"✗ Token schema error: {e}")
        db.close()
        return False
    
    db.close()
    return True

def main():
    print("=" * 70)
    print("LOGIN DIAGNOSTICS - BudgetBound Authentication Test Suite")
    print("=" * 70)
    
    try:
        results = {
            "Users exist": test_user_exists(),
            "Password hashing": test_password_verification(),
            "JWT tokens": test_jwt_creation(),
            "Database queries": test_database_user_query(),
            "Login flow": test_login_flow(),
            "Response schemas": test_endpoint_schema(),
        }
        
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        for test_name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {test_name}")
        
        all_passed = all(results.values())
        
        print("\n" + "=" * 70)
        if all_passed:
            print("✓ ALL TESTS PASSED - Authentication system is working correctly")
            print("=" * 70)
            print("\nIf you're unable to login from the frontend:")
            print("1. Check browser console for network errors")
            print("2. Verify you're using correct credentials")
            print("3. Check that backend is running on correct port")
            print("4. Verify CORS is configured correctly")
            print("5. Check localStorage for token storage issues")
            return 0
        else:
            print("✗ SOME TESTS FAILED - See details above")
            print("=" * 70)
            return 1
            
    except Exception as e:
        print(f"\n✗ Diagnostic test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
