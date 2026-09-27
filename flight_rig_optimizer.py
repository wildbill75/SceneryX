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
import glob
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


def get_available_user_cfg_backups(user_cfg_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns sorted list of available UserCfg.opt timestamped backups."""
    path = user_cfg_path or get_user_cfg_path()
    if not path or not os.path.exists(path):
        return []
    dir_name = os.path.dirname(path)
    base_name = os.path.basename(path)
    pattern = os.path.join(dir_name, f"{base_name}.backup_*")
    files = glob.glob(pattern)
    backups = []
    for f in files:
        fn = os.path.basename(f)
        ts_part = fn.replace(f"{base_name}.backup_", "")
        try:
            dt = datetime.strptime(ts_part, "%Y%m%d_%H%M%S")
            formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            formatted_date = ts_part
        size_kb = round(os.path.getsize(f) / 1024, 1)
        mtime = os.path.getmtime(f)
        backups.append({
            "filename": fn,
            "path": f,
            "timestamp": formatted_date,
            "raw_timestamp": ts_part,
            "mtime": mtime,
            "size_kb": size_kb
        })
    backups.sort(key=lambda x: x["mtime"], reverse=True)
    return backups


def restore_user_cfg_backup(backup_target: str, user_cfg_path: Optional[str] = None) -> Dict[str, Any]:
    """Safely restores a previously saved UserCfg.opt backup file."""
    path = user_cfg_path or get_user_cfg_path()
    if not path:
        return {"status": "error", "message": "UserCfg.opt path not detected."}
    dir_name = os.path.dirname(path)
    target_path = backup_target if os.path.isabs(backup_target) else os.path.join(dir_name, backup_target)
    if not os.path.exists(target_path):
        return {"status": "error", "message": f"Backup file {backup_target} not found."}

    safety_backup = backup_user_cfg(path)
    try:
        shutil.copy2(target_path, path)
        return {
            "status": "success",
            "message": f"Successfully restored UserCfg.opt from {os.path.basename(target_path)}",
            "restored_file": os.path.basename(target_path),
            "safety_backup": os.path.basename(safety_backup)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


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


def update_sub_block_setting(content: str, mode: str, block_name: str, pattern: str, replacement: str) -> str:
    """Met à jour un paramètre dans un sous-bloc d'un bloc de mode ({Graphics ou {GraphicsVR)."""
    mode_tag = '{Graphics\n' if mode == '2D' else '{GraphicsVR'
    mode_idx = content.find(mode_tag)
    if mode_idx == -1 and mode == '2D':
        mode_tag = '{Graphics\r\n'
        mode_idx = content.find(mode_tag)
    if mode_idx == -1:
        return content

    mode_boundary = content.find('{GraphicsVR', mode_idx) if mode == '2D' else len(content)
    if mode_boundary == -1:
        mode_boundary = len(content)

    mode_text = content[mode_idx:mode_boundary]
    sub_start = mode_text.find(block_name)
    if sub_start == -1:
        return content

    sub_end = mode_text.find('}', sub_start)
    if sub_end == -1:
        return content

    sub_slice = mode_text[sub_start:sub_end]
    new_sub_slice = re.sub(pattern, replacement, sub_slice)
    new_mode_text = mode_text[:sub_start] + new_sub_slice + mode_text[sub_end:]
    return content[:mode_idx] + new_mode_text + content[mode_boundary:]


def build_msfs_settings_matrix(user_cfg_path: Optional[str] = None, gpu_info: Optional[Dict[str, Any]] = None, cpu_info: Optional[Dict[str, Any]] = None, flight_profile: str = 'LINER', vr_refresh_rate: int = 72) -> Dict[str, Any]:
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
    is_liner = (str(flight_profile).upper() == 'LINER')
    try:
        vr_hz = int(vr_refresh_rate)
    except Exception:
        vr_hz = 72
    target_vr_fps = max(30, vr_hz // 2)
    target_vr_ms = round(1000.0 / target_vr_fps, 1)

    video = extract_block(content, '{Video')
    g2d = extract_block(content, '{Graphics\n') or extract_block(content, '{Graphics\r\n')
    gvr = extract_block(content, '{GraphicsVR')

    def make_setting_item(key, name, val, raw_val, shared, rating, color, label, tooltip, options, page=1, is_numeric=False, min_val=0, max_val=100, step=1, tag_reason=None):
        clean_lbl = str(label).upper().replace('(', ' ').replace(')', ' ').replace('-', '').strip().split()[0] if str(label).strip() else "OPTIMUM"
        if clean_lbl in ["NO", "NOGO", "RISK", "HAZARD", "ALERT"]:
            clean_lbl = "HAZARD"
            color = "rose"
        elif clean_lbl in ["SUBOPTIMAL", "MISMATCH"]:
            clean_lbl = "SUBOPTIMAL"
            color = "orange"
        elif clean_lbl in ["ACCEPTABLE", "WATCH", "PRESSURE"]:
            clean_lbl = "ACCEPTABLE"
            color = "amber"
        else:
            clean_lbl = "OPTIMUM"
            color = "emerald"

        return {
            "key": key,
            "name": name,
            "value": str(val),
            "raw_value": str(raw_val),
            "shared": shared,
            "page": page,
            "is_numeric": is_numeric,
            "min_val": min_val,
            "max_val": max_val,
            "step": step,
            "rating": rating,
            "rating_color": color,
            "rating_label": clean_lbl,
            "tag_reason": tag_reason or f"Rated {clean_lbl} based on hardware pacing budget.",
            "tooltip": tooltip,
            "options": options
        }

    q_map = {'0': 'Low', '1': 'Medium', '2': 'High', '3': 'Ultra'}
    fft_map = {'128': 'Low (128)', '256': 'Medium (256)', '512': 'High (512)', '1024': 'Ultra (1024)'}
    glass_map = {'0': 'Low (Quarter)', '1': 'Medium (Half)', '2': 'High (Full)'}
    shadow_map = {'512': 'Low (512)', '1024': 'Medium (1024)', '1536': 'High (1536)', '2048': 'Ultra (2048)'}
    hf_map = {'128': 'Low (128)', '256': 'Medium (256)', '512': 'High (512)', '1024': 'Ultra (1024)'}

    # ==========================================
    # PAGE 1: CORE & DISPLAY PACING (9 SETTINGS)
    # ==========================================

    # 1. Full Screen Resolution (Shared)
    res_raw = get_block_val(r'FullScreenResolution\s+([\d\s]+)', video, '2560 1440')
    res_formatted = " x ".join(res_raw.split()) if res_raw else "2560 x 1440"

    # 2. Anti-Aliasing & Upscaling
    aa_2d = get_block_val(r'AntiAliasing\s+([^\r\n]+)', video, 'TAA')
    dlss_2d = get_block_val(r'DLSSMode\s+(\w+)', video, '')
    aa_vr = get_block_val(r'AntiAliasingVR\s+([^\r\n]+)', video, 'TAA')
    dlss_vr = get_block_val(r'DLSSModeVR\s+(\w+)', video, '')

    val_aa_2d = f"DLSS ({dlss_2d.capitalize()})" if dlss_2d and dlss_2d.upper() != 'OFF' else aa_2d
    val_aa_vr = f"DLSS ({dlss_vr.capitalize()})" if dlss_vr and dlss_vr.upper() != 'OFF' else aa_vr

    # 3. Max Frame Rate (Manual numeric + Presets)
    fps_2d = get_block_val(r'TargetFrameRate\s+(\d+)', video, '0')
    fps_vr = get_block_val(r'TargetFrameRateVR\s+(\d+)', video, '0')

    # 4. Frame Generation
    fg_2d_raw = get_block_val(r'FrameGeneration\s+(\w+)', video, 'NONE')
    fg_2d = "DLSSG (2X)" if fg_2d_raw.upper() in ["DLSSG", "1", "ON"] else ("FSR3 (2X)" if fg_2d_raw.upper() == "FSR3" else "OFF")
    fg_vr_raw = get_block_val(r'FrameGenerationVR\s+(\w+)', video, 'NONE')
    fg_vr = "DLSSG (2X)" if fg_vr_raw.upper() in ["DLSSG", "1", "ON"] else "OFF"

    # 5. Framerate Multiplier
    mult_2d = get_block_val(r'NBFramesToGenerate\s+(\d+)', video, '1')
    mult_vr = get_block_val(r'NBFramesToGenerateVR\s+(\d+)', video, '1')

    # 6. V-Sync (Shared)
    vsync_raw = get_block_val(r'VSync\s+(\d+)', video, '1')
    vsync_val = "ON" if vsync_raw == '1' else "OFF"

    # 7. Dynamic Settings
    dyn_2d = "ON" if get_block_val(r'DynamicSettings\s+(\d+)', video, '0') == '1' else "OFF"
    dyn_vr = "ON" if get_block_val(r'DynamicSettingsVR\s+(\d+)', video, '0') == '1' else "OFF"

    # 8. NVIDIA Reflex Low Latency
    reflex_2d_raw = get_block_val(r'Reflex\s+([^\r\n]+)', video, 'ON').upper().replace(' ', '')
    reflex_2d = "ON+BOOST" if "BOOST" in reflex_2d_raw else ("ON" if reflex_2d_raw in ["ON", "1"] else "OFF")
    reflex_vr_raw = get_block_val(r'ReflexVR\s+([^\r\n]+)', video, 'ON').upper().replace(' ', '')
    reflex_vr = "ON+BOOST" if "BOOST" in reflex_vr_raw else ("ON" if reflex_vr_raw in ["ON", "1"] else "OFF")

    # 9. Texture Quality
    tex_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{Texture'), '2')
    tex_2d_val = q_map.get(tex_2d_raw, 'High')
    tex_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{Texture'), '1')
    tex_vr_val = q_map.get(tex_vr_raw, 'Medium')

    # Texture 2D Rating
    if is_liner:
        if tex_2d_val == "Low":
            tex_2d_rating, tex_2d_color, tex_2d_label = "optimum", "emerald", "OPTIMUM"
            tex_2d_tip = "Description: Base texture map resolution for scenery, airports, and cockpits.\nCurrent: LOW saves 6-8 GB VRAM, preventing D3D12 paging freezes at busy hubs while cockpit vector screens remain sharp.\nRecommendation: Maintain LOW for all airliner flights (Axel LFBO rule)."
            tex_2d_reason = "Axel LFBO rule: saves 6-8 GB VRAM, preventing D3D12 paging freezes at dense hubs while vector instruments stay sharp."
        elif tex_2d_val == "Medium":
            tex_2d_rating, tex_2d_color, tex_2d_label = "optimum", "emerald", "OPTIMUM"
            tex_2d_tip = "Description: Base texture map resolution for scenery, airports, and cockpits.\nCurrent: MEDIUM provides balanced textures with safe VRAM headroom for airliners.\nRecommendation: LOW is preferred for maximum stability at heavy airports; MEDIUM is safe with 16+ GB VRAM."
            tex_2d_reason = "Balanced texture resolution with adequate VRAM headroom for airliners."
        elif tex_2d_val == "High":
            tex_2d_rating = "acceptable" if vram_gb >= 16.0 else "suboptimal"
            tex_2d_color = "amber" if vram_gb >= 16.0 else "orange"
            tex_2d_label = "ACCEPTABLE" if vram_gb >= 16.0 else "SUBOPTIMAL"
            tex_2d_tip = f"Description: Base texture map resolution for scenery, airports, and cockpits.\nCurrent: HIGH consumes significant VRAM (~12-14 GB with complex airliners). Your GPU has {vram_gb:.0f} GB VRAM.\nRecommendation: Switch to LOW or MEDIUM for airliner flights to avoid sudden D3D12 memory paging freezes during landing."
            tex_2d_reason = f"High textures approach VRAM budget limits with airliners on {vram_gb:.0f} GB VRAM."
        else:
            tex_2d_rating, tex_2d_color, tex_2d_label = "hazard", "rose", "HAZARD"
            tex_2d_tip = "Description: Base texture map resolution for scenery, airports, and cockpits.\nCurrent: ULTRA textures consume 6-8 GB extra VRAM, triggering heavy D3D12 paging freezes on airliners.\nRecommendation: Switch to LOW immediately for airliner flights."
            tex_2d_reason = "ULTRA textures cause severe VRAM overflow and heavy stuttering on complex airliners."
    else:
        if tex_2d_val == "Ultra":
            tex_2d_rating = "optimum" if vram_gb >= 16.0 else "acceptable"
            tex_2d_color = "emerald" if vram_gb >= 16.0 else "amber"
            tex_2d_label = "OPTIMUM" if vram_gb >= 16.0 else "ACCEPTABLE"
            tex_2d_tip = "Description: Base texture map resolution for scenery, airports, and cockpits.\nCurrent: ULTRA provides maximum visual fidelity for low-altitude VFR flights.\nRecommendation: ULTRA is recommended for GA aircraft since they consume minimal VRAM."
            tex_2d_reason = "Maximum visual fidelity for low-altitude VFR. GA aircraft consume minimal VRAM."
        elif tex_2d_val == "High":
            tex_2d_rating, tex_2d_color, tex_2d_label = "optimum", "emerald", "OPTIMUM"
            tex_2d_tip = "Description: Base texture map resolution for scenery, airports, and cockpits.\nCurrent: HIGH offers crisp ground and cockpit textures with ample headroom for GA flights.\nRecommendation: Maintain HIGH or ULTRA for general aviation."
            tex_2d_reason = "Crisp ground and cockpit textures with ample headroom for GA flights."
        elif tex_2d_val == "Medium":
            tex_2d_rating, tex_2d_color, tex_2d_label = "acceptable", "amber", "ACCEPTABLE"
            tex_2d_tip = "Description: Base texture map resolution for scenery, airports, and cockpits.\nCurrent: MEDIUM provides good performance but slight texture blur at low altitude.\nRecommendation: Increase to HIGH or ULTRA for sharper scenery during VFR flights."
            tex_2d_reason = "Good performance, slight texture blur at low altitude."
        else:
            tex_2d_rating, tex_2d_color, tex_2d_label = "suboptimal", "orange", "SUBOPTIMAL"
            tex_2d_tip = "Description: Base texture map resolution for scenery, airports, and cockpits.\nCurrent: LOW causes visible texture blurring during low-altitude sightseeing.\nRecommendation: Increase to HIGH or ULTRA for VFR general aviation."
            tex_2d_reason = "Unnecessarily blurry for VFR sightseeing flights when VRAM is plentiful."

    # Texture VR Rating
    if is_liner:
        if tex_vr_val == "Low":
            tex_vr_rating, tex_vr_color, tex_vr_label = "optimum", "emerald", "OPTIMUM"
            tex_vr_tip = "Description: Base texture map resolution in VR stereo rendering.\nCurrent: LOW frees 6-8 GB VRAM, preventing VR compositor crashes and paging stutters while cockpit vector instruments stay crisp.\nRecommendation: Maintain LOW for all airliner flights in VR (Axel LFBO rule)."
            tex_vr_reason = "Essential Axel LFBO trick in VR: frees 6-8 GB VRAM, preventing VR compositor crashes and paging stutters."
        elif tex_vr_val == "Medium":
            tex_vr_rating = "optimum" if vram_gb >= 16.0 else "acceptable"
            tex_vr_color = "emerald" if vram_gb >= 16.0 else "amber"
            tex_vr_label = "OPTIMUM" if vram_gb >= 16.0 else "ACCEPTABLE"
            tex_vr_tip = "Description: Base texture map resolution in VR stereo rendering.\nCurrent: MEDIUM provides a good balance in VR stereo rendering.\nRecommendation: LOW is recommended for maximum stability at heavy airports; MEDIUM is viable with 16+ GB VRAM."
            tex_vr_reason = "Medium textures provide good balance in VR stereo rendering."
        elif tex_vr_val == "High":
            tex_vr_rating = "suboptimal" if vram_gb >= 16.0 else "hazard"
            tex_vr_color = "orange" if vram_gb >= 16.0 else "rose"
            tex_vr_label = "SUBOPTIMAL" if vram_gb >= 16.0 else "HAZARD"
            tex_vr_tip = "Description: Base texture map resolution in VR stereo rendering.\nCurrent: HIGH demands extreme VRAM in VR stereo, risking frame drops and reprojection judder.\nRecommendation: Switch to LOW or MEDIUM for airliners in VR."
            tex_vr_reason = "High textures in VR stereo demand extreme VRAM, risking frame drops on airliners."
        else:
            tex_vr_rating, tex_vr_color, tex_vr_label = "hazard", "rose", "HAZARD"
            tex_vr_tip = "Description: Base texture map resolution in VR stereo rendering.\nCurrent: ULTRA causes severe VRAM overflow and headset compositor tracking freezes.\nRecommendation: Set to LOW immediately for VR airliner flights."
            tex_vr_reason = "Ultra textures in VR cause severe VRAM overflow and headset tracking freezes."
    else:
        if tex_vr_val in ["Medium", "High"]:
            tex_vr_rating, tex_vr_color, tex_vr_label = "optimum", "emerald", "OPTIMUM"
            tex_vr_tip = "Description: Base texture map resolution in VR stereo rendering.\nCurrent: Sharp scenery textures for VFR immersion without overloading VR buffers.\nRecommendation: Maintain MEDIUM or HIGH for VFR flights in VR."
            tex_vr_reason = "Sharp scenery textures for VFR immersion without overloading VR buffers."
        elif tex_vr_val == "Low":
            tex_vr_rating, tex_vr_color, tex_vr_label = "acceptable", "amber", "ACCEPTABLE"
            tex_vr_tip = "Description: Base texture map resolution in VR stereo rendering.\nCurrent: LOW gives smooth performance but softer terrain textures in VR.\nRecommendation: Increase to MEDIUM for sharper terrain."
            tex_vr_reason = "Smooth performance but softer terrain textures in VR."
        else:
            tex_vr_rating, tex_vr_color, tex_vr_label = "hazard", "rose", "HAZARD"
            tex_vr_tip = "Description: Base texture map resolution in VR stereo rendering.\nCurrent: ULTRA can saturate VR stereo buffers even in GA aircraft.\nRecommendation: Reduce to HIGH or MEDIUM in VR."
            tex_vr_reason = "Ultra textures can saturate VR stereo buffers even in GA."

    # VR Max Frame Rate Rating
    is_vr_fps_opt = (fps_vr == str(target_vr_fps))
    vr_fps_rating = "optimum" if is_vr_fps_opt else "suboptimal"
    vr_fps_color = "emerald" if is_vr_fps_opt else "orange"
    vr_fps_label = "OPTIMUM" if is_vr_fps_opt else "SUBOPTIMAL"
    vr_fps_tooltip = f"Description: VR frame rate cap in UserCfg.opt to synchronize with headset reprojection interval. Direct numeric input supported.\nCurrent: {fps_vr} FPS ({'Matched to 1/2 sync' if is_vr_fps_opt else 'Mismatched'}).\nRecommendation: Lock to {target_vr_fps} FPS (exact 1/2 sync divisor of your {vr_hz} Hz headset) to guarantee judder-free motion reprojection."
    vr_fps_reason = f"Matches exact 1/2 sync divisor of {vr_hz} Hz headset ({target_vr_fps} FPS), delivering smooth motion reprojection." if is_vr_fps_opt else f"Target frame rate ({fps_vr} FPS) does not match the 1/2 sync divisor ({target_vr_fps} FPS) of your {vr_hz} Hz headset, causing motion judder."

    # ===============================================
    # PAGE 2: TERRAIN & ENVIRONMENT WORLD (9 SETTINGS)
    # ===============================================

    # 10. TLOD (Manual input up to 400 + Presets)
    tlod_2d_raw = get_block_val(r'LoDFactor\s+([\d\.]+)', extract_block(g2d, '{Terrain'), '1.0')
    tlod_2d_val = round(float(tlod_2d_raw) * 100)
    tlod_vr_raw = get_block_val(r'LoDFactor\s+([\d\.]+)', extract_block(gvr, '{Terrain'), '1.0')
    tlod_vr_val = round(float(tlod_vr_raw) * 100)

    # TLOD 2D Rating
    if is_liner:
        tlod_2d_rating = "optimum" if autofps or tlod_2d_val <= 120 else ("acceptable" if tlod_2d_val <= 150 else "hazard")
        tlod_2d_color = "emerald" if autofps or tlod_2d_val <= 120 else ("amber" if tlod_2d_val <= 150 else "rose")
        tlod_2d_label = "OPTIMUM" if autofps or tlod_2d_val <= 120 else ("ACCEPTABLE" if tlod_2d_val <= 150 else "HAZARD")
        tlod_2d_reason = "AutoFPS dynamic calibration active." if autofps else ("Within safe CPU MainThread budget for airliners." if tlod_2d_val <= 120 else ("MainThread pressure: possible micro-stutters during landing." if tlod_2d_val <= 150 else "High stutter risk: CPU MainThread saturation on approach."))
    else:
        tlod_2d_rating = "optimum" if autofps or tlod_2d_val <= 160 else "acceptable"
        tlod_2d_color = "emerald" if autofps or tlod_2d_val <= 160 else "amber"
        tlod_2d_label = "OPTIMUM" if autofps or tlod_2d_val <= 160 else "ACCEPTABLE"
        tlod_2d_reason = "AutoFPS dynamic calibration active." if autofps else ("Optimum draw distance for VFR terrain fidelity." if tlod_2d_val <= 160 else "Acceptable draw distance for GA flights.")

    # 11. OLOD (Manual input up to 400 + Presets)
    olod_2d_raw = get_block_val(r'LoDFactor\s+([\d\.]+)', extract_block(g2d, '{ObjectsLoD'), '1.0')
    olod_2d_val = round(float(olod_2d_raw) * 100)
    olod_vr_raw = get_block_val(r'LoDFactor\s+([\d\.]+)', extract_block(gvr, '{ObjectsLoD'), '1.0')
    olod_vr_val = round(float(olod_vr_raw) * 100)

    # 12. Offscreen Pre-Caching
    pre_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{OffscreenTerrainPreCaching'), '2')
    pre_2d_val = q_map.get(pre_2d_raw, 'High')
    pre_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{OffscreenTerrainPreCaching'), '2')
    pre_vr_val = q_map.get(pre_vr_raw, 'High')

    # 13. Volumetric Clouds
    cld_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{VolumetricClouds'), '2')
    cld_2d_val = q_map.get(cld_2d_raw, 'High')
    cld_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{VolumetricClouds'), '2')
    cld_vr_val = q_map.get(cld_vr_raw, 'High')

    # 14. Buildings Quality
    bld_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{Buildings'), '2')
    bld_2d_val = q_map.get(bld_2d_raw, 'High')
    bld_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{Buildings'), '1')
    bld_vr_val = q_map.get(bld_vr_raw, 'Medium')

    # 15. Trees Quality
    tree_2d_raw = get_block_val(r'TreesQuality\s+(\d+)', extract_block(g2d, '{Procedural'), '2')
    tree_2d_val = q_map.get(tree_2d_raw, 'High')
    tree_vr_raw = get_block_val(r'TreesQuality\s+(\d+)', extract_block(gvr, '{Procedural'), '1')
    tree_vr_val = q_map.get(tree_vr_raw, 'Medium')

    # 16. Grass & Bushes Quality
    grass_2d_raw = get_block_val(r'GrassQuality\s+(\d+)', extract_block(g2d, '{Procedural'), '2')
    grass_2d_val = q_map.get(grass_2d_raw, 'High')
    grass_vr_raw = get_block_val(r'GrassQuality\s+(\d+)', extract_block(gvr, '{Procedural'), '0')
    grass_vr_val = q_map.get(grass_vr_raw, 'Low')

    # 17. Water Waves Simulation
    water_2d_raw = get_block_val(r'FFTSize\s+(\d+)', extract_block(g2d, '{Water'), '512')
    water_2d_val = fft_map.get(water_2d_raw, 'High (512)')
    water_vr_raw = get_block_val(r'FFTSize\s+(\d+)', extract_block(gvr, '{Water'), '256')
    water_vr_val = fft_map.get(water_vr_raw, 'Medium (256)')

    # 18. Displacement Mapping
    disp_2d = "ON" if get_block_val(r'Enabled\s+(\d+)', extract_block(g2d, '{DisplacementMapping'), '0') == '1' else "OFF"
    disp_vr = "ON" if get_block_val(r'Enabled\s+(\d+)', extract_block(gvr, '{DisplacementMapping'), '0') == '1' else "OFF"

    # ==========================================================
    # PAGE 3: LIGHTING, AVIONICS & POST-PROCESSING (9 SETTINGS)
    # ==========================================================

    # 19. Glass Cockpit Refresh Rate (Critical for CPU MainThread!)
    glass_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{GlassCockpitsRefreshRate'), '2')
    glass_2d_val = glass_map.get(glass_2d_raw, 'High (Full)')
    glass_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{GlassCockpitsRefreshRate'), '0')
    glass_vr_val = glass_map.get(glass_vr_raw, 'Low (Quarter)')

    # 20. Shadow Maps Resolution
    shd_2d_raw = get_block_val(r'Size\s+(\d+)', extract_block(g2d, '{Shadows'), '1536')
    shd_2d_val = shadow_map.get(shd_2d_raw, 'High (1536)')
    shd_vr_raw = get_block_val(r'Size\s+(\d+)', extract_block(gvr, '{Shadows'), '1024')
    shd_vr_val = shadow_map.get(shd_vr_raw, 'Medium (1024)')

    # 21. Terrain Shadows
    tshd_2d_raw = get_block_val(r'Size\s+(\d+)', extract_block(g2d, '{HeightFieldShadows'), '512')
    tshd_2d_val = hf_map.get(tshd_2d_raw, 'High (512)')
    tshd_vr_raw = get_block_val(r'Size\s+(\d+)', extract_block(gvr, '{HeightFieldShadows'), '256')
    tshd_vr_val = hf_map.get(tshd_vr_raw, 'Medium (256)')

    # 22. Contact Shadows
    cshd_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{ContactShadows'), '2')
    cshd_2d_val = q_map.get(cshd_2d_raw, 'High')
    cshd_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{ContactShadows'), '1')
    cshd_vr_val = q_map.get(cshd_vr_raw, 'Medium')

    # 23. Ambient Occlusion (SSAO)
    ssao_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{SSAO'), '2')
    ssao_2d_val = q_map.get(ssao_2d_raw, 'High')
    ssao_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{SSAO'), '0')
    ssao_vr_val = q_map.get(ssao_vr_raw, 'Low')

    # 24. Screen Space Reflections (SSR)
    ssr_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{SSR'), '2')
    ssr_2d_val = q_map.get(ssr_2d_raw, 'High')
    ssr_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{SSR'), '0')
    ssr_vr_val = q_map.get(ssr_vr_raw, 'Low')

    # 25. Volumetric Lights
    vl_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{VolumetricLights'), '2')
    vl_2d_val = q_map.get(vl_2d_raw, 'High')
    vl_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{VolumetricLights'), '0')
    vl_vr_val = q_map.get(vl_vr_raw, 'Low')

    # 26. Anisotropic Filtering
    aniso_2d_raw = get_block_val(r'MaxAnisotropy\s+(\d+)', extract_block(g2d, '{Texture'), '16')
    aniso_2d_val = f"{aniso_2d_raw}X" if aniso_2d_raw != '0' else "OFF"
    aniso_vr_raw = get_block_val(r'MaxAnisotropy\s+(\d+)', extract_block(gvr, '{Texture'), '16')
    aniso_vr_val = f"{aniso_vr_raw}X" if aniso_vr_raw != '0' else "OFF"

    # 27. Windshield Effects
    wind_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{WindShield'), '2')
    wind_2d_val = q_map.get(wind_2d_raw, 'High')
    wind_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{WindShield'), '2')
    wind_vr_val = q_map.get(wind_vr_raw, 'High')

    # Preset Options Lists
    fps_options = ["Unlocked", "30", "36", "40", "45", "60", "72", "80", "82", "90", "120", "144", "165", "240"]
    lod_options = ["50", "80", "100", "120", "150", "180", "200", "250", "300", "350", "400"]
    q_options = ["Ultra", "High", "Medium", "Low"]
    glass_options = ["High (Full)", "Medium (Half)", "Low (Quarter)"]
    water_options = ["Ultra (1024)", "High (512)", "Medium (256)", "Low (128)"]
    shadow_options = ["Ultra (2048)", "High (1536)", "Medium (1024)", "Low (512)"]
    hf_options = ["Ultra (1024)", "High (512)", "Medium (256)", "Low (128)"]
    aniso_options = ["16X", "8X", "4X", "2X", "OFF"]

    # Glass Cockpit Ratings
    glass_2d_opt = (glass_2d_val != 'High (Full)') if is_liner else True
    glass_2d_rating = "optimum" if glass_2d_opt else "suboptimal"
    glass_2d_color = "emerald" if glass_2d_opt else "orange"
    glass_2d_label = "OPTIMUM" if glass_2d_opt else "SUBOPTIMAL"
    glass_2d_reason = "Avionics screen refresh throttled to save 5-8 ms CPU MainThread frame time on airliners." if (is_liner and glass_2d_opt) else ("Full glass refresh delivers smooth synthetic vision in GA aircraft." if not is_liner else "Full glass refresh heavily loads CPU MainThread on complex airliners.")
    glass_2d_tip = f"Description: Vector glass cockpit avionics redraw rate (PFD, ND, MFD, FMC screens). Major driver of CPU MainThread load!\nCurrent: {glass_2d_val}.\nRecommendation: {'Airliners: Set to MEDIUM (Half) or LOW (Quarter) to throttle avionics redraws, saving 5-8 ms MainThread frame time on complex payware airliners (Fenix, PMDG).' if is_liner else 'GA: HIGH (Full) for silky smooth synthetic vision.'}"

    glass_vr_opt = (glass_vr_val == 'Low (Quarter)')
    glass_vr_rating = "optimum" if glass_vr_opt else "acceptable"
    glass_vr_color = "emerald" if glass_vr_opt else "amber"
    glass_vr_label = "OPTIMUM" if glass_vr_opt else "ACCEPTABLE"
    glass_vr_reason = "Quarter-rate avionics refresh in VR frees critical CPU MainThread cycles for stereo reprojection." if glass_vr_opt else "Avionics refresh above quarter-rate increases MainThread load in VR."
    glass_vr_tip = f"Description: Vector glass cockpit avionics redraw rate in VR.\nCurrent: {glass_vr_val}.\nRecommendation: Set to LOW (Quarter) in VR to preserve critical CPU frame time budget for headset reprojection."

    # Build 2D Matrix (27 Items across 3 Pages of 9)
    matrix_2d = [
        # PAGE 1: CORE & DISPLAY PACING (9)
        make_setting_item("resolution", "Full Screen Resolution", res_formatted, res_raw, True, "optimum", "emerald", "OPTIMUM", f"Description: Native screen rendering resolution for MSFS.\nCurrent: {res_formatted} (shared with 2D windowing).\nRecommendation: Match physical monitor native resolution and leverage DLSS for optimal sharpness.", ["3840 x 2160", "2560 x 1440", "1920 x 1080"], page=1, tag_reason="Native display resolution ensures 1:1 pixel rendering clarity without scaling blur."),
        make_setting_item("anti_aliasing", "Anti-Aliasing & Upscaling", val_aa_2d, aa_2d, False, "optimum" if "DLSS" in val_aa_2d else "acceptable", "emerald" if "DLSS" in val_aa_2d else "amber", "OPTIMUM" if "DLSS" in val_aa_2d else "ACCEPTABLE", f"Description: Anti-aliasing method and AI upscaling mode (DLSS/TAA/DLAA).\nCurrent: {val_aa_2d}.\nRecommendation: Use DLSS Quality on RTX GPUs for superior edge stability with 20-30% GPU performance headroom.", ["DLSS (Quality)", "DLSS (Balanced)", "DLSS (Performance)", "TAA", "DLAA"], page=1, tag_reason="DLSS delivers superior edge stability and GPU headroom." if "DLSS" in val_aa_2d else "TAA provides native clarity at higher raster workload."),
        make_setting_item("max_frame_rate", "Max Frame Rate", f"{fps_2d} FPS" if fps_2d != '0' else "Unlocked", fps_2d, False, "optimum" if fps_2d in ['60', '72', '80', '82', '90'] else "suboptimal", "emerald" if fps_2d in ['60', '72', '80', '82', '90'] else "orange", "OPTIMUM" if fps_2d in ['60', '72', '80', '82', '90'] else "SUBOPTIMAL", f"Description: Frame rate limiter to synchronize frame delivery with monitor refresh intervals. Direct numeric input supported.\nCurrent: {fps_2d} FPS ({'Synchronized' if fps_2d in ['60', '72', '80', '82', '90'] else 'Unlocked/Custom'}).\nRecommendation: Lock to an exact sync divisor of your monitor (e.g. 60, 72, 80, 82, 90 FPS) to eliminate frame pacing jitter.", fps_options, page=1, is_numeric=True, min_val=0, max_val=240, step=1, tag_reason="Synchronized with monitor refresh divisor for zero judder." if fps_2d in ['60', '72', '80', '82', '90'] else "Uncapped or mismatched framerate causes micro-stutters and uneven frame pacing."),
        make_setting_item("frame_generation", "Frame Generation", fg_2d, fg_2d_raw, False, "optimum" if fg_2d.startswith("DLSSG") else "acceptable", "emerald" if fg_2d.startswith("DLSSG") else "amber", "OPTIMUM" if fg_2d.startswith("DLSSG") else "ACCEPTABLE", f"Description: AI optical flow frame interpolation (DLSS 3 Frame Generation / FSR 3).\nCurrent: {fg_2d}.\nRecommendation: Keep ON (DLSSG 2X) in 2D mode for doubled motion smoothness without increasing CPU MainThread load.", ["DLSSG (2X)", "FSR3 (2X)", "OFF"], page=1, tag_reason="Doubles motion smoothness via optical flow without CPU overhead." if fg_2d.startswith("DLSSG") else "Frame generation is inactive; native rendering requires more CPU/GPU pacing."),
        make_setting_item("framerate_multiplier", "Framerate Multiplier", f"{mult_2d}X", mult_2d, False, "optimum", "emerald", "OPTIMUM", f"Description: Number of interpolated frames generated per native frame.\nCurrent: {mult_2d}X.\nRecommendation: Set to 1 (2X interpolation) when Frame Generation is active.", ["1 (2X Interpolation)"], page=1, tag_reason="Standard 2X optical flow interpolation factor."),
        make_setting_item("vsync", "V-Sync", vsync_val, vsync_raw, True, "optimum" if vsync_val == "ON" else "acceptable", "emerald" if vsync_val == "ON" else "amber", "OPTIMUM" if vsync_val == "ON" else "ACCEPTABLE", f"Description: Vertical synchronization with physical monitor refresh cycle.\nCurrent: {vsync_val}.\nRecommendation: Keep ON with G-Sync/FreeSync and frame rate limiter to eliminate screen tearing.", ["ON", "OFF"], page=1, tag_reason="V-Sync locks buffer presentation to refresh boundaries, eliminating tearing." if vsync_val == "ON" else "V-Sync OFF may cause horizontal tearing lines during fast camera pans."),
        make_setting_item("dynamic_settings", "Dynamic Settings", dyn_2d, "0" if dyn_2d == "OFF" else "1", False, "optimum" if dyn_2d == "OFF" else "suboptimal", "emerald" if dyn_2d == "OFF" else "orange", "OPTIMUM" if dyn_2d == "OFF" else "SUBOPTIMAL", f"Description: Dynamic internal resolution scaling during heavy scenes.\nCurrent: {dyn_2d}.\nRecommendation: Keep OFF. Dynamic resolution triggers fluctuating cockpit blur and inconsistent image clarity.", ["OFF", "ON"], page=1, tag_reason="Disabled dynamic scaling guarantees consistent render sharpness in all phases." if dyn_2d == "OFF" else "Dynamic scaling lowers resolution unpredictably, blurring cockpit screens."),
        make_setting_item("reflex", "NVIDIA Reflex", reflex_2d, reflex_2d, False, "optimum" if reflex_2d in ["ON", "ON+BOOST"] else "suboptimal", "emerald" if reflex_2d in ["ON", "ON+BOOST"] else "orange", "OPTIMUM" if reflex_2d in ["ON", "ON+BOOST"] else "SUBOPTIMAL", f"Description: NVIDIA Reflex low-latency GPU queue pacing technology.\nCurrent: {reflex_2d}.\nRecommendation: Set to ON or ON+BOOST for responsive flight controls and minimum render queue latency.", ["ON", "ON+BOOST", "OFF"], page=1, tag_reason="Drains GPU render queue to minimize input latency." if reflex_2d in ["ON", "ON+BOOST"] else "Reflex OFF increases input-to-display latency during flight maneuvers."),
        make_setting_item("texture_resolution", "Texture Resolution", tex_2d_val, tex_2d_raw, False, tex_2d_rating, tex_2d_color, tex_2d_label, tex_2d_tip, q_options, page=1, tag_reason=tex_2d_reason),

        # PAGE 2: TERRAIN & ENVIRONMENT WORLD (9)
        make_setting_item("tlod", "Terrain LOD (TLOD)", f"{tlod_2d_val}" if not autofps else f"Dynamic ({tlod_2d_val})", str(tlod_2d_val), False, tlod_2d_rating, tlod_2d_color, tlod_2d_label, f"Description: Terrain mesh geometric complexity and photogrammetry draw distance. Major driver of CPU MainThread frame time! Direct numeric input supported up to 400.\nCurrent: {tlod_2d_val}{' (Managed by AutoFPS)' if autofps else ''}.\nRecommendation: {'Airliners: Keep 100-120 (or dynamic with AutoFPS) to ensure CPU MainThread stays under 25ms during landing flare.' if is_liner else 'GA: 150-200 provides rich ground relief and mountain detail.'}", lod_options, page=2, is_numeric=True, min_val=10, max_val=400, step=5, tag_reason=tlod_2d_reason),
        make_setting_item("olod", "Objects LOD (OLOD)", f"{olod_2d_val}" if not autofps else f"Dynamic ({olod_2d_val})", str(olod_2d_val), False, "optimum" if olod_2d_val <= 150 else "acceptable", "emerald" if olod_2d_val <= 150 else "amber", "OPTIMUM" if olod_2d_val <= 150 else "ACCEPTABLE", f"Description: Geometric draw distance for 3D airport buildings, hangars, and autogen. Direct numeric input supported up to 400.\nCurrent: {olod_2d_val}.\nRecommendation: 100-120 for airliners; 120-150 for GA. Values above 200 severely increase CPU draw calls at busy airports.", lod_options, page=2, is_numeric=True, min_val=10, max_val=400, step=5, tag_reason="Balanced 3D building draw distance with controlled draw call count." if olod_2d_val <= 150 else "Elevated draw distance increases CPU draw call overhead at dense hubs."),
        make_setting_item("offscreen_precaching", "Off Screen Pre-Caching", pre_2d_val, pre_2d_raw, False, "optimum" if pre_2d_val in ["High", "Ultra"] else "hazard", "emerald" if pre_2d_val in ["High", "Ultra"] else "rose", "OPTIMUM" if pre_2d_val in ["High", "Ultra"] else "HAZARD", f"Description: Scenery pre-caching outside the immediate camera field of view.\nCurrent: {pre_2d_val}.\nRecommendation: HIGH or ULTRA is mandatory to eliminate camera panning stutters when looking around the cockpit.", q_options, page=2, tag_reason="Sufficient scenery pre-cached to prevent panning freezes." if pre_2d_val in ["High", "Ultra"] else "Low pre-caching causes stutter whenever camera view rotates."),
        make_setting_item("volumetric_clouds", "Volumetric Clouds", cld_2d_val, cld_2d_raw, False, "optimum" if cld_2d_val == "High" else "acceptable", "emerald" if cld_2d_val == "High" else "amber", "OPTIMUM" if cld_2d_val == "High" else "ACCEPTABLE", f"Description: Raymarched volumetric cloud rendering quality and boundary scattering.\nCurrent: {cld_2d_val}.\nRecommendation: HIGH delivers near-identical visual fidelity to Ultra with 15% better GPU performance in overcast weather.", q_options, page=2, tag_reason="Optimal volumetric raymarching quality without GPU fill-rate drop." if cld_2d_val == "High" else "Cloud quality may impact GPU frame rate during heavy overcast."),
        make_setting_item("buildings", "Buildings Quality", bld_2d_val, bld_2d_raw, False, "optimum" if bld_2d_val in ["High", "Ultra"] else "acceptable", "emerald" if bld_2d_val in ["High", "Ultra"] else "amber", "OPTIMUM" if bld_2d_val in ["High", "Ultra"] else "ACCEPTABLE", f"Description: Procedural 3D buildings mesh detail, window reflections, and roof textures.\nCurrent: {bld_2d_val}.\nRecommendation: HIGH or ULTRA for crisp terminal and city structures with minimal performance impact.", q_options, page=2, tag_reason="Sharp 3D building geometry and roof textures."),
        make_setting_item("trees", "Trees Quality", tree_2d_val, tree_2d_raw, False, "optimum" if tree_2d_val in ["High", "Ultra"] else "acceptable", "emerald" if tree_2d_val in ["High", "Ultra"] else "amber", "OPTIMUM" if tree_2d_val in ["High", "Ultra"] else "ACCEPTABLE", f"Description: 3D tree canopy geometry density, draw distance, and foliage shadowing.\nCurrent: {tree_2d_val}.\nRecommendation: HIGH offers rich forests and realistic canopy cover with negligible performance cost.", q_options, page=2, tag_reason="High density 3D foliage with smooth LOD transitions."),
        make_setting_item("grass", "Grass & Bushes", grass_2d_val, grass_2d_raw, False, "optimum" if grass_2d_val in ["High", "Medium"] else "acceptable", "emerald" if grass_2d_val in ["High", "Medium"] else "amber", "OPTIMUM" if grass_2d_val in ["High", "Medium"] else "ACCEPTABLE", f"Description: Ground procedural turf, 3D grass, and wild flowers around airfields.\nCurrent: {grass_2d_val}.\nRecommendation: HIGH for GA grass airfields; MEDIUM is sufficient for paved airliner runways.", q_options, page=2, tag_reason="Natural airfield ground vegetation without excessive triangle density."),
        make_setting_item("water_waves", "Water Waves Simulation", water_2d_val, water_2d_raw, False, "optimum" if "512" in water_2d_val or "1024" in water_2d_val else "acceptable", "emerald" if "512" in water_2d_val or "1024" in water_2d_val else "amber", "OPTIMUM" if "512" in water_2d_val or "1024" in water_2d_val else "ACCEPTABLE", f"Description: Fast Fourier Transform (FFT) ocean and lake wave simulation resolution grid.\nCurrent: {water_2d_val}.\nRecommendation: HIGH (512) for realistic open water swells without GPU compute penalty.", water_options, page=2, tag_reason="High FFT wave resolution provides realistic ocean swells and reflections."),
        make_setting_item("displacement_mapping", "Displacement Mapping", disp_2d, "1" if disp_2d == "ON" else "0", False, "optimum" if disp_2d == "OFF" else "suboptimal", "emerald" if disp_2d == "OFF" else "orange", "OPTIMUM" if disp_2d == "OFF" else "SUBOPTIMAL", f"Description: Tessellated micro-surface height displacements on runway pavement and terrain.\nCurrent: {disp_2d}.\nRecommendation: Keep OFF to save VRAM and GPU compute. Visual difference from flight altitude is imperceptible.", ["OFF", "ON"], page=2, tag_reason="Displacement mapping disabled to conserve VRAM and GPU compute." if disp_2d == "OFF" else "Enables surface tessellation at the expense of extra VRAM and draw calls."),

        # PAGE 3: LIGHTING, AVIONICS & POST-PROCESSING (9)
        make_setting_item("glass_cockpits", "Glass Cockpit Refresh", glass_2d_val, glass_2d_raw, False, glass_2d_rating, glass_2d_color, glass_2d_label, glass_2d_tip, glass_options, page=3, tag_reason=glass_2d_reason),
        make_setting_item("shadow_maps", "Shadow Maps Resolution", shd_2d_val, shd_2d_raw, False, "optimum" if "1536" in shd_2d_val or "2048" in shd_2d_val else "acceptable", "emerald" if "1536" in shd_2d_val or "2048" in shd_2d_val else "amber", "OPTIMUM" if "1536" in shd_2d_val or "2048" in shd_2d_val else "ACCEPTABLE", f"Description: Direct sunlight shadow map buffer resolution for airframe and structures.\nCurrent: {shd_2d_val}.\nRecommendation: HIGH (1536) for clean shadow lines without shimmering.", shadow_options, page=3, tag_reason="High shadow map resolution delivers sharp cockpit and airframe shadows."),
        make_setting_item("terrain_shadows", "Terrain Shadows", tshd_2d_val, tshd_2d_raw, False, "optimum" if "512" in tshd_2d_val or "1024" in tshd_2d_val else "acceptable", "emerald" if "512" in tshd_2d_val or "1024" in tshd_2d_val else "amber", "OPTIMUM" if "512" in tshd_2d_val or "1024" in tshd_2d_val else "ACCEPTABLE", f"Description: Long-distance heightfield mountain and ridge self-shadowing.\nCurrent: {tshd_2d_val}.\nRecommendation: HIGH (512) for realistic mountain terrain relief during golden hour approaches.", hf_options, page=3, tag_reason="Realistic mountain shadowing during sunrise and sunset."),
        make_setting_item("contact_shadows", "Contact Shadows", cshd_2d_val, cshd_2d_raw, False, "optimum" if cshd_2d_val in ["High", "Ultra"] else "acceptable", "emerald" if cshd_2d_val in ["High", "Ultra"] else "amber", "OPTIMUM" if cshd_2d_val in ["High", "Ultra"] else "ACCEPTABLE", f"Description: Screen-space micro-shadows beneath wheels, switches, levers, and small cockpit fixtures.\nCurrent: {cshd_2d_val}.\nRecommendation: HIGH provides realistic contact depth in the cockpit with negligible GPU impact.", q_options, page=3, tag_reason="Enhances tactile depth around cockpit instruments and switches."),
        make_setting_item("ambient_occlusion", "Ambient Occlusion (SSAO)", ssao_2d_val, ssao_2d_raw, False, "optimum" if ssao_2d_val in ["High", "Ultra"] else "acceptable", "emerald" if ssao_2d_val in ["High", "Ultra"] else "amber", "OPTIMUM" if ssao_2d_val in ["High", "Ultra"] else "ACCEPTABLE", f"Description: Screen-space ambient occlusion (SSAO) providing realistic contact shading in crevices and corners.\nCurrent: {ssao_2d_val}.\nRecommendation: HIGH provides natural cockpit lighting and shadow depth without excessive shader overhead.", q_options, page=3, tag_reason="Natural contact shading in cockpit crevices and airframe recesses."),
        make_setting_item("reflections_ssr", "Screen Reflections (SSR)", ssr_2d_val, ssr_2d_raw, False, "optimum" if ssr_2d_val in ["High", "Ultra"] else "acceptable", "emerald" if ssr_2d_val in ["High", "Ultra"] else "amber", "OPTIMUM" if ssr_2d_val in ["High", "Ultra"] else "ACCEPTABLE", f"Description: Screen space reflections on wet runways, water puddles, and cockpit windshields.\nCurrent: {ssr_2d_val}.\nRecommendation: HIGH in 2D mode for realistic rainy runway reflections; LOW in VR mode to save GPU fill rate.", q_options, page=3, tag_reason="Realistic apron wetness reflections during rain and night lighting."),
        make_setting_item("volumetric_lights", "Volumetric Lights", vl_2d_val, vl_2d_raw, False, "optimum" if vl_2d_val in ["High", "Ultra"] else "acceptable", "emerald" if vl_2d_val in ["High", "Ultra"] else "amber", "OPTIMUM" if vl_2d_val in ["High", "Ultra"] else "ACCEPTABLE", f"Description: Atmospheric light beam scattering from runway lights, beacons, and landing lights in fog/clouds.\nCurrent: {vl_2d_val}.\nRecommendation: HIGH for dramatic night lighting and authentic low-visibility CAT III approaches.", q_options, page=3, tag_reason="Atmospheric light shaft rendering during night and low-visibility weather."),
        make_setting_item("anisotropic_filtering", "Anisotropic Filtering", aniso_2d_val, aniso_2d_raw, False, "optimum" if aniso_2d_val == "16X" else "acceptable", "emerald" if aniso_2d_val == "16X" else "amber", "OPTIMUM" if aniso_2d_val == "16X" else "ACCEPTABLE", f"Description: Texture sampling filter preventing runway markings and taxiway lines from blurring at acute angles.\nCurrent: {aniso_2d_val}.\nRecommendation: Set to 16X. Impact on modern GPUs is negligible (< 0.1 ms) and it ensures razor-sharp runway centerline lines.", aniso_options, page=3, tag_reason="16X anisotropic filtering keeps runway and taxiway markings sharp at glancing angles."),
        make_setting_item("windshield_effects", "Windshield Effects", wind_2d_val, wind_2d_raw, False, "optimum" if wind_2d_val in ["High", "Ultra"] else "acceptable", "emerald" if wind_2d_val in ["High", "Ultra"] else "amber", "OPTIMUM" if wind_2d_val in ["High", "Ultra"] else "ACCEPTABLE", f"Description: Dynamic raindrops, icing accretion, wiper blade sweeps, and glass reflection effects on windshield.\nCurrent: {wind_2d_val}.\nRecommendation: HIGH or ULTRA for full weather immersion on the flight deck.", q_options, page=3, tag_reason="Realistic dynamic rain, icing, and wiper sweep effects."),
    ]

    # Build VR Matrix (27 Items across 3 Pages of 9)
    matrix_vr = [
        # PAGE 1: CORE & DISPLAY PACING (9)
        make_setting_item("resolution", "Full Screen Resolution", res_formatted, res_raw, True, "optimum", "emerald", "OPTIMUM", f"Description: Desktop mirror resolution for MSFS VR mode.\nCurrent: {res_formatted} (shared with 2D windowing).\nRecommendation: Match your native screen resolution.", ["3840 x 2160", "2560 x 1440", "1920 x 1080"], page=1, tag_reason="Desktop mirror resolution."),
        make_setting_item("anti_aliasing", "Anti-Aliasing & Upscaling", val_aa_vr, aa_vr, False, "optimum" if "DLSS" in val_aa_vr else "acceptable", "emerald" if "DLSS" in val_aa_vr else "amber", "OPTIMUM" if "DLSS" in val_aa_vr else "ACCEPTABLE", f"Description: Anti-aliasing and upscaling mode in VR stereo.\nCurrent: {val_aa_vr}.\nRecommendation: DLSS Balanced or Quality is essential in VR to reduce stereo rendering load.", ["DLSS (Quality)", "DLSS (Balanced)", "DLSS (Performance)", "TAA"], page=1, tag_reason="DLSS reduces VR stereo rendering load while preserving cockpit clarity."),
        make_setting_item("max_frame_rate", "Max Frame Rate", f"{fps_vr} FPS" if fps_vr != '0' else "Unlocked", fps_vr, False, vr_fps_rating, vr_fps_color, vr_fps_label, vr_fps_tooltip, fps_options, page=1, is_numeric=True, min_val=0, max_val=240, step=1, tag_reason=vr_fps_reason),
        make_setting_item("frame_generation", "Frame Generation", fg_vr, fg_vr_raw, False, "optimum" if fg_vr == "OFF" else "hazard", "emerald" if fg_vr == "OFF" else "rose", "OPTIMUM" if fg_vr == "OFF" else "HAZARD", f"Description: AI optical flow frame generation in VR headsets.\nCurrent: {fg_vr}.\nRecommendation: Keep strictly OFF in VR. Frame generation adds motion-to-photon latency and causes severe head-tracking warping.", ["OFF", "DLSSG (2X)"], page=1, tag_reason="Frame generation OFF preserves native low-latency stereo head-tracking." if fg_vr == "OFF" else "Frame generation in VR causes severe motion judder and head-tracking distortion."),
        make_setting_item("framerate_multiplier", "Framerate Multiplier", f"{mult_vr}X", mult_vr, False, "optimum", "emerald", "OPTIMUM", f"Description: Multiplier in VR.\nCurrent: {mult_vr}X.\nRecommendation: Kept at 1 in VR.", ["1"], page=1, tag_reason="Standard multiplier for VR stereo."),
        make_setting_item("vsync", "V-Sync", vsync_val, vsync_raw, True, "optimum", "emerald", "OPTIMUM", f"Description: Global V-Sync state.\nCurrent: {vsync_val}.\nRecommendation: Handled by VR compositor.", ["ON", "OFF"], page=1, tag_reason="VR compositor manages display synchronization."),
        make_setting_item("dynamic_settings", "Dynamic Settings", dyn_vr, "0" if dyn_vr == "OFF" else "1", False, "optimum" if dyn_vr == "OFF" else "suboptimal", "emerald" if dyn_vr == "OFF" else "orange", "OPTIMUM" if dyn_vr == "OFF" else "SUBOPTIMAL", f"Description: Dynamic resolution in VR.\nCurrent: {dyn_vr}.\nRecommendation: Keep OFF in VR to avoid sudden stereo blurriness.", ["OFF", "ON"], page=1, tag_reason="Disabled dynamic scaling prevents sudden VR stereo resolution drops."),
        make_setting_item("reflex", "NVIDIA Reflex", reflex_vr, reflex_vr, False, "optimum" if reflex_vr in ["ON", "ON+BOOST"] else "suboptimal", "emerald" if reflex_vr in ["ON", "ON+BOOST"] else "orange", "OPTIMUM" if reflex_vr in ["ON", "ON+BOOST"] else "SUBOPTIMAL", f"Description: NVIDIA Reflex in VR.\nCurrent: {reflex_vr}.\nRecommendation: ON reduces VR motion-to-photon latency.", ["ON", "ON+BOOST", "OFF"], page=1, tag_reason="Reduces VR motion-to-photon latency."),
        make_setting_item("texture_resolution", "Texture Resolution", tex_vr_val, tex_vr_raw, False, tex_vr_rating, tex_vr_color, tex_vr_label, tex_vr_tip, q_options, page=1, tag_reason=tex_vr_reason),

        # PAGE 2: TERRAIN & ENVIRONMENT WORLD (9)
        make_setting_item("tlod", "Terrain LOD (TLOD)", f"{tlod_vr_val}" if not autofps else f"Dynamic ({tlod_vr_val})", str(tlod_vr_val), False, "optimum" if tlod_vr_val <= 100 else ("acceptable" if tlod_vr_val <= 120 else "hazard"), "emerald" if tlod_vr_val <= 100 else ("amber" if tlod_vr_val <= 120 else "rose"), "OPTIMUM" if tlod_vr_val <= 100 else ("ACCEPTABLE" if tlod_vr_val <= 120 else "HAZARD"), f"Description: Terrain mesh and photogrammetry draw distance in VR stereo. Direct numeric input supported up to 400.\nCurrent: {tlod_vr_val}{' (Managed by AutoFPS)' if autofps else ''}.\nRecommendation: Keep TLOD <= 100 in VR to protect stereo frame time budget and prevent motion reprojection drops.", lod_options, page=2, is_numeric=True, min_val=10, max_val=400, step=5, tag_reason="Dynamic AutoFPS management active." if autofps else ("Within safe VR stereo MainThread latency budget." if tlod_vr_val <= 100 else "High TLOD in VR triggers severe stereo reprojection judder.")),
        make_setting_item("olod", "Objects LOD (OLOD)", f"{olod_vr_val}" if not autofps else f"Dynamic ({olod_vr_val})", str(olod_vr_val), False, "optimum" if olod_vr_val <= 100 else "acceptable", "emerald" if olod_vr_val <= 100 else "amber", "OPTIMUM" if olod_vr_val <= 100 else "ACCEPTABLE", f"Description: 3D objects distance in VR up to 400.\nCurrent: {olod_vr_val}.\nRecommendation: Keep OLOD <= 100 in VR.", lod_options, page=2, is_numeric=True, min_val=10, max_val=400, step=5, tag_reason="Controlled 3D objects draw distance for VR stereo."),
        make_setting_item("offscreen_precaching", "Off Screen Pre-Caching", pre_vr_val, pre_vr_raw, False, "optimum" if pre_vr_val in ["High", "Ultra"] else "hazard", "emerald" if pre_vr_val in ["High", "Ultra"] else "rose", "OPTIMUM" if pre_vr_val in ["High", "Ultra"] else "HAZARD", f"Description: Scenery pre-caching in VR.\nCurrent: {pre_vr_val}.\nRecommendation: HIGH or ULTRA is essential for smooth head rotation in VR.", q_options, page=2, tag_reason="Essential for smooth head rotation without border popping in VR."),
        make_setting_item("volumetric_clouds", "Volumetric Clouds", cld_vr_val, cld_vr_raw, False, "optimum" if cld_vr_val in ["High", "Medium"] else "acceptable", "emerald" if cld_vr_val in ["High", "Medium"] else "amber", "OPTIMUM" if cld_vr_val in ["High", "Medium"] else "ACCEPTABLE", f"Description: Volumetric clouds in VR stereo.\nCurrent: {cld_vr_val}.\nRecommendation: HIGH or MEDIUM provides smooth frame pacing in VR.", q_options, page=2, tag_reason="Smooth frame pacing during cloudy flights in VR."),
        make_setting_item("buildings", "Buildings Quality", bld_vr_val, bld_vr_raw, False, "optimum" if bld_vr_val in ["High", "Medium"] else "acceptable", "emerald" if bld_vr_val in ["High", "Medium"] else "amber", "OPTIMUM" if bld_vr_val in ["High", "Medium"] else "ACCEPTABLE", f"Description: 3D building fidelity in VR.\nCurrent: {bld_vr_val}.\nRecommendation: HIGH or MEDIUM for optimal stereo performance.", q_options, page=2, tag_reason="Sharp building geometry in VR."),
        make_setting_item("trees", "Trees Quality", tree_vr_val, tree_vr_raw, False, "optimum" if tree_vr_val in ["High", "Medium"] else "acceptable", "emerald" if tree_vr_val in ["High", "Medium"] else "amber", "OPTIMUM" if tree_vr_val in ["High", "Medium"] else "ACCEPTABLE", f"Description: Trees geometry in VR.\nCurrent: {tree_vr_val}.\nRecommendation: HIGH or MEDIUM.", q_options, page=2, tag_reason="Optimized 3D trees geometry in VR."),
        make_setting_item("grass", "Grass & Bushes", grass_vr_val, grass_vr_raw, False, "optimum" if grass_vr_val in ["Low", "Medium"] else "acceptable", "emerald" if grass_vr_val in ["Low", "Medium"] else "amber", "OPTIMUM" if grass_vr_val in ["Low", "Medium"] else "ACCEPTABLE", f"Description: Ground procedural vegetation in VR.\nCurrent: {grass_vr_val}.\nRecommendation: LOW or MEDIUM saves GPU fill rate in VR stereo.", q_options, page=2, tag_reason="Balanced vegetation density for VR stereo."),
        make_setting_item("water_waves", "Water Waves Simulation", water_vr_val, water_vr_raw, False, "optimum" if "256" in water_vr_val or "512" in water_vr_val else "acceptable", "emerald" if "256" in water_vr_val or "512" in water_vr_val else "amber", "OPTIMUM" if "256" in water_vr_val or "512" in water_vr_val else "ACCEPTABLE", f"Description: Water FFT physics in VR.\nCurrent: {water_vr_val}.\nRecommendation: MEDIUM (256) or HIGH (512).", water_options, page=2, tag_reason="Realistic water wave physics in VR."),
        make_setting_item("displacement_mapping", "Displacement Mapping", disp_vr, "1" if disp_vr == "ON" else "0", False, "optimum" if disp_vr == "OFF" else "suboptimal", "emerald" if disp_vr == "OFF" else "orange", "OPTIMUM" if disp_vr == "OFF" else "SUBOPTIMAL", f"Description: Displacement mapping in VR.\nCurrent: {disp_vr}.\nRecommendation: Keep OFF in VR to save VRAM and GPU compute.", ["OFF", "ON"], page=2, tag_reason="Disabled displacement mapping saves GPU compute in VR."),

        # PAGE 3: LIGHTING, AVIONICS & POST-PROCESSING (9)
        make_setting_item("glass_cockpits", "Glass Cockpit Refresh", glass_vr_val, glass_vr_raw, False, glass_vr_rating, glass_vr_color, glass_vr_label, glass_vr_tip, glass_options, page=3, tag_reason=glass_vr_reason),
        make_setting_item("shadow_maps", "Shadow Maps Resolution", shd_vr_val, shd_vr_raw, False, "optimum" if "1024" in shd_vr_val or "1536" in shd_vr_val else "acceptable", "emerald" if "1024" in shd_vr_val or "1536" in shd_vr_val else "amber", "OPTIMUM" if "1024" in shd_vr_val or "1536" in shd_vr_val else "ACCEPTABLE", f"Description: Shadows buffer size in VR.\nCurrent: {shd_vr_val}.\nRecommendation: MEDIUM (1024) or HIGH (1536).", shadow_options, page=3, tag_reason="Clean shadow rendering in VR headset."),
        make_setting_item("terrain_shadows", "Terrain Shadows", tshd_vr_val, tshd_vr_raw, False, "optimum" if "256" in tshd_vr_val or "512" in tshd_vr_val else "acceptable", "emerald" if "256" in tshd_vr_val or "512" in tshd_vr_val else "amber", "OPTIMUM" if "256" in tshd_vr_val or "512" in tshd_vr_val else "ACCEPTABLE", f"Description: Heightfield mountain shadows in VR.\nCurrent: {tshd_vr_val}.\nRecommendation: MEDIUM (256) or HIGH (512).", hf_options, page=3, tag_reason="Terrain self-shadowing in VR."),
        make_setting_item("contact_shadows", "Contact Shadows", cshd_vr_val, cshd_vr_raw, False, "optimum" if cshd_vr_val in ["Medium", "High"] else "acceptable", "emerald" if cshd_vr_val in ["Medium", "High"] else "amber", "OPTIMUM" if cshd_vr_val in ["Medium", "High"] else "ACCEPTABLE", f"Description: Cockpit contact shadows in VR.\nCurrent: {cshd_vr_val}.\nRecommendation: MEDIUM or HIGH for cockpit depth.", q_options, page=3, tag_reason="Tactile depth for cockpit controls in VR."),
        make_setting_item("ambient_occlusion", "Ambient Occlusion (SSAO)", ssao_vr_val, ssao_vr_raw, False, "optimum" if ssao_vr_val in ["Low", "Medium"] else "acceptable", "emerald" if ssao_vr_val in ["Low", "Medium"] else "amber", "OPTIMUM" if ssao_vr_val in ["Low", "Medium"] else "ACCEPTABLE", f"Description: Ambient shading in VR.\nCurrent: {ssao_vr_val}.\nRecommendation: LOW or MEDIUM saves stereo fill rate.", q_options, page=3, tag_reason="Cockpit ambient shading in VR."),
        make_setting_item("reflections_ssr", "Screen Reflections (SSR)", ssr_vr_val, ssr_vr_raw, False, "optimum" if ssr_vr_val in ["Low", "Medium"] else "acceptable", "emerald" if ssr_vr_val in ["Low", "Medium"] else "amber", "OPTIMUM" if ssr_vr_val in ["Low", "Medium"] else "ACCEPTABLE", f"Description: Cockpit and puddle reflections in VR.\nCurrent: {ssr_vr_val}.\nRecommendation: LOW or MEDIUM to maintain high VR frame rates.", q_options, page=3, tag_reason="Puddle and glass reflections in VR."),
        make_setting_item("volumetric_lights", "Volumetric Lights", vl_vr_val, vl_vr_raw, False, "optimum" if vl_vr_val in ["Low", "Medium"] else "acceptable", "emerald" if vl_vr_val in ["Low", "Medium"] else "amber", "OPTIMUM" if vl_vr_val in ["Low", "Medium"] else "ACCEPTABLE", f"Description: Fog and landing light scattering in VR.\nCurrent: {vl_vr_val}.\nRecommendation: LOW or MEDIUM in VR.", q_options, page=3, tag_reason="Atmospheric light shafts in VR."),
        make_setting_item("anisotropic_filtering", "Anisotropic Filtering", aniso_vr_val, aniso_vr_raw, False, "optimum" if aniso_vr_val == "16X" else "acceptable", "emerald" if aniso_vr_val == "16X" else "amber", "OPTIMUM" if aniso_vr_val == "16X" else "ACCEPTABLE", f"Description: Ground texture sharpness in VR headset.\nCurrent: {aniso_vr_val}.\nRecommendation: 16X keeps runway lines sharp in VR.", aniso_options, page=3, tag_reason="16X filtering keeps runway lines sharp in VR."),
        make_setting_item("windshield_effects", "Windshield Effects", wind_vr_val, wind_vr_raw, False, "optimum" if wind_vr_val in ["High", "Ultra"] else "acceptable", "emerald" if wind_vr_val in ["High", "Ultra"] else "amber", "OPTIMUM" if wind_vr_val in ["High", "Ultra"] else "ACCEPTABLE", f"Description: Canopy rain and wipers in VR.\nCurrent: {wind_vr_val}.\nRecommendation: HIGH or ULTRA for cockpit immersion in VR.", q_options, page=3, tag_reason="Dynamic rain and wiper sweeps in VR."),
    ]

    # Cross-Settings Interdependences Analysis
    synergies_2d = []
    conflicts_2d = []
    synergies_vr = []
    conflicts_vr = []

    # 1. Frame Gen & V-Sync
    if fg_2d.startswith("DLSSG") and vsync_val == "ON":
        synergies_2d.append("DLSS Frame Gen + VSync: Smooth frame pacing without CPU MainThread load.")
    elif fg_2d.startswith("DLSSG") and vsync_val == "OFF":
        conflicts_2d.append("Frame Gen Active with VSync OFF: May cause micro-tearing and pacing jitter.")

    if fg_vr != "OFF":
        conflicts_vr.append("VR + Frame Generation: Severe motion distortion and tracking latency in headset. Keep OFF.")
    else:
        synergies_vr.append("Frame Gen OFF in VR: Native low-latency stereo head-tracking preserved.")

    # 2. Resolution & DLSS & Textures
    is_4k = "3840" in res_formatted
    if is_4k and "TAA" in val_aa_2d and tex_2d_val == "Ultra":
        conflicts_2d.append("4K Native TAA + Ultra Textures: Exceeds 15.8 GB VRAM. High risk of D3D12 paging freezes.")
    elif "DLSS" in val_aa_2d and tex_2d_val in ["Low", "Medium"]:
        synergies_2d.append("DLSS Upscaling + Low/Med Textures: Synergistic VRAM reduction (-8 GB) for zero-stutter flights.")

    # 3. Airliner vs GA TLOD & Avionics Refresh
    if is_liner and tlod_2d_val > 130 and not autofps:
        conflicts_2d.append(f"Airliner Profile + TLOD {tlod_2d_val}: High CPU MainThread load from avionics + high terrain draw.")
    elif is_liner and (tlod_2d_val <= 120 or autofps):
        synergies_2d.append("Airliner Profile + Controlled TLOD: Keeps MainThread latency under 25ms during landing flare.")

    if is_liner and glass_2d_val == 'High (Full)':
        conflicts_2d.append("Airliner Profile + High Glass Cockpits: Vector avionics (MFD/PFD/ND) severely stress CPU MainThread. Throttling to Medium/Low frees 5-8 ms.")
    elif is_liner and glass_2d_val in ['Medium (Half)', 'Low (Quarter)']:
        synergies_2d.append("Airliner Profile + Throttled Glass Cockpits: Balanced avionics refresh preserves MainThread budget.")

    # 4. AutoFPS Synergy
    if autofps:
        synergies_2d.append("AutoFPS Linked: Dynamic LOD management active, relaxing MainThread at busy airports.")
        synergies_vr.append("AutoFPS Linked: Dynamic VR LODs prevent stereo stutter on final approach.")

    # 5. VR Headset Sync Divisor
    if fps_vr == str(target_vr_fps):
        synergies_vr.append(f"VR {vr_hz} Hz Headset locked to exact 1/2 sync ({target_vr_fps} FPS): Maximum reprojection fluidity.")
    else:
        conflicts_vr.append(f"VR {vr_hz} Hz frame cap ({fps_vr} FPS) differs from 1/2 target ({target_vr_fps} FPS): Reprojection judder hazard.")

    # VRAM calculation
    vram_headroom_2d = "+ 6.4 GB FREE" if tex_2d_val == "Low" else ("+ 4.2 GB FREE" if tex_2d_val == "Medium" else "+ 2.1 GB FREE")
    vram_headroom_vr = "+ 5.6 GB FREE" if tex_vr_val == "Low" else ("+ 3.6 GB FREE" if tex_vr_val == "Medium" else "+ 1.2 GB FREE")

    return {
        "found": True,
        "path": path,
        "flight_profile": flight_profile,
        "vr_refresh_rate": vr_hz,
        "autofps_active": autofps,
        "matrix_2d": matrix_2d,
        "matrix_vr": matrix_vr,
        "target_pacing_2d": {
            "target_fps": f"{fps_2d} FPS" if fps_2d != '0' else "82 FPS",
            "frame_gen_label": "FRAME GEN 2X ACTIVE" if fg_2d.startswith("DLSSG") else "NATIVE SYNC",
            "frame_gen_color": "emerald" if fg_2d.startswith("DLSSG") else "slate",
            "target_mainthread": "24.4 ms" if fg_2d.startswith("DLSSG") else "12.2 ms",
            "mainthread_color": "emerald",
            "vram_headroom": vram_headroom_2d,
            "vram_color": "emerald"
        },
        "target_pacing_vr": {
            "target_fps": f"{fps_vr} FPS" if fps_vr != '0' else f"{target_vr_fps} FPS",
            "frame_gen_label": f"1/2 REPROJECTION ({target_vr_fps} FPS)",
            "frame_gen_color": "cyan",
            "target_mainthread": f"{target_vr_ms} ms",
            "mainthread_color": "emerald",
            "vram_headroom": vram_headroom_vr,
            "vram_color": "emerald"
        },
        "graphics_advisory_2d": {
            "status": "optimal" if not conflicts_2d else "suboptimal",
            "title": f"2D Graphics Profile Advisory ({'IFR Airliners' if is_liner else 'VFR General Aviation'})",
            "summary": f"Configured for {'complex airliners (Axel LFBO VRAM optimizations)' if is_liner else 'VFR general aviation flights'}.",
            "recommendations": [
                "Low/Medium textures eliminate D3D12 paging freezes with complex airliners." if is_liner else "High/Ultra textures maximize terrain & cockpit visual fidelity in GA.",
                "Offscreen Pre-Caching HIGH eliminates camera panning judder.",
                "Throttle Glass Cockpits to Medium/Low on airliners to protect CPU MainThread." if is_liner else "Full Glass Cockpit refresh provides peak synthetic vision fidelity."
            ],
            "synergies": synergies_2d,
            "conflicts": conflicts_2d
        },
        "graphics_advisory_vr": {
            "status": "optimal" if not conflicts_vr else "suboptimal",
            "title": f"VR Headset Profile Advisory ({vr_hz} Hz - {'IFR Airliners' if is_liner else 'VFR GA'})",
            "summary": f"Calibrated for {vr_hz} Hz VR Headset. {target_vr_fps} FPS lock provides 1/2 sync motion reprojection.",
            "recommendations": [
                f"Lock MSFS to {target_vr_fps} FPS for your {vr_hz} Hz headset to eliminate motion judder.",
                "Keep Frame Generation OFF in VR to avoid head-tracking latency and artifacting.",
                "Low textures in VR save 6-8 GB VRAM, preventing compositor crashes on heavy airliners." if is_liner else "Medium or High textures offer crisp immersion for VFR flights in VR."
            ],
            "synergies": synergies_vr,
            "conflicts": conflicts_vr
        }
    }


def update_msfs_user_cfg_setting(mode: str, setting_key: str, new_value: Any, user_cfg_path: Optional[str] = None, create_backup: bool = True) -> Dict[str, Any]:
    path = user_cfg_path or get_user_cfg_path()
    if not path or not os.path.exists(path):
        return {"status": "error", "message": "UserCfg.opt file not found."}

    backup_path = backup_user_cfg(path) if create_backup else None

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        mode = mode.upper()
        q_map_rev = {'ultra': '3', 'high': '2', 'medium': '1', 'low': '0'}
        fft_map_rev = {'ultra (1024)': '1024', 'high (512)': '512', 'medium (256)': '256', 'low (128)': '128', '1024': '1024', '512': '512', '256': '256', '128': '128'}
        glass_map_rev = {'high (full)': '2', 'medium (half)': '1', 'low (quarter)': '0', 'full': '2', 'half': '1', 'quarter': '0', 'high': '2', 'medium': '1', 'low': '0'}
        shadow_map_rev = {'ultra (2048)': '2048', 'high (1536)': '1536', 'medium (1024)': '1024', 'low (512)': '512', '2048': '2048', '1536': '1536', '1024': '1024', '512': '512'}
        hf_map_rev = {'ultra (1024)': '1024', 'high (512)': '512', 'medium (256)': '256', 'low (128)': '128', '1024': '1024', '512': '512', '256': '256', '128': '128'}

        # 1. Full Screen Resolution (Shared)
        if setting_key in ['resolution', 'FullScreenResolution']:
            clean_val = str(new_value).replace('x', ' ').replace('X', ' ')
            clean_val = " ".join(clean_val.split())
            content = re.sub(r'(FullScreenResolution\s+)[^\r\n]+', rf'\g<1>{clean_val}', content)

        # 2. Max Frame Rate (2D / VR + FrameLimiter)
        elif setting_key in ['max_frame_rate', 'TargetFrameRate']:
            k = 'TargetFrameRate' if mode == '2D' else 'TargetFrameRateVR'
            clean_val = str(new_value).replace('FPS', '').replace('Unlocked', '0').strip()
            content = re.sub(rf'({k}\s+)[^\r\n]+', rf'\g<1>{clean_val}', content)
            if mode == '2D':
                content = re.sub(r'(FrameLimiter\s+)[^\r\n]+', rf'\g<1>{clean_val}', content)

        # 3. Frame Generation
        elif setting_key in ['frame_generation', 'FrameGeneration']:
            k = 'FrameGeneration' if mode == '2D' else 'FrameGenerationVR'
            clean_val = 'DLSSG' if 'DLSSG' in str(new_value).upper() else ('FSR3' if 'FSR3' in str(new_value).upper() else 'NONE')
            content = re.sub(rf'({k}\s+)[^\r\n]+', rf'\g<1>{clean_val}', content)

        # 4. V-Sync (Shared)
        elif setting_key in ['vsync', 'VSync']:
            clean_val = '1' if str(new_value).upper() in ['1', 'ON', 'TRUE'] else '0'
            content = re.sub(r'(VSync\s+)[^\r\n]+', rf'\g<1>{clean_val}', content)

        # 5. Dynamic Settings
        elif setting_key in ['dynamic_settings', 'DynamicSettings']:
            k = 'DynamicSettings' if mode == '2D' else 'DynamicSettingsVR'
            clean_val = '1' if str(new_value).upper() in ['1', 'ON', 'TRUE'] else '0'
            content = re.sub(rf'({k}\s+)[^\r\n]+', rf'\g<1>{clean_val}', content)

        # 6. NVIDIA Reflex
        elif setting_key in ['reflex', 'Reflex']:
            k = 'Reflex' if mode == '2D' else 'ReflexVR'
            clean_val = 'ON_BOOST' if 'BOOST' in str(new_value).upper() else ('ON' if str(new_value).upper() in ['ON', '1', 'TRUE'] else 'OFF')
            content = re.sub(rf'({k}\s+)[^\r\n]+', rf'\g<1>{clean_val}', content)

        # 7. Anti-Aliasing & Upscaling
        elif setting_key in ['anti_aliasing', 'AntiAliasing']:
            aa_mode = 'DLSS' if 'DLSS' in str(new_value).upper() else ('TAA' if 'TAA' in str(new_value).upper() else 'DLAA')
            dlss_mode = 'QUALITY' if 'QUALITY' in str(new_value).upper() else ('BALANCED' if 'BALANCED' in str(new_value).upper() else ('PERFORMANCE' if 'PERFORMANCE' in str(new_value).upper() else 'OFF'))
            k_aa = 'AntiAliasing' if mode == '2D' else 'AntiAliasingVR'
            k_dlss = 'DLSSMode' if mode == '2D' else 'DLSSModeVR'
            content = re.sub(rf'({k_aa}\s+)[^\r\n]+', rf'\g<1>{aa_mode}', content)
            if dlss_mode != 'OFF':
                content = re.sub(rf'({k_dlss}\s+)[^\r\n]+', rf'\g<1>{dlss_mode}', content)

        # 8. TLOD (Supports up to 400 manual input)
        elif setting_key in ['tlod', 'TerrainLoD', 'LoDFactor']:
            clean_str = str(new_value).replace('Dynamic', '').replace('(', '').replace(')', '').replace('LOD', '').strip()
            num_val = max(10, min(400, float(clean_str)))
            val_f = f"{num_val / 100.0:.6f}"
            content = update_sub_block_setting(content, mode, '{Terrain', r'(LoDFactor\s+)[^\r\n]+', rf'\g<1>{val_f}')

        # 9. OLOD (Supports up to 400 manual input)
        elif setting_key in ['olod', 'ObjectsLoD']:
            clean_str = str(new_value).replace('Dynamic', '').replace('(', '').replace(')', '').replace('LOD', '').strip()
            num_val = max(10, min(400, float(clean_str)))
            val_f = f"{num_val / 100.0:.6f}"
            content = update_sub_block_setting(content, mode, '{ObjectsLoD', r'(LoDFactor\s+)[^\r\n]+', rf'\g<1>{val_f}')

        # 10. Offscreen Terrain Pre-Caching
        elif setting_key in ['offscreen_precaching', 'OffscreenTerrainPreCaching']:
            clean_q = q_map_rev.get(str(new_value).lower().strip(), '2')
            content = update_sub_block_setting(content, mode, '{OffscreenTerrainPreCaching', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}')

        # 11. Texture Resolution
        elif setting_key in ['texture_resolution', 'Texture']:
            clean_q = q_map_rev.get(str(new_value).lower().strip(), '2')
            content = update_sub_block_setting(content, mode, '{Texture', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}')

        # 12. Volumetric Clouds
        elif setting_key in ['volumetric_clouds', 'VolumetricClouds']:
            clean_q = q_map_rev.get(str(new_value).lower().strip(), '2')
            content = update_sub_block_setting(content, mode, '{VolumetricClouds', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}')

        # 13. Buildings Quality
        elif setting_key in ['buildings', 'Buildings']:
            clean_q = q_map_rev.get(str(new_value).lower().strip(), '2')
            content = update_sub_block_setting(content, mode, '{Buildings', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}')

        # 14. Trees Quality
        elif setting_key in ['trees', 'TreesQuality']:
            clean_q = q_map_rev.get(str(new_value).lower().strip(), '2')
            content = update_sub_block_setting(content, mode, '{Procedural', r'(TreesQuality\s+)[^\r\n]+', rf'\g<1>{clean_q}')

        # 15. Grass Quality
        elif setting_key in ['grass', 'GrassQuality']:
            clean_q = q_map_rev.get(str(new_value).lower().strip(), '2')
            content = update_sub_block_setting(content, mode, '{Procedural', r'(GrassQuality\s+)[^\r\n]+', rf'\g<1>{clean_q}')

        # 16. Water Waves Simulation
        elif setting_key in ['water_waves', 'Water']:
            clean_val = fft_map_rev.get(str(new_value).lower().strip(), '512')
            content = update_sub_block_setting(content, mode, '{Water', r'(FFTSize\s+)[^\r\n]+', rf'\g<1>{clean_val}')

        # 17. Displacement Mapping
        elif setting_key in ['displacement_mapping', 'DisplacementMapping']:
            clean_val = '1' if str(new_value).upper() in ['1', 'ON', 'TRUE'] else '0'
            content = update_sub_block_setting(content, mode, '{DisplacementMapping', r'(Enabled\s+)[^\r\n]+', rf'\g<1>{clean_val}')

        # 18. Glass Cockpits Refresh Rate
        elif setting_key in ['glass_cockpits', 'GlassCockpitsRefreshRate']:
            clean_val = glass_map_rev.get(str(new_value).lower().strip(), '1')
            content = update_sub_block_setting(content, mode, '{GlassCockpitsRefreshRate', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_val}')

        # 19. Shadow Maps Resolution
        elif setting_key in ['shadow_maps', 'Shadows']:
            clean_val = shadow_map_rev.get(str(new_value).lower().strip(), '1536')
            content = update_sub_block_setting(content, mode, '{Shadows', r'(Size\s+)[^\r\n]+', rf'\g<1>{clean_val}')

        # 20. Terrain Shadows
        elif setting_key in ['terrain_shadows', 'HeightFieldShadows']:
            clean_val = hf_map_rev.get(str(new_value).lower().strip(), '512')
            content = update_sub_block_setting(content, mode, '{HeightFieldShadows', r'(Size\s+)[^\r\n]+', rf'\g<1>{clean_val}')

        # 21. Contact Shadows
        elif setting_key in ['contact_shadows', 'ContactShadows']:
            clean_q = q_map_rev.get(str(new_value).lower().strip(), '2')
            content = update_sub_block_setting(content, mode, '{ContactShadows', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}')

        # 22. Ambient Occlusion (SSAO)
        elif setting_key in ['ambient_occlusion', 'SSAO']:
            clean_q = q_map_rev.get(str(new_value).lower().strip(), '2')
            content = update_sub_block_setting(content, mode, '{SSAO', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}')

        # 23. Screen Space Reflections (SSR)
        elif setting_key in ['reflections_ssr', 'SSR']:
            clean_q = q_map_rev.get(str(new_value).lower().strip(), '2')
            content = update_sub_block_setting(content, mode, '{SSR', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}')

        # 24. Volumetric Lights
        elif setting_key in ['volumetric_lights', 'VolumetricLights']:
            clean_q = q_map_rev.get(str(new_value).lower().strip(), '2')
            content = update_sub_block_setting(content, mode, '{VolumetricLights', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}')

        # 25. Anisotropic Filtering
        elif setting_key in ['anisotropic_filtering', 'MaxAnisotropy']:
            clean_val = str(new_value).upper().replace('X', '').replace('OFF', '0').strip()
            content = update_sub_block_setting(content, mode, '{Texture', r'(MaxAnisotropy\s+)[^\r\n]+', rf'\g<1>{clean_val}')

        # 26. Windshield Effects
        elif setting_key in ['windshield_effects', 'WindShield']:
            clean_q = q_map_rev.get(str(new_value).lower().strip(), '2')
            content = update_sub_block_setting(content, mode, '{WindShield', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}')

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "status": "success",
            "message": f"Updated {setting_key} to {new_value} for {mode} mode.",
            "backup_created": backup_path
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "backup_created": backup_path}


def apply_recommended_msfs_settings(mode: str, flight_profile: str = 'LINER', vr_refresh_rate: int = 72, user_cfg_path: Optional[str] = None) -> Dict[str, Any]:
    path = user_cfg_path or get_user_cfg_path()
    if not path or not os.path.exists(path):
        return {"status": "error", "message": "UserCfg.opt file not found."}

    backup_path = backup_user_cfg(path)
    mode = mode.upper()
    is_liner = (str(flight_profile).upper() == 'LINER')
    try:
        vr_hz = int(vr_refresh_rate)
    except Exception:
        vr_hz = 72
    target_vr_fps = max(30, vr_hz // 2)

    try:
        if mode == '2D':
            tex_val = 'Low' if is_liner else 'High'
            tlod_val = '100' if is_liner else '150'
            glass_val = 'Medium (Half)' if is_liner else 'High (Full)'
            
            # Page 1
            update_msfs_user_cfg_setting('2D', 'anti_aliasing', 'DLSS (Quality)', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'frame_generation', 'DLSSG (2X)', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'vsync', 'ON', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'max_frame_rate', '90', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'dynamic_settings', 'OFF', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'reflex', 'ON', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'texture_resolution', tex_val, path, create_backup=False)
            
            # Page 2
            update_msfs_user_cfg_setting('2D', 'tlod', tlod_val, path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'olod', '100', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'offscreen_precaching', 'High', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'volumetric_clouds', 'High', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'buildings', 'High', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'trees', 'High', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'grass', 'High', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'water_waves', 'High (512)', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'displacement_mapping', 'OFF', path, create_backup=False)
            
            # Page 3
            update_msfs_user_cfg_setting('2D', 'glass_cockpits', glass_val, path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'shadow_maps', 'High (1536)', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'terrain_shadows', 'High (512)', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'contact_shadows', 'High', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'ambient_occlusion', 'High', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'reflections_ssr', 'High', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'volumetric_lights', 'High', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'anisotropic_filtering', '16X', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'windshield_effects', 'High', path, create_backup=False)
        else:
            tex_val = 'Low' if is_liner else 'Medium'
            glass_val = 'Low (Quarter)' if is_liner else 'Medium (Half)'
            
            # Page 1
            update_msfs_user_cfg_setting('VR', 'anti_aliasing', 'DLSS (Balanced)', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'frame_generation', 'OFF', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'vsync', 'ON', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'max_frame_rate', str(target_vr_fps), path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'dynamic_settings', 'OFF', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'reflex', 'ON', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'texture_resolution', tex_val, path, create_backup=False)
            
            # Page 2
            update_msfs_user_cfg_setting('VR', 'tlod', '100', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'olod', '100', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'offscreen_precaching', 'High', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'volumetric_clouds', 'High', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'buildings', 'Medium', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'trees', 'Medium', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'grass', 'Low', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'water_waves', 'Medium (256)', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'displacement_mapping', 'OFF', path, create_backup=False)
            
            # Page 3
            update_msfs_user_cfg_setting('VR', 'glass_cockpits', glass_val, path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'shadow_maps', 'Medium (1024)', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'terrain_shadows', 'Medium (256)', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'contact_shadows', 'Medium', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'ambient_occlusion', 'Low', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'reflections_ssr', 'Low', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'volumetric_lights', 'Low', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'anisotropic_filtering', '16X', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'windshield_effects', 'High', path, create_backup=False)

        profile_desc = "IFR Airliners (Axel LFBO VRAM Saver)" if is_liner else "VFR General Aviation (High Detail)"
        return {
            "status": "success",
            "message": f"Optimal {mode} profile applied for {profile_desc} across 27 settings!",
            "backup_created": os.path.basename(backup_path),
            "profile": "LINER" if is_liner else "GA",
            "mode": mode,
            "target_vr_fps": target_vr_fps if mode == 'VR' else 90
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "backup_created": os.path.basename(backup_path) if backup_path else ""}


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


def get_full_rig_diagnostics(flight_profile: str = 'LINER', vr_refresh_rate: int = 72) -> Dict[str, Any]:
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
    matrix_data = build_msfs_settings_matrix(user_cfg_path=cfg.get("path"), gpu_info=gpu, cpu_info=cpu, flight_profile=flight_profile, vr_refresh_rate=vr_refresh_rate)
    backups = get_available_user_cfg_backups(cfg.get("path"))

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
        "settings_matrix": matrix_data,
        "backups": backups
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
