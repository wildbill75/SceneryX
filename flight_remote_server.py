#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SceneryX - Micro-Serveur HTTP REST Local pour In-Game Toolbar Panel MSFS.
Fournit une API locale ultra-légère (127.0.0.1:8383) pour la communication
entre le simulateur (CoherentGT) et SceneryX en vol.
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any

SERVER_PORT = 8383
_server_instance: Optional[HTTPServer] = None
_server_thread: Optional[threading.Thread] = None


class RemoteApiHandler(BaseHTTPRequestHandler):
    """Handler HTTP REST léger avec support CORS pour CoherentGT."""

    def log_message(self, format, *args):
        # Silence standard HTTP logs to avoid cluttering console
        pass

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/telemetry":
            self._handle_get_telemetry()
        elif self.path == "/api/status":
            self._send_json(200, {"status": "ok", "app": "SceneryX"})
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/api/smart_lod/toggle":
            self._handle_smart_lod_toggle()
        elif self.path == "/api/blackbox/toggle":
            self._handle_blackbox_toggle()
        else:
            self._send_json(404, {"error": "Not found"})

    def _send_json(self, status_code: int, data: Dict[str, Any]):
        try:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            pass

    def _handle_get_telemetry(self):
        telemetry_data = {
            "connected": False,
            "displayed_fps": None,
            "base_fps": None,
            "main_thread_ms": None,
            "msfs_vram_mb": None,
            "vram_total_mb": None,
            "cache_read_mbps": 0.0,
            "is_tracking": False,
            "elapsed_str": "00:00:00",
            "smart_lod_enabled": False,
            "smart_lod_running": False,
            "smart_lod_tlod": None,
            "smart_lod_status": "Inactif"
        }

        # 1. Tracker telemetry
        try:
            import flight_perf_tracker
            tracker = flight_perf_tracker.get_perf_tracker()
            telem = tracker.get_live_telemetry()
            telemetry_data.update({
                "connected": telem.get("simconnect_connected", False),
                "displayed_fps": telem.get("displayed_fps"),
                "base_fps": telem.get("base_fps"),
                "main_thread_ms": telem.get("main_thread_ms"),
                "msfs_vram_mb": telem.get("msfs_vram_mb"),
                "vram_total_mb": telem.get("vram_used_mb"),
                "cache_read_mbps": telem.get("cache_read_mbps", 0.0),
                "is_tracking": telem.get("is_tracking", False),
                "elapsed_str": telem.get("elapsed_str", "00:00:00")
            })
        except Exception:
            pass

        # 2. Smart LOD status
        try:
            import flight_lod_controller
            lod_ctrl = flight_lod_controller.get_smart_lod_controller()
            lod_status = lod_ctrl.get_status()
            telemetry_data.update({
                "smart_lod_enabled": lod_status.get("enabled", False),
                "smart_lod_running": lod_status.get("is_running", False),
                "smart_lod_tlod": lod_status.get("current_tlod_setpoint"),
                "smart_lod_status": lod_status.get("status_message", "Prêt")
            })
        except Exception:
            pass

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

    def _handle_blackbox_toggle(self):
        try:
            import flight_perf_tracker
            tracker = flight_perf_tracker.get_perf_tracker()
            if tracker.is_tracking:
                res = tracker.stop_flight_tracking()
                self._send_json(200, {"is_tracking": False, "result": res})
            else:
                res = tracker.start_flight_tracking()
                self._send_json(200, {"is_tracking": True, "result": res})
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})


def start_remote_server(port: int = SERVER_PORT) -> bool:
    """Démarre le micro-serveur REST en arrière-plan."""
    global _server_instance, _server_thread
    if _server_instance is not None:
        return True

    try:
        _server_instance = HTTPServer(("127.0.0.1", port), RemoteApiHandler)
        _server_thread = threading.Thread(target=_server_instance.serve_forever, daemon=True, name="SceneryXRemoteServer")
        _server_thread.start()
        print(f"[RemoteServer] Micro-serveur In-Game démarré sur http://127.0.0.1:{port}")
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
