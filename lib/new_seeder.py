"""
New-dataset seeder for simulation.db.

Reads VAT_Cases_Generated_17042026_6.xlsx (191 source rows) and
Context/Fake_ML.xlsx (per-tx engine outputs), emits transactions into
simulation.db with the new pre-baked engine fields populated.

Pipeline:

  1. Load both xlsx files; index Fake_ML by xlsx_row_index.
  2. For each (seller, dest, parent_category) cluster of investigate-
     route xlsx rows, pick a target cluster size (1..15, median 5)
     and synthesize siblings to reach it. Siblings inherit the
     parent's declared+recommended categories and engine outputs.
  3. Rewrite each cluster's product descriptions to share a common
     6-word prefix so Jaccard >= 0.4 between any pair.
  4. Release/retain rows pass through unchanged (no clustering, no
     synthetic siblings — neither route forms cases at the C&T factory).
  5. Distribute timestamps uniformly across the SIM_START..SIM_END
     window (default 15 minutes starting 2026-04-01 00:00:00).
  6. Generate a fresh transaction_id and value (uniform [10, 150)) for
     every tx — both xlsx-derived and synthetic.
  7. Bulk-insert into simulation.db.

Run via scripts/seed_new_dataset.py (preferred) or
seed_databases.py (which now wires this module in for the sim DB).
"""
from __future__ import annotations

import random
import uuid
from datetime import timedelta
from pathlib import Path

import pandas as pd

from lib.config      import SIM_START_DT, SIM_END_DT, SIMULATION_DB
from lib.database    import bulk_insert, init_simulation_db, _connect
from lib             import vat_dataset

ROOT      = Path(__file__).resolve().parent.parent
SOURCE_XLSX = ROOT / "Context" / "VAT_Cases_Generated_17042026_6.xlsx"
FAKE_ML_XLSX = ROOT / "Context" / "Fake_ML.xlsx"

# Seed for reproducibility — change only when intentionally regenerating.
_RNG_SEED = 20260401

# Cluster size distribution: triangular(1, 5, 15). Caller picks size for
# each investigate (seller, dest, parent_cat) cluster. Median lands ~5.
_CLUSTER_SIZE_MIN  = 1
_CLUSTER_SIZE_MODE = 5
_CLUSTER_SIZE_MAX  = 15

# Value distribution: uniform [10, 150). Below the EU IOSS threshold (€150).
_VALUE_MIN = 10.0
_VALUE_MAX = 150.0


# ── Description rewriter ────────────────────────────────────────────────────

def _seller_code(seller_name: str) -> str:
    """First three letters of each capitalised word, joined."""
    parts = [w[:3].upper() for w in seller_name.split() if w[0].isupper()]
    return "".join(parts[:2]) or "GEN"


def _category_code(parent_category: str) -> str:
    """Two-letter prefix derived from the parent category."""
    return "".join(w[0].upper() for w in parent_category.split() if w[0].isalpha())[:3]


def _cluster_prefix(seller_name: str, destination: str, parent_category: str) -> str:
    """5-token phrase where every token encodes the cluster identity.

    Design constraint: cross-cluster Jaccard must stay below 0.4 even
    when two clusters share the same destination or category. We achieve
    this by suffixing every prefix word with the cluster ID, so no two
    clusters share any prefix token. Intra-cluster Jaccard stays high
    because all 5 prefix tokens are identical for siblings.
    """
    cid = f"{_seller_code(seller_name)}-{destination}-{_category_code(parent_category)}"
    return (f"{cid}-shipment {cid}-lot {cid}-consignment {cid}-line {cid}-grade")


def _per_tx_suffix(rng: random.Random, base_description: str | None,
                   sibling_idx: int) -> str:
    """Differentiator appended after the cluster prefix.

    For xlsx rows we keep a short distinctive trailer derived from the
    original Product Name so the case still looks plausible to a
    reviewer. Synthetic siblings get a numbered variant tag. Tokens
    here are not constrained to be unique across clusters — the
    Jaccard story is carried entirely by the cluster prefix.
    """
    if sibling_idx == 0 and base_description:
        words = [w for w in base_description.split() if len(w) > 2][:4]
        return " ".join(words) if words else f"variant {sibling_idx + 1:02d}"
    return f"variant {chr(ord('A') + (sibling_idx % 26))} batch {sibling_idx + 1:02d}"


# ── Seeding ─────────────────────────────────────────────────────────────────

def _route_from_action(action: str) -> str:
    return (action or "").strip().lower()


def _new_tx_id(rng: random.Random) -> str:
    return f"TX-{uuid.UUID(int=rng.getrandbits(128)).hex[:12].upper()}"


def _build_tx_row(
    *,
    rng: random.Random,
    timestamp_iso: str,
    seller_dict: dict,
    destination: str,
    parent_category: str,
    declared_subcat: str,
    declared_rate: float,
    recommended_rate: float,
    description: str,
    fake_ml_row: dict,
) -> dict:
    """Compose one row in the shape expected by lib.database.bulk_insert."""
    seller_name    = seller_dict["name"]
    seller_origin  = seller_dict["origin"]
    value          = round(rng.uniform(_VALUE_MIN, _VALUE_MAX), 2)
    vat_amount     = round(value * declared_rate, 2)

    return {
        "transaction_id":   _new_tx_id(rng),
        "transaction_date": timestamp_iso,
        "seller_id":        seller_dict["id"],
        "seller_name":      seller_name,
        "seller_country":   seller_origin,
        "item_description": description,
        "item_category":    parent_category,
        "value":            value,
        "vat_rate":         declared_rate,
        "vat_amount":       vat_amount,
        "buyer_country":    destination,
        "correct_vat_rate": recommended_rate,
        # Has-error semantics: any rate mismatch on the declared invoice.
        "has_error":        1 if abs(declared_rate - recommended_rate) > 1e-9 else 0,
        "xml_message":      None,
        "created_at":       timestamp_iso,
        # No producer (the new dataset's "seller" is the non-EU
        # manufacturer directly — no two-tier party split).
        "producer_id":      None,
        "producer_name":    None,
        "producer_country": None,
        "producer_city":    None,
        # New-dataset Stage-3 fields ─────────────────────────────────
        "vat_subcategory_code":               declared_subcat,
        "engine_vat_ratio_risk":              float(fake_ml_row["expected_vat_ratio_risk"]),
        "engine_ml_risk":                     float(fake_ml_row["expected_ml_risk"]),
        "engine_ml_seller_contribution":      float(fake_ml_row["seller_contribution"]),
        "engine_ml_origin_contribution":      float(fake_ml_row["country_origin_contribution"]),
        "engine_ml_category_contribution":    float(fake_ml_row["category_contribution"]),
        "engine_ml_destination_contribution": float(fake_ml_row["destination_contribution"]),
        "engine_vagueness_risk":              float(fake_ml_row["expected_vagueness_risk"]),
        # IE watchlist is currently empty in the dataset; pre-bake 0
        # (the engine treats both 0 and missing-pre-bake as "not flagged"
        # but having an explicit value keeps the engine on the pre-baked
        # path rather than the legacy IE_WATCHLIST set lookup).
        "engine_ie_watchlist_risk":           0.0,
    }


def _evenly_spaced_timestamps(n: int, rng: random.Random) -> list[str]:
    """n timestamps inside [SIM_START_DT, SIM_END_DT). Evenly spaced with
    small jitter so we don't collide on identical sim-time instants but
    still fan out across the whole window."""
    if n <= 0:
        return []
    window_seconds = (SIM_END_DT - SIM_START_DT).total_seconds()
    step = window_seconds / (n + 1)   # leave a margin at start+end
    out: list[str] = []
    for i in range(n):
        base   = step * (i + 1)
        jitter = rng.uniform(-step * 0.25, step * 0.25)
        offset = max(0.5, min(window_seconds - 0.5, base + jitter))
        ts = SIM_START_DT + timedelta(seconds=offset)
        out.append(ts.isoformat())
    return out


def seed_simulation_db_from_xlsx() -> int:
    """Wipe simulation.db and reseed it from the xlsx + Fake_ML reference.

    Returns the number of transactions inserted.
    """
    init_simulation_db()
    rng = random.Random(_RNG_SEED)

    src = pd.read_excel(SOURCE_XLSX, sheet_name="VAT Missclassification Last")
    fml = pd.read_excel(FAKE_ML_XLSX, sheet_name="Per-Tx Expected Engine Outputs")
    fml_by_idx = {int(r["xlsx_row_index"]): r.to_dict() for _, r in fml.iterrows()}

    # Pre-resolve sellers by name to spare per-row lookups.
    seller_by_name = {s["name"]: s for s in vat_dataset.SELLERS}

    rows: list[dict] = []

    # ── Pass 1: investigate-route rows + their synthetic siblings ───────────
    investigate_mask = src["Customs Authority Action (Calculated)"].str.lower() == "investigate"
    investigate_rows = src[investigate_mask]

    cluster_groups = investigate_rows.groupby(
        ["Seller", "Destination Country", "VAT Category (declared)"], sort=True
    )

    cluster_summary: list[tuple[str, str, str, int, int]] = []  # for reporting

    for (seller_name, destination, parent_cat), group in cluster_groups:
        seller_dict = seller_by_name[seller_name]
        target_size = int(round(rng.triangular(_CLUSTER_SIZE_MIN, _CLUSTER_SIZE_MAX, _CLUSTER_SIZE_MODE)))
        target_size = max(len(group), min(_CLUSTER_SIZE_MAX, target_size))
        prefix = _cluster_prefix(seller_name, destination, parent_cat)

        # The xlsx rows for this cluster — keep their per-row signals;
        # rewrite description with the shared prefix.
        xlsx_records = [
            {"orig_idx": int(idx), "data": row.to_dict()}
            for idx, row in group.iterrows()
        ]
        siblings_needed = target_size - len(xlsx_records)
        cluster_summary.append((seller_name, destination, parent_cat,
                                len(xlsx_records), target_size))

        # Sibling parents: cycle through xlsx records so each sibling
        # inherits from a real source row (declared/recommended cat+rate,
        # engine outputs).
        cluster_members = [(rec, 0) for rec in xlsx_records] + [
            (xlsx_records[sibling_idx % len(xlsx_records)], sibling_idx + 1)
            for sibling_idx in range(siblings_needed)
        ]

        for rec, sibling_idx in cluster_members:
            xrow      = rec["data"]
            orig_idx  = rec["orig_idx"]
            base_desc = xrow["Product Description (declared)"]
            description = f"{prefix} — {_per_tx_suffix(rng, base_desc, sibling_idx)}"

            row = _build_tx_row(
                rng=rng,
                timestamp_iso="",
                seller_dict=seller_dict,
                destination=destination,
                parent_category=parent_cat,
                declared_subcat=xrow["VAT Code (declared)"],
                declared_rate=float(xrow["VAT Rate (%)"]) / 100.0,
                recommended_rate=float(xrow["VAT Rate (Recommended)"]) / 100.0,
                description=description,
                fake_ml_row=fml_by_idx[orig_idx],
            )
            rows.append(row)

    # ── Pass 2: release + retain rows (no clustering, descriptions kept) ────
    other_rows = src[~investigate_mask]
    for orig_idx, xrow in other_rows.iterrows():
        seller_dict = seller_by_name[xrow["Seller"]]
        row = _build_tx_row(
            rng=rng,
            timestamp_iso="",
            seller_dict=seller_dict,
            destination=xrow["Destination Country"],
            parent_category=xrow["VAT Category (declared)"],
            declared_subcat=xrow["VAT Code (declared)"],
            declared_rate=float(xrow["VAT Rate (%)"]) / 100.0,
            recommended_rate=float(xrow["VAT Rate (Recommended)"]) / 100.0,
            description=str(xrow["Product Description (declared)"]),
            fake_ml_row=fml_by_idx[int(orig_idx)],
        )
        rows.append(row)

    # ── Pass 3: assign timestamps inside the sim window ─────────────────────
    timestamps = _evenly_spaced_timestamps(len(rows), rng)
    rng.shuffle(rows)   # randomise arrival order so investigate clusters interleave with releases
    for r, ts in zip(rows, timestamps):
        r["transaction_date"] = ts
        r["created_at"]       = ts

    # ── Pass 4: wipe simulation.db transactions and bulk-insert ─────────────
    conn = _connect(SIMULATION_DB)
    with conn:
        conn.execute("DELETE FROM transactions")
    conn.close()
    bulk_insert(rows, path=SIMULATION_DB)

    # Report
    investigate_count = sum(1 for r in rows if r["engine_vat_ratio_risk"] is not None
                            and (r["has_error"] or r["engine_ml_risk"] > 0 or r["engine_vagueness_risk"] > 0))
    print(f"  source xlsx rows:              {len(src)}")
    print(f"  investigate clusters:          {len(cluster_summary)}")
    print(f"  → cluster sizes (min/median/max): "
          f"{min(s[4] for s in cluster_summary)}/"
          f"{sorted(s[4] for s in cluster_summary)[len(cluster_summary)//2]}/"
          f"{max(s[4] for s in cluster_summary)}")
    print(f"  total tx written:              {len(rows)}")
    return len(rows)


if __name__ == "__main__":
    n = seed_simulation_db_from_xlsx()
    print(f"\n✓ {n} transactions written to {SIMULATION_DB}")
