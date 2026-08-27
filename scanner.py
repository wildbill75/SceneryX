import os
import sys
import json
import re

def get_resource_file_path(filename):
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

AIRPORT_DB_PATH = get_resource_file_path("airports.json")
def get_user_data_dir():
    appdata = os.environ.get('APPDATA')
    if not appdata:
        appdata = os.path.expanduser('~')
    user_dir = os.path.join(appdata, 'SceneryX')
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

USER_DATA_DIR = get_user_data_dir()
OUTPUT_JSON_PATH = os.path.join(USER_DATA_DIR, "installed_airports.json")
SETTINGS_JSON_PATH = os.path.join(USER_DATA_DIR, "settings.json")
RATINGS_JSON_PATH = os.path.join(USER_DATA_DIR, "ratings.json")
CUSTOM_PRICES_JSON_PATH = os.path.join(USER_DATA_DIR, "custom_prices.json")

# Auto-migrate any existing legacy config files from local executable folder to %APPDATA%/SceneryX/
for filename, target_path in [
    ("settings.json", SETTINGS_JSON_PATH),
    ("ratings.json", RATINGS_JSON_PATH),
    ("custom_prices.json", CUSTOM_PRICES_JSON_PATH),
    ("installed_airports.json", OUTPUT_JSON_PATH)
]:
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if os.path.exists(local_path) and not os.path.exists(target_path):
        try:
            import shutil
            shutil.copy2(local_path, target_path)
        except Exception:
            pass

COMMERCIAL_PAYWARE_VENDORS = {
    # Major Publishers & Stores
    'orbx', 'orbxdirect', 'contrail', 'inibuilds', 'inimanager', 'aerosoft', 'aerosoftone',
    'justflight', 'just flight', 'simmarket', 'flightsimto_store', 'flightsimto store',
    
    # Tier-1 & Tier-2 Scenery Studios
    'flytampa', 'flytampa-amsterdam', 'flightbeam', 'flightbeam studios', 'fsdreamteam', 'fsdt',
    'drzewieckidesign', 'drzewiecki', 'pyreegue', 'pyreegue dev co', 'mkstudios', 'mk-studios',
    'gaya', 'gaya simulations', 'latinvfr', 'lvfr', 'uk2000', 'uk2000scenery', 'pilotplus', 'pilot plus',
    'justsim', 'francevfr', 'france vfr', 'deimosinc', 'deimos inc', 'deimos', 'bmw', 'bmw scenery',
    'amsim', 'fsx3d', 'lhsimulations', 'pilotexperiencesim', 'pilot experience sim', 'tailstrike',
    'tailstrike designs', 'taburet', 'regesim', 'sea front simulations', 'verticalsim', 'samscene3d',
    'samscene', 'boundless', 'macco', 'macco simulations', 'fsdg', 'tdm scenery design', 'sim-wings', 'simwings', 'sim_wings',
    'redwing', 'redwingsim', 'redwing simulations', 'jetstream', 'jetstream designs',
    'slh', 'slhsimdesigns', 'slh_sim_designs', 'slh sim designs', 'fly2high', 'northernsky', 'northern sky',
    'feelthere', 'tropicalsim', 'bmworld', 'bmworld & amsim', 'noolaero', 'nool', 'impulse simulation',
    'impulserc', 'magmexico', 'pazscenery', 'barelli', 'barelli msfs', 'pacific islands simulation', 'pacsim',
    'wf scenery studio', 'wfscenery', 'wfscenery studio', 'imaginesim', 'taxi2gate', 't2g',
    'vividvis', 'vivid visual', 'flightsim development group', 'beautiful model of the world', 'bmtw',
    'axonos', 'rdpreset', 'rdpresets', 'finch', 'finch simulation', 'dreamscenery', 'b4real',
    'x-codr', 'xcodr', 'godzone', 'chudoba', 'chudoba design', 'richard neswold', 'shining',
    'flightsim studio', 'fss', 'stardust', 'stardust simulations', 'skiathos', 'niels', 'rwytack',
    'rwy26', 'rwy26 simulations', 'flyingscenery', 'flying scenery', 'skyline simulations',
    'fsimstudio', 'fsimstudios', 'fs painter', 'skyport', 'skyport design', 'designworks',
    'airworthy designs', 'digital design', 'funner2010', 'prealistic', 'perfect flight',
    'chilek', 'chilek scenery', 'mexicoovfr', 'mexico vfr', 'southsim', 'southsimulations',
    'scenerytr', 'scenerytrdesign', 'scenerytr design', 'scenery tr', 'agsim', 'ag-sim', 'st-designs'
}

VENDOR_MAP = {
    'argaeus': 'Argaeus',
    'hb': 'Argaeus',
    'scenerytr': 'SceneryTR Design',
    'scenerytrdesign': 'SceneryTR Design',
    'scenerytr design': 'SceneryTR Design',
    'scenery tr': 'SceneryTR Design',
    'agsim': 'AG Sim',
    'ag-sim': 'AG Sim',
    'slh': 'SLH Sim Designs',
    'slhsimdesigns': 'SLH Sim Designs',
    'slh_sim_designs': 'SLH Sim Designs',
    'fly2high': 'Fly2High',
    'northernsky': 'Northern Sky Studio',
    'feelthere': 'FeelThere',
    'tropicalsim': 'TropicalSim',
    'bmworld': 'BMWorld & AMSim',
    'nool': 'Nool Aeroservices',
    'noolaero': 'Nool Aeroservices',
    'impulse': 'Impulse Simulation',
    'impulserc': 'Impulse Simulation',
    'wfscenery': 'WF Scenery Studio',
    'imaginesim': 'ImagineSim',
    'taxi2gate': 'Taxi2Gate',
    't2g': 'Taxi2Gate',
    'axonos': 'Axonos',
    'rdpreset': 'RDPresets',
    'rdpresets': 'RDPresets',
    'fsimstudio': 'FSimStudios',
    'fsimstudios': 'FSimStudios',
    'digitaldesign': 'Digital Design',
    'airworthy': 'Airworthy Designs',
    'lvfr': 'LatinVFR',
    'latinvfr': 'LatinVFR',
    'asobo': 'Microsoft / Asobo',
    'microsoft': 'Microsoft / Asobo',
    'simwings': 'Sim-Wings / Aerosoft',
    'sim-wings': 'Sim-Wings / Aerosoft',
    'sim_wings': 'Sim-Wings / Aerosoft',
    'aerosoft': 'Aerosoft',
    'inibuilds': 'iniBuilds',
    'flytampa': 'FlyTampa',
    'drzewieckidesign': 'Drzewiecki Design',
    'drzewiecki': 'Drzewiecki Design',
    'gaya-simulations': 'Gaya Simulations',
    'gayasimulations': 'Gaya Simulations',
    'gaya': 'Gaya Simulations',
    'uk2000scenery': 'UK2000 Scenery',
    'uk2000': 'UK2000 Scenery',
    'pilotplus': 'Pilot Plus',
    'justsim': 'JustSim',
    'francevfr': 'France VFR',
    'lisium': 'Lisium',
    'lisiumsim': 'Lisium',
    'deimosinc': 'DeimoS Inc',
    'deimos': 'DeimoS Inc',
    'bmw': 'BMW Scenery',
    'amsim': 'AMSim',
    'fsx3d': 'FSX3D',
    'lhsimulations': 'LHSimulations',
    'pilotexperiencesim': 'Pilot Experience Sim',
    'orbx': 'Orbx',
    'pyreegue': 'Pyreegue Dev Co',
    'flightbeam': 'Flightbeam Studios',
    'mkstudios': 'MK-Studios',
    'tailstrike': 'Tailstrike Designs',
    'taburet': 'Taburet',
    'regesim': 'Regesim',
    'sea': 'Sea Front Simulations',
    'verticalsim': 'Verticalsim',
    'samscene': 'SamScene3D',
    'boundless': 'Boundless',
    'macco': 'Macco Simulations',
    'fsdg': 'FSDG',
    'redwing': 'Redwing Simulations',
    'jetstream': 'Jetstream Designs',
    'fsdreamteam': 'FSDreamTeam'
}

EXCLUDE_WORDS = {
    'wasm', 'logo', 'cata', 'lvar', 'data', 'nav2', 'auto', 'vfr1', 'vfr2', 'pack', 
    'mesh', 'traf', 'airc', 'livr', 'tool', 'aircraft', 'livery', 'liveries', 'cabin',
    'utility', 'sound', 'vfx', 'effect', 'effects', 'traffic', 'vdgs', 'toolbar', 'tree', 'trees',
    'interior', 'scenery', 'project', 'version', 'mode', 'model', 'text', 'texture', 'html', 'json',
    'ktx2', 'ktx2p', 'sign', 'fact', 'wall', 'link', 'pa33', 'pa34', 'pa35', 'pa36', 'pa37', 'sdv2',
    'edge', 'leaf', 'side', 'fact', 'link', 'code', 'base', 'area', 'zone', 'west', 'east', 'south',
    'north', 'city', 'park', 'port', 'view', 'main', 'road', 'hill', 'lake', 'bay',
    'panama', 'france', 'germany', 'spain', 'italy', 'england', 'poland', 'japan', 'china',
    'canada', 'mexico', 'brazil', 'australia', 'alaska', 'hawaii', 'california', 'texas', 'florida'
}

NON_AIRPORT_KEYWORDS = [
    'landingchallenge', 'landing-challenge', 'point-of-interest', 'pointofinterest',
    'discovery', 'passiveaircraft', 'passive-aircraft', 'challenges', 'activities', 'activity',
    'certification', 'procedural', 'trainings', 'training', 'travelbook', 'simobjects', 'ships',
    'modellib', 'vertical-obstructions', 'verticalobstructions', 'crowds', 'gliders',
    'asobo-aircraft', 'fs20-asobo-aircraft', 'fs24-asobo-aircraft', 'fnx-aircraft', 'flybywire-aircraft',
    'fbw-a20n', 'fnx-livery', 'livery', 'aircraft', 'utility', 'toolbar', 'disastertracker',
    'fsdreamteam-gsx', 'gsx-pro', 'kt-gsx', 'papadelta-', 'navigraph', 'fsltl', 'airrace', 'redbull',
    'landmarks', 'landmark', 'aerial', 'cityscape', 'photogrammetry', 'seasons', 'biomes',
    'vfr-landmarks', 'vfr_landmarks', 'vfr-city', 'poilocalisation', 'worldupdate', 'world-update',
    'north-america-mesh', 'europe-mesh', 'south-america-mesh', 'asia-mesh', 'africa-mesh', 'oceania-mesh',
    'fs-base', 'fs24-fs-base', 'fs20-fs-base', 'coverage-map', 'coverage', 'genericairports',
    'generic-airports', 'bushtrip', 'bush-trip', 'bush', 'bushchallenge', 'bush-challenge',
    'flight-tutorials', 'tutorials', 'tutorial', 'shortto', 'shortldg', 'waterldg', 'waterto', 'watertr',
    'downdraft', 'career', 'career-mode', 'flight-lessons', 'lessons', 'examination', 'exam', 'emergency',
    'asobo-live', 'asobo-nav', 'asobo-generic'
]

ADDON_LIBRARY_KEYWORDS = [
    'models', 'model', 'library', 'libraries', 'interior', 'extension', 'mesh', 'aerial',
    'ortho', 'vdgs', 'lights', 'trees', 'vegetation', 'sound', 'gsx', 'enhancement', 'optional'
]

FIX_PATCH_KEYWORDS = [
    'fix', 'patch', 'flatten', 'fixer', 'correction', 'enhancement', 'mod',
    'update-fix', 'gsx-fix', 'vdgs-fix', 'ils-fix', 'nav-fix', 'lighting-fix',
    'taxiway-fix', 'runway-fix', 'flatten-fix', 'zparking', 'parking', 'vdgs',
    'stalex', 'stg', 'overlay', 'exclusion', 'excl', 'profile', 'xavios',
    'jetway', 'jetways', 'gate', 'gates', 'frequency', 'frequencies', 'marking', 'markings'
]

# Official MSFS Standard Edition Handcrafted Airports (Base Game Standard + World Updates I to XVIII)
ASOBO_STANDARD_ICAOS = {
    # MSFS Base Game Standard Edition Handcrafted Airports (40)
    'KASE', 'WX53', 'SPGL', 'LFLJ', 'EIDL', 'HUEN', 'LPMA', 'LXGB', 'TFFJ', 'RJTT',
    'LOWI', 'TNCS', 'EYLI', 'ZUGU', 'EYKL', 'KLAX', 'SEQM', 'NZMF', 'KSWF', 'LFMN',
    'KMCO', 'LFPG', 'VQPR', 'NZQN', 'SBGL', 'KSEZ', 'MRSN', 'YSSY', 'KTEX', 'VNLK',
    'MHTG', 'CYYZ', 'CYVR', 'KCRW', 'NZWN', 'KMPI',

    # World Update I: Japan
    'PAFR', 'RJFU', 'RJCK', 'RJTH', 'RJX8', 'ROKR', 'RORS',

    # World Update II: USA
    'KATL', 'KFHR', 'KDFW', 'C53',

    # World Update III: UK & Ireland
    'EGPR', 'EGGP', 'EGHC', 'EGCB', 'EG78',

    # World Update IV: France & Benelux
    'LFHM', 'EHRD',

    # World Update V: Nordics
    'EKRN', 'BIIS', 'ESSA', 'ENSB', 'EFVA',

    # World Update VI: Germany, Austria, Switzerland
    'LOWK', 'EDHL', 'LSZR', 'EDDS',

    # World Update VII: Australia
    'YMBT', 'YLRE', 'YPBO', 'YSHL',

    # World Update VIII: Iberia (Spain & Portugal)
    'LESU', 'LPPI', 'LPFR', 'LECO',

    # World Update IX: Italy & Malta
    'LICJ', 'LILO', 'LIRJ', 'LIPB',

    # World Update XI: Canada
    'CYCG',

    # World Update XII: New Zealand
    'NZGS', 'NZMJ', 'NZQE', 'NZRO', 'NZTL', 'NZWR', 'NZWS', 'T004',

    # World Update XIII: Oceania, Hawaii, Antarctica
    'SCIP', 'PHKO', 'AGGN', 'NTTB', 'NTTM', 'NFFN', 'PLPA', 'AYIN',

    # World Update XIV: Central Eastern Europe
    'LKKV', 'LZTT', 'LHPP', 'LJZA', 'LDRI', 'LQPD',

    # World Update XV: Nordics 2 & Greenland
    'BIAR', 'ENRA', 'ESNQ', 'EFIV', 'ENLK',

    # World Update XVI: Caribbean
    'MUCL', 'MDPP', 'MTCA', 'MKJS', 'TTCP', 'MYEH', 'TFFS',

    # World Update XVII: UK & Ireland 2
    'EGLF', 'EGSS', 'EICK', 'EGPB', 'EGFF',

    # World Update XVIII: Germany, Austria, Switzerland 2
    'LOWS', 'EDDM', 'LSZB'
}

# Deluxe Edition Specific Handcrafted Airports
ASOBO_DELUXE_ICAOS = {'EDHL', 'EGPR', 'LECO', 'LSZA', 'KDEN'}

# Premium Deluxe Specific Handcrafted Airports
ASOBO_PREMIUM_DELUXE_ICAOS = {'KSFO', 'FACT', 'HECA', 'OMAA', 'RJTH', 'EHAM', 'EGLL', 'KORD', 'LEMD', 'OMDB'}

WORLD_UPDATES_MAP = {
    # World Update I: Japan
    'PAFR': 'World Update I: Japan', 'RJFU': 'World Update I: Japan', 'RJCK': 'World Update I: Japan',
    'RJTH': 'World Update I: Japan', 'RJX8': 'World Update I: Japan', 'ROKR': 'World Update I: Japan',
    'RORS': 'World Update I: Japan', 'RJTT': 'World Update I: Japan', 'RJAA': 'World Update I: Japan',

    # World Update II: USA
    'KATL': 'World Update II: USA', 'KFHR': 'World Update II: USA', 'KDFW': 'World Update II: USA',
    'C53': 'World Update II: USA', 'KSEAT': 'World Update II: USA', 'KFRH': 'World Update II: USA',

    # World Update III: UK & Ireland
    'EGPR': 'World Update III: UK & Ireland', 'EGGP': 'World Update III: UK & Ireland',
    'EGHC': 'World Update III: UK & Ireland', 'EGCB': 'World Update III: UK & Ireland',
    'EG78': 'World Update III: UK & Ireland', 'EGLL': 'World Update III: UK & Ireland',
    'EGBB': 'World Update III: UK & Ireland', 'EGJJ': 'World Update III: UK & Ireland',

    # World Update IV: France & Benelux
    'LFHM': 'World Update IV: France & Benelux', 'EHRD': 'World Update IV: France & Benelux',
    'LFPG': 'World Update IV: France & Benelux', 'LFLB': 'World Update IV: France & Benelux',
    'LFMN': 'World Update IV: France & Benelux', 'EHAM': 'World Update IV: France & Benelux',
    'EBBR': 'World Update IV: France & Benelux', 'LFPO': 'World Update IV: France & Benelux',

    # World Update V: Nordics
    'EKRN': 'World Update V: Nordics', 'BIIS': 'World Update V: Nordics', 'ESSA': 'World Update V: Nordics',
    'ENSB': 'World Update V: Nordics', 'EFVA': 'World Update V: Nordics', 'EKCH': 'World Update V: Nordics',
    'ENGM': 'World Update V: Nordics', 'BIKF': 'World Update V: Nordics',

    # World Update VI: DACH (Germany, Austria, Switzerland)
    'LOWK': 'World Update VI: DACH', 'EDHL': 'World Update VI: DACH',
    'LSZR': 'World Update VI: DACH', 'EDDS': 'World Update VI: DACH',
    'EDDB': 'World Update VI: DACH', 'EDDF': 'World Update VI: DACH',
    'LOWW': 'World Update VI: DACH', 'LSZH': 'World Update VI: DACH',
    'LOWI': 'World Update VI: DACH', 'LSZA': 'World Update VI: DACH',

    # World Update VII: Australia
    'YMBT': 'World Update VII: Australia', 'YLRE': 'World Update VII: Australia',
    'YPBO': 'World Update VII: Australia', 'YSHL': 'World Update VII: Australia',
    'YSSY': 'World Update VII: Australia', 'YBBN': 'World Update VII: Australia',

    # World Update VIII: Iberia (Spain & Portugal)
    'LPMA': 'World Update VIII: Iberia (Madeira)', 'LESU': 'World Update VIII: Iberia',
    'LPPI': 'World Update VIII: Iberia', 'LPFR': 'World Update VIII: Iberia',
    'LECO': 'World Update VIII: Iberia', 'LEMD': 'World Update VIII: Iberia',
    'LEBL': 'World Update VIII: Iberia', 'LPPT': 'World Update VIII: Iberia',
    'GCXO': 'World Update VIII: Iberia', 'GCTS': 'World Update VIII: Iberia',

    # World Update IX: Italy & Malta
    'LICJ': 'World Update IX: Italy & Malta', 'LILO': 'World Update IX: Italy & Malta',
    'LIRJ': 'World Update IX: Italy & Malta', 'LIPB': 'World Update IX: Italy & Malta',
    'LIRF': 'World Update IX: Italy & Malta', 'LIMC': 'World Update IX: Italy & Malta',
    'LMML': 'World Update IX: Italy & Malta',

    # World Update X: USA
    'KDEN': 'World Update X: USA', 'KSFO': 'World Update X: USA',

    # World Update XI: Canada
    'CYCG': 'World Update XI: Canada', 'CYYZ': 'World Update XI: Canada',
    'CYVR': 'World Update XI: Canada', 'CYHU': 'World Update XI: Canada',

    # World Update XII: New Zealand
    'NZGS': 'World Update XII: New Zealand', 'NZMJ': 'World Update XII: New Zealand',
    'NZQE': 'World Update XII: New Zealand', 'NZRO': 'World Update XII: New Zealand',
    'NZTL': 'World Update XII: New Zealand', 'NZWR': 'World Update XII: New Zealand',
    'NZWS': 'World Update XII: New Zealand', 'T004': 'World Update XII: New Zealand',
    'NZQN': 'World Update XII: New Zealand', 'NZAA': 'World Update XII: New Zealand',

    # World Update XIII: Oceania, Hawaii, Antarctica
    'SCIP': 'World Update XIII: Oceania', 'PHKO': 'World Update XIII: Oceania',
    'AGGN': 'World Update XIII: Oceania', 'NTTB': 'World Update XIII: Oceania',
    'NTTM': 'World Update XIII: Oceania', 'NFFN': 'World Update XIII: Oceania',
    'PLPA': 'World Update XIII: Oceania', 'AYIN': 'World Update XIII: Oceania',

    # World Update XIV: Central & Eastern Europe
    'LKKV': 'World Update XIV: Central Europe', 'LZTT': 'World Update XIV: Central Europe',
    'LHPP': 'World Update XIV: Central Europe', 'LJZA': 'World Update XIV: Central Europe',
    'LDRI': 'World Update XIV: Central Europe', 'LQPD': 'World Update XIV: Central Europe',
    'EPWA': 'World Update XIV: Central Europe', 'LKPR': 'World Update XIV: Central Europe',

    # World Update XV: Nordics II & Greenland
    'BIAR': 'World Update XV: Nordics II', 'ENRA': 'World Update XV: Nordics II',
    'ESNQ': 'World Update XV: Nordics II', 'EFIV': 'World Update XV: Nordics II',
    'ENLK': 'World Update XV: Nordics II', 'ENBR': 'World Update XV: Nordics II',

    # World Update XVI: Caribbean
    'MUCL': 'World Update XVI: Caribbean', 'MDPP': 'World Update XVI: Caribbean',
    'MTCA': 'World Update XVI: Caribbean', 'MKJS': 'World Update XVI: Caribbean',
    'TTCP': 'World Update XVI: Caribbean', 'MYEH': 'World Update XVI: Caribbean',
    'TFFS': 'World Update XVI: Caribbean', 'TNCM': 'World Update XVI: Caribbean',

    # World Update XVII: UK & Ireland II
    'EGLF': 'World Update XVII: UK & Ireland II', 'EGSS': 'World Update XVII: UK & Ireland II',
    'EICK': 'World Update XVII: UK & Ireland II', 'EGPB': 'World Update XVII: UK & Ireland II',
    'EGFF': 'World Update XVII: UK & Ireland II',

    # World Update XVIII: DACH II
    'LOWS': 'World Update XVIII: DACH II', 'EDDM': 'World Update XVIII: DACH II',
    'LSZB': 'World Update XVIII: DACH II', 'EDDN': 'World Update XVIII: DACH II',

    # City Updates
    'EGLC': 'City Update I: London', 'LFPN': 'City Update II: France',
    'EDDS': 'City Update III: Germany', 'LSGG': 'City Update IV: Switzerland',

    # Base Game Edition Handcrafted
    'KORD': 'Premium Deluxe Base', 'OMDB': 'Premium Deluxe Base',
    'FACT': 'Premium Deluxe Base', 'HECA': 'Premium Deluxe Base',
    'OMAA': 'Premium Deluxe Base', 'KLAX': 'Standard Edition Base',
    'SEQM': 'Standard Edition Base', 'NZMF': 'Standard Edition Base',
    'VQPR': 'Standard Edition Base', 'SBGL': 'Standard Edition Base',
    'KASE': 'Standard Edition Base', 'LXGB': 'Standard Edition Base',
    'TFFJ': 'Standard Edition Base', 'WX53': 'Standard Edition Base',
    'SPGL': 'Standard Edition Base', 'LFLJ': 'Standard Edition Base'
}

def get_world_update_name(icao, folder_name=""):
    if icao in WORLD_UPDATES_MAP:
        return WORLD_UPDATES_MAP[icao]
    fn = (folder_name or "").lower()
    if "iberia" in fn: return "World Update VIII: Iberia"
    if "japan" in fn: return "World Update I: Japan"
    if "nordic" in fn: return "World Update V: Nordics"
    if "france" in fn or "benelux" in fn: return "World Update IV: France & Benelux"
    if "italy" in fn or "malta" in fn: return "World Update IX: Italy & Malta"
    if "caribbean" in fn: return "World Update XVI: Caribbean"
    if "oceania" in fn: return "World Update XIII: Oceania"
    if "australia" in fn: return "World Update VII: Australia"
    if "newzealand" in fn: return "World Update XII: New Zealand"
    if "canada" in fn: return "World Update XI: Canada"
    if "uk" in fn or "ireland" in fn: return "World Update III: UK & Ireland"
    if "germany" in fn or "dach" in fn or "austria" in fn: return "World Update VI: DACH"
    if "cityupdate" in fn: return "Asobo City Update"
    if "worldupdate" in fn: return "Asobo World Update"
    return "Asobo Sim Update"

SPECIAL_BUNDLE_MAP = {
    # France VFR Paris VFR Airports (LFPB Le Bourget & LFPG are Asobo, remaining 7 are France VFR Payware)
    'francevfr-airport-pidf-parisvfrairports': ['LFPN', 'LFPV', 'LFPQ', 'LFPT', 'LFPK', 'LFPL', 'LFPM'],
    'fs20-francevfr-airport-pidf-parisvfrairports': ['LFPN', 'LFPV', 'LFPQ', 'LFPT', 'LFPK', 'LFPL', 'LFPM'],

    # France VFR Airport FRANCE Pack 1
    'francevfr-airport-apt1-airportfrance-pack1': ['LFBD', 'LFMT', 'LFRB'],
    'fs20-francevfr-airport-apt1-airportfrance-pack1': ['LFBD', 'LFMT', 'LFRB'],

    # France VFR Sud Est Airports Bundle
    'francevfr-800-sevfrairports': [
        'LFHH', 'LFHN', 'LFHS', 'LFHV', 'LFKA', 'LFKO', 'LFKS', 'LFKT', 'LFLG', 'LFLI', 'LFLP', 'LFLQ', 
        'LFLU', 'LFLY', 'LFMA', 'LFMC', 'LFMD', 'LFME', 'LFMH', 'LFMI', 'LFMO', 'LFMQ', 'LFMR', 'LFMV', 
        'LFMY', 'LFMZ', 'LFNB', 'LFNF', 'LFNR', 'LFNT', 'LFTH', 'LFTZ', 'LFYS'
    ],
    'francevfr-800-marseille': ['LFML']
}

BUNDLE_PACKAGE_PRICES = {
    'francevfr-airport-pidf-parisvfrairports': {'price': 39.00, 'name': 'France VFR - Paris VFR Airports Pack'},
    'fs20-francevfr-airport-pidf-parisvfrairports': {'price': 39.00, 'name': 'France VFR - Paris VFR Airports Pack'},
    'francevfr-800-sevfrairports': {'price': 39.00, 'name': 'France VFR - Sud-Est VFR Airports Pack'},
    'francevfr-800-marseille': {'price': 14.99, 'name': 'France VFR - Marseille Airport'},
}

# Known Real Retail Prices Catalog in EUR (€)
# Known Real Retail Prices Catalog in EUR (€)
KNOWN_PAYWARE_PRICES = {
    # Specific Package Folder Patterns
    'francevfr-airport-apt1': 7.47, 'francevfr-airport-pidf': 5.00,
    'scenerytr-airport-ltfm-istanbul': 21.99,
    'slh_sim_designs_soca_fs24': 13.99
}

FOLDER_SIZE_CACHE_PATH = os.path.join(USER_DATA_DIR, "folder_sizes.json")

def load_folder_size_cache():
    if os.path.exists(FOLDER_SIZE_CACHE_PATH):
        try:
            with open(FOLDER_SIZE_CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_folder_size_cache(cache):
    try:
        with open(FOLDER_SIZE_CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def get_folder_size_formatted(folder_path, size_cache=None):
    if not os.path.exists(folder_path):
        return ""
    try:
        mtime = os.path.getmtime(folder_path)
    except Exception:
        mtime = 0

    if size_cache is not None and folder_path in size_cache:
        cached = size_cache[folder_path]
        if cached.get('mtime') == mtime and cached.get('size_str'):
            return cached['size_str']

    try:
        total_size = 0
        if os.path.isfile(folder_path):
            total_size = os.path.getsize(folder_path)
        else:
            def scan_dir(p):
                nonlocal total_size
                with os.scandir(p) as it:
                    for entry in it:
                        if entry.is_file(follow_symlinks=False):
                            total_size += entry.stat(follow_symlinks=False).st_size
                        elif entry.is_dir(follow_symlinks=False):
                            scan_dir(entry.path)
            scan_dir(folder_path)

        if total_size >= 1024 * 1024 * 1024:
            size_str = f"{total_size / (1024**3):.2f} GB"
        elif total_size >= 1024 * 1024:
            size_str = f"{total_size / (1024**2):.1f} MB"
        elif total_size >= 1024:
            size_str = f"{total_size / 1024:.0f} KB"
        else:
            size_str = f"{total_size} B"

        if size_cache is not None:
            size_cache[folder_path] = {'mtime': mtime, 'size_str': size_str}

        return size_str
    except Exception:
        return ""

def load_ratings():
    if os.path.exists(RATINGS_JSON_PATH):
        try:
            with open(RATINGS_JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_rating(icao, rating_val):
    ratings = load_ratings()
    if rating_val > 0:
        ratings[icao] = float(rating_val)
    else:
        ratings.pop(icao, None)
        
    with open(RATINGS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(ratings, f, indent=2, ensure_ascii=False)
    return ratings

def load_custom_prices():
    if os.path.exists(CUSTOM_PRICES_JSON_PATH):
        try:
            with open(CUSTOM_PRICES_JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_custom_price(icao, price_val):
    prices = load_custom_prices()
    if price_val is not None and float(price_val) >= 0:
        prices[icao] = float(price_val)
    else:
        prices.pop(icao, None)
    with open(CUSTOM_PRICES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(prices, f, indent=2, ensure_ascii=False)
    return prices

def get_estimated_price(icao, folder_name, vendor, pricing_type, english_type, is_asobo, custom_prices):
    if icao in custom_prices:
        return float(custom_prices[icao]), True

    if is_asobo or pricing_type in ["Asobo", "Asobo / MS", "Freeware", "Freeware / Flightsim.to"] or "freeware" in str(pricing_type).lower():
        return 0.0, False

    fn_lower = folder_name.lower()

    if fn_lower in KNOWN_PAYWARE_PRICES:
        return KNOWN_PAYWARE_PRICES[fn_lower], False

    for key, price in KNOWN_PAYWARE_PRICES.items():
        if len(key) > 4 and key in fn_lower:
            return price, False

    if english_type == "International":
        return 19.99, False
    elif english_type == "Regional":
        return 14.99, False
    elif english_type == "General Aviation":
        return 9.99, False
    elif english_type == "Heli / Water":
        return 7.99, False

    return 14.99, False

def auto_detect_default_paths():
    local_appdata = os.getenv('LOCALAPPDATA', '')
    appdata = os.getenv('APPDATA', '')

    candidate_roots = [
        ("MSFS 2024", os.path.join(local_appdata, r"Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\Packages")),
        ("MSFS 2020", os.path.join(local_appdata, r"Packages\Microsoft.FlightSimulator_8wekyb3d8bbwe\LocalCache\Packages")),
        ("MSFS Steam", os.path.join(appdata, r"Microsoft Flight Simulator\Packages")),
    ]

    detected_paths = []
    idx = 1

    for sim_name, root in candidate_roots:
        if os.path.exists(root):
            for sub in ['Community', 'Community2024', 'StreamedPackages', 'Official2020', 'Official2024']:
                sub_path = os.path.join(root, sub)
                if os.path.exists(sub_path):
                    detected_paths.append({
                        "id": str(idx),
                        "name": f"{sim_name} - {sub}",
                        "path": sub_path,
                        "enabled": True
                    })
                    idx += 1

    return detected_paths

def get_default_gsx_path():
    appdata = os.getenv('APPDATA', '')
    if appdata:
        gsx_p = os.path.join(appdata, r'Virtuali\GSX\MSFS')
        if os.path.exists(gsx_p):
            return gsx_p
    return r"C:\Users\%USERNAME%\AppData\Roaming\Virtuali\GSX\MSFS"

def scan_gsx_profiles(gsx_dir):
    if not gsx_dir or not os.path.exists(gsx_dir):
        return {}
    
    gsx_map = {}
    try:
        ini_files = [f for f in os.listdir(gsx_dir) if f.endswith('.ini') and f.lower() != 'configuration.ini']
        for f in ini_files:
            fp = os.path.join(gsx_dir, f)
            match = re.match(r'^([a-zA-Z]{4})', f)
            icao = match.group(1).upper() if match else None
            
            if not icao:
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        ic_m = re.search(r'\b([A-Z]{4})\b', content)
                        if ic_m:
                            icao = ic_m.group(1).upper()
                except Exception:
                    pass
            
            if icao:
                gsx_map[icao] = {
                    'filename': f,
                    'path': fp
                }
    except Exception:
        pass
    return gsx_map

def get_settings():
    if os.path.exists(SETTINGS_JSON_PATH):
        try:
            with open(SETTINGS_JSON_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                for item in settings.get("scan_paths", []):
                    if not item.get("name"):
                        sub = os.path.basename(item.get("path", ""))
                        item["name"] = f"MSFS 2024 - {sub}"
                if not settings.get("gsx_profile_path"):
                    settings["gsx_profile_path"] = get_default_gsx_path()
                return settings
        except Exception:
            pass

    default_paths = auto_detect_default_paths()
    settings = {
        "auto_scan_on_startup": True,
        "scan_paths": default_paths,
        "gsx_profile_path": get_default_gsx_path()
    }
    save_settings(settings)
    return settings

def save_settings(settings_data):
    with open(SETTINGS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(settings_data, f, indent=2, ensure_ascii=False)
    return settings_data

def load_airport_database():
    if not os.path.exists(AIRPORT_DB_PATH):
        return {}, {}, {}
    
    with open(AIRPORT_DB_PATH, 'r', encoding='utf-8') as f:
        airports = json.load(f)

    city_index = {}
    name_index = {}

    for icao, ap in airports.items():
        city = ap.get('city')
        if city:
            c_lower = city.lower().strip()
            if len(c_lower) > 3 and c_lower not in EXCLUDE_WORDS:
                if c_lower not in city_index:
                    city_index[c_lower] = []
                city_index[c_lower].append(ap)
                
        name = ap.get('name')
        if name:
            n_lower = name.lower().strip()
            clean_n = re.sub(r'\b(airport|international|heliport|regional|airbase|field|afb|rnas|raf)\b', '', n_lower).strip()
            if len(clean_n) > 3:
                if clean_n not in name_index:
                    name_index[clean_n] = []
                name_index[clean_n].append(ap)
                
    return airports, city_index, name_index

def get_clean_vendor(folder_name, manifest_data):
    fn_lower = folder_name.lower()

    # Strip system prefixes (e.g. communityfs20-, fs24-, etc.)
    clean_fn = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', fn_lower)

    # 1. Check cleaned folder name against VENDOR_MAP first (Folder naming is almost always higher quality than manifest fields)
    for key, pretty_name in VENDOR_MAP.items():
        if key in clean_fn:
            return pretty_name

    # 2. Check manifest creator / author / manufacturer against VENDOR_MAP
    if manifest_data and isinstance(manifest_data, dict):
        creator = str(manifest_data.get('creator', '')).strip()
        author = str(manifest_data.get('author', '')).strip()
        manufacturer = str(manifest_data.get('manufacturer', '')).strip()

        c_check = f"{creator} {author} {manufacturer}".lower()

        for key, pretty_name in VENDOR_MAP.items():
            if key in c_check:
                return pretty_name

        # 3. Only accept manifest candidate if it has a real brand name (> 3 chars, not 2-3 letter dev initials like "HB", "AB", "MS")
        for candidate in [creator, author, manufacturer]:
            if candidate and len(candidate) > 3 and candidate.lower() not in ['handcrafted', 'scenery', 'airport', 'default', 'none', 'unknown', 'france', 'asobo', 'microsoft', 'community creator', 'builder']:
                return candidate

    # 4. Fallback for Asobo / Microsoft
    if 'asobo' in clean_fn or 'microsoft' in clean_fn:
        return 'Microsoft / Asobo'

    # 5. Extract first valid segment from cleaned folder name
    parts = clean_fn.split('-')
    if parts:
        for p in parts:
            if p and p not in ['airport', 'scenery', 'handcrafted', 'france', 'pack', 'project', 'z', 'zzz', 'zzzz', 'msfs2024', 'msfs2020', 'msfs', 'fs20', 'fs24']:
                return p.capitalize()

    return 'Community Creator'

    return 'Community Creator'

def determine_pricing(source_folder, folder_name, vendor, manifest_data):
    fn_lower = folder_name.lower()
    v_lower = vendor.lower()
    creator = (manifest_data.get('creator', '') if manifest_data else '').lower()

    # Pure Asobo / MS default handcrafted sceneries
    if (
        vendor == 'Microsoft / Asobo' 
        or 'asobo studio' in creator
        or 'microsoft' in creator
        or any(fn_lower.startswith(p) for p in ['asobo-', 'microsoft-', 'fs20-asobo-', 'fs20-microsoft-', 'fs24-asobo-', 'fs24-microsoft-'])
    ):
        return "Asobo", False

    s_lower = source_folder.lower()

    # 3rd-Party Payware Marketplace sceneries (France VFR, Gaya, Deimos, BMW, Orbx, etc.)
    if any(p in fn_lower or p in v_lower or p in creator for p in COMMERCIAL_PAYWARE_VENDORS):
        return "Payware", True

    if 'community' in fn_lower or fn_lower.startswith('community'):
        return "Freeware / Flightsim.to", False

    if 'official' in s_lower or 'streamed' in s_lower:
        return "Payware", True

    return "Freeware / Flightsim.to", False

def run_scan():
    airports, city_index, name_index = load_airport_database()
    if not airports:
        print("Airport database not found!")
        return []

    settings = get_settings()
    ratings = load_ratings()
    custom_prices = load_custom_prices()
    folder_size_cache = load_folder_size_cache()
    scan_paths_cfg = settings.get("scan_paths", [])

    content_xml_status = {}
    content_xml_packages = []
    content_xml_path = r'C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml'
    if os.path.exists(content_xml_path):
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(content_xml_path)
            root = tree.getroot()
            for p in root.findall('Package'):
                pkg_name = p.get('name', '')
                act = p.get('active', 'Activated')
                clean_folder = pkg_name[:-9] if pkg_name.endswith('.disabled') else pkg_name
                folder_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', clean_folder.lower())
                is_active = (act == 'Activated')

                if clean_folder.lower() not in content_xml_status:
                    content_xml_status[clean_folder.lower()] = is_active
                else:
                    content_xml_status[clean_folder.lower()] = content_xml_status[clean_folder.lower()] or is_active

                if folder_norm not in content_xml_status:
                    content_xml_status[folder_norm] = is_active
                else:
                    content_xml_status[folder_norm] = content_xml_status[folder_norm] or is_active

                content_xml_packages.append((pkg_name, clean_folder, not is_active))
        except Exception:
            pass

    all_packages = []

    for cfg in scan_paths_cfg:
        if not cfg.get('enabled', True):
            continue
        dp = cfg.get('path', '')
        if not os.path.exists(dp):
            continue

        category_label = cfg.get('name', os.path.basename(dp))
        onestore = os.path.join(dp, 'OneStore')
        target_dirs = [onestore] if os.path.exists(onestore) else [dp]

        for td in target_dirs:
            try:
                items = os.listdir(td)
                for item in items:
                    ipath = os.path.join(td, item)
                    if os.path.isdir(ipath) and item != 'OneStore':
                        clean_folder = item[:-9] if item.endswith('.disabled') else item
                        is_disabled = item.endswith('.disabled') or os.path.exists(os.path.join(ipath, 'manifest.json.disabled')) or not content_xml_status.get(clean_folder.lower(), True)
                        all_packages.append((category_label, item, ipath, is_disabled))
            except Exception:
                pass

    # Dynamic discovery of StreamedPackages & Official packages listed in Content.xml
    def _normalize_pkg(f_name):
        c = f_name[:-9] if f_name.lower().endswith('.disabled') else f_name
        n = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', c.lower())
        n = re.sub(r'-(airport|scenery|pack|project)-', '-', n)
        n = re.sub(r'-(munich|istanbul|london|paris|frankfurt|berlin|tokyo|chicago|newyork|barcelona|madrid|rome)-', '-', n)
        return n

    existing_norms = {_normalize_pkg(f) for _, f, _, _ in all_packages}
    for pkg_name, clean_f, is_dis in content_xml_packages:
        # Ignore uninstalled 3rd-party community packages left over in Content.xml
        p_lower = pkg_name.lower()
        if p_lower.startswith('community') or 'community' in p_lower:
            continue
        fn_norm = _normalize_pkg(clean_f)
        if fn_norm not in existing_norms:
            all_packages.append(("MSFS 2024 - StreamedPackages", clean_f, "", is_dis))
            existing_norms.add(fn_norm)

    detected_map = {}

    disabled_in_xml = set()
    content_xml_path = r'C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml'
    if os.path.exists(content_xml_path):
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(content_xml_path)
            root = tree.getroot()
            for p in root.findall('Package'):
                if p.get('active') == 'UserDisabled':
                    name = p.get('name', '').lower()
                    clean = name[:-9] if name.endswith('.disabled') else name
                    disabled_in_xml.add(clean.lower())
        except Exception:
            pass

    def get_source_priority(cat_name):
        c_lower = cat_name.lower()
        if 'community' in c_lower:
            return 5
        if 'official' in c_lower:
            return 4
        if 'streamed' in c_lower:
            return 1
        return 2

    for cat, folder_name, full_path, is_disabled_pkg in all_packages:
        clean_folder = folder_name[:-9] if folder_name.lower().endswith('.disabled') else folder_name
        fn_lower = clean_folder.lower()
        fn_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', fn_lower)

        is_disabled = is_disabled_pkg
        
        if any(k in fn_lower for k in NON_AIRPORT_KEYWORDS) or '-livery-' in fn_lower or '-aircraft-' in fn_lower:
            continue
            
        found_ap_list = []
        manifest_ctype = ""
        manifest_title = ""
        manifest_data = None
        
        mpath = os.path.join(full_path, 'manifest.json')
        if not os.path.exists(mpath):
            mpath = os.path.join(full_path, 'manifest.json.disabled')

        pkg_order_hint = ""
        if os.path.exists(mpath):
            try:
                with open(mpath, 'r', encoding='utf-8', errors='ignore') as f:
                    manifest_data = json.load(f)
                    manifest_ctype = manifest_data.get('content_type', '').upper()
                    manifest_title = manifest_data.get('title', '')
                    pkg_order_hint = str(manifest_data.get('package_order_hint', '')).lower()
            except Exception:
                pass
                
        if manifest_ctype in ['AIRCRAFT', 'LIVERY', 'TOOL', 'MISC', 'INSTRUMENT']:
            continue
        
        # Check if this package is a fix/patch or a model library/interior/mesh addon rather than a main scenery
        m_title_lower = manifest_title.lower() if manifest_title else ""
        clean_hint = pkg_order_hint
        for hint_term in ['custom_airport_patch', 'bespoke_airport_patch', 'community_airport_patch', 'official_airport_patch', 'airport_patch', 'custom_airport', 'bespoke_airport', 'community_airport']:
            clean_hint = clean_hint.replace(hint_term, '')

        size_str = get_folder_size_formatted(full_path, folder_size_cache) if full_path else ""
        is_small_patch = False
        if size_str:
            if 'KB' in size_str or ' B' in size_str:
                is_small_patch = True
            elif 'MB' in size_str:
                try:
                    mb_val = float(size_str.replace('MB', '').strip())
                    if mb_val < 80.0:
                        is_small_patch = True
                except Exception:
                    pass

        is_fix_patch = (
            any(re.search(rf'\b{re.escape(k)}\b', fn_lower) for k in FIX_PATCH_KEYWORDS)
            or any(fn_lower.endswith(f"_{k}") or fn_lower.endswith(f"-{k}") for k in FIX_PATCH_KEYWORDS)
            or any(k in clean_hint for k in ['patch', 'fix', 'enhancement', 'correction'])
            or any(k in m_title_lower for k in ['fix', 'patch', 'enhancement', 'flatten', 'correction'])
            or (is_small_patch and not (fn_lower.startswith(('asobo-', 'microsoft-', 'fs20-asobo-', 'fs24-asobo-')) or (manifest_data and 'asobo' in str(manifest_data.get('creator','')).lower())))
        )
        is_addon_package = is_fix_patch or any(k in fn_lower for k in ADDON_LIBRARY_KEYWORDS)

        if fn_lower in SPECIAL_BUNDLE_MAP:
            bundle_icaos = SPECIAL_BUNDLE_MAP[fn_lower]
            for icao in bundle_icaos:
                if icao in airports:
                    found_ap_list.append((airports[icao], f"Special Bundle Map ({icao})"))

        # Primary token matching on folder name
        tokens = re.split(r'[-_ ]+', fn_lower)
        for t in tokens:
            t_upper = t.upper()
            if len(t_upper) == 4 and t_upper in airports and t.lower() not in EXCLUDE_WORDS:
                found_ap_list.append((airports[t_upper], f"Folder ICAO ({t_upper})"))
                break

        # Manifest Title explicit ICAO matching
        if not found_ap_list and manifest_title:
            m_tokens = re.findall(r'([A-Za-z]{4})', manifest_title)
            for tok in m_tokens:
                tok_u = tok.upper()
                if tok_u in airports and tok.lower() not in EXCLUDE_WORDS:
                    found_ap_list.append((airports[tok_u], f"Manifest Title ({tok_u})"))
                    break

        # Layout BGL path matching
        if not found_ap_list:
            lpath = os.path.join(full_path, 'layout.json')
            if not os.path.exists(lpath):
                lpath = os.path.join(full_path, 'layout.json.disabled')
            if os.path.exists(lpath):
                try:
                    with open(lpath, 'r', encoding='utf-8', errors='ignore') as f:
                        ldata = json.load(f)
                        entries = ldata.get('content', [])
                        paths_str = ' '.join([c.get('path', '') for c in entries[:2000]])
                        bgl_icaos = set(re.findall(r'([a-zA-Z]{4})[-_.]?(?:airport|scenery)?\.bgl', paths_str, re.IGNORECASE))
                        bgl_icaos.update(re.findall(r'scenery[/\\](?:airports[/\\])?(?:world[/\\]scenery[/\\])?(?:airport-)?([A-Za-z]{4})[._\\]', paths_str, re.IGNORECASE))
                        for tok in bgl_icaos:
                            tok_u = tok.upper()
                            if tok_u in airports and tok.lower() not in EXCLUDE_WORDS:
                                found_ap_list.append((airports[tok_u], f"Layout BGL ({tok_u})"))
                except Exception:
                    pass

        # City / Name Fallback Matching
        if not found_ap_list:
            for t in tokens:
                t_clean = t.strip()
                if t_clean in VENDOR_MAP or len(t_clean) <= 3 or t_clean in EXCLUDE_WORDS or t_clean in ['fs20', 'fs24', 'airport', 'airports', 'pack', 'edition', 'vfr', 'hd', 'sd']:
                    continue
                if t_clean in city_index:
                    candidates = city_index[t_clean]
                    major = [c for c in candidates if c.get('type') in ['large_airport', 'medium_airport']]
                    chosen = major[0] if major else candidates[0]
                    found_ap_list.append((chosen, f"City Match ('{t_clean}' -> {chosen['ident']})"))
                    break
                elif t_clean in name_index:
                    candidates = name_index[t_clean]
                    major = [c for c in candidates if c.get('type') in ['large_airport', 'medium_airport']]
                    chosen = major[0] if major else candidates[0]
                    found_ap_list.append((chosen, f"Name Match ('{t_clean}' -> {chosen['ident']})"))
                    break

        seen_in_pkg = set()
        for found_ap, match_source in found_ap_list:
            icao = found_ap['ident']
            if icao in seen_in_pkg:
                continue
            seen_in_pkg.add(icao)

            vendor = get_clean_vendor(clean_folder, manifest_data)
            pricing_type, is_payware = determine_pricing(cat, clean_folder, vendor, manifest_data)
            is_asobo_official = (pricing_type == "Asobo / MS" or vendor == "Microsoft / Asobo")

            raw_type = found_ap.get('type', 'airport')
            if raw_type == 'large_airport':
                english_type = "International"
            elif raw_type == 'medium_airport':
                english_type = "Regional"
            elif raw_type in ['small_airport', 'closed']:
                english_type = "General Aviation"
            elif raw_type in ['heliport', 'seaplane_base']:
                english_type = "Heli / Water"
            else:
                english_type = "General Aviation"

            user_rating = ratings.get(icao, 0.0)

            # Price estimation
            price_eur, is_custom_price = get_estimated_price(
                icao, clean_folder, vendor, pricing_type, english_type, is_asobo_official, custom_prices
            )

            pkg_version = ""
            if manifest_data and isinstance(manifest_data, dict):
                raw_v = str(manifest_data.get('package_version', '')).strip()
                if raw_v:
                    pkg_version = f"v{raw_v}" if not raw_v.lower().startswith('v') else raw_v

            if 'streamed' in cat.lower():
                pkg_size_str = "Streamed"
            else:
                pkg_size_str = get_folder_size_formatted(full_path, folder_size_cache)

            new_source = {
                "folder_name": folder_name,
                "package_path": full_path,
                "source_folder": cat,
                "match_source": match_source,
                "vendor": vendor,
                "pricing_type": pricing_type,
                "is_payware": is_payware,
                "is_asobo_official": is_asobo_official,
                "is_disabled": is_disabled,
                "is_addon": is_addon_package,
                "is_fix_patch": False if (is_asobo_official or is_payware) else is_fix_patch,
                "version": pkg_version,
                "size_str": pkg_size_str,
                "world_update_name": get_world_update_name(icao, folder_name)
            }

            if icao not in detected_map:
                detected_map[icao] = {
                    "icao": icao,
                    "name": found_ap.get('name', 'Airport'),
                    "city": found_ap.get('city', ''),
                    "country": found_ap.get('country', ''),
                    "lat": found_ap.get('lat', 0.0),
                    "lon": found_ap.get('lon', 0.0),
                    "elevation": found_ap.get('elevation', 0),
                    "type": raw_type,
                    "english_type": english_type,
                    "iata": found_ap.get('iata', ''),
                    "package_name": folder_name,
                    "package_path": full_path,
                    "source_folder": cat,
                    "match_source": match_source,
                    "vendor": vendor,
                    "pricing_type": pricing_type,
                    "is_payware": is_payware,
                    "is_asobo_official": is_asobo_official,
                    "version": pkg_version,
                    "size_str": pkg_size_str,
                    "rating": user_rating,
                    "price_eur": price_eur,
                    "is_custom_price": is_custom_price,
                    "all_sources": [new_source],
                    "has_conflict": False,
                    "conflict_count": 1
                }
            else:
                existing = detected_map[icao]
                if not any(s['folder_name'] == folder_name for s in existing["all_sources"]):
                    existing["all_sources"].append(new_source)

                p_existing = get_source_priority(existing["source_folder"])
                p_new = get_source_priority(cat)

                if p_new > p_existing or (not existing["is_asobo_official"] and is_asobo_official):
                    existing["package_name"] = folder_name
                    existing["package_path"] = full_path
                    existing["source_folder"] = cat
                    existing["match_source"] = match_source
                    existing["vendor"] = vendor
                    existing["pricing_type"] = pricing_type
                    existing["is_payware"] = is_payware
                    existing["version"] = pkg_version
                    existing["size_str"] = pkg_size_str
                    if is_asobo_official:
                        existing["is_asobo_official"] = True

    # Dynamic discovery of future World Updates & City Updates from packages & Content.xml
    dynamic_asobo_set = set(ASOBO_STANDARD_ICAOS)
    msfs_edition = settings.get("msfs_edition", "Standard")
    if msfs_edition in ["Deluxe", "Premium Deluxe"]:
        dynamic_asobo_set.update(ASOBO_DELUXE_ICAOS)
    if msfs_edition == "Premium Deluxe":
        dynamic_asobo_set.update(ASOBO_PREMIUM_DELUXE_ICAOS)

    # Scan package names from Content.xml and physical/streamed folders for new official airports
    pkg_names_scanned = set()
    content_xml_path = r'C:\Users\Bertrand\AppData\Local\Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache\ThirdBuk\Content.xml'
    if os.path.exists(content_xml_path):
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(content_xml_path)
            root = tree.getroot()
            for p in root.findall('Package'):
                name = p.get('name', '').lower()
                pkg_names_scanned.add(name)
        except Exception: pass

    for _, f_item, _, _ in all_packages:
        pkg_names_scanned.add(f_item.lower())

    for p_name in pkg_names_scanned:
        if any(k in p_name for k in ['asobo-airport-', 'microsoft-airport-', 'worldupdate', 'cityupdate']):
            tokens = re.split(r'[-_ ]+', p_name)
            for t in tokens:
                t_u = t.upper()
                if len(t_u) == 4 and t_u in airports and t_u not in dynamic_asobo_set:
                    if t.lower() not in ['fs20', 'fs24', 'vfra', 'pack', 'aero', 'vfr', 'mesh', 'tree', 'data', 'area', 'zone', 'city']:
                        dynamic_asobo_set.add(t_u)

    for h_icao in dynamic_asobo_set:
        h_u = h_icao.upper()
        if h_u in airports:
            is_asobo_dis = any(h_icao.lower() in d for d in disabled_in_xml)
            asobo_src = {
                "folder_name": f"fs24-asobo-airport-{h_icao.lower()}",
                "package_path": "",
                "source_folder": "MSFS 2024 - StreamedPackages",
                "match_source": "Default Asobo Handcrafted",
                "vendor": "Microsoft / Asobo",
                "pricing_type": "Asobo",
                "is_payware": False,
                "is_asobo_official": True,
                "is_disabled": is_asobo_dis,
                "is_addon": False,
                "is_fix_patch": False,
                "version": "",
                "size_str": "Streamed",
                "world_update_name": get_world_update_name(h_u, f"fs24-asobo-airport-{h_icao.lower()}")
            }
            if h_u not in detected_map:
                ap_info = airports[h_u]
                raw_type = ap_info.get('type', 'airport')
                if raw_type == 'large_airport':
                    english_type = "International"
                elif raw_type == 'medium_airport':
                    english_type = "Regional"
                elif raw_type in ['small_airport', 'closed']:
                    english_type = "General Aviation"
                elif raw_type in ['heliport', 'seaplane_base']:
                    english_type = "Heli / Water"
                else:
                    english_type = "General Aviation"

                detected_map[h_u] = {
                    "icao": h_u,
                    "ident": h_u,
                    "name": ap_info.get('name', ''),
                    "city": ap_info.get('city', ''),
                    "country": ap_info.get('country', ''),
                    "lat": ap_info.get('lat', 0.0),
                    "lon": ap_info.get('lon', 0.0),
                    "type": raw_type,
                    "english_type": english_type,
                    "vendor": "Microsoft / Asobo",
                    "pricing_type": "Asobo",
                    "is_payware": False,
                    "is_asobo_official": True,
                    "is_custom_price": False,
                    "price_eur": 0.0,
                    "package_name": f"fs24-asobo-airport-{h_icao.lower()}",
                    "package_path": "",
                    "source_folder": "MSFS 2024 - StreamedPackages",
                    "version": "",
                    "size_str": "Streamed",
                    "match_source": "Default Asobo Handcrafted",
                    "all_sources": [asobo_src],
                    "is_disabled": False,
                    "has_conflict": False,
                    "conflict_count": 1,
                    "rating": ratings.get(h_u, 0.0)
                }
            else:
                existing = detected_map[h_u]
                if not any(s.get('is_asobo_official') or s.get('pricing_type') == 'Asobo' or 'asobo-airport-' in s.get('folder_name', '').lower() for s in existing["all_sources"]):
                    existing["all_sources"].append(asobo_src)

    # Process each detected airport and resolve primary package & classification
    for icao, item in detected_map.items():
        # Deduplicate sources that represent the exact same package between physical disk and StreamedPackages
        if len(item['all_sources']) > 1:
            unique_srcs = []
            seen_norms = set()
            sorted_srcs = sorted(
                item['all_sources'], 
                key=lambda s: 0 if 'streamed' not in s.get('source_folder', '').lower() else 1
            )
            for s in sorted_srcs:
                fn = s.get('folder_name', '')
                fn_norm = _normalize_pkg(fn)
                if fn_norm not in seen_norms:
                    seen_norms.add(fn_norm)
                    unique_srcs.append(s)
            item['all_sources'] = unique_srcs

        # 1. Determine if this airport has an Official Asobo/Microsoft base scenery in ANY source (including StreamedPackages)
        has_asobo = (icao in ['LFPB', 'LFPG']) or any(
            s.get('is_asobo_official') 
            or s.get('pricing_type') == 'Asobo' 
            or s.get('vendor') == 'Microsoft / Asobo'
            or s.get('folder_name', '').lower().startswith(('asobo-', 'microsoft-', 'fs20-asobo-', 'fs20-microsoft-', 'fs24-asobo-', 'fs24-microsoft-'))
            for s in item['all_sources']
        )
        
        # 2. Determine if this airport has an active Payware package
        active_payware = any(
            s.get('is_payware') and not s.get('is_disabled') and not s.get('is_fix_patch') and not s.get('is_addon')
            for s in item['all_sources']
        )



        if item['all_sources']:
            def get_package_score(s):
                score = 0 if s.get('is_disabled') else 100
                score += get_source_priority(s.get('source_folder', ''))
                
                if active_payware:
                    if s.get('is_payware') and not s.get('is_disabled'):
                        score += 500
                elif has_asobo:
                    if s.get('is_asobo_official') or s.get('pricing_type') == 'Asobo':
                        score += 500
                
                if s.get('is_fix_patch'):
                    score -= 1000
                elif s.get('is_addon'):
                    score -= 500
                else:
                    score += 20
                return score

            item['all_sources'].sort(key=get_package_score, reverse=True)
            primary = item['all_sources'][0]
            
            item['package_name'] = primary['folder_name']
            item['package_path'] = primary['package_path']
            item['source_folder'] = primary['source_folder']
            
            if active_payware:
                item['vendor'] = primary['vendor']
                item['pricing_type'] = "Payware"
                item['is_payware'] = True
                item['is_asobo_official'] = False
            elif has_asobo:
                item['vendor'] = "Microsoft / Asobo"
                item['pricing_type'] = "Asobo"
                item['is_payware'] = False
                item['is_asobo_official'] = True
            else:
                item['vendor'] = primary['vendor']
                item['pricing_type'] = primary['pricing_type']
                item['is_payware'] = primary['is_payware']
                item['is_asobo_official'] = False

            item['match_source'] = primary['match_source']
            item['version'] = primary.get('version', '')
            item['size_str'] = primary.get('size_str', '')
            item['world_update_name'] = primary.get('world_update_name') or get_world_update_name(icao, primary['folder_name'])

        # Active sources calculation
        active_sources = [s for s in item['all_sources'] if not s.get('is_disabled')]

        # If all installed custom/Asobo packages are disabled, fallback to Default MSFS
        if len(active_sources) == 0:
            item['pricing_type'] = 'Default'
            item['vendor'] = 'Microsoft Flight Simulator (Default)'
            item['is_addon'] = False
            item['is_disabled'] = False
        else:
            item['is_disabled'] = False

        # Detect TRUE Scenery Conflicts (multiple active PRIMARY main scenery packages)
        active_primary_installs = [s for s in item['all_sources'] if not s.get('is_disabled') and not s.get('is_addon') and not s.get('is_fix_patch')]

        if len(active_primary_installs) > 1:
            item['has_conflict'] = True
            item['conflict_count'] = len(active_primary_installs)
        else:
            item['has_conflict'] = False
            item['conflict_count'] = len(active_sources)

    # Process bundle package pricing allocation
    bundle_counts = {}
    for icao, item in detected_map.items():
        pkg_name = (item.get('package_name') or '').lower()
        for b_key in BUNDLE_PACKAGE_PRICES:
            if b_key in pkg_name:
                bundle_counts[b_key] = bundle_counts.get(b_key, 0) + 1
                item['is_bundle'] = True
                item['bundle_id'] = b_key
                item['bundle_name'] = BUNDLE_PACKAGE_PRICES[b_key]['name']
                item['bundle_total_price'] = BUNDLE_PACKAGE_PRICES[b_key]['price']
                break

    for icao, item in detected_map.items():
        if item.get('is_bundle'):
            b_key = item.get('bundle_id')
            b_count = bundle_counts.get(b_key, 1)
            b_total = item.get('bundle_total_price', 39.00)
            item['bundle_airport_count'] = b_count
            if not item.get('is_custom_price'):
                item['price_eur'] = round(b_total / max(1, b_count), 2)

    # Load Operating Airlines Database & Routes Database
    AIRLINES_DB = {}
    AIRLINES_DB_PATH = get_resource_file_path("airport_airlines.json")
    if os.path.exists(AIRLINES_DB_PATH):
        try:
            with open(AIRLINES_DB_PATH, 'r', encoding='utf-8') as f:
                AIRLINES_DB = json.load(f)
        except Exception as e:
            print("Error loading airport_airlines.json:", e)

    ROUTES_DB = {}
    ROUTES_DB_PATH = get_resource_file_path("airport_routes.json")
    if os.path.exists(ROUTES_DB_PATH):
        try:
            with open(ROUTES_DB_PATH, 'r', encoding='utf-8') as f:
                ROUTES_DB = json.load(f)
        except Exception as e:
            print("Error loading airport_routes.json:", e)

    # Scan GSX Profiles
    gsx_path_cfg = settings.get("gsx_profile_path", get_default_gsx_path())
    gsx_map = scan_gsx_profiles(gsx_path_cfg)

    # Include all 4-letter ICAO default procedural MSFS airports from airports.json that are not already in detected_map
    for d_icao, ap_info in airports.items():
        if len(d_icao) == 4 and d_icao.isalpha() and d_icao not in detected_map:
            raw_type = ap_info.get('type', 'airport')
            if raw_type not in ['large_airport', 'medium_airport', 'small_airport']:
                continue

            if raw_type == 'large_airport':
                english_type = "International"
            elif raw_type == 'medium_airport':
                english_type = "Regional"
            else:
                english_type = "General Aviation"

            detected_map[d_icao] = {
                "icao": d_icao,
                "ident": d_icao,
                "name": ap_info.get('name', ''),
                "city": ap_info.get('city', ''),
                "country": ap_info.get('country', ''),
                "lat": ap_info.get('lat', 0.0),
                "lon": ap_info.get('lon', 0.0),
                "type": raw_type,
                "english_type": english_type,
                "vendor": "Microsoft Flight Simulator (Default)",
                "pricing_type": "Default",
                "is_payware": False,
                "is_asobo_official": False,
                "is_default": True,
                "is_custom_price": False,
                "price_eur": 0.0,
                "package_name": f"msfs-default-{d_icao.lower()}",
                "package_path": "",
                "source_folder": "MSFS - Default Procedural",
                "version": "",
                "size_str": "Default",
                "match_source": "Default MSFS Procedural",
                "all_sources": [{
                    "folder_name": f"msfs-default-{d_icao.lower()}",
                    "package_path": "",
                    "source_folder": "MSFS - Default Procedural",
                    "match_source": "Default MSFS Procedural",
                    "vendor": "Microsoft Flight Simulator (Default)",
                    "pricing_type": "Default",
                    "is_payware": False,
                    "is_asobo_official": False,
                    "is_default": True,
                    "is_disabled": False,
                    "is_addon": False,
                    "is_fix_patch": False,
                    "version": "",
                    "size_str": "Default"
                }],
                "is_disabled": False,
                "has_conflict": False,
                "conflict_count": 1,
                "rating": ratings.get(d_icao, 0.0)
            }

    for icao, item in detected_map.items():
        item['operating_airlines'] = AIRLINES_DB.get(icao, [])
        item['routes'] = ROUTES_DB.get(icao, {})
        if icao in gsx_map:
            item['has_gsx_profile'] = True
            item['gsx_profile_filename'] = gsx_map[icao]['filename']
            item['gsx_profile_path'] = gsx_map[icao]['path']
        else:
            item['has_gsx_profile'] = False
            item['gsx_profile_filename'] = ''
            item['gsx_profile_path'] = ''

    detected_airports = list(detected_map.values())

    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(detected_airports, f, indent=2, ensure_ascii=False)

    save_folder_size_cache(folder_size_cache)
    print(f"Scan complete: {len(detected_airports)} unique airports saved.")
    return detected_airports

if __name__ == "__main__":
    run_scan()
