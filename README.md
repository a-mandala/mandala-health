# Mandala Health

[![CI](https://github.com/a-mandala/mandala-health/actions/workflows/ci.yml/badge.svg)](https://github.com/a-mandala/mandala-health/actions/workflows/ci.yml) [![Docker](https://github.com/a-mandala/mandala-health/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/a-mandala/mandala-health/actions/workflows/docker-publish.yml) [![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)

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

## Installazione servizio (systemd user, su urano)

Il servizio gira come **user service** di systemd: niente sudo, nessun file
in `/etc/systemd`. I file sono pronti in `deploy/`.

1. Da un terminale sul server urano (account di Alessandro), dalla root del repo:

   ```bash
   ./deploy/install-service.sh
   ```

   Lo script copia `deploy/mandala-health.service` in
   `~/.config/systemd/user/`, fa `systemctl --user daemon-reload` e abilita/avvia
   il servizio (uvicorn su `0.0.0.0:8020`).

2. Verifica:

   ```bash
   systemctl --user status mandala-health.service
   journalctl --user -u mandala-health.service -f
   ```

3. Accesso dal telefono (stessa LAN):

   ```text
   http://<ip-urano>:8020
   ```

   (indirizzo IP di urano, es. `192.168.1.x` — `ip addr` per trovarlo).

Limiti noto: un user service si ferma al logout. Per farlo ripartire al boot e
tenerlo vivo senza sessione aperta, eseguire **una volta** (chiede la password):

```bash
loginctl enable-linger $USER
```

Questo passaggio richiede l'account di Alessandro e non può essere automatizzato
senza sudo/polkit.

- **Cronometer**: we reuse the client installed in `~/cronometer-api-mcp/.venv`
  instead of duplicating it. `app/integrations/cronometer.py` appends that
  venv's `site-packages` (and the editable `src/` layout) to `sys.path` on
  first use, and loads credentials from `~/cronometer-api-mcp/.env`
  (`CRONOMETER_USERNAME` / `CRONOMETER_PASSWORD`). Note: the client's method
  is `get_consumed_nutrients(day)` → `{"macros": {...}}`, which the wrapper
  maps to `{energy, protein, carbs, fat}`.
- **Food search (US-1)**: `CronometerService.search_foods()` calls the client's
  `search_food(query)`, then batch-fetches details with `get_foods()` — the
  Cronometer API already stores nutrients **per-100g** in that response, so
  `kcal_per_100g` / `protein_per_100g` need no manual scaling. Cost: one extra
  API call per search, in exchange for macros visible in the UI autocomplete.
- **Meal mapping (US-1)**: the UI/`POST /api/log` uses meal names
  (`breakfast|lunch|dinner|snacks`); the client expects integer
  `diary_group` (1–4), mapped in `CronometerService.MEAL_GROUPS`.
- **Hevy**: API key read from `HEVY_API_KEY` env var or
  `/home/mandala/.hevy/api_key`; REST `https://api.hevyapp.com/v1/workouts`
  with header `api-key`.
- Services are exposed to FastAPI via `get_cronometer_service()` /
  `get_hevy_service()` dependencies, so tests (or the future HTMX layer) can
  override them cleanly.
