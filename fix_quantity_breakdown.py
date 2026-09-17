PATH = "app.py"

old = '''LOTS = LOTS_PER_INSTRUMENT.get(INST, 1)  # used for the single-instrument Backtest tab
QTY = LOTSIZE * LOTS
LOT = QTY
st.sidebar.success(f"**Quantity ({INST}): {QTY:,}** ({LOTSIZE} x {LOTS} lots)")'''

new = '''LOTS = LOTS_PER_INSTRUMENT.get(INST, 1)  # used for the single-instrument Backtest tab
QTY = LOTSIZE * LOTS
LOT = QTY

_qty_lines = []
for _inst in PAPER_INSTRUMENTS:
    _sz = INSTRUMENTS[_inst][2]
    _lt = LOTS_PER_INSTRUMENT.get(_inst, 1)
    _qty_lines.append(f"**{_inst}**: {_sz*_lt:,} units ({_sz} x {_lt} lots)")
st.sidebar.success("Quantities:  \\n" + "  \\n".join(_qty_lines))'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_qtybreakdown")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- sidebar now shows the calculated quantity for EVERY paper-traded instrument, not just one.")
