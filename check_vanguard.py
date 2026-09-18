import os, datetime as dt
import pandas as pd
import pyotp
from dotenv import load_dotenv
from SmartApi import SmartConnect

load_dotenv()

def _wilder_rsi(close, period=9):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))

def _wma(series, period=21):
    weights = list(range(1, period + 1))
    return series.rolling(period).apply(lambda x: (x * weights).sum() / sum(weights), raw=True)

o = SmartConnect(api_key=os.environ["ANGEL_API_KEY"])
data = o.generateSession(os.environ["ANGEL_CLIENT_ID"], os.environ["ANGEL_PASSWORD"],
                          pyotp.TOTP(os.environ["ANGEL_TOTP"]).now())
if not data.get("status"):
    print("LOGIN FAILED:", data)
    raise SystemExit(1)

instruments = {
    "NIFTY 50": ("99926000", "NSE"),
    "NIFTY BANK": ("99926009", "NSE"),
}

now = dt.datetime.now()
frm = (now - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M")
to = now.strftime("%Y-%m-%d %H:%M")

for name, (token, exch) in instruments.items():
    res = o.getCandleData({
        "exchange": exch, "symboltoken": token, "interval": "FIVE_MINUTE",
        "fromdate": frm, "todate": to,
    })
    if not res.get("status"):
        print(f"{name}: FETCH FAILED: {res}")
        continue
    df = pd.DataFrame(res["data"], columns=["timestamp", "open", "high", "low", "close", "volume"])
    if len(df) < 22:
        print(f"{name}: only {len(df)} candles, not enough for RSI/WMA yet")
        continue
    close = df["close"].astype(float)
    r = _wilder_rsi(close, 9)
    w = _wma(r, 21)
    if pd.isna(r.iloc[-1]) or pd.isna(w.iloc[-1]):
        print(f"{name}: RSI/WMA still warming up (NaN)")
        continue
    gap = round(r.iloc[-1] - w.iloc[-1], 2)
    side = "above" if gap > 0 else "below"
    print(f"{name}: RSI {r.iloc[-1]:.2f} {side} WMA {w.iloc[-1]:.2f} (gap {gap:+.2f}) "
          f"-- candles={len(df)}, last close={close.iloc[-1]}")
