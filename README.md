# Local AI-Powered Photo Gallery

An ultra-responsive, modern, locally hosted photo gallery for PC that scans local directories, generates thumbnails, and uses AI facial clustering to organize photos by people.

## Tech Stack
- **Backend:** FastAPI, SQLite (with WAL mode & foreign keys), SQLAlchemy, Pillow, Face Recognition/Clustering.
- **Frontend:** React (Vite), Tailwind CSS, Virtualized Infinite Grid.
- **Code Quality:** CodeRabbit integration for automated reviews and clean architecture.

## Folder Structure
```
pc_gallery/
├── .coderabbit.yaml          # CodeRabbit review configuration
├── .gitignore                # Git ignore rules
├── README.md
├── backend/
│   ├── requirements.txt      # Python dependencies
│   ├── data/                 # SQLite database and .gallery_cache (auto-created)
│   └── app/
│       ├── __init__.py
│       ├── main.py           # FastAPI application and routing
│       ├── database.py       # Engine, SQLite WAL/FK pragmas, session & init_db
│       ├── models.py         # SQLAlchemy models (Image, Person, FaceMap)
│       ├── schemas.py        # Pydantic schemas (V2)
│       └── crud.py           # Database CRUD queries
└── frontend/                 # Vite + React + Tailwind (Step 4 & 5)
```

## Running the Backend (Step 1)
```bash
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload --port 8000
```
Swagger UI will be available at: `http://localhost:8000/docs`
