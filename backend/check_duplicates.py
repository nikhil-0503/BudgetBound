"""Check for and display remaining duplicate destinations"""

from app.database import engine
from app import models
from sqlalchemy.orm import Session
from sqlalchemy import func

db = Session(engine)

# Find duplicates
duplicates = db.query(
    models.Destination.name,
    func.count(models.Destination.id).label('count')
).group_by(models.Destination.name).having(
    func.count(models.Destination.id) > 1
).all()

print(f"\nFound {len(duplicates)} duplicate destination names:\n")

for name, count in duplicates:
    print(f"'{name}' appears {count} times:")
    entries = db.query(models.Destination).filter(
        models.Destination.name == name
    ).all()
    for entry in entries:
        desc = entry.description[:60] if entry.description else "No description"
        print(f"  • ID {entry.id}: {desc}... (Category: {entry.category})")
    print()

db.close()
