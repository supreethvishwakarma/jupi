from dotenv import load_dotenv
load_dotenv()
import os, pyotp, numpy as np, pandas as pd
from SmartApi import SmartConnect
from smartmoneyconcepts import smc

# ---------------- config ----------------
SWING_LENGTH = 10          # candles either side defining a swing
CLOSE_BREAK  = True        # break confirmed on close (False = wick)
SIGNAL       = "CHoCH"     # "CHoCH" | "BOS" | "both"
RR           = 2.0         # target = RR x risk
LOT          = 65
CACHE        = "nifty_5m.pkl"
FROM, TO     = "2026-06-01 09:15", "2026-09-10 15:30"
INTERVAL     = "FIVE_MINUTE"
TOKEN        = "99926000"  # NIFTY 50 index
EXCHANGE     = "NSE"

# ---------------- data ----------------
def get_data():
    if os.path.exists(CACHE):
        return pd.read_pickle(CACHE)
    obj = SmartConnect(api_key=os.environ["ANGEL_API_KEY"])
    obj.generateSession(os.environ["ANGEL_CLIENT_ID"],
                        os.environ["ANGEL_PASSWORD"],
                        pyotp.TOTP(os.environ["ANGEL_TOTP"]).now())
    r = obj.getCandleData(dict(exchange=EXCHANGE, symboltoken=TOKEN,
                               interval=INTERVAL, fromdate=FROM, todate=TO))
    df = pd.DataFrame(r["data"],
                      columns=["timestamp","open","high","low","close","volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.to_pickle(CACHE)
    return df

# ---------------- structure ----------------
def get_signals(df):
    ohlc = df[["open","high","low","close","volume"]].astype(float)
    swings = smc.swing_highs_lows(ohlc, swing_length=SWING_LENGTH)
    bc = smc.bos_choch(ohlc, swings, close_break=CLOSE_BREAK)

    sig = bc[bc.BOS.notna() | bc.CHOCH.notna()].copy()
    sig["type"] = np.where(sig.CHOCH.notna(), "CHoCH", "BOS")
    val = sig[["BOS","CHOCH"]].bfill(axis=1).iloc[:,0]
    sig["direction"] = np.where(val > 0, "bullish", "bearish")
    sig["broken_i"] = sig.BrokenIndex.astype(int)
    return swings, sig

# ---------------- backtest ----------------
def backtest(df, sig):
    use = sig if SIGNAL == "both" else sig[sig.type == SIGNAL]
    out = []
    for _, e in use.iterrows():
        i = e.broken_i + 1              # entry AFTER the break candle
        if i >= len(df): continue
        entry = df.loc[i,"open"]
        bull  = e.direction == "bullish"
        sl    = e.Level
        risk  = (entry - sl) if bull else (sl - entry)
        if risk <= 0: continue
        tgt = entry + RR*risk if bull else entry - RR*risk

        day, res, px, j = df.loc[i,"timestamp"].date(), None, None, i
        for j in range(i, len(df)):
            if df.loc[j,"timestamp"].date() != day: break
            h, l = df.loc[j,"high"], df.loc[j,"low"]
            if bull:
                if l <= sl:  res, px = "SL", sl; break
                if h >= tgt: res, px = "Target", tgt; break
            else:
                if h >= sl:  res, px = "SL", sl; break
                if l <= tgt: res, px = "Target", tgt; break
        if res is None: res, px = "EOD", df.loc[j,"close"]
        out.append(dict(time=df.loc[i,"timestamp"], dir=e.direction,
                        entry=entry, sl=sl, tgt=tgt, exit=res, px=px,
                        points=(px-entry) if bull else (entry-px), risk=risk))
    return pd.DataFrame(out)

# ---------------- report ----------------
def report(t):
    if not len(t):
        print("no trades"); return
    print(t.exit.value_counts().to_dict())
    g = t.points.sum()
    print(f"trades {len(t)} | gross {g:+.1f} pts | win {100*(t.points>0).mean():.0f}%")
    for c in (1,2,3,5):
        n = g - c*len(t)
        print(f"  cost {c} pts -> {n:+8.1f} pts = Rs {n*LOT:+10,.0f}")
    eq = t.points.cumsum()
    print(f"max drawdown {(eq-eq.cummax()).min():.1f} pts")
    h = len(t)//2
    print(f"first half {t.points[:h].sum():+.1f} | second half {t.points[h:].sum():+.1f}")
    print("both halves must be positive, else it's fitted to one period")

# ---------------- plot ----------------
def plot(df, swings, sig, days=7):
    import plotly.graph_objects as go
    m = df.timestamp >= df.timestamp.max() - pd.Timedelta(days=days)
    r = df[m]; sw = swings[m]
    fig = go.Figure(go.Candlestick(x=r.timestamp, open=r.open, high=r.high,
                                   low=r.low, close=r.close, name="NIFTY"))
    hi = r[sw.HighLow == 1]; lo = r[sw.HighLow == -1]
    fig.add_scatter(x=hi.timestamp, y=hi.high, mode="markers", name="swing high",
                    marker=dict(symbol="triangle-down", size=10, color="#c0392b"))
    fig.add_scatter(x=lo.timestamp, y=lo.low, mode="markers", name="swing low",
                    marker=dict(symbol="triangle-up", size=10, color="#27ae60"))
    for _, e in sig.iterrows():
        bt = df.loc[e.broken_i,"timestamp"]
        if bt in set(r.timestamp):
            fig.add_annotation(x=bt, y=e.Level, text=e.type, showarrow=True,
                               arrowhead=2, font=dict(size=9, color="white"),
                               bgcolor="#e67e22" if e.type=="CHoCH" else "#7f8c8d")
    fig.update_layout(height=650, xaxis_rangeslider_visible=False,
                      title=f"SWING_LENGTH={SWING_LENGTH}")
    fig.write_html("chart.html")
    print("wrote chart.html")

if __name__ == "__main__":
    df = get_data().reset_index(drop=True)
    print(df.shape, df.timestamp.min(), "->", df.timestamp.max())
    swings, sig = get_signals(df)
    print(sig.type.value_counts().to_dict())
    plot(df, swings, sig)
    report(backtest(df, sig))
