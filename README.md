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

POC / planning. Milestone 1: daily dashboard (kcal/macros vs targets) + quick food log.
