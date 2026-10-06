#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SceneryX Flight Bug Reporter & Diagnostic Engine
Module de capture d'incidents, traçage des erreurs (Stacktrace & Breadcrumbs),
anonymisation RGPD des chemins/identifiants, stockage local des incidents,
génération de bundle de diagnostic structuré et envoi direct / assisté.
Destinataire support : Bertrand Le Cabec <contact@sidestickpriority.com>
"""

import os
import sys
import time
import json
import traceback
import zipfile
import threading
import subprocess
import urllib.parse
import webbrowser
import hashlib
import uuid
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
import ctypes
from ctypes import wintypes
from PIL import Image

CONTACT_EMAIL = "contact@sidestickpriority.com"
RECIPIENT_NAME = "Bertrand Le Cabec"

# Dossier persistant pour l'archivage local des incidents
CRASH_REPORTS_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'SceneryX', 'crash_reports')
os.makedirs(CRASH_REPORTS_DIR, exist_ok=True)

# Verrou de synchronisation
_lock = threading.Lock()

# Ring Buffers pour logs et breadcrumbs
MAX_LOG_ENTRIES = 350
MAX_BREADCRUMBS = 60

_log_buffer: List[Dict[str, Any]] = []
_breadcrumb_buffer: List[Dict[str, Any]] = []
_last_exception: Optional[Dict[str, Any]] = None


def anonymize_text(text: str) -> str:
    """Remplace les chemins d'accès utilisateur et supprime les secrets éventuels."""
    if not text or not isinstance(text, str):
        return text or ""
    # Remplace C:\Users\NomUtilisateur\... par C:\Users\USER\...
    cleaned = re.sub(r'(?i)[a-zA-Z]:\\Users\\[^\\]+', r'C:\\Users\\USER', text)
    cleaned = re.sub(r'(?i)file:///[a-zA-Z]:/Users/[^/]+', r'file:///C:/Users/USER', cleaned)
    # Masque d'éventuels jetons ou clés d'API
    cleaned = re.sub(r'(?i)(token|password|secret|key|api_key)=([^\s&",]+)', r'\1=***REDACTED***', cleaned)
    return cleaned


def anonymize_data(obj: Any) -> Any:
    """Anonymise récursivement une structure de données (dict, list, str)."""
    if isinstance(obj, str):
        return anonymize_text(obj)
    elif isinstance(obj, dict):
        return {k: anonymize_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [anonymize_data(item) for item in obj]
    return obj


def get_anonymous_machine_id() -> str:
    """Génère un identifiant anonyme haché unique à la machine (non réversible)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as k:
            guid = winreg.QueryValueEx(k, "MachineGuid")[0]
            return f"SCX-ID-{hashlib.sha256(guid.encode('utf-8')).hexdigest()[:12].upper()}"
    except Exception:
        import platform
        node = platform.node() or "SCX_MACHINE"
        return f"SCX-ID-{hashlib.sha256(node.encode('utf-8')).hexdigest()[:12].upper()}"


def generate_incident_id() -> str:
    """Génère un identifiant d'incident unique et lisible (ex: SCX-20261006-F4D2)."""
    now_str = datetime.now().strftime("%Y%m%d")
    token = uuid.uuid4().hex[:4].upper()
    return f"SCX-{now_str}-{token}"


def get_privacy_settings() -> Dict[str, bool]:
    """Récupère les préférences de télémétrie et crash reporting depuis settings.json."""
    try:
        from scanner import get_settings
        st = get_settings()
        return {
            "auto_send_crash_reports": st.get("auto_send_crash_reports", True),
            "send_anonymous_telemetry": st.get("send_anonymous_telemetry", True)
        }
    except Exception:
        return {"auto_send_crash_reports": True, "send_anonymous_telemetry": True}


def save_privacy_settings(auto_send_crash_reports: bool, send_anonymous_telemetry: bool) -> bool:
    """Sauvegarde les préférences de télémétrie et crash reporting dans settings.json."""
    try:
        from scanner import get_settings, save_settings
        st = get_settings()
        st["auto_send_crash_reports"] = bool(auto_send_crash_reports)
        st["send_anonymous_telemetry"] = bool(send_anonymous_telemetry)
        save_settings(st)
        add_breadcrumb("SETTINGS", "Updated crash reporting & privacy preferences", {
            "auto_send_crash_reports": st["auto_send_crash_reports"],
            "send_anonymous_telemetry": st["send_anonymous_telemetry"]
        })
        return True
    except Exception as e:
        log_event("ERROR", f"Failed to save privacy settings: {e}")
        return False


def init_bug_reporter():
    """Initialise les intercepteurs globaux d'exceptions Python et l'enregistrement système."""
    def global_excepthook(exc_type, exc_value, exc_traceback):
        record_exception(exc_type, exc_value, exc_traceback, context="Unhandled Python Exception (Main Thread)")
        # Appel du hook système par défaut
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = global_excepthook

    if hasattr(threading, 'excepthook'):
        def threading_excepthook(args):
            record_exception(args.exc_type, args.exc_value, args.exc_traceback, context=f"Unhandled Thread Exception ({args.thread.name if args.thread else 'Unknown'})")
        threading.excepthook = threading_excepthook

    add_breadcrumb("SYSTEM", "SceneryX Bug Reporter & Diagnostic Engine initialized")


def log_event(level: str, message: str, details: Any = None):
    """Enregistre un événement dans le buffer circulaire de logs."""
    global _log_buffer
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "level": str(level).upper(),
        "message": anonymize_text(str(message))
    }
    if details:
        entry["details"] = anonymize_data(details)

    with _lock:
        _log_buffer.append(entry)
        if len(_log_buffer) > MAX_LOG_ENTRIES:
            _log_buffer.pop(0)


def add_breadcrumb(action: str, label: str, metadata: Optional[Dict[str, Any]] = None):
    """Enregistre une action utilisateur ou une étape clé dans le fil d'Ariane (Breadcrumbs)."""
    global _breadcrumb_buffer
    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "action": str(action).upper(),
        "label": anonymize_text(str(label))
    }
    if metadata:
        entry["metadata"] = anonymize_data(metadata)

    with _lock:
        _breadcrumb_buffer.append(entry)
        if len(_breadcrumb_buffer) > MAX_BREADCRUMBS:
            _breadcrumb_buffer.pop(0)


def record_exception(exc_type, exc_value, exc_tb, context: str = "Standard Exception"):
    """Capture une exception avec son extraction complète pour localisation immédiate du code."""
    global _last_exception

    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    formatted_tb = "".join(tb_lines)

    # Extraction du dernier frame suspect (le fichier et la ligne dans le projet)
    extracted = traceback.extract_tb(exc_tb)
    culprit_file = "Unknown"
    culprit_line = 0
    culprit_func = "Unknown"
    code_context = ""

    for frame in reversed(extracted):
        fn = os.path.basename(frame.filename)
        # Prioriser les fichiers du projet SceneryX
        if fn.endswith('.py') and not fn.startswith('<') and 'site-packages' not in frame.filename:
            culprit_file = fn
            culprit_line = frame.lineno
            culprit_func = frame.name
            code_context = frame.line
            break

    if culprit_file == "Unknown" and extracted:
        last_frame = extracted[-1]
        culprit_file = os.path.basename(last_frame.filename)
        culprit_line = last_frame.lineno
        culprit_func = last_frame.name
        code_context = last_frame.line

    incident_id = generate_incident_id()

    exc_data = {
        "incident_id": incident_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": getattr(exc_type, '__name__', str(exc_type)),
        "message": anonymize_text(str(exc_value)),
        "context": context,
        "culprit_file": culprit_file,
        "culprit_line": culprit_line,
        "culprit_func": culprit_func,
        "code_context": anonymize_text(str(code_context or '')),
        "traceback": anonymize_text(formatted_tb)
    }

    with _lock:
        _last_exception = exc_data

    log_event("ERROR", f"Exception captured in {culprit_file}:{culprit_line} ({exc_data['type']}): {exc_data['message']}")
    add_breadcrumb("EXCEPTION", f"{exc_data['type']} in {culprit_file}:{culprit_line}", {"message": exc_data['message']})

    # Sauvegarde automatique locale de l'incident si le paramètre privacy est actif
    privacy = get_privacy_settings()
    if privacy.get("auto_send_crash_reports", True):
        try:
            dump_file = os.path.join(CRASH_REPORTS_DIR, f"crash_{incident_id}.json")
            incident_payload = {
                "incident_id": incident_id,
                "created_at": datetime.now().isoformat(),
                "machine_id": get_anonymous_machine_id(),
                "exception": exc_data,
                "breadcrumbs": list(_breadcrumb_buffer)[-20:],
                "system": get_current_system_snapshot()
            }
            with open(dump_file, "w", encoding="utf-8") as f:
                json.dump(anonymize_data(incident_payload), f, indent=2, ensure_ascii=False)
            add_breadcrumb("CRASH_DUMP", f"Emergency crash dump saved: {os.path.basename(dump_file)}")
        except Exception as e:
            log_event("WARNING", f"Failed to save emergency crash dump: {e}")


def capture_window_screenshot() -> Optional[Image.Image]:
    """Capture d'écran native de la fenêtre SceneryX via Windows GDI (BitBlt/PrintWindow)."""
    try:
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        hwnd = user32.FindWindowW(None, "SceneryX")
        if not hwnd:
            hwnd = user32.GetDesktopWindow()

        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        w = max(100, rect.right - rect.left)
        h = max(100, rect.bottom - rect.top)

        hdc_win = user32.GetWindowDC(hwnd)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_win)
        hbm = gdi32.CreateCompatibleBitmap(hdc_win, w, h)
        gdi32.SelectObject(hdc_mem, hbm)

        printed = user32.PrintWindow(hwnd, hdc_mem, 2)
        if not printed:
            gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_win, 0, 0, 0x00CC0020)

        bmpinfo = (ctypes.c_byte * 40)()
        ctypes.c_uint32.from_buffer(bmpinfo, 0).value = 40
        ctypes.c_int32.from_buffer(bmpinfo, 4).value = w
        ctypes.c_int32.from_buffer(bmpinfo, 8).value = -h
        ctypes.c_uint16.from_buffer(bmpinfo, 12).value = 1
        ctypes.c_uint16.from_buffer(bmpinfo, 14).value = 32
        ctypes.c_uint32.from_buffer(bmpinfo, 16).value = 0

        buf = (ctypes.c_char * (w * h * 4))()
        gdi32.GetDIBits(hdc_mem, hbm, 0, h, buf, bmpinfo, 0)

        im = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1)
        rgb_im = im.convert('RGB')

        user32.ReleaseDC(hwnd, hdc_win)
        gdi32.DeleteDC(hdc_mem)
        gdi32.DeleteObject(hbm)

        return rgb_im
    except Exception as e:
        log_event("WARNING", f"Screenshot capture failed: {e}")
        return None


def get_current_system_snapshot() -> Dict[str, Any]:
    """Rassemble l'état actuel anonymisé de la machine, du simulateur et des profils."""
    snapshot: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "sceneryx_version": "v1.0.1",
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "machine_id": get_anonymous_machine_id()
    }

    # 1. Spécifications matérielles
    try:
        import flight_rig_optimizer
        diag = flight_rig_optimizer.get_full_rig_diagnostics()
        snapshot["hardware"] = diag.get("detected", {})
        snapshot["graphics_advisory"] = {
            "2d": diag.get("graphics_advisory_2d"),
            "vr": diag.get("graphics_advisory_vr")
        }
    except Exception as e:
        snapshot["hardware_error"] = str(e)

    # 2. Profil actif SceneryX
    try:
        import flight_rig_optimizer
        act_prof = flight_rig_optimizer.get_active_profile_snapshot()
        if act_prof:
            snapshot["active_profile"] = act_prof
    except Exception as e:
        snapshot["profile_error"] = str(e)

    # 3. Télémétrie de vol & SimConnect
    try:
        import flight_perf_tracker
        if hasattr(flight_perf_tracker, 'BLACKBOX'):
            data = flight_perf_tracker.BLACKBOX.get_telemetry()
            if data:
                snapshot["flight_telemetry"] = {
                    "is_tracking": data.get("is_tracking", False),
                    "msfs_active": data.get("msfs_active", False),
                    "simconnect_connected": data.get("simconnect_connected", False),
                    "aircraft": data.get("aircraft", "None"),
                    "route": data.get("route_display", "N/A"),
                    "mode": data.get("mode_display", "2D"),
                    "displayed_fps": data.get("displayed_fps", 0),
                    "base_fps": data.get("base_fps", 0),
                    "main_thread_ms": data.get("main_thread_ms", 0),
                    "tlod": data.get("tlod"),
                    "olod": data.get("olod")
                }
    except Exception as e:
        snapshot["telemetry_error"] = str(e)

    return anonymize_data(snapshot)


def generate_diagnostic_summary_markdown(user_description: str, category: str, incident_id: Optional[str] = None, exception_data: Optional[Dict[str, Any]] = None) -> str:
    """Génère le document diagnostic_summary.md spécialement architecturé pour l'assistance et l'analyse IA."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    exc = exception_data or _last_exception
    inc_id = incident_id or (exc.get('incident_id') if exc else generate_incident_id())

    lines = []
    lines.append("# SCENERYX ISSUE REPORT // DIAGNOSTIC SUMMARY")
    lines.append(f"**Incident ID :** `#{inc_id}`")
    lines.append(f"**Date & Time :** {now_str}")
    lines.append(f"**Category :** `{category}`")
    lines.append(f"**Anonymous Machine ID :** `{get_anonymous_machine_id()}`")
    lines.append(f"**Support Contact :** `{CONTACT_EMAIL}`\n")

    lines.append("## 1. User Description")
    clean_desc = anonymize_text(user_description.strip() if user_description else "*(No description provided)*")
    lines.append(f"> {clean_desc}\n")

    lines.append("## 2. Error Signature & Code Location")
    if exc:
        lines.append(f"- **Suspect File :** [`{exc['culprit_file']}`](file:///{exc['culprit_file']})")
        lines.append(f"- **Exact Line :** `Line {exc['culprit_line']}` in `{exc['culprit_func']}()`")
        lines.append(f"- **Exception :** `{exc['type']}: {exc['message']}`")
        if exc.get('code_context'):
            lines.append(f"- **Failing Instruction :** `{exc['code_context'].strip()}`")
        lines.append(f"- **Context :** {exc.get('context', 'Runtime execution error')}\n")

        lines.append("```python")
        lines.append("# --- CALLSTACK TRACE ---")
        lines.append(exc.get("traceback", "").strip())
        lines.append("```\n")
    else:
        lines.append("*No unhandled Python exception was intercepted during this session.*")
        lines.append("*(The issue is likely visual, timing, or configuration related).*\n")

    lines.append("## 3. Action Breadcrumbs (Recent Events)")
    with _lock:
        recent_crumbs = list(_breadcrumb_buffer)[-25:]

    if recent_crumbs:
        lines.append("| Time | Action | Event Details |")
        lines.append("| :--- | :--- | :--- |")
        for c in recent_crumbs:
            meta_str = f" `{json.dumps(c.get('metadata'))}`" if c.get('metadata') else ""
            lines.append(f"| {c['timestamp']} | **{c['action']}** | {c['label']}{meta_str} |")
        lines.append("")
    else:
        lines.append("*No breadcrumbs recorded in buffer.* \n")

    # Hardware & Telemetry
    lines.append("## 4. Hardware Environment & Telemetry")
    snapshot = get_current_system_snapshot()
    hw = snapshot.get("hardware", {})
    gpu = hw.get("gpu", {})
    cpu = hw.get("cpu", {})
    ram = hw.get("ram", {})
    storage = hw.get("storage", {})
    net = hw.get("network", {})
    vr = hw.get("vr_headset", {})
    dlss = hw.get("dlss", {})
    telem = snapshot.get("flight_telemetry", {})

    lines.append(f"- **GPU :** {gpu.get('name_simplified', 'Unknown')} ({gpu.get('vram_total_gb', 0)} GB VRAM) | Driver: `{gpu.get('driver_version')}` (Current: `{gpu.get('is_driver_current')}`)")
    lines.append(f"- **DLSS DLL :** `{dlss.get('version', 'Unknown')}` (Up to date: `{dlss.get('is_up_to_date')}`) | Re-BAR: `{gpu.get('is_rbar_active')}` | HAGS: `{hw.get('hags_active')}`")
    lines.append(f"- **CPU :** {cpu.get('name_simplified', 'Unknown')} ({cpu.get('cores', 0)}C / {cpu.get('threads', 0)}T)")
    lines.append(f"- **RAM :** {ram.get('total_gb', 0)} GB @ {ram.get('speed_mhz', 0)} MHz (XMP: `{ram.get('is_xmp_active')}`)")
    lines.append(f"- **MSFS Storage :** {storage.get('tier', 'SSD')} ({storage.get('free_gb', 0)} GB free / {storage.get('total_gb', 0)} GB)")
    lines.append(f"- **Network :** {net.get('link_speed_str', 'Active link')} | Ping: `{net.get('ping_ms', '--')} ms` (Wi-Fi: `{net.get('is_wifi')}`)")
    lines.append(f"- **VR Headset :** {vr.get('name', 'None detected')} (Active: `{vr.get('detected')}`, `{vr.get('refresh_rate_hz', 72)} Hz`)")
    if telem:
        lines.append(f"- **Active Flight :** Aircraft `{telem.get('aircraft')}`, Route `{telem.get('route')}`, Mode `{telem.get('mode')}`, FPS `{telem.get('displayed_fps')}`")

    lines.append("\n---")
    lines.append("*Generated by SceneryX Bug Reporter. Zero personal data or account credentials included.*")

    return "\n".join(lines)


def get_diagnostic_preview(user_description: str, category: str = "General") -> str:
    """Fournit un aperçu en lecture seule du rapport diagnostic avant soumission."""
    return generate_diagnostic_summary_markdown(user_description, category)


def build_bug_report_package(user_description: str, category: str = "General", include_screenshot: bool = True, include_logs: bool = True) -> Dict[str, Any]:
    """Compile diagnostic data, save incident JSON, write ZIP bundle on Desktop, open Explorer and prepare mail."""
    incident_id = generate_incident_id()
    report_zip_filename = f"SceneryX_BugReport_{incident_id}.zip"

    # 1. Target directory: User Desktop
    desktop_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
    if not os.path.exists(desktop_dir):
        desktop_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'SceneryX', 'Reports')
        os.makedirs(desktop_dir, exist_ok=True)

    zip_path = os.path.join(desktop_dir, report_zip_filename)

    # 2. Generate markdown summary
    summary_md = generate_diagnostic_summary_markdown(user_description, category, incident_id=incident_id)

    # 3. Capture screenshot
    screenshot_img = None
    if include_screenshot:
        screenshot_img = capture_window_screenshot()

    # 4. Save local incident JSON in persistent crash_reports/ directory
    try:
        local_incident_file = os.path.join(CRASH_REPORTS_DIR, f"incident_{incident_id}.json")
        incident_data = {
            "incident_id": incident_id,
            "created_at": datetime.now().isoformat(),
            "machine_id": get_anonymous_machine_id(),
            "category": category,
            "user_description": anonymize_text(user_description),
            "exception": _last_exception,
            "system_snapshot": get_current_system_snapshot(),
            "breadcrumbs": list(_breadcrumb_buffer),
            "logs": list(_log_buffer)[-150:] if include_logs else []
        }
        with open(local_incident_file, "w", encoding="utf-8") as f:
            json.dump(anonymize_data(incident_data), f, indent=2, ensure_ascii=False)
        log_event("INFO", f"Local incident record saved: {local_incident_file}")
    except Exception as e:
        log_event("WARNING", f"Failed to save local incident JSON: {e}")

    # 5. Assemble ZIP archive (contains everything inside)
    try:
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("diagnostic_summary.md", summary_md.encode('utf-8'))

            snapshot_data = get_current_system_snapshot()
            snapshot_data["user_report"] = {
                "incident_id": incident_id,
                "description": anonymize_text(user_description),
                "category": category
            }
            z.writestr("active_state.json", json.dumps(snapshot_data, indent=2, ensure_ascii=False).encode('utf-8'))

            if include_logs:
                with _lock:
                    log_text = "\n".join([f"[{l['timestamp']}] [{l['level']}] {l['message']}" for l in _log_buffer])
                z.writestr("app_runtime.log", log_text.encode('utf-8'))

            if screenshot_img:
                from io import BytesIO
                img_byte_arr = BytesIO()
                screenshot_img.save(img_byte_arr, format='PNG')
                z.writestr("screenshot.png", img_byte_arr.getvalue())

        log_event("INFO", f"Bug report ZIP successfully created: {zip_path}")
    except Exception as e:
        log_event("ERROR", f"Failed to build bug report zip: {e}")
        return {
            "success": False,
            "error": str(e)
        }

    # 6. Highlight the ZIP file in Windows Explorer
    try:
        subprocess.Popen(f'explorer.exe /select,"{os.path.abspath(zip_path)}"')
    except Exception as e:
        log_event("WARNING", f"Could not highlight file in explorer: {e}")

    # 7. Prepare mail links
    exc = _last_exception
    err_subj = f"[{exc['type']} in {exc['culprit_file']}]" if exc else f"[{category}]"
    subject = f"[SceneryX Issue #{incident_id}] {err_subj} - {user_description[:45]}"

    body_lines = [
        "Hello,",
        "",
        "Please find the SceneryX issue report details below.",
        "",
        f"Incident ID : #{incident_id}",
        f"Category    : {category}",
        f"Error       : {exc['type'] + ': ' + exc['message'] if exc else 'No exception raised'}",
        f"Location    : {exc['culprit_file'] + '#' + str(exc['culprit_line']) if exc else 'N/A'}",
        "",
        "--- PROBLEM DESCRIPTION ---",
        user_description.strip() if user_description else "(No description provided)",
        "",
        "*** ATTACHMENT ***",
        f"Attached file: '{report_zip_filename}'",
        "",
        "Thank you!"
    ]
    body = "\n".join(body_lines)

    mailto_url = f"mailto:{CONTACT_EMAIL}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    browser_mail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={urllib.parse.quote(CONTACT_EMAIL)}&su={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

    add_breadcrumb("REPORT_GENERATED", f"Bug report package generated: #{incident_id}", {"zip": report_zip_filename})

    return {
        "success": True,
        "incident_id": incident_id,
        "zip_path": zip_path,
        "filename": report_zip_filename,
        "recipient": CONTACT_EMAIL,
        "subject": subject,
        "body": body,
        "mailto_url": mailto_url,
        "browser_mail_url": browser_mail_url,
        "has_exception": bool(exc),
        "summary_md": summary_md
    }


def get_bug_reporter_status() -> Dict[str, Any]:
    """Retourne l'état en direct du module de diagnostic pour l'interface graphique."""
    with _lock:
        has_exc = _last_exception is not None
        exc_info = dict(_last_exception) if _last_exception else None
        crumbs_count = len(_breadcrumb_buffer)
        logs_count = len(_log_buffer)

    reports_count = 0
    if os.path.exists(CRASH_REPORTS_DIR):
        try:
            reports_count = len([f for f in os.listdir(CRASH_REPORTS_DIR) if f.endswith('.json')])
        except Exception:
            pass

    return {
        "has_exception": has_exc,
        "last_exception": exc_info,
        "breadcrumbs_count": crumbs_count,
        "logs_count": logs_count,
        "reports_count": reports_count,
        "machine_id": get_anonymous_machine_id(),
        "privacy": get_privacy_settings(),
        "contact_email": CONTACT_EMAIL
    }


def open_crash_reports_folder():
    """Ouvre le répertoire local des rapports de crash dans l'Explorateur Windows."""
    try:
        os.makedirs(CRASH_REPORTS_DIR, exist_ok=True)
        if sys.platform == 'win32':
            os.startfile(CRASH_REPORTS_DIR)
        else:
            subprocess.Popen(['xdg-open', CRASH_REPORTS_DIR])
        return {"status": "ok", "path": CRASH_REPORTS_DIR}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def simulate_test_bug(bug_type: str = "key_error") -> Dict[str, Any]:
    """Génère une exception réaliste pour tester l'ensemble du pipeline de diagnostic."""
    add_breadcrumb("USER_ACTION", "Clicked 'Apply VR 72Hz Airliner Profile'", {"profile": "VR_IFR_LINER", "target_lod": 140})
    add_breadcrumb("IPC_CALL", "Sent optimize_flight_rig command", {"mode": "VR", "aircraft": "Fenix A320"})
    add_breadcrumb("SIMCONNECT", "Queried aircraft coordinates & ground alt", {"sim": "MSFS 2024", "alt_ft": 2450})

    try:
        if bug_type == "vram_overflow":
            raise MemoryError("DirectX 12 Out of Memory: GPU VRAM threshold exceeded (16384 MB committed, 16376 MB physical) during photogrammetry terrain streaming")
        elif bug_type == "simconnect_timeout":
            raise TimeoutError("SimConnect connection lost: IPC pipe disconnected while polling SimVars in flight_memory_engine.py")
        else:
            raise KeyError("KeyError: 'target_vr_cadence_fps' not found in flight_rig_optimizer.py:8215 during profile application")
    except Exception as e:
        record_exception(type(e), e, e.__traceback__, context="Diagnostic pipeline self-test simulation")
        return {
            "status": "simulated",
            "message": f"Test error ({type(e).__name__}) captured successfully.",
            "exception": {
                "incident_id": _last_exception.get("incident_id") if _last_exception else "TEST",
                "type": type(e).__name__,
                "message": str(e),
                "culprit_file": _last_exception["culprit_file"] if _last_exception else "flight_rig_optimizer.py",
                "culprit_line": _last_exception["culprit_line"] if _last_exception else 8215
            }
        }
