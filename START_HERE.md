# GuidelineCheck — Quick Start

1. Unzip `GuidelineCheck.zip` and `cd GuidelineCheck`

2. **Backend** (terminal 1):
   ```bash
   cd backend
   pip install -r requirements.txt --break-system-packages   # or use a venv
   cd ..
   uvicorn app.main:app --reload --app-dir backend --host 0.0.0.0 --port 8000
   ```

3. **Ingest the synthetic documents** (terminal 2, once the backend is running):
   ```bash
   python scripts/ingest_documents.py --reset
   ```

4. **Frontend** (terminal 3):
   ```bash
   cd frontend
   pip install -r requirements.txt --break-system-packages
   cd ..
   streamlit run frontend/app.py
   ```

5. Open the URL Streamlit prints (usually `http://localhost:8501`) and try:
   *"What is the current measles outbreak vaccination protocol?"*

No API key is required — it runs fully offline in deterministic extractive-fallback mode by
default. If you want LLM-generated answers instead, copy `.env.example` to `.env` and set
`LLM_PROVIDER` + the matching API key.

Run the backend test suite anytime with:
```bash
cd backend && PYTHONPATH=. python -m pytest tests/ -v
```

Full details, architecture diagram, and troubleshooting are in `README.md` inside the zip.
