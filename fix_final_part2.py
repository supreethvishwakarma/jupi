PATH = "app.py"
START = "# ---------------------------------------------------------------- paper trading"
END = "# ---------------------------------------------------------------- chart"

new_tab_paper = '''# ---------------------------------------------------------------- paper trading

with tab_paper:
    st.subheader("Paper trading — live")
    st.caption("Buys the real ATM option (call on a bullish signal, put on a bearish one) "
               "at its actual live bid/ask -- not a synthetic premium model. The underlying's "
               "price still drives the SL/Target trigger, since that's what the strategy's "
               "structure is based on; the option's own real price drives the P&L. Real "
               "AngelOne-style charges are deducted per trade. Trading only runs within each "
               "instrument's market hours (NSE/BSE 9:15AM-3:30PM, MCX 9:15AM-10:55PM). No real "
               "orders are sent. One position per instrument, shared balance.")

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
                   f"@ Rs {round(exit_premium, 2)} · P&L Rs {pnl_rs:+,.0f}")

    if "trading_live" not in st.session_state:
        st.session_state.trading_live = False

    st.markdown("""
    <style>
    div[data-testid="stButton"] button {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        padding: 1.1rem 0.5rem !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    big1, big2 = st.columns(2)
    start_clicked = big1.button("\\u25b6\\ufe0f  START PAPER TRADING", type="primary",
                                 disabled=st.session_state.trading_live, use_container_width=True)
    stop_clicked = big2.button("\\u23f9\\ufe0f  STOP & SQUARE OFF ALL",
                                disabled=not st.session_state.trading_live, use_container_width=True)

    if st.session_state.trading_live:
        st.success("\\U0001F7E2 Paper trading is RUNNING -- scanning and monitoring live.")
    else:
        st.warning("\\U0001F534 Paper trading is STOPPED. Set your Instrument, Lot size, Strategy, "
                   "and \\"Paper trade these instruments\\" above, then click START.")

    top = st.columns([1, 1, 1])
    REFRESH_SECONDS = top[0].number_input("Signal scan (sec)", 30, 600, 60, 15,
                                           help="How often to check for NEW signals via REST candles. Keep at 60+.")
    STARTING_CAPITAL = top[1].number_input("Paper capital (Rs)", 10000, 10000000, 100000, 5000,
                                            help="Virtual starting balance. Only applied after Reset.")
    reset_clicked = top[2].button("Reset paper account")

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

    live_on = st.session_state.trading_live

    _pp_for_export = load_paper()
    if _pp_for_export.get("closed"):
        if st.button("Export trade book (CSV)", key="export_trade_book"):
            from zoneinfo import ZoneInfo as _ZoneInfo
            _ts = dt.datetime.now(_ZoneInfo("Asia/Kolkata")).strftime("%Y%m%d_%H%M%S")
            _export_path = f"trade_book_export_{_ts}.csv"
            _edf = pd.DataFrame(_pp_for_export["closed"])
            if "time" in _edf.columns:
                _edf = _edf.rename(columns={"time": "entry_time"})
            _first_cols = [x for x in ["instrument", "strategy", "dir", "type", "entry_time",
                                        "entry", "exit_time", "exit", "exit_price", "pnl_rs"]
                           if x in _edf.columns]
            _edf = _edf[_first_cols + [x for x in _edf.columns if x not in _first_cols]]
            _edf.to_csv(_export_path, index=False)
            st.success(f"Saved {len(_pp_for_export['closed'])} trades to {_export_path}")

    @st.fragment(run_every=1 if live_on else None)
    def fast_panel():
        from zoneinfo import ZoneInfo
        pp = load_paper()
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        ts = tick_service()

        blocked_total = sum(p.get("capital_blocked", 0) for name, p in pp["open"].items()
                            if p.get("status") == "open" and name in PAPER_INSTRUMENTS)
        _orphans = {name: p.get("capital_blocked", 0) for name, p in pp["open"].items()
                    if name not in PAPER_INSTRUMENTS}
        if _orphans:
            st.warning(f"Orphaned position(s) in storage for instruments not currently selected: "
                       f"{', '.join(_orphans)} -- click 'Reset paper account' to clear these.")
        balance = pp.get("balance", STARTING_CAPITAL)
        b1, b2, b3 = st.columns(3)
        b1.metric("Available", f"Rs {balance:,.0f}")
        b2.metric("Blocked in trades", f"Rs {blocked_total:,.0f}")
        b3.metric("Total equity", f"Rs {balance + blocked_total:,.0f}")

        st.caption(f"Strategy: **{STRATEGY}** · Instruments: **{', '.join(PAPER_INSTRUMENTS)}**")

        any_live = False
        for inst_name in PAPER_INSTRUMENTS:
            tok, exch, lot_size = INSTRUMENTS[inst_name]
            qty_i = lot_size * LOTS
            ts.ensure_subscribed(exch, tok)
            ltp = ts.get_ltp(tok)
            any_live = any_live or (ltp is not None)
            pos = pp["open"].get(inst_name)

            st.markdown(f"**{inst_name}**")

            if pos is None:
                if not is_market_open(exch, now):
                    st.caption(f"\\U0001F512 Market closed for {inst_name} "
                               f"({_market_hours_str(exch)}) -- not scanning.")
                else:
                    feed = "\\U0001F7E2" if ltp is not None else "\\U0001F7E1"
                    st.caption(f"{feed} No open position — watching for a fresh signal… "
                               f"Underlying LTP {ltp if ltp is not None else '—'}")
                continue

            if pos["status"] == "pending_entry":
                st.caption(f"Order pending — entry. {pos['dir'].capitalize()} {pos['type']} "
                           f"signal placed {pos['placed_time']}, filling on next tick.")
                bull = pos["dir"] == "bullish"
                has_option = "option_token" in pos
                fill_price = None
                if has_option:
                    ts.ensure_subscribed(pos["option_exch"], pos["option_token"])
                    _bid, fill_price = get_bid_ask(pos["option_exch"], pos["option_token"])
                elif ltp is not None:
                    fill_price = ltp

                if ltp is None:
                    st.warning("No underlying live tick yet — entry still pending.")
                elif has_option and fill_price is None:
                    st.warning(f"No live price yet for {pos.get('option_symbol', 'the option')} -- entry still pending.")
                else:
                    sl = pos["sl"]
                    risk = (ltp - sl) if bull else (sl - ltp)
                    if risk <= 0:
                        pp["ignored"].append(f"{inst_name}|{pos['signal_ts']}")
                        del pp["open"][inst_name]
                        save_paper(pp)
                        st.warning("Entry cancelled — price moved past the stop before the order could fill.")
                    else:
                        target = round(ltp + RR*risk if bull else ltp - RR*risk, 2)
                        if has_option:
                            capital_blocked = round(fill_price * qty_i, 2)
                            pos.update(status="open", entry=round(fill_price, 2),
                                       underlying_entry=round(ltp, 2), sl=sl, target=target,
                                       capital_blocked=capital_blocked, time=str(now))
                            pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) - capital_blocked, 2)
                            save_paper(pp)
                            st.success(f"Bought {pos['option_symbol']} at Rs {round(fill_price, 2)} (real ask) "
                                       f"· Rs {capital_blocked:,.0f} blocked")
                        else:
                            pos.update(status="open", mode="raw", entry=round(ltp, 2), time=str(now),
                                       target=target)
                            save_paper(pp)
                            st.success(f"Filled at {round(ltp, 2)} (raw underlying -- no option chain configured)")

            elif pos["status"] == "open":
                mode = pos.get("mode", "option" if "option_token" in pos else "raw")

                if mode == "raw":
                    if ltp is None:
                        st.warning("No live tick yet.")
                    else:
                        bull = pos["dir"] == "bullish"
                        hit_sl = ltp <= pos["sl"] if bull else ltp >= pos["sl"]
                        hit_tg = ltp >= pos["target"] if bull else ltp <= pos["target"]
                        pts = round((ltp - pos["entry"]) if bull else (pos["entry"] - ltp), 2)
                        sqoff = st.button(f"Square off {inst_name}", key=f"sqoff_{inst_name}")
                        if hit_sl or hit_tg or sqoff:
                            trigger = ("SL" if hit_sl else "Target") if (hit_sl or hit_tg) else "Manual"
                            pnl_rs = round(pts * qty_i, 2)
                            pos.update(exit=trigger, exit_price=round(ltp, 2), exit_time=str(now),
                                       points=pts, pnl_rs=pnl_rs)
                            pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + pnl_rs, 2)
                            pp["closed"].append(pos)
                            del pp["open"][inst_name]
                            save_paper(pp)
                            st.success(f"{inst_name}: closed — {trigger} @ {round(ltp, 2)} · P&L Rs {pnl_rs:+,.0f}")
                        else:
                            c = st.columns(5)
                            c[0].metric("Direction", pos["dir"].capitalize())
                            c[1].metric("Entry", pos["entry"])
                            c[2].metric("LTP", ltp)
                            c[3].metric("P&L (pts)", f"{pts:+.2f}", delta=f"{pts:+.2f}")
                            c[4].metric("P&L (Rs)", f"{pts*qty_i:+,.0f}", delta=f"{pts*qty_i:+,.0f}")
                            st.caption(f"SL {pos['sl']} · Target {pos['target']} · filled {pos['time']}")
                else:
                    option_token = pos["option_token"]
                    option_exch = pos["option_exch"]
                    ts.ensure_subscribed(option_exch, option_token)
                    opt_ltp = ts.get_ltp(option_token)
                    if ltp is None:
                        st.warning("No underlying live tick yet.")
                    else:
                        bull = pos["dir"] == "bullish"
                        hit_sl = ltp <= pos["sl"] if bull else ltp >= pos["sl"]
                        hit_tg = ltp >= pos["target"] if bull else ltp <= pos["target"]
                        sqoff = st.button(f"Square off {inst_name}", key=f"sqoff_{inst_name}")
                        if hit_sl or hit_tg or sqoff:
                            trigger = ("SL" if hit_sl else "Target") if (hit_sl or hit_tg) else "Manual"
                            bid, ask = get_bid_ask(option_exch, option_token)
                            exit_premium = bid if bid is not None else opt_ltp
                            if exit_premium is None:
                                st.warning(f"{pos.get('option_symbol','')}: no live price yet, will retry next cycle.")
                            else:
                                _close_position(pp, inst_name, pos, trigger, exit_premium, now, qty_i)
                        else:
                            live_price = opt_ltp if opt_ltp is not None else pos["entry"]
                            opt_pts = round(live_price - pos["entry"], 2)
                            pnl_rs = round(opt_pts * qty_i, 2)

                            _bid_now, _ask_now = get_bid_ask(option_exch, option_token)
                            if _bid_now is not None:
                                _net_cost = real_options_cost(pos["entry"], _bid_now, qty_i)
                                _net_proceeds = round(_bid_now * qty_i - _net_cost, 2)
                                _net_pnl = round(_net_proceeds - pos.get("capital_blocked", 0), 2)
                            else:
                                _net_pnl = None

                            c = st.columns(5)
                            c[0].metric("Option", pos.get("option_symbol", "-"))
                            c[1].metric("Entry premium", pos["entry"])
                            c[2].metric("LTP (mid)", live_price if opt_ltp is not None else "—")
                            c[3].metric("Mid P&L (pts)", f"{opt_pts:+.2f}", delta=f"{opt_pts:+.2f}")
                            c[4].metric("Mid P&L (Rs)", f"{pnl_rs:+,.0f}", delta=f"{pnl_rs:+,.0f}")
                            if _net_pnl is not None:
                                st.info(f"\\U0001F4B0 If you Square Off right now: **Rs {_net_pnl:+,.0f}** net "
                                        f"(real bid {_bid_now}, minus real spread + costs)")
                            st.caption(f"Underlying: {pos.get('underlying_entry','-')} \\u2192 {ltp} · "
                                       f"SL(underlying) {pos['sl']} · Target(underlying) {pos['target']} · "
                                       f"blocked Rs {pos.get('capital_blocked', 0):,.0f}")

        status_txt = "\\U0001F7E2 ticks live" if any_live else "\\U0001F7E1 waiting for ticks"
        st.caption(f"{status_txt} · checked {now:%H:%M:%S}" + ("" if live_on else " · paused"))

        st.markdown("**Closed trades**")
        if pp["closed"]:
            c = pd.DataFrame(pp["closed"])
            if "pnl_rs" not in c.columns:
                c["pnl_rs"] = pd.NA
            missing = c["pnl_rs"].isna()
            if missing.any():
                if "proceeds" in c.columns and "capital_blocked" in c.columns:
                    fallback = c["proceeds"].fillna(0) - c["capital_blocked"].fillna(0)
                else:
                    fallback = c["points"] * LOTSIZE * LOTS
                c.loc[missing, "pnl_rs"] = fallback[missing]
            c["pnl_rs"] = c["pnl_rs"].astype(float).round(2)
            if "time" in c.columns:
                c = c.rename(columns={"time": "entry_time"})
            tot = c.points.sum()
            realized = pp.get("balance", STARTING_CAPITAL) - STARTING_CAPITAL
            m = st.columns(5)
            m[0].metric("Trades", len(c))
            m[1].metric("Win rate", f"{100*(c.points>0).mean():.0f}%")
            m[2].metric("Gross", f"{tot:+.1f} pts")
            m[3].metric("Realized P&L", f"Rs {realized:+,.0f}", delta=f"{realized:+,.0f}")
            m[4].metric("Balance", f"Rs {pp.get('balance', STARTING_CAPITAL):,.0f}")
            cols_show = [x for x in ["instrument", "strategy", "dir", "type", "option_symbol",
                                      "entry_time", "entry", "sl", "target", "exit", "exit_price",
                                      "exit_time", "points", "real_cost", "pnl_rs"] if x in c.columns]
            color_cols = [x for x in ["points", "pnl_rs"] if x in cols_show]
            try:
                styled = c[cols_show].style.map(_pnl_color, subset=color_cols)
            except AttributeError:
                styled = c[cols_show].style.applymap(_pnl_color, subset=color_cols)
            st.dataframe(styled, use_container_width=True)
        else:
            st.caption("No closed paper trades yet.")

    fast_panel()

    @st.fragment(run_every=REFRESH_SECONDS if live_on else None)
    def slow_panel():
        from zoneinfo import ZoneInfo
        pp = load_paper()
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        any_opened = False

        for inst_name in PAPER_INSTRUMENTS:
            if inst_name in pp["open"]:
                continue
            tok, exch, _ = INSTRUMENTS[inst_name]
            if not is_market_open(exch, now):
                continue
            time.sleep(1.5)
            try:
                chart_df = fetch((now - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
                                  now.strftime("%Y-%m-%d %H:%M"), INTERVAL, tok, exch)
            except Exception as e:
                msg = str(e)
                _cached = st.session_state.get(f"proximity_{inst_name}")
                _suffix = f" (last known: {{_cached[0]}}, as of {{_cached[1]}})" if _cached else ""
                if "exceeding access rate" in msg:
                    st.caption(f"\\u26a0\\ufe0f {inst_name}: rate limited, will retry next cycle{_suffix}")
                else:
                    st.error(f"{inst_name}: broker call failed: {e}{_suffix}")
                continue

            if chart_df.empty or len(chart_df) < 3:
                continue

            sw, sig = get_signals(chart_df)

            if STRATEGY == "Hilega Milega (RSI x WMA)" and len(chart_df) > WMA_PERIOD:
                _r = _wilder_rsi(chart_df["close"].astype(float), RSI_PERIOD)
                _w = _wma(_r, WMA_PERIOD)
                if not pd.isna(_r.iloc[-1]) and not pd.isna(_w.iloc[-1]):
                    _diff = round(_r.iloc[-1] - _w.iloc[-1], 2)
                    _side = "above" if _diff > 0 else "below"
                    _msg = f"RSI {{_r.iloc[-1]:.1f}} {{_side}} WMA {{_w.iloc[-1]:.1f}} (gap {{_diff:+.1f}})"
                    st.session_state[f"proximity_{inst_name}"] = (_msg, f"{now:%H:%M:%S}")
                    st.caption(f"{inst_name}: {{_msg}} -- crosses to trigger a signal")

            use = sig if (sig.empty or SIGNAL == "both") else sig[sig.type == SIGNAL]
            if use.empty:
                continue
            last_sig = use.iloc[-1]
            is_fresh = last_sig.broken_i >= len(chart_df) - 2
            ts_sig = str(chart_df.iloc[-1].timestamp)
            seen = ({c.get("signal_ts") for c in pp["closed"] if c.get("instrument") == inst_name}
                    | {x.split("|", 1)[1] for x in pp["ignored"] if x.startswith(f"{inst_name}|")})
            if is_fresh and ts_sig not in seen:
                entry_close = float(chart_df.iloc[-1].close)
                new_pos = dict(status="pending_entry", signal_ts=ts_sig,
                                instrument=inst_name, strategy=STRATEGY,
                                dir=last_sig.direction,
                                type=last_sig.type, sl=round(float(last_sig.Level), 2),
                                placed_time=str(now))
                opt_cfg = get_option_config(inst_name)
                if opt_cfg is not None:
                    prefix, search_exch, weekly_1letter = opt_cfg
                    chain = find_atm_option(prefix, search_exch, weekly_1letter, round(entry_close/100)*100)
                    if chain is not None:
                        bull = last_sig.direction == "bullish"
                        new_pos["option_token"] = chain["ce_token"] if bull else chain["pe_token"]
                        new_pos["option_symbol"] = chain["ce_symbol"] if bull else chain["pe_symbol"]
                        new_pos["option_exch"] = chain["exch"]
                pp["open"][inst_name] = new_pos
                save_paper(pp)
                any_opened = True

        if any_opened:
            st.rerun()

        st.caption(f"Signal scan {now:%H:%M:%S}" + ("" if live_on else " · paused"))

    slow_panel()

'''

with open(PATH) as f:
    content = f.read()

if START not in content or END not in content:
    print("ERROR: markers not found")
    raise SystemExit(1)
start_i = content.index(START)
end_i = content.index(END, start_i)
content = content[:start_i] + new_tab_paper + content[end_i:]

import shutil
shutil.copy(PATH, PATH + ".bak_finalpart2")

with open(PATH, "w") as f:
    f.write(content)

print("Part 2 done -- full Paper trading tab replaced. app.py should now be fully consistent.")
