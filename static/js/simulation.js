/**
 * VayuDrishti Policy Simulation Sandbox Controller
 */
async function runPolicySimulation() {
    const atfVal = parseFloat(document.getElementById('simAtfSlider').value);
    const capVal = parseFloat(document.getElementById('simCapSlider').value);
    const udanVal = parseFloat(document.getElementById('simUdanSlider').value);
    const surgeVal = parseFloat(document.getElementById('simSurgeSlider').value);
    
    document.getElementById('simAtfLabel').innerText = `${atfVal > 0 ? '+' : ''}${atfVal}%`;
    document.getElementById('simCapLabel').innerText = capVal === 0 ? 'No Cap (Free Market)' : `${capVal}x Base Fare`;
    document.getElementById('simUdanLabel').innerText = `${udanVal > 0 ? '+' : ''}${udanVal}%`;
    document.getElementById('simSurgeLabel').innerText = `${surgeVal > 0 ? '+' : ''}${surgeVal}%`;
    
    try {
        const res = await fetch('/api/simulation/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                atf_tax_change_pct: atfVal,
                emergency_fare_cap_multiplier: capVal,
                udan_subsidy_change_pct: udanVal,
                festive_demand_surge_pct: surgeVal
            })
        });
        const data = await res.json();
        
        document.getElementById('simAfiResult').innerText = data.simulated_national_airfare_index;
        const deltaElem = document.getElementById('simAfiDelta');
        deltaElem.innerText = `${data.index_delta_pct > 0 ? '+' : ''}${data.index_delta_pct}%`;
        deltaElem.className = data.index_delta_pct > 0 ? 'text-red-600 font-bold' : (data.index_delta_pct < 0 ? 'text-emerald-600 font-bold' : 'text-slate-600');
        
        document.getElementById('simTransportResult').innerText = `${data.transport_cpi_impact_pct > 0 ? '+' : ''}${data.transport_cpi_impact_pct}%`;
        
        const bpsElem = document.getElementById('simBpsResult');
        bpsElem.innerText = `${data.headline_cpi_delta_bps > 0 ? '+' : ''}${data.headline_cpi_delta_bps} bps`;
        bpsElem.className = data.headline_cpi_delta_bps > 15 ? 'text-2xl font-black text-red-600' : (data.headline_cpi_delta_bps < -10 ? 'text-2xl font-black text-emerald-600' : 'text-2xl font-black text-blue-600');
        
        document.getElementById('simRecText').innerText = data.policy_recommendation;
        
        // Category impacts
        document.getElementById('simCatMetro').innerText = data.category_impacts['METRO_METRO'];
        document.getElementById('simCatTier2').innerText = data.category_impacts['METRO_TIER2'];
        document.getElementById('simCatHill').innerText = data.category_impacts['HILL_ISLAND'];
        document.getElementById('simCatUdan').innerText = data.category_impacts['UDAN_RCS'];
    } catch (e) {
        console.error('Simulation error:', e);
    }
}
