from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.events import router as events_router
from app.db.session import get_db
from app.main import app
from app.models.base import Base
from app.models.event import Event, EventSourceRecord
from app.schemas.event import EventCandidate
from app.services.ingestion.adapters import (
    CuratedJsonLdSiteAdapter,
    RSSFeedAdapter,
    RawEvent,
    StaticJsonAdapter,
)
from app.services.ingestion.pipeline import run_ingestion, save_candidate


@pytest.fixture
def db_session():
    engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


def make_candidate(source_name: str, source_url: str) -> EventCandidate:
    return EventCandidate.model_validate({
        'name': 'Example Developer Conference',
        'event_type': 'conference',
        'starts_at': (datetime.now(UTC) + timedelta(days=30)).isoformat(),
        'event_format': 'in_person',
        'official_url': 'https://example.org/events/developer-conf?utm_source=feed',
        'source_name': source_name,
        'source_url': source_url,
    })


def test_static_ingestion_is_repeatable(db_session: Session) -> None:
    sample_path = Path(__file__).parents[1] / 'data' / 'sample_events.json'
    adapter = StaticJsonAdapter(sample_path)

    first_run = run_ingestion(db_session, [adapter])
    second_run = run_ingestion(db_session, [adapter])

    assert first_run['created'] == 1
    assert second_run['updated'] == 1
    assert db_session.scalar(select(func.count()).select_from(Event)) == 1
    assert db_session.scalar(select(func.count()).select_from(EventSourceRecord)) == 1
    event = db_session.scalar(select(Event))
    assert event is not None
    assert event.review_status == 'pending_review'


def test_duplicate_official_url_links_multiple_sources(db_session: Session) -> None:
    first_raw = RawEvent('api-1', 'https://api.example.org/events/1', {})
    second_raw = RawEvent('feed-1', 'https://feed.example.org/item/1', {})
    first_candidate = make_candidate('api-source', first_raw.source_url).model_copy(
        update={'assistance_details': 'Scholarship applications open in January.'}
    )

    assert save_candidate(db_session, first_raw, first_candidate) == 'created'
    assert save_candidate(db_session, second_raw, make_candidate('feed-source', second_raw.source_url)) == 'deduplicated'

    assert db_session.scalar(select(func.count()).select_from(Event)) == 1
    assert db_session.scalar(select(func.count()).select_from(EventSourceRecord)) == 2
    event = db_session.scalar(select(Event))
    assert event is not None
    assert event.assistance_details == 'Scholarship applications open in January.'


def test_rss_normalizer_uses_explicit_event_date() -> None:
    adapter = RSSFeedAdapter('community-rss', 'https://events.example.org/feed.xml')
    raw = RawEvent(
        source_event_id='item-1',
        source_url='https://events.example.org/item-1',
        payload={
            'name': 'Regional Developer Conference',
            'starts_at': '2027-08-10T09:00:00-04:00',
            'official_url': 'https://events.example.org/item-1',
            'category': 'conference',
            'location': 'Online',
            'assistance_available': 'yes',
        },
    )

    candidate = adapter.normalize(raw)

    assert candidate.event_type.value == 'conference'
    assert candidate.event_format.value == 'virtual'
    assert candidate.assistance_available is True


def test_jsonld_site_normalizes_structured_event() -> None:
    adapter = CuratedJsonLdSiteAdapter('curated-site', 'https://events.example.org/summit')
    raw = RawEvent(
        source_event_id='event-1',
        source_url='https://events.example.org/summit',
        payload={
            '@type': 'Event',
            'name': 'Cloud Engineering Summit',
            'startDate': '2027-06-12T09:00:00-04:00',
            'endDate': '2027-06-12T17:00:00-04:00',
            'url': '/summit/register',
            'eventAttendanceMode': 'https://schema.org/OnlineEventAttendanceMode',
            'location': {'name': 'Online'},
        },
    )

    candidate = adapter.normalize(raw)

    assert candidate.event_type.value == 'summit'
    assert candidate.event_format.value == 'virtual'
    assert str(candidate.official_url) == 'https://events.example.org/summit/register'
    assert candidate.assistance_available is None


def test_candidate_rejects_naive_datetime() -> None:
    candidate_data = make_candidate('test', 'https://example.org').model_dump()
    candidate_data['starts_at'] = datetime(2027, 1, 1)
    with pytest.raises(ValidationError):
        EventCandidate.model_validate(candidate_data)


def test_public_api_only_returns_approved_future_events(db_session: Session) -> None:
    now = datetime.now(UTC)
    common_fields = {
        'event_type': 'conference',
        'starts_at': now + timedelta(days=10),
        'event_format': 'virtual',
        'official_url': 'https://example.org/events/',
        'topics': [],
    }
    db_session.add_all([
        Event(name='Approved event', review_status='approved', **common_fields),
        Event(
            name='Pending event',
            review_status='pending_review',
            official_url='https://example.org/events/pending',
            **{key: value for key, value in common_fields.items() if key != 'official_url'},
        ),
    ])
    db_session.commit()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.get('/api/events')
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert [event['name'] for event in response.json()] == ['Approved event']
    assert response.json()[0]['starts_at'].endswith(('Z', '+00:00'))