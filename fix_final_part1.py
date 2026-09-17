PATH = "app.py"

with open(PATH) as f:
    content = f.read()

if "MARKET_HOURS = {" in content:
    print("Market hours functions already present -- skipping part 1.")
else:
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

    n = content.count(old1)
    if n != 1:
        print(f"WARNING: expected 1 match, found {n}. Could not add market hours functions.")
        raise SystemExit(1)
    content = content.replace(old1, new1)

    import shutil
    shutil.copy(PATH, PATH + ".bak_finalpart1")

    with open(PATH, "w") as f:
        f.write(content)

    print("Part 1 done -- market hours functions added.")
