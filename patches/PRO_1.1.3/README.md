# SceneryX — Patch PRO_1.1.3

**Release Date:** October 19, 2026
**Channel:** `Updates/patches`

## What's New & Fixed

### 1. MSFS In-Game Panel — Independent Auto Cloud Recovery, Per-Setting Reset (`↺`) & Enlarged Controls
- **Independent Auto Cloud Recovery:** `AUTO CLOUD RECOVERY` now operates independently even when `SMART LOD REGULATION` (`TLOD`/`OLOD`) is turned `OFF`, continuously monitoring FPS/MainThread headroom and displaying real-time `LIVE : LOW / MEDIUM / HIGH / ULTRA` cloud status.
- **Per-Setting Baseline Reset (`↺`):** Added individual reset (`↺`) buttons next to each of the 8 hot-swappable graphics parameters in the In-Game Panel to instantly restore any setting back to its pre-flight baseline.
- **Refined Cockpit UI Ergonomics:** Enlarged the Live Graphics Tuning accordion controls, quick-pin badges, and default cockpit panel dimensions for effortless readability in both 2D and VR.

### 2. MSFS 2024 Store / Marketplace (`StreamedPackages`) Detection & Startup Modal Queue
- **Multi-Source Package Snapshot Tracking:** Upgraded `library_snapshot.json` to track all installed packages per airport across `Community`, `Official`, and `MSFS 2024 StreamedPackages`. Installing a new Store/Marketplace or Community airport for an ICAO that already had a base package now reliably triggers the **Library Changes Detected** modal on startup.
- **Non-Overlapping Startup Modal Sequence:** Synchronized startup modals so Background Tools alerts (`AutoFPS` / `OFXR`) wait until you close the **Library Changes Detected** summary instead of overlapping it.

### 3. Interactive Onboarding Tour Expansion (29 Steps) & First-Launch Indexing Polish
- **New Guided Tour Steps:** Added dedicated interactive steps for **My Rig > Update & Cache Cleaner** (Safe Update Quarantine & Shader/WASM Cache Purge), updated **In-Game Panel in Cockpit** (Smart LOD & Performance Telemetry), and added **In-Flight Live Graphics Controls** (hot-swappable settings & 5-pin quick bar).
- **Streamlined First-Launch Indexing:** Prevented redundant pre-disclaimer library scans on first launch and ensured instant ICAO search indexing and GSX profile badge initialization right after the initial database build.
