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
    conn = get_db_connection()
    fare_rows = conn.execute("""
        SELECT origin, destination, AVG(price_inr) AS average_price
        FROM sanitized_fares
        WHERE is_outlier = 0
        GROUP BY origin, destination
    """).fetchall()
    conn.close()
    live_fares = {
        (row["origin"], row["destination"]): row["average_price"]
        for row in fare_rows
    }

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
        current_fare = round(live_fares.get((orig, dest), base_cost), 0)
        route_index = round((current_fare / base_cost) * 100, 2) if base_cost else 100.0
        
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
            "index_value": route_index,
            "change_pct": round(route_index - 100.0, 2),
            "hhi_index": hhi_info["hhi_index"],
            "competition_status": hhi_info["competition_status"],
            "top_carrier": hhi_info["top_carrier"]
        })
    return enriched_routes

@router.get("/airports")
def get_all_airports():
    return AIRPORTS
