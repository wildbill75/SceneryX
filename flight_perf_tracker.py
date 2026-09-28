#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SceneryX Flight Performance Tracker (Standalone Telemetry Benchmark Pro)
Mesure et journalise en temps réel la VRAM GPU, la RAM de MSFS, les FPS, le MainThread,
la vitesse de lecture du Rolling Cache / Disque, la puissance GPU et les réglages LOD,
avec compte-rendu textuel automatisé des goulets d'étranglement.
"""

import os
import sys
import time
import math
import json
import csv
import re
import glob
import ctypes
import ctypes.wintypes
import subprocess
import webbrowser
import threading
from datetime import datetime

try:
    from SimConnect import SimConnect, RECV_EVENT_FRAME, PERIOD_SECOND
    import SimConnect.scdefs as scdefs
    HAS_SIMCONNECT = True
except Exception:
    HAS_SIMCONNECT = False
    SimConnect = None
    RECV_EVENT_FRAME = None
    PERIOD_SECOND = None
    scdefs = None


# Windows Memory API Structures
class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ('cb', ctypes.wintypes.DWORD),
        ('PageFaultCount', ctypes.wintypes.DWORD),
        ('PeakWorkingSetSize', ctypes.c_size_t),
        ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t),
        ('PeakPagefileUsage', ctypes.c_size_t),
        ('PrivateUsage', ctypes.c_size_t)
    ]

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ('dwLength', ctypes.wintypes.DWORD),
        ('dwMemoryLoad', ctypes.wintypes.DWORD),
        ('ullTotalPhys', ctypes.c_ulonglong),
        ('ullAvailPhys', ctypes.c_ulonglong),
        ('ullTotalPageFile', ctypes.c_ulonglong),
        ('ullAvailPageFile', ctypes.c_ulonglong),
        ('ullTotalVirtual', ctypes.c_ulonglong),
        ('ullAvailVirtual', ctypes.c_ulonglong),
        ('ullAvailExtendedVirtual', ctypes.c_ulonglong)
    ]

class FILETIME(ctypes.Structure):
    _fields_ = [('dwLowDateTime', ctypes.wintypes.DWORD), ('dwHighDateTime', ctypes.wintypes.DWORD)]

class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ('ReadOperationCount', ctypes.c_ulonglong),
        ('WriteOperationCount', ctypes.c_ulonglong),
        ('OtherOperationCount', ctypes.c_ulonglong),
        ('ReadTransferCount', ctypes.c_ulonglong),
        ('WriteTransferCount', ctypes.c_ulonglong),
        ('OtherTransferCount', ctypes.c_ulonglong),
    ]

TH32CS_SNAPPROCESS = 0x00000002
CREATE_NO_WINDOW = 0x08000000

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ('dwSize', ctypes.wintypes.DWORD),
        ('cntUsage', ctypes.wintypes.DWORD),
        ('th32ProcessID', ctypes.wintypes.DWORD),
        ('th32DefaultHeapID', ctypes.c_size_t),
        ('th32ModuleID', ctypes.wintypes.DWORD),
        ('cntThreads', ctypes.wintypes.DWORD),
        ('th32ParentProcessID', ctypes.wintypes.DWORD),
        ('pcPriClassBase', ctypes.c_long),
        ('dwFlags', ctypes.wintypes.DWORD),
        ('szExeFile', ctypes.c_char * 260)
    ]

def get_system_ram():
    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    total_mb = round(stat.ullTotalPhys / (1024 * 1024))
    used_mb = round((stat.ullTotalPhys - stat.ullAvailPhys) / (1024 * 1024))
    return used_mb, total_mb

def find_msfs_pid():
    hSnapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    found_pid = None
    found_name = None
    if hSnapshot and hSnapshot != -1:
        pe = PROCESSENTRY32()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
        if ctypes.windll.kernel32.Process32First(hSnapshot, ctypes.byref(pe)):
            while True:
                exe_name = pe.szExeFile.decode('utf-8', errors='ignore').lower()
                if 'flightsimulator' in exe_name or 'flightsim' in exe_name:
                    found_pid = pe.th32ProcessID
                    found_name = pe.szExeFile.decode('utf-8', errors='ignore')
                    break
                if not ctypes.windll.kernel32.Process32Next(hSnapshot, ctypes.byref(pe)):
                    break
        ctypes.windll.kernel32.CloseHandle(hSnapshot)
    
    # Fallback Windows tasklist if Toolhelp snapshot was blocked by UWP/elevation
    if not found_pid:
        try:
            cmd = ['tasklist', '/FO', 'CSV', '/NH', '/FI', 'IMAGENAME eq FlightSimulator*']
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
            for line in out.splitlines():
                parts = [p.strip(' "') for p in line.split('","')]
                if len(parts) >= 2 and 'flightsimulator' in parts[0].lower():
                    found_pid = int(parts[1])
                    found_name = parts[0]
                    break
        except Exception:
            pass

    return found_pid, found_name

class PDH_FMT_COUNTERVALUE_ITEM_DOUBLE(ctypes.Structure):
    _fields_ = [
        ('szName', ctypes.wintypes.LPWSTR),
        ('CStatus', ctypes.wintypes.DWORD),
        ('dummy', ctypes.wintypes.DWORD),
        ('doubleValue', ctypes.c_double)
    ]

_cached_vram_pid = None
_cached_vram_query = None
_cached_vram_counter = None

def get_msfs_dedicated_vram_mb(pid):
    global _cached_vram_pid, _cached_vram_query, _cached_vram_counter
    if not pid:
        if _cached_vram_query:
            try:
                ctypes.windll.pdh.PdhCloseQuery(_cached_vram_query)
            except Exception:
                pass
            _cached_vram_query = None
            _cached_vram_counter = None
            _cached_vram_pid = None
        return 0.0

    if pid != _cached_vram_pid or _cached_vram_query is None:
        if _cached_vram_query:
            try:
                ctypes.windll.pdh.PdhCloseQuery(_cached_vram_query)
            except Exception:
                pass
            _cached_vram_query = None
            _cached_vram_counter = None

        hQuery = ctypes.wintypes.HANDLE()
        if ctypes.windll.pdh.PdhOpenQueryW(None, 0, ctypes.byref(hQuery)) != 0:
            return 0.0
        hCounter = ctypes.wintypes.HANDLE()
        counter_path = fr'\GPU Process Memory(pid_{pid}*)\Dedicated Usage'
        if ctypes.windll.pdh.PdhAddEnglishCounterW(hQuery, counter_path, 0, ctypes.byref(hCounter)) != 0:
            ctypes.windll.pdh.PdhCloseQuery(hQuery)
            return 0.0

        _cached_vram_query = hQuery
        _cached_vram_counter = hCounter
        _cached_vram_pid = pid

    try:
        if ctypes.windll.pdh.PdhCollectQueryData(_cached_vram_query) != 0:
            return 0.0
        bufferSize = ctypes.wintypes.DWORD(0)
        itemCount = ctypes.wintypes.DWORD(0)
        PDH_FMT_DOUBLE = 0x00000200
        ctypes.windll.pdh.PdhGetFormattedCounterArrayW(_cached_vram_counter, PDH_FMT_DOUBLE, ctypes.byref(bufferSize), ctypes.byref(itemCount), None)
        if bufferSize.value > 0:
            buf = (ctypes.c_char * bufferSize.value)()
            if ctypes.windll.pdh.PdhGetFormattedCounterArrayW(_cached_vram_counter, PDH_FMT_DOUBLE, ctypes.byref(bufferSize), ctypes.byref(itemCount), buf) == 0:
                items = ctypes.cast(buf, ctypes.POINTER(PDH_FMT_COUNTERVALUE_ITEM_DOUBLE))
                total_bytes = sum(items[i].doubleValue for i in range(itemCount.value))
                return round(total_bytes / (1024.0 * 1024.0), 1)
    except Exception:
        pass
    return 0.0

def get_msfs_process():
    try:
        pid, name = find_msfs_pid()
        if not pid:
            return None
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010
        hProcess = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if hProcess:
            pmc = PROCESS_MEMORY_COUNTERS_EX()
            pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
            ctypes.windll.psapi.GetProcessMemoryInfo(hProcess, ctypes.byref(pmc), pmc.cb)
            
            # Read CPU times
            c, e, k, u = FILETIME(), FILETIME(), FILETIME(), FILETIME()
            ctypes.windll.kernel32.GetProcessTimes(hProcess, ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u))
            cpu_sec = ((k.dwHighDateTime << 32 | k.dwLowDateTime) + (u.dwHighDateTime << 32 | u.dwLowDateTime)) / 10000000.0

            # Read Disk & Rolling Cache IO
            ioc = IO_COUNTERS()
            ctypes.windll.kernel32.GetProcessIoCounters(hProcess, ctypes.byref(ioc))
            read_bytes = ioc.ReadTransferCount
            
            ctypes.windll.kernel32.CloseHandle(hProcess)
            return {
                'name': name,
                'pid': pid,
                'ram_mb': round(pmc.WorkingSetSize / (1024 * 1024), 1),
                'commit_mb': round(pmc.PrivateUsage / (1024 * 1024), 1),
                'peak_ram_mb': round(pmc.PeakWorkingSetSize / (1024 * 1024), 1),
                'cpu_sec': cpu_sec,
                'read_bytes': read_bytes,
                'vram_mb': get_msfs_dedicated_vram_mb(pid)
            }
    except Exception:
        pass
    return None

def get_nvidia_gpu_telemetry():
    try:
        cmd = [
            'nvidia-smi',
            '--query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw,clocks.gr,utilization.memory',
            '--format=csv,noheader,nounits'
        ]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
        line = out.strip().splitlines()[0]
        parts = [v.strip() for v in line.split(',')]
        used = int(float(parts[0]))
        total = int(float(parts[1]))
        util = int(float(parts[2]))
        temp = int(float(parts[3]))
        power = round(float(parts[4]), 1) if len(parts) > 4 else 0.0
        clock = int(float(parts[5])) if len(parts) > 5 else 0
        mem_bus = int(float(parts[6])) if len(parts) > 6 else 0
        return {
            'vram_used_mb': used,
            'vram_total_mb': total,
            'vram_pct': round((used / total) * 100, 1),
            'gpu_util_pct': util,
            'gpu_temp_c': temp,
            'gpu_power_w': power,
            'gpu_clock_mhz': clock,
            'gpu_mem_bus_pct': mem_bus
        }
    except Exception:
        return {
            'vram_used_mb': 0, 'vram_total_mb': 0, 'vram_pct': 0.0,
            'gpu_util_pct': 0, 'gpu_temp_c': 0, 'gpu_power_w': 0.0,
            'gpu_clock_mhz': 0, 'gpu_mem_bus_pct': 0
        }

_last_autofps_cache = None

def get_latest_autofps_data():
    global _last_autofps_cache
    try:
        log_dir = os.path.expandvars(r'%APPDATA%\MSFS_AutoFPS\log')
        if not os.path.exists(log_dir):
            return _last_autofps_cache
        logs = glob.glob(os.path.join(log_dir, 'MSFS_AutoFPS*.log'))
        if not logs:
            return _last_autofps_cache
        latest_log = max(logs, key=os.path.getmtime)
        # Accepter les logs récents de la session (dernières 6 heures)
        if time.time() - os.path.getmtime(latest_log) > 21600:
            return _last_autofps_cache
        with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        for line in reversed(lines):
            if 'UpdateVariables' in line and 'FPS:' in line:
                fps_m = re.search(r'FPS:(\d+)', line)
                tlod_m = re.search(r'TLOD:(\d+)', line)
                olod_m = re.search(r'OLOD:(\d+)', line)
                agl_m = re.search(r'AGL:(-?\d+)', line)
                fpm_m = re.search(r'FPM:(-?\d+)', line)
                mode_m = re.search(r'Mode:([^\s]+(?:\s+[^\s]+)?)', line)
                
                raw_fps = int(fps_m.group(1)) if fps_m else None
                fg_mode = mode_m.group(1) if mode_m else ''
                # AutoFPS rapporte le FPS final affiché si > 55 avec FG 2X
                if '2X' in fg_mode and raw_fps and raw_fps > 55:
                    disp_fps = raw_fps
                    base_fps = round(raw_fps / 2)
                elif '2X' in fg_mode and raw_fps:
                    base_fps = raw_fps
                    disp_fps = raw_fps * 2
                else:
                    disp_fps = raw_fps
                    base_fps = raw_fps
                main_thread_ms = round(1000.0 / base_fps, 1) if (base_fps and base_fps > 0) else None
                
                _last_autofps_cache = {
                    'base_fps': base_fps,
                    'displayed_fps': disp_fps,
                    'main_thread_ms': main_thread_ms,
                    'tlod': int(tlod_m.group(1)) if tlod_m else None,
                    'olod': int(olod_m.group(1)) if olod_m else None,
                    'agl_ft': int(agl_m.group(1)) if agl_m else None,
                    'fpm': int(fpm_m.group(1)) if fpm_m else None,
                    'fg_mode': fg_mode
                }
                return _last_autofps_cache
    except Exception:
        pass
    return _last_autofps_cache

def get_autofps_config():
    """Lit et extrait les réglages cibles d'AutoFPS depuis le fichier de configuration actif."""
    appdata = os.getenv('APPDATA', '')
    cfg_path = os.path.join(appdata, 'MSFS_AutoFPS', 'MSFS2024_AutoFPS.config')
    if not os.path.exists(cfg_path):
        cfg_path = os.path.join(appdata, 'MSFS_AutoFPS', 'MSFS2020_AutoFPS.config')
    if not os.path.exists(cfg_path):
        return None
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(cfg_path)
        root = tree.getroot()
        settings = {}
        for add in root.findall('.//add'):
            k = add.get('key')
            v = add.get('value')
            if k and v:
                settings[k] = v
        return {
            'target_fps_fg': int(settings.get('targetFpsFG', 90)),
            'target_fps_pc': int(settings.get('targetFpsPC', 45)),
            'target_fps_vr': int(settings.get('targetFpsVR', 36)),
            'min_tlod': int(settings.get('minTLod', 100)),
            'max_tlod': int(settings.get('maxTLod', 200)),
            'alt_tlod_top': int(settings.get('AltTLODTop_SensTol', 5000)),
            'auto_reduce_settings': settings.get('AutoReduceSettings', 'false').lower() == 'true',
            'inc_cloud_quality': settings.get('IncCloudQNonExpert', 'false').lower() == 'true',
            'olod_base': int(settings.get('OLODAtBase', 100)),
            'olod_top': int(settings.get('OLODAtTop', 20))
        }
    except Exception:
        return None

def is_autofps_active():
    """Détecte si AutoFPS est actif et génère des mises à jour récentes."""
    try:
        log_dir = os.path.expandvars(r'%APPDATA%\MSFS_AutoFPS\log')
        if os.path.exists(log_dir):
            logs = glob.glob(os.path.join(log_dir, 'MSFS_AutoFPS*.log'))
            if logs:
                latest = max(logs, key=os.path.getmtime)
                if time.time() - os.path.getmtime(latest) < 60:
                    return True
    except Exception:
        pass
    return False

def check_autofps_cloud_events():
    """Vérifie dans les logs récents d'AutoFPS si une réduction de qualité des nuages a eu lieu."""
    try:
        log_dir = os.path.expandvars(r'%APPDATA%\MSFS_AutoFPS\log')
        if not os.path.exists(log_dir):
            return "Nominale"
        logs = glob.glob(os.path.join(log_dir, 'MSFS_AutoFPS*.log'))
        if not logs:
            return "Nominale"
        latest_log = max(logs, key=os.path.getmtime)
        with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        recent = lines[-200:]
        reduced = False
        initial_q = "High"
        for l in recent:
            if "Initial Cloud Quality" in l:
                initial_q = l.split("Initial Cloud Quality")[-1].strip()
            if "Reducing Cloud Quality" in l:
                reduced = True
        if reduced:
            return f"Réductions automatiques déclenchées en vol (Initial : {initial_q})"
        return f"Qualité nominale maintenue ({initial_q}) - Aucun décrochage nuages"
    except Exception:
        return "Qualité nominale maintenue"

_AIRPORT_GEO_CACHE = None

def get_airport_geo_cache():
    global _AIRPORT_GEO_CACHE
    if _AIRPORT_GEO_CACHE is not None:
        return _AIRPORT_GEO_CACHE
    
    path = "airports.json"
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        p_frozen = os.path.join(sys._MEIPASS, "airports.json")
        if os.path.exists(p_frozen):
            path = p_frozen
    if not os.path.exists(path):
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "airports.json")

    cache = []
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                for icao, ap in data.items():
                    if len(icao) == 4 and ap.get('lat') is not None and ap.get('lon') is not None:
                        cache.append((icao, ap.get('name', ''), float(ap['lat']), float(ap['lon'])))
        except Exception:
            pass
    _AIRPORT_GEO_CACHE = cache
    return _AIRPORT_GEO_CACHE

def find_nearest_airport(lat, lon):
    if lat is None or lon is None:
        return None, "", 999999.0
    cache = get_airport_geo_cache()
    if not cache:
        return None, "", 999999.0

    best_icao = None
    best_name = ""
    min_d_sq = 999999.0
    for icao, name, alat, alon in cache:
        d_sq = (lat - alat)**2 + (lon - alon)**2
        if d_sq < min_d_sq:
            min_d_sq = d_sq
            best_icao = icao
            best_name = name

    nm_dist = (min_d_sq ** 0.5) * 60.0
    return best_icao, best_name, nm_dist

def resolve_flight_context(lat=None, lon=None, on_ground=False):
    """
    Détermine automatiquement l'appareil, la route, le point de départ
    ou la position la plus proche selon que le joueur utilise un profil SceneryX
    ou vole librement (au sol ou spawn en vol).
    """
    mode_str, is_corridor, dep, arr, dis_count, prof_slug = get_sceneryx_flight_mode()

    route_display = ""
    mode_display = "BASELINE STANDARD"

    if is_corridor and dep and arr:
        if prof_slug == 'direct':
            mode_display = f"A ➔ B DIRECT ({dis_count} scènes isolées)"
            route_display = f"{dep} ➔ {arr}"
        elif prof_slug == 'simbrief':
            mode_display = f"SIMBRIEF ({dis_count} scènes isolées)"
            route_display = f"{dep} ➔ {arr}"
        else:
            mode_display = f"COULOIR ({dis_count} scènes isolées)"
            route_display = f"{dep} ➔ {arr}"
    else:
        if lat is not None and lon is not None:
            # Handle possible radians conversion
            if abs(lat) <= 3.14159 and abs(lon) <= 3.14159 and (lat != 0.0 or lon != 0.0):
                lat = math.degrees(lat)
                lon = math.degrees(lon)
            near_icao, near_name, dist_nm = find_nearest_airport(lat, lon)
            if near_icao:
                if on_ground or dist_nm <= 4.0:
                    route_display = f"Départ : {near_icao} ({near_name})"
                else:
                    route_display = f"En vol à ~{int(round(dist_nm))} NM de {near_icao}"
            else:
                route_display = "Vol libre"
        else:
            route_display = "Vol libre (GPS en attente)"

    return {
        "route_display": route_display,
        "mode_display": mode_display,
        "is_corridor": is_corridor,
        "dep": dep,
        "arr": arr,
        "disabled_count": dis_count,
        "prof_slug": prof_slug
    }

def analyze_flight_milestones(samples, session_info=None):
    """
    Analyse chronologique complète des phases de vol :
    Taxi-Out (Départ), Montée Initiale, Montée/Plafond TLOD, Croisière,
    Descente, Approche Finale & Toucher, Taxi-In (Arrivée).
    Mesure les impacts de scène d'aéroports et du trafic sol.
    """
    if not samples:
        return []

    def avg(lst, key):
        vals = [s[key] for s in lst if s.get(key) is not None]
        return round(sum(vals)/len(vals), 1) if vals else 'N/A'

    def mode_val(lst, key):
        vals = [s[key] for s in lst if s.get(key) is not None]
        return round(sum(vals)/len(vals)) if vals else 'N/A'

    dep = ""
    arr = ""
    if session_info:
        dep = session_info.get('dep') or session_info.get('cur_dep') or ""
        arr = session_info.get('arr') or session_info.get('cur_arr') or ""

    # Détection des échantillons en vol (airborne)
    # Un point est considéré en l'air si on_ground == False et agl > 40, ou si agl >= 80 ft
    airborne_indices = [
        i for i, s in enumerate(samples)
        if (s.get('on_ground') is False and (s.get('agl_ft') is None or s.get('agl_ft') > 40))
        or (s.get('agl_ft') is not None and s.get('agl_ft') >= 80)
    ]

    milestones = []

    # CAS 1 : Aucun échantillon en l'air (Vol entièrement au sol / Test Taxi sur aéroport)
    if not airborne_indices:
        taxi_samples = [s for s in samples if s.get('agl_ft') is None or s.get('agl_ft') < 200]
        if taxi_samples:
            milestones.append({
                'phase': f"Roulage au Sol ({dep})" if dep else "Roulage au Sol (Taxi)",
                'alt': 'Sol (0 - 50 ft)',
                'tlod': str(mode_val(taxi_samples, 'tlod')),
                'olod': str(mode_val(taxi_samples, 'olod')),
                'fps': str(avg(taxi_samples, 'disp_fps')) + ' FPS',
                'mt': str(avg(taxi_samples, 'main_thread_ms')) + ' ms',
                'notes': 'Test de scène aéroportuaire & trafic au sol (Stationnaire / Roulage)'
            })
        return milestones

    # CAS 2 : Le vol comporte des phases en l'air
    idx_takeoff = airborne_indices[0]
    idx_touchdown = airborne_indices[-1]

    # --- 1. TAXI-OUT (Roulage au sol avant décollage) ---
    if idx_takeoff > 0:
        taxi_out_samples = [
            samples[i] for i in range(idx_takeoff)
            if samples[i].get('on_ground', True) and (samples[i].get('agl_ft') is None or samples[i].get('agl_ft') < 80)
        ]
        if len(taxi_out_samples) >= 3:
            taxi_out_title = f"Taxi Out ({dep})" if dep else "Taxi Out (Roulage Départ)"
            milestones.append({
                'phase': taxi_out_title,
                'alt': 'Sol (0 ft)',
                'tlod': str(mode_val(taxi_out_samples, 'tlod')),
                'olod': str(mode_val(taxi_out_samples, 'olod')),
                'fps': str(avg(taxi_out_samples, 'disp_fps')) + ' FPS',
                'mt': str(avg(taxi_out_samples, 'main_thread_ms')) + ' ms',
                'notes': 'Impact scène aéroport de départ, bâtiments & trafic sol'
            })

    # Analyse des données en vol (entre décollage et atterrissage)
    flight_samples = samples[idx_takeoff : idx_touchdown + 1]
    
    # Trouver le pic d'altitude et son index
    max_agl = 0
    idx_peak = idx_takeoff
    for i in range(idx_takeoff, idx_touchdown + 1):
        cur_agl = samples[i].get('agl_ft') or 0
        if cur_agl > max_agl:
            max_agl = cur_agl
            idx_peak = i

    # --- 2. MONTÉE INITIALE (0 - 3 000 ft) ---
    climb_init_samples = [
        samples[i] for i in range(idx_takeoff, idx_peak + 1)
        if (samples[i].get('agl_ft') is not None and samples[i].get('agl_ft') < 3000)
    ]
    if climb_init_samples:
        milestones.append({
            'phase': 'Montée Initiale',
            'alt': '0 - 3 000 ft',
            'tlod': str(mode_val(climb_init_samples, 'tlod')),
            'olod': str(mode_val(climb_init_samples, 'olod')),
            'fps': str(avg(climb_init_samples, 'disp_fps')) + ' FPS',
            'mt': str(avg(climb_init_samples, 'main_thread_ms')) + ' ms',
            'notes': 'Dégagement sol et escalade progressive du TLOD'
        })

    # --- 3. MONTÉE & PLAFOND TLOD (3 000 - 10 000 ft) ---
    climb_mid_samples = [
        samples[i] for i in range(idx_takeoff, idx_peak + 1)
        if (samples[i].get('agl_ft') is not None and 3000 <= samples[i].get('agl_ft') < 10000)
    ]
    if climb_mid_samples:
        milestones.append({
            'phase': 'Plafond TLOD',
            'alt': '3 000 - 10 000 ft',
            'tlod': str(mode_val(climb_mid_samples, 'tlod')),
            'olod': str(mode_val(climb_mid_samples, 'olod')),
            'fps': str(avg(climb_mid_samples, 'disp_fps')) + ' FPS',
            'mt': str(avg(climb_mid_samples, 'main_thread_ms')) + ' ms',
            'notes': 'LOD max atteint en montée'
        })

    # --- 4. CROISIÈRE HAUTE ALTITUDE (Altitude croisière ou > 10 000 ft) ---
    if max_agl >= 10000:
        cruise_samples = [
            s for s in flight_samples
            if s.get('agl_ft') is not None and s.get('agl_ft') >= 10000
        ]
        cruise_label = 'Croisière Haute Altitude'
        cruise_alt_str = '> 10 000 ft'
    elif max_agl >= 2000:
        threshold = max_agl * 0.85
        cruise_samples = [
            s for s in flight_samples
            if (s.get('agl_ft') or 0) >= threshold and abs(s.get('fpm') or 0) < 500
        ]
        cruise_label = 'Palier de Croisière'
        cruise_alt_str = f'~{mode_val(cruise_samples, "agl_ft")} ft' if cruise_samples else f'{max_agl} ft'
    else:
        cruise_samples = []
        cruise_label = 'Croisière'
        cruise_alt_str = ''

    if cruise_samples:
        milestones.append({
            'phase': cruise_label,
            'alt': cruise_alt_str,
            'tlod': str(mode_val(cruise_samples, 'tlod')),
            'olod': str(mode_val(cruise_samples, 'olod')),
            'fps': str(avg(cruise_samples, 'disp_fps')) + ' FPS',
            'mt': str(avg(cruise_samples, 'main_thread_ms')) + ' ms',
            'notes': 'Rendu horizon étendu et stabilité FPS'
        })

    # --- 5. DESCENTE (après le pic, altitude >= 3 000 ft) ---
    descent_samples = [
        samples[i] for i in range(idx_peak + 1, idx_touchdown + 1)
        if (samples[i].get('agl_ft') is not None and samples[i].get('agl_ft') >= 3000 and (samples[i].get('fpm') or 0) <= 200)
    ]
    if descent_samples:
        milestones.append({
            'phase': 'Descente',
            'alt': '> 3 000 ft',
            'tlod': str(mode_val(descent_samples, 'tlod')),
            'olod': str(mode_val(descent_samples, 'olod')),
            'fps': str(avg(descent_samples, 'disp_fps')) + ' FPS',
            'mt': str(avg(descent_samples, 'main_thread_ms')) + ' ms',
            'notes': 'Descente d\'altitude & chargement scènes d\'arrivée'
        })

    # --- 6. APPROCHE FINALE & TOUCHER (après le pic, altitude < 3 000 ft) ---
    approach_samples = [
        samples[i] for i in range(idx_peak + 1, idx_touchdown + 1)
        if (samples[i].get('agl_ft') is not None and samples[i].get('agl_ft') < 3000)
    ]
    if approach_samples:
        milestones.append({
            'phase': 'Approche Finale & Toucher',
            'alt': '3 000 - 0 ft',
            'tlod': str(mode_val(approach_samples, 'tlod')),
            'olod': str(mode_val(approach_samples, 'olod')),
            'fps': str(avg(approach_samples, 'disp_fps')) + ' FPS',
            'mt': str(avg(approach_samples, 'main_thread_ms')) + ' ms',
            'notes': 'Alignement, capture piste & décors d\'approche'
        })

    # --- 7. TAXI-IN (Roulage au sol après atterrissage) ---
    if idx_touchdown < len(samples) - 1:
        taxi_in_samples = [
            samples[i] for i in range(idx_touchdown + 1, len(samples))
            if samples[i].get('on_ground', True) and (samples[i].get('agl_ft') is None or samples[i].get('agl_ft') < 80)
        ]
        if len(taxi_in_samples) >= 3:
            taxi_in_title = f"Taxi In ({arr})" if arr else "Taxi In (Roulage Arrivée)"
            milestones.append({
                'phase': taxi_in_title,
                'alt': 'Sol (0 ft)',
                'tlod': str(mode_val(taxi_in_samples, 'tlod')),
                'olod': str(mode_val(taxi_in_samples, 'olod')),
                'fps': str(avg(taxi_in_samples, 'disp_fps')) + ' FPS',
                'mt': str(avg(taxi_in_samples, 'main_thread_ms')) + ' ms',
                'notes': 'Impact scène aéroport d\'arrivée, taxiways & parking gate'
            })

    return milestones

class SimConnectTelemetryClient:
    """
    Client de télémétrie natif haute précision SimConnect.
    Capture en continu les événements Frame (fFrameRate réel) et SimVars de vol
    directement depuis le moteur MSFS via l'API officielle SimConnect.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self.connected = False
        self.sc = None
        self.simdata_dd = None
        self.frame_rate = None
        self.base_fps = None
        self.displayed_fps = None
        self.frame_time_ms = None
        self.agl_ft = None
        self.vertical_speed_fpm = None
        self.airspeed_kts = None
        self.ground_speed_kts = None
        self.on_ground = None
        self.aircraft_title = None
        self.lat = None
        self.lon = None
        self._stop_event = threading.Event()
        self._thread = None
        self._accum_fps = 0.0
        self._frame_count = 0
        self._latest_instant_fps = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="SimConnectTelemetryWorker")
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._cleanup()

    def _cleanup(self):
        with self._lock:
            self.connected = False
            self.frame_rate = None
            self.base_fps = None
            self.displayed_fps = None
            self.frame_time_ms = None
            self.agl_ft = None
            self.vertical_speed_fpm = None
            self.airspeed_kts = None
            self.ground_speed_kts = None
            self.on_ground = None
            self.aircraft_title = None
            self.lat = None
            self.lon = None
            self._accum_fps = 0.0
            self._frame_count = 0
            self._latest_instant_fps = None
        if self.sc:
            try:
                self.sc.Close()
            except Exception:
                pass
            self.sc = None
        self.simdata_dd = None

    def _on_frame(self, recv):
        try:
            fps = float(recv.fFrameRate)
            if fps > 0.0:
                with self._lock:
                    self._accum_fps += fps
                    self._frame_count += 1
                    self._latest_instant_fps = fps
        except Exception:
            pass
        return True

    def _run_loop(self):
        while not self._stop_event.is_set():
            if not HAS_SIMCONNECT:
                self._stop_event.wait(5.0)
                continue

            # Tenter la connexion SimConnect si non connectée
            if not self.connected or self.sc is None:
                try:
                    sc = SimConnect(name='SceneryX_Telemetry', poll_interval_seconds=0.02)
                    sc.add_receiver(RECV_EVENT_FRAME, self._on_frame)
                    EVENT_ID_FRAME = 1
                    sc.SubscribeToSystemEvent(EVENT_ID_FRAME, "Frame")

                    # Souscription aux SimVars de vol
                    try:
                        simvars = [
                            {"name": "PLANE ALT ABOVE GROUND", "units": "feet"},
                            {"name": "VERTICAL SPEED", "units": "feet/minute"},
                            {"name": "AIRSPEED INDICATED", "units": "knots"},
                            {"name": "GROUND VELOCITY", "units": "knots"},
                            {"name": "SIM ON GROUND", "units": "bool"},
                            {"name": "PLANE LATITUDE", "units": "degrees"},
                            {"name": "PLANE LONGITUDE", "units": "degrees"},
                            {"name": "TITLE"}
                        ]
                        simdata_dd = sc.subscribe_simdata(simvars, period=PERIOD_SECOND)
                    except Exception:
                        simdata_dd = None

                    self.sc = sc
                    self.simdata_dd = simdata_dd
                    with self._lock:
                        self.connected = True
                        self._accum_fps = 0.0
                        self._frame_count = 0
                except Exception:
                    self._cleanup()
                    self._stop_event.wait(2.5)
                    continue

            # Boucle active de réception de télémétrie
            last_calc_time = time.time()
            try:
                while not self._stop_event.is_set():
                    self.sc.receive(timeout_seconds=0.05)
                    time.sleep(0.01)

                    now = time.time()
                    if now - last_calc_time >= 0.5:
                        with self._lock:
                            if self._frame_count > 0:
                                avg_fps = self._accum_fps / self._frame_count
                            elif self._latest_instant_fps:
                                avg_fps = self._latest_instant_fps
                            else:
                                avg_fps = None

                            if avg_fps and avg_fps > 0:
                                self.frame_rate = round(avg_fps, 1)
                                self.base_fps = round(avg_fps)
                                self.frame_time_ms = round(1000.0 / avg_fps, 1)

                                # Vérifier l'état Frame Generation dans UserCfg.opt
                                fg_active = False
                                try:
                                    import flight_rig_optimizer
                                    user_cfg = flight_rig_optimizer.detect_msfs_user_cfg()
                                    fg_active = user_cfg.get("frame_generation", False)
                                except Exception:
                                    pass

                                if fg_active:
                                    self.displayed_fps = round(avg_fps * 2)
                                else:
                                    self.displayed_fps = self.base_fps

                                self._accum_fps = 0.0
                                self._frame_count = 0

                            # Mise à jour des SimVars
                            if self.simdata_dd and getattr(self.simdata_dd, 'simdata', None):
                                sdata = self.simdata_dd.simdata
                                if 'PLANE ALT ABOVE GROUND' in sdata and sdata['PLANE ALT ABOVE GROUND'] is not None:
                                    self.agl_ft = round(float(sdata['PLANE ALT ABOVE GROUND']))
                                if 'VERTICAL SPEED' in sdata and sdata['VERTICAL SPEED'] is not None:
                                    self.vertical_speed_fpm = round(float(sdata['VERTICAL SPEED']))
                                if 'AIRSPEED INDICATED' in sdata and sdata['AIRSPEED INDICATED'] is not None:
                                    self.airspeed_kts = round(float(sdata['AIRSPEED INDICATED']))
                                if 'GROUND VELOCITY' in sdata and sdata['GROUND VELOCITY'] is not None:
                                    self.ground_speed_kts = round(float(sdata['GROUND VELOCITY']))
                                if 'SIM ON GROUND' in sdata and sdata['SIM ON GROUND'] is not None:
                                    self.on_ground = bool(sdata['SIM ON GROUND'])
                                if 'PLANE LATITUDE' in sdata and sdata['PLANE LATITUDE'] is not None:
                                    lat_val = float(sdata['PLANE LATITUDE'])
                                    if abs(lat_val) <= 3.14159 and lat_val != 0.0:
                                        lat_val = math.degrees(lat_val)
                                    self.lat = lat_val
                                if 'PLANE LONGITUDE' in sdata and sdata['PLANE LONGITUDE'] is not None:
                                    lon_val = float(sdata['PLANE LONGITUDE'])
                                    if abs(lon_val) <= 3.14159 and lon_val != 0.0:
                                        lon_val = math.degrees(lon_val)
                                    self.lon = lon_val
                                if 'TITLE' in sdata and sdata['TITLE']:
                                    t_str = str(sdata['TITLE']).strip()
                                    if t_str and t_str.lower() != 'none':
                                        self.aircraft_title = t_str

                        last_calc_time = now

            except Exception:
                self._cleanup()
                self._stop_event.wait(2.0)

    def get_data(self):
        with self._lock:
            return {
                "connected": self.connected,
                "base_fps": self.base_fps,
                "displayed_fps": self.displayed_fps,
                "frame_time_ms": self.frame_time_ms,
                "agl_ft": self.agl_ft,
                "fpm": self.vertical_speed_fpm,
                "airspeed_kts": self.airspeed_kts,
                "ground_speed_kts": self.ground_speed_kts,
                "on_ground": self.on_ground,
                "aircraft": self.aircraft_title,
                "lat": self.lat,
                "lon": self.lon
            }

SIMCONNECT_CLIENT = SimConnectTelemetryClient()
SIMCONNECT_CLIENT.start()

def get_sceneryx_flight_mode():
    appdata = os.getenv('APPDATA', '')
    settings_path = os.path.join(appdata, 'SceneryX', 'settings.json')
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                fm = data.get('flight_mode', {})
                if isinstance(fm, dict) and fm.get('active'):
                    dep = fm.get('dep_icao', 'DEP')
                    arr = fm.get('arr_icao', 'ARR')
                    dis = fm.get('disabled_count', 0)
                    alts_raw = fm.get('alternates', [])
                    alts = [a if isinstance(a, str) else a.get('icao', '') for a in alts_raw]
                    alts = [a for a in alts if a]
                    profile = fm.get('profile', 'CORRIDOR').upper()
                    alt_str = f" [Alts: {','.join(alts)}]" if alts else ""
                    if profile == 'DIRECT':
                        return f"SCENERYX DIRECT A->B ({dep} -> {arr} | {dis} scènes isolées)", True, dep, arr, dis, 'direct'
                    elif profile == 'SIMBRIEF':
                        return f"SCENERYX SIMBRIEF ({dep} -> {arr}{alt_str} | {dis} scènes isolées)", True, dep, arr, dis, 'simbrief'
                    else:
                        return f"SCENERYX COULOIR ({dep} -> {arr}{alt_str} | {dis} scènes isolées)", True, dep, arr, dis, 'corridor'
        except Exception:
            pass
    return "BASELINE STANDARD (Toutes scènes actives)", False, "", "", 0, "baseline_full"

def format_time_delta(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}h {m:02d}m {s:02d}s"
    return f"{m:02d}m {s:02d}s"

def get_benchmarks_directory():
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    benchmarks_dir = os.path.join(base_dir, 'benchmarks')
    os.makedirs(benchmarks_dir, exist_ok=True)
    return benchmarks_dir


def generate_automated_flight_narrative(samples, session_info):
    """
    Génère un diagnostic textuel expert et automatisé du vol
    expliquant les goulots d'étranglement, la VRAM et l'activité cache.
    """
    if not samples:
        return "<p>Aucune donnée suffisante pour générer un diagnostic.</p>"

    vrams = [s['vram_used'] for s in samples]
    commits = [s['msfs_commit'] for s in samples]
    fps_list = [s['disp_fps'] for s in samples if s.get('disp_fps') is not None]
    mt_list = [s['main_thread_ms'] for s in samples if s.get('main_thread_ms') is not None]
    gpus = [s['gpu_util'] for s in samples]
    tlods = [s['tlod'] for s in samples if s.get('tlod') is not None]
    io_reads = [s.get('cache_read_mbps', 0) for s in samples]

    peak_vram = max(vrams) if vrams else 0
    total_vram = samples[0].get('vram_total', 16376) if samples else 16376
    vram_peak_pct = round((peak_vram / total_vram) * 100, 1) if total_vram else 0
    avg_vram = round(sum(vrams) / len(vrams), 0) if vrams else 0

    avg_fps = round(sum(fps_list) / len(fps_list), 1) if fps_list else "N/A"
    avg_mt = round(sum(mt_list) / len(mt_list), 1) if mt_list else "N/A"
    avg_gpu = round(sum(gpus) / len(gpus), 1) if gpus else 0
    avg_tlod = round(sum(tlods) / len(tlods), 0) if tlods else "Fixe"
    peak_io = round(max(io_reads), 1) if io_reads else 0.0

    # AutoFPS Info
    autofps_active = session_info.get('autofps_active', False)
    autofps_cfg = session_info.get('autofps_config', {})
    cloud_status = session_info.get('cloud_events', 'Nominale')

    autofps_diag = ""
    if autofps_active and autofps_cfg:
        tfps = autofps_cfg.get('target_fps_fg') or autofps_cfg.get('targetFps', '--')
        min_t = autofps_cfg.get('min_tlod') or autofps_cfg.get('minTLod', '--')
        max_t = autofps_cfg.get('max_tlod') or autofps_cfg.get('maxTLod', '--')
        autofps_diag = f"<li><strong>Intégration AutoFPS Active :</strong> Cible de {tfps} FPS, plage TLOD configurée de {min_t} à {max_t}. TLOD moyen effectif mesuré à <strong>{avg_tlod}</strong>. État nuages : <em>{cloud_status}</em>.</li>"
    elif autofps_active:
        autofps_diag = f"<li><strong>Intégration AutoFPS Active :</strong> Ajustements dynamiques du TLOD détectés (TLOD moyen en vol : <strong>{avg_tlod}</strong>). État nuages : <em>{cloud_status}</em>.</li>"
    else:
        autofps_diag = f"<li><strong>Gestion LOD :</strong> AutoFPS non actif (valeurs statiques ou fixes, TLOD moyen : <strong>{avg_tlod}</strong>).</li>"

    # Diagnostic du goulot d'étranglement principal
    if avg_gpu >= 96 and (avg_mt != "N/A" and avg_mt <= 25.0):
        bottleneck_diag = "<strong>Profil GPU-Bound équilibré :</strong> La carte graphique RTX a tourné à plein régime avec une fluidité optimale, sans blocage sévère du MainThread."
    elif avg_mt != "N/A" and avg_mt > 30.0:
        bottleneck_diag = f"<strong>Profil MainThread Limité ({avg_mt} ms en moyenne) :</strong> Le fil processeur principal a été le facteur limitant, typique des phases au sol avec avionique complexe et décors denses."
    else:
        bottleneck_diag = "<strong>Profil Mixte Équilibré :</strong> Répartition harmonieuse entre la charge de calcul CPU et le rendu graphique."

    # Diagnostic VRAM & Paging
    if vram_peak_pct >= 92.0:
        vram_diag = f"<span style='color:#ef4444;'><strong>Alerte Risque de Paging :</strong> La VRAM a culminé à {peak_vram:,.0f} Mo ({vram_peak_pct}%). Proche du seuil de débordement vers la RAM système, pouvant causer des micro-saccades en vue externe.</span>"
    elif vram_peak_pct >= 85.0:
        vram_diag = f"<span style='color:#f59e0b;'><strong>Zone Haute Maîtrisée :</strong> VRAM crête à {peak_vram:,.0f} Mo ({vram_peak_pct}%). Marge de sécurité suffisante sans déclenchement de mémoire paginée.</span>"
    else:
        vram_diag = f"<span style='color:#10b981;'><strong>Excellente Marge Vidéo :</strong> VRAM crête contenue à {peak_vram:,.0f} Mo ({vram_peak_pct}%). L'isolation SceneryX a éliminé les textures en surplus.</span>"

    # Diagnostic spécifique des impacts au sol & aéroports
    milestones = analyze_flight_milestones(samples, session_info)
    ground_notes = []
    for m in milestones:
        if 'Taxi Out' in m['phase'] or 'Taxi In' in m['phase']:
            ground_notes.append(f"{m['phase']} : <strong>{m['fps']}</strong> (MainThread <strong>{m['mt']}</strong>)")
        elif 'Approche' in m['phase']:
            ground_notes.append(f"Approche Finale : <strong>{m['fps']}</strong> (MainThread <strong>{m['mt']}</strong>)")

    ground_diag = ""
    if ground_notes:
        ground_diag = f"<li><strong>Comportement Sol & Aéroports :</strong> {' • '.join(ground_notes)}.</li>"

    narrative = f"""
    <div style="background:#0f172a; border:1px solid #1e293b; border-radius:16px; padding:20px; margin-bottom:24px; line-height:1.6; font-size:13px; color:#cbd5e1;">
        <h3 style="margin-top:0; color:#38bdf8; font-size:16px;">📝 Compte-Rendu d'Analyse du Vol</h3>
        <ul style="padding-left:20px; margin-bottom:12px;">
            <li><strong>Comportement Système & Goulot d'Étranglement :</strong> {bottleneck_diag}</li>
            <li><strong>Empreinte Mémoire Vidéo (VRAM) :</strong> {vram_diag}</li>
            <li><strong>Fluidité & Affichage :</strong> Moyenne globale de <strong>{avg_fps} FPS</strong> avec un MainThread moyen de <strong>{avg_mt} ms</strong>.</li>
            {ground_diag}
            {autofps_diag}
            <li><strong>Activité Rolling Cache / Débit Disque :</strong> Pics d'accès aux textures et modèles de <strong>{peak_io} Mbps</strong> enregistrés lors des changements de zone géographique.</li>
        </ul>
        <div style="background:rgba(56, 189, 248, 0.08); border-left:3px solid #38bdf8; padding:8px 14px; border-radius:4px; font-size:12px;">
            <strong>Recommandation pour le prochain vol :</strong> Maintenir l'isolation active sur le corridor ou mode direct pour pérenniser l'économie de VRAM et la stabilité du MainThread sur les aéroports d'arrivée.
        </div>
    </div>
    """
    return narrative


def generate_html_report(csv_path, session_info, samples):
    html_path = csv_path.replace('.csv', '.html')
    os.makedirs(os.path.dirname(os.path.abspath(html_path)), exist_ok=True)
    
    times = [s['elapsed'] for s in samples]
    vram_vals = [s['vram_used'] for s in samples]
    msfs_ram_vals = [s['msfs_ram'] for s in samples]
    msfs_commit_vals = [s['msfs_commit'] for s in samples]
    gpu_power_vals = [s.get('gpu_power_w', 0) for s in samples]
    io_reads_mbps = [s.get('cache_read_mbps', 0) for s in samples]

    fps_vals = [s['disp_fps'] for s in samples if s.get('disp_fps') is not None]
    base_fps_vals = [s['base_fps'] for s in samples if s.get('base_fps') is not None]
    mainthread_vals = [s['main_thread_ms'] for s in samples if s.get('main_thread_ms') is not None]

    # Détection Frame Generation
    is_fg_used = any(
        (s.get('disp_fps') and s.get('base_fps') and s['disp_fps'] >= s['base_fps'] * 1.4)
        or ('2X' in str(s.get('fg_mode', '')).upper())
        for s in samples
    )

    avg_fps = round(sum(fps_vals) / len(fps_vals), 1) if fps_vals else "N/A"
    max_fps = max(fps_vals) if fps_vals else "N/A"
    min_fps = min(fps_vals) if fps_vals else "N/A"

    avg_base_fps = round(sum(base_fps_vals) / len(base_fps_vals), 1) if base_fps_vals else "N/A"
    max_base_fps = max(base_fps_vals) if base_fps_vals else "N/A"
    min_base_fps = min(base_fps_vals) if base_fps_vals else "N/A"

    avg_mt = round(sum(mainthread_vals) / len(mainthread_vals), 1) if mainthread_vals else "N/A"
    min_mt = min(mainthread_vals) if mainthread_vals else "N/A"
    max_mt = max(mainthread_vals) if mainthread_vals else "N/A"

    # VRAM (exprimée en Go)
    peak_vram_mb = max(vram_vals) if vram_vals else 0
    avg_vram_mb = round(sum(vram_vals) / len(vram_vals), 1) if vram_vals else 0
    min_vram_mb = min(vram_vals) if vram_vals else 0
    total_vram_mb = samples[0].get('vram_total', 16376) if samples else 16376
    peak_vram_pct = round((peak_vram_mb / total_vram_mb) * 100, 1) if total_vram_mb else 0

    avg_vram_gb = round(avg_vram_mb / 1024.0, 1)
    min_vram_gb = round(min_vram_mb / 1024.0, 1)
    peak_vram_gb = round(peak_vram_mb / 1024.0, 1)
    total_vram_gb = round(total_vram_mb / 1024.0, 1)

    # RAM Working Set (exprimée en Go)
    peak_ram_mb = max(msfs_ram_vals) if msfs_ram_vals else 0
    avg_ram_mb = round(sum(msfs_ram_vals) / len(msfs_ram_vals), 1) if msfs_ram_vals else 0
    min_ram_mb = min(msfs_ram_vals) if msfs_ram_vals else 0

    avg_ram_gb = round(avg_ram_mb / 1024.0, 1)
    min_ram_gb = round(min_ram_mb / 1024.0, 1)
    peak_ram_gb = round(peak_ram_mb / 1024.0, 1)

    # RAM Commit (exprimée en Go)
    peak_commit_mb = max(msfs_commit_vals) if msfs_commit_vals else 0
    avg_commit_mb = round(sum(msfs_commit_vals) / len(msfs_commit_vals), 1) if msfs_commit_vals else 0
    min_commit_mb = min(msfs_commit_vals) if msfs_commit_vals else 0

    avg_commit_gb = round(avg_commit_mb / 1024.0, 1)
    min_commit_gb = round(min_commit_mb / 1024.0, 1)
    peak_commit_gb = round(peak_commit_mb / 1024.0, 1)

    # Puissance GPU
    avg_power = round(sum(gpu_power_vals) / len(gpu_power_vals), 1) if gpu_power_vals else 0
    peak_power = round(max(gpu_power_vals), 1) if gpu_power_vals else 0
    min_power = round(min(gpu_power_vals), 1) if gpu_power_vals else 0

    mode_title = session_info['mode_str']
    is_corridor = session_info['is_corridor']
    badge_color = "#10b981" if is_corridor else "#f59e0b"
    badge_text = "OPTIMISÉ SCENERYX" if is_corridor else "BASELINE STANDARD"

    aircraft_display = session_info.get('aircraft') or "Non détecté / Générique"
    route_display = session_info.get('route_display') or "Non spécifiée"
    mode_display = session_info.get('mode_display') or session_info.get('mode_str', 'BASELINE STANDARD')
    autofps_active = session_info.get('autofps_active', False)
    autofps_cfg = session_info.get('autofps_config', {})
    cloud_status = session_info.get('cloud_events', 'Nominale')

    if autofps_active:
        tfps = autofps_cfg.get('target_fps_fg') or autofps_cfg.get('targetFps', '--') if autofps_cfg else '--'
        min_t = autofps_cfg.get('min_tlod') or autofps_cfg.get('minTLod', '--') if autofps_cfg else '--'
        max_t = autofps_cfg.get('max_tlod') or autofps_cfg.get('maxTLod', '--') if autofps_cfg else '--'
        cfg_sub = f" (Cible {tfps} FPS | TLOD {min_t}-{max_t})" if autofps_cfg else ""
        autofps_badge_html = f'<span style="color:#38bdf8; font-weight:bold; font-family:monospace; background:rgba(56,189,248,0.15); border:1px solid #38bdf8; padding:3px 8px; border-radius:6px; font-size:11px;">AUTOFPS LIVE{cfg_sub}</span>'
    else:
        autofps_badge_html = '<span style="color:#94a3b8; font-size:11px; background:rgba(148,163,184,0.1); border:1px solid #334155; padding:3px 8px; border-radius:6px;">Inactif / Non Détecté</span>'

    # Build Milestones section
    milestones = analyze_flight_milestones(samples, session_info)
    if milestones:
        rows_html = ""
        for m in milestones:
            rows_html += f"""
            <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                <td style="padding:10px 12px; font-weight:bold; color:#f8fafc;">{m['phase']}</td>
                <td style="padding:10px 12px; color:#38bdf8; font-family:monospace;">{m['alt']}</td>
                <td style="padding:10px 12px; color:#a855f7; font-family:monospace; font-weight:bold;">{m['tlod']}</td>
                <td style="padding:10px 12px; color:#a855f7; font-family:monospace;">{m['olod']}</td>
                <td style="padding:10px 12px; color:#10b981; font-family:monospace; font-weight:bold;">{m['fps']}</td>
                <td style="padding:10px 12px; color:#f59e0b; font-family:monospace; font-weight:bold;">{m['mt']}</td>
                <td style="padding:10px 12px; color:#cbd5e1; font-size:12px;">{m['notes']}</td>
            </tr>
            """
        milestones_section = f"""
        <div class="chart-box" style="padding: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:8px;">
                <div class="chart-title" style="margin-bottom:0;">🛫 Analyse des Phases de Vol, Paliers d'Altitude & Impacts Sol/LOD</div>
                <div style="font-size:12px; color:#94a3b8;">Qualité Nuages AutoFPS : <span style="color:#38bdf8; font-weight:bold;">{cloud_status}</span></div>
            </div>
            <div style="overflow-x:auto;">
                <table style="width:100%; border-collapse:collapse; font-size:13px; text-align:left;">
                    <thead>
                        <tr style="border-bottom:1px solid #334155; color:#94a3b8; font-size:11px; text-transform:uppercase;">
                            <th style="padding:8px 12px;">Phase de Vol</th>
                            <th style="padding:8px 12px;">Altitude (AGL)</th>
                            <th style="padding:8px 12px;">TLOD Moyen</th>
                            <th style="padding:8px 12px;">OLOD Moyen</th>
                            <th style="padding:8px 12px;">FPS Moyen</th>
                            <th style="padding:8px 12px;">MainThread CPU</th>
                            <th style="padding:8px 12px;">Comportement & Impact</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>
        """
    else:
        milestones_section = ""

    narrative_section = generate_automated_flight_narrative(samples, session_info)

    # Formatage des Cartes KPI (Moyenne en gros, Min/Pic en petit, Go pour mémoire)
    if is_fg_used and avg_base_fps != "N/A":
        card_fps_title = "FPS Moyens (Frame Gen)"
        card_fps_val = f'{avg_fps} <span style="font-size:16px;">FPS</span> <span style="font-size:15px; color:#38bdf8; font-weight:normal;">({avg_base_fps} base)</span>'
        card_fps_sub = f"Pic : {max_fps} FPS ({max_base_fps} base) • Min : {min_fps} FPS ({min_base_fps} base)"
    else:
        card_fps_title = "FPS Moyens (Natif)"
        card_fps_val = f'{avg_fps} <span style="font-size:16px;">FPS</span>'
        card_fps_sub = f"Pic : {max_fps} FPS • Min : {min_fps} FPS"

    card_mt_title = "MainThread CPU Moyen"
    card_mt_val = f'{avg_mt} <span style="font-size:16px;">ms</span>'
    card_mt_sub = f"Meilleur : {min_mt} ms • Pic : {max_mt} ms"

    card_vram_title = "VRAM GPU Moyenne"
    card_vram_val = f'{avg_vram_gb} <span style="font-size:16px;">Go</span>'
    card_vram_sub = f"Pic : {peak_vram_gb} Go ({peak_vram_pct}% de {total_vram_gb} Go) • Min : {min_vram_gb} Go"

    card_ram_title = "RAM MSFS Moyenne (Physique)"
    card_ram_val = f'{avg_ram_gb} <span style="font-size:16px;">Go</span>'
    card_ram_sub = f"Pic : {peak_ram_gb} Go • Min : {min_ram_gb} Go"

    card_commit_title = "RAM Allouée Moyenne (Commit)"
    card_commit_val = f'{avg_commit_gb} <span style="font-size:16px;">Go</span>'
    card_commit_sub = f"Pic : {peak_commit_gb} Go • Min : {min_commit_gb} Go"

    card_power_title = "Puissance GPU Moyenne"
    card_power_val = f'{avg_power} <span style="font-size:16px;">W</span>'
    card_power_sub = f"Pic : {peak_power} W • Min : {min_power} W"

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Rapport de Performance - {session_info['start_time']}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            background: #0b0f19;
            color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 24px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 1px;
            background: rgba(16, 185, 129, 0.15);
            color: {badge_color};
            border: 1px solid {badge_color};
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        .card-title {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #94a3b8;
            margin-bottom: 8px;
        }}
        .card-val {{
            font-size: 26px;
            font-weight: 900;
            font-family: monospace;
            color: #38bdf8;
        }}
        .card-sub {{
            font-size: 12px;
            color: #64748b;
            margin-top: 4px;
        }}
        .chart-box {{
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .chart-title {{
            font-size: 14px;
            font-weight: 800;
            margin-bottom: 16px;
            color: #f8fafc;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 style="margin:0 0 6px 0; font-size:24px;">Rapport de Télémétrie de Vol SceneryX Pro</h1>
                <div style="color:#94a3b8; font-size:13px;">Vol enregistré le {session_info['start_time']} • Durée : {session_info['duration']}</div>
            </div>
            <div>
                <span class="badge">{badge_text}</span>
            </div>
        </div>

        <!-- EN-TETE CONTEXTUELLE DE VOL (Appareil, Route, Mode, AutoFPS) -->
        <div style="background:#0f172a; border:1px solid #1e293b; border-radius:16px; padding:16px 20px; margin-bottom:20px; display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:16px; font-size:13px;">
            <div>
                <div style="color:#64748b; font-size:11px; font-weight:bold; text-transform:uppercase;">Appareil</div>
                <div style="color:#f8fafc; font-weight:bold; font-size:15px; margin-top:2px;">{aircraft_display}</div>
            </div>
            <div>
                <div style="color:#64748b; font-size:11px; font-weight:bold; text-transform:uppercase;">Route / Origine</div>
                <div style="color:#38bdf8; font-weight:bold; font-size:15px; margin-top:2px;">{route_display}</div>
            </div>
            <div>
                <div style="color:#64748b; font-size:11px; font-weight:bold; text-transform:uppercase;">Mode SceneryX</div>
                <div style="color:#10b981; font-weight:bold; font-size:14px; margin-top:2px;">{mode_display}</div>
            </div>
            <div>
                <div style="color:#64748b; font-size:11px; font-weight:bold; text-transform:uppercase;">AutoFPS</div>
                <div style="margin-top:2px;">{autofps_badge_html}</div>
            </div>
        </div>

        <!-- DIAGNOSTIC TEXTUEL EXPERT -->
        {narrative_section}

        <!-- PALIERS D'ALTITUDE & IMPACTS LOD -->
        {milestones_section}

        <div class="grid">
            <div class="card">
                <div class="card-title">{card_fps_title}</div>
                <div class="card-val" style="color: #10b981;">{card_fps_val}</div>
                <div class="card-sub">{card_fps_sub}</div>
            </div>

            <div class="card">
                <div class="card-title">{card_mt_title}</div>
                <div class="card-val" style="color: #f59e0b;">{card_mt_val}</div>
                <div class="card-sub">{card_mt_sub}</div>
            </div>

            <div class="card">
                <div class="card-title">{card_vram_title}</div>
                <div class="card-val" style="color: #38bdf8;">{card_vram_val}</div>
                <div class="card-sub">{card_vram_sub}</div>
            </div>

            <div class="card">
                <div class="card-title">{card_ram_title}</div>
                <div class="card-val">{card_ram_val}</div>
                <div class="card-sub">{card_ram_sub}</div>
            </div>

            <div class="card">
                <div class="card-title">{card_commit_title}</div>
                <div class="card-val">{card_commit_val}</div>
                <div class="card-sub">{card_commit_sub}</div>
            </div>

            <div class="card">
                <div class="card-title">{card_power_title}</div>
                <div class="card-val" style="color: #eab308;">{card_power_val}</div>
                <div class="card-sub">{card_power_sub}</div>
            </div>
        </div>

        <!-- GRAPH 1 : FPS & MainThread -->
        <div class="chart-box">
            <div class="chart-title">1. Fluidité & Latence : FPS Affichés vs MainThread (ms)</div>
            <div style="height: 320px;">
                <canvas id="fpsChart"></canvas>
            </div>
        </div>

        <!-- GRAPH 2 : VRAM & RAM MSFS -->
        <div class="chart-box">
            <div class="chart-title">2. Empreinte Mémoire : VRAM GPU & RAM MSFS au fil du vol (Mo)</div>
            <div style="height: 320px;">
                <canvas id="perfChart"></canvas>
            </div>
        </div>

        <!-- GRAPH 3 : Altitude & TLOD -->
        <div class="chart-box">
            <div class="chart-title">3. Profil de Vol & Dynamique : Altitude AGL (ft) et Terrain LOD (TLOD)</div>
            <div style="height: 300px;">
                <canvas id="lodChart"></canvas>
            </div>
        </div>

        <!-- GRAPH 4 : Rolling Cache & Débit Disque -->
        <div class="chart-box">
            <div class="chart-title">4. Streaming & Rolling Cache : Débit de Lecture Disque / Cache MSFS (Mbps)</div>
            <div style="height: 260px;">
                <canvas id="ioChart"></canvas>
            </div>
        </div>

        <div style="text-align:center; color:#64748b; font-size:12px; margin-top:24px;">
            Fichier source : {csv_path}
        </div>
    </div>

    <script>
        const times = {json.dumps(times)};

        // 1. FPS & MainThread Chart
        new Chart(document.getElementById('fpsChart').getContext('2d'), {{
            type: 'line',
            data: {{
                labels: times,
                datasets: [
                    {{
                        label: 'FPS Affichés (Frame Gen)',
                        data: {json.dumps([s.get('disp_fps') for s in samples])},
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 2,
                        tension: 0.2,
                        yAxisID: 'yFps',
                        pointRadius: 0
                    }},
                    {{
                        label: 'MainThread (ms)',
                        data: {json.dumps([s.get('main_thread_ms') for s in samples])},
                        borderColor: '#f59e0b',
                        borderWidth: 1.8,
                        tension: 0.2,
                        yAxisID: 'yMs',
                        pointRadius: 0
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ title: {{ display: true, text: 'Temps écoulé', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8', maxTicksLimit: 12 }} }},
                    yFps: {{ type: 'linear', position: 'left', title: {{ display: true, text: 'FPS', color: '#10b981' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#10b981' }} }},
                    yMs: {{ type: 'linear', position: 'right', title: {{ display: true, text: 'MainThread (ms)', color: '#f59e0b' }}, grid: {{ drawOnChartArea: false }}, ticks: {{ color: '#f59e0b' }} }}
                }},
                plugins: {{ legend: {{ labels: {{ color: '#f8fafc', font: {{ weight: 'bold' }} }} }} }}
            }}
        }});

        // 2. Memory Chart
        new Chart(document.getElementById('perfChart').getContext('2d'), {{
            type: 'line',
            data: {{
                labels: times,
                datasets: [
                    {{
                        label: 'VRAM GPU Occupée (Mo)',
                        data: {json.dumps(vram_vals)},
                        borderColor: '#38bdf8',
                        backgroundColor: 'rgba(56, 189, 248, 0.1)',
                        borderWidth: 2,
                        tension: 0.2,
                        fill: true,
                        pointRadius: 0
                    }},
                    {{
                        label: 'RAM MSFS Physique (Mo)',
                        data: {json.dumps(msfs_ram_vals)},
                        borderColor: '#a855f7',
                        borderWidth: 2,
                        tension: 0.2,
                        pointRadius: 0
                    }},
                    {{
                        label: 'RAM MSFS Allouée/Commit (Mo)',
                        data: {json.dumps(msfs_commit_vals)},
                        borderColor: '#f59e0b',
                        borderWidth: 1.5,
                        borderDash: [4, 4],
                        tension: 0.2,
                        pointRadius: 0
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ title: {{ display: true, text: 'Temps écoulé', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8', maxTicksLimit: 12 }} }},
                    y: {{ title: {{ display: true, text: 'Mémoire (Mo)', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8' }} }}
                }},
                plugins: {{ legend: {{ labels: {{ color: '#f8fafc', font: {{ weight: 'bold' }} }} }} }}
            }}
        }});

        // 3. Flight Profile & LOD Chart
        new Chart(document.getElementById('lodChart').getContext('2d'), {{
            type: 'line',
            data: {{
                labels: times,
                datasets: [
                    {{
                        label: 'Altitude AGL (ft)',
                        data: {json.dumps([s.get('agl_ft') for s in samples])},
                        borderColor: '#06b6d4',
                        backgroundColor: 'rgba(6, 182, 212, 0.08)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.2,
                        yAxisID: 'yAlt',
                        pointRadius: 0
                    }},
                    {{
                        label: 'Terrain LOD (TLOD)',
                        data: {json.dumps([s.get('tlod') for s in samples])},
                        borderColor: '#ec4899',
                        borderWidth: 2,
                        tension: 0.2,
                        yAxisID: 'yLod',
                        pointRadius: 0
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ title: {{ display: true, text: 'Temps écoulé', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8', maxTicksLimit: 12 }} }},
                    yAlt: {{ type: 'linear', position: 'left', title: {{ display: true, text: 'Altitude AGL (ft)', color: '#06b6d4' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#06b6d4' }} }},
                    yLod: {{ type: 'linear', position: 'right', title: {{ display: true, text: 'TLOD', color: '#ec4899' }}, grid: {{ drawOnChartArea: false }}, ticks: {{ color: '#ec4899' }} }}
                }},
                plugins: {{ legend: {{ labels: {{ color: '#f8fafc', font: {{ weight: 'bold' }} }} }} }}
            }}
        }});

        // 4. Rolling Cache & Disk Read
        new Chart(document.getElementById('ioChart').getContext('2d'), {{
            type: 'line',
            data: {{
                labels: times,
                datasets: [
                    {{
                        label: 'Débit Lecture Cache / Disque (Mbps)',
                        data: {json.dumps(io_reads_mbps)},
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 1.8,
                        fill: true,
                        tension: 0.1,
                        pointRadius: 0
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ title: {{ display: true, text: 'Temps écoulé', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8', maxTicksLimit: 12 }} }},
                    y: {{ title: {{ display: true, text: 'Mbps', color: '#3b82f6' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#3b82f6' }} }}
                }},
                plugins: {{ legend: {{ labels: {{ color: '#f8fafc', font: {{ weight: 'bold' }} }} }} }}
            }}
        }});
    </script>
</body>
</html>
"""
    try:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return html_path
    except Exception as e:
        print("Erreur génération HTML:", e)
        return None

def main():
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    os.system('cls' if os.name == 'nt' else 'clear')
    
    benchmarks_dir = get_benchmarks_directory()

    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    mode_str, is_corridor, dep, arr, dis_count, prof_slug = get_sceneryx_flight_mode()

    prefix = f"{prof_slug}_{dep}_{arr}" if is_corridor else "baseline_full"
    csv_filename = f"benchmark_{prefix}_{timestamp_str}.csv"
    csv_path = os.path.join(benchmarks_dir, csv_filename)

    # Initialize CSV File with expanded telemetry columns
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'timestamp', 'elapsed_sec', 'time_str', 'mode',
            'displayed_fps', 'base_fps', 'main_thread_ms',
            'tlod', 'olod', 'agl_ft', 'fpm', 'fg_mode',
            'cache_read_mbps', 'cache_read_mbs',
            'vram_used_mb', 'vram_total_mb', 'vram_pct',
            'gpu_util_pct', 'gpu_temp_c', 'gpu_power_w', 'gpu_clock_mhz', 'gpu_mem_bus_pct',
            'msfs_ram_mb', 'msfs_commit_mb', 'msfs_cpu_pct',
            'sys_ram_used_mb', 'sys_ram_total_mb'
        ])

    print("=" * 84)
    print("           SCENERYX - FLIGHT PERFORMANCE TRACKER (STANDALONE PRO)")
    print("=" * 84)
    print(f" Mode détecté   : {mode_str}")
    print(f" Journal CSV    : {csv_path}")
    print(f" Télémétrie     : FPS, MainThread, TLOD, Cache Read (Mbps), VRAM, RAM, GPU (W)")
    print("=" * 84)
    print(" En attente du simulateur de vol...")

    samples = []
    start_time = None
    sample_index = 0

    peak_vram = 0
    min_vram = 999999
    peak_msfs_ram = 0
    peak_msfs_commit = 0
    
    last_cpu_sec = None
    last_read_bytes = None
    last_tick_time = None
    cpu_cores = os.cpu_count() or 8

    try:
        while True:
            msfs = get_msfs_process()
            gpu = get_nvidia_gpu_telemetry()
            sys_ram_used, sys_ram_total = get_system_ram()
            autofps = get_latest_autofps_data()

            now_dt = datetime.now()
            now_iso = now_dt.strftime("%Y-%m-%d %H:%M:%S")

            if msfs:
                now_tick = time.time()
                if start_time is None:
                    start_time = now_tick
                    print("\n>> MSFS 2024 DÉTECTÉ ET ACTIF ! Démarrage du tracking en direct...\n")

                elapsed = round(now_tick - start_time, 1)
                time_formatted = format_time_delta(elapsed)
                sample_index += 1

                # Calculate MSFS CPU usage % & Rolling Cache / Disk Read speed
                msfs_cpu_pct = 0.0
                cache_read_mbps = 0.0
                cache_read_mbs = 0.0

                if last_tick_time is not None:
                    dt = now_tick - last_tick_time
                    if dt > 0:
                        if last_cpu_sec is not None:
                            dcpu = msfs['cpu_sec'] - last_cpu_sec
                            if dcpu >= 0:
                                msfs_cpu_pct = round(min(100.0, (dcpu / (dt * cpu_cores)) * 100.0), 1)

                        if last_read_bytes is not None and 'read_bytes' in msfs:
                            dread = msfs['read_bytes'] - last_read_bytes
                            if dread >= 0:
                                cache_read_mbs = round((dread / (1024 * 1024)) / dt, 2)
                                cache_read_mbps = round(cache_read_mbs * 8.0, 1)

                last_cpu_sec = msfs['cpu_sec']
                last_read_bytes = msfs.get('read_bytes', 0)
                last_tick_time = now_tick

                # Update Stats
                vram_used = gpu['vram_used_mb']
                if vram_used > peak_vram: peak_vram = vram_used
                if vram_used < min_vram and vram_used > 0: min_vram = vram_used

                msfs_ram = msfs['ram_mb']
                if msfs_ram > peak_msfs_ram: peak_msfs_ram = msfs_ram

                msfs_commit = msfs['commit_mb']
                if msfs_commit > peak_msfs_commit: peak_msfs_commit = msfs_commit

                sc_data = SIMCONNECT_CLIENT.get_data() if SIMCONNECT_CLIENT else {}
                sc_connected = sc_data.get("connected", False)

                if sc_connected and sc_data.get("base_fps") is not None:
                    disp_fps = sc_data.get('displayed_fps')
                    base_fps = sc_data.get('base_fps')
                    main_thread_ms = sc_data.get('frame_time_ms')
                    agl_ft = sc_data.get('agl_ft')
                    fpm = sc_data.get('fpm')
                    tlod = autofps.get('tlod') if autofps else None
                    olod = autofps.get('olod') if autofps else None
                    fg_mode = 'DLSSG (2X)' if (disp_fps and base_fps and disp_fps > base_fps) else 'NATIVE'
                else:
                    disp_fps = autofps.get('displayed_fps') if autofps else None
                    base_fps = autofps.get('base_fps') if autofps else None
                    main_thread_ms = autofps.get('main_thread_ms') if autofps else None
                    tlod = autofps.get('tlod') if autofps else None
                    olod = autofps.get('olod') if autofps else None
                    agl_ft = autofps.get('agl_ft') if autofps else None
                    fpm = autofps.get('fpm') if autofps else None
                    fg_mode = autofps.get('fg_mode', '') if autofps else ''


                # Append to sample list
                samples.append({
                    'elapsed': time_formatted,
                    'disp_fps': disp_fps,
                    'base_fps': base_fps,
                    'main_thread_ms': main_thread_ms,
                    'tlod': tlod,
                    'olod': olod,
                    'agl_ft': agl_ft,
                    'fpm': fpm,
                    'fg_mode': fg_mode,
                    'cache_read_mbps': cache_read_mbps,
                    'cache_read_mbs': cache_read_mbs,
                    'vram_used': vram_used,
                    'vram_total': gpu['vram_total_mb'],
                    'vram_pct': gpu['vram_pct'],
                    'gpu_util': gpu['gpu_util_pct'],
                    'gpu_temp': gpu['gpu_temp_c'],
                    'gpu_power_w': gpu['gpu_power_w'],
                    'gpu_clock_mhz': gpu['gpu_clock_mhz'],
                    'gpu_mem_bus_pct': gpu['gpu_mem_bus_pct'],
                    'msfs_ram': msfs_ram,
                    'msfs_commit': msfs_commit,
                    'msfs_cpu_pct': msfs_cpu_pct
                })

                # Write to CSV
                with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        now_iso, elapsed, time_formatted, mode_str,
                        disp_fps, base_fps, main_thread_ms,
                        tlod, olod, agl_ft, fpm, fg_mode,
                        cache_read_mbps, cache_read_mbs,
                        vram_used, gpu['vram_total_mb'], gpu['vram_pct'],
                        gpu['gpu_util_pct'], gpu['gpu_temp_c'], gpu['gpu_power_w'], gpu['gpu_clock_mhz'], gpu['gpu_mem_bus_pct'],
                        msfs_ram, msfs_commit, msfs_cpu_pct,
                        sys_ram_used, sys_ram_total
                    ])

                # Live Console Display (ANSI in-place rewrite)
                fps_disp = f"FPS: {disp_fps} ({main_thread_ms}ms)" if disp_fps else "FPS: --"
                lod_disp = f"TLOD: {tlod}" if tlod is not None else ""
                alt_disp = f"Alt: {agl_ft:,}ft" if agl_ft is not None else ""
                power_disp = f"{gpu['gpu_power_w']}W"
                io_disp = f"Disk: {cache_read_mbps} Mbps" if cache_read_mbps > 0 else ""

                sys.stdout.write(
                    f"\r[{time_formatted}] "
                    f"{fps_disp} | "
                    f"VRAM: {vram_used:,.0f} Mo ({gpu['vram_pct']}%) | "
                    f"GPU: {gpu['gpu_util_pct']}% ({power_disp}, {gpu['gpu_temp_c']}°C) | "
                    f"RAM: {round(msfs_ram/1024, 1)} Go | "
                    f"{lod_disp} {alt_disp} {io_disp} | #{sample_index}"
                )
                sys.stdout.flush()

            else:
                if start_time is not None:
                    print("\n\n>> MSFS s'est arrêté. Finalisation de la session de benchmark...")
                    break
                else:
                    sys.stdout.write(f"\r[{now_dt.strftime('%H:%M:%S')}] En attente du processus FlightSimulator2024.exe...")
                    sys.stdout.flush()

            time.sleep(2.0)

    except KeyboardInterrupt:
        print("\n\nArrêt manuel demandé par l'utilisateur (Ctrl+C).")

    # Generate Summary & HTML Report
    if samples:
        total_duration = format_time_delta(time.time() - start_time) if start_time else "00:00"
        avg_vram = round(sum(s['vram_used'] for s in samples) / len(samples), 1)
        avg_ram = round(sum(s['msfs_ram'] for s in samples) / len(samples), 1)

        valid_fps = [s['disp_fps'] for s in samples if s.get('disp_fps') is not None]
        avg_fps_str = f"{round(sum(valid_fps)/len(valid_fps), 1)} FPS" if valid_fps else "N/A"

        valid_mt = [s['main_thread_ms'] for s in samples if s.get('main_thread_ms') is not None]
        avg_mt_str = f"{round(sum(valid_mt)/len(valid_mt), 1)} ms" if valid_mt else "N/A"

        print("\n" + "=" * 80)
        print("               RÉSUMÉ DU VOL & BENCHMARK DE PERFORMANCE PRO")
        print("=" * 80)
        print(f" Mode Testé       : {mode_str}")
        print(f" Durée Enregistrée: {total_duration} ({len(samples)} échantillons)")
        print("-" * 80)
        print(f" FPS Moyen        : {avg_fps_str}  (MainThread moyen : {avg_mt_str})")
        print(f" VRAM GPU Crête   : {peak_vram:,.0f} Mo  (Moyenne : {avg_vram:,.0f} Mo)")
        print(f" RAM MSFS Crête   : {peak_msfs_ram:,.0f} Mo  (Moyenne : {avg_ram:,.0f} Mo)")
        print(f" RAM Allouée Max  : {peak_msfs_commit:,.0f} Mo")
        print("=" * 80)

        last_sc = SIMCONNECT_CLIENT.get_data() if SIMCONNECT_CLIENT else {}
        final_lat = last_sc.get('lat')
        final_lon = last_sc.get('lon')
        final_ground = last_sc.get('on_ground', False)
        ctx = resolve_flight_context(final_lat, final_lon, final_ground)
        final_aircraft = last_sc.get('aircraft') or "Avion générique"
        cloud_status = check_autofps_cloud_events()
        autofps_cfg = get_autofps_config()
        autofps_active = is_autofps_active()

        session_info = {
            'mode_str': mode_str,
            'is_corridor': is_corridor,
            'start_time': timestamp_str,
            'duration': total_duration,
            'aircraft': final_aircraft,
            'route_display': ctx['route_display'],
            'mode_display': ctx['mode_display'],
            'autofps_config': autofps_cfg,
            'autofps_active': autofps_active,
            'cloud_events': cloud_status
        }
        html_file = generate_html_report(csv_path, session_info, samples)
        if html_file and os.path.exists(html_file):
            print(f"\n📊 Rapport graphique complet généré : {html_file}")
            print("Ouverture du rapport dans votre navigateur...")
            webbrowser.open(f"file:///{os.path.abspath(html_file)}")
        print(f"📄 Journal CSV complet : {csv_path}\n")
    else:
        print("\nAucune donnée n'a été enregistrée (MSFS n'était pas actif).")


class BlackboxSession:
    def __init__(self):
        self.is_running = False
        self.thread = None
        self._stop_event = threading.Event()
        self.current_flight_name = ""
        self.current_csv_path = None
        self.last_report_path = None
        self.latest_telemetry = {
            "is_tracking": False,
            "flight_name": "",
            "displayed_fps": None,
            "base_fps": None,
            "main_thread_ms": None,
            "tlod": None,
            "olod": None,
            "vram_used_mb": 0,
            "vram_total_mb": 16376,
            "vram_pct": 0,
            "cache_read_mbps": 0.0,
            "msfs_ram_mb": 0,
            "msfs_vram_mb": 0.0,
            "gpu_power_w": 0,
            "elapsed_sec": 0,
            "elapsed_str": "00:00",
            "msfs_active": False,
            "aircraft": "--",
            "route_display": "--",
            "mode_display": "BASELINE STANDARD",
            "autofps_active": False
        }

    def start(self, flight_name="flight", dep="LFPO", arr="EGKK", aircraft="Airliner"):
        if self.is_running:
            return {"status": "already_running", "flight_name": self.current_flight_name}
        self._stop_event.clear()
        self.is_running = True
        self.current_flight_name = flight_name or f"{dep}_{arr}_{aircraft}"
        self.thread = threading.Thread(target=self._worker, args=(flight_name, dep, arr, aircraft), daemon=True)
        self.thread.start()
        return {"status": "started", "flight_name": self.current_flight_name}

    def stop(self):
        if not self.is_running:
            return {"status": "not_running", "report_path": self.last_report_path}
        self._stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3.0)
        self.is_running = False
        self.latest_telemetry["is_tracking"] = False
        return {
            "status": "stopped",
            "report_path": self.last_report_path,
            "csv_path": self.current_csv_path
        }

    def get_telemetry(self):
        msfs = get_msfs_process()
        gpu = get_nvidia_gpu_telemetry()
        sys_ram_used, sys_ram_total = get_system_ram()
        autofps = get_latest_autofps_data()
        sc_data = SIMCONNECT_CLIENT.get_data() if SIMCONNECT_CLIENT else {}
        sc_connected = sc_data.get("connected", False)
        
        telemetry = dict(self.latest_telemetry)
        telemetry["is_tracking"] = self.is_running
        telemetry["msfs_active"] = msfs is not None
        telemetry["simconnect_connected"] = sc_connected
        telemetry["autofps_active"] = is_autofps_active()

        # Context (Appareil, Route, Mode)
        lat = sc_data.get("lat")
        lon = sc_data.get("lon")
        on_ground = sc_data.get("on_ground", False)
        ctx = resolve_flight_context(lat, lon, on_ground)
        telemetry["aircraft"] = sc_data.get("aircraft") or "Non détecté"
        telemetry["route_display"] = ctx["route_display"]
        telemetry["mode_display"] = ctx["mode_display"]

        if gpu:
            telemetry["vram_used_mb"] = gpu.get("vram_used_mb", 0)
            telemetry["vram_total_mb"] = gpu.get("vram_total_mb", 16376)
            telemetry["vram_pct"] = gpu.get("vram_pct", 0)
            telemetry["gpu_power_w"] = gpu.get("gpu_power_w", 0)

        if sc_connected and sc_data.get("base_fps") is not None:
            telemetry["displayed_fps"] = sc_data.get("displayed_fps")
            telemetry["base_fps"] = sc_data.get("base_fps")
            telemetry["main_thread_ms"] = sc_data.get("frame_time_ms")
            if autofps:
                telemetry["tlod"] = autofps.get("tlod")
                telemetry["olod"] = autofps.get("olod")
        elif autofps:
            telemetry["displayed_fps"] = autofps.get("displayed_fps") or autofps.get("disp_fps")
            telemetry["base_fps"] = autofps.get("base_fps")
            telemetry["main_thread_ms"] = autofps.get("main_thread_ms")
            telemetry["tlod"] = autofps.get("tlod")
            telemetry["olod"] = autofps.get("olod")
        if msfs:
            telemetry["msfs_ram_mb"] = msfs.get("ram_mb", 0)
            telemetry["msfs_vram_mb"] = msfs.get("vram_mb", 0.0)
        return telemetry


    def _worker(self, flight_name, dep, arr, aircraft):
        benchmarks_dir = get_benchmarks_directory()
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        mode_str, is_corridor, cur_dep, cur_arr, dis_count, prof_slug = get_sceneryx_flight_mode()

        autofps_cfg = get_autofps_config()
        autofps_is_active = is_autofps_active()

        prefix = f"{dep or cur_dep}_{arr or cur_arr}_{aircraft or 'Flight'}"
        csv_filename = f"benchmark_{prefix}_{timestamp_str}.csv"
        csv_path = os.path.join(benchmarks_dir, csv_filename)
        self.current_csv_path = csv_path

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'elapsed_sec', 'time_str', 'mode',
                'displayed_fps', 'base_fps', 'main_thread_ms',
                'tlod', 'olod', 'agl_ft', 'fpm', 'fg_mode',
                'cache_read_mbps', 'cache_read_mbs',
                'vram_used_mb', 'vram_total_mb', 'vram_pct',
                'gpu_util_pct', 'gpu_temp_c', 'gpu_power_w', 'gpu_clock_mhz', 'gpu_mem_bus_pct',
                'msfs_ram_mb', 'msfs_commit_mb', 'msfs_cpu_pct',
                'sys_ram_used_mb', 'sys_ram_total_mb'
            ])

        samples = []
        start_time = time.time()
        last_read_bytes = None
        last_tick_time = None

        while not self._stop_event.is_set():
            msfs = get_msfs_process()
            gpu = get_nvidia_gpu_telemetry()
            sys_ram_used, sys_ram_total = get_system_ram()
            autofps = get_latest_autofps_data()

            now_tick = time.time()
            elapsed = round(now_tick - start_time, 1)
            time_formatted = format_time_delta(elapsed)

            sc_data = SIMCONNECT_CLIENT.get_data() if SIMCONNECT_CLIENT else {}
            sc_connected = sc_data.get("connected", False)

            if sc_connected and sc_data.get("base_fps") is not None:
                disp_fps = sc_data.get('displayed_fps')
                base_fps = sc_data.get('base_fps')
                mt_ms = sc_data.get('frame_time_ms')
                agl = sc_data.get('agl_ft')
                fpm = sc_data.get('fpm')
                tlod = autofps.get('tlod') if autofps else None
                olod = autofps.get('olod') if autofps else None
                fg_mode = 'DLSSG (2X)' if (disp_fps and base_fps and disp_fps > base_fps) else 'NATIVE'
            else:
                disp_fps = (autofps.get('displayed_fps') or autofps.get('disp_fps')) if autofps else None
                base_fps = autofps.get('base_fps') if autofps else None
                mt_ms = autofps.get('main_thread_ms') if autofps else None
                tlod = autofps.get('tlod') if autofps else None
                olod = autofps.get('olod') if autofps else None
                agl = autofps.get('agl_ft') if autofps else None
                fpm = autofps.get('fpm') if autofps else None
                fg_mode = autofps.get('fg_mode') if autofps else None

            # Rolling Cache I/O
            cur_read_bytes = msfs.get('read_bytes', 0) if msfs else 0
            cache_read_mbps = 0.0
            cache_read_mbs = 0.0
            if last_read_bytes is not None and last_tick_time is not None:
                delta_t = now_tick - last_tick_time
                if delta_t > 0.05 and cur_read_bytes >= last_read_bytes:
                    delta_bytes = cur_read_bytes - last_read_bytes
                    cache_read_mbps = round((delta_bytes * 8.0) / (delta_t * 1_000_000.0), 2)
                    cache_read_mbs = round(delta_bytes / (delta_t * 1024.0 * 1024.0), 2)
            last_read_bytes = cur_read_bytes
            last_tick_time = now_tick

            v_used = gpu.get('vram_used_mb', 0)
            v_total = gpu.get('vram_total_mb', 16376)
            v_pct = gpu.get('vram_pct', 0)

            msfs_vram = msfs.get('vram_mb', 0.0) if msfs else 0.0

            # Realtime Context
            lat = sc_data.get("lat")
            lon = sc_data.get("lon")
            on_ground = sc_data.get("on_ground", False)
            ctx = resolve_flight_context(lat, lon, on_ground)
            detected_aircraft = sc_data.get("aircraft") or aircraft or "Non détecté"

            self.latest_telemetry = {
                "is_tracking": True,
                "flight_name": self.current_flight_name,
                "displayed_fps": disp_fps,
                "base_fps": base_fps,
                "main_thread_ms": mt_ms,
                "tlod": tlod,
                "olod": olod,
                "vram_used_mb": v_used,
                "vram_total_mb": v_total,
                "vram_pct": v_pct,
                "msfs_vram_mb": msfs_vram,
                "cache_read_mbps": cache_read_mbps,
                "msfs_ram_mb": msfs.get('ram_mb', 0) if msfs else 0,
                "gpu_power_w": gpu.get('gpu_power_w', 0),
                "elapsed_sec": elapsed,
                "elapsed_str": time_formatted,
                "msfs_active": msfs is not None,
                "simconnect_connected": sc_connected,
                "aircraft": detected_aircraft,
                "route_display": ctx["route_display"],
                "mode_display": ctx["mode_display"],
                "autofps_active": is_autofps_active()
            }

            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), elapsed, time_formatted, mode_str,
                disp_fps if disp_fps is not None else '',
                base_fps if base_fps is not None else '',
                mt_ms if mt_ms is not None else '',
                tlod if tlod is not None else '',
                olod if olod is not None else '',
                agl if agl is not None else '',
                fpm if fpm is not None else '',
                fg_mode or '',
                cache_read_mbps, cache_read_mbs,
                v_used, v_total, v_pct,
                gpu.get('gpu_util_pct', 0), gpu.get('gpu_temp_c', 0), gpu.get('gpu_power_w', 0), gpu.get('gpu_clock_mhz', 0), gpu.get('gpu_mem_bus_pct', 0),
                msfs.get('ram_mb', 0) if msfs else 0, msfs.get('commit_mb', 0) if msfs else 0, 0,
                sys_ram_used, sys_ram_total
            ]
            try:
                with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerow(row)
            except Exception:
                pass

            samples.append({
                'elapsed': elapsed,
                'time_str': time_formatted,
                'disp_fps': disp_fps,
                'base_fps': base_fps,
                'main_thread_ms': mt_ms,
                'tlod': tlod,
                'olod': olod,
                'agl': agl,
                'agl_ft': agl,
                'fpm': fpm,
                'on_ground': sc_data.get('on_ground', False if (agl is not None and agl > 80) else True),
                'ground_speed_kts': sc_data.get('ground_speed_kts') or sc_data.get('airspeed_kts') or 0,
                'cache_read_mbps': cache_read_mbps,
                'vram_used': v_used,
                'vram_total': v_total,
                'vram_pct': v_pct,
                'msfs_vram': msfs_vram,
                'gpu_util': gpu.get('gpu_util_pct', 0),
                'gpu_temp': gpu.get('gpu_temp_c', 0),
                'gpu_power': gpu.get('gpu_power_w', 0),
                'gpu_clock': gpu.get('gpu_clock_mhz', 0),
                'gpu_bus': gpu.get('gpu_mem_bus_pct', 0),
                'msfs_ram': msfs.get('ram_mb', 0) if msfs else 0,
                'msfs_commit': msfs.get('commit_mb', 0) if msfs else 0,
                'sys_ram_used': sys_ram_used,
                'sys_ram_total': sys_ram_total
            })

            self._stop_event.wait(0.5)

        if samples:
            last_sc = SIMCONNECT_CLIENT.get_data() if SIMCONNECT_CLIENT else {}
            final_lat = last_sc.get('lat')
            final_lon = last_sc.get('lon')
            final_ground = last_sc.get('on_ground', False)
            ctx = resolve_flight_context(final_lat, final_lon, final_ground)
            final_aircraft = last_sc.get('aircraft') or aircraft or "Avion non détecté"
            cloud_status = check_autofps_cloud_events()

            session_info = {
                'mode_str': mode_str,
                'is_corridor': is_corridor,
                'start_time': timestamp_str,
                'duration': format_time_delta(round(time.time() - start_time, 1)),
                'aircraft': final_aircraft,
                'route_display': ctx['route_display'],
                'mode_display': ctx['mode_display'],
                'dep': dep or cur_dep or ctx.get('dep'),
                'arr': arr or cur_arr or ctx.get('arr'),
                'autofps_config': autofps_cfg,
                'autofps_active': autofps_is_active or is_autofps_active(),
                'cloud_events': cloud_status
            }
            html_file = generate_html_report(csv_path, session_info, samples)
            self.last_report_path = html_file


BLACKBOX = BlackboxSession()

if __name__ == '__main__':
    main()
