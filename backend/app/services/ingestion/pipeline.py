from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event, EventSourceRecord
from app.schemas.event import EventCandidate
from app.services.ingestion.adapters import EventSource, RawEvent


def canonicalize_url(value: str) -> str:
    parts = urlsplit(value)
    query = urlencode([
        (key, item) for key, item in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith('utm_') and key.lower() not in {'fbclid', 'gclid'}
    ])
    path = parts.path.rstrip('/') or '/'
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, ''))


def save_candidate(db: Session, raw: RawEvent, candidate: EventCandidate) -> str:
    source_record = None
    if raw.source_event_id:
        source_record = db.scalar(
            select(EventSourceRecord).where(
                EventSourceRecord.source_name == candidate.source_name,
                EventSourceRecord.source_event_id == raw.source_event_id,
            )
        )

    event = source_record.event if source_record else None
    normalized_url = canonicalize_url(str(candidate.official_url))
    result = 'updated'
    if event is None:
        event = db.scalar(select(Event).where(Event.official_url == normalized_url))
        result = 'deduplicated' if event else 'created'

    fields = candidate.model_dump(exclude={'source_name', 'source_url'})
    fields['event_type'] = candidate.event_type.value
    fields['event_format'] = candidate.event_format.value
    if candidate.assistance_url is not None:
        fields['assistance_url'] = str(candidate.assistance_url)
    fields['official_url'] = str(candidate.official_url)
    fields['official_url'] = normalized_url
    if event is None:
        event = Event(**fields, review_status='pending_review')
        db.add(event)
        db.flush()
    elif result == 'updated':
        # Preserve moderator decisions; refresh imported event data only.
        for field, value in fields.items():
            setattr(event, field, value)
    else:
        # A secondary source adds provenance and only fills gaps in the canonical event.
        for field, value in fields.items():
            if value is not None and value != [] and getattr(event, field) in (None, '', []):
                setattr(event, field, value)

    if source_record is None:
        source_record = EventSourceRecord(
            event=event,
            source_name=candidate.source_name,
            source_event_id=raw.source_event_id,
            source_url=canonicalize_url(raw.source_url),
            raw_payload=raw.payload,
        )
        db.add(source_record)
    else:
        source_record.source_url = canonicalize_url(raw.source_url)
        source_record.raw_payload = raw.payload
        source_record.last_seen_at = datetime.now(UTC)

    db.commit()
    return result


def run_ingestion(db: Session, sources: list[EventSource]) -> dict[str, Any]:
    result: dict[str, Any] = {'created': 0, 'updated': 0, 'deduplicated': 0, 'failed': 0}
    errors: list[str] = []

    for source in sources:
        try:
            for raw in source.fetch():
                try:
                    candidate = source.normalize(raw)
                    outcome = save_candidate(db, raw, candidate)
                    result[outcome] += 1
                except Exception as error:
                    db.rollback()
                    result['failed'] += 1
                    errors.append(f'{source.name}: {error}')
        except Exception as error:
            db.rollback()
            result['failed'] += 1
            errors.append(f'{source.name} fetch failed: {error}')

    result['errors'] = errors
    return result