PATH = "app.py"

old1 = '''            except Exception as e:
                msg = str(e)
                if "exceeding access rate" in msg:
                    st.caption(f"\\u26a0\\ufe0f {inst_name}: rate limited, will retry next cycle")
                else:
                    st.error(f"{inst_name}: broker call failed: {e}")
                continue'''

new1 = '''            except Exception as e:
                msg = str(e)
                _cached = st.session_state.get(f"proximity_{inst_name}")
                _suffix = f" (last known: {_cached[0]}, as of {_cached[1]})" if _cached else ""
                if "exceeding access rate" in msg:
                    st.caption(f"\\u26a0\\ufe0f {inst_name}: rate limited, will retry next cycle{_suffix}")
                else:
                    st.error(f"{inst_name}: broker call failed: {e}{_suffix}")
                continue'''

old2 = '''            if STRATEGY == "Hilega Milega (RSI x WMA)" and len(chart_df) > WMA_PERIOD:
                _r = _wilder_rsi(chart_df["close"].astype(float), RSI_PERIOD)
                _w = _wma(_r, WMA_PERIOD)
                if not pd.isna(_r.iloc[-1]) and not pd.isna(_w.iloc[-1]):
                    _diff = round(_r.iloc[-1] - _w.iloc[-1], 2)
                    _side = "above" if _diff > 0 else "below"
                    st.caption(f"{inst_name}: RSI {_r.iloc[-1]:.1f} {_side} WMA {_w.iloc[-1]:.1f} "
                               f"(gap {_diff:+.1f}) -- crosses to trigger a signal")'''

new2 = '''            if STRATEGY == "Hilega Milega (RSI x WMA)" and len(chart_df) > WMA_PERIOD:
                _r = _wilder_rsi(chart_df["close"].astype(float), RSI_PERIOD)
                _w = _wma(_r, WMA_PERIOD)
                if not pd.isna(_r.iloc[-1]) and not pd.isna(_w.iloc[-1]):
                    _diff = round(_r.iloc[-1] - _w.iloc[-1], 2)
                    _side = "above" if _diff > 0 else "below"
                    _msg = f"RSI {_r.iloc[-1]:.1f} {_side} WMA {_w.iloc[-1]:.1f} (gap {_diff:+.1f})"
                    st.session_state[f"proximity_{inst_name}"] = (_msg, f"{now:%H:%M:%S}")
                    st.caption(f"{inst_name}: {_msg} -- crosses to trigger a signal")'''

with open(PATH) as f:
    content = f.read()

n1, n2 = content.count(old1), content.count(old2)
if n1 != 1 or n2 != 1:
    print(f"WARNING: expected 1 match each, found {n1} and {n2}. Aborting.")
    raise SystemExit(1)
content = content.replace(old1, new1).replace(old2, new2)

import shutil
shutil.copy(PATH, PATH + ".bak_persistproximity")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- RSI/WMA reading now persists through rate-limit cycles instead of disappearing.")
