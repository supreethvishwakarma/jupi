import sys

PATH = "app.py"
START = "with tab_paper:"
END = "with tab_live:"

with open(PATH) as f:
    content = f.read()

if START not in content or END not in content:
    print("ERROR: could not find markers in app.py -- has the file changed since you last saw it?")
    sys.exit(1)

start_i = content.index(START)
end_i = content.index(END, start_i)

new_block = """with tab_paper:
    st.subheader("Paper trading — live")
    st.caption("Simulated fills against live market data, refreshed automatically. "
               "No real orders are sent. Only one position open at a time.")

    top = st.columns([1, 1, 2])
    live_on = top[0].toggle("Live", value=True, help="Turn off to pause auto-refresh")
    REFRESH_SECONDS = top[1].number_input("Refresh (sec)", 15, 600, 60, 15)
    if top[2].button("Reset paper account"):
        save_paper({"open": [], "closed": []})
        st.rerun()

    @st.fragment(run_every=REFRESH_SECONDS if live_on else None)
    def live_panel():
        pp = load_paper()
        now = dt.datetime.now()
        status = st.empty()

        if pp["open"]:
            p = pp["open"][0]
            df = fetch((now - dt.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M"),
                       now.strftime("%Y-%m-%d %H:%M"), "ONE_MINUTE", TOKEN, EXCH)
            if df.empty:
                status.warning("No live candle data returned yet — market may be closed.")
            else:
                ltp = float(df.iloc[-1].close)
                bull = p["dir"] == "bullish"
                hit_sl = ltp <= p["sl"] if bull else ltp >= p["sl"]
                hit_tg = ltp >= p["target"] if bull else ltp <= p["target"]
                pts = round((ltp - p["entry"]) if bull else (p["entry"] - ltp), 2)

                if hit_sl or hit_tg:
                    exit_px = p["sl"] if hit_sl else p["target"]
                    p.update(exit="SL" if hit_sl else "Target", exit_price=exit_px,
                             exit_time=str(now),
                             points=round((exit_px - p["entry"]) if bull else (p["entry"] - exit_px), 2))
                    pp["closed"].append(p)
                    pp["open"] = []
                    save_paper(pp)
                    st.success(f"Position closed — {p['exit']} @ {exit_px}")
                else:
                    st.markdown("### Open position")
                    c = st.columns(6)
                    c[0].metric("Direction", p["dir"].capitalize())
                    c[1].metric("Entry", p["entry"])
                    c[2].metric("LTP", ltp)
                    c[3].metric("P&L (pts)", f"{pts:+.2f}")
                    c[4].metric("P&L (Rs)", f"{pts*QTY:+,.0f}")
                    c[5].metric("Type", p["type"])
                    st.caption(f"SL {p['sl']} · Target {p['target']} · opened {p['time']}")
        else:
            df = fetch((now - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
                       now.strftime("%Y-%m-%d %H:%M"), INTERVAL, TOKEN, EXCH)
            if df.empty:
                status.warning("No candle data returned.")
            else:
                sw, sig = signals(df, SWING, CLOSE_BREAK)
                use = sig if SIGNAL == "both" else sig[sig.type == SIGNAL]
                known = {c["time"] for c in pp["closed"]}
                opened = False
                for _, e in use.iterrows():
                    i = e.broken_i + 1
                    if i >= len(df):
                        continue
                    ts = str(df.loc[i, "timestamp"])
                    if ts in known:
                        continue
                    entry, bull, sl = df.loc[i, "open"], e.direction == "bullish", e.Level
                    risk = (entry - sl) if bull else (sl - entry)
                    if risk <= 0:
                        continue
                    pp["open"] = [dict(time=ts, dir=e.direction, type=e.type,
                                        entry=round(entry, 2), sl=round(sl, 2),
                                        target=round(entry + RR*risk if bull else entry - RR*risk, 2))]
                    save_paper(pp)
                    opened = True
                    break
                if opened:
                    st.rerun(scope="fragment")
                else:
                    st.info("No open position — watching for a new BOS/CHoCH signal…")

        status.caption(f"Last checked {now:%d %b %H:%M:%S}" + (" · live" if live_on else " · paused"))

    live_panel()

    st.markdown("**Closed trades**")
    pp = load_paper()
    if pp["closed"]:
        c = pd.DataFrame(pp["closed"])
        tot = c.points.sum()
        m = st.columns(4)
        m[0].metric("Trades", len(c))
        m[1].metric("Win rate", f"{100*(c.points>0).mean():.0f}%")
        m[2].metric("Gross", f"{tot:+.1f} pts")
        m[3].metric(f"Net @ {COST_PTS}", f"Rs {(tot-COST_PTS*len(c))*LOT:+,.0f}")
        st.dataframe(c, use_container_width=True)
    else:
        st.caption("No closed paper trades yet.")

"""

new_content = content[:start_i] + new_block + content[end_i:]

with open(PATH + ".bak", "w") as f:
    f.write(content)

with open(PATH, "w") as f:
    f.write(new_content)

print("Done — app.py updated. Original saved as app.py.bak")
