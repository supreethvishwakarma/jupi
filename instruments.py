"""Resolve AngelOne symbol tokens from the official scrip master."""
import json, os, time, urllib.request
import pandas as pd

URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
CACHE = "scripmaster.json"


def load(max_age_hours=24):
    if os.path.exists(CACHE) and time.time() - os.path.getmtime(CACHE) < max_age_hours * 3600:
        return json.load(open(CACHE))
    data = json.load(urllib.request.urlopen(URL, timeout=120))
    json.dump(data, open(CACHE, "w"))
    return data


def indices():
    """NIFTY / BANKNIFTY spot indices."""
    d = load()
    out = {}
    for m in d:
        if m.get("exch_seg") == "NSE" and m.get("name") in ("NIFTY", "BANKNIFTY") \
                and m.get("symbol", "").upper().endswith("INDEX"):
            out[m["name"]] = m["token"]
    return out


def mcx_futures(name="CRUDEOIL"):
    """Current and next MCX futures contracts, nearest expiry first."""
    d = load()
    rows = [m for m in d
            if m.get("exch_seg") == "MCX" and m.get("name") == name
            and m.get("instrumenttype", "").startswith("FUT")]
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["exp"] = pd.to_datetime(df.expiry, format="%d%b%Y", errors="coerce")
    df = df[df.exp >= pd.Timestamp.now().normalize()]
    return df.sort_values("exp")[["symbol", "token", "expiry", "lotsize"]]


if __name__ == "__main__":
    print("INDICES:", indices())
    print("\nCRUDEOIL futures:")
    print(mcx_futures().head().to_string(index=False))
