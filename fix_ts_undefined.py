PATH = "app.py"

old = '''    def slow_panel():
        from zoneinfo import ZoneInfo
        pp = load_paper()
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)

        if not live_on:'''

new = '''    def slow_panel():
        from zoneinfo import ZoneInfo
        pp = load_paper()
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        ts = tick_service()

        if not live_on:'''

with open(PATH, encoding="utf-8") as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_tsfix")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched -- ts now defined in slow_panel, fixes the undefined variable bug in straddle entry logic.")
