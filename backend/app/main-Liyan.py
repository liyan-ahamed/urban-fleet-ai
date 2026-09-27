import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load backend/.env before importing modules that read configuration.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DEBUG = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"}

from .database import Base, engine
from .routes import analytics_router, events_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Urban Fleet AI API", version="0.1.0", debug=DEBUG)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(events_router)
app.include_router(analytics_router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}
