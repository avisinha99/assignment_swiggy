# Project Management Platform (Backend)

FastAPI backend starter with **JWT access-token auth**, SQLite (local dev), and Alembic migrations. This repo is intended to grow into a Jira-like project management system (projects/issues/sprints/workflows/websockets/search).

## Prereqs (local)
- Python 3.11+

## Environment
Copy `.env.example` to `.env` and adjust if needed.

## Run locally (SQLite)
1. Install deps and run migrations:

```bash
python -m pip install -r requirements.txt
alembic upgrade head
python scripts/seed.py
```

2. Start API:

```bash
uvicorn app.main:app --reload
```

Open Swagger at `http://localhost:8000/docs`.

## Core APIs (Jira-like)
- **Projects**: `POST /api/projects`, `GET /api/projects`, `GET /api/projects/{project_id}`
- **Issues**: `POST /api/projects/{project_id}/issues`, `PATCH /api/issues/{issue_id}`, `GET /api/projects/{project_id}/board`
- **Workflow**: `POST /api/issues/{issue_id}/transitions`, plus admin config under `/api/projects/{project_id}/workflow/*`
- **Sprints**: `GET/POST /api/projects/{project_id}/sprints`, `POST /api/sprints/{sprint_id}/start`, `POST /api/sprints/{sprint_id}/complete`
- **Comments**: `GET/POST /api/issues/{issue_id}/comments`
- **Watchers**: `POST /api/issues/{issue_id}/watch`, `POST /api/issues/{issue_id}/unwatch`
- **Activity**: `GET /api/projects/{project_id}/activity`
- **Notifications**: `GET /api/notifications`
- **Search**: `GET /api/search?q=...`
- **WebSocket**: `GET /ws?project_id=...&token=...&since_activity_id=...`

## Demo users
Seed script creates these users:
- `admin@demo.com` / `Admin1234!`
- `jane@demo.com` / `Jane1234!`
- `bob@demo.com` / `Bob1234!`

## Authentication
This prototype runs in **no-auth mode** for easier local demo. Endpoints assume the first seeded user is the acting user.\n+Run `python scripts/seed.py` before using the APIs.

## Migrations
Generate a new migration after adding models:

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```
