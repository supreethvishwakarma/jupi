PATH = "app.py"

old = '''st.sidebar.divider()
st.sidebar.subheader("Capital")
LOTSIZE = st.sidebar.number_input("Lot size (exchange)", 1, 5000, LOT, 1,
                                   key=f"lotsize_{INST}",
                                   help="Fixed by the exchange - NIFTY 65, BANKNIFTY 35, CRUDEOIL 100. "
                                        "Only change it if the exchange revises the contract.")
LOTS = st.sidebar.number_input("Number of lots", 1, 50, 1, 1, key="lots",
                                help="How many contracts you buy. This is the one you control.")
QTY = LOTSIZE * LOTS
LOT = QTY
st.sidebar.success(f"**Quantity: {QTY:,}** ({LOTSIZE} x {LOTS} lots)")'''

new = '''st.sidebar.divider()
st.sidebar.subheader("Capital")
LOTSIZE = LOT  # exchange-fixed lot size for the selected Instrument -- not user-editable
st.sidebar.metric("Lot size (exchange-fixed)", f"{LOTSIZE} units/lot")
LOTS = st.sidebar.number_input("Number of lots", 1, 50, 1, 1, key="lots",
                                help="How many contracts you buy. This is the only sizing input you control -- "
                                     "lot size itself is fixed by the exchange per instrument (NIFTY 50=65, "
                                     "NIFTY BANK=35, FINNIFTY=65, MIDCPNIFTY=120, SENSEX=10, CRUDEOIL=100) and "
                                     "is applied automatically and correctly per instrument during paper trading.")
QTY = LOTSIZE * LOTS
LOT = QTY
st.sidebar.success(f"**Quantity: {QTY:,}** ({LOTSIZE} x {LOTS} lots)")'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_lockedlotsize")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- Lot size is now a fixed, auto-correct display per instrument; Number of lots is the only input.")
