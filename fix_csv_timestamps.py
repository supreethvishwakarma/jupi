PATH = "app.py"

old1 = '''            cols_show = [x for x in ["instrument", "strategy", "dir", "type", "option_symbol",
                                      "entry", "sl", "target", "exit", "exit_price", "exit_time",
                                      "points", "real_cost", "pnl_rs"] if x in c.columns]'''

new1 = '''            if "time" in c.columns:
                c = c.rename(columns={"time": "entry_time"})
            cols_show = [x for x in ["instrument", "strategy", "dir", "type", "option_symbol",
                                      "entry_time", "entry", "sl", "target", "exit", "exit_price",
                                      "exit_time", "points", "real_cost", "pnl_rs"] if x in c.columns]'''

old2 = '''        _old = load_paper()
        if _old.get("closed"):
            from zoneinfo import ZoneInfo as _ZoneInfo
            _ts = dt.datetime.now(_ZoneInfo("Asia/Kolkata")).strftime("%Y%m%d_%H%M%S")
            _backup_path = f"trade_book_backup_{_ts}.csv"
            pd.DataFrame(_old["closed"]).to_csv(_backup_path, index=False)
            st.toast(f"Backed up {len(_old['closed'])} trades to {_backup_path} before reset")'''

new2 = '''        _old = load_paper()
        if _old.get("closed"):
            from zoneinfo import ZoneInfo as _ZoneInfo
            _ts = dt.datetime.now(_ZoneInfo("Asia/Kolkata")).strftime("%Y%m%d_%H%M%S")
            _backup_path = f"trade_book_backup_{_ts}.csv"
            _bdf = pd.DataFrame(_old["closed"])
            if "time" in _bdf.columns:
                _bdf = _bdf.rename(columns={"time": "entry_time"})
            _first_cols = [x for x in ["instrument", "strategy", "dir", "type", "entry_time",
                                        "entry", "exit_time", "exit", "exit_price", "pnl_rs"]
                           if x in _bdf.columns]
            _bdf = _bdf[_first_cols + [x for x in _bdf.columns if x not in _first_cols]]
            _bdf.to_csv(_backup_path, index=False)
            st.toast(f"Backed up {len(_old['closed'])} trades to {_backup_path} before reset")'''

old3 = '''            _export_path = f"trade_book_export_{_ts}.csv"
            pd.DataFrame(_pp_for_export["closed"]).to_csv(_export_path, index=False)
            st.success(f"Saved {len(_pp_for_export['closed'])} trades to {_export_path}")'''

new3 = '''            _export_path = f"trade_book_export_{_ts}.csv"
            _edf = pd.DataFrame(_pp_for_export["closed"])
            if "time" in _edf.columns:
                _edf = _edf.rename(columns={"time": "entry_time"})
            _first_cols = [x for x in ["instrument", "strategy", "dir", "type", "entry_time",
                                        "entry", "exit_time", "exit", "exit_price", "pnl_rs"]
                           if x in _edf.columns]
            _edf = _edf[_first_cols + [x for x in _edf.columns if x not in _first_cols]]
            _edf.to_csv(_export_path, index=False)
            st.success(f"Saved {len(_pp_for_export['closed'])} trades to {_export_path}")'''

with open(PATH) as f:
    content = f.read()

results = []
for i, (old, new) in enumerate([(old1, new1), (old2, new2), (old3, new3)], 1):
    n = content.count(old)
    results.append(n)
    if n != 1:
        print(f"WARNING patch {i}: expected 1 match, found {n}. Aborting.")
        raise SystemExit(1)
    content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_csvtimestamps")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- entry_time and exit_time now clearly shown in the table and every CSV export.")
