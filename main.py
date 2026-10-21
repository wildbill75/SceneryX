import os
import sys
import time
import json
import re
import threading
import urllib.request
import webbrowser
import webview
from datetime import datetime
import flight_rig_optimizer
import flight_perf_tracker
import flight_bug_reporter
from scanner import run_scan, get_settings, save_settings, load_ratings, save_rating, save_custom_price, save_custom_category, load_custom_prices, get_estimated_price, get_default_gsx_path, load_airport_database, SPECIAL_BUNDLE_MAP, OUTPUT_JSON_PATH, compute_scan_delta, build_library_snapshot, SNAPSHOT_JSON_PATH, get_resource_file_path, audit_all_gsx_profiles, audit_single_airport_gsx, extract_icao_from_gsx_filename, find_bundled_gsx, USER_DATA_DIR, IS_LITE, APP_VERSION

try:
    import webview.platforms.winforms as wf
    if hasattr(wf, 'OpenFolderDialog'):
        wf.OpenFolderDialog.foldersFilter = 'All Files (*.*)|*.*'
except Exception:
    pass

ISOLATION_SNAPSHOT_FILE = os.path.join(USER_DATA_DIR, "flight_isolation_snapshot.json")

def save_isolation_snapshot(snapshot_data):
    """Atomically persists the flight mode isolation state for guaranteed 1-click lossless rollback."""
    try:
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        with open(ISOLATION_SNAPSHOT_FILE, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving isolation snapshot: {e}")

def load_isolation_snapshot():
    """Loads the active flight isolation snapshot if present."""
    try:
        if os.path.exists(ISOLATION_SNAPSHOT_FILE):
            with open(ISOLATION_SNAPSHOT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading isolation snapshot: {e}")
    return None

def clear_isolation_snapshot():
    """Clears the active flight isolation snapshot after successful restore."""
    try:
        if os.path.exists(ISOLATION_SNAPSHOT_FILE):
            os.remove(ISOLATION_SNAPSHOT_FILE)
    except Exception as e:
        print(f"Error removing isolation snapshot: {e}")

# Known secondary / duplicate packages that must stay disabled to prevent conflict resurrection
KNOWN_CONFLICT_SECONDARY_PACKAGES = {
    'EDDF': ['virtualfra-eddf'],
    'LSZH': ['fs24-microsoft-airport-lszh-zurich', 'fs24-asobo-airport-lszh'],
    'EGKK': ['gatwick'],
    'CYVR': ['joelster-airport-cyvr-vancouver'],
    'LECO': ['fs24-microsoft-airport-leco-a-coruna'],
    'LPMA': ['fs24-asobo-airport-lpma-madeira'],
    'LFKB': ['fs20-orbx-airport-lfkb-bastia'],
    'LHBP': ['fs24-microsoft-scenery-budapest-rbr2']
}

def auto_resolve_known_conflicts():
    """
    Guarantees that secondary conflicting packages remain disabled so conflicts never resurrect.
    Only keeps secondary packages disabled when a primary scenery is present.
    """
    try:
        comm_dirs = []
        settings = get_settings()
        for cfg in settings.get("scan_paths", []):
            dp = cfg.get('path', '')
            if dp and os.path.exists(dp):
                comm_dirs.append(dp)
                onestore = os.path.join(dp, 'OneStore')
                if os.path.exists(onestore):
                    comm_dirs.append(onestore)

        # 1. Physical folders on disk (Community)
        for cd in comm_dirs:
            for icao, sec_list in KNOWN_CONFLICT_SECONDARY_PACKAGES.items():
                for sec_name in sec_list:
                    clean_sec = sec_name[:-9] if sec_name.endswith('.disabled') else sec_name
                    sec_path = os.path.join(cd, clean_sec)
                    dis_path = sec_path + '.disabled'
                    if (os.path.exists(sec_path) or os.path.islink(sec_path)) and not os.path.exists(dis_path):
                        try:
                            safe_rename_path(sec_path, dis_path)
                            print(f"[CONFLICT SAFEGUARD] Kept secondary package disabled on disk: {clean_sec}")
                        except Exception as e:
                            print(f"Error disabling secondary package {clean_sec}: {e}")

        # 2. MSFS Content.xml
        all_sec_lower = {k.lower() for sec_list in KNOWN_CONFLICT_SECONDARY_PACKAGES.values() for k in sec_list}
        for xml_path in get_content_xml_paths():
            if not os.path.exists(xml_path):
                continue
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(xml_path)
                root = tree.getroot()
                changed = False
                for p in root.findall('Package'):
                    name = p.get('name', '')
                    clean_name = (name[:-9] if name.endswith('.disabled') else name).lower()
                    clean_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', clean_name)
                    if clean_name in all_sec_lower or clean_norm in all_sec_lower:
                        if p.get('active') != 'UserDisabled':
                            p.set('active', 'UserDisabled')
                            changed = True
                            print(f"[CONFLICT SAFEGUARD] Set secondary package to UserDisabled in Content.xml: {name}")
                if changed:
                    tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            except Exception as e:
                print(f"Error updating Content.xml in auto_resolve_known_conflicts: {e}")
    except Exception as ex:
        print(f"Error in auto_resolve_known_conflicts: {ex}")

PROTECTED_SYSTEM_KEYWORDS = [
    'modellib', 'commonlibrary', 'projectairports', 'genericairports',
    'travelbook', 'worlddiscovery', 'bush-trip', 'bushtrip', 'activities',
    'instruments', 'navdata', 'fs-base', 'freeflight', 'mission',
    'tutorial', 'discovery', 'point-of-interest', 'simobjects',
    'passiveaircraft', 'ships', 'animals', 'vehicles', 'pgg',
    'sceneryx', 'sceneryx-ingame-panel', 'wildbill75-sceneryx', 'autofps', 'beyondatc', 'toolbar', 'simbridge', 'sayintentions',
    'chaseplane', 'p42-util', 'aircraft', 'livery', 'liveries', 'fleet',
    'gsx', 'mobiflight', 'fsuipc', 'fslabs', 'fsrealistic', 'raas',
    'wwtwasm', 'traffic', 'simbrief', 'fsipanel', 'gaist', 'asfs', 'navigraph',
    'fnx', 'fenix', 'pmdg', 'flybywire', 'fbw', 'a320', 'a319', 'a321', 'a350',
    'a220', 'b737', 'b747', 'b777', 'b787', 'crj', 'justflight-aircraft', 'justflight-traffic', 'blackbox',
    'headwind', 'horizon', 'maddog', 'tfdi', 'workingtitle',
    'wt21', 'avionics', 'sound', 'effects', 'visualeffect',
    'inibuilds-aircraft', 'aerosoft-aircraft', 'milviz', 'blackbird',
    'cowan', 'hpg-', 'got-friends', 'salty', 'simupdates', 'fs2crew',
    'hifi', 'active-sky', 'airbus', 'boeing', 'bombardier', 'cessna',
    'embraer', 'piper', 'beechcraft', 'atr', 'concorde', 'helicopter',
    'vessels', 'vessel', 'seafront', 'arex', 'landmarks', 'landmark'
]

def is_core_or_library_package(pkg_path_or_name):
    """
    Bulletproof immunity detector:
    Guarantees that NO aircraft, livery, utility, tool, or core package
    can ever be classified as an airport scenery or disabled under any circumstances.
    """
    if not pkg_path_or_name:
        return False

    p_str = str(pkg_path_or_name).replace('\\', '/')
    p_lower = p_str.lower()

    # 1. Path-level checks for aircraft / livery dedicated directories
    if any(k in p_lower for k in [
        '/msfs_aircraft/', '/msfs_livery/', '/msfs_liveries/',
        'simobjects/airplanes', 'simobjects/rotorcraft', 'simobjects/boats',
        'airplanes', 'rotorcraft'
    ]):
        return True

    # 2. Extract clean base folder name
    base_name = os.path.basename(p_str.rstrip('/'))
    if base_name.lower().endswith('.disabled'):
        base_name = base_name[:-9]
    base_lower = base_name.lower()

    # Remove standard MSFS Content.xml prefixes
    norm_name = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', base_lower)

    # 3. String token checks against protected keywords
    if any(k in base_lower or k in norm_name for k in PROTECTED_SYSTEM_KEYWORDS):
        return True

    # 4. Deep structural inspection if path is a directory
    target_dir = None
    if os.path.isdir(pkg_path_or_name):
        target_dir = pkg_path_or_name
    elif p_str.endswith('.disabled') and os.path.isdir(p_str[:-9]):
        target_dir = p_str[:-9]
    elif os.path.isdir(p_str + '.disabled'):
        target_dir = p_str + '.disabled'

    if target_dir:
        # Check manifest.json content_type
        mpath = os.path.join(target_dir, 'manifest.json')
        if not os.path.exists(mpath):
            mpath = os.path.join(target_dir, 'manifest.json.disabled')
        if os.path.exists(mpath):
            try:
                with open(mpath, 'r', encoding='utf-8', errors='ignore') as mf:
                    mdata = json.load(mf)
                    ctype = str(mdata.get('content_type', '')).upper()
                    if ctype and ctype != 'SCENERY':
                        return True
            except Exception:
                pass

        # Check SimObjects presence
        so_dir = os.path.join(target_dir, 'SimObjects')
        if not os.path.exists(so_dir):
            so_dir = os.path.join(target_dir, 'SimObjects.disabled')
        if os.path.isdir(so_dir):
            for sub in ['Airplanes', 'Rotorcraft', 'Boats', 'Airplanes.disabled', 'Rotorcraft.disabled', 'Boats.disabled']:
                if os.path.isdir(os.path.join(so_dir, sub)):
                    return True

        # Check if package is streamed or contains .fsarchive containers
        is_streamed = 'streamed' in p_lower
        if not is_streamed and target_dir:
            try:
                is_streamed = any(f.endswith('.fsarchive') for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f)))
                if not is_streamed and os.path.isdir(os.path.join(target_dir, 'content')):
                    is_streamed = any(f.endswith('.fsarchive') for f in os.listdir(os.path.join(target_dir, 'content')))
            except Exception:
                pass

        if not is_streamed:
            # Check if package contains any scenery folder or compiled BGL files
            has_scenery_dir = os.path.isdir(os.path.join(target_dir, 'scenery')) or os.path.isdir(os.path.join(target_dir, 'Scenery'))
            if not has_scenery_dir:
                has_bgl = False
                lpath = os.path.join(target_dir, 'layout.json')
                if not os.path.exists(lpath):
                    lpath = os.path.join(target_dir, 'layout.json.disabled')
                if os.path.exists(lpath):
                    try:
                        with open(lpath, 'r', encoding='utf-8', errors='ignore') as lf:
                            ldata = json.load(lf)
                            has_bgl = any(c.get('path', '').lower().endswith(('.bgl', '.bgl.disabled')) for c in ldata.get('content', []))
                    except Exception:
                        pass
                if not has_bgl:
                    for root, dirs, files in os.walk(target_dir):
                        if any(f.lower().endswith(('.bgl', '.bgl.disabled')) for f in files):
                            has_bgl = True
                            break
                if not has_bgl:
                    # No scenery folder and no BGL files -> immune from scenery disabling!
                    return True

    return False

AIRPORTS_DB_CACHE = None

def resolve_package_icaos(pkg_name):
    if is_core_or_library_package(pkg_name):
        return set()

    global AIRPORTS_DB_CACHE
    if AIRPORTS_DB_CACHE is None:
        AIRPORTS_DB_CACHE, _, _ = load_airport_database()
    airports = AIRPORTS_DB_CACHE

    clean_fn = pkg_name.lower()
    if clean_fn.endswith('.disabled'):
        clean_fn = clean_fn[:-9]
    for prefix in ['communityfs20-', 'communityfs24-', 'officialfs20-', 'officialfs24-', 'fs20-', 'fs24-']:
        if clean_fn.startswith(prefix):
            clean_fn = clean_fn[len(prefix):]
            break

    if is_core_or_library_package(clean_fn):
        return set()

    found = set()
    if clean_fn in SPECIAL_BUNDLE_MAP:
        found.update(SPECIAL_BUNDLE_MAP[clean_fn])
    for b_key, b_icaos in SPECIAL_BUNDLE_MAP.items():
        if b_key in clean_fn:
            found.update(b_icaos)

    tokens = re.split(r'[-_ ]+', clean_fn)
    for t in tokens:
        t_l = t.lower()
        if any(k in t_l for k in [
            'fnx', 'fenix', 'pmdg', 'fbw', 'flybywire', 'a320', 'a319', 'a321', 'a350', 'a220',
            'b737', 'b747', 'b777', 'b787', 'crj', 'livery', 'liveries', 'fleet', 'simobjects',
            'fs20', 'fs24', 'vfra', 'pack', 'aero', 'vfr', 'mesh', 'tree', 'data'
        ]):
            continue
        t_upper = t.upper()
        if len(t_upper) == 4 and t_upper in airports:
            found.add(t_upper)

    return found

def get_folder_to_icaos_map(airports=None):
    if airports is None:
        if os.path.exists(OUTPUT_JSON_PATH):
            try:
                with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                    airports = json.load(f)
            except Exception:
                airports = []
        else:
            airports = []

    folder_to_icaos = {}
    third_party_airport_pkgs = set()

    if airports:
        for ap in airports:
            icao = ap.get('icao')
            pricing = ap.get('pricing_type')
            for src in ap.get('all_sources', []):
                fn = src.get('folder_name', '')
                if fn:
                    fn_clean = fn[:-9] if fn.endswith('.disabled') else fn
                    fn_clean_lower = fn_clean.lower()
                    fn_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', fn_clean_lower)

                    folder_to_icaos.setdefault(fn_clean_lower, set()).add(icao)
                    folder_to_icaos.setdefault(fn_norm, set()).add(icao)
                    folder_to_icaos.setdefault(f"fs20-{fn_norm}", set()).add(icao)
                    folder_to_icaos.setdefault(f"fs24-{fn_norm}", set()).add(icao)
                    folder_to_icaos.setdefault(f"communityfs20-{fn_norm}", set()).add(icao)
                    folder_to_icaos.setdefault(f"communityfs24-{fn_norm}", set()).add(icao)

                    if pricing not in ['Asobo', 'Default'] and not src.get('is_asobo_official') and not src.get('is_default'):
                        third_party_airport_pkgs.add(fn_clean_lower)
                        third_party_airport_pkgs.add(fn_norm)
                        third_party_airport_pkgs.add(f"fs20-{fn_norm}")
                        third_party_airport_pkgs.add(f"fs24-{fn_norm}")
                        third_party_airport_pkgs.add(f"communityfs20-{fn_norm}")
                        third_party_airport_pkgs.add(f"communityfs24-{fn_norm}")

    return folder_to_icaos, third_party_airport_pkgs

_CACHED_CONTENT_XML_PATH = None

def get_content_xml_paths():
    local_appdata = os.getenv('LOCALAPPDATA', '')
    appdata = os.getenv('APPDATA', '')
    limitless_cache = os.path.join(local_appdata, r'Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache')
    msfs24_steam = os.path.join(appdata, r'Microsoft Flight Simulator 2024')

    paths = []

    # 1. MSFS 2024 Store / Game Pass (Limitless) - Dynamically discover Xbox Gamertag profile folder and root LocalCache
    if os.path.exists(limitless_cache):
        main_limitless_xml = os.path.join(limitless_cache, 'Content.xml')
        sub_xmls = []
        try:
            for item in os.listdir(limitless_cache):
                sub = os.path.join(limitless_cache, item)
                if os.path.isdir(sub) and item not in ('Packages', 'PC', '$PC$', 'ModelLibCache', 'SceneryIndexes', 'SimObjects'):
                    sub_xml = os.path.join(sub, 'Content.xml')
                    if os.path.exists(sub_xml):
                        sub_xmls.append(sub_xml)
        except Exception:
            pass

        # Synchronization guarantee: If sub_xml exists but main_limitless_xml does not, copy it over!
        if sub_xmls and not os.path.exists(main_limitless_xml):
            try:
                import shutil
                shutil.copy2(sub_xmls[0], main_limitless_xml)
            except Exception:
                pass
        # Conversely, if main_limitless_xml exists, ensure all sub profile folders have it synchronized
        elif os.path.exists(main_limitless_xml):
            for s_xml in sub_xmls:
                if not os.path.exists(s_xml):
                    try:
                        import shutil
                        shutil.copy2(main_limitless_xml, s_xml)
                    except Exception:
                        pass

        for s_xml in sub_xmls:
            if s_xml not in paths:
                paths.append(s_xml)
        if main_limitless_xml not in paths:
            paths.append(main_limitless_xml)

    # 2. MSFS 2024 Steam - Dynamically discover user profile folder
    if os.path.exists(msfs24_steam):
        try:
            for item in os.listdir(msfs24_steam):
                sub = os.path.join(msfs24_steam, item)
                if os.path.isdir(sub):
                    sub_xml = os.path.join(sub, 'Content.xml')
                    if os.path.exists(sub_xml):
                        paths.append(sub_xml)
        except Exception:
            pass
        paths.append(os.path.join(msfs24_steam, 'Content.xml'))

    # 3. MSFS 2020 Store & Steam
    paths.append(os.path.join(local_appdata, r'Packages\Microsoft.FlightSimulator_8wekyb3d8bbwe\LocalCache\Content.xml'))
    paths.append(os.path.join(appdata, r'Microsoft Flight Simulator\Content.xml'))

    return paths


def get_existing_content_xml_paths():
    return [p for p in get_content_xml_paths() if os.path.exists(p)]

def get_content_xml_path():
    global _CACHED_CONTENT_XML_PATH
    if _CACHED_CONTENT_XML_PATH and os.path.exists(_CACHED_CONTENT_XML_PATH):
        return _CACHED_CONTENT_XML_PATH

    paths = get_content_xml_paths()
    for p in paths:
        if os.path.exists(p):
            _CACHED_CONTENT_XML_PATH = p
            return p
    _CACHED_CONTENT_XML_PATH = paths[0]
    return _CACHED_CONTENT_XML_PATH

def sanitize_msfs_content_xml():
    """
    Enforces absolute immunity and integrity in MSFS Content.xml files:
    1. Unconditionally restores ANY aircraft, livery, utility, model library, or instrument to 'Activated'.
    2. Strips any corrupt or invalid .disabled elements.
    3. Removes duplicates.
    """
    content_xml_paths = get_content_xml_paths()
    for xml_path in content_xml_paths:
        if not os.path.exists(xml_path):
            continue
        try:
            import xml.etree.ElementTree as ET
            with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ET.fromstring(content)
            changed = False

            for elem in list(tree.findall('Package')):
                name = elem.get('name', '')
                if not name:
                    continue
                name_clean = name[:-9] if name.endswith('.disabled') else name
                if name.lower().endswith('.disabled'):
                    tree.remove(elem)
                    changed = True
                    continue

                if re.search(r'[-_\s.](copy|copie|backup|bak)(\b|\d*)', name.lower()) and elem.get('active') != 'UserDisabled':
                    tree.remove(elem)
                    changed = True
                    continue

                if is_core_or_library_package(name) or is_core_or_library_package(name_clean):
                    if elem.get('active') == 'UserDisabled':
                        elem.set('active', 'Activated')
                        changed = True

            if changed:
                seen_exact = set()
                for elem in list(tree.findall('Package')):
                    n = elem.get('name', '').strip().lower()
                    if n in seen_exact:
                        tree.remove(elem)
                    else:
                        seen_exact.add(n)

                ET.indent(tree, space='  ')
                xml_str = ET.tostring(tree, encoding='unicode')
                with open(xml_path, 'w', encoding='utf-8') as f:
                    f.write('<?xml version="1.0" encoding="utf-8"?>\n' + xml_str.strip() + '\n')
                print(f"[Sanitize] Repaired & ensured immunity in {xml_path}")
        except Exception as e:
            print(f"[Sanitize] Error sanitizing {xml_path}: {e}")

def safe_remove_path(p):
    """Safely removes a file, symlink, junction or folder without affecting the junction target."""
    if not p:
        return
    try:
        if os.path.islink(p):
            os.unlink(p)
        elif hasattr(os.path, 'isjunction') and os.path.isjunction(p):
            os.rmdir(p)
        elif os.path.isfile(p):
            os.remove(p)
        elif os.path.isdir(p):
            import shutil
            shutil.rmtree(p)
    except Exception as e:
        print(f"Warning: safe_remove_path failed on {p}: {e}")

def safe_rename_path(src, dst):
    """Safely renames src to dst, handling existing symlinks, junctions, files, and directories to prevent WinError 183."""
    if not src:
        return False
    src_exists = os.path.exists(src) or os.path.islink(src) or (hasattr(os.path, 'isjunction') and os.path.isjunction(src))
    if not src_exists:
        return False
    if os.path.abspath(src).lower() == os.path.abspath(dst).lower():
        return True

    dst_exists = os.path.exists(dst) or os.path.islink(dst) or (hasattr(os.path, 'isjunction') and os.path.isjunction(dst))
    if dst_exists:
        if os.path.islink(dst) or (hasattr(os.path, 'isjunction') and os.path.isjunction(dst)):
            safe_remove_path(dst)
        elif os.path.isfile(dst):
            os.remove(dst)
        elif os.path.isdir(dst):
            if os.path.islink(src) or (hasattr(os.path, 'isjunction') and os.path.isjunction(src)):
                safe_remove_path(src)
                return True
            else:
                safe_remove_path(dst)

    try:
        os.rename(src, dst)
        return True
    except Exception as e:
        print(f"Error renaming {src} to {dst}: {e}")
        raise

def disable_physical_package(p_path):
    """Disables a package on disk (folder.disabled, manifest.json.disabled, layout.json.disabled)."""
    if not p_path:
        return p_path

    # HARD IMMUNITY GUARD: Never disable any aircraft, livery, utility, tool or core package
    if is_core_or_library_package(p_path):
        print(f"[IMMUNITY GUARD] Refusing to disable protected package: {p_path}")
        return p_path

    clean_p = p_path[:-9] if p_path.endswith('.disabled') else p_path
    dis_p = clean_p + '.disabled'

    clean_exists = os.path.exists(clean_p) or os.path.islink(clean_p) or (hasattr(os.path, 'isjunction') and os.path.isjunction(clean_p))
    dis_exists = os.path.exists(dis_p) or os.path.islink(dis_p) or (hasattr(os.path, 'isjunction') and os.path.isjunction(dis_p))

    if clean_exists:
        if not dis_exists:
            safe_rename_path(clean_p, dis_p)
        else:
            safe_remove_path(dis_p)
            safe_rename_path(clean_p, dis_p)

    new_p = dis_p
    if os.path.exists(new_p):
        for mf in ['manifest.json', 'layout.json']:
            mf_norm = os.path.join(new_p, mf)
            mf_dis = os.path.join(new_p, mf + '.disabled')
            if os.path.exists(mf_norm):
                if os.path.exists(mf_dis):
                    safe_remove_path(mf_dis)
                safe_rename_path(mf_norm, mf_dis)
    return new_p

def enable_physical_package(p_path):
    """Enables a package on disk (removes .disabled suffix from folder and manifest/layout files)."""
    if not p_path:
        return p_path
    clean_p = p_path[:-9] if p_path.endswith('.disabled') else p_path
    dis_p = clean_p + '.disabled'

    clean_exists = os.path.exists(clean_p) or os.path.islink(clean_p) or (hasattr(os.path, 'isjunction') and os.path.isjunction(clean_p))
    dis_exists = os.path.exists(dis_p) or os.path.islink(dis_p) or (hasattr(os.path, 'isjunction') and os.path.isjunction(dis_p))

    if dis_exists:
        if not clean_exists:
            safe_rename_path(dis_p, clean_p)
        else:
            safe_remove_path(dis_p)

    new_p = clean_p
    if os.path.exists(new_p):
        for mf in ['manifest.json', 'layout.json']:
            mf_dis = os.path.join(new_p, mf + '.disabled')
            mf_norm = os.path.join(new_p, mf)
            if os.path.exists(mf_dis):
                if os.path.exists(mf_norm):
                    safe_remove_path(mf_norm)
                safe_rename_path(mf_dis, mf_norm)
    return new_p

def set_package_state_for_icao(p_path, target_icao, should_enable):
    """Enables or disables a package for a specific ICAO, handling multi-airport packages (bgl renaming) and single airport packages."""
    if not p_path:
        return

    # HARD IMMUNITY GUARD: Never alter any aircraft, livery, utility, tool or core package
    if is_core_or_library_package(p_path):
        print(f"[IMMUNITY GUARD] Refusing to alter protected package in set_package_state_for_icao: {p_path}")
        return

    clean_p = p_path[:-9] if p_path.endswith('.disabled') else p_path
    dis_p = clean_p + '.disabled'
    target_dir = clean_p if (os.path.exists(clean_p) or os.path.islink(clean_p) or (hasattr(os.path, 'isjunction') and os.path.isjunction(clean_p))) else (dis_p if (os.path.exists(dis_p) or os.path.islink(dis_p) or (hasattr(os.path, 'isjunction') and os.path.isjunction(dis_p))) else None)
    if not target_dir:
        return

    # Streamed / Asobo / Microsoft base packages must NEVER be renamed physically on disk (managed via Content.xml)
    td_lower = target_dir.lower()
    fn_base_lower = os.path.basename(clean_p).lower()
    if 'streamed' in td_lower or fn_base_lower.startswith(('asobo-', 'microsoft-', 'fs20-asobo-', 'fs24-asobo-', 'fs20-microsoft-', 'fs24-microsoft-', 'fs-base')):
        if should_enable and dis_p and (os.path.exists(dis_p) or os.path.islink(dis_p) or (hasattr(os.path, 'isjunction') and os.path.isjunction(dis_p))):
            enable_physical_package(dis_p)
        return

    # Check if package is potentially a multi-airport bundle
    folder_base = os.path.basename(clean_p).lower()
    is_potential_bundle = any(k in folder_base for k in ['pack', 'bundle', 'airports', 'vfr', 'airfields', 'francevfr', 'fvfr']) or folder_base in SPECIAL_BUNDLE_MAP

    if not is_potential_bundle:
        # Fast path for standard single-airport packages: instant folder rename
        if should_enable:
            enable_physical_package(target_dir)
            # Ensure any internal .bgl.disabled are restored to active .bgl
            if os.path.exists(clean_p):
                for root, dirs, files in os.walk(clean_p):
                    for f in files:
                        if f.lower().endswith('.bgl.disabled'):
                            old_bgl = os.path.join(root, f)
                            safe_rename_path(old_bgl, old_bgl[:-9])
        else:
            disable_physical_package(target_dir)
        return

    icao_l = target_icao.lower() if target_icao else ""
    matching_bgls = []
    other_bgls = []

    if os.path.exists(target_dir):
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d.lower() not in ('texture', 'textures', 'materiallibs', 'sound', 'modellib', 'html_ui', 'model', 'effects', 'weather', 'visualeffects', 'ai')]
            for f in files:
                f_l = f.lower()
                if f_l.endswith('.bgl') or f_l.endswith('.bgl.disabled'):
                    f_path = os.path.join(root, f)
                    if icao_l and icao_l in f_l:
                        matching_bgls.append(f_path)
                    else:
                        other_bgls.append(f_path)

    if matching_bgls and len(other_bgls) > 0:
        if target_dir.endswith('.disabled'):
            enable_physical_package(target_dir)
            target_dir = clean_p
            matching_bgls = []
            for root, dirs, files in os.walk(target_dir):
                dirs[:] = [d for d in dirs if d.lower() not in ('texture', 'textures', 'materiallibs', 'sound', 'modellib', 'html_ui', 'model', 'effects', 'weather', 'visualeffects', 'ai')]
                for f in files:
                    if icao_l and icao_l in f.lower() and (f.lower().endswith('.bgl') or f.lower().endswith('.bgl.disabled')):
                        matching_bgls.append(os.path.join(root, f))

        for bgl_p in matching_bgls:
            if should_enable:
                if bgl_p.endswith('.bgl.disabled'):
                    new_bgl = bgl_p[:-9]
                    safe_rename_path(bgl_p, new_bgl)
            else:
                if bgl_p.endswith('.bgl'):
                    new_bgl = bgl_p + '.disabled'
                    safe_rename_path(bgl_p, new_bgl)
    else:
        if should_enable:
            enable_physical_package(target_dir)
            if os.path.exists(clean_p):
                for root, dirs, files in os.walk(clean_p):
                    for f in files:
                        if f.lower().endswith('.bgl.disabled'):
                            old_bgl = os.path.join(root, f)
                            safe_rename_path(old_bgl, old_bgl[:-9])
        else:
            disable_physical_package(target_dir)

def update_msfs_content_xml(keep_icaos=None, restore_flight_mode=False, flight_disabled_xml=None, flight_added_xml=None, pre_existing_disabled_xml=None, folder_to_icaos=None, third_party_airport_pkgs=None, all_airports=None, full_reset=False):
    content_xml_paths = get_content_xml_paths()

    if folder_to_icaos is None or third_party_airport_pkgs is None:
        folder_to_icaos, third_party_airport_pkgs = get_folder_to_icaos_map(all_airports)

    def get_package_icaos(pkg_name):
        clean = pkg_name[:-9] if pkg_name.endswith('.disabled') else pkg_name
        clean_lower = clean.lower()
        norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', clean_lower)

        icaos = folder_to_icaos.get(clean_lower) or folder_to_icaos.get(norm)
        if icaos:
            return set(icaos)

        # SPECIAL_BUNDLE_MAP check (France VFR and other multi-airport bundles)
        b_icaos = SPECIAL_BUNDLE_MAP.get(clean_lower) or SPECIAL_BUNDLE_MAP.get(norm)
        if b_icaos:
            return set(b_icaos)
        for bk, bv in SPECIAL_BUNDLE_MAP.items():
            if bk in clean_lower or bk in norm:
                return set(bv)

        res = resolve_package_icaos(clean) or resolve_package_icaos(norm)
        if res:
            return set(res)

        m = re.search(r'[-_]airport[-_]([a-z0-9]{3,4})([-_]|$)', clean_lower)
        if m:
            return {m.group(1).upper()}

        # Known Handcrafted / Payware Airport name patterns (Gatwick, Frankfurt, Vancouver, etc.)
        for t_icao, t_words in [
            ('EGKK', ['gatwick', 'egkk']),
            ('EDDF', ['frankfurt', 'eddf']),
            ('CYVR', ['vancouver', 'cyvr']),
            ('LFBD', ['bordeaux', 'merignac', 'lfbd']),
            ('LFML', ['marseille', 'lfml']),
            ('LFKB', ['bastia', 'lfkb'])
        ]:
            if any(w in clean_lower for w in t_words):
                return {t_icao}

        if clean_lower in third_party_airport_pkgs or norm in third_party_airport_pkgs:
            return {'AIRPORT_UNKNOWN'}

        # France VFR generic fallback
        if any(k in clean_lower for k in ['francevfr', 'fvfr']):
            return {'AIRPORT_FRANCEVFR'}

        # General airport indicators
        if any(k in clean_lower for k in ['-airport-', '_airport_', '-airfield-', '-aerodrome-']):
            return {'AIRPORT_UNKNOWN'}

        # Discovery / Bushtrip for non-kept cities
        if any(k in clean_lower for k in ['bushtrip', 'discovery']):
            for t_icao, t_words in [
                ('EGKK', ['gatwick']),
                ('EDDF', ['frankfurt']),
                ('CYVR', ['vancouver'])
            ]:
                if any(w in clean_lower for w in t_words):
                    return {t_icao}

        return set()

    flight_disabled_set = set(flight_disabled_xml or [])
    flight_added_set = set(flight_added_xml or [])
    disabled_xml_packages = set()
    added_xml_packages = set()

    target_icaos = set(k.upper() for k in (keep_icaos or []))

    for xml_path in content_xml_paths:
        if not os.path.exists(xml_path):
            parent_dir = os.path.dirname(xml_path)
            if os.path.isdir(parent_dir):
                for other_p in content_xml_paths:
                    if other_p != xml_path and os.path.exists(other_p):
                        try:
                            import shutil
                            shutil.copy2(other_p, xml_path)
                            break
                        except Exception:
                            pass
            if not os.path.exists(xml_path):
                continue
        try:
            import xml.etree.ElementTree as ET
            with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            tree = ET.fromstring(content)
            changed = False

            if restore_flight_mode:
                flight_disabled_set_lower = {x.lower() for x in (flight_disabled_xml or [])}
                flight_added_set_lower = {x.lower() for x in (flight_added_xml or [])}
                pre_existing_xml_lower = {x.lower() for x in (pre_existing_disabled_xml or [])}
                all_conflict_sec_lower = {k.lower() for sec_list in KNOWN_CONFLICT_SECONDARY_PACKAGES.values() for k in sec_list}

                for elem in list(tree.findall('Package')):
                    name = elem.get('name', '')
                    name_clean = name[:-9] if name.endswith('.disabled') else name
                    name_lower = name.lower()
                    name_clean_lower = name_clean.lower()
                    name_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', name_clean_lower)

                    # Remove any spurious .disabled entries or packages temporarily added by flight mode
                    if name_lower.endswith('.disabled') or name_lower in flight_added_set_lower or name_clean_lower in flight_added_set_lower:
                        tree.remove(elem)
                        changed = True
                        continue

                    # STRICT SAFEGUARD: Never re-enable known secondary conflicting packages
                    if name_clean_lower in all_conflict_sec_lower or name_norm in all_conflict_sec_lower:
                        continue

                    # Re-enable all scenery packages to Activated
                    if elem.get('active') == 'UserDisabled':
                        elem.set('active', 'Activated')
                        changed = True

                # Always guarantee all aircraft, liveries, instruments and core tools are Activated
                for elem in tree.findall('Package'):
                    name = elem.get('name', '')
                    if is_core_or_library_package(name):
                        if elem.get('active') == 'UserDisabled':
                            elem.set('active', 'Activated')
                            changed = True
            else:
                seen_xml_names = set()
                for elem in tree.findall('Package'):
                    name = elem.get('name', '')
                    clean_lower = (name[:-9] if name.endswith('.disabled') else name).lower()
                    seen_xml_names.add(clean_lower)
                    norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', clean_lower)
                    seen_xml_names.add(norm)

                    # STRICT IMMUNITY: Never touch or disable aircraft, liveries, instruments or tools
                    if is_core_or_library_package(name):
                        if elem.get('active') == 'UserDisabled':
                            elem.set('active', 'Activated')
                            changed = True
                        continue

                    pkg_icaos = get_package_icaos(name)
                    if pkg_icaos:
                        is_keep = any(k in target_icaos for k in pkg_icaos)
                        if not is_keep:
                            if elem.get('active') == 'Activated':
                                elem.set('active', 'UserDisabled')
                                disabled_xml_packages.add(name)
                                changed = True
                    elif name.endswith('.disabled') and not is_core_or_library_package(name):
                        if elem.get('active') == 'Activated':
                            elem.set('active', 'UserDisabled')
                            disabled_xml_packages.add(name)
                            changed = True

                # Final immunity sweep: Guarantee ALL aircraft and liveries remain Activated
                for elem in tree.findall('Package'):
                    name = elem.get('name', '')
                    if is_core_or_library_package(name):
                        if elem.get('active') == 'UserDisabled':
                            elem.set('active', 'Activated')
                            changed = True

            if changed or not os.path.exists(xml_path):
                # Safeguard: deduplicate packages before saving
                seen_exact = set()
                for elem in list(tree.findall('Package')):
                    n = elem.get('name', '').strip().lower()
                    if n in seen_exact:
                        tree.remove(elem)
                    else:
                        seen_exact.add(n)

                ET.indent(tree, space='  ')
                xml_str = ET.tostring(tree, encoding='unicode')
                with open(xml_path, 'w', encoding='utf-8') as f:
                    f.write('<?xml version="1.0" encoding="utf-8"?>\n' + xml_str.strip() + '\n')
                print(f"Successfully updated MSFS Content.xml at {xml_path}")
        except Exception as e:
            print(f"Error updating Content.xml at {xml_path}: {e}")

    return disabled_xml_packages, added_xml_packages

AIRPORTS_CACHE = None

def fast_update_airport_cache(icao_target, target_pkg_name=None, toggle_all=False, fix_path_toggled=None, fix_enabled=None):
    global AIRPORTS_CACHE
    if not os.path.exists(OUTPUT_JSON_PATH):
        airports = run_scan()
        AIRPORTS_CACHE = airports
        return airports
    try:
        if AIRPORTS_CACHE is None:
            with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                AIRPORTS_CACHE = json.load(f)
        airports = AIRPORTS_CACHE

        target_ap = None
        for ap in airports:
            if ap.get('icao') == icao_target:
                target_ap = ap
                break

        if not target_ap:
            return run_scan()

        all_srcs = target_ap.get('all_sources', [])

        if target_pkg_name == 'DEFAULT':
            for s in all_srcs:
                if s.get('is_fix_patch') or s.get('is_addon'):
                    continue
                s['is_disabled'] = True
                fn = s.get('folder_name', '')
                s['folder_name'] = fn[:-9] if fn.lower().endswith('.disabled') else fn
        elif target_pkg_name:
            t_raw_clean = target_pkg_name[:-9] if target_pkg_name.lower().endswith('.disabled') else target_pkg_name
            t_is_path = ('\\' in t_raw_clean or '/' in t_raw_clean)
            t_clean = os.path.basename(t_raw_clean) if t_is_path else t_raw_clean
            t_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', t_clean.lower())
            for s in all_srcs:
                if s.get('is_fix_patch') or s.get('is_addon'):
                    continue
                fn = s.get('folder_name', '')
                fn_clean = fn[:-9] if fn.lower().endswith('.disabled') else fn
                fn_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', fn_clean.lower())
                s['folder_name'] = fn_clean
                p = s.get('package_path', '')
                clean_p = p[:-9] if p and p.endswith('.disabled') else p
                dis_p = clean_p + '.disabled' if clean_p else None

                if t_is_path and clean_p:
                    is_match = (os.path.normcase(os.path.abspath(clean_p)) == os.path.normcase(os.path.abspath(t_raw_clean)))
                else:
                    is_match = (
                        fn_clean.lower() == t_clean.lower() 
                        or fn_norm == t_norm 
                        or (s.get('is_asobo_official') and ('asobo' in t_clean.lower() or 'microsoft' in t_clean.lower()))
                    )

                if is_match:
                    s['is_disabled'] = False
                    if clean_p:
                        s['package_path'] = clean_p
                        if os.path.exists(clean_p):
                            for root, dirs, files in os.walk(clean_p):
                                for f in files:
                                    if f.lower().endswith('.bgl.disabled'):
                                        old_b = os.path.join(root, f)
                                        safe_rename_path(old_b, old_b[:-9])
                else:
                    s['is_disabled'] = True
                    if dis_p and (os.path.exists(dis_p) or os.path.islink(dis_p) or (hasattr(os.path, 'isjunction') and os.path.isjunction(dis_p))):
                        s['package_path'] = dis_p
        elif fix_path_toggled is not None:
            clean_fix_path = fix_path_toggled[:-9] if fix_path_toggled.lower().endswith('.disabled') else fix_path_toggled
            clean_fix_name = os.path.basename(clean_fix_path).lower()
            clean_fix_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', clean_fix_name)
            for s in all_srcs:
                fn = s.get('folder_name', '')
                clean_fn = fn[:-9] if fn.lower().endswith('.disabled') else fn
                clean_fn_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', clean_fn.lower())
                pkg_p = s.get('package_path', '')
                clean_p = pkg_p[:-9] if pkg_p and pkg_p.endswith('.disabled') else pkg_p

                is_this_fix = (
                    clean_fn.lower() == clean_fix_name 
                    or clean_fn_norm == clean_fix_norm
                    or (clean_p and clean_p.lower() == clean_fix_path.lower())
                    or (clean_fix_norm and clean_fn_norm and (clean_fix_norm in clean_fn_norm or clean_fn_norm in clean_fix_norm))
                )
                if is_this_fix:
                    s['is_disabled'] = not fix_enabled
                    s['folder_name'] = clean_fn if fix_enabled else (clean_fn + '.disabled')
                    if clean_p:
                        s['package_path'] = clean_p if fix_enabled else (clean_p + '.disabled')
        else:
            content_xml_path = get_content_xml_path()
            content_xml_status = {}
            if os.path.exists(content_xml_path):
                try:
                    import xml.etree.ElementTree as ET
                    tree = ET.parse(content_xml_path)
                    for p in tree.getroot().findall('Package'):
                        p_name = p.get('name', '')
                        p_clean = p_name[:-9] if p_name.lower().endswith('.disabled') else p_name
                        content_xml_status[p_clean.lower()] = (p.get('active') == 'Activated')
                except Exception:
                    pass

            for s in all_srcs:
                is_official = s.get('is_asobo_official') or any(k in (s.get('source_folder', '') or '').lower() for k in ['streamed', 'official']) or any(k in (s.get('folder_name', '') or '').lower() for k in ['asobo-', 'microsoft-'])
                fn = s.get('folder_name', '')
                fn_clean = fn[:-9] if fn.lower().endswith('.disabled') else fn
                p = s.get('package_path', '')
                clean_p = p[:-9] if p and p.endswith('.disabled') else p
                dis_p = clean_p + '.disabled' if clean_p else None

                if is_official:
                    found_in_xml = None
                    for xml_pkg, is_act in content_xml_status.items():
                        if xml_pkg == fn_clean.lower() or xml_pkg in fn_clean.lower() or fn_clean.lower() in xml_pkg:
                            found_in_xml = is_act
                            break
                    if found_in_xml is not None:
                        s['is_disabled'] = not found_in_xml
                        if found_in_xml and dis_p and (os.path.exists(dis_p) or os.path.islink(dis_p)):
                            enable_physical_package(dis_p)
                        continue

                folder_exists = clean_p and os.path.exists(clean_p)
                dis_folder_exists = dis_p and os.path.exists(dis_p)

                if dis_folder_exists and not folder_exists:
                    s['is_disabled'] = True
                    s['package_path'] = dis_p
                elif folder_exists:
                    s['package_path'] = clean_p
                    icao_l = icao_target.lower()
                    has_act_bgl = False
                    has_dis_bgl = False
                    for root, dirs, files in os.walk(clean_p):
                        for f in files:
                            f_l = f.lower()
                            if icao_l in f_l:
                                if f_l.endswith('.bgl'):
                                    has_act_bgl = True
                                elif f_l.endswith('.bgl.disabled'):
                                    has_dis_bgl = True
                    if has_dis_bgl and not has_act_bgl:
                        s['is_disabled'] = True
                    else:
                        s['is_disabled'] = False

        # Recalculate active main scenery packages (excluding Fix/Patch and Addon packages)
        active_primary_installs = [
            s for s in all_srcs 
            if not s.get('is_disabled') and not s.get('is_addon') and not s.get('is_fix_patch')
        ]
        
        # Conflict recalculation: A conflict ONLY exists if 2 or more MAIN sceneries are ACTIVE
        if len(active_primary_installs) > 1:
            target_ap['has_conflict'] = True
            target_ap['conflict_count'] = len(active_primary_installs)
        else:
            target_ap['has_conflict'] = False
            active_sources = [s for s in all_srcs if not s.get('is_disabled')]
            target_ap['conflict_count'] = max(1, len(active_sources))

        # Recalculate primary package & vendor from active sources
        active_sources = [s for s in all_srcs if not s.get('is_disabled')]
        main_active = [s for s in active_sources if not s.get('is_fix_patch') and not s.get('is_addon')]
        if main_active:
            primary = main_active[0]

            target_ap['package_name'] = primary['folder_name']
            target_ap['package_path'] = primary.get('package_path', '')
            target_ap['source_folder'] = primary.get('source_folder', '')
            target_ap['match_source'] = primary.get('match_source', '')
            target_ap['version'] = primary.get('version', '')

            custom_prices = load_custom_prices()
            user_override_cat = None
            if icao_target in custom_prices:
                val = custom_prices[icao_target]
                if isinstance(val, dict) and val.get('category'):
                    user_override_cat = val['category']

            if user_override_cat == 'Payware':
                target_ap['vendor'] = primary.get('vendor', 'Unknown')
                target_ap['pricing_type'] = "Payware"
                target_ap['is_payware'] = True
                target_ap['is_asobo_official'] = False
                for s in all_srcs:
                    s['pricing_type'] = "Payware"
                    s['is_payware'] = True
            elif user_override_cat in ['Freeware', 'Freeware / Flightsim.to']:
                target_ap['vendor'] = primary.get('vendor', 'Unknown')
                target_ap['pricing_type'] = "Freeware / Flightsim.to"
                target_ap['is_payware'] = False
                target_ap['is_asobo_official'] = False
                for s in all_srcs:
                    s['pricing_type'] = "Freeware / Flightsim.to"
                    s['is_payware'] = False
            elif primary.get('is_payware'):
                target_ap['vendor'] = primary.get('vendor', 'Unknown')
                target_ap['pricing_type'] = "Payware"
                target_ap['is_payware'] = True
                target_ap['is_asobo_official'] = False
            elif primary.get('is_asobo_official') or primary.get('pricing_type') == 'Asobo' or primary.get('vendor') == 'Microsoft / Asobo':
                target_ap['vendor'] = "Microsoft / Asobo"
                target_ap['pricing_type'] = "Asobo"
                target_ap['is_payware'] = False
                target_ap['is_asobo_official'] = True
            else:
                target_ap['vendor'] = primary.get('vendor', 'Unknown')
                target_ap['pricing_type'] = primary.get('pricing_type', 'Freeware / Flightsim.to')
                target_ap['is_payware'] = primary.get('is_payware', False)
                target_ap['is_asobo_official'] = False
            target_ap['is_disabled'] = False

            price_val, is_cust = get_estimated_price(
                icao_target,
                primary.get('folder_name', ''),
                target_ap.get('vendor', ''),
                target_ap.get('pricing_type', ''),
                target_ap.get('english_type', ''),
                target_ap.get('is_asobo_official', False),
                custom_prices
            )
            target_ap['price_eur'] = price_val
            target_ap['is_custom_price'] = is_cust
        else:
            target_ap['package_name'] = "Default MSFS Base Airport"
            target_ap['vendor'] = "Microsoft / Asobo"
            target_ap['pricing_type'] = "Default"
            target_ap['is_payware'] = False
            target_ap['is_asobo_official'] = False
            target_ap['is_disabled'] = False
            target_ap['price_eur'] = 0.0
            target_ap['is_custom_price'] = False

        tmp_path = OUTPUT_JSON_PATH + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(airports, f, ensure_ascii=False)
        try:
            os.replace(tmp_path, OUTPUT_JSON_PATH)
        except Exception:
            if os.path.exists(OUTPUT_JSON_PATH):
                os.remove(OUTPUT_JSON_PATH)
            os.rename(tmp_path, OUTPUT_JSON_PATH)

        import threading
        threading.Thread(target=sync_library_snapshot, args=(airports,), daemon=True).start()
        return airports
    except Exception as e:
        print("Error fast updating cache:", e)
        return run_scan()

def sync_library_snapshot(airports):
    try:
        current_snapshot = build_library_snapshot(airports)
        with open(SNAPSHOT_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(current_snapshot, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Error syncing library snapshot:", e)

def bring_window_to_front(window_title="SceneryX"):
    try:
        import ctypes
        hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception:
        pass

shared_splash_state = {
    "percent": 10,
    "text": "Scanning MSFS packages & GSX profiles..."
}

class SplashApi:
    def __init__(self, state):
        self._state = state

    def get_splash_state(self):
        return self._state

splash_window = None

def finish_splash_and_reveal_main():
    global splash_window
    import threading
    def _do_switch():
        time.sleep(0.15)
        global splash_window
        print("[Splash] Closing splash screen...", flush=True)
        if splash_window:
            try:
                splash_window.destroy()
            except Exception as e:
                print(f"[Splash] Destroy warning: {e}", flush=True)
            splash_window = None

        main_win = getattr(Api, '_main_window_instance', None)
        print(f"[Main] Revealing main window (instance: {main_win})...", flush=True)
        if main_win:
            try:
                main_win.show()
                main_win.restore()
            except Exception as e:
                print(f"[Main] Show warning: {e}", flush=True)
        bring_window_to_front("SceneryX")
        print("[Main] Transition complete!", flush=True)

    threading.Thread(target=_do_switch, daemon=True).start()

class Api:
    _main_window_instance = None

    def __init__(self):
        self._startup_delta = {"added": [], "removed": [], "total_changes": 0}
        self._startup_scanned = False
        threading.Thread(target=self._auto_sync_installed_ingame_panel, daemon=True).start()
        threading.Thread(target=self._auto_preload_simbrief_ofp, daemon=True).start()

    def _auto_preload_simbrief_ofp(self):
        try:
            flight_perf_tracker.get_simbrief_flight_plan(force_refresh=True)
        except Exception:
            pass

    def _auto_sync_installed_ingame_panel(self):
        try:
            import shutil
            all_paths = self._get_all_community_paths()
            if not all_paths:
                return
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            src_dir = os.path.join(base_dir, "sceneryx-ingame-panel")
            if not os.path.exists(src_dir):
                src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sceneryx-ingame-panel")
            if not os.path.exists(src_dir):
                return
            migrated_or_updated = False
            for c_path in all_paths:
                legacy_dir = os.path.join(c_path, "wildbill75-sceneryx")
                target_dir = os.path.join(c_path, "sceneryx-ingame-panel")
                had_legacy = os.path.exists(legacy_dir)
                if had_legacy:
                    try:
                        shutil.rmtree(legacy_dir)
                    except Exception:
                        pass
                if had_legacy or os.path.exists(os.path.join(target_dir, "manifest.json")):
                    shutil.copytree(src_dir, target_dir, dirs_exist_ok=True)
                    migrated_or_updated = True
            if migrated_or_updated:
                for p in get_content_xml_paths():
                    if os.path.exists(p):
                        try:
                            with open(p, "r", encoding="utf-8") as f:
                                cxml = f.read()
                            cxml_new = re.sub(r'\s*<Package name="[^"]*wildbill75-sceneryx"[^>]*/>', '', cxml)
                            for pk in ["communityfs20-sceneryx-ingame-panel", "communityfs24-sceneryx-ingame-panel"]:
                                if f'<Package name="{pk}"' not in cxml_new and '</Packages>' in cxml_new:
                                    cxml_new = cxml_new.replace('</Packages>', f'\t<Package name="{pk}" active="Activated" />\n</Packages>')
                            if cxml_new != cxml:
                                with open(p, "w", encoding="utf-8") as f:
                                    f.write(cxml_new)
                        except Exception:
                            pass
        except Exception:
            pass

    def update_splash_progress(self, percent, text=""):
        global shared_splash_state
        try:
            shared_splash_state["percent"] = percent
            if text:
                shared_splash_state["text"] = text
        except Exception:
            pass
        return json.dumps({"status": "ok"})

    def finish_splash_and_show_main(self):
        try:
            finish_splash_and_reveal_main()
        except Exception as e:
            print(f"[Splash] finish_splash_and_show_main error: {e}")
        return json.dumps({"status": "ok"})

    def minimize_to_tray(self):
        if getattr(self, '_window', None):
            try:
                self._window.hide()
            except Exception:
                pass
        return json.dumps({"status": "success"})

    def restore_from_tray(self):
        if getattr(self, '_window', None):
            try:
                self._window.show()
                self._window.restore()
            except Exception:
                pass
            bring_window_to_front("SceneryX")
        return json.dumps({"status": "success"})

    def generate_bug_report(self, payload_json="{}"):
        try:
            payload = json.loads(payload_json) if isinstance(payload_json, str) else (payload_json or {})
            desc = payload.get("description", "")
            cat = payload.get("category", "General")
            inc_screen = payload.get("include_screenshot", True)
            inc_logs = payload.get("include_logs", True)
            res = flight_bug_reporter.build_bug_report_package(desc, cat, inc_screen, inc_logs)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    def get_bug_reporter_status(self):
        try:
            res = flight_bug_reporter.get_bug_reporter_status()
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def preview_bug_report(self, payload_json="{}"):
        try:
            payload = json.loads(payload_json) if isinstance(payload_json, str) else (payload_json or {})
            desc = payload.get("description", "")
            cat = payload.get("category", "General")
            preview = flight_bug_reporter.get_diagnostic_preview(desc, cat)
            return json.dumps({"status": "ok", "preview": preview}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def open_crash_reports_folder(self):
        try:
            res = flight_bug_reporter.open_crash_reports_folder()
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def save_bug_reporter_privacy(self, payload_json="{}"):
        try:
            payload = json.loads(payload_json) if isinstance(payload_json, str) else (payload_json or {})
            auto_send = bool(payload.get("auto_send_crash_reports", True))
            telemetry = bool(payload.get("send_anonymous_telemetry", True))
            ok = flight_bug_reporter.save_privacy_settings(auto_send, telemetry)
            return json.dumps({"status": "ok" if ok else "error"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def simulate_test_bug(self, bug_type="key_error"):
        try:
            res = flight_bug_reporter.simulate_test_bug(bug_type)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def add_client_breadcrumb(self, action, label, metadata_json=None):
        try:
            meta = json.loads(metadata_json) if metadata_json and isinstance(metadata_json, str) else metadata_json
            flight_bug_reporter.add_breadcrumb(action, label, meta)
            return json.dumps({"status": "ok"})
        except Exception:
            return json.dumps({"status": "error"})

    def log_client_error(self, message, source="", lineno=0, colno=0, stack=""):
        try:
            flight_bug_reporter.log_event("JS_ERROR", f"{message} at {source}:{lineno}:{colno}", {"stack": stack})
            flight_bug_reporter.add_breadcrumb("JS_ERROR", f"{message} ({source}:{lineno})")
            return json.dumps({"status": "ok"})
        except Exception:
            return json.dumps({"status": "error"})

    def get_airports(self):
        settings = get_settings()
        disclaimer_accepted = settings.get("disclaimer_accepted", False)

        if not disclaimer_accepted:
            # First launch before Terms of Use accepted: don't auto-scan yet, return empty
            self._startup_delta = {"added": [], "removed": [], "total_changes": 0}
            return json.dumps([], ensure_ascii=False)

        # If already scanned during this startup session, return cached data without re-running delta
        if self._startup_scanned and self._startup_delta is not None and os.path.exists(OUTPUT_JSON_PATH):
            try:
                with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content and len(content) > 100:
                        return content
            except Exception:
                pass

        global AIRPORTS_CACHE
        auto_scan = settings.get("auto_scan_on_startup", True)
        if auto_scan:
            airports = run_scan()
            AIRPORTS_CACHE = airports
            self._startup_delta = compute_scan_delta(airports, update_snapshot=True)
            self._startup_scanned = True
            if os.path.exists(OUTPUT_JSON_PATH):
                try:
                    with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception:
                    pass
            return json.dumps(airports, separators=(',', ':'), ensure_ascii=False)

        if os.path.exists(OUTPUT_JSON_PATH):
            try:
                with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content and len(content) > 10:
                        self._startup_delta = {"added": [], "removed": [], "total_changes": 0}
                        self._startup_scanned = True
                        return content
            except Exception as e:
                print("Error reading cached installed_airports.json, performing fresh scan:", e)

        airports = run_scan()
        AIRPORTS_CACHE = airports
        self._startup_delta = compute_scan_delta(airports, update_snapshot=True)
        self._startup_scanned = True
        if os.path.exists(OUTPUT_JSON_PATH):
            try:
                with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                pass
        return json.dumps(airports, separators=(',', ':'), ensure_ascii=False)

    def initial_scan(self):
        """
        Runs the first-time scan right after the user accepts the Terms of Use.
        Builds the baseline library_snapshot.json and saves installed_airports.json.
        """
        airports = run_scan()
        current_snapshot = build_library_snapshot(airports)
        try:
            with open(SNAPSHOT_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(current_snapshot, f, separators=(',', ':'), ensure_ascii=False)
        except Exception as e:
            print("Error saving initial library snapshot:", e)
        self._startup_delta = {"added": [], "removed": [], "total_changes": 0}
        self._startup_scanned = True
        return json.dumps({"airports": airports, "delta": self._startup_delta}, separators=(',', ':'), ensure_ascii=False)

    def get_startup_delta(self):
        delta = getattr(self, '_startup_delta', None)
        if not delta or not isinstance(delta, dict):
            delta = {"added": [], "removed": [], "total_changes": 0}
        return json.dumps(delta, ensure_ascii=False)

    def get_world_airport_coords(self):
        try:
            if hasattr(Api, '_CACHED_WORLD_AIRPORT_COORDS') and Api._CACHED_WORLD_AIRPORT_COORDS is not None:
                return Api._CACHED_WORLD_AIRPORT_COORDS

            AIRPORTS_DB_CACHE, _, _ = load_airport_database()
            coords = {}
            for icao, ap in AIRPORTS_DB_CACHE.items():
                coords[icao] = {
                    'lat': ap.get('lat', 0.0),
                    'lon': ap.get('lon', 0.0),
                    'name': ap.get('name', ''),
                    'city': ap.get('city', ''),
                    'country': ap.get('country', ''),
                    'type': ap.get('type', 'airport')
                }
            if "EDDT" not in coords:
                coords["EDDT"] = {
                    'lat': 52.5597,
                    'lon': 13.2877,
                    'name': 'Berlin Tegel Airport',
                    'city': 'Berlin',
                    'country': 'Germany',
                    'type': 'large_airport'
                }
            Api._CACHED_WORLD_AIRPORT_COORDS = json.dumps(coords, separators=(',', ':'), ensure_ascii=False)
            return Api._CACHED_WORLD_AIRPORT_COORDS
        except Exception as e:
            print("Error returning world_airport_coords:", e)
            return json.dumps({})

    def get_airport_runways(self, icao):
        try:
            if not hasattr(Api, '_RUNWAYS_CACHE') or Api._RUNWAYS_CACHE is None:
                runways_path = get_resource_file_path("airport_runways.json")
                if os.path.exists(runways_path):
                    with open(runways_path, 'r', encoding='utf-8') as f:
                        Api._RUNWAYS_CACHE = json.load(f)
                else:
                    Api._RUNWAYS_CACHE = {}
            icao_clean = (icao or '').strip().upper()
            return json.dumps(Api._RUNWAYS_CACHE.get(icao_clean, []))
        except Exception as e:
            print("Error in get_airport_runways:", e)
            return json.dumps([])

    def get_world_airport(self, icao):
        """Returns on-demand synthesized metadata for any default MSFS procedural airport in the world."""
        try:
            from scanner import create_default_procedural_airport
            clean = (icao or '').strip().upper()
            if not clean:
                return json.dumps(None)
            ap = create_default_procedural_airport(clean)
            return json.dumps(ap, ensure_ascii=False)
        except Exception as e:
            print(f"Error in get_world_airport({icao}):", e)
            return json.dumps(None)

    def rescan(self):
        global AIRPORTS_CACHE
        airports = run_scan()
        AIRPORTS_CACHE = airports
        delta = compute_scan_delta(airports, update_snapshot=True)
        self._startup_delta = delta
        return json.dumps({"airports": airports, "delta": delta}, separators=(',', ':'), ensure_ascii=False)

    def fetch_simbrief(self, identifier):
        if IS_LITE:
            return json.dumps({"status": "locked", "is_lite": True, "message": "SimBrief Integration is only available in SceneryX Pro."})
        identifier = str(identifier).strip()
        if not identifier:
            return json.dumps({"status": "error", "message": "Identifier empty"})

        st = get_settings()
        stored_username = st.get('simbrief_username', '')
        stored_userid = st.get('simbrief_userid', '')

        known_map = st.get('simbrief_map', {})

        if identifier.isdigit():
            param_str = f"userid={identifier}"
            user_id = identifier
            username = stored_username if (stored_username and not stored_username.startswith('vamsys-')) else known_map.get(identifier, '')
        else:
            param_str = f"username={identifier}"
            username = identifier
            user_id = stored_userid or known_map.get(identifier.lower(), '')

        url = f"https://www.simbrief.com/api/xml.fetcher.php?{param_str}&json=1"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'SceneryX/1.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if not isinstance(data, dict) or 'origin' not in data or 'destination' not in data:
                    return json.dumps({"status": "error", "message": "No active flight plan found for this SimBrief account."})

                params = data.get('params', {})
                fetched_uid = str(params.get('user_id', '') or params.get('userid', ''))
                fetched_uname = str(params.get('username', '') or params.get('user_name', ''))
                if fetched_uid:
                    user_id = fetched_uid
                if fetched_uname:
                    username = fetched_uname

                if not username and user_id in known_map:
                    username = known_map[user_id]

                if username and user_id:
                    known_map[user_id] = username
                    known_map[username.lower()] = user_id
                    st['simbrief_map'] = known_map

                st['simbrief_username'] = username
                st['simbrief_userid'] = user_id
                save_settings(st)

                origin_icao = data.get('origin', {}).get('icao_code', '')
                origin_name = data.get('origin', {}).get('name', origin_icao)

                dest_icao = data.get('destination', {}).get('icao_code', '')
                dest_name = data.get('destination', {}).get('name', dest_icao)

                alternates = []
                alt_raw = data.get('alternate')
                if alt_raw:
                    if isinstance(alt_raw, list):
                        for item in alt_raw:
                            if isinstance(item, dict) and item.get('icao_code'):
                                alternates.append({
                                    'icao': item.get('icao_code').upper().strip(),
                                    'name': item.get('name', item.get('icao_code')),
                                    'lat': float(item.get('pos_lat')) if item.get('pos_lat') else None,
                                    'lon': float(item.get('pos_long')) if item.get('pos_long') else None
                                })
                    elif isinstance(alt_raw, dict) and alt_raw.get('icao_code'):
                        alternates.append({
                            'icao': alt_raw.get('icao_code').upper().strip(),
                            'name': alt_raw.get('name', alt_raw.get('icao_code')),
                            'lat': float(alt_raw.get('pos_lat')) if alt_raw.get('pos_lat') else None,
                            'lon': float(alt_raw.get('pos_long')) if alt_raw.get('pos_long') else None
                        })

                for alt_key in ['alternate_2', 'alternate_3', 'alternate_4']:
                    alt_data = data.get(alt_key)
                    if alt_data and isinstance(alt_data, dict) and alt_data.get('icao_code'):
                        alternates.append({
                            'icao': alt_data.get('icao_code').upper().strip(),
                            'name': alt_data.get('name', alt_data.get('icao_code')),
                            'lat': float(alt_data.get('pos_lat')) if alt_data.get('pos_lat') else None,
                            'lon': float(alt_data.get('pos_long')) if alt_data.get('pos_long') else None
                        })

                general = data.get('general', {})
                flight_num = f"{general.get('icao_airline', '')}{general.get('flight_number', '')}".strip()
                route = general.get('route', '')
                aircraft = data.get('aircraft', {}).get('name', '')

                all_flight_icaos = [origin_icao, dest_icao] + [a['icao'] for a in alternates]
                all_flight_icaos = list(dict.fromkeys([icao.upper() for icao in all_flight_icaos if icao]))

                flight_data = {
                    "origin": {
                        "icao": origin_icao,
                        "name": origin_name,
                        "lat": float(data.get('origin', {}).get('pos_lat', 0)) if data.get('origin', {}).get('pos_lat') else None,
                        "lon": float(data.get('origin', {}).get('pos_long', 0)) if data.get('origin', {}).get('pos_long') else None
                    },
                    "destination": {
                        "icao": dest_icao,
                        "name": dest_name,
                        "lat": float(data.get('destination', {}).get('pos_lat', 0)) if data.get('destination', {}).get('pos_lat') else None,
                        "lon": float(data.get('destination', {}).get('pos_long', 0)) if data.get('destination', {}).get('pos_long') else None
                    },
                    "alternates": alternates,
                    "flight_number": flight_num,
                    "aircraft": aircraft,
                    "route": route,
                    "flight_icaos": all_flight_icaos,
                    "fetched_at": time.time()
                }
                st['latest_simbrief_flight'] = flight_data
                save_settings(st)

                return json.dumps({
                    "status": "success",
                    "username": username,
                    "userid": user_id,
                    "flight": flight_data
                }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Error fetching SimBrief data: {str(e)}"})

    def toggle_airport_disabled(self, icao):
        try:
            icao_target = str(icao).strip().upper()
            if is_core_or_library_package(icao_target):
                return json.dumps({"status": "error", "message": "Protected package cannot be disabled."})
            target_xml_paths = get_existing_content_xml_paths()
            if not target_xml_paths:
                return json.dumps({"status": "error", "message": "Content.xml not found"})

            airports = run_scan()
            ap = next((a for a in airports if a['icao'] == icao_target), None)
            if not ap:
                return json.dumps({"status": "error", "message": f"Airport {icao_target} not found"})

            if ap.get('pricing_type') == 'Asobo':
                return json.dumps({"status": "error", "message": "Asobo base airports cannot be disabled."})

            curr_disabled = ap.get('is_disabled', False)
            new_active_val = 'UserDisabled' if not curr_disabled else 'Activated'

            import xml.etree.ElementTree as ET
            for content_xml_path in target_xml_paths:
                try:
                    tree = ET.parse(content_xml_path)
                    root = tree.getroot()
                    changed = False
                    for p in root.findall('Package'):
                        name = p.get('name', '')
                        clean = name[:-9] if name.endswith('.disabled') else name
                        p_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', clean.lower())

                        for src in ap.get('all_sources', []):
                            fn = src.get('folder_name', '').lower()
                            s_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', fn)
                            if p_norm == s_norm or p_norm in s_norm or s_norm in p_norm:
                                p.set('active', new_active_val)
                                changed = True

                    if changed:
                        tree.write(content_xml_path, encoding='utf-8', xml_declaration=True)
                except Exception as ex:
                    print(f"Error updating {content_xml_path}: {ex}")

            updated_airports = fast_update_airport_cache(icao_target, toggle_all=True)
            return json.dumps({
                "status": "success",
                "icao": icao_target,
                "is_disabled": not curr_disabled,
                "airports": updated_airports
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def reset_full_database(self):
        try:
            self.restore_all_sceneries(full_reset=True)

            st = get_settings()
            st['flight_mode'] = {'active': False, 'icaos': [], 'disabled_folders': []}
            save_settings(st)

            airports = run_scan()
            return json.dumps({
                "status": "success",
                "airports": airports
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_settings(self):
        try:
            return json.dumps(get_settings(), ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def exit_app(self, restore=False):
        try:
            if restore:
                self.restore_all_sceneries(full_reset=True)

            self._force_closing = True
            if getattr(self, '_tray_icon', None):
                try:
                    self._tray_icon.stop()
                except Exception:
                    pass
            import threading, os
            threading.Timer(0.05, lambda: os._exit(0)).start()
            return json.dumps({"status": "ok"})
        except Exception as e:
            import os
            os._exit(0)
            return json.dumps({"status": "error", "message": str(e)})

    def set_app_language(self, lang):
        try:
            norm = "fr" if str(lang or "").strip().lower().startswith("fr") else "en"
            st = get_settings()
            st["language"] = norm
            updated = save_settings(st)
            try:
                import flight_remote_server
                flight_remote_server.set_remote_panel_language(norm)
            except Exception:
                pass
            if hasattr(self, '_tray_icon') and self._tray_icon:
                try:
                    import pystray
                    show_lbl = 'Afficher SceneryX' if norm == 'fr' else 'Show SceneryX'
                    quit_lbl = 'Quitter' if norm == 'fr' else 'Quit'
                    self._tray_icon.menu = pystray.Menu(
                        pystray.MenuItem(show_lbl, getattr(self, '_on_tray_show', lambda: None), default=True),
                        pystray.MenuItem(quit_lbl, getattr(self, '_on_tray_quit', lambda: None))
                    )
                except Exception:
                    pass
            return json.dumps({"status": "ok", "language": norm, "settings": updated}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def save_settings(self, settings_json):
        try:
            data = json.loads(settings_json)
            updated = save_settings(data)
            norm = "fr" if str(updated.get("language", "en")).strip().lower().startswith("fr") else "en"
            try:
                import flight_remote_server
                flight_remote_server.set_remote_panel_language(norm)
            except Exception:
                pass
            if hasattr(self, '_tray_icon') and self._tray_icon:
                try:
                    import pystray
                    show_lbl = 'Afficher SceneryX' if norm == 'fr' else 'Show SceneryX'
                    quit_lbl = 'Quitter' if norm == 'fr' else 'Quit'
                    self._tray_icon.menu = pystray.Menu(
                        pystray.MenuItem(show_lbl, getattr(self, '_on_tray_show', lambda: None), default=True),
                        pystray.MenuItem(quit_lbl, getattr(self, '_on_tray_quit', lambda: None))
                    )
                except Exception as ex:
                    print(f"[Tray] Dynamic language update error: {ex}")
            return json.dumps({"status": "ok", "settings": updated}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_ratings(self):
        ratings = load_ratings()
        return json.dumps(ratings, ensure_ascii=False)

    def set_rating(self, icao, rating_val):
        try:
            r_float = float(rating_val)
            ratings = save_rating(icao, r_float)
            
            if os.path.exists(OUTPUT_JSON_PATH):
                with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                    airports = json.load(f)
                for ap in airports:
                    if ap['icao'] == icao:
                        ap['rating'] = r_float if r_float > 0 else 0
                compact_p = json.dumps(airports, separators=(',', ':'), ensure_ascii=False)
                with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
                    f.write(compact_p)
                local_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'installed_airports.json')
                if os.path.exists(local_json) and os.path.abspath(local_json) != os.path.abspath(OUTPUT_JSON_PATH):
                    try:
                        with open(local_json, 'w', encoding='utf-8') as f:
                            f.write(compact_p)
                    except Exception:
                        pass

            return json.dumps({"status": "ok", "ratings": ratings})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def set_custom_price(self, icao, price_val):
        try:
            p_float = float(price_val) if price_val is not None and str(price_val).strip() != '' else None
            save_custom_price(icao, p_float)
            airports = run_scan()
            return json.dumps({"status": "ok", "airports": airports}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def toggle_package(self, package_path, icao=None):
        try:
            if is_core_or_library_package(package_path):
                return json.dumps({"status": "error", "message": "Protected aircraft/livery/utility package cannot be modified."})
            content_xml_path = get_content_xml_path()
            pkg_name = os.path.basename(package_path)
            clean_pkg = pkg_name[:-9] if pkg_name.endswith('.disabled') else pkg_name
            p_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', clean_pkg.lower())

            is_enabled = True
            if os.path.exists(content_xml_path):
                import xml.etree.ElementTree as ET
                tree = ET.parse(content_xml_path)
                root = tree.getroot()
                changed = False
                for p in root.findall('Package'):
                    name = p.get('name', '')
                    clean = name[:-9] if name.endswith('.disabled') else name
                    s_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', clean.lower())
                    if clean.lower() == clean_pkg.lower() or p_norm == s_norm:
                        curr = p.get('active', 'Activated')
                        new_val = 'UserDisabled' if curr == 'Activated' else 'Activated'
                        p.set('active', new_val)
                        is_enabled = (new_val == 'Activated')
                        changed = True
                if changed:
                    tree.write(content_xml_path, encoding='utf-8', xml_declaration=True)

            target_path = package_path
            if not os.path.exists(target_path):
                settings = get_settings()
                scan_paths_cfg = settings.get("scan_paths", [])
                for cfg in scan_paths_cfg:
                    dp = cfg.get('path', '')
                    if not dp or not os.path.exists(dp):
                        continue
                    onestore = os.path.join(dp, 'OneStore')
                    dirs = [onestore, dp] if os.path.exists(onestore) else [dp]
                    cand_list = [pkg_name, clean_pkg + '.disabled', clean_pkg] if pkg_name.endswith('.disabled') else [pkg_name, clean_pkg, clean_pkg + '.disabled']
                    found = False
                    for d in dirs:
                        for candidate_name in cand_list:
                            cand = os.path.join(d, candidate_name)
                            if os.path.exists(cand):
                                target_path = cand
                                found = True
                                break
                        if found:
                            break
                    if found:
                        break

            def is_xml_match(clean_target, xml_pkg_name, target_icao=None):
                c1 = clean_target.lower()
                c2 = xml_pkg_name[:-9].lower() if xml_pkg_name.lower().endswith('.disabled') else xml_pkg_name.lower()
                if c1 == c2:
                    return True
                p1 = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', c1)
                p2 = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', c2)
                if p1 == p2:
                    return True
                if target_icao and target_icao.lower() in p1 and target_icao.lower() in p2:
                    if p1 in p2 or p2 in p1:
                        return True
                return False

            # Determine whether we are ENABLING or DISABLING
            is_currently_disabled = False

            if os.path.exists(content_xml_path):
                import xml.etree.ElementTree as ET
                tree = ET.parse(content_xml_path)
                root = tree.getroot()
                for p in root.findall('Package'):
                    name = p.get('name', '')
                    if is_xml_match(clean_pkg, name, icao):
                        if p.get('active') == 'UserDisabled' or name.lower().endswith('.disabled'):
                            is_currently_disabled = True
                            break

            if os.path.exists(target_path):
                if target_path.endswith('.disabled') or os.path.exists(os.path.join(target_path, 'manifest.json.disabled')):
                    is_currently_disabled = True

            should_enable = is_currently_disabled

            # If turning ON target package, find all other packages for this ICAO to disable them (Mutual Exclusion)
            other_packages_to_disable = []
            if should_enable and icao:
                scanned_airports = run_scan()
                ap_obj = next((a for a in scanned_airports if a['icao'].upper() == icao.upper()), None)
                if ap_obj and ap_obj.get('all_sources'):
                    for src in ap_obj['all_sources']:
                        fn = src.get('folder_name', '')
                        fn_clean = fn[:-9] if fn.endswith('.disabled') else fn
                        if fn_clean.lower() != clean_pkg.lower():
                            pkg_p = src.get('package_path', '')
                            other_packages_to_disable.append((fn_clean, pkg_p))

            # 1. Update Content.xml for target package AND other conflicting packages for this ICAO
            if os.path.exists(content_xml_path):
                import xml.etree.ElementTree as ET
                tree = ET.parse(content_xml_path)
                root = tree.getroot()
                changed = False
                seen_packages = set()
                to_remove = []

                for p in list(root.findall('Package')):
                    name = p.get('name', '')
                    clean = name[:-9] if name.lower().endswith('.disabled') else name
                    p.set('name', clean)

                    if clean.lower() in seen_packages:
                        to_remove.append(p)
                        changed = True
                        continue
                    seen_packages.add(clean.lower())
                    
                    if is_xml_match(clean_pkg, name, icao):
                        new_val = 'Activated' if should_enable else 'UserDisabled'
                        p.set('active', new_val)
                        changed = True
                    elif should_enable and icao and icao.lower() in clean.lower():
                        p.set('active', 'UserDisabled')
                        changed = True

                for p in to_remove:
                    root.remove(p)

                # If target or other packages for this ICAO weren't in Content.xml, add them
                if clean_pkg.lower() not in seen_packages:
                    new_p = ET.SubElement(root, 'Package')
                    new_p.set('name', clean_pkg)
                    new_p.set('active', 'Activated' if should_enable else 'UserDisabled')
                    seen_packages.add(clean_pkg.lower())
                    changed = True

                for fn_other, p_other in other_packages_to_disable:
                    if fn_other.lower() not in seen_packages:
                        new_p = ET.SubElement(root, 'Package')
                        new_p.set('name', fn_other)
                        new_p.set('active', 'UserDisabled')
                        seen_packages.add(fn_other.lower())
                        changed = True

                if changed:
                    tree.write(content_xml_path, encoding='utf-8', xml_declaration=True)

            # 2. Update physical disk files for target package AND other conflicting packages
            if should_enable:
                new_path = enable_physical_package(target_path)
                for fn_other, p_other in other_packages_to_disable:
                    disable_physical_package(p_other)
            else:
                new_path = disable_physical_package(target_path)

            airports = run_scan()
            sync_library_snapshot(airports)
            return json.dumps({"status": "ok", "enabled": should_enable, "new_path": new_path, "airports": airports}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def disable_single_airport(self, icao):
        try:
            if not icao:
                return json.dumps({"status": "error", "message": "No ICAO provided"})
            if is_core_or_library_package(icao):
                return json.dumps({"status": "error", "message": "Protected package cannot be disabled."})
            
            target_xml_paths = get_existing_content_xml_paths()

            with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                scanned_airports = json.load(f)
            ap_obj = next((a for a in scanned_airports if a['icao'].upper() == icao.upper()), None)

            import xml.etree.ElementTree as ET
            for content_xml_path in target_xml_paths:
                try:
                    tree = ET.parse(content_xml_path)
                    root = tree.getroot()
                    changed = False
                    seen_dis = set()
                    for p in root.findall('Package'):
                        name = p.get('name', '')
                        clean = name[:-9] if name.lower().endswith('.disabled') else name
                        p.set('name', clean)
                        seen_dis.add(clean.lower())
                        if icao.lower() in clean.lower():
                            p.set('active', 'UserDisabled')
                            changed = True

                    if ap_obj and ap_obj.get('all_sources'):
                        for src in ap_obj['all_sources']:
                            fn = src.get('folder_name', '')
                            fn_clean = fn[:-9] if fn.lower().endswith('.disabled') else fn
                            if fn_clean.lower() not in seen_dis:
                                new_p = ET.SubElement(root, 'Package')
                                new_p.set('name', fn_clean)
                                new_p.set('active', 'UserDisabled')
                                seen_dis.add(fn_clean.lower())
                                changed = True

                    if changed:
                        tree.write(content_xml_path, encoding='utf-8', xml_declaration=True)
                except Exception as ex:
                    print(f"Error updating {content_xml_path}: {ex}")

            if ap_obj and ap_obj.get('all_sources'):
                for src in ap_obj['all_sources']:
                    pkg_p = src.get('package_path', '')
                    set_package_state_for_icao(pkg_p, icao, should_enable=False)

            airports = fast_update_airport_cache(icao, toggle_all=True)
            return json.dumps({"status": "ok", "airports": airports}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def select_scenery_option(self, icao, target_folder_name):
        try:
            if not icao or not target_folder_name:
                return json.dumps({"status": "error", "message": "Missing arguments"})

            target_xml_paths = get_existing_content_xml_paths()

            target_raw_clean = target_folder_name[:-9] if target_folder_name.lower().endswith('.disabled') else target_folder_name
            target_is_path = ('\\' in target_raw_clean or '/' in target_raw_clean)
            target_clean = os.path.basename(target_raw_clean) if target_is_path else target_raw_clean
            target_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', target_clean.lower())

            global AIRPORTS_CACHE
            if AIRPORTS_CACHE is None:
                if os.path.exists(OUTPUT_JSON_PATH):
                    with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                        AIRPORTS_CACHE = json.load(f)
                else:
                    AIRPORTS_CACHE = run_scan()
            scanned_airports = AIRPORTS_CACHE
            ap_obj = next((a for a in scanned_airports if a['icao'].upper() == icao.upper()), None)

            # Build set of package names belonging to THIS specific airport
            airport_pkg_names = set()
            airport_pkg_norms = set()
            if ap_obj and ap_obj.get('all_sources'):
                for src in ap_obj['all_sources']:
                    fn = src.get('folder_name', '')
                    fn_c = fn[:-9] if fn.lower().endswith('.disabled') else fn
                    fn_c_lower = fn_c.lower()
                    airport_pkg_names.add(fn_c_lower)
                    fn_n = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', fn_c_lower)
                    airport_pkg_norms.add(fn_n)

            import xml.etree.ElementTree as ET
            for content_xml_path in target_xml_paths:
                try:
                    tree = ET.parse(content_xml_path)
                    root = tree.getroot()
                    changed = False
                    seen = set()
                    seen_norms = set()
                    to_remove = []

                    for p in list(root.findall('Package')):
                        name = p.get('name', '')
                        clean = name[:-9] if name.lower().endswith('.disabled') else name
                        clean_lower = clean.lower()
                        clean_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', clean_lower)
                        p.set('name', clean)

                        if is_core_or_library_package(clean):
                            continue

                        if clean_lower in seen:
                            to_remove.append(p)
                            changed = True
                            continue
                        seen.add(clean_lower)
                        seen_norms.add(clean_norm)

                        # Only update package if it belongs to this airport
                        is_pkg_for_icao = (clean_lower in airport_pkg_names) or (clean_norm in airport_pkg_norms) or (icao.lower() in clean_lower)

                        if is_pkg_for_icao:
                            is_target = (target_clean != 'DEFAULT') and (
                                clean_lower == target_clean.lower() 
                                or clean_norm == target_norm
                                or ((clean_lower.startswith('fs20-asobo-') or clean_lower.startswith('fs24-asobo-') or clean_lower.startswith('fs20-microsoft-') or clean_lower.startswith('fs24-microsoft-')) and ('asobo' in target_clean.lower() or 'microsoft' in target_clean.lower()))
                            )
                            if is_target:
                                p.set('active', 'Activated')
                            else:
                                p.set('active', 'UserDisabled')
                            changed = True

                    for p in to_remove:
                        root.remove(p)

                    # Ensure all sources for this airport (including streamed/Asobo) are represented in Content.xml
                    if ap_obj and ap_obj.get('all_sources'):
                        for src in ap_obj['all_sources']:
                            if src.get('is_fix_patch') or src.get('is_addon'):
                                continue
                            fn = src.get('folder_name', '')
                            fn_clean = fn[:-9] if fn.lower().endswith('.disabled') else fn
                            fn_clean_lower = fn_clean.lower()
                            fn_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', fn_clean_lower)

                            is_target = (target_clean != 'DEFAULT') and (
                                fn_clean_lower == target_clean.lower() 
                                or fn_norm == target_norm
                                or (src.get('is_asobo_official') and ('asobo' in target_clean.lower() or 'microsoft' in target_clean.lower()))
                            )

                            if fn_clean_lower not in seen and fn_norm not in seen_norms:
                                new_p = ET.SubElement(root, 'Package')
                                new_p.set('name', fn_clean)
                                new_p.set('active', 'Activated' if is_target else 'UserDisabled')
                                seen.add(fn_clean_lower)
                                seen_norms.add(fn_norm)
                                changed = True

                    if changed:
                        tree.write(content_xml_path, encoding='utf-8', xml_declaration=True)
                except Exception as ex:
                    print(f"Error updating {content_xml_path}: {ex}")

            if ap_obj and ap_obj.get('all_sources'):
                for src in ap_obj['all_sources']:
                    if src.get('is_fix_patch') or src.get('is_addon'):
                        continue
                    fn = src.get('folder_name', '')
                    pkg_p = src.get('package_path', '')
                    clean_pkg_p = pkg_p[:-9] if pkg_p and pkg_p.lower().endswith('.disabled') else pkg_p
                    fn_clean = fn[:-9] if fn.lower().endswith('.disabled') else fn
                    fn_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', fn_clean.lower())

                    if target_clean == 'DEFAULT':
                        is_target = False
                    elif target_is_path and clean_pkg_p:
                        is_target = (os.path.normcase(os.path.abspath(clean_pkg_p)) == os.path.normcase(os.path.abspath(target_raw_clean)))
                    else:
                        is_target = (
                            fn_clean.lower() == target_clean.lower() 
                            or fn_norm == target_norm
                            or (src.get('is_asobo_official') and ('asobo' in target_clean.lower() or 'microsoft' in target_clean.lower()))
                        )
                    if is_target:
                        set_package_state_for_icao(pkg_p, icao, should_enable=True)
                    else:
                        set_package_state_for_icao(pkg_p, icao, should_enable=False)

            airports = fast_update_airport_cache(icao, target_pkg_name=(target_raw_clean if target_clean != 'DEFAULT' else 'DEFAULT'))
            target_ap = next((a for a in airports if a['icao'].upper() == icao.upper()), None)
            return json.dumps({"status": "ok", "updated_airport": target_ap}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def apply_scenery_config(self, icao, target_folder_name="", fixes_json="{}"):
        try:
            if not icao:
                return json.dumps({"status": "error", "message": "No ICAO provided"})

            fixes_dict = {}
            if fixes_json:
                try:
                    fixes_dict = json.loads(fixes_json)
                except Exception:
                    fixes_dict = {}

            target_xml_paths = get_existing_content_xml_paths()
            target_raw_clean = ""
            target_is_path = False
            target_clean = ""
            target_norm = ""
            if target_folder_name:
                target_raw_clean = target_folder_name[:-9] if target_folder_name.lower().endswith('.disabled') else target_folder_name
                target_is_path = ('\\' in target_raw_clean or '/' in target_raw_clean)
                target_clean = os.path.basename(target_raw_clean) if target_is_path else target_raw_clean
                target_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', target_clean.lower())

            global AIRPORTS_CACHE
            if AIRPORTS_CACHE is None:
                if os.path.exists(OUTPUT_JSON_PATH):
                    with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                        AIRPORTS_CACHE = json.load(f)
                else:
                    AIRPORTS_CACHE = run_scan()
            scanned_airports = AIRPORTS_CACHE
            ap_obj = next((a for a in scanned_airports if a['icao'].upper() == icao.upper()), None)

            # 1. Update Content.xml if needed
            import xml.etree.ElementTree as ET
            for content_xml_path in target_xml_paths:
                try:
                    tree = ET.parse(content_xml_path)
                    root = tree.getroot()
                    changed = False
                    seen = set()
                    seen_norms = set()
                    to_remove = []

                    airport_pkg_names = set()
                    airport_pkg_norms = set()
                    if ap_obj and ap_obj.get('all_sources'):
                        for src in ap_obj['all_sources']:
                            fn = src.get('folder_name', '')
                            fn_c = fn[:-9] if fn.lower().endswith('.disabled') else fn
                            fn_c_lower = fn_c.lower()
                            airport_pkg_names.add(fn_c_lower)
                            fn_n = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', fn_c_lower)
                            airport_pkg_norms.add(fn_n)

                    for p in list(root.findall('Package')):
                        name = p.get('name', '')
                        clean = name[:-9] if name.lower().endswith('.disabled') else name
                        clean_lower = clean.lower()
                        clean_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', clean_lower)
                        p.set('name', clean)

                        if is_core_or_library_package(clean):
                            continue

                        if clean_lower in seen:
                            to_remove.append(p)
                            changed = True
                            continue
                        seen.add(clean_lower)
                        seen_norms.add(clean_norm)

                        # Check if this package is one of the fixes being updated
                        matched_fix = None
                        for fix_name, fix_enabled in fixes_dict.items():
                            c_fix = fix_name[:-9] if fix_name.lower().endswith('.disabled') else fix_name
                            if clean_lower == c_fix.lower() or c_fix.lower() in clean_lower or clean_lower in c_fix.lower():
                                matched_fix = (c_fix, fix_enabled)
                                break

                        if matched_fix is not None:
                            p.set('active', 'Activated' if matched_fix[1] else 'UserDisabled')
                            changed = True
                            continue

                        # If variant is specified, update main scenery packages belonging to this airport
                        if target_clean:
                            is_pkg_for_icao = (clean_lower in airport_pkg_names) or (clean_norm in airport_pkg_norms) or (icao.lower() in clean_lower)
                            if is_pkg_for_icao:
                                is_target = (target_clean != 'DEFAULT') and (
                                    clean_lower == target_clean.lower() 
                                    or clean_norm == target_norm
                                    or ((clean_lower.startswith('fs20-asobo-') or clean_lower.startswith('fs24-asobo-') or clean_lower.startswith('fs20-microsoft-') or clean_lower.startswith('fs24-microsoft-')) and ('asobo' in target_clean.lower() or 'microsoft' in target_clean.lower()))
                                )
                                p.set('active', 'Activated' if is_target else 'UserDisabled')
                                changed = True

                    for p in to_remove:
                        root.remove(p)

                    if target_clean and ap_obj and ap_obj.get('all_sources'):
                        for src in ap_obj['all_sources']:
                            if src.get('is_fix_patch') or src.get('is_addon'):
                                continue
                            fn = src.get('folder_name', '')
                            fn_clean = fn[:-9] if fn.lower().endswith('.disabled') else fn
                            fn_clean_lower = fn_clean.lower()
                            fn_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', fn_clean_lower)

                            is_target = (target_clean != 'DEFAULT') and (
                                fn_clean_lower == target_clean.lower() 
                                or fn_norm == target_norm
                                or (src.get('is_asobo_official') and ('asobo' in target_clean.lower() or 'microsoft' in target_clean.lower()))
                            )

                            if fn_clean_lower not in seen and fn_norm not in seen_norms:
                                new_p = ET.SubElement(root, 'Package')
                                new_p.set('name', fn_clean)
                                new_p.set('active', 'Activated' if is_target else 'UserDisabled')
                                seen.add(fn_clean_lower)
                                seen_norms.add(fn_norm)
                                changed = True

                    if changed:
                        tree.write(content_xml_path, encoding='utf-8', xml_declaration=True)
                except Exception as ex:
                    print(f"Error updating {content_xml_path}: {ex}")

            # 2. Physical package enable/disable for Main Sceneries
            if target_clean and ap_obj and ap_obj.get('all_sources'):
                for src in ap_obj['all_sources']:
                    if src.get('is_fix_patch') or src.get('is_addon'):
                        continue
                    fn = src.get('folder_name', '')
                    pkg_p = src.get('package_path', '')
                    clean_pkg_p = pkg_p[:-9] if pkg_p and pkg_p.lower().endswith('.disabled') else pkg_p
                    fn_clean = fn[:-9] if fn.lower().endswith('.disabled') else fn
                    fn_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', fn_clean.lower())

                    if target_clean == 'DEFAULT':
                        is_target = False
                    elif target_is_path and clean_pkg_p:
                        is_target = (os.path.normcase(os.path.abspath(clean_pkg_p)) == os.path.normcase(os.path.abspath(target_raw_clean)))
                    else:
                        is_target = (
                            fn_clean.lower() == target_clean.lower() 
                            or fn_norm == target_norm
                            or (src.get('is_asobo_official') and ('asobo' in target_clean.lower() or 'microsoft' in target_clean.lower()))
                        )
                    if is_target:
                        set_package_state_for_icao(pkg_p, icao, should_enable=True)
                    else:
                        set_package_state_for_icao(pkg_p, icao, should_enable=False)

            # 3. Physical package enable/disable for Fixes & Overlays
            if fixes_dict and ap_obj and ap_obj.get('all_sources'):
                for fix_name, fix_enabled in fixes_dict.items():
                    c_fix = fix_name[:-9] if fix_name.lower().endswith('.disabled') else fix_name
                    for src in ap_obj['all_sources']:
                        fn = src.get('folder_name', '')
                        fn_clean = fn[:-9] if fn.lower().endswith('.disabled') else fn
                        if fn_clean.lower() == c_fix.lower() or c_fix.lower() in fn_clean.lower() or fn_clean.lower() in c_fix.lower():
                            pkg_p = src.get('package_path', '')
                            if fix_enabled:
                                enable_physical_package(pkg_p)
                            else:
                                disable_physical_package(pkg_p)
                            break

            # 4. Update cache
            airports = fast_update_airport_cache(icao, target_pkg_name=(target_raw_clean if target_clean else None))
            target_ap = next((a for a in airports if a['icao'].upper() == icao.upper()), None)

            # 5. Synchronize fix states in target_ap
            if target_ap and fixes_dict:
                for fix_name, fix_enabled in fixes_dict.items():
                    c_fix = fix_name[:-9] if fix_name.lower().endswith('.disabled') else fix_name
                    for s in target_ap.get('all_sources', []):
                        fn = s.get('folder_name', '')
                        fn_clean = fn[:-9] if fn.lower().endswith('.disabled') else fn
                        if fn_clean.lower() == c_fix.lower() or c_fix.lower() in fn_clean.lower() or fn_clean.lower() in c_fix.lower():
                            s['is_disabled'] = not fix_enabled
                            s['folder_name'] = fn_clean if fix_enabled else (fn_clean + '.disabled')
                            p = s.get('package_path', '')
                            clean_p = p[:-9] if p and p.endswith('.disabled') else p
                            if clean_p:
                                s['package_path'] = clean_p if fix_enabled else (clean_p + '.disabled')

            if os.path.exists(OUTPUT_JSON_PATH):
                try:
                    compact_p = json.dumps(airports, separators=(',', ':'), ensure_ascii=False)
                    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
                        f.write(compact_p)
                    local_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'installed_airports.json')
                    if os.path.exists(local_json) and os.path.abspath(local_json) != os.path.abspath(OUTPUT_JSON_PATH):
                        try:
                            with open(local_json, 'w', encoding='utf-8') as f:
                                f.write(compact_p)
                        except Exception:
                            pass
                except Exception:
                    pass

            return json.dumps({"status": "ok", "updated_airport": target_ap}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def toggle_fix_patch(self, path, icao):
        try:
            if not path:
                return json.dumps({"status": "error", "message": "No path provided"})
            if is_core_or_library_package(path):
                return json.dumps({"status": "error", "message": "Protected package cannot be modified."})

            target_xml_paths = get_existing_content_xml_paths()
            
            clean_name = os.path.basename(path)
            if clean_name.lower().endswith('.disabled'):
                clean_name = clean_name[:-9]

            target_path = path
            if not os.path.isabs(target_path) or not os.path.exists(target_path):
                if os.path.exists(OUTPUT_JSON_PATH):
                    with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                        scanned_airports = json.load(f)
                else:
                    scanned_airports = run_scan()
                found_path = None
                for ap in scanned_airports:
                    for src in ap.get('all_sources', []):
                        fn = src.get('folder_name', '')
                        pkg_p = src.get('package_path', '')
                        if fn.lower() == clean_name.lower() or fn.lower() == (clean_name + '.disabled').lower():
                            if pkg_p and os.path.exists(pkg_p):
                                found_path = pkg_p
                                break
                    if found_path:
                        break
                if found_path:
                    target_path = found_path

            is_currently_disabled = target_path.endswith('.disabled') or os.path.exists(os.path.join(target_path, 'manifest.json.disabled')) or os.path.exists(target_path + '.disabled')
            should_enable = is_currently_disabled

            import xml.etree.ElementTree as ET
            for content_xml_path in target_xml_paths:
                try:
                    tree = ET.parse(content_xml_path)
                    root = tree.getroot()
                    changed = False
                    for p in root.findall('Package'):
                        name = p.get('name', '')
                        clean = name[:-9] if name.lower().endswith('.disabled') else name
                        p.set('name', clean)
                        if clean.lower() == clean_name.lower() or clean_name.lower() in clean.lower() or clean.lower() in clean_name.lower():
                            p.set('active', 'Activated' if should_enable else 'UserDisabled')
                            changed = True
                    if changed:
                        tree.write(content_xml_path, encoding='utf-8', xml_declaration=True)
                except Exception as ex:
                    print(f"Error updating {content_xml_path}: {ex}")

            if should_enable:
                enable_physical_package(target_path)
            else:
                disable_physical_package(target_path)

            airports = fast_update_airport_cache(icao, fix_path_toggled=clean_name, fix_enabled=should_enable) if icao else run_scan()
            target_ap = next((a for a in airports if a['icao'].upper() == (icao or '').upper()), None) if icao else None
            return json.dumps({"status": "ok", "enabled": should_enable, "updated_airport": target_ap}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def optimize_flight(self, keep_icaos_json):
        if IS_LITE:
            return json.dumps({"status": "locked", "is_lite": True, "message": "Flight Plan Optimizer is only available in SceneryX Pro."})
        return self.optimize_flight_mode(keep_icaos_json)

    def optimize_flight_mode(self, keep_icaos_json):
        if IS_LITE:
            return json.dumps({"status": "locked", "is_lite": True, "message": "Flight Plan Optimizer is only available in SceneryX Pro."})
        try:
            raw_param = json.loads(keep_icaos_json)
            dep_icao = ''
            arr_icao = ''
            profile = 'CORRIDOR'
            alternates = []
            simbrief_flight = None

            if isinstance(raw_param, dict):
                keep_icaos = set(raw_param.get('keep_icaos', []))
                dep_icao = raw_param.get('dep_icao', '')
                arr_icao = raw_param.get('arr_icao', '')
                profile = raw_param.get('profile', 'CORRIDOR')
                alternates = raw_param.get('alternates', [])
                simbrief_flight = raw_param.get('simbrief_flight', None)
            else:
                keep_icaos = set(raw_param)

            settings = get_settings()
            scan_paths_cfg = settings.get("scan_paths", [])

            all_airports = run_scan()
            folder_to_icaos, third_party_airport_pkgs = get_folder_to_icaos_map(all_airports)

            # Record all pre-existing disabled packages across all scan folders and Content.xml to guarantee lossless rollback
            pre_existing_disabled = []
            for cfg in scan_paths_cfg:
                dp = cfg.get('path', '')
                if not os.path.exists(dp):
                    continue
                onestore = os.path.join(dp, 'OneStore')
                target_dirs = [onestore] if os.path.exists(onestore) else [dp]
                for td in target_dirs:
                    if not os.path.exists(td):
                        continue
                    try:
                        for item in os.listdir(td):
                            if item.endswith('.disabled'):
                                pre_existing_disabled.append(item)
                    except Exception:
                        pass

            pre_existing_disabled_xml = []
            for xml_path in get_content_xml_paths():
                if os.path.exists(xml_path):
                    try:
                        import xml.etree.ElementTree as ET
                        tree = ET.parse(xml_path)
                        for elem in tree.getroot().findall('Package'):
                            if elem.get('active') == 'UserDisabled':
                                pre_existing_disabled_xml.append(elem.get('name', ''))
                    except Exception:
                        pass

            enabled_count = 0
            disabled_count = 0
            disabled_by_flight_mode = []
            disabled_bundle_bgls = []

            for cfg in scan_paths_cfg:
                dp = cfg.get('path', '')
                if not os.path.exists(dp):
                    continue

                dp_lower = dp.lower()
                is_community = 'community' in dp_lower

                onestore = os.path.join(dp, 'OneStore')
                target_dirs = [onestore] if os.path.exists(onestore) else [dp]

                for td in target_dirs:
                    if not os.path.exists(td):
                        continue
                    try:
                        for item in os.listdir(td):
                            item_p = os.path.join(td, item)
                            if not os.path.isdir(item_p) or item == 'OneStore':
                                continue

                            item_lower = item.lower()
                            # Never rename official Asobo/Microsoft packages physically
                            if any(k in item_lower for k in ['asobo-', 'microsoft-', 'official', 'streamed', 'worldupdate', 'cityupdate']):
                                continue

                            item_clean = item[:-9] if item.endswith('.disabled') else item
                            item_clean_lower = item_clean.lower()
                            item_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', item_clean_lower)

                            # STRICT IMMUNITY GUARD: Never touch aircraft, liveries, tools or core utilities
                            if is_core_or_library_package(item_p) or is_core_or_library_package(item_clean):
                                continue

                            pkg_icaos = folder_to_icaos.get(item_clean_lower) or folder_to_icaos.get(item_norm)
                            if not pkg_icaos:
                                bundle_icaos = SPECIAL_BUNDLE_MAP.get(item_clean_lower) or SPECIAL_BUNDLE_MAP.get(item_norm)
                                if not bundle_icaos:
                                    for bk, bv in SPECIAL_BUNDLE_MAP.items():
                                        if bk in item_clean_lower or bk in item_norm:
                                            bundle_icaos = bv
                                            break
                                if bundle_icaos:
                                    pkg_icaos = set(bundle_icaos)

                            # Known Handcrafted / Payware Airport name patterns (Gatwick, Frankfurt, Vancouver, etc.)
                            if not pkg_icaos:
                                for t_icao, t_words in [
                                    ('EGKK', ['gatwick', 'egkk']),
                                    ('EDDF', ['frankfurt', 'eddf']),
                                    ('CYVR', ['vancouver', 'cyvr']),
                                    ('LFBD', ['bordeaux', 'merignac', 'lfbd']),
                                    ('LFML', ['marseille', 'lfml']),
                                    ('LFKB', ['bastia', 'lfkb'])
                                ]:
                                    if any(w in item_clean_lower for w in t_words):
                                        pkg_icaos = {t_icao}
                                        break

                            # ONLY process packages that actually represent airport sceneries!
                            # NEVER rename liveries, aircraft, tools, GSX, or utilities!
                            is_airport_pkg = (
                                bool(pkg_icaos)
                                or (item_clean_lower in third_party_airport_pkgs)
                                or (item_norm in third_party_airport_pkgs)
                                or (item_clean_lower in SPECIAL_BUNDLE_MAP)
                                or (item_norm in SPECIAL_BUNDLE_MAP)
                                or any(k in item_clean_lower for k in ['francevfr', 'fvfr', '-airport-', '_airport_', '-airfield-', '-aerodrome-'])
                            )
                            if not is_airport_pkg:
                                continue

                            is_keep = any(k in keep_icaos for k in (pkg_icaos or []))

                            if is_community:
                                try:
                                    # Never re-enable packages that were already disabled prior to flight mode
                                    if not is_keep and not item.endswith('.disabled'):
                                        dis_p = disable_physical_package(item_p)
                                        if dis_p and dis_p.endswith('.disabled'):
                                            disabled_count += 1
                                            disabled_by_flight_mode.append(item)
                                    elif is_keep and pkg_icaos and len(pkg_icaos) > 1 and not item.endswith('.disabled'):
                                        # Multi-airport bundle (e.g. France VFR sevfrairports)
                                        # Dissociate non-kept ICAOs inside this bundle by disabling their specific BGLs!
                                        for b_icao in pkg_icaos:
                                            if b_icao not in keep_icaos:
                                                try:
                                                    set_package_state_for_icao(item_p, b_icao, should_enable=False)
                                                    disabled_bundle_bgls.append((item_p, b_icao))
                                                    disabled_count += 1
                                                except Exception as bgl_err:
                                                    print(f"Error dissociating bundle airport {b_icao} in {item}: {bgl_err}")
                                except Exception as rename_err:
                                    print(f"Skipping package state change for {item}: {rename_err}")
                    except Exception as e:
                        print(f"Error processing {td} during flight optimizer:", e)

            # Update MSFS Native Content.xml (UserDisabled / Activated)
            disabled_xml_pkgs, added_xml_pkgs = update_msfs_content_xml(
                keep_icaos=keep_icaos,
                restore_flight_mode=False,
                folder_to_icaos=folder_to_icaos,
                third_party_airport_pkgs=third_party_airport_pkgs,
                all_airports=all_airports
            )

            # Sanitize MSFS Content.xml unconditionally (forces all aircraft, liveries and utilities to Activated)
            sanitize_msfs_content_xml()

            # Merge with existing state if flight mode was already partially active
            existing_flight_cfg = settings.get('flight_mode', {})
            existing_folders = set(existing_flight_cfg.get('disabled_folders', []))
            existing_xml = set(existing_flight_cfg.get('disabled_xml_packages', []))
            existing_added = set(existing_flight_cfg.get('added_xml_packages', []))
            existing_bundle_bgls = existing_flight_cfg.get('disabled_bundle_bgls', [])

            all_disabled_folders = list(existing_folders.union(disabled_by_flight_mode))
            all_disabled_xml = list(existing_xml.union(disabled_xml_pkgs))
            all_added_xml = list(existing_added.union(added_xml_pkgs))
            all_bundle_bgls = existing_bundle_bgls + [list(pair) for pair in disabled_bundle_bgls if list(pair) not in existing_bundle_bgls]

            total_disabled_count = len(all_disabled_folders) + len(all_disabled_xml) + len(all_added_xml) + len(all_bundle_bgls)

            # Persist atomic isolation snapshot to disk
            snapshot_data = {
                "created_at": datetime.now().isoformat(),
                "route": {
                    "dep_icao": dep_icao,
                    "arr_icao": arr_icao,
                    "profile": profile,
                    "alternates": alternates,
                    "keep_icaos": list(keep_icaos)
                },
                "disabled_folders": all_disabled_folders,
                "disabled_xml_packages": all_disabled_xml,
                "added_xml_packages": all_added_xml,
                "disabled_bundle_bgls": all_bundle_bgls,
                "pre_existing_disabled_folders": pre_existing_disabled,
                "pre_existing_disabled_xml": pre_existing_disabled_xml
            }
            save_isolation_snapshot(snapshot_data)

            settings['flight_mode'] = {
                'active': True,
                'disabled_count': total_disabled_count,
                'icaos': list(keep_icaos),
                'dep_icao': dep_icao,
                'arr_icao': arr_icao,
                'profile': profile,
                'alternates': alternates,
                'simbrief_flight': simbrief_flight,
                'disabled_folders': all_disabled_folders,
                'disabled_xml_packages': all_disabled_xml,
                'added_xml_packages': all_added_xml,
                'disabled_bundle_bgls': all_bundle_bgls
            }
            save_settings(settings)

            airports = run_scan()
            return json.dumps({
                "status": "ok",
                "enabled_count": enabled_count,
                "disabled_count": total_disabled_count,
                "airports": airports
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def restore_all_flight_sceneries(self):
        """1-Click Flight Corridor Reversal: Restores all sceneries disabled by flight mode."""
        return self.restore_all_sceneries(full_reset=True)

    def restore_all_sceneries(self, full_reset=True):
        """
        Lossless 1-Click Scenery Restoration Engine:
        - Re-enables all disabled scenery packages across all scan folders (excluding known secondary conflict packages).
        - 100% aircraft, livery, and utility immunity is enforced in Content.xml, snapshot is cleared, and settings updated.
        """
        try:
            settings = get_settings()
            scan_paths_cfg = settings.get("scan_paths", [])
            re_enabled_count = 0

            snapshot = load_isolation_snapshot()
            flight_mode_cfg = settings.get('flight_mode', {})

            flight_disabled_folders = set()
            flight_disabled_xml = set()
            flight_added_xml = set()
            pre_existing_folders = set()
            pre_existing_xml = set()
            disabled_bundle_bgls = []

            if snapshot and isinstance(snapshot, dict):
                flight_disabled_folders.update(snapshot.get('disabled_folders', []))
                flight_disabled_xml.update(snapshot.get('disabled_xml_packages', []))
                flight_added_xml.update(snapshot.get('added_xml_packages', []))
                pre_existing_folders.update(snapshot.get('pre_existing_disabled_folders', []))
                pre_existing_xml.update(snapshot.get('pre_existing_disabled_xml', []))
                disabled_bundle_bgls.extend(snapshot.get('disabled_bundle_bgls', []))

            if isinstance(flight_mode_cfg, dict):
                flight_disabled_folders.update(flight_mode_cfg.get('disabled_folders', []))
                flight_disabled_xml.update(flight_mode_cfg.get('disabled_xml_packages', []))
                flight_added_xml.update(flight_mode_cfg.get('added_xml_packages', []))
                for pair in flight_mode_cfg.get('disabled_bundle_bgls', []):
                    if pair not in disabled_bundle_bgls:
                        disabled_bundle_bgls.append(pair)

            flight_disabled_folders_lower = {f.lower() for f in flight_disabled_folders}
            pre_existing_folders_lower = {f.lower() for f in pre_existing_folders}
            all_conflict_sec_lower = {k.lower() for sec_list in KNOWN_CONFLICT_SECONDARY_PACKAGES.values() for k in sec_list}

            # 1. Restore physical packages in Community
            for cfg in scan_paths_cfg:
                dp = cfg.get('path', '')
                if not os.path.exists(dp):
                    continue

                onestore = os.path.join(dp, 'OneStore')
                target_dirs = [onestore] if os.path.exists(onestore) else [dp]

                for td in target_dirs:
                    if not os.path.exists(td):
                        continue
                    try:
                        for item in os.listdir(td):
                            if item.endswith('.disabled'):
                                item_clean = item[:-9]
                                item_clean_lower = item_clean.lower()
                                item_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', item_clean_lower)

                                # NEVER restore known secondary conflict packages!
                                if item_clean_lower in all_conflict_sec_lower or item_norm in all_conflict_sec_lower:
                                    continue

                                dis_p = os.path.join(td, item)
                                # Never touch protected packages
                                if is_core_or_library_package(dis_p) or is_core_or_library_package(item_clean):
                                    continue

                                try:
                                    enable_physical_package(dis_p)
                                    re_enabled_count += 1
                                except Exception as e:
                                    print(f"Error restoring {dis_p}:", e)
                    except Exception as e:
                        print(f"Error scanning {td} for restore:", e)

            # 2. Re-enable dissociated bundle BGLs
            for item in disabled_bundle_bgls:
                try:
                    pkg_p = item[0] if isinstance(item, (list, tuple)) else ''
                    b_icao = item[1] if isinstance(item, (list, tuple)) and len(item) > 1 else ''
                    if pkg_p and b_icao:
                        set_package_state_for_icao(pkg_p, b_icao, should_enable=True)
                except Exception as bgl_e:
                    print(f"Error restoring bundle BGL: {bgl_e}")

            # 3. Restore MSFS Content.xml safely (restoring flight mode modifications)
            update_msfs_content_xml(
                restore_flight_mode=True,
                flight_disabled_xml=flight_disabled_xml,
                flight_added_xml=flight_added_xml,
                pre_existing_disabled_xml=pre_existing_xml,
                full_reset=full_reset
            )

            # 4. Conflict Prevention Safeguard: Ensure secondary conflicting packages remain disabled
            auto_resolve_known_conflicts()

            # 5. Sanitize MSFS Content.xml unconditionally (forces all aircraft, liveries and utilities to Activated)
            sanitize_msfs_content_xml()

            # 6. Clear snapshot and flight mode state
            clear_isolation_snapshot()
            settings['flight_mode'] = {
                'active': False,
                'icaos': [],
                'dep_icao': '',
                'arr_icao': '',
                'profile': 'CORRIDOR',
                'alternates': [],
                'simbrief_flight': None,
                'disabled_count': 0,
                'disabled_folders': [],
                'disabled_xml_packages': [],
                'added_xml_packages': [],
                'disabled_bundle_bgls': []
            }
            save_settings(settings)

            airports = run_scan()
            return json.dumps({
                "status": "ok",
                "re_enabled_count": re_enabled_count,
                "airports": airports
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def browse_folder(self, initial_directory=""):
        try:
            window = webview.windows[0]
            valid_dir = ""
            if initial_directory and isinstance(initial_directory, str):
                cleaned = initial_directory.strip().strip('"').strip("'")
                if cleaned:
                    norm = os.path.normpath(cleaned)
                    if os.path.isdir(norm):
                        valid_dir = norm
                    elif os.path.isfile(norm):
                        valid_dir = os.path.dirname(norm)
                    else:
                        parent = os.path.dirname(norm)
                        while parent and parent != norm:
                            if os.path.isdir(parent):
                                valid_dir = parent
                                break
                            norm = parent
                            parent = os.path.dirname(norm)

            if not valid_dir or not os.path.exists(valid_dir):
                valid_dir = os.path.expanduser("~")

            valid_dir = os.path.abspath(valid_dir)
            result = window.create_file_dialog(webview.FOLDER_DIALOG, directory=valid_dir)
            if result and len(result) > 0:
                selected = result[0]
                if os.path.isfile(selected):
                    selected = os.path.dirname(selected)
                return selected
        except Exception as e:
            print("Folder dialog error:", e)
        return ""

    def open_legal_folder(self):
        try:
            legal_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "SceneryX", "legal")
            if not os.path.exists(legal_dir):
                os.makedirs(legal_dir, exist_ok=True)
            os.startfile(legal_dir)
            return json.dumps({"status": "ok"})
        except Exception as e:
            print("Error in open_legal_folder:", e)
            return json.dumps({"status": "error", "message": str(e)})

    def open_folder(self, path):
        try:
            if not path:
                return False
            path = os.path.expandvars(path)

            # 1. Direct path exists
            if os.path.exists(path):
                os.startfile(path)
                return True

            # 2. Try with .disabled suffix if disabled
            if not path.endswith('.disabled') and os.path.exists(path + '.disabled'):
                os.startfile(path + '.disabled')
                return True

            # 3. Try without .disabled suffix if path ends with .disabled
            if path.endswith('.disabled') and os.path.exists(path[:-9]):
                os.startfile(path[:-9])
                return True

            # 4. Fallback: Open parent directory (Community or StreamedPackages)
            parent_dir = os.path.dirname(path)
            if parent_dir and os.path.exists(parent_dir):
                os.startfile(parent_dir)
                return True

            # 5. Fallback for StreamedPackages
            streamed_dir = r'C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages\StreamedPackages'
            if os.path.exists(streamed_dir):
                os.startfile(streamed_dir)
                return True

            return False
        except Exception as e:
            print("Error in open_folder:", e)
            return False

    def open_file_in_explorer(self, file_path):
        if file_path and os.path.exists(file_path):
            norm_p = os.path.normpath(file_path)
            os.system(f'explorer /select,"{norm_p}"')
            return True
        elif file_path and os.path.exists(os.path.dirname(file_path)):
            os.startfile(os.path.dirname(file_path))
            return True
        return False

    def _extract_archive_files(self, archive_path_or_bytes, ext, gsx_dir, icao="", replace_existing=False):
        import shutil
        import tempfile
        import subprocess
        import zipfile

        installed_files = []
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_file_path = None
            if isinstance(archive_path_or_bytes, bytes):
                archive_file_path = os.path.join(temp_dir, f"temp_input{ext}")
                with open(archive_file_path, "wb") as f:
                    f.write(archive_path_or_bytes)
            else:
                archive_file_path = archive_path_or_bytes

            extracted_ok = False

            # 1. Try zipfile if .zip
            if ext == '.zip':
                try:
                    with zipfile.ZipFile(archive_file_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                        extracted_ok = True
                except Exception as e:
                    print("Zipfile extraction failed, trying fallback:", e)

            # 2. Try 7-Zip (7z.exe) if available (extracts .rar, .7z, .zip, etc.)
            if not extracted_ok:
                seven_zip_paths = [
                    r"C:\Program Files\7-Zip\7z.exe",
                    r"C:\Program Files (x86)\7-Zip\7z.exe",
                    shutil.which("7z"),
                    shutil.which("7za")
                ]
                seven_zip = next((p for p in seven_zip_paths if p and os.path.exists(p)), None)
                if seven_zip:
                    try:
                        res = subprocess.run([seven_zip, "x", archive_file_path, f"-o{temp_dir}", "-y"], capture_output=True, text=True)
                        if res.returncode == 0:
                            extracted_ok = True
                        else:
                            print("7z.exe stderr:", res.stderr)
                    except Exception as e:
                        print("7z.exe extraction error:", e)

            # 3. Universal Windows tar.exe fallback (.rar, .7z, .zip, .tar, etc.)
            if not extracted_ok:
                tar_exe = shutil.which("tar") or r"C:\Windows\System32\tar.exe"
                if os.path.exists(tar_exe):
                    try:
                        res = subprocess.run([tar_exe, "-xf", archive_file_path, "-C", temp_dir], capture_output=True, text=True)
                        if res.returncode == 0:
                            extracted_ok = True
                        else:
                            print("tar.exe stderr:", res.stderr)
                    except Exception as e:
                        print("tar.exe extraction error:", e)

            # 4. Clean up old GSX files for this ICAO ONLY if replace_existing is True
            target_icao = (icao or '').upper().strip()
            if replace_existing and target_icao and len(target_icao) >= 3:
                try:
                    for existing_f in os.listdir(gsx_dir):
                        if existing_f.lower() == 'configuration.ini':
                            continue
                        fp = os.path.join(gsx_dir, existing_f)
                        f_icao = extract_icao_from_gsx_filename(existing_f, valid_icaos={target_icao}, file_path=fp)
                        if f_icao == target_icao:
                            try:
                                if os.path.isfile(fp):
                                    os.remove(fp)
                                    print(f"Cleaned up old GSX profile for {target_icao}: {existing_f}")
                            except Exception as e:
                                print(f"Could not remove old GSX file {existing_f}:", e)
                except Exception as e:
                    print("Error during GSX profile cleanup:", e)

            # 5. Walk temp_dir for .ini or .py files
            for root, dirs, files in os.walk(temp_dir):
                for f in files:
                    f_lower = f.lower()
                    if (f_lower.endswith('.ini') or f_lower.endswith('.py')) and f_lower != 'configuration.ini':
                        src_p = os.path.join(root, f)
                        target_p = os.path.join(gsx_dir, f)
                        shutil.copy2(src_p, target_p)
                        installed_files.append(f)

        return installed_files

    def evaluate_incoming_gsx_profile(self, icao="", file_path="", base64_data="", filename=""):
        try:
            import base64
            import zipfile
            import io
            
            settings = get_settings()
            gsx_dir = settings.get("gsx_profile_path", get_default_gsx_path())
            
            content_str = ""
            actual_filename = filename or (os.path.basename(file_path) if file_path else "profile.ini")
            
            if base64_data:
                if "," in base64_data:
                    base64_data = base64_data.split(",", 1)[1]
                file_bytes = base64.b64decode(base64_data)
                ext = os.path.splitext(actual_filename)[1].lower()
                if ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                    try:
                        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                            for zname in zf.namelist():
                                if zname.lower().endswith('.ini') and not zname.lower().endswith('configuration.ini'):
                                    content_str = zf.read(zname).decode('utf-8', errors='ignore')
                                    actual_filename = os.path.basename(zname)
                                    break
                    except Exception: pass
                else:
                    content_str = file_bytes.decode('utf-8', errors='ignore')
            elif file_path and os.path.exists(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.zip':
                    try:
                        with zipfile.ZipFile(file_path) as zf:
                            for zname in zf.namelist():
                                if zname.lower().endswith('.ini') and not zname.lower().endswith('configuration.ini'):
                                    content_str = zf.read(zname).decode('utf-8', errors='ignore')
                                    actual_filename = os.path.basename(zname)
                                    break
                    except Exception: pass
                else:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as fh:
                            content_str = fh.read()
                    except Exception: pass
            
            from scanner import parse_single_gsx_ini, evaluate_gsx_studio_match, extract_icao_from_gsx_filename, OUTPUT_JSON_PATH
            parsed_incoming = parse_single_gsx_ini(content_str, filename=actual_filename, file_path=file_path)
            
            target_icao = (icao or '').upper().strip()
            detected_icao = extract_icao_from_gsx_filename(actual_filename, file_path=file_path)
            if not target_icao:
                target_icao = (detected_icao or "").upper().strip()
            
            # Load airport from installed_airports.json
            installed_map = {}
            if os.path.exists(OUTPUT_JSON_PATH):
                try:
                    with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                        installed_list = json.load(f)
                        installed_map = {ap['icao']: ap for ap in installed_list if isinstance(ap, dict) and 'icao' in ap}
                except Exception: pass
            
            ap = installed_map.get(target_icao)
            status, reason = evaluate_gsx_studio_match(parsed_incoming, ap)
            parsed_incoming['status'] = status
            parsed_incoming['reason'] = reason
            
            # Get existing active files for target_icao
            existing_active = []
            if gsx_dir and os.path.exists(gsx_dir) and target_icao:
                for f in os.listdir(gsx_dir):
                    if f.lower() == 'configuration.ini' or f.endswith('.disabled'):
                        continue
                    fp = os.path.join(gsx_dir, f)
                    f_icao = extract_icao_from_gsx_filename(f, valid_icaos={target_icao}, file_path=fp)
                    if f_icao == target_icao:
                        try:
                            with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                                f_content = fh.read()
                        except Exception:
                            f_content = ""
                        p_exist = parse_single_gsx_ini(f_content, filename=f, file_path=fp)
                        e_status, e_reason = evaluate_gsx_studio_match(p_exist, ap)
                        p_exist['status'] = e_status
                        p_exist['reason'] = e_reason
                        existing_active.append(p_exist)
            
            active_scenery = None
            if ap:
                active_src = next((s for s in ap.get('all_sources', []) if not s.get('is_disabled') and not s.get('is_fix_patch') and not s.get('is_addon')), None)
                active_scenery = {
                    'vendor': (active_src.get('vendor') if active_src else ap.get('vendor')) or ap.get('vendor') or 'Unknown',
                    'version': (active_src.get('version') if active_src else ap.get('version')) or ap.get('version') or '',
                    'package_name': (active_src.get('folder_name') if active_src else ap.get('package_name')) or ap.get('package_name') or '',
                    'pricing_type': ap.get('pricing_type', 'Default')
                }
            
            return json.dumps({
                "status": "ok",
                "target_icao": target_icao,
                "detected_icao": detected_icao,
                "incoming": parsed_incoming,
                "existing_active": existing_active,
                "active_scenery": active_scenery
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def sync_airport_gsx_in_json(self, icao, has_profile, filename=None, file_path=None):
        target_icao = (icao or '').upper().strip()
        if not target_icao:
            return None

        updated_ap = None
        json_paths = [OUTPUT_JSON_PATH]
        local_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'installed_airports.json')
        if os.path.exists(local_json) and os.path.abspath(local_json) != os.path.abspath(OUTPUT_JSON_PATH):
            json_paths.append(local_json)

        for j_path in json_paths:
            if os.path.exists(j_path):
                try:
                    with open(j_path, 'r', encoding='utf-8') as f:
                        airports = json.load(f)
                    changed = False
                    for ap in airports:
                        if ap.get('icao') == target_icao:
                            old_has = bool(ap.get('has_gsx_profile'))
                            old_file = ap.get('gsx_profile_filename')
                            if old_has != has_profile or old_file != filename:
                                ap['has_gsx_profile'] = bool(has_profile)
                                if has_profile and filename:
                                    ap['gsx_profile_filename'] = filename
                                    ap['gsx_ini_file'] = filename
                                    if file_path:
                                        ap['gsx_profile_path'] = file_path
                                else:
                                    ap['has_gsx_profile'] = False
                                    ap.pop('gsx_profile_filename', None)
                                    ap.pop('gsx_ini_file', None)
                                    ap.pop('gsx_profile_path', None)
                                changed = True
                            if not updated_ap:
                                updated_ap = ap
                            break
                    if changed:
                        tmp_p = j_path + '.tmp'
                        with open(tmp_p, 'w', encoding='utf-8') as f:
                            json.dump(airports, f, ensure_ascii=False)
                        os.replace(tmp_p, j_path)
                except Exception as e:
                    print(f"Error syncing {j_path} for {target_icao}:", e)

        return updated_ap

    def install_gsx_profile(self, icao="", file_path="", base64_data="", filename="", replace_existing=False):
        import shutil
        import base64
        
        settings = get_settings()
        gsx_dir = settings.get("gsx_profile_path", get_default_gsx_path())
        
        if not os.path.exists(gsx_dir):
            os.makedirs(gsx_dir, exist_ok=True)
            
        installed_files = []
        target_icao = (icao or '').upper().strip()
        
        try:
            # Clean up all existing old GSX profile files for this ICAO to guarantee NO active duplicates or lingering disabled files
            if target_icao and len(target_icao) >= 3:
                try:
                    for existing_f in os.listdir(gsx_dir):
                        if existing_f.lower() == 'configuration.ini':
                            continue
                        fp = os.path.join(gsx_dir, existing_f)
                        f_icao = extract_icao_from_gsx_filename(existing_f, valid_icaos={target_icao}, file_path=fp)
                        if f_icao == target_icao:
                            try:
                                if os.path.isfile(fp):
                                    os.remove(fp)
                            except Exception: pass
                except Exception: pass

            # 1. Base64 dropped file handling
            if base64_data and filename:
                if "," in base64_data:
                    base64_data = base64_data.split(",", 1)[1]
                    
                file_bytes = base64.b64decode(base64_data)
                ext = os.path.splitext(filename)[1].lower()
                
                if ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                    installed_files = self._extract_archive_files(file_bytes, ext, gsx_dir, icao=target_icao, replace_existing=replace_existing)
                elif ext in ['.ini', '.py']:
                    if filename and filename.lower() != 'configuration.ini':
                        target_p = os.path.join(gsx_dir, filename)
                        with open(target_p, 'wb') as f:
                            f.write(file_bytes)
                        installed_files.append(filename)

            # 2. File path handling (from file picker or file.path)
            elif file_path:
                if not os.path.exists(file_path):
                    return json.dumps({"status": "error", "message": f"File not found: {file_path}"})
                    
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                    installed_files = self._extract_archive_files(file_path, ext, gsx_dir, icao=target_icao, replace_existing=replace_existing)
                elif ext in ['.ini', '.py']:
                    fname = os.path.basename(file_path)
                    if fname and fname.lower() != 'configuration.ini':
                        target_p = os.path.join(gsx_dir, fname)
                        shutil.copy2(file_path, target_p)
                        installed_files.append(fname)

                        # Also copy any companion .py or _handler.py files located in the same directory
                        src_dir = os.path.dirname(file_path)
                        stem = os.path.splitext(fname)[0].lower()
                        try:
                            for sibling in os.listdir(src_dir):
                                s_lower = sibling.lower()
                                if s_lower == fname.lower() or s_lower == 'configuration.ini':
                                    continue
                                if s_lower.endswith('.py'):
                                    s_stem = os.path.splitext(s_lower)[0]
                                    if (stem in s_stem or s_stem in stem or
                                        s_stem.replace('_', '-') == stem.replace('_', '-') or
                                        s_stem.replace('-', '_') == stem.replace('-', '_')):
                                        s_target = os.path.join(gsx_dir, sibling)
                                        shutil.copy2(os.path.join(src_dir, sibling), s_target)
                                        installed_files.append(sibling)
                        except Exception as e:
                            print(f"Error copying companion GSX files from {src_dir}:", e)

            # 3. No path/data provided -> Open File Dialog
            else:
                try:
                    window = webview.windows[0]
                    result = window.create_file_dialog(
                        webview.OPEN_DIALOG,
                        allow_multiple=False,
                        file_types=('GSX Profiles & Archives (*.zip;*.rar;*.7z;*.ini;*.py)', 'All files (*.*)')
                    )
                    if result and len(result) > 0:
                        return self.install_gsx_profile(icao=icao, file_path=result[0], replace_existing=replace_existing)
                except Exception as e:
                    return json.dumps({"status": "error", "message": str(e)})

            if not installed_files:
                return json.dumps({"status": "error", "message": "No valid GSX profile file (.ini or .py) found in this archive."})

            # Fast in-place sync of installed_airports.json
            updated_ap = None
            if target_icao:
                ini_f = next((f for f in installed_files if f.lower().endswith('.ini')), (installed_files[0] if installed_files else None))
                updated_ap = self.sync_airport_gsx_in_json(target_icao, True, ini_f, os.path.join(gsx_dir, ini_f) if ini_f else None)

            audit_data = audit_all_gsx_profiles(gsx_dir=gsx_dir)
            return json.dumps({
                "status": "ok",
                "installed_files": installed_files,
                "target_icao": target_icao,
                "airport": updated_ap,
                "audit": audit_data
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def check_airport_gsx_status(self, icao):
        try:
            target_icao = (icao or '').upper().strip()
            if not target_icao:
                return json.dumps({"status": "error", "message": "No ICAO provided"})
            settings = get_settings()
            gsx_dir = settings.get("gsx_profile_path", get_default_gsx_path())
            audit = audit_single_airport_gsx(target_icao, gsx_dir=gsx_dir)
            has_profile = (audit.get('status') == 'MATCHED') or bool([f for f in audit.get('files', []) if not f.get('is_disabled')])
            active_file = next((f for f in audit.get('files', []) if not f.get('is_disabled')), None)
            filename = active_file['filename'] if active_file else None

            # Sync into installed_airports.json
            self.sync_airport_gsx_in_json(target_icao, has_profile, filename, active_file.get('path', '') if active_file else None)

            return json.dumps({
                "status": "ok",
                "icao": target_icao,
                "has_gsx_profile": has_profile,
                "audit": audit
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def install_bundled_gsx_profile(self, icao):
        try:
            target_icao = (icao or '').upper().strip()
            if not target_icao:
                return json.dumps({"status": "error", "message": "No ICAO provided"})

            ini_path = None
            if os.path.exists(OUTPUT_JSON_PATH):
                try:
                    with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                        airports = json.load(f)
                    for ap in airports:
                        if ap.get('icao') == target_icao:
                            b_prof = ap.get('bundled_gsx_profile')
                            if b_prof and b_prof.get('ini_path') and os.path.exists(b_prof['ini_path']):
                                ini_path = b_prof['ini_path']
                            break
                except Exception as e:
                    print("Error reading airports JSON for bundled GSX:", e)

            # Fallback direct scan of packages if not in JSON yet
            if not ini_path and os.path.exists(OUTPUT_JSON_PATH):
                try:
                    with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                        airports = json.load(f)
                    for ap in airports:
                        if ap.get('icao') == target_icao:
                            for s in ap.get('all_sources', []):
                                pkg_p = s.get('package_path')
                                if pkg_p and os.path.exists(pkg_p):
                                    found_b = find_bundled_gsx(pkg_p, icao=target_icao)
                                    if found_b and os.path.exists(found_b['ini_path']):
                                        ini_path = found_b['ini_path']
                                        break
                            if ini_path:
                                break
                except Exception:
                    pass

            if not ini_path or not os.path.exists(ini_path):
                return json.dumps({"status": "error", "message": f"No official bundled GSX profile found on disk for {target_icao}."})

            res_str = self.install_gsx_profile(icao=target_icao, file_path=ini_path, replace_existing=True)
            res = json.loads(res_str) if isinstance(res_str, str) else res_str

            # Update bundled_gsx_profile.is_installed in installed_airports.json
            if res.get('status') == 'ok':
                json_paths = [OUTPUT_JSON_PATH]
                local_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'installed_airports.json')
                if os.path.exists(local_json) and os.path.abspath(local_json) != os.path.abspath(OUTPUT_JSON_PATH):
                    json_paths.append(local_json)

                for j_path in json_paths:
                    if os.path.exists(j_path):
                        try:
                            with open(j_path, 'r', encoding='utf-8') as f:
                                airports = json.load(f)
                            for ap in airports:
                                if ap.get('icao') == target_icao:
                                    if ap.get('bundled_gsx_profile'):
                                        ap['bundled_gsx_profile']['is_installed'] = True
                                    break
                            tmp_p = j_path + '.tmp'
                            with open(tmp_p, 'w', encoding='utf-8') as f:
                                json.dump(airports, f, ensure_ascii=False)
                            os.replace(tmp_p, j_path)
                        except Exception as e:
                            print(f"Error updating bundled_gsx_profile.is_installed in {j_path}:", e)

            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def scan_gsx_audit(self):
        try:
            settings = get_settings()
            gsx_dir = settings.get("gsx_profile_path", get_default_gsx_path())
            audit_data = audit_all_gsx_profiles(gsx_dir=gsx_dir)
            return json.dumps({"status": "ok", "data": audit_data}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def resolve_gsx_duplicate(self, icao, active_filename, disable_filename=None):
        try:
            settings = get_settings()
            gsx_dir = settings.get("gsx_profile_path", get_default_gsx_path())
            if not gsx_dir or not os.path.exists(gsx_dir):
                return json.dumps({"status": "error", "message": "GSX directory not found."})

            target_icao = (icao or '').upper().strip()
            if not target_icao or len(target_icao) < 3:
                target_icao = extract_icao_from_gsx_filename(active_filename, file_path=os.path.join(gsx_dir, active_filename)) or ''

            # If active_filename currently ends in .disabled, enable it
            active_path = os.path.join(gsx_dir, active_filename)
            if active_filename.endswith('.disabled'):
                new_active_name = active_filename[:-9]
                new_active_path = os.path.join(gsx_dir, new_active_name)
                if os.path.exists(new_active_path):
                    try: os.remove(new_active_path)
                    except Exception: pass
                if os.path.exists(active_path):
                    os.replace(active_path, new_active_path)
                active_filename = new_active_name

            # If disable_filename specified, disable that specific one
            if disable_filename:
                dis_path = os.path.join(gsx_dir, disable_filename)
                if os.path.exists(dis_path) and not disable_filename.endswith('.disabled'):
                    target_dis = dis_path + '.disabled'
                    if os.path.exists(target_dis):
                        try: os.remove(target_dis)
                        except Exception: pass
                    os.replace(dis_path, target_dis)
            else:
                # Disable all other active profiles for this ICAO ONLY if target_icao is valid!
                if target_icao and len(target_icao) >= 3:
                    for f in os.listdir(gsx_dir):
                        if f == active_filename or f.lower() == 'configuration.ini' or f.endswith('.disabled'):
                            continue
                        if not f.lower().endswith(('.ini', '.py')):
                            continue
                        fp = os.path.join(gsx_dir, f)
                        f_icao = extract_icao_from_gsx_filename(f, valid_icaos={target_icao}, file_path=fp)
                        if f_icao == target_icao:
                            dest_fp = fp + '.disabled'
                            if os.path.exists(dest_fp):
                                try: os.remove(dest_fp)
                                except Exception: pass
                            try:
                                os.replace(fp, dest_fp)
                            except Exception as e:
                                print(f"Error disabling GSX file {f}:", e)

            audit_data = audit_all_gsx_profiles(gsx_dir=gsx_dir)
            return json.dumps({"status": "ok", "data": audit_data}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def enable_gsx_profile(self, icao, filename):
        try:
            settings = get_settings()
            gsx_dir = settings.get("gsx_profile_path", get_default_gsx_path())
            if not gsx_dir or not os.path.exists(gsx_dir):
                return json.dumps({"status": "error", "message": "GSX directory not found."})

            target_icao = (icao or '').upper().strip()
            if not target_icao or len(target_icao) < 3:
                target_icao = extract_icao_from_gsx_filename(filename, file_path=os.path.join(gsx_dir, filename)) or ''

            # Disable any other active profile for this ICAO first ONLY if target_icao is valid
            if target_icao and len(target_icao) >= 3:
                for f in os.listdir(gsx_dir):
                    if f.lower() == 'configuration.ini' or f.endswith('.disabled') or f == filename:
                        continue
                    if not f.lower().endswith(('.ini', '.py')):
                        continue
                    fp = os.path.join(gsx_dir, f)
                    f_icao = extract_icao_from_gsx_filename(f, valid_icaos={target_icao}, file_path=fp)
                    if f_icao == target_icao:
                        dest_fp = fp + '.disabled'
                        if os.path.exists(dest_fp):
                            try: os.remove(dest_fp)
                            except Exception: pass
                        try:
                            os.replace(fp, dest_fp)
                        except Exception as e:
                            print(f"Error disabling GSX file {f}:", e)

            # Now enable target file and any companion scripts (.py.disabled, _handler.py.disabled)
            stem = filename[:-9] if filename.lower().endswith('.disabled') else filename
            stem_base = os.path.splitext(stem)[0].lower()
            target_ini_name = stem if (stem.lower().endswith('.ini') or stem.lower().endswith('.py')) else (stem + '.ini')
            
            for f in os.listdir(gsx_dir):
                f_clean = f[:-9] if f.lower().endswith('.disabled') else f
                f_base = os.path.splitext(f_clean)[0].lower()
                if f == filename or f_base == stem_base or f_base.startswith(stem_base) or stem_base.startswith(f_base):
                    fp = os.path.join(gsx_dir, f)
                    if f.lower().endswith('.disabled'):
                        target_name = f[:-9]
                        target_fp = os.path.join(gsx_dir, target_name)
                        if os.path.exists(target_fp):
                            try: os.remove(target_fp)
                            except Exception: pass
                        if os.path.exists(fp):
                            try: os.replace(fp, target_fp)
                            except Exception: pass
                        if target_name.lower().endswith('.ini'):
                            target_ini_name = target_name

            target_icao = (icao or '').upper().strip()
            if target_icao:
                self.sync_airport_gsx_in_json(target_icao, True, target_ini_name, os.path.join(gsx_dir, target_ini_name))

            audit_data = audit_all_gsx_profiles(gsx_dir=gsx_dir)
            return json.dumps({"status": "ok", "data": audit_data}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def disable_gsx_profile(self, icao, filename):
        try:
            settings = get_settings()
            gsx_dir = settings.get("gsx_profile_path", get_default_gsx_path())
            if not gsx_dir or not os.path.exists(gsx_dir):
                return json.dumps({"status": "error", "message": "GSX directory not found."})

            if not filename or '..' in filename or '/' in filename or '\\' in filename:
                return json.dumps({"status": "error", "message": "Invalid filename."})

            target_icao = (icao or '').upper().strip()
            stem = filename[:-9] if filename.lower().endswith('.disabled') else filename
            stem_base = os.path.splitext(stem)[0].lower()
            for f in os.listdir(gsx_dir):
                f_clean = f[:-9] if f.lower().endswith('.disabled') else f
                f_base = os.path.splitext(f_clean)[0].lower()
                if f == filename or f_base == stem_base or f_base.startswith(stem_base) or stem_base.startswith(f_base):
                    fp = os.path.join(gsx_dir, f)
                    if os.path.exists(fp) and not f.lower().endswith('.disabled'):
                        dest_fp = fp + '.disabled'
                        if os.path.exists(dest_fp):
                            try: os.remove(dest_fp)
                            except Exception: pass
                        try: os.replace(fp, dest_fp)
                        except Exception: pass

            # Determine remaining active file for target_icao
            active_file = None
            has_profile = False
            if target_icao:
                for f in os.listdir(gsx_dir):
                    if f.lower() == 'configuration.ini' or f.lower().endswith('.disabled'):
                        continue
                    fp = os.path.join(gsx_dir, f)
                    f_icao = extract_icao_from_gsx_filename(f, valid_icaos={target_icao}, file_path=fp)
                    if f_icao == target_icao:
                        active_file = f
                        has_profile = True
                        break
                self.sync_airport_gsx_in_json(target_icao, has_profile, active_file, os.path.join(gsx_dir, active_file) if active_file else None)

            audit_data = audit_all_gsx_profiles(gsx_dir=gsx_dir)
            return json.dumps({"status": "ok", "data": audit_data}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def delete_gsx_profile(self, icao, filename):
        try:
            settings = get_settings()
            gsx_dir = settings.get("gsx_profile_path", get_default_gsx_path())
            if not gsx_dir or not os.path.exists(gsx_dir):
                return json.dumps({"status": "error", "message": "GSX directory not found."})

            if not filename or '..' in filename or '/' in filename or '\\' in filename:
                return json.dumps({"status": "error", "message": "Invalid filename."})

            target_icao = (icao or '').upper().strip()
            stem = filename[:-9] if filename.lower().endswith('.disabled') else filename
            stem_base = os.path.splitext(stem)[0].lower()
            deleted_any = False
            for f in os.listdir(gsx_dir):
                f_clean = f[:-9] if f.lower().endswith('.disabled') else f
                f_base = os.path.splitext(f_clean)[0].lower()
                if f == filename or f_base == stem_base or f_base.startswith(stem_base) or stem_base.startswith(f_base):
                    fp = os.path.join(gsx_dir, f)
                    if os.path.exists(fp) and os.path.isfile(fp):
                        try:
                            os.remove(fp)
                            deleted_any = True
                        except Exception: pass
            if not deleted_any:
                return json.dumps({"status": "error", "message": f"File '{filename}' not found."})

            # Determine remaining active file for target_icao
            active_file = None
            has_profile = False
            if target_icao:
                for f in os.listdir(gsx_dir):
                    if f.lower() == 'configuration.ini' or f.lower().endswith('.disabled'):
                        continue
                    fp = os.path.join(gsx_dir, f)
                    f_icao = extract_icao_from_gsx_filename(f, valid_icaos={target_icao}, file_path=fp)
                    if f_icao == target_icao:
                        active_file = f
                        has_profile = True
                        break
                self.sync_airport_gsx_in_json(target_icao, has_profile, active_file, os.path.join(gsx_dir, active_file) if active_file else None)

            audit_data = audit_all_gsx_profiles(gsx_dir=gsx_dir)
            return json.dumps({"status": "ok", "data": audit_data}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def delete_all_disabled_gsx_profiles(self):
        try:
            settings = get_settings()
            gsx_dir = settings.get("gsx_profile_path", get_default_gsx_path())
            if not gsx_dir or not os.path.exists(gsx_dir):
                return json.dumps({"status": "error", "message": "GSX directory not found."})

            deleted_count = 0
            for f in os.listdir(gsx_dir):
                if f.lower().endswith('.disabled'):
                    fp = os.path.join(gsx_dir, f)
                    try:
                        if os.path.isfile(fp):
                            os.remove(fp)
                            deleted_count += 1
                    except Exception as e:
                        print(f"Error removing {fp}: {e}")

            audit_data = audit_all_gsx_profiles(gsx_dir=gsx_dir)
            for a_icao, entry in audit_data.get('by_icao', {}).items():
                act_f = next((f['filename'] for f in entry.get('files', []) if not f.get('is_disabled')), None)
                self.sync_airport_gsx_in_json(a_icao, bool(act_f), act_f, os.path.join(gsx_dir, act_f) if act_f else None)

            return json.dumps({"status": "ok", "deleted_count": deleted_count, "data": audit_data}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def search_gsx_profile(self, icao, name="", extra_terms=""):
        import webbrowser
        import urllib.parse
        target_icao = (icao or '').upper().strip()
        url = f"https://flightsim.to/miscellaneous/gsx-pro?q={urllib.parse.quote(target_icao)}"
        webbrowser.open(url)
        return json.dumps({"status": "ok", "url": url})

    def reveal_file_in_explorer(self, file_path):
        import subprocess
        try:
            settings = get_settings()
            gsx_dir = settings.get("gsx_profile_path", get_default_gsx_path())
            full_path = file_path or ''
            if not os.path.isabs(full_path) and gsx_dir:
                full_path = os.path.join(gsx_dir, file_path)
            
            if os.path.exists(full_path):
                subprocess.Popen(f'explorer /select,"{os.path.normpath(full_path)}"')
                return json.dumps({"status": "ok"})
            elif gsx_dir and os.path.exists(gsx_dir):
                subprocess.Popen(f'explorer "{os.path.normpath(gsx_dir)}"')
                return json.dumps({"status": "ok"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
        return json.dumps({"status": "error", "message": "File not found"})

    def open_file_in_explorer(self, file_path):
        return self.reveal_file_in_explorer(file_path)

    def check_update(self, icao, name, vendor, version, pricing_type=""):
        import webbrowser
        import urllib.parse
        
        PAYWARE_VENDOR_URLS = {
            'orbx': 'https://orbxdirect.com/search?q={query}',
            'aerosoft': 'https://www.aerosoft.com/en/search?sSearch={query}',
            'inibuilds': 'https://inibuilds.com/search?q={query}',
            'flightbeam': 'https://www.flightbeam.com/search?q={query}',
            'flytampa': 'https://www.flytampa.org/',
            'pyreegue': 'https://contrail.shop/collections/pyreegue-dev-co',
            'fsdreamteam': 'https://www.fsdreamteam.com/',
            'fsdt': 'https://www.fsdreamteam.com/',
            'mk-studios': 'https://mkstudios.com/',
            'mk studios': 'https://mkstudios.com/',
            'drzewiecki': 'https://www.drzewiecki-design.net/products.htm',
            'drzewiecki design': 'https://www.drzewiecki-design.net/products.htm',
            'simmarket': 'https://secure.simmarket.com/advanced_search_result.php?keywords={query}',
            'simwings': 'https://www.aerosoft.com/en/search?sSearch={query}',
            'sim-wings': 'https://www.aerosoft.com/en/search?sSearch={query}',
            'digital design': 'https://secure.simmarket.com/advanced_search_result.php?keywords={query}',
            'nza': 'https://nzasimulations.com/',
            'nza simulations': 'https://nzasimulations.com/',
            'verticalsim': 'https://verticalsims.com/shop/',
            'latinvfr': 'https://www.latinvfr.com/',
            'pilotplus': 'https://pilotplus.io/',
            'threshold': 'https://www.thresholdx.net/search?q={query}',
            'tailstrike': 'https://secure.simmarket.com/advanced_search_result.php?keywords={query}',
            'gaya': 'https://www.gaya-studios.com/',
            'gaya simulations': 'https://www.gaya-studios.com/',
            'dominicdesignteam': 'https://secure.simmarket.com/advanced_search_result.php?keywords={query}',
            'taimedia': 'https://secure.simmarket.com/advanced_search_result.php?keywords={query}',
            'contrail': 'https://contrail.shop/search?q={query}',
            'macco': 'https://contrail.shop/search?q={query}',
            'bmworld': 'https://contrail.shop/search?q={query}',
            'amsim': 'https://contrail.shop/search?q={query}',
            'fly2high': 'https://contrail.shop/search?q={query}',
            'northern sky': 'https://contrail.shop/search?q={query}',
            'uk2000': 'https://www.uk2000scenery.com/'
        }

        clean_name = (name or '').strip()
        q_str = f"{icao} {clean_name}".strip() if clean_name and clean_name.lower() not in ['unknown', 'default'] else f"{icao}".strip()
        q_enc = urllib.parse.quote(q_str)

        v_lower = (vendor or '').lower().strip()
        target_url = None

        for key, pattern in PAYWARE_VENDOR_URLS.items():
            if key in v_lower:
                target_url = pattern.format(query=q_enc) if '{query}' in pattern else pattern
                break

        if not target_url:
            if pricing_type == 'Payware' or (vendor and vendor.lower() not in ['unknown', 'microsoft / asobo', 'asobo', 'unknown vendor']):
                target_url = f"https://secure.simmarket.com/advanced_search_result.php?keywords={q_enc}"
            else:
                target_url = f"https://flightsim.to/search?q={q_enc}&cat=airports%2Cscenery&exclude_cat=static-aircraft%2Cgsx-pro&sim=msfs2020%2Cmsfs2024"

        webbrowser.open(target_url)
        return json.dumps({"status": "ok", "url": target_url})

    def open_external_url(self, url):
        import webbrowser
        try:
            if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('mailto:')):
                if url.startswith('mailto:'):
                    try:
                        os.startfile(url)
                    except Exception:
                        webbrowser.open(url)
                else:
                    webbrowser.open(url)
                return json.dumps({"status": "ok"})
        except Exception as e:
            print("open_external_url error:", e)
            return json.dumps({"status": "error", "message": str(e)})
        return json.dumps({"status": "error", "message": "Invalid URL"})

    def reveal_in_explorer(self, file_path):
        import subprocess
        try:
            if file_path and os.path.exists(file_path):
                subprocess.Popen(['explorer.exe', f'/select,"{os.path.abspath(file_path)}"'])
                return json.dumps({"status": "ok"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
        return json.dumps({"status": "error", "message": "File not found"})

    def set_user_category_override(self, icao, category):
        try:
            save_custom_category(icao, category)
            airports = fast_update_airport_cache(icao)
            return json.dumps({"status": "ok", "airports": airports}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def is_disclaimer_accepted(self):
        try:
            settings = get_settings()
            return json.dumps({"accepted": bool(settings.get("disclaimer_accepted", False))})
        except Exception as e:
            return json.dumps({"accepted": False})

    def accept_disclaimer(self):
        try:
            settings = get_settings()
            settings["disclaimer_accepted"] = True
            save_settings(settings)
            return json.dumps({"status": "ok"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def is_onboarding_completed(self):
        try:
            settings = get_settings()
            return json.dumps({"completed": bool(settings.get("has_seen_onboarding", False))})
        except Exception as e:
            return json.dumps({"completed": False})

    def set_onboarding_completed(self, completed=True):
        try:
            settings = get_settings()
            settings["has_seen_onboarding"] = bool(completed)
            save_settings(settings)
            return json.dumps({"status": "ok", "has_seen_onboarding": settings["has_seen_onboarding"]})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def close_app(self):
        try:
            if hasattr(webview, 'windows') and webview.windows:
                webview.windows[0].destroy()
        except Exception as e:
            print("Error closing app:", e)
        return json.dumps({"status": "ok"})

    def get_exports_dir(self):
        app_root = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        exports_dir = os.path.join(app_root, "exports")
        os.makedirs(exports_dir, exist_ok=True)
        return exports_dir

    def export_collection_csv(self, airports_json_str):
        import csv
        try:
            airports = json.loads(airports_json_str)
            window = webview.windows[0]
            exports_dir = self.get_exports_dir()
            result = window.create_file_dialog(
                webview.SAVE_DIALOG,
                directory=exports_dir,
                save_filename="SceneryX_Collection.csv",
                file_types=('CSV Files (*.csv)', 'All files (*.*)')
            )
            if not result:
                return json.dumps({"status": "cancelled"})
            
            file_path = result[0] if isinstance(result, (list, tuple)) else result
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'ICAO', 'Name', 'City', 'Country', 'Pricing Model', 
                    'Vendor/Developer', 'Version', 'Package Name', 'Disk Size', 
                    'GSX Profile', 'GSX INI File', 'Price (EUR)', 'User Rating'
                ])
                for ap in airports:
                    writer.writerow([
                        ap.get('icao', ''),
                        ap.get('name', ''),
                        ap.get('city', ''),
                        ap.get('country', ''),
                        ap.get('pricing_type', ''),
                        ap.get('vendor', ''),
                        ap.get('version', ''),
                        ap.get('package_name', ''),
                        ap.get('size_str', ''),
                        'Yes' if ap.get('has_gsx_profile') else 'No',
                        ap.get('gsx_profile_filename', ''),
                        ap.get('price_eur', 0.0),
                        ap.get('rating', 0.0)
                    ])
            return json.dumps({"status": "ok", "path": file_path, "count": len(airports)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def check_payware_stores(self, icao, airport_name=""):
        """Check availability of payware scenery for an ICAO code across major stores."""
        import urllib.request
        import urllib.parse
        import json
        import re
        from concurrent.futures import ThreadPoolExecutor

        if not hasattr(self, '_payware_store_cache'):
            self._payware_store_cache = {}

        icao_clean = (icao or "").strip().upper()
        name_clean = (airport_name or "").strip()
        if not icao_clean:
            return json.dumps([])

        cache_key = f"{icao_clean}_{name_clean.lower()}"
        if cache_key in self._payware_store_cache:
            return json.dumps(self._payware_store_cache[cache_key])

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        def fetch_html(u, post_json=None):
            try:
                h = dict(headers)
                data = None
                if post_json is not None:
                    h['Content-Type'] = 'application/json'
                    h['Origin'] = 'https://orbxdirect.com'
                    h['Referer'] = 'https://orbxdirect.com/'
                    data = json.dumps(post_json).encode('utf-8')
                req = urllib.request.Request(u, data=data, headers=h)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return resp.read().decode('utf-8', errors='ignore')
            except Exception:
                return ''

        BLACKLIST_KEYWORDS = [
            '1935', '1940', '1944', '1945', '1950', '1960', '1970', '1980',
            'retro', 'vintage', 'historical', 'historic', 'mesh', 'dem', 'traffic',
            'sound', 'pushback', 'ground service', 'gsx', 'livery', 'liveries',
            'texture', 'textures', 'night lighting', 'night light', 'lighting',
            'trial', 'free trial', 'emergencydispatcher', 'donation', 'linienstern',
            'skyelite', 'landmark', 'landmarks', 'city pack', 'city scenery', 'bridges',
            'photogrammetry', 'satellite', 'aerial', 'poi', 'points of interest',
            'profile', 'profiles', 'approach plate', 'charts', 'guide', 'manual',
            'tree', 'trees', 'vegetation', 'foliage', 'forest'
        ]

        clean_words = []
        if name_clean:
            for w in re.split(r'[\s\-,/]+', name_clean):
                w_clean = re.sub(r'[^a-zA-Z]', '', w).strip()
                if len(w_clean) >= 4 and w_clean.lower() not in ['airport', 'international', 'regional', 'national', 'field', 'paris', 'london', 'berlin', 'town', 'city', 'east', 'west', 'north', 'south']:
                    clean_words.append(w_clean.lower())

        def check_sm(code):
            u = f"https://secure.simmarket.com/advanced_search_result.php?keywords={code}"
            h = fetch_html(u)
            if not h or "There is no product that matches the search criteria" in h:
                return False, u, None, "", ""
            cards = re.findall(r'<a[^>]*class=[\'"]product-card__name[\'"][^>]*href=([^\s>]+)[^>]*>([\s\S]*?)</a>([\s\S]*?)product-card__price[\s\S]*?<span>([\s\S]*?)</span>', h)
            for link, title, middle, price_raw in cards:
                t = re.sub(r'<[^>]+>', '', title).strip()
                t_low = t.lower()
                # 1. Blacklist check (landmarks, retro, sounds, etc.)
                if any(b in t_low for b in BLACKLIST_KEYWORDS):
                    continue
                # 2. Simulator check (exclude X-Plane, P3D, FSX if not MSFS)
                if any(old in t_low for old in ['p3d', 'prepar3d', 'fsx', 'fs9', 'xp11', 'xp12', 'xp ', 'x-plane', 'xplane']) and 'msfs' not in t_low:
                    continue
                # 3. Product title must explicitly match ICAO code or airport city name
                has_code = bool(re.search(r'\b' + re.escape(code.lower()) + r'\b', t_low))
                has_name = any(re.search(r'\b' + re.escape(cw) + r'\b', t_low) for cw in clean_words) if clean_words else False
                if not (has_code or has_name):
                    continue

                p_clean = re.sub(r'<[^>]+>', '', price_raw).replace('&nbsp;', ' ').strip()
                num_m = re.search(r'(\d+[\.,]\d{2})', p_clean)
                price_val = float(num_m.group(1).replace(',', '.')) if num_m else None
                clean_link = link.strip('\'"')
                if clean_link.startswith('//'): clean_link = 'https:' + clean_link
                elif not clean_link.startswith('http'): clean_link = 'https://secure.simmarket.com/' + clean_link.lstrip('/')

                dev_m = re.search(r'class=[\'"]product-card__manufacturer-name[\'"][^>]*>([\s\S]*?)</a>', middle)
                dev_name = re.sub(r'<[^>]+>', '', dev_m.group(1)).strip() if dev_m else ""

                return True, clean_link, price_val, "EUR", dev_name
            return False, u, None, "", ""

        def check_orbx(code):
            default_u = f"https://orbxdirect.com/?s={code}"
            res = fetch_html("https://orbxdirect.com/api/v4/search", post_json={"search": code})
            if not res:
                return False, default_u, None, "", ""
            try:
                d = json.loads(res)
                results = d.get('data', {}).get('results', [])
                for p in results:
                    slug = p.get('slug', '')
                    name = p.get('primary_text', '')
                    full_desc = (slug + ' ' + name).lower()
                    if any(b in full_desc for b in BLACKLIST_KEYWORDS):
                        continue
                    if any(old in full_desc for old in ['p3d', 'prepar3d', 'fsx', 'fs9', 'xp11', 'xp12', 'xp ', 'x-plane', 'xplane']) and 'msfs' not in full_desc:
                        continue
                    if re.search(r'(^|-)' + re.escape(code.lower()) + r'(-|$)', slug) or code.lower() in slug:
                        prod_url = f"https://orbxdirect.com/product/{slug}"
                        pricing = p.get('pricing') or {}
                        price_val = pricing.get('price') or pricing.get('base')
                        price_float = float(price_val) if price_val is not None else None
                        comp = p.get('company')
                        dev_name = comp.get('name') if isinstance(comp, dict) else (comp if isinstance(comp, str) else "")
                        return True, prod_url, price_float, "AUD", dev_name
            except Exception:
                pass
            return False, default_u, None, "", ""

        def check_ini(code):
            u = f"https://inibuilds.com/search?q={code}&options%5Bprefix%5D=last"
            h = fetch_html(u)
            if not h or "0 results" in h.lower() or "could not find any results" in h.lower():
                return False, u, None, "", ""
            cards = re.findall(r'class=[\'"][^\'"]*card__heading[^\'"]*[\'"][\s\S]*?<a\s+href=[\'"]([^\'"]*)[\'"][^>]*>([\s\S]*?)</a>([\s\S]*?)(?=class=[\'"][^\'"]*card__heading|class=[\'"][^\'"]*footer|$)', h)
            for link, title, card_body in cards:
                t = re.sub(r'<[^>]+>', '', title).strip()
                t_low = t.lower()
                if any(b in t_low for b in BLACKLIST_KEYWORDS):
                    continue
                if re.search(r'\b' + re.escape(code) + r'\b', t, re.IGNORECASE):
                    prod_url = f"https://inibuilds.com{link}" if link.startswith('/') else f"https://inibuilds.com/{link}"
                    price_val, curr = None, "GBP"
                    dev_name = ""
                    idx = h.find(link)
                    if idx != -1:
                        snippet = h[idx:idx+4500]
                        m = re.search(r'class=[\'"]?money[\'"]?[^>]*>[^\d]*(\d+[\.,]\d{2})\s*([A-Z]{3})', snippet)
                        if not m:
                            m = re.search(r'[Â£$â‚¬]\s*(\d+[\.,]\d{2})\s*([A-Z]{3})?', snippet)
                        if m:
                            price_val = float(m.group(1).replace(',', '.'))
                            if len(m.groups()) > 1 and m.group(2):
                                curr = m.group(2)
                        dev_m = re.search(r'vendorColor[^>]*>([\s\S]*?)</div>', snippet)
                        if dev_m:
                            raw_vendor = re.sub(r'<[^>]+>', '', dev_m.group(1)).strip()
                            if raw_vendor.lower() in ['inibuilds', 'iniscene']:
                                if any(k in t_low for k in [' x ', 'collab', 'collaboration', '/']):
                                    dev_name = raw_vendor
                                else:
                                    dev_name = ""
                            else:
                                dev_name = raw_vendor
                    return True, prod_url, price_val, curr, dev_name
            return False, u, None, "", ""

        def get_fsto_prices():
            if not hasattr(self, '_fsto_prices_cache'):
                self._fsto_prices_cache = {}
            if self._fsto_prices_cache:
                return self._fsto_prices_cache
            try:
                p_req = urllib.request.Request('https://flightsim.to/backend/store/prices', headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://flightsim.to/store/'})
                with urllib.request.urlopen(p_req, timeout=4) as p_resp:
                    self._fsto_prices_cache = json.loads(p_resp.read().decode('utf-8'))
            except Exception:
                pass
            return self._fsto_prices_cache

        def check_fsto(code):
            default_u = f"https://flightsim.to/store/search?q={code}"
            code_low = code.lower()

            candidates = []
            queries = [code]
            if name_clean and len(name_clean) >= 4:
                queries.append(name_clean)
            elif len(clean_words) == 1:
                queries.append(clean_words[0])

            for q in queries:
                u = f"https://flightsim.to/backend/store/search?query={urllib.parse.quote(q)}"
                try:
                    req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://flightsim.to/store/'})
                    with urllib.request.urlopen(req, timeout=4) as resp:
                        d = json.loads(resp.read().decode('utf-8'))
                        for it in d.get('data', []):
                            if it.get('id') not in [c.get('id') for c in candidates]:
                                candidates.append(it)
                except Exception:
                    pass

            if not candidates:
                return False, default_u, None, "", ""

            prices = get_fsto_prices()

            def find_fsto_price(slug, code_val):
                if not prices or not slug:
                    return None
                if slug in prices:
                    return prices[slug]
                slug_tokens = set(re.split(r'[-_\s]+', slug.lower()))
                for k, v in prices.items():
                    k_tokens = set(re.split(r'[-_\s]+', k.lower()))
                    if slug_tokens == k_tokens:
                        return v
                code_low_val = code_val.lower()
                best_match = None
                best_score = 0
                for k, v in prices.items():
                    k_tokens = set(re.split(r'[-_\s]+', k.lower()))
                    if code_low_val in k_tokens:
                        overlap = len(slug_tokens & k_tokens)
                        if overlap > best_score:
                            best_score = overlap
                            best_match = v
                if best_match and best_score >= 3:
                    return best_match
                return None

            # Prioritize candidates that have an available price in prices map
            candidates.sort(key=lambda it: 0 if find_fsto_price(it.get('slug'), code) else 1)

            for it in candidates:
                title = it.get('title', '')
                t_low = title.lower()
                slug = it.get('slug', '')
                cat = it.get('category', '')

                # Exclude blacklisted items or non-airports
                if any(b in t_low for b in BLACKLIST_KEYWORDS) or any(b in slug for b in BLACKLIST_KEYWORDS):
                    continue
                if cat and cat not in ['Airports', 'Scenery', 'Scenery Enhancements']:
                    continue

                matched = False
                if re.search(r'\b' + re.escape(code_low) + r'\b', t_low) or re.search(r'(^|-)' + re.escape(code_low) + r'(-|$)', slug):
                    matched = True
                elif name_clean and len(name_clean) >= 4 and re.search(r'\b' + re.escape(name_clean.lower()) + r'\b', t_low):
                    matched = True
                elif len(clean_words) == 1:
                    cw = clean_words[0]
                    if len(cw) >= 4 and (re.search(r'\b' + re.escape(cw) + r'\b', t_low) or re.search(r'(^|-)' + re.escape(cw) + r'(-|$)', slug)):
                        matched = True
                elif len(clean_words) >= 2:
                    if all(re.search(r'\b' + re.escape(cw) + r'\b', t_low) or re.search(r'(^|-)' + re.escape(cw) + r'(-|$)', slug) for cw in clean_words[:2]):
                        matched = True

                if not matched:
                    continue

                price_val, curr = None, ""
                p_info = find_fsto_price(slug, code)
                if p_info:
                    raw_us = p_info.get('US', '')
                    raw_fr = p_info.get('FR', '')
                    if raw_us:
                        m_num = re.search(r'(\d+[\.,]\d{2})', raw_us)
                        if m_num:
                            price_val = float(m_num.group(1).replace(',', '.'))
                            curr = "USD"
                    elif raw_fr:
                        m_num = re.search(r'(\d+[\.,]\d{2})', raw_fr)
                        if m_num:
                            price_val = float(m_num.group(1).replace(',', '.'))
                            curr = "EUR"

                author = it.get('author', {}).get('name', '').strip()
                link = it.get('link') or f"https://flightsim.to/store/product/{slug}"
                return True, link, price_val, curr, author

            return False, default_u, None, "", ""

        def check_aero(code):
            default_url = f"https://www.aerosoft.com/en/search?sSearch={code}"
            h = fetch_html(default_url)
            if not h:
                return False, default_url, None, "", ""

            matches = re.findall(r'<a\s+href=[\'"]([^\'"]*)[\'"]\s+class=[\'"][^\'"]*product--title[^\'"]*[\'"]\s+title=[\'"]([^\'"]*)[\'"]', h)
            
            clean_words = []
            if name_clean:
                words = re.split(r'[\s\-,/]+', name_clean)
                for w in words:
                    w_clean = re.sub(r'[^a-zA-Z]', '', w).strip()
                    if len(w_clean) >= 4 and w_clean.lower() not in ['airport', 'international', 'regional', 'national', 'field']:
                        clean_words.append(w_clean.lower())

            for link, title in matches:
                t_low = title.lower()
                l_low = link.lower()
                code_low = code.lower()
                # 1. Blacklist check
                if any(b in t_low for b in BLACKLIST_KEYWORDS) or any(b in l_low for b in BLACKLIST_KEYWORDS):
                    continue
                # 2. Simulator check (exclude X-Plane, P3D, FSX if not MSFS)
                if any(old in t_low or old in l_low for old in ['p3d', 'prepar3d', 'fsx', 'fs9', 'xp11', 'xp12', 'xp ', 'x-plane', 'xplane']) and 'msfs' not in t_low and 'msfs' not in l_low:
                    continue
                    
                matched = False
                if re.search(r'\b' + re.escape(code_low) + r'\b', t_low) or re.search(r'(^|[/\-_])' + re.escape(code_low) + r'([/\-_]|$)', l_low):
                    matched = True
                elif clean_words:
                    for cw in clean_words:
                        if re.search(r'\b' + re.escape(cw) + r'\b', t_low) or re.search(r'(^|[/\-_])' + re.escape(cw) + r'([/\-_]|$)', l_low):
                            matched = True
                            break

                if matched:
                    idx = h.find(link)
                    price_val = None
                    if idx != -1:
                        snippet = h[idx:idx+1800]
                        p_m = re.search(r'price--default[^>]*>[\s\S]*?(\d+[\.,]\d{2})', snippet)
                        if p_m:
                            price_val = float(p_m.group(1).replace(',', '.'))

                    dev_name = ""
                    m_lead = re.match(r'^(sim-wings|fsdg|stairport sceneries|stairport|flightbeam|flytampa|mk-studios|mk studios|justsim|drzewiecki design|prealsoft)\b', title, re.IGNORECASE)
                    if m_lead:
                        dev_name = m_lead.group(1)

                    return True, link, price_val, "EUR", dev_name

            return False, default_url, None, "", ""

        # Developer Direct Store Catalogs
        DEV_CATALOGS = {
            'Flightbeam': {
                'KSFO': 'https://shop.flightbeam.net/products/flightbeam-ksfo-captains-edition-msfs',
                'KPHX': 'https://shop.flightbeam.net/products/flightbeam-kphx',
                'KDEN': 'https://shop.flightbeam.net/products/flightbeam-kden-msfs',
                'KIAD': 'https://shop.flightbeam.net/products/flightbeam-kiad-for-msfs',
                'KMSP': 'https://shop.flightbeam.net/products/flightbeam-kmsp-msfs',
                'LFBO': 'https://shop.flightbeam.net/products/flightbeam-lfbo-msfs',
                'LFBZ': 'https://shop.flightbeam.net/products/flightbeam-lfbz',
                'NZAA': 'https://shop.flightbeam.net/products/flightbeam-nzaa-msfs',
                'NZWN': 'https://shop.flightbeam.net/products/flightbeam-nzwn-msfs',
                'LSGG': 'https://shop.flightbeam.net/collections/frontpage/products/jetstream-lsgg-geneva-airport-for-microsoft-flight-simulator',
                'LFPO': 'https://shop.flightbeam.net/products/jetstream-designs-lfpo',
                'LFRS': 'https://shop.flightbeam.net/products/jetstream-designs-lfrs',
                'LIML': 'https://shop.flightbeam.net/products/jetstream-designs-liml'
            },
            'FlyTampa': {
                'EHAM': 'https://www.flytampa.org/eham.html',
                'KLAS': 'https://www.flytampa.org/klas.html',
                'YSSY': 'https://www.flytampa.org/yssy.html',
                'CYYZ': 'https://www.flytampa.org/cyyz.html',
                'CYUL': 'https://www.flytampa.org/cyul.html',
                'LGAV': 'https://www.flytampa.org/lgav.html',
                'LGKR': 'https://www.flytampa.org/lgkr.html',
                'LGIR': 'https://www.flytampa.org/lgir.html',
                'LGTS': 'https://www.flytampa.org/lgts.html',
                'VHHX': 'https://www.flytampa.org/vhhx.html',
                'TNCM': 'https://www.flytampa.org/tncm.html',
                'EGNJ': 'https://www.flytampa.org/egnj.html',
                'LOWW': 'https://www.flytampa.org/loww.html',
                'KBOS': 'https://www.flytampa.org/kbos.html',
                'EKCH': 'https://www.flytampa.org/ekch.html'
            },
            'FSDreamTeam': {
                'KORD': 'https://www.fsdreamteam.com/products_kordv2_msfs.html',
                'CYVR': 'https://www.fsdreamteam.com/products_cyvr2_msfs.html',
                'LFSB': 'https://www.fsdreamteam.com/products_lfsb.html',
                'LSZH': 'https://www.fsdreamteam.com/products_zurich_msfs.html',
                'KEYW': 'https://www.fsdreamteam.com/products_keyw_msfs.html',
                'KSDF': 'https://www.fsdreamteam.com/products_ksdf_msfs.html',
                'KIAH': 'https://www.fsdreamteam.com/products_kiah_msfs.html',
                'KCLT': 'https://www.fsdreamteam.com/products_kclt_msfs.html',
                'LFEQ': 'https://www.fsdreamteam.com/products_lfeq_msfs.html',
                'LFNC': 'https://www.fsdreamteam.com/products_lfnc_msfs.html'
            },
            'Jetstream Designs': {
                'LSGG': 'https://www.jetstream-designs.com/lsgg-for-msfs',
                'LFPO': 'https://www.jetstream-designs.com/lfpo-for-msfs',
                'LFRS': 'https://www.jetstream-designs.com/lfrs-for-msfs',
                'LIML': 'https://www.jetstream-designs.com/liml-for-msfs'
            },
            'NZA Simulations': {
                'NZQN': 'https://nzasimulations.com/',
                'NZNS': 'https://nzasimulations.com/',
                'NZCH': 'https://nzasimulations.com/',
                'YMHB': 'https://nzasimulations.com/',
                'NZMC': 'https://nzasimulations.com/',
                'NZFJ': 'https://nzasimulations.com/',
                'NZWF': 'https://nzasimulations.com/'
            },
            'Pyreegue Dev Co.': {
                'EGBB': 'https://contrail.shop/products/pyreegue-egbb-birmingham-msfs-2020-2024',
                'EGPH': 'https://contrail.shop/products/pyreegue-egph-edinburgh-airport-v2-msfs',
                'EGPF': 'https://contrail.shop/products/egpf-glasgow-airport-msfs',
                'EGAA': 'https://contrail.shop/products/egaa-belfast-airport-msfs',
                'EGNX': 'https://contrail.shop/products/egnx-east-midlands-airport-msfs',
                'LYTV': 'https://contrail.shop/products/lytv-tivat-airport-msfs',
                'UKOO': 'https://contrail.shop/products/ukoo-odesa-airport-msfs',
                'UKLL': 'https://contrail.shop/products/ukll-lviv-airport-msfs'
            },
            'Drzewiecki Design': {
                'EPWA': 'https://drzewiecki-design.net/products.htm',
                'EPKK': 'https://drzewiecki-design.net/products.htm',
                'EPGD': 'https://drzewiecki-design.net/products.htm',
                'EPPO': 'https://drzewiecki-design.net/products.htm',
                'EPRZ': 'https://drzewiecki-design.net/products.htm',
                'KDCA': 'https://drzewiecki-design.net/products.htm',
                'KEWR': 'https://drzewiecki-design.net/products.htm',
                'KMDW': 'https://drzewiecki-design.net/products.htm',
                'KRNT': 'https://drzewiecki-design.net/products.htm',
                'KBFI': 'https://drzewiecki-design.net/products.htm',
                'KPAE': 'https://drzewiecki-design.net/products.htm'
            },
            'LatinVFR': {
                'KMIA': 'https://latinvfr.com/products/latinvfr-miami-kmia-msfs',
                'KFLL': 'https://latinvfr.com/products/fort-lauderdale-hollywood-intl-kfll-for-msfs',
                'LEBL': 'https://latinvfr.com/products/lvfr-barcelona-lebl-for-msfs',
                'LEMD': 'https://latinvfr.com/products/madrid-barajas-airport-lemd-and-city-for-msfs',
                'KMSY': 'https://latinvfr.com/products/new-orleans-international-airport-kmsy-for-msfs',
                'KBDL': 'https://latinvfr.com/products/latinvfr-bradley-kbdl-msfs',
                'KSAN': 'https://latinvfr.com/products/latinvfr-san-diego-intl-airport-ksan-msfs',
                'KBWI': 'https://latinvfr.com/products/baltimore-washington-kbwi-for-msfs',
                'KLSV': 'https://latinvfr.com/products/copy-of-madrid-barajas-airport-lemd-and-city-for-msfs',
                'KNKX': 'https://latinvfr.com/products/copy-of-fort-lauderdale-hollywood-intl-kfll-for-msfs',
                'SCEL': 'https://latinvfr.com/products/santiago-chile-scel-for-msfs',
                'TJSJ': 'https://latinvfr.com/products/san-juan-tjsj-for-msfs'
            }
        }

        PYREEGUE_PRICES = {
            'EGBB': (23.68, 'EUR'),
            'EGPH': (23.68, 'EUR'),
            'EGPF': (15.39, 'EUR'),
            'EGAA': (18.94, 'EUR'),
            'EGNX': (18.94, 'EUR'),
            'LYTV': (5.91, 'EUR'),
            'UKOO': (9.47, 'EUR'),
            'UKLL': (9.47, 'EUR')
        }

        LATINVFR_PRICES = {
            'KMIA': 8.99,
            'KFLL': 8.99,
            'LEBL': 8.99,
            'LEMD': 12.99,
            'KMSY': 12.49,
            'KBDL': 7.99,
            'KSAN': 7.99,
            'KBWI': 8.99,
            'KLSV': 5.99,
            'KNKX': 5.99,
            'SCEL': 8.99,
            'TJSJ': 8.99
        }

        def check_pyreegue(code):
            prod_url = DEV_CATALOGS['Pyreegue Dev Co.'].get(code)
            if prod_url:
                p_info = PYREEGUE_PRICES.get(code, (18.99, "EUR"))
                return True, prod_url, p_info[0], p_info[1], "Pyreegue Dev Co."
            return False, "https://contrail.shop/collections/pyreegue-dev-co", None, "", ""

        def check_latinvfr(code):
            prod_url = DEV_CATALOGS['LatinVFR'].get(code)
            if prod_url:
                price = LATINVFR_PRICES.get(code, 12.99)
                return True, prod_url, price, "USD", "LatinVFR"
            return False, f"https://latinvfr.com/search?q={code}", None, "", ""

        def check_flightbeam(code):
            prod_url = DEV_CATALOGS['Flightbeam'].get(code)
            if not prod_url:
                return False, f"https://shop.flightbeam.net/search?q={code}", None, "", ""
            dev_name = "Jetstream Designs" if 'jetstream' in prod_url.lower() else "Flightbeam Studios"
            try:
                req = urllib.request.Request(prod_url, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'fr-FR,fr;q=0.9'})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                    num_m = re.search(r'â‚¬\s*(\d+[\.,]\d{2})|(\d+[\.,]\d{2})\s*â‚¬', html)
                    if num_m:
                        val = num_m.group(1) or num_m.group(2)
                        return True, prod_url, float(val.replace(',', '.')), "EUR", dev_name
                    usd_m = re.search(r'\$\s*(\d+[\.,]\d{2})', html)
                    if usd_m:
                        return True, prod_url, float(usd_m.group(1).replace(',', '.')), "USD", dev_name
            except Exception:
                pass
            try:
                json_u = prod_url.split('?')[0] + '.json'
                req = urllib.request.Request(json_u, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    d = json.loads(resp.read().decode('utf-8'))
                    v = d.get('product', {}).get('variants', [{}])[0]
                    if v.get('price'):
                        return True, prod_url, float(v['price']), "USD", dev_name
            except Exception:
                pass
            return True, prod_url, None, "", dev_name

        def check_francevfr(code):
            u = f"https://www.vfrnetwork.com/shop/fr/recherche?controller=search&s={code}"
            h = fetch_html(u)
            if not h or 'product-miniature' not in h:
                return False, u, None, "", ""
            articles = re.findall(r'<article[^>]*class=[\'"][^\'"]*product-miniature[\s\S]*?</article>', h)
            for art in articles:
                t_m = re.search(r'product-title[\s\S]*?<a[^>]*>([\s\S]*?)</a>', art)
                title = re.sub(r'<[^>]+>', '', t_m.group(1)).strip() if t_m else ""
                if any(b_kw in title.lower() for b_kw in BLACKLIST_KEYWORDS):
                    continue
                if re.search(r'\b' + re.escape(code) + r'\b', title, re.IGNORECASE):
                    p_m = re.search(r'<span[^>]*class=[\'"][^\'"]*price[^\'"]*[\'"][^>]*>([\s\S]*?)</div>', art)
                    price_val = None
                    if p_m:
                        raw_p = re.sub(r'<[^>]+>', '', p_m.group(1)).replace('\xa0', ' ').strip()
                        num_m = re.search(r'(\d+[\.,]\d{2})', raw_p)
                        if num_m:
                            price_val = float(num_m.group(1).replace(',', '.'))
                    return True, u, price_val, "EUR", "France VFR"
            return False, u, None, "", ""

        def check_contrail(code):
            u = f"https://contrail.shop/search/suggest.json?q={code}&resources[type]=product"
            fallback_u = f"https://contrail.shop/search?q={code}"
            try:
                req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    products = data.get('resources', {}).get('results', {}).get('products', [])
                    for p in products:
                        title = p.get('title', '')
                        handle = p.get('handle', '')
                        if re.search(r'\b' + re.escape(code) + r'\b', title, re.IGNORECASE) or re.search(r'\b' + re.escape(code) + r'\b', handle, re.IGNORECASE):
                            price = float(p.get('price')) if p.get('price') else None
                            prod_url = f"https://contrail.shop/products/{handle}"
                            dev_name = p.get('vendor') or ""
                            return True, prod_url, price, "EUR", dev_name
            except Exception:
                pass
            return False, fallback_u, None, "", ""

        stores_def = [
            ("France VFR", check_francevfr, "", "dev"),
            ("Flightbeam Studios", check_flightbeam, "", "dev"),
            ("FlyTampa", lambda c: (c in DEV_CATALOGS['FlyTampa'], DEV_CATALOGS['FlyTampa'].get(c, "https://www.flytampa.org/"), 21.99, "USD", "FlyTampa"), "", "dev"),
            ("FSDreamTeam", lambda c: (c in DEV_CATALOGS['FSDreamTeam'], DEV_CATALOGS['FSDreamTeam'].get(c, "https://www.fsdreamteam.com/products_msfs.html"), 19.99, "USD", "FSDreamTeam"), "", "dev"),
            ("Jetstream Designs", lambda c: (c in DEV_CATALOGS['Jetstream Designs'], DEV_CATALOGS['Jetstream Designs'].get(c, "https://www.jetstream-designs.com/"), None, "", "Jetstream Designs"), "", "dev"),
            ("NZA Simulations", lambda c: (c in DEV_CATALOGS['NZA Simulations'], DEV_CATALOGS['NZA Simulations'].get(c, "https://nzasimulations.com/"), 24.99, "AUD", "NZA Simulations"), "", "dev"),
            ("Pyreegue Dev Co.", check_pyreegue, "", "dev"),
            ("Drzewiecki Design", lambda c: (c in DEV_CATALOGS['Drzewiecki Design'], DEV_CATALOGS['Drzewiecki Design'].get(c, "https://drzewiecki-design.net/products.htm"), 21.00, "EUR", "Drzewiecki Design"), "", "dev"),
            ("LatinVFR", check_latinvfr, "", "dev"),
            ("simMarket", check_sm, "", "market"),
            ("Orbx Direct", check_orbx, "", "market"),
            ("Flightsim.to Store", check_fsto, "", "market"),
            ("iniBuilds Store", check_ini, "", "market"),
            ("Aerosoft Shop", check_aero, "", "market"),
            ("Contrail Web Shop", check_contrail, "", "market")
        ]

        results = []
        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = {ex.submit(fn, icao_clean): (name, desc, st_type) for name, fn, desc, st_type in stores_def}
            for fut in futures:
                name, desc, st_type = futures[fut]
                try:
                    res = fut.result()
                    found = res[0]
                    final_url = res[1]
                    price = res[2] if len(res) > 2 else None
                    curr = res[3] if len(res) > 3 else ""
                    developer = res[4] if len(res) > 4 else ""
                except Exception:
                    found, final_url, price, curr, developer = False, "", None, "", ""
                results.append({
                    "name": name,
                    "url": final_url,
                    "desc": desc,
                    "found": found,
                    "type": st_type,
                    "price": price,
                    "currency": curr,
                    "developer": developer
                })

        # Order: dev stores with found=True first, then available market stores, then unavailable market stores
        def sort_key(x):
            is_found = 0 if x.get("found") else 1
            is_dev = 0 if x.get("type") == "dev" else 1
            return (is_found, is_dev)

        results.sort(key=sort_key)

        self._payware_store_cache[cache_key] = results
        return json.dumps(results)

    def export_collection_json(self, airports_json_str):
        try:
            airports = json.loads(airports_json_str)
            window = webview.windows[0]
            exports_dir = self.get_exports_dir()
            result = window.create_file_dialog(
                webview.SAVE_DIALOG,
                directory=exports_dir,
                save_filename="SceneryX_Collection.json",
                file_types=('JSON Files (*.json)', 'All files (*.*)')
            )
            if not result:
                return json.dumps({"status": "cancelled"})
            
            file_path = result[0] if isinstance(result, (list, tuple)) else result
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(airports, f, indent=2, ensure_ascii=False)
                
            return json.dumps({"status": "ok", "path": file_path, "count": len(airports)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # =========================================================================
    # SUITE PERFORMANCE : FLIGHT RIG OPTIMIZER & LIVE BLACKBOX TELEMETRY
    # =========================================================================

    def get_rig_diagnostics(self, flight_profile='LINER', vr_refresh_rate=72, preferred_display_id=None, profile_id=None):
        try:
            data = flight_rig_optimizer.get_full_rig_diagnostics(flight_profile=flight_profile, vr_refresh_rate=vr_refresh_rate, preferred_display_id=preferred_display_id, profile_id=profile_id)
            return json.dumps(data, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def calculate_rig_profile(self, user_specs_json):
        try:
            specs = json.loads(user_specs_json) if isinstance(user_specs_json, str) else user_specs_json
            profile = flight_rig_optimizer.generate_optimized_rig_profile(specs)
            return json.dumps(profile, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def update_msfs_setting(self, mode, setting_key, new_value):
        try:
            res = flight_rig_optimizer.stage_msfs_setting(mode, setting_key, new_value)
            flight_rig_optimizer.update_msfs_user_cfg_setting(mode, setting_key, new_value, create_backup=False)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def apply_recommended_msfs_settings(self, mode, flight_profile='LINER', vr_refresh_rate=72, preferred_display_id=None):
        try:
            res = flight_rig_optimizer.apply_recommended_msfs_settings(mode, flight_profile=flight_profile, vr_refresh_rate=vr_refresh_rate, preferred_display_id=preferred_display_id)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def get_user_cfg_backups(self):
        try:
            backups = flight_rig_optimizer.get_available_user_cfg_backups()
            return json.dumps(backups, ensure_ascii=False)
        except Exception as e:
            return json.dumps([], ensure_ascii=False)

    def restore_user_cfg_backup(self, backup_name):
        try:
            res = flight_rig_optimizer.restore_user_cfg_backup(backup_name)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def delete_user_cfg_backup(self, backup_name):
        try:
            res = flight_rig_optimizer.delete_user_cfg_backup(backup_name)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def open_user_cfg_folder(self):
        try:
            res = flight_rig_optimizer.open_user_cfg_folder()
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def restore_original_user_cfg(self):
        try:
            res = flight_rig_optimizer.restore_original_user_cfg()
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def get_custom_profiles(self):
        try:
            profiles = flight_rig_optimizer.get_custom_profiles()
            return json.dumps(profiles, ensure_ascii=False)
        except Exception as e:
            return json.dumps([], ensure_ascii=False)

    def save_custom_profile(self, profile_name, overwrite_id=None):
        try:
            res = flight_rig_optimizer.save_custom_profile(profile_name, overwrite_id=overwrite_id)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def check_profile_changes(self, profile_id):
        try:
            res = flight_rig_optimizer.check_profile_changes(profile_id)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def rename_custom_profile(self, profile_id, new_name):
        try:
            res = flight_rig_optimizer.rename_custom_profile(profile_id, new_name)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def activate_custom_profile(self, profile_id):
        try:
            res = flight_rig_optimizer.activate_custom_profile(profile_id)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def delete_custom_profile(self, profile_id):
        try:
            res = flight_rig_optimizer.delete_custom_profile(profile_id)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def ensure_active_profile_applied(self):
        try:
            res = flight_rig_optimizer.ensure_active_profile_applied()
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def apply_staged_settings_to_user_cfg(self):
        try:
            res = flight_rig_optimizer.apply_staged_user_cfg_to_disk()
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def get_system_tuning_status(self):
        try:
            res = flight_rig_optimizer.get_system_tuning_status()
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def get_sim_maintenance_status(self):
        try:
            res = flight_rig_optimizer.get_sim_maintenance_status()
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def toggle_community_safe_update_mode(self, target_action=None):
        try:
            res = flight_rig_optimizer.toggle_community_safe_update_mode(target_action)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def run_sim_maintenance_action(self, action_id):
        try:
            res = flight_rig_optimizer.run_sim_maintenance_action(str(action_id))
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def set_system_game_mode(self, enable):
        try:
            ok = flight_rig_optimizer.set_windows_game_mode(bool(enable))
            refreshed = flight_rig_optimizer.get_system_tuning_status()
            refreshed["status"] = "success" if ok else "error"
            refreshed["success"] = ok
            refreshed["message"] = "Game mode updated successfully." if ok else "Failed to update Game mode in Windows registry."
            return json.dumps(refreshed, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e), "success": False}, ensure_ascii=False)

    def set_system_power_plan(self, plan_guid):
        try:
            ok = flight_rig_optimizer.set_windows_power_plan(str(plan_guid))
            refreshed = flight_rig_optimizer.get_system_tuning_status()
            refreshed["status"] = "success" if ok else "error"
            refreshed["success"] = ok
            refreshed["message"] = "Power plan updated successfully." if ok else "Failed to activate power plan."
            return json.dumps(refreshed, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e), "success": False}, ensure_ascii=False)

    def open_windows_graphics_settings(self):
        try:
            ok = flight_rig_optimizer.open_windows_graphics_settings()
            return json.dumps({"status": "ok" if ok else "error"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def launch_gpu_control_app(self):
        try:
            ok = flight_rig_optimizer.launch_gpu_control_app()
            return json.dumps({"status": "ok" if ok else "error"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def open_windows_power_options(self):
        try:
            ok = flight_rig_optimizer.open_windows_power_options()
            return json.dumps({"status": "ok" if ok else "error"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def open_shader_cache_settings(self):
        try:
            ok = flight_rig_optimizer.open_shader_cache_settings()
            return json.dumps({"status": "ok" if ok else "error"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def set_system_hags(self, enable):
        try:
            res = flight_rig_optimizer.set_windows_hags(bool(enable))
            refreshed = flight_rig_optimizer.get_system_tuning_status()
            refreshed["operation_result"] = res
            return json.dumps(refreshed, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e), "success": False}, ensure_ascii=False)

    def purge_shader_cache(self):
        try:
            res = flight_rig_optimizer.purge_shader_cache()
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e), "success": False}, ensure_ascii=False)

    def open_nvidia_control_panel(self):
        try:
            ok = flight_rig_optimizer.open_nvidia_control_panel()
            return json.dumps({"status": "ok" if ok else "error"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def open_windows_disk_cleanup(self):
        try:
            ok = flight_rig_optimizer.open_windows_disk_cleanup()
            return json.dumps({"status": "ok" if ok else "error"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def open_external_url(self, url):
        try:
            import webbrowser
            if url and (url.startswith("http://") or url.startswith("https://")):
                webbrowser.open(url)
                return json.dumps({"status": "ok"}, ensure_ascii=False)
            return json.dumps({"status": "error", "message": "Invalid URL protocol"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def apply_all_recommended_system_tweaks(self):
        try:
            res = flight_rig_optimizer.apply_all_recommended_system_tweaks()
            res["status"] = "success"
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e), "success": False}, ensure_ascii=False)

    def start_flight_blackbox(self, flight_name, dep_icao, arr_icao, aircraft):
        try:
            st = get_settings()
            fm = st.get('flight_mode', {})
            is_corridor = bool(fm.get('active') and fm.get('profile') in ('DIRECT', 'CORRIDOR', 'SIMBRIEF'))
            has_active_simbrief = bool(fm.get('active') and fm.get('profile') == 'SIMBRIEF')

            if has_active_simbrief:
                sb = fm.get('simbrief_flight') or flight_perf_tracker.get_simbrief_flight_plan(force_refresh=True)
                if sb and isinstance(sb, dict):
                    sb_orig = sb.get('origin', {}).get('icao')
                    sb_dest = sb.get('destination', {}).get('icao')
                    if sb_orig and (not dep_icao or dep_icao == 'DEP'): dep_icao = sb_orig
                    if sb_dest and (not arr_icao or arr_icao == 'ARR'): arr_icao = sb_dest

            res = flight_perf_tracker.BLACKBOX.start(flight_name=flight_name, dep=dep_icao, arr=arr_icao, aircraft=aircraft)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def stop_flight_blackbox(self):
        try:
            res = flight_perf_tracker.BLACKBOX.stop()
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def get_resumable_blackbox_session(self):
        try:
            res = flight_perf_tracker.BLACKBOX.get_resumable_session()
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"has_resumable": False, "error": str(e)}, ensure_ascii=False)

    def resume_flight_blackbox(self):
        try:
            res = flight_perf_tracker.BLACKBOX.resume_session()
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def end_resumable_blackbox_session(self, generate_report=True):
        try:
            res = flight_perf_tracker.BLACKBOX.end_resumable_session(generate_report=bool(generate_report))
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def resolve_monitoring_on_exit(self, keep_for_resume=True):
        try:
            if keep_for_resume:
                flight_perf_tracker.BLACKBOX.suspend_for_resume()
            else:
                flight_perf_tracker.BLACKBOX.stop()

            st = get_settings()
            fm = st.get('flight_mode', {})
            if isinstance(fm, dict) and fm.get('active'):
                return json.dumps({"status": "ok", "needs_flight_mode_prompt": True}, ensure_ascii=False)

            self.exit_app(False)
            return json.dumps({"status": "ok", "needs_flight_mode_prompt": False}, ensure_ascii=False)
        except Exception as e:
            self.exit_app(False)
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def _parse_version_tuple(self, ver_str):
        if not ver_str:
            return (0, 0, 0)
        m = re.search(r'(\d+)\.(\d+)\.(\d+)', str(ver_str))
        if m:
            return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return (0, 0, 0)

    @staticmethod
    def _normalize_version_tag(ver_str):
        if not ver_str:
            return ver_str
        return re.sub(r'^RC_v?', 'PRO_', str(ver_str).strip(), flags=re.IGNORECASE)

    def _get_current_app_version(self):
        if IS_LITE:
            return APP_VERSION
        # 1. Read bundled web/index.html version string first
        try:
            html_path = get_resource_file_path(os.path.join('web', 'index.html'))
            if html_path and os.path.exists(html_path):
                with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                m = re.search(r'title="SceneryX\s+((?:PRO_|LITE_|RC_(?:v)?)\d+\.\d+\.\d+(?:-LITE)?)"', content)
                if not m:
                    m = re.search(r'((?:PRO_|LITE_|RC_(?:v)?)\d+\.\d+\.\d+(?:-LITE)?)\s*(?:â€¢\s*)?&copy;', content)
                if m:
                    return self._normalize_version_tag(m.group(1).strip())
        except Exception:
            pass
        # 2. Fallback to Windows Registry
        try:
            import winreg
            for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(root, r"Software\SceneryX") as key:
                        val, _ = winreg.QueryValueEx(key, "Version")
                        if val:
                            return self._normalize_version_tag(str(val).strip())
                except Exception:
                    continue
        except Exception:
            pass
        return self._normalize_version_tag(APP_VERSION or ("LITE_1.1.0" if IS_LITE else "PRO_1.1.0"))

    PATCHES_REPO_RAW_BASE = "https://raw.githubusercontent.com/wildbill75/SceneryX/Updates/patches"
    PATCHES_MANIFEST_URL = "https://raw.githubusercontent.com/wildbill75/SceneryX/Updates/patches/version.json"

    _PATCH_1_1_1_CHANGELOG_BODY = (
        "**Release Date:** October 18, 2026\n"
        "**Channel:** `Updates/patches`\n\n"
        "## What's New & Fixed\n\n"
        "### 1. My Rig â€” Update & Cache Cleaner\n"
        "- **Safe Update Mode (Community Quarantine):** Added 1-click Community folder quarantine (`PREPARE FOR UPDATE` / restore) in **My Rig > Update & Cache Cleaner** to safely park and restore your Community add-ons before and after MSFS Sim Updates.\n"
        "- **MSFS & GPU Shader Cache Cleaner:** Added real-time scanning and 1-click cleanup (`PURGE ALL CACHES` or individual purge) for MSFS SceneryIndexes, Rolling Cache, StreamedPackages cache, WASM/Aircraft state caches, and DirectX / NVIDIA / AMD GPU Shader Caches.\n\n"
        "### 2. Live Telemetry & MSFS In-Game Panel Synchronization\n"
        "- **Bi-Directional Monitoring Sync:** Starting or stopping Flight Monitoring from either the MSFS In-Game Panel or the SceneryX desktop app now synchronizes immediately across both interfaces.\n"
        "- **Real-Time Sidebar Counter:** Fixed the `TELEMETRY` elapsed time counter badge (`00:01`, `00:02`...) in the left navigation bar so it updates live as soon as monitoring starts.\n"
        "- **30S Trend Sparkline Control:** Clicking `STOP MONITORING` now immediately halts the live `30S TREND` graph and returns the telemetry display to `STANDBY`.\n"
        "- **Post-Flight Report Generation:** Resolved an issue where stopping telemetry from the In-Game Panel did not trigger flight report generation in SceneryX.\n\n"
        "### 3. Route & Airport City Name Harmonization & Onboarding Fix\n"
        "- **Clean Metropolitan City Names:** Harmonized airport city labels across SimBrief plans, Live Flight Monitoring, and Post-Flight Reports (e.g., `LGAV (Athens)` instead of municipality names like `Spata-Artemida`).\n"
        "- **Onboarding Flight Optimizer Restore:** Fixed an issue where the `FLIGHT OPTIMIZER` sidebar menu remained hidden at the end of the interactive onboarding tour until clicking on the map.\n\n"
        "### 4. Automated Update & Patch Pipeline\n"
        "- **Unified Versioning (`PRO_1.1.1`):** Unified release versioning into `PRO_X.X.X` and `LITE_X.X.X`.\n"
        "- **Automatic Update Detection:** SceneryX automatically checks the `Updates/patches` Git branch on startup and offers 1-click patch installation while preserving all user settings, custom profiles, and scenery states.\n"
        "- **Post-Update Changelog Modal:** Displays the patch release notes (`README.md`) automatically after installing an update."
    )

    _PATCH_1_1_2_CHANGELOG_BODY = (
        "**Release Date:** October 19, 2026\n"
        "**Channel:** `Updates/patches`\n\n"
        "## What's New & Fixed\n\n"
        "### 1. MSFS In-Game Panel â€” Live Graphics Tuning Accordion & 5-Pin Header\n"
        "- **Live RAM Graphics Tuning (No Restart Required):** Added an expandable accordion in the MSFS In-Game Panel allowing real-time in-flight adjustment of the 8 live-modifiable MSFS graphics settings (`Max FPS`, `Volumetric Clouds`, `Terrain Pre-Caching`, `Terrain Shadows`, `Buildings`, `Trees`, `Plants`, and `Grass`).\n"
        "- **Dual-Write RAM + Profile Persistence:** Clicking `APPLY` injects the changes directly into MSFS memory (2D & VR) and automatically saves them into your active SceneryX profile and `UserCfg.opt`.\n"
        "- **Customizable 5-Pin Top Bar:** Pin up to 5 favorite parameters to keep their live values visible at a glance when the accordion is collapsed.\n"
        "- **Smart Cloud Override Protection:** Manually changing `Volumetric Clouds` and clicking `APPLY` while in flight automatically turns `Auto Cloud Recovery` `OFF` so your manual cloud setting is respected.\n\n"
        "### 2. Smart LOD & Auto Cloud Recovery Enhancements\n"
        "- **Live Cloud Quality Display & Ultra Boost:** Added real-time `LIVE : LOW / MEDIUM / HIGH / ULTRA` cloud quality indicators in both the MSFS In-Game Panel and the SceneryX Smart LOD window, with automatic recovery and boost up to `ULTRA` when GPU headroom allows.\n"
        "- **Instant Smart LOD Re-Engagement:** Resolved an issue in the In-Game Panel where re-enabling `SMART LOD REGULATION` (`ON`) after manual slider overrides required toggling `ON/OFF` twice to resume automatic regulation.\n\n"
        "### 3. Post-Flight Report â€” Velocity-Aware Timeline Zoom & Pan\n"
        "- **Duration-Scaled & Velocity-Aware Wheel Zoom:** Redesigned the Post-Flight Report chart zoom to scale dynamically with flight duration and mouse wheel scroll speed, making zooming into long flights effortless.\n"
        "- **Hard-Stop Minimum Window (No Disappearing Graphs):** Added a strict minimum 8-sample zoom floor (`minSpan`) and synchronized drag-to-pan across all flight report charts so curves never disappear at maximum zoom."
    )

    _PATCH_1_1_3_CHANGELOG_BODY = (
        "**Release Date:** October 19, 2026\n"
        "**Channel:** `Updates/patches`\n\n"
        "## What's New & Fixed\n\n"
        "### 1. MSFS In-Game Panel â€” Independent Auto Cloud Recovery, Per-Setting Reset (`â†º`) & Enlarged Controls\n"
        "- **Independent Auto Cloud Recovery:** `AUTO CLOUD RECOVERY` now operates independently even when `SMART LOD REGULATION` (`TLOD`/`OLOD`) is turned `OFF`, continuously monitoring FPS/MainThread headroom and displaying real-time `LIVE : LOW / MEDIUM / HIGH / ULTRA` cloud status.\n"
        "- **Per-Setting Baseline Reset (`â†º`):** Added individual reset (`â†º`) buttons next to each of the 8 hot-swappable graphics parameters in the In-Game Panel to instantly restore any setting back to its pre-flight baseline.\n"
        "- **Refined Cockpit UI Ergonomics:** Enlarged the Live Graphics Tuning accordion controls, quick-pin badges, and default cockpit panel dimensions for effortless readability in both 2D and VR.\n\n"
        "### 2. MSFS 2024 Store / Marketplace (`StreamedPackages`) Detection & Startup Modal Queue\n"
        "- **Multi-Source Package Snapshot Tracking:** Upgraded `library_snapshot.json` to track all installed packages per airport across `Community`, `Official`, and `MSFS 2024 StreamedPackages`. Installing a new Store/Marketplace or Community airport for an ICAO that already had a base package now reliably triggers the **Library Changes Detected** modal on startup.\n"
        "- **Non-Overlapping Startup Modal Sequence:** Synchronized startup modals so Background Tools alerts (`AutoFPS` / `OFXR`) wait until you close the **Library Changes Detected** summary instead of overlapping it.\n\n"
        "### 3. Interactive Onboarding Tour Expansion (29 Steps) & First-Launch Indexing Polish\n"
        "- **New Guided Tour Steps:** Added dedicated interactive steps for **My Rig > Update & Cache Cleaner** (Safe Update Quarantine & Shader/WASM Cache Purge), updated **In-Game Panel in Cockpit** (Smart LOD & Performance Telemetry), and added **In-Flight Live Graphics Controls** (hot-swappable settings & 5-pin quick bar).\n"
        "- **Streamlined First-Launch Indexing:** Prevented redundant pre-disclaimer library scans on first launch and ensured instant ICAO search indexing and GSX profile badge initialization right after the initial database build."
    )

    _PATCH_1_1_4_CHANGELOG_BODY = (
        "**Release Date:** October 20, 2026\n"
        "**Channel:** `Updates/patches`\n\n"
        "## What's New & Fixed\n\n"
        "### 1. Smart LOD Governor & MSFS In-Game Panel â€” Live Memory Engine & Manual Mode Fix\n"
        "- **MSFS 2024 Live Memory Offset & Automatic Signature Scanner:** Updated the Win32 Memory Engine base offset (`0x0A80B024`) for the latest `FlightSimulator2024.exe` build and added an automatic `.data` signature scanner so live `TLOD`, `OLOD`, `Clouds`, and hot-swappable graphics writes attach in Read/Write mode across all MSFS 2024 updates.\n"
        "- **Persistent Manual Mode (`MAN`) Disengagement:** Fixed an issue in both the MSFS In-Game Panel and the SceneryX internal Smart LOD window where disabling Smart LOD (`OFF`) or disengaging directly by dragging the `TLOD` / `OLOD` sliders caused Smart LOD to snap back to `ON` after ~2 seconds.\n"
        "- **Automatic In-Game Panel Refresh on Startup:** SceneryX Pro now automatically refreshes the installed **SceneryX In-Game Panel** in your MSFS `Community` folder on startup whenever a patch update is applied.\n\n"
        "### 2. Custom Graphics Profiles â€” Independent Profile Saving & Switching Fix\n"
        "- **Protected Active Profile Presets:** Changing individual settings in the Graphics Settings matrix no longer silently overwrites the currently active `.profile.json` file on disk before clicking `SAVE PROFILE`, allowing you to tweak settings and save them as a brand-new profile (e.g., `2D Display ULTRA`) without altering your baseline profile (`2D Display Standard`).\n"
        "- **Instant Matrix Refresh on Profile Switch:** Selecting a profile from the dropdown immediately loads and renders that profile's exact saved configuration in the Graphics Settings matrix and applies it to `UserCfg.opt`."
    )

    _PATCH_1_1_6_CHANGELOG_BODY = (
        "**Release Date:** October 21, 2026\n"
        "**Channel:** `Updates/patches`\n\n"
        "## What's New & Fixed (Includes v1.1.5 & v1.1.6)\n\n"
        "### 1. MSFS 2020/2024 In-Game Panel (`sceneryx-ingame-panel`)\n"
        "- **Dynamic Auto-Height Window:** The MSFS In-Game Panel now automatically wraps its vertical height to match its content in real time (when expanding/collapsing the Live Graphics drawer or switching between Offline/Online states) while remaining horizontally resizable.\n"
        "- **Full EN/FR Localization & Contextual Tooltips:** Added full English and French localization synchronized with SceneryX, plus resilient hover tooltips across all Live Graphics controls, Smart LOD sliders, Cloud Recovery, and Performance metrics.\n"
        "- **Clean Package Naming & Auto-Refresh:** Standardized the Community package folder name to `sceneryx-ingame-panel` (automatically migrating legacy panel folders on startup) and preserved the `SCENERY X` panel header.\n\n"
        "### 2. Smart LOD Governor & Live Memory Engine\n"
        "- **MSFS 2024 Live Memory Offset & Signature Scanner:** Updated the Win32 Memory Engine base offset (`0x0A80B024`) for the latest `FlightSimulator2024.exe` build and added an automatic `.data` signature scanner so live `TLOD`, `OLOD`, `Clouds`, and hot-swappable graphics writes attach reliably in Read/Write mode.\n"
        "- **Persistent Manual Mode (`MAN`) Disengagement:** Fixed an issue in both the MSFS In-Game Panel and the SceneryX Smart LOD window where disabling Smart LOD (`OFF`) or dragging the `TLOD` / `OLOD` sliders manually caused Smart LOD to snap back to `ON` after ~2 seconds.\n\n"
        "### 3. Custom Graphics Profiles & Scenery / GSX Conflict Scanner\n"
        "- **Independent Profile Saving & Switching:** Modifying individual settings in the Graphics Settings matrix no longer overwrites the active `.profile.json` file before clicking `SAVE PROFILE`, and switching profiles immediately refreshes the matrix and `UserCfg.opt`.\n"
        "- **Duplicate Scenery & GSX Detection Fix:** Restored full multi-layer duplicate airport detection across `Community`, `Official`, `StreamedPackages`, and Addon Linker folders, as well as GSX profile conflict scanning during package rescans."
    )

    _PATCH_1_1_6_CHANGELOG_BODY_FR = (
        "**Date de publication :** 21 Octobre 2026\n"
        "**Canal :** `Updates/patches`\n\n"
        "## Nouveautés et Corrections (Inclut v1.1.5 & v1.1.6)\n\n"
        "### 1. Panneau en jeu MSFS 2020/2024 (`sceneryx-ingame-panel`)\n"
        "- **Ajustement automatique de la hauteur :** Le panneau en jeu MSFS adapte désormais automatiquement sa hauteur verticale à son contenu en temps réel (ouverture/fermeture du tiroir Live Graphics, passage Hors-ligne / En ligne) tout en restant redimensionnable en largeur.\n"
        "- **Traduction complète EN/FR & Info-bulles contextuelles :** Ajout de la localisation complète en français et en anglais synchronisée avec SceneryX, ainsi que d'info-bulles contextuelles sur l'ensemble des réglages Live Graphics, curseurs Smart LOD, Auto Cloud Recovery et jauges de performance.\n"
        "- **Nommage unifié & Mise à jour auto :** Le package Community se nomme désormais `sceneryx-ingame-panel` (avec migration automatique de l'ancien dossier au démarrage) tout en conservant le titre `SCENERY X` dans l'en-tête.\n\n"
        "### 2. Régulation Smart LOD & Moteur Mémoire Temps Réel\n"
        "- **Offset mémoire MSFS 2024 & Scanner de signature :** Mise à jour de l'offset mémoire (`0x0A80B024`) pour la dernière version de `FlightSimulator2024.exe` avec scanner automatique de signature `.data` assurant l'écriture en direct (`TLOD`, `OLOD`, `Nuages` et réglages graphiques).\n"
        "- **Maintien du mode Manuel (`MAN`) :** Correction d'un bug dans le panneau en jeu et la fenêtre Smart LOD où la désactivation du Smart LOD (`OFF`) ou le déplacement manuel des curseurs `TLOD` / `OLOD` réactivait le mode `ON` au bout de 2 secondes.\n\n"
        "### 3. Profils Graphiques & Détection des doublons Scènes / GSX\n"
        "- **Sauvegarde et bascule de profils indépendantes :** Modifier un réglage dans la matrice graphique n'écrase plus le fichier `.profile.json` actif avant d'avoir cliqué sur `SAUVEGARDER LE PROFIL`, et le changement de profil met immédiatement à jour la matrice et `UserCfg.opt`.\n"
        "- **Détection des doublons Scènes & GSX :** Restauration complète de la détection des doublons d'aéroports multi-dossiers (`Community`, `Official`, `StreamedPackages`, Addon Linker) et des conflits de profils GSX lors du Re-scan Packages."
    )

    DEFAULT_PATCH_CHANGELOGS = {
        "PRO_1.1.1": "# SceneryX — Patch PRO_1.1.1 (Day-One Update)\n\n" + _PATCH_1_1_1_CHANGELOG_BODY,
        "PRO_1.1.2": "# SceneryX — Patch PRO_1.1.2\n\n" + _PATCH_1_1_2_CHANGELOG_BODY,
        "PRO_1.1.3": "# SceneryX — Patch PRO_1.1.3\n\n" + _PATCH_1_1_3_CHANGELOG_BODY,
        "PRO_1.1.4": "# SceneryX — Patch PRO_1.1.4\n\n" + _PATCH_1_1_4_CHANGELOG_BODY,
        "PRO_1.1.5": "# SceneryX — Patch PRO_1.1.5\n\n" + _PATCH_1_1_4_CHANGELOG_BODY,
        "PRO_1.1.6": "# SceneryX — Patch PRO_1.1.6\n\n" + _PATCH_1_1_6_CHANGELOG_BODY,
    }

    DEFAULT_PATCH_CHANGELOGS_FR = {
        "PRO_1.1.5": "# SceneryX — Patch PRO_1.1.5\n\n" + _PATCH_1_1_6_CHANGELOG_BODY_FR,
        "PRO_1.1.6": "# SceneryX — Patch PRO_1.1.6\n\n" + _PATCH_1_1_6_CHANGELOG_BODY_FR,
    }

    def _fetch_remote_text(self, url, timeout=3.5):
        try:
            sep = "&" if "?" in url else "?"
            bust_url = f"{url}{sep}t={int(time.time())}"
            req = urllib.request.Request(
                bust_url,
                headers={"User-Agent": "SceneryX-Updater/1.1", "Cache-Control": "no-cache"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    return resp.read().decode("utf-8-sig", errors="replace")
        except Exception:
            pass
        return None

    def _get_patch_changelog_markdown(self, version_tag, readme_url=None, lang=None):
        if not version_tag:
            return ""
        norm_tag = self._normalize_version_tag(version_tag)
        if not lang:
            try:
                lang = str(get_settings().get("language", "en")).strip().lower()
            except Exception:
                lang = "en"
        is_fr = str(lang).startswith("fr")

        if is_fr and norm_tag in self.DEFAULT_PATCH_CHANGELOGS_FR:
            return self.DEFAULT_PATCH_CHANGELOGS_FR[norm_tag]

        # Strictly fetch version-specific README.md from the Git Updates/patches branch
        urls_to_try = []
        if is_fr:
            urls_to_try.append(f"{self.PATCHES_REPO_RAW_BASE}/patches/{norm_tag}/README_FR.md")
        if readme_url and f"/{norm_tag}/" in readme_url:
            urls_to_try.append(readme_url)
        urls_to_try.append(f"{self.PATCHES_REPO_RAW_BASE}/patches/{norm_tag}/README.md")
        for u in urls_to_try:
            txt = self._fetch_remote_text(u, timeout=4.0)
            if txt and len(txt.strip()) > 20 and "img.shields.io" not in txt and ("Patch" in txt or "What's New" in txt or "Nouveautés" in txt or norm_tag in txt):
                return re.sub(r'\bRC_v?', 'PRO_', txt.strip())

        if is_fr:
            return self.DEFAULT_PATCH_CHANGELOGS_FR.get(
                norm_tag,
                f"# SceneryX — Patch {norm_tag}\n\nLe patch **{norm_tag}** a été installé avec succès.\nTous vos paramètres utilisateur, profils personnalisés et configurations de scènes ont été préservés."
            )
        return self.DEFAULT_PATCH_CHANGELOGS.get(
            norm_tag,
            f"# SceneryX — Patch {norm_tag}\n\nPatch **{norm_tag}** has been successfully installed.\nAll your user settings, custom profiles, and scenery configurations have been preserved."
        )

    def check_available_patch(self):
        if IS_LITE:
            return json.dumps({"has_patch": False, "current_version": APP_VERSION, "is_lite": True}, ensure_ascii=False)
        try:
            current_ver = self._get_current_app_version()
            cur_tuple = self._parse_version_tuple(current_ver)
            if cur_tuple == (0, 0, 0):
                return json.dumps({"has_patch": False}, ensure_ascii=False)

            # Strictly check remote GitHub Updates/patches branch manifest
            raw_manifest = self._fetch_remote_text(self.PATCHES_MANIFEST_URL, timeout=5.0)
            if raw_manifest:
                try:
                    mdata = json.loads(raw_manifest)
                    rem_ver = self._normalize_version_tag(mdata.get("latest_version") or mdata.get("version"))
                    rem_tuple = self._parse_version_tuple(rem_ver)
                    if rem_ver and rem_tuple > cur_tuple:
                        best_ver = str(rem_ver).strip()
                        download_url = mdata.get("download_url") or f"{self.PATCHES_REPO_RAW_BASE}/patches/{best_ver}/SceneryX_{best_ver}_Setup.exe"
                        readme_url = mdata.get("readme_url") or f"{self.PATCHES_REPO_RAW_BASE}/patches/{best_ver}/README.md"
                        changelog_md = self._get_patch_changelog_markdown(best_ver, readme_url=readme_url)
                        return json.dumps({
                            "has_patch": True,
                            "current_version": current_ver,
                            "patch_version": best_ver,
                            "installer_path": "",
                            "download_url": download_url,
                            "readme_url": readme_url,
                            "changelog_md": changelog_md,
                            "changelog_md_en": self._get_patch_changelog_markdown(best_ver, readme_url=readme_url, lang="en"),
                            "changelog_md_fr": self._get_patch_changelog_markdown(best_ver, readme_url=readme_url, lang="fr")
                        }, ensure_ascii=False)
                except Exception:
                    pass

            return json.dumps({"has_patch": False, "current_version": current_ver}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"has_patch": False, "error": str(e)}, ensure_ascii=False)

    def install_available_patch(self, installer_path=None, download_url=None, patch_version=None):
        if IS_LITE:
            return json.dumps({"status": "locked", "is_lite": True, "message": "Automatic patch updates are only used in SceneryX Pro."}, ensure_ascii=False)
        try:
            current_ver = self._get_current_app_version()
            readme_url = None
            if not patch_version or not download_url:
                raw = json.loads(self.check_available_patch())
                if not download_url:
                    download_url = raw.get("download_url")
                if not patch_version:
                    patch_version = raw.get("patch_version")
                readme_url = raw.get("readme_url")

            patch_version = self._normalize_version_tag(patch_version or "PRO_1.1.1")
            if not download_url:
                return json.dumps({"status": "error", "message": "Remote patch download URL not found on Git (Updates/patches)."}, ensure_ascii=False)

            # Strictly download from remote Updates/patches Git branch
            updates_dir = os.path.join(USER_DATA_DIR, "updates")
            os.makedirs(updates_dir, exist_ok=True)
            ver_tag = patch_version
            target_exe = os.path.join(updates_dir, f"SceneryX_{ver_tag}_Setup.exe")
            part_exe = target_exe + ".part"
            if os.path.exists(part_exe):
                try:
                    os.remove(part_exe)
                except Exception:
                    pass

            sep = "&" if "?" in download_url else "?"
            bust_dl_url = f"{download_url}{sep}t={int(time.time())}"
            req = urllib.request.Request(
                bust_dl_url,
                headers={"User-Agent": "SceneryX-Updater/1.1", "Cache-Control": "no-cache"}
            )
            with urllib.request.urlopen(req, timeout=180) as resp, open(part_exe, "wb") as out_f:
                while True:
                    chunk = resp.read(262144)
                    if not chunk:
                        break
                    out_f.write(chunk)
            if os.path.exists(part_exe) and os.path.getsize(part_exe) > 5 * 1024 * 1024:
                os.replace(part_exe, target_exe)
                installer_path = target_exe
            else:
                if os.path.exists(part_exe):
                    os.remove(part_exe)
                return json.dumps({"status": "error", "message": "Downloaded patch file from Git is incomplete or invalid."}, ensure_ascii=False)

            # Persist pending changelog marker so the post-patch changelog modal opens right after restart
            try:
                ver_tag = patch_version
                changelog_md = self._get_patch_changelog_markdown(ver_tag, readme_url=readme_url)
                os.makedirs(USER_DATA_DIR, exist_ok=True)
                pending_path = os.path.join(USER_DATA_DIR, "pending_changelog.json")
                with open(pending_path, "w", encoding="utf-8") as pf:
                    json.dump({
                        "version": ver_tag,
                        "previous_version": current_ver,
                        "changelog_md": changelog_md
                    }, pf, indent=2, ensure_ascii=False)
                settings = get_settings()
                settings["pending_changelog_version"] = ver_tag
                save_settings(settings)
            except Exception:
                pass

            import ctypes
            work_dir = os.path.dirname(os.path.abspath(installer_path))
            ret = ctypes.windll.shell32.ShellExecuteW(
                None,
                "open",
                str(installer_path),
                "/SILENT /AUTOPATCH",
                work_dir,
                1
            )
            if int(ret) <= 32:
                ret = ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    str(installer_path),
                    "/SILENT /AUTOPATCH",
                    work_dir,
                    1
                )
            if int(ret) <= 32:
                return json.dumps({"status": "cancelled", "code": int(ret)}, ensure_ascii=False)

            self.exit_app(False)
            return json.dumps({"status": "ok"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def check_post_patch_changelog(self):
        if IS_LITE:
            return json.dumps({"has_changelog": False, "version": APP_VERSION, "is_lite": True}, ensure_ascii=False)
        try:
            current_ver = self._get_current_app_version()
            cur_tuple = self._parse_version_tuple(current_ver)
            pending_path = os.path.join(USER_DATA_DIR, "pending_changelog.json")
            settings = get_settings()
            last_seen = settings.get("last_seen_version")
            pending_ver = settings.get("pending_changelog_version")

            cached_md = None
            has_pending_marker = False

            # 1. Check pending_changelog.json written by updater or Inno Setup
            if os.path.isfile(pending_path):
                try:
                    with open(pending_path, "r", encoding="utf-8", errors="ignore") as f:
                        pdata = json.load(f)
                    pver = self._normalize_version_tag(pdata.get("version"))
                    if not pver or pver == current_ver or self._parse_version_tuple(pver) == cur_tuple:
                        has_pending_marker = True
                        cached_md = pdata.get("changelog_md")
                except Exception:
                    has_pending_marker = True

            # 2. Check Windows Registry PendingChangelogVersion written by Inno Setup
            if not has_pending_marker:
                try:
                    import winreg
                    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                        try:
                            with winreg.OpenKey(root, r"Software\SceneryX") as key:
                                val, _ = winreg.QueryValueEx(key, "PendingChangelogVersion")
                                if val and (self._normalize_version_tag(str(val).strip()) == current_ver or self._parse_version_tuple(val) == cur_tuple):
                                    has_pending_marker = True
                                    break
                        except Exception:
                            continue
                except Exception:
                    pass

            # 3. Check settings.json pending_changelog_version or version upgrade transition
            if not has_pending_marker:
                if pending_ver and (self._normalize_version_tag(pending_ver) == current_ver or self._parse_version_tuple(pending_ver) == cur_tuple):
                    has_pending_marker = True
                elif last_seen and self._parse_version_tuple(last_seen) > (0, 0, 0) and cur_tuple > self._parse_version_tuple(last_seen):
                    has_pending_marker = True

            # If this is the first launch of a base install (no marker), record last_seen_version
            if not has_pending_marker:
                if last_seen != current_ver:
                    settings["last_seen_version"] = current_ver
                    save_settings(settings)
                return json.dumps({"has_changelog": False, "version": current_ver}, ensure_ascii=False)

            changelog_md = self._get_patch_changelog_markdown(current_ver)
            if not changelog_md and cached_md:
                changelog_md = re.sub(r'\bRC_v?', 'PRO_', str(cached_md))

            return json.dumps({
                "has_changelog": True,
                "version": current_ver,
                "changelog_md": changelog_md,
                "changelog_md_en": self._get_patch_changelog_markdown(current_ver, lang="en"),
                "changelog_md_fr": self._get_patch_changelog_markdown(current_ver, lang="fr")
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"has_changelog": False, "error": str(e)}, ensure_ascii=False)

    def acknowledge_post_patch_changelog(self):
        try:
            current_ver = self._get_current_app_version()
            pending_path = os.path.join(USER_DATA_DIR, "pending_changelog.json")
            if os.path.isfile(pending_path):
                try:
                    os.remove(pending_path)
                except Exception:
                    pass

            try:
                import winreg
                for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                    try:
                        with winreg.OpenKey(root, r"Software\SceneryX", 0, winreg.KEY_SET_VALUE) as key:
                            winreg.DeleteValue(key, "PendingChangelogVersion")
                    except Exception:
                        continue
            except Exception:
                pass

            settings = get_settings()
            settings["last_seen_version"] = current_ver
            if "pending_changelog_version" in settings:
                del settings["pending_changelog_version"]
            save_settings(settings)
            return json.dumps({"status": "ok"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def get_live_blackbox_telemetry(self):
        try:
            telemetry = flight_perf_tracker.BLACKBOX.get_telemetry()
            return json.dumps(telemetry, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def get_route_optimization_state(self):
        try:
            state = flight_perf_tracker.detect_route_optimization_state()
            return json.dumps(state, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def list_flight_benchmarks(self):
        try:
            import flight_perf_tracker
            bench_dir = flight_perf_tracker.get_benchmarks_directory()
            if not os.path.exists(bench_dir):
                return json.dumps([], ensure_ascii=False)

            # Auto-recover any orphan CSVs (e.g. from CTD or abrupt close) before listing
            try:
                flight_perf_tracker.recover_orphan_benchmarks(bench_dir)
            except Exception as e:
                print(f"[Telemetry] Orphan check during list error: {e}")

            files = []
            html_files = [f for f in os.listdir(bench_dir) if f.endswith('.html')]
            html_files.sort(key=lambda f: os.path.getmtime(os.path.join(bench_dir, f)), reverse=True)
            for f in html_files:
                full_p = os.path.join(bench_dir, f)
                stat = os.stat(full_p)
                files.append({
                    "filename": f,
                    "path": full_p,
                    "size_kb": round(stat.st_size / 1024, 1),
                    "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                })
            return json.dumps(files, ensure_ascii=False)
        except Exception as e:
            return json.dumps([], ensure_ascii=False)

    def open_benchmark_report(self, filename_or_path):
        try:
            import flight_perf_tracker
            bench_dir = flight_perf_tracker.get_benchmarks_directory()
            if not os.path.isabs(filename_or_path):
                p = os.path.join(bench_dir, filename_or_path)
            else:
                p = filename_or_path
            if os.path.exists(p):
                webbrowser.open(f"file:///{os.path.abspath(p)}")
                return json.dumps({"status": "ok"})
            return json.dumps({"status": "error", "message": "File not found"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_flight_report_data(self, filename_or_path):
        try:
            import flight_perf_tracker
            data = flight_perf_tracker.load_report_payload(filename_or_path)
            return json.dumps(data, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def delete_flight_benchmark(self, filename):
        try:
            import flight_perf_tracker
            bench_dir = flight_perf_tracker.get_benchmarks_directory()
            if isinstance(filename, list):
                files_to_delete = filename
            else:
                files_to_delete = [x.strip() for x in str(filename).split(',') if x.strip()]

            deleted_count = 0
            for item in files_to_delete:
                safe_name = os.path.basename(item)
                html_p = os.path.join(bench_dir, safe_name)
                stem = os.path.splitext(safe_name)[0]
                csv_p = os.path.join(bench_dir, f"{stem}.csv")
                json_p = os.path.join(bench_dir, f"{stem}.json")

                file_deleted = False
                if os.path.exists(html_p):
                    try:
                        os.remove(html_p)
                        file_deleted = True
                    except Exception:
                        pass
                if os.path.exists(csv_p):
                    try:
                        os.remove(csv_p)
                        file_deleted = True
                    except Exception:
                        pass
                if os.path.exists(json_p):
                    try:
                        os.remove(json_p)
                        file_deleted = True
                    except Exception:
                        pass
                if file_deleted:
                    deleted_count += 1

            if deleted_count > 0:
                return json.dumps({"status": "success", "deleted_count": deleted_count}, ensure_ascii=False)
            return json.dumps({"status": "error", "message": "No benchmark file deleted or found."}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def rename_flight_benchmark(self, old_filename, new_filename):
        try:
            import flight_perf_tracker
            bench_dir = flight_perf_tracker.get_benchmarks_directory()
            safe_old = os.path.basename(old_filename)
            clean_new = os.path.basename(new_filename.strip())
            if not clean_new:
                return json.dumps({"status": "error", "message": "New name cannot be empty."}, ensure_ascii=False)
            if not clean_new.lower().endswith('.html'):
                clean_new = f"{clean_new}.html"

            old_html_p = os.path.join(bench_dir, safe_old)
            new_html_p = os.path.join(bench_dir, clean_new)

            if not os.path.exists(old_html_p):
                return json.dumps({"status": "error", "message": "Original benchmark file not found."}, ensure_ascii=False)
            if os.path.exists(new_html_p) and old_html_p.lower() != new_html_p.lower():
                return json.dumps({"status": "error", "message": "A benchmark with this name already exists."}, ensure_ascii=False)

            os.rename(old_html_p, new_html_p)

            old_stem = os.path.splitext(safe_old)[0]
            new_stem = os.path.splitext(clean_new)[0]
            old_csv_p = os.path.join(bench_dir, f"{old_stem}.csv")
            new_csv_p = os.path.join(bench_dir, f"{new_stem}.csv")
            if os.path.exists(old_csv_p):
                try:
                    os.rename(old_csv_p, new_csv_p)
                except Exception:
                    pass

            return json.dumps({"status": "success", "new_filename": clean_new}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    # ================= SMART LOD (DYNAMIC PERFORMANCE ENGINE) =================

    def get_smart_lod_status(self):
        try:
            import flight_lod_controller
            ctrl = flight_lod_controller.get_smart_lod_controller()
            return json.dumps(ctrl.get_status(), ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def set_smart_lod_enabled(self, enabled, force_kill_autofps=False):
        if IS_LITE:
            return json.dumps({"success": False, "status": "locked", "is_lite": True, "error": "Smart LOD Governor is only available in SceneryX Pro."}, ensure_ascii=False)
        try:
            import flight_lod_controller
            ctrl = flight_lod_controller.get_smart_lod_controller()
            res = ctrl.set_enabled(bool(enabled), force_kill_autofps=bool(force_kill_autofps))
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    def set_smart_lod_cloud_recovery(self, enabled):
        if IS_LITE:
            return json.dumps({"success": False, "status": "locked", "is_lite": True, "error": "Smart LOD Governor is only available in SceneryX Pro."}, ensure_ascii=False)
        try:
            import flight_lod_controller
            ctrl = flight_lod_controller.get_smart_lod_controller()
            res = ctrl.set_cloud_recovery(bool(enabled))
            return json.dumps({"success": res, "cloud_recovery": bool(enabled)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    def save_smart_lod_config(self, config_json_str):
        if IS_LITE:
            return json.dumps({"success": False, "status": "locked", "is_lite": True, "error": "Smart LOD Governor is only available in SceneryX Pro."}, ensure_ascii=False)
        try:
            import flight_lod_controller
            cfg = json.loads(config_json_str) if isinstance(config_json_str, str) else config_json_str
            ctrl = flight_lod_controller.get_smart_lod_controller()
            ok = ctrl.save_config(cfg)
            return json.dumps({"success": ok, "config": ctrl.get_config()}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    def get_smart_lod_axis_state(self, mode="2D"):
        try:
            import flight_lod_controller
            st = flight_lod_controller.get_smart_lod_axis_state(mode)
            return json.dumps(st, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def set_smart_lod_axis_state(self, mode, axis, enabled=None, target=None, altitude=None, base=None):
        if IS_LITE:
            return json.dumps({"status": "locked", "is_lite": True, "error": "Smart LOD Governor is only available in SceneryX Pro."}, ensure_ascii=False)
        try:
            import flight_lod_controller
            st = flight_lod_controller.set_smart_lod_axis_state(mode, axis, enabled=enabled, target=target, altitude=altitude, base=base)
            return json.dumps(st, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def set_external_autofps(self, enabled):
        if IS_LITE:
            return json.dumps({"success": False, "status": "locked", "is_lite": True, "error": "External AutoFPS integration is only available in SceneryX Pro."}, ensure_ascii=False)
        try:
            import flight_lod_controller
            ok = flight_lod_controller.set_external_autofps(bool(enabled))
            return json.dumps({"success": ok}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    def reset_smart_lod_to_profile(self, axis="all"):
        if IS_LITE:
            return json.dumps({"success": False, "status": "locked", "is_lite": True, "error": "Smart LOD Governor is only available in SceneryX Pro."}, ensure_ascii=False)
        try:
            import flight_lod_controller
            res = flight_lod_controller.reset_smart_lod_to_profile(axis)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    def kill_external_autofps(self):
        try:
            from flight_memory_engine import FlightMemoryEngine
            ok = FlightMemoryEngine.kill_autofps_process()
            return json.dumps({"success": ok}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    def check_background_tools(self):
        try:
            from flight_memory_engine import FlightMemoryEngine
            from scanner import get_settings
            import flight_rig_optimizer
            
            af_running, af_pid = FlightMemoryEngine.is_autofps_running()
            ofxr_running, ofxr_pid = FlightMemoryEngine.is_ofxr_running()
            
            st = get_settings()
            remember = bool(st.get("background_tools_remembered", False))
            if remember and st.get("autofps_autokill", False) and af_running:
                FlightMemoryEngine.kill_autofps_process()
                af_running = False
                af_pid = None

            # Detect VR Headset refresh rate (Pimax, Meta, Index, etc.)
            det_vr = flight_rig_optimizer.detect_vr_headset()
            vr_hz = int(det_vr.get("refresh_rate_hz", 90)) if det_vr.get("detected") else 90

            fps_2x = max(20, vr_hz // 2)
            fps_3x = max(20, round(vr_hz / 3))
            is_3x_disabled = (fps_3x < 30) or (vr_hz <= 75)

            default_mode = "2X" if is_3x_disabled else "3X"
            ofxr_mode = str(st.get("ofxr_mode", default_mode if ofxr_running else "OFF")).upper()
            if ofxr_mode not in ["OFF", "2X", "3X"] or (is_3x_disabled and ofxr_mode == "3X"):
                ofxr_mode = default_mode if ofxr_running else "OFF"
                if is_3x_disabled and st.get("ofxr_mode") == "3X":
                    st["ofxr_mode"] = "2X"
                    st["ofxr_target_fps"] = fps_2x
                    save_settings(st)

            default_target = fps_2x if (is_3x_disabled or ofxr_mode == "2X") else fps_3x
            try:
                ofxr_target_fps = int(st.get("ofxr_target_fps", default_target))
                if is_3x_disabled and ofxr_target_fps < 30:
                    ofxr_target_fps = fps_2x
                    st["ofxr_target_fps"] = fps_2x
                    save_settings(st)
            except Exception:
                ofxr_target_fps = default_target

            ofxr_sync = bool(st.get("ofxr_sync_smart_lod", True))
            ext_af = bool(st.get("external_autofps", False))

            return json.dumps({
                "autofps_running": af_running,
                "autofps_pid": af_pid,
                "ofxr_running": ofxr_running,
                "ofxr_pid": ofxr_pid,
                "remember_choice": remember,
                "ofxr_mode": ofxr_mode,
                "ofxr_target_fps": ofxr_target_fps,
                "ofxr_sync_smart_lod": ofxr_sync,
                "external_autofps": ext_af,
                "vr_hz": vr_hz,
                "fps_2x": fps_2x,
                "fps_3x": fps_3x
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def resolve_background_tools(self, action_json_str):
        try:
            from flight_memory_engine import FlightMemoryEngine
            import flight_lod_controller
            import flight_rig_optimizer
            from scanner import get_settings, save_settings

            payload = json.loads(action_json_str) if isinstance(action_json_str, str) else action_json_str
            st = get_settings()

            det_vr = flight_rig_optimizer.detect_vr_headset()
            vr_hz = int(det_vr.get("refresh_rate_hz", 90)) if det_vr.get("detected") else 90
            fps_2x = max(20, vr_hz // 2)
            fps_3x = max(20, round(vr_hz / 3))
            is_3x_disabled = (fps_3x < 30) or (vr_hz <= 75)

            remember = bool(payload.get("remember", False))
            af_action = payload.get("autofps_action", "ignore")
            if af_action == "kill":
                FlightMemoryEngine.kill_autofps_process()
                flight_lod_controller.set_external_autofps(False)
                st["autofps_autokill"] = remember
                st["background_tools_remembered"] = remember
                st["external_autofps"] = False
            elif af_action == "keep":
                flight_lod_controller.set_external_autofps(True)
                st["autofps_autokill"] = False
                st["background_tools_remembered"] = remember
                st["external_autofps"] = True

            if "ofxr_mode" in payload:
                mode = str(payload.get("ofxr_mode", "OFF")).upper()
                if mode in ["OFF", "2X", "3X"]:
                    if is_3x_disabled and mode == "3X":
                        mode = "2X"
                    st["ofxr_mode"] = mode

            if "ofxr_target_fps" in payload:
                try:
                    fps = int(payload.get("ofxr_target_fps", 36))
                    if is_3x_disabled and fps < 30:
                        fps = fps_2x
                    st["ofxr_target_fps"] = fps
                except Exception:
                    pass

            if "ofxr_sync_smart_lod" in payload:
                sync = bool(payload.get("ofxr_sync_smart_lod", True))
                st["ofxr_sync_smart_lod"] = sync

            # Automatically sync Max Frame Rate (VR) in UserCfg.opt with OFXR target
            if st.get("ofxr_mode") in ["2X", "3X"]:
                fps = int(st.get("ofxr_target_fps", 36))
                path = flight_rig_optimizer.get_user_cfg_path()
                if path and os.path.exists(path):
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        current_fps_vr = flight_rig_optimizer.get_block_val(r'TargetFrameRateVR\s+(\d+)', content, '0')
                        if current_fps_vr and current_fps_vr not in ['0', str(fps)]:
                            if not st.get("ofxr_prev_max_frame_rate"):
                                st["ofxr_prev_max_frame_rate"] = current_fps_vr
                    except Exception:
                        pass
                flight_rig_optimizer.update_msfs_user_cfg_setting("VR", "max_frame_rate", str(fps), path, create_backup=False)

                if st.get("ofxr_sync_smart_lod", True):
                    flight_lod_controller.set_vr_target_fps(fps)

            st["background_tools_remembered"] = remember

            save_settings(st)
            return json.dumps({"success": True, "settings": st}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    def save_ofxr_settings(self, mode, target_fps, sync_smart_lod):
        try:
            from scanner import get_settings, save_settings
            import flight_lod_controller
            import flight_rig_optimizer
            import os
            st = get_settings()

            det_vr = flight_rig_optimizer.detect_vr_headset()
            vr_hz = int(det_vr.get("refresh_rate_hz", 90)) if det_vr.get("detected") else 90
            fps_2x = max(20, vr_hz // 2)
            fps_3x = max(20, round(vr_hz / 3))
            is_3x_disabled = (fps_3x < 30) or (vr_hz <= 75)

            mode_str = str(mode).upper().strip()
            if mode_str in ["OFF", "2X", "3X"]:
                if is_3x_disabled and mode_str == "3X":
                    mode_str = "2X"
                st["ofxr_mode"] = mode_str

            try:
                fps = int(target_fps)
                if is_3x_disabled and fps < 30:
                    fps = fps_2x
                st["ofxr_target_fps"] = fps
            except Exception:
                fps = fps_2x if is_3x_disabled else 36

            sync_bool = bool(sync_smart_lod)
            st["ofxr_sync_smart_lod"] = sync_bool

            path = flight_rig_optimizer.get_user_cfg_path()
            restored_fps = None

            if mode_str in ["2X", "3X"]:
                # 1. Capture current UserCfg.opt TargetFrameRateVR before changing, if not already saved
                if path and os.path.exists(path):
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        current_fps_vr = flight_rig_optimizer.get_block_val(r'TargetFrameRateVR\s+(\d+)', content, '0')
                        if current_fps_vr and current_fps_vr not in ['0', str(fps)]:
                            if not st.get("ofxr_prev_max_frame_rate"):
                                st["ofxr_prev_max_frame_rate"] = current_fps_vr
                    except Exception:
                        pass

                # 2. Automatically update TargetFrameRateVR in UserCfg.opt to match OFXR base target
                flight_rig_optimizer.update_msfs_user_cfg_setting("VR", "max_frame_rate", str(fps), path, create_backup=False)

                # 3. If synced, update Smart LOD target
                if sync_bool:
                    flight_lod_controller.set_vr_target_fps(fps)

            elif mode_str == "OFF":
                # Revert max frame rate back to previous value
                prev_fps = st.get("ofxr_prev_max_frame_rate")
                if not prev_fps:
                    det = flight_rig_optimizer.detect_vr_headset()
                    hz = int(det.get("refresh_rate_hz", 90)) if det.get("detected") else 90
                    prev_fps = str(max(30, hz // 2))

                flight_rig_optimizer.update_msfs_user_cfg_setting("VR", "max_frame_rate", str(prev_fps), path, create_backup=False)
                restored_fps = prev_fps
                st.pop("ofxr_prev_max_frame_rate", None)

                try:
                    flight_lod_controller.set_vr_target_fps(int(prev_fps))
                except Exception:
                    pass

            save_settings(st)
            return json.dumps({
                "status": "ok",
                "ofxr_mode": mode_str,
                "ofxr_target_fps": fps,
                "ofxr_sync_smart_lod": sync_bool,
                "restored_fps": restored_fps
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def get_smart_lod_profiles(self):
        try:
            import flight_lod_controller
            profiles = flight_lod_controller.get_smart_lod_profiles()
            return json.dumps(profiles, ensure_ascii=False)
        except Exception as e:
            return json.dumps([], ensure_ascii=False)

    def save_smart_lod_profile(self, profile_name, config_json_str, overwrite_id=None):
        try:
            import flight_lod_controller
            cfg = json.loads(config_json_str) if isinstance(config_json_str, str) else config_json_str
            res = flight_lod_controller.save_smart_lod_profile(profile_name, cfg, overwrite_id=overwrite_id)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def check_smart_lod_profile_changes(self, profile_id, current_config_json_str):
        try:
            import flight_lod_controller
            cfg = json.loads(current_config_json_str) if isinstance(current_config_json_str, str) else current_config_json_str
            res = flight_lod_controller.check_smart_lod_profile_changes(profile_id, cfg)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def rename_smart_lod_profile(self, profile_id, new_name):
        try:
            import flight_lod_controller
            res = flight_lod_controller.rename_smart_lod_profile(profile_id, new_name)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def activate_smart_lod_profile(self, profile_id):
        try:
            import flight_lod_controller
            res = flight_lod_controller.activate_smart_lod_profile(profile_id)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def delete_smart_lod_profile(self, profile_id):
        try:
            import flight_lod_controller
            res = flight_lod_controller.delete_smart_lod_profile(profile_id)
            return json.dumps(res, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    # ================= MSFS IN-GAME TOOLBAR PANEL MANAGEMENT =================

    def _get_all_community_paths(self):
        paths = []
        try:
            settings = get_settings()
            for sp in settings.get("scan_paths", []):
                p = sp.get("path", "")
                if "community" in p.lower() and os.path.exists(p) and p not in paths:
                    paths.append(p)
        except Exception:
            pass
        return paths

    def _get_primary_community_path(self):
        all_paths = self._get_all_community_paths()
        for p in all_paths:
            if "community2024" in p.lower():
                return p
        return all_paths[0] if all_paths else None

    def get_ingame_panel_status(self):
        try:
            all_paths = self._get_all_community_paths()
            if not all_paths:
                return json.dumps({"available": False, "installed": False, "message": "Community folder not detected."})
            primary = self._get_primary_community_path()
            target_dir = os.path.join(primary, "sceneryx-ingame-panel")
            legacy_dir = os.path.join(primary, "wildbill75-sceneryx")
            if os.path.exists(os.path.join(legacy_dir, "manifest.json")) and not os.path.exists(os.path.join(target_dir, "manifest.json")):
                self._auto_sync_installed_ingame_panel()
            installed = os.path.exists(os.path.join(target_dir, "manifest.json"))
            return json.dumps({
                "available": True,
                "installed": installed,
                "path": target_dir,
                "community": primary
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"available": False, "installed": False, "error": str(e)}, ensure_ascii=False)

    def install_ingame_panel(self):
        if IS_LITE:
            return json.dumps({"success": False, "status": "locked", "is_lite": True, "message": "The MSFS In-Game Toolbar Panel is only available in SceneryX Pro."}, ensure_ascii=False)
        try:
            import shutil
            all_paths = self._get_all_community_paths()
            if not all_paths:
                return json.dumps({"success": False, "message": "Community folder not detected."})
            
            # Locate sceneryx-ingame-panel source folder
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            src_dir = os.path.join(base_dir, "sceneryx-ingame-panel")
            if not os.path.exists(src_dir):
                src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sceneryx-ingame-panel")
            if not os.path.exists(src_dir):
                src_dir = os.path.join(os.getcwd(), "sceneryx-ingame-panel")
            
            if not os.path.exists(src_dir):
                return json.dumps({"success": False, "message": f"Source folder not found: {src_dir}"})
            
            targets = ["sceneryx-ingame-panel"]
            for c_path in all_paths:
                # Clean up legacy wildbill75-sceneryx folder if present
                old_legacy = os.path.join(c_path, "wildbill75-sceneryx")
                if os.path.exists(old_legacy):
                    try:
                        shutil.rmtree(old_legacy)
                    except Exception:
                        pass
                for tname in targets:
                    target_dir = os.path.join(c_path, tname)
                    shutil.copytree(src_dir, target_dir, dirs_exist_ok=True)

            # Ensure Content.xml activation and clean legacy wildbill75-sceneryx
            for p in get_content_xml_paths():
                if os.path.exists(p):
                    try:
                        with open(p, "r", encoding="utf-8") as f:
                            cxml = f.read()
                        cxml_new = re.sub(r'\s*<Package name="[^"]*wildbill75-sceneryx"[^>]*/>', '', cxml)
                        needed = [
                            "communityfs20-sceneryx-ingame-panel",
                            "communityfs24-sceneryx-ingame-panel"
                        ]
                        for pk in needed:
                            if f'<Package name="{pk}"' not in cxml_new and '</Packages>' in cxml_new:
                                cxml_new = cxml_new.replace('</Packages>', f'\t<Package name="{pk}" active="Activated" />\n</Packages>')
                        if cxml_new != cxml:
                            with open(p, "w", encoding="utf-8") as f:
                                f.write(cxml_new)
                    except Exception:
                        pass

            return json.dumps({"success": True, "message": "In-Game Panel installed successfully in Community folders!"})
        except Exception as e:
            return json.dumps({"success": False, "message": str(e)})

    def uninstall_ingame_panel(self):
        try:
            import shutil
            all_paths = self._get_all_community_paths()
            if not all_paths:
                return json.dumps({"success": False, "message": "Community folder not detected."})
            targets = ["sceneryx-ingame-panel", "wildbill75-sceneryx"]
            for c_path in all_paths:
                for tname in targets:
                    target_dir = os.path.join(c_path, tname)
                    if os.path.exists(target_dir):
                        shutil.rmtree(target_dir)
            return json.dumps({"success": True, "message": "In-Game Panel uninstalled from Community."})
        except Exception as e:
            return json.dumps({"success": False, "message": str(e)})




_SINGLE_INSTANCE_MUTEX = None

def ensure_single_instance():
    global _SINGLE_INSTANCE_MUTEX
    if sys.platform != 'win32' and os.name != 'nt':
        return True

    try:
        import ctypes
        ERROR_ALREADY_EXISTS = 183
        mutex_name = "SceneryX_SingleInstance_Mutex"
        _SINGLE_INSTANCE_MUTEX = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
        last_error = ctypes.windll.kernel32.GetLastError()

        if last_error == ERROR_ALREADY_EXISTS:
            # 1. Bring already running SceneryX window to front and restore if minimized
            hwnd = ctypes.windll.user32.FindWindowW(None, "SceneryX")
            if hwnd:
                SW_RESTORE = 9
                ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
                ctypes.windll.user32.SetForegroundWindow(hwnd)

            msg = "SceneryX is already running.\n\nOnly one instance of the application can run at a time."
            title = "SceneryX"

            # MB_OK (0x0) | MB_ICONWARNING (0x30) | MB_TOPMOST (0x40000) | MB_SETFOREGROUND (0x10000)
            MB_FLAGS = 0x00000000 | 0x00000030 | 0x00040000 | 0x00010000
            ctypes.windll.user32.MessageBoxW(hwnd or 0, msg, title, MB_FLAGS)

            if _SINGLE_INSTANCE_MUTEX:
                ctypes.windll.kernel32.CloseHandle(_SINGLE_INSTANCE_MUTEX)
                _SINGLE_INSTANCE_MUTEX = None
            return False
    except Exception as e:
        print("Single-instance check error:", e)

    return True


def main():
    # Headless CLI routines (used by uninstaller and automated fresh-user reset scripts)
    if any(arg in sys.argv for arg in ['--restore-defaults', '--restore-silent', '--uninstall-cleanup']):
        print("[SceneryX CLI] Headless rollback requested. Running non-destructive sim restoration...", flush=True)
        try:
            api = Api()
            print("[SceneryX CLI] 0/3 Restoring Community folder if quarantined in Safe Update Mode...", flush=True)
            try:
                flight_rig_optimizer.toggle_community_safe_update_mode(target_action="restore", force_when_running=True)
            except Exception as _e:
                print(f"[SceneryX CLI] Safe Update restore notice: {_e}", flush=True)
            print("[SceneryX CLI] 1/3 Restoring physical sceneries and Content.xml...", flush=True)
            api.restore_all_sceneries(full_reset=True)
            print("[SceneryX CLI] 2/3 Restoring original UserCfg.opt...", flush=True)
            api.restore_original_user_cfg()
            print("[SceneryX CLI] 3/3 Removing in-game toolbar panel from Community folder...", flush=True)
            api.uninstall_ingame_panel()
            print("[SceneryX CLI] Rollback finished successfully! Stock MSFS defaults restored.", flush=True)
        except Exception as e:
            print(f"[SceneryX CLI] Error during rollback: {e}", flush=True)
        os._exit(0)

    if '--setup-profiles' in sys.argv:
        print("[SceneryX CLI] Scanning rig hardware and calibrating standard profiles...", flush=True)
        try:
            appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'SceneryX')
            has_existing = os.path.exists(os.path.join(appdata_dir, 'settings.json'))
            flight_rig_optimizer.generate_default_rig_profiles(preserve_active=has_existing, missing_only=has_existing)
            print("[SceneryX CLI] Standard profiles successfully generated.", flush=True)
        except Exception as e:
            print(f"[SceneryX CLI] Profile generation error: {e}", flush=True)
        os._exit(0)

    if not ensure_single_instance():
        sys.exit(0)

    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    exe_dir = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    local_web = os.path.join(exe_dir, 'web')
    if os.path.exists(os.path.join(local_web, 'index.html')):
        web_dir = local_web
    elif os.path.exists(os.path.join(base_dir, 'web', 'index.html')):
        web_dir = os.path.join(base_dir, 'web')
    else:
        web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')
    html_file = os.path.join(web_dir, 'index.html')

    # Dynamically detect monitor resolution & center the window in the usable workspace
    init_width = 1760
    init_height = 1020
    init_x = None
    init_y = None
    try:
        if hasattr(webview, 'screens') and webview.screens:
            primary_screen = webview.screens[0]
            if hasattr(primary_screen, 'width') and hasattr(primary_screen, 'height'):
                sw = primary_screen.width
                sh = primary_screen.height
                
                # Proportional sizing: 84% width, 86% usable height (minus ~48px taskbar)
                init_width = max(1280, min(int(sw * 0.84), 2560))
                usable_height = max(700, sh - 48)
                init_height = max(800, min(int(usable_height * 0.86), 1400))
                
                # Pixel-perfect centering on the primary desktop workspace
                init_x = max(0, (sw - init_width) // 2)
                init_y = max(15, (usable_height - init_height) // 2)
    except Exception as e:
        print("Screen resolution detection fallback:", e)

    api = Api()
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_dir, 'icon.ico')
    if not os.path.exists(icon_path):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')

    # Initialisation du collecteur de bugs et traces d'exception
    try:
        flight_bug_reporter.init_bug_reporter()
    except Exception as e:
        print(f"[BugReporter] Initialization warning: {e}")

    # Ensure aircraft, liveries and core utilities are 100% active in Content.xml on startup
    try:
        sanitize_msfs_content_xml()
    except Exception as e:
        print(f"[Sanitize] Startup check warning: {e}")

    # Strictly synchronize saved active graphics profile to UserCfg.opt on startup
    try:
        flight_rig_optimizer.ensure_active_profile_applied()
    except Exception as e:
        print(f"[Optimizer] Startup active profile sync warning: {e}")

    # Automatically recover orphan benchmarks from abrupt exits or MSFS CTD
    try:
        import flight_perf_tracker
        flight_perf_tracker.recover_orphan_benchmarks()
    except Exception as e:
        print(f"[Telemetry] Startup orphan benchmark check warning: {e}")

    # Automatically refresh installed In-Game Panel in Community folders on Pro startup
    if not IS_LITE:
        try:
            for c_path in api._get_all_community_paths():
                target_panel_dir = os.path.join(c_path, "sceneryx-ingame-panel")
                legacy_panel_dir = os.path.join(c_path, "wildbill75-sceneryx")
                if os.path.exists(os.path.join(target_panel_dir, "manifest.json")) or os.path.exists(os.path.join(legacy_panel_dir, "manifest.json")):
                    api.install_ingame_panel()
                    break
        except Exception as e:
            print(f"[InGamePanel] Startup auto-refresh notice: {e}")

    # 1. Main Application Window (Master window, initialized hidden during splash phase)
    window = webview.create_window(
        title='SceneryX',
        url=html_file,
        js_api=api,
        width=init_width,
        height=init_height,
        x=init_x,
        y=init_y,
        min_size=(1280, 800),
        background_color='#0b0f19',
        hidden=True
    )
    api._window = window
    Api._main_window_instance = window

    # 2. Standalone Splash Window (Child window: 640x400, frameless, centered, on top)
    splash_width = 640
    splash_height = 400
    splash_x = None
    splash_y = None
    if 'sw' in locals() and 'sh' in locals() and sw and sh:
        splash_x = max(0, (sw - splash_width) // 2)
        splash_y = max(0, (sh - splash_height) // 2)

    splash_html_file = os.path.join(web_dir, 'splash.html')
    splash_api = SplashApi(shared_splash_state)

    global splash_window
    splash_window = webview.create_window(
        title='SceneryX',
        url=splash_html_file,
        js_api=splash_api,
        width=splash_width,
        height=splash_height,
        x=splash_x,
        y=splash_y,
        frameless=True,
        on_top=True,
        background_color='#0b0f19'
    )

    # Safety watchdog to guarantee main window reveals even if JS execution is interrupted
    def _safety_watchdog():
        time.sleep(25.0)
        global splash_window
        if splash_window is not None:
            print("[Watchdog] Safety reveal: closing splash and revealing main window...")
            finish_splash_and_reveal_main()

    import threading
    threading.Thread(target=_safety_watchdog, daemon=True).start()

    tray_icon = None

    def on_closing():
        global splash_window
        if splash_window:
            try:
                splash_window.destroy()
            except Exception:
                pass
            splash_window = None
        if getattr(api, '_force_closing', False):
            if tray_icon:
                try:
                    tray_icon.stop()
                except Exception:
                    pass
            try:
                import flight_perf_tracker
                if flight_perf_tracker.BLACKBOX.is_running:
                    print("[Telemetry] Force closing: suspending blackbox session for resume...")
                    flight_perf_tracker.BLACKBOX.suspend_for_resume()
            except Exception:
                pass
            try:
                import flight_remote_server
                flight_remote_server.stop_remote_server()
            except Exception:
                pass
            return True

        st = get_settings()
        close_action = st.get('close_action', 'quit')
        if close_action == 'minimize_to_tray':
            try:
                window.hide()
            except Exception as e:
                print(f"[Tray] Hide window error: {e}")
            return False

        try:
            import flight_perf_tracker
            if flight_perf_tracker.BLACKBOX.is_running:
                import threading
                threading.Timer(0.05, lambda: window.evaluate_js('promptClosingActiveMonitoring()')).start()
                return False
        except Exception:
            pass

        fm = st.get('flight_mode', {})
        if isinstance(fm, dict) and fm.get('active'):
            import threading
            threading.Timer(0.05, lambda: window.evaluate_js('promptClosingFlightMode()')).start()
            return False

        if tray_icon:
            try:
                tray_icon.stop()
            except Exception:
                pass
        try:
            flight_rig_optimizer.ensure_active_profile_applied()
        except Exception as e:
            print(f"[Optimizer] Closing active profile sync notice: {e}")
        try:
            import flight_remote_server
            flight_remote_server.stop_remote_server()
        except Exception:
            pass
        return True

    window.events.closing += on_closing

    # Start Micro HTTP REST Server for In-Game Toolbar Panel
    try:
        import flight_remote_server
        flight_remote_server.start_remote_server()
    except Exception as e:
        print(f"[RemoteServer] Startup error: {e}")

    # Initialize System Tray Icon (pystray)
    try:
        import pystray
        from PIL import Image

        tray_image = None
        if os.path.exists(icon_path):
            try:
                tray_image = Image.open(icon_path)
            except Exception as e:
                print(f"[Tray] Image load error: {e}")

        if tray_image:
            def on_tray_show(icon, item):
                try:
                    if window:
                        window.show()
                        window.restore()
                except Exception as e:
                    print(f"[Tray] Show error: {e}")
                bring_window_to_front("SceneryX")

            def on_tray_quit(icon, item):
                try:
                    import flight_perf_tracker
                    if flight_perf_tracker.BLACKBOX.is_running:
                        on_tray_show(icon, item)
                        import threading
                        threading.Timer(0.1, lambda: window.evaluate_js('promptClosingActiveMonitoring()')).start()
                        return
                except Exception:
                    pass
                try:
                    api._force_closing = True
                    if icon:
                        icon.stop()
                except Exception:
                    pass
                try:
                    import flight_remote_server
                    flight_remote_server.stop_remote_server()
                except Exception:
                    pass
                try:
                    if window:
                        window.destroy()
                except Exception:
                    pass
                import os
                os._exit(0)

            tray_menu = pystray.Menu(
                pystray.MenuItem('Show SceneryX', on_tray_show, default=True),
                pystray.MenuItem('Quit', on_tray_quit)
            )
            tray_icon = pystray.Icon('SceneryX', tray_image, 'SceneryX', tray_menu)
            api._tray_icon = tray_icon
            api._on_tray_show = on_tray_show
            api._on_tray_quit = on_tray_quit

            import threading
            def run_tray():
                try:
                    tray_icon.run()
                except Exception as e:
                    print(f"[Tray] Tray loop error: {e}")

            tray_thread = threading.Thread(target=run_tray, daemon=True)
            tray_thread.start()
    except Exception as e:
        print(f"[Tray] Init error: {e}")

    cache_dir = os.path.join(USER_DATA_DIR, 'web_cache')
    os.makedirs(cache_dir, exist_ok=True)
    try:
        import shutil
        for sub in ['EBWebView/Default/Cache', 'EBWebView/Default/Code Cache']:
            sub_path = os.path.join(cache_dir, os.path.normpath(sub))
            if os.path.exists(sub_path):
                shutil.rmtree(sub_path, ignore_errors=True)
    except Exception as e:
        print(f"[Cache] Disk cache clean warning: {e}")

    if os.path.exists(icon_path):
        webview.start(debug=False, private_mode=False, storage_path=cache_dir, icon=icon_path)
    else:
        webview.start(debug=False, private_mode=False, storage_path=cache_dir)

if __name__ == '__main__':
    main()
