#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SceneryX - Micro-Serveur HTTP REST Local pour In-Game Toolbar Panel MSFS.
Fournit une API locale ultra-légère multi-thread (127.0.0.1:8383) pour la communication
entre le simulateur (CoherentGT) et SceneryX en vol.
"""

import json
import threading
import socketserver
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Optional, Dict, Any

SERVER_PORT = 8383
_server_instance: Optional[HTTPServer] = None
_server_thread: Optional[threading.Thread] = None
_telemetry_poller_thread: Optional[threading.Thread] = None
_telemetry_poller_stop = threading.Event()
_CACHED_PANEL_TELEMETRY: Dict[str, Any] = {}
_CACHED_LOD_STATUS: Dict[str, Any] = {}
_CACHED_ACTIVE_HIGHLIGHTS: Dict[str, Dict[str, str]] = {}
_LAST_MANUAL_LOD: Dict[str, float] = {}
_CURRENT_LANGUAGE: str = "en"


def set_remote_panel_language(lang: str):
    global _CURRENT_LANGUAGE
    _CURRENT_LANGUAGE = "fr" if str(lang).lower().startswith("fr") else "en"


def _compute_active_highlights_snapshot() -> Dict[str, Dict[str, str]]:
    """Extracts 2D and VR active settings highlights (Display/Headset, AA/DLSS, Max FPS, Textures, Clouds)
    from UserCfg.opt and VR headset software without blocking the HTTP thread."""
    res_2d = {
        "display": "2D : 2560x1440",
        "aa": "DLSS Quality",
        "max_fps": "Max FPS : 36",
        "textures": "Textures : High",
        "clouds": "Clouds : High"
    }
    res_vr = {
        "display": "Headset : 1.00 90Hz",
        "aa": "DLSS Balanced",
        "max_fps": "Max FPS : 45",
        "textures": "Textures : Medium",
        "clouds": "Clouds : High"
    }
    try:
        import os
        import flight_rig_optimizer as fro
        path = fro.get_user_cfg_path()
        content = ""
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            staged_dict = getattr(fro, "_staged_user_cfg_settings", {})
            for m, staged in staged_dict.items():
                for k, v in staged.items():
                    content = fro.apply_setting_to_content(content, m, k, v)

        if content:
            video = fro.extract_block(content, "{Video")
            g2d = fro.extract_block(content, "{Graphics\n") or fro.extract_block(content, "{Graphics\r\n")
            gvr = fro.extract_block(content, "{GraphicsVR")

            # 1. 2D Display Resolution
            res_raw = fro.get_block_val(r"FullScreenResolution\s+([\d\s]+)", video, "2560 1440")
            parts = res_raw.split() if res_raw else ["2560", "1440"]
            if len(parts) >= 2:
                res_2d["display"] = f"2D : {parts[0]}x{parts[1]}"

            # 2. VR Headset Scale & Refresh Rate
            vr_info = {}
            try:
                vr_info = fro.detect_vr_headset() or {}
            except Exception:
                pass
            sw_scale = vr_info.get("software_render_scale")
            if sw_scale is None:
                ps_vr = fro.get_block_val(r"PrimaryScalingVR\s+([\d\.]+)", gvr, "1.0")
                try:
                    sw_scale = float(ps_vr)
                    if sw_scale > 5.0:
                        sw_scale = sw_scale / 100.0
                except Exception:
                    sw_scale = 1.0
            vr_hz = vr_info.get("refresh_rate_hz") or 90
            try:
                res_vr["display"] = f"Headset : {float(sw_scale):.2f} {int(vr_hz)}Hz"
            except Exception:
                res_vr["display"] = "Headset : 1.00 90Hz"

            # 3. Anti-Aliasing / DLSS (Minimal tags: TAA, DLAA, DLSS Quality, DLSS Balanced, DLSS Performance)
            def _fmt_minimal_aa(aa_raw: str, dlss_raw: str) -> str:
                aa_up = (aa_raw or "TAA").strip().upper()
                dlss_up = (dlss_raw or "QUALITY").strip().upper()
                if "DLAA" in aa_up:
                    return "DLAA"
                if "DLSS" in aa_up:
                    if "ULTRA" in dlss_up:
                        return "DLSS Ultra Perf"
                    if "PERF" in dlss_up:
                        return "DLSS Performance"
                    if "BAL" in dlss_up:
                        return "DLSS Balanced"
                    if "DLAA" in dlss_up:
                        return "DLAA"
                    return "DLSS Quality"
                if "FSR" in aa_up:
                    return "FSR 2"
                if "FXAA" in aa_up:
                    return "FXAA"
                if "OFF" in aa_up or aa_up == "NONE":
                    return "AA : OFF"
                return "TAA"

            aa_2d_raw = fro.get_block_val(r"AntiAliasing\s+([^\r\n]+)", video, "TAA")
            dlss_2d_raw = fro.get_block_val(r"DLSSMode\s+(\w+)", video, "QUALITY")
            aa_vr_raw = fro.get_block_val(r"AntiAliasingVR\s+([^\r\n]+)", video, "TAA")
            dlss_vr_raw = fro.get_block_val(r"DLSSModeVR\s+(\w+)", video, "QUALITY")
            res_2d["aa"] = _fmt_minimal_aa(aa_2d_raw, dlss_2d_raw)
            res_vr["aa"] = _fmt_minimal_aa(aa_vr_raw, dlss_vr_raw)

            # 4. Max Frame Rate
            fps_2d = fro.get_block_val(r"TargetFrameRate\s+(\d+)", video, "0").strip()
            fps_vr = fro.get_block_val(r"TargetFrameRateVR\s+(\d+)", video, "0").strip()
            res_2d["max_fps"] = f"Max FPS : {fps_2d}" if (fps_2d.isdigit() and int(fps_2d) > 0) else "Max FPS : OFF"
            res_vr["max_fps"] = f"Max FPS : {fps_vr}" if (fps_vr.isdigit() and int(fps_vr) > 0) else "Max FPS : OFF"

            # 5. Texture Resolution (0=Ultra, 1=High, 2=Medium, 3=Low)
            tex_q_map = {"0": "Ultra", "1": "High", "2": "Medium", "3": "Low"}
            tex_2d_raw = fro.get_block_val(r"Quality\s+(\d+)", fro.extract_block(g2d, "{Texture"), "1")
            tex_vr_raw = fro.get_block_val(r"Quality\s+(\d+)", fro.extract_block(gvr, "{Texture"), "2")
            res_2d["textures"] = f"Textures : {tex_q_map.get(tex_2d_raw, 'High')}"
            res_vr["textures"] = f"Textures : {tex_q_map.get(tex_vr_raw, 'Medium')}"

            # 6. Volumetric Clouds (0=Low, 1=Medium, 2=High, 3=Ultra)
            q_map = {"0": "Low", "1": "Medium", "2": "High", "3": "Ultra"}
            cld_2d_raw = fro.get_block_val(r"Quality\s+(\d+)", fro.extract_block(g2d, "{VolumetricClouds"), "2")
            cld_vr_raw = fro.get_block_val(r"Quality\s+(\d+)", fro.extract_block(gvr, "{VolumetricClouds"), "2")
            res_2d["clouds"] = f"Clouds : {q_map.get(cld_2d_raw, 'High')}"
            res_vr["clouds"] = f"Clouds : {q_map.get(cld_vr_raw, 'High')}"
    except Exception:
        pass
    return {"2d": res_2d, "vr": res_vr}


def _panel_telemetry_background_loop():
    """Dedicated background thread that refreshes hardware/sim telemetry at ~1.2 Hz
    so HTTP /api/telemetry requests return instantaneously (<1ms) from RAM without
    ever blocking on WMI COM calls, nvidia-smi subprocesses, or disk I/O."""
    global _CACHED_PANEL_TELEMETRY, _CACHED_LOD_STATUS, _CACHED_ACTIVE_HIGHLIGHTS
    tick_count = 0
    while not _telemetry_poller_stop.is_set():
        try:
            import flight_perf_tracker
            if hasattr(flight_perf_tracker, "BLACKBOX") and flight_perf_tracker.BLACKBOX:
                if hasattr(flight_perf_tracker.BLACKBOX, "get_panel_telemetry"):
                    snap = flight_perf_tracker.BLACKBOX.get_panel_telemetry()
                else:
                    snap = flight_perf_tracker.BLACKBOX.get_telemetry()
                if snap:
                    _CACHED_PANEL_TELEMETRY = dict(snap)
        except Exception:
            pass
        try:
            import flight_lod_controller
            lod_ctrl = flight_lod_controller.get_smart_lod_controller()
            if lod_ctrl:
                st = lod_ctrl.get_status()
                if st:
                    _CACHED_LOD_STATUS = dict(st)
        except Exception:
            pass
        if tick_count % 3 == 0 or not _CACHED_ACTIVE_HIGHLIGHTS:
            try:
                _CACHED_ACTIVE_HIGHLIGHTS = _compute_active_highlights_snapshot()
            except Exception:
                pass
            try:
                import scanner
                st_cfg = scanner.get_settings()
                if isinstance(st_cfg, dict) and st_cfg.get("language") in ("en", "fr"):
                    global _CURRENT_LANGUAGE
                    _CURRENT_LANGUAGE = st_cfg["language"]
            except Exception:
                pass
        tick_count += 1
        _telemetry_poller_stop.wait(0.8)


import socket

class DualStackThreadingServer(socketserver.ThreadingMixIn, HTTPServer):
    """Serveur HTTP multi-thread avec support Dual-Stack IPv4 et IPv6."""
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        try:
            self.address_family = socket.AF_INET6
            super().__init__(server_address, RequestHandlerClass, bind_and_activate=False)
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            if bind_and_activate:
                self.server_bind()
                self.server_activate()
        except Exception:
            self.address_family = socket.AF_INET
            super().__init__(server_address, RequestHandlerClass, bind_and_activate)


ThreadingSimpleServer = DualStackThreadingServer


import urllib.parse

class RemoteApiHandler(SimpleHTTPRequestHandler):
    """Handler HTTP REST multi-thread avec support CORS complet pour CoherentGT."""

    def log_message(self, format, *args):
        # Silence standard HTTP logs to avoid cluttering console
        pass

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, Accept, Origin, Range")
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Connection", "close")
        super().end_headers()

    def do_OPTIONS(self):
        self.close_connection = True
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        clean_path = parsed.path
        if clean_path in ("/api/telemetry", "/telemetry"):
            self._handle_get_telemetry()
        elif clean_path in ("/api/status", "/status"):
            self._send_json(200, {"status": "ok", "app": "SceneryX"})
        elif clean_path in ("/api/smart_lod/set_lod", "/smart_lod/set_lod"):
            query_params = urllib.parse.parse_qs(parsed.query)
            params = {}
            if "tlod" in query_params:
                try:
                    params["tlod"] = float(query_params["tlod"][0])
                except ValueError:
                    pass
            if "olod" in query_params:
                try:
                    params["olod"] = float(query_params["olod"][0])
                except ValueError:
                    pass
            self._handle_smart_lod_set_lod(params)
        elif clean_path in ("/api/smart_lod/reset_override", "/smart_lod/reset_override", "/api/smart_lod/reset_to_profile", "/smart_lod/reset_to_profile"):
            query_params = urllib.parse.parse_qs(parsed.query)
            axis = query_params.get("axis", ["all"])[0]
            self._handle_smart_lod_reset_to_profile({"axis": axis})
        elif clean_path in ("/api/smart_lod/axis_config", "/smart_lod/axis_config"):
            query_params = urllib.parse.parse_qs(parsed.query)
            mode = query_params.get("mode", ["2D"])[0]
            try:
                import flight_lod_controller
                st = flight_lod_controller.get_smart_lod_axis_state(mode)
                self._send_json(200, st)
            except Exception as e:
                self._send_json(500, {"error": str(e)})
        elif clean_path in ("/api/smart_lod/toggle", "/smart_lod/toggle"):
            query_params = urllib.parse.parse_qs(parsed.query)
            params = {}
            if "enabled" in query_params:
                params["enabled"] = query_params["enabled"][0].lower() in ("1", "true", "yes", "on")
            self._handle_smart_lod_toggle(params)
        elif clean_path in ("/api/smart_lod/cloud_recovery", "/smart_lod/cloud_recovery"):
            query_params = urllib.parse.parse_qs(parsed.query)
            params = {}
            if "enabled" in query_params:
                params["enabled"] = query_params["enabled"][0].lower() in ("1", "true", "yes", "on")
            self._handle_smart_lod_cloud_recovery(params)
        elif clean_path in ("/panel", "/panel/", "/preview", "/preview/"):
            self._handle_serve_panel_file("index.html")
        elif clean_path.startswith("/panel/"):
            rel = clean_path[len("/panel/"):]
            self._handle_serve_panel_file(rel)
        elif clean_path.startswith("/in_game_panel/"):
            rel = clean_path[len("/in_game_panel/"):]
            self._handle_serve_panel_file(rel)
        else:
            self._send_json(404, {"error": "Not found", "path": self.path})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        clean_path = parsed.path
        if clean_path in ("/api/smart_lod/toggle", "/smart_lod/toggle"):
            query_params = urllib.parse.parse_qs(parsed.query)
            params = {}
            if "enabled" in query_params:
                params["enabled"] = query_params["enabled"][0].lower() in ("1", "true", "yes", "on")
            self._handle_smart_lod_toggle(params)
        elif clean_path in ("/api/smart_lod/set_lod", "/smart_lod/set_lod"):
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
                params = json.loads(body)
            except Exception:
                params = {}
            self._handle_smart_lod_set_lod(params)
        elif clean_path in ("/api/smart_lod/reset_override", "/smart_lod/reset_override", "/api/smart_lod/reset_to_profile", "/smart_lod/reset_to_profile"):
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
                params = json.loads(body)
            except Exception:
                params = {}
            if "axis" not in params:
                parsed = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed.query)
                params["axis"] = query_params.get("axis", ["all"])[0]
            self._handle_smart_lod_reset_to_profile(params)
        elif clean_path in ("/api/smart_lod/axis_config", "/smart_lod/axis_config"):
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
                params = json.loads(body)
            except Exception:
                params = {}
            try:
                import flight_lod_controller
                st = flight_lod_controller.set_smart_lod_axis_state(
                    params.get("mode", "2D"),
                    params.get("axis", "tlod"),
                    enabled=params.get("enabled"),
                    target=params.get("target"),
                    altitude=params.get("altitude"),
                    base=params.get("base")
                )
                try:
                    global _CACHED_LOD_STATUS
                    _CACHED_LOD_STATUS = dict(flight_lod_controller.get_smart_lod_controller().get_status())
                except Exception:
                    pass
                self._send_json(200, st)
            except Exception as e:
                self._send_json(500, {"error": str(e)})
        elif clean_path in ("/api/smart_lod/cloud_recovery", "/smart_lod/cloud_recovery"):
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
                params = json.loads(body)
            except Exception:
                params = {}
            self._handle_smart_lod_cloud_recovery(params)
        elif clean_path in ("/api/smart_lod/apply_live_graphics", "/smart_lod/apply_live_graphics"):
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
                params = json.loads(body)
            except Exception:
                params = {}
            self._handle_apply_live_graphics(params)
        elif clean_path in ("/api/smart_lod/save_pins", "/smart_lod/save_pins"):
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
                params = json.loads(body)
            except Exception:
                params = {}
            self._handle_save_pins(params)
        elif clean_path in ("/api/blackbox/toggle", "/blackbox/toggle"):
            self._handle_blackbox_toggle()
        else:
            self._send_json(404, {"error": "Not found", "path": self.path})

    def _send_json(self, status_code: int, data: Dict[str, Any]):
        try:
            self.close_connection = True
            body = json.dumps(data, ensure_ascii=True).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()
        except Exception as e:
            print(f"[RemoteServer] Error sending JSON: {e}")

    def _handle_serve_panel_file(self, rel_path: str):
        import os
        base_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "web", "in_game_panel"))
        file_path = os.path.normpath(os.path.join(base_dir, rel_path.lstrip("/\\")))
        if not file_path.startswith(base_dir) or not os.path.exists(file_path) or os.path.isdir(file_path):
            self._send_json(404, {"error": "File not found", "path": rel_path})
            return
        content_type = "text/plain"
        if file_path.endswith(".html"):
            content_type = "text/html; charset=utf-8"
        elif file_path.endswith(".css"):
            content_type = "text/css; charset=utf-8"
        elif file_path.endswith(".js"):
            content_type = "application/javascript; charset=utf-8"
        elif file_path.endswith(".svg"):
            content_type = "image/svg+xml"
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            self.close_connection = True
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Connection", "close")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(data)
            self.wfile.flush()
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _handle_get_telemetry(self):
        try:
            import sys
            # 1. Performance Tracker Telemetry (non-blocking from background thread snapshot)
            telem = dict(_CACHED_PANEL_TELEMETRY) if _CACHED_PANEL_TELEMETRY else {}
            try:
                fpt = sys.modules.get("flight_perf_tracker")
                if fpt and hasattr(fpt, "BLACKBOX") and fpt.BLACKBOX:
                    telem["is_tracking"] = bool(fpt.BLACKBOX.is_running)
                    sc_client = getattr(fpt, "SIMCONNECT_CLIENT", None)
                    sc_data = sc_client.get_data() if sc_client else {}
                    if sc_data.get("connected") and sc_data.get("base_fps") is not None:
                        telem["displayed_fps"] = sc_data.get("displayed_fps")
                        telem["base_fps"] = sc_data.get("base_fps")
                        telem["main_thread_ms"] = sc_data.get("frame_time_ms")
                        telem["agl_ft"] = sc_data.get("agl_ft")
                        telem["simconnect_connected"] = True
            except Exception as e:
                print(f"[RemoteServer] Telemetry error: {e}")

            # 2. Smart LOD Status (non-blocking from background thread snapshot + live RAM state)
            lod_status = dict(_CACHED_LOD_STATUS) if _CACHED_LOD_STATUS else {}
            cur_tlod = lod_status.get("current_tlod_setpoint")
            cur_olod = lod_status.get("current_olod_setpoint")
            lod_ctrl = None
            mem = None
            try:
                flc = sys.modules.get("flight_lod_controller")
                if flc and getattr(flc, "_global_controller", None) is not None:
                    lod_ctrl = flc._global_controller
                    is_ext = bool(lod_ctrl.config.get("external_autofps", False) or (lod_ctrl.config.get("source") == "external_autofps") or lod_status.get("autofps_conflict", False))
                    lod_status["enabled"] = bool(lod_ctrl.config.get("enabled", False) and not is_ext)
                    lod_status["is_running"] = bool(lod_ctrl.is_running and not is_ext)
                    lod_status["external_autofps"] = is_ext
                    cur_tlod = round(lod_ctrl.current_tlod_setpoint, 1)
                    cur_olod = round(lod_ctrl.current_olod_setpoint, 1)
                    lod_status["current_tlod_setpoint"] = cur_tlod
                    lod_status["current_olod_setpoint"] = cur_olod
                    if getattr(lod_ctrl, "manual_olod", None) is not None:
                        cur_olod = lod_ctrl.manual_olod
                    if getattr(lod_ctrl, "manual_tlod", None) is not None:
                        cur_tlod = lod_ctrl.manual_tlod
            except Exception:
                pass

            # Check module-level manual LOD cache as persistent safety net
            if _LAST_MANUAL_LOD.get("tlod") is not None:
                cur_tlod = _LAST_MANUAL_LOD["tlod"]
            if _LAST_MANUAL_LOD.get("olod") is not None:
                cur_olod = _LAST_MANUAL_LOD["olod"]

            # Try direct memory engine read if available and not actively regulated
            try:
                fme = sys.modules.get("flight_memory_engine")
                if fme and getattr(fme, "_global_memory_engine", None) is not None:
                    mem = fme._global_memory_engine
                    if mem.is_attached and not mem.safe_read_only:
                        mem_tlod = mem.read_tlod()
                        mem_olod = mem.read_olod()
                        if mem_tlod is not None and "tlod" not in _LAST_MANUAL_LOD and not (lod_status.get("enabled") and lod_status.get("is_running")):
                            cur_tlod = mem_tlod
                        if mem_olod is not None and "olod" not in _LAST_MANUAL_LOD and not (lod_status.get("enabled") and lod_status.get("is_running")):
                            cur_olod = mem_olod
            except Exception:
                pass

            # Fallback to telemetry LOD if available
            if cur_tlod is None and telem.get("tlod") is not None:
                cur_tlod = telem.get("tlod")
            if cur_olod is None and telem.get("olod") is not None:
                cur_olod = telem.get("olod")

            disp_fps = telem.get("displayed_fps")
            base_fps = telem.get("base_fps")
            mt_ms = telem.get("main_thread_ms")

            # Frame pacing evaluation synchronized with desktop app and tracker
            if (base_fps is not None and base_fps >= 35) or (mt_ms is not None and mt_ms < 25.0):
                pacing = "OPTIMAL"
            elif (base_fps is not None and base_fps >= 24) or (mt_ms is not None and mt_ms <= 35.0):
                pacing = "ACCEPTABLE"
            elif base_fps is not None or mt_ms is not None:
                pacing = "HEAVY"
            else:
                pacing = "OPTIMAL"

            is_vr_mode = False
            try:
                if mem and mem.is_attached:
                    is_vr_mode = mem.is_vr_active()
            except Exception:
                pass

            axis_state = {}
            try:
                if lod_ctrl:
                    axis_state = lod_ctrl.get_axis_state("VR" if is_vr_mode else "2D")
            except Exception:
                pass

            is_ext_af = bool(lod_status.get("external_autofps", False))
            smart_lod_enabled = bool(lod_status.get("enabled", False)) and not is_ext_af
            smart_lod_running = bool(lod_status.get("is_running", False)) and not is_ext_af
            nom_tlod = float(lod_status.get("nominal_tlod", 100.0))
            nom_olod = float(lod_status.get("nominal_olod", 100.0))
            nom_profile = str(lod_status.get("nominal_profile", "Active Profile"))

            if is_ext_af:
                cur_tlod = _LAST_MANUAL_LOD.get("tlod", nom_tlod)
                cur_olod = _LAST_MANUAL_LOD.get("olod", nom_olod)
                tlod_floor = axis_state.get("tlod_base", cur_tlod)
                tlod_cruise = axis_state.get("tlod_target", min(400.0, cur_tlod + 50.0))
                olod_floor = axis_state.get("olod_base", cur_olod)
                olod_cruise = axis_state.get("olod_target", min(300.0, cur_olod + 50.0))
                tlod_is_manual = True
                olod_is_manual = True
                status_msg = "LOCKED (AUTOFPS)"
            elif not smart_lod_enabled:
                cur_tlod = _LAST_MANUAL_LOD.get("tlod", nom_tlod)
                cur_olod = _LAST_MANUAL_LOD.get("olod", nom_olod)
                tlod_floor = axis_state.get("tlod_base", cur_tlod)
                tlod_cruise = axis_state.get("tlod_target", min(400.0, cur_tlod + 50.0))
                olod_floor = axis_state.get("olod_base", cur_olod)
                olod_cruise = axis_state.get("olod_target", min(300.0, cur_olod + 50.0))
                tlod_is_manual = True
                olod_is_manual = True
                status_msg = "MAN"
            else:
                cur_tlod = lod_status.get("current_tlod_setpoint")
                cur_olod = lod_status.get("current_olod_setpoint")
                tlod_floor = axis_state.get("tlod_base", 100)
                tlod_cruise = axis_state.get("tlod_target", 200)
                olod_floor = axis_state.get("olod_base", 100)
                olod_cruise = axis_state.get("olod_target", 100)
                tlod_is_manual = bool((lod_ctrl and getattr(lod_ctrl, "manual_tlod", None) is not None) or "tlod" in _LAST_MANUAL_LOD)
                olod_is_manual = bool((lod_ctrl and getattr(lod_ctrl, "manual_olod", None) is not None) or "olod" in _LAST_MANUAL_LOD)
                status_msg = str(lod_status.get("status_message", "Ready (Standby)"))
                if "Inactif" in status_msg or "Pr" in status_msg:
                    status_msg = "Ready (Standby)"

            msfs_vram_mb = telem.get("msfs_vram_mb") or 0.0
            vram_used_mb = telem.get("vram_used_mb") or 0
            vram_total_mb = telem.get("vram_total_mb") or 16376
            vram_used_gb = round(vram_used_mb / 1024.0, 1) if vram_used_mb else 0.0
            vram_total_gb = round(vram_total_mb / 1024.0, 1) if vram_total_mb else 0.0
            cache_mbps = telem.get("cache_read_mbps", 0.0) or 0.0
            is_tracking = bool(telem.get("is_tracking", False))

            gpu_util = telem.get("gpu_util_pct", 0) or 0
            gpu_temp = telem.get("gpu_temp_c", 0) or 0
            cpu_util = telem.get("cpu_pct") or telem.get("msfs_cpu_pct") or 0
            cpu_temp = telem.get("cpu_temp_c") or 45.0

            hl_snap = _CACHED_ACTIVE_HIGHLIGHTS or {}
            active_highlights = dict(hl_snap.get("vr" if is_vr_mode else "2d") or {
                "display": "Headset : 1.00 90Hz" if is_vr_mode else "2D : 2560x1440",
                "aa": "DLSS Balanced" if is_vr_mode else "DLSS Quality",
                "max_fps": "Max FPS : 45" if is_vr_mode else "Max FPS : 36",
                "textures": "Textures : Medium" if is_vr_mode else "Textures : High",
                "clouds": "Clouds : High"
            })

            # 8 Live-Editable Graphics Settings + Active Profile Reference + Pinned Keys
            nom_prof_vals = {}
            overrides = {}
            try:
                import flight_lod_controller as _flc_mod
                nom_prof_vals = _flc_mod.get_active_profile_nominal_values(is_vr=is_vr_mode) or {}
                overrides = _flc_mod.get_live_graphics_overrides() or {}
            except Exception:
                nom_prof_vals = {}
                overrides = {}

            # Live Cloud Quality (0=Low, 1=Medium, 2=High, 3=Ultra)
            cloud_title_map = {0: "Low", 1: "Medium", 2: "High", 3: "Ultra"}
            cloud_upper_map = {0: "LOW", 1: "MEDIUM", 2: "HIGH", 3: "ULTRA"}
            nom_cloud_q = int(nom_prof_vals.get("clouds", lod_status.get("nominal_cloud_quality", 2)))
            cur_cloud_q = None
            if "clouds" in overrides:
                cur_cloud_q = int(overrides["clouds"])
            elif lod_ctrl and getattr(lod_ctrl, "current_cloud_quality", None) is not None:
                cur_cloud_q = int(lod_ctrl.current_cloud_quality)
            else:
                cur_cloud_q = int(lod_status.get("current_cloud_quality", nom_cloud_q))
            cur_cloud_q = max(0, min(3, int(cur_cloud_q)))
            nom_cloud_q = max(0, min(3, int(nom_cloud_q)))
            cur_cloud_label = cloud_upper_map.get(cur_cloud_q, "HIGH")
            nom_cloud_label = cloud_upper_map.get(nom_cloud_q, "HIGH")
            in_cloud_reduction = bool(cur_cloud_q < nom_cloud_q)
            in_cloud_boost = bool(cur_cloud_q > nom_cloud_q)
            active_highlights["clouds"] = f"Clouds : {cloud_title_map.get(cur_cloud_q, 'High')}"

            profile_graphics = {
                "max_fps": int(nom_prof_vals.get("max_fps", 36 if is_vr_mode else 60)),
                "clouds": int(nom_prof_vals.get("clouds", nom_cloud_q)),
                "precaching": int(nom_prof_vals.get("precaching", 2)),
                "terrain_shadows": int(nom_prof_vals.get("terrain_shadows", 256 if is_vr_mode else 512)),
                "buildings": int(nom_prof_vals.get("buildings", 2)),
                "trees": int(nom_prof_vals.get("trees", 2)),
                "plants": int(nom_prof_vals.get("plants", 1 if is_vr_mode else 2)),
                "grass": int(nom_prof_vals.get("grass", 0 if is_vr_mode else 2)),
            }

            live_graphics = dict(profile_graphics)
            live_graphics["clouds"] = int(cur_cloud_q)
            try:
                if mem and mem.is_attached and not mem.safe_read_only:
                    ram_gfx = mem.read_live_graphics()
                    if ram_gfx:
                        for gk, gv in ram_gfx.items():
                            if gv is not None and gk != "clouds" and gk not in overrides:
                                live_graphics[gk] = int(gv)
            except Exception:
                pass
            for ok, ov in overrides.items():
                if ov is not None:
                    live_graphics[ok] = int(ov)
            live_graphics["clouds"] = int(cur_cloud_q)
            if "max_fps" in live_graphics:
                fps_disp = int(live_graphics["max_fps"])
                active_highlights["max_fps"] = f"Max FPS : {fps_disp}" if fps_disp > 0 else "Max FPS : OFF"

            pinned_keys = ["max_fps", "clouds", "precaching", "buildings", "trees"]
            try:
                if lod_ctrl and hasattr(lod_ctrl, "get_ingame_pinned_settings"):
                    pinned_keys = lod_ctrl.get_ingame_pinned_settings()
            except Exception:
                pass

            telemetry_data = {
                "app_running": True,
                "connected": True,
                "language": _CURRENT_LANGUAGE,
                "sim_connected": bool(telem.get("simconnect_connected", False)),
                "msfs_active": bool(telem.get("msfs_active", False)),
                "is_vr": is_vr_mode,
                "agl_ft": telem.get("agl_ft") or 0,
                "active_highlights": active_highlights,
                "live_graphics": live_graphics,
                "profile_graphics": profile_graphics,
                "pinned_keys": pinned_keys,
                "perf": {
                    "displayed_fps": disp_fps,
                    "fps": base_fps,
                    "main_thread_ms": mt_ms,
                    "frame_pacing": pacing
                },
                "smart_lod": {
                    "active": smart_lod_enabled and smart_lod_running,
                    "enabled": smart_lod_enabled,
                    "running": smart_lod_running,
                    "external_autofps": is_ext_af,
                    "current_tlod": cur_tlod if cur_tlod is not None else 100,
                    "current_olod": cur_olod if cur_olod is not None else 100,
                    "nominal_tlod": nom_tlod,
                    "nominal_olod": nom_olod,
                    "nominal_profile": nom_profile,
                    "tlod_manual": tlod_is_manual,
                    "olod_manual": olod_is_manual,
                    "is_vr": is_vr_mode,
                    "status": status_msg,
                    "axis_state": axis_state,
                    "tlod_base": tlod_floor,
                    "tlod_target": tlod_cruise,
                    "tlod_altitude": axis_state.get("tlod_altitude", 3000),
                    "olod_base": olod_floor,
                    "olod_target": olod_cruise,
                    "olod_altitude": axis_state.get("olod_altitude", 3000),
                    "cloud_recovery": bool(lod_ctrl.config.get("cloud_recovery", True)) if lod_ctrl else True,
                    "cloud_quality": cur_cloud_q,
                    "cloud_label": cur_cloud_label,
                    "nominal_cloud_quality": nom_cloud_q,
                    "nominal_cloud_label": nom_cloud_label,
                    "in_cloud_reduction": in_cloud_reduction,
                    "in_cloud_boost": in_cloud_boost,
                },
                "external_autofps": is_ext_af,
                "vram_used_gb": vram_used_gb,
                "vram_total_gb": vram_total_gb,
                "gpu_util_pct": gpu_util,
                "gpu_temp_c": gpu_temp,
                "cpu_pct": cpu_util,
                "cpu_temp_c": cpu_temp,
                "rolling_cache_gb": round(cache_mbps, 1),
                "blackbox_recording": is_tracking,
                "gpu_temp": gpu_temp,
                "cpu_temp": cpu_temp,
                # Flat fields for direct compatibility
                "displayed_fps": disp_fps,
                "base_fps": base_fps,
                "main_thread_ms": mt_ms,
                "smart_lod_enabled": smart_lod_enabled,
                "smart_lod_running": smart_lod_running,
                "smart_lod_tlod": cur_tlod if cur_tlod is not None else 100,
                "smart_lod_olod": cur_olod if cur_olod is not None else 100,
                "nominal_tlod": nom_tlod,
                "nominal_olod": nom_olod,
                "nominal_profile": nom_profile,
                "smart_lod_tlod_manual": tlod_is_manual,
                "smart_lod_olod_manual": olod_is_manual,
                "smart_lod_status": status_msg,
                "cloud_recovery": bool(lod_ctrl.config.get("cloud_recovery", True)) if lod_ctrl else True,
                "smart_lod_cloud_recovery": bool(lod_ctrl.config.get("cloud_recovery", True)) if lod_ctrl else True,
                "cloud_quality": cur_cloud_q,
                "cloud_label": cur_cloud_label,
                "nominal_cloud_quality": nom_cloud_q,
                "nominal_cloud_label": nom_cloud_label,
                "in_cloud_reduction": in_cloud_reduction,
                "in_cloud_boost": in_cloud_boost,
            }

            self._send_json(200, telemetry_data)
        except Exception as e:
            print(f"[RemoteServer] Fallback telemetry triggered: {e}")
            fallback_data = {
                "app_running": True,
                "connected": True,
                "sim_connected": False,
                "msfs_active": True,
                "is_vr": False,
                "agl_ft": 0,
                "perf": {"displayed_fps": None, "fps": None, "main_thread_ms": None, "frame_pacing": "OPTIMAL"},
                "smart_lod": {"active": False, "enabled": False, "running": False, "current_tlod": 100, "current_olod": 100, "cloud_recovery": False, "cloud_label": "HIGH"},
                "displayed_fps": None,
                "base_fps": None,
                "main_thread_ms": None,
                "gpu_temp_c": 0,
                "cpu_temp_c": 0,
                "smart_lod_enabled": False,
                "smart_lod_running": False,
                "smart_lod_tlod": 100,
                "smart_lod_olod": 100,
                "smart_lod_tlod_manual": False,
                "smart_lod_olod_manual": False,
                "smart_lod_status": "Ready (Standby)",
                "cloud_recovery": False,
                "smart_lod_cloud_recovery": False,
                "cloud_label": "HIGH",
                "error": str(e)
            }
            self._send_json(200, fallback_data)

    def _handle_smart_lod_toggle(self, params: Optional[Dict[str, Any]] = None):
        global _LAST_MANUAL_LOD, _CACHED_LOD_STATUS
        try:
            import flight_lod_controller
            lod_ctrl = flight_lod_controller.get_smart_lod_controller()
            current_status = lod_ctrl.get_status()
            if current_status.get("external_autofps"):
                self._send_json(200, {
                    "success": False,
                    "enabled": False,
                    "locked": True,
                    "external_autofps": True,
                    "message": "Smart LOD verrouillé : MSFS AutoFPS est actif en arrière-plan."
                })
                return
            _LAST_MANUAL_LOD.clear()

            new_state = None
            if params and "enabled" in params:
                new_state = bool(params["enabled"])
            else:
                parsed = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed.query)
                if "enabled" in query_params:
                    new_state = query_params["enabled"][0].lower() in ("1", "true", "yes", "on")

            if new_state is None:
                # Read optional body or toggle current state
                length = int(self.headers.get("Content-Length", 0))
                if length > 0:
                    try:
                        body = self.rfile.read(length).decode("utf-8")
                        data = json.loads(body)
                        if "enabled" in data:
                            new_state = bool(data["enabled"])
                    except Exception:
                        pass
            if new_state is None:
                new_state = not bool(current_status.get("enabled", False))

            res = lod_ctrl.set_enabled(new_state, force_kill_autofps=False)
            if not new_state:
                nom_vals = flight_lod_controller.get_active_profile_nominal_values()
                nom_tlod = float(nom_vals.get("tlod", 100.0))
                nom_olod = float(nom_vals.get("olod", 100.0))
                cruise_tlod = min(400.0, nom_tlod + 50.0)
                cruise_olod = min(300.0, nom_olod + 50.0)
                _LAST_MANUAL_LOD["tlod"] = nom_tlod
                _LAST_MANUAL_LOD["olod"] = nom_olod
                res["tlod"] = nom_tlod
                res["olod"] = nom_olod
                res["nominal_tlod"] = nom_tlod
                res["nominal_olod"] = nom_olod
                res["tlod_base"] = nom_tlod
                res["tlod_target"] = cruise_tlod
                res["olod_base"] = nom_olod
                res["olod_target"] = cruise_olod
                res["nominal_profile"] = nom_vals.get("name", "Active Profile")
            try:
                _CACHED_LOD_STATUS = dict(lod_ctrl.get_status())
            except Exception:
                pass
            print(f"[RemoteServer] Smart LOD Toggle: set_enabled({new_state}) -> {res}")
            self._send_json(200, res)
        except Exception as e:
            print(f"[RemoteServer] Smart LOD Toggle Error: {e}")
            self._send_json(500, {"success": False, "error": str(e)})

    def _handle_smart_lod_set_lod(self, params: Dict[str, Any]):
        global _LAST_MANUAL_LOD, _CACHED_LOD_STATUS
        try:
            tlod = params.get("tlod")
            olod = params.get("olod")
            disengage_auto = bool(params.get("disengage_auto", False))
            base_param = params.get("base")
            target_param = params.get("target")
            alt_param = params.get("altitude")
            axis_param = str(params.get("axis", "")).lower()
            res = {"success": True}

            import flight_memory_engine
            mem = flight_memory_engine.get_memory_engine()
            if not mem.is_attached or mem.safe_read_only:
                mem.attach()

            if tlod is not None:
                tlod_val = float(tlod)
                _LAST_MANUAL_LOD["tlod"] = tlod_val
                if mem.is_attached and not mem.safe_read_only:
                    mem.write_tlod(tlod_val)
                res["tlod"] = tlod_val

            if olod is not None:
                olod_val = float(olod)
                _LAST_MANUAL_LOD["olod"] = olod_val
                if mem.is_attached and not mem.safe_read_only:
                    mem.write_olod(olod_val)
                res["olod"] = olod_val

            # Also update Smart LOD controller setpoints, manual slider bounds, and persist config
            try:
                import flight_lod_controller
                lod_ctrl = flight_lod_controller.get_smart_lod_controller()
                ax = "olod" if (olod is not None or "olod" in axis_param) else "tlod"
                max_v = 300 if ax == "olod" else 400
                config_changed = False

                with lod_ctrl._lock:
                    if disengage_auto:
                        lod_ctrl.config["enabled"] = False
                        lod_ctrl.config["2d_tlod_active"] = False
                        lod_ctrl.config["2d_olod_active"] = False
                        lod_ctrl.config["vr_tlod_active"] = False
                        lod_ctrl.config["vr_olod_active"] = False
                        lod_ctrl.status_message = "MAN"
                        config_changed = True

                    if base_param is not None:
                        b_val = max(0, min(int(round(float(base_param))), max_v))
                        lod_ctrl.config[f"2d_{ax}_base"] = b_val
                        lod_ctrl.config[f"vr_{ax}_base"] = b_val
                        if ax == "tlod":
                            lod_ctrl.dynamic_tlod_floor = float(b_val)
                        else:
                            lod_ctrl.dynamic_olod_floor = float(b_val)
                        config_changed = True

                    if target_param is not None:
                        t_val = max(0, min(int(round(float(target_param))), max_v))
                        lod_ctrl.config[f"2d_{ax}_target"] = t_val
                        lod_ctrl.config[f"vr_{ax}_target"] = t_val
                        if ax == "tlod":
                            lod_ctrl.dynamic_tlod_cruise = float(t_val)
                        else:
                            lod_ctrl.dynamic_olod_cruise = float(t_val)
                        config_changed = True

                    if alt_param is not None:
                        a_val = max(500, min(45000, int(round(float(alt_param)))))
                        lod_ctrl.config[f"2d_{ax}_altitude"] = a_val
                        lod_ctrl.config[f"vr_{ax}_altitude"] = a_val
                        config_changed = True

                    if tlod is not None:
                        lod_ctrl.manual_tlod = float(tlod)
                        lod_ctrl.current_tlod_setpoint = float(tlod)
                        if base_param is None:
                            b_fallback = max(0, min(int(round(float(tlod))), 400))
                            lod_ctrl.config["2d_tlod_base"] = b_fallback
                            lod_ctrl.config["vr_tlod_base"] = b_fallback
                            lod_ctrl.dynamic_tlod_floor = float(b_fallback)
                            config_changed = True

                    if olod is not None:
                        lod_ctrl.manual_olod = float(olod)
                        lod_ctrl.current_olod_setpoint = float(olod)
                        if base_param is None:
                            b_fallback = max(0, min(int(round(float(olod))), 300))
                            lod_ctrl.config["2d_olod_base"] = b_fallback
                            lod_ctrl.config["vr_olod_base"] = b_fallback
                            lod_ctrl.dynamic_olod_floor = float(b_fallback)
                            config_changed = True

                    if config_changed:
                        try:
                            with open(flight_lod_controller.CONFIG_FILE_PATH, "w", encoding="utf-8") as cf:
                                json.dump(lod_ctrl.config, cf, indent=4)
                        except Exception:
                            pass

                if disengage_auto and not lod_ctrl.config.get("cloud_recovery", True):
                    lod_ctrl.stop(detach=False)

                _CACHED_LOD_STATUS = dict(lod_ctrl.get_status())
            except Exception:
                pass

            self._send_json(200, res)
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

    def _handle_smart_lod_reset_to_profile(self, params: Dict[str, Any]):
        global _LAST_MANUAL_LOD
        try:
            axis = params.get("axis", "all")
            if axis in ("tlod", "all"):
                _LAST_MANUAL_LOD.pop("tlod", None)
            if axis in ("olod", "all"):
                _LAST_MANUAL_LOD.pop("olod", None)

            res = {"success": True, "axis": axis}
            try:
                import flight_lod_controller
                lod_ctrl = flight_lod_controller.get_smart_lod_controller()
                res = lod_ctrl.reset_to_active_profile(axis)
            except Exception as e:
                print(f"[RemoteServer] Reset to profile error: {e}")

            self._send_json(200, res)
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

    def _handle_smart_lod_reset_override(self, params: Dict[str, Any]):
        return self._handle_smart_lod_reset_to_profile(params)

    def _handle_smart_lod_cloud_recovery(self, params: Dict[str, Any]):
        global _CACHED_LOD_STATUS, _CACHED_ACTIVE_HIGHLIGHTS
        try:
            enabled = None
            if params and "enabled" in params:
                enabled = bool(params["enabled"])
            else:
                parsed = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed.query)
                if "enabled" in query_params:
                    enabled = query_params["enabled"][0].lower() in ("1", "true", "yes", "on")

            if enabled is None:
                length = int(self.headers.get("Content-Length", 0))
                if length > 0:
                    try:
                        body = self.rfile.read(length).decode("utf-8")
                        data = json.loads(body)
                        if "enabled" in data:
                            enabled = bool(data["enabled"])
                    except Exception:
                        pass

            import flight_lod_controller
            lod_ctrl = flight_lod_controller.get_smart_lod_controller()
            if enabled is None:
                enabled = not bool(lod_ctrl.config.get("cloud_recovery", True))

            lod_ctrl.set_cloud_recovery(enabled)
            _CACHED_LOD_STATUS = lod_ctrl.get_status()
            _CACHED_ACTIVE_HIGHLIGHTS = _read_active_settings_highlights()
            calc_q = int(lod_ctrl.current_cloud_quality)
            calc_label = flight_lod_controller.CLOUD_QUALITY_LABELS.get(calc_q, "HIGH")
            print(f"[RemoteServer] Cloud Recovery Toggle: set_cloud_recovery({enabled}) -> cloud_quality={calc_q} ({calc_label})")
            self._send_json(200, {
                "success": True,
                "enabled": enabled,
                "cloud_recovery": enabled,
                "cloud_quality": calc_q,
                "cloud_label": calc_label
            })
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

    def _handle_apply_live_graphics(self, params: Dict[str, Any]):
        global _CACHED_ACTIVE_HIGHLIGHTS, _CACHED_LOD_STATUS
        try:
            import flight_lod_controller
            import flight_memory_engine

            lod_ctrl = flight_lod_controller.get_smart_lod_controller()
            mem = flight_memory_engine.get_memory_engine()
            if mem and not mem.is_attached:
                mem.attach()

            is_vr = bool(mem.is_vr_active()) if (mem and mem.is_attached) else bool(params.get("is_vr", False))
            settings = params.get("settings") if isinstance(params.get("settings"), dict) else params
            if not isinstance(settings, dict):
                settings = {}

            raw_reset = params.get("reset_keys", [])
            if isinstance(raw_reset, str):
                raw_reset = [raw_reset]
            reset_keys = [str(rk) for rk in raw_reset if rk in ("max_fps", "clouds", "precaching", "terrain_shadows", "buildings", "trees", "plants", "grass")]

            clean_settings: Dict[str, int] = {}
            for k in ("max_fps", "clouds", "precaching", "terrain_shadows", "buildings", "trees", "plants", "grass"):
                if k in settings and settings[k] is not None and k not in reset_keys:
                    try:
                        clean_settings[k] = int(settings[k])
                    except Exception:
                        pass

            # Detect whether clouds was modified by the user
            clouds_changed = bool(params.get("clouds_changed", False))
            if not clouds_changed and "clouds" in clean_settings:
                prev_cloud_q = None
                if lod_ctrl and getattr(lod_ctrl, "current_cloud_quality", None) is not None:
                    prev_cloud_q = int(lod_ctrl.current_cloud_quality)
                if prev_cloud_q is None:
                    try:
                        if mem and mem.is_attached and not mem.safe_read_only:
                            prev_cloud_q = mem.read_cloud_quality()
                    except Exception:
                        pass
                if prev_cloud_q is not None and int(prev_cloud_q) != clean_settings["clouds"]:
                    clouds_changed = True

            # 1. Persist live overrides & sync to UserCfg.opt (preserving .profile.json reference for Reset)
            effective_settings = flight_lod_controller.apply_live_graphics_to_profile(
                clean_settings,
                is_vr=is_vr,
                reset_keys=reset_keys,
            )

            # 2. If clouds was changed and Smart LOD Cloud Recovery is active -> automatically turn Cloud Recovery OFF
            cloud_recovery_disabled = False
            if clouds_changed and lod_ctrl:
                lod_ctrl.set_cloud_recovery(False, restore_nominal=False)
                lod_ctrl.current_cloud_quality = max(0, min(3, effective_settings.get("clouds", 2)))
                cloud_recovery_disabled = True
            elif "clouds" in effective_settings and lod_ctrl:
                lod_ctrl.current_cloud_quality = max(0, min(3, effective_settings["clouds"]))

            # 3. Update target FPS in SmartLodController config if max_fps was supplied or reset
            if "max_fps" in effective_settings and lod_ctrl:
                fps_val = max(15, min(240, effective_settings["max_fps"]))
                with lod_ctrl._lock:
                    if is_vr:
                        lod_ctrl.config["vr_target_fps"] = fps_val
                    else:
                        lod_ctrl.config["ifr_target_fps"] = fps_val
                        lod_ctrl.config["vfr_target_fps"] = fps_val
                    try:
                        with open(flight_lod_controller.CONFIG_FILE_PATH, "w", encoding="utf-8") as cf:
                            json.dump(lod_ctrl.config, cf, indent=4)
                    except Exception:
                        pass

            # 4. Write directly to MSFS RAM (Dual-Write 2D + VR)
            ram_results = {}
            if mem and mem.is_attached and not mem.safe_read_only and effective_settings:
                ram_results = mem.write_live_graphics(effective_settings)

            try:
                _CACHED_ACTIVE_HIGHLIGHTS = _compute_active_highlights_snapshot()
                if lod_ctrl:
                    _CACHED_LOD_STATUS = dict(lod_ctrl.get_status())
            except Exception:
                pass

            cur_cr = bool(lod_ctrl.config.get("cloud_recovery", False)) if lod_ctrl else False
            print(f"[RemoteServer] Applied live graphics ({'VR' if is_vr else '2D'}): set={clean_settings} reset={reset_keys} eff={effective_settings} | RAM={ram_results} | CloudRec={cur_cr}")
            self._send_json(200, {
                "success": True,
                "applied": effective_settings,
                "reset_keys": reset_keys,
                "ram_written": ram_results,
                "cloud_recovery": cur_cr,
                "cloud_recovery_auto_disabled": cloud_recovery_disabled
            })
        except Exception as e:
            print(f"[RemoteServer] Error applying live graphics: {e}")
            self._send_json(500, {"success": False, "error": str(e)})

    def _handle_save_pins(self, params: Dict[str, Any]):
        try:
            import flight_lod_controller
            lod_ctrl = flight_lod_controller.get_smart_lod_controller()
            pins = params.get("pins", []) if isinstance(params, dict) else []
            saved = lod_ctrl.set_ingame_pinned_settings(pins) if lod_ctrl else pins[:5]
            self._send_json(200, {"success": True, "pinned_keys": saved})
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

    def _handle_blackbox_toggle(self):
        try:
            import flight_perf_tracker
            if flight_perf_tracker.BLACKBOX.is_running:
                res = flight_perf_tracker.BLACKBOX.stop()
                report_path = (res or {}).get("report_path")
                if report_path and os.path.exists(report_path):
                    try:
                        import webbrowser
                        webbrowser.open(f"file:///{os.path.abspath(report_path)}")
                    except Exception as err:
                        print(f"[RemoteServer] Browser open report notice: {err}")
                self._send_json(200, {"recording": False, "status": "stopped", "res": res})
            else:
                res = flight_perf_tracker.BLACKBOX.start()
                self._send_json(200, {"recording": True, "status": "started", "res": res})
        except Exception as e:
            print(f"[RemoteServer] Blackbox toggle error: {e}")
            self._send_json(500, {"success": False, "error": str(e)})


def start_remote_server(port: int = SERVER_PORT) -> bool:
    """Démarre le micro-serveur REST multi-thread dans un thread d'arrière-plan."""
    global _server_instance, _server_thread, _telemetry_poller_thread
    if _server_instance is not None:
        return True

    try:
        _telemetry_poller_stop.clear()
        if _telemetry_poller_thread is None or not _telemetry_poller_thread.is_alive():
            _telemetry_poller_thread = threading.Thread(
                target=_panel_telemetry_background_loop,
                daemon=True,
                name="SceneryXPanelTelemetryPoller"
            )
            _telemetry_poller_thread.start()

        try:
            _server_instance = DualStackThreadingServer(("::", port), RemoteApiHandler)
        except Exception:
            _server_instance = DualStackThreadingServer(("", port), RemoteApiHandler)
        _server_thread = threading.Thread(target=_server_instance.serve_forever, daemon=True, name="SceneryXRemoteServer")
        _server_thread.start()
        print(f"[RemoteServer] Micro-serveur In-Game multi-thread démarré sur port {port} (Dual-Stack IPv4/IPv6)")
        return True
    except Exception as e:
        print(f"[RemoteServer] Erreur lors du démarrage du micro-serveur: {e}")
        _server_instance = None
        _server_thread = None
        return False


def stop_remote_server():
    """Arrête le micro-serveur REST."""
    global _server_instance, _server_thread, _telemetry_poller_thread
    _telemetry_poller_stop.set()
    if _server_instance:
        try:
            _server_instance.shutdown()
            _server_instance.server_close()
        except Exception:
            pass
        _server_instance = None
        _server_thread = None
        print("[RemoteServer] Micro-serveur arrêté.")


if __name__ == "__main__":
    import time
    start_remote_server()
    print("Serveur en cours d'exécution. Appuyez sur Ctrl+C pour stopper.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_remote_server()
