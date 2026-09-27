# Backend

FastAPI and SQLite service for urban fleet events.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload --port 8000
```

The service is available at http://localhost:8000 and interactive API docs are at `/docs`.

`seed.py` is safe to run repeatedly: it only adds the initial 200 events to an empty database. Delete `urban_fleet.db` to generate a fresh dataset.
