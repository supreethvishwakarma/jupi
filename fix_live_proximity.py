PATH = "app.py"

old = '''            sw, sig = get_signals(chart_df)
            use = sig if (sig.empty or SIGNAL == "both") else sig[sig.type == SIGNAL]
            if use.empty:
                continue'''

new = '''            sw, sig = get_signals(chart_df)

            if STRATEGY == "Hilega Milega (RSI x WMA)" and len(chart_df) > WMA_PERIOD:
                _r = _wilder_rsi(chart_df["close"].astype(float), RSI_PERIOD)
                _w = _wma(_r, WMA_PERIOD)
                if not pd.isna(_r.iloc[-1]) and not pd.isna(_w.iloc[-1]):
                    _diff = round(_r.iloc[-1] - _w.iloc[-1], 2)
                    _side = "above" if _diff > 0 else "below"
                    st.caption(f"{inst_name}: RSI {_r.iloc[-1]:.1f} {_side} WMA {_w.iloc[-1]:.1f} "
                               f"(gap {_diff:+.1f}) -- crosses to trigger a signal")

            use = sig if (sig.empty or SIGNAL == "both") else sig[sig.type == SIGNAL]
            if use.empty:
                continue'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_liveproximity")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- live RSI vs WMA gap now shown each scan cycle for Hilega Milega.")
