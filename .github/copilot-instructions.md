# Copilot Instructions for Task Planner Agent

## Project Overview
- **Purpose:** AI-powered task planning app that turns natural language goals into structured, actionable plans, enriched with web search and weather data.
- **Core Stack:** FastAPI (API server), SQLAlchemy (ORM), SQLite (default DB), Jinja2 (templates), Google Gemini 2.5 Pro (AI), Tavily API (web search), OpenWeatherMap (weather).

## Architecture & Key Files
- `main.py`: FastAPI app, API endpoints, web server, and route definitions.
- `agent.py`: Core planning agent logic, Gemini API integration, plan orchestration.
- `models.py`: SQLAlchemy models for plans and DB operations.
- `tools.py`: Integrations for Tavily (web search) and OpenWeatherMap (weather).
- `templates/index.html`: Jinja2 template for the web UI.
- `exceptions.py`, `validators.py`: Error handling and input validation.
- `logging_config.py`: Centralized logging setup.

## Developer Workflows
- **Run locally:** `python main.py` (or `uvicorn main:app --reload` for dev hot-reload)
- **Test:** Use `run_tests.bat`, `run_tests.ps1`, or run test files directly (e.g., `python test_api.py`).
- **Reset DB:** Delete `task_planner.db` and restart app.
- **API docs:** Visit `/docs` when server is running.
- **Production:** Use Gunicorn (`gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker`) for Railway deployment

## Project Conventions
- **Error Handling:** All API responses use a `{ success, message, ... }` or `{ success, error, message }` pattern. See `ERROR_HANDLING_SUMMARY.md` for details.
- **Environment:** Secrets/API keys in `.env` (see README for required keys).
- **Database:** Auto-creates on startup; no migrations needed for basic use.
- **External APIs:** All third-party calls are wrapped in `tools.py` for isolation and error handling.
- **Frontend:** Minimal, server-rendered via Jinja2; no SPA or client-side routing.

## Patterns & Examples
- **Adding an API route:** Edit `main.py`, use FastAPI's `@app.get`/`@app.post` decorators.
- **Adding a new tool/integration:** Add to `tools.py`, expose via agent logic in `agent.py`.
- **Modifying DB schema:** Update `models.py`, delete `task_planner.db` to reset.
- **Logging:** Use the logger from `logging_config.py` for all non-trivial events/errors.

## Integration Points
- **Gemini API:** Used in `agent.py` for plan generation.
- **Tavily API:** Used in `tools.py` for web search enrichment.
- **OpenWeatherMap:** Used in `tools.py` for weather data.

## Notable Differences from Common Patterns
- No migrations: DB is reset by deleting the file.
- All external API logic is isolated in `tools.py` (not mixed in route handlers).
- Error handling is centralized and consistent across all endpoints.

## References
- See `README.md` for setup, deployment, and API usage details.
- See `ERROR_HANDLING_SUMMARY.md` for error/exception conventions.
- See `test_*.py` files for usage/testing patterns.

---

**Edit this file to keep Copilot and other AI agents productive!**
