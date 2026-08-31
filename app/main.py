"""FastAPI application: dashboard + JSON API.

Foods come from Open Food Facts (OFF); logged entries are persisted locally
in SQLite (data/entries.db) so the diary survives restarts and the day
summary works offline.
"""

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.integrations.entries import MEALS, EntryStore, get_entry_store
from app.integrations.hevy import HevyService, get_hevy_service
from app.integrations.off import OFFError, OFFNotFoundError, OFFService, get_off_service
from app.version import version_info

app = FastAPI(title="mandala-health")

app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

DAILY_TARGETS = {"energy": 2400.0, "protein": 155.0, "fat": 60.0}


@app.get("/api/today")
def api_today(
    entry_store: EntryStore = Depends(get_entry_store),
    hevy: HevyService = Depends(get_hevy_service),
):
    return {
        "nutrition": entry_store.day_summary(),
        "last_workout": hevy.last_workout(),
    }


@app.get("/api/version")
def api_version():
    return version_info()


@app.get("/api/foods/search")
def api_foods_search(
    q: str,
    request: Request,
    off: OFFService = Depends(get_off_service),
):
    try:
        results = off.search(q)
    except OFFError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="partials/food_results.html",
            context={"results": results},
        )
    return results


@app.get("/api/foods/barcode/{code}")
def api_food_barcode(
    code: str,
    request: Request,
    off: OFFService = Depends(get_off_service),
):
    try:
        product = off.get_by_barcode(code)
    except OFFNotFoundError as exc:
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                request=request,
                name="partials/barcode_error.html",
                context={"message": f"Nessun prodotto trovato per il codice {code}"},
            )
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OFFError as exc:
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                request=request,
                name="partials/barcode_error.html",
                context={"message": f"Errore Open Food Facts: {exc}"},
            )
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="partials/barcode_result.html",
            context={"product": product},
        )
    return product


@app.get("/scan")
def scan_page(
    request: Request,
    code: str = "",
    off: OFFService = Depends(get_off_service),
):
    """Deep-link page for the phone's native barcode scanner (no camera permission)."""
    product = None
    error = None
    if code.strip():
        try:
            product = off.get_by_barcode(code.strip())
        except OFFNotFoundError:
            error = f"Nessun prodotto trovato per il codice {code}"
        except OFFError as exc:
            error = f"Errore Open Food Facts: {exc}"
    return templates.TemplateResponse(
        request=request,
        name="scan.html",
        context={"product": product, "error": error},
    )


class LogEntry(BaseModel):
    food_id: str
    name: str
    brand: str | None = None
    kcal_per_100g: float
    protein_per_100g: float = 0.0
    carbs_per_100g: float = 0.0
    fat_per_100g: float = 0.0
    grams: float = Field(gt=0)
    meal: str


@app.post("/api/log")
def api_log(
    entry: LogEntry,
    request: Request,
    store: EntryStore = Depends(get_entry_store),
):
    if entry.meal not in MEALS:
        raise HTTPException(status_code=422, detail=f"invalid meal: {entry.meal!r}")
    store.log_entry(
        food_code=entry.food_id,
        name=entry.name,
        brand=entry.brand,
        kcal_per_100g=entry.kcal_per_100g,
        protein_per_100g=entry.protein_per_100g,
        carbs_per_100g=entry.carbs_per_100g,
        fat_per_100g=entry.fat_per_100g,
        grams=entry.grams,
        meal=entry.meal,
    )
    nutrition = store.day_summary()
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
    store: EntryStore = Depends(get_entry_store),
    hevy: HevyService = Depends(get_hevy_service),
):
    nutrition = store.day_summary()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "nutrition": nutrition,
            "targets": DAILY_TARGETS,
            "last_workout": hevy.last_workout(),
            "app_version": version_info(),
        },
    )
