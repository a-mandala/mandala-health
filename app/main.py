"""FastAPI application: /api/today JSON + minimal Jinja2 dashboard."""

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

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


@app.get("/api/foods/search")
def api_foods_search(
    q: str,
    cronometer: CronometerService = Depends(get_cronometer_service),
):
    return cronometer.search_foods(q)


class LogEntry(BaseModel):
    food_id: int
    measure_id: int
    grams: float = Field(gt=0)
    meal: str


@app.post("/api/log")
def api_log(
    entry: LogEntry,
    cronometer: CronometerService = Depends(get_cronometer_service),
):
    if entry.meal not in CronometerService.MEAL_GROUPS:
        raise HTTPException(status_code=422, detail=f"invalid meal: {entry.meal!r}")
    cronometer.add_food_entry(
        food_id=entry.food_id,
        measure_id=entry.measure_id,
        grams=entry.grams,
        meal=entry.meal,
    )
    return {"nutrition": cronometer.get_day_summary()}


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
