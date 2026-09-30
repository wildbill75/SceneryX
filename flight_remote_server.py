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
_LAST_MANUAL_LOD: Dict[str, float] = {"tlod": 100.0, "olod": 100.0}


class ThreadingSimpleServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


import urllib.parse

class RemoteApiHandler(SimpleHTTPRequestHandler):
    """Handler HTTP REST multi-thread avec support CORS complet pour CoherentGT."""

    def log_message(self, format, *args):
        # Silence standard HTTP logs to avoid cluttering console
        pass

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        clean_path = parsed.path
        if clean_path == "/api/telemetry":
            self._handle_get_telemetry()
        elif clean_path == "/api/status":
            self._send_json(200, {"status": "ok", "app": "SceneryX"})
        elif clean_path == "/api/smart_lod/set_lod":
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
        elif clean_path == "/api/smart_lod/reset_override":
            query_params = urllib.parse.parse_qs(parsed.query)
            axis = query_params.get("axis", ["all"])[0]
            self._handle_smart_lod_reset_override({"axis": axis})
        else:
            self._send_json(404, {"error": "Not found", "path": self.path})

    def do_POST(self):
        clean_path = self.path.split("?")[0]
        if clean_path == "/api/smart_lod/toggle":
            self._handle_smart_lod_toggle()
        elif clean_path == "/api/smart_lod/set_lod":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
                params = json.loads(body)
            except Exception:
                params = {}
            self._handle_smart_lod_set_lod(params)
        elif clean_path == "/api/smart_lod/reset_override":
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
            self._handle_smart_lod_reset_override(params)
        elif clean_path == "/api/blackbox/toggle":
            self._handle_blackbox_toggle()
        else:
            self._send_json(404, {"error": "Not found", "path": self.path})

    def _send_json(self, status_code: int, data: Dict[str, Any]):
        try:
            body = json.dumps(data, ensure_ascii=True).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            print(f"[RemoteServer] Error sending JSON: {e}")

    def _handle_get_telemetry(self):
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
        if cur_olod is None and _LAST_MANUAL_LOD.get("olod") is not None:
            cur_olod = _LAST_MANUAL_LOD["olod"]
        if cur_tlod is None and _LAST_MANUAL_LOD.get("tlod") is not None:
            cur_tlod = _LAST_MANUAL_LOD["tlod"]

        # Try direct memory engine read if available and not manually set
        try:
            import flight_memory_engine
            mem = flight_memory_engine.get_memory_engine()
            if mem.is_attached and not mem.safe_read_only:
                mem_tlod = mem.read_tlod()
                mem_olod = mem.read_olod()
                if mem_tlod is not None and cur_tlod is None:
                    cur_tlod = mem_tlod
                if mem_olod is not None and cur_olod is None:
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

        smart_lod_enabled = bool(lod_status.get("enabled", False))
        smart_lod_running = bool(lod_status.get("is_running", False))
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

        tlod_is_manual = bool(getattr(lod_ctrl, "manual_tlod", None) is not None or "tlod" in _LAST_MANUAL_LOD)
        olod_is_manual = bool(getattr(lod_ctrl, "manual_olod", None) is not None or "olod" in _LAST_MANUAL_LOD)

        telemetry_data = {
            "app_running": True,
            "connected": True,
            "sim_connected": bool(telem.get("simconnect_connected", False)),
            "msfs_active": bool(telem.get("msfs_active", False)),
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
                "current_tlod": cur_tlod if cur_tlod is not None else 100,
                "current_olod": cur_olod if cur_olod is not None else 100,
                "tlod_manual": tlod_is_manual,
                "olod_manual": olod_is_manual,
                "status": status_msg
            },
            "vram_used_gb": vram_used_gb,
            "vram_total_gb": vram_total_gb,
            "rolling_cache_gb": round(cache_mbps, 1),
            "blackbox_recording": is_tracking,
            # Flat fields for direct compatibility
            "displayed_fps": disp_fps,
            "base_fps": base_fps,
            "main_thread_ms": mt_ms,
            "smart_lod_enabled": smart_lod_enabled,
            "smart_lod_running": smart_lod_running,
            "smart_lod_tlod": cur_tlod if cur_tlod is not None else 100,
            "smart_lod_olod": cur_olod if cur_olod is not None else 100,
            "smart_lod_tlod_manual": tlod_is_manual,
            "smart_lod_olod_manual": olod_is_manual,
            "smart_lod_status": status_msg
        }

        self._send_json(200, telemetry_data)

    def _handle_smart_lod_toggle(self):
        try:
            import flight_lod_controller
            lod_ctrl = flight_lod_controller.get_smart_lod_controller()
            current_status = lod_ctrl.get_status()
            new_state = not current_status.get("enabled", False)
            res = lod_ctrl.set_enabled(new_state, force_kill_autofps=True)
            self._send_json(200, res)
        except Exception as e:
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

    def _handle_smart_lod_reset_override(self, params: Dict[str, Any]):
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
                res = lod_ctrl.reset_manual_override(axis)
            except Exception as e:
                print(f"[RemoteServer] Reset override error: {e}")

            self._send_json(200, res)
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

    def _handle_blackbox_toggle(self):
        try:
            import flight_perf_tracker
            if flight_perf_tracker.BLACKBOX.is_running:
                res = flight_perf_tracker.BLACKBOX.stop()
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
        _server_instance = ThreadingSimpleServer(("", port), RemoteApiHandler)
        _server_thread = threading.Thread(target=_server_instance.serve_forever, daemon=True, name="SceneryXRemoteServer")
        _server_thread.start()
        print(f"[RemoteServer] Micro-serveur In-Game multi-thread démarré sur port {port}")
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
