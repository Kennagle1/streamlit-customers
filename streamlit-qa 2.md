# Skill: Streamlit App QA Testing

Use this skill to systematically test a Streamlit web application for bugs,
regressions, and quality issues. Works for any Streamlit app in the Analytics
project family.

## When to Use

- After building or modifying a Streamlit app
- Before deploying to Streamlit Cloud
- When a user reports an issue and you need a full regression check
- Periodic health checks on running apps

## Inputs

The agent needs:
- **App directory**: path to the Streamlit project root (e.g. `Finance_Hub/`, `Learning_Development/`)
- **App entry point**: typically `app.py`
- **Port**: default 8501, or specify if another instance is running

## Test Stages

### Stage 1 -- Static Analysis (no server needed)

Run these checks before starting the app.

**1a. Import validation**

For every `.py` file in the project, verify it imports cleanly:

```python
import importlib, sys
sys.path.insert(0, '<app_dir>')
for module in [list all .py files as module paths]:
    importlib.import_module(module)
```

Report any `ImportError`, `ModuleNotFoundError`, or `SyntaxError`.

**1b. Python 3.9 compatibility**

Check that every file containing `def` or `class` includes
`from __future__ import annotations`. This prevents `X | Y` type hint
failures on Streamlit Cloud (which may run Python 3.9).

```bash
grep -rL "from __future__ import annotations" *.py pages/*.py components/*.py loaders/*.py 2>/dev/null
```

**1c. Streamlit key uniqueness**

Scan all pages for `key=` parameters in Streamlit widgets. Report any
duplicate keys within the same page or across pages that share a session.

```python
import re, glob
keys = {}
for f in glob.glob('**/*.py', recursive=True):
    for i, line in enumerate(open(f), 1):
        for m in re.finditer(r'key=["\']([^"\']+)["\']', line):
            key = m.group(1)
            keys.setdefault(key, []).append(f'{f}:{i}')
dupes = {k: v for k, v in keys.items() if len(v) > 1}
```

**1d. Hardcoded secrets check**

Grep for API tokens, passwords, or secrets that should not be in source:

```bash
grep -rn "Bearer\|api_key\|password\|secret" --include="*.py" | grep -v "token_path\|TOKEN_PATH\|secrets.get"
```

**1e. Encoding safety**

Check for subprocess calls missing `PYTHONIOENCODING=utf-8` (Windows cp1252 bug):

```python
# Any subprocess.run() call should include env={"PYTHONIOENCODING": "utf-8"}
grep -rn "subprocess.run" --include="*.py"
```

### Stage 2 -- Data Layer Testing

Test data loading functions without the Streamlit UI.

**2a. Loader smoke test**

Patch `st.cache_data` and call each loader function directly:

```python
import types
class MockCache:
    def __init__(self, *a, **kw): pass
    def __call__(self, fn): return fn
st.cache_data = MockCache
```

For each loader, verify:
- Returns a DataFrame (not None or error)
- Has expected columns
- Has expected row count (within reasonable bounds)
- Numeric columns are actually numeric (no "0.0" strings)

**2b. Redaction verification**

If the app redacts sensitive data, verify redacted columns are absent:

```python
REDACTED = {"Person Number", "Name", "Work Email", ...}
for loader_name, df in all_loaded_dataframes:
    leaked = REDACTED.intersection(set(df.columns))
    assert not leaked, f"{loader_name} leaks: {leaked}"
```

**2c. Column regression test**

For any column that was previously mismatched (e.g. "Cost Centre" appearing
in month columns due to prefix matching), add a specific assertion:

```python
assert "Cost Centre" not in month_columns, "Cost Centre regex regression"
```

### Stage 3 -- API Integration Testing

Test external API connections (Asana, GitHub, etc.).

**3a. Authentication**

Verify token files exist and are readable:

```python
token = Path("path/to/token.txt").read_text().strip()
assert len(token) > 10, "Token too short or empty"
```

**3b. API connectivity**

Make a lightweight read-only API call to verify credentials work:

```python
# Asana: fetch project metadata (read-only)
result = _get(f'/projects/{PROJECT_GID}', params={'opt_fields': 'name'})
assert 'error' not in result
```

**3c. Custom field GID validation**

For Asana integrations, verify all enum GIDs are valid options:

```python
# Fetch field options and check each configured GID exists
for field_gid, configured_values in field_config.items():
    valid_options = fetch_enum_options(field_gid)
    for val in configured_values:
        assert val in valid_options, f"GID {val} not found in field {field_gid}"
```

### Stage 4 -- Functional Testing

Test the business logic (extract builders, calculations, formatters).

**4a. Extract/report builders**

Call each builder function with real data and verify:
- Output is not empty
- Output columns match expected schema
- Aggregated totals are plausible (e.g. headcount > 0, cost > 0)
- No NaN in key columns

**4b. Financial calculations**

Verify FY boundaries, currency formatting, and rate calculations:

```python
assert fy_year(date(2026, 4, 1)) == 2026   # April = new FY
assert fy_year(date(2026, 3, 31)) == 2025  # March = old FY
assert fy_year(date(2026, 1, 15)) == 2025  # Jan-Mar rolls back
```

**4c. Filter logic**

Test that filters produce correct subsets:

```python
filtered = apply_filters(df, {"Business Area": "R&D"})
assert all(filtered["Business Area"] == "R&D")
assert len(filtered) < len(df)
```

**4d. Excel export**

Verify exported files are valid:

```python
xlsx_bytes = to_formatted_excel(df, "Test")
assert xlsx_bytes[:2] == b"PK"  # Valid ZIP/XLSX header
assert len(xlsx_bytes) > 100    # Not empty
```

### Stage 5 -- UI Smoke Test (server running)

Start the app and verify pages load.

**5a. Start server**

```bash
streamlit run app.py --server.port <PORT> &
```

**5b. Page load check**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:<PORT>/
```

Expect 200 for all pages. Check each page endpoint if accessible.

**5c. HTML injection check**

For any page using `unsafe_allow_html=True` with user-provided data,
verify that `html.escape()` is applied before rendering.

### Stage 6 -- Cross-Reference Against Known Issues

Check for patterns from previous projects that caused bugs:

| Pattern | What to check |
|---------|--------------|
| Prefix matching | Column selection uses regex, not `startswith()` |
| Enum GIDs | All Asana custom field GIDs validated against API |
| Subprocess encoding | `PYTHONIOENCODING=utf-8` in env |
| Session state | Forms use `st.session_state`, not local variables |
| Data persistence | Local file writes have GitHub sync for Cloud deploy |
| Sort order | Business-meaningful sort defined where needed |
| Date format | dd/mm/yyyy in outputs, FY April-March |
| Currency | EUR default, comma thousands, no hardcoded USD |
| Redaction | Sensitive columns dropped at loader level |
| from __future__ | All files have `from __future__ import annotations` |

## Output

Report findings in this format:

```
## QA Report: [App Name] -- [Date]

### Critical (blocks deployment)
- [issue]: [file:line] -- [description]

### High (fix before users see it)
- [issue]: [file:line] -- [description]

### Medium (fix soon)
- [issue]: [file:line] -- [description]

### Low (cosmetic / consistency)
- [issue]: [file:line] -- [description]

### Passed
- [list of checks that passed]
```

## Conventions

- UK English throughout
- No em dashes in code output
- EUR as default currency
- Date format: dd/mm/yyyy in outputs
- CSVs: read with latin-1 (HRIS), write with utf-8
- Fenergo FY: April to March (FY_START_MONTH=4)
