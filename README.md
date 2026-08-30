# Mandala Health

[![CI](https://github.com/a-mandala/mandala-health/actions/workflows/ci.yml/badge.svg)](https://github.com/a-mandala/mandala-health/actions/workflows/ci.yml) [![Docker](https://github.com/a-mandala/mandala-health/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/a-mandala/mandala-health/actions/workflows/docker-publish.yml) [![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)

Self-hosted personal health dashboard on urano: nutrition (food database locale SQLite),
training (Hevy), health metrics (Garmin) and medical archive — one integrated
panel, privacy-first, LAN-only.

## Stack

- Python + FastAPI, Jinja2 templates, HTMX + Alpine.js, Tailwind (CDN)
- SQLite for local cache/history
- Food database: locale, SQLite (`data/foods.db`), nessuna credenziale necessaria
- Integrations: Hevy (REST), Garmin (MCP)
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

All tests are offline: the food database runs on SQLite in `tmp_path`, Hevy is
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

- **Food database locale**: `app/integrations/food_db.py` (`FoodDatabase`) gestisce
  alimenti (macro per 100 g) e voci del diario in SQLite `data/foods.db`
  (volume `./data` in Docker — sopravvive ai rebuild). Nessuna credenziale,
  funziona offline.
- **Seed**: `python -m app.seed_foods` carica i 30 alimenti comuni da
  `data/seed_foods.json` (idempotente: salta i nomi già presenti).
- **Meals**: la UI/`POST /api/log` usa i nomi `breakfast|lunch|dinner|snacks`,
  validati in `FoodDatabase.MEALS`.
- **Hevy**: API key read from `HEVY_API_KEY` env var or
  `/home/mandala/.hevy/api_key`; REST `https://api.hevyapp.com/v1/workouts`
  with header `api-key`.
- Services are exposed to FastAPI via `get_food_db_service()` /
  `get_hevy_service()` dependencies, so tests (or the future HTMX layer) can
  override them cleanly.
