import os, re, pyotp, datetime as dt
from dotenv import load_dotenv
from SmartApi import SmartConnect

load_dotenv()
o = SmartConnect(api_key=os.environ["ANGEL_API_KEY"])
o.generateSession(os.environ["ANGEL_CLIENT_ID"], os.environ["ANGEL_PASSWORD"],
                   pyotp.TOTP(os.environ["ANGEL_TOTP"]).now())

now = dt.datetime.now()
r = o.getCandleData(dict(exchange="NSE", symboltoken="99926000", interval="FIVE_MINUTE",
                          fromdate=(now - dt.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M"),
                          todate=now.strftime("%Y-%m-%d %H:%M")))
ltp = r["data"][-1][4] if r.get("data") else None
print(f"NIFTY LTP (from last candle close): {ltp}")

res = o.searchScrip("NFO", "NIFTY")
rows = res.get("data", []) if res.get("status") else []
opts = [x for x in rows if x["tradingsymbol"].startswith("NIFTY")
        and (x["tradingsymbol"].endswith("CE") or x["tradingsymbol"].endswith("PE"))
        and not x["tradingsymbol"].startswith("NIFTYNXT")]
print(f"\nTotal NIFTY option contracts found: {len(opts)}")
print("First 15 raw symbols (to see the real naming pattern):")
for x in opts[:15]:
    print(" ", x["tradingsymbol"], x["symboltoken"])

if ltp:
    strike_re = re.compile(r"NIFTY(\d{2}[A-Z]{3}\d{2})(\d+)(CE|PE)$")
    parsed = []
    for x in opts:
        m = strike_re.match(x["tradingsymbol"])
        if m:
            parsed.append((m.group(1), int(m.group(2)), m.group(3), x))
    if parsed:
        expiries = sorted(set(p[0] for p in parsed),
                           key=lambda s: dt.datetime.strptime(s, "%d%b%y"))
        nearest_expiry = expiries[0]
        print(f"\nParsed {len(parsed)} contracts. Nearest expiry found: {nearest_expiry}")
        same_expiry = [p for p in parsed if p[0] == nearest_expiry]
        atm = min(same_expiry, key=lambda p: abs(p[1] - ltp))
        atm_strike = atm[1]
        ce = next((p[3] for p in same_expiry if p[1] == atm_strike and p[2] == "CE"), None)
        pe = next((p[3] for p in same_expiry if p[1] == atm_strike and p[2] == "PE"), None)
        print(f"ATM strike: {atm_strike}")
        print(f"  CE: {ce['tradingsymbol'] if ce else 'not found'} token={ce['symboltoken'] if ce else None}")
        print(f"  PE: {pe['tradingsymbol'] if pe else 'not found'} token={pe['symboltoken'] if pe else None}")

        tokens = [t["symboltoken"] for t in (ce, pe) if t]
        if tokens:
            print("\nFetching live quote (FULL mode) for ATM CE/PE...")
            try:
                q = o.getMarketData(mode="FULL", exchangeTokens={"NFO": tokens})
                print(q)
            except Exception as e:
                print("getMarketData FAILED:", repr(e))
    else:
        print("\nCouldn't parse any symbols with the weekly regex -- printing raw list above "
              "so we can see the actual format and fix the parser.")
