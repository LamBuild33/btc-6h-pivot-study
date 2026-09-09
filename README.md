# BTC 6H fractal pivots: a null result and a structural cost

Three weeks testing whether qualified swing highs on the 6-hour BTC chart
can be traded, or used as an exit, or predicted by anything.

**They can't.** Every stop/target combination tested lands between −0.22%
and 0.00% per trade before fees, across 615 pivots. Nothing measured —
open interest, CVD, volume, five price signals, ATR threshold, position in
the advance — predicts which pivots become real tops. The best predictor
found explains under 1% of the variance.

Two findings survive:

**A 30% hold rate that behaves like a constant.** 30% of qualified pivots
are real tops: price drops ~9% and retraces more than the whole prior leg.
The other 70% drop ~2.8% and continue. That split holds at 23/30/33/30%
across years, 30/29/26% across up/down/sideways regimes, 30–35% across ATR
thresholds 1.5 to 4.0, and 30% both hand-logged on Binance perp and
automated on Coinbase spot. Nothing predicts which population a pivot
lands in.

**A 1.57% confirmation lag.** A 1-1 fractal cannot be known until the next
bar closes, and that bar is lower by definition. By the time entry is
possible, price has already fallen a mean 1.57% from the pivot high —
against a median 2.66% drop on a pivot that fails. Most of the move is
gone before you can act. This applies to any signal on any instrument that
needs a bar to confirm, and it is the most transferable thing here.

## Scoreboard

| tested | result |
|---|---|
| Open interest — five constructions, 51 legs, 2 batches | null |
| CVD change, leg volume | null once leg size controlled |
| Five price votes at pivots | null, and mostly redundant with each other |
| ATR threshold selecting better pivots | no — hold rate flat 1.5 to 4.0 |
| Sequence position within an advance | no — flips direction with the gap cut |
| Anything predicting which pivots hold | no — best is r = +0.083 |
| Pivot as a **short** signal | **zero expectancy**, −0.22% to 0.00% |
| Pivot as an **exit** signal | near-wash vs tight trailing stops, loses to holding |

## If you read one section, read §3 of FINDINGS.md

Five results looked significant and dissolved, all from two confounds: leg
size (any cumulative quantity scales with the leg, and bigger legs have
more room to fall) and measurement span (a pivot that survives the full
32-bar window accumulates more drop than one invalidated after 2).

The part worth carrying elsewhere: **out-of-sample replication did not
catch either confound.** `cvd_change` replicated at r = +0.696 and +0.663
across independent batches and was still an artifact. Replication rules
out sampling noise, not bias — a structural confound reproduces faithfully
in every new sample. The check that worked was controlling for the
confounding variable directly.

## Running it

```bash
git clone https://github.com/LamBuild33/btc-6h-pivot-study
cd btc-6h-pivot-study
pip install -r requirements.txt
```

Then, from the repo root:

```python
import sys; sys.path.insert(0, "src")
import pandas as pd
from pivot_auto import find_pivots, add_regime, summarise, sweep
from exit_test import compare_exits, report

df = pd.read_csv("data/btc_6h.csv", parse_dates=["date"])

# atr_mult 1.5 rather than the 3.0 default: hold rate is flat across
# thresholds, so a higher setting costs 62% of the sample and buys nothing.
p = find_pivots(df, atr_mult=1.5)
p = add_regime(p, df)
p = summarise(p)          # two populations, hold rate, adverse excursion

sweep(df)                          # ATR sweep -- hold rate flat 1.5 to 4.0
report(compare_exits(df, p), p)    # the exit test
```

`data/btc_6h.csv` is the pinned dataset: 4,500 6H bars of BTC-USD spot,
2023-07-31 to 2026-08-28, pulled from Coinbase. Re-running `src/fetch.py` today
returns extra bars at the tail and slightly different pivot counts at the edge —
that's new data, not a reproducibility failure.

```
src/pivot_auto.py             pivot detection, regime tagging, threshold sweep
src/exit_test.py              alternative exit rules vs exiting at the pivot
src/fetch.py                  Coinbase pull (Binance returns 451 to US IPs)
data/btc_6h.csv               pinned 6H candles, 2023-07-31 to 2026-08-28
data/oi_legs_handlogged.csv   51 hand-read OI legs — see FINDINGS.md
FINDINGS.md                   the full record
```

## Robustness

The two surviving findings do not depend on how the pivot set is defined.

| swept | range | effect on n | hold rate | adverse p50 |
|---|---|---|---|---|
| ATR threshold | 1.5 – 4.0 | shrinks 62% | 30–35% | flat |

An independent reimplementation, written from FINDINGS.md without sight of
`pivot_auto.py`, reproduced hold rate at 28–30% and adverse p50 at 0.78–0.82%
across pivot separations of 3–8 bars and leg lookbacks of 15–60 bars, on the
same data. It arrived at a different pivot count (668 vs 615) because it
qualified pivots differently, and the structure was unchanged anyway.

That is on top of the original cross-check, where hand-logging on Binance perp
and automation on Coinbase spot both returned 30%.

## Limitations

Collected in one place in FINDINGS.md rather than scattered. The short
version: the OI data is 51 hand-read legs with no per-leg timestamps and
cannot be verified against an exchange API; no control group of random
entries was ever collected; the exit comparison ranks rules over a fixed
window but is not a full trade simulation (no re-entry, compounding, or
sizing); and everything here is 6H BTC, single instrument.

## Why publish a null result

One belief removed from a trading system on evidence rather than
preference, five false positives caught before they became rules, and a
pipeline that turns a multi-day hand-logging exercise into an afternoon.
The negatives are the product.
