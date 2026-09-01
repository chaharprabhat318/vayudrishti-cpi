"""
VayuDrishti CPI Augmentation & MPC Nowcasting REST API
"""
from fastapi import APIRouter
from app.engine.cpi_augmenter import CPIAugmenter
from app.models.schemas import CPIAugmentationReport
from app.engine.database import get_db_connection

router = APIRouter(prefix="/cpi", tags=["CPI Augmentation"])

@router.get("/augmentation", response_model=CPIAugmentationReport)
def get_cpi_augmentation(current_afi: float = 114.8):
    result = CPIAugmenter.compute_cpi_augmentation(current_airfare_index=current_afi)
    return CPIAugmentationReport(**result)

@router.get("/series")
def get_cpi_historical_series():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM cpi_series ORDER BY month_year ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
