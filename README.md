# MeetMate AI

**Every meeting. Clear decisions. Actionable next steps.**

MeetMate AI is a local-first meeting-to-action assistant. Add a transcript, receive a structured summary, confirmed decisions, action items, supporting evidence, and focused clarification questions. Review and update records in a persistent SQLite database.

## Features

- Dashboard backed by persisted meetings, tasks, deadlines, and clarifications.
- Transcript entry or UTF-8 `.txt` upload, with server-side size and file validation.
- Groq analysis through the OpenAI-compatible API, strict Pydantic validation, and clear provider errors. No automatic switch to Demo Mode after a failed live request.
- Explicit Demo Mode through `DEMO_MODE=true`. With live mode selected, a missing or rejected Groq key produces a clear error and never falls back to the heuristic.
- Meeting history, title search, detail editing, evidence review, transcript review, and Markdown export.
- Action tracking with owner/deadline/priority/status edits, filters, and overdue handling.
- Clarification inbox. Responses update owner or ISO deadline when specific; vague responses remain open.
- SQLite persistence, cascade deletion, responsive layout, accessible form labels, loading/error/empty states.

## Stack and architecture

React + Vite + JavaScript frontend (`client/`); FastAPI + Pydantic + SQLAlchemy backend (`server/app/`); local SQLite database. The browser calls `http://localhost:8000`; the backend keeps Groq credentials private. FastAPI docs are at `/docs`. The verified local environment uses Python 3.12.10 in `.venv312`.

## Folder structure

- `client/src/App.jsx` — app routes and workflow screens
- `client/src/services/api.js` — API and download helpers
- `client/src/index.css` — responsive design system
- `server/app/main.py` — REST endpoints, AI integration, transaction handling
- `server/app/models.py` — SQLite entities and relationships
- `server/app/schemas.py` — request and AI-output validation
- `server/app/config.py` — environment configuration
- `server/tests/` — automated API tests

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer and npm
- Groq API key in `server/.env` for live analysis

## Setup on Windows PowerShell

From the project root, open two terminals.

### Backend

```powershell
cd .\server
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install --upgrade pip
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt
# server/.env is created with blank placeholders; set GROQ_API_KEY there and leave DEMO_MODE=false.
.\.venv312\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

No activation or PowerShell policy change is needed when using these commands. Keep `.env` private; it is ignored by Git. `GROQ_MODEL` selects the model and `DATABASE_URL` selects storage. `FRONTEND_ORIGIN` accepts a comma-separated list and defaults to `http://localhost:5173`, `http://localhost:5174`, and `http://127.0.0.1:5174`.

### Frontend

```powershell
cd .\client
npm install
Copy-Item .env.example .env
npm run dev
```

Open <http://localhost:5174>. API documentation: <http://localhost:8000/docs>. Health: <http://localhost:8000/api/health>. Vite uses port 5174 so it can run alongside the other local app already using 5173.

The Vite client uses `VITE_API_URL` (default `http://localhost:8000`) and serves on port 5174. Update that value only if you run the backend on another port. Restart Vite after changing the environment file.

## Demo Mode

Set `DEMO_MODE=true` to use a deterministic local extractive heuristic. It tags every meeting as a demo and must not be treated as a real AI analysis. With the default `DEMO_MODE=false`, an empty key reports `AI Unavailable`; a configured key is checked with Groq before the transcript is submitted for analysis.

## Tests and build

```powershell
cd .\server
.\.venv312\Scripts\python.exe -m pip install pytest httpx
.\.venv312\Scripts\python.exe -m pytest

cd ..\client
npm run build
```

Tests cover explicit Demo Mode, missing/invalid keys, and mocked live AI responses/failures; no Groq credentials or provider network calls are needed.

## Troubleshooting

- **Frontend cannot connect:** confirm the API is running on port 8000 and `VITE_API_URL` matches. Check `/api/health` and backend CORS `FRONTEND_ORIGIN` includes `http://localhost:5174`.
- **Python version mismatch:** use the explicit Python 3.12 executable shown in the setup commands.
- **AI Unavailable shown:** set `GROQ_API_KEY` in `server/.env`, restart FastAPI, and check `/api/config/status`. The backend verifies the key with Groq before analysis.
- **Groq errors:** verify the key, model availability, and provider rate limits. The key never goes to the browser.
- **Database location:** default `server/meetmate.db`, retained across backend restarts. Back it up before manually removing it.
- **Upload rejected:** only UTF-8 `.txt` files up to the configured transcript character limit are accepted.

## Current limitations and future enhancements

This local prototype has no user accounts, access control, deployment setup, or background job queue. Demo Mode uses simple extraction and date answers require ISO `YYYY-MM-DD`; richer clarification editing, collaboration, calendar sync, audit history, and retries for transient AI failures are possible next steps.





