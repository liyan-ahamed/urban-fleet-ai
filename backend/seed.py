import random
from datetime import datetime, timedelta

from app.database import Base, SessionLocal, engine
from app.models import Event

Base.metadata.create_all(bind=engine)

EVENT_TYPES = [
    ("pothole", 38), ("vehicle_density", 20), ("waterlogging", 14),
    ("missing_signage", 11), ("pedestrian_risk", 9), ("rash_driving", 6),
    ("hit_and_run", 2),
]
SEVERITIES = ["low", "medium", "high", "critical"]


def pick_type():
    types, weights = zip(*EVENT_TYPES)
    return random.choices(types, weights=weights, k=1)[0]


def plate():
    return f"TN {random.randint(1, 99):02d} {random.choice(['AB', 'CD', 'EF', 'GH'])} {random.randint(1000, 9999)}"


def main():
    db = SessionLocal()
    try:
        if db.query(Event).count():
            print("Database already contains events; skipping seed.")
            return
        now = datetime.now()
        events = []
        for _ in range(200):
            event_type = pick_type()
            events.append(Event(
                type=event_type,
                lat=round(random.uniform(12.95, 13.20), 6),
                lng=round(random.uniform(80.15, 80.30), 6),
                confidence=round(random.uniform(0.62, 0.99), 2),
                timestamp=now - timedelta(hours=random.uniform(0, 72)),
                bus_id=f"MTC-{random.randint(1, 42):03d}",
                plate_number=plate() if event_type in {"hit_and_run", "rash_driving"} else None,
                severity=random.choice(SEVERITIES) if event_type in {"pothole", "waterlogging", "missing_signage"} else None,
                vehicle_count=random.randint(12, 85) if event_type == "vehicle_density" else None,
            ))
        db.add_all(events)
        db.commit()
        print("Seeded 200 Chennai fleet events.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
