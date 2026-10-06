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
    # Prop 12: float 36.0 (defaultWidth: 36% screen width)
    # Prop 13: float 34.0 (defaultHeight: 34% screen height - generous room for dual sliders and telemetry)
    # Prop 14: float 26.0 (minWidth)
    # Prop 15: float 2.0 (minHeight - allows clean compact fitting)
    numeric_chunk = bytearray()
    numeric_chunk.extend(struct.pack("<II", 9, 3))
    numeric_chunk.extend(struct.pack("<If", 10, 4.0))
    numeric_chunk.extend(struct.pack("<If", 11, 5.0))
    numeric_chunk.extend(struct.pack("<If", 12, 36.0))
    numeric_chunk.extend(struct.pack("<If", 13, 34.0))
    numeric_chunk.extend(struct.pack("<If", 14, 26.0))
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
                   min-width="380" min-height="340">

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
                        <button type="button" id="smart-lod-toggle-btn" class="msfs-btn-inline btn-primary">
                            <span id="smart-lod-btn-label">ENGAGE</span>
                        </button>
                    </div>

                    <!-- DUAL SLIDERS BOX (OPTION B) -->
                    <div class="lod-controls-box">
                        <!-- TLOD AXIS CARD -->
                        <div class="lod-axis-card" id="tlod-card">
                            <div class="lod-axis-header">
                                <div class="lod-title-group">
                                    <span class="lod-axis-title" id="tlod-name-label" title="Terrain LOD (Double-click to reset to Auto)">TLOD</span>
                                    <span class="lod-live-tag" title="Real-time in-sim TLOD setpoint">LIVE: <span id="tlod-live-val" class="live-num">100</span></span>
                                </div>
                                <span class="badge-tag tag-neutral" id="tlod-mode-badge" title="Double-click slider or click badge to reset to Auto">
                                    <span id="tlod-badge-text">AUTO</span>
                                </span>
                            </div>
                            <div class="lod-values-group">
                                <div class="lod-param" title="Floor LOD below transition altitude">
                                    <span class="param-lbl">Floor:</span>
                                    <span id="tlod-floor-val" class="param-val">100</span>
                                </div>
                                <div class="lod-param alt-param" title="Transition altitude in feet AGL">
                                    <span class="param-lbl">Alt:</span>
                                    <input type="number" id="tlod-alt-input" class="alt-input" value="5000" step="500" min="500" max="45000" />
                                    <span class="param-unit">ft AGL</span>
                                </div>
                                <div class="lod-param" title="Cruise LOD at or above transition altitude">
                                    <span class="param-lbl">Cruise:</span>
                                    <span id="tlod-cruise-val" class="param-val">200</span>
                                </div>
                            </div>
                            <!-- Track Container -->
                            <div class="dual-slider-container" id="tlod-dual-container">
                                <div class="dual-slider-track-bg"></div>
                                <div id="tlod-track-highlight" class="dual-slider-track-highlight"></div>
                                <input type="range" class="dual-slider-input" id="tlod-floor-range" min="0" max="400" step="5" value="100" title="Floor LOD: 100" />
                                <input type="range" class="dual-slider-input" id="tlod-cruise-range" min="0" max="400" step="5" value="200" title="Cruise LOD: 200" />
                            </div>
                            <div class="dual-slider-labels">
                                <span>0</span>
                                <span class="range-sub">Dynamic Range (Floor to Cruise)</span>
                                <span>400</span>
                            </div>
                        </div>

                        <!-- OLOD AXIS CARD -->
                        <div class="lod-axis-card" id="olod-card">
                            <div class="lod-axis-header">
                                <div class="lod-title-group">
                                    <span class="lod-axis-title" id="olod-name-label" title="Object LOD (Double-click to reset to Auto)">OLOD</span>
                                    <span class="lod-live-tag" title="Real-time in-sim OLOD setpoint">LIVE: <span id="olod-live-val" class="live-num">100</span></span>
                                </div>
                                <span class="badge-tag tag-neutral" id="olod-mode-badge" title="Double-click slider or click badge to reset to Auto">
                                    <span id="olod-badge-text">AUTO</span>
                                </span>
                            </div>
                            <div class="lod-values-group">
                                <div class="lod-param" title="Floor LOD below transition altitude">
                                    <span class="param-lbl">Floor:</span>
                                    <span id="olod-floor-val" class="param-val">100</span>
                                </div>
                                <div class="lod-param alt-param" title="Transition altitude in feet AGL">
                                    <span class="param-lbl">Alt:</span>
                                    <input type="number" id="olod-alt-input" class="alt-input" value="3000" step="500" min="500" max="45000" />
                                    <span class="param-unit">ft AGL</span>
                                </div>
                                <div class="lod-param" title="Cruise LOD at or above transition altitude">
                                    <span class="param-lbl">Cruise:</span>
                                    <span id="olod-cruise-val" class="param-val">100</span>
                                </div>
                            </div>
                            <!-- Track Container -->
                            <div class="dual-slider-container" id="olod-dual-container">
                                <div class="dual-slider-track-bg"></div>
                                <div id="olod-track-highlight" class="dual-slider-track-highlight"></div>
                                <input type="range" class="dual-slider-input" id="olod-floor-range" min="0" max="300" step="5" value="100" title="Floor LOD: 100" />
                                <input type="range" class="dual-slider-input" id="olod-cruise-range" min="0" max="300" step="5" value="100" title="Cruise LOD: 100" />
                            </div>
                            <div class="dual-slider-labels">
                                <span>0</span>
                                <span class="range-sub">Dynamic Range (Floor to Cruise)</span>
                                <span>300</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- SECTION 2: PERFORMANCE -->
                <div class="panel-section">
                    <div class="section-header">
                        <span class="section-title">PERFORMANCE MONITORING</span>
                        <span id="live-pacing-status" class="badge-tag tag-neutral">
                            <span id="pacing-badge-text">OPTIMAL</span>
                        </span>
                    </div>
                    <div class="perf-row">
                        <div class="perf-metric">
                            <span class="metric-label">DISPLAYED FPS</span>
                            <div class="metric-val-wrap">
                                <span id="live-fps-val" class="metric-number">--</span>
                                <span class="metric-unit">FPS</span>
                            </div>
                            <div id="live-fps-base-wrap" class="metric-base-badge" title="Native Frame Rate without Frame Generation">
                                <span class="base-label">BASE</span>
                                <span id="live-fps-base" class="base-val">--</span>
                                <span class="base-unit">FPS</span>
                            </div>
                        </div>
                        <div class="perf-metric">
                            <span class="metric-label">CPU MAIN THREAD</span>
                            <div class="metric-val-wrap">
                                <span id="live-mt-val" class="metric-number">--</span>
                                <span class="metric-unit">ms</span>
                            </div>
                            <div class="metric-base-badge metric-frametime-badge">
                                <span class="base-label">FRAMETIME</span>
                            </div>
                        </div>
                    </div>
                    <!-- Sparkline -->
                    <div class="sparkline-box">
                        <div class="sparkline-top">
                            <span class="sparkline-title">30S TREND</span>
                            <span id="fps-delta-label" class="delta-label delta-neutral">0 FPS</span>
                        </div>
                        <canvas id="fps-sparkline-canvas" class="sparkline-canvas" width="340" height="32"></canvas>
                    </div>
                </div>

                <!-- SECTION 3: SYSTEM METRICS -->
                <div class="panel-section">
                    <div class="metrics-grid">
                        <div class="metric-compact">
                            <span class="compact-label">GPU:</span>
                            <span id="live-gpu-val" class="compact-val">--</span>
                            <span class="compact-unit">%</span>
                        </div>
                        <div class="metric-compact">
                            <span class="compact-label">CPU:</span>
                            <span id="live-cpu-val" class="compact-val">--</span>
                            <span class="compact-unit">%</span>
                        </div>
                        <div class="metric-compact">
                            <span class="compact-label">VRAM:</span>
                            <span id="live-vram-val" class="compact-val">--</span>
                            <span class="compact-unit">GB</span>
                        </div>
                        <div class="metric-compact">
                            <span class="compact-label">CACHE:</span>
                            <span id="live-cache-val" class="compact-val">--</span>
                            <span class="compact-unit">MB/s</span>
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
   SceneryX MSFS In-Game Toolbar Panel - Native Theme
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
    gap: 11px;
    padding: 12px 14px 16px 14px;
    width: 100%;
    min-height: 100%;
    background: #020617;
    border: 1px solid rgba(51, 65, 85, 0.85);
    border-radius: 8px;
    box-sizing: border-box;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
}

.panel-section {
    background: rgba(15, 23, 42, 0.92);
    border: 1px solid rgba(51, 65, 85, 0.6);
    border-radius: 6px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
}

.section-rec {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 6px 10px;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(51, 65, 85, 0.5);
    border-radius: 6px;
    box-sizing: border-box;
    width: 100%;
}

.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.section-title {
    font-size: 11px;
    font-weight: 800;
    color: #94a3b8;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

/* STATUS PILLS & BADGES - Clean text badges without dots */
.badge-tag {
    font-size: 10px;
    font-weight: 800;
    padding: 2.5px 7px;
    border-radius: 4px;
    letter-spacing: 0.5px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    white-space: nowrap;
    user-select: none;
    transition: all 0.15s ease;
    line-height: 1;
}

.tag-neutral {
    background: #1e293b;
    border: 1px solid rgba(51, 65, 85, 0.6);
    color: #cbd5e1;
}

.tag-amber {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid rgba(245, 158, 11, 0.5);
    color: #fbbf24;
}

.tag-green {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.5);
    color: #34d399;
}

.tag-red {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.5);
    color: #f87171;
}

.pill-dot, .base-dot {
    display: none !important;
}

/* BUTTONS */
.msfs-btn {
    width: 100%;
    min-height: 28px;
    margin: 0 auto;
    padding: 6px 16px;
    border: none;
    border-radius: 4px;
    font-size: 11px;
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
    line-height: 1;
    box-sizing: border-box;
}

.msfs-btn-inline {
    padding: 3px 12px;
    border: none;
    border-radius: 4px;
    font-size: 10.5px;
    font-weight: 800;
    letter-spacing: 0.6px;
    cursor: pointer;
    text-transform: uppercase;
    transition: background 0.15s ease;
    color: #ffffff;
    display: inline-flex;
    align-items: center;
    justify-content: center;
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

/* SMART LOD DUAL SLIDERS (OPTION B) */
.lod-controls-box {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 1px;
}

.lod-axis-card {
    background: rgba(11, 15, 25, 0.75);
    border: 1px solid rgba(51, 65, 85, 0.5);
    border-radius: 6px;
    padding: 8px 10px 7px 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.lod-axis-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.lod-title-group {
    display: flex;
    align-items: center;
    gap: 6px;
}

.lod-axis-title {
    font-size: 12px;
    font-weight: 900;
    color: #f8fafc;
    letter-spacing: 0.6px;
    cursor: pointer;
}

.lod-live-tag {
    font-size: 10px;
    font-weight: 700;
    color: #64748b;
    background: rgba(30, 41, 59, 0.7);
    padding: 1px 5px;
    border-radius: 3px;
    border: 1px solid rgba(51, 65, 85, 0.4);
}

.live-num {
    font-family: 'Consolas', monospace;
    font-weight: 900;
    color: #38bdf8;
}

.lod-values-group {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(15, 23, 42, 0.55);
    border: 1px solid rgba(51, 65, 85, 0.4);
    border-radius: 4px;
    padding: 4px 8px;
}

.lod-param {
    display: flex;
    align-items: center;
    gap: 5px;
}

.param-lbl {
    color: #94a3b8;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.2px;
}

.param-val {
    font-family: 'Consolas', monospace;
    font-weight: 900;
    color: #38bdf8;
    font-size: 12px;
    min-width: 24px;
}

.alt-param {
    display: flex;
    align-items: center;
    gap: 4px;
}

.alt-input {
    width: 52px;
    background: #0b0f19;
    border: 1px solid rgba(51, 65, 85, 0.8);
    border-radius: 3px;
    color: #f1f5f9;
    font-family: 'Consolas', monospace;
    font-size: 11px;
    font-weight: 700;
    text-align: center;
    padding: 2px 3px;
    outline: none;
}

.alt-input:focus {
    border-color: #94a3b8;
    background: #1e293b;
}

.param-unit {
    color: #64748b;
    font-size: 10px;
    font-weight: 600;
}

/* DUAL RANGE SLIDER CONTAINER & THUMBS */
.dual-slider-container {
    position: relative;
    width: 100%;
    height: 20px;
    display: flex;
    align-items: center;
}

.dual-slider-track-bg {
    position: absolute;
    left: 0;
    top: 7px;
    width: 100%;
    height: 6px;
    background: #1e293b;
    border-radius: 3px;
    pointer-events: none;
    z-index: 0;
}

.dual-slider-track-highlight {
    position: absolute;
    top: 7px;
    height: 6px;
    background: #0284c7;
    border-radius: 3px;
    pointer-events: none;
    z-index: 1;
    transition: left 0.04s ease, width 0.04s ease;
}

.dual-slider-input {
    position: absolute;
    left: 0;
    top: 7px;
    width: 100%;
    height: 6px;
    margin: 0;
    padding: 0;
    background: transparent !important;
    background-color: transparent !important;
    -webkit-appearance: none !important;
    appearance: none !important;
    pointer-events: none;
    outline: none !important;
    border: none !important;
    box-shadow: none !important;
}

.dual-slider-input::-webkit-slider-runnable-track {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    height: 6px !important;
    -webkit-appearance: none !important;
    cursor: pointer;
}

.dual-slider-input::-moz-range-track {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    height: 6px !important;
    cursor: pointer;
}

.dual-slider-input::-webkit-slider-thumb {
    pointer-events: auto !important;
    cursor: pointer !important;
    -webkit-appearance: none !important;
    appearance: none !important;
    width: 16px !important;
    height: 16px !important;
    margin-top: -5px !important;
    border-radius: 50% !important;
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 2px solid #0284c7 !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.6) !important;
    transition: transform 0.1s ease, border-color 0.1s ease !important;
    opacity: 1 !important;
}

.dual-slider-input::-moz-range-thumb {
    pointer-events: auto !important;
    cursor: pointer !important;
    width: 16px !important;
    height: 16px !important;
    border-radius: 50% !important;
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 2px solid #0284c7 !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.6) !important;
    transition: transform 0.1s ease, border-color 0.1s ease !important;
    opacity: 1 !important;
}

.dual-slider-input:hover::-webkit-slider-thumb,
.dual-slider-input:focus::-webkit-slider-thumb {
    transform: scale(1.15) !important;
    border-color: #38bdf8 !important;
    background: #ffffff !important;
    background-color: #ffffff !important;
    opacity: 1 !important;
}

.dual-slider-input:hover::-moz-range-thumb,
.dual-slider-input:focus::-moz-range-thumb {
    transform: scale(1.15) !important;
    border-color: #38bdf8 !important;
    background: #ffffff !important;
    background-color: #ffffff !important;
    opacity: 1 !important;
}

.dual-slider-input:active::-webkit-slider-thumb {
    transform: scale(1.2) !important;
    border-color: #0ea5e9 !important;
    background: #ffffff !important;
    background-color: #ffffff !important;
    opacity: 1 !important;
}

.dual-slider-input:active::-moz-range-thumb {
    transform: scale(1.2) !important;
    border-color: #0ea5e9 !important;
    background: #ffffff !important;
    background-color: #ffffff !important;
    opacity: 1 !important;
}

.dual-slider-labels {
    display: flex;
    justify-content: space-between;
    font-size: 9.5px;
    font-family: 'Consolas', monospace;
    color: #64748b;
    padding: 0 2px;
}

.range-sub {
    font-family: 'Open Sans', sans-serif;
    font-size: 9px;
    color: #475569;
}

/* PERFORMANCE GRID & TYPOGRAPHY */
.perf-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}

.perf-metric {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: rgba(10, 14, 22, 0.7);
    border: 1px solid rgba(51, 65, 85, 0.4);
    border-radius: 5px;
    padding: 7px 10px 8px 10px;
}

.metric-label {
    font-size: 10.5px;
    font-weight: 800;
    color: #94a3b8;
    letter-spacing: 0.6px;
    margin-bottom: 2px;
}

.metric-val-wrap {
    display: flex;
    align-items: baseline;
    gap: 6px;
}

.metric-number {
    font-family: 'Consolas', monospace;
    font-size: 28px;
    font-weight: 900;
    color: #ffffff;
    line-height: 1;
}

.metric-unit {
    font-size: 12px;
    font-weight: 800;
    color: #94a3b8;
}

/* PROMINENT BASE FPS PILL */
.metric-base-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(30, 41, 59, 0.85);
    border: 1px solid rgba(51, 65, 85, 0.7);
    border-radius: 4px;
    padding: 2.5px 8px;
    margin-top: 5px;
}

.base-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #10b981;
}

.base-label {
    font-size: 10px;
    font-weight: 800;
    color: #94a3b8;
    letter-spacing: 0.4px;
}

.base-val {
    font-family: 'Consolas', monospace;
    font-size: 13.5px;
    font-weight: 900;
    color: #ffffff;
    margin-left: 2px;
}

.base-unit {
    font-size: 10px;
    font-weight: 700;
    color: #94a3b8;
    margin-left: 2px;
}

.metric-frametime-badge {
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid rgba(51, 65, 85, 0.4);
}

/* SPARKLINE */
.sparkline-box {
    display: flex;
    flex-direction: column;
    gap: 4px;
    background: rgba(10, 14, 22, 0.4);
    border: 1px solid rgba(51, 65, 85, 0.4);
    border-radius: 4px;
    padding: 6px 8px;
    margin-top: 1px;
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

/* SYSTEM METRICS GRID (GPU, CPU, VRAM, CACHE) */
.metrics-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 16px;
    padding: 2px 4px;
}

.metric-compact {
    display: flex;
    align-items: baseline;
    gap: 5px;
}

.compact-label {
    color: #94a3b8;
    font-weight: 800;
    font-size: 11.5px;
    letter-spacing: 0.4px;
}

.compact-val {
    font-family: 'Consolas', monospace;
    color: #ffffff;
    font-weight: 900;
    font-size: 15.5px;
}

.compact-unit {
    color: #94a3b8;
    font-weight: 700;
    font-size: 11px;
    margin-left: 2px;
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
