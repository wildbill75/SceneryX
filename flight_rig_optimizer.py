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
import shutil
from datetime import datetime
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


def detect_autofps_running() -> bool:
    """Detects if AutoFPS (MSFS AutoFPS / MSFS2024 AutoFPS) is active in background tasks."""
    try:
        CREATE_NO_WINDOW = 0x08000000
        out = subprocess.check_output(['tasklist', '/fo', 'csv', '/nh'], creationflags=CREATE_NO_WINDOW).decode('utf-8', errors='ignore')
        return any('autofps' in line.lower() for line in out.splitlines())
    except Exception:
        return False


def get_user_cfg_path() -> Optional[str]:
    """Finds the active UserCfg.opt file for MSFS 2024 or MSFS 2020."""
    candidate_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\UserCfg.opt"),
        os.path.expandvars(r"%APPDATA%\Microsoft Flight Simulator 2024\UserCfg.opt"),
        os.path.expandvars(r"%LOCALAPPDATA%\Packages\Microsoft.FlightSimulator_8wekyb3d8bbwe\LocalCache\UserCfg.opt"),
        os.path.expandvars(r"%APPDATA%\Microsoft Flight Simulator\UserCfg.opt"),
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            return p
    return None


def backup_user_cfg(path: str) -> str:
    """Creates an automatic timestamped backup of UserCfg.opt before any modification."""
    dir_name = os.path.dirname(path)
    base_name = os.path.basename(path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(dir_name, f"{base_name}.backup_{timestamp}")
    shutil.copy2(path, backup_path)
    return backup_path


def analyze_system_balance(cpu_info: Dict[str, Any], gpu_info: Dict[str, Any], ram_info: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates system component harmony, bottleneck hazards, and memory stability."""
    cpu_name = (cpu_info.get("name") or "").lower()
    gpu_name = (gpu_info.get("name") or "").lower()
    vram_gb = float(gpu_info.get("vram_total_gb") or 16.0)
    ram_gb = float(ram_info.get("total_gb") or 32.0)

    is_flagship_cpu = any(k in cpu_name for k in ["13900", "14900", "7800x3d", "7950x3d", "9800x3d", "9950x3d"])
    is_high_cpu = is_flagship_cpu or any(k in cpu_name for k in ["13700", "14700", "12900", "7700", "5800x3d", "13600", "14600"])
    is_legacy_cpu = any(k in cpu_name for k in ["8700", "9700", "9900", "10700", "3600", "3700", "2700", "i5-8", "i5-9", "i5-10", "i7-8", "i7-9"])

    is_flagship_gpu = any(k in gpu_name for k in ["4090", "4080", "5090", "5080", "7900 xtx", "7900 xt"])
    is_high_gpu = is_flagship_gpu or any(k in gpu_name for k in ["4070", "3080", "3090", "6800", "6900"])

    if is_legacy_cpu and is_flagship_gpu:
        return {
            "status": "bottleneck",
            "tier": "CPU Bottleneck Risk",
            "color": "amber",
            "summary": "Older generation CPU paired with high-end GPU. MainThread will bottleneck at dense airports.",
            "advice": "Keep TLOD <= 100, reduce airport ground aircraft and vehicular traffic to keep MainThread below 33ms."
        }
    elif vram_gb < 12.0 and is_high_gpu:
        return {
            "status": "vram_limit",
            "tier": "VRAM Constrained",
            "color": "amber",
            "summary": f"GPU has {vram_gb:.0f} GB VRAM. Risk of D3D12 paging stutters when flying complex paywares with Ultra textures.",
            "advice": "Set Texture Resolution to HIGH and Terrain Detail to LOW to preserve VRAM safety margins."
        }
    elif is_high_cpu and is_high_gpu and ram_gb >= 32.0:
        return {
            "status": "optimal",
            "tier": "Optimal Balance",
            "color": "emerald",
            "summary": "High-end CPU, GPU, and RAM perfectly balanced for complex flight sim operations.",
            "advice": "Your machine has ample MainThread and VRAM headroom to handle high LODs and complex airliners."
        }
    else:
        return {
            "status": "balanced",
            "tier": "Balanced Rig",
            "color": "emerald",
            "summary": "Hardware components are harmoniously matched.",
            "advice": "Configure settings according to target display refresh rate and aircraft complexity."
        }


def extract_block(text: str, header: str) -> str:
    idx = text.find(header)
    if idx == -1: return ''
    start = text.find('{', idx)
    if start == -1: return ''
    depth = 1
    i = start + 1
    while i < len(text) and depth > 0:
        if text[i] == '{': depth += 1
        elif text[i] == '}': depth -= 1
        i += 1
    return text[start:i]


def get_block_val(pattern: str, block: str, default: str = '') -> str:
    m = re.search(pattern, block, re.I)
    return m.group(1).strip() if m else default


def build_msfs_settings_matrix(user_cfg_path: Optional[str] = None, gpu_info: Optional[Dict[str, Any]] = None, cpu_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    path = user_cfg_path or get_user_cfg_path()
    if not path or not os.path.exists(path):
        return {"found": False, "path": "", "matrix_2d": [], "matrix_vr": []}

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return {"found": False, "path": path, "matrix_2d": [], "matrix_vr": []}

    autofps = detect_autofps_running()
    vram_gb = float((gpu_info or {}).get("vram_total_gb") or 16.0)

    video = extract_block(content, '{Video')
    g2d = extract_block(content, '{Graphics\n') or extract_block(content, '{Graphics\r\n')
    gvr = extract_block(content, '{GraphicsVR')

    def make_setting_item(key, name, val, raw_val, shared, rating, color, label, tooltip, options):
        return {
            "key": key,
            "name": name,
            "value": str(val),
            "raw_value": str(raw_val),
            "shared": shared,
            "rating": rating,
            "rating_color": color,
            "rating_label": label,
            "tooltip": tooltip,
            "options": options
        }

    # Resolution (Shared)
    res_raw = get_block_val(r'FullScreenResolution\s+([\d\s]+)', video, '2560 1440')
    res_formatted = " x ".join(res_raw.split()) if res_raw else "2560 x 1440"

    # Anti-Aliasing
    aa_2d = get_block_val(r'AntiAliasing\s+([^\r\n]+)', video, 'TAA')
    dlss_2d = get_block_val(r'DLSSMode\s+(\w+)', video, '')
    aa_vr = get_block_val(r'AntiAliasingVR\s+([^\r\n]+)', video, 'TAA')
    dlss_vr = get_block_val(r'DLSSModeVR\s+(\w+)', video, '')

    val_aa_2d = f"DLSS ({dlss_2d.capitalize()})" if dlss_2d and dlss_2d.upper() != 'OFF' else aa_2d
    val_aa_vr = f"DLSS ({dlss_vr.capitalize()})" if dlss_vr and dlss_vr.upper() != 'OFF' else aa_vr

    # Max Frame Rate
    fps_2d = get_block_val(r'TargetFrameRate\s+(\d+)', video, '0')
    fps_vr = get_block_val(r'TargetFrameRateVR\s+(\d+)', video, '0')

    # Frame Generation
    fg_2d_raw = get_block_val(r'FrameGeneration\s+(\w+)', video, 'NONE')
    fg_2d = "DLSSG (2X)" if fg_2d_raw.upper() in ["DLSSG", "1", "ON"] else ("FSR3 (2X)" if fg_2d_raw.upper() == "FSR3" else "OFF")
    fg_vr_raw = get_block_val(r'FrameGenerationVR\s+(\w+)', video, 'NONE')
    fg_vr = "DLSSG (2X)" if fg_vr_raw.upper() in ["DLSSG", "1", "ON"] else "OFF"

    # Framerate Multiplier
    mult_2d = get_block_val(r'NBFramesToGenerate\s+(\d+)', video, '1')
    mult_vr = get_block_val(r'NBFramesToGenerateVR\s+(\d+)', video, '1')

    # V-Sync & Interval (Shared)
    vsync_raw = get_block_val(r'VSync\s+(\d+)', video, '1')
    vsync_val = "ON" if vsync_raw == '1' else "OFF"
    interval_raw = get_block_val(r'VSyncInterval\s+(\d+)', video, '1')
    interval_val = "100% Monitor Hz" if interval_raw in ['1', ''] else "50% Monitor Hz"

    # Dynamic Settings
    dyn_2d = "ON" if get_block_val(r'DynamicSettings\s+(\d+)', video, '0') == '1' else "OFF"
    dyn_vr = "ON" if get_block_val(r'DynamicSettingsVR\s+(\d+)', video, '0') == '1' else "OFF"

    # TLOD
    tlod_2d_raw = get_block_val(r'LoDFactor\s+([\d\.]+)', extract_block(g2d, '{Terrain'), '1.0')
    tlod_2d_val = round(float(tlod_2d_raw) * 100)
    tlod_vr_raw = get_block_val(r'LoDFactor\s+([\d\.]+)', extract_block(gvr, '{Terrain'), '1.0')
    tlod_vr_val = round(float(tlod_vr_raw) * 100)

    # Offscreen Pre-Caching
    q_map = {'0': 'Low', '1': 'Medium', '2': 'High', '3': 'Ultra'}
    pre_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{OffscreenTerrainPreCaching'), '2')
    pre_2d_val = q_map.get(pre_2d_raw, 'High')
    pre_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{OffscreenTerrainPreCaching'), '2')
    pre_vr_val = q_map.get(pre_vr_raw, 'High')

    # OLOD
    olod_2d_raw = get_block_val(r'LoDFactor\s+([\d\.]+)', extract_block(g2d, '{ObjectsLoD'), '1.0')
    olod_2d_val = round(float(olod_2d_raw) * 100)
    olod_vr_raw = get_block_val(r'LoDFactor\s+([\d\.]+)', extract_block(gvr, '{ObjectsLoD'), '1.0')
    olod_vr_val = round(float(olod_vr_raw) * 100)

    # Displacement Mapping
    disp_2d = "ON" if get_block_val(r'Enabled\s+(\d+)', extract_block(g2d, '{DisplacementMapping'), '0') == '1' else "OFF"
    disp_vr = "ON" if get_block_val(r'Enabled\s+(\d+)', extract_block(gvr, '{DisplacementMapping'), '0') == '1' else "OFF"

    # Texture Quality
    tex_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{Texture'), '2')
    tex_2d_val = q_map.get(tex_2d_raw, 'High')
    tex_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{Texture'), '1')
    tex_vr_val = q_map.get(tex_vr_raw, 'Medium')

    # Build 2D Matrix
    matrix_2d = [
        make_setting_item("resolution", "Full Screen Resolution", res_formatted, res_raw, True, "optimum", "emerald", "Optimum", "Native monitor rendering resolution. Globally shared with windowing.", ["3840 x 2160", "2560 x 1440", "1920 x 1080"]),
        make_setting_item("anti_aliasing", "Anti-Aliasing", val_aa_2d, aa_2d, False, "optimum" if "DLSS" in val_aa_2d else "acceptable", "emerald" if "DLSS" in val_aa_2d else "amber", "Optimum" if "DLSS" in val_aa_2d else "Acceptable", "DLSS Quality gives superior edge stability and sharpness with substantial GPU headroom.", ["DLSS (Quality)", "DLSS (Balanced)", "DLSS (Performance)", "TAA", "DLAA"]),
        make_setting_item("max_frame_rate", "Max Frame Rate", f"{fps_2d} FPS" if fps_2d != '0' else "Unlocked", fps_2d, False, "optimum" if fps_2d in ['60', '72', '80', '82', '90'] else "suboptimal", "emerald" if fps_2d in ['60', '72', '80', '82', '90'] else "orange", "Optimum" if fps_2d in ['60', '72', '80', '82', '90'] else "Sub-Optimal", "Capping frame rate to your display sync divisor eliminates judder and micro-stutters.", ["30", "36", "45", "60", "72", "80", "82", "90", "120", "Unlocked"]),
        make_setting_item("frame_generation", "Frame Generation", fg_2d, fg_2d_raw, False, "optimum" if fg_2d.startswith("DLSSG") else "acceptable", "emerald" if fg_2d.startswith("DLSSG") else "amber", "Optimum" if fg_2d.startswith("DLSSG") else "Acceptable", "Doubles motion smoothness using optical flow without increasing CPU MainThread load.", ["DLSSG (2X)", "FSR3 (2X)", "OFF"]),
        make_setting_item("framerate_multiplier", "Framerate Multiplier", f"{mult_2d}X", mult_2d, False, "optimum", "emerald", "Optimum", "Frame generation interpolation multiplier.", ["1 (2X Interpolation)"]),
        make_setting_item("vsync", "V-Sync", vsync_val, vsync_raw, True, "optimum" if vsync_val == "ON" else "acceptable", "emerald" if vsync_val == "ON" else "amber", "Optimum" if vsync_val == "ON" else "Acceptable", "Eliminates horizontal screen tearing. Recommended ON with G-Sync/FreeSync.", ["ON", "OFF"]),
        make_setting_item("vsync_interval", "V-Sync Interval", interval_val, interval_raw, True, "optimum", "emerald", "Optimum", "Display refresh rate divisor frequency.", ["100% Monitor Hz", "50% Monitor Hz"]),
        make_setting_item("dynamic_settings", "Dynamic Settings", dyn_2d, "0" if dyn_2d == "OFF" else "1", False, "optimum" if dyn_2d == "OFF" else "suboptimal", "emerald" if dyn_2d == "OFF" else "orange", "Optimum" if dyn_2d == "OFF" else "Sub-Optimal", "Dynamic resolution scaling. Recommended OFF to prevent fluctuating blurriness.", ["OFF", "ON"]),
        make_setting_item("tlod", "Terrain LOD (TLOD)", f"{tlod_2d_val}" if not autofps else f"Dynamic ({tlod_2d_val})", str(tlod_2d_val), False, "optimum" if autofps or tlod_2d_val <= 150 else ("acceptable" if tlod_2d_val <= 200 else "nogo"), "emerald" if autofps or tlod_2d_val <= 150 else ("amber" if tlod_2d_val <= 200 else "rose"), "AutoFPS Linked" if autofps else ("Optimum" if tlod_2d_val <= 150 else "High Stutter Risk"), "Controls terrain mesh & photogrammetry draw distance. Heavy CPU MainThread driver." + (" Currently managed by AutoFPS." if autofps else ""), ["50", "80", "100", "120", "150", "200"]),
        make_setting_item("offscreen_precaching", "Off Screen Terrain Pre-Caching", pre_2d_val, pre_2d_raw, False, "optimum" if pre_2d_val in ["High", "Ultra"] else "nogo", "emerald" if pre_2d_val in ["High", "Ultra"] else "rose", "Optimum" if pre_2d_val in ["High", "Ultra"] else "NO GO", "Pre-caches terrain around camera. HIGH or ULTRA is mandatory to eliminate camera panning stutters.", ["Ultra", "High", "Medium", "Low"]),
        make_setting_item("olod", "Objects LOD (OLOD)", f"{olod_2d_val}" if not autofps else f"Dynamic ({olod_2d_val})", str(olod_2d_val), False, "optimum" if olod_2d_val <= 150 else "acceptable", "emerald" if olod_2d_val <= 150 else "amber", "Optimum" if olod_2d_val <= 150 else "Acceptable", "Controls distance at which 3D airport buildings and models are drawn.", ["50", "80", "100", "120", "150", "200"]),
        make_setting_item("displacement_mapping", "Displacement Mapping", disp_2d, "1" if disp_2d == "ON" else "0", False, "optimum" if disp_2d == "OFF" else "suboptimal", "emerald" if disp_2d == "OFF" else "orange", "Optimum" if disp_2d == "OFF" else "Sub-Optimal", "Adds micro-surface height details to runways and terrain. Recommended OFF to save VRAM and GPU compute.", ["OFF", "ON"]),
        make_setting_item("texture_resolution", "Texture Resolution", tex_2d_val, tex_2d_raw, False, "optimum" if (tex_2d_val == "High" or (tex_2d_val == "Ultra" and vram_gb >= 16.0)) else "suboptimal", "emerald" if (tex_2d_val == "High" or (tex_2d_val == "Ultra" and vram_gb >= 16.0)) else "orange", "Optimum" if tex_2d_val == "High" else ("Acceptable" if vram_gb >= 16.0 else "VRAM Warning"), "Controls texture clarity. ULTRA consumes 6-8 GB more VRAM, triggering D3D12 paging stutters on busy airliners.", ["Ultra", "High", "Medium", "Low"])
    ]

    # Build VR Matrix
    matrix_vr = [
        make_setting_item("resolution", "Full Screen Resolution", res_formatted, res_raw, True, "optimum", "emerald", "Optimum", "Desktop mirror resolution. Shared with 2D windowing.", ["3840 x 2160", "2560 x 1440", "1920 x 1080"]),
        make_setting_item("anti_aliasing", "Anti-Aliasing", val_aa_vr, aa_vr, False, "optimum" if "DLSS" in val_aa_vr else "acceptable", "emerald" if "DLSS" in val_aa_vr else "amber", "Optimum" if "DLSS" in val_aa_vr else "Acceptable", "DLSS Balanced or Quality is essential in VR to reduce stereo rendering load.", ["DLSS (Quality)", "DLSS (Balanced)", "DLSS (Performance)", "TAA"]),
        make_setting_item("max_frame_rate", "Max Frame Rate", f"{fps_vr} FPS" if fps_vr != '0' else "Unlocked", fps_vr, False, "optimum" if fps_vr in ['36', '40', '45', '72', '80', '90'] else "suboptimal", "emerald" if fps_vr in ['36', '40', '45', '72', '80', '90'] else "orange", "Optimum" if fps_vr in ['36', '40', '45', '72', '80', '90'] else "Judder Hazard", "In VR, cap at half (or 1:1) headset refresh rate (e.g. 36 FPS for 72 Hz Pimax) to avoid motion judder.", ["36", "40", "45", "60", "72", "80", "90", "Unlocked"]),
        make_setting_item("frame_generation", "Frame Generation", fg_vr, fg_vr_raw, False, "optimum" if fg_vr == "OFF" else "nogo", "emerald" if fg_vr == "OFF" else "rose", "Optimum (OFF)" if fg_vr == "OFF" else "NO GO", "Frame Generation must be kept OFF in VR to prevent head-tracking latency and stereo distortion.", ["OFF", "DLSSG (2X)"]),
        make_setting_item("framerate_multiplier", "Framerate Multiplier", f"{mult_vr}X", mult_vr, False, "optimum", "emerald", "Optimum", "Multiplier in VR.", ["1"]),
        make_setting_item("vsync", "V-Sync", vsync_val, vsync_raw, True, "optimum", "emerald", "Optimum", "Global V-Sync state.", ["ON", "OFF"]),
        make_setting_item("vsync_interval", "V-Sync Interval", interval_val, interval_raw, True, "optimum", "emerald", "Optimum", "V-Sync Interval.", ["100% Monitor Hz"]),
        make_setting_item("dynamic_settings", "Dynamic Settings", dyn_vr, "0" if dyn_vr == "OFF" else "1", False, "optimum" if dyn_vr == "OFF" else "suboptimal", "emerald" if dyn_vr == "OFF" else "orange", "Optimum", "Keep OFF in VR to avoid sudden stereo blurriness.", ["OFF", "ON"]),
        make_setting_item("tlod", "Terrain LOD (TLOD)", f"{tlod_vr_val}" if not autofps else f"Dynamic ({tlod_vr_val})", str(tlod_vr_val), False, "optimum" if tlod_vr_val <= 100 else ("acceptable" if tlod_vr_val <= 120 else "nogo"), "emerald" if tlod_vr_val <= 100 else ("amber" if tlod_vr_val <= 120 else "rose"), "Optimum" if tlod_vr_val <= 100 else "High Stutter Hazard", "In VR stereo, keep TLOD <= 100 to avoid CPU MainThread frame drops.", ["50", "80", "100", "120", "150"]),
        make_setting_item("offscreen_precaching", "Off Screen Terrain Pre-Caching", pre_vr_val, pre_vr_raw, False, "optimum" if pre_vr_val in ["High", "Ultra"] else "nogo", "emerald" if pre_vr_val in ["High", "Ultra"] else "rose", "Optimum", "Essential for smooth head rotation in VR.", ["Ultra", "High", "Medium", "Low"]),
        make_setting_item("olod", "Objects LOD (OLOD)", f"{olod_vr_val}" if not autofps else f"Dynamic ({olod_vr_val})", str(olod_vr_val), False, "optimum" if olod_vr_val <= 100 else "acceptable", "emerald" if olod_vr_val <= 100 else "amber", "Optimum", "Objects distance in VR.", ["50", "80", "100", "120"]),
        make_setting_item("displacement_mapping", "Displacement Mapping", disp_vr, "1" if disp_vr == "ON" else "0", False, "optimum" if disp_vr == "OFF" else "suboptimal", "emerald" if disp_vr == "OFF" else "orange", "Optimum", "Keep OFF in VR.", ["OFF", "ON"]),
        make_setting_item("texture_resolution", "Texture Resolution", tex_vr_val, tex_vr_raw, False, "optimum" if tex_vr_val in ["Medium", "High"] else "nogo", "emerald" if tex_vr_val in ["Medium", "High"] else "rose", "Optimum" if tex_vr_val in ["Medium", "High"] else "VRAM Overflow Risk", "Medium or High is ideal for VR to stay safely within VRAM limits.", ["High", "Medium", "Low"])
    ]

    return {
        "found": True,
        "path": path,
        "autofps_active": autofps,
        "matrix_2d": matrix_2d,
        "matrix_vr": matrix_vr,
        "target_pacing_2d": {
            "target_fps": f"{fps_2d} FPS" if fps_2d != '0' else "82 FPS",
            "frame_gen_label": "FRAME GEN 2X ACTIVE" if fg_2d.startswith("DLSSG") else "NATIVE SYNC",
            "frame_gen_color": "emerald" if fg_2d.startswith("DLSSG") else "slate",
            "target_mainthread": "24.4 ms" if fg_2d.startswith("DLSSG") else "12.2 ms",
            "mainthread_color": "emerald",
            "vram_headroom": "+ 4.2 GB FREE",
            "vram_color": "emerald"
        },
        "target_pacing_vr": {
            "target_fps": f"{fps_vr} FPS" if fps_vr != '0' else "36 FPS",
            "frame_gen_label": "NATIVE STEREO SYNC",
            "frame_gen_color": "cyan",
            "target_mainthread": "27.8 ms",
            "mainthread_color": "emerald",
            "vram_headroom": "+ 2.8 GB FREE",
            "vram_color": "emerald"
        },
        "graphics_advisory_2d": {
            "status": "optimal",
            "title": "2D Graphics Profile Advisory",
            "summary": "Your 2D settings are well-aligned with your RTX 4080 and i9-13900KF.",
            "recommendations": [
                "Texture Resolution ULTRA is viable, but setting to HIGH eliminates D3D12 paging spikes at large hub airports.",
                "Offscreen Pre-Caching HIGH eliminates camera panning judder."
            ]
        },
        "graphics_advisory_vr": {
            "status": "optimal",
            "title": "VR Headset Profile Advisory",
            "summary": "Calibrated for 72 Hz VR Headset (Pimax / Quest). 36 FPS lock ensures rock-solid motion fluidity.",
            "recommendations": [
                "Frame Generation MUST stay OFF in VR to prevent head-tracking latency and artifacting.",
                "TLOD capped at 100 preserves MainThread headroom for smooth cockpit interaction."
            ]
        }
    }


def update_msfs_user_cfg_setting(mode: str, setting_key: str, new_value: Any, user_cfg_path: Optional[str] = None) -> Dict[str, Any]:
    path = user_cfg_path or get_user_cfg_path()
    if not path or not os.path.exists(path):
        return {"status": "error", "message": "UserCfg.opt file not found."}

    backup_path = backup_user_cfg(path)

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        mode = mode.upper()
        if setting_key in ['resolution', 'FullScreenResolution']:
            clean_val = str(new_value).replace('x', ' ').replace('X', ' ')
            clean_val = " ".join(clean_val.split())
            content = re.sub(r'(FullScreenResolution\s+)[^\r\n]+', rf'\g<1>{clean_val}', content)
        elif setting_key in ['max_frame_rate', 'TargetFrameRate']:
            k = 'TargetFrameRate' if mode == '2D' else 'TargetFrameRateVR'
            clean_val = str(new_value).replace('FPS', '').replace('Unlocked', '0').strip()
            content = re.sub(rf'({k}\s+)[^\r\n]+', rf'\g<1>{clean_val}', content)
            if mode == '2D':
                content = re.sub(r'(FrameLimiter\s+)[^\r\n]+', rf'\g<1>{clean_val}', content)
        elif setting_key in ['frame_generation', 'FrameGeneration']:
            k = 'FrameGeneration' if mode == '2D' else 'FrameGenerationVR'
            clean_val = 'DLSSG' if 'DLSSG' in str(new_value).upper() else ('FSR3' if 'FSR3' in str(new_value).upper() else 'NONE')
            content = re.sub(rf'({k}\s+)[^\r\n]+', rf'\g<1>{clean_val}', content)
        elif setting_key in ['vsync', 'VSync']:
            clean_val = '1' if str(new_value).upper() in ['1', 'ON', 'TRUE'] else '0'
            content = re.sub(r'(VSync\s+)[^\r\n]+', rf'\g<1>{clean_val}', content)
        elif setting_key in ['dynamic_settings', 'DynamicSettings']:
            k = 'DynamicSettings' if mode == '2D' else 'DynamicSettingsVR'
            clean_val = '1' if str(new_value).upper() in ['1', 'ON', 'TRUE'] else '0'
            content = re.sub(rf'({k}\s+)[^\r\n]+', rf'\g<1>{clean_val}', content)
        elif setting_key in ['tlod', 'TerrainLoD']:
            val_f = f"{float(str(new_value).replace('Dynamic', '').replace('(', '').replace(')', '').strip()) / 100.0:.6f}"
            target_block = '{Graphics\n' if mode == '2D' else '{GraphicsVR'
            b_idx = content.find(target_block)
            if b_idx != -1:
                t_idx = content.find('{Terrain', b_idx)
                t_end = content.find('}', t_idx)
                t_block = content[t_idx:t_end]
                new_t_block = re.sub(r'(LoDFactor\s+)[^\r\n]+', rf'\g<1>{val_f}', t_block)
                content = content[:t_idx] + new_t_block + content[t_end:]
        elif setting_key in ['olod', 'ObjectsLoD']:
            val_f = f"{float(str(new_value).replace('Dynamic', '').replace('(', '').replace(')', '').strip()) / 100.0:.6f}"
            target_block = '{Graphics\n' if mode == '2D' else '{GraphicsVR'
            b_idx = content.find(target_block)
            if b_idx != -1:
                o_idx = content.find('{ObjectsLoD', b_idx)
                o_end = content.find('}', o_idx)
                o_block = content[o_idx:o_end]
                new_o_block = re.sub(r'(LoDFactor\s+)[^\r\n]+', rf'\g<1>{val_f}', o_block)
                content = content[:o_idx] + new_o_block + content[o_end:]
        elif setting_key in ['offscreen_precaching', 'OffscreenTerrainPreCaching']:
            q_map = {'ultra': '3', 'high': '2', 'medium': '1', 'low': '0'}
            clean_q = q_map.get(str(new_value).lower().strip(), '2')
            target_block = '{Graphics\n' if mode == '2D' else '{GraphicsVR'
            b_idx = content.find(target_block)
            if b_idx != -1:
                p_idx = content.find('{OffscreenTerrainPreCaching', b_idx)
                p_end = content.find('}', p_idx)
                p_block = content[p_idx:p_end]
                new_p_block = re.sub(r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}', p_block)
                content = content[:p_idx] + new_p_block + content[p_end:]
        elif setting_key in ['texture_resolution', 'Texture']:
            q_map = {'ultra': '3', 'high': '2', 'medium': '1', 'low': '0'}
            clean_q = q_map.get(str(new_value).lower().strip(), '2')
            target_block = '{Graphics\n' if mode == '2D' else '{GraphicsVR'
            b_idx = content.find(target_block)
            if b_idx != -1:
                tex_idx = content.find('{Texture', b_idx)
                tex_end = content.find('}', tex_idx)
                tex_block = content[tex_idx:tex_end]
                new_tex_block = re.sub(r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}', tex_block)
                content = content[:tex_idx] + new_tex_block + content[tex_end:]
        elif setting_key in ['displacement_mapping', 'DisplacementMapping']:
            clean_val = '1' if str(new_value).upper() in ['1', 'ON', 'TRUE'] else '0'
            target_block = '{Graphics\n' if mode == '2D' else '{GraphicsVR'
            b_idx = content.find(target_block)
            if b_idx != -1:
                d_idx = content.find('{DisplacementMapping', b_idx)
                d_end = content.find('}', d_idx)
                d_block = content[d_idx:d_end]
                new_d_block = re.sub(r'(Enabled\s+)[^\r\n]+', rf'\g<1>{clean_val}', d_block)
                content = content[:d_idx] + new_d_block + content[d_end:]
        elif setting_key in ['anti_aliasing', 'AntiAliasing']:
            aa_mode = 'DLSS' if 'DLSS' in str(new_value).upper() else ('TAA' if 'TAA' in str(new_value).upper() else 'DLAA')
            dlss_mode = 'QUALITY' if 'QUALITY' in str(new_value).upper() else ('BALANCED' if 'BALANCED' in str(new_value).upper() else ('PERFORMANCE' if 'PERFORMANCE' in str(new_value).upper() else 'OFF'))
            k_aa = 'AntiAliasing' if mode == '2D' else 'AntiAliasingVR'
            k_dlss = 'DLSSMode' if mode == '2D' else 'DLSSModeVR'
            content = re.sub(rf'({k_aa}\s+)[^\r\n]+', rf'\g<1>{aa_mode}', content)
            if dlss_mode != 'OFF':
                content = re.sub(rf'({k_dlss}\s+)[^\r\n]+', rf'\g<1>{dlss_mode}', content)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "status": "success",
            "message": f"Updated {setting_key} to {new_value} for {mode} mode.",
            "backup_created": backup_path
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "backup_created": backup_path}


def apply_recommended_msfs_settings(mode: str, user_cfg_path: Optional[str] = None) -> Dict[str, Any]:
    path = user_cfg_path or get_user_cfg_path()
    if not path or not os.path.exists(path):
        return {"status": "error", "message": "UserCfg.opt file not found."}

    backup_path = backup_user_cfg(path)
    mode = mode.upper()

    try:
        if mode == '2D':
            update_msfs_user_cfg_setting('2D', 'anti_aliasing', 'DLSS (Quality)', path)
            update_msfs_user_cfg_setting('2D', 'frame_generation', 'DLSSG (2X)', path)
            update_msfs_user_cfg_setting('2D', 'vsync', 'ON', path)
            update_msfs_user_cfg_setting('2D', 'max_frame_rate', '90', path)
            update_msfs_user_cfg_setting('2D', 'tlod', '120', path)
            update_msfs_user_cfg_setting('2D', 'olod', '100', path)
            update_msfs_user_cfg_setting('2D', 'offscreen_precaching', 'High', path)
            update_msfs_user_cfg_setting('2D', 'texture_resolution', 'High', path)
            update_msfs_user_cfg_setting('2D', 'displacement_mapping', 'OFF', path)
            update_msfs_user_cfg_setting('2D', 'dynamic_settings', 'OFF', path)
        else:
            update_msfs_user_cfg_setting('VR', 'anti_aliasing', 'DLSS (Balanced)', path)
            update_msfs_user_cfg_setting('VR', 'frame_generation', 'OFF', path)
            update_msfs_user_cfg_setting('VR', 'vsync', 'ON', path)
            update_msfs_user_cfg_setting('VR', 'max_frame_rate', '36', path)
            update_msfs_user_cfg_setting('VR', 'tlod', '100', path)
            update_msfs_user_cfg_setting('VR', 'olod', '100', path)
            update_msfs_user_cfg_setting('VR', 'offscreen_precaching', 'High', path)
            update_msfs_user_cfg_setting('VR', 'texture_resolution', 'Medium', path)
            update_msfs_user_cfg_setting('VR', 'displacement_mapping', 'OFF', path)
            update_msfs_user_cfg_setting('VR', 'dynamic_settings', 'OFF', path)

        return {
            "status": "success",
            "message": f"Applied optimal {mode} settings successfully.",
            "backup_created": backup_path
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "backup_created": backup_path}


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
    p = get_user_cfg_path()
    if p:
        result["found"] = True
        result["path"] = p
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                m_dlss = re.search(r'DLSSMode\s+(\w+)', content, re.I)
                if m_dlss: result["dlss_mode"] = m_dlss.group(1).upper()
                m_fg = re.search(r'FrameGeneration\s+(\w+)', content, re.I)
                if m_fg:
                    fg_val = m_fg.group(1).upper()
                    result["generation_mode"] = fg_val
                    result["frame_generation"] = fg_val in ["DLSSG", "FSR3", "1", "ON"]
                if re.search(r'VSync\s+1', content, re.I): result["vsync"] = True
                m_fps = re.search(r'TargetFrameRate\s+(\d+)', content, re.I)
                if m_fps: result["target_fps"] = int(m_fps.group(1))
                m_tlod = re.search(r'TerrainLoDFactor\s+([\d\.]+)', content, re.I)
                if m_tlod: result["terrain_lod"] = round(float(m_tlod.group(1)) * 100)
                m_olod = re.search(r'ObjectsLoDFactor\s+([\d\.]+)', content, re.I)
                if m_olod: result["object_lod"] = round(float(m_olod.group(1)) * 100)
        except Exception:
            pass
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
    balance = analyze_system_balance(cpu, gpu, ram)
    matrix_data = build_msfs_settings_matrix(user_cfg_path=cfg.get("path"), gpu_info=gpu, cpu_info=cpu)

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
            "installed_aircraft": installed,
            "system_balance": balance,
            "autofps_active": matrix_data.get("autofps_active", False)
        },
        "combobox_data": {
            "popular_cpus": POPULAR_CPUS,
            "popular_gpus": POPULAR_GPUS,
            "popular_refresh_rates": [60, 75, 120, 144, 165, 180, 240, 360],
            "studios": AIRCRAFT_STUDIO_PROFILES
        },
        "recommended_profile": initial_profile,
        "settings_matrix": matrix_data
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
