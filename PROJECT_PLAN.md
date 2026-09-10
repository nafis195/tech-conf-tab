# Technical Events Discovery Platform

## 1. Product Overview

A single-page website for discovering technical conferences, summits, meetups, workshops, and round tables in one searchable directory.

Visitors can browse approved events without signing in. Registered users can save favorites and receive reminders. Organizers can submit events for moderator approval, while administrators manage the complete platform.

## 2. Goals

- Make technical events easy to discover in one place.
- Provide reliable, structured event information.
- Allow filtering by name, location, date, format, event type, and assistance availability.
- Give organizers a controlled submission workflow.
- Help users track favorite events and receive timely reminders.
- Automatically identify events that have already ended.

## 3. User Roles

### Visitor

- View approved upcoming events.
- Search, filter, sort, and browse event details.
- Open the official event website.
- Create an account.

### Registered User

- All visitor capabilities.
- Save and remove favorite events.
- View a personal favorites list.
- Configure one-month and one-week email reminders.
- Manage email notification preferences.

### Organizer

- Submit a new event.
- View submission status.
- Update a submission when changes are requested.
- Receive approval, rejection, or change-request notifications.

### Moderator

- Review pending submissions.
- Approve, reject, or request changes.
- Edit event information when needed.
- Identify duplicate or inappropriate submissions.

### Administrator

- Full access to users, events, submissions, and settings.
- Add, edit, archive, and delete events.
- Manage moderators and roles.
- Review audit history.
- Receive daily expired-event summaries.

## 4. Event Fields

Each event should support:

- Name
- Event type: conference, summit, meetup, workshop, round table, or other
- Description
- Start date and time
- End date and time
- City
- State or region
- Country
- Optional venue
- Format: in-person, virtual, or hybrid
- Scholarship/assistance: available, unavailable, or unknown
- Scholarship details and application URL
- Official website URL
- Organizer name and contact email
- Technology topics or tags
- Approval status
- Created and updated timestamps

The main table should display the most important fields. Longer descriptions and additional information should appear in an event detail view.

## 5. Public Website Experience

The default page should provide:

- Search by event name, location, topic, and organizer.
- Filters for date range, event type, format, country, region, and assistance availability.
- Sorting by event date, name, and location.
- Upcoming-events view by default.
- Responsive event table on desktop.
- Compact rows or cards on mobile.
- Clear assistance indicators:
  - Green check: assistance available.
  - Red cross: assistance unavailable.
  - Neutral indicator: information unavailable.
- Format badges for virtual, hybrid, and in-person events.
- Direct links to official event websites.
- Pagination or incremental loading for larger datasets.
- Optional save/favorite action for signed-in users.

Search and filtering must be performed by the backend API so the browser does not need to load the entire database.

## 6. Submission and Approval Workflow

1. An organizer signs in and submits event information.
2. The event is stored with `Pending Review` status.
3. Moderators receive a notification.
4. A moderator reviews the event.
5. The moderator approves it, rejects it, or requests changes.
6. Approved events become publicly visible.
7. The organizer receives the decision by email.
8. Every decision and important edit is recorded in an audit history.

Recommended statuses:

- Draft
- Pending Review
- Changes Requested
- Approved
- Rejected
- Expired
- Archived

## 7. Favorites and Reminders

Registered users can favorite approved events and configure reminders per event:

- One month before the event.
- One week before the event.
- Both reminders.

The system must:

- Avoid sending duplicate reminders.
- Respect the user’s email preferences.
- Use the event and user timezone where available.
- Stop reminders for canceled, rejected, expired, or archived events.
- Keep a delivery record for troubleshooting.

## 8. Expired Event Automation

A daily scheduled job should:

1. Find approved events whose end date has passed.
2. Mark them as `Expired` or `Archived`.
3. Remove them from the default public listing.
4. Preserve them for administrative history.
5. Send administrators a summary of newly expired events.

Archiving is preferred over immediate permanent deletion. Permanent deletion should be a separate administrator action or occur only after a configurable retention period.

## 9. Technical Stack and AWS Architecture

### Frontend

- React and TypeScript.
- Responsive, accessible event table and filtering interface.
- Authenticated views for favorites and submissions.
- Build the frontend into a Docker image and serve it with Nginx from Amazon ECS on AWS Fargate.
- Route browser traffic through the same public load-balancing layer as the API, using `/api/*` for the backend and the default route for the frontend.

### Backend

- Python with FastAPI and a REST API.
- Authentication and role-based authorization.
- Event, submission, approval, favorite, and notification services.
- Server-side validation and filtering.
- Package the API as a Docker image and deploy it to Amazon ECS on AWS Fargate.
- Put the frontend and API services behind an internet-facing Application Load Balancer with separate target groups and health checks.

### Authentication and authorization

- Use Amazon Cognito User Pools for registration, email verification, login, and password reset.
- Pass Cognito identity claims to the API and enforce roles in backend authorization checks.
- Store application roles and moderation permissions in PostgreSQL so access can be managed without redeploying the frontend.

### Local development environment

- Use Docker Compose to run the React frontend, Python/FastAPI API, and PostgreSQL locally.
- Keep the frontend and API on separate containers with a documented local `/api` proxy or equivalent configuration.
- Use a local `.env.example` containing safe placeholder values; never commit real credentials.
- Run database migrations and seed data through documented local commands.
- Use a local email development service or console mail adapter so notification flows can be tested without production email delivery.

### Database

- Use Amazon RDS for PostgreSQL for users, events, submissions, favorites, reminders, notifications, and audit records.
- Use private subnets for the database and allow access only from the ECS task security group.
- Enable automated backups, encryption at rest, and a retention policy before production launch.
- Use Alembic migrations and a connection pool in the Python backend.

### Background Jobs

Use EventBridge Scheduler to invoke scheduled ECS Fargate tasks or a protected internal job endpoint for:

- Event expiration.
- One-month and one-week reminders.
- Moderator notifications.
- Daily administrator summaries.
- Notification cleanup and retry processing.

Jobs must be idempotent, record delivery results, and use PostgreSQL transactions to prevent duplicate processing.

### Email

- Use Amazon SES for account verification, password resets, submission updates, approval decisions, reminders, and admin summaries.
- Complete SES domain verification and production access before launch.
- Keep email templates versioned with the backend and record delivery status for troubleshooting.

### Supporting AWS services

- Amazon ECR for versioned backend container images.
- Amazon ECR for versioned frontend container images.
- AWS Secrets Manager for database credentials, application secrets, and SES configuration.
- Amazon CloudWatch for application logs, metrics, alarms, and scheduled-job failures.
- AWS WAF on the load balancer entry point where appropriate for common web protections and rate limiting.
- Amazon Route 53 for the domain and DNS records when the domain is ready.
- AWS Certificate Manager for TLS certificates in the later HTTPS phase.
- AWS IAM with least-privilege roles for deployment, ECS tasks, scheduled jobs, and CI/CD.

### DNS, IP, and TLS rollout

- Start with the load balancer DNS name for testing or use a temporary host name.
- When the production domain is available, create Route 53 alias records that point to the load balancer; do not hardcode an Application Load Balancer IP because AWS can change it.
- Request and validate an ACM certificate for the domain, then add an HTTPS listener and redirect HTTP to HTTPS.
- If a fixed public IP is a strict requirement, place a Network Load Balancer with Elastic IPs in front of the application routing layer and document the additional cost and operational complexity.

### Environments and delivery

- Maintain separate development, staging, and production environments.
- Use infrastructure as code, preferably AWS CDK or Terraform, for repeatable environments.
- Use GitHub Actions or another CI/CD service to run tests, build frontend and API images, publish both images to ECR, and deploy approved changes to ECS.
- Store frontend API URLs and other public configuration as environment-specific build settings; keep secrets out of frontend bundles.

## 10. Initial Data Model

Core tables:

- `users`
- `roles`
- `events`
- `event_submissions`
- `favorites`
- `reminder_preferences`
- `tags`
- `event_tags`
- `notifications`
- `approval_history`
- `audit_logs`

The database schema should include an external-auth identity mapping. In local development this can use a simple local authentication adapter; after migration it will map Amazon Cognito user IDs to application user records.

Important constraints:

- An event end date cannot be before its start date.
- Only approved events are publicly visible.
- A user can favorite an event only once.
- Reminder jobs must be idempotent.
- Event and user deletion behavior must be defined before production launch.

## 11. Initial API Surface

- `GET /events`
- `GET /events/:id`
- `POST /events`
- `PATCH /events/:id`
- `DELETE /events/:id`
- `GET /submissions`
- `POST /events/:id/approve`
- `POST /events/:id/reject`
- `POST /events/:id/request-changes`
- `POST /events/:id/favorite`
- `DELETE /events/:id/favorite`
- `GET /me/favorites`
- `PUT /me/reminder-preferences`
- `GET /admin/users`
- `GET /admin/audit-logs`

All protected operations must enforce permissions on the backend.

## 12. MVP Scope

The first release should include:

- Public event directory.
- Database-backed events.
- Search, filtering, sorting, and pagination.
- Event detail view.
- User registration and login.
- Organizer event submission.
- Moderator approval workflow.
- Administrator event management.
- Favorites.
- One-month and one-week email reminders.
- Daily expired-event processing.
- Basic audit logging.

Defer until after the MVP:

- Calendar integrations and calendar export.
- Social login.
- Event recommendations.
- Organizer analytics.
- Automatic duplicate detection.
- Ratings, reviews, or public comments.
- Multi-language support.

## 13. Security and Quality Requirements

- Hash passwords using a trusted authentication solution.
- Enforce authorization on every protected API endpoint.
- Validate and sanitize all submitted text and URLs.
- Rate-limit authentication and submission endpoints.
- Add email verification and password reset flows.
- Protect against spam with rate limiting or CAPTCHA where appropriate.
- Record administrative actions in an audit log.
- Use soft deletion or archiving for important records.
- Support keyboard navigation and screen readers.
- Test reminder jobs for duplicate delivery and timezone behavior.
- Add automated tests for event visibility and approval permissions.

## 14. Product Decisions Needed

Before implementation, decide:

1. Can anyone submit an event, or only verified organizers?
2. Is organizer registration different from normal user registration?
3. Should expired events always be archived instead of deleted?
4. Should assistance status include an `Unknown` option?
5. Which countries or regions should be supported initially?
6. Which transactional email provider will be used?
7. Should users select a timezone manually?
8. Can moderators edit approved events directly?
9. How long should rejected and expired events be retained?
10. Which technology tags should be available at launch?

## 15. Delivery Phases

### Phase 1: Foundation

- Confirm product decisions.
- Define the database schema and API contracts.
- Set up the React, Python, PostgreSQL, and Docker development environments.
- Add Docker Compose for the local frontend, API, and PostgreSQL services.
- Add local authentication and email adapters that preserve the production service interfaces.
- Add migrations, seed data, automated tests, linting, and local development documentation.

### Phase 2: Public Discovery

- Build the event listing page.
- Add search, filters, sorting, pagination, and event details.
- Add responsive and accessible layouts.

### Phase 3: Accounts and Management

- Add registration, login, and role-based access.
- Add organizer submissions.
- Add moderator review and approval.
- Add administrator event and user management.

### Phase 4: Personalization and Notifications

- Add favorites.
- Add reminder preferences.
- Implement email templates and reminder processing.

### Phase 5: Automation and Hardening

- Add daily expiration processing.
- Add administrator summaries and audit logs.
- Test security, accessibility, performance, and end-to-end workflows.
- Prepare deployment, monitoring, backups, and operational documentation.
- Complete local MVP acceptance testing and production-readiness review.

The detailed feature sequence and acceptance criteria are tracked in `FEATURE_PLAN.md`.

## 16. Later Cloud Migration: AWS Deployment and Operations Checklist

- Begin this phase only after the local MVP workflows pass their acceptance criteria.
- Confirm the AWS account, region, domain, environment strategy, and estimated operating cost.
- Create separate AWS environments with least-privilege IAM roles.
- Configure VPC networking, private RDS subnets, ECS security groups, and public load balancer access.
- Configure Cognito, SES domain verification, Secrets Manager, ECR, Route 53, and the ECS load balancer.
- Deploy separate frontend and API ECS/Fargate services with independent health checks and scaling settings.
- Run database migrations as a controlled deployment step before serving new API code.
- Add health checks for the API, CloudWatch alarms for errors and task health, and alerts for failed scheduled jobs.
- Enable RDS backups and define restore and disaster-recovery procedures.
- Add the Route 53 alias record when the production domain is ready.
- Add the ACM certificate, HTTPS listener, and HTTP-to-HTTPS redirect in the later TLS rollout.
- Document rollback procedures for frontend, API container, database migration, and scheduled-job changes.

## 17. Definition of Done for MVP

The MVP is ready when:

- A visitor can find approved events using search and filters.
- An organizer can submit an event.
- A moderator can approve, reject, or request changes.
- An administrator can manage all events and users.
- A registered user can favorite an event.
- Reminder emails are sent at the configured times without duplicates.
- Events ending before the current date are automatically removed from the default listing.
- Unauthorized users cannot access moderator or administrator actions.
- Core workflows have automated test coverage.
