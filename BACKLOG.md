# Backlog

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
