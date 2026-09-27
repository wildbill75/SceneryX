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
4. **Multi-Monitor Awareness & Dynamic Routing**:
   - Detect all active desktop monitors connected to the system with their individual resolutions and refresh rates (e.g. Display 1: LG UltraGear @ 180 Hz, Display 2: LG UltraGear @ 165 Hz).
   - Allow simmers to designate which display runs MSFS, dynamically adjusting the 1/2 sync pacing divisor (90 FPS for 180 Hz, 82 FPS for 165 Hz).
5. **AutoFPS Hierarchy & Integration**:
   - Detect whether `AutoFPS` is active in the background.
   - If active: reflect dynamic control over TLOD/OLOD and adapt recommendations accordingly.
   - If inactive: allow direct manual tuning of TLOD/OLOD.
6. **Target Pacing Clarification**:
   - Clean metrics without misleading engine divisor jargon: `TARGET FPS` and `TARGET MAIN THREAD` (ms).
7. **Cross-Settings Interdependence & Conflict Engine**:
   - Continuously evaluate cross-parameter synergies (e.g. DLSS + Low/Med textures = -8 GB VRAM) and conflicts (e.g. 4K TAA + Ultra textures on airliners = D3D12 paging stutters; VR + Frame Generation = head-tracking distortion).

---

## 2. Hardware Detection & System Balance Engine ("MY RIG")
- **CPU**: Model, physical cores, logical threads.
- **GPU**: Model, dedicated VRAM capacity, driver version, Re-Size BAR state.
- **Active Display (Monitor)**:
  - Enumerates all attached desktop displays using `EnumDisplayDevicesW`, `EnumDisplaySettingsW`, and `WmiMonitorID`.
  - Displays resolution and native refresh rate (e.g. `2560 x 1440 • LG ULTRAGEAR`).
  - When multi-monitor setups are detected, renders quick-switch pills (`DISPLAY 1 (180 Hz)` | `DISPLAY 2 (165 Hz)`) for on-the-fly display designation.
- **VR Headset Scanner Engine**:
  - Automatically scans the system at startup for active or configured Virtual Reality headsets across major PCVR ecosystems:
    - **Pimax**: Detects Pimax Crystal / Crystal Light / 8KX from Pimax runtime (`P3CONFIG.json`, `profile.json`, and live service logs), extracting active refresh rates (e.g. `72 Hz`, `80 Hz`, `90 Hz`, `120 Hz`).
    - **SteamVR**: Inspects `steamvr.vrsettings` for `LastKnown` HMD model and manufacturer (Valve Index, HTC Vive, Bigscreen Beyond).
    - **Meta / Oculus**: Inspects Oculus Runtime and Virtual Desktop configurations (Meta Quest 2/3/Pro, Rift S).
    - **Windows Mixed Reality**: Inspects Holographic system configurations (HP Reverb G2).
  - Reports detected headset model and native cadence directly in the dedicated card of **MY RIG** (e.g. `Pimax Crystal Light - 72 Hz Active`), and auto-initializes the VR refresh rate sync target.
- **System Memory (RAM)**: Capacity, clock speed (MHz), XMP activation.
- **Accelerators & Drivers**: Hardware-Accelerated GPU Scheduling (HAGS), Re-Size BAR, and DLSS runtime version.
- **System Balance Matrix**:
  - `OPTIMAL`: High-tier CPU matching flagship GPU with adequate VRAM.
  - `MAINTHREAD_BOTTLENECK_RISK`: Older architecture or lower single-core CPU paired with high-end GPU (recommends lower TLOD and reduced airport ground traffic).
  - `VRAM_CONSTRAINED`: High resolution paired with $\le 12$ GB VRAM (recommends High/Medium textures and lower Terrain Detail).

---

## 3. The Airliner VRAM Optimization Architecture
- **Technical Problem**: At major payware hub airports, complex airliners (Fenix A320, PMDG 777, FlyByWire A380, Inibuilds A300) combined with Ultra/High textures frequently exceed 15-16 GB of VRAM. DirectX 12 WDDM paging over PCIe then causes 0.5s to 2s stutter freezes.
- **The Solution**: Setting `Texture Resolution` to **LOW** slashes VRAM footprint by **6 to 8 GB**.
- **Avionics Rendering Mechanics**: In modern MSFS aircraft, cockpit screens (PFD, ND, MCDU, ECAM, EICAS) are vector and canvas render targets (CoherentGT/HTML/WASM), completely unaffected by world texture compression. Avionics remain sharp while completely freeing VRAM.
- **VR Impact**: In VR stereo rendering, Low texture resolution prevents compositor dropouts and frame stalls.
- **General Aviation Distinction**: In GA VFR flight, low-altitude scenery clarity is paramount and GA planes consume minimal VRAM ($\le 8$ GB). Thus, High/Ultra is optimal for GA.

---

## 4. MSFS Graphics Settings Architecture (27 Parameters across 7 Rubriques in 2x2 Layout)
To maximize readability and prevent visual clutter, the graphics configuration interface features a 7-rubrique lateral carousel with a spacious $2 \times 2$ grid (4 parameters per page, 3 on the final page):

### Page 1: DISPLAY & SYNC (4 Parameters)
| Parameter | 2D Key | VR Key | Shared? | Input Mode | Optimum Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Full Screen Resolution** | `FullScreenResolution` | Headset Native | **Yes** | Select | Native display resolution |
| **Anti-Aliasing & Upscaling** | `AntiAliasing` / `DLSSMode` | `AntiAliasingVR` / `DLSSModeVR` | No | Select | DLSS Quality / Balanced |
| **Max Frame Rate** | `TargetFrameRate` | `TargetFrameRateVR` | No | **Custom Combobox (Numeric + Presets)** | Display sync divisor (2D) / 1/2 Headset Hz (VR) |
| **V-Sync** | `VSync` | `VSync` | **Yes** | Select | ON for G-Sync/FreeSync pacing |

### Page 2: FRAME GEN & LATENCY (4 Parameters)
| Parameter | 2D Key | VR Key | Shared? | Input Mode | Optimum Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Frame Generation** | `FrameGeneration` | `FrameGenerationVR` | No | Select | DLSSG (2D) / OFF (VR mandatory) |
| **Framerate Multiplier** | `NBFramesToGenerate` | `NBFramesToGenerateVR` | No | Select | 1 (Standard 2X DLSSG) |
| **NVIDIA Reflex** | `Reflex` | `ReflexVR` | No | Select | ON / ON+BOOST (minimizes input latency) |
| **Dynamic Settings** | `DynamicSettings` | `DynamicSettingsVR` | No | Select | OFF (prevents random resolution drops) |

### Page 3: TERRAIN & LOD (4 Parameters)
| Parameter | 2D Key | VR Key | Shared? | Input Mode | Optimum Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Terrain LOD (TLOD)** | `{Terrain LoDFactor}` | `{Terrain LoDFactor}` | No | **Custom Combobox (Numeric + Presets)** | 100-120 (Airliners) / 150-200 (GA) / AutoFPS |
| **Objects LOD (OLOD)** | `{ObjectsLoD LoDFactor}` | `{ObjectsLoD LoDFactor}` | No | **Custom Combobox (Numeric + Presets)** | 100-120 |
| **Off Screen Pre-Caching** | `{OffscreenTerrainPreCaching}` | `{OffscreenTerrainPreCaching}` | No | Select | High / Ultra (prevents camera pan stutters) |
| **Displacement Mapping** | `{DisplacementMapping Enabled}` | `{DisplacementMapping Enabled}` | No | Select | OFF (spares GPU compute & VRAM) |

### Page 4: ENVIRONMENT & FLORA (4 Parameters)
| Parameter | 2D Key | VR Key | Shared? | Input Mode | Optimum Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Buildings Quality** | `{Buildings Quality}` | `{Buildings Quality}` | No | Select | High / Ultra |
| **Trees Quality** | `{Procedural TreesQuality}` | `{Procedural TreesQuality}` | No | Select | High |
| **Grass & Bushes** | `{Procedural GrassQuality}` | `{Procedural GrassQuality}` | No | Select | Low / Medium (Airliners) / High (GA) |
| **Water Waves Simulation** | `{Water FFTSize}` | `{Water FFTSize}` | No | Select | High (512) (2D) / Medium (256) (VR) |

### Page 5: SHADOWS & LIGHTS (4 Parameters)
| Parameter | 2D Key | VR Key | Shared? | Input Mode | Optimum Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Shadow Maps Resolution** | `{Shadows Size}` | `{Shadows Size}` | No | Select | High (1536) (2D) / Medium (1024) (VR) |
| **Terrain Shadows** | `{HeightFieldShadows Size}` | `{HeightFieldShadows Size}` | No | Select | High (512) (2D) / Medium (256) (VR) |
| **Contact Shadows** | `{ContactShadows Quality}` | `{ContactShadows Quality}` | No | Select | High (2D) / Medium (VR) |
| **Volumetric Lights** | `{VolumetricLights Quality}` | `{VolumetricLights Quality}` | No | Select | High (2D) / Low-Medium (VR) |

### Page 6: COCKPIT & AVIONICS (4 Parameters)
| Parameter | 2D Key | VR Key | Shared? | Input Mode | Optimum Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Texture Resolution** | `{Texture Quality}` | `{Texture Quality}` | No | Select | Low (Airliners - VRAM Optimization) / High-Ultra (GA) |
| **Glass Cockpit Refresh** | `{GlassCockpitsRefreshRate Quality}` | `{GlassCockpitsRefreshRate Quality}` | No | Select | Medium / Low (Airliners) / High (GA) |
| **Ambient Occlusion (SSAO)** | `{SSAO Quality}` | `{SSAO Quality}` | No | Select | High (2D) / Low-Medium (VR) |
| **Windshield Effects** | `{WindShield Quality}` | `{WindShield Quality}` | No | Select | High / Ultra |

### Page 7: WEATHER & REFLECTIONS (3 Parameters)
| Parameter | 2D Key | VR Key | Shared? | Input Mode | Optimum Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Volumetric Clouds** | `{VolumetricClouds Quality}` | `{VolumetricClouds Quality}` | No | Select | High |
| **Screen Reflections (SSR)** | `{SSR Quality}` | `{SSR Quality}` | No | Select | High (2D) / Low-Medium (VR) |
| **Anisotropic Filtering** | `{Texture MaxAnisotropy}` | `{Texture MaxAnisotropy}` | No | Select | 16X |

---

## 5. Ergonomics, Card Layout & Option Color-Coding Design
1. **Streamlined Card Header Layout**:
   - Setting title on the left (`text-sm font-mono font-bold text-slate-100 uppercase`).
   - Right-side cluster:
     - `[ SHARED ]` badge (when parameter is shared between 2D and VR), positioned immediately to the left of the rating tag with matching height and typography (`px-2 py-0.5 rounded text-xs font-mono font-bold bg-slate-800 text-slate-300`).
     - `[ OPTIMUM / ACCEPTABLE / HAZARD ]` tag (`px-2.5 py-0.5 rounded text-xs font-mono font-bold uppercase`).
     - `[ i ]` information button (`w-6 h-6 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-mono text-xs font-bold`) triggering the in-depth technical modal.
2. **De-Cluttered Card Footers**:
   - Redundant bottom trade-off pills (`+ PRO` / `- CON`) have been eliminated from the card surface, preventing card height distortion and dropdown clipping.
   - All trade-off analysis and technical explanations are centralized inside the dedicated `[ i ]` modal.
3. **Color-Coded Dropdown & Combobox Options**:
   - Options are classified and styled according to their impact:
     - **Optimum**: Emerald green (`text-emerald-400 font-bold`).
     - **Acceptable**: Amber (`text-amber-300 font-bold`).
     - **Hazard / Suboptimal**: Rose / Red (`text-rose-400 font-bold`).
   - In combobox popover menus, each option is accompanied by a color-coded indicator dot (`bg-emerald-400`, `bg-amber-400`, `bg-rose-400`) for immediate visual identification.

---

## 6. Dedicated Setting Information Modal Design (`[ i ]`)
Clicking the `[ i ]` button opens a clean, solid, flat modal (`#opt-setting-info-modal`) presenting structured technical intelligence:
1. **MSFS Technical Purpose**: Explains what the setting calculates in the engine.
2. **Hardware Impact Breakdown**:
   - *CPU MainThread*: Latency, thread synchronization, draw call overhead.
   - *GPU & VRAM*: Shading workload, texture memory footprint, compute shader passes.
3. **Flight Profile Guidance**:
   - *IFR Airliners*: Concrete guidance for complex payware airliners (Fenix, PMDG, FlyByWire, iniBuilds).
   - *VFR General Aviation*: Advice for light aircraft and visual navigation.
4. **Comparative Option Evaluation**:
   - Structured list of all options with their assigned rating badges and color-coded status dots.
   - Specific pros and cons associated with each choice.

---

## 7. Multi-Monitor & Cadence Calibration Architecture
1. **Multi-Monitor Discovery**:
   - Automatically enumerates all connected physical displays via Win32 APIs.
   - Detects resolution and exact refresh rates (e.g. 180 Hz, 165 Hz, 144 Hz, 120 Hz, 60 Hz).
2. **Dynamic Active Monitor Selection**:
   - In the Cadence Calibration modal, if two or more monitors are detected, a clean card grid allows the user to select which display runs MSFS.
   - The user's selection is persisted in `localStorage` (`sceneryx_selected_display_id`).
   - The active display is also switchable on-the-fly in the **MY RIG** hardware card.
3. **Harmonic 1/2 Sync Pacing Calculation**:
   - Automatically computes the optimal 1/2 sync target frame rate for the chosen display:
     - 240 Hz $\rightarrow$ 120 FPS
     - 180 Hz $\rightarrow$ 90 FPS
     - 165 Hz $\rightarrow$ 82 FPS
     - 144 Hz $\rightarrow$ 72 FPS
     - 120 Hz $\rightarrow$ 60 FPS
   - Updates `TargetFrameRate` in `UserCfg.opt` upon selection.
4. **De-Cluttered Cadence Calibration Modal**:
   - Removed bulky text blocks and redundant descriptions.
   - Removed "Native" and confusing liserets.
   - Clean single-line target badges: `90 FPS (1/2 SYNC)` and `36 FPS (1/2 SYNC)`.

---

## 8. Staging, Rollback & Backup System Design
- **In-Memory Staging Architecture (Zero Premature Disk Writes)**:
  - Modifying dropdowns or typing custom values in the UI updates an in-memory staging dictionary (`_staged_user_cfg_settings[mode][key] = val`) without touching `UserCfg.opt` on disk.
  - The live diagnostics matrix recalculates dynamically in-memory, updating ratings and tags instantly without writing any backup file or touching disk storage.
  - Disk writes and backup generation are strictly deferred until explicit confirmation.
- **Pristine Original Backup Preservation (`UserCfg.opt.original`)**:
  - Automatically and silently created upon the first launch of SceneryX before any diagnostics or optimizations can touch `UserCfg.opt`.
  - Permanently preserves the user's authentic personal configuration. If previous backups exist, it captures the earliest timestamped file.
  - Protected from deletion: `delete_user_cfg_backup` strictly prevents removing `UserCfg.opt.original`.
- **Single-Pass Safety Backup on Validation**:
  - Clicking `OPTIMIZE PROFILE` triggers the commit phase: exactly one timestamped safety backup (`UserCfg.opt.backup_YYYYMMDD_HHMMSS`) is generated before applying the calibrated profile and any staged overrides to `UserCfg.opt`.
- **Unified Two-Way Modal Navigation**:
  - Consolidates profile feedback and backup rollback into a single window with seamless view switching:
    - **View A (Feedback)**: Clean uppercase header `GRAPHICS PROFILE OPTIMIZED` without icon badge or subtitle clutter. Displays optimization results and applied profile details. Bottom actions feature a standard blue, icon-free `VIEW BACKUPS` button and an `OK` validation button.
    - **View B (Backups Management)**: Features a dedicated `OPEN FOLDER` button (launches Windows Explorer directly targeting `UserCfg.opt`), 1-click `RESTORE`, and an instant `DELETE` button next to each backup.
    - **Backups Footer Ergonomics**: Features a prominent red `RESTORE ORIGINAL CFG` button on the bottom-left allowing instant reversion to pristine pre-SceneryX settings, and the `CLOSE` button (along with `BACK` if navigated from feedback) positioned strictly on the bottom-right.
- **Safety Copy on Rollback**: Restoring any backup or the original file automatically creates a safety snapshot of the active file before overwriting, and clears in-memory staged overrides.
