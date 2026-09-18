PATH = "app.py"

old1 = '''                        if (not pd.isna(_cur_atr) and not pd.isna(_avg_atr) and _avg_atr > 0
                                and _cur_atr >= 1.2 * _avg_atr):
                            _qty_for_trade = _base_qty * 2'''

new1 = '''                        if (not pd.isna(_cur_atr) and not pd.isna(_avg_atr) and _avg_atr > 0
                                and _cur_atr >= 1.2 * _avg_atr):
                            _qty_for_trade = _base_qty * 3'''

old2 = '''                                if pos["peak_pnl"] >= 1000:
                                    _profit_floor = max(1000, pos["peak_pnl"] - 500)'''

new2 = '''                                if pos["peak_pnl"] >= 600:
                                    _profit_floor = max(600, pos["peak_pnl"] - 300)'''

with open(PATH, encoding="utf-8") as f:
    content = f.read()

results = []
for i, (old, new) in enumerate([(old1, new1), (old2, new2)], 1):
    n = content.count(old)
    results.append(n)
    if n != 1:
        print(f"WARNING patch {i}: expected 1 match, found {n}. Aborting.")
        raise SystemExit(1)
    content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_3xand600")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched -- volatility sizing now 3x, profit-lock now triggers at Rs 600 (floor = max(600, peak-300)).")
