"""
VayuDrishti Gazette and SDMX Export REST API
"""
from fastapi import APIRouter, Response
from app.engine.report_generator import GazettedReportGenerator
from app.engine.cpi_augmenter import CPIAugmenter
from app.engine.database import get_db_connection

router = APIRouter(prefix="/export", tags=["Export"])

@router.get("/gazette-pdf")
def export_gazette_pdf():
    index_data = {
        "laspeyres_index": 114.8,
        "jevons_index": 113.2,
        "hedonic_index": 113.9,
        "mom_change_pct": 1.8,
        "yoy_change_pct": 8.4
    }
    cpi_data = CPIAugmenter.compute_cpi_augmentation(114.8)
    pdf_buffer = GazettedReportGenerator.generate_mospi_gazette_pdf(index_data, cpi_data)
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=MoSPI_AFI_Gazetted_Release_Aug2026.pdf"}
    )

@router.get("/json-stat")
def export_jsonstat():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM daily_indices ORDER BY index_date ASC LIMIT 180")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    
    payload = GazettedReportGenerator.generate_jsonstat_feed(
        index_data={"laspeyres_index": 114.8},
        history_data=rows
    )
    return payload
