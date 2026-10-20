# SceneryX — Patch PRO_1.1.5

**Release Date:** October 20, 2026
**Channel:** `Updates/patches`

## What's New & Fixed

### 1. Smart LOD Governor & MSFS In-Game Panel — Live Memory Engine & Manual Mode Fix
- **MSFS 2024 Live Memory Offset & Automatic Signature Scanner:** Updated the Win32 Memory Engine base offset (`0x0A80B024`) for the latest `FlightSimulator2024.exe` build and added an automatic `.data` signature scanner so live `TLOD`, `OLOD`, `Clouds`, and hot-swappable graphics writes attach in Read/Write mode across all MSFS 2024 updates.
- **Persistent Manual Mode (`MAN`) Disengagement:** Fixed an issue in both the MSFS In-Game Panel and the SceneryX internal Smart LOD window where disabling Smart LOD (`OFF`) or disengaging directly by dragging the `TLOD` / `OLOD` sliders caused Smart LOD to snap back to `ON` after ~2 seconds.
- **Automatic In-Game Panel Refresh on Startup:** SceneryX Pro now automatically refreshes the installed `wildbill75-sceneryx` package in your MSFS `Community` folder on startup whenever a patch update is applied.

### 2. Custom Graphics Profiles — Independent Profile Saving & Switching Fix
- **Protected Active Profile Presets:** Changing individual settings in the Graphics Settings matrix no longer silently overwrites the currently active `.profile.json` file on disk before clicking `SAVE PROFILE`, allowing you to tweak settings and save them as a brand-new profile (e.g., `2D Display ULTRA`) without altering your baseline profile (`2D Display Standard`).
- **Instant Matrix Refresh on Profile Switch:** Selecting a profile from the dropdown immediately loads and renders that profile's exact saved configuration in the Graphics Settings matrix and applies it to `UserCfg.opt`.
