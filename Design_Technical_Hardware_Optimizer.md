# Design_Technical_Hardware_Optimizer

## Overview
This document specifies the technical design of the **Hardware & MSFS Graphics Optimizer** in SceneryX.
The purpose of this module is to serve as an intelligent advisory, calibration, and synchronization hub for the simmer's hardware and Microsoft Flight Simulator graphics settings, across both 2D and Virtual Reality (VR) display modes.

---

## 1. Architectural Principles
1. **Advisory & Calibration Hub**:
   - Provide clear, expert guidance on MSFS graphics parameters based on detected CPU, GPU, VRAM, and RAM characteristics.
   - Provide seamless 1-click calibration with automated timestamped configuration backups (`UserCfg.opt.backup_YYYYMMDD_HHMMSS`) and instant 1-click rollback.
2. **Flight Mission Profile Awareness (Airliners vs GA)**:
   - Provide dedicated flight mission modes: `[ IFR AIRLINER ]` and `[ VFR GENERAL AVIATION ]`.
   - Adapt evaluation matrices and advice based on flight characteristics: complex payware airliners stress the CPU MainThread and VRAM significantly more than General Aviation aircraft.
3. **VR Headset Decoupling & Refresh Rate Synchronization**:
   - Maintain distinct inspection and tuning for 2D (`{Graphics}` and 2D Video keys) and VR (`{GraphicsVR}` and VR Video keys).
   - Support selectable VR headset refresh rates (`72 Hz`, `80 Hz`, `90 Hz`, `120 Hz`) to accurately calculate the 1/2 sync reprojection target (36, 40, 45, 60 FPS).
   - Clearly flag settings shared between both modes (`VSync`, `FrameLimiter`, `FullScreenResolution`).
4. **AutoFPS Hierarchy & Integration**:
   - Detect whether `AutoFPS` is active in the background.
   - If active: reflect dynamic control over TLOD/OLOD and adapt recommendations accordingly.
   - If inactive: allow direct manual tuning of TLOD/OLOD.
5. **Target Pacing Clarification**:
   - Clean metrics without misleading engine divisor jargon: `TARGET FPS` and `TARGET MAIN THREAD` (ms).
6. **Cross-Settings Interdependence & Conflict Engine**:
   - Continuously evaluate cross-parameter synergies (e.g. DLSS + Low/Med textures = -8 GB VRAM) and conflicts (e.g. 4K TAA + Ultra textures on airliners = D3D12 paging stutters; VR + Frame Generation = head-tracking distortion).

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

## 3. The Axel LFBO Airliner VRAM Architecture
- **Technical Problem**: At major payware hub airports, complex airliners (Fenix A320, PMDG 777, FlyByWire A380, Inibuilds A300) combined with Ultra/High textures frequently exceed 15-16 GB of VRAM. DirectX 12 WDDM paging over PCIe then causes 0.5s to 2s stutter freezes.
- **The Solution**: Setting `Texture Resolution` to **LOW** slashes VRAM footprint by **6 to 8 GB**.
- **Avionics Rendering Mechanics**: In modern MSFS aircraft, cockpit screens (PFD, ND, MCDU, ECAM, EICAS) are vector and canvas render targets (CoherentGT/HTML/WASM), completely unaffected by world texture compression. Avionics remain sharp while completely freeing VRAM.
- **VR Impact**: In VR stereo rendering, Low texture resolution prevents compositor dropouts and frame stalls.
- **General Aviation Distinction**: In GA VFR flight, low-altitude scenery clarity is paramount and GA planes consume minimal VRAM ($\le 8$ GB). Thus, High/Ultra is optimal for GA.

---

## 4. MSFS Graphics Settings Matrix (13 Parameters)
| Parameter | 2D Key | VR Key | Shared? | Optimum Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **Full Screen Resolution** | `FullScreenResolution` | Headset Native | Yes | Native display resolution |
| **Anti-aliasing** | `AntiAliasing` / `DLSSMode` | `AntiAliasingVR` / `DLSSModeVR` | No | DLSS Quality / Balanced / TAA |
| **Max Frame Rate** | `TargetFrameRate` | `TargetFrameRateVR` | No | Display sync divisor (2D) / 1/2 Headset Hz (VR) |
| **Frame Generation** | `FrameGeneration` | `FrameGenerationVR` | No | DLSSG for 2D / OFF for VR |
| **Framerate Multiplier** | `NBFramesToGenerate` | `NBFramesToGenerateVR` | No | 1 (Standard 2X DLSSG) |
| **V-Sync** | `VSync` | `VSync` | **Yes** | ON for G-Sync/FreeSync pacing |
| **V-Sync Interval** | `VSyncInterval` | `VSyncInterval` | **Yes** | 100% monitor refresh |
| **Dynamic Settings** | `DynamicSettings` | `DynamicSettingsVR` | No | OFF (prevents random texture pop-in) |
| **Terrain LOD (TLOD)** | `{Terrain LoDFactor}` | `{Terrain LoDFactor}` | No | 100-120 (Airliners) / 150-180 (GA) / AutoFPS |
| **Off Screen Terrain Pre-Caching** | `{OffscreenTerrainPreCaching}` | `{OffscreenTerrainPreCaching}` | No | High / Ultra (prevents pan stutters) |
| **Objects LOD (OLOD)** | `{ObjectsLoD LoDFactor}` | `{ObjectsLoD LoDFactor}` | No | 100-120 |
| **Displacement Mapping** | `{DisplacementMapping}` | `{DisplacementMapping}` | No | OFF (spares GPU compute & VRAM) |
| **Texture Resolution** | `{Texture Quality}` | `{Texture Quality}` | No | Low (Airliners - Axel LFBO) / High-Ultra (GA) |

---

## 5. Rollback & Backup System Design
- **Single-Pass Safety Backup**: A timestamped backup (`UserCfg.opt.backup_YYYYMMDD_HHMMSS`) is generated once prior to batch optimization.
- **Rollback Interface**: A dedicated rollback modal lists all historical backups with timestamp and file size, enabling 1-click restore.
- **Safety Copy on Rollback**: Restoring a backup automatically creates a safety snapshot of the active file before overwriting.
