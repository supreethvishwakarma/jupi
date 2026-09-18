PATH = "app.py"

old = '''            _edf = pd.DataFrame(_pp_for_export["closed"])
            if "time" in _edf.columns:
                _edf = _edf.rename(columns={"time": "entry_time"})
            _first_cols = [x for x in ["instrument", "strategy", "dir", "type", "entry_time",
                                        "entry", "exit_time", "exit", "exit_price", "pnl_rs"]
                           if x in _edf.columns]
            _edf = _edf[_first_cols + [x for x in _edf.columns if x not in _first_cols]]
            _edf.to_csv(_export_path, index=False)'''

new = '''            _edf = pd.DataFrame(_pp_for_export["closed"])
            if "time" in _edf.columns:
                _edf = _edf.rename(columns={"time": "entry_time"})
            if "qty" not in _edf.columns:
                _edf["qty"] = pd.NA
            if "capital_blocked" in _edf.columns and "entry" in _edf.columns:
                _missing_qty = _edf["qty"].isna()
                _fallback_qty = (_edf["capital_blocked"] / _edf["entry"]).round()
                _edf.loc[_missing_qty, "qty"] = _fallback_qty[_missing_qty]
            _lot_sizes = {name: cfg[2] for name, cfg in INSTRUMENTS.items()}
            _edf["lots"] = _edf.apply(
                lambda r: round(r["qty"] / _lot_sizes.get(r.get("instrument"), 1), 2)
                if pd.notna(r.get("qty")) and r.get("instrument") in _lot_sizes else pd.NA, axis=1)
            _edf = _edf.rename(columns={"capital_blocked": "capital_utilized_rs", "qty": "quantity"})
            _first_cols = [x for x in ["instrument", "strategy", "dir", "type", "entry_time",
                                        "entry", "lots", "quantity", "capital_utilized_rs",
                                        "exit_time", "exit", "exit_price", "pnl_rs"]
                           if x in _edf.columns]
            _edf = _edf[_first_cols + [x for x in _edf.columns if x not in _first_cols]]
            _edf.to_csv(_export_path, index=False)'''

with open(PATH, encoding="utf-8") as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_csvlots")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched -- CSV export now shows lots and capital_utilized_rs as clear, prioritized columns.")
