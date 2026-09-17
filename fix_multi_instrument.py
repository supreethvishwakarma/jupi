PATH = "app.py"

# ---- patch 1: add real_options_cost() after get_signals() ----
old1 = '''def get_signals(df):
    """Dispatches to whichever strategy is selected in the sidebar."""
    if STRATEGY == "SMC BOS/CHoCH":
        return signals(df, SWING, CLOSE_BREAK)
    if STRATEGY == "ORB 5-Min Breakout":
        return None, orb_signals(df, OR_BARS)
    return None, hilega_milega_signals(df, RSI_PERIOD, WMA_PERIOD)'''

new1 = '''def get_signals(df):
    """Dispatches to whichever strategy is selected in the sidebar."""
    if STRATEGY == "SMC BOS/CHoCH":
        return signals(df, SWING, CLOSE_BREAK)
    if STRATEGY == "ORB 5-Min Breakout":
        return None, orb_signals(df, OR_BARS)
    return None, hilega_milega_signals(df, RSI_PERIOD, WMA_PERIOD)


def real_options_cost(entry_premium, exit_premium, qty):
    """Approximate round-trip AngelOne F&O charges for one options leg (buy then
    sell): flat brokerage, options STT (sell side only), NSE exchange transaction
    charge, SEBI turnover fee, stamp duty (buy side only), and GST on the taxable
    pieces -- based on Angel One's published rates. An estimate, not your exact
    contract note; these government/exchange rates do get revised periodically."""
    buy_value = entry_premium * qty
    sell_value = exit_premium * qty
    brokerage = 20 + 20  # flat Rs 20 per executed order, buy + sell
    stt = 0.001 * sell_value  # options STT: sell side only, 0.1%
    exch_charge = 0.0003503 * (buy_value + sell_value)  # NSE F&O options, both sides
    sebi_charge = 0.000001 * (buy_value + sell_value)  # SEBI turnover fee, both sides
    stamp_duty = 0.00003 * buy_value  # stamp duty, buy side only, 0.003%
    gst = 0.18 * (brokerage + exch_charge + sebi_charge)  # GST on brokerage+exchange+SEBI only
    return round(brokerage + stt + exch_charge + sebi_charge + stamp_duty + gst, 2)'''

# ---- patch 2: load_paper() -- open becomes a dict keyed by instrument ----
old2 = '''def load_paper():
    if os.path.exists(PAPER_FILE):
        d = json.load(open(PAPER_FILE))
        d.setdefault("ignored", [])
        d.setdefault("balance", STARTING_CAPITAL)
        return d
    return {"open": [], "closed": [], "ignored": [], "balance": STARTING_CAPITAL}'''

new2 = '''def load_paper():
    if os.path.exists(PAPER_FILE):
        d = json.load(open(PAPER_FILE))
        if not isinstance(d.get("open"), dict):
            d["open"] = {}  # migrate from the older single-position list format
        d.setdefault("closed", [])
        d.setdefault("ignored", [])
        d.setdefault("balance", STARTING_CAPITAL)
        return d
    return {"open": {}, "closed": [], "ignored": [], "balance": STARTING_CAPITAL}'''

# ---- patch 3: sidebar gets a multi-instrument selector ----
old3 = '''INST = st.sidebar.selectbox("Instrument", list(INSTRUMENTS))
TOKEN, EXCH, LOT = INSTRUMENTS[INST]

if EXCH == "MCX":'''

new3 = '''INST = st.sidebar.selectbox("Instrument", list(INSTRUMENTS))
TOKEN, EXCH, LOT = INSTRUMENTS[INST]

PAPER_INSTRUMENTS = st.sidebar.multiselect(
    "Paper trade these instruments", list(INSTRUMENTS), default=[INST],
    help="Runs the same Strategy on each selected instrument in parallel, "
         "sharing one paper trading balance.")
if not PAPER_INSTRUMENTS:
    PAPER_INSTRUMENTS = [INST]

if EXCH == "MCX":'''

# ---- patch 4: full replacement of the Paper trading tab for multi-instrument ----
START = "# ---------------------------------------------------------------- paper trading"
END = "# ---------------------------------------------------------------- chart"

new_tab_paper = '''# ---------------------------------------------------------------- paper trading

with tab_paper:
    st.subheader("Paper trading — live")
    st.caption("Position monitoring, fills, and P&L use real-time WebSocket ticks. "
               "New-signal scanning uses REST candles on a slower cycle. Real "
               "AngelOne-style charges (brokerage, STT, exchange, SEBI, stamp duty, "
               "GST) are deducted per trade. No real orders are sent. One position "
               "per instrument at a time, all sharing one balance.")

    top = st.columns([1, 1, 1, 1])
    live_on = top[0].toggle("Live", value=True, help="Turn off to pause both loops")
    REFRESH_SECONDS = top[1].number_input("Signal scan (sec)", 30, 600, 60, 15,
                                           help="How often to check for NEW signals via REST candles. Keep at 60+.")
    STARTING_CAPITAL = top[2].number_input("Paper capital (Rs)", 10000, 10000000, 100000, 5000,
                                            help="Virtual starting balance. Only applied after Reset.")
    if top[3].button("Reset paper account"):
        save_paper({"open": {}, "closed": [], "ignored": [], "balance": STARTING_CAPITAL})
        st.rerun()

    if not OPT_MODE:
        st.info("Capital tracking (premium debit/credit, real charges) needs 'Simulate "
                "option buying' turned on in the sidebar. Off, P&L shows raw index points only.")

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

    def _close_position(pp, inst_name, pos, trigger, ltp, now):
        bull = pos["dir"] == "bullish"
        pts = round((ltp - pos["entry"]) if bull else (pos["entry"] - ltp), 2)
        pos.update(exit=trigger, exit_price=round(ltp, 2), exit_time=str(now), points=pts)
        if OPT_MODE and "entry_premium" in pos:
            hours_held = max((now - dt.datetime.fromisoformat(pos["time"])).total_seconds() / 3600, 0)
            opt_pts = round(pts*DELTA - hours_held*THETA_HR - SPREAD, 2)
            exit_premium = max(0.0, round(pos["entry_premium"] + opt_pts, 2))
            cost = real_options_cost(pos["entry_premium"], exit_premium, QTY)
            proceeds = round(exit_premium * QTY - cost, 2)
            pos.update(opt_points=opt_pts, exit_premium=exit_premium, proceeds=proceeds,
                       real_cost=cost, hours_held=round(hours_held, 2))
            pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + proceeds, 2)
        else:
            pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + pts*QTY, 2)
        pp["closed"].append(pos)
        del pp["open"][inst_name]
        save_paper(pp)
        st.success(f"{inst_name}: closed — {trigger} @ {round(ltp, 2)}")

    @st.fragment(run_every=1 if live_on else None)
    def fast_panel():
        from zoneinfo import ZoneInfo
        pp = load_paper()
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        ts = tick_service()

        if OPT_MODE:
            balance = pp.get("balance", STARTING_CAPITAL)
            blocked = sum(p.get("capital_blocked", 0) for p in pp["open"].values()
                          if p.get("status") in ("open", "pending_exit"))
            b1, b2, b3 = st.columns(3)
            b1.metric("Available", f"Rs {balance:,.0f}")
            b2.metric("Blocked in trades", f"Rs {blocked:,.0f}")
            b3.metric("Total equity", f"Rs {balance + blocked:,.0f}")

        st.caption(f"Strategy: **{STRATEGY}** · Instruments: **{', '.join(PAPER_INSTRUMENTS)}**")

        any_live = False
        for inst_name in PAPER_INSTRUMENTS:
            tok, exch, _ = INSTRUMENTS[inst_name]
            ts.ensure_subscribed(exch, tok)
            ltp = ts.get_ltp(tok)
            any_live = any_live or (ltp is not None)
            pos = pp["open"].get(inst_name)

            st.markdown(f"**{inst_name}**")

            if pos is None:
                feed = "\\U0001F7E2" if ltp is not None else "\\U0001F7E1"
                st.caption(f"{feed} No open position — watching for a fresh signal… "
                           f"LTP {ltp if ltp is not None else '—'}")
                continue

            if pos["status"] == "pending_entry":
                st.caption(f"Order pending — entry. {pos['dir'].capitalize()} {pos['type']} "
                           f"signal placed {pos['placed_time']}, filling on next tick.")
                if ltp is None:
                    st.warning("No live tick yet — entry still pending.")
                else:
                    bull = pos["dir"] == "bullish"
                    sl = pos["sl"]
                    risk = (ltp - sl) if bull else (sl - ltp)
                    if risk <= 0:
                        pp["ignored"].append(f"{inst_name}|{pos['signal_ts']}")
                        del pp["open"][inst_name]
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

                    sqoff = st.button(f"Square off {inst_name}", key=f"sqoff_{inst_name}")

                    if hit_sl or hit_tg or sqoff:
                        trigger = ("SL" if hit_sl else "Target") if (hit_sl or hit_tg) else "Manual"
                        _close_position(pp, inst_name, pos, trigger, ltp, now)
                    else:
                        hours_held = max((now - dt.datetime.fromisoformat(pos["time"])).total_seconds() / 3600, 0)
                        live_premium = None
                        if OPT_MODE and "entry_premium" in pos:
                            opt_pts = round(pts*DELTA - hours_held*THETA_HR - SPREAD, 2)
                            live_premium = max(0.0, round(pos["entry_premium"] + opt_pts, 2))
                            pnl_rs = round((live_premium - pos["entry_premium"]) * QTY, 2)
                        else:
                            pnl_rs = round(pts * QTY, 2)

                        c = st.columns(5)
                        c[0].metric("Direction", pos["dir"].capitalize())
                        c[1].metric("Entry", pos["entry"])
                        c[2].metric("LTP", ltp)
                        c[3].metric("P&L (pts)", f"{pts:+.2f}", delta=f"{pts:+.2f}")
                        c[4].metric("P&L (Rs)", f"{pnl_rs:+,.0f}", delta=f"{pnl_rs:+,.0f}")
                        if live_premium is not None:
                            st.caption(f"SL {pos['sl']} · Target {pos['target']} · filled {pos['time']} · "
                                       f"Est. option value now: Rs {live_premium} "
                                       f"(entry Rs {pos['entry_premium']}, blocked Rs {pos.get('capital_blocked', 0):,.0f})")
                        else:
                            st.caption(f"SL {pos['sl']} · Target {pos['target']} · filled {pos['time']}")

            elif pos["status"] == "pending_exit":
                st.caption(f"Order pending — exit. {pos['trigger']} triggered at {pos['trigger_time']}, "
                           "filling on next tick.")
                if ltp is None:
                    st.warning("No live tick yet — exit still pending.")
                else:
                    _close_position(pp, inst_name, pos, pos["trigger"], ltp, now)

        status_txt = "\\U0001F7E2 ticks live" if any_live else "\\U0001F7E1 waiting for ticks"
        st.caption(f"{status_txt} · checked {now:%H:%M:%S}" + ("" if live_on else " · paused"))

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

    st.markdown("**Closed trades**")
    pp = load_paper()
    if pp["closed"]:
        c = pd.DataFrame(pp["closed"])
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
                                  "exit_premium", "real_cost", "proceeds"] if x in c.columns]
        color_cols = [x for x in ["points", "opt_points", "proceeds"] if x in cols_show]
        try:
            styled = c[cols_show].style.map(_pnl_color, subset=color_cols)
        except AttributeError:
            styled = c[cols_show].style.applymap(_pnl_color, subset=color_cols)
        st.dataframe(styled, use_container_width=True)
    else:
        st.caption("No closed paper trades yet.")

'''

with open(PATH) as f:
    content = f.read()

n1, n2, n3 = content.count(old1), content.count(old2), content.count(old3)
if n1 != 1 or n2 != 1 or n3 != 1:
    print(f"WARNING: expected 1 match each for patches 1-3, found {n1}, {n2}, {n3}. Aborting.")
    raise SystemExit(1)
content = content.replace(old1, new1).replace(old2, new2).replace(old3, new3)

if START not in content or END not in content:
    print("ERROR: tab_paper markers not found")
    raise SystemExit(1)
start_i = content.index(START)
end_i = content.index(END, start_i)
content = content[:start_i] + new_tab_paper + content[end_i:]

import shutil
shutil.copy(PATH, PATH + ".bak_multiinst")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- real costs + parallel multi-instrument paper trading added.")
