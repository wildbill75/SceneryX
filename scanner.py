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
SNAPSHOT_JSON_PATH = os.path.join(USER_DATA_DIR, "library_snapshot.json")

_CACHED_CONTENT_XML_PATH = None

def get_content_xml_path():
    global _CACHED_CONTENT_XML_PATH
    if _CACHED_CONTENT_XML_PATH and os.path.exists(_CACHED_CONTENT_XML_PATH):
        return _CACHED_CONTENT_XML_PATH

    local_appdata = os.getenv('LOCALAPPDATA', '')
    appdata = os.getenv('APPDATA', '')
    limitless_cache = os.path.join(local_appdata, r'Packages\Microsoft.Limitless_8wekyb3d8bbwe\LocalCache')
    candidates = [
        os.path.join(limitless_cache, 'Content.xml'),
        os.path.join(local_appdata, r'Packages\Microsoft.FlightSimulator_8wekyb3d8bbwe\LocalCache\Content.xml'),
        os.path.join(appdata, r'Microsoft Flight Simulator 2024\Content.xml'),
        os.path.join(appdata, r'Microsoft Flight Simulator\Content.xml'),
    ]
    for c in candidates:
        if os.path.exists(c):
            _CACHED_CONTENT_XML_PATH = c
            return c
    _CACHED_CONTENT_XML_PATH = candidates[0]
    return _CACHED_CONTENT_XML_PATH

# Auto-migrate any existing legacy config files from local executable folder to %APPDATA%/SceneryX/
for filename, target_path in [
    ("settings.json", SETTINGS_JSON_PATH),
    ("ratings.json", RATINGS_JSON_PATH),
    ("custom_prices.json", CUSTOM_PRICES_JSON_PATH),
    ("library_snapshot.json", SNAPSHOT_JSON_PATH),
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
    'simdesigngroup', 'sim design group', 'sdg', 'simdesigngroup-airport',
    'dominicdesignteam', 'dominic design team', 'dominic design', 'ddt',
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
    'scenerytr', 'scenerytrdesign', 'scenerytr design', 'scenery tr', 'agsim', 'ag-sim', 'st-designs',
    'pyszny', 'pyszny design', 'geardown', 'geardown simulations', 'vabb', 'vabb design',
    'rodriguez', 'rodriguez scenery', 'aliens', 'aliens simulations', 'aerobask', 'flyer',
    'bksim', 'shd', 'nemo', 'pilotg', 'rara-avis', 'aerodesigns', 'darkscenery', 'dark scenery'
}

VENDOR_MAP = {
    'simdesigngroup': 'Sim Design Group',
    'sim design group': 'Sim Design Group',
    'sdg': 'Sim Design Group',
    'dominicdesignteam': 'Dominic Design Team',
    'dominic design team': 'Dominic Design Team',
    'argaeus': 'Argaeus',
    'argaeus simulations': 'Argaeus',
    'argaeus studio': 'Argaeus',
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
    'lhsimulation': 'LHSimulations',
    'lhsim': 'LHSimulations',
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
    'farm', 'hang', 'silo', 'gate', 'bush', 'shed', 'rail', 'fuel', 'fire', 'flag', 'tile', 'male', 'barb',
    'panama', 'france', 'germany', 'spain', 'italy', 'england', 'poland', 'japan', 'china',
    'canada', 'mexico', 'brazil', 'australia', 'alaska', 'hawaii', 'california', 'texas', 'florida'
}

NON_AIRPORT_KEYWORDS = [
    'landingchallenge', 'landing-challenge', 'point-of-interest', 'pointofinterest',
    'discovery', 'passiveaircraft', 'passive-aircraft', 'challenges', 'activities', 'activity',
    'certification', 'procedural', 'trainings', 'training', 'travelbook', 'simobjects', 'ships',
    'modellib', 'library1v14', 'library2v14', 'commonlibrary', 'object-library', 'asset-library',
    'assetpack', 'asset-pack', 'sdr-pack', 'windy-things', 'palm_trees_library', 'vegetation-library',
    'totof-aircraft-library', 'dave-3d-people', 'seismic-library', 'vertical-obstructions', 'verticalobstructions', 'crowds', 'gliders',
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
    'asobo-live', 'asobo-nav', 'asobo-generic', 'instruments', 'instrument', 'avionics', 'workingtitle',
    'g1000', 'g3000', 'g5000', 'wt21', 'proline'
]

ADDON_LIBRARY_KEYWORDS = [
    'models', 'model', 'library', 'libraries', 'interior', 'extension', 'mesh', 'aerial',
    'ortho', 'vdgs', 'lights', 'trees', 'vegetation', 'gsx', 'enhancement', 'optional'
]

FIX_PATCH_KEYWORDS = [
    'fix', 'patch', 'flatten', 'fixer', 'correction', 'enhancement', 'mod',
    'update-fix', 'gsx-fix', 'vdgs-fix', 'ils-fix', 'nav-fix', 'lighting-fix',
    'taxiway-fix', 'runway-fix', 'flatten-fix', 'zparking', 'parking', 'vdgs',
    'stalex', 'stg', 'overlay', 'exclusion', 'excl', 'profile', 'xavios',
    'jetway', 'jetways', 'gate', 'gates', 'frequency', 'frequencies', 'marking', 'markings',
    'interior', 'optional', 'extension', 'mesh', 'aerial', 'ortho', 'lights', 'lighting',
    'trees', 'vegetation', 'texture', 'textures', 'liveries', 'livery',
    'static', 'statics', 'cars', 'people'
]

# Explicit exceptions for packages whose names contain "fix" but are genuine full sceneries
MAIN_SCENERY_EXCEPTIONS = {
    'wombiiactual-airport-enbr-fleslandfix'
}

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
    'francevfr-airport-pidf-parisvfrairports': {'price': 29.90, 'name': 'France VFR - Paris VFR Airports Pack'},
    'fs20-francevfr-airport-pidf-parisvfrairports': {'price': 29.90, 'name': 'France VFR - Paris VFR Airports Pack'},
    'francevfr-airport-apt1-airportfrance-pack1': {'price': 29.90, 'name': 'France VFR - Airport France Pack 1'},
    'fs20-francevfr-airport-apt1-airportfrance-pack1': {'price': 29.90, 'name': 'France VFR - Airport France Pack 1'},
    'francevfr-800-sevfrairports': {'price': 24.90, 'name': 'France VFR - Sud-Est VFR Airports Pack'},
    'francevfr-800-marseille': {'price': 14.99, 'name': 'France VFR - Marseille Airport'},
}

# Known Real Retail Prices Catalog in EUR (€)
KNOWN_PAYWARE_PRICES = {
    # Free official releases from vendors (0.00€)
    'aerosoft-paderborn': 0.0,
    'fs20-aerosoft-paderborn': 0.0,
    'inibuilds-airport-at98-wolfsfang': 0.0,
    'inibuilds-airport-kmke-milwaukee': 0.0,
    'at98-wolfsfang': 0.0,
    'kmke-milwaukee': 0.0,
    'inibuilds-at98': 0.0,
    'inibuilds-kmke': 0.0,
    'wolfsfang': 0.0,

    # Specific Package Folder Patterns
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
        if icao in prices and isinstance(prices[icao], dict):
            prices[icao]['price'] = float(price_val)
        else:
            prices[icao] = {"price": float(price_val)}
    else:
        if icao in prices:
            if isinstance(prices[icao], dict):
                prices[icao].pop('price', None)
                if not prices[icao]:
                    prices.pop(icao, None)
            else:
                prices.pop(icao, None)
    with open(CUSTOM_PRICES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(prices, f, indent=2, ensure_ascii=False)
    return prices

def save_custom_category(icao, category):
    prices = load_custom_prices()
    if category in ["Payware", "Freeware", "Freeware / Flightsim.to"]:
        if icao not in prices:
            prices[icao] = {}
        elif not isinstance(prices[icao], dict):
            prices[icao] = {"price": float(prices[icao])}
        prices[icao]["category"] = category
    else:
        if icao in prices:
            if isinstance(prices[icao], dict):
                prices[icao].pop("category", None)
                if not prices[icao]:
                    prices.pop(icao, None)
            else:
                prices.pop(icao, None)
    with open(CUSTOM_PRICES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(prices, f, indent=2, ensure_ascii=False)
    return prices

def get_estimated_price(icao, folder_name, vendor, pricing_type, english_type, is_asobo, custom_prices):
    if icao in custom_prices:
        val = custom_prices[icao]
        if isinstance(val, dict):
            if 'price' in val:
                return float(val['price']), True
        elif isinstance(val, (int, float, str)):
            try:
                return float(val), True
            except Exception:
                pass

    if is_asobo or pricing_type in ["Asobo", "Asobo / MS", "Freeware", "Freeware / Flightsim.to"] or "freeware" in str(pricing_type).lower():
        return 0.0, False

    fn_lower = folder_name.lower()
    v_lower = str(vendor).lower()

    # Free official promotional releases from payware vendors (remain in Payware category with 0.00€)
    if icao in ['KMKE', 'AT98'] and ('inibuilds' in fn_lower or 'inibuilds' in v_lower or 'wolf' in fn_lower):
        return 0.0, False

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

def extract_icao_from_gsx_filename(filename, valid_icaos=None, file_path=None):
    if not filename:
        return None
    clean_f = filename.lower()
    if clean_f.endswith('.disabled'):
        clean_f = clean_f[:-9]
    if not clean_f.endswith('.ini') and not clean_f.endswith('.py'):
        return None
    name_no_ext = os.path.splitext(clean_f)[0]

    # Exclude non-airport system ini files
    if name_no_ext in ['configuration', 'flywithlua', 'fwl_prefs', 'saveinitialassignments', 'user']:
        return None

    # Priority 1: Exact 4-letter ICAO prefix (e.g. EGLL.ini, LFPG-addon.ini, KJFK_gsx.ini)
    m = re.match(r'^([a-zA-Z]{4})(?:[_\-.\s0-9]|$)', clean_f)
    if m:
        candidate = m.group(1).upper()
        if valid_icaos is None or candidate in valid_icaos:
            return candidate

    # Priority 2: Look for valid 4-letter ICAO token anywhere in the filename
    # e.g. ScotFlight_EGPE_GSX_Profile_v1.0.ini -> 'EGPE', GSX-eghi-inibuilds.ini -> 'EGHI'
    tokens = re.split(r'[-_.\s]+', clean_f)
    ignore_tokens = {
        'gsx', 'msfs', 'pro', 'vfr', 'pack', 'free', 'base', 'user', 'data',
        'mesh', 'true', 'full', 'lite', 'afcad', 'safe', 'vdgs', 'dock',
        'scot', 'flight', 'scenery', 'profile', 'addon', 'prep', 'test',
        'ini', 'disabled'
    }
    for t in tokens:
        if len(t) == 4 and t.isalpha() and t not in ignore_tokens:
            cand = t.upper()
            if valid_icaos is None or cand in valid_icaos:
                return cand

    # Priority 3: Inspect file content if path available
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read(4096)
                afcad_m = re.search(r'afcad_path\s*=\s*(.+)', content)
                if afcad_m:
                    afcad_line = afcad_m.group(1).lower()
                    for t in re.split(r'[/\\_\-.\s]+', afcad_line):
                        if len(t) == 4 and t.isalpha() and t not in ignore_tokens:
                            cand = t.upper()
                            if valid_icaos is None or cand in valid_icaos:
                                return cand
        except Exception:
            pass

    return None

def scan_gsx_profiles(gsx_dir):
    if not gsx_dir or not os.path.exists(gsx_dir):
        return {}
    
    gsx_map = {}
    valid_db = None
    try:
        db_res = load_airport_database()
        if isinstance(db_res, tuple) and len(db_res) > 0 and isinstance(db_res[0], dict):
            valid_db = db_res[0]
        elif isinstance(db_res, dict):
            valid_db = db_res
    except Exception:
        pass

    try:
        ini_files = [f for f in os.listdir(gsx_dir) if f.endswith('.ini') and f.lower() != 'configuration.ini']
        for f in ini_files:
            fp = os.path.join(gsx_dir, f)
            icao = extract_icao_from_gsx_filename(f, valid_icaos=valid_db, file_path=fp)
            if icao:
                gsx_map[icao] = {
                    'filename': f,
                    'path': fp
                }
    except Exception:
        pass
    return gsx_map

KNOWN_STUDIO_ALIASES = {
    'francevfr': ['francevfr', 'fvfr', 'france vfr'],
    'fsdreamteam': ['fsdreamteam', 'fsdt', 'virtuali'],
    'latinvfr': ['latinvfr', 'lvfr', 'latin vfr'],
    'flytampa': ['flytampa', 'fly tampa'],
    'mkstudios': ['mkstudios', 'mk studios', 'mk-studios', 'mk'],
    'drzewiecki': ['drzewiecki', 'drzewiecki design', 'dd'],
    'pyreegue': ['pyreegue', 'pyreegue dev co', 'pyreegue dev co.'],
    'flightbeam': ['flightbeam', 'flightbeam studios'],
    'nza': ['nza', 'nza simulations', 'nzasimulations'],
    'justsim': ['justsim', 'just sim'],
    'digitaldesign': ['digitaldesign', 'digital design'],
    'simwings': ['simwings', 'sim-wings', 'sim wings', 'aerosoft'],
    'uk2000': ['uk2000', 'uk2000 scenery', 'uk2000scenery'],
    'redwing': ['redwing', 'redwings', 'redwing simulations'],
    'amsim': ['amsim', 'am sim'],
    'bmworld': ['bmworld', 'bm world'],
    'fly2high': ['fly2high', 'fly 2 high'],
    'scenerytr': ['scenerytr', 'scenerytr design', 'scenery tr'],
    'gaya': ['gaya', 'gaya simulations', 'gaya-simulations'],
    'pilotplus': ['pilotplus', 'pilot plus'],
    'verticalsim': ['verticalsim', 'vertical sim'],
    'tailstrike': ['tailstrike', 'tailstrike designs'],
    'orbx': ['orbx', 'orbxdirect'],
    'inibuilds': ['inibuilds', 'iniscene', 'ini scene'],
    'aerosoft': ['aerosoft'],
    'fsx3d': ['fsx3d', 'fsx 3d'],
    'lisium': ['lisium'],
    'deimos': ['deimos', 'deimos inc'],
    'lhsimulations': ['lhsimulations', 'lh simulations', 'lhsim'],
    'macco': ['macco', 'macco simulations'],
    'jopp': ['jopp'],
    'lazerbeam': ['lazerbeam'],
    'slhsimdesigns': ['slhsimdesigns', 'slh'],
    'atelic': ['atelic'],
    'justflight': ['justflight', 'just flight', 'jf'],
    'euroscene': ['euroscene', 'euro scene'],
    'burningblue': ['burningblue', 'burningbluedesign', 'burning blue'],
    'feelthere': ['feelthere', 'feel there'],
    'flightsimdevelopment': ['flightsimdevelopment', 'fsdg'],
    'samscene': ['samscene', 'samscene3d', 'sam scene'],
}

STUDIO_DISPLAY_NAMES = {
    'francevfr': 'France VFR',
    'fsdreamteam': 'FSDreamTeam',
    'latinvfr': 'LatinVFR',
    'flytampa': 'FlyTampa',
    'mkstudios': 'MK-Studios',
    'drzewiecki': 'Drzewiecki Design',
    'pyreegue': 'Pyreegue Dev Co.',
    'flightbeam': 'Flightbeam Studios',
    'nza': 'NZA Simulations',
    'justsim': 'JustSim',
    'digitaldesign': 'Digital Design',
    'simwings': 'Sim-Wings',
    'uk2000': 'UK2000 Scenery',
    'redwing': 'Redwing Simulations',
    'amsim': 'AMSim',
    'bmworld': 'BMWorld',
    'fly2high': 'Fly2High',
    'scenerytr': 'SceneryTR Design',
    'gaya': 'Gaya Simulations',
    'pilotplus': 'Pilot Plus',
    'verticalsim': 'Verticalsim',
    'tailstrike': 'Tailstrike Designs',
    'orbx': 'Orbx',
    'inibuilds': 'iniBuilds',
    'aerosoft': 'Aerosoft',
    'fsx3d': 'FSX3D',
    'lisium': 'Lisium',
    'deimos': 'DeimoS Inc',
    'lhsimulations': 'LHSimulations',
    'macco': 'Macco Simulations',
    'jopp': 'JOPP',
    'lazerbeam': 'Lazerbeam',
    'slhsimdesigns': 'SLH Sim Designs',
    'atelic': 'Atelic',
    'justflight': 'Just Flight',
    'euroscene': 'EuroScene',
    'burningblue': 'Burning Blue Design',
    'feelthere': 'FeelThere',
    'flightsimdevelopment': 'FSDG',
    'samscene': 'SamScene3D',
}

def _normalize_pkg(pkg_name):
    if not pkg_name:
        return ''
    cleaned = pkg_name.lower().replace('-', '').replace('_', '').replace(' ', '')
    cleaned = re.sub(r'^(community|official|streamedpackages|fs20|fs24|msfs2020|msfs2024|msfs)', '', cleaned)
    cleaned = re.sub(r'(airport|scenery|scene)$', '', cleaned)
    return cleaned

def normalize_studio_name(name):
    if not name:
        return ''
    cleaned = re.sub(r'[^a-z0-9]', '', name.lower())
    for suffix in ['simulations', 'simulation', 'studios', 'studio', 'designs', 'design', 'scenery', 'sceneries', 'airports', 'airport', 'team', 'devco', 'dev']:
        if cleaned.endswith(suffix) and len(cleaned) > len(suffix) + 2:
            cleaned = cleaned[:-len(suffix)]
            break
    if cleaned.endswith('s') and len(cleaned) > 4:
        cleaned = cleaned[:-1]
    return cleaned

def detect_studio_from_text(text):
    if not text:
        return None
    cleaned = re.sub(r'[^a-z0-9]', '', text.lower())
    t_lower = text.lower()
    for studio_key, aliases in KNOWN_STUDIO_ALIASES.items():
        for alias in aliases:
            clean_alias = re.sub(r'[^a-z0-9]', '', alias)
            if len(clean_alias) >= 3 and (clean_alias in cleaned or alias in t_lower):
                return studio_key
    return None

def evaluate_gsx_studio_match(pf, ap):
    """
    Evaluates whether a GSX profile matches the installed airport scenery.
    Returns (status, reason)
    status is one of: 'MATCHED', 'MISMATCH_STUDIO', 'MISMATCH_DEFAULT', 'ORPHAN'
    """
    if not ap:
        return ('ORPHAN', 'Airport not found in your MSFS library.')

    target_pkg = pf.get('target_pkg')
    filename = pf.get('filename')
    scenario = pf.get('scenario')
    creator = pf.get('creator')
    afcad = pf.get('afcad_path')

    pricing_type = ap.get('pricing_type', 'Default')
    is_asobo = bool(ap.get('is_asobo') or (ap.get('vendor') or '').lower() in ('asobo', 'microsoft / asobo', 'microsoft') or any(s.get('is_asobo_official') for s in ap.get('all_sources', [])))
    asobo_desc = ap.get('package_name') or 'Asobo Handcrafted Scenery'

    active_src = next((s for s in ap.get('all_sources', []) if not s.get('is_disabled') and not s.get('is_fix_patch') and not s.get('is_addon')), None)
    active_folder = (active_src.get('folder_name') or '').lower() if active_src else ''
    active_vendor = (active_src.get('vendor') or ap.get('vendor') or '').strip() if active_src else (ap.get('vendor') or '').strip()
    active_pkg_name = (active_src.get('package_name') or ap.get('package_name') or '').strip() if active_src else (ap.get('package_name') or '').strip()

    is_default_target = (target_pkg and 'default' in target_pkg.lower()) or (filename and ('default' in filename.lower() or 'stock' in filename.lower()))
    if is_default_target:
        if pricing_type != 'Default' and not is_asobo:
            active_desc = active_vendor if (active_vendor and active_vendor != 'Unknown') else (active_pkg_name or active_folder or 'Custom Scenery')
            return ('MISMATCH_DEFAULT', f'Profile designed for Default MSFS, but active scenery is "{active_desc}".')
        return ('MATCHED', 'Profile designed for Default MSFS airport.')

    # Direct folder/package exact match with active scenery
    if target_pkg and active_folder:
        clean_target = re.sub(r'[^a-z0-9]', '', target_pkg.lower())
        clean_active = re.sub(r'[^a-z0-9]', '', active_folder.lower())
        if clean_target == clean_active or clean_target in clean_active or clean_active in clean_target or _normalize_pkg(target_pkg) == _normalize_pkg(active_folder):
            disp_name = active_vendor if (active_vendor and active_vendor != 'Unknown') else target_pkg
            return ('MATCHED', f'Profile perfectly aligned with active scenery ({disp_name}).')

    # Studio identification
    prof_studio = (
        detect_studio_from_text(target_pkg) or
        detect_studio_from_text(filename) or
        detect_studio_from_text(scenario) or
        detect_studio_from_text(creator) or
        detect_studio_from_text(afcad)
    )

    act_studio = (
        detect_studio_from_text(active_vendor) or
        detect_studio_from_text(active_folder) or
        detect_studio_from_text(active_pkg_name)
    )

    norm_vendor = normalize_studio_name(active_vendor)
    norm_target = normalize_studio_name(target_pkg)
    norm_fn = normalize_studio_name(filename)

    # 1. If detected studio keys match exactly
    if prof_studio and act_studio and prof_studio == act_studio:
        studio_display = active_vendor if (active_vendor and active_vendor != 'Unknown') else STUDIO_DISPLAY_NAMES.get(prof_studio, prof_studio.title())
        return ('MATCHED', f'Profile perfectly aligned with active scenery ({studio_display}).')

    # 1b. Gaya / Asobo partner relationship for Asobo official handcrafted sceneries
    if is_asobo:
        fn_lower = (filename or '').lower()
        scen_lower = (scenario or '').lower()
        if prof_studio == 'gaya':
            return ('MATCHED', f'Profile aligned with Asobo handcrafted scenery by Gaya Simulations ({asobo_desc}).')
        if any(k in fn_lower or k in scen_lower for k in ['asobo', 'microsoft', 'worldupdate', 'world-update', 'world_update', 'wu1', 'wu2', 'wu3', 'wu4', 'wu5', 'wu6', 'wu7', 'wu8', 'wu9']):
            return ('MATCHED', f'Profile aligned with active scenery ({asobo_desc}).')

    # 2. If normalized vendor appears in target_pkg, filename, scenario or afcad
    if norm_vendor and len(norm_vendor) >= 3:
        if (norm_vendor in norm_target or 
            norm_vendor in norm_fn or 
            (scenario and norm_vendor in normalize_studio_name(scenario)) or
            (creator and norm_vendor in normalize_studio_name(creator)) or
            (afcad and norm_vendor in normalize_studio_name(afcad))):
            return ('MATCHED', f'Profile perfectly aligned with active scenery ({active_vendor}).')

    # 3. If studio in profile is explicitly known AND active scenery has a different known studio or is default
    if prof_studio:
        prof_display = STUDIO_DISPLAY_NAMES.get(prof_studio, target_pkg or prof_studio.title())
        if pricing_type == 'Default' and not is_asobo:
            return ('MISMATCH_DEFAULT', f'Profile designed for "{prof_display}", but active scenery is "Microsoft Flight Simulator (Default)".')
        elif is_asobo:
            return ('MISMATCH_STUDIO', f'Profile designed for "{prof_display}", but active scenery is "{asobo_desc}".')
        elif act_studio and prof_studio != act_studio:
            active_desc = active_vendor if (active_vendor and active_vendor != 'Unknown') else (active_pkg_name or active_folder)
            return ('MISMATCH_STUDIO', f'Profile designed for "{prof_display}", but active scenery is "{active_desc}".')
        elif not act_studio and (active_vendor or active_folder):
            active_desc = active_vendor if (active_vendor and active_vendor != 'Unknown') else active_folder
            return ('MISMATCH_STUDIO', f'Profile designed for "{prof_display}", but active scenery is "{active_desc}".')

    # 4. If target_pkg is given, check for mismatch against active scenery
    if target_pkg:
        prof_disp = STUDIO_DISPLAY_NAMES.get(detect_studio_from_text(target_pkg), target_pkg)
        if pricing_type == 'Default' and not is_asobo:
            return ('MISMATCH_DEFAULT', f'Profile designed for "{prof_disp}", but active scenery is "Microsoft Flight Simulator (Default)".')
        elif is_asobo:
            return ('MISMATCH_STUDIO', f'Profile designed for "{prof_disp}", but active scenery is "{asobo_desc}".')
        else:
            active_desc = active_vendor if (active_vendor and active_vendor != 'Unknown') else (active_pkg_name or active_folder)
            return ('MISMATCH_STUDIO', f'Profile designed for "{prof_disp}", but active scenery is "{active_desc}".')

    # 5. Scenario check: ONLY a mismatch if scenario names a KNOWN OTHER STUDIO that contradicts active scenery
    if scenario:
        scen_studio = detect_studio_from_text(scenario)
        if scen_studio:
            if pricing_type == 'Default' and not is_asobo:
                return ('MISMATCH_DEFAULT', f'Profile mentions "{scenario}", but active scenery is "Microsoft Flight Simulator (Default)".')
            elif is_asobo:
                if scen_studio == 'gaya':
                    return ('MATCHED', f'Profile aligned with Asobo handcrafted scenery by Gaya Simulations ({asobo_desc}).')
                return ('MISMATCH_STUDIO', f'Profile mentions "{scenario}", but active scenery is "{asobo_desc}".')
            elif act_studio and scen_studio != act_studio:
                return ('MISMATCH_STUDIO', f'Profile mentions "{scenario}", but active scenery is "{active_vendor or active_folder}".')

    # 6. Default or generic profile matching
    if pricing_type == 'Default' and not is_asobo:
        return ('MATCHED', 'Profile aligned with Default MSFS airport.')

    return ('MATCHED', 'Active GSX profile.')


def audit_all_gsx_profiles(gsx_dir=None, installed_airports=None):
    if not gsx_dir:
        gsx_dir = get_default_gsx_path()
    if not gsx_dir or not os.path.exists(gsx_dir):
        return {'summary': {'total_files': 0, 'total_icaos': 0, 'matched': 0, 'duplicate': 0, 'mismatch': 0, 'orphan': 0, 'invalid': 0}, 'by_icao': {}, 'non_icao_files': []}

    installed_map = {}
    if installed_airports is not None:
        if isinstance(installed_airports, dict):
            installed_map = installed_airports
        elif isinstance(installed_airports, list):
            installed_map = {ap['icao']: ap for ap in installed_airports if isinstance(ap, dict) and 'icao' in ap}
    elif os.path.exists(OUTPUT_JSON_PATH):
        try:
            with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                installed_list = json.load(f)
                installed_map = {ap['icao']: ap for ap in installed_list if isinstance(ap, dict) and 'icao' in ap}
        except Exception:
            pass

    try:
        all_dir_files = os.listdir(gsx_dir)
    except Exception:
        all_dir_files = []

    active_ini_files = [f for f in all_dir_files if f.endswith('.ini') and f.lower() != 'configuration.ini']
    disabled_ini_files = [f for f in all_dir_files if f.lower().endswith('.disabled') and not f.lower().startswith('configuration')]

    airports_db = {}
    try:
        db_res = load_airport_database()
        if isinstance(db_res, tuple) and len(db_res) > 0 and isinstance(db_res[0], dict):
            airports_db = db_res[0]
        elif isinstance(db_res, dict):
            airports_db = db_res
    except Exception:
        pass

    all_valid_icaos = set(airports_db.keys()) if airports_db else set()
    all_valid_icaos.update(installed_map.keys())

    by_icao = {}
    non_icao_files = []

    for f in active_ini_files:
        fp = os.path.join(gsx_dir, f)
        icao = extract_icao_from_gsx_filename(f, valid_icaos=all_valid_icaos, file_path=fp)
        if not icao:
            non_icao_files.append(f)
            continue
        by_icao.setdefault(icao, []).append({'filename': f, 'is_disabled': False})

    for f in disabled_ini_files:
        fp = os.path.join(gsx_dir, f)
        icao = extract_icao_from_gsx_filename(f, valid_icaos=all_valid_icaos, file_path=fp)
        if icao:
            by_icao.setdefault(icao, []).append({'filename': f, 'is_disabled': True})
        else:
            non_icao_files.append(f)

    results = {}
    summary = {
        'total_files': len(active_ini_files),
        'total_icaos': len(by_icao),
        'matched': 0,
        'duplicate': 0,
        'mismatch': 0,
        'orphan': 0,
        'disabled': len(disabled_ini_files),
        'invalid': len(non_icao_files)
    }

    import datetime

    for icao, file_entries in by_icao.items():
        ap = installed_map.get(icao)
        active_src = next((s for s in ap.get('all_sources', []) if not s.get('is_disabled') and not s.get('is_fix_patch') and not s.get('is_addon')), None) if ap else None
        parsed_files = []
        active_entries = [e for e in file_entries if not e['is_disabled']]

        for entry in file_entries:
            f = entry['filename']
            fp = os.path.join(gsx_dir, f)
            afcad = None
            scenario = None
            creator = None
            gates_count = 0
            target_pkg = None
            mtime_str = None
            mtime_ts = 0
            ver_str = None

            try:
                mtime_ts = os.path.getmtime(fp)
                mtime_str = datetime.datetime.fromtimestamp(mtime_ts).strftime('%Y-%m-%d')
            except Exception:
                pass

            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as file_h:
                    content = file_h.read()
                afcad_m = re.search(r'afcad_path\s*=\s*(.+)', content)
                if afcad_m:
                    afcad = afcad_m.group(1).strip()
                scenario_m = re.search(r'scenario\s*=\s*(.+)', content)
                if scenario_m:
                    scenario = scenario_m.group(1).strip()
                creator_m = re.search(r'creator\s*=\s*(.+)', content)
                if creator_m:
                    creator = creator_m.group(1).strip()
                gates_count = len(re.findall(r'\[(?:gate|rwy|parking)\s+[^\]]+\]', content, re.IGNORECASE))
                v_m = re.search(r'version\s*=\s*["\']?([^"\'\r\n]+)["\']?', content)
                if v_m:
                    ver_str = v_m.group(1).strip()
            except Exception:
                pass

            if afcad:
                parts = afcad.replace('/', '\\').split('\\')
                for i, p in enumerate(parts):
                    p_l = p.lower()
                    if p_l in ('community', 'official', 'streamedpackages'):
                        if i + 1 < len(parts):
                            next_p = parts[i + 1]
                            if next_p.lower() in ('onestore', 'steam') and i + 2 < len(parts):
                                target_pkg = parts[i + 2]
                            else:
                                target_pkg = next_p
                            break

            f_lower = f.lower()
            is_2024 = '2024' in f_lower or bool(re.search(r'msfs2024only\s*=\s*1', content if 'content' in locals() else ''))
            is_2020 = '2020' in f_lower

            vdgs_type = None
            if 'asvdgs' in f_lower or 'asxvdgs' in f_lower:
                vdgs_type = 'Aerosoft VDGS'
            elif 'gsxvdgs' in f_lower or ('gsx.ini' in f_lower and any('asvdgs' in other['filename'].lower() or 'asxvdgs' in other['filename'].lower() for other in file_entries)):
                vdgs_type = 'GSX SafeDock'

            parsed_files.append({
                'filename': f,
                'path': fp,
                'is_disabled': entry['is_disabled'],
                'afcad_path': afcad,
                'target_pkg': target_pkg,
                'scenario': scenario,
                'creator': creator,
                'gates_count': gates_count,
                'mtime': mtime_str,
                'mtime_ts': mtime_ts,
                'version': ver_str,
                'is_2024': is_2024,
                'is_2020': is_2020,
                'vdgs_type': vdgs_type,
                'is_recommended': False,
                'recommend_reason': None
            })

        db_ap = airports_db.get(icao, {}) if airports_db else {}
        is_known_world_airport = bool(db_ap)

        # Diagnosis logic
        if len(active_entries) == 0:
            status = 'DISABLED'
            reason = 'GSX profile(s) currently disabled.'
        elif not ap and not is_known_world_airport:
            status = 'ORPHAN'
            reason = 'Airport not found in your MSFS library.'
            summary['orphan'] += 1
        elif len(active_entries) > 1:
            status = 'DUPLICATE'
            active_names = [e['filename'] for e in active_entries]
            reason = f'{len(active_entries)} conflicting active profiles found for this airport ({", ".join(active_names)}).'
            summary['duplicate'] += 1

                        # Smart duplicate recommendation analysis
            for pf in parsed_files:
                f_status, f_reason = evaluate_gsx_studio_match(pf, ap)
                pf['match_status'] = f_status
                pf['match_reason'] = f_reason

                score = 0
                reasons = []
                if f_status == 'MATCHED':
                    score += 200
                    reasons.append("Aligned with active scenery")
                elif f_status == 'MISMATCH_STUDIO':
                    score -= 200
                    reasons.append("Designed for a different scenery add-on")
                elif f_status == 'MISMATCH_DEFAULT':
                    score -= 150
                    reasons.append("Designed for default MSFS")

                # MSFS 2024 match
                if pf.get('is_2024'):
                    score += 50
                    reasons.append("MSFS 2024 edition")
                elif pf.get('is_2020') and any(other.get('is_2024') for other in parsed_files):
                    score -= 50

                # Recency
                ts = pf.get('mtime_ts') or 0
                score += int(ts / (86400 * 30))

                # Gates
                gates = pf.get('gates_count') or 0
                score += min(50, gates)
                if gates >= 50:
                    reasons.append(f"{gates} gates configured")

                pf['score'] = score
                pf['score_reasons'] = reasons

            active_cands = [p for p in parsed_files if not p['is_disabled']]
            sorted_cand = sorted(active_cands if active_cands else parsed_files, key=lambda x: x.get('score', 0), reverse=True)
            if sorted_cand:
                sorted_cand[0]['is_recommended'] = True
                top_reasons = [r for r in sorted_cand[0].get('score_reasons', []) if not r.startswith('Designed for')]
                sorted_cand[0]['recommend_reason'] = ", ".join(top_reasons) if top_reasons else "Best matching profile"
        else:
            pf = next((p for p in parsed_files if not p['is_disabled']), parsed_files[0])
            status, reason = evaluate_gsx_studio_match(pf, ap)
            for other in parsed_files:
                if 'match_status' not in other or not other.get('match_status'):
                    o_status, o_reason = evaluate_gsx_studio_match(other, ap)
                    other['match_status'] = o_status
                    other['match_reason'] = o_reason
            if status == 'MATCHED':
                summary['matched'] += 1
            elif status in ('MISMATCH_STUDIO', 'MISMATCH_DEFAULT'):
                summary['mismatch'] += 1
            elif status == 'ORPHAN':
                summary['orphan'] += 1

        results[icao] = {
            'icao': icao,
            'name': ap.get('name') if (ap and ap.get('name')) else db_ap.get('name', f"{icao} Airport"),
            'city': ap.get('city') if (ap and ap.get('city')) else db_ap.get('city', ''),
            'country': ap.get('country') if (ap and ap.get('country')) else db_ap.get('country', ''),
            'lat': ap.get('lat') if ap else float(db_ap.get('lat', 0.0) or 0.0),
            'lon': ap.get('lon') if ap else float(db_ap.get('lon', 0.0) or 0.0),
            'pricing_type': ap.get('pricing_type') if ap else ('Default' if is_known_world_airport else 'Unknown'),
            'vendor': ap.get('vendor') if ap else ('Microsoft / Asobo' if is_known_world_airport else ''),
            'version': ap.get('version') if ap else None,
            'package_name': ap.get('package_name') if ap else None,
            'addon_vendor': (active_src.get('vendor') if active_src else ap.get('vendor')) if ap else None,
            'addon_version': (active_src.get('version') if active_src else ap.get('version')) if ap else None,
            'addon_name': (active_src.get('folder_name') if active_src else ap.get('package_name')) if ap else None,
            'addon_size': (active_src.get('size_str') if active_src else ap.get('size_str')) if ap else None,
            'is_asobo': bool(ap.get('is_asobo')) if ap else False,
            'is_freeware': (ap.get('pricing_type') == 'Freeware / Flightsim.to') if ap else False,
            'is_payware': (ap.get('pricing_type') == 'Payware') if ap else False,
            'status': status,
            'reason': reason,
            'files': parsed_files
        }

    # Detect installed airports without any GSX profile (active or disabled)
    installed_missing = []
    for icao, ap in installed_map.items():
        has_profile = icao in by_icao and len(by_icao[icao]) > 0
        if not has_profile:
            pt = ap.get('pricing_type', '')
            is_payware = bool(ap.get('is_payware') or pt == 'Payware')
            is_asobo = bool(ap.get('is_asobo_official') or pt == 'Asobo' or (ap.get('vendor') == 'Microsoft / Asobo'))
            is_freeware = bool((pt == 'Freeware' or pt == 'Freeware / Flightsim.to' or ap.get('is_freeware')) and not is_asobo and not is_payware)

            if is_payware or is_freeware or is_asobo:
                installed_missing.append({
                    'icao': icao,
                    'name': ap.get('name', icao),
                    'city': ap.get('city', ''),
                    'country': ap.get('country', ''),
                    'lat': ap.get('lat'),
                    'lon': ap.get('lon'),
                    'vendor': ap.get('vendor', ''),
                    'pricing_type': 'Payware' if is_payware else ('Asobo' if is_asobo else 'Freeware'),
                    'is_payware': is_payware,
                    'is_asobo': is_asobo,
                    'is_freeware': is_freeware
                })

    missing_rank = {'Payware': 1, 'Freeware': 2, 'Asobo': 3}
    installed_missing.sort(key=lambda x: (missing_rank.get(x['pricing_type'], 9), x['icao']))

    summary['missing_addons'] = len([m for m in installed_missing if not m['is_asobo']])
    summary['missing_asobo'] = len([m for m in installed_missing if m['is_asobo']])

    disabled_profiles = []
    for f in disabled_ini_files:
        fp = os.path.join(gsx_dir, f)
        icao = extract_icao_from_gsx_filename(f, valid_icaos=all_valid_icaos, file_path=fp) or ''
        ap = installed_map.get(icao)
        db_ap = airports_db.get(icao, {}) if airports_db else {}
        ap_name = ap.get('name') if ap else db_ap.get('name', icao)
        city = ap.get('city') if ap else db_ap.get('city', '')
        country = ap.get('country') if ap else db_ap.get('country', '')
        lat = ap.get('lat') if ap else db_ap.get('lat')
        lon = ap.get('lon') if ap else db_ap.get('lon')

        mtime_str = None
        try:
            mtime_ts = os.path.getmtime(fp)
            mtime_str = datetime.datetime.fromtimestamp(mtime_ts).strftime('%Y-%m-%d')
        except Exception:
            pass

        disabled_profiles.append({
            'filename': f,
            'path': fp,
            'icao': icao,
            'name': ap_name or icao,
            'city': city,
            'country': country,
            'lat': lat,
            'lon': lon,
            'mtime': mtime_str
        })

    disabled_profiles.sort(key=lambda x: (x['icao'] or 'ZZZZ', x['filename']))
    summary['disabled'] = len(disabled_profiles)

    audit_payload = {
        'summary': summary,
        'by_icao': results,
        'non_icao_files': non_icao_files,
        'missing_profiles': installed_missing,
        'disabled_profiles': disabled_profiles
    }

    # Save cache file
    try:
        audit_cache_file = os.path.join(BASE_DIR, 'gsx_audit.json')
        with open(audit_cache_file, 'w', encoding='utf-8') as f:
            json.dump(audit_payload, f, indent=2)
    except Exception:
        pass

    return audit_payload

def audit_single_airport_gsx(icao, gsx_dir=None, ap=None, airports_db=None):
    if not icao:
        return {'status': 'NONE', 'files': [], 'reason': 'No ICAO provided.'}
    target_icao = icao.upper().strip()
    if not gsx_dir:
        gsx_dir = get_default_gsx_path()
    if not gsx_dir or not os.path.exists(gsx_dir):
        return {'status': 'NONE', 'files': [], 'reason': 'GSX directory not found.'}

    if ap is None and os.path.exists(OUTPUT_JSON_PATH):
        try:
            with open(OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
                installed_list = json.load(f)
                for item in installed_list:
                    if item.get('icao') == target_icao:
                        ap = item
                        break
        except Exception:
            pass

    try:
        all_files = os.listdir(gsx_dir)
    except Exception:
        all_files = []

    matching_files = []
    for f in all_files:
        if not f.endswith('.ini') and not f.endswith('.ini.disabled'):
            continue
        fp = os.path.join(gsx_dir, f)
        f_icao = extract_icao_from_gsx_filename(f, valid_icaos={target_icao}, file_path=fp)
        if f_icao == target_icao:
            matching_files.append({
                'filename': f,
                'path': fp,
                'is_disabled': f.endswith('.disabled')
            })

    if not matching_files:
        return {'status': 'NONE', 'files': [], 'reason': 'No GSX profile installed.'}

    import datetime
    parsed_files = []
    active_entries = [e for e in matching_files if not e['is_disabled']]

    for entry in matching_files:
        f = entry['filename']
        fp = entry['path']
        afcad = None
        scenario = None
        creator = None
        gates_count = 0
        target_pkg = None
        mtime_str = None
        mtime_ts = 0
        ver_str = None

        try:
            mtime_ts = os.path.getmtime(fp)
            mtime_str = datetime.datetime.fromtimestamp(mtime_ts).strftime('%Y-%m-%d')
        except Exception:
            pass

        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as file_h:
                content = file_h.read()
            afcad_m = re.search(r'afcad_path\s*=\s*(.+)', content)
            if afcad_m:
                afcad = afcad_m.group(1).strip()
            scenario_m = re.search(r'scenario\s*=\s*(.+)', content)
            if scenario_m:
                scenario = scenario_m.group(1).strip()
            creator_m = re.search(r'creator\s*=\s*(.+)', content)
            if creator_m:
                creator = creator_m.group(1).strip()
            gates_count = len(re.findall(r'\[(?:gate|rwy|parking)\s+[^\]]+\]', content, re.IGNORECASE))
            v_m = re.search(r'version\s*=\s*["\']?([^"\'\r\n]+)["\']?', content)
            if v_m:
                ver_str = v_m.group(1).strip()
        except Exception:
            pass

        if afcad:
            parts = afcad.replace('/', '\\').split('\\')
            for i, p in enumerate(parts):
                p_l = p.lower()
                if p_l in ('community', 'official', 'streamedpackages'):
                    if i + 1 < len(parts):
                        next_p = parts[i + 1]
                        if next_p.lower() in ('onestore', 'steam') and i + 2 < len(parts):
                            target_pkg = parts[i + 2]
                        else:
                            target_pkg = next_p
                        break

        f_lower = f.lower()
        is_2024 = '2024' in f_lower or bool(re.search(r'msfs2024only\s*=\s*1', content if 'content' in locals() else ''))
        is_2020 = '2020' in f_lower

        vdgs_type = None
        if 'asvdgs' in f_lower or 'asxvdgs' in f_lower:
            vdgs_type = 'Aerosoft VDGS'
        elif 'gsxvdgs' in f_lower or ('gsx.ini' in f_lower and any('asvdgs' in other['filename'].lower() or 'asxvdgs' in other['filename'].lower() for other in matching_files)):
            vdgs_type = 'GSX SafeDock'

        parsed_files.append({
            'filename': f,
            'path': fp,
            'is_disabled': entry['is_disabled'],
            'afcad_path': afcad,
            'target_pkg': target_pkg,
            'scenario': scenario,
            'creator': creator,
            'gates_count': gates_count,
            'mtime': mtime_str,
            'mtime_ts': mtime_ts,
            'version': ver_str,
            'is_2024': is_2024,
            'is_2020': is_2020,
            'vdgs_type': vdgs_type,
            'is_recommended': False,
            'recommend_reason': None
        })

    if len(active_entries) == 0:
        status = 'DISABLED'
        reason = 'GSX profile(s) currently disabled.'
        for pf in parsed_files:
            f_status, f_reason = evaluate_gsx_studio_match(pf, ap)
            pf['match_status'] = f_status
            pf['match_reason'] = f_reason
    elif not ap:
        status = 'ORPHAN'
        reason = 'Airport not found in your MSFS library.'
        for pf in parsed_files:
            pf['match_status'] = 'ORPHAN'
            pf['match_reason'] = 'Airport not found in your MSFS library.'
    elif len(active_entries) > 1:
        status = 'DUPLICATE'
        active_names = [e['filename'] for e in active_entries]
        reason = f'{len(active_entries)} conflicting active profiles found for this airport ({", ".join(active_names)}).'
        for pf in parsed_files:
            f_status, f_reason = evaluate_gsx_studio_match(pf, ap)
            pf['match_status'] = f_status
            pf['match_reason'] = f_reason
            score = 0
            reasons = []
            if f_status == 'MATCHED':
                score += 200
                reasons.append("Aligned with active scenery")
            elif f_status == 'MISMATCH_STUDIO':
                score -= 200
                reasons.append("Designed for a different scenery add-on")
            elif f_status == 'MISMATCH_DEFAULT':
                score -= 150
                reasons.append("Designed for default MSFS")
            if pf.get('is_2024'):
                score += 50
                reasons.append("MSFS 2024 edition")
            elif pf.get('is_2020') and any(other.get('is_2024') for other in parsed_files):
                score -= 50
            ts = pf.get('mtime_ts') or 0
            score += int(ts / (86400 * 30))
            gates = pf.get('gates_count') or 0
            score += min(50, gates)
            if gates >= 50:
                reasons.append(f"{gates} gates configured")
            pf['score'] = score
            pf['score_reasons'] = reasons

        active_cands = [p for p in parsed_files if not p['is_disabled']]
        sorted_cand = sorted(active_cands if active_cands else parsed_files, key=lambda x: x.get('score', 0), reverse=True)
        if sorted_cand:
            sorted_cand[0]['is_recommended'] = True
            top_reasons = [r for r in sorted_cand[0].get('score_reasons', []) if not r.startswith('Designed for')]
            sorted_cand[0]['recommend_reason'] = ", ".join(top_reasons) if top_reasons else "Best matching profile"
    else:
        active_f = active_entries[0]
        active_pf = next((pf for pf in parsed_files if pf['filename'] == active_f['filename']), None)
        status, reason = evaluate_gsx_studio_match(active_pf, ap)
        for other in parsed_files:
            o_status, o_reason = evaluate_gsx_studio_match(other, ap)
            other['match_status'] = o_status
            other['match_reason'] = o_reason

    return {
        'status': status,
        'reason': reason,
        'files': parsed_files
    }

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
    has_existing_db = os.path.exists(OUTPUT_JSON_PATH) and os.path.getsize(OUTPUT_JSON_PATH) > 1000
    settings = {
        "auto_scan_on_startup": True,
        "scan_paths": default_paths,
        "gsx_profile_path": get_default_gsx_path(),
        "disclaimer_accepted": True if has_existing_db else False
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
        if len(key) <= 3:
            if re.search(rf'(^|[-_ ]){re.escape(key)}([-_ ]|$)', clean_fn):
                return pretty_name
        elif key in clean_fn:
            return pretty_name

    # 2. Check manifest creator / author / manufacturer against VENDOR_MAP
    if manifest_data and isinstance(manifest_data, dict):
        creator = str(manifest_data.get('creator', '')).strip()
        author = str(manifest_data.get('author', '')).strip()
        manufacturer = str(manifest_data.get('manufacturer', '')).strip()

        c_check = f"{creator} {author} {manufacturer}".lower()

        for key, pretty_name in VENDOR_MAP.items():
            if len(key) <= 3:
                if re.search(rf'\b{re.escape(key)}\b', c_check):
                    return pretty_name
            elif key in c_check:
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

def determine_pricing(source_folder, folder_name, vendor, manifest_data, icao=None, custom_prices=None):
    if icao and custom_prices and icao in custom_prices:
        val = custom_prices[icao]
        if isinstance(val, dict) and val.get('category'):
            user_cat = val['category']
            if user_cat == 'Payware':
                return "Payware", True
            elif user_cat in ['Freeware', 'Freeware / Flightsim.to']:
                return "Freeware / Flightsim.to", False

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

    # Known Official Freeware Releases (Paderborn Aerosoft, iniBuilds AT98 & KMKE giveaways)
    if 'paderborn' in fn_lower:
        return "Freeware / Flightsim.to", False
    if icao in ['AT98', 'KMKE'] and ('wolf' in fn_lower or 'at98' in fn_lower or 'milwaukee' in fn_lower or 'kmke' in fn_lower):
        return "Freeware / Flightsim.to", False

    # 3rd-Party Payware Marketplace sceneries (France VFR, Gaya, Deimos, BMW, Orbx, Sim Design Group, etc.)
    if any(p in fn_lower or p in v_lower or p in creator for p in COMMERCIAL_PAYWARE_VENDORS):
        return "Payware", True

    if 'official' in s_lower or 'streamed' in s_lower:
        return "Payware", True

    if 'community' in fn_lower or fn_lower.startswith('community'):
        return "Freeware / Flightsim.to", False

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
    content_xml_path = get_content_xml_path()
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
                    if os.path.isdir(ipath) and item != 'OneStore' and 'projectairports' not in item.lower():
                        clean_folder = item[:-9] if item.lower().endswith('.disabled') else item
                        is_disabled = item.lower().endswith('.disabled') or os.path.exists(os.path.join(ipath, 'manifest.json.disabled')) or not content_xml_status.get(clean_folder.lower(), True)
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
    content_xml_path = get_content_xml_path()
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
        
        if (
            any(k in fn_lower for k in NON_AIRPORT_KEYWORDS)
            or fn_lower.endswith(('-library', '_library', '-assetpack', '_assetpack', '-asset-pack', '-models'))
            or '-livery-' in fn_lower
            or '-aircraft-' in fn_lower
        ):
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
                
        has_scenery_dir = (
            os.path.isdir(os.path.join(full_path, 'scenery')) 
            or os.path.isdir(os.path.join(full_path, 'Scenery'))
            or os.path.isdir(os.path.join(full_path, 'scenery.disabled'))
            or os.path.isdir(os.path.join(full_path, 'Scenery.disabled'))
        )

        tokens = re.split(r'[-_ ]+', fn_lower)
        has_explicit_icao = any(len(t) == 4 and t.isalpha() and t.upper() in airports and t.lower() not in EXCLUDE_WORDS for t in tokens)

        if not has_explicit_icao:
            for t in tokens:
                m = re.match(r'^([a-zA-Z]{4})(?:light|fix|lighting|night|scene|patch|jetway|taxiway|rwy|runway|\d)', t)
                if m and m.group(1).upper() in airports and m.group(1).lower() not in EXCLUDE_WORDS:
                    has_explicit_icao = True
                    break

        if not has_explicit_icao and manifest_title:
            m_tokens = re.findall(r'(?:^|[-_ \d])([A-Za-z]{4})(?=$|[-_ \d])', manifest_title)
            if any(tok.upper() in airports and tok.lower() not in EXCLUDE_WORDS for tok in m_tokens):
                has_explicit_icao = True

        if manifest_ctype in ['AIRCRAFT', 'LIVERY', 'TOOL', 'MISC', 'INSTRUMENT', 'CORE', 'LIBRARY']:
            if not has_explicit_icao and not has_scenery_dir:
                continue

        # Filter out generic global asset libraries that have no ICAO code in folder name
        if any(k in fn_lower for k in ['assetpack', 'vegetation-library', 'windy-things', 'palm_trees_library', 'fly-in-library', 'libraryv14', 'object-library', 'objects-library']):
            if not has_explicit_icao:
                continue
        
        # Check if this package is a fix/patch or a model library/interior/mesh addon rather than a main scenery
        m_title_lower = manifest_title.lower() if manifest_title else ""
        clean_hint = pkg_order_hint
        for hint_term in ['custom_airport_patch', 'bespoke_airport_patch', 'community_airport_patch', 'official_airport_patch', 'airport_patch', 'custom_airport', 'bespoke_airport', 'community_airport']:
            clean_hint = clean_hint.replace(hint_term, '')

        is_official_asobo_base = (
            fn_lower.startswith(('asobo-airport-', 'microsoft-airport-', 'fs20-asobo-', 'fs20-microsoft-', 'fs24-asobo-', 'fs24-microsoft-'))
            or 'asobo-airport-' in fn_lower
            or 'microsoft-airport-' in fn_lower
        )

        is_fix_patch = (
            not is_official_asobo_base
            and fn_lower not in MAIN_SCENERY_EXCEPTIONS
            and (
                any(re.search(rf'\b{re.escape(k)}\b', fn_lower) for k in FIX_PATCH_KEYWORDS)
                or any(fn_lower.endswith(f"_{k}") or fn_lower.endswith(f"-{k}") for k in FIX_PATCH_KEYWORDS)
                or any(k in clean_hint for k in ['patch', 'fix', 'enhancement', 'correction', 'overlay'])
                or any(k in m_title_lower for k in ['fix', 'patch', 'enhancement', 'flatten', 'correction', 'overlay'])
            )
        )
        is_addon_package = (not is_official_asobo_base and fn_lower not in MAIN_SCENERY_EXCEPTIONS) and (is_fix_patch or any(k in fn_lower for k in ADDON_LIBRARY_KEYWORDS))

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

        # Folder prefix matching (e.g. lirflightfix20 -> LIRF)
        if not found_ap_list:
            for t in tokens:
                m = re.match(r'^([a-zA-Z]{4})(?:light|fix|lighting|night|scene|patch|jetway|taxiway|rwy|runway|\d)', t)
                if m:
                    cand = m.group(1).upper()
                    if cand in airports and cand.lower() not in EXCLUDE_WORDS:
                        found_ap_list.append((airports[cand], f"Folder Prefix ICAO ({cand})"))
                        break

        # Manifest Title explicit ICAO matching
        if not found_ap_list and manifest_title:
            m_tokens = re.findall(r'(?:^|[-_ \d])([A-Za-z]{4})(?=$|[-_ \d])', manifest_title)
            for tok in m_tokens:
                tok_u = tok.upper()
                if tok_u in airports and tok.lower() not in EXCLUDE_WORDS:
                    found_ap_list.append((airports[tok_u], f"Manifest Title ({tok_u})"))
                    break

        # Layout BGL path matching (only inspect actual compiled .bgl files)
        if not found_ap_list:
            lpath = os.path.join(full_path, 'layout.json')
            if not os.path.exists(lpath):
                lpath = os.path.join(full_path, 'layout.json.disabled')
            if os.path.exists(lpath):
                try:
                    with open(lpath, 'r', encoding='utf-8', errors='ignore') as f:
                        ldata = json.load(f)
                        entries = ldata.get('content', [])
                        bgl_entries = [c.get('path', '') for c in entries if c.get('path', '').lower().endswith('.bgl')]
                        bgl_icaos = set()
                        for bpath in bgl_entries:
                            m = re.findall(r'(?:^|[/\-_])([a-zA-Z]{4})(?:[-_.](?:airport|scenery|ap|runway|fix|patch))?\.bgl', bpath, re.IGNORECASE)
                            bgl_icaos.update(m)
                            m2 = re.findall(r'scenery[/\\](?:airports[/\\])?(?:world[/\\]scenery[/\\])?(?:airport-)?([A-Za-z]{4})[._/\\]', bpath, re.IGNORECASE)
                            bgl_icaos.update(m2)
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
            pricing_type, is_payware = determine_pricing(cat, clean_folder, vendor, manifest_data, icao=icao, custom_prices=custom_prices)
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

            # Check per-ICAO BGL disabled state inside active multi-airport packages
            source_is_disabled = is_disabled
            if not source_is_disabled and os.path.exists(full_path):
                icao_l = icao.lower()
                has_active_bgl = False
                has_disabled_bgl = False
                for root, dirs, files in os.walk(full_path):
                    for f in files:
                        f_l = f.lower()
                        if icao_l in f_l:
                            if f_l.endswith('.bgl'):
                                has_active_bgl = True
                            elif f_l.endswith('.bgl.disabled'):
                                has_disabled_bgl = True
                if has_disabled_bgl and not has_active_bgl:
                    source_is_disabled = True

            new_source = {
                "folder_name": folder_name,
                "package_path": full_path,
                "source_folder": cat,
                "match_source": match_source,
                "vendor": vendor,
                "pricing_type": pricing_type,
                "is_payware": is_payware,
                "is_asobo_official": is_asobo_official,
                "is_disabled": source_is_disabled,
                "is_addon": False if (is_asobo_official or is_official_asobo_base) else is_addon_package,
                "is_fix_patch": False if (is_asobo_official or is_official_asobo_base or is_payware) else (is_fix_patch or is_addon_package),
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
                    "elevation_ft": found_ap.get('elevation', 0),
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
    content_xml_path = get_content_xml_path()
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
            is_asobo_dis = any(
                d == f"fs24-asobo-airport-{h_icao.lower()}" 
                or d == f"asobo-airport-{h_icao.lower()}" 
                or d == f"microsoft-airport-{h_icao.lower()}"
                or h_icao.lower() in re.split(r'[-_ ]+', d)
                for d in disabled_in_xml
            )
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

                user_rating = ratings.get(h_u, 0.0)
                price_eur, is_custom_price = get_estimated_price(
                    h_u, f"fs24-asobo-airport-{h_icao.lower()}", "Microsoft / Asobo", "Asobo", english_type, True, custom_prices
                )
                detected_map[h_u] = {
                    "icao": h_u,
                    "name": ap_info.get('name', 'Unknown Airport'),
                    "city": ap_info.get('municipality', ''),
                    "country": ap_info.get('iso_country', ''),
                    "lat": float(ap_info.get('latitude_deg', 0.0)),
                    "lon": float(ap_info.get('longitude_deg', 0.0)),
                    "type": ap_info.get('type', 'airport'),
                    "english_type": english_type,
                    "elevation": int(float(ap_info.get('elevation_ft', 0))) if ap_info.get('elevation_ft') else None,
                    "elevation_ft": int(float(ap_info.get('elevation_ft', 0))) if ap_info.get('elevation_ft') else None,
                    "has_custom_scenery": True,
                    "package_name": f"fs24-asobo-airport-{h_icao.lower()}",
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
                    "rating": user_rating,
                    "price_eur": price_eur,
                    "is_custom_price": is_custom_price,
                    "version": "",
                    "size_str": "Streamed",
                    "world_update_name": get_world_update_name(h_u, f"fs24-asobo-airport-{h_icao.lower()}"),
                    "all_sources": [asobo_src]
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

        # 3. Determine if this airport has an active Official Asobo/Microsoft package
        active_asobo = any(
            (s.get('is_asobo_official') 
             or s.get('pricing_type') == 'Asobo' 
             or s.get('vendor') == 'Microsoft / Asobo'
             or s.get('folder_name', '').lower().startswith(('asobo-', 'microsoft-', 'fs20-asobo-', 'fs20-microsoft-', 'fs24-asobo-', 'fs24-microsoft-')))
            and not s.get('is_disabled') and not s.get('is_fix_patch') and not s.get('is_addon')
            for s in item['all_sources']
        )

        if item['all_sources']:
            def get_package_score(s):
                score = 0 if s.get('is_disabled') else 100
                score += get_source_priority(s.get('source_folder', ''))
                
                if active_payware:
                    if s.get('is_payware') and not s.get('is_disabled'):
                        score += 500
                elif active_asobo:
                    if (s.get('is_asobo_official') or s.get('pricing_type') == 'Asobo' or s.get('vendor') == 'Microsoft / Asobo') and not s.get('is_disabled'):
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
            elif active_asobo:
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

            if not item.get('is_custom_price'):
                p_price, p_cust = get_estimated_price(
                    icao, primary['folder_name'], item['vendor'], item['pricing_type'], item['english_type'], item['is_asobo_official'], custom_prices
                )
                item['price_eur'] = p_price
                item['is_custom_price'] = p_cust

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

    RUNWAYS_DB = {}
    RUNWAYS_DB_PATH = get_resource_file_path("airport_runways.json")
    if os.path.exists(RUNWAYS_DB_PATH):
        try:
            with open(RUNWAYS_DB_PATH, 'r', encoding='utf-8') as f:
                RUNWAYS_DB = json.load(f)
        except Exception as e:
            print("Error loading airport_runways.json:", e)

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
        item['runways'] = RUNWAYS_DB.get(icao, [])
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

def build_library_snapshot(airports):
    """
    Extracts all custom scenery packages and GSX profiles into a dictionary
    keyed by unique clean identifier.
    Clean names strip '.disabled' so toggling within SceneryX never counts as an external add/remove.
    """
    snapshot = {}
    for ap in airports:
        icao = ap.get('icao', '')
        name = ap.get('name', '') or ap.get('city', '') or icao

        # 1. Scenery packages from all_sources
        for s in ap.get('all_sources', []):
            fn = s.get('folder_name', '')
            if not fn or fn.startswith('msfs-default-') or s.get('pricing_type') == 'Default':
                continue

            clean_fn = fn[:-9] if fn.lower().endswith('.disabled') else fn
            clean_norm = re.sub(r'^(community|official)?(fs20|fs24)?-?', '', clean_fn.lower())
            key = f"pkg:{icao.lower()}:{clean_norm}"

            p_type = s.get('pricing_type') or ('Payware' if s.get('is_payware') else ('Asobo' if s.get('is_asobo_official') else 'Freeware'))

            snapshot[key] = {
                "key": key,
                "kind": "scenery",
                "folder_name": clean_fn,
                "icao": icao,
                "name": name,
                "type": p_type,
                "vendor": s.get('vendor', '') or ap.get('vendor', ''),
                "source_folder": s.get('source_folder', '') or ap.get('source_folder', ''),
                "is_patch": s.get('is_fix_patch', False) or s.get('is_addon', False)
            }

        # 2. GSX Profiles
        if ap.get('has_gsx_profile') and ap.get('gsx_profile_filename'):
            g_fn = ap.get('gsx_profile_filename', '')
            key = f"gsx:{icao.lower()}:{g_fn.lower()}"
            snapshot[key] = {
                "key": key,
                "kind": "gsx",
                "folder_name": g_fn,
                "icao": icao,
                "name": name,
                "type": "GSX Profile",
                "vendor": "GSX Pro",
                "source_folder": "GSX Profiles",
                "is_patch": False
            }

    return snapshot

def compute_scan_delta(new_airports, update_snapshot=True):
    """
    Compares the newly scanned airports with the stored library_snapshot.json.
    Returns a dict with 'added', 'removed', and 'total_changes'.
    Updates the snapshot on disk if update_snapshot is True.
    """
    current_snapshot = build_library_snapshot(new_airports)

    if not os.path.exists(SNAPSHOT_JSON_PATH):
        # Initial launch: save snapshot and return 0 changes
        if update_snapshot:
            try:
                with open(SNAPSHOT_JSON_PATH, 'w', encoding='utf-8') as f:
                    json.dump(current_snapshot, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print("Error saving initial library snapshot:", e)
        return {"added": [], "removed": [], "total_changes": 0}

    try:
        with open(SNAPSHOT_JSON_PATH, 'r', encoding='utf-8') as f:
            prev_snapshot = json.load(f)
    except Exception as e:
        print("Error reading library_snapshot.json:", e)
        prev_snapshot = {}

    added = []
    for k, item in current_snapshot.items():
        if k not in prev_snapshot:
            added.append(item)

    removed = []
    for k, item in prev_snapshot.items():
        if k not in current_snapshot:
            removed.append(item)

    delta = {
        "added": added,
        "removed": removed,
        "total_changes": len(added) + len(removed)
    }

    if update_snapshot:
        try:
            with open(SNAPSHOT_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(current_snapshot, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("Error updating library snapshot:", e)

    return delta

if __name__ == "__main__":
    run_scan()
