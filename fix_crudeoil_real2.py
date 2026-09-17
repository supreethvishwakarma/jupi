PATH = "app.py"
START = "# ---------------------------------------------------------------- paper trading"
END = "# ---------------------------------------------------------------- chart"

new_tab_paper = '''# ---------------------------------------------------------------- paper trading

with tab_paper:
    st.subheader("Paper trading — live")
    st.caption("Position monitoring uses real-time WebSocket ticks. MCX futures fill at "
               "real bid/ask from the live order book; NSE index positions use the "
               "delta/theta option-premium model. New-signal scanning uses REST candles "
               "on a slower cycle. Real AngelOne-style charges are deducted per trade. "
               "No real orders are sent. One position per instrument, shared balance.")

    top = st.columns([1, 1, 1, 1])
    live_on = top[0].toggle("Live", value=True, help="Turn off to pause both loops")
    REFRESH_SECONDS = top[1].number_input("Signal scan (sec)", 30, 600, 60, 15,
                                           help="How often to check for NEW signals via REST candles. Keep at 60+.")
    STARTING_CAPITAL = top[2].number_input("Paper capital (Rs)", 10000, 10000000, 100000, 5000,
                                            help="Virtual starting balance. Only applied after Reset.")
    if top[3].button("Reset paper account"):
        save_paper({"open": {}, "closed": [], "ignored": [], "balance": STARTING_CAPITAL})
        st.rerun()

    if not OPT_MODE and not any(INSTRUMENTS[i][1] == "MCX" for i in PAPER_INSTRUMENTS):
        st.info("Capital tracking needs 'Simulate option buying' on (for NSE indices) or "
                "an MCX instrument selected (always tracked via margin). Otherwise P&L "
                "shows raw index points only.")

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

    def _close_position(pp, inst_name, pos, trigger, fill_price, now, qty_i, is_futures):
        bull = pos["dir"] == "bullish"
        pts = round((fill_price - pos["entry"]) if bull else (pos["entry"] - fill_price), 2)
        pos.update(exit=trigger, exit_price=round(fill_price, 2), exit_time=str(now), points=pts)
        if is_futures:
            cost = real_futures_cost(pos["entry"], fill_price, qty_i)
            pnl_rs = round(pts * qty_i - cost, 2)
            pos.update(real_cost=cost, pnl_rs=pnl_rs)
            pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + pos.get("capital_blocked", 0) + pnl_rs, 2)
        elif OPT_MODE and "entry_premium" in pos:
            hours_held = max((now - dt.datetime.fromisoformat(pos["time"])).total_seconds() / 3600, 0)
            opt_pts = round(pts*DELTA - hours_held*THETA_HR - SPREAD, 2)
            exit_premium = max(0.0, round(pos["entry_premium"] + opt_pts, 2))
            cost = real_options_cost(pos["entry_premium"], exit_premium, qty_i)
            proceeds = round(exit_premium * qty_i - cost, 2)
            pnl_rs = round(proceeds - pos.get("capital_blocked", 0), 2)
            pos.update(opt_points=opt_pts, exit_premium=exit_premium, proceeds=proceeds,
                       real_cost=cost, hours_held=round(hours_held, 2), pnl_rs=pnl_rs)
            pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + proceeds, 2)
        else:
            pnl_rs = round(pts * qty_i, 2)
            pos["pnl_rs"] = pnl_rs
            pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + pnl_rs, 2)
        pp["closed"].append(pos)
        del pp["open"][inst_name]
        save_paper(pp)
        st.success(f"{inst_name}: closed — {trigger} @ {round(fill_price, 2)} · P&L Rs {pnl_rs:+,.0f}")

    @st.fragment(run_every=1 if live_on else None)
    def fast_panel():
        from zoneinfo import ZoneInfo
        pp = load_paper()
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        ts = tick_service()

        blocked_total = sum(p.get("capital_blocked", 0) for p in pp["open"].values()
                            if p.get("status") in ("open", "pending_exit"))
        if OPT_MODE or blocked_total > 0 or any(INSTRUMENTS[i][1] == "MCX" for i in PAPER_INSTRUMENTS):
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
            is_futures = (exch == "MCX")
            ts.ensure_subscribed(exch, tok)
            ltp = ts.get_ltp(tok)
            any_live = any_live or (ltp is not None)
            pos = pp["open"].get(inst_name)

            st.markdown(f"**{inst_name}**" + (" _(futures, real bid/ask)_" if is_futures else ""))

            if pos is None:
                feed = "\\U0001F7E2" if ltp is not None else "\\U0001F7E1"
                st.caption(f"{feed} No open position — watching for a fresh signal… "
                           f"LTP {ltp if ltp is not None else '—'}")
                continue

            if pos["status"] == "pending_entry":
                st.caption(f"Order pending — entry. {pos['dir'].capitalize()} {pos['type']} "
                           f"signal placed {pos['placed_time']}, filling on next tick.")
                bull = pos["dir"] == "bullish"
                if is_futures:
                    bid, ask = get_bid_ask(exch, tok)
                    fill_price = ask if bull else bid
                else:
                    fill_price = ltp
                if fill_price is None:
                    st.warning("No live price yet — entry still pending.")
                else:
                    sl = pos["sl"]
                    risk = (fill_price - sl) if bull else (sl - fill_price)
                    if risk <= 0:
                        pp["ignored"].append(f"{inst_name}|{pos['signal_ts']}")
                        del pp["open"][inst_name]
                        save_paper(pp)
                        st.warning("Entry cancelled — price moved past the stop before the order could fill.")
                    else:
                        update = dict(status="open", entry=round(fill_price, 2), time=str(now),
                                      target=round(fill_price + RR*risk if bull else fill_price - RR*risk, 2))
                        if is_futures:
                            capital_blocked = round(MARGIN_PCT/100 * fill_price * qty_i, 2)
                            update["capital_blocked"] = capital_blocked
                            pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) - capital_blocked, 2)
                            msg = f"Filled at {round(fill_price, 2)} (real bid/ask) · Rs {capital_blocked:,.0f} margin blocked"
                        elif OPT_MODE:
                            capital_blocked = round(PREMIUM * qty_i, 2)
                            update.update(entry_premium=PREMIUM, capital_blocked=capital_blocked)
                            pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) - capital_blocked, 2)
                            msg = f"Filled at {round(fill_price, 2)} · Rs {capital_blocked:,.0f} blocked"
                        else:
                            msg = f"Filled at {round(fill_price, 2)}"
                        pos.update(update)
                        save_paper(pp)
                        st.success(msg)

            elif pos["status"] == "open":
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
                        if is_futures:
                            bid, ask = get_bid_ask(exch, tok)
                            fill_price = (bid if bull else ask) or ltp
                        else:
                            fill_price = ltp
                        _close_position(pp, inst_name, pos, trigger, fill_price, now, qty_i, is_futures)
                    else:
                        extra = ""
                        if is_futures:
                            pnl_rs = round(pts * qty_i, 2)
                            extra = f" · margin blocked Rs {pos.get('capital_blocked', 0):,.0f}"
                        else:
                            hours_held = max((now - dt.datetime.fromisoformat(pos["time"])).total_seconds() / 3600, 0)
                            live_premium = None
                            if OPT_MODE and "entry_premium" in pos:
                                opt_pts = round(pts*DELTA - hours_held*THETA_HR - SPREAD, 2)
                                live_premium = max(0.0, round(pos["entry_premium"] + opt_pts, 2))
                                pnl_rs = round((live_premium - pos["entry_premium"]) * qty_i, 2)
                            else:
                                pnl_rs = round(pts * qty_i, 2)
                            if live_premium is not None:
                                extra = (f" · Est. option value now: Rs {live_premium} (entry Rs {pos['entry_premium']}, "
                                         f"blocked Rs {pos.get('capital_blocked', 0):,.0f})")

                        c = st.columns(5)
                        c[0].metric("Direction", pos["dir"].capitalize())
                        c[1].metric("Entry", pos["entry"])
                        c[2].metric("LTP", ltp)
                        c[3].metric("P&L (pts)", f"{pts:+.2f}", delta=f"{pts:+.2f}")
                        c[4].metric("P&L (Rs)", f"{pnl_rs:+,.0f}", delta=f"{pnl_rs:+,.0f}")
                        st.caption(f"SL {pos['sl']} · Target {pos['target']} · filled {pos['time']}{extra}")

            elif pos["status"] == "pending_exit":
                st.caption(f"Order pending — exit. {pos['trigger']} triggered at {pos['trigger_time']}, "
                           "filling on next tick.")
                bull = pos["dir"] == "bullish"
                if is_futures:
                    bid, ask = get_bid_ask(exch, tok)
                    fill_price = (bid if bull else ask) or ltp
                else:
                    fill_price = ltp
                if fill_price is None:
                    st.warning("No live price yet — exit still pending.")
                else:
                    _close_position(pp, inst_name, pos, pos["trigger"], fill_price, now, qty_i, is_futures)

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
            tot = c.points.sum()
            realized = pp.get("balance", STARTING_CAPITAL) - STARTING_CAPITAL
            m = st.columns(5)
            m[0].metric("Trades", len(c))
            m[1].metric("Win rate", f"{100*(c.points>0).mean():.0f}%")
            m[2].metric("Gross", f"{tot:+.1f} pts")
            m[3].metric("Realized P&L", f"Rs {realized:+,.0f}", delta=f"{realized:+,.0f}")
            m[4].metric("Balance", f"Rs {pp.get('balance', STARTING_CAPITAL):,.0f}")
            cols_show = [x for x in ["instrument", "strategy", "dir", "type", "entry", "sl", "target",
                                      "exit", "exit_price", "exit_time", "points", "opt_points",
                                      "exit_premium", "real_cost", "pnl_rs"] if x in c.columns]
            color_cols = [x for x in ["points", "pnl_rs", "opt_points"] if x in cols_show]
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
            try:
                chart_df = fetch((now - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
                                  now.strftime("%Y-%m-%d %H:%M"), INTERVAL, tok, exch)
            except Exception as e:
                st.error(f"{inst_name}: broker call failed: {e}")
                continue

            if chart_df.empty or len(chart_df) < 3:
                continue

            sw, sig = get_signals(chart_df)
            use = sig if (sig.empty or SIGNAL == "both") else sig[sig.type == SIGNAL]
            if use.empty:
                continue
            last_sig = use.iloc[-1]
            is_fresh = last_sig.broken_i >= len(chart_df) - 2
            ts_sig = str(chart_df.iloc[-1].timestamp)
            seen = ({c.get("signal_ts") for c in pp["closed"] if c.get("instrument") == inst_name}
                    | {x.split("|", 1)[1] for x in pp["ignored"] if x.startswith(f"{inst_name}|")})
            if is_fresh and ts_sig not in seen:
                pp["open"][inst_name] = dict(status="pending_entry", signal_ts=ts_sig,
                                              instrument=inst_name, strategy=STRATEGY,
                                              dir=last_sig.direction,
                                              type=last_sig.type, sl=round(float(last_sig.Level), 2),
                                              placed_time=str(now))
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
    print("ERROR: tab_paper markers not found")
    raise SystemExit(1)
start_i = content.index(START)
end_i = content.index(END, start_i)
content = content[:start_i] + new_tab_paper + content[end_i:]

import shutil
shutil.copy(PATH, PATH + ".bak_crude_real2")

with open(PATH, "w") as f:
    f.write(content)

print("Patched (2/2) -- MCX now fills at real bid/ask with real margin, all instruments use correct per-instrument lot size.")
