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

## 4. MSFS Graphics Settings Architecture (27 Parameters across 3 Pages)
The graphics configuration interface features a 3-page lateral carousel with a clean $3 \times 3$ grid (exactly 9 parameters per page) to optimize visual ergonomics and clarity:

### Page 1: Core & Display Pacing (9 Parameters)
| Parameter | 2D Key | VR Key | Shared? | Input Mode | Optimum Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Full Screen Resolution** | `FullScreenResolution` | Headset Native | **Yes** | Select | Native display resolution |
| **Anti-Aliasing & Upscaling** | `AntiAliasing` / `DLSSMode` | `AntiAliasingVR` / `DLSSModeVR` | No | Select | DLSS Quality / Balanced |
| **Max Frame Rate** | `TargetFrameRate` | `TargetFrameRateVR` | No | **Numeric + Presets** | Display sync divisor (2D) / 1/2 Headset Hz (VR) |
| **Frame Generation** | `FrameGeneration` | `FrameGenerationVR` | No | Select | DLSSG (2D) / OFF (VR mandatory) |
| **Framerate Multiplier** | `NBFramesToGenerate` | `NBFramesToGenerateVR` | No | Select | 1 (Standard 2X DLSSG) |
| **V-Sync** | `VSync` | `VSync` | **Yes** | Select | ON for G-Sync/FreeSync pacing |
| **Dynamic Settings** | `DynamicSettings` | `DynamicSettingsVR` | No | Select | OFF (prevents random resolution drops) |
| **NVIDIA Reflex** | `Reflex` | `ReflexVR` | No | Select | ON / ON+BOOST (minimizes input latency) |
| **Texture Resolution** | `{Texture Quality}` | `{Texture Quality}` | No | Select | Low (Airliners - Axel LFBO) / High-Ultra (GA) |

### Page 2: Terrain & Environment World (9 Parameters)
| Parameter | 2D Key | VR Key | Shared? | Input Mode | Optimum Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Terrain LOD (TLOD)** | `{Terrain LoDFactor}` | `{Terrain LoDFactor}` | No | **Numeric (10-400) + Presets** | 100-120 (Airliners) / 150-200 (GA) / AutoFPS |
| **Objects LOD (OLOD)** | `{ObjectsLoD LoDFactor}` | `{ObjectsLoD LoDFactor}` | No | **Numeric (10-400) + Presets** | 100-120 |
| **Off Screen Pre-Caching** | `{OffscreenTerrainPreCaching}` | `{OffscreenTerrainPreCaching}` | No | Select | High / Ultra (prevents camera pan stutters) |
| **Volumetric Clouds** | `{VolumetricClouds Quality}` | `{VolumetricClouds Quality}` | No | Select | High |
| **Buildings Quality** | `{Buildings Quality}` | `{Buildings Quality}` | No | Select | High / Ultra |
| **Trees Quality** | `{Procedural TreesQuality}` | `{Procedural TreesQuality}` | No | Select | High |
| **Grass & Bushes** | `{Procedural GrassQuality}` | `{Procedural GrassQuality}` | No | Select | High / Medium |
| **Water Waves Simulation** | `{Water FFTSize}` | `{Water FFTSize}` | No | Select | High (512) (2D) / Medium (256) (VR) |
| **Displacement Mapping** | `{DisplacementMapping Enabled}` | `{DisplacementMapping Enabled}` | No | Select | OFF (spares GPU compute & VRAM) |

### Page 3: Lighting, Avionics & Post-Processing (9 Parameters)
| Parameter | 2D Key | VR Key | Shared? | Input Mode | Optimum Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Glass Cockpit Refresh** | `{GlassCockpitsRefreshRate Quality}` | `{GlassCockpitsRefreshRate Quality}` | No | Select | Medium / Low (Airliners) / High (GA) |
| **Shadow Maps Resolution** | `{Shadows Size}` | `{Shadows Size}` | No | Select | High (1536) (2D) / Medium (1024) (VR) |
| **Terrain Shadows** | `{HeightFieldShadows Size}` | `{HeightFieldShadows Size}` | No | Select | High (512) (2D) / Medium (256) (VR) |
| **Contact Shadows** | `{ContactShadows Quality}` | `{ContactShadows Quality}` | No | Select | High (2D) / Medium (VR) |
| **Ambient Occlusion (SSAO)** | `{SSAO Quality}` | `{SSAO Quality}` | No | Select | High (2D) / Low-Medium (VR) |
| **Screen Reflections (SSR)** | `{SSR Quality}` | `{SSR Quality}` | No | Select | High (2D) / Low-Medium (VR) |
| **Volumetric Lights** | `{VolumetricLights Quality}` | `{VolumetricLights Quality}` | No | Select | High (2D) / Low-Medium (VR) |
| **Anisotropic Filtering** | `{Texture MaxAnisotropy}` | `{Texture MaxAnisotropy}` | No | Select | 16X |
| **Windshield Effects** | `{WindShield Quality}` | `{WindShield Quality}` | No | Select | High / Ultra |

---

## 5. Lateral Carousel & Manual Numeric Input Design
1. **Airy Dual-Row Header**:
   - **Row 1**: Displays section title, 2D/VR display switcher, Airliner/GA mission profile switcher, VR refresh rate selector (72, 80, 90, 120 Hz), AutoFPS live indicator, Rollback button, and Profile Optimization button.
   - **Row 2**: Displays carousel page navigation tabs (`1. CORE & DISPLAY`, `2. TERRAIN & WORLD`, `3. LIGHTING & AVIONICS`), left/right navigation arrows (`<` and `>`), and live page counter (`PAGE X / 3`).
2. **Carousel Viewport**:
   - Houses three full-width $3 \times 3$ grid panels sliding along the X-axis via CSS transform transitions (`translateX(-0%)`, `translateX(-100%)`, `translateX(-200%)`).
3. **Manual Numeric Input System**:
   - For `tlod`, `olod`, and `max_frame_rate`, users can either:
     - Directly type any custom numeric value (e.g. 85, 115, 235, up to 400) and commit via Enter or field exit (blur).
     - Select from an ergonomic preset dropdown that automatically synchronizes with the numeric field.

---

## 6. Rollback & Backup System Design
- **Single-Pass Safety Backup**: A timestamped backup (`UserCfg.opt.backup_YYYYMMDD_HHMMSS`) is generated once prior to batch optimization.
- **Rollback Interface**: A dedicated rollback modal lists all historical backups with timestamp and file size, enabling 1-click restore.
- **Safety Copy on Rollback**: Restoring a backup automatically creates a safety snapshot of the active file before overwriting.
