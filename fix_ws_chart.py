PATH = "app.py"

# ---- patch 1: insert TickService + bucketed candle cache after fetch() ----
old1 = '''    df = pd.concat(parts).drop_duplicates("timestamp")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)

# ---------------------------------------------------------------- strategies'''

new1 = '''    df = pd.concat(parts).drop_duplicates("timestamp")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)


@st.cache_resource
def tick_service():
    """Background WebSocket connection to AngelOne, giving real-time LTP ticks
    without touching the REST historical-data rate limit at all."""
    import threading, time as _time
    import pyotp
    from SmartApi import SmartConnect
    from SmartApi.smartWebSocketV2 import SmartWebSocketV2

    class TickService:
        def __init__(self):
            self.latest = {}
            self.subscribed = set()
            self.lock = threading.Lock()
            self.ready = False
            self.sws = None
            self._connect()

        def _connect(self):
            api_key = os.environ["ANGEL_API_KEY"]
            client_id = os.environ["ANGEL_CLIENT_ID"]
            o = SmartConnect(api_key=api_key)
            data = o.generateSession(client_id, os.environ["ANGEL_PASSWORD"],
                                      pyotp.TOTP(os.environ["ANGEL_TOTP"]).now())
            auth_token = data["data"]["jwtToken"]
            feed_token = o.getfeedToken()
            self.sws = SmartWebSocketV2(auth_token, api_key, client_id, feed_token,
                                         max_retry_attempt=5)

            def on_data(wsapp, message):
                token = message.get("token")
                ltp = message.get("last_traded_price")
                if token is not None and ltp is not None:
                    with self.lock:
                        self.latest[str(token)] = {"ltp": ltp / 100.0, "ts": _time.time()}

            def on_open(wsapp):
                self.ready = True

            def on_error(wsapp, error):
                pass

            def on_close(wsapp):
                self.ready = False

            self.sws.on_data = on_data
            self.sws.on_open = on_open
            self.sws.on_error = on_error
            self.sws.on_close = on_close
            threading.Thread(target=self.sws.connect, daemon=True).start()

        def ensure_subscribed(self, exch, token):
            key = (exch, str(token))
            if key in self.subscribed or not self.ready:
                return
            exch_map = {"NSE": 1, "NFO": 2, "BSE": 3, "MCX": 5}
            etype = exch_map.get(exch, 1)
            try:
                self.sws.subscribe("live_chart", 1, [{"exchangeType": etype, "tokens": [str(token)]}])
                self.subscribed.add(key)
            except Exception:
                pass

        def get_ltp(self, token):
            with self.lock:
                d = self.latest.get(str(token))
                return d["ltp"] if d else None

    return TickService()


@st.cache_data(ttl=35)
def get_bucketed_candles(token, exch, interval, bucket, days=2):
    """REST candle history, refetched at most every ~30s (via the bucket key)
    regardless of how often the caller runs -- keeps the fast tick-driven chart
    loop from ever hitting the historical-data rate limit."""
    from zoneinfo import ZoneInfo
    now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
    return fetch((now - dt.timedelta(days=days)).strftime("%Y-%m-%d %H:%M"),
                 now.strftime("%Y-%m-%d %H:%M"), interval, token, exch)

# ---------------------------------------------------------------- strategies'''

# ---- patch 2: replace the whole Chart tab with the WebSocket-powered version ----
START = "# ---------------------------------------------------------------- chart (search any instrument)"
END = "# ---------------------------------------------------------------- live"

new_tab_chart = '''# ---------------------------------------------------------------- chart (search any instrument)

with tab_chart:
    st.subheader("Chart")
    st.caption("Shows the sidebar's selected Instrument automatically, with real-time ticks "
               "over WebSocket. Use search below to look at a different instrument instead.")

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

    @st.fragment(run_every=1.5 if chart_live_on else None)
    def live_chart_panel():
        import json as _json, time as _time
        sel = st.session_state.chart_sel
        ts = tick_service()
        ts.ensure_subscribed(sel["exchange"], sel["symboltoken"])

        bucket = int(_time.time() // 30)
        try:
            df = get_bucketed_candles(sel["symboltoken"], sel["exchange"], chart_interval, bucket)
        except Exception as e:
            st.error(f"Broker call failed: {e}")
            df = pd.DataFrame()

        if df.empty:
            st.warning("No candle data returned yet.")
            return

        days = st.slider("Days shown", 1, 10, 2, key="chart_days_shown")
        m = df.timestamp >= df.timestamp.max() - pd.Timedelta(days=days)
        r = df[m].copy()

        ltp = ts.get_ltp(sel["symboltoken"])
        if ltp is not None and len(r) > 0:
            i = r.index[-1]
            r.loc[i, "close"] = ltp
            r.loc[i, "high"] = max(r.loc[i, "high"], ltp)
            r.loc[i, "low"] = min(r.loc[i, "low"], ltp)

        candles = [
            dict(time=int(row.timestamp.timestamp()) + 19800,
                 open=round(float(row.open), 2), high=round(float(row.high), 2),
                 low=round(float(row.low), 2), close=round(float(row.close), 2))
            for _, row in r.iterrows()
        ]
        candles_json = _json.dumps(candles)
        html = f"""
        <div id="tv_chart" style="height:560px;"></div>
        <script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
        <script>
          const el = document.getElementById('tv_chart');
          const chart = LightweightCharts.createChart(el, {{
            width: el.clientWidth,
            height: 560,
            layout: {{ background: {{ color: '#131722' }}, textColor: '#d1d4dc' }},
            grid: {{ vertLines: {{ color: '#1e222d' }}, horzLines: {{ color: '#1e222d' }} }},
            timeScale: {{ timeVisible: true, secondsVisible: false, borderColor: '#2a2e39' }},
            rightPriceScale: {{ borderColor: '#2a2e39' }},
            crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
          }});
          const series = chart.addCandlestickSeries({{
            upColor: '#26a69a', downColor: '#ef5350', borderVisible: false,
            wickUpColor: '#26a69a', wickDownColor: '#ef5350',
          }});
          series.setData({candles_json});
          chart.timeScale().fitContent();
          window.addEventListener('resize', () => {{
            chart.applyOptions({{ width: el.clientWidth }});
          }});
        </script>
        """
        components.html(html, height=580)

        status = "\\U0001F7E2 live tick" if ltp is not None else "\\U0001F7E1 waiting for first tick…"
        st.caption(f"{sel['tradingsymbol']} · {chart_interval} · {status}" +
                   (f" · LTP {ltp}" if ltp is not None else "") +
                   (" · paused" if not chart_live_on else ""))

    live_chart_panel()

'''

with open(PATH) as f:
    content = f.read()

n1 = content.count(old1)
if n1 != 1:
    print(f"WARNING patch 1: expected 1 match, found {n1}. Aborting.")
    raise SystemExit(1)
content = content.replace(old1, new1)

if START not in content or END not in content:
    print("ERROR: chart tab markers not found")
    raise SystemExit(1)
start_i = content.index(START)
end_i = content.index(END, start_i)
content = content[:start_i] + new_tab_chart + content[end_i:]

import shutil
shutil.copy(PATH, PATH + ".bak_wschart")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- Chart tab now uses a real WebSocket tick feed.")
