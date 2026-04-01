"""European Custom Data Hub — Real-Time Demo Dashboard (Streamlit entry point)."""
import streamlit as st

st.set_page_config(
    page_title="European Custom Data Hub",
    page_icon="🇪🇺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Flag_of_Europe.svg/320px-Flag_of_Europe.svg.png",
    width=80,
)
st.sidebar.title("European Custom\nData Hub")
st.sidebar.caption("Real-Time Transaction Demo")
st.sidebar.markdown("---")
st.sidebar.page_link("pages/1_Live_Queue.py",        label="📡 Live Transaction Queue")
st.sidebar.page_link("pages/2_VAT_Metrics.py",       label="📊 VAT Metrics")
st.sidebar.page_link("pages/3_Simulation.py",        label="⚙️ Simulation Control")

st.title("🇪🇺 European Custom Data Hub")
st.markdown(
    """
    Welcome to the **European Custom Data Hub** real-time demo.

    | Page | Description |
    |------|-------------|
    | 📡 **Live Queue** | Last 30 transactions as they arrive in real time |
    | 📊 **VAT Metrics** | Due VAT aggregated by country, supplier, category |
    | ⚙️ **Simulation** | Start, pause, speed and reset the March-2026 replay |

    Use the sidebar to navigate.
    """
)

# Quick stats from the API
import httpx
from lib.config import API_BASE_URL

try:
    r = httpx.get(f"{API_BASE_URL}/health", timeout=2)
    data = r.json()
    col1, col2 = st.columns(2)
    col1.metric("Records in European Custom DB", f"{data['records_in_db']:,}")
    col2.metric("API status", "✅ Online")
except Exception:
    st.warning("API not reachable — start the FastAPI server first: `uvicorn api:app --port 8505`")
