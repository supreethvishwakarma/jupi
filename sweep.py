from dotenv import load_dotenv; load_dotenv()
import itertools, pandas as pd
import smc as m

df = m.get_data().reset_index(drop=True)
rows = []
for sl, rr, sig in itertools.product([5,10,20,30,50], [1.0,1.5,2.0,3.0], ["CHoCH","BOS","both"]):
    m.SWING_LENGTH, m.RR, m.SIGNAL = sl, rr, sig
    _, s = m.get_signals(df)
    t = m.backtest(df, s)
    if len(t) < 5: continue
    g = t.points.sum(); h = len(t)//2
    rows.append(dict(swing=sl, rr=rr, sig=sig, n=len(t),
                     gross=round(g,1), net2=round(g-2*len(t),1),
                     win=round(100*(t.points>0).mean()),
                     h1=round(t.points[:h].sum(),1), h2=round(t.points[h:].sum(),1)))
r = pd.DataFrame(rows).sort_values("net2", ascending=False)
print(r.to_string(index=False))
print(f"\nprofitable after costs: {(r.net2>0).sum()} of {len(r)}")
print(f"and consistent (both halves +): {((r.net2>0)&(r.h1>0)&(r.h2>0)).sum()}")
