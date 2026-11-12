# Local AI-Powered Photo Gallery (PC)

An ultra-responsive, modern, locally hosted photo gallery for PC that scans local directories, generates thumbnails, and uses AI facial recognition (YuNet + SFace) to cluster and organize photos by people.

---

## ⚡ Quick Start (Windows)

### 1. Fresh PC Setup
On a new PC, simply double-click:
```
setup.bat
```
This automated script will:
1. Verify Python (3.10+) and Node.js/NPM prerequisites.
2. Create all database and `.gallery_cache` directories.
3. Install all Python dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `pillow`, `opencv-python`, `numpy`, etc.).
4. Download the local AI facial recognition ONNX models (~230 KB YuNet + ~37 MB SFace).
5. Install frontend NPM packages and build the optimized production UI into `frontend/dist`.
6. Initialize the SQLite database.

---

### 2. Launching the Gallery
Whenever you want to use the gallery, double-click:
```
run.bat
```
* Starts the unified FastAPI server on `http://localhost:8000`.
* Automatically opens your default web browser to `http://localhost:8000`.
* API interactive Swagger documentation is accessible at `http://localhost:8000/docs`.

---

## 🛠️ Tech Stack
- **Backend:** FastAPI, SQLite (with WAL mode & foreign keys), SQLAlchemy, Pillow, OpenCV YuNet & SFace DNN models.
- **Frontend:** React, Vite, Tailwind CSS, Lucide Icons, Infinite Virtualized Grid, Fullscreen Lightbox.
- **Code Quality:** CodeRabbit integration ([.coderabbit.yaml](.coderabbit.yaml)) for clean, production-grade architecture.

## 📁 Folder Structure
```text
pc_gallery/
├── setup.bat                 # One-click installer for new PCs
├── run.bat                   # One-click launcher
├── run_dev.bat               # Developer mode (hot-reloading Vite + FastAPI)
├── .coderabbit.yaml          # CodeRabbit review configuration
├── .gitignore
├── README.md
├── backend/
│   ├── requirements.txt      # Python dependencies
│   ├── data/                 # SQLite database and .gallery_cache (auto-created)
│   │   └── models/           # YuNet & SFace ONNX AI models
│   ├── app/
│   │   ├── main.py           # FastAPI application, static file serving & REST endpoints
│   │   ├── database.py       # Engine, SQLite WAL/FK pragmas, session & init_db
│   │   ├── models.py         # SQLAlchemy models (Image, Person, FaceMap)
│   │   ├── schemas.py        # Pydantic schemas (V2)
│   │   ├── crud.py           # Database CRUD operations
│   │   ├── scanner.py        # Multithreaded directory scanner & WebP thumbnail generator
│   │   ├── face_engine.py    # AI facial detection & clustering worker (YuNet + SFace)
│   │   └── download_models.py# Automatic AI models downloader
│   └── tests/                # Automated backend unit tests
└── frontend/                 # React + Tailwind application
    ├── dist/                 # Production build served directly by FastAPI
    └── src/
        ├── App.jsx           # Master gallery controller
        ├── api.js            # Frontend API client
        └── components/
            ├── ImageCard.jsx     # Photo thumbnail card with progressive load
            ├── ImageGrid.jsx     # Responsive infinite-scroll grid
            ├── PeopleGrid.jsx    # Recognized people cards & renaming
            ├── LightboxModal.jsx # Fullscreen modal with EXIF & face tags
            ├── ScanModal.jsx     # Local folder scanner modal
            └── Sidebar.jsx       # Navigation sidebar & AI quick trigger
```
