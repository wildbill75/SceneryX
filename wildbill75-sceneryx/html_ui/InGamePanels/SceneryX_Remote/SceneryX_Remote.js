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

    // Independent LOD tracking & Débrayage (Selected vs Managed Mode)
    let currentTlod = 100;
    let currentOlod = 100;
    let tlodIsManual = false;
    let olodIsManual = false;

    let isUserDraggingLod = false;
    let lodGraceUntil = 0;
    let lodDebounceTimer = null;
    let pendingLodUpdates = { tlod: false, olod: false };

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

    function setAxisUiState(axis, isManual) {
        if (axis === "tlod") {
            tlodIsManual = isManual;
            let sl = document.getElementById("tlod-slider");
            let valLbl = document.getElementById("tlod-val-label");
            let badge = document.getElementById("tlod-mode-badge");
            if (sl) {
                if (isManual) sl.classList.add("is-manual");
                else sl.classList.remove("is-manual");
            }
            if (valLbl) {
                if (isManual) valLbl.classList.add("is-manual");
                else valLbl.classList.remove("is-manual");
            }
            if (badge) {
                if (isManual) {
                    badge.textContent = "MAN";
                    badge.className = "lod-mode-badge badge-mode-manual";
                    badge.title = "Manual override active. Click badge or double-click slider to reset to Auto";
                } else {
                    badge.textContent = "AUTO";
                    badge.className = "lod-mode-badge badge-mode-auto";
                    badge.title = "Automatic altitude profile active";
                }
            }
        } else if (axis === "olod") {
            olodIsManual = isManual;
            let sl = document.getElementById("olod-slider");
            let valLbl = document.getElementById("olod-val-label");
            let badge = document.getElementById("olod-mode-badge");
            if (sl) {
                if (isManual) sl.classList.add("is-manual");
                else sl.classList.remove("is-manual");
            }
            if (valLbl) {
                if (isManual) valLbl.classList.add("is-manual");
                else valLbl.classList.remove("is-manual");
            }
            if (badge) {
                if (isManual) {
                    badge.textContent = "MAN";
                    badge.className = "lod-mode-badge badge-mode-manual";
                    badge.title = "Manual override active. Click badge or double-click slider to reset to Auto";
                } else {
                    badge.textContent = "AUTO";
                    badge.className = "lod-mode-badge badge-mode-auto";
                    badge.title = "Automatic altitude profile active";
                }
            }
        }
    }

    function resetAxisToAuto(axis) {
        // Optimistic UI state reset
        setAxisUiState(axis, false);
        isUserDraggingLod = false;
        lodGraceUntil = 0;

        let url = getApiBase() + "/smart_lod/reset_override?axis=" + axis + "&_=" + Date.now();
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

        // 1. SMART LOD
        let lod = data.smart_lod || {};
        let lodActive = (lod.active !== undefined) ? !!lod.active : (!!data.smart_lod_running && !!data.smart_lod_enabled);
        let sTlod = (lod.current_tlod !== undefined && lod.current_tlod !== null) ? lod.current_tlod : (data.smart_lod_tlod !== undefined ? data.smart_lod_tlod : 100);
        let sOlod = (lod.current_olod !== undefined && lod.current_olod !== null) ? lod.current_olod : (data.smart_lod_olod !== undefined ? data.smart_lod_olod : 100);

        let now = Date.now();
        if (!isUserDraggingLod && now > lodGraceUntil) {
            currentTlod = Math.round(Number(sTlod) || 100);
            currentOlod = Math.round(Number(sOlod) || 100);

            let slTlod = document.getElementById("tlod-slider");
            if (slTlod) slTlod.value = currentTlod;
            let lblTlod = document.getElementById("tlod-val-label");
            if (lblTlod) lblTlod.textContent = currentTlod;

            let slOlod = document.getElementById("olod-slider");
            if (slOlod) slOlod.value = currentOlod;
            let lblOlod = document.getElementById("olod-val-label");
            if (lblOlod) lblOlod.textContent = currentOlod;

            let tlodManualRemote = !!(lod.tlod_manual !== undefined ? lod.tlod_manual : data.smart_lod_tlod_manual);
            let olodManualRemote = !!(lod.olod_manual !== undefined ? lod.olod_manual : data.smart_lod_olod_manual);
            setAxisUiState("tlod", tlodManualRemote);
            setAxisUiState("olod", olodManualRemote);
        }

        let btnLod = document.getElementById("smart-lod-toggle-btn");
        let lblLod = document.getElementById("smart-lod-btn-label");
        if (btnLod && !isSmartLodToggling) {
            if (lodActive) {
                btnLod.className = "msfs-btn btn-active-green";
                if (lblLod) lblLod.textContent = "ACTIVE";
            } else {
                btnLod.className = "msfs-btn btn-primary";
                if (lblLod) lblLod.textContent = "ENGAGE";
            }
        }

        // 2. LIVE PERFORMANCE (ALWAYS LIVE MONITORED)
        let perf = data.perf || {};
        let dispFps = (perf.displayed_fps !== undefined && perf.displayed_fps !== null) ? perf.displayed_fps : (data.displayed_fps || 0);
        let baseFps = (perf.fps !== undefined && perf.fps !== null) ? perf.fps : (data.base_fps || 0);
        let mtMs = (perf.main_thread_ms !== undefined && perf.main_thread_ms !== null) ? perf.main_thread_ms : (data.main_thread_ms || 0);
        let pacing = (perf.frame_pacing || "OPTIMAL").toUpperCase();

        let elFps = document.getElementById("live-fps-val");
        if (elFps) elFps.textContent = (dispFps && dispFps > 0) ? Math.round(dispFps) : "--";

        let elBase = document.getElementById("live-fps-base");
        if (elBase) elBase.textContent = (baseFps && baseFps > 0) ? "(" + Math.round(baseFps) + " base)" : "";

        let elMt = document.getElementById("live-mt-val");
        if (elMt) elMt.textContent = (mtMs && mtMs > 0) ? Number(mtMs).toFixed(1) : "--";

        let elPacing = document.getElementById("live-pacing-status");
        if (elPacing) {
            if (pacing === "OPTIMAL" || pacing === "FLUIDE") {
                elPacing.textContent = "OPTIMAL";
                elPacing.className = "badge-tag tag-green";
            } else if (pacing === "ACCEPTABLE" || pacing === "CHARGE" || pacing === "CHARGÉ") {
                elPacing.textContent = "ACCEPTABLE";
                elPacing.className = "badge-tag tag-amber";
            } else {
                elPacing.textContent = "HEAVY";
                elPacing.className = "badge-tag tag-red";
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

        // 4. SPARKLINE TREND GRAPH (MONITORS ONLY WHILE RECORDING!)
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

        // 5. SYSTEM METRICS
        let elVram = document.getElementById("live-vram-val");
        if (elVram) {
            let vramUsed = data.vram_used_gb !== undefined ? data.vram_used_gb : "--";
            let vramTot = data.vram_total_gb !== undefined ? data.vram_total_gb : "--";
            if (vramUsed !== "--" && vramTot !== "--") {
                elVram.textContent = vramUsed + " / " + vramTot + " GB";
            } else {
                elVram.textContent = "-- GB";
            }
        }

        let elCache = document.getElementById("live-cache-val");
        if (elCache) {
            let cacheVal = data.rolling_cache_gb !== undefined ? data.rolling_cache_gb : 0.0;
            elCache.textContent = cacheVal + " MB/s";
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

    function queueLodAxisUpdate(axis) {
        pendingLodUpdates[axis] = true;
        isUserDraggingLod = true;
        lodGraceUntil = Date.now() + 2500;
        if (lodDebounceTimer) clearTimeout(lodDebounceTimer);
        lodDebounceTimer = setTimeout(sendPendingLodUpdates, 150);
    }

    function sendPendingLodUpdates() {
        let params = [];
        if (pendingLodUpdates.tlod) {
            params.push("tlod=" + currentTlod);
        }
        if (pendingLodUpdates.olod) {
            params.push("olod=" + currentOlod);
        }
        pendingLodUpdates = { tlod: false, olod: false };
        if (params.length === 0) return;

        let url = getApiBase() + "/smart_lod/set_lod?" + params.join("&") + "&_=" + Date.now();
        let xhr = new XMLHttpRequest();
        xhr.open("GET", url, true);
        xhr.timeout = 2000;
        xhr.onload = function () {
            lodGraceUntil = Date.now() + 1500;
            setTimeout(function () {
                isUserDraggingLod = false;
            }, 1500);
        };
        xhr.onerror = function () {
            setTimeout(function () {
                isUserDraggingLod = false;
            }, 1500);
        };
        xhr.send();
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

    function init() {
        let discView = document.getElementById("disconnected-view");
        let connView = document.getElementById("connected-view");
        if (!discView || !connView) {
            setTimeout(init, 100);
            return;
        }

        let btnLod = document.getElementById("smart-lod-toggle-btn");
        if (btnLod) {
            btnLod.addEventListener("click", onSmartLodClick);
        }

        let btnRec = document.getElementById("blackbox-toggle-btn");
        if (btnRec) {
            btnRec.addEventListener("click", onBlackboxClick);
        }

        // Wire TLOD Controls
        let slTlod = document.getElementById("tlod-slider");
        let lblTlod = document.getElementById("tlod-val-label");
        let nameTlod = document.getElementById("tlod-name-label");
        let badgeTlod = document.getElementById("tlod-mode-badge");

        if (slTlod) {
            slTlod.addEventListener("input", function () {
                currentTlod = parseInt(slTlod.value, 10) || 100;
                if (lblTlod) lblTlod.textContent = currentTlod;
                setAxisUiState("tlod", true);
                queueLodAxisUpdate("tlod");
            });
            slTlod.addEventListener("dblclick", function (e) {
                e.preventDefault();
                e.stopPropagation();
                resetAxisToAuto("tlod");
            });
        }
        if (lblTlod) {
            lblTlod.addEventListener("dblclick", function (e) {
                e.preventDefault();
                e.stopPropagation();
                resetAxisToAuto("tlod");
            });
        }
        if (nameTlod) {
            nameTlod.addEventListener("dblclick", function (e) {
                e.preventDefault();
                e.stopPropagation();
                resetAxisToAuto("tlod");
            });
        }
        if (badgeTlod) {
            badgeTlod.addEventListener("click", function () {
                if (tlodIsManual) resetAxisToAuto("tlod");
            });
        }

        let btnTlodMinus = document.getElementById("tlod-minus-btn");
        if (btnTlodMinus) {
            btnTlodMinus.addEventListener("click", function () {
                currentTlod = Math.max(10, currentTlod - 10);
                if (slTlod) slTlod.value = currentTlod;
                if (lblTlod) lblTlod.textContent = currentTlod;
                setAxisUiState("tlod", true);
                queueLodAxisUpdate("tlod");
            });
        }
        let btnTlodPlus = document.getElementById("tlod-plus-btn");
        if (btnTlodPlus) {
            btnTlodPlus.addEventListener("click", function () {
                currentTlod = Math.min(400, currentTlod + 10);
                if (slTlod) slTlod.value = currentTlod;
                if (lblTlod) lblTlod.textContent = currentTlod;
                setAxisUiState("tlod", true);
                queueLodAxisUpdate("tlod");
            });
        }

        // Wire OLOD Controls
        let slOlod = document.getElementById("olod-slider");
        let lblOlod = document.getElementById("olod-val-label");
        let nameOlod = document.getElementById("olod-name-label");
        let badgeOlod = document.getElementById("olod-mode-badge");

        if (slOlod) {
            slOlod.addEventListener("input", function () {
                currentOlod = parseInt(slOlod.value, 10) || 100;
                if (lblOlod) lblOlod.textContent = currentOlod;
                setAxisUiState("olod", true);
                queueLodAxisUpdate("olod");
            });
            slOlod.addEventListener("dblclick", function (e) {
                e.preventDefault();
                e.stopPropagation();
                resetAxisToAuto("olod");
            });
        }
        if (lblOlod) {
            lblOlod.addEventListener("dblclick", function (e) {
                e.preventDefault();
                e.stopPropagation();
                resetAxisToAuto("olod");
            });
        }
        if (nameOlod) {
            nameOlod.addEventListener("dblclick", function (e) {
                e.preventDefault();
                e.stopPropagation();
                resetAxisToAuto("olod");
            });
        }
        if (badgeOlod) {
            badgeOlod.addEventListener("click", function () {
                if (olodIsManual) resetAxisToAuto("olod");
            });
        }

        let btnOlodMinus = document.getElementById("olod-minus-btn");
        if (btnOlodMinus) {
            btnOlodMinus.addEventListener("click", function () {
                currentOlod = Math.max(10, currentOlod - 10);
                if (slOlod) slOlod.value = currentOlod;
                if (lblOlod) lblOlod.textContent = currentOlod;
                setAxisUiState("olod", true);
                queueLodAxisUpdate("olod");
            });
        }
        let btnOlodPlus = document.getElementById("olod-plus-btn");
        if (btnOlodPlus) {
            btnOlodPlus.addEventListener("click", function () {
                currentOlod = Math.min(300, currentOlod + 10);
                if (slOlod) slOlod.value = currentOlod;
                if (lblOlod) lblOlod.textContent = currentOlod;
                setAxisUiState("olod", true);
                queueLodAxisUpdate("olod");
            });
        }

        pollTelemetry();
        setInterval(pollTelemetry, POLL_INTERVAL_MS);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
