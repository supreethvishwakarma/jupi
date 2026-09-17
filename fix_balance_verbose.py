import json, os

path = "paper_positions.json"
print(f"Looking for: {os.path.abspath(path)}")
print(f"Exists: {os.path.exists(path)}\n")

with open(path) as f:
    pp = json.load(f)

STARTING_CAPITAL = 100000

closed = pp.get("closed", [])
print(f"Number of closed trades in file: {len(closed)}\n")

running = STARTING_CAPITAL
for i, t in enumerate(closed):
    pnl = t.get("pnl_rs", None)
    inst = t.get("instrument", "?")
    exit_type = t.get("exit", "?")
    exit_time = t.get("exit_time", "?")
    print(f"[{i}] {inst} | exit={exit_type} | pnl_rs={pnl!r} | exit_time={exit_time}")
    if pnl is not None:
        running += pnl
    else:
        print(f"     ^ WARNING: this trade has no pnl_rs field at all!")

print(f"\nStarting capital: Rs {STARTING_CAPITAL:,.2f}")
print(f"Sum of all pnl_rs: Rs {running - STARTING_CAPITAL:,.2f}")
print(f"Correct ending balance: Rs {running:,.2f}")
print(f"\nCurrent (possibly wrong) balance in file: Rs {pp.get('balance', 'MISSING'):,.2f}" 
      if isinstance(pp.get('balance'), (int, float)) else f"\nCurrent balance field: {pp.get('balance')!r}")

orphans = list(pp.get("open", {}).keys())
print(f"\nOpen/orphaned positions: {orphans if orphans else 'none'}")

confirm = input("\nType YES to write the corrected balance (leaves closed-trades history untouched): ")
if confirm.strip() == "YES":
    pp["balance"] = round(running, 2)
    pp["open"] = {}
    with open(path, "w") as f:
        json.dump(pp, f, indent=1, default=str)
    print(f"Written. New balance: Rs {round(running, 2):,.2f}")
else:
    print("Not written -- nothing changed.")
