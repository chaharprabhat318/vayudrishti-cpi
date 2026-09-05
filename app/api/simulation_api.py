"""
VayuDrishti Policy Simulation Sandbox REST API
"""
from fastapi import APIRouter
from app.models.schemas import PolicySimulationRequest, PolicySimulationResponse
from app.engine.policy_simulator import PolicySimulator
from app.engine.database import get_db_connection

router = APIRouter(prefix="/simulation", tags=["Policy Simulation"])

@router.post("/run", response_model=PolicySimulationResponse)
@router.post("/simulate", response_model=PolicySimulationResponse)
def run_simulation(req: PolicySimulationRequest):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT national_index FROM daily_indices ORDER BY index_date DESC LIMIT 1"
    ).fetchone()
    conn.close()
    baseline_index = row["national_index"] if row else 100.0
    res = PolicySimulator.simulate_policy_shock(
        baseline_index=baseline_index,
        atf_tax_change_pct=req.atf_tax_change_pct,
        emergency_fare_cap_multiplier=req.emergency_fare_cap_multiplier,
        udan_subsidy_change_pct=req.udan_subsidy_change_pct,
        festive_demand_surge_pct=req.festive_demand_surge_pct
    )
    return PolicySimulationResponse(**res)
