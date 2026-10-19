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

    function setConnectedState(online) {
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
                this.floorHandle.title = "Floor LOD: " + floor;
            }
            if (this.cruiseHandle) {
                this.cruiseHandle.style.left = cruisePct + "%";
                this.cruiseHandle.title = "Cruise LOD: " + cruise;
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
                    disengageSmartLodFromManualAction();
                }
                e.preventDefault();
                e.stopPropagation();
                self.activeHandle = handleType;
                self.isDragging = true;
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
                    disengageSmartLodFromManualAction();
                }
                e.preventDefault();
                let clickedVal = self.calcValFromClientX(e.clientX);
                let current = self.getValues();
                let distFloor = Math.abs(clickedVal - current.floor);
                let distCruise = Math.abs(clickedVal - current.cruise);

                let chosenHandle = (distFloor <= distCruise) ? "floor" : "cruise";
                self.activeHandle = chosenHandle;
                self.isDragging = true;
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
                    self.isDragging = false;
                    isSliderDragging = false;
                    if (self.floorHandle) self.floorHandle.classList.remove("active");
                    if (self.cruiseHandle) self.cruiseHandle.classList.remove("active");
                    self.activeHandle = null;
                    markUserInteracting();
                }
            }

            window.addEventListener("mouseup", stopDrag);
            window.addEventListener("touchend", stopDrag);
            window.addEventListener("touchcancel", stopDrag);
        }
    }

    function disengageSmartLodFromManualAction() {
        if (!currentLodActive || currentIsExtAutoFps) return;
        currentLodActive = false;
        lastSmartLodToggleTime = Date.now();
        let btnLod = document.getElementById("smart-lod-toggle-btn");
        let lblLod = document.getElementById("smart-lod-btn-label");
        if (btnLod) {
            btnLod.className = "switch-btn switch-off";
            btnLod.setAttribute("aria-checked", "false");
        }
        if (lblLod) lblLod.textContent = "OFF";
        setAxisUiState("tlod", true, false);
        setAxisUiState("olod", true, false);
    }

    function markUserInteracting() {
        isUserInteracting = true;
        if (userInteractionTimeout) clearTimeout(userInteractionTimeout);
        userInteractionTimeout = setTimeout(function () {
            isUserInteracting = false;
        }, 2500);
    }

    function queueAxisConfigUpdate(axis, directVal) {
        markUserInteracting();
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function () {
            sendAxisConfigUpdate(axis, directVal);
        }, 120);
    }

    function sendAxisConfigUpdate(axis, directVal) {
        let mode = currentIsVr ? "VR" : "2D";
        let baseVal = (axis === "tlod") ? currentTlodFloor : currentOlodFloor;
        let targetVal = (axis === "tlod") ? currentTlodCruise : currentOlodCruise;
        let altVal = (axis === "tlod") ? currentTlodAlt : currentOlodAlt;

        if (!currentLodActive) {
            // In MAN mode: write directly to MSFS RAM and disengage auto without overwriting Smart LOD profile bounds
            let valToWrite = (directVal !== undefined) ? directVal : baseVal;
            let payload = { disengage_auto: true };
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
    const QUALITY_TITLE_MAP = { 0: "Low", 1: "Medium", 2: "High", 3: "Ultra" };

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
                return "Max FPS : " + (v > 0 ? v : 36);
            case "clouds":
                return "Clouds : " + (QUALITY_TITLE_MAP[v] || "High");
            case "precaching":
                return "Pre-Cache : " + (QUALITY_TITLE_MAP[v] || "High");
            case "terrain_shadows":
                return "Terr. Shd : " + (v <= 0 ? "Off" : v);
            case "buildings":
                return "Buildings : " + (QUALITY_TITLE_MAP[v] || "High");
            case "trees":
                return "Trees : " + (QUALITY_TITLE_MAP[v] || "High");
            case "plants":
                return "Plants : " + (QUALITY_TITLE_MAP[v] || "High");
            case "grass":
                return "Grass : " + (QUALITY_TITLE_MAP[v] || "High");
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
                let styleAttr = "";
                if (k === "clouds") {
                    if (lastInCloudRed) styleAttr = ' style="color: #fbbf24;"';
                    else if (lastInCloudBoost) styleAttr = ' style="color: #10b981;"';
                }
                html += '<span class="hl-tag" data-pin-key="' + k + '"' + styleAttr + '>' + txt + '</span>';
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
            return v <= 0 ? "Off" : String(v);
        }
        return QUALITY_TITLE_MAP[v] || "High";
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
                resetBtn.title = "Reset to Active Profile (" + formatLiveGfxDisplayVal(k, profVal) + ")";
            }
        }

        let applyBtn = document.getElementById("lgfx-apply-btn");
        if (applyBtn && applyBtn.className.indexOf("btn-applied") === -1) {
            if (hasDirty) {
                applyBtn.className = "lgfx-apply-btn btn-dirty";
                applyBtn.textContent = "APPLY *";
            } else {
                applyBtn.className = "lgfx-apply-btn";
                applyBtn.textContent = "APPLY";
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
        setTimeout(notifyHeight, 20);
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
                return; // Keep at least 1 pinned pill
            }
            pinnedGfxKeys.splice(idx, 1);
        } else {
            if (pinnedGfxKeys.length >= 5) {
                if (hintEl) {
                    hintEl.style.color = "#fbbf24";
                    hintEl.innerHTML = 'MAX 5 PINS REACHED (<span id="lgfx-pin-count">5</span>/5)';
                    setTimeout(function () {
                        if (hintEl) {
                            hintEl.style.color = "";
                            hintEl.innerHTML = 'PINNED : <span id="lgfx-pin-count">' + pinnedGfxKeys.length + '</span>/5';
                        }
                    }, 1400);
                }
                return;
            }
            // Insert in canonical LIVE_GFX_KEYS order
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
                let cMap = { 0: "LOW", 1: "MEDIUM", 2: "HIGH", 3: "ULTRA" };
                elCloudLiveVal.textContent = cMap[profVal] || "HIGH";
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

        // Check manual FPS input first
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

        // If user manually changed clouds, immediately turn Auto Cloud Recovery OFF in UI
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
                let cMap = { 0: "LOW", 1: "MEDIUM", 2: "HIGH", 3: "ULTRA" };
                elCloudLiveVal.textContent = cMap[payloadSettings.clouds] || "HIGH";
                elCloudLiveVal.style.color = "#38bdf8";
            }
        }

        renderPinnedPills();
        syncLiveGfxSelectsFromTelemetry();

        let applyBtn = document.getElementById("lgfx-apply-btn");
        if (applyBtn) {
            applyBtn.className = "lgfx-apply-btn btn-applied";
            applyBtn.textContent = "APPLIED";
            setTimeout(function () {
                let ab = document.getElementById("lgfx-apply-btn");
                if (ab && Object.keys(stagedGfxValues).length === 0) {
                    ab.className = "lgfx-apply-btn";
                    ab.textContent = "APPLY";
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
        let lodActive = !isExtAutoFps && ((lod.active !== undefined) ? !!lod.active : lodEnabled);
        if (!isSmartLodToggling) {
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
                if (lblLod) lblLod.textContent = "LOCKED";
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
                if (!isSmartLodToggling && (Date.now() - lastSmartLodToggleTime > 1200)) {
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
                // MODE AUTO: Locked inputs, dynamically moving slider handles & green values based on performance
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
                // MODE MANUEL: Nominal active profile values or direct user adjustments
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

        let cloudLbl = (lod.cloud_label || data.cloud_label || "HIGH").toUpperCase();
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
                elPacingBadge.textContent = "OPTIMAL";
            } else if (pacing === "ACCEPTABLE" || pacing === "CHARGE" || pacing === "CHARGÉ") {
                elPacingBadge.className = "badge-tag badge-acceptable";
                elPacingBadge.textContent = "ACCEPTABLE";
            } else {
                elPacingBadge.className = "badge-tag badge-heavy";
                elPacingBadge.textContent = "HEAVY";
            }
        }

        // 3. BLACKBOX RECORDER STATUS & SPARKLINE TREND GRAPH
        let isRec = (data.blackbox_recording !== undefined) ? !!data.blackbox_recording : !!data.is_tracking;
        let btnRec = document.getElementById("blackbox-toggle-btn");
        let lblRec = document.getElementById("rec-btn-label");
        if (btnRec && !isBlackboxToggling) {
            if (isRec) {
                btnRec.className = "msfs-btn btn-rec-stop";
                if (lblRec) lblRec.textContent = "STOP MONITORING";
            } else {
                btnRec.className = "msfs-btn btn-rec-start";
                if (lblRec) lblRec.textContent = "START MONITORING";
            }
        }

        // When monitoring just started, reset sparkline to fresh session
        if (isRec && !wasRecording) {
            fpsHistory = [];
        }
        wasRecording = isRec;

        // When monitoring is active, push new points and advance sparkline
        if (isRec && dispFps && dispFps > 0) {
            fpsHistory.push(Math.round(dispFps));
            if (fpsHistory.length > MAX_HISTORY_POINTS) {
                fpsHistory.shift();
            }
            drawSparkline();
        } else if (!isRec && fpsHistory.length >= 2) {
            // Keep graph frozen when recording is stopped
            drawSparkline();
        } else if (!isRec && fpsHistory.length < 2) {
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

    function notifyHeight() {
        let connView = document.getElementById("connected-view");
        let discView = document.getElementById("disconnected-view");
        let targetEl = (connView && connView.style.display !== "none" && !connView.classList.contains("hidden")) ? connView : discView;
        let h = targetEl ? targetEl.offsetHeight + 18 : document.body.scrollHeight;
        if (window.parent && window.parent !== window) {
            window.parent.postMessage({ type: "SCENERYX_PANEL_RESIZE", height: h }, "*");
        }
    }

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
            // In standalone preview mode, provide mock preview data ONLY if explicitly requested via ?preview=1
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
            // Hysteresis: Once connected, ignore transient hiccups and only switch to disconnected view after 5 consecutive failures
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
                elDelta.textContent = "STANDBY";
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

        // Gradient fill
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

        // Stroke line
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

        // Delta
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

        // Immediately cancel any lingering manual slider interaction lock or debounced manual write
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

        // Immediate optimistic visual toggle
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

        // Safety fallback: guarantee release within 1500ms
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

        // Safety fallback: guarantee release within 1500ms
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
        let currentLabel = lblRec ? lblRec.textContent : "";
        let willStart = (currentLabel.indexOf("START") !== -1);
        if (willStart) {
            if (btnRec) btnRec.className = "msfs-btn btn-rec-stop";
            if (lblRec) lblRec.textContent = "STOP MONITORING";
            fpsHistory = [];
            drawSparkline();
        } else {
            if (btnRec) btnRec.className = "msfs-btn btn-rec-start";
            if (lblRec) lblRec.textContent = "START MONITORING";
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
        let container = document.getElementById(axis + "-dual-container");
        let altInput = document.getElementById(axis + "-alt-input");
        let badge = document.getElementById(axis + "-mode-badge");
        let nameLbl = document.getElementById(axis + "-name-label");
        let card = document.getElementById(axis + "-card");

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
                    disengageSmartLodFromManualAction();
                }
                setAxisUiState(axis, true, false);
                let liveEl = document.getElementById(axis + "-live-val");
                if (liveEl) liveEl.textContent = directVal;
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

        // Global delegated click listener (immune to MSFS template element cloning)
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

        drawSparkline();

        setupAxis("tlod");
        setupAxis("olod");

        pollTelemetry();
        setInterval(pollTelemetry, POLL_INTERVAL_MS);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
