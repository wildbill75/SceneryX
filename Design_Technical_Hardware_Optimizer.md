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
- **GPU**: Model, dedicated VRAM capacity, driver version, Re-Size BAR state.
- **Primary Display (Monitor)**: Native resolution (e.g. `2560 x 1440 Native`) and native refresh rate frequency in Hz (e.g. `165 HZ REFRESH RATE`), acquired via Windows `EnumDisplaySettingsW` system API.
- **VR Headset Scanner Engine**:
  - Automatically scans the system at startup for active or configured Virtual Reality headsets across major PCVR ecosystems:
    - **Pimax**: Detects Pimax Crystal / Crystal Light / 8KX from Pimax runtime (`P3CONFIG.json`, `profile.json`, and live service logs), extracting active refresh rates (e.g. `72 Hz`, `80 Hz`, `90 Hz`, `120 Hz`).
    - **SteamVR**: Inspects `steamvr.vrsettings` for `LastKnown` HMD model and manufacturer (Valve Index, HTC Vive, Bigscreen Beyond).
    - **Meta / Oculus**: Inspects Oculus Runtime and Virtual Desktop configurations (Meta Quest 2/3/Pro, Rift S).
    - **Windows Mixed Reality**: Inspects Holographic system configurations (HP Reverb G2).
  - Reports detected headset model and native cadence directly in the dedicated 6th card of **MY RIG** (e.g. `Pimax Crystal Light - 72 Hz Active`), and auto-initializes the VR refresh rate sync target.
- **System Memory (RAM)**: Capacity, clock speed (MHz), XMP activation.
- **Accelerators & Drivers**: Hardware-Accelerated GPU Scheduling (HAGS), Re-Size BAR, and DLSS runtime version.
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
| **Grass & Bushes** | `{Procedural GrassQuality}` | `{Procedural GrassQuality}` | No | Select | High / Medium |
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
| **Texture Resolution** | `{Texture Quality}` | `{Texture Quality}` | No | Select | Low (Airliners - Axel LFBO) / High-Ultra (GA) |
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

## 5. Ergonomics, Tag Nomenclature & Action Placement Design
1. **Wider Window Architecture (1180px)**:
   - Floating window width expanded from `940px` to `1180px` (`w-[1180px] max-w-[96vw]`), providing generous breathing room for cards and preventing any horizontal cramping.
2. **Airy Header & Centered Control Pills (Row 1B)**:
   - **Row 1**: Displays clean uppercase section title `MSFS GRAPHICS SETTINGS` without subtitle clutter.
   - **Row 1B**: Houses a centered, unified controls line with `[ 2D DISPLAY / VR HEADSET ]`, `[ IFR AIRLINER / VFR GA ]`, `VR HZ: [ 72 Hz / 80 Hz / 90 Hz / 120 Hz ]`, and a solid `AUTOFPS` pill (solid green `bg-emerald-600` when dynamic sync is active, solid dark gray `bg-slate-800` when inactive, without blinking artifacts).
   - **Row 2**: Displays a streamlined segmented tab bar with exactly seven clean rubrique pills: `DISPLAY & SYNC`, `FRAME GEN & LATENCY`, `TERRAIN & LOD`, `ENVIRONMENT & FLORA`, `SHADOWS & LIGHTS`, `COCKPIT & AVIONICS`, and `WEATHER & REFLECTIONS`. Structured with `flex-nowrap justify-between gap-1.5` so all 7 tabs sit strictly on a single horizontal row without wrapping.
3. **Carousel Viewport (2x2 Grid per Rubrique with Enhanced Readability)**:
   - Houses seven full-width $2 \times 2$ grid panels (4 cards each, 3 on final page) sliding along the X-axis via CSS transform transitions (`translateX(-0%)` to `translateX(-600%)`).
   - Cards feature expanded internal padding (`p-3.5`), high-contrast uppercase titles (`text-sm font-bold text-slate-100`), and generous vertical spacing.
4. **Custom Dark Combobox with Full Preset Visibility**:
   - Replaces the native `<datalist>` dropdown with a custom dark-themed combobox popover menu.
   - On click or chevron toggle, the dropdown renders **all** preset options without filtering out non-matching values.
   - Presets highlight the `CURRENT` active value with a dedicated cyan badge.
   - Users can either click a preset for instant application or freely type custom numeric values (e.g. `82` or `125`), validated with min/max thresholds.
5. **Strict Single-Word Uppercase Tag System (Enlarged)**:
   - Every graphics setting badge displays strictly one single uppercase word: `OPTIMUM`, `ACCEPTABLE`, `SUBOPTIMAL`, or `HAZARD`.
   - Prominently sized (`text-xs font-black px-3 py-1`) for effortless legibility.
   - Explanations in parentheses are banned entirely from the tag label.
   - Solid, full-opacity background colors only: `bg-emerald-600`, `bg-amber-600`, `bg-orange-600`, `bg-rose-600`. All stroke, border, and glass opacity effects are removed.
   - Hovering over any tag reveals a dedicated tooltip explaining the specific rationale for the assigned rating (e.g. Axel LFBO VRAM savings or MainThread throttling).
6. **Structured 3-Part Setting Tooltips**:
   - Each card provides a structured 3-part tooltip:
     - `Description`: Exact functional description of what the graphics parameter controls.
     - `Current`: Analysis of the currently selected value and its system impact.
     - `Recommendation`: Concrete, actionable advice tailored to hardware capabilities and flight mission profile.
7. **Uniform Combobox & Select Dropdown Chevrons**:
   - Both standard `<select>` dropdowns and editable text/numeric fields (`tlod`, `olod`, `max_frame_rate`) share an identical SVG down-arrow chevron (`w-4 h-4 text-slate-400`).
   - The chevron remains visible 100% of the time, in both free text typing mode and dropdown selection mode. Native browser indicators are hidden via CSS for visual consistency.
8. **Bottom-Right Action Placement**:
   - `ROLLBACK` and `OPTIMIZE PROFILE` action buttons are positioned at the bottom-right of the graphics settings block (beneath the carousel viewport).
   - Icons are stripped from both buttons, adopting a clean, solid, uppercase typography (`text-sm font-black` for Optimize Profile).

---

## 6. Staging, Rollback & Backup System Design
- **In-Memory Staging Architecture (Zero Premature Disk Writes)**:
  - Modifying dropdowns or typing custom values in the UI updates an in-memory staging dictionary (`_staged_user_cfg_settings[mode][key] = val`) without touching `UserCfg.opt` on disk.
  - The live diagnostics matrix recalculates dynamically in-memory, updating ratings, tags, and trade-off pills instantly without writing any backup file or touching disk storage.
  - Disk writes and backup generation are strictly deferred until explicit confirmation.
- **Single-Pass Safety Backup on Validation**:
  - Clicking `OPTIMIZE PROFILE` triggers the commit phase: exactly one timestamped safety backup (`UserCfg.opt.backup_YYYYMMDD_HHMMSS`) is generated before applying the calibrated profile and any staged overrides to `UserCfg.opt`.
- **Unified Two-Way Modal Navigation (Zero Modal Stacking)**:
  - Consolidates profile feedback and backup rollback into a single window with seamless view switching:
    - **View A (Feedback)**: Displays optimization results and applied profile details. Clicking `VIEW BACKUPS` smoothly switches to View B inside the same modal container.
    - **View B (Backups Management)**: Features a dedicated `OPEN FOLDER` button (opens the UserCfg.opt directory in Windows Explorer), 1-click `RESTORE`, and an instant `DELETE` button next to each backup. Clicking `BACK` returns directly to View A.
  - Backups list features clean single-line timestamp titles (extraneous filename/size subtitles stripped), solid `MOST RECENT` badges, and full English localization (`CLOSE`, `BACK`, `RESTORE`, `DELETE`).
- **Safety Copy on Rollback**: Restoring a backup automatically creates a safety snapshot of the active file before overwriting, and clears in-memory staged overrides.

---

## 7. Trade-Off (Pour & Contre) System & Confirmation Modal Design
1. **Dynamic Trade-Off Pills (Pour & Contre - High Contrast & Enlarged)**:
   - Each setting card conveys the exact visual vs. frame pacing trade-off via two solid, compact pills positioned immediately below the input field:
     - **Pro Pill (`+ PRO`)**: Solid emerald (`bg-emerald-600 text-white font-bold text-[11px] px-2.5 py-1 rounded-md`), highlighting the immediate performance or visual advantage (e.g. `+ MAX RUNWAY FPS`, `+ FREES 6-8GB VRAM`, `+ 2X SMOOTHNESS`). Hovering displays a detailed explanation.
     - **Con Pill (`- CON`)**: Solid slate (`bg-slate-700 text-slate-100 font-bold text-[11px] px-2.5 py-1 rounded-md`), detailing what is sacrificed (e.g. `- FLAT RUNWAY EDGE`, `- SOFTER LIVERY`, `- 10MS INPUT LAG`). Hovering displays a detailed explanation.
   - **Mission-Aware Calibration**:
     - *Airliners (IFR)*: Parameters prioritize CPU MainThread and VRAM preservation. Grass at `Low` or `Medium` is rated `OPTIMUM` because 3D grass geometry is wasted on concrete runways while consuming critical draw calls.
     - *General Aviation (VFR)*: Parameters prioritize low-altitude visual richness. Grass at `High` or `Ultra` is rated `OPTIMUM` for bush and grass runway realism.
2. **All-Caps Card Typography**:
   - Setting card headers are rendered strictly in uppercase (e.g. `GRASS & BUSHES`, `TEXTURE RESOLUTION`, `TERRAIN LOD (TLOD)`).
   - Card rating tags are single uppercase words (`OPTIMUM`, `ACCEPTABLE`, `SUBOPTIMAL`, `HAZARD`) with solid background colors and zero parenthetical text.
3. **Instant Optimization Confirmation Modal**:
   - Triggered upon clicking `OPTIMIZE PROFILE`.
   - Renders a focused dialog displaying the target display mode, active flight mission profile, generated safety backup path, and an icon-free summary list with solid `[OK]` badges.


