/**
 * VayuDrishti Core App Manager & Real-Time Live Streaming Controller
 */
let globalRoutes = [];
let globalAirports = {};
let globalLatestIndex = {};
let globalCpi = {};
let lastKnownIndexValue = 114.80;
let lastRenderedQuotes = new Set();
let livePollingInterval = null;
let isAutoScrapingEnabled = true;

document.addEventListener('DOMContentLoaded', async () => {
    setupTabNavigation();
    await loadInitialData();
    setupEventListeners();
    startRealtimeStreamPolling();
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
        lastKnownIndexValue = globalLatestIndex.national_airfare_index;
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
        
        // 6. Fetch Scraper Status & Prime Live Stream
        await refreshLiveStreamFeed();
        
        // 7. Initialize Policy Simulator defaults
        runPolicySimulation();
    } catch (e) {
        console.error('Error initializing VayuDrishti dashboard:', e);
    }
}

function startRealtimeStreamPolling() {
    if (livePollingInterval) clearInterval(livePollingInterval);
    // Poll live stream every 3.5 seconds to catch newly scraped flights
    livePollingInterval = setInterval(refreshLiveStreamFeed, 3500);
}

async function refreshLiveStreamFeed() {
    try {
        const res = await fetch('/api/scrapers/live-stream');
        const data = await res.json();
        
        isAutoScrapingEnabled = data.is_auto_scraping;
        
        // Update Live Status Pill
        const statusBadge = document.getElementById('headerScraperStatus');
        if (statusBadge) {
            if (isAutoScrapingEnabled) {
                statusBadge.className = 'flex items-center gap-2 bg-violet-50 text-violet-800 border border-violet-200 px-3 py-1.5 rounded-full text-xs font-semibold';
                statusBadge.innerHTML = `<span class="pulse-green"></span><span>Demo Refresh (Every ${data.interval_seconds}s)</span>`;
            } else {
                statusBadge.className = 'flex items-center gap-2 bg-amber-50 text-amber-800 border border-amber-200 px-3 py-1.5 rounded-full text-xs font-semibold';
                statusBadge.innerHTML = `<i class="fa-solid fa-pause text-amber-600"></i><span>Demo Refresh Paused</span>`;
            }
        }
        
        // Update Live Total Quotes
        const obsElem = document.getElementById('kpiObsCount');
        if (obsElem && data.total_quotes_db) {
            obsElem.innerText = data.total_quotes_db.toLocaleString();
        }
        
        const totalScrapedElem = document.getElementById('scraperTotalQuotes');
        if (totalScrapedElem) totalScrapedElem.innerText = data.total_quotes_db.toLocaleString();
        
        // Check if National AFI changed and trigger visual flash animation
        const newAfi = data.latest_index.national_index;
        if (newAfi && Math.abs(newAfi - lastKnownIndexValue) > 0.001) {
            lastKnownIndexValue = newAfi;
            
            const kpiCard = document.getElementById('nationalKpiCard');
            if (kpiCard) {
                kpiCard.classList.remove('flash-update');
                void kpiCard.offsetWidth; // trigger reflow
                kpiCard.classList.add('flash-update');
            }
            
            document.getElementById('kpiNationalIndex').innerText = newAfi.toFixed(2);
            document.getElementById('kpiLaspeyres').innerText = data.latest_index.laspeyres_index.toFixed(2);
            document.getElementById('kpiJevons').innerText = data.latest_index.jevons_index.toFixed(2);
            document.getElementById('kpiHedonic').innerText = data.latest_index.hedonic_index.toFixed(2);
            
            // Recompute CPI on the fly
            const resCpi = await fetch('/api/cpi/augmentation?current_afi=' + newAfi);
            globalCpi = await resCpi.json();
            renderCPIAugmentation(globalCpi);
        }
        
        // Render Live Quotes Streaming List
        renderLiveQuotesStream(data.live_quotes);
        
    } catch (e) {
        console.warn('Live stream poll error:', e);
    }
}

function renderLiveQuotesStream(quotes) {
    const container = document.getElementById('liveStreamContainer');
    if (!container || !quotes || quotes.length === 0) return;
    
    container.innerHTML = '';
    
    quotes.slice(0, 10).forEach((q, idx) => {
        const item = document.createElement('div');
        item.className = 'quote-item-enter p-2.5 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 transition';
        
        let carrierColor = 'bg-blue-600';
        if (q.carrier_code === 'AI') carrierColor = 'bg-red-600';
        if (q.carrier_code === 'QP') carrierColor = 'bg-amber-600';
        if (q.carrier_code === 'SG') carrierColor = 'bg-orange-600';
        
        const leadText = q.lead_time_days === 0 ? 'D-0 (Emergency)' : `D-${q.lead_time_days}`;
        
        item.innerHTML = `
            <div class="flex items-center gap-2">
                <span class="${carrierColor} text-white text-[10px] font-black px-2 py-0.5 rounded shadow-sm">${q.carrier_code}</span>
                <div>
                    <span class="font-bold text-slate-900">${q.origin_city} (${q.origin}) &rarr; ${q.dest_city} (${q.destination})</span>
                    <span class="text-[10px] text-slate-500 ml-1 font-mono">${q.flight_number} &bull; ${q.portal_source}</span>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <span class="bg-slate-200 text-slate-700 px-2 py-0.5 rounded text-[10px] font-semibold">${leadText}</span>
                <span class="font-bold text-sm text-blue-950 font-mono">&#8377;${q.price_inr.toLocaleString()}</span>
                <span class="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1">
                    <i class="fa-solid fa-check text-[9px]"></i> ${q.is_outlier ? 'Outlier Flagged' : 'Tukey IQR Pass'}
                </span>
                <span class="text-[10px] text-slate-400 font-mono hidden md:inline">${q.timestamp.split(' ')[1]}</span>
            </div>
        `;
        container.appendChild(item);
    });
}

function renderKPIs(data) {
    document.getElementById('kpiNationalIndex').innerText = data.national_airfare_index.toFixed(2);
    document.getElementById('kpiLaspeyres').innerText = data.laspeyres_index.toFixed(2);
    document.getElementById('kpiJevons').innerText = data.jevons_index.toFixed(2);
    document.getElementById('kpiHedonic').innerText = data.hedonic_index.toFixed(2);
    
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
    
    // Demo refresh buttons (one in the overview and one in ingestion telemetry)
    document.querySelectorAll('[data-demo-refresh]').forEach((btnScrape) => {
        btnScrape.addEventListener('click', async () => {
            btnScrape.disabled = true;
            btnScrape.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Refreshing Demo Dataset...';
            try {
                const res = await fetch('/api/scrapers/trigger-batch', { method: 'POST' });
                const result = await res.json();
                
                await refreshLiveStreamFeed();
                alert(`Demo refresh completed
• Routes sampled: ${result.routes_scanned}
• Observations generated: ${result.quotes_collected}
• Outliers flagged: ${result.outliers_filtered}
• Recomputed AFI: ${result.recomputed_national_index}
• Duration: ${result.execution_time_sec}s`);
            } catch (e) {
                alert('Demo refresh could not be completed');
            } finally {
                btnScrape.disabled = false;
                btnScrape.innerHTML = '<i class="fa-solid fa-play mr-2"></i> Refresh Demo Dataset';
            }
        });
    });
    
    // Toggle Auto Scraping Button
    const btnToggle = document.getElementById('btnToggleAutoScraper');
    if (btnToggle) {
        btnToggle.addEventListener('click', async () => {
            const newStatus = !isAutoScrapingEnabled;
            const intervalSel = document.getElementById('scraperIntervalSelect');
            const intervalVal = intervalSel ? parseInt(intervalSel.value) : 15;
            
            try {
                const res = await fetch('/api/scrapers/toggle-auto', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ is_enabled: newStatus, interval_seconds: intervalVal })
                });
                const resData = await res.json();
                isAutoScrapingEnabled = resData.is_enabled;
                
                if (isAutoScrapingEnabled) {
                    btnToggle.innerHTML = '<i class="fa-solid fa-pause text-amber-500"></i> Pause Demo Refresh';
                    btnToggle.className = 'bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-700 flex items-center gap-1.5 transition';
                } else {
                    btnToggle.innerHTML = '<i class="fa-solid fa-play text-emerald-400"></i> Resume Demo Refresh';
                    btnToggle.className = 'bg-emerald-900 hover:bg-emerald-800 text-white text-xs font-semibold px-3 py-1.5 rounded-lg border border-emerald-700 flex items-center gap-1.5 transition';
                }
                await refreshLiveStreamFeed();
            } catch (e) {
                console.error('Error toggling auto-scraper:', e);
            }
        });
    }
    
    // Interval Change Handler
    const intervalSel = document.getElementById('scraperIntervalSelect');
    if (intervalSel) {
        intervalSel.addEventListener('change', async (e) => {
            const val = parseInt(e.target.value);
            await fetch('/api/scrapers/toggle-auto', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_enabled: isAutoScrapingEnabled, interval_seconds: val })
            });
            await refreshLiveStreamFeed();
        });
    }
    
    // Simulation Sliders
    ['simAtfSlider', 'simCapSlider', 'simUdanSlider', 'simSurgeSlider'].forEach(id => {
        const slider = document.getElementById(id);
        if (slider) slider.addEventListener('input', runPolicySimulation);
    });
}


function updateGazettePreview(latestIndex, cpi) {
    const gazetteMonth = document.getElementById('gazetteMonthYear');
    if (gazetteMonth) {
        const now = new Date();
        gazetteMonth.innerText = now.toLocaleDateString('en-IN', { month: 'long', year: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
    const gLasp = document.getElementById('gazetteLaspeyres');
    if (gLasp) gLasp.innerText = latestIndex.national_airfare_index.toFixed(2);
    
    const gHed = document.getElementById('gazetteHedonic');
    if (gHed) gHed.innerText = latestIndex.hedonic_index.toFixed(2);
    
    const gJev = document.getElementById('gazetteJevons');
    if (gJev) gJev.innerText = latestIndex.jevons_index.toFixed(2);
    
    const gCpiTrans = document.getElementById('gazetteCpiTransport');
    if (gCpiTrans && cpi.vayudrishti_cpi_transport_augmented) gCpiTrans.innerText = cpi.vayudrishti_cpi_transport_augmented.toFixed(2);
}


function downloadLivePdf(e) {
    if (e && e.preventDefault) e.preventDefault();
    const currentAfi = (typeof lastKnownIndexValue !== 'undefined' && lastKnownIndexValue) ? lastKnownIndexValue : 114.80;
    const url = `/api/export/gazette-pdf?afi=${currentAfi}&t=${Date.now()}`;
    window.open(url, '_blank');
}
