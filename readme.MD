# Blog Platform

This repository contains a React frontend and a FastAPI backend for a modern blogging platform.

## Phase 1: Foundation

### Prerequisites

- Node.js 24+
- Python 3.10+
- Docker Desktop (optional, for the PostgreSQL service)

### Run locally

1. Start PostgreSQL (when Docker is available): `docker compose up -d db`
2. In `backend`, copy `.env.example` to `.env`, then run:
   - `..\\.venv\\Scripts\\python.exe -m alembic upgrade head`
   - `..\\.venv\\Scripts\\uvicorn.exe app.main:app --reload`
3. In `frontend`, run `npm run dev`.

The API health endpoint is available at `http://localhost:8000/api/v1/health`.

For local schema verification without PostgreSQL, the backend defaults to SQLite when no `.env` file is present.

## Production configuration

- Set `DATABASE_URL` to the managed PostgreSQL connection string.
- Set a unique, high-entropy `SECRET_KEY`; never use the development default.
- Set `CORS_ORIGINS` to the deployed frontend origin.
- Copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_URL` to the deployed API's `/api/v1` URL before building the frontend.
- Run `alembic upgrade head` as part of each backend release.
