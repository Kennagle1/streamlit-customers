import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from rapidfuzz import fuzz
from datetime import datetime
import io
import re

# -----------------------------------------------
# PAGE CONFIG
# -----------------------------------------------
st.set_page_config(page_title="Fenergo | Account Intelligence", layout="wide", page_icon="🏦")

# -----------------------------------------------
# FENERGO BRAND STYLING
# Deep Teal: #002E33 | Java Turquoise: #21CFB2 | White: #FFFFFF
# -----------------------------------------------
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #f5f7f7; }

    /* Top header bar */
    .fenergo-header {
        background-color: #002E33;
        padding: 18px 32px;
        border-radius: 8px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
    }
    .fenergo-header h1 {
        color: #21CFB2;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        font-family: sans-serif;
        letter-spacing: 0.5px;
    }
    .fenergo-header span {
        color: #ffffff;
        font-size: 1.6rem;
        font-weight: 700;
        font-family: sans-serif;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #002E33 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .stFileUploader label {
        color: #21CFB2 !important;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #002E33;
        border-radius: 8px 8px 0 0;
        padding: 0 8px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #a0bfbf !important;
        background-color: transparent !important;
        border-radius: 6px 6px 0 0 !important;
        padding: 10px 20px !important;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #21CFB2 !important;
        color: #002E33 !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #ffffff;
        border-radius: 0 0 8px 8px;
        padding: 24px;
        border: 1px solid #dde8e8;
    }

    /* Cards */
    .fen-card {
        background: #ffffff;
        border-left: 4px solid #21CFB2;
        border-radius: 6px;
        padding: 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 4px rgba(0,46,51,0.08);
    }
    .fen-card h4 {
        color: #002E33;
        margin-top: 0;
        margin-bottom: 12px;
        font-size: 0.95rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background-color: #21CFB2 !important;
        color: #002E33 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1ab89d !important;
    }

    /* Section headers */
    .fen-section-title {
        color: #002E33;
        font-weight: 700;
        font-size: 1rem;
        border-bottom: 2px solid #21CFB2;
        padding-bottom: 6px;
        margin-bottom: 16px;
    }

    /* Placeholder tab content */
    .placeholder-box {
        background: #f0f9f8;
        border: 2px dashed #21CFB2;
        border-radius: 8px;
        padding: 60px 40px;
        text-align: center;
        color: #002E33;
    }
    .placeholder-box h3 { color: #002E33; font-size: 1.3rem; }
    .placeholder-box p { color: #5a7a7a; font-size: 0.95rem; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="fenergo-header">
    <h1>fener<span style="color:#21CFB2">g</span><span style="color:#ffffff">o</span>&nbsp;&nbsp;|&nbsp;&nbsp;</h1>
    <span>&nbsp;Account Intelligence</span>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------
# APPROVED SEGMENTATION HIERARCHY
# -----------------------------------------------
SEGMENT_HIERARCHY = [
    ("Alternative Asset Management",                   "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
    ("Asset Management",                               "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
    ("Hedge Funds",                                    "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
    ("Investech",                                      "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
    ("Pension Funds",                                  "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
    ("Private Banking",                                "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
    ("Real Estate",                                    "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
    ("Sovereign Wealth Funds",                         "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
    ("Wealth Management",                              "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
    ("Family Offices",                                 "Asset & Wealth Mgmt.",           "Asset Mgmt., Servicing & Insurance"),
    ("Asset Servicing",                                "Asset Servicing",                "Asset Mgmt., Servicing & Insurance"),
    ("Custodian",                                      "Asset Servicing",                "Asset Mgmt., Servicing & Insurance"),
    ("Insurance",                                      "Insurance",                      "Asset Mgmt., Servicing & Insurance"),
    ("Insurtech",                                      "Insurance",                      "Asset Mgmt., Servicing & Insurance"),
    ("Brokerage/Broker-dealer",                        "Transaction & Trust Activities", "Asset Mgmt., Servicing & Insurance"),
    ("Clearing House",                                 "Transaction & Trust Activities", "Asset Mgmt., Servicing & Insurance"),
    ("Transaction & Trust Activities",                 "Transaction & Trust Activities", "Asset Mgmt., Servicing & Insurance"),
    ("Investment / Institutional Banking",             "C&IB",                           "Banks"),
    ("Central Banking",                                "Commercial & Business",          "Banks"),
    ("Commercial Banking",                             "Commercial & Business",          "Banks"),
    ("Business Banking",                               "Commercial & Business",          "Banks"),
    ("Financial Services",                             "Commercial & Business",          "Banks"),
    ("Community Bank",                                 "Retail",                         "Banks"),
    ("Credit Union",                                   "Retail",                         "Banks"),
    ("Retail Banking",                                 "Retail",                         "Banks"),
    ("Mutual Savings Bank",                            "Retail",                         "Banks"),
    ("Exchanges and Commodity Trading",                "Exchanges and Commodity trading","Corporates"),
    ("Market Maker",                                   "Exchanges and Commodity trading","Corporates"),
    ("Oil & Gas",                                      "Oil & Gas",                      "Corporates"),
    ("Energy",                                         "Energy",                         "Corporates"),
    ("Renewable Energy",                               "Energy",                         "Corporates"),
    ("Banking as a Service",                           "Fintech",                        "Fintech"),
    ("Crypto",                                         "Fintech",                        "Fintech"),
    ("Digital Banks",                                  "Fintech",                        "Fintech"),
    ("Embedded Finance & BNPL",                        "Fintech",                        "Fintech"),
    ("E-money Institutions",                           "Fintech",                        "Fintech"),
    ("Fintech",                                        "Fintech",                        "Fintech"),
    ("Marketplaces",                                   "Fintech",                        "Fintech"),
    ("Money Services Business",                        "Fintech",                        "Fintech"),
    ("Neo Banks",                                      "Fintech",                        "Fintech"),
    ("Open Banking",                                   "Fintech",                        "Fintech"),
    ("Payments Service Provider",                      "Fintech",                        "Fintech"),
    ("Remittance",                                     "Fintech",                        "Fintech"),
    ("Gaming and Gambling",                            "Fintech",                        "Fintech"),
    ("Proptech",                                       "Fintech",                        "Fintech"),
    ("Full-Service Banks",                             "Full-Service Banks",             "Full-Service Banks"),
    ("Precious Metals and Jewellery",                  "Other",                          "Other"),
    ("Legal and Accounting Services",                  "Other",                          "Other"),
    ("Other",                                          "Other",                          "Other"),
    ("Professional Services",                          "Other",                          "Other"),
    ("Other Corporates",                               "Other",                          "Other"),
    ("Building Society",                               "Other",                          "Other"),
    ("Aviation and Aerospace Component Manufacturing", "Other",                          "Other"),
    ("High Value Goods and Luxury Items",              "Other",                          "Other"),
]

SEGMENT_LOOKUP = {
    row[0].lower(): {"detailed": row[0], "business": row[1], "market": row[2]}
    for row in SEGMENT_HIERARCHY
}
VALID_DETAILED_SEGMENTS = [row[0] for row in SEGMENT_HIERARCHY]
VALID_BUSINESS_SEGMENTS = list(dict.fromkeys(row[1] for row in SEGMENT_HIERARCHY))
VALID_MARKET_SEGMENTS   = list(dict.fromkeys(row[2] for row in SEGMENT_HIERARCHY))

# -----------------------------------------------
# G-SIB & D-SIB LISTS
# -----------------------------------------------
GSIB_LIST = [
    "jpmorgan chase", "bank of america", "citigroup", "wells fargo",
    "goldman sachs", "morgan stanley", "bank of new york mellon", "state street",
    "hsbc", "barclays", "standard chartered", "lloyds banking group", "natwest",
    "bnp paribas", "credit agricole", "groupe bpce", "societe generale",
    "deutsche bank", "unicredit", "ing group", "santander", "bbva",
    "ubs", "credit suisse",
    "mitsubishi ufj", "mizuho", "sumitomo mitsui",
    "bank of china", "icbc", "china construction bank", "agricultural bank of china",
    "bank of communications",
    "royal bank of canada", "toronto dominion", "td bank",
]

DSIB_LIST = {
    "ireland":      ["bank of ireland", "allied irish banks", "aib", "permanent tsb", "ulster bank"],
    "uk":           ["nationwide", "santander uk", "virgin money", "metro bank", "co-operative bank"],
    "germany":      ["commerzbank", "dz bank", "landesbank baden-wurttemberg", "lbbw", "bayerische landesbank", "norddeutsche landesbank"],
    "france":       ["la banque postale", "credit mutuel"],
    "netherlands":  ["rabobank", "abn amro"],
    "spain":        ["caixabank", "bankinter", "sabadell"],
    "italy":        ["intesa sanpaolo", "mediobanca"],
    "switzerland":  ["zuercher kantonalbank", "raiffeisen switzerland", "postfinance"],
    "australia":    ["commonwealth bank", "westpac", "anz", "nab", "national australia bank", "macquarie"],
    "canada":       ["bank of nova scotia", "scotiabank", "bank of montreal", "bmo", "canadian imperial bank", "cibc", "national bank of canada"],
    "singapore":    ["dbs", "ocbc", "uob"],
    "hong kong":    ["hang seng bank", "bank of east asia"],
    "india":        ["state bank of india", "sbi", "hdfc bank", "icici bank", "axis bank", "kotak mahindra"],
    "south africa": ["standard bank", "firstrand", "absa", "nedbank", "capitec"],
    "brazil":       ["itau unibanco", "bradesco", "caixa economica", "banco do brasil"],
    "sweden":       ["swedbank", "seb", "handelsbanken"],
    "norway":       ["dnb"],
    "denmark":      ["danske bank", "jyske bank", "sydbank"],
    "belgium":      ["kbc", "belfius"],
    "austria":      ["erste group", "raiffeisen bank international"],
    "poland":       ["pko bank polski", "pko bp", "bank pekao"],
    "uae":          ["emirates nbd", "first abu dhabi bank", "fab", "abu dhabi commercial bank", "adcb"],
    "saudi arabia": ["al rajhi bank", "national commercial bank", "snb", "samba financial"],
    "malaysia":     ["maybank", "cimb", "public bank", "rhb bank", "hong leong bank"],
    "new zealand":  ["anz new zealand", "westpac new zealand", "bnz", "asb bank", "kiwibank"],
}
DSIB_FLAT = [name for names in DSIB_LIST.values() for name in names]

# -----------------------------------------------
# SIDEBAR
# -----------------------------------------------
st.sidebar.markdown("### Account Intelligence")
st.sidebar.markdown("---")
st.sidebar.markdown("**📂 Salesforce Account List**")
uploaded_file = st.sidebar.file_uploader("Upload Salesforce Accounts CSV", type=["csv"])
sf_accounts = None
if uploaded_file:
    sf_accounts = pd.read_csv(uploaded_file)
    st.sidebar.success(f"✅ Loaded {len(sf_accounts)} accounts")
    with st.sidebar.expander("Preview"):
        st.dataframe(sf_accounts.head())

# -----------------------------------------------
# LOAD ACCOUNT CATEGORY MATRIX
# -----------------------------------------------
@st.cache_data
def load_account_category_matrix():
    try:
        df = pd.read_excel("account_category_matrix.xlsx", header=[0, 1], index_col=0)
        df.columns = pd.MultiIndex.from_arrays([
            pd.Series(df.columns.get_level_values(0)).ffill().values,
            df.columns.get_level_values(1)
        ])
        lookup = {}
        for country in df.index:
            if pd.isna(country):
                continue
            country_clean = str(country).strip().lower()
            for (business_seg, customer_seg) in df.columns:
                value = df.loc[country, (business_seg, customer_seg)]
                if pd.notna(value):
                    lookup[(
                        country_clean,
                        str(business_seg).strip().lower(),
                        str(customer_seg).strip().lower()
                    )] = str(value).strip()
        return lookup, None
    except FileNotFoundError:
        return {}, "account_category_matrix.xlsx not found in repo root"
    except Exception as e:
        return {}, f"Error loading matrix: {str(e)}"

matrix_lookup, matrix_error = load_account_category_matrix()
if matrix_error:
    st.sidebar.warning(matrix_error)
else:
    st.sidebar.success(f"✅ Matrix loaded ({len(set(k[0] for k in matrix_lookup.keys()))} countries)")

# -----------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------
def generate_name_variations(name):
    variations = [name.lower().strip()]
    words = name.lower().split()
    initials = ''.join(w[0] for w in words if w not in ['of', 'the', 'and', '&'])
    if len(initials) >= 2:
        variations.append(initials)
    known = {
        "bank of ireland": ["boi"],
        "bank of america": ["boa", "bofa"],
        "jpmorgan chase": ["jpm", "jpmorgan"],
        "hsbc holdings": ["hsbc"],
        "deutsche bank": ["db"],
        "ubs group": ["ubs"],
        "standard chartered": ["stan chart", "stanchart"],
    }
    for key, abbrevs in known.items():
        if key in name.lower():
            variations.extend(abbrevs)
    return list(set(variations))

def normalize_name(name):
    """Strip common legal entity suffixes and normalise whitespace for fuzzy matching."""
    s = str(name).strip().lower()
    s = re.sub(r'[.,\-]', ' ', s)
    legal_suffixes = [
        r'\bpty\s+ltd\b', r'\bpte\s+ltd\b', r'\bltd\b', r'\bllc\b', r'\binc\b',
        r'\bcorp\b', r'\bcorporation\b', r'\bplc\b', r'\bag\b',
        r'\bsrl\b', r'\bgmbh\b', r'\bbv\b', r'\bnv\b', r'\bspa\b',
        r'\blimited\b', r'\bincorporated\b', r'\bholdings?\b',
        r'\bco\b', r'\bcompany\b',
    ]
    for suffix in legal_suffixes:
        s = re.sub(suffix, ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def check_duplicate(sf_accounts, account_name, region, country):
    if sf_accounts is None:
        return [], "No Salesforce account list uploaded — skipping duplicate check"
    variations = generate_name_variations(account_name)
    matches = []
    for _, row in sf_accounts.iterrows():
        row_name = str(
            row.get('Account Name', row.get('Name', row.get('account_name', row.iloc[0])))
        ).lower().strip()
        for var in variations:
            if var in row_name or row_name in var or (len(var) > 4 and var in row_name):
                row_region  = str(row.get('Region', row.get('region', ''))).strip()
                row_country = str(row.get('Country', row.get('country', ''))).strip()
                same_region  = region.lower() in row_region.lower() or row_region.lower() in region.lower()
                same_country = country.lower() in row_country.lower() or row_country.lower() in country.lower()
                matches.append({
                    'Matched Account Name': row.get('Account Name', row.get('Name', row.iloc[0])),
                    'Region':      row_region  or 'Unknown',
                    'Country':     row_country or 'Unknown',
                    'Same Region':  '🔴 Yes' if same_region  else '🟢 No',
                    'Same Country': '🔴 Yes' if same_country else '🟢 No',
                })
                break
    return matches, None

def parse_numeric(value_str):
    if not value_str or value_str in ('Not found', 'N/A', 'Unknown'):
        return None
    s = str(value_str).lower().replace(',', '').replace('$', '').replace('€', '').replace('£', '').strip()
    multiplier = 1.0
    if s.endswith('bn') or s.endswith('b'):
        s = s.rstrip('n').rstrip('b')
    elif s.endswith('m'):
        multiplier = 0.001
        s = s.rstrip('m')
    elif s.endswith('k'):
        multiplier = 0.000001
        s = s.rstrip('k')
    try:
        return float(s) * multiplier
    except ValueError:
        return None

def parse_employees(value_str):
    if not value_str or value_str in ('Not found', 'N/A', 'Unknown'):
        return None
    s = str(value_str).lower().replace(',', '').strip()
    match = re.search(r'[\d.]+', s)
    if not match:
        return None
    num = float(match.group())
    if 'k' in s:
        num *= 1000
    return int(num)

def resolve_segment(detailed_segment_guess):
    if not detailed_segment_guess:
        return None
    guess = detailed_segment_guess.lower().strip()
    if guess in SEGMENT_LOOKUP:
        return SEGMENT_LOOKUP[guess]
    for key, value in SEGMENT_LOOKUP.items():
        if guess in key or key in guess:
            return value
    return None

# -----------------------------------------------
# G-SIB / D-SIB CHECKS
# -----------------------------------------------
def is_gsib(account_name):
    name_lower = account_name.lower()
    return any(g in name_lower or name_lower in g for g in GSIB_LIST)

def is_dsib(account_name):
    name_lower = account_name.lower()
    return any(d in name_lower or name_lower in d for d in DSIB_FLAT)

def check_full_service_bank_eligibility(account_name):
    if is_gsib(account_name):
        return True, "G-SIB", None
    if is_dsib(account_name):
        return True, "D-SIB (static list match)", (
            "D-SIB match found on static list — please confirm against your "
            "local regulator's current D-SIB designation before assigning Full-Service Banks."
        )
    return False, "Neither G-SIB nor D-SIB", (
        "This institution is not on the G-SIB list and was not found on the static D-SIB list. "
        "It has been classified as Banks. If you believe this is a D-SIB, verify with the "
        "relevant local regulator and override manually."
    )

# -----------------------------------------------
# CUSTOMER SEGMENT LOGIC
# -----------------------------------------------
def classify_customer_segment(market_segment, aum_bn, revenue_bn, employees, account_name=""):
    all_unknown = aum_bn is None and revenue_bn is None and employees is None
    if all_unknown:
        return "Scale-up", "All metrics unknown — defaulting to Scale-up per business rules."

    seg = (market_segment or '').strip()

    def tier(e_hit, m_hit, parts):
        rationale = " | ".join(parts) if parts else "Insufficient data"
        if e_hit:
            return "Enterprise", rationale
        if m_hit:
            return "Mid-Market", rationale
        return "Scale-up", rationale

    if seg == "Full-Service Banks":
        eligible, classification, warning = check_full_service_bank_eligibility(account_name)
        if eligible:
            msg = f"Confirmed {classification} — Full-Service Banks classification applied."
            if warning:
                msg += f" | {warning}"
            return "Enterprise", msg
        else:
            return classify_customer_segment("Banks", aum_bn, revenue_bn, employees, account_name)

    if seg == "Banks":
        e, m, parts = False, False, []
        if aum_bn is not None:
            if aum_bn > 200:
                e = True; parts.append(f"AUM {aum_bn:.1f}bn > 200bn (Enterprise)")
            elif aum_bn >= 10:
                m = True; parts.append(f"AUM {aum_bn:.1f}bn in 10-200bn (Mid-Market)")
            else:
                parts.append(f"AUM {aum_bn:.1f}bn < 10bn (Scale-up)")
        if revenue_bn is not None:
            if revenue_bn > 10:
                e = True; parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
            elif revenue_bn >= 2:
                m = True; parts.append(f"Revenue {revenue_bn:.1f}bn in 2-10bn (Mid-Market)")
            else:
                parts.append(f"Revenue {revenue_bn:.1f}bn < 2bn (Scale-up)")
        if employees is not None:
            if employees > 5000:
                e = True; parts.append(f"{employees:,} FTE > 5,000 (Enterprise)")
            elif employees >= 1000:
                m = True; parts.append(f"{employees:,} FTE in 1,000-5,000 (Mid-Market)")
            else:
                parts.append(f"{employees:,} FTE < 1,000 (Scale-up)")
        return tier(e, m, parts)

    if seg == "Asset Mgmt., Servicing & Insurance":
        e, m, parts = False, False, []
        if aum_bn is not None:
            if aum_bn > 100:
                e = True; parts.append(f"AUM {aum_bn:.1f}bn > 100bn (Enterprise)")
            elif aum_bn >= 10:
                m = True; parts.append(f"AUM {aum_bn:.1f}bn in 10-100bn (Mid-Market)")
            else:
                parts.append(f"AUM {aum_bn:.1f}bn < 10bn (Scale-up)")
        if revenue_bn is not None:
            if revenue_bn > 10:
                e = True; parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
            elif revenue_bn >= 2:
                m = True; parts.append(f"Revenue {revenue_bn:.1f}bn in 2-10bn (Mid-Market)")
            else:
                parts.append(f"Revenue {revenue_bn:.1f}bn < 2bn (Scale-up)")
        if employees is not None:
            if employees > 1000:
                e = True; parts.append(f"{employees:,} FTE > 1,000 (Enterprise)")
            elif employees >= 150:
                m = True; parts.append(f"{employees:,} FTE in 150-1,000 (Mid-Market)")
            else:
                parts.append(f"{employees:,} FTE < 150 (Scale-up)")
        return tier(e, m, parts)

    if seg == "Corporates":
        e, m, parts = False, False, []
        if revenue_bn is not None:
            if revenue_bn > 10:
                e = True; parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
            elif revenue_bn >= 2:
                m = True; parts.append(f"Revenue {revenue_bn:.1f}bn in 2-10bn (Mid-Market)")
            else:
                parts.append(f"Revenue {revenue_bn:.1f}bn < 2bn (Scale-up)")
        if employees is not None:
            if employees > 5000:
                e = True; parts.append(f"{employees:,} FTE > 5,000 (Enterprise)")
            elif employees >= 1000:
                m = True; parts.append(f"{employees:,} FTE in 1,000-5,000 (Mid-Market)")
            else:
                parts.append(f"{employees:,} FTE < 1,000 (Scale-up)")
        return tier(e, m, parts)

    if seg == "Fintech":
        e, m, parts = False, False, []
        if revenue_bn is not None:
            if revenue_bn > 10:
                e = True; parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
            elif revenue_bn >= 0.5:
                m = True; parts.append(f"Revenue {revenue_bn:.1f}bn in 0.5-10bn (Mid-Market)")
            else:
                parts.append(f"Revenue {revenue_bn:.1f}bn < 500m (Scale-up)")
        if employees is not None:
            if employees > 1000:
                e = True; parts.append(f"{employees:,} FTE > 1,000 (Enterprise)")
            elif employees >= 250:
                m = True; parts.append(f"{employees:,} FTE in 250-1,000 (Mid-Market)")
            else:
                parts.append(f"{employees:,} FTE < 250 (Scale-up)")
        return tier(e, m, parts)

    e, m, parts = False, False, []
    if revenue_bn is not None:
        if revenue_bn > 10:
            e = True; parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
        elif revenue_bn >= 2:
            m = True; parts.append(f"Revenue {revenue_bn:.1f}bn in 2-10bn (Mid-Market)")
        else:
            parts.append(f"Revenue {revenue_bn:.1f}bn < 2bn (Scale-up)")
    if employees is not None:
        if employees > 5000:
            e = True; parts.append(f"{employees:,} FTE > 5,000 (Enterprise)")
        elif employees >= 1000:
            m = True; parts.append(f"{employees:,} FTE in 1,000-5,000 (Mid-Market)")
        else:
            parts.append(f"{employees:,} FTE < 1,000 (Scale-up)")
    return tier(e, m, parts)

# -----------------------------------------------
# ACCOUNT CATEGORY LOOKUP
# -----------------------------------------------
def fuzzy_country_match(country_input, lookup_keys):
    country_lower = country_input.strip().lower()
    aliases = {
        "usa": "united states", "us": "united states", "u.s.": "united states",
        "u.s.a.": "united states", "uk": "united kingdom", "u.k.": "united kingdom",
        "uae": "united arab emirates", "u.a.e.": "united arab emirates",
        "korea": "south korea", "republic of ireland": "ireland", "eire": "ireland",
    }
    country_lower = aliases.get(country_lower, country_lower)
    if country_lower in lookup_keys:
        return country_lower
    for key in lookup_keys:
        if country_lower in key or key in country_lower:
            return key
    return None

def get_account_category(country, business_segment, customer_segment, matrix_lookup):
    if not matrix_lookup:
        return "Matrix not loaded", "Matrix file could not be loaded"
    country_keys = set(k[0] for k in matrix_lookup.keys())
    matched_country = fuzzy_country_match(country, country_keys)
    if not matched_country:
        return "No match found", f"Country '{country}' not found in matrix"
    lookup_key = (matched_country, str(business_segment).strip().lower(), str(customer_segment).strip().lower())
    if lookup_key in matrix_lookup:
        return matrix_lookup[lookup_key], f"Matched: {matched_country.title()} | {business_segment} | {customer_segment}"
    return "No match found", f"No matrix entry for {matched_country.title()} + {business_segment} + {customer_segment}"

# -----------------------------------------------
# SECONDARY ACCOUNT OWNER
# -----------------------------------------------
def get_secondary_account_owner(region, account_category):
    region_upper = (region or '').upper()
    if "AMER" in region_upper or "AMERICAS" in region_upper:
        if account_category and "cat 1" in str(account_category).lower():
            return "Elaine Zhang"
        else:
            current_month = datetime.now().month
            if current_month % 2 == 1:
                return f"Joseph Cawley (current month: {datetime.now().strftime('%B')})"
            else:
                return f"Gabriel Simpatico (current month: {datetime.now().strftime('%B')})"
    if "EMEA" in region_upper:
        return "Elaine Zhang"
    if "APAC" in region_upper:
        return "Vernis Tan"
    if "UK" in region_upper or "IRELAND" in region_upper:
        return "Elaine Zhang"
    return "Region not recognised — please assign manually"

# -----------------------------------------------
# WEB RESEARCH
# -----------------------------------------------
def web_research(account_name):
    data = {
        'legal_name': 'Not found', 'country_hq': 'Not found',
        'annual_revenue_eur': 'Not found', 'employees': 'Not found',
        'aum_eur': 'N/A', 'ultimate_parent': 'Not found',
        'ultimate_parent_hq': 'Not found',
        'detailed_business_segment': 'Not found',
        'business_segment': 'Not found', 'market_segment': 'Not found',
        'sources': [], 'snippets': []
    }
    queries = [
        f"{account_name} annual revenue employees headquarters",
        f"{account_name} legal name parent company",
        f"{account_name} AUM assets under management",
        f"{account_name} industry type financial services",
    ]
    try:
        with DDGS() as ddgs:
            for query in queries:
                results = list(ddgs.text(query, max_results=3))
                for r in results:
                    if r.get('href') and r['href'] not in data['sources']:
                        data['sources'].append(r['href'])
                    if r.get('body'):
                        data['snippets'].append({
                            'query':   query,
                            'source':  r.get('href', ''),
                            'snippet': r.get('body', '')
                        })
    except Exception as e:
        data['error'] = str(e)
    return data

# -----------------------------------------------
# FULL SEGMENTATION
# -----------------------------------------------
def apply_segmentation(research_data, account_name="", region="", country=""):
    market_segment   = research_data.get('market_segment', '')
    business_segment = research_data.get('business_segment', '')
    aum_bn     = parse_numeric(research_data.get('aum_eur', ''))
    revenue_bn = parse_numeric(research_data.get('annual_revenue_eur', ''))
    employees  = parse_employees(research_data.get('employees', ''))
    customer_segment, rationale = classify_customer_segment(
        market_segment, aum_bn, revenue_bn, employees, account_name
    )
    account_category, category_note = get_account_category(
        country, business_segment, customer_segment, matrix_lookup
    )
    secondary_owner = get_secondary_account_owner(region, account_category)
    return {
        'customer_segment':           customer_segment,
        'customer_segment_rationale': rationale,
        'account_category':           account_category,
        'account_category_note':      category_note,
        'secondary_account_owner':    secondary_owner,
    }

# -----------------------------------------------
# TABS
# -----------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Customer Attributes", "Lead Matching", "Account Matching", "ICP Analysis"])

# ===============================================
# TAB 1 — CUSTOMER ATTRIBUTES
# ===============================================
with tab1:

    st.markdown('<p class="fen-section-title">Enter Account Details</p>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        account_name = st.text_input("Account Name *", placeholder="e.g. Bank of Ireland")
    with col2:
        account_type = st.selectbox("Account Type *", ["Other", "Partner"])
    with col3:
        region = st.selectbox("Region *", ["EMEA", "APAC", "Americas", "UK & Ireland"])
    with col4:
        country = st.text_input("Country *", placeholder="e.g. Ireland")

    run_button = st.button("Run Enrichment Checks", type="primary", use_container_width=True)

    if run_button:
        if not account_name.strip() or not region or not country.strip():
            st.error("Please fill in all required fields: Account Name, Region, and Country.")
            st.stop()

        st.divider()
        st.markdown(f'<p class="fen-section-title">Running checks for: {account_name}</p>', unsafe_allow_html=True)

        # PARTNER ACCOUNT FLOW
        if account_type == "Partner":
            st.info("Partner Account — only a Region/Country duplicate check is required.")
            with st.status("Checking for existing Partner account...", expanded=True) as status:
                st.write(f"Searching for `{account_name}` in region `{region}` / country `{country}`...")
                st.write(f"Also checking variations: {generate_name_variations(account_name)}")
                matches, warning = check_duplicate(sf_accounts, account_name, region, country)
                if warning:
                    st.warning(warning)
                    status.update(label="Duplicate check skipped — no file uploaded", state="error")
                elif matches:
                    same_region = [m for m in matches if '🔴' in m['Same Region']]
                    if same_region:
                        st.error("Existing Partner account found in the same region!")
                        st.dataframe(pd.DataFrame(same_region), use_container_width=True, hide_index=True)
                        st.warning("Please check with Ken before proceeding.")
                        status.update(label="Duplicate detected — escalate to Ken", state="error")
                    else:
                        st.warning("Similar account name found but in a different region — review below:")
                        st.dataframe(pd.DataFrame(matches), use_container_width=True, hide_index=True)
                        status.update(label="Similar account found (different region)", state="complete")
                else:
                    st.success(f"No existing Partner account found for {account_name} in {region} / {country}")
                    status.update(label="No duplicate found — safe to proceed", state="complete")

        # ALL OTHER ACCOUNTS FLOW
        else:
            duplicate_ok = True

            with st.status("Step 1 of 3: Checking for existing account in Salesforce...", expanded=True) as status:
                st.write(f"Searching for `{account_name}` and variations: {generate_name_variations(account_name)}")
                matches, warning = check_duplicate(sf_accounts, account_name, region, country)
                if warning:
                    st.warning(warning)
                    status.update(label="Step 1: Duplicate check skipped — no file uploaded", state="error")
                elif matches:
                    same_region = [m for m in matches if '🔴' in m['Same Region']]
                    if same_region:
                        st.error("Potential duplicate found in the same region!")
                        st.dataframe(pd.DataFrame(same_region), use_container_width=True, hide_index=True)
                        st.warning("Please check with Ken before proceeding. Enrichment has been paused.")
                        status.update(label="Step 1: Duplicate detected — check with Ken", state="error")
                        duplicate_ok = False
                    else:
                        st.warning("Similar name found but in a different region:")
                        st.dataframe(pd.DataFrame(matches), use_container_width=True, hide_index=True)
                        st.info("Proceeding with enrichment — review the match above carefully.")
                        status.update(label="Step 1: Similar name (different region) — review carefully", state="complete")
                else:
                    st.success(f"No existing account found for {account_name} in {region}")
                    status.update(label="Step 1: No duplicate found", state="complete")

            if not duplicate_ok:
                st.stop()

            research = {}
            with st.status("Step 2 of 3: Researching company on the web...", expanded=True) as status:
                st.write("Querying: revenue, employees, HQ, legal name, parent company, AUM, industry")
                st.write("Sources: DuckDuckGo → company site, Wikipedia, Bloomberg, Reuters, Crunchbase")
                research = web_research(account_name)
                if 'error' in research:
                    st.error(f"Search error: {research['error']}")
                    status.update(label="Step 2: Web research failed", state="error")
                else:
                    st.write(f"Retrieved {len(research['snippets'])} results from {len(research['sources'])} sources")
                    for src in research['sources'][:4]:
                        st.write(f"  - {src}")
                    status.update(label=f"Step 2: Web research complete ({len(research['sources'])} sources)", state="complete")

            segmentation = {}
            with st.status("Step 3 of 3: Applying segmentation logic...", expanded=True) as status:
                st.write("Applying Customer Segment, Account Category and Secondary Owner rules...")
                segmentation = apply_segmentation(research, account_name, region, country)
                seg    = segmentation.get('customer_segment', '')
                colour = {"Enterprise": "🔵", "Mid-Market": "🟡", "Scale-up": "🟢"}.get(seg, "⚪")
                st.write(f"{colour} Customer Segment: {seg}")
                rationale = segmentation.get('customer_segment_rationale', '')
                if "warning" in rationale.lower() or "verify" in rationale.lower():
                    st.warning(rationale)
                else:
                    st.caption(f"Rationale: {rationale}")
                status.update(label=f"Step 3: Segmentation complete — {seg}", state="complete")

            # RESULTS
            st.divider()
            st.markdown('<p class="fen-section-title">Enrichment Results</p>', unsafe_allow_html=True)

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown('<div class="fen-card"><h4>Segment Information</h4>', unsafe_allow_html=True)
                st.dataframe(pd.DataFrame({
                    "Field": ["Detailed Business Segment", "Business Segment", "Market Segment"],
                    "Value": [
                        research.get('detailed_business_segment', 'N/A'),
                        research.get('business_segment', 'N/A'),
                        research.get('market_segment', 'N/A'),
                    ]
                }), use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="fen-card"><h4>Parent Information</h4>', unsafe_allow_html=True)
                st.dataframe(pd.DataFrame({
                    "Field": ["Ultimate Parent", "Ultimate Parent HQ"],
                    "Value": [
                        research.get('ultimate_parent', 'N/A'),
                        research.get('ultimate_parent_hq', 'N/A'),
                    ]
                }), use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col_b:
                st.markdown('<div class="fen-card"><h4>Company Metrics</h4>', unsafe_allow_html=True)
                aum_segments = ['Full-Service Banks', 'Banks', 'Asset Mgmt., Servicing & Insurance']
                show_aum = research.get('market_segment', '') in aum_segments
                metrics_fields = ["Legal Name", "Country HQ", "Annual Revenue (EUR)", "Employees"]
                metrics_values = [
                    research.get('legal_name', 'N/A'),
                    research.get('country_hq', 'N/A'),
                    research.get('annual_revenue_eur', 'N/A'),
                    research.get('employees', 'N/A'),
                ]
                if show_aum:
                    metrics_fields.append("AUM (EUR)")
                    metrics_values.append(research.get('aum_eur', 'N/A'))
                st.dataframe(pd.DataFrame({
                    "Field": metrics_fields,
                    "Value": metrics_values
                }), use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="fen-card"><h4>Account Categorisation</h4>', unsafe_allow_html=True)
                seg    = segmentation.get('customer_segment', 'N/A')
                colour = {"Enterprise": "🔵", "Mid-Market": "🟡", "Scale-up": "🟢"}.get(seg, "⚪")
                st.dataframe(pd.DataFrame({
                    "Field": [
                        "Customer Segment",
                        "Segment Rationale",
                        "Account Category",
                        "Account Category Note",
                        "Secondary Account Owner",
                    ],
                    "Value": [
                        f"{colour} {seg}",
                        segmentation.get('customer_segment_rationale', 'N/A'),
                        segmentation.get('account_category', 'N/A'),
                        segmentation.get('account_category_note', 'N/A'),
                        segmentation.get('secondary_account_owner', 'N/A'),
                    ]
                }), use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with st.expander("View raw web search results (for manual review)"):
                for i, item in enumerate(research.get('snippets', []), 1):
                    st.markdown(f"**Result {i}** — _{item['query']}_")
                    st.write(f"Source: {item['source']}")
                    st.write(item['snippet'])
                    st.divider()

# ===============================================
# TAB 2 — LEAD MATCHING (placeholder)
# ===============================================
with tab2:
    st.markdown("""
    <div class="placeholder-box">
        <h3>Lead Matching</h3>
        <p>This module is coming soon.<br>
        It will automatically match enriched accounts against open leads in Salesforce,<br>
        surfacing potential overlaps and routing recommendations.</p>
    </div>
    """, unsafe_allow_html=True)

# ===============================================
# TAB 3 — ACCOUNT MATCHING
# ===============================================
with tab3:
    st.markdown('<p class="fen-section-title">Account Matching</p>', unsafe_allow_html=True)
    NO_VALUE_PLACEHOLDER = "—"
    HIGH_CONFIDENCE_THRESHOLD = 80

    st.markdown("""
    Upload a **New Customer** file (CSV or Excel) containing a list of customer names.  
    The tool will fuzzy-match each name against **Account Name**, **Reporting Group**, **Ultimate Parent**,  
    and **Legal Name** in the **Salesforce Accounts CSV** uploaded in the sidebar,  
    returning a confidence score, a primary suggested match, and a secondary match where applicable.
    """)

    new_customer_file = st.file_uploader(
        "Upload New Customer File (CSV or Excel)",
        type=["csv", "xlsx", "xls"],
        key="account_matching_upload"
    )

    if new_customer_file is not None:
        try:
            if new_customer_file.name.endswith(('.xlsx', '.xls')):
                new_customers_df = pd.read_excel(new_customer_file)
            else:
                new_customers_df = pd.read_csv(new_customer_file)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()

        name_col_candidates = [c for c in new_customers_df.columns if any(
            kw in c.lower() for kw in ['name', 'account', 'customer', 'company', 'organisation', 'organization']
        )]
        if name_col_candidates:
            default_col = name_col_candidates[0]
        else:
            default_col = new_customers_df.columns[0]

        name_column = st.selectbox(
            "Select the column containing customer names:",
            options=new_customers_df.columns.tolist(),
            index=new_customers_df.columns.tolist().index(default_col)
        )

        st.info(f"📋 Loaded **{len(new_customers_df)}** new customers from uploaded file.")

        if sf_accounts is None:
            st.warning("⚠️ No Salesforce Accounts CSV uploaded. Please upload it in the sidebar first.")
        else:
            sf_columns = sf_accounts.columns.tolist()
            sf_columns_lc = {c: c.lower() for c in sf_columns}

            def pick_col(primary_terms, secondary_terms=None, exclude_terms=None):
                secondary_terms = secondary_terms or []
                exclude_terms = exclude_terms or []
                candidates = [
                    c for c in sf_columns
                    if not any(ex in sf_columns_lc[c] for ex in exclude_terms)
                ]
                for term in primary_terms:
                    for c in candidates:
                        if term in sf_columns_lc[c]:
                            return c
                for term in secondary_terms:
                    for c in candidates:
                        if term in sf_columns_lc[c]:
                            return c
                return None

            account_col_candidates = [c for c in sf_columns if 'id' not in sf_columns_lc[c]]
            sf_account_name_col = next(
                (c for c in account_col_candidates if sf_columns_lc[c].strip() == 'account name'),
                None
            )
            if sf_account_name_col is None:
                sf_account_name_col = pick_col(
                    primary_terms=['account name'],
                    secondary_terms=['name', 'account'],
                    exclude_terms=['id']
                )
            sf_reporting_group_col = pick_col(primary_terms=['reporting group'], secondary_terms=['reporting'])
            sf_ultimate_parent_col = pick_col(primary_terms=['ultimate parent'], secondary_terms=['parent'])
            sf_legal_name_col = pick_col(primary_terms=['legal name'], secondary_terms=['legal'])

            detected_columns = []
            if sf_account_name_col:
                detected_columns.append(f'Account Name → "{sf_account_name_col}"')
            if sf_reporting_group_col:
                detected_columns.append(f'Reporting Group → "{sf_reporting_group_col}"')
            if sf_ultimate_parent_col:
                detected_columns.append(f'Ultimate Parent → "{sf_ultimate_parent_col}"')
            if sf_legal_name_col:
                detected_columns.append(f'Legal Name → "{sf_legal_name_col}"')
            if detected_columns:
                st.success(" | ".join(detected_columns))

            confidence_threshold = st.slider(
                "Minimum confidence threshold to show a match (%)",
                min_value=0, max_value=100, value=60, step=5,
                help="Matches below this threshold will be marked as 'No match found'"
            )

            run_matching = st.button("▶ Run Account Matching", type="primary", use_container_width=True)

            if run_matching:
                new_names = new_customers_df[name_column].dropna().astype(str).tolist()
                match_columns = []
                for col in [sf_account_name_col, sf_reporting_group_col, sf_ultimate_parent_col, sf_legal_name_col]:
                    if col and col not in match_columns:
                        match_columns.append(col)
                sf_records = sf_accounts.to_dict("records")

                results = []
                progress = st.progress(0, text="Matching accounts...")

                total = len(new_names)
                for i, new_name in enumerate(new_names):
                    new_norm = normalize_name(new_name)
                    top_matches = []

                    for row in sf_records:
                        row_best_score = None
                        row_fallback_display = ""
                        for col in match_columns:
                            val = row.get(col, "")
                            if pd.isna(val):
                                continue
                            val_str = str(val).strip()
                            if not val_str:
                                continue
                            if not row_fallback_display:
                                row_fallback_display = val_str

                            val_norm = normalize_name(val_str)
                            if not new_norm or not val_norm:
                                continue

                            score = max(
                                fuzz.WRatio(new_norm, val_norm),
                                fuzz.token_sort_ratio(new_norm, val_norm),
                                fuzz.token_set_ratio(new_norm, val_norm),
                            )

                            if row_best_score is None or score > row_best_score:
                                row_best_score = score

                        if row_best_score is not None:
                            if sf_account_name_col:
                                account_name_val = row.get(sf_account_name_col, "")
                                row_display_name = str(account_name_val).strip() if pd.notna(account_name_val) else ""
                            else:
                                row_display_name = row_fallback_display

                            if row_display_name:
                                top_matches.append((row_best_score, row_display_name))

                    top_matches = sorted(top_matches, key=lambda x: x[0], reverse=True)[:2]

                    if top_matches:
                        primary_score = round(top_matches[0][0], 1)
                        primary_name = top_matches[0][1] if primary_score >= confidence_threshold else "No match found"
                        if primary_name == "No match found":
                            primary_score = None

                        secondary_name = ""
                        secondary_score = None
                        if len(top_matches) > 1 and primary_name != "No match found":
                            sec_score = round(top_matches[1][0], 1)
                            if sec_score >= confidence_threshold:
                                secondary_name = top_matches[1][1]
                                secondary_score = sec_score
                    else:
                        primary_name = "No match found"
                        primary_score = None
                        secondary_name = ""
                        secondary_score = None

                    results.append({
                        "New Customer Name": new_name,
                        "Primary Match": primary_name,
                        "Confidence Score (%)": primary_score if primary_score is not None else NO_VALUE_PLACEHOLDER,
                        "Secondary Match": secondary_name if secondary_name else NO_VALUE_PLACEHOLDER,
                        "Secondary Confidence (%)": secondary_score if secondary_score is not None else NO_VALUE_PLACEHOLDER,
                    })

                    if (i + 1) % max(1, total // 20) == 0 or i == total - 1:
                        progress.progress((i + 1) / total, text=f"Matching accounts... {i+1}/{total}")

                progress.empty()

                results_df = pd.DataFrame(results)

                matched = results_df[results_df["Primary Match"] != "No match found"]
                unmatched = results_df[results_df["Primary Match"] == "No match found"]
                high_conf = matched[
                    pd.to_numeric(matched["Confidence Score (%)"], errors='coerce') >= HIGH_CONFIDENCE_THRESHOLD
                ]

                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                col_m1.metric("Total New Customers", total)
                col_m2.metric("Matched", len(matched))
                col_m3.metric(f"High Confidence (≥{HIGH_CONFIDENCE_THRESHOLD}%)", len(high_conf))
                col_m4.metric("No Match Found", len(unmatched))

                st.divider()
                st.markdown('<p class="fen-section-title">Matching Results</p>', unsafe_allow_html=True)

                def highlight_confidence(val):
                    try:
                        v = float(val)
                        if v >= 90:
                            return 'background-color: #d4edda; color: #155724'
                        elif v >= 70:
                            return 'background-color: #fff3cd; color: #856404'
                        else:
                            return 'background-color: #f8d7da; color: #721c24'
                    except (ValueError, TypeError):
                        return ''

                styled_df = results_df.style.map(
                    highlight_confidence,
                    subset=["Confidence Score (%)"]
                )
                st.dataframe(styled_df, use_container_width=True, hide_index=True)

                export_df = results_df.copy()
                export_df["Confidence Score (%)"] = export_df["Confidence Score (%)"].replace(NO_VALUE_PLACEHOLDER, "")
                export_df["Secondary Confidence (%)"] = export_df["Secondary Confidence (%)"].replace(NO_VALUE_PLACEHOLDER, "")
                export_df["Secondary Match"] = export_df["Secondary Match"].replace(NO_VALUE_PLACEHOLDER, "")

                csv_buffer = io.StringIO()
                export_df.to_csv(csv_buffer, index=False)
                csv_bytes = csv_buffer.getvalue().encode("utf-8")

                st.download_button(
                    label="⬇️ Download Results as CSV",
                    data=csv_bytes,
                    file_name="account_matching_results.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
    else:
        st.markdown("""
        <div class="placeholder-box">
            <h3>Account Matching</h3>
            <p>Upload a New Customer file above to begin.<br>
            Ensure the Salesforce Accounts CSV is also loaded in the sidebar.</p>
        </div>
        """, unsafe_allow_html=True)

# ===============================================
# TAB 4 — ICP ANALYSIS (placeholder)
# ===============================================
with tab4:
    st.markdown("""
    <div class="placeholder-box">
        <h3>ICP Analysis</h3>
        <p>This module is coming soon.<br>
        It will score accounts against Fenergo's Ideal Customer Profile,<br>
        providing fit ratings and prioritisation recommendations for the sales team.</p>
    </div>
    """, unsafe_allow_html=True)
