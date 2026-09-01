"""
VayuDrishti Scrapers Management & Real-Time Live Stream REST API
"""
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.models.schemas import ScraperJobStatus
from app.scrapers.orchestrator import IngestionOrchestrator, live_quotes_buffer, auto_scraper_config
from app.engine.database import get_db_connection

router = APIRouter(prefix="/scrapers", tags=["Scrapers"])
orchestrator = IngestionOrchestrator()

class ToggleAutoRequest(BaseModel):
    is_enabled: bool = True
    interval_seconds: int = 15

@router.get("/status", response_model=ScraperJobStatus)
def get_scraper_status():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM raw_quotes")
    total_quotes = c.fetchone()[0]
    conn.close()
    
    return ScraperJobStatus(
        is_running=auto_scraper_config["is_enabled"],
        last_run_timestamp=auto_scraper_config["last_run_timestamp"],
        total_quotes_collected=total_quotes,
        quotes_last_24h=total_quotes,
        active_sources=["IndiGo_Direct", "AirIndia_Direct", "AkasaAir_Direct", "SpiceJet_Direct", "MakeMyTrip", "EaseMyTrip"],
        health=f"OPERATING AUTONOMOUSLY (Sync every {auto_scraper_config['interval_seconds']}s)" if auto_scraper_config["is_enabled"] else "PAUSED"
    )

@router.get("/live-stream")
def get_live_stream_quotes():
    """
    Returns recent quotes from the live streaming ring-buffer + session stats for real-time UI animation.
    """
    # If buffer is empty, prime it with a fast micro-scrape pass
    if len(live_quotes_buffer) == 0:
        orchestrator.run_live_ingestion_batch(sample_size_routes=3)
        
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT national_index, laspeyres_index, jevons_index, hedonic_index, dod_change_pct FROM daily_indices ORDER BY index_date DESC LIMIT 1")
    latest_row = c.fetchone()
    c.execute("SELECT COUNT(*) FROM raw_quotes")
    total_quotes = c.fetchone()[0]
    conn.close()
    
    return {
        "is_auto_scraping": auto_scraper_config["is_enabled"],
        "interval_seconds": auto_scraper_config["interval_seconds"],
        "session_quotes_count": auto_scraper_config["session_quotes_count"],
        "total_quotes_db": total_quotes,
        "latest_index": {
            "national_index": latest_row[0] if latest_row else 114.80,
            "laspeyres_index": latest_row[1] if latest_row else 114.80,
            "jevons_index": latest_row[2] if latest_row else 113.20,
            "hedonic_index": latest_row[3] if latest_row else 113.90,
            "dod_change_pct": latest_row[4] if latest_row else 0.4
        },
        "live_quotes": list(live_quotes_buffer)[:25]
    }

@router.post("/toggle-auto")
def toggle_auto_scraping(req: ToggleAutoRequest):
    auto_scraper_config["is_enabled"] = req.is_enabled
    auto_scraper_config["interval_seconds"] = max(5, min(3600, req.interval_seconds))
    return {
        "status": "UPDATED",
        "is_enabled": auto_scraper_config["is_enabled"],
        "interval_seconds": auto_scraper_config["interval_seconds"]
    }

@router.post("/trigger-batch")
def trigger_scraping_batch():
    result = orchestrator.run_live_ingestion_batch(sample_size_routes=8)
    return result

@router.get("/logs")
def get_scraper_logs(limit: int = 15):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM scraper_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
