"""
VayuDrishti Econometric Hedonic Quality Adjustment REST API
"""
from fastapi import APIRouter
from app.engine.hedonic_model import HedonicRegressionEngine
from app.models.schemas import HedonicRegressionReport
from app.engine.database import get_db_connection

router = APIRouter(prefix="/hedonic", tags=["Hedonic Quality Adjustment"])

@router.get("/summary", response_model=HedonicRegressionReport)
def get_hedonic_summary():
    """Fit the displayed model from the observations currently in the database."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT price_inr, duration_min, stops, lead_time_days, baggage_kg, carrier_code
        FROM sanitized_fares
        WHERE is_outlier = 0
        ORDER BY id DESC
        LIMIT 1000
    """).fetchall()
    conn.close()
    report = HedonicRegressionEngine.run_hedonic_regression([dict(row) for row in rows])
    return HedonicRegressionReport(**report)
