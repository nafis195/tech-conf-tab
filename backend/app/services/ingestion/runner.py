import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

from app.db.session import SessionLocal
from app.services.ingestion.adapters import (
    CuratedJsonLdSiteAdapter,
    ICalendarAdapter,
    JsonApiAdapter,
    RSSFeedAdapter,
    StaticJsonAdapter,
)
from app.services.ingestion.pipeline import run_ingestion


def _urls(environment_key: str) -> list[str]:
    return [url.strip() for url in os.getenv(environment_key, '').split(',') if url.strip()]


def build_sources():
    backend_root = Path(__file__).resolve().parents[3]
    sources = [StaticJsonAdapter(backend_root / 'data' / 'sample_events.json')]

    sources.extend(
        ICalendarAdapter(f'ics-{index + 1}', url)
        for index, url in enumerate(_urls('EVENT_ICS_FEEDS'))
    )
    sources.extend(
        RSSFeedAdapter(f'rss-{index + 1}', url)
        for index, url in enumerate(_urls('EVENT_RSS_FEEDS'))
    )
    sources.extend(
        JsonApiAdapter(f'json-api-{index + 1}', url)
        for index, url in enumerate(_urls('EVENT_JSON_API_URLS'))
    )
    sources.extend(
        CuratedJsonLdSiteAdapter(
            f'curated-site-{index + 1}-{urlsplit(url).hostname or "site"}', url
        )
        for index, url in enumerate(_urls('EVENT_CURATED_SITE_URLS'))
    )
    return sources


def main() -> int:
    with SessionLocal() as db:
        result = run_ingestion(db, build_sources())
    print(json.dumps(result, indent=2))
    return 1 if result['failed'] else 0


if __name__ == '__main__':
    sys.exit(main())