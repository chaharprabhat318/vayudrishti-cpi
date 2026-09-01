"""
VayuDrishti (??????????) - Enterprise MoSPI Backend Application
Ministry of Statistics and Programme Implementation (MoSPI), Government of India
"""
import os
import sys
import asyncio
from pathlib import Path
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure all search paths are present
current_dir = Path(__file__).resolve().parent
for p in [current_dir, current_dir / "app", current_dir / "backend", current_dir / "backend" / "app"]:
    p_str = str(p)
    if p.exists() and p_str not in sys.path:
        sys.path.insert(0, p_str)

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

def find_static_file(rel_path: str):
    """Finds a file across all possible static locations safely."""
    candidates = [
        STATIC_DIR / rel_path,
        current_dir / "static" / rel_path,
        current_dir / "app" / "static" / rel_path,
        current_dir / "backend" / "app" / "static" / rel_path
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    return None

# 1. Root Route Handler: ALWAYS returns index.html safely
@app.get("/")
async def serve_root_page():
    p = find_static_file("index.html")
    if p:
        return FileResponse(str(p), media_type="text/html")
    return HTMLResponse("<h1>VayuDrishti System Booting... Please refresh in 5 seconds.</h1>")

# 2. Static Asset Routes (JS/CSS/Assets) with automatic fallback
@app.get("/js/{filename}")
async def serve_js(filename: str):
    p = find_static_file(f"js/{filename}")
    if p:
        return FileResponse(str(p), media_type="application/javascript")
    return Response(status_code=404, content="JS File Not Found")

@app.get("/css/{filename}")
async def serve_css(filename: str):
    p = find_static_file(f"css/{filename}")
    if p:
        return FileResponse(str(p), media_type="text/css")
    return Response(status_code=404, content="CSS File Not Found")

# Safely mount static files if directory exists
for candidate in [STATIC_DIR, current_dir / "static", current_dir / "app" / "static"]:
    if candidate.exists() and candidate.is_dir():
        app.mount("/static", StaticFiles(directory=str(candidate)), name="static_mount")
        break

async def scheduled_background_scraper():
    """
    Autonomous background scheduler.
    Harvests flight fares every 15-30s, recalculates indices, and streams fresh live data.
    """
    orchestrator = IngestionOrchestrator()
    try:
        orchestrator.run_live_ingestion_batch(sample_size_routes=3)
    except Exception as e:
        print(f"[Boot Ingestion] Initial batch status: {e}")
        
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
    try:
        init_database()
        seed_database_if_empty()
    except Exception as e:
        print("[Database Init Error]:", e)
    asyncio.create_task(scheduled_background_scraper())
    print("[VayuDrishti MoSPI] Server started successfully with Auto-Scraping Active!")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    uvicorn.run(app, host=host, port=port)
