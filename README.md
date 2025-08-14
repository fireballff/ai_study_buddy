# AI Study Buddy

This repository contains a cross‑platform desktop app (Windows and macOS) built with Python 3.13+ and PyQt6.  
The app helps students organize tasks, plan study sessions, and schedule their calendar automatically using AI‑driven features.  

## Features

- **Light/Dark Theme** — Apple‑style minimal design with dynamic switching.  
- **Tasks & Events** — Import events (stubbed) and create tasks, with type classification.  
- **Smart Planning** — Simple planner places tasks around calendar events; future milestones could integrate DeepSeek AI for more advanced reasoning.  
- **Smart Calendar** — Weekly view grid that shows tasks and events; supports quick add dialog.  
- **ADHD Mode** — Focus timer with Pomodoro presets and a simplified “one thing now” panel.  

## Development

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. Copy `.env.sample` to `.env` and modify values if connecting to Supabase/Google.

   The app reads the following Supabase settings:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SQLITE_PATH` (optional override for the local cache)

   Additional feature flags are available via environment variables or `.env`:
   `ENABLE_ADHD_MODE`, `ENABLE_MICRO_COACHING`, `ENABLE_LIVE_RESCHEDULE`.

3. Run the application:
   ```bash
   python scripts/dev_run.py
   ```

4. Run tests with pytest:
   ```bash
   pytest -q
   ```

5. Build a standalone executable (PyInstaller):
   ```bash
   pyinstaller packaging/pyinstaller.spec
   ```

## Project Structure

```
ai_study_buddy/
├── project/            # core configuration, DB, logging
├── integrations/       # Supabase auth and Google Calendar stubs
├── agents/            # AI agents: planner, breakdown, adaptive learning
├── llm/               # LLM integration (stubbed for DeepSeek)
├── utils/             # helpers (error handling)
├── ui/                # PyQt6 user interface components and pages
├── scripts/           # entry points for development
├── migrations/        # database migrations via Alembic
├── packaging/         # PyInstaller spec
├── tests/             # pytest unit tests
├── requirements.txt   # dependencies
└── .env.sample        # sample environment configuration
```

## Supabase Edge Functions

This project uses Supabase Edge Functions written in Deno. Environment variables must be provided when deploying via the Supabase CLI.

### google_oauth_exchange

Exchanges a Google OAuth authorization code for tokens and securely stores the refresh token on the server.

Set the following variables for the function:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `SYM_ENCRYPTION_KEY`

Example invocation after deploying the function:

```bash
curl -X POST https://<project-ref>.functions.supabase.co/google_oauth_exchange \
  -H "Authorization: Bearer <supabase_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"code":"<oauth-code>","code_verifier":"<verifier>","redirect_uri":"http://localhost:8765/callback"}'
```

A successful call returns `{ "ok": true }`.
