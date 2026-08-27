let map;
let markerClusterGroup;
let allAirportsData = [];
let currentlyFilteredAirports = [];
let selectedAirport = null;
let userRatingsMap = {};
let currentSettings = { auto_scan_on_startup: true, scan_paths: [] };
let lastFocusedIcao = null;

// Currency & Investment Engine
let selectedCurrency = 'EUR';
const CURRENCY_SYMBOLS = { EUR: '€', USD: '$', GBP: '£' };
const CURRENCY_RATES = { EUR: 1.0, USD: 1.09, GBP: 0.85 };

// Conflict Navigation Engine
let currentConflictIndex = 0;

// Multi-select Sets
const ALL_PRICING_LIST = ['Payware', 'Freeware / Flightsim.to', 'Asobo', 'Default'];
const ALL_SOURCES_LIST = ['asobo', 'Community', 'StreamedPackages', 'Official'];
const ALL_TYPES_LIST = ['International', 'Regional', 'General Aviation', 'Heli / Water'];

let selectedPricing = new Set(['Payware', 'Freeware / Flightsim.to', 'Asobo']);
let selectedSources = new Set(ALL_SOURCES_LIST);
let selectedTypes = new Set(ALL_TYPES_LIST);
let selectedMinRating = 0; // 0 = All ratings
let selectedGsxFilter = 'all'; // 'all', 'with', 'none'
let selectedAirline = null;
let activeRouteOrigin = null;
let activeRouteLinesGroup = null;

// Flight Optimizer Engine State
let flightOriginAirport = null;
let flightDestAirport = null;
let isFlightOptimizerActive = false;
let flightRouteLineGroup = null;

function filterByAirline(airlineName) {
    const originAp = selectedAirport;
    if (!originAp) return;

    const isSameAirline = (selectedAirline === airlineName && activeRouteOrigin && activeRouteOrigin.icao === originAp.icao);

    // Always reset current airline selection first
    selectedAirline = null;
    activeRouteOrigin = null;

    if (isSameAirline) {
        // Toggle off current airline
        filterAirports();
        updateFilterUI();
        showAirportDetails(originAp);
        return;
    }

    // Check matching installed destination sceneries for the new airline
    const destIcaos = (originAp.routes && originAp.routes[airlineName]) || [];
    const matchingInstalledDests = allAirportsData.filter(a => a.icao !== originAp.icao && destIcaos.includes(a.icao));

    if (matchingInstalledDests.length === 0) {
        // 0 installed destinations for this airline route -> reset map, clear top filter, pop modal!
        filterAirports();
        updateFilterUI();
        showAirportDetails(originAp);

        const destText = destIcaos.length > 0 ? ` (${destIcaos.join(', ')})` : '';
        showCustomModal({
            title: 'No Installed Destination',
            message: `You don't have any addon airport (Payware/Freeware) in your scenery collection for ${airlineName} from ${originAp.icao}${destText}.`,
            type: 'info',
            confirmText: 'OK'
        });
        return;
    }

    // Installed destination sceneries exist -> activate new airline filter!
    selectedAirline = airlineName;
    activeRouteOrigin = originAp;
    filterAirports();
    updateFilterUI();
    showAirportDetails(originAp);
}

function clearAirlineFilter() {
    selectedAirline = null;
    activeRouteOrigin = null;
    filterAirports();
    updateFilterUI();
    if (selectedAirport) {
        showAirportDetails(selectedAirport);
    }
}

/* ================= FLIGHT OPTIMIZER (MODE VOL & FPS BOOST) ================= */

let isSuppressingHoverPopups = false;

function suppressHoverPopupsTemporarily() {
    isSuppressingHoverPopups = true;
    if (map) map.closePopup();
    setTimeout(() => {
        isSuppressingHoverPopups = false;
    }, 500);
}

function setFlightOrigin(ap) {
    if (!ap) {
        flightOriginAirport = null;
    } else {
        if (flightDestAirport && flightDestAirport.icao === ap.icao) {
            flightDestAirport = null;
        }
        flightOriginAirport = ap;
    }
    updateFlightOptimizerUI();
    drawFlightOptimizerRoute();
    suppressHoverPopupsTemporarily();
}

function setFlightDest(ap) {
    if (!ap) {
        flightDestAirport = null;
    } else {
        if (flightOriginAirport && flightOriginAirport.icao === ap.icao) {
            flightOriginAirport = null;
        }
        flightDestAirport = ap;
    }
    updateFlightOptimizerUI();
    drawFlightOptimizerRoute();
    suppressHoverPopupsTemporarily();
}

function setFlightOriginByIcao(icao) {
    const ap = allAirportsData.find(a => a.icao === icao);
    if (ap) setFlightOrigin(ap);
}

function setFlightDestByIcao(icao) {
    const ap = allAirportsData.find(a => a.icao === icao);
    if (ap) setFlightDest(ap);
}

function clearFlightOrigin() {
    flightOriginAirport = null;
    updateFlightOptimizerUI();
    drawFlightOptimizerRoute();
    suppressHoverPopupsTemporarily();
}

function clearFlightDest() {
    flightDestAirport = null;
    updateFlightOptimizerUI();
    drawFlightOptimizerRoute();
    suppressHoverPopupsTemporarily();
}

function clearFlightSelection() {
    flightOriginAirport = null;
    flightDestAirport = null;
    isFlightOptimizerActive = false;
    if (flightRouteLineGroup) {
        flightRouteLineGroup.clearLayers();
    }
    updateFlightOptimizerUI();
    filterAirports();
}

function updateFlightOptimizerUI() {
    const bar = document.getElementById('flight-optimizer-bar');
    const originTag = document.getElementById('flight-origin-tag');
    const destTag = document.getElementById('flight-dest-tag');
    const badge = document.getElementById('flight-planner-badge');
    const optBtn = document.getElementById('btn-run-flight-opt');

    if (!bar) return;

    if (flightOriginAirport || flightDestAirport) {
        bar.classList.remove('hidden');
        bar.classList.add('flex');

        if (originTag) originTag.innerText = `DEP: ${flightOriginAirport ? flightOriginAirport.icao : '----'}`;
        if (destTag) destTag.innerText = `ARR: ${flightDestAirport ? flightDestAirport.icao : '----'}`;

        let count = 0;
        if (flightOriginAirport) count++;
        if (flightDestAirport) count++;
        if (badge) {
            badge.classList.remove('hidden');
            badge.innerText = count;
        }

        if (optBtn) {
            if (isFlightOptimizerActive) {
                optBtn.className = "px-3.5 py-1.5 rounded-xl bg-emerald-500 text-slate-950 font-black text-xs transition-all shadow-md shadow-emerald-500/30 flex items-center gap-1.5 cursor-pointer ring-2 ring-emerald-400 animate-pulse";
                optBtn.innerHTML = `<i class="fa-solid fa-check"></i> <span>Flight Active (+FPS)</span>`;
            } else {
                optBtn.className = "px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-black text-xs transition-all shadow-md shadow-emerald-500/20 flex items-center gap-1.5 cursor-pointer";
                optBtn.innerHTML = `<i class="fa-solid fa-bolt"></i> <span>Disable Rest (+FPS)</span>`;
            }
        }
    } else {
        bar.classList.add('hidden');
        bar.classList.remove('flex');
        if (badge) badge.classList.add('hidden');
    }
}

function drawFlightOptimizerRoute() {
    if (flightRouteLineGroup) {
        flightRouteLineGroup.clearLayers();
    } else {
        if (map) flightRouteLineGroup = L.layerGroup().addTo(map);
    }

    if (!flightOriginAirport || !flightDestAirport || !flightRouteLineGroup) return;

    const lat1 = flightOriginAirport.lat;
    const lon1 = flightOriginAirport.lon;
    const lat2 = flightDestAirport.lat;
    const lon2 = flightDestAirport.lon;

    if (!lat1 || !lon1 || !lat2 || !lon2) return;

    const arcPoints = createBezierArcPoints(lat1, lon1, lat2, lon2, 35);

    // Draw glowing flight route line (Emerald green gradient glow)
    const glowLine = L.polyline(arcPoints, {
        color: '#10b981', // Neon Emerald
        weight: 3.5,
        opacity: 0.9,
        smoothFactor: 1
    });

    glowLine.addTo(flightRouteLineGroup);
}

async function executeFlightOptimizer() {
    const keepIcaos = [];
    if (flightOriginAirport) keepIcaos.push(flightOriginAirport.icao);
    if (flightDestAirport) keepIcaos.push(flightDestAirport.icao);

    if (keepIcaos.length === 0) {
        showCustomModal("Select Departure & Arrival", "Please select at least one Departure or Arrival airport before running Flight Optimizer.", "info");
        return;
    }

    const routeText = keepIcaos.join(' ➔ ');
    showCustomModal(
        `Optimizing Flight (${routeText})`,
        `Disabling all other sceneries to maximize MSFS performance...`,
        "info"
    );

    try {
        if (window.pywebview) {
            const resRaw = await window.pywebview.api.optimize_flight_mode(JSON.stringify(keepIcaos));
            const res = JSON.parse(resRaw);
            if (res.status === 'ok') {
                isFlightOptimizerActive = true;
                if (res.airports && res.airports.length > 0) {
                    allAirportsData = res.airports;
                }
                updateStats(allAirportsData);
                updateFlightOptimizerUI();
                filterAirports();
                showCustomModal(
                    "Flight Optimizer Active! 🚀",
                    `Kept ${keepIcaos.join(' & ')} active.\nDisabled ${res.disabled_count} other sceneries for maximum FPS during your flight!`,
                    "success"
                );
            } else {
                showCustomModal("Optimization Error", res.message || "Failed to optimize sceneries.", "error");
            }
        }
    } catch (err) {
        console.error("Failed to execute flight optimizer:", err);
        showCustomModal("Error", "Flight Optimizer execution failed: " + err, "error");
    }
}

async function executeRestoreAllSceneries() {
    // Clear all departure & arrival flight selections completely
    flightOriginAirport = null;
    flightDestAirport = null;
    isFlightOptimizerActive = false;
    if (flightRouteLineGroup) {
        flightRouteLineGroup.clearLayers();
    }
    updateFlightOptimizerUI();
    filterAirports();

    showCustomModal(
        "Restoring All Sceneries...",
        "Re-enabling all previously disabled scenery packages...",
        "info"
    );

    try {
        if (window.pywebview) {
            const resRaw = await window.pywebview.api.restore_all_sceneries();
            const res = JSON.parse(resRaw);
            if (res.status === 'ok') {
                allAirportsData = res.airports;
                updateStats(allAirportsData);
                updateFlightOptimizerUI();
                filterAirports();
                showCustomModal(
                    "All Sceneries Restored! 🟢",
                    `Successfully re-enabled ${res.re_enabled_count} sceneries. All your add-ons are now active.`,
                    "success"
                );
            } else {
                showCustomModal("Restore Error", res.message || "Failed to restore sceneries.", "error");
            }
        }
    } catch (err) {
        console.error("Failed to restore sceneries:", err);
        showCustomModal("Error", "Restore execution failed: " + err, "error");
    }
}

function executeFlightOptimizerQuickPrompt() {
    if (selectedAirport) {
        if (!flightOriginAirport) {
            setFlightOrigin(selectedAirport);
            showCustomModal("Departure Airport Set 🛫", `Set ${selectedAirport.icao} as Departure airport. Now select an Arrival airport and click 'Disable Rest (+FPS)'!`, "info");
        } else if (!flightDestAirport && selectedAirport.icao !== flightOriginAirport.icao) {
            setFlightDest(selectedAirport);
            showCustomModal("Arrival Airport Set 🛬", `Set ${selectedAirport.icao} as Arrival airport. Click 'Disable Rest (+FPS)' on the bottom bar to launch Flight Mode!`, "info");
        } else {
            updateFlightOptimizerUI();
        }
    } else {
        updateFlightOptimizerUI();
        showCustomModal("Flight Optimizer 🚀", "Select a Departure airport and an Arrival airport from the map/drawer, then click 'Disable Rest (+FPS)' to disable all other sceneries during your flight!", "info");
    }
}

// Initialize App
let isAppInitialized = false;

async function ensureAppLoaded() {
    if (isAppInitialized || allAirportsData.length > 0) return;

    for (let i = 0; i < 50; i++) {
        if (window.pywebview && window.pywebview.api) {
            isAppInitialized = true;
            await loadInitialAppData();
            return;
        }
        await new Promise(r => setTimeout(r, 100));
    }

    if (!isAppInitialized && allAirportsData.length === 0) {
        isAppInitialized = true;
        await loadInitialAppData();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    renderStarRatingWidget(0);
    renderFilterStarWidget(0);
    startCurrencyCarousel();
    ensureAppLoaded();
});

window.addEventListener('pywebviewready', async () => {
    await ensureAppLoaded();
});

function initMap() {
    map = L.map('map', {
        center: [46.2276, 2.2137], // Default view Europe
        zoom: 5,
        zoomControl: false
    });

    L.control.zoom({ position: 'topright' }).addTo(map);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
        maxZoom: 16
    }).addTo(map);

    markerClusterGroup = L.markerClusterGroup({
        chunkedLoading: true,
        maxClusterRadius: 40,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true
    });

    map.addLayer(markerClusterGroup);
}

async function loadInitialAppData() {
    try {
        if (!map) initMap();
        if (window.pywebview && window.pywebview.api) {
            try {
                const cfgStr = await window.pywebview.api.get_settings();
                if (cfgStr) {
                    currentSettings = JSON.parse(cfgStr);
                    loadSimBriefSettingsUI();
                }
            } catch(e) {
                console.warn("Settings loading warning:", e);
            }

            try {
                const rStr = await window.pywebview.api.get_ratings();
                if (rStr) {
                    userRatingsMap = JSON.parse(rStr);
                }
            } catch(e) {
                console.warn("Ratings loading warning:", e);
            }
        }
        await loadAirportsData();
    } catch (e) {
        console.error("Error loading app initial data:", e);
        await loadAirportsData();
    }
}

function updateSplashProgress(percent, text, folder) {
    const bar = document.getElementById('splash-progress-bar');
    const pText = document.getElementById('splash-percent-text');
    const sText = document.getElementById('splash-status-text');
    const fText = document.getElementById('splash-folder-text');

    if (bar) bar.style.width = `${percent}%`;
    if (pText) pText.innerText = `${percent}%`;
    if (sText && text) sText.innerText = text;
    if (fText && folder) fText.innerText = folder;
}

function hideSplashScreen() {
    const splash = document.getElementById('splash-screen');
    if (splash) {
        updateSplashProgress(100, "Ready!", "Scan Complete");
        setTimeout(() => {
            splash.style.opacity = '0';
            setTimeout(() => {
                splash.style.display = 'none';
            }, 700);
        }, 300);
    }
}

async function loadAirportsData() {
    try {
        updateSplashProgress(25, "Loading airports database...", "Airports DB");
        let response;
        if (window.pywebview) {
            updateSplashProgress(35, "Loading user configuration...", "Settings & Credentials");
            try {
                const settingsStr = await window.pywebview.api.get_settings();
                if (settingsStr) {
                    currentSettings = JSON.parse(settingsStr);
                    loadSimBriefSettingsUI();
                    const st = currentSettings.settings || currentSettings;
                    if (st && st.flight_mode) {
                        updateFlightModeBannerUI(st.flight_mode);
                    }
                }
            } catch(e) {
                console.warn("Could not load settings on startup:", e);
            }

            updateSplashProgress(55, "Scanning MSFS packages & GSX profiles...", "Community & OneStore");
            const dataStr = await window.pywebview.api.get_airports();
            updateSplashProgress(85, "Parsing scenery packages...", "Rendering Map");
            allAirportsData = JSON.parse(dataStr);
        } else {
            response = await fetch('/api/airports');
            if (!response.ok) {
                response = await fetch('installed_airports.json');
            }
            allAirportsData = await response.json();
        }

        // Apply loaded user ratings to allAirportsData
        allAirportsData.forEach(ap => {
            if (userRatingsMap[ap.icao] !== undefined) {
                ap.rating = userRatingsMap[ap.icao];
            } else {
                ap.rating = ap.rating || 0;
            }
        });

        updateStats(allAirportsData);
        filterAirports();
        hideSplashScreen();
    } catch (err) {
        console.error("Failed to load airports:", err);
        hideSplashScreen();
    }
}

function formatCurrency(amountEur) {
    const rate = CURRENCY_RATES[selectedCurrency] || 1.0;
    const symbol = CURRENCY_SYMBOLS[selectedCurrency] || '€';
    const val = (amountEur || 0) * rate;
    return `${symbol}${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function setCurrency(curr) {
    selectedCurrency = curr;
    ['EUR', 'USD', 'GBP'].forEach(c => {
        const btn = document.getElementById(`curr-btn-${c}`);
        if (btn) {
            if (c === curr) {
                btn.className = "font-bold text-emerald-400";
            } else {
                btn.className = "text-slate-500 hover:text-slate-300";
            }
        }
    });
    updateStats(allAirportsData);
    if (selectedAirport) {
        showAirportDetails(selectedAirport);
    }
}

function updateConflictNavigator() {
    const conflictAirports = allAirportsData.filter(a => a.has_conflict);
    const pill = document.getElementById('conflict-nav-pill');
    const counter = document.getElementById('conflict-nav-counter');
    const indexDisplay = document.getElementById('conflict-nav-index');

    if (!pill) return;

    if (conflictAirports.length > 0) {
        pill.classList.remove('hidden');
        counter.innerText = conflictAirports.length;
        if (currentConflictIndex >= conflictAirports.length) {
            currentConflictIndex = 0;
        }
        indexDisplay.innerText = `${currentConflictIndex + 1}/${conflictAirports.length}`;
    } else {
        pill.classList.add('hidden');
        currentConflictIndex = 0;
    }
}

function navigateConflict(direction) {
    const conflictAirports = allAirportsData.filter(a => a.has_conflict);
    if (conflictAirports.length === 0) return;

    currentConflictIndex += direction;
    if (currentConflictIndex >= conflictAirports.length) {
        currentConflictIndex = 0;
    } else if (currentConflictIndex < 0) {
        currentConflictIndex = conflictAirports.length - 1;
    }

    const targetAp = conflictAirports[currentConflictIndex];
    document.getElementById('conflict-nav-index').innerText = `${currentConflictIndex + 1}/${conflictAirports.length}`;
    
    focusAirportWithAnimation(targetAp);
}

let currencyList = ['EUR', 'USD', 'GBP'];
let currencyIndex = 0;
let currencyInterval = null;
let isCurrencyCarouselPaused = false;

function startCurrencyCarousel() {
    if (currencyInterval) clearInterval(currencyInterval);
    currencyInterval = setInterval(() => {
        if (isCurrencyCarouselPaused) return;
        currencyIndex = (currencyIndex + 1) % currencyList.length;
        selectedCurrency = currencyList[currencyIndex];
        updateInvestmentBanner();
        if (selectedAirport) {
            showAirportDetails(selectedAirport);
        }
    }, 10000); // 10 seconds per currency
}

function pauseCurrencyCarousel() {
    isCurrencyCarouselPaused = true;
}

function resumeCurrencyCarousel() {
    setTimeout(() => {
        const inputEl = document.getElementById('drawer-price-input');
        if (document.activeElement !== inputEl) {
            isCurrencyCarouselPaused = false;
        }
    }, 1500);
}

function updateInvestmentBanner() {
    let totalSpentEur = 0;
    let paywareCount = 0;
    const processedBundles = new Set();

    allAirportsData.forEach(ap => {
        const pt = ap.pricing_type || (ap.is_asobo_official ? "Asobo / MS" : "Freeware / Flightsim.to");
        if (pt === "Payware" || ap.is_payware) {
            paywareCount++;
            if (ap.is_bundle || ap.bundle_id) {
                const bKey = ap.bundle_id || ap.package_name;
                if (!processedBundles.has(bKey)) {
                    processedBundles.add(bKey);
                    totalSpentEur += (ap.bundle_total_price || 39.00);
                }
            } else {
                totalSpentEur += (ap.price_eur || 0);
            }
        }
    });

    const bannerEl = document.getElementById('investment-banner-text');
    const cardEl = document.getElementById('investment-card');

    if (bannerEl) {
        const formatted = formatCurrency(totalSpentEur);
        bannerEl.innerText = formatted;
    }

    if (cardEl) {
        const avgPriceEur = paywareCount > 0 ? (totalSpentEur / paywareCount) : 0;
        const avgFormatted = formatCurrency(avgPriceEur);
        cardEl.title = `Based on single sceneries & bundle packs (Avg ${avgFormatted}/scenery across ${paywareCount} payware sceneries).`;
    }
}

function getAirportPricingType(ap) {
    const pt = ap.pricing_type || '';
    const v = (ap.vendor || '').toLowerCase();
    
    if (ap.is_default || pt === 'Default') {
        return 'Default';
    }
    if (pt === 'Payware' || ap.is_payware) {
        return 'Payware';
    }
    if (ap.is_asobo_official || pt === 'Asobo' || pt === 'Asobo / MS' || v.includes('asobo') || v.includes('microsoft')) {
        return 'Asobo';
    }
    return 'Freeware / Flightsim.to';
}

function getAirportCategory(ap) {
    // If all installed 3rd-party/Asobo packages for this airport are disabled, it falls back to Default MSFS!
    const allSourcesDisabled = ap.all_sources && ap.all_sources.length > 0 && ap.all_sources.every(s => s.is_disabled);
    if (allSourcesDisabled) return 'DEFAULT';

    const pt = getAirportPricingType(ap);
    if (pt === 'Default') return 'DEFAULT';
    if (pt === 'Asobo') return 'ASOBO';
    if (pt === 'Payware') return 'PAYWARE';
    return 'FREEWARE';
}

function updateStats(airports) {
    document.getElementById('stat-total').innerText = airports.length.toLocaleString();

    let asoboCount = 0;
    let paywareCount = 0;
    let freewareCount = 0;
    let defaultCount = 0;

    airports.forEach(ap => {
        const pt = getAirportPricingType(ap);
        if (pt === 'Asobo') {
            asoboCount++;
        } else if (pt === 'Payware') {
            paywareCount++;
        } else if (pt === 'Default') {
            defaultCount++;
        } else {
            freewareCount++;
        }
    });

    document.getElementById('stat-asobo').innerText = asoboCount.toLocaleString();
    document.getElementById('stat-payware').innerText = paywareCount.toLocaleString();
    document.getElementById('stat-freeware').innerText = freewareCount.toLocaleString();
    const defEl = document.getElementById('stat-default');
    if (defEl) defEl.innerText = defaultCount.toLocaleString();

    updateInvestmentBanner();
    updateConflictNavigator();
}

let currentFlightMode = { active: false, icaos: [] };

function createCustomIcon(ap) {
    const allSourcesDisabled = ap.all_sources && ap.all_sources.length > 0 && ap.all_sources.every(s => s.is_disabled);
    let isApDisabled = ap.is_disabled || allSourcesDisabled;

    const cat = getAirportCategory(ap);
    let color = '#06b6d4'; // Freeware = Neon Cyan
    if (cat === 'ASOBO') color = '#f59e0b'; // Asobo Handcrafted = Amber/Gold
    else if (cat === 'PAYWARE') color = '#a855f7'; // Payware = Neon Purple
    else if (cat === 'DEFAULT') color = '#3b82f6'; // Default MSFS = Soft Royal Blue

    let strokeColor = ap.has_conflict ? '#ef4444' : '#ffffff';
    let strokeWidth = ap.has_conflict ? '2' : '1.2';

    if (isApDisabled && cat !== 'DEFAULT') {
        color = '#475569'; // Slate 600 Matte Gray fill
        strokeColor = '#cbd5e1'; // Crisp Silver/Slate 300 Outline
        strokeWidth = '1.5';
    }

    // Default MSFS procedural airports are drawn as CIRCLES / DOTS (not stars)
    const isCircleShape = (cat === 'DEFAULT');

    const svgIcon = isCircleShape ? `
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="drop-shadow-md">
            <circle cx="12" cy="12" r="7.5" fill="${color}" stroke="${strokeColor}" stroke-width="${strokeWidth}" />
            <circle cx="12" cy="12" r="2.5" fill="#ffffff" opacity="0.9" />
        </svg>
    ` : `
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="drop-shadow-md">
            <path d="M12 2l2.9 6.26 6.9.83-5.2 4.7 1.4 6.84L12 17.1 5.9 20.63l1.4-6.84-5.2-4.7 6.9-.83L12 2z" 
                  fill="${color}" stroke="${strokeColor}" stroke-width="${strokeWidth}" stroke-linejoin="round"/>
        </svg>
    `;

    return L.divIcon({
        html: svgIcon,
        className: `custom-map-marker ${isApDisabled ? 'grayscale-[0.5]' : ''}`,
        iconSize: isCircleShape ? [22, 22] : [26, 26],
        iconAnchor: isCircleShape ? [11, 11] : [13, 13]
    });
}

function getAirportPopupHtml(ap) {
    const cat = getAirportCategory(ap);
    let badgeClass = 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';
    let badgeLabel = 'Freeware';

    if (cat === 'DEFAULT') {
        badgeClass = 'bg-blue-500/20 text-blue-300 border-blue-500/40';
        badgeLabel = 'Default MSFS';
    } else if (cat === 'ASOBO') {
        badgeClass = 'bg-amber-500/20 text-amber-300 border-amber-500/40';
        badgeLabel = 'Asobo';
    } else if (cat === 'PAYWARE') {
        badgeClass = 'bg-purple-500/20 text-purple-300 border-purple-500/40';
        badgeLabel = 'Payware Addon';
    }

    const ratingVal = ap.rating || 0;
    const ratingBadgeHtml = ratingVal > 0 ? `
        <div class="flex items-center gap-1 text-amber-400 font-bold text-xs pt-0.5">
            <i class="fa-solid fa-star text-[11px]"></i>
            <span>${ratingVal.toFixed(1)} / 5.0</span>
        </div>
    ` : '';

    const conflictBadgeHtml = ap.has_conflict ? `
        <div class="mt-1 flex items-center gap-1 text-red-400 font-bold text-[10px] bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
            <i class="fa-solid fa-triangle-exclamation"></i>
            <span>Conflict: ${ap.conflict_count} Active Sceneries</span>
        </div>
    ` : '';

    const publisherHtml = `
        <div class="text-[10px] font-bold text-amber-300/90 truncate pt-1 border-t border-slate-800/60 flex items-center gap-1.5">
            <i class="fa-solid fa-building text-[10px] text-amber-400"></i>
            <span class="truncate">${ap.vendor || 'Unknown Publisher'}</span>
        </div>
    `;

    return `
        <div class="p-1 font-['Outfit'] space-y-2">
            <div class="flex items-center justify-between gap-2">
                <span class="text-xl font-black font-mono text-cyan-400 leading-none">${ap.icao}</span>
                <span class="text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${badgeClass} shrink-0">${badgeLabel}</span>
            </div>
            <div>
                <div class="text-xs font-bold text-slate-100 leading-snug line-clamp-2">${ap.name}</div>
                <div class="text-[11px] text-slate-400 mt-0.5 truncate">${ap.city || ''} ${ap.country ? '(' + ap.country + ')' : ''}</div>
            </div>
            ${publisherHtml}
            ${ratingBadgeHtml}
            ${conflictBadgeHtml}
            <div class="text-[10px] font-semibold text-cyan-400 pt-1.5 border-t border-slate-800 flex justify-between items-center">
                <span class="font-bold">${ap.english_type || ap.type}</span>
            </div>
        </div>
    `;
}

let isToggleInProgress = false;

function toggleAirportScenery(icao) {
    if (!window.pywebview || isToggleInProgress) return;
    isToggleInProgress = true;
    window.pywebview.api.toggle_airport_disabled(icao).then(resStr => {
        isToggleInProgress = false;
        try {
            const res = JSON.parse(resStr);
            if (res.status === 'success') {
                allAirportsData = res.airports || [];
                filterAirports();
                if (selectedAirport && selectedAirport.icao === icao) {
                    const updated = allAirportsData.find(a => a.icao === icao);
                    if (updated) showAirportDetails(updated);
                }
            } else if (res.message) {
                showCustomModal({
                    title: 'Action Not Allowed',
                    message: res.message,
                    type: 'warning',
                    confirmText: 'OK'
                });
            }
        } catch(e){}
    }).catch(() => { isToggleInProgress = false; });
}

function toggleSelectedAirportScenery() {
    if (!selectedAirport) return;
    toggleAirportScenery(selectedAirport.icao);
}

function renderAirportsOnMap(airports) {
    markerClusterGroup.clearLayers();

    const markers = [];

    airports.forEach(ap => {
        if (!ap.lat || !ap.lon) return;

        const icon = createCustomIcon(ap);
        const marker = L.marker([ap.lat, ap.lon], { icon: icon });

        // Bind default preview popup content
        marker.bindPopup(getAirportPopupHtml(ap), {
            maxWidth: 340,
            minWidth: 250,
            closeButton: false,
            autoClose: true
        });

        // Hover events for quick popup preview (shows developer/publisher)
        marker.on('mouseover', function () {
            if (isSuppressingHoverPopups) return;
            this.setPopupContent(getAirportPopupHtml(ap));
            this.openPopup();
        });

        marker.on('mouseout', function () {
            this.closePopup();
        });

        // Left-Click event: opens detailed drawer on right sidebar
        marker.on('click', function () {
            showAirportDetails(ap);
        });

        // Right-Click event: toggles scenery activation state directly & changes star color!
        marker.on('contextmenu', function (e) {
            if (e.originalEvent) {
                e.originalEvent.preventDefault();
                e.originalEvent.stopPropagation();
            }
            toggleAirportScenery(ap.icao);
        });

        markers.push(marker);
    });

    markerClusterGroup.addLayers(markers);
    const fcEl = document.getElementById('filtered-count');
    if (fcEl) fcEl.innerText = `${airports.length} visible`;

    renderRouteLines(airports);
}

function createBezierArcPoints(lat1, lon1, lat2, lon2, numPoints = 30) {
    const dLat = lat2 - lat1;
    const dLon = lon2 - lon1;
    const dist = Math.sqrt(dLat * dLat + dLon * dLon);
    if (dist === 0) return [[lat1, lon1]];

    // Perpendicular vector for smooth concave arc (standard aviation map convention)
    const normLat = dLon / dist;
    const normLon = -dLat / dist;
    const curvature = Math.min(dist * 0.18, 10.0);

    const ctrlLat = (lat1 + lat2) / 2 + normLat * curvature;
    const ctrlLon = (lon1 + lon2) / 2 + normLon * curvature;

    const points = [];
    for (let i = 0; i <= numPoints; i++) {
        const t = i / numPoints;
        const oneMinusT = 1 - t;
        const lat = oneMinusT * oneMinusT * lat1 + 2 * oneMinusT * t * ctrlLat + t * t * lat2;
        const lon = oneMinusT * oneMinusT * lon1 + 2 * oneMinusT * t * ctrlLon + t * t * lon2;
        points.push([lat, lon]);
    }
    return points;
}

function renderRouteLines(filteredAirports) {
    if (activeRouteLinesGroup) {
        activeRouteLinesGroup.clearLayers();
    } else {
        if (map) activeRouteLinesGroup = L.layerGroup().addTo(map);
    }

    if (!selectedAirline || !activeRouteOrigin || !activeRouteOrigin.lat || !activeRouteOrigin.lon || !activeRouteLinesGroup) {
        return;
    }

    const originLat = activeRouteOrigin.lat;
    const originLon = activeRouteOrigin.lon;

    filteredAirports.forEach(ap => {
        if (!ap.lat || !ap.lon || ap.icao === activeRouteOrigin.icao) return;

        const destLat = ap.lat;
        const destLon = ap.lon;

        const arcPoints = createBezierArcPoints(originLat, originLon, destLat, destLon, 30);

        const routeLine = L.polyline(arcPoints, {
            color: '#64748b', // Discrete Slate Gray
            weight: 1.2,      // Fine & thin
            opacity: 0.5,     // Subtle / discrete
            smoothFactor: 1
        });

        routeLine.addTo(activeRouteLinesGroup);
    });
}

function selectAirport(icao) {
    const ap = allAirportsData.find(a => a.icao === icao);
    if (ap) {
        focusAirportWithAnimation(ap);
    }
}

function focusAirportWithAnimation(ap) {
    if (!ap) return;
    lastFocusedIcao = ap.icao;

    if (map && ap.lat && ap.lon) {
        map.flyTo([ap.lat, ap.lon], 11, {
            animate: true,
            duration: 1.5
        });
        showAirportDetails(ap);
    }
}

function showAirportDetails(ap) {
    selectedAirport = ap;

    document.getElementById('drawer-icao').innerText = ap.icao;
    document.getElementById('drawer-iata').innerText = ap.iata ? ap.iata : '—';
    document.getElementById('drawer-name').innerText = ap.name;
    document.getElementById('drawer-city-country').innerText = `${ap.city || 'Unknown City'}, ${ap.country || 'Unknown Country'}`;

    document.getElementById('drawer-lat').innerText = ap.lat ? ap.lat.toFixed(4) : '0.0000';
    document.getElementById('drawer-lon').innerText = ap.lon ? ap.lon.toFixed(4) : '0.0000';
    
    const elevFt = ap.elevation !== undefined ? ap.elevation : 0;
    const elevM = Math.round(elevFt * 0.3048);
    document.getElementById('drawer-elevation').innerText = `${elevFt.toLocaleString()} ft (${elevM} m)`;
    
    document.getElementById('drawer-vendor').innerText = ap.vendor || (ap.is_asobo_official ? 'Microsoft / Asobo' : 'Unknown');
    const versionBadge = document.getElementById('drawer-version');
    if (versionBadge) {
        if (ap.version) {
            versionBadge.innerText = ap.version;
            versionBadge.classList.remove('hidden');
        } else {
            versionBadge.classList.add('hidden');
        }
    }

    const icaoEl = document.getElementById('drawer-icao');
    const vendorEl = document.getElementById('drawer-vendor');
    const typeBadge = document.getElementById('drawer-type-badge');
    const pricingBadge = document.getElementById('drawer-pricing-badge');

    const cat = getAirportCategory(ap);
    const hasActiveFix = (ap.all_sources || []).some(s => !s.is_disabled && (s.is_fix_patch || (s.folder_name && (s.folder_name.toLowerCase().includes('fix') || s.folder_name.toLowerCase().includes('patch')))));

    // Clean previous category color classes
    const categoryColorClasses = [
        'text-purple-400', 'text-cyan-400', 'text-amber-400', 'text-blue-400',
        'drop-shadow-[0_0_10px_rgba(192,132,252,0.3)]',
        'drop-shadow-[0_0_10px_rgba(56,189,248,0.3)]',
        'drop-shadow-[0_0_10px_rgba(245,158,11,0.3)]',
        'drop-shadow-[0_0_10px_rgba(59,130,246,0.3)]'
    ];
    if (icaoEl) icaoEl.classList.remove(...categoryColorClasses);
    if (vendorEl) vendorEl.classList.remove(...categoryColorClasses);
    if (typeBadge) typeBadge.classList.remove(...categoryColorClasses);

    if (cat === 'DEFAULT') {
        pricingBadge.innerText = "Default MSFS";
        pricingBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30";
        if (icaoEl) icaoEl.classList.add('text-blue-400', 'drop-shadow-[0_0_10px_rgba(59,130,246,0.3)]');
        if (vendorEl) vendorEl.classList.add('text-blue-400', 'drop-shadow-[0_0_10px_rgba(59,130,246,0.3)]');
        if (typeBadge) typeBadge.classList.add('text-blue-400');
    } else if (cat === 'ASOBO') {
        pricingBadge.innerText = hasActiveFix ? "Asobo + Fix" : "Asobo";
        pricingBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30";
        if (icaoEl) icaoEl.classList.add('text-amber-400', 'drop-shadow-[0_0_10px_rgba(245,158,11,0.3)]');
        if (vendorEl) vendorEl.classList.add('text-amber-400', 'drop-shadow-[0_0_10px_rgba(245,158,11,0.3)]');
        if (typeBadge) typeBadge.classList.add('text-amber-400');
    } else if (cat === 'PAYWARE') {
        pricingBadge.innerText = "Payware Addon";
        pricingBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-purple-500/20 text-purple-400 border border-purple-500/30";
        if (icaoEl) icaoEl.classList.add('text-purple-400', 'drop-shadow-[0_0_10px_rgba(192,132,252,0.3)]');
        if (vendorEl) vendorEl.classList.add('text-purple-400', 'drop-shadow-[0_0_10px_rgba(192,132,252,0.3)]');
        if (typeBadge) typeBadge.classList.add('text-purple-400');
    } else {
        pricingBadge.innerText = "Freeware";
        pricingBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30";
        if (icaoEl) icaoEl.classList.add('text-cyan-400', 'drop-shadow-[0_0_10px_rgba(56,189,248,0.3)]');
        if (vendorEl) vendorEl.classList.add('text-cyan-400', 'drop-shadow-[0_0_10px_rgba(56,189,248,0.3)]');
        if (typeBadge) typeBadge.classList.add('text-cyan-400');
    }

    if (typeBadge) typeBadge.innerText = ap.english_type || ap.type;

    // Update Activation Status Card in Drawer
    const actBadge = document.getElementById('drawer-activation-badge');
    const actBtn = document.getElementById('drawer-toggle-activation-btn');
    const actIcon = document.getElementById('drawer-toggle-icon');
    const actText = document.getElementById('drawer-toggle-text');

    if (actBadge && actBtn) {
        if (cat === 'DEFAULT') {
            actBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/40";
            actBadge.innerText = "🔵 Native Game Airport (Built-in)";
            actBtn.classList.add('hidden');
        } else if (cat === 'ASOBO') {
            actBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40";
            actBadge.innerText = "🟢 Core MSFS Base";
            actBtn.classList.add('hidden');
        } else {
            actBtn.classList.remove('hidden');
            if (ap.is_disabled) {
                actBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse";
                actBadge.innerText = "🔴 Disabled in MSFS";
                actBtn.className = "px-3 py-1.5 rounded-xl text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 cursor-pointer bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40";
                if (actIcon) actIcon.className = "fa-solid fa-power-off text-emerald-400";
                if (actText) actText.innerText = "Activate Scenery";
            } else {
                actBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40";
                actBadge.innerText = "🟢 Activated in MSFS";
                actBtn.className = "px-3 py-1.5 rounded-xl text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 cursor-pointer bg-slate-800 hover:bg-red-500/20 text-slate-200 hover:text-red-300 border border-slate-700 hover:border-red-500/40";
                if (actIcon) actIcon.className = "fa-solid fa-power-off text-red-400";
                if (actText) actText.innerText = "Disable Scenery";
            }
        }
    }

    // Price override card logic
    const priceCard = document.getElementById('drawer-price-card');
    if (cat === 'PAYWARE') {
        priceCard.classList.remove('hidden');
        const currSym = CURRENCY_SYMBOLS[selectedCurrency] || '€';
        document.getElementById('drawer-price-curr-symbol').innerText = currSym;

        const pValEur = ap.price_eur || 0;
        const formattedP = formatCurrency(pValEur);
        
        let tagText = "";
        if (ap.is_custom_price) {
            tagText = `Paid: ${formattedP} (Custom)`;
        } else if (ap.is_bundle || ap.bundle_total_price) {
            const bTotalFormatted = formatCurrency(ap.bundle_total_price || 39.00);
            const apCount = ap.bundle_airport_count || 'several';
            tagText = `Bundle Pack: ${bTotalFormatted} (${apCount} airports, ~${formattedP}/ap)`;
        } else {
            tagText = `Est: ~${formattedP}`;
        }
        document.getElementById('drawer-price-tag').innerText = tagText;

        const rate = CURRENCY_RATES[selectedCurrency] || 1.0;
        const valConverted = pValEur * rate;
        document.getElementById('drawer-price-input').value = ap.is_custom_price ? valConverted.toFixed(2) : '';
    } else {
        priceCard.classList.add('hidden');
    }

    // GSX Profile Card Logic
    const gsxBadge = document.getElementById('drawer-gsx-badge');
    const gsxContainer = document.getElementById('drawer-gsx-container');

    if (gsxBadge && gsxContainer) {
        if (ap.has_gsx_profile) {
            gsxBadge.className = "px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
            gsxBadge.innerText = "Profile Installed";
            const safeGsxPath = encodeURIComponent(ap.gsx_profile_path || '');
            gsxContainer.innerHTML = `
                <div class="space-y-2">
                    <div onclick="openGsxProfileInExplorer(decodeURIComponent('${safeGsxPath}'))" 
                         class="p-2.5 rounded-xl bg-slate-950/80 hover:bg-slate-800/80 border border-slate-800/80 hover:border-cyan-500/50 cursor-pointer flex items-center justify-between gap-2 text-xs font-mono font-bold text-slate-200 hover:text-cyan-300 transition-all group shadow-sm"
                         title="Click to reveal GSX INI file in Explorer">
                        <span class="truncate">${ap.gsx_profile_filename}</span>
                        <i class="fa-solid fa-folder-open text-cyan-400 group-hover:scale-110 transition-transform"></i>
                    </div>
                    <div ondragover="handleGsxDragOver(event)" ondragleave="handleGsxDragLeave(event)" ondrop="handleGsxDrop(event)"
                         class="p-2 rounded-xl bg-slate-950/40 border border-dashed border-slate-800/60 hover:border-cyan-500/40 flex items-center justify-between text-[11px] text-slate-400 hover:text-cyan-300 transition-all">
                        <span>📥 Drop .zip / .ini here to replace</span>
                        <button onclick="triggerInstallGsxProfile()" class="text-cyan-400 font-bold hover:underline">Replace .zip</button>
                    </div>
                </div>
            `;
        } else {
            gsxBadge.className = "px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-slate-800 text-slate-400 border border-slate-700";
            gsxBadge.innerText = "No Profile";
            gsxContainer.innerHTML = `
                <div class="space-y-2">
                    <button onclick="triggerSearchGsxProfile()" 
                            class="w-full p-2.5 rounded-xl bg-slate-950/40 hover:bg-cyan-500/10 border border-slate-800/50 hover:border-cyan-500/40 text-slate-300 hover:text-cyan-300 text-xs font-bold transition-all flex items-center justify-center gap-2 shadow-sm">
                        <i class="fa-solid fa-magnifying-glass text-cyan-400 text-xs"></i>
                        <span>Search GSX Profile on Flightsim.to</span>
                    </button>
                    <div ondragover="handleGsxDragOver(event)" ondragleave="handleGsxDragLeave(event)" ondrop="handleGsxDrop(event)"
                         onclick="triggerInstallGsxProfile()"
                         class="p-3 rounded-xl bg-slate-950/40 border-2 border-dashed border-slate-800 hover:border-cyan-500/50 flex flex-col items-center justify-center gap-1 text-center transition-all cursor-pointer group">
                        <i class="fa-solid fa-file-arrow-up text-cyan-400 text-base group-hover:scale-110 transition-transform"></i>
                        <span class="text-xs font-bold text-slate-300 group-hover:text-cyan-300">Drop downloaded .zip or .ini here</span>
                        <span class="text-[10px] text-slate-500">or click to browse & install directly</span>
                    </div>
                </div>
            `;
        }
    }

    // Render Operating Airlines Card (Simple Clean Text Badges, in English - Alphabetical & Interactive)
    const airlinesListEl = document.getElementById('drawer-airlines-list');
    const airlinesCountEl = document.getElementById('drawer-airlines-count');
    if (airlinesListEl && airlinesCountEl) {
        const airlines = (ap.operating_airlines || []).slice().sort((a, b) => a.localeCompare(b));
        if (airlines.length > 0) {
            airlinesCountEl.innerText = `${airlines.length} Airlines`;
            airlinesListEl.innerHTML = airlines.map(al => {
                const isActive = (selectedAirline === al && activeRouteOrigin && activeRouteOrigin.icao === ap.icao);
                const activeClass = isActive 
                    ? 'bg-cyan-500/25 text-cyan-300 border-cyan-400 shadow-[0_0_12px_rgba(56,189,248,0.4)] scale-105 font-bold' 
                    : 'bg-slate-950 text-slate-200 border-slate-800/80 hover:border-cyan-500/50 hover:text-cyan-300';
                const safeAl = al.replace(/'/g, "\\'");
                const dests = (ap.routes && ap.routes[al]) ? ap.routes[al].length : 0;
                const tooltipText = dests > 0 ? `Show ${dests} direct flight connections from ${ap.icao} on ${al}` : `Filter map by ${al}`;
                return `<button onclick="filterByAirline('${safeAl}')" 
                                class="text-xs font-semibold px-2.5 py-1 rounded-lg border transition-all cursor-pointer shadow-sm ${activeClass}" 
                                title="${tooltipText}">
                            ${al}
                        </button>`;
            }).join('');
        } else {
            airlinesCountEl.innerText = `0 Airlines`;
            airlinesListEl.innerHTML = `<span class="text-xs text-slate-500 italic">No scheduled airlines data available for this airport.</span>`;
        }
    }

    // Render rating widget for this airport
    renderStarRatingWidget(ap.rating || 0);

    // Conflict Alert Banner
    const conflictContainer = document.getElementById('drawer-conflict-banner');
    if (conflictContainer) {
        if (ap.has_conflict) {
            conflictContainer.innerHTML = `
                <div class="p-3.5 rounded-2xl bg-red-500/15 border border-red-500/40 text-red-300 space-y-1">
                    <div class="flex items-center gap-2 font-bold text-xs">
                        <i class="fa-solid fa-triangle-exclamation text-red-400"></i>
                        <span>SCENERY CONFLICT DETECTED</span>
                    </div>
                    <p class="text-[11px] text-red-200/90 leading-relaxed">
                        ${ap.conflict_count} active main sceneries are installed for ${ap.icao}. You can disable one below to avoid sim overlaps!
                    </p>
                </div>
            `;
            conflictContainer.classList.remove('hidden');
        } else {
            conflictContainer.classList.add('hidden');
        }
    }

    const sourcesContainer = document.getElementById('drawer-sources-list');
    sourcesContainer.innerHTML = '';

    const sources = ap.all_sources || [{
        folder_name: ap.package_name,
        source_folder: ap.source_folder,
        package_path: ap.package_path,
        match_source: ap.match_source,
        is_disabled: false,
        is_addon: false
    }];

    sources.forEach((src, idx) => {
        const isDisabled = !!src.is_disabled;
        const isFixPatch = !!src.is_fix_patch || (src.folder_name && (src.folder_name.toLowerCase().includes('fix') || src.folder_name.toLowerCase().includes('patch')));
        const isAddon = !!src.is_addon || isFixPatch;

        const cardBgClass = isDisabled 
            ? 'bg-slate-950/40 border-slate-800/40 opacity-60 grayscale-[0.5]' 
            : `bg-slate-900/95 ${isAddon ? 'border-slate-800/60' : 'border-slate-700/80'} shadow-md`;

        const titleClass = isDisabled 
            ? 'text-slate-500 font-semibold' 
            : 'text-white font-bold';

        const folderBoxClass = isDisabled 
            ? 'text-slate-500 line-through bg-slate-950/30 border-slate-800/30 font-mono text-xs p-2.5 rounded-lg border break-all' 
            : 'text-slate-200 font-bold bg-slate-950/70 border-slate-800 font-mono text-xs p-2.5 rounded-lg border break-all';

        const statusBadge = isDisabled 
            ? `<span class="text-xs font-mono font-bold px-3 py-1 rounded-full bg-slate-950 text-slate-400 border border-slate-800/60 whitespace-nowrap">🔴 Disabled</span>`
            : `<span class="text-xs font-mono font-bold px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 whitespace-nowrap">🟢 Active</span>`;

        const toggleBtnText = isDisabled ? 'Enable' : 'Disable';
        const toggleBtnIcon = isDisabled ? 'fa-power-off text-emerald-400' : 'fa-ban text-red-400';
        const toggleBtnClass = isDisabled 
            ? 'bg-emerald-500/25 hover:bg-emerald-500/35 text-emerald-300 border-emerald-500/50 shadow-sm shadow-emerald-500/10 font-extrabold cursor-pointer' 
            : 'bg-slate-800 hover:bg-red-500/20 text-slate-300 hover:text-red-300 border-slate-700 cursor-pointer';

        const openBtnClass = isDisabled
            ? 'px-2.5 py-1.5 rounded-lg bg-slate-950/60 text-slate-500 border border-slate-800/40 text-xs font-semibold flex items-center gap-1.5 transition-all shrink-0 whitespace-nowrap'
            : 'px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-all shadow-sm shrink-0 whitespace-nowrap';

        const hasConflict = ap.has_conflict || (ap.all_sources && ap.all_sources.length > 1);
        const isAsoboPkg = (src.is_asobo_official || src.vendor === 'Microsoft / Asobo' || (src.folder_name && (src.folder_name.toLowerCase().includes('asobo-airport-') || src.folder_name.toLowerCase().includes('microsoft-airport-'))));
        const isDefaultPkg = (src.pricing_type === 'Default' || (src.folder_name && src.folder_name.startsWith('msfs-default-')));

        let actionControlsHtml = '';

        if (isDefaultPkg) {
            actionControlsHtml = `
                <div class="flex items-center justify-center w-full pt-1 border-t border-slate-800/60">
                    <span class="text-xs font-mono font-bold px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/40">
                        🔵 Built-in Procedural MSFS Airport
                    </span>
                </div>
            `;
        } else if (isAsoboPkg && !hasConflict && !isDisabled) {
            actionControlsHtml = `
                <div class="flex items-center justify-between gap-2 pt-1 border-t border-slate-800/60">
                    <button onclick="openSpecificPackageFolderByIndex('${ap.icao}', ${idx})" class="${openBtnClass}" title="Open Folder">
                        <i class="fa-solid fa-folder-open text-cyan-400"></i> Open
                    </button>
                    <span class="text-xs font-mono font-bold px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 whitespace-nowrap">
                        🟢 Official Asobo Handcrafted
                    </span>
                </div>
            `;
        } else {
            const hasMultiplePkgs = (ap.all_sources && ap.all_sources.length > 1);
            actionControlsHtml = `
                <div class="flex items-center justify-between gap-2 pt-1 border-t border-slate-800/60">
                    <!-- 1. Open Button -->
                    <button onclick="openSpecificPackageFolderByIndex('${ap.icao}', ${idx})" class="${openBtnClass}" title="Open Folder">
                        <i class="fa-solid fa-folder-open ${isDisabled ? 'text-slate-500' : 'text-cyan-400'}"></i> Open
                    </button>
                    
                    <!-- 2. Active / Disabled Status Pill -->
                    ${statusBadge}
                    
                    <!-- 3. Disable / Enable Button (Only displayed if airport has multiple packages/fixes) -->
                    ${hasMultiplePkgs ? `
                    <button onclick="toggleSpecificPackageByIndex('${ap.icao}', ${idx})" class="px-2.5 py-1.5 rounded-lg border text-xs flex items-center gap-1.5 transition-all shadow-sm shrink-0 whitespace-nowrap ${toggleBtnClass}" title="Toggle Enable/Disable">
                        <i class="fa-solid ${toggleBtnIcon}"></i> ${toggleBtnText}
                    </button>
                    ` : ''}
                </div>
            `;
        }

        const itemHtml = `
            <div class="p-3.5 rounded-xl transition-all space-y-2.5 ${cardBgClass}">
                <!-- Line 1: Source Folder Name, Fix Tag & Disk Size / Streamed Badge -->
                <div class="flex items-center justify-between text-xs font-bold gap-2">
                    <div class="flex items-center gap-1.5 min-w-0 flex-1">
                        <span class="truncate min-w-0 ${titleClass}">${src.source_folder}</span>
                        ${isFixPatch ? `<span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shrink-0 whitespace-nowrap">🛠️ Fix / Patch</span>` : ''}
                    </div>
                    ${src.size_str === 'Streamed' || src.source_folder.toLowerCase().includes('streamed') 
                        ? `<span class="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full ${isDisabled ? 'bg-slate-950 text-slate-500 border border-slate-800/40' : 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30'} shrink-0 whitespace-nowrap">Streamed</span>`
                        : (src.size_str ? `<span class="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full ${isDisabled ? 'bg-slate-950 text-slate-500 border border-slate-800/40' : 'bg-slate-950 text-slate-200 border border-slate-800'} shrink-0 whitespace-nowrap">${src.size_str}</span>` : '')
                    }
                </div>
                
                <!-- Line 2: Package Directory Name -->
                <div class="${folderBoxClass}">${src.folder_name}</div>
                
                <!-- Line 3: Action Controls -->
                ${actionControlsHtml}
            </div>
        `;
        sourcesContainer.innerHTML += itemHtml;
    });

    document.getElementById('detail-drawer').classList.remove('translate-x-full');
}

async function triggerCheckSceneryUpdate() {
    if (!selectedAirport) return;
    try {
        if (window.pywebview) {
            await window.pywebview.api.check_update(
                selectedAirport.icao,
                selectedAirport.name || '',
                selectedAirport.vendor || '',
                selectedAirport.version || ''
            );
        }
    } catch (e) {
        console.error("Check update error:", e);
    }
}

async function resetCustomPriceForSelected() {
    if (!selectedAirport) return;
    document.getElementById('drawer-price-input').value = '';
    await saveCustomPriceForSelected();
}

async function saveCustomPriceForSelected() {
    if (!selectedAirport) return;
    const inputVal = document.getElementById('drawer-price-input').value;
    const rate = CURRENCY_RATES[selectedCurrency] || 1.0;

    let valInEur = null;
    if (inputVal !== '' && !isNaN(inputVal)) {
        valInEur = parseFloat(inputVal) / rate;
    }

    try {
        if (window.pywebview) {
            const resStr = await window.pywebview.api.set_custom_price(selectedAirport.icao, valInEur);
            const res = JSON.parse(resStr);
            if (res.status === 'ok') {
                allAirportsData = res.airports;
                allAirportsData.forEach(ap => {
                    if (userRatingsMap[ap.icao] !== undefined) {
                        ap.rating = userRatingsMap[ap.icao];
                    }
                });
                updateStats(allAirportsData);
                filterAirports();
                const updatedAp = allAirportsData.find(a => a.icao === selectedAirport.icao);
                if (updatedAp) showAirportDetails(updatedAp);
            }
        }
    } catch (e) {
        console.error("Failed to save custom price:", e);
    }
}

async function toggleSpecificPackage(path, icao) {
    if (!window.pywebview || isToggleInProgress) return;
    isToggleInProgress = true;
    try {
        const resStr = await window.pywebview.api.toggle_package(path, icao || '');
        const res = JSON.parse(resStr);
        if (res.status === 'ok') {
            allAirportsData = res.airports;
            allAirportsData.forEach(ap => {
                if (userRatingsMap[ap.icao] !== undefined) {
                    ap.rating = userRatingsMap[ap.icao];
                }
            });
            updateStats(allAirportsData);
            filterAirports();
            if (selectedAirport) {
                const updatedAp = allAirportsData.find(a => a.icao === selectedAirport.icao);
                if (updatedAp) showAirportDetails(updatedAp);
            }
        }
    } catch (e) {
        console.error("Failed to toggle package:", e);
    } finally {
        isToggleInProgress = false;
    }
}

function openSpecificPackageFolder(path) {
    if (window.pywebview) {
        window.pywebview.api.open_folder(path);
    }
}

function openSpecificPackageFolderByIndex(icao, idx) {
    if (!selectedAirport || !selectedAirport.all_sources || !selectedAirport.all_sources[idx]) return;
    const path = selectedAirport.all_sources[idx].package_path;
    if (path) openSpecificPackageFolder(path);
}

function toggleSpecificPackageByIndex(icao, idx) {
    if (!selectedAirport || !selectedAirport.all_sources || !selectedAirport.all_sources[idx]) return;
    const src = selectedAirport.all_sources[idx];
    const pathOrName = src.package_path || src.folder_name;
    if (pathOrName) toggleSpecificPackage(pathOrName, icao);
}

function closeDrawer() {
    document.getElementById('detail-drawer').classList.add('translate-x-full');
}

/* ================= STAR RATING WIDGET LOGIC (AIRPORT DETAIL) ================= */

function renderStarRatingWidget(rating) {
    const container = document.getElementById('interactive-star-widget');
    const scoreDisplay = document.getElementById('rating-score-display');
    if (!container || !scoreDisplay) return;

    container.innerHTML = '';

    if (rating > 0) {
        scoreDisplay.innerText = `★ ${rating.toFixed(1)} / 5.0`;
        scoreDisplay.className = "text-xs font-mono font-bold text-amber-400";
    } else {
        scoreDisplay.innerText = "Unrated";
        scoreDisplay.className = "text-xs font-mono font-semibold text-slate-500";
    }

    for (let starIdx = 1; starIdx <= 5; starIdx++) {
        const starEl = document.createElement('i');
        starEl.className = 'fa-regular fa-star star-item';

        if (rating >= starIdx) {
            starEl.className = 'fa-solid fa-star star-item full';
        } else if (rating >= starIdx - 0.5) {
            starEl.className = 'fa-solid fa-star-half-stroke star-item full';
        } else {
            starEl.className = 'fa-regular fa-star star-item';
        }

        starEl.addEventListener('mousemove', (e) => handleStarMouseMove(e, starIdx));
        starEl.addEventListener('click', (e) => handleStarClick(e, starIdx));

        container.appendChild(starEl);
    }
}

function handleStarMouseMove(e, starIdx) {
    const rect = e.target.getBoundingClientRect();
    const isLeftHalf = (e.clientX - rect.left) < (rect.width / 2);
    const hoverVal = isLeftHalf ? (starIdx - 0.5) : starIdx;

    renderStarRatingWidgetPreview(hoverVal);
}

function renderStarRatingWidgetPreview(val) {
    const container = document.getElementById('interactive-star-widget');
    const scoreDisplay = document.getElementById('rating-score-display');
    if (!container || !scoreDisplay) return;

    const stars = container.querySelectorAll('.star-item');

    scoreDisplay.innerText = `★ ${val.toFixed(1)}+`;
    scoreDisplay.className = "text-xs font-mono font-bold text-amber-300 animate-pulse";

    stars.forEach((starEl, index) => {
        const starIdx = index + 1;
        if (val >= starIdx) {
            starEl.className = 'fa-solid fa-star star-item full';
        } else if (val >= starIdx - 0.5) {
            starEl.className = 'fa-solid fa-star-half-stroke star-item full';
        } else {
            starEl.className = 'fa-regular fa-star star-item';
        }
    });
}

function resetStarHover() {
    if (selectedAirport) {
        renderStarRatingWidget(selectedAirport.rating || 0);
    } else {
        renderStarRatingWidget(0);
    }
}

async function handleStarClick(e, starIdx) {
    if (!selectedAirport) return;

    const rect = e.target.getBoundingClientRect();
    const isLeftHalf = (e.clientX - rect.left) < (rect.width / 2);
    const ratingVal = isLeftHalf ? (starIdx - 0.5) : starIdx;

    selectedAirport.rating = ratingVal;
    userRatingsMap[selectedAirport.icao] = ratingVal;

    renderStarRatingWidget(ratingVal);

    try {
        if (window.pywebview) {
            await window.pywebview.api.set_rating(selectedAirport.icao, ratingVal);
        }
    } catch (err) {
        console.error("Failed to save rating:", err);
    }

    filterAirports();
}

async function clearCurrentRating() {
    if (!selectedAirport) return;

    selectedAirport.rating = 0;
    delete userRatingsMap[selectedAirport.icao];

    renderStarRatingWidget(0);

    try {
        if (window.pywebview) {
            await window.pywebview.api.set_rating(selectedAirport.icao, 0);
        }
    } catch (err) {
        console.error("Failed to clear rating:", err);
    }

    filterAirports();
}

/* ================= STAR RATING FILTER WIDGET (LEFT SIDEBAR) ================= */

function renderFilterStarWidget(val) {
    const container = document.getElementById('filter-star-widget');
    const display = document.getElementById('filter-rating-display');
    if (!container || !display) return;

    container.innerHTML = '';

    if (val > 0) {
        display.innerText = `★ ${val.toFixed(1)}+`;
        display.className = "text-xs font-mono font-bold text-amber-400";
    } else {
        display.innerText = "All (0.0★)";
        display.className = "text-xs font-mono font-bold text-cyan-400";
    }

    for (let starIdx = 1; starIdx <= 5; starIdx++) {
        const starEl = document.createElement('i');

        if (val >= starIdx) {
            starEl.className = 'fa-solid fa-star star-item full';
        } else if (val >= starIdx - 0.5) {
            starEl.className = 'fa-solid fa-star-half-stroke star-item full';
        } else {
            starEl.className = 'fa-regular fa-star star-item';
        }

        starEl.addEventListener('mousemove', (e) => handleFilterStarMouseMove(e, starIdx));
        starEl.addEventListener('click', (e) => handleFilterStarClick(e, starIdx));

        container.appendChild(starEl);
    }
}

function handleFilterStarMouseMove(e, starIdx) {
    const rect = e.target.getBoundingClientRect();
    const isLeftHalf = (e.clientX - rect.left) < (rect.width / 2);
    const hoverVal = isLeftHalf ? (starIdx - 0.5) : starIdx;

    renderFilterStarWidgetPreview(hoverVal);
}

function renderFilterStarWidgetPreview(val) {
    const container = document.getElementById('filter-star-widget');
    const display = document.getElementById('filter-rating-display');
    if (!container || !display) return;

    const stars = container.querySelectorAll('.star-item');

    display.innerText = `★ ${val.toFixed(1)}+`;
    display.className = "text-xs font-mono font-bold text-amber-300 animate-pulse";

    stars.forEach((starEl, index) => {
        const starIdx = index + 1;
        if (val >= starIdx) {
            starEl.className = 'fa-solid fa-star star-item full';
        } else if (val >= starIdx - 0.5) {
            starEl.className = 'fa-solid fa-star-half-stroke star-item full';
        } else {
            starEl.className = 'fa-regular fa-star star-item';
        }
    });
}

function resetFilterStarHover() {
    renderFilterStarWidget(selectedMinRating);
}

function handleFilterStarClick(e, starIdx) {
    const rect = e.target.getBoundingClientRect();
    const isLeftHalf = (e.clientX - rect.left) < (rect.width / 2);
    const val = isLeftHalf ? (starIdx - 0.5) : starIdx;

    if (selectedMinRating === val) {
        selectedMinRating = 0;
    } else {
        selectedMinRating = val;
    }

    renderFilterStarWidget(selectedMinRating);
    filterAirports();
}

function resetMinRatingFilter() {
    selectedMinRating = 0;
    renderFilterStarWidget(0);
    filterAirports();
}

function resetFullDatabase() {
    showCustomModal({
        title: 'Reset Full Database & Restore Sceneries?',
        message: 'This will re-activate all disabled MSFS scenery packages, clear flight mode, and perform a fresh scan of your Community & Official folders.',
        type: 'warning',
        confirmText: 'Yes, Reset All',
        cancelText: 'Cancel',
        onConfirm: () => {
            const icon = document.getElementById('reset-icon');
            if (icon) icon.className = "fa-solid fa-spinner fa-spin text-red-400 text-xs";
            if (!window.pywebview) return;
            window.pywebview.api.reset_full_database().then(resStr => {
                if (icon) icon.className = "fa-solid fa-trash-can-arrow-up text-red-400 text-xs";
                try {
                    const res = JSON.parse(resStr);
                    if (res.status === 'success') {
                        allAirportsData = res.airports || [];
                        updateFlightModeBannerUI({ active: false, icaos: [] });
                        filterAirports();
                        showCustomModal({
                            title: 'Database Reset Complete',
                            message: 'All sceneries have been restored to Activated status and your database has been freshly scanned.',
                            type: 'success',
                            confirmText: 'Great!'
                        });
                    }
                } catch(e){}
            });
        }
    });
}

/* ================= FILTER & UI LOGIC ================= */

function filterAirports() {
    const rawSearch = document.getElementById('search-input').value.toLowerCase();
    const search = rawSearch.trim ? rawSearch.trim() : rawSearch;
    
    document.getElementById('clear-search').classList.toggle('hidden', search.length === 0);

    currentlyFilteredAirports = allAirportsData.filter(ap => {
        // Rating Filter
        const apRating = ap.rating || 0;
        if (selectedMinRating > 0 && apRating < selectedMinRating) {
            return false;
        }

        // Pricing Filter
        const pt = getAirportPricingType(ap);
        if (!selectedPricing.has(pt)) return false;

        // Type Filter
        const typeStr = ap.english_type || ap.type;
        if (!selectedTypes.has(typeStr)) return false;

        // GSX Profile Filter
        if (selectedGsxFilter === 'with' && !ap.has_gsx_profile) return false;
        if (selectedGsxFilter === 'none' && ap.has_gsx_profile) return false;

        // Operating Airline & Direct Route Filter
        if (selectedAirline) {
            if (activeRouteOrigin) {
                // Specific origin airport route mode
                if (ap.icao === activeRouteOrigin.icao) {
                    return true;
                }
                const destIcaos = (activeRouteOrigin.routes && activeRouteOrigin.routes[selectedAirline]) || [];
                if (!destIcaos.includes(ap.icao)) return false;
            } else {
                // Global airline filter mode
                const airlines = ap.operating_airlines || [];
                if (!airlines.includes(selectedAirline)) return false;
            }
        }

        // Search text
        if (search) {
            const matchesIcao = ap.icao.toLowerCase().includes(search);
            const matchesName = ap.name.toLowerCase().includes(search);
            const matchesCity = (ap.city || '').toLowerCase().includes(search);
            const matchesPkg = ap.package_name.toLowerCase().includes(search);
            const matchesVendor = (ap.vendor || '').toLowerCase().includes(search);
            return matchesIcao || matchesName || matchesCity || matchesPkg || matchesVendor;
        }

        return true;
    });

    renderAirportsOnMap(currentlyFilteredAirports);
}

function handleSearchKeyDown(e) {
    if (e.key === 'Enter') {
        triggerSearchFocus();
    }
}

function triggerSearchFocus() {
    const rawSearch = document.getElementById('search-input').value.toLowerCase();
    const search = rawSearch.trim ? rawSearch.trim() : rawSearch;
    if (!search || currentlyFilteredAirports.length === 0) return;

    const sUpper = search.toUpperCase();
    const exactIcaoMatch = currentlyFilteredAirports.find(a => a.icao === sUpper);

    if (exactIcaoMatch) {
        focusAirportWithAnimation(exactIcaoMatch);
    } else {
        focusAirportWithAnimation(currentlyFilteredAirports[0]);
    }
}

function clearSearch() {
    document.getElementById('search-input').value = '';
    lastFocusedIcao = null;
    filterAirports();
}

function filterByPricingPill(pricing) {
    if (pricing === 'All') {
        selectedPricing = new Set(ALL_PRICING_LIST);
    } else if (pricing === 'Payware') {
        if (selectedPricing.size === 1 && selectedPricing.has('Payware')) {
            selectedPricing = new Set(['Payware', 'Freeware / Flightsim.to', 'Asobo']);
        } else {
            selectedPricing = new Set(['Payware']);
        }
    } else if (pricing === 'Freeware') {
        if (selectedPricing.size === 1 && selectedPricing.has('Freeware / Flightsim.to')) {
            selectedPricing = new Set(['Payware', 'Freeware / Flightsim.to', 'Asobo']);
        } else {
            selectedPricing = new Set(['Freeware / Flightsim.to']);
        }
    } else if (pricing === 'Asobo') {
        if (selectedPricing.size === 1 && selectedPricing.has('Asobo')) {
            selectedPricing = new Set(['Payware', 'Freeware / Flightsim.to', 'Asobo']);
        } else {
            selectedPricing = new Set(['Asobo']);
        }
    } else if (pricing === 'Default') {
        if (selectedPricing.has('Default')) {
            selectedPricing.delete('Default');
        } else {
            selectedPricing.add('Default');
        }
    }
    updateFilterUI();
    filterAirports();
}

function togglePricingFilter(pricing) {
    if (pricing === 'all') {
        if (selectedPricing.size === ALL_PRICING_LIST.length) {
            selectedPricing.clear();
        } else {
            selectedPricing = new Set(ALL_PRICING_LIST);
        }
    } else {
        if (selectedPricing.has(pricing)) {
            selectedPricing.delete(pricing);
        } else {
            selectedPricing.add(pricing);
        }
    }
    updateFilterUI();
    filterAirports();
}

function toggleSourceFilter(src) {
    if (src === 'all') {
        if (selectedSources.size === ALL_SOURCES_LIST.length) {
            selectedSources.clear();
        } else {
            selectedSources = new Set(ALL_SOURCES_LIST);
        }
    } else {
        if (selectedSources.has(src)) {
            selectedSources.delete(src);
        } else {
            selectedSources.add(src);
        }
    }
    updateFilterUI();
    filterAirports();
}

function toggleTypeFilter(type) {
    if (type === 'all') {
        if (selectedTypes.size === ALL_TYPES_LIST.length) {
            selectedTypes.clear();
        } else {
            selectedTypes = new Set(ALL_TYPES_LIST);
        }
    } else {
        if (selectedTypes.has(type)) {
            selectedTypes.delete(type);
        } else {
            selectedTypes.add(type);
        }
    }
    updateFilterUI();
    filterAirports();
}

function setPillHighlight(el, isActive, colorType) {
    if (!el) return;

    el.classList.remove(
        'border-2', 'border-sky-400', 'border-purple-400', 'border-cyan-400', 'border-amber-400',
        'bg-sky-500/30', 'bg-purple-500/30', 'bg-cyan-500/30', 'bg-amber-500/30',
        'shadow-[0_0_15px_rgba(56,189,248,0.4)]', 'shadow-[0_0_15px_rgba(168,85,247,0.4)]',
        'shadow-[0_0_15px_rgba(6,182,212,0.4)]', 'shadow-[0_0_15px_rgba(245,158,11,0.4)]',
        'scale-105', 'opacity-60'
    );

    if (isActive) {
        if (colorType === 'sky') {
            el.classList.add('border-2', 'border-sky-400', 'bg-sky-500/30', 'shadow-[0_0_15px_rgba(56,189,248,0.4)]', 'scale-105');
        } else if (colorType === 'purple') {
            el.classList.add('border-2', 'border-purple-400', 'bg-purple-500/30', 'shadow-[0_0_15px_rgba(168,85,247,0.4)]', 'scale-105');
        } else if (colorType === 'cyan') {
            el.classList.add('border-2', 'border-cyan-400', 'bg-cyan-500/30', 'shadow-[0_0_15px_rgba(6,182,212,0.4)]', 'scale-105');
        } else if (colorType === 'amber') {
            el.classList.add('border-2', 'border-amber-400', 'bg-amber-500/30', 'shadow-[0_0_15px_rgba(245,158,11,0.4)]', 'scale-105');
        }
    } else {
        el.classList.add('opacity-60');
    }
}

function updateFilterUI() {
    // Stat Pills Active Glow Highlight
    const isAllSelected = (selectedPricing.size === ALL_PRICING_LIST.length);
    const isOnlyPayware = (selectedPricing.size === 1 && selectedPricing.has('Payware'));
    const isOnlyFreeware = (selectedPricing.size === 1 && selectedPricing.has('Freeware / Flightsim.to'));
    const isOnlyAsobo = (selectedPricing.size === 1 && selectedPricing.has('Asobo'));

    setPillHighlight(document.getElementById('stat-pill-total'), isAllSelected, 'sky');
    setPillHighlight(document.getElementById('stat-pill-payware'), isOnlyPayware, 'purple');
    setPillHighlight(document.getElementById('stat-pill-freeware'), isOnlyFreeware, 'cyan');
    setPillHighlight(document.getElementById('stat-pill-asobo'), isOnlyAsobo, 'amber');

    // Pricing Buttons UI
    const priceMap = {
        'Payware': 'filter-price-payware',
        'Freeware / Flightsim.to': 'filter-price-freeware',
        'Asobo': 'filter-price-asobo'
    };

    const allPriceBtn = document.getElementById('filter-price-all');
    setButtonActive(allPriceBtn, selectedPricing.size === ALL_PRICING_LIST.length);

    ALL_PRICING_LIST.forEach(price => {
        const btnId = priceMap[price];
        const btn = document.getElementById(btnId);
        if (btn) {
            setButtonActive(btn, selectedPricing.has(price));
        }
    });

    // Source Buttons UI
    const allSrcBtn = document.getElementById('filter-src-all');
    setButtonActive(allSrcBtn, selectedSources.size === ALL_SOURCES_LIST.length);

    ALL_SOURCES_LIST.forEach(src => {
        const btn = document.getElementById(`filter-src-${src}`);
        if (btn) {
            setButtonActive(btn, selectedSources.has(src));
        }
    });

    // Type Buttons UI
    const allTypeBtn = document.getElementById('filter-type-all');
    setButtonActive(allTypeBtn, selectedTypes.size === ALL_TYPES_LIST.length);

    ALL_TYPES_LIST.forEach(type => {
        const btnId = `filter-type-${type.replace(/\s+/g, '-').replace(/\//g, '-')}`;
        const btn = document.getElementById(btnId);
        if (btn) {
            setButtonActive(btn, selectedTypes.has(type));
        }
    });

    updateGsxFilterUI();

    // Airline Filter Pill UI
    const airlinePill = document.getElementById('airline-filter-pill');
    const airlineNameEl = document.getElementById('airline-filter-name');
    const airlineCountEl = document.getElementById('airline-filter-count');
    if (airlinePill) {
        if (selectedAirline) {
            airlinePill.classList.remove('hidden');
            airlinePill.classList.add('flex');
            if (airlineNameEl) airlineNameEl.innerText = selectedAirline;
            if (airlineCountEl) airlineCountEl.innerText = currentlyFilteredAirports ? currentlyFilteredAirports.length : 0;
        } else {
            airlinePill.classList.add('hidden');
            airlinePill.classList.remove('flex');
        }
    }
}

function toggleGsxFilter(val) {
    selectedGsxFilter = val;
    updateGsxFilterUI();
    filterAirports();
}

function updateGsxFilterUI() {
    ['all', 'with', 'none'].forEach(mode => {
        const btn = document.getElementById(`filter-gsx-${mode}`);
        if (!btn) return;
        if (selectedGsxFilter === mode) {
            btn.className = "py-2 px-2 rounded-xl border text-xs font-semibold bg-cyan-500/20 text-cyan-300 border-cyan-500/40 transition-all text-center flex items-center justify-center gap-1 shadow-sm shadow-cyan-500/10";
        } else {
            btn.className = "py-2 px-2 rounded-xl border text-xs font-medium bg-slate-900/60 text-slate-400 border-slate-800/80 opacity-60 hover:opacity-100 transition-all text-center flex items-center justify-center gap-1";
        }
    });
}

function setButtonActive(btn, active) {
    if (!btn) return;
    if (active) {
        btn.className = "py-2 px-3 rounded-xl border text-xs font-semibold bg-cyan-500/20 text-cyan-300 border-cyan-500/40 transition-all text-center flex items-center justify-center gap-1.5 shadow-sm shadow-cyan-500/10";
    } else {
        btn.className = "py-2 px-3 rounded-xl border text-xs font-medium bg-slate-900/60 text-slate-400 border-slate-800/80 opacity-60 hover:opacity-100 transition-all text-center flex items-center justify-center gap-1.5";
    }
}

async function rescanMSFS() {
    const icon = document.getElementById('rescan-icon');
    if (icon) icon.classList.add('fa-spin');

    try {
        if (window.pywebview) {
            const dataStr = await window.pywebview.api.rescan();
            allAirportsData = JSON.parse(dataStr);
        } else {
            const resp = await fetch('/api/rescan', { method: 'POST' });
            allAirportsData = await resp.json();
        }

        allAirportsData.forEach(ap => {
            if (userRatingsMap[ap.icao] !== undefined) {
                ap.rating = userRatingsMap[ap.icao];
            } else {
                ap.rating = ap.rating || 0;
            }
        });

        updateStats(allAirportsData);
        filterAirports();

        if (selectedAirport) {
            const updatedAp = allAirportsData.find(a => a.icao === selectedAirport.icao);
            if (updatedAp) showAirportDetails(updatedAp);
        }
    } catch (err) {
        console.error("Rescan error:", err);
    } finally {
        if (icon) icon.classList.remove('fa-spin');
    }
}

function openPackageFolder() {
    if (selectedAirport && window.pywebview) {
        window.pywebview.api.open_folder(selectedAirport.package_path);
    }
}

/* ================= SETTINGS MODAL FUNCTIONS ================= */

async function triggerSearchGsxProfile() {
    if (!selectedAirport) return;
    try {
        if (window.pywebview) {
            await window.pywebview.api.search_gsx_profile(selectedAirport.icao, selectedAirport.name || '');
        }
    } catch (e) {
        console.error("Search GSX profile error:", e);
    }
}

async function openGsxProfileInExplorer(path) {
    if (!path) return;
    try {
        if (window.pywebview) {
            await window.pywebview.api.open_file_in_explorer(path);
        }
    } catch (e) {
        console.error("Open GSX profile error:", e);
    }
}

function handleGsxDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    const container = document.getElementById('drawer-gsx-card');
    if (container) {
        container.classList.add('border-cyan-500', 'bg-cyan-500/10');
    }
}

function handleGsxDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    const container = document.getElementById('drawer-gsx-card');
    if (container) {
        container.classList.remove('border-cyan-500', 'bg-cyan-500/10');
    }
}

async function handleGsxDrop(e) {
    e.preventDefault();
    e.stopPropagation();

    const container = document.getElementById('drawer-gsx-card');
    if (container) {
        container.classList.remove('border-cyan-500', 'bg-cyan-500/10');
    }

    if (!e.dataTransfer || !e.dataTransfer.files || e.dataTransfer.files.length === 0) return;

    const file = e.dataTransfer.files[0];
    const path = file.path || '';

    if (path) {
        await executeGsxInstallation({ filePath: path });
    } else {
        const reader = new FileReader();
        reader.onload = async function(event) {
            const base64Data = event.target.result;
            await executeGsxInstallation({ base64Data: base64Data, filename: file.name });
        };
        reader.onerror = function() {
            showCustomModal({ title: 'Erreur de lecture', message: 'Impossible de lire le fichier déposé.', type: 'error' });
        };
        reader.readAsDataURL(file);
    }
}

async function triggerInstallGsxProfile() {
    await executeGsxInstallation({ filePath: '' });
}

async function executeGsxInstallation({ filePath = '', base64Data = '', filename = '' } = {}) {
    if (!selectedAirport) return;
    try {
        if (window.pywebview) {
            const resStr = await window.pywebview.api.install_gsx_profile(
                selectedAirport.icao || '',
                filePath || '',
                base64Data || '',
                filename || ''
            );
            const res = JSON.parse(resStr);
            if (res.status === 'ok') {
                allAirportsData = res.airports;
                allAirportsData.forEach(ap => {
                    if (userRatingsMap[ap.icao] !== undefined) {
                        ap.rating = userRatingsMap[ap.icao];
                    }
                });
                updateStats(allAirportsData);
                filterAirports();
                const updatedAp = allAirportsData.find(a => a.icao === selectedAirport.icao);
                if (updatedAp) showAirportDetails(updatedAp);
                showCustomModal({
                    title: 'Profil GSX Installé',
                    message: `Profil(s) GSX extrait(s) et installé(s) avec succès :\n\n• ${res.installed_files.join('\n• ')}`,
                    type: 'success',
                    confirmText: 'Continuer'
                });
            } else {
                showCustomModal({
                    title: 'Information Profil GSX',
                    message: res.message,
                    type: 'info',
                    confirmText: 'Compris'
                });
            }
        }
    } catch (e) {
        console.error("GSX Installation error:", e);
        showCustomModal({
            title: 'Erreur d\'installation GSX',
            message: e.message || String(e),
            type: 'error'
        });
    }
}

async function browseGsxFolder() {
    try {
        if (window.pywebview) {
            const folder = await window.pywebview.api.browse_folder();
            if (folder) {
                document.getElementById('cfg-gsx-path').value = folder;
                currentSettings.gsx_profile_path = folder;
            }
        }
    } catch (e) {
        console.error("Browse GSX folder error:", e);
    }
}

async function openSettingsModal() {
    try {
        if (window.pywebview) {
            const cfgStr = await window.pywebview.api.get_settings();
            currentSettings = JSON.parse(cfgStr);
        } else {
            const resp = await fetch('/api/settings');
            currentSettings = await resp.json();
        }
    } catch (e) {
        console.error("Failed to load settings:", e);
    }

    document.getElementById('cfg-auto-scan').checked = !!currentSettings.auto_scan_on_startup;
    const gsxInput = document.getElementById('cfg-gsx-path');
    if (gsxInput) {
        gsxInput.value = currentSettings.gsx_profile_path || '';
    }

    renderSettingsPathsList();
    document.getElementById('settings-modal').classList.remove('hidden');
}

function closeSettingsModal() {
    document.getElementById('settings-modal').classList.add('hidden');
}

function renderSettingsPathsList() {
    const container = document.getElementById('settings-paths-list');
    container.innerHTML = '';

    const paths = currentSettings.scan_paths || [];

    paths.forEach((item, index) => {
        const row = document.createElement('div');
        row.className = "p-3 rounded-2xl bg-slate-950/70 border border-slate-800 flex items-center justify-between gap-3";

        row.innerHTML = `
            <div class="space-y-1.5 flex-1">
                <div class="flex items-center justify-between">
                    <input type="text" value="${item.name || 'MSFS Scenery Path'}" 
                           oninput="updatePathName(${index}, this.value)"
                           placeholder="Folder Name (e.g. MSFS 2024 - Community)"
                           class="bg-transparent text-xs font-bold text-cyan-400 border-b border-slate-700/60 hover:border-cyan-500 focus:border-cyan-400 focus:outline-none px-1 py-0.5 w-full max-w-md transition-all">
                </div>

                <div class="flex items-center gap-2">
                    <input type="text" value="${item.path || ''}" 
                           oninput="updatePathValue(${index}, this.value)"
                           class="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-500">
                    <button onclick="browsePathFolder(${index})" class="px-2.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white text-xs transition-all flex items-center gap-1.5" title="Browse Folder">
                        <i class="fa-solid fa-folder-open text-cyan-400"></i>
                    </button>
                </div>
            </div>

            <div class="flex items-center gap-3 self-center pl-2">
                <label class="relative inline-flex items-center cursor-pointer" title="Enable/Disable Path Scan">
                    <input type="checkbox" ${item.enabled ? 'checked' : ''} onchange="togglePathEnabled(${index}, this.checked)" class="sr-only peer">
                    <div class="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-500"></div>
                </label>

                <button onclick="removePathRow(${index})" class="w-8 h-8 rounded-xl bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 border border-slate-700 transition-all flex items-center justify-center" title="Remove Path">
                    <i class="fa-solid fa-trash text-xs"></i>
                </button>
            </div>
        `;

        container.appendChild(row);
    });
}

function updatePathName(index, val) {
    if (currentSettings.scan_paths[index]) {
        currentSettings.scan_paths[index].name = val;
    }
}

function updatePathValue(index, val) {
    if (currentSettings.scan_paths[index]) {
        currentSettings.scan_paths[index].path = val;
    }
}

function togglePathEnabled(index, checked) {
    if (currentSettings.scan_paths[index]) {
        currentSettings.scan_paths[index].enabled = checked;
    }
}

async function browsePathFolder(index) {
    if (window.pywebview) {
        const folder = await window.pywebview.api.browse_folder();
        if (folder) {
            currentSettings.scan_paths[index].path = folder;
            renderSettingsPathsList();
        }
    }
}

function removePathRow(index) {
    currentSettings.scan_paths.splice(index, 1);
    renderSettingsPathsList();
}

function addCustomPathRow() {
    const newId = String(Date.now());
    currentSettings.scan_paths.push({
        id: newId,
        name: "Custom Scenery Directory",
        path: "D:\\Custom_MSFS_Sceneries",
        enabled: true
    });
    renderSettingsPathsList();
}

async function saveAndRescanSettings() {
    currentSettings.auto_scan_on_startup = document.getElementById('cfg-auto-scan').checked;
    const gsxInput = document.getElementById('cfg-gsx-path');
    if (gsxInput) {
        currentSettings.gsx_profile_path = gsxInput.value.trim();
    }

    try {
        if (window.pywebview) {
            await window.pywebview.api.save_settings(JSON.stringify(currentSettings));
        }
        closeSettingsModal();
        await rescanMSFS();
    } catch (e) {
        console.error("Failed to save settings:", e);
    }
}

/* ================= EXPORT COLLECTION FUNCTIONS ================= */

function openExportModal() {
    const modal = document.getElementById('export-modal');
    if (modal) modal.classList.remove('hidden');

    const txtEl = document.getElementById('export-scope-text');
    const scopeEl = document.querySelector('input[name="export-scope"]:checked');
    if (txtEl && scopeEl) {
        if (scopeEl.value === 'all') {
            txtEl.innerText = `Exports all ${allAirportsData.length} installed sceneries (physical sceneries & streamed Marketplace).`;
        } else {
            txtEl.innerText = `Exports only the ${currentlyFilteredAirports.length} sceneries currently visible on the map based on active filters (Payware, GSX, etc.).`;
        }
    }

    document.querySelectorAll('input[name="export-scope"]').forEach(radio => {
        radio.onclick = function() {
            if (!txtEl) return;
            if (this.value === 'all') {
                txtEl.innerText = `Exports all ${allAirportsData.length} installed sceneries (physical sceneries & streamed Marketplace).`;
            } else {
                txtEl.innerText = `Exports only the ${currentlyFilteredAirports.length} sceneries currently visible on the map based on active filters (Payware, GSX, etc.).`;
            }
        };
    });
}

function closeExportModal() {
    const modal = document.getElementById('export-modal');
    if (modal) modal.classList.add('hidden');
}

async function triggerExportCollection(format) {
    const scopeEl = document.querySelector('input[name="export-scope"]:checked');
    const scope = scopeEl ? scopeEl.value : 'all';

    const dataToExport = (scope === 'filtered') ? currentlyFilteredAirports : allAirportsData;

    if (!dataToExport || dataToExport.length === 0) {
        alert("No sceneries available to export.");
        return;
    }

    try {
        if (window.pywebview) {
            const dataJson = JSON.stringify(dataToExport);
            let resStr;
            if (format === 'csv') {
                resStr = await window.pywebview.api.export_collection_csv(dataJson);
            } else {
                resStr = await window.pywebview.api.export_collection_json(dataJson);
            }

            const res = JSON.parse(resStr);
            if (res.status === 'ok') {
                closeExportModal();
                alert(`✅ Collection Exported Successfully!\n\nExported ${res.count} sceneries to:\n${res.path}`);
            } else if (res.status !== 'cancelled') {
                alert(`⚠️ Export Error: ${res.message}`);
            }
        }
    } catch (e) {
        console.error("Export collection error:", e);
        alert("Failed to export collection.");
    }
}

/* ================= SYSTEM NOTIFICATION MODAL FUNCTIONS ================= */

let customModalConfirmCallback = null;
let customModalCancelCallback = null;

function showCustomModal(titleOrObj, messageStr, typeStr = 'info') {
    const modal = document.getElementById('custom-modal');

    let title = 'Notification';
    let message = '';
    let type = 'info';
    let confirmText = 'OK';
    let cancelText = 'Annuler';
    let showCancel = false;

    if (typeof titleOrObj === 'object' && titleOrObj !== null) {
        title = titleOrObj.title || 'Notification';
        message = titleOrObj.message || '';
        type = titleOrObj.type || 'info';
        confirmText = titleOrObj.confirmText || 'OK';
        cancelText = titleOrObj.cancelText || 'Annuler';
        showCancel = !!titleOrObj.showCancel;
        customModalConfirmCallback = titleOrObj.onConfirm || null;
        customModalCancelCallback = titleOrObj.onCancel || null;
    } else {
        title = titleOrObj || 'Notification';
        message = messageStr || '';
        type = typeStr || 'info';
        customModalConfirmCallback = null;
        customModalCancelCallback = null;
    }

    if (!modal) {
        alert(`${title}\n\n${message}`);
        return;
    }

    const titleEl = document.getElementById('custom-modal-title');
    const msgEl = document.getElementById('custom-modal-message');
    const cancelBtn = document.getElementById('custom-modal-cancel-btn');
    const confirmBtn = document.getElementById('custom-modal-confirm-btn');
    const iconBg = document.getElementById('custom-modal-icon-bg');
    const iconEl = document.getElementById('custom-modal-icon');

    if (titleEl) titleEl.innerText = title;
    if (msgEl) msgEl.innerText = message;
    if (confirmBtn) confirmBtn.innerText = confirmText;
    if (cancelBtn) {
        cancelBtn.innerText = cancelText;
        cancelBtn.classList.toggle('hidden', !showCancel);
    }

    if (iconBg && iconEl) {
        iconBg.className = "w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 shadow-inner ";
        iconEl.className = "fa-solid text-lg ";
        if (type === 'success') {
            iconBg.classList.add('bg-emerald-500/10', 'border', 'border-emerald-500/20');
            iconEl.classList.add('fa-circle-check', 'text-emerald-400');
        } else if (type === 'error') {
            iconBg.classList.add('bg-red-500/10', 'border', 'border-red-500/20');
            iconEl.classList.add('fa-triangle-exclamation', 'text-red-400');
        } else {
            iconBg.classList.add('bg-cyan-500/10', 'border', 'border-cyan-500/20');
            iconEl.classList.add('fa-circle-info', 'text-cyan-400');
        }
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeCustomModal() {
    const modal = document.getElementById('custom-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    customModalConfirmCallback = null;
    customModalCancelCallback = null;
}

function confirmCustomModal() {
    const cb = customModalConfirmCallback;
    closeCustomModal();
    if (cb && typeof cb === 'function') {
        cb();
    }
}

function cancelCustomModal() {
    const cb = customModalCancelCallback;
    closeCustomModal();
    if (cb && typeof cb === 'function') {
        cb();
    }
}

function promptClosingFlightMode() {
    showCustomModal({
        title: 'Plan de Vol SimBrief Actif',
        message: 'Un plan de vol SimBrief est actuellement actif dans SceneryX (les scènes hors-route sont isolées et désactivées dans MSFS pour optimiser vos performances).\n\nQue souhaitez-vous faire en quittant SceneryX ?',
        type: 'warning',
        confirmText: '⚡ Garder l\'isolement (En Vol)',
        cancelText: '🔄 Rétablir toutes mes scènes',
        showCancel: true,
        onConfirm: () => {
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.exit_app(false);
            }
        },
        onCancel: () => {
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.exit_app(true);
            }
        }
    });
}

/* ================= SIMBRIEF FLIGHT OPTIMIZER UI ENGINE ================= */

let currentSimBriefFlight = null;

function loadSimBriefSettingsUI() {
    if (!currentSettings) return;
    if (currentSettings.simbrief_username) {
        const uInput = document.getElementById('sb-username-input');
        if (uInput) uInput.value = currentSettings.simbrief_username;
    }
    if (currentSettings.simbrief_userid) {
        const idInput = document.getElementById('sb-userid-input');
        if (idInput) idInput.value = currentSettings.simbrief_userid;
    }
    if (currentSettings.flight_mode && currentSettings.flight_mode.active) {
        updateFlightModeBannerUI(currentSettings.flight_mode);
    }
}

function autoSyncSimBrief(changedField) {
    let val = '';
    if (changedField === 'username') {
        val = document.getElementById('sb-username-input').value.trim();
    } else {
        val = document.getElementById('sb-userid-input').value.trim();
    }
    if (!val || !window.pywebview) return;

    window.pywebview.api.fetch_simbrief(val).then(resStr => {
        try {
            const res = JSON.parse(resStr);
            if (res.status === 'success') {
                if (res.username && document.getElementById('sb-username-input')) {
                    document.getElementById('sb-username-input').value = res.username;
                }
                if (res.userid && document.getElementById('sb-userid-input')) {
                    document.getElementById('sb-userid-input').value = res.userid;
                }
            }
        } catch(e){}
    });
}

function triggerSimBriefImport() {
    const uVal = document.getElementById('sb-username-input').value.trim();
    const idVal = document.getElementById('sb-userid-input').value.trim();
    const identifier = uVal || idVal;

    if (!identifier) {
        showCustomModal({
            title: 'SimBrief Credentials Required',
            message: 'Please enter your SimBrief Username or Pilot ID in the left sidebar to import your flight plan.',
            type: 'warning',
            confirmText: 'OK'
        });
        return;
    }

    const icon = document.getElementById('sb-import-icon');
    if (icon) icon.className = "fa-solid fa-spinner fa-spin text-amber-400";

    if (!window.pywebview) return;

    window.pywebview.api.fetch_simbrief(identifier).then(resStr => {
        if (icon) icon.className = "fa-solid fa-cloud-arrow-down text-amber-400";
        try {
            const res = JSON.parse(resStr);
            if (res.status === 'error') {
                showCustomModal({
                    title: 'SimBrief Import Error',
                    message: res.message || 'Could not fetch flight plan from SimBrief.',
                    type: 'error',
                    confirmText: 'OK'
                });
                return;
            }

            currentSimBriefFlight = res.flight;
            if (res.username) document.getElementById('sb-username-input').value = res.username;
            if (res.userid) document.getElementById('sb-userid-input').value = res.userid;

            openSimBriefModal(res.flight);
        } catch(e) {
            showCustomModal({
                title: 'SimBrief Import Error',
                message: 'Failed to parse response: ' + e.message,
                type: 'error',
                confirmText: 'OK'
            });
        }
    });
}

function openSimBriefModal(flight) {
    const infoEl = document.getElementById('sb-modal-flight-info');
    if (infoEl) infoEl.innerText = `${flight.flight_number ? flight.flight_number + ' | ' : ''}${flight.aircraft ? flight.aircraft + ' | ' : ''}OFP LOADED`;
    
    document.getElementById('sb-modal-origin-icao').innerText = flight.origin.icao;
    document.getElementById('sb-modal-origin-name').innerText = flight.origin.name;

    document.getElementById('sb-modal-dest-icao').innerText = flight.destination.icao;
    document.getElementById('sb-modal-dest-name').innerText = flight.destination.name;

    const altsContainer = document.getElementById('sb-modal-alternates-list');
    altsContainer.innerHTML = '';
    if (flight.alternates && flight.alternates.length > 0) {
        flight.alternates.forEach(alt => {
            const pill = document.createElement('div');
            pill.className = "px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 font-mono font-bold flex items-center gap-1.5";
            pill.innerHTML = `<span class="text-amber-400 font-black">${alt.icao}</span> <span class="text-[10px] text-slate-400 font-sans font-normal truncate max-w-[150px]">${alt.name}</span>`;
            altsContainer.appendChild(pill);
        });
    } else {
        altsContainer.innerHTML = `<span class="text-slate-500 italic">No alternate airports specified in OFP</span>`;
    }

    const routeIcaos = flight.flight_icaos || [];
    const thirdPartyAirports = allAirportsData.filter(a => 
        a.pricing_type !== 'Asobo' && 
        a.pricing_type !== 'Default' && 
        !a.is_default && 
        !a.is_asobo_official
    );
    const toKeep = thirdPartyAirports.filter(a => routeIcaos.includes(a.icao));
    const toDisableCount = thirdPartyAirports.length - toKeep.length;

    document.getElementById('sb-modal-impact-text').innerText = `${toDisableCount} non-route 3rd-party sceneries will be disabled to boost FPS and stability. ${toKeep.length} installed route scenery package(s) (${toKeep.map(a=>a.icao).join(', ') || 'None'}) will remain 100% active.`;

    const modal = document.getElementById('simbrief-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeSimBriefModal() {
    const modal = document.getElementById('simbrief-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function confirmSimBriefOptimization() {
    closeSimBriefModal();
    if (!currentSimBriefFlight || !window.pywebview) return;

    const flightIcaos = currentSimBriefFlight.flight_icaos || [];
    const origStr = (currentSimBriefFlight.origin && currentSimBriefFlight.origin.icao) ? currentSimBriefFlight.origin.icao : (typeof currentSimBriefFlight.origin === 'string' ? currentSimBriefFlight.origin : '');
    const destStr = (currentSimBriefFlight.destination && currentSimBriefFlight.destination.icao) ? currentSimBriefFlight.destination.icao : (typeof currentSimBriefFlight.destination === 'string' ? currentSimBriefFlight.destination : '');
    const routeName = (origStr && destStr) ? `${origStr} ➔ ${destStr}` : 'SimBrief Route';

    const apiFn = window.pywebview.api.optimize_flight_mode || window.pywebview.api.optimize_flight;
    apiFn.call(window.pywebview.api, JSON.stringify(flightIcaos)).then(resStr => {
        try {
            const res = JSON.parse(resStr);
            if (res.status === 'ok' || res.status === 'success') {
                if (res.airports && res.airports.length > 0) {
                    allAirportsData = res.airports;
                }

                const disabledNum = res.disabled_count !== undefined ? res.disabled_count : (res.disabledCount !== undefined ? res.disabledCount : 0);

                updateFlightModeBannerUI({
                    active: true,
                    origin: origStr,
                    destination: destStr,
                    disabled_count: disabledNum,
                    icaos: flightIcaos
                });

                filterAirports();

                showCustomModal(
                    'Flight Scenery Optimization Active 🚀',
                    `Successfully isolated sceneries for flight ${routeName}.\n\nNon-route 3rd-party sceneries are disabled & MSFS Content.xml updated. Enjoy your flight!`,
                    'success'
                );
            } else {
                showCustomModal('Optimization Error', res.message || "Failed to optimize sceneries.", 'error');
            }
        } catch(e){
            console.error("Error parsing flight optimization result:", e);
        }
    }).catch(err => {
        showCustomModal('Optimization Error', String(err), 'error');
    });
}

function updateFlightModeBannerUI(flightMode) {
    currentFlightMode = flightMode || { active: false, icaos: [] };
    const badge = document.getElementById('sb-status-badge');
    const routeInfo = document.getElementById('sb-route-info');
    const routeText = document.getElementById('sb-route-text');
    const disabledText = document.getElementById('sb-disabled-text');
    const importBtn = document.getElementById('sb-import-btn');

    if (currentFlightMode && currentFlightMode.active) {
        if (badge) {
            badge.className = "text-[9px] font-bold font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse";
            badge.innerText = "ACTIVE";
        }
        if (routeInfo) routeInfo.classList.remove('hidden');
        if (routeText && currentFlightMode.icaos) {
            routeText.innerText = currentFlightMode.icaos.join(' ➔ ');
        }
        if (disabledText) {
            disabledText.innerText = `${currentFlightMode.disabled_count || 0} sceneries isolated`;
        }
        if (importBtn) {
            importBtn.className = "w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-red-500/30 via-amber-500/30 to-orange-500/30 hover:from-red-500/40 hover:to-orange-500/40 border border-amber-500/60 text-amber-200 font-extrabold text-xs transition-all flex items-center justify-center gap-2 shadow-md shadow-amber-500/10 active:scale-98 cursor-pointer";
            importBtn.onclick = function() { restoreAllFlightSceneriesUI(); };
            importBtn.innerHTML = `<i class="fa-solid fa-power-off text-amber-400"></i> <span>Exit Flight Mode & Restore Sceneries</span>`;
        }
    } else {
        if (badge) {
            badge.className = "text-[9px] font-bold font-mono px-2 py-0.5 rounded-full bg-slate-900 text-slate-400 border border-slate-800";
            badge.innerText = "INACTIVE";
        }
        if (routeInfo) routeInfo.classList.add('hidden');
        if (importBtn) {
            importBtn.className = "w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-amber-500/20 to-orange-500/20 hover:from-amber-500/30 hover:to-orange-500/30 border border-amber-500/40 text-amber-300 font-extrabold text-xs transition-all flex items-center justify-center gap-2 shadow-sm shadow-amber-500/10 active:scale-98 cursor-pointer";
            importBtn.onclick = function() { triggerSimBriefImport(); };
            importBtn.innerHTML = `<i id="sb-import-icon" class="fa-solid fa-cloud-arrow-down text-amber-400"></i> <span>Import Active SimBrief OFP</span>`;
        }
    }
}

function restoreAllFlightSceneriesUI() {
    if (!window.pywebview) return;
    const apiFn = window.pywebview.api.restore_all_sceneries || window.pywebview.api.restore_all_flight_sceneries;
    apiFn.call(window.pywebview.api).then(resStr => {
        try {
            const res = JSON.parse(resStr);
            if (res.status === 'ok' || res.status === 'success') {
                if (res.airports && res.airports.length > 0) {
                    allAirportsData = res.airports;
                }
                isFlightOptimizerActive = false;
                updateFlightModeBannerUI({ active: false, icaos: [] });
                filterAirports();
                showCustomModal(
                    'Sceneries Restored 🟢',
                    'All 3rd-party airport sceneries have been restored to their active state.',
                    'success'
                );
            } else {
                showCustomModal('Restore Error', res.message || "Failed to restore sceneries.", 'error');
            }
        } catch(e){
            console.error("Error parsing restore result:", e);
        }
    }).catch(err => {
        showCustomModal('Restore Error', String(err), 'error');
    });
}

