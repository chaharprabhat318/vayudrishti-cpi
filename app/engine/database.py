"""
VayuDrishti Database Manager & Historical Data Seeder
SQLite persistence engine for raw fares, sanitized aggregates, and MoSPI CPI time series.
"""
import sqlite3
import json
import math
import random
from datetime import datetime, timedelta
from app.core.config import DATABASE_PATH, BASE_INDEX_VALUE, LEAD_TIME_HORIZONS, ROUTE_CATEGORIES
from app.core.airports_data import ROUTES, AIRPORTS
from app.core.dgca_weights import DGCA_AIRLINE_MARKET_SHARES, ROUTE_WEIGHTS, CATEGORY_WEIGHTS

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table 1: Raw Quotes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_quotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        carrier_code TEXT NOT NULL,
        carrier_name TEXT NOT NULL,
        flight_number TEXT NOT NULL,
        departure_time TEXT,
        arrival_time TEXT,
        duration_min INTEGER,
        stops INTEGER DEFAULT 0,
        lead_time_days INTEGER,
        cabin_class TEXT DEFAULT 'Economy',
        baggage_kg INTEGER DEFAULT 15,
        base_fare_inr REAL,
        taxes_fees_inr REAL,
        total_price_inr REAL,
        portal_source TEXT,
        collected_at TEXT
    )
    """)

    # Table 2: Sanitized Price Observations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sanitized_fares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quote_id INTEGER,
        route_id TEXT NOT NULL,
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        category TEXT NOT NULL,
        carrier_code TEXT NOT NULL,
        lead_time_days INTEGER,
        duration_min INTEGER,
        stops INTEGER,
        baggage_kg INTEGER,
        price_inr REAL NOT NULL,
        is_outlier INTEGER DEFAULT 0,
        z_score REAL,
        collected_at TEXT,
        FOREIGN KEY (quote_id) REFERENCES raw_quotes(id)
    )
    """)

    # Table 3: Daily Price Indices
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_indices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        index_date TEXT UNIQUE NOT NULL,
        national_index REAL NOT NULL,
        laspeyres_index REAL NOT NULL,
        jevons_index REAL NOT NULL,
        hedonic_index REAL NOT NULL,
        tornqvist_index REAL NOT NULL,
        dod_change_pct REAL,
        mom_change_pct REAL,
        yoy_change_pct REAL,
        category_indices_json TEXT,
        regional_indices_json TEXT,
        lead_time_indices_json TEXT,
        observations_count INTEGER
    )
    """)

    # Table 4: Scraper Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scraper_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_timestamp TEXT NOT NULL,
        portal_source TEXT NOT NULL,
        routes_scanned INTEGER,
        quotes_collected INTEGER,
        status TEXT,
        execution_time_sec REAL
    )
    """)

    # Table 5: MoSPI CPI Series & Augmentation
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cpi_series (
        month_year TEXT PRIMARY KEY,
        official_cpi_general REAL,
        official_cpi_transport REAL,
        vayudrishti_airfare_index REAL,
        augmented_cpi_transport REAL,
        nowcast_cpi_general REAL,
        delta_bps REAL
    )
    """)

    conn.commit()
    conn.close()

def seed_database_if_empty():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM daily_indices")
    count = cursor.fetchone()[0]
    
    if count > 0:
        conn.close()
        return

    print("Seeding initial historical data (2024 - 2026 time-series)...")
    
    # Generate 180 days of daily historical index records up to today (2026-08-31)
    end_date = datetime(2026, 8, 31)
    start_date = end_date - timedelta(days=180)
    
    current_date = start_date
    base_val = 100.0
    prev_national = base_val
    prev_laspeyres = base_val
    prev_jevons = base_val
    prev_hedonic = base_val
    
    daily_records = []
    
    day_idx = 0
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        month = current_date.month
        
        # Realistic Indian aviation seasonality:
        # Summer vacation peak (May-June): +8% to +15%
        # Monsoon dip (July-Aug): -4% to -8%
        # Festive season peak (Oct-Nov): +12% to +22%
        # Year-end holiday peak (Dec): +10% to +18%
        seasonality = 0.0
        if month in [5, 6]:
            seasonality = 7.5 + 3.0 * math.sin(day_idx / 10.0)
        elif month in [7, 8]:
            seasonality = -3.0 + 2.0 * math.sin(day_idx / 12.0)
        elif month in [10, 11]:
            seasonality = 14.0 + 4.0 * math.sin(day_idx / 8.0)
        elif month == 12:
            seasonality = 11.0 + 3.0 * math.sin(day_idx / 7.0)
        else:
            seasonality = 2.0 + 1.5 * math.sin(day_idx / 14.0)

        # Gradual economic secular trend (Aviation fuel & capacity growth)
        trend = (day_idx / 180.0) * 8.5
        
        # Add slight daily noise
        noise = (random.random() - 0.48) * 1.8
        
        # Calculate indices
        laspeyres = round(base_val + trend + seasonality + noise, 2)
        # Jevons geometric index is typically slightly lower due to substitution avoidance
        jevons = round(laspeyres * (0.985 + (random.random() * 0.008)), 2)
        # Hedonic index controls for amenity and duration variations
        hedonic = round(laspeyres * (0.992 + (random.random() * 0.005)), 2)
        tornqvist = round((laspeyres * jevons) ** 0.5, 2)
        national = laspeyres
        
        dod_pct = round(((national - prev_national) / prev_national) * 100.0, 2) if day_idx > 0 else 0.0
        mom_pct = round(dod_pct * 3.8, 2)
        yoy_pct = round(8.4 + (noise * 0.5), 2)
        
        # Category Sub-Indices
        cat_indices = {
            "METRO_METRO": round(national * (0.99 + random.random() * 0.02), 2),
            "METRO_TIER2": round(national * (1.02 + random.random() * 0.03), 2),
            "HILL_ISLAND": round(national * (1.14 + random.random() * 0.06), 2), # Higher volatility & surge
            "UDAN_RCS": round(national * (0.94 + random.random() * 0.02), 2)     # Subsidized ceiling
        }
        
        # Regional Sub-Indices
        reg_indices = {
            "Northern": round(national * (1.01 + random.random() * 0.02), 2),
            "Western": round(national * (0.99 + random.random() * 0.02), 2),
            "Southern": round(national * (0.98 + random.random() * 0.02), 2),
            "Eastern": round(national * (1.03 + random.random() * 0.03), 2),
            "North-Eastern": round(national * (1.08 + random.random() * 0.04), 2),
            "Central": round(national * (1.00 + random.random() * 0.02), 2)
        }
        
        # Lead Time Sub-Indices (D-0 emergency is 2x+ of D-30/D-60)
        lead_indices = {
            0: round(national * 2.15, 2),
            1: round(national * 1.78, 2),
            3: round(national * 1.35, 2),
            7: round(national * 1.05, 2),
            15: round(national * 0.94, 2),
            30: round(national * 0.82, 2),
            60: round(national * 0.74, 2)
        }
        
        obs_count = random.randint(1850, 2400)
        
        daily_records.append((
            date_str, national, laspeyres, jevons, hedonic, tornqvist,
            dod_pct, mom_pct, yoy_pct,
            json.dumps(cat_indices), json.dumps(reg_indices), json.dumps(lead_indices),
            obs_count
        ))
        
        prev_national = national
        current_date += timedelta(days=1)
        day_idx += 1
        
    cursor.executemany("""
    INSERT OR REPLACE INTO daily_indices (
        index_date, national_index, laspeyres_index, jevons_index, hedonic_index, tornqvist_index,
        dod_change_pct, mom_change_pct, yoy_change_pct,
        category_indices_json, regional_indices_json, lead_time_indices_json,
        observations_count
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, daily_records)

    # Seed Sample Live Recent Raw Fares and Sanitized Fares for the latest day
    print("Seeding representative live quotes and route aggregates...")
    sample_quotes = []
    sample_sanitized = []
    
    carriers = list(DGCA_AIRLINE_MARKET_SHARES.keys())
    carrier_weights = [DGCA_AIRLINE_MARKET_SHARES[c]["share"] for c in carriers]
    portals = ["IndiGo_Direct", "AirIndia_Direct", "MakeMyTrip", "EaseMyTrip", "GoogleFlights"]
    
    latest_date_str = "2026-08-31"
    
    for r in ROUTES:
        dist = r["distance_km"]
        base_rate_per_km = 4.2 if r["category"] != "HILL_ISLAND" else 6.8
        base_route_cost = 1800 + (dist * base_rate_per_km)
        
        for lead in LEAD_TIME_HORIZONS:
            lead_mult = {0: 2.2, 1: 1.8, 3: 1.35, 7: 1.05, 15: 0.95, 30: 0.82, 60: 0.75}[lead]
            
            # Generate 2 carrier quotes per lead time
            sampled_carriers = random.choices(carriers, weights=carrier_weights, k=2)
            for c_code in sampled_carriers:
                c_info = DGCA_AIRLINE_MARKET_SHARES[c_code]
                flt_no = f"{c_code}-{random.randint(101, 999)}"
                dur = int((dist / 700.0) * 60) + 40
                stops = 0 if dist < 1600 or random.random() > 0.3 else 1
                if stops == 1: dur += 90
                
                c_premium = 1.18 if not c_info["is_lcc"] else 1.0
                price = round(base_route_cost * lead_mult * c_premium * (0.92 + random.random() * 0.16), 0)
                base_fare = round(price * 0.78, 0)
                tax = price - base_fare
                portal = random.choice(portals)
                
                sample_quotes.append((
                    r["origin"], r["destination"], c_code, c_info["name"], flt_no,
                    "08:30", "10:45", dur, stops, lead, "Economy", c_info["base_baggage"],
                    base_fare, tax, price, portal, f"{latest_date_str} 10:00:00"
                ))
                
                route_id = f"{r['origin']}-{r['destination']}"
                sample_sanitized.append((
                    route_id, r["origin"], r["destination"], r["category"],
                    c_code, lead, dur, stops, c_info["base_baggage"],
                    price, 0, round((random.random() - 0.5) * 1.5, 2), f"{latest_date_str} 10:00:00"
                ))

    cursor.executemany("""
    INSERT INTO raw_quotes (
        origin, destination, carrier_code, carrier_name, flight_number,
        departure_time, arrival_time, duration_min, stops, lead_time_days, cabin_class, baggage_kg,
        base_fare_inr, taxes_fees_inr, total_price_inr, portal_source, collected_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_quotes)

    cursor.executemany("""
    INSERT INTO sanitized_fares (
        route_id, origin, destination, category, carrier_code,
        lead_time_days, duration_min, stops, baggage_kg, price_inr, is_outlier, z_score, collected_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_sanitized)

    # Seed CPI Augmentation Series (Monthly 2025-2026)
    cpi_months = [
        ("2025-09", 192.4, 178.5, 108.2, 179.2, 192.6, 20),
        ("2025-10", 193.1, 179.8, 114.6, 181.1, 193.5, 40),
        ("2025-11", 193.8, 180.4, 116.8, 181.9, 194.2, 45),
        ("2025-12", 194.2, 181.0, 115.2, 182.2, 194.5, 30),
        ("2026-01", 194.5, 181.4, 111.0, 182.3, 194.7, 20),
        ("2026-02", 194.8, 181.9, 110.5, 182.6, 195.0, 15),
        ("2026-03", 195.2, 182.3, 112.4, 183.2, 195.4, 22),
        ("2026-04", 195.9, 183.0, 113.8, 184.1, 196.2, 30),
        ("2026-05", 196.7, 184.1, 118.5, 185.8, 197.1, 42),
        ("2026-06", 197.3, 184.8, 119.2, 186.6, 197.8, 50),
        ("2026-07", 197.8, 185.0, 113.4, 186.1, 198.0, 20),
        ("2026-08", 198.4, 185.6, 114.8, 186.9, 198.7, 30)
    ]
    cursor.executemany("""
    INSERT OR REPLACE INTO cpi_series (
        month_year, official_cpi_general, official_cpi_transport,
        vayudrishti_airfare_index, augmented_cpi_transport, nowcast_cpi_general, delta_bps
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, cpi_months)

    conn.commit()
    conn.close()
    print("Database initialization and historical seed completed successfully!")
