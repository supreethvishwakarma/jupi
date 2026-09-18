PATH = "app.py"

old1 = '''    def _close_position(pp, inst_name, pos, trigger, exit_premium, now, qty_i):
        entry_premium = pos["entry"]
        opt_pts = round(exit_premium - entry_premium, 2)
        cost = real_options_cost(entry_premium, exit_premium, qty_i)
        proceeds = round(exit_premium * qty_i - cost, 2)
        pnl_rs = round(proceeds - pos.get("capital_blocked", 0), 2)
        pos.update(exit=trigger, exit_price=round(exit_premium, 2), exit_time=str(now),
                   points=opt_pts, real_cost=cost, proceeds=proceeds, pnl_rs=pnl_rs)
        pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + proceeds, 2)
        pp["closed"].append(pos)
        del pp["open"][inst_name]
        save_paper(pp)
        st.success(f"{inst_name}: closed {pos.get('option_symbol', '')} \u2014 {trigger} "
                   f"@ Rs {round(exit_premium, 2)} \u00b7 P&L Rs {pnl_rs:+,.0f}")'''

new1 = '''    def _close_position(pp, inst_name, pos, trigger, exit_premium, now, qty_i):
        entry_premium = pos["entry"]
        opt_pts = round(exit_premium - entry_premium, 2)
        cost = real_options_cost(entry_premium, exit_premium, qty_i)
        proceeds = round(exit_premium * qty_i - cost, 2)
        pnl_rs = round(proceeds - pos.get("capital_blocked", 0), 2)
        pos.update(exit=trigger, exit_price=round(exit_premium, 2), exit_time=str(now),
                   points=opt_pts, real_cost=cost, proceeds=proceeds, pnl_rs=pnl_rs)
        pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + proceeds, 2)
        pp["closed"].append(pos)
        del pp["open"][inst_name]
        save_paper(pp)
        st.success(f"{inst_name}: closed {pos.get('option_symbol', '')} \u2014 {trigger} "
                   f"@ Rs {round(exit_premium, 2)} \u00b7 P&L Rs {pnl_rs:+,.0f}")

    def _atr(df, period=14):
        high, low, close = df["high"].astype(float), df["low"].astype(float), df["close"].astype(float)
        prev_close = close.shift(1)
        tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
        return tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()'''

old2 = '''                else:
                    sl = pos["sl"]
                    risk = (ltp - sl) if bull else (sl - ltp)'''

new2 = '''                else:
                    qty_i = pos.get("qty", qty_i)
                    sl = pos["sl"]
                    risk = (ltp - sl) if bull else (sl - ltp)'''

old3 = '''                else:
                    option_token = pos["option_token"]'''

new3 = '''                else:
                    qty_i = pos.get("qty", qty_i)
                    option_token = pos["option_token"]'''

old4 = '''                        hit_sl = ltp <= pos["sl"] if bull else ltp >= pos["sl"]
                        hit_tg = ltp >= pos["target"] if bull else ltp <= pos["target"]
                        sqoff = st.button(f"Square off {inst_name}", key=f"sqoff_{inst_name}")
                        if hit_sl or hit_tg or sqoff:
                            trigger = ("SL" if hit_sl else "Target") if (hit_sl or hit_tg) else "Manual"
                            bid, ask = get_bid_ask(option_exch, option_token)
                            exit_premium = bid if bid is not None else opt_ltp
                            if exit_premium is None:
                                st.warning(f"{pos.get('option_symbol','')}: no live price yet, will retry next cycle.")
                            else:
                                _close_position(pp, inst_name, pos, trigger, exit_premium, now, qty_i)'''

new4 = '''                        hit_sl = ltp <= pos["sl"] if bull else ltp >= pos["sl"]
                        hit_tg = ltp >= pos["target"] if bull else ltp <= pos["target"]

                        hit_profit_lock = False
                        if pos.get("strategy") == "Vanguard (RSI x WMA)":
                            _plb, _pla = get_bid_ask(option_exch, option_token)
                            if _plb is not None:
                                _pl_cost = real_options_cost(pos["entry"], _plb, qty_i)
                                _pl_pnl = round(_plb * qty_i - _pl_cost - pos.get("capital_blocked", 0), 2)
                                pos["peak_pnl"] = max(pos.get("peak_pnl", 0), _pl_pnl)
                                if pos["peak_pnl"] >= 1000:
                                    _profit_floor = max(1000, pos["peak_pnl"] - 500)
                                    if _pl_pnl <= _profit_floor:
                                        hit_profit_lock = True

                        sqoff = st.button(f"Square off {inst_name}", key=f"sqoff_{inst_name}")
                        if hit_sl or hit_tg or hit_profit_lock or sqoff:
                            trigger = ("Profit-Lock" if hit_profit_lock else
                                       "SL" if hit_sl else "Target" if hit_tg else "Manual")
                            bid, ask = get_bid_ask(option_exch, option_token)
                            exit_premium = bid if bid is not None else opt_ltp
                            if exit_premium is None:
                                st.warning(f"{pos.get('option_symbol','')}: no live price yet, will retry next cycle.")
                            else:
                                _close_position(pp, inst_name, pos, trigger, exit_premium, now, qty_i)'''

old5 = '''            if is_fresh and ts_sig not in seen:
                entry_close = float(chart_df.iloc[-1].close)
                new_pos = dict(status="pending_entry", signal_ts=ts_sig,
                                instrument=inst_name, strategy=STRATEGY,
                                dir=last_sig.direction,
                                type=last_sig.type, sl=round(float(last_sig.Level), 2),
                                placed_time=str(now))'''

new5 = '''            if is_fresh and ts_sig not in seen:
                entry_close = float(chart_df.iloc[-1].close)
                _base_qty = INSTRUMENTS[inst_name][2] * LOTS_PER_INSTRUMENT.get(inst_name, 1)
                _qty_for_trade = _base_qty
                if STRATEGY == "Vanguard (RSI x WMA)":
                    _atr_series = _atr(chart_df)
                    if len(_atr_series.dropna()) >= 21:
                        _cur_atr = _atr_series.iloc[-1]
                        _avg_atr = _atr_series.iloc[-21:-1].mean()
                        if (not pd.isna(_cur_atr) and not pd.isna(_avg_atr) and _avg_atr > 0
                                and _cur_atr >= 1.2 * _avg_atr):
                            _qty_for_trade = _base_qty * 2
                new_pos = dict(status="pending_entry", signal_ts=ts_sig,
                                instrument=inst_name, strategy=STRATEGY,
                                dir=last_sig.direction, qty=_qty_for_trade,
                                type=last_sig.type, sl=round(float(last_sig.Level), 2),
                                placed_time=str(now))'''

with open(PATH, encoding="utf-8") as f:
    content = f.read()

results = []
for i, (old, new) in enumerate([(old1, new1), (old2, new2), (old3, new3), (old4, new4), (old5, new5)], 1):
    n = content.count(old)
    results.append((i, n))
    if n != 1:
        print(f"WARNING patch {i}: expected 1 match, found {n}. Aborting.")
        raise SystemExit(1)
    content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_vanguardcomplete")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched -- volatility sizing, qty consistency (both fill points), and profit-lock (floor=max(1000,peak-500)) all applied.")
