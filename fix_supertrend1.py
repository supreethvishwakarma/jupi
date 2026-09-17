PATH = "app.py"

old = '''def get_option_config(inst_name):'''

new = '''def supertrend_indicator(df, period=10, multiplier=3.0):
    """Standard Supertrend: an ATR-based band that flips sides of price and,
    while on one side, only ever moves toward price (never away) -- this is
    what makes it a genuine trailing stop, not just an entry signal."""
    high, low, close = df["high"].astype(float), df["low"].astype(float), df["close"].astype(float)
    hl2 = (high + low) / 2
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    basic_upper = hl2 + multiplier * atr
    basic_lower = hl2 - multiplier * atr

    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()
    st_line = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=object)

    for i in range(len(df)):
        if i == 0 or pd.isna(atr.iloc[i]):
            final_upper.iloc[i] = basic_upper.iloc[i]
            final_lower.iloc[i] = basic_lower.iloc[i]
            st_line.iloc[i] = final_upper.iloc[i]
            direction.iloc[i] = "bearish"
            continue
        final_upper.iloc[i] = (basic_upper.iloc[i]
                                if (basic_upper.iloc[i] < final_upper.iloc[i-1] or close.iloc[i-1] > final_upper.iloc[i-1])
                                else final_upper.iloc[i-1])
        final_lower.iloc[i] = (basic_lower.iloc[i]
                                if (basic_lower.iloc[i] > final_lower.iloc[i-1] or close.iloc[i-1] < final_lower.iloc[i-1])
                                else final_lower.iloc[i-1])
        if direction.iloc[i-1] == "bearish":
            if close.iloc[i] > final_upper.iloc[i]:
                direction.iloc[i] = "bullish"
                st_line.iloc[i] = final_lower.iloc[i]
            else:
                direction.iloc[i] = "bearish"
                st_line.iloc[i] = final_upper.iloc[i]
        else:
            if close.iloc[i] < final_lower.iloc[i]:
                direction.iloc[i] = "bearish"
                st_line.iloc[i] = final_upper.iloc[i]
            else:
                direction.iloc[i] = "bullish"
                st_line.iloc[i] = final_lower.iloc[i]

    return st_line, direction


def supertrend_signals(df, period=10, multiplier=3.0):
    """Signal fires on every direction flip -- Level is the Supertrend value
    at that candle, used as the initial (soon-to-be-trailed) stop."""
    st_line, direction = supertrend_indicator(df, period, multiplier)
    rows = []
    for i in range(1, len(df)):
        if direction.iloc[i] != direction.iloc[i-1]:
            rows.append(dict(type="ST", direction=direction.iloc[i], broken_i=i, Level=float(st_line.iloc[i])))
    return pd.DataFrame(rows, columns=["type", "direction", "broken_i", "Level"])


def supertrend_current_value(df, period=10, multiplier=3.0):
    """Just the latest Supertrend line value, for updating a trailing SL on an open position."""
    if len(df) <= period:
        return None
    st_line, _ = supertrend_indicator(df, period, multiplier)
    v = st_line.iloc[-1]
    return None if pd.isna(v) else float(v)


def get_option_config(inst_name):'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_supertrend1")

with open(PATH, "w") as f:
    f.write(content)

print("Patched (1/3) -- Supertrend functions added.")
