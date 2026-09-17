PATH = "app.py"

old1 = '''def get_bid_ask(exchange, token):
    """Real best bid/ask via AngelOne's quote endpoint. Returns (bid, ask);
    falls back to (ltp, ltp) if depth is empty (e.g. market closed), or
    (None, None) on failure. Only called at actual fill moments, not every
    tick, to stay well clear of this endpoint's own rate limit."""
    try:
        q = broker().getMarketData(mode="FULL", exchangeTokens={exchange: [str(token)]})
        fetched = q.get("data", {}).get("fetched", [])
        if not fetched:
            return None, None
        f = fetched[0]
        depth = f.get("depth", {})
        bid = depth["buy"][0]["price"] if depth.get("buy") else None
        ask = depth["sell"][0]["price"] if depth.get("sell") else None
        if not bid or not ask:
            ltp = f.get("ltp")
            return (ltp, ltp) if ltp else (None, None)
        return bid, ask
    except Exception:
        return None, None'''

new1 = '''def get_bid_ask(exchange, token):
    """Real best bid/ask via AngelOne's quote endpoint. Returns (bid, ask);
    falls back to (ltp, ltp) if depth is empty (e.g. market closed), or
    (None, None) on failure. Only called at actual fill moments, not every
    tick, to stay well clear of this endpoint's own rate limit."""
    try:
        q = broker().getMarketData(mode="FULL", exchangeTokens={exchange: [str(token)]})
        fetched = q.get("data", {}).get("fetched", [])
        if not fetched:
            return None, None
        f = fetched[0]
        depth = f.get("depth", {})
        bid = depth["buy"][0]["price"] if depth.get("buy") else None
        ask = depth["sell"][0]["price"] if depth.get("sell") else None
        if not bid or not ask:
            ltp = f.get("ltp")
            return (ltp, ltp) if ltp else (None, None)
        return bid, ask
    except Exception:
        return None, None


_MONTH_LETTER = {"J": 1, "F": 2, "M": 3, "A": 4, "Y": 5, "U": 6, "L": 7,
                  "G": 8, "S": 9, "O": 10, "N": 11, "D": 12}


def _parse_expiry_code(code):
    """Parses either a weekly single-letter-month code (e.g. '26O01') or a
    3-letter-month code (weekly-with-day 'DDMonYY' or monthly-only 'YYMon')
    into a real datetime for correct chronological sorting."""
    import re as _re
    m = _re.match(r"^(\\d{2})([A-Z])(\\d{2})$", code)
    if m:
        yy, letter, dd = m.groups()
        mon = _MONTH_LETTER.get(letter)
        if mon:
            try:
                return dt.datetime(2000 + int(yy), mon, int(dd))
            except ValueError:
                pass
    m = _re.match(r"^(\\d{2})([A-Z]{3})$", code)
    if m:
        yy, mon3 = m.groups()
        try:
            return dt.datetime.strptime(f"01{mon3}{yy}", "%d%b%y").replace(day=28)
        except ValueError:
            pass
    try:
        return dt.datetime.strptime(code, "%d%b%y")
    except ValueError:
        pass
    return dt.datetime.max


@st.cache_data(ttl=300, show_spinner="looking up the option chain…")
def find_atm_option(prefix, search_exch, weekly_1letter, spot_ltp_rounded):
    """Looks up the real, currently-listed option chain for `prefix` on
    `search_exch` and returns the ATM CE/PE contracts for the nearest
    upcoming expiry, or None if unavailable. Cached for 5 minutes and keyed
    on a rounded spot price so it doesn't re-search on every tiny tick."""
    import re as _re
    try:
        res = broker().searchScrip(search_exch, prefix)
    except Exception:
        return None
    if not res.get("status"):
        return None
    rows = res.get("data", [])
    opts = [x for x in rows if x["tradingsymbol"].startswith(prefix)
            and (x["tradingsymbol"].endswith("CE") or x["tradingsymbol"].endswith("PE"))]
    if prefix == "NIFTY":
        opts = [x for x in opts if not x["tradingsymbol"].startswith("NIFTYNXT")]

    parsed = []
    if weekly_1letter:
        re_weekly = _re.compile(rf"^{prefix}(\\d{{2}})([A-Z])(\\d{{2}})(\\d+)(CE|PE)$")
        re_monthly = _re.compile(rf"^{prefix}(\\d{{2}})([A-Z]{{3}})(\\d+)(CE|PE)$")
        for x in opts:
            mw = re_weekly.match(x["tradingsymbol"])
            mm = re_monthly.match(x["tradingsymbol"])
            if mw:
                yy, mon1, dd, strike, typ = mw.groups()
                parsed.append((f"{yy}{mon1}{dd}", int(strike), typ, x))
            elif mm:
                yy, mon3, strike, typ = mm.groups()
                parsed.append((f"{yy}{mon3}", int(strike), typ, x))
    else:
        re_std = _re.compile(rf"^{prefix}(\\d{{2}}[A-Z]{{3}}\\d{{2}})(\\d+)(CE|PE)$")
        for x in opts:
            m = re_std.match(x["tradingsymbol"])
            if m:
                code, strike, typ = m.groups()
                parsed.append((code, int(strike), typ, x))

    if not parsed:
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
        return None
    return dict(ce_token=ce["symboltoken"], ce_symbol=ce["tradingsymbol"],
                pe_token=pe["symboltoken"], pe_symbol=pe["tradingsymbol"],
                expiry=nearest, strike=strike, exch=search_exch)


def get_option_config(inst_name):
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

with open(PATH) as f:
    content = f.read()

n = content.count(old1)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old1, new1)

import shutil
shutil.copy(PATH, PATH + ".bak_unified1")

with open(PATH, "w") as f:
    f.write(content)

print("Patched (1/4) -- option-chain lookup functions added.")
