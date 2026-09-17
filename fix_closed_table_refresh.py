PATH = "app.py"

old1 = '''        status_txt = "\\U0001F7E2 ticks live" if any_live else "\\U0001F7E1 waiting for ticks"
        st.caption(f"{status_txt} · checked {now:%H:%M:%S}" + ("" if live_on else " · paused"))

    fast_panel()'''

new1 = '''        status_txt = "\\U0001F7E2 ticks live" if any_live else "\\U0001F7E1 waiting for ticks"
        st.caption(f"{status_txt} · checked {now:%H:%M:%S}" + ("" if live_on else " · paused"))

        st.markdown("**Closed trades**")
        if pp["closed"]:
            c = pd.DataFrame(pp["closed"])
            tot = c.points.sum()
            realized = pp.get("balance", STARTING_CAPITAL) - STARTING_CAPITAL
            m = st.columns(5)
            m[0].metric("Trades", len(c))
            m[1].metric("Win rate", f"{100*(c.points>0).mean():.0f}%")
            m[2].metric("Gross", f"{tot:+.1f} pts")
            m[3].metric("Realized P&L", f"Rs {realized:+,.0f}", delta=f"{realized:+,.0f}")
            m[4].metric("Balance", f"Rs {pp.get('balance', STARTING_CAPITAL):,.0f}")
            cols_show = [x for x in ["instrument", "strategy", "dir", "type", "entry", "sl", "target",
                                      "exit", "exit_price", "exit_time", "points", "opt_points",
                                      "exit_premium", "real_cost", "proceeds"] if x in c.columns]
            color_cols = [x for x in ["points", "opt_points", "proceeds"] if x in cols_show]
            try:
                styled = c[cols_show].style.map(_pnl_color, subset=color_cols)
            except AttributeError:
                styled = c[cols_show].style.applymap(_pnl_color, subset=color_cols)
            st.dataframe(styled, use_container_width=True)
        else:
            st.caption("No closed paper trades yet.")

    fast_panel()'''

old2 = '''    slow_panel()

    st.markdown("**Closed trades**")
    pp = load_paper()
    if pp["closed"]:
        c = pd.DataFrame(pp["closed"])
        tot = c.points.sum()
        realized = pp.get("balance", STARTING_CAPITAL) - STARTING_CAPITAL
        m = st.columns(5)
        m[0].metric("Trades", len(c))
        m[1].metric("Win rate", f"{100*(c.points>0).mean():.0f}%")
        m[2].metric("Gross", f"{tot:+.1f} pts")
        m[3].metric("Realized P&L", f"Rs {realized:+,.0f}", delta=f"{realized:+,.0f}")
        m[4].metric("Balance", f"Rs {pp.get('balance', STARTING_CAPITAL):,.0f}")
        cols_show = [x for x in ["instrument", "strategy", "dir", "type", "entry", "sl", "target",
                                  "exit", "exit_price", "exit_time", "points", "opt_points",
                                  "exit_premium", "real_cost", "proceeds"] if x in c.columns]
        color_cols = [x for x in ["points", "opt_points", "proceeds"] if x in cols_show]
        try:
            styled = c[cols_show].style.map(_pnl_color, subset=color_cols)
        except AttributeError:
            styled = c[cols_show].style.applymap(_pnl_color, subset=color_cols)
        st.dataframe(styled, use_container_width=True)
    else:
        st.caption("No closed paper trades yet.")'''

new2 = '''    slow_panel()'''

with open(PATH) as f:
    content = f.read()

n1, n2 = content.count(old1), content.count(old2)
if n1 != 1 or n2 != 1:
    print(f"WARNING: expected 1 match each, found {n1} and {n2}. Aborting.")
    raise SystemExit(1)
content = content.replace(old1, new1).replace(old2, new2)

import shutil
shutil.copy(PATH, PATH + ".bak_closedrefresh")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- Closed trades table now lives inside the fast (1s) fragment, always fresh.")
