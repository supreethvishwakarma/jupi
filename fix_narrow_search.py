PATH = "app.py"

old = '''    if not parsed:
        return None
    today = dt.datetime.now()
    codes = sorted(set(p[0] for p in parsed), key=_parse_expiry_code)
    upcoming = [c for c in codes if _parse_expiry_code(c) >= today - dt.timedelta(days=1)]
    if not upcoming:
        return None
    nearest = upcoming[0]
    same = [p for p in parsed if p[0] == nearest]
    atm = min(same, key=lambda p: abs(p[1] - spot_ltp_rounded))
    strike = atm[1]
    ce = next((p[3] for p in same if p[1] == strike and p[2] == "CE"), None)
    pe = next((p[3] for p in same if p[1] == strike and p[2] == "PE"), None)
    if not ce or not pe:
        return None'''

new = '''    if not parsed:
        return None
    today = dt.datetime.now()
    codes = sorted(set(p[0] for p in parsed), key=_parse_expiry_code)
    upcoming = [c for c in codes if _parse_expiry_code(c) >= today - dt.timedelta(days=1)]
    if not upcoming:
        return None
    nearest = upcoming[0]
    same = [p for p in parsed if p[0] == nearest]

    # the broad prefix-only search can be truncated for large chains (e.g. BANKNIFTY
    # spans years of expiries) and silently miss some strikes -- re-search narrowly
    # using the exact expiry, which reliably returns the complete strike chain
    try:
        narrow_res = broker().searchScrip(search_exch, prefix + nearest)
        if narrow_res.get("status"):
            narrow_rows = narrow_res.get("data", [])
            narrow_opts = [x for x in narrow_rows if x["tradingsymbol"].startswith(prefix + nearest)
                           and (x["tradingsymbol"].endswith("CE") or x["tradingsymbol"].endswith("PE"))]
            if narrow_opts:
                strike_re = _re.compile(rf"^{prefix}{_re.escape(nearest)}(\\d+)(CE|PE)$")
                narrow_parsed = []
                for x in narrow_opts:
                    m = strike_re.match(x["tradingsymbol"])
                    if m:
                        narrow_parsed.append((int(m.group(1)), m.group(2), x))
                if narrow_parsed:
                    same = [(nearest, s, t, x) for s, t, x in narrow_parsed]
    except Exception:
        pass  # fall back to whatever the broad search already found

    atm = min(same, key=lambda p: abs(p[1] - spot_ltp_rounded))
    strike = atm[1]
    ce = next((p[3] for p in same if p[1] == strike and p[2] == "CE"), None)
    pe = next((p[3] for p in same if p[1] == strike and p[2] == "PE"), None)
    if not ce or not pe:
        return None'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_narrowsearch")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- option chain lookup now does a second, narrow search on the exact expiry to avoid truncation.")
