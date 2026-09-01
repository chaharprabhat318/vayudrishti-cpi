"""
VayuDrishti (??????????) - Real-time Airfare Price Index for MoSPI
System Configuration and Constants
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Look for data and static either at root or inside backend
if (BASE_DIR / "data").exists():
    DATA_DIR = BASE_DIR / "data"
else:
    DATA_DIR = Path(__file__).resolve().parent.parent.parent / "backend" / "data"

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

DATABASE_PATH = DATA_DIR / "vayudrishti.db"

BASE_YEAR = "2024"
BASE_INDEX_VALUE = 100.0

CPI_BASKET_WEIGHTS = {
    "food_and_beverages": 45.86,
    "pan_tobacco_intoxicants": 2.38,
    "clothing_and_footwear": 6.53,
    "housing": 10.07,
    "fuel_and_light": 6.84,
    "miscellaneous": 28.32
}

CPI_TRANSPORT_COMMUNICATION_WEIGHT = 8.59
AIRFARE_SUB_WEIGHT_IN_TRANSPORT = 0.185
AIRFARE_EFFECTIVE_CPI_WEIGHT = (CPI_TRANSPORT_COMMUNICATION_WEIGHT * AIRFARE_SUB_WEIGHT_IN_TRANSPORT) / 100.0

LEAD_TIME_HORIZONS = [0, 1, 3, 7, 15, 30, 60]

LEAD_TIME_WEIGHTS = {
    0: 0.08,
    1: 0.10,
    3: 0.14,
    7: 0.22,
    15: 0.24,
    30: 0.15,
    60: 0.07
}

ROUTE_CATEGORIES = {
    "METRO_METRO": "Metro to Metro (Trunk Routes)",
    "METRO_TIER2": "Metro to Tier-2 / Emerging Hubs",
    "UDAN_RCS": "Regional Connectivity Scheme (UDAN)",
    "HILL_ISLAND": "Strategic / Remote / Island Corridors"
}

REGIONAL_ZONES = ["Northern", "Western", "Southern", "Eastern", "North-Eastern", "Central"]
