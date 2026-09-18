PATH = "app.py"

old = '''            if "ce_token" in _pos:
                _ce_bid, _ce_ask = get_bid_ask(_pos["ce_exch"], _pos["ce_token"])
                _pe_bid, _pe_ask = get_bid_ask(_pos["pe_exch"], _pos["pe_token"])
                _ce_exit = _ce_bid if _ce_bid is not None else _ts_stop.get_ltp(_pos["ce_token"])
                _pe_exit = _pe_bid if _pe_bid is not None else _ts_stop.get_ltp(_pos["pe_token"])
                if _ce_exit is not None and _pe_exit is not None:
                    _close_straddle(pp, _inst_name, _pos, reason, _ce_exit, _pe_exit, _now_stop, _qty_i)
                    _closed_count += 1
                else:
                    del pp["open"][_inst_name]
            elif "option_token" in _pos:'''

new = '''            if _pos.get("mode") == "short_straddle" and "ce_token" in _pos:
                _ce_bid, _ce_ask = get_bid_ask(_pos["ce_exch"], _pos["ce_token"])
                _pe_bid, _pe_ask = get_bid_ask(_pos["pe_exch"], _pos["pe_token"])
                _ce_buyback = _ce_ask if _ce_ask is not None else _ts_stop.get_ltp(_pos["ce_token"])
                _pe_buyback = _pe_ask if _pe_ask is not None else _ts_stop.get_ltp(_pos["pe_token"])
                if _ce_buyback is not None and _pe_buyback is not None:
                    _close_short_straddle(pp, _inst_name, _pos, reason, _ce_buyback, _pe_buyback, _now_stop, _qty_i)
                    _closed_count += 1
                else:
                    del pp["open"][_inst_name]
            elif "ce_token" in _pos:
                _ce_bid, _ce_ask = get_bid_ask(_pos["ce_exch"], _pos["ce_token"])
                _pe_bid, _pe_ask = get_bid_ask(_pos["pe_exch"], _pos["pe_token"])
                _ce_exit = _ce_bid if _ce_bid is not None else _ts_stop.get_ltp(_pos["ce_token"])
                _pe_exit = _pe_bid if _pe_bid is not None else _ts_stop.get_ltp(_pos["pe_token"])
                if _ce_exit is not None and _pe_exit is not None:
                    _close_straddle(pp, _inst_name, _pos, reason, _ce_exit, _pe_exit, _now_stop, _qty_i)
                    _closed_count += 1
                else:
                    del pp["open"][_inst_name]
            elif "option_token" in _pos:'''

with open(PATH, encoding="utf-8") as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_sqoffshort")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched -- Stop-All now correctly buys back short straddles instead of misreading them as buying straddles.")
