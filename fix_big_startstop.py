PATH = "app.py"

old = '''    if "trading_live" not in st.session_state:
        st.session_state.trading_live = True

    top = st.columns([1, 1, 1, 1, 1])
    start_clicked = top[0].button("\\u25b6 Start Trading", type="primary",
                                   disabled=st.session_state.trading_live, use_container_width=True)
    stop_clicked = top[1].button("\\u23f9 Stop & Square Off All",
                                  disabled=not st.session_state.trading_live, use_container_width=True)
    REFRESH_SECONDS = top[2].number_input("Signal scan (sec)", 30, 600, 60, 15,
                                           help="How often to check for NEW signals via REST candles. Keep at 60+.")
    STARTING_CAPITAL = top[3].number_input("Paper capital (Rs)", 10000, 10000000, 100000, 5000,
                                            help="Virtual starting balance. Only applied after Reset.")
    reset_clicked = top[4].button("Reset paper account")'''

new = '''    if "trading_live" not in st.session_state:
        st.session_state.trading_live = False  # app launches idle -- configure first, then Start

    st.markdown("""
    <style>
    div[data-testid="stButton"] button {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        padding: 1.1rem 0.5rem !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    big1, big2 = st.columns(2)
    start_clicked = big1.button("\\u25b6\\ufe0f  START PAPER TRADING", type="primary",
                                 disabled=st.session_state.trading_live, use_container_width=True)
    stop_clicked = big2.button("\\u23f9\\ufe0f  STOP & SQUARE OFF ALL",
                                disabled=not st.session_state.trading_live, use_container_width=True)

    if st.session_state.trading_live:
        st.success("\\U0001F7E2 Paper trading is RUNNING -- scanning and monitoring live.")
    else:
        st.warning("\\U0001F534 Paper trading is STOPPED. Set your Instrument, Lot size, Strategy, and "
                   "\\\"Paper trade these instruments\\\" above, then click START.")

    top = st.columns([1, 1, 1])
    REFRESH_SECONDS = top[0].number_input("Signal scan (sec)", 30, 600, 60, 15,
                                           help="How often to check for NEW signals via REST candles. Keep at 60+.")
    STARTING_CAPITAL = top[1].number_input("Paper capital (Rs)", 10000, 10000000, 100000, 5000,
                                            help="Virtual starting balance. Only applied after Reset.")
    reset_clicked = top[2].button("Reset paper account")'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_bigstartstop")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- big Start/Stop buttons added, app now launches idle by default.")
