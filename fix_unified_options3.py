PATH = "app.py"

old1 = '''if EXCH == "MCX":
    st.sidebar.warning("MCX futures expire monthly. History is limited to this "
                        "contract's life, and stitching contracts creates fake "
                        "price jumps that look like real breaks.")
    MARGIN_PCT = st.sidebar.slider("Margin % of contract value (MCX)", 5.0, 100.0, 30.0, 1.0,
                                    help="Real MCX crude margin varies with volatility -- "
                                         "historically ~15-30%, has spiked to 60-100% in extreme "
                                         "moves. Check AngelOne's own margin calculator for today's "
                                         "real figure before trusting this.")
else:
    MARGIN_PCT = 30.0'''

new1 = '''if EXCH == "MCX":
    st.sidebar.warning("MCX futures expire monthly. History is limited to this "
                        "contract's life, and stitching contracts creates fake "
                        "price jumps that look like real breaks. Paper trading now "
                        "buys real CRUDEOIL options against this contract, not the "
                        "future itself.")'''

old2 = '''st.sidebar.divider()
st.sidebar.subheader("Option buying")
OPT_MODE = st.sidebar.checkbox("Simulate option buying", True)
PREMIUM = st.sidebar.number_input("ATM premium (Rs)", 20, 500, 140, 10)
DELTA = st.sidebar.slider("Delta", 0.3, 0.8, 0.5, 0.05)
THETA_HR = st.sidebar.slider("Theta (pts/hour)", 0.0, 10.0, 3.0, 0.5)
SPREAD = st.sidebar.slider("Spread (pts/trade)", 0.0, 5.0, 1.0, 0.25)'''

new2 = '''st.sidebar.divider()
st.sidebar.subheader("Option buying (backtest model)")
st.sidebar.caption("Paper trading now buys the real ATM option at its real live price -- "
                    "these settings only affect the Backtest tab's approximation, since "
                    "real historical option prices aren't available this way.")
OPT_MODE = st.sidebar.checkbox("Simulate option buying (backtest)", True)
PREMIUM = st.sidebar.number_input("ATM premium (Rs)", 20, 500, 140, 10)
DELTA = st.sidebar.slider("Delta", 0.3, 0.8, 0.5, 0.05)
THETA_HR = st.sidebar.slider("Theta (pts/hour)", 0.0, 10.0, 3.0, 0.5)
SPREAD = st.sidebar.slider("Spread (pts/trade)", 0.0, 5.0, 1.0, 0.25)'''

with open(PATH) as f:
    content = f.read()

n1, n2 = content.count(old1), content.count(old2)
if n1 != 1 or n2 != 1:
    print(f"WARNING: expected 1 match each, found {n1} and {n2}. Aborting.")
    raise SystemExit(1)
content = content.replace(old1, new1).replace(old2, new2)

import shutil
shutil.copy(PATH, PATH + ".bak_unified3")

with open(PATH, "w") as f:
    f.write(content)

print("Patched (3/4) -- sidebar simplified/relabeled.")
