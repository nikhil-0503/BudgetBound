from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import uuid
from typing import List

from app import models, schemas, auth
from app.database import get_db

router = APIRouter(prefix="/api/trips", tags=["Documents"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/{trip_id}/documents", response_model=schemas.TravelDocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    trip_id: int,
    category: str = Form(...),
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Verify trip ownership
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    valid_categories = ["Hotel Booking", "Train Ticket", "Flight Ticket", "Bus Ticket", "Passport", "Visa", "Insurance", "Other"]
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"Category must be one of {valid_categories}")

    # Enforce extension check for upload security
    allowed_extensions = {".pdf", ".jpeg", ".jpg", ".png", ".doc", ".docx", ".txt"}
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"File format {file_ext} not allowed. Supported formats: {list(allowed_extensions)}"
        )

    # Save file contents with max size verification (10MB limit)
    MAX_SIZE = 10 * 1024 * 1024 # 10MB
    try:
        contents = await file.read(MAX_SIZE + 1)
        filesize = len(contents)
        if filesize > MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File exceeds maximum allowed upload size of 10MB."
            )
            
        unique_name = f"{uuid.uuid4().hex}{file_ext}"
        filepath = os.path.join(UPLOAD_DIR, unique_name)
        with open(filepath, "wb") as f:
            f.write(contents)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file to storage disk: {e}")

    # Save metadata in DB
    db_doc = models.TravelDocument(
        trip_id=trip_id,
        category=category,
        filename=file.filename,
        filepath=filepath,
        filesize=filesize
    )
    db.add(db_doc)
    
    # Add a success log notification
    db_notif = models.Notification(
        user_id=current_user.id,
        type="Trip Exported" if "ticket" in category.lower() else "Trip Reminder",
        message=f"Uploaded document '{file.filename}' for your trip to {trip.destination.name}."
    )
    db.add(db_notif)
    
    db.commit()
    db.refresh(db_doc)
    return db_doc

@router.get("/{trip_id}/documents", response_model=List[schemas.TravelDocumentOut])
def list_trip_documents(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip.documents

@router.get("/{trip_id}/documents/{doc_id}")
def download_trip_document(
    trip_id: int,
    doc_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Verify owner
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    doc = db.query(models.TravelDocument).filter(models.TravelDocument.id == doc_id, models.TravelDocument.trip_id == trip_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Travel document not found")
    
    if not os.path.exists(doc.filepath):
        raise HTTPException(status_code=404, detail="File content missing on storage server")
    
    return FileResponse(
        path=doc.filepath,
        filename=doc.filename,
        media_type="application/octet-stream"
    )

@router.put("/{trip_id}/documents/{doc_id}", response_model=schemas.TravelDocumentOut)
def rename_trip_document(
    trip_id: int,
    doc_id: int,
    payload: dict,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    doc = db.query(models.TravelDocument).filter(models.TravelDocument.id == doc_id, models.TravelDocument.trip_id == trip_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Travel document not found")
        
    new_name = payload.get("filename")
    if not new_name:
        raise HTTPException(status_code=400, detail="Filename parameter is required")
        
    doc.filename = new_name
    db.commit()
    db.refresh(doc)
    return doc

@router.delete("/{trip_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip_document(
    trip_id: int,
    doc_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    doc = db.query(models.TravelDocument).filter(models.TravelDocument.id == doc_id, models.TravelDocument.trip_id == trip_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Travel document not found")
        
    # Delete from local disk
    if os.path.exists(doc.filepath):
        try:
            os.remove(doc.filepath)
        except Exception:
            pass
            
    db.delete(doc)
    db.commit()
    return None
