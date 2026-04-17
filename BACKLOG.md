# Backlog

---

## Review event statuses / values of the Automated Assessment Factory

The Release Factory (Automated Assessment) publishes `ASSESSMENT_OUTCOME`
with a `route` field (`release` / `retain` / `investigate`) and an
`Overall_Risk_Level` field (`green` / `amber` / `red`). These values are
**not centralised** in a reference table or constants module — they're
inline strings in `api.py::_publish_assessment`. Similarly the `status`
field on the `RT_SCORE` legacy counter carries `green` / `amber` / `red`
as raw strings.

**What to review:**
- Should these route/level labels live in a reference table (like
  `case_statuses` and `sales_order_statuses`) or a constants module
  (like `lib/case_statuses.py`)?
- Are the labels user-facing? If so, do they need human-readable
  equivalents (e.g. `"release"` → `"Automated Release"`)?
- The pipeline diagram currently colour-codes by these raw strings —
  a rename would need a coordinated frontend update.

**When this matters:** the moment a new route is added (e.g.
`escalate`) or the label vocabulary is exposed to the Revenue Guardian
frontend.

---

## Third-party input loop — currently a workflow dead-end

When a Customs or Tax officer triggers **Request Input from Third Party**,
the case transitions to `Status = "Requested Input by Third Party"` and
sits there indefinitely. There is no:

- "Response received" action / endpoint to bring it back into a queue
- Audit field for *which third party* was contacted or *what was asked*
  (only an unstructured Communication entry)
- Reminder / escalation timer for stale input requests

The case remains visible on both Customs and Tax pages but has no
defined exit path other than the officer manually choosing a different
action (release / retain / submit-for-tax-review), which silently
overwrites the pending-input status.

**When this matters:** the moment the demo includes a real third-party
back-and-forth scenario, this gap will block the flow. Acceptable for
now; document if a stakeholder asks.

---

## Three-outcome risk engine results (flagged / clear / insufficient_data)

Currently each risk engine returns a binary `flagged: true | false`.
When the engine skips a transaction due to insufficient data (e.g.
fewer than `MIN_CURRENT_TX` transactions in the 7-day window), it
returns `False` — indistinguishable from "checked and clean."

**Proposed change:** each engine publishes a `status` field with three
possible values:

| Status | Meaning |
|---|---|
| `flagged` | Deviation detected / watchlist match |
| `clear` | Checked, within threshold |
| `insufficient_data` | Skipped — not enough transactions to evaluate |

**Impact on the Assessment Factory:**
- `flagged` counts toward the numerator (flagged_count)
- `clear` counts toward the denominator (total_outcomes) but not numerator
- `insufficient_data` does NOT count toward the denominator — effectively
  excluded from the score, keeping confidence lower

This means a new supplier with no history would get `confidence < 100%`
instead of a false "clean" signal, giving downstream consumers (C&T
Risk Management, DB Store) a more honest picture of the assessment
quality.
