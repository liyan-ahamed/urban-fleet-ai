from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event, EventCreate, EventRead

router = APIRouter(tags=["events"])


@router.post("/events", response_model=EventRead, status_code=201)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    record = Event(**event.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/events", response_model=list[EventRead])
def list_events(
    type: Optional[str] = None,
    bus_id: Optional[str] = None,
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db),
):
    statement = select(Event)
    if type:
        statement = statement.where(Event.type == type)
    if bus_id:
        statement = statement.where(Event.bus_id == bus_id)
    if start_date:
        statement = statement.where(Event.timestamp >= start_date)
    if end_date:
        statement = statement.where(Event.timestamp <= end_date)
    return db.scalars(statement.order_by(Event.timestamp.desc())).all()


@router.get("/events/{event_id}", response_model=EventRead)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
