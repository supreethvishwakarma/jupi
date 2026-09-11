"""SMC Trading Dashboard — backtest, paper trade, live.

Run:  streamlit run app.py
Requires smc.py in the same folder.
"""
from dotenv import load_dotenv
load_dotenv()

import os, json, time, datetime as dt
import pandas as pd, numpy as np
import streamlit as st
import plotly.graph_objects as go
from smartmoneyconcepts import smc

st.set_page_config(page_title="SMC Dashboard", layout="wide")

PAPER_FILE = "paper_positions.json"
LOT = 65


# ---------------------------------------------------------------- broker
@st.cache_resource
def broker():
    import pyotp
    from SmartApi import SmartConnect
    o = SmartConnect(api_key=os.environ["ANGEL_API_KEY"])
    o.generateSession(os.environ["ANGEL_CLIENT_ID"],
                      os.environ["ANGEL_PASSWORD"],
                      pyotp.TOTP(os.environ["ANGEL_TOTP"]).now())
    return o


@st.cache_data(ttl=300, show_spinner="fetching candles…")
def fetch(frm, to, interval, token="99926000", exch="NSE"):
    r = broker().getCandleData(dict(exchange=exch, symboltoken=token,
                                    interval=interval, fromdate=frm, todate=to))
    df = pd.DataFrame(r["data"],
                      columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.reset_index(drop=True)


# ---------------------------------------------------------------- strategy
def signals(df, swing_length, close_break):
    ohlc = df[["open", "high", "low", "close", "volume"]].astype(float)
    sw = smc.swing_highs_lows(ohlc, swing_length=swing_length)
    bc = smc.bos_choch(ohlc, sw, close_break=close_break)
    s = bc[bc.BOS.notna() | bc.CHOCH.notna()].copy()
    if s.empty:
        return sw, s
    s["type"] = np.where(s.CHOCH.notna(), "CHoCH", "BOS")
    v = s[["BOS", "CHOCH"]].bfill(axis=1).iloc[:, 0]
    s["direction"] = np.where(v > 0, "bullish", "bearish")
    s["broken_i"] = s.BrokenIndex.astype(int)
    return sw, s


def run_backtest(df, sig, rr, which):
    use = sig if which == "both" else sig[sig.type == which]
    out = []
    for _, e in use.iterrows():
        i = e.broken_i + 1                       # entry AFTER the break
        if i >= len(df):
            continue
        entry = df.loc[i, "open"]
        bull = e.direction == "bullish"
        sl = e.Level
        risk = (entry - sl) if bull else (sl - entry)
        if risk <= 0:
            continue
        tgt = entry + rr * risk if bull else entry - rr * risk

        day, res, px, j = df.loc[i, "timestamp"].date(), None, None, i
        for j in range(i, len(df)):
            if df.loc[j, "timestamp"].date() != day:
                break
            h, l = df.loc[j, "high"], df.loc[j, "low"]
            if bull:
                if l <= sl:  res, px = "SL", sl; break
                if h >= tgt: res, px = "Target", tgt; break
            else:
                if h >= sl:  res, px = "SL", sl; break
                if l <= tgt: res, px = "Target", tgt; break
        if res is None:
            res, px = "EOD", df.loc[j, "close"]
        out.append(dict(time=df.loc[i, "timestamp"], dir=e.direction, type=e.type,
                        entry=round(entry, 2), sl=round(sl, 2), target=round(tgt, 2),
                        exit=res, exit_price=round(px, 2),
                        points=round((px - entry) if bull else (entry - px), 2),
                        risk=round(risk, 2)))
    return pd.DataFrame(out)


def chart(df, sw, sig, days, swing_length):
    m = df.timestamp >= df.timestamp.max() - pd.Timedelta(days=days)
    r, s = df[m], sw[m]
    f = go.Figure(go.Candlestick(x=r.timestamp, open=r.open, high=r.high,
                                 low=r.low, close=r.close, name="NIFTY"))
    hi, lo = r[s.HighLow == 1], r[s.HighLow == -1]
    f.add_scatter(x=hi.timestamp, y=hi.high, mode="markers", name="swing high",
                  marker=dict(symbol="triangle-down", size=10, color="#c0392b"))
    f.add_scatter(x=lo.timestamp, y=lo.low, mode="markers", name="swing low",
                  marker=dict(symbol="triangle-up", size=10, color="#27ae60"))
    if not sig.empty:
        for _, e in sig.iterrows():
            if e.broken_i < len(df):
                bt = df.loc[e.broken_i, "timestamp"]
                if bt in set(r.timestamp):
                    f.add_annotation(x=bt, y=e.Level, text=e.type, showarrow=True,
                                     arrowhead=2, font=dict(size=9, color="white"),
                                     bgcolor="#e67e22" if e.type == "CHoCH" else "#7f8c8d")
    f.update_layout(height=600, xaxis_rangeslider_visible=False,
                    margin=dict(t=30, b=20), title=f"SWING_LENGTH={swing_length}")
    return f


# ---------------------------------------------------------------- paper store
def load_paper():
    if os.path.exists(PAPER_FILE):
        return json.load(open(PAPER_FILE))
    return {"open": [], "closed": []}


def save_paper(d):
    json.dump(d, open(PAPER_FILE, "w"), indent=1, default=str)


# ---------------------------------------------------------------- sidebar
st.sidebar.header("Strategy")
SWING = st.sidebar.slider("Swing length", 3, 60, 20, 1,
                          help="Candles either side defining a swing. Tune this on the CHART, not the P&L.")
SIGNAL = st.sidebar.selectbox("Signal", ["BOS", "CHoCH", "both"], index=0)
RR = st.sidebar.slider("Risk : Reward", 0.5, 5.0, 2.0, 0.5)
CLOSE_BREAK = st.sidebar.checkbox("Confirm break on close", True)
INTERVAL = st.sidebar.selectbox("Interval",
                                ["ONE_MINUTE", "THREE_MINUTE", "FIVE_MINUTE", "FIFTEEN_MINUTE"], 2)
COST_PTS = st.sidebar.number_input("Cost per trade (points)", 0.0, 20.0, 2.0, 0.5,
                                   help="Brokerage + STT + slippage. Be pessimistic.")

st.sidebar.caption("Validated config: swing 20, BOS, RR 2.0 — the only one that "
                   "survived out-of-sample testing.")

tab_bt, tab_paper, tab_live = st.tabs(["Backtest", "Paper trading", "Live"])


# ---------------------------------------------------------------- backtest
with tab_bt:
    c1, c2 = st.columns(2)
    frm = c1.date_input("From", dt.date(2026, 6, 1))
    to = c2.date_input("To", dt.date(2026, 9, 10))

    if st.button("Run backtest", type="primary"):
        df = fetch(f"{frm} 09:15", f"{to} 15:30", INTERVAL)
        sw, sig = signals(df, SWING, CLOSE_BREAK)
        st.session_state.bt = (df, sw, sig, run_backtest(df, sig, RR, SIGNAL))

    if "bt" in st.session_state:
        df, sw, sig, t = st.session_state.bt
        st.caption(f"{len(df):,} candles · {df.timestamp.min():%d %b %Y} → {df.timestamp.max():%d %b %Y}")

        st.subheader("Structure")
        st.info("Check this first. If the triangles aren't on the highs and lows "
                "you'd pick by eye, change Swing length — the numbers below are "
                "meaningless until the structure looks right.")
        st.plotly_chart(chart(df, sw, sig, st.slider("Days shown", 2, 30, 7), SWING),
                        use_container_width=True)

        st.subheader("Results")
        if t.empty:
            st.warning("No trades for these settings.")
        else:
            gross = t.points.sum()
            net = gross - COST_PTS * len(t)
            h = len(t) // 2
            h1, h2 = t.points[:h].sum(), t.points[h:].sum()
            eq = t.points.cumsum()

            k = st.columns(5)
            k[0].metric("Trades", len(t))
            k[1].metric("Win rate", f"{100*(t.points>0).mean():.0f}%")
            k[2].metric("Gross", f"{gross:+.0f} pts")
            k[3].metric(f"Net @ {COST_PTS}", f"{net:+.0f} pts", f"Rs {net*LOT:+,.0f}")
            k[4].metric("Max DD", f"{(eq-eq.cummax()).min():.0f} pts")

            if h1 > 0 and h2 > 0:
                st.success(f"Both halves positive ({h1:+.0f} / {h2:+.0f}) — consistent so far.")
            else:
                st.error(f"First half {h1:+.0f}, second half {h2:+.0f}. "
                         "Only one half positive means this is fitted to that period, not an edge.")

            st.plotly_chart(go.Figure(go.Scatter(y=eq, mode="lines"))
                            .update_layout(height=260, title="Equity (points)",
                                           margin=dict(t=40, b=20)),
                            use_container_width=True)
            st.dataframe(t, use_container_width=True, height=300)


# ---------------------------------------------------------------- paper
with tab_paper:
    st.subheader("Paper trading")
    st.caption("Simulated fills at candle prices. No orders are sent anywhere.")

    pp = load_paper()
    a, b = st.columns([1, 1])

    if a.button("Check for signals now", type="primary"):
        end = dt.datetime.now()
        df = fetch((end - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
                   end.strftime("%Y-%m-%d %H:%M"), INTERVAL)
        sw, sig = signals(df, SWING, CLOSE_BREAK)
        use = sig if SIGNAL == "both" else sig[sig.type == SIGNAL]

        # manage open positions against latest candles
        still = []
        for p in pp["open"]:
            after = df[df.timestamp > pd.to_datetime(p["time"])]
            done = False
            for _, c in after.iterrows():
                bull = p["dir"] == "bullish"
                hit_sl = c.low <= p["sl"] if bull else c.high >= p["sl"]
                hit_tg = c.high >= p["target"] if bull else c.low <= p["target"]
                if hit_sl or hit_tg:
                    px = p["sl"] if hit_sl else p["target"]
                    p.update(exit="SL" if hit_sl else "Target", exit_price=px,
                             exit_time=str(c.timestamp),
                             points=round((px - p["entry"]) if bull else (p["entry"] - px), 2))
                    pp["closed"].append(p); done = True; break
            if not done:
                still.append(p)
        pp["open"] = still

        # open new ones
        known = {p["time"] for p in pp["open"]} | {p["time"] for p in pp["closed"]}
        for _, e in use.iterrows():
            i = e.broken_i + 1
            if i >= len(df):
                continue
            ts = str(df.loc[i, "timestamp"])
            if ts in known:
                continue
            entry, bull, sl = df.loc[i, "open"], e.direction == "bullish", e.Level
            risk = (entry - sl) if bull else (sl - entry)
            if risk <= 0:
                continue
            pp["open"].append(dict(time=ts, dir=e.direction, type=e.type,
                                   entry=round(entry, 2), sl=round(sl, 2),
                                   target=round(entry + RR*risk if bull else entry - RR*risk, 2)))
        save_paper(pp)
        st.rerun()

    if b.button("Reset paper account"):
        save_paper({"open": [], "closed": []}); st.rerun()

    st.markdown("**Open**")
    st.dataframe(pd.DataFrame(pp["open"]) if pp["open"] else pd.DataFrame(),
                 use_container_width=True)

    st.markdown("**Closed**")
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


# ---------------------------------------------------------------- live
with tab_live:
    st.subheader("Live trading")
    st.error("**Not enabled.** This strategy has one out-of-sample result behind it. "
             "That is not enough evidence to risk money.")

    st.markdown("""
Before wiring real orders, all of these should be true:

- **Several months of paper trading** on the Paper tab, with results that match
  the backtest. If paper and backtest disagree, the backtest is wrong.
- **Walk-forward validation**, not just the single split already run.
- **Costs measured, not estimated** — from your actual AngelOne contract notes.
- **A daily loss limit you will not override.** Decide it now, while nothing is
  at stake.

If all of that holds, order placement goes here — `obj.placeOrder(...)`. It's
deliberately not written yet, because an untested strategy with a working order
button is how accounts get damaged.
    """)
    st.caption("Ask me to add order placement once the paper results are in.")
