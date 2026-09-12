# Swing highs in BTC 6H price data: a null result and a structural cost

A hypothesis-testing project on observational time-series data. The question:
do any of a set of measurements predict which local price peaks resolve into
sustained declines? The answer is no, and most of the value is in how five
apparently significant results turned out to be confounded.

Three weeks, 615 automated observations plus 139 hand-logged, eleven predictors
tested, one hypothesis pre-declared before collection. Everything here is
reproducible from the committed data.

**The methods content, if that's what brings you here:** a pre-registered
hypothesis that failed its own test; six false positives traced to three
structural confounds, one of them caught prospectively; a look-ahead bias caught by an implausible win rate; and
a cross-check where two independent collection methods on two exchanges
returned the same figure to within half a percent. Section 3 of FINDINGS.md is
the part worth reading.

**The domain result, if you want it:** nothing measured — open interest, CVD,
volume, five price signals, threshold choice, position in the advance —
predicts which peaks hold. The best predictor found explains under 1% of the
variance. Traded at the first moment the signal is knowable, expectancy is
zero.

Two findings survive:

**A 30% hold rate that behaves like a constant.** 30% of qualified peaks are
real tops: price drops ~9.9% and retraces more than the whole prior advance.
The other 70% drop ~2.7% and continue. That split holds at 23/30/33/30% across
years, 30/29/26% across up/down/sideways regimes, 30–35% across detection
thresholds, and 29.5% hand-logged on Binance perp against 30.0% automated on
Coinbase spot — two independent measurements, median held-drop 9.93% and 9.91%.
Nothing predicts which population a peak lands in.

**A 1.57% confirmation lag.** A local peak cannot be identified until the next
bar closes, and that bar is lower by definition. By the time the signal exists,
price has already fallen a mean 1.57% from the peak — against a median 2.66%
total move on a peak that fails. Most of the effect is gone before it can be
acted on. This is a general property of any signal requiring confirmation, and
it is the most transferable finding here.

## Scoreboard

| tested | result |
|---|---|
| Open interest — five constructions, 51 legs, 2 batches | null |
| CVD change, leg volume | null once leg size controlled |
| Five price votes at pivots | null, and mostly redundant with each other |
| ATR threshold selecting better pivots | no — hold rate flat 1.5 to 4.0 |
| Sequence position within an advance | no — flips direction with the gap cut |
| Anything predicting which pivots hold | no — best is r = +0.083 |
| Swing lows vs highs — same behaviour? | yes, once drift is removed; gap non-significant in 12/12 cells |
| Pivot as a **short** signal | **zero expectancy**, −0.22% to 0.00% |
| Pivot as an **exit** signal | near-wash vs tight trailing stops, loses to holding |
| Lows vs highs reaching a small target | **+10 points for lows**, 23/23 cells — exploratory |
| Scaling the target by leg size | no improvement — helps in consolidation, hurts in downtrends |

## If you read one section, read §3 of FINDINGS.md

Five results looked significant and dissolved, all from two confounds: leg
size (any cumulative quantity scales with the leg, and bigger legs have
more room to fall) and measurement span (in the OI legs, which have no
window cap, one pivot survived 116 bars and another 2).

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
data/oi_legs_batch1.csv       21 hand-read OI legs, Feb-May 2026
data/oi_legs_batch2.csv       30 hand-read OI legs, Jul-Aug 2026
data/pivots_handlogged.csv    88 hand-logged pivots, Binance perp
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
version: the OI data is 51 hand-read legs, reproducible from the committed
files but not independently verifiable against an exchange API; no control group of random
entries was ever collected; the exit comparison ranks rules over a fixed
window but is not a full trade simulation (no re-entry, compounding, or
sizing); and everything here is 6H BTC, single instrument.

## Why publish a null result

One belief removed from a trading system on evidence rather than
preference, five false positives caught before they became rules, and a
pipeline that turns a multi-day hand-logging exercise into an afternoon.
The negatives are the product.
