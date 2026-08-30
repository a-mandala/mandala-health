# Mandala Health

[![CI](https://github.com/a-mandala/mandala-health/actions/workflows/ci.yml/badge.svg)](https://github.com/a-mandala/mandala-health/actions/workflows/ci.yml) [![Docker](https://github.com/a-mandala/mandala-health/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/a-mandala/mandala-health/actions/workflows/docker-publish.yml) [![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)

Self-hosted personal health dashboard on urano: nutrition (alimenti da
Open Food Facts + diario locale), training (Hevy), health metrics (Garmin)
and medical archive — one integrated panel, privacy-first, LAN-only.

## Stack

- Python + FastAPI, Jinja2 templates, HTMX + Alpine.js, Tailwind (CDN)
- SQLite for local diary/history (`data/entries.db`)
- Food data: Open Food Facts (unica fonte, nessuna credenziale) — niente food DB locale
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
- `GET /api/foods/search?q=` — ricerca alimenti su Open Food Facts (503 JSON se OFF non raggiungibile)
- `GET /api/foods/barcode/{code}` — prodotto OFF per barcode (404 se inesistente)
- `POST /api/log` — logga una voce del diario (snapshot dell'alimento) in SQLite
- `GET /api/version` — `{version, git_hash, build_date}` (git hash iniettato al build; "dev" in locale)
- `GET /` — mobile-first dashboard (kcal vs 2400, proteine vs 155, grassi vs 60, card ultima sessione, footer con versione)

## Architettura nutrizione

- **Fonte dati unica: Open Food Facts** (`app/integrations/off.py`, `OFFService`):
  search (`cgi/search.pl`) e barcode (`api/v2/product/{code}.json`), normalizzati
  a macro per 100 g (kJ → kcal fallback `/4.184`, prodotti senza nome →
  "Prodotto sconosciuto"), ordinati per completeness. Mai chiamate reali nei
  test (respx).
- **Diario locale** (`app/integrations/entries.py`, `EntryStore`): le voci
  loggate salvano uno snapshot dell'alimento (code, nome, brand, macro per
  100 g) in SQLite `data/entries.db` — il riepilogo del giorno funziona anche
  offline e sopravvive ai rebuild (volume `./data`).
- **Versione visibile**: `ARG GIT_VERSION` nel Dockerfile → `ENV APP_VERSION`,
  passata dal workflow `docker-publish`. Esposta su `/api/version` e nel
  footer della dashboard (`v<hash>`, link a `/api/version`).

## Tests

```bash
uv run pytest -v
```

All tests are offline: Open Food Facts is mocked with `respx`, Hevy is faked,
and routes use FastAPI dependency overrides with a real SQLite entries store
in `tmp_path`.

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

- **Diario locale**: `app/integrations/entries.py` (`EntryStore`) salva le
  voci loggate (snapshot alimento + grammi + pasto) in SQLite `data/entries.db`
  (volume `./data` in Docker — sopravvive ai rebuild). Nessuna credenziale.
- **Alimenti**: `app/integrations/off.py` (`OFFService`) — Open Food Facts è
  l'unica fonte dati; non esiste più un food DB locale né seed.
- **Meals**: la UI/`POST /api/log` usa i nomi `breakfast|lunch|dinner|snacks`,
  validati in `EntryStore.MEALS`.
- **Hevy**: API key read from `HEVY_API_KEY` env var or
  `/home/mandala/.hevy/api_key`; REST `https://api.hevyapp.com/v1/workouts`
  with header `api-key`.
- Services are exposed to FastAPI via `get_off_service()` /
  `get_entry_store()` / `get_hevy_service()` dependencies, so tests (or the
  future HTMX layer) can override them cleanly.
