PATH = "app.py"

old = '''        for inst_name in PAPER_INSTRUMENTS:
            if inst_name in pp["open"]:
                continue
            tok, exch, _ = INSTRUMENTS[inst_name]
            if not is_market_open(exch, now):
                continue
            time.sleep(1.5)
            try:
                chart_df = fetch((now - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
                                  now.strftime("%Y-%m-%d %H:%M"), INTERVAL, tok, exch)'''

new = '''        for inst_name in PAPER_INSTRUMENTS:
            tok, exch, _ = INSTRUMENTS[inst_name]
            if not is_market_open(exch, now):
                continue

            if inst_name in pp["open"]:
                _existing = pp["open"][inst_name]
                if STRATEGY == "Supertrend (Trailing SL)" and _existing.get("status") == "open":
                    time.sleep(1.5)
                    try:
                        _st_df = fetch((now - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
                                       now.strftime("%Y-%m-%d %H:%M"), INTERVAL, tok, exch)
                        if not _st_df.empty:
                            _new_sl = supertrend_current_value(_st_df, ST_PERIOD, ST_MULT)
                            if _new_sl is not None:
                                _bull = _existing["dir"] == "bullish"
                                _updated = max(_existing["sl"], _new_sl) if _bull else min(_existing["sl"], _new_sl)
                                if round(_updated, 2) != _existing["sl"]:
                                    _existing["sl"] = round(_updated, 2)
                                    save_paper(pp)
                                    st.caption(f"{inst_name}: trailing SL updated to {_existing['sl']}")
                    except Exception:
                        pass
                continue

            time.sleep(1.5)
            try:
                chart_df = fetch((now - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
                                  now.strftime("%Y-%m-%d %H:%M"), INTERVAL, tok, exch)'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_supertrend3")

with open(PATH, "w") as f:
    f.write(content)

print("Patched (3/3) -- live trailing SL now active for Supertrend positions.")
