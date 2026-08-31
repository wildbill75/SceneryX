let map;
let markerClusterGroup;
let allAirportsData = [];
let currentlyFilteredAirports = [];
let selectedAirport = null;
let activeDrawerMode = 'MAP'; // 'MAP', 'COUNTRY', 'AIRPORT'
let userRatingsMap = {};
let currentSettings = { auto_scan_on_startup: true, scan_paths: [] };
let lastFocusedIcao = null;

// Currency & Investment Engine
let selectedCurrency = 'EUR';
const CURRENCY_SYMBOLS = { EUR: '€', USD: '$', GBP: '£' };
const CURRENCY_RATES = { EUR: 1.0, USD: 1.09, GBP: 0.85 };

// Conflict Navigation Engine
let currentConflictIndex = 0;

// Multi-select Sets
const ALL_PRICING_LIST = ['Payware', 'Freeware / Flightsim.to', 'Asobo', 'Default'];
const ALL_SOURCES_LIST = ['asobo', 'Community', 'StreamedPackages', 'Official'];
const ALL_TYPES_LIST = ['International', 'Regional', 'General Aviation', 'Heli / Water'];

const DEFAULT_STARTUP_PRICING = ['Payware', 'Freeware / Flightsim.to', 'Asobo'];
let selectedPricing = new Set(DEFAULT_STARTUP_PRICING);
let selectedSources = new Set(ALL_SOURCES_LIST);
let selectedTypes = new Set(ALL_TYPES_LIST);
let selectedMinRating = 0; // 0 = All ratings
let selectedGsxFilter = 'all'; // 'all', 'with', 'none'
let selectedAirline = null;
let selectedAirlines = new Set();
let activeRouteOrigin = null;
let activeRouteLinesGroup = null;
// Global Country Name to ISO Lookup Map
const COUNTRY_NAME_TO_ISO = {
    'afghanistan': 'AF', 'albania': 'AL', 'algeria': 'DZ', 'andorra': 'AD', 'angola': 'AO',
    'argentina': 'AR', 'armenia': 'AM', 'australia': 'AU', 'austria': 'AT', 'azerbaijan': 'AZ',
    'bahamas': 'BS', 'bahrain': 'BH', 'bangladesh': 'BD', 'barbados': 'BB', 'belarus': 'BY',
    'belgium': 'BE', 'belize': 'BZ', 'benin': 'BJ', 'bhutan': 'BT', 'bolivia': 'BO',
    'bosnia': 'BA', 'bosnia and herzegovina': 'BA', 'botswana': 'BW', 'brazil': 'BR', 'brunei': 'BN',
    'bulgaria': 'BG', 'burkina faso': 'BF', 'burundi': 'BI',
    'cambodia': 'KH', 'cameroon': 'CM', 'canada': 'CA', 'cape verde': 'CV', 'central african republic': 'CF',
    'chad': 'TD', 'chile': 'CL', 'china': 'CN', 'colombia': 'CO', 'comoros': 'KM',
    'congo': 'CG', 'dr congo': 'CD', 'democratic republic of the congo': 'CD', 'costa rica': 'CR', 'croatia': 'HR', 'cuba': 'CU',
    'cyprus': 'CY', 'czech republic': 'CZ', 'czechia': 'CZ',
    'denmark': 'DK', 'djibouti': 'DJ', 'dominica': 'DM', 'dominican republic': 'DO',
    'ecuador': 'EC', 'egypt': 'EG', 'el salvador': 'SV', 'equatorial guinea': 'GQ', 'eritrea': 'ER',
    'estonia': 'EE', 'eswatini': 'SZ', 'ethiopia': 'ET',
    'fiji': 'FJ', 'finland': 'FI', 'france': 'FR', 'french guiana': 'GF', 'french polynesia': 'PF',
    'gabon': 'GA', 'gambia': 'GM', 'georgia': 'GE', 'germany': 'DE', 'ghana': 'GH',
    'greece': 'GR', 'greenland': 'GL', 'grenada': 'GD', 'guatemala': 'GT', 'guinea': 'GN',
    'guinea-bissau': 'GW', 'guyana': 'GY',
    'haiti': 'HT', 'honduras': 'HN', 'hong kong': 'HK', 'hungary': 'HU',
    'iceland': 'IS', 'india': 'IN', 'indonesia': 'ID', 'iran': 'IR', 'iraq': 'IQ',
    'ireland': 'IE', 'israel': 'IL', 'italy': 'IT', 'ivory coast': 'CI',
    'jamaica': 'JM', 'japan': 'JP', 'jordan': 'JO',
    'kazakhstan': 'KZ', 'kenya': 'KE', 'kiribati': 'KI', 'north korea': 'KP', 'south korea': 'KR', 'korea': 'KR',
    'kosovo': 'XK', 'kuwait': 'KW', 'kyrgyzstan': 'KG',
    'laos': 'LA', 'latvia': 'LV', 'lebanon': 'LB', 'lesotho': 'LS', 'liberia': 'LR',
    'libya': 'LY', 'liechtenstein': 'LI', 'lithuania': 'LT', 'luxembourg': 'LU',
    'macao': 'MO', 'macedonia': 'MK', 'north macedonia': 'MK', 'madagascar': 'MG', 'malawi': 'MW',
    'malaysia': 'MY', 'maldives': 'MV', 'mali': 'ML', 'malta': 'MT', 'marshall islands': 'MH',
    'mauritania': 'MR', 'mauritius': 'MU', 'mexico': 'MX', 'micronesia': 'FM', 'moldova': 'MD',
    'monaco': 'MC', 'mongolia': 'MN', 'montenegro': 'ME', 'morocco': 'MA', 'mozambique': 'MZ',
    'myanmar': 'MM',
    'namibia': 'NA', 'nauru': 'NR', 'nepal': 'NP', 'netherlands': 'NL', 'holland': 'NL',
    'new caledonia': 'NC', 'new zealand': 'NZ', 'nicaragua': 'NI', 'niger': 'NE', 'nigeria': 'NG',
    'norway': 'NO',
    'oman': 'OM',
    'pakistan': 'PK', 'palau': 'PW', 'palestine': 'PS', 'panama': 'PA', 'papua new guinea': 'PG',
    'paraguay': 'PY', 'peru': 'PE', 'philippines': 'PH', 'poland': 'PL', 'portugal': 'PT', 'puerto rico': 'PR',
    'qatar': 'QA',
    'romania': 'RO', 'russia': 'RU', 'rwanda': 'RW',
    'samoa': 'WS', 'san marino': 'SM', 'saudi arabia': 'SA', 'senegal': 'SN', 'serbia': 'RS',
    'seychelles': 'SC', 'sierra leone': 'SL', 'singapore': 'SG', 'slovakia': 'SK', 'slovenia': 'SI',
    'solomon islands': 'SB', 'somalia': 'SO', 'south africa': 'ZA', 'south sudan': 'SS',
    'spain': 'ES', 'espana': 'ES', 'sri lanka': 'LK', 'sudan': 'SD', 'suriname': 'SR',
    'sweden': 'SE', 'switzerland': 'CH', 'syria': 'SY',
    'taiwan': 'TW', 'tajikistan': 'TJ', 'tanzania': 'TZ', 'thailand': 'TH', 'timor-leste': 'TL',
    'togo': 'TG', 'tonga': 'TO', 'trinidad': 'TT', 'trinidad and tobago': 'TT', 'tunisia': 'TN',
    'turkey': 'TR', 'turkiye': 'TR', 'turkmenistan': 'TM', 'tuvalu': 'TV',
    'uganda': 'UG', 'ukraine': 'UA', 'united arab emirates': 'AE', 'uae': 'AE',
    'united kingdom': 'GB', 'uk': 'GB', 'england': 'GB', 'scotland': 'GB', 'wales': 'GB',
    'united states': 'US', 'united states of america': 'US', 'usa': 'US', 'us': 'US',
    'uruguay': 'UY', 'uzbekistan': 'UZ',
    'vanuatu': 'VU', 'venezuela': 'VE', 'vietnam': 'VN', 'viet nam': 'VN',
    'yemen': 'YE',
    'zambia': 'ZM', 'zimbabwe': 'ZW'
};

// Authoritative ISO to Full English Country Name Map
const ISO_TO_COUNTRY_NAME = {
    'AF': 'Afghanistan', 'AL': 'Albania', 'DZ': 'Algeria', 'AD': 'Andorra', 'AO': 'Angola',
    'AR': 'Argentina', 'AM': 'Armenia', 'AU': 'Australia', 'AT': 'Austria', 'AZ': 'Azerbaijan',
    'BS': 'Bahamas', 'BH': 'Bahrain', 'BD': 'Bangladesh', 'BB': 'Barbados', 'BY': 'Belarus',
    'BE': 'Belgium', 'BZ': 'Belize', 'BJ': 'Benin', 'BT': 'Bhutan', 'BO': 'Bolivia',
    'BA': 'Bosnia & Herzegovina', 'BW': 'Botswana', 'BR': 'Brazil', 'BN': 'Brunei', 'BG': 'Bulgaria',
    'BF': 'Burkina Faso', 'BI': 'Burundi', 'KH': 'Cambodia', 'CM': 'Cameroon', 'CA': 'Canada',
    'CV': 'Cape Verde', 'CF': 'Central African Republic', 'TD': 'Chad', 'CL': 'Chile', 'CN': 'China',
    'CO': 'Colombia', 'KM': 'Comoros', 'CG': 'Congo', 'CD': 'DR Congo', 'CR': 'Costa Rica',
    'HR': 'Croatia', 'CU': 'Cuba', 'CY': 'Cyprus', 'CZ': 'Czech Republic', 'DK': 'Denmark',
    'DJ': 'Djibouti', 'DM': 'Dominica', 'DO': 'Dominican Republic', 'EC': 'Ecuador', 'EG': 'Egypt',
    'SV': 'El Salvador', 'GQ': 'Equatorial Guinea', 'ER': 'Eritrea', 'EE': 'Estonia', 'SZ': 'Eswatini',
    'ET': 'Ethiopia', 'FJ': 'Fiji', 'FI': 'Finland', 'FR': 'France', 'GF': 'French Guiana',
    'PF': 'French Polynesia', 'GA': 'Gabon', 'GM': 'Gambia', 'GE': 'Georgia', 'DE': 'Germany',
    'GH': 'Ghana', 'GR': 'Greece', 'GL': 'Greenland', 'GD': 'Grenada', 'GT': 'Guatemala',
    'GN': 'Guinea', 'GW': 'Guinea-Bissau', 'GY': 'Guyana', 'HT': 'Haiti', 'HN': 'Honduras',
    'HK': 'Hong Kong', 'HU': 'Hungary', 'IS': 'Iceland', 'IN': 'India', 'ID': 'Indonesia',
    'IR': 'Iran', 'IQ': 'Iraq', 'IE': 'Ireland', 'IL': 'Israel', 'IT': 'Italy', 'CI': 'Ivory Coast',
    'JM': 'Jamaica', 'JP': 'Japan', 'JO': 'Jordan', 'KZ': 'Kazakhstan', 'KE': 'Kenya', 'KI': 'Kiribati',
    'KP': 'North Korea', 'KR': 'South Korea', 'KW': 'Kuwait', 'KG': 'Kyrgyzstan', 'LA': 'Laos',
    'LV': 'Latvia', 'LB': 'Lebanon', 'LS': 'Lesotho', 'LR': 'Liberia', 'LY': 'Libya', 'LI': 'Liechtenstein',
    'LT': 'Lithuania', 'LU': 'Luxembourg', 'MO': 'Macau', 'MG': 'Madagascar', 'MW': 'Malawi',
    'MY': 'Malaysia', 'MV': 'Maldives', 'ML': 'Mali', 'MT': 'Malta', 'MH': 'Marshall Islands',
    'MR': 'Mauritania', 'MU': 'Mauritius', 'MX': 'Mexico', 'FM': 'Micronesia', 'MD': 'Moldova',
    'MC': 'Monaco', 'MN': 'Mongolia', 'ME': 'Montenegro', 'MA': 'Morocco', 'MZ': 'Mozambique',
    'MM': 'Myanmar', 'NA': 'Namibia', 'NR': 'Nauru', 'NP': 'Nepal', 'NL': 'Netherlands',
    'NZ': 'New Zealand', 'NI': 'Nicaragua', 'NE': 'Niger', 'NG': 'Nigeria', 'MK': 'North Macedonia',
    'NO': 'Norway', 'OM': 'Oman', 'PK': 'Pakistan', 'PW': 'Palau', 'PS': 'Palestine', 'PA': 'Panama',
    'PG': 'Papua New Guinea', 'PY': 'Paraguay', 'PE': 'Peru', 'PH': 'Philippines', 'PL': 'Poland',
    'PT': 'Portugal', 'PR': 'Puerto Rico', 'QA': 'Qatar', 'RO': 'Romania', 'RU': 'Russia',
    'RW': 'Rwanda', 'KN': 'Saint Kitts & Nevis', 'LC': 'Saint Lucia', 'VC': 'Saint Vincent',
    'WS': 'Samoa', 'SM': 'San Marino', 'ST': 'Sao Tome & Principe', 'SA': 'Saudi Arabia',
    'SN': 'Senegal', 'RS': 'Serbia', 'SC': 'Seychelles', 'SL': 'Sierra Leone', 'SG': 'Singapore',
    'SK': 'Slovakia', 'SI': 'Slovenia', 'SB': 'Solomon Islands', 'SO': 'Somalia', 'ZA': 'South Africa',
    'SS': 'South Sudan', 'ES': 'Spain', 'LK': 'Sri Lanka', 'SD': 'Sudan', 'SR': 'Suriname',
    'SE': 'Sweden', 'CH': 'Switzerland', 'SY': 'Syria', 'TW': 'Taiwan', 'TJ': 'Tajikistan',
    'TZ': 'Tanzania', 'TH': 'Thailand', 'TL': 'Timor-Leste', 'TG': 'Togo', 'TO': 'Tonga',
    'TT': 'Trinidad & Tobago', 'TN': 'Tunisia', 'TR': 'Turkey', 'TM': 'Turkmenistan',
    'TV': 'Tuvalu', 'UG': 'Uganda', 'UA': 'Ukraine', 'AE': 'United Arab Emirates',
    'GB': 'United Kingdom', 'US': 'United States', 'UY': 'Uruguay', 'UZ': 'Uzbekistan',
    'VU': 'Vanuatu', 'VA': 'Vatican City', 'VE': 'Venezuela', 'VN': 'Vietnam', 'YE': 'Yemen',
    'ZM': 'Zambia', 'ZW': 'Zimbabwe'
};

const REGION_VIEWPORTS = {
    'weurope': { center: [54.0, 10.0], zoom: 4 },
    'eeurope': { center: [45.0, 25.0], zoom: 4.5 },
    'namerica': { center: [48.0, -95.0], zoom: 3.5 },
    'camerica_caribbean': { center: [18.0, -78.0], zoom: 4.8 },
    'samerica': { center: [-15.0, -60.0], zoom: 3.5 },
    'asia': { center: [25.0, 105.0], zoom: 3.5 },
    'middleeast': { center: [26.0, 48.0], zoom: 4.8 },
    'nafrica': { center: [27.0, 17.0], zoom: 4.8 },
    'ssafrica': { center: [-5.0, 22.0], zoom: 3.5 },
    'oceania': { center: [-25.0, 135.0], zoom: 4 },
    'pacific': { center: [-15.0, -145.0], zoom: 3.5 }
};

const REGION_COUNTRY_MAP = {
    'weurope': ['FR', 'DE', 'GB', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'PT', 'IE', 'NO', 'SE', 'DK', 'FI', 'LU', 'IS', 'MC', 'AD', 'SM', 'VA', 'LI', 'GI', 'FO', 'AX', 'SJ'],
    'eeurope': ['PL', 'GR', 'TR', 'RO', 'CZ', 'HU', 'BG', 'HR', 'SK', 'UA', 'RS', 'SI', 'EE', 'LV', 'LT', 'CY', 'AL', 'BA', 'ME', 'MK', 'MD', 'BY', 'MT', 'GE', 'AM', 'AZ', 'RU'],
    'namerica': ['US', 'CA', 'GL', 'PM'],
    'camerica_caribbean': ['MX', 'GT', 'BZ', 'HN', 'SV', 'NI', 'CR', 'PA', 'CU', 'DO', 'JM', 'HT', 'PR', 'BS', 'TT', 'BB', 'CW', 'AW', 'GP', 'MQ', 'KY', 'VG', 'VI', 'KN', 'LC', 'VC', 'AG', 'GD', 'TC', 'SX', 'BL', 'BQ', 'MF', 'AI', 'MS'],
    'samerica': ['BR', 'AR', 'CL', 'CO', 'PE', 'VE', 'EC', 'BO', 'PY', 'UY', 'GY', 'SR', 'GF'],
    'asia': ['JP', 'CN', 'IN', 'KR', 'TH', 'ID', 'MY', 'PH', 'VN', 'SG', 'PK', 'BD', 'LK', 'NP', 'MM', 'KH', 'LA', 'TW', 'HK', 'MO', 'MN', 'KZ', 'UZ', 'TM', 'KG', 'TJ', 'AF', 'BT', 'MV', 'TL', 'BN'],
    'middleeast': ['AE', 'SA', 'QA', 'KW', 'OM', 'BH', 'JO', 'LB', 'IQ', 'IR', 'IL', 'PS', 'YE'],
    'nafrica': ['EG', 'MA', 'DZ', 'TN', 'LY', 'SD', 'MR', 'EH'],
    'ssafrica': ['ZA', 'KE', 'NG', 'GH', 'TZ', 'UG', 'ET', 'CI', 'CM', 'SN', 'ZW', 'AM', 'MU', 'RE', 'YT', 'SC', 'CV', 'AO', 'MZ', 'NA', 'BW', 'ZMW', 'ZM', 'MW', 'MG', 'RW', 'BI', 'DJ', 'ER', 'SO', 'SL', 'LR', 'GN', 'GW', 'GM', 'TG', 'BJ', 'NE', 'BF', 'ML', 'TD', 'CF', 'CG', 'CD', 'GA', 'GQ', 'ST', 'LS', 'SZ', 'SH', 'KM', 'SS'],
    'oceania': ['AU', 'NZ', 'PG', 'NF', 'CC', 'CX'],
    'pacific': ['PF', 'NC', 'FJ', 'GU', 'MP', 'WS', 'TO', 'VU', 'SB', 'FM', 'PW', 'MH', 'KI', 'NR', 'TV', 'CK', 'NU', 'WF', 'AS', 'UM', 'TK']
};

function getCountryFlagEmoji(iso) {
    if (!iso || iso.length !== 2) return '🌐';
    const codePoints = iso.toUpperCase().split('').map(char => 127397 + char.charCodeAt(0));
    return String.fromCodePoint(...codePoints);
}

let selectedCountryPricingFilters = new Set(['PAYWARE', 'FREEWARE', 'ASOBO']);
let selectedCountryTypeFilters = new Set(['INT', 'REG', 'GA', 'HW']);

function toggleCountryPricingFilter(cat) {
    if (selectedCountryPricingFilters.has(cat)) {
        if (selectedCountryPricingFilters.size > 1) {
            selectedCountryPricingFilters.delete(cat);
        }
    } else {
        selectedCountryPricingFilters.add(cat);
    }
    if (selectedCountryCode) {
        openCountryDrawer(selectedCountryCode);
        filterAirports();
    }
}

function toggleCountryTypeFilter(type) {
    if (selectedCountryTypeFilters.has(type)) {
        if (selectedCountryTypeFilters.size > 1) {
            selectedCountryTypeFilters.delete(type);
        }
    } else {
        selectedCountryTypeFilters.add(type);
    }
    if (selectedCountryCode) {
        openCountryDrawer(selectedCountryCode);
        filterAirports();
    }
}

function updateCountryFilterButtonsUI() {
    const pBtn = document.getElementById('country-btn-payware');
    const fBtn = document.getElementById('country-btn-freeware');
    const aBtn = document.getElementById('country-btn-asobo');
    const dBtn = document.getElementById('country-btn-default');

    if (pBtn) {
        const active = selectedCountryPricingFilters.has('PAYWARE');
        pBtn.className = `p-3 rounded-xl border flex items-center justify-between transition-all cursor-pointer text-left group hover:scale-[1.02] ${active ? 'bg-purple-500/20 text-purple-200 border-purple-500/40 shadow-lg shadow-purple-500/10 font-bold' : 'bg-slate-950/40 text-slate-500 border-slate-800/80 opacity-60'}`;
    }
    if (fBtn) {
        const active = selectedCountryPricingFilters.has('FREEWARE');
        fBtn.className = `p-3 rounded-xl border flex items-center justify-between transition-all cursor-pointer text-left group hover:scale-[1.02] ${active ? 'bg-cyan-500/20 text-cyan-200 border-cyan-500/40 shadow-lg shadow-cyan-500/10 font-bold' : 'bg-slate-950/40 text-slate-500 border-slate-800/80 opacity-60'}`;
    }
    if (aBtn) {
        const active = selectedCountryPricingFilters.has('ASOBO');
        aBtn.className = `p-3 rounded-xl border flex items-center justify-between transition-all cursor-pointer text-left group hover:scale-[1.02] ${active ? 'bg-amber-500/20 text-amber-200 border-amber-500/40 shadow-lg shadow-amber-500/10 font-bold' : 'bg-slate-950/40 text-slate-500 border-slate-800/80 opacity-60'}`;
    }
    if (dBtn) {
        const active = selectedCountryPricingFilters.has('DEFAULT');
        dBtn.className = `p-3 rounded-xl border flex items-center justify-between transition-all cursor-pointer text-left group hover:scale-[1.02] ${active ? 'bg-slate-800/80 text-slate-200 border-slate-700 shadow-md font-bold' : 'bg-slate-950/40 text-slate-500 border-slate-800/80 opacity-60'}`;
    }

    const intBtn = document.getElementById('country-btn-type-int');
    const regBtn = document.getElementById('country-btn-type-reg');
    const gaBtn = document.getElementById('country-btn-type-ga');
    const hwBtn = document.getElementById('country-btn-type-hw');

    if (intBtn) {
        const active = selectedCountryTypeFilters.has('INT');
        intBtn.className = `p-2.5 rounded-xl border flex items-center justify-between transition-all cursor-pointer text-left hover:scale-[1.02] ${active ? 'bg-indigo-500/20 text-indigo-200 border-indigo-500/40 font-bold' : 'bg-slate-950/40 text-slate-500 border-slate-800/80 opacity-60'}`;
    }
    if (regBtn) {
        const active = selectedCountryTypeFilters.has('REG');
        regBtn.className = `p-2.5 rounded-xl border flex items-center justify-between transition-all cursor-pointer text-left hover:scale-[1.02] ${active ? 'bg-indigo-500/20 text-indigo-200 border-indigo-500/40 font-bold' : 'bg-slate-950/40 text-slate-500 border-slate-800/80 opacity-60'}`;
    }
    if (gaBtn) {
        const active = selectedCountryTypeFilters.has('GA');
        gaBtn.className = `p-2.5 rounded-xl border flex items-center justify-between transition-all cursor-pointer text-left hover:scale-[1.02] ${active ? 'bg-indigo-500/20 text-indigo-200 border-indigo-500/40 font-bold' : 'bg-slate-950/40 text-slate-500 border-slate-800/80 opacity-60'}`;
    }
    if (hwBtn) {
        const active = selectedCountryTypeFilters.has('HW');
        hwBtn.className = `p-2.5 rounded-xl border flex items-center justify-between transition-all cursor-pointer text-left hover:scale-[1.02] ${active ? 'bg-indigo-500/20 text-indigo-200 border-indigo-500/40 font-bold' : 'bg-slate-950/40 text-slate-500 border-slate-800/80 opacity-60'}`;
    }
}

// Flight Optimizer Engine State
let flightOriginAirport = null;
let flightDestAirport = null;
let isFlightOptimizerActive = false;
let flightRouteLineGroup = null;

function filterByAirline(airlineName, btnEl = null) {
    const originAp = selectedAirport;
    if (!originAp) return;

    if (!activeRouteOrigin || activeRouteOrigin.icao !== originAp.icao) {
        selectedAirlines.clear();
        activeRouteOrigin = originAp;
    }

    if (selectedAirlines.has(airlineName)) {
        selectedAirlines.delete(airlineName);
        if (selectedAirlines.size === 0) {
            activeRouteOrigin = null;
            selectedAirline = null;
        } else {
            selectedAirline = Array.from(selectedAirlines)[selectedAirlines.size - 1];
        }
        if (btnEl) {
            btnEl.className = 'text-xs font-semibold px-2.5 py-1 rounded-lg border transition-all cursor-pointer shadow-sm bg-slate-950 text-slate-200 border-slate-800/80 hover:border-cyan-500/50 hover:text-cyan-300';
        }
    } else {
        const destIcaos = (originAp.routes && originAp.routes[airlineName]) || [];
        if (destIcaos.length === 0 && selectedAirlines.size === 0) {
            showCustomModal({
                title: 'No Route Destinations',
                message: `No scheduled route destination data found for ${airlineName} from ${originAp.icao}.`,
                type: 'info',
                confirmText: 'OK'
            });
            return;
        }
        selectedAirlines.add(airlineName);
        selectedAirline = airlineName;
        activeRouteOrigin = originAp;
        if (btnEl) {
            btnEl.className = 'text-xs font-semibold px-2.5 py-1 rounded-lg border transition-all cursor-pointer shadow-sm bg-cyan-500/25 text-cyan-300 border-cyan-400 shadow-[0_0_12px_rgba(56,189,248,0.4)] scale-105 font-bold';
        }
    }

    filterAirports();
    updateFilterUI();
    updateAirlinePillsUI(originAp);
}

function updateAirlinePillsUI(ap) {
    if (!ap) return;
    const airlinesListEl = document.getElementById('drawer-airlines-list');
    if (!airlinesListEl) return;

    const btns = airlinesListEl.querySelectorAll('button[data-airline]');
    btns.forEach(btn => {
        const alName = btn.getAttribute('data-airline');
        if (!alName) return;

        const isActive = selectedAirlines.has(alName) && (activeRouteOrigin && activeRouteOrigin.icao === ap.icao);
        if (isActive) {
            btn.className = 'text-xs font-semibold px-2.5 py-1 rounded-lg border transition-all cursor-pointer shadow-sm bg-cyan-500/25 text-cyan-300 border-cyan-400 shadow-[0_0_12px_rgba(56,189,248,0.4)] scale-105 font-bold';
        } else {
            btn.className = 'text-xs font-semibold px-2.5 py-1 rounded-lg border transition-all cursor-pointer shadow-sm bg-slate-950 text-slate-200 border-slate-800/80 hover:border-cyan-500/50 hover:text-cyan-300';
        }
    });
}

function clearAirlineFilter() {
    selectedAirline = null;
    selectedAirlines.clear();
    activeRouteOrigin = null;
    filterAirports();
    updateFilterUI();
    if (selectedAirport) {
        showAirportDetails(selectedAirport);
    }
}

/* ================= FLIGHT OPTIMIZER (MODE VOL & FPS BOOST) ================= */

let isSuppressingHoverPopups = false;

function suppressHoverPopupsTemporarily() {
    isSuppressingHoverPopups = true;
    if (map) map.closePopup();
    setTimeout(() => {
        isSuppressingHoverPopups = false;
    }, 500);
}

function setFlightOrigin(ap) {
    if (!ap) {
        flightOriginAirport = null;
    } else {
        if (flightDestAirport && flightDestAirport.icao === ap.icao) {
            flightDestAirport = null;
        }
        flightOriginAirport = ap;
    }
    updateFlightOptimizerUI();
    drawFlightOptimizerRoute();
    suppressHoverPopupsTemporarily();
}

function setFlightDest(ap) {
    if (!ap) {
        flightDestAirport = null;
    } else {
        if (flightOriginAirport && flightOriginAirport.icao === ap.icao) {
            flightOriginAirport = null;
        }
        flightDestAirport = ap;
    }
    updateFlightOptimizerUI();
    drawFlightOptimizerRoute();
    suppressHoverPopupsTemporarily();
}

function setFlightOriginByIcao(icao) {
    const ap = allAirportsData.find(a => a.icao === icao);
    if (ap) setFlightOrigin(ap);
}

function setFlightDestByIcao(icao) {
    const ap = allAirportsData.find(a => a.icao === icao);
    if (ap) setFlightDest(ap);
}

function clearFlightOrigin() {
    flightOriginAirport = null;
    updateFlightOptimizerUI();
    drawFlightOptimizerRoute();
    suppressHoverPopupsTemporarily();
}

function clearFlightDest() {
    flightDestAirport = null;
    updateFlightOptimizerUI();
    drawFlightOptimizerRoute();
    suppressHoverPopupsTemporarily();
}

function clearFlightSelection() {
    flightOriginAirport = null;
    flightDestAirport = null;
    isFlightOptimizerActive = false;
    if (flightRouteLineGroup) {
        flightRouteLineGroup.clearLayers();
    }
    updateFlightOptimizerUI();
    filterAirports();
}

function updateFlightOptimizerUI() {
    const bar = document.getElementById('flight-optimizer-bar');
    const originTag = document.getElementById('flight-origin-tag');
    const destTag = document.getElementById('flight-dest-tag');
    const badge = document.getElementById('flight-planner-badge');
    const optBtn = document.getElementById('btn-run-flight-opt');

    if (!bar) return;

    if (flightOriginAirport || flightDestAirport) {
        bar.classList.remove('hidden');
        bar.classList.add('flex');

        if (originTag) originTag.innerText = `DEP: ${flightOriginAirport ? flightOriginAirport.icao : '----'}`;
        if (destTag) destTag.innerText = `ARR: ${flightDestAirport ? flightDestAirport.icao : '----'}`;

        let count = 0;
        if (flightOriginAirport) count++;
        if (flightDestAirport) count++;
        if (badge) {
            badge.classList.remove('hidden');
            badge.innerText = count;
        }

        if (optBtn) {
            if (isFlightOptimizerActive) {
                optBtn.className = "px-3.5 py-1.5 rounded-xl bg-emerald-500 text-slate-950 font-black text-xs transition-all shadow-md shadow-emerald-500/30 flex items-center gap-1.5 cursor-pointer ring-2 ring-emerald-400 animate-pulse";
                optBtn.innerHTML = `<i class="fa-solid fa-check"></i> <span>Flight Active (+FPS)</span>`;
            } else {
                optBtn.className = "px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-black text-xs transition-all shadow-md shadow-emerald-500/20 flex items-center gap-1.5 cursor-pointer";
                optBtn.innerHTML = `<i class="fa-solid fa-bolt"></i> <span>Disable Rest (+FPS)</span>`;
            }
        }
    } else {
        bar.classList.add('hidden');
        bar.classList.remove('flex');
        if (badge) badge.classList.add('hidden');
    }
}

function drawFlightOptimizerRoute() {
    if (flightRouteLineGroup) {
        flightRouteLineGroup.clearLayers();
    } else {
        if (map) flightRouteLineGroup = L.layerGroup().addTo(map);
    }

    if (!flightOriginAirport || !flightDestAirport || !flightRouteLineGroup) return;

    const lat1 = flightOriginAirport.lat;
    const lon1 = flightOriginAirport.lon;
    const lat2 = flightDestAirport.lat;
    const lon2 = flightDestAirport.lon;

    if (!lat1 || !lon1 || !lat2 || !lon2) return;

    const arcPoints = createBezierArcPoints(lat1, lon1, lat2, lon2, 35);

    // Draw glowing flight route line (Emerald green gradient glow)
    const glowLine = L.polyline(arcPoints, {
        color: '#10b981', // Neon Emerald
        weight: 3.5,
        opacity: 0.9,
        smoothFactor: 1
    });

    glowLine.addTo(flightRouteLineGroup);
}

async function executeFlightOptimizer() {
    const keepIcaos = [];
    if (flightOriginAirport) keepIcaos.push(flightOriginAirport.icao);
    if (flightDestAirport) keepIcaos.push(flightDestAirport.icao);

    if (keepIcaos.length === 0) {
        showCustomModal("Select Departure & Arrival", "Please select at least one Departure or Arrival airport before running Flight Optimizer.", "info");
        return;
    }

    const routeText = keepIcaos.join(' ➔ ');
    showCustomModal(
        `Optimizing Flight (${routeText})`,
        `Disabling all other sceneries to maximize MSFS performance...`,
        "info"
    );

    try {
        if (window.pywebview) {
            const resRaw = await window.pywebview.api.optimize_flight_mode(JSON.stringify(keepIcaos));
            const res = JSON.parse(resRaw);
            if (res.status === 'ok') {
                isFlightOptimizerActive = true;
                if (res.airports && res.airports.length > 0) {
                    allAirportsData = res.airports;
                }
                updateStats(allAirportsData);
                updateFlightOptimizerUI();
                filterAirports();
                showCustomModal(
                    "Flight Optimizer Active! 🚀",
                    `Kept ${keepIcaos.join(' & ')} active.\nDisabled ${res.disabled_count} other sceneries for maximum FPS during your flight!`,
                    "success"
                );
            } else {
                showCustomModal("Optimization Error", res.message || "Failed to optimize sceneries.", "error");
            }
        }
    } catch (err) {
        console.error("Failed to execute flight optimizer:", err);
        showCustomModal("Error", "Flight Optimizer execution failed: " + err, "error");
    }
}

async function executeRestoreAllSceneries() {
    // Clear all departure & arrival flight selections completely
    flightOriginAirport = null;
    flightDestAirport = null;
    isFlightOptimizerActive = false;
    if (flightRouteLineGroup) {
        flightRouteLineGroup.clearLayers();
    }
    updateFlightOptimizerUI();
    filterAirports();

    showCustomModal(
        "Restoring All Sceneries...",
        "Re-enabling all previously disabled scenery packages...",
        "info"
    );

    try {
        if (window.pywebview) {
            const resRaw = await window.pywebview.api.restore_all_sceneries();
            const res = JSON.parse(resRaw);
            if (res.status === 'ok') {
                allAirportsData = res.airports;
                updateStats(allAirportsData);
                updateFlightOptimizerUI();
                filterAirports();
                showCustomModal(
                    "All Sceneries Restored! 🟢",
                    `Successfully re-enabled ${res.re_enabled_count} sceneries. All your add-ons are now active.`,
                    "success"
                );
            } else {
                showCustomModal("Restore Error", res.message || "Failed to restore sceneries.", "error");
            }
        }
    } catch (err) {
        console.error("Failed to restore sceneries:", err);
        showCustomModal("Error", "Restore execution failed: " + err, "error");
    }
}

function executeFlightOptimizerQuickPrompt() {
    if (selectedAirport) {
        if (!flightOriginAirport) {
            setFlightOrigin(selectedAirport);
            showCustomModal("Departure Airport Set 🛫", `Set ${selectedAirport.icao} as Departure airport. Now select an Arrival airport and click 'Disable Rest (+FPS)'!`, "info");
        } else if (!flightDestAirport && selectedAirport.icao !== flightOriginAirport.icao) {
            setFlightDest(selectedAirport);
            showCustomModal("Arrival Airport Set 🛬", `Set ${selectedAirport.icao} as Arrival airport. Click 'Disable Rest (+FPS)' on the bottom bar to launch Flight Mode!`, "info");
        } else {
            updateFlightOptimizerUI();
        }
    } else {
        updateFlightOptimizerUI();
        showCustomModal("Flight Optimizer 🚀", "Select a Departure airport and an Arrival airport from the map/drawer, then click 'Disable Rest (+FPS)' to disable all other sceneries during your flight!", "info");
    }
}

// Initialize App
let isAppInitialized = false;

async function ensureAppLoaded() {
    if (isAppInitialized || allAirportsData.length > 0) return;

    for (let i = 0; i < 50; i++) {
        if (window.pywebview && window.pywebview.api) {
            isAppInitialized = true;
            await loadInitialAppData();
            return;
        }
        await new Promise(r => setTimeout(r, 100));
    }

    if (!isAppInitialized && allAirportsData.length === 0) {
        isAppInitialized = true;
        await loadInitialAppData();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    renderStarRatingWidget(0);
    renderFilterStarWidget(0);
    startCurrencyCarousel();
    ensureAppLoaded();
});

window.addEventListener('pywebviewready', async () => {
    await ensureAppLoaded();
});

function initMap() {
    map = L.map('map', {
        center: [20.0, 0.0], // Global world view (Screenshot 3)
        zoom: 2.5,
        minZoom: 2,
        zoomControl: false,
        worldCopyJump: true
    });

    L.control.zoom({ position: 'topright' }).addTo(map);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
        maxZoom: 16
    }).addTo(map);

    // Dedicated high-z-index map pane for operating airline route lines (z-index 620)
    if (map && !map.getPane('routeLinesPane')) {
        const rPane = map.createPane('routeLinesPane');
        rPane.style.zIndex = '620';
        rPane.style.pointerEvents = 'none';
    }

    markerClusterGroup = L.markerClusterGroup({
        chunkedLoading: true,
        maxClusterRadius: 25,
        disableClusteringAtZoom: 7,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true
    });

    map.addLayer(markerClusterGroup);

    // Click map background (neutral area) to clear active country filter, close drawer, and restore global mode
    map.on('click', () => {
        if (flightCorridorArrivalAirport) {
            flightCorridorArrivalAirport = null;
            if (flightCorridorLayerGroup && map) {
                flightCorridorLayerGroup.clearLayers();
            }
        }
        if (selectedCountryCode || activeDrawerMode === 'COUNTRY' || selectedAirport || activeDrawerMode === 'AIRPORT') {
            exitCountryMode();
        }
    });

    loadCountryOverlays();
}

let countryGeoJsonLayer = null;
let selectedCountryCode = null;

function getFeatureIso(feature) {
    if (!feature || !feature.properties) return '';
    const p = feature.properties;
    let iso = p.ISO_A2_EH;
    if (!iso || iso === '-99') {
        iso = p.ISO_A2;
    }
    if (!iso || iso === '-99') {
        iso = p.ISO_A3 || p.ADM0_A3 || p.SU_A3 || '';
    }
    return (iso || '').toString().toUpperCase().trim();
}

async function loadCountryOverlays() {
    try {
        const resp = await fetch('countries.geojson');
        if (!resp.ok) return;
        const geoData = await resp.json();

        countryGeoJsonLayer = L.geoJSON(geoData, {
            style: feature => {
                const iso = getFeatureIso(feature);
                const isSelected = (selectedCountryCode && iso && selectedCountryCode === iso);
                return {
                    fillColor: isSelected ? '#a855f7' : '#06b6d4',
                    fillOpacity: isSelected ? 0.22 : 0.0,
                    color: isSelected ? '#a855f7' : '#475569',
                    weight: isSelected ? 2 : 0.5,
                    opacity: isSelected ? 0.9 : 0.3
                };
            },
            onEachFeature: (feature, layer) => {
                const props = feature.properties || {};
                const cName = props.NAME || props.ADMIN || props.NAME_LONG || 'Country';
                const iso = getFeatureIso(feature);

                layer.on({
                    mouseover: (e) => {
                        const l = e.target;
                        if (!selectedCountryCode || selectedCountryCode !== iso) {
                            l.setStyle({
                                fillColor: '#06b6d4',
                                fillOpacity: 0.16,
                                color: '#06b6d4',
                                weight: 1.5,
                                opacity: 0.8
                            });
                        }
                    },
                    mouseout: (e) => {
                        if (countryGeoJsonLayer) {
                            countryGeoJsonLayer.resetStyle(e.target);
                        }
                    },
                    click: (e) => {
                        L.DomEvent.stopPropagation(e);
                        if (selectedCountryCode || activeDrawerMode === 'COUNTRY') {
                            exitCountryMode();
                        } else {
                            toggleCountrySelection(iso, cName, layer);
                        }
                    }
                });
            }
        }).addTo(map);
    } catch (err) {
        console.error("Failed to load country overlay GeoJSON:", err);
    }
}

function openCountryDrawer(iso, countryName) {
    if (!iso || iso === '-99') return;

    activeDrawerMode = 'COUNTRY';
    selectedAirport = null;

    updateCountryFilterButtonsUI();

    // Auto-hide Left Sidebar to maximize map viewport
    const sb = document.getElementById('sidebar-panel');
    if (sb) sb.classList.add('-ml-80', 'opacity-0', 'pointer-events-none');

    // 1. Find all airports belonging to this country
    const isoUpper = iso.toUpperCase().trim();
    const countryAirports = allAirportsData.filter(ap => {
        const apIso = ((ap.country || ap.iso_country || '').toString()).toUpperCase().trim();
        return apIso === isoUpper;
    });

    if (countryAirports.length === 0) {
        exitCountryMode();
        return;
    }

    // 2. Set Header Data with Full English Country Name & Flag Emoji
    const resolvedName = ISO_TO_COUNTRY_NAME[isoUpper] || countryName || isoUpper;
    const flagEl = document.getElementById('country-drawer-flag');
    if (flagEl) flagEl.innerText = getCountryFlagEmoji(isoUpper);

    const nameEl = document.getElementById('country-drawer-name');
    if (nameEl) nameEl.innerText = resolvedName;

    const totalEl = document.getElementById('country-drawer-total-airports');
    if (totalEl) totalEl.innerText = countryAirports.length.toLocaleString();

    // 3. Compute Breakdown Statistics
    let countPayware = 0;
    let countFreeware = 0;
    let countAsobo = 0;
    let countDefault = 0;

    let countInt = 0;
    let countReg = 0;
    let countGa = 0;
    let countHw = 0;

    let totalSpentEur = 0;
    const processedBundles = new Set();

    const customSceneryAirports = [];

    countryAirports.forEach(ap => {
        const hasCustom = hasCustomAddonSources(ap);
        const pt = getAirportPricingType(ap);

        if (hasCustom) {
            customSceneryAirports.push(ap);
            if (pt === 'Payware') {
                countPayware++;
                // Compute spent price in EUR / local currency
                if (ap.is_bundle || ap.bundle_id) {
                    const bKey = ap.bundle_id || ap.package_name;
                    if (!processedBundles.has(bKey)) {
                        processedBundles.add(bKey);
                        totalSpentEur += (ap.bundle_total_price || 39.00);
                    }
                } else {
                    totalSpentEur += (ap.price_eur || 0);
                }
            } else if (pt === 'Asobo') {
                countAsobo++;
            } else {
                countFreeware++;
            }
        } else {
            countDefault++;
        }

        // Airport Type
        const typeStr = (ap.english_type || ap.type || '').toLowerCase();
        if (typeStr.includes('international')) {
            countInt++;
        } else if (typeStr.includes('regional')) {
            countReg++;
        } else if (typeStr.includes('general') || typeStr.includes('ga')) {
            countGa++;
        } else if (typeStr.includes('heli') || typeStr.includes('water')) {
            countHw++;
        } else {
            countReg++;
        }
    });

    // Populate Pricing Breakdown
    const pEl = document.getElementById('country-count-payware');
    if (pEl) pEl.innerText = countPayware;
    const fEl = document.getElementById('country-count-freeware');
    if (fEl) fEl.innerText = countFreeware;
    const aEl = document.getElementById('country-count-asobo');
    if (aEl) aEl.innerText = countAsobo;
    const dEl = document.getElementById('country-count-default');
    if (dEl) dEl.innerText = countDefault;

    // Populate Total Spent
    const spentEl = document.getElementById('country-drawer-total-spent');
    if (spentEl) spentEl.innerText = formatCurrency(totalSpentEur);

    // Populate Airport Types
    const intEl = document.getElementById('country-type-int');
    if (intEl) intEl.innerText = countInt;
    const regEl = document.getElementById('country-type-reg');
    if (regEl) regEl.innerText = countReg;
    const gaEl = document.getElementById('country-type-ga');
    if (gaEl) gaEl.innerText = countGa;
    const hwEl = document.getElementById('country-type-hw');
    if (hwEl) hwEl.innerText = countHw;

    // Update Interactive Country Filter Buttons
    updateCountryFilterButtonsUI();

    // Filter Airports in this country based on active country pricing & type filter sets
    const filteredCountryAirports = countryAirports.filter(ap => {
        const pt = getAirportPricingType(ap);
        let catKey = 'FREEWARE';
        if (pt === 'Payware') catKey = 'PAYWARE';
        else if (pt === 'Asobo') catKey = 'ASOBO';
        else if (pt === 'Default' || ap.pricing_type === 'Default' || ap.package_name === 'Default MSFS Base Airport') catKey = 'DEFAULT';

        if (!selectedCountryPricingFilters.has(catKey)) return false;

        const typeStr = (ap.english_type || ap.type || '').toLowerCase();
        let typeKey = 'REG';
        if (typeStr.includes('international')) typeKey = 'INT';
        else if (typeStr.includes('regional')) typeKey = 'REG';
        else if (typeStr.includes('general') || typeStr.includes('ga')) typeKey = 'GA';
        else if (typeStr.includes('heli') || typeStr.includes('water')) typeKey = 'HW';

        return selectedCountryTypeFilters.has(typeKey);
    });

    // Populate Sceneries List
    const sceneryBadgeEl = document.getElementById('country-scenery-count-badge');
    if (sceneryBadgeEl) sceneryBadgeEl.innerText = `${filteredCountryAirports.length} Airports`;

    const listEl = document.getElementById('country-airports-list');
    if (listEl) {
        if (filteredCountryAirports.length === 0) {
            listEl.innerHTML = `
                <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-center space-y-1">
                    <p class="text-xs font-semibold text-slate-400">No Airports Matching Filter</p>
                    <p class="text-[10px] text-slate-500">Try enabling more pricing or airport type filter buttons above.</p>
                </div>
            `;
        } else {
            // Sort sceneries: Payware first, then Freeware, then Asobo, then Default
            filteredCountryAirports.sort((a, b) => {
                const ptOrder = { 'Payware': 1, 'Freeware': 2, 'Asobo': 3, 'Default': 4 };
                const ptA = getAirportPricingType(a);
                const ptB = getAirportPricingType(b);
                return (ptOrder[ptA] || 9) - (ptOrder[ptB] || 9);
            });

            listEl.innerHTML = filteredCountryAirports.map(ap => {
                const pt = getAirportPricingType(ap);
                const isExpanded = (expandedCountryIcao === ap.icao);
                let badgeHtml = '';
                let borderClass = 'border-slate-800 hover:border-indigo-500/50';

                if (pt === 'Payware') {
                    badgeHtml = `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">PAYWARE</span>`;
                    borderClass = isExpanded ? 'border-purple-400 bg-purple-950/40 shadow-lg shadow-purple-950/30' : 'border-purple-500/30 hover:border-purple-400 bg-purple-950/20';
                } else if (pt === 'Freeware') {
                    badgeHtml = `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">FREEWARE</span>`;
                    borderClass = isExpanded ? 'border-cyan-400 bg-cyan-950/40 shadow-lg shadow-cyan-950/30' : 'border-cyan-500/30 hover:border-cyan-400 bg-cyan-950/20';
                } else if (pt === 'Asobo') {
                    badgeHtml = `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">ASOBO</span>`;
                    borderClass = isExpanded ? 'border-amber-400 bg-amber-950/40 shadow-lg shadow-amber-950/30' : 'border-amber-500/30 hover:border-amber-400 bg-amber-950/20';
                } else {
                    badgeHtml = `<span class="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-slate-800 text-slate-400 border border-slate-700">DEFAULT</span>`;
                    borderClass = isExpanded ? 'border-blue-400 bg-blue-950/40 shadow-lg shadow-blue-950/30' : 'border-slate-800 hover:border-slate-700 bg-slate-900/60';
                }

                const vendorStr = ap.vendor || (ap.is_asobo_official ? 'Microsoft / Asobo' : 'Community');
                const activeSrc = getActiveSource(ap);
                const safeFolder = activeSrc ? (activeSrc.folder_name || '') : (ap.package_name || '');
                const sizeStr = (activeSrc && activeSrc.size_str) ? activeSrc.size_str : (ap.size_str || '');
                const storeSearchUrl = `https://flightsim.to/sceneries?q=${encodeURIComponent(ap.icao)}`;

                let accordionHtml = '';
                const sources = ap.all_sources || [];
                const fsToSearchUrl = `https://flightsim.to/search?q=${encodeURIComponent(ap.icao)}`;
                const simMarketSearchUrl = `https://secure.simmarket.com/advanced_search_result.php?keywords=${encodeURIComponent(ap.icao)}`;

                let rowsHtml = '';
                if (sources.length > 0) {
                    rowsHtml = sources.map(s => {
                        const isInst = !s.is_disabled;
                        const devName = s.vendor || (s.is_asobo_official ? 'Microsoft / Asobo' : 'Community');
                        const sPt = s.pricing_type || (s.is_payware ? 'Payware' : (s.is_asobo_official ? 'Asobo' : 'Freeware'));
                        let pBadge = '';
                        if (sPt === 'Payware') pBadge = `<span class="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">PAYWARE</span>`;
                        else if (sPt === 'Asobo') pBadge = `<span class="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">ASOBO</span>`;
                        else if (sPt === 'Default' || ap.pricing_type === 'Default') pBadge = `<span class="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-slate-800 text-slate-400 border border-slate-700">DEFAULT</span>`;
                        else pBadge = `<span class="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">FREEWARE</span>`;

                        return `
                            <div onclick="event.stopPropagation(); window.open('${sPt === 'Payware' ? simMarketSearchUrl : fsToSearchUrl}', '_blank')"
                                 class="flex items-center justify-between p-2 rounded-lg bg-slate-900/70 hover:bg-slate-800/80 border border-slate-800/80 cursor-pointer transition-all group">
                                <div class="flex items-center gap-2 min-w-0 flex-1">
                                    <span class="text-xs font-mono font-black text-cyan-300 shrink-0">${ap.icao}</span>
                                    <span class="text-xs font-bold text-slate-200 group-hover:text-white truncate min-w-0">${devName}</span>
                                    ${pBadge}
                                </div>
                                <div class="shrink-0 pl-2">
                                    ${isInst ? '<i class="fa-solid fa-circle-check text-emerald-400 text-sm" title="Installed"></i>' : '<i class="fa-regular fa-circle text-slate-600 text-sm group-hover:text-slate-400" title="Not Installed"></i>'}
                                </div>
                            </div>
                        `;
                    }).join('');
                } else {
                    rowsHtml = `
                        <div onclick="event.stopPropagation(); window.open('${fsToSearchUrl}', '_blank')"
                             class="flex items-center justify-between p-2 rounded-lg bg-slate-900/70 hover:bg-slate-800/80 border border-slate-800/80 cursor-pointer transition-all group">
                            <div class="flex items-center gap-2 min-w-0 flex-1">
                                <span class="text-xs font-mono font-black text-cyan-300 shrink-0">${ap.icao}</span>
                                <span class="text-xs font-bold text-slate-300 group-hover:text-white truncate min-w-0">Microsoft / Asobo (Default)</span>
                                <span class="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-slate-800 text-slate-400 border border-slate-700">DEFAULT</span>
                            </div>
                            <div class="shrink-0 pl-2">
                                <i class="fa-solid fa-circle-check text-emerald-400 text-sm" title="Installed Base Airport"></i>
                            </div>
                        </div>
                    `;
                }

                const freewareSearchRow = `
                    <div onclick="event.stopPropagation(); window.open('${fsToSearchUrl}', '_blank')"
                         class="flex items-center justify-between p-2 rounded-lg bg-slate-900/40 hover:bg-slate-800/60 border border-slate-800/50 cursor-pointer transition-all group opacity-85 hover:opacity-100">
                        <div class="flex items-center gap-2 min-w-0 flex-1">
                            <span class="text-xs font-mono font-black text-slate-400 shrink-0">${ap.icao}</span>
                            <span class="text-xs font-semibold text-slate-400 group-hover:text-cyan-300 truncate min-w-0">Search Freeware on Flightsim.to</span>
                            <span class="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">FREEWARE</span>
                        </div>
                        <div class="shrink-0 pl-2">
                            <i class="fa-regular fa-circle text-slate-600 text-sm group-hover:text-cyan-400" title="Search Freeware"></i>
                        </div>
                    </div>
                `;

                const paywareSearchRow = `
                    <div onclick="event.stopPropagation(); window.open('${simMarketSearchUrl}', '_blank')"
                         class="flex items-center justify-between p-2 rounded-lg bg-slate-900/40 hover:bg-slate-800/60 border border-slate-800/50 cursor-pointer transition-all group opacity-85 hover:opacity-100">
                        <div class="flex items-center gap-2 min-w-0 flex-1">
                            <span class="text-xs font-mono font-black text-slate-400 shrink-0">${ap.icao}</span>
                            <span class="text-xs font-semibold text-slate-400 group-hover:text-purple-300 truncate min-w-0">Search Payware Stores (SimMarket)</span>
                            <span class="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">PAYWARE</span>
                        </div>
                        <div class="shrink-0 pl-2">
                            <i class="fa-regular fa-circle text-slate-600 text-sm group-hover:text-purple-400" title="Search Payware Stores"></i>
                        </div>
                    </div>
                `;

                accordionHtml = `
                    <div id="country-accordion-${ap.icao}" class="mt-2.5 pt-2.5 border-t border-slate-800/80 ${isExpanded ? '' : 'hidden'}">
                        <div class="p-2 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1.5 font-mono">
                            ${rowsHtml}
                            ${freewareSearchRow}
                            ${paywareSearchRow}
                        </div>
                    </div>
                `;

                return `
                    <div id="country-ap-card-${ap.icao}"
                         onclick="selectCountryAirport('${ap.icao}')" 
                         class="p-3 rounded-xl bg-slate-900/90 border ${borderClass} shadow-md hover:bg-slate-850 cursor-pointer transition-all flex flex-col gap-1 group">
                        <div class="flex items-center justify-between gap-2.5 min-w-0">
                            <div class="min-w-0 flex-1">
                                <div class="flex items-center gap-2 mb-0.5">
                                    <span class="text-xs font-mono font-black text-white group-hover:text-cyan-300 transition-colors">${ap.icao}</span>
                                    ${badgeHtml}
                                </div>
                                <h4 class="text-xs font-extrabold text-slate-200 truncate group-hover:text-white leading-tight">${ap.name}</h4>
                                <p class="text-[10px] font-medium text-slate-400 truncate mt-0.5">${ap.city || 'Unknown City'} • <span class="text-slate-300 font-semibold">${vendorStr}</span></p>
                            </div>
                            <i id="country-chevron-${ap.icao}" class="fa-solid ${isExpanded ? 'fa-chevron-down text-cyan-400' : 'fa-chevron-right text-slate-500'} text-xs group-hover:text-white transition-all shrink-0"></i>
                        </div>
                        ${accordionHtml}
                    </div>
                `;
            }).join('');
        }
    }

    // 4. Switch Drawer Modes and Open Drawer
    const apMode = document.getElementById('drawer-airport-mode');
    if (apMode) apMode.classList.add('hidden');
    const cMode = document.getElementById('drawer-country-mode');
    if (cMode) cMode.classList.remove('hidden');
    const drawer = document.getElementById('detail-drawer');
    if (drawer) drawer.classList.remove('translate-x-full');
}

let expandedCountryIcao = null;

function selectCountryAirport(icao) {
    if (!icao) return;
    const ap = allAirportsData.find(a => a.icao === icao);
    if (!ap) return;

    if (map && ap.lat && ap.lon) {
        map.flyTo([ap.lat, ap.lon], 13, {
            animate: true,
            duration: 1.2
        });
    }

    const targetCard = document.getElementById(`country-ap-card-${icao}`);
    const accordionEl = document.getElementById(`country-accordion-${icao}`);
    const iconEl = document.getElementById(`country-chevron-${icao}`);

    if (accordionEl) {
        const isHidden = accordionEl.classList.contains('hidden');
        document.querySelectorAll('[id^="country-accordion-"]').forEach(el => el.classList.add('hidden'));
        document.querySelectorAll('[id^="country-chevron-"]').forEach(el => el.className = 'fa-solid fa-chevron-right text-xs text-slate-500 group-hover:text-white transition-all shrink-0');

        if (isHidden) {
            accordionEl.classList.remove('hidden');
            if (iconEl) iconEl.className = 'fa-solid fa-chevron-down text-xs text-cyan-400 transition-all shrink-0';
            expandedCountryIcao = icao;
        } else {
            expandedCountryIcao = null;
        }
    }

    if (targetCard) {
        targetCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

async function toggleCountrySceneryInPlace(icao, folderName) {
    if (!window.pywebview || isToggleInProgress || !icao) return;
    isToggleInProgress = true;
    try {
        const targetPkg = folderName || 'DEFAULT';
        const resStr = await window.pywebview.api.select_scenery_option(icao, targetPkg);
        const res = JSON.parse(resStr);
        if (res.status === 'ok') {
            allAirportsData = res.airports;
            allAirportsData.forEach(ap => {
                if (userRatingsMap[ap.icao] !== undefined) {
                    ap.rating = userRatingsMap[ap.icao];
                }
            });
            updateStats(allAirportsData);
            filterAirports();
            if (selectedCountryCode) {
                expandedCountryIcao = icao;
                openCountryDrawer(selectedCountryCode, selectedCountryName);
            }
            showToast(`✓ ${icao} Scenery State Updated`, 'success');
        }
    } catch (e) {
        console.error("Failed to toggle scenery in country mode:", e);
    } finally {
        isToggleInProgress = false;
    }
}

function resetConflictingFiltersForCountrySelection() {
    selectedRegions.clear();
    updateRegionPillUI();
}

function toggleCountrySelection(iso, countryName, layer, forceSelect = false) {
    if (!iso || iso === '-99') return;

    const isoUpper = iso.toUpperCase().trim();

    // If currently in Country Mode, ANY click on map/polygon exits Country Mode back to Global Addon Mode
    if ((selectedCountryCode || activeDrawerMode === 'COUNTRY') && !forceSelect) {
        exitCountryMode();
        return;
    }

    selectedCountryCode = isoUpper;
    selectedCountryName = countryName || isoUpper;
    selectedCountryPricingFilters = new Set(['PAYWARE', 'FREEWARE', 'ASOBO']);
    selectedCountryTypeFilters = new Set(['INT', 'REG', 'GA', 'HW']);
    resetConflictingFiltersForCountrySelection();

    // Smooth zoom to country bounds
    if (countryGeoJsonLayer) {
        const matchingLayers = [];
        countryGeoJsonLayer.eachLayer(l => {
            const lIso = getFeatureIso(l.feature);
            if (lIso === isoUpper) {
                matchingLayers.push(l);
            }
        });

        if (matchingLayers.length > 0) {
            // If France (FR), fit bounds to main European France polygon to prevent overseas territories from over-expanding zoom
            let targetLayer = matchingLayers[0];
            if (isoUpper === 'FR') {
                const mainFrance = matchingLayers.find(l => {
                    const b = l.getBounds();
                    return b.getNorth() > 40 && b.getSouth() < 52 && b.getEast() > -5 && b.getWest() < 10;
                });
                if (mainFrance) targetLayer = mainFrance;
            }

            if (targetLayer && targetLayer.getBounds) {
                map.fitBounds(targetLayer.getBounds(), { padding: [40, 40], maxZoom: 7, animate: true });
            }
        } else if (layer && layer.getBounds) {
            map.fitBounds(layer.getBounds(), { padding: [40, 40], maxZoom: 7, animate: true });
        }
    }

    openCountryDrawer(isoUpper, countryName);

    if (countryGeoJsonLayer) {
        countryGeoJsonLayer.eachLayer(l => countryGeoJsonLayer.resetStyle(l));
    }

    filterAirports();
}

async function loadInitialAppData() {
    try {
        updateSplashProgress(15, "Initializing SceneryX Engine...", "Starting components");
        if (!map) initMap();
        if (window.pywebview && window.pywebview.api) {
            try {
                updateSplashProgress(25, "Loading user preferences...", "Settings & Credentials");
                const cfgStr = await window.pywebview.api.get_settings();
                if (cfgStr) {
                    currentSettings = JSON.parse(cfgStr);
                    loadSimBriefSettingsUI();
                }
            } catch(e) {
                console.warn("Settings loading warning:", e);
            }

            try {
                updateSplashProgress(35, "Loading user ratings database...", "Database");
                const rStr = await window.pywebview.api.get_ratings();
                if (rStr) {
                    userRatingsMap = JSON.parse(rStr);
                }
            } catch(e) {
                console.warn("Ratings loading warning:", e);
            }
        }
        await loadAirportsData();
    } catch (e) {
        console.error("Error loading app initial data:", e);
        await loadAirportsData();
    }
}

function updateSplashProgress(percent, text, folder) {
    const bar = document.getElementById('splash-progress-bar');
    const pText = document.getElementById('splash-percent-text');
    const sText = document.getElementById('splash-status-text');
    const fText = document.getElementById('splash-folder-text');

    if (bar) bar.style.width = `${percent}%`;
    if (pText) pText.innerText = `${percent}%`;
    if (sText && text) sText.innerText = text;
    if (fText && folder) fText.innerText = folder;
}

function hideSplashScreen() {
    const splash = document.getElementById('splash-screen');
    if (splash) {
        updateSplashProgress(100, "Ready!", "Scan Complete");
        setTimeout(() => {
            splash.style.opacity = '0';
            setTimeout(() => {
                splash.style.display = 'none';
            }, 700);
        }, 300);
    }
}

async function loadAirportsData() {
    try {
        updateSplashProgress(25, "Loading airports database...", "Airports DB");
        let response;
        if (window.pywebview) {
            updateSplashProgress(35, "Loading user configuration...", "Settings & Credentials");
            try {
                const settingsStr = await window.pywebview.api.get_settings();
                if (settingsStr) {
                    currentSettings = JSON.parse(settingsStr);
                    loadSimBriefSettingsUI();
                    const st = currentSettings.settings || currentSettings;
                    if (st && st.flight_mode) {
                        updateFlightModeBannerUI(st.flight_mode);
                    }
                }
            } catch(e) {
                console.warn("Could not load settings on startup:", e);
            }

            updateSplashProgress(55, "Scanning MSFS packages & GSX profiles...", "Community & OneStore");
            const dataStr = await window.pywebview.api.get_airports();
            updateSplashProgress(85, "Parsing scenery packages...", "Rendering Map");
            allAirportsData = JSON.parse(dataStr);
            if (window.pywebview.api.get_world_airport_coords) {
                try {
                    const coordsStr = await window.pywebview.api.get_world_airport_coords();
                    window.worldAirportCoords = JSON.parse(coordsStr);
                } catch(e) {
                    console.warn("Could not load worldAirportCoords:", e);
                }
            }
        } else {
            response = await fetch('/api/airports');
            if (!response.ok) {
                response = await fetch('installed_airports.json');
            }
            allAirportsData = await response.json();
        }

        // Apply loaded user ratings to allAirportsData
        allAirportsData.forEach(ap => {
            if (userRatingsMap[ap.icao] !== undefined) {
                ap.rating = userRatingsMap[ap.icao];
            } else {
                ap.rating = ap.rating || 0;
            }
            ap._searchKey = `${ap.icao} ${ap.name} ${ap.city || ''} ${ap.package_name || ''} ${ap.vendor || ''}`.toLowerCase();
        });

        updateStats(allAirportsData);
        updateFilterUI();
        filterAirports();
        hideSplashScreen();
        checkFirstLaunchDisclaimer();
    } catch (err) {
        console.error("Failed to load airports:", err);
        hideSplashScreen();
        checkFirstLaunchDisclaimer();
    }
}

async function checkFirstLaunchDisclaimer() {
    try {
        const accepted = localStorage.getItem('sceneryx_disclaimer_accepted');
        if (accepted === 'true') {
            return;
        }

        if (window.pywebview && window.pywebview.api && window.pywebview.api.is_disclaimer_accepted) {
            const resStr = await window.pywebview.api.is_disclaimer_accepted();
            const res = JSON.parse(resStr);
            if (res.accepted) {
                try {
                    localStorage.setItem('sceneryx_disclaimer_accepted', 'true');
                } catch (e) {}
                return;
            }
        }

        const modal = document.getElementById('disclaimer-modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    } catch (e) {
        console.error("Disclaimer check failed:", e);
    }
}

async function agreeAndContinueApp() {
    try {
        localStorage.setItem('sceneryx_disclaimer_accepted', 'true');
        if (window.pywebview && window.pywebview.api && window.pywebview.api.accept_disclaimer) {
            await window.pywebview.api.accept_disclaimer();
        }
    } catch (e) {
        console.error("Error saving disclaimer acceptance:", e);
    }
    const modal = document.getElementById('disclaimer-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

function disagreeAndExitApp() {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.close_app) {
        window.pywebview.api.close_app();
    } else {
        window.close();
    }
}

async function openSupportLink() {
    const targetUrl = "https://www.flightsim.to/profile/wildbill75";
    try {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.open_external_url) {
            await window.pywebview.api.open_external_url(targetUrl);
        } else {
            window.open(targetUrl, '_blank');
        }
    } catch (e) {
        console.error("Failed to open support URL:", e);
        window.open(targetUrl, '_blank');
    }
}

function formatCurrency(amountEur) {
    const rate = CURRENCY_RATES[selectedCurrency] || 1.0;
    const symbol = CURRENCY_SYMBOLS[selectedCurrency] || '€';
    const val = (amountEur || 0) * rate;
    return `${symbol}${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function setCurrency(curr) {
    selectedCurrency = curr;
    ['EUR', 'USD', 'GBP'].forEach(c => {
        const btn = document.getElementById(`curr-btn-${c}`);
        if (btn) {
            if (c === curr) {
                btn.className = "font-bold text-emerald-400";
            } else {
                btn.className = "text-slate-500 hover:text-slate-300";
            }
        }
    });
    updateStats(allAirportsData);
    if (activeDrawerMode === 'AIRPORT' && selectedAirport) {
        showAirportDetails(selectedAirport);
    } else if (activeDrawerMode === 'COUNTRY' && selectedCountryCode) {
        openCountryDrawer(selectedCountryCode);
    }
}

function updateConflictNavigator() {
    const conflictAirports = allAirportsData.filter(a => a.has_conflict);
    const pill = document.getElementById('conflict-nav-pill');
    const counter = document.getElementById('conflict-nav-counter');
    const indexDisplay = document.getElementById('conflict-nav-index');

    if (!pill) return;

    if (conflictAirports.length > 0) {
        pill.classList.remove('hidden');
        counter.innerText = conflictAirports.length;
        if (currentConflictIndex >= conflictAirports.length) {
            currentConflictIndex = 0;
        }
        indexDisplay.innerText = `${currentConflictIndex + 1}/${conflictAirports.length}`;
    } else {
        pill.classList.add('hidden');
        currentConflictIndex = 0;
    }
}

function navigateConflict(direction) {
    const conflictAirports = allAirportsData.filter(a => a.has_conflict);
    if (conflictAirports.length === 0) return;

    currentConflictIndex += direction;
    if (currentConflictIndex >= conflictAirports.length) {
        currentConflictIndex = 0;
    } else if (currentConflictIndex < 0) {
        currentConflictIndex = conflictAirports.length - 1;
    }

    const targetAp = conflictAirports[currentConflictIndex];
    document.getElementById('conflict-nav-index').innerText = `${currentConflictIndex + 1}/${conflictAirports.length}`;
    
    focusAirportWithAnimation(targetAp);
}

let currencyList = ['EUR', 'USD', 'GBP'];
let currencyIndex = 0;
let currencyInterval = null;
let isCurrencyCarouselPaused = false;

function startCurrencyCarousel() {
    if (currencyInterval) clearInterval(currencyInterval);
    currencyInterval = setInterval(() => {
        if (isCurrencyCarouselPaused) return;
        currencyIndex = (currencyIndex + 1) % currencyList.length;
        selectedCurrency = currencyList[currencyIndex];
        updateInvestmentBanner();
        if (activeDrawerMode === 'AIRPORT' && selectedAirport) {
            showAirportDetails(selectedAirport);
        } else if (activeDrawerMode === 'COUNTRY' && selectedCountryCode) {
            openCountryDrawer(selectedCountryCode);
        }
    }, 10000); // 10 seconds per currency
}

function pauseCurrencyCarousel() {
    isCurrencyCarouselPaused = true;
}

function resumeCurrencyCarousel() {
    setTimeout(() => {
        const inputEl = document.getElementById('drawer-price-input');
        if (document.activeElement !== inputEl) {
            isCurrencyCarouselPaused = false;
        }
    }, 1500);
}

function updateInvestmentBanner() {
    let totalSpentEur = 0;
    let paywareCount = 0;
    const processedBundles = new Set();

    allAirportsData.forEach(ap => {
        const pt = ap.pricing_type || (ap.is_asobo_official ? "Asobo / MS" : "Freeware / Flightsim.to");
        if (pt === "Payware" || ap.is_payware) {
            paywareCount++;
            if (ap.is_bundle || ap.bundle_id) {
                const bKey = ap.bundle_id || ap.package_name;
                if (!processedBundles.has(bKey)) {
                    processedBundles.add(bKey);
                    totalSpentEur += (ap.bundle_total_price || 39.00);
                }
            } else {
                totalSpentEur += (ap.price_eur || 0);
            }
        }
    });

    const bannerEl = document.getElementById('investment-banner-text');
    const cardEl = document.getElementById('investment-card');

    if (bannerEl) {
        const formatted = formatCurrency(totalSpentEur);
        bannerEl.innerText = formatted;
    }

    if (cardEl) {
        const avgPriceEur = paywareCount > 0 ? (totalSpentEur / paywareCount) : 0;
        const avgFormatted = formatCurrency(avgPriceEur);
        cardEl.title = `Based on single sceneries & bundle packs (Avg ${avgFormatted}/scenery across ${paywareCount} payware sceneries).`;
    }
}

function getActiveSource(ap) {
    if (!ap || !ap.all_sources) return null;
    return ap.all_sources.find(s => !s.is_disabled && !(s.is_default || (s.folder_name && s.folder_name.startsWith('msfs-default-')))) || null;
}

function hasCustomAddonSources(ap) {
    if (!ap || !ap.all_sources) return false;
    return ap.all_sources.some(s => !(s.is_default || s.pricing_type === 'Default' || (s.folder_name && s.folder_name.startsWith('msfs-default-'))));
}

function getAirportPricingType(ap) {
    if (!ap) return 'Default';
    
    const activeSrc = getActiveSource(ap);
    if (!activeSrc) {
        return 'Default';
    }

    if (ap.pricing_type === 'Payware' || activeSrc.is_payware || activeSrc.pricing_type === 'Payware') {
        return 'Payware';
    }
    if (ap.pricing_type === 'Asobo' || activeSrc.is_asobo_official || activeSrc.pricing_type === 'Asobo' || (activeSrc.vendor && activeSrc.vendor.toLowerCase().includes('asobo'))) {
        return 'Asobo';
    }
    return 'Freeware / Flightsim.to';
}

function getAirportCategory(ap) {
    if (!ap) return 'DEFAULT';
    const activeSrc = getActiveSource(ap);
    if (!activeSrc) return 'DEFAULT';

    const pt = getAirportPricingType(ap);
    if (pt === 'Asobo') return 'ASOBO';
    if (pt === 'Payware') return 'PAYWARE';
    if (pt === 'Default') return 'DEFAULT';
    return 'FREEWARE';
}

function updateStats(airports) {
    document.getElementById('stat-total').innerText = airports.length.toLocaleString();

    let asoboCount = 0;
    let paywareCount = 0;
    let freewareCount = 0;
    let defaultCount = 0;

    airports.forEach(ap => {
        const nonDefaultSources = ap.all_sources ? ap.all_sources.filter(s => !(s.pricing_type === 'Default' || (s.folder_name && s.folder_name.startsWith('msfs-default-')))) : [];
        const hasActiveCustom = nonDefaultSources.some(s => !s.is_disabled);

        if (!hasActiveCustom) {
            defaultCount++;
        } else {
            const pt = getAirportPricingType(ap);
            if (pt === 'Payware') paywareCount++;
            else if (pt === 'Asobo') asoboCount++;
            else freewareCount++;
        }
    });

    document.getElementById('stat-asobo').innerText = asoboCount.toLocaleString();
    document.getElementById('stat-payware').innerText = paywareCount.toLocaleString();
    document.getElementById('stat-freeware').innerText = freewareCount.toLocaleString();
    const defEl = document.getElementById('stat-default');
    if (defEl) defEl.innerText = defaultCount.toLocaleString();

    updateInvestmentBanner();
    updateConflictNavigator();
}

let currentFlightMode = { active: false, icaos: [] };

function createCustomIcon(ap) {
    const nonDefaultSources = ap.all_sources ? ap.all_sources.filter(s => !(s.pricing_type === 'Default' || (s.folder_name && s.folder_name.startsWith('msfs-default-')))) : [];
    let isApDisabled = ap.is_disabled || (nonDefaultSources.length > 0 && nonDefaultSources.every(s => s.is_disabled));

    const cat = getAirportCategory(ap);
    let color = '#06b6d4'; // Freeware = Neon Cyan
    if (cat === 'ASOBO') color = '#f59e0b'; // Asobo Handcrafted = Amber/Gold
    else if (cat === 'PAYWARE') color = '#a855f7'; // Payware = Neon Purple
    else if (cat === 'DEFAULT') color = '#3b82f6'; // Default MSFS = Soft Royal Blue

    // Check if airport has at least one active Fix/Patch!
    const hasActiveFix = ap.all_sources && ap.all_sources.some(s => s.is_fix_patch && !s.is_disabled);

    let strokeColor = ap.has_conflict ? '#ef4444' : '#ffffff';
    let strokeWidth = ap.has_conflict ? '2' : '1.2';

    if (isApDisabled && cat !== 'DEFAULT') {
        color = '#475569'; // Slate 600 Matte Gray fill
        strokeColor = '#cbd5e1'; // Crisp Silver/Slate 300 Outline
        strokeWidth = '1.5';
    }

    if (hasActiveFix) {
        strokeColor = '#10b981'; // Emerald Green stroke outline for airports with active Fix/Patch!
        strokeWidth = '2.5';
    }

    // Default MSFS procedural airports are drawn as CIRCLES / DOTS (not stars)
    const isCircleShape = (cat === 'DEFAULT');

    const svgIcon = isCircleShape ? `
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="${hasActiveFix ? 'drop-shadow-[0_0_8px_rgba(16,185,129,0.9)]' : 'drop-shadow-md'}">
            <circle cx="12" cy="12" r="7.5" fill="${color}" stroke="${strokeColor}" stroke-width="${strokeWidth}" />
            <circle cx="12" cy="12" r="2.5" fill="#ffffff" opacity="0.9" />
        </svg>
    ` : `
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="${hasActiveFix ? 'drop-shadow-[0_0_8px_rgba(16,185,129,0.9)]' : 'drop-shadow-md'}">
            <path d="M12 2l2.9 6.26 6.9.83-5.2 4.7 1.4 6.84L12 17.1 5.9 20.63l1.4-6.84-5.2-4.7 6.9-.83L12 2z" 
                  fill="${color}" stroke="${strokeColor}" stroke-width="${strokeWidth}" stroke-linejoin="round"/>
        </svg>
    `;

    return L.divIcon({
        html: svgIcon,
        className: `custom-map-marker ${isApDisabled && !hasActiveFix ? 'grayscale-[0.5]' : ''}`,
        iconSize: isCircleShape ? [22, 22] : [26, 26],
        iconAnchor: isCircleShape ? [11, 11] : [13, 13]
    });
}

function getAirportPopupHtml(ap) {
    const cat = getAirportCategory(ap);
    let badgeClass = 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 shadow-sm';
    let badgeLabel = 'Freeware';
    let icaoColorClass = 'text-cyan-400';
    let publisherColorClass = 'text-cyan-400';

    if (cat === 'DEFAULT') {
        badgeClass = 'bg-blue-500/20 text-blue-300 border-blue-500/40 shadow-sm';
        badgeLabel = 'Default MSFS';
        icaoColorClass = 'text-blue-400';
        publisherColorClass = 'text-slate-400';
    } else if (cat === 'ASOBO') {
        badgeClass = 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-sm';
        badgeLabel = 'Asobo';
        icaoColorClass = 'text-amber-400';
        publisherColorClass = 'text-amber-400';
    } else if (cat === 'PAYWARE') {
        badgeClass = 'bg-purple-500/20 text-purple-300 border-purple-500/40 shadow-sm';
        badgeLabel = 'Payware Addon';
        icaoColorClass = 'text-purple-400';
        publisherColorClass = 'text-purple-400';
    }

    const ratingVal = ap.rating || 0;
    const ratingBadgeHtml = ratingVal > 0 ? `
        <div class="flex items-center gap-1.5 text-amber-400 font-bold text-xs pt-1">
            <i class="fa-solid fa-star text-xs"></i>
            <span>${ratingVal.toFixed(1)} / 5.0</span>
        </div>
    ` : '';

    const conflictBadgeHtml = ap.has_conflict ? `
        <div class="mt-1.5 flex items-center gap-1.5 text-red-400 font-bold text-xs bg-red-500/10 px-2.5 py-1 rounded-lg border border-red-500/30">
            <i class="fa-solid fa-triangle-exclamation"></i>
            <span>Conflict: ${ap.conflict_count} Active Sceneries</span>
        </div>
    ` : '';

    const allSourcesDisabled = ap.all_sources && ap.all_sources.length > 0 && ap.all_sources.every(s => s.is_disabled);
    const isFallbackDefault = ap.is_disabled || allSourcesDisabled || cat === 'DEFAULT';

    const publisherHtml = (!isFallbackDefault && ap.vendor) ? `
        <div class="pt-2 border-t border-slate-800/80">
            <span class="text-sm font-black ${publisherColorClass} truncate block tracking-wide">${ap.vendor}</span>
        </div>
    ` : '';

    return `
        <div class="p-1.5 font-['Outfit'] space-y-2.5">
            <div class="flex items-center justify-between gap-2.5">
                <span class="text-2xl font-black font-mono ${icaoColorClass} leading-none tracking-tight">${ap.icao}</span>
                <span class="text-xs font-mono font-bold px-3 py-1 rounded-full border ${badgeClass} shrink-0">${badgeLabel}</span>
            </div>
            <div>
                <div class="text-sm lg:text-base font-extrabold text-white leading-snug line-clamp-2">${ap.name}</div>
                <div class="text-xs font-medium text-slate-300 mt-0.5 truncate">${ap.city || ''} ${ap.country ? '(' + ap.country + ')' : ''}</div>
            </div>
            ${publisherHtml}
            ${ratingBadgeHtml}
            ${conflictBadgeHtml}
            <div class="text-xs font-bold ${icaoColorClass} pt-2 border-t border-slate-800/80 flex justify-between items-center">
                <span>${ap.english_type || ap.type}</span>
            </div>
        </div>
    `;
}

let isToggleInProgress = false;

function toggleAirportScenery(icao) {
    if (!window.pywebview || isToggleInProgress) return;
    isToggleInProgress = true;
    window.pywebview.api.toggle_airport_disabled(icao).then(resStr => {
        isToggleInProgress = false;
        try {
            const res = JSON.parse(resStr);
            if (res.status === 'success') {
                allAirportsData = res.airports || [];
                filterAirports();
                if (selectedAirport && selectedAirport.icao === icao) {
                    const updated = allAirportsData.find(a => a.icao === icao);
                    if (updated) showAirportDetails(updated);
                }
            } else if (res.message) {
                showCustomModal({
                    title: 'Action Not Allowed',
                    message: res.message,
                    type: 'warning',
                    confirmText: 'OK'
                });
            }
        } catch(e){}
    }).catch(() => { isToggleInProgress = false; });
}

function toggleSelectedAirportScenery() {
    if (!selectedAirport) return;
    toggleAirportScenery(selectedAirport.icao);
}

function renderAirportsOnMap(airports) {
    if (!map) return;

    markerClusterGroup.clearLayers();

    const markers = [];

    airports.forEach(ap => {
        if (!ap.lat || !ap.lon) return;

        const icon = createCustomIcon(ap);
        const marker = L.marker([ap.lat, ap.lon], { icon: icon });

        // Bind default preview popup content
        marker.bindPopup(getAirportPopupHtml(ap), {
            maxWidth: 340,
            minWidth: 250,
            closeButton: false,
            autoClose: true
        });

        // Hover events for quick popup preview (shows developer/publisher)
        marker.on('mouseover', function () {
            if (isSuppressingHoverPopups) return;
            this.setPopupContent(getAirportPopupHtml(ap));
            this.openPopup();
        });

        marker.on('mouseout', function () {
            this.closePopup();
        });

        // Left-Click event: opens detailed drawer on right sidebar (or Alt+Click for Flight Corridor)
        marker.on('click', function (e) {
            if (e.originalEvent) {
                L.DomEvent.stopPropagation(e.originalEvent);
            }
            if (e.originalEvent && (e.originalEvent.altKey || e.originalEvent.metaKey)) {
                setArrivalAirportCorridor(ap);
            } else {
                if (flightCorridorArrivalAirport) {
                    clearFlightCorridor();
                }
                if (activeDrawerMode === 'COUNTRY') {
                    selectCountryAirport(ap.icao);
                } else {
                    showAirportDetails(ap);
                }
            }
        });

        // Right-Click event: toggles scenery activation state directly & changes star color!
        marker.on('contextmenu', function (e) {
            if (e.originalEvent) {
                e.originalEvent.preventDefault();
                e.originalEvent.stopPropagation();
            }
            toggleAirportScenery(ap.icao);
        });

        markers.push(marker);
    });

    markerClusterGroup.addLayers(markers);
    const fcEl = document.getElementById('filtered-count');
    if (fcEl) fcEl.innerText = `${airports.length} visible`;

    renderRouteLines(airports);
}

/* ================= FLIGHT CORRIDOR (ALT + CLICK) LOGIC ================= */

let flightCorridorArrivalAirport = null;
let flightCorridorLayerGroup = L.layerGroup();

function getHaversineDistanceKm(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function getGreatCircleInterpolatedPoint(lat1, lon1, lat2, lon2, f) {
    const rLat1 = lat1 * Math.PI / 180;
    let rLon1 = lon1 * Math.PI / 180;
    const rLat2 = lat2 * Math.PI / 180;
    let rLon2 = lon2 * Math.PI / 180;

    // Handle Antimeridian Longitude Wrapping (-180 / +180) for Transpacific & Transpolar routes
    let dlon = rLon2 - rLon1;
    if (dlon > Math.PI) {
        rLon2 -= 2 * Math.PI;
    } else if (dlon < -Math.PI) {
        rLon2 += 2 * Math.PI;
    }

    const d = 2 * Math.asin(Math.sqrt(
        Math.pow(Math.sin((rLat1 - rLat2) / 2), 2) +
        Math.cos(rLat1) * Math.cos(rLat2) * Math.pow(Math.sin((rLon2 - rLon1) / 2), 2)
    ));

    if (d === 0) return [lat1, lon1];

    const A = Math.sin((1 - f) * d) / Math.sin(d);
    const B = Math.sin(f * d) / Math.sin(d);

    const x = A * Math.cos(rLat1) * Math.cos(rLon1) + B * Math.cos(rLat2) * Math.cos(rLon2);
    const y = A * Math.cos(rLat1) * Math.sin(rLon1) + B * Math.cos(rLat2) * Math.sin(rLon2);
    const z = A * Math.sin(rLat1) + B * Math.sin(rLat2);

    let lat = Math.atan2(z, Math.sqrt(x * x + y * y)) * 180 / Math.PI;
    let lon = Math.atan2(y, x) * 180 / Math.PI;

    // North Atlantic Track Arc Curve (NAT Bias) for Europe <-> North America flights (Iceland/Greenland)
    const isTransatlantic = (
        ((lon1 > -15 && lon1 < 35 && lat1 > 35) && (lon2 < -50 && lat2 > 25)) ||
        ((lon2 > -15 && lon2 < 35 && lat2 > 35) && (lon1 < -50 && lat1 > 25))
    );

    if (isTransatlantic) {
        lat += 4.8 * Math.sin(f * Math.PI);
    }

    return [lat, lon];
}

function makeContinuousLongitudePoints(points) {
    if (!points || points.length === 0) return points;
    const result = [[points[0][0], points[0][1]]];
    for (let i = 1; i < points.length; i++) {
        let lat = points[i][0];
        let lon = points[i][1];
        const prevLon = result[i - 1][1];

        while (lon - prevLon > 180.0) {
            lon -= 360.0;
        }
        while (lon - prevLon < -180.0) {
            lon += 360.0;
        }
        result.push([lat, lon]);
    }
    return result;
}

function getCommercialFlightCorridorWaypoints(depAp, arrAp) {
    const lat1 = depAp.lat;
    const lon1 = depAp.lon;
    const lat2 = arrAp.lat;
    const lon2 = arrAp.lon;

    const rawPath = [];
    const numPts = 80;

    for (let i = 0; i <= numPts; i++) {
        const f = i / numPts;
        let [ptLat, ptLon] = getGreatCircleInterpolatedPoint(lat1, lon1, lat2, lon2, f);
        if (ptLat > 75.0) ptLat = 75.0; // Cap latitude at 75° N to prevent top edge map clipping
        rawPath.push([ptLat, ptLon]);
    }

    return makeContinuousLongitudePoints(rawPath);
}

function getCommercialCorridorFilterPoints(depAp, arrAp) {
    const lat1 = depAp.lat;
    const lon1 = depAp.lon;
    const lat2 = arrAp.lat;
    const lon2 = arrAp.lon;

    const isUSEastToAsia = (
        ((lon1 < -60 && lat1 > 25) && (lon2 > 60 && lon2 < 140)) ||
        ((lon2 < -60 && lat2 > 25) && (lon1 > 60 && lon1 < 140))
    );

    const isEuropeToAsia = (
        ((lon1 > -15 && lon1 < 35 && lat1 > 35) && (lon2 > 80 && lon2 < 140 && lat2 < 35)) ||
        ((lon2 > -15 && lon2 < 35 && lat2 > 35) && (lon1 > 80 && lon1 < 140 && lat1 < 35))
    );

    const filterWaypoints = [];

    // 1. Commercial US East Coast <-> SE Asia / Far East via NOPAC Alaska & Japan Corridor
    if (isUSEastToAsia) {
        const isDepUS = lon1 < -60;
        const usAp = isDepUS ? depAp : arrAp;
        const asiaAp = isDepUS ? arrAp : depAp;

        const waypoints = [
            [usAp.lat, usAp.lon],
            [56.0, -112.0],   // Canada (Edmonton / Alberta)
            [61.17, -149.99], // Alaska (Anchorage PANC)
            [48.0, 162.0],    // Aleutian Islands / NOPAC Track
            [35.77, 140.39],  // Japan (Tokyo RJTT)
            [22.31, 113.91],  // Hong Kong / Taiwan
            [asiaAp.lat, asiaAp.lon]
        ];

        if (!isDepUS) waypoints.reverse();

        for (let i = 0; i < waypoints.length - 1; i++) {
            const w1 = waypoints[i];
            const w2 = waypoints[i + 1];
            const segPts = createBezierArcPoints(w1[0], w1[1], w2[0], w2[1], 15);
            filterWaypoints.push(...segPts);
        }
    } else if (isEuropeToAsia) {
        // 2. Commercial Europe <-> South East Asia via Silk Road / Middle East Corridor
        const isDepEU = lon1 < 35;
        const euAp = isDepEU ? depAp : arrAp;
        const asiaAp = isDepEU ? arrAp : depAp;

        const waypoints = [
            [euAp.lat, euAp.lon],
            [41.0, 29.0],    // Turkey (Istanbul)
            [25.25, 55.36],  // Middle East (Dubai)
            [19.07, 72.87],  // India (Mumbai)
            [13.69, 100.75], // Thailand (Bangkok)
            [asiaAp.lat, asiaAp.lon]
        ];

        if (!isDepEU) waypoints.reverse();

        for (let i = 0; i < waypoints.length - 1; i++) {
            const w1 = waypoints[i];
            const w2 = waypoints[i + 1];
            const segPts = createBezierArcPoints(w1[0], w1[1], w2[0], w2[1], 15);
            filterWaypoints.push(...segPts);
        }
    } else {
        // 3. Standard Spherical Great Circle (Orthodromic / NAT Track) for all other flights
        const numPts = 80;
        for (let i = 0; i <= numPts; i++) {
            const f = i / numPts;
            let [ptLat, ptLon] = getGreatCircleInterpolatedPoint(lat1, lon1, lat2, lon2, f);
            filterWaypoints.push([ptLat, ptLon]);
        }
    }

    return filterWaypoints;
}

function isAirportInCorridor(ap, depAp, arrAp) {
    if (!ap || !depAp || !arrAp || !ap.lat || !ap.lon) return false;
    if (ap.icao === depAp.icao || ap.icao === arrAp.icao) return true;

    const totalDist = getHaversineDistanceKm(depAp.lat, depAp.lon, arrAp.lat, arrAp.lon);
    if (totalDist === 0) return false;

    // Dynamic corridor width: 300 km for regional, 750 km for long-haul routes to match real-world commercial flight paths
    const maxDistKm = totalDist > 1500 ? 750 : 300;
    const filterWaypoints = getCommercialCorridorFilterPoints(depAp, arrAp);

    for (const p of filterWaypoints) {
        const distToPath = getHaversineDistanceKm(ap.lat, ap.lon, p[0], p[1]);
        if (distToPath <= maxDistKm) {
            return true;
        }
    }
    return false;
}

function setArrivalAirportCorridor(arrAp) {
    if (!selectedAirport) {
        showToast('Click an Airport first (Departure), then Alt+Click an Arrival airport.', 'warning');
        return;
    }

    if (selectedAirport.icao === arrAp.icao) {
        clearFlightCorridor();
        showToast('Flight corridor cleared', 'info');
        return;
    }

    flightCorridorArrivalAirport = arrAp;
    renderFlightCorridor();
}

function clearFlightCorridor() {
    flightCorridorArrivalAirport = null;
    if (flightCorridorLayerGroup && map) {
        flightCorridorLayerGroup.clearLayers();
    }
    filterAirports();
}

function renderFlightCorridor() {
    if (!map || !selectedAirport || !flightCorridorArrivalAirport) return;

    if (!map.hasLayer(flightCorridorLayerGroup)) {
        map.addLayer(flightCorridorLayerGroup);
    }
    flightCorridorLayerGroup.clearLayers();

    const dep = selectedAirport;
    const arr = flightCorridorArrivalAirport;

    const distKm = getHaversineDistanceKm(dep.lat, dep.lon, arr.lat, arr.lon);
    const distNm = Math.round(distKm * 0.539957);

    // Generate commercial flight corridor waypoints (NOPAC Pacific / Silk Road / NAT Tracks)
    const arcPts = getCommercialFlightCorridorWaypoints(dep, arr);

    // Glowing Neon Flight Corridor Line
    const corridorLine = L.polyline(arcPts, {
        color: '#a855f7',
        weight: 4,
        dashArray: '10, 8',
        opacity: 0.95
    });

    flightCorridorLayerGroup.addLayer(corridorLine);

    // Filter airports to display only sceneries/airports inside corridor
    filterAirports();

    // Count custom sceneries along corridor
    const customCount = currentlyFilteredAirports.filter(a => hasCustomAddonSources(a)).length;

    const isTransoceanic = distKm > 2000;
    const trackLabel = isTransoceanic ? 'Commercial Long-Haul Route' : 'Orthodromic Track';

    showToast(`✈ Flight Corridor (${trackLabel}): ${dep.icao} → ${arr.icao} (${distNm.toLocaleString()} NM / ${Math.round(distKm).toLocaleString()} km) | ${customCount} Custom Sceneries En-Route`, 'success');

    // Smoothly zoom map to fit both departure & arrival airports
    map.fitBounds(arcPts, { padding: [60, 60], animate: true });
}

function createBezierArcPoints(lat1, lon1, lat2, lon2, numPoints = 30) {
    let targetLon2 = lon2;
    while (targetLon2 - lon1 > 180.0) targetLon2 -= 360.0;
    while (targetLon2 - lon1 < -180.0) targetLon2 += 360.0;

    const dLat = lat2 - lat1;
    const dLon = targetLon2 - lon1;
    const dist = Math.sqrt(dLat * dLat + dLon * dLon);
    if (dist === 0) return [[lat1, lon1]];

    // Perpendicular vector for smooth concave arc (standard aviation map convention)
    const normLat = dLon / dist;
    const normLon = -dLat / dist;
    const curvature = Math.min(dist * 0.18, 10.0);

    const ctrlLat = (lat1 + lat2) / 2 + normLat * curvature;
    const ctrlLon = (lon1 + targetLon2) / 2 + normLon * curvature;

    const points = [];
    for (let i = 0; i <= numPoints; i++) {
        const t = i / numPoints;
        const oneMinusT = 1 - t;
        const lat = oneMinusT * oneMinusT * lat1 + 2 * oneMinusT * t * ctrlLat + t * t * lat2;
        const lon = oneMinusT * oneMinusT * lon1 + 2 * oneMinusT * t * ctrlLon + t * t * targetLon2;
        points.push([lat, lon]);
    }
    return points;
}

function renderRouteLines(filteredAirports) {
    if (!map) return;
    if (!activeRouteLinesGroup) {
        activeRouteLinesGroup = L.layerGroup().addTo(map);
    } else {
        if (!map.hasLayer(activeRouteLinesGroup)) {
            map.addLayer(activeRouteLinesGroup);
        }
        activeRouteLinesGroup.clearLayers();
    }

    if (selectedAirlines.size === 0 || !activeRouteOrigin || !activeRouteOrigin.lat || !activeRouteOrigin.lon) {
        return;
    }

    const originLat = parseFloat(activeRouteOrigin.lat);
    const originLon = parseFloat(activeRouteOrigin.lon);

    // Collect all destination ICAOs across all selected active airlines at origin airport
    const allDestIcaos = new Set();
    selectedAirlines.forEach(al => {
        const dests = (activeRouteOrigin.routes && activeRouteOrigin.routes[al]) || [];
        dests.forEach(d => allDestIcaos.add(d));
    });

    allDestIcaos.forEach(destIcao => {
        if (destIcao === activeRouteOrigin.icao) return;
        
        let ap = allAirportsData.find(a => a.icao === destIcao);
        if (!ap && window.worldAirportCoords && window.worldAirportCoords[destIcao]) {
            const wInfo = window.worldAirportCoords[destIcao];
            ap = {
                icao: destIcao,
                lat: wInfo.lat,
                lon: wInfo.lon,
                name: wInfo.name,
                country: wInfo.country,
                pricing_type: 'Default',
                is_default: true
            };
        }

        if (!ap || !ap.lat || !ap.lon) return;

        const cat = getAirportCategory(ap);
        let lineColor = '#38bdf8';
        let lineWeight = 2.8;
        let lineOpacity = 0.95;
        let lineDashArray = null;

        if (cat === 'DEFAULT') {
            // Fine subtle gray dashed line for Default MSFS destination airports
            lineColor = '#94a3b8';  // Bright Slate Gray
            lineWeight = 1.8;       // Fine thin line
            lineOpacity = 0.75;     // Subtle & elegant
            lineDashArray = '4, 4'; // Discrete dashed line
        } else if (cat === 'PAYWARE') {
            lineColor = '#c084fc';  // Vibrant Purple (Payware Addon)
            lineWeight = 3.0;
            lineOpacity = 0.95;
        } else if (cat === 'ASOBO') {
            lineColor = '#fbbf24';  // Vibrant Amber/Gold (Asobo Official Handcrafted)
            lineWeight = 3.0;
            lineOpacity = 0.95;
        } else if (cat === 'FREEWARE') {
            lineColor = '#22d3ee';  // Vibrant Cyan (Freeware Addon)
            lineWeight = 3.0;
            lineOpacity = 0.95;
        }

        const destLat = parseFloat(ap.lat);
        const destLon = parseFloat(ap.lon);

        const arcPoints = createBezierArcPoints(originLat, originLon, destLat, destLon, 35);

        const routeLineOptions = {
            color: lineColor,
            weight: lineWeight,
            opacity: lineOpacity,
            smoothFactor: 1
        };
        if (lineDashArray) {
            routeLineOptions.dashArray = lineDashArray;
        }

        const routeLine = L.polyline(arcPoints, routeLineOptions);
        activeRouteLinesGroup.addLayer(routeLine);
        if (routeLine.bringToFront) {
            try { routeLine.bringToFront(); } catch (e) {}
        }
    });
}

function selectAirport(icao) {
    const ap = allAirportsData.find(a => a.icao === icao);
    if (ap) {
        focusAirportWithAnimation(ap);
    }
}

function focusAirportWithAnimation(ap) {
    if (!ap) return;
    lastFocusedIcao = ap.icao;

    if (map && ap.lat && ap.lon) {
        map.flyTo([ap.lat, ap.lon], 14, {
            animate: true,
            duration: 1.5
        });
        showAirportDetails(ap);
    }
}

function showAirportDetails(ap) {
    activeDrawerMode = 'AIRPORT';
    selectedAirport = ap;

    const sb = document.getElementById('sidebar-panel');
    if (sb) sb.classList.remove('-ml-80', 'opacity-0', 'pointer-events-none');

    const cMode = document.getElementById('drawer-country-mode');
    if (cMode) cMode.classList.add('hidden');
    const apMode = document.getElementById('drawer-airport-mode');
    if (apMode) apMode.classList.remove('hidden');
    const drawer = document.getElementById('detail-drawer');
    if (drawer) drawer.classList.remove('translate-x-full');

    document.getElementById('drawer-icao').innerText = ap.icao;
    document.getElementById('drawer-iata').innerText = ap.iata ? ap.iata : '—';
    document.getElementById('drawer-name').innerText = ap.name;
    document.getElementById('drawer-city-country').innerText = `${ap.city || 'Unknown City'}, ${ap.country || 'Unknown Country'}`;

    document.getElementById('drawer-lat').innerText = ap.lat ? ap.lat.toFixed(4) : '0.0000';
    document.getElementById('drawer-lon').innerText = ap.lon ? ap.lon.toFixed(4) : '0.0000';
    
    const elevFt = ap.elevation !== undefined ? ap.elevation : 0;
    const elevM = Math.round(elevFt * 0.3048);
    document.getElementById('drawer-elevation').innerText = `${elevFt.toLocaleString()} ft (${elevM} m)`;
    
    document.getElementById('drawer-vendor').innerText = ap.vendor || (ap.is_asobo_official ? 'Microsoft / Asobo' : 'Unknown');
    const versionBadge = document.getElementById('drawer-version');
    if (versionBadge) {
        if (ap.version) {
            versionBadge.innerText = ap.version;
            versionBadge.classList.remove('hidden');
        } else {
            versionBadge.classList.add('hidden');
        }
    }

    const icaoEl = document.getElementById('drawer-icao');
    const vendorEl = document.getElementById('drawer-vendor');
    const typeBadge = document.getElementById('drawer-type-badge');
    const pricingBadge = document.getElementById('drawer-pricing-badge');

    const cat = getAirportCategory(ap);
    const hasActiveFix = (ap.all_sources || []).some(s => !s.is_disabled && (s.is_fix_patch || (s.folder_name && (s.folder_name.toLowerCase().includes('fix') || s.folder_name.toLowerCase().includes('patch')))));

    // Clean previous category color classes
    const categoryColorClasses = [
        'text-purple-400', 'text-cyan-400', 'text-amber-400', 'text-blue-400',
        'drop-shadow-[0_0_10px_rgba(192,132,252,0.3)]',
        'drop-shadow-[0_0_10px_rgba(56,189,248,0.3)]',
        'drop-shadow-[0_0_10px_rgba(245,158,11,0.3)]',
        'drop-shadow-[0_0_10px_rgba(59,130,246,0.3)]'
    ];
    if (icaoEl) icaoEl.classList.remove(...categoryColorClasses);
    if (vendorEl) vendorEl.classList.remove(...categoryColorClasses);
    if (typeBadge) typeBadge.classList.remove(...categoryColorClasses);

    if (cat === 'DEFAULT') {
        pricingBadge.innerText = "Default MSFS";
        pricingBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30";
        if (icaoEl) icaoEl.classList.add('text-blue-400', 'drop-shadow-[0_0_10px_rgba(59,130,246,0.3)]');
        if (vendorEl) vendorEl.classList.add('text-blue-400', 'drop-shadow-[0_0_10px_rgba(59,130,246,0.3)]');
        if (typeBadge) typeBadge.classList.add('text-blue-400');
    } else if (cat === 'ASOBO') {
        pricingBadge.innerText = hasActiveFix ? "Asobo + Fix" : "Asobo";
        pricingBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30";
        if (icaoEl) icaoEl.classList.add('text-amber-400', 'drop-shadow-[0_0_10px_rgba(245,158,11,0.3)]');
        if (vendorEl) vendorEl.classList.add('text-amber-400', 'drop-shadow-[0_0_10px_rgba(245,158,11,0.3)]');
        if (typeBadge) typeBadge.classList.add('text-amber-400');
    } else if (cat === 'PAYWARE') {
        pricingBadge.innerText = "Payware Addon";
        pricingBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-purple-500/20 text-purple-400 border border-purple-500/30";
        if (icaoEl) icaoEl.classList.add('text-purple-400', 'drop-shadow-[0_0_10px_rgba(192,132,252,0.3)]');
        if (vendorEl) vendorEl.classList.add('text-purple-400', 'drop-shadow-[0_0_10px_rgba(192,132,252,0.3)]');
        if (typeBadge) typeBadge.classList.add('text-purple-400');
    } else {
        pricingBadge.innerText = "Freeware";
        pricingBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30";
        if (icaoEl) icaoEl.classList.add('text-cyan-400', 'drop-shadow-[0_0_10px_rgba(56,189,248,0.3)]');
        if (vendorEl) vendorEl.classList.add('text-cyan-400', 'drop-shadow-[0_0_10px_rgba(56,189,248,0.3)]');
        if (typeBadge) typeBadge.classList.add('text-cyan-400');
    }

    if (typeBadge) typeBadge.innerText = ap.english_type || ap.type;

    // Update Activation Status Card in Drawer & Developer Info Visibility
    const actBadge = document.getElementById('drawer-activation-badge');
    const devBlockEl = document.getElementById('drawer-dev-block');
    const allSourcesDisabled = ap.all_sources && ap.all_sources.length > 0 && ap.all_sources.every(s => s.is_disabled);
    const isFallbackDefault = ap.is_disabled || allSourcesDisabled || cat === 'DEFAULT';

    if (actBadge) {
        if (isFallbackDefault) {
            actBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/40";
            actBadge.innerText = "Default MSFS Airport";
        } else if (cat === 'ASOBO') {
            actBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40";
            actBadge.innerText = ap.world_update_name || "Asobo Sim Update";
        } else if (cat === 'PAYWARE') {
            actBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40";
            actBadge.innerText = "Payware Addon";
        } else {
            actBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40";
            actBadge.innerText = "Freeware Addon";
        }
    }

    // Pricing category override toggle logic (Payware vs Freeware for 3rd party sceneries)
    const toggleContainer = document.getElementById('drawer-pricing-toggle-container');
    const btnPayware = document.getElementById('btn-override-payware');
    const btnFreeware = document.getElementById('btn-override-freeware');

    if (toggleContainer) {
        if (isFallbackDefault || cat === 'ASOBO' || ap.is_asobo_official) {
            toggleContainer.classList.add('hidden');
            toggleContainer.classList.remove('flex');
        } else {
            toggleContainer.classList.remove('hidden');
            toggleContainer.classList.add('flex');

            const isCurrentPayware = (cat === 'PAYWARE');
            if (btnPayware) {
                btnPayware.className = isCurrentPayware
                    ? "px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-sm cursor-pointer"
                    : "px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all text-slate-500 hover:text-slate-300 cursor-pointer";
            }
            if (btnFreeware) {
                btnFreeware.className = !isCurrentPayware
                    ? "px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm cursor-pointer"
                    : "px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all text-slate-500 hover:text-slate-300 cursor-pointer";
            }
        }
    }

    const checkUpdateBtn = document.getElementById('btn-check-update');
    if (checkUpdateBtn) {
        if (cat === 'ASOBO' || isFallbackDefault || ap.is_asobo_official || (ap.vendor && (ap.vendor.includes('Asobo') || ap.vendor.includes('Microsoft')))) {
            checkUpdateBtn.classList.add('hidden');
        } else {
            checkUpdateBtn.classList.remove('hidden');
        }
    }

    // Price override card logic
    const priceCard = document.getElementById('drawer-price-card');
    if (cat === 'PAYWARE') {
        priceCard.classList.remove('hidden');
        const currSym = CURRENCY_SYMBOLS[selectedCurrency] || '€';
        document.getElementById('drawer-price-curr-symbol').innerText = currSym;

        const pValEur = ap.price_eur || 0;
        const formattedP = formatCurrency(pValEur);
        
        let tagText = "";
        if (ap.is_custom_price) {
            tagText = `Paid: ${formattedP} (Custom)`;
        } else if (ap.is_bundle || ap.bundle_total_price) {
            const bTotalFormatted = formatCurrency(ap.bundle_total_price || 39.00);
            const apCount = ap.bundle_airport_count || 'several';
            tagText = `Bundle Pack: ${bTotalFormatted} (${apCount} airports, ~${formattedP}/ap)`;
        } else {
            tagText = `Est: ~${formattedP}`;
        }
        document.getElementById('drawer-price-tag').innerText = tagText;

        const rate = CURRENCY_RATES[selectedCurrency] || 1.0;
        const valConverted = pValEur * rate;
        document.getElementById('drawer-price-input').value = ap.is_custom_price ? valConverted.toFixed(2) : '';
    } else {
        priceCard.classList.add('hidden');
    }

    // GSX Profile Card Logic
    const gsxBadge = document.getElementById('drawer-gsx-badge');
    const gsxContainer = document.getElementById('drawer-gsx-container');

    if (gsxBadge && gsxContainer) {
        if (ap.has_gsx_profile) {
            gsxBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
            gsxBadge.innerText = "Profile Installed";
            const safeGsxPath = encodeURIComponent(ap.gsx_profile_path || '');
            gsxContainer.innerHTML = `
                <div class="space-y-2.5">
                    <div onclick="openGsxProfileInExplorer(decodeURIComponent('${safeGsxPath}'))" 
                         class="p-3 rounded-xl bg-slate-950/80 hover:bg-slate-800/80 border border-slate-800/80 hover:border-cyan-500/50 cursor-pointer flex items-center justify-between gap-2 text-xs lg:text-sm font-mono font-bold text-slate-100 hover:text-cyan-300 transition-all group shadow-sm"
                         title="Click to reveal GSX INI file in Explorer">
                        <span class="truncate">${ap.gsx_profile_filename}</span>
                        <i class="fa-solid fa-folder-open text-cyan-400 text-sm group-hover:scale-110 transition-transform"></i>
                    </div>
                    <div ondragover="handleGsxDragOver(event)" ondragleave="handleGsxDragLeave(event)" ondrop="handleGsxDrop(event)"
                         onclick="triggerInstallGsxProfile()"
                         class="p-3.5 rounded-xl bg-slate-950/40 border-2 border-dashed border-slate-800 hover:border-cyan-500/50 flex flex-col items-center justify-center gap-1.5 text-center transition-all cursor-pointer group">
                        <i class="fa-solid fa-file-arrow-up text-cyan-400 text-lg group-hover:scale-110 transition-transform"></i>
                        <span class="text-xs lg:text-sm font-extrabold text-cyan-300 group-hover:text-cyan-200">Drop downloaded .zip or .ini here to replace</span>
                        <span class="text-xs text-slate-400">or click to browse & replace directly</span>
                    </div>
                </div>
            `;
        } else {
            gsxBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-slate-800 text-slate-400 border border-slate-700";
            gsxBadge.innerText = "No Profile";
            gsxContainer.innerHTML = `
                <div class="space-y-2.5">
                    <button onclick="triggerSearchGsxProfile()" 
                            class="w-full p-3 rounded-xl bg-slate-950/40 hover:bg-cyan-500/10 border border-slate-800/50 hover:border-cyan-500/40 text-slate-200 hover:text-cyan-300 text-xs lg:text-sm font-bold transition-all flex items-center justify-center gap-2 shadow-sm cursor-pointer">
                        <i class="fa-solid fa-magnifying-glass text-cyan-400 text-xs"></i>
                        <span>Search GSX Profile on Flightsim.to</span>
                    </button>
                    <div ondragover="handleGsxDragOver(event)" ondragleave="handleGsxDragLeave(event)" ondrop="handleGsxDrop(event)"
                         onclick="triggerInstallGsxProfile()"
                         class="p-3.5 rounded-xl bg-slate-950/40 border-2 border-dashed border-slate-800 hover:border-cyan-500/50 flex flex-col items-center justify-center gap-1.5 text-center transition-all cursor-pointer group">
                        <i class="fa-solid fa-file-arrow-up text-cyan-400 text-lg group-hover:scale-110 transition-transform"></i>
                        <span class="text-xs lg:text-sm font-extrabold text-cyan-300 group-hover:text-cyan-200">Drop downloaded .zip or .ini here</span>
                        <span class="text-xs text-slate-400">or click to browse & install directly</span>
                    </div>
                </div>
            `;
        }
    }

    // Render Operating Airlines Card (Simple Clean Text Badges, in English - Alphabetical & Interactive)
    const airlinesListEl = document.getElementById('drawer-airlines-list');
    const airlinesCountEl = document.getElementById('drawer-airlines-count');
    if (airlinesListEl && airlinesCountEl) {
        const airlines = (ap.operating_airlines || []).slice().sort((a, b) => a.localeCompare(b));
        if (airlines.length > 0) {
            airlinesCountEl.innerText = `${airlines.length} Airlines`;
            airlinesListEl.innerHTML = airlines.map(al => {
                const isActive = selectedAirlines.has(al) && (activeRouteOrigin && activeRouteOrigin.icao === ap.icao);
                const activeClass = isActive 
                    ? 'bg-cyan-500/25 text-cyan-300 border-cyan-400 shadow-[0_0_12px_rgba(56,189,248,0.4)] scale-105 font-bold' 
                    : 'bg-slate-950 text-slate-200 border-slate-800/80 hover:border-cyan-500/50 hover:text-cyan-300';
                const safeAl = al.replace(/'/g, "\\'");
                const safeAttrAl = al.replace(/"/g, '&quot;');
                const dests = (ap.routes && ap.routes[al]) ? ap.routes[al].length : 0;
                const tooltipText = dests > 0 ? `Show ${dests} direct flight connections from ${ap.icao} on ${al}` : `Filter map by ${al}`;
                return `<button data-airline="${safeAttrAl}" onclick="filterByAirline('${safeAl}', this)" 
                                class="text-xs font-semibold px-2.5 py-1 rounded-lg border transition-all cursor-pointer shadow-sm ${activeClass}" 
                                title="${tooltipText}">
                            ${al}
                        </button>`;
            }).join('');
        } else {
            airlinesCountEl.innerText = `0 Airlines`;
            airlinesListEl.innerHTML = `<span class="text-xs text-slate-500 italic">No scheduled airlines data available for this airport.</span>`;
        }
    }

    // Render rating widget for this airport
    renderStarRatingWidget(ap.rating || 0);

    // Conflict Alert Banner
    const conflictContainer = document.getElementById('drawer-conflict-banner');
    if (conflictContainer) {
        if (ap.has_conflict) {
            conflictContainer.innerHTML = `
                <div class="p-3.5 rounded-2xl bg-red-500/15 border border-red-500/40 text-red-300 space-y-1">
                    <div class="flex items-center gap-2 font-bold text-xs">
                        <i class="fa-solid fa-triangle-exclamation text-red-400"></i>
                        <span>SCENERY CONFLICT DETECTED</span>
                    </div>
                    <p class="text-[11px] text-red-200/90 leading-relaxed">
                        ${ap.conflict_count} active main sceneries are installed for ${ap.icao}. You can disable one below to avoid sim overlaps!
                    </p>
                </div>
            `;
            conflictContainer.classList.remove('hidden');
        } else {
            conflictContainer.classList.add('hidden');
        }
    }

    const sourcesContainer = document.getElementById('drawer-sources-list');
    sourcesContainer.innerHTML = '';

    const sources = ap.all_sources || [];
    const nonDefaultSources = sources.filter(s => !(s.pricing_type === 'Default' || (s.folder_name && s.folder_name.startsWith('msfs-default-'))));
    
    // Separate into Main Base Sceneries vs Stackable Fixes/Patches
    const baseSources = nonDefaultSources.filter(s => !s.is_fix_patch);
    const fixSources = nonDefaultSources.filter(s => !!s.is_fix_patch);

    const isDefaultActive = (ap.pricing_type === 'Default' || ap.package_name === 'Default MSFS Base Airport' || baseSources.length === 0 || baseSources.every(s => s.is_disabled));

    let html = `
        <div class="space-y-3">
            <div class="flex items-center justify-between pb-1">
                <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Available Scenery Options</span>
                <span class="text-[10px] font-mono text-slate-500 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">1-Click Selection</span>
            </div>
            <div class="space-y-2.5">
    `;

    // CHOICE 1: Default MSFS Base Airport Card
    if (isDefaultActive) {
        html += `
            <div class="p-3.5 rounded-xl border-2 border-blue-500/80 bg-blue-500/10 shadow-lg shadow-blue-500/10 transition-all space-y-1">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <i class="fa-solid fa-circle-dot text-blue-400 text-sm"></i>
                        <span class="text-xs font-bold text-blue-200">Default MSFS Base Airport</span>
                    </div>
                    <span class="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/40">Active</span>
                </div>
                <p class="text-[11px] text-slate-400 pl-6">Built-in Procedural MSFS Base Scenery</p>
            </div>
        `;
    } else {
        html += `
            <div onclick="selectDefaultMSFSScenery('${ap.icao}')" class="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 hover:border-slate-700 cursor-pointer transition-all space-y-1 group">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <i class="fa-regular fa-circle text-slate-500 text-sm transition-colors"></i>
                        <span class="text-xs font-bold text-slate-300 group-hover:text-white transition-colors">Default MSFS Base Airport</span>
                    </div>
                    <span class="text-[10px] font-mono text-slate-500 group-hover:text-slate-300 shrink-0 whitespace-nowrap">Click to Activate</span>
                </div>

                <p class="text-[11px] text-slate-500 pl-6">Built-in Procedural MSFS Base Scenery</p>
            </div>
        `;
    }

    // CHOICE 2+: Installed Base Scenery Addons / World Updates
    baseSources.forEach((src) => {
        const idx = sources.indexOf(src);
        const isDisabled = !!src.is_disabled;
        const isActive = !isDisabled;
        const isAsoboPkg = (src.is_asobo_official || src.vendor === 'Microsoft / Asobo' || (src.folder_name && (src.folder_name.toLowerCase().includes('asobo-airport-') || src.folder_name.toLowerCase().includes('microsoft-airport-'))));

        const updateLabel = src.world_update_name || ap.world_update_name || "Asobo World Update";
        const titleLabel = isAsoboPkg ? updateLabel : (src.vendor && src.vendor !== 'Unknown' ? src.vendor : src.folder_name);
        const openBtnClass = 'px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-all shadow-sm shrink-0 whitespace-nowrap cursor-pointer';

        if (isActive) {
            let activeBorderClass = 'border-cyan-500/80 bg-cyan-500/10 shadow-cyan-500/10';
            let activeIconColor = 'text-cyan-400';
            let activeBadgeClass = 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40';

            if (isAsoboPkg) {
                activeBorderClass = 'border-amber-500/80 bg-amber-500/10 shadow-amber-500/10';
                activeIconColor = 'text-amber-400';
                activeBadgeClass = 'bg-amber-500/20 text-amber-300 border border-amber-500/40';
            } else if (src.pricing_type === 'Payware') {
                activeBorderClass = 'border-purple-500/80 bg-purple-500/10 shadow-purple-500/10';
                activeIconColor = 'text-purple-400';
                activeBadgeClass = 'bg-purple-500/20 text-purple-300 border border-purple-500/40';
            }

            html += `
                <div class="p-3.5 rounded-xl border-2 ${activeBorderClass} transition-all space-y-2.5">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2 min-w-0 flex-1">
                            <i class="fa-solid fa-circle-dot ${activeIconColor} text-sm shrink-0"></i>
                            <span class="text-xs font-bold text-white truncate min-w-0">${titleLabel}</span>
                        </div>
                        <span class="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full ${activeBadgeClass} shrink-0 whitespace-nowrap">Active</span>
                    </div>

                    <div class="text-[11px] font-mono text-slate-300 bg-slate-950/70 border border-slate-800 p-2 rounded-lg break-all">
                        ${src.folder_name}
                    </div>

                    <div class="flex items-center justify-between text-xs pt-0.5">
                        <span class="text-[11px] font-mono text-slate-400">${src.source_folder} ${src.size_str ? `• ${src.size_str}` : ''}</span>
                        <button onclick="openSpecificPackageFolderByIndex('${ap.icao}', ${idx})" class="${openBtnClass}" title="Open Folder">
                            <i class="fa-solid fa-folder-open text-cyan-400"></i> Open Folder
                        </button>
                    </div>
                </div>
            `;
        } else {
            const safePkgName = (src.folder_name || '').replace(/'/g, "\\'");
            html += `
                <div onclick="selectSceneryPackageByName('${ap.icao}', '${safePkgName}')" class="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 hover:border-slate-700 cursor-pointer transition-all space-y-2 group">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2 min-w-0 flex-1">
                            <i class="fa-regular fa-circle text-slate-500 text-sm transition-colors shrink-0"></i>
                            <span class="text-xs font-bold text-slate-300 group-hover:text-white truncate transition-colors min-w-0">${titleLabel}</span>
                        </div>
                        <span class="text-[10px] font-mono text-slate-500 group-hover:text-slate-300 shrink-0 whitespace-nowrap">Click to Activate</span>
                    </div>

                    <div class="text-[11px] font-mono text-slate-400 group-hover:text-slate-300 bg-slate-950/40 border border-slate-800/60 p-2 rounded-lg break-all transition-colors">
                        ${src.folder_name}
                    </div>

                    <div class="flex items-center justify-between text-xs pt-0.5 text-slate-500 font-mono text-[11px]">
                        <span>${src.source_folder} ${src.size_str ? `• ${src.size_str}` : ''}</span>
                    </div>
                </div>
            `;
        }
    });

    html += `</div></div>`;

    // SECTION 2: Available Fixes & Overlays (Stackable Independent Toggles)
    if (fixSources.length > 0) {
        html += `
            <div class="pt-4 border-t border-slate-800/80 space-y-3">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-bold uppercase tracking-wider text-slate-300">Available Fixes & Overlays</span>
                    </div>
                </div>
                <div class="space-y-2.5">
        `;

        fixSources.forEach((src) => {
            const idx = sources.indexOf(src);
            const isDisabled = !!src.is_disabled;
            const isActive = !isDisabled;
            const pkgPath = (src.folder_name || '').replace(/'/g, "\\'");
            const openBtnClass = 'px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-all shadow-sm shrink-0 whitespace-nowrap cursor-pointer';

            if (isActive) {
                html += `
                    <div onclick="toggleFixPatchPackage('${pkgPath}', '${ap.icao}')" class="p-3.5 rounded-xl border-2 border-emerald-500/80 bg-emerald-500/10 shadow-lg shadow-emerald-500/10 cursor-pointer transition-all space-y-2.5 group">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2 min-w-0 flex-1">
                                <i class="fa-solid fa-circle-dot text-emerald-400 text-sm shrink-0"></i>
                                <span class="text-xs font-bold text-white truncate min-w-0">${src.folder_name}</span>
                                <span class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shrink-0 whitespace-nowrap">Fix / Overlay</span>
                            </div>
                            <span class="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shrink-0 whitespace-nowrap">Active</span>
                        </div>

                        <div class="text-[11px] font-mono text-slate-300 bg-slate-950/70 border border-slate-800 p-2 rounded-lg break-all">
                            ${src.folder_name}
                        </div>

                        <div class="flex items-center justify-between text-xs pt-0.5">
                            <span class="text-[11px] font-mono text-slate-400">${src.source_folder} ${src.size_str ? `• ${src.size_str}` : ''}</span>
                            <button onclick="event.stopPropagation(); openSpecificPackageFolderByIndex('${ap.icao}', ${idx})" class="${openBtnClass}" title="Open Folder">
                                <i class="fa-solid fa-folder-open text-cyan-400"></i> Open Folder
                            </button>
                        </div>
                    </div>
                `;
            } else {
                html += `
                    <div onclick="toggleFixPatchPackage('${pkgPath}', '${ap.icao}')" class="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 hover:border-slate-700 cursor-pointer transition-all space-y-2 group">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2 min-w-0 flex-1">
                                <i class="fa-regular fa-circle text-slate-500 text-sm transition-colors shrink-0"></i>
                                <span class="text-xs font-bold text-slate-300 group-hover:text-white truncate transition-colors min-w-0">${src.folder_name}</span>
                                <span class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 shrink-0 whitespace-nowrap">Fix / Overlay</span>
                            </div>
                            <span class="text-[10px] font-mono text-slate-500 group-hover:text-slate-300 shrink-0 whitespace-nowrap">Click to Activate</span>
                        </div>

                        <div class="text-[11px] font-mono text-slate-400 group-hover:text-slate-300 bg-slate-950/40 border border-slate-800/60 p-2 rounded-lg break-all transition-colors">
                            ${src.folder_name}
                        </div>

                        <div class="flex items-center justify-between text-xs pt-0.5 text-slate-500 font-mono text-[11px]">
                            <span>${src.source_folder} ${src.size_str ? `• ${src.size_str}` : ''}</span>
                        </div>
                    </div>
                `;
            }
        });

        html += `</div></div>`;
    }

    html += `</div>`;
    sourcesContainer.innerHTML = html;

    document.getElementById('detail-drawer').classList.remove('translate-x-full');
}

async function triggerCheckSceneryUpdate() {
    if (!selectedAirport) return;
    try {
        if (window.pywebview) {
            await window.pywebview.api.check_update(
                selectedAirport.icao,
                selectedAirport.name || '',
                selectedAirport.vendor || '',
                selectedAirport.version || '',
                selectedAirport.pricing_type || ''
            );
        }
    } catch (e) {
        console.error("Check update error:", e);
    }
}

async function resetCustomPriceForSelected() {
    if (!selectedAirport) return;
    document.getElementById('drawer-price-input').value = '';
    await saveCustomPriceForSelected();
}

async function saveCustomPriceForSelected() {
    if (!selectedAirport) return;
    const inputVal = document.getElementById('drawer-price-input').value;
    const rate = CURRENCY_RATES[selectedCurrency] || 1.0;

    let valInEur = null;
    if (inputVal !== '' && !isNaN(inputVal)) {
        valInEur = parseFloat(inputVal) / rate;
    }

    try {
        if (window.pywebview) {
            const resStr = await window.pywebview.api.set_custom_price(selectedAirport.icao, valInEur);
            const res = JSON.parse(resStr);
            if (res.status === 'ok') {
                allAirportsData = res.airports;
                allAirportsData.forEach(ap => {
                    if (userRatingsMap[ap.icao] !== undefined) {
                        ap.rating = userRatingsMap[ap.icao];
                    }
                });
                updateStats(allAirportsData);
                filterAirports();
                const updatedAp = allAirportsData.find(a => a.icao === selectedAirport.icao);
                if (updatedAp) showAirportDetails(updatedAp);
            }
        }
    } catch (e) {
        console.error("Failed to save custom price:", e);
    }
}

async function toggleUserCategoryOverride(newCategory) {
    if (!selectedAirport || !selectedAirport.icao || isToggleInProgress) return;
    isToggleInProgress = true;
    try {
        const icao = selectedAirport.icao;
        if (window.pywebview && window.pywebview.api && window.pywebview.api.set_user_category_override) {
            const resStr = await window.pywebview.api.set_user_category_override(icao, newCategory);
            const res = JSON.parse(resStr);
            if (res.status === 'ok') {
                allAirportsData = res.airports;
                allAirportsData.forEach(ap => {
                    if (userRatingsMap[ap.icao] !== undefined) {
                        ap.rating = userRatingsMap[ap.icao];
                    }
                    ap._searchKey = `${ap.icao} ${ap.name} ${ap.city || ''} ${ap.package_name || ''} ${ap.vendor || ''}`.toLowerCase();
                });
                updateStats(allAirportsData);
                filterAirports();
                const updatedAp = allAirportsData.find(a => a.icao === icao);
                if (updatedAp) showAirportDetails(updatedAp);
                showToast(`✓ Pricing model changed to ${newCategory} for ${icao}`, 'success');
            }
        }
    } catch (e) {
        console.error("Failed to set category override:", e);
    } finally {
        isToggleInProgress = false;
    }
}

async function toggleSpecificPackage(path, icao) {
    if (!window.pywebview || isToggleInProgress) return;
    isToggleInProgress = true;
    try {
        const resStr = await window.pywebview.api.toggle_package(path, icao || '');
        const res = JSON.parse(resStr);
        if (res.status === 'ok') {
            allAirportsData = res.airports;
            allAirportsData.forEach(ap => {
                if (userRatingsMap[ap.icao] !== undefined) {
                    ap.rating = userRatingsMap[ap.icao];
                }
            });
            updateStats(allAirportsData);
            filterAirports();
            if (selectedAirport) {
                const updatedAp = allAirportsData.find(a => a.icao === selectedAirport.icao);
                if (updatedAp) showAirportDetails(updatedAp);
            }
            showToast(`✓ ${icao || 'Scenery'} Activated & Saved to Disk`, 'success');
        }
    } catch (e) {
        console.error("Failed to toggle package:", e);
    } finally {
        isToggleInProgress = false;
    }
}

function showToast(message, type = 'success') {
    let toast = document.getElementById('sceneryx-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'sceneryx-toast';
        toast.className = 'fixed bottom-6 z-[9999] px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 border transition-all duration-300 transform translate-y-10 opacity-0 pointer-events-none font-semibold text-xs backdrop-blur-md';
        document.body.appendChild(toast);
    }
    
    const drawer = document.getElementById('detail-drawer');
    const isDrawerOpen = drawer && !drawer.classList.contains('translate-x-full');
    const rightPosClass = isDrawerOpen ? 'right-[440px]' : 'right-6';
    
    if (type === 'success') {
        toast.className = `fixed bottom-6 ${rightPosClass} z-[9999] px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 border border-emerald-500/50 bg-slate-900/95 text-emerald-300 transition-all duration-300 transform translate-y-0 opacity-100 shadow-emerald-500/20 backdrop-blur-md`;
        toast.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400 text-base"></i> <span>${message}</span>`;
    } else {
        toast.className = `fixed bottom-6 ${rightPosClass} z-[9999] px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 border border-cyan-500/50 bg-slate-900/95 text-cyan-300 transition-all duration-300 transform translate-y-0 opacity-100 shadow-cyan-500/20 backdrop-blur-md`;
        toast.innerHTML = `<i class="fa-solid fa-circle-info text-cyan-400 text-base"></i> <span>${message}</span>`;
    }
    
    setTimeout(() => {
        toast.classList.add('translate-y-10', 'opacity-0', 'pointer-events-none');
    }, 3000);
}

function openSpecificPackageFolder(path) {
    if (window.pywebview) {
        window.pywebview.api.open_folder(path);
    }
}

function openSpecificPackageFolderByIndex(icao, idx) {
    if (!selectedAirport || !selectedAirport.all_sources || !selectedAirport.all_sources[idx]) return;
    const src = selectedAirport.all_sources[idx];
    const path = src.package_path || src.folder_name;
    if (path) openSpecificPackageFolder(path);
}

async function selectDefaultMSFSScenery(icao) {
    if (!window.pywebview || isToggleInProgress || !icao) return;
    isToggleInProgress = true;
    try {
        const resStr = await window.pywebview.api.select_scenery_option(icao, 'DEFAULT');
        const res = JSON.parse(resStr);
        if (res.status === 'ok') {
            allAirportsData = res.airports;
            allAirportsData.forEach(ap => {
                if (userRatingsMap[ap.icao] !== undefined) {
                    ap.rating = userRatingsMap[ap.icao];
                }
            });
            updateStats(allAirportsData);
            const targetIcao = selectedAirport ? selectedAirport.icao : icao;
            const updatedAp = allAirportsData.find(a => a.icao === targetIcao);
            if (updatedAp) {
                selectedAirport = updatedAp;
                showAirportDetails(updatedAp);
            }
            filterAirports();
            showToast(`✓ Reverted to Default MSFS Base Airport`, 'info');
        }
    } catch (e) {
        console.error("Failed to select scenery option:", e);
    } finally {
        isToggleInProgress = false;
    }
}

async function selectSceneryPackageByName(icao, folderName) {
    if (!window.pywebview || isToggleInProgress || !icao || !folderName) return;
    isToggleInProgress = true;
    try {
        const resStr = await window.pywebview.api.select_scenery_option(icao, folderName);
        const res = JSON.parse(resStr);
        if (res.status === 'ok') {
            allAirportsData = res.airports;
            allAirportsData.forEach(ap => {
                if (userRatingsMap[ap.icao] !== undefined) {
                    ap.rating = userRatingsMap[ap.icao];
                }
            });
            updateStats(allAirportsData);
            const targetIcao = selectedAirport ? selectedAirport.icao : icao;
            const updatedAp = allAirportsData.find(a => a.icao === targetIcao);
            if (updatedAp) {
                selectedAirport = updatedAp;
                showAirportDetails(updatedAp);
            }
            filterAirports();
            showToast(`✓ ${icao} Scenery Activated & Saved to Disk`, 'success');
        }
    } catch (e) {
        console.error("Failed to select scenery option:", e);
    } finally {
        isToggleInProgress = false;
    }
}

async function toggleFixPatchPackage(path, icao) {
    if (!window.pywebview || isToggleInProgress || !path) return;
    isToggleInProgress = true;
    try {
        const resStr = await window.pywebview.api.toggle_fix_patch(path, icao || '');
        const res = JSON.parse(resStr);
        if (res.status === 'ok') {
            allAirportsData = res.airports;
            allAirportsData.forEach(ap => {
                if (userRatingsMap[ap.icao] !== undefined) {
                    ap.rating = userRatingsMap[ap.icao];
                }
            });
            updateStats(allAirportsData);
            filterAirports();
            if (selectedAirport) {
                const updatedAp = allAirportsData.find(a => a.icao === selectedAirport.icao);
                if (updatedAp) showAirportDetails(updatedAp);
            }
            const statusLabel = res.enabled ? 'Enabled' : 'Disabled';
            showToast(`✓ Fix / Overlay ${statusLabel} & Saved to Disk`, res.enabled ? 'success' : 'info');
        }
    } catch (e) {
        console.error("Failed to toggle fix/patch package:", e);
    } finally {
        isToggleInProgress = false;
    }
}

function exitCountryMode() {
    try {
        const prevCountryCode = selectedCountryCode;

        activeDrawerMode = 'MAP';
        selectedCountryCode = null;
        selectedCountryName = '';
        expandedCountryIcao = null;
        selectedAirport = null;

        // 1. Hide Country Mode & Airport Mode drawers, close drawer panel
        const cMode = document.getElementById('drawer-country-mode');
        if (cMode) cMode.classList.add('hidden');

        const apMode = document.getElementById('drawer-airport-mode');
        if (apMode) apMode.classList.add('hidden');

        const drawer = document.getElementById('detail-drawer');
        if (drawer) drawer.classList.add('translate-x-full');

        // 2. Slide Left Sidebar back into view
        const sb = document.getElementById('sidebar-panel');
        if (sb) sb.classList.remove('-ml-80', 'opacity-0', 'pointer-events-none');

        // 3. Reset Country Polygon Overlay on Leaflet map
        if (selectedCountryPolygonLayer) {
            map.removeLayer(selectedCountryPolygonLayer);
            selectedCountryPolygonLayer = null;
        }
        if (countryGeoJsonLayer) {
            try { countryGeoJsonLayer.resetStyle(); } catch (err) {}
            countryGeoJsonLayer.eachLayer(l => {
                if (l.setStyle) {
                    l.setStyle({
                        fillColor: '#06b6d4',
                        fillOpacity: 0.0,
                        color: '#475569',
                        weight: 0.5,
                        opacity: 0.3
                    });
                }
            });
        }

        // 4. Instantly remove and destroy any leftover toast element from DOM
        const statusEl = document.getElementById('country-filter-indicator');
        if (statusEl) statusEl.classList.add('hidden');

        const toast = document.getElementById('sceneryx-toast');
        if (toast) {
            try { toast.remove(); } catch(e) {}
        }

        // 5. Restore global sidebar filters to default map mode (Screenshot 2 & 3: Default MSFS unchecked)
        selectedPricing = new Set(DEFAULT_STARTUP_PRICING);
        selectedSources = new Set(ALL_SOURCES_LIST);
        selectedRegions.clear();
        selectedTypes = new Set(ALL_TYPES_LIST);
        selectedGsxFilter = 'all';
        updateFilterUI();
        filterAirports();

        // 6. Camera Zoom: Smoothly fly camera to the geographic region of the exited country
        if (prevCountryCode && map && typeof REGION_COUNTRY_MAP !== 'undefined') {
            let regionKey = null;
            for (const [rKey, isoList] of Object.entries(REGION_COUNTRY_MAP)) {
                if (isoList.includes(prevCountryCode)) {
                    regionKey = rKey;
                    break;
                }
            }
            if (regionKey && typeof REGION_VIEWPORTS !== 'undefined' && REGION_VIEWPORTS[regionKey]) {
                const vp = REGION_VIEWPORTS[regionKey];
                map.flyTo(vp.center, vp.zoom, { animate: true, duration: 1.2 });
            }
        }
    } catch (e) {
        console.error("Error in exitCountryMode:", e);
    }
}

function closeDrawer() {
    exitCountryMode();
}

/* ================= STAR RATING WIDGET LOGIC (AIRPORT DETAIL) ================= */

function renderStarRatingWidget(rating) {
    const container = document.getElementById('interactive-star-widget');
    const scoreDisplay = document.getElementById('rating-score-display');
    if (!container || !scoreDisplay) return;

    container.innerHTML = '';

    if (rating > 0) {
        scoreDisplay.innerText = `★ ${rating.toFixed(1)} / 5.0`;
        scoreDisplay.className = "text-xs font-mono font-bold text-amber-400";
    } else {
        scoreDisplay.innerText = "Unrated";
        scoreDisplay.className = "text-xs font-mono font-semibold text-slate-500";
    }

    for (let starIdx = 1; starIdx <= 5; starIdx++) {
        const starEl = document.createElement('i');
        starEl.className = 'fa-regular fa-star star-item';

        if (rating >= starIdx) {
            starEl.className = 'fa-solid fa-star star-item full';
        } else if (rating >= starIdx - 0.5) {
            starEl.className = 'fa-solid fa-star-half-stroke star-item full';
        } else {
            starEl.className = 'fa-regular fa-star star-item';
        }

        starEl.addEventListener('mousemove', (e) => handleStarMouseMove(e, starIdx));
        starEl.addEventListener('click', (e) => handleStarClick(e, starIdx));

        container.appendChild(starEl);
    }
}

function handleStarMouseMove(e, starIdx) {
    const rect = e.target.getBoundingClientRect();
    const isLeftHalf = (e.clientX - rect.left) < (rect.width / 2);
    const hoverVal = isLeftHalf ? (starIdx - 0.5) : starIdx;

    renderStarRatingWidgetPreview(hoverVal);
}

function renderStarRatingWidgetPreview(val) {
    const container = document.getElementById('interactive-star-widget');
    const scoreDisplay = document.getElementById('rating-score-display');
    if (!container || !scoreDisplay) return;

    const stars = container.querySelectorAll('.star-item');

    scoreDisplay.innerText = `★ ${val.toFixed(1)}+`;
    scoreDisplay.className = "text-xs font-mono font-bold text-amber-300 animate-pulse";

    stars.forEach((starEl, index) => {
        const starIdx = index + 1;
        if (val >= starIdx) {
            starEl.className = 'fa-solid fa-star star-item full';
        } else if (val >= starIdx - 0.5) {
            starEl.className = 'fa-solid fa-star-half-stroke star-item full';
        } else {
            starEl.className = 'fa-regular fa-star star-item';
        }
    });
}

function resetStarHover() {
    if (selectedAirport) {
        renderStarRatingWidget(selectedAirport.rating || 0);
    } else {
        renderStarRatingWidget(0);
    }
}

async function handleStarClick(e, starIdx) {
    if (!selectedAirport) return;

    const rect = e.target.getBoundingClientRect();
    const isLeftHalf = (e.clientX - rect.left) < (rect.width / 2);
    const ratingVal = isLeftHalf ? (starIdx - 0.5) : starIdx;

    selectedAirport.rating = ratingVal;
    userRatingsMap[selectedAirport.icao] = ratingVal;

    renderStarRatingWidget(ratingVal);

    try {
        if (window.pywebview) {
            await window.pywebview.api.set_rating(selectedAirport.icao, ratingVal);
        }
    } catch (err) {
        console.error("Failed to save rating:", err);
    }

    filterAirports();
}

async function clearCurrentRating() {
    if (!selectedAirport) return;

    selectedAirport.rating = 0;
    delete userRatingsMap[selectedAirport.icao];

    renderStarRatingWidget(0);

    try {
        if (window.pywebview) {
            await window.pywebview.api.set_rating(selectedAirport.icao, 0);
        }
    } catch (err) {
        console.error("Failed to clear rating:", err);
    }

    filterAirports();
}

/* ================= STAR RATING FILTER WIDGET (LEFT SIDEBAR) ================= */

function renderFilterStarWidget(val) {
    const container = document.getElementById('filter-star-widget');
    const display = document.getElementById('filter-rating-display');
    if (!container || !display) return;

    container.innerHTML = '';

    if (val > 0) {
        display.innerText = `★ ${val.toFixed(1)}+`;
        display.className = "text-xs font-mono font-bold text-amber-400";
    } else {
        display.innerText = "All (0.0★)";
        display.className = "text-xs font-mono font-bold text-cyan-400";
    }

    for (let starIdx = 1; starIdx <= 5; starIdx++) {
        const starEl = document.createElement('i');

        if (val >= starIdx) {
            starEl.className = 'fa-solid fa-star star-item full';
        } else if (val >= starIdx - 0.5) {
            starEl.className = 'fa-solid fa-star-half-stroke star-item full';
        } else {
            starEl.className = 'fa-regular fa-star star-item';
        }

        starEl.addEventListener('mousemove', (e) => handleFilterStarMouseMove(e, starIdx));
        starEl.addEventListener('click', (e) => handleFilterStarClick(e, starIdx));

        container.appendChild(starEl);
    }
}

function handleFilterStarMouseMove(e, starIdx) {
    const rect = e.target.getBoundingClientRect();
    const isLeftHalf = (e.clientX - rect.left) < (rect.width / 2);
    const hoverVal = isLeftHalf ? (starIdx - 0.5) : starIdx;

    renderFilterStarWidgetPreview(hoverVal);
}

function renderFilterStarWidgetPreview(val) {
    const container = document.getElementById('filter-star-widget');
    const display = document.getElementById('filter-rating-display');
    if (!container || !display) return;

    const stars = container.querySelectorAll('.star-item');

    display.innerText = `★ ${val.toFixed(1)}+`;
    display.className = "text-xs font-mono font-bold text-amber-300 animate-pulse";

    stars.forEach((starEl, index) => {
        const starIdx = index + 1;
        if (val >= starIdx) {
            starEl.className = 'fa-solid fa-star star-item full';
        } else if (val >= starIdx - 0.5) {
            starEl.className = 'fa-solid fa-star-half-stroke star-item full';
        } else {
            starEl.className = 'fa-regular fa-star star-item';
        }
    });
}

function resetFilterStarHover() {
    renderFilterStarWidget(selectedMinRating);
}

function handleFilterStarClick(e, starIdx) {
    const rect = e.target.getBoundingClientRect();
    const isLeftHalf = (e.clientX - rect.left) < (rect.width / 2);
    const val = isLeftHalf ? (starIdx - 0.5) : starIdx;

    if (selectedMinRating === val) {
        selectedMinRating = 0;
    } else {
        selectedMinRating = val;
    }

    renderFilterStarWidget(selectedMinRating);
    filterAirports();
}

function resetMinRatingFilter() {
    selectedMinRating = 0;
    renderFilterStarWidget(0);
    filterAirports();
}

function resetFullDatabase() {
    showCustomModal({
        title: 'Are you sure you want to reset?',
        message: 'This will re-activate all disabled MSFS scenery packages, reset custom pricing overrides, and perform a fresh scan of your Community & Official folders. All custom toggles and state overrides will be reset to default.',
        type: 'warning',
        confirmText: 'Yes, Reset All',
        cancelText: 'Cancel',
        showCancel: true,
        onConfirm: () => {
            closeSettingsModal();
            if (!window.pywebview) return;
            window.pywebview.api.reset_full_database().then(resStr => {
                try {
                    const res = JSON.parse(resStr);
                    if (res.status === 'success') {
                        allAirportsData = res.airports || [];
                        updateFlightModeBannerUI({ active: false, icaos: [] });
                        filterAirports();
                        showToast('✓ Database reset & freshly scanned', 'success');
                    }
                } catch(e){}
            });
        }
    });
}

/* ================= FILTER & UI LOGIC ================= */

let selectedRegions = new Set();

function toggleRegionFilter(regionKey) {
    if (regionKey === 'all') {
        selectedRegions.clear();
    } else {
        if (selectedRegions.has(regionKey)) {
            selectedRegions.delete(regionKey);
        } else {
            selectedRegions.add(regionKey);
        }
    }
    updateRegionPillUI();
    filterAirports();

    if (map) {
        if (selectedRegions.size === 1) {
            const singleKey = Array.from(selectedRegions)[0];
            const vp = REGION_VIEWPORTS[singleKey];
            if (vp) {
                map.flyTo(vp.center, vp.zoom, { duration: 1.2 });
            } else if (currentlyFilteredAirports.length > 0) {
                zoomToFilteredAirportsBounds();
            }
        } else if (selectedRegions.size > 1 && currentlyFilteredAirports.length > 0) {
            zoomToFilteredAirportsBounds();
        }
    }
}

function updateRegionPillUI() {
    const container = document.getElementById('region-pills-container');
    if (!container) return;

    const allBtn = document.getElementById('filter-region-all');
    if (allBtn) {
        if (selectedRegions.size === 0) {
            allBtn.className = "col-span-2 py-1.5 px-2 rounded-xl border text-[11px] font-semibold bg-cyan-500/20 text-cyan-300 border-cyan-500/40 transition-all text-center flex items-center justify-center shadow-sm shadow-cyan-500/10 cursor-pointer";
        } else {
            allBtn.className = "col-span-2 py-1.5 px-2 rounded-xl border text-[11px] font-semibold bg-slate-900/90 text-slate-400 border-slate-800 hover:border-slate-700 transition-all text-center flex items-center justify-center cursor-pointer";
        }
    }

    const keys = ['weurope', 'eeurope', 'namerica', 'camerica_caribbean', 'samerica', 'asia', 'middleeast', 'nafrica', 'ssafrica', 'oceania', 'pacific'];
    keys.forEach(k => {
        const btn = document.getElementById(`filter-region-${k}`);
        if (btn) {
            const isSpan2 = (k === 'pacific');
            const spanClass = isSpan2 ? 'col-span-2 ' : '';
            if (selectedRegions.has(k)) {
                btn.className = `${spanClass}py-1.5 px-2 rounded-xl border text-[11px] font-semibold bg-cyan-500/20 text-cyan-300 border-cyan-500/40 transition-all text-center flex items-center justify-center shadow-sm shadow-cyan-500/10 cursor-pointer`;
            } else {
                btn.className = `${spanClass}py-1.5 px-2 rounded-xl border text-[11px] font-semibold bg-slate-900/90 text-slate-400 border-slate-800 hover:border-slate-700 transition-all text-center flex items-center justify-center cursor-pointer`;
            }
        }
    });
}

function zoomToAirportsBounds(airports) {
    if (!map || !airports || airports.length === 0) return;
    const validAps = airports.filter(a => a.lat && a.lon);
    if (validAps.length === 0) return;

    let minLat = 90, maxLat = -90, minLon = 180, maxLon = -180;
    validAps.forEach(a => {
        if (a.lat < minLat) minLat = a.lat;
        if (a.lat > maxLat) maxLat = a.lat;
        if (a.lon < minLon) minLon = a.lon;
        if (a.lon > maxLon) maxLon = a.lon;
    });

    if (minLat !== 90 && maxLat !== -90) {
        map.fitBounds([[minLat, minLon], [maxLat, maxLon]], { padding: [50, 50], maxZoom: 8, animate: true });
    }
}

function zoomToFilteredAirportsBounds() {
    zoomToAirportsBounds(currentlyFilteredAirports);
}

function airportMatchesSourceFilter(ap) {
    if (selectedSources.size === ALL_SOURCES_LIST.length) return true;
    if (selectedSources.size === 0) return false;

    const sources = ap.all_sources || [];
    if (sources.length === 0) {
        const cat = getAirportCategory(ap);
        if (cat === 'DEFAULT') {
            return selectedSources.has('Official') || selectedSources.has('asobo');
        }
        return false;
    }

    // Only evaluate ACTIVE sources (or primary active source) so disabled packages don't trigger wrong category/source filters
    const activeSources = sources.filter(s => !s.is_disabled);
    const evalSources = activeSources.length > 0 ? activeSources : sources;

    return evalSources.some(s => {
        const sf = (s.source_folder || '').toLowerCase();
        const v = (s.vendor || '').toLowerCase();
        const fn = (s.folder_name || '').toLowerCase();
        const pt = (s.pricing_type || '').toLowerCase();

        // 1. Community Filter
        if (selectedSources.has('Community') && sf.includes('community')) return true;

        // 2. StreamedPackages Filter (MSFS 2024 Streamed)
        if (selectedSources.has('StreamedPackages') && sf.includes('streamedpackages')) return true;

        // 3. Asobo Filter (Asobo / Microsoft Handcrafted)
        if (selectedSources.has('asobo') && (s.is_asobo_official || pt === 'asobo' || v.includes('asobo') || (v.includes('microsoft') && !v.includes('community')) || fn.startsWith('asobo-') || fn.startsWith('microsoft-') || fn.startsWith('fs20-asobo-') || fn.startsWith('fs24-asobo-'))) return true;

        // 4. Official / OneStore Filter
        if (selectedSources.has('Official') && (sf.includes('official') || sf.includes('onestore'))) return true;

        return false;
    });
}

function filterAirports() {
    const rawSearch = document.getElementById('search-input').value.toLowerCase();
    const search = rawSearch.trim ? rawSearch.trim() : rawSearch;
    
    document.getElementById('clear-search').classList.toggle('hidden', search.length === 0);

    // Pre-calculate active route destination ICAOs if operating airline route filter is active
    let activeRouteDestIcaos = null;
    if (selectedAirlines.size > 0 && activeRouteOrigin) {
        activeRouteDestIcaos = new Set();
        selectedAirlines.forEach(al => {
            const dests = (activeRouteOrigin.routes && activeRouteOrigin.routes[al]) || [];
            dests.forEach(d => activeRouteDestIcaos.add(d));
        });
    }

    currentlyFilteredAirports = allAirportsData.filter(ap => {
        // High Priority: Origin Airport & Direct Airline Route Destinations (Bypasses global filters)
        if (activeRouteDestIcaos) {
            if (ap.icao === activeRouteOrigin.icao || activeRouteDestIcaos.has(ap.icao)) {
                if (search && search.length > 0) {
                    const searchStr = `${ap.icao} ${ap.name || ''} ${ap.city || ''} ${ap.country || ''}`.toLowerCase();
                    if (!searchStr.includes(search)) return false;
                }
                return true;
            }
            return false;
        }

        // Active Flight Corridor Filter (Alt + Click)
        if (selectedAirport && flightCorridorArrivalAirport) {
            if (!isAirportInCorridor(ap, selectedAirport, flightCorridorArrivalAirport, 250)) {
                return false;
            }
        }

        // Selected Country Overlay Filter
        if (selectedCountryCode) {
            const apIso = ((ap.country || ap.iso_country || '').toString()).toUpperCase().trim();
            if (apIso !== selectedCountryCode) {
                return false;
            }

            // Apply Country Pricing Breakdown Filter
            const pt = getAirportPricingType(ap);
            let catKey = 'FREEWARE';
            if (pt === 'Payware') catKey = 'PAYWARE';
            else if (pt === 'Asobo') catKey = 'ASOBO';
            else if (pt === 'Default' || ap.pricing_type === 'Default' || ap.package_name === 'Default MSFS Base Airport') catKey = 'DEFAULT';

            if (!selectedCountryPricingFilters.has(catKey)) return false;

            // Apply Country Airport Type Filter
            const typeStr = (ap.english_type || ap.type || '').toLowerCase();
            let typeKey = 'REG';
            if (typeStr.includes('international')) typeKey = 'INT';
            else if (typeStr.includes('general') || typeStr.includes('ga')) typeKey = 'GA';
            else if (typeStr.includes('heli') || typeStr.includes('water')) typeKey = 'HW';

            if (!selectedCountryTypeFilters.has(typeKey)) return false;
        } else {
            // Global Scenery Source Filter (only applied when NOT in country mode)
            if (!airportMatchesSourceFilter(ap)) {
                return false;
            }

            // Global Airport Type Filter (only applied when NOT in country mode)
            const apType = ap.english_type || ap.type || 'General Aviation';
            if (!selectedTypes.has(apType)) {
                return false;
            }
        }

        // GSX Profile Filter (all, with, none)
        const hasGsx = !!(ap.gsx_profile || ap.has_gsx_profile);
        if (selectedGsxFilter === 'with' && !hasGsx) {
            return false;
        }
        if (selectedGsxFilter === 'none' && hasGsx) {
            return false;
        }

        // Operating Airline & Direct Route Filter
        if (selectedAirlines.size > 0) {
            if (activeRouteOrigin) {
                // Specific origin airport route mode: Include origin AND all destination ICAOs (custom + default MSFS)
                if (ap.icao === activeRouteOrigin.icao) {
                    return true;
                }
                let combinedDestIcaos = new Set();
                selectedAirlines.forEach(al => {
                    const dests = (activeRouteOrigin.routes && activeRouteOrigin.routes[al]) || [];
                    dests.forEach(d => combinedDestIcaos.add(d));
                });
                if (!combinedDestIcaos.has(ap.icao)) return false;
            } else {
                // Global airline filter mode
                const airlines = ap.operating_airlines || [];
                if (!Array.from(selectedAirlines).some(al => airlines.includes(al))) return false;
            }
        } else if (!selectedCountryCode) {
            // Global Pricing Filter (only applied when NOT in country mode and NOT in airline route mode)
            const pt = getAirportPricingType(ap);
            if (selectedPricing.size === 1) {
                // Strict single-category mode
                if (!selectedPricing.has(pt)) return false;
            } else {
                // Multi-select mode
                if (!selectedPricing.has(pt) && !hasCustomAddonSources(ap)) return false;
            }
        }

        // High-performance search text filtering via pre-computed _searchKey
        if (search) {
            const searchIso = COUNTRY_NAME_TO_ISO[search] || (search.length === 2 ? search.toUpperCase() : null);
            const apIso = ((ap.country || ap.iso_country || '').toString()).toUpperCase().trim();

            if (searchIso) {
                // If search query is a country name, match airports in that country ISO!
                if (apIso !== searchIso) return false;
            } else {
                if (!ap._searchKey) {
                    ap._searchKey = `${ap.icao} ${ap.name} ${ap.city || ''} ${ap.country || ''} ${ap.iso_country || ''} ${ap.package_name || ''} ${ap.vendor || ''}`.toLowerCase();
                }
                if (!ap._searchKey.includes(search)) return false;
            }
        }

        return true;
    });

    if (activeRouteDestIcaos && window.worldAirportCoords) {
        activeRouteDestIcaos.forEach(dIcao => {
            if (dIcao !== activeRouteOrigin.icao && !currentlyFilteredAirports.some(a => a.icao === dIcao)) {
                const wInfo = window.worldAirportCoords[dIcao];
                if (wInfo) {
                    currentlyFilteredAirports.push({
                        icao: dIcao,
                        ident: dIcao,
                        lat: wInfo.lat,
                        lon: wInfo.lon,
                        name: wInfo.name,
                        city: wInfo.city || '',
                        country: wInfo.country || '',
                        type: wInfo.type || 'airport',
                        english_type: 'General Aviation',
                        vendor: 'Microsoft Flight Simulator (Default)',
                        pricing_type: 'Default',
                        is_default: true
                    });
                }
            }
        });
    }

    renderAirportsOnMap(currentlyFilteredAirports);
}

function handleSearchKeyDown(e) {
    if (e.key === 'Enter') {
        triggerSearchFocus();
    }
}

function triggerSearchFocus() {
    const rawSearch = document.getElementById('search-input').value.toLowerCase().trim();
    if (!rawSearch) return;

    // 1. Check for exact ICAO match
    const sUpper = rawSearch.toUpperCase();
    const exactIcaoMatch = currentlyFilteredAirports.find(a => a.icao === sUpper);
    if (exactIcaoMatch) {
        focusAirportWithAnimation(exactIcaoMatch);
        return;
    }

    // 2. Check if search query matches a Country Name or Country ISO Code
    const targetIso = COUNTRY_NAME_TO_ISO[rawSearch] || (rawSearch.length === 2 ? rawSearch.toUpperCase() : null);

    if (targetIso) {
        let countryLayer = null;
        if (countryGeoJsonLayer) {
            countryGeoJsonLayer.eachLayer(layer => {
                if (layer.feature && getFeatureIso(layer.feature) === targetIso) {
                    countryLayer = layer;
                }
            });
        }

        const countryName = rawSearch.charAt(0).toUpperCase() + rawSearch.slice(1);
        toggleCountrySelection(targetIso, countryName, countryLayer);
        return;
    }

    // 3. Fallback to zooming to the filtered airports bounds or first airport
    if (currentlyFilteredAirports.length > 1) {
        zoomToFilteredAirportsBounds();
    } else if (currentlyFilteredAirports.length === 1) {
        focusAirportWithAnimation(currentlyFilteredAirports[0]);
    }
}

function clearSearch() {
    document.getElementById('search-input').value = '';
    lastFocusedIcao = null;
    filterAirports();
}

function filterByPricingPill(pricing) {
    if (pricing === 'All') {
        if (selectedPricing.size === ALL_PRICING_LIST.length) {
            selectedPricing = new Set(DEFAULT_STARTUP_PRICING);
        } else {
            selectedPricing = new Set(ALL_PRICING_LIST);
        }
    } else if (pricing === 'Payware') {
        if (selectedPricing.size === 1 && selectedPricing.has('Payware')) {
            selectedPricing = new Set(DEFAULT_STARTUP_PRICING);
        } else {
            selectedPricing = new Set(['Payware']);
        }
    } else if (pricing === 'Freeware') {
        if (selectedPricing.size === 1 && selectedPricing.has('Freeware / Flightsim.to')) {
            selectedPricing = new Set(DEFAULT_STARTUP_PRICING);
        } else {
            selectedPricing = new Set(['Freeware / Flightsim.to']);
        }
    } else if (pricing === 'Asobo') {
        if (selectedPricing.size === 1 && selectedPricing.has('Asobo')) {
            selectedPricing = new Set(DEFAULT_STARTUP_PRICING);
        } else {
            selectedPricing = new Set(['Asobo']);
        }
    } else if (pricing === 'Default') {
        if (selectedPricing.size === 1 && selectedPricing.has('Default')) {
            selectedPricing = new Set(DEFAULT_STARTUP_PRICING);
        } else {
            selectedPricing = new Set(['Default']);
        }
    }
    updateFilterUI();
    filterAirports();
}

function togglePricingFilter(pricing) {
    if (pricing === 'all') {
        if (selectedPricing.size === ALL_PRICING_LIST.length) {
            selectedPricing.clear();
        } else {
            selectedPricing = new Set(ALL_PRICING_LIST);
        }
    } else {
        if (selectedPricing.has(pricing)) {
            selectedPricing.delete(pricing);
        } else {
            selectedPricing.add(pricing);
        }
    }
    updateFilterUI();
    filterAirports();
}

function toggleSourceFilter(src) {
    if (src === 'all') {
        if (selectedSources.size === ALL_SOURCES_LIST.length) {
            selectedSources.clear();
        } else {
            selectedSources = new Set(ALL_SOURCES_LIST);
        }
    } else {
        if (selectedSources.has(src)) {
            selectedSources.delete(src);
        } else {
            selectedSources.add(src);
        }
    }
    updateFilterUI();
    filterAirports();
}

function toggleTypeFilter(type) {
    if (type === 'all') {
        if (selectedTypes.size === ALL_TYPES_LIST.length) {
            selectedTypes.clear();
        } else {
            selectedTypes = new Set(ALL_TYPES_LIST);
        }
    } else {
        if (selectedTypes.has(type)) {
            selectedTypes.delete(type);
        } else {
            selectedTypes.add(type);
        }
    }
    updateFilterUI();
    filterAirports();
}

function setPillHighlight(el, isActive, colorType) {
    if (!el) return;

    // Fully strip both active and default colored backgrounds, borders, and shadows
    el.classList.remove(
        'border-2', 'border', 'border-sky-400', 'border-purple-400', 'border-cyan-400', 'border-amber-400', 'border-blue-400', 'border-slate-800',
        'border-sky-500/40', 'border-purple-500/40', 'border-cyan-500/40', 'border-amber-500/40', 'border-blue-500/40',
        'bg-sky-500/15', 'bg-purple-500/15', 'bg-cyan-500/15', 'bg-amber-500/15', 'bg-blue-500/15',
        'bg-sky-500/30', 'bg-purple-500/30', 'bg-cyan-500/30', 'bg-amber-500/30', 'bg-blue-500/30', 'bg-slate-900/60',
        'shadow-[0_0_15px_rgba(56,189,248,0.4)]', 'shadow-[0_0_15px_rgba(168,85,247,0.4)]',
        'shadow-[0_0_15px_rgba(6,182,212,0.4)]', 'shadow-[0_0_15px_rgba(245,158,11,0.4)]', 'shadow-[0_0_15px_rgba(59,130,246,0.4)]',
        'shadow-sky-950/20', 'shadow-purple-950/20', 'shadow-cyan-950/20', 'shadow-amber-950/20', 'shadow-blue-950/20',
        'scale-105', 'opacity-60', 'opacity-100'
    );

    if (isActive) {
        el.classList.add('opacity-100', 'scale-105');
        if (colorType === 'sky') {
            el.classList.add('border-2', 'border-sky-400', 'bg-sky-500/30', 'shadow-[0_0_15px_rgba(56,189,248,0.4)]');
        } else if (colorType === 'purple') {
            el.classList.add('border-2', 'border-purple-400', 'bg-purple-500/30', 'shadow-[0_0_15px_rgba(168,85,247,0.4)]');
        } else if (colorType === 'cyan') {
            el.classList.add('border-2', 'border-cyan-400', 'bg-cyan-500/30', 'shadow-[0_0_15px_rgba(6,182,212,0.4)]');
        } else if (colorType === 'amber') {
            el.classList.add('border-2', 'border-amber-400', 'bg-amber-500/30', 'shadow-[0_0_15px_rgba(245,158,11,0.4)]');
        } else if (colorType === 'blue') {
            el.classList.add('border-2', 'border-blue-400', 'bg-blue-500/30', 'shadow-[0_0_15px_rgba(59,130,246,0.4)]');
        }
    } else {
        el.classList.add('border', 'border-slate-800', 'bg-slate-900/60', 'opacity-60');
    }
}

function updateFilterUI() {
    // Stat Pills Active Glow Highlight
    const isAllSelected = (selectedPricing.size === ALL_PRICING_LIST.length);
    const isOnlyPayware = (selectedPricing.size === 1 && selectedPricing.has('Payware'));
    const isOnlyFreeware = (selectedPricing.size === 1 && selectedPricing.has('Freeware / Flightsim.to'));
    const isOnlyAsobo = (selectedPricing.size === 1 && selectedPricing.has('Asobo'));
    const isOnlyDefault = (selectedPricing.size === 1 && selectedPricing.has('Default'));

    setPillHighlight(document.getElementById('stat-pill-total'), isAllSelected, 'sky');
    setPillHighlight(document.getElementById('stat-pill-payware'), isOnlyPayware, 'purple');
    setPillHighlight(document.getElementById('stat-pill-freeware'), isOnlyFreeware, 'cyan');
    setPillHighlight(document.getElementById('stat-pill-asobo'), isOnlyAsobo, 'amber');
    setPillHighlight(document.getElementById('stat-pill-default'), isOnlyDefault, 'blue');

    // Pricing Buttons UI
    const priceMap = {
        'Payware': 'filter-price-payware',
        'Freeware / Flightsim.to': 'filter-price-freeware',
        'Asobo': 'filter-price-asobo',
        'Default': 'filter-price-default'
    };

    const allPriceBtn = document.getElementById('filter-price-all');
    setButtonActive(allPriceBtn, selectedPricing.size === ALL_PRICING_LIST.length);

    ALL_PRICING_LIST.forEach(price => {
        const btnId = priceMap[price];
        const btn = document.getElementById(btnId);
        if (btn) {
            setButtonActive(btn, selectedPricing.has(price));
        }
    });

    // Source Buttons UI
    const allSrcBtn = document.getElementById('filter-src-all');
    setButtonActive(allSrcBtn, selectedSources.size === ALL_SOURCES_LIST.length);

    ALL_SOURCES_LIST.forEach(src => {
        const btn = document.getElementById(`filter-src-${src}`);
        if (btn) {
            setButtonActive(btn, selectedSources.has(src));
        }
    });

    // Type Buttons UI
    const allTypeBtn = document.getElementById('filter-type-all');
    setButtonActive(allTypeBtn, selectedTypes.size === ALL_TYPES_LIST.length);

    ALL_TYPES_LIST.forEach(type => {
        const btnId = `filter-type-${type.replace(/\s+/g, '-').replace(/\//g, '-')}`;
        const btn = document.getElementById(btnId);
        if (btn) {
            setButtonActive(btn, selectedTypes.has(type));
        }
    });

    updateGsxFilterUI();

    // Airline Filter Pill UI
    const airlinePill = document.getElementById('airline-filter-pill');
    const airlineNameEl = document.getElementById('airline-filter-name');
    const airlineCountEl = document.getElementById('airline-filter-count');
    if (airlinePill) {
        if (selectedAirlines.size > 0) {
            airlinePill.classList.remove('hidden');
            airlinePill.classList.add('flex');
            const namesList = Array.from(selectedAirlines).join(', ');
            if (airlineNameEl) airlineNameEl.innerText = namesList;
            if (airlineCountEl) airlineCountEl.innerText = currentlyFilteredAirports ? currentlyFilteredAirports.length : 0;
        } else {
            airlinePill.classList.add('hidden');
            airlinePill.classList.remove('flex');
        }
    }
}

function toggleGsxFilter(val) {
    selectedGsxFilter = val;
    updateGsxFilterUI();
    filterAirports();
}

function updateGsxFilterUI() {
    ['all', 'with', 'none'].forEach(mode => {
        const btn = document.getElementById(`filter-gsx-${mode}`);
        if (!btn) return;
        if (selectedGsxFilter === mode) {
            btn.className = "py-2 px-2 rounded-xl border text-xs font-semibold bg-cyan-500/20 text-cyan-300 border-cyan-500/40 transition-all text-center flex items-center justify-center gap-1 shadow-sm shadow-cyan-500/10";
        } else {
            btn.className = "py-2 px-2 rounded-xl border text-xs font-medium bg-slate-900/60 text-slate-400 border-slate-800/80 opacity-60 hover:opacity-100 transition-all text-center flex items-center justify-center gap-1";
        }
    });
}

function setButtonActive(btn, active) {
    if (!btn) return;
    if (active) {
        btn.className = "py-2 px-3 rounded-xl border text-xs font-semibold bg-cyan-500/20 text-cyan-300 border-cyan-500/40 transition-all text-center flex items-center justify-center gap-1.5 shadow-sm shadow-cyan-500/10";
    } else {
        btn.className = "py-2 px-3 rounded-xl border text-xs font-medium bg-slate-900/60 text-slate-400 border-slate-800/80 opacity-60 hover:opacity-100 transition-all text-center flex items-center justify-center gap-1.5";
    }
}

async function rescanMSFS() {
    const icon = document.getElementById('rescan-icon');
    if (icon) icon.classList.add('fa-spin');

    const splash = document.getElementById('splash-screen');
    const statusTxt = document.getElementById('splash-status-text');
    const folderTxt = document.getElementById('splash-folder-text');
    const progressFx = document.getElementById('splash-progress-bar');
    const percentTxt = document.getElementById('splash-percent-text');

    if (splash) {
        splash.classList.remove('hidden', 'opacity-0', 'pointer-events-none');
        splash.classList.add('flex', 'opacity-100');
        if (statusTxt) statusTxt.innerText = "Rescanning MSFS 2024 Sceneries & Packages...";
        if (folderTxt) folderTxt.innerText = "Scanning Community & StreamedPackages folders...";
        if (progressFx) progressFx.style.width = "25%";
        if (percentTxt) percentTxt.innerText = "25%";
    }

    // Force browser repaint before calling pywebview rescan
    await new Promise(r => setTimeout(r, 60));

    let progressTimer = setInterval(() => {
        if (!progressFx) return;
        let curr = parseInt(progressFx.style.width) || 25;
        if (curr < 85) {
            curr += 15;
            progressFx.style.width = curr + '%';
            if (percentTxt) percentTxt.innerText = curr + '%';
            if (curr === 40 && folderTxt) folderTxt.innerText = "Scanning Official2020 / OneStore packages...";
            if (curr === 70 && folderTxt) folderTxt.innerText = "Parsing Content.xml & resolving conflicts...";
        }
    }, 150);

    try {
        let dataStr;
        if (window.pywebview) {
            dataStr = await window.pywebview.api.rescan();
            allAirportsData = JSON.parse(dataStr);
        } else {
            const resp = await fetch('/api/rescan', { method: 'POST' });
            allAirportsData = await resp.json();
        }

        clearInterval(progressTimer);
        if (progressFx) progressFx.style.width = "100%";
        if (percentTxt) percentTxt.innerText = "100%";
        if (folderTxt) folderTxt.innerText = "Scan complete! Updating database...";

        allAirportsData.forEach(ap => {
            if (userRatingsMap[ap.icao] !== undefined) {
                ap.rating = userRatingsMap[ap.icao];
            } else {
                ap.rating = ap.rating || 0;
            }
        });

        updateStats(allAirportsData);
        filterAirports();

        if (selectedAirport) {
            const updatedAp = allAirportsData.find(a => a.icao === selectedAirport.icao);
            if (updatedAp) showAirportDetails(updatedAp);
        }

        await new Promise(r => setTimeout(r, 400));
    } catch (err) {
        console.error("Rescan error:", err);
    } finally {
        clearInterval(progressTimer);
        if (icon) icon.classList.remove('fa-spin');
        if (splash) {
            splash.classList.add('opacity-0', 'pointer-events-none');
            setTimeout(() => splash.classList.add('hidden'), 500);
        }
    }
}

function openPackageFolder() {
    if (selectedAirport && window.pywebview) {
        window.pywebview.api.open_folder(selectedAirport.package_path);
    }
}

/* ================= SETTINGS MODAL FUNCTIONS ================= */

async function triggerSearchGsxProfile() {
    if (!selectedAirport) return;
    try {
        if (window.pywebview) {
            await window.pywebview.api.search_gsx_profile(selectedAirport.icao, selectedAirport.name || '');
        }
    } catch (e) {
        console.error("Search GSX profile error:", e);
    }
}

async function openGsxProfileInExplorer(path) {
    if (!path) return;
    try {
        if (window.pywebview) {
            await window.pywebview.api.open_file_in_explorer(path);
        }
    } catch (e) {
        console.error("Open GSX profile error:", e);
    }
}

function handleGsxDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    const container = document.getElementById('drawer-gsx-card');
    if (container) {
        container.classList.add('border-cyan-500', 'bg-cyan-500/10');
    }
}

function handleGsxDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    const container = document.getElementById('drawer-gsx-card');
    if (container) {
        container.classList.remove('border-cyan-500', 'bg-cyan-500/10');
    }
}

async function handleGsxDrop(e) {
    e.preventDefault();
    e.stopPropagation();

    const container = document.getElementById('drawer-gsx-card');
    if (container) {
        container.classList.remove('border-cyan-500', 'bg-cyan-500/10');
    }

    if (!e.dataTransfer || !e.dataTransfer.files || e.dataTransfer.files.length === 0) return;

    const file = e.dataTransfer.files[0];
    const path = file.path || '';

    if (path) {
        await executeGsxInstallation({ filePath: path });
    } else {
        const reader = new FileReader();
        reader.onload = async function(event) {
            const base64Data = event.target.result;
            await executeGsxInstallation({ base64Data: base64Data, filename: file.name });
        };
        reader.onerror = function() {
            showCustomModal({ title: 'Erreur de lecture', message: 'Impossible de lire le fichier déposé.', type: 'error' });
        };
        reader.readAsDataURL(file);
    }
}

async function triggerInstallGsxProfile() {
    await executeGsxInstallation({ filePath: '' });
}

async function executeGsxInstallation({ filePath = '', base64Data = '', filename = '' } = {}) {
    if (!selectedAirport) return;
    try {
        if (window.pywebview) {
            const resStr = await window.pywebview.api.install_gsx_profile(
                selectedAirport.icao || '',
                filePath || '',
                base64Data || '',
                filename || ''
            );
            const res = JSON.parse(resStr);
            if (res.status === 'ok') {
                allAirportsData = res.airports;
                allAirportsData.forEach(ap => {
                    if (userRatingsMap[ap.icao] !== undefined) {
                        ap.rating = userRatingsMap[ap.icao];
                    }
                });
                updateStats(allAirportsData);
                filterAirports();
                const updatedAp = allAirportsData.find(a => a.icao === selectedAirport.icao);
                if (updatedAp) showAirportDetails(updatedAp);
                showCustomModal({
                    title: 'Profil GSX Installé',
                    message: `Profil(s) GSX extrait(s) et installé(s) avec succès :\n\n• ${res.installed_files.join('\n• ')}`,
                    type: 'success',
                    confirmText: 'Continuer'
                });
            } else {
                showCustomModal({
                    title: 'Information Profil GSX',
                    message: res.message,
                    type: 'info',
                    confirmText: 'Compris'
                });
            }
        }
    } catch (e) {
        console.error("GSX Installation error:", e);
        showCustomModal({
            title: 'Erreur d\'installation GSX',
            message: e.message || String(e),
            type: 'error'
        });
    }
}

async function browseGsxFolder() {
    try {
        if (window.pywebview) {
            const folder = await window.pywebview.api.browse_folder();
            if (folder) {
                document.getElementById('cfg-gsx-path').value = folder;
                currentSettings.gsx_profile_path = folder;
            }
        }
    } catch (e) {
        console.error("Browse GSX folder error:", e);
    }
}

async function openSettingsModal() {
    try {
        if (window.pywebview) {
            const cfgStr = await window.pywebview.api.get_settings();
            currentSettings = JSON.parse(cfgStr);
        } else {
            const resp = await fetch('/api/settings');
            currentSettings = await resp.json();
        }
    } catch (e) {
        console.error("Failed to load settings:", e);
    }

    document.getElementById('cfg-auto-scan').checked = !!currentSettings.auto_scan_on_startup;
    const gsxInput = document.getElementById('cfg-gsx-path');
    if (gsxInput) {
        gsxInput.value = currentSettings.gsx_profile_path || '';
    }

    renderSettingsPathsList();
    document.getElementById('settings-modal').classList.remove('hidden');
}

function closeSettingsModal() {
    document.getElementById('settings-modal').classList.add('hidden');
}

function renderSettingsPathsList() {
    const container = document.getElementById('settings-paths-list');
    container.innerHTML = '';

    const paths = currentSettings.scan_paths || [];

    paths.forEach((item, index) => {
        const row = document.createElement('div');
        row.className = "p-3 rounded-2xl bg-slate-950/70 border border-slate-800 flex items-center justify-between gap-3";

        row.innerHTML = `
            <div class="space-y-1.5 flex-1">
                <div class="flex items-center justify-between">
                    <input type="text" value="${item.name || 'MSFS Scenery Path'}" 
                           oninput="updatePathName(${index}, this.value)"
                           placeholder="Folder Name (e.g. MSFS 2024 - Community)"
                           class="bg-transparent text-xs font-bold text-cyan-400 border-b border-slate-700/60 hover:border-cyan-500 focus:border-cyan-400 focus:outline-none px-1 py-0.5 w-full max-w-md transition-all">
                </div>

                <div class="flex items-center gap-2">
                    <input type="text" value="${item.path || ''}" 
                           oninput="updatePathValue(${index}, this.value)"
                           class="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-500">
                    <button onclick="browsePathFolder(${index})" class="px-2.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white text-xs transition-all flex items-center gap-1.5" title="Browse Folder">
                        <i class="fa-solid fa-folder-open text-cyan-400"></i>
                    </button>
                </div>
            </div>

            <div class="flex items-center gap-3 self-center pl-2">
                <label class="relative inline-flex items-center cursor-pointer" title="Enable/Disable Path Scan">
                    <input type="checkbox" ${item.enabled ? 'checked' : ''} onchange="togglePathEnabled(${index}, this.checked)" class="sr-only peer">
                    <div class="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-500"></div>
                </label>

                <button onclick="removePathRow(${index})" class="w-8 h-8 rounded-xl bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 border border-slate-700 transition-all flex items-center justify-center" title="Remove Path">
                    <i class="fa-solid fa-trash text-xs"></i>
                </button>
            </div>
        `;

        container.appendChild(row);
    });
}

function updatePathName(index, val) {
    if (currentSettings.scan_paths[index]) {
        currentSettings.scan_paths[index].name = val;
    }
}

function updatePathValue(index, val) {
    if (currentSettings.scan_paths[index]) {
        currentSettings.scan_paths[index].path = val;
    }
}

function togglePathEnabled(index, checked) {
    if (currentSettings.scan_paths[index]) {
        currentSettings.scan_paths[index].enabled = checked;
    }
}

async function browsePathFolder(index) {
    if (window.pywebview) {
        const folder = await window.pywebview.api.browse_folder();
        if (folder) {
            currentSettings.scan_paths[index].path = folder;
            renderSettingsPathsList();
        }
    }
}

function removePathRow(index) {
    currentSettings.scan_paths.splice(index, 1);
    renderSettingsPathsList();
}

function addCustomPathRow() {
    const newId = String(Date.now());
    currentSettings.scan_paths.push({
        id: newId,
        name: "Custom Scenery Directory",
        path: "D:\\Custom_MSFS_Sceneries",
        enabled: true
    });
    renderSettingsPathsList();
}

async function saveAndRescanSettings() {
    currentSettings.auto_scan_on_startup = document.getElementById('cfg-auto-scan').checked;
    const gsxInput = document.getElementById('cfg-gsx-path');
    if (gsxInput) {
        currentSettings.gsx_profile_path = gsxInput.value.trim();
    }

    try {
        if (window.pywebview) {
            await window.pywebview.api.save_settings(JSON.stringify(currentSettings));
        }
        closeSettingsModal();
        await rescanMSFS();
    } catch (e) {
        console.error("Failed to save settings:", e);
    }
}

/* ================= EXPORT COLLECTION FUNCTIONS ================= */

function openExportModal() {
    const modal = document.getElementById('export-modal');
    if (modal) modal.classList.remove('hidden');

    const txtEl = document.getElementById('export-scope-text');
    const scopeEl = document.querySelector('input[name="export-scope"]:checked');
    if (txtEl && scopeEl) {
        if (scopeEl.value === 'all') {
            txtEl.innerText = `Exports all ${allAirportsData.length} installed sceneries (physical sceneries & streamed Marketplace).`;
        } else {
            txtEl.innerText = `Exports only the ${currentlyFilteredAirports.length} sceneries currently visible on the map based on active filters (Payware, GSX, etc.).`;
        }
    }

    document.querySelectorAll('input[name="export-scope"]').forEach(radio => {
        radio.onclick = function() {
            if (!txtEl) return;
            if (this.value === 'all') {
                txtEl.innerText = `Exports all ${allAirportsData.length} installed sceneries (physical sceneries & streamed Marketplace).`;
            } else {
                txtEl.innerText = `Exports only the ${currentlyFilteredAirports.length} sceneries currently visible on the map based on active filters (Payware, GSX, etc.).`;
            }
        };
    });
}

function closeExportModal() {
    const modal = document.getElementById('export-modal');
    if (modal) modal.classList.add('hidden');
}

async function triggerExportCollection(format) {
    const scopeEl = document.querySelector('input[name="export-scope"]:checked');
    const scope = scopeEl ? scopeEl.value : 'all';

    const dataToExport = (scope === 'filtered') ? currentlyFilteredAirports : allAirportsData;

    if (!dataToExport || dataToExport.length === 0) {
        alert("No sceneries available to export.");
        return;
    }

    try {
        if (window.pywebview) {
            const dataJson = JSON.stringify(dataToExport);
            let resStr;
            if (format === 'csv') {
                resStr = await window.pywebview.api.export_collection_csv(dataJson);
            } else {
                resStr = await window.pywebview.api.export_collection_json(dataJson);
            }

            const res = JSON.parse(resStr);
            if (res.status === 'ok') {
                closeExportModal();
                showCustomModal({
                    title: "Collection Exported Successfully",
                    message: `Exported ${res.count} sceneries to:\n${res.path}`,
                    confirmText: "OK"
                });
            } else if (res.status !== 'cancelled') {
                showCustomModal({
                    title: "Export Failed",
                    message: res.message || "Could not export collection.",
                    confirmText: "OK"
                });
            }
        }
    } catch (e) {
        console.error("Export collection error:", e);
        showCustomModal({
            title: "Export Error",
            message: "Failed to export collection.",
            confirmText: "OK"
        });
    }
}

/* ================= SYSTEM NOTIFICATION MODAL FUNCTIONS ================= */

let customModalConfirmCallback = null;
let customModalCancelCallback = null;

function showCustomModal(titleOrObj, messageStr, typeStr = 'info') {
    const modal = document.getElementById('custom-modal');

    let title = 'Notification';
    let message = '';
    let type = 'info';
    let confirmText = 'OK';
    let cancelText = 'Annuler';
    let showCancel = false;

    if (typeof titleOrObj === 'object' && titleOrObj !== null) {
        title = titleOrObj.title || 'Notification';
        message = titleOrObj.message || '';
        type = titleOrObj.type || 'info';
        confirmText = titleOrObj.confirmText || 'OK';
        cancelText = titleOrObj.cancelText || 'Cancel';
        showCancel = titleOrObj.showCancel !== undefined ? !!titleOrObj.showCancel : (!!titleOrObj.cancelText || !!titleOrObj.onCancel);
        customModalConfirmCallback = titleOrObj.onConfirm || null;
        customModalCancelCallback = titleOrObj.onCancel || null;
    } else {
        title = titleOrObj || 'Notification';
        message = messageStr || '';
        type = typeStr || 'info';
        customModalConfirmCallback = null;
        customModalCancelCallback = null;
    }

    if (!modal) {
        alert(`${title}\n\n${message}`);
        return;
    }

    const titleEl = document.getElementById('custom-modal-title');
    const msgEl = document.getElementById('custom-modal-message');
    const cancelBtn = document.getElementById('custom-modal-cancel-btn');
    const confirmBtn = document.getElementById('custom-modal-confirm-btn');
    const iconBg = document.getElementById('custom-modal-icon-bg');
    const iconEl = document.getElementById('custom-modal-icon');

    if (titleEl) titleEl.innerText = title;
    if (msgEl) msgEl.innerText = message;
    if (confirmBtn) confirmBtn.innerText = confirmText;
    if (cancelBtn) {
        cancelBtn.innerText = cancelText;
        cancelBtn.classList.toggle('hidden', !showCancel);
    }

    if (iconBg && iconEl) {
        iconBg.className = "w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 shadow-inner ";
        iconEl.className = "fa-solid text-lg ";
        if (type === 'success') {
            iconBg.classList.add('bg-emerald-500/10', 'border', 'border-emerald-500/20');
            iconEl.classList.add('fa-circle-check', 'text-emerald-400');
        } else if (type === 'error') {
            iconBg.classList.add('bg-red-500/10', 'border', 'border-red-500/20');
            iconEl.classList.add('fa-triangle-exclamation', 'text-red-400');
        } else {
            iconBg.classList.add('bg-cyan-500/10', 'border', 'border-cyan-500/20');
            iconEl.classList.add('fa-circle-info', 'text-cyan-400');
        }
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeCustomModal() {
    const modal = document.getElementById('custom-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    customModalConfirmCallback = null;
    customModalCancelCallback = null;
}

function confirmCustomModal() {
    const cb = customModalConfirmCallback;
    closeCustomModal();
    if (cb && typeof cb === 'function') {
        cb();
    }
}

function cancelCustomModal() {
    const cb = customModalCancelCallback;
    closeCustomModal();
    if (cb && typeof cb === 'function') {
        cb();
    }
}

function promptClosingFlightMode() {
    showCustomModal({
        title: 'Plan de Vol SimBrief Actif',
        message: 'Un plan de vol SimBrief est actuellement actif dans SceneryX (les scènes hors-route sont isolées et désactivées dans MSFS pour optimiser vos performances).\n\nQue souhaitez-vous faire en quittant SceneryX ?',
        type: 'warning',
        confirmText: '⚡ Garder l\'isolement (En Vol)',
        cancelText: '🔄 Rétablir toutes mes scènes',
        showCancel: true,
        onConfirm: () => {
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.exit_app(false);
            }
        },
        onCancel: () => {
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.exit_app(true);
            }
        }
    });
}

/* ================= SIMBRIEF FLIGHT OPTIMIZER UI ENGINE ================= */

let currentSimBriefFlight = null;

function loadSimBriefSettingsUI() {
    if (!currentSettings) return;
    if (currentSettings.simbrief_username) {
        const uInput = document.getElementById('sb-username-input');
        if (uInput) uInput.value = currentSettings.simbrief_username;
    }
    if (currentSettings.simbrief_userid) {
        const idInput = document.getElementById('sb-userid-input');
        if (idInput) idInput.value = currentSettings.simbrief_userid;
    }
    if (currentSettings.flight_mode && currentSettings.flight_mode.active) {
        updateFlightModeBannerUI(currentSettings.flight_mode);
    }
}

function autoSyncSimBrief(changedField) {
    let val = '';
    if (changedField === 'username') {
        val = document.getElementById('sb-username-input').value.trim();
    } else {
        val = document.getElementById('sb-userid-input').value.trim();
    }
    if (!val || !window.pywebview) return;

    window.pywebview.api.fetch_simbrief(val).then(resStr => {
        try {
            const res = JSON.parse(resStr);
            if (res.status === 'success') {
                if (res.username && document.getElementById('sb-username-input')) {
                    document.getElementById('sb-username-input').value = res.username;
                }
                if (res.userid && document.getElementById('sb-userid-input')) {
                    document.getElementById('sb-userid-input').value = res.userid;
                }
            }
        } catch(e){}
    });
}

function triggerSimBriefImport() {
    const uVal = document.getElementById('sb-username-input').value.trim();
    const idVal = document.getElementById('sb-userid-input').value.trim();
    const identifier = uVal || idVal;

    if (!identifier) {
        showCustomModal({
            title: 'SimBrief Credentials Required',
            message: 'Please enter your SimBrief Username or Pilot ID in the left sidebar to import your flight plan.',
            type: 'warning',
            confirmText: 'OK'
        });
        return;
    }

    const icon = document.getElementById('sb-import-icon');
    if (icon) icon.className = "fa-solid fa-spinner fa-spin text-amber-400";

    if (!window.pywebview) return;

    window.pywebview.api.fetch_simbrief(identifier).then(resStr => {
        if (icon) icon.className = "fa-solid fa-cloud-arrow-down text-amber-400";
        try {
            const res = JSON.parse(resStr);
            if (res.status === 'error') {
                showCustomModal({
                    title: 'SimBrief Import Error',
                    message: res.message || 'Could not fetch flight plan from SimBrief.',
                    type: 'error',
                    confirmText: 'OK'
                });
                return;
            }

            currentSimBriefFlight = res.flight;
            if (res.username) document.getElementById('sb-username-input').value = res.username;
            if (res.userid) document.getElementById('sb-userid-input').value = res.userid;

            openSimBriefModal(res.flight);
        } catch(e) {
            showCustomModal({
                title: 'SimBrief Import Error',
                message: 'Failed to parse response: ' + e.message,
                type: 'error',
                confirmText: 'OK'
            });
        }
    });
}

function openSimBriefModal(flight) {
    const infoEl = document.getElementById('sb-modal-flight-info');
    if (infoEl) infoEl.innerText = `${flight.flight_number ? flight.flight_number + ' | ' : ''}${flight.aircraft ? flight.aircraft + ' | ' : ''}OFP LOADED`;
    
    document.getElementById('sb-modal-origin-icao').innerText = flight.origin.icao;
    document.getElementById('sb-modal-origin-name').innerText = flight.origin.name;

    document.getElementById('sb-modal-dest-icao').innerText = flight.destination.icao;
    document.getElementById('sb-modal-dest-name').innerText = flight.destination.name;

    const altsContainer = document.getElementById('sb-modal-alternates-list');
    altsContainer.innerHTML = '';
    if (flight.alternates && flight.alternates.length > 0) {
        flight.alternates.forEach(alt => {
            const pill = document.createElement('div');
            pill.className = "px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 font-mono font-bold flex items-center gap-1.5";
            pill.innerHTML = `<span class="text-amber-400 font-black">${alt.icao}</span> <span class="text-[10px] text-slate-400 font-sans font-normal truncate max-w-[150px]">${alt.name}</span>`;
            altsContainer.appendChild(pill);
        });
    } else {
        altsContainer.innerHTML = `<span class="text-slate-500 italic">No alternate airports specified in OFP</span>`;
    }

    const routeIcaos = flight.flight_icaos || [];
    const thirdPartyAirports = allAirportsData.filter(a => 
        a.pricing_type !== 'Asobo' && 
        a.pricing_type !== 'Default' && 
        !a.is_default && 
        !a.is_asobo_official
    );
    const toKeep = thirdPartyAirports.filter(a => routeIcaos.includes(a.icao));
    const toDisableCount = thirdPartyAirports.length - toKeep.length;

    document.getElementById('sb-modal-impact-text').innerText = `${toDisableCount} non-route 3rd-party sceneries will be disabled to boost FPS and stability. ${toKeep.length} installed route scenery package(s) (${toKeep.map(a=>a.icao).join(', ') || 'None'}) will remain 100% active.`;

    const modal = document.getElementById('simbrief-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeSimBriefModal() {
    const modal = document.getElementById('simbrief-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function confirmSimBriefOptimization() {
    closeSimBriefModal();
    if (!currentSimBriefFlight || !window.pywebview) return;

    const flightIcaos = currentSimBriefFlight.flight_icaos || [];
    const origStr = (currentSimBriefFlight.origin && currentSimBriefFlight.origin.icao) ? currentSimBriefFlight.origin.icao : (typeof currentSimBriefFlight.origin === 'string' ? currentSimBriefFlight.origin : '');
    const destStr = (currentSimBriefFlight.destination && currentSimBriefFlight.destination.icao) ? currentSimBriefFlight.destination.icao : (typeof currentSimBriefFlight.destination === 'string' ? currentSimBriefFlight.destination : '');
    const routeName = (origStr && destStr) ? `${origStr} ➔ ${destStr}` : 'SimBrief Route';

    const apiFn = window.pywebview.api.optimize_flight_mode || window.pywebview.api.optimize_flight;
    apiFn.call(window.pywebview.api, JSON.stringify(flightIcaos)).then(resStr => {
        try {
            const res = JSON.parse(resStr);
            if (res.status === 'ok' || res.status === 'success') {
                if (res.airports && res.airports.length > 0) {
                    allAirportsData = res.airports;
                }

                const disabledNum = res.disabled_count !== undefined ? res.disabled_count : (res.disabledCount !== undefined ? res.disabledCount : 0);

                updateFlightModeBannerUI({
                    active: true,
                    origin: origStr,
                    destination: destStr,
                    disabled_count: disabledNum,
                    icaos: flightIcaos
                });

                filterAirports();

                showCustomModal(
                    'Flight Scenery Optimization Active 🚀',
                    `Successfully isolated sceneries for flight ${routeName}.\n\nNon-route 3rd-party sceneries are disabled & MSFS Content.xml updated. Enjoy your flight!`,
                    'success'
                );
            } else {
                showCustomModal('Optimization Error', res.message || "Failed to optimize sceneries.", 'error');
            }
        } catch(e){
            console.error("Error parsing flight optimization result:", e);
        }
    }).catch(err => {
        showCustomModal('Optimization Error', String(err), 'error');
    });
}

function updateFlightModeBannerUI(flightMode) {
    currentFlightMode = flightMode || { active: false, icaos: [] };
    const badge = document.getElementById('sb-status-badge');
    const routeInfo = document.getElementById('sb-route-info');
    const routeText = document.getElementById('sb-route-text');
    const disabledText = document.getElementById('sb-disabled-text');
    const importBtn = document.getElementById('sb-import-btn');

    if (currentFlightMode && currentFlightMode.active) {
        if (badge) {
            badge.className = "text-[9px] font-bold font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse";
            badge.innerText = "ACTIVE";
        }
        if (routeInfo) routeInfo.classList.remove('hidden');
        if (routeText && currentFlightMode.icaos) {
            routeText.innerText = currentFlightMode.icaos.join(' ➔ ');
        }
        if (disabledText) {
            disabledText.innerText = `${currentFlightMode.disabled_count || 0} sceneries isolated`;
        }
        if (importBtn) {
            importBtn.className = "w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-red-500/30 via-amber-500/30 to-orange-500/30 hover:from-red-500/40 hover:to-orange-500/40 border border-amber-500/60 text-amber-200 font-extrabold text-xs transition-all flex items-center justify-center gap-2 shadow-md shadow-amber-500/10 active:scale-98 cursor-pointer";
            importBtn.onclick = function() { restoreAllFlightSceneriesUI(); };
            importBtn.innerHTML = `<i class="fa-solid fa-power-off text-amber-400"></i> <span>Exit Flight Mode & Restore Sceneries</span>`;
        }
    } else {
        if (badge) {
            badge.className = "text-[9px] font-bold font-mono px-2 py-0.5 rounded-full bg-slate-900 text-slate-400 border border-slate-800";
            badge.innerText = "INACTIVE";
        }
        if (routeInfo) routeInfo.classList.add('hidden');
        if (importBtn) {
            importBtn.className = "w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-amber-500/20 to-orange-500/20 hover:from-amber-500/30 hover:to-orange-500/30 border border-amber-500/40 text-amber-300 font-extrabold text-xs transition-all flex items-center justify-center gap-2 shadow-sm shadow-amber-500/10 active:scale-98 cursor-pointer";
            importBtn.onclick = function() { triggerSimBriefImport(); };
            importBtn.innerHTML = `<i id="sb-import-icon" class="fa-solid fa-cloud-arrow-down text-amber-400"></i> <span>Import Active SimBrief OFP</span>`;
        }
    }
}

function restoreAllFlightSceneriesUI() {
    if (!window.pywebview) return;
    const apiFn = window.pywebview.api.restore_all_sceneries || window.pywebview.api.restore_all_flight_sceneries;
    apiFn.call(window.pywebview.api).then(resStr => {
        try {
            const res = JSON.parse(resStr);
            if (res.status === 'ok' || res.status === 'success') {
                if (res.airports && res.airports.length > 0) {
                    allAirportsData = res.airports;
                }
                isFlightOptimizerActive = false;
                updateFlightModeBannerUI({ active: false, icaos: [] });
                filterAirports();
                showCustomModal(
                    'Sceneries Restored 🟢',
                    'All 3rd-party airport sceneries have been restored to their active state.',
                    'success'
                );
            } else {
                showCustomModal('Restore Error', res.message || "Failed to restore sceneries.", 'error');
            }
        } catch(e){
            console.error("Error parsing restore result:", e);
        }
    }).catch(err => {
        showCustomModal('Restore Error', String(err), 'error');
    });
}

