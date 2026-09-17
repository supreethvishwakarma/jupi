PATH = "app.py"

old = '''        blocked_total = sum(p.get("capital_blocked", 0) for p in pp["open"].values()
                            if p.get("status") in ("open",))'''

new = '''        blocked_total = sum(p.get("capital_blocked", 0) for name, p in pp["open"].items()
                            if p.get("status") == "open" and name in PAPER_INSTRUMENTS)
        _orphans = {name: p.get("capital_blocked", 0) for name, p in pp["open"].items()
                    if name not in PAPER_INSTRUMENTS}
        if _orphans:
            st.warning(f"Orphaned position(s) in storage for instruments not currently selected: "
                       f"{', '.join(_orphans)} -- click 'Reset paper account' to clear these.")'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_blockedscope")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- Blocked total now scoped to current instruments, orphans surfaced visibly instead of silently.")
