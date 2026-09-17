PATH = "app.py"

old = '''    if "trading_live" not in st.session_state:
        st.session_state.trading_live = False'''

new = '''    def _safe_date(s):
        try:
            return dt.datetime.fromisoformat(s).date()
        except (ValueError, TypeError):
            return None

    def _square_off_all(pp, reason="Stop-All"):
        from zoneinfo import ZoneInfo as _ZoneInfo
        _ts_stop = tick_service()
        _now_stop = dt.datetime.now(_ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        _closed_count = 0
        for _inst_name, _pos in list(pp["open"].items()):
            _tok, _exch, _lot = INSTRUMENTS.get(_inst_name, (None, None, 1))
            _qty_i = _lot * LOTS_PER_INSTRUMENT.get(_inst_name, 1)
            if _pos.get("status") != "open":
                del pp["open"][_inst_name]
                continue
            if "option_token" in _pos:
                _bid, _ask = get_bid_ask(_pos["option_exch"], _pos["option_token"])
                _exit_px = _bid if _bid is not None else _ts_stop.get_ltp(_pos["option_token"])
                if _exit_px is not None:
                    _close_position(pp, _inst_name, _pos, reason, _exit_px, _now_stop, _qty_i)
                    _closed_count += 1
                else:
                    del pp["open"][_inst_name]
            else:
                _ltp_u = _ts_stop.get_ltp(_tok) if _tok else None
                if _ltp_u is not None:
                    _bull = _pos["dir"] == "bullish"
                    _pts = round((_ltp_u - _pos["entry"]) if _bull else (_pos["entry"] - _ltp_u), 2)
                    _pnl_rs = round(_pts * _qty_i, 2)
                    _pos.update(exit=reason, exit_price=round(_ltp_u, 2), exit_time=str(_now_stop),
                                points=_pts, pnl_rs=_pnl_rs)
                    pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + _pnl_rs, 2)
                    pp["closed"].append(_pos)
                    del pp["open"][_inst_name]
                    _closed_count += 1
                else:
                    del pp["open"][_inst_name]
        save_paper(pp)
        return _closed_count

    if "trading_live" not in st.session_state:
        st.session_state.trading_live = False'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_dailyrisk2")

with open(PATH, "w") as f:
    f.write(content)

print("Patched (2/4) -- helper functions added.")
