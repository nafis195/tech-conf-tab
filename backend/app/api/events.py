from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import Event
from app.schemas.event import EventFormat, EventRead, EventType

router = APIRouter(prefix='/api/events', tags=['events'])


@router.get('', response_model=list[EventRead])
def list_approved_events(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, max_length=200),
    event_type: EventType | None = None,
    event_format: EventFormat | None = None,
    assistance_available: bool | None = None,
) -> list[Event]:
    statement = (
        select(Event)
        .where(
            Event.review_status == 'approved',
            Event.starts_at >= datetime.now(UTC),
        )
        .order_by(Event.starts_at, Event.id)
        .offset(offset)
        .limit(limit)
    )
    if q and q.strip():
        search = f'%{q.strip()}%'
        statement = statement.where(or_(
            Event.name.ilike(search),
            Event.description.ilike(search),
            Event.city.ilike(search),
            Event.region.ilike(search),
            Event.country.ilike(search),
        ))
    if event_type is not None:
        statement = statement.where(Event.event_type == event_type.value)
    if event_format is not None:
        statement = statement.where(Event.event_format == event_format.value)
    if assistance_available is not None:
        statement = statement.where(Event.assistance_available.is_(assistance_available))
    return list(db.scalars(statement).all())