PATH = "app.py"

old1 = '''def load_paper():
    if os.path.exists(PAPER_FILE):
        d = json.load(open(PAPER_FILE))
        d.setdefault("ignored", [])
        return d
    return {"open": [], "closed": [], "ignored": []}'''

new1 = '''def load_paper():
    if os.path.exists(PAPER_FILE):
        d = json.load(open(PAPER_FILE))
        d.setdefault("ignored", [])
        d.setdefault("balance", STARTING_CAPITAL)
        return d
    return {"open": [], "closed": [], "ignored": [], "balance": STARTING_CAPITAL}'''

START = "# ---------------------------------------------------------------- paper trading"
END = "# ---------------------------------------------------------------- chart"

new_tab_paper = '''# ---------------------------------------------------------------- paper trading

with tab_paper:
    st.subheader("Paper trading — live")
    st.caption("Simulates a real broker order lifecycle: entries and exits are placed as "
               "pending and fill on the *next* check at the actual live price — not "
               "instantly at the signal price. No real orders are sent. One position at a time.")

    top = st.columns([1, 1, 1, 1])
    live_on = top[0].toggle("Live", value=True, help="Turn off to pause auto-refresh")
    REFRESH_SECONDS = top[1].number_input("Refresh (sec)", 30, 600, 60, 15,
                                           help="Keep this at 60+ to avoid broker rate limits.")
    STARTING_CAPITAL = top[2].number_input("Paper capital (Rs)", 10000, 10000000, 100000, 5000,
                                            help="Virtual starting balance. Only applied after Reset.")
    if top[3].button("Reset paper account"):
        save_paper({"open": [], "closed": [], "ignored": [], "balance": STARTING_CAPITAL})
        st.rerun()

    if not OPT_MODE:
        st.info("Capital tracking (premium debit/credit) needs 'Simulate option buying' "
                "turned on in the sidebar. Off, P&L shows raw index points only.")

    @st.fragment(run_every=REFRESH_SECONDS if live_on else None)
    def live_panel():
        from zoneinfo import ZoneInfo
        pp = load_paper()
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)

        st.caption(f"Instrument: **{INST}** ({EXCH}) · Strategy: **{STRATEGY}** · Interval {INTERVAL}")

        pos = pp["open"][0] if pp["open"] else None

        if OPT_MODE:
            balance = pp.get("balance", STARTING_CAPITAL)
            blocked = pos.get("capital_blocked", 0) if pos and pos.get("status") in ("open", "pending_exit") else 0
            b1, b2, b3 = st.columns(3)
            b1.metric("Available", f"Rs {balance:,.0f}")
            b2.metric("Blocked in trade", f"Rs {blocked:,.0f}")
            b3.metric("Total equity", f"Rs {balance + blocked:,.0f}")

        # ---- live price, for open-position P&L and order fills ----
        try:
            price_df = fetch((now - dt.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M"),
                              now.strftime("%Y-%m-%d %H:%M"), "ONE_MINUTE", TOKEN, EXCH)
            ltp = float(price_df.iloc[-1].close) if not price_df.empty else None
        except Exception as e:
            st.error(f"Broker call failed: {e}")
            ltp = None

        # ---- candles for the live chart AND signal scanning (one shared fetch) ----
        try:
            chart_df = fetch((now - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
                              now.strftime("%Y-%m-%d %H:%M"), INTERVAL, TOKEN, EXCH)
        except Exception as e:
            st.error(f"Broker call failed: {e}")
            chart_df = pd.DataFrame()

        sw, sig = get_signals(chart_df) if not chart_df.empty else (None, pd.DataFrame())

        if not chart_df.empty:
            chart_days = st.slider("Chart days shown", 1, 5, 1, key="live_chart_days")
            fig = chart(chart_df, sw, sig, chart_days, f"{INST} live · {STRATEGY}")
            if pos and pos.get("status") in ("open", "pending_exit") and "entry" in pos:
                fig.add_hline(y=pos["entry"], line_dash="dot", line_color="#3498db",
                              annotation_text="Entry", annotation_position="top left")
                fig.add_hline(y=pos["sl"], line_dash="dot", line_color="#c0392b",
                              annotation_text="SL", annotation_position="bottom left")
                fig.add_hline(y=pos["target"], line_dash="dot", line_color="#27ae60",
                              annotation_text="Target", annotation_position="top left")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Not enough candle data returned yet for the chart.")

        if pos is None:
            use = sig if (sig.empty or SIGNAL == "both") else sig[sig.type == SIGNAL]
            opened = False
            if not chart_df.empty and len(chart_df) >= 3 and not use.empty:
                last_sig = use.iloc[-1]
                is_fresh = last_sig.broken_i >= len(chart_df) - 2
                ts = str(chart_df.iloc[-1].timestamp)
                seen = {c.get("signal_ts") for c in pp["closed"]} | set(pp["ignored"])
                if is_fresh and ts not in seen:
                    pp["open"] = [dict(status="pending_entry", signal_ts=ts,
                                        instrument=INST, strategy=STRATEGY,
                                        dir=last_sig.direction,
                                        type=last_sig.type, sl=round(float(last_sig.Level), 2),
                                        placed_time=str(now))]
                    save_paper(pp)
                    opened = True
            if opened:
                st.rerun()
            else:
                st.info(f"No open position — watching for a fresh {STRATEGY} signal…")

        elif pos["status"] == "pending_entry":
            st.markdown("### Order pending — entry")
            st.caption(f"{pos['dir'].capitalize()} {pos['type']} signal placed {pos['placed_time']}, "
                       "filling on next check (simulates real order latency).")
            if ltp is None:
                st.warning("No live price yet — entry still pending.")
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
                st.warning("No live price data returned yet.")
            else:
                bull = pos["dir"] == "bullish"
                hit_sl = ltp <= pos["sl"] if bull else ltp >= pos["sl"]
                hit_tg = ltp >= pos["target"] if bull else ltp <= pos["target"]
                pts = round((ltp - pos["entry"]) if bull else (pos["entry"] - ltp), 2)

                if hit_sl or hit_tg:
                    pos.update(status="pending_exit", trigger="SL" if hit_sl else "Target",
                               trigger_time=str(now))
                    save_paper(pp)
                    st.warning(f"{pos['trigger']} triggered — exit order placed, filling on next check.")
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
                    c = st.columns(7)
                    c[0].metric("Instrument", pos.get("instrument", INST))
                    c[1].metric("Direction", pos["dir"].capitalize())
                    c[2].metric("Entry", pos["entry"])
                    c[3].metric("LTP", ltp)
                    c[4].metric("P&L (pts)", f"{pts:+.2f}")
                    c[5].metric("P&L (Rs)", f"{pnl_rs:+,.0f}")
                    c[6].metric("Type", pos["type"])
                    if live_premium is not None:
                        st.caption(f"SL {pos['sl']} · Target {pos['target']} · filled {pos['time']} · "
                                   f"Est. option value now: Rs {live_premium} "
                                   f"(entry Rs {pos['entry_premium']}, blocked Rs {pos.get('capital_blocked', 0):,.0f})")
                    else:
                        st.caption(f"SL {pos['sl']} · Target {pos['target']} · filled {pos['time']}")

        elif pos["status"] == "pending_exit":
            st.markdown("### Order pending — exit")
            st.caption(f"{pos['trigger']} triggered at {pos['trigger_time']}, filling on next check.")
            if ltp is None:
                st.warning("No live price yet — exit still pending.")
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

        st.caption(f"Last checked {now:%d %b %H:%M:%S}" + (" · live" if live_on else " · paused"))

        st.markdown("**Closed trades**")
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
            st.dataframe(c[cols_show], use_container_width=True)
        else:
            st.caption("No closed paper trades yet.")

    live_panel()

'''

with open(PATH) as f:
    content = f.read()

n1 = content.count(old1)
if n1 != 1:
    print(f"WARNING load_paper: expected 1 match, found {n1}. Aborting patch 1.")
    raise SystemExit(1)
content = content.replace(old1, new1)

if START not in content or END not in content:
    print("ERROR: could not find tab_paper markers")
    raise SystemExit(1)
start_i = content.index(START)
end_i = content.index(END, start_i)
content = content[:start_i] + new_tab_paper + content[end_i:]

with open(PATH + ".bak_capital", "w") as f:
    f.write(open(PATH + ".bak_capital", "w").name and "")  # placeholder, overwritten below
with open(PATH + ".bak_capital", "w") as f:
    pass
import shutil
shutil.copy(PATH, PATH + ".bak_capital")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- paper trading now tracks a real virtual balance.")
