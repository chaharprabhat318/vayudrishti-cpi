"""
VayuDrishti Ingestion Orchestrator
Coordinates multi-source scraping across 100+ routes and 7 lead-time horizons.
"""
import time
import json
import random
from datetime import datetime
from typing import Dict, Any, List
from app.core.config import LEAD_TIME_HORIZONS, BASE_INDEX_VALUE
from app.core.airports_data import ROUTES
from app.core.dgca_weights import ROUTE_WEIGHTS, DGCA_AIRLINE_MARKET_SHARES
from app.scrapers.airline_scrapers import AirlineScraper
from app.scrapers.ota_scrapers import OTAScraper
from app.engine.sanitization import DataSanitizer
from app.engine.index_calculator import IndexCalculator
from app.engine.database import get_db_connection

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

    def run_live_ingestion_batch(self, sample_size_routes: int = 15) -> Dict[str, Any]:
        """
        Executes an ingestion pass across representative routes and booking horizons,
        sanitizes data via Tukey IQR fences, updates SQLite tables, and re-computes daily indices.
        """
        start_time = time.time()
        selected_routes = random.sample(ROUTES, min(sample_size_routes, len(ROUTES)))
        
        all_raw_quotes = []
        sanitized_records = []
        
        for r in selected_routes:
            for lead in [0, 3, 7, 30]:  # Sample representative lead times for quick batch run
                # 1. Scrape Direct Airlines
                for c_code, scraper in self.airline_scrapers.items():
                    quotes = scraper.fetch_quotes_for_route(
                        r["origin"], r["destination"], lead, r["distance_km"], r["category"]
                    )
                    all_raw_quotes.extend(quotes)
                    
                # 2. Scrape OTAs
                for ota_name, ota in self.ota_scrapers.items():
                    ota_quotes = ota.fetch_quotes_for_route(
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
        
        # Save sanitized fares
        sanitized_rows = []
        for i, q in enumerate(all_raw_quotes):
            route_id = f"{q['origin']}-{q['destination']}"
            r_cat = "METRO_METRO"
            for rt in ROUTES:
                if rt["origin"] == q["origin"] and rt["destination"] == q["destination"]:
                    r_cat = rt["category"]
                    break
                    
            sanitized_rows.append((
                route_id, q["origin"], q["destination"], r_cat, q["carrier_code"],
                q["lead_time_days"], q["duration_min"], q["stops"], q["baggage_kg"],
                q["total_price_inr"], 1 if is_outlier_flags[i] else 0, z_scores[i], q["collected_at"]
            ))
            
        cursor.executemany("""
        INSERT INTO sanitized_fares (
            route_id, origin, destination, category, carrier_code,
            lead_time_days, duration_min, stops, baggage_kg, price_inr, is_outlier, z_score, collected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sanitized_rows)
        
        # Log scraper execution
        exec_time = round(time.time() - start_time, 2)
        cursor.execute("""
        INSERT INTO scraper_logs (run_timestamp, portal_source, routes_scanned, quotes_collected, status, execution_time_sec)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Multi-Source Batch Orchestrator", len(selected_routes), len(all_raw_quotes), "SUCCESS", exec_time))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "SUCCESS",
            "routes_scanned": len(selected_routes),
            "quotes_collected": len(all_raw_quotes),
            "clean_quotes_count": len(clean_prices),
            "outliers_filtered": tukey_stats.get("outlier_count", 0),
            "execution_time_sec": exec_time,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
