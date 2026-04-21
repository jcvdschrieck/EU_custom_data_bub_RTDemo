"""
Single source of truth for Sales_Order.Status values.

These strings are persisted to investigation.db (Sales_Order table) and
travel on the wire inside the hydrated /api/rg/cases payload. Renaming
any of them is a breaking change.

Lifecycle:
  UNDER_INVESTIGATION  → set at case-open by the C&T factory
  TO_BE_RELEASED       → set by Customs officer (recommend release)
  TO_BE_RETAINED       → set by Customs officer (recommend retainment)
"""
from __future__ import annotations

UNDER_INVESTIGATION = "Under Investigation"
TO_BE_RELEASED      = "To Be Released"
TO_BE_RETAINED      = "To Be Retained"

ALL: frozenset[str] = frozenset({
    UNDER_INVESTIGATION,
    TO_BE_RELEASED,
    TO_BE_RETAINED,
})
