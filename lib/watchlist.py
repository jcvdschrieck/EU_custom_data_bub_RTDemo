"""
RT Risk Monitoring 2 — static watchlist.

Transactions whose (seller_id, buyer_country) pair appears in WATCHLIST
are flagged by _RT_risk_monitoring_2_factory regardless of VAT ratio
deviation.  Edit this set to add / remove monitored pairs.
"""
from __future__ import annotations

# Each entry is (seller_id, buyer_country)
WATCHLIST: frozenset[tuple[str, str]] = frozenset({
    ("SUP001", "IE"),   # TechZone GmbH → Ireland  (overlaps with scenario)
    ("SUP002", "PL"),   # FashionHub Paris → Poland
    ("SUP005", "ES"),   # AutoParts Nederland → Spain
})


def is_watchlisted(seller_id: str, buyer_country: str) -> bool:
    return (seller_id, buyer_country) in WATCHLIST
