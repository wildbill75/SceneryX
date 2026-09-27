# Design_Technical_Hardware_Optimizer

## Overview
This document specifies the technical design of the **Hardware & MSFS Graphics Optimizer** in SceneryX.
The purpose of this module is to serve as an intelligent advisory, calibration, and synchronization hub for the simmer's hardware and Microsoft Flight Simulator graphics settings, across both 2D and Virtual Reality (VR) display modes.

---

## 1. Architectural Principles
1. **Advisory & Calibration Hub**:
   - Provide clear, expert guidance on MSFS graphics parameters based on detected CPU, GPU, VRAM, and RAM characteristics.
   - Provide seamless 1-click calibration with automated timestamped configuration backups (`UserCfg.opt.backup_YYYYMMDD_HHMMSS`).
2. **2D Screen vs. VR Headset Decoupling**:
   - Maintain distinct inspection and tuning for 2D (`{Graphics}` and 2D Video keys) and VR (`{GraphicsVR}` and VR Video keys).
   - Clearly flag settings shared between both modes (`VSync`, `FrameLimiter`, `FullScreenResolution`).
3. **AutoFPS Hierarchy & Integration**:
   - Detect whether `AutoFPS` is active in the background.
   - If active: reflect dynamic control over TLOD/OLOD and adapt recommendations accordingly.
   - If inactive: allow direct manual tuning of TLOD/OLOD.
4. **Target Pacing Clarification**:
   - Clean metrics without misleading engine divisor jargon: `TARGET FPS` and `TARGET MAIN THREAD` (ms).

---

## 2. Hardware Detection & System Balance Engine ("MY RIG")
- **CPU**: Model, physical cores, logical threads.
- **GPU**: Model, VRAM capacity, driver version, Re-Size BAR state.
- **RAM**: Capacity, clock speed (MHz), XMP activation.
- **System Balance Matrix**:
  - `OPTIMAL`: High-tier CPU matching flagship GPU with adequate VRAM.
  - `MAINTHREAD_BOTTLENECK_RISK`: Older architecture or lower single-core CPU paired with high-end GPU (recommends lower TLOD and reduced airport ground traffic).
  - `VRAM_CONSTRAINED`: High resolution paired with $\le 12$ GB VRAM (recommends High/Medium textures and lower Terrain Detail).

---

## 3. MSFS Graphics Settings Matrix (13 Parameters)
| Parameter | 2D Key | VR Key | Shared? | Optimum Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **Full Screen Resolution** | `FullScreenResolution` | Headset Native | Yes | Native display resolution |
| **Anti-aliasing** | `AntiAliasing` / `DLSSMode` | `AntiAliasingVR` / `DLSSModeVR` | No | DLSS Quality / TAA |
| **Max Frame Rate** | `TargetFrameRate` | `TargetFrameRateVR` | No | Matched to display/headset sync divisor |
| **Frame Generation** | `FrameGeneration` | `FrameGenerationVR` | No | DLSSG for 2D / Off for native VR |
| **Framerate Multiplier** | `NBFramesToGenerate` | `NBFramesToGenerateVR` | No | 1 (Standard 2X DLSSG) |
| **V-Sync** | `VSync` | `VSync` | **Yes** | ON for G-Sync/FreeSync pacing |
| **V-Sync Interval** | `VSyncInterval` | `VSyncInterval` | **Yes** | 100% monitor refresh |
| **Dynamic Settings** | `DynamicSettings` | `DynamicSettingsVR` | No | OFF (prevents random texture pop-in) |
| **Terrain LOD (TLOD)** | `{Terrain LoDFactor}` | `{Terrain LoDFactor}` | No | 100-150 (or Dynamic if AutoFPS) |
| **Off Screen Terrain Pre-Caching** | `{OffscreenTerrainPreCaching}` | `{OffscreenTerrainPreCaching}` | No | High / Ultra (prevents pan stutters) |
| **Objects LOD (OLOD)** | `{ObjectsLoD LoDFactor}` | `{ObjectsLoD LoDFactor}` | No | 100-150 |
| **Displacement Mapping** | `{DisplacementMapping}` | `{DisplacementMapping}` | No | OFF (spares GPU compute & VRAM) |
| **Texture Resolution** | `{Texture Quality}` | `{Texture Quality}` | No | High (or Ultra if $\ge 16$ GB VRAM) |

---

## 4. Color-Coding & Evaluation Rules
- **Green (`Optimum`)**: Setting matches hardware capabilities and maximizes frame pacing stability.
- **Yellow (`Acceptable`)**: Setting is acceptable but may incur minor frametime variance.
- **Orange (`Sub-Optimal`)**: Setting causes avoidable performance penalties or high VRAM allocation.
- **Red (`NO GO`)**: Severe stutter hazard or memory overflow risk (e.g. TLOD 300 on mid-range CPU, Ultra Textures on 8 GB VRAM).
