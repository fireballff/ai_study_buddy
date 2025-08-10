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
