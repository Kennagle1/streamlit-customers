from __future__ import annotations

import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from rapidfuzz import fuzz
from datetime import datetime
import io
import re
import difflib
import json
from html import escape as html_escape
from openai import OpenAI
import openai
import traceback

# -----------------------------------------------
# PAGE CONFIG
# -----------------------------------------------
st.set_page_config(page_title="Fenergo | Account Intelligence", layout="wide", page_icon="🏦")

# -----------------------------------------------
# OPENAI CLIENT
# -----------------------------------------------
_openai_init_error = None
try:
    _openai_api_key = st.secrets["openai"]["api_key"]
    client = OpenAI(api_key=_openai_api_key)
except Exception as _e:
    client = None
    _openai_init_error = str(_e)

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

    /* Sidebar file upload browse button — make it visible on dark background */
    section[data-testid="stSidebar"] .stFileUploader button {
        background-color: #21CFB2 !important;
        color: #002E33 !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
    }
    section[data-testid="stSidebar"] .stFileUploader button:hover {
        background-color: #1ab89d !important;
        color: #002E33 !important;
    }

    /* Sidebar uploaded file name — override white text so it's readable on the widget's light background */
    section[data-testid="stSidebar"] .stFileUploader [data-testid="stFileUploaderFile"] {
        color: #002E33 !important;
    }
    section[data-testid="stSidebar"] .stFileUploader [data-testid="stFileUploaderFile"] * {
        color: #002E33 !important;
    }

    /* Sidebar expander content — dark background so white text remains readable */
    section[data-testid="stSidebar"] .streamlit-expanderContent {
        background-color: #003a40 !important;
    }
    section[data-testid="stSidebar"] .streamlit-expanderContent * {
        color: #ffffff !important;
    }

    /* Sidebar success/warning/error/info alert boxes — dark background with white text */
    section[data-testid="stSidebar"] [data-testid="stAlert"] {
        background-color: #003a40 !important;
        border-color: #21CFB2 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stAlert"] * {
        color: #ffffff !important;
    }

    /* Sidebar checkbox, radio, selectbox label text */
    section[data-testid="stSidebar"] .stCheckbox label,
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #ffffff !important;
    }

    /* Sidebar dataframe/table text */
    section[data-testid="stSidebar"] [data-testid="stDataFrame"] * {
        color: #002E33 !important;
        background-color: #ffffff !important;
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

    /* Salesforce-mirrored layout */
    .sf-layout {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        margin-top: 8px;
    }
    .sf-section {
        background: #ffffff;
        border: 1px solid #dddbda;
        border-radius: 4px;
        margin-bottom: 20px;
        overflow: hidden;
    }
    .sf-section-header {
        background-color: #f3f3f3;
        border-bottom: 1px solid #dddbda;
        padding: 8px 16px;
        font-size: 0.8rem;
        font-weight: 700;
        color: #3e3e3c;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }
    .sf-fields-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
    }
    .sf-field {
        padding: 10px 16px;
        border-bottom: 1px solid #f3f3f3;
        min-height: 52px;
    }
    .sf-field-label {
        font-size: 0.7rem;
        color: #706e6b;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 3px;
        font-weight: 600;
    }
    .sf-field-value {
        font-size: 0.88rem;
        color: #181818;
        font-weight: 500;
        line-height: 1.3;
    }
    .sf-field-value.sf-empty {
        color: #c9c7c5;
    }
    .sf-field.sf-greyed .sf-field-label {
        color: #c9c7c5;
    }
    .sf-field.sf-greyed .sf-field-value {
        color: #c9c7c5;
    }
    .sf-field-note {
        font-size: 0.73rem;
        color: #706e6b;
        margin-top: 4px;
        font-style: italic;
        line-height: 1.3;
    }
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

FINANCIAL_STOP_WORDS = {
    "bank", "financial", "group", "capital", "asset", "management",
    "services", "solutions", "international", "global", "trust",
    "investments", "partners", "advisory", "fund", "funds",
    "federal", "savings", "national", "commercial", "credit",
    "corporate", "holding", "holdings", "co", "company",
}

COUNTRY_REGION_MAP = {
    # EMEA — UK & Ireland
    "United Kingdom": "EMEA",
    "Ireland": "EMEA",
    # EMEA — Western Europe
    "France": "EMEA", "Germany": "EMEA", "Netherlands": "EMEA",
    "Belgium": "EMEA", "Luxembourg": "EMEA", "Switzerland": "EMEA",
    "Austria": "EMEA", "Italy": "EMEA", "Spain": "EMEA",
    "Portugal": "EMEA", "Sweden": "EMEA", "Norway": "EMEA",
    "Denmark": "EMEA", "Finland": "EMEA", "Iceland": "EMEA",
    # EMEA — Eastern Europe
    "Poland": "EMEA", "Czech Republic": "EMEA", "Hungary": "EMEA",
    "Romania": "EMEA", "Bulgaria": "EMEA", "Croatia": "EMEA",
    "Slovakia": "EMEA", "Slovenia": "EMEA", "Serbia": "EMEA",
    "Greece": "EMEA", "Cyprus": "EMEA", "Malta": "EMEA",
    "Estonia": "EMEA", "Latvia": "EMEA", "Lithuania": "EMEA",
    "Ukraine": "EMEA", "Russia": "EMEA",
    # EMEA — Middle East & Africa
    "United Arab Emirates": "EMEA", "Saudi Arabia": "EMEA",
    "Qatar": "EMEA", "Kuwait": "EMEA", "Bahrain": "EMEA",
    "Oman": "EMEA", "Israel": "EMEA", "Turkey": "EMEA",
    "Jordan": "EMEA", "Lebanon": "EMEA", "Egypt": "EMEA",
    "South Africa": "EMEA", "Nigeria": "EMEA", "Kenya": "EMEA",
    "Ghana": "EMEA", "Morocco": "EMEA",
    # APAC
    "Australia": "APAC", "New Zealand": "APAC", "Singapore": "APAC",
    "Hong Kong": "APAC", "Japan": "APAC", "China": "APAC",
    "India": "APAC", "South Korea": "APAC", "Malaysia": "APAC",
    "Thailand": "APAC", "Indonesia": "APAC", "Philippines": "APAC",
    "Vietnam": "APAC", "Taiwan": "APAC", "Pakistan": "APAC",
    "Bangladesh": "APAC", "Sri Lanka": "APAC",
    # AMER
    "United States": "AMER", "Canada": "AMER",
    "Mexico": "AMER", "Brazil": "AMER", "Argentina": "AMER",
    "Chile": "AMER", "Colombia": "AMER", "Peru": "AMER",
    "Uruguay": "AMER", "Venezuela": "AMER", "Ecuador": "AMER",
    "Costa Rica": "AMER", "Panama": "AMER",
    "Cayman Islands": "AMER", "Bermuda": "AMER",
    "British Virgin Islands": "AMER",
}

# -----------------------------------------------
# Matching weights — Account Name is primary signal,
# Legal Name is a supporting signal.
# Special rule: if Account Name is an exact match (score = 100),
# the overall confidence is immediately returned as 100 regardless of legal name.
# Otherwise: combined score = ACCT_WEIGHT * acct_score + LEGAL_WEIGHT * legal_score
# -----------------------------------------------
ACCT_WEIGHT  = 0.70
LEGAL_WEIGHT = 0.30

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
uploaded_file = st.sidebar.file_uploader(
    "Upload Salesforce Accounts CSV",
    type=["csv"],
    help="Maximum recommended file size: 10 MB",
)
sf_accounts = None
if uploaded_file:
    sf_accounts = pd.read_csv(uploaded_file)
    st.sidebar.success(f"✅ Loaded {len(sf_accounts)} accounts")

# -----------------------------------------------
# LOAD ACCOUNT CATEGORY MATRIX
# -----------------------------------------------
@st.cache_data
def load_account_category_matrix():
    """Load account category matrix. Tries multi-header first, falls back to single-header."""
    _primary_err = None
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
        if lookup:
            return lookup, None
        _primary_err = "Multi-header read succeeded but matrix contains no valid entries"
    except FileNotFoundError:
        return {}, "account_category_matrix.xlsx not found in repo root"
    except Exception as e:
        _primary_err = str(e)

    # Fallback: single-header row with "BusinessSegment / CustomerSegment" column names
    try:
        df2 = pd.read_excel("account_category_matrix.xlsx", header=0, index_col=0)
        lookup2 = {}
        for country in df2.index:
            if pd.isna(country):
                continue
            country_clean = str(country).strip().lower()
            for col in df2.columns:
                col_str = str(col).strip()
                for sep in [' / ', ' | ', '/', ' - ']:
                    if sep in col_str:
                        parts = col_str.split(sep, 1)
                        bseg = parts[0].strip()
                        cseg = parts[1].strip()
                        val = df2.loc[country, col]
                        if pd.notna(val):
                            lookup2[(country_clean, bseg.lower(), cseg.lower())] = str(val).strip()
                        break
        if lookup2:
            return lookup2, None
        return {}, f"Matrix loaded but no entries found. Primary error: {_primary_err}. Fallback attempted with {len(df2.columns)} columns."
    except FileNotFoundError:
        return {}, "account_category_matrix.xlsx not found in repo root"
    except Exception as e2:
        return {}, f"Error loading matrix: primary={_primary_err}; fallback={e2}"

matrix_lookup, matrix_error = load_account_category_matrix()
if matrix_error:
    st.sidebar.warning(matrix_error)
else:
    st.sidebar.success(f"✅ Matrix loaded ({len(set(k[0] for k in matrix_lookup.keys()))} countries)")

# -----------------------------------------------
# AI DEBUG INFO (sidebar) — visible to admins only
# -----------------------------------------------
try:
    _show_debug = st.secrets.get("show_debug", False)
except Exception:
    _show_debug = False

if _show_debug:
    with st.sidebar.expander("🔧 AI Debug Info"):
        st.markdown("**Model:** `gpt-4.1`")
        st.markdown(f"**openai SDK:** `{openai.__version__}`")
        if client is not None:
            st.success("✅ OpenAI client initialised")
        else:
            st.error("❌ OpenAI client NOT initialised")
            if _openai_init_error:
                st.code(_openai_init_error)

        # Matrix diagnostic info
        st.markdown("---")
        st.markdown("**Matrix Lookup Debug:**")
        if matrix_lookup:
            _matrix_country_set = {k[0] for k in matrix_lookup.keys()}
            st.markdown(f"Countries loaded: **{len(_matrix_country_set)}**")
            _sample_keys = list(matrix_lookup.keys())[:5]
            st.markdown("Sample keys (country, business_seg, customer_seg):")
            for _sk in _sample_keys:
                st.caption(f"`{_sk}`")
        else:
            st.warning("Matrix not loaded")

# -----------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------
def _highlight_conf(val):
    """Colour-code a confidence score cell for use with DataFrame.style.map()."""
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

def compute_match_score(new_norm, val_norm):
    """Compute a calibrated fuzzy match score between two normalised strings.

    Scoring philosophy:
    - 100   = exact normalised match only
    - 85-99 = very close (minor word order / spelling differences)
    - 70-84 = good match (significant token overlap, similar length)
    - <70   = weak / coincidental overlap

    Key safeguards:
    1. token_set_ratio is scaled by the length ratio of the two strings so that a
       short name cannot score 100 as a pure subset of a longer name.
    2. fuzz.WRatio is NOT used — it internally returns the uncapped maximum of
       several methods including token_set_ratio, causing score inflation.
    3. Shared tokens that are all financial stop-words are penalised further.
    4. An additional multiplicative penalty is applied when the strings differ
       greatly in length (length_ratio < 0.6).
    5. Any non-exact match is capped at 99 so that 100 is reserved for exact matches.
    """
    if not new_norm or not val_norm:
        return 0

    # Exact normalised match → 100
    if new_norm == val_norm:
        return 100

    # Hard filter: very low character-level overlap
    char_ratio = difflib.SequenceMatcher(None, new_norm, val_norm).ratio()
    if char_ratio < 0.25:
        return 0

    # Length ratio — how similar are the two strings in length?
    len_a, len_b = len(new_norm), len(val_norm)
    length_ratio = min(len_a, len_b) / max(len_a, len_b) if max(len_a, len_b) > 0 else 1.0

    # Core metrics (no WRatio)
    r   = fuzz.ratio(new_norm, val_norm)             # pure character-level similarity
    tsr = fuzz.token_sort_ratio(new_norm, val_norm)  # token order-insensitive similarity

    # token_set_ratio: always scale by length ratio to penalise subset matches
    tset_contrib = 0.0
    if len(new_norm) >= 5 and len(val_norm) >= 5:
        raw_tset = fuzz.token_set_ratio(new_norm, val_norm)
        tset_adjusted = raw_tset * length_ratio   # scale down proportionally

        # Extra penalty if all shared tokens are financial stop-words
        new_tokens    = set(new_norm.split())
        val_tokens    = set(val_norm.split())
        shared_tokens = new_tokens & val_tokens
        if shared_tokens and shared_tokens.issubset(FINANCIAL_STOP_WORDS):
            tset_adjusted = min(tset_adjusted, 59)

        tset_contrib = tset_adjusted

    # Weighted blend: token_sort is most reliable, then char ratio, then adjusted token_set
    blended = 0.50 * tsr + 0.30 * r + 0.20 * tset_contrib

    # Extra multiplicative penalty for very large length differences (likely a subset match)
    if length_ratio < 0.6:
        blended *= (0.5 + 0.5 * length_ratio)

    # Word-level substring boost: if all words of the shorter name appear as whole words in
    # the longer name, boost to at least 75.  This handles abbreviations like "UBS" → "UBS IB"
    # or "UBS LUX" without relying solely on fuzzy ratios that penalize length differences.
    _new_words = set(new_norm.split()) if new_norm else set()
    _val_words = set(val_norm.split()) if val_norm else set()
    _shorter_words = _new_words if len(new_norm) <= len(val_norm) else _val_words
    _longer_words  = _val_words if len(new_norm) <= len(val_norm) else _new_words
    _shorter_norm  = new_norm if len(new_norm) <= len(val_norm) else val_norm
    if (
        len(_shorter_norm) >= 3
        and _shorter_words
        and _shorter_words.issubset(_longer_words)
        and not _shorter_words.issubset(FINANCIAL_STOP_WORDS)
    ):
        blended = max(blended, 75.0)

    # Cap at 99 — only exact normalised match earns 100
    return round(min(blended, 99.0), 1)

def combined_score(acct_score, legal_score):
    """Compute the overall confidence score for a candidate SF record.

    Rules (in priority order):
    1. If Account Name is an exact match (score = 100) → return 100 immediately.
       The account name is definitively correct; no blending needed.
    2. Otherwise → weighted blend: 70% Account Name + 30% Legal Name.
       A strong legal name match alone cannot compensate for a poor account name.

    Examples:
      Exact acct match:  acct=100, legal=any  → 100
      Close acct match:  acct=85,  legal=90   → 0.70*85 + 0.30*90 = 86.5
      Poor acct match:   acct=18,  legal=90   → 0.70*18 + 0.30*90 = 39.6
    """
    if acct_score == 100:
        return 100.0
    return round(ACCT_WEIGHT * acct_score + LEGAL_WEIGHT * legal_score, 1)

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

def lookup_sf_ultimate_parent(sf_accounts, ultimate_parent):
    """Search the SF upload for a row whose 'Ultimate Parent' column matches
    *ultimate_parent* (exact normalised match or fuzzy ≥ 80).

    Returns:
        (parent_account: str|None, reporting_group: str|None)
    """
    if sf_accounts is None or not ultimate_parent:
        return None, None
    ult_str = str(ultimate_parent).strip()
    if ult_str.lower() in ('', 'not found', 'n/a', 'null', 'none'):
        return None, None

    cols = sf_accounts.columns.tolist()
    cols_lc = {c: c.lower().strip() for c in cols}

    # Detect Ultimate Parent column (exact first, then partial)
    ult_parent_col = None
    for c in cols:
        if cols_lc[c] in ('ultimate parent', 'ultimate_parent'):
            ult_parent_col = c
            break
    if ult_parent_col is None:
        for c in cols:
            lc = cols_lc[c]
            if 'ultimate' in lc and 'parent' in lc:
                ult_parent_col = c
                break

    # Detect Parent Account column (exact first, then partial, exclude IDs)
    parent_account_col = None
    for c in cols:
        if cols_lc[c] in ('parent account', 'parent_account'):
            parent_account_col = c
            break
    if parent_account_col is None:
        for c in cols:
            lc = cols_lc[c]
            if 'parent' in lc and 'account' in lc and 'id' not in lc and 'ultimate' not in lc:
                parent_account_col = c
                break

    # Detect Reporting Group column
    reporting_group_col = None
    for c in cols:
        lc = cols_lc[c]
        if 'reporting group' in lc or lc == 'reportinggroup' or lc == 'reporting_group':
            reporting_group_col = c
            break

    if not ult_parent_col:
        return None, None

    ult_norm = normalize_name(ult_str)
    for _, row in sf_accounts.iterrows():
        sf_ult_raw = row.get(ult_parent_col, '')
        if pd.isna(sf_ult_raw) or str(sf_ult_raw).strip() == '':
            continue
        sf_ult_norm = normalize_name(str(sf_ult_raw).strip())
        if sf_ult_norm == ult_norm or compute_match_score(ult_norm, sf_ult_norm) >= 80:
            parent_acct = ''
            rgroup = ''
            if parent_account_col:
                raw = row.get(parent_account_col, '')
                if pd.notna(raw):
                    parent_acct = str(raw).strip()
            if reporting_group_col:
                raw = row.get(reporting_group_col, '')
                if pd.notna(raw):
                    rgroup = str(raw).strip()
            return parent_acct or None, rgroup or None

    return None, None

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
    _country_normalized = str(country).strip().lower()
    if not matched_country:
        return "No match found", f"Country '{country}' not found in matrix (normalised lookup key: '{_country_normalized}')"
    # Normalise business_segment and customer_segment: strip + lowercase for case-insensitive matching
    bs_norm = str(business_segment).strip().lower()
    cs_norm = str(customer_segment).strip().lower()
    lookup_key = (matched_country, bs_norm, cs_norm)
    if lookup_key in matrix_lookup:
        return matrix_lookup[lookup_key], f"Matched: {matched_country.title()} | {business_segment} | {customer_segment}"
    # Diagnostic: collect what business/customer segment keys exist for this country
    _available_bs = sorted({k[1] for k in matrix_lookup if k[0] == matched_country})
    _available_cs = sorted({k[2] for k in matrix_lookup if k[0] == matched_country})
    return (
        "No match found",
        (
            f"No matrix entry for {matched_country.title()} + '{business_segment}' + '{customer_segment}'. "
            f"Available business segments for this country: {_available_bs[:5]}. "
            f"Available customer segments: {_available_cs}."
        )
    )

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
                return "Joseph Cawley"
            else:
                return "Gabriel Simpatico"
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
# LLM FIRMOGRAPHIC EXTRACTION
# -----------------------------------------------
def enrich_with_llm(snippets, account_name):
    """Extract structured firmographic data using the OpenAI Responses API
    with the built-in web_search tool for live internet data.

    Primary path: Responses API with web_search tool — searches the live web for
    current employee counts, revenue figures, parent company info, etc.
    Fallback: Chat Completions API (used if the Responses API call fails for any reason).

    The `snippets` parameter accepts pre-fetched web snippets.
    When `snippets` is empty, the LLM is prompted to search the web directly for all
    fields.
    """
    use_knowledge_fallback = not snippets

    # Shared JSON field definitions
    _fields = f"""- legal_name: full registered legal name (string or null)
- country_hq: ISO country name of headquarters (string or null)
- annual_revenue_eur: revenue as a human-readable string like "€4.5bn" or "€320m"; include the data year, e.g. "€4.5bn (FY2024)" — MUST be the most recent year available (string or null)
- employees: headcount as integer or human-readable string like "12,500"; include the data year, e.g. "12,500 (2024)" — MUST be the most recent year available (string or null)
- aum_eur: assets under management as a human-readable string like "€1.2tn"; include the data year; use "N/A" if not applicable to this company type, or null if unknown (string or null)
- ultimate_parent: full legal name of the ultimate parent / group holding company at the very top of the corporate ownership chain. See instructions above — MUST always be populated for publicly traded companies. (string or null)
- ultimate_parent_hq: country of the ultimate parent HQ (string or null)
- detailed_business_segment: the single best-fit Detailed Business Segment — must be exactly one of {json.dumps(VALID_DETAILED_SEGMENTS)}. This is the PRIMARY segment; business_segment and market_segment are derived automatically from it. (string)
- alternative_detailed_business_segment: if more than one Detailed Business Segment is equally valid for this company, provide ONE alternative here — must be one of {json.dumps(VALID_DETAILED_SEGMENTS)}, or null if only one segment clearly applies (string or null)
- business_segment: must be one of {json.dumps(VALID_BUSINESS_SEGMENTS)} — will be overridden by hierarchy lookup but provide your best estimate (string)
- market_segment: must be one of {json.dumps(VALID_MARKET_SEGMENTS)} — will be overridden by hierarchy lookup but provide your best estimate (string)
- industry_classification_rationale: a 1-2 sentence explanation of why you chose the detailed_business_segment value for this company (string or null)
- reporting_group_suggestion: a short, commonly-used friendly name for this company or its group — the informal name rather than the full legal name (e.g. "Barclays" for "Barclays Services Limited", "Mastercard" for "Mastercard Incorporated", "HSBC" for "HSBC Holdings plc", "UBS" for "UBS Group AG"). Used as the Reporting Group if not found in the CRM upload. (string or null)
- sources: a JSON object with keys "revenue_source", "employees_source", "aum_source" — each value should be the URL of the source used for that data point, or null if unavailable (object)"""

    system_prompt = f"""You are a financial-services data analyst with broad knowledge of global financial institutions.

Conduct COMPREHENSIVE DEEP RESEARCH on the named company using multiple authoritative sources. Do NOT rely on just the first result you find — cross-reference multiple sources and assess their credibility before settling on a value.

SOURCE PRIORITY ORDER (highest to lowest authority):
1. The company's own website — annual reports, investor relations pages, official press releases
2. Official regulatory filings — SEC EDGAR, Companies House, central bank registers, stock exchange filings
3. Major financial data providers — Bloomberg, Reuters, S&P Global, Moody's, Fitch, FactSet
4. Wikipedia and established business databases — Crunchbase, LinkedIn, Dun & Bradstreet, Bureau van Dijk
5. News articles from reputable outlets — Financial Times, Wall Street Journal, The Economist

For REVENUE and EMPLOYEE figures: You MUST use the MOST RECENT data available — current year (2025) or last fiscal year (FY2024/FY2025). Do NOT return 2023 data if 2024 or 2025 data exists. Always check the company's latest annual report or most recent quarterly filing FIRST. If more recent data exists, use it and explicitly state the year (e.g. "€4.5bn (FY2024)" or "€4.5bn (FY2025)"). Never use outdated data when more recent data is available. If sources conflict, use the most authoritative and recent one.

For ULTIMATE PARENT: You MUST find and return the ultimate parent company for EVERY company — do NOT return null without exhaustive research. This is critically important.

CRITICAL RULE: For well-known publicly traded companies that ARE themselves the ultimate parent entity, you MUST return the company itself (or its holding company name). Examples:
- Mastercard Incorporated → "Mastercard Incorporated" (self-owned, publicly traded — Mastercard IS the ultimate parent)
- Visa Inc. → "Visa Inc." (self-owned, publicly traded)
- PayPal Holdings, Inc. → "PayPal Holdings, Inc." (publicly traded holding company)
- Apple Inc. → "Apple Inc." (self-owned, publicly traded)
- Bank of Ireland → "Bank of Ireland Group plc" (the listed holding company)
- AIB → "AIB Group plc"
- Barclays → "Barclays PLC"
- JPMorgan Chase Bank → "JPMorgan Chase & Co."
- Goldman Sachs Bank → "The Goldman Sachs Group, Inc."
- UBS → "UBS Group AG"
Do NOT return null for major publicly traded companies. Always return the top-level listed or registered entity, not an operating subsidiary.

IMPORTANT:
- Include the year/date of each data point where possible (e.g. "€4.5bn (FY2024)").
- For each data point (revenue, employees, AUM), include the source URL where you found the information.
- If different sources give different values, prefer the most authoritative/recent source and note the discrepancy.

Extract structured firmographic data about the named company and return it as a single JSON object with exactly these keys:
{_fields}

Use null for fields you cannot determine. For segment fields, pick the single best match from the valid values list; use "Other" if none fits."""

    if use_knowledge_fallback:
        user_message = (
            f"Company: {account_name}\n\n"
            "Conduct comprehensive deep research on this company using multiple authoritative sources. "
            "Search the company's own website (annual reports, investor relations pages) first, "
            "then regulatory filings, then major financial data providers. "
            "Find the MOST RECENT figures for revenue, employees, AUM, ultimate parent company, and all other fields. "
            "For employee count and revenue, ALWAYS use the most recent year available (2024 or 2025 if possible). "
            "For ultimate parent, research the full corporate ownership chain to find the top-level holding company. "
            "For well-known public companies, return themselves as the ultimate parent if they have no parent above them. "
            "Cross-reference multiple sources and note any discrepancies. "
            "Include the year/date of the data where possible."
        )
    else:
        snippets_text = "\n\n".join(
            f"[Query: {s['query']}]\nSource: {s['source']}\n{s['snippet']}"
            for s in snippets
        )
        user_message = (
            f"Company: {account_name}\n\n"
            f"Preliminary web search results (these may be limited or incomplete):\n{snippets_text}\n\n"
            "Now conduct your own comprehensive deep research to verify and supplement the above data. "
            "Search the company's own website (annual reports, investor relations) as the primary source, "
            "then cross-reference with regulatory filings and major financial data providers. "
            "Pay special attention to: (1) the MOST RECENT employee count and revenue (prefer 2024/2025 data), "
            "(2) the full corporate ownership chain to identify the ultimate parent holding company, "
            "(3) for well-known public companies that are their own ultimate parent, return themselves. "
            "Note any discrepancies between sources."
        )

    try:
        if client is None:
            return {"_llm_error": "OpenAI client not configured"}

        extracted = None

        # --- Primary path: Responses API with web_search tool for live internet data ---
        _responses_api_error = None
        _search_method = None

        combined_input = (
            f"{system_prompt}\n\n{user_message}\n\n"
            "IMPORTANT: Use the web_search tool to conduct comprehensive deep research. "
            "Search multiple authoritative sources — prioritise the company's own website, "
            "annual reports, regulatory filings, then major financial data providers. "
            "Do NOT stop at the first result. Cross-reference sources and use the most "
            "authoritative/recent data. Return your response as a JSON object."
        )

        try:
            resp_data = client.responses.create(
                model="gpt-4.1",
                tools=[{"type": "web_search_preview"}],
                input=combined_input,
            )

            # Use SDK's built-in property to extract text from the response
            text_content = resp_data.output_text or ""

            # Strip markdown code fences if present (e.g. ```json ... ```)
            text_content = text_content.strip()
            if text_content.startswith("```"):
                lines = text_content.split("\n")
                if len(lines) >= 3:
                    text_content = "\n".join(lines[1:-1]).strip()

            # Remove any citation annotations like 【4:0†source】
            text_content = re.sub(r'【[^】]*】', '', text_content)

            # If still not valid JSON, try to extract the JSON object
            if text_content and not text_content.startswith("{"):
                first_brace = text_content.find("{")
                last_brace = text_content.rfind("}")
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    text_content = text_content[first_brace:last_brace + 1]

            if not text_content:
                raise ValueError(f"Responses API returned empty text after cleanup. Raw output_text: {repr(resp_data.output_text)[:500]}")

            extracted = json.loads(text_content)
            _search_method = "responses_api_web_search"
        except Exception as e:
            _raw_preview = ""
            try:
                if 'resp_data' in locals():
                    _raw_preview = f" | Raw output_text preview: {repr(resp_data.output_text)[:300]}"
            except Exception:
                pass
            _responses_api_error = f"{e}{_raw_preview}"

        # --- Fallback path: Chat Completions API ---
        if extracted is None:
            # Build a modified system prompt that prohibits URL fabrication since this
            # path has no internet access (only training data).
            fallback_system_prompt = (
                system_prompt
                + "\n\nCRITICAL — NO INTERNET ACCESS IN THIS MODE:\n"
                "- You do NOT have access to the internet. Do NOT fabricate or guess source URLs.\n"
                "- For the sources object, set all values to null since you cannot verify any URLs.\n"
                "- Clearly indicate that figures come from training data and may be outdated by "
                "appending '(training data, may be outdated)' to revenue and employee values, "
                "e.g. '€4.5bn (FY2023, training data, may be outdated)'."
            )

            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": fallback_system_prompt},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            extracted = json.loads(response.choices[0].message.content)
            _search_method = "chat_completions_fallback"

        result = {}
        for key in ("legal_name", "country_hq", "annual_revenue_eur", "employees",
                    "aum_eur", "ultimate_parent", "ultimate_parent_hq",
                    "detailed_business_segment", "business_segment", "market_segment",
                    "industry_classification_rationale",
                    "alternative_detailed_business_segment", "reporting_group_suggestion"):
            val = extracted.get(key)
            if val is not None and str(val).strip():
                result[key] = str(val).strip()
        # Preserve sources dict as-is (not coerced to string)
        sources = extracted.get("sources")
        if isinstance(sources, dict):
            result["sources"] = sources
        # Record which API path was used (for UI freshness indicator)
        result["_search_method"] = _search_method
        if _responses_api_error:
            result["_responses_api_error"] = _responses_api_error
        return result
    except Exception as e:
        return {"_llm_error": str(e), "_llm_traceback": traceback.format_exc()}

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
# FUZZY DUPLICATE CHECK HELPER
# -----------------------------------------------
def run_fuzzy_dup_check(sf_accounts, account_name, top_n=10, min_score=60):
    """Score account_name against every row in sf_accounts using the same
    fuzzy-matching engine as Tab 3.  Returns a list of dicts (sorted
    high→low by Confidence %) containing only rows with combined score
    ≥ min_score, capped at top_n results.

    Args:
        sf_accounts (pd.DataFrame | None): The uploaded Salesforce Accounts CSV.
            Column names are auto-detected (Account ID, Account Name, Legal Name,
            Country).  Returns [] immediately when None or empty.
        account_name (str): The name to search for.
        top_n (int): Maximum number of results to return (default 10).
        min_score (float): Minimum combined confidence score to include a row
            (default 60, i.e. 60%).

    Returns:
        list[dict]: Each dict has keys: Account ID, Account Name, Legal Name,
            Country, Confidence %.
    """
    if sf_accounts is None or sf_accounts.empty:
        return []

    cols = sf_accounts.columns.tolist()
    cols_lc = {c: c.lower().strip() for c in cols}

    # Detect Account ID column — exact "account id" > "accountid" > partial > "id"
    sf_id_col = None
    for c in cols:
        if cols_lc[c] == "account id":
            sf_id_col = c
            break
    if sf_id_col is None:
        for c in cols:
            if cols_lc[c] == "accountid":
                sf_id_col = c
                break
    if sf_id_col is None:
        for c in cols:
            lc = cols_lc[c]
            if "account" in lc and "id" in lc:
                sf_id_col = c
                break
    if sf_id_col is None:
        for c in cols:
            if cols_lc[c] == "id":
                sf_id_col = c
                break

    # Detect Account Name column (exclude columns containing "id")
    sf_acct_name_col = None
    non_id_cols = [c for c in cols if 'id' not in cols_lc[c]]
    for c in non_id_cols:
        if cols_lc[c] == 'account name':
            sf_acct_name_col = c
            break
    if sf_acct_name_col is None:
        for c in non_id_cols:
            if 'account name' in cols_lc[c]:
                sf_acct_name_col = c
                break
    if sf_acct_name_col is None:
        for c in non_id_cols:
            if 'name' in cols_lc[c]:
                sf_acct_name_col = c
                break

    # Detect Legal Name column
    sf_legal_col = None
    for c in cols:
        if 'legal name' in cols_lc[c]:
            sf_legal_col = c
            break
    if sf_legal_col is None:
        for c in cols:
            if 'legal' in cols_lc[c]:
                sf_legal_col = c
                break

    # Detect Country column — prefer exact "country" match over partial
    sf_country_col = None
    for c in cols:
        if cols_lc[c] == 'country':
            sf_country_col = c
            break
    if sf_country_col is None:
        for c in cols:
            if 'country' in cols_lc[c]:
                sf_country_col = c
                break

    new_norm = normalize_name(account_name)
    scored = []

    for _, row in sf_accounts.iterrows():
        acct_score = 0
        acct_val = ""
        if sf_acct_name_col:
            raw = row.get(sf_acct_name_col, "")
            if pd.notna(raw):
                acct_val = str(raw).strip()
                if acct_val:
                    acct_score = compute_match_score(new_norm, normalize_name(acct_val))

        legal_score = 0
        legal_val = ""
        if sf_legal_col:
            raw = row.get(sf_legal_col, "")
            if pd.notna(raw):
                legal_val = str(raw).strip()
                if legal_val:
                    legal_score = compute_match_score(new_norm, normalize_name(legal_val))

        score = combined_score(acct_score, legal_score)

        if score >= min_score and acct_val:
            id_val = ""
            if sf_id_col:
                raw = row.get(sf_id_col, "")
                id_val = str(raw).strip() if pd.notna(raw) else ""

            country_val = ""
            if sf_country_col:
                raw = row.get(sf_country_col, "")
                country_val = str(raw).strip() if pd.notna(raw) else ""

            scored.append({
                "Account ID": id_val,
                "Account Name": acct_val,
                "Legal Name": legal_val,
                "Country": country_val,
                "Confidence %": score,
            })

    scored.sort(key=lambda x: x["Confidence %"], reverse=True)
    return scored[:top_n]

# -----------------------------------------------
# TABS
# -----------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Customer Attributes", "Lead Matching", "Account Matching", "ICP Analysis",
    "Customer Segment Logic", "Fenergo Segmentation"
])

# ===============================================
# TAB 1 — CUSTOMER ATTRIBUTES
# ===============================================
with tab1:

    # Initialise session state keys
    for _k, _v in [
        ("tab1_phase", "input"),
        ("tab1_dup_results", []),
        ("tab1_research", None),
        ("tab1_segmentation", None),
        ("tab1_snap", {}),
    ]:
        if _k not in st.session_state:
            st.session_state[_k] = _v

    st.markdown(
        """
        **How to use this tool:**
        Upload your Salesforce account list via the sidebar, then enter the account details below and
        click **Run Checks**. The tool will check for potential duplicate accounts, research the
        company online, and generate a recommended Fenergo segmentation.
        """,
    )

    st.markdown('<p class="fen-section-title">Enter Account Details</p>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        account_name = st.text_input("Account Name *", placeholder="e.g. Bank of Ireland")
    with col2:
        account_type = st.selectbox("Account Type *", ["Prospect", "Partner"], index=0)
    with col3:
        # Build country options: union of SF account countries + COUNTRY_REGION_MAP keys
        _sf_country_opts = []
        if sf_accounts is not None:
            for _c in sf_accounts.columns:
                if 'country' in _c.lower():
                    _raw = sf_accounts[_c].dropna().astype(str).str.strip().str.title()
                    _sf_country_opts = sorted(_raw[_raw != ""].unique().tolist())
                    break
        _all_countries = sorted(set(_sf_country_opts) | set(COUNTRY_REGION_MAP.keys()))
        t1_country = st.selectbox(
            "Country *",
            options=[""] + _all_countries,
            help="Type to search countries",
            key="tab1_country",
        )
    with col4:
        t1_region = COUNTRY_REGION_MAP.get(t1_country, "")
        st.text_input("Region", value=t1_region, disabled=True)

    run_button = st.button("Run Enrichment Checks", type="primary", use_container_width=True)

    if run_button:
        if not account_name.strip() or not t1_country:
            st.error("Please fill in all required fields: Account Name and Country.")
            st.stop()

        if sf_accounts is None:
            st.error(
                "⚠️ **No Salesforce Account list uploaded.** Please upload the Salesforce Accounts CSV "
                "using the sidebar uploader before running enrichment checks. "
                "This is required to perform the duplicate check."
            )
            st.stop()

        st.session_state["tab1_snap"] = {
            "account_name": account_name,
            "account_type": account_type,
            "country": t1_country,
            "region": t1_region,
        }
        st.session_state["tab1_dup_results"] = run_fuzzy_dup_check(sf_accounts, account_name)
        st.session_state["tab1_phase"] = "dup_check"
        st.session_state["tab1_research"] = None
        st.session_state["tab1_segmentation"] = None
        st.rerun()

    # ── Phases: dup_check / enrichment ────────────────────────────────────────
    if st.session_state["tab1_phase"] in ("dup_check", "enrichment"):
        _snap         = st.session_state.get("tab1_snap", {})
        _account_name = _snap.get("account_name", "")
        _account_type = _snap.get("account_type", "")
        _country      = _snap.get("country", "")
        _region       = _snap.get("region", "")
        _dup_results  = st.session_state.get("tab1_dup_results", [])

        st.divider()
        st.markdown(
            f'<p class="fen-section-title">Running checks for: {html_escape(_account_name)}</p>',
            unsafe_allow_html=True,
        )

        # ── PARTNER FLOW ──────────────────────────────────────────────────────
        if _account_type == "Partner":
            st.info("Partner Account — only a duplicate check is required.")
            st.markdown(
                '<p class="fen-section-title">Suggested Matches</p>',
                unsafe_allow_html=True,
            )
            if not _dup_results:
                st.success("No potential duplicate accounts found.")
            else:
                _dup_df = pd.DataFrame(_dup_results)
                _styled = _dup_df.style.map(_highlight_conf, subset=["Confidence %"])
                st.dataframe(_styled, use_container_width=True, hide_index=True)

                _same_country = [
                    m for m in _dup_results
                    if m.get("Country", "").strip().lower() == _country.strip().lower()
                ]
                if _same_country:
                    st.warning(
                        "⚠️ Similar account found in the same country. "
                        "Please check with the Account Owner before proceeding."
                    )

        # ── PROSPECT (and all non-Partner) FLOW ───────────────────────────────
        else:
            st.markdown(
                '<p class="fen-section-title">Suggested Matches</p>',
                unsafe_allow_html=True,
            )
            if not _dup_results:
                st.success("No potential duplicate accounts found.")
            else:
                _dup_df = pd.DataFrame(_dup_results)
                _styled = _dup_df.style.map(_highlight_conf, subset=["Confidence %"])
                st.dataframe(_styled, use_container_width=True, hide_index=True)

            # Show "Continue" button only in dup_check phase
            if st.session_state["tab1_phase"] == "dup_check":
                _continue = st.button(
                    "✅ Continue with Enrichment", type="primary", use_container_width=True
                )
                if _continue:
                    st.session_state["tab1_phase"] = "enrichment"
                    st.rerun()

            # Enrichment: Steps 2 & 3
            elif st.session_state["tab1_phase"] == "enrichment":
                # Step 2 — AI extraction with live web search (run once, cache in session state)
                if st.session_state["tab1_research"] is None:
                    _research = {}
                    with st.status(
                        "Step 2 of 3: Researching company with AI (live web search)...", expanded=True
                    ) as _status:
                        st.write("Querying OpenAI (gpt-4.1) with live web search for current firmographic data...")
                        st.write("Searching: revenue, employees, HQ, legal name, parent company, AUM, industry")
                        _llm_data = enrich_with_llm([], _account_name)
                        if '_llm_error' in _llm_data:
                            st.warning(f"AI extraction unavailable: {_llm_data['_llm_error']}")
                            if _show_debug and '_llm_traceback' in _llm_data:
                                with st.expander("🔍 Error details"):
                                    st.code(_llm_data['_llm_traceback'])
                            _status.update(
                                label="Step 2: AI extraction failed",
                                state="error",
                            )
                        else:
                            _empty = {None, 'Not found', 'N/A', ''}
                            _fields_found = []
                            for _key, _val in _llm_data.items():
                                # sources is a dict — store as-is without empty-value filtering
                                if _key == 'sources':
                                    if isinstance(_val, dict):
                                        _research[_key] = _val
                                        _fields_found.append(_key)
                                elif _key.startswith('_'):
                                    # Internal metadata keys (e.g. _search_method, _responses_api_error)
                                    _research[_key] = _val
                                elif _val not in _empty:
                                    _research[_key] = _val
                                    _fields_found.append(_key)
                            st.write(f"Extracted {len(_fields_found)} firmographic field(s): {', '.join(_fields_found)}")
                            _search_method_val = _llm_data.get('_search_method')
                            _resp_err = _llm_data.get('_responses_api_error')
                            if _search_method_val == "responses_api_web_search":
                                st.write("✅ Used Responses API (gpt-4.1) with live web search")
                            elif _search_method_val == "chat_completions_fallback":
                                st.warning(
                                    "⚠️ Responses API failed, fell back to Chat Completions (training data only)"
                                )
                            if _resp_err:
                                st.caption(f"ℹ️ Responses API error: {_resp_err}")
                            _status.update(
                                label=f"Step 2: AI extraction complete ({len(_fields_found)} fields)",
                                state="complete",
                            )

                        # Override business_segment and market_segment from hierarchy
                        # (AI only determines detailed_business_segment; roll-ups are auto-derived)
                        _det_seg_llm = _research.get('detailed_business_segment', '')
                        if _det_seg_llm:
                            _seg_resolved = resolve_segment(_det_seg_llm)
                            if _seg_resolved:
                                _research['business_segment'] = _seg_resolved['business']
                                _research['market_segment'] = _seg_resolved['market']

                        # Lookup Parent Account and Reporting Group from SF upload
                        _ult_parent_llm = _research.get('ultimate_parent', '')
                        if _ult_parent_llm and sf_accounts is not None:
                            _sf_parent_acct, _sf_rgroup = lookup_sf_ultimate_parent(sf_accounts, _ult_parent_llm)
                            if _sf_parent_acct:
                                _research['_parent_account'] = _sf_parent_acct
                            if _sf_rgroup:
                                _research['_reporting_group'] = _sf_rgroup
                                _research['_reporting_group_source'] = 'sf'
                            elif _research.get('reporting_group_suggestion'):
                                _research['_reporting_group'] = _research['reporting_group_suggestion']
                                _research['_reporting_group_source'] = 'ai'
                        elif _research.get('reporting_group_suggestion'):
                            _research['_reporting_group'] = _research['reporting_group_suggestion']
                            _research['_reporting_group_source'] = 'ai'

                    st.session_state["tab1_research"] = _research

                # Step 3 — Segmentation (run once, cache in session state)
                if st.session_state["tab1_segmentation"] is None:
                    _research = st.session_state["tab1_research"]
                    _segmentation = {}
                    with st.status(
                        "Step 3 of 3: Applying segmentation logic...", expanded=True
                    ) as _status:
                        st.write(
                            "Applying Customer Segment, Account Category and Secondary Owner rules..."
                        )
                        _segmentation = apply_segmentation(
                            _research, _account_name, _region, _country
                        )
                        _seg = _segmentation.get('customer_segment', '')
                        _colour = {"Enterprise": "🔵", "Mid-Market": "🟡", "Scale-up": "🟢"}.get(
                            _seg, "⚪"
                        )
                        st.write(f"{_colour} Customer Segment: {_seg}")
                        _rationale = _segmentation.get('customer_segment_rationale', '')
                        if "warning" in _rationale.lower() or "verify" in _rationale.lower():
                            st.warning(_rationale)
                        else:
                            st.caption(f"Rationale: {_rationale}")
                        _status.update(
                            label=f"Step 3: Segmentation complete — {_seg}", state="complete"
                        )
                    st.session_state["tab1_segmentation"] = _segmentation

                # Display results from session state
                _research     = st.session_state["tab1_research"]
                _segmentation = st.session_state["tab1_segmentation"]

                st.divider()
                st.markdown(
                    '<p class="fen-section-title">Enrichment Results</p>',
                    unsafe_allow_html=True,
                )

                # ── Salesforce-mirrored layout ──────────────────────────────────
                _seg     = _segmentation.get('customer_segment', '')
                _colour  = {"Enterprise": "🔵", "Mid-Market": "🟡", "Scale-up": "🟢"}.get(_seg, "⚪")
                _seg_display = f"{_colour} {_seg}" if _seg else ""
                _rationale   = _segmentation.get('customer_segment_rationale', '')

                # Source URLs returned by LLM (dict or None)
                _llm_sources = _research.get('sources', {})
                if not isinstance(_llm_sources, dict):
                    _llm_sources = {}

                _URL_DISPLAY_MAX = 60  # max chars to show for a source URL before truncating

                def _source_link_html(url):
                    """Return a small HTML link for a source URL, or empty string."""
                    if url and isinstance(url, str) and url.startswith('http'):
                        display = url if len(url) <= _URL_DISPLAY_MAX else url[:_URL_DISPLAY_MAX - 3] + '...'
                        return (
                            f'<div class="sf-field-note">'
                            f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
                            f'style="font-size:0.75rem;color:#21CFB2;">🔗 {display}</a>'
                            f'</div>'
                        )
                    return ''

                def _sf_field(label, value, greyed=False, note=None, source_url=None, highlight=None):
                    """Return HTML for one Salesforce-style field cell.

                    highlight: 'green' | 'red' | None — applies a background tint to the value.
                    source_url: optional URL rendered as a small clickable link below the value.
                    """
                    css_class    = "sf-field sf-greyed" if greyed else "sf-field"
                    value_stripped = str(value).strip()
                    value_string = value_stripped if value and value_stripped not in ('', 'N/A') else "—"
                    value_class  = "sf-field-value sf-empty" if value_string == "—" else "sf-field-value"
                    note_html    = f'<div class="sf-field-note">{note}</div>' if note else ""
                    src_html     = _source_link_html(source_url)
                    if highlight == 'green':
                        hl_style = 'background:#d4edda;color:#155724;padding:2px 6px;border-radius:4px;'
                    elif highlight == 'red':
                        hl_style = 'background:#f8d7da;color:#721c24;padding:2px 6px;border-radius:4px;'
                    else:
                        hl_style = ''
                    escaped_value = html_escape(value_string) if value_string != "—" else value_string
                    value_inner = (
                        f'<span style="{hl_style}">{escaped_value}</span>'
                        if hl_style and value_string != "—"
                        else escaped_value
                    )
                    return (
                        f'<div class="{css_class}">'
                        f'<div class="sf-field-label">{label}</div>'
                        f'<div class="{value_class}">{value_inner}</div>'
                        f'{note_html}'
                        f'{src_html}'
                        f'</div>'
                    )

                # Account Category colour coding (Issue 7)
                # Use word-boundary regex to avoid false positives like "cat 12" → "cat 1"
                _acct_cat_val = _segmentation.get('account_category', '')
                _acct_cat_lower = str(_acct_cat_val).lower()
                if re.search(r'\bcat\s*[12]\b', _acct_cat_lower):
                    _acct_cat_highlight = 'green'
                elif re.search(r'\bcat\s*3\b', _acct_cat_lower):
                    _acct_cat_highlight = 'red'
                else:
                    _acct_cat_highlight = None

                # Section 1 — About The Account (6 rows × 2 columns)
                _parent_account_disp = _research.get('_parent_account', '')
                _reporting_group_disp = _research.get('_reporting_group', '')
                _rg_source = _research.get('_reporting_group_source', '')
                _rg_note = "AI-generated friendly name (no matching entry in Salesforce)" if _rg_source == 'ai' else None
                _s1_left = [
                    _sf_field("Account Name",            _account_name),
                    _sf_field("Account Type",            _account_type),
                    _sf_field("Parent Account",          _parent_account_disp,
                              greyed=not bool(_parent_account_disp)),
                    _sf_field("Reporting Group",         _reporting_group_disp,
                              greyed=not bool(_reporting_group_disp), note=_rg_note),
                    _sf_field("Account Owner",           "",  greyed=True),
                    _sf_field("Secondary Account Owner", _segmentation.get('secondary_account_owner', '')),
                ]
                _s1_right = [
                    _sf_field("Market Segment",            _research.get('market_segment', '')),
                    _sf_field("Business Segment",          _research.get('business_segment', '')),
                    _sf_field("Detailed Business Segment", _research.get('detailed_business_segment', '')),
                    _sf_field("Customer Segment",          _seg_display,
                              note=_rationale if _rationale else None),
                    _sf_field("Account Category",          _acct_cat_val,
                              note=_segmentation.get('account_category_note', '') or None,
                              highlight=_acct_cat_highlight),
                    _sf_field("Priority Account",          "",  greyed=True),
                ]
                _s1_cells = "".join(left_cell + right_cell for left_cell, right_cell in zip(_s1_left, _s1_right))

                # AUM: always visible; show "N/A — not applicable" when LLM flags it as N/A
                _aum_raw = _research.get('aum_eur', '')
                _aum_display = (
                    "N/A — not applicable"
                    if str(_aum_raw).strip().upper() in ('N/A', 'NOT FOUND', 'NOT APPLICABLE', '')
                    else _aum_raw
                )

                # Section 2 — Supplementary Account Information (4 rows + rationale row)
                _s2_rows = [
                    (_sf_field("BvD ID (Moody's)", "",  greyed=True),
                     _sf_field("Account ID",        "",  greyed=True)),
                    (_sf_field("NAICS Code",         "",  greyed=True),
                     _sf_field("Annual Revenue",     _research.get('annual_revenue_eur', ''),
                               source_url=_llm_sources.get('revenue_source'))),
                    (_sf_field("Legal Name (BvD)",   _research.get('legal_name', '')),
                     _sf_field("Employees",          _research.get('employees', ''),
                               source_url=_llm_sources.get('employees_source'))),
                    (_sf_field("Ultimate Parent",    _research.get('ultimate_parent', '')),
                     _sf_field("AUM (EUR)",          _aum_display,
                               source_url=_llm_sources.get('aum_source'))),
                ]
                _s2_cells = "".join(left_cell + right_cell for left_cell, right_cell in _s2_rows)
                # Industry Classification Rationale spans left column only
                _s2_cells += (
                    _sf_field("Industry Classification Rationale",
                              _research.get('industry_classification_rationale', ''))
                    + '<div class="sf-field"></div>'
                )

                st.markdown(f"""
<div class="sf-layout">
  <div class="sf-section">
    <div class="sf-section-header">About The Account</div>
    <div class="sf-fields-grid">{_s1_cells}</div>
  </div>
  <div class="sf-section">
    <div class="sf-section-header">Supplementary Account Information</div>
    <div class="sf-fields-grid">{_s2_cells}</div>
  </div>
</div>
""", unsafe_allow_html=True)

                # Data freshness indicator
                _search_method_display = _research.get('_search_method')
                _resp_api_err_display = _research.get('_responses_api_error')
                if _search_method_display == "responses_api_web_search":
                    st.success("🌐 Data sourced from live web search (OpenAI gpt-4.1)")
                elif _search_method_display == "chat_completions_fallback":
                    _err_detail = f" Last error: {_resp_api_err_display}." if _resp_api_err_display else ""
                    st.warning(
                        f"⚠️ Data sourced from AI training data (may be outdated).{_err_detail} "
                        "Responses API with web_search was unavailable; fell back to Chat Completions."
                    )

                # Alternative segment warning (Change 6)
                _alt_seg = _research.get('alternative_detailed_business_segment', '')
                if _alt_seg:
                    st.warning(
                        f"⚠️ **Multiple Detailed Business Segments could apply** for this company: "
                        f"**{_research.get('detailed_business_segment', '')}** (selected) and "
                        f"**{_alt_seg}** (alternative). "
                        "Please review and confirm the most appropriate segment."
                    )

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
    MAX_TOP_MATCHES_TO_CONSIDER = 10

    st.markdown(f"""
    Upload a **New Customer** file (CSV or Excel) containing a list of customer names.  
    The tool will fuzzy-match each name against **Account Name** and **Legal Name**  
    in the **Salesforce Accounts CSV** uploaded in the sidebar,  
    returning a combined confidence score, a primary suggested match, and a secondary match where applicable.

    **Scoring rules:**
    - **100%** = exact Account Name match (after normalisation) — no blending applied
    - Otherwise: **{int(ACCT_WEIGHT*100)}% Account Name** + **{int(LEGAL_WEIGHT*100)}% Legal Name** weighted blend
    - Both the matched Account Name and Legal Name are shown for Primary and Secondary matches
    """)

    new_customer_file = st.file_uploader(
        "Upload New Customer File (CSV or Excel)",
        type=["csv", "xlsx", "xls"],
        key="account_matching_upload",
        help="Maximum recommended file size: 10 MB",
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

        new_country_col_candidates = [c for c in new_customers_df.columns if 'country' in c.lower()]
        new_customer_country_col_options = ["(none)"] + new_customers_df.columns.tolist()
        default_country_idx = 0
        if new_country_col_candidates:
            default_country_idx = new_customer_country_col_options.index(new_country_col_candidates[0])
        new_customer_country_col_raw = st.selectbox(
            "Select the Country column in the New Customer file (optional — used to refine match suggestions):",
            options=new_customer_country_col_options,
            index=default_country_idx,
            key="new_cust_country_col"
        )
        new_customer_country_col = new_customer_country_col_raw if new_customer_country_col_raw != "(none)" else None

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
            sf_legal_name_col = pick_col(primary_terms=['legal name'], secondary_terms=['legal'])
            sf_country_col = pick_col(primary_terms=['country'], secondary_terms=[])

            detected_columns = []
            if sf_account_name_col:
                detected_columns.append(f'Account Name → "{sf_account_name_col}"')
            if sf_legal_name_col:
                detected_columns.append(f'Legal Name → "{sf_legal_name_col}"')
            if sf_country_col:
                detected_columns.append(f'Country → "{sf_country_col}"')
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
                new_customer_country_map = {}
                if new_customer_country_col:
                    country_df = new_customers_df[[name_column, new_customer_country_col]].drop_duplicates(
                        subset=[name_column],
                        keep="first"
                    )
                    for _, country_row in country_df.iterrows():
                        row_name = str(country_row.get(name_column, "")).strip()
                        row_country = country_row.get(new_customer_country_col, "")
                        if row_name and pd.notna(row_country):
                            new_customer_country_map[row_name] = str(row_country).strip().lower()

                sf_records = sf_accounts.to_dict("records")

                # Pre-compute normalised names for every SF record once to avoid
                # repeated normalize_name() calls inside the inner loop (O(n²) → O(n+m)).
                sf_records_normalised = []
                for row in sf_records:
                    acct_name_val = ""
                    acct_norm = ""
                    if sf_account_name_col:
                        val = row.get(sf_account_name_col, "")
                        if pd.notna(val):
                            val_str = str(val).strip()
                            if val_str:
                                acct_name_val = val_str
                                acct_norm = normalize_name(val_str)
                    legal_name_val = ""
                    legal_norm = ""
                    if sf_legal_name_col:
                        val = row.get(sf_legal_name_col, "")
                        if pd.notna(val):
                            val_str = str(val).strip()
                            if val_str:
                                legal_name_val = val_str
                                legal_norm = normalize_name(val_str)
                    sf_country_val = ""
                    if sf_country_col:
                        raw = row.get(sf_country_col, "")
                        sf_country_val = str(raw).strip() if pd.notna(raw) else ""
                    sf_records_normalised.append((
                        acct_name_val, acct_norm,
                        legal_name_val, legal_norm,
                        sf_country_val,
                    ))

                results = []
                progress = st.progress(0, text="Matching accounts...")

                total = len(new_names)
                for i, new_name in enumerate(new_names):
                    new_norm = normalize_name(new_name)

                    # Each entry: (rep_score, acct_name_val, legal_name_val, sf_country_val, acct_score, legal_score)
                    top_matches = []

                    for acct_name_val, acct_norm, legal_name_val, legal_norm, sf_country_val in sf_records_normalised:
                        # ── Score against Account Name column ──────────────────────────
                        acct_score = 0
                        if acct_name_val:
                            acct_score = compute_match_score(new_norm, acct_norm)

                        # ── Score against Legal Name column ────────────────────────────
                        legal_score = 0
                        if legal_name_val:
                            legal_score = compute_match_score(new_norm, legal_norm)

                        # ── Combined score ─────────────────────────────────────────────
                        # If account name is exact (100) → overall = 100.
                        # Otherwise → 70% acct + 30% legal weighted blend.
                        rep_score = combined_score(acct_score, legal_score)

                        if rep_score > 0 and acct_name_val:
                            top_matches.append((
                                rep_score,
                                acct_name_val,
                                legal_name_val,
                                sf_country_val,
                                acct_score,
                                legal_score,
                            ))

                    # Sort by combined score descending, keep top N
                    top_matches = sorted(top_matches, key=lambda x: x[0], reverse=True)[:MAX_TOP_MATCHES_TO_CONSIDER]
                    new_cust_country = new_customer_country_map.get(str(new_name).strip(), "")

                    # ── Filter by confidence threshold ─────────────────────────────────
                    primary_name       = "No match found"
                    primary_legal      = NO_VALUE_PLACEHOLDER
                    primary_score      = None
                    primary_sf_country = ""
                    secondary_name     = NO_VALUE_PLACEHOLDER
                    secondary_legal    = NO_VALUE_PLACEHOLDER
                    secondary_score    = None

                    if top_matches:
                        eligible = [m for m in top_matches if m[0] >= confidence_threshold]

                        # Country-aware re-sort: country match used as tiebreaker
                        if eligible and new_cust_country:
                            eligible = sorted(
                                eligible,
                                key=lambda x: (
                                    x[0],
                                    1 if str(x[3] or "").strip().lower() == new_cust_country else 0,
                                ),
                                reverse=True
                            )

                        if eligible:
                            primary_score      = round(eligible[0][0], 1)
                            primary_name       = eligible[0][1]
                            primary_legal      = eligible[0][2] if eligible[0][2] else NO_VALUE_PLACEHOLDER
                            primary_sf_country = eligible[0][3]
                            if len(eligible) > 1:
                                secondary_score = round(eligible[1][0], 1)
                                secondary_name  = eligible[1][1]
                                secondary_legal = eligible[1][2] if eligible[1][2] else NO_VALUE_PLACEHOLDER
                        else:
                            primary_name  = "No match found"
                            primary_score = None

                    # ── Country match flag ─────────────────────────────────────────────
                    country_match_flag = ""
                    if new_cust_country and primary_sf_country:
                        country_match_flag = "✅" if primary_sf_country.strip().lower() == new_cust_country else "⬜"

                    results.append({
                        "New Customer Name":          new_name,
                        "Primary Match (Account)":    primary_name,
                        "Primary Match (Legal Name)": primary_legal,
                        "Confidence Score (%)":       primary_score if primary_score is not None else NO_VALUE_PLACEHOLDER,
                        "Country Match":              country_match_flag,
                        "Secondary Match (Account)":    secondary_name,
                        "Secondary Match (Legal Name)": secondary_legal,
                        "Secondary Confidence (%)":   secondary_score if secondary_score is not None else NO_VALUE_PLACEHOLDER,
                    })

                    if (i + 1) % max(1, total // 20) == 0 or i == total - 1:
                        progress.progress((i + 1) / total, text=f"Matching accounts... {i+1}/{total}")

                progress.empty()

                results_df = pd.DataFrame(results)

                matched   = results_df[results_df["Primary Match (Account)"] != "No match found"]
                unmatched = results_df[results_df["Primary Match (Account)"] == "No match found"]
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

                styled_df = results_df.style.map(
                    _highlight_conf,
                    subset=["Confidence Score (%)"]
                )
                st.dataframe(styled_df, use_container_width=True, hide_index=True)

                export_df = results_df.copy()
                for col in ["Confidence Score (%)", "Secondary Confidence (%)"]:
                    export_df[col] = export_df[col].replace(NO_VALUE_PLACEHOLDER, "")
                for col in ["Secondary Match (Account)", "Secondary Match (Legal Name)", "Primary Match (Legal Name)"]:
                    export_df[col] = export_df[col].replace(NO_VALUE_PLACEHOLDER, "")

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

# ===============================================
# TAB 5 — CUSTOMER SEGMENT LOGIC
# ===============================================
with tab5:
    st.markdown('<p class="fen-section-title">Customer Segment Logic</p>', unsafe_allow_html=True)
    st.markdown("""
This tab explains how the **Customer Segment** (Enterprise / Mid-Market / Scale-up) is derived for each account.
The classification is based on the account's **Market Segment** combined with key financial metrics.
""")

    # Key rules callout
    st.info("""
**Key Rules:**
- 🏆 **"Highest tier wins"** — if *any single metric* reaches the Enterprise threshold, the result is **Enterprise**, regardless of other metrics.
- ❓ **All metrics unknown** — if AUM, Revenue, and Employees are all unavailable, the account defaults to **Scale-up**.
- 🏦 **Full-Service Banks** — classification is special: the account must have **G-SIB or D-SIB designation** to be classified as Enterprise. Without it, the Banks thresholds apply instead.
- 📊 **Metrics evaluated independently** — each metric (AUM, Revenue, Employees) is assessed on its own; any single Enterprise-level metric triggers Enterprise.
""")

    # Segmentation threshold data for the table
    _seg_data = [
        {
            "Market Segment": "Banks",
            "Metric": "AUM (Assets)",
            "Scale-up": "< €10bn",
            "Mid-Market": "€10bn – €200bn",
            "Enterprise": "> €200bn",
        },
        {
            "Market Segment": "Banks",
            "Metric": "Annual Revenue",
            "Scale-up": "< €2bn",
            "Mid-Market": "€2bn – €10bn",
            "Enterprise": "> €10bn",
        },
        {
            "Market Segment": "Banks",
            "Metric": "Employees (FTE)",
            "Scale-up": "< 1,000",
            "Mid-Market": "1,000 – 5,000",
            "Enterprise": "> 5,000",
        },
        {
            "Market Segment": "Asset Mgmt., Servicing & Insurance",
            "Metric": "AUM (Assets)",
            "Scale-up": "< €10bn",
            "Mid-Market": "€10bn – €100bn",
            "Enterprise": "> €100bn",
        },
        {
            "Market Segment": "Asset Mgmt., Servicing & Insurance",
            "Metric": "Annual Revenue",
            "Scale-up": "< €2bn",
            "Mid-Market": "€2bn – €10bn",
            "Enterprise": "> €10bn",
        },
        {
            "Market Segment": "Asset Mgmt., Servicing & Insurance",
            "Metric": "Employees (FTE)",
            "Scale-up": "< 150",
            "Mid-Market": "150 – 1,000",
            "Enterprise": "> 1,000",
        },
        {
            "Market Segment": "Corporates",
            "Metric": "Annual Revenue",
            "Scale-up": "< €2bn",
            "Mid-Market": "€2bn – €10bn",
            "Enterprise": "> €10bn",
        },
        {
            "Market Segment": "Corporates",
            "Metric": "Employees (FTE)",
            "Scale-up": "< 1,000",
            "Mid-Market": "1,000 – 5,000",
            "Enterprise": "> 5,000",
        },
        {
            "Market Segment": "Fintech",
            "Metric": "Annual Revenue",
            "Scale-up": "< €500m",
            "Mid-Market": "€500m – €10bn",
            "Enterprise": "> €10bn",
        },
        {
            "Market Segment": "Fintech",
            "Metric": "Employees (FTE)",
            "Scale-up": "< 250",
            "Mid-Market": "250 – 1,000",
            "Enterprise": "> 1,000",
        },
        {
            "Market Segment": "Other / Default",
            "Metric": "Annual Revenue",
            "Scale-up": "< €2bn",
            "Mid-Market": "€2bn – €10bn",
            "Enterprise": "> €10bn",
        },
        {
            "Market Segment": "Other / Default",
            "Metric": "Employees (FTE)",
            "Scale-up": "< 1,000",
            "Mid-Market": "1,000 – 5,000",
            "Enterprise": "> 5,000",
        },
    ]

    _seg_df = pd.DataFrame(_seg_data)

    def _colour_tier(val):
        if val and ">" in str(val):
            return "background-color: #d4edda; color: #155724; font-weight: 600;"
        if val and "–" in str(val):
            return "background-color: #fff3cd; color: #856404; font-weight: 600;"
        if val and "<" in str(val):
            return "background-color: #f8d7da; color: #721c24; font-weight: 600;"
        return ""

    _styled_seg = (
        _seg_df.style
        .map(_colour_tier, subset=["Scale-up", "Mid-Market", "Enterprise"])
        .set_properties(**{"text-align": "left"})
    )
    st.dataframe(_styled_seg, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🏦 Full-Service Banks — Special Classification Logic")
    st.markdown("""
Full-Service Banks follow a distinct classification path:

| Designation | How classified | Notes |
|---|---|---|
| **G-SIB** (Global Systemically Important Bank) | Automatically **Enterprise** | The G-SIB list is maintained in the code (`GSIB_LIST`). If the account name matches any G-SIB, it is immediately classified as Enterprise. |
| **D-SIB** (Domestic Systemically Important Bank) | **Enterprise** after verification | D-SIBs are matched against a static list by country (`DSIB_LIST`). A warning is shown to verify with the local regulator before finalising. |
| **Neither G-SIB nor D-SIB** | Falls back to **Banks** thresholds | AUM / Revenue / Employees thresholds for "Banks" are applied as normal. |

> ⚠️ The D-SIB list is maintained in the application code and should be kept up to date. D-SIB designations can change — always verify with the relevant local regulator.
""")

    st.markdown("---")
    st.markdown("### 📝 Notes")
    st.markdown("""
- **AUM** (Assets Under Management) is primarily relevant for Banks and Asset Management firms. For Corporates and Fintechs, it is typically N/A.
- **Revenue** figures should be in EUR billions (€bn). The LLM converts values from other currencies automatically.
- **Employees** refers to full-time equivalent (FTE) headcount.
- When both Revenue and Employees are known, **either one** can independently trigger Enterprise or Mid-Market — the highest tier wins.
- The "Other / Default" thresholds apply to any Market Segment not explicitly listed above (e.g. Other, Precious Metals, Legal Services, etc.).
""")

# ===============================================
# TAB 6 — FENERGO SEGMENTATION
# ===============================================
with tab6:
    st.markdown('<p class="fen-section-title">Fenergo Segmentation Hierarchy</p>', unsafe_allow_html=True)
    st.markdown("""
This tab shows the full **three-level segmentation hierarchy** used by Fenergo.
Every account is classified across three levels:

> **Market Segment** → **Business Segment** → **Detailed Business Segment**

The Detailed Business Segment drives the **Customer Segment**, **Account Category**, and **Secondary Account Owner** assignments.
""")

    # Build a grouped structure from SEGMENT_HIERARCHY
    _hier_dict = {}
    for (detailed, business, market) in SEGMENT_HIERARCHY:
        _hier_dict.setdefault(market, {}).setdefault(business, []).append(detailed)

    # Display each Market Segment as an expandable section
    for _market_seg, _business_segs in _hier_dict.items():
        with st.expander(f"🏛️ **{_market_seg}**", expanded=False):
            for _biz_seg, _detailed_segs in _business_segs.items():
                st.markdown(f"**📂 {_biz_seg}**")
                _ds_items = "  \n".join(f"&nbsp;&nbsp;&nbsp;&nbsp;• {ds}" for ds in _detailed_segs)
                st.markdown(_ds_items, unsafe_allow_html=True)
            # Special note for Full-Service Banks
            if _market_seg == "Full-Service Banks":
                st.info("""
**Full-Service Banks — classification logic:**

Accounts in this segment require a **G-SIB or D-SIB designation** to be classified as Enterprise.

- **G-SIBs** (Global Systemically Important Banks) are automatically classified as Enterprise based on the GSIB_LIST maintained in the code. This list includes major global banks (JPMorgan Chase, HSBC, Deutsche Bank, BNP Paribas, etc.).
- **D-SIBs** (Domestic Systemically Important Banks) are matched against a country-specific DSIB_LIST. A verification warning is shown — always confirm with the local regulator, as designations can change.
- Banks that are **neither G-SIB nor D-SIB** fall back to the standard **Banks** segment thresholds (AUM / Revenue / Employees).
""")

    st.markdown("---")

    # Full hierarchy table view
    st.markdown("### 📋 Complete Hierarchy Table")
    _hier_df = pd.DataFrame(SEGMENT_HIERARCHY, columns=["Detailed Business Segment", "Business Segment", "Market Segment"])
    _hier_df = _hier_df[["Market Segment", "Business Segment", "Detailed Business Segment"]]
    st.dataframe(_hier_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 📝 Notes")
    st.markdown("""
- The **Detailed Business Segment** is the most granular classification — it is what the LLM assigns based on the company's industry and activities.
- The **Business Segment** is the mid-level grouping (e.g. "Asset & Wealth Mgmt." groups together Asset Management, Hedge Funds, Pension Funds, etc.).
- The **Market Segment** is the top-level grouping that drives the Customer Segment thresholds (see the **Customer Segment Logic** tab).
- These three levels are used together to determine the **Account Category** (via the account category matrix) and the **Secondary Account Owner**.
- The G-SIB and D-SIB lists (`GSIB_LIST` and `DSIB_LIST`) are maintained in the application code and should be reviewed periodically to ensure accuracy.
""")
