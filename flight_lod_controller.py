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

    def reset_manual_override(self, axis: str = "all") -> Dict[str, Any]:
        """Réengage les limitations d'altitude et l'automatisation en supprimant le débrayage manuel."""
        with self._lock:
            if axis in ("tlod", "all"):
                self.manual_tlod = None
            if axis in ("olod", "all"):
                self.manual_olod = None
        if self.is_running:
            try:
                self._tick()
            except Exception:
                pass
        return {
            "success": True,
            "axis": axis,
            "manual_tlod": self.manual_tlod is not None,
            "manual_olod": self.manual_olod is not None,
            "current_tlod": round(self.current_tlod_setpoint, 1),
            "current_olod": round(self.current_olod_setpoint, 1)
        }

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

        # 4-6. Gestion du Terrain LOD (TLOD)
        if getattr(self, "manual_tlod", None) is not None:
            # Mode Débrayé / Manual Override : Consigne manuelle stricte (contourne les profils d'altitude)
            self.current_tlod_setpoint = float(self.manual_tlod)
        else:
            # Mode Automatique : Calcul de la consigne d'altitude (Interpolation Sol -> Croisière)
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
        if getattr(self, "manual_olod", None) is not None:
            # Mode Débrayé / Manual Override : Consigne manuelle stricte
            self.current_olod_setpoint = float(self.manual_olod)
            self.engine.write_olod(self.current_olod_setpoint)
        else:
            # Mode Automatique : Interpolation selon profil d'altitude
            olod_ground = self.config.get(f"{mode.lower()}_olod_ground", 100)
            olod_cruise = self.config.get(f"{mode.lower()}_olod_cruise", 50)
            if agl >= alt_trans:
                target_olod = float(olod_cruise)
            else:
                ratio = max(0.0, min(1.0, agl / max(1, alt_trans)))
                target_olod = olod_ground - ratio * (olod_ground - olod_cruise)
            self.current_olod_setpoint = target_olod
            self.engine.write_olod(target_olod)

        if ok:
            # Enregistrement des déclenchements (Triggers) pour feedback visuel et télémétrie
            current_phase = "ground" if (on_ground or agl < 500) else ("cruise" if agl >= alt_trans else "climb_descent")
            phase_changed = current_phase != self._last_phase
            tlod_rounded = round(self.current_tlod_setpoint)
            last_tlod = self._last_logged_tlod if self._last_logged_tlod is not None else tlod_rounded
            tlod_diff = abs(tlod_rounded - last_tlod)

            if phase_changed or tlod_diff >= 10:
                import datetime
                now_iso = datetime.datetime.now().strftime("%H:%M:%S")
                trigger_type = "phase_transition" if phase_changed else ("fps_regulation_drop" if tlod_rounded < last_tlod else "fps_regulation_boost")
                reason_text = ""
                if phase_changed:
                    if current_phase == "cruise":
                        reason_text = f"Plafond croisière atteint (> {alt_trans} ft) -> TLOD {tlod_rounded}"
                    elif current_phase == "ground":
                        reason_text = f"Zone sol / approche (< 500 ft) -> TLOD {tlod_rounded} (protection MainThread)"
                    else:
                        reason_text = f"Transition montée/descente ({round(agl)} ft) -> TLOD {tlod_rounded}"
                elif tlod_rounded < last_tlod:
                    reason_text = f"Régulation FPS : baisse TLOD {last_tlod} -> {tlod_rounded} (FPS {round(base_fps)} < {target_fps})"
                else:
                    reason_text = f"Marge de fluidité : montée TLOD {last_tlod} -> {tlod_rounded} (FPS {round(base_fps)})"

                event = {
                    "timestamp": time.time(),
                    "time_str": now_iso,
                    "agl_ft": round(agl),
                    "phase": current_phase,
                    "old_tlod": last_tlod,
                    "new_tlod": tlod_rounded,
                    "fps": round(base_fps, 1),
                    "type": trigger_type,
                    "reason": reason_text
                }
                with self._lock:
                    self.trigger_events.append(event)
                    if len(self.trigger_events) > 100:
                        self.trigger_events.pop(0)

                self._last_logged_tlod = tlod_rounded
                self._last_phase = current_phase

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
            "manual_tlod": self.manual_tlod is not None,
            "manual_olod": self.manual_olod is not None,
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
