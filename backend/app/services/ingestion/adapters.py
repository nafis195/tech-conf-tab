import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urljoin
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

import httpx

from app.schemas.event import EventCandidate, EventFormat, EventType


@dataclass
class RawEvent:
    source_event_id: str | None
    source_url: str
    payload: dict[str, Any]


class EventSource(Protocol):
    name: str

    def fetch(self) -> Iterable[RawEvent]: ...

    def normalize(self, raw: RawEvent) -> EventCandidate: ...


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
    except ValueError:
        parsed = parsedate_to_datetime(value.strip())
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed


def _event_type(*values: str | None) -> EventType:
    text = ' '.join(str(value or '') for value in values).lower().replace('-', ' ')
    for kind, terms in {
        EventType.conference: ('conference', 'convention'),
        EventType.summit: ('summit',),
        EventType.meetup: ('meetup', 'meet up'),
        EventType.workshop: ('workshop', 'hackathon'),
        EventType.round_table: ('round table', 'roundtable'),
    }.items():
        if any(term in text for term in terms):
            return kind
    return EventType.other


def _event_format(*values: str | None) -> EventFormat:
    text = ' '.join(str(value or '') for value in values).lower()
    remote = any(term in text for term in ('online', 'virtual', 'webinar'))
    physical = any(term in text for term in ('in person', 'in-person', 'onsite', 'on-site'))
    if remote and physical:
        return EventFormat.hybrid
    if remote:
        return EventFormat.virtual
    return EventFormat.in_person


class StaticJsonAdapter:
    def __init__(self, path: Path):
        self.path = path
        self.name = 'local-samples'

    def fetch(self) -> Iterable[RawEvent]:
        records = json.loads(self.path.read_text(encoding='utf-8'))
        for record in records:
            yield RawEvent(
                source_event_id=str(record['id']),
                source_url=record.get('source_url', record['official_url']),
                payload=record,
            )

    def normalize(self, raw: RawEvent) -> EventCandidate:
        fields = {key: value for key, value in raw.payload.items() if key != 'id'}
        fields.setdefault('source_name', self.name)
        fields.setdefault('source_url', raw.source_url)
        return EventCandidate.model_validate(fields)


class JsonApiAdapter:
    """Adapter for APIs returning canonical event fields in JSON."""

    def __init__(self, name: str, url: str, events_key: str = 'events'):
        self.name = name
        self.url = url
        self.events_key = events_key

    def fetch(self) -> Iterable[RawEvent]:
        response = httpx.get(self.url, timeout=20, follow_redirects=True)
        response.raise_for_status()
        body = response.json()
        records = body if isinstance(body, list) else body[self.events_key]
        for record in records:
            yield RawEvent(
                source_event_id=str(record['id']) if record.get('id') is not None else None,
                source_url=record.get('source_url') or record.get('url') or self.url,
                payload=record,
            )

    def normalize(self, raw: RawEvent) -> EventCandidate:
        fields = dict(raw.payload)
        fields.pop('id', None)
        fields.setdefault('source_name', self.name)
        fields.setdefault('source_url', raw.source_url)
        if 'official_url' not in fields and 'url' in fields:
            fields['official_url'] = fields.pop('url')
        return EventCandidate.model_validate(fields)


class RSSFeedAdapter:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def fetch(self) -> Iterable[RawEvent]:
        response = httpx.get(self.url, timeout=20, follow_redirects=True)
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        for index, item in enumerate(
            element for element in root.iter() if element.tag.rsplit('}', 1)[-1].lower() == 'item'
        ):
            payload: dict[str, Any] = {}
            for child in item:
                key = child.tag.rsplit('}', 1)[-1].replace('_', '').lower()
                text = ''.join(child.itertext()).strip()
                aliases = {
                    'eventstartdate': 'starts_at', 'startdate': 'starts_at', 'dtstart': 'starts_at',
                    'eventenddate': 'ends_at', 'enddate': 'ends_at', 'dtend': 'ends_at',
                    'eventtype': 'event_type_text', 'category': 'category',
                    'eventformat': 'event_format_text', 'location': 'location',
                    'city': 'city', 'region': 'region', 'country': 'country',
                    'assistanceavailable': 'assistance_available',
                    'assistancedetails': 'assistance_details', 'assistanceurl': 'assistance_url',
                    'organizer': 'organizer_name', 'organizername': 'organizer_name',
                    'organizeremail': 'organizer_email', 'description': 'description',
                    'title': 'name', 'link': 'official_url', 'guid': 'guid',
                }
                mapped_key = aliases.get(key)
                if mapped_key:
                    if mapped_key == 'category' and payload.get('category'):
                        payload['category'] += f' {text}'
                    else:
                        payload[mapped_key] = text
            if not payload.get('starts_at'):
                continue
            yield RawEvent(
                source_event_id=payload.get('guid') or payload.get('official_url') or str(index),
                source_url=payload.get('official_url') or self.url,
                payload=payload,
            )

    def normalize(self, raw: RawEvent) -> EventCandidate:
        item = raw.payload
        start = _parse_datetime(item.get('starts_at'))
        end = _parse_datetime(item.get('ends_at'))
        if start is None:
            raise ValueError('RSS event is missing an event start date')
        assistance_value = item.get('assistance_available')
        assistance = None
        if assistance_value:
            normalized = assistance_value.strip().lower()
            if normalized in {'true', 'yes', 'available', '1'}:
                assistance = True
            elif normalized in {'false', 'no', 'unavailable', '0'}:
                assistance = False
        location = item.get('location')
        return EventCandidate.model_validate({
            'name': item.get('name'),
            'event_type': _event_type(item.get('event_type_text'), item.get('category'), item.get('name')),
            'description': item.get('description'),
            'starts_at': start,
            'ends_at': end,
            'timezone': str(start.tzinfo),
            'city': item.get('city'),
            'region': item.get('region'),
            'country': item.get('country'),
            'venue': location,
            'event_format': _event_format(item.get('event_format_text'), location),
            'assistance_available': assistance,
            'assistance_details': item.get('assistance_details'),
            'assistance_url': item.get('assistance_url'),
            'official_url': item.get('official_url') or raw.source_url,
            'organizer_name': item.get('organizer_name'),
            'organizer_email': item.get('organizer_email'),
            'source_name': self.name,
            'source_url': raw.source_url,
        })


class ICalendarAdapter:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def fetch(self) -> Iterable[RawEvent]:
        response = httpx.get(self.url, timeout=20, follow_redirects=True)
        response.raise_for_status()
        lines: list[str] = []
        for line in response.text.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
            if line.startswith((' ', '\t')) and lines:
                lines[-1] += line[1:]
            else:
                lines.append(line)

        component: list[str] | None = None
        for line in lines:
            if line == 'BEGIN:VEVENT':
                component = []
            elif line == 'END:VEVENT' and component is not None:
                payload = self._parse_component(component)
                yield RawEvent(
                    source_event_id=payload.get('uid'),
                    source_url=payload.get('url') or self.url,
                    payload=payload,
                )
                component = None
            elif component is not None:
                component.append(line)

    def _parse_component(self, lines: list[str]) -> dict[str, Any]:
        properties: dict[str, tuple[dict[str, str], str]] = {}
        for line in lines:
            if ':' not in line:
                continue
            key_part, value = line.split(':', 1)
            key, *parameter_parts = key_part.split(';')
            parameters = {
                part.split('=', 1)[0].upper(): part.split('=', 1)[1].strip('"')
                for part in parameter_parts
                if '=' in part
            }
            properties[key.upper()] = (parameters, value)

        def value(name: str) -> str | None:
            item = properties.get(name)
            if item is None:
                return None
            return item[1].replace('\\n', '\n').replace('\\,', ',').replace('\\;', ';').replace('\\\\', '\\')

        def date_value(name: str) -> datetime | None:
            item = properties.get(name)
            if item is None:
                return None
            parameters, raw_value = item
            if re.fullmatch(r'\d{8}', raw_value):
                return datetime.combine(date.fromisoformat(
                    f'{raw_value[:4]}-{raw_value[4:6]}-{raw_value[6:]}'
                ), datetime.min.time(), tzinfo=UTC)
            parsed = datetime.strptime(raw_value, '%Y%m%dT%H%M%S%z') if raw_value.endswith('Z') else datetime.strptime(
                raw_value, '%Y%m%dT%H%M%S'
            )
            if parsed.tzinfo is None:
                timezone_name = parameters.get('TZID', 'UTC')
                parsed = parsed.replace(tzinfo=ZoneInfo(timezone_name))
            return parsed

        summary = value('SUMMARY') or ''
        description = value('DESCRIPTION')
        location = value('LOCATION')
        start = date_value('DTSTART')
        if start is None:
            raise ValueError('iCalendar event is missing DTSTART')
        return {
            'uid': value('UID'),
            'name': summary,
            'event_type': _event_type(summary),
            'description': description,
            'starts_at': start.isoformat(),
            'ends_at': date_value('DTEND').isoformat() if date_value('DTEND') else None,
            'timezone': str(start.tzinfo),
            'venue': location,
            'event_format': _event_format(location, description),
            'official_url': value('URL') or self.url,
        }

    def normalize(self, raw: RawEvent) -> EventCandidate:
        fields = dict(raw.payload)
        fields.pop('uid', None)
        fields.update(source_name=self.name, source_url=raw.source_url)
        return EventCandidate.model_validate(fields)


class _JsonLdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._capture = False
        self._parts: list[str] = []
        self.documents: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == 'script' and attributes.get('type', '').lower() == 'application/ld+json':
            self._capture = True
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == 'script' and self._capture:
            self.documents.append(''.join(self._parts))
            self._capture = False


class CuratedJsonLdSiteAdapter:
    """Read schema.org Event records from a configured conference page."""

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def fetch(self) -> Iterable[RawEvent]:
        response = httpx.get(self.url, timeout=20, follow_redirects=True)
        response.raise_for_status()
        parser = _JsonLdParser()
        parser.feed(response.text)
        for document in parser.documents:
            for index, event in enumerate(self._event_objects(json.loads(document))):
                event_url = urljoin(self.url, event.get('url', self.url))
                yield RawEvent(
                    source_event_id=str(event.get('@id') or event_url or index),
                    source_url=self.url,
                    payload=event,
                )

    @classmethod
    def _event_objects(cls, document: Any) -> Iterable[dict[str, Any]]:
        if isinstance(document, list):
            for item in document:
                yield from cls._event_objects(item)
        elif isinstance(document, dict):
            if document.get('@type') == 'Event' or (
                isinstance(document.get('@type'), list) and 'Event' in document['@type']
            ):
                yield document
            if '@graph' in document:
                yield from cls._event_objects(document['@graph'])

    def normalize(self, raw: RawEvent) -> EventCandidate:
        event = raw.payload
        location = event.get('location') or {}
        if isinstance(location, list):
            location = location[0] if location else {}
        address = location.get('address') or {} if isinstance(location, dict) else {}
        if isinstance(address, str):
            address = {'streetAddress': address}
        attendance = str(event.get('eventAttendanceMode', ''))
        fmt = _event_format(attendance, str(location.get('name', '')) if isinstance(location, dict) else '')
        start = _parse_datetime(event.get('startDate'))
        end = _parse_datetime(event.get('endDate'))
        if start is None:
            raise ValueError('schema.org Event is missing startDate')
        event_url = urljoin(self.url, event.get('url') or self.url)
        return EventCandidate.model_validate({
            'name': event.get('name'),
            'event_type': _event_type(event.get('name'), event.get('keywords')),
            'description': event.get('description'),
            'starts_at': start,
            'ends_at': end,
            'timezone': str(start.tzinfo),
            'city': address.get('addressLocality'),
            'region': address.get('addressRegion'),
            'country': address.get('addressCountry'),
            'venue': location.get('name') if isinstance(location, dict) else None,
            'event_format': fmt,
            'assistance_available': None,
            'official_url': event_url,
            'organizer_name': (event.get('organizer') or {}).get('name')
                if isinstance(event.get('organizer'), dict) else None,
            'topics': [event['keywords']] if isinstance(event.get('keywords'), str) else event.get('keywords', []),
            'source_name': self.name,
            'source_url': raw.source_url,
        })