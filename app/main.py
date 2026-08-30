"""FastAPI application: /api/today JSON + minimal Jinja2 dashboard."""

from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.integrations.cronometer import CronometerService, get_cronometer_service
from app.integrations.hevy import HevyService, get_hevy_service

app = FastAPI(title="mandala-health")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

DAILY_TARGETS = {"energy": 2400.0, "protein": 155.0, "fat": 60.0}


@app.get("/api/today")
def api_today(
    cronometer: CronometerService = Depends(get_cronometer_service),
    hevy: HevyService = Depends(get_hevy_service),
):
    return {
        "nutrition": cronometer.get_day_summary(),
        "last_workout": hevy.last_workout(),
    }


@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    cronometer: CronometerService = Depends(get_cronometer_service),
    hevy: HevyService = Depends(get_hevy_service),
):
    nutrition = cronometer.get_day_summary()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "nutrition": nutrition,
            "targets": DAILY_TARGETS,
            "last_workout": hevy.last_workout(),
        },
    )
