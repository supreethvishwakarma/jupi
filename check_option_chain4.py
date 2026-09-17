import os, re, time, logging, pyotp, datetime as dt
from dotenv import load_dotenv
from SmartApi import SmartConnect

logging.disable(logging.CRITICAL)
for name in list(logging.root.manager.loggerDict):
    logging.getLogger(name).disabled = True

load_dotenv()
o = SmartConnect(api_key=os.environ["ANGEL_API_KEY"])
o.generateSession(os.environ["ANGEL_CLIENT_ID"], os.environ["ANGEL_PASSWORD"],
                   pyotp.TOTP(os.environ["ANGEL_TOTP"]).now())

MONTH_LETTER = {"J": 1, "F": 2, "M": 3, "A": 4, "Y": 5, "U": 6, "L": 7,
                "G": 8, "S": 9, "O": 10, "N": 11, "D": 12}  # best-effort for weekly single-letter codes

def parse_expiry(code):
    """Returns a real datetime for any of the expiry code shapes we might see,
    or datetime.max if it can't be parsed (so unparseable/far-future codes sort last,
    never picked as 'nearest')."""
    m = re.match(r"^(\d{2})([A-Z])(\d{2})$", code)  # weekly: YY + letter-month + DD
    if m:
        yy, letter, dd = m.groups()
        mon = MONTH_LETTER.get(letter)
        if mon:
            try:
                return dt.datetime(2000 + int(yy), mon, int(dd))
            except ValueError:
                pass
    m = re.match(r"^(\d{2})([A-Z]{3})$", code)  # monthly: YY + 3-letter month, no day
    if m:
        yy, mon3 = m.groups()
        try:
            d = dt.datetime.strptime(f"01{mon3}{yy}", "%d%b%y")
            return d.replace(day=28)  # push to end of month so it sorts after same-month weeklies
        except ValueError:
            pass
    try:
        return dt.datetime.strptime(code, "%d%b%y")  # standard: DD + 3-letter month + YY
    except ValueError:
        pass
    return dt.datetime.max

def spot_ltp(exchange, token):
    now = dt.datetime.now()
    r = o.getCandleData(dict(exchange=exchange, symboltoken=token, interval="FIVE_MINUTE",
                              fromdate=(now - dt.timedelta(days=4)).strftime("%Y-%m-%d %H:%M"),
                              todate=now.strftime("%Y-%m-%d %H:%M")))
    return r["data"][-1][4] if r.get("data") else None

def check_index(name, prefix, search_exch, spot_exch, spot_token, weekly_1letter=False):
    print(f"\n{'='*60}\n{name}  (search exch={search_exch}, spot exch={spot_exch})")
    try:
        ltp = spot_ltp(spot_exch, spot_token)
        print(f"Spot LTP: {ltp}")
    except Exception as e:
        print(f"Spot LTP fetch FAILED: {e}")
        ltp = None
    time.sleep(4)

    try:
        res = o.searchScrip(search_exch, prefix)
    except Exception as e:
        print(f"searchScrip FAILED: {e}")
        return
    time.sleep(4)

    rows = res.get("data", []) if res.get("status") else []
    opts = [x for x in rows if x["tradingsymbol"].startswith(prefix)
            and (x["tradingsymbol"].endswith("CE") or x["tradingsymbol"].endswith("PE"))]
    if prefix == "NIFTY":
        opts = [x for x in opts if not x["tradingsymbol"].startswith("NIFTYNXT")]
    print(f"Total {prefix} option contracts found: {len(opts)}")

    if not ltp or not opts:
        print("Missing LTP or contracts -- stopping here for this index.")
        return

    parsed = []
    if weekly_1letter:
        re_weekly = re.compile(rf"^{prefix}(\d{{2}})([A-Z])(\d{{2}})(\d+)(CE|PE)$")
        re_monthly = re.compile(rf"^{prefix}(\d{{2}})([A-Z]{{3}})(\d+)(CE|PE)$")
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
        re_std = re.compile(rf"^{prefix}(\d{{2}}[A-Z]{{3}}\d{{2}})(\d+)(CE|PE)$")
        for x in opts:
            m = re_std.match(x["tradingsymbol"])
            if m:
                code, strike, typ = m.groups()
                parsed.append((code, int(strike), typ, x))

    print(f"Parsed {len(parsed)} of {len(opts)}.")
    if not parsed:
        return

    today = dt.datetime.now()
    codes = sorted(set(p[0] for p in parsed), key=parse_expiry)
    # only consider expiries that are actually still upcoming (today or later)
    upcoming = [c for c in codes if parse_expiry(c) >= today - dt.timedelta(days=1)]
    print(f"All codes, date-sorted: {codes[:6]}...")
    print(f"Nearest upcoming: {upcoming[0] if upcoming else 'NONE FOUND'} "
          f"(parses to {parse_expiry(upcoming[0]).date() if upcoming else '-'})")

    if not upcoming:
        return
    nearest = upcoming[0]
    same = [p for p in parsed if p[0] == nearest]
    atm = min(same, key=lambda p: abs(p[1] - ltp))
    strike = atm[1]
    ce = next((p[3] for p in same if p[1] == strike and p[2] == "CE"), None)
    pe = next((p[3] for p in same if p[1] == strike and p[2] == "PE"), None)
    print(f"ATM strike ~{strike}")
    print(f"  CE: {ce['tradingsymbol'] if ce else 'not found'} token={ce['symboltoken'] if ce else None}")
    print(f"  PE: {pe['tradingsymbol'] if pe else 'not found'} token={pe['symboltoken'] if pe else None}")

    tokens = [t["symboltoken"] for t in (ce, pe) if t]
    if tokens:
        time.sleep(4)
        try:
            q = o.getMarketData(mode="FULL", exchangeTokens={search_exch: tokens})
            for f in q.get("data", {}).get("fetched", []):
                buy = f["depth"]["buy"][0]["price"] if f["depth"]["buy"] else None
                sell = f["depth"]["sell"][0]["price"] if f["depth"]["sell"] else None
                print(f"  {f['tradingSymbol']}: LTP={f['ltp']} bid={buy} ask={sell} volume={f['tradeVolume']}")
        except Exception as e:
            print("getMarketData FAILED:", repr(e))

check_index("NIFTY", "NIFTY", "NFO", "NSE", "99926000", weekly_1letter=False)
time.sleep(6)
check_index("BANKNIFTY", "BANKNIFTY", "NFO", "NSE", "99926009", weekly_1letter=False)
time.sleep(6)
check_index("SENSEX", "SENSEX", "BFO", "BSE", "99919000", weekly_1letter=True)

print("\nDone.")
