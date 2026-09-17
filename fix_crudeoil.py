PATH = "app.py"

old1 = '''def save_paper(d):
    json.dump(d, open(PAPER_FILE, "w"), indent=1, default=str)

# ---------------------------------------------------------------- sidebar'''

new1 = '''def save_paper(d):
    json.dump(d, open(PAPER_FILE, "w"), indent=1, default=str)


@st.cache_data(ttl=3600, show_spinner="looking up current MCX CRUDEOIL contracts…")
def lookup_crude_contracts():
    """Looks up the real, currently-listed MCX CRUDEOIL futures contracts from
    AngelOne's own scrip master, instead of trusting hardcoded tokens that go
    stale every month when contracts roll over."""
    try:
        res = broker().searchScrip("MCX", "CRUDEOIL")
    except Exception:
        return []
    if not res.get("status"):
        return []
    rows = [r for r in res.get("data", [])
            if r["tradingsymbol"].startswith("CRUDEOIL")
            and r["tradingsymbol"].endswith("FUT")
            and not r["tradingsymbol"].startswith("CRUDEOILM")]

    def parse_expiry(sym):
        core = sym[len("CRUDEOIL"):-len("FUT")]  # e.g. "19SEP26"
        try:
            return dt.datetime.strptime(core, "%d%b%y")
        except ValueError:
            return dt.datetime.max

    rows.sort(key=lambda r: parse_expiry(r["tradingsymbol"]))
    return rows[:2]

# ---------------------------------------------------------------- sidebar'''

old2 = '''INSTRUMENTS = {
    "NIFTY 50": ("99926000", "NSE", 65),
    "NIFTY BANK": ("99926009", "NSE", 35),
    "FINNIFTY": ("99926037", "NSE", 65),
    "MIDCPNIFTY": ("99926074", "NSE", 120),
    "CRUDEOIL Sep26": ("565899", "MCX", 100),
    "CRUDEOIL Oct26": ("569900", "MCX", 100),
}'''

new2 = '''INSTRUMENTS = {
    "NIFTY 50": ("99926000", "NSE", 65),
    "NIFTY BANK": ("99926009", "NSE", 35),
    "FINNIFTY": ("99926037", "NSE", 65),
    "MIDCPNIFTY": ("99926074", "NSE", 120),
}
_crude = lookup_crude_contracts()
for r in _crude:
    INSTRUMENTS[r["tradingsymbol"]] = (r["symboltoken"], "MCX", 100)
if not _crude:
    st.sidebar.caption("Couldn't look up live CRUDEOIL contracts (broker call failed) -- "
                        "MCX instruments unavailable this session.")'''

with open(PATH) as f:
    content = f.read()

n1 = content.count(old1)
n2 = content.count(old2)
if n1 != 1 or n2 != 1:
    print(f"WARNING: expected 1 match each, found {n1} and {n2}. Aborting.")
    raise SystemExit(1)

content = content.replace(old1, new1).replace(old2, new2)

with open(PATH + ".bak_crude", "w") as f:
    import shutil as _sh
with open(PATH) as f:
    pass
import shutil
shutil.copy(PATH, PATH + ".bak_crude")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- CRUDEOIL contracts now looked up live from AngelOne instead of hardcoded.")
