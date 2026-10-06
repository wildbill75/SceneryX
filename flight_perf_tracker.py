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
            return f"Automatic reductions triggered during flight (Initial: {initial_q})"
        return f"Nominal quality maintained ({initial_q}) - No cloud drops"
    except Exception:
        return "Nominal quality maintained"

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

def sanitize_aircraft_slug(aircraft_title):
    if not aircraft_title or str(aircraft_title).lower() in ('not detected', 'aircraft not detected', 'aircraft', 'flight', 'none'):
        return 'Aircraft'
    s = re.sub(r'\(.*?\)|\[.*?\]', '', str(aircraft_title)).strip()
    patterns = [
        (r'\b(A318|A319|A320neo|A320|A321neo|A321|A330|A340|A350|A380)\b', r'\1'),
        (r'\b(B737|B747|B777|B787|737[-\s]?\d+|747[-\s]?\d+|777[-\s]?\d+|787[-\s]?\d+)\b', r'\1'),
        (r'\b(CRJ[-\s]?\d+|ATR[-\s]?\d+|Dash[-\s]?8|Q400|ERJ[-\s]?\d+|E\d{3})\b', r'\1'),
        (r'\b(C172|C152|C208|DA40|DA62|SR22|KingAir|Baron|Bonanza)\b', r'\1'),
    ]
    for pat, rep in patterns:
        m = re.search(pat, s, re.IGNORECASE)
        if m:
            return re.sub(r'[\s\-]+', '', m.group(1).upper())
    words = [w for w in re.split(r'[^a-zA-Z0-9]', s) if w]
    if words:
        slug = '_'.join(words[:2])
        return slug[:16]
    return 'Aircraft'

def get_simbrief_flight_plan():
    """
    Tente de récupérer le plan de vol SimBrief actif :
    1. Depuis settings.json (flight_mode.simbrief_flight ou latest_simbrief_flight).
    2. En interrogeant l'API SimBrief si un username ou pilot_id est configuré.
    """
    appdata = os.getenv('APPDATA', '')
    settings_path = os.path.join(appdata, 'SceneryX', 'settings.json')
    if not os.path.exists(settings_path):
        return None

    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            st = json.load(f)
    except Exception:
        return None

    # Source 1 : flight_mode.simbrief_flight
    fm = st.get('flight_mode', {})
    if isinstance(fm, dict):
        sb_fm = fm.get('simbrief_flight')
        if isinstance(sb_fm, dict) and sb_fm.get('origin', {}).get('icao') and sb_fm.get('destination', {}).get('icao'):
            return sb_fm

    # Source 2 : latest_simbrief_flight
    latest_sb = st.get('latest_simbrief_flight')
    if isinstance(latest_sb, dict) and latest_sb.get('origin', {}).get('icao') and latest_sb.get('destination', {}).get('icao'):
        return latest_sb

    # Source 3 : interrogation directe SimBrief API si un identifiant est configuré
    uid = str(st.get('simbrief_userid') or '').strip()
    uname = str(st.get('simbrief_username') or '').strip()
    ident = uid or uname
    if ident:
        try:
            import urllib.request
            param = f"userid={ident}" if ident.isdigit() else f"username={ident}"
            url = f"https://www.simbrief.com/api/xml.fetcher.php?{param}&json=1"
            req = urllib.request.Request(url, headers={'User-Agent': 'SceneryX/1.0'})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if isinstance(data, dict) and 'origin' in data and 'destination' in data:
                    orig_icao = data.get('origin', {}).get('icao_code', '').upper()
                    dest_icao = data.get('destination', {}).get('icao_code', '').upper()
                    if orig_icao and dest_icao:
                        sb_obj = {
                            "origin": {
                                "icao": orig_icao,
                                "name": data.get('origin', {}).get('name', orig_icao),
                                "lat": float(data.get('origin', {}).get('pos_lat', 0)) if data.get('origin', {}).get('pos_lat') else None,
                                "lon": float(data.get('origin', {}).get('pos_long', 0)) if data.get('origin', {}).get('pos_long') else None
                            },
                            "destination": {
                                "icao": dest_icao,
                                "name": data.get('destination', {}).get('name', dest_icao),
                                "lat": float(data.get('destination', {}).get('pos_lat', 0)) if data.get('destination', {}).get('pos_lat') else None,
                                "lon": float(data.get('destination', {}).get('pos_long', 0)) if data.get('destination', {}).get('pos_long') else None
                            },
                            "aircraft": data.get('aircraft', {}).get('name', ''),
                            "route": data.get('general', {}).get('route', ''),
                            "fetched_at": time.time()
                        }
                        try:
                            st['latest_simbrief_flight'] = sb_obj
                            with open(settings_path, 'w', encoding='utf-8') as out_f:
                                json.dump(st, out_f, indent=2, ensure_ascii=False)
                        except Exception:
                            pass
                        return sb_obj
        except Exception:
            pass

    return None

def match_simbrief_plan(sb_flight, ref_lat=None, ref_lon=None, arr_lat=None, arr_lon=None):
    if not sb_flight or not isinstance(sb_flight, dict):
        return None, None, None, None
    orig = sb_flight.get('origin', {})
    dest = sb_flight.get('destination', {})
    orig_icao = orig.get('icao', '').upper().strip()
    dest_icao = dest.get('icao', '').upper().strip()
    if not orig_icao or not dest_icao or len(orig_icao) != 4 or len(dest_icao) != 4:
        return None, None, None, None

    orig_name = orig.get('name') or orig_icao
    dest_name = dest.get('name') or dest_icao

    # Vérification géographique départ si ref_lat/lon sont disponibles
    if ref_lat is not None and ref_lon is not None and (abs(ref_lat) > 0.01 or abs(ref_lon) > 0.01):
        orig_lat = orig.get('lat')
        orig_lon = orig.get('lon')
        if orig_lat is None or orig_lon is None:
            cache = get_airport_geo_cache()
            for icao, name, alat, alon in cache:
                if icao == orig_icao:
                    orig_lat, orig_lon = alat, alon
                    break
        if orig_lat is not None and orig_lon is not None:
            dist_nm = (((ref_lat - float(orig_lat))**2 + (ref_lon - float(orig_lon))**2)**0.5) * 60.0
            if dist_nm > 120.0:
                return None, None, None, None

    # Vérification géographique arrivée : si l'avion a atterri ailleurs que la destination SimBrief (ex: vol libre ou nouveau vol non re-généré sur SimBrief)
    if arr_lat is not None and arr_lon is not None and (abs(arr_lat) > 0.01 or abs(arr_lon) > 0.01):
        dest_lat = dest.get('lat')
        dest_lon = dest.get('lon')
        if dest_lat is None or dest_lon is None:
            cache = get_airport_geo_cache()
            for icao, name, alat, alon in cache:
                if icao == dest_icao:
                    dest_lat, dest_lon = alat, alon
                    break
        if dest_lat is not None and dest_lon is not None:
            dest_dist_nm = (((arr_lat - float(dest_lat))**2 + (arr_lon - float(dest_lon))**2)**0.5) * 60.0
            if dest_dist_nm > 80.0:
                # L'arrivée réelle ne correspond pas à la destination SimBrief : conserver le départ SimBrief mais laisser le GPS déterminer l'arrivée réelle
                return orig_icao, None, orig_name, None

    return orig_icao, dest_icao, orig_name, dest_name

def detect_flight_airports(samples=None, first_valid_gps=None, last_valid_gps=None,
                           first_ground_gps=None, last_ground_gps=None,
                           initial_dep=None, initial_arr=None):
    """
    Résout les aéroports de départ et d'arrivée selon la règle métier :
    1. Si un plan SimBrief est disponible et correspond au vol (départ ET arrivée), on le récupère.
    2. Si le départ correspond à SimBrief mais que l'arrivée est différente, départ = SimBrief et arrivée = GPS réel.
    3. Sinon (pas de SimBrief ou vol libre ailleurs), détection automatique par GPS sol/arrêt.
    """
    samples = samples or []
    
    # 1. Priorité SimBrief avec validation de l'arrivée réelle
    sb = get_simbrief_flight_plan()
    ref_start = first_ground_gps or first_valid_gps
    ref_end = last_ground_gps or last_valid_gps
    dep_icao, dep_name = None, ""
    arr_icao, arr_name = None, ""
    det_source = "Auto-GPS"

    if sb:
        s_dep, s_arr, s_dep_name, s_arr_name = match_simbrief_plan(
            sb,
            ref_start[0] if ref_start else None,
            ref_start[1] if ref_start else None,
            ref_end[0] if ref_end else None,
            ref_end[1] if ref_end else None
        )
        if s_dep and s_arr:
            return s_dep, s_arr, s_dep_name, s_arr_name, "SimBrief OFP"
        elif s_dep:
            dep_icao, dep_name = s_dep, s_dep_name
            det_source = "SimBrief + GPS Arr"

    # 2. Détection par GPS (si pas de SimBrief pour le départ)
    if not dep_icao:
        dep_pt = first_ground_gps or first_valid_gps
        if not dep_pt and samples:
            for s in samples:
                if s.get('lat') is not None and s.get('lon') is not None and (abs(s['lat']) > 0.01 or abs(s['lon']) > 0.01):
                    dep_pt = (s['lat'], s['lon'])
                    break

        if dep_pt:
            icao, name, dist = find_nearest_airport(dep_pt[0], dep_pt[1])
            if icao:
                dep_icao, dep_name = icao, name

        if not dep_icao:
            if initial_dep and len(initial_dep) == 4 and initial_dep != 'DEP':
                dep_icao = initial_dep
                dep_name = initial_dep
            else:
                dep_icao = "DEP"

    # Arrivée au moment précis de l'arrêt de la télémétrie
    arr_icao, arr_name = None, ""
    arr_pt = last_valid_gps or last_ground_gps
    if not arr_pt and samples:
        for s in reversed(samples):
            if s.get('lat') is not None and s.get('lon') is not None and (abs(s['lat']) > 0.01 or abs(s['lon']) > 0.01):
                arr_pt = (s['lat'], s['lon'])
                break

    if arr_pt:
        icao, name, dist = find_nearest_airport(arr_pt[0], arr_pt[1])
        if icao:
            arr_icao, arr_name = icao, name

    if not arr_icao:
        if initial_arr and len(initial_arr) == 4 and initial_arr != 'ARR':
            arr_icao = initial_arr
            arr_name = initial_arr
        else:
            arr_icao = "ARR"

    return dep_icao, arr_icao, dep_name, arr_name, det_source

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
            mode_display = f"A ➔ B DIRECT ({dis_count} isolated sceneries)"
            route_display = f"{dep} ➔ {arr}"
        elif prof_slug == 'simbrief':
            mode_display = f"SIMBRIEF ({dis_count} isolated sceneries)"
            route_display = f"{dep} ➔ {arr}"
        else:
            mode_display = f"CORRIDOR ({dis_count} isolated sceneries)"
            route_display = f"{dep} ➔ {arr}"
    else:
        # Vérification si un plan SimBrief est actif même sans mode corridor
        sb = get_simbrief_flight_plan()
        if sb:
            sb_dep, sb_arr, sb_dname, sb_aname = match_simbrief_plan(sb, lat, lon)
            if sb_dep and sb_arr:
                dep = sb_dep
                arr = sb_arr
                mode_display = "BASELINE (SimBrief OFP • No Scenery Isolation)"
                route_display = f"{sb_dep} ➔ {sb_arr}"

        if not route_display:
            if lat is not None and lon is not None:
                near_icao, near_name, dist_nm = find_nearest_airport(lat, lon)
                if near_icao:
                    if on_ground or dist_nm <= 4.0:
                        route_display = f"Departure: {near_icao} ({near_name})"
                        dep = near_icao
                    else:
                        route_display = f"In flight ~{int(round(dist_nm))} NM from {near_icao}"
                else:
                    route_display = "Free flight"
            else:
                route_display = "Waiting for flight"

    return {
        "route_display": route_display,
        "mode_display": mode_display,
        "is_corridor": is_corridor,
        "dep": dep,
        "arr": arr,
        "disabled_count": dis_count,
        "prof_slug": prof_slug
    }

def get_current_lod_data(autofps_data=None):
    """
    Retrieves current TLOD and OLOD directly from MSFS memory or active controllers.
    Priority:
    1. Direct MSFS RAM via FlightMemoryEngine (exact ground truth in memory).
    2. SceneryX Smart LOD setpoints if active.
    3. External AutoFPS if present.
    """
    try:
        import flight_memory_engine
        mem = flight_memory_engine.get_memory_engine()
        if not mem.is_attached:
            mem.attach()
        if mem.is_attached:
            t = mem.read_tlod()
            o = mem.read_olod()
            if t is not None and t > 0:
                return round(t), round(o) if o is not None else None, True
    except Exception:
        pass

    try:
        from flight_lod_controller import get_smart_lod_controller
        s_ctrl = get_smart_lod_controller()
        if s_ctrl and s_ctrl.config.get("enabled"):
            st = s_ctrl.get_status()
            tlod_val = st.get("current_tlod_setpoint")
            olod_val = st.get("current_olod_setpoint")
            if tlod_val is not None and tlod_val > 0:
                return round(tlod_val), round(olod_val) if olod_val is not None else None, True
    except Exception:
        pass

    if autofps_data:
        return autofps_data.get('tlod'), autofps_data.get('olod'), False
    return None, None, False


def analyze_smart_lod_performance(samples, session_info=None):
    """
    Analyse détaillée de l'efficacité de Smart LOD :
    - Évalue les performances (FPS, MainThread ms) selon les paliers d'altitude
      (Sol < 500ft, Montée/Descente 500-5000ft, Croisière > 5000ft).
    - Calcule les gains ou pertes de FPS et de MainThread avant/après chaque seuil.
    - Liste les déclenchements précis enregistrés pendant la session.
    """
    if not samples:
        return None

    def avg_val(lst, key):
        vals = [s[key] for s in lst if s.get(key) is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    # Tiers d'altitude
    ground_samples = [s for s in samples if (s.get('agl_ft') is not None and s.get('agl_ft') < 500) or s.get('on_ground')]
    trans_samples = [s for s in samples if s.get('agl_ft') is not None and 500 <= s.get('agl_ft') < 5000]
    cruise_samples = [s for s in samples if s.get('agl_ft') is not None and s.get('agl_ft') >= 5000]

    tier_ground = {
        'name': 'Sol & Décollage (< 500 ft)',
        'tlod': avg_val(ground_samples, 'tlod') or 100,
        'fps': avg_val(ground_samples, 'disp_fps'),
        'mt': avg_val(ground_samples, 'main_thread_ms'),
        'count': len(ground_samples)
    }

    tier_trans = {
        'name': 'Montée / Transition (500 - 5000 ft)',
        'tlod': avg_val(trans_samples, 'tlod') or 175,
        'fps': avg_val(trans_samples, 'disp_fps'),
        'mt': avg_val(trans_samples, 'main_thread_ms'),
        'count': len(trans_samples)
    }

    tier_cruise = {
        'name': 'Croisière & Haute Altitude (> 5000 ft)',
        'tlod': avg_val(cruise_samples, 'tlod') or 250,
        'fps': avg_val(cruise_samples, 'disp_fps'),
        'mt': avg_val(cruise_samples, 'main_thread_ms'),
        'count': len(cruise_samples)
    }

    # Calcul des Deltas (Gain / Perte)
    deltas = []
    if tier_ground['fps'] and tier_trans['fps']:
        fps_diff = round(tier_trans['fps'] - tier_ground['fps'], 1)
        mt_diff = round(tier_trans['mt'] - tier_ground['mt'], 1) if tier_ground['mt'] and tier_trans['mt'] else 0.0
        fps_sign = f"+{fps_diff}" if fps_diff > 0 else str(fps_diff)
        mt_sign = f"+{mt_diff}" if mt_diff > 0 else str(mt_diff)
        deltas.append({
            'label': 'Seuil Décollage / Montée (500 ft)',
            'tlod_trans': f"{round(tier_ground['tlod'])} ➔ {round(tier_trans['tlod'])}",
            'fps_delta': f"{fps_sign} FPS",
            'fps_color': '#10b981' if fps_diff >= 0 else '#f43f5e',
            'mt_delta': f"{mt_sign} ms",
            'mt_color': '#10b981' if mt_diff <= 0 else '#f59e0b',
            'verdict': 'MainThread préservé au sol, expansion progressive du décor' if mt_diff <= 2 else 'Augmentation attendue de charge décor'
        })

    if tier_trans['fps'] and tier_cruise['fps']:
        fps_diff = round(tier_cruise['fps'] - tier_trans['fps'], 1)
        mt_diff = round(tier_cruise['mt'] - tier_trans['mt'], 1) if tier_trans['mt'] and tier_cruise['mt'] else 0.0
        fps_sign = f"+{fps_diff}" if fps_diff > 0 else str(fps_diff)
        mt_sign = f"+{mt_diff}" if mt_diff > 0 else str(mt_diff)
        deltas.append({
            'label': 'Seuil Altitude de Croisière (5000 ft)',
            'tlod_trans': f"{round(tier_trans['tlod'])} ➔ {round(tier_cruise['tlod'])}",
            'fps_delta': f"{fps_sign} FPS",
            'fps_color': '#10b981' if fps_diff >= 0 else '#f43f5e',
            'mt_delta': f"{mt_sign} ms",
            'mt_color': '#10b981' if mt_diff <= 0 else '#f59e0b',
            'verdict': 'Maximum visual quality achieved with stable smoothness' if fps_diff >= -3 else 'Dynamic adjustment recommended if stuttering occurs'
        })

    # Récupérer les événements Smart LOD spécifiques s'ils existent
    smart_events = []
    if session_info and session_info.get('smart_lod'):
        smart_events = session_info['smart_lod'].get('events') or []

    return {
        'tiers': [tier_ground, tier_trans, tier_cruise],
        'deltas': deltas,
        'events': smart_events
    }


def analyze_flight_milestones(samples, session_info=None):
    """
    Chronological analysis of flight phases:
    Taxi-Out (Departure), Initial Climb, Climb/TLOD Ceiling, Cruise,
    Descent, Final Approach & Touchdown, Taxi-In (Arrival).
    Measures airport scenery impacts and ground traffic.
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

    # Detection of airborne samples
    airborne_indices = [
        i for i, s in enumerate(samples)
        if (s.get('on_ground') is False and (s.get('agl_ft') is None or s.get('agl_ft') > 40))
        or (s.get('agl_ft') is not None and s.get('agl_ft') >= 80)
    ]

    milestones = []

    # CASE 1: No airborne samples (Flight entirely on ground / Taxi test)
    if not airborne_indices:
        taxi_samples = [s for s in samples if s.get('agl_ft') is None or s.get('agl_ft') < 200]
        if taxi_samples:
            milestones.append({
                'phase': f"Ground Taxi ({dep})" if dep else "Ground Taxi",
                'alt': 'Ground (0 - 50 ft)',
                'tlod': str(mode_val(taxi_samples, 'tlod')),
                'olod': str(mode_val(taxi_samples, 'olod')),
                'fps': str(avg(taxi_samples, 'disp_fps')) + ' FPS',
                'mt': str(avg(taxi_samples, 'main_thread_ms')) + ' ms',
                'notes': 'Airport scenery & ground traffic test (Stationary / Taxi)'
            })
        return milestones

    # CASE 2: Flight has airborne phases
    idx_takeoff = airborne_indices[0]
    idx_touchdown = airborne_indices[-1]

    # --- 1. TAXI-OUT ---
    if idx_takeoff > 0:
        taxi_out_samples = [
            samples[i] for i in range(idx_takeoff)
            if samples[i].get('on_ground', True) and (samples[i].get('agl_ft') is None or samples[i].get('agl_ft') < 80)
        ]
        if len(taxi_out_samples) >= 3:
            taxi_out_title = f"Taxi Out ({dep})" if dep else "Taxi Out"
            milestones.append({
                'phase': taxi_out_title,
                'alt': 'Ground (0 ft)',
                'tlod': str(mode_val(taxi_out_samples, 'tlod')),
                'olod': str(mode_val(taxi_out_samples, 'olod')),
                'fps': str(avg(taxi_out_samples, 'disp_fps')) + ' FPS',
                'mt': str(avg(taxi_out_samples, 'main_thread_ms')) + ' ms',
                'notes': 'Departure airport scenery impact, terminal buildings & ground traffic'
            })

    # In-flight data
    flight_samples = samples[idx_takeoff : idx_touchdown + 1]
    
    # Peak altitude
    max_agl = 0
    idx_peak = idx_takeoff
    for i in range(idx_takeoff, idx_touchdown + 1):
        cur_agl = samples[i].get('agl_ft') or 0
        if cur_agl > max_agl:
            max_agl = cur_agl
            idx_peak = i

    # --- 2. INITIAL CLIMB (0 - 3,000 ft) ---
    climb_init_samples = [
        samples[i] for i in range(idx_takeoff, idx_peak + 1)
        if (samples[i].get('agl_ft') is not None and samples[i].get('agl_ft') < 3000)
    ]
    if climb_init_samples:
        milestones.append({
            'phase': 'Initial Climb',
            'alt': '0 - 3,000 ft',
            'tlod': str(mode_val(climb_init_samples, 'tlod')),
            'olod': str(mode_val(climb_init_samples, 'olod')),
            'fps': str(avg(climb_init_samples, 'disp_fps')) + ' FPS',
            'mt': str(avg(climb_init_samples, 'main_thread_ms')) + ' ms',
            'notes': 'Ground clearance and progressive TLOD ramp'
        })

    # --- 3. CLIMB & TLOD CEILING (3,000 - 10,000 ft) ---
    climb_mid_samples = [
        samples[i] for i in range(idx_takeoff, idx_peak + 1)
        if (samples[i].get('agl_ft') is not None and 3000 <= samples[i].get('agl_ft') < 10000)
    ]
    if climb_mid_samples:
        milestones.append({
            'phase': 'TLOD Peak / Transition',
            'alt': '3,000 - 10,000 ft',
            'tlod': str(mode_val(climb_mid_samples, 'tlod')),
            'olod': str(mode_val(climb_mid_samples, 'olod')),
            'fps': str(avg(climb_mid_samples, 'disp_fps')) + ' FPS',
            'mt': str(avg(climb_mid_samples, 'main_thread_ms')) + ' ms',
            'notes': 'Maximum climb LOD attained'
        })

    # --- 4. CRUISE (> 10,000 ft or cruise level) ---
    if max_agl >= 10000:
        cruise_samples = [
            s for s in flight_samples
            if s.get('agl_ft') is not None and s.get('agl_ft') >= 10000
        ]
        cruise_label = 'High Altitude Cruise'
        cruise_alt_str = '> 10,000 ft'
    elif max_agl >= 2000:
        threshold = max_agl * 0.85
        cruise_samples = [
            s for s in flight_samples
            if (s.get('agl_ft') or 0) >= threshold and abs(s.get('fpm') or 0) < 500
        ]
        cruise_label = 'Cruise Level'
        cruise_alt_str = f'~{mode_val(cruise_samples, "agl_ft")} ft' if cruise_samples else f'{max_agl} ft'
    else:
        cruise_samples = []
        cruise_label = 'Cruise'
        cruise_alt_str = ''

    if cruise_samples:
        milestones.append({
            'phase': cruise_label,
            'alt': cruise_alt_str,
            'tlod': str(mode_val(cruise_samples, 'tlod')),
            'olod': str(mode_val(cruise_samples, 'olod')),
            'fps': str(avg(cruise_samples, 'disp_fps')) + ' FPS',
            'mt': str(avg(cruise_samples, 'main_thread_ms')) + ' ms',
            'notes': 'Extended horizon rendering & FPS stability'
        })

    # --- 5. DESCENT (after peak, altitude >= 3,000 ft) ---
    descent_samples = [
        samples[i] for i in range(idx_peak + 1, idx_touchdown + 1)
        if (samples[i].get('agl_ft') is not None and samples[i].get('agl_ft') >= 3000 and (samples[i].get('fpm') or 0) <= 200)
    ]
    if descent_samples:
        milestones.append({
            'phase': 'Descent',
            'alt': '> 3,000 ft',
            'tlod': str(mode_val(descent_samples, 'tlod')),
            'olod': str(mode_val(descent_samples, 'olod')),
            'fps': str(avg(descent_samples, 'disp_fps')) + ' FPS',
            'mt': str(avg(descent_samples, 'main_thread_ms')) + ' ms',
            'notes': 'Altitude descent & arrival scenery streaming'
        })

    # --- 6. FINAL APPROACH & TOUCHDOWN (after peak, altitude < 3,000 ft) ---
    approach_samples = [
        samples[i] for i in range(idx_peak + 1, idx_touchdown + 1)
        if (samples[i].get('agl_ft') is not None and samples[i].get('agl_ft') < 3000)
    ]
    if approach_samples:
        milestones.append({
            'phase': 'Final Approach & Touchdown',
            'alt': '3,000 - 0 ft',
            'tlod': str(mode_val(approach_samples, 'tlod')),
            'olod': str(mode_val(approach_samples, 'olod')),
            'fps': str(avg(approach_samples, 'disp_fps')) + ' FPS',
            'mt': str(avg(approach_samples, 'main_thread_ms')) + ' ms',
            'notes': 'Runway alignment, capture & final approach scenery'
        })

    # --- 7. TAXI-IN ---
    if idx_touchdown < len(samples) - 1:
        taxi_in_samples = [
            samples[i] for i in range(idx_touchdown + 1, len(samples))
            if samples[i].get('on_ground', True) and (samples[i].get('agl_ft') is None or samples[i].get('agl_ft') < 80)
        ]
        if len(taxi_in_samples) >= 3:
            taxi_in_title = f"Taxi In ({arr})" if arr else "Taxi In"
            milestones.append({
                'phase': taxi_in_title,
                'alt': 'Ground (0 ft)',
                'tlod': str(mode_val(taxi_in_samples, 'tlod')),
                'olod': str(mode_val(taxi_in_samples, 'olod')),
                'fps': str(avg(taxi_in_samples, 'disp_fps')) + ' FPS',
                'mt': str(avg(taxi_in_samples, 'main_thread_ms')) + ' ms',
                'notes': 'Arrival airport scenery impact, taxiways & gate parking'
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
        self.in_flight = False
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
        self.sim_rate = 1.0
        self.is_paused = False
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
            self.in_flight = False
            self.is_paused = False
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
            self.sim_rate = 1.0
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

    def _on_quit(self, recv):
        with self._lock:
            self.connected = False
            self.in_flight = False
            self.is_paused = False
        return True

    def _on_event(self, recv):
        try:
            ev_id = getattr(recv, 'uEventID', None)
            ev_data = getattr(recv, 'dwData', None)
            with self._lock:
                if ev_id in (5, 6):  # EVENT_ID_PAUSE, EVENT_ID_PAUSE_EX1
                    self.is_paused = bool(ev_data == 1)
                elif ev_id == 4:  # EVENT_ID_SIMSTOP
                    self.is_paused = True
                elif ev_id == 3:  # EVENT_ID_SIMSTART
                    self.is_paused = False
                    self.in_flight = True
                elif ev_id == 2:  # EVENT_ID_SIM
                    if ev_data == 1:
                        self.is_paused = False
                        self.in_flight = True
                    elif ev_data == 0:
                        self.is_paused = True
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
                    if scdefs and hasattr(scdefs, 'RECV_QUIT'):
                        try:
                            sc.add_receiver(scdefs.RECV_QUIT, self._on_quit)
                        except Exception:
                            pass
                    if scdefs and hasattr(scdefs, 'RECV_EVENT'):
                        try:
                            sc.add_receiver(scdefs.RECV_EVENT, self._on_event)
                        except Exception:
                            pass

                    EVENT_ID_FRAME = 1
                    EVENT_ID_SIM = 2
                    EVENT_ID_SIMSTART = 3
                    EVENT_ID_SIMSTOP = 4
                    EVENT_ID_PAUSE = 5
                    EVENT_ID_PAUSE_EX1 = 6
                    sc.SubscribeToSystemEvent(EVENT_ID_FRAME, "Frame")
                    try:
                        sc.SubscribeToSystemEvent(EVENT_ID_SIM, "Sim")
                        sc.SubscribeToSystemEvent(EVENT_ID_SIMSTART, "SimStart")
                        sc.SubscribeToSystemEvent(EVENT_ID_SIMSTOP, "SimStop")
                        sc.SubscribeToSystemEvent(EVENT_ID_PAUSE, "Pause")
                        sc.SubscribeToSystemEvent(EVENT_ID_PAUSE_EX1, "Pause_EX1")
                    except Exception:
                        pass

                    # Souscription aux SimVars de vol
                    try:
                        simvars = [
                            {"name": "PLANE ALT ABOVE GROUND", "units": "feet"},
                            {"name": "VERTICAL SPEED", "units": "feet/minute"},
                            {"name": "AIRSPEED INDICATED", "units": "knots"},
                            {"name": "GROUND VELOCITY", "units": "knots"},
                            {"name": "SIM ON GROUND", "units": "bool"},
                            {"name": "SIMULATION RATE", "units": "number"},
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
                                if 'SIMULATION RATE' in sdata and sdata['SIMULATION RATE'] is not None:
                                    try:
                                        self.sim_rate = round(float(sdata['SIMULATION RATE']), 2)
                                    except Exception:
                                        pass
                                if 'PLANE LATITUDE' in sdata and sdata['PLANE LATITUDE'] is not None:
                                    self.lat = float(sdata['PLANE LATITUDE'])
                                if 'PLANE LONGITUDE' in sdata and sdata['PLANE LONGITUDE'] is not None:
                                    self.lon = float(sdata['PLANE LONGITUDE'])
                                if 'TITLE' in sdata and sdata['TITLE']:
                                    t_str = str(sdata['TITLE']).strip()
                                    if t_str and t_str.lower() != 'none':
                                        self.aircraft_title = t_str
                                        self.in_flight = True
                                    else:
                                        self.aircraft_title = None
                                        self.in_flight = False

                        last_calc_time = now

            except Exception:
                self._cleanup()
                self._stop_event.wait(2.0)

    def get_data(self):
        with self._lock:
            return {
                "connected": self.connected,
                "in_flight": self.in_flight,
                "is_paused": self.is_paused,
                "base_fps": self.base_fps,
                "displayed_fps": self.displayed_fps,
                "frame_time_ms": self.frame_time_ms,
                "agl_ft": self.agl_ft,
                "fpm": self.vertical_speed_fpm,
                "airspeed_kts": self.airspeed_kts,
                "ground_speed_kts": self.ground_speed_kts,
                "on_ground": self.on_ground,
                "aircraft": self.aircraft_title,
                "sim_rate": self.sim_rate,
                "lat": self.lat,
                "lon": self.lon
            }

SIMCONNECT_CLIENT = SimConnectTelemetryClient()
SIMCONNECT_CLIENT.start()
_last_telemetry_cache = None

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
                    dis_folders = fm.get('disabled_folders', [])
                    dis_xml = fm.get('disabled_xml_packages', [])
                    total_dis = dis if dis > 0 else (len(dis_folders) + len(dis_xml))
                    if total_dis > 0:
                        alts_raw = fm.get('alternates', [])
                        alts = [a if isinstance(a, str) else a.get('icao', '') for a in alts_raw]
                        alts = [a for a in alts if a]
                        profile = fm.get('profile', 'CORRIDOR').upper()
                        alt_str = f" [Alts: {','.join(alts)}]" if alts else ""
                        if profile == 'DIRECT':
                            return f"SCENERYX DIRECT A->B ({dep} -> {arr} | {total_dis} isolated sceneries)", True, dep, arr, total_dis, 'direct'
                        elif profile == 'SIMBRIEF':
                            return f"SCENERYX SIMBRIEF ({dep} -> {arr}{alt_str} | {total_dis} isolated sceneries)", True, dep, arr, total_dis, 'simbrief'
                        else:
                            return f"SCENERYX CORRIDOR ({dep} -> {arr}{alt_str} | {total_dis} isolated sceneries)", True, dep, arr, total_dis, 'corridor'
        except Exception:
            pass
    return "BASELINE STANDARD (All sceneries active)", False, "", "", 0, "baseline_full"


def detect_route_optimization_state(session_info=None):
    """
    Détecte précisément l'état de l'optimisation de route / isolation de scènes SceneryX.
    Distingue rigoureusement :
    - Route Isolation Active (Packages de scènes désactivés hors couloir/trajectoire, disabled_count > 0)
    - Mode Baseline / Sans Isolation (Tous les packages actifs, même si un plan SimBrief est suivi)
    """
    # 1. Vérification contextuelle depuis session_info si fourni
    if session_info and isinstance(session_info, dict):
        is_corr = bool(session_info.get('is_corridor'))
        dis_cnt = session_info.get('disabled_count', 0)
        mode_str = str(session_info.get('mode_str', ''))
        detection_source = str(session_info.get('detection_source', ''))
        mode_display = str(session_info.get('mode_display', ''))
        has_sb = "SimBrief" in detection_source or "SIMBRIEF" in mode_display.upper() or "SIMBRIEF" in mode_str.upper()

        if is_corr and dis_cnt > 0:
            profile = "CORRIDOR"
            if "DIRECT" in mode_str.upper() or "DIRECT" in mode_display.upper():
                profile = "DIRECT"
            elif "SIMBRIEF" in mode_str.upper() or "SIMBRIEF" in mode_display.upper():
                profile = "SIMBRIEF"
            return {
                "is_optimized": True,
                "isolation_active": True,
                "disabled_count": dis_cnt,
                "profile": profile,
                "has_simbrief": profile == "SIMBRIEF" or has_sb,
                "badge_text": "SCENERYX OPTIMIZED",
                "badge_bg": "#059669",
                "mode_display": f"SCENERYX {profile} ({dis_cnt} isolated sceneries)",
                "status_desc": f"Route isolation active ({dis_cnt} sceneries disabled outside flight corridor)",
                "reason": f"Active flight corridor with {dis_cnt} isolated packages"
            }
        else:
            return {
                "is_optimized": False,
                "isolation_active": False,
                "disabled_count": 0,
                "profile": "BASELINE",
                "has_simbrief": has_sb,
                "badge_text": "BASELINE STANDARD",
                "badge_bg": "#d97706",
                "mode_display": "BASELINE (SimBrief OFP • No Scenery Isolation)" if has_sb else "BASELINE STANDARD (All sceneries active)",
                "status_desc": "No scenery isolation active (Baseline library)",
                "reason": "Flight performed without SceneryX scenery isolation"
            }

    # 2. Lecture directe depuis settings.json
    appdata = os.getenv('APPDATA', '')
    settings_path = os.path.join(appdata, 'SceneryX', 'settings.json')
    has_simbrief = False
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                fm = data.get('flight_mode', {})
                sb = data.get('latest_simbrief_flight') or (fm.get('simbrief_flight') if isinstance(fm, dict) else None)
                has_simbrief = bool(sb)

                if isinstance(fm, dict) and fm.get('active'):
                    dis = fm.get('disabled_count', 0)
                    dis_folders = fm.get('disabled_folders', [])
                    dis_xml = fm.get('disabled_xml_packages', [])
                    total_dis = dis if dis > 0 else (len(dis_folders) + len(dis_xml))
                    profile = str(fm.get('profile', 'CORRIDOR')).upper()

                    if total_dis > 0:
                        return {
                            "is_optimized": True,
                            "isolation_active": True,
                            "disabled_count": total_dis,
                            "profile": profile,
                            "has_simbrief": profile == "SIMBRIEF" or has_simbrief,
                            "badge_text": "SCENERYX OPTIMIZED",
                            "badge_bg": "#059669",
                            "mode_display": f"SCENERYX {profile} ({total_dis} isolated sceneries)",
                            "status_desc": f"Route isolation active ({total_dis} sceneries disabled outside corridor)",
                            "reason": f"Active flight corridor with {total_dis} isolated packages"
                        }
        except Exception as e:
            print(f"[detect_route_optimization_state] Error reading settings: {e}")

    return {
        "is_optimized": False,
        "isolation_active": False,
        "disabled_count": 0,
        "profile": "BASELINE",
        "has_simbrief": has_simbrief,
        "badge_text": "BASELINE STANDARD",
        "badge_bg": "#d97706",
        "mode_display": "BASELINE (SimBrief OFP • No Scenery Isolation)" if has_simbrief else "BASELINE STANDARD (All sceneries active)",
        "status_desc": "No scenery isolation active (Baseline library)",
        "reason": "Flight performed without SceneryX scenery isolation"
    }


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


def get_flight_network_info():
    """Safely retrieves cached or live network/internet telemetry diagnostics."""
    try:
        from flight_rig_optimizer import detect_network_info
        return detect_network_info()
    except Exception:
        return {}


def get_flight_graphics_profile():
    """Safely retrieves active MSFS graphics profile snapshot for telemetry reports."""
    try:
        import flight_rig_optimizer
        return flight_rig_optimizer.get_active_profile_snapshot()
    except Exception:
        return None


def generate_graphics_profile_section(session_info):
    """
    Generates a sleek, structured HTML section displaying the active MSFS graphics profile,
    mode, headline parameter highlights, and a collapsible accordion containing all engine settings.
    """
    prof_data = (session_info or {}).get('graphics_profile')
    if not prof_data:
        prof_data = get_flight_graphics_profile()
    if not prof_data or not prof_data.get('name'):
        return ""

    prof_name = prof_data.get('name', 'Active Profile')
    prof_mode = prof_data.get('mode', 'Standard Mode')
    highlights = prof_data.get('highlights', {})
    settings = prof_data.get('settings', [])

    color_map = {
        'emerald': '#10b981',
        'amber': '#f59e0b',
        'orange': '#f97316',
        'rose': '#f43f5e',
        'cyan': '#06b6d4',
        'slate': '#94a3b8'
    }

    # Top headline cards (clean, prominent, easy to read at a glance)
    hl_cards_html = ""
    for hl_label, hl_val in highlights.items():
        hl_cards_html += f"""
        <div style="background:#0b0f19; border:1px solid rgba(51,65,85,0.6); border-radius:10px; padding:12px 14px;">
            <div style="color:#64748b; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">{hl_label}</div>
            <div style="color:#f8fafc; font-size:15px; font-weight:800; margin-top:4px; font-family:monospace;">{hl_val}</div>
        </div>
        """

    # Collapsible list of all detailed engine settings
    all_settings_html = ""
    for s in settings:
        s_name = s.get('name', 'Setting')
        s_val = s.get('value', '')
        s_lbl = s.get('rating_label', '')
        s_color = color_map.get(s.get('rating_color', ''), '#94a3b8')
        s_tag = f"""<span style="display:inline-flex; align-items:center; gap:4px; font-size:10px; font-weight:700; color:{s_color}; background:#0f172a; border:1px solid rgba(51,65,85,0.8); border-radius:4px; padding:2px 6px; text-transform:uppercase;"><span style="width:5px; height:5px; border-radius:50%; background:{s_color};"></span>{s_lbl}</span>""" if s_lbl else ""
        
        all_settings_html += f"""
        <div style="background:#0b0f19; border:1px solid rgba(51,65,85,0.6); border-radius:8px; padding:10px 12px; display:flex; flex-direction:column; justify-content:space-between; gap:6px;">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                <span style="color:#94a3b8; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.3px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="{s_name}">{s_name}</span>
                {s_tag}
            </div>
            <div style="color:#f8fafc; font-size:13px; font-weight:700; word-break:break-word;">{s_val}</div>
        </div>
        """

    return f"""
        <!-- ACTIVE GRAPHICS PROFILE & CALIBRATION -->
        <div class="chart-box" style="padding: 20px; margin-bottom: 24px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:10px;">
                <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                    <div class="chart-title" style="margin-bottom:0; letter-spacing:0.5px;">ACTIVE GRAPHICS PROFILE & CALIBRATION</div>
                    <span style="padding:4px 10px; border-radius:6px; background:#065f46; color:#a7f3d0; border:1px solid #059669; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">{prof_name}</span>
                </div>
                <div style="font-size:11px; color:#94a3b8; font-weight:700; text-transform:uppercase; background:#0b0f19; border:1px solid rgba(51,65,85,0.6); border-radius:6px; padding:4px 10px;">
                    {prof_mode}
                </div>
            </div>
            
            <!-- KEY HEADLINE SETTINGS -->
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin-bottom:14px;">
                {hl_cards_html}
            </div>

            <!-- COLLAPSIBLE FULL PARAMETERS ACCORDION -->
            <details style="background:#080c14; border:1px solid rgba(51,65,85,0.4); border-radius:10px; padding:12px 16px;">
                <summary style="cursor:pointer; user-select:none; font-size:11px; font-weight:700; color:#94a3b8; outline:none; display:flex; align-items:center; justify-content:space-between;">
                    <span>FULL ENGINE PARAMETERS & DIRECTIVES ({len(settings)} SETTINGS)</span>
                    <span style="color:#38bdf8; font-family:monospace; font-size:10px; text-transform:uppercase;">[ CLICK TO EXPAND / COLLAPSE ]</span>
                </summary>
                <div style="margin-top:14px; display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:10px;">
                    {all_settings_html}
                </div>
            </details>
        </div>
    """


def generate_automated_flight_narrative(samples, session_info):
    """
    Generates an expert automated textual diagnostic of the flight,
    explaining bottlenecks, VRAM pressure, and cache streaming activity.
    """
    if not samples:
        return "<p>Insufficient telemetry data to generate a diagnostic.</p>"

    vrams = [s.get('vram_used', s.get('vram_used_mb', 0)) for s in samples]
    commits = [s.get('msfs_commit', s.get('msfs_commit_mb', 0)) for s in samples]
    fps_list = [s.get('disp_fps', s.get('displayed_fps')) for s in samples if s.get('disp_fps') is not None or s.get('displayed_fps') is not None]
    mt_list = [s.get('main_thread_ms') for s in samples if s.get('main_thread_ms') is not None]
    gpus = [s.get('gpu_util', s.get('gpu_util_pct', 0)) for s in samples]
    tlods = [s.get('tlod') for s in samples if s.get('tlod') is not None]
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

    # Route Optimization state detection
    opt_state = detect_route_optimization_state(session_info)
    is_optimized = opt_state.get('is_optimized', False)
    dis_count = opt_state.get('disabled_count', 0)

    # LOD Engine Info (Smart LOD / AutoFPS)
    smart_lod_info = session_info.get('smart_lod') or {}
    smart_lod_active = bool(smart_lod_info.get('enabled'))
    smart_lod_cfg = smart_lod_info.get('config', {})

    autofps_active = session_info.get('autofps_active', False)
    autofps_cfg = session_info.get('autofps_config', {})
    cloud_status = session_info.get('cloud_events', 'Nominal')

    autofps_diag = ""
    if smart_lod_active:
        st_mode = smart_lod_info.get('mode', 'IFR').lower()
        t_fps = smart_lod_cfg.get(f'{st_mode}_target_fps', 40)
        min_tlod = smart_lod_cfg.get(f'{st_mode}_tlod_ground', 100)
        max_tlod = smart_lod_cfg.get(f'{st_mode}_tlod_cruise', 250)
        autofps_diag = f"<li><strong>LOD Management:</strong> Smart LOD Dynamic Engine Active (Target <strong>{t_fps} FPS</strong> • TLOD {min_tlod} ➔ {max_tlod}, average TLOD: <strong>{avg_tlod}</strong>).</li>"
    elif autofps_active and autofps_cfg:
        tfps = autofps_cfg.get('target_fps_fg') or autofps_cfg.get('targetFps', '--')
        min_t = autofps_cfg.get('min_tlod') or autofps_cfg.get('minTLod', '--')
        max_t = autofps_cfg.get('max_tlod') or autofps_cfg.get('maxTLod', '--')
        autofps_diag = f"<li><strong>Active AutoFPS Integration:</strong> Target {tfps} FPS, configured TLOD range {min_t} to {max_t}. Effective average TLOD measured at <strong>{avg_tlod}</strong>. Cloud state: <em>{cloud_status}</em>.</li>"
    elif autofps_active:
        autofps_diag = f"<li><strong>Active AutoFPS Integration:</strong> Dynamic TLOD adjustments detected (average in-flight TLOD: <strong>{avg_tlod}</strong>). Cloud state: <em>{cloud_status}</em>.</li>"
    else:
        autofps_diag = f"<li><strong>LOD Management:</strong> Dynamic LOD engine inactive (static or fixed values, average TLOD: <strong>{avg_tlod}</strong>).</li>"

    # Main bottleneck diagnostic
    if avg_gpu >= 96 and (avg_mt != "N/A" and avg_mt <= 25.0):
        bottleneck_diag = "<strong>Balanced GPU-Bound Profile:</strong> GPU ran at full capacity with optimal smoothness, without severe MainThread bottlenecks."
    elif avg_mt != "N/A" and avg_mt > 30.0:
        bottleneck_diag = f"<strong>MainThread Limited Profile ({avg_mt} ms avg):</strong> The main CPU thread was the limiting factor, typical of ground phases with complex avionics and dense scenery."
    else:
        bottleneck_diag = "<strong>Balanced Mixed Profile:</strong> Harmonious balance between CPU computation and graphics rendering."

    # VRAM & Paging Diagnostic
    if vram_peak_pct >= 92.0:
        vram_diag = f"<span style='color:#ef4444;'><strong>Paging Risk Alert:</strong> VRAM peaked at {peak_vram:,.0f} MB ({vram_peak_pct}%). Close to system RAM spillover threshold, potentially causing micro-stutters in external view.</span>"
    elif vram_peak_pct >= 85.0:
        vram_diag = f"<span style='color:#f59e0b;'><strong>Controlled High Zone:</strong> Peak VRAM at {peak_vram:,.0f} MB ({vram_peak_pct}%). Sufficient safety headroom without triggering paged memory.</span>"
    else:
        if is_optimized and dis_count > 0:
            vram_diag = f"<span style='color:#10b981;'><strong>Excellent Video Headroom:</strong> Peak VRAM contained at {peak_vram:,.0f} MB ({vram_peak_pct}%). SceneryX route isolation eliminated {dis_count} out-of-corridor scenery packages.</span>"
        else:
            vram_diag = f"<span style='color:#10b981;'><strong>Adequate Video Headroom:</strong> Peak VRAM contained at {peak_vram:,.0f} MB ({vram_peak_pct}%). VRAM footprint was maintained within safe limits despite running all installed sceneries.</span>"

    # Ground & airport impact diagnostic
    milestones = analyze_flight_milestones(samples, session_info)
    ground_notes = []
    for m in milestones:
        if 'Taxi Out' in m['phase'] or 'Taxi In' in m['phase']:
            ground_notes.append(f"{m['phase']}: <strong>{m['fps']}</strong> (MainThread <strong>{m['mt']}</strong>)")
        elif 'Approach' in m['phase'] or 'Approche' in m['phase']:
            ground_notes.append(f"Final Approach: <strong>{m['fps']}</strong> (MainThread <strong>{m['mt']}</strong>)")

    ground_diag = ""
    if ground_notes:
        ground_diag = f"<li><strong>Ground & Airport Behavior:</strong> {' • '.join(ground_notes)}.</li>"

    monitoring_duration = session_info.get('duration') or "00:00"

    # Network Streaming Diagnostic
    net_info = session_info.get('network')
    if not net_info:
        net_info = get_flight_network_info()

    net_diag = ""
    if net_info and net_info.get('is_connected'):
        net_spd = net_info.get('link_speed_str', '')
        ping_val = net_info.get('ping_ms')
        ping_txt = f" ({ping_val} ms ping)" if ping_val is not None else ""
        if net_info.get('is_wifi'):
            sig = net_info.get('wifi_signal_pct')
            sig_txt = f", {sig}% signal" if sig is not None else ""
            net_diag = f" Online photogrammetry & cloud scenery streaming served via <strong>Wi-Fi {net_spd}{sig_txt}{ping_txt}</strong>."
        else:
            net_diag = f" Online photogrammetry & thin-client world data secured via ultra-low latency <strong>Ethernet {net_spd}{ping_txt}</strong>."
    elif net_info and not net_info.get('is_connected'):
        net_diag = " <span style='color:#ef4444;'>No active internet connection detected during flight (offline mode).</span>"

    # Dynamic recommendation based on Route Optimization state
    if is_optimized and dis_count > 0:
        recommendation_text = (
            f"Route corridor isolation was actively engaged during this flight (<strong>{dis_count} out-of-corridor sceneries unloaded</strong>), "
            "preserving VRAM headroom and eliminating asset-streaming hitches. "
            "Keep corridor or direct route isolation active on subsequent flights to sustain smooth performance at complex airport hubs."
        )
    else:
        recommendation_text = (
            "This flight was conducted in <strong>Baseline mode without Scenery Isolation</strong> (all airport sceneries remained active in MSFS). "
            f"To free up VRAM ({vram_peak_pct}% peak observed) and minimize MainThread stuttering on approach into dense areas, "
            "consider activating <strong>SceneryX Route Corridor</strong> or <strong>Direct Isolation</strong> before your next flight."
        )

    narrative = f"""
    <div style="background:#0f172a; border:1px solid #1e293b; border-radius:16px; padding:20px; margin-bottom:24px; line-height:1.6; font-size:13px; color:#cbd5e1;">
        <h3 style="margin-top:0; color:#38bdf8; font-size:16px;">Flight Analysis Summary</h3>
        <ul style="padding-left:20px; margin-bottom:12px;">
            <li><strong>Flight Monitoring Duration:</strong> Total recorded monitoring time of <strong>{monitoring_duration}</strong> ({len(samples)} logged telemetry samples).</li>
            <li><strong>System Behavior & Primary Bottleneck:</strong> {bottleneck_diag}</li>
            <li><strong>Video Memory Footprint (VRAM):</strong> {vram_diag}</li>
            <li><strong>Smoothness & Frame Pacing:</strong> Global average of <strong>{avg_fps} FPS</strong> with average MainThread of <strong>{avg_mt} ms</strong>.</li>
            {ground_diag}
            {autofps_diag}
            <li><strong>Rolling Cache / Disk IO & Network Streaming:</strong> Peak texture & model streaming access of <strong>{peak_io} Mbps</strong> logged during area transitions.{net_diag}</li>
        </ul>
        <div style="background:#0b0f19; border:1px solid #1e293b; padding:12px 16px; border-radius:8px; font-size:12px; color:#cbd5e1; margin-top:14px;">
            <strong style="color:#f8fafc;">Recommendation for next flight:</strong> {recommendation_text}
        </div>
    </div>
    """
    return narrative


def generate_html_report(csv_path, session_info, samples):
    html_path = csv_path.replace('.csv', '.html')
    os.makedirs(os.path.dirname(os.path.abspath(html_path)), exist_ok=True)
    
    times = [s.get('elapsed') or s.get('time_str') or str(s.get('elapsed_sec', '')) for s in samples]
    vram_vals = [s.get('vram_used', s.get('vram_used_mb', 0)) for s in samples]
    msfs_ram_vals = [s.get('msfs_ram', s.get('msfs_ram_mb', 0)) for s in samples]
    msfs_commit_vals = [s.get('msfs_commit', s.get('msfs_commit_mb', 0)) for s in samples]
    gpu_power_vals = [s.get('gpu_power', s.get('gpu_power_w', 0)) for s in samples]
    io_reads_mbps = [s.get('cache_read_mbps', 0) for s in samples]

    # Smart LOD Trigger points overlay for lodChart
    smart_triggers = []
    last_t = None
    for s in samples:
        cur_t = s.get('tlod')
        if cur_t is not None and last_t is not None and abs(cur_t - last_t) >= 5:
            smart_triggers.append(cur_t)
        else:
            smart_triggers.append(None)
        if cur_t is not None:
            last_t = cur_t

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

    # MSFS Process Dedicated VRAM (PDH counter)
    msfs_vram_vals = [s.get('msfs_vram', s.get('msfs_vram_mb', 0)) or 0.0 for s in samples]
    has_msfs_vram = any(v > 0 for v in msfs_vram_vals)
    if has_msfs_vram:
        valid_msfs_vram = [v for v in msfs_vram_vals if v > 0]
        avg_msfs_vram_mb = round(sum(valid_msfs_vram) / len(valid_msfs_vram), 1)
        peak_msfs_vram_mb = max(valid_msfs_vram)
        min_msfs_vram_mb = min(valid_msfs_vram)
        avg_msfs_vram_gb = round(avg_msfs_vram_mb / 1024.0, 1)
        peak_msfs_vram_gb = round(peak_msfs_vram_mb / 1024.0, 1)
    else:
        avg_msfs_vram_gb = None
        peak_msfs_vram_gb = None

    # Track dynamic flight events, VR periods, and Pauses
    tlod_vals = [s.get('tlod') for s in samples]
    olod_vals = [s.get('olod') for s in samples]
    sim_rate_vals = [round(float(s.get('sim_rate', 1.0) or 1.0), 2) for s in samples]
    has_sim_compression = any(r > 1.0 for r in sim_rate_vals)
    has_olod = any(o is not None for o in olod_vals)

    flight_events = []
    vr_intervals = []
    pause_intervals = []
    vr_start_idx = None
    pause_start_idx = None
    last_tlod = None
    last_olod = None
    last_rate = None
    last_vr = None

    for i, s in enumerate(samples):
        t_str = s.get('time_str') or str(s.get('elapsed', ''))
        cur_t = s.get('tlod')
        cur_o = s.get('olod')
        cur_r = round(float(s.get('sim_rate', 1.0) or 1.0), 2)
        cur_vr = bool(s.get('is_vr', False))
        cur_paused = bool(s.get('is_paused', False))

        # VR interval tracking
        if cur_vr and vr_start_idx is None:
            vr_start_idx = i
        elif not cur_vr and vr_start_idx is not None:
            vr_intervals.append({"startIdx": vr_start_idx, "endIdx": i})
            vr_start_idx = None

        # Pause interval tracking
        if cur_paused and pause_start_idx is None:
            pause_start_idx = i
        elif not cur_paused and pause_start_idx is not None:
            pause_intervals.append({"startIdx": pause_start_idx, "endIdx": i})
            pause_start_idx = None

        # TLOD changes (step >= 5)
        if cur_t is not None:
            if last_tlod is not None and abs(cur_t - last_tlod) >= 5:
                flight_events.append({
                    "idx": i,
                    "time": t_str,
                    "type": "TLOD",
                    "badge": "TLOD STEP",
                    "badge_color": "#ec4899",
                    "label": f"TLOD {int(last_tlod)} ➔ {int(cur_t)}",
                    "alt": s.get('agl_ft'),
                    "color": "#ec4899"
                })
            last_tlod = cur_t

        # OLOD changes (step >= 10)
        if cur_o is not None:
            if last_olod is not None and abs(cur_o - last_olod) >= 10:
                flight_events.append({
                    "idx": i,
                    "time": t_str,
                    "type": "OLOD",
                    "badge": "OLOD STEP",
                    "badge_color": "#a855f7",
                    "label": f"OLOD {int(last_olod)} ➔ {int(cur_o)}",
                    "alt": s.get('agl_ft'),
                    "color": "#a855f7"
                })
            last_olod = cur_o

        # Sim Rate changes
        if cur_r is not None:
            if last_rate is not None and cur_r != last_rate:
                flight_events.append({
                    "idx": i,
                    "time": t_str,
                    "type": "SIM_RATE",
                    "badge": "SIM RATE",
                    "badge_color": "#f59e0b",
                    "label": f"Sim Rate x{cur_r:g}",
                    "alt": s.get('agl_ft'),
                    "color": "#f59e0b"
                })
            last_rate = cur_r

        # VR transitions
        if last_vr is not None and cur_vr != last_vr:
            flight_events.append({
                "idx": i,
                "time": t_str,
                "type": "VR_MODE",
                "badge": "VR MODE",
                "badge_color": "#38bdf8" if cur_vr else "#94a3b8",
                "label": "VR Headset Active" if cur_vr else "2D Desktop Active",
                "alt": s.get('agl_ft'),
                "color": "#38bdf8" if cur_vr else "#94a3b8"
            })
        last_vr = cur_vr

    if vr_start_idx is not None:
        vr_intervals.append({"startIdx": vr_start_idx, "endIdx": len(samples) - 1})
    if pause_start_idx is not None:
        pause_intervals.append({"startIdx": pause_start_idx, "endIdx": len(samples) - 1})

    for p in session_info.get('pause_events', []):
        dur_str = p.get('duration_str') or f"{p.get('duration_sec', 0)}s"
        flight_events.append({
            "idx": 0,
            "time": p.get('time_str', '--'),
            "type": "PAUSE",
            "badge": "PAUSE",
            "badge_color": "#eab308",
            "label": f"Simulator Paused ({dur_str})",
            "alt": None,
            "color": "#eab308"
        })

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

    opt_state = detect_route_optimization_state(session_info)
    is_corridor = opt_state['is_optimized']
    badge_bg = opt_state['badge_bg']
    badge_text = opt_state['badge_text']

    aircraft_display = session_info.get('aircraft') or "Not detected / Generic"
    route_display = session_info.get('route_display') or "Not specified"
    mode_display = session_info.get('mode_display') or opt_state['mode_display']
    mode_color = "#10b981" if is_corridor else "#f59e0b"
    autofps_active = session_info.get('autofps_active', False)
    autofps_cfg = session_info.get('autofps_config', {})
    cloud_status = session_info.get('cloud_events', 'Nominal')

    smart_lod_info = session_info.get('smart_lod') or {}
    smart_lod_active = bool(smart_lod_info.get('enabled'))
    smart_lod_cfg = smart_lod_info.get('config', {})

    if smart_lod_active:
        lod_badge_text = "SMART LOD ACTIVE"
        lod_badge_bg = "#059669"
    elif autofps_active:
        lod_badge_text = "AUTOFPS LIVE"
        lod_badge_bg = "#059669"
    else:
        lod_badge_text = "LOD ENGINE INACTIVE"
        lod_badge_bg = "#475569"

    # Network Connection Badge for Contextual Header
    net_info = session_info.get('network')
    if not net_info:
        net_info = get_flight_network_info()

    if net_info and net_info.get('is_connected'):
        net_spd = str(net_info.get('link_speed_str') or '').upper().strip()
        if net_info.get('is_wifi'):
            sig = net_info.get('wifi_signal_pct')
            if sig is not None:
                net_badge_text = f"WI-FI ({sig}%)" if not net_spd else f"WI-FI {net_spd}"
            else:
                net_badge_text = f"WI-FI {net_spd}".strip() if net_spd else "WI-FI"
            net_badge_bg = "#059669" if (sig is None or sig >= 60) else "#d97706"
        else:
            net_badge_text = f"ETHERNET {net_spd}".strip() if net_spd else "ETHERNET"
            net_badge_bg = "#059669"
    else:
        net_badge_text = "OFFLINE"
        net_badge_bg = "#dc2626"

    # Build Smart LOD Performance & Threshold Analysis section
    smart_lod_perf = analyze_smart_lod_performance(samples, session_info)
    smart_lod_section = ""
    if smart_lod_perf and smart_lod_perf.get('deltas'):
        delta_rows = ""
        for d in smart_lod_perf['deltas']:
            delta_rows += f"""
            <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                <td style="padding:10px 12px; font-weight:bold; color:#f8fafc;">{d['label']}</td>
                <td style="padding:10px 12px; color:#38bdf8; font-family:monospace; font-weight:bold;">{d['tlod_trans']}</td>
                <td style="padding:10px 12px; color:{d['fps_color']}; font-family:monospace; font-weight:bold;">{d['fps_delta']}</td>
                <td style="padding:10px 12px; color:{d['mt_color']}; font-family:monospace; font-weight:bold;">{d['mt_delta']}</td>
                <td style="padding:10px 12px; color:#cbd5e1; font-size:12px;">{d['verdict']}</td>
            </tr>
            """

        event_rows = ""
        events = smart_lod_perf.get('events', [])
        if events:
            for ev in events[-8:]:
                event_rows += f"""
                <tr style="border-bottom:1px solid rgba(255,255,255,0.03); font-size:12px;">
                    <td style="padding:6px 12px; color:#94a3b8; font-family:monospace;">{ev.get('time_str')}</td>
                    <td style="padding:6px 12px; color:#06b6d4; font-family:monospace;">{ev.get('agl_ft')} ft</td>
                    <td style="padding:6px 12px; color:#ec4899; font-family:monospace; font-weight:bold;">TLOD {ev.get('old_tlod')} ➔ {ev.get('new_tlod')}</td>
                    <td style="padding:6px 12px; color:#10b981; font-family:monospace;">{ev.get('fps')} FPS</td>
                    <td style="padding:6px 12px; color:#cbd5e1;">{ev.get('reason')}</td>
                </tr>
                """
            events_table_html = f"""
            <div style="margin-top:16px; border-top:1px solid #1e293b; padding-top:12px;">
                <div style="font-size:12px; font-weight:bold; color:#38bdf8; margin-bottom:8px;">⚡ Dynamic Regulation & Trigger Log:</div>
                <table style="width:100%; border-collapse:collapse; text-align:left;">
                    <thead>
                        <tr style="color:#64748b; font-size:11px; text-transform:uppercase;">
                            <th style="padding:6px 12px;">Time</th>
                            <th style="padding:6px 12px;">Altitude</th>
                            <th style="padding:6px 12px;">TLOD Target</th>
                            <th style="padding:6px 12px;">Measured FPS</th>
                            <th style="padding:6px 12px;">Trigger Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                        {event_rows}
                    </tbody>
                </table>
            </div>
            """
        else:
            events_table_html = ""

        smart_lod_section = f"""
        <div class="chart-box" style="padding: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:8px;">
                <div class="chart-title" style="margin-bottom:0;">⚡ Smart LOD Trigger Analysis & Step Efficiency</div>
                <div style="font-size:12px; color:#06b6d4; font-weight:bold;">Dynamic MSFS Regulation</div>
            </div>
            <div style="overflow-x:auto;">
                <table style="width:100%; border-collapse:collapse; font-size:13px; text-align:left;">
                    <thead>
                        <tr style="border-bottom:1px solid #334155; color:#94a3b8; font-size:11px; text-transform:uppercase;">
                            <th style="padding:8px 12px;">Threshold / Transition</th>
                            <th style="padding:8px 12px;">TLOD Step</th>
                            <th style="padding:8px 12px;">FPS Delta (Gain/Loss)</th>
                            <th style="padding:8px 12px;">MainThread Delta (ms)</th>
                            <th style="padding:8px 12px;">Benefit & Real Impact</th>
                        </tr>
                    </thead>
                    <tbody>
                        {delta_rows}
                    </tbody>
                </table>
            </div>
            {events_table_html}
        </div>
        """

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
                <div class="chart-title" style="margin-bottom:0;">Flight Phases Analysis, Altitude Steps & Ground/LOD Impacts</div>
                <div style="font-size:12px; color:#94a3b8;">AutoFPS Cloud Quality: <span style="color:#38bdf8; font-weight:bold;">{cloud_status}</span></div>
            </div>
            <div style="overflow-x:auto;">
                <table style="width:100%; border-collapse:collapse; font-size:13px; text-align:left;">
                    <thead>
                        <tr style="border-bottom:1px solid #334155; color:#94a3b8; font-size:11px; text-transform:uppercase;">
                            <th style="padding:8px 12px;">Flight Phase</th>
                            <th style="padding:8px 12px;">Altitude (AGL)</th>
                            <th style="padding:8px 12px;">Avg TLOD</th>
                            <th style="padding:8px 12px;">Avg OLOD</th>
                            <th style="padding:8px 12px;">Avg FPS</th>
                            <th style="padding:8px 12px;">CPU MainThread</th>
                            <th style="padding:8px 12px;">Behavior & Impact</th>
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
    profile_section = generate_graphics_profile_section(session_info)

    # Format KPI Cards
    if is_fg_used and avg_base_fps != "N/A":
        card_fps_title = "Average FPS (Frame Gen)"
        card_fps_val = f'{avg_fps} <span style="font-size:16px;">FPS</span> <span style="font-size:15px; color:#38bdf8; font-weight:normal;">({avg_base_fps} base)</span>'
        card_fps_sub = f"Peak: {max_fps} FPS ({max_base_fps} base) • Min: {min_fps} FPS ({min_base_fps} base)"
    else:
        card_fps_title = "Average FPS (Native)"
        card_fps_val = f'{avg_fps} <span style="font-size:16px;">FPS</span>'
        card_fps_sub = f"Peak: {max_fps} FPS • Min: {min_fps} FPS"

    card_mt_title = "Average CPU MainThread"
    card_mt_val = f'{avg_mt} <span style="font-size:16px;">ms</span>'
    card_mt_sub = f"Best: {min_mt} ms • Peak: {max_mt} ms"

    if avg_msfs_vram_gb:
        card_vram_title = "Average GPU VRAM (MSFS / Total)"
        card_vram_val = f'{avg_msfs_vram_gb} <span style="font-size:16px;">GB MSFS</span> <span style="font-size:14px; color:#38bdf8; font-weight:normal;">({avg_vram_gb} GB Rig)</span>'
        card_vram_sub = f"MSFS Peak: {peak_msfs_vram_gb} GB • Rig GPU Total Peak: {peak_vram_gb} GB ({peak_vram_pct}% of {total_vram_gb} GB)"
    else:
        card_vram_title = "Average GPU VRAM"
        card_vram_val = f'{avg_vram_gb} <span style="font-size:16px;">GB</span>'
        card_vram_sub = f"Peak: {peak_vram_gb} GB ({peak_vram_pct}% of {total_vram_gb} GB) • Min: {min_vram_gb} GB"

    card_ram_title = "Average MSFS RAM (Physical)"
    card_ram_val = f'{avg_ram_gb} <span style="font-size:16px;">GB</span>'
    card_ram_sub = f"Peak: {peak_ram_gb} GB • Min: {min_ram_gb} GB"

    card_commit_title = "Average Committed RAM"
    card_commit_val = f'{avg_commit_gb} <span style="font-size:16px;">GB</span>'
    card_commit_sub = f"Peak: {peak_commit_gb} GB • Min: {min_commit_gb} GB"

    card_power_title = "Average GPU Power"
    card_power_val = f'{avg_power} <span style="font-size:16px;">W</span>'
    card_power_sub = f"Peak: {peak_power} W • Min: {min_power} W"

    dep_hdr = session_info.get('dep') or 'DEP'
    arr_hdr = session_info.get('arr') or 'ARR'
    route_hdr_title = f"{dep_hdr} ➔ {arr_hdr}"

    # Build Events Timeline section
    events_table_section = ""
    if flight_events:
        event_rows = ""
        for ev in flight_events:
            alt_disp = f"{int(ev['alt']):,} ft" if ev.get('alt') is not None else "--"
            event_rows += f"""
            <tr style="border-bottom:1px solid rgba(255,255,255,0.05); font-size:13px;">
                <td style="padding:10px 12px; color:#94a3b8; font-family:monospace; font-weight:bold;">{ev['time']}</td>
                <td style="padding:10px 12px;">
                    <span style="display:inline-block; padding:3px 8px; border-radius:6px; font-size:10px; font-weight:800; background:#1e293b; color:{ev['badge_color']}; border:1px solid rgba(51, 65, 85, 0.6);">{ev['badge']}</span>
                </td>
                <td style="padding:10px 12px; color:#f8fafc; font-weight:bold;">{ev['label']}</td>
                <td style="padding:10px 12px; color:#06b6d4; font-family:monospace;">{alt_disp}</td>
            </tr>
            """
        events_table_section = f"""
        <div class="chart-box" style="padding: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:8px;">
                <div class="chart-title" style="margin-bottom:0;">Dynamic Flight Events, Transitions & Pause Timeline</div>
                <div style="font-size:12px; color:#94a3b8;">Recorded changes during session ({len(flight_events)} event(s))</div>
            </div>
            <div style="overflow-x:auto;">
                <table style="width:100%; border-collapse:collapse; font-size:13px; text-align:left;">
                    <thead>
                        <tr style="border-bottom:1px solid #334155; color:#94a3b8; font-size:11px; text-transform:uppercase;">
                            <th style="padding:8px 12px;">Time</th>
                            <th style="padding:8px 12px;">Event Type</th>
                            <th style="padding:8px 12px;">Transition / Setting</th>
                            <th style="padding:8px 12px;">Altitude AGL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {event_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

    tot_pause = session_info.get('total_paused_sec', 0)
    pause_str = session_info.get('total_paused_str', '00:00')
    if tot_pause > 0:
        time_display_full = f"{session_info['duration']} (Active) • {pause_str} (Paused)"
        hdr_duration_sub = f"Flight recorded on {session_info['start_time']} • Active Flight: {session_info['duration']} • Paused: {pause_str}"
    else:
        time_display_full = session_info['duration']
        hdr_duration_sub = f"Flight recorded on {session_info['start_time']} • Monitoring Duration: {session_info['duration']}"

    is_vr_flight = session_info.get('has_vr') or any(s.get('is_vr') for s in samples)
    vr_badge_html = '<span class="badge" style="background:#0284c7;">VR HEADSET</span>' if is_vr_flight else '<span class="badge" style="background:#334155;">2D DESKTOP</span>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SceneryX Telemetry Report - {route_hdr_title} ({session_info['start_time']})</title>
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
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.6px;
            text-transform: uppercase;
            color: #ffffff;
            border: none;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
            white-space: nowrap;
            line-height: 1.2;
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
                <h1 style="margin:0 0 6px 0; font-size:24px; font-weight:800; letter-spacing:0.5px; text-transform:uppercase;">SCENERYX FLIGHT TELEMETRY REPORT</h1>
                <div style="color:#94a3b8; font-size:13px;">{hdr_duration_sub}</div>
            </div>
            <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                {vr_badge_html}
                <span class="badge" style="background:{net_badge_bg};">{net_badge_text}</span>
                <span class="badge" style="background:{lod_badge_bg};">{lod_badge_text}</span>
                <span class="badge" style="background:{badge_bg};">{badge_text}</span>
            </div>
        </div>

        <!-- CONTEXTUAL FLIGHT HEADER (Aircraft, Route, Mode, Monitoring Duration) -->
        <div style="background:#0f172a; border:1px solid #1e293b; border-radius:16px; padding:20px 24px; margin-bottom:24px; display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:20px;">
            <div>
                <div style="color:#64748b; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.8px;">Aircraft</div>
                <div style="color:#f8fafc; font-weight:800; font-size:17px; margin-top:4px;">{aircraft_display}</div>
            </div>
            <div>
                <div style="color:#64748b; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.8px;">Route / Origin</div>
                <div style="color:#38bdf8; font-weight:800; font-size:17px; margin-top:4px;">{route_display}</div>
            </div>
            <div>
                <div style="color:#64748b; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.8px;">SceneryX Flight Mode</div>
                <div style="color:{mode_color}; font-weight:800; font-size:17px; margin-top:4px;">{mode_display}</div>
            </div>
            <div>
                <div style="color:#64748b; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.8px;">Monitoring Time</div>
                <div style="color:#f8fafc; font-weight:800; font-size:17px; margin-top:4px; font-family:monospace;">{time_display_full}</div>
            </div>
        </div>

        <!-- ACTIVE GRAPHICS PROFILE & CALIBRATION -->
        {profile_section}

        <!-- EXPERT TEXTUAL DIAGNOSTIC -->
        {narrative_section}

        <!-- ALTITUDE STEPS & LOD IMPACTS -->
        {milestones_section}

        <!-- SMART LOD TRIGGER & STEP ANALYSIS -->
        {smart_lod_section}

        <!-- DYNAMIC FLIGHT EVENTS & TRANSITIONS TIMELINE -->
        {events_table_section}

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
            <div class="chart-title">1. Smoothness & Latency: Displayed FPS vs MainThread (ms)</div>
            <div style="height: 320px;">
                <canvas id="fpsChart"></canvas>
            </div>
        </div>

        <!-- GRAPH 2 : VRAM & RAM MSFS -->
        <div class="chart-box">
            <div class="chart-title">2. Memory Footprint: GPU VRAM & MSFS RAM over flight (MB)</div>
            <div style="height: 320px;">
                <canvas id="perfChart"></canvas>
            </div>
        </div>

        <!-- GRAPH 3 : Altitude & TLOD -->
        <div class="chart-box">
            <div class="chart-title">3. Flight Profile & Dynamics: AGL Altitude (ft) and Terrain LOD (TLOD)</div>
            <div style="height: 300px;">
                <canvas id="lodChart"></canvas>
            </div>
        </div>

        <!-- GRAPH 4 : Rolling Cache & Disk Read -->
        <div class="chart-box">
            <div class="chart-title">4. Streaming & Rolling Cache: MSFS Cache / Disk Read Throughput (Mbps)</div>
            <div style="height: 260px;">
                <canvas id="ioChart"></canvas>
            </div>
        </div>

        <div style="text-align:center; color:#64748b; font-size:12px; margin-top:24px;">
            Source file: {csv_path}
        </div>
    </div>

    <script>
        const times = {json.dumps(times)};
        const vrIntervals = {json.dumps(vr_intervals)};
        const pauseIntervals = {json.dumps(pause_intervals)};
        const chartEvents = {json.dumps(flight_events)};

        // Universal Chart.js annotation plugin for VR bands, pause intervals, and event markers
        const flightAnnotationsPlugin = {{
            id: 'flightAnnotations',
            beforeDraw(chart) {{
                const {{ ctx, chartArea, scales }} = chart;
                if (!chartArea || !scales.x) return;
                const {{ top, bottom, left, right }} = chartArea;
                const x = scales.x;

                // Draw VR shaded intervals
                vrIntervals.forEach(iv => {{
                    const startX = Math.max(left, x.getPixelForValue(iv.startIdx));
                    const endX = Math.min(right, x.getPixelForValue(iv.endIdx));
                    if (endX > startX) {{
                        ctx.save();
                        ctx.fillStyle = 'rgba(56, 189, 248, 0.07)';
                        ctx.fillRect(startX, top, endX - startX, bottom - top);
                        ctx.restore();
                    }}
                }});

                // Draw Pause shaded intervals
                pauseIntervals.forEach(iv => {{
                    const startX = Math.max(left, x.getPixelForValue(iv.startIdx));
                    const endX = Math.min(right, x.getPixelForValue(iv.endIdx));
                    if (endX > startX) {{
                        ctx.save();
                        ctx.fillStyle = 'rgba(234, 179, 8, 0.14)';
                        ctx.fillRect(startX, top, endX - startX, bottom - top);
                        ctx.restore();
                    }}
                }});
            }},
            afterDraw(chart) {{
                const {{ ctx, chartArea, scales }} = chart;
                if (!chartArea || !scales.x) return;
                const {{ top, bottom, left, right }} = chartArea;
                const x = scales.x;

                chartEvents.forEach(ev => {{
                    if (ev.idx === undefined || ev.idx < 0) return;
                    const posX = x.getPixelForValue(ev.idx);
                    if (posX >= left && posX <= right) {{
                        ctx.save();
                        ctx.beginPath();
                        ctx.setLineDash([4, 4]);
                        ctx.strokeStyle = ev.color || '#94a3b8';
                        ctx.lineWidth = 1;
                        ctx.moveTo(posX, top);
                        ctx.lineTo(posX, bottom);
                        ctx.stroke();

                        ctx.setLineDash([]);
                        ctx.font = 'bold 9px sans-serif';
                        const textW = ctx.measureText(ev.label).width;
                        const bw = textW + 8;
                        const bh = 15;
                        const bx = Math.min(right - bw, Math.max(left, posX - bw / 2));
                        const by = top + 3;

                        ctx.fillStyle = '#0f172a';
                        ctx.fillRect(bx, by, bw, bh);
                        ctx.strokeStyle = ev.color || 'rgba(51, 65, 85, 0.6)';
                        ctx.lineWidth = 1;
                        ctx.strokeRect(bx, by, bw, bh);

                        ctx.fillStyle = '#f8fafc';
                        ctx.fillText(ev.label, bx + 4, by + 10);
                        ctx.restore();
                    }}
                }});
            }}
        }};
        Chart.register(flightAnnotationsPlugin);

        // 1. FPS & MainThread Chart
        new Chart(document.getElementById('fpsChart').getContext('2d'), {{
            type: 'line',
            data: {{
                labels: times,
                datasets: [
                    {{
                        label: 'Displayed FPS',
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
                    }},
                    {f'''{{
                        label: 'Simulation Rate (x)',
                        data: {json.dumps(sim_rate_vals)},
                        borderColor: '#eab308',
                        borderWidth: 1.5,
                        borderDash: [3, 3],
                        stepped: true,
                        yAxisID: 'yRate',
                        pointRadius: 0
                    }},''' if has_sim_compression else ''}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ title: {{ display: true, text: 'Elapsed Time', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8', maxTicksLimit: 12 }} }},
                    yFps: {{ type: 'linear', position: 'left', title: {{ display: true, text: 'FPS', color: '#10b981' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#10b981' }} }},
                    yMs: {{ type: 'linear', position: 'right', title: {{ display: true, text: 'MainThread (ms)', color: '#f59e0b' }}, grid: {{ drawOnChartArea: false }}, ticks: {{ color: '#f59e0b' }} }},
                    {f'''yRate: {{ type: 'linear', position: 'right', min: 1, max: 8, title: {{ display: true, text: 'Sim Rate (x)', color: '#eab308' }}, grid: {{ drawOnChartArea: false }}, ticks: {{ color: '#eab308', stepSize: 1 }} }},''' if has_sim_compression else ''}
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
                        label: 'Rig GPU VRAM Total Used (MB)',
                        data: {json.dumps(vram_vals)},
                        borderColor: '#38bdf8',
                        backgroundColor: 'rgba(56, 189, 248, 0.1)',
                        borderWidth: 2,
                        tension: 0.2,
                        fill: true,
                        pointRadius: 0
                    }},
                    {f'''{{
                        label: 'MSFS 2024 Dedicated VRAM (MB)',
                        data: {json.dumps(msfs_vram_vals)},
                        borderColor: '#06b6d4',
                        borderWidth: 1.8,
                        borderDash: [5, 5],
                        tension: 0.2,
                        pointRadius: 0
                    }},''' if has_msfs_vram else ''}
                    {{
                        label: 'MSFS Physical RAM (MB)',
                        data: {json.dumps(msfs_ram_vals)},
                        borderColor: '#a855f7',
                        borderWidth: 2,
                        tension: 0.2,
                        pointRadius: 0
                    }},
                    {{
                        label: 'MSFS Committed RAM (MB)',
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
                    x: {{ title: {{ display: true, text: 'Elapsed Time', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8', maxTicksLimit: 12 }} }},
                    y: {{ title: {{ display: true, text: 'Memory (MB)', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8' }} }}
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
                        label: 'AGL Altitude (ft)',
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
                        data: {json.dumps(tlod_vals)},
                        borderColor: '#ec4899',
                        borderWidth: 2,
                        tension: 0.2,
                        yAxisID: 'yLod',
                        pointRadius: 0
                    }},
                    {f'''{{
                        label: 'Objects LOD (OLOD)',
                        data: {json.dumps(olod_vals)},
                        borderColor: '#a855f7',
                        borderWidth: 2,
                        borderDash: [4, 4],
                        tension: 0.2,
                        yAxisID: 'yLod',
                        pointRadius: 0
                    }},''' if has_olod else ''}
                    {{
                        label: '⚡ Smart LOD Trigger',
                        data: {json.dumps(smart_triggers)},
                        borderColor: '#38bdf8',
                        backgroundColor: '#38bdf8',
                        pointBackgroundColor: '#ffffff',
                        pointBorderColor: '#38bdf8',
                        pointBorderWidth: 2.5,
                        pointRadius: 6,
                        pointHoverRadius: 9,
                        pointStyle: 'rectRot',
                        showLine: false,
                        yAxisID: 'yLod'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ title: {{ display: true, text: 'Elapsed Time', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8', maxTicksLimit: 12 }} }},
                    yAlt: {{ type: 'linear', position: 'left', title: {{ display: true, text: 'AGL Altitude (ft)', color: '#06b6d4' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#06b6d4' }} }},
                    yLod: {{ type: 'linear', position: 'right', title: {{ display: true, text: 'LOD (TLOD / OLOD)', color: '#ec4899' }}, grid: {{ drawOnChartArea: false }}, ticks: {{ color: '#ec4899' }} }}
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
                        label: 'Cache / Disk Read Speed (Mbps)',
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
                    x: {{ title: {{ display: true, text: 'Elapsed Time', color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8', maxTicksLimit: 12 }} }},
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


def recover_orphan_benchmarks(benchmarks_dir=None):
    """
    Scans the benchmarks directory for CSV logs that do not have a matching HTML report
    (e.g. due to simulator crash, sudden exit, or power interruption).
    Reconstructs the telemetry samples and generates the missing HTML benchmark report.
    Returns a list of paths to newly generated reports.
    """
    if benchmarks_dir is None:
        benchmarks_dir = get_benchmarks_directory()

    if not os.path.exists(benchmarks_dir):
        return []

    recovered = []
    try:
        csv_files = [f for f in os.listdir(benchmarks_dir) if f.startswith('benchmark_') and f.endswith('.csv')]
    except Exception as e:
        print(f"[Telemetry] Error scanning benchmarks dir: {e}")
        return []

    for csv_file in csv_files:
        csv_path = os.path.join(benchmarks_dir, csv_file)
        html_file = csv_file[:-4] + '.html'
        html_path = os.path.join(benchmarks_dir, html_file)

        if os.path.exists(html_path):
            continue

        try:
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.strip() for line in f if line.strip()]

            # Require header + at least 6 telemetry data rows (same standard as live sessions)
            if len(lines) < 7:
                continue

            reader = csv.DictReader(lines)
            samples = []
            pause_events = []
            total_paused_sec = 0.0
            was_paused = False
            pause_start_time = 0.0

            for row in reader:
                try:
                    el_sec = float(row.get('elapsed_sec') or 0.0)
                except Exception:
                    el_sec = 0.0

                t_str = row.get('time_str') or format_time_delta(el_sec)

                def _safe_float(val, default=None):
                    try:
                        return float(val) if val is not None and str(val).strip() != '' else default
                    except Exception:
                        return default

                def _safe_int(val, default=None):
                    try:
                        return int(float(val)) if val is not None and str(val).strip() != '' else default
                    except Exception:
                        return default

                def _safe_bool(val):
                    return str(val or '').strip().lower() in ('true', '1', 'yes')

                cur_paused = _safe_bool(row.get('is_paused'))
                if cur_paused and not was_paused:
                    was_paused = True
                    pause_start_time = el_sec
                    pause_events.append({
                        "event": "pause_start",
                        "elapsed_sec": el_sec,
                        "time_str": t_str
                    })
                elif not cur_paused and was_paused:
                    was_paused = False
                    p_dur = max(0.0, el_sec - pause_start_time)
                    total_paused_sec += p_dur
                    pause_events.append({
                        "event": "pause_resume",
                        "elapsed_sec": el_sec,
                        "time_str": t_str,
                        "duration_sec": round(p_dur, 1)
                    })

                s_dict = {
                    'timestamp': row.get('timestamp', ''),
                    'elapsed': el_sec,
                    'elapsed_sec': el_sec,
                    'time_str': t_str,
                    'mode': row.get('mode', 'BASELINE STANDARD (All sceneries active)'),
                    'disp_fps': _safe_int(row.get('displayed_fps')),
                    'base_fps': _safe_int(row.get('base_fps')),
                    'main_thread_ms': _safe_float(row.get('main_thread_ms')),
                    'tlod': _safe_float(row.get('tlod')),
                    'olod': _safe_float(row.get('olod')),
                    'agl': _safe_float(row.get('agl_ft')),
                    'agl_ft': _safe_float(row.get('agl_ft')),
                    'fpm': _safe_float(row.get('fpm')),
                    'fg_mode': row.get('fg_mode', ''),
                    'cache_read_mbps': _safe_float(row.get('cache_read_mbps'), 0.0),
                    'cache_read_mbs': _safe_float(row.get('cache_read_mbs'), 0.0),
                    'vram_used': _safe_float(row.get('vram_used_mb'), 0.0),
                    'vram_used_mb': _safe_float(row.get('vram_used_mb'), 0.0),
                    'vram_total': _safe_float(row.get('vram_total_mb'), 16376.0),
                    'vram_total_mb': _safe_float(row.get('vram_total_mb'), 16376.0),
                    'vram_pct': _safe_float(row.get('vram_pct'), 0.0),
                    'msfs_vram': _safe_float(row.get('msfs_vram_mb'), 0.0),
                    'gpu_util': _safe_float(row.get('gpu_util_pct'), 0.0),
                    'gpu_util_pct': _safe_float(row.get('gpu_util_pct'), 0.0),
                    'gpu_temp': _safe_float(row.get('gpu_temp_c'), 0.0),
                    'gpu_power': _safe_float(row.get('gpu_power_w'), 0.0),
                    'gpu_clock': _safe_float(row.get('gpu_clock_mhz'), 0.0),
                    'gpu_bus': _safe_float(row.get('gpu_mem_bus_pct'), 0.0),
                    'msfs_ram': _safe_float(row.get('msfs_ram_mb'), 0.0),
                    'msfs_ram_mb': _safe_float(row.get('msfs_ram_mb'), 0.0),
                    'msfs_commit': _safe_float(row.get('msfs_commit_mb'), 0.0),
                    'msfs_commit_mb': _safe_float(row.get('msfs_commit_mb'), 0.0),
                    'sys_ram_used': _safe_float(row.get('sys_ram_used_mb'), 0.0),
                    'sys_ram_total': _safe_float(row.get('sys_ram_total_mb'), 0.0),
                    'sim_rate': _safe_float(row.get('sim_rate'), 1.0),
                    'is_vr': _safe_bool(row.get('is_vr')),
                    'is_paused': cur_paused
                }
                samples.append(s_dict)

            if len(samples) < 6:
                continue

            stem = csv_file[:-4]
            raw_core = stem[10:] if stem.startswith('benchmark_') else stem
            parts = raw_core.split('_')
            start_date_str = ""
            dep = "DEP"
            arr = "ARR"
            aircraft = "Aircraft"

            if len(parts) >= 3 and len(parts[-2]) == 10 and '-' in parts[-2]:
                time_token = parts[-1].replace('-', ':')
                date_token = parts[-2]
                start_date_str = f"{date_token} {time_token}"
                prefix_tokens = parts[:-2]
            else:
                prefix_tokens = parts

            if len(prefix_tokens) >= 2 and prefix_tokens[0].lower() != 'baseline':
                dep = prefix_tokens[0]
                arr = prefix_tokens[1]
                if len(prefix_tokens) > 2:
                    aircraft = "_".join(prefix_tokens[2:])
            elif len(prefix_tokens) >= 1 and prefix_tokens[0].lower() == 'baseline':
                dep = "BASELINE"
                arr = "SESSION"
                aircraft = "MSFS"

            if not start_date_str:
                start_date_str = samples[0].get('timestamp') or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            first_mode = samples[0].get('mode') or 'BASELINE STANDARD (All sceneries active)'
            is_corridor = 'CORRIDOR' in first_mode.upper() or 'SCENERYX' in first_mode.upper()
            max_elapsed = max((s.get('elapsed_sec', 0.0) for s in samples), default=0.0)

            session_info = {
                'mode_str': first_mode,
                'is_corridor': is_corridor,
                'disabled_count': 0,
                'start_time': start_date_str,
                'duration': format_time_delta(round(max_elapsed, 1)),
                'aircraft': aircraft,
                'route_display': f"{dep} ➔ {arr}" if dep != arr else dep,
                'mode_display': first_mode,
                'dep': dep,
                'arr': arr,
                'dep_name': '',
                'arr_name': '',
                'detection_source': 'Orphan Recovery / Auto-saved log',
                'autofps_config': {},
                'autofps_active': False,
                'cloud_events': 'Nominal',
                'smart_lod': {},
                'network': get_flight_network_info(),
                'graphics_profile': get_flight_graphics_profile(),
                'pause_events': pause_events,
                'total_paused_sec': round(total_paused_sec, 1),
                'total_paused_str': format_time_delta(round(total_paused_sec, 1)),
                'has_vr': any(s.get('is_vr') for s in samples),
                'max_sim_rate': max(((s.get('sim_rate') or 1.0) for s in samples), default=1.0)
            }

            rep_path = generate_html_report(csv_path, session_info, samples)
            if rep_path and os.path.exists(rep_path):
                print(f"[Telemetry] Successfully recovered orphan benchmark: {os.path.basename(rep_path)}")
                recovered.append(rep_path)
        except Exception as err:
            print(f"[Telemetry] Error recovering orphan benchmark {csv_file}: {err}")

    return recovered


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
    print(f" Detected Mode  : {mode_str}")
    print(f" CSV Log        : {csv_path}")
    print(f" Telemetry      : FPS, MainThread, TLOD, Cache Read (Mbps), VRAM, RAM, GPU (W)")
    print("=" * 84)
    print(" Waiting for flight simulator...")

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
                    print("\n>> MSFS 2024 DETECTED AND ACTIVE! Starting live tracking...\n")

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

                cur_tlod, cur_olod, _ = get_current_lod_data(autofps)
                tlod = cur_tlod
                olod = cur_olod

                if sc_connected and sc_data.get("base_fps") is not None:
                    disp_fps = sc_data.get('displayed_fps')
                    base_fps = sc_data.get('base_fps')
                    main_thread_ms = sc_data.get('frame_time_ms')
                    agl_ft = sc_data.get('agl_ft')
                    fpm = sc_data.get('fpm')
                    fg_mode = 'DLSSG (2X)' if (disp_fps and base_fps and disp_fps > base_fps) else 'NATIVE'
                else:
                    disp_fps = autofps.get('displayed_fps') if autofps else None
                    base_fps = autofps.get('base_fps') if autofps else None
                    main_thread_ms = autofps.get('main_thread_ms') if autofps else None
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
        print("               FLIGHT SUMMARY & PRO PERFORMANCE BENCHMARK")
        print("=" * 80)
        print(f" Tested Mode      : {mode_str}")
        print(f" Recorded Duration: {total_duration} ({len(samples)} samples)")
        print("-" * 80)
        print(f" Average FPS      : {avg_fps_str}  (Average MainThread: {avg_mt_str})")
        print(f" Peak GPU VRAM    : {peak_vram:,.0f} MB  (Average: {avg_vram:,.0f} MB)")
        print(f" Peak MSFS RAM    : {peak_msfs_ram:,.0f} MB  (Average: {avg_ram:,.0f} MB)")
        print(f" Max Committed RAM: {peak_msfs_commit:,.0f} MB")
        print("=" * 80)

        last_sc = SIMCONNECT_CLIENT.get_data() if SIMCONNECT_CLIENT else {}
        final_lat = last_sc.get('lat')
        final_lon = last_sc.get('lon')
        final_ground = last_sc.get('on_ground', False)
        ctx = resolve_flight_context(final_lat, final_lon, final_ground)
        final_aircraft = last_sc.get('aircraft') or "Generic aircraft"
        cloud_status = check_autofps_cloud_events()
        autofps_cfg = get_autofps_config()
        autofps_active = is_autofps_active()

        smart_lod_info = {}
        try:
            from flight_lod_controller import get_smart_lod_controller
            s_ctrl = get_smart_lod_controller()
            if s_ctrl:
                smart_lod_info = s_ctrl.get_status()
                smart_lod_info['events'] = s_ctrl.get_trigger_events()
        except Exception:
            pass

        session_info = {
            'mode_str': mode_str,
            'is_corridor': is_corridor and (dis_count > 0),
            'disabled_count': dis_count if is_corridor else 0,
            'start_time': timestamp_str,
            'duration': total_duration,
            'aircraft': final_aircraft,
            'route_display': ctx['route_display'],
            'mode_display': ctx['mode_display'],
            'autofps_config': autofps_cfg,
            'autofps_active': autofps_active,
            'cloud_events': cloud_status,
            'smart_lod': smart_lod_info,
            'network': get_flight_network_info(),
            'graphics_profile': get_flight_graphics_profile()
        }
        html_file = generate_html_report(csv_path, session_info, samples)
        if html_file and os.path.exists(html_file):
            print(f"\n📊 Full graphical report generated: {html_file}")
            print("Opening report in your browser...")
            webbrowser.open(f"file:///{os.path.abspath(html_file)}")
        print(f"📄 Full CSV log: {csv_path}\n")
    else:
        print("\nNo data recorded (MSFS was not active).")


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
            "is_paused": False,
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

    def start(self, flight_name="flight", dep=None, arr=None, aircraft=None):
        if self.is_running:
            return {"status": "already_running", "flight_name": self.current_flight_name}
        self._stop_event.clear()
        self.is_running = True
        self.current_flight_name = flight_name or f"{dep or 'DEP'}_{arr or 'ARR'}_{aircraft or 'Flight'}"
        self.thread = threading.Thread(target=self._worker, args=(flight_name, dep, arr, aircraft), daemon=True)
        self.thread.start()
        return {"status": "started", "flight_name": self.current_flight_name}

    def stop(self):
        if not self.is_running:
            return {"status": "not_running", "report_path": self.last_report_path}
        self._stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10.0)
        self.is_running = False
        self.latest_telemetry["is_tracking"] = False
        self.latest_telemetry["is_paused"] = False
        self.latest_telemetry["elapsed_sec"] = 0
        self.latest_telemetry["elapsed_str"] = "00:00"
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
        telemetry["is_paused"] = sc_data.get("is_paused", False)
        if not self.is_running:
            telemetry["elapsed_sec"] = 0
            telemetry["elapsed_str"] = "00:00"
        telemetry["msfs_active"] = msfs is not None
        telemetry["simconnect_connected"] = sc_connected
        telemetry["autofps_active"] = is_autofps_active()

        # Context (Appareil, Route, Mode)
        lat = sc_data.get("lat")
        lon = sc_data.get("lon")
        on_ground = sc_data.get("on_ground", False)
        ctx = resolve_flight_context(lat, lon, on_ground)
        telemetry["aircraft"] = sc_data.get("aircraft") or "Not detected"
        route_text = ctx["route_display"]
        if telemetry.get("is_paused") and self.is_running:
            route_text = f"[PAUSED] {route_text}"
        telemetry["route_display"] = route_text
        telemetry["mode_display"] = ctx["mode_display"]

        if gpu:
            telemetry["vram_used_mb"] = gpu.get("vram_used_mb", 0)
            telemetry["vram_total_mb"] = gpu.get("vram_total_mb", 16376)
            telemetry["vram_pct"] = gpu.get("vram_pct", 0)
            telemetry["gpu_power_w"] = gpu.get("gpu_power_w", 0)
            telemetry["gpu_util_pct"] = gpu.get("gpu_util_pct", 0)
            telemetry["gpu_temp_c"] = gpu.get("gpu_temp_c", 0)

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
            telemetry["msfs_cpu_pct"] = msfs.get("cpu_pct", 0)

        telemetry["agl_ft"] = sc_data.get("agl_ft")
        telemetry["on_ground"] = sc_data.get("on_ground", False if (sc_data.get("agl_ft") is not None and sc_data.get("agl_ft") > 80) else True)
        global _last_telemetry_cache
        _last_telemetry_cache = telemetry
        return telemetry


    def _worker(self, flight_name, dep, arr, aircraft):
        benchmarks_dir = get_benchmarks_directory()
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        mode_str, is_corridor, cur_dep, cur_arr, dis_count, prof_slug = get_sceneryx_flight_mode()

        autofps_cfg = get_autofps_config()
        autofps_is_active = is_autofps_active()

        # Priorité SimBrief initiale si départ/arrivée non spécifiés ou placeholders
        initial_dep = dep or cur_dep
        initial_arr = arr or cur_arr
        if not initial_dep or initial_dep == 'DEP' or not initial_arr or initial_arr == 'ARR':
            sb_init = get_simbrief_flight_plan()
            if sb_init:
                s_orig = sb_init.get('origin', {}).get('icao')
                s_dest = sb_init.get('destination', {}).get('icao')
                if s_orig and (not initial_dep or initial_dep == 'DEP'):
                    initial_dep = s_orig
                if s_dest and (not initial_arr or initial_arr == 'ARR'):
                    initial_arr = s_dest

        initial_aircraft_slug = sanitize_aircraft_slug(aircraft)
        prefix = f"{initial_dep or 'DEP'}_{initial_arr or 'ARR'}_{initial_aircraft_slug}"
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
                'sys_ram_used_mb', 'sys_ram_total_mb',
                'msfs_vram_mb', 'sim_rate', 'is_vr', 'is_paused'
            ])

        samples = []
        start_time = time.time()
        last_worker_time = start_time
        elapsed_active_sec = 0.0
        total_paused_sec = 0.0
        was_paused = False
        pause_start_tick = None
        pause_events = []
        last_read_bytes = None
        last_tick_time = None
        had_msfs = False
        had_flight = False
        no_flight_ticks = 0

        # Suivi GPS continu et détection appareil
        first_valid_gps = None
        first_ground_gps = None
        last_valid_gps = None
        last_ground_gps = None
        best_detected_aircraft = None

        while not self._stop_event.is_set():
            now_tick = time.time()
            dt = now_tick - last_worker_time
            last_worker_time = now_tick
            if dt < 0 or dt > 5.0:
                dt = 0.5

            msfs = get_msfs_process()
            gpu = get_nvidia_gpu_telemetry()
            sys_ram_used, sys_ram_total = get_system_ram()
            autofps = get_latest_autofps_data()

            sc_data = SIMCONNECT_CLIENT.get_data() if SIMCONNECT_CLIENT else {}
            sc_connected = sc_data.get("connected", False)
            in_flight = sc_data.get("in_flight", False)
            is_paused = sc_data.get("is_paused", False)
            detected_aircraft = sc_data.get("aircraft")
            if detected_aircraft and detected_aircraft not in ("Not detected", "None", ""):
                best_detected_aircraft = detected_aircraft

            cur_tlod, cur_olod, _ = get_current_lod_data(autofps)
            tlod = cur_tlod
            olod = cur_olod

            if sc_connected and sc_data.get("base_fps") is not None:
                disp_fps = sc_data.get('displayed_fps')
                base_fps = sc_data.get('base_fps')
                mt_ms = sc_data.get('frame_time_ms')
                agl = sc_data.get('agl_ft')
                fpm = sc_data.get('fpm')
                fg_mode = 'DLSSG (2X)' if (disp_fps and base_fps and disp_fps > base_fps) else 'NATIVE'
            else:
                disp_fps = (autofps.get('displayed_fps') or autofps.get('disp_fps')) if autofps else None
                base_fps = autofps.get('base_fps') if autofps else None
                mt_ms = autofps.get('main_thread_ms') if autofps else None
                agl = autofps.get('agl_ft') if autofps else None
                fpm = autofps.get('fpm') if autofps else None
                fg_mode = autofps.get('fg_mode') if autofps else None

            # Track simulator & flight lifecycle
            if msfs is not None or sc_connected:
                had_msfs = True

            if (sc_connected and (in_flight or (detected_aircraft and detected_aircraft != "Not detected"))) or (agl is not None and agl > 0):
                had_flight = True

            # -----------------------------------------------------------------
            # AUTO-STOP CONDITIONS
            # 1. MSFS quit completely
            # 2. Player quit flight (returned to main menu) - ONLY when NOT paused!
            # -----------------------------------------------------------------
            if had_msfs and (msfs is None and not sc_connected):
                print("[Telemetry] Auto-stopping: MSFS process completely closed.")
                break

            if had_flight:
                if not sc_connected:
                    print("[Telemetry] Auto-stopping: SimConnect disconnected after flight.")
                    break
                elif is_paused and (detected_aircraft and detected_aircraft != "Not detected"):
                    # SIMULATOR IS PAUSED during active flight: NEVER auto-stop during pause!
                    no_flight_ticks = 0
                elif not in_flight or not detected_aircraft or detected_aircraft == "Not detected":
                    no_flight_ticks += 1
                    if no_flight_ticks >= 12:  # 6 seconds grace period
                        print("[Telemetry] Auto-stopping: Flight ended / returned to main menu.")
                        break
                else:
                    no_flight_ticks = 0

            # Accumulation du temps de vol réel actif (uniquement hors pause)
            if not is_paused:
                elapsed_active_sec += dt
            elapsed = round(elapsed_active_sec, 1)
            time_formatted = format_time_delta(elapsed)

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

            # Simulation Rate & VR mode tracking
            sim_rate = sc_data.get("sim_rate", 1.0) or 1.0
            is_vr = False
            try:
                import flight_memory_engine
                mem = flight_memory_engine.get_memory_engine()
                if mem.is_attached:
                    is_vr = mem.is_vr_active()
            except Exception:
                is_vr = False

            v_used = gpu.get('vram_used_mb', 0)
            v_total = gpu.get('vram_total_mb', 16376)
            v_pct = gpu.get('vram_pct', 0)

            msfs_vram = msfs.get('vram_mb', 0.0) if msfs else 0.0

            # Realtime Context
            lat = sc_data.get("lat")
            lon = sc_data.get("lon")
            on_ground = sc_data.get("on_ground", False)

            # Enregistrement des coordonnées GPS valides (uniquement hors pause et > 0.001)
            if not is_paused and lat is not None and lon is not None and (abs(lat) > 0.001 or abs(lon) > 0.001):
                if first_valid_gps is None:
                    first_valid_gps = (lat, lon)
                last_valid_gps = (lat, lon)

                if on_ground or (agl is not None and agl < 200):
                    if first_ground_gps is None:
                        first_ground_gps = (lat, lon)
                    last_ground_gps = (lat, lon)

            ctx = resolve_flight_context(lat, lon, on_ground)
            final_detected_aircraft = best_detected_aircraft or detected_aircraft or aircraft or "Not detected"

            route_str = ctx["route_display"]
            if is_paused:
                route_str = f"[PAUSED] {route_str}"

            self.latest_telemetry = {
                "is_tracking": True,
                "is_paused": is_paused,
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
                "aircraft": final_detected_aircraft,
                "route_display": route_str,
                "mode_display": ctx["mode_display"],
                "autofps_active": is_autofps_active(),
                "sim_rate": sim_rate,
                "is_vr": is_vr
            }

            if is_paused:
                if not was_paused:
                    was_paused = True
                    pause_start_tick = time.time()
                    pause_events.append({
                        "elapsed_at_pause": elapsed,
                        "time_str": time_formatted,
                        "start_iso": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "duration_sec": 0,
                        "duration_str": "00:00"
                    })
                    # Log pause start row in CSV so timeline records the transition
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
                        sys_ram_used, sys_ram_total,
                        msfs_vram, sim_rate, int(is_vr), 1
                    ]
                    try:
                        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                            csv.writer(f).writerow(row)
                    except Exception:
                        pass
                self._stop_event.wait(0.5)
                continue
            else:
                if was_paused and pause_start_tick is not None:
                    p_dur = max(0.0, time.time() - pause_start_tick)
                    total_paused_sec += p_dur
                    if pause_events:
                        pause_events[-1]["duration_sec"] = round(p_dur, 1)
                        pause_events[-1]["duration_str"] = format_time_delta(round(p_dur, 1))
                    was_paused = False
                    pause_start_tick = None

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
                sys_ram_used, sys_ram_total,
                msfs_vram, sim_rate, int(is_vr), 0
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
                'sys_ram_total': sys_ram_total,
                'lat': lat,
                'lon': lon,
                'sim_rate': sim_rate,
                'is_vr': is_vr,
                'is_paused': False
            })

            self._stop_event.wait(0.5)

        if samples and len(samples) >= 6:
            last_sc = SIMCONNECT_CLIENT.get_data() if SIMCONNECT_CLIENT else {}
            final_aircraft = best_detected_aircraft or last_sc.get('aircraft') or aircraft or "Aircraft not detected"

            # -------------------------------------------------------------
            # DÉTECTION FINALE DU DÉPART ET DE L'ARRIVÉE
            # Si SimBrief existe, on le récupère. Sinon, détection GPS à l'arrêt.
            # -------------------------------------------------------------
            final_dep, final_arr, dep_name, arr_name, source = detect_flight_airports(
                samples=samples,
                first_valid_gps=first_valid_gps,
                last_valid_gps=last_valid_gps,
                first_ground_gps=first_ground_gps,
                last_ground_gps=last_ground_gps,
                initial_dep=initial_dep,
                initial_arr=initial_arr
            )

            final_aircraft_slug = sanitize_aircraft_slug(final_aircraft)
            final_prefix = f"{final_dep}_{final_arr}_{final_aircraft_slug}"
            final_csv_filename = f"benchmark_{final_prefix}_{timestamp_str}.csv"
            final_csv_path = os.path.join(benchmarks_dir, final_csv_filename)

            # Renommer le fichier CSV avec les aéroports réels et l'appareil détecté
            if csv_path != final_csv_path and os.path.exists(csv_path):
                try:
                    if os.path.exists(final_csv_path):
                        os.remove(final_csv_path)
                    os.rename(csv_path, final_csv_path)
                    csv_path = final_csv_path
                    self.current_csv_path = final_csv_path
                    print(f"[Telemetry] Benchmark CSV finalized as: {final_csv_filename} ({source})")
                except Exception as e:
                    print(f"[Telemetry] Could not rename benchmark CSV: {e}")

            # Route & mode formatting
            if dep_name and arr_name:
                route_display = f"{final_dep} ({dep_name}) ➔ {final_arr} ({arr_name})"
            elif dep_name:
                route_display = f"{final_dep} ({dep_name}) ➔ {final_arr}"
            elif arr_name:
                route_display = f"{final_dep} ➔ {final_arr} ({arr_name})"
            else:
                route_display = f"{final_dep} ➔ {final_arr}"

            opt_state = detect_route_optimization_state()
            if is_corridor and dis_count > 0:
                mode_disp = ctx.get('mode_display', mode_str)
            elif "SimBrief" in source or opt_state.get('has_simbrief'):
                mode_disp = "BASELINE (SimBrief OFP • No Scenery Isolation)"
            else:
                mode_disp = f"BASELINE ({source})"

            cloud_status = check_autofps_cloud_events()

            smart_lod_info = {}
            try:
                from flight_lod_controller import get_smart_lod_controller
                s_ctrl = get_smart_lod_controller()
                if s_ctrl:
                    smart_lod_info = s_ctrl.get_status()
                    smart_lod_info['events'] = s_ctrl.get_trigger_events()
            except Exception:
                pass

            session_info = {
                'mode_str': mode_str,
                'is_corridor': is_corridor and (dis_count > 0),
                'disabled_count': dis_count if is_corridor else 0,
                'start_time': timestamp_str,
                'duration': format_time_delta(round(elapsed_active_sec, 1)),
                'aircraft': final_aircraft,
                'route_display': route_display,
                'mode_display': mode_disp,
                'dep': final_dep,
                'arr': final_arr,
                'dep_name': dep_name,
                'arr_name': arr_name,
                'detection_source': source,
                'autofps_config': autofps_cfg,
                'autofps_active': autofps_is_active or is_autofps_active(),
                'cloud_events': cloud_status,
                'smart_lod': smart_lod_info,
                'network': get_flight_network_info(),
                'graphics_profile': get_flight_graphics_profile(),
                'pause_events': pause_events,
                'total_paused_sec': round(total_paused_sec, 1),
                'total_paused_str': format_time_delta(round(total_paused_sec, 1)),
                'has_vr': any(s.get('is_vr') for s in samples),
                'max_sim_rate': max(((s.get('sim_rate') or 1.0) for s in samples), default=1.0)
            }
            try:
                html_file = generate_html_report(csv_path, session_info, samples)
                self.last_report_path = html_file
            except Exception as e:
                print(f"[Telemetry] Error generating HTML report: {e}")
        else:
            try:
                if os.path.exists(csv_path):
                    os.remove(csv_path)
            except Exception:
                pass
            self.current_csv_path = None

        self.is_running = False
        self.latest_telemetry["is_tracking"] = False
        self.latest_telemetry["is_paused"] = False
        self.latest_telemetry["elapsed_sec"] = 0
        self.latest_telemetry["elapsed_str"] = "00:00"


BLACKBOX = BlackboxSession()

import atexit

def _on_perf_tracker_exit():
    if BLACKBOX.is_running:
        try:
            print("[Telemetry] Application exit detected, auto-saving blackbox report...")
            BLACKBOX.stop()
        except Exception:
            pass

atexit.register(_on_perf_tracker_exit)

if __name__ == '__main__':
    main()
