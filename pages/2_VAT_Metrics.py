"""VAT Metrics — aggregated analytics with filters, auto-refresh optional."""
import time
import httpx
import pandas as pd
import streamlit as st

try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from lib.config import API_BASE_URL
from lib.catalog import SUPPLIERS, COUNTRY_NAMES

st.set_page_config(page_title="VAT Metrics", page_icon="📊", layout="wide")
st.title("📊 VAT Metrics")

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.header("Filters")

supplier_options = ["All"] + [s["name"] for s in SUPPLIERS]
sel_supplier = st.sidebar.selectbox("Supplier", supplier_options)

country_options = ["All"] + [f"{k} – {v}" for k, v in COUNTRY_NAMES.items()]
sel_buyer = st.sidebar.selectbox("Buyer country", country_options)
sel_seller = st.sidebar.selectbox("Seller country", country_options)

col_df, col_dt = st.sidebar.columns(2)
date_from = col_df.date_input("From", value=None, key="vm_from")
date_to   = col_dt.date_input("To",   value=None, key="vm_to")

refresh_rate = st.sidebar.selectbox("Auto-refresh (s)", [0, 5, 10, 30], index=2,
                                    format_func=lambda x: "Off" if x == 0 else f"{x}s")


def _code(opt):
    return None if opt == "All" else opt.split(" – ")[0]


params = dict(
    seller_name    = None if sel_supplier == "All" else sel_supplier,
    buyer_country  = _code(sel_buyer),
    seller_country = _code(sel_seller),
    date_from      = str(date_from) if date_from else None,
    date_to        = str(date_to)   if date_to   else None,
)

# ── Fetch metrics ─────────────────────────────────────────────────────────────
try:
    r = httpx.get(f"{API_BASE_URL}/api/metrics", params={k: v for k, v in params.items() if v},
                  timeout=5)
    m = r.json()
except Exception as exc:
    st.error(f"API error: {exc}")
    st.stop()

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Transactions",   f"{m['total_transactions']:,}")
k2.metric("Total value (€)", f"{m['total_value']:,.2f}")
k3.metric("Total VAT due (€)", f"{m['total_vat']:,.2f}")
k4.metric("Rate errors",    f"{m['error_count']:,}")

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────

col_l, col_r = st.columns(2)

# VAT by buyer country
with col_l:
    st.subheader("VAT due by buyer country")
    bc = pd.DataFrame(m["by_buyer_country"])
    if not bc.empty:
        bc = bc.rename(columns={"buyer_country": "Country", "vat": "VAT (€)", "n": "Transactions"})
        bc["Country"] = bc["Country"].map(lambda x: COUNTRY_NAMES.get(x, x))
        if HAS_PLOTLY:
            fig = px.bar(bc, x="Country", y="VAT (€)", color="Country",
                         text_auto=".2s", height=320)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(bc.set_index("Country")["VAT (€)"])
    else:
        st.info("No data")

# VAT by supplier
with col_r:
    st.subheader("VAT due by supplier")
    bs = pd.DataFrame(m["by_seller"])
    if not bs.empty:
        bs = bs.rename(columns={"seller_name": "Supplier", "vat": "VAT (€)", "n": "Transactions"})
        if HAS_PLOTLY:
            fig = px.bar(bs, x="VAT (€)", y="Supplier", orientation="h",
                         color="VAT (€)", color_continuous_scale="Blues", height=320)
            fig.update_layout(showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(bs.set_index("Supplier")["VAT (€)"])
    else:
        st.info("No data")

# VAT over time (daily)
st.subheader("Daily VAT due over time")
dv = pd.DataFrame(m["daily_vat"])
if not dv.empty:
    dv = dv.rename(columns={"day": "Date", "vat": "VAT (€)"})
    dv["Date"] = pd.to_datetime(dv["Date"])
    if HAS_PLOTLY:
        fig = px.line(dv, x="Date", y="VAT (€)", markers=True, height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.line_chart(dv.set_index("Date")["VAT (€)"])
else:
    st.info("No time-series data yet")

# VAT by category
col_cat, col_err = st.columns(2)
with col_cat:
    st.subheader("VAT due by category")
    cat = pd.DataFrame(m["by_category"])
    if not cat.empty and HAS_PLOTLY:
        cat = cat.rename(columns={"item_category": "Category", "vat": "VAT (€)"})
        fig = px.pie(cat, names="Category", values="VAT (€)", height=280)
        st.plotly_chart(fig, use_container_width=True)
    elif not cat.empty:
        st.dataframe(cat, hide_index=True)
    else:
        st.info("No data")

with col_err:
    st.subheader("Error rate")
    total = m["total_transactions"]
    errors = m["error_count"]
    if total:
        pct = errors / total * 100
        st.metric("Transactions with wrong VAT rate",
                  f"{errors:,}",
                  delta=f"{pct:.1f}% of total",
                  delta_color="inverse")
        correct = total - errors
        if HAS_PLOTLY:
            fig = px.pie(
                values=[correct, errors],
                names=["Correct rate", "Wrong rate"],
                color_discrete_sequence=["#2ca02c", "#d62728"],
                height=240,
            )
            st.plotly_chart(fig, use_container_width=True)

# ── Auto-refresh ──────────────────────────────────────────────────────────────
if refresh_rate:
    time.sleep(refresh_rate)
    st.rerun()
