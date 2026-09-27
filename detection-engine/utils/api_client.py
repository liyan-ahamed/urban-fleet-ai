"""Client for the local Urban Fleet API."""

from __future__ import annotations

import requests


EVENTS_URL = "http://localhost:8000/events"


def post_event(event_dict: dict) -> dict:
    """POST an event payload and return the backend's created event."""
    response = requests.post(EVENTS_URL, json=event_dict, timeout=10)
    response.raise_for_status()
    return response.json()
