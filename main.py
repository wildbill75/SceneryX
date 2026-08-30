import os
import sys
import json
import re
import urllib.request
import webbrowser
import webview
from scanner import run_scan, get_settings, save_settings, load_ratings, save_rating, save_custom_price, save_custom_category, load_custom_prices, get_estimated_price, get_default_gsx_path, load_airport_database, SPECIAL_BUNDLE_MAP, OUTPUT_JSON_PATH

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
                    folder_to_icaos.setdefault(fn_clean_lower, set()).add(icao)
                    if pricing not in ['Asobo', 'Default'] and not src.get('is_asobo_official') and not src.get('is_default'):
                        third_party_airport_pkgs.add(fn_clean_lower)

    return folder_to_icaos, third_party_airport_pkgs

def update_msfs_content_xml(keep_icaos=None, restore_all=False, folder_to_icaos=None, third_party_airport_pkgs=None):
    local_appdata = os.getenv('LOCALAPPDATA', '')
    appdata = os.getenv('APPDATA', '')

    content_xml_paths = [
        r'C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml',
        os.path.join(local_appdata, r'Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Content.xml'),
        os.path.join(local_appdata, r'Packages\Microsoft.FlightSimulator_8wekyb3d8bbwe\LocalCache\Content.xml'),
        os.path.join(appdata, r'Microsoft Flight Simulator\Content.xml')
    ]

    if folder_to_icaos is None or third_party_airport_pkgs is None:
        folder_to_icaos, third_party_airport_pkgs = get_folder_to_icaos_map()

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
                name_clean_lower = (name[:-9] if name.endswith('.disabled') else name).lower()

                if restore_all:
                    if elem.get('active') == 'UserDisabled':
                        elem.set('active', 'Activated')
                else:
                    # ONLY toggle 3rd-party airport scenery packages in Content.xml
                    # NEVER touch aircraft, navdata, GSX, liveries, or core MSFS packages!
                    if name_clean_lower in third_party_airport_pkgs:
                        pkg_icaos = folder_to_icaos.get(name_clean_lower, set())
                        if any(k in target_icaos for k in pkg_icaos):
                            elem.set('active', 'Activated')
                        else:
                            elem.set('active', 'UserDisabled')
                    else:
                        # Ensure all non-airport packages (aircraft, navdata, utilities) remain 100% Activated
                        elem.set('active', 'Activated')

            xml_str = ET.tostring(tree, encoding='unicode')
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="utf-8"?>\n' + xml_str)
            print(f"Successfully updated MSFS Content.xml at {xml_path}")
        except Exception as e:
            print(f"Error updating Content.xml at {xml_path}: {e}")

def fast_update_airport_cache(icao_target, target_pkg_name=None, toggle_all=False):
    if not os.path.exists(OUTPUT_JSON_PATH):
        return run_scan()
    try:
        with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
            airports = json.load(f)

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
                s['is_disabled'] = True
                fn = s.get('folder_name', '')
                s['folder_name'] = fn[:-9] if fn.lower().endswith('.disabled') else fn
        elif target_pkg_name:
            t_clean = target_pkg_name[:-9] if target_pkg_name.lower().endswith('.disabled') else target_pkg_name
            for s in all_srcs:
                fn = s.get('folder_name', '')
                fn_clean = fn[:-9] if fn.lower().endswith('.disabled') else fn
                s['folder_name'] = fn_clean
                p = s.get('package_path', '')
                clean_p = p[:-9] if p and p.endswith('.disabled') else p
                dis_p = clean_p + '.disabled' if clean_p else None

                if fn_clean.lower() == t_clean.lower() or t_clean.lower() in fn_clean.lower():
                    s['is_disabled'] = False
                    if clean_p:
                        s['package_path'] = clean_p
                else:
                    s['is_disabled'] = True
                    if dis_p and os.path.exists(dis_p):
                        s['package_path'] = dis_p
        else:
            for s in all_srcs:
                p = s.get('package_path', '')
                clean_p = p[:-9] if p and p.endswith('.disabled') else p
                dis_p = clean_p + '.disabled' if clean_p else None

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
        if active_sources:
            main_active = [s for s in active_sources if not s.get('is_fix_patch') and not s.get('is_addon')]
            primary = main_active[0] if main_active else active_sources[0]

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

        with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(airports, f, ensure_ascii=False, indent=2)

        return airports
    except Exception as e:
        print("Error fast updating cache:", e)
        return run_scan()

class Api:
    def __init__(self):
        pass

    def get_airports(self):
        if os.path.exists(OUTPUT_JSON_PATH):
            try:
                with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print("Error reading cached installed_airports.json, performing fresh scan:", e)
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

    def toggle_package(self, package_path, icao=None):
        try:
            content_xml_path = r'C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml'
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

            # Helper function to disable a physical package directory on disk
            def disable_physical_package(p_path):
                if not p_path or not os.path.exists(p_path):
                    return p_path
                new_p = p_path
                if not p_path.endswith('.disabled'):
                    new_p = p_path + '.disabled'
                    os.rename(p_path, new_p)
                for mf in ['manifest.json', 'layout.json']:
                    mf_norm = os.path.join(new_p, mf)
                    mf_dis = os.path.join(new_p, mf + '.disabled')
                    if os.path.exists(mf_norm):
                        if os.path.exists(mf_dis):
                            os.remove(mf_dis)
                        os.rename(mf_norm, mf_dis)
                return new_p

            # Helper function to enable a physical package directory on disk
            def enable_physical_package(p_path):
                if not p_path or not os.path.exists(p_path):
                    return p_path
                new_p = p_path
                if p_path.endswith('.disabled'):
                    new_p = p_path[:-9]
                    os.rename(p_path, new_p)
                for mf in ['manifest.json', 'layout.json']:
                    mf_dis = os.path.join(new_p, mf + '.disabled')
                    mf_norm = os.path.join(new_p, mf)
                    if os.path.exists(mf_dis):
                        if os.path.exists(mf_norm):
                            os.remove(mf_norm)
                        os.rename(mf_dis, mf_norm)
                return new_p

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
            return json.dumps({"status": "ok", "enabled": should_enable, "new_path": new_path, "airports": airports}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def disable_all_for_airport(self, icao):
        try:
            if not icao:
                return json.dumps({"status": "error", "message": "No ICAO provided"})
            
            content_xml_path = r'C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml'
            
            def disable_physical_package(p_path):
                if not p_path or not os.path.exists(p_path):
                    return
                new_p = p_path
                if not p_path.endswith('.disabled'):
                    new_p = p_path + '.disabled'
                    os.rename(p_path, new_p)
                for mf in ['manifest.json', 'layout.json']:
                    mf_norm = os.path.join(new_p, mf)
                    mf_dis = os.path.join(new_p, mf + '.disabled')
                    if os.path.exists(mf_norm):
                        if os.path.exists(mf_dis):
                            os.remove(mf_dis)
                        os.rename(mf_norm, mf_dis)

            def enable_physical_package(p_path):
                if not p_path or not os.path.exists(p_path):
                    return
                new_p = p_path
                if p_path.endswith('.disabled'):
                    new_p = p_path[:-9]
                    os.rename(p_path, new_p)
                for mf in ['manifest.json', 'layout.json']:
                    mf_dis = os.path.join(new_p, mf + '.disabled')
                    mf_norm = os.path.join(new_p, mf)
                    if os.path.exists(mf_dis):
                        if os.path.exists(mf_norm):
                            os.remove(mf_norm)
                        os.rename(mf_dis, mf_norm)

            def set_package_state_for_icao(p_path, target_icao, should_enable):
                if not p_path:
                    return
                clean_p = p_path[:-9] if p_path.endswith('.disabled') else p_path
                dis_p = clean_p + '.disabled'
                target_dir = clean_p if os.path.exists(clean_p) else (dis_p if os.path.exists(dis_p) else None)
                if not target_dir:
                    return

                icao_l = target_icao.lower() if target_icao else ""
                matching_bgls = []
                other_bgls = []

                if os.path.exists(target_dir):
                    for root, dirs, files in os.walk(target_dir):
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
                            for f in files:
                                if icao_l and icao_l in f.lower() and (f.lower().endswith('.bgl') or f.lower().endswith('.bgl.disabled')):
                                    matching_bgls.append(os.path.join(root, f))

                    for bgl_p in matching_bgls:
                        if should_enable:
                            if bgl_p.endswith('.bgl.disabled'):
                                new_bgl = bgl_p[:-9]
                                if not os.path.exists(new_bgl):
                                    os.rename(bgl_p, new_bgl)
                        else:
                            if bgl_p.endswith('.bgl'):
                                new_bgl = bgl_p + '.disabled'
                                if not os.path.exists(new_bgl):
                                    os.rename(bgl_p, new_bgl)
                else:
                    if should_enable:
                        enable_physical_package(target_dir)
                    else:
                        disable_physical_package(target_dir)

            if os.path.exists(content_xml_path):
                import xml.etree.ElementTree as ET
                tree = ET.parse(content_xml_path)
                root = tree.getroot()
                changed = False
                for p in root.findall('Package'):
                    name = p.get('name', '')
                    clean = name[:-9] if name.lower().endswith('.disabled') else name
                    p.set('name', clean)
                    if icao.lower() in clean.lower():
                        p.set('active', 'UserDisabled')
                        changed = True
                if changed:
                    tree.write(content_xml_path, encoding='utf-8', xml_declaration=True)

            with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                scanned_airports = json.load(f)
            ap_obj = next((a for a in scanned_airports if a['icao'].upper() == icao.upper()), None)
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

            content_xml_path = r'C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml'

            def disable_physical_package(p_path):
                if not p_path or not os.path.exists(p_path):
                    return
                new_p = p_path
                if not p_path.endswith('.disabled'):
                    new_p = p_path + '.disabled'
                    os.rename(p_path, new_p)
                for mf in ['manifest.json', 'layout.json']:
                    mf_dis = os.path.join(new_p, mf + '.disabled')
                    mf_norm = os.path.join(new_p, mf)
                    if os.path.exists(mf_dis):
                        if os.path.exists(mf_norm):
                            os.remove(mf_dis)
                        else:
                            os.rename(mf_dis, mf_norm)

            def enable_physical_package(p_path):
                if not p_path or not os.path.exists(p_path):
                    return
                new_p = p_path
                if p_path.endswith('.disabled'):
                    new_p = p_path[:-9]
                    os.rename(p_path, new_p)
                for mf in ['manifest.json', 'layout.json']:
                    mf_dis = os.path.join(new_p, mf + '.disabled')
                    mf_norm = os.path.join(new_p, mf)
                    if os.path.exists(mf_dis):
                        if os.path.exists(mf_norm):
                            os.remove(mf_norm)
                        os.rename(mf_dis, mf_norm)

            def set_package_state_for_icao(p_path, target_icao, should_enable):
                if not p_path:
                    return
                clean_p = p_path[:-9] if p_path.endswith('.disabled') else p_path
                dis_p = clean_p + '.disabled'
                target_dir = clean_p if os.path.exists(clean_p) else (dis_p if os.path.exists(dis_p) else None)
                if not target_dir:
                    return

                icao_l = target_icao.lower() if target_icao else ""
                matching_bgls = []
                other_bgls = []

                if os.path.exists(target_dir):
                    for root, dirs, files in os.walk(target_dir):
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
                            for f in files:
                                if icao_l and icao_l in f.lower() and (f.lower().endswith('.bgl') or f.lower().endswith('.bgl.disabled')):
                                    matching_bgls.append(os.path.join(root, f))

                    for bgl_p in matching_bgls:
                        if should_enable:
                            if bgl_p.endswith('.bgl.disabled'):
                                new_bgl = bgl_p[:-9]
                                if not os.path.exists(new_bgl):
                                    os.rename(bgl_p, new_bgl)
                        else:
                            if bgl_p.endswith('.bgl'):
                                new_bgl = bgl_p + '.disabled'
                                if not os.path.exists(new_bgl):
                                    os.rename(bgl_p, new_bgl)
                else:
                    if should_enable:
                        enable_physical_package(target_dir)
                    else:
                        disable_physical_package(target_dir)

            target_clean = target_folder_name[:-9] if target_folder_name.lower().endswith('.disabled') else target_folder_name

            if os.path.exists(content_xml_path):
                import xml.etree.ElementTree as ET
                tree = ET.parse(content_xml_path)
                root = tree.getroot()
                changed = False
                seen = set()
                to_remove = []

                for p in list(root.findall('Package')):
                    name = p.get('name', '')
                    clean = name[:-9] if name.lower().endswith('.disabled') else name
                    p.set('name', clean)

                    if clean.lower() in seen:
                        to_remove.append(p)
                        changed = True
                        continue
                    seen.add(clean.lower())

                    if target_clean != 'DEFAULT' and (clean.lower() == target_clean.lower() or target_clean.lower() in clean.lower()):
                        p.set('active', 'Activated')
                        changed = True
                    elif icao.lower() in clean.lower():
                        p.set('active', 'UserDisabled')
                        changed = True

                for p in to_remove:
                    root.remove(p)

                if changed:
                    tree.write(content_xml_path, encoding='utf-8', xml_declaration=True)

            with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                scanned_airports = json.load(f)
            ap_obj = next((a for a in scanned_airports if a['icao'].upper() == icao.upper()), None)
            if ap_obj and ap_obj.get('all_sources'):
                for src in ap_obj['all_sources']:
                    fn = src.get('folder_name', '')
                    pkg_p = src.get('package_path', '')
                    fn_clean = fn[:-9] if fn.lower().endswith('.disabled') else fn

                    if target_clean != 'DEFAULT' and (fn_clean.lower() == target_clean.lower() or target_clean.lower() in fn_clean.lower()):
                        set_package_state_for_icao(pkg_p, icao, should_enable=True)
                    else:
                        set_package_state_for_icao(pkg_p, icao, should_enable=False)

            airports = fast_update_airport_cache(icao, target_pkg_name=target_clean)
            return json.dumps({"status": "ok", "airports": airports}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def toggle_fix_patch(self, path, icao):
        try:
            if not path:
                return json.dumps({"status": "error", "message": "No path provided"})

            content_xml_path = r'C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml'
            
            clean_name = os.path.basename(path)
            if clean_name.lower().endswith('.disabled'):
                clean_name = clean_name[:-9]

            target_path = path

            def disable_physical_package(p_path):
                if not p_path or not os.path.exists(p_path):
                    return p_path
                new_p = p_path
                if not p_path.endswith('.disabled'):
                    new_p = p_path + '.disabled'
                    os.rename(p_path, new_p)
                for mf in ['manifest.json', 'layout.json']:
                    mf_dis = os.path.join(new_p, mf + '.disabled')
                    mf_norm = os.path.join(new_p, mf)
                    if os.path.exists(mf_dis):
                        if os.path.exists(mf_norm):
                            os.remove(mf_dis)
                        else:
                            os.rename(mf_dis, mf_norm)
                return new_p

            def enable_physical_package(p_path):
                if not p_path or not os.path.exists(p_path):
                    return p_path
                new_p = p_path
                if p_path.endswith('.disabled'):
                    new_p = p_path[:-9]
                    os.rename(p_path, new_p)
                for mf in ['manifest.json', 'layout.json']:
                    mf_dis = os.path.join(new_p, mf + '.disabled')
                    mf_norm = os.path.join(new_p, mf)
                    if os.path.exists(mf_dis):
                        if os.path.exists(mf_norm):
                            os.remove(mf_norm)
                        os.rename(mf_dis, mf_norm)
                return new_p

            target_path = path
            if not os.path.isabs(target_path) or not os.path.exists(target_path):
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

            airports = run_scan()
            return json.dumps({"status": "ok", "enabled": should_enable, "airports": airports}, ensure_ascii=False)
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
                            pkg_icaos = folder_to_icaos.get(item_clean.lower()) or resolve_package_icaos(item_clean)

                            is_keep = any(k in keep_icaos for k in pkg_icaos)

                            if is_community:
                                try:
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
                                                disabled_by_flight_mode.append(item)
                                except Exception as rename_err:
                                    print(f"Skipping rename for {item}: {rename_err}")
                    except Exception as e:
                        print(f"Error processing {td} during flight optimizer:", e)

            # Update MSFS Native Content.xml (UserDisabled / Activated)
            update_msfs_content_xml(keep_icaos=keep_icaos, restore_all=False, folder_to_icaos=folder_to_icaos, third_party_airport_pkgs=third_party_airport_pkgs)

            settings['flight_mode'] = {
                'active': True,
                'disabled_count': disabled_count,
                'icaos': list(keep_icaos),
                'disabled_folders': disabled_by_flight_mode
            }
            save_settings(settings)

            return json.dumps({
                "status": "ok",
                "enabled_count": enabled_count,
                "disabled_count": disabled_count
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
                                # If full_reset is False and we have flight_disabled_folders, only restore folders disabled by flight mode!
                                if not full_reset and flight_disabled_folders and (item_clean not in flight_disabled_folders and item not in flight_disabled_folders):
                                    continue

                                dis_p = os.path.join(td, item)
                                orig_p = os.path.join(td, item_clean)
                                if os.path.isdir(dis_p) and not os.path.exists(orig_p):
                                    try:
                                        os.rename(dis_p, orig_p)
                                        re_enabled_count += 1
                                    except Exception as e:
                                        print(f"Error restoring {dis_p}:", e)
                    except Exception as e:
                        print(f"Error scanning {td} for restore:", e)

            # Update MSFS Native Content.xml to restore UserDisabled packages back to Activated
            update_msfs_content_xml(restore_all=True)

            settings['flight_mode'] = {'active': False, 'icaos': [], 'disabled_folders': []}
            save_settings(settings)

            airports = run_scan()
            return json.dumps({
                "status": "ok",
                "re_enabled_count": re_enabled_count,
                "airports": airports
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

    def _extract_archive_files(self, archive_path_or_bytes, ext, gsx_dir, icao=""):
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

            # 4. Clean up old GSX files for this ICAO if target ICAO is specified
            target_icao = (icao or '').upper()
            if target_icao and len(target_icao) == 4:
                try:
                    for existing_f in os.listdir(gsx_dir):
                        if existing_f.lower() == 'configuration.ini':
                            continue
                        if existing_f.upper().startswith(target_icao) and existing_f.lower().endswith(('.ini', '.py')):
                            old_path = os.path.join(gsx_dir, existing_f)
                            try:
                                os.remove(old_path)
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

    def install_gsx_profile(self, icao="", file_path="", base64_data="", filename=""):
        import shutil
        import base64
        
        settings = get_settings()
        gsx_dir = settings.get("gsx_profile_path", get_default_gsx_path())
        
        if not os.path.exists(gsx_dir):
            os.makedirs(gsx_dir, exist_ok=True)
            
        installed_files = []
        target_icao = (icao or '').upper()
        
        try:
            # Clean up existing old GSX profile files for this ICAO if installing direct single .ini or .py
            if target_icao and len(target_icao) == 4:
                try:
                    for existing_f in os.listdir(gsx_dir):
                        if existing_f.lower() == 'configuration.ini':
                            continue
                        if existing_f.upper().startswith(target_icao) and existing_f.lower().endswith(('.ini', '.py')):
                            old_path = os.path.join(gsx_dir, existing_f)
                            try:
                                os.remove(old_path)
                            except Exception: pass
                except Exception: pass

            # 1. Base64 dropped file handling
            if base64_data and filename:
                if "," in base64_data:
                    base64_data = base64_data.split(",", 1)[1]
                    
                file_bytes = base64.b64decode(base64_data)
                ext = os.path.splitext(filename)[1].lower()
                
                if ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                    installed_files = self._extract_archive_files(file_bytes, ext, gsx_dir, icao=target_icao)
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
                    installed_files = self._extract_archive_files(file_path, ext, gsx_dir, icao=target_icao)
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

    def check_update(self, icao, name, vendor, version, pricing_type=""):
        import webbrowser
        import urllib.parse
        
        PAYWARE_VENDOR_URLS = {
            'orbx': 'https://orbxdirect.com/search?q={query}',
            'aerosoft': 'https://www.aerosoft.com/en/search?sSearch={query}',
            'inibuilds': 'https://inibuilds.com/search?q={query}',
            'flightbeam': 'https://www.flightbeam.com/search?q={query}',
            'flytampa': 'https://www.flytampa.org/',
            'pyreegue': 'https://pyreegue.dev/',
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
            'verticalsim': 'https://verticalsim.com/shop/',
            'latinvfr': 'https://www.latinvfr.com/',
            'pilotplus': 'https://pilotplus.io/',
            'threshold': 'https://www.thresholdx.net/search?q={query}',
            'tailstrike': 'https://tailstrikedesigns.com/',
            'gaya': 'https://www.gaya-simulations.com/',
            'gaya simulations': 'https://www.gaya-simulations.com/',
            'dominicdesignteam': 'https://secure.simmarket.com/advanced_search_result.php?keywords={query}',
            'taimedia': 'https://secure.simmarket.com/advanced_search_result.php?keywords={query}'
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
                target_url = f"https://flightsim.to/search?q={q_enc}"

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
    webview.start(debug=False)

if __name__ == '__main__':
    main()
