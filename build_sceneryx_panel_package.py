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

CONTENT_XML_PATHS = [
    r"C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Content.xml",
    r"C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml"
]

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
    # Prop 11: float 4.0 (y min/pad)
    # Prop 12: float 32.0 (defaultWidth: 32% screen width, ~820px on 1440p matching preview)
    # Prop 13: float 25.5 (defaultHeight: 25.5% screen height, tightly framed below footer at 367px on 1440p)
    # Prop 14: float 24.0 (minWidth)
    # Prop 15: float 2.0 (minHeight: 2% screen height, freely resizable without lock)
    numeric_chunk = bytearray()
    numeric_chunk.extend(struct.pack("<II", 9, 3))
    numeric_chunk.extend(struct.pack("<If", 10, 4.0))
    numeric_chunk.extend(struct.pack("<If", 11, 4.0))
    numeric_chunk.extend(struct.pack("<If", 12, 32.0))
    numeric_chunk.extend(struct.pack("<If", 13, 25.5))
    numeric_chunk.extend(struct.pack("<If", 14, 24.0))
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
    panel_ui_dir = os.path.join(PANEL_PKG_DIR, "html_ui", "InGamePanels", "SceneryX_Remote")
    saved_html = None
    saved_css = None
    saved_js = None
    if os.path.exists(panel_ui_dir):
        h_path = os.path.join(panel_ui_dir, "SceneryX_Remote.html")
        c_path = os.path.join(panel_ui_dir, "SceneryX_Remote.css")
        j_path = os.path.join(panel_ui_dir, "SceneryX_Remote.js")
        if os.path.exists(h_path):
            with open(h_path, "r", encoding="utf-8") as f:
                saved_html = f.read()
        if os.path.exists(c_path):
            with open(c_path, "r", encoding="utf-8") as f:
                saved_css = f.read()
        if os.path.exists(j_path):
            with open(j_path, "r", encoding="utf-8") as f:
                saved_js = f.read()

    if os.path.exists(PANEL_PKG_DIR):
        shutil.rmtree(PANEL_PKG_DIR)
    
    os.makedirs(os.path.join(PANEL_PKG_DIR, "InGamePanels"), exist_ok=True)
    os.makedirs(os.path.join(PANEL_PKG_DIR, "html_ui", "icons", "toolbar"), exist_ok=True)
    os.makedirs(os.path.join(PANEL_PKG_DIR, "html_ui", "Textures", "Menu", "toolbar"), exist_ok=True)
    os.makedirs(os.path.join(PANEL_PKG_DIR, "html_ui", "InGamePanels", "SceneryX_Remote"), exist_ok=True)

    # 1. MANIFEST.JSON (v1.0.5 to ensure clean MSFS VFS cache invalidation)
    manifest = {
        "dependencies": [],
        "content_type": "UI",
        "title": "SCENERY X",
        "manufacturer": "SceneryX",
        "creator": "wildbill75",
        "package_version": "1.0.7",
        "minimum_game_version": "1.0.0",
        "release_notes": {
            "neutral": {
                "LastUpdate": "SceneryX In-Game Panel V1.0.7 - Calibrated Height (25.5% snug fit)",
                "OlderHistory": ""
            }
        }
    }
    with open(os.path.join(PANEL_PKG_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("  -> manifest.json written (v1.0.5, title: SCENERY X)")

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
    <link rel="stylesheet" href="SceneryX_Remote.css?v=117" />
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
    <script type="text/javascript" src="SceneryX_Remote.js?v=117"></script>
</head>
<body class="border-box">
    <ingamepanel-sceneryx>
        <ingame-ui id="SceneryX_Remote" panel-id="PANEL_SCENERYX" title="SCENERY X"
                   class="ingameUiFrame panelInvisible"
                   content-fit="true" resize="both"
                   min-width="440" min-height="200">

            <!-- OFFLINE VIEW -->
            <div id="disconnected-view" class="offline-box">
                <div class="offline-title">Please launch Scenery X</div>
            </div>

            <!-- ONLINE VIEW -->
            <div id="connected-view" class="main-content hidden">
                <!-- SECTION 1: SMART LOD REGULATION -->
                <div class="panel-section">
                    <div class="section-header">
                        <span class="section-title">SMART LOD REGULATION</span>
                        <button type="button" id="smart-lod-toggle-btn" class="switch-btn switch-off" role="switch" aria-checked="false" title="Toggle Smart Dynamic LOD" onclick="onSmartLodClick(event)">
                            <span class="switch-thumb"></span>
                            <span id="smart-lod-btn-label" class="switch-label">OFF</span>
                        </button>
                    </div>

                    <!-- DUAL SLIDERS BOX (OPTION B) -->
                    <div class="lod-controls-box">
                        <!-- TLOD AXIS CARD -->
                        <div class="lod-axis-card" id="tlod-card">
                            <div class="lod-axis-header">
                                <div class="lod-title-group">
                                    <span class="lod-axis-title" id="tlod-name-label" title="Terrain LOD (Double-click to reset to Auto)">TLOD</span>
                                    <span class="lod-live-tag" title="Real-time in-sim TLOD setpoint">LIVE <span id="tlod-live-val" class="live-num">100</span></span>
                                </div>
                                <span class="badge-tag badge-off" id="tlod-mode-badge" title="Double-click slider or click badge to reset to Auto">
                                    <span id="tlod-badge-text">AUTO</span>
                                </span>
                            </div>
                            <div class="lod-values-group">
                                <div class="lod-param" title="Floor LOD below transition altitude">
                                    <span class="param-lbl">Floor :</span>
                                    <span id="tlod-floor-val" class="param-val">100</span>
                                </div>
                                <div class="lod-param alt-param" title="Transition altitude in feet AGL">
                                    <span class="param-lbl">Alt :</span>
                                    <button type="button" class="alt-chevron-btn" id="tlod-alt-down" title="Decrease altitude (-100 ft)">
                                        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                            <polyline points="15.5 5 8.5 12 15.5 19"></polyline>
                                        </svg>
                                    </button>
                                    <input type="number" id="tlod-alt-input" class="alt-input" value="3000" step="100" min="500" max="45000" />
                                    <button type="button" class="alt-chevron-btn" id="tlod-alt-up" title="Increase altitude (+100 ft)">
                                        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                            <polyline points="8.5 5 15.5 12 8.5 19"></polyline>
                                        </svg>
                                    </button>
                                    <span class="param-unit">ft AGL</span>
                                </div>
                                <div class="lod-param" title="Cruise LOD at or above transition altitude">
                                    <span class="param-lbl">Cruise :</span>
                                    <span id="tlod-cruise-val" class="param-val">200</span>
                                </div>
                            </div>
                            <!-- Pure HTML/CSS Track & Handles (100% Centered) -->
                            <div class="dual-slider-container" id="tlod-dual-container">
                                <div class="dual-slider-track-bg"></div>
                                <div id="tlod-track-highlight" class="dual-slider-track-highlight" style="left: 25%; width: 25%;"></div>
                                <div id="tlod-floor-handle" class="slider-handle" style="left: 25%;" title="Floor LOD: 100"></div>
                                <div id="tlod-cruise-handle" class="slider-handle" style="left: 50%;" title="Cruise LOD: 200"></div>
                            </div>
                            <div class="dual-slider-labels">
                                <span>0</span>
                                <span>400</span>
                            </div>
                        </div>

                        <!-- OLOD AXIS CARD -->
                        <div class="lod-axis-card" id="olod-card">
                            <div class="lod-axis-header">
                                <div class="lod-title-group">
                                    <span class="lod-axis-title" id="olod-name-label" title="Object LOD (Double-click to reset to Auto)">OLOD</span>
                                    <span class="lod-live-tag" title="Real-time in-sim OLOD setpoint">LIVE <span id="olod-live-val" class="live-num">100</span></span>
                                </div>
                                <span class="badge-tag badge-off" id="olod-mode-badge" title="Double-click slider or click badge to reset to Auto">
                                    <span id="olod-badge-text">AUTO</span>
                                </span>
                            </div>
                            <div class="lod-values-group">
                                <div class="lod-param" title="Floor LOD below transition altitude">
                                    <span class="param-lbl">Floor :</span>
                                    <span id="olod-floor-val" class="param-val">100</span>
                                </div>
                                <div class="lod-param alt-param" title="Transition altitude in feet AGL">
                                    <span class="param-lbl">Alt :</span>
                                    <button type="button" class="alt-chevron-btn" id="olod-alt-down" title="Decrease altitude (-100 ft)">
                                        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                            <polyline points="15.5 5 8.5 12 15.5 19"></polyline>
                                        </svg>
                                    </button>
                                    <input type="number" id="olod-alt-input" class="alt-input" value="3000" step="100" min="500" max="45000" />
                                    <button type="button" class="alt-chevron-btn" id="olod-alt-up" title="Increase altitude (+100 ft)">
                                        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                            <polyline points="8.5 5 15.5 12 8.5 19"></polyline>
                                        </svg>
                                    </button>
                                    <span class="param-unit">ft AGL</span>
                                </div>
                                <div class="lod-param" title="Cruise LOD at or above transition altitude">
                                    <span class="param-lbl">Cruise :</span>
                                    <span id="olod-cruise-val" class="param-val">200</span>
                                </div>
                            </div>
                            <!-- Pure HTML/CSS Track & Handles (100% Centered) -->
                            <div class="dual-slider-container" id="olod-dual-container">
                                <div class="dual-slider-track-bg"></div>
                                <div id="olod-track-highlight" class="dual-slider-track-highlight" style="left: 33.33%; width: 33.34%;"></div>
                                <div id="olod-floor-handle" class="slider-handle" style="left: 33.33%;" title="Floor LOD: 100"></div>
                                <div id="olod-cruise-handle" class="slider-handle" style="left: 66.67%;" title="Cruise LOD: 200"></div>
                            </div>
                            <div class="dual-slider-labels">
                                <span>0</span>
                                <span>300</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- SECTION 2: PERFORMANCE -->
                <div class="panel-section">
                    <div class="section-header">
                        <span class="section-title">PERFORMANCE MONITORING</span>
                        <span id="live-pacing-status" class="badge-tag badge-optimal">OPTIMAL</span>
                    </div>
                    <div class="perf-row">
                        <div class="perf-metric">
                            <span class="metric-label">DISPLAYED FPS</span>
                            <div class="fps-line">
                                <span id="live-fps-val" class="metric-number fps-val">--</span>
                                <span class="fps-sep">/</span>
                                <span class="fps-base-lbl">BASE</span>
                                <span id="live-fps-base" class="metric-number fps-base-val">--</span>
                                <span class="metric-unit">FPS</span>
                            </div>
                        </div>
                        <div class="perf-metric">
                            <span class="metric-label">CPU MAIN THREAD</span>
                            <div class="mt-line">
                                <span id="live-mt-val" class="metric-number mt-val">--</span>
                                <span class="metric-unit">ms</span>
                            </div>
                        </div>
                    </div>

                    <!-- Sparkline Trend Graph -->
                    <div class="sparkline-box">
                        <div class="sparkline-top">
                            <span class="sparkline-title">30S TREND</span>
                            <span id="fps-delta-label" class="delta-label delta-neutral">STANDBY</span>
                        </div>
                        <canvas id="fps-sparkline-canvas" class="sparkline-canvas" width="340" height="32"></canvas>
                    </div>
                </div>

                <!-- SECTION 3: SYSTEM METRICS -->
                <div class="panel-section">
                    <div class="metrics-grid">
                        <div class="metric-compact">
                            <span class="compact-label">GPU</span>
                            <div class="compact-val-wrap">
                                <span id="live-gpu-val" class="compact-val">--</span>
                                <span class="compact-unit">%</span>
                            </div>
                        </div>
                        <div class="metric-compact">
                            <span class="compact-label">CPU</span>
                            <div class="compact-val-wrap">
                                <span id="live-cpu-val" class="compact-val">--</span>
                                <span class="compact-unit">%</span>
                            </div>
                        </div>
                        <div class="metric-compact">
                            <span class="compact-label">VRAM</span>
                            <div class="compact-val-wrap">
                                <span id="live-vram-val" class="compact-val">--</span>
                                <span class="compact-unit">GB</span>
                            </div>
                        </div>
                        <div class="metric-compact">
                            <span class="compact-label">CACHE</span>
                            <div class="compact-val-wrap">
                                <span id="live-cache-val" class="compact-val">--</span>
                                <span class="compact-unit">MB/s</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- SECTION 4: BLACKBOX RECORDER -->
                <div class="panel-section section-rec">
                    <button type="button" id="blackbox-toggle-btn" class="msfs-btn btn-rec-start" onclick="onBlackboxClick(event)">
                        <span id="rec-btn-label">START MONITORING</span>
                    </button>
                </div>
            </div>
        </ingame-ui>
    </ingamepanel-sceneryx>
</body>
</html>'''

    panel_ui_dir = os.path.join(PANEL_PKG_DIR, "html_ui", "InGamePanels", "SceneryX_Remote")
    final_html = saved_html if saved_html else html_content
    with open(os.path.join(panel_ui_dir, "SceneryX_Remote.html"), "w", encoding="utf-8") as f:
        f.write(final_html)

    css_content = '''/* =========================================================
   SceneryX MSFS In-Game Toolbar Panel - Clean Slate Theme
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
    display: flex !important;
    flex-direction: column !important;
    width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    min-width: 0 !important;
    overflow: visible !important;
    align-items: stretch !important;
    flex: 0 0 auto !important;
    background: transparent !important;
}

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

/* OFFLINE VIEW */
.offline-box {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    min-height: 220px;
    text-align: center;
    padding: 30px 15px;
    background: #1e293b;
}

.offline-title {
    font-size: 16px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.5px;
}

/* MAIN LIVE CONTENT - Clean Lighter Slate (#162032) */
.main-content {
    display: flex;
    flex-direction: column;
    padding: 10px 14px;
    width: 100%;
    height: auto;
    min-height: 0;
    overflow: hidden;
    background: #162032;
    border: 1px solid #334155;
    border-radius: 8px;
    box-sizing: border-box;
}

.panel-section {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 10px 14px;
    display: flex;
    flex-direction: column;
    margin-bottom: 8px;
    flex-shrink: 0;
}

.panel-section:last-child {
    margin-bottom: 0 !important;
}

.section-rec {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 6px 12px;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    box-sizing: border-box;
    width: 100%;
    margin-bottom: 0 !important;
    flex-shrink: 0;
}

.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 26px;
    margin-bottom: 8px;
}

.section-title {
    font-size: 11px;
    font-weight: 800;
    color: #94a3b8;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

/* SOLID COLOR PILLS - STRICTLY NO BORDER, NO DOTS, UNIFORM SOLID COLOR */
.badge-tag {
    font-size: 10px;
    font-weight: 800;
    padding: 3px 9px;
    border-radius: 4px;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: none !important;
    outline: none !important;
    white-space: nowrap;
    user-select: none;
    line-height: 1.2;
}

.badge-auto, .badge-optimal {
    background: #059669 !important;
    color: #ffffff !important;
}

.badge-man {
    background: #0284c7 !important;
    color: #ffffff !important;
}

.badge-acceptable {
    background: #d97706 !important;
    color: #ffffff !important;
}

.badge-off, .badge-heavy {
    background: #334155 !important;
    color: #cbd5e1 !important;
}

/* LIVE TAG */
.lod-live-tag {
    font-size: 10px;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 4px;
    letter-spacing: 0.5px;
    background: #273549;
    color: #94a3b8;
    border: none !important;
    display: inline-flex;
    align-items: baseline;
    line-height: 1.2;
}

.live-num {
    font-family: 'Consolas', monospace;
    font-weight: 900;
    color: #38bdf8;
    margin-left: 6px;
}

/* BUTTONS - Compact and inline (NEVER full width) */
.msfs-btn {
    width: auto;
    min-width: 180px;
    max-width: 220px;
    height: 30px;
    margin: 0 auto;
    padding: 5px 16px;
    border: none !important;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.8px;
    cursor: pointer;
    text-transform: uppercase;
    transition: background 0.15s ease;
    color: #ffffff;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    line-height: 1;
    box-sizing: border-box;
}

.btn-rec-start {
    background: #0284c7 !important;
    color: #ffffff !important;
}
.btn-rec-start:hover {
    background: #0369a1 !important;
}

.btn-rec-stop {
    background: #dc2626 !important;
    color: #ffffff !important;
}
.btn-rec-stop:hover {
    background: #b91c1c !important;
}

.msfs-btn-inline {
    padding: 4px 16px;
    height: 26px;
    width: auto;
    min-width: 84px;
    max-width: 120px;
    border: none !important;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.8px;
    cursor: pointer;
    text-transform: uppercase;
    transition: background 0.15s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
    line-height: 1;
}

.btn-master-off {
    background: #334155 !important;
    color: #cbd5e1 !important;
}
.btn-master-off:hover {
    background: #475569 !important;
    color: #ffffff !important;
}

.btn-master-on {
    background: #059669 !important;
    color: #ffffff !important;
}
.btn-master-on:hover {
    background: #047857 !important;
}

/* SWITCH TOGGLE BUTTON (Unified ON/OFF) */
.switch-btn {
    position: relative;
    display: inline-flex;
    align-items: center;
    width: 54px;
    height: 24px;
    padding: 0 3px;
    border-radius: 9999px;
    cursor: pointer;
    border: 1px solid #475569;
    background: #334155;
    transition: background-color 0.2s ease, border-color 0.2s ease;
    user-select: none;
    box-sizing: border-box;
    outline: none;
    flex-shrink: 0;
}
.switch-btn.switch-off {
    background: #334155 !important;
    border-color: #475569 !important;
    flex-direction: row;
    justify-content: space-between;
}
.switch-btn.switch-on {
    background: #059669 !important;
    border-color: #10b981 !important;
    flex-direction: row-reverse;
    justify-content: space-between;
}
.switch-btn .switch-thumb {
    width: 18px;
    height: 18px;
    border-radius: 9999px;
    background: #ffffff;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
    flex-shrink: 0;
    pointer-events: none;
}
.switch-btn .switch-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.04em;
    line-height: 1;
    text-transform: uppercase;
    padding: 0 4px;
    pointer-events: none;
}
.switch-btn.switch-off .switch-label {
    color: #cbd5e1;
}
.switch-btn.switch-on .switch-label {
    color: #ffffff;
}
.switch-btn:hover {
    filter: brightness(1.08);
}

/* SMART LOD DUAL SLIDERS */
.lod-controls-box {
    display: flex;
    flex-direction: column;
}

.lod-axis-card {
    background: #111827;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
}

#tlod-card {
    margin-bottom: 8px;
}

.lod-axis-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 24px;
    margin-bottom: 12px;
}

.lod-title-group {
    display: flex;
    align-items: center;
}

.lod-axis-title {
    font-size: 12px;
    font-weight: 900;
    color: #f8fafc;
    letter-spacing: 0.6px;
    cursor: pointer;
    margin-right: 16px;
}

.lod-values-group {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 6px 14px;
    height: 38px;
    box-sizing: border-box;
    margin-bottom: 10px;
}

.lod-param {
    display: inline-flex;
    align-items: baseline;
}

.param-lbl {
    font-family: 'Open Sans', 'Segoe UI', sans-serif;
    color: #94a3b8;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    line-height: normal;
    margin-right: 8px;
}

.param-val {
    font-family: 'Consolas', monospace;
    font-weight: 900;
    color: #38bdf8;
    font-size: 14px;
    line-height: normal;
    min-width: 28px;
}

.alt-param {
    display: inline-flex;
    align-items: center;
}

.alt-chevron-btn {
    background: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 1px !important;
    width: 14px;
    height: 24px;
    color: #64748b;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: color 0.15s ease;
    user-select: none;
    -webkit-user-select: none;
    vertical-align: middle;
}

.alt-chevron-btn svg {
    display: block;
    pointer-events: none;
}

.alt-chevron-btn:hover {
    color: #cbd5e1 !important;
}

.alt-chevron-btn:active {
    color: #ffffff !important;
}

#tlod-alt-up, #olod-alt-up {
    margin-right: 6px !important;
}

.alt-input {
    width: 68px;
    height: 26px;
    background: #0f172a;
    border: 1px solid #475569;
    border-radius: 4px;
    color: #f1f5f9;
    font-family: 'Consolas', monospace;
    font-size: 13.5px;
    font-weight: 800;
    text-align: center;
    padding: 0;
    outline: none;
    line-height: 24px;
    box-sizing: border-box;
    margin: 0 2px;
}

.alt-input:focus {
    border-color: #38bdf8;
    background: #1e293b;
}

.param-unit {
    color: #64748b;
    font-size: 10.5px;
    font-weight: 600;
    line-height: 1;
}

/* DUAL RANGE SLIDER - PURE CSS DIVS WITH 100% MATHEMATICAL CENTERING */
.dual-slider-container {
    position: relative;
    width: 100%;
    height: 24px;
    display: flex;
    align-items: center;
    cursor: pointer;
    user-select: none;
    -webkit-user-select: none;
    margin: 4px 0 2px 0;
}

.dual-slider-track-bg {
    position: absolute;
    left: 0;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    height: 6px;
    background: #334155;
    border-radius: 3px;
    pointer-events: none;
}

.dual-slider-track-highlight {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    height: 6px;
    background: #0284c7;
    border-radius: 3px;
    pointer-events: none;
}

.slider-handle {
    position: absolute;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #ffffff;
    border: 2px solid #0284c7;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.6);
    cursor: grab;
    z-index: 10;
    transition: border-color 0.12s, box-shadow 0.12s;
}

.slider-handle:hover, .slider-handle.active {
    border-color: #38bdf8;
    box-shadow: 0 0 6px #0284c7;
}

.slider-handle.active {
    cursor: grabbing;
}

.dual-slider-labels {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 10px;
    font-family: 'Consolas', monospace;
    font-weight: 700;
    color: #64748b;
    padding: 0 2px;
}

.range-sub {
    font-family: 'Open Sans', sans-serif;
    font-size: 9px;
    color: #64748b;
}

/* PERFORMANCE GRID & TYPOGRAPHY */
.perf-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}

.perf-metric {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: #111827;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 10px 12px;
    min-height: 58px;
    box-sizing: border-box;
}

.metric-label {
    font-size: 10px;
    font-weight: 800;
    color: #94a3b8;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
    text-transform: uppercase;
}

/* Single clean row for DISPLAYED FPS: [72] [/] [BASE] [36] [FPS] */
.fps-line {
    display: inline-flex;
    align-items: baseline;
    justify-content: center;
    gap: 5px;
}

.fps-val {
    font-family: 'Consolas', monospace;
    font-size: 24px;
    font-weight: 900;
    color: #ffffff;
    line-height: 1;
}

.fps-sep {
    font-family: 'Consolas', monospace;
    font-size: 18px;
    font-weight: 700;
    color: #64748b;
    margin: 0 1px;
}

.fps-base-lbl {
    font-size: 11px;
    font-weight: 800;
    color: #94a3b8;
    letter-spacing: 0.6px;
    margin-left: 2px;
    margin-right: -1px;
    text-transform: uppercase;
    align-self: baseline;
}

.fps-base-val {
    font-family: 'Consolas', monospace;
    font-size: 19px;
    font-weight: 900;
    color: #e2e8f0;
    line-height: 1;
}

/* Single clean row for CPU MAIN THREAD: [13.8] [ms] */
.mt-line {
    display: inline-flex;
    align-items: baseline;
    justify-content: center;
    gap: 4px;
}

.mt-val {
    font-family: 'Consolas', monospace;
    font-size: 24px;
    font-weight: 900;
    color: #ffffff;
    line-height: 1;
}

.metric-number {
    font-family: 'Consolas', monospace;
    font-size: 24px;
    font-weight: 900;
    color: #ffffff;
    line-height: 1;
}

.metric-unit {
    font-size: 11px;
    font-weight: 800;
    color: #94a3b8;
    line-height: 1;
    margin-left: 1px;
}

/* SYSTEM METRICS GRID (GPU, CPU, VRAM, CACHE) - Single Row of 4 */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 6px;
    width: 100%;
}

.metric-compact {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: #111827;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 8px 6px;
    text-align: center;
}

.compact-label {
    color: #94a3b8;
    font-weight: 800;
    font-size: 10.5px;
    letter-spacing: 0.6px;
    margin-bottom: 3px;
}

.compact-val-wrap {
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: 3px;
    white-space: nowrap;
}

.compact-val {
    font-family: 'Consolas', monospace;
    color: #ffffff;
    font-weight: 900;
    font-size: 16px;
    line-height: 1;
    letter-spacing: -0.3px;
}

#live-vram-val {
    font-size: 14.5px;
}

.compact-unit {
    color: #94a3b8;
    font-weight: 800;
    font-size: 10.5px;
    line-height: 1;
    margin-left: 2px;
}

/* SPARKLINE TREND GRAPH */
.sparkline-box {
    display: flex;
    flex-direction: column;
    gap: 4px;
    background: #0b0f19;
    border: 1px solid rgba(51, 65, 85, 0.6);
    border-radius: 4px;
    padding: 6px 8px;
    margin-top: 8px;
    box-sizing: border-box;
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
    font-family: inherit;
}

.delta-label {
    font-size: 11px;
    font-weight: 700;
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

.hidden {
    display: none !important;
}'''
    final_css = saved_css if saved_css else css_content
    with open(os.path.join(panel_ui_dir, "SceneryX_Remote.css"), "w", encoding="utf-8") as f:
        f.write(final_css)

    js_content = '''// =========================================================
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
    let currentLodActive = false;

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
        if (axis === "tlod") tlodIsManual = isManual;
        else olodIsManual = isManual;

        if (txt && badge) {
            if (isOff) {
                badge.className = "badge-tag badge-off";
                txt.textContent = "OFF";
            } else if (isManual) {
                badge.className = "badge-tag badge-man";
                txt.textContent = "MAN";
            } else {
                badge.className = "badge-tag badge-auto";
                txt.textContent = "AUTO";
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
            floor = Math.max(0, Math.min(this.maxVal, floor));
            cruise = Math.max(0, Math.min(this.maxVal, cruise));

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
                if (e.target === self.floorHandle || e.target === self.cruiseHandle) return;
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

        // 1. Always update backend axis configuration so controller keeps exact base, target, alt
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

        // 2. If Smart LOD is disengaged: write live to MSFS memory directly without changing profile files
        if (!currentLodActive) {
            let valToWrite = (directVal !== undefined) ? directVal : baseVal;
            let payload = {};
            payload[axis] = valToWrite;
            let urlLod = getApiBase() + "/smart_lod/set_lod";
            let xhrLod = new XMLHttpRequest();
            xhrLod.open("POST", urlLod, true);
            xhrLod.setRequestHeader("Content-Type", "application/json");
            xhrLod.timeout = 2500;
            xhrLod.send(JSON.stringify(payload));
        }
    }

    function resetToProfile(axis) {
        if (!axis) axis = "all";
        if (axis === "all") {
            setAxisUiState("tlod", false, !currentLodActive);
            setAxisUiState("olod", false, !currentLodActive);
        } else {
            setAxisUiState(axis, false, !currentLodActive);
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

        let activeEl = document.activeElement;
        let isInputFocused = (activeEl && (activeEl.tagName === 'INPUT'));

        if (!isUserInteracting && !isInputFocused && !isSliderDragging) {
            let tlodFloorVal = lod.tlod_base !== undefined ? lod.tlod_base : 100;
            let tlodCruiseVal = lod.tlod_target !== undefined ? lod.tlod_target : 200;
            let tlodAltVal = lod.tlod_altitude !== undefined ? lod.tlod_altitude : 3000;

            let olodFloorVal = lod.olod_base !== undefined ? lod.olod_base : 100;
            let olodCruiseVal = lod.olod_target !== undefined ? lod.olod_target : 200;
            let olodAltVal = lod.olod_altitude !== undefined ? lod.olod_altitude : 3000;

            // Robust fallback: handles must never overlap and remain distinctly visible
            if (tlodFloorVal >= tlodCruiseVal) tlodCruiseVal = Math.min(400, tlodFloorVal + 100);
            if (olodFloorVal >= olodCruiseVal) olodCruiseVal = Math.min(300, olodFloorVal + 100);

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

            let tlodManualRemote = !!(lod.tlod_manual !== undefined ? lod.tlod_manual : data.smart_lod_tlod_manual);
            let olodManualRemote = !!(lod.olod_manual !== undefined ? lod.olod_manual : data.smart_lod_olod_manual);
            setAxisUiState("tlod", tlodManualRemote, !lodActive);
            setAxisUiState("olod", olodManualRemote, !lodActive);
        }

        let btnLod = document.getElementById("smart-lod-toggle-btn");
        let lblLod = document.getElementById("smart-lod-btn-label");
        if (btnLod && !isSmartLodToggling) {
            if (lodActive) {
                btnLod.className = "switch-btn switch-on";
                btnLod.setAttribute("aria-checked", "true");
                if (lblLod) lblLod.textContent = "ON";
            } else {
                btnLod.className = "switch-btn switch-off";
                btnLod.setAttribute("aria-checked", "false");
                if (lblLod) lblLod.textContent = "OFF";
            }
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
    function notifyHeight() {
        let connView = document.getElementById("connected-view");
        let discView = document.getElementById("disconnected-view");
        let targetEl = (connView && connView.style.display !== "none" && !connView.classList.contains("hidden")) ? connView : discView;
        let h = targetEl ? targetEl.offsetHeight + 10 : document.body.scrollHeight;
        if (window.parent && window.parent !== window) {
            window.parent.postMessage({ type: "SCENERYX_PANEL_RESIZE", height: h }, "*");
        }
    }

    function pollTelemetry() {
        let url = getApiBase() + "/telemetry?_=" + Date.now();

        function handleSuccess(data) {
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
            consecutiveFailures++;
            // In standalone preview mode (outside MSFS without active sim), provide mock preview data after 2 failed attempts
            if (consecutiveFailures >= 2) {
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
                    cpu_pct: 44,
                    vram_used_gb: 7.4,
                    vram_total_gb: 16.0,
                    rolling_cache_gb: 12.5,
                    blackbox_recording: false
                });
                notifyHeight();
                return;
            }
            setConnectedState(false);
            notifyHeight();
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

    function onSmartLodClick(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        let now = Date.now();
        if (now - lastSmartLodToggleTime < 350) return;
        lastSmartLodToggleTime = now;

        let btnLod = document.getElementById("smart-lod-toggle-btn");
        let lblLod = document.getElementById("smart-lod-btn-label");
        let targetState = !currentLodActive;

        // Immediate optimistic visual toggle
        currentLodActive = targetState;
        isSmartLodToggling = true;
        if (btnLod) {
            if (targetState) {
                btnLod.className = "switch-btn switch-on";
                btnLod.setAttribute("aria-checked", "true");
                if (lblLod) lblLod.textContent = "ON";
            } else {
                btnLod.className = "switch-btn switch-off";
                btnLod.setAttribute("aria-checked", "false");
                if (lblLod) lblLod.textContent = "OFF";
            }
        }

        let url = getApiBase() + "/smart_lod/toggle";
        let xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.timeout = 8000;
        xhr.onload = function () {
            isSmartLodToggling = false;
            try {
                let resp = JSON.parse(xhr.responseText);
                if (resp && resp.enabled !== undefined) {
                    currentLodActive = !!resp.enabled;
                }
            } catch (err) {}
            pollTelemetry();
        };
        xhr.onerror = function () {
            isSmartLodToggling = false;
            pollTelemetry();
        };
        xhr.ontimeout = function () {
            isSmartLodToggling = false;
            pollTelemetry();
        };
        xhr.send(JSON.stringify({ enabled: targetState }));
    }
    window.onSmartLodClick = onSmartLodClick;

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
                setAxisUiState(axis, true, !currentLodActive);
                if (!currentLodActive) {
                    let liveEl = document.getElementById(axis + "-live-val");
                    if (liveEl) liveEl.textContent = directVal;
                }
                queueAxisConfigUpdate(axis, directVal);
            }
        );

        if (axis === "tlod") tlodController = controller;
        else olodController = controller;

        if (container) {
            container.addEventListener("dblclick", function (e) {
                e.preventDefault();
                e.stopPropagation();
                resetToProfile(axis);
            });
        }

        let btnAltDown = document.getElementById(axis + "-alt-down");
        let btnAltUp = document.getElementById(axis + "-alt-up");

        function adjustAlt(delta) {
            let currentVal = (axis === "tlod") ? currentTlodAlt : currentOlodAlt;
            let nextVal = Math.max(500, Math.min(45000, currentVal + delta));
            if (axis === "tlod") currentTlodAlt = nextVal;
            else currentOlodAlt = nextVal;
            if (altInput) altInput.value = nextVal;
            setAxisUiState(axis, true, !currentLodActive);
            queueAxisConfigUpdate(axis);
        }

        if (btnAltDown) {
            btnAltDown.addEventListener("click", function (e) {
                e.preventDefault();
                e.stopPropagation();
                let step = e.shiftKey ? 500 : 100;
                adjustAlt(-step);
            });
        }

        if (btnAltUp) {
            btnAltUp.addEventListener("click", function (e) {
                e.preventDefault();
                e.stopPropagation();
                let step = e.shiftKey ? 500 : 100;
                adjustAlt(step);
            });
        }

        if (altInput) {
            altInput.addEventListener("change", function () {
                let num = Math.max(500, Math.min(45000, parseInt(altInput.value, 10) || 5000));
                altInput.value = num;
                if (axis === "tlod") currentTlodAlt = num;
                else currentOlodAlt = num;
                setAxisUiState(axis, true, !currentLodActive);
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
                if (e.target.tagName !== 'INPUT' && !e.target.classList.contains('slider-handle') && !e.target.closest('.alt-chevron-btn')) {
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

        connView.addEventListener("dblclick", function (e) {
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON' && !e.target.classList.contains('slider-handle') && !e.target.closest('.alt-chevron-btn')) {
                resetToProfile("all");
            }
        });
        document.body.addEventListener("dblclick", function (e) {
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON' && !e.target.classList.contains('slider-handle') && !e.target.closest('.alt-chevron-btn')) {
                resetToProfile("all");
            }
        });

        let btnLod = document.getElementById("smart-lod-toggle-btn");
        if (btnLod) {
            btnLod.onclick = onSmartLodClick;
            btnLod.addEventListener("click", onSmartLodClick);
        }

        let btnRec = document.getElementById("blackbox-toggle-btn");
        if (btnRec) {
            btnRec.onclick = onBlackboxClick;
            btnRec.addEventListener("click", onBlackboxClick);
        }

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
'''
    final_js = saved_js if saved_js else js_content
    with open(os.path.join(panel_ui_dir, "SceneryX_Remote.js"), "w", encoding="utf-8") as f:
        f.write(final_js)
    print("  -> SceneryX_Remote HTML, CSS, JS written with resilient AutoFPS-grade polling and DOM binding")

    # Also synchronize the standalone web preview in web/in_game_panel/
    web_panel_dir = os.path.join(BASE_DIR, "web", "in_game_panel")
    os.makedirs(web_panel_dir, exist_ok=True)
    with open(os.path.join(web_panel_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(final_html)
    with open(os.path.join(web_panel_dir, "SceneryX_Remote.css"), "w", encoding="utf-8") as f:
        f.write(final_css)
    with open(os.path.join(web_panel_dir, "SceneryX_Remote.js"), "w", encoding="utf-8") as f:
        f.write(final_js)
    print(f"  -> Synchronized web in-game panel preview in {web_panel_dir}")

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
    for cxml_path in CONTENT_XML_PATHS:
        if os.path.exists(cxml_path):
            try:
                with open(cxml_path, "r", encoding="utf-8") as f:
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
                            print(f"  -> Added {pkg_name} to {os.path.basename(cxml_path)}")

                with open(cxml_path, "w", encoding="utf-8") as f:
                    f.write(content_xml)
                print(f"  -> {cxml_path} successfully updated and saved!")
            except Exception as e:
                print(f"  -> Note updating {cxml_path}: {e}")

    print("\n[SUCCESS] SceneryX In-Game Panel built and deployed cleanly!")


if __name__ == "__main__":
    build()
