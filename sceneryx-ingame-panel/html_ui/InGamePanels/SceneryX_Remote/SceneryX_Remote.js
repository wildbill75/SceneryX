// =========================================================
// SceneryX MSFS In-Game Toolbar Panel - Resilient Controller
// =========================================================

if (typeof TemplateElement === "undefined") {
    window.TemplateElement = HTMLElement;
}
class IngamePanelSceneryX extends TemplateElement {
    constructor() {
        super(...arguments);
        this.ingameUi = null;
    }

    connectedCallback() {
        super.connectedCallback();
        this.ingameUi = this.querySelector("ingame-ui");
        let mainDisp = this.querySelector("#MainDisplay");
        if (mainDisp) mainDisp.classList.add("hidden");
        let footer = this.querySelector("#Footer");
        if (footer) footer.classList.add("hidden");
        if (this.ingameUi) {
            this.ingameUi.classList.remove("minimized");
            if (!this.ingameUi.getAttribute("title") || this.ingameUi.getAttribute("title") === "null") {
                this.ingameUi.setAttribute("title", "SCENERY X");
            }
            this.ingameUi.addEventListener("panelActive", function () {
                if (typeof window.sceneryxForcePanelHeight === "function") {
                    window.sceneryxForcePanelHeight();
                    setTimeout(window.sceneryxForcePanelHeight, 120);
                    setTimeout(window.sceneryxForcePanelHeight, 400);
                }
            });
        }
    }
}
if (!window.customElements.get("ingamepanel-sceneryx")) {
    window.customElements.define("ingamepanel-sceneryx", IngamePanelSceneryX);
}
if (typeof checkAutoload === "function") {
    checkAutoload();
}

(function () {
    const API_BASE = "http://127.0.0.1:8383/api";
    const POLL_INTERVAL_MS = 1000;
    const MAX_HISTORY_POINTS = 30;

    let currentLang = "en";
    const PANEL_I18N = {
        en: {
            offline_title: "Please launch Scenery X",
            offline_sub: "Waiting for local telemetry bridge (127.0.0.1:8383)...",
            live_gfx_btn: "LIVE GRAPHICS",
            live_gfx_btn_tip: "Open / close live graphics quick settings drawer",
            pinned_pills_tip: "Pinned graphics settings currently active in MSFS",
            lbl_max_fps: "Max FPS",
            lbl_clouds: "Clouds",
            lbl_precaching: "Pre-Caching",
            lbl_terrain_shadows: "Terrain Shadows",
            lbl_buildings: "Buildings",
            lbl_trees: "Trees",
            lbl_plants: "Plants",
            lbl_grass: "Grass",
            row_tip_max_fps: "Maximum frame rate target in MSFS",
            row_tip_clouds: "Volumetric Clouds quality in MSFS",
            row_tip_precaching: "Off-Screen Terrain Pre-Caching quality in MSFS",
            row_tip_terrain_shadows: "Terrain Shadows resolution in MSFS",
            row_tip_buildings: "Buildings rendering quality in MSFS",
            row_tip_trees: "Trees rendering quality in MSFS",
            row_tip_plants: "Plants rendering quality in MSFS",
            row_tip_grass: "Grass and bushes rendering quality in MSFS",
            input_fps_tip: "Enter custom Max FPS target (15-240)",
            presets_fps_tip: "Select from standard Max FPS presets",
            pin_tip: "Pin / Unpin from header bar (Max 5)",
            reset_profile_prefix: "Reset to Active Profile",
            pinned_count_label: "PINNED :",
            pinned_count_tip: "Number of graphics settings pinned to the top bar (maximum 5)",
            max_pins_reached: "MAX 5 PINS REACHED",
            apply_btn: "APPLY",
            apply_dirty_btn: "APPLY *",
            applied_btn: "APPLIED",
            apply_btn_tip: "Write modified graphics settings directly into MSFS memory",
            q_low: "Low",
            q_med: "Medium",
            q_high: "High",
            q_ultra: "Ultra",
            q_off: "Off",
            pill_max_fps: "Max FPS",
            pill_clouds: "Clouds",
            pill_precaching: "Pre-Cache",
            pill_terrain_shadows: "Terr. Shd",
            pill_buildings: "Buildings",
            pill_trees: "Trees",
            pill_plants: "Plants",
            pill_grass: "Grass",
            sec_smart_lod: "SMART LOD REGULATION",
            sec_smart_lod_tip: "Dynamic real-time TLOD and OLOD regulation based on altitude and frame rate",
            toggle_smart_lod_tip: "Enable / disable automatic Smart LOD regulation",
            autofps_lock_msg: "Managed by external AutoFPS",
            autofps_lock_tip: "External AutoFPS process detected — SceneryX Smart LOD is locked to prevent memory conflicts",
            tlod_title_tip: "Terrain Level of Detail (0-400) — controls terrain mesh and texture draw distance",
            tlod_badge_tip: "Current TLOD regulation mode (AUTO = regulated by SceneryX, MAN = manual override). Click to reset to profile.",
            olod_title_tip: "Objects Level of Detail (0-300) — controls buildings and airport clutter draw distance",
            olod_badge_tip: "Current OLOD regulation mode (AUTO = regulated by SceneryX, MAN = manual override). Click to reset to profile.",
            floor_lbl: "Floor :",
            cruise_lbl: "Cruise :",
            alt_lbl: "Alt :",
            floor_tip_tlod: "Minimum TLOD on the ground and below transition altitude",
            cruise_tip_tlod: "Target TLOD at or above transition altitude",
            alt_tip_tlod: "Transition altitude (in feet AGL) where TLOD reaches Cruise target",
            floor_tip_olod: "Minimum OLOD on the ground and below transition altitude",
            cruise_tip_olod: "Target OLOD at or above transition altitude",
            alt_tip_olod: "Transition altitude (in feet AGL) where OLOD reaches Cruise target",
            alt_down_tip: "Decrease transition altitude (-100 ft, Shift+Click: -500 ft)",
            alt_up_tip: "Increase transition altitude (+100 ft, Shift+Click: +500 ft)",
            alt_input_tip: "Enter transition altitude in feet Above Ground Level (500 - 45000 ft)",
            slider_tip_tlod: "Drag handles to adjust Floor (ground) and Cruise (altitude) TLOD limits",
            slider_tip_olod: "Drag handles to adjust Floor (ground) and Cruise (altitude) OLOD limits",
            handle_floor_prefix: "Floor LOD: ",
            handle_cruise_prefix: "Cruise LOD: ",
            cloud_rec_title: "AUTO CLOUD RECOVERY",
            cloud_rec_tip: "Automatically reduces Volumetric Clouds by 1 tier if FPS drops critically, and restores or boosts when headroom allows",
            cloud_rec_toggle_tip: "Enable / disable Automatic Cloud Recovery protection",
            sec_perf: "PERFORMANCE MONITORING",
            sec_perf_tip: "Real-time frame rate, CPU main thread timing, and 30-second stability trend",
            pacing_tip: "Frame pacing stability indicator (OPTIMAL, ACCEPTABLE, or HEAVY)",
            pacing_optimal: "OPTIMAL",
            pacing_acceptable: "ACCEPTABLE",
            pacing_heavy: "HEAVY",
            disp_fps_lbl: "DISPLAYED FPS",
            disp_fps_tip: "Final displayed frame rate vs native simulation base FPS",
            cpu_mt_lbl: "CPU MAIN THREAD",
            cpu_mt_tip: "CPU Main Thread frame time in milliseconds (lower is smoother)",
            trend_title: "30S TREND",
            trend_tip: "30-second FPS stability sparkline and net FPS variation",
            standby: "STANDBY",
            gpu_tip: "Graphics card core utilization (%) and temperature (°C)",
            cpu_tip: "Processor utilization (%) and package temperature (°C)",
            vram_tip: "Dedicated Video RAM currently used vs total available (GB)",
            cache_lbl: "CACHE",
            cache_tip: "Active MSFS Rolling Cache size in gigabytes (GB)",
            start_mon: "START MONITORING",
            stop_mon: "STOP MONITORING",
            blackbox_tip: "Start / Stop Blackbox flight performance recording",
            locked: "LOCKED"
        },
        fr: {
            offline_title: "Veuillez lancer Scenery X",
            offline_sub: "En attente du pont de télémétrie local (127.0.0.1:8383)...",
            live_gfx_btn: "GRAPHIQUES LIVE",
            live_gfx_btn_tip: "Ouvrir / fermer le tiroir de réglages graphiques en direct",
            pinned_pills_tip: "Réglages graphiques épinglés actuellement actifs dans MSFS",
            lbl_max_fps: "FPS Max",
            lbl_clouds: "Nuages",
            lbl_precaching: "Pré-Cache",
            lbl_terrain_shadows: "Ombres Terrain",
            lbl_buildings: "Bâtiments",
            lbl_trees: "Arbres",
            lbl_plants: "Plantes",
            lbl_grass: "Herbe",
            row_tip_max_fps: "Limite maximale d'images par seconde dans MSFS",
            row_tip_clouds: "Qualité des nuages volumétriques dans MSFS",
            row_tip_precaching: "Qualité de la mise en cache préalable du terrain hors écran dans MSFS",
            row_tip_terrain_shadows: "Résolution des ombres du terrain dans MSFS",
            row_tip_buildings: "Qualité d'affichage des bâtiments dans MSFS",
            row_tip_trees: "Qualité d'affichage des arbres dans MSFS",
            row_tip_plants: "Qualité d'affichage des plantes dans MSFS",
            row_tip_grass: "Qualité d'affichage de l'herbe et des buissons dans MSFS",
            input_fps_tip: "Saisir une cible FPS Max personnalisée (15-240)",
            presets_fps_tip: "Choisir parmi les préréglages FPS Max standards",
            pin_tip: "Épingler / Désépingler de la barre supérieure (Max 5)",
            reset_profile_prefix: "Réinitialiser au profil actif",
            pinned_count_label: "ÉPINGLÉS :",
            pinned_count_tip: "Nombre de paramètres graphiques épinglés dans la barre supérieure (maximum 5)",
            max_pins_reached: "MAX 5 ÉPINGLES ATTEINT",
            apply_btn: "APPLIQUER",
            apply_dirty_btn: "APPLIQUER *",
            applied_btn: "APPLIQUÉ",
            apply_btn_tip: "Écrire les paramètres graphiques modifiés directement dans la mémoire de MSFS",
            q_low: "Faible",
            q_med: "Moyen",
            q_high: "Élevé",
            q_ultra: "Ultra",
            q_off: "Désactivé",
            pill_max_fps: "FPS Max",
            pill_clouds: "Nuages",
            pill_precaching: "Pré-Cache",
            pill_terrain_shadows: "Ombres Terr.",
            pill_buildings: "Bâtiments",
            pill_trees: "Arbres",
            pill_plants: "Plantes",
            pill_grass: "Herbe",
            sec_smart_lod: "RÉGULATION SMART LOD",
            sec_smart_lod_tip: "Régulation dynamique en temps réel du TLOD et de l'OLOD selon l'altitude et les FPS",
            toggle_smart_lod_tip: "Activer / désactiver la régulation automatique Smart LOD",
            autofps_lock_msg: "Géré par AutoFPS externe",
            autofps_lock_tip: "Processus AutoFPS externe détecté — le Smart LOD de SceneryX est verrouillé pour éviter tout conflit mémoire",
            tlod_title_tip: "Niveau de détail du terrain (0-400) — contrôle la distance d'affichage du relief et des textures",
            tlod_badge_tip: "Mode de régulation TLOD actuel (AUTO = géré par SceneryX, MAN = manuel). Cliquez pour réinitialiser au profil.",
            olod_title_tip: "Niveau de détail des objets (0-300) — contrôle la distance d'affichage des bâtiments et objets",
            olod_badge_tip: "Mode de régulation OLOD actuel (AUTO = géré par SceneryX, MAN = manuel). Cliquez pour réinitialiser au profil.",
            floor_lbl: "Sol :",
            cruise_lbl: "Croisière :",
            alt_lbl: "Alt :",
            floor_tip_tlod: "TLOD minimum au sol et sous l'altitude de transition",
            cruise_tip_tlod: "TLOD cible à l'altitude de transition et au-dessus",
            alt_tip_tlod: "Altitude de transition (en pieds AGL) où le TLOD atteint la cible de croisière",
            floor_tip_olod: "OLOD minimum au sol et sous l'altitude de transition",
            cruise_tip_olod: "OLOD cible à l'altitude de transition et au-dessus",
            alt_tip_olod: "Altitude de transition (en pieds AGL) où l'OLOD atteint la cible de croisière",
            alt_down_tip: "Diminuer l'altitude de transition (-100 ft, Maj+Clic : -500 ft)",
            alt_up_tip: "Augmenter l'altitude de transition (+100 ft, Maj+Clic : +500 ft)",
            alt_input_tip: "Saisir l'altitude de transition en pieds au-dessus du sol (500 - 45000 ft)",
            slider_tip_tlod: "Faites glisser les poignées pour ajuster les limites TLOD Sol et Croisière",
            slider_tip_olod: "Faites glisser les poignées pour ajuster les limites OLOD Sol et Croisière",
            handle_floor_prefix: "LOD Sol : ",
            handle_cruise_prefix: "LOD Croisière : ",
            cloud_rec_title: "RÉCUPÉRATION AUTO DES NUAGES",
            cloud_rec_tip: "Réduit automatiquement la qualité des nuages d'un palier si les FPS chutent sous le seuil critique, et la restaure dès que la marge le permet",
            cloud_rec_toggle_tip: "Activer / désactiver la protection automatique des nuages",
            sec_perf: "SURVEILLANCE DES PERFORMANCES",
            sec_perf_tip: "Fréquence d'images en temps réel, temps CPU Main Thread et tendance de stabilité sur 30 secondes",
            pacing_tip: "Indicateur de fluidité d'affichage (OPTIMAL, ACCEPTABLE ou LOURD)",
            pacing_optimal: "OPTIMAL",
            pacing_acceptable: "ACCEPTABLE",
            pacing_heavy: "LOURD",
            disp_fps_lbl: "FPS AFFICHÉS",
            disp_fps_tip: "FPS finaux affichés (incluant Frame Generation) par rapport aux FPS natifs de base",
            cpu_mt_lbl: "CPU MAIN THREAD",
            cpu_mt_tip: "Temps de calcul par image du thread principal CPU en millisecondes (plus bas = plus fluide)",
            trend_title: "TENDANCE 30S",
            trend_tip: "Courbe de stabilité des FPS sur 30 secondes et variation nette",
            standby: "EN ATTENTE",
            gpu_tip: "Utilisation de la carte graphique (%) et température (°C)",
            cpu_tip: "Utilisation du processeur (%) et température (°C)",
            vram_tip: "Mémoire vidéo dédiée (VRAM) utilisée par rapport au total disponible (Go)",
            cache_lbl: "CACHE",
            cache_tip: "Taille actuelle du Rolling Cache MSFS en gigaoctets (Go)",
            start_mon: "DÉMARRER LE SUIVI",
            stop_mon: "ARRÊTER LE SUIVI",
            blackbox_tip: "Démarrer / Arrêter l'enregistrement des performances de vol Blackbox",
            locked: "VERROUILLÉ"
        }
    };

    function pt(key) {
        let dict = PANEL_I18N[currentLang] || PANEL_I18N.en;
        return dict[key] || PANEL_I18N.en[key] || key;
    }

    function setElText(id, text) {
        let el = document.getElementById(id);
        if (el) el.textContent = text;
    }

    function setElTitle(id, titleText) {
        let el = document.getElementById(id);
        if (el) {
            el.setAttribute("data-scx-tip", titleText);
            if (el.hasAttribute("title") && el.id !== "SceneryX_Remote") {
                el.removeAttribute("title");
            }
        }
    }

    let isConnected = false;
    let fpsHistory = [];
    let wasRecording = false;
    let isSmartLodToggling = false;
    let isBlackboxToggling = false;
    let lastSmartLodToggleTime = 0;
    let currentIsExtAutoFps = false;

    // Dual LOD State
    let currentTlodFloor = 100;
    let currentTlodCruise = 200;
    let currentTlodAlt = 3000;
    let currentTlodLive = 100;

    let currentOlodFloor = 100;
    let currentOlodCruise = 200;
    let currentOlodAlt = 3000;
    let currentOlodLive = 100;

    let tlodIsManual = false;
    let olodIsManual = false;
    let currentIsVr = false;
    let currentLodActive = true;
    let currentCloudRecovery = true;
    let isCloudRecoveryToggling = false;
    let lastCloudRecoveryToggleTime = 0;

    let isSliderDragging = false;
    let isUserInteracting = false;
    let userInteractionTimeout = null;
    let debounceTimer = null;

    let tlodController = null;
    let olodController = null;

    function getApiBase() {
        return API_BASE;
    }

    function applyPanelLanguage(lang) {
        let norm = (lang && String(lang).toLowerCase().indexOf("fr") === 0) ? "fr" : "en";
        let changed = (norm !== currentLang);
        currentLang = norm;

        setElText("offline-title-text", pt("offline_title"));
        setElText("offline-sub-text", pt("offline_sub"));
        setElText("live-gfx-btn-label", pt("live_gfx_btn"));
        setElTitle("live-gfx-accordion-btn", pt("live_gfx_btn_tip"));
        setElTitle("pinned-pills-container", pt("pinned_pills_tip"));

        setElText("lgfx-lbl-max_fps", pt("lbl_max_fps"));
        setElText("lgfx-lbl-clouds", pt("lbl_clouds"));
        setElText("lgfx-lbl-precaching", pt("lbl_precaching"));
        setElText("lgfx-lbl-terrain_shadows", pt("lbl_terrain_shadows"));
        setElText("lgfx-lbl-buildings", pt("lbl_buildings"));
        setElText("lgfx-lbl-trees", pt("lbl_trees"));
        setElText("lgfx-lbl-plants", pt("lbl_plants"));
        setElText("lgfx-lbl-grass", pt("lbl_grass"));

        setElTitle("lgfx-item-max_fps", pt("row_tip_max_fps"));
        setElTitle("lgfx-item-clouds", pt("row_tip_clouds"));
        setElTitle("lgfx-item-precaching", pt("row_tip_precaching"));
        setElTitle("lgfx-item-terrain_shadows", pt("row_tip_terrain_shadows"));
        setElTitle("lgfx-item-buildings", pt("row_tip_buildings"));
        setElTitle("lgfx-item-trees", pt("row_tip_trees"));
        setElTitle("lgfx-item-plants", pt("row_tip_plants"));
        setElTitle("lgfx-item-grass", pt("row_tip_grass"));

        setElTitle("lgfx-input-max_fps", pt("input_fps_tip"));
        setElTitle("lgfx-ddbtn-max_fps", pt("presets_fps_tip"));

        let pinKeys = ["max_fps", "clouds", "precaching", "terrain_shadows", "buildings", "trees", "plants", "grass"];
        for (let i = 0; i < pinKeys.length; i++) {
            setElTitle("lgfx-pin-" + pinKeys[i], pt("pin_tip"));
            let menu = document.getElementById("lgfx-menu-" + pinKeys[i]);
            if (menu && pinKeys[i] !== "max_fps" && pinKeys[i] !== "terrain_shadows") {
                let opts = menu.getElementsByClassName("lgfx-dd-option");
                for (let j = 0; j < opts.length; j++) {
                    let dv = parseInt(opts[j].getAttribute("data-val"), 10);
                    if (dv === 0) opts[j].textContent = pt("q_low");
                    else if (dv === 1) opts[j].textContent = pt("q_med");
                    else if (dv === 2) opts[j].textContent = pt("q_high");
                    else if (dv === 3) opts[j].textContent = pt("q_ultra");
                }
            } else if (menu && pinKeys[i] === "terrain_shadows") {
                let opts = menu.getElementsByClassName("lgfx-dd-option");
                for (let j = 0; j < opts.length; j++) {
                    let dv = parseInt(opts[j].getAttribute("data-val"), 10);
                    if (dv === 0) opts[j].textContent = pt("q_off");
                }
            }
        }

        setElText("lgfx-pinned-label", pt("pinned_count_label"));
        setElTitle("lgfx-footer-hint", pt("pinned_count_tip"));
        setElTitle("lgfx-apply-btn", pt("apply_btn_tip"));

        setElText("sec-title-smart-lod", pt("sec_smart_lod"));
        setElTitle("sec-title-smart-lod", pt("sec_smart_lod_tip"));
        setElTitle("smart-lod-toggle-btn", pt("toggle_smart_lod_tip"));
        setElText("smart-lod-autofps-lock-msg", pt("autofps_lock_msg"));
        setElTitle("smart-lod-autofps-lock-msg", pt("autofps_lock_tip"));

        setElTitle("tlod-title-group", pt("tlod_title_tip"));
        setElTitle("tlod-name-label", pt("tlod_title_tip"));
        setElTitle("tlod-mode-badge", pt("tlod_badge_tip"));
        setElTitle("olod-title-group", pt("olod_title_tip"));
        setElTitle("olod-name-label", pt("olod_title_tip"));
        setElTitle("olod-mode-badge", pt("olod_badge_tip"));

        setElText("tlod-floor-lbl", pt("floor_lbl"));
        setElText("tlod-cruise-lbl", pt("cruise_lbl"));
        setElText("tlod-alt-lbl", pt("alt_lbl"));
        setElText("olod-floor-lbl", pt("floor_lbl"));
        setElText("olod-cruise-lbl", pt("cruise_lbl"));
        setElText("olod-alt-lbl", pt("alt_lbl"));

        setElTitle("tlod-floor-param", pt("floor_tip_tlod"));
        setElTitle("tlod-cruise-param", pt("cruise_tip_tlod"));
        setElTitle("tlod-alt-param", pt("alt_tip_tlod"));
        setElTitle("olod-floor-param", pt("floor_tip_olod"));
        setElTitle("olod-cruise-param", pt("cruise_tip_olod"));
        setElTitle("olod-alt-param", pt("alt_tip_olod"));

        setElTitle("tlod-alt-down", pt("alt_down_tip"));
        setElTitle("tlod-alt-up", pt("alt_up_tip"));
        setElTitle("tlod-alt-input", pt("alt_input_tip"));
        setElTitle("olod-alt-down", pt("alt_down_tip"));
        setElTitle("olod-alt-up", pt("alt_up_tip"));
        setElTitle("olod-alt-input", pt("alt_input_tip"));

        setElTitle("tlod-dual-container", pt("slider_tip_tlod"));
        setElTitle("olod-dual-container", pt("slider_tip_olod"));

        setElText("cloud-recovery-title", pt("cloud_rec_title"));
        setElTitle("cloud-recovery-bar", pt("cloud_rec_tip"));
        setElTitle("cloud-recovery-toggle-btn", pt("cloud_rec_toggle_tip"));

        setElText("sec-title-perf", pt("sec_perf"));
        setElTitle("sec-title-perf", pt("sec_perf_tip"));
        setElTitle("live-pacing-status", pt("pacing_tip"));

        setElText("lbl-displayed-fps", pt("disp_fps_lbl"));
        setElTitle("perf-metric-fps", pt("disp_fps_tip"));
        setElText("lbl-cpu-mt", pt("cpu_mt_lbl"));
        setElTitle("perf-metric-mt", pt("cpu_mt_tip"));

        setElText("lbl-sparkline-trend", pt("trend_title"));
        setElTitle("sparkline-box", pt("trend_tip"));

        setElTitle("metric-card-gpu", pt("gpu_tip"));
        setElTitle("metric-card-cpu", pt("cpu_tip"));
        setElTitle("metric-card-vram", pt("vram_tip"));
        setElText("lbl-metric-cache", pt("cache_lbl"));
        setElTitle("metric-card-cache", pt("cache_tip"));

        setElTitle("blackbox-toggle-btn", pt("blackbox_tip"));
        let lblRec = document.getElementById("rec-btn-label");
        if (lblRec) {
            lblRec.textContent = wasRecording ? pt("stop_mon") : pt("start_mon");
        }

        if (changed) {
            renderPinnedPills();
            syncLiveGfxSelectsFromTelemetry();
            if (tlodController) tlodController.updateUI(currentTlodFloor, currentTlodCruise);
            if (olodController) olodController.updateUI(currentOlodFloor, currentOlodCruise);
        }
    }

    function setConnectedState(online) {
        let changed = (isConnected !== online);
        isConnected = online;
        let discView = document.getElementById("disconnected-view");
        let connView = document.getElementById("connected-view");

        if (online) {
            if (discView) {
                discView.classList.add("hidden");
                discView.style.display = "none";
            }
            if (connView) {
                connView.classList.remove("hidden");
                connView.style.display = "flex";
            }
        } else {
            isSmartLodToggling = false;
            isBlackboxToggling = false;
            if (discView) {
                discView.classList.remove("hidden");
                discView.style.display = "flex";
            }
            if (connView) {
                connView.classList.add("hidden");
                connView.style.display = "none";
            }
        }
        if (changed) {
            setTimeout(notifyHeight, 15);
        }
    }

    function setAxisUiState(axis, isManual, isOff) {
        let badge = document.getElementById(axis + "-mode-badge");
        let txt = document.getElementById(axis + "-badge-text");
        let card = document.getElementById(axis + "-card");
        if (axis === "tlod") tlodIsManual = isManual;
        else olodIsManual = isManual;

        if (txt && badge) {
            if (currentIsExtAutoFps) {
                badge.className = "badge-tag badge-off";
                txt.textContent = "AUTOFPS";
                if (card) {
                    card.classList.remove("auto-locked");
                    card.classList.remove("mode-auto");
                    card.classList.add("mode-man");
                }
            } else if (!currentLodActive || isManual || isOff) {
                badge.className = "badge-tag badge-man";
                txt.textContent = "MAN";
                if (card) {
                    card.classList.remove("auto-locked");
                    card.classList.remove("mode-auto");
                    card.classList.add("mode-man");
                }
            } else {
                badge.className = "badge-tag badge-auto";
                txt.textContent = "AUTO";
                if (card) {
                    card.classList.add("auto-locked");
                    card.classList.add("mode-auto");
                    card.classList.remove("mode-man");
                }
            }
        }
    }

    // Pure DIV Dual Slider Controller (Snapping 5 by 5, no dots, 100% centered)
    class DualSliderController {
        constructor(axis, maxVal, getValues, setValues, onCommit) {
            this.axis = axis;
            this.maxVal = maxVal;
            this.minVal = 10;
            this.step = 5;
            this.getValues = getValues;
            this.setValues = setValues;
            this.onCommit = onCommit;

            this.container = document.getElementById(axis + "-dual-container");
            this.highlight = document.getElementById(axis + "-track-highlight");
            this.floorHandle = document.getElementById(axis + "-floor-handle");
            this.cruiseHandle = document.getElementById(axis + "-cruise-handle");
            this.floorValEl = document.getElementById(axis + "-floor-val");
            this.cruiseValEl = document.getElementById(axis + "-cruise-val");

            this.activeHandle = null;
            this.isDragging = false;

            this.initEvents();
        }

        updateUI(floor, cruise) {
            if (!this.container) return;
            floor = Math.max(0, Math.min(this.maxVal, Math.round(Number(floor) || 0)));
            cruise = Math.max(0, Math.min(this.maxVal, Math.round(Number(cruise) || 0)));

            let floorPct = (floor / this.maxVal) * 100;
            let cruisePct = (cruise / this.maxVal) * 100;

            if (this.floorHandle) {
                this.floorHandle.style.left = floorPct + "%";
                this.floorHandle.setAttribute("data-scx-tip", pt("handle_floor_prefix") + floor);
                this.floorHandle.removeAttribute("title");
            }
            if (this.cruiseHandle) {
                this.cruiseHandle.style.left = cruisePct + "%";
                this.cruiseHandle.setAttribute("data-scx-tip", pt("handle_cruise_prefix") + cruise);
                this.cruiseHandle.removeAttribute("title");
            }
            if (this.highlight) {
                let leftPct = Math.min(floorPct, cruisePct);
                let widthPct = Math.abs(cruisePct - floorPct);
                this.highlight.style.left = leftPct + "%";
                this.highlight.style.width = widthPct + "%";
            }
            if (this.floorValEl) this.floorValEl.textContent = floor;
            if (this.cruiseValEl) this.cruiseValEl.textContent = cruise;
        }

        calcValFromClientX(clientX) {
            if (!this.container) return 0;
            let rect = this.container.getBoundingClientRect();
            if (rect.width <= 0) return 0;
            let x = clientX - rect.left;
            let pct = Math.max(0, Math.min(1, x / rect.width));
            let rawVal = pct * this.maxVal;
            let snappedVal = Math.round(rawVal / this.step) * this.step;
            return Math.max(this.minVal, Math.min(this.maxVal, snappedVal));
        }

        initEvents() {
            if (!this.container) return;
            let self = this;

            function startDrag(handleType, e) {
                if (currentIsExtAutoFps) return;
                if (currentLodActive) {
                    disengageSmartLodFromManualAction(true);
                }
                e.preventDefault();
                e.stopPropagation();
                self.activeHandle = handleType;
                self.isDragging = true;
                self.hasMovedDuringDrag = false;
                isSliderDragging = true;
                markUserInteracting();

                if (handleType === 'floor') {
                    if (self.floorHandle) self.floorHandle.classList.add("active");
                } else {
                    if (self.cruiseHandle) self.cruiseHandle.classList.add("active");
                }
            }

            if (this.floorHandle) {
                this.floorHandle.addEventListener("mousedown", function (e) { startDrag("floor", e); });
                this.floorHandle.addEventListener("touchstart", function (e) { startDrag("floor", e); }, { passive: false });
            }

            if (this.cruiseHandle) {
                this.cruiseHandle.addEventListener("mousedown", function (e) { startDrag("cruise", e); });
                this.cruiseHandle.addEventListener("touchstart", function (e) { startDrag("cruise", e); }, { passive: false });
            }

            // Click / mousedown on track jumps closest handle
            this.container.addEventListener("mousedown", function (e) {
                if (currentIsExtAutoFps) return;
                if (e.target === self.floorHandle || e.target === self.cruiseHandle) return;
                if (currentLodActive) {
                    disengageSmartLodFromManualAction(true);
                }
                e.preventDefault();
                let clickedVal = self.calcValFromClientX(e.clientX);
                let current = self.getValues();
                let distFloor = Math.abs(clickedVal - current.floor);
                let distCruise = Math.abs(clickedVal - current.cruise);

                let chosenHandle = (distFloor <= distCruise) ? "floor" : "cruise";
                self.activeHandle = chosenHandle;
                self.isDragging = true;
                self.hasMovedDuringDrag = true;
                isSliderDragging = true;
                markUserInteracting();

                if (chosenHandle === "floor") {
                    if (self.floorHandle) self.floorHandle.classList.add("active");
                    let newFloor = Math.min(clickedVal, current.cruise);
                    self.setValues(newFloor, current.cruise);
                    self.updateUI(newFloor, current.cruise);
                    self.onCommit(newFloor);
                } else {
                    if (self.cruiseHandle) self.cruiseHandle.classList.add("active");
                    let newCruise = Math.max(clickedVal, current.floor);
                    self.setValues(current.floor, newCruise);
                    self.updateUI(current.floor, newCruise);
                    self.onCommit(newCruise);
                }
            });

            // Global mouse move & mouse up
            window.addEventListener("mousemove", function (e) {
                if (!self.isDragging || !self.activeHandle) return;
                e.preventDefault();
                self.hasMovedDuringDrag = true;
                markUserInteracting();
                let val = self.calcValFromClientX(e.clientX);
                let current = self.getValues();

                if (self.activeHandle === "floor") {
                    let newFloor = Math.min(val, current.cruise);
                    self.setValues(newFloor, current.cruise);
                    self.updateUI(newFloor, current.cruise);
                    self.onCommit(newFloor);
                } else if (self.activeHandle === "cruise") {
                    let newCruise = Math.max(val, current.floor);
                    self.setValues(current.floor, newCruise);
                    self.updateUI(current.floor, newCruise);
                    self.onCommit(newCruise);
                }
            });

            window.addEventListener("touchmove", function (e) {
                if (!self.isDragging || !self.activeHandle || !e.touches || e.touches.length === 0) return;
                e.preventDefault();
                self.hasMovedDuringDrag = true;
                markUserInteracting();
                let touch = e.touches[0];
                let val = self.calcValFromClientX(touch.clientX);
                let current = self.getValues();

                if (self.activeHandle === "floor") {
                    let newFloor = Math.min(val, current.cruise);
                    self.setValues(newFloor, current.cruise);
                    self.updateUI(newFloor, current.cruise);
                    self.onCommit(newFloor);
                } else if (self.activeHandle === "cruise") {
                    let newCruise = Math.max(val, current.floor);
                    self.setValues(current.floor, newCruise);
                    self.updateUI(current.floor, newCruise);
                    self.onCommit(newCruise);
                }
            }, { passive: false });

            function stopDrag() {
                if (self.isDragging) {
                    let lastHandle = self.activeHandle;
                    let moved = self.hasMovedDuringDrag;
                    self.isDragging = false;
                    self.hasMovedDuringDrag = false;
                    isSliderDragging = false;
                    if (self.floorHandle) self.floorHandle.classList.remove("active");
                    if (self.cruiseHandle) self.cruiseHandle.classList.remove("active");
                    self.activeHandle = null;
                    markUserInteracting();
                    let current = self.getValues();
                    let finalVal = (lastHandle === "cruise") ? current.cruise : current.floor;
                    if (!moved) {
                        self.onCommit(finalVal);
                    } else {
                        sendAxisConfigUpdate(self.axis, finalVal);
                    }
                }
            }

            window.addEventListener("mouseup", stopDrag);
            window.addEventListener("touchend", stopDrag);
            window.addEventListener("touchcancel", stopDrag);
        }
    }

    function disengageSmartLodFromManualAction(skipNetwork) {
        if (!currentLodActive || currentIsExtAutoFps) return;
        currentLodActive = false;
        isSmartLodToggling = true;
        lastSmartLodToggleTime = Date.now();
        markUserInteracting();
        let btnLod = document.getElementById("smart-lod-toggle-btn");
        let lblLod = document.getElementById("smart-lod-btn-label");
        if (btnLod) {
            btnLod.className = "switch-btn switch-off";
            btnLod.setAttribute("aria-checked", "false");
        }
        if (lblLod) lblLod.textContent = "OFF";
        setAxisUiState("tlod", true, false);
        setAxisUiState("olod", true, false);

        setTimeout(function () {
            isSmartLodToggling = false;
        }, 2500);

        if (skipNetwork) return;

        try {
            let xhr = new XMLHttpRequest();
            xhr.open("POST", getApiBase() + "/smart_lod/set_lod", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.timeout = 2500;
            xhr.onload = xhr.onerror = xhr.ontimeout = function () {
                isSmartLodToggling = false;
            };
            xhr.send(JSON.stringify({
                disengage_auto: true,
                mode: currentIsVr ? "VR" : "2D",
                axis: "tlod",
                tlod: currentTlodFloor,
                base: currentTlodFloor,
                target: currentTlodCruise,
                altitude: currentTlodAlt
            }));
        } catch (e) {
            isSmartLodToggling = false;
        }
    }

    function markUserInteracting() {
        isUserInteracting = true;
        if (userInteractionTimeout) clearTimeout(userInteractionTimeout);
        userInteractionTimeout = setTimeout(function () {
            isUserInteracting = false;
        }, 2500);
    }

    let lastAxisSendTime = { tlod: 0, olod: 0 };
    let axisThrottleTimers = { tlod: null, olod: null };

    function queueAxisConfigUpdate(axis, directVal) {
        markUserInteracting();
        let now = Date.now();
        let elapsed = now - (lastAxisSendTime[axis] || 0);
        if (axisThrottleTimers[axis]) {
            clearTimeout(axisThrottleTimers[axis]);
            axisThrottleTimers[axis] = null;
        }
        if (elapsed >= 80) {
            lastAxisSendTime[axis] = now;
            sendAxisConfigUpdate(axis, directVal);
        } else {
            axisThrottleTimers[axis] = setTimeout(function () {
                lastAxisSendTime[axis] = Date.now();
                axisThrottleTimers[axis] = null;
                sendAxisConfigUpdate(axis, directVal);
            }, 80 - elapsed);
        }
    }

    function sendAxisConfigUpdate(axis, directVal) {
        let mode = currentIsVr ? "VR" : "2D";
        let baseVal = (axis === "tlod") ? currentTlodFloor : currentOlodFloor;
        let targetVal = (axis === "tlod") ? currentTlodCruise : currentOlodCruise;
        let altVal = (axis === "tlod") ? currentTlodAlt : currentOlodAlt;

        if (!currentLodActive) {
            let valToWrite = (directVal !== undefined) ? directVal : baseVal;
            let payload = {
                disengage_auto: true,
                mode: mode,
                axis: axis,
                base: baseVal,
                target: targetVal,
                altitude: altVal
            };
            payload[axis] = valToWrite;
            let urlLod = getApiBase() + "/smart_lod/set_lod";
            let xhrLod = new XMLHttpRequest();
            xhrLod.open("POST", urlLod, true);
            xhrLod.setRequestHeader("Content-Type", "application/json");
            xhrLod.timeout = 2500;
            xhrLod.send(JSON.stringify(payload));
        } else {
            let urlCfg = getApiBase() + "/smart_lod/axis_config";
            let xhrCfg = new XMLHttpRequest();
            xhrCfg.open("POST", urlCfg, true);
            xhrCfg.setRequestHeader("Content-Type", "application/json");
            xhrCfg.timeout = 2500;
            xhrCfg.send(JSON.stringify({
                mode: mode,
                axis: axis,
                base: baseVal,
                target: targetVal,
                altitude: altVal
            }));
        }
    }

    function resetToProfile(axis) {
        if (!axis) axis = "all";
        setAxisUiState("tlod", true, false);
        setAxisUiState("olod", true, false);
        isUserInteracting = false;

        let url = getApiBase() + "/smart_lod/reset_to_profile?axis=" + axis + "&_=" + Date.now();
        let xhr = new XMLHttpRequest();
        xhr.open("GET", url, true);
        xhr.timeout = 2000;
        xhr.onload = function () {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    let res = JSON.parse(xhr.responseText);
                    if (res && res.current_tlod !== undefined) {
                        let t = res.current_tlod;
                        let o = res.current_olod;
                        let tCruise = Math.min(400, t + 50);
                        let oCruise = Math.min(300, o + 50);
                        currentTlodFloor = t;
                        currentTlodCruise = tCruise;
                        currentOlodFloor = o;
                        currentOlodCruise = oCruise;
                        if (tlodController) tlodController.updateUI(t, tCruise);
                        if (olodController) olodController.updateUI(o, oCruise);
                    }
                } catch (e) {}
            }
            pollTelemetry();
        };
        xhr.onerror = function () {
            pollTelemetry();
        };
        xhr.send();
    }

    // =========================================================
    // LIVE GRAPHICS ACCORDION & 5-PIN HEADER SYSTEM
    // =========================================================
    const LIVE_GFX_KEYS = ["max_fps", "clouds", "precaching", "terrain_shadows", "buildings", "trees", "plants", "grass"];

    function getQualityLabel(v) {
        let num = Number(v);
        if (num === 0) return pt("q_low");
        if (num === 1) return pt("q_med");
        if (num === 2) return pt("q_high");
        if (num === 3) return pt("q_ultra");
        return pt("q_high");
    }

    let liveGfxValues = {
        max_fps: 36,
        clouds: 2,
        precaching: 2,
        terrain_shadows: 512,
        buildings: 2,
        trees: 2,
        plants: 2,
        grass: 2
    };
    let profileGfxValues = {
        max_fps: 36,
        clouds: 2,
        precaching: 2,
        terrain_shadows: 512,
        buildings: 2,
        trees: 2,
        plants: 2,
        grass: 2
    };
    let stagedGfxValues = {};
    let pinnedGfxKeys = ["max_fps", "clouds", "precaching", "buildings", "trees"];
    let isLiveGfxExpanded = false;
    let lastPinSaveTime = 0;
    let lastLiveGfxApplyTime = 0;
    let lastInCloudRed = false;
    let lastInCloudBoost = false;

    function formatPinnedPillText(key, val) {
        let v = (val !== undefined && val !== null) ? Number(val) : 0;
        switch (key) {
            case "max_fps":
                return pt("pill_max_fps") + " : " + (v > 0 ? v : 36);
            case "clouds":
                return pt("pill_clouds") + " : " + getQualityLabel(v);
            case "precaching":
                return pt("pill_precaching") + " : " + getQualityLabel(v);
            case "terrain_shadows":
                return pt("pill_terrain_shadows") + " : " + (v <= 0 ? pt("q_off") : v);
            case "buildings":
                return pt("pill_buildings") + " : " + getQualityLabel(v);
            case "trees":
                return pt("pill_trees") + " : " + getQualityLabel(v);
            case "plants":
                return pt("pill_plants") + " : " + getQualityLabel(v);
            case "grass":
                return pt("pill_grass") + " : " + getQualityLabel(v);
            default:
                return key + " : " + v;
        }
    }

    function renderPinnedPills(inCloudRed, inCloudBoost) {
        if (inCloudRed !== undefined) lastInCloudRed = !!inCloudRed;
        if (inCloudBoost !== undefined) lastInCloudBoost = !!inCloudBoost;

        let container = document.getElementById("pinned-pills-container");
        if (container) {
            let html = "";
            let keysToShow = (pinnedGfxKeys && pinnedGfxKeys.length > 0) ? pinnedGfxKeys.slice(0, 5) : ["max_fps", "clouds", "precaching", "buildings", "trees"];
            for (let i = 0; i < keysToShow.length; i++) {
                let k = keysToShow[i];
                let v = liveGfxValues[k];
                let txt = formatPinnedPillText(k, v);
                let tip = pt("row_tip_" + k) || txt;
                let styleAttr = "";
                if (k === "clouds") {
                    if (lastInCloudRed) styleAttr = ' style="color: #fbbf24;"';
                    else if (lastInCloudBoost) styleAttr = ' style="color: #10b981;"';
                }
                html += '<span class="hl-tag" data-pin-key="' + k + '" data-scx-tip="' + tip.replace(/"/g, '&quot;') + '"' + styleAttr + '>' + txt + '</span>';
            }
            container.innerHTML = html;
        }

        // Sync pin button active states & counter
        for (let j = 0; j < LIVE_GFX_KEYS.length; j++) {
            let gk = LIVE_GFX_KEYS[j];
            let btn = document.getElementById("lgfx-pin-" + gk);
            if (btn) {
                if (pinnedGfxKeys.indexOf(gk) !== -1) {
                    btn.className = "lgfx-pin-btn pinned";
                } else {
                    btn.className = "lgfx-pin-btn";
                }
            }
        }
        let elCount = document.getElementById("lgfx-pin-count");
        if (elCount) {
            elCount.textContent = String(pinnedGfxKeys.length);
        }
    }

    let openDropdownKey = null;

    function formatLiveGfxDisplayVal(key, val) {
        let v = (val !== undefined && val !== null) ? Number(val) : 0;
        if (key === "max_fps") {
            return String(v > 0 ? v : 36);
        }
        if (key === "terrain_shadows") {
            return v <= 0 ? pt("q_off") : String(v);
        }
        return getQualityLabel(v);
    }

    function closeAllLiveGfxDropdowns() {
        openDropdownKey = null;
        for (let i = 0; i < LIVE_GFX_KEYS.length; i++) {
            let k = LIVE_GFX_KEYS[i];
            let menu = document.getElementById("lgfx-menu-" + k);
            if (menu) menu.className = "lgfx-dropdown-menu hidden";
            let btn = document.getElementById("lgfx-ddbtn-" + k);
            if (btn && k !== "max_fps") {
                btn.className = stagedGfxValues.hasOwnProperty(k) ? "lgfx-dd-trigger dirty" : "lgfx-dd-trigger";
            }
        }
    }

    document.addEventListener("click", function () {
        if (openDropdownKey !== null) {
            closeAllLiveGfxDropdowns();
        }
    });

    function syncLiveGfxSelectsFromTelemetry() {
        let hasDirty = false;
        for (let i = 0; i < LIVE_GFX_KEYS.length; i++) {
            let k = LIVE_GFX_KEYS[i];
            let effectiveVal = stagedGfxValues.hasOwnProperty(k) ? stagedGfxValues[k] : liveGfxValues[k];
            let isDirty = stagedGfxValues.hasOwnProperty(k);
            if (isDirty) hasDirty = true;

            if (k === "max_fps") {
                let inp = document.getElementById("lgfx-input-max_fps");
                let wrap = document.getElementById("lgfx-ctrl-max_fps");
                if (inp && document.activeElement !== inp) {
                    inp.value = String(effectiveVal > 0 ? effectiveVal : 36);
                }
                if (wrap) {
                    wrap.className = isDirty ? "lgfx-combo-wrap dirty" : "lgfx-combo-wrap";
                }
            } else {
                let valSpan = document.getElementById("lgfx-val-" + k);
                if (valSpan) {
                    valSpan.textContent = formatLiveGfxDisplayVal(k, effectiveVal);
                }
                let btn = document.getElementById("lgfx-ddbtn-" + k);
                if (btn) {
                    let cls = "lgfx-dd-trigger";
                    if (openDropdownKey === k) cls += " open";
                    if (isDirty) cls += " dirty";
                    btn.className = cls;
                }
            }

            // Highlight selected option in dropdown menu
            let menu = document.getElementById("lgfx-menu-" + k);
            if (menu) {
                let opts = menu.getElementsByClassName("lgfx-dd-option");
                for (let oi = 0; oi < opts.length; oi++) {
                    let ov = parseInt(opts[oi].getAttribute("data-val"), 10);
                    if (ov === Number(effectiveVal)) {
                        opts[oi].className = "lgfx-dd-option selected";
                    } else {
                        opts[oi].className = "lgfx-dd-option";
                    }
                }
            }

            // Update per-item Reset to Active Profile button state & tooltip
            let resetBtn = document.getElementById("lgfx-reset-" + k);
            if (resetBtn) {
                let profVal = profileGfxValues[k];
                let isModifiedFromProfile = (profVal !== undefined && Number(effectiveVal) !== Number(profVal));
                resetBtn.className = isModifiedFromProfile ? "lgfx-reset-btn modified" : "lgfx-reset-btn";
                resetBtn.setAttribute("data-scx-tip", pt("reset_profile_prefix") + " (" + formatLiveGfxDisplayVal(k, profVal) + ")");
                resetBtn.removeAttribute("title");
            }
        }

        let applyBtn = document.getElementById("lgfx-apply-btn");
        if (applyBtn && applyBtn.className.indexOf("btn-applied") === -1) {
            if (hasDirty) {
                applyBtn.className = "lgfx-apply-btn btn-dirty";
                applyBtn.textContent = pt("apply_dirty_btn");
            } else {
                applyBtn.className = "lgfx-apply-btn";
                applyBtn.textContent = pt("apply_btn");
            }
        }
    }

    window.onToggleLiveGfxAccordion = function (e) {
        if (e && e.stopPropagation) e.stopPropagation();
        closeAllLiveGfxDropdowns();
        isLiveGfxExpanded = !isLiveGfxExpanded;
        let body = document.getElementById("live-gfx-accordion-body");
        let btn = document.getElementById("live-gfx-accordion-btn");
        if (body) {
            if (isLiveGfxExpanded) {
                body.className = "live-gfx-body";
                syncLiveGfxSelectsFromTelemetry();
            } else {
                body.className = "live-gfx-body hidden";
            }
        }
        if (btn) {
            btn.className = isLiveGfxExpanded ? "gfx-accordion-btn expanded" : "gfx-accordion-btn";
        }
        notifyHeight();
        setTimeout(notifyHeight, 30);
        setTimeout(notifyHeight, 120);
    };

    window.onToggleLiveGfxDropdown = function (key, e) {
        if (e && e.stopPropagation) e.stopPropagation();
        if (e && e.preventDefault) e.preventDefault();
        let wasOpen = (openDropdownKey === key);
        closeAllLiveGfxDropdowns();
        if (!wasOpen) {
            openDropdownKey = key;
            let menu = document.getElementById("lgfx-menu-" + key);
            if (menu) {
                menu.className = "lgfx-dropdown-menu";
            }
            let btn = document.getElementById("lgfx-ddbtn-" + key);
            if (btn && key !== "max_fps") {
                btn.className = stagedGfxValues.hasOwnProperty(key) ? "lgfx-dd-trigger open dirty" : "lgfx-dd-trigger open";
            }
            syncLiveGfxSelectsFromTelemetry();
        }
    };

    window.onSelectLiveGfxOption = function (key, rawVal, e) {
        if (e && e.stopPropagation) e.stopPropagation();
        if (e && e.preventDefault) e.preventDefault();
        let numVal = parseInt(rawVal, 10);
        if (isNaN(numVal)) return;

        if (numVal === Number(liveGfxValues[key])) {
            delete stagedGfxValues[key];
        } else {
            stagedGfxValues[key] = numVal;
        }
        if (key === "max_fps") {
            let inp = document.getElementById("lgfx-input-max_fps");
            if (inp) inp.value = String(numVal);
        }
        closeAllLiveGfxDropdowns();
        syncLiveGfxSelectsFromTelemetry();
    };

    window.onLiveGfxManualFpsInput = function (rawVal) {
        let cleaned = String(rawVal || "").replace(/[^0-9]/g, "");
        let inp = document.getElementById("lgfx-input-max_fps");
        if (inp && inp.value !== cleaned) {
            inp.value = cleaned;
        }
        let numVal = parseInt(cleaned, 10);
        if (isNaN(numVal) || numVal <= 0) {
            return;
        }
        if (numVal === Number(liveGfxValues.max_fps)) {
            delete stagedGfxValues.max_fps;
        } else {
            stagedGfxValues.max_fps = numVal;
        }
        syncLiveGfxSelectsFromTelemetry();
    };

    window.onToggleLiveGfxPin = function (key, e) {
        if (e && e.stopPropagation) e.stopPropagation();
        if (e && e.preventDefault) e.preventDefault();
        let idx = pinnedGfxKeys.indexOf(key);
        let hintEl = document.getElementById("lgfx-footer-hint");
        if (idx !== -1) {
            if (pinnedGfxKeys.length <= 1) {
                return;
            }
            pinnedGfxKeys.splice(idx, 1);
        } else {
            if (pinnedGfxKeys.length >= 5) {
                if (hintEl) {
                    hintEl.style.color = "#fbbf24";
                    hintEl.innerHTML = pt("max_pins_reached") + ' (<span id="lgfx-pin-count">5</span>/5)';
                    setTimeout(function () {
                        if (hintEl) {
                            hintEl.style.color = "";
                            hintEl.innerHTML = '<span id="lgfx-pinned-label">' + pt("pinned_count_label") + '</span> <span id="lgfx-pin-count">' + pinnedGfxKeys.length + '</span>/5';
                        }
                    }, 1400);
                }
                return;
            }
            let nextPins = [];
            for (let i = 0; i < LIVE_GFX_KEYS.length; i++) {
                let k = LIVE_GFX_KEYS[i];
                if (k === key || pinnedGfxKeys.indexOf(k) !== -1) {
                    nextPins.push(k);
                }
            }
            pinnedGfxKeys = nextPins.slice(0, 5);
        }

        lastPinSaveTime = Date.now();
        renderPinnedPills();

        let xhr = new XMLHttpRequest();
        xhr.open("POST", getApiBase() + "/smart_lod/save_pins?_=" + Date.now(), true);
        xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        xhr.timeout = 2000;
        xhr.send(JSON.stringify({ pins: pinnedGfxKeys }));
    };

    window.onResetLiveGfxItem = function (key, e) {
        if (e && e.stopPropagation) e.stopPropagation();
        if (e && e.preventDefault) e.preventDefault();
        if (!key || LIVE_GFX_KEYS.indexOf(key) === -1) return;

        closeAllLiveGfxDropdowns();

        delete stagedGfxValues[key];
        let profVal = (profileGfxValues[key] !== undefined && profileGfxValues[key] !== null) ? Number(profileGfxValues[key]) : Number(liveGfxValues[key]);
        liveGfxValues[key] = profVal;
        lastLiveGfxApplyTime = Date.now();

        if (key === "max_fps") {
            let inp = document.getElementById("lgfx-input-max_fps");
            if (inp) inp.value = String(profVal > 0 ? profVal : 36);
        } else if (key === "clouds") {
            lastInCloudRed = false;
            lastInCloudBoost = false;
            let elCloudLiveVal = document.getElementById("cloud-recovery-live-val");
            if (elCloudLiveVal) {
                elCloudLiveVal.textContent = getQualityLabel(profVal).toUpperCase();
                elCloudLiveVal.style.color = "#38bdf8";
            }
        }

        renderPinnedPills();
        syncLiveGfxSelectsFromTelemetry();

        let xhr = new XMLHttpRequest();
        xhr.open("POST", getApiBase() + "/smart_lod/apply_live_graphics?_=" + Date.now(), true);
        xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        xhr.timeout = 3000;
        xhr.onload = function () {
            setTimeout(pollTelemetry, 250);
        };
        xhr.send(JSON.stringify({
            is_vr: currentIsVr,
            reset_keys: [key],
            settings: {}
        }));
    };

    window.onApplyLiveGraphics = function (e) {
        if (e && e.stopPropagation) e.stopPropagation();
        if (e && e.preventDefault) e.preventDefault();

        closeAllLiveGfxDropdowns();

        let fpsInp = document.getElementById("lgfx-input-max_fps");
        if (fpsInp) {
            let typedFps = parseInt(fpsInp.value, 10);
            if (!isNaN(typedFps) && typedFps > 0) {
                let clampedFps = Math.max(15, Math.min(240, typedFps));
                fpsInp.value = String(clampedFps);
                if (clampedFps !== Number(liveGfxValues.max_fps)) {
                    stagedGfxValues.max_fps = clampedFps;
                }
            }
        }

        let payloadSettings = {};
        let prevClouds = Number(liveGfxValues.clouds);
        let stagedKeys = Object.keys(stagedGfxValues);
        if (stagedKeys.length > 0) {
            for (let i = 0; i < stagedKeys.length; i++) {
                let k = stagedKeys[i];
                let nv = Number(stagedGfxValues[k]);
                if (!isNaN(nv)) {
                    payloadSettings[k] = nv;
                    liveGfxValues[k] = nv;
                }
            }
        } else {
            for (let i = 0; i < LIVE_GFX_KEYS.length; i++) {
                let k = LIVE_GFX_KEYS[i];
                if (Number(liveGfxValues[k]) !== Number(profileGfxValues[k])) {
                    payloadSettings[k] = Number(liveGfxValues[k]);
                }
            }
        }
        let cloudsChanged = (payloadSettings.clouds !== undefined && Number(payloadSettings.clouds) !== prevClouds);
        stagedGfxValues = {};
        lastLiveGfxApplyTime = Date.now();

        if (cloudsChanged) {
            currentCloudRecovery = false;
            lastCloudRecoveryToggleTime = Date.now();
            lastInCloudRed = false;
            lastInCloudBoost = false;
            let btnCloud = document.getElementById("cloud-recovery-toggle-btn");
            let lblCloud = document.getElementById("cloud-recovery-btn-label");
            if (btnCloud) {
                btnCloud.className = "switch-btn switch-off";
                btnCloud.setAttribute("aria-checked", "false");
                if (lblCloud) lblCloud.textContent = "OFF";
            }
            let elCloudLiveVal = document.getElementById("cloud-recovery-live-val");
            if (elCloudLiveVal) {
                elCloudLiveVal.textContent = getQualityLabel(payloadSettings.clouds).toUpperCase();
                elCloudLiveVal.style.color = "#38bdf8";
            }
        }

        renderPinnedPills();
        syncLiveGfxSelectsFromTelemetry();

        let applyBtn = document.getElementById("lgfx-apply-btn");
        if (applyBtn) {
            applyBtn.className = "lgfx-apply-btn btn-applied";
            applyBtn.textContent = pt("applied_btn");
            setTimeout(function () {
                let ab = document.getElementById("lgfx-apply-btn");
                if (ab && Object.keys(stagedGfxValues).length === 0) {
                    ab.className = "lgfx-apply-btn";
                    ab.textContent = pt("apply_btn");
                }
            }, 1300);
        }

        let xhr = new XMLHttpRequest();
        xhr.open("POST", getApiBase() + "/smart_lod/apply_live_graphics?_=" + Date.now(), true);
        xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        xhr.timeout = 3000;
        xhr.onload = function () {
            setTimeout(pollTelemetry, 250);
        };
        xhr.send(JSON.stringify({
            is_vr: currentIsVr,
            clouds_changed: cloudsChanged,
            settings: payloadSettings
        }));
    };

    function updateTelemetryUI(data) {
        if (!data) return;

        if (data.language) {
            applyPanelLanguage(data.language);
        }

        currentIsVr = !!data.is_vr;

        // 0. LIVE GRAPHICS & PINNED PILLS HEADER
        if (data.pinned_keys && Array.isArray(data.pinned_keys) && (Date.now() - lastPinSaveTime > 1500)) {
            pinnedGfxKeys = data.pinned_keys.slice(0, 5);
        }
        if (data.profile_graphics) {
            let pg = data.profile_graphics;
            for (let i = 0; i < LIVE_GFX_KEYS.length; i++) {
                let k = LIVE_GFX_KEYS[i];
                if (pg[k] !== undefined && pg[k] !== null) {
                    profileGfxValues[k] = Number(pg[k]);
                }
            }
        }
        if (data.live_graphics && (Date.now() - lastLiveGfxApplyTime > 1500)) {
            let lg = data.live_graphics;
            for (let i = 0; i < LIVE_GFX_KEYS.length; i++) {
                let k = LIVE_GFX_KEYS[i];
                if (lg[k] !== undefined && lg[k] !== null) {
                    liveGfxValues[k] = Number(lg[k]);
                }
            }
        }

        // 1. SMART LOD REGULATION
        let lod = data.smart_lod || {};
        let isExtAutoFps = !!(lod.external_autofps || data.external_autofps);
        currentIsExtAutoFps = isExtAutoFps;
        let lodEnabled = !isExtAutoFps && ((lod.enabled !== undefined) ? !!lod.enabled : (data.smart_lod_enabled !== undefined ? !!data.smart_lod_enabled : false));
        let isProtectedManualTransition = isSmartLodToggling || isSliderDragging || isUserInteracting || (Date.now() - lastSmartLodToggleTime <= 2500);
        if (!isProtectedManualTransition) {
            currentLodActive = isExtAutoFps ? false : lodEnabled;
        }

        let lockMsg = document.getElementById("smart-lod-autofps-lock-msg");
        let controlsBox = document.getElementById("lod-controls-box");
        let btnLod = document.getElementById("smart-lod-toggle-btn");
        let lblLod = document.getElementById("smart-lod-btn-label");

        if (isExtAutoFps) {
            if (lockMsg) lockMsg.className = "";
            if (controlsBox) {
                controlsBox.style.opacity = "0.3";
                controlsBox.style.pointerEvents = "none";
                controlsBox.style.userSelect = "none";
            }
            if (btnLod) {
                btnLod.disabled = true;
                btnLod.className = "switch-btn switch-off";
                btnLod.setAttribute("aria-checked", "false");
                btnLod.style.opacity = "0.3";
                btnLod.style.pointerEvents = "none";
                btnLod.style.cursor = "not-allowed";
                if (lblLod) lblLod.textContent = pt("locked");
            }
        } else {
            if (lockMsg) lockMsg.className = "hidden";
            if (controlsBox) {
                controlsBox.style.opacity = "1";
                controlsBox.style.pointerEvents = "auto";
                controlsBox.style.userSelect = "auto";
            }
            if (btnLod) {
                btnLod.disabled = false;
                btnLod.style.opacity = "1";
                btnLod.style.pointerEvents = "auto";
                btnLod.style.cursor = "pointer";
                if (!isProtectedManualTransition) {
                    if (lodEnabled) {
                        btnLod.className = "switch-btn switch-on";
                        btnLod.setAttribute("aria-checked", "true");
                        if (lblLod) lblLod.textContent = "ON";
                    } else {
                        btnLod.className = "switch-btn switch-off";
                        btnLod.setAttribute("aria-checked", "false");
                        if (lblLod) lblLod.textContent = "OFF";
                    }
                }
            }
        }

        let sTlod = (lod.current_tlod !== undefined && lod.current_tlod !== null) ? lod.current_tlod : (data.smart_lod_tlod !== undefined ? data.smart_lod_tlod : 100);
        let sOlod = (lod.current_olod !== undefined && lod.current_olod !== null) ? lod.current_olod : (data.smart_lod_olod !== undefined ? data.smart_lod_olod : 100);

        currentTlodLive = Math.round(Number(sTlod) || 100);
        currentOlodLive = Math.round(Number(sOlod) || 100);

        let activeEl = document.activeElement;
        let isInputFocused = (activeEl && (activeEl.tagName === 'INPUT'));

        if (!isUserInteracting && !isInputFocused && !isSliderDragging) {
            if (currentLodActive) {
                let tlodFloorVal = lod.tlod_base !== undefined ? lod.tlod_base : 100;
                let tlodCruiseVal = lod.tlod_target !== undefined ? lod.tlod_target : 200;
                let tlodAltVal = lod.tlod_altitude !== undefined ? lod.tlod_altitude : 3000;

                let olodFloorVal = lod.olod_base !== undefined ? lod.olod_base : 100;
                let olodCruiseVal = lod.olod_target !== undefined ? lod.olod_target : 200;
                let olodAltVal = lod.olod_altitude !== undefined ? lod.olod_altitude : 3000;

                currentTlodFloor = tlodFloorVal;
                currentTlodCruise = tlodCruiseVal;
                currentTlodAlt = tlodAltVal;

                currentOlodFloor = olodFloorVal;
                currentOlodCruise = olodCruiseVal;
                currentOlodAlt = olodAltVal;

                if (tlodController) {
                    tlodController.updateUI(currentTlodFloor, currentTlodCruise);
                }
                let tAltInput = document.getElementById("tlod-alt-input");
                if (tAltInput && document.activeElement !== tAltInput) tAltInput.value = currentTlodAlt;

                if (olodController) {
                    olodController.updateUI(currentOlodFloor, currentOlodCruise);
                }
                let oAltInput = document.getElementById("olod-alt-input");
                if (oAltInput && document.activeElement !== oAltInput) oAltInput.value = currentOlodAlt;

                setAxisUiState("tlod", false, false);
                setAxisUiState("olod", false, false);
            } else {
                let nomTlod = lod.nominal_tlod !== undefined ? lod.nominal_tlod : (data.nominal_tlod || 100);
                let nomOlod = lod.nominal_olod !== undefined ? lod.nominal_olod : (data.nominal_olod || 100);

                let tlodFloorVal = (lod.tlod_base !== undefined) ? lod.tlod_base : nomTlod;
                let tlodCruiseVal = (lod.tlod_target !== undefined) ? lod.tlod_target : nomTlod;
                let tlodAltVal = (lod.tlod_altitude !== undefined) ? lod.tlod_altitude : 3000;

                let olodFloorVal = (lod.olod_base !== undefined) ? lod.olod_base : nomOlod;
                let olodCruiseVal = (lod.olod_target !== undefined) ? lod.olod_target : nomOlod;
                let olodAltVal = (lod.olod_altitude !== undefined) ? lod.olod_altitude : 3000;

                currentTlodFloor = tlodFloorVal;
                currentTlodCruise = tlodCruiseVal;
                currentTlodAlt = tlodAltVal;

                currentOlodFloor = olodFloorVal;
                currentOlodCruise = olodCruiseVal;
                currentOlodAlt = olodAltVal;

                if (tlodController) {
                    tlodController.updateUI(currentTlodFloor, currentTlodCruise);
                }
                let tAltInput = document.getElementById("tlod-alt-input");
                if (tAltInput && document.activeElement !== tAltInput) tAltInput.value = currentTlodAlt;

                if (olodController) {
                    olodController.updateUI(currentOlodFloor, currentOlodCruise);
                }
                let oAltInput = document.getElementById("olod-alt-input");
                if (oAltInput && document.activeElement !== oAltInput) oAltInput.value = currentOlodAlt;

                setAxisUiState("tlod", true, false);
                setAxisUiState("olod", true, false);
            }
        }

        // Auto Cloud Recovery UI & Live Cloud Quality badge update
        let cloudRec = (lod.cloud_recovery !== undefined) ? !!lod.cloud_recovery : (data.cloud_recovery !== undefined ? !!data.cloud_recovery : true);
        if (!isCloudRecoveryToggling && (Date.now() - lastCloudRecoveryToggleTime > 1200)) {
            currentCloudRecovery = cloudRec;
            let btnCloud = document.getElementById("cloud-recovery-toggle-btn");
            let lblCloud = document.getElementById("cloud-recovery-btn-label");
            if (btnCloud) {
                if (cloudRec) {
                    btnCloud.className = "switch-btn switch-on";
                    btnCloud.setAttribute("aria-checked", "true");
                    if (lblCloud) lblCloud.textContent = "ON";
                } else {
                    btnCloud.className = "switch-btn switch-off";
                    btnCloud.setAttribute("aria-checked", "false");
                    if (lblCloud) lblCloud.textContent = "OFF";
                }
            }
        }

        let cloudQualNum = (liveGfxValues.clouds !== undefined) ? Number(liveGfxValues.clouds) : 2;
        let cloudLbl = getQualityLabel(cloudQualNum).toUpperCase();
        let inCloudRed = !!(lod.in_cloud_reduction || data.in_cloud_reduction);
        let inCloudBoost = !!(lod.in_cloud_boost || data.in_cloud_boost);
        let elCloudLiveVal = document.getElementById("cloud-recovery-live-val");
        if (elCloudLiveVal) {
            elCloudLiveVal.textContent = cloudLbl;
            if (inCloudRed) {
                elCloudLiveVal.style.color = "#fbbf24";
            } else if (inCloudBoost) {
                elCloudLiveVal.style.color = "#10b981";
            } else {
                elCloudLiveVal.style.color = "#38bdf8";
            }
        }
        renderPinnedPills(inCloudRed, inCloudBoost);
        if (isLiveGfxExpanded) {
            syncLiveGfxSelectsFromTelemetry();
        }

        // 2. LIVE PERFORMANCE
        let perf = data.perf || {};
        let dispFps = (perf.displayed_fps !== undefined && perf.displayed_fps !== null) ? perf.displayed_fps : (data.displayed_fps || 0);
        let baseFps = (perf.fps !== undefined && perf.fps !== null) ? perf.fps : (data.base_fps || 0);
        let mtMs = (perf.main_thread_ms !== undefined && perf.main_thread_ms !== null) ? perf.main_thread_ms : (data.main_thread_ms || 0);
        let pacing = (perf.frame_pacing || "OPTIMAL").toUpperCase();

        let elFps = document.getElementById("live-fps-val");
        if (elFps) elFps.textContent = (dispFps && dispFps > 0) ? Math.round(dispFps) : "--";

        let elBase = document.getElementById("live-fps-base");
        if (elBase) elBase.textContent = (baseFps && baseFps > 0) ? Math.round(baseFps) : "--";

        let elMt = document.getElementById("live-mt-val");
        if (elMt) elMt.textContent = (mtMs && mtMs > 0) ? Number(mtMs).toFixed(1) : "--";

        let elPacingBadge = document.getElementById("live-pacing-status");
        if (elPacingBadge) {
            if (pacing === "OPTIMAL" || pacing === "FLUIDE") {
                elPacingBadge.className = "badge-tag badge-optimal";
                elPacingBadge.textContent = pt("pacing_optimal");
            } else if (pacing === "ACCEPTABLE" || pacing === "CHARGE" || pacing === "CHARGÉ") {
                elPacingBadge.className = "badge-tag badge-acceptable";
                elPacingBadge.textContent = pt("pacing_acceptable");
            } else {
                elPacingBadge.className = "badge-tag badge-heavy";
                elPacingBadge.textContent = pt("pacing_heavy");
            }
        }

        // 3. BLACKBOX RECORDER STATUS & SPARKLINE TREND GRAPH
        let isRec = (data.blackbox_recording !== undefined) ? !!data.blackbox_recording : !!data.is_tracking;
        let btnRec = document.getElementById("blackbox-toggle-btn");
        let lblRec = document.getElementById("rec-btn-label");
        if (btnRec && !isBlackboxToggling) {
            if (isRec) {
                btnRec.className = "msfs-btn btn-rec-stop";
                if (lblRec) lblRec.textContent = pt("stop_mon");
            } else {
                btnRec.className = "msfs-btn btn-rec-start";
                if (lblRec) lblRec.textContent = pt("start_mon");
            }
        }

        if (isRec && !wasRecording) {
            fpsHistory = [];
        }
        wasRecording = isRec;

        if (isRec && dispFps && dispFps > 0) {
            fpsHistory.push(Math.round(dispFps));
            if (fpsHistory.length > MAX_HISTORY_POINTS) {
                fpsHistory.shift();
            }
            drawSparkline();
        } else {
            drawSparkline();
        }

        // 4. SYSTEM METRICS (GPU, CPU, VRAM, CACHE)
        let elGpu = document.getElementById("live-gpu-val");
        if (elGpu) {
            let gpuPct = (data.gpu_util_pct !== undefined && data.gpu_util_pct !== null) ? data.gpu_util_pct : 0;
            elGpu.textContent = Math.round(Number(gpuPct) || 0);
        }
        let elGpuTemp = document.getElementById("live-gpu-temp");
        if (elGpuTemp) {
            let gpuTemp = (data.gpu_temp_c !== undefined && data.gpu_temp_c !== null) ? data.gpu_temp_c : (data.gpu_temp !== undefined ? data.gpu_temp : "--");
            let numGpu = Number(gpuTemp);
            elGpuTemp.textContent = (gpuTemp !== "--" && !isNaN(numGpu) && numGpu > 0) ? Math.round(numGpu) : "--";
        }

        let elCpu = document.getElementById("live-cpu-val");
        if (elCpu) {
            let cpuPct = (data.cpu_pct !== undefined && data.cpu_pct !== null) ? data.cpu_pct : 0;
            elCpu.textContent = Math.round(Number(cpuPct) || 0);
        }
        let elCpuTemp = document.getElementById("live-cpu-temp");
        if (elCpuTemp) {
            let cpuTemp = (data.cpu_temp_c !== undefined && data.cpu_temp_c !== null) ? data.cpu_temp_c : (data.cpu_temp !== undefined ? data.cpu_temp : "--");
            let numCpu = Number(cpuTemp);
            elCpuTemp.textContent = (cpuTemp !== "--" && !isNaN(numCpu) && numCpu > 0) ? Math.round(numCpu) : "--";
        }

        let elVram = document.getElementById("live-vram-val");
        if (elVram) {
            let vramUsed = data.vram_used_gb !== undefined ? data.vram_used_gb : "--";
            let vramTot = data.vram_total_gb !== undefined ? data.vram_total_gb : "--";
            if (vramUsed !== "--" && vramTot !== "--") {
                let vramTotClean = (typeof vramTot === 'number' && vramTot % 1 === 0) ? vramTot.toFixed(0) : vramTot;
                elVram.textContent = vramUsed + " / " + vramTotClean;
            } else {
                elVram.textContent = "--";
            }
        }

        let elCache = document.getElementById("live-cache-val");
        if (elCache) {
            let cacheVal = data.rolling_cache_gb !== undefined ? data.rolling_cache_gb : 0.0;
            elCache.textContent = Number(cacheVal).toFixed(1);
        }
    }

    let consecutiveFailures = 0;
    let isPollingTelemetry = false;
    const DISCONNECT_FAILURE_THRESHOLD = 5;
    let lastNotifiedHeight = 0;

    function measureNaturalContentHeight() {
        let connView = document.getElementById("connected-view");
        let isConn = (connView && connView.style.display !== "none" && !connView.classList.contains("hidden"));
        if (!isConn) {
            return 220;
        }
        let sum = 14; // top + bottom padding of .main-content
        let children = connView.children;
        for (let i = 0; i < children.length; i++) {
            let ch = children[i];
            if (!ch || ch.classList.contains("hidden") || ch.style.display === "none") continue;
            let h = ch.offsetHeight || Math.ceil(ch.getBoundingClientRect().height) || 0;
            sum += h + 6;
        }
        return Math.max(495, sum);
    }

    function notifyHeight(forceUpdate) {
        let connView = document.getElementById("connected-view");
        let isConn = (connView && connView.style.display !== "none" && !connView.classList.contains("hidden"));
        let naturalH = measureNaturalContentHeight();

        // 1. Desktop Preview iframe auto-fit notification
        if (window.parent && window.parent !== window) {
            if (document.body && !document.body.classList.contains("is-desktop-preview")) {
                document.body.classList.add("is-desktop-preview");
            }
            window.parent.postMessage({ type: "SCENERYX_PANEL_RESIZE", height: naturalH }, "*");
            return;
        }

        // 2. Native MSFS 2020/2024 In-Game Panel window height sync
        let ingameUi = document.getElementById("SceneryX_Remote");
        if (ingameUi) {
            ingameUi.classList.remove("minimized");
            if (ingameUi.getAttribute("title") !== "SCENERY X") {
                ingameUi.setAttribute("title", "SCENERY X");
            }
            let headerEl = ingameUi.querySelector("ingame-ui-header");
            if (headerEl && headerEl.getAttribute("title") !== "SCENERY X") {
                headerEl.setAttribute("title", "SCENERY X");
            }
            let headerH = headerEl ? Math.max(32, Math.ceil(headerEl.getBoundingClientRect().height || 36)) : 36;
            let minTotal = isConn ? 520 : 160;
            let msfsTargetH = Math.max(minTotal, naturalH + headerH + 6);
            if (forceUpdate || Math.abs(msfsTargetH - lastNotifiedHeight) >= 3) {
                lastNotifiedHeight = msfsTargetH;
                try {
                    if (typeof ingameUi.sendUpdatePanelSize === "function") {
                        ingameUi.sendUpdatePanelSize();
                    }
                    if (typeof ingameUi.sendRect === "function") {
                        ingameUi.sendRect();
                    }
                } catch (e) {}
                try {
                    if (typeof Coherent !== "undefined" && typeof Coherent.trigger === "function") {
                        Coherent.trigger("UPDATE_PANEL_HEIGHT", ingameUi.panelID || "PANEL_SCENERYX", msfsTargetH);
                    }
                } catch (e) {}
            }
        }
    }
    window.sceneryxNotifyHeight = notifyHeight;
    window.sceneryxForcePanelHeight = function () {
        lastNotifiedHeight = 0;
        notifyHeight(true);
    };

    function pollTelemetry() {
        if (isPollingTelemetry) return;
        isPollingTelemetry = true;
        let url = getApiBase() + "/telemetry?_=" + Date.now();

        function handleSuccess(data) {
            isPollingTelemetry = false;
            consecutiveFailures = 0;
            setConnectedState(true);
            try {
                updateTelemetryUI(data);
                notifyHeight();
            } catch (e) {
                console.error("[SceneryX] UI update error:", e);
            }
        }

        function handleFailure() {
            isPollingTelemetry = false;
            consecutiveFailures++;
            let isExplicitPreview = (typeof window !== "undefined" && window.location && window.location.search && window.location.search.indexOf("preview=1") !== -1);
            if (isExplicitPreview && consecutiveFailures >= 2) {
                setConnectedState(true);
                updateTelemetryUI({
                    app_running: true,
                    perf: {
                        displayed_fps: 72,
                        fps: 36,
                        main_thread_ms: 13.8,
                        frame_pacing: "OPTIMAL"
                    },
                    smart_lod: {
                        active: false,
                        current_tlod: currentTlodLive || 100,
                        current_olod: currentOlodLive || 100,
                        tlod_base: currentTlodFloor || 100,
                        tlod_target: currentTlodCruise || 200,
                        tlod_altitude: currentTlodAlt || 3000,
                        olod_base: currentOlodFloor || 100,
                        olod_target: currentOlodCruise || 200,
                        olod_altitude: currentOlodAlt || 3000
                    },
                    gpu_util_pct: 82,
                    gpu_temp_c: 62,
                    cpu_pct: 44,
                    cpu_temp_c: 58,
                    vram_used_gb: 7.4,
                    vram_total_gb: 16.0,
                    rolling_cache_gb: 12.5,
                    blackbox_recording: false
                });
                notifyHeight();
                return;
            }
            if (!isConnected || consecutiveFailures >= DISCONNECT_FAILURE_THRESHOLD) {
                setConnectedState(false);
                notifyHeight();
            }
        }

        tryXhr(url, handleSuccess, handleFailure);
    }

    function tryXhr(url, onSuccess, onError) {
        try {
            let xhr = new XMLHttpRequest();
            xhr.open("GET", url, true);
            xhr.timeout = 3500;
            xhr.onload = function () {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        let data = JSON.parse(xhr.responseText);
                        onSuccess(data);
                    } catch (e) {
                        onError();
                    }
                } else {
                    onError();
                }
            };
            xhr.onerror = onError;
            xhr.ontimeout = onError;
            xhr.send();
        } catch (e) {
            onError();
        }
    }

    function drawSparkline() {
        let canvas = document.getElementById("fps-sparkline-canvas");
        if (!canvas || !canvas.getContext) return;

        let ctx = canvas.getContext("2d");
        let w = canvas.width;
        let h = canvas.height;

        ctx.clearRect(0, 0, w, h);

        if (fpsHistory.length < 2) {
            ctx.beginPath();
            ctx.setLineDash([4, 4]);
            ctx.moveTo(0, Math.floor(h / 2));
            ctx.lineTo(w, Math.floor(h / 2));
            ctx.strokeStyle = "#334155";
            ctx.lineWidth = 1;
            ctx.stroke();
            ctx.setLineDash([]);
            let elDelta = document.getElementById("fps-delta-label");
            if (elDelta) {
                elDelta.textContent = pt("standby");
                elDelta.className = "delta-label delta-neutral";
            }
            return;
        }

        let minVal = 999999;
        let maxVal = -999999;
        for (let i = 0; i < fpsHistory.length; i++) {
            let val = fpsHistory[i];
            if (val < minVal) minVal = val;
            if (val > maxVal) maxVal = val;
        }

        if (maxVal - minVal < 4) {
            maxVal += 2;
            minVal = Math.max(0, minVal - 2);
        }

        let range = maxVal - minVal || 1;
        let stepX = w / (MAX_HISTORY_POINTS - 1);
        let startIdx = MAX_HISTORY_POINTS - fpsHistory.length;

        let grad = ctx.createLinearGradient(0, 0, 0, h);
        grad.addColorStop(0, "rgba(2, 132, 199, 0.4)");
        grad.addColorStop(1, "rgba(2, 132, 199, 0.0)");

        ctx.beginPath();
        for (let i = 0; i < fpsHistory.length; i++) {
            let x = (startIdx + i) * stepX;
            let norm = (fpsHistory[i] - minVal) / range;
            let y = h - (norm * (h - 6)) - 3;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.lineTo((startIdx + fpsHistory.length - 1) * stepX, h);
        ctx.lineTo(startIdx * stepX, h);
        ctx.closePath();
        ctx.fillStyle = grad;
        ctx.fill();

        ctx.beginPath();
        for (let i = 0; i < fpsHistory.length; i++) {
            let x = (startIdx + i) * stepX;
            let norm = (fpsHistory[i] - minVal) / range;
            let y = h - (norm * (h - 6)) - 3;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = "#38bdf8";
        ctx.lineWidth = 2;
        ctx.stroke();

        let first = fpsHistory[0];
        let last = fpsHistory[fpsHistory.length - 1];
        let delta = Math.round(last - first);

        let elDelta = document.getElementById("fps-delta-label");
        if (elDelta) {
            if (delta > 0) {
                elDelta.textContent = "+" + delta + " FPS";
                elDelta.className = "delta-label delta-up";
            } else if (delta < 0) {
                elDelta.textContent = delta + " FPS";
                elDelta.className = "delta-label delta-down";
            } else {
                elDelta.textContent = "0 FPS";
                elDelta.className = "delta-label delta-neutral";
            }
        }
    }

    function sendToggleRequest(path, targetState, onComplete) {
        let qs = "?enabled=" + (targetState ? "true" : "false") + "&_=" + Date.now();
        let fullUrl = getApiBase() + path + qs;

        let called = false;
        let safetyTimer = null;

        function finish(data) {
            if (called) return;
            called = true;
            if (safetyTimer) {
                clearTimeout(safetyTimer);
                safetyTimer = null;
            }
            if (onComplete) onComplete(data);
        }

        safetyTimer = setTimeout(function () {
            finish({ success: true, enabled: targetState, cloud_recovery: targetState });
        }, 2200);

        try {
            let xhr = new XMLHttpRequest();
            xhr.open("GET", fullUrl, true);
            xhr.timeout = 2000;
            xhr.onload = function () {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        let data = JSON.parse(xhr.responseText);
                        finish(data);
                    } catch (e) {
                        finish({ success: true, enabled: targetState, cloud_recovery: targetState });
                    }
                } else {
                    finish({ success: false, enabled: targetState, cloud_recovery: targetState });
                }
            };
            xhr.onerror = function () {
                finish({ success: false, enabled: targetState, cloud_recovery: targetState });
            };
            xhr.ontimeout = function () {
                finish({ success: false, enabled: targetState, cloud_recovery: targetState });
            };
            xhr.send();
        } catch (e) {
            finish({ success: false, enabled: targetState, cloud_recovery: targetState });
        }
    }

    function onSmartLodClick(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        if (currentIsExtAutoFps) return;
        let now = Date.now();
        if (now - lastSmartLodToggleTime < 250) return;
        lastSmartLodToggleTime = now;

        isUserInteracting = false;
        isSliderDragging = false;
        if (userInteractionTimeout) {
            clearTimeout(userInteractionTimeout);
            userInteractionTimeout = null;
        }
        if (debounceTimer) {
            clearTimeout(debounceTimer);
            debounceTimer = null;
        }

        let btnLod = document.getElementById("smart-lod-toggle-btn");
        let lblLod = document.getElementById("smart-lod-btn-label");
        let isCurrentlyOn = btnLod ? btnLod.classList.contains("switch-on") : currentLodActive;
        let targetState = !isCurrentlyOn;

        currentLodActive = targetState;
        isSmartLodToggling = true;
        if (btnLod) {
            if (targetState) {
                btnLod.className = "switch-btn switch-on";
                btnLod.setAttribute("aria-checked", "true");
                if (lblLod) lblLod.textContent = "ON";
                setAxisUiState("tlod", false, false);
                setAxisUiState("olod", false, false);
            } else {
                btnLod.className = "switch-btn switch-off";
                btnLod.setAttribute("aria-checked", "false");
                if (lblLod) lblLod.textContent = "OFF";
                setAxisUiState("tlod", true, false);
                setAxisUiState("olod", true, false);
            }
        }

        setTimeout(function () {
            isSmartLodToggling = false;
        }, 1500);

        sendToggleRequest("/smart_lod/toggle", targetState, function (data) {
            isSmartLodToggling = false;
            isUserInteracting = false;
            if (data && data.enabled !== undefined) {
                currentLodActive = !!data.enabled;
            }
            if (btnLod) {
                btnLod.className = currentLodActive ? "switch-btn switch-on" : "switch-btn switch-off";
                btnLod.setAttribute("aria-checked", currentLodActive ? "true" : "false");
                if (lblLod) lblLod.textContent = currentLodActive ? "ON" : "OFF";
            }
            if (currentLodActive && data) {
                let tFloor = (data.tlod_base !== undefined) ? data.tlod_base : currentTlodFloor;
                let tCruise = (data.tlod_target !== undefined) ? data.tlod_target : currentTlodCruise;
                let tAlt = (data.tlod_altitude !== undefined) ? data.tlod_altitude : currentTlodAlt;
                let oFloor = (data.olod_base !== undefined) ? data.olod_base : currentOlodFloor;
                let oCruise = (data.olod_target !== undefined) ? data.olod_target : currentOlodCruise;
                let oAlt = (data.olod_altitude !== undefined) ? data.olod_altitude : currentOlodAlt;

                currentTlodFloor = tFloor;
                currentTlodCruise = tCruise;
                currentTlodAlt = tAlt;
                currentOlodFloor = oFloor;
                currentOlodCruise = oCruise;
                currentOlodAlt = oAlt;

                if (tlodController) tlodController.updateUI(tFloor, tCruise);
                if (olodController) olodController.updateUI(oFloor, oCruise);
                let tAltInput = document.getElementById("tlod-alt-input");
                if (tAltInput) tAltInput.value = tAlt;
                let oAltInput = document.getElementById("olod-alt-input");
                if (oAltInput) oAltInput.value = oAlt;

                setAxisUiState("tlod", false, false);
                setAxisUiState("olod", false, false);
            } else if (!currentLodActive && data) {
                let nomT = data.nominal_tlod || data.tlod || 100;
                let nomO = data.nominal_olod || data.olod || 100;
                let cruiseT = data.tlod_target !== undefined ? data.tlod_target : Math.min(400, nomT + 50);
                let cruiseO = data.olod_target !== undefined ? data.olod_target : Math.min(300, nomO + 50);
                currentTlodFloor = nomT;
                currentTlodCruise = cruiseT;
                currentOlodFloor = nomO;
                currentOlodCruise = cruiseO;
                if (tlodController) tlodController.updateUI(nomT, cruiseT);
                if (olodController) olodController.updateUI(nomO, cruiseO);
                setAxisUiState("tlod", true, false);
                setAxisUiState("olod", true, false);
            }
            pollTelemetry();
        });
    }
    window.onSmartLodClick = onSmartLodClick;

    function onCloudRecoveryClick(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        let now = Date.now();
        if (now - lastCloudRecoveryToggleTime < 300) return;
        lastCloudRecoveryToggleTime = now;

        let btnCloud = document.getElementById("cloud-recovery-toggle-btn");
        let lblCloud = document.getElementById("cloud-recovery-btn-label");
        let isCurrentlyOn = btnCloud ? btnCloud.classList.contains("switch-on") : currentCloudRecovery;
        let targetState = !isCurrentlyOn;

        currentCloudRecovery = targetState;
        isCloudRecoveryToggling = true;
        if (btnCloud) {
            if (targetState) {
                btnCloud.className = "switch-btn switch-on";
                btnCloud.setAttribute("aria-checked", "true");
                if (lblCloud) lblCloud.textContent = "ON";
            } else {
                btnCloud.className = "switch-btn switch-off";
                btnCloud.setAttribute("aria-checked", "false");
                if (lblCloud) lblCloud.textContent = "OFF";
            }
        }

        if (targetState) {
            delete stagedGfxValues.clouds;
            if (profileGfxValues && profileGfxValues.clouds !== undefined) {
                liveGfxValues.clouds = Number(profileGfxValues.clouds);
            }
            let liveCloudValEl = document.getElementById("cloud-recovery-live-val");
            if (liveCloudValEl && liveGfxValues.clouds !== undefined) {
                liveCloudValEl.textContent = getQualityLabel(liveGfxValues.clouds).toUpperCase();
            }
            renderPinnedPills();
            syncLiveGfxSelectsFromTelemetry();
        }

        setTimeout(function () {
            isCloudRecoveryToggling = false;
        }, 1500);

        sendToggleRequest("/smart_lod/cloud_recovery", targetState, function (data) {
            isCloudRecoveryToggling = false;
            if (data && data.cloud_recovery !== undefined) {
                currentCloudRecovery = !!data.cloud_recovery;
            } else if (data && data.enabled !== undefined) {
                currentCloudRecovery = !!data.enabled;
            }
            if (btnCloud) {
                btnCloud.className = currentCloudRecovery ? "switch-btn switch-on" : "switch-btn switch-off";
                btnCloud.setAttribute("aria-checked", currentCloudRecovery ? "true" : "false");
                if (lblCloud) lblCloud.textContent = currentCloudRecovery ? "ON" : "OFF";
            }
            if (currentCloudRecovery && data && data.cloud_quality !== undefined) {
                delete stagedGfxValues.clouds;
                liveGfxValues.clouds = Number(data.cloud_quality);
                let liveCloudValEl = document.getElementById("cloud-recovery-live-val");
                if (liveCloudValEl) {
                    liveCloudValEl.textContent = getQualityLabel(liveGfxValues.clouds).toUpperCase();
                }
                renderPinnedPills();
                syncLiveGfxSelectsFromTelemetry();
            }
            pollTelemetry();
        });
    }
    window.onCloudRecoveryClick = onCloudRecoveryClick;

    function onBlackboxClick(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        isBlackboxToggling = true;
        let btnRec = document.getElementById("blackbox-toggle-btn");
        let lblRec = document.getElementById("rec-btn-label");
        let willStart = !wasRecording;
        if (willStart) {
            if (btnRec) btnRec.className = "msfs-btn btn-rec-stop";
            if (lblRec) lblRec.textContent = pt("stop_mon");
            fpsHistory = [];
            drawSparkline();
        } else {
            if (btnRec) btnRec.className = "msfs-btn btn-rec-start";
            if (lblRec) lblRec.textContent = pt("start_mon");
        }

        let url = getApiBase() + "/blackbox/toggle";
        let xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.timeout = 6000;
        xhr.onload = function () {
            isBlackboxToggling = false;
            pollTelemetry();
        };
        xhr.onerror = function () { isBlackboxToggling = false; };
        xhr.ontimeout = function () { isBlackboxToggling = false; };
        xhr.send();
    }
    window.onBlackboxClick = onBlackboxClick;

    function setupAxis(axis) {
        let maxVal = (axis === "tlod") ? 400 : 300;
        let altInput = document.getElementById(axis + "-alt-input");
        let badge = document.getElementById(axis + "-mode-badge");

        let controller = new DualSliderController(
            axis,
            maxVal,
            function () {
                return (axis === "tlod")
                    ? { floor: currentTlodFloor, cruise: currentTlodCruise }
                    : { floor: currentOlodFloor, cruise: currentOlodCruise };
            },
            function (f, c) {
                if (axis === "tlod") {
                    currentTlodFloor = f;
                    currentTlodCruise = c;
                } else {
                    currentOlodFloor = f;
                    currentOlodCruise = c;
                }
            },
            function (directVal) {
                if (currentIsExtAutoFps) return;
                if (currentLodActive) {
                    disengageSmartLodFromManualAction(true);
                }
                setAxisUiState(axis, true, false);
                queueAxisConfigUpdate(axis, directVal);
            }
        );

        if (axis === "tlod") tlodController = controller;
        else olodController = controller;

        let btnAltDown = document.getElementById(axis + "-alt-down");
        let btnAltUp = document.getElementById(axis + "-alt-up");

        function adjustAlt(delta) {
            if (currentIsExtAutoFps) return;
            if (currentLodActive) {
                disengageSmartLodFromManualAction();
            }
            let currentVal = (axis === "tlod") ? currentTlodAlt : currentOlodAlt;
            let nextVal = Math.max(500, Math.min(45000, currentVal + delta));
            if (axis === "tlod") currentTlodAlt = nextVal;
            else currentOlodAlt = nextVal;
            if (altInput) altInput.value = nextVal;
            setAxisUiState(axis, true, false);
            queueAxisConfigUpdate(axis);
        }

        if (btnAltDown) {
            btnAltDown.addEventListener("click", function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (currentIsExtAutoFps) return;
                let step = e.shiftKey ? 500 : 100;
                adjustAlt(-step);
            });
        }

        if (btnAltUp) {
            btnAltUp.addEventListener("click", function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (currentIsExtAutoFps) return;
                let step = e.shiftKey ? 500 : 100;
                adjustAlt(step);
            });
        }

        if (altInput) {
            altInput.addEventListener("change", function () {
                if (currentIsExtAutoFps) return;
                if (currentLodActive) {
                    disengageSmartLodFromManualAction();
                }
                let num = Math.max(500, Math.min(45000, parseInt(altInput.value, 10) || 5000));
                altInput.value = num;
                if (axis === "tlod") currentTlodAlt = num;
                else currentOlodAlt = num;
                setAxisUiState(axis, true, false);
                queueAxisConfigUpdate(axis);
            });
        }

        if (badge) {
            badge.addEventListener("click", function () {
                if (!currentLodActive) {
                    resetToProfile(axis);
                }
            });
        }
    }

    // CoherentGT & Webview resilient contextual tooltip controller
    function initCustomTooltip() {
        let tipEl = document.getElementById("scx-custom-tooltip");
        if (!tipEl) return;
        let tipTimer = null;
        let activeTarget = null;

        function isMsfsShellNode(el) {
            if (!el) return true;
            if (el.id === "SceneryX_Remote") return true;
            let tag = (el.tagName || "").toUpperCase();
            if (tag === "INGAME-UI" || tag === "INGAME-UI-HEADER" || tag === "INGAMEPANEL-SCENERYX") return true;
            if (el.closest && el.closest("ingame-ui-header")) return true;
            return false;
        }

        function findTitledElement(el) {
            while (el && el !== document && el !== document.body) {
                if (isMsfsShellNode(el)) {
                    break;
                }
                if (el.getAttribute) {
                    let scxTip = el.getAttribute("data-scx-tip");
                    let nativeTitle = el.getAttribute("title");
                    if (nativeTitle) {
                        if (nativeTitle !== "null" && nativeTitle !== "undefined" && nativeTitle !== "SCENERY X") {
                            el.setAttribute("data-scx-tip", nativeTitle);
                            scxTip = nativeTitle;
                        }
                        el.removeAttribute("title");
                    }
                    if (scxTip && scxTip !== "null" && scxTip !== "undefined") {
                        return el;
                    }
                }
                el = el.parentElement;
            }
            return null;
        }

        function positionTip(clientX, clientY) {
            let vw = window.innerWidth || document.documentElement.clientWidth || 500;
            let vh = window.innerHeight || document.documentElement.clientHeight || 500;
            let rect = tipEl.getBoundingClientRect();
            let tw = rect.width || 180;
            let th = rect.height || 28;
            let left = clientX + 10;
            let top = clientY + 16;
            if (left + tw + 8 > vw) {
                left = Math.max(6, vw - tw - 8);
            }
            if (top + th + 8 > vh) {
                top = Math.max(6, clientY - th - 8);
            }
            tipEl.style.left = left + "px";
            tipEl.style.top = top + "px";
        }

        document.addEventListener("mouseover", function (e) {
            let target = findTitledElement(e.target);
            if (!target) {
                activeTarget = null;
                if (tipTimer) { clearTimeout(tipTimer); tipTimer = null; }
                tipEl.className = "scx-custom-tooltip hidden";
                return;
            }
            if (target === activeTarget) return;
            activeTarget = target;
            if (tipTimer) clearTimeout(tipTimer);
            let cx = e.clientX;
            let cy = e.clientY;
            tipTimer = setTimeout(function () {
                if (!activeTarget || isMsfsShellNode(activeTarget)) return;
                let text = activeTarget.getAttribute("data-scx-tip") || activeTarget.getAttribute("title");
                if (activeTarget.getAttribute("title") && !isMsfsShellNode(activeTarget)) {
                    activeTarget.setAttribute("data-scx-tip", activeTarget.getAttribute("title"));
                    activeTarget.removeAttribute("title");
                }
                if (!text || text === "null" || text === "undefined" || text === "SCENERY X") return;
                tipEl.textContent = text;
                tipEl.className = "scx-custom-tooltip";
                positionTip(cx, cy);
            }, 320);
        });

        document.addEventListener("mousemove", function (e) {
            if (activeTarget && tipEl.className.indexOf("hidden") === -1) {
                positionTip(e.clientX, e.clientY);
            }
        });

        document.addEventListener("mousedown", function () {
            if (tipTimer) { clearTimeout(tipTimer); tipTimer = null; }
            tipEl.className = "scx-custom-tooltip hidden";
        });
    }

    function init() {
        let discView = document.getElementById("disconnected-view");
        let connView = document.getElementById("connected-view");
        if (!discView || !connView) {
            setTimeout(init, 100);
            return;
        }

        window.addEventListener("mouseup", function () {
            if (isSliderDragging) {
                isSliderDragging = false;
                markUserInteracting();
            }
        });
        window.addEventListener("touchend", function () {
            if (isSliderDragging) {
                isSliderDragging = false;
                markUserInteracting();
            }
        });
        window.addEventListener("resize", function () {
            lastNotifiedHeight = 0;
            notifyHeight();
        });

        let btnLod = document.getElementById("smart-lod-toggle-btn");
        if (btnLod) {
            btnLod.onclick = null;
            btnLod.addEventListener("click", onSmartLodClick);
        }

        let btnCloud = document.getElementById("cloud-recovery-toggle-btn");
        if (btnCloud) {
            btnCloud.onclick = null;
            btnCloud.addEventListener("click", onCloudRecoveryClick);
        }

        let btnRec = document.getElementById("blackbox-toggle-btn");
        if (btnRec) {
            btnRec.onclick = null;
            btnRec.addEventListener("click", onBlackboxClick);
        }

        document.addEventListener("click", function (e) {
            let el = e.target;
            while (el && el !== document && el !== document.body) {
                if (el.id === "smart-lod-toggle-btn") {
                    onSmartLodClick(e);
                    return;
                }
                if (el.id === "cloud-recovery-toggle-btn") {
                    onCloudRecoveryClick(e);
                    return;
                }
                if (el.id === "blackbox-toggle-btn") {
                    onBlackboxClick(e);
                    return;
                }
                el = el.parentElement;
            }
        });

        applyPanelLanguage("en");
        initCustomTooltip();
        window.addEventListener("message", function (e) {
            if (e && e.data && e.data.type === "SCENERYX_SET_LANGUAGE" && e.data.language) {
                applyPanelLanguage(e.data.language);
                setTimeout(notifyHeight, 30);
            }
        });
        drawSparkline();

        setupAxis("tlod");
        setupAxis("olod");

        pollTelemetry();
        setInterval(pollTelemetry, POLL_INTERVAL_MS);
        setTimeout(window.sceneryxForcePanelHeight, 60);
        setTimeout(window.sceneryxForcePanelHeight, 300);
        setTimeout(window.sceneryxForcePanelHeight, 900);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
