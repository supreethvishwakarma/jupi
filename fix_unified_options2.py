PATH = "app.py"

old = '''INSTRUMENTS = {
    "NIFTY 50": ("99926000", "NSE", 65),
    "NIFTY BANK": ("99926009", "NSE", 35),
    "FINNIFTY": ("99926037", "NSE", 65),
    "MIDCPNIFTY": ("99926074", "NSE", 120),
}'''

new = '''INSTRUMENTS = {
    "NIFTY 50": ("99926000", "NSE", 65),
    "NIFTY BANK": ("99926009", "NSE", 35),
    "FINNIFTY": ("99926037", "NSE", 65),
    "MIDCPNIFTY": ("99926074", "NSE", 120),
    "SENSEX": ("99919000", "BSE", 10),
}'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_unified2")

with open(PATH, "w") as f:
    f.write(content)

print("Patched (2/4) -- SENSEX added to Instrument list.")
