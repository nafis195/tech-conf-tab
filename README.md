# Technical Conference Table

This project is organized as a local-first full-stack application with a React frontend and a Python FastAPI backend. The initial development setup runs locally with Docker Compose, PostgreSQL, and a simple email/test adapter, while the AWS deployment model is reserved for a later cloud migration phase.

## Project structure

```text
tech-conf-tab/
├── README.md
├── PROJECT_PLAN.md
├── FEATURE_PLAN.md
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── .env.example
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── .env.example
│   └── pytest.ini
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.frontend
│   └── Dockerfile.backend
├── .gitignore
└── .env.example
```

## Tech stack

- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI
- Database: PostgreSQL
- Local orchestration: Docker Compose
- Future cloud migration: AWS ECS/Fargate, RDS, Route 53, and ACM

## Local development

- Start the application with Docker Compose from the project root.
- Use the frontend to access the public event directory and auth flows.
- Use the backend API for event search, moderation, favorites, reminders, and admin actions.
- Run database migrations and tests from the backend folder.

## Notes

The repo is intentionally structured for local-first delivery. Once the MVP is validated locally and the architecture is proven, the same application can be migrated to AWS infrastructure with ECS/Fargate, Route 53, and ACM.
