import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image as PILImage, ImageOps

from app.database import DATA_DIR, PEOPLE_DIR, SessionLocal
from app.models import FaceMap, Image, Person
from app import crud, schemas

logger = logging.getLogger("gallery.faces")

MODELS_DIR = DATA_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

YUNET_MODEL_FILE = MODELS_DIR / "face_detection_yunet_2023mar.onnx"
SFACE_MODEL_FILE = MODELS_DIR / "face_recognition_sface_2021dec.onnx"

# HuggingFace official release URLs
YUNET_URL = "https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx"
SFACE_URL = "https://huggingface.co/opencv/face_recognition_sface/resolve/main/face_recognition_sface_2021dec.onnx"

# SFace cosine similarity threshold (0.363 is official threshold, 0.40 recommended for tight clusters)
COSINE_SIMILARITY_THRESHOLD = 0.40


def ensure_models():
    """Ensure ONNX weights exist locally; download from HuggingFace if missing."""
    import urllib.request

    if not YUNET_MODEL_FILE.exists() or YUNET_MODEL_FILE.stat().st_size < 10000:
        logger.info("Downloading YuNet face detection model...")
        urllib.request.urlretrieve(YUNET_URL, YUNET_MODEL_FILE)

    if not SFACE_MODEL_FILE.exists() or SFACE_MODEL_FILE.stat().st_size < 1000000:
        logger.info("Downloading SFace face recognition model...")
        urllib.request.urlretrieve(SFACE_URL, SFACE_MODEL_FILE)


class FaceEngine:
    """Fast, local AI Facial Detection and Recognition engine powered by OpenCV YuNet & SFace."""

    def __init__(self):
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self.is_processing: bool = False
        self.total_unprocessed: int = 0
        self.processed_count: int = 0
        self.faces_detected_count: int = 0
        self.people_count: int = 0
        self.current_image: Optional[str] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.recent_errors: List[str] = []

        # Known person average embeddings: {person_id: np.ndarray}
        self.person_embeddings: Dict[int, np.ndarray] = {}

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            elapsed = 0.0
            if self.start_time:
                end = self.end_time or time.time()
                elapsed = round(end - self.start_time, 2)

            return {
                "is_processing": self.is_processing,
                "total_unprocessed": self.total_unprocessed,
                "processed_count": self.processed_count,
                "faces_detected_count": self.faces_detected_count,
                "people_count": self.people_count,
                "current_image": self.current_image,
                "elapsed_seconds": elapsed,
                "recent_errors": self.recent_errors[-10:],
            }

    def cancel_processing(self) -> bool:
        if not self.is_processing:
            return False
        self._stop_event.set()
        return True

    def start_processing(self, batch_size: int = 100) -> bool:
        with self._lock:
            if self.is_processing:
                return False

            self.is_processing = True
            self.total_unprocessed = 0
            self.processed_count = 0
            self.faces_detected_count = 0
            self.current_image = None
            self.start_time = time.time()
            self.end_time = None
            self.recent_errors = []
            self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run_face_worker,
            args=(batch_size,),
            daemon=True,
        )
        self._thread.start()
        return True

    def _load_known_embeddings(self, db) -> Dict[int, np.ndarray]:
        """Load embeddings of known people from cache or existing people."""
        embeddings_cache_file = MODELS_DIR / "people_embeddings.npy"
        if embeddings_cache_file.exists():
            try:
                data = np.load(embeddings_cache_file, allow_pickle=True).item()
                if isinstance(data, dict):
                    return data
            except Exception as exc:
                logger.warning(f"Could not load people embeddings cache: {exc}")

        return {}

    def _save_known_embeddings(self):
        embeddings_cache_file = MODELS_DIR / "people_embeddings.npy"
        try:
            np.save(embeddings_cache_file, self.person_embeddings)
        except Exception as exc:
            logger.warning(f"Failed to persist people embeddings: {exc}")

    def _match_or_create_person(
        self,
        db,
        feature: np.ndarray,
        aligned_face: np.ndarray,
        recognizer: Any,
    ) -> int:
        """Match feature embedding with known persons or create a new Person record."""
        best_person_id: Optional[int] = None
        best_score = -1.0

        # Cosine similarity matching
        for person_id, known_feature in self.person_embeddings.items():
            # OpenCV SFace matching
            score = recognizer.match(feature, known_feature, cv2.FaceRecognizerSF_FR_COSINE)
            if score > best_score:
                best_score = score
                best_person_id = person_id

        # If similarity is high enough, assign to existing person
        if best_person_id is not None and best_score >= COSINE_SIMILARITY_THRESHOLD:
            # Update running average embedding
            curr = self.person_embeddings[best_person_id]
            updated = (curr + feature) / 2.0
            norm = np.linalg.norm(updated)
            if norm > 0:
                updated = updated / norm
            self.person_embeddings[best_person_id] = updated
            return best_person_id

        # Otherwise, create a new unique Person
        new_person = crud.create_person(
            db=db,
            person_in=schemas.PersonCreate(name=f"Person {len(self.person_embeddings) + 1}"),
        )
        person_id = new_person.id

        # Save cropped face image as profile avatar
        avatar_filename = f"person_{person_id}.jpg"
        avatar_path = PEOPLE_DIR / avatar_filename
        cv2.imwrite(str(avatar_path), aligned_face)

        # Update profile avatar path in DB
        crud.update_person(
            db=db,
            person_id=person_id,
            person_in=schemas.PersonUpdate(profile_face_path=str(avatar_path.resolve())),
        )

        # Store normalized embedding
        norm = np.linalg.norm(feature)
        normalized_feat = feature / norm if norm > 0 else feature
        self.person_embeddings[person_id] = normalized_feat
        self._save_known_embeddings()

        with self._lock:
            self.people_count = len(self.person_embeddings)

        return person_id

    def _run_face_worker(self, batch_size: int):
        ensure_models()

        # Initialize detector and recognizer
        detector = cv2.FaceDetectorYN_create(
            str(YUNET_MODEL_FILE),
            "",
            (320, 320),
            0.6,   # Score threshold (0.6 avoids false positives)
            0.3,   # NMS threshold
            5000,  # Top K
        )
        recognizer = cv2.FaceRecognizerSF_create(str(SFACE_MODEL_FILE), "")

        db = SessionLocal()
        try:
            self.person_embeddings = self._load_known_embeddings(db)
            with self._lock:
                self.people_count = len(self.person_embeddings)

            # Query all unprocessed images
            unprocessed = (
                db.query(Image)
                .filter(Image.is_processed_for_faces.is_(False))
                .order_by(Image.id.asc())
                .all()
            )

            with self._lock:
                self.total_unprocessed = len(unprocessed)

            logger.info(f"Starting facial processing for {len(unprocessed)} images.")

            for img_record in unprocessed:
                if self._stop_event.is_set():
                    logger.info("Face processing cancelled by user.")
                    break

                with self._lock:
                    self.current_image = Path(img_record.original_path).name

                try:
                    img_path = Path(img_record.original_path)
                    if not img_path.exists():
                        img_record.is_processed_for_faces = True
                        db.commit()
                        with self._lock:
                            self.processed_count += 1
                        continue

                    # Load image with Pillow first to handle EXIF orientation properly
                    with PILImage.open(img_path) as pil_img:
                        pil_img = ImageOps.exif_transpose(pil_img)
                        if pil_img.mode != "RGB":
                            pil_img = pil_img.convert("RGB")
                        # Downscale if huge (> 1920) for blazing fast detection
                        max_dim = 1600
                        if max(pil_img.size) > max_dim:
                            pil_img.thumbnail((max_dim, max_dim))
                        np_img = np.array(pil_img)
                        # Convert RGB to BGR for OpenCV
                        bgr_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)

                    h, w, _ = bgr_img.shape
                    detector.setInputSize((w, h))

                    # Run YuNet detection
                    _, faces = detector.detect(bgr_img)

                    if faces is not None and len(faces) > 0:
                        for face in faces:
                            # face: [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rcm, y_rcm, x_lcm, y_lcm, score]
                            x, y, fw, fh = int(face[0]), int(face[1]), int(face[2]), int(face[3])
                            confidence = float(face[-1])

                            # Clamp bounding box
                            x = max(0, x)
                            y = max(0, y)
                            fw = min(fw, w - x)
                            fh = min(fh, h - y)

                            if fw < 20 or fh < 20:
                                continue

                            # Align and crop face using SFace
                            aligned_face = recognizer.alignCrop(bgr_img, face)
                            # Extract 128D facial feature vector
                            feature = recognizer.feature(aligned_face)

                            # Match against known persons or create new Person
                            person_id = self._match_or_create_person(
                                db=db,
                                feature=feature,
                                aligned_face=aligned_face,
                                recognizer=recognizer,
                            )

                            # Save FaceMap record
                            box_json = json.dumps([x, y, fw, fh])
                            crud.create_face_map(
                                db=db,
                                face_map_in=schemas.FaceMapCreate(
                                    image_id=img_record.id,
                                    person_id=person_id,
                                    bounding_box=box_json,
                                    confidence=confidence,
                                ),
                            )

                            with self._lock:
                                self.faces_detected_count += 1

                    # Mark image as processed
                    img_record.is_processed_for_faces = True
                    db.commit()

                    with self._lock:
                        self.processed_count += 1

                except Exception as exc:
                    err = f"{Path(img_record.original_path).name}: {str(exc)}"
                    logger.warning(f"Error processing faces for {err}")
                    with self._lock:
                        self.recent_errors.append(err)
                        self.processed_count += 1
                    # Mark processed so we don't loop endlessly on corrupt files
                    img_record.is_processed_for_faces = True
                    db.commit()

            self._save_known_embeddings()

        finally:
            db.close()
            with self._lock:
                self.is_processing = False
                self.end_time = time.time()
                self.current_image = None
            logger.info("Facial recognition background job finished.")


# Global singleton instance
face_engine = FaceEngine()
