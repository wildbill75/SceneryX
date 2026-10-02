#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SceneryX Flight Rig Optimizer & Hardware Intelligence Engine (v1.0.1)
Module autonome d'auto-détection matérielle, de calcul de synchronisation d'affichage (Frame Pacing),
de calibrage VRAM / CPU et de génération de profils optimisés par studio d'avionique.
"""

import os
import sys
import time
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

def simplify_cpu_name(raw_name: str) -> str:
    """Nettoie et raccourcit le nom du CPU pour l'affichage en capitales épurées."""
    if not raw_name:
        return "UNKNOWN CPU"
    s = raw_name
    for token in ['(R)', '(TM)', 'Processor', 'CPU', '12-Core', '16-Core', '24-Core', '8-Core', '6-Core', '4-Core', '32-Core']:
        s = s.replace(token, '')
    s = re.sub(r'@\s*[\d\.]+\s*[GgMm][Hh][Zz]', '', s)
    s = re.sub(r'\b\d+(?:st|nd|rd|th)\s+Gen\b', '', s, flags=re.IGNORECASE)
    s = ' '.join(s.split()).upper()
    return s


def simplify_gpu_name(raw_name: str) -> str:
    """Nettoie et raccourcit le nom du GPU pour l'affichage en capitales épurées."""
    if not raw_name:
        return "UNKNOWN GPU"
    s = raw_name
    for token in ['(R)', '(TM)', 'Graphics', 'Video Controller']:
        s = s.replace(token, '')
    s = ' '.join(s.split()).upper()
    return s


def detect_cpu_info() -> Dict[str, Any]:
    """Détecte le processeur, le nombre de cœurs/threads et la vitesse via WinReg et ctypes en ~0.1ms."""
    result = {
        "name": "Unknown CPU",
        "name_simplified": "UNKNOWN CPU",
        "cores": 0,
        "threads": 0,
        "max_clock_mhz": 0,
        "raw_string": ""
    }
    # Stratégie 1 : Registry + GetLogicalProcessorInformationEx (Ultra-rapide ~0.1ms, 0 sous-processus)
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DESCRIPTION\System\CentralProcessor\0')
        raw_name, _ = winreg.QueryValueEx(key, 'ProcessorNameString')
        raw_mhz, _ = winreg.QueryValueEx(key, '~MHz')
        winreg.CloseKey(key)
        name = str(raw_name).strip()
        mhz = int(raw_mhz or 0)

        cores = 0
        RelationProcessorCore = 0
        length = ctypes.c_ulong(0)
        ctypes.windll.kernel32.GetLogicalProcessorInformationEx(RelationProcessorCore, None, ctypes.byref(length))
        if length.value > 0:
            buf = ctypes.create_string_buffer(length.value)
            if ctypes.windll.kernel32.GetLogicalProcessorInformationEx(RelationProcessorCore, buf, ctypes.byref(length)):
                ptr = 0
                while ptr < length.value:
                    rel = int.from_bytes(buf[ptr:ptr+4], 'little')
                    size = int.from_bytes(buf[ptr+4:ptr+8], 'little')
                    if rel == RelationProcessorCore:
                        cores += 1
                    ptr += size

        threads = os.cpu_count() or 8
        if cores == 0:
            cores = max(1, threads // 2)

        result["name"] = name
        result["name_simplified"] = simplify_cpu_name(name)
        result["cores"] = cores
        result["threads"] = threads
        result["max_clock_mhz"] = mhz
        result["raw_string"] = f"{name} ({cores}C/{threads}T)"
        return result
    except Exception:
        pass

    # Stratégie 2 : WMI COM In-Process (~15ms)
    try:
        import win32com.client
        wmi = win32com.client.GetObject('winmgmts:')
        for proc in wmi.InstancesOf('Win32_Processor'):
            name = str(proc.Name or '').strip()
            cores = int(proc.NumberOfCores or 0)
            threads = int(proc.NumberOfLogicalProcessors or 0)
            mhz = int(proc.MaxClockSpeed or 0)
            result["name"] = name
            result["name_simplified"] = simplify_cpu_name(name)
            result["cores"] = cores
            result["threads"] = threads
            result["max_clock_mhz"] = mhz
            result["raw_string"] = f"{name} ({cores}C/{threads}T)"
            return result
    except Exception:
        pass

    # Stratégie 3 : Fallback variables système
    result["name"] = os.environ.get("PROCESSOR_IDENTIFIER", "Intel/AMD Processor")
    result["name_simplified"] = simplify_cpu_name(result["name"])
    result["threads"] = os.cpu_count() or 8
    result["cores"] = max(1, result["threads"] // 2)
    result["raw_string"] = result["name"]
    return result


def detect_gpu_info() -> Dict[str, Any]:
    """Détecte la carte graphique NVIDIA/AMD, VRAM totale et Re-Size BAR."""
    result = {
        "name": "Unknown GPU",
        "name_simplified": "UNKNOWN GPU",
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
            result["name_simplified"] = simplify_gpu_name(result["name"])
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
        result["name_simplified"] = simplify_gpu_name(result["name"])
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
    """Détecte la RAM totale, la fréquence en MHz et l'activation du profil XMP/EXPO via WMI COM (~12ms)."""
    result = {
        "total_gb": 0.0,
        "speed_mhz": 0,
        "is_xmp_active": False,
        "stick_count": 0
    }
    # Stratégie 1 : WMI COM In-Process (~12ms, 0 sous-processus PowerShell)
    try:
        import win32com.client
        wmi = win32com.client.GetObject('winmgmts:')
        total_bytes = 0
        speeds = []
        stick_count = 0
        for stick in wmi.InstancesOf('Win32_PhysicalMemory'):
            stick_count += 1
            cap = int(stick.Capacity or 0)
            total_bytes += cap
            speed = int(stick.ConfiguredClockSpeed or stick.Speed or 0)
            if speed > 0:
                speeds.append(speed)

        if total_bytes > 0:
            result["total_gb"] = round(total_bytes / (1024**3), 1)
            result["stick_count"] = stick_count
            if speeds:
                result["speed_mhz"] = max(speeds)
                if result["speed_mhz"] >= 3200:
                    result["is_xmp_active"] = True
            return result
    except Exception:
        pass

    # Stratégie 2 : Windows GlobalMemoryStatusEx (~0.05ms pour total_gb)
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ('dwLength', ctypes.c_ulong),
                ('dwMemoryLoad', ctypes.c_ulong),
                ('ullTotalPhys', ctypes.c_ulonglong),
                ('ullAvailPhys', ctypes.c_ulonglong),
                ('ullTotalPageFile', ctypes.c_ulonglong),
                ('ullAvailPageFile', ctypes.c_ulonglong),
                ('ullTotalVirtual', ctypes.c_ulonglong),
                ('ullAvailVirtual', ctypes.c_ulonglong),
                ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            result["total_gb"] = round(stat.ullTotalPhys / (1024**3), 1)
    except Exception:
        pass

    return result


def detect_all_displays() -> List[Dict[str, Any]]:
    """Détecte tous les écrans connectés et configurés dans Windows avec leur résolution et Hz."""
    class DISPLAY_DEVICEW(ctypes.Structure):
        _fields_ = [
            ('cb', ctypes.wintypes.DWORD),
            ('DeviceName', ctypes.c_wchar * 32),
            ('DeviceString', ctypes.c_wchar * 128),
            ('StateFlags', ctypes.wintypes.DWORD),
            ('DeviceID', ctypes.c_wchar * 128),
            ('DeviceKey', ctypes.c_wchar * 128)
        ]
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

    wmi_names = []
    try:
        import win32com.client
        wmi = win32com.client.GetObject(r'winmgmts:root\wmi')
        for mon in wmi.InstancesOf('WmiMonitorID'):
            if mon.UserFriendlyName:
                name = ''.join(chr(c) for c in mon.UserFriendlyName if c != 0).strip()
                if name:
                    wmi_names.append(name)
    except Exception:
        pass

    displays = []
    try:
        d = DISPLAY_DEVICEW()
        d.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        i = 0
        display_num = 1
        while ctypes.windll.user32.EnumDisplayDevicesW(None, i, ctypes.byref(d), 0):
            if d.StateFlags & 1:  # DISPLAY_DEVICE_ATTACHED_TO_DESKTOP
                dm = DEVMODEW()
                dm.dmSize = ctypes.sizeof(DEVMODEW)
                if ctypes.windll.user32.EnumDisplaySettingsW(d.DeviceName, -1, ctypes.byref(dm)):
                    friendly = wmi_names[len(displays)] if len(displays) < len(wmi_names) else 'Monitor'
                    is_primary = bool(d.StateFlags & 4)
                    dev_num_str = d.DeviceName.replace(r'\\.\DISPLAY', '')
                    try:
                        num = int(dev_num_str)
                    except Exception:
                        num = display_num
                    displays.append({
                        "id": f"DISPLAY{num}",
                        "index": num,
                        "name": f"Display {num}: {friendly}",
                        "friendly_name": friendly,
                        "device_name": d.DeviceName,
                        "width": dm.dmPelsWidth,
                        "height": dm.dmPelsHeight,
                        "refresh_rate_hz": float(dm.dmDisplayFrequency),
                        "refresh_rate_int": int(dm.dmDisplayFrequency),
                        "formatted": f"{dm.dmPelsWidth}x{dm.dmPelsHeight} @ {dm.dmDisplayFrequency} Hz",
                        "is_primary": is_primary
                    })
                    display_num += 1
            i += 1
    except Exception:
        pass

    if not displays:
        displays.append({
            "id": "DISPLAY1",
            "index": 1,
            "name": "Display 1: Monitor",
            "friendly_name": "Monitor",
            "device_name": r"\\.\DISPLAY1",
            "width": 1920,
            "height": 1080,
            "refresh_rate_hz": 60.0,
            "refresh_rate_int": 60,
            "formatted": "1920x1080 @ 60 Hz",
            "is_primary": True
        })

    return displays


def detect_display_info(preferred_id: Optional[str] = None, displays_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Retourne les informations de l'écran actif (ou sélectionné si multi-écran)."""
    all_displays = displays_list if displays_list is not None else detect_all_displays()
    if preferred_id:
        p_str = str(preferred_id).strip().upper()
        for d in all_displays:
            if d["id"].upper() == p_str or str(d["index"]) == p_str or p_str in d["device_name"].upper():
                return d
    primary = next((d for d in all_displays if d.get("is_primary")), None)
    return primary or (all_displays[0] if all_displays else {
        "id": "DISPLAY1",
        "index": 1,
        "name": "Display 1: Monitor",
        "friendly_name": "Monitor",
        "device_name": r"\\.\DISPLAY1",
        "width": 2560,
        "height": 1440,
        "refresh_rate_hz": 60.0,
        "refresh_rate_int": 60,
        "formatted": "2560x1440 @ 60 Hz",
        "is_primary": True
    })


def detect_vr_headset() -> Dict[str, Any]:
    """
    Scanne le système au démarrage et détecte le casque VR connecté/configuré
    (Pimax Crystal / Crystal Light, Meta Quest, Valve Index, HTC Vive, HP Reverb G2 / WMR, etc.)
    ainsi que sa cadence de rafraîchissement native / configurée en Hz.
    """
    result = {
        "detected": False,
        "name": "None",
        "manufacturer": "None",
        "refresh_rate_hz": 72,
        "status": "Not Connected",
        "source": "None"
    }

    # 1. Écosystème Pimax (Pimax Crystal, Crystal Light, 8KX, etc.)
    try:
        pimax_profile_path = os.path.expandvars(r"%LOCALAPPDATA%\Pimax\runtime\profile.json")
        pimax_p3config = r"C:\Program Files\Pimax\Runtime\P3CONFIG.json"
        pimax_openxr = r"C:\Program Files\Pimax\Runtime\PiOpenXR_64.json"
        pimax_base = r"C:\Program Files\Pimax"

        if os.path.exists(pimax_profile_path) or os.path.exists(pimax_p3config) or os.path.exists(pimax_openxr) or os.path.exists(pimax_base):
            result["detected"] = True
            result["manufacturer"] = "Pimax"
            result["name"] = "Pimax Crystal Light"
            result["source"] = "Pimax Runtime"
            result["status"] = "Configured"

            if os.path.exists(pimax_p3config):
                try:
                    with open(pimax_p3config, 'r', encoding='utf-8', errors='ignore') as f:
                        p3_data = json.load(f)
                        hmd_list = p3_data.get('hmd', [])
                        if hmd_list and 'name' in hmd_list[0]:
                            result["name"] = hmd_list[0]['name']
                except Exception:
                    pass

            hz_found = None
            if os.path.exists(pimax_profile_path):
                try:
                    with open(pimax_profile_path, 'r', encoding='utf-8', errors='ignore') as f:
                        prof_data = json.load(f)
                        p_rate = prof_data.get('pixels_per_display_pixel_rate')
                        if p_rate is not None:
                            try:
                                scale_flt = round(float(p_rate), 2)
                                result["software_render_scale"] = scale_flt
                                result["software_render_scale_pct"] = round(scale_flt * 100)
                                result["software_name"] = "Pimax Play"
                            except Exception:
                                pass

                        for k, v in prof_data.items():
                            if isinstance(v, dict) and 'display_timing_selection' in v:
                                timing = v['display_timing_selection']
                                timing_map = {0: 120, 1: 90, 2: 72, 3: 80}
                                hz_found = timing_map.get(timing, 72)
                                break
                except Exception:
                    pass

            try:
                runtime_dir = os.path.expandvars(r"%LOCALAPPDATA%\Pimax\runtime")
                srv_logs = sorted(glob.glob(os.path.join(runtime_dir, 'pvr_srv_log_*.txt')), reverse=True)
                if srv_logs:
                    with open(srv_logs[0], 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        matches = re.findall(r'fps:\(a:[\d\.]+,c:([\d\.]+)\)', content)
                        if matches:
                            latest_fps = float(matches[-1])
                            if 65 <= latest_fps <= 76:
                                hz_found = 72
                            elif 76 < latest_fps <= 85:
                                hz_found = 80
                            elif 85 < latest_fps <= 95:
                                hz_found = 90
                            elif 110 <= latest_fps <= 125:
                                hz_found = 120
            except Exception:
                pass

            if hz_found:
                result["refresh_rate_hz"] = hz_found
            return result
    except Exception:
        pass

    # 2. Écosystème SteamVR (Valve Index, HTC Vive, Bigscreen Beyond, etc.)
    try:
        steamvr_settings = os.path.expandvars(r"%LOCALAPPDATA%\openvr\steamvr.vrsettings")
        if not os.path.exists(steamvr_settings):
            steamvr_settings = r"C:\Program Files (x86)\Steam\config\steamvr.vrsettings"

        if os.path.exists(steamvr_settings):
            with open(steamvr_settings, 'r', encoding='utf-8', errors='ignore') as f:
                svr_data = json.load(f)
                last_known = svr_data.get('LastKnown', {})
                hmd_model = last_known.get('HMDModel')
                if hmd_model:
                    result["detected"] = True
                    result["name"] = hmd_model
                    result["manufacturer"] = last_known.get('HMDManufacturer', 'SteamVR')
                    result["source"] = "SteamVR"
                    result["software_name"] = "SteamVR"
                    result["status"] = "Configured"
                    
                    svr_scale = svr_data.get('steamvr', {}).get('renderTargetScale')
                    if svr_scale is not None:
                        try:
                            scale_flt = round(float(svr_scale), 2)
                            result["software_render_scale"] = scale_flt
                            result["software_render_scale_pct"] = round(scale_flt * 100)
                        except Exception:
                            pass

                    if 'index' in hmd_model.lower():
                        result["refresh_rate_hz"] = 90
                    elif 'crystal' in hmd_model.lower():
                        result["refresh_rate_hz"] = 72
                    elif 'beyond' in hmd_model.lower():
                        result["refresh_rate_hz"] = 90
                    return result
    except Exception:
        pass

    # 3. Écosystème Meta / Oculus (Quest 2/3/Pro, Rift S)
    try:
        oculus_runtime = r"C:\Program Files\Oculus\Support\oculus-runtime"
        if os.path.exists(oculus_runtime):
            result["detected"] = True
            result["manufacturer"] = "Meta"
            result["name"] = "Meta Quest (Link)"
            result["source"] = "Oculus Runtime"
            result["software_name"] = "Meta Quest Link"
            result["refresh_rate_hz"] = 72
            result["status"] = "Configured"
            return result
    except Exception:
        pass

    # 4. Windows Mixed Reality (HP Reverb G2)
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Holographic"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            result["detected"] = True
            result["manufacturer"] = "HP / Microsoft"
            result["name"] = "HP Reverb G2 (WMR)"
            result["source"] = "WMR"
            result["refresh_rate_hz"] = 90
            result["status"] = "Configured"
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


_autofps_cache_timestamp: float = 0.0
_autofps_cached_result: bool = False

def detect_autofps_running() -> bool:
    """Detects if AutoFPS (MSFS AutoFPS / MSFS2024 AutoFPS) is active in background tasks via Toolhelp32 (~3ms)."""
    global _autofps_cache_timestamp, _autofps_cached_result
    now = time.time()
    if (now - _autofps_cache_timestamp) < 5.0:
        return _autofps_cached_result

    found = False
    try:
        TH32CS_SNAPPROCESS = 0x00000002
        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [
                ('dwSize', ctypes.wintypes.DWORD),
                ('cntUsage', ctypes.wintypes.DWORD),
                ('th32ProcessID', ctypes.wintypes.DWORD),
                ('th32DefaultHeapID', ctypes.c_void_p),
                ('th32ModuleID', ctypes.wintypes.DWORD),
                ('cntThreads', ctypes.wintypes.DWORD),
                ('th32ParentProcessID', ctypes.wintypes.DWORD),
                ('pcPriClassBase', ctypes.c_long),
                ('dwFlags', ctypes.wintypes.DWORD),
                ('szExeFile', ctypes.c_char * 260)
            ]
        hSnap = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if hSnap and hSnap != -1:
            pe = PROCESSENTRY32()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
            if ctypes.windll.kernel32.Process32First(hSnap, ctypes.byref(pe)):
                while True:
                    if b'autofps' in pe.szExeFile.lower():
                        found = True
                        break
                    if not ctypes.windll.kernel32.Process32Next(hSnap, ctypes.byref(pe)):
                        break
            ctypes.windll.kernel32.CloseHandle(hSnap)
    except Exception:
        found = False

    _autofps_cached_result = found
    _autofps_cache_timestamp = now
    return found


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


_cached_storage_info: Optional[Dict[str, Any]] = None

def detect_msfs_storage(user_cfg_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Detects the physical storage drive on which MSFS Packages are installed.
    Extracts InstalledPackagesPath from UserCfg.opt, queries physical disk model,
    drive type (NVMe SSD, SATA SSD, Mechanical HDD), and available storage capacity.
    Specifically flags mechanical HDDs to prevent severe terrain streaming bottlenecks.
    Uses DeviceIoControl and kernel queries for ~0.1ms execution.
    """
    global _cached_storage_info
    path = user_cfg_path or get_user_cfg_path()
    pkg_dir = "C:"
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.strip().startswith("InstalledPackagesPath"):
                        parts = line.strip().split(" ", 1)
                        if len(parts) > 1:
                            pkg_dir = parts[1].strip('"\'')
                        break
        except Exception:
            pass

    drive = os.path.splitdrive(pkg_dir)[0].rstrip(':').upper() or 'C'
    
    total_gb, free_gb, used_gb = 0.0, 0.0, 0.0
    try:
        u = shutil.disk_usage(f"{drive}:\\")
        free_gb = round(u.free / (1024**3), 1)
        total_gb = round(u.total / (1024**3), 1)
        used_gb = round((u.total - u.free) / (1024**3), 1)
    except Exception:
        pass

    if _cached_storage_info is not None and _cached_storage_info.get("drive_letter") == f"{drive}:":
        res = dict(_cached_storage_info)
        res["free_gb"] = free_gb
        res["total_gb"] = total_gb
        res["used_gb"] = used_gb
        res["packages_path"] = pkg_dir
        return res

    friendly_name = "Solid State Drive (SSD)"
    media_type = "SSD"
    bus_type = "NVMe"

    # Fast Kernel DeviceIoControl Query (~0.1ms)
    try:
        IOCTL_STORAGE_QUERY_PROPERTY = 0x002D1400
        vol_path = f"\\\\.\\{drive}:"
        h = ctypes.windll.kernel32.CreateFileW(vol_path, 0, 1 | 2, None, 3, 0, None)
        if h and h != -1:
            query = (ctypes.c_byte * 12)(0)
            out_buf = ctypes.create_string_buffer(1024)
            ret = ctypes.c_ulong(0)
            ok = ctypes.windll.kernel32.DeviceIoControl(h, IOCTL_STORAGE_QUERY_PROPERTY, query, 12, out_buf, 1024, ctypes.byref(ret), None)
            ctypes.windll.kernel32.CloseHandle(h)
            if ok:
                bus_id = out_buf[28] if len(out_buf) > 28 else 0
                if bus_id == 17:
                    bus_type = "NVMe"
                    media_type = "SSD"
                elif bus_id in [11, 15]:
                    bus_type = "SATA"
                    media_type = "SSD"
                prod_offset = int.from_bytes(out_buf[16:20], 'little')
                if 0 < prod_offset < 1024:
                    raw_str = out_buf[prod_offset:].split(b'\x00')[0]
                    parsed_name = raw_str.decode('latin1', errors='ignore').strip()
                    if parsed_name:
                        friendly_name = parsed_name
    except Exception:
        pass

    fn_upper = friendly_name.upper()
    mt_upper = media_type.upper()
    bt_upper = bus_type.upper()

    is_hdd = ('HDD' in mt_upper or 'HDD' in fn_upper or 'SPIN' in fn_upper or 'HARDDISK' in fn_upper)
    is_nvme = ('NVME' in bt_upper or 'NVME' in fn_upper)

    if is_hdd:
        tier = "MECHANICAL HDD"
        badge_color = "rose"
        warning = "CRITICAL: MSFS packages are installed on a mechanical hard drive (HDD). This causes severe terrain streaming bottlenecks, frequent photogrammetry stutters, and prolonged load times. Migrating to an NVMe or SATA SSD is strongly recommended."
    elif is_nvme:
        tier = "NVMe SSD"
        badge_color = "emerald"
        warning = None
    else:
        tier = "SATA SSD" if ('SSD' in mt_upper or 'SSD' in fn_upper) else "HIGH SPEED STORAGE"
        badge_color = "cyan"
        warning = None

    info = {
        "drive_letter": f"{drive}:",
        "packages_path": pkg_dir,
        "model": friendly_name,
        "media_type": media_type,
        "bus_type": bus_type,
        "tier": tier,
        "badge_color": badge_color,
        "is_hdd": is_hdd,
        "is_nvme": is_nvme,
        "free_gb": free_gb,
        "total_gb": total_gb,
        "used_gb": used_gb,
        "warning": warning
    }
    _cached_storage_info = info
    return info


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


def ensure_original_user_cfg_backup(user_cfg_path: Optional[str] = None) -> Optional[str]:
    """Ensures a permanent pristine copy of the user's original UserCfg.opt exists prior to any SceneryX tampering."""
    path = user_cfg_path or get_user_cfg_path()
    if not path or not os.path.exists(path):
        return None
    dir_name = os.path.dirname(path)
    original_path = os.path.join(dir_name, "UserCfg.opt.original")
    if os.path.exists(original_path):
        return original_path

    # If UserCfg.opt.original doesn't exist yet, check for existing backups to find the very oldest one
    base_name = os.path.basename(path)
    pattern = os.path.join(dir_name, f"{base_name}.backup_*")
    files = glob.glob(pattern)
    if files:
        # Sort by filename / timestamp suffix to get the earliest backup ever made by SceneryX
        oldest_backup = sorted(files)[0]
        try:
            shutil.copy2(oldest_backup, original_path)
            return original_path
        except Exception:
            pass

    # If no prior backup existed, copy the active UserCfg.opt directly
    try:
        shutil.copy2(path, original_path)
        return original_path
    except Exception:
        return None


def restore_original_user_cfg(user_cfg_path: Optional[str] = None) -> Dict[str, Any]:
    """Safely restores the user's original UserCfg.opt configuration from before SceneryX was first run."""
    path = user_cfg_path or get_user_cfg_path()
    if not path or not os.path.exists(path):
        return {"status": "error", "message": "UserCfg.opt path not detected."}
    dir_name = os.path.dirname(path)
    original_path = os.path.join(dir_name, "UserCfg.opt.original")

    if not os.path.exists(original_path):
        ensured = ensure_original_user_cfg_backup(path)
        if not ensured or not os.path.exists(ensured):
            return {"status": "error", "message": "Original UserCfg.opt backup not found."}
        original_path = ensured

    safety_backup = backup_user_cfg(path)
    try:
        shutil.copy2(original_path, path)
        clear_staged_settings()
        return {
            "status": "success",
            "message": "Original UserCfg.opt configuration restored successfully.",
            "safety_backup": os.path.basename(safety_backup)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def delete_user_cfg_backup(backup_target: str, user_cfg_path: Optional[str] = None) -> Dict[str, Any]:
    """Safely deletes an obsolete UserCfg.opt backup file."""
    path = user_cfg_path or get_user_cfg_path()
    if not path:
        return {"status": "error", "message": "UserCfg.opt path not detected."}
    dir_name = os.path.dirname(path)
    target_path = backup_target if os.path.isabs(backup_target) else os.path.join(dir_name, backup_target)
    # Critical safety guard: never allow deleting the active UserCfg.opt or the pristine UserCfg.opt.original
    if os.path.abspath(target_path) == os.path.abspath(path) or os.path.basename(target_path) == "UserCfg.opt.original":
        return {"status": "error", "message": "Cannot delete protected configuration files."}
    if not os.path.exists(target_path):
        return {"status": "error", "message": f"Backup file {backup_target} not found."}
    try:
        os.remove(target_path)
        return {
            "status": "success",
            "message": f"Successfully deleted {os.path.basename(target_path)}",
            "deleted_file": os.path.basename(target_path)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def open_user_cfg_folder(user_cfg_path: Optional[str] = None) -> Dict[str, Any]:
    """Opens the directory containing UserCfg.opt backups in Windows Explorer."""
    path = user_cfg_path or get_user_cfg_path()
    if not path:
        return {"status": "error", "message": "UserCfg.opt path not detected."}
    norm_path = os.path.normpath(path)
    dir_name = os.path.normpath(os.path.dirname(norm_path))
    if os.path.exists(dir_name):
        try:
            if os.path.exists(norm_path):
                subprocess.Popen(f'explorer.exe /select,"{norm_path}"', shell=True)
            else:
                subprocess.Popen(f'explorer.exe "{dir_name}"', shell=True)
            return {"status": "success", "folder": dir_name}
        except Exception as e:
            try:
                os.startfile(dir_name)
                return {"status": "success", "folder": dir_name}
            except Exception as e2:
                return {"status": "error", "message": f"{e}; {e2}"}
    return {"status": "error", "message": f"Folder {dir_name} not found."}


# ==============================================================================
# CUSTOM GRAPHICS PROFILES STORE (SAVE & ACTIVATE WITHOUT DIALOG SPAM)
# ==============================================================================

def get_custom_profiles_dir() -> str:
    """Returns directory where user custom graphics profiles are saved permanently."""
    appdata = os.environ.get('APPDATA')
    if appdata:
        profiles_dir = os.path.join(appdata, "SceneryX", "custom_profiles")
    else:
        profiles_dir = os.path.join(os.path.expanduser("~"), ".sceneryx", "custom_profiles")
    os.makedirs(profiles_dir, exist_ok=True)
    return profiles_dir


def _sync_and_recover_custom_profiles(profiles_dir: str):
    """Initializes custom profiles only if user directory is completely empty."""
    existing = glob.glob(os.path.join(profiles_dir, "*.profile.json"))
    if existing:
        return

    candidates = []
    ws_dir = r"D:\SceneryX\custom_profiles"
    if os.path.exists(ws_dir) and os.path.abspath(ws_dir) != os.path.abspath(profiles_dir):
        candidates.append(ws_dir)
    base_cp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_profiles")
    if os.path.exists(base_cp) and os.path.abspath(base_cp) != os.path.abspath(profiles_dir):
        candidates.append(base_cp)

    for src_dir in candidates:
        try:
            for pfile in glob.glob(os.path.join(src_dir, "*.profile.json")):
                fname = os.path.basename(pfile)
                dst = os.path.join(profiles_dir, fname)
                if not os.path.exists(dst):
                    try:
                        shutil.copy2(pfile, dst)
                    except Exception:
                        pass
            state_dst = os.path.join(profiles_dir, "active_profile.json")
            state_src = os.path.join(src_dir, "active_profile.json")
            if not os.path.exists(state_dst) and os.path.exists(state_src):
                try:
                    shutil.copy2(state_src, state_dst)
                except Exception:
                    pass
        except Exception:
            pass


def get_active_profile_id() -> str:
    """Returns the ID of the currently active profile. If none active, defaults to newest."""
    profiles_dir = get_custom_profiles_dir()
    _sync_and_recover_custom_profiles(profiles_dir)
    state_file = os.path.join(profiles_dir, "active_profile.json")
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                active_id = data.get("active_id", "")
                if active_id:
                    target_file = os.path.join(profiles_dir, f"{active_id}.profile.json")
                    if os.path.exists(target_file):
                        return active_id
        except Exception:
            pass
    all_profiles = glob.glob(os.path.join(profiles_dir, "*.profile.json"))
    if all_profiles:
        newest = max(all_profiles, key=os.path.getmtime)
        base = os.path.basename(newest)
        newest_id = base[:-len(".profile.json")]
        set_active_profile_id(newest_id)
        return newest_id
    return ""


def set_active_profile_id(profile_id: str):
    profiles_dir = get_custom_profiles_dir()
    state_file = os.path.join(profiles_dir, "active_profile.json")
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"active_id": profile_id, "updated_at": datetime.now().isoformat()}, f, indent=2)
    except Exception:
        pass
    ws_state = r"D:\SceneryX\custom_profiles\active_profile.json"
    if os.path.exists(os.path.dirname(ws_state)) and os.path.abspath(os.path.dirname(ws_state)) != os.path.abspath(profiles_dir):
        try:
            with open(ws_state, "w", encoding="utf-8") as f:
                json.dump({"active_id": profile_id, "updated_at": datetime.now().isoformat()}, f, indent=2)
        except Exception:
            pass


def get_custom_profiles() -> List[Dict[str, Any]]:
    """Lists all saved custom profiles, sorted newest first."""
    profiles_dir = get_custom_profiles_dir()
    _sync_and_recover_custom_profiles(profiles_dir)
    files = glob.glob(os.path.join(profiles_dir, "*.profile.json"))
    profiles = []
    active_id = get_active_profile_id()

    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as pf:
                data = json.load(pf)
                data["is_active"] = (data.get("id") == active_id)
                profiles.append(data)
        except Exception:
            pass

    profiles.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    if profiles and not any(p.get("is_active") for p in profiles):
        profiles[0]["is_active"] = True
        set_active_profile_id(profiles[0].get("id", ""))
    return profiles


def save_custom_profile(profile_name: str, user_cfg_path: Optional[str] = None) -> Dict[str, Any]:
    """Saves current settings (with any staged UI edits) as a reusable custom profile."""
    path = user_cfg_path or get_user_cfg_path()
    if not path or not os.path.exists(path):
        return {"status": "error", "message": "UserCfg.opt not found."}

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Overlay staged settings so current UI tweaks are captured
        global _staged_user_cfg_settings
        for m, staged in _staged_user_cfg_settings.items():
            for k, v in staged.items():
                content = apply_setting_to_content(content, m, k, v)

        name = str(profile_name).strip() if profile_name else ""
        if not name:
            name = f"Profile {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # Prevent duplicate profile names
        existing_profiles = list_custom_profiles()
        for p in existing_profiles:
            if str(p.get("name", "")).strip().lower() == name.lower():
                return {
                    "status": "error",
                    "code": "DUPLICATE_NAME",
                    "message": "Profile already exists. Please choose another name."
                }

        profile_id = f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        profiles_dir = get_custom_profiles_dir()
        profile_file = os.path.join(profiles_dir, f"{profile_id}.profile.json")

        profile_data = {
            "id": profile_id,
            "name": name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": content,
            "is_active": True
        }

        with open(profile_file, "w", encoding="utf-8") as pf:
            json.dump(profile_data, pf, indent=2, ensure_ascii=False)

        # Mirror to D:\SceneryX\custom_profiles if accessible
        ws_dir = r"D:\SceneryX\custom_profiles"
        if os.path.exists(ws_dir) and os.path.abspath(ws_dir) != os.path.abspath(profiles_dir):
            try:
                with open(os.path.join(ws_dir, f"{profile_id}.profile.json"), "w", encoding="utf-8") as pf_ws:
                    json.dump(profile_data, pf_ws, indent=2, ensure_ascii=False)
            except Exception:
                pass

        # Also write the updated content directly to UserCfg.opt so saving a profile applies it immediately
        with open(path, "w", encoding="utf-8") as f_cfg:
            f_cfg.write(content)

        # Mark as active
        set_active_profile_id(profile_id)

        # Clear staged overrides now saved
        clear_staged_settings()

        return {
            "status": "success",
            "message": f"Profile '{name}' saved successfully!",
            "profile": profile_data,
            "profiles": get_custom_profiles()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def activate_custom_profile(profile_id: str, user_cfg_path: Optional[str] = None) -> Dict[str, Any]:
    """Immediately activates a saved custom profile by writing its content to MSFS UserCfg.opt."""
    path = user_cfg_path or get_user_cfg_path()
    if not path or not os.path.exists(path):
        return {"status": "error", "message": "UserCfg.opt not found."}

    profiles_dir = get_custom_profiles_dir()
    profile_file = os.path.join(profiles_dir, f"{profile_id}.profile.json")
    if not os.path.exists(profile_file):
        return {"status": "error", "message": f"Profile '{profile_id}' not found."}

    try:
        with open(profile_file, "r", encoding="utf-8") as pf:
            profile_data = json.load(pf)

        content = profile_data.get("content", "")
        if not content:
            return {"status": "error", "message": "Profile content is empty."}

        # Ensure pristine original backup exists before overwriting
        ensure_original_user_cfg_backup(path)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        set_active_profile_id(profile_id)
        clear_staged_settings()

        return {
            "status": "success",
            "message": f"Profile '{profile_data.get('name')}' activated in MSFS!",
            "profile_id": profile_id,
            "profile_name": profile_data.get("name"),
            "profiles": get_custom_profiles()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def delete_custom_profile(profile_id: str) -> Dict[str, Any]:
    """Deletes one or multiple custom profiles."""
    profiles_dir = get_custom_profiles_dir()
    ids = [x.strip() for x in str(profile_id).split(",") if x.strip()]
    if not ids:
        return {"status": "error", "message": "No profile ID provided."}

    deleted_count = 0
    errors = []
    active_id = get_active_profile_id()
    active_was_deleted = False

    for pid in ids:
        profile_file = os.path.join(profiles_dir, f"{pid}.profile.json")
        try:
            if os.path.exists(profile_file):
                os.remove(profile_file)
                deleted_count += 1
            ws_file = os.path.join(r"D:\SceneryX\custom_profiles", f"{pid}.profile.json")
            if os.path.exists(ws_file):
                try:
                    os.remove(ws_file)
                except Exception:
                    pass
            if active_id == pid:
                active_was_deleted = True
        except Exception as e:
            errors.append(str(e))

    if active_was_deleted:
        set_active_profile_id("")

    if deleted_count == 0 and errors:
        return {"status": "error", "message": "; ".join(errors)}

    return {
        "status": "success",
        "message": f"{deleted_count} profile(s) deleted.",
        "profiles": get_custom_profiles()
    }


def apply_staged_user_cfg_to_disk(user_cfg_path: Optional[str] = None) -> Dict[str, Any]:
    """Writes all currently staged settings directly to UserCfg.opt on disk."""
    path = user_cfg_path or get_user_cfg_path()
    if not path or not os.path.exists(path):
        return {"status": "error", "message": "UserCfg.opt not found on system."}

    global _staged_user_cfg_settings
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        ensure_original_user_cfg_backup(path)

        for m, staged in _staged_user_cfg_settings.items():
            for k, v in staged.items():
                content = apply_setting_to_content(content, m, k, v)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        clear_staged_settings()
        set_active_profile_id("")

        return {
            "status": "success",
            "message": "All current graphics settings successfully applied directly to UserCfg.opt!",
            "path": path,
            "profiles": get_custom_profiles()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}



def analyze_system_balance(cpu_info: Dict[str, Any], gpu_info: Dict[str, Any], ram_info: Dict[str, Any], storage_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Evaluates system component harmony, bottleneck hazards, and memory stability."""
    if storage_info and storage_info.get("is_hdd"):
        model_str = storage_info.get("model") or "Mechanical HDD"
        drive_str = storage_info.get("drive_letter") or "C:"
        return {
            "status": "hdd_bottleneck",
            "tier": "Severe Storage Bottleneck (HDD)",
            "color": "rose",
            "summary": f"CRITICAL: MSFS Packages installed on a mechanical hard drive ({drive_str} {model_str}).",
            "advice": "Mechanical HDDs have seek times 100x slower than SSDs. Severe terrain pop-in, photogrammetry streaming drops, and 1-2 second freezes are inevitable until packages are moved to an NVMe or SATA SSD."
        }

    cpu_name = (cpu_info.get("name") or "").lower()
    gpu_name = (gpu_info.get("name") or "").lower()
    vram_gb = float(gpu_info.get("vram_total_gb") or 16.0)
    ram_gb = float(ram_info.get("total_gb") or 32.0)

    is_x3d = "x3d" in cpu_name or "3d v-cache" in cpu_name
    is_flagship_x3d = is_x3d and any(k in cpu_name for k in ["9850", "9800", "7800", "9950", "7950"])
    is_flagship_cpu = is_x3d or any(k in cpu_name for k in ["13900", "14900", "285k", "7950", "9950"])
    is_high_cpu = is_flagship_cpu or any(k in cpu_name for k in ["13700", "14700", "12900", "7700", "5800x3d", "13600", "14600"])
    is_legacy_cpu = any(k in cpu_name for k in ["8700", "9700", "9900", "10700", "3600", "3700", "2700", "1600", "2600", "i5-8", "i5-9", "i5-10", "i7-8", "i7-9"])

    is_flagship_5090 = "5090" in gpu_name
    is_flagship_gpu = is_flagship_5090 or any(k in gpu_name for k in ["5080", "4090", "4080", "7900 xtx", "7900xtx"]) or vram_gb >= 20.0
    is_high_gpu = is_flagship_gpu or any(k in gpu_name for k in ["4070 ti", "4070ti", "4070 super", "4070", "3090", "3080", "7900 xt", "7900xt", "7900 gre", "6800", "6900"]) or vram_gb >= 12.0
    is_vram_constrained = vram_gb <= 8.5

    if is_legacy_cpu and is_flagship_gpu:
        return {
            "status": "bottleneck",
            "tier": "CPU Bottleneck Risk",
            "color": "amber",
            "summary": "Older generation CPU paired with high-end GPU. MainThread will bottleneck at dense airports.",
            "advice": "Keep TLOD <= 100, reduce airport ground aircraft and vehicular traffic to keep MainThread below 33ms."
        }
    elif is_vram_constrained and is_high_cpu:
        return {
            "status": "vram_limit",
            "tier": "VRAM Constrained (8 GB)",
            "color": "amber",
            "summary": f"GPU has {vram_gb:.0f} GB VRAM. Risk of D3D12 paging stutters when flying complex paywares with Ultra textures.",
            "advice": "Set Texture Resolution to LOW or MEDIUM to prevent VRAM overflow and protect D3D12 frametimes."
        }
    elif is_flagship_x3d and is_flagship_gpu and ram_gb >= 32.0:
        return {
            "status": "elite",
            "tier": "Elite Simulation Monster Rig",
            "color": "emerald",
            "summary": "AMD 3D V-Cache processor paired with top-tier flagship GPU. Best-in-class MainThread frame pacing and unlimited raster margin.",
            "advice": "Your machine effortlessly powers through study-level airliners, dense payware hubs, and severe weather. You can safely run TLOD 180-200, DLAA, and Ultra settings with virtually zero landing stutter."
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


def update_sub_block_setting(content: str, mode: str, block_name: str, pattern: str, replacement: str, fallback_line: Optional[str] = None) -> str:
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
        if fallback_line:
            last_brace = mode_text.rfind('}')
            if last_brace != -1:
                new_block_str = f"\t{block_name}\n\t\t{fallback_line}\n\t}}\n"
                new_mode_text = mode_text[:last_brace] + new_block_str + mode_text[last_brace:]
                return content[:mode_idx] + new_mode_text + content[mode_boundary:]
        return content

    sub_end = mode_text.find('}', sub_start)
    if sub_end == -1:
        return content

    sub_slice = mode_text[sub_start:sub_end]
    if re.search(pattern, sub_slice):
        new_sub_slice = re.sub(pattern, replacement, sub_slice)
    elif fallback_line:
        new_sub_slice = sub_slice.rstrip() + f"\n\t\t{fallback_line}\n\t"
    else:
        new_sub_slice = sub_slice

    new_mode_text = mode_text[:sub_start] + new_sub_slice + mode_text[sub_end:]
    return content[:mode_idx] + new_mode_text + content[mode_boundary:]


_staged_user_cfg_settings: Dict[str, Dict[str, Any]] = {"2D": {}, "VR": {}}


def stage_msfs_setting(mode: str, setting_key: str, new_value: Any) -> Dict[str, Any]:
    global _staged_user_cfg_settings
    mode = (mode or '2D').upper()
    if mode == 'COMMON':
        for m in ['2D', 'VR']:
            if m not in _staged_user_cfg_settings:
                _staged_user_cfg_settings[m] = {}
            _staged_user_cfg_settings[m][setting_key] = new_value
    else:
        if mode not in _staged_user_cfg_settings:
            _staged_user_cfg_settings[mode] = {}
        _staged_user_cfg_settings[mode][setting_key] = new_value

    # Synchronize globally shared settings across both 2D and VR modes
    common_sync_keys = [
        'vsync', 'vsync_interval', 'resolution', 'fullscreenresolution', 'texture_resolution', 'texture', 'anisotropic_filtering', 'maxanisotropy',
        'aircraft_traffic_quantity', 'aircraft_traffic_variety', 'parked_aircraft_quantity', 'parked_aircraft_variety',
        'airport_services_quantity', 'airport_services_variety', 'road_traffic', 'sea_traffic',
        'characters_quantity', 'characters_variety', 'characters_quality', 'fauna_density', 'seatbelt_visibility'
    ]
    if str(setting_key).lower() in common_sync_keys:
        for m in ['2D', 'VR']:
            if m not in _staged_user_cfg_settings:
                _staged_user_cfg_settings[m] = {}
            _staged_user_cfg_settings[m][setting_key] = new_value

    return {"status": "success", "staged": True, "setting_key": setting_key, "new_value": new_value}


def clear_staged_settings(mode: Optional[str] = None):
    global _staged_user_cfg_settings
    if mode:
        _staged_user_cfg_settings[mode.upper()] = {}
    else:
        _staged_user_cfg_settings = {"2D": {}, "VR": {}}


def apply_setting_to_content(content: str, mode: str, setting_key: str, new_value: Any) -> str:
    mode = (mode or '2D').upper()
    if mode == 'COMMON':
        content = apply_setting_to_content(content, '2D', setting_key, new_value)
        content = apply_setting_to_content(content, 'VR', setting_key, new_value)
        return content

    q_map_rev = {'ultra': '3', 'high': '2', 'medium': '1', 'low': '0', '3': '3', '2': '2', '1': '1', '0': '0'}
    fft_map_rev = {'ultra (1024)': '1024', 'high (512)': '512', 'medium (256)': '256', 'low (128)': '128', '1024': '1024', '512': '512', '256': '256', '128': '128'}
    glass_map_rev = {'high (full)': '2', 'medium (half)': '1', 'low (quarter)': '0', 'full': '2', 'half': '1', 'quarter': '0', 'high': '2', 'medium': '1', 'low': '0'}
    shadow_map_rev = {'ultra (2048)': '2048', 'high (1536)': '1536', 'medium (1024)': '1024', 'low (512)': '512', '2048': '2048', '1536': '1536', '1024': '1024', '512': '512'}
    hf_map_rev = {'ultra (1024)': '1024', 'high (512)': '512', 'medium (256)': '256', 'low (128)': '128', '1024': '1024', '512': '512', '256': '256', '128': '128'}
    traffic_qty_map_rev = {'off': '-1', 'low': '0', 'medium': '1', 'high': '2', 'ultra': '3', '-1': '-1', '0': '0', '1': '1', '2': '2', '3': '3'}
    traffic_var_map_rev = {'low': '0', 'medium': '1', 'high': '2', 'ultra': '3', '0': '0', '1': '1', '2': '2', '3': '3'}
    reproj_map_rev = {
        'off': '0', '0': '0',
        'auto': '1', '1': '1',
        '1/2 reprojection': '2', '1/2': '2', '2': '2',
        '1/3 reprojection': '3', '1/3': '3', '3': '3',
        'depth & motion': '4', 'depth': '4', 'motion': '4', '4': '4'
    }

    # 1. Full Screen Resolution (Shared)
    if setting_key in ['resolution', 'FullScreenResolution']:
        clean_val = str(new_value).replace('x', ' ').replace('X', ' ')
        clean_val = " ".join(clean_val.split())
        content = re.sub(r'(FullScreenResolution\s+)[^\r\n]+', rf'\g<1>{clean_val}', content, flags=re.IGNORECASE)

    # 2. Max Frame Rate (2D / VR + FrameLimiter)
    elif setting_key in ['max_frame_rate', 'TargetFrameRate']:
        k = 'TargetFrameRate' if mode == '2D' else 'TargetFrameRateVR'
        clean_val = str(new_value).replace('FPS', '').replace('Unlocked', '0').replace('OFF', '0').replace('off', '0').strip()
        content = re.sub(rf'({k}\s+)[^\r\n]+', rf'\g<1>{clean_val}', content, flags=re.IGNORECASE)
        # Always synchronize engine-level FrameLimiter in UserCfg.opt with active mode's target (2D or VR)
        limiter_val = clean_val
        if limiter_val == '0':
            other_k = 'TargetFrameRateVR' if mode == '2D' else 'TargetFrameRate'
            m_other = re.search(rf'{other_k}\s+([-\d]+)', content, flags=re.IGNORECASE)
            other_val = m_other.group(1) if m_other else '0'
            if other_val != '0':
                limiter_val = other_val
        if re.search(r'(FrameLimiter\s+)[^\r\n]+', content, flags=re.IGNORECASE):
            content = re.sub(r'(FrameLimiter\s+)[^\r\n]+', rf'\g<1>{limiter_val}', content, flags=re.IGNORECASE)
        else:
            content = re.sub(r'(\}\s*\{Graphics)', rf'\tFrameLimiter {limiter_val}\n\1', content, count=1)

    # 3. Frame Generation
    elif setting_key in ['frame_generation', 'FrameGeneration']:
        k = 'FrameGeneration' if mode == '2D' else 'FrameGenerationVR'
        clean_val = 'DLSSG' if 'DLSSG' in str(new_value).upper() else ('FSR3' if 'FSR3' in str(new_value).upper() else 'NONE')
        content = re.sub(rf'({k}\s+)[^\r\n]+', rf'\g<1>{clean_val}', content, flags=re.IGNORECASE)

    # 3b. Framerate Multiplier
    elif setting_key in ['framerate_multiplier', 'NBFramesToGenerate']:
        k = 'NBFramesToGenerate' if mode == '2D' else 'NBFramesToGenerateVR'
        clean_val = '0' if any(x in str(new_value).upper() for x in ['OFF', 'INACTIVE', '0']) else '1'
        content = re.sub(rf'({k}\s+)[^\r\n]+', rf'\g<1>{clean_val}', content, flags=re.IGNORECASE)

    # 4. V-Sync (Shared)
    elif str(setting_key).lower() in ['vsync']:
        clean_val = '1' if str(new_value).strip().upper() in ['1', 'ON', 'TRUE'] else '0'
        if re.search(r'(VSync\s+)[^\r\n]+', content, flags=re.IGNORECASE):
            content = re.sub(r'(VSync\s+)[^\r\n]+', rf'\g<1>{clean_val}', content, flags=re.IGNORECASE)
        else:
            v_start = content.find('{Video')
            if v_start != -1:
                v_end = content.find('}', v_start)
                if v_end != -1:
                    content = content[:v_end] + f"\tVSync {clean_val}\n" + content[v_end:]

    # 4b. V-Sync Interval (Shared)
    elif str(setting_key).lower() in ['vsync_interval', 'vsyncinterval']:
        v_str = str(new_value).upper()
        if '100' in v_str or '1/1' in v_str or v_str == '1':
            interval_val = '1'
        elif '50' in v_str or '1/2' in v_str or 'HALF' in v_str or v_str == '2':
            interval_val = '2'
        elif '33' in v_str or '1/3' in v_str or v_str == '3':
            interval_val = '3'
        elif '25' in v_str or '1/4' in v_str or v_str == '4':
            interval_val = '4'
        else:
            interval_val = '2'

        try:
            disp_info = detect_display_info()
            screen_hz = int(disp_info.get("refresh_rate_int", 60))
        except Exception:
            screen_hz = 60
        target_fps = max(15, screen_hz // int(interval_val))

        if re.search(r'(VSyncInterval\s+)[^\r\n]+', content, flags=re.IGNORECASE):
            content = re.sub(r'(VSyncInterval\s+)[^\r\n]+', rf'\g<1>{interval_val}', content, flags=re.IGNORECASE)
        else:
            v_start = content.find('{Video')
            if v_start != -1:
                v_end = content.find('}', v_start)
                if v_end != -1:
                    content = content[:v_end] + f"\tVSyncInterval {interval_val}\n" + content[v_end:]

        # When V-Sync is ON, synchronize TargetFrameRate & FrameLimiter
        m_vsync = re.search(r'VSync\s+(\d+)', content, re.IGNORECASE)
        if m_vsync and m_vsync.group(1) == '1':
            if re.search(r'(TargetFrameRate\s+)[^\r\n]+', content, flags=re.IGNORECASE):
                content = re.sub(r'(TargetFrameRate\s+)[^\r\n]+', rf'\g<1>{target_fps}', content, flags=re.IGNORECASE)
            if re.search(r'(FrameLimiter\s+)[^\r\n]+', content, flags=re.IGNORECASE):
                content = re.sub(r'(FrameLimiter\s+)[^\r\n]+', rf'\g<1>{target_fps}', content, flags=re.IGNORECASE)

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

    # 7. Anti-Aliasing & Upscaling (TAA / DLAA / DLSS)
    elif setting_key in ['anti_aliasing', 'AntiAliasing']:
        k_aa = 'AntiAliasing' if mode == '2D' else 'AntiAliasingVR'
        k_dlss = 'DLSSMode' if mode == '2D' else 'DLSSModeVR'
        val_upper = str(new_value).upper()
        if 'DLSS' in val_upper:
            aa_mode = 'DLSS'
            if 'PERFORMANCE' in val_upper:
                dlss_mode = 'PERFORMANCE'
            elif 'BALANCED' in val_upper:
                dlss_mode = 'BALANCED'
            else:
                dlss_mode = 'QUALITY'
            content = re.sub(rf'({k_aa}\s+)[^\r\n]+', rf'\g<1>{aa_mode}', content, flags=re.IGNORECASE)
            if re.search(rf'({k_dlss}\s+)[^\r\n]+', content, flags=re.IGNORECASE):
                content = re.sub(rf'({k_dlss}\s+)[^\r\n]+', rf'\g<1>{dlss_mode}', content, flags=re.IGNORECASE)
            else:
                v_start = content.find('{Video')
                if v_start != -1:
                    v_end = content.find('}', v_start)
                    if v_end != -1:
                        content = content[:v_end] + f"\t{k_dlss} {dlss_mode}\n" + content[v_end:]
        elif 'DLAA' in val_upper:
            content = re.sub(rf'({k_aa}\s+)[^\r\n]+', r'\g<1>DLAA', content, flags=re.IGNORECASE)
        else: # TAA (Native)
            content = re.sub(rf'({k_aa}\s+)[^\r\n]+', r'\g<1>TAA', content, flags=re.IGNORECASE)

    # 7b. VR Foveated Rendering & Scale (VR only in {Video})
    elif setting_key in ['foveated_rendering', 'FoveatedRendering']:
        clean_val = '1' if str(new_value).upper() in ['1', 'ON', 'TRUE'] else '0'
        content = re.sub(r'(FoveatedRendering\s+)[^\r\n]+', rf'\g<1>{clean_val}', content, flags=re.IGNORECASE)

    elif setting_key in ['foveated_scale', 'FoveatedRenderingScale']:
        clean_str = str(new_value).replace('%', '').strip()
        try:
            num = float(clean_str)
            if num > 1.0: num = num / 100.0
            val_f = f"{num:.6f}"
        except Exception:
            val_f = "0.400000"
        content = re.sub(r'(FoveatedRenderingScale\s+)[^\r\n]+', rf'\g<1>{val_f}', content, flags=re.IGNORECASE)

    # 7c. VR Primary Scaling & Sharpen Amount in {Video}
    elif setting_key in ['primary_scaling_vr', 'PrimaryScalingVR']:
        clean_str = str(new_value).replace('%', '').strip()
        try:
            num = float(clean_str)
            if num > 2.0: num = num / 100.0
            val_f = f"{num:.6f}"
        except Exception:
            val_f = "1.000000"
        content = re.sub(r'(PrimaryScalingVR\s+)[^\r\n]+', rf'\g<1>{val_f}', content, flags=re.IGNORECASE)

    elif setting_key in ['sharpen_amount_vr', 'SharpenAmountVR']:
        try:
            num = float(str(new_value).strip())
            val_f = f"{num:.6f}"
        except Exception:
            val_f = "0.200000"
        content = re.sub(r'(SharpenAmountVR\s+)[^\r\n]+', rf'\g<1>{val_f}', content, flags=re.IGNORECASE)

    # 7d. VR Reprojection Mode in {Video}
    elif setting_key in ['reprojection_mode', 'ReprojectionMode']:
        clean_val = reproj_map_rev.get(str(new_value).lower().strip(), '0')
        content = re.sub(r'(ReprojectionMode\s+)[^\r\n]+', rf'\g<1>{clean_val}', content, flags=re.IGNORECASE)

    # 7e. Raytraced Shadows
    elif setting_key in ['raytraced_shadows', 'RaytracedShadows']:
        clean_val = '1' if str(new_value).upper() in ['1', 'ON', 'TRUE'] else '0'
        content = update_sub_block_setting(content, mode, '{RaytracedShadows', r'(Enabled\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"Enabled {clean_val}")

    # 8. TLOD (Supports up to 400 manual input)
    elif setting_key in ['tlod', 'TerrainLoD', 'LoDFactor']:
        clean_str = str(new_value).replace('Dynamic', '').replace('(', '').replace(')', '').replace('LOD', '').strip()
        num_val = max(10, min(400, float(clean_str)))
        val_f = f"{num_val / 100.0:.6f}"
        content = update_sub_block_setting(content, mode, '{Terrain', r'(LoDFactor\s+)[^\r\n]+', rf'\g<1>{val_f}', f"LoDFactor {val_f}")

    # 9. OLOD (Supports up to 400 manual input)
    elif setting_key in ['olod', 'ObjectsLoD']:
        clean_str = str(new_value).replace('Dynamic', '').replace('(', '').replace(')', '').replace('LOD', '').strip()
        num_val = max(10, min(400, float(clean_str)))
        val_f = f"{num_val / 100.0:.6f}"
        content = update_sub_block_setting(content, mode, '{ObjectsLoD', r'(LoDFactor\s+)[^\r\n]+', rf'\g<1>{val_f}', f"LoDFactor {val_f}")

    # 10. Offscreen Terrain Pre-Caching
    elif setting_key in ['offscreen_precaching', 'OffscreenTerrainPreCaching']:
        v_clean = str(new_value).lower()
        if 'ultra' in v_clean or v_clean.strip() == '3':
            clean_q = '3'
        elif 'high' in v_clean or v_clean.strip() == '2':
            clean_q = '2'
        elif 'medium' in v_clean or 'med' in v_clean or v_clean.strip() == '1':
            clean_q = '1'
        elif 'low' in v_clean or v_clean.strip() == '0':
            clean_q = '0'
        else:
            clean_q = q_map_rev.get(v_clean.strip(), '2')
        content = update_sub_block_setting(content, mode, '{OffscreenTerrainPreCaching', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}', f"Quality {clean_q}")

    # 11. Texture Resolution (MSFS uses inverted mipmap drop level: 0=Ultra, 1=High, 2=Medium, 3=Low)
    elif setting_key in ['texture_resolution', 'Texture']:
        v_clean = str(new_value).lower().strip()
        if 'ultra' in v_clean or v_clean == '0':
            clean_q = '0'
        elif 'high' in v_clean or v_clean == '1':
            clean_q = '1'
        elif 'medium' in v_clean or 'med' in v_clean or v_clean == '2':
            clean_q = '2'
        elif 'low' in v_clean or v_clean == '3':
            clean_q = '3'
        else:
            clean_q = '2'
        content = update_sub_block_setting(content, mode, '{Texture', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}', f"Quality {clean_q}")

    # 12. Volumetric Clouds
    elif setting_key in ['volumetric_clouds', 'VolumetricClouds']:
        clean_q = q_map_rev.get(str(new_value).split("(")[0].strip().lower(), '2')
        content = update_sub_block_setting(content, mode, '{VolumetricClouds', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}', f"Quality {clean_q}")

    # 13. Buildings Quality
    elif setting_key in ['buildings', 'Buildings']:
        clean_q = q_map_rev.get(str(new_value).split("(")[0].strip().lower(), '2')
        content = update_sub_block_setting(content, mode, '{Buildings', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}', f"Quality {clean_q}")

    # 14. Trees Quality
    elif setting_key in ['trees', 'TreesQuality']:
        clean_q = q_map_rev.get(str(new_value).split("(")[0].strip().lower(), '2')
        content = update_sub_block_setting(content, mode, '{Procedural', r'(TreesQuality\s+)[^\r\n]+', rf'\g<1>{clean_q}', f"TreesQuality {clean_q}")

    # 15. Grass Quality
    elif setting_key in ['grass', 'GrassQuality']:
        clean_q = q_map_rev.get(str(new_value).split("(")[0].strip().lower(), '2')
        content = update_sub_block_setting(content, mode, '{Procedural', r'(GrassQuality\s+)[^\r\n]+', rf'\g<1>{clean_q}', f"GrassQuality {clean_q}")

    # 16. Water Waves Simulation
    elif setting_key in ['water_waves', 'Water']:
        v_low = str(new_value).lower().strip()
        clean_val = fft_map_rev.get(v_low, fft_map_rev.get(v_low.split("(")[0].strip(), '512'))
        content = update_sub_block_setting(content, mode, '{Water', r'(FFTSize\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"FFTSize {clean_val}")

    # 17. Displacement Mapping
    elif setting_key in ['displacement_mapping', 'DisplacementMapping']:
        v_up = str(new_value).upper()
        clean_val = '1' if (('ON' in v_up and 'OFF' not in v_up) or str(new_value).strip() in ['1', 'TRUE']) else '0'
        content = update_sub_block_setting(content, mode, '{DisplacementMapping', r'(Enabled\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"Enabled {clean_val}")

    # 18. Glass Cockpits Refresh Rate
    elif setting_key in ['glass_cockpits', 'GlassCockpitsRefreshRate']:
        v_low = str(new_value).lower().strip()
        clean_val = glass_map_rev.get(v_low, glass_map_rev.get(v_low.split("(")[0].strip(), '1'))
        content = update_sub_block_setting(content, mode, '{GlassCockpitsRefreshRate', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"Quality {clean_val}")

    # 19. Shadow Maps Resolution
    elif setting_key in ['shadow_maps', 'Shadows']:
        v_low = str(new_value).lower().strip()
        clean_val = shadow_map_rev.get(v_low, shadow_map_rev.get(v_low.split("(")[0].strip(), '1536'))
        content = update_sub_block_setting(content, mode, '{Shadows', r'(Size\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"Size {clean_val}")

    # 20. Terrain Shadows
    elif setting_key in ['terrain_shadows', 'HeightFieldShadows']:
        v_low = str(new_value).lower().strip()
        clean_val = hf_map_rev.get(v_low, hf_map_rev.get(v_low.split("(")[0].strip(), '512'))
        content = update_sub_block_setting(content, mode, '{HeightFieldShadows', r'(Size\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"Size {clean_val}")

    # 21. Contact Shadows
    elif setting_key in ['contact_shadows', 'ContactShadows']:
        clean_q = q_map_rev.get(str(new_value).split("(")[0].strip().lower(), '2')
        content = update_sub_block_setting(content, mode, '{ContactShadows', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}', f"Quality {clean_q}")

    # 22. Ambient Occlusion (SSAO)
    elif setting_key in ['ambient_occlusion', 'SSAO']:
        clean_q = q_map_rev.get(str(new_value).split("(")[0].strip().lower(), '2')
        content = update_sub_block_setting(content, mode, '{SSAO', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}', f"Quality {clean_q}")

    # 23. Screen Space Reflections (SSR)
    elif setting_key in ['reflections_ssr', 'SSR']:
        clean_q = q_map_rev.get(str(new_value).split("(")[0].strip().lower(), '2')
        content = update_sub_block_setting(content, mode, '{SSR', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}', f"Quality {clean_q}")

    # 24. Volumetric Lights
    elif setting_key in ['volumetric_lights', 'VolumetricLights']:
        clean_q = q_map_rev.get(str(new_value).split("(")[0].strip().lower(), '2')
        content = update_sub_block_setting(content, mode, '{VolumetricLights', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}', f"Quality {clean_q}")

    # 25. Anisotropic Filtering
    elif setting_key in ['anisotropic_filtering', 'MaxAnisotropy']:
        clean_val = str(new_value).upper().split("(")[0].replace('X', '').replace('OFF', '0').strip()
        content = update_sub_block_setting(content, mode, '{Texture', r'(MaxAnisotropy\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"MaxAnisotropy {clean_val}")

    # 26. Windshield Effects
    elif setting_key in ['windshield_effects', 'WindShield']:
        clean_q = q_map_rev.get(str(new_value).split("(")[0].strip().lower(), '2')
        content = update_sub_block_setting(content, mode, '{WindShield', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}', f"Quality {clean_q}")

    # 27. Cubemap Reflections (ReflectionProbe)
    elif setting_key in ['cubemap_reflections', 'ReflectionProbe']:
        clean_val = str(new_value).split("(")[0].replace('X', '').strip()
        content = update_sub_block_setting(content, mode, '{ReflectionProbe', r'(Size\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"Size {clean_val}")

    # 28. Depth Of Field (DOF)
    elif setting_key in ['dof', 'DOF']:
        val_str = str(new_value).split("(")[0].strip().lower()
        if val_str in ['off', '0', 'false']:
            content = update_sub_block_setting(content, mode, '{DOF', r'(Enabled\s+)[^\r\n]+', r'\g<1>0', "Enabled 0")
            content = update_sub_block_setting(content, mode, '{DOF', r'(Quality\s+)[^\r\n]+', r'\g<1>0', "Quality 0")
        else:
            q_val = q_map_rev.get(val_str, '1')
            content = update_sub_block_setting(content, mode, '{DOF', r'(Enabled\s+)[^\r\n]+', r'\g<1>1', "Enabled 1")
            content = update_sub_block_setting(content, mode, '{DOF', r'(Quality\s+)[^\r\n]+', rf'\g<1>{q_val}', f"Quality {q_val}")

    # 29. Motion Blur
    elif setting_key in ['motion_blur', 'MotionBlur']:
        val_str = str(new_value).split("(")[0].strip().lower()
        if val_str in ['off', '0', 'false']:
            content = update_sub_block_setting(content, mode, '{MotionBlur', r'(Enabled\s+)[^\r\n]+', r'\g<1>0', "Enabled 0")
            content = update_sub_block_setting(content, mode, '{MotionBlur', r'(Quality\s+)[^\r\n]+', r'\g<1>0', "Quality 0")
        else:
            q_val = q_map_rev.get(val_str, '1')
            content = update_sub_block_setting(content, mode, '{MotionBlur', r'(Enabled\s+)[^\r\n]+', r'\g<1>1', "Enabled 1")
            content = update_sub_block_setting(content, mode, '{MotionBlur', r'(Quality\s+)[^\r\n]+', rf'\g<1>{q_val}', f"Quality {q_val}")

    # 30. Visual Effects Particles
    elif setting_key in ['particles', 'Particles']:
        clean_q = q_map_rev.get(str(new_value).split("(")[0].strip().lower(), '0')
        content = update_sub_block_setting(content, mode, '{Particles', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}', f"Quality {clean_q}")

    # 31. Aircraft Traffic Quantity
    elif setting_key in ['aircraft_traffic_quantity', 'AircraftTrafficQuantity']:
        clean_val = traffic_qty_map_rev.get(str(new_value).split("(")[0].strip().lower(), '-1')
        content = update_sub_block_setting(content, mode, '{Traffic', r'(AircraftTrafficQuantity\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"AircraftTrafficQuantity {clean_val}")

    # 32. Aircraft Traffic Variety
    elif setting_key in ['aircraft_traffic_variety', 'AircraftTrafficVariety']:
        clean_val = traffic_var_map_rev.get(str(new_value).split("(")[0].strip().lower(), '3')
        content = update_sub_block_setting(content, mode, '{Traffic', r'(AircraftTrafficVariety\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"AircraftTrafficVariety {clean_val}")

    # 33. Parked Aircraft Quantity
    elif setting_key in ['parked_aircraft_quantity', 'ParkedAircraftQuantity']:
        clean_val = traffic_qty_map_rev.get(str(new_value).split("(")[0].strip().lower(), '-1')
        content = update_sub_block_setting(content, mode, '{Traffic', r'(ParkedAircraftQuantity\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"ParkedAircraftQuantity {clean_val}")

    # 34. Parked Aircraft Variety
    elif setting_key in ['parked_aircraft_variety', 'ParkedAircraftVariety']:
        clean_val = traffic_var_map_rev.get(str(new_value).split("(")[0].strip().lower(), '3')
        content = update_sub_block_setting(content, mode, '{Traffic', r'(ParkedAircraftVariety\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"ParkedAircraftVariety {clean_val}")

    # 35. Airport Services Quantity
    elif setting_key in ['airport_services_quantity', 'AirportsServicesQuantity']:
        clean_val = traffic_qty_map_rev.get(str(new_value).split("(")[0].strip().lower(), '-1')
        content = update_sub_block_setting(content, mode, '{Traffic', r'(AirportsServicesQuantity\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"AirportsServicesQuantity {clean_val}")

    # 36. Airport Services Variety
    elif setting_key in ['airport_services_variety', 'AirportsServicesVariety']:
        clean_val = traffic_var_map_rev.get(str(new_value).split("(")[0].strip().lower(), '1')
        content = update_sub_block_setting(content, mode, '{Traffic', r'(AirportsServicesVariety\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"AirportsServicesVariety {clean_val}")

    # 37. Road Traffic
    elif setting_key in ['road_traffic', 'RoadQuality']:
        clean_val = traffic_qty_map_rev.get(str(new_value).split("(")[0].strip().lower(), '1')
        content = update_sub_block_setting(content, mode, '{Traffic', r'(RoadQuality\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"RoadQuality {clean_val}")

    # 38. Sea Traffic
    elif setting_key in ['sea_traffic', 'SeaQuality']:
        clean_val = traffic_qty_map_rev.get(str(new_value).split("(")[0].strip().lower(), '3')
        content = update_sub_block_setting(content, mode, '{Traffic', r'(SeaQuality\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"SeaQuality {clean_val}")

    # 39. Characters Quantity
    elif setting_key in ['characters_quantity']:
        clean_val = traffic_qty_map_rev.get(str(new_value).split("(")[0].strip().lower(), '1')
        content = update_sub_block_setting(content, mode, '{Characters', r'(Quantity\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"Quantity {clean_val}")

    # 40. Characters Variety
    elif setting_key in ['characters_variety']:
        clean_val = traffic_var_map_rev.get(str(new_value).split("(")[0].strip().lower(), '1')
        content = update_sub_block_setting(content, mode, '{Characters', r'(Variety\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"Variety {clean_val}")

    # 41. Characters Quality
    elif setting_key in ['characters_quality']:
        clean_val = traffic_var_map_rev.get(str(new_value).split("(")[0].strip().lower(), '1')
        content = update_sub_block_setting(content, mode, '{Characters', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"Quality {clean_val}")

    # 42. Fauna Density
    elif setting_key in ['fauna_density']:
        clean_val = traffic_qty_map_rev.get(str(new_value).split("(")[0].strip().lower(), '-1')
        content = update_sub_block_setting(content, mode, '{Fauna', r'(Quantity\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"Quantity {clean_val}")

    # 43. Seatbelt Visibility
    elif setting_key in ['seatbelt_visibility', 'Seatbelts']:
        v_up = str(new_value).upper()
        clean_val = '1' if ('ON' in v_up and 'OFF' not in v_up) or str(new_value).strip() in ['1', 'TRUE'] else '0'
        content = update_sub_block_setting(content, mode, '{Seatbelts', r'(Enabled\s+)[^\r\n]+', rf'\g<1>{clean_val}', f"Enabled {clean_val}")

    return content

    return content



# ==============================================================================
# BASE DE CONNAISSANCES TECHNIQUE DES PARAMÈTRES MSFS (INFO MODAL & NOTATIONS)
# ==============================================================================

SETTING_INFO_DATABASE = {
    "resolution": {
        "title": "Full Screen Resolution",
        "desc": "MSFS internal frame buffer rendering resolution. Sets the raw pixel grid computed by the graphics pipeline before presentation. In 2D, this matches display resolution; in VR, it governs the desktop mirror.",
        "cpu_impact": "Negligible MainThread impact. Workload falls almost exclusively on GPU rasterization and pixel shading units.",
        "gpu_impact": "Extremely heavy impact on raster fill-rate, VRAM footprint, and memory bus bandwidth.",
        "liner_advice": "Keep native display resolution (e.g. 2560x1440 or 3840x2160) paired with DLSS Quality to maximize EFIS display sharpness without choking the GPU.",
        "ga_advice": "Native resolution recommended to maintain maximum visual clarity on ground landmarks for VFR navigation.",
        "tradeoffs": [
            ("Native (1:1)", "Absolute 1:1 pixel sharpness on analog needles and avionics text", "Full GPU fill-rate workload in 4K UHD"),
            ("Downscaled", "Instant 25-40% boost in raw GPU framerate", "Severe scaling blur and soft fonts across cockpit panels")
        ]
    },
    "anti_aliasing": {
        "title": "Anti-Aliasing & Upscaling",
        "desc": "Edge anti-aliasing method and AI temporal reconstruction. DLSS leverages NVIDIA Tensor Cores to reconstruct a crisp high-resolution image from an optimized internal buffer. TAA performs native temporal supersampling.",
        "cpu_impact": "DLSS frees CPU time by lowering overall rasterization draw call overhead handled by the graphics driver.",
        "gpu_impact": "DLSS Quality reduces raw GPU shading load by 25-35% while stabilizing fine geometry lines against aliasing crawl.",
        "liner_advice": "DLSS (Quality) is strongly recommended on RTX GPUs to guarantee a healthy GPU frame time margin during heavy rain/cloud approaches.",
        "ga_advice": "DLSS (Quality) or DLAA. DLAA delivers maximum image sharpness when sufficient GPU headroom exists.",
        "tradeoffs": [
            ("DLSS (Quality)", "20-30% GPU performance headroom with pristine temporal anti-aliasing", "Mild temporal ghosting possible on fast rolling digit tapes"),
            ("TAA", "Pure native raster rendering without neural interpolation", "Full GPU workload; fine wire and fence shimmering"),
            ("DLAA", "Supreme AI anti-aliasing at native 1:1 resolution", "Zero framerate gain; same GPU workload as native TAA")
        ]
    },
    "max_frame_rate": {
        "title": "Max Frame Rate (Cadence Lock)",
        "desc": "Internal MSFS framerate limiter (written to UserCfg.opt). Synchronizes engine frame delivery intervals with an integer divisor of your display or VR headset refresh rate.",
        "cpu_impact": "Crucial for CPU MainThread pacing. Prevents the engine from running unconstrained in simple scenes, establishing a perfectly uniform frame time and eliminating micro-stutters.",
        "gpu_impact": "Substantially lowers GPU power consumption, thermal load, and stabilizes render queue latency.",
        "liner_advice": "Lock strictly to an exact 1/2 divisor of your monitor (e.g. 90 FPS for 180 Hz, 82 FPS for 165 Hz, 60 FPS for 120 Hz) for silky-smooth, judder-free flight.",
        "ga_advice": "Use the same 1/2 sync divisor principle, or OFF if running dedicated G-Sync/FreeSync hardware synchronization.",
        "tradeoffs": [
            ("1/2 Divisor (e.g. 82 / 90 FPS)", "Flawless frame pacing, zero camera judder, stabilized CPU MainThread", "Strict framerate ceiling"),
            ("OFF (Unlocked)", "Uncapped peak framerate in clear skies", "Frame time variance causing noticeable micro-stutters near dense airports")
        ]
    },
    "vsync": {
        "title": "Vertical Synchronization (V-Sync)",
        "desc": "Synchronizes front and back buffer swaps with the physical refresh intervals of your display panel. Eliminates horizontal tearing lines across the screen.",
        "cpu_impact": "Zero impact on CPU flight physics or avionics compute.",
        "gpu_impact": "Regulates frame swap timing without additional shading computational overhead.",
        "liner_advice": "Always enable (ON) alongside G-Sync/FreeSync and the Frame Limiter for clean runway centerline and taxiway presentation.",
        "ga_advice": "Enable (ON) to eliminate tear lines during steep turns and low-altitude canyon flights.",
        "tradeoffs": [
            ("ON", "Completely eliminates horizontal screen tearing", "Buffer swaps locked to monitor refresh cadence"),
            ("OFF", "Immediate frame presentation without waiting for v-blank interval", "Distracting tear lines across cockpit dials during rapid camera pans")
        ]
    },
    "vsync_interval": {
        "title": "V-Sync Interval",
        "desc": "Defines the Direct3D 12 swap chain presentation cadence relative to your monitor's physical refresh rate. When V-Sync is ON, setting 50% (1/2 rate) presents 1 frame every 2 monitor refresh blanks, locking frame delivery to an exact harmonic divisor of the display.",
        "cpu_impact": "Zero computational load; significantly stabilizes CPU MainThread pacing by eliminating frame delivery erratic bursts.",
        "gpu_impact": "Regulates DirectX 12 flip queue presentation frequency. Prevents GPU overheating and unneeded power draw.",
        "liner_advice": "50% (Half Refresh Rate) is the golden standard. On a 165Hz monitor, locking to 82 FPS (or 60 FPS on 120Hz) guarantees perfectly fluid runway tracking without stressing the D3D12 pipeline.",
        "ga_advice": "50% on 120Hz/144Hz/165Hz+ monitors; 100% on 60Hz monitors if hardware permits.",
        "tradeoffs": [
            ("50% (Half Rate)", "Flawless frame pacing, zero camera judder, stabilized GPU thermals", "Framerate capped at half monitor refresh rate"),
            ("100% (Full Rate)", "Max native framerate matching monitor refresh rate", "High GPU workload, increased frame variance near complex airports"),
            ("33% (1/3 Rate)", "Ultra-stable cadence for extreme 4K loads or heavy airliner hubs", "Lower motion fluidity (e.g. 55 FPS on 165Hz, 48 FPS on 144Hz)")
        ]
    },
    "frame_generation": {
        "title": "Frame Generation",
        "desc": "AI optical flow frame interpolation (DLSS 3 Frame Generation on RTX 40/50 series or AMD FSR 3). Generates and inserts an AI-computed frame between each native frame using the Optical Flow Accelerator.",
        "cpu_impact": "Doubles perceived motion smoothness without requiring a single additional compute cycle from the CPU MainThread. The definitive countermeasure against airliner CPU bottlenecks.",
        "gpu_impact": "Allocates approximately 1 GB additional VRAM and requires NVIDIA Reflex active to ensure low input lag.",
        "liner_advice": "Keep strictly ON in 2D mode (DLSSG 2X). Delivers 90 FPS fluidity in demanding scenarios where the CPU MainThread only produces 45 native FPS.",
        "ga_advice": "Keep ON in 2D mode for cinematic motion smoothness.",
        "tradeoffs": [
            ("DLSSG (2X)", "Doubled visual smoothness, 100% relief for CPU MainThread", "Adds ~10ms latency mitigated by Reflex. STRICTLY PROHIBITED in VR"),
            ("OFF", "Absolute lowest control input latency", "Visual smoothness strictly bound to native CPU MainThread performance")
        ]
    },
    "framerate_multiplier": {
        "title": "Framerate Multiplier",
        "desc": "Multiplier coefficient coupled to the MSFS frame interpolation subsystem.",
        "cpu_impact": "Neutral.",
        "gpu_impact": "Handled by the Optical Flow Accelerator.",
        "liner_advice": "Keep at 1 (standard 2X interpolation) whenever Frame Generation is enabled.",
        "ga_advice": "Keep at 1.",
        "tradeoffs": [
            ("1 (2X Interpolation)", "Symmetrical 1:1 cadence between native and interpolated frames", "Fixed 2X ratio")
        ]
    },
    "reflex": {
        "title": "NVIDIA Reflex Low Latency",
        "desc": "Dynamic GPU render queue synchronization technology engineered by NVIDIA. Eliminates backlogged render frames between the CPU and GPU.",
        "cpu_impact": "Optimizes CPU render command dispatch timing.",
        "gpu_impact": "Maintains optimal GPU clock frequencies to prevent render latency spikes.",
        "liner_advice": "Set to ON or ON+BOOST. Dramatically minimizes control lag between sidestick/yoke input and aircraft visual response during landing flare.",
        "ga_advice": "Set to ON for crisp flight control feedback.",
        "tradeoffs": [
            ("ON / ON+BOOST", "Lowest control latency, responsive and precise hand-flying", "GPU held at elevated clock speeds"),
            ("OFF", "Standard driver power saving", "Noticeable control sluggishness during gusty crosswind landings")
        ]
    },
    "dynamic_settings": {
        "title": "Dynamic Settings (Dynamic Resolution Scaling)",
        "desc": "Internal MSFS mechanism that dynamically downscales 3D render resolution whenever GPU frame time exceeds target thresholds.",
        "cpu_impact": "Neutral.",
        "gpu_impact": "Prevents severe framerate drops on entry-level hardware.",
        "liner_advice": "Keep strictly OFF. Dynamic downscaling unpredictably blurs primary PFD/ND flight instruments on short final approach.",
        "ga_advice": "Keep OFF to guarantee razor-sharp cockpit readouts at all times.",
        "tradeoffs": [
            ("OFF", "Rock-solid cockpit readout sharpness and consistent visual fidelity", "No automatic downscaling relief if GPU reaches 100% load"),
            ("ON", "Throttles GPU load during unexpected scene spikes", "Jarring intermittent cockpit blur during critical flight phases")
        ]
    },
    "tlod": {
        "title": "Terrain Level of Detail (TLOD)",
        "desc": "Geometric density and distance scaling for the digital elevation terrain mesh and photogrammetry. THIS IS THE SINGLE MOST DEMANDING CPU MAINTHREAD SETTING IN THE SIMULATOR.",
        "cpu_impact": "Critical impact. Every 50-point increase in TLOD adds 3 to 6 ms to CPU MainThread frame time and dramatically multiplies DirectX draw calls.",
        "gpu_impact": "Moderate impact on VRAM allocation and vertex geometry shading.",
        "liner_advice": "Maintain between 100 and 120 on complex airliners (or delegate to AutoFPS). Exceeding 140 at dense international airports triggers MainThread saturation and landing stutters.",
        "ga_advice": "150 to 200 in General Aviation to enjoy rich mountain ridges and scenic valleys.",
        "tradeoffs": [
            ("100 - 120", "Protects CPU MainThread budget, guarantees stutter-free flare and touchdown", "Distant mountains slightly less detailed"),
            ("200 - 400", "Photographic distant ridges and urban skylines", "Severe CPU MainThread bottleneck, inevitable landing stutters at hubs")
        ]
    },
    "olod": {
        "title": "Objects Level of Detail (OLOD)",
        "desc": "Draw distance and geometric complexity for 3D scenery models: airport terminals, jetways, airfield lighting fixtures, ground service equipment, and autogen buildings.",
        "cpu_impact": "Direct driver of CPU draw calls around complex airfield perimeters.",
        "gpu_impact": "Increases vertex count and texture streaming load.",
        "liner_advice": "Set to 100. Modern payware hubs already feature tens of thousands of modeled objects; OLOD 100 prevents CPU draw-call overload.",
        "ga_advice": "100 to 150 to admire hangars and facilities at regional airfields.",
        "tradeoffs": [
            ("100", "Controlled draw call budget, maximum ground smoothness and stability", "Distant airport vehicles not rendered until closer"),
            ("150 - 400", "Terminals and hangars visible from extreme distances", "Noticeable framerate penalty on major international hub ramps")
        ]
    },
    "offscreen_precaching": {
        "title": "Off Screen Pre-Caching",
        "desc": "Allocates memory buffers to retain terrain mesh, building geometry, and textures situated outside the immediate camera field of view.",
        "cpu_impact": "Eliminates sudden CPU thread spikes and draw call bursts when rotating the camera quickly.",
        "gpu_impact": "Allocates extra system RAM and approximately 500 MB to 1 GB of additional VRAM.",
        "liner_advice": "Must be set to HIGH or ULTRA. Completely eliminates panning stutters and camera hesitation when scanning between the overhead panel and lateral windows.",
        "ga_advice": "HIGH or ULTRA for fluid visual scans during circuit flying.",
        "tradeoffs": [
            ("HIGH / ULTRA", "Zero hitching during quick view switches and head-tracking panning", "Consumes ~1 GB additional video memory"),
            ("LOW / MEDIUM", "Minor memory savings", "Frequent micro-freezes whenever view angle changes")
        ]
    },
    "displacement_mapping": {
        "title": "Displacement Mapping",
        "desc": "Surface tessellation technique that synthesizes micro-relief height displacement on runway concrete joints, pavement cracks, and terrain.",
        "cpu_impact": "Low to moderate.",
        "gpu_impact": "Consumes GPU geometry shader tessellation stages and VRAM bandwidth.",
        "liner_advice": "Keep OFF. From the cockpit height of an airliner, pavement micro-relief is completely invisible and wastes memory bandwidth.",
        "ga_advice": "OFF or ON. Barely visible once wheels leave the ground.",
        "tradeoffs": [
            ("OFF", "Saves VRAM bandwidth and geometry compute passes", "Concrete expansion joints appear flat at wheel level"),
            ("ON", "Fine pavement surface depth visible only at ground level", "Unnecessary geometry workload throughout all flight phases")
        ]
    },
    "buildings": {
        "title": "Buildings Quality",
        "desc": "Mesh polygon budget, roof geometry, and facade texture atlases for procedural autogen structures generated by Blackshark AI (does not affect handcrafted airport terminals).",
        "cpu_impact": "Low on modern CPUs; moderate draw call volume in dense metropolitan areas (London, New York, Tokyo).",
        "gpu_impact": "High/Ultra increases geometry tessellation and texture streaming. In VR stereo rendering, high polygon counts are rasterized twice per frame, impacting frametime budgets.",
        "liner_advice": "2D: HIGH or MEDIUM (balanced urban facades with safe VRAM margin). VR: MEDIUM or LOW to preserve stereo reprojection headroom and avoid VRAM spikes during airport approaches.",
        "ga_advice": "HIGH or ULTRA for realistic cityscapes and suburban landmarks during low-altitude VFR navigation.",
        "tradeoffs": [
            ("LOW / MEDIUM (Recommended VR)", "Lightweight autogen geometry, minimal stereo draw calls, and low VRAM footprint to guarantee reprojection fluidity", "Simplified building roof shapes and lower-resolution facade textures"),
            ("HIGH", "Crisp architectural facades, detailed rooftops, and window reflections with balanced performance", "Moderate VRAM and geometry rasterization workload"),
            ("ULTRA", "Maximum rooftop geometry and high-resolution facade texture atlases", "Higher VRAM allocation and stereo draw call overhead; potential reprojection drops in VR")
        ]
    },
    "trees": {
        "title": "Trees Quality",
        "desc": "Procedural 3D foliage density, canopy branch modeling, and self-shadowing across forests and suburban woodlots.",
        "cpu_impact": "Low; instanced foliage rendering.",
        "gpu_impact": "Significant alpha-tested fill-rate and geometry load over dense continuous forests, especially in VR stereo rendering.",
        "liner_advice": "2D: HIGH for lush approach corridors. VR: MEDIUM or LOW to save double-eye foliage rasterization and sustain locked reprojection.",
        "ga_advice": "HIGH or ULTRA for bush flying immersion.",
        "tradeoffs": [
            ("LOW / MEDIUM (Recommended VR)", "Reduces double-eye foliage rasterization to secure locked VR frame pacing", "Slightly reduced canopy density in dense woodlands"),
            ("HIGH", "Dense 3D tree canopies with smooth LOD cross-fading", "Modest rasterization cost over massive forest regions"),
            ("ULTRA", "Maximum foliage density and realistic crown shadowing", "Heavy stereo fill-rate penalty in VR; potential frame pacing drops")
        ]
    },
    "grass": {
        "title": "Grass & Bushes",
        "desc": "Procedural 3D ground vegetation blades, wild meadow flowers, and airfield perimeter shrubs.",
        "cpu_impact": "Extremely heavy on large hub airports if set too high (generates millions of redundant grass draw calls).",
        "gpu_impact": "Substantial fill-rate cost at ground level.",
        "liner_advice": "LOW or MEDIUM. On paved asphalt/concrete runways, rendering millions of 3D grass blades invisible from the flight deck robs vital FPS on short final.",
        "ga_advice": "HIGH or ULTRA for backcountry grass strip and mountain altisurface operations.",
        "tradeoffs": [
            ("LOW / MEDIUM", "Saves millions of draw calls, preserves critical landing FPS", "Grass runway shoulders use flat turf texture rather than 3D blades"),
            ("HIGH / ULTRA", "Rich 3D vegetation field for unpaved bush airstrips", "Redundant draw call load on major international runways")
        ]
    },
    "water_waves": {
        "title": "Water Waves Simulation",
        "desc": "Fast Fourier Transform (FFT) grid resolution governing ocean wave mechanics, coastal swells, and shoreline foam.",
        "cpu_impact": "Very low.",
        "gpu_impact": "Computed via GPU compute shaders.",
        "liner_advice": "HIGH (512). Offers authentic maritime wave motion with negligible overhead.",
        "ga_advice": "HIGH (512) or ULTRA (1024) for floatplane and seaplane operations.",
        "tradeoffs": [
            ("HIGH (512)", "Dynamic swells and authentic maritime light specular highlights", "Minimal compute cost"),
            ("LOW (128)", "Flatter water surface with repetitive tiling patterns", "Negligible performance gain")
        ]
    },
    "shadow_maps": {
        "title": "Shadow Maps Resolution",
        "desc": "Depth buffer resolution allocated for direct solar shadows (cockpit canopy frames, wings, control surfaces, and ground scenery).",
        "cpu_impact": "Negligible.",
        "gpu_impact": "Allocates dedicated VRAM shadow map render targets. In VR stereo rendering, high shadow maps multiply rasterization passes.",
        "liner_advice": "2D: HIGH (1536) or ULTRA (2048) on high-end GPUs. VR: MEDIUM (1024) or HIGH (1536) to prevent stereo depth buffer rasterization spikes and save VRAM.",
        "ga_advice": "HIGH (1536) or ULTRA (2048) in 2D; MEDIUM (1024) in VR.",
        "tradeoffs": [
            ("MEDIUM (1024) / HIGH (1536)", "Crisp, stable cockpit shadows with safe VRAM and zero stereo hitching", "Very slightly softer shadow penumbra than 2048"),
            ("ULTRA (2048)", "Razor-sharp shadow lines across all surfaces", "Consumes 4x depth render target memory; severe reprojection hazard in VR"),
            ("LOW (512)", "Minimal VRAM footprint for entry hardware", "Visible stair-stepping and jittering along cockpit glare shields")
        ]
    },
    "terrain_shadows": {
        "title": "Terrain Shadows",
        "desc": "Long-range cast shadows projected by mountain massifs, peaks, and terrain ridges relative to solar elevation.",
        "cpu_impact": "Low.",
        "gpu_impact": "Heightfield raymarching calculations across digital elevation data.",
        "liner_advice": "HIGH (512). Produces stunning golden-hour arrivals in mountainous terrain (e.g. Innsbruck, Geneva, Nice).",
        "ga_advice": "HIGH (512) for scenic mountain VFR navigation.",
        "tradeoffs": [
            ("HIGH (512)", "Spectacular alpine ridges with dramatic shadow casting", "Minor GPU shading workload in mountain valleys"),
            ("LOW (128)", "Flattened terrain relief with simplified illumination", "Negligible framerate gain")
        ]
    },
    "contact_shadows": {
        "title": "Contact Shadows",
        "desc": "Screen-space micro-shadows beneath switches, toggles, rudder pedals, landing gear bogies, and cockpit instrumentation.",
        "cpu_impact": "Zero.",
        "gpu_impact": "Very lightweight screen-space shader pass (< 0.2 ms).",
        "liner_advice": "HIGH. Adds indispensable tactile depth and physical realism to overhead and pedestal panels.",
        "ga_advice": "HIGH for rich cockpit instrument depth.",
        "tradeoffs": [
            ("HIGH", "Switches and levers appear firmly seated on cockpit panels", "Practically imperceptible GPU cost"),
            ("OFF / LOW", "Cockpit knobs appear visually detached and floating", "Zero measurable performance gain")
        ]
    },
    "volumetric_lights": {
        "title": "Volumetric Lights",
        "desc": "Atmospheric light scattering through fog, haze, and rain (landing light beams, runway strobe illumination, and beacon shafts).",
        "cpu_impact": "Low.",
        "gpu_impact": "Volumetric light marching during night low-visibility CAT III ILS approaches.",
        "liner_advice": "HIGH. Delivers iconic immersion as high-intensity runway lights pierce thick overcast at night.",
        "ga_advice": "HIGH for dawn/dusk and misty morning flights.",
        "tradeoffs": [
            ("HIGH / ULTRA", "Authentic light shafts cutting through cloud bases and rain", "Minor GPU fill cost when crossing multiple light cones"),
            ("LOW", "Thin, transparent light beams lacking atmospheric presence", "Marginal framerate difference")
        ]
    },
    "texture_resolution": {
        "title": "Texture Resolution",
        "desc": "Resolution of texture mipmaps loaded into Video RAM (VRAM) for airframes, virtual cockpits, liveries, and ground scenery. THIS SETTING IS THE PRIMARY CAUSE OF D3D12 DEVICE-HUNG CRASHES AND SEVERE STUTTERS.",
        "cpu_impact": "Indirect. When VRAM overflows, DirectX 12 evicts assets to system RAM over the PCIe bus, triggering instantaneous CPU hitches and frame freezes.",
        "gpu_impact": "Directly determines VRAM allocation (6 to 8 GB difference between LOW and ULTRA!).",
        "liner_advice": "Set strictly to LOW or MEDIUM on complex airliners. Vector avionics screens (PFD, ND, FMC) retain 100% vector sharpness, while saving 6-8 GB VRAM to eliminate landing flare D3D12 stutters.",
        "ga_advice": "HIGH or ULTRA. General aviation aircraft consume modest VRAM, leaving ample video memory for max textures.",
        "tradeoffs": [
            ("LOW (Recommended for Airliners)", "Frees 6-8 GB VRAM, zero D3D12 paging freezes, 100% crisp vector cockpit displays", "Slightly softer external fuselage decals when viewed up close in drone view"),
            ("MEDIUM", "Well-balanced visual quality with safe VRAM margin on 16 GB GPUs", "Consumes ~3 GB more VRAM than LOW"),
            ("ULTRA", "Rivet-by-rivet sharpness on external paint schemes", "CRITICAL VRAM RISK: Guaranteed memory overflow at complex payware airports causing severe stutters")
        ]
    },
    "glass_cockpits": {
        "title": "Glass Cockpit Refresh Rate",
        "desc": "Update frequency of vector avionics displays in the flight deck (PFD, ND, EICAS, MCDU/FMC). MAJOR DRIVER OF CPU MAINTHREAD FRAME TIME ON COMPLEX PAYWARE AIRLINERS.",
        "cpu_impact": "Colossal. In study-level airliners (Fenix, PMDG, iniBuilds), redrawing vector gauges at full framerate exhausts CPU MainThread. Throttling to Medium or Low instantly recovers 5 to 8 ms CPU time.",
        "gpu_impact": "Low.",
        "liner_advice": "MEDIUM (Half) or LOW (Quarter). Attitude indicator and numerical tapes remain crystal clear while simulator-wide smoothness improves substantially.",
        "ga_advice": "HIGH (Full) for Garmin G1000/G3000 synthetic vision on high-end CPUs.",
        "tradeoffs": [
            ("MEDIUM (Half)", "Recovers 5-8 ms CPU MainThread budget, eliminates micro-stutters", "Artificial horizon movement animated at 30-45 Hz instead of 60+ Hz"),
            ("HIGH (Full)", "Silky 60 Hz display animations", "Heavy CPU MainThread saturation on complex airliner avionics")
        ]
    },
    "ambient_occlusion": {
        "title": "Ambient Occlusion (SSAO)",
        "desc": "Screen-space calculation of diffuse contact shadows in crevices, cockpit footwells, and beneath instrument glare shields.",
        "cpu_impact": "Zero.",
        "gpu_impact": "Moderate post-processing shading pass in 2D; significant double-pass compute overhead in VR stereo.",
        "liner_advice": "2D: HIGH. Natural volumetric depth with minor GPU cost. VR: LOW or MEDIUM to preserve per-eye fragment shading performance.",
        "ga_advice": "HIGH in 2D; MEDIUM in VR.",
        "tradeoffs": [
            ("HIGH / ULTRA", "Deep, natural contact shadows in cockpit corners and footwells", "Moderate compute shader pass; heavy stereo overhead in VR"),
            ("LOW / MEDIUM (Recommended VR)", "Natural cockpit shadow depth with low per-eye shader cost", "Slightly softer crevice shading"),
            ("OFF", "Zero shading compute", "Cockpit appears flat and unnaturally washed out")
        ]
    },
    "windshield_effects": {
        "title": "Windshield Effects",
        "desc": "Dynamic physics simulation of windshield raindrops, wiper sweep clearing, progressive structural icing, and condensation.",
        "cpu_impact": "Negligible.",
        "gpu_impact": "Refraction and distortion shader passes during heavy precipitation.",
        "liner_advice": "HIGH or ULTRA. Essential for immersion during stormy or severe icing approaches.",
        "ga_advice": "HIGH or ULTRA.",
        "tradeoffs": [
            ("HIGH / ULTRA", "Ultra-realistic rain bead aerodynamics and wiper clearing", "Minor shader workload during heavy downpours"),
            ("LOW", "Static, simplified droplet textures", "Negligible framerate gain")
        ]
    },
    "volumetric_clouds": {
        "title": "Volumetric Clouds",
        "desc": "Raymarched volumetric cloud rendering of stratus, cumulus, and towering cumulonimbus with multi-bounce internal light scattering.",
        "cpu_impact": "Low.",
        "gpu_impact": "Extremely heavy on GPU rasterization and pixel shading units when flying through dense overcast layers.",
        "liner_advice": "HIGH. HIGH provides 95% of Ultra visual fidelity while reclaiming 15-20% vital GPU performance during cloud penetration.",
        "ga_advice": "HIGH.",
        "tradeoffs": [
            ("HIGH (Optimal)", "Stunning, dense cloud formations with 15% GPU safety headroom", "Cloud margins subtly softer than Ultra"),
            ("ULTRA", "Razor-sharp cloud boundary definition", "Substantial framerate drops inside thick overcast soup"),
            ("MEDIUM / LOW", "Maximum GPU performance", "Noticeable dithering noise and blocky cloud edges")
        ]
    },
    "reflections_ssr": {
        "title": "Screen Space Reflections (SSR)",
        "desc": "Raymarching calculation of real-time mirror reflections across canopy glass, wet tarmac puddles, and reflective runway asphalt.",
        "cpu_impact": "Zero.",
        "gpu_impact": "Moderate in 2D; very heavy in stereo VR rendering.",
        "liner_advice": "HIGH in 2D mode for glistening wet runway visuals at night. In VR, reduce to LOW to preserve reprojection budget.",
        "ga_advice": "HIGH in 2D, LOW in VR.",
        "tradeoffs": [
            ("HIGH (2D)", "Gorgeous reflections on wet tarmac and canopy surfaces", "1-2 ms GPU cost during rainy conditions"),
            ("LOW (Recommended VR)", "Greatly alleviates stereo fill-rate pressure in VR headsets", "Water surfaces appear matte without dynamic reflections")
        ]
    },
    "anisotropic_filtering": {
        "title": "Anisotropic Filtering",
        "desc": "Texture sampling filter preventing oblique surface blurring on runway touchdown markings, threshold lines, and taxiway centerlines.",
        "cpu_impact": "Zero.",
        "gpu_impact": "Trivial memory bandwidth cost (< 0.1 ms on any modern GPU).",
        "liner_advice": "16X without exception. Guarantees runway centerlines and touchdown markers stay razor-sharp to the horizon.",
        "ga_advice": "16X.",
        "tradeoffs": [
            ("16X", "Centerlines and ground markings remain sharp all the way to horizon", "Practically nonexistent performance cost"),
            ("OFF / 2X / 4X", "Muddy runway markings beyond 100 meters", "Zero measurable framerate improvement")
        ]
    },
    "raytraced_shadows": {
        "title": "Raytraced Shadows",
        "desc": "Real-time ray-traced shadows computed on GPU RT cores for realistic sun shadows and contact attenuation.",
        "cpu_impact": "Dispatches ray tracing acceleration structures.",
        "gpu_impact": "Heavy GPU RT-core computation and BVH traversal time.",
        "liner_advice": "Keep OFF. Frame generation and DLSS performance take priority over micro shadow ray tracing.",
        "ga_advice": "OFF, or ON if running top-tier RTX 4080/4090 GPUs at 1440p.",
        "tradeoffs": [
            ("OFF", "Maximum GPU frame budget preserved for DLSS and high resolution", "Sun shadows use standard high-res shadow maps"),
            ("ON", "Ultra-crisp contact shadows under wings and landing gear", "Significant GPU frame time overhead; severe hazard in VR")
        ]
    },
    "primary_scaling_vr": {
        "title": "VR Render Scale",
        "desc": "Primary render buffer scaling factor in VR stereo before DLSS or TAA reconstruction.",
        "cpu_impact": "Zero.",
        "gpu_impact": "Directly scales total rasterized pixel count in both eyes.",
        "liner_advice": "Strictly 100% when DLSS is active. Lowering this value causes double downscaling blur!",
        "ga_advice": "100%.",
        "tradeoffs": [
            ("100%", "Native input resolution into DLSS tensor reconstruction for maximum cockpit gauge legibility", "Standard stereo pixel workload"),
            ("< 100%", "Slight GPU fill rate relief", "Noticeable stereo blurriness across avionics numbers")
        ]
    },
    "sharpen_amount_vr": {
        "title": "VR Sharpening",
        "desc": "Post-processing contrast-adaptive sharpening filter applied to the stereo headset view.",
        "cpu_impact": "Zero.",
        "gpu_impact": "Negligible post-process compute pass.",
        "liner_advice": "0.20 when paired with DLSS. Prevents edge shimmering across runway markings and horizon.",
        "ga_advice": "0.20 to 0.50.",
        "tradeoffs": [
            ("0.20", "Clean edge definition without high-frequency aliasing shimmer", "Subtle sharpening effect"),
            ("> 1.00", "Heavily pronounced edges", "Harsh sparkling noise on trees, fences, and runway centerlines")
        ]
    },
    "foveated_rendering": {
        "title": "Foveated Rendering",
        "desc": "Variable Rate Shading (VRS) rendering the center of the VR view at full resolution while reducing shading rate in the peripheral vision.",
        "cpu_impact": "Zero.",
        "gpu_impact": "Provides 10-15% GPU frame time reduction in compatible VR headsets.",
        "liner_advice": "Always enable (ON) in VR to maintain smooth head tracking and 1/2 sync reprojection.",
        "ga_advice": "ON.",
        "tradeoffs": [
            ("ON", "10-15% GPU performance gain in headset with zero perceptible center loss", "Slightly reduced pixel shading in far peripheral vision"),
            ("OFF", "Uniform peripheral shading", "Unnecessary GPU fill rate spent where the human eye does not focus")
        ]
    },
    "foveated_scale": {
        "title": "Foveated Rendering Scale",
        "desc": "Radius of the central high-resolution foveal zone in VR headsets.",
        "cpu_impact": "Zero.",
        "gpu_impact": "Governs the proportion of pixels rendered at full resolution versus lower peripheral rate.",
        "liner_advice": "40% offers the ideal balance between wide cockpit clarity and peripheral GPU savings.",
        "ga_advice": "40% to 50%.",
        "tradeoffs": [
            ("40% - 50%", "Generous central focus circle covering instruments and windshield", "Good peripheral performance reclamation"),
            ("> 60%", "Larger center circle", "Diminished performance headroom")
        ]
    },
    "reprojection_mode": {
        "title": "VR Reprojection Mode",
        "desc": "Motion vector reprojection engine synthesizing intermediate stereo frames to match headset panel refresh rate.",
        "cpu_impact": "Zero MainThread load. Pacing managed in OpenXR / headset compositor runtime.",
        "gpu_impact": "Optical flow or depth reprojection pass in headset compositor runtime.",
        "liner_advice": "OFF for pure native frames (essential with OFXR Bridge or high-end rigs) or AUTO / 1/2 REPROJECTION for fixed pacing.",
        "ga_advice": "OFF or AUTO.",
        "tradeoffs": [
            ("OFF (Recommended Native)", "Zero warping, razor-sharp cockpit dials and propeller blades, pure 1:1 motion-to-photon latency (mandatory with OFXR Bridge)", "Requires solid hardware to sustain native framerate"),
            ("AUTO", "Dynamic reprojection: engages smoothly only when framerate drops below headset refresh rate", "Occasional edge shimmering during rapid head turns"),
            ("1/2 REPROJECTION", "Locks sim to 1/2 headset refresh rate for consistent cinematic pacing on heavy airliners", "Slight motion warping around propeller and canopy frames")
        ]
    },
    "cubemap_reflections": {
        "title": "Cubemap Reflections",
        "desc": "Texture resolution of local reflection probes capturing cockpit canopy glass, dials, and chrome throttle levers.",
        "cpu_impact": "Low.",
        "gpu_impact": "Probe render target memory allocation and face redraw pass.",
        "liner_advice": "192 or 128. Provides rich, glossy cockpit glass and dial reflections without wasteful probe memory overhead.",
        "ga_advice": "192 or 256.",
        "tradeoffs": [
            ("192 / 128", "Crisp cockpit reflections and canopy sheen with safe VRAM footprint", "Slightly softer specular highlights on chrome knobs"),
            ("512", "Rivet-sharp environment reflections", "Consumes extra VRAM for cubemap probe buffers")
        ]
    },
    "dof": {
        "title": "Depth Of Field (DOF)",
        "desc": "Cinematic camera lens depth of field blurring objects outside the active camera focal plane.",
        "cpu_impact": "Zero.",
        "gpu_impact": "Circle-of-confusion post-process blur pass.",
        "liner_advice": "Keep OFF. During pilot operations, instrument dials and runway lights must remain 100% sharp at all times.",
        "ga_advice": "OFF for flight, or LOW for cinematic screenshots.",
        "tradeoffs": [
            ("OFF", "Razor-sharp clarity across all flight deck instruments and exterior scenery", "Lacks cinematic camera depth blur"),
            ("ON / HIGH", "Cinematic photograph aesthetic", "Blurs avionics displays and instruments whenever camera focuses elsewhere")
        ]
    },
    "motion_blur": {
        "title": "Motion Blur",
        "desc": "Post-processing directional velocity blur applied to moving scenery and fast camera pans.",
        "cpu_impact": "Zero.",
        "gpu_impact": "Velocity buffer gathering pass.",
        "liner_advice": "Strictly OFF. Motion blur smears runway centerlines, touchdown zones, and attitude indicators during landing maneuvers.",
        "ga_advice": "OFF.",
        "tradeoffs": [
            ("OFF", "Crystal clear vision of runway markings and avionics during rapid flight maneuvers", "No artificial velocity streaking"),
            ("ON", "Sensation of extreme speed in low passes", "Smears critical flight data tapes and runway thresholds")
        ]
    },
    "particles": {
        "title": "Particles Quality",
        "desc": "Simulation density and alpha blending resolution for engine contrails, smoke, water spray, and tire smoke.",
        "cpu_impact": "Low to moderate during multi-aircraft formation or heavy reverse thrust.",
        "gpu_impact": "Heavy alpha fill-rate load when passing directly through thick smoke clouds.",
        "liner_advice": "MEDIUM. Provides realistic touchdown tire smoke, thrust reverser spray, and wing condensation without choking GPU fill-rate.",
        "ga_advice": "MEDIUM or HIGH.",
        "tradeoffs": [
            ("MEDIUM", "Authentic smoke, spray, and contrails with safe alpha blending overhead", "Subtly lower particle count in dense smoke"),
            ("ULTRA", "Massive volumetric particle counts", "Substantial framerate drops when cameras intersect dense smoke plumes")
        ]
    },
    "aircraft_traffic_quantity": {
        "title": "Aircraft Traffic Quantity",
        "desc": "Density of live and simulated AI aircraft in the surrounding airspace and on airport taxiways. MAJOR DRIVER OF CPU MAINTHREAD WORKLOAD.",
        "cpu_impact": "Extreme. Each active aircraft executes flight plan calculations, physics, and generates draw calls on the MainThread.",
        "gpu_impact": "Low to moderate.",
        "liner_advice": "OFF or LOW. For study-level airliners at busy hub airports, AI traffic simulation is the #1 culprit behind landing flare stuttering.",
        "ga_advice": "LOW or MEDIUM.",
        "tradeoffs": [
            ("OFF / LOW", "Saves critical CPU MainThread frame time; ensures silky 60+ FPS touchdown flare", "Quieter airspace without heavy AI traffic swarms"),
            ("HIGH / ULTRA", "Packed skies and busy taxiways", "Severe CPU bottlenecking and micro-stutters near major hubs")
        ]
    },
    "aircraft_traffic_variety": {
        "title": "Aircraft Traffic Variety",
        "desc": "Controls how Microsoft Flight Simulator selects and displays unique 3D aircraft models and authentic airline liveries for live, AI, and third-party injected traffic (FSLTL, BeyondATC, SayIntentions, VATSIM/vPilot).",
        "cpu_impact": "Negligible CPU overhead. Handled primarily by Direct3D 12 texture streaming.",
        "gpu_impact": "Directly scales dedicated VRAM allocation according to the number of unique 2K/4K airline liveries and 3D airframes loaded into GPU memory.",
        "liner_advice": "ULTRA (if VRAM >= 16 GB) / HIGH (if VRAM 12 GB) / MEDIUM (if VRAM <= 8 GB).\n\n• FSLTL & BeyondATC (BATC) & SayIntentions: FSLTL officially recommends setting this option to ULTRA. When set to ULTRA, MSFS pulls directly from your installed base models without substituting generic fallback aircraft. If you set this to LOW or MEDIUM on a high-end card, MSFS will override your realistic models and display plain white or generic twin-engine planes at the gates.\n• VATSIM (vPilot): While vPilot controls model matching rules via .vmr files, having Variety on ULTRA ensures MSFS never blocks or deduplicates the models matched by vPilot.\n• LOW: LOW is only acceptable as a fallback on entry-level GPUs with <= 8 GB of VRAM to prevent DirectX 12 out-of-memory crashes. On a modern GPU with 16-24 GB VRAM (RTX 4080, 4090, 7900 XTX), LOW is suboptimal as it needlessly cripples model matching realism while leaving massive VRAM unused.",
        "ga_advice": "HIGH or ULTRA on modern GPUs with >= 12 GB VRAM; MEDIUM on 8 GB GPUs.",
        "tradeoffs": [
            ("ULTRA", "FSLTL & VATSIM Golden Standard: Renders 100% authentic airline liveries with zero generic white plane fallback", "Requires sufficient VRAM (+1.5 to 2.5 GB allocated for unique livery textures)"),
            ("HIGH", "Balanced livery diversity with safe VRAM headroom on 12 GB GPUs", "Rare generic substitution at massive international hubs"),
            ("LOW", "Strict VRAM conservation for 8 GB cards", "Ruins model matching: forces generic white aircraft and identical duplicate airframes")
        ]
    },
    "parked_aircraft_quantity": {
        "title": "Parked Aircraft Quantity",
        "desc": "Number of static decorative aircraft placed at parking stands and gates across the airport.",
        "cpu_impact": "Substantial draw call overhead when taxiing past crowded terminals.",
        "gpu_impact": "Moderate polygon and texture memory cost.",
        "liner_advice": "OFF or LOW. If using third-party traffic add-ons (FSLTL, BATC), keep this strictly OFF to prevent double-spawning.",
        "ga_advice": "LOW or MEDIUM.",
        "tradeoffs": [
            ("OFF / LOW", "Eliminates redundant static model draw calls at gates", "Empty gates unless using live traffic inject tool"),
            ("HIGH", "Vibrant, crowded terminal gates", "Heavy draw call penalties lowering apron taxi FPS")
        ]
    },
    "parked_aircraft_variety": {
        "title": "Parked Aircraft Variety",
        "desc": "Controls the visual diversity and paint schemes applied to static parked aircraft spawned at terminal gates and ramp stands.",
        "cpu_impact": "Negligible CPU overhead.",
        "gpu_impact": "Allocates texture memory (VRAM) according to the diversity of static exterior airframe liveries.",
        "liner_advice": "ULTRA (if VRAM >= 16 GB) / HIGH (if VRAM 12 GB) / MEDIUM (if VRAM <= 8 GB). If you choose to enable Parked Aircraft Quantity, setting Variety to ULTRA on a high-tier GPU ensures you see diverse, authentic airline tail liveries at every gate instead of the same repetitive default scheme.",
        "ga_advice": "HIGH or ULTRA on GPUs with >= 12 GB VRAM; MEDIUM on 8 GB GPUs.",
        "tradeoffs": [
            ("ULTRA", "Maximum visual realism: authentic diverse airline liveries across all terminal stands", "Requires ample VRAM (+0.5 to 1.5 GB allocated for static liveries)"),
            ("HIGH", "Balanced gate variety with safe memory margin on 12 GB GPUs", "Occasional identical tail schemes at huge international hubs"),
            ("LOW", "Strict VRAM conservation for 8 GB cards", "Clones identical liveries across the entire apron")
        ]
    },
    "airport_services_quantity": {
        "title": "Airport Services Quantity (Airport Life)",
        "desc": "Density of default MSFS ground service equipment: catering trucks, baggage tugs, fuel tankers, and pushback vehicles roaming airport aprons.",
        "cpu_impact": "Substantial CPU pathfinding and animation dispatch overhead on airport ramps, frequently causing MainThread frame spikes and micro-stutters during taxi and apron operations.",
        "gpu_impact": "Low polygon vehicle meshes and ground equipment shadow draw calls.",
        "liner_advice": "OFF (0%). Essential when using GSX Pro (Ground Services X) or flying study-level airliners:\n• GSX Pro injects its own high-fidelity, custom-animated ground fleet (catering, baggage trains, pushback tugs with marshals, passenger stairs, GPU/ASU carts).\n• If MSFS Airport Services is NOT set to OFF, default generic Asobo ground vehicles wander aimlessly, clip through wings and fuselage, block GSX vehicles, and trigger 'Obstacle detected' pushback errors in GSX.\n• Setting to OFF eliminates default vehicle pathfinding, freeing vital CPU MainThread cycles during taxi and turnaround.",
        "ga_advice": "OFF (if using GSX) or LOW/MEDIUM for general aviation at uncontrolled airfields.",
        "tradeoffs": [
            ("OFF (0%)", "Official GSX Pro standard: completely eliminates clipping with default trucks and frees CPU apron draw calls", "Clean ramps reserved for GSX custom ground equipment"),
            ("LOW / MEDIUM", "Spawns moderate default ground equipment if not using GSX", "Minor CPU MainThread dispatch overhead"),
            ("HIGH / ULTRA", "Spawns dense swarms of default ground vehicles", "Severe collision risks with GSX and CPU MainThread frame time spikes on aprons")
        ]
    },
    "airport_services_variety": {
        "title": "Airport Services Variety",
        "desc": "Visual diversity of ground handling equipment 3D models and operator liveries (Swissport, Menzies, dnata, local fuel and catering liveries) loaded into video memory.",
        "cpu_impact": "Minimal. Catalog asset lookup on background threads.",
        "gpu_impact": "VRAM allocation for distinct vehicle textures and 3D equipment meshes.",
        "liner_advice": "LOW (recommandé pour les performances maximales) ou MEDIUM.\n• LOW : Empreinte VRAM minimale et chargement instantané des textures de piste.\n• MEDIUM / HIGH : Diversité accrue des livrées d'assistance au sol au prix d'une allocation VRAM plus importante.\n• ULTRA : Allocation mémoire maximale (+1 à +2 Go de textures), à réserver aux configurations à très grande VRAM (16 Go+).",
        "ga_advice": "LOW ou MEDIUM.",
        "tradeoffs": [
            ("LOW", "Performance maximale : empreinte VRAM minimale et chargement instantané sans saccade de streaming", "Livrées d'assistance au sol standardisées"),
            ("MEDIUM / HIGH", "Diversité visuelle équilibrée des livrées d'opérateurs au sol", "Consommation mémoire vidéo accrue (+0.5 à 1.0 Go)"),
            ("ULTRA", "Diversité maximale de livrées", "Forte allocation VRAM (+1 à 2 Go)")
        ]
    },
    "road_traffic": {
        "title": "Road Traffic",
        "desc": "Density of cars, buses, and trucks simulated along highways, bridges, and city avenues.",
        "cpu_impact": "Moderate CPU vehicle simulation overhead.",
        "gpu_impact": "Very low.",
        "liner_advice": "MEDIUM. Provides realistic traffic flows along approach paths without wasting CPU power.",
        "ga_advice": "MEDIUM or HIGH.",
        "tradeoffs": [
            ("MEDIUM", "Lively motorways beneath approach corridors with zero stutter", "Balanced vehicle density"),
            ("OFF", "Ghost town highways", "Negligible framerate difference over Medium")
        ]
    },
    "sea_traffic": {
        "title": "Sea Traffic (Ships & Ferries)",
        "desc": "Density of commercial maritime shipping, cargo container freighters, cruise liners, oil tankers, and ferries navigating coastal and open-sea waters.",
        "cpu_impact": "Very low. Handled on asynchronous background waypoint navigation threads with zero impact inland and only ~1-2 FPS max near busy coastal ports.",
        "gpu_impact": "Low polygon vessel meshes and wake particle generation. Negligible rasterization overhead.",
        "liner_advice": "OFF (maximum performance) ou LOW (5% - 10%, standard recommandé pour GAIST / Seafront Simulations).\n• OFF désactive complètement les trajectoires maritimes en tâche de fond pour une efficacité maximale.\n• LOW (5-10%) permet d'afficher les navires réels via GAIST/Seafront sans encombrement ni collisions visuelles.\n• HIGH/ULTRA n'a qu'un impact très modeste sur le framerate (~1-3 FPS max près des côtes, 0 FPS dans les terres), mais fait apparaître des navires génériques en surnombre.",
        "ga_advice": "OFF pour une efficacité maximale, ou LOW (5-10%) pour le réalisme côtier.",
        "tradeoffs": [
            ("OFF", "Désactive totalement la navigation maritime en tâche de fond", "Plans d'eau déserts"),
            ("LOW (5-10%)", "Standard GAIST & Seafront Simulations : flotte maritime réaliste sans congestion", "Impact quasi-nul sur les FPS"),
            ("HIGH / ULTRA", "Trafic maritime dense sur les côtes et ports majeurs", "Impact très modeste (~1-3 FPS près des côtes, nul dans les terres)")
        ]
    },
    "characters_quantity": {
        "title": "Characters Quantity (Worker Density)",
        "desc": "Density of animated ground personnel, ramp workers, marshallers, and gate crew roaming around airport stands.",
        "cpu_impact": "Skeletal bone animation and transformation hierarchy calculated on the CPU MainThread. Crowds of workers multiply draw calls at busy terminals.",
        "gpu_impact": "Low polygon character meshes.",
        "liner_advice": "OFF (0%) ou LOW (15-20%).\n• OFF (0%) : Choix de performance maximale (0 calcul d'animation squelettique, 0 draw call supplémentaire). Idéal et recommandé pour les configurations CPU modestes ou les puristes de fluidité.\n• LOW (15-20%) : Compromis fonctionnel sur machine moderne (standard FSLTL : garantit l'apparition des marshallers avec bâtons lumineux et agents de calage sans impact sensible sur un CPU récent).\n• Éviter MEDIUM, HIGH et ULTRA qui saturent le CPU MainThread avec des foules de travailleurs itinérants.",
        "ga_advice": "OFF ou LOW.",
        "tradeoffs": [
            ("OFF (0%)", "Performance CPU maximale : élimination totale des calculs de squelette osseux et des draw calls de personnel au terminal", "Pas de placeurs de porte (marshallers) ni de personnel animé"),
            ("LOW (15-20%)", "Standard FSLTL & compromis équilibré : garantit l'apparition des placeurs de guidage avec un impact CPU négligeable sur machine moderne", "Légère sollicitation MainThread lors des gros rassemblements au sol"),
            ("MEDIUM / HIGH / ULTRA", "Terminaux très peuplés", "Pénalité sévère sur le CPU MainThread (stutters au roulage)")
        ]
    },
    "characters_variety": {
        "title": "Characters Variety",
        "desc": "Visual variety of ground personnel uniforms, high-visibility jackets, and airport ramp worker models.",
        "cpu_impact": "Low CPU dispatch for avatar model selection and texture binding.",
        "gpu_impact": "Texture memory allocation (VRAM) for varied ground crew apparel.",
        "liner_advice": "LOW (recommandé pour une fluidité maximale) ou MEDIUM.\n• LOW : Empreinte VRAM minimale et chargement instantané sans saccades de texture streaming.\n• MEDIUM : Diversité équilibrée des tenues d'agents de piste sans surcharger la mémoire vidéo.\n• ULTRA : Allocation mémoire excessive pour du personnel au sol observé à distance depuis le cockpit.",
        "ga_advice": "LOW ou MEDIUM.",
        "tradeoffs": [
            ("LOW", "Performance maximale : empreinte VRAM minimale et chargement instantané des textures", "Tenues d'agents de piste standardisées"),
            ("MEDIUM", "Diversité visuelle équilibrée des uniformes de piste", "Légère allocation de texture VRAM"),
            ("HIGH / ULTRA", "Variété maximale des uniformes et gilets de sécurité", "Allocation mémoire vidéo superflue")
        ]
    },
    "characters_quality": {
        "title": "Characters Quality",
        "desc": "3D polygon mesh density and facial detail for ramp personnel and pilots.",
        "cpu_impact": "Low (vertex transformation and bone hierarchy LOD).",
        "gpu_impact": "Polygon rasterization and vertex processing workload.",
        "liner_advice": "LOW ou MEDIUM.\n• LOW : Choix de performance maximale (maillage polygonal allégé, charge géométrique minimale). Fortement recommandé sur configurations modestes et pour les cockpits de liners où le personnel au sol est observé à distance.\n• MEDIUM : Compromis standard propre sans perte visible.\n• Éviter HIGH et ULTRA : détails vestimentaires et faciaux invisibles depuis le cockpit qui consomment inutilement des ressources géométriques.",
        "ga_advice": "LOW ou MEDIUM.",
        "tradeoffs": [
            ("LOW", "Performance maximale : maillage 3D allégé, charge géométrique et vertex processing minimaux", "Détails faciaux simplifiés de très près"),
            ("MEDIUM", "Modèles humains équilibrés observés depuis les fenêtres du cockpit", "Légère augmentation du nombre de polygones"),
            ("HIGH / ULTRA", "Plis de vêtements et accessoires détaillés", "Charge géométrique inutile depuis le cockpit")
        ]
    },
    "fauna_density": {
        "title": "Fauna Density",
        "desc": "Spawning frequency of wildlife: bird flocks, safari animals, and marine life in designated biome zones.",
        "cpu_impact": "Low.",
        "gpu_impact": "Low.",
        "liner_advice": "OFF or LOW. Birds and wildlife are not simulated along high-altitude airliner flight paths.",
        "ga_advice": "MEDIUM or HIGH for bush flying immersion.",
        "tradeoffs": [
            ("OFF / LOW", "Saves background biome animal spawning cycles", "No bird flocks around commercial airports"),
            ("HIGH", "Exciting wildlife encounters during backcountry exploration", "Minor background simulation overhead")
        ]
    },
    "seatbelt_visibility": {
        "title": "Seatbelt Visibility",
        "desc": "Rendering of cockpit shoulder harness straps and pilot seatbelts across empty seats.",
        "cpu_impact": "Zero.",
        "gpu_impact": "Negligible polygon cost. Setting to OFF eliminates seatbelt mesh geometry from cockpit draw calls.",
        "liner_advice": "OFF (Optimum) pour éliminer les polygones des harnais de siège, ou ON (Acceptable) pour l'immersion visuelle dans le poste de pilotage.\n• OFF : Gain minime de géométrie cockpit (statut vert / optimum).\n• ON : Affiche les ceintures et harnais de sécurité drapés sur les sièges (statut ambre / acceptable).",
        "ga_advice": "OFF pour la performance, ON pour l'immersion.",
        "tradeoffs": [
            ("OFF (Optimum)", "Suppression du maillage des ceintures, allège la géométrie cockpit", "Harnais non visibles"),
            ("ON (Acceptable)", "Harnais et ceintures drapés sur les sièges pour l'immersion cockpit", "Léger surcoût géométrique dans le cockpit")
        ]
    }
}


def get_lod_thresholds(
    key: str,
    is_liner: bool,
    is_vr: bool,
    is_x3d: bool,
    is_flagship_cpu: bool,
    is_legacy_cpu: bool,
    is_flagship_gpu: bool,
    is_high_tier_gpu: bool,
    is_entry_gpu: bool,
    vram_gb: float
) -> Tuple[int, int, int]:
    """
    Returns (green_max, amber_max, orange_max) calibrated for CPU/GPU tier and flight scenario.
    - val <= green_max: OPTIMUM (emerald) - ALWAYS >= 100 for all systems.
    - green_max < val <= amber_max: ACCEPTABLE (amber)
    - amber_max < val <= orange_max: SUBOPTIMAL (orange)
    - val > orange_max: HAZARD (rose)
    """
    is_entry_rig = is_legacy_cpu or is_entry_gpu or (vram_gb <= 8.5)
    is_x3d_flagship = is_x3d and (is_flagship_gpu or is_high_tier_gpu)
    is_flagship = (is_flagship_cpu or is_x3d or (is_flagship_gpu and not is_legacy_cpu))
    is_mid_tier = not is_legacy_cpu and not is_entry_gpu and (vram_gb >= 10.0)

    if key in ["tlod", "terrain_lod"]:
        if is_vr:
            if is_x3d_flagship:
                # 9800X3D + 5090/4090 in VR
                return (100, 130, 170) if is_liner else (130, 170, 220)
            elif is_flagship:
                # 14900K / 7800X3D in VR
                return (100, 120, 150) if is_liner else (120, 150, 190)
            elif is_entry_rig:
                # i5 + 1060 in VR
                return (100, 110, 120) if is_liner else (100, 120, 140)
            else: # Mid-tier in VR
                return (100, 110, 130) if is_liner else (100, 130, 160)
        else: # 2D Desktop
            if is_x3d_flagship:
                # 9800X3D + 5090 in 2D
                return (150, 200, 260) if is_liner else (200, 260, 320)
            elif is_flagship:
                # 14900K / 285K / 7950X in 2D
                return (130, 180, 240) if is_liner else (180, 240, 300)
            elif is_high_tier_gpu and not is_legacy_cpu:
                # Modern fast CPU + 4070/3080
                return (120, 160, 220) if is_liner else (150, 220, 280)
            elif is_entry_rig:
                # i5 + 1060 / 8GB VRAM
                return (100, 120, 150) if is_liner else (100, 130, 170)
            else: # Mid-tier (13600K / 5600X + 3060/4060)
                return (100, 140, 180) if is_liner else (120, 170, 220)
    else: # OLOD
        if is_vr:
            if is_x3d_flagship:
                return 110, 140, 180
            elif is_flagship:
                return 100, 130, 160
            elif is_entry_rig:
                return 100, 110, 130
            else:
                return 100, 120, 150
        else: # 2D Desktop
            if is_x3d_flagship:
                return 140, 190, 250
            elif is_flagship:
                return 130, 180, 240
            elif is_high_tier_gpu and not is_legacy_cpu:
                return 120, 160, 220
            elif is_entry_rig:
                return 100, 120, 150
            else:
                return 100, 140, 180


def get_lod_rating_info(
    val: Any,
    key: str,
    is_liner: bool,
    is_vr: bool,
    is_x3d: bool,
    is_flagship_cpu: bool,
    is_legacy_cpu: bool,
    is_flagship_gpu: bool,
    is_high_tier_gpu: bool,
    is_entry_gpu: bool,
    vram_gb: float,
    autofps: bool = False
) -> Tuple[str, str, str, str]:
    """
    Returns (rating, color, label, reason) for a given TLOD or OLOD value.
    """
    try:
        clean_str = str(val).replace('Dynamic', '').replace('(', '').replace(')', '').strip()
        num = int(''.join(filter(str.isdigit, clean_str)) or 100)
    except Exception:
        num = 100

    is_tlod = key in ["tlod", "terrain_lod"]

    if autofps and is_tlod:
        return "optimum", "emerald", "OPTIMUM", f"AutoFPS dynamic calibration active (Target base: {num})."

    green_max, amber_max, orange_max = get_lod_thresholds(
        key, is_liner, is_vr, is_x3d, is_flagship_cpu, is_legacy_cpu,
        is_flagship_gpu, is_high_tier_gpu, is_entry_gpu, vram_gb
    )

    if num <= green_max:
        r, c = "optimum", "emerald"
        lbl = "OPTIMUM"
        if is_tlod:
            reason = f"TLOD {num} is fully within safe MainThread frame budget (<= {green_max}). Fluid approach and flare."
        else:
            reason = f"OLOD {num} keeps terminal and autogen draw calls well within single-core dispatch budget (<= {green_max})."
    elif num <= amber_max:
        r, c = "acceptable", "amber"
        lbl = "ACCEPTABLE"
        if is_tlod:
            reason = f"TLOD {num} imposes moderate CPU MainThread load ({green_max+1}-{amber_max}). Stable in cruise, slight latency variance possible at major hubs."
        else:
            reason = f"OLOD {num} increases 3D object draw calls ({green_max+1}-{amber_max}). Sustainable on this hardware."
    elif num <= orange_max:
        r, c = "suboptimal", "orange"
        lbl = "SUBOPTIMAL"
        if is_tlod:
            reason = f"TLOD {num} pushes CPU MainThread near limits ({amber_max+1}-{orange_max}). Risk of micro-stutters during landing flare at dense airports."
        else:
            reason = f"OLOD {num} generates high 3D draw call density ({amber_max+1}-{orange_max}). May cause frame drops at large international hubs."
    else:
        r, c = "hazard", "rose"
        lbl = "HAZARD"
        if is_tlod:
            reason = f"TLOD {num} severely exceeds hardware MainThread capacity (> {orange_max})! High risk of landing freezes and audio crackling."
        else:
            reason = f"OLOD {num} severely overloads draw call dispatch (> {orange_max})! Significant CPU frame time penalty at airports."

    return r, c, lbl, reason


def calculate_option_ratings(key: str, options: List[str], is_liner: bool, is_vr: bool, vram_gb: float = 16.0, target_fps: int = 60, native_w: int = 2560, native_h: int = 1440, gpu: Optional[Dict[str, Any]] = None, cpu: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, str]]:
    """Retourne pour chaque option sa classification ('optimum', 'acceptable', 'suboptimal', 'hazard') et sa couleur ('emerald', 'amber', 'orange', 'rose')."""
    gpu_full = str((gpu or {}).get("name") or "").upper()
    cpu_full = str((cpu or {}).get("name") or "").upper()
    vram_gb = float((gpu or {}).get("vram_total_gb") or vram_gb or 16.0)

    is_flagship_gpu = any(k in gpu_full for k in ["5090", "5080", "4090", "4080", "7900 XTX", "7900XTX"]) or vram_gb >= 20.0
    is_high_tier_gpu = is_flagship_gpu or any(k in gpu_full for k in ["4070 TI", "4070TI", "4070 SUPER", "4070", "3090", "3080", "7900 XT", "7900XT", "7900 GRE", "6800", "6900"]) or vram_gb >= 12.0
    is_vram_constrained = vram_gb <= 8.5
    is_entry_gpu = any(k in gpu_full for k in ["1660", "1060", "1070", "1650", "3050", "2060", "6600", "580", "570"]) or (vram_gb <= 6.5)

    is_x3d = "X3D" in cpu_full or "3D V-CACHE" in cpu_full
    is_flagship_cpu = is_x3d or any(k in cpu_full for k in ["13900", "14900", "285K", "9950", "7950"])
    is_legacy_cpu = any(k in cpu_full for k in ["8700", "9700", "9900", "10700", "3600", "2600", "1600", "2700", "I5-2", "I5-3", "I5-4", "I5-6", "I5-7", "I5-8", "I5-9", "I5-10", "I7-2", "I7-3", "I7-4", "I7-6", "I7-7", "I7-8", "I7-9", "I3-"])
    is_entry_rig = is_legacy_cpu or is_entry_gpu or is_vram_constrained

    ratings = {}
    for opt in options:
        opt_str = str(opt).strip()
        o_up = opt_str.upper()
        
        r = "acceptable"
        c = "amber"
        reason = None
        tag = None

        if key == "resolution":
            try:
                tokens = opt_str.replace('x', ' ').replace('X', ' ').split()
                if len(tokens) >= 2:
                    w, h = int(tokens[0]), int(tokens[1])
                    if w == native_w and h == native_h:
                        r, c = "optimum", "emerald"
                        reason = f"Native display resolution ({w}x{h}): perfect 1:1 pixel grid mapping, crystal clear avionics and runway lights."
                    elif w > native_w or h > native_h:
                        r, c = "hazard", "rose"
                        reason = f"DSR / Super-sampling ({w}x{h}): exceeds physical display panel ({native_w}x{native_h}), wasting massive GPU fillrate."
                    else:
                        r, c = "suboptimal", "orange"
                        reason = f"Sub-native display resolution ({w}x{h}): causes display scaling blur across cockpit avionics and runway markings."
                else:
                    r, c = "acceptable", "amber"
                    reason = f"Display resolution {opt_str}."
            except Exception:
                r, c = "acceptable", "amber"
                reason = "Display resolution setting."

        elif key == "texture_resolution":
            opt_lead = o_up.split("(")[0].strip()
            if is_vr:
                if "ULTRA" in opt_lead:
                    r, c = "hazard", "rose"
                    reason = "Full 4K Texture Atlases (14-16 GB Alloc): extreme VRAM footprint saturates stereo buffers and induces headset compositor tracking freezes."
                elif "HIGH" in opt_lead:
                    r, c = ("acceptable", "amber") if is_flagship_gpu else ("suboptimal", "orange")
                    reason = "2K High-Res Textures (9-11 GB Alloc): heavy VRAM footprint, high risk of stereo paging stutters during final approach."
                elif "MEDIUM" in opt_lead:
                    r, c = ("optimum", "emerald") if is_flagship_gpu else ("acceptable", "amber")
                    reason = "1K Compressed Textures (6-8 GB Alloc): balanced memory allocation, viable with 16 GB+ VRAM."
                else: # LOW
                    r, c = "optimum", "emerald"
                    reason = "512px Optimized Textures (3-4 GB Alloc): minimal memory footprint, frees 6-8 GB VRAM to guarantee zero compositor drops."
            else: # 2D Desktop
                if is_liner:
                    if "LOW" in opt_lead:
                        r, c = "optimum", "emerald"
                        reason = "512px Optimized Textures (3-4 GB Alloc): ultra-safe VRAM footprint, prevents D3D12 paging freezes at dense hubs."
                    elif "MEDIUM" in opt_lead:
                        r, c = ("optimum", "emerald") if vram_gb >= 16.0 else ("acceptable", "amber")
                        reason = "1K Compressed Textures (6-8 GB Alloc): balanced memory footprint with safe headroom on complex airliners."
                    elif "HIGH" in opt_lead:
                        r, c = ("acceptable", "amber") if vram_gb >= 16.0 else ("suboptimal", "orange")
                        reason = f"2K High-Res Textures (9-11 GB Alloc): approaches VRAM budget limits with airliners on {vram_gb:.0f} GB VRAM."
                    else: # ULTRA
                        r, c = ("acceptable", "amber") if vram_gb >= 24.0 else ("hazard", "rose")
                        reason = "Full 4K Texture Atlases (14-16 GB Alloc): severe VRAM overflow and heavy stuttering on complex airliners at heavy hubs."
                else: # GA / VFR
                    if "ULTRA" in opt_lead:
                        r, c = ("optimum", "emerald") if vram_gb >= 16.0 else ("acceptable", "amber")
                        reason = "Full 4K Texture Atlases (14-16 GB Alloc): maximum photorealism for low-altitude VFR sightseeing on 24 GB+ GPUs."
                    elif "HIGH" in opt_lead:
                        r, c = "optimum", "emerald"
                        reason = "2K High-Res Textures (9-11 GB Alloc): crisp ground terrain, runway markings, and cockpit placards with ample headroom."
                    elif "MEDIUM" in opt_lead:
                        r, c = "acceptable", "amber"
                        reason = "1K Compressed Textures (6-8 GB Alloc): good performance, but slight ground texture softness at low altitude."
                    else: # LOW
                        r, c = "acceptable", "amber"
                        reason = "512px Optimized Textures (3-4 GB Alloc): unnecessarily blurry for VFR sightseeing flights when VRAM headroom is plentiful."

        elif key == "glass_cockpits":
            opt_lead = o_up.split("(")[0].strip()
            if is_liner:
                if is_vr:
                    if "LOW" in opt_lead or "QUARTER" in opt_lead:
                        r, c = "optimum", "emerald"
                        reason = "Quarter-rate display update: avionics update every 4th frame, freeing maximum CPU MainThread cycles in VR."
                    elif "MEDIUM" in opt_lead or "HALF" in opt_lead:
                        r, c = "acceptable", "amber"
                        reason = "Half-rate display update: avionics update every 2nd frame (~30-45 FPS), balanced for VR headsets."
                    else: # HIGH / FULL
                        r, c = "suboptimal", "orange"
                        reason = "Full rate display update: adds 2-4ms MainThread CoherentGT UI load, risking VR reprojection stutters."
                else: # 2D
                    if "MEDIUM" in opt_lead or "HALF" in opt_lead:
                        r, c = "optimum", "emerald"
                        reason = "Half-rate display update: avionics update every 2nd frame (~30-45 FPS), delivering smooth dials while halving CPU UI load."
                    elif "LOW" in opt_lead or "QUARTER" in opt_lead:
                        r, c = "acceptable", "amber"
                        reason = "Quarter-rate display update: avionics update every 4th frame, freeing maximum CPU MainThread cycles on complex airliners."
                    else: # HIGH / FULL
                        r, c = ("optimum", "emerald") if is_flagship_cpu else ("acceptable", "amber")
                        reason = "Full rate display update: avionics instruments render every frame, adding 2-4ms MainThread CoherentGT UI load."
            else: # GA
                if is_vr:
                    if "LOW" in opt_lead or "QUARTER" in opt_lead:
                        r, c = "optimum", "emerald"
                        reason = "Quarter-rate display update: preserves CPU frame times for stereo tracking in VR."
                    elif "MEDIUM" in opt_lead or "HALF" in opt_lead:
                        r, c = "acceptable", "amber"
                        reason = "Half-rate display update: smooth analog and digital gauges with low UI thread overhead in VR."
                    else:
                        r, c = "suboptimal", "orange"
                        reason = "Full rate display update in VR: higher UI thread dispatch time."
                else: # 2D GA
                    if "HIGH" in opt_lead or "FULL" in opt_lead:
                        r, c = "optimum", "emerald"
                        reason = "Full rate display update: silky smooth needle movements on G1000 and steam gauges with negligible GA UI overhead."
                    elif "MEDIUM" in opt_lead or "HALF" in opt_lead:
                        r, c = "acceptable", "amber"
                        reason = "Half-rate display update: clean needle animations with reduced CPU overhead."
                    else:
                        r, c = "acceptable", "amber"
                        reason = "Quarter-rate display update: slight stepping visible on fast-moving altitude and airspeed needles."

        elif key == "max_frame_rate":
            clean_num = ''.join(filter(str.isdigit, opt_str))
            if clean_num and int(clean_num) == target_fps:
                r, c = "optimum", "emerald"
                reason = f"Exact 1/2 sync divisor ({target_fps} FPS): delivers perfect 1:2 monitor frame cadence without micro-stutter."
            elif o_up == "OFF" or opt_str == "0":
                r, c = "acceptable", "amber"
                reason = "Uncapped FPS: relies on external frame limiters (RTSS / NVCP) or G-Sync/FreeSync VRR."
            elif clean_num and int(clean_num) in [30, 36, 40, 45, 60, 72, 80, 82, 90, 120, 144, 165, 180, 240]:
                r, c = "acceptable", "amber"
                reason = f"Manual cap ({clean_num} FPS): functional limiter, but misaligned with the ideal 1/2 refresh divisor ({target_fps} FPS)."
            else:
                r, c = "suboptimal", "orange"
                reason = "Non-standard frame limit: may introduce uneven frame delivery intervals."

        elif key == "frame_generation":
            if is_vr:
                if o_up in ["OFF", "NONE", "0"]:
                    r, c = "optimum", "emerald"
                    reason = "Direct stereo presentation: zero headset compositor latency or motion vector warping."
                else:
                    r, c = "hazard", "rose"
                    reason = "HAZARD in VR: optical flow frame interpolation induces severe headset motion disorientation and edge tearing."
            else:
                is_nvidia = any(x in gpu_full for x in ["NVIDIA", "RTX", "GTX"])
                if "DLSSG" in o_up:
                    r, c = ("optimum", "emerald") if is_nvidia else ("hazard", "rose")
                    reason = "Optical Flow Frame Generation: generates 1 AI frame per native frame, doubling smoothness with zero CPU cost." if is_nvidia else "Requires NVIDIA RTX 40/50 series GPU with Optical Flow Accelerator."
                elif "FSR3" in o_up:
                    r, c = ("optimum", "emerald") if not is_nvidia else ("acceptable", "amber")
                    reason = "AMD FSR 3 Frame Generation: open driver/engine interpolation alternative for non-RTX 40 hardware."
                else: # OFF
                    r, c = "acceptable", "amber"
                    reason = "Native frame rendering: requires higher raw GPU and CPU framerate to achieve high refresh rates."

        elif key == "framerate_multiplier":
            if any(x in o_up for x in ["OFF", "INACTIVE", "0"]):
                r, c = "acceptable", "amber"
                reason = "Optical Flow Accelerator is idle; all displayed frames are rasterized natively."
            else:
                r, c = "optimum", "emerald"
                reason = "Standard 2X cadence: delivers 1 AI interpolated frame between consecutive native frames."

        elif key == "offscreen_precaching":
            opt_lead = o_up.split("(")[0].strip()
            if "HIGH" in opt_lead:
                r, c = "optimum", "emerald"
                reason = "Pre-loads a 90° peripheral arc: eliminates camera rotation stutter without overflowing VRAM buffer."
            elif "ULTRA" in opt_lead:
                if vram_gb >= 20.0 or is_flagship_gpu:
                    r, c = "optimum", "emerald"
                    reason = "Pre-loads full 360° environment: instantaneous camera panning for high-VRAM rigs (≥ 20 GB)."
                else:
                    r, c = "acceptable", "amber"
                    reason = "Pre-loads full 360° environment, but demands heavy system RAM and VRAM capacity."
            elif "MEDIUM" in opt_lead:
                r, c = "acceptable", "amber"
                reason = "Narrow buffer pre-caching: suitable for 16 GB RAM rigs, with minor pop-in during fast pans."
            else: # LOW
                r, c = "hazard", "rose"
                reason = "HAZARD: zero background scenery pre-caching induces severe stutter whenever panning view."

        elif key == "displacement_mapping":
            if o_up.startswith("OFF") or o_up in ["0", "FALSE"] or ("OFF" in o_up and "ON" not in o_up.split("(")[0]):
                r, c = "optimum", "emerald"
                reason = "Standard flat tarmac mesh: eliminates runway texture shimmering and saves GPU tessellation compute."
            else:
                r, c = "hazard" if is_vr else "suboptimal", "rose" if is_vr else "orange"
                if is_vr:
                    reason = "HAZARD in VR: micro-surface 3D tessellation severely taxes stereo vertex pipeline and triggers cockpit judder."
                else:
                    reason = "SUBOPTIMAL: tarmac 3D displacement is imperceptible from cockpit height (~3m) while needlessly taxing GPU."

        elif key == "dynamic_settings":
            if o_up in ["OFF", "0"]:
                r, c = "optimum", "emerald"
                reason = "Fixed native resolution: ensures steady cockpit gauge sharpness and predictable frame pacing."
            else:
                r, c = "hazard" if is_vr else "suboptimal", "rose" if is_vr else "orange"
                reason = "HAZARD in VR: dynamic resolution scaling causes sudden stereo blur and gauge illegibility." if is_vr else "Dynamic resolution scaling triggers fluctuating cockpit blur and gauge softening."

        elif key == "reflex":
            if o_up == "ON":
                r, c = "optimum", "emerald"
                reason = "Low-latency queue pacing: clears GPU render queue ahead of CPU MainThread submission, minimizing flight control lag."
            elif "BOOST" in o_up:
                r, c = "acceptable", "amber"
                reason = "Pinned GPU boost clocks: prevents core downclocking with slightly higher thermal/power draw."
            else: # OFF
                r, c = "suboptimal", "orange"
                reason = "Standard GPU buffer queue: adds 1-2 frames of display latency during pitch and roll maneuvers."

        elif key == "vsync":
            if o_up in ["ON", "1"]:
                r, c = "optimum", "emerald"
                reason = "Vertical synchronization: locks frame presentation to display refresh cycles, eliminating horizontal tearing."
            else:
                r, c = "acceptable", "amber"
                reason = "Unsynchronized presentation: delivers newest buffer immediately; causes tearing unless using external VRR."

        elif key == "vsync_interval":
            if "50%" in o_up or "1/2" in o_up:
                r, c = "optimum", "emerald"
                reason = "1/2 sync cadence: Golden standard for flight sim pacing. Perfect motion smoothness without thermal saturation."
            elif "100%" in o_up or "1/1" in o_up:
                r, c = "acceptable", "amber"
                reason = "1:1 full refresh presentation: Peak framerate; higher GPU power draw and potential stutter if MainThread drops."
            elif "33%" in o_up or "1/3" in o_up:
                r, c = "acceptable", "amber"
                reason = "1/3 sync cadence: Rock-solid pacing for ultra-heavy airliners (Fenix/PMDG) at dense photogrammetry hubs."
            else:
                r, c = "suboptimal", "orange"
                reason = "1/4 sync cadence: Aggressive framerate throttling; noticeable motion latency."

        elif key == "anti_aliasing":
            if is_vr:
                if "QUALITY" in o_up or (o_up == "DLSS" and not any(k in o_up for k in ["PERFORMANCE", "BALANCED"])):
                    r, c = "optimum", "emerald"
                    reason = "67% internal render: crisp cockpit avionics, runway markings, and clean HUD lines with DLSS AI reconstruction."
                elif "BALANCED" in o_up:
                    r, c = ("optimum", "emerald") if not is_flagship_gpu else ("acceptable", "amber")
                    reason = "58% internal render: steady 90Hz frame pacing with slight softening on distant taxiway signs."
                elif "PERFORMANCE" in o_up:
                    r, c = "acceptable" if is_entry_rig else "suboptimal", "amber" if is_entry_rig else "orange"
                    reason = "50% internal render: frees GPU fillrate, but induces noticeable blur and ghosting on EFIS dials."
                elif "DLAA" in o_up:
                    r, c = "hazard", "rose"
                    reason = "HAZARD in VR: 100% native stereo AI workload severely overburdens GPU frametimes, causing motion reprojection collapse."
                elif "TAA" in o_up:
                    r, c = "suboptimal", "orange"
                    reason = "100% native stereo rasterization: heavy fill-rate workload, risks reprojection drops without AI acceleration."
                else:
                    r, c = "acceptable", "amber"
                    reason = "Anti-aliasing mode evaluated for VR stereo pipeline."
            else: # 2D Desktop
                if "QUALITY" in o_up:
                    r, c = "optimum", "emerald"
                    reason = "67% render scale + DLSS 3 optical flow: pristine cockpit clarity with high framerate."
                elif "DLAA" in o_up:
                    if is_flagship_gpu:
                        r, c = "optimum", "emerald"
                        reason = "100% native AI anti-aliasing: absolute peak edge sharpness on flagship GPUs."
                    else:
                        r, c = "acceptable", "amber"
                        reason = "100% native AI anti-aliasing: pristine edges with full GPU rasterization workload."
                elif "BALANCED" in o_up:
                    r, c = "acceptable", "amber"
                    reason = "58% render scale: low GPU load with subtle softening on distant ground detail."
                elif "PERFORMANCE" in o_up:
                    r, c = "acceptable", "amber"
                    reason = "50% render scale: maximum framerate boost, ideal for GPU-bound scenarios."
                elif "TAA" in o_up:
                    r, c = "acceptable", "amber"
                    reason = "Standard native rasterization: reliable clarity without temporal AI reconstruction."
                else:
                    r, c = "suboptimal", "orange"
                    reason = "Legacy anti-aliasing mode with suboptimal edge reconstruction."

        elif key == "grass":
            opt_lead = o_up.split("(")[0].strip()
            if is_vr:
                if "LOW" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "Minimal 3D turf: saves critical stereo alpha fill rate and apron draw calls in VR."
                elif "MEDIUM" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Balanced grass density: realistic grass strips with controlled VR stereo fill-rate overhead."
                elif "HIGH" in opt_lead:
                    r, c = "suboptimal", "orange"
                    reason = "Heavy grass density: noticeable stereo reprojection load when taxiing on runways and grass strips in VR."
                else: # ULTRA in VR
                    r, c = "hazard", "rose"
                    reason = "HAZARD in VR: dense grass geometry overtaxes stereo rasterization and causes headset judder."
            else: # 2D Desktop
                if is_liner:
                    if "LOW" in opt_lead:
                        r, c = "optimum", "emerald"
                        reason = "Minimal 3D turf: eliminates unneeded 3D grass triangles on concrete runways, saving apron draw calls."
                    elif "MEDIUM" in opt_lead:
                        r, c = "acceptable", "amber"
                        reason = "Moderate turf density: subtle grass along taxiway borders with low alpha-testing cost."
                    elif "HIGH" in opt_lead:
                        r, c = "acceptable", "amber"
                        reason = "Dense 3D grass: adds unnecessary vertex overhead during airline operations on concrete pavements."
                    else: # ULTRA
                        r, c = "suboptimal", "orange"
                        reason = "Maximum blade density + wild flowers: heavy alpha-blending and vertex passes around airfield perimeters."
                else: # 2D GA / Bush
                    if "HIGH" in opt_lead:
                        r, c = "optimum", "emerald"
                        reason = "Rich 3D turf and wild flowers: authentic grass strip immersion for low-altitude bush flying."
                    elif "MEDIUM" in opt_lead:
                        r, c = "acceptable", "amber"
                        reason = "Balanced turf density: clean grassy airfield appearance with lower alpha cost."
                    elif "LOW" in opt_lead:
                        r, c = "acceptable", "amber"
                        reason = "Sparse grass: uninspiring flat green textures on grass airfields."
                    else: # ULTRA
                        r, c = "suboptimal", "orange"
                        reason = "Ultra-dense grass blades: unnecessary GPU overhead for minor visual difference over High."

        elif key == "volumetric_clouds":
            opt_lead = o_up.split("(")[0].strip()
            if is_vr:
                if "MEDIUM" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "8 Raymarching Samples / 32 steps: lightweight raymarching, saves substantial stereo fill-rate in VR."
                elif "HIGH" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "12 Raymarching Samples / 48 steps: crisp cloud boundaries, but taxes stereo frame times in dense overcast."
                elif "LOW" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "4 Raymarching Samples / 16 steps: coarse voxel sampling with visible edge dithering and reduced atmospheric depth."
                else: # ULTRA in VR
                    r, c = "hazard", "rose"
                    reason = "HAZARD in VR: 16 Raymarching Samples overtaxes stereo frame times, triggering reprojection drops in weather."
            else: # 2D Desktop
                if "HIGH" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "12 Raymarching Samples / 48 steps: excellent volumetric light scattering with 15-20% faster frame times than Ultra."
                elif "ULTRA" in opt_lead:
                    r, c = ("suboptimal", "orange") if is_entry_gpu else ("acceptable", "amber")
                    reason = "16 Raymarching Samples / 64 steps: full volumetric density, but costs 3-4ms extra GPU frame time in dense overcast and storms."
                elif "MEDIUM" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "8 Raymarching Samples / 32 steps: solid cloud density with fast compute, subtle pixelation on cloud edges."
                else: # LOW
                    r, c = "suboptimal", "orange"
                    reason = "4 Raymarching Samples / 16 steps: coarse voxel sampling with visible edge dithering."

        elif key == "anisotropic_filtering":
            if "16X" in o_up:
                r, c = "optimum", "emerald"
                reason = "16-sample oblique filtering: keeps runway centerline, touchdown markers, and taxi lines razor-sharp at shallow angles."
            elif "8X" in o_up:
                r, c = "acceptable", "amber"
                reason = "8-sample texture filtering: clean markings with slight softening on distant runway thresholds."
            elif "4X" in o_up:
                r, c = "suboptimal", "orange"
                reason = "4-sample texture filtering: noticeable texture blurring on runway surfaces beyond 200 meters."
            else: # 2X / OFF
                r, c = "suboptimal", "orange"
                reason = "Low/No anisotropic sampling: runway and taxiway lines blur into muddy streaks at glancing cockpit angles."

        elif key in ["buildings", "vector_data_buildings"]:
            opt_lead = o_up.split("(")[0].strip()
            if is_vr:
                if "MEDIUM" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "Simplified building meshes + 1K atlases: lightweight autogen geometry, optimal for VR stereo frame budgets."
                elif "HIGH" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Standard extrusion + 2K facade atlases: crisp urban skylines with ~25% higher draw calls in VR."
                elif "LOW" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Flat rooftops + low-res textures: minimal geometry dispatch, but noticeable suburban pop-in."
                else: # ULTRA in VR
                    r, c = "suboptimal", "orange"
                    reason = "Full footprint extrusion + 4K facade atlases: heavy draw call volume and VRAM pressure in VR headset."
            else: # 2D Desktop
                if "HIGH" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "Standard extrusion + 2K facade atlases: sharp urban skylines with ~25% lower draw calls and stable VRAM headroom."
                elif "ULTRA" in opt_lead:
                    r, c = ("suboptimal", "orange") if is_entry_gpu else ("acceptable", "amber")
                    reason = "Full footprint extrusion + 4K facade atlases: maximum building LOD distance, but adds ~25% extra autogen draw calls at major hubs."
                elif "MEDIUM" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Simplified building meshes + 1K atlases: good performance on mid-tier hardware with minor rooftop detail loss."
                else: # LOW
                    r, c = "suboptimal", "orange"
                    reason = "Flat rooftops + low-res textures: minimal geometry dispatch, but noticeable suburban pop-in."

        elif key == "trees":
            opt_lead = o_up.split("(")[0].strip()
            if is_vr:
                if "MEDIUM" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "Balanced canopy density: reduces foliage triangle count by ~30%, ideal for maintaining 60+ FPS in VR stereo."
                elif "HIGH" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Dense 3D tree canopies: realistic forests with slightly elevated stereo rasterization load."
                elif "LOW" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Sparse tree clustering: noticeable canopy pop-in during low-altitude flight."
                else: # ULTRA in VR
                    r, c = "suboptimal", "orange"
                    reason = "Highest 3D canopy density: heavy vertex and alpha-testing workload over dense forest terrain in VR."
            else: # 2D Desktop
                if "HIGH" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "Dense 3D tree canopies with optimized LOD falloff: realistic forests with negligible GPU/CPU overhead."
                elif "ULTRA" in opt_lead:
                    r, c = ("suboptimal", "orange") if is_entry_gpu else ("acceptable", "amber")
                    reason = "Highest 3D canopy density + extended draw distance: maximum foliage richness, but heavy vertex and shadow cascade passes over dense forests."
                elif "MEDIUM" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Balanced canopy density: reduces foliage triangle count by ~30%, good for entry-level GPUs."
                else: # LOW
                    r, c = "suboptimal", "orange"
                    reason = "Sparse tree clustering and aggressive LOD culling: noticeable canopy pop-in during low-altitude flight."

        elif key == "shadow_maps":
            if is_vr:
                if any(k in o_up for k in ["1024", "MEDIUM"]):
                    r, c = "optimum", "emerald"
                    reason = "1024x1024 shadow cascade buffer: soft cockpit shadows, optimal memory and rasterization balance for VR stereo."
                elif any(k in o_up for k in ["1536", "HIGH"]):
                    r, c = "acceptable", "amber"
                    reason = "1536x1536 shadow cascade buffer: crisp shadow lines, slightly higher stereo depth-pass cost in headset."
                elif any(k in o_up for k in ["512", "LOW"]):
                    r, c = "acceptable", "amber"
                    reason = "512x512 shadow cascade buffer: pixelated shadow boundaries and visible staircase artifacts across the panel."
                else: # 2048 / ULTRA in VR
                    r, c = "suboptimal", "orange"
                    reason = "2048x2048 shadow cascade buffer: razor-sharp shadow edges, but demands ~400 MB extra VRAM and heavy raster pass."
            else: # 2D Desktop
                if any(k in o_up for k in ["1536", "HIGH"]):
                    r, c = "optimum", "emerald"
                    reason = "1536x1536 shadow cascade buffer: crisp cockpit switch shadows and airframe lines with zero shimmering."
                elif any(k in o_up for k in ["2048", "ULTRA"]):
                    r, c = ("optimum", "emerald") if is_flagship_gpu else ("acceptable", "amber")
                    reason = "2048x2048 shadow cascade buffer: razor-sharp shadow edges, but demands ~400 MB extra VRAM and heavy raster pass."
                elif any(k in o_up for k in ["1024", "MEDIUM"]):
                    r, c = "acceptable", "amber"
                    reason = "1024x1024 shadow cascade buffer: soft cockpit shadows, low memory and rasterization cost."
                else: # 512 / LOW
                    r, c = "suboptimal", "orange"
                    reason = "512x512 shadow cascade buffer: pixelated shadow boundaries and visible staircase artifacts across the panel."

        elif key == "terrain_shadows":
            if is_vr:
                if any(k in o_up for k in ["256", "MEDIUM"]):
                    r, c = "optimum", "emerald"
                    reason = "256px DEM shadow heightfield: lightweight terrain self-shadowing, protects stereo frame budgets in VR."
                elif any(k in o_up for k in ["512", "HIGH"]):
                    r, c = "acceptable", "amber"
                    reason = "512px DEM shadow heightfield: realistic mountain relief, slight depth-pass cost in VR stereo."
                elif any(k in o_up for k in ["128", "LOW"]):
                    r, c = "acceptable", "amber"
                    reason = "128px DEM shadow heightfield: coarse mountain shadows with visible banding on distant ridges."
                else: # 1024 / ULTRA in VR
                    r, c = "suboptimal", "orange"
                    reason = "1024px DEM shadow heightfield: heavy compute pass across horizon, risk of VR stereo frame hitching."
            else: # 2D Desktop
                if any(k in o_up for k in ["512", "HIGH"]):
                    r, c = "optimum", "emerald"
                    reason = "512px DEM shadow heightfield: realistic mountain relief and valley shadowing during golden hour approaches."
                elif any(k in o_up for k in ["1024", "ULTRA"]):
                    r, c = ("optimum", "emerald") if is_flagship_gpu else ("acceptable", "amber")
                    reason = "1024px DEM shadow heightfield: sharp mountain ridge shadows at low sun angles, heavy compute pass across horizon."
                elif any(k in o_up for k in ["256", "MEDIUM"]):
                    r, c = "acceptable", "amber"
                    reason = "256px DEM shadow heightfield: basic mountain relief shadowing with low compute impact."
                else: # 128 / LOW
                    r, c = "suboptimal", "orange"
                    reason = "128px DEM shadow heightfield: coarse mountain shadows with visible banding on distant ridges."

        elif key == "water_waves":
            if is_vr:
                if any(k in o_up for k in ["256", "MEDIUM"]):
                    r, c = "optimum", "emerald"
                    reason = "256x256 FFT simulation grid: basic ocean swell patterns, lightweight for VR stereo pipelines."
                elif any(k in o_up for k in ["512", "HIGH"]):
                    r, c = "acceptable", "amber"
                    reason = "512x512 FFT simulation grid: realistic wave swells with moderate compute shader load in VR."
                elif any(k in o_up for k in ["128", "LOW"]):
                    r, c = "acceptable", "amber"
                    reason = "128x128 FFT simulation grid: simplified wave animation, minimal GPU compute."
                else: # 1024 / ULTRA in VR
                    r, c = "suboptimal", "orange"
                    reason = "1024x1024 FFT simulation grid: fine wave cresting and dynamic foam, heavy compute shader load for VR."
            else: # 2D Desktop
                if any(k in o_up for k in ["512", "HIGH"]):
                    r, c = "optimum", "emerald"
                    reason = "512x512 FFT simulation grid: realistic wave swells and shoreline ripples with negligible compute overhead."
                elif any(k in o_up for k in ["1024", "ULTRA"]):
                    r, c = ("suboptimal", "orange") if is_entry_gpu else ("acceptable", "amber")
                    reason = "1024x1024 FFT simulation grid: fine wave cresting and dynamic foam, requires heavy compute shader passes with minor visual difference from altitude."
                elif any(k in o_up for k in ["256", "MEDIUM"]):
                    r, c = "acceptable", "amber"
                    reason = "256x256 FFT simulation grid: clean ocean swell patterns with low compute overhead."
                else: # 128 / LOW
                    r, c = "suboptimal", "orange"
                    reason = "128x128 FFT simulation grid: simplified wave animation, minimal GPU compute."

        elif key == "reflections_ssr":
            opt_lead = o_up.split("(")[0].strip()
            if is_vr:
                if "LOW" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "Minimal ray step: lightweight reflection pass; saves critical stereo fill rate in VR."
                elif "OFF" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Disabled SSR: wet surfaces use static cubemap reflection lookups, saving maximum GPU fill rate."
                elif "MEDIUM" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Coarse screen-space ray step: basic water puddle reflections with minor reflection edge dithering in VR."
                else: # HIGH / ULTRA in VR
                    r, c = "hazard", "rose"
                    reason = "HAZARD in VR: multi-sample screen-space ray tracing overburdens stereo fill rate, inducing severe frame drops."
            else: # 2D Desktop
                if "HIGH" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "Half-resolution SSR with temporal filtering: realistic wet runway and apron reflections without severe frame hits."
                elif "ULTRA" in opt_lead:
                    r, c = ("optimum", "emerald") if is_flagship_gpu else ("acceptable", "amber")
                    reason = "Full-resolution screen-space ray tracing: crisp wet runway puddles, but high memory bandwidth and GPU fill cost."
                elif "MEDIUM" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Coarse screen-space ray step: basic water puddle reflections with minor reflection edge dithering."
                elif "LOW" in opt_lead:
                    r, c = "suboptimal", "orange"
                    reason = "Minimal ray step: low fidelity reflections with noticeable screen-edge cutoff artifacts."
                else: # OFF
                    r, c = "suboptimal", "orange"
                    reason = "Disabled SSR: wet runway surfaces look flat and lack real-time lighting reflection."

        elif key == "contact_shadows":
            opt_lead = o_up.split("(")[0].strip()
            if is_vr:
                if "MEDIUM" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "Short-range depth buffer sampling: tactile cockpit depth with virtually zero GPU frame time impact in VR."
                elif "HIGH" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Screen-space directional ray sampling: crisp tactile depth under switches and levers in VR."
                elif any(k in opt_lead for k in ["LOW", "OFF"]):
                    r, c = "acceptable", "amber"
                    reason = "Disabled / coarse sampling: cockpit controls appear slightly flat against the panel."
                else: # ULTRA
                    r, c = "suboptimal", "orange"
                    reason = "Multi-sample screen-space ray tracing: deep micro-shadows, but adds needless pixel shader cost in VR."
            else: # 2D Desktop
                if "HIGH" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "Screen-space directional ray sampling: crisp tactile depth under switches, levers, and avionics bezels."
                elif "ULTRA" in opt_lead:
                    r, c = ("optimum", "emerald") if is_flagship_gpu else ("acceptable", "amber")
                    reason = "Multi-sample screen-space ray tracing: deep ambient micro-shadows under cockpit dials, highest pixel shader cost."
                elif "MEDIUM" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Short-range depth buffer sampling: tactile cockpit depth with virtually zero GPU frame time impact."
                else: # LOW / OFF
                    r, c = "suboptimal", "orange"
                    reason = "Disabled / coarse sampling: dials and levers appear slightly detached or floating against panels."

        elif key in ["ambient_occlusion", "ssao"]:
            opt_lead = o_up.split("(")[0].strip()
            if is_vr:
                if "LOW" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "Quarter-resolution SSAO: subtle crevice shadowing, very lightweight for VR stereo viewports."
                elif "MEDIUM" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Balanced SSAO radius: natural contact shadowing with moderate shader cost in VR."
                elif "OFF" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Disabled SSAO: flight deck corners and recesses appear flatly lit without ambient depth."
                elif "HIGH" in opt_lead:
                    r, c = "suboptimal", "orange"
                    reason = "Half-resolution SSAO: natural contact shadowing, but taxes stereo fragment shaders in VR."
                else: # ULTRA in VR
                    r, c = "hazard", "rose"
                    reason = "HAZARD in VR: full-resolution SSAO pass overburdens stereo frame times and risks reprojection drops."
            else: # 2D Desktop
                if "HIGH" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "Half-resolution SSAO with bilateral blur filter: natural cockpit contact shadowing with safe GPU overhead."
                elif "ULTRA" in opt_lead:
                    r, c = ("optimum", "emerald") if is_flagship_gpu else ("acceptable", "amber")
                    reason = "Full-resolution SSAO with wide sample radius: deep corner shadowing, but taxes GPU fragment shaders."
                elif "MEDIUM" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Quarter-resolution SSAO: clean contact shading with minimal performance overhead."
                elif "LOW" in opt_lead:
                    r, c = "suboptimal", "orange"
                    reason = "Coarse SSAO sampling: faint crevice shadows with visible grain in cockpit recesses."
                else: # OFF
                    r, c = "suboptimal", "orange"
                    reason = "Disabled SSAO: flight deck corners and recesses appear flatly lit without ambient depth."

        elif key == "volumetric_lights":
            opt_lead = o_up.split("(")[0].strip()
            if is_vr:
                if "MEDIUM" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "Quarter-res raymarching: authentic light scattering shafts with minimal GPU fill-rate overhead in VR."
                elif "HIGH" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Half-res raymarching: dramatic landing light beams, moderate stereo fill load in fog."
                elif any(k in opt_lead for k in ["LOW", "OFF"]):
                    r, c = "acceptable", "amber"
                    reason = "Disabled / minimal shafts: light cones appear flat without atmospheric volumetric depth."
                else: # ULTRA
                    r, c = "suboptimal", "orange"
                    reason = "Full resolution light shaft raymarching: heavy fill-rate load in dense fog during VR flight."
            else: # 2D Desktop
                if "HIGH" in opt_lead:
                    r, c = "optimum", "emerald"
                    reason = "Half-res raymarching with temporal reconstruction: dramatic landing light beams and runway strobes in fog/clouds."
                elif "ULTRA" in opt_lead:
                    r, c = ("optimum", "emerald") if is_flagship_gpu else ("acceptable", "amber")
                    reason = "Full resolution light shaft raymarching: maximum atmospheric beam scattering, heavy fill-rate load in dense fog."
                elif "MEDIUM" in opt_lead:
                    r, c = "acceptable", "amber"
                    reason = "Quarter-res raymarching: authentic light scattering shafts with minimal GPU fill-rate overhead."
                else: # LOW / OFF
                    r, c = "suboptimal", "orange"
                    reason = "Disabled / minimal shafts: light cones appear flat without atmospheric volumetric depth."

        elif key == "windshield_effects":
            opt_lead = o_up.split("(")[0].strip()
            if "HIGH" in opt_lead:
                r, c = "optimum", "emerald"
                reason = "Dynamic raindrop physics, wiper sweep clearing, and frost accretion: full flight deck weather immersion with negligible GPU load."
            elif "ULTRA" in opt_lead:
                r, c = ("optimum", "emerald") if is_flagship_gpu else ("acceptable", "amber")
                reason = "Full resolution dynamic fluid simulation: hundreds of interacting rain droplets and dual wiper paths."
            elif "MEDIUM" in opt_lead:
                r, c = "acceptable", "amber"
                reason = "Simplified rain particle beads and wiper motion with reduced droplet count."
            else: # LOW
                r, c = "suboptimal", "orange"
                reason = "Static precipitation texture overlay without dynamic droplet physics."

        elif key in ["tlod", "olod", "terrain_lod", "objects_lod"]:
            r, c, _, reason = get_lod_rating_info(
                opt_str, key, is_liner, is_vr, is_x3d, is_flagship_cpu, is_legacy_cpu,
                is_flagship_gpu, is_high_tier_gpu, is_entry_gpu, vram_gb, autofps=False
            )
            try:
                clean_digits = ''.join(filter(str.isdigit, opt_str))
                num = int(clean_digits) if clean_digits else 100
                if num <= 50:
                    tag = "ECO"
                elif num <= 80:
                    tag = "SMOOTH"
                elif num <= 100:
                    tag = "SWEET SPOT"
                elif num <= 120:
                    tag = "BALANCED"
                elif num <= 160:
                    tag = "HIGH DETAIL"
                elif num <= 200:
                    tag = "ULTRA VFR"
                else:
                    tag = "HEAVY LOAD"
            except Exception:
                tag = None

        elif key in ["reprojection_mode"]:
            if o_up in ["OFF", "0"]:
                r, c = "optimum", "emerald"
                reason = "Native frame presentation: zero reprojection wobble or warping artifacts; lowest motion-to-photon latency."
            elif "1/2" in o_up:
                r, c = "optimum", "emerald"
                reason = "Locked 1/2 refresh cadence (e.g. 45 -> 90 Hz): silky smooth frame pacing for airliners with motion vector extrapolation."
            elif "AUTO" in o_up:
                r, c = "optimum", "emerald"
                reason = "Dynamic compositor reprojection: automatically engages only during localized framerate dips over dense scenery."
            elif "1/3" in o_up:
                r, c = "acceptable", "amber"
                reason = "Locked 1/3 refresh cadence (e.g. 30 -> 90 Hz): high stability for heavy airliner hubs, with visible propeller wobble."
            elif "DEPTH" in o_up or "MOTION" in o_up:
                r, c = "acceptable", "amber"
                reason = "OpenXR depth-guided reprojection: reduces edge shimmering around cockpit frames with slight compositor GPU overhead."
            else:
                r, c = "acceptable", "amber"
                reason = "OpenXR motion reprojection active."

        elif key in ["foveated_rendering"]:
            if o_up in ["ON", "1", "TRUE"]:
                r, c = "optimum", "emerald"
                reason = "Fixed Foveated Shading active: saves 15-20% GPU raster time by reducing shading rate in outer peripheral lens zones."
            else:
                r, c = "acceptable", "amber"
                reason = "Uniform 100% peripheral shading: renders outer lens edges at full resolution where headset optics naturally blur."

        elif key in ["foveated_scale"]:
            if "40%" in o_up:
                r, c = "optimum", "emerald"
                reason = "40% inner foveal radius: ideal sweet spot between sharp central cockpit instruments and peripheral GPU savings."
            elif any(k in o_up for k in ["30%", "50%", "60%", "70%"]):
                r, c = "acceptable", "amber"
                if "30%" in o_up:
                    reason = "30% aggressive inner radius: maximum GPU shading reduction, but inner ring boundary may be visible during saccades."
                else:
                    reason = "Wide inner radius (50-70%): imperceptible foveation boundary with modest (5-10%) peripheral GPU savings."
            else:
                r, c = "acceptable", "amber"
                reason = "Foveal resolution radius calibrated for headset optical sweet spot."

        elif key in ["primary_scaling_vr"]:
            if "100%" in o_up:
                r, c = "optimum", "emerald"
                reason = "100% Native 1:1 render scale: crystal-clear cockpit avionics and runway distance cues; avoids compound blur."
            elif any(k in o_up for k in ["95%", "90%"]):
                r, c = "acceptable", "amber"
                reason = "Sub-native render scale (90-95%): frees 10-15% GPU fillrate with minimal degradation to cockpit readability."
            elif any(k in o_up for k in ["85%", "80%"]):
                r, c = "suboptimal", "orange"
                reason = "Sub-native render scale (80-85%): softens small EFIS digital readouts and distant runway threshold markings."
            else: # 75%, 70%
                r, c = "hazard", "rose"
                reason = "HAZARD: excessive downsampling (<80%) severely degrades glass cockpit fonts and runway identification to unreadable levels."

        elif key in ["sharpen_amount_vr"]:
            try:
                num = float(opt_str)
                if abs(num - 0.20) < 0.05:
                    r, c = "optimum", "emerald"
                    reason = "CAS 20% sharpening: subtle edge contrast enhancement resolving runway markings without halo ringing."
                elif num < 0.60:
                    r, c = "acceptable", "amber"
                    reason = f"CAS {int(num*100)}% sharpening: readable cockpit text, but slight white fringe noise on high-contrast horizon edges."
                else:
                    r, c = "suboptimal", "orange"
                    reason = f"Over-sharpening ({int(num*100)}%): severe pixel halos, shimmering runway thresholds, and noisy cloud boundaries."
            except Exception:
                r, c = "acceptable", "amber"
                reason = "Post-process contrast adaptive sharpening in headset."

        elif key in ["cubemap_reflections"]:
            if is_vr:
                if o_up == "128":
                    r, c = "optimum", "emerald"
                    reason = "128px cubemap: balanced reflections on cockpit canopy glass and chrome dials with minimal stereo VRAM bandwidth."
                elif o_up in ["64", "192"]:
                    r, c = "acceptable", "amber"
                    reason = "64/192px cubemap: 64px saves VRAM while 192px offers crisper gauge glass reflections with minor stereo compute cost."
                else: # 256, 512
                    r, c = "suboptimal", "orange"
                    reason = "256/512px ultra cubemap: heavy dynamic multi-face rasterization passes for subtle reflections rarely noticed in VR."
            else:
                if o_up == "192":
                    r, c = "optimum", "emerald"
                    reason = "192px cubemap: sweet spot for glossy airframe surfaces and windshield reflections without frame rate penalty."
                elif o_up in ["128", "256", "64"]:
                    r, c = "acceptable", "amber"
                    reason = "Standard cubemap probe: 128px saves VRAM while 256px delivers sharp liveries with moderate memory footprint."
                else: # 512
                    r, c = "suboptimal", "orange"
                    reason = "512px ultra cubemap: high multi-face rasterization load for negligible visual gain over 192/256."

        elif key == "motion_blur":
            if o_up in ["OFF", "0"]:
                r, c = "optimum", "emerald"
                reason = "Disabled camera velocity smearing: crisp cockpit instruments during turbulent flight and sharp runway view during flare."
            else:
                r, c = "hazard" if is_vr else "suboptimal", "rose" if is_vr else "orange"
                reason = "HAZARD in VR: artificial motion blur induces severe vestibular disorientation and motion sickness." if is_vr else "SUBOPTIMAL: directional blur smears vital PFD/ND readouts and runway centerline during pitch and roll maneuvers."

        elif key == "dof":
            if o_up in ["OFF", "0"]:
                r, c = "optimum", "emerald"
                reason = "Full focal plane depth: guarantees both cockpit avionics and distant runway threshold remain in sharp focus."
            elif o_up == "LOW":
                r, c = "acceptable", "amber"
                reason = "Subtle cinematic defocus: minimal post-processing cost, but can occasionally soften wingtip and runway views."
            else:
                r, c = "suboptimal", "orange"
                reason = "Cinematic depth of field: artificially blurs out-of-cockpit horizon when focusing on instruments, wasting GPU compute."

        elif key in ["particles"]:
            if is_vr:
                if "LOW" in o_up:
                    r, c = "optimum", "emerald"
                    reason = "Optimized particle system: protects stereo compute buffers during heavy reverse thrust, tire smoke, and rain spray."
                elif "MEDIUM" in o_up:
                    r, c = "acceptable", "amber"
                    reason = "Balanced particle simulation: good spray effects on wet runways with moderate GPU fillrate impact."
                else: # HIGH / ULTRA
                    r, c = "suboptimal", "orange"
                    reason = "High particle density: dense smoke and cloud condensation compute triggers stereo frame drops on touchdown."
            else:
                if is_entry_rig:
                    if "LOW" in o_up:
                        r, c = "optimum", "emerald"
                        reason = "Lightweight particles: prevents alpha-blending stalls on budget GPUs during heavy rain and engine contrails."
                    elif "MEDIUM" in o_up:
                        r, c = "acceptable", "amber"
                        reason = "Balanced particle budget: realistic engine contrails and touchdown smoke without GPU thermal throttle."
                    elif "HIGH" in o_up:
                        r, c = "suboptimal", "orange"
                        reason = "High particle density: detailed spray and wingtip vortices with measurable compute overhead in storm conditions."
                    else: # ULTRA
                        r, c = "hazard", "rose"
                        reason = "HAZARD: maximum particle emitter count causes severe alpha overdraw and frametime spikes on this GPU."
                else:
                    if any(k in o_up for k in ["LOW", "MEDIUM"]):
                        r, c = "optimum", "emerald"
                        reason = "Balanced particle budget: realistic engine contrails and touchdown smoke without GPU frame drops."
                    elif "HIGH" in o_up:
                        r, c = "acceptable", "amber"
                        reason = "High particle density: authentic spray and wingtip vortices with minor GPU compute impact."
                    else: # ULTRA
                        r, c = "suboptimal", "orange"
                        reason = "Ultra particle density: maximum emitter count with minor visual gain over High during storm landings."

        elif key == "aircraft_traffic_quantity":
            if is_liner:
                if is_entry_rig:
                    if o_up == "OFF":
                        r, c = "optimum", "emerald"
                        reason = "Zero AI airliner injection: eliminates SimConnect/CPU dispatch stalls at mega-hub airports (ideal for vPilot/VATSIM/IVAO)."
                    elif o_up == "LOW":
                        r, c = "acceptable", "amber"
                        reason = "5-10 AI aircraft: light regional traffic with low MainThread flight-plan pathfinding cost."
                    else:
                        r, c = "hazard", "rose"
                        reason = "HAZARD: 15+ AI aircraft choke single-core CPU MainThread with continuous pathfinding and TCAS calculations."
                else:
                    if o_up in ["OFF", "LOW"]:
                        r, c = "optimum", "emerald"
                        reason = "Zero or light AI traffic: optimal MainThread frame pacing at major payware hubs (mandatory for VATSIM/IVAO/vPilot)." if o_up == "OFF" else "5-10 AI aircraft: authentic traffic density with minimal CPU flight-plan pathfinding overhead."
                    elif o_up == "MEDIUM":
                        r, c = "acceptable", "amber"
                        reason = "15-25 AI aircraft: moderate traffic density; adds 2-3ms MainThread route evaluation overhead."
                    else:
                        r, c = "hazard", "rose"
                        reason = "HAZARD: dense AI airliner fleet generates heavy SimConnect position updates and apron traffic conflicts."
            else: # GA
                if is_entry_rig:
                    if o_up == "LOW":
                        r, c = "optimum", "emerald"
                        reason = "Light GA traffic: authentic rural circuit aircraft with minimal CPU pathfinding impact."
                    elif o_up in ["OFF", "MEDIUM"]:
                        r, c = "acceptable", "amber"
                        reason = "Zero traffic (OFF) or moderate activity (MEDIUM): acceptable balance between CPU load and airspace immersion."
                    else:
                        r, c = "suboptimal", "orange"
                        reason = "High AI density: multiple simultaneous ground taxi path calculations reduce framerate stability."
                else:
                    if o_up in ["LOW", "MEDIUM"]:
                        r, c = "optimum", "emerald"
                        reason = "Balanced GA airspace activity: lively uncontrolled airfields with low MainThread simulation impact."
                    elif o_up == "OFF":
                        r, c = "acceptable", "amber"
                        reason = "No ambient AI traffic: cleanest frame pacing for low-spec CPU rigs."
                    else:
                        r, c = "suboptimal", "orange"
                        reason = "High AI density: multiple simultaneous ground taxi path calculations reduce framerate stability."

        elif key == "parked_aircraft_quantity":
            if is_entry_rig:
                if o_up == "OFF":
                    r, c = "optimum", "emerald"
                    reason = "Clean tarmac: frees 1-2 GB VRAM and eliminates static aircraft polygon batches at airport gates."
                elif o_up == "LOW":
                    r, c = "acceptable", "amber"
                    reason = "Light gate occupancy (~15%): realistic empty/busy gate balance with low Draw Call count."
                elif o_up == "MEDIUM":
                    r, c = "suboptimal", "orange"
                    reason = "Moderate gate occupancy (~30%): lively ramps, but introduces noticeable Draw Calls on large payware airports."
                else:
                    r, c = "hazard", "rose"
                    reason = "HAZARD: saturates GPU Draw Call queue with high-poly static airliner 3D models and liveries."
            else:
                if o_up in ["OFF", "LOW"]:
                    r, c = "optimum", "emerald"
                    reason = "Eliminates duplicate static airframes and frees critical apron CPU draw calls at terminal gates." if o_up == "OFF" else "Light gate occupancy (~15%): realistic empty/busy gate balance with low Draw Call count."
                elif o_up == "MEDIUM":
                    r, c = "acceptable", "amber"
                    reason = "Moderate gate occupancy (~30%): lively ramps, but introduces noticeable Draw Calls on large payware airports."
                else:
                    r, c = "hazard", "rose"
                    reason = "HAZARD: saturates GPU Draw Call queue with high-poly static airliner 3D models and liveries."

        elif key == "airport_services_quantity":
            if is_entry_rig:
                if o_up == "OFF":
                    r, c = "optimum", "emerald"
                    reason = "Official GSX Pro standard (OFF): eliminates vehicle clipping and frees apron CPU cycles."
                elif o_up == "LOW":
                    r, c = "acceptable", "amber"
                    reason = "Minimal apron service vehicles: essential pushback and catering without cluttering apron Draw Calls."
                elif o_up == "MEDIUM":
                    r, c = "suboptimal", "orange"
                    reason = "Standard apron traffic: realistic tugs and stairs with minor CPU physics simulation overhead."
                else:
                    r, c = "hazard", "rose"
                    reason = "HAZARD: continuous ground vehicle pathfinding across apron nodes induces CPU spikes."
            else:
                if o_up in ["OFF", "LOW"]:
                    r, c = "optimum", "emerald"
                    reason = "Official GSX Pro standard (OFF): eliminates vehicle clipping and frees apron CPU cycles." if o_up == "OFF" else "Minimal apron service vehicles: essential pushback and catering without cluttering apron Draw Calls."
                elif o_up == "MEDIUM":
                    r, c = "acceptable", "amber"
                    reason = "Standard apron traffic: realistic tugs and stairs with minor CPU physics simulation overhead."
                elif o_up == "HIGH":
                    r, c = "suboptimal", "orange"
                    reason = "Dense apron traffic: continuous pathfinding queries across apron nodes induce CPU spikes."
                else:
                    r, c = "hazard", "rose"
                    reason = "HAZARD: continuous ground vehicle pathfinding across apron nodes induces CPU spikes."

        elif key in ["aircraft_traffic_variety", "parked_aircraft_variety", "airport_services_variety", "characters_variety"]:
            if o_up == "LOW":
                r, c = "optimum", "emerald"
                reason = "Shared texture atlases: reuses common 3D liveries/models, saving up to 2 GB VRAM at major hubs."
            elif o_up == "MEDIUM":
                r, c = "acceptable", "amber"
                reason = "Moderate livery variety: good aesthetic distribution without excessive texture memory thrashing."
            elif o_up == "HIGH":
                if is_flagship_gpu or is_high_tier_gpu:
                    r, c = "acceptable", "amber"
                    reason = "Expanded model library: diverse airline liveries requiring high VRAM (≥ 12 GB) to avoid texture paging."
                else:
                    r, c = "suboptimal", "orange"
                    reason = "Expanded model library: high VRAM allocation risks texture paging and hitching on mid-range GPUs."
            else: # ULTRA
                if is_flagship_gpu:
                    r, c = "acceptable", "amber"
                    reason = "Maximum livery diversity: loads hundreds of unique liveries, requiring 16-24 GB VRAM."
                elif is_high_tier_gpu:
                    r, c = "suboptimal", "orange"
                    reason = "Full uncompressed variety: loads hundreds of unique liveries, risking VRAM overflow and hitching."
                else:
                    r, c = "hazard", "rose"
                    reason = "HAZARD: severe VRAM paging stalls when loading dozens of unique high-res liveries."

        elif key == "sea_traffic":
            if is_entry_rig:
                if o_up == "OFF":
                    r, c = "optimum", "emerald"
                    reason = "Maximum performance: maritime simulation disabled on background threads."
                elif o_up == "LOW":
                    r, c = "acceptable", "amber"
                    reason = "Official GAIST/Seafront standard (5-10%): complete AI shipping fleet without ship collisions."
                elif o_up == "MEDIUM":
                    r, c = "suboptimal", "orange"
                    reason = "Moderate maritime traffic: background wake physics and vessel tracking on coastal approaches."
                else: # HIGH / ULTRA
                    r, c = "suboptimal", "orange"
                    reason = "Dense coastal vessel fleets: continuous wake simulations tax CPU on coastal approaches."
            else:
                if o_up in ["OFF", "LOW"]:
                    r, c = "optimum", "emerald"
                    reason = "Maximum performance: maritime simulation disabled on background threads." if o_up == "OFF" else "Official GAIST/Seafront standard (5-10%): complete AI shipping fleet without ship collisions."
                elif o_up in ["MEDIUM", "HIGH", "ULTRA"]:
                    r, c = "acceptable", "amber"
                    reason = "Active maritime shipping: realistic coastal and harbor traffic with negligible inland CPU impact."

        elif key == "road_traffic":
            if is_entry_rig:
                if o_up == "OFF":
                    r, c = "optimum", "emerald"
                    reason = "Eliminates procedural vehicle thread dispatch, freeing CPU cycles."
                elif o_up == "LOW":
                    r, c = "acceptable", "amber"
                    reason = "Light highway traffic: visible vehicle flow on motorways with minimal CPU pathing impact."
                elif o_up == "MEDIUM":
                    r, c = "suboptimal", "orange"
                    reason = "Standard highway traffic: believable suburban road networks with moderate CPU vehicle dispatch."
                else:
                    r, c = "hazard", "rose"
                    reason = "HAZARD: thousands of simultaneous vehicle nodes tax CPU MainThread near urban airports."
            else:
                if o_up in ["OFF", "LOW"]:
                    r, c = "optimum", "emerald"
                    reason = "Eliminates procedural vehicle thread dispatch, freeing CPU cycles." if o_up == "OFF" else "Light highway traffic: visible vehicle flow on motorways with minimal CPU pathing impact."
                elif o_up == "MEDIUM":
                    r, c = "acceptable", "amber"
                    reason = "Standard highway traffic: believable suburban road networks with moderate CPU vehicle dispatch."
                elif o_up == "HIGH":
                    r, c = "suboptimal", "orange"
                    reason = "Dense highway networks: continuous vehicle updates tax CPU MainThread near city centers."
                else:
                    r, c = "hazard", "rose"
                    reason = "HAZARD: thousands of simultaneous vehicle nodes tax CPU MainThread near urban airports."

        elif key == "characters_quantity":
            if is_entry_rig:
                if o_up == "OFF":
                    r, c = "optimum", "emerald"
                    reason = "Maximum performance: zero ground personnel animation overhead on CPU."
                elif o_up == "LOW":
                    r, c = "acceptable", "amber"
                    reason = "Official standard (LOW): guarantees gate marshallers without CPU penalty on this system."
                elif o_up in ["MEDIUM", "HIGH"]:
                    r, c = "suboptimal", "orange"
                    reason = "Standard apron personnel: lively terminal gates with modest CPU skeletal animation overhead."
                else: # ULTRA
                    r, c = "hazard", "rose"
                    reason = "HAZARD: heavy skeletal animation and pathfinding node calculations overload CPU MainThread."
            else:
                if o_up in ["OFF", "LOW"]:
                    r, c = "optimum", "emerald"
                    reason = "Maximum performance: zero ground personnel animation overhead on CPU." if o_up == "OFF" else "Official standard (LOW): guarantees gate marshallers without CPU penalty on this system."
                elif o_up == "MEDIUM":
                    r, c = "acceptable", "amber"
                    reason = "Standard apron personnel: lively terminal gates with modest CPU skeletal animation overhead."
                elif o_up == "HIGH":
                    r, c = "suboptimal", "orange"
                    reason = "Dense apron personnel: multiple animated avatars tax CPU MainThread at terminal gates."
                else: # ULTRA
                    r, c = "hazard", "rose"
                    reason = "HAZARD: heavy skeletal animation and pathfinding node calculations overload CPU MainThread."

        elif key == "characters_quality":
            if is_entry_rig:
                if o_up == "LOW":
                    r, c = "optimum", "emerald"
                    reason = "Minimal polygon and vertex geometry workload for ground personnel."
                elif o_up == "MEDIUM":
                    r, c = "acceptable", "amber"
                    reason = "Balanced polygon fidelity for airport workers within 20m of aircraft."
                elif o_up == "HIGH":
                    r, c = "suboptimal", "orange"
                    reason = "High-poly character models: detailed uniforms and faces with higher vertex buffer allocations."
                else: # ULTRA
                    r, c = "hazard", "rose"
                    reason = "HAZARD: excessive polygon density for personnel viewed from the flight deck."
            else:
                if o_up in ["LOW", "MEDIUM"]:
                    r, c = "optimum", "emerald"
                    reason = "Minimal polygon and vertex geometry workload." if o_up == "LOW" else "Balanced polygon fidelity for airport workers."
                elif o_up == "HIGH":
                    r, c = "acceptable", "amber"
                    reason = "High-poly character models: detailed uniforms and faces with higher vertex buffer allocations."
                else: # ULTRA
                    r, c = "suboptimal", "orange"
                    reason = "Excessive polygon density for personnel viewed from the flight deck."

        elif key == "fauna_density":
            if is_entry_rig:
                if o_up == "OFF":
                    r, c = "optimum", "emerald"
                    reason = "Fauna disabled: zero bird strike or animal spawn queries in CPU background worker threads."
                elif o_up == "LOW":
                    r, c = "acceptable", "amber"
                    reason = "Occasional wildlife: subtle immersion over nature reserves with negligible CPU overhead."
                elif o_up == "MEDIUM":
                    r, c = "suboptimal", "orange"
                    reason = "Standard wildlife: natural animal spawns with light background navigation mesh queries."
                else:
                    r, c = "hazard", "rose"
                    reason = "HAZARD: unneeded animal navigation mesh queries for airliner and IFR flying."
            else:
                if o_up in ["OFF", "LOW"]:
                    r, c = "optimum", "emerald"
                    reason = "Controlled wildlife spawning: zero CPU overhead for airliner operations." if o_up == "OFF" else "Occasional wildlife: subtle immersion over nature reserves with negligible CPU overhead."
                elif o_up == "MEDIUM":
                    r, c = "acceptable", "amber"
                    reason = "Standard wildlife: natural animal spawns with light background navigation mesh queries."
                else:
                    r, c = "suboptimal", "orange"
                    reason = "Dense animal herds: unneeded navigation mesh queries for airliner and IFR flying."

        elif key in ["seatbelt_visibility", "seatbelts"]:
            if o_up in ["OFF", "0"]:
                r, c = "optimum", "emerald"
                reason = "Hidden cockpit seatbelts: frees small cockpit mesh hierarchy and camera collision calculations."
            else:
                r, c = "acceptable", "amber"
                reason = "Visible cockpit harness: aesthetic 3D seatbelts with minimal polygon overhead."

        elif key == "raytraced_shadows":
            if o_up in ["OFF", "0"]:
                r, c = "optimum", "emerald"
                reason = "Rasterized shadow cascades: uses standard depth maps, delivering 15-30% higher framerate."
            else:
                if is_vr:
                    r, c = "hazard", "rose"
                    reason = "HAZARD in VR: BVH ray traversal cripples stereo frame times and introduces severe motion reprojection stutter."
                elif is_flagship_gpu:
                    r, c = "acceptable", "amber"
                    reason = "Hardware RT Shadows: BVH acceleration structure traversal yields photorealistic cockpit shadows on high-tier RTX GPUs."
                else:
                    r, c = "hazard", "rose"
                    reason = "HAZARD: raytracing hardware BVH traversal severely degrades GPU frametimes on mid-tier GPUs."

        entry = {"rating": r, "color": c}
        if reason:
            entry["reason"] = reason
        if tag:
            entry["tag"] = tag
        ratings[opt_str] = entry
    return ratings


def generate_rig_setting_implications(
    key: str,
    val: Any,
    cpu: Dict[str, Any],
    gpu: Dict[str, Any],
    storage: Dict[str, Any],
    disp: Dict[str, Any],
    vr: Dict[str, Any],
    is_liner: bool,
    is_vr: bool
) -> Dict[str, Any]:
    """
    Produces deep, technically sophisticated, hardware-tailored implications for MSFS graphics settings.
    Contextualizes the setting against the user's specific CPU (IPC, 3D V-Cache, hybrid cores),
    GPU (VRAM capacity, Tensor/RT cores, Optical Flow), storage drive (NVMe speed vs mechanical HDD bottlenecks),
    and display cadence / VR headset refresh targets.
    """
    val_str = str(val).strip()
    v_upper = val_str.upper()

    cpu_name = (cpu.get("name_simplified") or cpu.get("name") or "Modern Multi-Core CPU").strip()
    cpu_cores = cpu.get("cores") or 8
    cpu_threads = cpu.get("threads") or 16
    cpu_full = str(cpu.get("name") or "").upper()
    is_x3d = "X3D" in cpu_full or "3D V-CACHE" in cpu_full
    is_flagship_intel = any(k in cpu_full for k in ["13900", "14900", "285K", "13700", "14700", "9950", "7950"])
    is_legacy_cpu = any(k in cpu_full for k in ["8700", "9700", "9900", "10700", "3600", "2600", "1600", "2700", "i5-8", "i5-9", "i5-10", "i7-8", "i7-9"])
    is_intel_hybrid = is_flagship_intel or any(k in cpu_full for k in ["13600", "14600", "12700", "12900"])
    
    gpu_name = (gpu.get("name_simplified") or gpu.get("name") or "Dedicated Graphics Card").strip()
    vram_gb = float(gpu.get("vram_total_gb") or 16.0)
    gpu_full = str(gpu.get("name") or "").upper()
    is_flagship_gpu = any(k in gpu_full for k in ["5090", "5080", "4090", "7900 XTX", "7900XTX"]) or vram_gb >= 20.0
    is_high_tier_gpu = is_flagship_gpu or any(k in gpu_full for k in ["4080", "4070 TI", "4070TI", "4070 SUPER", "3090", "7900 XT", "7900XT", "7900 GRE"]) or vram_gb >= 15.0
    is_mid_tier_gpu = not is_high_tier_gpu and (any(k in gpu_full for k in ["4070", "3080", "6800", "7800", "7700"]) or (vram_gb >= 10.0 and vram_gb < 15.0))
    is_vram_constrained = (vram_gb <= 8.5) and not (vram_gb < 6.5)
    is_entry_gpu = any(k in gpu_full for k in ["1660", "1060", "1070", "1650", "3050", "2060", "6600", "580", "570"]) or (vram_gb < 6.5)
    is_rtx40 = any(k in gpu_full for k in ["4090", "4080", "4070", "4060", "5090", "5080", "5070"])
    is_rtx50 = any(k in gpu_full for k in ["5090", "5080", "5070"])
    
    storage_model = storage.get("model") or "NVMe Solid State Drive"
    storage_tier = storage.get("tier") or "NVMe SSD"
    storage_drive = storage.get("drive_letter") or "C:"
    is_hdd = storage.get("is_hdd", False)
    is_nvme = storage.get("is_nvme", True)
    
    screen_hz = int(disp.get("refresh_rate_int") or 60)
    target_fps = screen_hz // 2 if screen_hz >= 75 else screen_hz
    frame_budget_ms = round(1000.0 / target_fps, 1) if target_fps else 16.6
    
    vr_detected = vr.get("detected", False)
    vr_hz = vr.get("refresh_rate_hz", 72) if vr_detected else 72
    vr_name = vr.get("name", "VR Headset") if vr_detected else "VR Headset"
    vr_target_fps = max(30, vr_hz // 2)
    
    mission_tag = "IFR AIRLINER" if is_liner else "VFR GENERAL AVIATION"
    cadence_desc = f"{vr_target_fps} FPS @ {vr_hz} HZ (VR REPROJECTION)" if is_vr else f"{target_fps} FPS @ {screen_hz} HZ (1/2 SYNC - {frame_budget_ms} MS BUDGET)"

    # Rig tier badge
    elite_badge = ""
    if is_x3d and is_flagship_gpu:
        elite_badge = '<span class="px-2.5 py-0.5 rounded-lg bg-purple-950/80 border border-purple-600 text-purple-300 font-bold uppercase"><i class="fa-solid fa-crown mr-1 text-amber-400"></i>ELITE RIG (X3D + FLAGSHIP)</span>'
    elif is_vram_constrained:
        elite_badge = '<span class="px-2.5 py-0.5 rounded-lg bg-amber-950/80 border border-amber-600 text-amber-300 font-bold uppercase"><i class="fa-solid fa-triangle-exclamation mr-1 text-amber-400"></i>8GB VRAM BOUNDARY</span>'

    # Top badges banner
    storage_badge_color = "bg-rose-950 text-rose-300 border-rose-700 animate-pulse" if is_hdd else ("bg-emerald-950 text-emerald-400 border-emerald-800/80" if is_nvme else "bg-cyan-950 text-cyan-400 border-cyan-800/80")
    badges_html = f"""
    <div class="flex items-center gap-1.5 flex-wrap pb-2.5 border-b border-slate-800 text-[11px] font-mono">
        {elite_badge}
        <span class="px-2.5 py-0.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 font-bold uppercase"><i class="fa-solid fa-microchip mr-1 text-slate-400"></i>CPU: {cpu_name}</span>
        <span class="px-2.5 py-0.5 rounded-lg bg-slate-900 border border-slate-800 text-cyan-300 font-bold uppercase"><i class="fa-solid fa-tv mr-1 text-cyan-400"></i>GPU: {gpu_name} ({vram_gb:.0f} GB)</span>
        <span class="px-2.5 py-0.5 rounded-lg border {storage_badge_color} font-bold uppercase"><i class="fa-solid fa-hard-drive mr-1"></i>DRIVE: {storage_drive} {storage_tier}</span>
        <span class="px-2.5 py-0.5 rounded-lg bg-slate-900 border border-slate-800 text-emerald-300 font-bold uppercase"><i class="fa-solid fa-gauge-high mr-1 text-emerald-400"></i>{cadence_desc}</span>
        <span class="px-2.5 py-0.5 rounded-lg bg-slate-900 border border-slate-800 text-amber-300 font-bold uppercase"><i class="fa-solid fa-plane mr-1 text-amber-400"></i>{mission_tag}</span>
    </div>
    """

    # Storage section HTML
    if is_hdd:
        storage_html = f"""
        <div class="p-3 rounded-xl bg-rose-950/80 border border-rose-600/80 text-rose-200 text-xs leading-relaxed space-y-1">
            <div class="font-bold flex items-center gap-1.5 text-rose-300 uppercase tracking-wide">
                <i class="fa-solid fa-triangle-exclamation text-rose-400 text-sm"></i>
                <span>CRITICAL: MECHANICAL HDD DETECTED ({storage_drive} {storage_model})</span>
            </div>
            <p>MSFS packages are installed on a mechanical hard drive. Mechanical read heads have an inherent seek latency of 12-15ms and transfer rates below 150 MB/s. Background asset streaming for this setting will repeatedly saturate the drive's queue depth, resulting in sudden 1-2 second frame freezes, photogrammetry melting, and terrain pop-in. Moving your MSFS installation to an NVMe or SATA SSD will completely eliminate this critical bottleneck.</p>
        </div>
        """
    elif is_nvme:
        storage_html = f"""
        <div class="text-xs text-slate-300 leading-relaxed">
            <span class="text-emerald-400 font-bold uppercase"><i class="fa-solid fa-bolt mr-1"></i>NVMe Storage Streaming ({storage_tier}):</span> 
            MSFS packages are hosted on your high-speed <strong>{storage_model}</strong> ({storage_drive}). Sub-millisecond random access and multi-gigabyte PCIe bandwidth allow the engine to stream quadtree chunks and mipmaps directly into system memory with zero disk queue delays.
        </div>
        """
    else:
        storage_html = f"""
        <div class="text-xs text-slate-300 leading-relaxed">
            <span class="text-cyan-400 font-bold uppercase"><i class="fa-solid fa-hard-drive mr-1"></i>SATA SSD Streaming ({storage_tier}):</span> 
            Packages on <strong>{storage_model}</strong> ({storage_drive}) provide ~500 MB/s read throughput, delivering smooth asset decompression without mechanical head seek penalties.
        </div>
        """

    pipe_text = ""
    cpu_detail = ""
    gpu_detail = ""
    verdict_text = ""
    cpu_note = ""
    gpu_note = ""

    if key in ["terrain_lod", "tlod"]:
        pipe_text = "Governs the tessellation distance and geometric mesh resolution of the worldwide Digital Elevation Model (DEM). Higher values force the DirectX 12 engine to continuously evaluate, subdivide, and submit exponentially denser terrain geometry into the CPU MainThread render queue."
        if is_x3d:
            cpu_detail = f"Your <strong>{cpu_name}</strong> features a dedicated 96MB 3D V-Cache (Zen 4/5). This ultra-fast cache pool acts as an ideal shock absorber for terrain quadtree bounding volume hierarchy (BVH) lookups, buffering vertex index calls and reducing MainThread cache-miss stalls by over 40% compared to standard architectures."
        elif is_flagship_intel:
            cpu_detail = f"Your <strong>{cpu_name}</strong> utilizes high-IPC Performance-cores (boosting up to 5.6-6.0 GHz). While your background cores decompress terrain data effectively, the DirectX 12 MainThread is bound to a single P-core. Above 140-160 TLOD at complex hub sceneries (e.g. LFPG, EGLL, KJFK), MainThread execution time can exceed your {frame_budget_ms} ms budget, creating micro-hitches during flare and roll-out."
        elif is_legacy_cpu:
            cpu_detail = f"Your <strong>{cpu_name}</strong> is based on legacy IPC and cache structures. In DirectX 12, higher TLOD exponentially increases MainThread draw call submission and memory latency. Setting TLOD above 100 with complex airliners causes severe MainThread frame time spikes (>35ms), producing visible landing freezes."
        else:
            cpu_detail = f"Your {cpu_cores}-core CPU handles terrain dispatch adequately, but higher TLOD exponentially increases MainThread draw call submission. Keep TLOD under 120 to avoid exceeding your {frame_budget_ms} ms frame time ceiling."
        
        if is_flagship_gpu:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM - Flagship Monster): Terrain vertex buffers and heightfield rasterization consume approximately 2.0 to 3.0 GB of video memory. In your massive {vram_gb:.0f} GB pool, this represents negligible overhead with zero risk of saturation."
        elif is_vram_constrained:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM - 8GB Pool): Terrain vertex buffers and heightfield rasterization consume ~2.0 GB of your precious 8 GB pool. Keeping TLOD balanced is vital to prevent competing with high-resolution cockpit and airport textures."
        else:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): Terrain vertex buffers and heightfield rasterization consume approximately 1.8 to 2.8 GB of video memory. With your {vram_gb:.0f} GB pool, there is zero risk of VRAM saturation."

        if is_x3d:
            verdict_text = f"Recommended for your rig in {mission_tag}: <strong>{'150 to 180 (up to 200)' if is_liner else '200 to 250'}</strong>. Your 3D V-Cache guarantees razor-sharp distant horizons while maintaining rock-solid 60+ FPS flaring onto dense payware airports."
            cpu_note = f"On your {cpu_name} (3D V-Cache): Exceptional BVH quadtree resilience. Handles TLOD up to 180-200 with rock-solid frame times."
        elif is_flagship_intel:
            verdict_text = f"Recommended for your rig in {mission_tag}: <strong>{'100 to 120 (up to 140)' if is_liner else '150 to 180'}</strong>. Preserves smooth {cadence_desc} pacing during touchdown flare at major payware hubs."
            cpu_note = f"On your {cpu_name}: Heavy MainThread draw-call dispatch. Handled well, but >140-150 TLOD at large hubs pushes frame time past {frame_budget_ms}ms."
        elif is_legacy_cpu:
            verdict_text = f"Recommended for your rig in {mission_tag}: <strong>80 to 100</strong>. Strictly avoid exceeding 100 to prevent severe CPU MainThread stuttering on final approach."
            cpu_note = f"On your {cpu_name}: Severe MainThread draw call bottleneck. TLOD > 100 causes severe touchdown stutter spikes."
        else:
            verdict_text = f"Recommended for your rig in {mission_tag}: <strong>{'100 to 120' if is_liner else '140 to 160'}</strong>."
            cpu_note = f"On your {cpu_name}: Balanced terrain draw-call dispatch."

        gpu_note = f"On your {gpu_name} ({vram_gb:.0f} GB): Terrain vertex throughput & polygon rasterization. Comfortably fits in your {vram_gb:.0f} GB VRAM pool."

    elif key in ["objects_lod", "olod"]:
        pipe_text = "Controls the render distance and polygon mesh simplification thresholds for 3D scenery models: airport terminals, jetways, hangars, light poles, antennas, and urban autogen buildings."
        if is_x3d:
            cpu_detail = f"Every discrete 3D building and airport model introduces individual draw calls and state changes into the DirectX 12 command stream. Your <strong>{cpu_name}</strong> with 96MB 3D V-Cache buffers these object draw calls with remarkable efficiency, sustaining high object density without the typical landing micro-stutters seen on standard processors."
            verdict_text = f"Recommended: <strong>120 to 160</strong> (up to 180 acceptable). Pristine airport terminal and jetway detail with fluid {cadence_desc} pacing."
            cpu_note = f"On your {cpu_name} (3D V-Cache): 3D airport building draw calls efficiently buffered by L3 cache."
        elif is_legacy_cpu:
            cpu_detail = f"Every discrete 3D building and airport model introduces individual draw calls into the DirectX 12 command stream on your <strong>{cpu_name}</strong>. On legacy architectures, OLOD above 100 heavily saturates the single-core MainThread queue, causing major taxi and rollout stuttering."
            verdict_text = "Recommended: <strong>80 to 100</strong>. Strictly avoid >100 to prevent CPU draw-call queuing at busy airports."
            cpu_note = f"On your {cpu_name}: Major draw-call bottleneck on 3D buildings. Keep OLOD <= 100."
        else:
            cpu_detail = f"Every discrete 3D building and airport model introduces individual draw calls and state changes into the DirectX 12 command stream on your <strong>{cpu_name}</strong>. At dense hubs, OLOD above 150 multiplies active draw calls by over 300%, adding significant queue latency to the CPU MainThread."
            verdict_text = f"Recommended: <strong>100 to 140</strong>. Setting OLOD higher than 150 at major international airports introduces noticeable CPU draw call bottlenecks with virtually zero perceptible visual benefit from the cockpit."
            cpu_note = f"On your {cpu_name}: Multiplies scene draw calls for 3D airport buildings. High OLOD creates MainThread queues during taxi."
        gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB): 3D model polygon rasterization and PBR material evaluation place light-to-moderate compute load on your architecture. Fits easily within your VRAM budget."
        gpu_note = f"On your {gpu_name}: Polygon shading workload. Negligible impact on your {vram_gb:.0f} GB VRAM."

    elif key in ["terrain_texture", "texture_resolution"]:
        pipe_text = "Defines the resolution and mipmap chains of aerial satellite ground orthoimagery loaded into video memory. Direct3D binds these high-resolution aerial tiles onto the terrain heightfield mesh."
        cpu_detail = f"Minimal CPU computation on your <strong>{cpu_name}</strong>. Background worker threads manage disk I/O requests and decompression, leaving the MainThread free to handle flight dynamics and cockpit avionics."
        if is_flagship_gpu or vram_gb >= 20.0:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM - Flagship Tier): Ultra ground textures allocate ~3.5 - 4.5 GB of VRAM. With your massive {vram_gb:.0f} GB buffer, you have over {vram_gb - 5.0:.0f} GB of free headroom! There is zero risk of D3D12 memory pool exhaustion or PCIe bus paging stutters, even when flying complex payware airliners at massive custom airports."
            verdict_text = "Recommended: <strong>ULTRA</strong>. Matches your massive VRAM buffer perfectly with zero performance penalty."
            gpu_note = f"On your {gpu_name} ({vram_gb:.0f} GB): Ultra textures allocate ~4.0 GB VRAM. Zero risk of paging in your {vram_gb:.0f} GB buffer."
        elif is_vram_constrained or is_entry_gpu:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM - Constrained Pool): <strong>Critical VRAM Safety Warning!</strong> Windows D3D12 compositor and MSFS core engine already occupy ~4.0-4.5 GB. Running complex payware airliners (Fenix A320, PMDG 737) with High or Ultra textures forces total VRAM allocation above your physical {vram_gb:.0f} GB limit. When VRAM overflows, D3D12 pages textures into system RAM across the PCIe bus, triggering catastrophic frame drops (5-10 FPS) and severe stuttering."
            verdict_text = f"Recommended: <strong>{'LOW' if is_liner else 'MEDIUM'}</strong>. Essential safeguard to prevent VRAM overflow and paging stutters on your 8 GB card."
            gpu_note = f"On your {gpu_name} ({vram_gb:.0f} GB): 8GB VRAM boundary! Low textures required for airliners to prevent PCIe paging crash."
        elif is_high_tier_gpu:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): Ultra ground textures allocate ~3.5 - 4.5 GB of VRAM. With your {vram_gb:.0f} GB buffer, you have ample headroom. For complex payware airliners at huge international hubs, Medium or High provides a bulletproof buffer against rare VRAM spikes."
            verdict_text = f"Recommended: <strong>{'HIGH (or MEDIUM)' if is_liner else 'ULTRA'}</strong>. Matches your available {vram_gb:.0f} GB memory pool perfectly."
            gpu_note = f"On your {gpu_name} ({vram_gb:.0f} GB): Allocates ~3.5 GB VRAM. Comfortably fits in your {vram_gb:.0f} GB buffer with high safety margin."
        else:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): Ultra ground textures require substantial VRAM. With {vram_gb:.0f} GB available, High or Medium is strongly recommended when flying detailed add-on airliners to prevent VRAM overflow and paging stutters."
            verdict_text = f"Recommended: <strong>{'MEDIUM' if is_liner else 'HIGH'}</strong>."
            gpu_note = f"On your {gpu_name} ({vram_gb:.0f} GB): Allocates ~3.0 GB VRAM."
        cpu_note = f"On your {cpu_name}: Minimal CPU draw call cost; background threads manage streaming."

    elif key == "volumetric_clouds":
        pipe_text = "Raymarches through 3D density voxel fields to simulate realistic cloud formations, light scattering, multiple phase functions, and atmospheric transmittance in real time."
        cpu_detail = f"Negligible computational load on your <strong>{cpu_name}</strong>. Cloud field positions and weather transitions are passed directly to GPU compute shaders."
        if is_vr:
            gpu_detail = f"On your <strong>{gpu_name}</strong> (VR Stereo): Volumetric raymarching is rendered per eye. Ultra (16 samples) overtaxes stereo frame times, triggering severe reprojection judder in overcast skies. Medium (8 samples) preserves stereo fill rate and maintains steady frame pacing."
            verdict_text = "Recommended in VR: <strong>MEDIUM</strong> to protect stereo fill rate and maintain steady frame pacing during overcast weather."
            gpu_note = f"On your {gpu_name} (VR): 8-sample raymarching preserves stereo fill rate (~3-4/12 load)."
        elif is_flagship_gpu:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM - Flagship Monster): Massive compute array powers through volumetric raymarching effortlessly (~1.8ms GPU frame time). High provides 12-sample raymarching with 15-20% faster frame times than Ultra for virtually identical fidelity."
            verdict_text = "Recommended: <strong>HIGH</strong>. Near-identical photorealism to Ultra (+15% FPS) with rock-solid framerate margin in storms."
            gpu_note = f"On your {gpu_name}: 12-sample volumetric raymarching smoothly handled (~4/12 load)."
        elif is_vram_constrained or is_entry_gpu:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): High arithmetic shader and texture filtering workload. Inside thick thunderstorm cells, Ultra clouds can cause GPU frame time to increase noticeably (~8-10ms), causing frame drops."
            verdict_text = "Recommended: <strong>HIGH or MEDIUM</strong> to maintain smooth framerates in heavy overcast weather."
            gpu_note = f"On your {gpu_name}: High shader load in dense clouds (~8-11/12 load). High or Medium recommended."
        else:
            gpu_detail = f"On your <strong>{gpu_name}</strong>: The advanced compute architecture handles volumetric raymarching smoothly (~2.5ms GPU frame time). High provides optimal boundary scattering with 15-20% headroom over Ultra."
            verdict_text = "Recommended: <strong>HIGH</strong>. Near-identical photorealism to Ultra with stable frame delivery."
            gpu_note = f"On your {gpu_name}: Volumetric raymarching (~5-6/12 load)."
        cpu_note = f"On your {cpu_name}: Zero compute overhead; cloud simulation is offloaded entirely to GPU shaders."

    elif key in ["glass_cockpit_refresh", "glass_cockpits"]:
        pipe_text = "Dictates how frequently HTML5, JavaScript, SVG, and WebAssembly avionics displays (PFD, ND, EICAS, FMC, MFD) are re-rendered and updated via Coherent GT."
        if is_x3d:
            cpu_detail = f"Your <strong>{cpu_name}</strong> features 96MB of ultra-fast 3D V-Cache. Unlike standard CPUs that suffer severe cache-miss latency during Coherent GT HTML/JS vector avionics redraws, your X3D cache effortlessly buffers electronic flight instrument loops. On High (Full), redraws run every frame with minimal stutter, while Medium (Half) gives you maximum MainThread headroom."
            verdict_text = "Recommended: <strong>MEDIUM (HALF) or HIGH (FULL)</strong>. Your 3D V-Cache handles avionics redraws with exceptional fluidity."
            cpu_note = f"On your {cpu_name} (3D V-Cache): 96MB L3 cache buffers Coherent GT DOM updates and avionics redraws."
        elif is_legacy_cpu:
            cpu_detail = f"<strong>Major CPU MainThread bottleneck!</strong> On your <strong>{cpu_name}</strong>, setting Glass Cockpits to High forces full HTML/JS redraws on every single frame, adding 6 to 10ms of continuous MainThread overhead. This directly causes severe frame dips during landing flare."
            verdict_text = "Recommended: <strong>LOW (QUARTER) or MEDIUM (HALF)</strong>. Mandatory setting to prevent CPU MainThread starvation on legacy processors."
            cpu_note = f"On your {cpu_name} (Legacy CPU): High avionics refresh severely saturates the MainThread. Low or Medium is mandatory."
        else:
            cpu_detail = f"<strong>Critical CPU MainThread setting!</strong> In complex airliners with 5-6 active MFDs (Fenix A320, PMDG 737, FlyByWire A32NX), High (Full) creates 4 to 8ms of continuous CPU MainThread overhead on your <strong>{cpu_name}</strong>. Setting Medium (Half) throttles avionics refresh to alternate frames, saving ~4ms of frame budget with zero perceived loss of needle smoothness."
            verdict_text = "Recommended: <strong>MEDIUM (HALF)</strong>. This is the single most effective setting to unlock 4-6ms of CPU MainThread headroom when flying modern glass-cockpit airliners."
            cpu_note = f"On your {cpu_name}: Critical CPU MainThread impact. High forces Coherent GT avionics loops every frame, risking frame drops."
        gpu_detail = f"Minimal GPU impact on your <strong>{gpu_name}</strong>. The 2D instrument canvas textures are simply blitted onto the 3D cockpit model material."
        gpu_note = f"On your {gpu_name}: Lightweight 2D canvas texture composition into 3D cockpit mesh."

    elif key == "anti_aliasing":
        pipe_text = "DirectX 12 anti-aliasing and image reconstruction pipeline. Determines whether MSFS shades geometry at native monitor resolution (TAA / DLAA) or downscales internal rendering and reconstructs the image using NVIDIA Tensor Core neural networks (DLSS Super Resolution)."
        cpu_detail = f"On your <strong>{cpu_name}</strong>: DLSS slightly reduces internal render target resolution, cutting command list processing overhead. DLAA and TAA operate at native resolution, submitting standard DirectX 12 draw lists to the GPU queue."
        cpu_note = f"On your {cpu_name}: Minimal CPU draw-call cost; DLSS slightly reduces driver queue overhead."
        
        if is_vr:
            if "QUALITY" in v_upper:
                gpu_detail = f"In VR stereo on your <strong>{gpu_name}</strong>: Currently set to <strong>DLSS Quality</strong>. Renders internally at 67% resolution and uses Tensor Cores to reconstruct a crisp stereo image. Reduces stereo shader load by ~30%, preserving vital headset reprojection headroom."
                gpu_note = f"On your {gpu_name}: 67% internal stereo render + Tensor AI reconstruction. Essential VR performance margin."
            elif "BALANCED" in v_upper:
                gpu_detail = f"In VR stereo on your <strong>{gpu_name}</strong>: Currently set to <strong>DLSS Balanced</strong>. Renders internally at 58% resolution. Recommended for high-resolution VR headsets to prevent frame drops in dense weather."
                gpu_note = f"On your {gpu_name}: 58% internal stereo render. High performance headroom in VR headset."
            elif "PERFORMANCE" in v_upper:
                gpu_detail = f"In VR stereo on your <strong>{gpu_name}</strong>: Currently set to <strong>DLSS Performance</strong>. Aggressive 50% downscaling. Significantly boosts stereo framerate, but gauge needles and small numbers in cockpit appear noticeably softer."
                gpu_note = f"On your {gpu_name}: 50% internal downscale. Maximizes VR framerate at the cost of gauge clarity."
            elif "DLAA" in v_upper:
                gpu_detail = f"In VR stereo on your <strong>{gpu_name}</strong>: Currently set to <strong>DLAA</strong>. Full native stereo AI anti-aliasing. Unmatched cockpit clarity, but doubles stereo rasterization cost and risks reprojection drops in VR."
                gpu_note = f"On your {gpu_name}: Native stereo DLAA. Very high fill-rate load across dual headset displays."
            else:
                gpu_detail = f"In VR stereo on your <strong>{gpu_name}</strong>: Currently set to <strong>TAA</strong>. Standard native stereo rasterization. Heavy fill-rate workload across both headset eye panels."
                gpu_note = f"On your {gpu_name}: Native stereo TAA rasterization. Standard high stereo fill-rate load."
            verdict_text = "Recommended for VR: <strong>DLSS QUALITY or DLSS BALANCED</strong> to maximize stereo frame pacing and prevent headset reprojection stutters."
        else: # 2D mode
            if is_flagship_gpu:
                if "DLAA" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM - Flagship Tier): Currently running <strong>DLAA at 100% native resolution ({disp.get('width', 2560)}x{disp.get('height', 1440)})</strong>. 4th/5th-Gen Tensor Cores apply AI temporal reconstruction without downscaling, completely eliminating wire/fence shimmering and jagged runway lines. Digital EFIS, MCDU, and PFD avionics readouts remain impeccably sharp. Your {gpu_name} has massive compute headroom to sustain DLAA with zero framerate loss."
                    gpu_note = f"On your {gpu_name}: AI edge reconstruction at native resolution. Pristine cockpit clarity with massive GPU margin."
                elif "QUALITY" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): Currently running <strong>DLSS Quality</strong>. Renders internally at 67% resolution and uses Tensor Cores to reconstruct a crisp native image. Frees 25-35% GPU shading frame time. On this flagship GPU, you can comfortably switch to DLAA for even sharper digital avionics."
                    gpu_note = f"On your {gpu_name}: 67% internal render with Tensor reconstruction. Low GPU load; DLAA is easily affordable."
                elif "BALANCED" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently running <strong>DLSS Balanced</strong>. Renders internally at 58% resolution. While it saves extra GPU compute, it slightly softens small cockpit typography without yielding measurable FPS gains on your powerful {gpu_name}."
                    gpu_note = f"On your {gpu_name}: 58% internal render. Minor font softening for unneeded GPU relief."
                elif "PERFORMANCE" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently running <strong>DLSS Performance</strong>. Downscales internal rendering to 50%. This is an unnecessary visual sacrifice on your {gpu_name}: it causes noticeable blurring and ghosting on digital flight instruments while offering zero real FPS improvement because your simulator is paced by the CPU."
                    gpu_note = f"On your {gpu_name}: 50% internal downscale (720p). Blurs cockpit screens without improving FPS."
                else: # TAA
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently running <strong>TAA (Temporal Anti-Aliasing)</strong>. Native raster reconstruction with no AI upscaling. Delivers faithful native sharpness, but exhibits slight temporal crawl on runway fences and fine powerlines compared to DLAA."
                    gpu_note = f"On your {gpu_name}: Standard native raster TAA. Full pixel shading workload."
                verdict_text = f"Recommended for your {gpu_name}: <strong>DLAA</strong> for absolute peak glass cockpit instrument clarity (zero blur), or <strong>DLSS QUALITY</strong> if flying at 4K in extreme thunderstorms."
            elif is_vram_constrained or is_entry_gpu:
                if "DLAA" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): Currently running <strong>DLAA</strong>. While DLAA offers sharp cockpit edges, native resolution shading and Tensor passes put heavy pressure on your {vram_gb:.0f} GB memory buffer and memory bus, increasing GPU frame times."
                    gpu_note = f"On your {gpu_name}: Native DLAA on constrained memory bus puts heavy pressure on your {vram_gb:.0f} GB VRAM pool."
                elif "QUALITY" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): Currently running <strong>DLSS Quality</strong>. Renders internally at 67% resolution and reconstructs via Tensor Cores. Frees 30-35% GPU shading time and significantly reduces VRAM framebuffer allocation, providing vital headroom on your {vram_gb:.0f} GB card."
                    gpu_note = f"On your {gpu_name}: 67% internal render with Tensor reconstruction. Vital GPU relief and VRAM savings."
                elif "BALANCED" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently running <strong>DLSS Balanced</strong>. Renders internally at 58% resolution. Provides strong framerate relief on your {gpu_name} with acceptable instrument readability."
                    gpu_note = f"On your {gpu_name}: 58% internal render. Strong framerate relief."
                elif "PERFORMANCE" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently running <strong>DLSS Performance</strong>. Downscales internal rendering to 50%. Maximizes framerate and minimizes VRAM usage on entry hardware, at the cost of softening small cockpit fonts."
                    gpu_note = f"On your {gpu_name}: 50% internal downscale. Maximizes framerate on entry hardware."
                else: # TAA
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently running <strong>TAA</strong>. Full native raster shading places heavy demands on your GPU compute units and memory bandwidth."
                    gpu_note = f"On your {gpu_name}: Native raster TAA. Full pixel shading workload on constrained GPU."
                verdict_text = f"Recommended for your {gpu_name}: <strong>DLSS QUALITY</strong> (or <strong>DLSS BALANCED</strong>). Crucial setting to relieve your {vram_gb:.0f} GB VRAM pool and guarantee smooth 50-60 FPS flight."
            else: # Tier 2/3 (RTX 4080, 4070, 3080)
                if "DLAA" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): Currently running <strong>DLAA at 100% native resolution ({disp.get('width', 2560)}x{disp.get('height', 1440)})</strong>. 4th-Gen Tensor Cores apply AI temporal reconstruction without downscaling, completely eliminating wire/fence shimmering and jagged runway lines. Digital EFIS, MCDU, and PFD avionics readouts remain impeccably sharp. Your {gpu_name} has high headroom to sustain DLAA with zero framerate loss."
                    gpu_note = f"On your {gpu_name}: AI edge reconstruction at native 1440p. Pristine cockpit clarity with high GPU margin (~5/12 load)."
                elif "QUALITY" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): Currently running <strong>DLSS Quality</strong>. Renders internally at 67% resolution and uses Tensor Cores to reconstruct a crisp native image. Frees 25-35% GPU shading frame time (~3.5 ms), providing an immense safety cushion during severe storm approaches with thick volumetric cloud layers."
                    gpu_note = f"On your {gpu_name}: 67% internal render with Tensor reconstruction. Saves 25-35% GPU frame time (~3/12 load)."
                elif "BALANCED" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently running <strong>DLSS Balanced</strong>. Renders internally at 58% resolution. While it saves extra GPU compute, it slightly softens small cockpit typography and runway threshold numbers."
                    gpu_note = f"On your {gpu_name}: 58% internal render. Minor font softening (~2/12 load)."
                elif "PERFORMANCE" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently running <strong>DLSS Performance</strong>. Downscales internal rendering to 50%. This is an unnecessary visual sacrifice on your {gpu_name}: it causes noticeable blurring and ghosting on digital flight instruments."
                    gpu_note = f"On your {gpu_name}: 50% internal downscale (720p). Blurs cockpit screens (~2/12 load)."
                else: # TAA
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently running <strong>TAA (Temporal Anti-Aliasing)</strong>. Native raster reconstruction with no AI upscaling. Delivers faithful native sharpness, but exhibits slight temporal crawl on runway fences."
                    gpu_note = f"On your {gpu_name}: Standard native raster TAA. Full pixel shading workload (~6/12 load)."
                verdict_text = f"Recommended for your {gpu_name}: <strong>DLAA</strong> at 1440p for absolute peak glass cockpit instrument clarity, or <strong>DLSS QUALITY</strong> at 4K / heavy thunderstorms."

    elif key == "frame_generation":
        pipe_text = "Uses NVIDIA Ada Lovelace / Blackwell Optical Flow Accelerator (OFA) hardware to analyze motion vectors across consecutive rendered frames and generate an intermediate AI-synthesized frame."
        if is_rtx40 or is_rtx50:
            cpu_detail = f"<strong>Pure CPU Headroom Miracle:</strong> On your <strong>{cpu_name}</strong>, Frame Generation inserts synthesized frames with <strong>ZERO extra computational workload on the CPU MainThread</strong>! This literally doubles your visual framerate in scenarios where your CPU is heavily loaded by complex airliner systems and dense airport scenery."
            gpu_detail = f"On your <strong>{gpu_name}</strong>: Handled directly by dedicated Optical Flow hardware. Adds slight frame latency (~10ms), which is effectively counterbalanced by NVIDIA Reflex."
        else:
            cpu_detail = f"On your {cpu_name}: Handled via software or driver interpolation."
            gpu_detail = f"On your {gpu_name}: Interpolation pass on GPU execution units."
        verdict_text = f"Recommended: <strong>{'ON for 2D Flight (OFF for VR)' if not is_vr else 'OFF in VR (Use OpenXR Reprojection)'}</strong>."
        cpu_note = f"On your {cpu_name}: ZERO MainThread penalty. Frames are synthesized independently on the GPU Optical Flow Accelerator."
        gpu_note = f"On your {gpu_name}: Optical Flow Accelerator compute pass. Doubles motion framerate with ~10ms latency mitigated by Reflex."

    elif key == "max_frame_rate":
        pipe_text = "Imposes a hard presentation limit on the DirectX 12 swapchain, governing the exact intervals at which rendered frames are delivered to the display."
        cpu_detail = f"Essential governor for your <strong>{cpu_name}</strong> MainThread. An uncapped framerate produces erratic frame interval spikes (e.g. 11ms then 19ms), causing visual judder. Capping to an exact divisor of your monitor ({target_fps} FPS on {screen_hz} Hz) enforces a strict {frame_budget_ms} ms frame time ceiling, completely eliminating micro-stutters."
        gpu_detail = f"On your <strong>{gpu_name}</strong>: Prevents GPU thermal saturation and eliminates erratic frame buffer queues."
        verdict_text = f"Recommended: <strong>{target_fps} FPS</strong> (exact 1/2 sync of your {screen_hz} Hz monitor). Guarantees silky-smooth, judder-free motion cadence."
        cpu_note = f"On your {cpu_name}: Crucial governor for MainThread pacing. Eliminates micro-stutter spikes by locking frame intervals."
        gpu_note = f"On your {gpu_name}: Prevents GPU thermal saturation and eliminates erratic frame queue backlog."

    elif key in ["vsync", "vsync_interval", "reflex"]:
        pipe_text = "Coordinates frame buffer presentation with physical display vertical refresh cycles (V-Sync) and trims the driver render queue to reduce system latency (NVIDIA Reflex)."
        cpu_detail = f"On your <strong>{cpu_name}</strong>: Reflex prevents the CPU render queue from getting backlogged behind the GPU, maintaining instantaneous yoke and flight control response."
        gpu_detail = f"On your <strong>{gpu_name}</strong>: Eliminates horizontal screen tearing without introducing frame buffer latency."
        verdict_text = "Recommended: <strong>V-SYNC FAST / ON + REFLEX ON</strong> for tear-free, responsive flight control."
        cpu_note = f"On your {cpu_name}: Optimizes CPU render queue dispatch and prevents frame buffer queuing."
        gpu_note = f"On your {gpu_name}: Regulates swapchain presentation and reduces system latency via NVIDIA Reflex."

    elif key in ["offscreen_terrain_pre_caching", "offscreen_precaching", "terrain_detail"]:
        pipe_text = "Determines whether terrain geometry and orthoimagery outside the active camera field-of-view are cached in system RAM and VRAM during flight."
        cpu_detail = f"On your <strong>{cpu_name}</strong>: On Low or Medium, every camera pan requires worker threads to decompress offscreen geometry on the fly, creating sudden frame time hitches. On High or Ultra, models remain resident in memory."
        if vram_gb >= 16.0:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): Ultra pre-caching allocates an extra ~1.5 - 2.5 GB of VRAM. With your {vram_gb:.0f} GB buffer and abundant system RAM, Ultra eliminates all camera-pan stutters completely."
        else:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): Caching offscreen terrain consumes memory that may be needed for payware airliner cockpits. High or Medium is recommended."
        verdict_text = f"Recommended: <strong>{'ULTRA' if vram_gb >= 16.0 else 'HIGH'}</strong>. Eliminates cockpit head-panning and external camera stutters."
        cpu_note = f"On your {cpu_name}: Reduces camera-turn MainThread hitches by preserving geometry in memory."
        gpu_note = f"On your {gpu_name} ({vram_gb:.0f} GB): Allocates ~2.0 GB VRAM cache for offscreen terrain."

    elif key in ["shadow_maps", "terrain_shadows", "contact_shadows"]:
        pipe_text = "Cascaded Shadow Maps (CSM) require multiple depth buffer passes from the sun's angle to compute crisp real-time dynamic shadows across the aircraft exterior and cockpit."
        cpu_detail = f"Each shadow cascade triggers an additional frustum culling pass on your <strong>{cpu_name}</strong> MainThread. Ultra shadow maps (2048) increase draw calls moderately."
        gpu_detail = f"On your <strong>{gpu_name}</strong>: Depth buffer rasterization and percentage-closer filtering (PCF). Moderate VRAM footprint."
        verdict_text = "Recommended: <strong>1536 (HIGH) or 2048 (ULTRA)</strong>. Delivers sharp cockpit shadows without degrading frame delivery."
        cpu_note = f"On your {cpu_name}: Generates frustum culling passes per shadow cascade. High settings increase draw calls."
        gpu_note = f"On your {gpu_name}: Depth buffer rasterization and filtering passes. Modest impact on your {vram_gb:.0f} GB VRAM."

    elif key in ["ambient_occlusion", "raytracing", "raytraced_shadows"]:
        pipe_text = "Evaluates ambient contact shadows and indirect lighting via Screen Space Ambient Occlusion (SSAO/GTAO) or hardware DirectX Raytracing (DXR)."
        cpu_detail = f"On your <strong>{cpu_name}</strong>: Ray Tracing requires rebuilding Bounding Volume Hierarchy (BVH) acceleration structures on the CPU every frame, increasing MainThread frame times at complex airports."
        gpu_detail = f"On your <strong>{gpu_name}</strong>: Dedicated hardware RT Cores accelerate ray-triangle intersection tests. Ambient Occlusion uses lightweight compute shaders."
        verdict_text = "Recommended: <strong>HIGH for Ambient Occlusion</strong>; <strong>OFF for Ray Tracing</strong> in complex airliner operations to preserve CPU MainThread headroom."
        cpu_note = f"On your {cpu_name}: Manages BVH acceleration structures on CPU. Ray Tracing adds MainThread overhead."
        gpu_note = f"On your {gpu_name}: Ray-triangle intersection tests on RT Cores. High shader compute workload."

    elif key in ["aircraft_traffic_quantity", "parked_aircraft_quantity", "airport_services_quantity"]:
        pipe_text = "Simulates in-game AI aircraft, flight plans, ATC communications, gate parking, and ground support service vehicles."
        cpu_detail = f"<strong>Major CPU MainThread workload!</strong> Spawning dense in-game traffic forces your <strong>{cpu_name}</strong> to continuously calculate AI navigation, flight dynamics, and collision meshes. If you utilize dedicated traffic add-ons (FSLTL, BATC, SayIntentions), keep in-sim traffic strictly OFF to avoid severe double-spawning and stuttering."
        gpu_detail = f"On your <strong>{gpu_name}</strong>: Each spawned aircraft loads 3D exterior models and multiple liveries into VRAM."
        verdict_text = "Recommended: <strong>OFF or LOW</strong> if using third-party traffic add-ons (FSLTL, BATC); <strong>MEDIUM</strong> for native live traffic."
        cpu_note = f"On your {cpu_name}: Heavy CPU simulation burden (ATC, physics, pathfinding). Major MainThread bottleneck."
        gpu_note = f"On your {gpu_name}: Multiplies exterior aircraft models and livery textures resident in VRAM."

    elif key in ["aircraft_traffic_variety", "parked_aircraft_variety", "airport_services_variety"]:
        pipe_text = "Controls the number of distinct 3D aircraft models, GSE equipment, and unique airline livery textures kept simultaneously in VRAM."
        cpu_detail = f"On your <strong>{cpu_name}</strong>: Light background catalog lookups. Does not add MainThread physics overhead."
        if is_flagship_gpu:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): High or Ultra variety caches multiple 4K liveries effortlessly within your massive {vram_gb:.0f} GB memory pool without risk of paging."
            verdict_text = "Recommended: <strong>HIGH (or MEDIUM)</strong> for rich apron variety."
        elif is_vram_constrained:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): <strong>VRAM Warning!</strong> High or Ultra variety keeps dozens of 4K liveries simultaneously in video memory, easily exceeding 8 GB and causing severe PCIe paging stutters."
            verdict_text = "Recommended: <strong>LOW or MEDIUM</strong>. Essential to protect your 8 GB VRAM pool."
        else:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): Medium variety provides realistic airline diversity while keeping a safe 2-3 GB VRAM safety buffer for payware airliners."
            verdict_text = "Recommended: <strong>MEDIUM (or LOW)</strong> for safe VRAM headroom."
        cpu_note = f"On your {cpu_name}: Minimal CPU logic for model diversity."
        gpu_note = f"On your {gpu_name}: Manages livery texture memory footprint in your {vram_gb:.0f} GB VRAM."

    elif key in ["buildings", "vector_data_buildings"]:
        pipe_text = "Blackshark AI procedural 3D building footprint extrusion, roof geometry, and facade texture atlases evaluated across global land-class grids (distinct from handcrafted airport terminal models)."
        cpu_detail = f"On your <strong>{cpu_name}</strong>: Evaluates spatial quadtree queries and submits instanced building draw calls. High/Ultra increases draw calls over dense metropolitan areas (e.g. London, New York)."
        if is_vr:
            gpu_detail = f"On your <strong>{gpu_name}</strong> in VR: Autogen building geometry and facade textures must be rasterized twice per frame in stereo. High/Ultra increases vertex overhead and texture memory streaming against tight reprojection budgets."
            verdict_text = "Recommended in VR: <strong>MEDIUM</strong>. Protects stereo frame pacing, eliminates draw-call spikes, and preserves critical VRAM for smooth head tracking."
            cpu_note = f"On your {cpu_name}: Autogen building spatial queries and draw-call dispatch."
            gpu_note = f"On your {gpu_name}: Lightweight building geometry protects VR stereo reprojection and frees VRAM."
        else:
            gpu_detail = f"On your <strong>{gpu_name}</strong>: High provides standard extrusion and 2K facade atlases with ~25% lower draw calls than Ultra and stable VRAM headroom, eliminating city stutters above 500ft."
            verdict_text = "Recommended: <strong>HIGH</strong>. Crisp urban autogen and controlled draw calls across major metropolitan centers."
            cpu_note = f"On your {cpu_name}: Autogen building spatial queries and draw-call dispatch."
            gpu_note = f"On your {gpu_name} ({vram_gb:.0f} GB): Building geometry and texture streaming."

    elif key == "trees":
        pipe_text = "Procedural 3D foliage density, canopy branch modeling, and self-shadowing across forests and suburban woodlots."
        cpu_detail = f"On your <strong>{cpu_name}</strong>: Generates instanced tree coordinate buffers across terrain tiles with minimal MainThread impact."
        if is_vr:
            gpu_detail = f"On your <strong>{gpu_name}</strong> in VR: Dense forest canopies require heavy alpha-tested quad rasterization rendered independently per eye. High/Ultra can degrade stereo frametime over continuous forest approaches."
            verdict_text = "Recommended in VR: <strong>MEDIUM</strong> to relieve stereo foliage fill rate and secure locked reprojection."
            cpu_note = f"On your {cpu_name}: Instanced foliage positioning."
            gpu_note = f"On your {gpu_name}: Balanced tree canopy preserves stereo fill rate in VR."
        else:
            gpu_detail = f"On your <strong>{gpu_name}</strong>: High provides dense 3D tree canopies with optimized LOD falloff; realistic forests with negligible GPU/CPU overhead."
            verdict_text = "Recommended: <strong>HIGH</strong>. Dense 3D canopies with minimal FPS impact."
            cpu_note = f"On your {cpu_name}: Instanced tree coordinate buffers."
            gpu_note = f"On your {gpu_name}: Foliage rasterization and self-shadowing."

    elif key == "grass":
        pipe_text = "Procedural 3D ground vegetation blades, wild meadow flowers, and airfield perimeter shrubs."
        if is_vr:
            cpu_detail = f"On your <strong>{cpu_name}</strong>: Procedural meadow vegetation geometry dispatch."
            gpu_detail = f"On your <strong>{gpu_name}</strong> in VR: Grass blades require dual-eye transparent alpha passes. High/Ultra grass induces severe reprojection judder during landing flare."
            verdict_text = "Recommended in VR: <strong>LOW</strong>. Eliminates stereo alpha overdraw and prevents headset reprojection judder on airport taxiways."
            cpu_note = f"On your {cpu_name}: Low grass saves critical draw calls on airfield perimeters."
            gpu_note = f"On your {gpu_name}: Saves critical stereo alpha fill rate in VR."
        elif is_liner:
            cpu_detail = f"On your <strong>{cpu_name}</strong>: On paved commercial runways, High/Ultra generates millions of redundant 3D vegetation triangles completely invisible from an airliner flight deck, wasting valuable CPU draw calls during landing flare."
            gpu_detail = f"On your <strong>{gpu_name}</strong>: Low eliminates unnecessary ground-level alpha overdraw on concrete aprons and runways."
            verdict_text = "Recommended for Airliners: <strong>LOW</strong>. Eliminates millions of useless draw calls on paved runways, preserving critical landing flare framerates."
            cpu_note = f"On your {cpu_name}: Saves millions of useless draw calls on concrete runways."
            gpu_note = f"On your {gpu_name}: Eliminates ground-level alpha overdraw during landing."
        else:
            cpu_detail = f"On your <strong>{cpu_name}</strong>: Procedural meadow vegetation geometry."
            gpu_detail = f"On your <strong>{gpu_name}</strong>: 3D grass blades and turf for unpaved grass runways and backcountry strips."
            verdict_text = "Recommended for GA: <strong>HIGH</strong> for immersive grass airstrips and backcountry strips."
            cpu_note = f"On your {cpu_name}: Procedural ground vegetation geometry."
            gpu_note = f"On your {gpu_name}: 3D grass and flower rasterization."

    elif key == "displacement_mapping":
        pipe_text = "Surface heightfield tessellation generating micro-relief on concrete expansion joints, tarmac cracks, and ground terrain."
        cpu_detail = f"On your <strong>{cpu_name}</strong>: Coordinates geometry tessellation stages."
        gpu_detail = f"On your <strong>{gpu_name}</strong>: Tessellation compute passes consume geometry shader stages and VRAM bandwidth for micro-relief that is completely invisible from normal flight deck eye heights."
        verdict_text = "Recommended: strictly <strong>OFF</strong>. Saves geometry shader stages and VRAM bandwidth with zero visual loss. In VR, keeping this ON introduces severe frame pacing hitches."
        cpu_note = f"On your {cpu_name}: Surface tessellation disabled."
        gpu_note = f"On your {gpu_name}: Disabling displacement mapping conserves geometry shader throughput and VRAM."

    elif key == "water_waves":
        pipe_text = "Computes Fast Fourier Transform (FFT) grid displacement for ocean, lake, and river wave dynamics with screen-space Fresnel reflection shaders."
        cpu_detail = f"On your <strong>{cpu_name}</strong>: Dispatches water simulation tasks to worker threads with virtually zero impact on the MainThread flight loop."
        if is_vr:
            gpu_detail = f"On your <strong>{gpu_name}</strong> in VR: Medium (256) FFT wave simulation provides clean ocean swell patterns while conserving compute shader throughput for stereo presentation."
            verdict_text = "Recommended in VR: <strong>MEDIUM (256)</strong>. Preserves stereo compute shader budget in VR without noticeable loss in open-water swell animation."
            cpu_note = f"On your {cpu_name}: Water FFT simulation dispatch."
            gpu_note = f"On your {gpu_name}: Lightweight FFT wave grid preserves stereo frame budget in VR."
        else:
            gpu_detail = f"On your <strong>{gpu_name}</strong>: High (512) FFT wave simulation delivers realistic wave swells and shoreline ripples with negligible compute overhead."
            verdict_text = "Recommended: <strong>HIGH (512)</strong>. Outstanding maritime realism without GPU compute penalty."
            cpu_note = f"On your {cpu_name}: Wave displacement simulation dispatch. Negligible impact on your CPU."
            gpu_note = f"On your {gpu_name}: 512x512 FFT wave simulation with negligible compute overhead."

    elif key in ["windshield_effects", "particles"]:
        pipe_text = "Simulates procedural rain droplet physics, condensation, engine contrails, smoke plumes, and touchdown tire smoke."
        cpu_detail = f"Lightweight emitter dispatch on your <strong>{cpu_name}</strong>."
        gpu_detail = f"On your <strong>{gpu_name}</strong>: High particle density inside heavy clouds or tire smoke can cause brief transparent alpha overdraw fill-rate load, easily sustained by your GPU."
        verdict_text = "Recommended: <strong>HIGH / ULTRA</strong> for immersive weather and landing smoke effects."
        cpu_note = f"On your {cpu_name}: Particle emitter and droplet physics dispatch."
        gpu_note = f"On your {gpu_name}: Transparent alpha fill-rate and refraction shader passes."

    elif key in ["texture_supersampling", "anisotropic_filtering"]:
        pipe_text = "Controls texture sampling quality at oblique viewing angles and screen-space texture filter tap counts (up to 16x)."
        cpu_detail = f"Zero CPU compute on your <strong>{cpu_name}</strong>."
        gpu_detail = f"On your <strong>{gpu_name}</strong>: High-speed texture sampler units on your GPU execute 16x anisotropic lookups with less than 0.5% performance cost."
        verdict_text = "Recommended: <strong>16X ANISOTROPIC / 4x4 SUPERSAMPLING</strong>. Keeps runway centerlines and taxiway markings crisp and readable."
        cpu_note = f"On your {cpu_name}: Zero CPU compute; handled entirely by GPU texture samplers."
        gpu_note = f"On your {gpu_name}: Texture sampler unit filtering. Negligible performance cost on modern GPUs."

    elif key in ["dynamic_settings"]:
        pipe_text = "Dynamically downscales internal render resolution in real time when the GPU encounters heavy scenes to sustain a target framerate."
        cpu_detail = f"On your <strong>{cpu_name}</strong>: Minimal CPU impact, but can introduce visual confusion when diagnosing MainThread vs GPU limits."
        gpu_detail = f"On your <strong>{gpu_name}</strong>: Dynamically modulates render resolution, causing cockpit digital avionics and runway numbers to blur unpredictably."
        verdict_text = "Recommended: <strong>OFF</strong>. Keeping resolution fixed ensures cockpit instruments and HUD elements remain permanently sharp."
        cpu_note = f"On your {cpu_name}: Dynamic governor; does not resolve CPU MainThread bottlenecks."
        gpu_note = f"On your {gpu_name}: Modulates render resolution; can cause blurry cockpit avionics."

    elif key in ["vr_reprojection"]:
        pipe_text = "Asynchronous SpaceWarp / Motion Reprojection in OpenXR compositor. Synthesizes alternate frames based on headset gyroscope and depth buffer to ensure fluid head tracking."
        cpu_detail = f"On your <strong>{cpu_name}</strong>: Paces render loop to match {vr_target_fps} FPS reprojection target, relieving MainThread pressure."
        gpu_detail = f"On your <strong>{gpu_name}</strong>: OpenXR depth reprojection compute pass to maintain fluid {vr_hz} Hz stereo tracking."
        verdict_text = f"Recommended: <strong>AUTO or ON</strong> for {vr_name} @ {vr_hz} Hz to maintain glass-smooth motion in VR."
        cpu_note = f"On your {cpu_name}: Low compositor pacing overhead. Paces render loop to match {vr_target_fps} FPS reprojection target."
        gpu_note = f"On your {gpu_name}: OpenXR depth reprojection compute pass to maintain fluid {vr_hz} Hz stereo tracking."

    elif key in ["volumetric_lights", "light_shafts"]:
        pipe_text = "Volumetric atmospheric light scattering and sunbeam crepuscular rays passing through clouds and terrain."
        cpu_detail = f"Negligible CPU overhead on your <strong>{cpu_name}</strong>."
        gpu_detail = f"Volumetric light marching pass on your <strong>{gpu_name}</strong>."
        verdict_text = "Recommended: <strong>HIGH / ULTRA</strong>."
        cpu_note = f"On your {cpu_name}: Negligible CPU compute."
        gpu_note = f"On your {gpu_name}: Volumetric light scattering shader pass."

    elif key == "reflections_ssr":
        pipe_text = "Screen Space Reflections (SSR) calculates real-time specular reflections by raymarching across the depth and color buffers. It simulates mirror-like wet apron tarmac, water puddles, runway rain sheen, and canopy glass reflections."
        cpu_detail = f"Zero impact on your <strong>{cpu_name}</strong> MainThread. Raymarching is executed entirely on GPU shader cores after scene depth rasterization."
        
        if is_vr:
            if any(k in v_upper for k in ["LOW", "OFF"]):
                gpu_detail = f"In VR on your <strong>{gpu_name}</strong>: Currently set to <strong>{val_str.upper()}</strong>. Low SSR preserves critical stereo fill rate across dual headset eye displays and prevents distracting reflection disparity between left and right eyes."
                gpu_note = f"On your {gpu_name}: Low SSR in VR preserves stereo fill-rate budget (~2-3/12 load)."
            else:
                gpu_detail = f"In VR on your <strong>{gpu_name}</strong>: Currently set to <strong>{val_str.upper()}</strong>. SSR in VR requires computing raymarching twice per frame in stereo. This imposes a heavy 2-3ms GPU penalty and can cause stereo visual divergence when looking at puddles in the headset."
                gpu_note = f"On your {gpu_name}: Heavy stereo raymarching in headset (~8-10/12 load). Risks VR reprojection drops."
            verdict_text = "Recommended in VR: <strong>LOW or OFF</strong> to eliminate stereo reflection disparity and preserve headset frame budget."
        else: # 2D mode
            if is_flagship_gpu or is_high_tier_gpu:
                if any(k in v_upper for k in ["HIGH", "ULTRA"]):
                    gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): Currently set to <strong>{val_str.upper()}</strong>. Full-sample screen-space raymarching delivers gorgeous wet asphalt puddles, tarmac gloss, and cockpit canopy rain sheen during night/rain operations. Your {gpu_name} evaluates these depth passes in ~0.3-0.5 ms with virtually zero impact on your {cadence_desc} target."
                    gpu_note = f"On your {gpu_name}: High-fidelity wet runway raymarching. Easily rendered in ~0.5ms (~2-4/12 load)."
                elif "MEDIUM" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently set to <strong>MEDIUM</strong>. Quarter-resolution raymarching reduces reflection sample counts. Reflections appear slightly noisier and lower resolution on wet runways."
                    gpu_note = f"On your {gpu_name}: Quarter-resolution reflection buffer (~2-3/12 load)."
                else: # LOW or OFF
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently set to <strong>{val_str.upper()}</strong>. Depth raymarching is disabled or severely truncated. While this uses negligible GPU compute (~1/12 load), it leaves wet runways, aprons, and taxiways looking completely flat, dry, and matte during rain. Given your {gpu_name}'s high rasterization headroom, setting SSR to <strong>HIGH</strong> or <strong>ULTRA</strong> provides realistic wet runway reflections with zero measurable framerate loss."
                    gpu_note = f"On your {gpu_name}: Minimal raymarching compute (~1/12 load), but wet runways appear flat and matte."
                verdict_text = f"Recommended for your {gpu_name}: <strong>HIGH or ULTRA</strong>. Realistic wet runway puddle gloss and cockpit canopy reflections with virtually zero FPS penalty on this GPU."
            elif is_vram_constrained or is_entry_gpu:
                if any(k in v_upper for k in ["HIGH", "ULTRA"]):
                    gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): Currently set to <strong>{val_str.upper()}</strong>. Full screen-space raymarching requires 2-3ms of GPU shader frame time on your architecture, which can cause frame dips and stutter during stormy instrument approaches."
                    gpu_note = f"On your {gpu_name}: Heavy raymarching shader pass on constrained GPU (~7-9/12 load). May cause frame drops in rain."
                elif "MEDIUM" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently set to <strong>MEDIUM</strong>. Balanced quarter-resolution raymarching delivers visible wet runway reflections with controlled GPU shader overhead."
                    gpu_note = f"On your {gpu_name}: Quarter-resolution reflection buffer (~4/12 load)."
                else:
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently set to <strong>{val_str.upper()}</strong>. Preserves maximum GPU shader throughput for fluid flight."
                    gpu_note = f"On your {gpu_name}: Minimal raymarching compute (~2/12 load)."
                verdict_text = f"Recommended for your {gpu_name}: <strong>MEDIUM</strong> (or <strong>LOW</strong>). Balances realistic wet runway sheen with GPU frame budget."
            else: # Mid-range
                if any(k in v_upper for k in ["HIGH", "ULTRA"]):
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently set to <strong>{val_str.upper()}</strong>. Screen-space raymarching delivers crisp wet runway reflections."
                    gpu_note = f"On your {gpu_name}: Screen-space raymarching (~4-5/12 load)."
                elif "MEDIUM" in v_upper:
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently set to <strong>MEDIUM</strong>. Quarter-resolution reflection buffer."
                    gpu_note = f"On your {gpu_name}: Quarter-resolution reflection buffer (~3/12 load)."
                else:
                    gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently set to <strong>{val_str.upper()}</strong>. Wet runways look flat and matte."
                    gpu_note = f"On your {gpu_name}: Minimal compute (~1/12 load)."
                verdict_text = "Recommended: <strong>MEDIUM or HIGH</strong> for balanced wet runway visual fidelity."

    elif key in ["cubemap_reflections"]:
        pipe_text = "Controls the resolution of static and local environment reflection probes used for cockpit instrument glass, gauge bezel chrome, throttle quadrant polish, and metal fuselage liveries."
        cpu_detail = f"Lightweight cubemap probe culling and dispatch on your <strong>{cpu_name}</strong>."
        gpu_detail = f"Allocates reflection probe texture memory on your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM). Probe updates consume under 0.2 ms of GPU frame time."
        verdict_text = "Recommended: <strong>192 or 128</strong> in 2D (crisp metallic reflections); <strong>128 or 64</strong> in VR."
        cpu_note = f"On your {cpu_name}: Low reflection probe management."
        gpu_note = f"On your {gpu_name}: Local reflection probe texture allocation (~3/12 load)."

    elif key in ["dof", "depth_of_field", "motion_blur"]:
        pipe_text = "Cinematic post-processing passes: Circle-of-Confusion camera depth of field blur and velocity vector motion blur."
        cpu_detail = f"Zero CPU compute on your <strong>{cpu_name}</strong>."
        gpu_detail = f"Post-processing pixel shader passes on your <strong>{gpu_name}</strong>."
        verdict_text = "Recommended: <strong>LOW / OFF</strong> for cockpits; <strong>HIGH</strong> for cinematic external replay."
        cpu_note = f"On your {cpu_name}: Zero CPU compute; pure post-processing."
        gpu_note = f"On your {gpu_name}: Velocity vector and depth buffer blur post-processing."

    elif key in ["framerate_multiplier", "multiplier"]:
        pipe_text = "Frame Generation multiplier factor (DLSS 3 / FSR 3)."
        cpu_detail = f"Zero CPU compute on your <strong>{cpu_name}</strong>."
        gpu_detail = f"Optical flow interpolation passes on your <strong>{gpu_name}</strong>."
        verdict_text = "Recommended: <strong>2X</strong>."
        cpu_note = f"On your {cpu_name}: Zero CPU compute."
        gpu_note = f"On your {gpu_name}: Optical flow interpolation buffer pass."

    elif key in ["primary_scaling_vr"]:
        sw_name = (vr or {}).get("software_name") or "VR Headset Driver"
        sw_scale = (vr or {}).get("software_render_scale")
        sw_scale_pct = (vr or {}).get("software_render_scale_pct")
        hmd_name = (vr or {}).get("name") or "VR Headset"

        pipe_text = f"Governs the DirectX 12 primary render buffer scaling factor in VR stereo before handing frames to the OpenXR runtime. Operates downstream of the headset software compositor ({sw_name})."
        cpu_detail = f"Zero direct CPU draw-call compute on your <strong>{cpu_name}</strong>. Raster scaling is executed entirely on the GPU."
        
        if sw_scale:
            sw_info_str = f"Your <strong>{sw_name}</strong> software is currently set to <strong>{sw_scale:.2f} ({sw_scale_pct}%)</strong> on the {hmd_name}."
        else:
            sw_info_str = f"Connected headset: <strong>{hmd_name}</strong> via OpenXR."

        if "100%" in val_str:
            gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM): {sw_info_str} With MSFS locked at <strong>100%</strong>, the engine renders directly at 1:1 matching the OpenXR swapchain target. This guarantees zero double-downscaling blur, preserving razor-sharp text on PFD, ND, and MCDU cockpit screens."
            verdict_text = f"Optimal Configuration: <strong>LOCKED AT 100%</strong> in MSFS. Always adjust resolution and supersampling exclusively in <strong>{sw_name}</strong> to avoid compound bilinear downscaling."
            gpu_note = f"On your {gpu_name}: 1:1 OpenXR buffer rasterization. Pristine cockpit clarity."
        else:
            effective_pct = round(float(str(val_str).replace('%', '')) * (sw_scale or 1.0))
            effective_note = f" (effective resolution drops to {effective_pct}%!)" if sw_scale else ""
            gpu_detail = f"On your <strong>{gpu_name}</strong>: Currently set to <strong>{val_str}</strong> in MSFS{effective_note}. This causes <em>compound downscaling</em>: MSFS downsamples the frame, bilinearly upscales it, and the {sw_name} compositor resamples it again. This destroys high-frequency font legibility in the cockpit."
            verdict_text = f"Action Required: <strong>Reset MSFS to 100%</strong> immediately! On a high-tier {gpu_name}, all resolution scaling should be managed in <strong>{sw_name}</strong>."
            gpu_note = f"On your {gpu_name}: Compound downscaling blur hazard."

        cpu_note = f"On your {cpu_name}: Zero CPU MainThread workload."

    elif key in ["resolution", "display_resolution", "vr_resolution"]:
        pipe_text = "Governs the primary render target pixel count. Directly multiplies the total number of shaded fragments executed across the GPU rasterization pipeline."
        cpu_detail = f"Negligible direct CPU draw-call cost on your <strong>{cpu_name}</strong>; render resolution is primarily GPU fill-rate bound."
        gpu_detail = f"On your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB): At native resolution ({disp.get('width', 2560)}x{disp.get('height', 1440)}), the pipeline shades 3.68 million pixels per frame. Handled effortlessly with ample memory bandwidth headroom."
        verdict_text = "Recommended: <strong>Native 100%</strong> with DLSS or DLAA."
        cpu_note = f"On your {cpu_name}: Minimal direct CPU draw-call cost; resolution is primarily GPU-bound."
        gpu_note = f"On your {gpu_name} ({vram_gb:.0f} GB): Direct pixel fill-rate and memory bus workload. Ample headroom at current resolution."

    else:
        pipe_text = "MSFS DirectX 12 rendering pipeline and scene composition setting."
        cpu_detail = f"Standard MainThread scene dispatch and command list recording on your <strong>{cpu_name}</strong> ({cpu_cores}C/{cpu_threads}T)."
        gpu_detail = f"Rasterization and shading workload evaluated across execution units on your <strong>{gpu_name}</strong> ({vram_gb:.0f} GB VRAM)."
        verdict_text = f"Recommended: <strong>HIGH / BALANCED</strong> for optimal flight simulation fidelity and smooth {cadence_desc} pacing."
        cpu_note = f"On your {cpu_name}: Standard MainThread workload."
        gpu_note = f"On your {gpu_name} ({vram_gb:.0f} GB): Standard GPU rasterization workload."

    # Assemble complete HTML block
    implications_html = f"""
    <div class="space-y-3 font-sans">
        {badges_html}
        <div class="space-y-1.5 text-xs">
            <span class="text-slate-400 font-bold uppercase tracking-wider block font-mono">DIRECTX 12 PIPELINE BEHAVIOR</span>
            <p class="text-slate-300 leading-relaxed">{pipe_text}</p>
        </div>
        <div class="space-y-2 text-xs">
            <span class="text-cyan-400 font-bold uppercase tracking-wider block font-mono">CPU MAINTHREAD IMPACT ({cpu_name})</span>
            <p class="text-slate-300 leading-relaxed">{cpu_detail}</p>
        </div>
        <div class="space-y-2 text-xs">
            <span class="text-emerald-400 font-bold uppercase tracking-wider block font-mono">GPU &amp; VRAM IMPACT ({gpu_name})</span>
            <p class="text-slate-300 leading-relaxed">{gpu_detail}</p>
        </div>
        {storage_html}
        <div class="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-amber-200 leading-relaxed">
            <span class="text-amber-400 font-bold uppercase font-mono block mb-0.5">TAILORED RIG VERDICT</span>
            <p>{verdict_text}</p>
        </div>
    </div>
    """

    return {
        "implications_html": implications_html,
        "cpu_note": cpu_note,
        "gpu_note": gpu_note
    }


def calculate_dynamic_hardware_impact(
    key: str,
    val: Any,
    gpu: Optional[Dict[str, Any]] = None,
    cpu: Optional[Dict[str, Any]] = None,
    is_vr: bool = False,
    is_liner: bool = True
) -> Tuple[int, int, str, str]:
    """
    Computes dynamic, hardware-calibrated CPU impact (1-12) and GPU impact (1-12)
    along with informative explanatory notes for MSFS graphics settings.
    Dynamically modulates scores based on the active setting value (e.g. Low vs Ultra),
    the detected GPU (Tier 1 Flagship RTX 5090/4090 vs Tier 2 High-End 16GB vs Tier 4 8GB VRAM Constrained),
    the detected CPU (Tier 1 3D V-Cache Elite 9850X3D/7800X3D vs Tier 2 Ultra-IPC 13900K vs Tier 4 Legacy),
    and whether rendering in 2D or stereo VR.
    """
    val_str = str(val).strip()
    v_up = val_str.upper()

    gpu_dict = gpu or {}
    cpu_dict = cpu or {}

    gpu_name = (gpu_dict.get("name_simplified") or gpu_dict.get("name") or "Dedicated GPU").strip()
    gpu_full = str(gpu_dict.get("name") or "").upper()
    vram_gb = float(gpu_dict.get("vram_total_gb") or 16.0)

    # 5 GPU Tiers
    is_flagship_gpu = any(k in gpu_full for k in ["5090", "5080", "4090", "7900 XTX", "7900XTX"]) or vram_gb >= 20.0
    is_high_tier_gpu = is_flagship_gpu or any(k in gpu_full for k in ["4080", "4070 TI", "4070TI", "4070 SUPER", "3090", "7900 XT", "7900XT", "7900 GRE"]) or vram_gb >= 15.0
    is_mid_tier_gpu = not is_high_tier_gpu and (any(k in gpu_full for k in ["4070", "3080", "6800", "7800", "7700"]) or (vram_gb >= 10.0 and vram_gb < 15.0))
    is_vram_constrained = (vram_gb <= 8.5) and not (vram_gb < 6.5)
    is_entry_gpu = any(k in gpu_full for k in ["1660", "1060", "1070", "1650", "3050", "2060", "6600", "580", "570"]) or (vram_gb < 6.5)
    is_rtx40 = any(k in gpu_full for k in ["4090", "4080", "4070", "4060", "5090", "5080", "5070"])
    is_rtx50 = any(k in gpu_full for k in ["5090", "5080", "5070"])

    cpu_name = (cpu_dict.get("name_simplified") or cpu_dict.get("name") or "Multi-Core CPU").strip()
    cpu_full = str(cpu_dict.get("name") or "").upper()

    # 4 CPU Tiers
    is_x3d = "X3D" in cpu_full or "3D V-CACHE" in cpu_full
    is_flagship_intel = any(k in cpu_full for k in ["13900", "14900", "285K", "13700", "14700", "9950", "7950"])
    is_legacy_cpu = any(k in cpu_full for k in ["8700", "9700", "9900", "10700", "3600", "2600", "1600", "2700", "i5-8", "i5-9", "i5-10", "i7-8", "i7-9"])

    # Default baseline scores
    c_score = 2
    g_score = 3
    c_note = f"On your {cpu_name}: Standard MainThread workload."
    g_note = f"On your {gpu_name}: Standard GPU rasterization workload."

    if key == "anti_aliasing":
        c_score = 2
        if "PERFORMANCE" in v_up:
            g_score = 1 if not is_vr else 2
            g_note = f"On your {gpu_name}: Ultra-light 50% internal render ({g_score}/12 load). Maximizes GPU framerate headroom and ensures rock-solid frame pacing in heavy weather and complex airports."
            c_note = f"On your {cpu_name}: Minimal driver queue overhead; completely eliminates GPU backpressure."
        elif "BALANCED" in v_up:
            if is_flagship_gpu:
                g_score = 2 if not is_vr else 4
                g_note = f"On your {gpu_name}: 58% internal render scale ({g_score}/12 load). Minor font softening for unneeded GPU relief."
            elif is_vram_constrained or is_entry_gpu:
                g_score = 4 if not is_vr else 6
                g_note = f"On your {gpu_name}: 58% internal render ({g_score}/12 load). Provides strong framerate relief with acceptable readability."
            else:
                g_score = 3 if not is_vr else 5
                g_note = f"On your {gpu_name}: 58% internal render downscale ({g_score}/12 load). Light GPU load with subtle font softening."
            c_note = f"On your {cpu_name}: Minimal driver queue overhead."
        elif "QUALITY" in v_up:
            if is_flagship_gpu:
                g_score = 2 if not is_vr else 4
                g_note = f"On your {gpu_name} (Flagship): 67% render + Tensor reconstruction ({g_score}/12 load). Saves 30% shading time, though DLAA is easily affordable."
            elif is_vram_constrained or is_entry_gpu:
                g_score = 5 if not is_vr else 8
                g_note = f"On your {gpu_name} ({vram_gb:.0f} GB VRAM): 67% render scale + DLSS upscaling ({g_score}/12 load). Essential to preserve VRAM and sustain smooth 50-60 FPS."
            else:
                g_score = 3 if not is_vr else 5
                g_note = f"On your {gpu_name}: 67% render + Tensor AI reconstruction ({g_score}/12 load). Saves 25-35% shading time while keeping cockpits sharp."
            c_note = f"On your {cpu_name}: Relieves GPU backpressure on the CPU MainThread."
        elif "DLAA" in v_up:
            if is_flagship_gpu:
                g_score = 3 if not is_vr else 6
                g_note = f"On your {gpu_name} (Flagship Monster): Native AI anti-aliasing ({g_score}/12 load). Pristine cockpit EFIS avionics with immense GPU headroom."
            elif is_vram_constrained or is_entry_gpu:
                g_score = 9 if not is_vr else 12
                g_note = f"On your {gpu_name} ({vram_gb:.0f} GB VRAM): Native DLAA heavily saturates the memory bus and Tensor cores ({g_score}/12 load). DLSS Quality recommended."
            elif is_high_tier_gpu:
                g_score = 5 if not is_vr else 9
                g_note = f"On your {gpu_name}: Native 1:1 AI anti-aliasing ({g_score}/12 load). Crystal-clear EFIS instruments with high GPU margin."
            else:
                g_score = 6 if not is_vr else 10
                g_note = f"On your {gpu_name}: Native 1:1 AI anti-aliasing ({g_score}/12 load). High clarity, moderate GPU frame time."
            c_note = f"On your {cpu_name}: Tensor Cores handle temporal stability at native resolution."
        else: # TAA
            if is_flagship_gpu:
                g_score = 4 if not is_vr else 7
                g_note = f"On your {gpu_name}: Native rasterization TAA ({g_score}/12 load). Clean frame delivery at standard GPU time."
            elif is_vram_constrained or is_entry_gpu:
                g_score = 8 if not is_vr else 11
                g_note = f"On your {gpu_name}: Native raster TAA ({g_score}/12 load). Full raster shading burden on entry/constrained hardware."
            else:
                g_score = 6 if not is_vr else 8
                g_note = f"On your {gpu_name}: Native rasterization TAA ({g_score}/12 load). Clean image at standard GPU frame time."
            c_note = f"On your {cpu_name}: Standard DirectX 12 native render queue."

    elif key in ["reflections_ssr", "reflections"]:
        c_score = 1
        c_note = f"On your {cpu_name}: Zero reflection compute; executed entirely on GPU."
        if "OFF" in v_up or v_up in ["0", "NONE"]:
            g_score = 1
            if is_flagship_gpu:
                g_note = f"On your {gpu_name}: Screen Space Reflections disabled ({g_score}/12 load). Wet aprons look flat and matte despite your GPU having massive headroom."
            else:
                g_note = f"On your {gpu_name}: Screen Space Reflections disabled ({g_score}/12 load)."
        elif "LOW" in v_up:
            g_score = 1 if is_flagship_gpu else (2 if not is_vr else 3)
            g_note = f"On your {gpu_name}: Low-sample depth raymarching ({g_score}/12 load). Wet runways lack realistic reflection definition."
        elif "MEDIUM" in v_up:
            g_score = 2 if is_flagship_gpu else (3 if not is_vr else 5)
            g_note = f"On your {gpu_name}: Quarter-resolution reflection buffer ({g_score}/12 load). Balanced wet runway sheen."
        elif "HIGH" in v_up:
            if is_flagship_gpu:
                g_score = 2 if not is_vr else 5
                g_note = f"On your {gpu_name} (Flagship): Half-resolution depth raymarching (~0.2ms, {g_score}/12 load). Flawlessly rendered."
            elif is_vram_constrained or is_entry_gpu:
                g_score = 7 if not is_vr else 10
                g_note = f"On your {gpu_name}: Noticeable shader load on constrained hardware ({g_score}/12 load)."
            else:
                g_score = 4 if not is_vr else 7
                g_note = f"On your {gpu_name}: Half-resolution depth raymarching (~0.5ms, {g_score}/12 load). Realistic wet tarmac gloss."
        elif "ULTRA" in v_up:
            if is_flagship_gpu:
                g_score = 3 if not is_vr else 6
                g_note = f"On your {gpu_name} (Flagship Monster): Full-fidelity screen-space raymarching (~0.3-0.5ms, {g_score}/12 load). Gorgeous wet tarmac gloss with zero FPS loss."
            elif is_vram_constrained or is_entry_gpu:
                g_score = 9 if not is_vr else 12
                g_note = f"On your {gpu_name} ({vram_gb:.0f} GB VRAM): Full SSR raymarching heavily strains shaders and memory bandwidth ({g_score}/12 HAZARD, 2-3ms). Medium or Low advised."
            else:
                g_score = 5 if not is_vr else 9
                g_note = f"On your {gpu_name}: Full-fidelity raymarching on wet tarmac and canopy glass (~{g_score}/12, 0.8ms)."

    elif key == "volumetric_clouds":
        if is_flagship_gpu:
            if "LOW" in v_up: c_score, g_score = 2, 2
            elif "MEDIUM" in v_up: c_score, g_score = 2, 3
            elif "HIGH" in v_up: c_score, g_score = 3, 4
            else: c_score, g_score = 3, 5
            g_note = f"On your {gpu_name} (Flagship Monster): Volumetric 3D density raymarching effortlessly handled (~1.8ms, {g_score}/12 load)."
        elif is_vram_constrained or is_entry_gpu:
            if "LOW" in v_up: c_score, g_score = 2, 3
            elif "MEDIUM" in v_up: c_score, g_score = 2, 5
            elif "HIGH" in v_up: c_score, g_score = 3, 8
            else: c_score, g_score = 3, 11
            g_note = f"On your {gpu_name} ({vram_gb:.0f} GB VRAM): Dense cloud raymarching heavily taxes shader units ({g_score}/12 load). High or Medium recommended."
        elif is_high_tier_gpu:
            if "LOW" in v_up: c_score, g_score = 2, 3
            elif "MEDIUM" in v_up: c_score, g_score = 2, 4
            elif "HIGH" in v_up: c_score, g_score = 3, 6
            else: c_score, g_score = 3, 8
            g_note = f"On your {gpu_name}: Advanced architecture handles volumetric raymarching smoothly ({g_score}/12 load)."
        else:
            if "LOW" in v_up: c_score, g_score = 2, 3
            elif "MEDIUM" in v_up: c_score, g_score = 2, 5
            elif "HIGH" in v_up: c_score, g_score = 3, 7
            else: c_score, g_score = 3, 9
            g_note = f"On your {gpu_name}: Volumetric 3D density raymarching ({g_score}/12)."
        c_note = f"On your {cpu_name}: Cloud weather simulation passed directly to GPU."

    elif key in ["shadow_maps", "shadows"]:
        if any(k in v_up for k in ["512", "LOW"]): c_score, g_score = 2, 3
        elif any(k in v_up for k in ["1024", "MEDIUM"]): c_score, g_score = 4, 5
        elif any(k in v_up for k in ["1536", "HIGH"]): c_score, g_score = 5, 6
        elif any(k in v_up for k in ["2048", "ULTRA"]): c_score, g_score = 7, 8
        c_note = f"On your {cpu_name}: Frustum culling and cascaded shadow draw calls ({c_score}/12)."
        g_note = f"On your {gpu_name}: Direct shadow map depth rendering ({g_score}/12)."

    elif key in ["terrain_shadows"]:
        if "OFF" in v_up: c_score, g_score = 1, 1
        elif any(k in v_up for k in ["LOW", "256"]): c_score, g_score = 2, 3
        elif any(k in v_up for k in ["MEDIUM", "512"]): c_score, g_score = 3, 5
        elif any(k in v_up for k in ["HIGH", "1024"]): c_score, g_score = 4, 6
        elif any(k in v_up for k in ["ULTRA", "2048"]): c_score, g_score = 5, 7
        c_note = f"On your {cpu_name}: Long-distance terrain shadow boundary dispatch."
        g_note = f"On your {gpu_name}: Raymarched digital elevation shadow casting ({g_score}/12)."

    elif key in ["ambient_occlusion", "ssao"]:
        if "OFF" in v_up: c_score, g_score = 1, 1
        elif "LOW" in v_up: c_score, g_score = 1, 2
        elif "MEDIUM" in v_up: c_score, g_score = 1, 4
        elif "HIGH" in v_up: c_score, g_score = 1, (5 if is_high_tier_gpu else 7)
        elif "ULTRA" in v_up: c_score, g_score = 1, (7 if is_high_tier_gpu else 9)
        c_note = f"On your {cpu_name}: Negligible CPU compute."
        g_note = f"On your {gpu_name}: Compute shader screen-space ambient occlusion ({g_score}/12)."

    elif key == "water_waves":
        if any(k in v_up for k in ["LOW", "128"]): c_score, g_score = 1, 2
        elif any(k in v_up for k in ["MEDIUM", "256"]): c_score, g_score = 2, 4
        elif any(k in v_up for k in ["HIGH", "512"]): c_score, g_score = 2, 6
        elif any(k in v_up for k in ["ULTRA", "1024"]): c_score, g_score = 3, 7
        c_note = f"On your {cpu_name}: Water FFT grid simulation dispatch."
        g_note = f"On your {gpu_name}: Ocean wave displacement and reflection shaders ({g_score}/12)."

    elif key == "contact_shadows":
        if "OFF" in v_up: c_score, g_score = 1, 1
        elif "LOW" in v_up: c_score, g_score = 1, 2
        elif "MEDIUM" in v_up: c_score, g_score = 1, 3
        elif "HIGH" in v_up: c_score, g_score = 1, 4
        elif "ULTRA" in v_up: c_score, g_score = 2, 5
        c_note = f"On your {cpu_name}: Low CPU overhead."
        g_note = f"On your {gpu_name}: Screen-space depth micro-shadows ({g_score}/12)."

    elif key == "windshield_effects":
        if "OFF" in v_up: c_score, g_score = 1, 1
        elif "LOW" in v_up: c_score, g_score = 1, 2
        elif "MEDIUM" in v_up: c_score, g_score = 1, 4
        elif "HIGH" in v_up: c_score, g_score = 1, 5
        elif "ULTRA" in v_up: c_score, g_score = 1, 6
        c_note = f"On your {cpu_name}: Zero CPU compute."
        g_note = f"On your {gpu_name}: Procedural rain droplets and windshield refraction ({g_score}/12)."

    elif key in ["tlod", "terrain_lod"]:
        clean_num = int(''.join(filter(str.isdigit, val_str)) or 100)
        if is_x3d:
            if clean_num <= 100: c_score = 3
            elif clean_num <= 150: c_score = 5
            elif clean_num <= 180: c_score = 6
            elif clean_num <= 220: c_score = 8
            elif clean_num <= 280: c_score = 10
            else: c_score = 12
            c_note = f"On your {cpu_name} (3D V-Cache Elite): 96MB L3 cache acts as a shock absorber for terrain quadtree BVH lookups ({c_score}/12 load). MainThread frame pacing remains rock-solid."
        elif is_flagship_intel:
            if clean_num <= 100: c_score = 4
            elif clean_num <= 130: c_score = 6
            elif clean_num <= 160: c_score = 8
            elif clean_num <= 200: c_score = 10
            else: c_score = 12
            c_note = f"On your {cpu_name} (Ultra-IPC Hybrid): Strong single P-core throughput ({c_score}/12 load). Beyond 150 at dense payware hubs risks pushing MainThread past frame budget."
        elif is_legacy_cpu:
            if clean_num <= 80: c_score = 6
            elif clean_num <= 100: c_score = 8
            elif clean_num <= 130: c_score = 11
            else: c_score = 12
            c_note = f"On your {cpu_name} (Legacy Architecture): Severe CPU MainThread bottleneck ({c_score}/12 HAZARD). TLOD > 100 causes severe touchdown stutter spikes."
        else: # Mainstream
            if clean_num <= 100: c_score = 5
            elif clean_num <= 130: c_score = 7
            elif clean_num <= 160: c_score = 9
            else: c_score = 11
            c_note = f"On your {cpu_name}: MainThread draw call dispatch ({c_score}/12 load). Keep under 130 for fluid airliner landings."
        
        if is_flagship_gpu:
            g_score = 2 if clean_num <= 120 else (3 if clean_num <= 180 else 4)
            g_note = f"On your {gpu_name} (Flagship Monster): Terrain vertex buffers & heightfield geometry ({g_score}/12 load). Easily buffered in your {vram_gb:.0f} GB pool."
        elif is_vram_constrained or is_entry_gpu:
            g_score = 6 if clean_num <= 120 else (8 if clean_num <= 180 else 10)
            g_note = f"On your {gpu_name} ({vram_gb:.0f} GB VRAM): High vertex buffer and heightfield rasterization load ({g_score}/12 load)."
        elif is_high_tier_gpu:
            g_score = 4 if clean_num <= 120 else (5 if clean_num <= 180 else 6)
            g_note = f"On your {gpu_name}: Terrain vertex buffers and heightfield geometry ({g_score}/12)."
        else:
            g_score = 5 if clean_num <= 120 else 7
            g_note = f"On your {gpu_name}: Terrain vertex buffers and heightfield geometry ({g_score}/12)."

    elif key in ["olod", "objects_lod"]:
        clean_num = int(''.join(filter(str.isdigit, val_str)) or 100)
        if is_x3d:
            if clean_num <= 100: c_score = 3
            elif clean_num <= 150: c_score = 5
            elif clean_num <= 200: c_score = 7
            else: c_score = 9
            c_note = f"On your {cpu_name} (3D V-Cache): 3D airport building draw calls efficiently buffered by L3 cache ({c_score}/12 load)."
        elif is_flagship_intel:
            if clean_num <= 100: c_score = 4
            elif clean_num <= 150: c_score = 6
            elif clean_num <= 200: c_score = 8
            else: c_score = 11
            c_note = f"On your {cpu_name}: Multiplies scene draw calls for 3D airport buildings ({c_score}/12)."
        elif is_legacy_cpu:
            if clean_num <= 100: c_score = 7
            elif clean_num <= 150: c_score = 10
            else: c_score = 12
            c_note = f"On your {cpu_name} (Legacy): Major draw-call bottleneck on 3D buildings ({c_score}/12 HAZARD)."
        else:
            if clean_num <= 100: c_score = 5
            elif clean_num <= 150: c_score = 7
            else: c_score = 10
            c_note = f"On your {cpu_name}: Multiplies scene draw calls for 3D airport buildings ({c_score}/12)."
        g_score = 3 if is_flagship_gpu else (4 if clean_num <= 120 else 5)
        g_note = f"On your {gpu_name}: 3D model polygon rasterization ({g_score}/12)."

    elif key in ["glass_cockpits", "glass_cockpit_refresh"]:
        if is_x3d:
            if any(k in v_up for k in ["LOW", "QUARTER"]): c_score, g_score = 2, 2
            elif any(k in v_up for k in ["MEDIUM", "HALF"]): c_score, g_score = 4, 2
            else: c_score, g_score = 6, 2
            c_note = f"On your {cpu_name} (3D V-Cache Elite): 96MB L3 cache buffers Coherent GT JavaScript avionics and DOM nodes ({c_score}/12 load). High refresh runs smoothly."
        elif is_flagship_intel:
            if any(k in v_up for k in ["LOW", "QUARTER"]): c_score, g_score = 3, 2
            elif any(k in v_up for k in ["MEDIUM", "HALF"]): c_score, g_score = 5, 2
            else: c_score, g_score = 9, 3
            c_note = f"On your {cpu_name} (Intel Hybrid): High forces Coherent GT avionics redraw every frame ({c_score}/12 load), adding 4-6ms to the MainThread P-core. Medium (Half) recommended."
        elif is_legacy_cpu:
            if any(k in v_up for k in ["LOW", "QUARTER"]): c_score, g_score = 4, 2
            elif any(k in v_up for k in ["MEDIUM", "HALF"]): c_score, g_score = 7, 2
            else: c_score, g_score = 11, 3
            c_note = f"On your {cpu_name} (Legacy Architecture): High avionics refresh severely saturates the MainThread ({c_score}/12 HAZARD). Medium or Low is mandatory."
        else:
            if any(k in v_up for k in ["LOW", "QUARTER"]): c_score, g_score = 3, 2
            elif any(k in v_up for k in ["MEDIUM", "HALF"]): c_score, g_score = 5, 2
            else: c_score, g_score = 9, 3
            c_note = f"On your {cpu_name}: Coherent GT avionics execution ({c_score}/12)."
        g_note = f"On your {gpu_name}: 2D canvas texture blit to cockpit screens ({g_score}/12)."

    elif key == "frame_generation":
        if any(k in v_up for k in ["DLSSG", "FSR3", "2X", "ON", "1"]):
            if is_rtx50 or (is_rtx40 and is_flagship_gpu):
                c_score, g_score = 1, 2
                g_note = f"On your {gpu_name} (Flagship OFA): Dedicated Optical Flow hardware synthesizes frames with ~0.8ms compute pass ({g_score}/12 load)."
            elif is_rtx40:
                c_score, g_score = 1, 4
                g_note = f"On your {gpu_name}: Optical Flow Accelerator compute pass ({g_score}/12)."
            else:
                c_score, g_score = 1, 6
                g_note = f"On your {gpu_name}: Frame generation shader pass ({g_score}/12)."
            c_note = f"On your {cpu_name}: Zero CPU MainThread cycles. Frames synthesized independently on GPU."
        else:
            c_score, g_score = 1, 1
            c_note = f"On your {cpu_name}: Frame generation disabled."
            g_note = f"On your {gpu_name}: Frame generation disabled (1/12)."

    elif key in ["resolution", "display_resolution", "vr_resolution"]:
        c_score = 1
        g_score = 11 if is_vr else (5 if is_flagship_gpu else (7 if is_high_tier_gpu else 10))
        c_note = f"On your {cpu_name}: Minimal direct CPU draw-call cost."
        g_note = f"On your {gpu_name}: Direct pixel fill-rate across native frame buffer ({g_score}/12)."

    elif key in ["texture_resolution", "terrain_texture"]:
        c_score = 2
        c_note = f"On your {cpu_name}: Background I/O threads stream aerial textures."
        if is_flagship_gpu or vram_gb >= 20.0:
            if "LOW" in v_up: g_score = 1
            elif "MEDIUM" in v_up: g_score = 2
            elif "HIGH" in v_up: g_score = 2
            else: g_score = 3
            g_note = f"On your {gpu_name} ({vram_gb:.0f} GB VRAM): Ultra textures consume ~4.2 GB VRAM ({g_score}/12 load). Zero risk of D3D12 memory paging in your massive buffer."
        elif is_vram_constrained:
            if "LOW" in v_up:
                g_score = 4
                g_note = f"On your {gpu_name} (8 GB VRAM): Low textures consume ~1.8 GB VRAM ({g_score}/12 load). Essential safety margin to prevent 8GB pool overflow on complex airliners."
            elif "MEDIUM" in v_up:
                g_score = 7
                g_note = f"On your {gpu_name} (8 GB VRAM): Medium textures allocate ~2.8 GB ({g_score}/12 load). Leaves tight memory margin at payware airports."
            elif "HIGH" in v_up:
                g_score = 10
                g_note = f"On your {gpu_name} (8 GB VRAM): High textures push total MSFS VRAM near 7.8-8.2 GB ({g_score}/12 HAZARD). Risk of PCIe paging and frame rate collapse."
            else: # ULTRA
                g_score = 12
                g_note = f"On your {gpu_name} (8 GB VRAM): Ultra textures exceed the 8 GB GDDR6 physical pool ({g_score}/12 HAZARD). Overflows into system RAM, causing catastrophic 5-10 FPS stutters."
        elif is_entry_gpu:
            if "LOW" in v_up: g_score = 5
            elif "MEDIUM" in v_up: g_score = 8
            elif "HIGH" in v_up: g_score = 11
            else: g_score = 12
            g_note = f"On your {gpu_name} ({vram_gb:.0f} GB VRAM): Heavy texture memory load ({g_score}/12 load)."
        elif is_high_tier_gpu:
            if "LOW" in v_up: g_score = 2
            elif "MEDIUM" in v_up: g_score = 4
            elif "HIGH" in v_up: g_score = 6
            else: g_score = 7
            g_note = f"On your {gpu_name} ({vram_gb:.0f} GB): Ultra textures allocate ~3.5-4.5 GB ({g_score}/12 load). Fits comfortably; Medium/High gives comfortable safety margin for add-on airliners."
        else: # Mid-range
            if "LOW" in v_up: g_score = 2
            elif "MEDIUM" in v_up: g_score = 5
            elif "HIGH" in v_up: g_score = 7
            else: g_score = 9
            g_note = f"On your {gpu_name} ({vram_gb:.0f} GB): Textures allocate significant memory ({g_score}/12 load). Medium is optimal for airliners."

    elif key in ["anisotropic_filtering"]:
        c_score = 1
        g_score = 2
        c_note = f"On your {cpu_name}: Zero CPU compute."
        g_note = f"On your {gpu_name}: Texture sampler lookups. Negligible cost (<0.1ms)."

    elif key in ["cubemap_reflections"]:
        c_score = 1
        g_score = 3
        c_note = f"On your {cpu_name}: Low reflection probe management."
        g_note = f"On your {gpu_name}: Reflection probe buffer resolution ({g_score}/12)."

    elif key in ["raytraced_shadows", "raytracing"]:
        if "OFF" in v_up or v_up in ["0", "NONE"]:
            c_score, g_score = 1, 1
            c_note = f"On your {cpu_name}: RT structures inactive."
            g_note = f"On your {gpu_name}: Ray tracing disabled (1/12)."
        else:
            c_score, g_score = 4, (8 if is_flagship_gpu else 11)
            c_note = f"On your {cpu_name}: BVH acceleration structure management."
            g_note = f"On your {gpu_name}: Heavy RT-core intersection passes ({g_score}/12)."

    elif key in ["buildings", "vector_data_buildings"]:
        if is_x3d:
            if "LOW" in v_up: c_score = 1
            elif "MEDIUM" in v_up: c_score = 2
            elif "HIGH" in v_up: c_score = 3
            else: c_score = 4
            c_note = f"On your {cpu_name} (3D V-Cache): L3 cache swiftly processes Blackshark AI autogen building quadtree indexes ({c_score}/12 load)."
        elif is_flagship_intel:
            if "LOW" in v_up: c_score = 2
            elif "MEDIUM" in v_up: c_score = 3
            elif "HIGH" in v_up: c_score = 4
            else: c_score = 6
            c_note = f"On your {cpu_name} (Ultra-IPC Hybrid): Strong single P-core handles urban building indexing and draw dispatch ({c_score}/12 load)."
        elif is_legacy_cpu:
            if "LOW" in v_up: c_score = 3
            elif "MEDIUM" in v_up: c_score = 5
            elif "HIGH" in v_up: c_score = 7
            else: c_score = 10
            c_note = f"On your {cpu_name} (Legacy): High/Ultra autogen buildings strain MainThread draw calls over cities ({c_score}/12 load)."
        else:
            if "LOW" in v_up: c_score = 2
            elif "MEDIUM" in v_up: c_score = 3
            elif "HIGH" in v_up: c_score = 5
            else: c_score = 7
            c_note = f"On your {cpu_name}: Autogen building spatial queries and draw-call dispatch ({c_score}/12 load)."

        if is_vr:
            if "LOW" in v_up:
                g_score = 2
                g_note = f"On your {gpu_name} (VR): Lightweight autogen geometry minimizes double-eye vertex workload and saves VRAM ({g_score}/12 load)."
            elif "MEDIUM" in v_up:
                g_score = 3 if is_flagship_gpu else 4
                g_note = f"On your {gpu_name} (VR): Balanced autogen building density with safe stereo frametime pacing ({g_score}/12 load)."
            elif "HIGH" in v_up:
                g_score = 5 if is_flagship_gpu else 6
                g_note = f"On your {gpu_name} (VR): High building geometry rendered per eye ({g_score}/12 load). Moderate VRAM allocation."
            else: # ULTRA in VR
                g_score = 7 if is_flagship_gpu else (8 if is_high_tier_gpu else 11)
                g_note = f"On your {gpu_name} (VR): Ultra autogen buildings doubles vertex throughput and texture streaming in headset ({g_score}/12 load). Risks reprojection drops."
        else: # 2D
            if is_flagship_gpu:
                if "LOW" in v_up: g_score = 1
                elif "MEDIUM" in v_up: g_score = 2
                elif "HIGH" in v_up: g_score = 3
                else: g_score = 4
                g_note = f"On your {gpu_name} (Flagship Monster): Procedural building meshes effortlessly rasterized with zero frame impact ({g_score}/12 load)."
            elif is_vram_constrained:
                if "LOW" in v_up: g_score = 2
                elif "MEDIUM" in v_up: g_score = 4
                elif "HIGH" in v_up: g_score = 6
                else: g_score = 9
                g_note = f"On your {gpu_name} (8 GB VRAM): High/Ultra building facade atlases consume valuable VRAM at dense hubs ({g_score}/12 load). Medium or Low advised."
            elif is_high_tier_gpu:
                if "LOW" in v_up: g_score = 2
                elif "MEDIUM" in v_up: g_score = 3
                elif "HIGH" in v_up: g_score = 4
                else: g_score = 5
                g_note = f"On your {gpu_name} ({vram_gb:.0f} GB VRAM): Architectural building meshes and facade reflections rendered cleanly ({g_score}/12 load)."
            else:
                if "LOW" in v_up: g_score = 2
                elif "MEDIUM" in v_up: g_score = 4
                elif "HIGH" in v_up: g_score = 6
                else: g_score = 8
                g_note = f"On your {gpu_name}: Building geometry and facade textures ({g_score}/12 load)."

    elif key == "trees":
        c_score = 1 if "LOW" in v_up else (2 if "MEDIUM" in v_up else (3 if "HIGH" in v_up else 4))
        c_note = f"On your {cpu_name}: Instanced tree billboard and 3D crown positioning ({c_score}/12 load)."
        if is_vr:
            if "LOW" in v_up:
                g_score = 2
                g_note = f"On your {gpu_name} (VR): Sparse foliage preserves vital stereo fill-rate budget ({g_score}/12 load)."
            elif "MEDIUM" in v_up:
                g_score = 3 if is_flagship_gpu else 4
                g_note = f"On your {gpu_name} (VR): Balanced tree canopy density with smooth stereo reprojection ({g_score}/12 load)."
            elif "HIGH" in v_up:
                g_score = 5 if is_flagship_gpu else 7
                g_note = f"On your {gpu_name} (VR): High foliage rasterization rendered twice per frame ({g_score}/12 load). Modest frame pacing impact."
            else: # ULTRA
                g_score = 7 if is_flagship_gpu else 9
                g_note = f"On your {gpu_name} (VR): Ultra dense tree canopy heavily stresses double-eye alpha fill rate ({g_score}/12 load). Risks VR reprojection drops."
        else: # 2D
            if is_flagship_gpu:
                g_score = 1 if "LOW" in v_up else (2 if "MEDIUM" in v_up else (3 if "HIGH" in v_up else 4))
                g_note = f"On your {gpu_name}: Dense forest canopies easily rasterized with negligible fill-rate penalty ({g_score}/12 load)."
            elif is_vram_constrained or is_entry_gpu:
                g_score = 2 if "LOW" in v_up else (4 if "MEDIUM" in v_up else (7 if "HIGH" in v_up else 9))
                g_note = f"On your {gpu_name}: Alpha-blended foliage shading over continuous forests ({g_score}/12 load)."
            else:
                g_score = 2 if "LOW" in v_up else (3 if "MEDIUM" in v_up else (4 if "HIGH" in v_up else 6))
                g_note = f"On your {gpu_name}: 3D tree foliage and shadow self-occlusion ({g_score}/12 load)."

    elif key == "grass":
        if is_liner:
            if any(k in v_up for k in ["LOW", "OFF"]):
                c_score, g_score = 1, 1
                c_note = f"On your {cpu_name}: Eliminates millions of useless 3D grass blade draw calls on paved runways ({c_score}/12 load)."
                g_note = f"On your {gpu_name}: Zero ground-level alpha overdraw on concrete aprons and runways ({g_score}/12 load)."
            elif "MEDIUM" in v_up:
                c_score, g_score = 2, 2
                c_note = f"On your {cpu_name}: Controlled procedural vegetation draw calls ({c_score}/12 load)."
                g_note = f"On your {gpu_name}: Light ground-level grass fill rate ({g_score}/12 load)."
            else: # HIGH / ULTRA
                c_score = 6 if not is_vr else 8
                g_score = 5 if not is_vr else 8
                c_note = f"On your {cpu_name}: Generates millions of redundant 3D vegetation triangles on paved runways ({c_score}/12 HAZARD on flare)."
                g_note = f"On your {gpu_name}: Unnecessary ground vegetation fill rate ({g_score}/12 load)."
        else: # GA
            c_score = 1 if "LOW" in v_up else (2 if "MEDIUM" in v_up else 3)
            g_score = 2 if "LOW" in v_up else (3 if "MEDIUM" in v_up else (5 if "HIGH" in v_up else 7))
            c_note = f"On your {cpu_name}: Procedural ground meadow geometry ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: 3D grass blades and flowers for grass airstrips ({g_score}/12 load)."

    elif key == "displacement_mapping":
        if "OFF" in v_up or v_up in ["0", "NONE"]:
            c_score, g_score = 1, 1
            c_note = f"On your {cpu_name}: Surface tessellation disabled (1/12)."
            g_note = f"On your {gpu_name}: Saves geometry shader stages and VRAM bandwidth (1/12)."
        else:
            c_score = 3 if not is_vr else 5
            g_score = 5 if not is_vr else 8
            c_note = f"On your {cpu_name}: Coordinates terrain heightfield tessellation ({c_score}/12)."
            g_note = f"On your {gpu_name}: Real-time surface tessellation across pavement and terrain ({g_score}/12)."

    elif key in ["volumetric_lights", "light_shafts"]:
        c_score = 1
        c_note = f"On your {cpu_name}: Negligible CPU compute."
        if "LOW" in v_up:
            g_score = 2
            g_note = f"On your {gpu_name}: Lightweight light beam marching ({g_score}/12 load)."
        elif "MEDIUM" in v_up:
            g_score = 3
            g_note = f"On your {gpu_name}: Balanced atmospheric light scattering in fog ({g_score}/12 load)."
        elif "HIGH" in v_up:
            g_score = 4 if not is_vr else 6
            g_note = f"On your {gpu_name}: Authentic runway light cones and strobe beams in low visibility CAT III ({g_score}/12 load)."
        else: # ULTRA
            g_score = 5 if not is_vr else 8
            g_note = f"On your {gpu_name}: Maximum density volumetric light cone marching ({g_score}/12 load)."

    elif key in ["particles"]:
        c_score = 1
        c_note = f"On your {cpu_name}: Particle emitter and physics dispatch."
        if any(k in v_up for k in ["LOW", "OFF"]):
            g_score = 2
            g_note = f"On your {gpu_name}: Light particle buffer allocation ({g_score}/12 load)."
        elif "MEDIUM" in v_up:
            g_score = 3 if not is_vr else 4
            g_note = f"On your {gpu_name}: Balanced smoke, spray, and contrail particle density ({g_score}/12 load)."
        elif "HIGH" in v_up:
            g_score = 5 if not is_vr else 7
            g_note = f"On your {gpu_name}: Dense touchdown tire smoke and spray with moderate alpha overdraw ({g_score}/12 load)."
        else: # ULTRA
            g_score = 6 if not is_vr else 9
            g_note = f"On your {gpu_name}: Maximum particle overdraw ({g_score}/12 load). Potential alpha fill rate drops in heavy spray."

    elif key in ["aircraft_traffic_variety", "parked_aircraft_variety", "airport_services_variety"]:
        c_score = 1
        c_note = f"On your {cpu_name}: Minimal CPU dispatch overhead for model selection."
        if "LOW" in v_up:
            g_score = 2
            g_note = f"On your {gpu_name}: Basic generic liveries cached. Minimal VRAM overhead (~200MB) and zero streaming hitching."
        elif "MEDIUM" in v_up:
            g_score = 4
            g_note = f"On your {gpu_name}: Balanced livery variety. Caches realistic airline fleet without straining VRAM (~600MB)."
        elif "HIGH" in v_up:
            g_score = 6 if not is_vram_constrained else 8
            g_note = f"On your {gpu_name}: High livery variety. Caches dozens of 4K liveries, consuming ~1.5-2.0 GB extra VRAM."
        else: # ULTRA
            g_score = 8 if is_flagship_gpu else 11
            g_note = f"On your {gpu_name}: Ultra livery variety. Caches uncapped 3D airframes and liveries ({g_score}/12 load). Can trigger VRAM thrashing at busy hubs."

    elif key == "sea_traffic":
        if "OFF" in v_up:
            c_score, g_score = 1, 1
            c_note = f"On your {cpu_name}: Maritime vessel pathfinding threads completely disabled ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Zero boat models, wake particles, or water foam decals rendered ({g_score}/12 load)."
        elif "LOW" in v_up:
            c_score, g_score = 1, 1
            c_note = f"On your {cpu_name}: Light background maritime navigation for GAIST / Seafront ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Lightweight boat models and wake meshes ({g_score}/12 load)."
        elif "MEDIUM" in v_up:
            c_score, g_score = 2, 2
            c_note = f"On your {cpu_name}: Moderate maritime pathfinding across coastal waterways ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Standard boat geometry and wake effects ({g_score}/12 load)."
        else: # HIGH / ULTRA
            c_score = 3 if not is_vr else 4
            g_score = 2 if not is_vr else 3
            c_note = f"On your {cpu_name}: Background thread maritime pathfinding ({c_score}/12 load). Modest impact (~1-3 FPS near ports, 0 FPS inland)."
            g_note = f"On your {gpu_name}: Low-polygon maritime vessel models and wake decals ({g_score}/12 load)."

    elif key == "road_traffic":
        if "OFF" in v_up:
            c_score, g_score = 1, 1
            c_note = f"On your {cpu_name}: Procedural vehicle thread dispatch completely disabled ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Zero roadway cars or vehicle headlights rendered ({g_score}/12 load)."
        elif "LOW" in v_up:
            c_score, g_score = 2, 2
            c_note = f"On your {cpu_name}: Sparse highway traffic simulation ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Low-polygon road vehicles ({g_score}/12 load)."
        elif "MEDIUM" in v_up:
            c_score, g_score = 4, 3
            c_note = f"On your {cpu_name}: Moderate urban vehicle pathfinding ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Standard road traffic density ({g_score}/12 load)."
        else: # HIGH / ULTRA
            c_score = 7 if not is_vr else 9
            g_score = 5 if not is_vr else 7
            c_note = f"On your {cpu_name}: Heavy traffic flow calculations across city grid ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Dense car queues and dynamic headlight illumination ({g_score}/12 load)."

    elif key == "characters_variety":
        c_score = 1 if "LOW" in v_up else (2 if "MEDIUM" in v_up else 3)
        c_note = f"On your {cpu_name}: Ground worker uniform selection and texture binding dispatch ({c_score}/12 load)."
        if "LOW" in v_up:
            g_score = 2
            g_note = f"On your {gpu_name}: Minimal worker uniform textures in VRAM ({g_score}/12 load). Zero memory paging overhead."
        elif "MEDIUM" in v_up:
            g_score = 3
            g_note = f"On your {gpu_name}: Balanced uniform sets cached in VRAM ({g_score}/12 load). Clean variety with safe headroom."
        elif "HIGH" in v_up:
            g_score = 5 if not is_vram_constrained else 7
            g_note = f"On your {gpu_name}: Multiple worker vest variations loaded into VRAM ({g_score}/12 load)."
        else: # ULTRA
            g_score = 7 if is_flagship_gpu else 9
            g_note = f"On your {gpu_name}: Uncapped ground crew texture variations cached ({g_score}/12 load)."

    elif key == "characters_quality":
        if "LOW" in v_up:
            c_score, g_score = 1, 1
            c_note = f"On your {cpu_name}: Low-polygon character LOD mesh minimizes vertex processing ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Lightweight character geometry rasterization ({g_score}/12 load)."
        elif "MEDIUM" in v_up:
            c_score, g_score = 2, 2
            c_note = f"On your {cpu_name}: Standard character skeletal mesh detail ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Balanced vertex density for ground crew ({g_score}/12 load)."
        elif "HIGH" in v_up:
            c_score, g_score = 4, 4
            c_note = f"On your {cpu_name}: High polygon character LODs add draw call vertex complexity ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Dense character polygon meshes ({g_score}/12 load)."
        else: # ULTRA
            c_score, g_score = 6, 6
            c_note = f"On your {cpu_name}: Ultra-dense character meshes viewed from far cockpit distances waste CPU vertex throughput ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Unnecessary sub-pixel polygon density for ground personnel ({g_score}/12 load)."

    elif key == "characters_quantity":
        if "OFF" in v_up:
            c_score, g_score = 1, 1
            c_note = f"On your {cpu_name}: Zero ground crew skeletal animations on CPU MainThread ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Zero ground personnel rendered on tarmac ({g_score}/12 load)."
        elif "LOW" in v_up:
            c_score, g_score = 2, 2
            c_note = f"On your {cpu_name}: Minimal apron personnel (gate marshallers only) ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Sparse worker models ({g_score}/12 load)."
        elif "MEDIUM" in v_up:
            c_score, g_score = 4, 3
            c_note = f"On your {cpu_name}: Animated baggage handlers and ramp workers ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Standard apron personnel density ({g_score}/12 load)."
        elif "HIGH" in v_up:
            c_score, g_score = 7, 5
            c_note = f"On your {cpu_name}: Crowds of animated ramp workers increase MainThread skeletal transforms ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Multiplies personnel polygon draw calls ({g_score}/12 load)."
        else: # ULTRA
            c_score, g_score = 10, 7
            c_note = f"On your {cpu_name}: Swarms of ground crew heavily saturate MainThread animation cycles ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Extreme ground worker draw call multiplier ({g_score}/12 load)."

    elif key == "fauna_density":
        if "OFF" in v_up:
            c_score, g_score = 1, 1
            c_note = f"On your {cpu_name}: Wildlife and bird flock spawning logic disabled ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Zero fauna models or animations rendered ({g_score}/12 load)."
        elif "LOW" in v_up:
            c_score, g_score = 2, 2
            c_note = f"On your {cpu_name}: Light wildlife spawning in rural areas ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Sparse low-polygon animal models ({g_score}/12 load)."
        elif "MEDIUM" in v_up:
            c_score, g_score = 3, 3
            c_note = f"On your {cpu_name}: Moderate bird flocks and land animals ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Standard wildlife model density ({g_score}/12 load)."
        else: # HIGH / ULTRA
            c_score, g_score = 6, 4
            c_note = f"On your {cpu_name}: Dense animal herds and continuous bird flock pathfinding ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Multiple wildlife instances and shadow rendering ({g_score}/12 load)."

    elif key in ["seatbelt_visibility", "seatbelts"]:
        if "OFF" in v_up or v_up in ["0", "NONE"]:
            c_score, g_score = 1, 1
            c_note = f"On your {cpu_name}: Seatbelt geometry completely omitted from cockpit mesh ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Saves cockpit harness polygon draw calls ({g_score}/12 load)."
        else: # ON
            c_score, g_score = 1, 2
            c_note = f"On your {cpu_name}: Zero CPU overhead ({c_score}/12 load)."
            g_note = f"On your {gpu_name}: Renders cockpit shoulder harness straps ({g_score}/12 load)."

    elif key == "primary_scaling_vr":
        c_score = 1
        c_note = f"On your {cpu_name}: Zero CPU MainThread workload."
        if "100%" in v_up:
            g_score = 6 if is_flagship_gpu else 8
            g_note = f"On your {gpu_name}: Native 1:1 OpenXR swapchain rasterization ({g_score}/12 load). Pristine cockpit avionics with zero double-downsampling blur."
        elif any(k in v_up for k in ["90%", "95%"]):
            g_score = 5 if is_flagship_gpu else 7
            g_note = f"On your {gpu_name}: Mild in-engine downscale ({g_score}/12 load). Noticeable softening of fine EFIS avionics fonts."
        else:
            g_score = 4 if is_flagship_gpu else 6
            g_note = f"On your {gpu_name}: Severe downscale ({val_str}) on a {gpu_name} ({vram_gb:.0f} GB VRAM). Compounds with headset software scale, creating heavy blur."

    elif key == "reflex":
        if "BOOST" in v_up:
            c_score, g_score = 1, 3
            c_note = f"On your {cpu_name}: Just-in-time draw call submission ({c_score}/12 load). Eliminates render queue lag."
            g_note = f"On your {gpu_name}: Forces GPU Core/Memory clocks to maximum boost frequency ({g_score}/12 load). Elevated power consumption with negligible latency gain over standard ON."
        elif "ON" in v_up or v_up == "1":
            c_score, g_score = 1, 1
            c_note = f"On your {cpu_name}: Optimal render queue pacing ({c_score}/12 load). Drains driver queue for zero input lag on flight controls."
            g_note = f"On your {gpu_name}: Standard dynamic clock scaling ({g_score}/12 load). Low power draw and zero shading penalty."
        else: # OFF
            c_score, g_score = 4, 2
            c_note = f"On your {cpu_name}: Unconstrained render queue buildup ({c_score}/12 load). CPU may queue 2-3 frames ahead, causing sluggish yoke and control response."
            g_note = f"On your {gpu_name}: Unsynchronized swapchain presentation ({g_score}/12 load). Higher input-to-display latency."

    return c_score, g_score, c_note, g_note


def build_msfs_settings_matrix(user_cfg_path: Optional[str] = None, gpu_info: Optional[Dict[str, Any]] = None, cpu_info: Optional[Dict[str, Any]] = None, storage_info: Optional[Dict[str, Any]] = None, flight_profile: str = 'LINER', vr_refresh_rate: int = 72, preferred_display_id: Optional[str] = None, all_displays_info: Optional[List[Dict[str, Any]]] = None, vr_headset_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    path = user_cfg_path or get_user_cfg_path()
    if not path or not os.path.exists(path):
        return {"found": False, "path": "", "matrix_2d": [], "matrix_vr": []}

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Overlay any in-memory staged settings on content without touching UserCfg.opt on disk
        for m, staged in _staged_user_cfg_settings.items():
            for k, v in staged.items():
                content = apply_setting_to_content(content, m, k, v)
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

    all_displays = all_displays_info if all_displays_info is not None else detect_all_displays()
    active_disp = detect_display_info(preferred_id=preferred_display_id, displays_list=all_displays)
    if vr_headset_info is None:
        vr_headset_info = detect_vr_headset()
    storage = storage_info or detect_msfs_storage(path)
    cpu = cpu_info or detect_cpu_info()
    gpu = gpu_info or detect_gpu_info()
    gpu_full = str((gpu or {}).get("name", "")).upper()
    cpu_full = str((cpu or {}).get("name", "")).upper()
    is_flagship_gpu = any(k in gpu_full for k in ["5090", "5080", "4090", "4080", "7900 XTX", "7900XTX"]) or vram_gb >= 20.0
    is_high_tier_gpu = is_flagship_gpu or any(k in gpu_full for k in ["4070 TI", "4070TI", "4070 SUPER", "4070", "3090", "3080", "7900 XT", "7900XT", "7900 GRE", "6800", "6900"]) or vram_gb >= 12.0
    is_vram_constrained = vram_gb <= 8.5
    is_entry_gpu = any(k in gpu_full for k in ["1660", "1060", "1070", "1650", "3050", "2060", "6600", "580", "570"]) or (vram_gb <= 6.5)
    is_x3d = "X3D" in cpu_full or "3D V-CACHE" in cpu_full
    is_flagship_cpu = is_x3d or any(k in cpu_full for k in ["13900", "14900", "285K", "9950", "7950"])
    is_legacy_cpu = any(k in cpu_full for k in ["8700", "9700", "9900", "10700", "3600", "2600", "1600", "2700", "I5-2", "I5-3", "I5-4", "I5-6", "I5-7", "I5-8", "I5-9", "I5-10", "I7-2", "I7-3", "I7-4", "I7-6", "I7-7", "I7-8", "I7-9", "I3-"])
    is_entry_rig = is_legacy_cpu or is_entry_gpu or is_vram_constrained
    screen_hz = int(active_disp.get("refresh_rate_int", 60))
    native_w = int(active_disp.get("width", 2560))
    native_h = int(active_disp.get("height", 1440))
    if screen_hz >= 240:
        target_2d_fps = 120
    elif screen_hz >= 180:
        target_2d_fps = 90
    elif screen_hz >= 165:
        target_2d_fps = 82
    elif screen_hz >= 144:
        target_2d_fps = 72
    elif screen_hz >= 120:
        target_2d_fps = 60
    elif screen_hz >= 75:
        target_2d_fps = screen_hz // 2
    else:
        target_2d_fps = 60

    video = extract_block(content, '{Video')
    g2d = extract_block(content, '{Graphics\n') or extract_block(content, '{Graphics\r\n')
    gvr = extract_block(content, '{GraphicsVR')

    def resolve_setting_tradeoff(key, val, is_liner, is_vr):
        val_str = str(val).strip()
        v_upper = val_str.upper()

        if key == "resolution":
            return ("+ NATIVE 1:1", "Matches physical display pixels with zero scaling blur.",
                    "- PIXEL SHADING", "Full raster fill-rate workload on GPU.")

        if key == "anti_aliasing":
            if "PERFORMANCE" in v_upper:
                return ("+ MAX GPU HEADROOM", "Cuts GPU rasterization workload by ~50%, securing locked framerates in heavy weather.",
                        "- AI RECONSTRUCTION", "Relies heavily on AI temporal upscaling.")
            elif "DLSS" in v_upper:
                return ("+ 25% GPU HEADROOM", "DLSS Tensor upscaling saves massive GPU frame time and stabilizes edges.",
                        "- MILD HUD GHOSTING", "Subtle temporal ghosting on fast digital cockpit displays.")
            elif "DLAA" in v_upper:
                return ("+ ULTRA SHARP EDGES", "AI edge smoothing at native resolution with zero upscaling blur.",
                        "- FULL GPU WORKLOAD", "Runs at native resolution without upscaling performance boost.")
            else:
                return ("+ NATIVE CLARITY", "Native raster clarity without AI reconstruction artifacts.",
                        "- HIGH GPU LOAD", "Full native shading workload reduces headroom in heavy clouds.")

        if key == "max_frame_rate":
            if any(num in val_str for num in ['30', '36', '40', '45', '60', '72', '80', '82', '90', '120']):
                return ("+ ZERO JUDDER", "Eliminates frame pacing spikes and stutter by locking to refresh divisor.",
                        "- CAPPED FPS", "Framerate cannot exceed locked refresh divisor.")
            else:
                return ("+ MAX PEAK FPS", "GPU runs uncapped for maximum instantaneous framerate.",
                        "- PACING JITTER", "Fluctuating frame delivery times cause micro-stutters.")

        if key == "frame_generation":
            if not is_vr:
                if any(k in v_upper for k in ["DLSSG", "FSR3", "ON", "2X"]):
                    return ("+ 2X SMOOTHNESS", "Optical Flow doubles visual framerate without CPU MainThread penalty.",
                            "- 10MS INPUT LAG", "Adds slight frame latency; requires NVIDIA Reflex to mitigate.")
                else:
                    return ("+ LOWEST LATENCY", "Pure direct yoke and flight control responsiveness.",
                            "- 1X MOTION FPS", "Half the perceived visual motion smoothness.")
            else:
                if v_upper in ["OFF", "0"]:
                    return ("+ STEREO STABILITY", "Zero motion-to-photon lag; headset reprojection works cleanly without distortion.",
                            "- REQUIRES RAW FPS", "Demands pure native rendering performance from hardware.")
                else:
                    return ("+ HIGH RAW FPS", "Interpolated frames generated.",
                            "- HEAD WARPING", "Severe stereo disorientation and tracking artifacting in VR headsets.")

        if key == "framerate_multiplier":
            return ("+ STABLE CADENCE", "Even 1:1 interpolated frame cadence.",
                    "- FIXED RATIO", "Single interpolation pass per rendered frame.")

        if key == "reprojection_mode":
            if "OFF" in v_upper or v_upper == "0":
                return ("+ ZERO WARPING", "Pure native rendering: razor-sharp cockpit dials, zero propeller distortion, and zero conflict with OFXR Bridge.",
                        "- RAW FPS REQUIRED", "Demands consistent native framerate from GPU/CPU.")
            elif "AUTO" in v_upper:
                return ("+ DYNAMIC SMOOTHING", "Engages reprojection only when framerate drops below headset refresh rate.",
                        "- OCCASIONAL WARP", "Minor edge warping during dynamic transitions.")
            elif "1/2" in v_upper:
                return ("+ LOCKED 1/2 CADENCE", "Divides framerate target by 2 for predictable airliner smoothness on high-refresh headsets.",
                        "- CANOPY WOBBLE", "Noticeable heat-haze style warping along canopy frames and propeller arcs.")
            else:
                return ("+ REPROJECTION ACTIVE", "Motion vector synthesis enabled.",
                        "- HIGH COMPOSITOR LOAD", "Increased compositor overhead in headset runtime.")

        if key == "vsync":
            if "ON" in v_upper:
                return ("+ ZERO TEARING", "Eliminates horizontal screen tears during rapid camera pans.",
                        "- BUFFER CADENCE", "Locks buffer presentation strictly to display scan cycles.")
            else:
                return ("+ DIRECT BUFFER", "Immediate buffer presentation without waiting for refresh cycle.",
                        "- SCREEN TEARING", "Noticeable horizontal visual tears across runway lines during camera movement.")

        if key == "vsync_interval":
            if "50%" in v_upper or "1/2" in v_upper:
                return ("+ PERFECT 1/2 CADENCE", "Stable frame times without GPU overheating or erratic queue spikes.",
                        "- 1/2 FPS CEILING", f"Caps framerate to {screen_hz // 2} FPS.")
            elif "100%" in v_upper or "1/1" in v_upper:
                return ("+ FULL REFRESH", f"Maximum motion smoothness up to {screen_hz} FPS.",
                        "- HIGH GPU LOAD", "Increased GPU thermals and higher risk of MainThread drop hitches.")
            else:
                return ("+ ROCK-SOLID STABILITY", "Ultra-safe frametime headroom for complex airliner operations.",
                        "- REDUCED FLUIDITY", "Noticeably lower display refresh cadence.")

        if key == "dynamic_settings":
            if "OFF" in v_upper or v_upper == "0":
                return ("+ CRISP COCKPIT", "Guaranteed 100% render scale; instruments and labels remain razor-sharp.",
                        "- NO AUTO THROTTLE", "GPU will not downscale resolution automatically during heavy scenes.")
            else:
                return ("+ DYNAMIC RELIEF", "Downscales internal render resolution when GPU is saturated.",
                        "- BLURRY DISPLAYS", "Cockpit avionics blur unpredictably during low approaches.")

        if key == "reflex":
            if "ON" in v_upper:
                return ("+ MIN INPUT LAG", "Drains GPU render queue for instantaneous flight control response.",
                        "- PEAK GPU CLOCK", "Keeps GPU memory and core clocks at performance state.")
            else:
                return ("+ STANDARD POWER", "Standard power and clock management.",
                        "- SLUGGISH CONTROLS", "Higher control latency during critical landing flares.")

        if key == "texture_resolution":
            if is_liner:
                if "LOW" in v_upper:
                    return ("+ FREES 6-8GB VRAM", "VRAM optimization: prevents D3D12 paging freezes at heavy hubs while vector instruments stay sharp.",
                            "- SOFTER LIVERY", "Slightly softer exterior airframe and apron asphalt decals up close.")
                elif "MEDIUM" in v_upper:
                    return ("+ BALANCED VRAM", "Sharper exterior liveries and ramp textures with moderate VRAM margin.",
                            "- 3-4GB VRAM LOAD", "Moderate VRAM consumption; safe on 16+ GB GPUs.")
                else:
                    return ("+ MAXIMUM DETAIL", "Ultra-sharp ground markings and exterior paint rivets.",
                            "- D3D12 STUTTERS", "High risk of VRAM paging stutters and CTD at payware hubs.")
            else:
                if any(k in v_upper for k in ["HIGH", "ULTRA"]):
                    return ("+ ULTRA REALISM", "Photorealistic cockpit placards, upholstery, and runway surface.",
                            "- MODERATE VRAM", "Higher VRAM footprint, easily sustained by GA aircraft.")
                else:
                    return ("+ LOW MEMORY", "Very light memory footprint.",
                            "- BLURRY CABIN", "Visible texture blurring on cockpit labels and close ground.")

        if key == "tlod":
            try:
                num = int(''.join(filter(str.isdigit, val_str)) or 100)
            except Exception:
                num = 100
            if is_liner:
                if autofps or num <= 120:
                    return ("+ FLUID FLARE", "Protects CPU MainThread; prevents landing micro-stutters at dense airports.",
                            "- DRAW DISTANCE", "Distant mountain meshes and urban autogen simplified.")
                else:
                    return ("+ DISTANT DETAIL", "Crisp mountain peaks and urban skylines visible from 50 NM.",
                            "- MAINTHREAD LAG", "Heavy CPU MainThread saturation causes stutters on short final.")
            else:
                if autofps or num >= 150:
                    return ("+ VFR TOPOGRAPHY", "Sharp ridgelines, valleys, and roads for visual navigation.",
                            "- CPU DRAW CALLS", "Higher CPU overhead, easily handled by GA aircraft.")
                else:
                    return ("+ HIGH FPS", "Maximum framerate for low-end CPUs.",
                            "- SIMPLIFIED RELIEF", "Terrain geometry pops in closer during low-altitude flights.")

        if key == "olod":
            try:
                num = int(''.join(filter(str.isdigit, val_str)) or 100)
            except Exception:
                num = 100
            if num <= 120:
                return ("+ LIGHT DRAWCALLS", "Frees CPU from rendering distant airport clutter and vehicles.",
                        "- PROXIMITY POP-IN", "Terminal buildings and jetways pop in closer to the field.")
            else:
                return ("+ DENSE AIRPORTS", "Terminal buildings, hangars, and light poles visible from afar.",
                        "- HEAVY DRAW CALLS", "Significantly increases CPU draw call overhead at major airports.")

        if key == "offscreen_precaching":
            if any(k in v_upper for k in ["HIGH", "ULTRA"]):
                return ("+ SMOOTH PANNING", "Zero stutter when panning camera left/right around cockpit.",
                        "- 1-2GB RAM USAGE", "Retains more scenery geometry in system RAM and VRAM.")
            else:
                return ("+ LOW RAM FOOTPRINT", "Unloads offscreen objects immediately.",
                        "- PANNING FREEZES", "Noticeable micro-freezes every time camera rotates.")

        if key == "volumetric_clouds":
            if "HIGH" in v_upper:
                return ("+ 15% CLOUD FPS", "Near-identical raymarched fidelity with strong GPU headroom in storm fronts.",
                        "- SUBTLE NOISE", "Minor raymarching edge softness in dense overcast layers.")
            elif "ULTRA" in v_upper:
                return ("+ DENSE VOXELS", "Maximum cloud volume density and sharpest boundary scattering.",
                        "- HEAVY GPU FILL", "Significant GPU framerate drop during heavy overcast approaches.")
            else:
                return ("+ MAX CLOUD FPS", "Lightweight raymarching passes.",
                        "- GRAINY EDGES", "Pixelated cloud boundaries and flatter atmospheric lighting.")

        if key in ["buildings", "vector_data_buildings"]:
            if is_vr:
                if any(k in v_upper for k in ["LOW", "MEDIUM"]):
                    return ("+ VR REPROJECTION SAFETY", "Lightweight autogen geometry protects stereo frame budget and saves VRAM.",
                            "- BASIC ROOF DETAILS", "Autogen city buildings use simplified roof geometry and facade textures.")
                elif "HIGH" in v_upper:
                    return ("+ CRISP AUTOGEN CITIES", "Detailed urban building facades and varied architectural models.",
                            "- STEREO DRAW CALLS", "Higher vertex pass in both eye viewports; moderate VRAM allocation.")
                else: # ULTRA
                    return ("+ MAXIMUM ARCHITECTURE", "Dense autogen facades, detailed dormers, and rooftop HVAC geometry.",
                            "- HEAVY STEREO LOAD", "Excessive stereo geometry and VRAM consumption; risks VR reprojection stutter.")
            else: # 2D Desktop
                if "ULTRA" in v_upper:
                    return ("+ MAXIMUM ARCHITECTURE", "Dense autogen facades, detailed dormers, and rooftop HVAC geometry.",
                            "- VRAM ALLOCATION", "Consumes additional video memory and geometry bandwidth around dense hubs.")
                elif "HIGH" in v_upper:
                    return ("+ CRISP AUTOGEN CITIES", "Detailed urban building facades and varied architectural models.",
                            "- MINOR DRAW CALLS", "Slightly higher polygon count for autogen cities.")
                elif "MEDIUM" in v_upper:
                    return ("+ BALANCED PERFORMANCE", "Balanced urban density with low VRAM footprint and swift draw call dispatch.",
                            "- SIMPLIFIED ROOFS", "Slightly simplified roof geometry on residential buildings.")
                else: # LOW
                    return ("+ MINIMAL VRAM & DRAW", "Lightweight geometry and low VRAM footprint for constrained hardware.",
                            "- FLAT GEOMETRY", "Boxy autogen buildings and low-detail facade textures.")

        if key == "trees":
            if is_vr:
                if any(k in v_upper for k in ["LOW", "MEDIUM"]):
                    return ("+ STEREO RASTER RELIEF", "Reduces double-eye foliage rasterization to secure locked VR frame pacing.",
                            "- SPARSITY ON APPROACH", "Canopy density is slightly reduced in suburban and woodland areas.")
                elif "HIGH" in v_upper:
                    return ("+ DENSE CANOPIES", "Full 3D tree volume and realistic foliage shading.",
                            "- STEREO FILL PENALTY", "Higher raster fill rate cost across continuous forests in VR.")
                else: # ULTRA
                    return ("+ MAXIMUM WOODLAND", "Photorealistic foliage density and shadow self-occlusion.",
                            "- SEVERE STEREO COST", "Heavy double-eye fragment shading; risks dropping out of reprojection.")
            else: # 2D Desktop
                if "ULTRA" in v_upper:
                    return ("+ LUSH 3D CANOPIES", "Maximum foliage density, crown branches, and realistic self-shadowing.",
                            "- FOREST RASTER COST", "Higher fragment shading cost when flying low over extensive forests.")
                elif "HIGH" in v_upper:
                    return ("+ REALISTIC FORESTS", "Full 3D tree canopies, deep foliage shadows, and natural woodlots.",
                            "- MINOR GPU WORKLOAD", "Modest fill-rate cost over heavily forested approaches.")
                elif "MEDIUM" in v_upper:
                    return ("+ BALANCED FOLIAGE", "Good woodland coverage with low vertex and fill-rate footprint.",
                            "- MODERATE DENSITY", "Slightly thinner tree clusters at airport boundaries.")
                else: # LOW
                    return ("+ LIGHT FILL-RATE", "Sparse procedural foliage.",
                            "- THIN CANOPY", "Sparse tree clusters and visible LOD popping on approach.")

        if key == "grass":
            if is_liner:
                if any(k in v_upper for k in ["LOW", "MEDIUM"]):
                    return ("+ MAX RUNWAY FPS", "Eliminates millions of unnecessary 3D grass blade triangles on concrete runways.",
                            "- FLAT RUNWAY EDGE", "Flat turf texture along asphalt runway shoulders instead of 3D blades.")
                else:
                    return ("+ 3D WILDFLOWERS", "Dense 3D grass blades and flowers visible on runway shoulders.",
                            "- USELESS DRAWCALLS", "Wastes CPU draw calls and GPU fill rate on paved airliner operations.")
            else:
                if any(k in v_upper for k in ["HIGH", "ULTRA"]):
                    return ("+ BUSH REALISM", "Immersive 3D grass, flowers, and turf for grass runway landings.",
                            "- MODERATE GPU LOAD", "GPU fill rate impact when taxiing through dense grass fields.")
                else:
                    return ("+ MAX VEGETATION FPS", "Lightweight procedural vegetation pass.",
                            "- FLAT BUSH STRIPS", "Grass runways appear flat and painted without 3D depth.")

        if key == "water_waves":
            if any(k in v_upper for k in ["512", "1024", "HIGH", "ULTRA"]):
                return ("+ REALISTIC SWELLS", "High-resolution FFT ocean swells, whitecaps, and realistic reflections.",
                        "- COMPUTE SHADER", "Modest compute shader workload during coastal approaches.")
            else:
                return ("+ LIGHT COMPUTE", "Low FFT simulation overhead.",
                        "- REPETITIVE WAVES", "Flatter water surface with repetitive ripple patterns.")

        if key == "displacement_mapping":
            if "OFF" in v_upper or v_upper == "0":
                return ("+ SAVES VRAM", "Zero tessellation geometry overhead; saves memory bandwidth.",
                        "- FLAT RUNWAY CRACKS", "Runway pavement seams and cracks appear flat at wheel level.")
            else:
                return ("+ 3D TARMAC RELIEF", "Micro-relief on runway concrete and asphalt joints.",
                        "- EXTRA TESSELLATION", "Consumes VRAM and GPU tessellation cycles with zero airborne visibility.")

        if key == "glass_cockpits":
            if is_liner:
                if "HIGH" not in v_upper:
                    return ("+ SAVES 5-8MS CPU", "Throttles vector glass redraws, dramatically lowering CPU MainThread frame time.",
                            "- LOWER DISPLAY HZ", "PFD attitude indicator updates at half or quarter refresh rate.")
                else:
                    return ("+ SILKY 60HZ PFD", "Vector instruments redraw every single frame with zero stepped motion.",
                            "- SEVERE CPU STUTTERS", "Heavily overloads CPU MainThread on complex airliners like Fenix/PMDG.")
            else:
                if "HIGH" in v_upper:
                    return ("+ FLUID SYNTH VISION", "Smooth synthetic vision and Garmin G1000 flight director animation.",
                            "- MINOR CPU LOAD", "Easily sustained by GA aircraft with simple systems.")
                else:
                    return ("+ SAVES CPU CYCLES", "Throttles Garmin screen redraws.",
                            "- STEPPED GAUGES", "Stepped needle movement on digital engine and airspeed gauges.")

        if key == "shadow_maps":
            if is_vr:
                if any(k in v_upper for k in ["1024", "MEDIUM"]):
                    return ("+ VR DEPTH STABILITY", "Crisp cockpit pillar shadows with safe VRAM and zero reprojection drop.",
                            "- MODERATE EDGES", "Slightly softer shadow margins than high resolutions.")
                elif any(k in v_upper for k in ["1536", "HIGH"]):
                    return ("+ RAZOR SHADOWS", "Sharp canopy, frame, and wing shadows without shimmering jagged edges.",
                            "- HIGHER VRAM", "Allocates larger shadow depth textures in VR.")
                elif any(k in v_upper for k in ["512", "LOW"]):
                    return ("+ MINIMAL VRAM USAGE", "Small shadow texture footprint.",
                            "- JAGGED SHADOWS", "Pixelated, shimmering shadow borders across cockpit dashboard.")
                else: # 2048 / ULTRA
                    return ("+ PINPOINT SHADOWS", "Ultra-crisp shadow lines across cockpit and airframe.",
                            "- VR REPROJECTION RISK", "4x depth buffer cost and raster passes; risks VR pacing drops.")
            else: # 2D Desktop
                if any(k in v_upper for k in ["1536", "2048", "HIGH", "ULTRA"]):
                    return ("+ RAZOR SHADOWS", "Sharp canopy, frame, and wing shadows without shimmering jagged edges.",
                            "- VRAM SHADOW MAP", "Allocates larger shadow depth textures in VRAM.")
                elif any(k in v_upper for k in ["1024", "MEDIUM"]):
                    return ("+ BALANCED SHADOWS", "Good shadow definition with minimal VRAM and raster overhead.",
                            "- SLIGHT SOFTNESS", "Shadow borders slightly softer on long throw angles.")
                else:
                    return ("+ LOW VRAM USAGE", "Small shadow texture footprint.",
                            "- JAGGED SHADOWS", "Pixelated, shimmering shadow borders across cockpit dashboard.")

        if key == "terrain_shadows":
            if any(k in v_upper for k in ["512", "1024", "HIGH", "ULTRA"]):
                return ("+ ALPINE RELIEF", "Dramatic mountain ridge self-shadowing during sunrise and sunset.",
                        "- HEIGHTFIELD LOAD", "GPU heightfield raymarching overhead in mountainous terrain.")
            else:
                return ("+ FAST MOUNTAINS", "Simplified terrain shadowing.",
                        "- WASHED MOUNTAINS", "Flatter mountain ridges with reduced depth during low sun angles.")

        if key == "contact_shadows":
            if any(k in v_upper for k in ["HIGH", "ULTRA"]):
                return ("+ TACTILE SWITCHES", "Crisp contact ambient shadows under cockpit switches, levers, and tires.",
                        "- SCREEN SHADER", "Subtle screen-space pass overhead (< 0.2 ms).")
            else:
                return ("+ MAX FILL RATE", "Minimal screen-space shading.",
                        "- FLOATING SWITCHES", "Cockpit dials and floor pedals look slightly disconnected or floating.")

        if key in ["ambient_occlusion", "ssao"]:
            if is_vr:
                if any(k in v_upper for k in ["LOW", "MEDIUM"]):
                    return ("+ STEREO COMPUTE SAVINGS", "Natural cockpit shadow depth with low per-eye shader cost.",
                            "- SOFT OCCLUSION", "Slightly diffuse crevice shading.")
                elif "HIGH" in v_upper:
                    return ("+ DEEP COCKPIT CREVICES", "Maximum contact shadow depth in cockpit footwells and crevices.",
                            "- STEREO SHADER LOAD", "Raymarched SSAO computed per eye adds GPU frametime in VR.")
                elif "ULTRA" in v_upper:
                    return ("+ FULL AMBIENT SHIFT", "Extreme contact shadow contrast in all crevices.",
                            "- VR REPROJECTION RISK", "Heavy per-eye compute pass threatens VR reprojection budget.")
                else: # OFF
                    return ("+ ZERO SHADER COST", "Completely disables screen-space ambient occlusion passes.",
                            "- WASHED COCKPIT", "Cockpit interior corners look flat and overly bright.")
            else: # 2D Desktop
                if any(k in v_upper for k in ["HIGH", "ULTRA"]):
                    return ("+ NATURAL COCKPIT", "Deep crevice and corner shading; authentic enclosed cockpit feel.",
                            "- POST-PROCESS GPU", "Requires full screen-space ambient occlusion compute pass.")
                elif "MEDIUM" in v_upper:
                    return ("+ BALANCED SSAO", "Natural ambient shading with low GPU compute cost.",
                            "- MODERATE DEPTH", "Slightly less pronounced shading in deep floor recesses.")
                else:
                    return ("+ SAVES GPU FILL", "Light ambient shading pass.",
                            "- WASHED COCKPIT", "Cockpit interior corners look flat and overly bright.")

        if key == "reflections_ssr":
            if not is_vr:
                if any(k in v_upper for k in ["HIGH", "ULTRA"]):
                    return ("+ WET TARMAC GLOW", "Realistic wet apron puddle reflections and canopy rain sheen.",
                            "- 1-2 MS GPU TIME", "Screen space raymarching overhead on wet runways.")
                else:
                    return ("+ HIGH WET FPS", "Prevents frame drops during heavy rainy landings.",
                            "- MATTE WATER", "Water puddles and windshield appear matte with minimal reflections.")
            else:
                if any(k in v_upper for k in ["LOW", "OFF"]):
                    return ("+ STEREO FILL RATE", "Crucial for maintaining locked 45/60 FPS in VR headsets.",
                            "- LIMITED REFLECTIONS", "Simplified cockpit glass reflections.")
                else:
                    return ("+ VIVID WET APRON", "Glossy wet reflections.",
                            "- REPROJECTION DROPS", "Heavy stereo reflection overhead drops headset into reprojection.")

        if key == "volumetric_lights":
            if any(k in v_upper for k in ["HIGH", "ULTRA"]):
                return ("+ DRAMATIC BEAMS", "Atmospheric light scattering through fog, mist, and night clouds for CAT III.",
                        "- LIGHT VOLUME GPU", "Compute cost when intersecting multiple dense light shafts.")
            else:
                return ("+ FAST NIGHT FPS", "Smooth frame delivery at busy illuminated night airports.",
                        "- FAINT SHAFTS", "Landing light beams look faint and less atmospheric in thick fog.")

        if key == "anisotropic_filtering":
            if "16X" in v_upper:
                return ("+ SHARP RUNWAY LINES", "Razor-sharp runway threshold, centerline, and touchdown markings at acute angles.",
                        "- TRIVIAL MEMORY BW", "Negligible < 0.1 ms impact on any modern GPU.")
            else:
                return ("+ MINIMAL BW", "Minimal memory bandwidth.",
                        "- BLURRY RUNWAY", "Runway centerlines and touchdown markers blur into mud ahead of aircraft.")

        if key == "windshield_effects":
            if any(k in v_upper for k in ["HIGH", "ULTRA"]):
                return ("+ VIVID RAIN & ICE", "Dynamic rain rivulets, wiper blade clearance, and icing accretion.",
                        "- SHADER OVERHEAD", "Glass distortion shader pass during heavy precipitation.")
            else:
                return ("+ HIGH STORM FPS", "Lower shader overhead during thunderstorm flights.",
                        "- COARSE WATER DROPS", "Simpler, less realistic raindrop physics on the glass.")

        if key == "raytraced_shadows":
            if "OFF" in v_upper or v_upper == "0":
                return ("+ PRESERVES RT CORES", "Frees GPU RT cores for DLSS frame generation and maintains peak framerate.",
                        "- STANDARD SHADOWS", "Cockpit and landing gear shadows use depth raster maps.")
            else:
                return ("+ PRECISE CONTACT SHADOWS", "Raytraced shadow penumbra under wheels and wings.",
                        "- HEAVY RT LOAD", "Substantial GPU frame time cost; severe hazard in VR stereo.")

        if key == "primary_scaling_vr":
            if "100%" in v_upper:
                return ("+ CRISP DLSS INPUT", "Full native 1:1 input into DLSS tensor reconstruction for razor-sharp avionics.",
                        "- NATIVE STEREO LOAD", "Standard stereo raster pixel workload.")
            else:
                return ("+ LIGHTER STEREO FILL", "Slightly reduces stereo pixel rasterization.",
                        "- DOUBLE DOWNSCALE BLUR", "Degrades image before DLSS upscaling, blurring cockpit instruments.")

        if key == "sharpen_amount_vr":
            try:
                val_flt = float(val_str)
            except Exception:
                val_flt = 0.2
            if val_flt <= 0.5:
                return ("+ CLEAN EDGES", "Clear avionics and runway lines without shimmering high-frequency noise.",
                        "- SUBTLE SHARPNESS", "Natural edge contrast.")
            else:
                return ("+ HIGH CONTRAST", "Pronounced edge separation.",
                        "- SHIMMERING JITTER", "Harsh sparkling noise on horizon lines and runway centerlines.")

        if key == "foveated_rendering":
            if "ON" in v_upper or v_upper == "1":
                return ("+ 10-15% GPU HEADROOM", "Variable Rate Shading reduces peripheral workload, securing VR 1/2 sync.",
                        "- PERIPHERAL SHADING", "Subtly lower shading resolution in far peripheral eye vision.")
            else:
                return ("+ UNIFORM SHADING", "Full shading across entire headset field of view.",
                        "- WASTED STEREO FILL", "GPU wastes cycles shading peripheral pixels where the eye cannot focus.")

        if key == "cubemap_reflections":
            if any(k in v_upper for k in ["128", "192", "256"]):
                return ("+ GLOSSY COCKPIT", "Crisp reflections across canopy glass, dials, and throttle levers with safe VRAM.",
                        "- PROBE MEMORY", "Controlled cubemap probe memory allocation.")
            else:
                return ("+ SAVES VRAM", "Minimal cubemap probe buffer footprint.",
                        "- DULL GLASS", "Reflective cockpit dials appear matte or low-resolution.")

        if key in ["dof", "motion_blur"]:
            if "OFF" in v_upper or v_upper == "0":
                return ("+ RAZOR-SHARP GAUGES", "Crystal clear avionics and runway centerlines during all flight phases.",
                        "- NO CINEMATIC BLUR", "Pure sharp flight deck view without camera velocity streaking.")
            else:
                return ("+ CINEMATIC DEPTH", "Motion or depth blurring for screenshots.",
                        "- SMEARED DIALS", "Smears critical flight data tapes and runway thresholds during maneuvers.")

        if key == "particles":
            if any(k in v_upper for k in ["LOW", "MEDIUM"]):
                return ("+ SAFE ALPHA FILL", "Realistic tire touchdown smoke and contrails without GPU fill-rate stalling.",
                        "- CONTROLLED DENSITY", "Slightly lower particle density in thick smoke plumes.")
            else:
                return ("+ VOLUMETRIC SMOKE", "Massive particle clouds for thrust reversers and fire effects.",
                        "- ALPHA STALL RISK", "Significant framerate drop when camera passes through dense smoke.")

        if key in ["aircraft_traffic_quantity", "parked_aircraft_quantity", "airport_services_quantity"]:
            if any(k in v_upper for k in ["OFF", "LOW"]):
                return ("+ PROTECTS MAINTHREAD", "Frees vital CPU MainThread cycles, guaranteeing smooth 60+ FPS touchdown flare.",
                        "- CALMER AIRPORT", "Fewer AI aircraft and ground support vehicles moving on the apron.")
            else:
                return ("+ PACKED AIRPORT", "Bustling airport gates and busy taxiways.",
                        "- CPU BOTTLENECK", "Severe CPU MainThread saturation causing landing flare micro-stutters.")

        if key == "sea_traffic":
            if "OFF" in v_upper:
                return ("+ ZERO MARITIME LOAD", "Completely disables boat physics, pathfinding, and wake rendering.",
                        "- EMPTY WATERWAYS", "Coastal waters and ports will have no moving ships or ferries.")
            elif "LOW" in v_upper:
                return ("+ AUTHENTIC AI SHIPPING", "Official GAIST / Seafront standard: 100% custom AI ships with zero duplicate collisions.",
                        "- LIGHT BACKGROUND THREAD", "Low-priority maritime waypoint navigation active.")
            else:
                return ("+ DENSE BOATS", "Maximum vessel count in coastal areas.",
                        "- DUPLICATE COLLISIONS", "Causes default generic ships to overlap and collide with custom AI shipping.")

        if key == "road_traffic":
            if "OFF" in v_upper:
                return ("+ ZERO ROADWAY CPU", "Completely disables procedural car pathfinding, freeing CPU MainThread cycles.",
                        "- EMPTY FREEWAYS", "City highways and bridges will have no moving cars.")
            elif "LOW" in v_upper:
                return ("+ LIGHT ROADWAYS", "Light vehicle movement beneath approach corridors with negligible CPU overhead.",
                        "- SPARSE CARS", "Few moving cars on major highways.")
            else:
                return ("+ BUSY HIGHWAYS", "Dense procedural traffic flow across all urban roadways.",
                        "- CPU DISPATCH LOAD", "Continuous procedural vehicle thread dispatch on CPU MainThread.")

        if key in ["aircraft_traffic_variety", "parked_aircraft_variety", "airport_services_variety", "characters_variety"]:
            if any(k in v_upper for k in ["LOW", "MEDIUM"]):
                return ("+ SAVES VRAM & TEXTURES", "Limits unique 3D livery textures in memory, preventing PCIe bus thrashing.",
                        "- FEWER UNIQUE LIVERIES", "Some airline liveries or ground worker models may be duplicated across the gates.")
            else:
                return ("+ MAXIMUM LIVERY REALISM", "Diverse authentic airline liveries and unique 3D ground worker uniforms.",
                        "- VRAM SATURATION", "Can consume significant extra VRAM, risking memory paging stutters at complex airports.")

        if key == "characters_quantity":
            if any(k in v_upper for k in ["OFF", "LOW"]):
                return ("+ MINIMAL BONE ANIMATION", "Frees CPU MainThread cycles by eliminating or limiting animated tarmac personnel.",
                        "- SPARSE RAMP WORKERS", "Fewer animated baggage handlers and ground crew around the aircraft.")
            else:
                return ("+ LIVELY APRON CREW", "Dense animated ground crew, marshallers, and technicians around terminal stands.",
                        "- CPU SKELETAL OVERHEAD", "Heavy skeletal transform load on CPU MainThread.")

        if key == "characters_quality":
            if any(k in v_upper for k in ["LOW", "MEDIUM"]):
                return ("+ LIGHTWEIGHT MESHES", "Low-polygon character LODs reduce vertex transformation workload on CPU and GPU.",
                        "- SIMPLER WORKER MESH", "Ground personnel models have simpler clothing folds and facial meshes.")
            else:
                return ("+ DETAILED RAMP WORKERS", "High-polygon 3D meshes and high-resolution clothing for airport staff.",
                        "- WASTED VERTEX LOAD", "Heavy geometry complexity for personnel viewed from cockpit distances.")

        if key == "fauna_density":
            if any(k in v_upper for k in ["OFF", "LOW"]):
                return ("+ ZERO WILDLIFE CPU", "Eliminates animal herd spawning and bird flock navigation threads.",
                        "- NO WILDLIFE FLOCKS", "No animated birds or land animals in rural areas.")
            else:
                return ("+ ABUNDANT WILDLIFE", "Animated bird flocks and land animal herds in wilderness and farm areas.",
                        "- EXTRA CPU THREADS", "Active animal spawning and pathfinding overhead.")

        return ("+ BALANCED", "Maintains optimal frame delivery.", "- BASELINE LOAD", "Standard hardware utilization.")

    SETTING_HARDWARE_IMPACT_SCORES = {
        # Key: (cpu_score [1-12], gpu_score [1-12], cpu_note, gpu_note)
        "resolution": (1, 11, "Minimal CPU draw call workload.", "Massive pixel fill-rate and memory bus saturation."),
        "display_resolution": (1, 11, "Minimal CPU draw call workload.", "Massive pixel fill-rate and memory bus saturation."),
        "vr_resolution": (1, 12, "Negligible CPU overhead.", "Extreme dual-display stereo fill-rate load."),
        "anti_aliasing": (2, 8, "Reduces driver overhead via DLSS.", "AI tensor reconstruction or native supersampling."),
        "max_frame_rate": (3, 4, "Key governor for CPU MainThread pacing.", "Reduces GPU thermal dissipation and latency."),
        "vsync": (1, 2, "Zero CPU computation.", "Regulates frame buffer swaps without shading penalty."),
        "vsync_interval": (1, 2, "Zero CPU computation; stabilizes MainThread pacing.", "Regulates D3D12 swap chain presentation cadence."),
        "reflex": (3, 3, "Optimizes CPU render queue dispatch.", "Reduces GPU queue backlog for lower system latency."),
        "frame_generation": (1, 7, "Zero extra compute cycles on CPU MainThread.", "Optical flow accelerator compute pass on GPU."),
        "multiplier": (1, 5, "Zero CPU compute.", "Temporal interpolation buffer management on GPU."),
        "vr_reprojection": (3, 7, "Low compositor pacing overhead.", "Headset optical flow / depth reprojection pass."),
        "terrain_lod": (11, 7, "Heavy CPU MainThread draw calls & terrain tessellation.", "High vertex throughput and heightfield geometry."),
        "objects_lod": (10, 6, "Multiplies scene draw calls for airport & city objects.", "3D model polygon rasterization."),
        "buildings": (8, 7, "Generates CPU draw calls for urban autogen.", "Building textures and geometry rendering."),
        "trees": (7, 6, "Vegetation tree placement and instancing on CPU.", "Alpha-tested foliage quad rasterization."),
        "grass": (3, 4, "Ground clutter density dispatch.", "Foliage alpha blending on GPU."),
        "terrain_vector_data": (5, 4, "Vector road, shoreline, and water body calculations.", "Decal projection onto ground terrain."),
        "terrain_texture": (2, 11, "Low CPU compute; streams satellite aerial tiles.", "Massive VRAM footprint and memory bandwidth."),
        "vector_data_buildings": (7, 5, "Procedural city footprint generation on CPU.", "Extruded mesh building rasterization."),
        "texture_supersampling": (2, 8, "Low CPU impact.", "Texture filtering anisotropy and cache lookups."),
        "anisotropic_filtering": (1, 4, "Zero CPU compute.", "Texture sampler unit memory lookups on GPU."),
        "volumetric_clouds": (4, 11, "Light cloud placement and density dispatch.", "Heavy raymarching shader through 3D density fields."),
        "water_waves": (3, 8, "Simulation dispatch of water FFT grid.", "Complex ocean wave displacement and reflection shaders."),
        "shadow_maps": (6, 8, "CPU frustum culling and cascaded shadow draw calls.", "Cascaded shadow map depth rendering passes."),
        "terrain_shadows": (4, 7, "Terrain shadow boundary dispatch.", "Raymarched digital elevation shadow casting."),
        "contact_shadows": (2, 5, "Low CPU overhead.", "Screen-space depth buffer raymarching pass."),
        "windshield_effects": (1, 7, "Zero CPU physics compute.", "Procedural rain droplet physics and refraction on GPU."),
        "ambient_occlusion": (1, 9, "Negligible CPU overhead.", "Compute shader screen-space ambient occlusion (SSAO/GTAO)."),
        "cubemap_reflections": (2, 6, "Low.", "Local probe texture memory allocation and rendering."),
        "raytracing": (4, 12, "BVH tree acceleration structure management.", "Massive hardware DXR ray intersection shader passes."),
        "light_shafts": (1, 5, "Zero CPU compute.", "Volumetric atmospheric light scattering shader."),
        "bloom": (1, 3, "Zero CPU compute.", "Post-processing bright pixel bloom threshold filter."),
        "depth_of_field": (1, 4, "Zero CPU compute.", "Post-processing circle-of-confusion blur pass."),
        "motion_blur": (1, 4, "Zero CPU compute.", "Post-processing velocity buffer vector blur pass."),
        "lens_flare": (1, 2, "Zero CPU compute.", "Billboard flare sprite overlay pass."),
        "glass_cockpit_refresh": (9, 3, "Critical CPU load: HTML/JS avionics rendering per frame.", "2D canvas texture blit to cockpit MFD/PFD screens."),
        "particles": (4, 8, "Particle emitter simulation on CPU.", "Heavy transparent alpha fill-rate when inside smoke/clouds."),
        "aircraft_traffic_quantity": (12, 5, "Extreme: Full flight plans, ATC, avionics & physics for each plane.", "Aircraft exterior 3D models rendering."),
        "aircraft_traffic_variety": (2, 9, "Low CPU logic.", "Multiplies unique aircraft textures loaded into VRAM."),
        "parked_aircraft_quantity": (8, 5, "Draw calls for static aircraft placed at gates.", "Polygon and texture allocation for parked airframes."),
        "parked_aircraft_variety": (2, 7, "Low CPU compute.", "Static livery textures loaded into VRAM."),
        "airport_services_quantity": (7, 4, "Pathfinding and ground vehicle animation dispatch.", "Ground vehicle 3D models and lighting."),
        "airport_services_variety": (2, 5, "Low CPU compute.", "Service vehicle liveries and texture memory."),
        "road_traffic": (6, 3, "Freeway car pathfinding and traffic flow simulation.", "Low-polygon vehicle models on roadways."),
        "sea_traffic": (3, 3, "Maritime vessel waypoint navigation.", "Low-polygon boat models and wakes."),
        "characters_quantity": (5, 3, "Skeletal bone animation calculations on CPU.", "Character polygon meshes on airport tarmac."),
        "characters_variety": (2, 4, "Low CPU compute.", "Ramp agent uniform textures in memory."),
        "characters_quality": (3, 4, "Low CPU overhead.", "Character facial mesh polygon density."),
        "fauna_density": (2, 2, "Light animal herd spawning logic.", "Low-polygon wildlife models."),
        "seatbelt_visibility": (1, 1, "Zero CPU compute.", "Negligible polygon cost for cockpit harness straps.")
    }

    def make_setting_item(key, name, val, raw_val, shared, rating, color, label, tooltip, options, page=1, is_numeric=False, min_val=0, max_val=100, step=1, tag_reason=None, is_vr=False, pro_label=None, pro_desc=None, con_label=None, con_desc=None, rec_guidance=None, is_active=None, target_fps=None):
        clean_lbl = str(label).upper().replace('(', ' ').replace(')', ' ').replace('-', '').strip().split()[0] if str(label).strip() else "OPTIMUM"
        if clean_lbl in ["OFF", "INACTIVE", "DISABLED"]:
            clean_lbl = "OFF"
            color = "slate"
            rating = "acceptable"
        elif clean_lbl in ["NO", "NOGO", "RISK", "HAZARD", "ALERT"]:
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

        if not pro_label or not con_label:
            calc_pro, calc_pro_desc, calc_con, calc_con_desc = resolve_setting_tradeoff(key, val, is_liner, is_vr)
            pro_label = pro_label or calc_pro
            pro_desc = pro_desc or calc_pro_desc
            con_label = con_label or calc_con
            con_desc = con_desc or calc_con_desc

        info_db = SETTING_INFO_DATABASE.get(key, {})
        opt_ratings = calculate_option_ratings(key, options, is_liner, is_vr, vram_gb, target_vr_fps if is_vr else target_2d_fps, native_w=native_w, native_h=native_h, gpu=gpu, cpu=cpu)

        # Synchronize active rating, color, clean_lbl with opt_ratings if matched
        val_norm = str(val).strip().upper()
        matched_opt = None
        # Pass 1: Prioritize exact option match
        for opt_name, r_data in opt_ratings.items():
            if val_norm == str(opt_name).strip().upper():
                matched_opt = r_data
                break
        # Pass 2: Fallback to substring matching only if no exact match found
        if not matched_opt:
            for opt_name, r_data in opt_ratings.items():
                o_norm = str(opt_name).strip().upper()
                if len(val_norm) > 2 and (val_norm in o_norm or o_norm in val_norm):
                    matched_opt = r_data
                    break
        
        if clean_lbl == "OFF":
            rating = "acceptable"
            color = "slate"
            clean_lbl = "OFF"
        elif matched_opt:
            rating = matched_opt["rating"]
            color = matched_opt["color"]
            clean_lbl = rating.upper()
            if matched_opt.get("reason"):
                tag_reason = matched_opt["reason"]
        elif key in ["tlod", "olod", "terrain_lod", "objects_lod"]:
            is_af = autofps and key in ["tlod", "terrain_lod"]
            r_c, c_c, lbl_c, rsn_c = get_lod_rating_info(
                val, key, is_liner, is_vr, is_x3d, is_flagship_cpu, is_legacy_cpu,
                is_flagship_gpu, is_high_tier_gpu, is_entry_gpu, vram_gb, autofps=is_af
            )
            rating = r_c
            color = c_c
            clean_lbl = lbl_c
            tag_reason = rsn_c
            clean_digits = ''.join(filter(str.isdigit, str(val)))
            if clean_digits:
                opt_ratings[clean_digits] = {"rating": r_c, "color": c_c, "reason": rsn_c}

        # Dynamic Hardware Impact Scores (1-12) based on active val, GPU, CPU, VR
        c_score, g_score, c_dyn_note, g_dyn_note = calculate_dynamic_hardware_impact(
            key=key,
            val=val,
            gpu=gpu,
            cpu=cpu,
            is_vr=is_vr,
            is_liner=is_liner
        )

        imp_res = generate_rig_setting_implications(
            key=key,
            val=val,
            cpu=cpu,
            gpu=gpu,
            storage=storage,
            disp=active_disp,
            vr=vr_headset_info,
            is_liner=is_liner,
            is_vr=is_vr
        )
        c_note = imp_res.get("cpu_note") or c_dyn_note
        g_note = imp_res.get("gpu_note") or g_dyn_note
        rig_implications = imp_res.get("implications_html") or ""

        # Specific explanatory tooltips for badge mouseover
        if key == "anti_aliasing":
            if is_vr:
                if "PERFORMANCE" in val_norm:
                    tag_reason = "50% internal render: least taxing mode for the GPU, securing maximum framerate headroom in VR."
                elif "BALANCED" in val_norm:
                    tag_reason = "58% internal render: strong balance between high framerate pacing and sharp cockpit readability."
                elif "QUALITY" in val_norm:
                    tag_reason = "67% internal render: enhanced cockpit sharpness, but taxes GPU stereo frame times more heavily."
                elif "DLAA" in val_norm:
                    tag_reason = "HAZARD in VR: 100% native stereo AI workload severely overburdens GPU frametimes, causing motion reprojection collapse."
                elif "TAA" in val_norm:
                    tag_reason = "100% native stereo rasterization: heavy fill-rate workload, risks reprojection drops without AI acceleration."
                else:
                    tag_reason = "Stereo anti-aliasing evaluated for VR frame pacing."
            else:
                if "DLAA" in val_norm:
                    tag_reason = "100% native AI anti-aliasing via Tensor Cores: razor-sharp EFIS instruments with abundant GPU margin."
                elif "QUALITY" in val_norm:
                    tag_reason = "Tensor AI reconstruction frees 25-35% GPU shading time while keeping cockpit displays sharp."
                elif "BALANCED" in val_norm:
                    tag_reason = "Tensor AI upscaling balances high visual clarity with strong GPU framerate relief."
                elif "PERFORMANCE" in val_norm:
                    tag_reason = "Ultra-light 50% internal rasterization: maximum GPU framerate relief, securing locked cadence in heavy weather."
                else:
                    tag_reason = "Native raster anti-aliasing: sharp presentation with standard GPU shading workload."
        elif key == "reflections_ssr":
            if is_vr:
                if any(k in val_norm for k in ["LOW", "OFF"]):
                    tag_reason = "Saves vital stereo GPU fill rate and prevents reflection disparity in headset."
                else:
                    tag_reason = "High stereo raymarching pass risks headset frame pacing drops."
            else:
                if any(k in val_norm for k in ["HIGH", "ULTRA"]):
                    tag_reason = "Realistic wet tarmac and puddle reflections effortlessly computed by your GPU (~0.6ms)."
                elif "MEDIUM" in val_norm:
                    tag_reason = "Balanced wet surface reflections with moderate raymarching sample density."
                else:
                    tag_reason = "Wet runways look flat and dry; underutilizes your GPU's rasterization headroom with zero FPS gain."
        elif not tag_reason:
            tag_reason = f"Rated {clean_lbl} based on hardware pacing budget."

        res_item = {
            "key": key,
            "name": str(name).upper(),
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
            "tag_reason": tag_reason,
            "rec_guidance": rec_guidance,
            "tooltip": tooltip,
            "options": options,
            "option_ratings": opt_ratings,
            "info_desc": info_db.get("desc", tooltip),
            "info_cpu": info_db.get("cpu_impact", ""),
            "info_gpu": info_db.get("gpu_impact", ""),
            "cpu_score": c_score,
            "gpu_score": g_score,
            "cpu_note": c_note,
            "gpu_note": g_note,
            "rig_implications": rig_implications,
            "info_liner": info_db.get("liner_advice", ""),
            "info_ga": info_db.get("ga_advice", ""),
            "info_tradeoffs": info_db.get("tradeoffs", []),
            "pro_label": pro_label,
            "pro_desc": pro_desc,
            "con_label": con_label,
            "con_desc": con_desc
        }

        if is_active is not None:
            res_item["is_active"] = bool(is_active)
        if target_fps is not None:
            res_item["target_fps"] = int(target_fps)

        if key == "primary_scaling_vr" and vr_headset_info:
            if vr_headset_info.get("software_name"):
                res_item["software_name"] = vr_headset_info.get("software_name")
            if vr_headset_info.get("software_render_scale") is not None:
                res_item["software_render_scale"] = vr_headset_info.get("software_render_scale")
                res_item["software_render_scale_pct"] = vr_headset_info.get("software_render_scale_pct")

        return res_item

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
    aa_2d_raw = get_block_val(r'AntiAliasing\s+([^\r\n]+)', video, 'TAA').strip()
    dlss_2d_raw = get_block_val(r'DLSSMode\s+(\w+)', video, 'QUALITY').strip()
    aa_vr_raw = get_block_val(r'AntiAliasingVR\s+([^\r\n]+)', video, 'TAA').strip()
    dlss_vr_raw = get_block_val(r'DLSSModeVR\s+(\w+)', video, 'QUALITY').strip()

    if 'DLSS' in aa_2d_raw.upper():
        d_mode = dlss_2d_raw.capitalize() if dlss_2d_raw.upper() in ['QUALITY', 'BALANCED', 'PERFORMANCE', 'ULTRA_PERFORMANCE'] else 'Quality'
        val_aa_2d = f"DLSS ({d_mode})"
    elif 'DLAA' in aa_2d_raw.upper():
        val_aa_2d = "DLAA"
    else:
        val_aa_2d = "TAA"

    if 'DLSS' in aa_vr_raw.upper():
        d_mode_vr = dlss_vr_raw.capitalize() if dlss_vr_raw.upper() in ['QUALITY', 'BALANCED', 'PERFORMANCE', 'ULTRA_PERFORMANCE'] else 'Quality'
        val_aa_vr = f"DLSS ({d_mode_vr})"
    elif 'DLAA' in aa_vr_raw.upper():
        val_aa_vr = "DLAA"
    else:
        val_aa_vr = "TAA"

    aa_2d = aa_2d_raw
    aa_vr = aa_vr_raw


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

    # 6b. V-Sync Interval
    vsync_interval_raw = get_block_val(r'VSyncInterval\s+(\d+)', video, '')
    if vsync_interval_raw in ['1', '2', '3', '4']:
        interval_idx = int(vsync_interval_raw)
    else:
        fps_num = int(fps_2d) if (fps_2d and fps_2d.isdigit()) else 0
        if fps_num > 0 and screen_hz > 0:
            ratio = round(screen_hz / float(fps_num))
            interval_idx = min(4, max(1, ratio))
        else:
            interval_idx = 2 if screen_hz >= 120 else 1

    fps_100 = screen_hz
    fps_50 = screen_hz // 2
    fps_33 = screen_hz // 3
    fps_25 = screen_hz // 4

    vsync_interval_options = [
        f"100% ({fps_100} FPS)",
        f"50% ({fps_50} FPS)",
        f"33% ({fps_33} FPS)",
        f"25% ({fps_25} FPS)"
    ]

    interval_labels = {
        1: f"100% ({fps_100} FPS)",
        2: f"50% ({fps_50} FPS)",
        3: f"33% ({fps_33} FPS)",
        4: f"25% ({fps_25} FPS)"
    }
    vsync_interval_val = interval_labels.get(interval_idx, f"50% ({fps_50} FPS)")
    vsync_interval_raw_str = str(interval_idx)

    if interval_idx == 2:
        vsi_rating, vsi_color, vsi_label = "optimum", "emerald", "OPTIMUM"
        vsi_reason = f"50% refresh rate ({fps_50} FPS): Golden standard for flight sim pacing without GPU saturation."
        vsi_guidance = f"50% ({fps_50} FPS) • Ideal 1:2 monitor cadence preventing frame pacing judder"
    elif interval_idx == 1:
        vsi_rating, vsi_color, vsi_label = "acceptable", "amber", "ACCEPTABLE"
        vsi_reason = f"100% refresh rate ({fps_100} FPS): High GPU workload; higher risk of stutter if CPU MainThread drops."
        vsi_guidance = f"100% ({fps_100} FPS) • Full monitor refresh rate (demands high GPU headroom)"
    elif interval_idx == 3:
        vsi_rating, vsi_color, vsi_label = "acceptable", "amber", "ACCEPTABLE"
        vsi_reason = f"33% refresh rate ({fps_33} FPS): Rock solid pacing for ultra-heavy airliners or 4K ultra graphics."
        vsi_guidance = f"33% ({fps_33} FPS) • 1:3 divisor for complex airliners at ultra-dense hubs"
    else:
        vsi_rating, vsi_color, vsi_label = "suboptimal", "orange", "SUBOPTIMAL"
        vsi_reason = f"25% refresh rate ({fps_25} FPS): Aggressive throttling; noticeable motion latency."
        vsi_guidance = f"25% ({fps_25} FPS) • Heavy throttle (emergency low-power mode)"

    # 7. Dynamic Settings
    dyn_2d = "ON" if get_block_val(r'DynamicSettings\s+(\d+)', video, '0') == '1' else "OFF"
    dyn_vr = "ON" if get_block_val(r'DynamicSettingsVR\s+(\d+)', video, '0') == '1' else "OFF"

    # 8. NVIDIA Reflex Low Latency
    reflex_2d_raw = get_block_val(r'Reflex\s+([^\r\n]+)', video, 'ON').upper().replace(' ', '')
    reflex_2d = "ON+BOOST" if "BOOST" in reflex_2d_raw else ("ON" if reflex_2d_raw in ["ON", "1"] else "OFF")
    reflex_vr_raw = get_block_val(r'ReflexVR\s+([^\r\n]+)', video, 'ON').upper().replace(' ', '')
    reflex_vr = "ON+BOOST" if "BOOST" in reflex_vr_raw else ("ON" if reflex_vr_raw in ["ON", "1"] else "OFF")

    # 9. Texture Quality (MSFS inverted mip-drop scale: 0=Ultra, 1=High, 2=Medium, 3=Low)
    tex_q_map = {'0': 'Ultra', '1': 'High', '2': 'Medium', '3': 'Low'}
    tex_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{Texture'), '1')
    tex_2d_val = tex_q_map.get(tex_2d_raw, 'High')
    tex_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{Texture'), '2')
    tex_vr_val = tex_q_map.get(tex_vr_raw, 'Medium')

    # Texture 2D Rating
    if is_liner:
        if tex_2d_val == "Low":
            tex_2d_rating, tex_2d_color, tex_2d_label = "optimum", "emerald", "OPTIMUM"
            tex_2d_tip = "Description: Base texture map resolution for scenery, airports, and cockpits.\nCurrent: LOW saves 6-8 GB VRAM, preventing D3D12 paging freezes at busy hubs while cockpit vector screens remain sharp.\nRecommendation: Maintain LOW for all airliner flights (VRAM Optimization)."
            tex_2d_reason = "VRAM Optimization: saves 6-8 GB VRAM, preventing D3D12 paging freezes at dense hubs while vector instruments stay sharp."
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
            tex_vr_tip = "Description: Base texture map resolution in VR stereo rendering.\nCurrent: LOW frees 6-8 GB VRAM, preventing VR compositor crashes and paging stutters while cockpit vector instruments stay crisp.\nRecommendation: Maintain LOW for all airliner flights in VR (VRAM Optimization)."
            tex_vr_reason = "VRAM Optimization in VR: frees 6-8 GB VRAM, preventing VR compositor crashes and paging stutters."
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
    is_vr_fps_off = (fps_vr == '0' or str(fps_vr).upper() == 'OFF')
    vr_fps_rating = "optimum" if is_vr_fps_opt else ("acceptable" if is_vr_fps_off else "suboptimal")
    vr_fps_color = "emerald" if is_vr_fps_opt else ("slate" if is_vr_fps_off else "orange")
    vr_fps_label = "OPTIMUM" if is_vr_fps_opt else ("OFF" if is_vr_fps_off else "SUBOPTIMAL")
    vr_fps_tooltip = f"Description: VR frame rate cap in UserCfg.opt to synchronize with headset reprojection interval. Direct numeric input supported.\nCurrent: {'OFF (Uncapped)' if is_vr_fps_off else f'{fps_vr} FPS'}.\nRecommendation: Lock to {target_vr_fps} FPS (exact 1/2 sync divisor of your {vr_hz} Hz headset) to guarantee judder-free motion reprojection."
    vr_fps_reason = f"Matches exact 1/2 sync divisor of {vr_hz} Hz headset ({target_vr_fps} FPS), delivering smooth motion reprojection." if is_vr_fps_opt else (f"VR frame rate is uncapped (OFF). Locking to {target_vr_fps} FPS is recommended for reprojection." if is_vr_fps_off else f"Target frame rate ({fps_vr} FPS) does not match the 1/2 sync divisor ({target_vr_fps} FPS) of your {vr_hz} Hz headset, causing motion judder.")

    # ===============================================
    # PAGE 2: TERRAIN & ENVIRONMENT WORLD (9 SETTINGS)
    # ===============================================

    # 10. TLOD (Manual input up to 400 + Presets)
    tlod_2d_raw = get_block_val(r'LoDFactor\s+([\d\.]+)', extract_block(g2d, '{Terrain'), '1.0')
    tlod_2d_val = round(float(tlod_2d_raw) * 100)
    tlod_vr_raw = get_block_val(r'LoDFactor\s+([\d\.]+)', extract_block(gvr, '{Terrain'), '1.0')
    tlod_vr_val = round(float(tlod_vr_raw) * 100)

    # TLOD Ratings (Calibrated via get_lod_rating_info)
    tlod_2d_rating, tlod_2d_color, tlod_2d_label, tlod_2d_reason = get_lod_rating_info(
        tlod_2d_val, "tlod", is_liner, False, is_x3d, is_flagship_cpu, is_legacy_cpu,
        is_flagship_gpu, is_high_tier_gpu, is_entry_gpu, vram_gb, autofps=autofps
    )
    tlod_vr_rating, tlod_vr_color, tlod_vr_label, tlod_vr_reason = get_lod_rating_info(
        tlod_vr_val, "tlod", is_liner, True, is_x3d, is_flagship_cpu, is_legacy_cpu,
        is_flagship_gpu, is_high_tier_gpu, is_entry_gpu, vram_gb, autofps=autofps
    )

    # 11. OLOD (Manual input up to 400 + Presets)
    olod_2d_raw = get_block_val(r'LoDFactor\s+([\d\.]+)', extract_block(g2d, '{ObjectsLoD'), '1.0')
    olod_2d_val = round(float(olod_2d_raw) * 100)
    olod_vr_raw = get_block_val(r'LoDFactor\s+([\d\.]+)', extract_block(gvr, '{ObjectsLoD'), '1.0')
    olod_vr_val = round(float(olod_vr_raw) * 100)

    # OLOD Ratings (Calibrated via get_lod_rating_info)
    olod_2d_rating, olod_2d_color, olod_2d_label, olod_2d_reason = get_lod_rating_info(
        olod_2d_val, "olod", is_liner, False, is_x3d, is_flagship_cpu, is_legacy_cpu,
        is_flagship_gpu, is_high_tier_gpu, is_entry_gpu, vram_gb, autofps=False
    )
    olod_vr_rating, olod_vr_color, olod_vr_label, olod_vr_reason = get_lod_rating_info(
        olod_vr_val, "olod", is_liner, True, is_x3d, is_flagship_cpu, is_legacy_cpu,
        is_flagship_gpu, is_high_tier_gpu, is_entry_gpu, vram_gb, autofps=False
    )

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
    fps_options = ["30", "36", "40", "45", "60", "72", "80", "82", "90", "120", "144", "165", "180", "240"]
    lod_options = ["50", "80", "100", "120", "150", "180", "200", "250", "300", "350", "400"]
    q_options = ["Ultra", "High", "Medium", "Low"]
    tex_options = [
        "Ultra (Full 4K Texture Atlases • 14-16 GB Alloc)",
        "High (2K High-Res Textures • 9-11 GB Alloc)",
        "Medium (1K Compressed Textures • 6-8 GB Alloc)",
        "Low (512px Optimized Textures • 3-4 GB Alloc)"
    ]

    def format_tex_display(val: str) -> str:
        v = str(val).lower()
        if "ultra" in v:
            return "Ultra (Full 4K Texture Atlases • 14-16 GB Alloc)"
        if "high" in v:
            return "High (2K High-Res Textures • 9-11 GB Alloc)"
        if "medium" in v or "med" in v:
            return "Medium (1K Compressed Textures • 6-8 GB Alloc)"
        return "Low (512px Optimized Textures • 3-4 GB Alloc)"

    precaching_options = [
        "Ultra (Full 360° Scene Pre-Load • 32GB RAM & 24GB VRAM)",
        "High (90° Peripheral Arc • Balanced Memory Cache)",
        "Medium (Narrow Front Buffer • 16GB RAM Target)",
        "Low (Zero Pre-Caching • High Disk Streaming)"
    ]

    def format_precaching_display(val: str) -> str:
        v = str(val).lower()
        if "ultra" in v:
            return "Ultra (Full 360° Scene Pre-Load • 32GB RAM & 24GB VRAM)"
        if "high" in v:
            return "High (90° Peripheral Arc • Balanced Memory Cache)"
        if "medium" in v or "med" in v:
            return "Medium (Narrow Front Buffer • 16GB RAM Target)"
        return "Low (Zero Pre-Caching • High Disk Streaming)"

    disp_options = [
        "OFF (Flat Tarmac Mesh • Zero Tessellation Overhead)",
        "ON (3D Surface Tessellation • Heavy Vertex Shading)"
    ]

    def format_disp_display(val: str) -> str:
        v = str(val).upper()
        if "ON" in v and "OFF" not in v:
            return "ON (3D Surface Tessellation • Heavy Vertex Shading)"
        return "OFF (Flat Tarmac Mesh • Zero Tessellation Overhead)"
    glass_options = ["High (Full)", "Medium (Half)", "Low (Quarter)"]
    water_options = ["Ultra (1024)", "High (512)", "Medium (256)", "Low (128)"]
    shadow_options = ["Ultra (2048)", "High (1536)", "Medium (1024)", "Low (512)"]
    hf_options = ["Ultra (1024)", "High (512)", "Medium (256)", "Low (128)"]
    aniso_options = ["16X", "8X", "4X", "2X", "OFF"]
    aa_options_vr = [
        "DLSS (Performance • 50% Render • Maximum FPS)",
        "DLSS (Balanced • 58% Render • Stable 90Hz)",
        "DLSS (Quality • 67% Render • Sharp Cockpits)",
        "TAA (100% Native Raster • High Fill-Rate)",
        "DLAA (100% Native AI • Extreme GPU Load)"
    ]
    aa_options_2d = [
        "DLSS (Quality • 67% Render • Sweet Spot)",
        "DLAA (100% Native AI • Ultra Sharp)",
        "DLSS (Balanced • 58% Render • Low GPU Load)",
        "DLSS (Performance • 50% Render • Max FPS)",
        "TAA (100% Native Raster • Standard)"
    ]

    def format_aa_display(val: str, is_vr_mode: bool) -> str:
        v = str(val).upper()
        if is_vr_mode:
            if "PERFORMANCE" in v:
                return "DLSS (Performance • 50% Render • Maximum FPS)"
            if "BALANCED" in v:
                return "DLSS (Balanced • 58% Render • Stable 90Hz)"
            if "QUALITY" in v:
                return "DLSS (Quality • 67% Render • Sharp Cockpits)"
            if "DLAA" in v:
                return "DLAA (100% Native AI • Extreme GPU Load)"
            if "TAA" in v:
                return "TAA (100% Native Raster • High Fill-Rate)"
            return "DLSS (Performance • 50% Render • Maximum FPS)"
        else:
            if "QUALITY" in v:
                return "DLSS (Quality • 67% Render • Sweet Spot)"
            if "DLAA" in v:
                return "DLAA (100% Native AI • Ultra Sharp)"
            if "BALANCED" in v:
                return "DLSS (Balanced • 58% Render • Low GPU Load)"
            if "PERFORMANCE" in v:
                return "DLSS (Performance • 50% Render • Max FPS)"
            if "TAA" in v:
                return "TAA (100% Native Raster • Standard)"
            return "DLSS (Quality • 67% Render • Sweet Spot)"

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

    # 2D Max Frame Rate Rating
    is_2d_fps_opt = (fps_2d == str(target_2d_fps))
    is_2d_fps_off = (fps_2d == '0' or str(fps_2d).upper() == 'OFF')
    fps_2d_rating = "optimum" if is_2d_fps_opt else ("acceptable" if is_2d_fps_off else "suboptimal")
    fps_2d_color = "emerald" if is_2d_fps_opt else ("slate" if is_2d_fps_off else "orange")
    fps_2d_label = "OPTIMUM" if is_2d_fps_opt else ("OFF" if is_2d_fps_off else "SUBOPTIMAL")
    fps_2d_reason = f"Synchronized with {screen_hz} Hz monitor 1/2 divisor ({target_2d_fps} FPS) for zero judder." if is_2d_fps_opt else ("Max frame rate is OFF (uncapped). Frame pacing is free." if is_2d_fps_off else f"Target frame rate ({fps_2d} FPS) does not match the 1/2 sync divisor ({target_2d_fps} FPS) of your {screen_hz} Hz display.")

    # 1. Full Screen Resolution (Shared) Rating & Options
    cur_w, cur_h = 2560, 1440
    if res_raw:
        parts = res_raw.split()
        if len(parts) >= 2:
            try:
                cur_w, cur_h = int(parts[0]), int(parts[1])
            except Exception:
                pass

    if cur_w == native_w and cur_h == native_h:
        res_rating = "optimum"
        res_color = "emerald"
        res_label = "OPTIMUM"
        res_tag_reason = "Matches physical monitor native resolution for pixel-perfect 1:1 rendering."
    elif cur_w > native_w or cur_h > native_h:
        res_rating = "hazard"
        res_color = "rose"
        res_label = "HAZARD"
        res_tag_reason = f"Resolution ({cur_w}x{cur_h}) exceeds native monitor resolution ({native_w}x{native_h}). Causes severe GPU fillrate load."
    else:
        res_rating = "suboptimal"
        res_color = "orange"
        res_label = "SUBOPTIMAL"
        res_tag_reason = f"Resolution ({cur_w}x{cur_h}) is lower than native ({native_w}x{native_h}). Produces non-native scaling blur and soft fonts."

    base_res_options = ["3840 x 2160", "2560 x 1440", "1920 x 1080"]
    native_res_str = f"{native_w} x {native_h}"
    if native_res_str not in base_res_options:
        base_res_options.append(native_res_str)

    def res_key(r_str):
        try:
            toks = r_str.replace('x', ' ').replace('X', ' ').split()
            return int(toks[0]) * int(toks[1])
        except Exception:
            return 0
    res_options = sorted(list(set(base_res_options)), key=res_key, reverse=True)

    # 28. Raytraced Shadows
    rt_2d_raw = get_block_val(r'Enabled\s+(\d+)', extract_block(g2d, '{RaytracedShadows'), '0')
    rt_2d_val = "ON" if rt_2d_raw == '1' else "OFF"
    rt_vr_raw = get_block_val(r'Enabled\s+(\d+)', extract_block(gvr, '{RaytracedShadows'), '0')
    rt_vr_val = "ON" if rt_vr_raw == '1' else "OFF"

    # 29. VR Primary Scaling & Sharpening
    scale_vr_raw = get_block_val(r'PrimaryScalingVR\s+([\d\.]+)', video, '1.000000')
    try:
        scale_vr_pct = f"{round(float(scale_vr_raw) * 100)}%"
    except Exception:
        scale_vr_pct = "100%"

    sharpen_vr_raw = get_block_val(r'SharpenAmountVR\s+([\d\.]+)', video, '0.200000')
    try:
        sharpen_vr_val = f"{float(sharpen_vr_raw):.2f}"
    except Exception:
        sharpen_vr_val = "0.20"

    # 30. VR Foveated Rendering & Scale
    fov_vr_raw = get_block_val(r'FoveatedRendering\s+(\d+)', video, '1')
    fov_vr_val = "ON" if fov_vr_raw == '1' else "OFF"
    fov_scale_raw = get_block_val(r'FoveatedRenderingScale\s+([\d\.]+)', video, '0.400000')
    try:
        fov_scale_pct = f"{round(float(fov_scale_raw) * 100)}%"
    except Exception:
        fov_scale_pct = "40%"

    # 31. VR Reprojection Mode
    reproj_vr_raw = get_block_val(r'ReprojectionMode\s+(\d+)', video, '0')
    reproj_map = {'0': 'OFF', '1': 'AUTO', '2': '1/2 REPROJECTION', '3': '1/3 REPROJECTION', '4': 'DEPTH & MOTION'}
    reproj_vr_val = reproj_map.get(reproj_vr_raw, 'AUTO' if reproj_vr_raw == '1' else 'OFF')

    # 32. Cubemap Reflections (ReflectionProbe)
    cube_map = {'0': '64', '1': '128', '2': '192', '3': '256', '4': '512'}
    cube_2d_raw = get_block_val(r'Size\s+(\d+)', extract_block(g2d, '{ReflectionProbe'), '2')
    cube_2d_val = cube_map.get(cube_2d_raw, '192')
    cube_vr_raw = get_block_val(r'Size\s+(\d+)', extract_block(gvr, '{ReflectionProbe'), '1')
    cube_vr_val = cube_map.get(cube_vr_raw, '128')

    # 33. Depth Of Field (DOF)
    dof_2d_block = extract_block(g2d, '{DOF')
    dof_2d_enabled = get_block_val(r'Enabled\s+(\d+)', dof_2d_block, '0')
    dof_2d_raw = get_block_val(r'Quality\s+(\d+)', dof_2d_block, '0')
    dof_2d_val = 'OFF' if dof_2d_enabled == '0' else q_map.get(dof_2d_raw, 'Low')

    dof_vr_block = extract_block(gvr, '{DOF')
    dof_vr_enabled = get_block_val(r'Enabled\s+(\d+)', dof_vr_block, '0')
    dof_vr_raw = get_block_val(r'Quality\s+(\d+)', dof_vr_block, '0')
    dof_vr_val = 'OFF' if dof_vr_enabled == '0' else q_map.get(dof_vr_raw, 'Low')

    # 34. Motion Blur
    mb_2d_block = extract_block(g2d, '{MotionBlur')
    mb_2d_enabled = get_block_val(r'Enabled\s+(\d+)', mb_2d_block, '0')
    mb_2d_raw = get_block_val(r'Quality\s+(\d+)', mb_2d_block, '0')
    mb_2d_val = 'OFF' if mb_2d_enabled == '0' else q_map.get(mb_2d_raw, 'Low')

    mb_vr_block = extract_block(gvr, '{MotionBlur')
    mb_vr_enabled = get_block_val(r'Enabled\s+(\d+)', mb_vr_block, '0')
    mb_vr_raw = get_block_val(r'Quality\s+(\d+)', mb_vr_block, '0')
    mb_vr_val = 'OFF' if mb_vr_enabled == '0' else q_map.get(mb_vr_raw, 'Low')

    # 35. Particles Quality
    part_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{Particles'), '1')
    part_2d_val = q_map.get(part_2d_raw, 'Medium')
    part_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{Particles'), '0')
    part_vr_val = q_map.get(part_vr_raw, 'Low')

    # Common Settings: Traffic, Characters, Fauna, Seatbelts
    traffic_qty_map = {'-1': 'OFF', '0': 'LOW', '1': 'MEDIUM', '2': 'HIGH', '3': 'ULTRA'}
    traffic_var_map = {'0': 'LOW', '1': 'MEDIUM', '2': 'HIGH', '3': 'ULTRA'}
    traffic_block = extract_block(g2d, '{Traffic')
    char_block = extract_block(g2d, '{Characters')
    fauna_block = extract_block(g2d, '{Fauna')
    seatbelt_block = extract_block(g2d, '{Seatbelts')

    # Aircraft Traffic Quantity & Variety
    air_qty_raw = get_block_val(r'AircraftTrafficQuantity\s+([-\d]+)', traffic_block, '-1')
    air_qty_val = traffic_qty_map.get(air_qty_raw, 'OFF')
    air_var_raw = get_block_val(r'AircraftTrafficVariety\s+([-\d]+)', traffic_block, '2')
    air_var_val = traffic_var_map.get(air_var_raw, 'HIGH')

    # Parked Aircraft Quantity & Variety
    park_qty_raw = get_block_val(r'ParkedAircraftQuantity\s+([-\d]+)', traffic_block, '-1')
    park_qty_val = traffic_qty_map.get(park_qty_raw, 'OFF')
    park_var_raw = get_block_val(r'ParkedAircraftVariety\s+([-\d]+)', traffic_block, '2')
    park_var_val = traffic_var_map.get(park_var_raw, 'HIGH')

    # Airport Services Quantity & Variety
    svc_qty_raw = get_block_val(r'AirportsServicesQuantity\s+([-\d]+)', traffic_block, '-1')
    svc_qty_val = traffic_qty_map.get(svc_qty_raw, 'OFF')
    svc_var_raw = get_block_val(r'AirportsServicesVariety\s+([-\d]+)', traffic_block, '1')
    svc_var_val = traffic_var_map.get(svc_var_raw, 'MEDIUM')

    # Road & Sea Traffic
    road_raw = get_block_val(r'RoadQuality\s+([-\d]+)', traffic_block, '1')
    road_val = traffic_qty_map.get(road_raw, 'MEDIUM')
    sea_raw = get_block_val(r'SeaQuality\s+([-\d]+)', traffic_block, '2')
    sea_val = traffic_qty_map.get(sea_raw, 'HIGH')

    # Characters Quantity, Variety, Quality
    char_qty_raw = get_block_val(r'Quantity\s+([-\d]+)', char_block, '1')
    char_qty_val = traffic_qty_map.get(char_qty_raw, 'MEDIUM')
    char_var_raw = get_block_val(r'Variety\s+([-\d]+)', char_block, '1')
    char_var_val = traffic_var_map.get(char_var_raw, 'MEDIUM')
    char_qlt_raw = get_block_val(r'Quality\s+([-\d]+)', char_block, '1')
    char_qlt_val = traffic_var_map.get(char_qlt_raw, 'MEDIUM')

    # Fauna Density
    fauna_raw = get_block_val(r'Quantity\s+([-\d]+)', fauna_block, '-1')
    fauna_val = traffic_qty_map.get(fauna_raw, 'OFF')

    # Seatbelts
    seatbelt_raw = get_block_val(r'Enabled\s+([-\d]+)', seatbelt_block, '1')
    seatbelt_val = "ON" if seatbelt_raw == '1' else "OFF"

    # Options Lists
    scale_vr_options = ["100%", "95%", "90%", "85%", "80%", "75%", "70%"]
    sharpen_vr_options = ["0.00", "0.20", "0.50", "1.00", "1.50"]
    fov_scale_options = ["30%", "40%", "50%", "60%", "70%"]
    reproj_options = ["OFF", "AUTO", "1/2 REPROJECTION", "1/3 REPROJECTION", "DEPTH & MOTION"]
    cube_options = ["512", "256", "192", "128", "64"]
    dof_options = ["OFF", "Low", "Medium", "High", "Ultra"]
    mb_options = ["OFF", "Low", "Medium", "High", "Ultra"]
    part_options = ["Ultra", "High", "Medium", "Low"]
    traffic_qty_options = ["OFF", "LOW", "MEDIUM", "HIGH", "ULTRA"]
    traffic_var_options = ["LOW", "MEDIUM", "HIGH", "ULTRA"]

    char_qty_is_opt = (char_qty_val == "OFF") if (is_legacy_cpu or is_vram_constrained) else (char_qty_val in ["OFF", "LOW"])
    char_var_is_opt = (char_var_val == "LOW")
    char_qlt_is_opt = (char_qlt_val == "LOW") if (is_legacy_cpu or is_vram_constrained) else (char_qlt_val in ["LOW", "MEDIUM"])
    sea_is_opt = (sea_val == "OFF") if is_entry_rig else (sea_val in ["OFF", "LOW"])

    # =========================================================================
    # BUILD COMMON MATRIX (Shared global settings - 3 Pages)
    # =========================================================================
    matrix_common = [
        # PAGE 1: TRAFFIC (6)
        make_setting_item("aircraft_traffic_quantity", "Aircraft Traffic Quantity", air_qty_val, air_qty_raw, True, "optimum" if air_qty_val == "OFF" else "acceptable", "emerald" if air_qty_val == "OFF" else "amber", "OPTIMUM" if air_qty_val == "OFF" else "ACCEPTABLE", "Description: Global live or AI aircraft density. Major consumer of CPU MainThread cycles at busy hubs.\nRecommendation: OFF or LOW for study-level airliner flights; MEDIUM for general aviation.", traffic_qty_options, page=1, tag_reason="Conserves MainThread cycles by limiting AI traffic simulation." if air_qty_val in ["OFF", "LOW"] else "High traffic quantity adds substantial MainThread CPU overhead.", rec_guidance="OFF (IFR Liners) or LOW/MEDIUM (VFR/GA)", is_vr=False),
        make_setting_item("aircraft_traffic_variety", "Aircraft Traffic Variety", air_var_val, air_var_raw, True, "optimum" if air_var_val == "LOW" else "acceptable", "emerald" if air_var_val == "LOW" else "amber", "OPTIMUM" if air_var_val == "LOW" else "ACCEPTABLE", f"Description: AI and injected traffic model/livery diversity (FSLTL, VATSIM, BATC, SayIntentions).\nCurrent: {air_var_val}.\nRecommendation: LOW for peak performance and minimal VRAM; MEDIUM/HIGH if visual airline diversity is desired on high-VRAM GPUs.", traffic_var_options, page=1, tag_reason="Minimal VRAM texture footprint and zero streaming hitching." if air_var_val == "LOW" else "Balanced airline liveries across injected traffic.", rec_guidance="LOW • Minimizes VRAM footprint and prevents hitching", is_vr=False),
        make_setting_item("parked_aircraft_quantity", "Parked Aircraft Quantity", park_qty_val, park_qty_raw, True, "optimum" if park_qty_val == "OFF" else "acceptable", "emerald" if park_qty_val == "OFF" else "amber", "OPTIMUM" if park_qty_val == "OFF" else "ACCEPTABLE", "Description: Static parked aircraft placed at airport gates and ramps.\nRecommendation: OFF eliminates duplicate static airframes and frees critical apron CPU draw calls.", traffic_qty_options, page=1, tag_reason="Eliminates static airframe clutter and apron draw calls." if park_qty_val == "OFF" else "Parked aircraft increase apron draw calls at terminals.", rec_guidance="OFF • Eliminates duplicate statics and frees apron draw calls", is_vr=False),
        make_setting_item("parked_aircraft_variety", "Parked Aircraft Variety", park_var_val, park_var_raw, True, "optimum" if park_var_val == "LOW" else "acceptable", "emerald" if park_var_val == "LOW" else "amber", "OPTIMUM" if park_var_val == "LOW" else "ACCEPTABLE", f"Description: Visual diversity of static parked aircraft liveries at gates.\nCurrent: {park_var_val}.\nRecommendation: LOW for minimal texture memory usage; MEDIUM for balanced gate variety.", traffic_var_options, page=1, tag_reason="Minimal VRAM texture footprint for parked aircraft." if park_var_val == "LOW" else "Diverse gate liveries across parked terminal stands.", rec_guidance="LOW • Reduces aircraft livery memory footprint", is_vr=False),
        make_setting_item("road_traffic", "Road Traffic", road_val, road_raw, True, "optimum" if road_val == "OFF" else "acceptable", "emerald" if road_val == "OFF" else "amber", "OPTIMUM" if road_val == "OFF" else "ACCEPTABLE", "Description: Procedural cars and trucks moving along highways and city streets.\nRecommendation: OFF eliminates unnecessary procedural vehicle thread dispatch and frees MainThread cycles.", traffic_qty_options, page=1, tag_reason="Eliminates procedural vehicle thread dispatch, freeing CPU cycles." if road_val == "OFF" else "Procedural cars and trucks add MainThread vehicle dispatch overhead.", rec_guidance="OFF • Relieves CPU MainThread from procedural vehicles", is_vr=False),
        make_setting_item("sea_traffic", "Sea Traffic", sea_val, sea_raw, True, "optimum" if sea_is_opt else "acceptable", "emerald" if sea_is_opt else "amber", "OPTIMUM" if sea_is_opt else "ACCEPTABLE", "Description: Commercial maritime shipping and boat traffic.\nRecommendation: OFF (maximum performance, eliminates ship pathfinding threads) or LOW (official GAIST / Seafront standard). HIGH/ULTRA adds minor port overhead without major framerate penalty.", traffic_qty_options, page=1, tag_reason="Maximum performance: maritime simulation disabled on background threads." if sea_val == "OFF" else ("Official GAIST / Seafront standard (5-10% LOW): complete AI shipping fleet without ship collisions." if sea_val == "LOW" else "Acceptable: maritime simulation on background threads (~1-3 FPS impact max near ports, 0 FPS inland)."), rec_guidance="OFF (Max FPS) or LOW (Standard GAIST / Seafront)", is_vr=False),

        # PAGE 2: AIRPORT SERVICES (2)
        make_setting_item("airport_services_quantity", "Airport Services Quantity", svc_qty_val, svc_qty_raw, True, "optimum" if svc_qty_val == "OFF" else "acceptable", "emerald" if svc_qty_val == "OFF" else "amber", "OPTIMUM" if svc_qty_val == "OFF" else "ACCEPTABLE", "Description: Ground service equipment (catering trucks, baggage carts, fuelers, pushback tugs).\nRecommendation: OFF is the official standard when using GSX Pro to prevent truck clipping and free CPU MainThread cycles.", traffic_qty_options, page=2, tag_reason="Official GSX Pro standard (OFF): eliminates vehicle clipping and frees apron CPU cycles." if svc_qty_val == "OFF" else "Active default GSE fleet increases apron CPU draw calls and can conflict with GSX Pro.", rec_guidance="OFF • Official GSX Pro standard (avoids GSE conflicts)", is_vr=False),
        make_setting_item("airport_services_variety", "Airport Services Variety", svc_var_val, svc_var_raw, True, "optimum" if svc_var_val == "LOW" else "acceptable", "emerald" if svc_var_val == "LOW" else "amber", "OPTIMUM" if svc_var_val == "LOW" else "ACCEPTABLE", f"Description: Visual diversity of ground handling equipment 3D models and operator liveries.\nCurrent: {svc_var_val}.\nRecommendation: LOW for peak performance (minimal VRAM texture footprint); MEDIUM for balanced diversity.", traffic_var_options, page=2, tag_reason="Minimal VRAM texture footprint and zero streaming hitching." if svc_var_val == "LOW" else ("Balanced ground service liveries." if svc_var_val == "MEDIUM" else "Elevated texture sets in memory."), rec_guidance="LOW • Minimizes ground handling equipment texture memory", is_vr=False),

        # PAGE 3: CHARACTERS & FAUNA (5)
        make_setting_item("characters_quantity", "Characters Quantity", char_qty_val, char_qty_raw, True, "optimum" if char_qty_is_opt else "acceptable", "emerald" if char_qty_is_opt else "amber", "OPTIMUM" if char_qty_is_opt else "ACCEPTABLE", "Description: Density of ground crew, marshallers, and airport personnel.\nRecommendation: OFF (maximum performance) or LOW (FSLTL standard for gate marshallers). Avoid HIGH/ULTRA.", traffic_qty_options, page=3, tag_reason="Maximum performance: zero ground personnel animation overhead on CPU." if char_qty_val == "OFF" else ("Official standard (LOW): guarantees gate marshallers without CPU penalty on this system." if char_qty_val == "LOW" else "Avoid HIGH/ULTRA (heavy CPU animation load)."), rec_guidance="OFF or LOW • Recommended standard for gate marshallers", is_vr=False),
        make_setting_item("characters_variety", "Characters Variety", char_var_val, char_var_raw, True, "optimum" if char_var_val == "LOW" else "acceptable", "emerald" if char_var_val == "LOW" else "amber", "OPTIMUM" if char_var_val == "LOW" else "ACCEPTABLE", f"Description: Visual diversity of ground crew uniforms and body meshes.\nCurrent: {char_var_val}.\nRecommendation: LOW for minimal texture memory usage and peak smoothness; MEDIUM for balanced ramp personnel variety.", traffic_var_options, page=3, tag_reason="Minimal VRAM texture footprint and zero streaming hitching." if char_var_val == "LOW" else ("Balanced ramp worker variation." if char_var_val == "MEDIUM" else "Elevated ground personnel texture sets in VRAM."), rec_guidance="LOW • Reduces personnel texture variety in VRAM", is_vr=False),
        make_setting_item("characters_quality", "Characters Quality", char_qlt_val, char_qlt_raw, True, "optimum" if char_qlt_is_opt else "acceptable", "emerald" if char_qlt_is_opt else "amber", "OPTIMUM" if char_qlt_is_opt else "ACCEPTABLE", "Description: Polygon resolution and skeletal animation fidelity for airport personnel.\nRecommendation: LOW (minimal geometry and vertex workload) or MEDIUM (balanced fidelity). Avoid HIGH/ULTRA.", traffic_var_options, page=3, tag_reason="Minimal polygon and vertex geometry workload." if char_qlt_val == "LOW" else ("Balanced polygon fidelity for airport workers." if char_qlt_val == "MEDIUM" else "Excessive polygon density for personnel viewed from the flight deck."), rec_guidance="LOW • Lightweight 3D geometry for ground personnel", is_vr=False),
        make_setting_item("fauna_density", "Fauna Density", fauna_val, fauna_raw, True, "optimum" if fauna_val == "OFF" else "acceptable", "emerald" if fauna_val == "OFF" else "amber", "OPTIMUM" if fauna_val == "OFF" else "ACCEPTABLE", "Description: Wildlife and bird flock generation in rural and wilderness areas.\nRecommendation: OFF or LOW for airline ops; MEDIUM for bush flying.", traffic_qty_options, page=3, tag_reason="Controlled wildlife spawning.", rec_guidance="OFF (Liners) or LOW/MEDIUM (Bush Flying)", is_vr=False),
        make_setting_item("seatbelt_visibility", "Seatbelt Visibility", seatbelt_val, seatbelt_raw, True, "optimum" if seatbelt_val == "OFF" else "acceptable", "emerald" if seatbelt_val == "OFF" else "amber", "OPTIMUM" if seatbelt_val == "OFF" else "ACCEPTABLE", "Description: Pilot seatbelt and harness strap geometry rendering.\nRecommendation: OFF slightly reduces cockpit polygon count (optimum); ON enhances visual immersion (acceptable).", ["ON", "OFF"], page=3, tag_reason="Seatbelt geometry disabled, slightly reducing cockpit polygon count." if seatbelt_val == "OFF" else "Cockpit seatbelts rendered.", rec_guidance="OFF (Geometry savings) or ON (Cockpit immersion)", is_vr=False),
    ]

    # =========================================================================
    # BUILD 2D MATRIX (30 Items across 6 Categories in 2x2 Grid)
    # =========================================================================
    part_2d_is_opt = (part_2d_val == "Low") if is_entry_rig else (part_2d_val in ["Low", "Medium"])
    reflex_2d_rating = "optimum" if reflex_2d == "ON" else ("acceptable" if "BOOST" in reflex_2d else "suboptimal")
    reflex_2d_color = "emerald" if reflex_2d == "ON" else ("amber" if "BOOST" in reflex_2d else "orange")
    reflex_2d_label = "OPTIMUM" if reflex_2d == "ON" else ("ACCEPTABLE" if "BOOST" in reflex_2d else "SUBOPTIMAL")
    reflex_2d_reason = "Drains GPU render queue to minimize input latency." if reflex_2d == "ON" else ("Locks GPU core and memory clocks to maximum boost frequency; higher power draw with negligible latency gain." if "BOOST" in reflex_2d else "Reflex OFF increases input-to-display latency during flight maneuvers.")

    val_aa_2d_up = val_aa_2d.upper()
    if "QUALITY" in val_aa_2d_up:
        aa_2d_rating, aa_2d_color, aa_2d_lbl = "optimum", "emerald", "OPTIMUM"
    elif "DLAA" in val_aa_2d_up:
        aa_2d_rating, aa_2d_color, aa_2d_lbl = ("optimum", "emerald", "OPTIMUM") if is_flagship_gpu else ("acceptable", "amber", "ACCEPTABLE")
    else:
        aa_2d_rating, aa_2d_color, aa_2d_lbl = "acceptable", "amber", "ACCEPTABLE"

    matrix_2d = [
        # PAGE 1: FRAME RATE & SYNC (6)
        make_setting_item("resolution", "Full Screen Resolution", res_formatted, res_raw, True, res_rating, res_color, res_label, f"Description: Native screen rendering resolution for MSFS.\nCurrent: {res_formatted}.\nRecommendation: Match physical monitor native resolution and leverage DLSS for optimal sharpness.", res_options, page=1, tag_reason=res_tag_reason, rec_guidance=f"Native resolution {native_w}x{native_h} recommended", is_vr=False),
        make_setting_item("max_frame_rate", "Max Frame Rate", f"{fps_2d} FPS" if not is_2d_fps_off else "OFF", fps_2d, False, fps_2d_rating, fps_2d_color, fps_2d_label, f"Description: Frame rate limiter to synchronize frame delivery with monitor refresh intervals. Direct numeric input supported.\nCurrent: {'OFF (Uncapped)' if is_2d_fps_off else f'{fps_2d} FPS'} ({'Synchronized' if is_2d_fps_opt else ('OFF / Uncapped' if is_2d_fps_off else 'Custom')}).\nRecommendation: Lock to an exact sync divisor of your monitor (e.g. 60, 72, 80, 82, 90 FPS) to eliminate frame pacing jitter, or OFF if using external limiter.", fps_options, page=1, is_numeric=True, min_val=0, max_val=240, step=1, tag_reason=fps_2d_reason, rec_guidance=f"{target_2d_fps} FPS • Display refresh rate divided by 2 ({screen_hz}Hz / 2)", is_vr=False, is_active=not is_2d_fps_off, target_fps=target_2d_fps),
        make_setting_item("vsync", "V-Sync", vsync_val, vsync_raw, True, "optimum" if vsync_val == "ON" else "acceptable", "emerald" if vsync_val == "ON" else "amber", "OPTIMUM" if vsync_val == "ON" else "ACCEPTABLE", f"Description: Vertical synchronization with physical monitor refresh cycle.\nCurrent: {vsync_val}.\nRecommendation: Keep ON with G-Sync/FreeSync and frame rate limiter to eliminate screen tearing.", ["ON", "OFF"], page=1, tag_reason="V-Sync locks buffer presentation to refresh boundaries, eliminating tearing." if vsync_val == "ON" else "V-Sync OFF may cause horizontal tearing lines during fast camera pans.", rec_guidance="ON • Eliminates screen tearing with G-Sync / FreeSync", is_vr=False),
        make_setting_item("vsync_interval", "V-Sync Interval", vsync_interval_val, vsync_interval_raw_str, True, vsi_rating, vsi_color, vsi_label, f"Description: Swap chain presentation interval relative to physical display refresh rate ({screen_hz} Hz).\nCurrent: {vsync_interval_val}.\nRecommendation: 50% (1/2 divisor) provides the smoothest frame pacing for flight simulation.", vsync_interval_options, page=1, tag_reason=vsi_reason, rec_guidance=vsi_guidance, is_vr=False),
        make_setting_item("reflex", "NVIDIA Reflex", reflex_2d, reflex_2d, False, reflex_2d_rating, reflex_2d_color, reflex_2d_label, f"Description: NVIDIA Reflex low-latency GPU queue pacing technology. Synchronizes CPU/GPU frame submission to eliminate input lag. Has 0 GB impact on VRAM allocation (acts purely on MainThread CPU latency and GPU clock pacing).\nCurrent: {reflex_2d}.\nRecommendation: Set to ON for optimal flight control responsiveness and efficiency (or ON+BOOST if GPU downclocking occurs).", ["ON", "ON+BOOST", "OFF"], page=1, tag_reason=reflex_2d_reason, rec_guidance="ON • Drains GPU queue and minimizes input latency", is_vr=False),
        make_setting_item("frame_generation", "Frame Generation", fg_2d, fg_2d_raw, False, "optimum" if fg_2d.startswith("DLSSG") else "acceptable", "emerald" if fg_2d.startswith("DLSSG") else "amber", "OPTIMUM" if fg_2d.startswith("DLSSG") else "ACCEPTABLE", f"Description: AI optical flow frame interpolation (DLSS 3 Frame Generation / FSR 3).\nCurrent: {fg_2d}.\nRecommendation: Keep ON (DLSSG 2X) in 2D mode for doubled motion smoothness without increasing CPU MainThread load.", ["DLSSG (2X)", "FSR3 (2X)", "OFF"], page=1, tag_reason="Doubles motion smoothness via optical flow without CPU overhead." if fg_2d.startswith("DLSSG") else "Frame generation is inactive; native rendering requires more CPU/GPU pacing.", rec_guidance="DLSSG (2X) • Doubles motion smoothness with zero CPU cost", is_vr=False),
        make_setting_item("framerate_multiplier", "Framerate Multiplier", "1 (2X Interpolation)" if not fg_2d.startswith("OFF") else "OFF (Inactive)", mult_2d, False, "optimum" if not fg_2d.startswith("OFF") else "acceptable", "emerald" if not fg_2d.startswith("OFF") else "amber", "OPTIMUM" if not fg_2d.startswith("OFF") else "INACTIVE", f"Description: Number of interpolated frames generated per native frame via Optical Flow Accelerator (OFA).\nCurrent: {'1 (2X Interpolation)' if not fg_2d.startswith('OFF') else 'OFF (Inactive)'}.\nRecommendation: Set to 1 (2X interpolation) when Frame Generation is active. Generates 1 AI frame per native frame with zero CPU MainThread cost.", ["1 (2X Interpolation)"] if not fg_2d.startswith("OFF") else ["OFF (Inactive)"], page=1, tag_reason="Standard 2X optical flow interpolation factor (1 generated frame per native frame)." if not fg_2d.startswith("OFF") else "Frame Generation is inactive; optical flow multiplier is idle.", rec_guidance="1 (2X) • Standard Optical Flow DLSS 3 multiplier", is_vr=False),

        # PAGE 2: TERRAIN & TEXTURES (6)
        make_setting_item("texture_resolution", "Texture Resolution", format_tex_display(tex_2d_val), tex_2d_raw, True, tex_2d_rating, tex_2d_color, tex_2d_label, tex_2d_tip, tex_options, page=2, tag_reason=tex_2d_reason, rec_guidance="LOW (IFR Liners & VRAM budget) or ULTRA (VFR/GA on 16GB+ GPUs)", is_vr=False),
        make_setting_item("anisotropic_filtering", "Anisotropic Filtering", aniso_2d_val, aniso_2d_raw, True, "optimum" if aniso_2d_val == "16X" else "acceptable", "emerald" if aniso_2d_val == "16X" else "amber", "OPTIMUM" if aniso_2d_val == "16X" else "ACCEPTABLE", "Description: Global texture sampling filter. Prevents runway markings and taxiway lines from blurring at acute angles.\nRecommendation: 16X.", aniso_options, page=2, tag_reason="16X keeps markings sharp at glancing angles.", rec_guidance="16X • Crisp runway markings and lines at acute angles", is_vr=False),
        make_setting_item("tlod", "Terrain LOD (TLOD)", f"{tlod_2d_val}" if not autofps else f"Dynamic ({tlod_2d_val})", str(tlod_2d_val), False, tlod_2d_rating, tlod_2d_color, tlod_2d_label, f"Description: Terrain mesh geometric complexity and photogrammetry draw distance. Major driver of CPU MainThread frame time! Direct numeric input supported up to 400.\nCurrent: {tlod_2d_val}{' (Managed by AutoFPS)' if autofps else ''}.\nRecommendation: {'Airliners: Keep 100-120 (or dynamic with AutoFPS) to ensure CPU MainThread stays under 25ms during landing flare.' if is_liner else 'GA: 150-200 provides rich ground relief and mountain detail.'}", lod_options, page=2, is_numeric=True, min_val=10, max_val=400, step=5, tag_reason=tlod_2d_reason, rec_guidance="100 - 120 (IFR Liners) • 150 - 200 (GA/VFR low altitude)", is_vr=False),
        make_setting_item("olod", "Objects LOD (OLOD)", f"{olod_2d_val}" if not autofps else f"Dynamic ({olod_2d_val})", str(olod_2d_val), False, olod_2d_rating, olod_2d_color, olod_2d_label, f"Description: Geometric draw distance for 3D airport buildings, hangars, and autogen. Direct numeric input supported up to 400.\nCurrent: {olod_2d_val}.\nRecommendation: 100-120 for airliners; 120-150 for GA. Values above 200 severely increase CPU draw calls at busy airports.", lod_options, page=2, is_numeric=True, min_val=10, max_val=400, step=5, tag_reason=olod_2d_reason, rec_guidance="100 - 120 • Optimal balance for airport 3D object draw calls", is_vr=False),
        make_setting_item("offscreen_precaching", "Off Screen Pre-Caching", format_precaching_display(pre_2d_val), pre_2d_raw, False, "optimum" if pre_2d_val == "High" else "acceptable", "emerald" if pre_2d_val == "High" else "amber", "OPTIMUM" if pre_2d_val == "High" else "ACCEPTABLE", f"Description: Scenery pre-caching outside the immediate camera field of view.\nCurrent: {pre_2d_val}.\nRecommendation: HIGH is the optimal balance to eliminate camera panning stutters without excess memory caching.", precaching_options, page=2, tag_reason="Sufficient scenery pre-cached to prevent panning freezes." if pre_2d_val in ["High", "Ultra"] else "Low pre-caching causes stutter whenever camera view rotates.", rec_guidance="HIGH • Eliminates 100% of camera panning stutters without VRAM overload" if vram_gb < 20.0 else "ULTRA • Fluid 360° panning for 20GB+ VRAM GPUs", is_vr=False),
        make_setting_item("displacement_mapping", "Displacement Mapping", format_disp_display(disp_2d), "1" if disp_2d == "ON" else "0", False, "optimum" if disp_2d == "OFF" else "suboptimal", "emerald" if disp_2d == "OFF" else "orange", "OPTIMUM" if disp_2d == "OFF" else "SUBOPTIMAL", f"Description: Tessellated micro-surface height displacements on runway pavement and terrain.\nCurrent: {disp_2d}.\nRecommendation: Keep OFF to save VRAM and GPU compute. Visual difference from flight altitude is imperceptible.", disp_options, page=2, tag_reason="Displacement mapping disabled to conserve VRAM and GPU compute." if disp_2d == "OFF" else "Enables surface tessellation at the expense of extra VRAM and draw calls.", rec_guidance="OFF • Prevents runway texture shimmering and saves VRAM", is_vr=False),

        # PAGE 3: ENVIRONMENT (5)
        make_setting_item(
            "buildings", "Buildings Quality", bld_2d_val, bld_2d_raw, False,
            "optimum" if bld_2d_val == "High" else ("suboptimal" if bld_2d_val == "Low" else "acceptable"),
            "emerald" if bld_2d_val == "High" else ("orange" if bld_2d_val == "Low" else "amber"),
            "OPTIMUM" if bld_2d_val == "High" else ("SUBOPTIMAL" if bld_2d_val == "Low" else "ACCEPTABLE"),
            f"Description: Blackshark AI procedural 3D building footprint extrusion, roof geometry, and facade texture atlases for autogen cities.\nCurrent: {bld_2d_val}.\nRecommendation: HIGH for crisp city structures while keeping safe VRAM headroom at busy hubs.",
            q_options, page=3,
            tag_reason="Standard extrusion + 2K facade atlases: sharp urban skylines with ~25% lower draw calls and stable VRAM headroom." if bld_2d_val == "High" else ("Full footprint extrusion + 4K facade atlases: maximum building LOD distance, but adds ~25% extra autogen draw calls at major hubs." if bld_2d_val == "Ultra" else ("Simplified building meshes + 1K atlases: good performance on mid-tier hardware with minor rooftop detail loss." if bld_2d_val == "Medium" else "Flat rooftops + low-res textures: minimal geometry dispatch, but noticeable suburban pop-in.")),
            rec_guidance="HIGH • Crisp urban autogen and controlled draw calls",
            is_vr=False
        ),
        make_setting_item(
            "trees", "Trees Quality", tree_2d_val, tree_2d_raw, False,
            "optimum" if tree_2d_val == "High" else ("suboptimal" if tree_2d_val == "Low" else "acceptable"),
            "emerald" if tree_2d_val == "High" else ("orange" if tree_2d_val == "Low" else "amber"),
            "OPTIMUM" if tree_2d_val == "High" else ("SUBOPTIMAL" if tree_2d_val == "Low" else "ACCEPTABLE"),
            f"Description: 3D tree canopy geometry density, draw distance, and foliage shadowing.\nCurrent: {tree_2d_val}.\nRecommendation: HIGH offers rich forests and realistic canopy cover with negligible performance cost.",
            q_options, page=3,
            tag_reason="Dense 3D tree canopies with optimized LOD falloff: realistic forests with negligible GPU/CPU overhead." if tree_2d_val == "High" else ("Highest 3D canopy density + extended draw distance: maximum foliage richness, but heavy vertex and shadow cascade passes over dense forests." if tree_2d_val == "Ultra" else ("Balanced canopy density: reduces foliage triangle count by ~30%, good for entry-level GPUs." if tree_2d_val == "Medium" else "Sparse tree clustering and aggressive LOD culling: noticeable canopy pop-in during low-altitude flight.")),
            rec_guidance="HIGH • Dense 3D canopy with minimal FPS impact",
            is_vr=False
        ),
        make_setting_item(
            "grass", "Grass & Bushes", grass_2d_val, grass_2d_raw, False,
            "optimum" if (grass_2d_val == "Low" if is_liner else grass_2d_val == "High") else ("suboptimal" if grass_2d_val == "Ultra" else "acceptable"),
            "emerald" if (grass_2d_val == "Low" if is_liner else grass_2d_val == "High") else ("orange" if grass_2d_val == "Ultra" else "amber"),
            "OPTIMUM" if (grass_2d_val == "Low" if is_liner else grass_2d_val == "High") else ("SUBOPTIMAL" if grass_2d_val == "Ultra" else "ACCEPTABLE"),
            f"Description: Ground procedural turf, 3D grass, and wild flowers around airfields.\nCurrent: {grass_2d_val}.\nRecommendation: {'Airliners: LOW eliminates useless 3D grass triangles on concrete runways, saving CPU draw calls.' if is_liner else 'GA: HIGH for realistic grass airfields.'}",
            q_options, page=3,
            tag_reason="Minimal 3D turf: eliminates unneeded 3D grass triangles on concrete runways, saving apron draw calls." if is_liner and grass_2d_val == "Low" else ("Rich 3D turf and wild flowers: authentic grass strip immersion for low-altitude bush flying." if not is_liner and grass_2d_val == "High" else ("Maximum blade density + wild flowers: heavy alpha-blending and vertex passes around airfield perimeters." if grass_2d_val == "Ultra" else "Moderate turf density: subtle grass along taxiway borders with low alpha-testing cost.")),
            rec_guidance="LOW (Liners / Runway pavement) or HIGH (GA / Turf fields)",
            is_vr=False
        ),
        make_setting_item(
            "water_waves", "Water Waves Simulation", water_2d_val, water_2d_raw, False,
            "optimum" if "512" in water_2d_val else ("suboptimal" if "128" in water_2d_val else "acceptable"),
            "emerald" if "512" in water_2d_val else ("orange" if "128" in water_2d_val else "amber"),
            "OPTIMUM" if "512" in water_2d_val else ("SUBOPTIMAL" if "128" in water_2d_val else "ACCEPTABLE"),
            f"Description: Fast Fourier Transform (FFT) ocean and lake wave simulation resolution grid.\nCurrent: {water_2d_val}.\nRecommendation: HIGH (512) for realistic open water swells without GPU compute penalty.",
            water_options, page=3,
            tag_reason="512x512 FFT simulation grid: realistic wave swells and shoreline ripples with negligible compute overhead." if "512" in water_2d_val else ("1024x1024 FFT simulation grid: fine wave cresting and dynamic foam, requires heavy compute shader passes with minor visual difference from altitude." if "1024" in water_2d_val else ("256x256 FFT simulation grid: clean ocean swell patterns with low compute overhead." if "256" in water_2d_val else "128x128 FFT simulation grid: simplified wave animation, minimal GPU compute.")),
            rec_guidance="HIGH (512) • Realistic ocean swells without GPU compute penalty",
            is_vr=False
        ),
        make_setting_item(
            "volumetric_clouds", "Volumetric Clouds", cld_2d_val, cld_2d_raw, False,
            "optimum" if cld_2d_val == "High" else ("suboptimal" if cld_2d_val == "Low" else "acceptable"),
            "emerald" if cld_2d_val == "High" else ("orange" if cld_2d_val == "Low" else "amber"),
            "OPTIMUM" if cld_2d_val == "High" else ("SUBOPTIMAL" if cld_2d_val == "Low" else "ACCEPTABLE"),
            f"Description: Raymarched volumetric cloud rendering quality and boundary scattering.\nCurrent: {cld_2d_val}.\nRecommendation: HIGH delivers near-identical visual fidelity to Ultra with 15% better GPU performance in overcast weather.",
            q_options, page=3,
            tag_reason="12 Raymarching Samples / 48 steps: excellent volumetric light scattering with 15-20% faster frame times than Ultra." if cld_2d_val == "High" else ("16 Raymarching Samples / 64 steps: full volumetric density, but costs 3-4ms extra GPU frame time in dense overcast and storms." if cld_2d_val == "Ultra" else ("8 Raymarching Samples / 32 steps: solid cloud density with fast compute, subtle pixelation on cloud edges." if cld_2d_val == "Medium" else "4 Raymarching Samples / 16 steps: coarse voxel sampling with visible edge dithering.")),
            rec_guidance="HIGH • Near-identical photorealism to Ultra (+15% FPS)",
            is_vr=False
        ),

        # PAGE 4: LIGHTING (5)
        make_setting_item("shadow_maps", "Shadow Maps Resolution", shd_2d_val, shd_2d_raw, False, "optimum" if "1536" in shd_2d_val else "acceptable", "emerald" if "1536" in shd_2d_val else "amber", "OPTIMUM" if "1536" in shd_2d_val else "ACCEPTABLE", f"Description: Direct sunlight shadow map buffer resolution for airframe and structures.\nCurrent: {shd_2d_val}.\nRecommendation: HIGH (1536) for clean shadow lines without shimmering.", shadow_options, page=4, tag_reason="High shadow map resolution delivers sharp cockpit and airframe shadows.", rec_guidance="HIGH (1536) • Crisp cockpit and airframe shadows", is_vr=False),
        make_setting_item("terrain_shadows", "Terrain Shadows", tshd_2d_val, tshd_2d_raw, False, "optimum" if "512" in tshd_2d_val else "acceptable", "emerald" if "512" in tshd_2d_val else "amber", "OPTIMUM" if "512" in tshd_2d_val else "ACCEPTABLE", f"Description: Long-distance heightfield mountain and ridge self-shadowing.\nCurrent: {tshd_2d_val}.\nRecommendation: HIGH (512) for realistic mountain terrain relief during golden hour approaches.", hf_options, page=4, tag_reason="Realistic mountain shadowing during sunrise and sunset.", rec_guidance="HIGH (512) • Realistic mountain relief during low sun angles", is_vr=False),
        make_setting_item("contact_shadows", "Contact Shadows", cshd_2d_val, cshd_2d_raw, False, "optimum" if cshd_2d_val == "High" else "acceptable", "emerald" if cshd_2d_val == "High" else "amber", "OPTIMUM" if cshd_2d_val == "High" else "ACCEPTABLE", f"Description: Screen-space micro-shadows beneath wheels, switches, levers, and small cockpit fixtures.\nCurrent: {cshd_2d_val}.\nRecommendation: HIGH provides realistic contact depth in the cockpit with negligible GPU impact.", q_options, page=4, tag_reason="Enhances tactile depth around cockpit instruments and switches.", rec_guidance="HIGH • Precise contact depth under switches and levers", is_vr=False),
        make_setting_item("raytraced_shadows", "Raytraced Shadows", rt_2d_val, "1" if rt_2d_val == "ON" else "0", False, "optimum" if rt_2d_val == "OFF" else "acceptable", "emerald" if rt_2d_val == "OFF" else "amber", "OPTIMUM" if rt_2d_val == "OFF" else "ACCEPTABLE", f"Description: Hardware ray-traced shadows on RT cores.\nCurrent: {rt_2d_val}.\nRecommendation: Keep OFF in flight sims to conserve RT cores and GPU frame time for DLSS.", ["OFF", "ON"], page=4, tag_reason="Disabled ray tracing frees RT cores for DLSS frame generation." if rt_2d_val == "OFF" else "Enables RT shadows at the cost of GPU frame time.", rec_guidance="OFF • Conserves RT cores and frame time for DLSS FG", is_vr=False),
        make_setting_item("volumetric_lights", "Volumetric Lights", vl_2d_val, vl_2d_raw, False, "optimum" if vl_2d_val == "High" else "acceptable", "emerald" if vl_2d_val == "High" else "amber", "OPTIMUM" if vl_2d_val == "High" else "ACCEPTABLE", f"Description: Atmospheric light beam scattering from runway lights, beacons, and landing lights in fog/clouds.\nCurrent: {vl_2d_val}.\nRecommendation: HIGH for dramatic night lighting and authentic low-visibility CAT III approaches.", q_options, page=4, tag_reason="Atmospheric light shaft rendering during night and low-visibility weather.", rec_guidance="HIGH • Dramatic light shafts at night and in low visibility", is_vr=False),

        # PAGE 5: COCKPIT (3)
        make_setting_item("glass_cockpits", "Glass Cockpit Refresh", glass_2d_val, glass_2d_raw, False, glass_2d_rating, glass_2d_color, glass_2d_label, glass_2d_tip, glass_options, page=5, tag_reason=glass_2d_reason, rec_guidance="MEDIUM • Smooth EFIS refresh while protecting MainThread", is_vr=False),
        make_setting_item("ambient_occlusion", "Ambient Occlusion (SSAO)", ssao_2d_val, ssao_2d_raw, False, "optimum" if ssao_2d_val == "High" else "acceptable", "emerald" if ssao_2d_val == "High" else "amber", "OPTIMUM" if ssao_2d_val == "High" else "ACCEPTABLE", f"Description: Screen-space ambient occlusion (SSAO) providing realistic contact shading in crevices and corners.\nCurrent: {ssao_2d_val}.\nRecommendation: HIGH provides natural cockpit lighting and shadow depth without excessive shader overhead.", q_options, page=5, tag_reason="Natural contact shading in cockpit crevices and airframe recesses.", rec_guidance="HIGH • Natural contact shading without heavy GPU penalty", is_vr=False),
        make_setting_item("windshield_effects", "Windshield Effects", wind_2d_val, wind_2d_raw, False, "optimum" if wind_2d_val == "High" else "acceptable", "emerald" if wind_2d_val == "High" else "amber", "OPTIMUM" if wind_2d_val == "High" else "ACCEPTABLE", f"Description: Dynamic raindrops, icing accretion, wiper blade sweeps, and glass reflection effects on windshield.\nCurrent: {wind_2d_val}.\nRecommendation: HIGH for full weather immersion on the flight deck.", q_options, page=5, tag_reason="Realistic dynamic rain, icing, and wiper sweep effects.", rec_guidance="HIGH • Dynamic rain and icing immersion on flight deck", is_vr=False),

        # PAGE 6: POST-PROCESSING (7)
        make_setting_item("anti_aliasing", "Anti-Aliasing & Upscaling", format_aa_display(val_aa_2d, False), aa_2d, False, aa_2d_rating, aa_2d_color, aa_2d_lbl, f"Description: Anti-aliasing method and AI upscaling mode (DLSS/TAA/DLAA).\nCurrent: {val_aa_2d}.\nRecommendation: DLSS Quality balances sharp flight decks with DLSS 3 FG; DLAA for maximum native edge clarity.", aa_options_2d, page=6, rec_guidance="Quality balances sharp flight decks with DLSS 3 FG • DLAA for maximum native edge clarity", is_vr=False),
        make_setting_item("dynamic_settings", "Dynamic Settings", dyn_2d, "0" if dyn_2d == "OFF" else "1", False, "optimum" if dyn_2d == "OFF" else "suboptimal", "emerald" if dyn_2d == "OFF" else "orange", "OPTIMUM" if dyn_2d == "OFF" else "SUBOPTIMAL", f"Description: Dynamic internal resolution scaling during heavy scenes.\nCurrent: {dyn_2d}.\nRecommendation: Keep OFF. Dynamic resolution triggers fluctuating cockpit blur and inconsistent image clarity.", ["OFF", "ON"], page=6, tag_reason="Disabled dynamic scaling guarantees consistent render sharpness in all phases." if dyn_2d == "OFF" else "Dynamic scaling lowers resolution unpredictably, blurring cockpit screens.", rec_guidance="OFF • Guarantees consistent cockpit gauge clarity", is_vr=False),
        make_setting_item("reflections_ssr", "Screen Reflections (SSR)", ssr_2d_val, ssr_2d_raw, False, "optimum" if ssr_2d_val == "High" else "acceptable", "emerald" if ssr_2d_val == "High" else "amber", "OPTIMUM" if ssr_2d_val == "High" else "ACCEPTABLE", f"Description: Screen space reflections on wet runways, water puddles, and cockpit windshields.\nCurrent: {ssr_2d_val}.\nRecommendation: HIGH in 2D mode for realistic rainy runway reflections; LOW in VR mode to save GPU fill rate.", q_options, page=6, rec_guidance="HIGH • Realistic runway reflections in wet conditions", is_vr=False),
        make_setting_item("cubemap_reflections", "Cubemap Reflections", cube_2d_val, cube_2d_raw, False, "optimum" if cube_2d_val == "192" else "acceptable", "emerald" if cube_2d_val == "192" else "amber", "OPTIMUM" if cube_2d_val == "192" else "ACCEPTABLE", f"Description: Resolution of cubemap reflection probes used for cockpit dials, canopy gloss, and shiny metal surfaces.\nCurrent: {cube_2d_val}.\nRecommendation: 192 for crisp reflections without excessive probe rendering cost.", cube_options, page=6, tag_reason="Balanced reflection probe resolution.", rec_guidance="192 • Sharp reflections on instruments and canopy glass", is_vr=False),
        make_setting_item("dof", "Depth Of Field (DOF)", dof_2d_val, dof_2d_raw, False, "optimum" if dof_2d_val == "OFF" else "acceptable", "emerald" if dof_2d_val == "OFF" else "amber", "OPTIMUM" if dof_2d_val == "OFF" else "ACCEPTABLE", f"Description: Cinematic focal blur on distant cockpit or exterior objects.\nCurrent: {dof_2d_val}.\nRecommendation: Keep OFF for maximum cockpit gauge legibility.", dof_options, page=6, tag_reason="Disabled DOF keeps all flight instruments sharp." if dof_2d_val == "OFF" else "DOF blurs out-of-focus cockpit gauges.", rec_guidance="OFF • Keeps all flight instruments and dials crystal clear", is_vr=False),
        make_setting_item("motion_blur", "Motion Blur", mb_2d_val, mb_2d_raw, False, "optimum" if mb_2d_val == "OFF" else "suboptimal", "emerald" if mb_2d_val == "OFF" else "orange", "OPTIMUM" if mb_2d_val == "OFF" else "SUBOPTIMAL", f"Description: Directional camera velocity smearing.\nCurrent: {mb_2d_val}.\nRecommendation: Keep OFF. Motion blur smears runway centerline markings and avionics during landing flare.", mb_options, page=6, tag_reason="Disabled blur ensures sharp vision during landing maneuvers." if mb_2d_val == "OFF" else "Smears gauges and runway markings during camera motion.", rec_guidance="OFF • Crisp vision of runway centerline during flare", is_vr=False),
        make_setting_item("particles", "Particles Quality", part_2d_val, part_2d_raw, False, "optimum" if part_2d_is_opt else "acceptable", "emerald" if part_2d_is_opt else "amber", "OPTIMUM" if part_2d_is_opt else "ACCEPTABLE", f"Description: Contrails, engine smoke, tire touchdown smoke, and spray particles.\nCurrent: {part_2d_val}.\nRecommendation: LOW (minimal alpha fill rate) or MEDIUM (balanced smoke and contrails).", part_options, page=6, tag_reason="Minimal alpha fill-rate workload, preventing frame drops in dense smoke." if part_2d_val == "Low" else ("Balanced particle density prevents alpha fill drops in heavy smoke." if part_2d_val == "Medium" else "Particle counts evaluated."), rec_guidance="MEDIUM • Balanced smoke and contrails without FPS drops", is_vr=False),
    ]

    # =========================================================================
    # BUILD VR MATRIX (26 Items across 6 Categories in 2x2 Grid)
    # =========================================================================
    sw_name = vr_headset_info.get("software_name") or "Headset Software"
    sw_scale = vr_headset_info.get("software_render_scale")
    sw_scale_pct = vr_headset_info.get("software_render_scale_pct")

    if scale_vr_pct == "100%":
        scale_vr_rating = "optimum"
        scale_vr_color = "emerald"
        scale_vr_lbl = "OPTIMUM"
        if sw_scale:
            scale_vr_reason = f"Clean 1:1 pairing with {sw_name} ({sw_scale_pct}% / {sw_scale:.2f}). In-engine scaling locked at 100% to prevent compound blur."
        else:
            scale_vr_reason = "100% preserves full DLSS reconstruction sharpness in headset."
    else:
        try:
            scale_flt = float(scale_vr_raw)
        except Exception:
            scale_flt = 1.0
        scale_vr_rating = "hazard" if scale_flt < 0.85 else "suboptimal"
        scale_vr_color = "rose" if scale_flt < 0.85 else "orange"
        scale_vr_lbl = "HAZARD" if scale_flt < 0.85 else "SUBOPTIMAL"
        if sw_scale:
            effective_pct = round(scale_flt * sw_scale * 100)
            scale_vr_reason = f"COMPOUND BLUR HAZARD: MSFS is set to {scale_vr_pct} while {sw_name} is set to {sw_scale_pct}%, resulting in an effective resolution of {effective_pct}%! Lock MSFS to 100%."
        else:
            scale_vr_reason = f"Suboptimal downsampling ({scale_vr_pct}): softens cockpit glass displays and runway lines. Keep MSFS locked at 100%."

    scale_vr_tooltip = f"Description: Primary rendering scale in VR before DLSS upscaling.\nCurrent: {scale_vr_pct} (In-game MSFS).\nRecommendation: Set strictly to 100% in MSFS! Use your headset software ({sw_name}) to adjust resolution scale without causing double-downscaling blur."

    reflex_vr_rating = "optimum" if reflex_vr == "ON" else ("acceptable" if "BOOST" in reflex_vr else "suboptimal")
    reflex_vr_color = "emerald" if reflex_vr == "ON" else ("amber" if "BOOST" in reflex_vr else "orange")
    reflex_vr_label = "OPTIMUM" if reflex_vr == "ON" else ("ACCEPTABLE" if "BOOST" in reflex_vr else "SUBOPTIMAL")
    reflex_vr_reason = "Minimizes VR motion-to-photon latency without GPU thermal penalty." if reflex_vr == "ON" else ("Keeps GPU boost clocks pinned; extra heat in VR headset without motion-to-photon gain." if "BOOST" in reflex_vr else "Reflex OFF increases VR motion-to-photon latency and judder risk.")

    reproj_is_opt = reproj_vr_val in ["OFF", "AUTO", "1/2 REPROJECTION"]
    reproj_reason_desc = (
        "Pure native frame presentation: zero reprojection wobble or ghosting (essential for OFXR Bridge)." if reproj_vr_val == "OFF"
        else ("Dynamic OpenXR reprojection: engages smoothly only during framerate dips." if reproj_vr_val == "AUTO"
        else ("Locked 1/2 cadence reprojection for smooth airliner flight." if reproj_vr_val == "1/2 REPROJECTION"
        else "Stereo motion reprojection configured."))
    )

    val_aa_vr_up = val_aa_vr.upper()
    if "QUALITY" in val_aa_vr_up or (val_aa_vr_up == "DLSS" and not any(k in val_aa_vr_up for k in ["PERFORMANCE", "BALANCED"])):
        aa_vr_rating, aa_vr_color, aa_vr_lbl = "optimum", "emerald", "OPTIMUM"
    elif "BALANCED" in val_aa_vr_up:
        aa_vr_rating, aa_vr_color, aa_vr_lbl = "acceptable", "amber", "ACCEPTABLE"
    elif "PERFORMANCE" in val_aa_vr_up:
        aa_vr_rating, aa_vr_color, aa_vr_lbl = "suboptimal", "orange", "SUBOPTIMAL"
    elif "DLAA" in val_aa_vr_up:
        aa_vr_rating, aa_vr_color, aa_vr_lbl = "hazard", "rose", "HAZARD"
    elif "TAA" in val_aa_vr_up:
        aa_vr_rating, aa_vr_color, aa_vr_lbl = "suboptimal", "orange", "SUBOPTIMAL"
    else:
        aa_vr_rating, aa_vr_color, aa_vr_lbl = "acceptable", "amber", "ACCEPTABLE"

    matrix_vr = [
        # PAGE 1: VR HEADSET & SYNC (5)
        make_setting_item("primary_scaling_vr", "VR Render Scale", scale_vr_pct, scale_vr_raw, False, scale_vr_rating, scale_vr_color, scale_vr_lbl, scale_vr_tooltip, scale_vr_options, page=1, tag_reason=scale_vr_reason, rec_guidance="100% • Native 1:1 render scale for crystal clear gauges", is_vr=True),
        make_setting_item("max_frame_rate", "Max Frame Rate (VR)", f"{fps_vr} FPS" if not is_vr_fps_off else "OFF", fps_vr, False, vr_fps_rating, vr_fps_color, vr_fps_label, vr_fps_tooltip, fps_options, page=1, is_numeric=True, min_val=0, max_val=240, step=1, tag_reason=vr_fps_reason, rec_guidance=f"{target_vr_fps} FPS • Headset refresh rate divided by 2 ({vr_hz}Hz / 2)", is_vr=True, is_active=not is_vr_fps_off, target_fps=target_vr_fps),
        make_setting_item("reprojection_mode", "Reprojection Mode", reproj_vr_val, reproj_vr_raw, False, "optimum" if reproj_is_opt else "acceptable", "emerald" if reproj_is_opt else "amber", "OPTIMUM" if reproj_is_opt else "ACCEPTABLE", f"Description: Motion reprojection mode for VR headset.\nCurrent: {reproj_vr_val}.\nRecommendation: OFF (zero warping & pure latency, mandatory with OFXR Bridge) or AUTO / 1/2 REPROJECTION (cadence smoothing).", reproj_options, page=1, tag_reason=reproj_reason_desc, rec_guidance="OFF (pure latency & zero warping) or 1/2 REPROJ (locked sync)", is_vr=True),
        make_setting_item("reflex", "NVIDIA Reflex (VR)", reflex_vr, reflex_vr, False, reflex_vr_rating, reflex_vr_color, reflex_vr_label, f"Description: NVIDIA Reflex low-latency GPU queue pacing in VR. Synchronizes headset frame pacing and eliminates control lag. Has 0 GB impact on VRAM allocation (acts purely on MainThread and motion-to-photon latency).\nCurrent: {reflex_vr}.\nRecommendation: Set to ON to minimize VR motion-to-photon latency and eliminate control lag.", ["ON", "ON+BOOST", "OFF"], page=1, tag_reason=reflex_vr_reason, rec_guidance="ON • Minimizes headset motion-to-photon latency", is_vr=True),
        make_setting_item("sharpen_amount_vr", "VR Sharpening", sharpen_vr_val, sharpen_vr_raw, False, "optimum" if abs(float(sharpen_vr_val) - 0.20) < 0.05 else "acceptable", "emerald" if abs(float(sharpen_vr_val) - 0.20) < 0.05 else "amber", "OPTIMUM" if abs(float(sharpen_vr_val) - 0.20) < 0.05 else "ACCEPTABLE", f"Description: Post-processing sharpening filter in VR headset.\nCurrent: {sharpen_vr_val}.\nRecommendation: Set to 0.20 when using DLSS. Excessive values (>1.0) cause harsh shimmering on runway lines and horizon.", sharpen_vr_options, page=1, is_numeric=True, min_val=0.0, max_val=2.0, step=0.1, tag_reason="Subtle sharpening without shimmering." if abs(float(sharpen_vr_val) - 0.20) < 0.05 else "High sharpening causes noise and shimmering in VR.", rec_guidance="0.20 • Clean clarity without noise or horizon shimmering", is_vr=True),

        # PAGE 2: VR OPTIMIZATIONS & DLSS (4)
        make_setting_item("anti_aliasing", "Anti-Aliasing & Upscaling (VR)", format_aa_display(val_aa_vr, True), aa_vr, False, aa_vr_rating, aa_vr_color, aa_vr_lbl, f"Description: Anti-aliasing and upscaling mode in VR stereo.\nCurrent: {val_aa_vr}.\nRecommendation: DLSS Quality balances sharp flight decks with high framerate in VR stereo.", aa_options_vr, page=2, rec_guidance="DLSS (Quality) • Crisp cockpit gauges and runway lines • Balanced for lower tier GPUs", is_vr=True),
        make_setting_item("foveated_rendering", "Foveated Rendering", fov_vr_val, fov_vr_raw, False, "optimum" if fov_vr_val == "ON" else "acceptable", "emerald" if fov_vr_val == "ON" else "amber", "OPTIMUM" if fov_vr_val == "ON" else "ACCEPTABLE", f"Description: Variable rate shading reducing GPU load in peripheral vision.\nCurrent: {fov_vr_val}.\nRecommendation: ON for 10-15% GPU frame time reduction in VR headsets.", ["ON", "OFF"], page=2, tag_reason="Reduces GPU peripheral shading workload in headset.", rec_guidance="ON • 10-15% GPU frame time savings in peripheral vision", is_vr=True),
        make_setting_item("dynamic_settings", "Dynamic Settings (VR)", dyn_vr, "0" if dyn_vr == "OFF" else "1", False, "optimum" if dyn_vr == "OFF" else "suboptimal", "emerald" if dyn_vr == "OFF" else "orange", "OPTIMUM" if dyn_vr == "OFF" else "SUBOPTIMAL", f"Description: Dynamic resolution in VR.\nCurrent: {dyn_vr}.\nRecommendation: Keep OFF in VR to avoid sudden stereo blurriness.", ["OFF", "ON"], page=2, tag_reason="Disabled dynamic scaling prevents sudden VR stereo resolution drops.", rec_guidance="OFF • Prevents abrupt stereo resolution drops in headset", is_vr=True),
        make_setting_item("foveated_scale", "Foveated Scale", fov_scale_pct, fov_scale_raw, False, "optimum" if "40%" in fov_scale_pct else "acceptable", "emerald" if "40%" in fov_scale_pct else "amber", "OPTIMUM" if "40%" in fov_scale_pct else "ACCEPTABLE", f"Description: Inner foveal resolution radius.\nCurrent: {fov_scale_pct}.\nRecommendation: 40% offers the best balance between peripheral performance gain and central sharpness.", fov_scale_options, page=2, tag_reason="Optimal foveal radius for wide-FOV headsets.", rec_guidance="40% • Optimal balance of central clarity and GPU savings", is_vr=True),

        # PAGE 3: TERRAIN & TEXTURES VR (5)
        make_setting_item("texture_resolution", "Texture Resolution (VR)", format_tex_display(tex_vr_val), tex_vr_raw, True, tex_vr_rating, tex_vr_color, tex_vr_label, tex_vr_tip, tex_options, page=3, tag_reason=tex_vr_reason, rec_guidance="LOW • Saves 6-8 GB VRAM, preventing compositor crashes in VR", is_vr=True),
        make_setting_item("tlod", "Terrain LOD (TLOD)", f"{tlod_vr_val}" if not autofps else f"Dynamic ({tlod_vr_val})", str(tlod_vr_val), False, tlod_vr_rating, tlod_vr_color, tlod_vr_label, f"Description: Terrain mesh and photogrammetry draw distance in VR stereo. Direct numeric input supported up to 400.\nCurrent: {tlod_vr_val}{' (Managed by AutoFPS)' if autofps else ''}.\nRecommendation: Keep TLOD <= 100 in VR on ground to protect stereo frame time budget and prevent motion reprojection drops.", lod_options, page=3, is_numeric=True, min_val=10, max_val=400, step=5, tag_reason=tlod_vr_reason, rec_guidance="80 - 100 • Protects MainThread to avoid stereo reprojection drops", is_vr=True),
        make_setting_item("olod", "Objects LOD (OLOD)", f"{olod_vr_val}" if not autofps else f"Dynamic ({olod_vr_val})", str(olod_vr_val), False, olod_vr_rating, olod_vr_color, olod_vr_label, f"Description: 3D objects distance in VR up to 400.\nCurrent: {olod_vr_val}.\nRecommendation: Keep OLOD <= 100 in VR.", lod_options, page=3, is_numeric=True, min_val=10, max_val=400, step=5, tag_reason=olod_vr_reason, rec_guidance="80 - 100 • Reduces 3D object draw calls in both eye viewports", is_vr=True),
        make_setting_item("offscreen_precaching", "Off Screen Pre-Caching", format_precaching_display(pre_vr_val), pre_vr_raw, False, "optimum" if pre_vr_val == "High" else "acceptable", "emerald" if pre_vr_val == "High" else "amber", "OPTIMUM" if pre_vr_val == "High" else "ACCEPTABLE", f"Description: Scenery pre-caching in VR.\nCurrent: {pre_vr_val}.\nRecommendation: HIGH is essential for smooth head rotation in VR without stutter.", precaching_options, page=3, tag_reason="Essential for smooth head rotation without border popping in VR.", rec_guidance="HIGH • Mandatory in VR to eliminate head-turning micro-stutters", is_vr=True),
        make_setting_item("displacement_mapping", "Displacement Mapping", format_disp_display(disp_vr), "1" if disp_vr == "ON" else "0", False, "optimum" if disp_vr == "OFF" else "hazard", "emerald" if disp_vr == "OFF" else "rose", "OPTIMUM" if disp_vr == "OFF" else "HAZARD", f"Description: Displacement micro-tessellation in VR.\nCurrent: {disp_vr}.\nRecommendation: Keep OFF in VR. In VR, displacement mapping severely overloads MainThread and VRAM without visible benefit!", disp_options, page=3, tag_reason="Disabled displacement mapping saves GPU compute and prevents VR stutters." if disp_vr == "OFF" else "HAZARD: Displacement mapping in VR causes severe frame drops and MainThread hitches.", rec_guidance="OFF • Mandatory in VR: eliminates judder and saves MainThread", is_vr=True),

        # PAGE 4: ENVIRONMENT VR (5)
        make_setting_item(
            "buildings", "Buildings Quality", bld_vr_val, bld_vr_raw, False,
            "optimum" if bld_vr_val == "Medium" else ("suboptimal" if bld_vr_val == "Ultra" else "acceptable"),
            "emerald" if bld_vr_val == "Medium" else ("orange" if bld_vr_val == "Ultra" else "amber"),
            "OPTIMUM" if bld_vr_val == "Medium" else ("SUBOPTIMAL" if bld_vr_val == "Ultra" else "ACCEPTABLE"),
            f"Description: 3D autogen building fidelity in VR.\nCurrent: {bld_vr_val}.\nRecommendation: MEDIUM in VR to ensure lightweight autogen geometry, save VRAM, and maintain strict stereo reprojection frame budget.",
            q_options, page=4,
            tag_reason="Simplified building meshes + 1K atlases: lightweight autogen geometry, optimal for VR stereo frame budgets." if bld_vr_val == "Medium" else ("Standard extrusion + 2K facade atlases: crisp urban skylines with ~25% higher draw calls in VR." if bld_vr_val == "High" else ("Full footprint extrusion + 4K facade atlases: heavy draw call volume and VRAM pressure in VR headset." if bld_vr_val == "Ultra" else "Flat rooftops + low-res textures: minimal geometry dispatch, but noticeable suburban pop-in.")),
            rec_guidance="MEDIUM • Lightweight geometry for stereo frame time budget",
            is_vr=True
        ),
        make_setting_item(
            "trees", "Trees Quality", tree_vr_val, tree_vr_raw, False,
            "optimum" if tree_vr_val == "Medium" else ("suboptimal" if tree_vr_val == "Ultra" else "acceptable"),
            "emerald" if tree_vr_val == "Medium" else ("orange" if tree_vr_val == "Ultra" else "amber"),
            "OPTIMUM" if tree_vr_val == "Medium" else ("SUBOPTIMAL" if tree_vr_val == "Ultra" else "ACCEPTABLE"),
            f"Description: Trees foliage geometry in VR.\nCurrent: {tree_vr_val}.\nRecommendation: MEDIUM in VR to preserve double-eye foliage rasterization budget.",
            q_options, page=4,
            tag_reason="Balanced canopy density: reduces foliage triangle count by ~30%, ideal for maintaining stable frame pacing in VR stereo." if tree_vr_val == "Medium" else ("Dense 3D tree canopies: realistic forests with slightly elevated stereo rasterization load." if tree_vr_val == "High" else ("Highest 3D canopy density: heavy vertex and alpha-testing workload over dense forest terrain in VR." if tree_vr_val == "Ultra" else "Sparse tree clustering: noticeable canopy pop-in during low-altitude flight.")),
            rec_guidance="MEDIUM • Optimized foliage density for VR stereo fill rate",
            is_vr=True
        ),
        make_setting_item(
            "grass", "Grass & Bushes", grass_vr_val, grass_vr_raw, False,
            "optimum" if grass_vr_val == "Low" else ("hazard" if grass_vr_val == "Ultra" else ("suboptimal" if grass_vr_val == "High" else "acceptable")),
            "emerald" if grass_vr_val == "Low" else ("rose" if grass_vr_val == "Ultra" else ("orange" if grass_vr_val == "High" else "amber")),
            "OPTIMUM" if grass_vr_val == "Low" else ("HAZARD" if grass_vr_val == "Ultra" else ("SUBOPTIMAL" if grass_vr_val == "High" else "ACCEPTABLE")),
            f"Description: Ground procedural vegetation in VR.\nCurrent: {grass_vr_val}.\nRecommendation: LOW saves GPU fill rate in VR stereo.",
            q_options, page=4,
            tag_reason="Minimal 3D turf: saves critical stereo alpha fill rate and apron draw calls in VR." if grass_vr_val == "Low" else ("Balanced grass density: realistic grass strips with controlled VR stereo fill-rate overhead." if grass_vr_val == "Medium" else ("Heavy grass density: noticeable stereo reprojection load when taxiing on runways and grass strips in VR." if grass_vr_val == "High" else "HAZARD in VR: dense grass geometry overtaxes stereo rasterization and causes headset judder.")),
            rec_guidance="LOW • Saves critical stereo fill rate on airport taxiways",
            is_vr=True
        ),
        make_setting_item(
            "water_waves", "Water Waves Simulation", water_vr_val, water_vr_raw, False,
            "optimum" if "256" in water_vr_val else ("suboptimal" if "1024" in water_vr_val else "acceptable"),
            "emerald" if "256" in water_vr_val else ("orange" if "1024" in water_vr_val else "amber"),
            "OPTIMUM" if "256" in water_vr_val else ("SUBOPTIMAL" if "1024" in water_vr_val else "ACCEPTABLE"),
            f"Description: Fast Fourier Transform (FFT) ocean and lake wave simulation grid in VR stereo.\nCurrent: {water_vr_val}.\nRecommendation: MEDIUM (256) preserves stereo compute shader budget in VR without noticeable loss in open-water swell animation.",
            water_options, page=4,
            tag_reason="256x256 FFT simulation grid: basic ocean swell patterns, lightweight for VR stereo pipelines." if "256" in water_vr_val else ("512x512 FFT simulation grid: realistic wave swells with moderate compute shader load in VR." if "512" in water_vr_val else ("1024x1024 FFT simulation grid: fine wave cresting and dynamic foam, heavy compute shader load for VR." if "1024" in water_vr_val else "128x128 FFT simulation grid: simplified wave animation, minimal GPU compute.")),
            rec_guidance="MEDIUM (256) • Lightweight ocean swell simulation for VR stereo",
            is_vr=True
        ),
        make_setting_item(
            "volumetric_clouds", "Volumetric Clouds", cld_vr_val, cld_vr_raw, False,
            "optimum" if cld_vr_val == "Medium" else ("hazard" if cld_vr_val == "Ultra" else "acceptable"),
            "emerald" if cld_vr_val == "Medium" else ("rose" if cld_vr_val == "Ultra" else "amber"),
            "OPTIMUM" if cld_vr_val == "Medium" else ("HAZARD" if cld_vr_val == "Ultra" else "ACCEPTABLE"),
            f"Description: Volumetric clouds in VR stereo.\nCurrent: {cld_vr_val}.\nRecommendation: MEDIUM provides smooth frame pacing without severe cloud penetration drops in VR.",
            q_options, page=4,
            tag_reason="8 Raymarching Samples / 32 steps: lightweight raymarching, saves substantial stereo fill-rate in VR." if cld_vr_val == "Medium" else ("12 Raymarching Samples / 48 steps: crisp cloud boundaries, but taxes stereo frame times in dense overcast." if cld_vr_val == "High" else ("HAZARD in VR: 16 Raymarching Samples overtaxes stereo frame times, triggering reprojection drops in weather." if cld_vr_val == "Ultra" else "4 Raymarching Samples / 16 steps: coarse voxel sampling with visible edge dithering and reduced atmospheric depth.")),
            rec_guidance="MEDIUM • Protects stereo fill rate during heavy overcast",
            is_vr=True
        ),

        # PAGE 5: LIGHTING VR (4)
        make_setting_item(
            "shadow_maps", "Shadow Maps Resolution", shd_vr_val, shd_vr_raw, False,
            "optimum" if "1024" in shd_vr_val else "acceptable",
            "emerald" if "1024" in shd_vr_val else "amber",
            "OPTIMUM" if "1024" in shd_vr_val else "ACCEPTABLE",
            f"Description: Shadows buffer size in VR.\nCurrent: {shd_vr_val}.\nRecommendation: MEDIUM (1024) for clean cockpit shadows without heavy VRAM or stereo rasterization penalty.",
            shadow_options, page=5,
            tag_reason="Clean shadow rendering in VR headset without rasterization spikes.",
            rec_guidance="MEDIUM (1024) • Soft cockpit shadows tuned for VR headset",
            is_vr=True
        ),
        make_setting_item("terrain_shadows", "Terrain Shadows", tshd_vr_val, tshd_vr_raw, False, "optimum" if "256" in tshd_vr_val else "acceptable", "emerald" if "256" in tshd_vr_val else "amber", "OPTIMUM" if "256" in tshd_vr_val else "ACCEPTABLE", f"Description: Heightfield mountain shadows in VR.\nCurrent: {tshd_vr_val}.\nRecommendation: MEDIUM (256) for rich mountain contours with safe stereo frame budget.", hf_options, page=5, tag_reason="Terrain self-shadowing in VR.", rec_guidance="MEDIUM (256) • Lightweight mountain relief shadows in VR", is_vr=True),
        make_setting_item("contact_shadows", "Contact Shadows", cshd_vr_val, cshd_vr_raw, False, "optimum" if cshd_vr_val == "Medium" else "acceptable", "emerald" if cshd_vr_val == "Medium" else "amber", "OPTIMUM" if cshd_vr_val == "Medium" else "ACCEPTABLE", f"Description: Cockpit contact shadows in VR.\nCurrent: {cshd_vr_val}.\nRecommendation: MEDIUM for tactile cockpit depth.", q_options, page=5, tag_reason="Tactile depth for cockpit controls in VR.", rec_guidance="MEDIUM • Tactile depth for cockpit controls in VR", is_vr=True),
        make_setting_item("raytraced_shadows", "Raytraced Shadows (VR)", rt_vr_val, "1" if rt_vr_val == "ON" else "0", False, "optimum" if rt_vr_val == "OFF" else "hazard", "emerald" if rt_vr_val == "OFF" else "rose", "OPTIMUM" if rt_vr_val == "OFF" else "HAZARD", f"Description: Hardware ray-traced shadows in VR stereo.\nCurrent: {rt_vr_val}.\nRecommendation: Strictly keep OFF in VR. Ray tracing severely bottlenecks stereo VR frame times!", ["OFF", "ON"], page=5, tag_reason="Disabled ray tracing is essential to preserve VR stereo framerate." if rt_vr_val == "OFF" else "HAZARD: Ray tracing in VR causes catastrophic stereo reprojection collapse.", rec_guidance="OFF • Strictly forbidden in VR (causes reprojection collapse)", is_vr=True),

        # PAGE 6: COCKPIT & POST VR (8)
        make_setting_item("glass_cockpits", "Glass Cockpit Refresh", glass_vr_val, glass_vr_raw, False, glass_vr_rating, glass_vr_color, glass_vr_label, glass_vr_tip, glass_options, page=6, tag_reason=glass_vr_reason, rec_guidance="LOW or MEDIUM • Relieves CoherentGT UI thread in headset", is_vr=True),
        make_setting_item("ambient_occlusion", "Ambient Occlusion (SSAO)", ssao_vr_val, ssao_vr_raw, False, "optimum" if ssao_vr_val == "Low" else "acceptable", "emerald" if ssao_vr_val == "Low" else "amber", "OPTIMUM" if ssao_vr_val == "Low" else "ACCEPTABLE", f"Description: Screen-space ambient occlusion in VR.\nCurrent: {ssao_vr_val}.\nRecommendation: LOW for natural depth without heavy stereo shading passes.", q_options, page=6, tag_reason="Natural contact shading for VR flight deck.", rec_guidance="LOW • Contact shading without heavy stereo shader passes", is_vr=True),
        make_setting_item("windshield_effects", "Windshield Effects", wind_vr_val, wind_vr_raw, False, "optimum" if wind_vr_val == "High" else "acceptable", "emerald" if wind_vr_val == "High" else "amber", "OPTIMUM" if wind_vr_val == "High" else "ACCEPTABLE", f"Description: Windshield rain and icing in VR.\nCurrent: {wind_vr_val}.\nRecommendation: HIGH for authentic weather immersion in VR.", q_options, page=6, tag_reason="Raindrops and ice accretion in VR.", rec_guidance="HIGH • Realistic rain and icing immersion on VR windshield", is_vr=True),
        make_setting_item("reflections_ssr", "Screen Reflections (SSR)", ssr_vr_val, ssr_vr_raw, False, "optimum" if ssr_vr_val == "Low" else "acceptable", "emerald" if ssr_vr_val == "Low" else "amber", "OPTIMUM" if ssr_vr_val == "Low" else "ACCEPTABLE", f"Description: Screen space reflections in VR.\nCurrent: {ssr_vr_val}.\nRecommendation: LOW in VR saves substantial stereo GPU fill rate.", q_options, page=6, rec_guidance="LOW or OFF • Saves substantial stereo GPU fill rate in VR", is_vr=True),
        make_setting_item("cubemap_reflections", "Cubemap Reflections (VR)", cube_vr_val, cube_vr_raw, False, "optimum" if cube_vr_val == "128" else "acceptable", "emerald" if cube_vr_val == "128" else "amber", "OPTIMUM" if cube_vr_val == "128" else "ACCEPTABLE", f"Description: Cubemap reflection probe resolution in VR.\nCurrent: {cube_vr_val}.\nRecommendation: 128 in VR to protect stereo frame budget.", cube_options, page=6, tag_reason="Lightweight cubemap resolution for VR.", rec_guidance="128 • Lightweight reflection probe resolution for headset", is_vr=True),
        make_setting_item("particles", "Particles Quality (VR)", part_vr_val, part_vr_raw, False, "optimum" if part_vr_val == "Low" else "acceptable", "emerald" if part_vr_val == "Low" else "amber", "OPTIMUM" if part_vr_val == "Low" else "ACCEPTABLE", f"Description: Contrails, smoke, and spray particles in VR.\nCurrent: {part_vr_val}.\nRecommendation: LOW to prevent alpha blending drops in headset.", part_options, page=6, tag_reason="Controlled particles save stereo alpha fill rate.", rec_guidance="LOW • Prevents alpha-blending frame drops in heavy smoke", is_vr=True),
        make_setting_item("dof", "Depth Of Field (DOF VR)", dof_vr_val, "OFF" if dof_vr_val == "OFF" else dof_vr_raw, False, "optimum" if dof_vr_val == "OFF" else "acceptable", "emerald" if dof_vr_val == "OFF" else "amber", "OPTIMUM" if dof_vr_val == "OFF" else "ACCEPTABLE", f"Description: Cinematic focal blur in VR.\nCurrent: {dof_vr_val}.\nRecommendation: Keep strictly OFF in VR to avoid stereo eye fatigue and blurry instruments.", dof_options, page=6, tag_reason="Disabled DOF prevents stereo eye strain in VR." if dof_vr_val in ["OFF", "Low"] else "DOF in VR blurs gauges and induces eye fatigue.", rec_guidance="OFF • Eliminates stereo eye strain and blurred gauges", is_vr=True),
        make_setting_item("motion_blur", "Motion Blur (VR)", mb_vr_val, "OFF" if mb_vr_val == "OFF" else mb_vr_raw, False, "optimum" if mb_vr_val == "OFF" else "suboptimal", "emerald" if mb_vr_val == "OFF" else "orange", "OPTIMUM" if mb_vr_val == "OFF" else "SUBOPTIMAL", f"Description: Camera motion smearing in VR.\nCurrent: {mb_vr_val}.\nRecommendation: Keep strictly OFF in VR to eliminate VR motion sickness and smearing during head movements.", mb_options, page=6, tag_reason="Disabled motion blur prevents simulator sickness in headset." if mb_vr_val == "OFF" else "Motion blur in VR causes severe motion disorientation.", rec_guidance="OFF • Eliminates VR motion sickness and rotation smearing", is_vr=True),
    ]


    # Cross-Settings Interdependences Analysis
    synergies_2d = []
    conflicts_2d = []
    synergies_vr = []
    conflicts_vr = []

    # 1. Frame Gen & V-Sync
    is_fg_2d = any(fg_2d.startswith(k) for k in ["DLSSG", "FSR3"])
    fg_tech_name = "DLSS 3" if "DLSSG" in fg_2d else "FSR 3"
    if is_fg_2d and vsync_val == "ON":
        synergies_2d.append(f"{fg_tech_name} Frame Gen + VSync: Smooth frame pacing without CPU MainThread load.")
    elif is_fg_2d and vsync_val == "OFF":
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
    if reproj_vr_val == "OFF":
        synergies_vr.append("Reprojection OFF: Pure native frame presentation without compositor warping or OFXR conflict.")
    elif fps_vr == str(target_vr_fps):
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
        "vram_total_gb": vram_gb,
        "autofps_active": autofps,
        "matrix_common": matrix_common,
        "matrix_2d": matrix_2d,
        "matrix_vr": matrix_vr,
        "all_displays": all_displays,
        "active_display": active_disp,
        "target_pacing_2d": {
            "target_fps": f"{fps_2d} FPS" if fps_2d != '0' else f"{target_2d_fps} FPS",
            "calculated_target_fps": target_2d_fps,
            "screen_hz": screen_hz,
            "frame_gen_label": f"{fg_tech_name.upper()} FRAME GEN (2X)" if is_fg_2d else "NATIVE SYNC",
            "frame_gen_color": "emerald" if "DLSSG" in fg_2d else ("cyan" if "FSR3" in fg_2d else "slate"),
            "target_mainthread": f"~{2000.0 / target_2d_fps:.1f} ms" if is_fg_2d else f"~{1000.0 / target_2d_fps:.1f} ms",
            "mainthread_color": "emerald",
            "vram_headroom": vram_headroom_2d,
            "vram_color": "emerald"
        },
        "target_pacing_vr": {
            "target_fps": f"{fps_vr} FPS" if fps_vr != '0' else f"{target_vr_fps} FPS",
            "calculated_target_fps": target_vr_fps,
            "vr_hz": vr_hz,
            "frame_gen_label": f"NATIVE 1:1 ({vr_hz} Hz)" if reproj_vr_val == "OFF" else f"1/2 REPROJECTION ({target_vr_fps} FPS)",
            "frame_gen_color": "emerald" if reproj_vr_val == "OFF" else "cyan",
            "target_mainthread": f"{target_vr_ms} ms",
            "mainthread_color": "emerald",
            "vram_headroom": vram_headroom_vr,
            "vram_color": "emerald"
        },
        "graphics_advisory_2d": {
            "status": "optimal" if not conflicts_2d else "suboptimal",
            "title": f"2D Graphics Profile Advisory ({'IFR Airliners' if is_liner else 'VFR General Aviation'})",
            "summary": f"Configured for {'complex airliners (VRAM optimizations)' if is_liner else 'VFR general aviation flights'}.",
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

        content = apply_setting_to_content(content, mode, setting_key, new_value)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "status": "success",
            "message": f"Updated {setting_key} to {new_value} for {mode} mode.",
            "backup_created": backup_path
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "backup_created": backup_path}


def apply_recommended_msfs_settings(mode: str, flight_profile: str = 'LINER', vr_refresh_rate: int = 72, user_cfg_path: Optional[str] = None, preferred_display_id: Optional[str] = None) -> Dict[str, Any]:
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

    # Silent detection of hardware refresh rates
    detected_vr = detect_vr_headset()
    if detected_vr.get("detected") and detected_vr.get("refresh_rate_hz"):
        vr_hz = int(detected_vr["refresh_rate_hz"])
    else:
        try:
            vr_hz = int(vr_refresh_rate)
        except Exception:
            vr_hz = 72
    target_vr_fps = max(30, vr_hz // 2)

    disp_info = detect_display_info(preferred_id=preferred_display_id)
    screen_hz = int(disp_info.get("refresh_rate_int", 60))
    if screen_hz >= 240:
        target_2d_fps = 120
    elif screen_hz >= 180:
        target_2d_fps = 90
    elif screen_hz >= 165:
        target_2d_fps = 82
    elif screen_hz >= 144:
        target_2d_fps = 72
    elif screen_hz >= 120:
        target_2d_fps = 60
    elif screen_hz >= 75:
        target_2d_fps = screen_hz // 2
    else:
        target_2d_fps = 60

    try:
        if mode == '2D':
            tex_val = 'Low' if is_liner else 'High'
            tlod_val = '100' if is_liner else '150'
            glass_val = 'Medium (Half)' if is_liner else 'High (Full)'
            
            # Page 1
            update_msfs_user_cfg_setting('2D', 'anti_aliasing', 'DLSS (Quality)', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'frame_generation', 'DLSSG (2X)', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'vsync', 'ON', path, create_backup=False)
            update_msfs_user_cfg_setting('2D', 'max_frame_rate', str(target_2d_fps), path, create_backup=False)
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
            grass_val_2d = 'Low' if is_liner else 'High'
            update_msfs_user_cfg_setting('2D', 'grass', grass_val_2d, path, create_backup=False)
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
            grass_val_vr = 'Low' if is_liner else 'Medium'
            
            # Page 1
            update_msfs_user_cfg_setting('VR', 'anti_aliasing', 'DLSS (Balanced)', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'frame_generation', 'OFF', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'vsync', 'ON', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'max_frame_rate', str(target_vr_fps), path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'dynamic_settings', 'OFF', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'reflex', 'ON', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'texture_resolution', tex_val, path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'sharpen_amount_vr', '0.20', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'reprojection_mode', 'OFF', path, create_backup=False)
            
            # Page 2
            update_msfs_user_cfg_setting('VR', 'tlod', '100', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'olod', '100', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'offscreen_precaching', 'High', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'volumetric_clouds', 'Medium', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'buildings', 'Medium', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'trees', 'Medium', path, create_backup=False)
            update_msfs_user_cfg_setting('VR', 'grass', grass_val_vr, path, create_backup=False)
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

        # Apply any staged custom setting overrides the user modified in the UI
        staged = _staged_user_cfg_settings.get(mode, {})
        for staged_key, staged_val in staged.items():
            update_msfs_user_cfg_setting(mode, staged_key, staged_val, path, create_backup=False)

        # Clear staged overrides now that they have been committed to disk
        clear_staged_settings(mode)

        profile_desc = "IFR Airliners (VRAM Saver)" if is_liner else "VFR General Aviation (High Detail)"
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
        "description": f"{hz:.0f} Hz Display / Divisor {divisor} -> {displayed_fps} Target FPS ({base_engine_fps} Engine FPS). CPU MainThread frame budget: {frame_budget_ms} ms."
    }


def generate_optimized_rig_profile(user_specs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates recommended graphics profile, AutoFPS thresholds, and SceneryX settings
    combining detected hardware and aircraft studio profiles.
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
        vram_risk = "High (Probable D3D12 paging on Ultra textures)"
    elif vram_gb <= 16.0:
        if studio_id in ["fslabs", "fenix", "inibuilds"]:
            terrain_detail = "LOW"
            dlss_preset = "Quality"
            vram_risk = "Moderate to Controlled (Low Terrain Detail frees ~7 GB VRAM)"
        else:
            terrain_detail = "MEDIUM"
            dlss_preset = "Quality"
            vram_risk = "Low"
    else:
        terrain_detail = "HIGH"
        dlss_preset = "Quality"
        vram_risk = "Zero (Comfortable VRAM headroom)"

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
        "isolation_mode": "Direct A -> B (Recommended)",
        "memory_saving_commit": "~ 2.70 GB Commit RAM",
        "memory_saving_vram": "~ 650 MB VRAM freed",
        "stutter_reduction": "Eliminates 100% of intermediate scenery disk I/O"
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


_cached_hardware_specs: Optional[Dict[str, Any]] = None

def get_full_rig_diagnostics(flight_profile: str = 'LINER', vr_refresh_rate: int = 72, preferred_display_id: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
    """Point d'entrée complet : retourne le diagnostic matériel complet et les listes pour l'UI."""
    global _cached_hardware_specs
    if force_refresh or _cached_hardware_specs is None:
        cpu = detect_cpu_info()
        gpu = detect_gpu_info()
        ram = detect_ram_and_xmp()
        storage = detect_msfs_storage()
        all_displays = detect_all_displays()
        hags = detect_windows_hags()
        dlss = detect_dlss_version()
        installed = detect_installed_aircraft()
        balance = analyze_system_balance(cpu, gpu, ram, storage)
        vr_headset = detect_vr_headset()
        _cached_hardware_specs = {
            "cpu": cpu,
            "gpu": gpu,
            "ram": ram,
            "storage": storage,
            "all_displays": all_displays,
            "hags": hags,
            "dlss": dlss,
            "installed": installed,
            "balance": balance,
            "vr_headset": vr_headset
        }
    else:
        cpu = _cached_hardware_specs["cpu"]
        gpu = _cached_hardware_specs["gpu"]
        ram = _cached_hardware_specs["ram"]
        storage = _cached_hardware_specs.get("storage") or detect_msfs_storage()
        all_displays = _cached_hardware_specs["all_displays"]
        hags = _cached_hardware_specs["hags"]
        dlss = _cached_hardware_specs["dlss"]
        installed = _cached_hardware_specs["installed"]
        balance = _cached_hardware_specs["balance"]
        vr_headset = _cached_hardware_specs["vr_headset"]

    disp = detect_display_info(preferred_id=preferred_display_id, displays_list=all_displays)
    cfg = detect_msfs_user_cfg()
    # Silently ensure pristine copy of user's original UserCfg.opt is preserved
    ensure_original_user_cfg_backup(cfg.get("path"))

    effective_vr_hz = vr_headset["refresh_rate_hz"] if (vr_headset.get("detected") and vr_headset.get("refresh_rate_hz")) else 72

    matrix_data = build_msfs_settings_matrix(user_cfg_path=cfg.get("path"), gpu_info=gpu, cpu_info=cpu, storage_info=storage, flight_profile=flight_profile, vr_refresh_rate=effective_vr_hz, preferred_display_id=preferred_display_id, all_displays_info=all_displays, vr_headset_info=vr_headset)
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
            "storage": storage,
            "display": disp,
            "all_displays": all_displays,
            "vr_headset": vr_headset,
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
