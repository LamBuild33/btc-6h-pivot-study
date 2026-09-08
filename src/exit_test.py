
"""
Exit comparison.

You are already long. A pivot has just confirmed. Does closing here beat the
rules you would otherwise have used?

No control group needed and no spread to overcome -- this compares decision
rules against each other over the identical window, which is a much lower bar
than the shorting test that came back at zero.
"""
import numpy as np
import pandas as pd


def compare_exits(df, pivots, horizon=32, trail_pcts=(2, 3, 5),
                  hold_bars=(8, 16, 32), target_pcts=(3, 5)):
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    rows = []

    for b in pivots["bar"]:
        b = int(b)
        ei = b + 1                       # confirming bar: earliest exit
        if ei + horizon >= n:
            continue
        entry_ref = c[ei]                # what exiting at confirmation gets
        r = {"bar": b, "pivot_exit": 0.0}   # baseline, by definition

        # Trailing stop from the pivot high
        for t in trail_pcts:
            peak = h[b]
            out = None
            for k in range(1, horizon + 1):
                j = ei + k
                peak = max(peak, h[j])
                if l[j] <= peak * (1 - t / 100):
                    out = peak * (1 - t / 100)
                    break
            if out is None:
                out = c[ei + horizon]
            r[f"trail_{t}"] = (out - entry_ref) / entry_ref * 100

        # Hold a fixed number of bars, then exit at the close
        for k in hold_bars:
            r[f"hold_{k}"] = (c[ei + k] - entry_ref) / entry_ref * 100

        # Take profit at a fixed target above the confirming close
        for t in target_pcts:
            lvl = entry_ref * (1 + t / 100)
            out = None
            for k in range(1, horizon + 1):
                j = ei + k
                if h[j] >= lvl:
                    out = lvl
                    break
            if out is None:
                out = c[ei + horizon]
            r[f"target_{t}"] = (out - entry_ref) / entry_ref * 100

        rows.append(r)

    return pd.DataFrame(rows)


def report(res, pivots):
    cols = [c for c in res.columns if c != "bar"]
    print(f"n = {len(res)} pivots")
    print("Every figure is % relative to exiting at pivot confirmation.")
    print("Positive means the alternative beat the pivot exit.\n")
    print(f"{'rule':<14}{'mean':>9}{'median':>9}{'worst':>9}{'best':>9}{'beat pivot':>13}")
    print("-" * 63)
    for col in cols:
        v = res[col]
        print(f"{col:<14}{v.mean():>+9.2f}{v.median():>+9.2f}{v.min():>+9.2f}"
              f"{v.max():>+9.2f}{(v > 0).mean()*100:>12.0f}%")

    held = pivots.set_index("bar")["bars_held"].isna()
    res = res.assign(held=res["bar"].map(held))
    print("\nSplit by whether the pivot held the span")
    print("-" * 63)
    print(f"{'rule':<14}{'held (30%)':>14}{'failed (70%)':>16}")
    for col in cols:
        a = res[res["held"]][col].mean()
        b = res[~res["held"]][col].mean()
        print(f"{col:<14}{a:>+14.2f}{b:>+16.2f}")
