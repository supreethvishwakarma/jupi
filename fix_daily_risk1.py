PATH = "app.py"

old = '''    top = st.columns([1, 1, 1])
    REFRESH_SECONDS = top[0].number_input("Signal scan (sec)", 30, 600, 60, 15,
                                           help="How often to check for NEW signals via REST candles. Keep at 60+.")
    STARTING_CAPITAL = top[1].number_input("Paper capital (Rs)", 10000, 10000000, 100000, 5000,
                                            help="Virtual starting balance. Only applied after Reset.")
    reset_clicked = top[2].button("Reset paper account")'''

new = '''    top = st.columns([1, 1, 1])
    REFRESH_SECONDS = top[0].number_input("Signal scan (sec)", 30, 600, 60, 15,
                                           help="How often to check for NEW signals via REST candles. Keep at 60+.")
    STARTING_CAPITAL = top[1].number_input("Paper capital (Rs)", 10000, 10000000, 100000, 5000,
                                            help="Virtual starting balance. Only applied after Reset.")
    reset_clicked = top[2].button("Reset paper account")

    risk1, risk2 = st.columns(2)
    DAILY_PROFIT_TARGET = risk1.number_input("Daily profit target (Rs, 0=off)", 0, 1000000, 10000, 500,
                                              help="Once today's realized P&L across all instruments reaches "
                                                   "this, everything auto-squares-off and trading stops for the day.")
    MAX_TRADES_PER_DAY = risk2.number_input("Max trades/instrument/day (0=unlimited)", 0, 100, 10, 1,
                                             help="Stops opening new positions for an instrument once it's had "
                                                  "this many closed trades today. Resets automatically at midnight "
                                                  "(counted per calendar day, not per session).")'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_dailyrisk1")

with open(PATH, "w") as f:
    f.write(content)

print("Patched (1/4) -- sidebar risk controls added.")
