"""
fetch.py — pull 6H BTC candles from Coinbase.

Binance returns HTTP 451 to US IPs. Coinbase serves them.

    from fetch import fetch_coinbase
    df = fetch_coinbase(out="data/btc_6h.csv")

The committed data/btc_6h.csv is the pinned dataset the findings were
computed on. Re-running this today returns extra bars at the tail and
slightly different pivot counts — that is not a reproducibility failure,
it is new data. Use the committed CSV to reproduce, this script to extend.
"""

import datetime as dt
import json
import time
import urllib.request

import pandas as pd

__all__ = ["fetch_coinbase"]


def fetch_coinbase(product="BTC-USD", granularity=21600, years=3,
                   out="data/btc_6h.csv"):
    """granularity in seconds: 21600 = 6h, 14400 = 4h, 86400 = 1d.
    Coinbase caps each request at 300 candles, so this pages backward."""
    want = int(years * 365 * 86400 / granularity)
    end = dt.datetime.now(dt.timezone.utc)
    rows = []
    while len(rows) < want:
        start = end - dt.timedelta(seconds=granularity * 300)
        url = (f"https://api.exchange.coinbase.com/products/{product}/candles"
               f"?granularity={granularity}"
               f"&start={start.isoformat()}&end={end.isoformat()}")
        req = urllib.request.Request(url, headers={"User-Agent": "python"})
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.loads(r.read())
        if not batch:
            break
        rows = batch + rows
        end = start
        print(f"  {len(rows)} bars...", end="\r")
        time.sleep(0.4)

    # Coinbase returns [time, low, high, open, close, volume]
    df = pd.DataFrame(rows, columns=["t", "low", "high", "open", "close", "volume"])
    df["date"] = pd.to_datetime(df["t"], unit="s")
    df = (df[["date", "open", "high", "low", "close", "volume"]]
          .drop_duplicates("date").sort_values("date").reset_index(drop=True))
    if out:
        df.to_csv(out, index=False)
        print(f"\n{len(df)} bars -> {out}")
    return df
