"""
VayuDrishti Econometric Hedonic Quality Adjustment REST API
"""
from fastapi import APIRouter
from app.engine.hedonic_model import HedonicRegressionEngine
from app.models.schemas import HedonicRegressionReport

router = APIRouter(prefix="/hedonic", tags=["Hedonic Quality Adjustment"])

@router.get("/summary", response_model=HedonicRegressionReport)
def get_hedonic_summary():
    report = HedonicRegressionEngine._fallback_hedonic_report()
    return HedonicRegressionReport(**report)
