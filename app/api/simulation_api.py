"""
VayuDrishti Policy Simulation Sandbox REST API
"""
from fastapi import APIRouter
from app.models.schemas import PolicySimulationRequest, PolicySimulationResponse
from app.engine.policy_simulator import PolicySimulator

router = APIRouter(prefix="/simulation", tags=["Policy Simulation"])

@router.post("/run", response_model=PolicySimulationResponse)
@router.post("/simulate", response_model=PolicySimulationResponse)
def run_simulation(req: PolicySimulationRequest):
    res = PolicySimulator.simulate_policy_shock(
        baseline_index=114.8,
        atf_tax_change_pct=req.atf_tax_change_pct,
        emergency_fare_cap_multiplier=req.emergency_fare_cap_multiplier,
        udan_subsidy_change_pct=req.udan_subsidy_change_pct,
        festive_demand_surge_pct=req.festive_demand_surge_pct
    )
    return PolicySimulationResponse(**res)
