from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# -------------------------------------------------------------
# Image Schemas
# -------------------------------------------------------------
class ImageBase(BaseModel):
    original_path: str
    thumbnail_path: Optional[str] = None
    date_taken: Optional[datetime] = None
    is_processed_for_faces: bool = False
    file_size: Optional[int] = None


class ImageCreate(ImageBase):
    pass


class ImageUpdate(BaseModel):
    thumbnail_path: Optional[str] = None
    date_taken: Optional[datetime] = None
    is_processed_for_faces: Optional[bool] = None
    file_size: Optional[int] = None


class ImageOut(ImageBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedImages(BaseModel):
    items: List[ImageOut]
    total: int
    page: int
    limit: int
    has_next: bool


# -------------------------------------------------------------
# FaceMap Schemas
# -------------------------------------------------------------
class FaceMapBase(BaseModel):
    image_id: int
    person_id: Optional[int] = None
    bounding_box: Optional[str] = None
    confidence: Optional[float] = None


class FaceMapCreate(FaceMapBase):
    pass


class FaceMapOut(FaceMapBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# People Schemas
# -------------------------------------------------------------
class PersonBase(BaseModel):
    name: str = "Unknown"
    profile_face_path: Optional[str] = None


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    profile_face_path: Optional[str] = None


class PersonOut(PersonBase):
    id: int
    created_at: datetime
    image_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Scan Request / Response Schemas
# -------------------------------------------------------------
class ScanRequest(BaseModel):
    folder_path: str = Field(..., description="Absolute path of folder to scan on local machine")
    force_rescan: bool = Field(False, description="Whether to re-scan already indexed files")


class ScanResponse(BaseModel):
    status: str
    message: str
    folder_path: str
