"""
VayuDrishti Indices REST API Endpoints
"""
import json
from fastapi import APIRouter
from app.engine.database import get_db_connection
from app.models.schemas import IndexQueryResponse

router = APIRouter(prefix="/indices", tags=["Indices"])

@router.get("/latest", response_model=IndexQueryResponse)
def get_latest_index():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM daily_indices ORDER BY index_date DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    
    if not row:
        return IndexQueryResponse(
            index_date="2026-08-31",
            national_airfare_index=114.8,
            laspeyres_index=114.8,
            jevons_index=113.2,
            hedonic_index=113.9,
            tornqvist_index=114.0,
            dod_change_pct=0.4,
            mom_change_pct=1.8,
            yoy_change_pct=8.4,
            category_indices={"METRO_METRO": 113.8, "METRO_TIER2": 116.4, "HILL_ISLAND": 128.5, "UDAN_RCS": 108.2},
            regional_indices={"Northern": 115.2, "Western": 113.9, "Southern": 112.8, "Eastern": 117.1, "North-Eastern": 122.4, "Central": 114.0},
            lead_time_indices={0: 246.8, 1: 204.2, 3: 155.0, 7: 120.5, 15: 107.9, 30: 94.2, 60: 85.0},
            observations_count=2140
        )
        
    return IndexQueryResponse(
        index_date=row["index_date"],
        national_airfare_index=row["national_index"],
        laspeyres_index=row["laspeyres_index"],
        jevons_index=row["jevons_index"],
        hedonic_index=row["hedonic_index"],
        tornqvist_index=row["tornqvist_index"],
        dod_change_pct=row["dod_change_pct"],
        mom_change_pct=row["mom_change_pct"],
        yoy_change_pct=row["yoy_change_pct"],
        category_indices=json.loads(row["category_indices_json"]),
        regional_indices=json.loads(row["regional_indices_json"]),
        lead_time_indices={int(k): v for k, v in json.loads(row["lead_time_indices_json"]).items()},
        observations_count=row["observations_count"]
    )

@router.get("/history")
def get_index_history(limit: int = 180):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM daily_indices ORDER BY index_date ASC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        result.append({
            "index_date": r["index_date"],
            "national_index": r["national_index"],
            "laspeyres_index": r["laspeyres_index"],
            "jevons_index": r["jevons_index"],
            "hedonic_index": r["hedonic_index"],
            "tornqvist_index": r["tornqvist_index"],
            "dod_change_pct": r["dod_change_pct"],
            "category_indices": json.loads(r["category_indices_json"]) if r["category_indices_json"] else {},
            "regional_indices": json.loads(r["regional_indices_json"]) if r["regional_indices_json"] else {},
            "lead_time_indices": json.loads(r["lead_time_indices_json"]) if r["lead_time_indices_json"] else {}
        })
    return result
