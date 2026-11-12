import os
import shutil
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

from app.database import init_db, SessionLocal
from app.models import Image as DBImage
from app.scanner import scanner_manager, generate_thumbnail, extract_date_taken
from app import crud


def test_scanner_and_thumbnails():
    # 1. Initialize database
    init_db()

    # 2. Create temporary folder with mock test images
    temp_dir = Path(tempfile.mkdtemp(prefix="gallery_test_"))
    try:
        img1_path = temp_dir / "sample1.jpg"
        img1 = Image.new("RGB", (800, 600), color=(73, 109, 137))
        draw = ImageDraw.Draw(img1)
        draw.text((10, 10), "Test Image 1", fill=(255, 255, 0))
        img1.save(img1_path, "JPEG")

        img2_path = temp_dir / "sample2.png"
        img2 = Image.new("RGBA", (1200, 900), color=(180, 50, 80, 255))
        img2.save(img2_path, "PNG")

        print(f"Created test images in: {temp_dir}")

        # 3. Test thumbnail generation directly
        thumb1 = generate_thumbnail(img1_path)
        assert thumb1 is not None and Path(thumb1).exists(), "Thumbnail 1 failed to generate"
        print(f"Direct thumbnail 1 generated at: {thumb1}")

        # 4. Run scan worker
        scanner_manager.start_scan(str(temp_dir), force_rescan=True)
        if scanner_manager._thread:
            scanner_manager._thread.join(timeout=10)

        status = scanner_manager.get_status()
        print(f"Scan status: {status}")
        assert status["total_files"] == 2, f"Expected 2 total files, got {status['total_files']}"
        assert status["indexed_count"] == 2, f"Expected 2 indexed files, got {status['indexed_count']}"

        # 5. Query DB records via CRUD
        db = SessionLocal()
        try:
            images, total = crud.get_images(db=db, page=1, limit=10)
            assert total >= 2, f"Expected >= 2 total images in DB, got {total}"
            print(f"CRUD query returned {total} images in DB.")

            for img in images:
                if img.original_path.startswith(temp_dir.as_posix()):
                    assert img.thumbnail_path is not None
                    assert Path(img.thumbnail_path).exists(), f"Thumbnail not on disk: {img.thumbnail_path}"
                    assert img.date_taken is not None
                    print(f"Verified image id={img.id}, thumb={Path(img.thumbnail_path).name}, date={img.date_taken}")
        finally:
            db.close()

        print(">>> ALL SCANNER & THUMBNAIL TESTS PASSED! <<<")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_scanner_and_thumbnails()
