"""
VayuDrishti Policy Simulation Sandbox
Models Aviation Turbine Fuel (ATF) excise duty shocks, emergency price capping, and UDAN VGF subsidies.
"""
from typing import Dict, Any
from app.core.config import BASE_INDEX_VALUE, AIRFARE_EFFECTIVE_CPI_WEIGHT

class PolicySimulator:
    @staticmethod
    def simulate_policy_shock(
        baseline_index: float = 114.8,
        atf_tax_change_pct: float = 0.0,
        emergency_fare_cap_multiplier: float = 0.0,
        udan_subsidy_change_pct: float = 0.0,
        festive_demand_surge_pct: float = 0.0
    ) -> Dict[str, Any]:
        """
        Simulates macro & regulatory interventions.
        - ATF is ~40% of airline direct operating cost, pass-through elasticity ~0.65.
        - Fare cap compresses D-0/D-1 extreme right-tail price distribution.
        - UDAN subsidy directly reduces RCS tier fares.
        - Festive surge increases trunk & leisure demand.
        """
        # 1. ATF Fuel Pass-through Impact
        # Delta_AFI = ATF_Change * 0.40 * 0.65
        atf_impact_pct = atf_tax_change_pct * 0.40 * 0.65
        
        # 2. Fare Cap Impact (if set between 1.5x and 3.0x base)
        fare_cap_reduction_pct = 0.0
        if emergency_fare_cap_multiplier > 0:
            # Stronger capping (e.g. 1.8x) yields larger reduction on peak surges
            fare_cap_reduction_pct = max(0.0, (2.8 - emergency_fare_cap_multiplier) * 4.2)
            
        # 3. UDAN Subsidy Expansion (affects ~6% of total network basket)
        udan_impact_pct = -(udan_subsidy_change_pct * 0.06 * 0.8)
        
        # 4. Festive Surge Impact
        festive_impact_pct = festive_demand_surge_pct * 0.35
        
        # Net simulated index
        total_delta_pct = atf_impact_pct - fare_cap_reduction_pct + udan_impact_pct + festive_impact_pct
        simulated_index = round(baseline_index * (1.0 + (total_delta_pct / 100.0)), 2)
        index_delta_pct = round(((simulated_index - baseline_index) / baseline_index) * 100.0, 2)
        
        # Impact on Transport CPI and Headline CPI in basis points
        transport_cpi_impact_pct = round(index_delta_pct * 0.185, 2)
        headline_cpi_delta_bps = round(index_delta_pct * AIRFARE_EFFECTIVE_CPI_WEIGHT * 100.0, 1)
        
        # Category breakdown impacts
        cat_impacts = {
            "METRO_METRO": round(simulated_index * 0.99, 2),
            "METRO_TIER2": round(simulated_index * 1.01, 2),
            "HILL_ISLAND": round(simulated_index * (1.12 - (fare_cap_reduction_pct * 0.01)), 2),
            "UDAN_RCS": round(simulated_index * (0.94 + (udan_impact_pct * 0.01)), 2)
        }
        
        # Policy recommendation text
        if headline_cpi_delta_bps > 25.0:
            rec = "CRITICAL INFLATION IMPACT: The simulated policy/shock will add >25 bps to national headline CPI. Recommend implementing targeted ATF tax rationalization and temporary lead-time fare caps."
        elif headline_cpi_delta_bps < -15.0:
            rec = "DEFLATIONARY / CONSUMER RELIEF: Policy significantly eases passenger travel cost and reduces transport inflation pressure by over 15 bps."
        else:
            rec = "MODERATE IMPACT: Policy shift causes contained price adjustments (+/- 10-15 bps headline CPI impact), well within monetary policy tolerance bands."
            
        return {
            "simulated_national_airfare_index": simulated_index,
            "baseline_national_airfare_index": baseline_index,
            "index_delta_pct": index_delta_pct,
            "transport_cpi_impact_pct": transport_cpi_impact_pct,
            "headline_cpi_delta_bps": headline_cpi_delta_bps,
            "category_impacts": cat_impacts,
            "policy_recommendation": rec
        }
