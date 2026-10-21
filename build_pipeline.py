#!/usr/bin/env python3
"""
SceneryX - Unified Production Build Pipeline
===========================================
Strictly isolates build artifacts into:
  - App Binaries:     D:\\SceneryX\\build\\SceneryX\\
  - Setup Executable: D:\\SceneryX\\build\\installer\\<ReleaseName>\\<ReleaseName>_Setup.exe
Cleans up all intermediate compilation caches and builds the Inno Setup installer.
Synchronizes release versions across UI (splash.html, index.html) and installer scripts.
"""

import os
import sys
import shutil
import hashlib
import subprocess
import winreg
import json
import re
import argparse
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(BASE_DIR, "build")
APP_DIST_DIR = os.path.join(BUILD_DIR, "SceneryX")
INSTALLER_BASE_DIR = os.path.join(BUILD_DIR, "installer")
TEMP_WORK_DIR = os.path.join(BUILD_DIR, "pyinstaller_temp")
ISS_SCRIPT_PATH = os.path.join(BASE_DIR, "installer", "SceneryX_Setup.iss")
ICON_PATH = os.path.join(BASE_DIR, "icon.ico")
VERSION_FILE = os.path.join(BASE_DIR, "version.json")


def load_or_update_version(increment=False, explicit_version=None):
    """
    Loads version configuration from version.json.
    If increment=True, increments patch version by 0.0.1.
    If explicit_version is provided, sets it (e.g. PRO_1.1.1 or LITE_1.1.1).
    Returns (version_tag, release_name).
    """
    default_cfg = {
        "app_name": "SceneryX",
        "stage": "PRO",
        "major": 1,
        "minor": 1,
        "patch": 1,
        "version": "PRO_1.1.1",
        "release_name": "SceneryX_PRO_1.1.1"
    }

    cfg = default_cfg
    if os.path.isfile(VERSION_FILE):
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            print(f"[WARN] Error reading {VERSION_FILE}: {e}")

    if explicit_version:
        clean_v = explicit_version.replace("SceneryX_", "").strip()
        cfg["version"] = clean_v
        cfg["release_name"] = f"SceneryX_{clean_v}"
        if clean_v.upper().startswith("LITE"):
            cfg["stage"] = "LITE"
        elif clean_v.upper().startswith("PRO"):
            cfg["stage"] = "PRO"
        # Parse major.minor.patch if pattern matches
        m = re.search(r"(\d+)\.(\d+)\.(\d+)", clean_v)
        if m:
            cfg["major"] = int(m.group(1))
            cfg["minor"] = int(m.group(2))
            cfg["patch"] = int(m.group(3))
    elif increment:
        cfg["patch"] = cfg.get("patch", 0) + 1
        stage = cfg.get("stage", "PRO")
        if stage not in ("PRO", "LITE"):
            stage = "PRO"
            cfg["stage"] = stage
        cfg["version"] = f"{stage}_{cfg.get('major', 1)}.{cfg.get('minor', 1)}.{cfg['patch']}"
        cfg["release_name"] = f"SceneryX_{cfg['version']}"

    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"[WARN] Failed to write {VERSION_FILE}: {e}")

    return cfg.get("version", "PRO_1.1.1"), cfg.get("release_name", "SceneryX_PRO_1.1.1")


def sync_ui_versions(version_tag):
    """
    Ensures scanner.py, web/app.js, web/splash.html, and web/index.html have the exact
    edition flag (IS_LITE) and version_tag (PRO_X.X.X or LITE_X.X.X) synchronized.
    """
    is_lite = ("LITE" in version_tag.upper())
    m = re.search(r"(\d+\.\d+\.\d+)", version_tag)
    semver = m.group(1) if m else "1.1.1"
    lite_ver = f"LITE_{semver}"
    pro_ver = f"PRO_{semver}"

    scanner_file = os.path.join(BASE_DIR, "scanner.py")
    app_js_file = os.path.join(BASE_DIR, "web", "app.js")
    splash_file = os.path.join(BASE_DIR, "web", "splash.html")
    index_file = os.path.join(BASE_DIR, "web", "index.html")

    # 0a. scanner.py IS_LITE and APP_VERSION
    if os.path.isfile(scanner_file):
        with open(scanner_file, "r", encoding="utf-8") as f:
            s_content = f.read()
        s_new = re.sub(
            r"^IS_LITE\s*=\s*(?:True|False)",
            f"IS_LITE = {'True' if is_lite else 'False'}",
            s_content,
            count=1,
            flags=re.MULTILINE
        )
        s_new = re.sub(
            r'^APP_VERSION\s*=\s*".*?"\s*if\s*IS_LITE\s*else\s*".*?"',
            f'APP_VERSION = "{lite_ver}" if IS_LITE else "{pro_ver}"',
            s_new,
            count=1,
            flags=re.MULTILINE
        )
        if s_new != s_content:
            with open(scanner_file, "w", encoding="utf-8") as f:
                f.write(s_new)
        print(f"  [OK] Synchronized scanner.py -> IS_LITE={is_lite}, APP_VERSION={version_tag}")

    # 0b. web/app.js window.IS_LITE
    if os.path.isfile(app_js_file):
        with open(app_js_file, "r", encoding="utf-8") as f:
            a_content = f.read()
        a_new = re.sub(
            r"window\.IS_LITE\s*=\s*(?:true|false);",
            f"window.IS_LITE = {'true' if is_lite else 'false'};",
            a_content,
            count=1
        )
        if a_new != a_content:
            with open(app_js_file, "w", encoding="utf-8") as f:
                f.write(a_new)
        print(f"  [OK] Synchronized web/app.js -> window.IS_LITE={'true' if is_lite else 'false'}")

    # 1. splash.html footer copyright & version
    if os.path.isfile(splash_file):
        with open(splash_file, "r", encoding="utf-8") as f:
            content = f.read()
        new_content = re.sub(
            r'<span class="copyright-text">.*?•\s*&copy;\s*2026 Sidestick Priority</span>',
            f'<span class="copyright-text">{version_tag} • &copy; 2026 Sidestick Priority</span>',
            content
        )
        if new_content != content:
            with open(splash_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"  [OK] Synchronized version in splash.html -> {version_tag}")

    # 2. index.html splash & top navbar header badge
    if os.path.isfile(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Splash footer in index.html
        content = re.sub(
            r'<span class="text-\[10px\] text-\[#64748B\] font-medium tracking-wide">.*?•\s*&copy;\s*2026 Sidestick Priority</span>',
            f'<span class="text-[10px] text-[#64748B] font-medium tracking-wide">{version_tag} • &copy; 2026 Sidestick Priority</span>',
            content
        )
        # Header version badge in index.html
        content = re.sub(
            r'<span class="typo-metadata text-\[11px\] font-mono font-medium text-\[#64748B\] leading-none mb-1"\s*title="[^"]*">[^<]*</span>',
            f'<span class="typo-metadata text-[11px] font-mono font-medium text-[#64748B] leading-none mb-1" title="SceneryX {version_tag}">{version_tag}</span>',
            content
        )
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [OK] Synchronized version in index.html -> {version_tag}")


def compute_sha256(filepath):
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def find_iscc_executable():
    """Locates the Inno Setup Command-Line Compiler (ISCC.exe)."""
    # 1. Check PATH
    which_iscc = shutil.which("ISCC.exe")
    if which_iscc and os.path.isfile(which_iscc):
        return which_iscc

    # 2. Known standard paths
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        os.path.join(local_appdata, r"Programs\Inno Setup 6\ISCC.exe"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe"
    ]
    for p in candidates:
        if p and os.path.isfile(p):
            return p

    # 3. Registry lookup
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1"),
    ]
    for hkey, subkey in reg_paths:
        try:
            with winreg.OpenKey(hkey, subkey) as k:
                val, _ = winreg.QueryValueEx(k, "InstallLocation")
                cand = os.path.join(val, "ISCC.exe")
                if os.path.isfile(cand):
                    return cand
        except Exception:
            continue

    return None


def kill_running_sceneryx_instances():
    """Safely terminates only SceneryX instances running from the local build directory."""
    try:
        ps_cmd = (
            f"Get-Process SceneryX -ErrorAction SilentlyContinue | "
            f"Where-Object {{ $_.Path -and $_.Path.StartsWith('{BUILD_DIR}', [System.StringComparison]::OrdinalIgnoreCase) }} | "
            f"Stop-Process -Force -ErrorAction SilentlyContinue"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        time.sleep(0.5)
    except Exception:
        pass


def clean_directory(dir_path):
    """Safely removes and recreates a directory."""
    if os.path.exists(dir_path):
        try:
            shutil.rmtree(dir_path)
        except Exception as e:
            print(f"[WARN] Failed to fully remove {dir_path}: {e}")
    os.makedirs(dir_path, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="SceneryX Unified Production Build Pipeline")
    parser.add_argument("--increment", action="store_true", help="Increment patch version by 0.0.1")
    parser.add_argument("--version", type=str, default=None, help="Explicit version tag (e.g. RC_v1.0.1)")
    parser.add_argument("--skip-pyinstaller", action="store_true", help="Skip PyInstaller step if binary is unchanged")
    args = parser.parse_args()

    version_tag, release_name = load_or_update_version(
        increment=args.increment,
        explicit_version=args.version
    )

    print("=" * 75)
    print(f"  SceneryX Production Build Pipeline: {release_name} ({version_tag})")
    print("=" * 75)

    # Terminate any running instance of SceneryX to release file locks
    kill_running_sceneryx_instances()

    # Synchronize UI version displays
    print("\n[Step 1/5] Synchronizing UI version tags...")
    sync_ui_versions(version_tag)

    # Clean intermediate output folders
    release_installer_dir = os.path.join(INSTALLER_BASE_DIR, release_name)
    print("\n[Step 2/5] Preparing clean build environments...")
    print(f"  -> App Output Directory:       {APP_DIST_DIR}")
    print(f"  -> Release Installer Dir:      {release_installer_dir}")
    print(f"  -> Intermediate Cache Dir:     {TEMP_WORK_DIR}")

    clean_directory(TEMP_WORK_DIR)
    os.makedirs(release_installer_dir, exist_ok=True)

    # 3. PyInstaller Packaging
    app_exe = os.path.join(APP_DIST_DIR, "SceneryX.exe")
    if not args.skip_pyinstaller or not os.path.isfile(app_exe):
        clean_directory(APP_DIST_DIR)
        print("\n[Step 3/5] Compiling SceneryX binary via PyInstaller...")
        pyinstaller_cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--windowed",
            "--name=SceneryX",
            f"--icon={ICON_PATH}",
            f"--distpath={APP_DIST_DIR}",
            f"--workpath={TEMP_WORK_DIR}",
            f"--specpath={TEMP_WORK_DIR}",
            f"--add-data={os.path.join(BASE_DIR, 'airports.json')};.",
            f"--add-data={os.path.join(BASE_DIR, 'airport_airlines.json')};.",
            f"--add-data={os.path.join(BASE_DIR, 'airport_routes.json')};.",
            f"--add-data={os.path.join(BASE_DIR, 'airport_runways.json')};.",
            f"--add-data={os.path.join(BASE_DIR, 'installed_airports.json')};.",
            f"--add-data={ICON_PATH};.",
            f"--add-data={os.path.join(BASE_DIR, 'web')};web",
            f"--add-data={os.path.join(BASE_DIR, 'custom_profiles')};custom_profiles",
            f"--add-data={os.path.join(BASE_DIR, 'legal')};legal",
            f"--add-data={os.path.join(BASE_DIR, 'sceneryx-ingame-panel')};sceneryx-ingame-panel",
            "--collect-all=SimConnect",
            "--collect-all=pystray",
            "--collect-all=PIL",
            os.path.join(BASE_DIR, "main.py")
        ]

        print(f"  Running command: {' '.join(pyinstaller_cmd[:6])} ...")
        res = subprocess.run(pyinstaller_cmd, cwd=BASE_DIR)
        if res.returncode != 0:
            print(f"\n[FATAL] PyInstaller failed with exit code {res.returncode}!")
            sys.exit(res.returncode)

        if not os.path.isfile(app_exe):
            print(f"\n[FATAL] Target binary not found at: {app_exe}")
            sys.exit(1)

        app_size_mb = os.path.getsize(app_exe) / (1024 * 1024)
        print(f"  [OK] Successfully built {app_exe} ({app_size_mb:.2f} MB)")
    else:
        app_size_mb = os.path.getsize(app_exe) / (1024 * 1024)
        print(f"\n[Step 3/5] Skipping PyInstaller compilation (using existing binary: {app_size_mb:.2f} MB)")

    # 4. Clean Intermediate Cache
    print("\n[Step 4/5] Purging intermediate compilation caches...")
    if os.path.exists(TEMP_WORK_DIR):
        shutil.rmtree(TEMP_WORK_DIR, ignore_errors=True)
        print(f"  [OK] Removed cache directory: {TEMP_WORK_DIR}")

    # 5. Inno Setup Compilation
    print("\n[Step 5/5] Compiling Windows Installer (Inno Setup)...")
    iscc_exe = find_iscc_executable()
    if not iscc_exe:
        print("[FATAL] Inno Setup Compiler (ISCC.exe) could not be located!")
        print("Please verify Inno Setup 6 installation or ensure ISCC.exe is in PATH.")
        sys.exit(2)

    print(f"  Found ISCC compiler:   {iscc_exe}")
    print(f"  Target Release Folder: {release_installer_dir}")
    print(f"  Installer Package:     {release_name}_Setup.exe")

    installer_target_name = f"{release_name}_Setup"

    iscc_cmd = [
        iscc_exe,
        f"/O{release_installer_dir}",
        f"/F{installer_target_name}",
        f"/DSourceDir={APP_DIST_DIR}",
        f"/DOutputDir={release_installer_dir}",
        f"/DOutputBaseFilename={installer_target_name}",
        f"/DMyAppVersion={version_tag}",
        f"/DReleaseName={release_name}",
        ISS_SCRIPT_PATH
    ]

    res_iscc = subprocess.run(iscc_cmd, cwd=BASE_DIR)
    if res_iscc.returncode != 0:
        print(f"\n[FATAL] Inno Setup compilation failed with exit code {res_iscc.returncode}!")
        sys.exit(res_iscc.returncode)

    installer_exe = os.path.join(release_installer_dir, f"{installer_target_name}.exe")
    if not os.path.isfile(installer_exe):
        # Look for any .exe produced in that folder
        candidates = [os.path.join(release_installer_dir, f) for f in os.listdir(release_installer_dir) if f.endswith(".exe")]
        if candidates:
            installer_exe = candidates[0]
        else:
            print(f"\n[FATAL] Installer executable not found in: {release_installer_dir}")
            sys.exit(3)

    installer_size_mb = os.path.getsize(installer_exe) / (1024 * 1024)
    installer_sha256 = compute_sha256(installer_exe)

    print("\n" + "=" * 75)
    print("                    BUILD PIPELINE COMPLETE!                    ")
    print("=" * 75)
    print(f"Release Name:      {release_name}")
    print(f"Version Tag:       {version_tag}")
    print(f"App Binary:        {app_exe} ({app_size_mb:.2f} MB)")
    print(f"Installer Folder:  {release_installer_dir}")
    print(f"Installer Exec:    {installer_exe} ({installer_size_mb:.2f} MB)")
    print(f"SHA-256 Checksum:  {installer_sha256}")
    print("=" * 75)


if __name__ == "__main__":
    main()
