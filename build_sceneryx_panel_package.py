import os
import sys
import json
import shutil
import struct
import re

BASE_DIR = r"D:\SceneryX"
PANEL_PKG_DIR = os.path.join(BASE_DIR, "sceneryx-ingame-panel")
LEGACY_PKG_DIR = os.path.join(BASE_DIR, "wildbill75-sceneryx")

COMMUNITY_PATHS = [
    r"C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\Community",
    r"C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\Community2024"
]

CONTENT_XML_PATHS = [
    r"C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Content.xml",
    r"C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml"
]


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
    if os.path.exists(batc_spb):
        with open(batc_spb, "rb") as f:
            batc_orig = f.read()
        header = bytearray(batc_orig[:0x18e])
    else:
        existing_spb = os.path.join(PANEL_PKG_DIR, "InGamePanels", "InGamePanel_SceneryX.spb")
        if not os.path.exists(existing_spb):
            existing_spb = os.path.join(LEGACY_PKG_DIR, "InGamePanels", "InGamePanel_SceneryX.spb")
        with open(existing_spb, "rb") as f:
            batc_orig = f.read()
        header = bytearray(batc_orig[:0x18e])

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
    numeric_chunk = bytearray()
    numeric_chunk.extend(struct.pack("<II", 9, 1))
    numeric_chunk.extend(struct.pack("<If", 10, 4.0))
    numeric_chunk.extend(struct.pack("<If", 11, 4.0))
    numeric_chunk.extend(struct.pack("<If", 12, 37.0))
    numeric_chunk.extend(struct.pack("<If", 13, 65.0))
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
    print("[*] Rebuilding SceneryX In-Game Panel (sceneryx-ingame-panel) with auto-fit, EN/FR i18n, and contextual tooltips...")
    web_panel_dir = os.path.join(BASE_DIR, "web", "in_game_panel")
    h_src = os.path.join(web_panel_dir, "SceneryX_Remote.html")
    c_src = os.path.join(web_panel_dir, "SceneryX_Remote.css")
    j_src = os.path.join(web_panel_dir, "SceneryX_Remote.js")

    with open(h_src, "r", encoding="utf-8") as f:
        final_html = f.read()
    with open(c_src, "r", encoding="utf-8") as f:
        final_css = f.read()
    with open(j_src, "r", encoding="utf-8") as f:
        final_js = f.read()

    spb_bytes = build_spb(
        spb_filename="InGamePanel_SceneryX.spb",
        panel_id="PANEL_SCENERYX",
        panel_title="SCENERY X",
        html_url="html_ui/InGamePanels/SceneryX_Remote/SceneryX_Remote.html",
        toolbar_icon="ICON_TOOLBAR_SCENERYX"
    )

    if os.path.exists(LEGACY_PKG_DIR):
        shutil.rmtree(LEGACY_PKG_DIR)
        print(f"  -> Removed legacy repo folder: {LEGACY_PKG_DIR}")

    if os.path.exists(PANEL_PKG_DIR):
        shutil.rmtree(PANEL_PKG_DIR)

    os.makedirs(os.path.join(PANEL_PKG_DIR, "InGamePanels"), exist_ok=True)
    os.makedirs(os.path.join(PANEL_PKG_DIR, "html_ui", "icons", "toolbar"), exist_ok=True)
    os.makedirs(os.path.join(PANEL_PKG_DIR, "html_ui", "Textures", "Menu", "toolbar"), exist_ok=True)
    panel_ui_dir = os.path.join(PANEL_PKG_DIR, "html_ui", "InGamePanels", "SceneryX_Remote")
    os.makedirs(panel_ui_dir, exist_ok=True)

    # 1. MANIFEST.JSON
    manifest = {
        "dependencies": [],
        "content_type": "UI",
        "title": "SCENERY X",
        "manufacturer": "SceneryX",
        "creator": "SceneryX",
        "package_version": "1.1.6",
        "minimum_game_version": "1.0.0",
        "release_notes": {
            "neutral": {
                "LastUpdate": "SceneryX In-Game Panel V1.1.6 - Auto-fit window height & EN/FR Localization",
                "OlderHistory": ""
            }
        }
    }
    with open(os.path.join(PANEL_PKG_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("  -> manifest.json written (v1.1.6, creator: SceneryX, title: SCENERY X)")

    # 2. LOCPAKS
    locpak_strings = {
        "SCENERY X": "SCENERY X",
        "SceneryX": "SCENERY X",
        "SCENERYX": "SCENERY X",
        "PANEL_SCENERYX": "SCENERY X",
        "SceneryX_Remote": "SCENERY X",
        "ICON_TOOLBAR_SCENERYX": "SCENERY X",
        "sceneryx-ingame-panel": "SCENERY X"
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
    spb_out = os.path.join(PANEL_PKG_DIR, "InGamePanels", "InGamePanel_SceneryX.spb")
    with open(spb_out, "wb") as f:
        f.write(spb_bytes)
    print(f"  -> InGamePanels/InGamePanel_SceneryX.spb compiled ({len(spb_bytes)} bytes, Title: 'SCENERY X')")

    # 4. CLEAN VECTOR SVG ICONS
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
    with open(os.path.join(panel_ui_dir, "SceneryX_Remote.html"), "w", encoding="utf-8") as f:
        f.write(final_html)
    with open(os.path.join(panel_ui_dir, "SceneryX_Remote.css"), "w", encoding="utf-8") as f:
        f.write(final_css)
    with open(os.path.join(panel_ui_dir, "SceneryX_Remote.js"), "w", encoding="utf-8") as f:
        f.write(final_js)
    print("  -> SceneryX_Remote HTML, CSS, JS written to package")

    # 6. LAYOUT.JSON GENERATOR
    layout_entries = []
    for root, _, files in os.walk(PANEL_PKG_DIR):
        for file in files:
            if file == "layout.json":
                continue
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

    # 7. DEPLOY DIRECTLY TO ALL COMMUNITY TARGETS (sceneryx-ingame-panel ONLY, purge wildbill75-sceneryx)
    for base_comm in COMMUNITY_PATHS:
        if not os.path.exists(base_comm):
            continue

        old_legacy = os.path.join(base_comm, "wildbill75-sceneryx")
        if os.path.exists(old_legacy):
            shutil.rmtree(old_legacy)
            print(f"  -> Removed legacy package from {old_legacy}")

        dest = os.path.join(base_comm, "sceneryx-ingame-panel")
        print(f"[*] Deploying to: {dest}...")
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(PANEL_PKG_DIR, dest)
        print(f"  -> Successfully deployed to {dest}")

    # 8. UPDATE CONTENT.XML (Remove wildbill75-sceneryx, ensure sceneryx-ingame-panel)
    for cxml_path in CONTENT_XML_PATHS:
        if os.path.exists(cxml_path):
            try:
                with open(cxml_path, "r", encoding="utf-8") as f:
                    content_xml = f.read()

                content_xml = re.sub(r'\s*<Package name="[^"]*wildbill75-sceneryx"[^>]*/>', '', content_xml)

                packages_to_ensure = [
                    "communityfs20-sceneryx-ingame-panel",
                    "communityfs24-sceneryx-ingame-panel"
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

    print("\n[SUCCESS] SceneryX In-Game Panel (sceneryx-ingame-panel) built and deployed cleanly!")


if __name__ == "__main__":
    build()
