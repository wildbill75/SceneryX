# SceneryX — Patch PRO_1.1.6

**Release Date:** October 21, 2026
**Channel:** `Updates/patches`

## What's New & Fixed (Includes v1.1.5 & v1.1.6)

### 1. MSFS 2020/2024 In-Game Panel (`sceneryx-ingame-panel`)
- **Dynamic Auto-Height Window:** The MSFS In-Game Panel now automatically wraps its vertical height to match its content in real time (when expanding/collapsing the Live Graphics drawer or switching between Offline/Online states) while remaining horizontally resizable.
- **Full EN/FR Localization & Contextual Tooltips:** Added full English and French localization synchronized with SceneryX, plus resilient hover tooltips across all Live Graphics controls, Smart LOD sliders, Cloud Recovery, and Performance metrics.
- **Clean Package Naming & Auto-Refresh:** Standardized the Community package folder name to `sceneryx-ingame-panel` (automatically migrating legacy panel folders on startup) and preserved the `SCENERY X` panel header.

### 2. Smart LOD Governor & Live Memory Engine
- **MSFS 2024 Live Memory Offset & Signature Scanner:** Updated the Win32 Memory Engine base offset (`0x0A80B024`) for the latest `FlightSimulator2024.exe` build and added an automatic `.data` signature scanner so live `TLOD`, `OLOD`, `Clouds`, and hot-swappable graphics writes attach reliably in Read/Write mode.
- **Persistent Manual Mode (`MAN`) Disengagement:** Fixed an issue in both the MSFS In-Game Panel and the SceneryX Smart LOD window where disabling Smart LOD (`OFF`) or dragging the `TLOD` / `OLOD` sliders manually caused Smart LOD to snap back to `ON` after ~2 seconds.

### 3. Custom Graphics Profiles & Scenery / GSX Conflict Scanner
- **Independent Profile Saving & Switching:** Modifying individual settings in the Graphics Settings matrix no longer overwrites the active `.profile.json` file before clicking `SAVE PROFILE`, and switching profiles immediately refreshes the matrix and `UserCfg.opt`.
- **Duplicate Scenery & GSX Detection Fix:** Restored full multi-layer duplicate airport detection across `Community`, `Official`, `StreamedPackages`, and Addon Linker folders, as well as GSX profile conflict scanning during package rescans.
