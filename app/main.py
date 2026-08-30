"""FastAPI application: /api/today JSON + minimal Jinja2 dashboard."""

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.integrations.food_db import MEALS, FoodDatabase, get_food_db_service
from app.integrations.hevy import HevyService, get_hevy_service

app = FastAPI(title="mandala-health")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

DAILY_TARGETS = {"energy": 2400.0, "protein": 155.0, "fat": 60.0}


@app.get("/api/today")
def api_today(
    food_db: FoodDatabase = Depends(get_food_db_service),
    hevy: HevyService = Depends(get_hevy_service),
):
    return {
        "nutrition": food_db.day_summary(),
        "last_workout": hevy.last_workout(),
    }


@app.get("/api/foods/search")
def api_foods_search(
    q: str,
    request: Request,
    food_db: FoodDatabase = Depends(get_food_db_service),
):
    results = food_db.search(q)
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="partials/food_results.html",
            context={"results": results},
        )
    return results


class LogEntry(BaseModel):
    food_id: int
    grams: float = Field(gt=0)
    meal: str


@app.post("/api/log")
def api_log(
    entry: LogEntry,
    request: Request,
    food_db: FoodDatabase = Depends(get_food_db_service),
):
    if entry.meal not in MEALS:
        raise HTTPException(status_code=422, detail=f"invalid meal: {entry.meal!r}")
    food_db.log_entry(food_id=entry.food_id, grams=entry.grams, meal=entry.meal)
    nutrition = food_db.day_summary()
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="partials/macros.html",
            context={"nutrition": nutrition, "targets": DAILY_TARGETS},
        )
    return {"nutrition": nutrition}


@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    food_db: FoodDatabase = Depends(get_food_db_service),
    hevy: HevyService = Depends(get_hevy_service),
):
    nutrition = food_db.day_summary()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "nutrition": nutrition,
            "targets": DAILY_TARGETS,
            "last_workout": hevy.last_workout(),
        },
    )
