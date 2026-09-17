PATH = "app.py"

old = '''                    except Exception:
                        pass
                continue

            time.sleep(1.5)
            try:
                chart_df = fetch((now - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
                                  now.strftime("%Y-%m-%d %H:%M"), INTERVAL, tok, exch)'''

new = '''                    except Exception:
                        pass
                continue

            if MAX_TRADES_PER_DAY > 0:
                _today_count = sum(1 for t in pp["closed"]
                                    if t.get("instrument") == inst_name
                                    and _safe_date(t.get("exit_time", "")) == now.date())
                if _today_count >= MAX_TRADES_PER_DAY:
                    st.caption(f"{inst_name}: daily trade limit reached "
                               f"({_today_count}/{MAX_TRADES_PER_DAY}) -- not scanning for more today.")
                    continue

            time.sleep(1.5)
            try:
                chart_df = fetch((now - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
                                  now.strftime("%Y-%m-%d %H:%M"), INTERVAL, tok, exch)'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_dailyrisk4")

with open(PATH, "w") as f:
    f.write(content)

print("Patched (4/4) -- max trades per instrument per day now enforced.")
