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
_LAST_MANUAL_LOD: Dict[str, float] = {}


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
            # 1. Performance Tracker Telemetry
            telem = {}
            try:
                import flight_perf_tracker
                telem = flight_perf_tracker.BLACKBOX.get_telemetry() or {}
            except Exception as e:
                print(f"[RemoteServer] Telemetry error: {e}")

            # 2. Smart LOD Status
            lod_status = {}
            cur_tlod = None
            cur_olod = None
            lod_ctrl = None
            mem = None
            try:
                import flight_lod_controller
                lod_ctrl = flight_lod_controller.get_smart_lod_controller()
                lod_status = lod_ctrl.get_status() or {}
                cur_tlod = lod_status.get("current_tlod_setpoint")
                cur_olod = lod_status.get("current_olod_setpoint")
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
                import flight_memory_engine
                mem = flight_memory_engine.get_memory_engine()
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

            # Frame pacing evaluation
            if base_fps and base_fps >= 35:
                pacing = "OPTIMAL"
            elif base_fps and base_fps >= 25:
                pacing = "ACCEPTABLE"
            elif base_fps:
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

            gpu_util = telem.get("gpu_util_pct", 0)
            gpu_temp = telem.get("gpu_temp_c", 0)
            if not gpu_temp:
                try:
                    import flight_perf_tracker
                    nv = flight_perf_tracker.get_nvidia_gpu_telemetry()
                    gpu_temp = nv.get("gpu_temp_c", 0)
                    if not gpu_util:
                        gpu_util = nv.get("gpu_util_pct", 0)
                except Exception:
                    pass
            cpu_util = telem.get("cpu_pct") or telem.get("msfs_cpu_pct") or 0
            if not cpu_util:
                try:
                    import psutil
                    cpu_util = round(psutil.cpu_percent(interval=None), 1)
                except Exception:
                    pass
            cpu_temp = telem.get("cpu_temp_c")
            if not cpu_temp:
                try:
                    import flight_perf_tracker
                    cpu_temp = flight_perf_tracker.get_cpu_temperature_c(cpu_util)
                except Exception:
                    cpu_temp = 0

            telemetry_data = {
                "app_running": True,
                "connected": True,
                "sim_connected": bool(telem.get("simconnect_connected", False)),
                "msfs_active": bool(telem.get("msfs_active", False)),
                "is_vr": is_vr_mode,
                "agl_ft": telem.get("agl_ft") or 0,
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
                    "tlod_altitude": axis_state.get("tlod_altitude", 5000),
                    "olod_base": olod_floor,
                    "olod_target": olod_cruise,
                    "olod_altitude": axis_state.get("olod_altitude", 3000),
                    "cloud_recovery": bool(lod_ctrl.config.get("cloud_recovery", True)) if lod_ctrl else True,
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
                "smart_lod_cloud_recovery": bool(lod_ctrl.config.get("cloud_recovery", True)) if lod_ctrl else True
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
                "smart_lod": {"active": False, "enabled": False, "running": False, "current_tlod": 100, "current_olod": 100, "cloud_recovery": False},
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
                "error": str(e)
            }
            self._send_json(200, fallback_data)

    def _handle_smart_lod_toggle(self, params: Optional[Dict[str, Any]] = None):
        global _LAST_MANUAL_LOD
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
            print(f"[RemoteServer] Smart LOD Toggle: set_enabled({new_state}) -> {res}")
            self._send_json(200, res)
        except Exception as e:
            print(f"[RemoteServer] Smart LOD Toggle Error: {e}")
            self._send_json(500, {"success": False, "error": str(e)})

    def _handle_smart_lod_set_lod(self, params: Dict[str, Any]):
        global _LAST_MANUAL_LOD
        try:
            tlod = params.get("tlod")
            olod = params.get("olod")
            res = {"success": True}

            import flight_memory_engine
            mem = flight_memory_engine.get_memory_engine()
            if not mem.is_attached:
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

            # Also update Smart LOD controller setpoints and manual overrides
            try:
                import flight_lod_controller
                lod_ctrl = flight_lod_controller.get_smart_lod_controller()
                if tlod is not None:
                    lod_ctrl.manual_tlod = float(tlod)
                    lod_ctrl.current_tlod_setpoint = float(tlod)
                if olod is not None:
                    lod_ctrl.manual_olod = float(olod)
                    lod_ctrl.current_olod_setpoint = float(olod)
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
            print(f"[RemoteServer] Cloud Recovery Toggle: set_cloud_recovery({enabled})")
            self._send_json(200, {"success": True, "enabled": enabled, "cloud_recovery": enabled})
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
    global _server_instance, _server_thread
    if _server_instance is not None:
        return True

    try:
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
    global _server_instance, _server_thread
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
