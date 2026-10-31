# SceneryX — Release PRO_1.2.0

**Release Date:** October 30, 2026
**Channel:** `Updates/patches`

## NEW FEATURES

### 1. Interactive 3D Terrestrial Globe & Cartographic Engine
- **2D Planisphere & 3D Terrestrial Globe (`2D Map` / `3D Globe`):** Seamlessly switch between the 2D Mercator planisphere and the new 3D Terrestrial Globe with full spherical projection, fine mouse-wheel zoom increments, 3D great-circle flight arcs, and world-space airport clustering.
- **8 Unified Cartographic Styles & VFR / IFR Aeronautical Charts:** Choose between 4 dark cockpit themes (`Avionics Blue`, `Deep Navy`, `Carbon Dark`, `Radar Emerald`), official OpenAIP **VFR Chart** & **IFR Enroute** aeronautical overlays (controlled airspaces, VOR/NDB navaids, frequencies), **Satellite** imagery, and **Street Map** in both 2D and 3D.
- **Real-Time Day / Night Solar Terminator & UTC / Local Timeline:** Visualize real-time daylight, twilight, and night across the world in 2D and 3D. Scrub through the 24-hour timeline (`-1H` / `+1H` or slider), toggle between **UTC (Zulu)** and **Local Time (`UTC±`)**, or sync with the **LIVE** clock.

### 2. Unified Scenery & Route Optimizer + Loadout Rules Builder
- **Custom Base Loadout Profiles (`Edit Loadout Rules`):** Create, save, and activate reusable base scenery environments (e.g., *Europe Airliners*, *North America*). Filter active sceneries by category (`Payware`, `Freeware`, `Asobo`), world regions, or individual countries.
- **Interactive Map Airport Pinning (`Pin Airports on Map`):** Lock favorite hubs directly on the 2D map or 3D globe so they always stay enabled regardless of regional rules.
- **Route Overlay & SimBrief Alternates Integration:** Combine any Base Loadout Profile with a **Direct A-to-B**, **En-Route Corridor**, or **SimBrief OFP** flight plan (automatically protecting departure, destination, corridor, and SimBrief alternate airports).

### 3. Live Telemetry (`DEP / ARR / ACTUAL POSITION`) & Hardware-Tailored Profiles
- **Enhanced Live Flight Telemetry Header:** Displays your planned **DEP** and **ARR** from SimBrief (or live auto-detected origin in Free Flight) alongside your aircraft's real-time **ACTUAL POSITION**.
- **Continuous Hardware Sync & Tailored Presets:** Automatically adapts `LOW`, `OPTIMUM`, and `ULTRA` MSFS graphics profiles and Smart LOD targets to your detected CPU, GPU VRAM, RAM, and display refresh rate, and refreshes recommendations whenever a hardware upgrade is detected.
- **Updated Interactive Onboarding Tour:** Added `NEW` feature tags and a dedicated walkthrough step for **Edit Loadout Rules & Custom Profiles**.

## BUG FIXES & STABILITY

### 1. 3D Globe, UI & Graphics Settings Fixes
- **3D Globe Startup Optical Centering:** Fixed the 3D Globe horizontal offset when opening SceneryX with the Classic left sidebar active, and added `ResizeObserver` viewport tracking.
- **MSFS Graphic Settings 2D / VR Mode Badge Sync:** Fixed the sidebar and top banner `2D` / `VR` indicator so it updates immediately when switching between `2D DISPLAY` and `VR HEADSET` tabs, and aligned all 4 quick-preset keys (`TerrainLoDFactor`, `ObjectsLoDFactor`, `OffscreenTerrainPreCaching`, `TextureResolution`).
- **Loadout Builder Map Click & Modal Close Cleanup:** Fixed map click interception when opening another drawer over the Loadout Builder, and ensured closing the window while in Pin Mode properly restores the active loadout map preview.

### 2. Backend NTFS Concurrency, Sim Guards & State Persistence
- **Multi-Airport Bundle BGL Restoration:** Fixed orphaned `.bgl.sceneryx_off` files when switching directly between Loadout Profiles and preserved manual scenery exclusions during partial restores.
- **Strict Simulator Locks & Mutation Mutex:** Added thread-safe re-entrant locking (`_scenery_mutation_lock`), strict simulator-running checks (`_is_sim_running_guard`) on all NTFS junction/folder operations, and frontend button debouncing.
- **Atomic Settings & Hardware Cache Writes:** Prevented concurrent `settings.json` overwrites when saving `hardware_profile_cache.json` and eliminated false-positive RAM change loops on boot.
