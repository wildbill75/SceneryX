#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SceneryX Flight Performance Tracker (Standalone Telemetry Benchmark)
Mesure et journalise en temps réel la VRAM GPU, la RAM de MSFS et les performances système
pour comparer les vols avec et sans le mode Flight Plan de SceneryX.
"""

import os
import sys
import time
import json
import csv
import ctypes
import ctypes.wintypes
import subprocess
import webbrowser
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

def get_system_ram():
    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    total_mb = round(stat.ullTotalPhys / (1024 * 1024))
    used_mb = round((stat.ullTotalPhys - stat.ullAvailPhys) / (1024 * 1024))
    return used_mb, total_mb

def get_msfs_process():
    try:
        cmd = ['tasklist', '/FI', 'IMAGENAME eq FlightSimulator*', '/FO', 'CSV', '/NH']
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        for line in out.strip().splitlines():
            if 'FlightSimulator' in line:
                parts = [p.strip('"') for p in line.split('","')]
                name = parts[0]
                pid = int(parts[1])
                PROCESS_QUERY_INFORMATION = 0x0400
                PROCESS_VM_READ = 0x0010
                hProcess = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
                if hProcess:
                    pmc = PROCESS_MEMORY_COUNTERS_EX()
                    pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
                    ctypes.windll.psapi.GetProcessMemoryInfo(hProcess, ctypes.byref(pmc), pmc.cb)
                    ctypes.windll.kernel32.CloseHandle(hProcess)
                    return {
                        'name': name,
                        'pid': pid,
                        'ram_mb': round(pmc.WorkingSetSize / (1024 * 1024), 1),
                        'commit_mb': round(pmc.PrivateUsage / (1024 * 1024), 1),
                        'peak_ram_mb': round(pmc.PeakWorkingSetSize / (1024 * 1024), 1)
                    }
    except Exception:
        pass
    return None

def get_nvidia_gpu_telemetry():
    try:
        cmd = [
            'nvidia-smi',
            '--query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu',
            '--format=csv,noheader,nounits'
        ]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        line = out.strip().splitlines()[0]
        used, total, util, temp = [int(v.strip()) for v in line.split(',')]
        return {
            'vram_used_mb': used,
            'vram_total_mb': total,
            'vram_pct': round((used / total) * 100, 1),
            'gpu_util_pct': util,
            'gpu_temp_c': temp
        }
    except Exception:
        return {
            'vram_used_mb': 0,
            'vram_total_mb': 0,
            'vram_pct': 0.0,
            'gpu_util_pct': 0,
            'gpu_temp_c': 0
        }

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
                    alts = fm.get('alternates', [])
                    alt_str = f" [Alts: {','.join(alts)}]" if alts else ""
                    return f"SCENERYX CORRIDOR ({dep} ➔ {arr}{alt_str} | {dis} scènes isolées)", True, dep, arr, dis
        except Exception:
            pass
    return "BASELINE STANDARD (Toutes scènes actives)", False, "", "", 0

def format_time_delta(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}h {m:02d}m {s:02d}s"
    return f"{m:02d}m {s:02d}s"

def generate_html_report(csv_path, session_info, samples):
    html_path = csv_path.replace('.csv', '.html')
    os.makedirs(os.path.dirname(os.path.abspath(html_path)), exist_ok=True)
    
    times = [s['elapsed'] for s in samples]
    vram_vals = [s['vram_used'] for s in samples]
    msfs_ram_vals = [s['msfs_ram'] for s in samples]
    msfs_commit_vals = [s['msfs_commit'] for s in samples]
    gpu_util_vals = [s['gpu_util'] for s in samples]

    peak_vram = max(vram_vals) if vram_vals else 0
    avg_vram = round(sum(vram_vals) / len(vram_vals), 1) if vram_vals else 0
    total_vram = samples[0]['vram_total'] if samples else 16376
    peak_vram_pct = round((peak_vram / total_vram) * 100, 1) if total_vram else 0

    peak_ram = max(msfs_ram_vals) if msfs_ram_vals else 0
    avg_ram = round(sum(msfs_ram_vals) / len(msfs_ram_vals), 1) if msfs_ram_vals else 0

    peak_commit = max(msfs_commit_vals) if msfs_commit_vals else 0
    avg_commit = round(sum(msfs_commit_vals) / len(msfs_commit_vals), 1) if msfs_commit_vals else 0

    mode_title = session_info['mode_str']
    is_corridor = session_info['is_corridor']
    badge_color = "#06b6d4" if is_corridor else "#f59e0b"
    badge_text = "OPTIMISÉ SCENERYX" if is_corridor else "BASELINE STANDARD"

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
            background: rgba(6, 182, 212, 0.15);
            color: {badge_color};
            border: 1px solid {badge_color};
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
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
                <h1 style="margin:0 0 6px 0; font-size:24px;">Rapport de Télémétrie de Vol SceneryX</h1>
                <div style="color:#94a3b8; font-size:13px;">Vol enregistré le {session_info['start_time']} • Durée : {session_info['duration']}</div>
            </div>
            <div>
                <span class="badge">{badge_text}</span>
            </div>
        </div>

        <div style="background:#1e293b; padding:12px 18px; border-radius:12px; margin-bottom:24px; font-size:13px; font-weight:600;">
            Configuration du vol : <span style="color:#38bdf8;">{mode_title}</span>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-title">VRAM GPU Maximale</div>
                <div class="card-val" style="color: {'#ef4444' if peak_vram_pct > 88 else '#38bdf8'};">{peak_vram:,.0f} Mo</div>
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
                <div class="card-title">Échantillons Enregistrés</div>
                <div class="card-val" style="color:#a855f7;">{len(samples)}</div>
                <div class="card-sub">Fréquence : toutes les 2 secondes</div>
            </div>
        </div>

        <div class="chart-box">
            <div class="chart-title">Évolution de la VRAM GPU & de la RAM MSFS au fil du vol (Mo)</div>
            <div style="height: 380px;">
                <canvas id="perfChart"></canvas>
            </div>
        </div>

        <div style="text-align:center; color:#64748b; font-size:12px; margin-top:24px;">
            Fichier source : {csv_path}
        </div>
    </div>

    <script>
        const ctx = document.getElementById('perfChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(times)},
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
                    x: {{
                        title: {{ display: true, text: 'Temps écoulé', color: '#94a3b8' }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }},
                        ticks: {{ color: '#94a3b8', maxTicksLimit: 12 }}
                    }},
                    y: {{
                        title: {{ display: true, text: 'Mémoire (Mo)', color: '#94a3b8' }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }},
                        ticks: {{ color: '#94a3b8' }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        labels: {{ color: '#f8fafc', font: {{ weight: 'bold' }} }}
                    }}
                }}
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
    mode_str, is_corridor, dep, arr, dis_count = get_sceneryx_flight_mode()

    prefix = f"corridor_{dep}_{arr}" if is_corridor else "baseline_full"
    csv_filename = f"benchmark_{prefix}_{timestamp_str}.csv"
    csv_path = os.path.join(benchmarks_dir, csv_filename)

    # Initialize CSV File
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'timestamp', 'elapsed_sec', 'time_str', 'mode',
            'vram_used_mb', 'vram_total_mb', 'vram_pct',
            'gpu_util_pct', 'gpu_temp_c',
            'msfs_ram_mb', 'msfs_commit_mb',
            'sys_ram_used_mb', 'sys_ram_total_mb'
        ])

    print("=" * 76)
    print("           SCENERYX - FLIGHT PERFORMANCE TRACKER (STANDALONE)")
    print("=" * 76)
    print(f" Mode détecté : {mode_str}")
    print(f" Journal CSV   : {csv_path}")
    print("=" * 76)
    print(" En attente du simulateur de vol...")

    samples = []
    start_time = None
    sample_index = 0

    peak_vram = 0
    min_vram = 999999
    peak_msfs_ram = 0
    peak_msfs_commit = 0

    try:
        while True:
            msfs = get_msfs_process()
            gpu = get_nvidia_gpu_telemetry()
            sys_ram_used, sys_ram_total = get_system_ram()

            now_dt = datetime.now()
            now_iso = now_dt.strftime("%Y-%m-%d %H:%M:%S")

            if msfs:
                if start_time is None:
                    start_time = time.time()
                    print("\n>> MSFS 2024 DÉTECTÉ ET ACTIF ! Démarrage de l'enregistrement en direct...\n")

                elapsed = round(time.time() - start_time, 1)
                time_formatted = format_time_delta(elapsed)
                sample_index += 1

                # Update Stats
                vram_used = gpu['vram_used_mb']
                if vram_used > peak_vram: peak_vram = vram_used
                if vram_used < min_vram and vram_used > 0: min_vram = vram_used

                msfs_ram = msfs['ram_mb']
                if msfs_ram > peak_msfs_ram: peak_msfs_ram = msfs_ram

                msfs_commit = msfs['commit_mb']
                if msfs_commit > peak_msfs_commit: peak_msfs_commit = msfs_commit

                # Append to memory sample list
                samples.append({
                    'elapsed': time_formatted,
                    'vram_used': vram_used,
                    'vram_total': gpu['vram_total_mb'],
                    'msfs_ram': msfs_ram,
                    'msfs_commit': msfs_commit,
                    'gpu_util': gpu['gpu_util_pct']
                })

                # Write to CSV
                with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        now_iso, elapsed, time_formatted, mode_str,
                        vram_used, gpu['vram_total_mb'], gpu['vram_pct'],
                        gpu['gpu_util_pct'], gpu['gpu_temp_c'],
                        msfs_ram, msfs_commit,
                        sys_ram_used, sys_ram_total
                    ])

                # Live Console Display (ANSI in-place rewrite)
                sys.stdout.write(
                    f"\r[{time_formatted}] "
                    f"VRAM: {vram_used:,.0f} Mo ({gpu['vram_pct']}%) [Peak: {peak_vram:,.0f} Mo] | "
                    f"GPU: {gpu['gpu_util_pct']}% ({gpu['gpu_temp_c']}°C) | "
                    f"MSFS RAM: {round(msfs_ram/1024, 1)} Go (Commit: {round(msfs_commit/1024, 1)} Go) | "
                    f"Échantillons: {sample_index}"
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

        print("\n" + "=" * 76)
        print("               RÉSUMÉ DU VOL & BENCHMARK DE PERFORMANCE")
        print("=" * 76)
        print(f" Mode Testé       : {mode_str}")
        print(f" Durée Enregistrée: {total_duration} ({len(samples)} échantillons)")
        print("-" * 76)
        print(f" VRAM GPU Crête   : {peak_vram:,.0f} Mo  (Moyenne : {avg_vram:,.0f} Mo)")
        print(f" RAM MSFS Crête   : {peak_msfs_ram:,.0f} Mo  (Moyenne : {avg_ram:,.0f} Mo)")
        print(f" RAM Allouée Max  : {peak_msfs_commit:,.0f} Mo")
        print("=" * 76)

        session_info = {
            'mode_str': mode_str,
            'is_corridor': is_corridor,
            'start_time': timestamp_str,
            'duration': total_duration
        }
        html_file = generate_html_report(csv_path, session_info, samples)
        if html_file and os.path.exists(html_file):
            print(f"\n📊 Rapport graphique généré : {html_file}")
            print("Ouverture du rapport dans votre navigateur...")
            webbrowser.open(f"file:///{os.path.abspath(html_file)}")
        print(f"📄 Journal CSV complet : {csv_path}\n")
    else:
        print("\nAucune donnée n'a été enregistrée (MSFS n'était pas actif).")

if __name__ == '__main__':
    main()
