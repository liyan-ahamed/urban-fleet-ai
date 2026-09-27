from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String, index=True)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    bus_id: Mapped[str] = mapped_column(String, index=True)
    plate_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    vehicle_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class EventCreate(BaseModel):
    type: str = Field(pattern="^(pothole|hit_and_run|rash_driving|missing_signage|waterlogging|vehicle_density|pedestrian_risk)$")
    lat: float
    lng: float
    confidence: float = Field(ge=0, le=1)
    timestamp: datetime
    bus_id: str
    plate_number: Optional[str] = None
    severity: Optional[str] = None
    vehicle_count: Optional[int] = Field(default=None, ge=0)


class EventRead(EventCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)
