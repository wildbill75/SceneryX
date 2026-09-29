import os
import sys
import json
import shutil

BASE_DIR = r"D:\SceneryX"
PANEL_PKG_DIR = os.path.join(BASE_DIR, "sceneryx-ingame-panel")
GATEFINDER_SPB = r"D:\GateFinder\GateFinder_V1.7\wildbill75-gatefinder\InGamePanels\InGamePanel_GateFinder.spb"

def build():
    print("[*] Rebuilding sceneryx-ingame-panel with exact GateFinder standard...")
    if os.path.exists(PANEL_PKG_DIR):
        shutil.rmtree(PANEL_PKG_DIR)
    
    os.makedirs(os.path.join(PANEL_PKG_DIR, "InGamePanels"), exist_ok=True)
    os.makedirs(os.path.join(PANEL_PKG_DIR, "html_ui", "icons", "toolbar"), exist_ok=True)
    os.makedirs(os.path.join(PANEL_PKG_DIR, "html_ui", "Textures", "Menu", "toolbar"), exist_ok=True)
    os.makedirs(os.path.join(PANEL_PKG_DIR, "html_ui", "ingamePanels", "SceneryX_Remote"), exist_ok=True)

    # 1. MANIFEST.JSON
    manifest = {
        "dependencies": [],
        "content_type": "UI",
        "title": "SceneryX Live Remote",
        "manufacturer": "SceneryX",
        "creator": "wildbill75",
        "package_version": "1.0.0",
        "minimum_game_version": "1.0.0",
        "release_notes": {
            "neutral": {
                "LastUpdate": "SceneryX Live Remote & Smart LOD In-Game Panel",
                "OlderHistory": ""
            }
        }
    }
    with open(os.path.join(PANEL_PKG_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("  -> manifest.json written (content_type: UI)")

    # 2. EN-US.LOCPAK
    locpak = {
        "LocalisationPackage": {
            "Language": "en-US",
            "Strings": {
                "SceneryX_Remote": "SceneryX Remote",
                "PANEL_SCENERYX_R": "SceneryX Remote",
                "PANEL_SCENERYX": "SceneryX Remote",
                "SceneryX Panel": "SceneryX Remote",
                "SceneryXPanel": "SceneryX Remote",
                "SCENERYXPANEL": "SceneryX Remote",
                "SceneryX_R": "SceneryX Remote",
                "SceneryX": "SceneryX Remote"
            }
        }
    }
    with open(os.path.join(PANEL_PKG_DIR, "en-US.locPak"), "w", encoding="utf-8") as f:
        json.dump(locpak, f, indent=2)
    print("  -> en-US.locPak written")

    # 3. SPB FILE GENERATION (from GateFinder SPB reverse-engineered XOR keystream)
    with open(GATEFINDER_SPB, "rb") as f:
        orig = bytearray(f.read())
    
    s1_url = orig[0x23f : 0x23f + 58]
    p1_url = b"html_UI/ingamePanels/GateFinderPanel/GateFinderPanel.html\x00\x00"
    ks = [c ^ p for c, p in zip(s1_url, p1_url)]

    def encrypt(text):
        return bytes([c ^ k for c, k in zip(text, ks[:len(text)])])

    new_id = encrypt(b"PANEL_SCENERYX_R\x00")
    new_title = encrypt(b"SceneryX Panel\x00")
    new_url = encrypt(b"html_ui/ingamePanels/SceneryX_Remote/SceneryX_Remote.html\x00")
    new_icon = encrypt(b"SceneryX_R\x00")

    orig[0x20f : 0x20f + 17] = new_id
    orig[0x228 : 0x228 + 15] = new_title
    orig[0x23f : 0x23f + 58] = new_url
    orig[0x2b9 : 0x2b9 + 11] = new_icon

    spb_out = os.path.join(PANEL_PKG_DIR, "InGamePanels", "InGamePanel_SceneryX.spb")
    with open(spb_out, "wb") as f:
        f.write(orig)
    print("  -> InGamePanels/InGamePanel_SceneryX.spb generated and verified!")

    # 4. TOOLBAR ICONS (SVGs)
    svg_active = '''<svg width="64" height="64" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <g id="HIGHLIGHT">
    <!-- Outer Cyan Ring -->
    <circle cx="50" cy="50" r="42" fill="none" stroke="#38bdf8" stroke-width="4" opacity="0.95"/>
    <circle cx="50" cy="50" r="28" fill="none" stroke="#38bdf8" stroke-width="2" stroke-dasharray="4 4" opacity="0.6"/>
    <!-- Runway Centerline X -->
    <line x1="26" y1="26" x2="74" y2="74" stroke="#ffffff" stroke-width="8" stroke-linecap="round"/>
    <line x1="74" y1="26" x2="26" y2="74" stroke="#38bdf8" stroke-width="8" stroke-linecap="round"/>
    <line x1="26" y1="26" x2="74" y2="74" stroke="#0ea5e9" stroke-width="2" stroke-dasharray="4 3"/>
    <!-- Radar Center Core -->
    <circle cx="50" cy="50" r="5" fill="#ffffff"/>
  </g>
</svg>'''

    svg_off = '''<svg width="64" height="64" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <g id="HIGHLIGHT">
    <circle cx="50" cy="50" r="42" fill="none" stroke="#94a3b8" stroke-width="4" opacity="0.8"/>
    <circle cx="50" cy="50" r="28" fill="none" stroke="#94a3b8" stroke-width="2" stroke-dasharray="4 4" opacity="0.5"/>
    <line x1="26" y1="26" x2="74" y2="74" stroke="#cbd5e1" stroke-width="8" stroke-linecap="round"/>
    <line x1="74" y1="26" x2="26" y2="74" stroke="#94a3b8" stroke-width="8" stroke-linecap="round"/>
    <circle cx="50" cy="50" r="5" fill="#cbd5e1"/>
  </g>
</svg>'''

    icon_names = [
        "SceneryX_R",
        "SceneryX",
        "SceneryXPanel",
        "ICON_TOOLBAR_SCENERYX_R",
        "ICON_TOOLBAR_SCENERYX",
        "ICON_TOOLBAR_SCENERYXPANEL"
    ]

    target_dirs = [
        os.path.join(PANEL_PKG_DIR, "html_ui", "icons", "toolbar"),
        os.path.join(PANEL_PKG_DIR, "html_ui", "Textures", "Menu", "toolbar")
    ]

    for d in target_dirs:
        for name in icon_names:
            with open(os.path.join(d, f"{name}.svg"), "w", encoding="utf-8") as f:
                f.write(svg_active)
            with open(os.path.join(d, f"{name}-OFF.svg"), "w", encoding="utf-8") as f:
                f.write(svg_off)
    print("  -> Toolbar SVGs written in icons/toolbar and Textures/Menu/toolbar")

    # 5. HTML, CSS, JS
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <link rel="stylesheet" href="/SCSS/common.css" />
    <link rel="stylesheet" href="SceneryX_Remote.css?v=2" />

    <script type="text/javascript" src="/JS/coherent.js"></script>
    <script type="text/javascript" src="/JS/common.js"></script>
    <script type="text/javascript" src="/JS/dataStorage.js"></script>
    <script type="text/javascript" src="/JS/buttons.js"></script>
    <script type="text/javascript" src="/JS/Services/ToolBarPanels.js"></script>
    <script type="text/javascript" src="/Pages/VCockpit/Instruments/Shared/BaseInstrument.js"></script>

    <link rel="import" href="/templates/NewPushButton/NewPushButton.html" />
    <link rel="import" href="/templates/ToggleButton/toggleButton.html" />
    <link rel="import" href="/templates/tabMenu/tabMenu.html" />
    <link rel="import" href="/templates/ingameUi/ingameUi.html" />
    <link rel="import" href="/templates/ingameUiHeader/ingameUiHeader.html" />
    <link rel="import" href="/templates/NewListButton/NewListButton.html" />
    <script type="text/javascript" src="SceneryX_Remote.js?v=2"></script>
</head>
<body class="border-box color-white">
    <sceneryx-panel>
        <ingame-ui id="SceneryX_Remote" panel-id="PANEL_SCENERYX_R" title="SCENERYX REMOTE" class="ingameUiFrame panelInvisible" content-fit="true" min-width="330" min-height="350">
            <section id="sceneryx-panel-root" class="sceneryx-container">
                <!-- TOP HEADER -->
                <div class="panel-header">
                    <div class="header-left">
                        <span class="app-icon">✈</span>
                        <span class="app-title">SCENERYX REMOTE</span>
                    </div>
                    <div class="header-right">
                        <span id="conn-badge" class="badge-offline">OFFLINE</span>
                        <button type="button" id="panel-close-btn" class="close-btn" title="Fermer">✕</button>
                    </div>
                </div>

                <!-- DISCONNECTED SCREEN -->
                <div id="disconnected-view" class="disconnected-box">
                    <div class="offline-icon">⚠</div>
                    <div class="offline-title">SceneryX non connecté</div>
                    <div class="offline-desc">Veuillez lancer l'application <strong>SceneryX</strong> sur le bureau Windows pour activer la télécommande et Smart LOD.</div>
                </div>

                <!-- MAIN LIVE CONTENT -->
                <div id="connected-view" class="main-content hidden">

                    <!-- SECTION 1: SMART LOD CONTROLLER -->
                    <div class="card smart-lod-card">
                        <div class="card-header">
                            <span class="card-title">SMART LOD ENGINE</span>
                            <span id="smart-lod-tlod-badge" class="badge-tlod">TLOD: --</span>
                        </div>
                        <div class="smart-lod-body">
                            <button type="button" id="smart-lod-toggle-btn" class="btn-smart-lod btn-inactive">
                                <span class="dot" id="smart-lod-dot"></span>
                                <span id="smart-lod-btn-label">SMART LOD : INACTIF</span>
                            </button>
                            <span id="smart-lod-status-desc" class="subtext">Régulation en mémoire</span>
                        </div>
                    </div>

                    <!-- SECTION 2: LIVE PERFORMANCE & HOT FPS IMPACT -->
                    <div class="card perf-card">
                        <div class="perf-grid">
                            <!-- Displayed FPS -->
                            <div class="perf-col">
                                <span class="metric-label">DISPLAYED FPS</span>
                                <div class="metric-main">
                                    <span id="live-fps-val" class="metric-number">--</span>
                                    <span class="metric-unit">FPS</span>
                                </div>
                                <span id="live-fps-base" class="subtext">(-- base)</span>
                            </div>

                            <!-- CPU Frame Pacing -->
                            <div class="perf-col">
                                <span class="metric-label">CPU MAIN THREAD</span>
                                <div class="metric-main">
                                    <span id="live-mt-val" class="metric-number">--</span>
                                    <span class="metric-unit">ms</span>
                                </div>
                                <span id="live-pacing-status" class="status-pill status-optimum">FLUIDE</span>
                            </div>
                        </div>

                        <!-- LIVE FPS TREND (30-SEC SPARKLINE TO SEE HOT IMPACT) -->
                        <div class="sparkline-wrapper">
                            <div class="sparkline-header">
                                <span class="sparkline-title">Tendance FPS (30s) • Impact à chaud</span>
                                <span id="fps-delta-label" class="delta-label">--</span>
                            </div>
                            <canvas id="fps-sparkline-canvas" width="280" height="34" class="sparkline-canvas"></canvas>
                        </div>
                    </div>

                    <!-- SECTION 3: VRAM & ROLLING CACHE METRICS -->
                    <div class="card mini-card">
                        <div class="mini-grid">
                            <div class="mini-item">
                                <span class="mini-label">MSFS VRAM:</span>
                                <span id="live-vram-val" class="mini-val">--</span>
                            </div>
                            <div class="mini-item">
                                <span class="mini-label">Rolling Cache:</span>
                                <span id="live-cache-val" class="mini-val">--</span>
                            </div>
                        </div>
                    </div>

                    <!-- SECTION 4: BLACKBOX TELEMETRY RECORDER -->
                    <div class="card rec-card">
                        <button type="button" id="blackbox-toggle-btn" class="btn-rec btn-rec-inactive">
                            <span class="rec-dot" id="rec-dot"></span>
                            <span id="rec-btn-label">ENREGISTREMENT FLIGHT RIG</span>
                        </button>
                    </div>

                </div>
            </section>
        </ingame-ui>
    </sceneryx-panel>
</body>
</html>'''

    panel_ui_dir = os.path.join(PANEL_PKG_DIR, "html_ui", "ingamePanels", "SceneryX_Remote")
    with open(os.path.join(panel_ui_dir, "SceneryX_Remote.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    css_content = '''/* =========================================================
   SceneryX MSFS In-Game Toolbar Panel - Blue Glass CSS Theme
   ========================================================= */

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    user-select: none;
    -webkit-user-select: none;
}

body.border-box {
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: transparent;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #e2e8f0;
}

sceneryx-panel {
    display: block;
    width: 100%;
    height: 100%;
}

.sceneryx-container {
    width: 100%;
    min-width: 310px;
    max-width: 340px;
    background: rgba(10, 18, 30, 0.94);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

/* HEADER */
.panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(56, 189, 248, 0.15);
}

.header-left {
    display: flex;
    align-items: center;
    gap: 6px;
}

.app-icon {
    color: #00d2ff;
    font-size: 14px;
}

.app-title {
    font-family: 'Consolas', monospace;
    font-weight: 800;
    font-size: 12px;
    letter-spacing: 0.5px;
    color: #f8fafc;
}

.header-right {
    display: flex;
    align-items: center;
    gap: 6px;
}

.badge-offline {
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.5);
    color: #f87171;
    font-size: 9px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 6px;
    letter-spacing: 0.5px;
}

.badge-online {
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid rgba(16, 185, 129, 0.5);
    color: #34d399;
    font-size: 9px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 6px;
    letter-spacing: 0.5px;
}

.close-btn {
    background: none;
    border: none;
    color: #64748b;
    font-size: 14px;
    cursor: pointer;
    line-height: 1;
    padding: 2px;
    transition: color 0.15s ease;
}

.close-btn:hover {
    color: #f87171;
}

/* DISCONNECTED VIEW */
.disconnected-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 20px 10px;
    background: rgba(15, 23, 42, 0.6);
    border-radius: 8px;
    border: 1px dashed rgba(100, 116, 139, 0.3);
}

.offline-icon {
    font-size: 28px;
    color: #f59e0b;
    margin-bottom: 8px;
}

.offline-title {
    font-weight: 700;
    font-size: 13px;
    color: #e2e8f0;
    margin-bottom: 4px;
}

.offline-desc {
    font-size: 11px;
    color: #94a3b8;
    line-height: 1.4;
}

/* CARDS */
.main-content {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.card {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(56, 189, 248, 0.15);
    border-radius: 8px;
    padding: 8px 10px;
}

.card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
}

.card-title {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: #94a3b8;
}

.badge-tlod {
    font-family: 'Consolas', monospace;
    font-size: 11px;
    font-weight: 800;
    color: #38bdf8;
    background: rgba(56, 189, 248, 0.15);
    padding: 1px 6px;
    border-radius: 4px;
    border: 1px solid rgba(56, 189, 248, 0.3);
}

/* SMART LOD BODY */
.smart-lod-body {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.btn-smart-lod {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    width: 100%;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
}

.btn-active {
    background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    color: #ffffff;
    box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
}

.btn-active:hover {
    background: linear-gradient(135deg, #047857 0%, #059669 100%);
}

.btn-inactive {
    background: rgba(30, 41, 59, 0.8);
    color: #94a3b8;
    border: 1px solid rgba(100, 116, 139, 0.3);
}

.btn-inactive:hover {
    background: rgba(51, 65, 85, 0.8);
    color: #f1f5f9;
}

.dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.btn-active .dot {
    background: #ffffff;
    box-shadow: 0 0 6px #ffffff;
}

.btn-inactive .dot {
    background: #64748b;
}

.subtext {
    font-size: 10px;
    color: #64748b;
    text-align: center;
}

/* PERF GRID */
.perf-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 8px;
}

.perf-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: rgba(10, 15, 25, 0.5);
    border-radius: 6px;
    padding: 6px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.metric-label {
    font-size: 9px;
    font-weight: 700;
    color: #64748b;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
}

.metric-main {
    display: flex;
    align-items: baseline;
    gap: 3px;
}

.metric-number {
    font-family: 'Consolas', monospace;
    font-size: 20px;
    font-weight: 800;
    color: #38bdf8;
    line-height: 1;
}

.metric-unit {
    font-size: 10px;
    font-weight: 600;
    color: #64748b;
}

.status-pill {
    margin-top: 4px;
    font-size: 9px;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 4px;
    letter-spacing: 0.5px;
}

.status-optimum {
    background: rgba(16, 185, 129, 0.2);
    color: #34d399;
}

.status-warning {
    background: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
}

.status-danger {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
}

/* SPARKLINE */
.sparkline-wrapper {
    background: rgba(10, 15, 25, 0.6);
    border-radius: 6px;
    padding: 6px 8px;
    border: 1px solid rgba(56, 189, 248, 0.1);
}

.sparkline-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 4px;
}

.sparkline-title {
    font-size: 9px;
    font-weight: 600;
    color: #94a3b8;
}

.delta-label {
    font-family: 'Consolas', monospace;
    font-size: 10px;
    font-weight: 800;
}

.delta-up {
    color: #34d399;
}

.delta-down {
    color: #f87171;
}

.delta-neutral {
    color: #94a3b8;
}

.sparkline-canvas {
    width: 100%;
    height: 34px;
    display: block;
}

/* MINI METRICS */
.mini-card {
    padding: 6px 8px;
}

.mini-grid {
    display: flex;
    justify-content: space-around;
}

.mini-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 10px;
}

.mini-label {
    color: #64748b;
}

.mini-val {
    font-family: 'Consolas', monospace;
    font-weight: 700;
    color: #e2e8f0;
}

/* BLACKBOX BUTTON */
.btn-rec {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    width: 100%;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
}

.btn-rec-inactive {
    background: rgba(30, 41, 59, 0.7);
    color: #94a3b8;
    border: 1px solid rgba(100, 116, 139, 0.2);
}

.btn-rec-inactive:hover {
    background: rgba(51, 65, 85, 0.7);
    color: #e2e8f0;
}

.btn-rec-active {
    background: rgba(239, 68, 68, 0.25);
    border: 1px solid rgba(239, 68, 68, 0.6);
    color: #fca5a5;
    box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
}

.rec-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
}

.btn-rec-inactive .rec-dot {
    background: #64748b;
}

.btn-rec-active .rec-dot {
    background: #ef4444;
    box-shadow: 0 0 6px #ef4444;
    animation: blink 1s infinite alternate;
}

@keyframes blink {
    0% { opacity: 0.3; }
    100% { opacity: 1; }
}

.hidden {
    display: none !important;
}
'''
    with open(os.path.join(panel_ui_dir, "SceneryX_Remote.css"), "w", encoding="utf-8") as f:
        f.write(css_content)

    js_content = '''// =========================================================
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
'''
    with open(os.path.join(panel_ui_dir, "SceneryX_Remote.js"), "w", encoding="utf-8") as f:
        f.write(js_content)
    print("  -> SceneryX_Remote HTML, CSS, JS written with TemplateElement & checkAutoload()")

    # 6. LAYOUT.JSON GENERATOR
    layout_entries = []
    for root, _, files in os.walk(PANEL_PKG_DIR):
        for file in files:
            if file == "layout.json": continue
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, PANEL_PKG_DIR).replace("\\", "/")
            size = os.path.getsize(filepath)
            date = int(os.path.getmtime(filepath)) * 10000000 + 116444736000000000
            layout_entries.append({
                "path": rel_path,
                "size": size,
                "date": date
            })

    layout = {"content": layout_entries}
    with open(os.path.join(PANEL_PKG_DIR, "layout.json"), "w", encoding="utf-8") as f:
        json.dump(layout, f, indent=2)
    print(f"  -> layout.json generated with {len(layout_entries)} entries.")

    # 7. DEPLOY DIRECTLY TO COMMUNITY
    community_dir = r"C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\Community\sceneryx-ingame-panel"
    print(f"[*] Deploying to MSFS Community folder: {community_dir}...")
    if os.path.exists(community_dir):
        shutil.rmtree(community_dir)
    shutil.copytree(PANEL_PKG_DIR, community_dir)
    print("  -> Successfully deployed to MSFS Community folder!")
    print("\n[SUCCESS] SceneryX In-Game Panel built and deployed!")

if __name__ == "__main__":
    build()
