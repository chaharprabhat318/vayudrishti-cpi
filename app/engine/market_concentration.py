"""
VayuDrishti Route Market Concentration Engine
Computes Herfindahl-Hirschman Index (HHI) for each corridor to evaluate monopoly pricing & competition.
HHI = sum( (share_i * 100)^2 )
"""
from typing import List, Dict, Any
from app.core.airports_data import ROUTES
from app.core.dgca_weights import DGCA_AIRLINE_MARKET_SHARES

class MarketConcentrationEngine:
    @staticmethod
    def calculate_hhi(carrier_shares: Dict[str, float]) -> float:
        """
        Computes HHI from a dict of carrier market shares (0.0 to 1.0).
        """
        hhi = sum((share * 100.0) ** 2 for share in carrier_shares.values())
        return round(hhi, 1)

    @staticmethod
    def get_route_concentration_profile(route_id: str, category: str) -> Dict[str, Any]:
        """
        Returns HHI, market concentration classification, and dominant carrier for a route.
        """
        # Metro routes have high competition (IndiGo + Air India + Akasa + SpiceJet)
        if category == "METRO_METRO":
            shares = {"6E": 0.54, "AI": 0.32, "QP": 0.08, "SG": 0.06}
            status = "Moderate Competition"
            top_carrier = "IndiGo (54%)"
        elif category == "METRO_TIER2":
            shares = {"6E": 0.65, "AI": 0.25, "SG": 0.10}
            status = "Concentrated"
            top_carrier = "IndiGo (65%)"
        elif category == "HILL_ISLAND":
            shares = {"6E": 0.58, "AI": 0.42}
            status = "Highly Concentrated (Duopoly)"
            top_carrier = "IndiGo (58%)"
        else: # UDAN_RCS
            shares = {"6E": 0.82, "9I": 0.18}
            status = "Near Monopoly (RCS Concession)"
            top_carrier = "IndiGo (82%)"
            
        hhi = MarketConcentrationEngine.calculate_hhi(shares)
        return {
            "hhi_index": hhi,
            "competition_status": status,
            "top_carrier": top_carrier,
            "carrier_shares": shares
        }
