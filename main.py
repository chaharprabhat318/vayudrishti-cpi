"""
VayuDrishti (??????????) - Enterprise MoSPI Backend Application
Ministry of Statistics and Programme Implementation (MoSPI), Government of India
"""
import os
import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import STATIC_DIR
from app.engine.database import init_database, seed_database_if_empty
from app.scrapers.orchestrator import IngestionOrchestrator, auto_scraper_config

from app.api.indices_api import router as indices_router
from app.api.routes_api import router as routes_router
from app.api.hedonic_api import router as hedonic_router
from app.api.cpi_api import router as cpi_router
from app.api.simulation_api import router as simulation_router
from app.api.scrapers_api import router as scrapers_router
from app.api.export_api import router as export_router

app = FastAPI(
    title="VayuDrishti (??????????) - Real-time Airfare Price Index & CPI Platform",
    description="Enterprise statistical platform developed for MoSPI, Government of India (SIH26056)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(indices_router, prefix="/api")
app.include_router(routes_router, prefix="/api")
app.include_router(hedonic_router, prefix="/api")
app.include_router(cpi_router, prefix="/api")
app.include_router(simulation_router, prefix="/api")
app.include_router(scrapers_router, prefix="/api")
app.include_router(export_router, prefix="/api")

# Explicit Root Route: Guarantees index.html is ALWAYS served without 404
@app.get("/")
async def serve_root_page():
    root_dir = Path(__file__).resolve().parent
    possible_index_paths = [
        STATIC_DIR / "index.html",
        root_dir / "static" / "index.html",
        root_dir.parent / "static" / "index.html",
        root_dir / "app" / "static" / "index.html",
        root_dir.parent / "app" / "static" / "index.html"
    ]
    for p in possible_index_paths:
        if p.exists():
            return FileResponse(str(p), media_type="text/html")
    return HTMLResponse("<h1>VayuDrishti Platform Starting Up...</h1>")

# Mount Static Directories for CSS/JS
for static_candidate in [STATIC_DIR, Path(__file__).resolve().parent / "static", Path(__file__).resolve().parent.parent / "static"]:
    if static_candidate.exists():
        app.mount("/static", StaticFiles(directory=str(static_candidate)), name="static_files")
        app.mount("/js", StaticFiles(directory=str(static_candidate / "js")), name="static_js")
        app.mount("/css", StaticFiles(directory=str(static_candidate / "css")), name="static_css")
        break

async def scheduled_background_scraper():
    """
    Autonomous continuous background scheduler.
    Harvests flight fares every 15 seconds, runs Tukey IQR filtering,
    dynamically recalculates indices, and streams fresh live data to the MoSPI dashboard.
    """
    orchestrator = IngestionOrchestrator()
    try:
        orchestrator.run_live_ingestion_batch(sample_size_routes=3)
    except Exception as e:
        print(f"[Boot Initializer] Error: {e}")
        
    while True:
        try:
            interval = auto_scraper_config.get("interval_seconds", 15)
            await asyncio.sleep(interval)
            
            if auto_scraper_config.get("is_enabled", True):
                res = orchestrator.run_live_ingestion_batch(sample_size_routes=3)
                print(f"[VayuDrishti Live-Sync] Ingested {res['quotes_collected']} quotes | Recomputed AFI: {res['recomputed_national_index']}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[VayuDrishti Live-Sync] Background error: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
def on_startup():
    init_database()
    seed_database_if_empty()
    asyncio.create_task(scheduled_background_scraper())
    print("VayuDrishti MoSPI System initialized with Real-Time Auto-Scraping Active!")
