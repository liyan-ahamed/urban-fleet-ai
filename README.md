# urban-fleet-ai

Urban intelligence prototype for visualising AI-detected road and traffic events from a public bus fleet. The dashboard currently uses realistic mock data; the backend `POST /events` endpoint is the future AI detector integration point.

## Run locally

Start the backend first. It creates the SQLite database and seeds 200 mock Chennai events when empty:

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload --port 8000
```

Then start the dashboard in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The dashboard fetches data from the API at http://localhost:8000.

See the README files in `backend/` and `frontend/` for their individual setup details.
