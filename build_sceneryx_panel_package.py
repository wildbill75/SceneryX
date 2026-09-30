import os
import sys
import json
import shutil
import struct

BASE_DIR = r"D:\SceneryX"
PANEL_PKG_DIR = os.path.join(BASE_DIR, "wildbill75-sceneryx")

COMMUNITY_PATHS = [
    r"C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\Community",
    r"C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\Community2024"
]

CONTENT_XML_PATH = r"C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Content.xml"

AUTOFPS_SPB = r"C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\Community\autofps-html-widget-panel\InGamePanels\InGamePanel_HtmlWidgetPanel.spb"


def build_spb(
    spb_filename: str = "InGamePanel_SceneryX.spb",
    panel_id: str = "PANEL_SCENERYX",
    panel_title: str = "SCENERY X",
    html_url: str = "html_ui/InGamePanels/SceneryX_Remote/SceneryX_Remote.html",
    toolbar_icon: str = "ICON_TOOLBAR_SCENERYX"
) -> bytes:
    """Builds a 100% compliant MSFS 2024 / MSFS 2020 binary SPB for the in-game toolbar panel."""
    ks = [
        42, 7, 43, 49, 50, 92, 99, 142, 191, 241, 82, 181, 72, 12, 2, 84, 14, 86, 98, 100,
        184, 198, 33, 131, 231, 164, 111, 144, 24, 4, 168, 28, 172, 196, 200, 117, 145, 66,
        11, 211, 77, 222, 37, 48, 8, 85, 56, 93, 141, 149, 234, 39, 132, 22, 171, 154, 193,
        74, 96, 16, 170, 45, 88, 12, 99, 210, 114, 55, 89, 140, 201, 15
    ]

    def encode_str(s: str) -> bytes:
        raw = s.encode("utf-8") + b"\x00"
        return bytes([b ^ ks[i % len(ks)] for i, b in enumerate(raw)])

    batc_spb = r"C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\Community\beyondatc-toolbar\InGamePanels\beyondatc-toolbar.spb"
    with open(batc_spb, "rb") as f:
        batc_orig = f.read()

    header = bytearray(batc_orig[:0x18e])

    # Children of Container prop 5
    children = bytearray()

    # prop 6: Panel ID
    enc_id = encode_str(panel_id)
    children.extend(struct.pack("<II", 6, len(enc_id)))
    children.extend(enc_id)

    # prop 7: Title (Rendered natively in Toolbar Tooltip and Window Header)
    enc_title = encode_str(panel_title)
    children.extend(struct.pack("<II", 7, len(enc_title)))
    children.extend(enc_title)

    # prop 8: HTML URL
    enc_url = encode_str(html_url)
    children.extend(struct.pack("<II", 8, len(enc_url)))
    children.extend(enc_url)

    # numeric chunk (56 bytes: 7 props * 8 bytes):
    # Prop 9: int 3 (window type)
    # Prop 10: float 4.0 (x min/pad)
    # Prop 11: float 5.0 (y min/pad)
    # Prop 12: float 28.0 (defaultWidth: 28% screen width)
    # Prop 13: float 24.0 (defaultHeight: 24% screen height - well-proportioned rectangle matching Screen 2)
    # Prop 14: float 20.0 (minWidth)
    # Prop 15: float 2.0 (minHeight - allows clean compact fitting)
    numeric_chunk = bytearray()
    numeric_chunk.extend(struct.pack("<II", 9, 3))
    numeric_chunk.extend(struct.pack("<If", 10, 4.0))
    numeric_chunk.extend(struct.pack("<If", 11, 5.0))
    numeric_chunk.extend(struct.pack("<If", 12, 28.0))
    numeric_chunk.extend(struct.pack("<If", 13, 24.0))
    numeric_chunk.extend(struct.pack("<If", 14, 20.0))
    numeric_chunk.extend(struct.pack("<If", 15, 2.0))
    children.extend(numeric_chunk)


    # prop 16: Icon name
    enc_icon = encode_str(toolbar_icon)
    children.extend(struct.pack("<II", 16, len(enc_icon)))
    children.extend(enc_icon)

    # prop 17: buttonVisible = 1 (12 bytes)
    prop_17 = struct.pack("<III", 17, 1, 0)
    children.extend(prop_17)

    # Outer payload (Document level)
    payload = bytearray()

    # prop 2: InGamePanels
    enc_ingamepanels = encode_str("InGamePanels")
    payload.extend(struct.pack("<II", 2, len(enc_ingamepanels)))
    payload.extend(enc_ingamepanels)

    # prop 3: 12 bytes
    payload.extend(struct.pack("<III", 3, 1, 0))

    # prop 4: Filename
    enc_fn = encode_str(spb_filename)
    payload.extend(struct.pack("<II", 4, len(enc_fn)))
    payload.extend(enc_fn)

    # prop 5: container holding children (length = len(children))
    payload.extend(struct.pack("<II", 5, len(children)))
    payload.extend(children)

    # 4 bytes null tail
    payload.extend(b"\x00\x00\x00\x00")

    # Store payload length at offset 0x18a
    struct.pack_into("<H", header, 0x18a, len(payload))

    return bytes(header) + bytes(payload)


def build():
    print("[*] Rebuilding SceneryX In-Game Panel with authentic MSFS SPB binary, unified locPaks, clean SVG and resilient JS...")
    if os.path.exists(PANEL_PKG_DIR):
        shutil.rmtree(PANEL_PKG_DIR)
    
    os.makedirs(os.path.join(PANEL_PKG_DIR, "InGamePanels"), exist_ok=True)
    os.makedirs(os.path.join(PANEL_PKG_DIR, "html_ui", "icons", "toolbar"), exist_ok=True)
    os.makedirs(os.path.join(PANEL_PKG_DIR, "html_ui", "Textures", "Menu", "toolbar"), exist_ok=True)
    os.makedirs(os.path.join(PANEL_PKG_DIR, "html_ui", "InGamePanels", "SceneryX_Remote"), exist_ok=True)

    # 1. MANIFEST.JSON (v1.0.3 to ensure clean MSFS VFS cache invalidation)
    manifest = {
        "dependencies": [],
        "content_type": "UI",
        "title": "SCENERY X",
        "manufacturer": "SceneryX",
        "creator": "wildbill75",
        "package_version": "1.0.3",
        "minimum_game_version": "1.0.0",
        "release_notes": {
            "neutral": {
                "LastUpdate": "SceneryX In-Game Panel V1.0.3 - Live Telemetry & Smart LOD Remote",
                "OlderHistory": ""
            }
        }
    }
    with open(os.path.join(PANEL_PKG_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("  -> manifest.json written (v1.0.3, title: SCENERY X)")

    # 2. LOCPAKS (Comprehensive string mapping)
    locpak_strings = {
        "SCENERY X": "SCENERY X",
        "SceneryX": "SCENERY X",
        "SCENERYX": "SCENERY X",
        "PANEL_SCENERYX": "SCENERY X",
        "SceneryX_Remote": "SCENERY X",
        "ICON_TOOLBAR_SCENERYX": "SCENERY X",
        "wildbill75-sceneryx": "SCENERY X"
    }

    for lang in ["en-US", "fr-FR"]:
        pkg = {
            "LocalisationPackage": {
                "Language": lang,
                "Strings": locpak_strings
            }
        }
        with open(os.path.join(PANEL_PKG_DIR, f"{lang}.locPak"), "w", encoding="utf-8") as f:
            json.dump(pkg, f, indent=2)
    print("  -> en-US.locPak and fr-FR.locPak written")

    # 3. SPB BINARY
    spb_bytes = build_spb(
        spb_filename="InGamePanel_SceneryX.spb",
        panel_id="PANEL_SCENERYX",
        panel_title="SCENERY X",
        html_url="html_ui/InGamePanels/SceneryX_Remote/SceneryX_Remote.html",
        toolbar_icon="ICON_TOOLBAR_SCENERYX"
    )
    spb_out = os.path.join(PANEL_PKG_DIR, "InGamePanels", "InGamePanel_SceneryX.spb")
    with open(spb_out, "wb") as f:
        f.write(spb_bytes)
    print(f"  -> InGamePanels/InGamePanel_SceneryX.spb compiled ({len(spb_bytes)} bytes, Title: 'SCENERY X')")

    # 4. CLEAN VECTOR SVG ICONS (Authentic sharp SceneryX polygon from Logo_SCENERYX_Blanc.svg)
    svg_icon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-70 -95 591 591" width="100" height="100">
  <polygon fill="#ffffff" points="164.31 0 222.9 94.76 281.48 0 438.27 0 307.9 191.83 450.33 402.6 290.67 402.6 222.9 298.65 156.27 402.6 .63 402.6 141.92 198.14 9.25 0 164.31 0"/>
</svg>'''

    icon_names = [
        "ICON_TOOLBAR_SCENERYX.svg",
        "ICON_TOOLBAR_SCENERYX-OFF.svg",
        "ICON_TOOLBAR_SCENERYX_R.svg",
        "ICON_TOOLBAR_SCENERYX_R-OFF.svg",
        "SceneryX.svg",
        "SceneryX-OFF.svg"
    ]
    for dir_rel in [
        os.path.join(PANEL_PKG_DIR, "html_ui", "icons", "toolbar"),
        os.path.join(PANEL_PKG_DIR, "html_ui", "Textures", "Menu", "toolbar")
    ]:
        for iname in icon_names:
            with open(os.path.join(dir_rel, iname), "w", encoding="utf-8") as f:
                f.write(svg_icon)
    print("  -> Toolbar SVG icons written to all standard paths")

    # 5. HTML_UI PANEL (SceneryX_Remote)
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>SCENERY X</title>
    <link rel="stylesheet" href="/SCSS/common.css" />
    <link rel="stylesheet" href="SceneryX_Remote.css" />
    <script type="text/javascript" src="/JS/coherent.js"></script>
    <script type="text/javascript" src="/JS/common.js"></script>
    <script type="text/javascript" src="/JS/buttons.js"></script>
    <script type="text/javascript" src="/JS/dataStorage.js"></script>
    <script type="text/javascript" src="/JS/Services/ToolBarPanels.js"></script>
    <script type="text/javascript" src="/Pages/VCockpit/Instruments/Shared/BaseInstrument.js"></script>
    <link rel="import" href="/templates/NewPushButton/NewPushButton.html" />
    <link rel="import" href="/templates/ToggleButton/toggleButton.html" />
    <link rel="import" href="/templates/tabMenu/tabMenu.html" />
    <link rel="import" href="/templates/ingameUi/ingameUi.html" />
    <link rel="import" href="/templates/ingameUiHeader/ingameUiHeader.html" />
    <script type="text/javascript" src="SceneryX_Remote.js"></script>
</head>
<body class="border-box">
    <ingamepanel-sceneryx>
        <ingame-ui id="SceneryX_Remote" panel-id="PANEL_SCENERYX" title="SCENERY X"
                   class="ingameUiFrame panelInvisible"
                   content-fit="true" resize="both"
                   min-width="320" min-height="220">

            <!-- OFFLINE VIEW -->
            <div id="disconnected-view" class="offline-box">
                <div class="offline-title">Please launch Scenery X</div>
            </div>

            <!-- ONLINE VIEW -->
            <div id="connected-view" class="main-content hidden">
                <!-- SECTION 1: SMART LOD -->
                <div class="panel-section">
                    <div class="section-header">
                        <span class="section-title">SMART LOD</span>
                    </div>
                    <button type="button" id="smart-lod-toggle-btn" class="msfs-btn btn-primary">
                        <span id="smart-lod-btn-label">ENGAGE</span>
                    </button>
                    <!-- On-the-fly LOD Controls -->
                    <div class="lod-controls-box">
                        <div class="lod-control-row" id="tlod-row">
                            <span class="lod-name" id="tlod-name-label" title="Terrain LOD (Double-click to reset to Auto)">TLOD</span>
                            <button type="button" class="lod-step-btn" id="tlod-minus-btn" title="Decrease TLOD by 10">-10</button>
                            <input type="range" class="lod-slider" id="tlod-slider" min="10" max="400" step="10" value="100" title="Double-click thumb to reset to Auto" />
                            <button type="button" class="lod-step-btn" id="tlod-plus-btn" title="Increase TLOD by 10">+10</button>
                            <span class="lod-val" id="tlod-val-label" title="Double-click to reset to Auto">100</span>
                            <span class="lod-mode-badge badge-mode-auto" id="tlod-mode-badge" title="Double-click slider or click badge to reset to Auto">AUTO</span>
                        </div>
                        <div class="lod-control-row" id="olod-row">
                            <span class="lod-name" id="olod-name-label" title="Object LOD (Double-click to reset to Auto)">OLOD</span>
                            <button type="button" class="lod-step-btn" id="olod-minus-btn" title="Decrease OLOD by 10">-10</button>
                            <input type="range" class="lod-slider" id="olod-slider" min="10" max="300" step="10" value="100" title="Double-click thumb to reset to Auto" />
                            <button type="button" class="lod-step-btn" id="olod-plus-btn" title="Increase OLOD by 10">+10</button>
                            <span class="lod-val" id="olod-val-label" title="Double-click to reset to Auto">100</span>
                            <span class="lod-mode-badge badge-mode-auto" id="olod-mode-badge" title="Double-click slider or click badge to reset to Auto">AUTO</span>
                        </div>
                    </div>
                </div>

                <!-- SECTION 2: PERFORMANCE -->
                <div class="panel-section">
                    <div class="section-header">
                        <span class="section-title">PERFORMANCE</span>
                        <span id="live-pacing-status" class="badge-tag tag-green">OPTIMAL</span>
                    </div>
                    <div class="perf-row">
                        <div class="perf-metric">
                            <span class="metric-label">DISPLAYED FPS</span>
                            <div class="metric-val-wrap">
                                <span id="live-fps-val" class="metric-number">--</span>
                                <span class="metric-unit">FPS</span>
                                <span id="live-fps-base" class="metric-sub"></span>
                            </div>
                        </div>
                        <div class="perf-metric">
                            <span class="metric-label">CPU MAIN THREAD</span>
                            <div class="metric-val-wrap">
                                <span id="live-mt-val" class="metric-number">--</span>
                                <span class="metric-unit">ms</span>
                            </div>
                        </div>
                    </div>
                    <!-- Sparkline -->
                    <div class="sparkline-box">
                        <div class="sparkline-top">
                            <span class="sparkline-title">30S TREND</span>
                            <span id="fps-delta-label" class="delta-label delta-neutral">0 FPS</span>
                        </div>
                        <canvas id="fps-sparkline-canvas" class="sparkline-canvas" width="280" height="32"></canvas>
                    </div>
                </div>

                <!-- SECTION 3: SYSTEM METRICS -->
                <div class="panel-section">
                    <div class="metrics-row">
                        <div class="metric-compact">
                            <span class="compact-label">VRAM:</span>
                            <span id="live-vram-val" class="compact-val">-- GB</span>
                        </div>
                        <div class="metric-compact">
                            <span class="compact-label">CACHE:</span>
                            <span id="live-cache-val" class="compact-val">-- MB/s</span>
                        </div>
                    </div>
                </div>

                <!-- SECTION 4: BLACKBOX RECORDER -->
                <div class="panel-section section-rec">
                    <button type="button" id="blackbox-toggle-btn" class="msfs-btn btn-primary">
                        <span id="rec-btn-label">START RECORDING</span>
                    </button>
                </div>
            </div>
        </ingame-ui>
    </ingamepanel-sceneryx>
</body>
</html>'''

    panel_ui_dir = os.path.join(PANEL_PKG_DIR, "html_ui", "InGamePanels", "SceneryX_Remote")
    with open(os.path.join(panel_ui_dir, "SceneryX_Remote.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    css_content = '''/* =========================================================
   SceneryX MSFS In-Game Toolbar Panel - Native MSFS Theme
   ========================================================= */

html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background-color: transparent !important;
    font-family: 'Open Sans', 'Segoe UI', Tahoma, sans-serif;
    color: #ffffff;
    overflow: hidden;
}

ingamepanel-sceneryx {
    display: block;
    width: 100%;
    height: 100%;
}

ingame-ui#SceneryX_Remote {
    background: transparent !important;
}

ingame-ui#SceneryX_Remote .ingameUiContent {
    background: transparent !important;
    overflow: hidden !important;
}

/* Scoped layout rules - never interfere with MSFS stock header buttons */
.main-content, .offline-box {
    box-sizing: border-box;
    font-family: 'Open Sans', 'Segoe UI', Tahoma, sans-serif;
    color: #ffffff;
    user-select: none;
    -webkit-user-select: none;
}

.main-content *, .offline-box * {
    box-sizing: border-box;
}

/* OFFLINE VIEW - Centered clean white message */
.offline-box {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    min-height: 220px;
    text-align: center;
    padding: 30px 15px;
}

.offline-title {
    font-size: 16px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.5px;
}

/* MAIN LIVE CONTENT */
.main-content {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 10px 12px 12px 12px;
    width: 100%;
    box-sizing: border-box;
}

.panel-section {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 10px 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
}

.section-rec {
    padding: 8px 12px;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
}

.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.section-title {
    font-size: 11.5px;
    font-weight: 800;
    color: #94a3b8;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

/* BADGES / PILLS */
.badge-tag {
    font-size: 10.5px;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 4px;
    letter-spacing: 0.5px;
    background: rgba(148, 163, 184, 0.15);
    color: #cbd5e1;
}

.tag-green {
    background: rgba(16, 185, 129, 0.2);
    color: #34d399;
}

.tag-amber {
    background: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
}

.tag-red {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
}

/* BUTTONS - Centered, stylish, solid colors, sky-blue default */
.msfs-btn {
    width: auto;
    min-width: 170px;
    max-width: 220px;
    margin: 3px auto;
    padding: 7px 22px;
    border: none;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.8px;
    cursor: pointer;
    text-transform: uppercase;
    transition: background 0.15s ease;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
}

.btn-primary {
    background: #0284c7;
}

.btn-primary:hover {
    background: #0ea5e9;
}

.btn-active-green {
    background: #10b981;
}

.btn-active-green:hover {
    background: #059669;
}

.btn-active-red {
    background: #ef4444;
}

.btn-active-red:hover {
    background: #dc2626;
}

/* LOD CONTROLS BOX */
.lod-controls-box {
    display: flex;
    flex-direction: column;
    gap: 7px;
    margin-top: 3px;
    padding-top: 7px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.lod-control-row {
    display: flex;
    align-items: center;
    gap: 7px;
}

.lod-name {
    width: 38px;
    font-size: 12px;
    font-weight: 800;
    color: #cbd5e1;
    letter-spacing: 0.5px;
    cursor: default;
}

.lod-step-btn {
    background: #1e293b;
    color: #ffffff;
    border: none;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 800;
    padding: 4px 7px;
    cursor: pointer;
    min-width: 28px;
    text-align: center;
}

.lod-step-btn:hover {
    background: #334155;
}

.lod-step-btn:active {
    background: #0284c7;
}

.lod-slider {
    flex: 1;
    height: 6px;
    -webkit-appearance: none;
    appearance: none;
    cursor: pointer;
    background: #334155;
    border-radius: 3px;
    outline: none;
}

/* Default AUTO mode thumb: Sky Blue */
.lod-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 15px;
    height: 15px;
    border-radius: 50%;
    background: #0284c7;
    border: 2px solid #ffffff;
    cursor: pointer;
    box-shadow: 0 0 5px rgba(2, 132, 199, 0.7);
    transition: background 0.15s ease, box-shadow 0.15s ease, transform 0.1s ease;
}

.lod-slider::-webkit-slider-thumb:hover {
    transform: scale(1.15);
    box-shadow: 0 0 8px rgba(56, 189, 248, 0.9);
}

/* DÉBRAYÉ / MANUAL OVERRIDE mode thumb: Amber / Orange */
.lod-slider.is-manual::-webkit-slider-thumb {
    background: #f59e0b !important;
    border: 2px solid #ffffff !important;
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.9) !important;
}

.lod-val {
    width: 32px;
    font-family: 'Consolas', monospace;
    font-size: 14px;
    font-weight: 900;
    color: #38bdf8;
    text-align: right;
    cursor: pointer;
    transition: color 0.15s ease;
}

.lod-val.is-manual {
    color: #f59e0b !important;
}

/* Mode pill: AUTO (Sky-blue subtle) vs MAN (Amber warning) */
.lod-mode-badge {
    font-size: 8.5px;
    font-weight: 800;
    padding: 2px 4px;
    border-radius: 3px;
    letter-spacing: 0.5px;
    cursor: pointer;
    user-select: none;
    min-width: 32px;
    text-align: center;
    transition: all 0.15s ease;
}

.badge-mode-auto {
    background: rgba(2, 132, 199, 0.2);
    color: #38bdf8;
    border: 1px solid rgba(2, 132, 199, 0.35);
}

.badge-mode-manual {
    background: rgba(245, 158, 11, 0.25);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.6);
}

.badge-mode-manual:hover {
    background: rgba(245, 158, 11, 0.4);
    box-shadow: 0 0 6px rgba(245, 158, 11, 0.5);
}

/* PERFORMANCE GRID */
.perf-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}

.perf-metric {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: rgba(10, 14, 22, 0.6);
    border-radius: 4px;
    padding: 7px 8px;
}

.metric-label {
    font-size: 10.5px;
    font-weight: 800;
    color: #94a3b8;
    letter-spacing: 0.6px;
    margin-bottom: 3px;
}

.metric-val-wrap {
    display: flex;
    align-items: baseline;
    gap: 4px;
}

.metric-number {
    font-family: 'Consolas', monospace;
    font-size: 26px;
    font-weight: 900;
    color: #ffffff;
    line-height: 1;
}

.metric-unit {
    font-size: 11px;
    font-weight: 800;
    color: #94a3b8;
}

.metric-sub {
    font-size: 11px;
    color: #64748b;
    font-weight: 700;
    margin-left: 2px;
}

/* SPARKLINE */
.sparkline-box {
    display: flex;
    flex-direction: column;
    gap: 4px;
    background: rgba(10, 14, 22, 0.4);
    border-radius: 4px;
    padding: 6px 8px;
    margin-top: 2px;
}

.sparkline-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.sparkline-title {
    font-size: 10px;
    font-weight: 800;
    color: #64748b;
    letter-spacing: 0.5px;
}

.delta-label {
    font-size: 11px;
    font-weight: 900;
    font-family: 'Consolas', monospace;
}

.delta-neutral { color: #94a3b8; }
.delta-up { color: #34d399; }
.delta-down { color: #f87171; }

.sparkline-canvas {
    width: 100%;
    height: 32px;
    display: block;
}

/* SYSTEM METRICS ROW */
.metrics-row {
    display: flex;
    justify-content: space-around;
    align-items: center;
    padding: 2px 0;
}

.metric-compact {
    display: flex;
    gap: 6px;
    align-items: baseline;
}

.compact-label {
    color: #94a3b8;
    font-weight: 800;
    font-size: 12px;
}

.compact-val {
    font-family: 'Consolas', monospace;
    color: #ffffff;
    font-weight: 900;
    font-size: 14.5px;
}

.hidden {
    display: none !important;
}
'''
    with open(os.path.join(panel_ui_dir, "SceneryX_Remote.css"), "w", encoding="utf-8") as f:
        f.write(css_content)

    js_content = '''// =========================================================
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
'''
    with open(os.path.join(panel_ui_dir, "SceneryX_Remote.js"), "w", encoding="utf-8") as f:
        f.write(js_content)
    print("  -> SceneryX_Remote HTML, CSS, JS written with resilient AutoFPS-grade polling and DOM binding")

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

    # 7. DEPLOY DIRECTLY TO ALL COMMUNITY TARGETS (wildbill75-sceneryx ONLY)
    for base_comm in COMMUNITY_PATHS:
        if not os.path.exists(base_comm):
            continue

        # Purge any old conflicting sceneryx-ingame-panel
        old_duplicate = os.path.join(base_comm, "sceneryx-ingame-panel")
        if os.path.exists(old_duplicate):
            shutil.rmtree(old_duplicate)
            print(f"  -> Removed duplicate package from {old_duplicate}")

        dest = os.path.join(base_comm, "wildbill75-sceneryx")
        print(f"[*] Deploying to: {dest}...")
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(PANEL_PKG_DIR, dest)
        print(f"  -> Successfully deployed to {dest}")

    # 8. UPDATE CONTENT.XML (Keep only wildbill75-sceneryx)
    if os.path.exists(CONTENT_XML_PATH):
        try:
            with open(CONTENT_XML_PATH, "r", encoding="utf-8") as f:
                content_xml = f.read()

            # Remove sceneryx-ingame-panel from Content.xml to prevent duplicates
            import re
            content_xml = re.sub(r'\s*<Package name="[^"]*sceneryx-ingame-panel"[^>]*/>', '', content_xml)

            packages_to_ensure = [
                "communityfs20-wildbill75-sceneryx",
                "communityfs24-wildbill75-sceneryx"
            ]

            for pkg_name in packages_to_ensure:
                tag = f'<Package name="{pkg_name}"'
                if tag not in content_xml:
                    insert_marker = '</Packages>'
                    if insert_marker in content_xml:
                        new_entry = f'\t<Package name="{pkg_name}" active="Activated" />\n'
                        content_xml = content_xml.replace(insert_marker, new_entry + insert_marker)
                        print(f"  -> Added {pkg_name} to Content.xml")

            with open(CONTENT_XML_PATH, "w", encoding="utf-8") as f:
                f.write(content_xml)
            print("  -> Content.xml successfully updated and saved!")
        except Exception as e:
            print(f"  -> Note updating Content.xml: {e}")

    print("\n[SUCCESS] SceneryX In-Game Panel built and deployed cleanly!")


if __name__ == "__main__":
    build()
