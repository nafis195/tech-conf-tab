from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Event(Base):
    __tablename__ = 'events'
    __table_args__ = (
        CheckConstraint(
            "review_status IN ('pending_review', 'changes_requested', 'approved', 'rejected', 'expired', 'archived')",
            name='ck_events_review_status',
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(150))
    region: Mapped[str | None] = mapped_column(String(150))
    country: Mapped[str | None] = mapped_column(String(150))
    venue: Mapped[str | None] = mapped_column(String(300))
    event_format: Mapped[str] = mapped_column(String(30), nullable=False)
    assistance_available: Mapped[bool | None] = mapped_column(Boolean)
    assistance_details: Mapped[str | None] = mapped_column(Text)
    assistance_url: Mapped[str | None] = mapped_column(String(2048))
    official_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    organizer_name: Mapped[str | None] = mapped_column(String(200))
    organizer_email: Mapped[str | None] = mapped_column(String(320))
    topics: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    review_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default='pending_review', index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    sources: Mapped[list['EventSourceRecord']] = relationship(
        back_populates='event', cascade='all, delete-orphan'
    )


class EventSourceRecord(Base):
    __tablename__ = 'event_source_records'
    __table_args__ = (
        UniqueConstraint('source_name', 'source_event_id', name='uq_source_name_event_id'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_event_id: Mapped[str | None] = mapped_column(String(300))
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    event: Mapped[Event] = relationship(back_populates='sources')