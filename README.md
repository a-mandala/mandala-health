# Mandala Health

Self-hosted personal health dashboard on urano: nutrition (Cronometer),
training (Hevy), health metrics (Garmin) and medical archive — one integrated
panel, privacy-first, LAN-only.

## Stack

- Python + FastAPI, Jinja2 templates, HTMX + Alpine.js, Tailwind (CDN)
- SQLite for local cache/history
- Integrations: Cronometer (mobile API), Hevy (REST), Garmin (MCP)
- TDD enforced (pytest)

## Status

POC / Milestone 1: daily dashboard (kcal/macros vs targets) + last Hevy workout.

## Run

```bash
uv sync --extra dev
uv run uvicorn app.main:app --port 8020
# open http://localhost:8020
```

Endpoints:

- `GET /api/today` — JSON: `{nutrition: {energy, protein, carbs, fat}, last_workout: {date, exercises}}`
- `GET /` — mobile-first dashboard (kcal vs 2400, proteine vs 155, grassi vs 60, card ultima sessione)

## Tests

```bash
uv run pytest -v
```

All tests are offline: the Cronometer client is injected (fake), Hevy is
mocked with `respx`, and routes use FastAPI dependency overrides.

## Integration choices

- **Cronometer**: we reuse the client installed in `~/cronometer-api-mcp/.venv`
  instead of duplicating it. `app/integrations/cronometer.py` appends that
  venv's `site-packages` (and the editable `src/` layout) to `sys.path` on
  first use, and loads credentials from `~/cronometer-api-mcp/.env`
  (`CRONOMETER_USERNAME` / `CRONOMETER_PASSWORD`). Note: the client's method
  is `get_consumed_nutrients(day)` → `{"macros": {...}}`, which the wrapper
  maps to `{energy, protein, carbs, fat}`.
- **Hevy**: API key read from `HEVY_API_KEY` env var or
  `/home/mandala/.hevy/api_key`; REST `https://api.hevyapp.com/v1/workouts`
  with header `api-key`.
- Services are exposed to FastAPI via `get_cronometer_service()` /
  `get_hevy_service()` dependencies, so tests (or the future HTMX layer) can
  override them cleanly.
