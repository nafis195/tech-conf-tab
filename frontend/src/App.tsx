import { FormEvent, useEffect, useState } from 'react';

type EventFormat = 'in_person' | 'virtual' | 'hybrid';
type EventType = 'conference' | 'summit' | 'meetup' | 'workshop' | 'round_table' | 'other';

interface ConferenceEvent {
  id: number;
  name: string;
  event_type: EventType;
  description: string | null;
  starts_at: string;
  ends_at: string | null;
  timezone: string | null;
  city: string | null;
  region: string | null;
  country: string | null;
  venue: string | null;
  event_format: EventFormat;
  assistance_available: boolean | null;
  assistance_details: string | null;
  assistance_url: string | null;
  official_url: string;
  organizer_name: string | null;
  topics: string[];
  review_status: string;
}

interface EventFilters {
  q: string;
  event_type: string;
  event_format: string;
  assistance_available: string;
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '';

const App = () => {
  const [events, setEvents] = useState<ConferenceEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [filters, setFilters] = useState<EventFilters>({
    q: '',
    event_type: '',
    event_format: '',
    assistance_available: '',
  });

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ limit: '50' });
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });

    setLoading(true);
    setError('');
    fetch(`${apiBaseUrl}/api/events?${params.toString()}`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error('The event service could not load events.');
        return response.json() as Promise<ConferenceEvent[]>;
      })
      .then(setEvents)
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return;
        setError(requestError instanceof Error ? requestError.message : 'Unable to load events.');
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [filters]);

  const submitSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFilters((current) => ({ ...current, q: searchInput.trim() }));
  };

  const updateFilter = (key: keyof Omit<EventFilters, 'q'>, value: string) => {
    setFilters((current) => ({ ...current, [key]: value }));
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Tech Conf Tab home">
          <span className="brand-mark">TC</span>
          <span>Tech Conf Tab</span>
        </a>
        <span className="topbar-note">The technical events directory</span>
      </header>

      <section className="directory" aria-labelledby="page-title">
        <div className="intro-row">
          <div>
            <p className="eyebrow">Discover what's next</p>
            <h1 id="page-title">Find your next<br />technical gathering.</h1>
          </div>
          <p className="intro-copy">
            Conferences, workshops, and meetups from across the technology community.
          </p>
        </div>

        <form className="search-panel" onSubmit={submitSearch}>
          <label className="search-field">
            <span className="field-label">Search events</span>
            <input
              type="search"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Name, place, or topic"
            />
          </label>
          <label>
            <span className="field-label">Type</span>
            <select value={filters.event_type} onChange={(event) => updateFilter('event_type', event.target.value)}>
              <option value="">All types</option>
              <option value="conference">Conference</option>
              <option value="summit">Summit</option>
              <option value="meetup">Meetup</option>
              <option value="workshop">Workshop</option>
              <option value="round_table">Round table</option>
            </select>
          </label>
          <label>
            <span className="field-label">Format</span>
            <select value={filters.event_format} onChange={(event) => updateFilter('event_format', event.target.value)}>
              <option value="">Any format</option>
              <option value="in_person">In person</option>
              <option value="virtual">Virtual</option>
              <option value="hybrid">Hybrid</option>
            </select>
          </label>
          <label>
            <span className="field-label">Assistance</span>
            <select
              value={filters.assistance_available}
              onChange={(event) => updateFilter('assistance_available', event.target.value)}
            >
              <option value="">Any status</option>
              <option value="true">Available</option>
              <option value="false">Not available</option>
            </select>
          </label>
          <button className="search-button" type="submit">Search events <span aria-hidden="true">↗</span></button>
        </form>

        <div className="results-heading">
          <div>
            <p className="eyebrow">Upcoming</p>
            <h2>Events worth your time</h2>
          </div>
          <span className="result-count">{loading ? 'Loading' : `${events.length} shown`}</span>
        </div>

        {error && <div className="notice error" role="alert">{error}</div>}
        {loading && <div className="notice" role="status">Loading upcoming events…</div>}
        {!loading && !error && events.length === 0 && (
          <div className="empty-state">
            <span className="empty-mark" aria-hidden="true">—</span>
            <h3>No events match just yet</h3>
            <p>Try another search, or check back as new events are reviewed and published.</p>
          </div>
        )}

        <div className="event-list">
          {events.map((item) => {
            const start = new Date(item.starts_at);
            const dateLabel = new Intl.DateTimeFormat(undefined, {
              month: 'short', day: 'numeric', year: 'numeric',
              timeZone: item.timezone ?? undefined,
            }).format(start);
            const place = [item.city, item.region, item.country].filter(Boolean).join(', ');
            const assistance = item.assistance_available === true
              ? 'Assistance available'
              : item.assistance_available === false ? 'No assistance' : 'Assistance not listed';

            return (
              <article className="event-row" key={item.id}>
                <div className="event-date">
                  <span>{dateLabel}</span>
                  <span>{item.timezone ?? 'Local time'}</span>
                </div>
                <div className="event-main">
                  <div className="event-heading">
                    <span className="event-type">{item.event_type.replace('_', ' ')}</span>
                    <span className={`format-tag ${item.event_format}`}>{item.event_format.replace('_', ' ')}</span>
                  </div>
                  <h3>{item.name}</h3>
                  <p className="event-location">{place || (item.event_format === 'virtual' ? 'Online' : 'Location to be announced')}</p>
                  {item.description && <p className="event-description">{item.description}</p>}
                  <div className="event-footer">
                    <span className={item.assistance_available === true ? 'assistance available' : 'assistance'}>
                      <span className="assistance-dot" aria-hidden="true" />{assistance}
                    </span>
                    {item.organizer_name && <span className="organizer">By {item.organizer_name}</span>}
                    <a href={item.official_url} target="_blank" rel="noreferrer">
                      Event website <span aria-hidden="true">↗</span>
                    </a>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </section>
      <footer className="site-footer"><span>TECH CONF TAB</span><span>Events selected for curious minds.</span></footer>
    </main>
  );
};

export default App;
