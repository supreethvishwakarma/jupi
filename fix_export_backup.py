PATH = "app.py"

old = '''    if top[3].button("Reset paper account"):
        save_paper({"open": {}, "closed": [], "ignored": [], "balance": STARTING_CAPITAL})
        st.rerun()'''

new = '''    if top[3].button("Reset paper account"):
        _old = load_paper()
        if _old.get("closed"):
            from zoneinfo import ZoneInfo as _ZoneInfo
            _ts = dt.datetime.now(_ZoneInfo("Asia/Kolkata")).strftime("%Y%m%d_%H%M%S")
            _backup_path = f"trade_book_backup_{_ts}.csv"
            pd.DataFrame(_old["closed"]).to_csv(_backup_path, index=False)
            st.toast(f"Backed up {len(_old['closed'])} trades to {_backup_path} before reset")
        save_paper({"open": {}, "closed": [], "ignored": [], "balance": STARTING_CAPITAL})
        st.rerun()

    _pp_for_export = load_paper()
    if _pp_for_export.get("closed"):
        if st.button("Export trade book (CSV)", key="export_trade_book"):
            from zoneinfo import ZoneInfo as _ZoneInfo
            _ts = dt.datetime.now(_ZoneInfo("Asia/Kolkata")).strftime("%Y%m%d_%H%M%S")
            _export_path = f"trade_book_export_{_ts}.csv"
            pd.DataFrame(_pp_for_export["closed"]).to_csv(_export_path, index=False)
            st.success(f"Saved {len(_pp_for_export['closed'])} trades to {_export_path}")'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_export")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- trade book export button added, Reset now auto-backs-up first.")
