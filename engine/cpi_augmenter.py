"""
VayuDrishti MoSPI CPI Transport Basket Augmentation & Nowcasting Engine
Integrates high-frequency airfare price relatives into the official CPI framework.
"""
from typing import Dict, Any
from app.core.config import CPI_TRANSPORT_COMMUNICATION_WEIGHT, AIRFARE_SUB_WEIGHT_IN_TRANSPORT, AIRFARE_EFFECTIVE_CPI_WEIGHT

class CPIAugmenter:
    @staticmethod
    def compute_cpi_augmentation(
        current_airfare_index: float,
        official_cpi_general: float = 198.4,
        official_cpi_transport: float = 185.6,
        base_airfare_index: float = 100.0
    ) -> Dict[str, Any]:
        """
        Calculates augmented CPI Transport sub-index, Headline CPI nowcast, and RBI MPC warning level.
        """
        airfare_growth_ratio = current_airfare_index / base_airfare_index
        
        # Transport basket has ~18.5% weight for civil aviation in modern urban transport
        # Other transport (railways, buses, fuel, auto) accounts for remaining 81.5%
        other_transport_sub_index = official_cpi_transport
        
        # Augmented Transport CPI
        augmented_transport_cpi = round(
            (other_transport_sub_index * (1.0 - AIRFARE_SUB_WEIGHT_IN_TRANSPORT)) +
            (other_transport_sub_index * AIRFARE_SUB_WEIGHT_IN_TRANSPORT * airfare_growth_ratio),
            2
        )
        
        # Impact on Headline CPI (Combined General Index)
        transport_growth = (augmented_transport_cpi - official_cpi_transport) / official_cpi_transport
        cpi_delta_points = round(official_cpi_general * (CPI_TRANSPORT_COMMUNICATION_WEIGHT / 100.0) * transport_growth, 3)
        nowcast_headline = round(official_cpi_general + cpi_delta_points, 2)
        
        delta_bps = round(cpi_delta_points * 100.0, 1)
        
        # Determine RBI Monetary Policy Committee Warning Level
        afi_change_pct = ((current_airfare_index - base_airfare_index) / base_airfare_index) * 100.0
        
        if afi_change_pct > 20.0:
            warning = "CRITICAL (Severe Dynamic Pricing Surge)"
            commentary = f"Airfare inflation (+{afi_change_pct:.1f}%) adds +{delta_bps:.1f} bps to headline CPI. High-frequency transport shock detected. Recommended: Review dynamic yield capping on trunk corridors."
        elif afi_change_pct > 10.0:
            warning = "ELEVATED (Seasonal Peak Demand)"
            commentary = f"Airfare inflation (+{afi_change_pct:.1f}%) contributes +{delta_bps:.1f} bps to CPI. Seasonal festival/holiday surge active. Monitor weekly trajectory."
        elif afi_change_pct < -5.0:
            warning = "DEFLATIONARY (Monsoon / Off-peak discounting)"
            commentary = f"Airfare discount cycle (-{abs(afi_change_pct):.1f}%) softens headline transport inflation by -{abs(delta_bps):.1f} bps."
        else:
            warning = "NORMAL (Stable Corridors)"
            commentary = "Airfare movements are well within baseline seasonal volatility bands. No disruptive CPI pass-through."
            
        return {
            "reference_month": "August 2026",
            "official_cpi_general": official_cpi_general,
            "official_cpi_transport": official_cpi_transport,
            "vayudrishti_cpi_transport_augmented": augmented_transport_cpi,
            "cpi_headline_nowcast": nowcast_headline,
            "airfare_index_value": current_airfare_index,
            "airfare_effective_weight_pct": round(AIRFARE_EFFECTIVE_CPI_WEIGHT * 100.0, 2),
            "cpi_basis_points_delta": delta_bps,
            "rbi_mpc_warning_level": warning,
            "commentary": commentary
        }
