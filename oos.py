from dotenv import load_dotenv; load_dotenv()
import os, time, pyotp, pandas as pd
from SmartApi import SmartConnect
import smc as m

obj = SmartConnect(api_key=os.environ["ANGEL_API_KEY"])
obj.generateSession(os.environ["ANGEL_CLIENT_ID"], os.environ["ANGEL_PASSWORD"],
                    pyotp.TOTP(os.environ["ANGEL_TOTP"]).now())

CHUNKS = [("2026-01-01 09:15","2026-02-28 15:30"),
          ("2026-03-01 09:15","2026-04-30 15:30"),
          ("2026-05-01 09:15","2026-05-31 15:30")]

parts = []
for a, b in CHUNKS:
    r = obj.getCandleData(dict(exchange="NSE", symboltoken="99926000",
                               interval="FIVE_MINUTE", fromdate=a, todate=b))
    parts.append(pd.DataFrame(r["data"],
                 columns=["timestamp","open","high","low","close","volume"]))
    print("got", a[:10], len(parts[-1]))
    time.sleep(3)                     # respect the rate limiter

df = pd.concat(parts).drop_duplicates("timestamp")
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)
df.to_pickle("nifty_oos.pkl")
print("OUT-OF-SAMPLE:", df.shape, df.timestamp.min(), "->", df.timestamp.max())

for sl, rr, sig in [(5,2.0,"CHoCH"), (5,1.5,"CHoCH"), (20,2.0,"BOS")]:
    m.SWING_LENGTH, m.RR, m.SIGNAL = sl, rr, sig
    _, s = m.get_signals(df)
    t = m.backtest(df, s)
    if not len(t):
        print(f"swing={sl} rr={rr} {sig}: no trades"); continue
    g = t.points.sum()
    print(f"swing={sl} rr={rr} {sig:5s} | n={len(t):3d} gross {g:+8.1f} "
          f"net2 {g-2*len(t):+8.1f} win {100*(t.points>0).mean():.0f}%")
