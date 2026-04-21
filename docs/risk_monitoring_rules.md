# Risk Monitoring Rules

The EU Custom Data Hub runs **four** independent real-time risk monitoring
engines. Each subscribes to the Sales Order Event broker and publishes
its result to the unified **RT Risk Outcome** broker. The Release
Factory's `_compute_score` collects the outcomes per transaction and
computes a **weighted, capped sum** that decides the route
(release / investigate / retain).

```
                 SALES_ORDER_EVENT broker
                          │
   ┌─────────┬────────────┼──────────────┬─────────────────┐
   ▼         ▼            ▼              ▼                 ▼
vat_ratio  watchlist   ireland_       description_     order_validation
 engine     engine     watchlist       vagueness         factory
   │         │            │              │                 │
   └────┬────┴────────────┴──────────────┘                 │
        ▼                                                  │
   RT_RISK_OUTCOME broker  ────►  Release Factory ◄────────┘
                                  (_compute_score)
                                       │
                                       ▼
                                ASSESSMENT_OUTCOME
                                  release / investigate / retain
```

---

## How each engine resolves its risk

Every engine tries its resolution paths **in order** and stops at the
first one that fires. The pre-baked path is always preferred when the
seeder has supplied a per-tx value; the legacy path stays in place so
the historical seeder still works without changes.

| Engine | 1. Pre-baked tx field | 2. Fallback path |
|---|---|---|
| `vat_ratio` | `_engine_vat_ratio_risk` | declared-vs-expected subcategory rate via `lib.vat_dataset.expected_rate_for(...)`; if no subcategory on the tx → legacy 7-day vs 8-week volume-ratio alarm |
| `watchlist` (ML) | `_engine_ml_risk` + 4 contributors | 4-tuple lookup in `ml_risk_rules` (seeded from the legacy `Fake ML.xlsx`) |
| `ireland_watchlist` | `_engine_ie_watchlist_risk` | static `IE_WATCHLIST: set[(seller_id, seller_country)]` (currently empty) |
| `description_vagueness` | `_engine_vagueness_risk` | `sentence-transformers/all-MiniLM-L6-v2` cosine-similarity to a vague-text anchor embedding |

All four engines are implemented inside `api.py`
(`_RT_risk_monitoring_{1,2,3,4}_factory`).

---

## Engine 1 — `vat_ratio`

**Source:** `api.py` `_RT_risk_monitoring_1_factory`
**Engine ID:** `vat_ratio`
**Source data (new dataset):** `Context/VAT_Cases_Generated_17042026_6.xlsx` `Score 1`,
gated by actual rate mismatch.

### What it detects

Declared VAT rate that does not match the rate the EU expects for the
declared product subcategory in the destination country — the canonical
VAT-misclassification fraud pattern.

### Three resolution paths

1. **Pre-baked.** Tx carries `_engine_vat_ratio_risk` (set by the new
   seeder from `Fake_ML.xlsx`). Used as-is. Risk values are graded:
   `Score 1 / 100`, gated to 0 whenever `declared_rate == recommended_rate`
   (the xlsx zeroes out misclassification with no revenue impact).
2. **Subcategory rate check.** Tx carries `vat_subcategory_code` and
   `vat_rate`. Look up the canonical rate via
   `lib.vat_dataset.expected_rate_for(buyer_country, vat_subcategory_code)`;
   emit `1.0` on mismatch, `0.0` on match.
3. **Legacy volume-ratio alarm.** Tx has neither pre-bake nor a
   subcategory. Fall back to `lib.alarm_checker.check_alarm`: 7-day
   vs 8-week aggregate VAT/value ratio deviation > 25%. Used only by
   the legacy historical seeder (Sept 2025 – Feb 2026 simulation).

### Reason codes

`prebaked` · `rate_mismatch` · `rate_match` · `unknown_subcategory` ·
`alarm_match` · `alarm_clear`.

---

## Engine 2 — `watchlist` (ML / supplier risk)

**Source:** `api.py` `_RT_risk_monitoring_2_factory`
**Engine ID:** `watchlist` (named for legacy reasons; effectively the ML
supplier-risk engine)
**Source data (new dataset):** `Context/Fake_ML.xlsx` `expected_ml_risk`
(itself derived from the source xlsx `Score 3`).

### What it detects

Per-tx supplier risk. Mirrors the xlsx `Score 3` signal — values 0,
0.40 or 0.90 in the new dataset, where 0.90 is "this seller is
flagged in the risk-intelligence database for this destination" and
0.40 is "this seller exhibits compliance-risk characteristics but no
direct flag yet."

### Two resolution paths

1. **Pre-baked.** Tx carries `_engine_ml_risk` plus the four
   contributor weights:
   - `_engine_ml_seller_contribution`
   - `_engine_ml_origin_contribution`
   - `_engine_ml_category_contribution`
   - `_engine_ml_destination_contribution`

   Engine returns the pre-baked risk and propagates the contributors
   so the C&T factory writes them onto `Sales_Order_Risk` at case
   creation.
2. **4-tuple rule lookup (legacy).** `lib.database.lookup_ml_risk_rule`
   keys on `(seller, country_origin, vat_product_category,
   country_destination)` against the `ml_risk_rules` table seeded
   from the legacy `Context/Fake ML.xlsx`. Returns the rule's risk +
   per-dimension weights.

### Flag threshold

`ML_RISK_FLAG_THRESHOLD = 0.5`. The flagged boolean is informational
only — the score consolidator uses the raw `risk` value.

---

## Engine 3 — `ireland_watchlist`

**Source:** `api.py` `_RT_risk_monitoring_3_factory`
**Engine ID:** `ireland_watchlist`

### What it detects

A country-specific channel hosted (in real life) on a server managed
by the Irish authority. Subscribes to every `SALES_ORDER_EVENT` but
only **processes** events whose `buyer_country == "IE"` — non-IE
events are immediately published with `applicable=False` and excluded
from the consolidator's denominator.

### Two resolution paths

1. **Pre-baked.** Tx carries `_engine_ie_watchlist_risk`. Used as-is.
   The new seeder pre-bakes `0.0` for every IE tx (the xlsx has no
   separate IE-watchlist signal beyond the general supplier risk).
2. **Static set lookup.** `(seller_id, seller_country) in IE_WATCHLIST`
   (currently empty). Returns `1.0` on match, `0.0` otherwise.

### Latency

Both paths apply a uniform `random.uniform(1.0, 5.0)` second sleep
to simulate the round-trip to a remote server. Because the latency
can exceed `ASSESSMENT_TIMER_S` (3 s by design), some IE outcomes
legitimately arrive too late to influence the consolidator. That is
intended behaviour — the consolidator still publishes on time and
the late outcome is discarded.

---

## Engine 4 — `description_vagueness`

**Source:** `api.py` `_RT_risk_monitoring_4_factory`
**Engine ID:** `description_vagueness`
**Source data (new dataset):** `Context/Fake_ML.xlsx` `expected_vagueness_risk`
(derived from the source xlsx `Score 2` — binary 0 or 0.60).

### What it detects

Product descriptions that are too generic to support a category
classification (e.g. "general goods", "miscellaneous items"). High
vagueness alone doesn't make a tx fraudulent, but combined with
other signals it tips the consolidated score over the investigate
threshold.

### Two resolution paths

1. **Pre-baked.** Tx carries `_engine_vagueness_risk`. Used as-is.
2. **Embedding model (legacy).** Cosine similarity between the
   description's `all-MiniLM-L6-v2` embedding and a pre-computed
   "vague text" anchor (mean of phrases like "general goods",
   "miscellaneous items", "various products", …). Clamped to `[0, 1]`.

The pre-baked path lets the new seeder pin per-tx values for
deterministic routing without paying the embedding-model cost on
every tx.

---

## Consolidation (Release Factory)

**Source:** `api.py` `_release_factory._compute_score`

### Score formula

```
score = min(1.0,
    Σ ENGINE_WEIGHTS[engine] · risk[engine]   for every applicable engine
)
```

This is a **weighted sum, capped at 1.0** — chosen to mirror the xlsx
"Overall Risk Score (Calculated)" model (`Score 1 + Score 2 + Score 3`,
capped at 100). It replaces the earlier mean-of-applicable-engines
formula; the change was needed because a single high signal averaged
with three zeros never crossed the retain threshold.

### Engine weights

```python
ENGINE_WEIGHTS = {
    "vat_ratio":             0.5,
    "watchlist":             0.9,    # ML / supplier-risk engine
    "ireland_watchlist":     1.0,
    "description_vagueness": 0.8,
}
```

Weights are **tuned against the new dataset** (`Context/Fake_ML.xlsx`,
191 rows) for maximum route-prediction accuracy: 189/191 (99.0%) tx
land on their xlsx target route from the precomputed signals using
these values.

The two residual mismatches (tx#70 → FR, tx#146 → NL) are rate-match
cases where supplier_risk Score 3=40 alone makes us emit Investigate
while the xlsx says Release. Both have non-IE destinations so they
are filtered out at the C&T frontend (see `customsandtaxriskmanagemensystem`
`backendCaseStore` IE filter) and don't affect the demo.

### vat_ratio floor

```python
VAT_RATIO_FLOOR_TRIGGER = 0.30                   # raw risk threshold to engage floor
VAT_RATIO_FLOOR         = THRESHOLD_RELEASE + ε  # floored contribution value (≈ 0.334)

if engine == "vat_ratio" and raw_risk >= VAT_RATIO_FLOOR_TRIGGER:
    contribution = max(weighted_risk, VAT_RATIO_FLOOR)
```

Policy stance: **any genuine rate mismatch above the xlsx's release
tier (Score 1 ≥ 30) deserves at least an investigation**, regardless
of how low its weighted contribution would otherwise be. Without this
floor, tx#42 (IE, Score 1=40 alone) would mis-route to Release and
disappear from the C&T queue — the only IE mismatch in the previous
weighting, which would have been highly visible because of the
frontend's IE filter.

The trigger threshold (0.30) sits between the xlsx's Release tier
(Score 1=25) and Investigate tier (Score 1≥37.5), so no row that
xlsx releases on a low Score 1 gets bumped up.

### Confidence

```
confidence = applicable_engines_received / TOTAL_RISK_ENGINES_EXPECTED
```

`TOTAL_RISK_ENGINES_EXPECTED` is 4 minus any engine that self-reported
`applicable=False` (currently only the IE watchlist on non-IE tx).
With all four engines: 0% (none received), 25%, 50%, 75% or 100%.

### Routing thresholds

```python
THRESHOLD_RELEASE = 1.0 / 3.0   # < 33.33% → release
THRESHOLD_RETAIN  = 0.80        # ≥ 80%   → retain
```

| Score range | Route | Action |
|---|---|---|
| `score < 33.33%` | **Green** → Release | Auto-released, terminal event published |
| `33.33% ≤ score < 80%` | **Amber** → Investigate | Sent to the C&T Risk Management Factory; case is opened in `investigation.db` |
| `score ≥ 80%` | **Red** → Retain | Terminal event published; **no case** is opened (retain bypasses the C&T factory by design — retentions are the result of officer escalation from an existing investigate case, not an automatic route) |

The retain threshold was raised from the original `2/3 ≈ 0.667` to
`0.80` because the xlsx puts `Score 75` rows in Investigate (not
Retain) and only `Score ≥ 90` in Retain.

### Assessment timer

```python
ASSESSMENT_TIMER_S = 3.0
```

Starts when the Order Validation event arrives. The assessment
publishes either:
- **Immediately** if all `TOTAL_RISK_ENGINES` outcomes arrive before
  the timer, or
- **On timer expiry** with whatever risk data is available (lower
  confidence — the IE watchlist's 1–5 s latency frequently makes it
  miss the timer for non-IE tx, but those engine outcomes are
  `applicable=False` anyway).

Late outcomes after publication are discarded.

---

## Per-tx pre-baking — `Context/Fake_ML.xlsx`

**Source:** `scripts/regenerate_fake_ml.py` (regenerates from the source
xlsx); `lib/new_seeder.py` (writes the pre-baked values onto each
transaction row).

The new seeder pre-bakes per-tx engine outputs into the
`transactions` table at seed time, so each tx carries its own
target signals through the pipeline. This replaces the earlier
per-(seller, dest, parent_cat) rule lookup, which couldn't reproduce
the xlsx's per-row labels.

### Schema

`Context/Fake_ML.xlsx` (sheet `Per-Tx Expected Engine Outputs`), one
row per source-xlsx tx:

| Column | Engine field on tx |
|---|---|
| `xlsx_row_index` | seeder bookkeeping |
| `expected_vat_ratio_risk` | `_engine_vat_ratio_risk` |
| `expected_ml_risk` | `_engine_ml_risk` |
| `seller_contribution` | `_engine_ml_seller_contribution` |
| `country_origin_contribution` | `_engine_ml_origin_contribution` |
| `category_contribution` | `_engine_ml_category_contribution` |
| `destination_contribution` | `_engine_ml_destination_contribution` |
| `expected_vagueness_risk` | `_engine_vagueness_risk` |
| `expected_overall_risk` | (informational — not consumed by engines) |
| `expected_route` | (informational — used by the validation script) |

The values are also persisted in `simulation.db.transactions` (9
nullable columns added to the schema in Stage 3) and propagated
onto the `SALES_ORDER_EVENT` payload by
`lib.message_factory.build_sales_order_event` as the underscore-
prefixed `_engine_*` keys the engines look for.

### Synthetic siblings

The new seeder grows each (seller, dest, parent_cat) cluster of
investigate-route rows up to a target size drawn from
`triangular(1, 5, 15)`. Synthetic siblings inherit their parent
xlsx row's pre-baked engine outputs verbatim — so a cluster's
score consolidation is identical for every member.

---

## Validation

`scripts/verify_vat_dataset.py` mirrors `_compute_score` and reports
how many of the 191 source-xlsx rows land on their xlsx target route
from the precomputed signals. Run after editing `ENGINE_WEIGHTS`,
thresholds, or the floor parameters.

`scripts/verify_new_seed.py` runs end-to-end on `simulation.db` after
seeding: per-cluster Jaccard, cross-cluster Jaccard, value range,
timestamp window, and replayed route distribution.
