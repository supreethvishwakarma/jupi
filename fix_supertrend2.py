PATH = "app.py"

old1 = '''st.sidebar.header("Strategy")
STRATEGY = st.sidebar.selectbox("Strategy",
    ["SMC BOS/CHoCH", "ORB 5-Min Breakout", "Vanguard (RSI x WMA)"], index=0)

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
    SWING, SIGNAL, OR_BARS, CLOSE_BREAK = 20, "both", 1, True

RR = st.sidebar.slider("Risk : Reward", 0.5, 5.0, 2.0, 0.5)'''

new1 = '''st.sidebar.header("Strategy")
STRATEGY = st.sidebar.selectbox("Strategy",
    ["SMC BOS/CHoCH", "ORB 5-Min Breakout", "Vanguard (RSI x WMA)", "Supertrend (Trailing SL)"], index=0)

if STRATEGY == "SMC BOS/CHoCH":
    SWING = st.sidebar.slider("Swing length", 3, 60, 20, 1,
                               help="Candles either side defining a swing. Tune this on the CHART, not the P&L.")
    SIGNAL = st.sidebar.selectbox("Signal", ["BOS", "CHoCH", "both"], index=0)
    CLOSE_BREAK = st.sidebar.checkbox("Confirm break on close", True)
    OR_BARS, RSI_PERIOD, WMA_PERIOD, ST_PERIOD, ST_MULT = 1, 9, 21, 7, 2.5
elif STRATEGY == "ORB 5-Min Breakout":
    OR_BARS = st.sidebar.number_input("Opening range candles", 1, 6, 1, 1,
                                       help="How many candles from the day's open define the range. "
                                            "1 candle = first 5 minutes on a 5-min chart (classic ORB).")
    SWING, SIGNAL, CLOSE_BREAK = 20, "both", True
    RSI_PERIOD, WMA_PERIOD, ST_PERIOD, ST_MULT = 9, 21, 7, 2.5
elif STRATEGY == "Vanguard (RSI x WMA)":
    RSI_PERIOD = st.sidebar.slider("RSI period", 3, 30, 9, 1)
    WMA_PERIOD = st.sidebar.slider("WMA period (on RSI)", 5, 50, 21, 1,
                                    help="Classic setup: RSI(9) crossing its own WMA(21). "
                                         "Buy on cross above, sell on cross below.")
    SWING, SIGNAL, OR_BARS, CLOSE_BREAK = 20, "both", 1, True
    ST_PERIOD, ST_MULT = 7, 2.5
else:
    ST_PERIOD = st.sidebar.slider("ATR period", 5, 21, 7, 1,
                                   help="Lower = more responsive (scalping). Classic default is 10; "
                                        "7 is a common scalping tune.")
    ST_MULT = st.sidebar.slider("ATR multiplier", 1.0, 5.0, 2.5, 0.5,
                                 help="Lower = tighter trailing stop, more flips. Classic default is 3.0.")
    SWING, SIGNAL, OR_BARS, CLOSE_BREAK, RSI_PERIOD, WMA_PERIOD = 20, "both", 1, True, 9, 21

RR = st.sidebar.slider("Risk : Reward", 0.5, 5.0, 2.0, 0.5,
                        help="For Supertrend, Target is still RR-based, but SL trails live in paper "
                             "trading -- the trade may exit via trailing stop well before Target.")'''

old2 = '''def get_signals(df):
    """Dispatches to whichever strategy is selected in the sidebar."""
    if STRATEGY == "SMC BOS/CHoCH":
        return signals(df, SWING, CLOSE_BREAK)
    if STRATEGY == "ORB 5-Min Breakout":
        return None, orb_signals(df, OR_BARS)
    return None, hilega_milega_signals(df, RSI_PERIOD, WMA_PERIOD)'''

new2 = '''def get_signals(df):
    """Dispatches to whichever strategy is selected in the sidebar."""
    if STRATEGY == "SMC BOS/CHoCH":
        return signals(df, SWING, CLOSE_BREAK)
    if STRATEGY == "ORB 5-Min Breakout":
        return None, orb_signals(df, OR_BARS)
    if STRATEGY == "Vanguard (RSI x WMA)":
        return None, hilega_milega_signals(df, RSI_PERIOD, WMA_PERIOD)
    return None, supertrend_signals(df, ST_PERIOD, ST_MULT)'''

old3 = '''        elif STRATEGY == "ORB 5-Min Breakout":
            st.info("Each day's opening range (first candle(s)) sets the breakout levels. "
                    "Check the annotated breakouts line up with real range breaks before "
                    "trusting the numbers below.")
            chart_label = f"ORB ({OR_BARS}-candle range)"
        else:
            st.info("Signals fire when RSI crosses its own WMA. This is a lagging, "
                    "trend-following setup by nature — expect fewer, later signals "
                    "than SMC/ORB, and more whipsaws in a sideways/choppy market.")
            chart_label = f"RSI({RSI_PERIOD}) x WMA({WMA_PERIOD})"'''

new3 = '''        elif STRATEGY == "ORB 5-Min Breakout":
            st.info("Each day's opening range (first candle(s)) sets the breakout levels. "
                    "Check the annotated breakouts line up with real range breaks before "
                    "trusting the numbers below.")
            chart_label = f"ORB ({OR_BARS}-candle range)"
        elif STRATEGY == "Vanguard (RSI x WMA)":
            st.info("Signals fire when RSI crosses its own WMA. This is a lagging, "
                    "trend-following setup by nature — expect fewer, later signals "
                    "than SMC/ORB, and more whipsaws in a sideways/choppy market.")
            chart_label = f"RSI({RSI_PERIOD}) x WMA({WMA_PERIOD})"
        else:
            st.info("Signals fire on every Supertrend direction flip. In paper trading the "
                    "stop trails the Supertrend line live and only tightens -- this backtest "
                    "approximates that with a fixed RR target instead, since it doesn't "
                    "re-check a moving SL candle-by-candle the same way.")
            chart_label = f"Supertrend({ST_PERIOD}, {ST_MULT})"'''

with open(PATH) as f:
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
shutil.copy(PATH, PATH + ".bak_supertrend2")

with open(PATH, "w") as f:
    f.write(content)

print("Patched (2/3) -- Supertrend added to sidebar, dispatcher, and backtest labeling.")
