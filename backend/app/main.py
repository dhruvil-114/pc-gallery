import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app import crud, models, schemas
from app.scanner import scanner_manager
from app.face_engine import face_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event to automatically initialize database tables on startup."""
    init_db()
    yield


app = FastAPI(
    title="Local AI Photo Gallery API",
    description="Blazingly fast backend for local photo library scanning, face recognition, and indexing.",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for local Vite development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in local desktop environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------
# System & Health
# -------------------------------------------------------------
@app.get("/api/health", tags=["System"])
def health_check():
    return {"status": "ok", "app": "Local AI Photo Gallery"}


# -------------------------------------------------------------
# Image Endpoints
# -------------------------------------------------------------
@app.get("/api/images", response_model=schemas.PaginatedImages, tags=["Images"])
def list_images(
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Fetch paginated photos sorted by date_taken descending."""
    items, total = crud.get_images(db=db, page=page, limit=limit)
    has_next = (page * limit) < total
    return schemas.PaginatedImages(
        items=items,
        total=total,
        page=page,
        limit=limit,
        has_next=has_next,
    )


@app.get("/api/images/{image_id}", response_model=schemas.ImageOut, tags=["Images"])
def get_image_details(image_id: int, db: Session = Depends(get_db)):
    """Fetch details of a single photo by its database ID."""
    image = crud.get_image(db=db, image_id=image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found",
        )
    return image


@app.delete("/api/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Images"])
def delete_image(image_id: int, db: Session = Depends(get_db)):
    """Delete an image record from the gallery database."""
    success = crud.delete_image(db=db, image_id=image_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found",
        )
    return None


@app.get("/api/images/person/{person_id}", response_model=schemas.PaginatedImages, tags=["Images"])
def list_images_by_person(
    person_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Fetch all images where a specific person was recognized."""
    person = crud.get_person(db=db, person_id=person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with id {person_id} not found",
        )
    items, total = crud.get_images_by_person(db=db, person_id=person_id, page=page, limit=limit)
    has_next = (page * limit) < total
    return schemas.PaginatedImages(
        items=items,
        total=total,
        page=page,
        limit=limit,
        has_next=has_next,
    )


# -------------------------------------------------------------
# Static Media Serving (Thumbnails, Full-Res, Face Avatars)
# -------------------------------------------------------------
@app.get("/thumbnail/{image_id}", tags=["Media"])
def serve_thumbnail(image_id: int, db: Session = Depends(get_db)):
    """Serve the generated lightweight thumbnail for fast grid rendering."""
    image = crud.get_image(db=db, image_id=image_id)
    if not image or not image.thumbnail_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not found for image",
        )

    thumb_file = Path(image.thumbnail_path)
    if not thumb_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thumbnail file missing on disk: {thumb_file.name}",
        )

    # Determine media type based on extension
    media_type = "image/webp" if thumb_file.suffix.lower() == ".webp" else "image/jpeg"
    return FileResponse(thumb_file, media_type=media_type)


@app.get("/image/{image_id}", tags=["Media"])
def serve_original_image(image_id: int, db: Session = Depends(get_db)):
    """Serve the full-resolution original image for fullscreen view."""
    image = crud.get_image(db=db, image_id=image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found",
        )

    orig_file = Path(image.original_path)
    if not orig_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Original photo file not found at: {image.original_path}",
        )

    suffix = orig_file.suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }
    media_type = media_type_map.get(suffix, "image/jpeg")
    return FileResponse(orig_file, media_type=media_type)


@app.get("/person-face/{person_id}", tags=["Media"])
def serve_person_face(person_id: int, db: Session = Depends(get_db)):
    """Serve the cropped face thumbnail for a recognized person."""
    person = crud.get_person(db=db, person_id=person_id)
    if not person or not person.profile_face_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Face avatar not available for this person",
        )

    face_file = Path(person.profile_face_path)
    if not face_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Face crop file missing on disk",
        )

    return FileResponse(face_file, media_type="image/jpeg")


# -------------------------------------------------------------
# People Endpoints
# -------------------------------------------------------------
@app.get("/api/people", response_model=List[schemas.PersonOut], tags=["People"])
def list_people(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Fetch list of all unique people identified by facial recognition."""
    people = crud.get_people(db=db, skip=skip, limit=limit)
    return people


@app.get("/api/people/{person_id}", response_model=schemas.PersonOut, tags=["People"])
def get_person(person_id: int, db: Session = Depends(get_db)):
    """Fetch single person details."""
    person = crud.get_person(db=db, person_id=person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with id {person_id} not found",
        )
    # Count images
    _, count = crud.get_images_by_person(db=db, person_id=person_id, page=1, limit=1)
    return {
        "id": person.id,
        "name": person.name,
        "profile_face_path": person.profile_face_path,
        "created_at": person.created_at,
        "image_count": count,
    }


@app.patch("/api/people/{person_id}", response_model=schemas.PersonOut, tags=["People"])
def update_person(
    person_id: int,
    person_in: schemas.PersonUpdate,
    db: Session = Depends(get_db),
):
    """Update a person's display name or avatar path."""
    person = crud.update_person(db=db, person_id=person_id, person_in=person_in)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with id {person_id} not found",
        )
    _, count = crud.get_images_by_person(db=db, person_id=person_id, page=1, limit=1)
    return {
        "id": person.id,
        "name": person.name,
        "profile_face_path": person.profile_face_path,
        "created_at": person.created_at,
        "image_count": count,
    }


# -------------------------------------------------------------
# Scanner Endpoints (Step 2: Non-blocking Multithreaded Engine)
# -------------------------------------------------------------
@app.post("/api/scan", response_model=schemas.ScanResponse, tags=["Scanner"])
def trigger_scan(request: schemas.ScanRequest):
    """Trigger background directory scan and thumbnail generation."""
    target = Path(request.folder_path)
    if not target.exists() or not target.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provided directory does not exist or is not a folder: {request.folder_path}",
        )

    started = scanner_manager.start_scan(
        folder_path=str(target.resolve()),
        force_rescan=request.force_rescan,
    )
    if not started:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A scan job is already actively running. Check /api/scan/status.",
        )

    return schemas.ScanResponse(
        status="started",
        message=f"Scan started for directory '{request.folder_path}'.",
        folder_path=str(target.resolve()),
    )


@app.get("/api/scan/status", response_model=schemas.ScanStatusResponse, tags=["Scanner"])
def get_scan_status():
    """Get live progress and statistics for the background scanner."""
    return scanner_manager.get_status()


@app.post("/api/scan/cancel", response_model=schemas.CancelScanResponse, tags=["Scanner"])
def cancel_scan():
    """Cancel currently running scan job."""
    cancelled = scanner_manager.cancel_scan()
    if not cancelled:
        return schemas.CancelScanResponse(
            status="idle",
            message="No scan is currently running.",
        )
    return schemas.CancelScanResponse(
        status="cancelling",
        message="Scan cancellation signal dispatched.",
    )


# -------------------------------------------------------------
# Facial Recognition & Clustering Endpoints (Step 3)
# -------------------------------------------------------------
@app.post("/api/faces/process", response_model=schemas.FaceActionResponse, tags=["Faces"])
def trigger_face_processing(request: schemas.FaceProcessRequest = schemas.FaceProcessRequest()):
    """Trigger background AI facial recognition worker for unprocessed photos."""
    started = face_engine.start_processing(batch_size=request.batch_size)
    if not started:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Face processing is already running. Check /api/faces/status.",
        )
    return schemas.FaceActionResponse(
        status="started",
        message="AI facial recognition background worker started.",
    )


@app.get("/api/faces/status", response_model=schemas.FaceProcessStatusResponse, tags=["Faces"])
def get_face_processing_status():
    """Get live progress and statistics for AI facial recognition."""
    return face_engine.get_status()


@app.post("/api/faces/cancel", response_model=schemas.FaceActionResponse, tags=["Faces"])
def cancel_face_processing():
    """Cancel currently running AI facial recognition job."""
    cancelled = face_engine.cancel_processing()
    if not cancelled:
        return schemas.FaceActionResponse(
            status="idle",
            message="No facial processing job is currently running.",
        )
    return schemas.FaceActionResponse(
        status="cancelling",
        message="Face processing cancellation signal dispatched.",
    )


@app.get("/api/images/{image_id}/faces", response_model=List[schemas.FaceMapOut], tags=["Faces"])
def get_image_face_tags(image_id: int, db: Session = Depends(get_db)):
    """Retrieve all detected face bounding boxes and recognized people for a photo."""
    return crud.get_faces_for_image(db=db, image_id=image_id)


