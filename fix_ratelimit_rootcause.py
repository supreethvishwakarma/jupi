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

new1 = '''_bid_ask_cache = {}


def get_bid_ask(exchange, token):
    """Real best bid/ask via AngelOne's quote endpoint, throttled to at most
    once every 2 seconds per token -- this endpoint has its own strict
    (~1 req/sec) rate limit, and callers may run every second. Returns
    (bid, ask); falls back to (ltp, ltp) if depth is empty, or the last
    cached value (or None, None) if the call itself fails."""
    key = (exchange, str(token))
    cached = _bid_ask_cache.get(key)
    now_ts = time.time()
    if cached and (now_ts - cached[2]) < 2.0:
        return cached[0], cached[1]
    try:
        q = broker().getMarketData(mode="FULL", exchangeTokens={exchange: [str(token)]})
        fetched = q.get("data", {}).get("fetched", [])
        if not fetched:
            return (cached[0], cached[1]) if cached else (None, None)
        f = fetched[0]
        depth = f.get("depth", {})
        bid = depth["buy"][0]["price"] if depth.get("buy") else None
        ask = depth["sell"][0]["price"] if depth.get("sell") else None
        if not bid or not ask:
            ltp = f.get("ltp")
            bid, ask = (ltp, ltp) if ltp else (None, None)
        _bid_ask_cache[key] = (bid, ask, now_ts)
        return bid, ask
    except Exception:
        return (cached[0], cached[1]) if cached else (None, None)'''

old2 = "                    chain = find_atm_option(prefix, search_exch, weekly_1letter, round(ltp/50)*50)"
new2 = "                    chain = find_atm_option(prefix, search_exch, weekly_1letter, round(ltp/100)*100)"

with open(PATH) as f:
    content = f.read()

n1, n2 = content.count(old1), content.count(old2)
if n1 != 1 or n2 != 1:
    print(f"WARNING: expected 1 match each, found {n1} and {n2}. Aborting.")
    raise SystemExit(1)
content = content.replace(old1, new1).replace(old2, new2)

import shutil
shutil.copy(PATH, PATH + ".bak_ratelimitroot")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- get_bid_ask throttled to 1 call/2sec per token, option-chain cache widened to 100pt buckets.")
