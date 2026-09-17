PATH = "app.py"
START = "# ---------------------------------------------------------------- paper trading"
END = "# ---------------------------------------------------------------- chart"

with open(PATH) as f:
    content = f.read()

if START not in content or END not in content:
    print("ERROR: markers not found")
    raise SystemExit(1)

start_i = content.index(START)
end_i = content.index(END, start_i)

new_block = '''# ---------------------------------------------------------------- paper trading

with tab_paper:
    st.subheader("Paper trading — live")
    st.caption("Position monitoring, fills, and P&L use real-time WebSocket ticks "
               "(near-instant, no rate-limit risk). New-signal scanning uses REST "
               "candles on a slower cycle to stay well under the broker's rate limit. "
               "No real orders are sent. One position at a time.")

    top = st.columns([1, 1, 1, 1])
    live_on = top[0].toggle("Live", value=True, help="Turn off to pause both loops")
    REFRESH_SECONDS = top[1].number_input("Signal scan (sec)", 30, 600, 60, 15,
                                           help="How often to check for NEW signals via REST candles. Keep at 60+.")
    STARTING_CAPITAL = top[2].number_input("Paper capital (Rs)", 10000, 10000000, 100000, 5000,
                                            help="Virtual starting balance. Only applied after Reset.")
    if top[3].button("Reset paper account"):
        save_paper({"open": [], "closed": [], "ignored": [], "balance": STARTING_CAPITAL})
        st.rerun()

    if not OPT_MODE:
        st.info("Capital tracking (premium debit/credit) needs 'Simulate option buying' "
                "turned on in the sidebar. Off, P&L shows raw index points only.")

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

    @st.fragment(run_every=1 if live_on else None)
    def fast_panel():
        from zoneinfo import ZoneInfo
        pp = load_paper()
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        pos = pp["open"][0] if pp["open"] else None

        ts = tick_service()
        ts.ensure_subscribed(EXCH, TOKEN)
        ltp = ts.get_ltp(TOKEN)

        if OPT_MODE:
            balance = pp.get("balance", STARTING_CAPITAL)
            blocked = pos.get("capital_blocked", 0) if pos and pos.get("status") in ("open", "pending_exit") else 0
            b1, b2, b3 = st.columns(3)
            b1.metric("Available", f"Rs {balance:,.0f}")
            b2.metric("Blocked in trade", f"Rs {blocked:,.0f}")
            b3.metric("Total equity", f"Rs {balance + blocked:,.0f}")

        st.caption(f"Instrument: **{INST}** ({EXCH}) · Strategy: **{STRATEGY}** · Interval {INTERVAL}")

        if pos is None:
            feed = "\\U0001F7E2 tick feed live" if ltp is not None else "\\U0001F7E1 connecting to tick feed…"
            st.info(f"No open position — watching for a fresh {STRATEGY} signal… "
                    f"({feed}, LTP {ltp if ltp is not None else '—'})")
            st.caption(f"Checked {now:%H:%M:%S}" + ("" if live_on else " · paused"))
            return

        if pos["status"] == "pending_entry":
            st.markdown("### Order pending — entry")
            st.caption(f"{pos['dir'].capitalize()} {pos['type']} signal placed {pos['placed_time']}, "
                       "filling on next tick (simulates real order latency).")
            if ltp is None:
                st.warning("No live tick yet — entry still pending.")
            else:
                bull = pos["dir"] == "bullish"
                sl = pos["sl"]
                risk = (ltp - sl) if bull else (sl - ltp)
                if risk <= 0:
                    pp["ignored"].append(pos["signal_ts"])
                    pp["open"] = []
                    save_paper(pp)
                    st.warning("Entry cancelled — price moved past the stop before the order could fill.")
                else:
                    update = dict(status="open", entry=round(ltp, 2), time=str(now),
                                  target=round(ltp + RR*risk if bull else ltp - RR*risk, 2))
                    capital_blocked = 0
                    if OPT_MODE:
                        capital_blocked = round(PREMIUM * QTY, 2)
                        update.update(entry_premium=PREMIUM, capital_blocked=capital_blocked)
                        pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) - capital_blocked, 2)
                    pos.update(update)
                    save_paper(pp)
                    msg = f"Filled at {round(ltp, 2)}"
                    if OPT_MODE:
                        msg += f" · Rs {capital_blocked:,.0f} blocked"
                    st.success(msg)

        elif pos["status"] == "open":
            if ltp is None:
                st.warning("No live tick yet.")
            else:
                bull = pos["dir"] == "bullish"
                hit_sl = ltp <= pos["sl"] if bull else ltp >= pos["sl"]
                hit_tg = ltp >= pos["target"] if bull else ltp <= pos["target"]
                pts = round((ltp - pos["entry"]) if bull else (pos["entry"] - ltp), 2)

                sqoff = st.button("Square off now", key="manual_squareoff", type="secondary")

                if hit_sl or hit_tg or sqoff:
                    trigger = ("SL" if hit_sl else "Target") if (hit_sl or hit_tg) else "Manual"
                    pos.update(exit=trigger, exit_price=round(ltp, 2), exit_time=str(now), points=pts)
                    if OPT_MODE and "entry_premium" in pos:
                        hours_held = max((now - dt.datetime.fromisoformat(pos["time"])).total_seconds() / 3600, 0)
                        opt_pts = round(pts*DELTA - hours_held*THETA_HR - SPREAD, 2)
                        exit_premium = max(0.0, round(pos["entry_premium"] + opt_pts, 2))
                        proceeds = round(exit_premium * QTY, 2)
                        pos.update(opt_points=opt_pts, exit_premium=exit_premium, proceeds=proceeds,
                                   hours_held=round(hours_held, 2))
                        pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + proceeds, 2)
                    else:
                        pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + pts*QTY, 2)
                    pp["closed"].append(pos)
                    pp["open"] = []
                    save_paper(pp)
                    st.success(f"Position closed — {trigger} @ {round(ltp, 2)}")
                else:
                    hours_held = max((now - dt.datetime.fromisoformat(pos["time"])).total_seconds() / 3600, 0)
                    live_premium = None
                    if OPT_MODE and "entry_premium" in pos:
                        opt_pts = round(pts*DELTA - hours_held*THETA_HR - SPREAD, 2)
                        live_premium = max(0.0, round(pos["entry_premium"] + opt_pts, 2))
                        pnl_rs = round((live_premium - pos["entry_premium"]) * QTY, 2)
                    else:
                        pnl_rs = round(pts * QTY, 2)

                    st.markdown("### Open position")
                    c = st.columns(6)
                    c[0].metric("Instrument", pos.get("instrument", INST))
                    c[1].metric("Direction", pos["dir"].capitalize())
                    c[2].metric("Entry", pos["entry"])
                    c[3].metric("LTP", ltp)
                    c[4].metric("P&L (pts)", f"{pts:+.2f}", delta=f"{pts:+.2f}")
                    c[5].metric("P&L (Rs)", f"{pnl_rs:+,.0f}", delta=f"{pnl_rs:+,.0f}")
                    if live_premium is not None:
                        st.caption(f"SL {pos['sl']} · Target {pos['target']} · filled {pos['time']} · "
                                   f"Est. option value now: Rs {live_premium} "
                                   f"(entry Rs {pos['entry_premium']}, blocked Rs {pos.get('capital_blocked', 0):,.0f})")
                    else:
                        st.caption(f"SL {pos['sl']} · Target {pos['target']} · filled {pos['time']}")

        elif pos["status"] == "pending_exit":
            st.markdown("### Order pending — exit")
            st.caption(f"{pos['trigger']} triggered at {pos['trigger_time']}, filling on next tick.")
            if ltp is None:
                st.warning("No live tick yet — exit still pending.")
            else:
                bull = pos["dir"] == "bullish"
                pts = round((ltp - pos["entry"]) if bull else (pos["entry"] - ltp), 2)
                pos.update(exit=pos["trigger"], exit_price=round(ltp, 2), exit_time=str(now), points=pts)
                if OPT_MODE and "entry_premium" in pos:
                    hours_held = max((now - dt.datetime.fromisoformat(pos["time"])).total_seconds() / 3600, 0)
                    opt_pts = round(pts*DELTA - hours_held*THETA_HR - SPREAD, 2)
                    exit_premium = max(0.0, round(pos["entry_premium"] + opt_pts, 2))
                    proceeds = round(exit_premium * QTY, 2)
                    pos.update(opt_points=opt_pts, exit_premium=exit_premium, proceeds=proceeds,
                               hours_held=round(hours_held, 2))
                    pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + proceeds, 2)
                else:
                    pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + pts*QTY, 2)
                pp["closed"].append(pos)
                pp["open"] = []
                save_paper(pp)
                st.success(f"Exit filled — {pos['exit']} @ {round(ltp, 2)}")

        status_txt = "\\U0001F7E2 live tick" if ltp is not None else "\\U0001F7E1 waiting for tick"
        st.caption(f"{status_txt} · checked {now:%H:%M:%S}" + ("" if live_on else " · paused"))

    fast_panel()

    @st.fragment(run_every=REFRESH_SECONDS if live_on else None)
    def slow_panel():
        from zoneinfo import ZoneInfo
        pp = load_paper()
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)

        if pp["open"]:
            return

        try:
            chart_df = fetch((now - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
                              now.strftime("%Y-%m-%d %H:%M"), INTERVAL, TOKEN, EXCH)
        except Exception as e:
            st.error(f"Broker call failed: {e}")
            chart_df = pd.DataFrame()

        if chart_df.empty or len(chart_df) < 3:
            st.caption(f"Signal scan {now:%H:%M:%S}: not enough candle data yet.")
            return

        sw, sig = get_signals(chart_df)
        use = sig if (sig.empty or SIGNAL == "both") else sig[sig.type == SIGNAL]
        if not use.empty:
            last_sig = use.iloc[-1]
            is_fresh = last_sig.broken_i >= len(chart_df) - 2
            ts_sig = str(chart_df.iloc[-1].timestamp)
            seen = {c.get("signal_ts") for c in pp["closed"]} | set(pp["ignored"])
            if is_fresh and ts_sig not in seen:
                pp["open"] = [dict(status="pending_entry", signal_ts=ts_sig,
                                    instrument=INST, strategy=STRATEGY,
                                    dir=last_sig.direction,
                                    type=last_sig.type, sl=round(float(last_sig.Level), 2),
                                    placed_time=str(now))]
                save_paper(pp)
                st.rerun()

        st.caption(f"Signal scan {now:%H:%M:%S}" + ("" if live_on else " · paused"))

    slow_panel()

    st.markdown("**Closed trades**")
    pp = load_paper()
    if pp["closed"]:
        c = pd.DataFrame(pp["closed"])
        tot = c.points.sum()
        m = st.columns(5)
        m[0].metric("Trades", len(c))
        m[1].metric("Win rate", f"{100*(c.points>0).mean():.0f}%")
        m[2].metric("Gross", f"{tot:+.1f} pts")
        m[3].metric(f"Net @ {COST_PTS}", f"Rs {(tot-COST_PTS*len(c))*LOT:+,.0f}")
        m[4].metric("Balance", f"Rs {pp.get('balance', STARTING_CAPITAL):,.0f}")
        cols_show = [x for x in ["instrument", "strategy", "dir", "type", "entry", "sl", "target",
                                  "exit", "exit_price", "exit_time", "points", "opt_points",
                                  "exit_premium", "proceeds"] if x in c.columns]
        color_cols = [x for x in ["points", "opt_points", "proceeds"] if x in cols_show]
        try:
            styled = c[cols_show].style.map(_pnl_color, subset=color_cols)
        except AttributeError:
            styled = c[cols_show].style.applymap(_pnl_color, subset=color_cols)
        st.dataframe(styled, use_container_width=True)
    else:
        st.caption("No closed paper trades yet.")

'''

new_content = content[:start_i] + new_block + content[end_i:]

import shutil
shutil.copy(PATH, PATH + ".bak_livepnl")

with open(PATH, "w") as f:
    f.write(new_content)

print("Patched -- live tick-driven P&L, manual square-off, and green/red color coding added.")
