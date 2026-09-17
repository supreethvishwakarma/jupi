PATH = "app.py"

old = '''        def get_ltp(self, token):
            with self.lock:
                d = self.latest.get(str(token))
                return d["ltp"] if d else None'''

new = '''        def get_ltp(self, token):
            with self.lock:
                d = self.latest.get(str(token))
                if d and (_time.time() - d["ts"]) < 20:
                    return d["ltp"]
                return None  # stale (no tick in 20s) -- treat as no live data, don't show a frozen price'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_tickrecency")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- stale ticks (>20s old) now correctly show as 'no live data' instead of a frozen number.")
