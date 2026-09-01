"""
VayuDrishti (??????????) - Enterprise MoSPI Backend Application
Ministry of Statistics and Programme Implementation (MoSPI), Government of India
"""
import asyncio
from fastapi import FastAPI
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

# Mount Frontend Static Directory
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

async def scheduled_background_scraper():
    """
    Autonomous continuous background scheduler.
    Harvests flight fares every 15-30 seconds, runs Tukey IQR filtering,
    dynamically recalculates indices, and streams fresh live data to the MoSPI dashboard.
    """
    orchestrator = IngestionOrchestrator()
    # Initial quick burst to populate live stream on boot
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
