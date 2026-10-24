"""Final cleanup of duplicate destinations"""

from app.database import engine
from app import models
from sqlalchemy.orm import Session

db = Session(engine)

print("\n" + "=" * 60)
print("FINAL DUPLICATE CLEANUP")
print("=" * 60)

# Remove Gangtok duplicates (keep ID 145, remove 208, 209)
gangtok_dups = [208, 209]
print(f"\n🗑️  Removing Gangtok duplicates (IDs: {gangtok_dups})")
for dest_id in gangtok_dups:
    dest = db.query(models.Destination).filter(models.Destination.id == dest_id).first()
    if dest:
        print(f"   • Deleted: ID {dest_id} - {dest.name} ({dest.category})")
        db.delete(dest)

# Remove Ooty Hill Station duplicates (keep ID 56, remove 206, 207)
ooty_dups = [206, 207]
print(f"\n🗑️  Removing Ooty Hill Station duplicates (IDs: {ooty_dups})")
for dest_id in ooty_dups:
    dest = db.query(models.Destination).filter(models.Destination.id == dest_id).first()
    if dest:
        print(f"   • Deleted: ID {dest_id} - {dest.name} ({dest.category})")
        db.delete(dest)

db.commit()

# Verify
final_count = db.query(models.Destination).count()
from sqlalchemy import func
duplicates = db.query(
    models.Destination.name,
    func.count(models.Destination.id).label('count')
).group_by(models.Destination.name).having(
    func.count(models.Destination.id) > 1
).count()

print(f"\n✅ CLEANUP COMPLETE")
print(f"   • Total destinations: {final_count}")
print(f"   • Remaining duplicates: {duplicates}")
print("=" * 60 + "\n")

db.close()
