PATH = "app.py"

old1 = '''        balance = pp.get("balance", STARTING_CAPITAL)
        b1, b2, b3 = st.columns(3)
        b1.metric("Available", f"Rs {balance:,.0f}")
        b2.metric("Blocked in trades", f"Rs {blocked_total:,.0f}")
        b3.metric("Total equity", f"Rs {balance + blocked_total:,.0f}")'''

new1 = '''        balance = pp.get("balance", STARTING_CAPITAL)
        b1, b2, b3 = st.columns(3)
        b1.metric("Available", f"Rs {balance:,.0f}")
        b2.metric("Blocked in trades", f"Rs {blocked_total:,.0f}")
        b3.metric("Total equity", f"Rs {balance + blocked_total:,.0f}")

        _breakdown = {name: p.get("capital_blocked", 0) for name, p in pp["open"].items()
                      if p.get("status") == "open" and name in PAPER_INSTRUMENTS
                      and p.get("capital_blocked", 0) > 0}
        if _breakdown:
            st.caption("Capital utilization: " + " · ".join(
                f"{name}: Rs {amt:,.0f}" for name, amt in _breakdown.items()))'''

old2 = '''            tot = c.points.sum()
            realized = pp.get("balance", STARTING_CAPITAL) - STARTING_CAPITAL'''

new2 = '''            tot = c.points.sum()
            realized = round(c["pnl_rs"].sum(), 2)  # from actual closed trades only -- excludes any currently-blocked capital'''

with open(PATH) as f:
    content = f.read()

n1, n2 = content.count(old1), content.count(old2)
if n1 != 1 or n2 != 1:
    print(f"WARNING: expected 1 match each, found {n1} and {n2}. Aborting.")
    raise SystemExit(1)
content = content.replace(old1, new1).replace(old2, new2)

import shutil
shutil.copy(PATH, PATH + ".bak_realizedfix")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- Realized P&L now strictly from closed trades; per-instrument capital breakdown added.")
