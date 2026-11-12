import os
import sys
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODELS = [
    {
        "name": "YuNet Face Detector (~230 KB)",
        "file": MODELS_DIR / "face_detection_yunet_2023mar.onnx",
        "url": "https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx",
        "min_size": 100_000,
    },
    {
        "name": "SFace Face Recognizer (~37 MB)",
        "file": MODELS_DIR / "face_recognition_sface_2021dec.onnx",
        "url": "https://huggingface.co/opencv/face_recognition_sface/resolve/main/face_recognition_sface_2021dec.onnx",
        "min_size": 10_000_000,
    },
]


def reporthook(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100, int(downloaded * 100 / total_size))
        mb_down = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        sys.stdout.write(f"\r  Progress: {percent}% ({mb_down:.1f} MB / {mb_total:.1f} MB)")
        sys.stdout.flush()


def download_all_models():
    print("\n--- Checking AI Facial Recognition Models ---")
    for m in MODELS:
        target = m["file"]
        if target.exists() and target.stat().st_size >= m["min_size"]:
            print(f"[OK] {m['name']} is already present.")
            continue

        print(f"[Downloading] {m['name']} from HuggingFace...")
        try:
            urllib.request.urlretrieve(m["url"], target, reporthook=reporthook)
            print("\n  [Done] Downloaded successfully!")
        except Exception as exc:
            print(f"\n  [Error] Failed to download {m['name']}: {exc}")
            sys.exit(1)

    print("All AI models ready!\n")


if __name__ == "__main__":
    download_all_models()
