from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now() -> datetime:
    """Return current UTC timestamp without timezone offset issues."""
    return datetime.now(timezone.utc)


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    original_path = Column(String, unique=True, index=True, nullable=False)
    thumbnail_path = Column(String, nullable=True)
    date_taken = Column(DateTime, nullable=True, index=True)
    is_processed_for_faces = Column(Boolean, default=False, index=True, nullable=False)
    file_size = Column(Integer, nullable=True)  # File size in bytes
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    face_maps = relationship("FaceMap", back_populates="image", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Image id={self.id} path='{self.original_path}'>"


class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, default="Unknown", nullable=False, index=True)
    profile_face_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    face_maps = relationship("FaceMap", back_populates="person")

    def __repr__(self) -> str:
        return f"<Person id={self.id} name='{self.name}'>"


class FaceMap(Base):
    __tablename__ = "face_maps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id = Column(Integer, ForeignKey("people.id", ondelete="SET NULL"), nullable=True, index=True)
    bounding_box = Column(Text, nullable=True)  # JSON string representing [top, right, bottom, left]
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    image = relationship("Image", back_populates="face_maps")
    person = relationship("Person", back_populates="face_maps")

    def __repr__(self) -> str:
        return f"<FaceMap id={self.id} image_id={self.image_id} person_id={self.person_id}>"
