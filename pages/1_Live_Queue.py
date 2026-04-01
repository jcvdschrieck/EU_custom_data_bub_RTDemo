"""Live Transaction Queue — auto-refreshes every 2 seconds."""
import time
import httpx
import pandas as pd
import streamlit as st

from lib.config import API_BASE_URL, QUEUE_SIZE

st.set_page_config(page_title="Live Queue", page_icon="📡", layout="wide")
st.title("📡 Live Transaction Queue")
st.caption(f"Showing the latest {QUEUE_SIZE} transactions as they arrive.")

# ── Controls ──────────────────────────────────────────────────────────────────
col_r, col_a = st.columns([1, 4])
refresh_rate = col_r.selectbox("Refresh (s)", [1, 2, 5], index=1, key="lq_refresh")
auto = col_a.checkbox("Auto-refresh", value=True, key="lq_auto")

placeholder = st.empty()

# ── Render function ───────────────────────────────────────────────────────────

def render():
    try:
        resp = httpx.get(f"{API_BASE_URL}/api/queue", timeout=3)
        data = resp.json()
        items = data.get("items", [])
        source = data.get("source", "")
    except Exception as exc:
        placeholder.error(f"Cannot reach API: {exc}")
        return

    if not items:
        placeholder.info("No transactions yet — start the simulation from the Simulation page.")
        return

    df = pd.DataFrame(items)

    # Tidy display
    display_cols = {
        "transaction_date": "Date / Time",
        "seller_name":      "Seller",
        "seller_country":   "From",
        "buyer_country":    "To",
        "item_description": "Item",
        "item_category":    "Category",
        "value":            "Value (€)",
        "vat_rate":         "VAT Rate",
        "vat_amount":       "VAT Due (€)",
        "has_error":        "⚠ Error",
    }
    df = df[[c for c in display_cols if c in df.columns]].rename(columns=display_cols)
    df["Date / Time"] = pd.to_datetime(df["Date / Time"], utc=True).dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    df["Value (€)"]   = df["Value (€)"].map(lambda x: f"{x:,.2f}")
    df["VAT Rate"]    = df["VAT Rate"].map(lambda x: f"{x*100:.1f}%")
    df["VAT Due (€)"] = df["VAT Due (€)"].map(lambda x: f"{x:,.2f}")
    df["⚠ Error"]    = df["⚠ Error"].map(lambda x: "❌ Yes" if x else "✅ No")

    with placeholder.container():
        badge = "🟢 Live" if source == "live" else "📦 Historical"
        st.caption(badge)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "⚠ Error": st.column_config.TextColumn(width="small"),
            },
        )

        # Mini KPIs
        k1, k2, k3, k4 = st.columns(4)
        raw = data.get("items", [])
        k1.metric("Transactions shown", len(raw))
        total_vat = sum(r.get("vat_amount", 0) for r in raw)
        k2.metric("VAT in queue (€)", f"{total_vat:,.2f}")
        errors = sum(1 for r in raw if r.get("has_error"))
        k3.metric("Rate errors", errors)
        countries = len({r.get("buyer_country") for r in raw})
        k4.metric("Buyer countries", countries)


render()

if auto:
    time.sleep(refresh_rate)
    st.rerun()
