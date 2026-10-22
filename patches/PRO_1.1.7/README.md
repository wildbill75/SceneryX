# SceneryX — Patch PRO_1.1.7

**Release Date:** October 21, 2026
**Channel:** `Updates/patches`

## What's New & Fixed (Includes v1.1.5, v1.1.6 & v1.1.7)

### 1. GSX Pro Manager & Interactive Map Rendering
- **Smart `.ini` + `.py` Companion Bundling:** Fixed an issue where GSX profile archives containing both an `.ini` configuration file and a companion `.py` Python customization script with a Flightsim.to hash in the filename (e.g., `lpma-7ryin1-amsim-zwackelpeter.ini` + `lpma-amsim-zwackelpeter.py`) were flagged as conflicting `DUPLICATE` profiles instead of being bundled into a single unified profile with the `+ Python Script` badge.
- **Unified Enable / Disable / Delete / Duplicate Resolution:** Enabling, disabling, deleting, or resolving duplicates for a GSX profile now keeps its `.ini` configuration and `.py` companion script synchronized together.
- **Smooth Map Zoom & Tile Rendering:** Eliminated bright square tile artifacts during map zooming/panning (`mix-blend-mode` fix) and optimized off-screen tile buffering for faster, seamless map transitions.

### 2. MSFS 2020/2024 In-Game Panel (`sceneryx-ingame-panel`) — VR Stability Fix
- **VR VRAM & Render-Target Stability Fix:** Resolved a critical CoherentGT `resize` feedback loop (`content-fit` / `sendUpdatePanelSize`) that continuously reallocated 3D VR panel render-target textures in VRAM when opening the In-Game Panel in VR with high-VRAM aircraft (e.g., Fenix A320).
- **Full EN/FR Localization & Contextual Tooltips:** Added full English and French localization synchronized with SceneryX, plus resilient hover tooltips across all Live Graphics controls, Smart LOD sliders, Cloud Recovery, and Performance metrics.
- **Clean Package Naming & Auto-Refresh:** Standardized the Community package folder name to `sceneryx-ingame-panel` (automatically migrating legacy panel folders on startup) and preserved the `SCENERY X` panel header.

### 3. Smart LOD Governor & Live Memory Engine
- **MSFS 2024 Live Memory Offset & Signature Scanner:** Updated the Win32 Memory Engine base offset (`0x0A80B024`) for the latest `FlightSimulator2024.exe` build and added an automatic `.data` signature scanner so live `TLOD`, `OLOD`, `Clouds`, and hot-swappable graphics writes attach reliably in Read/Write mode.
- **Persistent Manual Mode (`MAN`) Disengagement:** Fixed an issue in both the MSFS In-Game Panel and the SceneryX Smart LOD window where disabling Smart LOD (`OFF`) or dragging the `TLOD` / `OLOD` sliders manually caused Smart LOD to snap back to `ON` after ~2 seconds.

### 4. Custom Graphics Profiles, Settings Persistence & Conflict Scanner
- **Atomic `settings.json` Persistence:** Protected user preferences (language, theme, close action, scan paths, SimBrief ID) against concurrent read/write resets during patches or background scans.
- **Independent Profile Saving & Switching:** Modifying individual settings in the Graphics Settings matrix no longer overwrites the active `.profile.json` file before clicking `SAVE PROFILE`, and switching profiles immediately refreshes the matrix and `UserCfg.opt`.
- **Duplicate Scenery & GSX Detection Fix:** Restored full multi-layer duplicate airport detection across `Community`, `Official`, `StreamedPackages`, and Addon Linker folders.
