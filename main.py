import os
import sys
import json
import re
import urllib.request
import webview
from scanner import run_scan, get_settings, save_settings, load_ratings, save_rating, save_custom_price, load_custom_prices, get_default_gsx_path, load_airport_database, SPECIAL_BUNDLE_MAP, OUTPUT_JSON_PATH

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

def update_msfs_content_xml(keep_icaos=None, restore_all=False):
    local_appdata = os.getenv('LOCALAPPDATA', '')
    appdata = os.getenv('APPDATA', '')

    content_xml_paths = [
        r'C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml',
        os.path.join(local_appdata, r'Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Content.xml'),
        os.path.join(local_appdata, r'Packages\Microsoft.FlightSimulator_8wekyb3d8bbwe\LocalCache\Content.xml'),
        os.path.join(appdata, r'Microsoft Flight Simulator\Content.xml')
    ]

    target_icaos = set(k.upper() for k in (keep_icaos or []))

    for xml_path in content_xml_paths:
        if not os.path.exists(xml_path):
            continue
        try:
            import xml.etree.ElementTree as ET
            with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            tree = ET.fromstring(content)

            for elem in tree.findall('Package'):
                name = elem.get('name', '')
                if restore_all:
                    if elem.get('active') == 'UserDisabled':
                        elem.set('active', 'Activated')
                else:
                    pkg_icaos = resolve_package_icaos(name)
                    if any(k in target_icaos for k in pkg_icaos):
                        elem.set('active', 'Activated')
                    elif pkg_icaos:
                        elem.set('active', 'UserDisabled')

            xml_str = ET.tostring(tree, encoding='unicode')
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="utf-8"?>\n' + xml_str)
            print(f"Successfully updated MSFS Content.xml at {xml_path}")
        except Exception as e:
            print(f"Error updating Content.xml at {xml_path}: {e}")

class Api:
    def __init__(self):
        pass

    def get_airports(self):
        airports = run_scan()
        return json.dumps(airports, ensure_ascii=False)

    def rescan(self):
        airports = run_scan()
        return json.dumps(airports, ensure_ascii=False)

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
        try:
            if isinstance(flight_icaos_json, str):
                flight_icaos = json.loads(flight_icaos_json)
            else:
                flight_icaos = flight_icaos_json

            flight_icaos = [str(x).upper() for x in flight_icaos]
            flight_set = set(flight_icaos)
            airports = run_scan()

            disabled_count = 0
            content_xml_path = r'C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml'
            if os.path.exists(content_xml_path):
                import xml.etree.ElementTree as ET
                tree = ET.parse(content_xml_path)
                root = tree.getroot()
                changed = False

                for p in root.findall('Package'):
                    name = p.get('name', '')
                    clean_folder = name[:-9] if name.endswith('.disabled') else name
                    p_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', clean_folder.lower())

                    matched_ap = None
                    for ap in airports:
                        if ap.get('pricing_type') != 'Asobo':
                            for src in ap.get('all_sources', []):
                                fn = src.get('folder_name', '').lower()
                                s_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', fn)
                                if p_norm == s_norm or p_norm in s_norm or s_norm in p_norm:
                                    matched_ap = ap
                                    break
                            if matched_ap:
                                break

                    if matched_ap:
                        if matched_ap['icao'] in flight_set:
                            if p.get('active') == 'UserDisabled':
                                p.set('active', 'Activated')
                                changed = True
                        else:
                            if p.get('active') != 'UserDisabled':
                                p.set('active', 'UserDisabled')
                                changed = True
                                disabled_count += 1

                if changed:
                    tree.write(content_xml_path, encoding='utf-8', xml_declaration=True)

            st = get_settings()
            st['flight_mode'] = {
                'active': True,
                'icaos': flight_icaos,
                'disabled_count': disabled_count
            }
            save_settings(st)

            updated_airports = run_scan()
            return json.dumps({
                "status": "success",
                "airports": updated_airports,
                "disabled_count": disabled_count,
                "flight_icaos": flight_icaos
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def restore_all_flight_sceneries(self):
        try:
            content_xml_path = r'C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml'
            if os.path.exists(content_xml_path):
                import xml.etree.ElementTree as ET
                tree = ET.parse(content_xml_path)
                root = tree.getroot()
                changed = False

                # Get physical folders across all scan paths to avoid activating deleted/absent packages
                st_cfg = get_settings()
                scan_paths_cfg = st_cfg.get("scan_paths", [])

                physical_folders_lower = set()
                for cfg in scan_paths_cfg:
                    if not cfg.get('enabled', True):
                        continue
                    dp = cfg.get('path', '')
                    if os.path.exists(dp):
                        try:
                            for item in os.listdir(dp):
                                physical_folders_lower.add(item.lower())
                        except Exception:
                            pass

                for p in root.findall('Package'):
                    name = p.get('name', '')
                    clean = name[:-9] if name.endswith('.disabled') else name
                    folder_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', clean.lower())
                    
                    exists_on_disk = any(folder_norm in f or f in folder_norm for f in physical_folders_lower)
                    if exists_on_disk and p.get('active') == 'UserDisabled':
                        p.set('active', 'Activated')
                        changed = True
                if changed:
                    tree.write(content_xml_path, encoding='utf-8', xml_declaration=True)

            st = get_settings()
            st['flight_mode'] = {'active': False, 'icaos': []}
            save_settings(st)

            airports = run_scan()
            return json.dumps({
                "status": "success",
                "airports": airports
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def toggle_airport_disabled(self, icao):
        try:
            icao_target = str(icao).strip().upper()
            content_xml_path = r'C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml'
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
                        break

            if changed:
                tree.write(content_xml_path, encoding='utf-8', xml_declaration=True)

            updated_airports = run_scan()
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
            content_xml_path = r'C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml'
            if os.path.exists(content_xml_path):
                import xml.etree.ElementTree as ET
                tree = ET.parse(content_xml_path)
                root = tree.getroot()
                changed = False
                for p in root.findall('Package'):
                    if p.get('active') == 'UserDisabled':
                        p.set('active', 'Activated')
                        changed = True
                if changed:
                    tree.write(content_xml_path, encoding='utf-8', xml_declaration=True)

            st = get_settings()
            st['flight_mode'] = {'active': False, 'icaos': []}
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

    def save_settings(self, settings_json):
        try:
            data = json.loads(settings_json)
            updated = save_settings(data)
            airports = run_scan()
            return json.dumps({"status": "ok", "settings": updated, "airports": airports}, ensure_ascii=False)
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

    def toggle_package(self, package_path):
        try:
            if not os.path.exists(package_path):
                return json.dumps({"status": "error", "message": "Package path not found"})

            if package_path.endswith('.disabled'):
                new_path = package_path[:-9]
                os.rename(package_path, new_path)
                is_enabled = True
            else:
                new_path = package_path + '.disabled'
                os.rename(package_path, new_path)
                is_enabled = False

            airports = run_scan()
            return json.dumps({"status": "ok", "enabled": is_enabled, "new_path": new_path, "airports": airports}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def optimize_flight_mode(self, keep_icaos_json):
        try:
            keep_icaos = set(json.loads(keep_icaos_json))
            settings = get_settings()
            scan_paths_cfg = settings.get("scan_paths", [])

            enabled_count = 0
            disabled_count = 0

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
                            item_p = os.path.join(td, item)
                            if not os.path.isdir(item_p) or item == 'OneStore':
                                continue

                            pkg_icaos = resolve_package_icaos(item)
                            if not pkg_icaos:
                                if item.endswith('.disabled'):
                                    orig_p = os.path.join(td, item[:-9])
                                    if not os.path.exists(orig_p):
                                        os.rename(item_p, orig_p)
                                        enabled_count += 1
                                continue

                            is_keep = any(k in keep_icaos for k in pkg_icaos)

                            if is_keep:
                                if item.endswith('.disabled'):
                                    orig_p = os.path.join(td, item[:-9])
                                    if not os.path.exists(orig_p):
                                        os.rename(item_p, orig_p)
                                        enabled_count += 1
                            else:
                                if not item.endswith('.disabled'):
                                    dis_p = item_p + '.disabled'
                                    if not os.path.exists(dis_p):
                                        os.rename(item_p, dis_p)
                                        disabled_count += 1
                    except Exception as e:
                        print(f"Error processing {td} during flight optimizer:", e)

            # Update MSFS Native Content.xml (UserDisabled / Activated)
            update_msfs_content_xml(keep_icaos=keep_icaos, restore_all=False)

            updated_airports = run_scan()
            return json.dumps({
                "status": "ok",
                "enabled_count": enabled_count,
                "disabled_count": disabled_count,
                "airports": updated_airports
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def restore_all_sceneries(self):
        try:
            settings = get_settings()
            scan_paths_cfg = settings.get("scan_paths", [])
            re_enabled_count = 0

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
                                dis_p = os.path.join(td, item)
                                orig_p = os.path.join(td, item[:-9])
                                if os.path.isdir(dis_p) and not os.path.exists(orig_p):
                                    try:
                                        os.rename(dis_p, orig_p)
                                        re_enabled_count += 1
                                    except Exception as e:
                                        print(f"Error restoring {dis_p}:", e)
                    except Exception as e:
                        print(f"Error scanning {td} for restore:", e)

            # Update MSFS Native Content.xml to restore all UserDisabled packages back to Activated
            update_msfs_content_xml(restore_all=True)

            updated_airports = run_scan()
            return json.dumps({
                "status": "ok",
                "re_enabled_count": re_enabled_count,
                "airports": updated_airports
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def browse_folder(self):
        try:
            window = webview.windows[0]
            result = window.create_file_dialog(webview.FOLDER_DIALOG)
            if result and len(result) > 0:
                return result[0]
        except Exception as e:
            print("Folder dialog error:", e)
        return ""

    def open_folder(self, path):
        if path and os.path.exists(path):
            os.startfile(path)
            return True
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

    def _extract_archive_files(self, archive_path_or_bytes, ext, gsx_dir):
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
                    print("Zipfile extraction failed, trying tar fallback:", e)

            # 2. Universal Windows tar.exe fallback (.rar, .7z, .zip, .tar, etc.)
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

            # 3. Walk temp_dir for .ini or .py files
            for root, dirs, files in os.walk(temp_dir):
                for f in files:
                    f_lower = f.lower()
                    if (f_lower.endswith('.ini') or f_lower.endswith('.py')) and f_lower != 'configuration.ini':
                        src_p = os.path.join(root, f)
                        target_p = os.path.join(gsx_dir, f)
                        shutil.copy2(src_p, target_p)
                        installed_files.append(f)

        return installed_files

    def install_gsx_profile(self, icao="", file_path="", base64_data="", filename=""):
        import shutil
        import base64
        
        settings = get_settings()
        gsx_dir = settings.get("gsx_profile_path", get_default_gsx_path())
        
        if not os.path.exists(gsx_dir):
            os.makedirs(gsx_dir, exist_ok=True)
            
        installed_files = []
        
        try:
            # 1. Base64 dropped file handling
            if base64_data and filename:
                if "," in base64_data:
                    base64_data = base64_data.split(",", 1)[1]
                    
                file_bytes = base64.b64decode(base64_data)
                ext = os.path.splitext(filename)[1].lower()
                
                if ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                    installed_files = self._extract_archive_files(file_bytes, ext, gsx_dir)
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
                    installed_files = self._extract_archive_files(file_path, ext, gsx_dir)
                elif ext in ['.ini', '.py']:
                    fname = os.path.basename(file_path)
                    if fname and fname.lower() != 'configuration.ini':
                        target_p = os.path.join(gsx_dir, fname)
                        shutil.copy2(file_path, target_p)
                        installed_files.append(fname)

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
                        return self.install_gsx_profile(icao=icao, file_path=result[0])
                except Exception as e:
                    return json.dumps({"status": "error", "message": str(e)})

            if not installed_files:
                return json.dumps({"status": "error", "message": "Aucun fichier de profil GSX (.ini ou .py) valide n'a été trouvé dans cette archive."})

            airports = run_scan()
            return json.dumps({
                "status": "ok",
                "installed_files": installed_files,
                "airports": airports
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def search_gsx_profile(self, icao, name=""):
        import webbrowser
        import urllib.parse
        query = f"GSX {icao}".strip()
        url = f"https://flightsim.to/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return json.dumps({"status": "ok", "url": url})

    def check_update(self, icao, name, vendor, version):
        import webbrowser
        import urllib.parse
        
        v_str = f" {vendor}" if vendor and vendor.lower() not in ['unknown', 'microsoft / asobo', 'asobo', 'unknown vendor'] else ""
        if v_str:
            query = f"{vendor} {icao} {name} MSFS scenery update"
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return json.dumps({"status": "ok", "url": url})

    def export_collection_csv(self, airports_json_str):
        import csv
        try:
            airports = json.loads(airports_json_str)
            window = webview.windows[0]
            result = window.create_file_dialog(
                webview.SAVE_DIALOG,
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

    def export_collection_json(self, airports_json_str):
        try:
            airports = json.loads(airports_json_str)
            window = webview.windows[0]
            result = window.create_file_dialog(
                webview.SAVE_DIALOG,
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

    # Calculate optimal window dimensions (85% of primary monitor size for 2K/4K displays)
    init_width = 1760
    init_height = 1020
    try:
        if hasattr(webview, 'screens') and webview.screens:
            primary_screen = webview.screens[0]
            if hasattr(primary_screen, 'width') and hasattr(primary_screen, 'height'):
                init_width = int(primary_screen.width * 0.85)
                init_height = int(primary_screen.height * 0.85)
    except Exception as e:
        print("Screen resolution detection fallback:", e)

    api = Api()
    window = webview.create_window(
        title='SceneryX',
        url=html_file,
        js_api=api,
        width=init_width,
        height=init_height,
        min_size=(1280, 800),
        background_color='#0b0f19'
    )
    webview.start(debug=False)

if __name__ == '__main__':
    main()
