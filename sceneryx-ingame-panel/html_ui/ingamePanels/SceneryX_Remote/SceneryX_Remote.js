// =========================================================
// SceneryX MSFS In-Game Toolbar Panel - Remote Controller
// =========================================================

class SceneryXPanel extends TemplateElement {
    constructor() {
        super();
        this.API_BASE = "http://127.0.0.1:8383/api";
        this.POLL_INTERVAL_MS = 1000;
        this.MAX_HISTORY_POINTS = 30;

        this.isConnected = false;
        this.fpsHistory = [];
        this.isSmartLodToggling = false;
        this.isBlackboxToggling = false;

        // DOM Elements
        this.elConnBadge = null;
        this.elDisconnectedView = null;
        this.elConnectedView = null;
        this.elPanelCloseBtn = null;

        this.elSmartLodBtn = null;
        this.elSmartLodLabel = null;
        this.elSmartLodDot = null;
        this.elSmartLodTlodBadge = null;
        this.elSmartLodDesc = null;

        this.elFpsVal = null;
        this.elFpsBase = null;
        this.elMtVal = null;
        this.elPacingStatus = null;
        this.elDeltaLabel = null;
        this.canvasSparkline = null;
        this.ctxSparkline = null;

        this.elVramVal = null;
        this.elCacheVal = null;
        this.elBlackboxBtn = null;
        this.elRecDot = null;
        this.elRecBtnLabel = null;
    }

    connectedCallback() {
        super.connectedCallback();
        let self = this;

        function replaceText(node) {
            if (node.nodeType === Node.TEXT_NODE) {
                if (node.nodeValue && node.nodeValue.toUpperCase().trim() === "PANEL_SCENERYX_R") {
                    node.nodeValue = "SCENERYX REMOTE";
                }
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                if (node.shadowRoot) {
                    for (let child of node.shadowRoot.childNodes) replaceText(child);
                }
                for (let child of node.childNodes) replaceText(child);
            }
        }

        function forceTitle() {
            replaceText(document.documentElement);
            let ui = document.querySelector("ingame-ui");
            if (ui) ui.setAttribute("title", "SCENERYX REMOTE");
            let header = document.querySelector("ingame-ui-header");
            if (header) {
                header.setAttribute("title", "SCENERYX REMOTE");
                if (header.shadowRoot) {
                    let titleElem = header.shadowRoot.querySelector(".title");
                    if (titleElem) titleElem.innerText = "SCENERYX REMOTE";
                }
            }
        }

        setTimeout(forceTitle, 500);
        setTimeout(forceTitle, 1500);
        setTimeout(forceTitle, 3000);

        setTimeout(() => {
            self.init();
        }, 300);
    }

    init() {
        let root = this;

        this.elConnBadge = root.querySelector("#conn-badge");
        this.elDisconnectedView = root.querySelector("#disconnected-view");
        this.elConnectedView = root.querySelector("#connected-view");
        this.elPanelCloseBtn = root.querySelector("#panel-close-btn");

        this.elSmartLodBtn = root.querySelector("#smart-lod-toggle-btn");
        this.elSmartLodLabel = root.querySelector("#smart-lod-btn-label");
        this.elSmartLodDot = root.querySelector("#smart-lod-dot");
        this.elSmartLodTlodBadge = root.querySelector("#smart-lod-tlod-badge");
        this.elSmartLodDesc = root.querySelector("#smart-lod-status-desc");

        this.elFpsVal = root.querySelector("#live-fps-val");
        this.elFpsBase = root.querySelector("#live-fps-base");
        this.elMtVal = root.querySelector("#live-mt-val");
        this.elPacingStatus = root.querySelector("#live-pacing-status");
        this.elDeltaLabel = root.querySelector("#fps-delta-label");

        this.canvasSparkline = root.querySelector("#fps-sparkline-canvas");
        if (this.canvasSparkline && this.canvasSparkline.getContext) {
            this.ctxSparkline = this.canvasSparkline.getContext("2d");
        }

        this.elVramVal = root.querySelector("#live-vram-val");
        this.elCacheVal = root.querySelector("#live-cache-val");
        this.elBlackboxBtn = root.querySelector("#blackbox-toggle-btn");
        this.elRecDot = root.querySelector("#rec-dot");
        this.elRecBtnLabel = root.querySelector("#rec-btn-label");

        if (this.elSmartLodBtn) {
            this.elSmartLodBtn.addEventListener("click", () => this.onSmartLodClick());
        }

        if (this.elBlackboxBtn) {
            this.elBlackboxBtn.addEventListener("click", () => this.onBlackboxClick());
        }

        if (this.elPanelCloseBtn) {
            this.elPanelCloseBtn.addEventListener("click", () => {
                let ui = document.querySelector("ingame-ui");
                if (ui && ui.close) {
                    ui.close();
                } else if (window.parent && window.parent.document) {
                    let parentUi = window.parent.document.querySelector("ingame-ui#SceneryX_Remote");
                    if (parentUi && parentUi.close) parentUi.close();
                }
            });
        }

        // Start Telemetry Polling Loop
        this.pollTelemetry();
        setInterval(() => this.pollTelemetry(), this.POLL_INTERVAL_MS);
    }

    pollTelemetry() {
        let self = this;
        let url = this.API_BASE + "/telemetry";

        if (typeof fetch !== "undefined") {
            fetch(url, { cache: "no-store" })
                .then(function(res) {
                    if (!res.ok) throw new Error("HTTP " + res.status);
                    return res.json();
                })
                .then(function(data) {
                    self.setConnectedState(true);
                    self.updateTelemetryUI(data);
                })
                .catch(function() {
                    self.setConnectedState(false);
                });
            return;
        }

        let xhr = new XMLHttpRequest();
        xhr.open("GET", url, true);
        xhr.timeout = 2000;

        xhr.onload = function () {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    let data = JSON.parse(xhr.responseText);
                    self.setConnectedState(true);
                    self.updateTelemetryUI(data);
                } catch (e) {
                    self.setConnectedState(false);
                }
            } else {
                self.setConnectedState(false);
            }
        };

        xhr.onerror = function () {
            self.setConnectedState(false);
        };

        xhr.ontimeout = function () {
            self.setConnectedState(false);
        };

        xhr.send();
    }

    setConnectedState(online) {
        this.isConnected = online;
        if (!this.elConnBadge) return;

        if (online) {
            this.elConnBadge.textContent = "ONLINE";
            this.elConnBadge.className = "badge-online";
            if (this.elDisconnectedView) this.elDisconnectedView.classList.add("hidden");
            if (this.elConnectedView) this.elConnectedView.classList.remove("hidden");
        } else {
            this.elConnBadge.textContent = "OFFLINE";
            this.elConnBadge.className = "badge-offline";
            if (this.elDisconnectedView) this.elDisconnectedView.classList.remove("hidden");
            if (this.elConnectedView) this.elConnectedView.classList.add("hidden");
        }
    }

    updateTelemetryUI(data) {
        if (!data) return;

        // 1. SMART LOD CONTROLLER
        let lod = data.smart_lod || {};
        let lodActive = (lod.active !== undefined) ? !!lod.active : (!!data.smart_lod_running && !!data.smart_lod_enabled);
        let curTlod = (lod.current_tlod !== undefined && lod.current_tlod !== null) ? lod.current_tlod : (data.smart_lod_tlod !== undefined ? data.smart_lod_tlod : "--");
        let curOlod = (lod.current_olod !== undefined && lod.current_olod !== null) ? lod.current_olod : "--";
        let targetFps = lod.target_fps || "--";

        if (this.elSmartLodTlodBadge) {
            if (curTlod !== "--" && curOlod !== "--") {
                this.elSmartLodTlodBadge.textContent = "TLOD " + Math.round(curTlod) + " / OLOD " + Math.round(curOlod);
            } else if (curTlod !== "--") {
                this.elSmartLodTlodBadge.textContent = "TLOD: " + Math.round(curTlod);
            } else {
                this.elSmartLodTlodBadge.textContent = "TLOD: --";
            }
        }

        if (this.elSmartLodBtn && !this.isSmartLodToggling) {
            if (lodActive) {
                this.elSmartLodBtn.className = "btn-smart-lod btn-active";
                if (this.elSmartLodLabel) this.elSmartLodLabel.textContent = "SMART LOD : ACTIF";
                if (this.elSmartLodDesc) this.elSmartLodDesc.textContent = "Cible: " + targetFps + " FPS • Régulation continue";
            } else {
                this.elSmartLodBtn.className = "btn-smart-lod btn-inactive";
                if (this.elSmartLodLabel) this.elSmartLodLabel.textContent = "SMART LOD : INACTIF";
                if (this.elSmartLodDesc) this.elSmartLodDesc.textContent = "Cliquez pour engager la régulation dynamique";
            }
        }

        // 2. LIVE FPS & PERFORMANCE
        let perf = data.perf || {};
        let dispFps = (perf.displayed_fps !== undefined && perf.displayed_fps !== null) ? perf.displayed_fps : (data.displayed_fps || 0);
        let baseFps = (perf.fps !== undefined && perf.fps !== null) ? perf.fps : (data.base_fps || 0);
        let mtMs = (perf.main_thread_ms !== undefined && perf.main_thread_ms !== null) ? perf.main_thread_ms : (data.main_thread_ms || 0);
        let pacing = perf.frame_pacing || "OPTIMAL";

        if (this.elFpsVal) {
            this.elFpsVal.textContent = dispFps > 0 ? Math.round(dispFps) : "--";
        }
        if (this.elFpsBase) {
            this.elFpsBase.textContent = baseFps > 0 ? "(" + Math.round(baseFps) + " base)" : "(-- base)";
        }
        if (this.elMtVal) {
            this.elMtVal.textContent = mtMs > 0 ? mtMs.toFixed(1) : "--";
        }
        if (this.elPacingStatus) {
            this.elPacingStatus.textContent = pacing;
            if (pacing === "OPTIMAL" || pacing === "FLUIDE") {
                this.elPacingStatus.className = "status-pill status-optimum";
            } else if (pacing === "ACCEPTABLE" || pacing === "CHARGE") {
                this.elPacingStatus.className = "status-pill status-warning";
            } else {
                this.elPacingStatus.className = "status-pill status-danger";
            }
        }

        // 3. SPARKLINE & DELTA CALCULATION
        if (dispFps > 0) {
            this.fpsHistory.push(dispFps);
            if (this.fpsHistory.length > this.MAX_HISTORY_POINTS) {
                this.fpsHistory.shift();
            }
            this.drawSparkline();
        }

        // 4. VRAM & ROLLING CACHE
        if (this.elVramVal) {
            let vramUsed = data.vram_used_gb !== undefined ? data.vram_used_gb : (data.msfs_vram_mb ? (data.msfs_vram_mb / 1024).toFixed(1) : 0);
            let vramTot = data.vram_total_gb !== undefined ? data.vram_total_gb : (data.vram_total_mb ? (data.vram_total_mb / 1024).toFixed(1) : 0);
            this.elVramVal.textContent = (vramUsed || "--") + " / " + (vramTot || "--") + " Go";
        }
        if (this.elCacheVal) {
            let cacheVal = data.rolling_cache_gb !== undefined ? data.rolling_cache_gb : (data.cache_read_mbps || 0);
            this.elCacheVal.textContent = cacheVal + " Go";
        }

        // 5. BLACKBOX RECORDER
        let isRec = !!data.blackbox_recording;
        if (this.elBlackboxBtn && !this.isBlackboxToggling) {
            if (isRec) {
                this.elBlackboxBtn.className = "btn-rec btn-rec-active";
                if (this.elRecBtnLabel) this.elRecBtnLabel.textContent = "ENREGISTREMENT EN COURS...";
            } else {
                this.elBlackboxBtn.className = "btn-rec btn-rec-inactive";
                if (this.elRecBtnLabel) this.elRecBtnLabel.textContent = "ENREGISTREMENT FLIGHT RIG";
            }
        }
    }

    drawSparkline() {
        if (!this.ctxSparkline || !this.canvasSparkline || this.fpsHistory.length < 2) return;

        let w = this.canvasSparkline.width;
        let h = this.canvasSparkline.height;
        let ctx = this.ctxSparkline;

        ctx.clearRect(0, 0, w, h);

        let minVal = Math.min(...this.fpsHistory);
        let maxVal = Math.max(...this.fpsHistory);
        if (maxVal - minVal < 5) {
            maxVal += 3;
            minVal = Math.max(0, minVal - 3);
        }

        let range = maxVal - minVal || 1;
        let stepX = w / (this.MAX_HISTORY_POINTS - 1);
        let startIdx = this.MAX_HISTORY_POINTS - this.fpsHistory.length;

        // Draw gradient fill
        let grad = ctx.createLinearGradient(0, 0, 0, h);
        grad.addColorStop(0, "rgba(56, 189, 248, 0.35)");
        grad.addColorStop(1, "rgba(56, 189, 248, 0.0)");

        ctx.beginPath();
        for (let i = 0; i < this.fpsHistory.length; i++) {
            let x = (startIdx + i) * stepX;
            let norm = (this.fpsHistory[i] - minVal) / range;
            let y = h - (norm * (h - 6)) - 3;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.lineTo((startIdx + this.fpsHistory.length - 1) * stepX, h);
        ctx.lineTo(startIdx * stepX, h);
        ctx.closePath();
        ctx.fillStyle = grad;
        ctx.fill();

        // Draw stroke line
        ctx.beginPath();
        for (let i = 0; i < this.fpsHistory.length; i++) {
            let x = (startIdx + i) * stepX;
            let norm = (this.fpsHistory[i] - minVal) / range;
            let y = h - (norm * (h - 6)) - 3;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = "#38bdf8";
        ctx.lineWidth = 2;
        ctx.stroke();

        // Calculate Delta (last vs first in 30s window)
        let first = this.fpsHistory[0];
        let last = this.fpsHistory[this.fpsHistory.length - 1];
        let delta = Math.round(last - first);

        if (this.elDeltaLabel) {
            if (delta > 0) {
                this.elDeltaLabel.textContent = "+" + delta + " FPS";
                this.elDeltaLabel.className = "delta-label delta-up";
            } else if (delta < 0) {
                this.elDeltaLabel.textContent = delta + " FPS";
                this.elDeltaLabel.className = "delta-label delta-down";
            } else {
                this.elDeltaLabel.textContent = "0 FPS";
                this.elDeltaLabel.className = "delta-label delta-neutral";
            }
        }
    }

    onSmartLodClick() {
        let self = this;
        this.isSmartLodToggling = true;
        let url = this.API_BASE + "/smart_lod/toggle";

        if (typeof fetch !== "undefined") {
            fetch(url, { method: "POST" })
                .then(function(r) { return r.json(); })
                .then(function() {
                    self.isSmartLodToggling = false;
                    self.pollTelemetry();
                })
                .catch(function() {
                    self.isSmartLodToggling = false;
                });
            return;
        }

        let xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.timeout = 2000;
        xhr.onload = function () {
            self.isSmartLodToggling = false;
            self.pollTelemetry();
        };
        xhr.onerror = function () {
            self.isSmartLodToggling = false;
        };
        xhr.send();
    }

    onBlackboxClick() {
        let self = this;
        this.isBlackboxToggling = true;
        let url = this.API_BASE + "/blackbox/toggle";

        if (typeof fetch !== "undefined") {
            fetch(url, { method: "POST" })
                .then(function(r) { return r.json(); })
                .then(function() {
                    self.isBlackboxToggling = false;
                    self.pollTelemetry();
                })
                .catch(function() {
                    self.isBlackboxToggling = false;
                });
            return;
        }

        let xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.timeout = 2000;
        xhr.onload = function () {
            self.isBlackboxToggling = false;
            self.pollTelemetry();
        };
        xhr.onerror = function () {
            self.isBlackboxToggling = false;
        };
        xhr.send();
    }
}

window.customElements.define("sceneryx-panel", SceneryXPanel);
checkAutoload();
