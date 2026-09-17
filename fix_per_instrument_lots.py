PATH = "app.py"

old1 = '''st.sidebar.divider()
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

new1 = '''st.sidebar.divider()
st.sidebar.subheader("Capital")
LOTSIZE = LOT  # exchange-fixed lot size for the selected Instrument -- not user-editable
st.sidebar.metric("Lot size (exchange-fixed)", f"{LOTSIZE} units/lot")

st.sidebar.caption("Lots per instrument (paper trading):")
LOTS_PER_INSTRUMENT = {}
for _inst in PAPER_INSTRUMENTS:
    _inst_lot_size = INSTRUMENTS[_inst][2]
    LOTS_PER_INSTRUMENT[_inst] = st.sidebar.number_input(
        f"{_inst} lots ({_inst_lot_size}/lot)", 1, 50, 1, 1, key=f"lots_{_inst}")

LOTS = LOTS_PER_INSTRUMENT.get(INST, 1)  # used for the single-instrument Backtest tab
QTY = LOTSIZE * LOTS
LOT = QTY
st.sidebar.success(f"**Quantity ({INST}): {QTY:,}** ({LOTSIZE} x {LOTS} lots)")'''

old2 = '''            tok, exch, lot_size = INSTRUMENTS[inst_name]
            qty_i = lot_size * LOTS
            ts.ensure_subscribed(exch, tok)'''

new2 = '''            tok, exch, lot_size = INSTRUMENTS[inst_name]
            qty_i = lot_size * LOTS_PER_INSTRUMENT.get(inst_name, 1)
            ts.ensure_subscribed(exch, tok)'''

old3 = '''            _tok, _exch, _lot = INSTRUMENTS.get(_inst_name, (None, None, 1))
            _qty_i = _lot * LOTS'''

new3 = '''            _tok, _exch, _lot = INSTRUMENTS.get(_inst_name, (None, None, 1))
            _qty_i = _lot * LOTS_PER_INSTRUMENT.get(_inst_name, 1)'''

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
shutil.copy(PATH, PATH + ".bak_perinstlots")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- each paper-traded instrument now has its own 'Number of lots' input.")
