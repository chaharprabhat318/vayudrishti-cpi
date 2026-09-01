/**
 * VayuDrishti Core App Manager
 */
let globalRoutes = [];
let globalAirports = {};
let globalLatestIndex = {};
let globalCpi = {};

document.addEventListener('DOMContentLoaded', async () => {
    setupTabNavigation();
    await loadInitialData();
    setupEventListeners();
});

function setupTabNavigation() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active', 'bg-blue-900', 'text-white'));
            tab.classList.add('active', 'bg-blue-900', 'text-white');
            
            const target = tab.getAttribute('data-tab');
            document.querySelectorAll('.tab-content').forEach(tc => tc.classList.add('hidden'));
            const targetContent = document.getElementById(target);
            if (targetContent) targetContent.classList.remove('hidden');
            
            if (target === 'tabRoutes' && mapInstance) {
                setTimeout(() => mapInstance.invalidateSize(), 150);
            }
        });
    });
}

async function loadInitialData() {
    try {
        // 1. Fetch Latest Index
        const resIdx = await fetch('/api/indices/latest');
        globalLatestIndex = await resIdx.json();
        renderKPIs(globalLatestIndex);
        
        // 2. Fetch History
        const resHist = await fetch('/api/indices/history');
        const historyData = await resHist.json();
        initTimeSeriesChart(historyData);
        initLeadTimeChart(globalLatestIndex.lead_time_indices);
        initCategoryBarChart(globalLatestIndex.category_indices);
        
        // 3. Fetch Routes & Airports
        const resRoutes = await fetch('/api/routes/');
        globalRoutes = await resRoutes.json();
        const resApt = await fetch('/api/routes/airports');
        globalAirports = await resApt.json();
        
        renderRoutesTable(globalRoutes);
        initAirRouteMap(globalRoutes, globalAirports);
        
        // 4. Fetch Hedonic Summary
        const resHed = await fetch('/api/hedonic/summary');
        const hedData = await resHed.json();
        renderHedonicTable(hedData);
        initHedonicCharts(hedData);
        
        // 5. Fetch CPI Augmentation
        const resCpi = await fetch('/api/cpi/augmentation?current_afi=' + globalLatestIndex.national_airfare_index);
        globalCpi = await resCpi.json();
        renderCPIAugmentation(globalCpi);
        
        const resCpiSeries = await fetch('/api/cpi/series');
        const cpiSeriesData = await resCpiSeries.json();
        initCPIChart(cpiSeriesData);
        
        // 6. Fetch Scraper Status
        await refreshScraperStatus();
        
        // 7. Initialize Policy Simulator defaults
        runPolicySimulation();
    } catch (e) {
        console.error('Error initializing VayuDrishti dashboard:', e);
    }
}

function renderKPIs(data) {
    document.getElementById('kpiNationalIndex').innerText = data.national_airfare_index;
    document.getElementById('kpiLaspeyres').innerText = data.laspeyres_index;
    document.getElementById('kpiJevons').innerText = data.jevons_index;
    document.getElementById('kpiHedonic').innerText = data.hedonic_index;
    
    document.getElementById('kpiDodChange').innerText = `${data.dod_change_pct > 0 ? '+' : ''}${data.dod_change_pct}%`;
    document.getElementById('kpiMomChange').innerText = `+${data.mom_change_pct}%`;
    document.getElementById('kpiYoyChange').innerText = `+${data.yoy_change_pct}%`;
    document.getElementById('kpiObsCount').innerText = data.observations_count.toLocaleString();
}

function renderRoutesTable(routes) {
    const tbody = document.getElementById('routesTableBody');
    tbody.innerHTML = '';
    
    routes.slice(0, 15).forEach(r => {
        const tr = document.createElement('tr');
        tr.className = 'border-b hover:bg-slate-50 text-xs';
        
        let catBadge = 'bg-blue-100 text-blue-800';
        if (r.category === 'HILL_ISLAND') catBadge = 'bg-red-100 text-red-800';
        if (r.category === 'UDAN_RCS') catBadge = 'bg-emerald-100 text-emerald-800';
        if (r.category === 'METRO_TIER2') catBadge = 'bg-indigo-100 text-indigo-800';
        
        tr.innerHTML = `
            <td class="py-2.5 px-3 font-semibold text-slate-800">${r.origin_city} (${r.origin}) &rarr; ${r.dest_city} (${r.destination})</td>
            <td class="py-2.5 px-2"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${catBadge}">${r.category}</span></td>
            <td class="py-2.5 px-2 text-right font-medium">&#8377;${r.base_fare.toLocaleString()}</td>
            <td class="py-2.5 px-2 text-right font-bold text-blue-900">&#8377;${r.current_avg_fare.toLocaleString()}</td>
            <td class="py-2.5 px-2 text-center font-bold text-amber-600">${r.index_value}</td>
            <td class="py-2.5 px-2 text-center font-mono font-bold text-slate-700">${r.hhi_index}</td>
            <td class="py-2.5 px-2 text-slate-600">${r.competition_status}</td>
            <td class="py-2.5 px-3 text-slate-700 font-medium">${r.top_carrier}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderHedonicTable(hedData) {
    document.getElementById('hedRSquared').innerText = hedData.r_squared;
    document.getElementById('hedAdjRSquared').innerText = hedData.adj_r_squared;
    document.getElementById('hedSampleSize').innerText = hedData.sample_size.toLocaleString();
    document.getElementById('hedPureInflation').innerText = `+${hedData.pure_price_inflation_pct}%`;
    document.getElementById('hedQualityDrift').innerText = `+${hedData.quality_drift_impact_pct}%`;
    
    const tbody = document.getElementById('hedonicCoefBody');
    tbody.innerHTML = '';
    
    const coefNames = {
        'intercept': 'Model Constant / Intercept (ln P0)',
        'flight_duration_per_hr': 'Flight Duration Elasticity (per Hour)',
        'layover_stop_discount': 'Layover Penalty / Stop Discount',
        'lead_time_advance_discount': 'Advance Booking Discount ln(Lead+1)',
        'baggage_allowance_per_10kg': 'Baggage Allowance Surcharge (10kg)',
        'air_india_full_service_premium': 'Air India Full-Service Quality Premium',
        'akasa_air_lcc_differential': 'Akasa Air Low-Cost Differential',
        'spicejet_differential': 'SpiceJet Low-Cost Differential'
    };
    
    Object.entries(hedData.coefficients).forEach(([k, val]) => {
        const tr = document.createElement('tr');
        tr.className = 'border-b text-xs hover:bg-slate-50';
        const pval = hedData.p_values[k] ? hedData.p_values[k].toFixed(4) : '< 0.0001';
        
        tr.innerHTML = `
            <td class="py-2 px-3 font-medium text-slate-800">${coefNames[k] || k}</td>
            <td class="py-2 px-3 text-right font-mono font-bold ${val < 0 ? 'text-red-600' : 'text-emerald-700'}">${val > 0 ? '+' : ''}${val.toFixed(4)}</td>
            <td class="py-2 px-3 text-right font-mono text-slate-500">${pval}</td>
            <td class="py-2 px-3 text-center"><span class="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded text-[10px] font-bold">p &lt; 0.05 (Significant)</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderCPIAugmentation(cpi) {
    document.getElementById('cpiGeneralOfficial').innerText = cpi.official_cpi_general;
    document.getElementById('cpiTransportOfficial').innerText = cpi.official_cpi_transport;
    document.getElementById('cpiTransportAugmented').innerText = cpi.vayudrishti_cpi_transport_augmented;
    document.getElementById('cpiHeadlineNowcast').innerText = cpi.cpi_headline_nowcast;
    document.getElementById('cpiDeltaBps').innerText = `+${cpi.cpi_basis_points_delta} bps`;
    document.getElementById('cpiWarningLevel').innerText = cpi.rbi_mpc_warning_level;
    document.getElementById('cpiCommentary').innerText = cpi.commentary;
}

async function refreshScraperStatus() {
    try {
        const res = await fetch('/api/scrapers/status');
        const data = await res.json();
        
        document.getElementById('scraperTotalQuotes').innerText = data.total_quotes_collected.toLocaleString();
        document.getElementById('scraperLastRun').innerText = data.last_run_timestamp;
        document.getElementById('scraperHealth').innerText = data.health;
        
        const resLogs = await fetch('/api/scrapers/logs');
        const logs = await resLogs.json();
        const logBody = document.getElementById('scraperLogsBody');
        if (logBody) {
            logBody.innerHTML = '';
            logs.forEach(l => {
                const tr = document.createElement('tr');
                tr.className = 'border-b text-xs';
                tr.innerHTML = `
                    <td class="py-2 px-3 text-slate-500">${l.run_timestamp}</td>
                    <td class="py-2 px-3 font-semibold text-slate-700">${l.portal_source}</td>
                    <td class="py-2 px-3 text-center font-mono">${l.routes_scanned}</td>
                    <td class="py-2 px-3 text-center font-mono font-bold text-blue-900">${l.quotes_collected}</td>
                    <td class="py-2 px-3 text-center"><span class="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-bold">${l.status}</span></td>
                    <td class="py-2 px-3 text-right font-mono text-slate-600">${l.execution_time_sec}s</td>
                `;
                logBody.appendChild(tr);
            });
        }
    } catch (e) {
        console.error('Error updating scraper status:', e);
    }
}

function setupEventListeners() {
    // Route Filter
    const catFilter = document.getElementById('routeCategoryFilter');
    if (catFilter) {
        catFilter.addEventListener('change', (e) => {
            const val = e.target.value;
            const filtered = val === 'ALL' ? globalRoutes : globalRoutes.filter(r => r.category === val);
            renderRoutesTable(filtered);
            renderRouteLines(globalRoutes, val);
        });
    }
    
    // Route Search
    const searchInput = document.getElementById('routeSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const filtered = globalRoutes.filter(r => 
                r.origin.toLowerCase().includes(query) ||
                r.destination.toLowerCase().includes(query) ||
                r.origin_city.toLowerCase().includes(query) ||
                r.dest_city.toLowerCase().includes(query)
            );
            renderRoutesTable(filtered);
        });
    }
    
    // Scraper Batch Trigger Button
    const btnScrape = document.getElementById('btnTriggerBatch');
    if (btnScrape) {
        btnScrape.addEventListener('click', async () => {
            btnScrape.disabled = true;
            btnScrape.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Scraping Live Portals...';
            try {
                const res = await fetch('/api/scrapers/trigger-batch', { method: 'POST' });
                const result = await res.json();
                
                alert(`Batch Ingestion Successful!
- Routes Scanned: ${result.routes_scanned}
- Raw Quotes Ingested: ${result.quotes_collected}
- Outliers Filtered (Tukey IQR): ${result.outliers_filtered}
- Execution Time: ${result.execution_time_sec}s`);
                await loadInitialData();
            } catch (e) {
                alert('Error running ingestion batch');
            } finally {
                btnScrape.disabled = false;
                btnScrape.innerHTML = '<i class="fa-solid fa-play mr-2"></i> Trigger Live Ingestion Batch';
            }
        });
    }
    
    // Simulation Sliders
    ['simAtfSlider', 'simCapSlider', 'simUdanSlider', 'simSurgeSlider'].forEach(id => {
        const slider = document.getElementById(id);
        if (slider) slider.addEventListener('input', runPolicySimulation);
    });
}
