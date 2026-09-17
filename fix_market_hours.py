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
    }.get(inst_name)


MARKET_HOURS = {
    "NSE": (dt.time(9, 15), dt.time(15, 30)),
    "BSE": (dt.time(9, 15), dt.time(15, 30)),
    "NFO": (dt.time(9, 15), dt.time(15, 30)),
    "BFO": (dt.time(9, 15), dt.time(15, 30)),
    "MCX": (dt.time(9, 15), dt.time(22, 55)),
}


def is_market_open(exch, now):
    open_t, close_t = MARKET_HOURS.get(exch, (dt.time(9, 15), dt.time(15, 30)))
    return open_t <= now.time() <= close_t


def _market_hours_str(exch):
    open_t, close_t = MARKET_HOURS.get(exch, (dt.time(9, 15), dt.time(15, 30)))
    return f"{open_t.strftime('%I:%M %p')}\\u2013{close_t.strftime('%I:%M %p')}"'''

old2 = '''            if pos is None:
                feed = "\\U0001F7E2" if ltp is not None else "\\U0001F7E1"
                st.caption(f"{feed} No open position — watching for a fresh signal… "
                           f"Underlying LTP {ltp if ltp is not None else '—'}")
                continue'''

new2 = '''            if pos is None:
                if not is_market_open(exch, now):
                    st.caption(f"\\U0001F512 Market closed for {inst_name} "
                               f"({_market_hours_str(exch)}) -- not scanning.")
                else:
                    feed = "\\U0001F7E2" if ltp is not None else "\\U0001F7E1"
                    st.caption(f"{feed} No open position — watching for a fresh signal… "
                               f"Underlying LTP {ltp if ltp is not None else '—'}")
                continue'''

old3 = '''        for inst_name in PAPER_INSTRUMENTS:
            if inst_name in pp["open"]:
                continue
            tok, exch, _ = INSTRUMENTS[inst_name]
            time.sleep(1.5)  # spread out per-instrument REST calls, avoid bursting the rate limit
            try:'''

new3 = '''        for inst_name in PAPER_INSTRUMENTS:
            if inst_name in pp["open"]:
                continue
            tok, exch, _ = INSTRUMENTS[inst_name]
            if not is_market_open(exch, now):
                continue
            time.sleep(1.5)  # spread out per-instrument REST calls, avoid bursting the rate limit
            try:'''

with open(PATH) as f:
    content = f.read()

results = []
for i, (old, new) in enumerate([(old1, new1), (old2, new2), (old3, new3)], 1):
    n = content.count(old)
    results.append(n)
    if n != 1:
        print(f"WARNING patch {i}: expected 1 match, found {n}. Aborting.")
        raise SystemExit(1)
    content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_markethours")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- market hours added: NSE/BSE/NFO/BFO 9:15AM-3:30PM, MCX 9:15AM-10:55PM.")
