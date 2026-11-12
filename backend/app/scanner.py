import hashlib
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from PIL import Image as PILImage, ImageOps, ExifTags

from app.database import SessionLocal, THUMBNAIL_DIR
from app.models import Image
from app import crud, schemas

logger = logging.getLogger("gallery.scanner")

# Supported image file extensions
SUPPORTED_EXTENSIONS: Set[str] = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tiff",
    ".tif",
}

# Optional HEIC support check
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    SUPPORTED_EXTENSIONS.update({".heic", ".heif"})
except ImportError:
    pass


def extract_date_taken(image_path: Path, pil_img: Optional[PILImage.Image] = None) -> datetime:
    """Extract photo capture date from EXIF tags or fallback to file modification time."""
    if pil_img is not None:
        try:
            exif = pil_img.getexif()
            if exif:
                # 36867 = DateTimeOriginal, 36868 = DateTimeDigitized, 306 = DateTime
                date_str = None
                for tag_id in (36867, 36868, 306):
                    val = exif.get(tag_id)
                    if val and isinstance(val, str):
                        date_str = val.strip()
                        break

                if date_str:
                    # Common EXIF date formats
                    for fmt in (
                        "%Y:%m:%d %H:%M:%S",
                        "%Y-%m-%d %H:%M:%S",
                        "%Y:%m:%d %H:%M",
                        "%Y-%m-%d %H:%M",
                    ):
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
        except Exception as exc:
            logger.debug(f"Could not read EXIF date for {image_path}: {exc}")

    # Fallback to filesystem mtime
    try:
        mtime = os.path.getmtime(image_path)
        return datetime.fromtimestamp(mtime)
    except Exception:
        return datetime.now()


def generate_thumbnail(image_path: Path, target_size=(400, 400), quality: int = 82) -> Optional[str]:
    """Generate high-quality WebP thumbnail maintaining aspect ratio and EXIF orientation."""
    try:
        # Create unique deterministic hash based on normalized path and file size
        stat = os.stat(image_path)
        hash_input = f"{image_path.resolve().as_posix()}_{stat.st_mtime}_{stat.st_size}"
        thumb_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:20]
        thumb_filename = f"{thumb_hash}.webp"
        thumb_path = THUMBNAIL_DIR / thumb_filename

        # If thumbnail already exists on disk, reuse it
        if thumb_path.exists():
            return str(thumb_path.resolve())

        with PILImage.open(image_path) as img:
            # Auto-rotate based on EXIF orientation tag
            img = ImageOps.exif_transpose(img)

            # Convert color modes suitable for WebP
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

            # Resample thumbnail
            resample_filter = getattr(PILImage, "Resampling", PILImage).LANCZOS
            img.thumbnail(target_size, resample=resample_filter)

            # Save as WebP
            img.save(thumb_path, format="WEBP", quality=quality, method=6)
            return str(thumb_path.resolve())
    except Exception as exc:
        logger.error(f"Failed to generate thumbnail for {image_path}: {exc}")
        return None


class ScanManager:
    """Thread-safe manager for recursive scanning, thumbnail generation, and progress tracking."""

    def __init__(self):
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self.is_scanning: bool = False
        self.folder_path: Optional[str] = None
        self.total_files: int = 0
        self.processed_files: int = 0
        self.indexed_count: int = 0
        self.skipped_count: int = 0
        self.error_count: int = 0
        self.current_file: Optional[str] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.recent_errors: List[str] = []

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            elapsed = 0.0
            if self.start_time:
                end = self.end_time or time.time()
                elapsed = round(end - self.start_time, 2)

            return {
                "is_scanning": self.is_scanning,
                "folder_path": self.folder_path,
                "total_files": self.total_files,
                "processed_files": self.processed_files,
                "indexed_count": self.indexed_count,
                "skipped_count": self.skipped_count,
                "error_count": self.error_count,
                "current_file": self.current_file,
                "elapsed_seconds": elapsed,
                "recent_errors": self.recent_errors[-10:],
            }

    def cancel_scan(self) -> bool:
        if not self.is_scanning:
            return False
        self._stop_event.set()
        return True

    def start_scan(self, folder_path: str, force_rescan: bool = False) -> bool:
        with self._lock:
            if self.is_scanning:
                return False

            self.is_scanning = True
            self.folder_path = folder_path
            self.total_files = 0
            self.processed_files = 0
            self.indexed_count = 0
            self.skipped_count = 0
            self.error_count = 0
            self.current_file = None
            self.start_time = time.time()
            self.end_time = None
            self.recent_errors = []
            self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run_scan_worker,
            args=(folder_path, force_rescan),
            daemon=True,
        )
        self._thread.start()
        return True

    def _run_scan_worker(self, folder_path: str, force_rescan: bool):
        logger.info(f"Starting directory traversal in: {folder_path}")
        root_dir = Path(folder_path)

        # 1. Discover all candidate image files
        all_candidates: List[Path] = []
        try:
            for root, _, files in os.walk(root_dir):
                if self._stop_event.is_set():
                    break
                for f in files:
                    ext = Path(f).suffix.lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        all_candidates.append(Path(root) / f)
        except Exception as exc:
            with self._lock:
                self.recent_errors.append(f"Directory walk error: {exc}")

        with self._lock:
            self.total_files = len(all_candidates)

        logger.info(f"Discovered {len(all_candidates)} image files to process.")

        # 2. Process images with dedicated database session
        db = SessionLocal()
        try:
            # Cache known paths in memory for instant O(1) duplicate checks
            existing_records = {
                img.original_path: (img.id, img.thumbnail_path)
                for img in db.query(Image.original_path, Image.id, Image.thumbnail_path).all()
            }

            for file_path in all_candidates:
                if self._stop_event.is_set():
                    logger.info("Scan cancelled by user.")
                    break

                posix_path = file_path.resolve().as_posix()

                with self._lock:
                    self.current_file = file_path.name

                # Check if already indexed
                already_indexed = posix_path in existing_records
                if already_indexed and not force_rescan:
                    _, existing_thumb = existing_records[posix_path]
                    if existing_thumb and Path(existing_thumb).exists():
                        with self._lock:
                            self.processed_files += 1
                            self.skipped_count += 1
                        continue

                # Process image
                try:
                    stat = file_path.stat()
                    file_size = stat.st_size

                    # Open image to extract EXIF and verify readability
                    with PILImage.open(file_path) as pil_img:
                        date_taken = extract_date_taken(file_path, pil_img)

                    # Generate WebP thumbnail
                    thumb_path = generate_thumbnail(file_path)

                    if already_indexed:
                        # Update existing record
                        img_id, _ = existing_records[posix_path]
                        crud.update_image(
                            db=db,
                            image_id=img_id,
                            image_in=schemas.ImageUpdate(
                                thumbnail_path=thumb_path,
                                date_taken=date_taken,
                                file_size=file_size,
                            ),
                        )
                    else:
                        # Insert new record
                        new_img = crud.create_image(
                            db=db,
                            image_in=schemas.ImageCreate(
                                original_path=posix_path,
                                thumbnail_path=thumb_path,
                                date_taken=date_taken,
                                is_processed_for_faces=False,
                                file_size=file_size,
                            ),
                        )
                        existing_records[posix_path] = (new_img.id, thumb_path)

                    with self._lock:
                        self.processed_files += 1
                        self.indexed_count += 1

                except Exception as exc:
                    err_msg = f"{file_path.name}: {str(exc)}"
                    logger.warning(f"Error processing image {err_msg}")
                    with self._lock:
                        self.processed_files += 1
                        self.error_count += 1
                        self.recent_errors.append(err_msg)

        finally:
            db.close()
            with self._lock:
                self.is_scanning = False
                self.end_time = time.time()
                self.current_file = None
            logger.info("Scan completed.")


# Global scanner instance
scanner_manager = ScanManager()
