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
               "AngelOne-style charges are deducted per trade. No real orders are sent. "
               "One position per instrument, shared balance.")

    top = st.columns([1, 1, 1, 1])
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
                   f"@ Rs {round(exit_premium, 2)} · P&L Rs {pnl_rs:+,.0f}")

    @st.fragment(run_every=1 if live_on else None)
    def fast_panel():
        from zoneinfo import ZoneInfo
        pp = load_paper()
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        ts = tick_service()

        blocked_total = sum(p.get("capital_blocked", 0) for p in pp["open"].values()
                            if p.get("status") in ("open",))
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
            opt_cfg = get_option_config(inst_name)
            ts.ensure_subscribed(exch, tok)
            ltp = ts.get_ltp(tok)
            any_live = any_live or (ltp is not None)
            pos = pp["open"].get(inst_name)

            st.markdown(f"**{inst_name}**")

            if pos is None:
                feed = "\\U0001F7E2" if ltp is not None else "\\U0001F7E1"
                st.caption(f"{feed} No open position — watching for a fresh signal… "
                           f"Underlying LTP {ltp if ltp is not None else '—'}")
                continue

            if pos["status"] == "pending_entry":
                st.caption(f"Order pending — entry. {pos['dir'].capitalize()} {pos['type']} "
                           f"signal placed {pos['placed_time']}, finding the option & filling…")
                bull = pos["dir"] == "bullish"
                if ltp is None:
                    st.warning("No underlying live tick yet — entry still pending.")
                elif opt_cfg is None:
                    sl = pos["sl"]
                    risk = (ltp - sl) if bull else (sl - ltp)
                    if risk <= 0:
                        pp["ignored"].append(f"{inst_name}|{pos['signal_ts']}")
                        del pp["open"][inst_name]
                        save_paper(pp)
                        st.warning("Entry cancelled — price moved past the stop before the order could fill.")
                    else:
                        pos.update(status="open", mode="raw", entry=round(ltp, 2), time=str(now),
                                   target=round(ltp + RR*risk if bull else ltp - RR*risk, 2))
                        save_paper(pp)
                        st.success(f"Filled at {round(ltp, 2)} (raw underlying -- no option chain configured)")
                else:
                    prefix, search_exch, weekly_1letter = opt_cfg
                    chain = find_atm_option(prefix, search_exch, weekly_1letter, round(ltp/50)*50)
                    if chain is None:
                        st.warning("Couldn't look up the option chain yet -- retrying next cycle.")
                    else:
                        opt_token = chain["ce_token"] if bull else chain["pe_token"]
                        opt_symbol = chain["ce_symbol"] if bull else chain["pe_symbol"]
                        ts.ensure_subscribed(chain["exch"], opt_token)
                        bid, ask = get_bid_ask(chain["exch"], opt_token)
                        if ask is None:
                            st.warning(f"No live price yet for {opt_symbol} -- entry still pending.")
                        else:
                            sl = pos["sl"]
                            risk = (ltp - sl) if bull else (sl - ltp)
                            if risk <= 0:
                                pp["ignored"].append(f"{inst_name}|{pos['signal_ts']}")
                                del pp["open"][inst_name]
                                save_paper(pp)
                                st.warning("Entry cancelled -- underlying price moved past the stop before the order could fill.")
                            else:
                                target = round(ltp + RR*risk if bull else ltp - RR*risk, 2)
                                capital_blocked = round(ask * qty_i, 2)
                                pos.update(status="open", mode="option", entry=round(ask, 2),
                                           option_token=opt_token, option_symbol=opt_symbol,
                                           option_exch=chain["exch"], underlying_entry=round(ltp, 2),
                                           sl=sl, target=target, capital_blocked=capital_blocked,
                                           time=str(now))
                                pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) - capital_blocked, 2)
                                save_paper(pp)
                                st.success(f"Bought {opt_symbol} at Rs {round(ask, 2)} (real ask) "
                                           f"· Rs {capital_blocked:,.0f} blocked")

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
                            c = st.columns(5)
                            c[0].metric("Option", pos.get("option_symbol", "-"))
                            c[1].metric("Entry premium", pos["entry"])
                            c[2].metric("LTP", live_price if opt_ltp is not None else "—")
                            c[3].metric("P&L (pts)", f"{opt_pts:+.2f}", delta=f"{opt_pts:+.2f}")
                            c[4].metric("P&L (Rs)", f"{pnl_rs:+,.0f}", delta=f"{pnl_rs:+,.0f}")
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
            tot = c.points.sum()
            realized = pp.get("balance", STARTING_CAPITAL) - STARTING_CAPITAL
            m = st.columns(5)
            m[0].metric("Trades", len(c))
            m[1].metric("Win rate", f"{100*(c.points>0).mean():.0f}%")
            m[2].metric("Gross", f"{tot:+.1f} pts")
            m[3].metric("Realized P&L", f"Rs {realized:+,.0f}", delta=f"{realized:+,.0f}")
            m[4].metric("Balance", f"Rs {pp.get('balance', STARTING_CAPITAL):,.0f}")
            cols_show = [x for x in ["instrument", "strategy", "dir", "type", "option_symbol",
                                      "entry", "sl", "target", "exit", "exit_price", "exit_time",
                                      "points", "real_cost", "pnl_rs"] if x in c.columns]
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
shutil.copy(PATH, PATH + ".bak_unified4")

with open(PATH, "w") as f:
    f.write(content)

print("Patched (4/4) -- unified real-option paper trading is live across all instruments.")
