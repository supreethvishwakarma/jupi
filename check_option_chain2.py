import os, re, pyotp, datetime as dt
from dotenv import load_dotenv
from SmartApi import SmartConnect

load_dotenv()
o = SmartConnect(api_key=os.environ["ANGEL_API_KEY"])
o.generateSession(os.environ["ANGEL_CLIENT_ID"], os.environ["ANGEL_PASSWORD"],
                   pyotp.TOTP(os.environ["ANGEL_TOTP"]).now())

def spot_ltp(exchange, token):
    now = dt.datetime.now()
    r = o.getCandleData(dict(exchange=exchange, symboltoken=token, interval="FIVE_MINUTE",
                              fromdate=(now - dt.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M"),
                              todate=now.strftime("%Y-%m-%d %H:%M")))
    return r["data"][-1][4] if r.get("data") else None

MONTHS3 = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
MONTH1 = {m[0] if m[0] not in "JJ" else m: m for m in MONTHS3}  # not used, placeholder

def parse_expiry_3letter(code):
    # e.g. "06OCT26" -> datetime
    return dt.datetime.strptime(code, "%d%b%y")

def check_index(name, prefix, search_exch, spot_exch, spot_token, weekly_1letter=False):
    print(f"\n{'='*60}\n{name}  (search exch={search_exch}, spot exch={spot_exch})")
    ltp = spot_ltp(spot_exch, spot_token)
    print(f"Spot LTP: {ltp}")

    res = o.searchScrip(search_exch, prefix)
    rows = res.get("data", []) if res.get("status") else []
    opts = [x for x in rows if x["tradingsymbol"].startswith(prefix)
            and (x["tradingsymbol"].endswith("CE") or x["tradingsymbol"].endswith("PE"))]
    if prefix == "NIFTY":
        opts = [x for x in opts if not x["tradingsymbol"].startswith("NIFTYNXT")]
    print(f"Total {prefix} option contracts found: {len(opts)}")
    print("First 10 raw symbols:")
    for x in opts[:10]:
        print(" ", x["tradingsymbol"], x["symboltoken"])

    if not ltp:
        print("No spot LTP -- can't determine ATM.")
        return

    parsed = []
    if weekly_1letter:
        # weekly: PREFIX + YY + [single-letter month] + DD + strike + CE/PE
        # monthly: PREFIX + YY + [3-letter month] + strike + CE/PE
        re_weekly = re.compile(rf"^{prefix}(\d{{2}})([A-Z])(\d{{2}})(\d+)(CE|PE)$")
        re_monthly = re.compile(rf"^{prefix}(\d{{2}})([A-Z]{{3}})(\d+)(CE|PE)$")
        for x in opts:
            mw = re_weekly.match(x["tradingsymbol"])
            mm = re_monthly.match(x["tradingsymbol"])
            if mw:
                yy, mon1, dd, strike, typ = mw.groups()
                parsed.append((f"{yy}{mon1}{dd}", int(strike), typ, x, "weekly"))
            elif mm:
                yy, mon3, strike, typ = mm.groups()
                parsed.append((f"{yy}{mon3}", int(strike), typ, x, "monthly"))
    else:
        re_std = re.compile(rf"^{prefix}(\d{{2}}[A-Z]{{3}}\d{{2}})(\d+)(CE|PE)$")
        for x in opts:
            m = re_std.match(x["tradingsymbol"])
            if m:
                code, strike, typ = m.groups()
                parsed.append((code, int(strike), typ, x, "std"))

    print(f"Parsed {len(parsed)} of {len(opts)} using the regex.")
    if not parsed:
        print("Couldn't parse any -- format differs from what we assumed, need to inspect raw symbols above.")
        return

    codes = sorted(set(p[0] for p in parsed))
    print(f"Distinct expiry codes seen (raw, unsorted-by-date): {codes[:10]}{'...' if len(codes) > 10 else ''}")

    same = [p for p in parsed if p[0] == codes[0]]
    atm = min(same, key=lambda p: abs(p[1] - ltp))
    strike = atm[1]
    ce = next((p[3] for p in same if p[1] == strike and p[2] == "CE"), None)
    pe = next((p[3] for p in same if p[1] == strike and p[2] == "PE"), None)
    print(f"Using first expiry code '{codes[0]}' as a guess -- ATM strike ~{strike}")
    print(f"  CE: {ce['tradingsymbol'] if ce else 'not found'} token={ce['symboltoken'] if ce else None}")
    print(f"  PE: {pe['tradingsymbol'] if pe else 'not found'} token={pe['symboltoken'] if pe else None}")

    tokens = [t["symboltoken"] for t in (ce, pe) if t]
    if tokens:
        try:
            q = o.getMarketData(mode="FULL", exchangeTokens={search_exch: tokens})
            print("getMarketData result:", q)
        except Exception as e:
            print("getMarketData FAILED:", repr(e))

check_index("NIFTY", "NIFTY", "NFO", "NSE", "99926000", weekly_1letter=False)
check_index("BANKNIFTY", "BANKNIFTY", "NFO", "NSE", "99926009", weekly_1letter=False)
check_index("SENSEX", "SENSEX", "BFO", "BSE", "99919000", weekly_1letter=True)
