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
import re
from datetime import datetime
from typing import List
from typing import Dict, Any, Optional, Tuple

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
    "2d_tlod_altitude": 3000,
    "2d_olod_active": False,
    "2d_olod_base": 100,
    "2d_olod_target": 200,
    "2d_olod_altitude": 3000,
    
    # VR Independent LOD Axis
    "vr_tlod_active": False,
    "vr_tlod_base": 100,
    "vr_tlod_target": 200,
    "vr_tlod_altitude": 3000,
    "vr_olod_active": False,
    "vr_olod_base": 100,
    "vr_olod_target": 200,
    "vr_olod_altitude": 3000,
    
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
    "deadband_fps": 2,           # Marge de tolérance (±2 FPS)
    "ingame_pinned_settings": ["max_fps", "clouds", "precaching", "buildings", "trees"]
}

VALID_INGAME_PIN_KEYS = ("max_fps", "clouds", "precaching", "terrain_shadows", "buildings", "trees", "plants", "grass")


_nominal_profile_cache: Dict[bool, Tuple[float, Dict[str, Any]]] = {}


def get_active_profile_nominal_values(is_vr: Optional[bool] = None) -> Dict[str, Any]:
    """
    Lecture directe ultra-rapide (<1ms) des valeurs nominales TLOD, OLOD, Nuages et
    paramètres graphiques modifiables à chaud du profil graphique actif sans bloquer
    avec build_msfs_settings_matrix(). Isole {GraphicsVR en mode VR et {Graphics en mode 2D.
    """
    global _nominal_profile_cache
    try:
        if is_vr is None:
            try:
                import flight_memory_engine
                mem = flight_memory_engine.get_memory_engine()
                if mem and mem.is_attached:
                    is_vr = mem.is_vr_active()
            except Exception:
                is_vr = False

        vr_flag = bool(is_vr)
        now_ts = time.time()
        cached_entry = _nominal_profile_cache.get(vr_flag)
        if cached_entry and (now_ts - cached_entry[0] < 2.0):
            return dict(cached_entry[1])

        res: Dict[str, Any] = {
            "name": "Active Profile",
            "tlod": 100.0,
            "olod": 100.0,
            "clouds": 2,
            "precaching": 2,
            "terrain_shadows": 256 if vr_flag else 512,
            "buildings": 2,
            "trees": 2,
            "plants": 1 if vr_flag else 2,
            "grass": 0 if vr_flag else 2,
            "max_fps": 36 if vr_flag else 60,
            "is_vr": vr_flag
        }
        appdata = os.environ.get("APPDATA", "")
        ws_dir = os.path.join(appdata, "SceneryX", "custom_profiles")
        state_file = os.path.join(ws_dir, "active_profile.json")
        if os.path.exists(state_file):
            with open(state_file, "r", encoding="utf-8") as f:
                sdata = json.load(f)
            aid = sdata.get("active_id")
            if aid:
                pfile = os.path.join(ws_dir, f"{aid}.profile.json")
                if os.path.exists(pfile):
                    with open(pfile, "r", encoding="utf-8") as pf:
                        pjson = json.load(pf)
                    res["name"] = pjson.get("name", aid)
                    content = pjson.get("content", "")

                    # Extract TargetFrameRate / TargetFrameRateVR from {Video
                    fps_key = "TargetFrameRateVR" if vr_flag else "TargetFrameRate"
                    m_fps = re.search(rf"\b{fps_key}\s+(\d+)", content)
                    if m_fps:
                        fps_v = int(m_fps.group(1))
                        if fps_v > 0:
                            res["max_fps"] = fps_v

                    # Isolate section: GraphicsVR for VR, Graphics for 2D
                    if vr_flag and "{GraphicsVR" in content:
                        section = content.split("{GraphicsVR", 1)[1]
                    elif "{Graphics" in content:
                        section = content.split("{Graphics", 1)[1]
                        if "{GraphicsVR" in section:
                            section = section.split("{GraphicsVR", 1)[0]
                    else:
                        section = content

                    m_cloud = re.search(r"\{VolumetricClouds\s+Enabled\s+\d+\s+Quality\s+(\d+)", section)
                    if m_cloud:
                        res["clouds"] = max(0, min(3, int(m_cloud.group(1))))
                    m_prec = re.search(r"\{OffscreenTerrainPreCaching\s+Enabled\s+\d+\s+Quality\s+(\d+)", section)
                    if m_prec:
                        res["precaching"] = max(0, min(3, int(m_prec.group(1))))
                    m_hfs = re.search(r"\{HeightFieldShadows\s+Enabled\s+(\d+)\s+Size\s+(\d+)", section)
                    if m_hfs:
                        hfs_en = int(m_hfs.group(1))
                        hfs_sz = int(m_hfs.group(2))
                        res["terrain_shadows"] = 0 if hfs_en == 0 else (hfs_sz if hfs_sz in (128, 256, 512, 1024, 2048) else 512)
                    m_bldg = re.search(r"\{Buildings\s+Quality\s+(\d+)", section)
                    if m_bldg:
                        res["buildings"] = max(0, min(3, int(m_bldg.group(1))))
                    m_proc = re.search(r"\{Procedural([^}]*)\}", section)
                    if m_proc:
                        p_body = m_proc.group(1)
                        m_tr = re.search(r"TreesQuality\s+(\d+)", p_body)
                        if m_tr:
                            res["trees"] = max(0, min(3, int(m_tr.group(1))))
                        m_pl = re.search(r"PlantsQuality\s+(\d+)", p_body)
                        if m_pl:
                            res["plants"] = max(0, min(3, int(m_pl.group(1))))
                        m_gr = re.search(r"GrassQuality\s+(\d+)", p_body)
                        if m_gr:
                            res["grass"] = max(0, min(3, int(m_gr.group(1))))
                    m_tlod = re.search(r"\{Terrain\s+LoDFactor\s+([\d\.]+)", section)
                    if m_tlod:
                        res["tlod"] = round(float(m_tlod.group(1)) * 100.0, 1)
                    m_olod = re.search(r"\{ObjectsLoD\s+LoDFactor\s+([\d\.]+)", section)
                    if m_olod:
                        res["olod"] = round(float(m_olod.group(1)) * 100.0, 1)
                    _nominal_profile_cache[vr_flag] = (now_ts, dict(res))
                    return res
        _nominal_profile_cache[vr_flag] = (now_ts, dict(res))
        return res
    except Exception as e:
        print(f"[SmartLOD] Notice fast active profile reader: {e}")
    return {
        "name": "Active Profile",
        "tlod": 100.0,
        "olod": 100.0,
        "clouds": 2,
        "precaching": 2,
        "terrain_shadows": 256 if is_vr else 512,
        "buildings": 2,
        "trees": 2,
        "plants": 1 if is_vr else 2,
        "grass": 0 if is_vr else 2,
        "max_fps": 36 if is_vr else 60,
        "is_vr": bool(is_vr)
    }


def _patch_usercfg_live_graphics(content: str, settings: Dict[str, Any], vr_flag: bool) -> str:
    """Met à jour les blocs de settings modifiés à chaud dans une chaîne UserCfg.opt ({Graphics ou {GraphicsVR + {Video)."""
    if not content:
        return content

    # 1. max_fps dans {Video
    if "max_fps" in settings and settings["max_fps"] is not None:
        try:
            fps_v = max(15, min(240, int(settings["max_fps"])))
            fps_key = "TargetFrameRateVR" if vr_flag else "TargetFrameRate"
            if re.search(rf"({fps_key}\s+)\d+", content):
                content = re.sub(rf"({fps_key}\s+)\d+", rf"\g<1>{fps_v}", content)
            if re.search(r"(FrameLimiter\s+)\d+", content):
                content = re.sub(r"(FrameLimiter\s+)\d+", rf"\g<1>{fps_v}", content)
        except Exception:
            pass

    # 2. Isoler {Graphics ou {GraphicsVR
    mode_tag = "{GraphicsVR" if vr_flag else "{Graphics\n"
    mode_idx = content.find(mode_tag)
    if mode_idx == -1 and not vr_flag:
        mode_tag = "{Graphics\r\n"
        mode_idx = content.find(mode_tag)
    if mode_idx == -1:
        return content

    mode_end = len(content) if vr_flag else content.find("{GraphicsVR", mode_idx)
    if mode_end == -1:
        mode_end = len(content)

    sec = content[mode_idx:mode_end]

    if "clouds" in settings and settings["clouds"] is not None:
        q = max(0, min(3, int(settings["clouds"])))
        sec = re.sub(r"(\{VolumetricClouds\s+Enabled\s+\d+\s+Quality\s+)\d+", rf"\g<1>{q}", sec)

    if "precaching" in settings and settings["precaching"] is not None:
        q = max(0, min(3, int(settings["precaching"])))
        sec = re.sub(r"(\{OffscreenTerrainPreCaching\s+Enabled\s+\d+\s+Quality\s+)\d+", rf"\g<1>{q}", sec)

    if "terrain_shadows" in settings and settings["terrain_shadows"] is not None:
        ts = int(settings["terrain_shadows"])
        if ts <= 0:
            sec = re.sub(r"(\{HeightFieldShadows\s+Enabled\s+)\d+", r"\g<1>0", sec)
        elif ts in (128, 256, 512, 1024, 2048):
            sec = re.sub(
                r"(\{HeightFieldShadows\s+Enabled\s+)\d+(\s+Size\s+)\d+",
                rf"\g<1>1\g<2>{ts}",
                sec
            )

    if "buildings" in settings and settings["buildings"] is not None:
        q = max(0, min(3, int(settings["buildings"])))
        sec = re.sub(r"(\{Buildings\s+Quality\s+)\d+", rf"\g<1>{q}", sec)

    # Procedural sub-block: TreesQuality, PlantsQuality, RocksQuality, GrassQuality
    if any(k in settings and settings[k] is not None for k in ("trees", "plants", "grass")):
        m_proc = re.search(r"(\{Procedural[^}]*\})", sec)
        if m_proc:
            p_block = m_proc.group(1)
            if "trees" in settings and settings["trees"] is not None:
                q = max(0, min(3, int(settings["trees"])))
                p_block = re.sub(r"(TreesQuality\s+)\d+", rf"\g<1>{q}", p_block)
            if "plants" in settings and settings["plants"] is not None:
                q = max(0, min(3, int(settings["plants"])))
                p_block = re.sub(r"(PlantsQuality\s+)\d+", rf"\g<1>{q}", p_block)
            if "grass" in settings and settings["grass"] is not None:
                q = max(0, min(3, int(settings["grass"])))
                p_block = re.sub(r"(GrassQuality\s+)\d+", rf"\g<1>{q}", p_block)
            sec = sec[:m_proc.start()] + p_block + sec[m_proc.end():]

    return content[:mode_idx] + sec + content[mode_end:]


_LIVE_GRAPHICS_OVERRIDES: Dict[str, int] = {}


def get_live_graphics_overrides() -> Dict[str, int]:
    """Retourne les overrides graphiques appliqués à chaud en vol depuis l'In-Game Panel."""
    return dict(_LIVE_GRAPHICS_OVERRIDES)


def clear_live_graphics_overrides(keys: Optional[List[str]] = None):
    """Efface tous les overrides graphiques à chaud (ou une sous-liste de clés) pour revenir au profil actif."""
    global _LIVE_GRAPHICS_OVERRIDES
    if not keys or "all" in keys:
        _LIVE_GRAPHICS_OVERRIDES.clear()
    else:
        for k in keys:
            _LIVE_GRAPHICS_OVERRIDES.pop(str(k), None)


def apply_live_graphics_to_profile(
    settings: Dict[str, Any],
    is_vr: Optional[bool] = None,
    reset_keys: Optional[List[str]] = None
) -> Dict[str, int]:
    """
    Applique les réglages graphiques modifiés à chaud en tant qu'overrides en vol et dans UserCfg.opt,
    tout en conservant intact le fichier .profile.json du profil actif afin de permettre un Reset
    individuel de chaque paramètre vers la valeur nominale du profil actif.
    """
    global _nominal_profile_cache, _LIVE_GRAPHICS_OVERRIDES
    try:
        if is_vr is None:
            try:
                import flight_memory_engine
                mem = flight_memory_engine.get_memory_engine()
                if mem and mem.is_attached and not mem.safe_read_only:
                    is_vr = mem.is_vr_active()
            except Exception:
                is_vr = False
        vr_flag = bool(is_vr)

        nom_vals = get_active_profile_nominal_values(is_vr=vr_flag)
        effective_settings: Dict[str, int] = {}

        if reset_keys:
            for rk in reset_keys:
                rk_str = str(rk)
                _LIVE_GRAPHICS_OVERRIDES.pop(rk_str, None)
                if rk_str in nom_vals and nom_vals[rk_str] is not None:
                    effective_settings[rk_str] = int(nom_vals[rk_str])

        if isinstance(settings, dict):
            for k in VALID_INGAME_PIN_KEYS:
                if k in settings and settings[k] is not None and (not reset_keys or k not in reset_keys):
                    val_int = int(settings[k])
                    effective_settings[k] = val_int
                    nom_v = nom_vals.get(k)
                    if nom_v is not None and int(nom_v) == val_int:
                        _LIVE_GRAPHICS_OVERRIDES.pop(k, None)
                    else:
                        _LIVE_GRAPHICS_OVERRIDES[k] = val_int

        # Synchroniser UserCfg.opt sur le disque (2D et VR) sans écraser la référence .profile.json
        if effective_settings:
            try:
                import flight_rig_optimizer
                ucfg_path = flight_rig_optimizer.get_user_cfg_path()
                if ucfg_path and os.path.exists(ucfg_path):
                    with open(ucfg_path, "r", encoding="utf-8", errors="ignore") as uf:
                        u_content = uf.read()
                    if u_content:
                        u_patched = _patch_usercfg_live_graphics(u_content, effective_settings, False)
                        u_patched = _patch_usercfg_live_graphics(u_patched, effective_settings, True)
                        with open(ucfg_path, "w", encoding="utf-8") as uf:
                            uf.write(u_patched)
            except Exception as ue:
                print(f"[SmartLOD] Notice syncing UserCfg.opt on live graphics apply: {ue}")

        return effective_settings
    except Exception as e:
        print(f"[SmartLOD] Warning applying live graphics override: {e}")
        return {}


CLOUD_QUALITY_LABELS = {0: "LOW", 1: "MEDIUM", 2: "HIGH", 3: "ULTRA"}
CLOUD_QUALITY_TITLE_LABELS = {0: "Low", 1: "Medium", 2: "High", 3: "Ultra"}


def get_nominal_cloud_quality() -> int:
    """
    Retourne la qualite des nuages nominale (0=Low, 1=Medium, 2=High, 3=Ultra)
    extraite ultra-rapidement du profil graphique MSFS actuellement actif dans SceneryX.
    """
    return max(0, min(3, int(get_active_profile_nominal_values().get("clouds", 2))))


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
        self.in_cloud_boost: bool = False
        self.current_cloud_quality: int = get_nominal_cloud_quality()
        self.original_cloud_quality: Optional[int] = None
        self._last_cloud_change_time: float = 0.0
        self.trigger_events: List[Dict[str, Any]] = []
        self._last_logged_tlod: Optional[float] = None
        self._last_phase: str = "ground"

        # Synchroniser et appliquer le profil Smart LOD actif dès l'allumage
        self.load_active_profile_into_config()

        from scanner import IS_LITE
        if IS_LITE:
            self.config["enabled"] = False
            self.is_running = False
        elif self.config.get("enabled", False):
            self.start()

    def load_active_profile_into_config(self):
        """Charge et applique le profil Smart LOD actif dans self.config au démarrage ou au rechargement."""
        try:
            aid = get_active_smart_lod_profile_id()
            if not aid:
                profs = get_smart_lod_profiles()
                if profs:
                    aid = profs[0].get("id", "")
            if aid:
                pdir = get_smart_lod_profiles_dir()
                pfile = os.path.join(pdir, f"{aid}.lodprofile.json")
                if os.path.exists(pfile):
                    with open(pfile, "r", encoding="utf-8") as f:
                        pdata = json.load(f)
                    pdata = _sanitize_smart_lod_profile_data(pdata)
                    with self._lock:
                        self.config.update({
                            "cloud_recovery": pdata["cloud_recovery"],
                            "2d_tlod_base": pdata["ground_tlod"],
                            "2d_tlod_target": pdata["cruise_tlod"],
                            "2d_tlod_altitude": pdata["alt_trans"],
                            "2d_olod_base": pdata["ground_olod"],
                            "2d_olod_target": pdata["cruise_olod"],
                            "2d_olod_altitude": pdata["alt_trans_olod"],
                            "vr_tlod_base": pdata["vr_ground_tlod"],
                            "vr_tlod_target": pdata["vr_cruise_tlod"],
                            "vr_tlod_altitude": pdata["vr_alt_trans"],
                            "vr_olod_base": pdata["vr_ground_olod"],
                            "vr_olod_target": pdata["vr_cruise_olod"],
                            "vr_olod_altitude": pdata["vr_alt_trans_olod"],
                            "vr_cloud_recovery": pdata["vr_cloud_recovery"],
                            # Legacy mirror
                            "ifr_tlod_ground": pdata["ground_tlod"],
                            "ifr_tlod_cruise": pdata["cruise_tlod"],
                            "ifr_alt_transition": pdata["alt_trans"],
                            "ifr_olod_ground": pdata["ground_olod"],
                            "ifr_olod_cruise": pdata["cruise_olod"],
                            "vfr_tlod_ground": pdata["ground_tlod"],
                            "vfr_tlod_cruise": pdata["cruise_tlod"],
                            "vfr_alt_transition": pdata["alt_trans"],
                            "vfr_olod_ground": pdata["ground_olod"],
                            "vfr_olod_cruise": pdata["cruise_olod"],
                        })
                    print(f"[SmartLOD] Initialized active profile '{pdata.get('name', aid)}' (TLOD {pdata['ground_tlod']}-{pdata['cruise_tlod']}, OLOD {pdata['ground_olod']}-{pdata['cruise_olod']})")
        except Exception as e:
            print(f"[SmartLOD] Notice initializing active profile: {e}")

    def set_cloud_recovery(self, enabled: bool, restore_nominal: bool = True) -> bool:
        """Active ou désactive Auto Cloud Recovery de manière 100% indépendante du Smart LOD."""
        with self._lock:
            self.config["cloud_recovery"] = bool(enabled)
            self.config["vr_cloud_recovery"] = bool(enabled)
            self.config["2d_cloud_recovery"] = bool(enabled)
            if enabled:
                _LIVE_GRAPHICS_OVERRIDES.pop("clouds", None)
            try:
                with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4)
            except Exception as e:
                print(f"[SmartLOD] Erreur sauvegarde config cloud_recovery: {e}")

        if enabled:
            # Recalculer immédiatement la valeur cible d'Auto Cloud Recovery (nominale du profil actif ou réduite si déficit FPS)
            nom_q = get_nominal_cloud_quality()
            calc_q = nom_q
            try:
                telemetry = self._get_live_flight_telemetry()
                base_fps = float(telemetry.get("base_fps", 0) or telemetry.get("displayed_fps", 0) or 0)
                is_vr = self.engine.is_vr_active() if (self.engine.is_attached and not self.engine.safe_read_only) else False
                target_fps = float(self.config.get("vr_target_fps", 36) if is_vr else self.config.get("2d_target_fps", self.config.get("ifr_target_fps", 40)))
                if base_fps > 0 and base_fps < (target_fps - 5):
                    calc_q = max(0, nom_q - 1)
            except Exception:
                calc_q = nom_q

            self.current_cloud_quality = calc_q
            self.in_cloud_reduction = bool(calc_q < nom_q)
            self.in_cloud_boost = False
            self._last_cloud_change_time = time.time()

            def _async_apply_cloud_rec():
                try:
                    apply_live_graphics_to_profile({}, reset_keys=["clouds"])
                    if not self.engine.is_attached:
                        self.engine.attach()
                    if self.engine.is_attached and not self.engine.safe_read_only:
                        self.engine.write_cloud_quality(calc_q)
                        self.engine.write_live_graphics({"clouds": calc_q})
                    print(f"[SmartLOD] Auto Cloud Recovery turned ON -> applied calculated cloud quality {CLOUD_QUALITY_LABELS.get(calc_q)} ({calc_q}) [nominal={nom_q}]")
                except Exception as e:
                    print(f"[SmartLOD] Warning applying cloud recovery on enable: {e}")

            threading.Thread(target=_async_apply_cloud_rec, daemon=True, name="AsyncCloudRecEnable").start()
            if not self.config.get("external_autofps", False):
                self.start()
        else:
            was_reduced_or_boosted = bool(self.in_cloud_reduction or self.in_cloud_boost)
            self.in_cloud_reduction = False
            self.in_cloud_boost = False
            if restore_nominal and "clouds" not in _LIVE_GRAPHICS_OVERRIDES and was_reduced_or_boosted:
                def _async_restore():
                    try:
                        nom_q = get_nominal_cloud_quality()
                        self.current_cloud_quality = nom_q
                        if not self.engine.is_attached:
                            self.engine.attach()
                        if self.engine.is_attached and not self.engine.safe_read_only:
                            self.engine.write_cloud_quality(nom_q)
                            self.engine.write_live_graphics({"clouds": nom_q})
                            print(f"[SmartLOD] Auto Cloud Recovery turned OFF -> restored MSFS cloud quality to nominal ({nom_q})")
                    except Exception as e:
                        print(f"[SmartLOD] Warning restoring cloud quality: {e}")
                threading.Thread(target=_async_restore, daemon=True, name="AsyncCloudRestore").start()
            if not self.config.get("enabled", False):
                self.stop(detach=False)
        return True

    def get_ingame_pinned_settings(self) -> List[str]:
        """Retourne la liste ordonnée (max 5) des paramètres épinglés dans le bandeau de l'In-Game Panel."""
        with self._lock:
            raw = self.config.get("ingame_pinned_settings")
            if not isinstance(raw, list):
                raw = list(DEFAULT_CONFIG["ingame_pinned_settings"])
            cleaned = []
            for k in raw:
                ks = str(k).strip()
                if ks in VALID_INGAME_PIN_KEYS and ks not in cleaned:
                    cleaned.append(ks)
                if len(cleaned) >= 5:
                    break
            return cleaned

    def set_ingame_pinned_settings(self, pins: List[str]) -> List[str]:
        """Met à jour et sauvegarde la liste (max 5) des paramètres épinglés dans l'In-Game Panel."""
        cleaned = []
        if isinstance(pins, list):
            for k in pins:
                ks = str(k).strip()
                if ks in VALID_INGAME_PIN_KEYS and ks not in cleaned:
                    cleaned.append(ks)
                if len(cleaned) >= 5:
                    break
        with self._lock:
            self.config["ingame_pinned_settings"] = cleaned
            try:
                with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4)
            except Exception as e:
                print(f"[SmartLOD] Erreur sauvegarde ingame_pinned_settings: {e}")
        return cleaned

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
        axis="lod" ne réinitialise que TLOD et OLOD sans toucher aux nuages ni aux surcharges graphiques.
        """
        nom_vals = get_active_profile_nominal_values()
        nom_tlod = nom_vals.get("tlod", 100.0)
        nom_olod = nom_vals.get("olod", 100.0)
        nom_cloud = max(0, min(3, int(nom_vals.get("clouds", 2))))
        profile_name = nom_vals.get("name", "Active Profile")

        with self._lock:
            if axis == "all":
                _LIVE_GRAPHICS_OVERRIDES.clear()
            elif axis == "clouds":
                _LIVE_GRAPHICS_OVERRIDES.pop("clouds", None)
            if axis in ("tlod", "lod", "all"):
                self.manual_tlod = None
                self.current_tlod_setpoint = float(nom_tlod)
            if axis in ("olod", "lod", "all"):
                self.manual_olod = None
                self.current_olod_setpoint = float(nom_olod)
            if axis in ("clouds", "all"):
                self.in_cloud_reduction = False
                self.in_cloud_boost = False
                self.current_cloud_quality = nom_cloud

        if not self.engine.is_attached:
            self.engine.attach()

        if self.engine.is_attached and not self.engine.safe_read_only:
            if axis in ("tlod", "lod", "all"):
                self.engine.write_tlod(nom_tlod)
            if axis in ("olod", "lod", "all"):
                self.engine.write_olod(nom_olod)
            if axis in ("clouds", "all"):
                self.engine.write_cloud_quality(nom_cloud)

        cur_cld = getattr(self, "current_cloud_quality", nom_cloud)
        print(f"[SmartLOD] Reset ({axis}) to active profile '{profile_name}': TLOD={nom_tlod}, OLOD={nom_olod}, Clouds={cur_cld}")
        return {
            "success": True,
            "axis": axis,
            "reset_to_profile": True,
            "profile_name": profile_name,
            "manual_tlod": False,
            "manual_olod": False,
            "current_tlod": round(self.current_tlod_setpoint, 1),
            "current_olod": round(self.current_olod_setpoint, 1),
            "cloud_quality": cur_cld,
            "cloud_label": CLOUD_QUALITY_LABELS.get(cur_cld, "HIGH")
        }

    def reset_manual_override(self, axis: str = "all") -> Dict[str, Any]:
        """Réengage les limitations d'altitude et l'automatisation en réinitialisant sur le profil actif."""
        return self.reset_to_active_profile(axis)

    def get_axis_state(self, mode: str = "2D") -> Dict[str, Any]:
        with self._lock:
            pfx = "vr" if str(mode).upper() == "VR" else "2d"
            if self.config.get("enabled", False) and self.is_running:
                tlod_base = int(round(getattr(self, "dynamic_tlod_floor", self.config.get(f"{pfx}_tlod_base", 100))))
                tlod_target = int(round(getattr(self, "dynamic_tlod_cruise", self.config.get(f"{pfx}_tlod_target", 200))))
                olod_base = int(round(getattr(self, "dynamic_olod_floor", self.config.get(f"{pfx}_olod_base", 100))))
                olod_target = int(round(getattr(self, "dynamic_olod_cruise", self.config.get(f"{pfx}_olod_target", 200))))
            else:
                tlod_base = int(self.config.get(f"{pfx}_tlod_base", 100))
                tlod_target = int(self.config.get(f"{pfx}_tlod_target", 200))
                olod_base = int(self.config.get(f"{pfx}_olod_base", 100))
                olod_target = int(self.config.get(f"{pfx}_olod_target", 200))

            return {
                "mode": pfx.upper(),
                "external_autofps": bool(self.config.get("external_autofps", False)),
                "tlod_active": bool(self.config.get(f"{pfx}_tlod_active", False)),
                "tlod_base": tlod_base,
                "tlod_target": tlod_target,
                "tlod_altitude": int(self.config.get(f"{pfx}_tlod_altitude", 3000)),
                "olod_active": bool(self.config.get(f"{pfx}_olod_active", False)),
                "olod_base": olod_base,
                "olod_target": olod_target,
                "olod_altitude": int(self.config.get(f"{pfx}_olod_altitude", 3000)),
            }

    def set_axis_state(self, mode: str, axis: str, enabled: Optional[bool] = None, target: Optional[int] = None, altitude: Optional[int] = None, base: Optional[int] = None) -> Dict[str, Any]:
        write_val: Optional[float] = None
        with self._lock:
            pfx = "vr" if str(mode).upper() == "VR" else "2d"
            ax = "olod" if "olod" in str(axis).lower() else "tlod"

            if enabled is not None:
                if not bool(enabled):
                    self.config["enabled"] = False
                    self.config["2d_tlod_active"] = False
                    self.config["2d_olod_active"] = False
                    self.config["vr_tlod_active"] = False
                    self.config["vr_olod_active"] = False
                    self.status_message = "MAN"
                else:
                    self.config[f"{pfx}_{ax}_active"] = True
            max_v = 400 if ax == "tlod" else 300
            other_pfx = "2d" if pfx == "vr" else "vr"
            if base is not None:
                b_val = max(0, min(int(base), max_v))
                self.config[f"{pfx}_{ax}_base"] = b_val
                self.config[f"{other_pfx}_{ax}_base"] = b_val
                if ax == "tlod":
                    self.dynamic_tlod_floor = float(b_val)
                else:
                    self.dynamic_olod_floor = float(b_val)
                write_val = float(b_val)
            if target is not None:
                t_val = max(0, min(int(target), max_v))
                self.config[f"{pfx}_{ax}_target"] = t_val
                self.config[f"{other_pfx}_{ax}_target"] = t_val
                if ax == "tlod":
                    self.dynamic_tlod_cruise = float(t_val)
                else:
                    self.dynamic_olod_cruise = float(t_val)
                if write_val is None:
                    write_val = float(t_val)
            if altitude is not None:
                a_val = max(0, int(altitude))
                self.config[f"{pfx}_{ax}_altitude"] = a_val
                self.config[f"{other_pfx}_{ax}_altitude"] = a_val

            any_active = any([
                self.config.get("2d_tlod_active", False),
                self.config.get("2d_olod_active", False),
                self.config.get("vr_tlod_active", False),
                self.config.get("vr_olod_active", False),
            ])
            if enabled is not None:
                self.config["enabled"] = bool(enabled) and any_active and not self.config.get("external_autofps", False)

            if self.config.get("enabled", False):
                if ax == "tlod":
                    self.manual_tlod = None
                else:
                    self.manual_olod = None
            elif write_val is not None:
                if ax == "tlod":
                    self.manual_tlod = float(write_val)
                    self.current_tlod_setpoint = float(write_val)
                else:
                    self.manual_olod = float(write_val)
                    self.current_olod_setpoint = float(write_val)

            try:
                with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4)
            except Exception as e:
                print(f"[SmartLOD] Erreur sauvegarde config: {e}")

            # Sync updated slider bounds to active .lodprofile.json so re-enabling Smart LOD keeps user's slider settings
            try:
                aid = get_active_smart_lod_profile_id()
                if aid:
                    pfile = os.path.join(_get_smart_lod_profiles_dir(), f"{aid}.lodprofile.json")
                    if os.path.exists(pfile):
                        with open(pfile, "r", encoding="utf-8") as pf:
                            pdata = json.load(pf)
                        t_base_2d = int(self.config.get("2d_tlod_base", 100))
                        t_targ_2d = int(self.config.get("2d_tlod_target", 200))
                        o_base_2d = int(self.config.get("2d_olod_base", 100))
                        o_targ_2d = int(self.config.get("2d_olod_target", 200))
                        if t_base_2d < t_targ_2d:
                            pdata["ground_tlod"] = t_base_2d
                            pdata["cruise_tlod"] = t_targ_2d
                            pdata["vr_ground_tlod"] = int(self.config.get("vr_tlod_base", t_base_2d))
                            pdata["vr_cruise_tlod"] = int(self.config.get("vr_tlod_target", t_targ_2d))
                        if o_base_2d < o_targ_2d:
                            pdata["ground_olod"] = o_base_2d
                            pdata["cruise_olod"] = o_targ_2d
                            pdata["vr_ground_olod"] = int(self.config.get("vr_olod_base", o_base_2d))
                            pdata["vr_cruise_olod"] = int(self.config.get("vr_olod_target", o_targ_2d))
                        pdata["alt_trans"] = int(self.config.get("2d_tlod_altitude", 3000))
                        pdata["vr_alt_trans"] = int(self.config.get("vr_tlod_altitude", 3000))
                        pdata["alt_trans_olod"] = int(self.config.get("2d_olod_altitude", 3000))
                        pdata["vr_alt_trans_olod"] = int(self.config.get("vr_olod_altitude", 3000))
                        with open(pfile, "w", encoding="utf-8") as pf:
                            json.dump(pdata, pf, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[SmartLOD] Notice syncing active lodprofile: {e}")

        if self.config.get("enabled"):
            self.start()
            try:
                self._tick()
            except Exception:
                pass
        else:
            if not self.config.get("cloud_recovery", True):
                self.stop(detach=False)
            if write_val is not None:
                try:
                    if not self.engine.is_attached or self.engine.safe_read_only:
                        self.engine.attach()
                    if self.engine.is_attached and not self.engine.safe_read_only:
                        if ax == "tlod":
                            self.engine.write_tlod(write_val)
                        else:
                            self.engine.write_olod(write_val)
                except Exception:
                    pass

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
        from scanner import IS_LITE
        if IS_LITE:
            self.is_running = False
            return
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="SmartLodController")
        self._thread.start()
        print("[SmartLOD] Moteur de régulation démarré.")

    def stop(self, detach: bool = False):
        """Arrête la boucle de régulation."""
        if self.is_running:
            self.is_running = False
            self._stop_event.set()
            if self._thread and self._thread.is_alive() and self._thread is not threading.current_thread():
                self._thread.join(timeout=0.05)
            self._thread = None
            print("[SmartLOD] Moteur de régulation arrêté.")
        if detach:
            self.engine.detach()

    def set_enabled(self, enabled: bool, force_kill_autofps: bool = False) -> Dict[str, Any]:
        """Active ou désactive Smart LOD avec arbitrage de conflit AutoFPS."""
        from scanner import IS_LITE
        if IS_LITE:
            return {
                "success": False,
                "lite_locked": True,
                "enabled": False,
                "is_running": False,
                "error": "Smart LOD Governor is only available in SceneryX Pro."
            }
        if enabled:
            # 1. Recharger systématiquement le profil Smart LOD actif pour écraser tout réglage manuel précédent
            self.load_active_profile_into_config()

            # 2. Réinitialiser les débrayages manuels pour reprendre la régulation automatique dès le 1er clic
            with self._lock:
                self.manual_tlod = None
                self.manual_olod = None
                self.config["enabled"] = True
                self.config["source"] = "native"
                self.config["2d_tlod_active"] = True
                self.config["2d_olod_active"] = True
                self.config["vr_tlod_active"] = True
                self.config["vr_olod_active"] = True

                # S'assurer d'une plage dynamique floor -> cruise valide pour la régulation automatique
                if self.config.get("2d_tlod_base", 100) >= self.config.get("2d_tlod_target", 200):
                    self.config["2d_tlod_target"] = min(400, max(200, self.config.get("2d_tlod_base", 100) + 100))
                if self.config.get("vr_tlod_base", 90) >= self.config.get("vr_tlod_target", 150):
                    self.config["vr_tlod_target"] = min(400, max(150, self.config.get("vr_tlod_base", 90) + 80))
                if self.config.get("2d_olod_base", 100) >= self.config.get("2d_olod_target", 200):
                    self.config["2d_olod_target"] = min(300, max(150, self.config.get("2d_olod_base", 100) + 50))
                if self.config.get("vr_olod_base", 100) >= self.config.get("vr_olod_target", 150):
                    self.config["vr_olod_target"] = min(300, max(120, self.config.get("vr_olod_base", 100) + 50))

                is_vr = self.engine.is_vr_active() if self.engine.is_attached else False
                pfx = "vr" if is_vr else "2d"
                self.dynamic_tlod_floor = float(self.config.get(f"{pfx}_tlod_base", 100))
                self.dynamic_tlod_cruise = float(self.config.get(f"{pfx}_tlod_target", 200))
                self.dynamic_olod_floor = float(self.config.get(f"{pfx}_olod_base", 100))
                self.dynamic_olod_cruise = float(self.config.get(f"{pfx}_olod_target", 200))
                self.current_tlod_setpoint = float(self.dynamic_tlod_floor)
                self.current_olod_setpoint = float(self.dynamic_olod_floor)

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

            self.save_config({
                "enabled": True,
                "source": "native",
                "2d_tlod_active": True,
                "2d_olod_active": True,
                "vr_tlod_active": True,
                "vr_olod_active": True,
                "2d_tlod_base": self.config.get("2d_tlod_base", 100),
                "2d_tlod_target": self.config.get("2d_tlod_target", 200),
                "vr_tlod_base": self.config.get("vr_tlod_base", 90),
                "vr_tlod_target": self.config.get("vr_tlod_target", 150),
                "2d_olod_base": self.config.get("2d_olod_base", 100),
                "2d_olod_target": self.config.get("2d_olod_target", 200),
                "vr_olod_base": self.config.get("vr_olod_base", 100),
                "vr_olod_target": self.config.get("vr_olod_target", 150),
            })
            self.start()
            # Forcer un premier tick de régulation immédiat
            try:
                self._tick()
            except Exception:
                pass
            is_vr = self.engine.is_vr_active() if self.engine.is_attached else False
            pfx = "vr" if is_vr else "2d"
            return {
                "success": True,
                "conflict": False,
                "enabled": True,
                "current_tlod": round(self.current_tlod_setpoint, 1),
                "current_olod": round(self.current_olod_setpoint, 1),
                "tlod_base": int(round(getattr(self, "dynamic_tlod_floor", self.config.get(f"{pfx}_tlod_base", 100)))),
                "tlod_target": int(round(getattr(self, "dynamic_tlod_cruise", self.config.get(f"{pfx}_tlod_target", 200)))),
                "tlod_altitude": int(self.config.get(f"{pfx}_tlod_altitude", 3000)),
                "olod_base": int(round(getattr(self, "dynamic_olod_floor", self.config.get(f"{pfx}_olod_base", 100)))),
                "olod_target": int(round(getattr(self, "dynamic_olod_cruise", self.config.get(f"{pfx}_olod_target", 200)))),
                "olod_altitude": int(self.config.get(f"{pfx}_olod_altitude", 3000)),
            }
        else:
            nom_vals = get_active_profile_nominal_values()
            nom_tlod = int(round(float(nom_vals.get("tlod", 100.0))))
            nom_olod = int(round(float(nom_vals.get("olod", 100.0))))
            cruise_tlod = min(400, nom_tlod + 50)
            cruise_olod = min(300, nom_olod + 50)

            with self._lock:
                self.manual_tlod = None
                self.manual_olod = None
                self.config["enabled"] = False
                self.config["2d_tlod_active"] = False
                self.config["2d_olod_active"] = False
                self.config["vr_tlod_active"] = False
                self.config["vr_olod_active"] = False
                self.config["2d_tlod_base"] = nom_tlod
                self.config["2d_tlod_target"] = cruise_tlod
                self.config["vr_tlod_base"] = nom_tlod
                self.config["vr_tlod_target"] = cruise_tlod
                self.config["2d_olod_base"] = nom_olod
                self.config["2d_olod_target"] = cruise_olod
                self.config["vr_olod_base"] = nom_olod
                self.config["vr_olod_target"] = cruise_olod
                self.dynamic_tlod_floor = float(nom_tlod)
                self.dynamic_tlod_cruise = float(cruise_tlod)
                self.dynamic_olod_floor = float(nom_olod)
                self.dynamic_olod_cruise = float(cruise_olod)

            self.save_config({
                "enabled": False,
                "2d_tlod_active": False,
                "2d_olod_active": False,
                "vr_tlod_active": False,
                "vr_olod_active": False,
                "2d_tlod_base": nom_tlod,
                "2d_tlod_target": cruise_tlod,
                "vr_tlod_base": nom_tlod,
                "vr_tlod_target": cruise_tlod,
                "2d_olod_base": nom_olod,
                "2d_olod_target": cruise_olod,
                "vr_olod_base": nom_olod,
                "vr_olod_target": cruise_olod,
            })
            if not self.config.get("cloud_recovery", True):
                self.stop(detach=False)
            self.status_message = "MAN"
            self.current_tlod_setpoint = float(nom_tlod)
            self.current_olod_setpoint = float(nom_olod)

            def _async_reset_lod():
                try:
                    self.reset_to_active_profile("lod")
                except Exception:
                    pass
            threading.Thread(target=_async_reset_lod, daemon=True, name="AsyncLodReset").start()

            return {
                "success": True,
                "conflict": False,
                "enabled": False,
                "nominal_tlod": nom_tlod,
                "nominal_olod": nom_olod,
                "tlod": nom_tlod,
                "olod": nom_olod,
                "tlod_base": nom_tlod,
                "tlod_target": cruise_tlod,
                "olod_base": nom_olod,
                "olod_target": cruise_olod,
                "reset_info": {"success": True, "axis": "lod"}
            }

    # ================= REGULATION ALGORITHM =================

    def _worker_loop(self):
        """Boucle de travail principale exécutée à ~1 Hz."""
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception as e:
                self.status_message = f"Erreur régulation: {e}"
            self._stop_event.wait(1.0)

    def _tick(self):
        lod_enabled = bool(self.config.get("enabled", False))
        cloud_rec_enabled = bool(self.config.get("cloud_recovery", True))
        if (not lod_enabled and not cloud_rec_enabled) or self.config.get("external_autofps", False):
            self.status_message = "Handled by External AutoFPS" if self.config.get("external_autofps", False) else "Désactivé"
            return

        # 1. Vérifier la présence d'AutoFPS externe
        af_running, _ = self.engine.is_autofps_running()
        if af_running:
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
        tlod_is_active = bool(lod_enabled and self.config.get(f"{pfx}_tlod_active", False))
        olod_is_active = bool(lod_enabled and self.config.get(f"{pfx}_olod_active", False))
        cloud_rec_enabled = bool(self.config.get(f"{pfx}_cloud_recovery", self.config.get("cloud_recovery", True)))

        if not tlod_is_active and not olod_is_active and not cloud_rec_enabled:
            self.status_message = f"Standby (No {pfx.upper()} LOD axis active)"
            return

        # Récupérer la télémétrie de vol depuis flight_perf_tracker
        telemetry = self._get_live_flight_telemetry()
        agl = telemetry.get("agl_ft", 0) or 0
        on_ground = telemetry.get("on_ground", False)
        base_fps = telemetry.get("base_fps", 0) or telemetry.get("displayed_fps", 0) or 0
        main_thread_ms = telemetry.get("main_thread_ms")
        vram_pct = telemetry.get("vram_pct", 0.0) or 0.0

        target_fps = float(self.config.get("vr_target_fps", 36) if is_vr else self.config.get("2d_target_fps", self.config.get("ifr_target_fps", 40)))
        target_mt_ms = 1000.0 / max(15.0, target_fps)
        deadband = float(self.config.get("deadband_fps", 2))
        step = float(self.config.get("step_size", 5))

        # Calcul des pressions et marges de performance
        fps_deficit = (target_fps - base_fps) if (base_fps > 0 and base_fps < (target_fps - deadband)) else 0.0
        fps_surplus = (base_fps - (target_fps + deadband)) if (base_fps > (target_fps + deadband)) else 0.0

        mt_excess_ms = (main_thread_ms - target_mt_ms) if (main_thread_ms and main_thread_ms > (target_mt_ms + 1.0)) else 0.0
        mt_headroom_ms = (target_mt_ms - 2.0 - main_thread_ms) if (main_thread_ms and main_thread_ms < (target_mt_ms - 2.0)) else 0.0

        vram_saturated = (vram_pct >= 0.88)

        ok_tlod = True
        ok_olod = True

        # 4. Gestion intelligente du Terrain LOD (TLOD) si activé
        if tlod_is_active:
            tlod_cruise = float(self.config.get(f"{pfx}_tlod_target", 200 if pfx == "2d" else 150))
            tlod_ground = float(self.config.get(f"{pfx}_tlod_base", 100 if pfx == "2d" else 90))
            alt_trans = float(self.config.get(f"{pfx}_tlod_altitude", 5000 if pfx == "2d" else 4000))

            if not hasattr(self, "dynamic_tlod_floor") or self.dynamic_tlod_floor is None:
                self.dynamic_tlod_floor = tlod_ground
            if not hasattr(self, "dynamic_tlod_cruise") or self.dynamic_tlod_cruise is None:
                self.dynamic_tlod_cruise = tlod_cruise

            if getattr(self, "manual_tlod", None) is not None:
                self.current_tlod_setpoint = float(self.manual_tlod)
                self.dynamic_tlod_floor = float(self.manual_tlod)
                self.dynamic_tlod_cruise = min(400.0, float(self.manual_tlod) + 50.0)
            else:
                # 1. Calcul du ratio d'altitude AGL
                min_alt = min(500.0, alt_trans)
                alt_span = max(1.0, alt_trans - min_alt)
                if on_ground or agl < min_alt:
                    ratio = 0.0
                elif agl >= alt_trans:
                    ratio = 1.0
                else:
                    ratio = max(0.0, min(1.0, (agl - min_alt) / alt_span))

                # 2. Régulation adaptative des bornes Floor et Cruise selon la performance
                if mt_excess_ms > 0 or fps_deficit > 0:
                    strain_factor = max(mt_excess_ms / max(1.0, target_mt_ms), fps_deficit / max(1.0, target_fps))
                    reduction = step * (1.0 + min(2.5, strain_factor * 3.0))
                    # Au sol / basse altitude, réduire le Floor vers la gauche pour libérer la charge
                    if ratio < 0.5:
                        min_flr = max(20.0, tlod_ground * 0.45)
                        self.dynamic_tlod_floor = max(min_flr, self.dynamic_tlod_floor - reduction)
                        if self.dynamic_tlod_cruise > tlod_cruise:
                            self.dynamic_tlod_cruise = max(self.dynamic_tlod_floor + 20.0, self.dynamic_tlod_cruise - reduction)
                    else:
                        # En vol / croisière, réduire Cruise vers la gauche
                        min_cru = max(self.dynamic_tlod_floor + 10.0, tlod_cruise * 0.55)
                        self.dynamic_tlod_cruise = max(min_cru, self.dynamic_tlod_cruise - reduction)
                elif vram_saturated:
                    if self.dynamic_tlod_cruise > tlod_cruise:
                        self.dynamic_tlod_cruise = max(tlod_cruise, self.dynamic_tlod_cruise - step)
                elif fps_surplus > 0 or mt_headroom_ms > 0 or (base_fps == 0 and main_thread_ms is None):
                    # Capital performance disponible :
                    # 1. Rétablir Floor vers la valeur nominale
                    if self.dynamic_tlod_floor < tlod_ground:
                        self.dynamic_tlod_floor = min(tlod_ground, self.dynamic_tlod_floor + step)
                    # 2. Augmenter Cruise vers la droite si surplus de perf et pas de saturation VRAM
                    if (fps_surplus > 0 or mt_headroom_ms > 0) and (not vram_saturated):
                        max_cruise_headroom = min(400.0, max(tlod_cruise, tlod_cruise + 100.0))
                        self.dynamic_tlod_cruise = min(max_cruise_headroom, self.dynamic_tlod_cruise + step)

                # Garantir bornes cohérentes
                self.dynamic_tlod_floor = max(10.0, min(400.0, self.dynamic_tlod_floor))
                self.dynamic_tlod_cruise = max(self.dynamic_tlod_floor, min(400.0, self.dynamic_tlod_cruise))

                # Setpoint injecté dans MSFS selon l'altitude actuelle
                target_tlod = self.dynamic_tlod_floor + ratio * (self.dynamic_tlod_cruise - self.dynamic_tlod_floor)
                self.current_tlod_setpoint = max(10.0, min(400.0, round(target_tlod)))

            ok_tlod = self.engine.write_tlod(self.current_tlod_setpoint)

        # 5. Gestion intelligente de l'Object LOD (OLOD) si activé
        if olod_is_active:
            olod_cruise = float(self.config.get(f"{pfx}_olod_target", 100 if pfx == "2d" else 80))
            olod_ground = float(self.config.get(f"{pfx}_olod_base", 100 if pfx == "2d" else 80))
            alt_trans_olod = float(self.config.get(f"{pfx}_olod_altitude", 3000 if pfx == "2d" else 2500))

            if not hasattr(self, "dynamic_olod_floor") or self.dynamic_olod_floor is None:
                self.dynamic_olod_floor = olod_ground
            if not hasattr(self, "dynamic_olod_cruise") or self.dynamic_olod_cruise is None:
                self.dynamic_olod_cruise = olod_cruise

            if getattr(self, "manual_olod", None) is not None:
                self.current_olod_setpoint = float(self.manual_olod)
                self.dynamic_olod_floor = float(self.manual_olod)
                self.dynamic_olod_cruise = min(300.0, float(self.manual_olod) + 50.0)
            else:
                # 1. Calcul du ratio d'altitude AGL
                if on_ground or agl < 500:
                    ratio_olod = 0.0
                elif agl >= alt_trans_olod:
                    ratio_olod = 1.0
                else:
                    ratio_olod = max(0.0, min(1.0, agl / max(1.0, alt_trans_olod)))

                # 2. Régulation adaptative Floor & Cruise
                if mt_excess_ms > 0 or fps_deficit > 0:
                    strain_factor = max(mt_excess_ms / max(1.0, target_mt_ms), fps_deficit / max(1.0, target_fps))
                    reduction = step * (1.0 + min(2.0, strain_factor * 2.5))
                    if ratio_olod < 0.5:
                        min_flr_o = max(20.0, olod_ground * 0.45)
                        self.dynamic_olod_floor = max(min_flr_o, self.dynamic_olod_floor - reduction)
                        if self.dynamic_olod_cruise > olod_cruise:
                            self.dynamic_olod_cruise = max(self.dynamic_olod_floor + 15.0, self.dynamic_olod_cruise - reduction)
                    else:
                        min_cru_o = max(self.dynamic_olod_floor + 10.0, olod_cruise * 0.55)
                        self.dynamic_olod_cruise = max(min_cru_o, self.dynamic_olod_cruise - reduction)
                elif fps_surplus > 0 or mt_headroom_ms > 0 or (base_fps == 0 and main_thread_ms is None):
                    if self.dynamic_olod_floor < olod_ground:
                        self.dynamic_olod_floor = min(olod_ground, self.dynamic_olod_floor + step)
                    if (fps_surplus > 0 or mt_headroom_ms > 0):
                        max_olod_headroom = min(300.0, max(olod_cruise, olod_cruise + 80.0))
                        self.dynamic_olod_cruise = min(max_olod_headroom, self.dynamic_olod_cruise + step)

                self.dynamic_olod_floor = max(10.0, min(300.0, self.dynamic_olod_floor))
                self.dynamic_olod_cruise = max(self.dynamic_olod_floor, min(300.0, self.dynamic_olod_cruise))

                target_olod = self.dynamic_olod_floor + ratio_olod * (self.dynamic_olod_cruise - self.dynamic_olod_floor)
                self.current_olod_setpoint = max(10.0, min(300.0, round(target_olod)))

            ok_olod = self.engine.write_olod(self.current_olod_setpoint)

        # 6. Auto Cloud Recovery (100% indépendant du Smart LOD)
        if cloud_rec_enabled:
            nom_q = get_nominal_cloud_quality()
            cur_q = max(0, min(3, int(getattr(self, "current_cloud_quality", nom_q))))
            self.current_cloud_quality = cur_q
            now_ts = time.time()
            last_cloud_ts = getattr(self, "_last_cloud_change_time", 0.0)

            # Si cur_q était au-dessus de la valeur nominale (ex: Ultra manuel précédent), ramener immédiatement à la valeur nominale du profil
            if cur_q > nom_q:
                new_q = nom_q
                self.engine.write_cloud_quality(new_q)
                self.current_cloud_quality = new_q
                self.in_cloud_reduction = False
                self.in_cloud_boost = False
                self._last_cloud_change_time = now_ts
            # A. Déficit FPS significatif : réduire d'1 cran (jusqu'à 0=Low) avec cooldown 8s
            elif base_fps > 0 and base_fps < (target_fps - 5):
                if cur_q > 0 and (now_ts - last_cloud_ts >= 8.0):
                    if self.original_cloud_quality is None:
                        self.original_cloud_quality = nom_q
                    new_q = max(0, cur_q - 1)
                    if self.engine.write_cloud_quality(new_q):
                        self.current_cloud_quality = new_q
                        self.in_cloud_reduction = (new_q < nom_q)
                        self.in_cloud_boost = False
                        self._last_cloud_change_time = now_ts
                        self.trigger_events.append({
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "agl_ft": round(agl),
                            "tlod": round(self.current_tlod_setpoint),
                            "fps": round(base_fps, 1),
                            "reason": f"Cloud Quality Step-Down: {CLOUD_QUALITY_LABELS.get(cur_q, cur_q)} -> {CLOUD_QUALITY_LABELS.get(new_q, new_q)}"
                        })
                        print(f"[SmartLOD] Cloud Recovery step-down: {CLOUD_QUALITY_LABELS.get(cur_q)} ({cur_q}) -> {CLOUD_QUALITY_LABELS.get(new_q)} ({new_q}) (FPS: {round(base_fps)} < {target_fps - 5})")
            # B. FPS revenu à la cible : remonter progressivement jusqu'à la valeur nominale du profil (ex: High)
            elif (base_fps >= target_fps or base_fps == 0) and cur_q < nom_q:
                if now_ts - last_cloud_ts >= 8.0:
                    new_q = min(nom_q, cur_q + 1)
                    if self.engine.write_cloud_quality(new_q):
                        self.current_cloud_quality = new_q
                        self.in_cloud_reduction = (new_q < nom_q)
                        self.in_cloud_boost = False
                        self._last_cloud_change_time = now_ts
                        self.trigger_events.append({
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "agl_ft": round(agl),
                            "tlod": round(self.current_tlod_setpoint),
                            "fps": round(base_fps, 1),
                            "reason": f"Cloud Quality Restored: {CLOUD_QUALITY_LABELS.get(cur_q, cur_q)} -> {CLOUD_QUALITY_LABELS.get(new_q, new_q)}"
                        })
                        print(f"[SmartLOD] Cloud Recovery restored: {CLOUD_QUALITY_LABELS.get(cur_q)} ({cur_q}) -> {CLOUD_QUALITY_LABELS.get(new_q)} ({new_q}) (FPS: {round(base_fps)} >= {target_fps})")

        if ok_tlod and ok_olod:
            status_parts = []
            if tlod_is_active:
                status_parts.append(f"TLOD {round(self.current_tlod_setpoint)}")
            if olod_is_active:
                status_parts.append(f"OLOD {round(self.current_olod_setpoint)}")
            status_parts.append(f"CLOUDS {CLOUD_QUALITY_LABELS.get(self.current_cloud_quality, 'HIGH')}")
            self.status_message = f"Smart LOD Active • {' | '.join(status_parts)} • {pfx.upper()} ({round(base_fps)} FPS)"
        else:
            self.status_message = "Erreur d'écriture mémoire"

    def _get_live_flight_telemetry(self) -> Dict[str, Any]:
        """Extrait la télémétrie courante de SimConnect ou du tracker de SceneryX."""
        res = {
            "agl_ft": 0,
            "on_ground": True,
            "base_fps": 0,
            "displayed_fps": 0,
            "main_thread_ms": None,
            "vram_pct": 0.0,
            "vram_used_mb": 0,
            "vram_total_mb": 16376,
            "cache_read_mbps": 0.0
        }
        try:
            import flight_perf_tracker
            # 1. Direct from Blackbox tracker if active
            if hasattr(flight_perf_tracker, 'BLACKBOX') and flight_perf_tracker.BLACKBOX:
                telem = flight_perf_tracker.BLACKBOX.get_panel_telemetry() if hasattr(flight_perf_tracker.BLACKBOX, 'get_panel_telemetry') else flight_perf_tracker.BLACKBOX.get_telemetry()
                if telem:
                    agl = telem.get("agl_ft") or telem.get("agl") or 0
                    res["agl_ft"] = agl
                    res["on_ground"] = bool(telem.get("on_ground", agl < 50))
                    res["base_fps"] = telem.get("base_fps") or telem.get("displayed_fps") or 0
                    res["displayed_fps"] = telem.get("displayed_fps") or 0
                    res["main_thread_ms"] = telem.get("main_thread_ms")
                    res["vram_pct"] = telem.get("vram_pct") or 0.0
                    res["vram_used_mb"] = telem.get("vram_used_mb") or 0
                    res["vram_total_mb"] = telem.get("vram_total_mb") or 16376
                    res["cache_read_mbps"] = telem.get("cache_read_mbps") or 0.0
                    return res

            # 2. Direct from live SimConnect client if active
            if hasattr(flight_perf_tracker, 'SIMCONNECT_CLIENT') and flight_perf_tracker.SIMCONNECT_CLIENT:
                sc_data = flight_perf_tracker.SIMCONNECT_CLIENT.get_data()
                if sc_data.get("connected"):
                    agl = sc_data.get("agl_ft")
                    on_ground = sc_data.get("on_ground")
                    if on_ground is None:
                        on_ground = (agl is None or agl < 50)
                    res["agl_ft"] = agl or 0
                    res["on_ground"] = bool(on_ground)
                    res["base_fps"] = sc_data.get("base_fps") or sc_data.get("displayed_fps") or 0
                    res["displayed_fps"] = sc_data.get("displayed_fps") or 0
                    res["main_thread_ms"] = sc_data.get("main_thread_ms")
                    return res

            # 3. Direct from cache
            if hasattr(flight_perf_tracker, '_last_telemetry_cache') and flight_perf_tracker._last_telemetry_cache:
                c = flight_perf_tracker._last_telemetry_cache
                agl = c.get("agl_ft") or c.get("agl") or 0
                res["agl_ft"] = agl
                res["on_ground"] = bool(agl < 50)
                res["base_fps"] = c.get("base_fps") or c.get("displayed_fps") or 0
                res["displayed_fps"] = c.get("displayed_fps") or 0
                res["main_thread_ms"] = c.get("main_thread_ms")
                return res
        except Exception:
            pass
        return res

    # ================= STATUS API =================

    def get_status(self) -> Dict[str, Any]:
        """Retourne l'état complet pour l'UI Web."""
        mem_status = self.engine.get_status()
        is_af_running, af_pid = self.engine.is_autofps_running()
        is_vr = self.engine.is_vr_active() if (self.engine.is_attached and not self.engine.safe_read_only) else False
        nom_vals = get_active_profile_nominal_values(is_vr=is_vr)
        is_ext = bool(self.config.get("external_autofps", False) or (self.config.get("source") == "external_autofps") or is_af_running)
        nom_cloud_q = max(0, min(3, int(nom_vals.get("clouds", 2))))
        override_cloud_q = _LIVE_GRAPHICS_OVERRIDES.get("clouds")
        cloud_rec_active = bool(self.config.get("cloud_recovery", True) and not is_ext)

        if cloud_rec_active:
            cur_cloud_q = max(0, min(3, int(getattr(self, "current_cloud_quality", nom_cloud_q))))
            if cur_cloud_q > nom_cloud_q:
                cur_cloud_q = nom_cloud_q
                self.current_cloud_quality = nom_cloud_q
        elif override_cloud_q is not None:
            cur_cloud_q = max(0, min(3, int(override_cloud_q)))
            self.current_cloud_quality = cur_cloud_q
        else:
            cur_cloud_q = max(0, min(3, int(getattr(self, "current_cloud_quality", nom_cloud_q))))

        return {
            "enabled": (self.config.get("enabled", False) and not is_ext),
            "external_autofps": is_ext,
            "is_running": (self.is_running and not is_ext),
            "status_message": "Verrouillé (AutoFPS externe actif)" if is_ext else self.status_message,
            "current_tlod_setpoint": round(self.current_tlod_setpoint, 1),
            "current_olod_setpoint": round(self.current_olod_setpoint, 1),
            "nominal_tlod": nom_vals.get("tlod", 100.0),
            "nominal_olod": nom_vals.get("olod", 100.0),
            "nominal_profile": nom_vals.get("name", "Active Profile"),
            "is_vr": is_vr,
            "manual_tlod": self.manual_tlod is not None,
            "manual_olod": self.manual_olod is not None,
            "axis_state_2d": self.get_axis_state("2D"),
            "axis_state_vr": self.get_axis_state("VR"),
            "mode": self.config.get("mode", "IFR"),
            "source": self.config.get("source", "native"),
            "autofps_conflict": is_af_running,
            "autofps_pid": af_pid,
            "ofxr_running": mem_status.get("ofxr_running", False),
            "ofxr_pid": mem_status.get("ofxr_pid"),
            "memory": mem_status,
            "config": self.config,
            "cloud_recovery": bool(self.config.get("cloud_recovery", True)),
            "current_cloud_quality": cur_cloud_q,
            "current_cloud_label": CLOUD_QUALITY_LABELS.get(cur_cloud_q, "HIGH"),
            "nominal_cloud_quality": nom_cloud_q,
            "nominal_cloud_label": CLOUD_QUALITY_LABELS.get(nom_cloud_q, "HIGH"),
            "in_cloud_reduction": bool(cloud_rec_active and cur_cloud_q < nom_cloud_q),
            "in_cloud_boost": False,
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


def _sanitize_smart_lod_profile_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures Smart LOD profile strictly contains only TLOD/OLOD floor, cruise, altitude, and cloud recovery for 2D & VR. Strips target_fps."""
    data.pop("target_fps", None)
    data.pop("ifr_target_fps", None)
    data.pop("vfr_target_fps", None)
    data.pop("mode", None)
    data.pop("flight_mode", None)

    # 2D fallbacks (100 - 200 at 3000 ft)
    data["ground_tlod"] = int(data.get("ground_tlod", 100))
    data["cruise_tlod"] = int(data.get("cruise_tlod", 200))
    data["alt_trans"] = int(data.get("alt_trans", 3000))
    data["ground_olod"] = int(data.get("ground_olod", 100))
    data["cruise_olod"] = int(data.get("cruise_olod", 200))
    data["alt_trans_olod"] = int(data.get("alt_trans_olod", 3000))
    data["cloud_recovery"] = bool(data.get("cloud_recovery", True))

    # VR fallbacks
    data["vr_ground_tlod"] = int(data.get("vr_ground_tlod", data["ground_tlod"]))
    data["vr_cruise_tlod"] = int(data.get("vr_cruise_tlod", data["cruise_tlod"]))
    data["vr_alt_trans"] = int(data.get("vr_alt_trans", data["alt_trans"]))
    data["vr_ground_olod"] = int(data.get("vr_ground_olod", data["ground_olod"]))
    data["vr_cruise_olod"] = int(data.get("vr_cruise_olod", data["cruise_olod"]))
    data["vr_alt_trans_olod"] = int(data.get("vr_alt_trans_olod", data["alt_trans_olod"]))
    data["vr_cloud_recovery"] = bool(data.get("vr_cloud_recovery", data["cloud_recovery"]))

    return data


def generate_default_smart_lod_profiles() -> List[Dict[str, Any]]:
    """Generates standard calibrated Smart LOD profiles for flight simmers."""
    profiles_dir = get_smart_lod_profiles_dir()
    defaults = [
        {
            "id": "lod_prof_balanced_airliner",
            "name": "Balanced Airliner",
            "description": "Standard setpoint: TLOD 100-200, OLOD 100-200 at 3000 ft transition.",
            "ground_tlod": 100,
            "cruise_tlod": 200,
            "alt_trans": 3000,
            "ground_olod": 100,
            "cruise_olod": 200,
            "alt_trans_olod": 3000,
            "cloud_recovery": True,
            "vr_ground_tlod": 100,
            "vr_cruise_tlod": 200,
            "vr_alt_trans": 3000,
            "vr_ground_olod": 100,
            "vr_cruise_olod": 200,
            "vr_alt_trans_olod": 3000,
            "vr_cloud_recovery": True,
            "created_at": "2026-01-01T00:00:00"
        },
        {
            "id": "lod_prof_heavy_hub_optimizer",
            "name": "Heavy Hub & Megacity",
            "description": "Maximum FPS protection at congested payware hubs: TLOD 80-180, OLOD 80-150.",
            "ground_tlod": 80,
            "cruise_tlod": 180,
            "alt_trans": 3000,
            "ground_olod": 80,
            "cruise_olod": 150,
            "alt_trans_olod": 3000,
            "cloud_recovery": True,
            "vr_ground_tlod": 80,
            "vr_cruise_tlod": 160,
            "vr_alt_trans": 3000,
            "vr_ground_olod": 80,
            "vr_cruise_olod": 150,
            "vr_alt_trans_olod": 3000,
            "vr_cloud_recovery": True,
            "created_at": "2026-01-01T00:01:00"
        },
        {
            "id": "lod_prof_vfr_bush_sightseeing",
            "name": "VFR Bush & Mountains",
            "description": "Pristine terrain relief: TLOD 120-250, OLOD 100-200 at 3000 ft.",
            "ground_tlod": 120,
            "cruise_tlod": 250,
            "alt_trans": 3000,
            "ground_olod": 100,
            "cruise_olod": 200,
            "alt_trans_olod": 3000,
            "cloud_recovery": True,
            "vr_ground_tlod": 100,
            "vr_cruise_tlod": 200,
            "vr_alt_trans": 3000,
            "vr_ground_olod": 100,
            "vr_cruise_olod": 200,
            "vr_alt_trans_olod": 3000,
            "vr_cloud_recovery": True,
            "created_at": "2026-01-01T00:02:00"
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
                data = _sanitize_smart_lod_profile_data(data)
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

    sanitized = _sanitize_smart_lod_profile_data(config_data.copy())
    profile_obj = {
        "id": target_id,
        "name": clean_name,
        "ground_tlod": sanitized["ground_tlod"],
        "cruise_tlod": sanitized["cruise_tlod"],
        "alt_trans": sanitized["alt_trans"],
        "ground_olod": sanitized["ground_olod"],
        "cruise_olod": sanitized["cruise_olod"],
        "alt_trans_olod": sanitized["alt_trans_olod"],
        "cloud_recovery": sanitized["cloud_recovery"],
        "vr_ground_tlod": sanitized["vr_ground_tlod"],
        "vr_cruise_tlod": sanitized["vr_cruise_tlod"],
        "vr_alt_trans": sanitized["vr_alt_trans"],
        "vr_ground_olod": sanitized["vr_ground_olod"],
        "vr_cruise_olod": sanitized["vr_cruise_olod"],
        "vr_alt_trans_olod": sanitized["vr_alt_trans_olod"],
        "vr_cloud_recovery": sanitized["vr_cloud_recovery"],
        "created_at": datetime.now().isoformat()
    }

    file_path = os.path.join(profiles_dir, f"{target_id}.lodprofile.json")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(profile_obj, f, indent=2, ensure_ascii=False)
        set_active_smart_lod_profile_id(target_id)
        
        # Apply to live smart lod controller without touching target_fps
        ctrl = get_smart_lod_controller()
        cfg_update = {
            "cloud_recovery": profile_obj["cloud_recovery"],
            "2d_tlod_base": profile_obj["ground_tlod"],
            "2d_tlod_target": profile_obj["cruise_tlod"],
            "2d_tlod_altitude": profile_obj["alt_trans"],
            "2d_olod_base": profile_obj["ground_olod"],
            "2d_olod_target": profile_obj["cruise_olod"],
            "2d_olod_altitude": profile_obj["alt_trans_olod"],
            "vr_tlod_base": profile_obj["vr_ground_tlod"],
            "vr_tlod_target": profile_obj["vr_cruise_tlod"],
            "vr_tlod_altitude": profile_obj["vr_alt_trans"],
            "vr_olod_base": profile_obj["vr_ground_olod"],
            "vr_olod_target": profile_obj["vr_cruise_olod"],
            "vr_olod_altitude": profile_obj["vr_alt_trans_olod"],
            # Legacy mirror
            "ifr_tlod_ground": profile_obj["ground_tlod"],
            "ifr_tlod_cruise": profile_obj["cruise_tlod"],
            "ifr_alt_transition": profile_obj["alt_trans"],
            "ifr_olod_ground": profile_obj["ground_olod"],
            "ifr_olod_cruise": profile_obj["cruise_olod"],
            "vfr_tlod_ground": profile_obj["ground_tlod"],
            "vfr_tlod_cruise": profile_obj["cruise_tlod"],
            "vfr_alt_transition": profile_obj["alt_trans"],
            "vfr_olod_ground": profile_obj["ground_olod"],
            "vfr_olod_cruise": profile_obj["cruise_olod"],
        }
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
        pdata = _sanitize_smart_lod_profile_data(pdata)
        curr = _sanitize_smart_lod_profile_data(current_data)
        
        has_changes = (
            pdata["ground_tlod"] != curr["ground_tlod"] or
            pdata["cruise_tlod"] != curr["cruise_tlod"] or
            pdata["alt_trans"] != curr["alt_trans"] or
            pdata["ground_olod"] != curr["ground_olod"] or
            pdata["cruise_olod"] != curr["cruise_olod"] or
            pdata["alt_trans_olod"] != curr["alt_trans_olod"] or
            pdata["cloud_recovery"] != curr["cloud_recovery"] or
            pdata["vr_ground_tlod"] != curr["vr_ground_tlod"] or
            pdata["vr_cruise_tlod"] != curr["vr_cruise_tlod"] or
            pdata["vr_alt_trans"] != curr["vr_alt_trans"] or
            pdata["vr_ground_olod"] != curr["vr_ground_olod"] or
            pdata["vr_cruise_olod"] != curr["vr_cruise_olod"] or
            pdata["vr_alt_trans_olod"] != curr["vr_alt_trans_olod"] or
            pdata["vr_cloud_recovery"] != curr["vr_cloud_recovery"]
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
        pdata = _sanitize_smart_lod_profile_data(pdata)
        set_active_smart_lod_profile_id(profile_id)
        ctrl = get_smart_lod_controller()

        g_tlod_2d = pdata["ground_tlod"]
        c_tlod_2d = pdata["cruise_tlod"]
        a_tlod_2d = pdata["alt_trans"]
        g_olod_2d = pdata["ground_olod"]
        c_olod_2d = pdata["cruise_olod"]
        a_olod_2d = pdata["alt_trans_olod"]
        cloud_rec_2d = pdata["cloud_recovery"]

        g_tlod_vr = pdata["vr_ground_tlod"]
        c_tlod_vr = pdata["vr_cruise_tlod"]
        a_tlod_vr = pdata["vr_alt_trans"]
        g_olod_vr = pdata["vr_ground_olod"]
        c_olod_vr = pdata["vr_cruise_olod"]
        a_olod_vr = pdata["vr_alt_trans_olod"]
        cloud_rec_vr = pdata["vr_cloud_recovery"]

        cfg_update = {
            "cloud_recovery": cloud_rec_2d,
            "2d_tlod_base": g_tlod_2d,
            "2d_tlod_target": c_tlod_2d,
            "2d_tlod_altitude": a_tlod_2d,
            "2d_olod_base": g_olod_2d,
            "2d_olod_target": c_olod_2d,
            "2d_olod_altitude": a_olod_2d,
            "vr_tlod_base": g_tlod_vr,
            "vr_tlod_target": c_tlod_vr,
            "vr_tlod_altitude": a_tlod_vr,
            "vr_olod_base": g_olod_vr,
            "vr_olod_target": c_olod_vr,
            "vr_olod_altitude": a_olod_vr,
            # Legacy mirror
            "ifr_tlod_ground": g_tlod_2d,
            "ifr_tlod_cruise": c_tlod_2d,
            "ifr_alt_transition": a_tlod_2d,
            "ifr_olod_ground": g_olod_2d,
            "ifr_olod_cruise": c_olod_2d,
            "vfr_tlod_ground": g_tlod_2d,
            "vfr_tlod_cruise": c_tlod_2d,
            "vfr_alt_transition": a_tlod_2d,
            "vfr_olod_ground": g_olod_2d,
            "vfr_olod_cruise": c_olod_2d,
        }
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


def set_vr_target_fps(fps: int) -> bool:
    try:
        ctrl = get_smart_lod_controller()
        return ctrl.save_config({"vr_target_fps": int(fps)})
    except Exception as e:
        print(f"[SmartLOD] Error setting vr_target_fps: {e}")
        return False

