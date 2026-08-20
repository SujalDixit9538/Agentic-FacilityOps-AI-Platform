
import sys
from pathlib import Path
import streamlit as st

root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pandas as pd
from frontend.services.api_client import safe_get, safe_post
from frontend.components.status import render_status_banner, render_empty_state


# Page Configuration
st.set_page_config(page_title="Occupancy & Security Intelligence | FacilityOPS", layout="wide")

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Module Controls")
    seed_facility = st.selectbox("Target Facility", ["FAC-001", "FAC-002"], key="occ_seed_target")
    if st.button("🔄 Refresh Data Ingestion", use_container_width=True):
        with st.spinner("Provisioning data..."):
            safe_post("/occupancy/seed", params={"facility_id": seed_facility, "days": 7})
            st.rerun()

# 1. Header
st.title("Occupancy & Security Intelligence")
st.markdown("Operational dashboard monitoring facility utilization, overcrowding and physical security events.")
selected_facility = st.sidebar.selectbox("Select Facility", ["FAC-001", "FAC-002"])
st.divider()

# API Data Fetch
dashboard_data = safe_get(f"/occupancy/dashboard/{selected_facility}")
success = dashboard_data.get("success", False)
data = dashboard_data.get("data", {})

if not success:
    st.error("Failed to load dashboard data.")
    st.stop()

summary = data.get("summary", {})

# 2. Top KPI row
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Occupants", summary.get('total_occupants', 0))
kpi2.metric("Facility Utilization", f"{summary.get('utilization_percent', 0)}%")
kpi3.metric("Overcrowded Zones", summary.get('overcrowded_zones', 0))
kpi4.metric("Active Alerts", len(data.get('alerts', [])))

st.divider()

# 3. Live Occupancy Heatmap
st.markdown("### 🗺️ Live Occupancy Heatmap")
zones = data.get("zones", [])
if zones:
    cols = st.columns(min(len(zones), 4))
    for i, zone in enumerate(zones):
        with cols[i % 4]:
            util = zone.get('utilization_percent', 0)
            status_color = "🔴" if util > 90 else "🟠" if util > 70 else "🟢"
            st.info(f"**{zone['zone_name']}**\n\n{status_color} {util}% Utilization")
else:
    st.info("No zone data available.")



# 4. Space & Room Utilization
c1, c2 = st.columns(2)
with c1:
    st.markdown("### 📊 Space Utilization Analytics")
    analytics = data.get("zone_analytics", [])
    if analytics:
        df_an = pd.DataFrame(analytics)
        st.dataframe(df_an, use_container_width=True)
    else:
        st.info("No analytics data.")
with c2:
    st.markdown("### 🚪 Room Utilization")
    rooms = data.get("room_utilization", [])
    if rooms:
        df_rooms = pd.DataFrame(rooms)
        st.dataframe(df_rooms, use_container_width=True)
    else:
        st.info("No room data.")

# 5. Alerts
st.markdown("### ⚠️ Occupancy Alerts")
alerts = data.get("alerts", [])
if alerts:
    for al in alerts:
        st.error(f"**{al['severity']}** | {al['zone_name']}: {al['message']}")
else:
    st.success("No active occupancy alerts.")

# 6. Security Operations
st.markdown("### 🔒 Security Operations")
sec_data = safe_get(f"/occupancy/security/{selected_facility}")
sec_events = sec_data.get("data", {}).get("events", [])
if sec_events:
    df_sec = pd.DataFrame(sec_events)
    st.dataframe(df_sec, use_container_width=True)
else:
    st.info("No security events.")

# 7. Agent Intelligence
st.markdown("### 🤖 Intelligence Engine")
if st.button("Run Facility Analysis", type="primary"):
    analysis = safe_get(f"/occupancy/analyze/{selected_facility}")
    if analysis.get("success"):
        st.write(analysis.get("data"))
    else:
        st.error("Analysis failed.")
