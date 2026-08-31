"""
VayuDrishti DGCA Official Market Share and Traffic Weight Matrices
Sourced from DGCA Monthly Domestic Air Transport Reports
"""
from app.core.airports_data import ROUTES

# DGCA Domestic Passenger Market Shares (Normalized Weights for Indian Carriers)
DGCA_AIRLINE_MARKET_SHARES = {
    "6E": {"name": "IndiGo", "share": 0.608, "is_lcc": True, "base_baggage": 15},
    "AI": {"name": "Air India Group (Air India / AIX / Vistara)", "share": 0.272, "is_lcc": False, "base_baggage": 20},
    "QP": {"name": "Akasa Air", "share": 0.045, "is_lcc": True, "base_baggage": 15},
    "SG": {"name": "SpiceJet", "share": 0.042, "is_lcc": True, "base_baggage": 15},
    "9I": {"name": "Alliance Air / Regional", "share": 0.033, "is_lcc": True, "base_baggage": 15}
}

# Calculate normalized route weights based on monthly passenger volume
TOTAL_BASE_MONTHLY_PAX = sum(r["base_pax_monthly"] for r in ROUTES)

ROUTE_WEIGHTS = {}
for r in ROUTES:
    route_key = f"{r['origin']}-{r['destination']}"
    ROUTE_WEIGHTS[route_key] = r["base_pax_monthly"] / TOTAL_BASE_MONTHLY_PAX

# Category Level Weights
CATEGORY_WEIGHTS = {}
for r in ROUTES:
    cat = r["category"]
    CATEGORY_WEIGHTS[cat] = CATEGORY_WEIGHTS.get(cat, 0.0) + (r["base_pax_monthly"] / TOTAL_BASE_MONTHLY_PAX)

def get_route_weight(origin: str, destination: str) -> float:
    key = f"{origin}-{destination}"
    return ROUTE_WEIGHTS.get(key, 1.0 / len(ROUTES))
