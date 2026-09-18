PATH = "app.py"

old = '''                        hit_profit_lock = False
                        if pos.get("strategy") == "Vanguard (RSI x WMA)":
                            _plb, _pla = get_bid_ask(option_exch, option_token)
                            if _plb is not None:
                                _pl_cost = real_options_cost(pos["entry"], _plb, qty_i)
                                _pl_pnl = round(_plb * qty_i - _pl_cost - pos.get("capital_blocked", 0), 2)
                                pos["peak_pnl"] = max(pos.get("peak_pnl", 0), _pl_pnl)
                                if pos["peak_pnl"] >= 1000 and _pl_pnl <= pos["peak_pnl"] - 500:
                                    hit_profit_lock = True'''

new = '''                        hit_profit_lock = False
                        if pos.get("strategy") == "Vanguard (RSI x WMA)":
                            _plb, _pla = get_bid_ask(option_exch, option_token)
                            if _plb is not None:
                                _pl_cost = real_options_cost(pos["entry"], _plb, qty_i)
                                _pl_pnl = round(_plb * qty_i - _pl_cost - pos.get("capital_blocked", 0), 2)
                                pos["peak_pnl"] = max(pos.get("peak_pnl", 0), _pl_pnl)
                                if pos["peak_pnl"] >= 1000:
                                    _profit_floor = max(1000, pos["peak_pnl"] - 500)
                                    if _pl_pnl <= _profit_floor:
                                        hit_profit_lock = True'''

with open(PATH, encoding="utf-8") as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_profitfloor1000")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched -- profit floor now locks at a guaranteed minimum of Rs 1,000 once touched, trailing further beyond that.")
