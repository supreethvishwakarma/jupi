PATH = "app.py"

old1 = '''["Vanguard (RSI x WMA)", "Scalping (EMA+VWAP+RSI)", "Supertrend (Trailing SL)",
     "ATM Straddle (Time-based)"], index=0)'''

new1 = '''["Vanguard (RSI x WMA)", "Scalping (EMA+VWAP+RSI)", "Supertrend (Trailing SL)",
     "ATM Straddle (Time-based)", "Short Straddle (Selling, Time-based)"], index=0)'''

old2 = '''    def _close_straddle(pp, inst_name, pos, trigger, ce_exit, pe_exit, now, qty_i):
        ce_cost = real_options_cost(pos["ce_entry"], ce_exit, qty_i)
        pe_cost = real_options_cost(pos["pe_entry"], pe_exit, qty_i)
        total_cost = round(ce_cost + pe_cost, 2)
        proceeds = round((ce_exit + pe_exit) * qty_i - total_cost, 2)
        pnl_rs = round(proceeds - pos.get("capital_blocked", 0), 2)
        pos.update(exit=trigger, ce_exit=round(ce_exit, 2), pe_exit=round(pe_exit, 2),
                   exit_time=str(now), real_cost=total_cost, proceeds=proceeds, pnl_rs=pnl_rs,
                   points=round((ce_exit + pe_exit) - (pos["ce_entry"] + pos["pe_entry"]), 2))
        pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + proceeds, 2)
        pp["closed"].append(pos)
        del pp["open"][inst_name]
        save_paper(pp)
        st.success(f"{inst_name}: closed straddle ({pos.get('ce_symbol','')}+{pos.get('pe_symbol','')}) "
                   f"\\u2014 {trigger} \\u00b7 P&L Rs {pnl_rs:+,.0f}")'''

new2 = '''    def _close_straddle(pp, inst_name, pos, trigger, ce_exit, pe_exit, now, qty_i):
        ce_cost = real_options_cost(pos["ce_entry"], ce_exit, qty_i)
        pe_cost = real_options_cost(pos["pe_entry"], pe_exit, qty_i)
        total_cost = round(ce_cost + pe_cost, 2)
        proceeds = round((ce_exit + pe_exit) * qty_i - total_cost, 2)
        pnl_rs = round(proceeds - pos.get("capital_blocked", 0), 2)
        pos.update(exit=trigger, ce_exit=round(ce_exit, 2), pe_exit=round(pe_exit, 2),
                   exit_time=str(now), real_cost=total_cost, proceeds=proceeds, pnl_rs=pnl_rs,
                   points=round((ce_exit + pe_exit) - (pos["ce_entry"] + pos["pe_entry"]), 2))
        pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + proceeds, 2)
        pp["closed"].append(pos)
        del pp["open"][inst_name]
        save_paper(pp)
        st.success(f"{inst_name}: closed straddle ({pos.get('ce_symbol','')}+{pos.get('pe_symbol','')}) "
                   f"\\u2014 {trigger} \\u00b7 P&L Rs {pnl_rs:+,.0f}")

    def _get_margin_estimate(ce_token, pe_token, exch, qty):
        """Tries AngelOne's real Margin Calculator API for an accurate short-straddle
        margin figure; falls back to a conservative approximation if the live call
        fails for any reason (auth quirk, unexpected response shape, etc.). Returns
        (margin_rupees, is_real_bool)."""
        try:
            import requests as _requests
            o = broker()
            headers = {
                "Authorization": f"Bearer {getattr(o, 'access_token', '')}",
                "X-PrivateKey": os.environ["ANGEL_API_KEY"],
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "127.0.0.1",
                "X-MACAddress": "00:00:00:00:00:00",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            payload = {"positions": [
                {"exchange": exch, "qty": qty, "price": 0, "productType": "INTRADAY",
                 "token": str(ce_token), "tradeType": "SELL", "orderType": "MARKET"},
                {"exchange": exch, "qty": qty, "price": 0, "productType": "INTRADAY",
                 "token": str(pe_token), "tradeType": "SELL", "orderType": "MARKET"},
            ]}
            r = _requests.post(
                "https://apiconnect.angelbroking.com/rest/secure/angelbroking/margin/v1/batch",
                json=payload, headers=headers, timeout=5)
            data = r.json()
            total = (data.get("data") or {}).get("totalMarginRequired")
            if total is not None:
                return round(float(total), 2), True
        except Exception:
            pass
        approx = round(qty * 2200, 2)  # conservative fallback: ~Rs 2200/unit, roughly matches
        return approx, False           # real-world SEBI SPAN+exposure references we found

    def _close_short_straddle(pp, inst_name, pos, trigger, ce_buyback, pe_buyback, now, qty_i):
        ce_cost = real_options_cost(pos["ce_entry"], ce_buyback, qty_i)
        pe_cost = real_options_cost(pos["pe_entry"], pe_buyback, qty_i)
        total_cost = round(ce_cost + pe_cost, 2)
        buyback_paid = round((ce_buyback + pe_buyback) * qty_i, 2)
        premium_received = pos.get("premium_received",
                                    round((pos["ce_entry"] + pos["pe_entry"]) * qty_i, 2))
        pnl_rs = round(premium_received - buyback_paid - total_cost, 2)
        pos.update(exit=trigger, ce_exit=round(ce_buyback, 2), pe_exit=round(pe_buyback, 2),
                   exit_time=str(now), real_cost=total_cost, pnl_rs=pnl_rs,
                   points=round((pos["ce_entry"] + pos["pe_entry"]) - (ce_buyback + pe_buyback), 2))
        pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) + pos.get("capital_blocked", 0) + pnl_rs, 2)
        pp["closed"].append(pos)
        del pp["open"][inst_name]
        save_paper(pp)
        st.success(f"{inst_name}: closed short straddle ({pos.get('ce_symbol','')}+{pos.get('pe_symbol','')}) "
                   f"\\u2014 {trigger} \\u00b7 P&L Rs {pnl_rs:+,.0f}")'''

old3 = '''            if pos is not None and pos.get("mode") == "straddle":'''

new3 = '''            if pos is not None and pos.get("mode") == "short_straddle":
                ts.ensure_subscribed(pos["ce_exch"], pos["ce_token"])
                ts.ensure_subscribed(pos["pe_exch"], pos["pe_token"])
                ce_ltp = ts.get_ltp(pos["ce_token"])
                pe_ltp = ts.get_ltp(pos["pe_token"])
                _sqty = pos.get("qty", qty_i)
                if ce_ltp is None or pe_ltp is None:
                    st.caption("Short straddle open \\u2014 waiting for live option ticks...")
                else:
                    _combined_entry = pos["ce_entry"] + pos["pe_entry"]
                    _combined_now = ce_ltp + pe_ltp
                    _pct_change = round((_combined_entry - _combined_now) / _combined_entry * 100, 2)
                    _hit_target = _pct_change >= pos.get("target_pct", 30)
                    _hit_sl = _pct_change <= -pos.get("sl_pct", 30)
                    _sqoff = st.button(f"Square off short straddle {inst_name}", key=f"sqoff_ss_{inst_name}")
                    if _hit_target or _hit_sl or _sqoff:
                        _trigger = "Target" if _hit_target else "SL" if _hit_sl else "Manual"
                        _ce_bid, _ce_ask = get_bid_ask(pos["ce_exch"], pos["ce_token"])
                        _pe_bid, _pe_ask = get_bid_ask(pos["pe_exch"], pos["pe_token"])
                        _ce_buyback = _ce_ask if _ce_ask is not None else ce_ltp
                        _pe_buyback = _pe_ask if _pe_ask is not None else pe_ltp
                        _close_short_straddle(pp, inst_name, pos, _trigger, _ce_buyback, _pe_buyback, now, _sqty)
                    else:
                        c = st.columns(5)
                        c[0].metric("Combined entry (sold)", round(_combined_entry, 2))
                        c[1].metric("Combined now (buyback)", round(_combined_now, 2))
                        c[2].metric("Change (%)", f"{_pct_change:+.1f}%")
                        c[3].metric("CE", pos.get("ce_symbol", "-"))
                        c[4].metric("PE", pos.get("pe_symbol", "-"))
                        _margin_note = "real margin" if pos.get("margin_is_real") else "approx margin (live API unavailable)"
                        st.caption(f"Target {pos.get('target_pct',30)}% \\u00b7 SL {pos.get('sl_pct',30)}% \\u00b7 "
                                   f"{_margin_note}: Rs {pos.get('capital_blocked', 0):,.0f} \\u00b7 "
                                   f"premium received Rs {pos.get('premium_received', 0):,.0f} \\u00b7 "
                                   f"opened {pos.get('time','')}")
                continue

            if pos is not None and pos.get("mode") == "straddle":'''

old4 = '''            if STRATEGY == "ATM Straddle (Time-based)":'''

new4 = '''            if STRATEGY == "Short Straddle (Selling, Time-based)":
                if inst_name in pp["open"]:
                    continue
                _today_name = now.strftime("%A")
                if _today_name in STRADDLE_SKIP_DAYS:
                    continue
                if now.time() < STRADDLE_ENTRY_TIME:
                    continue
                _already_today = any(
                    c.get("instrument") == inst_name and c.get("signal_ts") == str(now.date())
                    for c in pp["closed"])
                if _already_today:
                    continue
                opt_cfg = get_option_config(inst_name)
                if opt_cfg is None:
                    continue
                prefix, search_exch, weekly_1letter, min_runway = opt_cfg
                spot_ltp = ts.get_ltp(tok)
                if spot_ltp is None:
                    continue
                chain = find_atm_option(prefix, search_exch, weekly_1letter,
                                         round(spot_ltp / 100) * 100, min_runway)
                if chain is None:
                    continue
                ce_bid, ce_ask = get_bid_ask(chain["exch"], chain["ce_token"])
                pe_bid, pe_ask = get_bid_ask(chain["exch"], chain["pe_token"])
                if ce_bid is None or pe_bid is None:
                    continue
                _qty_ss = INSTRUMENTS[inst_name][2] * LOTS_PER_INSTRUMENT.get(inst_name, 1)
                _margin_blocked, _margin_is_real = _get_margin_estimate(
                    chain["ce_token"], chain["pe_token"], chain["exch"], _qty_ss)
                new_short_straddle = dict(
                    status="open", mode="short_straddle", signal_ts=str(now.date()),
                    instrument=inst_name, strategy=STRATEGY, qty=_qty_ss,
                    ce_token=chain["ce_token"], ce_symbol=chain["ce_symbol"],
                    ce_entry=round(ce_bid, 2), ce_exch=chain["exch"],
                    pe_token=chain["pe_token"], pe_symbol=chain["pe_symbol"],
                    pe_entry=round(pe_bid, 2), pe_exch=chain["exch"],
                    capital_blocked=_margin_blocked, margin_is_real=_margin_is_real,
                    premium_received=round((ce_bid + pe_bid) * _qty_ss, 2), time=str(now),
                    target_pct=STRADDLE_TARGET_PCT, sl_pct=STRADDLE_SL_PCT)
                pp["balance"] = round(pp.get("balance", STARTING_CAPITAL) - _margin_blocked, 2)
                pp["open"][inst_name] = new_short_straddle
                save_paper(pp)
                any_opened = True
                continue

            if STRATEGY == "ATM Straddle (Time-based)":'''

with open(PATH, encoding="utf-8") as f:
    content = f.read()

results = []
for i, (old, new) in enumerate([(old1, new1), (old2, new2), (old3, new3), (old4, new4)], 1):
    n = content.count(old)
    results.append(n)
    if n != 1:
        print(f"WARNING patch {i}: expected 1 match, found {n}. Aborting.")
        raise SystemExit(1)
    content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_shortstraddle")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched -- Short Straddle (Selling) strategy added: entry, monitoring, exit, real margin API with fallback.")
