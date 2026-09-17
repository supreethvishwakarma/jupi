PATH = "app.py"

old = '''    rows.sort(key=lambda r: parse_expiry(r["tradingsymbol"]))
    return rows[:1]  # just the single nearest contract, not two confusing ones'''

new = '''    rows.sort(key=lambda r: parse_expiry(r["tradingsymbol"]))

    today = dt.datetime.now()
    with_runway = [r for r in rows if parse_expiry(r["tradingsymbol"]) >= today + dt.timedelta(days=7)]
    chosen = with_runway if with_runway else rows  # fallback: if everything's within 7 days, use nearest anyway
    return chosen[:1]  # the nearest contract WITH real runway, not the literal soonest one'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_crudeexpiry")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- CRUDEOIL now skips contracts expiring within 7 days, picks the next one with real runway.")
