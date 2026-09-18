PATH = "app.py"

old1 = '''STRATEGY = st.sidebar.selectbox("Strategy",
    ["Vanguard (RSI x WMA)", "Scalping (EMA+VWAP+RSI)", "Supertrend (Trailing SL)"], index=0)

if STRATEGY == "Vanguard (RSI x WMA)":
    RSI_PERIOD = st.sidebar.slider("RSI period", 3, 30, 9, 1)
    WMA_PERIOD = st.sidebar.slider("WMA period (on RSI)", 5, 50, 21, 1,
                                    help="Classic setup: RSI(9) crossing its own WMA(21). "
                                         "Buy on cross above, sell on cross below.")
    MIN_GAP = st.sidebar.slider("Minimum signal strength (RSI-WMA gap)", 0.0, 15.0, 3.0, 0.5,
                                 help="Requires RSI to be at least this far past its WMA at the "
                                      "crossing candle -- filters out marginal, whipsaw-prone "
                                      "crosses. Higher = fewer, more decisive signals. 0 = off "
                                      "(any cross counts, original behavior).")
    ST_PERIOD, ST_MULT, EMA_PERIOD, SCALP_RSI_PERIOD = 7, 2.5, 9, 14
elif STRATEGY == "Scalping (EMA+VWAP+RSI)":
    MIN_GAP = 0.0
    EMA_PERIOD = st.sidebar.slider("EMA period", 3, 30, 9, 1)
    SCALP_RSI_PERIOD = st.sidebar.slider("RSI period", 5, 30, 14, 1)
    st.sidebar.caption("Entry when close crosses above/below BOTH the EMA and session VWAP, "
                        "confirmed by RSI. SL = that candle's own high/low -- tight and fast.")
    RSI_PERIOD, WMA_PERIOD, ST_PERIOD, ST_MULT = 9, 21, 7, 2.5
else:
    ST_PERIOD = st.sidebar.slider("ATR period", 5, 21, 7, 1,
                                   help="Lower = more responsive (scalping). Classic default is 10; "
                                        "7 is a common scalping tune.")
    ST_MULT = st.sidebar.slider("ATR multiplier", 1.0, 5.0, 2.5, 0.5,
                                 help="Lower = tighter trailing stop, more flips. Classic default is 3.0.")
    RSI_PERIOD, WMA_PERIOD, EMA_PERIOD, SCALP_RSI_PERIOD = 9, 21, 9, 14

SWING, SIGNAL, OR_BARS, CLOSE_BREAK = 20, "both", 1, True  # unused (SMC/ORB removed), kept for other code paths'''

new1 = '''STRATEGY = st.sidebar.selectbox("Strategy",
    ["Vanguard (RSI x WMA)", "Scalping (EMA+VWAP+RSI)", "Supertrend (Trailing SL)",
     "ATM Straddle (Time-based)"], index=0)

if STRATEGY == "Vanguard (RSI x WMA)":
    RSI_PERIOD = st.sidebar.slider("RSI period", 3, 30, 9, 1)
    WMA_PERIOD = st.sidebar.slider("WMA period (on RSI)", 5, 50, 21, 1,
                                    help="Classic setup: RSI(9) crossing its own WMA(21). "
                                         "Buy on cross above, sell on cross below.")
    MIN_GAP = st.sidebar.slider("Minimum signal strength (RSI-WMA gap)", 0.0, 15.0, 3.0, 0.5,
                                 help="Requires RSI to be at least this far past its WMA at the "
                                      "crossing candle -- filters out marginal, whipsaw-prone "
                                      "crosses. Higher = fewer, more decisive signals. 0 = off "
                                      "(any cross counts, original behavior).")
    ST_PERIOD, ST_MULT, EMA_PERIOD, SCALP_RSI_PERIOD = 7, 2.5, 9, 14
    STRADDLE_ENTRY_TIME, STRADDLE_TARGET_PCT, STRADDLE_SL_PCT, STRADDLE_SKIP_DAYS = dt.time(9, 20), 30, 30, ["Tuesday"]
elif STRATEGY == "Scalping (EMA+VWAP+RSI)":
    MIN_GAP = 0.0
    EMA_PERIOD = st.sidebar.slider("EMA period", 3, 30, 9, 1)
    SCALP_RSI_PERIOD = st.sidebar.slider("RSI period", 5, 30, 14, 1)
    st.sidebar.caption("Entry when close crosses above/below BOTH the EMA and session VWAP, "
                        "confirmed by RSI. SL = that candle's own high/low -- tight and fast.")
    RSI_PERIOD, WMA_PERIOD, ST_PERIOD, ST_MULT = 9, 21, 7, 2.5
    STRADDLE_ENTRY_TIME, STRADDLE_TARGET_PCT, STRADDLE_SL_PCT, STRADDLE_SKIP_DAYS = dt.time(9, 20), 30, 30, ["Tuesday"]
elif STRATEGY == "Supertrend (Trailing SL)":
    ST_PERIOD = st.sidebar.slider("ATR period", 5, 21, 7, 1,
                                   help="Lower = more responsive (scalping). Classic default is 10; "
                                        "7 is a common scalping tune.")
    ST_MULT = st.sidebar.slider("ATR multiplier", 1.0, 5.0, 2.5, 0.5,
                                 help="Lower = tighter trailing stop, more flips. Classic default is 3.0.")
    RSI_PERIOD, WMA_PERIOD, EMA_PERIOD, SCALP_RSI_PERIOD = 9, 21, 9, 14
    MIN_GAP = 0.0
    STRADDLE_ENTRY_TIME, STRADDLE_TARGET_PCT, STRADDLE_SL_PCT, STRADDLE_SKIP_DAYS = dt.time(9, 20), 30, 30, ["Tuesday"]
else:
    STRADDLE_ENTRY_TIME = st.sidebar.time_input("Straddle entry time", value=dt.time(9, 20))
    STRADDLE_TARGET_PCT = st.sidebar.slider("Profit target (%)", 5, 100, 30, 5,
                                             help="Exit both legs when combined premium value gains this % from entry.")
    STRADDLE_SL_PCT = st.sidebar.slider("Stop loss (%)", 5, 100, 30, 5,
                                         help="Exit both legs when combined premium value loses this % from entry.")
    STRADDLE_SKIP_DAYS = st.sidebar.multiselect("Skip these days",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], default=["Tuesday"],
        help="NIFTY's weekly expiry (Tuesday) sees the steepest theta decay, which especially "
             "hurts a long straddle buyer -- skipped by default. Adjust as you like.")
    RSI_PERIOD, WMA_PERIOD, EMA_PERIOD, SCALP_RSI_PERIOD, ST_PERIOD, ST_MULT, MIN_GAP = 9, 21, 9, 14, 7, 2.5, 0.0

SWING, SIGNAL, OR_BARS, CLOSE_BREAK = 20, "both", 1, True  # unused (SMC/ORB removed), kept for other code paths'''

old2 = '''    def _square_off_all(pp, reason="Stop-All"):
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
            if "option_token" in _pos:'''

new2 = '''    def _close_straddle(pp, inst_name, pos, trigger, ce_exit, pe_exit, now, qty_i):
        ce_cost = real_options_cost(pos["ce_entry"], ce_exit, qty_i)
        pe_cost = real_options_cost(pos["pe_entry"], pe_exit, qty_i)
        total_cost = round(ce_cost + pe_cost, 2)
        proceeds = round((ce_exit + pe_exit) * qty_i - total_cost, 2)
        pnl_rs = round(proceeds - pos.get("capital_blocked", 0), 2)
        pos.update(exit=trigger, ce_exit=round(ce_exit, 2), pe_exit=round(pe_exit, 2),
                   exit_time=str(now), real_cost=total_cost, proceeds=proceeds, pnl_rs=pnl_rs,
                   points=round((ce_exit + pe_exit) - (pos["ce_entry"] + pos["pe_entry"]), 2))
        pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + proceeds, 2)
        pp["closed"].append(pos)
        del pp["open"][inst_name]
        save_paper(pp)
        st.success(f"{inst_name}: closed straddle ({pos.get('ce_symbol','')}+{pos.get('pe_symbol','')}) "
                   f"\\u2014 {trigger} \\u00b7 P&L Rs {pnl_rs:+,.0f}")

    def _square_off_all(pp, reason="Stop-All"):
        from zoneinfo import ZoneInfo as _ZoneInfo
        _ts_stop = tick_service()
        _now_stop = dt.datetime.now(_ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        _closed_count = 0
        for _inst_name, _pos in list(pp["open"].items()):
            _tok, _exch, _lot = INSTRUMENTS.get(_inst_name, (None, None, 1))
            _qty_i = _pos.get("qty", _lot * LOTS_PER_INSTRUMENT.get(_inst_name, 1))
            if _pos.get("status") != "open":
                del pp["open"][_inst_name]
                continue
            if "ce_token" in _pos:
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

old3 = '''        for inst_name in PAPER_INSTRUMENTS:
            tok, exch, lot_size = INSTRUMENTS[inst_name]
            qty_i = lot_size * LOTS_PER_INSTRUMENT.get(inst_name, 1)
            ts.ensure_subscribed(exch, tok)
            ltp = ts.get_ltp(tok)
            any_live = any_live or (ltp is not None)
            pos = pp["open"].get(inst_name)

            st.markdown(f"**{inst_name}**")

            if pos is None:'''

new3 = '''        for inst_name in PAPER_INSTRUMENTS:
            tok, exch, lot_size = INSTRUMENTS[inst_name]
            qty_i = lot_size * LOTS_PER_INSTRUMENT.get(inst_name, 1)
            ts.ensure_subscribed(exch, tok)
            ltp = ts.get_ltp(tok)
            any_live = any_live or (ltp is not None)
            pos = pp["open"].get(inst_name)

            st.markdown(f"**{inst_name}**")

            if pos is not None and pos.get("mode") == "straddle":
                ts.ensure_subscribed(pos["ce_exch"], pos["ce_token"])
                ts.ensure_subscribed(pos["pe_exch"], pos["pe_token"])
                ce_ltp = ts.get_ltp(pos["ce_token"])
                pe_ltp = ts.get_ltp(pos["pe_token"])
                _sqty = pos.get("qty", qty_i)
                if ce_ltp is None or pe_ltp is None:
                    st.caption("Straddle open \\u2014 waiting for live option ticks...")
                else:
                    _combined_entry = pos["ce_entry"] + pos["pe_entry"]
                    _combined_now = ce_ltp + pe_ltp
                    _pct_change = round((_combined_now - _combined_entry) / _combined_entry * 100, 2)
                    _hit_target = _pct_change >= pos.get("target_pct", 30)
                    _hit_sl = _pct_change <= -pos.get("sl_pct", 30)
                    _sqoff = st.button(f"Square off straddle {inst_name}", key=f"sqoff_straddle_{inst_name}")
                    if _hit_target or _hit_sl or _sqoff:
                        _trigger = "Target" if _hit_target else "SL" if _hit_sl else "Manual"
                        _ce_bid, _ce_ask = get_bid_ask(pos["ce_exch"], pos["ce_token"])
                        _pe_bid, _pe_ask = get_bid_ask(pos["pe_exch"], pos["pe_token"])
                        _ce_exit = _ce_bid if _ce_bid is not None else ce_ltp
                        _pe_exit = _pe_bid if _pe_bid is not None else pe_ltp
                        _close_straddle(pp, inst_name, pos, _trigger, _ce_exit, _pe_exit, now, _sqty)
                    else:
                        c = st.columns(5)
                        c[0].metric("Combined entry", round(_combined_entry, 2))
                        c[1].metric("Combined now", round(_combined_now, 2))
                        c[2].metric("Change (%)", f"{_pct_change:+.1f}%")
                        c[3].metric("CE", pos.get("ce_symbol", "-"))
                        c[4].metric("PE", pos.get("pe_symbol", "-"))
                        st.caption(f"Target {pos.get('target_pct',30)}% \\u00b7 SL {pos.get('sl_pct',30)}% \\u00b7 "
                                   f"blocked Rs {pos.get('capital_blocked', 0):,.0f} \\u00b7 opened {pos.get('time','')}")
                continue

            if pos is None:'''

old4 = '''        for inst_name in PAPER_INSTRUMENTS:
            tok, exch, _ = INSTRUMENTS[inst_name]
            if not is_market_open(exch, now):
                continue

            if inst_name in pp["open"]:
                _existing = pp["open"][inst_name]
                if STRATEGY == "Supertrend (Trailing SL)" and _existing.get("status") == "open":'''

new4 = '''        for inst_name in PAPER_INSTRUMENTS:
            tok, exch, _ = INSTRUMENTS[inst_name]
            if not is_market_open(exch, now):
                continue

            if STRATEGY == "ATM Straddle (Time-based)":
                if inst_name in pp["open"]:
                    continue
                _today_name = now.strftime("%A")
                if _today_name in STRADDLE_SKIP_DAYS:
                    continue
                if now.time() < STRADDLE_ENTRY_TIME:
                    continue
                _already_today = any(
                    c.get("instrument") == inst_name and c.get("signal_ts") == str(now.date())
                    for c in pp["closed"])
                if _already_today:
                    continue
                opt_cfg = get_option_config(inst_name)
                if opt_cfg is None:
                    continue
                prefix, search_exch, weekly_1letter, min_runway = opt_cfg
                spot_ltp = ts.get_ltp(tok)
                if spot_ltp is None:
                    continue
                chain = find_atm_option(prefix, search_exch, weekly_1letter,
                                         round(spot_ltp / 100) * 100, min_runway)
                if chain is None:
                    continue
                ce_bid, ce_ask = get_bid_ask(chain["exch"], chain["ce_token"])
                pe_bid, pe_ask = get_bid_ask(chain["exch"], chain["pe_token"])
                if ce_ask is None or pe_ask is None:
                    continue
                _qty_st = INSTRUMENTS[inst_name][2] * LOTS_PER_INSTRUMENT.get(inst_name, 1)
                _capital_blocked_st = round((ce_ask + pe_ask) * _qty_st, 2)
                new_straddle = dict(status="open", mode="straddle", signal_ts=str(now.date()),
                                     instrument=inst_name, strategy=STRATEGY, qty=_qty_st,
                                     ce_token=chain["ce_token"], ce_symbol=chain["ce_symbol"],
                                     ce_entry=round(ce_ask, 2), ce_exch=chain["exch"],
                                     pe_token=chain["pe_token"], pe_symbol=chain["pe_symbol"],
                                     pe_entry=round(pe_ask, 2), pe_exch=chain["exch"],
                                     capital_blocked=_capital_blocked_st, time=str(now),
                                     target_pct=STRADDLE_TARGET_PCT, sl_pct=STRADDLE_SL_PCT)
                pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) - _capital_blocked_st, 2)
                pp["open"][inst_name] = new_straddle
                save_paper(pp)
                any_opened = True
                continue

            if inst_name in pp["open"]:
                _existing = pp["open"][inst_name]
                if STRATEGY == "Supertrend (Trailing SL)" and _existing.get("status") == "open":'''

with open(PATH, encoding="utf-8") as f:
    content = f.read()

results = []
for i, (old, new) in enumerate([(old1, new1), (old2, new2), (old3, new3), (old4, new4)], 1):
    n = content.count(old)
    results.append(n)
    if n != 1:
        print(f"WARNING patch {i}: expected 1 match, found {n}. Aborting.")
        raise SystemExit(1)
    content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_straddle")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched -- ATM Straddle (Time-based) strategy fully added: entry, monitoring, exit, and Stop-All support.")
