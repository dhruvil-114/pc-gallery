# Contributing to PC Gallery 🖼️

Thank you for your interest in contributing to **PC Gallery**! Community contributions help make this project more powerful, accessible, and fast.

---

## 📌 Ways to Contribute

- **Bug Reports**: Open an Issue detailing steps to reproduce, OS version, and console logs.
- **Feature Requests**: Suggest ideas (e.g., semantic search with CLIP, video indexing, timeline heatmaps).
- **Pull Requests**: Implement performance optimizations, UI improvements, or new features.
- **Documentation**: Help improve setup instructions for Linux / macOS or add usage tips.

---

## 🚀 Development Setup

1. **Fork the Repository** on GitHub.
2. **Clone your fork locally**:
   ```bash
   git clone https://github.com/dhruvil-114/pc-gallery.git
   cd pc-gallery
   ```
3. **Backend Setup**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate

   pip install -r backend/requirements.txt
   python backend/app/download_models.py
   ```
4. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
5. **Run Developer Server**:
   You can run `run_dev.bat` on Windows to launch both backend and frontend hot-reloading dev servers simultaneously.

---

## 📋 Guidelines

- Keep code clean, modular, and typed where appropriate.
- Adhere to PEP 8 standards for Python and ESLint/Prettier standards for JavaScript/React.
- Do not commit any personal database files (`gallery.db`), thumbnails, or personal image directories.

---

## 📄 License

Contributions are submitted under the project's [MIT License](LICENSE).
