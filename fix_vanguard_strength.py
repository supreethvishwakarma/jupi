PATH = "app.py"

old1 = '''def hilega_milega_signals(df, rsi_period=9, wma_period=21):
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
    return pd.DataFrame(rows, columns=["type", "direction", "broken_i", "Level"])'''

new1 = '''def hilega_milega_signals(df, rsi_period=9, wma_period=21, min_gap=0.0):
    """Hilega Milega: RSI crossing its own WMA. Buy when RSI crosses above the
    WMA of RSI, sell when it crosses below -- and, once past it, has moved at
    least min_gap further, to filter out marginal, whipsaw-prone crosses that
    barely nudge over the line. SL uses the signal candle's own low/high as a
    simple structural stop."""
    close = df["close"].astype(float)
    r = _wilder_rsi(close, rsi_period)
    w = _wma(r, wma_period)
    rows = []
    for i in range(1, len(df)):
        if pd.isna(r.iloc[i-1]) or pd.isna(w.iloc[i-1]) or pd.isna(r.iloc[i]) or pd.isna(w.iloc[i]):
            continue
        prev_diff = r.iloc[i-1] - w.iloc[i-1]
        curr_diff = r.iloc[i] - w.iloc[i]
        if prev_diff <= 0 and curr_diff > min_gap:
            rows.append(dict(type="HM", direction="bullish", broken_i=i, Level=float(df.loc[i, "low"])))
        elif prev_diff >= 0 and curr_diff < -min_gap:
            rows.append(dict(type="HM", direction="bearish", broken_i=i, Level=float(df.loc[i, "high"])))
    return pd.DataFrame(rows, columns=["type", "direction", "broken_i", "Level"])'''

old2 = '''def get_signals(df):
    """Dispatches to whichever strategy is selected in the sidebar."""
    if STRATEGY == "Vanguard (RSI x WMA)":
        return None, hilega_milega_signals(df, RSI_PERIOD, WMA_PERIOD)
    if STRATEGY == "Scalping (EMA+VWAP+RSI)":
        return None, scalp_signals(df, EMA_PERIOD, SCALP_RSI_PERIOD)
    return None, supertrend_signals(df, ST_PERIOD, ST_MULT)'''

new2 = '''def get_signals(df):
    """Dispatches to whichever strategy is selected in the sidebar."""
    if STRATEGY == "Vanguard (RSI x WMA)":
        return None, hilega_milega_signals(df, RSI_PERIOD, WMA_PERIOD, MIN_GAP)
    if STRATEGY == "Scalping (EMA+VWAP+RSI)":
        return None, scalp_signals(df, EMA_PERIOD, SCALP_RSI_PERIOD)
    return None, supertrend_signals(df, ST_PERIOD, ST_MULT)'''

old3 = '''if STRATEGY == "Vanguard (RSI x WMA)":
    RSI_PERIOD = st.sidebar.slider("RSI period", 3, 30, 9, 1)
    WMA_PERIOD = st.sidebar.slider("WMA period (on RSI)", 5, 50, 21, 1,
                                    help="Classic setup: RSI(9) crossing its own WMA(21). "
                                         "Buy on cross above, sell on cross below.")
    ST_PERIOD, ST_MULT, EMA_PERIOD, SCALP_RSI_PERIOD = 7, 2.5, 9, 14
elif STRATEGY == "Scalping (EMA+VWAP+RSI)":'''

new3 = '''if STRATEGY == "Vanguard (RSI x WMA)":
    RSI_PERIOD = st.sidebar.slider("RSI period", 3, 30, 9, 1)
    WMA_PERIOD = st.sidebar.slider("WMA period (on RSI)", 5, 50, 21, 1,
                                    help="Classic setup: RSI(9) crossing its own WMA(21). "
                                         "Buy on cross above, sell on cross below.")
    MIN_GAP = st.sidebar.slider("Minimum signal strength (RSI-WMA gap)", 0.0, 15.0, 3.0, 0.5,
                                 help="Requires RSI to be at least this far past its WMA at the "
                                      "crossing candle -- filters out marginal, whipsaw-prone "
                                      "crosses. Higher = fewer, more decisive signals. 0 = off "
                                      "(any cross counts, original behavior).")
    ST_PERIOD, ST_MULT, EMA_PERIOD, SCALP_RSI_PERIOD = 7, 2.5, 9, 14
elif STRATEGY == "Scalping (EMA+VWAP+RSI)":
    MIN_GAP = 0.0'''

with open(PATH, encoding="utf-8") as f:
    content = f.read()

results = []
for i, (old, new) in enumerate([(old1, new1), (old2, new2), (old3, new3)], 1):
    n = content.count(old)
    results.append(n)
    if n != 1:
        print(f"WARNING patch {i}: expected 1 match, found {n}. Aborting.")
        raise SystemExit(1)
    content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_vanguardstrength")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched -- Vanguard now has a Minimum Signal Strength filter (RSI-WMA gap).")
