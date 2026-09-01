/**
 * VayuDrishti Interactive GIS Network Map (Leaflet.js)
 */
let mapInstance = null;
let routePolylines = [];
let airportMarkers = [];

function initAirRouteMap(routes, airports) {
    if (!document.getElementById('leafletMap')) return;
    
    if (mapInstance) {
        mapInstance.remove();
    }
    
    // Center map on India (Nagpur approx coordinates [21.5, 78.9])
    mapInstance = L.map('leafletMap').setView([21.8, 79.5], 5);
    
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> | MoSPI VayuDrishti',
        maxZoom: 18
    }).addTo(mapInstance);
    
    // Plot Airports as custom circle markers
    Object.keys(airports).forEach(code => {
        const apt = airports[code];
        const color = apt.tier === 'Metro' ? '#1e3a8a' : (apt.tier === 'Hill_Island' ? '#dc2626' : (apt.tier === 'UDAN_RCS' ? '#16a34a' : '#d97706'));
        const radius = apt.tier === 'Metro' ? 7 : (apt.tier === 'Hill_Island' ? 6 : 5);
        
        const marker = L.circleMarker([apt.lat, apt.lon], {
            radius: radius,
            fillColor: color,
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9
        }).addTo(mapInstance);
        
        marker.bindPopup(`
            <div class="text-xs p-1">
                <div class="font-bold text-sm text-blue-900">${apt.name} (${code})</div>
                <div class="text-gray-600">${apt.city}, ${apt.state}</div>
                <div class="mt-1 font-semibold">Tier: <span class="text-indigo-600">${apt.tier}</span> | Region: ${apt.region}</div>
            </div>
        `);
        airportMarkers.push(marker);
    });
    
    // Draw Route Flight Arcs
    renderRouteLines(routes);
}

function renderRouteLines(routes, filterCat = 'ALL') {
    routePolylines.forEach(l => mapInstance.removeLayer(l));
    routePolylines = [];
    
    routes.forEach(r => {
        if (filterCat !== 'ALL' && r.category !== filterCat) return;
        
        const latlngs = [
            [r.origin_lat, r.origin_lon],
            [r.dest_lat, r.dest_lon]
        ];
        
        let color = '#3b82f6';
        let weight = 1.5;
        let opacity = 0.45;
        
        if (r.category === 'METRO_METRO') {
            color = '#1e40af';
            weight = 2.2;
            opacity = 0.6;
        } else if (r.category === 'HILL_ISLAND') {
            color = '#ef4444';
            weight = 2.0;
            opacity = 0.7;
        } else if (r.category === 'UDAN_RCS') {
            color = '#10b981';
            weight = 1.8;
            opacity = 0.6;
        }
        
        const polyline = L.polyline(latlngs, {
            color: color,
            weight: weight,
            opacity: opacity,
            dashArray: r.category === 'UDAN_RCS' ? '4, 4' : null
        }).addTo(mapInstance);
        
        polyline.bindPopup(`
            <div class="text-xs p-1">
                <div class="font-bold text-sm text-slate-800">${r.origin_city} (${r.origin}) &rarr; ${r.dest_city} (${r.destination})</div>
                <div class="text-gray-500">Category: <b>${r.category}</b> | Distance: <b>${r.distance_km} km</b></div>
                <div class="mt-1.5 grid grid-cols-2 gap-1 bg-slate-50 p-1.5 rounded border border-slate-200">
                    <div>Avg Fare: <span class="font-bold text-blue-700">&#8377;${r.current_avg_fare.toLocaleString()}</span></div>
                    <div>AFI Index: <span class="font-bold text-amber-600">${r.index_value}</span></div>
                    <div>HHI Index: <span class="font-bold text-slate-700">${r.hhi_index}</span></div>
                    <div>Market: <span class="font-bold text-indigo-600">${r.competition_status}</span></div>
                </div>
                <div class="mt-1 text-gray-600">Top Carrier: <b>${r.top_carrier}</b></div>
            </div>
        `);
        
        routePolylines.push(polyline);
    });
}
