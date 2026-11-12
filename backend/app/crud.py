from typing import List, Optional, Tuple
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from app.models import FaceMap, Image, Person
from app.schemas import ImageCreate, ImageUpdate, PersonCreate, PersonUpdate, FaceMapCreate


# ------------------------------------------------------------------
# Image CRUD
# ------------------------------------------------------------------
def get_image(db: Session, image_id: int) -> Optional[Image]:
    return db.query(Image).filter(Image.id == image_id).first()


def get_image_by_path(db: Session, original_path: str) -> Optional[Image]:
    return db.query(Image).filter(Image.original_path == original_path).first()


def get_images(
    db: Session,
    page: int = 1,
    limit: int = 50,
) -> Tuple[List[Image], int]:
    offset = max(0, (page - 1) * limit)
    query = db.query(Image)
    total = query.count()
    items = (
        query.order_by(
            Image.date_taken.desc().nullslast(),
            Image.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def create_image(db: Session, image_in: ImageCreate) -> Image:
    db_image = Image(
        original_path=image_in.original_path,
        thumbnail_path=image_in.thumbnail_path,
        date_taken=image_in.date_taken,
        is_processed_for_faces=image_in.is_processed_for_faces,
        file_size=image_in.file_size,
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image


def update_image(db: Session, image_id: int, image_in: ImageUpdate) -> Optional[Image]:
    db_image = get_image(db, image_id)
    if not db_image:
        return None

    update_data = image_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_image, field, value)

    db.commit()
    db.refresh(db_image)
    return db_image


def delete_image(db: Session, image_id: int) -> bool:
    db_image = get_image(db, image_id)
    if not db_image:
        return False
    db.delete(db_image)
    db.commit()
    return True


def get_unprocessed_images_for_faces(db: Session, limit: int = 100) -> List[Image]:
    return (
        db.query(Image)
        .filter(Image.is_processed_for_faces.is_(False))
        .order_by(Image.id.asc())
        .limit(limit)
        .all()
    )


# ------------------------------------------------------------------
# People CRUD
# ------------------------------------------------------------------
def get_person(db: Session, person_id: int) -> Optional[Person]:
    return db.query(Person).filter(Person.id == person_id).first()


def get_people(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> List[dict]:
    """Retrieve people with count of associated images."""
    rows = (
        db.query(
            Person,
            func.count(FaceMap.id).label("image_count")
        )
        .outerjoin(FaceMap, FaceMap.person_id == Person.id)
        .group_by(Person.id)
        .order_by(desc("image_count"), Person.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for person, count in rows:
        result.append(
            {
                "id": person.id,
                "name": person.name,
                "profile_face_path": person.profile_face_path,
                "created_at": person.created_at,
                "image_count": count or 0,
            }
        )
    return result


def create_person(db: Session, person_in: PersonCreate) -> Person:
    db_person = Person(
        name=person_in.name,
        profile_face_path=person_in.profile_face_path,
    )
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person


def update_person(db: Session, person_id: int, person_in: PersonUpdate) -> Optional[Person]:
    db_person = get_person(db, person_id)
    if not db_person:
        return None

    update_data = person_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_person, field, value)

    db.commit()
    db.refresh(db_person)
    return db_person


def delete_person(db: Session, person_id: int) -> bool:
    db_person = get_person(db, person_id)
    if not db_person:
        return False
    db.delete(db_person)
    db.commit()
    return True


def get_images_by_person(
    db: Session,
    person_id: int,
    page: int = 1,
    limit: int = 50,
) -> Tuple[List[Image], int]:
    offset = max(0, (page - 1) * limit)
    query = (
        db.query(Image)
        .join(FaceMap, FaceMap.image_id == Image.id)
        .filter(FaceMap.person_id == person_id)
        .distinct()
    )
    total = query.count()
    items = (
        query.order_by(
            Image.date_taken.desc().nullslast(),
            Image.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


# ------------------------------------------------------------------
# FaceMap CRUD
# ------------------------------------------------------------------
def create_face_map(db: Session, face_map_in: FaceMapCreate) -> FaceMap:
    db_map = FaceMap(
        image_id=face_map_in.image_id,
        person_id=face_map_in.person_id,
        bounding_box=face_map_in.bounding_box,
        confidence=face_map_in.confidence,
    )
    db.add(db_map)
    db.commit()
    db.refresh(db_map)
    return db_map


def get_faces_for_image(db: Session, image_id: int) -> List[FaceMap]:
    return db.query(FaceMap).filter(FaceMap.image_id == image_id).all()
