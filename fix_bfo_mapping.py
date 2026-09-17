PATH = "app.py"

old = '            exch_map = {"NSE": 1, "NFO": 2, "BSE": 3, "MCX": 5}'
new = '            exch_map = {"NSE": 1, "NFO": 2, "BSE": 3, "BFO": 4, "MCX": 5}'

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_bfomap")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- BFO (SENSEX options) now correctly maps to exchangeType 4 for WebSocket subscriptions.")
