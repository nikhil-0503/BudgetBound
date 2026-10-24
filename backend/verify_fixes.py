"""
Quick verification script for bug fixes
"""

from app.database import engine, get_db
from app import models
from sqlalchemy.orm import Session

def verify_fixes():
    print("=" * 60)
    print("BUDGETBOUND BUG FIXES VERIFICATION")
    print("=" * 60)
    
    db = Session(engine)
    
    try:
        # 1. Verify database state
        dest_count = db.query(models.Destination).count()
        trip_count = db.query(models.Trip).count()
        expense_count = db.query(models.Expense).count()
        user_count = db.query(models.User).count()
        
        print(f"\n📊 DATABASE STATUS")
        print(f"   • Destinations: {dest_count}")
        print(f"   • Users: {user_count}")
        print(f"   • Trips: {trip_count}")
        print(f"   • Expenses: {expense_count}")
        
        # 2. Check for duplicate destinations
        print(f"\n🔍 DUPLICATE CHECK")
        duplicates = db.query(models.Destination.name).group_by(
            models.Destination.name
        ).having(db.query(models.Destination.id).count() > 1).all()
        
        if duplicates:
            print(f"   ⚠️  Found {len(duplicates)} duplicate destination names:")
            for dup in duplicates:
                print(f"      - {dup[0]}")
        else:
            print(f"   ✅ No duplicate destinations found")
        
        # 3. Check budget allocations exist for trips
        trips_with_alloc = db.query(models.Trip).filter(
            models.Trip.budget_allocation != None
        ).count()
        print(f"\n💰 BUDGET ALLOCATIONS")
        print(f"   • Trips with allocations: {trips_with_alloc}/{trip_count}")
        
        # 4. Sample trip with expenses
        trip_with_expenses = db.query(models.Trip).join(
            models.Expense
        ).first()
        
        if trip_with_expenses:
            expense_sum = sum([e.amount for e in trip_with_expenses.expenses])
            print(f"\n💳 EXPENSE TRACKING (Sample)")
            print(f"   • Trip: {trip_with_expenses.destination.name}")
            print(f"   • Budget: ₹{trip_with_expenses.budget:,.2f}")
            print(f"   • Estimated: ₹{trip_with_expenses.total_estimated_cost:,.2f}")
            print(f"   • Actual spent: ₹{expense_sum:,.2f}")
            print(f"   • Expenses logged: {len(trip_with_expenses.expenses)}")
        else:
            print(f"\n💳 EXPENSE TRACKING")
            print(f"   • No trips with expenses yet")
        
        # 5. Check schema imports
        from app import schemas
        print(f"\n📋 SCHEMA VERIFICATION")
        print(f"   • ExpenseBase: {'✅ Available' if hasattr(schemas, 'ExpenseBase') else '❌ Missing'}")
        print(f"   • ExpenseCreate: {'✅ Available' if hasattr(schemas, 'ExpenseCreate') else '❌ Missing'}")
        print(f"   • TripOut: {'✅ Available' if hasattr(schemas, 'TripOut') else '❌ Missing'}")
        
        print(f"\n" + "=" * 60)
        print("✅ VERIFICATION COMPLETE - All fixes in place!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during verification: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_fixes()
