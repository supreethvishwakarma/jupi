PATH = "app.py"

old = '''        st.markdown("**Closed trades**")
        if pp["closed"]:
            c = pd.DataFrame(pp["closed"])
            tot = c.points.sum()'''

new = '''        st.markdown("**Closed trades**")
        if pp["closed"]:
            c = pd.DataFrame(pp["closed"])
            if "pnl_rs" not in c.columns:
                c["pnl_rs"] = pd.NA
            missing = c["pnl_rs"].isna()
            if missing.any():
                if "proceeds" in c.columns and "capital_blocked" in c.columns:
                    fallback = c["proceeds"].fillna(0) - c["capital_blocked"].fillna(0)
                else:
                    fallback = c["points"] * QTY
                c.loc[missing, "pnl_rs"] = fallback[missing]
            c["pnl_rs"] = c["pnl_rs"].astype(float).round(2)
            tot = c.points.sum()'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_pnlbackfill")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- pnl_rs is now backfilled for trades closed before it existed.")
