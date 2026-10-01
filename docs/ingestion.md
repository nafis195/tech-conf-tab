# Event Ingestion MVP

## Sources

The backend provides four adapters:

- `StaticJsonAdapter` reads the local sample file at `backend/data/sample_events.json`.
- `ICalendarAdapter` reads `.ics` calendars with concrete `VEVENT` records.
- `RSSFeedAdapter` reads RSS items that include an explicit event start-date field such as `eventStartDate`, `startDate`, or `dtstart`. It intentionally does not treat an item's publication date as its event date.
- `JsonApiAdapter` reads a JSON list or an object containing an `events` list. API records should use the canonical event field names.
- `CuratedJsonLdSiteAdapter` reads `schema.org/Event` records embedded as JSON-LD on explicitly configured conference pages.

Remote source URLs are opt-in. Add comma-separated URLs to the root `.env` file:

```dotenv
EVENT_ICS_FEEDS=https://events.example.org/calendar.ics
EVENT_RSS_FEEDS=https://events.example.org/events.rss
EVENT_JSON_API_URLS=https://api.example.org/events
EVENT_CURATED_SITE_URLS=https://conference.example.org/events
```

The sample URLs above are placeholders. Configure only sources you are permitted to access and use. The adapters do not crawl arbitrary domains. iCalendar recurrence rules are not expanded by this MVP.

## Local Run With Docker Compose

From the repository root:

```bash
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml exec backend alembic upgrade head
docker compose -f docker/docker-compose.yml exec backend python -m app.services.ingestion.runner
```

The sample dataset creates a `pending_review` event using reserved `example.org` URLs. Imported events are never auto-approved. For a local API smoke test only, approve the sample row in PostgreSQL:

```bash
docker compose -f docker/docker-compose.yml exec db psql -U postgres -d tech_conf_tab -c "UPDATE events SET review_status = 'approved' WHERE official_url LIKE 'https://example.org/events/%';"
```

The public endpoint is `GET http://localhost:8000/api/events`. It returns approved future events only and accepts `limit` (1–100) and `offset` query parameters.

## Adding An Adapter

Implement `fetch()` to yield `RawEvent` records and `normalize()` to return a validated `EventCandidate`. Register the adapter in `app/services/ingestion/runner.py`. Validation failures are counted and logged; valid records are persisted with source provenance. Records with the same source ID are updated on subsequent runs, while matching normalized official URLs are linked to the existing event.

## Bedrock Later

Keep any Bedrock integration inside a future unstructured-page adapter that returns an `EventCandidate`. The current schema, validation, deduplication, provenance, and persistence steps can remain unchanged. AI-extracted events should continue to enter `pending_review`.