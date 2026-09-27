"""Simple simulated route for development without a bus GPS feed."""

from __future__ import annotations


class GPSSimulator:
    """Move gradually through a bounded Chennai route on each sampled frame."""

    def __init__(self, start_lat: float = 13.0827, start_lng: float = 80.2707):
        self.lat = start_lat
        self.lng = start_lng
        self.lat_step = 0.00018
        self.lng_step = -0.00012

    def next_position(self) -> tuple[float, float]:
        """Return the next simulated latitude/longitude within Chennai bounds."""
        self.lat += self.lat_step
        self.lng += self.lng_step
        if not 12.95 <= self.lat <= 13.20:
            self.lat_step *= -1
            self.lat += self.lat_step * 2
        if not 80.15 <= self.lng <= 80.30:
            self.lng_step *= -1
            self.lng += self.lng_step * 2
        return round(self.lat, 6), round(self.lng, 6)
