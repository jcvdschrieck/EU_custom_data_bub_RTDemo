"""
RT Risk Monitoring 2 — static watchlist.

Transactions whose (seller_id, seller_country) pair appears in WATCHLIST
are flagged by _RT_risk_monitoring_2_factory regardless of VAT ratio
deviation.  The pairing is supplier × country of origin (where the goods
originate) — useful for flagging all transactions by a known-suspicious
supplier exporting from a specific country.  Edit this set to add /
remove monitored pairs.
"""
from __future__ import annotations

# Each entry is (seller_id, seller_country) — country of origin.
WATCHLIST: frozenset[tuple[str, str]] = frozenset({
    ("SUP001", "DE"),   # TechZone GmbH (Germany) — overlaps with fraud scenario
    ("SUP002", "FR"),   # FashionHub Paris (France)
    ("SUP005", "NL"),   # SportsPro Amsterdam (Netherlands)
})


def is_watchlisted(seller_id: str, seller_country: str) -> bool:
    return (seller_id, seller_country) in WATCHLIST
