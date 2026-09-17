PATH = "app.py"
START = "# ---------------------------------------------------------------- chart (search any instrument)"
END = "# ---------------------------------------------------------------- live"

with open(PATH) as f:
    content = f.read()

if START not in content or END not in content:
    print("ERROR: could not find markers")
    raise SystemExit(1)

start_i = content.index(START)
end_i = content.index(END, start_i)

new_block = '''# ---------------------------------------------------------------- chart (search any instrument)

with tab_chart:
    st.subheader("Chart")
    st.caption("Shows the sidebar's selected Instrument automatically. Use search below "
               "to look at a different instrument instead.")

    if st.session_state.get("chart_last_sidebar_inst") != INST:
        st.session_state.chart_sel = {"tradingsymbol": INST, "symboltoken": TOKEN, "exchange": EXCH}
        st.session_state.chart_last_sidebar_inst = INST

    if "chart_search_results" not in st.session_state:
        st.session_state.chart_search_results = []

    with st.expander("Search a different instrument"):
        sc1, sc2, sc3 = st.columns([1, 2, 1])
        search_exch = sc1.selectbox("Exchange", ["NSE", "NFO", "MCX", "BSE"], key="chart_search_exch")
        search_query = sc2.text_input("Search instrument", placeholder="e.g. RELIANCE, TCS",
                                       key="chart_search_query")
        sc3.markdown("<br>", unsafe_allow_html=True)
        if sc3.button("Search", type="primary", key="chart_search_btn"):
            if not search_query.strip():
                st.warning("Type something to search first.")
            else:
                try:
                    res = broker().searchScrip(search_exch, search_query.strip())
                    st.session_state.chart_search_results = res.get("data", []) if res.get("status") else []
                    if not st.session_state.chart_search_results:
                        st.warning("No matches found.")
                except Exception as e:
                    st.error(f"Search failed: {e}")
                    st.session_state.chart_search_results = []

        results = st.session_state.chart_search_results
        if results:
            options = {f"{r['tradingsymbol']}  ·  {r['exchange']}  ·  token {r['symboltoken']}": r
                       for r in results}
            picked = st.selectbox("Results", list(options), key="chart_search_pick")
            if st.button("Load this instead", key="chart_load_btn"):
                st.session_state.chart_sel = options[picked]
                st.rerun()

    sel = st.session_state.chart_sel
    st.divider()
    cc1, cc2, cc3 = st.columns([2, 1, 1])
    cc1.markdown(f"### {sel['tradingsymbol']} ({sel['exchange']})")
    chart_interval = cc2.selectbox("Interval",
        ["ONE_MINUTE", "THREE_MINUTE", "FIVE_MINUTE", "FIFTEEN_MINUTE"], 2,
        key="chart_interval")
    chart_live_on = cc3.toggle("Live", value=True, key="chart_live_toggle")
    chart_refresh_sec = st.number_input("Refresh (sec)", 30, 600, 60, 15, key="chart_refresh_sec")

    @st.fragment(run_every=chart_refresh_sec if chart_live_on else None)
    def live_chart_panel():
        from zoneinfo import ZoneInfo
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        sel = st.session_state.chart_sel
        try:
            df = fetch((now - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
                       now.strftime("%Y-%m-%d %H:%M"), chart_interval,
                       sel["symboltoken"], sel["exchange"])
        except Exception as e:
            st.error(f"Broker call failed: {e}")
            df = pd.DataFrame()

        if df.empty:
            st.warning("No candle data returned yet.")
        else:
            days = st.slider("Days shown", 1, 10, 2, key="chart_days_shown")
            empty_sig = pd.DataFrame(columns=["type", "direction", "broken_i", "Level"])
            fig = chart(df, None, empty_sig, days, f"{sel['tradingsymbol']} · {chart_interval}")
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Last checked {now:%d %b %H:%M:%S}" +
                       (" · live" if chart_live_on else " · paused"))

    live_chart_panel()

'''

new_content = content[:start_i] + new_block + content[end_i:]

with open(PATH + ".bak_chart", "w") as f:
    f.write(content)

with open(PATH, "w") as f:
    f.write(new_content)

print("Patched -- Chart tab now auto-syncs to the sidebar Instrument.")
