"""Remove duplicate destination entries from database"""
from app.database import SessionLocal
from app import models

db = SessionLocal()

# List of duplicate destination names to remove
duplicates_to_remove = [
    "Manali Couple Getaway",
    "Andaman Islands Romantic Escape", 
    "Coorg Family Holiday"
]

removed_count = 0
for dup_name in duplicates_to_remove:
    dest = db.query(models.Destination).filter(
        models.Destination.name == dup_name
    ).first()
    
    if dest:
        print(f"Removing duplicate: {dest.name}")
        db.delete(dest)
        removed_count += 1

# Rename Gangtok Family Sikkim to just Gangtok
gangtok_family = db.query(models.Destination).filter(
    models.Destination.name == "Gangtok Family Sikkim"
).first()

if gangtok_family:
    print(f"Renaming: {gangtok_family.name} -> Gangtok")
    gangtok_family.name = "Gangtok"
    gangtok_family.category = "Nature"
    gangtok_family.description = "Beautiful orchid houses, cable car rides, and colourful Rumtek Monastery for exploration."

db.commit()
print(f"\nTotal removed: {removed_count} duplicate destinations")
print("Database cleaned successfully!")

db.close()
