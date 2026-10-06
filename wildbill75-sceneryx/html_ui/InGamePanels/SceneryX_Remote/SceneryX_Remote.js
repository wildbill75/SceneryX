// =========================================================
// SceneryX MSFS In-Game Toolbar Panel - Resilient Controller
// =========================================================

class IngamePanelSceneryX extends TemplateElement {
    constructor() {
        super(...arguments);
        this.ingameUi = null;
    }

    connectedCallback() {
        super.connectedCallback();
        this.ingameUi = this.querySelector("ingame-ui");
    }
}
window.customElements.define("ingamepanel-sceneryx", IngamePanelSceneryX);
checkAutoload();

(function () {
    const HOSTS = ["http://127.0.0.1:8383", "http://localhost:8383"];
    let hostIndex = 0;
    const POLL_INTERVAL_MS = 1000;
    const MAX_HISTORY_POINTS = 30;

    let isConnected = false;
    let fpsHistory = [];
    let wasRecording = false;
    let isSmartLodToggling = false;
    let isBlackboxToggling = false;

    // Dual LOD State
    let currentTlodFloor = 100;
    let currentTlodCruise = 200;
    let currentTlodAlt = 5000;
    let currentTlodLive = 100;

    let currentOlodFloor = 100;
    let currentOlodCruise = 100;
    let currentOlodAlt = 3000;
    let currentOlodLive = 100;

    let tlodIsManual = false;
    let olodIsManual = false;
    let currentIsVr = false;
    let currentLodActive = false;

    let isUserInteracting = false;
    let userInteractionTimeout = null;
    let debounceTimer = null;

    function getApiBase() {
        return HOSTS[hostIndex % HOSTS.length] + "/api";
    }

    function switchHost() {
        hostIndex = (hostIndex + 1) % HOSTS.length;
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

    function updateDualSliderTrack(axis, floor, cruise) {
        let maxVal = (axis === "tlod") ? 400 : 300;
        let highlight = document.getElementById(axis + "-track-highlight");
        if (highlight) {
            let leftPct = (Math.max(0, Math.min(maxVal, floor)) / maxVal) * 100;
            let widthPct = (Math.max(0, Math.min(maxVal - floor, cruise - floor)) / maxVal) * 100;
            highlight.style.left = leftPct + "%";
            highlight.style.width = widthPct + "%";
        }
    }

    function onDualSliderMouseMove(e, axis) {
        if (e.buttons === 1) return; // Never switch z-index while dragging
        let container = document.getElementById(axis + "-dual-container");
        if (!container) return;
        let rect = container.getBoundingClientRect();
        if (!rect.width) return;
        let x = e.clientX - rect.left;
        let pct = Math.max(0, Math.min(1, x / rect.width));
        let maxVal = (axis === "tlod") ? 400 : 300;
        let mouseVal = pct * maxVal;

        let floorInput = document.getElementById(axis + "-floor-range");
        let cruiseInput = document.getElementById(axis + "-cruise-range");
        if (!floorInput || !cruiseInput) return;

        let floorVal = parseInt(floorInput.value, 10);
        let cruiseVal = parseInt(cruiseInput.value, 10);

        let distFloor = Math.abs(mouseVal - floorVal);
        let distCruise = Math.abs(mouseVal - cruiseVal);

        if (distFloor < distCruise || (distFloor === distCruise && mouseVal <= floorVal)) {
            floorInput.style.zIndex = "25";
            cruiseInput.style.zIndex = "10";
        } else {
            floorInput.style.zIndex = "10";
            cruiseInput.style.zIndex = "25";
        }
    }

    function setAxisUiState(axis, isManual, isOff) {
        let badge = document.getElementById(axis + "-mode-badge");
        let txt = document.getElementById(axis + "-badge-text");
        if (axis === "tlod") tlodIsManual = isManual;
        else olodIsManual = isManual;

        if (txt && badge) {
            if (isOff) {
                badge.className = "badge-tag tag-neutral";
                txt.textContent = "OFF";
            } else if (isManual) {
                badge.className = "badge-tag tag-amber";
                txt.textContent = "MAN";
            } else {
                badge.className = "badge-tag tag-green";
                txt.textContent = "AUTO";
            }
        }
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
            // Smart LOD is disengaged: write live to MSFS memory directly without changing profile files
            let valToWrite = (directVal !== undefined) ? directVal : baseVal;
            let payload = {};
            payload[axis] = valToWrite;
            let url = getApiBase() + "/smart_lod/set_lod";
            let xhr = new XMLHttpRequest();
            xhr.open("POST", url, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.timeout = 2500;
            xhr.send(JSON.stringify(payload));
            return;
        }

        let url = getApiBase() + "/smart_lod/axis_config";
        let xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.timeout = 2500;
        xhr.send(JSON.stringify({
            mode: mode,
            axis: axis,
            base: baseVal,
            target: targetVal,
            altitude: altVal
        }));
    }

    function resetToProfile(axis) {
        if (!axis) axis = "all";
        if (axis === "all") {
            setAxisUiState("tlod", false);
            setAxisUiState("olod", false);
        } else {
            setAxisUiState(axis, false);
        }
        isUserInteracting = false;

        let url = getApiBase() + "/smart_lod/reset_to_profile?axis=" + axis + "&_=" + Date.now();
        let xhr = new XMLHttpRequest();
        xhr.open("GET", url, true);
        xhr.timeout = 2000;
        xhr.onload = function () {
            pollTelemetry();
        };
        xhr.onerror = function () {
            pollTelemetry();
        };
        xhr.send();
    }

    function drawSparkline() {
        let canvas = document.getElementById("fps-sparkline-canvas");
        if (!canvas || !canvas.getContext || fpsHistory.length < 2) return;

        let ctx = canvas.getContext("2d");
        let w = canvas.width;
        let h = canvas.height;

        ctx.clearRect(0, 0, w, h);

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

    function updateTelemetryUI(data) {
        if (!data) return;

        currentIsVr = !!data.is_vr;

        // 1. SMART LOD REGULATION
        let lod = data.smart_lod || {};
        let lodActive = (lod.active !== undefined) ? !!lod.active : (!!data.smart_lod_running && !!data.smart_lod_enabled);
        currentLodActive = lodActive;

        let sTlod = (lod.current_tlod !== undefined && lod.current_tlod !== null) ? lod.current_tlod : (data.smart_lod_tlod !== undefined ? data.smart_lod_tlod : 100);
        let sOlod = (lod.current_olod !== undefined && lod.current_olod !== null) ? lod.current_olod : (data.smart_lod_olod !== undefined ? data.smart_lod_olod : 100);

        currentTlodLive = Math.round(Number(sTlod) || 100);
        currentOlodLive = Math.round(Number(sOlod) || 100);

        let liveTlodEl = document.getElementById("tlod-live-val");
        if (liveTlodEl) liveTlodEl.textContent = currentTlodLive;
        let liveOlodEl = document.getElementById("olod-live-val");
        if (liveOlodEl) liveOlodEl.textContent = currentOlodLive;

        if (!isUserInteracting) {
            let tlodFloorVal = lod.tlod_base !== undefined ? lod.tlod_base : 100;
            let tlodCruiseVal = lod.tlod_target !== undefined ? lod.tlod_target : 200;
            let tlodAltVal = lod.tlod_altitude !== undefined ? lod.tlod_altitude : 5000;

            let olodFloorVal = lod.olod_base !== undefined ? lod.olod_base : 100;
            let olodCruiseVal = lod.olod_target !== undefined ? lod.olod_target : 100;
            let olodAltVal = lod.olod_altitude !== undefined ? lod.olod_altitude : 3000;

            currentTlodFloor = tlodFloorVal;
            currentTlodCruise = tlodCruiseVal;
            currentTlodAlt = tlodAltVal;

            currentOlodFloor = olodFloorVal;
            currentOlodCruise = olodCruiseVal;
            currentOlodAlt = olodAltVal;

            // Update DOM inputs and readouts
            let tFloorRange = document.getElementById("tlod-floor-range");
            let tCruiseRange = document.getElementById("tlod-cruise-range");
            let tAltInput = document.getElementById("tlod-alt-input");
            let tFloorVal = document.getElementById("tlod-floor-val");
            let tCruiseVal = document.getElementById("tlod-cruise-val");

            if (tFloorRange) tFloorRange.value = currentTlodFloor;
            if (tCruiseRange) tCruiseRange.value = currentTlodCruise;
            if (tAltInput && document.activeElement !== tAltInput) tAltInput.value = currentTlodAlt;
            if (tFloorVal) tFloorVal.textContent = currentTlodFloor;
            if (tCruiseVal) tCruiseVal.textContent = currentTlodCruise;
            updateDualSliderTrack("tlod", currentTlodFloor, currentTlodCruise);

            let oFloorRange = document.getElementById("olod-floor-range");
            let oCruiseRange = document.getElementById("olod-cruise-range");
            let oAltInput = document.getElementById("olod-alt-input");
            let oFloorVal = document.getElementById("olod-floor-val");
            let oCruiseVal = document.getElementById("olod-cruise-val");

            if (oFloorRange) oFloorRange.value = currentOlodFloor;
            if (oCruiseRange) oCruiseRange.value = currentOlodCruise;
            if (oAltInput && document.activeElement !== oAltInput) oAltInput.value = currentOlodAlt;
            if (oFloorVal) oFloorVal.textContent = currentOlodFloor;
            if (oCruiseVal) oCruiseVal.textContent = currentOlodCruise;
            updateDualSliderTrack("olod", currentOlodFloor, currentOlodCruise);

            let tlodManualRemote = !!(lod.tlod_manual !== undefined ? lod.tlod_manual : data.smart_lod_tlod_manual);
            let olodManualRemote = !!(lod.olod_manual !== undefined ? lod.olod_manual : data.smart_lod_olod_manual);
            setAxisUiState("tlod", tlodManualRemote, !lodActive);
            setAxisUiState("olod", olodManualRemote, !lodActive);
        }

        let btnLod = document.getElementById("smart-lod-toggle-btn");
        let lblLod = document.getElementById("smart-lod-btn-label");
        if (btnLod && !isSmartLodToggling) {
            if (lodActive) {
                btnLod.className = "msfs-btn-inline btn-active-green";
                if (lblLod) lblLod.textContent = "ACTIVE";
            } else {
                btnLod.className = "msfs-btn-inline btn-primary";
                if (lblLod) lblLod.textContent = "ENGAGE";
            }
        }

        // 2. LIVE PERFORMANCE (Enlarged typography with spaced units)
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

        let elPacingTxt = document.getElementById("pacing-badge-text");
        let elPacingBadge = document.getElementById("live-pacing-status");
        if (elPacingTxt && elPacingBadge) {
            if (pacing === "OPTIMAL" || pacing === "FLUIDE") {
                elPacingTxt.textContent = "OPTIMAL";
                elPacingBadge.className = "badge-tag tag-green";
            } else if (pacing === "ACCEPTABLE" || pacing === "CHARGE" || pacing === "CHARGÉ") {
                elPacingTxt.textContent = "ACCEPTABLE";
                elPacingBadge.className = "badge-tag tag-amber";
            } else {
                elPacingTxt.textContent = "HEAVY";
                elPacingBadge.className = "badge-tag tag-red";
            }
        }

        // 3. BLACKBOX RECORDER STATUS
        let isRec = !!data.blackbox_recording;
        let btnRec = document.getElementById("blackbox-toggle-btn");
        let lblRec = document.getElementById("rec-btn-label");
        if (btnRec && !isBlackboxToggling) {
            if (isRec) {
                btnRec.className = "msfs-btn btn-active-red";
                if (lblRec) lblRec.textContent = "STOP RECORDING";
            } else {
                btnRec.className = "msfs-btn btn-primary";
                if (lblRec) lblRec.textContent = "START RECORDING";
            }
        }

        // 4. SPARKLINE TREND GRAPH (MONITORS DURING RECORDING)
        if (isRec && !wasRecording) {
            fpsHistory = [];
        }
        wasRecording = isRec;

        if (isRec && dispFps && dispFps > 0) {
            fpsHistory.push(dispFps);
            if (fpsHistory.length > MAX_HISTORY_POINTS) {
                fpsHistory.shift();
            }
            drawSparkline();
        }

        // 5. SYSTEM METRICS (GPU, CPU, VRAM, CACHE with spaced units)
        let elGpu = document.getElementById("live-gpu-val");
        if (elGpu) {
            let gpuPct = (data.gpu_util_pct !== undefined && data.gpu_util_pct !== null) ? data.gpu_util_pct : 0;
            elGpu.textContent = Math.round(Number(gpuPct) || 0);
        }

        let elCpu = document.getElementById("live-cpu-val");
        if (elCpu) {
            let cpuPct = (data.cpu_pct !== undefined && data.cpu_pct !== null) ? data.cpu_pct : 0;
            elCpu.textContent = Math.round(Number(cpuPct) || 0);
        }

        let elVram = document.getElementById("live-vram-val");
        if (elVram) {
            let vramUsed = data.vram_used_gb !== undefined ? data.vram_used_gb : "--";
            let vramTot = data.vram_total_gb !== undefined ? data.vram_total_gb : "--";
            if (vramUsed !== "--" && vramTot !== "--") {
                elVram.textContent = vramUsed + " / " + vramTot;
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

    function pollTelemetry() {
        let url = getApiBase() + "/telemetry?_=" + Date.now();

        function handleSuccess(data) {
            setConnectedState(true);
            try {
                updateTelemetryUI(data);
            } catch (e) {
                console.error("[SceneryX] UI update error:", e);
            }
        }

        function handleFailure() {
            switchHost();
            setConnectedState(false);
        }

        if (typeof fetch === "function") {
            fetch(url, { cache: "no-store" })
                .then(function (res) {
                    if (!res.ok) throw new Error("HTTP " + res.status);
                    return res.json();
                })
                .then(handleSuccess)
                .catch(function () {
                    tryXhr(url, handleSuccess, handleFailure);
                });
        } else {
            tryXhr(url, handleSuccess, handleFailure);
        }
    }

    function tryXhr(url, onSuccess, onError) {
        try {
            let xhr = new XMLHttpRequest();
            xhr.open("GET", url, true);
            xhr.timeout = 1500;
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

    function onSmartLodClick() {
        isSmartLodToggling = true;
        let url = getApiBase() + "/smart_lod/toggle";
        let xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.timeout = 2500;
        xhr.onload = function () {
            isSmartLodToggling = false;
            pollTelemetry();
        };
        xhr.onerror = function () { isSmartLodToggling = false; };
        xhr.ontimeout = function () { isSmartLodToggling = false; };
        xhr.send();
    }

    function onBlackboxClick() {
        isBlackboxToggling = true;
        let btnRec = document.getElementById("blackbox-toggle-btn");
        let lblRec = document.getElementById("rec-btn-label");
        let currentLabel = lblRec ? lblRec.textContent : "";
        if (currentLabel.indexOf("START") !== -1) {
            if (btnRec) btnRec.className = "msfs-btn btn-active-red";
            if (lblRec) lblRec.textContent = "STOP RECORDING";
        } else {
            if (btnRec) btnRec.className = "msfs-btn btn-primary";
            if (lblRec) lblRec.textContent = "START RECORDING";
        }

        let url = getApiBase() + "/blackbox/toggle";
        let xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.timeout = 3000;
        xhr.onload = function () {
            isBlackboxToggling = false;
            pollTelemetry();
        };
        xhr.onerror = function () { isBlackboxToggling = false; };
        xhr.ontimeout = function () { isBlackboxToggling = false; };
        xhr.send();
    }

    function setupDualSliderAxis(axis) {
        let maxVal = (axis === "tlod") ? 400 : 300;
        let container = document.getElementById(axis + "-dual-container");
        let floorRange = document.getElementById(axis + "-floor-range");
        let cruiseRange = document.getElementById(axis + "-cruise-range");
        let altInput = document.getElementById(axis + "-alt-input");
        let floorValLbl = document.getElementById(axis + "-floor-val");
        let cruiseValLbl = document.getElementById(axis + "-cruise-val");
        let badge = document.getElementById(axis + "-mode-badge");
        let nameLbl = document.getElementById(axis + "-name-label");
        let card = document.getElementById(axis + "-card");

        if (container) {
            container.addEventListener("mousemove", function (e) {
                onDualSliderMouseMove(e, axis);
            });
            container.addEventListener("dblclick", function (e) {
                e.preventDefault();
                e.stopPropagation();
                resetToProfile(axis);
            });
        }

        if (floorRange) {
            floorRange.addEventListener("mousedown", function () {
                floorRange.style.zIndex = "30";
                if (cruiseRange) cruiseRange.style.zIndex = "10";
            });
            floorRange.addEventListener("input", function () {
                let fVal = parseInt(floorRange.value, 10);
                let cVal = parseInt(cruiseRange.value, 10);
                if (fVal > cVal) {
                    fVal = cVal;
                    floorRange.value = fVal;
                }
                if (axis === "tlod") currentTlodFloor = fVal;
                else currentOlodFloor = fVal;

                if (floorValLbl) floorValLbl.textContent = fVal;
                updateDualSliderTrack(axis, fVal, cVal);
                setAxisUiState(axis, true, !currentLodActive);
                if (!currentLodActive) {
                    let liveEl = document.getElementById(axis + "-live-val");
                    if (liveEl) liveEl.textContent = fVal;
                }
                queueAxisConfigUpdate(axis, fVal);
            });
            floorRange.addEventListener("dblclick", function (e) {
                e.preventDefault();
                e.stopPropagation();
                resetToProfile(axis);
            });
        }

        if (cruiseRange) {
            cruiseRange.addEventListener("mousedown", function () {
                cruiseRange.style.zIndex = "30";
                if (floorRange) floorRange.style.zIndex = "10";
            });
            cruiseRange.addEventListener("input", function () {
                let fVal = parseInt(floorRange.value, 10);
                let cVal = parseInt(cruiseRange.value, 10);
                if (cVal < fVal) {
                    cVal = fVal;
                    cruiseRange.value = cVal;
                }
                if (axis === "tlod") currentTlodCruise = cVal;
                else currentOlodCruise = cVal;

                if (cruiseValLbl) cruiseValLbl.textContent = cVal;
                updateDualSliderTrack(axis, fVal, cVal);
                setAxisUiState(axis, true, !currentLodActive);
                if (!currentLodActive) {
                    let liveEl = document.getElementById(axis + "-live-val");
                    if (liveEl) liveEl.textContent = cVal;
                }
                queueAxisConfigUpdate(axis, cVal);
            });
            cruiseRange.addEventListener("dblclick", function (e) {
                e.preventDefault();
                e.stopPropagation();
                resetToProfile(axis);
            });
        }

        if (altInput) {
            altInput.addEventListener("change", function () {
                let num = Math.max(500, Math.min(45000, parseInt(altInput.value, 10) || 5000));
                altInput.value = num;
                if (axis === "tlod") currentTlodAlt = num;
                else currentOlodAlt = num;
                queueAxisConfigUpdate(axis);
            });
        }

        if (badge) {
            badge.addEventListener("click", function () {
                resetToProfile(axis);
            });
        }

        if (nameLbl) {
            nameLbl.addEventListener("dblclick", function (e) {
                e.preventDefault();
                e.stopPropagation();
                resetToProfile(axis);
            });
        }

        if (card) {
            card.addEventListener("dblclick", function (e) {
                if (e.target.tagName !== 'INPUT') {
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

        connView.addEventListener("dblclick", function (e) {
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON') {
                resetToProfile("all");
            }
        });
        document.body.addEventListener("dblclick", function (e) {
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON') {
                resetToProfile("all");
            }
        });

        let btnLod = document.getElementById("smart-lod-toggle-btn");
        if (btnLod) {
            btnLod.addEventListener("click", onSmartLodClick);
        }

        let btnRec = document.getElementById("blackbox-toggle-btn");
        if (btnRec) {
            btnRec.addEventListener("click", onBlackboxClick);
        }

        setupDualSliderAxis("tlod");
        setupDualSliderAxis("olod");

        pollTelemetry();
        setInterval(pollTelemetry, POLL_INTERVAL_MS);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
