import os
import sys
import json
import re
import urllib.request
import webbrowser
import webview
from scanner import run_scan, get_settings, save_settings, load_ratings, save_rating, save_custom_price, save_custom_category, load_custom_prices, get_estimated_price, get_default_gsx_path, load_airport_database, SPECIAL_BUNDLE_MAP, OUTPUT_JSON_PATH, compute_scan_delta, build_library_snapshot, SNAPSHOT_JSON_PATH, get_resource_file_path, audit_all_gsx_profiles, audit_single_airport_gsx, extract_icao_from_gsx_filename, find_bundled_gsx

AIRPORTS_DB_CACHE = None

def resolve_package_icaos(pkg_name):
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

    found = set()
    if clean_fn in SPECIAL_BUNDLE_MAP:
        found.update(SPECIAL_BUNDLE_MAP[clean_fn])
    for b_key, b_icaos in SPECIAL_BUNDLE_MAP.items():
        if b_key in clean_fn:
            found.update(b_icaos)

    tokens = re.split(r'[-_ ]+', clean_fn)
    for t in tokens:
        t_upper = t.upper()
        if len(t_upper) == 4 and t_upper in airports and t.lower() not in ['fs20', 'fs24', 'vfra', 'pack', 'aero', 'vfr', 'mesh', 'tree', 'data']:
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

def is_core_or_library_package(pkg_name):
    nl = pkg_name.lower()
    return any(k in nl for k in [
        'modellib', 'commonlibrary', 'projectairports', 'genericairports',
        'travelbook', 'worlddiscovery', 'bush-trip', 'activities',
        'instruments', 'navdata', 'fs-base'
    ])

_CACHED_CONTENT_XML_PATH = None

def get_content_xml_paths():
    local_appdata = os.getenv('LOCALAPPDATA', '')
    appdata = os.getenv('APPDATA', '')
    limitless_cache = os.path.join(local_appdata, r'Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache')

    return [
        os.path.join(limitless_cache, 'Content.xml'),
        os.path.join(local_appdata, r'Packages\Microsoft.FlightSimulator_8wekyb3d8bbwe\LocalCache\Content.xml'),
        os.path.join(appdata, r'Microsoft Flight Simulator 2024\Content.xml'),
        os.path.join(appdata, r'Microsoft Flight Simulator\Content.xml')
    ]

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
    clean_p = p_path[:-9] if p_path.endswith('.disabled') else p_path
    dis_p = clean_p + '.disabled'
    target_dir = clean_p if (os.path.exists(clean_p) or os.path.islink(clean_p) or (hasattr(os.path, 'isjunction') and os.path.isjunction(clean_p))) else (dis_p if (os.path.exists(dis_p) or os.path.islink(dis_p)) else None)
    if not target_dir:
        return

    # Official / Streamed packages must NEVER be renamed physically on disk (managed via Content.xml)
    td_lower = target_dir.lower()
    if any(k in td_lower for k in ['official', 'streamed', 'asobo-', 'microsoft-']):
        if should_enable and dis_p and (os.path.exists(dis_p) or os.path.islink(dis_p)):
            enable_physical_package(dis_p)
        return

    # Check if package is potentially a multi-airport bundle
    folder_base = os.path.basename(clean_p).lower()
    is_potential_bundle = any(k in folder_base for k in ['pack', 'bundle', 'airports', 'vfr', 'airfields']) or folder_base in SPECIAL_BUNDLE_MAP

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

def update_msfs_content_xml(keep_icaos=None, restore_flight_mode=False, flight_disabled_xml=None, flight_added_xml=None, folder_to_icaos=None, third_party_airport_pkgs=None, all_airports=None):
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

        res = resolve_package_icaos(clean) or resolve_package_icaos(norm)
        if res:
            return set(res)

        m = re.search(r'[-_]airport[-_]([a-z0-9]{3,4})([-_]|$)', clean_lower)
        if m:
            return {m.group(1).upper()}

        if clean_lower in third_party_airport_pkgs or norm in third_party_airport_pkgs:
            return {'AIRPORT_UNKNOWN'}

        return set()

    flight_disabled_set = set(flight_disabled_xml or [])
    flight_added_set = set(flight_added_xml or [])
    disabled_xml_packages = set()
    added_xml_packages = set()

    target_icaos = set(k.upper() for k in (keep_icaos or []))

    for xml_path in content_xml_paths:
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
                for elem in list(tree.findall('Package')):
                    name = elem.get('name', '')
                    name_clean = name[:-9] if name.endswith('.disabled') else name
                    name_lower = name.lower()
                    name_clean_lower = name_clean.lower()
                    if name_lower in flight_added_set_lower or name_clean_lower in flight_added_set_lower:
                        tree.remove(elem)
                        changed = True
                    elif name_lower in flight_disabled_set_lower or name_clean_lower in flight_disabled_set_lower or (not flight_disabled_set_lower and elem.get('active') == 'UserDisabled'):
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

                    if is_core_or_library_package(name):
                        continue

                    pkg_icaos = get_package_icaos(name)
                    if pkg_icaos:
                        is_keep = any(k in target_icaos for k in pkg_icaos)
                        if is_keep:
                            pass
                        else:
                            if elem.get('active') == 'Activated':
                                elem.set('active', 'UserDisabled')
                                disabled_xml_packages.add(name)
                                changed = True

                if all_airports:
                    for ap in all_airports:
                        icao = ap.get('icao', '').upper()
                        if icao and icao not in target_icaos:
                            for src in ap.get('all_sources', []):
                                if src.get('is_fix_patch') or src.get('is_addon') or src.get('is_default'):
                                    continue
                                fn = src.get('folder_name', '')
                                if not fn:
                                    continue
                                fn_clean = fn[:-9] if fn.lower().endswith('.disabled') else fn
                                fn_clean_lower = fn_clean.lower()
                                fn_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', fn_clean_lower)
                                if fn_clean_lower not in seen_xml_names and fn_norm not in seen_xml_names:
                                    new_p = ET.SubElement(tree, 'Package')
                                    new_p.set('name', fn_clean)
                                    new_p.set('active', 'UserDisabled')
                                    seen_xml_names.add(fn_clean_lower)
                                    seen_xml_names.add(fn_norm)
                                    added_xml_packages.add(fn_clean)
                                    changed = True

            if changed or not os.path.exists(xml_path):
                xml_str = ET.tostring(tree, encoding='unicode')
                with open(xml_path, 'w', encoding='utf-8') as f:
                    f.write('<?xml version="1.0" encoding="utf-8"?>\n' + xml_str)
                print(f"Successfully updated MSFS Content.xml at {xml_path}")

                if 'ThirdBuk' in xml_path and os.path.exists(limitless_cache):
                    mirror_path = os.path.join(limitless_cache, 'Content.xml')
                    try:
                        with open(mirror_path, 'w', encoding='utf-8') as mf:
                            mf.write('<?xml version="1.0" encoding="utf-8"?>\n' + xml_str)
                    except Exception as me:
                        print(f"Could not mirror Content.xml to {mirror_path}: {me}")
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
            t_clean = target_pkg_name[:-9] if target_pkg_name.lower().endswith('.disabled') else target_pkg_name
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

                is_match = (
                    fn_clean.lower() == t_clean.lower() 
                    or fn_norm == t_norm 
                    or (fn_norm and t_norm and (fn_norm in t_norm or t_norm in fn_norm))
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
                    if dis_p and os.path.exists(dis_p):
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

class Api:
    def __init__(self):
        self._startup_delta = {"added": [], "removed": [], "total_changes": 0}
        self._startup_scanned = False

    def get_airports(self):
        settings = get_settings()
        disclaimer_accepted = settings.get("disclaimer_accepted", False)

        # If installed_airports.json exists and has data, user is not on first launch
        if not disclaimer_accepted and os.path.exists(OUTPUT_JSON_PATH) and os.path.getsize(OUTPUT_JSON_PATH) > 1000:
            disclaimer_accepted = True
            settings["disclaimer_accepted"] = True
            save_settings(settings)

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

        auto_scan = settings.get("auto_scan_on_startup", True)
        if auto_scan:
            airports = run_scan()
            self._startup_delta = compute_scan_delta(airports, update_snapshot=True)
            self._startup_scanned = True
            return json.dumps(airports, ensure_ascii=False)

        if os.path.exists(OUTPUT_JSON_PATH):
            try:
                with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                    airports = json.load(f)
                    if airports and len(airports) > 0:
                        self._startup_delta = {"added": [], "removed": [], "total_changes": 0}
                        self._startup_scanned = True
                        return json.dumps(airports, ensure_ascii=False)
            except Exception as e:
                print("Error reading cached installed_airports.json, performing fresh scan:", e)

        airports = run_scan()
        self._startup_delta = compute_scan_delta(airports, update_snapshot=True)
        self._startup_scanned = True
        return json.dumps(airports, ensure_ascii=False)

    def initial_scan(self):
        """
        Runs the first-time scan right after the user accepts the Terms of Use.
        Builds the baseline library_snapshot.json and saves installed_airports.json.
        """
        airports = run_scan()
        current_snapshot = build_library_snapshot(airports)
        try:
            with open(SNAPSHOT_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(current_snapshot, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("Error saving initial library snapshot:", e)
        self._startup_delta = {"added": [], "removed": [], "total_changes": 0}
        return json.dumps({"airports": airports, "delta": self._startup_delta}, ensure_ascii=False)

    def get_startup_delta(self):
        delta = getattr(self, '_startup_delta', None)
        if not delta or not isinstance(delta, dict):
            delta = {"added": [], "removed": [], "total_changes": 0}
        return json.dumps(delta, ensure_ascii=False)

    def get_world_airport_coords(self):
        try:
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
            return json.dumps(coords, ensure_ascii=False)
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

    def rescan(self):
        airports = run_scan()
        delta = compute_scan_delta(airports, update_snapshot=True)
        self._startup_delta = delta
        return json.dumps({"airports": airports, "delta": delta}, ensure_ascii=False)

    def fetch_simbrief(self, identifier):
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
                for alt_key in ['alternate', 'alternate_2', 'alternate_3', 'alternate_4']:
                    alt_data = data.get(alt_key)
                    if alt_data and isinstance(alt_data, dict) and alt_data.get('icao_code'):
                        alternates.append({
                            'icao': alt_data.get('icao_code'),
                            'name': alt_data.get('name', alt_data.get('icao_code'))
                        })

                general = data.get('general', {})
                flight_num = f"{general.get('icao_airline', '')}{general.get('flight_number', '')}".strip()
                route = general.get('route', '')
                aircraft = data.get('aircraft', {}).get('name', '')

                all_flight_icaos = [origin_icao, dest_icao] + [a['icao'] for a in alternates]
                all_flight_icaos = list(dict.fromkeys([icao.upper() for icao in all_flight_icaos if icao]))

                return json.dumps({
                    "status": "success",
                    "username": username,
                    "userid": user_id,
                    "flight": {
                        "origin": {"icao": origin_icao, "name": origin_name},
                        "destination": {"icao": dest_icao, "name": dest_name},
                        "alternates": alternates,
                        "flight_number": flight_num,
                        "aircraft": aircraft,
                        "route": route,
                        "flight_icaos": all_flight_icaos
                    }
                }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Error fetching SimBrief data: {str(e)}"})

    def optimize_flight(self, flight_icaos_json):
        return self.optimize_flight_mode(flight_icaos_json)

    def restore_all_flight_sceneries(self):
        return self.restore_all_sceneries(full_reset=False)

    def toggle_airport_disabled(self, icao):
        try:
            icao_target = str(icao).strip().upper()
            content_xml_path = get_content_xml_path()
            if not os.path.exists(content_xml_path):
                return json.dumps({"status": "error", "message": "Content.xml not found"})

            import xml.etree.ElementTree as ET
            tree = ET.parse(content_xml_path)
            root = tree.getroot()

            airports = run_scan()
            ap = next((a for a in airports if a['icao'] == icao_target), None)
            if not ap:
                return json.dumps({"status": "error", "message": f"Airport {icao_target} not found"})

            if ap.get('pricing_type') == 'Asobo':
                return json.dumps({"status": "error", "message": "Asobo base airports cannot be disabled."})

            curr_disabled = ap.get('is_disabled', False)
            new_active_val = 'UserDisabled' if not curr_disabled else 'Activated'

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
                update_msfs_content_xml(restore_all=True)
                st = get_settings()
                st['flight_mode'] = {'active': False, 'icaos': []}
                save_settings(st)

            self._force_closing = True
            import threading, os
            threading.Timer(0.05, lambda: os._exit(0)).start()
            return json.dumps({"status": "ok"})
        except Exception as e:
            import os
            os._exit(0)
            return json.dumps({"status": "error", "message": str(e)})

    def save_settings(self, settings_json):
        try:
            data = json.loads(settings_json)
            updated = save_settings(data)
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
                with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
                    json.dump(airports, f, indent=2, ensure_ascii=False)

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
            
            content_xml_path = get_content_xml_path()

            with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                scanned_airports = json.load(f)
            ap_obj = next((a for a in scanned_airports if a['icao'].upper() == icao.upper()), None)

            if os.path.exists(content_xml_path):
                import xml.etree.ElementTree as ET
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

            content_xml_path = get_content_xml_path()

            target_clean = target_folder_name[:-9] if target_folder_name.lower().endswith('.disabled') else target_folder_name
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

            if os.path.exists(content_xml_path):
                import xml.etree.ElementTree as ET
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
                            or (clean_norm and target_norm and (clean_norm in target_norm or target_norm in clean_norm))
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
                            or (fn_norm and target_norm and (fn_norm in target_norm or target_norm in fn_norm))
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

            if ap_obj and ap_obj.get('all_sources'):
                for src in ap_obj['all_sources']:
                    if src.get('is_fix_patch') or src.get('is_addon'):
                        continue
                    fn = src.get('folder_name', '')
                    pkg_p = src.get('package_path', '')
                    fn_clean = fn[:-9] if fn.lower().endswith('.disabled') else fn
                    fn_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', fn_clean.lower())

                    is_target = (target_clean != 'DEFAULT') and (
                        fn_clean.lower() == target_clean.lower() 
                        or fn_norm == target_norm
                        or (fn_norm and target_norm and (fn_norm in target_norm or target_norm in fn_norm))
                        or (src.get('is_asobo_official') and ('asobo' in target_clean.lower() or 'microsoft' in target_clean.lower()))
                    )
                    if is_target:
                        set_package_state_for_icao(pkg_p, icao, should_enable=True)
                    else:
                        set_package_state_for_icao(pkg_p, icao, should_enable=False)

            airports = fast_update_airport_cache(icao, target_pkg_name=target_clean)
            target_ap = next((a for a in airports if a['icao'].upper() == icao.upper()), None)
            return json.dumps({"status": "ok", "updated_airport": target_ap}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def toggle_fix_patch(self, path, icao):
        try:
            if not path:
                return json.dumps({"status": "error", "message": "No path provided"})

            content_xml_path = get_content_xml_path()
            
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

            if os.path.exists(content_xml_path):
                import xml.etree.ElementTree as ET
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
        return self.optimize_flight_mode(keep_icaos_json)

    def optimize_flight_mode(self, keep_icaos_json):
        try:
            keep_icaos = set(json.loads(keep_icaos_json))
            settings = get_settings()
            scan_paths_cfg = settings.get("scan_paths", [])

            all_airports = run_scan()
            folder_to_icaos, third_party_airport_pkgs = get_folder_to_icaos_map(all_airports)

            enabled_count = 0
            disabled_count = 0
            disabled_by_flight_mode = []

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
                            pkg_icaos = folder_to_icaos.get(item_clean_lower) or resolve_package_icaos(item_clean)

                            # ONLY process packages that actually represent airport sceneries!
                            # NEVER rename liveries, aircraft, tools, GSX, or utilities!
                            is_airport_pkg = bool(pkg_icaos) or (item_clean_lower in third_party_airport_pkgs)
                            if not is_airport_pkg:
                                continue

                            is_keep = any(k in keep_icaos for k in (pkg_icaos or []))

                            if is_community:
                                try:
                                    if is_keep:
                                        if item.endswith('.disabled'):
                                            orig_p = os.path.join(td, item[:-9])
                                            if safe_rename_path(item_p, orig_p):
                                                enabled_count += 1
                                    else:
                                        if not item.endswith('.disabled'):
                                            dis_p = item_p + '.disabled'
                                            if safe_rename_path(item_p, dis_p):
                                                disabled_count += 1
                                                disabled_by_flight_mode.append(item)
                                except Exception as rename_err:
                                    print(f"Skipping rename for {item}: {rename_err}")
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

            # Merge with existing state if flight mode was already partially active
            existing_flight_cfg = settings.get('flight_mode', {})
            existing_folders = set(existing_flight_cfg.get('disabled_folders', []))
            existing_xml = set(existing_flight_cfg.get('disabled_xml_packages', []))
            existing_added = set(existing_flight_cfg.get('added_xml_packages', []))

            all_disabled_folders = list(existing_folders.union(disabled_by_flight_mode))
            all_disabled_xml = list(existing_xml.union(disabled_xml_pkgs))
            all_added_xml = list(existing_added.union(added_xml_pkgs))

            total_disabled_count = len(all_disabled_folders) + len(all_disabled_xml) + len(all_added_xml)

            settings['flight_mode'] = {
                'active': True,
                'disabled_count': total_disabled_count,
                'icaos': list(keep_icaos),
                'disabled_folders': all_disabled_folders,
                'disabled_xml_packages': all_disabled_xml,
                'added_xml_packages': all_added_xml
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
        return self.restore_all_sceneries(full_reset=False)

    def restore_all_sceneries(self, full_reset=False):
        try:
            settings = get_settings()
            scan_paths_cfg = settings.get("scan_paths", [])
            re_enabled_count = 0

            flight_mode_cfg = settings.get('flight_mode', {})
            flight_disabled_folders = set(flight_mode_cfg.get('disabled_folders', []))
            flight_disabled_xml = set(flight_mode_cfg.get('disabled_xml_packages', []))
            flight_added_xml = set(flight_mode_cfg.get('added_xml_packages', []))

            flight_disabled_folders_lower = {f.lower() for f in flight_disabled_folders}

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
                                item_lower = item.lower()
                                item_clean_lower = item_clean.lower()
                                # If full_reset is False and we have flight_disabled_folders, only restore folders disabled by flight mode!
                                if not full_reset and flight_disabled_folders_lower and (item_clean_lower not in flight_disabled_folders_lower and item_lower not in flight_disabled_folders_lower):
                                    continue

                                dis_p = os.path.join(td, item)
                                orig_p = os.path.join(td, item_clean)
                                try:
                                    if safe_rename_path(dis_p, orig_p):
                                        re_enabled_count += 1
                                except Exception as e:
                                    print(f"Error restoring {dis_p}:", e)
                    except Exception as e:
                        print(f"Error scanning {td} for restore:", e)

            # Update MSFS Native Content.xml safely (restoring ONLY flight mode modifications)
            update_msfs_content_xml(
                restore_flight_mode=True,
                flight_disabled_xml=flight_disabled_xml,
                flight_added_xml=flight_added_xml
            )

            settings['flight_mode'] = {
                'active': False,
                'icaos': [],
                'disabled_count': 0,
                'disabled_folders': [],
                'disabled_xml_packages': [],
                'added_xml_packages': []
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
                return result[0]
        except Exception as e:
            print("Folder dialog error:", e)
        return ""

    def open_folder(self, path):
        try:
            if not path:
                return False

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
            if url and (url.startswith('http://') or url.startswith('https://')):
                webbrowser.open(url)
                return json.dumps({"status": "ok"})
        except Exception as e:
            print("open_external_url error:", e)
            return json.dumps({"status": "error", "message": str(e)})
        return json.dumps({"status": "error", "message": "Invalid URL"})

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
                            m = re.search(r'[£$€]\s*(\d+[\.,]\d{2})\s*([A-Z]{3})?', snippet)
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
                    num_m = re.search(r'€\s*(\d+[\.,]\d{2})|(\d+[\.,]\d{2})\s*€', html)
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


def main():
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
    window = webview.create_window(
        title='SceneryX',
        url=html_file,
        js_api=api,
        width=init_width,
        height=init_height,
        x=init_x,
        y=init_y,
        min_size=(1280, 800),
        background_color='#0b0f19'
    )
    api._window = window

    def on_closing():
        if getattr(api, '_force_closing', False):
            return True
        st = get_settings()
        fm = st.get('flight_mode', {})
        if isinstance(fm, dict) and fm.get('active'):
            import threading
            threading.Timer(0.05, lambda: window.evaluate_js('promptClosingFlightMode()')).start()
            return False
        return True

    window.events.closing += on_closing

    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_dir, 'icon.ico')
    if not os.path.exists(icon_path):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')

    if os.path.exists(icon_path):
        webview.start(debug=False, icon=icon_path)
    else:
        webview.start(debug=False)

if __name__ == '__main__':
    main()
