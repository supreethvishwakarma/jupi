PATH = "app.py"

old1 = '''    if stop_clicked:
        from zoneinfo import ZoneInfo as _ZoneInfo
        _pp = load_paper()
        _ts_stop = tick_service()
        _now_stop = dt.datetime.now(_ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        _closed_count = 0
        for _inst_name, _pos in list(_pp["open"].items()):
            _tok, _exch, _lot = INSTRUMENTS.get(_inst_name, (None, None, 1))
            _qty_i = _lot * LOTS_PER_INSTRUMENT.get(_inst_name, 1)
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
        st.rerun()'''

new1 = '''    if stop_clicked:
        _pp = load_paper()
        _closed_count = _square_off_all(_pp, "Stop-All")
        st.session_state.trading_live = False
        st.success(f"Stopped -- squared off {_closed_count} position(s).")
        st.rerun()'''

old2 = '''        ts = tick_service()
        ts.ensure_connected()

        blocked_total = sum(p.get("capital_blocked", 0) for name, p in pp["open"].items()
                            if p.get("status") == "open" and name in PAPER_INSTRUMENTS)'''

new2 = '''        ts = tick_service()
        ts.ensure_connected()

        today_date = now.date()
        _todays_pnl = round(sum((t.get("pnl_rs", 0) or 0) for t in pp["closed"]
                                 if _safe_date(t.get("exit_time", "")) == today_date), 2)
        if live_on and DAILY_PROFIT_TARGET > 0 and _todays_pnl >= DAILY_PROFIT_TARGET:
            if pp["open"]:
                _n = _square_off_all(pp, "Daily-Target")
                st.session_state.trading_live = False
                st.success(f"\\U0001F3AF Daily profit target of Rs {DAILY_PROFIT_TARGET:,.0f} reached "
                           f"(today's realized P&L: Rs {_todays_pnl:,.0f}). Squared off {_n} position(s) "
                           f"and stopped trading for today.")
                st.rerun()
            else:
                st.session_state.trading_live = False
                st.info(f"\\U0001F3AF Daily profit target of Rs {DAILY_PROFIT_TARGET:,.0f} already reached "
                        f"(today's realized P&L: Rs {_todays_pnl:,.0f}). Trading stopped for today.")

        blocked_total = sum(p.get("capital_blocked", 0) for name, p in pp["open"].items()
                            if p.get("status") == "open" and name in PAPER_INSTRUMENTS)'''

with open(PATH) as f:
    content = f.read()

n1, n2 = content.count(old1), content.count(old2)
if n1 != 1 or n2 != 1:
    print(f"WARNING: expected 1 match each, found {n1} and {n2}. Aborting.")
    raise SystemExit(1)
content = content.replace(old1, new1).replace(old2, new2)

import shutil
shutil.copy(PATH, PATH + ".bak_dailyrisk3")

with open(PATH, "w") as f:
    f.write(content)

print("Patched (3/4) -- daily profit target auto-stop wired in, Stop button simplified.")
