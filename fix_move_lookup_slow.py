PATH = "app.py"

old1 = '''            if is_fresh and ts_sig not in seen:
                pp["open"][inst_name] = dict(status="pending_entry", signal_ts=ts_sig,
                                              instrument=inst_name, strategy=STRATEGY,
                                              dir=last_sig.direction,
                                              type=last_sig.type, sl=round(float(last_sig.Level), 2),
                                              placed_time=str(now))
                save_paper(pp)
                any_opened = True'''

new1 = '''            if is_fresh and ts_sig not in seen:
                entry_close = float(chart_df.iloc[-1].close)
                new_pos = dict(status="pending_entry", signal_ts=ts_sig,
                                instrument=inst_name, strategy=STRATEGY,
                                dir=last_sig.direction,
                                type=last_sig.type, sl=round(float(last_sig.Level), 2),
                                placed_time=str(now))
                opt_cfg = get_option_config(inst_name)
                if opt_cfg is not None:
                    prefix, search_exch, weekly_1letter = opt_cfg
                    chain = find_atm_option(prefix, search_exch, weekly_1letter, round(entry_close/100)*100)
                    if chain is not None:
                        bull = last_sig.direction == "bullish"
                        new_pos["option_token"] = chain["ce_token"] if bull else chain["pe_token"]
                        new_pos["option_symbol"] = chain["ce_symbol"] if bull else chain["pe_symbol"]
                        new_pos["option_exch"] = chain["exch"]
                pp["open"][inst_name] = new_pos
                save_paper(pp)
                any_opened = True'''

old2 = '''            if pos["status"] == "pending_entry":
                st.caption(f"Order pending — entry. {pos['dir'].capitalize()} {pos['type']} "
                           f"signal placed {pos['placed_time']}, finding the option & filling…")
                bull = pos["dir"] == "bullish"
                if ltp is None:
                    st.warning("No underlying live tick yet — entry still pending.")
                elif opt_cfg is None:
                    sl = pos["sl"]
                    risk = (ltp - sl) if bull else (sl - ltp)
                    if risk <= 0:
                        pp["ignored"].append(f"{inst_name}|{pos['signal_ts']}")
                        del pp["open"][inst_name]
                        save_paper(pp)
                        st.warning("Entry cancelled — price moved past the stop before the order could fill.")
                    else:
                        pos.update(status="open", mode="raw", entry=round(ltp, 2), time=str(now),
                                   target=round(ltp + RR*risk if bull else ltp - RR*risk, 2))
                        save_paper(pp)
                        st.success(f"Filled at {round(ltp, 2)} (raw underlying -- no option chain configured)")
                else:
                    prefix, search_exch, weekly_1letter = opt_cfg
                    chain = find_atm_option(prefix, search_exch, weekly_1letter, round(ltp/100)*100)
                    if chain is None:
                        st.warning("Couldn't look up the option chain yet -- retrying next cycle.")
                    else:
                        opt_token = chain["ce_token"] if bull else chain["pe_token"]
                        opt_symbol = chain["ce_symbol"] if bull else chain["pe_symbol"]
                        ts.ensure_subscribed(chain["exch"], opt_token)
                        bid, ask = get_bid_ask(chain["exch"], opt_token)
                        if ask is None:
                            st.warning(f"No live price yet for {opt_symbol} -- entry still pending.")
                        else:
                            sl = pos["sl"]
                            risk = (ltp - sl) if bull else (sl - ltp)
                            if risk <= 0:
                                pp["ignored"].append(f"{inst_name}|{pos['signal_ts']}")
                                del pp["open"][inst_name]
                                save_paper(pp)
                                st.warning("Entry cancelled -- underlying price moved past the stop before the order could fill.")
                            else:
                                target = round(ltp + RR*risk if bull else ltp - RR*risk, 2)
                                capital_blocked = round(ask * qty_i, 2)
                                pos.update(status="open", mode="option", entry=round(ask, 2),
                                           option_token=opt_token, option_symbol=opt_symbol,
                                           option_exch=chain["exch"], underlying_entry=round(ltp, 2),
                                           sl=sl, target=target, capital_blocked=capital_blocked,
                                           time=str(now))
                                pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) - capital_blocked, 2)
                                save_paper(pp)
                                st.success(f"Bought {opt_symbol} at Rs {round(ask, 2)} (real ask) "
                                           f"· Rs {capital_blocked:,.0f} blocked")'''

new2 = '''            if pos["status"] == "pending_entry":
                st.caption(f"Order pending — entry. {pos['dir'].capitalize()} {pos['type']} "
                           f"signal placed {pos['placed_time']}, filling on next tick.")
                bull = pos["dir"] == "bullish"
                has_option = "option_token" in pos
                fill_price = None
                if has_option:
                    ts.ensure_subscribed(pos["option_exch"], pos["option_token"])
                    _bid, fill_price = get_bid_ask(pos["option_exch"], pos["option_token"])
                elif ltp is not None:
                    fill_price = ltp

                if ltp is None:
                    st.warning("No underlying live tick yet — entry still pending.")
                elif has_option and fill_price is None:
                    st.warning(f"No live price yet for {pos.get('option_symbol', 'the option')} -- entry still pending.")
                else:
                    sl = pos["sl"]
                    risk = (ltp - sl) if bull else (sl - ltp)
                    if risk <= 0:
                        pp["ignored"].append(f"{inst_name}|{pos['signal_ts']}")
                        del pp["open"][inst_name]
                        save_paper(pp)
                        st.warning("Entry cancelled — price moved past the stop before the order could fill.")
                    else:
                        target = round(ltp + RR*risk if bull else ltp - RR*risk, 2)
                        if has_option:
                            capital_blocked = round(fill_price * qty_i, 2)
                            pos.update(status="open", entry=round(fill_price, 2),
                                       underlying_entry=round(ltp, 2), sl=sl, target=target,
                                       capital_blocked=capital_blocked, time=str(now))
                            pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) - capital_blocked, 2)
                            save_paper(pp)
                            st.success(f"Bought {pos['option_symbol']} at Rs {round(fill_price, 2)} (real ask) "
                                       f"· Rs {capital_blocked:,.0f} blocked")
                        else:
                            pos.update(status="open", mode="raw", entry=round(ltp, 2), time=str(now),
                                       target=target)
                            save_paper(pp)
                            st.success(f"Filled at {round(ltp, 2)} (raw underlying -- no option chain configured)")'''

with open(PATH) as f:
    content = f.read()

n1, n2 = content.count(old1), content.count(old2)
if n1 != 1 or n2 != 1:
    print(f"WARNING: expected 1 match each, found {n1} and {n2}. Aborting.")
    raise SystemExit(1)
content = content.replace(old1, new1).replace(old2, new2)

import shutil
shutil.copy(PATH, PATH + ".bak_movelookup")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- option chain lookup now happens in the slow (60s) loop; fast loop only does cheap per-token quotes.")
