#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SceneryX Smart LOD - Win32 Memory Engine
Permet l'accès sécurisé en lecture et écriture aux paramètres graphiques
de Microsoft Flight Simulator (2020 et 2024) via les APIs natives de Windows.
Aucune dépendance externe (.NET / C#) requise.
"""

import os
import sys
import time
import ctypes
import ctypes.wintypes
import subprocess
from typing import Optional, Tuple, Dict, Any

# Constantes Win32 pour l'accès mémoire
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
psapi = ctypes.WinDLL('psapi', use_last_error=True)

# Structures Win32
class MODULEENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.wintypes.DWORD),
        ("th32ModuleID", ctypes.wintypes.DWORD),
        ("th32ProcessID", ctypes.wintypes.DWORD),
        ("GlblcntUsage", ctypes.wintypes.DWORD),
        ("ProccntUsage", ctypes.wintypes.DWORD),
        ("modBaseAddr", ctypes.c_void_p),
        ("modBaseSize", ctypes.wintypes.DWORD),
        ("hModule", ctypes.wintypes.HMODULE),
        ("szModule", ctypes.c_char * 256),
        ("szExePath", ctypes.c_char * 260)
    ]

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.wintypes.DWORD),
        ("cntUsage", ctypes.wintypes.DWORD),
        ("th32ProcessID", ctypes.wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", ctypes.wintypes.DWORD),
        ("cntThreads", ctypes.wintypes.DWORD),
        ("th32ParentProcessID", ctypes.wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("szExeFile", ctypes.c_char * 260)
    ]

# Signatures des fonctions kernel32
kernel32.OpenProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]
kernel32.OpenProcess.restype = ctypes.wintypes.HANDLE

kernel32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
kernel32.CloseHandle.restype = ctypes.wintypes.BOOL

kernel32.ReadProcessMemory.argtypes = [
    ctypes.wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
]
kernel32.ReadProcessMemory.restype = ctypes.wintypes.BOOL

kernel32.WriteProcessMemory.argtypes = [
    ctypes.wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
]
kernel32.WriteProcessMemory.restype = ctypes.wintypes.BOOL

kernel32.CreateToolhelp32Snapshot.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.DWORD]
kernel32.CreateToolhelp32Snapshot.restype = ctypes.wintypes.HANDLE

kernel32.Process32First.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
kernel32.Process32First.restype = ctypes.wintypes.BOOL

kernel32.Process32Next.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
kernel32.Process32Next.restype = ctypes.wintypes.BOOL

kernel32.Module32First.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32)]
kernel32.Module32First.restype = ctypes.wintypes.BOOL

kernel32.Module32Next.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32)]
kernel32.Module32Next.restype = ctypes.wintypes.BOOL


class FlightMemoryEngine:
    """
    Moteur de manipulation mémoire Win32 pour MSFS 2020 et MSFS 2024.
    """

    # Offsets relatifs identifiés par rétro-ingénierie
    OFFSETS_2024 = {
        'default_module_base': 0x0A5BFF94,
        'sim_module': 'FlightSimulator2024.exe',
        'tlod': 0x358,
        'olod': 0x36C,
        'cloud_q': 0x3A4,
        'dyn_set': 0x32C,
        'dyn_set_vr': 0x32D,
        'dyn_set_target_fps': 0x330,
        'dyn_set_target_fps_vr': 0x334,
        'vr_mode': 0x338,
        'ost_precaching': 0x368,
        'terrain_shadows': 0x390,
        'tshadows_enabled': 0x38C,
        'buildings': 0x414,
        'trees': 0x418,
        'plants': 0x41C,
        'grass': 0x424,
    }

    OFFSETS_2020 = {
        'default_module_base': 0x004B2368,
        'sim_module': 'FlightSimulator.exe',
        'pointer_main': 0x0,
        'tlod': 0x0,
        'olod': 0x0,
        'cloud_q': 0x0
    }

    def __init__(self):
        self.process_handle: Optional[int] = None
        self.pid: Optional[int] = None
        self.exe_name: str = ""
        self.is_2024: bool = False
        self.module_base_address: int = 0
        self.offset_module_base: int = 0
        
        # Adresses directes calculées
        self.addr_tlod: int = 0
        self.addr_olod: int = 0
        self.addr_cloud_q: int = 0
        self.addr_dyn_set: int = 0
        self.addr_vr_mode: int = 0
        
        # État et sécurité
        self.is_attached: bool = False
        self.safe_read_only: bool = True
        self.last_attach_error: str = ""
        self.consecutive_valid_reads: int = 0

    # ================= PROCESS DETECTION & MANAGEMENT =================

    @staticmethod
    def is_autofps_running() -> Tuple[bool, Optional[int]]:
        """Détecte si l'application externe MSFS_AutoFPS est en cours d'exécution."""
        snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot == -1 or not snapshot:
            return False, None

        entry = PROCESSENTRY32()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
        found = False
        pid = None

        if kernel32.Process32First(snapshot, ctypes.byref(entry)):
            while True:
                name = entry.szExeFile.decode('utf-8', errors='ignore').lower()
                if 'msfs_autofps' in name or 'autofps.exe' in name or 'dynamiclod' in name:
                    found = True
                    pid = entry.th32ProcessID
                    break
                if not kernel32.Process32Next(snapshot, ctypes.byref(entry)):
                    break

        kernel32.CloseHandle(snapshot)
        return found, pid

    @staticmethod
    def kill_autofps_process() -> bool:
        """Termine proprement le processus externe MSFS_AutoFPS pour éviter tout conflit d'écriture."""
        running, pid = FlightMemoryEngine.is_autofps_running()
        if not running or not pid:
            return True

        try:
            # Tentative de fermeture douce via taskkill
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            time.sleep(0.5)
            # Vérification
            still_running, _ = FlightMemoryEngine.is_autofps_running()
            return not still_running
        except Exception as e:
            print(f"[SmartLOD] Erreur lors de la fermeture d'AutoFPS: {e}")
            return False

    @staticmethod
    def find_msfs_process() -> Tuple[bool, str, Optional[int]]:
        """Trouve le processus MSFS actif (2024 en priorité puis 2020)."""
        snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot == -1 or not snapshot:
            return False, "", None

        entry = PROCESSENTRY32()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
        found_proc = ""
        found_pid = None

        if kernel32.Process32First(snapshot, ctypes.byref(entry)):
            while True:
                name = entry.szExeFile.decode('utf-8', errors='ignore').lower()
                if name == "flightsimulator2024.exe":
                    found_proc = "FlightSimulator2024.exe"
                    found_pid = entry.th32ProcessID
                    break
                elif name == "flightsimulator.exe" and not found_proc:
                    found_proc = "FlightSimulator.exe"
                    found_pid = entry.th32ProcessID
                if not kernel32.Process32Next(snapshot, ctypes.byref(entry)):
                    break

        kernel32.CloseHandle(snapshot)
        return (found_pid is not None), found_proc, found_pid

    def get_module_base(self, pid: int, module_name: str) -> int:
        """Récupère l'adresse de base du module exécutable principal."""
        snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)
        if snapshot == -1 or not snapshot:
            return 0

        entry = MODULEENTRY32()
        entry.dwSize = ctypes.sizeof(MODULEENTRY32)
        base_addr = 0

        target = module_name.lower()
        if kernel32.Module32First(snapshot, ctypes.byref(entry)):
            while True:
                mod_name = entry.szModule.decode('utf-8', errors='ignore').lower()
                if mod_name == target:
                    base_addr = entry.modBaseAddr or 0
                    break
                if not kernel32.Module32Next(snapshot, ctypes.byref(entry)):
                    break

        kernel32.CloseHandle(snapshot)
        return int(base_addr) if base_addr else 0

    # ================= ATTACH & ATOM READ/WRITE =================

    def attach(self) -> bool:
        """S'attache au processus MSFS actif et valide la table des adresses mémoires."""
        if self.is_attached and self.process_handle:
            # Vérifier si le processus est toujours en vie
            exit_code = ctypes.wintypes.DWORD()
            if kernel32.GetExitCodeProcess(self.process_handle, ctypes.byref(exit_code)):
                if exit_code.value == 259: # STILL_ACTIVE
                    return True
            self.detach()

        found, exe_name, pid = self.find_msfs_process()
        if not found or not pid:
            self.last_attach_error = "Processus MSFS non trouvé (ni 2020 ni 2024)"
            return False

        self.pid = pid
        self.exe_name = exe_name
        self.is_2024 = (exe_name.lower() == "flightsimulator2024.exe")

        flags = PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION
        handle = kernel32.OpenProcess(flags, False, pid)
        if not handle:
            err = ctypes.get_last_error()
            self.last_attach_error = f"Échec OpenProcess (PID {pid}, Erreur Win32: {err})"
            return False

        self.process_handle = handle

        # Récupération de l'adresse de base du module
        self.module_base_address = self.get_module_base(pid, exe_name)
        if not self.module_base_address:
            self.last_attach_error = f"Impossible de localiser la base du module {exe_name}"
            self.detach()
            return False

        # Résolution des offsets selon la version
        if self.is_2024:
            # Vérifier si une valeur personnalisée existe dans le config AutoFPS local
            saved_offset = self._read_saved_autofps_offset_2024()
            self.offset_module_base = saved_offset or self.OFFSETS_2024['default_module_base']
            
            base_ptr = self.module_base_address + self.offset_module_base
            self.addr_tlod = base_ptr + self.OFFSETS_2024['tlod']
            self.addr_olod = base_ptr + self.OFFSETS_2024['olod']
            self.addr_cloud_q = base_ptr + self.OFFSETS_2024['cloud_q']
            self.addr_dyn_set = base_ptr + self.OFFSETS_2024['dyn_set']
            self.addr_vr_mode = base_ptr + self.OFFSETS_2024['vr_mode']
        else:
            self.offset_module_base = self.OFFSETS_2020['default_module_base']
            # MSFS 2020 utilise un pointeur indirectionnel
            ptr_val = self._read_int64(self.module_base_address + self.offset_module_base)
            if ptr_val and ptr_val > 0x10000:
                self.addr_tlod = ptr_val
                self.addr_olod = ptr_val + 0x10 # Offset typique 2020
            else:
                self.addr_tlod = 0
                self.addr_olod = 0

        # Test de validation de sécurité
        if self._run_safety_validation():
            self.is_attached = True
            self.safe_read_only = False
            self.last_attach_error = ""
            return True
        else:
            # Échec de validation : Passage forcé en mode lecture seule passif
            self.is_attached = True
            self.safe_read_only = True
            self.last_attach_error = "Offsets mémoire non validés (Mode Read-Only de sécurité activé)"
            return False

    def detach(self):
        """Ferme proprement le handle mémoire."""
        if self.process_handle:
            try:
                kernel32.CloseHandle(self.process_handle)
            except Exception:
                pass
        self.process_handle = None
        self.is_attached = False
        self.safe_read_only = True
        self.consecutive_valid_reads = 0

    def _read_saved_autofps_offset_2024(self) -> Optional[int]:
        """Tente de lire l'offset validé le plus récent dans la configuration locale d'AutoFPS si présente."""
        try:
            cfg_path = os.path.expandvars(r'%APPDATA%\MSFS_AutoFPS\MSFS2024_AutoFPS.config')
            if os.path.exists(cfg_path):
                import xml.etree.ElementTree as ET
                tree = ET.parse(cfg_path)
                for add in tree.findall('.//add'):
                    k = add.get('key', '')
                    v = add.get('value', '')
                    if k == 'offsetModuleBase' and v and v.startswith('0x'):
                        return int(v, 16)
        except Exception:
            pass
        return None

    def _run_safety_validation(self) -> bool:
        """
        Vérifie que la lecture du TLOD produit un flottant réaliste (entre 10 et 1000).
        Si la valeur lue est aberrante, l'écriture est totalement bloquée pour protéger MSFS.
        """
        if not self.addr_tlod:
            return False

        val = self.read_tlod()
        if val is not None and 10.0 <= val <= 1000.0:
            self.consecutive_valid_reads += 1
            return True
        return False

    # ================= LOW-LEVEL READ/WRITE HELPERS =================

    def _read_float(self, address: int) -> Optional[float]:
        if not self.process_handle or not address:
            return None
        buf = ctypes.c_float()
        bytes_read = ctypes.c_size_t()
        ok = kernel32.ReadProcessMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            ctypes.byref(buf),
            ctypes.sizeof(buf),
            ctypes.byref(bytes_read)
        )
        if ok and bytes_read.value == ctypes.sizeof(buf):
            return float(buf.value)
        return None

    def _write_float(self, address: int, value: float) -> bool:
        if not self.process_handle or not address or self.safe_read_only:
            return False
        buf = ctypes.c_float(value)
        bytes_written = ctypes.c_size_t()
        ok = kernel32.WriteProcessMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            ctypes.byref(buf),
            ctypes.sizeof(buf),
            ctypes.byref(bytes_written)
        )
        return bool(ok and bytes_written.value == ctypes.sizeof(buf))

    def _read_int32(self, address: int) -> Optional[int]:
        if not self.process_handle or not address:
            return None
        buf = ctypes.c_int32()
        bytes_read = ctypes.c_size_t()
        ok = kernel32.ReadProcessMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            ctypes.byref(buf),
            ctypes.sizeof(buf),
            ctypes.byref(bytes_read)
        )
        if ok and bytes_read.value == ctypes.sizeof(buf):
            return int(buf.value)
        return None

    def _write_int32(self, address: int, value: int) -> bool:
        if not self.process_handle or not address or self.safe_read_only:
            return False
        buf = ctypes.c_int32(value)
        bytes_written = ctypes.c_size_t()
        ok = kernel32.WriteProcessMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            ctypes.byref(buf),
            ctypes.sizeof(buf),
            ctypes.byref(bytes_written)
        )
        return bool(ok and bytes_written.value == ctypes.sizeof(buf))

    def _read_int64(self, address: int) -> Optional[int]:
        if not self.process_handle or not address:
            return None
        buf = ctypes.c_int64()
        bytes_read = ctypes.c_size_t()
        ok = kernel32.ReadProcessMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            ctypes.byref(buf),
            ctypes.sizeof(buf),
            ctypes.byref(bytes_read)
        )
        if ok and bytes_read.value == ctypes.sizeof(buf):
            return int(buf.value)
        return None

    # ================= PUBLIC HIGH-LEVEL API =================

    def read_tlod(self) -> Optional[float]:
        """Retourne la valeur actuelle de Terrain LOD (ex: 100.0, 150.0, 250.0)."""
        raw = self._read_float(self.addr_tlod)
        if raw is not None:
            # Facteur d'échelle 1.0f = 100
            return round(raw * 100.0, 1)
        return None

    def write_tlod(self, value: float) -> bool:
        """Ajuste le Terrain LOD (sécurisé entre 10 et 1000)."""
        if self.safe_read_only or not self.addr_tlod:
            return False
        val_clamped = max(10.0, min(float(value), 1000.0))
        # Écriture du flottant avec mise à l'échelle (ex: 150 -> 1.5f)
        return self._write_float(self.addr_tlod, val_clamped / 100.0)

    def read_olod(self) -> Optional[float]:
        """Retourne la valeur actuelle d'Object LOD (ex: 100.0, 50.0, 20.0)."""
        raw = self._read_float(self.addr_olod)
        if raw is not None:
            return round(raw * 100.0, 1)
        return None

    def write_olod(self, value: float) -> bool:
        """Ajuste l'Object LOD (sécurisé entre 10 et 500)."""
        if self.safe_read_only or not self.addr_olod:
            return False
        val_clamped = max(10.0, min(float(value), 500.0))
        return self._write_float(self.addr_olod, val_clamped / 100.0)

    def read_cloud_quality(self) -> Optional[int]:
        """Retourne la qualité des nuages (0=Low, 1=Medium, 2=High, 3=Ultra)."""
        return self._read_int32(self.addr_cloud_q)

    def write_cloud_quality(self, quality: int) -> bool:
        """Modifie la qualité des nuages (0=Low, 1=Medium, 2=High, 3=Ultra)."""
        if self.safe_read_only or not self.addr_cloud_q:
            return False
        q_clamped = max(0, min(int(quality), 3))
        return self._write_int32(self.addr_cloud_q, q_clamped)

    def is_vr_active(self) -> bool:
        """Indique si le mode VR est actif dans le simulateur."""
        if not self.addr_vr_mode:
            return False
        val = self._read_int32(self.addr_vr_mode)
        return bool(val and val == 1)

    def get_status(self) -> Dict[str, Any]:
        """Retourne un dictionnaire complet sur l'état du moteur mémoire."""
        is_autofps_up, autofps_pid = self.is_autofps_running()
        return {
            "is_attached": self.is_attached,
            "safe_read_only": self.safe_read_only,
            "pid": self.pid,
            "exe_name": self.exe_name,
            "is_2024": self.is_2024,
            "addr_tlod": hex(self.addr_tlod) if self.addr_tlod else None,
            "addr_olod": hex(self.addr_olod) if self.addr_olod else None,
            "current_tlod": self.read_tlod() if self.is_attached else None,
            "current_olod": self.read_olod() if self.is_attached else None,
            "cloud_quality": self.read_cloud_quality() if self.is_attached else None,
            "is_vr": self.is_vr_active() if self.is_attached else False,
            "autofps_conflict": is_autofps_up,
            "autofps_pid": autofps_pid,
            "last_error": self.last_attach_error
        }


# Instance globale singleton
_global_memory_engine: Optional[FlightMemoryEngine] = None

def get_memory_engine() -> FlightMemoryEngine:
    global _global_memory_engine
    if _global_memory_engine is None:
        _global_memory_engine = FlightMemoryEngine()
    return _global_memory_engine


if __name__ == "__main__":
    print("=== Test SceneryX Smart LOD Memory Engine ===")
    engine = FlightMemoryEngine()
    af_running, af_pid = engine.is_autofps_running()
    print(f"AutoFPS Running: {af_running} (PID: {af_pid})")
    
    msfs_found, proc, pid = engine.find_msfs_process()
    print(f"MSFS Found: {msfs_found} ({proc}, PID: {pid})")
    
    if msfs_found:
        ok = engine.attach()
        print(f"Attach result: {ok}")
        print("Status:", engine.get_status())
    else:
        print("MSFS non démarré (test nominal)")
