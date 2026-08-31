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
from app.scrapers.orchestrator import IngestionOrchestrator

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
    Runs an ingestion and index update cycle periodically (every 4 hours).
    """
    orchestrator = IngestionOrchestrator()
    while True:
        try:
            # Wait 4 hours between automatic background runs
            await asyncio.sleep(4 * 3600)
            print("[VayuDrishti Auto-Scheduler] Triggering scheduled autonomous batch ingestion...")
            result = orchestrator.run_live_ingestion_batch(sample_size_routes=12)
            print(f"[VayuDrishti Auto-Scheduler] Ingestion completed: {result['quotes_collected']} quotes updated.")
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[VayuDrishti Auto-Scheduler] Background sync error: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
def on_startup():
    init_database()
    seed_database_if_empty()
    # Start the automated background updater task
    asyncio.create_task(scheduled_background_scraper())
    print("VayuDrishti MoSPI System initialized and operational with auto-scheduler enabled!")
