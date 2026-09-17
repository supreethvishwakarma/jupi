PATH = "app.py"

old = '''        status.caption(f"Last checked {now:%d %b %H:%M:%S}" + (" · live" if live_on else " · paused"))

    live_panel()

    st.markdown("**Closed trades**")
    pp = load_paper()
    if pp["closed"]:
        c = pd.DataFrame(pp["closed"])
        tot = c.points.sum()
        m = st.columns(4)
        m[0].metric("Trades", len(c))
        m[1].metric("Win rate", f"{100*(c.points>0).mean():.0f}%")
        m[2].metric("Gross", f"{tot:+.1f} pts")
        m[3].metric(f"Net @ {COST_PTS}", f"Rs {(tot-COST_PTS*len(c))*LOT:+,.0f}")
        st.dataframe(c, use_container_width=True)
    else:
        st.caption("No closed paper trades yet.")'''

new = '''        status.caption(f"Last checked {now:%d %b %H:%M:%S}" + (" · live" if live_on else " · paused"))

        st.markdown("**Closed trades**")
        if pp["closed"]:
            c = pd.DataFrame(pp["closed"])
            tot = c.points.sum()
            m = st.columns(4)
            m[0].metric("Trades", len(c))
            m[1].metric("Win rate", f"{100*(c.points>0).mean():.0f}%")
            m[2].metric("Gross", f"{tot:+.1f} pts")
            m[3].metric(f"Net @ {COST_PTS}", f"Rs {(tot-COST_PTS*len(c))*LOT:+,.0f}")
            st.dataframe(c, use_container_width=True)
        else:
            st.caption("No closed paper trades yet.")

    live_panel()'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected exactly 1 match, found {n}. Paste your tab_paper section instead of patching blind.")
else:
    content = content.replace(old, new)
    with open(PATH, "w") as f:
        f.write(content)
    print("Patched -- closed trades table now lives inside the live fragment.")
