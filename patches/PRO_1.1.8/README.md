# SceneryX — Patch PRO_1.1.8

**Release Date:** October 22, 2026
**Channel:** `Updates/patches`

## What's New & Fixed (Includes v1.1.5, v1.1.6, v1.1.7 & v1.1.8)

### 1. Scenery Scanner & Conflict Resolution Persistence
- **Strict Non-Airport Scenery Exclusion & Immunity:** Completely excluded and protected all non-airport scenery packages (City & Sightseeing packs such as SamScene3D, Landmarks, POI, Photogrammetry, Asobo/Microsoft non-airport scenery & Red Bull Air Race packs, Bridges, Vessels/Marinas, VFR Obstacles, Powerlines, Night Lighting, and Terrain/DEM Mesh) from being flagged as airports or disabled during conflict resolution.
- **Persistent Conflict Resolution Choices (`resolved_conflicts`):** Your choices in the **Scenery Conflict Detected** modal are now permanently saved in `settings.json` and synchronized across all `Content.xml` locations (including MSFS 2024 `StreamedPackages` handcrafted airports), so you never have to answer the same conflict prompt twice on startup.

### 2. MSFS 2020/2024 In-Game Panel (`sceneryx-ingame-panel`) — VR & 2D Auto-Fit
- **VR Stability & Native Auto-Fit Sizing:** Resolved the CoherentGT `ON_VIEW_RESIZED` feedback loop in VR and implemented native Asobo one-shot vertical auto-fit when expanding/collapsing the Live Graphics drawer or switching Offline/Online in both 2D and VR.
- **Full EN/FR Localization & Contextual Tooltips:** Added full English and French localization synchronized with SceneryX, plus instant hover tooltips across all controls.

### 3. GSX Pro Manager, Smart LOD & Map Rendering
- **Smart `.ini` + `.py` Companion Bundling:** GSX profile archives containing both an `.ini` file and a companion `.py` script with a Flightsim.to hash in the filename are now paired into a single unified profile (`+ Python Script`).
- **MSFS 2024 Live Memory Offset & Manual Mode (`MAN`) Fix:** Updated the Win32 Memory Engine offset + signature scanner for MSFS 2024 and fixed Smart LOD snapping back to `ON` after manual overrides.
- **Smooth Map Zoom & Tile Rendering:** Eliminated bright square tile artifacts during map zooming/panning.
