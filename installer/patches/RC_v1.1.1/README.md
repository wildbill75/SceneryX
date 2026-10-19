# SceneryX — Patch RC_v1.1.1 (Day-One Update)

**Release Date:** October 17, 2026  
**Channel:** `Updates/patches`  
**Installer:** `SceneryX_RC_v1.1.1_Setup.exe`

---

## What's New & Fixed

### 1. My Rig — Update & Cache Cleaner
- **Safe Update Mode (Community Quarantine):** Added 1-click Community folder quarantine (`PREPARE FOR UPDATE` / restore) in **My Rig > Update & Cache Cleaner** to safely park and restore your Community add-ons before and after MSFS Sim Updates.
- **MSFS & GPU Shader Cache Cleaner:** Added real-time scanning and 1-click cleanup (`PURGE ALL CACHES` or individual purge) for MSFS SceneryIndexes, Rolling Cache, StreamedPackages cache, WASM/Aircraft state caches, and DirectX / NVIDIA / AMD GPU Shader Caches.

### 2. Live Telemetry & MSFS In-Game Panel Synchronization
- **Bi-Directional Monitoring Sync:** Starting or stopping Flight Monitoring from either the MSFS In-Game Panel or the SceneryX desktop app now synchronizes immediately across both interfaces.
- **Real-Time Sidebar Counter:** Fixed the `TELEMETRY` elapsed time counter badge (`00:01`, `00:02`...) in the left navigation bar so it updates live as soon as monitoring starts.
- **30S Trend Sparkline Control:** Clicking `STOP MONITORING` now immediately halts the live `30S TREND` graph and returns the telemetry display to `STANDBY`.
- **Post-Flight Report Generation:** Resolved an issue where stopping telemetry from the In-Game Panel did not trigger flight report generation in SceneryX.

### 3. Route & Airport City Name Harmonization
- **Clean Metropolitan City Names:** Harmonized airport city labels across SimBrief plans, Live Flight Monitoring, and Post-Flight Reports (e.g., `LGAV (Athens)` instead of municipality names like `Spata-Artemida`).

### 4. Automated Update & Patch Pipeline
- **Automatic Update Detection:** SceneryX now automatically checks the `Updates/patches` Git branch on startup and offers 1-click patch installation while preserving all user settings, custom profiles, and scenery states.
- **Post-Update Changelog Modal:** Displays the patch release notes (`README.md`) automatically after installing an update.
