# BTC 6H Pivot & Open Interest Study — Findings

Record of what was tested, what was found, and why the negative results are
trustworthy. Written so that future-you does not re-run any of it by accident.

**Instrument:** BTCUSDT.P (hand-logged) and BTC-USD spot (automated), 6H
**Automated pivots:** 2023-07-31 to 2026-08-28, 4,500 bars, 615 pivots
**Hand-logged pivots:** 88
**Hand-logged OI legs:** 51, sampled from two 2026 batches — see the note in
section 1. This is a six-month window inside the automated period, not three
years of OI coverage.

---

## The headline

**A qualified swing high on 6H BTC has zero expectancy when traded at the first
moment it is knowable.** Every stop/target combination tested landed between
−0.22% and 0.00% per trade, before fees, across 615 pivots.

The reason is a **1.57% confirmation lag**. A 1-1 fractal is only confirmed once
the next bar closes, and that bar is lower by definition. By the time you can
act, price has already fallen 1.57% on average from the pivot high — against a
median drop of 2.79% on a failed pivot. Most of the move is gone before entry
is possible.

**Open interest does not predict swing-high outcomes.** Five constructions,
51 legs, two batches including one that ended in a 30% cascade. All null.

## 1. What was tested and what happened

| Question | Result |
|---|---|
| Does OI change across a leg predict a decline? | Null — `eff` r = −0.083, declared test, p = 0.115 on retest |
| Does OI level (percentile) predict? | Null, and the sign flipped between batches |
| Does OI predict cascade depth, conditional on a decline? | Untestable — restricted range, cascades confined to batch 1 |
| Does CVD change predict? | Null once leg size is controlled (p = 0.010 → 0.819) |
| Does leg volume predict? | Null once leg size is controlled (p = 0.043 → 0.262) |
| Do the five price votes predict at pivots? | All p > 0.20, none replicating |
| Does the ATR threshold select better pivots? | No — hold rate flat at 30% from 1.5 to 4.0 |
| Does position in the advance predict? | No — flat, and direction flips with the gap threshold |
| Does anything predict which pivots hold? | No — `gain` r = +0.083 (under 1% of variance), everything else dead |
| Is a pivot tradeable at the confirming bar? | **No — expectancy −0.22% to 0.00%** |

### On the OI data

The 51 legs in `data/oi_legs_handlogged.csv` were read manually off TradingView
charts (BTCUSDT.P, Binance) in two batches: batch 1 from approximately
2026-02-05 to 2026-05-13, batch 2 from approximately 2026-06-05 to 2026-08-13.

Batch 1 was a countertrend advance — a bear flag that resolved into a lower low,
and the source of the cascade in the sample. Batch 2 was sampled from a rally
whose larger structure had not resolved at time of writing; individual legs were
scored on a fixed window and are final.

Per-leg timestamps were not recorded — only the batch windows are known — so the
readings cannot be verified against an exchange API and the legs cannot be
joined to the automated pivot set. The analysis in this section is fully
re-runnable from the committed file; the collection is not. The `eff` hypothesis
was declared before batch 2 was collected, and the batches are non-overlapping
in time, so the direction-consistency checks in section 3 compare independent
market periods.

At n = 51 this is a documented negative, not a verified one — enough to remove
OI from the system, not enough to conclude OI carries no information. A weak
effect would need several hundred legs to detect.

## 2. The structural finding that did hold

**Pivots split into two populations, and the split is a constant.**

| | share | median drop | retrace of leg |
|---|---|---|---|
| held the 32-bar span | **30%** | ~9% | > 100% |
| closed above and failed | 70% | ~2.8% | ~40% |

That 30% is stable across:

- **years** — 23%, 30%, 33%, 30% (2023–2026)
- **regimes** — up 30%, consolidation 29%, down 26%
- **ATR thresholds** — 30%, 30%, 32%, 30%, 35% (mult 1.5 to 4.0)
- **two exchanges** — 30% hand-logged on Binance perp, 30% automated on Coinbase spot
- **sequence position** — flat at every gap threshold tried

Nothing measured predicts which population a pivot lands in. It behaves as a
fixed-odds structure.

**Adverse excursion is small and consistent:** median 0.83% above the pivot
high, 80th percentile 1.91%, and 43 of 231 never traded above it at all.
Near-identical in up and down regimes.

Note on measuring this: adverse excursion must be measured only until the pivot
is invalidated, not across the full 32-bar span. On a failed pivot, price closes
above the high and keeps running, and that continuation is not excursion against
a live position — you are already out. Measuring across the full span inflates
the median from 0.8% to 2.8%.

## 3. The confounds — the most transferable lesson

Five separate findings looked significant and dissolved. All for the same two
reasons.

### Leg size

Any cumulative quantity measured across a leg scales with the leg. Bigger legs
also have more room to fall, so both sides of the correlation track size.

```
cvd_change vs price gain:   rho = +0.740
leg_volume vs price gain:   rho = +0.575
pct        vs price gain:   rho = -0.711  (batch 3)
```

Controlling for gain killed every one of them.

### Measurement span

`max_drop` is measured until the pivot is invalidated. A hand-logged pivot that
survived 116 bars had far longer to accumulate a decline than one that survived
2. (The 116 comes from the hand-logged set, which had no cap. The automated
pipeline caps the forward window at 32 bars, so `bars_held` there never exceeds
32 — the confound is the same, bounded differently.) The rho below is from the
hand-logged data.

```
span vs max_drop:  rho = 0.85 to 0.91
```

This made `max_up` look like a strong predictor of `max_drop` (rho = −0.441,
p < 0.0001, replicating in *both* regimes separately). Control for span and it
is rho = −0.088, p = 0.415. Among pivots with an identical 32-bar span, the
relationship is gone entirely.

### Why out-of-sample replication did not catch these

`cvd_change` replicated at r = +0.696 and +0.663 across independent batches and
was still an artifact. **Replication rules out sampling noise, not bias.** A
structural confound reproduces faithfully in every sample.

The check that did work was controlling for the confounding variable directly.

## 4. Method notes worth keeping

**Declare the hypothesis before collecting.** `eff` got a fair test and failed
it. Without the pre-declaration, the temptation would have been to report
whichever of seven variables looked best — and one always does at n = 15.

**Direction consistency across samples catches most false positives.**
`cvd_change`, `pct`, `sma150` and `bb_position` all reversed sign between
batches. That check is cheap and it worked.

**Record the timestamp of every hand-logged observation**, even when it seems
irrelevant to the hypothesis being tested. The OI legs were logged without them,
which cost the ability to verify the readings against an exchange API and the
ability to join those legs to the automated pivot set. Neither mattered at
collection time; both matter now.

**Automate before scaling.** Hand-logging took two days for 88 pivots.
The automated pipeline produced 615 in an afternoon and allowed threshold
sweeps that would each have needed their own multi-day collection.

**The automation validated the hand-logging.** Independent measurement on a
different exchange reproduced the hand results closely — hold rate 30% vs 30%,
adverse p50 0.83% vs 0.84%. Both were sound.

**Watch for implausible results.** A 77% win rate on a 2:1 payoff was the tell
that revealed look-ahead bias: the simulation was entering at the pivot high,
a price not knowable until after the move away from it.

## 5. Reproducing any of this

`src/pivot_auto.py` holds the pipeline. Binance returns HTTP 451 to US IPs;
`src/fetch.py` uses Coinbase, which serves them.

The committed `data/btc_6h.csv` is the pinned dataset. Re-pulling today returns
extra bars at the tail and slightly different pivot counts at the edge — that is
new data, not a reproducibility failure.

```python
import pandas as pd
from pivot_auto import find_pivots, add_regime, summarise, sweep, sweep_gap

df = pd.read_csv("data/btc_6h.csv", parse_dates=["date"])

# atr_mult 1.5 rather than 3.0: the sweep showed the hold rate is flat across
# thresholds, so a higher setting costs 62% of the sample and buys nothing.
p = find_pivots(df, atr_mult=1.5)
p = add_regime(p, df)
summarise(p)

print(sweep(df))       # ATR threshold — hold rate flat 1.5 to 4.0
print(sweep_gap(df))   # pivot separation — hold rate flat 3 to 8 bars
```

**A note on the fetcher.** `pivot_auto.fetch_klines` pulls from Binance and
still returns HTTP 451 to US IPs. `src/fetch.py` is the Coinbase equivalent and
is what produced the committed CSV.

**Independent cross-check.** A separate implementation was written from this
document alone, without sight of `pivot_auto.py`. On the same data it
reproduced hold rate at 28–30%, adverse p50 at 0.78–0.82%, confirmation lag at
1.5%, and median failed drop at ~2.5%, across pivot separations of 3–8 bars and
leg lookbacks of 15–60. It qualified pivots differently and arrived at 668
rather than 615, and the structure was unchanged. That the numbers survive a
reimplementation by someone working only from the write-up is a stronger check
than any internal one here.

## 6. The tradeability test — the decisive one

Entry at the **close of the confirming bar**, which is the first moment a
fractal is knowable. Stop above the pivot high. Adverse case resolved first
within each bar, so the simulation is conservative rather than optimistic.
That convention applies to this short simulation only — the exit comparison in
section 9 resolves the favourable case first inside the trailing-stop loop.
See the limitations.

Running this on the pivot high instead of the confirming close is what produced
the earlier, wrong, +1.3% result.

```python
import numpy as np

h, l, c = df["high"].values, df["low"].values, df["close"].values

def simulate(bar, stop_pct, target_pct, span=32):
    """Short at the confirming bar's close. Returns % gain."""
    ref = h[bar]              # pivot high -- not knowable until bar+1 closes
    ei  = bar + 1             # confirming bar; earliest possible entry
    if ei + 1 >= len(df):
        return None
    entry      = c[ei]
    stop_lvl   = ref   * (1 + stop_pct   / 100)
    target_lvl = entry * (1 - target_pct / 100)

    for k in range(1, span + 1):
        j = ei + k
        if j >= len(df):
            break
        if h[j] >= stop_lvl:                    # adverse checked first
            return (entry - stop_lvl) / entry * 100
        if l[j] <= target_lvl:
            return target_pct
    return (entry - c[min(ei + span, len(df) - 1)]) / entry * 100

# How much of the move is surrendered waiting for confirmation
giveup = np.mean([(h[int(b)] - c[int(b)+1]) / h[int(b)] * 100
                  for b in p["bar"] if int(b) + 1 < len(df)])
print(f"confirmation lag: {giveup:.2f}% of the move is gone before entry")
print(f"median drop on a failed pivot: {p[~p['held']]['max_drop'].median():.2f}%\n")

print(f"{'stop':>6}{'target':>8}{'win%':>8}{'exp%':>9}")
for stop in [0.5, 1.0, 1.5, 2.0]:
    for target in [2.0, 3.0, 4.0]:
        r = np.array([x for x in (simulate(int(b), stop, target)
                                  for b in p["bar"]) if x is not None])
        print(f"{stop:>6.1f}{target:>8.1f}{(r > 0).mean()*100:>7.0f}%{r.mean():>8.2f}%")
```

**Expected output:** every cell between −0.22% and 0.00%, before fees.

Note also that 615 pivots across 4,500 bars average 7 bars apart while each
position is held up to 32 — so roughly four or five overlap at any time, all
short the same asset. Per-trade expectancy would not translate into a realisable
return even if it were positive.

## 7. What remains untested

**Whether pivots beat a random entry.** No control group was ever collected.
Three control designs were considered and each had a fatal flaw: random bars
are not local highs so their measurement spans are systematically shorter;
matched pivots at a lower threshold sit too close together on a 6H chart to be
independent. Given the zero expectancy result, this is now moot.

**The five price votes at decision points.** They were tested at swing highs,
where they barely vary — `avwap` read "above" 90% of the time. That is a verdict
on them in that context only. Testing them properly needs logging at entries and
exits, which is a different pipeline.

**Higher timeframes.** Everything here is 6H. On 12H or daily the confirmation
lag would be a larger absolute percentage but the moves are larger too — the
ratio is the open question.

**The volume-normalised CVD ratio** (`cvd_change / leg_volume`). The one
measurement constructed correctly and never given a fair test: rho = −0.310,
p = 0.171 at n = 21. It was found after the fact, so it would need fresh data.

## 8. Consequences for the system

**Open interest is out.** Removed on evidence, not preference. If a chart later
shows OI diverging before a top, this file is the reason not to add it back.

**The five price votes are structurally about two.** `sma50` and `avwap` agree
82%; `sma50_slope` and `sma150` have phi = 0.55. Only `bb_ext` is independent
(phi ≈ 0). A threshold calibrated for five independent votes is overconfident.

**`avwap` was "above" on 90% of pivots.** A vote that reads the same way nine
times in ten cannot discriminate. Worth checking whether that holds at entry
points before it keeps a slot.

**Any fractal-confirmed signal on 6H BTC surrenders ~1.57% before entry.** That
number is the single most transferable finding here and applies to anything
requiring a bar to confirm.

---

## 9. The exit test — the last question asked

Reframing from "is a pivot a short signal" to "is a pivot a good exit from a
long" lowers the bar considerably. No spread to overcome from a standing start,
no control group needed — it compares decision rules against each other over the
identical window.

It is the only test in this project where the pivot did something measurable.

### The split by outcome, which the definitions largely force

Every figure below is % relative to exiting at pivot confirmation. Positive
means the alternative rule beat the pivot exit.

| rule | held (30%) | failed (70%) |
|---|---|---|
| `hold_32` | **−4.99** | **+3.38** |
| `target_5` | −4.66 | +2.74 |
| `hold_16` | −4.20 | +2.36 |
| `trail_5` | −2.82 | +1.44 |
| `trail_3` | −0.96 | +0.42 |
| `trail_2` | +0.04 | +0.31 |

On the 30% that held, every alternative loses 1–5%. On the 70% that failed,
every alternative gains 0.3–3.4%.

**This table is weaker evidence than it looks.** "Held" means price never closed
back above the pivot high, so any rule that stays in marks to a lower price by
construction; "failed" means it did, so staying in marks higher. The signs and
the ordering are close to definitional — running the same comparison on a random
walk reproduces both. The table shows the arithmetic is working, not that the
pivot carries information. The only content is in the net, below.

### It does not net out, but it is close

| rule | mean | median | beat the pivot exit |
|---|---|---|---|
| `trail_2` | +0.23 | **−0.19** | 44% |
| `trail_3` | +0.01 | −0.56 | 39% |
| `trail_5` | +0.17 | −0.89 | 41% |
| `hold_16` | +0.41 | +0.09 | 52% |
| `hold_32` | +0.89 | +0.62 | 53% |
| `target_5` | +0.54 | +2.63 | 59% |

Against **holding or fixed targets**, the pivot exit clearly loses. Continuations
outweigh tops.

Against **tight trailing stops**, it is a wash on the mean and it *wins on the
median*. `trail_2` beats the pivot exit on only 44% of trades — the positive mean
comes from a handful of large wins, not from typical ones.

```
trail_2:  mean +0.23   median -0.19   std 1.45   min -1.74   max +8.70
hold_16:  mean +0.41   median +0.09   std 5.07   min -15.36  max +21.23
```

So which rule is "better" depends on what is being optimised. Total return
favours holding. Consistency favours the pivot exit — it wins more often and its
worst case is capped at −1.74% against `trail_2`, versus −15.36% against
`hold_16`.

### Regime made no difference

| regime | trail_2 | trail_3 | hold_16 | target_5 |
|---|---|---|---|---|
| up | +0.24 | −0.14 | +1.00 | +1.30 |
| down | +0.46 | +0.06 | +0.13 | +0.96 |
| consolidation | +0.17 | +0.09 | +0.20 | +0.10 |

All small, no consistent pattern. Holding beat the pivot exit most in uptrends,
which is what the mechanism predicts, but even there `trail_2` was near a wash.

*(An `unknown` row appears for pivots too near the start of the data to classify.
Two rows. Ignore it.)*

### One convention differs from section 6

The short simulation resolves the adverse case first within each bar, which
makes it conservative. The exit comparison does not: in the trailing-stop rules,
the bar's high updates the running peak before the bar's low is tested against
the stop. On a bar that makes a new high and then falls, that books the exit at
the higher stop level rather than the lower one.

Six-hour bars do not record whether the high or the low came first, so one
assumption has to be made either way. This one flatters the trailing rules,
which are the alternatives — not the pivot exit. Since the pivot exit already
loses to holding and is at best a wash against the trails, correcting it would
widen that gap rather than close it. Worth knowing, not worth rerunning.

### Reproducing the exit test

```python
import pandas as pd
from pivot_auto import find_pivots, add_regime
from exit_test import compare_exits, report

df = pd.read_csv("data/btc_6h.csv", parse_dates=["date"])
p   = find_pivots(df, atr_mult=1.5)
p   = add_regime(p, df)

res = compare_exits(df, p)
report(res, p)
```

---

## 10. Limitations

Gathered here rather than scattered, because the total is the honest picture.

**The OI data cannot be independently verified.** 51 legs, hand-read, no per-leg
timestamps. See the note in section 1. At that n, "null" means "did not clear the
bar in this sample," not "carries no information."

**No control group.** Whether qualified pivots beat random entries was never
tested, and the three designs considered each had a fatal flaw. Moot given zero
expectancy, but it means there is no baseline anywhere in this document.

**The exit comparison is not a trade simulation.** Every alternative is measured
over the same 32-bar horizon and marked to whatever price is there. That ranks
the rules fairly but has no re-entry, no compounding, and no position sizing.
Enough to say which rule wins; not enough to project a return.

**The trailing-stop rules resolve the favourable case first.** Inside
`exit_test.compare_exits`, the running peak is updated before the stop level is
tested, so a bar that makes a new high and then falls is scored off the new
high. That is the opposite of the convention used in section 6, and it biases
the trail rules mildly in their own favour — against the pivot exit, not for
it. The section 9 conclusion is unaffected: the trail rules already fail to
beat the pivot exit on the median.

**The held/failed split in section 9 is near-definitional.** It reproduces on
random data. Only the net result carries information.

**The exit test's trailing rules resolve the favorable case first.** See the
note in section 9. It biases toward the alternatives, not toward the pivot exit,
so the conclusion is unaffected — but the convention is not the one stated in
section 6.

**Single instrument, single timeframe.** All of this is 6H BTC. The confirmation
lag is a structural argument that should generalise; nothing else here is
claimed to.

**Overlapping positions were never modelled.** 615 pivots at ~7 bars apart with
32-bar holds means four or five concurrent positions in the same direction on
the same asset. Not addressed anywhere.

---

## 11. Where this ends

### The complete scoreboard

| tested | result |
|---|---|
| OI — five constructions, 51 legs, 2 batches | null |
| CVD change, leg volume | null once leg size controlled |
| Five price votes at pivots | null, and mostly redundant with each other |
| ATR threshold selecting better pivots | no — hold rate flat 1.5 to 4.0 |
| Sequence position within an advance | no — flips direction with the gap cut |
| Anything predicting which pivots hold | no — best is r = +0.083 |
| Pivot as a **short** signal | **zero expectancy**, −0.22% to 0.00% |
| Pivot as an **exit** signal | near-wash vs tight trailing stops, loses to holding |

### The two things that are real

**A 30% hold rate that behaves like a constant.** Stable across years, regimes,
ATR thresholds, pivot separation, two exchanges, and sequence position. When a
pivot holds, price drops ~9% and retraces more than the whole leg. When it
fails, ~2.8%. Nothing measured predicts which.

**A 1.57% confirmation lag.** A 1-1 fractal cannot be known until the next bar
closes, and that bar is lower by definition. Against a median failed-pivot drop
of 2.79%, most of the move is gone before entry is possible. This is the single
most transferable finding here — it applies to any signal on any instrument that
needs a bar to confirm.

### What this cost and what it bought

Roughly three weeks. One belief removed from the system on evidence rather than
preference, five false positives caught before they became rules, and a working
research pipeline that turns a multi-day hand-logging exercise into an afternoon.

The negatives are the product. A system with OI removed and five votes known to
be really two is more trustworthy than the same system with an untested vote
still in it — even though it looks like less.

### If picking this back up

Read section 3 first. Leg size and measurement span produced five separate false
positives, and the note that out-of-sample replication does not catch a confound
is the thing most likely to save time on whatever comes next.

The open threads, in order of appeal:

1. **The five price votes at actual decision points.** They were only ever tested
   at swing highs, where they barely vary — `avwap` read "above" 90% of the time.
   Needs a different logging anchor.
2. **Higher timeframes.** The 1.57% lag would be a larger absolute cost on 12H or
   daily, but the moves are larger too. The ratio is the open question, and the
   pipeline already handles any timeframe.
3. **The volume-normalised CVD ratio.** The one measurement built correctly and
   never given a fair test — rho = −0.310, p = 0.171 at n = 21. Found after the
   fact, so it needs fresh data.

And it is entirely reasonable to stop here.
