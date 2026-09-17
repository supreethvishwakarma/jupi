PATH = "app.py"

old1 = '''def get_option_config(inst_name):
    """Maps an instrument name to (search_prefix, search_exchange, weekly_1letter)
    for its option chain. Handles CRUDEOIL's dynamically-named contract via prefix match."""
    if inst_name.startswith("CRUDEOIL"):
        return ("CRUDEOIL", "MCX", False)
    return {
        "NIFTY 50": ("NIFTY", "NFO", False),
        "NIFTY BANK": ("BANKNIFTY", "NFO", False),
        "FINNIFTY": ("FINNIFTY", "NFO", False),
        "MIDCPNIFTY": ("MIDCPNIFTY", "NFO", False),
        "SENSEX": ("SENSEX", "BFO", True),
    }.get(inst_name)'''

new1 = '''def get_option_config(inst_name):
    """Maps an instrument name to (search_prefix, search_exchange, weekly_1letter,
    min_runway_days) for its option chain. Handles CRUDEOIL's dynamically-named
    contract via prefix match. min_runway_days requires the picked expiry be at
    least that many days out -- 0 for index options (trading the nearest weekly,
    even on expiry day, is normal and often the most liquid choice), but a real
    safety margin for CRUDEOIL, whose options liquidity near expiry is unverified."""
    if inst_name.startswith("CRUDEOIL"):
        return ("CRUDEOIL", "MCX", False, 5)
    return {
        "NIFTY 50": ("NIFTY", "NFO", False, 0),
        "NIFTY BANK": ("BANKNIFTY", "NFO", False, 0),
        "FINNIFTY": ("FINNIFTY", "NFO", False, 0),
        "MIDCPNIFTY": ("MIDCPNIFTY", "NFO", False, 0),
        "SENSEX": ("SENSEX", "BFO", True, 0),
    }.get(inst_name)'''

old2 = '''@st.cache_data(ttl=300, show_spinner="looking up the option chain…")
def find_atm_option(prefix, search_exch, weekly_1letter, spot_ltp_rounded):'''

new2 = '''@st.cache_data(ttl=300, show_spinner="looking up the option chain…")
def find_atm_option(prefix, search_exch, weekly_1letter, spot_ltp_rounded, min_runway_days=0):'''

old3 = '''    today = dt.datetime.now()
    codes = sorted(set(p[0] for p in parsed), key=_parse_expiry_code)
    upcoming = [c for c in codes if _parse_expiry_code(c) >= today - dt.timedelta(days=1)]
    if not upcoming:
        return None
    nearest = upcoming[0]'''

new3 = '''    today = dt.datetime.now()
    codes = sorted(set(p[0] for p in parsed), key=_parse_expiry_code)
    upcoming = [c for c in codes if _parse_expiry_code(c) >= today + dt.timedelta(days=min_runway_days)]
    if not upcoming:
        upcoming = [c for c in codes if _parse_expiry_code(c) >= today - dt.timedelta(days=1)]  # fallback: nearest anyway
    if not upcoming:
        return None
    nearest = upcoming[0]'''

old4 = '''                opt_cfg = get_option_config(inst_name)
                if opt_cfg is not None:
                    prefix, search_exch, weekly_1letter = opt_cfg
                    chain = find_atm_option(prefix, search_exch, weekly_1letter, round(entry_close/100)*100)'''

new4 = '''                opt_cfg = get_option_config(inst_name)
                if opt_cfg is not None:
                    prefix, search_exch, weekly_1letter, min_runway = opt_cfg
                    chain = find_atm_option(prefix, search_exch, weekly_1letter,
                                             round(entry_close/100)*100, min_runway)'''

with open(PATH) as f:
    content = f.read()

results = []
for i, (old, new) in enumerate([(old1, new1), (old2, new2), (old3, new3), (old4, new4)], 1):
    n = content.count(old)
    results.append(n)
    if n != 1:
        print(f"WARNING patch {i}: expected 1 match, found {n}. Aborting.")
        raise SystemExit(1)
    content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_crudeoptrunway")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- CRUDEOIL options now require 5+ days runway; NIFTY/BANKNIFTY/SENSEX unchanged.")
