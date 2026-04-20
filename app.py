import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from datetime import datetime
import re

# -----------------------------------------------
# PAGE CONFIG
# -----------------------------------------------
st.set_page_config(page_title="Salesforce Account Enrichment", layout="wide")
st.title("🏦 Salesforce Account Enrichment Tool")

# -----------------------------------------------
# APPROVED SEGMENTATION HIERARCHY
# Detailed Business Segment → Business Segment → Market Segment
# -----------------------------------------------
SEGMENT_HIERARCHY = [
    # Asset Mgmt., Servicing & Insurance
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
    # Banks
    ("Investment / Institutional Banking",             "C&IB",                           "Banks"),
    ("Central Banking",                                "Commercial & Business",          "Banks"),
    ("Commercial Banking",                             "Commercial & Business",          "Banks"),
    ("Business Banking",                               "Commercial & Business",          "Banks"),
    ("Financial Services",                             "Commercial & Business",          "Banks"),
    ("Community Bank",                                 "Retail",                         "Banks"),
    ("Credit Union",                                   "Retail",                         "Banks"),
    ("Retail Banking",                                 "Retail",                         "Banks"),
    ("Mutual Savings Bank",                            "Retail",                         "Banks"),
    # Corporates
    ("Exchanges and Commodity Trading",                "Exchanges and Commodity trading","Corporates"),
    ("Market Maker",                                   "Exchanges and Commodity trading","Corporates"),
    ("Oil & Gas",                                      "Oil & Gas",                      "Corporates"),
    ("Energy",                                         "Energy",                         "Corporates"),
    ("Renewable Energy",                               "Energy",                         "Corporates"),
    # Fintech
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
    # Full-Service Banks
    ("Full-Service Banks",                             "Full-Service Banks",             "Full-Service Banks"),
    # Other
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
    "bnp paribas", "crédit agricole", "groupe bpce", "société générale",
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
    "germany":      ["commerzbank", "dz bank", "landesbank baden-württemberg", "lbbw", "bayerische landesbank", "norddeutsche landesbank"],
    "france":       ["la banque postale", "crédit mutuel"],
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
    "brazil":       ["itaú unibanco", "bradesco", "caixa econômica", "banco do brasil"],
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
# SIDEBAR — Salesforce Account List Upload
# -----------------------------------------------
st.sidebar.header("📂 Salesforce Account List")
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
        return {}, "⚠️ account_category_matrix.xlsx not found in repo root"
    except Exception as e:
        return {}, f"⚠️ Error loading matrix: {str(e)}"

matrix_lookup, matrix_error = load_account_category_matrix()
if matrix_error:
    st.sidebar.warning(matrix_error)
else:
    st.sidebar.success(f"✅ Account category matrix loaded ({len(set(k[0] for k in matrix_lookup.keys()))} countries)")

# -----------------------------------------------
# MAIN FORM
# -----------------------------------------------
st.subheader("Enter Account Details")
col1, col2, col3, col4 = st.columns(4)
with col1:
    account_name = st.text_input("Account Name *", placeholder="e.g. Bank of Ireland")
with col2:
    account_type = st.selectbox("Account Type *", ["Other", "Partner"])
with col3:
    region = st.selectbox("Region *", ["EMEA", "APAC", "Americas", "UK & Ireland"])
with col4:
    country = st.text_input("Country *", placeholder="e.g. Ireland")

run_button = st.button("🔍 Run Enrichment Checks", type="primary", use_container_width=True)

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


def check_duplicate(sf_accounts, account_name, region, country):
    if sf_accounts is None:
        return [], "⚠️ No Salesforce account list uploaded — skipping duplicate check"
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
    """Parse strings like '$2.3B', '€10bn', '500m' → float in billions. Returns None if unparseable."""
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
    """Parse employee count string → int. Returns None if unparseable."""
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
    """
    Returns (is_eligible, classification, warning_message)
    G-SIB → eligible, no warning
    D-SIB → eligible, always flag for human confirmation
    Neither → NOT eligible, downgrade to Banks, flag for review
    """
    if is_gsib(account_name):
        return True, "G-SIB", None
    if is_dsib(account_name):
        return True, "D-SIB (static list match)", (
            "⚠️ D-SIB match found on static list — please confirm against your "
            "local regulator's current D-SIB designation before assigning Full-Service Banks."
        )
    return False, "Neither G-SIB nor D-SIB", (
        "⚠️ This institution is not on the G-SIB list and was not found on the static D-SIB list. "
        "It has been classified as **Banks**. If you believe this is a D-SIB, verify with the "
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
        if e_hit:   return "Enterprise", rationale
        if m_hit:   return "Mid-Market", rationale
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
            if aum_bn > 200:   e = True;  parts.append(f"AUM {aum_bn:.1f}bn > 200bn (Enterprise)")
            elif aum_bn >= 10: m = True;  parts.append(f"AUM {aum_bn:.1f}bn in 10–200bn (Mid-Market)")
            else:                         parts.append(f"AUM {aum_bn:.1f}bn < 10bn (Scale-up)")
        if revenue_bn is not None:
            if revenue_bn > 10:   e = True;  parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
            elif revenue_bn >= 2: m = True;  parts.append(f"Revenue {revenue_bn:.1f}bn in 2–10bn (Mid-Market)")
            else:                            parts.append(f"Revenue {revenue_bn:.1f}bn < 2bn (Scale-up)")
        if employees is not None:
            if employees > 5000:    e = True;  parts.append(f"{employees:,} FTE > 5,000 (Enterprise)")
            elif employees >= 1000: m = True;  parts.append(f"{employees:,} FTE in 1,000–5,000 (Mid-Market)")
            else:                              parts.append(f"{employees:,} FTE < 1,000 (Scale-up)")
        return tier(e, m, parts)

    if seg == "Asset Mgmt., Servicing & Insurance":
        e, m, parts = False, False, []
        if aum_bn is not None:
            if aum_bn > 100:   e = True;  parts.append(f"AUM {aum_bn:.1f}bn > 100bn (Enterprise)")
            elif aum_bn >= 10: m = True;  parts.append(f"AUM {aum_bn:.1f}bn in 10–100bn (Mid-Market)")
            else:                         parts.append(f"AUM {aum_bn:.1f}bn < 10bn (Scale-up)")
        if revenue_bn is not None:
            if revenue_bn > 10:   e = True;  parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
            elif revenue_bn >= 2: m = True;  parts.append(f"Revenue {revenue_bn:.1f}bn in 2–10bn (Mid-Market)")
            else:                            parts.append(f"Revenue {revenue_bn:.1f}bn < 2bn (Scale-up)")
        if employees is not None:
            if employees > 1000:  e = True;  parts.append(f"{employees:,} FTE > 1,000 (Enterprise)")
            elif employees >= 150: m = True; parts.append(f"{employees:,} FTE in 150–1,000 (Mid-Market)")
            else:                            parts.append(f"{employees:,} FTE < 150 (Scale-up)")
        return tier(e, m, parts)

    if seg == "Corporates":
        e, m, parts = False, False, []
        if revenue_bn is not None:
            if revenue_bn > 10:   e = True;  parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
            elif revenue_bn >= 2: m = True;  parts.append(f"Revenue {revenue_bn:.1f}bn in 2–10bn (Mid-Market)")
            else:                            parts.append(f"Revenue {revenue_bn:.1f}bn < 2bn (Scale-up)")
        if employees is not None:
            if employees > 5000:    e = True;  parts.append(f"{employees:,} FTE > 5,000 (Enterprise)")
            elif employees >= 1000: m = True;  parts.append(f"{employees:,} FTE in 1,000–5,000 (Mid-Market)")
            else:                              parts.append(f"{employees:,} FTE < 1,000 (Scale-up)")
        return tier(e, m, parts)

    if seg == "Fintech":
        e, m, parts = False, False, []
        if revenue_bn is not None:
            if revenue_bn > 10:     e = True;  parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
            elif revenue_bn >= 0.5: m = True;  parts.append(f"Revenue {revenue_bn:.1f}bn in 0.5–10bn (Mid-Market)")
            else:                              parts.append(f"Revenue {revenue_bn:.1f}bn < 500m (Scale-up)")
        if employees is not None:
            if employees > 1000:  e = True;  parts.append(f"{employees:,} FTE > 1,000 (Enterprise)")
            elif employees >= 250: m = True; parts.append(f"{employees:,} FTE in 250–1,000 (Mid-Market)")
            else:                            parts.append(f"{employees:,} FTE < 250 (Scale-up)")
        return tier(e, m, parts)

    # Others / catch-all
    e, m, parts = False, False, []
    if revenue_bn is not None:
        if revenue_bn > 10:   e = True;  parts.append(f"Revenue {revenue_bn:.1f}bn > 10bn (Enterprise)")
        elif revenue_bn >= 2: m = True;  parts.append(f"Revenue {revenue_bn:.1f}bn in 2–10bn (Mid-Market)")
        else:                            parts.append(f"Revenue {revenue_bn:.1f}bn < 2bn (Scale-up)")
    if employees is not None:
        if employees > 5000:    e = True;  parts.append(f"{employees:,} FTE > 5,000 (Enterprise)")
        elif employees >= 1000: m = True;  parts.append(f"{employees:,} FTE in 1,000–5,000 (Mid-Market)")
        else:                              parts.append(f"{employees:,} FTE < 1,000 (Scale-up)")
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
        return "⚠️ Matrix not loaded", "Matrix file could not be loaded"
    country_keys   = set(k[0] for k in matrix_lookup.keys())
    matched_country = fuzzy_country_match(country, country_keys)
    if not matched_country:
        return "⚠️ No match found", f"Country '{country}' not found in matrix"
    lookup_key = (matched_country, str(business_segment).strip().lower(), str(customer_segment).strip().lower())
    if lookup_key in matrix_lookup:
        return matrix_lookup[lookup_key], f"Matched: {matched_country.title()} | {business_segment} | {customer_segment}"
    return "⚠️ No match found", f"No matrix entry for {matched_country.title()} + {business_segment} + {customer_segment}"


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

    return "⚠️ Region not recognised — please assign manually"


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
# MAIN LOGIC
# -----------------------------------------------

if run_button:
    if not account_name.strip() or not region or not country.strip():
        st.error("Please fill in all required fields: Account Name, Region, and Country.")
        st.stop()

    st.divider()
    st.subheader(f"🔄 Running checks for: **{account_name}**")

    # ── PARTNER ACCOUNT FLOW ─────────────────────────────────────────────
    if account_type == "Partner":
        st.info("ℹ️ **Partner Account** — only a Region/Country duplicate check is required.")

        with st.status("Checking for existing Partner account...", expanded=True) as status:
            st.write(f"Searching for `{account_name}` in region `{region}` / country `{country}`...")
            st.write(f"Also checking variations: {generate_name_variations(account_name)}")
            matches, warning = check_duplicate(sf_accounts, account_name, region, country)

            if warning:
                st.warning(warning)
                status.update(label="⚠️ Duplicate check skipped — no file uploaded", state="error")
            elif matches:
                same_region = [m for m in matches if '🔴' in m['Same Region']]
                if same_region:
                    st.error("🚨 Existing Partner account found in the **same region**!")
                    st.dataframe(pd.DataFrame(same_region), use_container_width=True, hide_index=True)
                    st.warning("⚠️ **Please check with Ken before proceeding.**")
                    status.update(label="🚨 Duplicate detected — escalate to Ken", state="error")
                else:
                    st.warning("Similar account name found but in a **different region** — review below:")
                    st.dataframe(pd.DataFrame(matches), use_container_width=True, hide_index=True)
                    status.update(label="⚠️ Similar account found (different region)", state="complete")
            else:
                st.success(f"✅ No existing Partner account found for **{account_name}** in {region} / {country}")
                status.update(label="✅ No duplicate found — safe to proceed", state="complete")

    # ── ALL OTHER ACCOUNTS FLOW ──────────────────────────────────────────
    else:
        duplicate_ok = True

        # STEP 1 — Duplicate Check
        with st.status("Step 1 of 3: Checking for existing account in Salesforce...", expanded=True) as status:
            st.write(f"Searching for `{account_name}` and variations: {generate_name_variations(account_name)}")
            matches, warning = check_duplicate(sf_accounts, account_name, region, country)

            if warning:
                st.warning(warning)
                status.update(label="⚠️ Step 1: Duplicate check skipped — no file uploaded", state="error")
            elif matches:
                same_region = [m for m in matches if '🔴' in m['Same Region']]
                if same_region:
                    st.error("🚨 Potential duplicate found in the **same region!**")
                    st.dataframe(pd.DataFrame(same_region), use_container_width=True, hide_index=True)
                    st.warning("⚠️ **Please check with Ken before proceeding.** Enrichment has been paused.")
                    status.update(label="🚨 Step 1: Duplicate detected — check with Ken", state="error")
                    duplicate_ok = False
                else:
                    st.warning("Similar name found but in a different region:")
                    st.dataframe(pd.DataFrame(matches), use_container_width=True, hide_index=True)
                    st.info("ℹ️ Proceeding with enrichment — review the match above carefully.")
                    status.update(label="⚠️ Step 1: Similar name (different region) — review carefully", state="complete")
            else:
                st.success(f"✅ No existing account found for **{account_name}** in {region}")
                status.update(label="✅ Step 1: No duplicate found", state="complete")

        if not duplicate_ok:
            st.stop()

        # STEP 2 — Web Research
        research = {}
        with st.status("Step 2 of 3: Researching company on the web...", expanded=True) as status:
            st.write("🔍 Querying: revenue, employees, HQ, legal name, parent company, AUM, industry")
            st.write("📡 Sources: DuckDuckGo → company site, Wikipedia, Bloomberg, Reuters, Crunchbase")
            research = web_research(account_name)
            if 'error' in research:
                st.error(f"Search error: {research['error']}")
                status.update(label="❌ Step 2: Web research failed", state="error")
            else:
                st.write(f"✅ Retrieved {len(research['snippets'])} results from {len(research['sources'])} sources")
                for src in research['sources'][:4]:
                    st.write(f"  - {src}")
                status.update(label=f"✅ Step 2: Web research complete ({len(research['sources'])} sources)", state="complete")

        # STEP 3 — Segmentation
        segmentation = {}
        with st.status("Step 3 of 3: Applying segmentation logic...", expanded=True) as status:
            st.write("📋 Applying Customer Segment, Account Category and Secondary Owner rules...")
            segmentation = apply_segmentation(research, account_name, region, country)

            seg    = segmentation.get('customer_segment', '')
            colour = {"Enterprise": "🔵", "Mid-Market": "🟡", "Scale-up": "🟢"}.get(seg, "⚪")
            st.write(f"{colour} **Customer Segment → {seg}**")

            rationale = segmentation.get('customer_segment_rationale', '')
            if "⚠️" in rationale:
                st.warning(rationale)
            else:
                st.caption(f"Rationale: {rationale}")

            status.update(label=f"✅ Step 3: Segmentation complete — {seg}", state="complete")

        # ── RESULTS ─────────────────────────────────────────────────────
        st.divider()
        st.subheader("📊 Enrichment Results")

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### 🏷️ Segment Information")
            st.dataframe(pd.DataFrame({
                "Field": ["Detailed Business Segment", "Business Segment", "Market Segment"],
                "Value": [
                    research.get('detailed_business_segment', 'N/A'),
                    research.get('business_segment', 'N/A'),
                    research.get('market_segment', 'N/A'),
                ]
            }), use_container_width=True, hide_index=True)

            st.markdown("#### 🌐 Parent Information")
            st.dataframe(pd.DataFrame({
                "Field": ["Ultimate Parent", "Ultimate Parent HQ"],
                "Value": [
                    research.get('ultimate_parent', 'N/A'),
                    research.get('ultimate_parent_hq', 'N/A'),
                ]
            }), use_container_width=True, hide_index=True)

        with col_b:
            st.markdown("#### 📈 Other Metrics")
            aum_segments = ['Full-Service Banks', 'Banks', 'Asset Mgmt., Servicing & Insurance']
            show_aum     = research.get('market_segment', '') in aum_segments

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

            st.markdown("#### 🗂️ Account Categorisation")
          
            seg    = segmentation.get('customer_segment', 'N/A')
            colour = {"Enterprise": "🔵", "Mid-Market": "🟡", "Scale-up": "🟢"}.get(seg, "⚪")
            st.dataframe(pd.DataFrame({
                "Field": [
                    "Customer Segment",
                    "Segment Rationale",
                    "Account Category",
                    "Account Category Note",
                    "Secondary Account Owner"
                ],
                "Value": [
                    f"{colour} {seg}",
                    segmentation.get('customer_segment_rationale', 'N/A'),
                    segmentation.get('account_category', 'N/A'),
                    segmentation.get('account_category_note', 'N/A'),
                    segmentation.get('secondary_account_owner', 'N/A'),
                ]
            }), use_container_width=True, hide_index=True)

        with st.expander("🔍 View raw web search results (for manual review)"):
            for i, item in enumerate(research.get('snippets', []), 1):
                st.markdown(f"**Result {i}** — _{item['query']}_")
                st.write(f"Source: {item['source']}")
                st.write(item['snippet'])
                st.divider()
