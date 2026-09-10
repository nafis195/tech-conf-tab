# Technical Conference Table Feature Plan

This document breaks the MVP into implementable features. Each feature should be delivered with backend tests, frontend tests where applicable, API documentation, and accessibility checks for user-facing flows.

## Delivery Order

1. Local platform foundation
2. Event data model and public discovery
3. Accounts and access control
4. Organizer submissions and moderation
5. Favorites and reminders
6. Expiration automation and administration
7. Local MVP validation and hardening
8. AWS cloud migration and production release

## 1. Platform Foundation

### Scope

- Create the React/TypeScript frontend and Python/FastAPI backend.
- Configure PostgreSQL locally using Docker Compose.
- Add Dockerfiles for the frontend and API, environment configuration, linting, formatting, and automated tests.
- Define API error responses, pagination, validation rules, and timezone handling.
- Add local authentication and email adapters with interfaces that can later be backed by Cognito and SES.
- Document local setup, migrations, seed data, and test commands.

### User stories

- As a developer, I can run the frontend, API, and PostgreSQL locally with one command so I can build and test the app before cloud deployment.
- As a developer, I can apply and rollback database migrations so schema changes are safe and repeatable.
- As a developer, I can use local seed data and email stubs to test the core workflows without external service dependencies.
- As a contributor, I can follow the setup guide in the repository so onboarding is predictable and consistent.

### Acceptance criteria

- A developer can start the frontend, API, and PostgreSQL locally with documented commands.
- CI runs frontend checks, backend checks, and database-backed tests.
- A new developer can reproduce the local environment from the repository and `.env.example`.
- Local authentication and email flows can be tested without AWS credentials or production email delivery.
- Database migrations and seed data can be applied and reset through documented commands.
- Secrets are loaded from local environment configuration and never committed.

## 2. Event Data and Public Discovery

### Scope

- Create the event, tag, and event-tag tables with migrations.
- Add event creation and editing services with date, URL, and required-field validation.
- Implement `GET /events` with search, filters, sorting, pagination, and upcoming-event defaults.
- Implement `GET /events/:id` for event details.
- Build the responsive event table, mobile cards, filter controls, sort controls, and detail view.
- Show event type, format, assistance status, date, location, tags, and official website links.

### User stories

- As a visitor, I can browse a list of upcoming approved events so I can discover relevant conferences quickly.
- As a visitor, I can search by keyword and filter by date, type, location, and format so I can narrow the results to my needs.
- As a visitor, I can click an event to view details such as dates, organizer, venue, tags, and official links.
- As a user on mobile, I can still browse and filter events using a responsive layout that remains usable.

### Acceptance criteria

- Visitors see only approved, non-expired, non-archived events in the default listing.
- Search and filters execute through the API rather than loading the full dataset into the browser.
- Invalid dates, URLs, and date ranges are rejected with useful errors.
- The listing works with keyboard navigation, screen readers, loading states, empty states, and API errors.

## 3. Accounts and Access Control

### Scope

- Configure Cognito User Pools and application user records.
- Add registration, email verification, login, logout, password reset, and session handling.
- Add backend authentication middleware and role checks for visitor, organizer, moderator, and administrator roles.
- Add account and notification-preference screens.

### User stories

- As a new user, I can register and verify my account so I can access personalized features.
- As a returning user, I can log in and recover my password so I can access my saved preferences securely.
- As a visitor, I can browse public pages without authentication while protected actions remain blocked from unauthenticated access.
- As an organizer, moderator, or administrator, I receive the correct permissions for my role so I can access only the actions intended for me.

### Acceptance criteria

- A new user cannot use protected features until authentication requirements are satisfied.
- Backend authorization rejects requests based on missing or insufficient roles, regardless of frontend state.
- Users can update their notification preferences and timezone.
- Passwords and authentication tokens are handled only by the trusted authentication solution.

## 4. Organizer Submissions

### Scope

- Add submission creation, editing, status display, and change-request handling.
- Reuse event validation while keeping drafts and pending submissions private.
- Add organizer screens for creating a submission and viewing its history.
- Add notifications for submitted, change-requested, approved, and rejected submissions.

### User stories

- As an organizer, I can submit an event with all required fields so it can go through review.
- As an organizer, I can save a draft and continue editing before submitting for approval.
- As an organizer, I can view my submission status and recent moderator notes so I know what to update.
- As an organizer, I can revise a submission after a change request so my event can move forward.

### Acceptance criteria

- An organizer can save or submit a complete event proposal.
- A submitted proposal is stored as `Pending Review` and is not publicly visible.
- Organizers can edit a proposal after `Changes Requested`.
- Organizers can see the current status and moderator feedback.

## 5. Moderation Workflow

### Scope

- Add moderator queue with filtering by status and submission date.
- Add review view with duplicate and content checks.
- Implement approve, reject, and request-changes actions.
- Store approval history and moderator feedback.
- Send the organizer the decision notification through SES.

### User stories

- As a moderator, I can view a queue of pending submissions so I can review them efficiently.
- As a moderator, I can approve, reject, or request changes on a submission so the event lifecycle stays controlled.
- As a moderator, I can record a reason for my decision so organizers understand what needs to change.
- As an administrator, I can review approval history and audit records to monitor moderation actions.

### Acceptance criteria

- Only moderators and administrators can review or decide submissions.
- Approval creates or updates a public event while preserving the submission history.
- Rejection and change requests include a reason.
- Every decision records actor, timestamp, prior status, new status, and notes.

## 6. Favorites and Reminder Preferences

### Scope

- Add favorite and unfavorite API operations and the user favorites view.
- Add per-event one-month and one-week reminder preferences.
- Add user-level email opt-in and timezone settings.
- Add reminder delivery records and duplicate-prevention keys.

### User stories

- As a registered user, I can save events I like so I can revisit them later.
- As a registered user, I can configure one-month and one-week reminders so I receive notifications before events I care about.
- As a user, I can manage my reminder preferences and email settings so notifications match my preferences.
- As a system operator, I need reminder jobs to be idempotent so duplicate emails are not sent.

### Acceptance criteria

- A user can favorite an approved event only once and can remove it later.
- Favorite actions are unavailable or clearly prompted for unauthenticated visitors.
- Users can choose either reminder, both, or neither.
- A reminder is sent at most once for each user, event, and reminder window.
- Canceled, expired, rejected, and archived events do not generate reminders.

## 7. Expiration and Administration

### Scope

- Add the daily expiration job using EventBridge Scheduler and an ECS task or internal job endpoint.
- Mark ended approved events as `Expired` or `Archived` without destroying history.
- Add administrator event, user, role, and retention controls.
- Add daily expired-event summaries and notification retry handling.
- Add audit log views and exportable administrative history where needed.

### Acceptance criteria

- Events are removed from the default public listing after their end date.
- The expiration job is safe to retry and produces no duplicate state changes or notifications.
- Administrators can manage events and users, but destructive actions require explicit confirmation.
- Administrative actions are recorded with actor, target, action, timestamp, and relevant change details.

## 7. Local MVP Validation and Hardening

### Scope

- Add API rate limits for authentication, submissions, and public search.
- Configure local CORS, security headers, secure cookie/token handling, and development logging.
- Run automated security, accessibility, performance, and end-to-end tests.
- Verify all MVP workflows against a clean local database and seeded test data.

### User stories

- As a QA tester, I can run the local regression suite so I can validate the platform before cloud deployment.
- As a developer, I can verify API authorization and security controls so protected endpoints stay protected.
- As an operator, I can run scheduled jobs and confirm they are idempotent and safe to retry.
- As a project owner, I can confirm the MVP works end-to-end from a clean checkout before starting the AWS migration.

### Acceptance criteria

- No secret is present in source control or the frontend bundle.
- Protected endpoints, database access, and scheduled jobs are covered by authorization tests.
- The complete MVP can be demonstrated locally from a clean checkout.
- Local scheduled jobs and email notifications are repeatable and idempotent.
- The MVP passes the definition of done in `PROJECT_PLAN.md`.

## 8. AWS Cloud Migration and Production Release

### Scope

- Provision ECR, ECS/Fargate services, target groups, and an internet-facing load balancer with infrastructure as code.
- Move PostgreSQL to Amazon RDS and migrate data using a tested backup and restore procedure.
- Replace local authentication and email adapters with Cognito and SES integrations.
- Add Secrets Manager, CloudWatch logs and alarms, IAM roles, and scheduled ECS jobs.
- Add Route 53 alias records when the production domain is ready.
- Request and validate an ACM certificate, add the HTTPS load balancer listener, and redirect HTTP to HTTPS.
- Document deployment, rollback, migration, backup, and disaster-recovery procedures.

### User stories

- As a platform engineer, I can package the frontend and API into Docker images so they can be pushed to ECR and deployed consistently.
- As a DevOps engineer, I can deploy the application to ECS/Fargate and validate the load-balancer routing and service health checks.
- As a systems operator, I can configure Route 53 and ACM so the production domain resolves securely over HTTPS.
- As a project owner, I can perform rollback and restore procedures to recover from deployment issues without data loss.

### Acceptance criteria

- Frontend and API images build, publish to ECR, and deploy independently to ECS/Fargate.
- The frontend and API are reachable through the ECS load balancer, and `/api/*` routes to the API service.
- Production secrets are stored in Secrets Manager and are absent from images and source control.
- Operators can identify API errors, unhealthy ECS tasks, failed email jobs, and failed scheduled jobs.
- The production domain resolves through Route 53 and passes HTTPS certificate validation after the TLS rollout.
- A documented rollback and database restore procedure has been tested in staging.

## Post-MVP Features

- Calendar integrations and calendar export.
- Social login.
- Event recommendations.
- Organizer analytics.
- Automatic duplicate detection.
- Ratings, reviews, or public comments.
- Multi-language support.