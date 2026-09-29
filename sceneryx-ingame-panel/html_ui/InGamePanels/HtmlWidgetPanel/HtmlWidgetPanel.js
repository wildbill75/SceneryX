// =========================================================
// SceneryX MSFS In-Game Toolbar Panel - Remote Controller
// =========================================================

(function () {
    const API_BASE = "http://127.0.0.1:8383/api";
    const POLL_INTERVAL_MS = 1000;
    const MAX_HISTORY_POINTS = 30;

    let isConnected = false;
    let fpsHistory = [];
    let isSmartLodToggling = false;
    let isBlackboxToggling = false;

    // DOM Elements
    let elConnBadge = null;
    let elDisconnectedView = null;
    let elConnectedView = null;
    let elPanelCloseBtn = null;

    let elSmartLodBtn = null;
    let elSmartLodLabel = null;
    let elSmartLodDot = null;
    let elSmartLodTlodBadge = null;
    let elSmartLodDesc = null;

    let elFpsVal = null;
    let elFpsBase = null;
    let elMtVal = null;
    let elPacingStatus = null;
    let elDeltaLabel = null;
    let canvasSparkline = null;
    let ctxSparkline = null;

    let elVramVal = null;
    let elCacheVal = null;
    let elBlackboxBtn = null;
    let elRecDot = null;
    let elRecBtnLabel = null;

    function init() {
        // Cache DOM elements
        elConnBadge = document.getElementById("conn-badge");
        elDisconnectedView = document.getElementById("disconnected-view");
        elConnectedView = document.getElementById("connected-view");
        elPanelCloseBtn = document.getElementById("panel-close-btn");

        elSmartLodBtn = document.getElementById("smart-lod-toggle-btn");
        elSmartLodLabel = document.getElementById("smart-lod-btn-label");
        elSmartLodDot = document.getElementById("smart-lod-dot");
        elSmartLodTlodBadge = document.getElementById("smart-lod-tlod-badge");
        elSmartLodDesc = document.getElementById("smart-lod-status-desc");

        elFpsVal = document.getElementById("live-fps-val");
        elFpsBase = document.getElementById("live-fps-base");
        elMtVal = document.getElementById("live-mt-val");
        elPacingStatus = document.getElementById("live-pacing-status");
        elDeltaLabel = document.getElementById("fps-delta-label");

        canvasSparkline = document.getElementById("fps-sparkline-canvas");
        if (canvasSparkline && canvasSparkline.getContext) {
            ctxSparkline = canvasSparkline.getContext("2d");
        }

        elVramVal = document.getElementById("live-vram-val");
        elCacheVal = document.getElementById("live-cache-val");
        elBlackboxBtn = document.getElementById("blackbox-toggle-btn");
        elRecDot = document.getElementById("rec-dot");
        elRecBtnLabel = document.getElementById("rec-btn-label");

        // Event Listeners
        if (elSmartLodBtn) {
            elSmartLodBtn.addEventListener("click", onSmartLodClick);
        }

        if (elBlackboxBtn) {
            elBlackboxBtn.addEventListener("click", onBlackboxClick);
        }

        if (elPanelCloseBtn) {
            elPanelCloseBtn.addEventListener("click", function () {
                // MSFS Toolbar panel close
                const panel = document.getElementById("HtmlWidgetPanel");
                if (panel && typeof panel.close === "function") {
                    panel.close();
                } else if (window.parent && typeof window.parent.closePanel === "function") {
                    window.parent.closePanel();
                }
            });
        }

        // Start Telemetry Poll
        pollTelemetry();
        setInterval(pollTelemetry, POLL_INTERVAL_MS);
    }

    function setConnectedState(connected) {
        isConnected = connected;
        if (connected) {
            if (elConnBadge) {
                elConnBadge.className = "badge-online";
                elConnBadge.textContent = "ONLINE";
            }
            if (elDisconnectedView) elDisconnectedView.classList.add("hidden");
            if (elConnectedView) elConnectedView.classList.remove("hidden");
        } else {
            if (elConnBadge) {
                elConnBadge.className = "badge-offline";
                elConnBadge.textContent = "OFFLINE";
            }
            if (elDisconnectedView) elDisconnectedView.classList.remove("hidden");
            if (elConnectedView) elConnectedView.classList.add("hidden");
        }
    }

    function pollTelemetry() {
        fetch(API_BASE + "/telemetry", { cache: "no-store" })
            .then(function (res) {
                if (!res.ok) throw new Error("HTTP " + res.status);
                return res.json();
            })
            .then(function (data) {
                setConnectedState(true);
                updateUI(data);
            })
            .catch(function () {
                setConnectedState(false);
            });
    }

    function updateUI(data) {
        if (!data) return;

        // 1. SMART LOD STATE
        const isSmartLodOn = !!(data.smart_lod_enabled && data.smart_lod_running);
        if (elSmartLodBtn) {
            if (isSmartLodOn) {
                elSmartLodBtn.className = "btn-smart-lod btn-active";
                if (elSmartLodLabel) elSmartLodLabel.textContent = "SMART LOD : ACTIF";
            } else {
                elSmartLodBtn.className = "btn-smart-lod btn-inactive";
                if (elSmartLodLabel) elSmartLodLabel.textContent = "SMART LOD : INACTIF";
            }
        }

        if (elSmartLodTlodBadge) {
            if (isSmartLodOn && data.smart_lod_tlod) {
                elSmartLodTlodBadge.textContent = "TLOD: " + Math.round(data.smart_lod_tlod);
                elSmartLodTlodBadge.style.color = "#38bdf8";
            } else {
                elSmartLodTlodBadge.textContent = "TLOD: --";
                elSmartLodTlodBadge.style.color = "#64748b";
            }
        }

        if (elSmartLodDesc) {
            elSmartLodDesc.textContent = data.smart_lod_status || "Régulation en mémoire";
        }

        // 2. DISPLAYED FPS & BASE FPS
        const curFps = data.displayed_fps !== null && data.displayed_fps !== undefined ? Number(data.displayed_fps) : null;
        if (elFpsVal) {
            elFpsVal.textContent = curFps !== null ? curFps.toFixed(1) : "--";
        }

        if (elFpsBase) {
            if (data.base_fps !== null && data.base_fps !== undefined) {
                const isFg = curFps !== null && data.base_fps > 0 && Math.abs(curFps - data.base_fps) > 5;
                elFpsBase.textContent = "(" + Math.round(data.base_fps) + " base" + (isFg ? " • FG ON" : "") + ")";
            } else {
                elFpsBase.textContent = "(-- base)";
            }
        }

        // Push to history for sparkline
        if (curFps !== null && curFps > 0) {
            fpsHistory.push(curFps);
            if (fpsHistory.length > MAX_HISTORY_POINTS) {
                fpsHistory.shift();
            }
            renderSparkline();
        }

        // 3. CPU MAIN THREAD (PACING)
        const curMt = data.main_thread_ms !== null && data.main_thread_ms !== undefined ? Number(data.main_thread_ms) : null;
        if (elMtVal) {
            elMtVal.textContent = curMt !== null ? curMt.toFixed(1) : "--";
        }

        if (elPacingStatus) {
            if (curMt !== null) {
                if (curMt <= 22.5) {
                    elPacingStatus.className = "status-pill status-optimum";
                    elPacingStatus.textContent = "FLUIDE";
                } else if (curMt <= 33.3) {
                    elPacingStatus.className = "status-pill status-warning";
                    elPacingStatus.textContent = "CHARGE MOY.";
                } else {
                    elPacingStatus.className = "status-pill status-danger";
                    elPacingStatus.textContent = "SATURÉ CPU";
                }
            } else {
                elPacingStatus.className = "status-pill status-optimum";
                elPacingStatus.textContent = "ATTENTE";
            }
        }

        // 4. VRAM & ROLLING CACHE
        if (elVramVal) {
            if (data.msfs_vram_mb) {
                elVramVal.textContent = (data.msfs_vram_mb / 1024).toFixed(1) + " GB";
            } else {
                elVramVal.textContent = "--";
            }
        }

        if (elCacheVal) {
            elCacheVal.textContent = (data.cache_read_mbps || 0.0).toFixed(1) + " MB/s";
        }

        // 5. BLACKBOX STATE
        if (elBlackboxBtn && elRecBtnLabel) {
            if (data.is_tracking) {
                elBlackboxBtn.className = "btn-record btn-rec-active";
                elRecBtnLabel.textContent = "STOP & DEBRIEF (" + (data.elapsed_str || "REC") + ")";
            } else {
                elBlackboxBtn.className = "btn-record btn-rec-idle";
                elRecBtnLabel.textContent = "DÉMARRER ENREGISTREMENT (BLACKBOX)";
            }
        }
    }

    function renderSparkline() {
        if (!ctxSparkline || fpsHistory.length < 2) return;

        const w = canvasSparkline.width;
        const h = canvasSparkline.height;

        ctxSparkline.clearRect(0, 0, w, h);

        const minVal = Math.max(10, Math.min.apply(null, fpsHistory) - 5);
        const maxVal = Math.max.apply(null, fpsHistory) + 5;
        const range = maxVal - minVal || 1;

        // Background subtle grid lines
        ctxSparkline.strokeStyle = "rgba(255, 255, 255, 0.05)";
        ctxSparkline.lineWidth = 1;
        ctxSparkline.beginPath();
        ctxSparkline.moveTo(0, h / 2);
        ctxSparkline.lineTo(w, h / 2);
        ctxSparkline.stroke();

        // Draw Area & Line
        ctxSparkline.beginPath();
        const step = w / (MAX_HISTORY_POINTS - 1);
        const startX = (MAX_HISTORY_POINTS - fpsHistory.length) * step;

        for (let i = 0; i < fpsHistory.length; i++) {
            const x = startX + i * step;
            const y = h - ((fpsHistory[i] - minVal) / range) * (h - 6) - 3;
            if (i === 0) {
                ctxSparkline.moveTo(x, y);
            } else {
                ctxSparkline.lineTo(x, y);
            }
        }

        ctxSparkline.strokeStyle = "#38bdf8";
        ctxSparkline.lineWidth = 2;
        ctxSparkline.stroke();

        // Calculate Delta over last 10 points
        if (fpsHistory.length >= 10 && elDeltaLabel) {
            const recent = fpsHistory[fpsHistory.length - 1];
            const older = fpsHistory[fpsHistory.length - 10];
            const diff = recent - older;
            if (Math.abs(diff) >= 1.0) {
                const sign = diff >= 0 ? "+" : "";
                const color = diff >= 0 ? "#34d399" : "#f87171";
                elDeltaLabel.textContent = "Δ 10s: " + sign + diff.toFixed(1) + " FPS";
                elDeltaLabel.style.color = color;
            } else {
                elDeltaLabel.textContent = "Stable";
                elDeltaLabel.style.color = "#94a3b8";
            }
        }
    }

    function onSmartLodClick() {
        if (isSmartLodToggling) return;
        isSmartLodToggling = true;

        fetch(API_BASE + "/smart_lod/toggle", { method: "POST", cache: "no-store" })
            .then(function (res) { return res.json(); })
            .then(function () {
                // Poll immediately to reflect state
                setTimeout(pollTelemetry, 150);
            })
            .catch(function (err) {
                console.error("Smart LOD toggle error:", err);
            })
            .finally(function () {
                setTimeout(function () { isSmartLodToggling = false; }, 400);
            });
    }

    function onBlackboxClick() {
        if (isBlackboxToggling) return;
        isBlackboxToggling = true;

        fetch(API_BASE + "/blackbox/toggle", { method: "POST", cache: "no-store" })
            .then(function (res) { return res.json(); })
            .then(function () {
                setTimeout(pollTelemetry, 150);
            })
            .catch(function (err) {
                console.error("Blackbox toggle error:", err);
            })
            .finally(function () {
                setTimeout(function () { isBlackboxToggling = false; }, 400);
            });
    }

    // Auto-init on load
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
