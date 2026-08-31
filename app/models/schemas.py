"""
VayuDrishti Pydantic Models and API Schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class RawFareQuote(BaseModel):
    origin: str
    destination: str
    carrier_code: str
    carrier_name: str
    flight_number: str
    departure_time: str
    arrival_time: str
    duration_min: int
    stops: int
    lead_time_days: int
    cabin_class: str = "Economy"
    baggage_kg: int = 15
    base_fare_inr: float
    taxes_fees_inr: float
    total_price_inr: float
    portal_source: str
    collected_at: str

class SanitizedFare(BaseModel):
    id: Optional[int] = None
    route_id: str
    origin: str
    destination: str
    category: str
    carrier_code: str
    lead_time_days: int
    price_inr: float
    is_outlier: bool
    z_score: float
    timestamp: str

class IndexQueryResponse(BaseModel):
    index_date: str
    national_airfare_index: float
    laspeyres_index: float
    jevons_index: float
    hedonic_index: float
    tornqvist_index: float
    dod_change_pct: float
    mom_change_pct: float
    yoy_change_pct: float
    category_indices: Dict[str, float]
    regional_indices: Dict[str, float]
    lead_time_indices: Dict[int, float]
    observations_count: int

class RouteDetail(BaseModel):
    origin: str
    destination: str
    origin_city: str
    dest_city: str
    category: str
    distance_km: int
    current_avg_fare: float
    base_fare: float
    index_value: float
    change_pct: float
    hhi_index: float
    competition_status: str
    top_carrier: str

class HedonicRegressionReport(BaseModel):
    model_timestamp: str
    r_squared: float
    adj_r_squared: float
    sample_size: int
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    pure_price_inflation_pct: float
    quality_drift_impact_pct: float
    feature_importance: Dict[str, float]

class CPIAugmentationReport(BaseModel):
    reference_month: str
    official_cpi_general: float
    official_cpi_transport: float
    vayudrishti_cpi_transport_augmented: float
    cpi_headline_nowcast: float
    airfare_index_value: float
    airfare_effective_weight_pct: float
    cpi_basis_points_delta: float
    rbi_mpc_warning_level: str
    commentary: str

class PolicySimulationRequest(BaseModel):
    atf_tax_change_pct: float = Field(0.0, description="ATF Aviation Fuel Tax change %")
    emergency_fare_cap_multiplier: float = Field(0.0, description="Emergency fare cap factor")
    udan_subsidy_change_pct: float = Field(0.0, description="UDAN VGF Subsidy expansion %")
    festive_demand_surge_pct: float = Field(0.0, description="Festive holiday surge demand %")

class PolicySimulationResponse(BaseModel):
    simulated_national_airfare_index: float
    baseline_national_airfare_index: float
    index_delta_pct: float
    transport_cpi_impact_pct: float
    headline_cpi_delta_bps: float
    category_impacts: Dict[str, float]
    policy_recommendation: str

class ScraperJobStatus(BaseModel):
    is_running: bool
    last_run_timestamp: Optional[str]
    total_quotes_collected: int
    quotes_last_24h: int
    active_sources: List[str]
    health: str
