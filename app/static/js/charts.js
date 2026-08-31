/**
 * VayuDrishti Charting Suite (Chart.js Integration)
 */
let timeSeriesChart = null;
let leadTimeChart = null;
let categoryBarChart = null;
let hedonicImportanceChart = null;
let cpiComparisonChart = null;

function initTimeSeriesChart(historyData) {
    const ctx = document.getElementById('timeSeriesCanvas').getContext('2d');
    
    const labels = historyData.map(d => d.index_date);
    const laspeyres = historyData.map(d => d.laspeyres_index);
    const jevons = historyData.map(d => d.jevons_index);
    const hedonic = historyData.map(d => d.hedonic_index);
    
    if (timeSeriesChart) timeSeriesChart.destroy();
    
    timeSeriesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'DGCA-Weighted Laspeyres (Official)',
                    data: laspeyres,
                    borderColor: '#1e40af',
                    backgroundColor: 'rgba(30, 64, 175, 0.08)',
                    borderWidth: 2.5,
                    pointRadius: 0,
                    fill: true,
                    tension: 0.2
                },
                {
                    label: 'Hedonic Quality-Adjusted',
                    data: hedonic,
                    borderColor: '#059669',
                    borderWidth: 2,
                    borderDash: [4, 4],
                    pointRadius: 0,
                    tension: 0.2
                },
                {
                    label: 'Jevons Elementary Geometric Mean',
                    data: jevons,
                    borderColor: '#d97706',
                    borderWidth: 1.8,
                    pointRadius: 0,
                    tension: 0.2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { font: { size: 11, weight: 'bold' } } },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y} (Base=100.0)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 12, font: { size: 10 } }
                },
                y: {
                    title: { display: true, text: 'Index Value (2024 = 100.0)', font: { size: 11, weight: 'bold' } },
                    grid: { color: '#f1f5f9' },
                    min: 95
                }
            }
        }
    });
}

function initLeadTimeChart(leadData) {
    const ctx = document.getElementById('leadTimeCanvas').getContext('2d');
    
    const horizons = [0, 1, 3, 7, 15, 30, 60];
    const labels = ['D-0 (Same Day)', 'D-1 (Next Day)', 'D-3 (3 Days)', 'D-7 (1 Week)', 'D-15 (2 Weeks)', 'D-30 (1 Month)', 'D-60 (2 Months)'];
    const values = horizons.map(h => leadData[h] || 100.0);
    
    if (leadTimeChart) leadTimeChart.destroy();
    
    leadTimeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Airfare Index by Booking Horizon',
                data: values,
                backgroundColor: [
                    '#ef4444', '#f97316', '#f59e0b', '#3b82f6', '#2563eb', '#10b981', '#059669'
                ],
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const ratio = (context.parsed.y / 100.0).toFixed(2);
                            return `Multiplier vs Base: ${ratio}x`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    title: { display: true, text: 'Index Relatives (Base=100.0)' },
                    grid: { color: '#f1f5f9' }
                },
                x: { grid: { display: false } }
            }
        }
    });
}

function initCategoryBarChart(catData) {
    const ctx = document.getElementById('categoryBarCanvas').getContext('2d');
    
    const catLabels = {
        'METRO_METRO': 'Metro-to-Metro Trunk',
        'METRO_TIER2': 'Metro to Tier-2 Corridors',
        'HILL_ISLAND': 'Hill & Island Strategic',
        'UDAN_RCS': 'UDAN Regional Connectivity'
    };
    
    const keys = Object.keys(catData);
    const labels = keys.map(k => catLabels[k] || k);
    const values = keys.map(k => catData[k]);
    
    if (categoryBarChart) categoryBarChart.destroy();
    
    categoryBarChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Corridor Category Index',
                data: values,
                backgroundColor: ['#1e40af', '#3b82f6', '#dc2626', '#16a34a'],
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: {
                x: { min: 90, grid: { color: '#f1f5f9' } },
                y: { grid: { display: false } }
            }
        }
    });
}

function initHedonicCharts(hedonicData) {
    const ctx = document.getElementById('hedonicRadarCanvas').getContext('2d');
    const feat = hedonicData.feature_importance;
    
    if (hedonicImportanceChart) hedonicImportanceChart.destroy();
    
    hedonicImportanceChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(feat),
            datasets: [{
                data: Object.values(feat),
                backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } }
            }
        }
    });
}

function initCPIChart(cpiSeries) {
    const ctx = document.getElementById('cpiComparisonCanvas').getContext('2d');
    
    const labels = cpiSeries.map(d => d.month_year);
    const officialGeneral = cpiSeries.map(d => d.official_cpi_general);
    const augmentedGeneral = cpiSeries.map(d => d.nowcast_cpi_general);
    const transportAugmented = cpiSeries.map(d => d.augmented_cpi_transport);
    
    if (cpiComparisonChart) cpiComparisonChart.destroy();
    
    cpiComparisonChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Official CPI Headline (Lagged Monthly)',
                    data: officialGeneral,
                    borderColor: '#64748b',
                    borderWidth: 2,
                    pointRadius: 3
                },
                {
                    label: 'VayuDrishti CPI Headline Nowcast',
                    data: augmentedGeneral,
                    borderColor: '#2563eb',
                    borderWidth: 2.5,
                    pointRadius: 4,
                    backgroundColor: 'rgba(37, 99, 235, 0.05)',
                    fill: true
                },
                {
                    label: 'Augmented Transport Sub-Index (8.59% Weight)',
                    data: transportAugmented,
                    borderColor: '#ea580c',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' }
            },
            scales: {
                y: { grid: { color: '#f1f5f9' } },
                x: { grid: { display: false } }
            }
        }
    });
}
