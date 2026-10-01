from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class EventType(str, Enum):
    conference = 'conference'
    summit = 'summit'
    meetup = 'meetup'
    workshop = 'workshop'
    round_table = 'round_table'
    other = 'other'


class EventFormat(str, Enum):
    in_person = 'in_person'
    virtual = 'virtual'
    hybrid = 'hybrid'


class ReviewStatus(str, Enum):
    pending_review = 'pending_review'
    changes_requested = 'changes_requested'
    approved = 'approved'
    rejected = 'rejected'
    expired = 'expired'
    archived = 'archived'


class EventCandidate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=300)
    event_type: EventType = EventType.other
    description: str | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    timezone: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=150)
    region: str | None = Field(default=None, max_length=150)
    country: str | None = Field(default=None, max_length=150)
    venue: str | None = Field(default=None, max_length=300)
    event_format: EventFormat = EventFormat.in_person
    assistance_available: bool | None = None
    assistance_details: str | None = None
    assistance_url: HttpUrl | None = None
    official_url: HttpUrl
    organizer_name: str | None = Field(default=None, max_length=200)
    organizer_email: str | None = Field(default=None, max_length=320)
    topics: list[str] = Field(default_factory=list)
    source_name: str = Field(min_length=1, max_length=100)
    source_url: HttpUrl

    @field_validator('starts_at', 'ends_at')
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError('Event datetimes must include a timezone')
        return value

    @model_validator(mode='after')
    def end_must_follow_start(self):
        if self.ends_at is not None and self.ends_at < self.starts_at:
            raise ValueError('ends_at must be after starts_at')
        return self


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_validator('starts_at', 'ends_at')
    @classmethod
    def restore_utc_for_naive_database_values(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    id: int
    name: str
    event_type: EventType
    description: str | None
    starts_at: datetime
    ends_at: datetime | None
    timezone: str | None
    city: str | None
    region: str | None
    country: str | None
    venue: str | None
    event_format: EventFormat
    assistance_available: bool | None
    assistance_details: str | None
    assistance_url: str | None
    official_url: str
    organizer_name: str | None
    topics: list[str]
    review_status: ReviewStatus