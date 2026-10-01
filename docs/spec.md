# Tech Conf Tab — Product Specification

## 1. Overview

Tech Conf Tab is a local-first conference discovery platform that helps users find technical events such as conferences, meetups, workshops, summits, and round tables in a single searchable directory. The platform supports public browsing, organizer submissions, moderation workflows, registration-based favorites, reminder notifications, and administrative management.

The initial version is designed for local development with Docker Compose and PostgreSQL. It is structured so the same application can later be migrated to cloud deployment with AWS services.

## 2. Product Goal

Create a reliable event discovery platform where visitors can find relevant upcoming events quickly, organizers can submit events for review, and administrators can manage content and moderation processes with minimal friction.

## 3. Target Users

### Visitor
- Browses approved upcoming events
- Searches and filters listings
- Views event metadata and official links
- Creates an account

### Registered User
- Performs all visitor actions
- Saves favorite events
- Receives reminder emails
- Manages email notification preferences

### Organizer
- Submits new events
- Tracks review status
- Updates submissions following moderator feedback

### Moderator
- Reviews pending submissions
- Approves, rejects, or requests changes
- Detects duplicate or invalid events

### Administrator
- Manages users, events, submissions, and roles
- Archives or removes stale content
- Reviews platform activity and expired event summaries

## 4. Core Features

### 4.1 Public Event Discovery
- Search events by name, organizer, location, and topic
- Filter by date, event type, format, country, region, and assistance availability
- Sort by date, name, or location
- Default to upcoming events only
- Display assistance availability clearly
- Show event format badges such as in-person, hybrid, and virtual
- Link to official event websites
- Support responsive desktop and mobile layouts

### 4.2 Event Submission Workflow
- Organizer-submitted events enter a pending review queue
- Events move through statuses such as Draft, Pending Review, Changes Requested, Approved, Rejected, Expired, and Archived
- Moderators can approve, reject, or request changes
- Submission decisions are recorded in audit history

### 4.3 Favorites and Reminders
- Registered users can favorite approved events
- Reminders can be configured for one month and/or one week before the event
- Duplicate reminder deliveries must be prevented
- Reminder processing must respect user email preferences and event status

### 4.4 Expired Event Handling
- Approved events whose end date has passed are marked expired or archived
- Expired events are removed from public listings while preserving audit history
- Administrator summary emails are sent for newly expired events

### 4.5 Administration
- Event management and moderation controls
- User and role management
- Audit tracking of status changes and major edits
- Summary reporting for expired events and notification outcomes

## 5. Functional Requirements

### Search and Filtering
- Search must be executed server-side from the backend API
- Supported filters include date range, event type, format, city/state/country, assistance status, and topic tags
- Results should be paginated or loaded incrementally for performance

### Event Metadata
Each event record should contain:
- name
- event type
- description
- start and end datetime
- city, state/region, country
- optional venue
- format
- assistance availability and details
- official website URL
- organizer name and contact email
- technology topics/tags
- approval status
- timestamps for creation and updates

### User Experience
- Public browsing is available without sign-in
- Personalized actions appear only for signed-in users
- Mobile and desktop layouts must remain usable and readable
- Visual indicators must clearly communicate assistance information and event format

### Notification Requirements
- Reminder jobs must be idempotent
- Invalid or canceled events must not trigger reminder emails
- Notification logs should record delivery results and failures

## 6. Non-Functional Requirements

### Performance
- Search and filtering should remain responsive for typical datasets
- Public listings should not require the browser to load the full database

### Reliability
- Background jobs must be safe to retry
- Reminder and expiration actions should avoid duplicate processing
- Event status transitions should be auditable

### Security
- Authentication and authorization must be enforced for protected actions
- Role-based controls must restrict moderator and admin features
- Environment variables and secrets must never be committed to source control

### Maintainability
- Backend and frontend must be modular and logically separated
- Database changes should use migration-based versioning
- The codebase should remain portable across local development and later cloud deployment

## 7. Technical Constraints

- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI
- Database: PostgreSQL
- Local runtime: Docker Compose
- Later deployment target: AWS services including ECS/Fargate, RDS, SES, EventBridge, and CloudWatch

## 8. MVP Scope

The MVP includes:
- searchable and filterable event directory
- public event detail pages or cards
- organizer event submission flow
- moderator approval workflow
- registered-user favorites
- reminder configuration for approved events
- expired event automation
- local Docker-based development environment
- basic admin and audit capability

## 9. Out of Scope for Initial Release
- Full production-scale multi-region deployment
- Advanced analytics dashboard
- Complex automated email template builder
- Full custom billing and payment flows
- Deep AWS infrastructure migration during the initial local-first milestone

## 10. Acceptance Criteria

The project is considered successful when:
1. Users can browse and filter upcoming events from the public site.
2. Organizers can submit events that enter review.
3. Moderators can approve, reject, or request changes.
4. Registered users can save favorite events.
5. Reminder jobs fire only for valid approved events.
6. Expired events are hidden from default listings but retained for admin history.
7. The application runs locally via Docker Compose.
8. The project is documented clearly enough for a development team to continue building it.
