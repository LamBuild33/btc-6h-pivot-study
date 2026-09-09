"""
Swing lows — the mirror of pivot_auto.find_pivots.

The study tested swing highs only. This asks whether lows behave the same way,
and nothing else: structure only, no predictor testing. Re-mining eleven
predictors on the same data in the other direction is how a false positive gets
found, and the point of this file is a single pre-declared comparison.

PRE-DECLARED, before the first run:
    hold rate         27-33%   (highs gave 30.0%, band is +/- 3 points)
    confirmation lag  1.4-1.7% (highs gave 1.57%; structural, so this is a
                                check on the code rather than on the market)
    adverse excursion no prediction -- no basis for one

Every rule mirrors pivot_auto exactly:
    fractal        low[i] < low[i-1] and low[i] < low[i+1]
    leg            running HIGH since the last qualified low
    qualification  (leg_high - low[i]) >= atr_mult * ATR[i], min_sep bars apart
    span           until a CLOSE below the pivot low, or span_bars
    wicks          count for max_down / max_rise, as in the highs

COLUMN MAPPING against pivot_auto
    max_up   -> max_down   adverse excursion, now BELOW the pivot low
    max_drop -> max_rise   the favourable move, now upward
    gain     -> decline    the leg into the pivot, now a fall
Both adverse columns are positive numbers measuring distance the wrong way.
"""

import numpy as np
import pandas as pd

from pivot_auto import atr

__all__ = ["find_lows", "summarise_lows", "compare"]


def find_lows(df, atr_mult=3.0, atr_len=14, min_sep=2, span_bars=32,
              rise_target=3.5):
    """One row per qualified swing low, with its outcome fields."""
    df = df.reset_index(drop=True).copy()
    df["atr"] = atr(df, atr_len)
    high, low, close = df["high"].values, df["low"].values, df["close"].values
    atrv = df["atr"].values
    n = len(df)

    leg_hi_price, leg_hi_bar, leg_bars, q_lo_bar = np.nan, -1, 0, -1
    out = []
    for i in range(1, n - 1):
        is_fractal = low[i] < low[i - 1] and low[i] < low[i + 1]
        if is_fractal and not np.isnan(atrv[i]):
            sep_ok = q_lo_bar < 0 or (i - q_lo_bar) >= min_sep
            disp_ok = np.isnan(leg_hi_price) or (leg_hi_price - low[i]) >= atr_mult * atrv[i]
            order_ok = leg_hi_bar < 0 or leg_hi_bar < i
            if sep_ok and disp_ok and order_ok and not np.isnan(leg_hi_price):
                ref = low[i]
                decline = (leg_hi_price - ref) / leg_hi_price * 100
                mult = (leg_hi_price - ref) / atrv[i]
                hi_seen, lo_seen = ref, ref
                bars_held, bars_to_35 = np.nan, np.nan
                for k in range(1, span_bars + 1):
                    j = i + k
                    if j >= n:
                        break
                    hi_seen = max(hi_seen, high[j])
                    lo_seen = min(lo_seen, low[j])
                    if np.isnan(bars_to_35) and high[j] >= ref * (1 + rise_target / 100):
                        bars_to_35 = k
                    if close[j] < ref:
                        bars_held = k
                        break
                out.append({
                    "date": df["date"].iloc[i], "bar": i,
                    "atr_mult": round(mult, 2), "decline": round(decline, 2),
                    "bars": leg_bars,
                    "max_down": round(max(ref - lo_seen, 0) / ref * 100, 2),
                    "max_rise": round(max(hi_seen - ref, 0) / ref * 100, 2),
                    "lag_pct": round((close[i + 1] - ref) / ref * 100, 2),
                    "bars_held": bars_held, "bars_to_35": bars_to_35})
                leg_hi_price, leg_hi_bar, leg_bars = np.nan, -1, 0
                q_lo_bar = i
        if np.isnan(leg_hi_price) or high[i] > leg_hi_price:
            leg_hi_price, leg_hi_bar, leg_bars = high[i], i, 0
        else:
            leg_bars += 1
    return pd.DataFrame(out)


def summarise_lows(p, rise_target=3.5):
    """Same shape as pivot_auto.summarise, with the directions flipped."""
    from scipy import stats
    p = p.copy()
    p["held"] = p["bars_held"].isna()
    p["ratio"] = p["max_rise"] / p["decline"]
    p["span"] = p["bars_held"].fillna(32)
    print(f"\n{len(p)} swing lows   {p['date'].min().date()} to {p['date'].max().date()}")
    print("=" * 68)
    print(f"  held the full span: {p['held'].sum()}/{len(p)} ({p['held'].mean()*100:.0f}%)")
    print(f"  reached +{rise_target}%:      {p['bars_to_35'].notna().sum()}/{len(p)} "
          f"({p['bars_to_35'].notna().mean()*100:.0f}%)")
    print("\n  THE TWO POPULATIONS")
    print("  " + "-" * 64)
    print(f"  {'':<12}{'n':>5}{'med rise':>11}{'med ratio':>11}{'med down':>11}{'med decline':>13}")
    for lab, g in [("held", p[p["held"]]), ("failed", p[~p["held"]])]:
        if len(g):
            print(f"  {lab:<12}{len(g):>5}{g['max_rise'].median():>11.2f}"
                  f"{g['ratio'].median():>11.2f}{g['max_down'].median():>11.2f}"
                  f"{g['decline'].median():>13.2f}")
    if "regime" in p.columns:
        print("\n  HOLD RATE BY REGIME")
        print("  " + "-" * 64)
        for r, g in p.groupby("regime"):
            print(f"  {r:<16}{len(g):>5} lows   held {g['held'].mean()*100:>3.0f}%   "
                  f"med rise {g['max_rise'].median():>5.2f}%")
    print("\n  ADVERSE EXCURSION (below the pivot low)")
    print("  " + "-" * 64)
    u = p["max_down"]
    print("  " + "   ".join(f"p{q}: {np.percentile(u, q):.2f}%" for q in (50, 80, 90, 95)))
    print(f"  never traded below the pivot low: {(u == 0).sum()}/{len(p)}")
    print("\n  CONFIRMATION LAG")
    print("  " + "-" * 64)
    print(f"  mean {p['lag_pct'].mean():.2f}%  -- gone before the low is knowable")
    print("\n  SPAN CONFOUND CHECK")
    print("  " + "-" * 64)
    rho, _ = stats.spearmanr(p["span"], p["max_rise"])
    print(f"  span vs max_rise: rho={rho:+.3f}")
    return p


def compare(highs, lows, df):
    """The pre-declared comparison. Prints pass/fail against the two bands.

    `highs` comes from pivot_auto.find_pivots and has no lag column, so the
    confirmation lag is recomputed here from the price data the same way.
    """
    df = df.reset_index(drop=True)
    hi, cl = df["high"].values, df["close"].values
    h_held = highs["bars_held"].isna()
    l_held = lows["bars_held"].isna()
    h_lag = np.mean([(hi[int(b)] - cl[int(b) + 1]) / hi[int(b)] * 100
                     for b in highs["bar"] if int(b) + 1 < len(df)])

    rows = [
        ("n", len(highs), len(lows), ""),
        ("hold rate %", h_held.mean() * 100, l_held.mean() * 100, "27-33"),
        ("adverse p50 %", highs["max_up"].median(), lows["max_down"].median(), "none"),
        ("adverse p80 %", highs["max_up"].quantile(.8), lows["max_down"].quantile(.8), "none"),
        ("med move, held", highs[h_held]["max_drop"].median(),
         lows[l_held]["max_rise"].median(), ""),
        ("med move, failed", highs[~h_held]["max_drop"].median(),
         lows[~l_held]["max_rise"].median(), ""),
        ("confirm lag %", h_lag, lows["lag_pct"].mean(), "1.4-1.7"),
    ]
    print(f"{'':<20}{'highs':>10}{'lows':>10}{'predicted':>12}{'':>8}")
    print("-" * 60)
    for name, a, b, band in rows:
        verdict = ""
        if band == "27-33":
            verdict = "ok" if 27 <= b <= 33 else "MISS"
        elif band == "1.4-1.7":
            verdict = "ok" if 1.4 <= b <= 1.7 else "MISS"
        av = f"{a:>10.2f}" if isinstance(a, float) and np.isfinite(a) else f"{a:>10}"
        print(f"{name:<20}{av}{b:>10.2f}{band:>12}{verdict:>8}")
