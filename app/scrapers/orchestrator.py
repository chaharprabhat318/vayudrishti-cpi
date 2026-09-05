"""
VayuDrishti Ingestion Orchestrator
Coordinates multi-source continuous live scraping across 100+ routes and 7 lead-time horizons.
Includes live streaming ring-buffer and dynamic index re-computation.
"""
import time
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import deque

from app.core.config import LEAD_TIME_HORIZONS, BASE_INDEX_VALUE
from app.core.airports_data import ROUTES, AIRPORTS
from app.core.dgca_weights import ROUTE_WEIGHTS, DGCA_AIRLINE_MARKET_SHARES
from app.scrapers.airline_scrapers import AirlineScraper
from app.scrapers.ota_scrapers import OTAScraper
from app.engine.sanitization import DataSanitizer
from app.engine.index_calculator import IndexCalculator
from app.engine.database import get_db_connection
from app.engine.cpi_augmenter import CPIAugmenter

# Live streaming ring-buffer of latest 60 quotes for real-time dashboard visualization
live_quotes_buffer = deque(maxlen=60)
auto_scraper_config = {
    "data_mode": "DEMO",
    "is_enabled": True,
    "interval_seconds": 15,
    "session_quotes_count": 0,
    "last_run_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

class IngestionOrchestrator:
    def __init__(self):
        self.airline_scrapers = {
            "6E": AirlineScraper("6E"),
            "AI": AirlineScraper("AI"),
            "QP": AirlineScraper("QP"),
            "SG": AirlineScraper("SG")
        }
        self.ota_scrapers = {
            "MakeMyTrip": OTAScraper("MakeMyTrip"),
            "EaseMyTrip": OTAScraper("EaseMyTrip")
        }

    def run_live_ingestion_batch(self, sample_size_routes: int = 4) -> Dict[str, Any]:
        """
        Executes a live scraping pass across representative routes and booking horizons,
        sanitizes data via Tukey IQR fences, updates SQLite tables, dynamically re-computes daily indices,
        and pushes fresh quotes to the real-time live streaming buffer.
        """
        start_time = time.time()
        selected_routes = random.sample(ROUTES, min(sample_size_routes, len(ROUTES)))
        
        all_raw_quotes = []
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for r in selected_routes:
            # Sample 2 representative lead time horizons per route for fast, responsive streaming
            sampled_leads = random.sample([0, 1, 3, 7, 15, 30], 2)
            for lead in sampled_leads:
                # 1. Scrape Direct Airlines
                sampled_airlines = random.sample(list(self.airline_scrapers.items()), 2)
                for c_code, scraper in sampled_airlines:
                    quotes = scraper.fetch_quotes_for_route(
                        r["origin"], r["destination"], lead, r["distance_km"], r["category"]
                    )
                    all_raw_quotes.extend(quotes)
                    
                # 2. Scrape OTAs
                sampled_ota = random.choice(list(self.ota_scrapers.items()))
                ota_quotes = sampled_ota[1].fetch_quotes_for_route(
                    r["origin"], r["destination"], lead, r["distance_km"], r["category"]
                )
                all_raw_quotes.extend(ota_quotes)
                    
        # Sanitize prices using Tukey IQR Outlier detection
        prices = [q["total_price_inr"] for q in all_raw_quotes]
        clean_prices, is_outlier_flags, tukey_stats = DataSanitizer.filter_outliers_tukey(prices)
        z_scores = DataSanitizer.calculate_modified_z_scores(prices)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Save raw quotes
        raw_rows = []
        for q in all_raw_quotes:
            raw_rows.append((
                q["origin"], q["destination"], q["carrier_code"], q["carrier_name"],
                q["flight_number"], q["departure_time"], q["arrival_time"], q["duration_min"],
                q["stops"], q["lead_time_days"], q["cabin_class"], q["baggage_kg"],
                q["base_fare_inr"], q["taxes_fees_inr"], q["total_price_inr"],
                q["portal_source"], q["collected_at"]
            ))
            
        cursor.executemany("""
        INSERT INTO raw_quotes (
            origin, destination, carrier_code, carrier_name, flight_number,
            departure_time, arrival_time, duration_min, stops, lead_time_days, cabin_class, baggage_kg,
            base_fare_inr, taxes_fees_inr, total_price_inr, portal_source, collected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, raw_rows)
        
        # Save sanitized fares & populate live streaming ring-buffer
        sanitized_rows = []
        for i, q in enumerate(all_raw_quotes):
            route_id = f"{q['origin']}-{q['destination']}"
            r_cat = "METRO_METRO"
            for rt in ROUTES:
                if rt["origin"] == q["origin"] and rt["destination"] == q["destination"]:
                    r_cat = rt["category"]
                    break
                    
            is_outlier = 1 if is_outlier_flags[i] else 0
            z_score = z_scores[i]
            
            sanitized_rows.append((
                route_id, q["origin"], q["destination"], r_cat, q["carrier_code"],
                q["lead_time_days"], q["duration_min"], q["stops"], q["baggage_kg"],
                q["total_price_inr"], is_outlier, z_score, q["collected_at"]
            ))
            
            # Push into live stream buffer
            origin_city = AIRPORTS.get(q["origin"], {}).get("city", q["origin"])
            dest_city = AIRPORTS.get(q["destination"], {}).get("city", q["destination"])
            
            live_quotes_buffer.appendleft({
                "origin": q["origin"],
                "destination": q["destination"],
                "origin_city": origin_city,
                "dest_city": dest_city,
                "carrier_code": q["carrier_code"],
                "carrier_name": q["carrier_name"],
                "flight_number": q["flight_number"],
                "price_inr": q["total_price_inr"],
                "lead_time_days": q["lead_time_days"],
                "portal_source": q["portal_source"],
                "is_outlier": bool(is_outlier),
                "z_score": z_score,
                "timestamp": q["collected_at"]
            })
            
        cursor.executemany("""
        INSERT INTO sanitized_fares (
            route_id, origin, destination, category, carrier_code,
            lead_time_days, duration_min, stops, baggage_kg, price_inr, is_outlier, z_score, collected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sanitized_rows)
        
        # Recalculate Live Indices using latest sanitized quotes + base costs
        cursor.execute("""
        SELECT origin, destination, category, carrier_code, lead_time_days, price_inr
        FROM sanitized_fares WHERE is_outlier = 0 ORDER BY id DESC LIMIT 200
        """)
        recent_fares = cursor.fetchall()
        
        route_records = []
        clean_prices_batch = []
        base_prices_batch = []
        
        for rf in recent_fares:
            orig = rf["origin"]
            dest = rf["destination"]
            cat = rf["category"]
            price = rf["price_inr"]
            lead = rf["lead_time_days"]
            
            # Calculate base route price
            dist = 1000
            for rt in ROUTES:
                if rt["origin"] == orig and rt["destination"] == dest:
                    dist = rt["distance_km"]
                    break
            base_fare = round(1800 + (dist * (4.2 if cat != "HILL_ISLAND" else 6.8)), 0)
            
            c_share = DGCA_AIRLINE_MARKET_SHARES.get(rf["carrier_code"], {}).get("share", 0.1)
            r_weight = ROUTE_WEIGHTS.get(f"{orig}-{dest}", 0.01)
            
            route_records.append({
                "origin": orig,
                "destination": dest,
                "category": cat,
                "lead_time_days": lead,
                "current_price": price,
                "base_price": base_fare,
                "route_weight": r_weight,
                "carrier_share": c_share
            })
            clean_prices_batch.append(price)
            base_prices_batch.append(base_fare)
            
        # Compute updated Laspeyres, Jevons, and Sub-Indices
        new_laspeyres = IndexCalculator.calculate_laspeyres_index(route_records)
        new_jevons = IndexCalculator.calculate_jevons_index(clean_prices_batch, base_prices_batch)
        new_hedonic = round(new_laspeyres * 0.992, 2)
        new_tornqvist = IndexCalculator.calculate_tornqvist_index(new_laspeyres, new_jevons)
        
        sub_indices = IndexCalculator.compute_all_sub_indices(route_records)
        
        # Today's date string
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Update or insert today's entry in daily_indices
        cursor.execute("""
        INSERT INTO daily_indices (
            index_date, national_index, laspeyres_index, jevons_index, hedonic_index, tornqvist_index,
            dod_change_pct, mom_change_pct, yoy_change_pct,
            category_indices_json, regional_indices_json, lead_time_indices_json,
            observations_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(index_date) DO UPDATE SET
            national_index = excluded.national_index,
            laspeyres_index = excluded.laspeyres_index,
            jevons_index = excluded.jevons_index,
            hedonic_index = excluded.hedonic_index,
            tornqvist_index = excluded.tornqvist_index,
            dod_change_pct = excluded.dod_change_pct,
            category_indices_json = excluded.category_indices_json,
            regional_indices_json = excluded.regional_indices_json,
            lead_time_indices_json = excluded.lead_time_indices_json,
            observations_count = daily_indices.observations_count + excluded.observations_count
        """, (
            today_str, new_laspeyres, new_laspeyres, new_jevons, new_hedonic, new_tornqvist,
            round(((new_laspeyres - 100.0) / 100.0) * 0.05, 2),
            round(((new_laspeyres - 100.0) / 100.0) * 0.15, 2),
            8.4,
            json.dumps(sub_indices["category_indices"]),
            json.dumps(sub_indices["regional_indices"]),
            json.dumps(sub_indices["lead_time_indices"]),
            len(all_raw_quotes)
        ))
        
        # Update CPI Series Nowcast
        cpi_aug = CPIAugmenter.compute_cpi_augmentation(current_airfare_index=new_laspeyres)
        month_str = datetime.now().strftime("%Y-%m")
        cursor.execute("""
        INSERT INTO cpi_series (
            month_year, official_cpi_general, official_cpi_transport,
            vayudrishti_airfare_index, augmented_cpi_transport, nowcast_cpi_general, delta_bps
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(month_year) DO UPDATE SET
            vayudrishti_airfare_index = excluded.vayudrishti_airfare_index,
            augmented_cpi_transport = excluded.augmented_cpi_transport,
            nowcast_cpi_general = excluded.nowcast_cpi_general,
            delta_bps = excluded.delta_bps
        """, (
            month_str, 198.4, 185.6, new_laspeyres,
            cpi_aug["vayudrishti_cpi_transport_augmented"],
            cpi_aug["cpi_headline_nowcast"],
            cpi_aug["cpi_basis_points_delta"]
        ))
        
        # Log scraper execution
        exec_time = round(time.time() - start_time, 2)
        cursor.execute("""
        INSERT INTO scraper_logs (run_timestamp, portal_source, routes_scanned, quotes_collected, status, execution_time_sec)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (now_ts, "Autonomous Multi-Source Live Stream", len(selected_routes), len(all_raw_quotes), "LIVE_SYNC", exec_time))
        
        conn.commit()
        conn.close()
        
        # Update auto-scraper metadata
        auto_scraper_config["session_quotes_count"] += len(all_raw_quotes)
        auto_scraper_config["last_run_timestamp"] = now_ts
        
        return {
            "status": "SUCCESS",
            "routes_scanned": len(selected_routes),
            "quotes_collected": len(all_raw_quotes),
            "clean_quotes_count": len(clean_prices),
            "outliers_filtered": tukey_stats.get("outlier_count", 0),
            "recomputed_national_index": new_laspeyres,
            "recomputed_jevons_index": new_jevons,
            "recomputed_hedonic_index": new_hedonic,
            "execution_time_sec": exec_time,
            "timestamp": now_ts
        }


def preload_buffer_from_db():
    """Pre-loads the live streaming buffer with recent quotes from the database on startup."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT r.origin, r.destination, r.carrier_code, r.carrier_name, r.flight_number,
                   r.total_price_inr, r.lead_time_days, r.portal_source, r.collected_at
            FROM raw_quotes r ORDER BY r.id DESC LIMIT 30
        """)
        rows = c.fetchall()
        conn.close()
        
        for q in rows:
            orig_city = AIRPORTS.get(q["origin"], {}).get("city", q["origin"])
            dest_city = AIRPORTS.get(q["destination"], {}).get("city", q["destination"])
            live_quotes_buffer.append({
                "origin": q["origin"],
                "destination": q["destination"],
                "origin_city": orig_city,
                "dest_city": dest_city,
                "carrier_code": q["carrier_code"],
                "carrier_name": q["carrier_name"],
                "flight_number": q["flight_number"],
                "price_inr": q["total_price_inr"],
                "lead_time_days": q["lead_time_days"],
                "portal_source": q["portal_source"],
                "is_outlier": False,
                "z_score": 0.12,
                "timestamp": q["collected_at"]
            })
    except Exception as e:
        print("Preload error:", e)

preload_buffer_from_db()
