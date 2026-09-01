"""
VayuDrishti Statistical Index Engine
Implements Jevons (Geometric Mean), DGCA-Weighted Laspeyres, T?rnqvist, and Sub-Indices.
"""
import math
import numpy as np
from typing import List, Dict, Any, Optional
from app.core.config import BASE_INDEX_VALUE, LEAD_TIME_WEIGHTS
from app.core.airports_data import ROUTES, AIRPORTS
from app.core.dgca_weights import DGCA_AIRLINE_MARKET_SHARES, ROUTE_WEIGHTS, CATEGORY_WEIGHTS

class IndexCalculator:
    @staticmethod
    def calculate_jevons_index(current_prices: List[float], base_prices: List[float]) -> float:
        """
        Jevons Elementary Price Index (Geometric Mean of Price Relatives):
        I_J = exp( (1/n) * sum(ln(P_t / P_0)) ) * 100
        """
        if not current_prices or not base_prices or len(current_prices) != len(base_prices):
            return BASE_INDEX_VALUE
            
        relatives = []
        for p_t, p_0 in zip(current_prices, base_prices):
            if p_0 > 0 and p_t > 0:
                relatives.append(math.log(p_t / p_0))
                
        if not relatives:
            return BASE_INDEX_VALUE
            
        mean_log = sum(relatives) / len(relatives)
        return round(math.exp(mean_log) * BASE_INDEX_VALUE, 2)

    @staticmethod
    def calculate_laspeyres_index(route_data: List[Dict[str, Any]]) -> float:
        """
        DGCA-Weighted Laspeyres Price Index:
        I_L = sum_r ( w_r * sum_a ( s_a * (P_{r,a,t} / P_{r,a,0}) ) ) * 100
        """
        if not route_data:
            return BASE_INDEX_VALUE
            
        weighted_sum = 0.0
        total_weight = 0.0
        
        for item in route_data:
            p_t = item.get("current_price", 0.0)
            p_0 = item.get("base_price", 0.0)
            w = item.get("route_weight", 0.0)
            s = item.get("carrier_share", 1.0)
            
            effective_weight = w * s
            if p_0 > 0 and p_t > 0 and effective_weight > 0:
                ratio = p_t / p_0
                weighted_sum += effective_weight * ratio
                total_weight += effective_weight
                
        if total_weight == 0:
            return BASE_INDEX_VALUE
            
        normalized_index = (weighted_sum / total_weight) * BASE_INDEX_VALUE
        return round(normalized_index, 2)

    @staticmethod
    def calculate_tornqvist_index(laspeyres_idx: float, jevons_idx: float) -> float:
        """
        T?rnqvist / Fisher Superlative Approximation
        """
        return round(math.sqrt(laspeyres_idx * jevons_idx), 2)

    @staticmethod
    def compute_all_sub_indices(route_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Computes granular breakdowns across Categories, Regions, and Lead Time Horizons.
        """
        cat_sums = {}
        cat_counts = {}
        
        reg_sums = {}
        reg_counts = {}
        
        lead_sums = {}
        lead_counts = {}
        
        for r in route_records:
            ratio = r["current_price"] / r["base_price"] if r["base_price"] > 0 else 1.0
            
            # Category
            cat = r["category"]
            cat_sums[cat] = cat_sums.get(cat, 0.0) + ratio
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            
            # Region (origin airport region)
            origin_info = AIRPORTS.get(r["origin"], {})
            reg = origin_info.get("region", "Northern")
            reg_sums[reg] = reg_sums.get(reg, 0.0) + ratio
            reg_counts[reg] = reg_counts.get(reg, 0) + 1
            
            # Lead Time
            lead = r.get("lead_time_days", 7)
            lead_sums[lead] = lead_sums.get(lead, 0.0) + ratio
            lead_counts[lead] = lead_counts.get(lead, 0) + 1
            
        category_indices = {c: round((cat_sums[c] / cat_counts[c]) * BASE_INDEX_VALUE, 2) for c in cat_sums if cat_counts[c] > 0}
        regional_indices = {rg: round((reg_sums[rg] / reg_counts[rg]) * BASE_INDEX_VALUE, 2) for rg in reg_sums if reg_counts[rg] > 0}
        lead_time_indices = {int(ld): round((lead_sums[ld] / lead_counts[ld]) * BASE_INDEX_VALUE, 2) for ld in lead_sums if lead_counts[ld] > 0}
        
        return {
            "category_indices": category_indices,
            "regional_indices": regional_indices,
            "lead_time_indices": lead_time_indices
        }
