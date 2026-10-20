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
        'default_module_base': 0x0A80B024,
        'sim_module': 'FlightSimulator2024.exe',
        'offset_vr': 0x148,  # Décalage VR vs 2D Desktop (+328 octets)
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
        # Offsets VR directs
        'tlod_vr': 0x4A0,     # 0x358 + 0x148
        'olod_vr': 0x4B4,     # 0x36C + 0x148
        'cloud_q_vr': 0x4EC,  # 0x3A4 + 0x148
    }

    OFFSETS_2020 = {
        'default_module_base': 0x004B2368,
        'sim_module': 'FlightSimulator.exe',
        'pointer_main': 0x03D0,
        'pointer_tlod': 0x0C,
        'pointer_tlod_vr': 0x0114,
        'pointer_olod': 0x0C,
        'pointer_cloud_q': 0x44,
        'pointer_cloud_q_vr': 0x0108,
        'pointer_vr_mode': 0x1C
    }

    def __init__(self):
        self.process_handle: Optional[int] = None
        self.pid: Optional[int] = None
        self.exe_name: str = ""
        self.is_2024: bool = False
        self.module_base_address: int = 0
        self.offset_module_base: int = 0
        
        # Adresses directes calculées (2D Desktop)
        self.addr_tlod: int = 0
        self.addr_olod: int = 0
        self.addr_cloud_q: int = 0
        self.addr_dyn_set: int = 0
        self.addr_vr_mode: int = 0
        
        # Adresses directes calculées (VR Headset)
        self.addr_tlod_vr: int = 0
        self.addr_olod_vr: int = 0
        self.addr_cloud_q_vr: int = 0
        self.addr_dyn_set_vr: int = 0
        
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
    def is_ofxr_running() -> Tuple[bool, Optional[int]]:
        """Détecte si l'application OFXR Bridge (OFXRBridgeTray.exe) est en cours d'exécution."""
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
                if 'ofxrbridgetray' in name or 'ofxrbridge' in name or 'ofxr.exe' in name:
                    found = True
                    pid = entry.th32ProcessID
                    break
                if not kernel32.Process32Next(snapshot, ctypes.byref(entry)):
                    break

        kernel32.CloseHandle(snapshot)
        return found, pid

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
                    if not self.safe_read_only and self._run_safety_validation():
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
            candidates = []
            cached_off = self._read_cached_sceneryx_offset_2024()
            if cached_off:
                candidates.append(cached_off)
            if self.OFFSETS_2024['default_module_base'] not in candidates:
                candidates.append(self.OFFSETS_2024['default_module_base'])
            saved_offset = self._read_saved_autofps_offset_2024()
            if saved_offset and saved_offset not in candidates:
                candidates.append(saved_offset)

            matched_off = None
            for cand in candidates:
                self._apply_2024_offset_candidate(cand)
                if self._run_safety_validation():
                    matched_off = cand
                    break

            if matched_off is None:
                scanned_off = self._scan_msfs2024_module_offset()
                if scanned_off:
                    self._apply_2024_offset_candidate(scanned_off)
                    if self._run_safety_validation():
                        matched_off = scanned_off
                        self._save_cached_sceneryx_offset_2024(scanned_off)
        else:
            self.offset_module_base = self.OFFSETS_2020['default_module_base']
            # MSFS 2020 utilise un pointeur indirectionnel
            ptr_val = self._read_int64(self.module_base_address + self.offset_module_base)
            if ptr_val and ptr_val > 0x10000:
                self.addr_tlod = self._read_int64(ptr_val + self.OFFSETS_2020['pointer_tlod']) or 0
                self.addr_tlod_vr = self._read_int64(ptr_val + self.OFFSETS_2020['pointer_tlod_vr']) or 0
                if self.addr_tlod:
                    self.addr_olod = self.addr_tlod + self.OFFSETS_2020['pointer_olod']
                    self.addr_cloud_q = self.addr_tlod + self.OFFSETS_2020['pointer_cloud_q']
                    self.addr_vr_mode = self.addr_tlod + self.OFFSETS_2020['pointer_vr_mode']
                if self.addr_tlod_vr:
                    self.addr_olod_vr = self.addr_tlod_vr + self.OFFSETS_2020['pointer_olod']
                    self.addr_cloud_q_vr = self.addr_tlod_vr + self.OFFSETS_2020['pointer_cloud_q_vr']
            else:
                self.addr_tlod = 0
                self.addr_olod = 0
                self.addr_tlod_vr = 0
                self.addr_olod_vr = 0
                self.addr_cloud_q = 0
                self.addr_cloud_q_vr = 0
                self.addr_vr_mode = 0

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
        self.addr_tlod = 0
        self.addr_olod = 0
        self.addr_cloud_q = 0
        self.addr_dyn_set = 0
        self.addr_vr_mode = 0
        self.addr_tlod_vr = 0
        self.addr_olod_vr = 0
        self.addr_cloud_q_vr = 0
        self.addr_dyn_set_vr = 0

    def _apply_2024_offset_candidate(self, offset_val: int):
        self.offset_module_base = int(offset_val)
        base_ptr = self.module_base_address + self.offset_module_base
        self.addr_tlod = base_ptr + self.OFFSETS_2024['tlod']
        self.addr_olod = base_ptr + self.OFFSETS_2024['olod']
        self.addr_cloud_q = base_ptr + self.OFFSETS_2024['cloud_q']
        self.addr_dyn_set = base_ptr + self.OFFSETS_2024['dyn_set']
        self.addr_vr_mode = base_ptr + self.OFFSETS_2024['vr_mode']
        self.addr_dyn_set_vr = base_ptr + self.OFFSETS_2024['dyn_set_vr']
        offset_vr = self.OFFSETS_2024.get('offset_vr', 0x148)
        self.addr_tlod_vr = self.addr_tlod + offset_vr
        self.addr_olod_vr = self.addr_olod + offset_vr
        self.addr_cloud_q_vr = self.addr_cloud_q + offset_vr

    def _read_cached_sceneryx_offset_2024(self) -> Optional[int]:
        try:
            import json
            cache_file = os.path.expandvars(r'%APPDATA%\SceneryX\msfs2024_offset_cache.json')
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                val = data.get('offset_module_base')
                if isinstance(val, int) and val > 0:
                    return val
                if isinstance(val, str) and val.startswith('0x'):
                    return int(val, 16)
        except Exception:
            pass
        return None

    def _save_cached_sceneryx_offset_2024(self, offset_val: int):
        try:
            import json
            cache_dir = os.path.expandvars(r'%APPDATA%\SceneryX')
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, 'msfs2024_offset_cache.json')
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({'offset_module_base': hex(offset_val)}, f, indent=2)
        except Exception:
            pass

    def _scan_msfs2024_module_offset(self) -> Optional[int]:
        """Scans FlightSimulator2024.exe .data memory for the unique 2D + VR graphics settings structure."""
        if not self.process_handle or not self.pid or not self.module_base_address:
            return None
        try:
            import struct
            snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, self.pid)
            if snapshot == -1 or not snapshot:
                return None
            entry = MODULEENTRY32()
            entry.dwSize = ctypes.sizeof(MODULEENTRY32)
            mod_size = 0
            target = self.exe_name.lower()
            if kernel32.Module32First(snapshot, ctypes.byref(entry)):
                while True:
                    if entry.szModule.decode('utf-8', errors='ignore').lower() == target:
                        mod_size = int(entry.modBaseSize or 0)
                        break
                    if not kernel32.Module32Next(snapshot, ctypes.byref(entry)):
                        break
            kernel32.CloseHandle(snapshot)
            if mod_size <= 0:
                return None

            # Focus scan on the .data section range (typically 0x07000000 .. mod_size) first
            start_off = min(0x07000000, max(0, mod_size - 0x08000000))
            chunk_size = 4 * 1024 * 1024
            buf = ctypes.create_string_buffer(chunk_size)
            bytes_read = ctypes.c_size_t()
            pat = struct.pack('<ffff', 0.1, 0.1, 0.1, 0.1)
            valid_shd = {512, 768, 1024, 1536, 2048, 3072, 4096, 6144, 8192}

            for offset in range(start_off, mod_size, chunk_size - 0x600):
                addr = self.module_base_address + offset
                read_len = min(chunk_size, mod_size - offset)
                if read_len < 0x600:
                    break
                ok = kernel32.ReadProcessMemory(self.process_handle, ctypes.c_void_p(addr), buf, read_len, ctypes.byref(bytes_read))
                if not ok or bytes_read.value < 0x600:
                    continue
                raw = buf.raw[:bytes_read.value]
                pos = 0
                while True:
                    idx = raw.find(pat, pos)
                    if idx == -1:
                        break
                    pos = idx + 4
                    tlod_idx = idx - 0x20
                    if tlod_idx < 0x40 or tlod_idx + 0x290 > len(raw):
                        continue
                    slice_cnt, shd_size = struct.unpack_from('<ii', raw, idx - 8)
                    if slice_cnt != 4 or shd_size not in valid_shd:
                        continue
                    # Check that VR block at +0x148 also has MaxSliceCount == 4 and valid shadow map size
                    vr_slice_cnt, vr_shd_size = struct.unpack_from('<ii', raw, idx - 8 + 0x148)
                    if vr_slice_cnt != 4 or vr_shd_size not in valid_shd:
                        continue
                    tlod_f, pom1, pom2 = struct.unpack_from('<fff', raw, tlod_idx)
                    prec_en, prec_q, olod_f = struct.unpack_from('<iif', raw, tlod_idx + 12)
                    cld_q, = struct.unpack_from('<i', raw, tlod_idx + 0x4C)
                    aniso, tex_q = struct.unpack_from('<ii', raw, tlod_idx - 0x1C)
                    if (0.1 <= tlod_f <= 10.0 and 0.1 <= olod_f <= 10.0 and
                        0 <= prec_q <= 3 and 0 <= cld_q <= 3 and
                        aniso in (1, 2, 4, 8, 16) and 0 <= tex_q <= 3 and
                        pom1 in (10.0, 15.0, 20.0, 25.0)):
                        rel_tlod = (offset + tlod_idx)
                        found_base = rel_tlod - self.OFFSETS_2024['tlod']
                        print(f"[MemoryEngine] Auto-discovered MSFS 2024 offset_module_base: {hex(found_base)}")
                        return found_base
        except Exception as e:
            print(f"[MemoryEngine] Scan warning: {e}")
        return None

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
        Vérifie que la lecture du TLOD/OLOD et des marqueurs adjacents produit des valeurs réalistes.
        Si la valeur lue est aberrante, l'écriture est totalement bloquée pour protéger MSFS.
        Valide à la fois les adresses 2D Desktop et VR Headset.
        """
        if not self.addr_tlod and not self.addr_tlod_vr:
            return False

        pc_ok = False
        if self.addr_tlod:
            raw_pc = self._read_float(self.addr_tlod)
            raw_olod = self._read_float(self.addr_olod) if self.addr_olod else None
            raw_cld = self._read_int32(self.addr_cloud_q) if self.addr_cloud_q else None
            if (raw_pc is not None and 0.1 <= raw_pc <= 10.0 and
                raw_olod is not None and 0.1 <= raw_olod <= 10.0 and
                raw_cld is not None and 0 <= raw_cld <= 3):
                if self.is_2024:
                    shd_slices = self._read_int32(self.addr_tlod + 0x18)
                    pc_ok = (shd_slices == 4)
                else:
                    pc_ok = True

        vr_ok = False
        if self.addr_tlod_vr:
            raw_vr = self._read_float(self.addr_tlod_vr)
            raw_olod_vr = self._read_float(self.addr_olod_vr) if self.addr_olod_vr else None
            if (raw_vr is not None and 0.1 <= raw_vr <= 10.0 and
                raw_olod_vr is not None and 0.1 <= raw_olod_vr <= 10.0):
                vr_ok = True
            else:
                # Si l'adresse VR n'est pas cohérente, invalidation préventive des adresses VR
                self.addr_tlod_vr = 0
                self.addr_olod_vr = 0
                self.addr_cloud_q_vr = 0

        if pc_ok or vr_ok:
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
        """Retourne la valeur actuelle de Terrain LOD (ex: 100.0, 150.0, 250.0).
        En mode VR actif, lit préférentiellement l'adresse VR."""
        if not self.is_attached or self.safe_read_only:
            return None
        addr = self.addr_tlod_vr if (self.is_vr_active() and self.addr_tlod_vr) else self.addr_tlod
        if not addr:
            addr = self.addr_tlod or self.addr_tlod_vr
        raw = self._read_float(addr)
        if raw is not None and 0.1 <= raw <= 10.0:
            # Facteur d'échelle 1.0f = 100
            return round(raw * 100.0, 1)
        return None

    def write_tlod(self, value: float) -> bool:
        """Ajuste le Terrain LOD (sécurisé entre 10 et 1000) sur 2D et VR simultanément (Dual-Write)."""
        if self.safe_read_only or (not self.addr_tlod and not self.addr_tlod_vr):
            return False
        val_clamped = max(10.0, min(float(value), 1000.0))
        float_val = val_clamped / 100.0
        ok_pc = False
        ok_vr = False
        if self.addr_tlod:
            ok_pc = self._write_float(self.addr_tlod, float_val)
        if self.addr_tlod_vr:
            ok_vr = self._write_float(self.addr_tlod_vr, float_val)
        return ok_pc or ok_vr

    def read_olod(self) -> Optional[float]:
        """Retourne la valeur actuelle d'Object LOD (ex: 100.0, 50.0, 20.0).
        En mode VR actif, lit préférentiellement l'adresse VR."""
        if not self.is_attached or self.safe_read_only:
            return None
        addr = self.addr_olod_vr if (self.is_vr_active() and self.addr_olod_vr) else self.addr_olod
        if not addr:
            addr = self.addr_olod or self.addr_olod_vr
        raw = self._read_float(addr)
        if raw is not None and 0.1 <= raw <= 10.0:
            return round(raw * 100.0, 1)
        return None

    def write_olod(self, value: float) -> bool:
        """Ajuste l'Object LOD (sécurisé entre 10 et 500) sur 2D et VR simultanément (Dual-Write)."""
        if self.safe_read_only or (not self.addr_olod and not self.addr_olod_vr):
            return False
        val_clamped = max(10.0, min(float(value), 500.0))
        float_val = val_clamped / 100.0
        ok_pc = False
        ok_vr = False
        if self.addr_olod:
            ok_pc = self._write_float(self.addr_olod, float_val)
        if self.addr_olod_vr:
            ok_vr = self._write_float(self.addr_olod_vr, float_val)
        return ok_pc or ok_vr

    def read_cloud_quality(self) -> Optional[int]:
        """Retourne la qualité des nuages (0=Low, 1=Medium, 2=High, 3=Ultra)."""
        if not self.is_attached or self.safe_read_only:
            return None
        addr = self.addr_cloud_q_vr if (self.is_vr_active() and self.addr_cloud_q_vr) else self.addr_cloud_q
        if not addr:
            addr = self.addr_cloud_q or self.addr_cloud_q_vr
        val = self._read_int32(addr)
        if val is not None and 0 <= val <= 3:
            return int(val)
        return None

    def write_cloud_quality(self, quality: int) -> bool:
        """Modifie la qualité des nuages (0=Low, 1=Medium, 2=High, 3=Ultra) sur 2D et VR simultanément."""
        if self.safe_read_only or (not self.addr_cloud_q and not self.addr_cloud_q_vr):
            return False
        q_clamped = max(0, min(int(quality), 3))
        ok_pc = False
        ok_vr = False
        if self.addr_cloud_q:
            cur_pc = self._read_int32(self.addr_cloud_q)
            if cur_pc is not None and 0 <= cur_pc <= 3:
                ok_pc = self._write_int32(self.addr_cloud_q, q_clamped)
        if self.addr_cloud_q_vr:
            cur_vr = self._read_int32(self.addr_cloud_q_vr)
            if cur_vr is not None and 0 <= cur_vr <= 3:
                ok_vr = self._write_int32(self.addr_cloud_q_vr, q_clamped)
        return ok_pc or ok_vr

    def is_vr_active(self) -> bool:
        """Indique si le mode VR est actif dans le simulateur."""
        if not self.is_attached or self.safe_read_only or not self.addr_vr_mode:
            return False
        val = self._read_int32(self.addr_vr_mode)
        return bool(val and val == 1)

    def _get_live_struct_base(self, for_vr: bool = False) -> int:
        if for_vr:
            return self.addr_tlod_vr if self.addr_tlod_vr else 0
        return self.addr_tlod if self.addr_tlod else 0

    def read_live_graphics(self) -> Dict[str, Any]:
        """
        Lit en mémoire MSFS les paramètres graphiques modifiables à chaud :
        clouds, precaching, terrain_shadows, buildings, trees, plants, grass.
        Retourne uniquement les clés dont la valeur lue est valide.
        """
        out: Dict[str, Any] = {}
        if not self.is_attached or self.safe_read_only:
            return out

        cq = self.read_cloud_quality()
        if cq is not None and 0 <= cq <= 3:
            out["clouds"] = int(cq)

        if not self.is_2024:
            return out

        is_vr = self.is_vr_active()
        base = self._get_live_struct_base(for_vr=is_vr) or self._get_live_struct_base(for_vr=False)
        if not base:
            return out

        # Offsets relatifs par rapport à addr_tlod (0x358)
        prec = self._read_int32(base + 0x10)  # 0x368
        if prec is not None and 0 <= prec <= 3:
            out["precaching"] = int(prec)

        ts_en_raw = self._read_int32(base + 0x34)   # 0x38C (uint8 bool in lower byte)
        ts_en = (ts_en_raw & 0xFF) if ts_en_raw is not None else None
        ts_sz = self._read_int32(base + 0x38)       # 0x390
        if ts_en == 0:
            out["terrain_shadows"] = 0
        elif ts_sz in (128, 256, 512, 1024, 2048):
            out["terrain_shadows"] = int(ts_sz)

        bldg = self._read_int32(base + 0xBC)  # 0x414
        if bldg is not None and 0 <= bldg <= 3:
            out["buildings"] = int(bldg)

        trees = self._read_int32(base + 0xC0)  # 0x418
        if trees is not None and 0 <= trees <= 3:
            out["trees"] = int(trees)

        plants = self._read_int32(base + 0xC4)  # 0x41C
        if plants is not None and 0 <= plants <= 3:
            out["plants"] = int(plants)

        grass = self._read_int32(base + 0xCC)  # 0x424
        if grass is not None and 0 <= grass <= 3:
            out["grass"] = int(grass)

        return out

    def write_live_graphics(self, settings: Dict[str, Any]) -> Dict[str, bool]:
        """
        Écrit à chaud en RAM MSFS (Dual-Write 2D + VR) les paramètres graphiques supportés.
        Vérifie systématiquement la cohérence de la valeur existante avant écriture.
        """
        results: Dict[str, bool] = {}
        if not self.is_attached or self.safe_read_only or not isinstance(settings, dict):
            return results

        if "clouds" in settings and settings["clouds"] is not None:
            try:
                results["clouds"] = self.write_cloud_quality(int(settings["clouds"]))
            except Exception:
                results["clouds"] = False

        if not self.is_2024:
            return results

        bases = [b for b in (self.addr_tlod, self.addr_tlod_vr) if b]
        if not bases:
            return results

        def _safe_write_enum(delta: int, new_val: int, min_v: int, max_v: int) -> bool:
            clamped = max(min_v, min(max_v, int(new_val)))
            any_ok = False
            for b in bases:
                cur = self._read_int32(b + delta)
                if cur is not None and min_v <= cur <= max_v:
                    if self._write_int32(b + delta, clamped):
                        any_ok = True
            return any_ok

        if "precaching" in settings and settings["precaching"] is not None:
            try:
                results["precaching"] = _safe_write_enum(0x10, int(settings["precaching"]), 0, 3)
            except Exception:
                results["precaching"] = False

        if "terrain_shadows" in settings and settings["terrain_shadows"] is not None:
            try:
                ts_val = int(settings["terrain_shadows"])
                any_ts_ok = False
                for b in bases:
                    cur_en_raw = self._read_int32(b + 0x34)
                    cur_en = (cur_en_raw & 0xFF) if cur_en_raw is not None else None
                    cur_sz = self._read_int32(b + 0x38)
                    if cur_en in (0, 1) and (cur_sz in (0, 128, 256, 512, 1024, 2048)):
                        if ts_val <= 0:
                            new_en_raw = (cur_en_raw & ~0xFF)
                            ok1 = self._write_int32(b + 0x34, new_en_raw)
                            any_ts_ok = any_ts_ok or ok1
                        elif ts_val in (128, 256, 512, 1024, 2048):
                            new_en_raw = (cur_en_raw & ~0xFF) | 1
                            ok1 = self._write_int32(b + 0x34, new_en_raw)
                            ok2 = self._write_int32(b + 0x38, ts_val)
                            any_ts_ok = any_ts_ok or (ok1 and ok2)
                results["terrain_shadows"] = any_ts_ok
            except Exception:
                results["terrain_shadows"] = False

        if "buildings" in settings and settings["buildings"] is not None:
            try:
                results["buildings"] = _safe_write_enum(0xBC, int(settings["buildings"]), 0, 3)
            except Exception:
                results["buildings"] = False

        if "trees" in settings and settings["trees"] is not None:
            try:
                results["trees"] = _safe_write_enum(0xC0, int(settings["trees"]), 0, 3)
            except Exception:
                results["trees"] = False

        if "plants" in settings and settings["plants"] is not None:
            try:
                results["plants"] = _safe_write_enum(0xC4, int(settings["plants"]), 0, 3)
            except Exception:
                results["plants"] = False

        if "grass" in settings and settings["grass"] is not None:
            try:
                results["grass"] = _safe_write_enum(0xCC, int(settings["grass"]), 0, 3)
            except Exception:
                results["grass"] = False

        return results

    def get_status(self) -> Dict[str, Any]:
        """Retourne un dictionnaire complet sur l'état du moteur mémoire."""
        is_autofps_up, autofps_pid = self.is_autofps_running()
        is_ofxr_up, ofxr_pid = self.is_ofxr_running()
        is_vr = self.is_vr_active() if self.is_attached else False
        return {
            "is_attached": self.is_attached,
            "safe_read_only": self.safe_read_only,
            "pid": self.pid,
            "exe_name": self.exe_name,
            "is_2024": self.is_2024,
            "addr_tlod": hex(self.addr_tlod) if self.addr_tlod else None,
            "addr_olod": hex(self.addr_olod) if self.addr_olod else None,
            "addr_tlod_vr": hex(self.addr_tlod_vr) if self.addr_tlod_vr else None,
            "addr_olod_vr": hex(self.addr_olod_vr) if self.addr_olod_vr else None,
            "addr_cloud_q_vr": hex(self.addr_cloud_q_vr) if self.addr_cloud_q_vr else None,
            "current_tlod": self.read_tlod() if self.is_attached else None,
            "current_olod": self.read_olod() if self.is_attached else None,
            "cloud_quality": self.read_cloud_quality() if self.is_attached else None,
            "is_vr": is_vr,
            "autofps_conflict": is_autofps_up,
            "autofps_pid": autofps_pid,
            "ofxr_running": is_ofxr_up,
            "ofxr_pid": ofxr_pid,
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
