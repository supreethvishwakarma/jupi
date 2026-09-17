PATH = "app.py"

old = '''                        else:
                            live_price = opt_ltp if opt_ltp is not None else pos["entry"]
                            opt_pts = round(live_price - pos["entry"], 2)
                            pnl_rs = round(opt_pts * qty_i, 2)
                            c = st.columns(5)
                            c[0].metric("Option", pos.get("option_symbol", "-"))
                            c[1].metric("Entry premium", pos["entry"])
                            c[2].metric("LTP", live_price if opt_ltp is not None else "—")
                            c[3].metric("P&L (pts)", f"{opt_pts:+.2f}", delta=f"{opt_pts:+.2f}")
                            c[4].metric("P&L (Rs)", f"{pnl_rs:+,.0f}", delta=f"{pnl_rs:+,.0f}")
                            st.caption(f"Underlying: {pos.get('underlying_entry','-')} \\u2192 {ltp} · "
                                       f"SL(underlying) {pos['sl']} · Target(underlying) {pos['target']} · "
                                       f"blocked Rs {pos.get('capital_blocked', 0):,.0f}")'''

new = '''                        else:
                            live_price = opt_ltp if opt_ltp is not None else pos["entry"]
                            opt_pts = round(live_price - pos["entry"], 2)
                            pnl_rs = round(opt_pts * qty_i, 2)

                            _bid_now, _ask_now = get_bid_ask(option_exch, option_token)
                            if _bid_now is not None:
                                _net_cost = real_options_cost(pos["entry"], _bid_now, qty_i)
                                _net_proceeds = round(_bid_now * qty_i - _net_cost, 2)
                                _net_pnl = round(_net_proceeds - pos.get("capital_blocked", 0), 2)
                            else:
                                _net_pnl = None

                            c = st.columns(5)
                            c[0].metric("Option", pos.get("option_symbol", "-"))
                            c[1].metric("Entry premium", pos["entry"])
                            c[2].metric("LTP (mid)", live_price if opt_ltp is not None else "—")
                            c[3].metric("Mid P&L (pts)", f"{opt_pts:+.2f}", delta=f"{opt_pts:+.2f}")
                            c[4].metric("Mid P&L (Rs)", f"{pnl_rs:+,.0f}", delta=f"{pnl_rs:+,.0f}")
                            if _net_pnl is not None:
                                st.info(f"\\U0001F4B0 If you Square Off right now: **Rs {_net_pnl:+,.0f}** net "
                                        f"(real bid {_bid_now}, minus real spread + costs)")
                            st.caption(f"Underlying: {pos.get('underlying_entry','-')} \\u2192 {ltp} · "
                                       f"SL(underlying) {pos['sl']} · Target(underlying) {pos['target']} · "
                                       f"blocked Rs {pos.get('capital_blocked', 0):,.0f}")'''

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n != 1:
    print(f"WARNING: expected 1 match, found {n}. Aborting.")
    raise SystemExit(1)
content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_realisticpnl")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- open positions now show a realistic 'if you square off now' net P&L, not just the optimistic mid-price number.")
