PATH = "app.py"

old = '''        _breakdown = {name: p.get("capital_blocked", 0) for name, p in pp["open"].items()
                      if p.get("status") == "open" and name in PAPER_INSTRUMENTS
                      and p.get("capital_blocked", 0) > 0}
        if _breakdown:
            st.caption("Capital utilization: " + " · ".join(
                f"{name}: Rs {amt:,.0f}" for name, amt in _breakdown.items()))'''

new = '''        _breakdown = {name: p.get("capital_blocked", 0) for name, p in pp["open"].items()
                      if p.get("status") == "open" and name in PAPER_INSTRUMENTS
                      and p.get("capital_blocked", 0) > 0}
        if _breakdown:
            st.caption("Capital utilization: " + " · ".join(
                f"{name}: Rs {amt:,.0f}" for name, amt in _breakdown.items()))

        if pp["closed"]:
            _cdf_daily = pd.DataFrame(pp["closed"])
            _cdf_daily["exit_date"] = _cdf_daily["exit_time"].apply(_safe_date)
            _cdf_daily = _cdf_daily.dropna(subset=["exit_date"])
            if not _cdf_daily.empty:
                _daily_grp = _cdf_daily.groupby("exit_date").agg(
                    trades=("pnl_rs", "count"),
                    win_rate=("pnl_rs", lambda s: round(100 * (s > 0).mean())),
                    day_pnl=("pnl_rs", "sum"),
                ).reset_index().sort_values("exit_date", ascending=False)
                _daily_grp["day_pnl"] = _daily_grp["day_pnl"].round(2)

                _today_row = _daily_grp[_daily_grp["exit_date"] == now.date()]
                _today_total = float(_today_row["day_pnl"].iloc[0]) if not _today_row.empty else 0.0
                _dm1, _dm2 = st.columns([1, 3])
                _dm1.metric("Today's P&L", f"Rs {_today_total:+,.0f}", delta=f"{_today_total:+,.0f}")

                with st.expander(f"Daily P&L history ({len(_daily_grp)} day(s))"):
                    _disp = _daily_grp.rename(columns={"exit_date": "Date", "trades": "Trades",
                                                        "win_rate": "Win %", "day_pnl": "Day P&L (Rs)"})
                    try:
                        _styled_daily = _disp.style.map(_pnl_color, subset=["Day P&L (Rs)"])
                    except AttributeError:
                        _styled_daily = _disp.style.applymap(_pnl_color, subset=["Day P&L (Rs)"])
                    st.dataframe(_styled_daily, use_container_width=True, hide_index=True)'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_dailypnldash")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- Today's P&L + full daily P&L history table added.")
