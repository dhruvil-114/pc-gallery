import os
import shutil
import tempfile
import time
from pathlib import Path
import cv2
import numpy as np

from app.database import init_db, SessionLocal
from app.models import Image as DBImage, Person, FaceMap
from app.scanner import scanner_manager
from app.face_engine import face_engine, ensure_models
from app import crud


def draw_face_canvas(width=400, height=400, eye_color=(50, 50, 200)):
    """Draw a stylized human-like face representation with contrast for YuNet."""
    canvas = np.ones((height, width, 3), dtype=np.uint8) * 230  # Light background

    # Face oval
    center = (width // 2, height // 2)
    cv2.ellipse(canvas, center, (110, 140), 0, 0, 360, (180, 210, 240), -1)
    cv2.ellipse(canvas, center, (110, 140), 0, 0, 360, (100, 120, 150), 2)

    # Eyes
    left_eye = (width // 2 - 40, height // 2 - 25)
    right_eye = (width // 2 + 40, height // 2 - 25)
    cv2.circle(canvas, left_eye, 14, (255, 255, 255), -1)
    cv2.circle(canvas, right_eye, 14, (255, 255, 255), -1)
    cv2.circle(canvas, left_eye, 6, eye_color, -1)
    cv2.circle(canvas, right_eye, 6, eye_color, -1)

    # Eyebrows
    cv2.line(canvas, (left_eye[0] - 15, left_eye[1] - 18), (left_eye[0] + 15, left_eye[1] - 18), (60, 60, 60), 3)
    cv2.line(canvas, (right_eye[0] - 15, right_eye[1] - 18), (right_eye[0] + 15, right_eye[1] - 18), (60, 60, 60), 3)

    # Nose
    nose_pts = np.array([
        [width // 2, height // 2 - 5],
        [width // 2 - 12, height // 2 + 25],
        [width // 2 + 12, height // 2 + 25]
    ], np.int32)
    cv2.polylines(canvas, [nose_pts], True, (130, 150, 180), 2)

    # Mouth
    cv2.ellipse(canvas, (width // 2, height // 2 + 65), (35, 15), 0, 0, 180, (60, 60, 180), 3)

    return canvas


def test_face_engine():
    print("Ensuring ONNX models are ready...")
    ensure_models()

    init_db()

    temp_dir = Path(tempfile.mkdtemp(prefix="gallery_face_test_"))
    try:
        # Create 2 mock photos
        canvas1 = draw_face_canvas(eye_color=(40, 40, 190))
        canvas2 = np.ones((400, 400, 3), dtype=np.uint8) * 100  # Image with no face

        p1 = temp_dir / "portrait1.jpg"
        p2 = temp_dir / "landscape.jpg"

        cv2.imwrite(str(p1), canvas1)
        cv2.imwrite(str(p2), canvas2)

        # 1. Scan folder first
        print(f"Scanning test folder: {temp_dir}")
        scanner_manager.start_scan(str(temp_dir), force_rescan=True)
        if scanner_manager._thread:
            scanner_manager._thread.join(timeout=10)

        db = SessionLocal()
        try:
            unprocessed_before = db.query(DBImage).filter(DBImage.is_processed_for_faces.is_(False)).count()
            print(f"Unprocessed images before AI step: {unprocessed_before}")
            assert unprocessed_before >= 2
        finally:
            db.close()

        # 2. Trigger Face Engine
        print("Starting AI Facial Recognition engine...")
        face_engine.start_processing()
        if face_engine._thread:
            face_engine._thread.join(timeout=15)

        status = face_engine.get_status()
        print(f"Face Engine status: {status}")

        # 3. Verify in Database
        db = SessionLocal()
        try:
            unprocessed_after = db.query(DBImage).filter(DBImage.is_processed_for_faces.is_(False)).count()
            print(f"Unprocessed images after AI step: {unprocessed_after}")
            assert unprocessed_after == 0, f"Expected 0 unprocessed images, found {unprocessed_after}"

            people = crud.get_people(db=db)
            print(f"Identified people count: {len(people)}")

            # Check FaceMap records
            face_maps = db.query(FaceMap).all()
            print(f"Total face maps recorded: {len(face_maps)}")
        finally:
            db.close()

        print(">>> ALL FACIAL RECOGNITION TESTS PASSED! <<<")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_face_engine()
