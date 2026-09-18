PATH = "app.py"

old = '''def get_option_config(inst_name):'''

new = '''def scalp_signals(df, ema_period=9, rsi_period=14):
    """Nifty Options Scalping Playbook: 9 EMA + session VWAP + RSI(14). Entry
    fires the moment close crosses above/below BOTH the EMA and VWAP, with RSI
    confirming direction (>50 bullish, <50 bearish). SL = that candle's own
    high/low -- tight and fast, matching a quick-in-quick-out scalp, not a
    trend-riding trailing stop."""
    d = df.copy()
    close = d["close"].astype(float)
    high = d["high"].astype(float)
    low = d["low"].astype(float)
    volume = d["volume"].astype(float).replace(0, 1)

    ema = close.ewm(span=ema_period, adjust=False).mean()

    d["date"] = d["timestamp"].dt.date
    typical = (high + low + close) / 3
    pv = typical * volume
    cum_pv = pv.groupby(d["date"]).cumsum()
    cum_vol = volume.groupby(d["date"]).cumsum()
    vwap = cum_pv / cum_vol

    rsi = _wilder_rsi(close, rsi_period)

    above_ema = close > ema
    above_vwap = close > vwap
    bull_now = above_ema & above_vwap & (rsi > 50)
    bear_now = (~above_ema) & (~above_vwap) & (rsi < 50)

    rows = []
    for i in range(1, len(d)):
        if pd.isna(ema.iloc[i]) or pd.isna(vwap.iloc[i]) or pd.isna(rsi.iloc[i]):
            continue
        if bull_now.iloc[i] and not bull_now.iloc[i-1]:
            rows.append(dict(type="SCALP", direction="bullish", broken_i=i, Level=float(low.iloc[i])))
        elif bear_now.iloc[i] and not bear_now.iloc[i-1]:
            rows.append(dict(type="SCALP", direction="bearish", broken_i=i, Level=float(high.iloc[i])))
    return pd.DataFrame(rows, columns=["type", "direction", "broken_i", "Level"])


def get_option_config(inst_name):'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_scalping1")

with open(PATH, "w") as f:
    f.write(content)

print("Patched (1/2) -- scalping strategy function added.")
