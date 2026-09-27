from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    rows = db.execute(select(Event.type, func.count(Event.id)).group_by(Event.type)).all()
    return [{"type": event_type, "count": count} for event_type, count in rows]


@router.get("/heatmap")
def heatmap(db: Session = Depends(get_db)):
    rows = db.execute(select(Event.lat, Event.lng, Event.confidence)).all()
    return [{"lat": lat, "lng": lng, "weight": round(confidence, 2)} for lat, lng, confidence in rows]
