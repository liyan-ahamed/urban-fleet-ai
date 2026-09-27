"""Client for the local Urban Fleet API."""

from __future__ import annotations

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load detection-engine/.env when this client is imported by main.py.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
EVENTS_URL = f"{BACKEND_API_URL.rstrip('/')}/events"


def post_event(event_dict: dict) -> dict:
    """POST an event payload and return the backend's created event."""
    response = requests.post(EVENTS_URL, json=event_dict, timeout=10)
    response.raise_for_status()
    return response.json()
