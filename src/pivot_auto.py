
import argparse, sys
import numpy as np
import pandas as pd


def fetch_klines(symbol="BTCUSDT", interval="6h", years=3, out="btc_6h.csv"):
    """Pull OHLCV from Binance in 1000-bar pages."""
    import time, urllib.request, json
    bars_per_year = {"6h": 1460, "4h": 2190, "12h": 730, "1d": 365}[interval]
    want = years * bars_per_year
    end = int(time.time() * 1000)
    rows = []
    while len(rows) < want:
        url = (f"https://api.binance.com/api/v3/klines?symbol={symbol}"
               f"&interval={interval}&limit=1000&endTime={end}")
        with urllib.request.urlopen(url, timeout=30) as r:
            batch = json.loads(r.read())
        if not batch:
            break
        rows = batch + rows
        end = batch[0][0] - 1
        print(f"  {len(rows)} bars...", end="\r")
        time.sleep(0.3)
    df = pd.DataFrame(rows, columns=[
        "open_time","open","high","low","close","volume",
        "close_time","qav","trades","tbav","tqav","ignore"])
    df = df[["open_time","open","high","low","close","volume"]]
    for c in ["open","high","low","close","volume"]:
        df[c] = df[c].astype(float)
    df["date"] = pd.to_datetime(df["open_time"], unit="ms")
    df = df.drop(columns=["open_time"]).drop_duplicates("date").sort_values("date")
    df.to_csv(out, index=False)
    print(f"\n{len(df)} bars -> {out}   ({df['date'].min().date()} to {df['date'].max().date()})")
    return df


def atr(df, length=14):
    h, l, c = df["high"], df["low"], df["close"].shift(1)
    tr = pd.concat([h - l, (h - c).abs(), (l - c).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/length, adjust=False).mean()


def find_pivots(df, atr_mult=3.0, atr_len=14, min_sep=2, span_bars=32, drop_target=3.5):
    """One row per qualified pivot, with its outcome fields.

    Mirrors the Pine indicator: 1-1 fractal, leg low = running low since the
    last qualified pivot, span runs until a CLOSE above the pivot high or
    span_bars, whichever comes first. Wicks count for max_up / max_drop.
    """
    df = df.reset_index(drop=True).copy()
    df["atr"] = atr(df, atr_len)
    high, low, close = df["high"].values, df["low"].values, df["close"].values
    atrv = df["atr"].values
    n = len(df)

    leg_lo_price, leg_lo_bar, leg_bars, q_hi_bar = np.nan, -1, 0, -1
    out = []
    for i in range(1, n - 1):
        is_fractal = high[i] > high[i-1] and high[i] > high[i+1]
        if is_fractal and not np.isnan(atrv[i]):
            sep_ok = q_hi_bar < 0 or (i - q_hi_bar) >= min_sep
            disp_ok = np.isnan(leg_lo_price) or (high[i] - leg_lo_price) >= atr_mult * atrv[i]
            order_ok = leg_lo_bar < 0 or leg_lo_bar < i
            if sep_ok and disp_ok and order_ok and not np.isnan(leg_lo_price):
                ref = high[i]
                gain = (ref - leg_lo_price) / leg_lo_price * 100
                mult = (ref - leg_lo_price) / atrv[i]
                hi_seen, lo_seen = ref, ref
                bars_held, bars_to_35 = np.nan, np.nan
                for k in range(1, span_bars + 1):
                    j = i + k
                    if j >= n:
                        break
                    hi_seen = max(hi_seen, high[j])
                    lo_seen = min(lo_seen, low[j])
                    if np.isnan(bars_to_35) and low[j] <= ref * (1 - drop_target/100):
                        bars_to_35 = k
                    if close[j] > ref:
                        bars_held = k
                        break
                out.append({
                    "date": df["date"].iloc[i], "bar": i,
                    "atr_mult": round(mult, 2), "gain": round(gain, 2),
                    "bars": leg_bars,
                    "max_up": round(max(hi_seen - ref, 0)/ref*100, 2),
                    "max_drop": round(max(ref - lo_seen, 0)/ref*100, 2),
                    "bars_held": bars_held, "bars_to_35": bars_to_35})
                leg_lo_price, leg_lo_bar, leg_bars = np.nan, -1, 0
                q_hi_bar = i
        if np.isnan(leg_lo_price) or low[i] < leg_lo_price:
            leg_lo_price, leg_lo_bar, leg_bars = low[i], i, 0
        else:
            leg_bars += 1
    return pd.DataFrame(out)


def add_regime(pivots, df, lookback=120):
    """Label each pivot by the prior `lookback` bars: net change over range.

    A trend spends most of its range going one way; a consolidation ends near
    where it started despite covering ground. Scale-free, volatility-adjusted.
    """
    regs = []
    for b in pivots["bar"]:
        w = df.iloc[max(0, b - lookback): b + 1]
        if len(w) < lookback // 2:
            regs.append("unknown"); continue
        net = w["close"].iloc[-1] - w["open"].iloc[0]
        span = w["high"].max() - w["low"].min()
        r = net / span if span else 0
        regs.append("up" if r > 0.5 else "down" if r < -0.5 else "consolidation")
    pivots = pivots.copy()
    pivots["regime"] = regs
    return pivots


def summarise(p, drop_target=3.5):
    from scipy import stats
    p = p.copy()
    p["held"] = p["bars_held"].isna()
    p["ratio"] = p["max_drop"] / p["gain"]
    p["span"] = p["bars_held"].fillna(32)
    print(f"\n{len(p)} pivots   {p['date'].min().date()} to {p['date'].max().date()}")
    print("=" * 68)
    print(f"  held the full span: {p['held'].sum()}/{len(p)} ({p['held'].mean()*100:.0f}%)")
    print(f"  reached -{drop_target}%:      {p['bars_to_35'].notna().sum()}/{len(p)} "
          f"({p['bars_to_35'].notna().mean()*100:.0f}%)")
    print("\n  THE TWO POPULATIONS")
    print("  " + "-"*64)
    print(f"  {'':<12}{'n':>5}{'med drop':>11}{'med ratio':>11}{'med up':>9}{'med gain':>10}")
    for lab, g in [("held", p[p["held"]]), ("failed", p[~p["held"]])]:
        if len(g):
            print(f"  {lab:<12}{len(g):>5}{g['max_drop'].median():>11.2f}"
                  f"{g['ratio'].median():>11.2f}{g['max_up'].median():>9.2f}"
                  f"{g['gain'].median():>10.2f}")
    if "regime" in p.columns:
        print("\n  HOLD RATE BY REGIME")
        print("  " + "-"*64)
        for r, g in p.groupby("regime"):
            print(f"  {r:<16}{len(g):>5} pivots   held {g['held'].mean()*100:>3.0f}%   "
                  f"med drop {g['max_drop'].median():>5.2f}%")
    print("\n  ADVERSE EXCURSION")
    print("  " + "-"*64)
    u = p["max_up"]
    print("  " + "   ".join(f"p{q}: {np.percentile(u,q):.2f}%" for q in (50,80,90,95)))
    print(f"  never traded above the pivot high: {(u==0).sum()}/{len(p)}")
    print("\n  SPAN CONFOUND CHECK")
    print("  " + "-"*64)
    rho, _ = stats.spearmanr(p["span"], p["max_drop"])
    print(f"  span vs max_drop: rho={rho:+.3f}  "
          f"-- max_drop is largely a restatement of survival time")
    return p


def sweep(df, mults=(1.5, 2.0, 2.5, 3.0, 4.0), **kw):
    print(f"\n{'mult':>6}{'pivots':>9}{'held %':>9}{'med gain':>11}"
          f"{'med drop':>11}{'held drop':>12}{'fail drop':>12}")
    print("-" * 70)
    for m in mults:
        p = find_pivots(df, atr_mult=m, **kw)
        if not len(p):
            continue
        h = p["bars_held"].isna()
        print(f"{m:>6.1f}{len(p):>9}{h.mean()*100:>8.0f}%{p['gain'].median():>11.2f}"
              f"{p['max_drop'].median():>11.2f}"
              f"{p[h]['max_drop'].median():>12.2f}{p[~h]['max_drop'].median():>12.2f}")
