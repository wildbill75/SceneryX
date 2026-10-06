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
import glob
from datetime import datetime
from typing import List
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
    "external_autofps": False,   # Si True, délègue totalement à MSFS_AutoFPS.exe
    
    # 2D Independent LOD Axis
    "2d_tlod_active": False,
    "2d_tlod_base": 100,
    "2d_tlod_target": 200,
    "2d_tlod_altitude": 5000,
    "2d_olod_active": False,
    "2d_olod_base": 100,
    "2d_olod_target": 100,
    "2d_olod_altitude": 3000,
    
    # VR Independent LOD Axis
    "vr_tlod_active": False,
    "vr_tlod_base": 90,
    "vr_tlod_target": 150,
    "vr_tlod_altitude": 4000,
    "vr_olod_active": False,
    "vr_olod_base": 80,
    "vr_olod_target": 80,
    "vr_olod_altitude": 2500,
    
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
    
    # Paramètres VR (Stéréo HMD Cadence)
    "vr_tlod_ground": 90,
    "vr_tlod_cruise": 200,
    "vr_alt_transition": 4000,
    "vr_olod_ground": 100,
    "vr_olod_cruise": 50,
    "vr_target_fps": 36,
    
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
        self.manual_olod: Optional[float] = None
        self.manual_tlod: Optional[float] = None
        self.last_adjustment_time: float = 0.0
        self.status_message: str = "Ready (Standby)"
        self.in_cloud_reduction: bool = False
        self.original_cloud_quality: Optional[int] = None
        self.trigger_events: List[Dict[str, Any]] = []
        self._last_logged_tlod: Optional[float] = None
        self._last_phase: str = "ground"

        if self.config.get("enabled", False):
            if self.config.get("auto_kill_autofps", False):
                is_af_running, _ = self.engine.is_autofps_running()
                if is_af_running:
                    print("[SmartLOD] Auto-terminating external AutoFPS based on user preference...")
                    self.engine.kill_autofps_process()
            self.start()

    def get_trigger_events(self, clear: bool = False) -> List[Dict[str, Any]]:
        with self._lock:
            events = list(self.trigger_events)
            if clear:
                self.trigger_events.clear()
            return events

    def reset_to_active_profile(self, axis: str = "all") -> Dict[str, Any]:
        """
        Recalibre immédiatement les curseurs et la mémoire MSFS sur les valeurs nominales du profil actif,
        en supprimant tout débrayage manuel ou temporaire.
        """
        nom_tlod = 100.0
        nom_olod = 100.0
        profile_name = "Active Profile"
        try:
            import flight_rig_optimizer
            snap = flight_rig_optimizer.get_active_profile_snapshot()
            profile_name = snap.get("name", "Active Profile")
            hl = snap.get("highlights", {})
            if "Terrain LOD (TLOD)" in hl:
                val_str = str(hl["Terrain LOD (TLOD)"]).replace("%", "").strip()
                try:
                    nom_tlod = float(val_str)
                except ValueError:
                    pass
            if "Objects LOD (OLOD)" in hl:
                val_str = str(hl["Objects LOD (OLOD)"]).replace("%", "").strip()
                try:
                    nom_olod = float(val_str)
                except ValueError:
                    pass
        except Exception as e:
            print(f"[SmartLOD] Erreur lecture snapshot profil actif: {e}")

        with self._lock:
            if axis in ("tlod", "all"):
                self.manual_tlod = None
                self.current_tlod_setpoint = float(nom_tlod)
            if axis in ("olod", "all"):
                self.manual_olod = None
                self.current_olod_setpoint = float(nom_olod)

        if not self.engine.is_attached:
            self.engine.attach()

        if self.engine.is_attached and not self.engine.safe_read_only:
            if axis in ("tlod", "all"):
                self.engine.write_tlod(nom_tlod)
            if axis in ("olod", "all"):
                self.engine.write_olod(nom_olod)

        print(f"[SmartLOD] Reset to active profile '{profile_name}': TLOD={nom_tlod}, OLOD={nom_olod}")
        return {
            "success": True,
            "axis": axis,
            "reset_to_profile": True,
            "profile_name": profile_name,
            "manual_tlod": False,
            "manual_olod": False,
            "current_tlod": round(self.current_tlod_setpoint, 1),
            "current_olod": round(self.current_olod_setpoint, 1)
        }

    def reset_manual_override(self, axis: str = "all") -> Dict[str, Any]:
        """Réengage les limitations d'altitude et l'automatisation en réinitialisant sur le profil actif."""
        return self.reset_to_active_profile(axis)

    def get_axis_state(self, mode: str = "2D") -> Dict[str, Any]:
        with self._lock:
            pfx = "vr" if str(mode).upper() == "VR" else "2d"
            return {
                "mode": pfx.upper(),
                "external_autofps": bool(self.config.get("external_autofps", False)),
                "tlod_active": bool(self.config.get(f"{pfx}_tlod_active", False)),
                "tlod_base": int(self.config.get(f"{pfx}_tlod_base", 100 if pfx == "2d" else 90)),
                "tlod_target": int(self.config.get(f"{pfx}_tlod_target", 200 if pfx == "2d" else 150)),
                "tlod_altitude": int(self.config.get(f"{pfx}_tlod_altitude", 5000 if pfx == "2d" else 4000)),
                "olod_active": bool(self.config.get(f"{pfx}_olod_active", False)),
                "olod_base": int(self.config.get(f"{pfx}_olod_base", 100 if pfx == "2d" else 80)),
                "olod_target": int(self.config.get(f"{pfx}_olod_target", 100 if pfx == "2d" else 80)),
                "olod_altitude": int(self.config.get(f"{pfx}_olod_altitude", 3000 if pfx == "2d" else 2500)),
            }

    def set_axis_state(self, mode: str, axis: str, enabled: Optional[bool] = None, target: Optional[int] = None, altitude: Optional[int] = None, base: Optional[int] = None) -> Dict[str, Any]:
        with self._lock:
            pfx = "vr" if str(mode).upper() == "VR" else "2d"
            ax = "olod" if "olod" in str(axis).lower() else "tlod"
            
            if enabled is not None:
                self.config[f"{pfx}_{ax}_active"] = bool(enabled)
            max_v = 400 if ax == "tlod" else 300
            if base is not None:
                self.config[f"{pfx}_{ax}_base"] = max(0, min(int(base), max_v))
            if target is not None:
                self.config[f"{pfx}_{ax}_target"] = max(0, min(int(target), max_v))
            if altitude is not None:
                self.config[f"{pfx}_{ax}_altitude"] = max(0, int(altitude))
                
            any_active = any([
                self.config.get("2d_tlod_active", False),
                self.config.get("2d_olod_active", False),
                self.config.get("vr_tlod_active", False),
                self.config.get("vr_olod_active", False),
            ])
            self.config["enabled"] = any_active and not self.config.get("external_autofps", False)
            try:
                with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4)
            except Exception as e:
                print(f"[SmartLOD] Erreur sauvegarde config: {e}")
                
        if self.config.get("enabled"):
            self.start()
            try:
                self._tick()
            except Exception:
                pass
        else:
            if not any_active:
                self.stop()
                
        return self.get_axis_state(mode)

    def set_external_autofps(self, enabled: bool) -> bool:
        with self._lock:
            self.config["external_autofps"] = bool(enabled)
            if enabled:
                self.config["enabled"] = False
                self.config["source"] = "external_autofps"
            else:
                self.config["source"] = "native"
                any_active = any([
                    self.config.get("2d_tlod_active", False),
                    self.config.get("2d_olod_active", False),
                    self.config.get("vr_tlod_active", False),
                    self.config.get("vr_olod_active", False),
                ])
                self.config["enabled"] = any_active
            try:
                with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4)
            except Exception as e:
                print(f"[SmartLOD] Erreur sauvegarde config: {e}")
        if enabled:
            self.stop()
        elif self.config.get("enabled"):
            self.start()
        return True

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
            # Réinitialiser les débrayages manuels pour reprendre la régulation automatique immédiate
            with self._lock:
                self.manual_tlod = None
                self.manual_olod = None

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
            # Forcer un premier tick de régulation immédiat
            try:
                self._tick()
            except Exception:
                pass
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
        if not self.config.get("enabled", False) or self.config.get("external_autofps", False):
            self.status_message = "Handled by External AutoFPS" if self.config.get("external_autofps", False) else "Désactivé"
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

        # 3. Mode et activation des axes indépendants
        is_vr = self.engine.is_vr_active() if self.engine.is_attached else False
        pfx = "vr" if is_vr else "2d"
        tlod_is_active = bool(self.config.get(f"{pfx}_tlod_active", False))
        olod_is_active = bool(self.config.get(f"{pfx}_olod_active", False))

        if not tlod_is_active and not olod_is_active:
            self.status_message = f"Standby (No {pfx.upper()} LOD axis active)"
            return

        # Récupérer la télémétrie de vol depuis flight_perf_tracker
        telemetry = self._get_live_flight_telemetry()
        agl = telemetry.get("agl_ft", 0) or 0
        on_ground = telemetry.get("on_ground", False)
        base_fps = telemetry.get("base_fps", 0) or telemetry.get("displayed_fps", 0) or 0

        target_fps = self.config.get("vr_target_fps", 36) if is_vr else self.config.get("2d_target_fps", self.config.get("ifr_target_fps", 40))
        deadband = self.config.get("deadband_fps", 2)
        step = self.config.get("step_size", 5)

        ok_tlod = True
        ok_olod = True

        # 4. Gestion indépendante du Terrain LOD (TLOD) si activé
        if tlod_is_active:
            tlod_cruise = float(self.config.get(f"{pfx}_tlod_target", 200 if pfx == "2d" else 150))
            tlod_ground = float(self.config.get(f"{pfx}_tlod_base", 100 if pfx == "2d" else 90))
            alt_trans = float(self.config.get(f"{pfx}_tlod_altitude", 5000 if pfx == "2d" else 4000))

            if getattr(self, "manual_tlod", None) is not None:
                self.current_tlod_setpoint = float(self.manual_tlod)
            else:
                if on_ground or agl < 500:
                    altitude_target_tlod = float(tlod_ground)
                elif agl >= alt_trans:
                    altitude_target_tlod = float(tlod_cruise)
                else:
                    ratio = max(0.0, min(1.0, (agl - 500) / max(1.0, alt_trans - 500)))
                    altitude_target_tlod = tlod_ground + ratio * (tlod_cruise - tlod_ground)

                target_tlod = altitude_target_tlod
                if base_fps > 0 and agl >= 1000:
                    if base_fps < (target_fps - deadband):
                        deficit = (target_fps - base_fps)
                        target_tlod = max(tlod_ground, self.current_tlod_setpoint - (step * (deficit / 3.0)))
                    elif base_fps > (target_fps + deadband):
                        target_tlod = min(altitude_target_tlod, self.current_tlod_setpoint + step)

                delta = target_tlod - self.current_tlod_setpoint
                if abs(delta) > step:
                    delta = step if delta > 0 else -step
                self.current_tlod_setpoint += delta
                self.current_tlod_setpoint = max(0.0, min(400.0, self.current_tlod_setpoint))

            ok_tlod = self.engine.write_tlod(self.current_tlod_setpoint)

        # 5. Gestion indépendante de l'Object LOD (OLOD) si activé
        if olod_is_active:
            olod_cruise = float(self.config.get(f"{pfx}_olod_target", 100 if pfx == "2d" else 80))
            olod_ground = float(self.config.get(f"{pfx}_olod_base", 100 if pfx == "2d" else 80))
            alt_trans_olod = float(self.config.get(f"{pfx}_olod_altitude", 3000 if pfx == "2d" else 2500))

            if getattr(self, "manual_olod", None) is not None:
                self.current_olod_setpoint = float(self.manual_olod)
            else:
                if agl >= alt_trans_olod:
                    target_olod = float(olod_cruise)
                else:
                    ratio = max(0.0, min(1.0, agl / max(1.0, alt_trans_olod)))
                    target_olod = olod_ground + ratio * (olod_cruise - olod_ground)
                self.current_olod_setpoint = max(0.0, min(300.0, target_olod))

            ok_olod = self.engine.write_olod(self.current_olod_setpoint)

        if ok_tlod and ok_olod:
            status_parts = []
            if tlod_is_active:
                status_parts.append(f"TLOD {round(self.current_tlod_setpoint)}")
            if olod_is_active:
                status_parts.append(f"OLOD {round(self.current_olod_setpoint)}")
            self.status_message = f"Smart LOD Active • {' | '.join(status_parts)} • {pfx.upper()} ({round(base_fps)} FPS)"
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
            "external_autofps": bool(self.config.get("external_autofps", False)),
            "is_running": self.is_running,
            "status_message": self.status_message,
            "current_tlod_setpoint": round(self.current_tlod_setpoint, 1),
            "current_olod_setpoint": round(self.current_olod_setpoint, 1),
            "manual_tlod": self.manual_tlod is not None,
            "manual_olod": self.manual_olod is not None,
            "axis_state_2d": self.get_axis_state("2D"),
            "axis_state_vr": self.get_axis_state("VR"),
            "mode": self.config.get("mode", "IFR"),
            "source": self.config.get("source", "native"),
            "autofps_conflict": is_af_running,
            "autofps_pid": af_pid,
            "memory": mem_status,
            "config": self.config,
            "trigger_events_count": len(self.trigger_events),
            "last_trigger": self.trigger_events[-1] if self.trigger_events else None
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


# ==============================================================================
# SMART LOD PROFILES STORE (SAVE & ACTIVATE DYNAMIC PROFILES)
# ==============================================================================

def get_smart_lod_profiles_dir() -> str:
    """Returns directory where Smart LOD custom profiles are stored."""
    profiles_dir = os.path.join(get_user_data_dir(), "smart_lod_profiles")
    os.makedirs(profiles_dir, exist_ok=True)
    return profiles_dir


def generate_default_smart_lod_profiles() -> List[Dict[str, Any]]:
    """Generates standard calibrated Smart LOD profiles for flight simmers."""
    profiles_dir = get_smart_lod_profiles_dir()
    defaults = [
        {
            "id": "lod_prof_balanced_airliner",
            "name": "Balanced Airliner (IFR)",
            "description": "Standard IFR setpoint: TLOD 100 on ground, smooth climb to 250 in cruise.",
            "mode": "2D",
            "flight_mode": "IFR",
            "ground_tlod": 100,
            "cruise_tlod": 250,
            "alt_trans": 5000,
            "target_fps": 45,
            "cloud_recovery": True,
            "created_at": "2026-01-01T00:00:00"
        },
        {
            "id": "lod_prof_heavy_hub_optimizer",
            "name": "Heavy Hub & Megacity (EGLL / KJFK)",
            "description": "Maximum FPS protection at congested payware hubs: TLOD 80 on ground, 200 cruise.",
            "mode": "2D",
            "flight_mode": "IFR",
            "ground_tlod": 80,
            "cruise_tlod": 200,
            "alt_trans": 4000,
            "target_fps": 40,
            "cloud_recovery": True,
            "created_at": "2026-01-01T00:01:00"
        },
        {
            "id": "lod_prof_vfr_bush_sightseeing",
            "name": "VFR Bush & Mountain Sightseeing",
            "description": "Pristine terrain relief: TLOD 150 ground, 350 cruise for backcountry exploration.",
            "mode": "2D",
            "flight_mode": "VFR",
            "ground_tlod": 150,
            "cruise_tlod": 350,
            "alt_trans": 3000,
            "target_fps": 60,
            "cloud_recovery": True,
            "created_at": "2026-01-01T00:02:00"
        },
        {
            "id": "lod_prof_vr_headset_pacing",
            "name": "VR Headset Locked Stereo Cadence",
            "description": "Tailored for VR stereo reprojection: TLOD 90 ground, 220 cruise with locked 45 FPS.",
            "mode": "VR",
            "flight_mode": "IFR",
            "ground_tlod": 90,
            "cruise_tlod": 220,
            "alt_trans": 4500,
            "target_fps": 45,
            "cloud_recovery": True,
            "created_at": "2026-01-01T00:03:00"
        }
    ]
    for d in defaults:
        p_path = os.path.join(profiles_dir, f"{d['id']}.lodprofile.json")
        try:
            with open(p_path, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    set_active_smart_lod_profile_id(defaults[0]["id"])
    defaults[0]["is_active"] = True
    return defaults


def get_active_smart_lod_profile_id() -> str:
    profiles_dir = get_smart_lod_profiles_dir()
    state_file = os.path.join(profiles_dir, "active_profile.json")
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                aid = data.get("active_id", "")
                if aid and os.path.exists(os.path.join(profiles_dir, f"{aid}.lodprofile.json")):
                    return aid
        except Exception:
            pass
    files = glob.glob(os.path.join(profiles_dir, "*.lodprofile.json"))
    if files:
        newest = max(files, key=os.path.getmtime)
        aid = os.path.basename(newest)[:-len(".lodprofile.json")]
        set_active_smart_lod_profile_id(aid)
        return aid
    return ""


def set_active_smart_lod_profile_id(profile_id: str):
    profiles_dir = get_smart_lod_profiles_dir()
    state_file = os.path.join(profiles_dir, "active_profile.json")
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"active_id": profile_id, "updated_at": datetime.now().isoformat()}, f, indent=2)
    except Exception:
        pass


def get_smart_lod_profiles() -> List[Dict[str, Any]]:
    profiles_dir = get_smart_lod_profiles_dir()
    files = glob.glob(os.path.join(profiles_dir, "*.lodprofile.json"))
    if not files:
        return generate_default_smart_lod_profiles()

    active_id = get_active_smart_lod_profile_id()
    profiles = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as pf:
                data = json.load(pf)
                data["is_active"] = (data.get("id") == active_id)
                profiles.append(data)
        except Exception:
            pass

    profiles.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    if profiles and not any(p.get("is_active") for p in profiles):
        profiles[0]["is_active"] = True
        set_active_smart_lod_profile_id(profiles[0].get("id", ""))
    return profiles


def save_smart_lod_profile(name: str, config_data: Dict[str, Any], overwrite_id: Optional[str] = None) -> Dict[str, Any]:
    clean_name = str(name).strip()
    if not clean_name:
        return {"status": "error", "message": "Profile name cannot be empty."}

    profiles_dir = get_smart_lod_profiles_dir()
    existing = get_smart_lod_profiles()

    target_id = overwrite_id
    if not target_id:
        for p in existing:
            if p.get("name", "").strip().lower() == clean_name.lower():
                target_id = p.get("id")
                break

    if not target_id:
        import uuid
        target_id = f"lod_prof_{uuid.uuid4().hex[:10]}"

    profile_obj = {
        "id": target_id,
        "name": clean_name,
        "mode": config_data.get("mode", "2D"),
        "flight_mode": config_data.get("flight_mode", "IFR"),
        "ground_tlod": int(config_data.get("ground_tlod", 100)),
        "cruise_tlod": int(config_data.get("cruise_tlod", 250)),
        "alt_trans": int(config_data.get("alt_trans", 5000)),
        "target_fps": int(config_data.get("target_fps", 40)),
        "cloud_recovery": bool(config_data.get("cloud_recovery", True)),
        "created_at": datetime.now().isoformat()
    }

    file_path = os.path.join(profiles_dir, f"{target_id}.lodprofile.json")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(profile_obj, f, indent=2, ensure_ascii=False)
        set_active_smart_lod_profile_id(target_id)
        
        # Also apply to live smart lod controller config
        ctrl = get_smart_lod_controller()
        cfg_update = {
            "cloud_recovery": profile_obj["cloud_recovery"],
        }
        if profile_obj["flight_mode"] == "IFR":
            cfg_update["ifr_tlod_ground"] = profile_obj["ground_tlod"]
            cfg_update["ifr_tlod_cruise"] = profile_obj["cruise_tlod"]
            cfg_update["ifr_alt_transition"] = profile_obj["alt_trans"]
            cfg_update["ifr_target_fps"] = profile_obj["target_fps"]
        else:
            cfg_update["vfr_tlod_ground"] = profile_obj["ground_tlod"]
            cfg_update["vfr_tlod_cruise"] = profile_obj["cruise_tlod"]
            cfg_update["vfr_alt_transition"] = profile_obj["alt_trans"]
            cfg_update["vfr_target_fps"] = profile_obj["target_fps"]
        ctrl.save_config(cfg_update)

        return {"status": "success", "profile": profile_obj}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_smart_lod_profile_changes(profile_id: str, current_data: Dict[str, Any]) -> Dict[str, Any]:
    profiles_dir = get_smart_lod_profiles_dir()
    pfile = os.path.join(profiles_dir, f"{profile_id}.lodprofile.json")
    if not os.path.exists(pfile):
        return {"status": "error", "message": "Profile not found."}
    try:
        with open(pfile, "r", encoding="utf-8") as f:
            pdata = json.load(f)
        
        has_changes = (
            int(pdata.get("ground_tlod", 100)) != int(current_data.get("ground_tlod", 100)) or
            int(pdata.get("cruise_tlod", 250)) != int(current_data.get("cruise_tlod", 250)) or
            int(pdata.get("alt_trans", 5000)) != int(current_data.get("alt_trans", 5000)) or
            int(pdata.get("target_fps", 40)) != int(current_data.get("target_fps", 40)) or
            bool(pdata.get("cloud_recovery", True)) != bool(current_data.get("cloud_recovery", True)) or
            str(pdata.get("mode", "2D")) != str(current_data.get("mode", "2D"))
        )
        return {
            "status": "success",
            "has_changes": has_changes,
            "profile_id": profile_id,
            "profile_name": pdata.get("name", "")
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def rename_smart_lod_profile(profile_id: str, new_name: str) -> Dict[str, Any]:
    clean_name = str(new_name).strip()
    if not clean_name:
        return {"status": "error", "message": "Profile name cannot be empty."}
    profiles = get_smart_lod_profiles()
    for p in profiles:
        if p.get("id") != profile_id and p.get("name", "").strip().lower() == clean_name.lower():
            return {"status": "error", "message": f'A profile named "{clean_name}" already exists.'}
    profiles_dir = get_smart_lod_profiles_dir()
    pfile = os.path.join(profiles_dir, f"{profile_id}.lodprofile.json")
    if not os.path.exists(pfile):
        return {"status": "error", "message": "Profile not found."}
    try:
        with open(pfile, "r", encoding="utf-8") as f:
            pdata = json.load(f)
        pdata["name"] = clean_name
        pdata["updated_at"] = datetime.now().isoformat()
        with open(pfile, "w", encoding="utf-8") as f:
            json.dump(pdata, f, indent=2, ensure_ascii=False)
        return {"status": "success", "profile": pdata}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def activate_smart_lod_profile(profile_id: str) -> Dict[str, Any]:
    profiles_dir = get_smart_lod_profiles_dir()
    pfile = os.path.join(profiles_dir, f"{profile_id}.lodprofile.json")
    if not os.path.exists(pfile):
        return {"status": "error", "message": "Profile not found."}
    try:
        with open(pfile, "r", encoding="utf-8") as f:
            pdata = json.load(f)
        set_active_smart_lod_profile_id(profile_id)
        ctrl = get_smart_lod_controller()
        cfg_update = {
            "cloud_recovery": pdata.get("cloud_recovery", True),
        }
        f_mode = pdata.get("flight_mode", "IFR")
        if f_mode == "IFR":
            cfg_update["ifr_tlod_ground"] = pdata.get("ground_tlod", 100)
            cfg_update["ifr_tlod_cruise"] = pdata.get("cruise_tlod", 250)
            cfg_update["ifr_alt_transition"] = pdata.get("alt_trans", 5000)
            cfg_update["ifr_target_fps"] = pdata.get("target_fps", 40)
        else:
            cfg_update["vfr_tlod_ground"] = pdata.get("ground_tlod", 100)
            cfg_update["vfr_tlod_cruise"] = pdata.get("cruise_tlod", 250)
            cfg_update["vfr_alt_transition"] = pdata.get("alt_trans", 5000)
            cfg_update["vfr_target_fps"] = pdata.get("target_fps", 40)
        ctrl.save_config(cfg_update)
        return {"status": "success", "profile": pdata}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def delete_smart_lod_profile(profile_id: str) -> Dict[str, Any]:
    profiles_dir = get_smart_lod_profiles_dir()
    pfile = os.path.join(profiles_dir, f"{profile_id}.lodprofile.json")
    if not os.path.exists(pfile):
        return {"status": "error", "message": "Profile not found."}
    try:
        os.remove(pfile)
        active_id = get_active_smart_lod_profile_id()
        if active_id == profile_id:
            rem = get_smart_lod_profiles()
            if rem:
                set_active_smart_lod_profile_id(rem[0].get("id", ""))
        return {"status": "success", "deleted_id": profile_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_smart_lod_axis_state(mode="2D") -> Dict[str, Any]:
    return get_smart_lod_controller().get_axis_state(mode)


def set_smart_lod_axis_state(mode: str, axis: str, enabled=None, target=None, altitude=None, base=None) -> Dict[str, Any]:
    return get_smart_lod_controller().set_axis_state(mode, axis, enabled, target, altitude, base)


def set_external_autofps(enabled: bool) -> bool:
    return get_smart_lod_controller().set_external_autofps(enabled)


def reset_smart_lod_to_profile(axis: str = "all") -> Dict[str, Any]:
    return get_smart_lod_controller().reset_to_active_profile(axis)

