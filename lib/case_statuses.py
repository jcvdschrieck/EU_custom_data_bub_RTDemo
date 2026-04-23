"""
Single source of truth for Sales_Order_Case.Status values used by the
C&T Risk Management System flow. The frontend has a mirror file (see
customsandtaxriskmanagemensystem/src/lib/caseStatuses.ts) — keep both in sync.

These strings are persisted to investigation.db and travel over the wire
on every /api/rg/cases payload, so renaming any of them is a breaking
change.
"""
from __future__ import annotations

# ── Individual status constants ─────────────────────────────────────────────
NEW                       = "New"
UNDER_REVIEW_BY_CUSTOMS   = "Under Review by Customs"
AI_INVESTIGATING          = "AI Investigation in Progress"
UNDER_REVIEW_BY_TAX       = "Under Review by Tax"
REVIEWED_BY_TAX           = "Reviewed by Tax"
REQUESTED_INPUT           = "Requested Input by Deemed Importer"
CLOSED                    = "Closed"

# ── Convenience set: every legal value ──────────────────────────────────────
ALL: frozenset[str] = frozenset({
    NEW,
    UNDER_REVIEW_BY_CUSTOMS,
    AI_INVESTIGATING,
    UNDER_REVIEW_BY_TAX,
    REVIEWED_BY_TAX,
    REQUESTED_INPUT,
    CLOSED,
})

# Subsets useful for filters / guards.
TERMINAL: frozenset[str]   = frozenset({CLOSED})
TAX_QUEUE: frozenset[str]  = frozenset({UNDER_REVIEW_BY_TAX, AI_INVESTIGATING, REQUESTED_INPUT})
LOCKED:   frozenset[str]   = frozenset({AI_INVESTIGATING})
