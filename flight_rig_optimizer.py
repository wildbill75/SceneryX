#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SceneryX Flight Rig Optimizer & Hardware Intelligence Engine (v1.0.1)
Module autonome d'auto-détection matérielle, de calcul de synchronisation d'affichage (Frame Pacing),
de calibrage VRAM / CPU et de génération de profils optimisés par studio d'avionique.
"""

import os
import sys
import json
import re
import ctypes
import ctypes.wintypes
import subprocess
import winreg
from typing import Dict, Any, List, Optional, Tuple

# Forçage encodage UTF-8 pour la console Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

CREATE_NO_WINDOW = 0x08000000

# ==============================================================================
# BASE DE DONNÉES MATÉRIELLE (CATÉGORIES POUR COMBOBOX FILTRABLE)
# ==============================================================================

POPULAR_CPUS = {
    "Intel Core 14th Gen": [
        "Intel Core i9-14900KS (24c/32t - 6.2 GHz)",
        "Intel Core i9-14900K (24c/32t - 6.0 GHz)",
        "Intel Core i9-14900KF (24c/32t - 6.0 GHz)",
        "Intel Core i7-14700K (20c/28t - 5.6 GHz)",
        "Intel Core i7-14700KF (20c/28t - 5.6 GHz)",
        "Intel Core i5-14600K (14c/20t - 5.3 GHz)",
    ],
    "Intel Core 13th Gen": [
        "Intel Core i9-13900KS (24c/32t - 6.0 GHz)",
        "Intel Core i9-13900K (24c/32t - 5.8 GHz)",
        "Intel Core i9-13900KF (24c/32t - 5.8 GHz)",
        "Intel Core i7-13700K (16c/24t - 5.4 GHz)",
        "Intel Core i7-13700KF (16c/24t - 5.4 GHz)",
        "Intel Core i5-13600K (14c/20t - 5.1 GHz)",
    ],
    "Intel Core 12th Gen": [
        "Intel Core i9-12900KS (16c/24t - 5.5 GHz)",
        "Intel Core i9-12900K (16c/24t - 5.2 GHz)",
        "Intel Core i7-12700K (12c/20t - 5.0 GHz)",
        "Intel Core i5-12600K (10c/16t - 4.9 GHz)",
    ],
    "AMD Ryzen 9000 Series (Zen 5)": [
        "AMD Ryzen 9 9950X (16c/32t - 5.7 GHz)",
        "AMD Ryzen 9 9900X (12c/24t - 5.6 GHz)",
        "AMD Ryzen 7 9800X3D (8c/16t - 3D V-Cache)",
        "AMD Ryzen 7 9700X (8c/16t - 5.5 GHz)",
        "AMD Ryzen 5 9600X (6c/12t - 5.4 GHz)",
    ],
    "AMD Ryzen 7000 Series (Zen 4)": [
        "AMD Ryzen 7 7800X3D (8c/16t - 3D V-Cache)",
        "AMD Ryzen 9 7950X3D (16c/32t - 3D V-Cache)",
        "AMD Ryzen 9 7900X3D (12c/24t - 3D V-Cache)",
        "AMD Ryzen 9 7950X (16c/32t - 5.7 GHz)",
        "AMD Ryzen 7 7700X (8c/16t - 5.4 GHz)",
        "AMD Ryzen 5 7600X (6c/12t - 5.3 GHz)",
    ],
    "AMD Ryzen 5000 Series (Zen 3)": [
        "AMD Ryzen 7 5800X3D (8c/16t - 3D V-Cache)",
        "AMD Ryzen 7 5700X3D (8c/16t - 3D V-Cache)",
        "AMD Ryzen 9 5950X (16c/32t - 4.9 GHz)",
        "AMD Ryzen 9 5900X (12c/24t - 4.8 GHz)",
        "AMD Ryzen 7 5800X (8c/16t - 4.7 GHz)",
        "AMD Ryzen 5 5600X (6c/12t - 4.6 GHz)",
    ]
}

POPULAR_GPUS = {
    "NVIDIA GeForce RTX 50 Series": [
        "NVIDIA GeForce RTX 5090 (32 Go GDDR7)",
        "NVIDIA GeForce RTX 5080 (16 Go GDDR7)",
        "NVIDIA GeForce RTX 5070 Ti (16 Go GDDR7)",
        "NVIDIA GeForce RTX 5070 (12 Go GDDR7)",
    ],
    "NVIDIA GeForce RTX 40 Series": [
        "NVIDIA GeForce RTX 4090 (24 Go GDDR6X)",
        "NVIDIA GeForce RTX 4080 Super (16 Go GDDR6X)",
        "NVIDIA GeForce RTX 4080 (16 Go GDDR6X)",
        "NVIDIA GeForce RTX 4070 Ti Super (16 Go GDDR6X)",
        "NVIDIA GeForce RTX 4070 Ti (12 Go GDDR6X)",
        "NVIDIA GeForce RTX 4070 Super (12 Go GDDR6X)",
        "NVIDIA GeForce RTX 4070 (12 Go GDDR6X)",
        "NVIDIA GeForce RTX 4060 Ti (16 Go GDDR6)",
        "NVIDIA GeForce RTX 4060 Ti (8 Go GDDR6)",
        "NVIDIA GeForce RTX 4060 (8 Go GDDR6)",
    ],
    "NVIDIA GeForce RTX 30 Series": [
        "NVIDIA GeForce RTX 3090 Ti (24 Go GDDR6X)",
        "NVIDIA GeForce RTX 3090 (24 Go GDDR6X)",
        "NVIDIA GeForce RTX 3080 Ti (12 Go GDDR6X)",
        "NVIDIA GeForce RTX 3080 (12 Go GDDR6X)",
        "NVIDIA GeForce RTX 3080 (10 Go GDDR6X)",
        "NVIDIA GeForce RTX 3070 Ti (8 Go GDDR6X)",
        "NVIDIA GeForce RTX 3070 (8 Go GDDR6)",
        "NVIDIA GeForce RTX 3060 Ti (8 Go GDDR6)",
        "NVIDIA GeForce RTX 3060 (12 Go GDDR6)",
    ],
    "AMD Radeon RX 7000 Series": [
        "AMD Radeon RX 7900 XTX (24 Go GDDR6)",
        "AMD Radeon RX 7900 XT (20 Go GDDR6)",
        "AMD Radeon RX 7900 GRE (16 Go GDDR6)",
        "AMD Radeon RX 7800 XT (16 Go GDDR6)",
        "AMD Radeon RX 7700 XT (12 Go GDDR6)",
        "AMD Radeon RX 7600 XT (16 Go GDDR6)",
    ],
    "AMD Radeon RX 6000 Series": [
        "AMD Radeon RX 6950 XT (16 Go GDDR6)",
        "AMD Radeon RX 6900 XT (16 Go GDDR6)",
        "AMD Radeon RX 6800 XT (16 Go GDDR6)",
        "AMD Radeon RX 6800 (16 Go GDDR6)",
        "AMD Radeon RX 6700 XT (12 Go GDDR6)",
    ]
}

AIRCRAFT_STUDIO_PROFILES = {
    "fslabs": {
        "id": "fslabs",
        "name": "Flight Sim Labs (FSLabs)",
        "aircraft": ["A321-X", "A320-X", "A319-X", "Concorde"],
        "architecture": "Simulation physique ultra-profonde (circuits hydrauliques, thermodynamique, Fly-By-Wire millimétrique)",
        "bottleneck_tendency": "MainThread CPU & Cache L3 (très lourd)",
        "vram_demand": "High",
        "recommended_terrain_detail": "Low",
        "recommended_t_lod_base": 110,
        "recommended_t_lod_cruise": 220,
        "recommended_o_lod_cruise": 20,
        "strict_fps_lock_mandatory": True,
        "direct_ab_mandatory": True,
        "advice": "Verrouillage strict 45 FPS moteur (90 FPS affichés) impératif. SceneryX Direct A -> B requis pour libérer le bus mémoire."
    },
    "fenix": {
        "id": "fenix",
        "name": "Fenix Simulations",
        "aircraft": ["A319", "A320", "A321"],
        "architecture": "Avionique déportée ProSim + rendu DirectX externe pour les écrans",
        "bottleneck_tendency": "VRAM & CoherentGTUIThread (+1.5 Go VRAM pour les écrans)",
        "vram_demand": "Extreme",
        "recommended_terrain_detail": "Low",
        "recommended_t_lod_base": 120,
        "recommended_t_lod_cruise": 250,
        "recommended_o_lod_cruise": 20,
        "strict_fps_lock_mandatory": True,
        "direct_ab_mandatory": True,
        "advice": "Régler le Display Rendering de l'app Fenix sur CPU ou Balanced pour préserver la VRAM de la carte graphique."
    },
    "pmdg": {
        "id": "pmdg",
        "name": "PMDG",
        "aircraft": ["B737-600/700/800/900", "B777-300ER", "B777-F", "DC-6"],
        "architecture": "Code pur C++ compilé en WASM natif",
        "bottleneck_tendency": "MainThread CPU équilibré / VRAM très économe",
        "vram_demand": "Low-Medium",
        "recommended_terrain_detail": "Medium-High",
        "recommended_t_lod_base": 140,
        "recommended_t_lod_cruise": 280,
        "recommended_o_lod_cruise": 30,
        "strict_fps_lock_mandatory": False,
        "direct_ab_mandatory": False,
        "advice": "Très économe en VRAM. Permet de monter le TLOD ou les textures sans risque de paging D3D12."
    },
    "inibuilds": {
        "id": "inibuilds",
        "name": "iniBuilds",
        "aircraft": ["A300-600R", "A310", "A320neo v2", "A350"],
        "architecture": "Cockpit et cabine 3D ultra-détaillés (textures 8K/4K volumineuses)",
        "bottleneck_tendency": "VRAM élevée & géométrie complexe",
        "vram_demand": "High-Extreme",
        "recommended_terrain_detail": "Low",
        "recommended_t_lod_base": 120,
        "recommended_t_lod_cruise": 240,
        "recommended_o_lod_cruise": 20,
        "strict_fps_lock_mandatory": True,
        "direct_ab_mandatory": True,
        "advice": "Désactiver les textures passagers/cabine dans l'EFB si votre GPU a 16 Go de VRAM ou moins."
    },
    "flybywire": {
        "id": "flybywire",
        "name": "FlyByWire Simulations",
        "aircraft": ["A32NX", "A380X"],
        "architecture": "Avionique c-wasm + écrans React / JavaScript CoherentGT",
        "bottleneck_tendency": "CoherentGTUIThread (charge fil CPU d'interface)",
        "vram_demand": "Medium",
        "recommended_terrain_detail": "Medium",
        "recommended_t_lod_base": 125,
        "recommended_t_lod_cruise": 250,
        "recommended_o_lod_cruise": 25,
        "strict_fps_lock_mandatory": False,
        "direct_ab_mandatory": False,
        "advice": "Modérer la fréquence de rafraîchissement des écrans dans les options EFB et fermer les barres d'outils superflues."
    },
    "justflight": {
        "id": "justflight",
        "name": "Just Flight",
        "aircraft": ["BAe 146", "Fokker F28", "PA-28", "Tomahawk"],
        "architecture": "Cadrans à aiguilles complexes et centaine de contacteurs 3D",
        "bottleneck_tendency": "Manipulators (clickspots en cockpit 3D)",
        "vram_demand": "Medium",
        "recommended_terrain_detail": "Medium",
        "recommended_t_lod_base": 130,
        "recommended_t_lod_cruise": 260,
        "recommended_o_lod_cruise": 25,
        "strict_fps_lock_mandatory": False,
        "direct_ab_mandatory": False,
        "advice": "Excellente optimisation générale, attention aux clickspots en cockpit 3D."
    },
    "asobo": {
        "id": "asobo",
        "name": "Asobo / Working Title",
        "aircraft": ["Citation Longitude", "TBM 930", "G1000/G3000 General Aviation"],
        "architecture": "Code natif Microsoft hautement optimisé",
        "bottleneck_tendency": "Neutre / Minimal",
        "vram_demand": "Low",
        "recommended_terrain_detail": "High",
        "recommended_t_lod_base": 150,
        "recommended_t_lod_cruise": 300,
        "recommended_o_lod_cruise": 50,
        "strict_fps_lock_mandatory": False,
        "direct_ab_mandatory": False,
        "advice": "Empreinte minimale sur le simulateur. Vous pouvez pousser les réglages visuels au maximum."
    }
}


# ==============================================================================
# SONDAGE MATÉRIEL & SYSTÈME WINDOWS
# ==============================================================================

def detect_cpu_info() -> Dict[str, Any]:
    """Détecte le processeur, le nombre de cœurs/threads et la vitesse via WMI/PowerShell."""
    result = {
        "name": "Unknown CPU",
        "cores": 0,
        "threads": 0,
        "max_clock_mhz": 0,
        "raw_string": ""
    }
    try:
        ps_cmd = 'Get-CimInstance Win32_Processor | Select-Object -Property Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed | ConvertTo-Json'
        out = subprocess.check_output(['powershell', '-NoProfile', '-Command', ps_cmd], text=True, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
        data = json.loads(out)
        if isinstance(data, list):
            data = data[0]
        result["name"] = data.get("Name", "").strip()
        result["cores"] = data.get("NumberOfCores", 0)
        result["threads"] = data.get("NumberOfLogicalProcessors", 0)
        result["max_clock_mhz"] = data.get("MaxClockSpeed", 0)
        result["raw_string"] = f"{result['name']} ({result['cores']}C/{result['threads']}T)"
    except Exception:
        result["name"] = os.environ.get("PROCESSOR_IDENTIFIER", "Intel/AMD Processor")
        result["threads"] = os.cpu_count() or 8
        result["raw_string"] = result["name"]
    return result


def detect_gpu_info() -> Dict[str, Any]:
    """Détecte la carte graphique NVIDIA/AMD, VRAM totale et Re-Size BAR."""
    result = {
        "name": "Unknown GPU",
        "vram_total_mb": 0,
        "vram_total_gb": 0.0,
        "driver_version": "Unknown",
        "bar1_memory_mb": 0,
        "is_rbar_active": False,
        "vendor": "Unknown"
    }
    
    # 1. Requête standard nvidia-smi pour nom, pilote et VRAM totale
    try:
        cmd = [
            'nvidia-smi',
            '--query-gpu=name,driver_version,memory.total',
            '--format=csv,noheader,nounits'
        ]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW).strip()
        parts = [p.strip() for p in out.split(',')]
        if len(parts) >= 3:
            result["name"] = parts[0]
            result["driver_version"] = parts[1]
            result["vram_total_mb"] = int(float(parts[2]))
            result["vram_total_gb"] = round(result["vram_total_mb"] / 1024.0, 1)
            result["vendor"] = "NVIDIA"
    except Exception:
        pass

    # 2. Requête nvidia-smi pour Re-Size BAR (BAR1 Memory Usage)
    if result["vendor"] == "NVIDIA":
        try:
            cmd_bar = ['nvidia-smi', '-q', '-d', 'MEMORY']
            out_bar = subprocess.check_output(cmd_bar, text=True, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
            m_bar = re.search(r'BAR1 Memory Usage\s+Total\s+:\s+(\d+)\s+MiB', out_bar)
            if m_bar:
                result["bar1_memory_mb"] = int(m_bar.group(1))
                # BAR1 >= 2048 MiB indique que Re-Size BAR est actif
                result["is_rbar_active"] = result["bar1_memory_mb"] >= 2048
            return result
        except Exception:
            return result

    # 3. Fallback via PowerShell / WMI pour AMD / Intel / générique
    try:
        ps_cmd = 'Get-CimInstance Win32_VideoController | Select-Object -Property Name, DriverVersion, AdapterRAM | ConvertTo-Json'
        out = subprocess.check_output(['powershell', '-NoProfile', '-Command', ps_cmd], text=True, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
        data = json.loads(out)
        if isinstance(data, list):
            data = data[0]
        result["name"] = data.get("Name", "Unknown GPU").strip()
        result["driver_version"] = data.get("DriverVersion", "Unknown")
        raw_ram = data.get("AdapterRAM", 0)
        if raw_ram and raw_ram > 0:
            result["vram_total_mb"] = int(raw_ram / (1024 * 1024))
            result["vram_total_gb"] = round(result["vram_total_mb"] / 1024.0, 1)
        if "NVIDIA" in result["name"].upper():
            result["vendor"] = "NVIDIA"
        elif "AMD" in result["name"].upper() or "RADEON" in result["name"].upper():
            result["vendor"] = "AMD"
    except Exception:
        pass

    return result


def detect_ram_and_xmp() -> Dict[str, Any]:
    """Détecte la RAM totale, la fréquence en MHz et l'activation du profil XMP/EXPO."""
    result = {
        "total_gb": 0.0,
        "speed_mhz": 0,
        "is_xmp_active": False,
        "stick_count": 0
    }
    try:
        ps_cmd = 'Get-CimInstance Win32_PhysicalMemory | Select-Object -Property Capacity, Speed, ConfiguredClockSpeed | ConvertTo-Json'
        out = subprocess.check_output(['powershell', '-NoProfile', '-Command', ps_cmd], text=True, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
        data = json.loads(out)
        if not isinstance(data, list):
            data = [data]
        
        total_bytes = 0
        speeds = []
        for stick in data:
            cap = int(stick.get("Capacity", 0))
            total_bytes += cap
            speed = int(stick.get("ConfiguredClockSpeed") or stick.get("Speed") or 0)
            if speed > 0:
                speeds.append(speed)
        
        result["total_gb"] = round(total_bytes / (1024**3), 1)
        result["stick_count"] = len(data)
        if speeds:
            result["speed_mhz"] = max(speeds)
            if result["speed_mhz"] >= 3200:
                result["is_xmp_active"] = True
    except Exception:
        pass
    return result


def detect_display_info() -> Dict[str, Any]:
    """Détecte la résolution et le taux de rafraîchissement (Hz) du moniteur principal."""
    result = {
        "width": 1920,
        "height": 1080,
        "refresh_rate_hz": 60.0,
        "refresh_rate_int": 60,
        "formatted": "1920x1080 @ 60 Hz"
    }
    class DEVMODEW(ctypes.Structure):
        _fields_ = [
            ('dmDeviceName', ctypes.c_wchar * 32),
            ('dmSpecVersion', ctypes.wintypes.WORD),
            ('dmDriverVersion', ctypes.wintypes.WORD),
            ('dmSize', ctypes.wintypes.WORD),
            ('dmDriverExtra', ctypes.wintypes.WORD),
            ('dmFields', ctypes.wintypes.DWORD),
            ('dmOrientation', ctypes.c_short),
            ('dmPaperSize', ctypes.c_short),
            ('dmPaperLength', ctypes.c_short),
            ('dmPaperWidth', ctypes.c_short),
            ('dmScale', ctypes.c_short),
            ('dmCopies', ctypes.c_short),
            ('dmDefaultSource', ctypes.c_short),
            ('dmPrintQuality', ctypes.c_short),
            ('dmColor', ctypes.c_short),
            ('dmDuplex', ctypes.c_short),
            ('dmYResolution', ctypes.c_short),
            ('dmTTOption', ctypes.c_short),
            ('dmCollate', ctypes.c_short),
            ('dmFormName', ctypes.c_wchar * 32),
            ('dmLogPixels', ctypes.wintypes.WORD),
            ('dmBitsPerPel', ctypes.wintypes.DWORD),
            ('dmPelsWidth', ctypes.wintypes.DWORD),
            ('dmPelsHeight', ctypes.wintypes.DWORD),
            ('dmDisplayFlags', ctypes.wintypes.DWORD),
            ('dmDisplayFrequency', ctypes.wintypes.DWORD),
            ('dmICMMethod', ctypes.wintypes.DWORD),
            ('dmICMIntent', ctypes.wintypes.DWORD),
            ('dmMediaType', ctypes.wintypes.DWORD),
            ('dmDitherType', ctypes.wintypes.DWORD),
            ('dmReserved1', ctypes.wintypes.DWORD),
            ('dmReserved2', ctypes.wintypes.DWORD),
            ('dmPanningWidth', ctypes.wintypes.DWORD),
            ('dmPanningHeight', ctypes.wintypes.DWORD),
        ]

    try:
        dm = DEVMODEW()
        dm.dmSize = ctypes.sizeof(DEVMODEW)
        ENUM_CURRENT_SETTINGS = -1
        if ctypes.windll.user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(dm)):
            result["width"] = dm.dmPelsWidth
            result["height"] = dm.dmPelsHeight
            result["refresh_rate_int"] = dm.dmDisplayFrequency
            result["refresh_rate_hz"] = float(dm.dmDisplayFrequency)
            result["formatted"] = f"{result['width']}x{result['height']} @ {result['refresh_rate_int']} Hz"
            return result
    except Exception:
        pass

    return result


def detect_windows_hags() -> bool:
    """Vérifie si la planification GPU accélérée (HAGS) est active dans le registre Windows."""
    try:
        key_path = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            val, _ = winreg.QueryValueEx(key, "HwSchMode")
            return val == 2
    except Exception:
        return False


def detect_dlss_version() -> Dict[str, Any]:
    """Détecte la version DLSS et Frame Generation active via DLSS Swapper."""
    result = {
        "version": "Inconnue",
        "frame_gen_version": "Inconnue",
        "source": "Non détecté"
    }
    swapper_db = os.path.expandvars(r"%LOCALAPPDATA%\DLSS Swapper\dlss_swapper.db")
    if os.path.exists(swapper_db):
        try:
            import sqlite3
            conn = sqlite3.connect(swapper_db)
            cur = conn.cursor()
            
            # Recherche de la dernière version nvngx_dlss.dll
            cur.execute("""
                SELECT asset_version FROM game_history 
                WHERE asset_path LIKE '%Limitless%nvngx_dlss.dll%' OR asset_path LIKE '%Flight%nvngx_dlss.dll%'
                ORDER BY rowid DESC LIMIT 1
            """)
            row = cur.fetchone()
            if row and row[0]:
                result["version"] = row[0]
                result["source"] = "DLSS Swapper (MSFS 2024)"

            # Recherche de la version Frame Generation nvngx_dlssg.dll
            cur.execute("""
                SELECT asset_version FROM game_history 
                WHERE asset_path LIKE '%Limitless%nvngx_dlssg.dll%' OR asset_path LIKE '%Flight%nvngx_dlssg.dll%'
                ORDER BY rowid DESC LIMIT 1
            """)
            row_g = cur.fetchone()
            if row_g and row_g[0]:
                result["frame_gen_version"] = row_g[0]

            conn.close()
            return result
        except Exception:
            pass

    return result


def detect_msfs_user_cfg() -> Dict[str, Any]:
    """Analyse les réglages actuels de UserCfg.opt de MSFS 2024 / 2020."""
    result = {
        "found": False,
        "path": "",
        "dlss_mode": "Auto",
        "frame_generation": False,
        "generation_mode": "NONE",
        "target_fps": 0,
        "vsync": False,
        "terrain_lod": 100,
        "object_lod": 100
    }
    candidate_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\UserCfg.opt"),
        os.path.expandvars(r"%APPDATA%\Microsoft Flight Simulator 2024\UserCfg.opt"),
        os.path.expandvars(r"%LOCALAPPDATA%\Packages\Microsoft.FlightSimulator_8wekyb3d8bbwe\LocalCache\UserCfg.opt"),
        os.path.expandvars(r"%APPDATA%\Microsoft Flight Simulator\UserCfg.opt"),
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            result["found"] = True
            result["path"] = path
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Mode DLSS
                    m_dlss = re.search(r'DLSSMode\s+(\w+)', content, re.I)
                    if m_dlss:
                        result["dlss_mode"] = m_dlss.group(1).upper()

                    # Frame Generation (DLSSG / FSR3 / 1)
                    m_fg = re.search(r'FrameGeneration\s+(\w+)', content, re.I)
                    if m_fg:
                        fg_val = m_fg.group(1).upper()
                        result["generation_mode"] = fg_val
                        result["frame_generation"] = fg_val in ["DLSSG", "FSR3", "1", "ON"]

                    # VSync
                    if re.search(r'VSync\s+1', content, re.I):
                        result["vsync"] = True
                    
                    # Target Frame Rate / Limiter
                    m_fps = re.search(r'TargetFrameRate\s+(\d+)', content, re.I)
                    if m_fps:
                        result["target_fps"] = int(m_fps.group(1))

                    # LODs
                    m_tlod = re.search(r'TerrainLoDFactor\s+([\d\.]+)', content, re.I)
                    if m_tlod:
                        result["terrain_lod"] = round(float(m_tlod.group(1)) * 100)

                    m_olod = re.search(r'ObjectsLoDFactor\s+([\d\.]+)', content, re.I)
                    if m_olod:
                        result["object_lod"] = round(float(m_olod.group(1)) * 100)
            except Exception:
                pass
            break
    return result


def detect_installed_aircraft(community_path: Optional[str] = None) -> List[Dict[str, str]]:
    """Détecte les avions installés et identifie leur studio éditeur."""
    detected = []
    
    search_paths = []
    if community_path and os.path.exists(community_path):
        search_paths.append(community_path)
    
    search_paths.extend([
        os.path.expandvars(r"%LOCALAPPDATA%\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\Community"),
        os.path.expandvars(r"%APPDATA%\Microsoft Flight Simulator 2024\Packages\Community"),
        r"C:\MSFS2024\Community",
        r"D:\MSFS2024\Community",
        r"E:\MSFS2024\Community",
        r"C:\Community",
        r"D:\Community"
    ])

    found_folder = None
    for p in search_paths:
        if os.path.exists(p):
            found_folder = p
            break

    if not found_folder:
        return detected

    try:
        for entry in os.listdir(found_folder):
            full_p = os.path.join(found_folder, entry)
            if not os.path.isdir(full_p):
                continue
            lower_name = entry.lower()

            # Flight Sim Labs
            if "fslabs" in lower_name or ("a321" in lower_name and "fsl" in lower_name):
                detected.append({"studio_id": "fslabs", "studio": "Flight Sim Labs", "name": "FSLabs A321 / A320", "package": entry})
            # Fenix
            elif "fnx-aircraft" in lower_name or "fenix" in lower_name:
                detected.append({"studio_id": "fenix", "studio": "Fenix Simulations", "name": "Fenix A320 Family", "package": entry})
            # PMDG
            elif "pmdg-aircraft" in lower_name:
                detected.append({"studio_id": "pmdg", "studio": "PMDG", "name": entry.replace("pmdg-aircraft-", "PMDG "), "package": entry})
            # iniBuilds
            elif "inibuilds-aircraft" in lower_name:
                detected.append({"studio_id": "inibuilds", "studio": "iniBuilds", "name": entry.replace("inibuilds-aircraft-", "iniBuilds "), "package": entry})
            # FlyByWire
            elif "flybywire-aircraft" in lower_name or "a32nx" in lower_name or "a380x" in lower_name:
                detected.append({"studio_id": "flybywire", "studio": "FlyByWire", "name": "FBW A32NX / A380X", "package": entry})
            # Just Flight
            elif "justflight-aircraft" in lower_name:
                detected.append({"studio_id": "justflight", "studio": "Just Flight", "name": entry.replace("justflight-aircraft-", "Just Flight "), "package": entry})
    except Exception:
        pass

    return detected


# ==============================================================================
# MOTEUR DE CALCUL DE SYNCHRONISATION (FRAME PACING) & OPTIMISATION
# ==============================================================================

def calculate_frame_pacing(screen_hz: float, use_frame_gen: bool = True) -> Dict[str, Any]:
    """
    Calcule le diviseur entier idéal pour verrouiller un Frame Pacing parfait sans judder.
    Formule : Cible FPS affichés = screen_hz / N (avec N entier).
    FPS moteur = Cible FPS affichés / 2 si Frame Generation 2X est actif.
    Budget temps MainThread = 1000 / FPS moteur (ms).
    """
    hz = float(screen_hz)
    
    if hz >= 240:
        divisor = 3
    elif hz >= 160:
        divisor = 2  # 180 / 2 = 90 FPS | 165 / 2 = 82.5 -> 82 FPS
    elif hz >= 120:
        divisor = 2  # 144 / 2 = 72 FPS | 120 / 2 = 60 FPS
    else:
        divisor = 1

    displayed_fps = round(hz / divisor)
    
    if use_frame_gen:
        base_engine_fps = round(displayed_fps / 2.0)
    else:
        base_engine_fps = displayed_fps

    frame_budget_ms = round(1000.0 / base_engine_fps, 2) if base_engine_fps > 0 else 33.3

    return {
        "screen_hz": hz,
        "divisor": divisor,
        "displayed_fps_target": displayed_fps,
        "base_engine_fps_target": base_engine_fps,
        "frame_budget_ms": frame_budget_ms,
        "sync_ratio": f"{divisor}:1",
        "description": f"Écran {hz:.0f} Hz / Diviseur {divisor} -> {displayed_fps} FPS affichés ({base_engine_fps} FPS moteur). Budget temps CPU MainThread : {frame_budget_ms} ms."
    }


def generate_optimized_rig_profile(user_specs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère l'ensemble des recommandations graphiques, AutoFPS et SceneryX
    en combinant le matériel détecté/ajusté et l'appareil sélectionné.
    """
    screen_hz = float(user_specs.get("screen_hz", 180.0))
    vram_gb = float(user_specs.get("vram_gb", 16.0))
    studio_id = user_specs.get("studio_id", "fslabs").lower()
    has_frame_gen = bool(user_specs.get("frame_gen", True))
    
    studio_profile = AIRCRAFT_STUDIO_PROFILES.get(studio_id, AIRCRAFT_STUDIO_PROFILES["fslabs"])
    pacing = calculate_frame_pacing(screen_hz, use_frame_gen=has_frame_gen)

    if vram_gb <= 12.0:
        terrain_detail = "LOW"
        dlss_preset = "Balanced"
        vram_risk = "Élevé (Paging D3D12 probable en textures Ultra)"
    elif vram_gb <= 16.0:
        if studio_id in ["fslabs", "fenix", "inibuilds"]:
            terrain_detail = "LOW"
            dlss_preset = "Quality"
            vram_risk = "Modéré à Maîtrisé (Terrain Detail LOW libère ~7 Go de VRAM)"
        else:
            terrain_detail = "MEDIUM"
            dlss_preset = "Quality"
            vram_risk = "Faible"
    else:
        terrain_detail = "HIGH"
        dlss_preset = "Quality"
        vram_risk = "Nul (Marge VRAM confortable)"

    autofps = {
        "target_fps": pacing["displayed_fps_target"],
        "tlod_base_min": studio_profile["recommended_t_lod_base"],
        "tlod_top_max": studio_profile["recommended_t_lod_cruise"],
        "olod_cruise": studio_profile["recommended_o_lod_cruise"],
        "vram_plus_active": True,
        "vram_target_percent": 96
    }

    user_cfg_recommendations = {
        "FrameLimiter": pacing["displayed_fps_target"],
        "TerrainLoD": 100 if terrain_detail == "LOW" else 150,
        "DLSSMode": dlss_preset,
        "FrameGeneration": 1 if has_frame_gen else 0,
        "VSync": 1
    }

    sceneryx_recommendations = {
        "isolation_mode": "Direct A -> B (Recommandé)",
        "memory_saving_commit": "~ 2.70 Go Commit RAM",
        "memory_saving_vram": "~ 650 Mo VRAM libérée",
        "stutter_reduction": "Élimine 100% des accès I/O disque des scènes intermédiaires"
    }

    return {
        "pacing": pacing,
        "studio_profile": studio_profile,
        "terrain_detail": terrain_detail,
        "vram_risk": vram_risk,
        "autofps": autofps,
        "user_cfg": user_cfg_recommendations,
        "sceneryx": sceneryx_recommendations,
        "summary_advice": studio_profile["advice"]
    }


def get_full_rig_diagnostics() -> Dict[str, Any]:
    """Point d'entrée complet : retourne le diagnostic matériel complet et les listes pour l'UI."""
    cpu = detect_cpu_info()
    gpu = detect_gpu_info()
    ram = detect_ram_and_xmp()
    disp = detect_display_info()
    hags = detect_windows_hags()
    dlss = detect_dlss_version()
    cfg = detect_msfs_user_cfg()
    installed = detect_installed_aircraft()

    initial_specs = {
        "screen_hz": disp["refresh_rate_hz"],
        "vram_gb": gpu["vram_total_gb"],
        "studio_id": "fslabs",
        "frame_gen": True
    }
    initial_profile = generate_optimized_rig_profile(initial_specs)

    return {
        "detected": {
            "cpu": cpu,
            "gpu": gpu,
            "ram": ram,
            "display": disp,
            "hags_active": hags,
            "rbar_active": gpu.get("is_rbar_active", False),
            "dlss": dlss,
            "user_cfg": cfg,
            "installed_aircraft": installed
        },
        "combobox_data": {
            "popular_cpus": POPULAR_CPUS,
            "popular_gpus": POPULAR_GPUS,
            "popular_refresh_rates": [60, 75, 120, 144, 165, 180, 240, 360],
            "studios": AIRCRAFT_STUDIO_PROFILES
        },
        "recommended_profile": initial_profile
    }


# ==============================================================================
# EXÉCUTION EN LIGNE DE COMMANDE (TEST AUTONOME & VÉRIFICATION)
# ==============================================================================

if __name__ == "__main__":
    print("=" * 75)
    print("  SceneryX Flight Rig Optimizer - Moteur de Détection & Calibration v1.0.1")
    print("=" * 75)
    
    diag = get_full_rig_diagnostics()
    det = diag["detected"]
    
    print("\n[1] MATÉRIEL DÉTECTÉ :")
    print(f"  * Processeur : {det['cpu']['name']} ({det['cpu']['cores']}C/{det['cpu']['threads']}T)")
    print(f"  * Carte Graphique : {det['gpu']['name']} (VRAM : {det['gpu']['vram_total_gb']} Go - Pilote : {det['gpu']['driver_version']})")
    print(f"  * Mémoire Vive : {det['ram']['total_gb']} Go @ {det['ram']['speed_mhz']} MHz | XMP : {'ACTIF' if det['ram']['is_xmp_active'] else 'INACTIF'}")
    print(f"  * Écran Principal : {det['display']['formatted']}")
    print(f"  * Windows HAGS : {'ACTIF' if det['hags_active'] else 'INACTIF'} | Re-Size BAR : {'ACTIF' if det['rbar_active'] else 'INACTIF'}")
    print(f"  * DLSS Actif : {det['dlss']['version']} | FrameGen : {det['dlss']['frame_gen_version']} (Source : {det['dlss']['source']})")
    print(f"  * MSFS UserCfg : {'Trouvé' if det['user_cfg']['found'] else 'Non trouvé'} (FrameGen: {det['user_cfg']['generation_mode']}, DLSSMode: {det['user_cfg']['dlss_mode']}, TargetFPS: {det['user_cfg']['target_fps']})")
    print(f"  * Avions Détectés : {len(det['installed_aircraft'])}")

    print("\n[2] TEST DE CALIBRATION : FLIGHT SIM LABS (FSLabs) A321 SUR ÉCRAN 180 Hz :")
    fslabs_test = generate_optimized_rig_profile({
        "screen_hz": 180.0,
        "vram_gb": det['gpu']['vram_total_gb'],
        "studio_id": "fslabs",
        "frame_gen": True
    })
    p = fslabs_test["pacing"]
    print(f"  * Frame Pacing : {p['description']}")
    print(f"  * Terrain Detail : {fslabs_test['terrain_detail']} ({fslabs_test['vram_risk']})")
    print(f"  * AutoFPS : Target {fslabs_test['autofps']['target_fps']} FPS | TLOD Sol {fslabs_test['autofps']['tlod_base_min']} | TLOD Croisière {fslabs_test['autofps']['tlod_top_max']}")
    print(f"  * SceneryX : {fslabs_test['sceneryx']['isolation_mode']} -> Gain : {fslabs_test['sceneryx']['memory_saving_commit']}")
    print(f"  * Conseil : {fslabs_test['summary_advice']}")
    print("=" * 75)
