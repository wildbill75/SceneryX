#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SceneryX Smart LOD - Dynamic Performance Controller
Boucle d'asservissement en temps réel pour l'ajustement dynamique du TLOD,
de l'OLOD et des nuages selon la télémétrie de vol et le framerate cible.
"""

import os
import sys
import time
import json
import threading
from typing import Dict, Any, Optional

from flight_memory_engine import get_memory_engine, FlightMemoryEngine

def get_user_data_dir():
    appdata = os.environ.get('APPDATA')
    if not appdata:
        appdata = os.path.expanduser('~')
    user_dir = os.path.join(appdata, 'SceneryX')
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

CONFIG_FILE_PATH = os.path.join(get_user_data_dir(), "smart_lod_config.json")

DEFAULT_CONFIG = {
    "enabled": False,
    "mode": "IFR",               # "IFR" (Airliner) ou "VFR" (GA)
    "source": "native",          # "native" (Smart LOD) ou "external_autofps" ou "manual"
    "auto_kill_autofps": False,  # Fermer automatiquement AutoFPS au démarrage
    
    # Paramètres IFR
    "ifr_tlod_ground": 100,      # TLOD au sol / approche (Min)
    "ifr_tlod_cruise": 250,      # TLOD en croisière (Max)
    "ifr_alt_transition": 5000,  # Altitude AGL de pleine transition (ft)
    "ifr_olod_ground": 100,      # OLOD au sol
    "ifr_olod_cruise": 50,       # OLOD en croisière
    "ifr_target_fps": 40,        # FPS cible de rendu natif (base FPS)
    
    # Paramètres VFR
    "vfr_tlod_ground": 120,
    "vfr_tlod_cruise": 300,
    "vfr_alt_transition": 3000,
    "vfr_olod_ground": 120,
    "vfr_olod_cruise": 80,
    "vfr_target_fps": 40,
    
    # Options avancées
    "cloud_recovery": True,      # Réduction temporaire des nuages si saturation GPU
    "step_size": 5,              # Pas d'ajustement par seconde (lissage anti-stutter)
    "deadband_fps": 2            # Marge de tolérance (±2 FPS)
}


class SmartLodController:
    """
    Contrôleur daemon gérant l'algorithme d'asservissement de Smart LOD.
    """

    def __init__(self):
        self.config: Dict[str, Any] = self._load_config()
        self.engine: FlightMemoryEngine = get_memory_engine()
        self._lock = threading.Lock()
        
        # État courant
        self.is_running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Télémétrie interne et lissage
        self.current_tlod_setpoint: float = 100.0
        self.current_olod_setpoint: float = 100.0
        self.last_adjustment_time: float = 0.0
        self.status_message: str = "Prêt (Inactif)"
        self.in_cloud_reduction: bool = False
        self.original_cloud_quality: Optional[int] = None

        if self.config.get("enabled", False):
            if self.config.get("auto_kill_autofps", False):
                is_af_running, _ = self.engine.is_autofps_running()
                if is_af_running:
                    print("[SmartLOD] Auto-terminating external AutoFPS based on user preference...")
                    self.engine.kill_autofps_process()
            self.start()

    # ================= CONFIG PERSISTENCE =================

    def _load_config(self) -> Dict[str, Any]:
        cfg = DEFAULT_CONFIG.copy()
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    cfg.update(saved)
            except Exception as e:
                print(f"[SmartLOD] Erreur lecture config: {e}")
        return cfg

    def save_config(self, new_config: Dict[str, Any]) -> bool:
        with self._lock:
            self.config.update(new_config)
            try:
                with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4)
                return True
            except Exception as e:
                print(f"[SmartLOD] Erreur sauvegarde config: {e}")
                return False

    def get_config(self) -> Dict[str, Any]:
        with self._lock:
            return self.config.copy()

    # ================= LIFECYCLE MANAGEMENT =================

    def start(self):
        """Démarre la boucle de régulation daemon."""
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="SmartLodController")
        self._thread.start()
        print("[SmartLOD] Moteur de régulation démarré.")

    def stop(self):
        """Arrête la boucle de régulation."""
        if not self.is_running:
            return
        self.is_running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        self._thread = None
        self.engine.detach()
        print("[SmartLOD] Moteur de régulation arrêté.")

    def set_enabled(self, enabled: bool, force_kill_autofps: bool = False) -> Dict[str, Any]:
        """Active ou désactive Smart LOD avec arbitrage de conflit AutoFPS."""
        if enabled:
            # Vérifier si AutoFPS externe tourne
            af_running, pid = self.engine.is_autofps_running()
            if af_running:
                if force_kill_autofps:
                    killed = self.engine.kill_autofps_process()
                    if not killed:
                        return {
                            "success": False,
                            "conflict": True,
                            "message": "Impossible de fermer le processus externe AutoFPS."
                        }
                else:
                    return {
                        "success": False,
                        "conflict": True,
                        "autofps_pid": pid,
                        "message": "AutoFPS externe est actif. Conflit détecté."
                    }

            self.save_config({"enabled": True, "source": "native"})
            self.start()
            return {"success": True, "conflict": False, "enabled": True}
        else:
            self.save_config({"enabled": False})
            self.stop()
            return {"success": True, "conflict": False, "enabled": False}

    # ================= REGULATION ALGORITHM =================

    def _worker_loop(self):
        """Boucle de travail principale exécutée à ~1 Hz."""
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception as e:
                self.status_message = f"Erreur régulation: {e}"
            time.sleep(1.0)

    def _tick(self):
        if not self.config.get("enabled", False):
            self.status_message = "Désactivé"
            return

        # 1. Vérifier la présence d'AutoFPS externe
        af_running, _ = self.engine.is_autofps_running()
        if af_running:
            if self.config.get("auto_kill_autofps", False):
                self.engine.kill_autofps_process()
            else:
                self.status_message = "En pause (AutoFPS externe détecté en arrière-plan)"
                return

        # 2. Vérifier l'attachement à MSFS
        if not self.engine.is_attached:
            attached = self.engine.attach()
            if not attached:
                self.status_message = self.engine.last_attach_error or "En attente du lancement de MSFS..."
                return

        if self.engine.safe_read_only:
            self.status_message = "Mode Sécurité : Read-Only (écriture désactivée)"
            return

        # 3. Récupérer la télémétrie de vol depuis flight_perf_tracker
        telemetry = self._get_live_flight_telemetry()
        agl = telemetry.get("agl_ft", 0) or 0
        on_ground = telemetry.get("on_ground", False)
        base_fps = telemetry.get("base_fps", 0) or telemetry.get("displayed_fps", 0) or 0
        
        mode = self.config.get("mode", "IFR")
        tlod_ground = self.config.get(f"{mode.lower()}_tlod_ground", 100)
        tlod_cruise = self.config.get(f"{mode.lower()}_tlod_cruise", 250)
        alt_trans = self.config.get(f"{mode.lower()}_alt_transition", 5000)
        target_fps = self.config.get(f"{mode.lower()}_target_fps", 40)
        deadband = self.config.get("deadband_fps", 2)
        step = self.config.get("step_size", 5)

        # 4. Calcul de la consigne d'altitude (Interpolation Sol -> Croisière)
        if on_ground or agl < 500:
            altitude_target_tlod = float(tlod_ground)
        elif agl >= alt_trans:
            altitude_target_tlod = float(tlod_cruise)
        else:
            # Interpolation linéaire douce
            ratio = max(0.0, min(1.0, (agl - 500) / max(1, alt_trans - 500)))
            altitude_target_tlod = tlod_ground + ratio * (tlod_cruise - tlod_ground)

        # 5. Ajustement selon le framerate réel (si en vol et FPS disponible)
        target_tlod = altitude_target_tlod
        if base_fps > 0 and agl >= 1000:
            if base_fps < (target_fps - deadband):
                # Sous-performance : Baisse du TLOD
                deficit = (target_fps - base_fps)
                target_tlod = max(tlod_ground, self.current_tlod_setpoint - (step * (deficit / 3.0)))
            elif base_fps > (target_fps + deadband):
                # Marge de performance : Remontée progressive
                target_tlod = min(altitude_target_tlod, self.current_tlod_setpoint + step)

        # 6. Lissage progressif anti-saccades (Max step par cycle)
        delta = target_tlod - self.current_tlod_setpoint
        if abs(delta) > step:
            delta = step if delta > 0 else -step
        self.current_tlod_setpoint += delta
        self.current_tlod_setpoint = max(float(tlod_ground), min(float(tlod_cruise), self.current_tlod_setpoint))

        # 7. Écriture en mémoire
        ok = self.engine.write_tlod(self.current_tlod_setpoint)
        
        # 8. Gestion de l'Object LOD (OLOD)
        olod_ground = self.config.get(f"{mode.lower()}_olod_ground", 100)
        olod_cruise = self.config.get(f"{mode.lower()}_olod_cruise", 50)
        if agl >= alt_trans:
            target_olod = float(olod_cruise)
        else:
            ratio = max(0.0, min(1.0, agl / max(1, alt_trans)))
            target_olod = olod_ground - ratio * (olod_ground - olod_cruise)
        self.engine.write_olod(target_olod)

        if ok:
            self.status_message = f"Actif • TLOD {round(self.current_tlod_setpoint)} • {mode} ({round(base_fps)} FPS)"
        else:
            self.status_message = "Erreur d'écriture mémoire"

    def _get_live_flight_telemetry(self) -> Dict[str, Any]:
        """Extrait la télémétrie courante de SimConnect ou du tracker de SceneryX."""
        try:
            import flight_perf_tracker
            # Récupération depuis le cache du tracker si disponible
            if hasattr(flight_perf_tracker, '_last_telemetry_cache') and flight_perf_tracker._last_telemetry_cache:
                c = flight_perf_tracker._last_telemetry_cache
                return {
                    "agl_ft": c.get("agl_ft") or c.get("agl") or 0,
                    "on_ground": (c.get("agl_ft") or 0) < 50,
                    "base_fps": c.get("base_fps") or c.get("displayed_fps") or 0,
                    "displayed_fps": c.get("displayed_fps") or 0
                }
        except Exception:
            pass
        return {"agl_ft": 0, "on_ground": True, "base_fps": 0, "displayed_fps": 0}

    # ================= STATUS API =================

    def get_status(self) -> Dict[str, Any]:
        """Retourne l'état complet pour l'UI Web."""
        mem_status = self.engine.get_status()
        is_af_running, af_pid = self.engine.is_autofps_running()
        
        return {
            "enabled": self.config.get("enabled", False),
            "is_running": self.is_running,
            "status_message": self.status_message,
            "current_tlod_setpoint": round(self.current_tlod_setpoint, 1),
            "current_olod_setpoint": round(self.current_olod_setpoint, 1),
            "mode": self.config.get("mode", "IFR"),
            "source": self.config.get("source", "native"),
            "autofps_conflict": is_af_running,
            "autofps_pid": af_pid,
            "memory": mem_status,
            "config": self.config
        }


# Instance singleton globale
_global_controller: Optional[SmartLodController] = None

def get_smart_lod_controller() -> SmartLodController:
    global _global_controller
    if _global_controller is None:
        _global_controller = SmartLodController()
    return _global_controller


if __name__ == "__main__":
    print("=== Test SceneryX Smart LOD Controller ===")
    ctrl = SmartLodController()
    print("Status:", ctrl.get_status())
