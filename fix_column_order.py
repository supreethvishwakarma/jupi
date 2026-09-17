PATH = "app.py"

old = '''            cols_show = [x for x in ["instrument", "strategy", "dir", "type", "entry", "sl", "target",
                                      "exit", "exit_price", "exit_time", "points", "pnl_rs", "opt_points",
                                      "exit_premium", "real_cost", "proceeds"] if x in c.columns]
            color_cols = [x for x in ["points", "pnl_rs", "opt_points", "proceeds"] if x in cols_show]'''

new = '''            cols_show = [x for x in ["instrument", "strategy", "dir", "type", "entry", "sl", "target",
                                      "exit", "exit_price", "exit_time", "points", "opt_points",
                                      "exit_premium", "real_cost", "pnl_rs"] if x in c.columns]
            color_cols = [x for x in ["points", "pnl_rs", "opt_points"] if x in cols_show]'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_colorder")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- 'proceeds' removed, 'pnl_rs' is now the last column.")
