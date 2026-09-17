PATH = "app.py"

old = '''    @st.fragment(run_every=REFRESH_SECONDS if live_on else None)
    def slow_panel():
        from zoneinfo import ZoneInfo
        pp = load_paper()
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        any_opened = False

        for inst_name in PAPER_INSTRUMENTS:'''

new = '''    @st.fragment(run_every=REFRESH_SECONDS if live_on else None)
    def slow_panel():
        from zoneinfo import ZoneInfo
        pp = load_paper()
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)

        if not live_on:
            st.caption("Signal scan paused -- no new positions will open until you click START.")
            return

        any_opened = False

        for inst_name in PAPER_INSTRUMENTS:'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_blockscan")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- slow_panel now refuses to scan or open any position at all while stopped, even on a one-time rerun.")
