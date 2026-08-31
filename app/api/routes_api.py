"""
VayuDrishti Routes and Geo Network REST API
"""
from fastapi import APIRouter
from app.core.airports_data import ROUTES, AIRPORTS
from app.core.dgca_weights import ROUTE_WEIGHTS
from app.engine.market_concentration import MarketConcentrationEngine
from app.engine.database import get_db_connection

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.get("/")
def get_all_routes():
    """
    Returns all 100+ corridors with airports metadata, HHI concentration, and current fare stats.
    """
    enriched_routes = []
    for r in ROUTES:
        orig = r["origin"]
        dest = r["destination"]
        orig_info = AIRPORTS.get(orig, {})
        dest_info = AIRPORTS.get(dest, {})
        
        route_id = f"{orig}-{dest}"
        cat = r["category"]
        dist = r["distance_km"]
        base_rate = 4.2 if cat != "HILL_ISLAND" else 6.8
        base_cost = round(1800 + (dist * base_rate), 0)
        current_fare = round(base_cost * 1.148, 0)
        
        hhi_info = MarketConcentrationEngine.get_route_concentration_profile(route_id, cat)
        
        enriched_routes.append({
            "route_id": route_id,
            "origin": orig,
            "destination": dest,
            "origin_city": orig_info.get("city", orig),
            "dest_city": dest_info.get("city", dest),
            "origin_lat": orig_info.get("lat", 0.0),
            "origin_lon": orig_info.get("lon", 0.0),
            "dest_lat": dest_info.get("lat", 0.0),
            "dest_lon": dest_info.get("lon", 0.0),
            "category": cat,
            "distance_km": dist,
            "base_fare": base_cost,
            "current_avg_fare": current_fare,
            "index_value": 114.8,
            "change_pct": 8.4,
            "hhi_index": hhi_info["hhi_index"],
            "competition_status": hhi_info["competition_status"],
            "top_carrier": hhi_info["top_carrier"]
        })
    return enriched_routes

@router.get("/airports")
def get_all_airports():
    return AIRPORTS
