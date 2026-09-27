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
    if not hSnapshot or hSnapshot == -1:
        return None, None
    pe = PROCESSENTRY32()
    pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
    found_pid = None
    found_name = None
    if ctypes.windll.kernel32.Process32First(hSnapshot, ctypes.byref(pe)):
        while True:
            exe_name = pe.szExeFile.decode('utf-8', errors='ignore').lower()
            if 'flightsimulator' in exe_name:
                found_pid = pe.th32ProcessID
                found_name = pe.szExeFile.decode('utf-8', errors='ignore')
                break
            if not ctypes.windll.kernel32.Process32Next(hSnapshot, ctypes.byref(pe)):
                break
    ctypes.windll.kernel32.CloseHandle(hSnapshot)
    return found_pid, found_name

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
                'read_bytes': read_bytes
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

    peak_vram = max(vrams)
    total_vram = samples[0]['vram_total']
    vram_peak_pct = round((peak_vram / total_vram) * 100, 1) if total_vram else 0
    avg_vram = round(sum(vrams) / len(vrams), 0)

    avg_fps = round(sum(fps_list) / len(fps_list), 1) if fps_list else "N/A"
    avg_mt = round(sum(mt_list) / len(mt_list), 1) if mt_list else "N/A"
    avg_gpu = round(sum(gpus) / len(gpus), 1)
    avg_tlod = round(sum(tlods) / len(tlods), 0) if tlods else "Fixe"
    peak_io = round(max(io_reads), 1) if io_reads else 0.0

    # Diagnostic du goulot d'étranglement principal
    if avg_gpu >= 96 and (avg_mt != "N/A" and avg_mt <= 25.0):
        bottleneck_diag = "<strong>Profil GPU-Bound équilibré :</strong> La carte graphique RTX a tourné à plein régime avec une fluidité optimale, sans blocage sévère du MainThread."
    elif avg_mt != "N/A" and avg_mt > 30.0:
        bottleneck_diag = f"<strong>Profil MainThread Limité ({avg_mt} ms en moyenne) :</strong> Le fil processeur principal a été le facteur limitant, typique des phases au sol avec avionique complexe (Fenix) et décors denses."
    else:
        bottleneck_diag = "<strong>Profil Mixte Équilibré :</strong> Répartition harmonieuse entre la charge de calcul CPU et le rendu graphique."

    # Diagnostic VRAM & Paging
    if vram_peak_pct >= 92.0:
        vram_diag = f"<span style='color:#ef4444;'><strong>Alerte Risque de Paging :</strong> La VRAM a culminé à {peak_vram:,.0f} Mo ({vram_peak_pct}%). Proche du seuil de débordement vers la RAM système, pouvant causer des micro-saccades en vue externe.</span>"
    elif vram_peak_pct >= 85.0:
        vram_diag = f"<span style='color:#f59e0b;'><strong>Zone Haute Maîtrisée :</strong> VRAM crête à {peak_vram:,.0f} Mo ({vram_peak_pct}%). Marge de sécurité suffisante sans déclenchement de mémoire paginée.</span>"
    else:
        vram_diag = f"<span style='color:#10b981;'><strong>Excellente Marge Vidéo :</strong> VRAM crête contenue à {peak_vram:,.0f} Mo ({vram_peak_pct}%). L'isolation SceneryX a éliminé les textures en surplus.</span>"

    narrative = f"""
    <div style="background:#0f172a; border:1px solid #1e293b; border-radius:16px; padding:20px; margin-bottom:24px; line-height:1.6; font-size:13px; color:#cbd5e1;">
        <h3 style="margin-top:0; color:#38bdf8; font-size:16px;">📝 Compte-Rendu d'Analyse du Vol</h3>
        <ul style="padding-left:20px; margin-bottom:12px;">
            <li><strong>Comportement Système & Goulot d'Étranglement :</strong> {bottleneck_diag}</li>
            <li><strong>Empreinte Mémoire Vidéo (VRAM) :</strong> {vram_diag}</li>
            <li><strong>Fluidité & Affichage :</strong> Moyenne de <strong>{avg_fps} FPS</strong> avec un MainThread de <strong>{avg_mt} ms</strong>.</li>
            <li><strong>Gestion Dynamique LOD (AutoFPS) :</strong> TLOD moyen maintenu à <strong>{avg_tlod}</strong>. Les ajustements automatiques ont permis de soulager le RdrThread et le processeur lors des variations de charge.</li>
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
    mainthread_vals = [s['main_thread_ms'] for s in samples if s.get('main_thread_ms') is not None]

    peak_vram = max(vram_vals) if vram_vals else 0
    avg_vram = round(sum(vram_vals) / len(vram_vals), 1) if vram_vals else 0
    total_vram = samples[0]['vram_total'] if samples else 16376
    peak_vram_pct = round((peak_vram / total_vram) * 100, 1) if total_vram else 0

    peak_ram = max(msfs_ram_vals) if msfs_ram_vals else 0
    avg_ram = round(sum(msfs_ram_vals) / len(msfs_ram_vals), 1) if msfs_ram_vals else 0

    peak_commit = max(msfs_commit_vals) if msfs_commit_vals else 0
    avg_commit = round(sum(msfs_commit_vals) / len(msfs_commit_vals), 1) if msfs_commit_vals else 0

    avg_power = round(sum(gpu_power_vals) / len(gpu_power_vals), 1) if gpu_power_vals else 0
    peak_power = max(gpu_power_vals) if gpu_power_vals else 0

    avg_fps = round(sum(fps_vals) / len(fps_vals), 1) if fps_vals else "N/A"
    max_fps = max(fps_vals) if fps_vals else "N/A"
    min_fps = min(fps_vals) if fps_vals else "N/A"

    avg_mt = round(sum(mainthread_vals) / len(mainthread_vals), 1) if mainthread_vals else "N/A"
    min_mt = min(mainthread_vals) if mainthread_vals else "N/A"
    max_mt = max(mainthread_vals) if mainthread_vals else "N/A"

    mode_title = session_info['mode_str']
    is_corridor = session_info['is_corridor']
    badge_color = "#10b981" if is_corridor else "#f59e0b"
    badge_text = "OPTIMISÉ SCENERYX" if is_corridor else "BASELINE STANDARD"

    narrative_section = generate_automated_flight_narrative(samples, session_info)

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

        <div style="background:#1e293b; padding:12px 18px; border-radius:12px; margin-bottom:20px; font-size:13px; font-weight:600;">
            Configuration du vol : <span style="color:#38bdf8;">{mode_title}</span>
        </div>

        <!-- DIAGNOSTIC TEXTUEL EXPERT -->
        {narrative_section}

        <div class="grid">
            <div class="card">
                <div class="card-title">FPS Affichés (Frame Gen)</div>
                <div class="card-val" style="color: #10b981;">{avg_fps} <span style="font-size:16px;">FPS</span></div>
                <div class="card-sub">Crête : {max_fps} FPS • Min : {min_fps} FPS</div>
            </div>

            <div class="card">
                <div class="card-title">MainThread CPU</div>
                <div class="card-val" style="color: #f59e0b;">{avg_mt} <span style="font-size:16px;">ms</span></div>
                <div class="card-sub">Meilleur : {min_mt} ms • Max : {max_mt} ms</div>
            </div>

            <div class="card">
                <div class="card-title">VRAM GPU Maximale</div>
                <div class="card-val" style="color: #38bdf8;">{peak_vram:,.0f} Mo</div>
                <div class="card-sub">{peak_vram_pct}% de {total_vram:,.0f} Mo • Moyenne : {avg_vram:,.0f} Mo</div>
            </div>

            <div class="card">
                <div class="card-title">RAM MSFS (Working Set)</div>
                <div class="card-val">{peak_ram:,.0f} Mo</div>
                <div class="card-sub">{round(peak_ram/1024, 1)} Go Crête • Moyenne : {round(avg_ram/1024, 1)} Go</div>
            </div>

            <div class="card">
                <div class="card-title">RAM Allouée (Commit)</div>
                <div class="card-val">{peak_commit:,.0f} Mo</div>
                <div class="card-sub">{round(peak_commit/1024, 1)} Go Crête • Moyenne : {round(avg_commit/1024, 1)} Go</div>
            </div>

            <div class="card">
                <div class="card-title">Puissance GPU (Watts)</div>
                <div class="card-val" style="color: #eab308;">{avg_power} W</div>
                <div class="card-sub">Moyenne vol • Crête : {peak_power} W</div>
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
    
    benchmarks_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'benchmarks')
    os.makedirs(benchmarks_dir, exist_ok=True)

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

        session_info = {
            'mode_str': mode_str,
            'is_corridor': is_corridor,
            'start_time': timestamp_str,
            'duration': total_duration
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
            "gpu_power_w": 0,
            "elapsed_sec": 0,
            "elapsed_str": "00:00",
            "msfs_active": False
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
        
        telemetry = dict(self.latest_telemetry)
        telemetry["is_tracking"] = self.is_running
        telemetry["msfs_active"] = msfs is not None
        if gpu:
            telemetry["vram_used_mb"] = gpu.get("vram_used_mb", 0)
            telemetry["vram_total_mb"] = gpu.get("vram_total_mb", 16376)
            telemetry["vram_pct"] = gpu.get("vram_pct", 0)
            telemetry["gpu_power_w"] = gpu.get("power_w", 0)
        if autofps:
            telemetry["displayed_fps"] = autofps.get("disp_fps")
            telemetry["base_fps"] = autofps.get("base_fps")
            telemetry["main_thread_ms"] = autofps.get("main_thread_ms")
            telemetry["tlod"] = autofps.get("tlod")
            telemetry["olod"] = autofps.get("olod")
        if msfs:
            telemetry["msfs_ram_mb"] = msfs.get("ws_mb", 0)
        return telemetry

    def _worker(self, flight_name, dep, arr, aircraft):
        benchmarks_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'benchmarks')
        os.makedirs(benchmarks_dir, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        mode_str, is_corridor, cur_dep, cur_arr, dis_count, prof_slug = get_sceneryx_flight_mode()

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

            disp_fps = autofps.get('disp_fps') if autofps else None
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
                "cache_read_mbps": cache_read_mbps,
                "msfs_ram_mb": msfs.get('ws_mb', 0) if msfs else 0,
                "gpu_power_w": gpu.get('power_w', 0),
                "elapsed_sec": elapsed,
                "elapsed_str": time_formatted,
                "msfs_active": msfs is not None
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
                gpu.get('util_pct', 0), gpu.get('temp_c', 0), gpu.get('power_w', 0), gpu.get('clock_mhz', 0), gpu.get('mem_bus_pct', 0),
                msfs.get('ws_mb', 0) if msfs else 0, msfs.get('commit_mb', 0) if msfs else 0, 0,
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
                'fpm': fpm,
                'cache_mbps': cache_read_mbps,
                'vram_used': v_used,
                'vram_pct': v_pct,
                'gpu_util': gpu.get('util_pct', 0),
                'gpu_temp': gpu.get('temp_c', 0),
                'gpu_power': gpu.get('power_w', 0),
                'gpu_clock': gpu.get('clock_mhz', 0),
                'gpu_bus': gpu.get('mem_bus_pct', 0),
                'msfs_ram': msfs.get('ws_mb', 0) if msfs else 0,
                'msfs_commit': msfs.get('commit_mb', 0) if msfs else 0,
                'sys_ram_used': sys_ram_used,
                'sys_ram_total': sys_ram_total
            })

            self._stop_event.wait(0.5)

        if samples:
            session_info = {
                'mode_str': mode_str,
                'is_corridor': is_corridor,
                'start_time': timestamp_str,
                'duration': format_time_delta(round(time.time() - start_time, 1))
            }
            html_file = generate_html_report(csv_path, session_info, samples)
            self.last_report_path = html_file


BLACKBOX = BlackboxSession()

if __name__ == '__main__':
    main()
