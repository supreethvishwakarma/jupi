import json

with open("paper_positions.json") as f:
    pp = json.load(f)

STARTING_CAPITAL = 100000  # change this if you'd set a different starting capital

total_pnl = sum(t.get("pnl_rs", 0) or 0 for t in pp.get("closed", []))
correct_balance = round(STARTING_CAPITAL + total_pnl, 2)

print(f"Trades in history: {len(pp.get('closed', []))}")
print(f"Sum of pnl_rs across all closed trades: Rs {total_pnl:,.2f}")
print(f"Old (corrupted) balance: Rs {pp.get('balance', 0):,.2f}")
print(f"Corrected balance: Rs {correct_balance:,.2f}")

# Also clear any orphaned open positions (capital already lost to the same bug,
# can't be recovered, but at least stops them polluting future 'Blocked' totals)
orphans = list(pp.get("open", {}).keys())
if orphans:
    print(f"Clearing orphaned open position(s): {orphans}")
    pp["open"] = {}

pp["balance"] = correct_balance

with open("paper_positions.json", "w") as f:
    json.dump(pp, f, indent=1, default=str)

print("Done -- balance corrected, closed-trades history untouched.")
