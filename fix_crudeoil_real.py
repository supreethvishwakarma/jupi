PATH = "app.py"

# ---- patch 1: single CRUDEOIL contract instead of two ----
old1 = "    return rows[:2]"
new1 = "    return rows[:1]  # just the single nearest contract, not two confusing ones"

# ---- patch 2: add real_futures_cost() and get_bid_ask() after real_options_cost() ----
old2 = '''    gst = 0.18 * (brokerage + exch_charge + sebi_charge)  # GST on brokerage+exchange+SEBI only
    return round(brokerage + stt + exch_charge + sebi_charge + stamp_duty + gst, 2)'''

new2 = '''    gst = 0.18 * (brokerage + exch_charge + sebi_charge)  # GST on brokerage+exchange+SEBI only
    return round(brokerage + stt + exch_charge + sebi_charge + stamp_duty + gst, 2)


def real_futures_cost(entry_price, exit_price, qty):
    """Approximate round-trip AngelOne MCX futures charges: flat brokerage,
    CTT (sell side only, ~0.01% for non-agri futures like crude), exchange
    transaction charge, SEBI fee, stamp duty (buy side), GST on the taxable
    pieces. An estimate based on published rates -- MCX's own schedule is
    more granular than this; verify against your own contract note."""
    buy_value = entry_price * qty
    sell_value = exit_price * qty
    brokerage = 20 + 20
    ctt = 0.0001 * sell_value
    exch_charge = 0.000026 * (buy_value + sell_value)
    sebi_charge = 0.000001 * (buy_value + sell_value)
    stamp_duty = 0.00002 * buy_value
    gst = 0.18 * (brokerage + exch_charge + sebi_charge)
    return round(brokerage + ctt + exch_charge + sebi_charge + stamp_duty + gst, 2)


def get_bid_ask(exchange, token):
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

# ---- patch 3: MARGIN_PCT slider for MCX instruments ----
old3 = '''if EXCH == "MCX":
    st.sidebar.warning("MCX futures expire monthly. History is limited to this "
                        "contract's life, and stitching contracts creates fake "
                        "price jumps that look like real breaks.")'''

new3 = '''if EXCH == "MCX":
    st.sidebar.warning("MCX futures expire monthly. History is limited to this "
                        "contract's life, and stitching contracts creates fake "
                        "price jumps that look like real breaks.")
    MARGIN_PCT = st.sidebar.slider("Margin % of contract value (MCX)", 5.0, 100.0, 30.0, 1.0,
                                    help="Real MCX crude margin varies with volatility -- "
                                         "historically ~15-30%, has spiked to 60-100% in extreme "
                                         "moves. Check AngelOne's own margin calculator for today's "
                                         "real figure before trusting this.")
else:
    MARGIN_PCT = 30.0'''

with open(PATH) as f:
    content = f.read()

for i, (old, new) in enumerate([(old1, new1), (old2, new2), (old3, new3)], 1):
    n = content.count(old)
    if n != 1:
        print(f"WARNING patch {i}: expected 1 match, found {n}. Aborting.")
        raise SystemExit(1)
    content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_crude_real")

with open(PATH, "w") as f:
    f.write(content)

print("Patched (1/2) -- crude naming fixed, real_futures_cost/get_bid_ask/margin added.")
