PATH = "app.py"

# ---- patch 1: add hilega_milega_signals() and update get_signals() ----
old1 = '''def orb_signals(df, or_bars=1):
    """Opening Range Breakout: the first `or_bars` candles of each trading day
    set the range (high/low). The first later candle whose CLOSE breaks beyond
    that range is the breakout signal for that day (one signal per day, first
    breakout only, classic ORB rule)."""
    d = df.copy()
    d["date"] = d["timestamp"].dt.date
    rows = []
    for day, g in d.groupby("date"):
        if len(g) <= or_bars:
            continue
        opening = g.iloc[:or_bars]
        or_high, or_low = float(opening["high"].max()), float(opening["low"].min())
        for idx, row in g.iloc[or_bars:].iterrows():
            if row["close"] > or_high:
                rows.append(dict(type="ORB", direction="bullish", broken_i=idx, Level=or_low))
                break
            elif row["close"] < or_low:
                rows.append(dict(type="ORB", direction="bearish", broken_i=idx, Level=or_high))
                break
    return pd.DataFrame(rows, columns=["type", "direction", "broken_i", "Level"])


def get_signals(df):
    """Dispatches to whichever strategy is selected in the sidebar."""
    if STRATEGY == "SMC BOS/CHoCH":
        return signals(df, SWING, CLOSE_BREAK)
    return None, orb_signals(df, OR_BARS)'''

new1 = '''def orb_signals(df, or_bars=1):
    """Opening Range Breakout: the first `or_bars` candles of each trading day
    set the range (high/low). The first later candle whose CLOSE breaks beyond
    that range is the breakout signal for that day (one signal per day, first
    breakout only, classic ORB rule)."""
    d = df.copy()
    d["date"] = d["timestamp"].dt.date
    rows = []
    for day, g in d.groupby("date"):
        if len(g) <= or_bars:
            continue
        opening = g.iloc[:or_bars]
        or_high, or_low = float(opening["high"].max()), float(opening["low"].min())
        for idx, row in g.iloc[or_bars:].iterrows():
            if row["close"] > or_high:
                rows.append(dict(type="ORB", direction="bullish", broken_i=idx, Level=or_low))
                break
            elif row["close"] < or_low:
                rows.append(dict(type="ORB", direction="bearish", broken_i=idx, Level=or_high))
                break
    return pd.DataFrame(rows, columns=["type", "direction", "broken_i", "Level"])


def _wilder_rsi(close, period):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _wma(series, period):
    weights = np.arange(1, period + 1)
    return series.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def hilega_milega_signals(df, rsi_period=9, wma_period=21):
    """Hilega Milega: RSI crossing its own WMA. Buy when RSI crosses above the
    WMA of RSI, sell when it crosses below. SL uses the signal candle's own
    low/high as a simple structural stop."""
    close = df["close"].astype(float)
    r = _wilder_rsi(close, rsi_period)
    w = _wma(r, wma_period)
    rows = []
    for i in range(1, len(df)):
        if pd.isna(r.iloc[i-1]) or pd.isna(w.iloc[i-1]) or pd.isna(r.iloc[i]) or pd.isna(w.iloc[i]):
            continue
        prev_diff = r.iloc[i-1] - w.iloc[i-1]
        curr_diff = r.iloc[i] - w.iloc[i]
        if prev_diff <= 0 and curr_diff > 0:
            rows.append(dict(type="HM", direction="bullish", broken_i=i, Level=float(df.loc[i, "low"])))
        elif prev_diff >= 0 and curr_diff < 0:
            rows.append(dict(type="HM", direction="bearish", broken_i=i, Level=float(df.loc[i, "high"])))
    return pd.DataFrame(rows, columns=["type", "direction", "broken_i", "Level"])


def get_signals(df):
    """Dispatches to whichever strategy is selected in the sidebar."""
    if STRATEGY == "SMC BOS/CHoCH":
        return signals(df, SWING, CLOSE_BREAK)
    if STRATEGY == "ORB 5-Min Breakout":
        return None, orb_signals(df, OR_BARS)
    return None, hilega_milega_signals(df, RSI_PERIOD, WMA_PERIOD)'''

# ---- patch 2: sidebar Strategy dropdown gets a third option ----
old2 = '''st.sidebar.header("Strategy")
STRATEGY = st.sidebar.selectbox("Strategy", ["SMC BOS/CHoCH", "ORB 5-Min Breakout"], index=0)

if STRATEGY == "SMC BOS/CHoCH":
    SWING = st.sidebar.slider("Swing length", 3, 60, 20, 1,
                               help="Candles either side defining a swing. Tune this on the CHART, not the P&L.")
    SIGNAL = st.sidebar.selectbox("Signal", ["BOS", "CHoCH", "both"], index=0)
    CLOSE_BREAK = st.sidebar.checkbox("Confirm break on close", True)
    OR_BARS = 1
else:
    OR_BARS = st.sidebar.number_input("Opening range candles", 1, 6, 1, 1,
                                       help="How many candles from the day's open define the range. "
                                            "1 candle = first 5 minutes on a 5-min chart (classic ORB).")
    SWING = 20
    SIGNAL = "both"
    CLOSE_BREAK = True'''

new2 = '''st.sidebar.header("Strategy")
STRATEGY = st.sidebar.selectbox("Strategy",
    ["SMC BOS/CHoCH", "ORB 5-Min Breakout", "Hilega Milega (RSI x WMA)"], index=0)

if STRATEGY == "SMC BOS/CHoCH":
    SWING = st.sidebar.slider("Swing length", 3, 60, 20, 1,
                               help="Candles either side defining a swing. Tune this on the CHART, not the P&L.")
    SIGNAL = st.sidebar.selectbox("Signal", ["BOS", "CHoCH", "both"], index=0)
    CLOSE_BREAK = st.sidebar.checkbox("Confirm break on close", True)
    OR_BARS, RSI_PERIOD, WMA_PERIOD = 1, 9, 21
elif STRATEGY == "ORB 5-Min Breakout":
    OR_BARS = st.sidebar.number_input("Opening range candles", 1, 6, 1, 1,
                                       help="How many candles from the day's open define the range. "
                                            "1 candle = first 5 minutes on a 5-min chart (classic ORB).")
    SWING, SIGNAL, CLOSE_BREAK = 20, "both", True
    RSI_PERIOD, WMA_PERIOD = 9, 21
else:
    RSI_PERIOD = st.sidebar.slider("RSI period", 3, 30, 9, 1)
    WMA_PERIOD = st.sidebar.slider("WMA period (on RSI)", 5, 50, 21, 1,
                                    help="Classic setup: RSI(9) crossing its own WMA(21). "
                                         "Buy on cross above, sell on cross below.")
    SWING, SIGNAL, OR_BARS, CLOSE_BREAK = 20, "both", 1, True'''

# ---- patch 3: backtest Structure info box gets a third branch ----
old3 = '''        st.subheader("Structure")
        if STRATEGY == "SMC BOS/CHoCH":
            st.info("Check this first. If the triangles aren't on the highs and lows "
                    "you'd pick by eye, change Swing length — the numbers below are "
                    "meaningless until the structure looks right.")
            chart_label = f"SWING_LENGTH={SWING}"
        else:
            st.info("Each day's opening range (first candle(s)) sets the breakout levels. "
                    "Check the annotated breakouts line up with real range breaks before "
                    "trusting the numbers below.")
            chart_label = f"ORB ({OR_BARS}-candle range)"'''

new3 = '''        st.subheader("Structure")
        if STRATEGY == "SMC BOS/CHoCH":
            st.info("Check this first. If the triangles aren't on the highs and lows "
                    "you'd pick by eye, change Swing length — the numbers below are "
                    "meaningless until the structure looks right.")
            chart_label = f"SWING_LENGTH={SWING}"
        elif STRATEGY == "ORB 5-Min Breakout":
            st.info("Each day's opening range (first candle(s)) sets the breakout levels. "
                    "Check the annotated breakouts line up with real range breaks before "
                    "trusting the numbers below.")
            chart_label = f"ORB ({OR_BARS}-candle range)"
        else:
            st.info("Signals fire when RSI crosses its own WMA. This is a lagging, "
                    "trend-following setup by nature — expect fewer, later signals "
                    "than SMC/ORB, and more whipsaws in a sideways/choppy market.")
            chart_label = f"RSI({RSI_PERIOD}) x WMA({WMA_PERIOD})"'''

with open(PATH) as f:
    content = f.read()

results = []
for i, (old, new) in enumerate([(old1, new1), (old2, new2), (old3, new3)], 1):
    n = content.count(old)
    results.append(n)
    if n != 1:
        print(f"WARNING patch {i}: expected 1 match, found {n}. Aborting all.")
        raise SystemExit(1)
    content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_hilegamilega")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- Hilega Milega (RSI x WMA) added as a third strategy option.")
