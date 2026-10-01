# Tech Conf Tab — Tasks

## Project Status

This plan tracks the MVP implementation for the conference discovery platform. Items are grouped by delivery phase and should be updated as work progresses.

## Phase 1 — Project Foundation

- [ ] Confirm the project structure and repository conventions
- [ ] Set up the frontend React + TypeScript app
- [ ] Set up the FastAPI backend and Python environment
- [ ] Configure PostgreSQL for local development
- [ ] Add Docker Compose orchestration for frontend, backend, and database
- [ ] Create environment variable samples and local configuration files
- [ ] Add initial backend health-check endpoint and frontend smoke check
- [ ] Document local setup and runtime commands in the README

## Phase 2 — Data and Domain Model

- [ ] Define database tables for events, users, favorites, reminders, and submissions
- [ ] Add event status enums and audit support
- [ ] Set up Alembic migration workflow
- [ ] Create backend models and validation schemas
- [ ] Add seed data for testing and local development
- [ ] Implement repository/service layer structure for core domain logic

## Phase 3 — Public Event Experience

- [ ] Build the public events listing page with search
- [ ] Add filtering by type, format, region, date, and assistance availability
- [ ] Add sorting for event date, name, and location
- [ ] Implement responsive card/table layout
- [ ] Add event detail view with official website link
- [ ] Support upcoming-events default behavior
- [ ] Add pagination or incremental loading for large result sets

## Phase 4 — Organizer and Moderator Workflow

- [ ] Create organizer submission form and validation
- [ ] Implement submission status tracking
- [ ] Add moderator review queue
- [ ] Implement approve, reject, and request-change actions
- [ ] Record decision history and audit events
- [ ] Add duplicate/inappropriate submission handling rules
- [ ] Ensure approved events become publicly visible after review

## Phase 5 — Favorites and Notifications

- [ ] Add authenticated user favorites flow
- [ ] Implement favorite creation and removal APIs
- [ ] Add reminder preference configuration for users
- [ ] Build reminder scheduling logic for one-month and one-week notifications
- [ ] Ensure reminder delivery is idempotent and de-duped
- [ ] Record notification delivery history and failures

## Phase 6 — Expired Event Automation

- [ ] Implement event expiration detection
- [ ] Mark expired/archived events without deleting records immediately
- [ ] Remove expired events from default public listings
- [ ] Add administrator summary notifications for new expirations
- [ ] Validate idempotent background job behavior

## Phase 7 — Admin and Security

- [ ] Add role-based access control for admin and moderator actions
- [ ] Create administrative event management tools
- [ ] Add user management and role assignment views or APIs
- [ ] Review audit trail logging and data integrity constraints
- [ ] Harden endpoint security and input validation
- [ ] Verify secret handling and environment protections

## Phase 8 — Testing and Quality

- [ ] Add backend tests for health, auth, and event logic
- [ ] Add frontend smoke tests or UI validation checks
- [ ] Add integration tests for submission and moderation flow
- [ ] Test reminder and expiration automation behavior
- [ ] Confirm all critical flows pass local validation

## Phase 9 — Release Readiness

- [ ] Prepare final environment docs for local startup
- [ ] Verify Docker Compose setup and dependency installation
- [ ] Review performance and UX polish for MVP release
- [ ] Capture known gaps and deferred features for future phases
- [ ] Prepare a cloud migration plan for later AWS deployment

## Definition of Done

The MVP is complete when:
- the app runs locally through Docker Compose
- users can browse, filter, and save events
- organizers can submit events and moderators can review them
- reminders and expiration jobs work without duplicate processing
- the codebase is documented and ready for incremental team development
