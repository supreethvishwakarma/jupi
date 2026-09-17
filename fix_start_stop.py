PATH = "app.py"

old = '''    top = st.columns([1, 1, 1, 1])
    live_on = top[0].toggle("Live", value=True, help="Turn off to pause both loops")
    REFRESH_SECONDS = top[1].number_input("Signal scan (sec)", 30, 600, 60, 15,
                                           help="How often to check for NEW signals via REST candles. Keep at 60+.")
    STARTING_CAPITAL = top[2].number_input("Paper capital (Rs)", 10000, 10000000, 100000, 5000,
                                            help="Virtual starting balance. Only applied after Reset.")
    if top[3].button("Reset paper account"):
        save_paper({"open": {}, "closed": [], "ignored": [], "balance": STARTING_CAPITAL})
        st.rerun()

    def _pnl_color(val):
        try:
            v = float(val)
        except (TypeError, ValueError):
            return ""
        if v > 0:
            return "color: #16a34a; font-weight: 600;"
        if v < 0:
            return "color: #dc2626; font-weight: 600;"
        return ""

    def _close_position(pp, inst_name, pos, trigger, exit_premium, now, qty_i):
        entry_premium = pos["entry"]
        opt_pts = round(exit_premium - entry_premium, 2)
        cost = real_options_cost(entry_premium, exit_premium, qty_i)
        proceeds = round(exit_premium * qty_i - cost, 2)
        pnl_rs = round(proceeds - pos.get("capital_blocked", 0), 2)
        pos.update(exit=trigger, exit_price=round(exit_premium, 2), exit_time=str(now),
                   points=opt_pts, real_cost=cost, proceeds=proceeds, pnl_rs=pnl_rs)
        pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + proceeds, 2)
        pp["closed"].append(pos)
        del pp["open"][inst_name]
        save_paper(pp)
        st.success(f"{inst_name}: closed {pos.get('option_symbol', '')} — {trigger} "
                   f"@ Rs {round(exit_premium, 2)} · P&L Rs {pnl_rs:+,.0f}")'''

new = '''    def _pnl_color(val):
        try:
            v = float(val)
        except (TypeError, ValueError):
            return ""
        if v > 0:
            return "color: #16a34a; font-weight: 600;"
        if v < 0:
            return "color: #dc2626; font-weight: 600;"
        return ""

    def _close_position(pp, inst_name, pos, trigger, exit_premium, now, qty_i):
        entry_premium = pos["entry"]
        opt_pts = round(exit_premium - entry_premium, 2)
        cost = real_options_cost(entry_premium, exit_premium, qty_i)
        proceeds = round(exit_premium * qty_i - cost, 2)
        pnl_rs = round(proceeds - pos.get("capital_blocked", 0), 2)
        pos.update(exit=trigger, exit_price=round(exit_premium, 2), exit_time=str(now),
                   points=opt_pts, real_cost=cost, proceeds=proceeds, pnl_rs=pnl_rs)
        pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + proceeds, 2)
        pp["closed"].append(pos)
        del pp["open"][inst_name]
        save_paper(pp)
        st.success(f"{inst_name}: closed {pos.get('option_symbol', '')} — {trigger} "
                   f"@ Rs {round(exit_premium, 2)} · P&L Rs {pnl_rs:+,.0f}")

    if "trading_live" not in st.session_state:
        st.session_state.trading_live = True

    top = st.columns([1, 1, 1, 1, 1])
    start_clicked = top[0].button("\\u25b6 Start Trading", type="primary",
                                   disabled=st.session_state.trading_live, use_container_width=True)
    stop_clicked = top[1].button("\\u23f9 Stop & Square Off All",
                                  disabled=not st.session_state.trading_live, use_container_width=True)
    REFRESH_SECONDS = top[2].number_input("Signal scan (sec)", 30, 600, 60, 15,
                                           help="How often to check for NEW signals via REST candles. Keep at 60+.")
    STARTING_CAPITAL = top[3].number_input("Paper capital (Rs)", 10000, 10000000, 100000, 5000,
                                            help="Virtual starting balance. Only applied after Reset.")
    reset_clicked = top[4].button("Reset paper account")

    if start_clicked:
        st.session_state.trading_live = True
        st.rerun()

    if stop_clicked:
        from zoneinfo import ZoneInfo as _ZoneInfo
        _pp = load_paper()
        _ts_stop = tick_service()
        _now_stop = dt.datetime.now(_ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        _closed_count = 0
        for _inst_name, _pos in list(_pp["open"].items()):
            _tok, _exch, _lot = INSTRUMENTS.get(_inst_name, (None, None, 1))
            _qty_i = _lot * LOTS
            if _pos.get("status") != "open":
                del _pp["open"][_inst_name]
                continue
            if "option_token" in _pos:
                _bid, _ask = get_bid_ask(_pos["option_exch"], _pos["option_token"])
                _exit_px = _bid if _bid is not None else _ts_stop.get_ltp(_pos["option_token"])
                if _exit_px is not None:
                    _close_position(_pp, _inst_name, _pos, "Stop-All", _exit_px, _now_stop, _qty_i)
                    _closed_count += 1
                else:
                    del _pp["open"][_inst_name]
            else:
                _ltp_u = _ts_stop.get_ltp(_tok) if _tok else None
                if _ltp_u is not None:
                    _bull = _pos["dir"] == "bullish"
                    _pts = round((_ltp_u - _pos["entry"]) if _bull else (_pos["entry"] - _ltp_u), 2)
                    _pnl_rs = round(_pts * _qty_i, 2)
                    _pos.update(exit="Stop-All", exit_price=round(_ltp_u, 2), exit_time=str(_now_stop),
                                points=_pts, pnl_rs=_pnl_rs)
                    _pp["balance"] = round(_pp.get("balance", STARTING_CAPITAL) + _pnl_rs, 2)
                    _pp["closed"].append(_pos)
                    del _pp["open"][_inst_name]
                    _closed_count += 1
                else:
                    del _pp["open"][_inst_name]
        save_paper(_pp)
        st.session_state.trading_live = False
        st.success(f"Stopped -- squared off {_closed_count} position(s).")
        st.rerun()

    if reset_clicked:
        save_paper({"open": {}, "closed": [], "ignored": [], "balance": STARTING_CAPITAL})
        st.session_state.trading_live = True
        st.rerun()

    live_on = st.session_state.trading_live'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_startstop")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- Start/Stop buttons added. Stop squares off every open position at real current price and pauses everything.")
