PATH = "app.py"

old1 = '''    def _close_position(pp, inst_name, pos, trigger, ltp, now):
        bull = pos["dir"] == "bullish"
        pts = round((ltp - pos["entry"]) if bull else (pos["entry"] - ltp), 2)
        pos.update(exit=trigger, exit_price=round(ltp, 2), exit_time=str(now), points=pts)
        if OPT_MODE and "entry_premium" in pos:
            hours_held = max((now - dt.datetime.fromisoformat(pos["time"])).total_seconds() / 3600, 0)
            opt_pts = round(pts*DELTA - hours_held*THETA_HR - SPREAD, 2)
            exit_premium = max(0.0, round(pos["entry_premium"] + opt_pts, 2))
            cost = real_options_cost(pos["entry_premium"], exit_premium, QTY)
            proceeds = round(exit_premium * QTY - cost, 2)
            pos.update(opt_points=opt_pts, exit_premium=exit_premium, proceeds=proceeds,
                       real_cost=cost, hours_held=round(hours_held, 2))
            pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + proceeds, 2)
        else:
            pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + pts*QTY, 2)
        pp["closed"].append(pos)
        del pp["open"][inst_name]
        save_paper(pp)
        st.success(f"{inst_name}: closed — {trigger} @ {round(ltp, 2)}")'''

new1 = '''    def _close_position(pp, inst_name, pos, trigger, ltp, now):
        bull = pos["dir"] == "bullish"
        pts = round((ltp - pos["entry"]) if bull else (pos["entry"] - ltp), 2)
        pos.update(exit=trigger, exit_price=round(ltp, 2), exit_time=str(now), points=pts)
        if OPT_MODE and "entry_premium" in pos:
            hours_held = max((now - dt.datetime.fromisoformat(pos["time"])).total_seconds() / 3600, 0)
            opt_pts = round(pts*DELTA - hours_held*THETA_HR - SPREAD, 2)
            exit_premium = max(0.0, round(pos["entry_premium"] + opt_pts, 2))
            cost = real_options_cost(pos["entry_premium"], exit_premium, QTY)
            proceeds = round(exit_premium * QTY - cost, 2)
            pnl_rs = round(proceeds - pos.get("capital_blocked", 0), 2)
            pos.update(opt_points=opt_pts, exit_premium=exit_premium, proceeds=proceeds,
                       real_cost=cost, hours_held=round(hours_held, 2), pnl_rs=pnl_rs)
            pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + proceeds, 2)
        else:
            pnl_rs = round(pts * QTY, 2)
            pos["pnl_rs"] = pnl_rs
            pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + pnl_rs, 2)
        pp["closed"].append(pos)
        del pp["open"][inst_name]
        save_paper(pp)
        st.success(f"{inst_name}: closed — {trigger} @ {round(ltp, 2)} · P&L Rs {pnl_rs:+,.0f}")'''

old2 = '''            cols_show = [x for x in ["instrument", "strategy", "dir", "type", "entry", "sl", "target",
                                      "exit", "exit_price", "exit_time", "points", "opt_points",
                                      "exit_premium", "real_cost", "proceeds"] if x in c.columns]
            color_cols = [x for x in ["points", "opt_points", "proceeds"] if x in cols_show]'''

new2 = '''            cols_show = [x for x in ["instrument", "strategy", "dir", "type", "entry", "sl", "target",
                                      "exit", "exit_price", "exit_time", "points", "pnl_rs", "opt_points",
                                      "exit_premium", "real_cost", "proceeds"] if x in c.columns]
            color_cols = [x for x in ["points", "pnl_rs", "opt_points", "proceeds"] if x in cols_show]'''

with open(PATH) as f:
    content = f.read()

n1, n2 = content.count(old1), content.count(old2)
if n1 != 1 or n2 != 1:
    print(f"WARNING: expected 1 match each, found {n1} and {n2}. Aborting.")
    raise SystemExit(1)
content = content.replace(old1, new1).replace(old2, new2)

import shutil
shutil.copy(PATH, PATH + ".bak_pnlcol")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- Closed trades table now shows the actual per-trade Rs P&L, color-coded.")
