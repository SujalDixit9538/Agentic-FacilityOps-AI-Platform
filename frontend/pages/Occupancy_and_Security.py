
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
    selected_facility = st.session_state.get('occ_seed_target', 'FAC-001')
    if st.button("🔄 Refresh Data Ingestion", use_container_width=True):
        with st.spinner("Provisioning data..."):
            safe_post("/occupancy/seed", params={"facility_id": seed_facility, "days": 7})
            st.rerun()

from datetime import datetime
import plotly.express as px
from frontend.services.api_client import safe_get, safe_post
from frontend.components.status import render_status_banner, render_empty_state

# Professional Styling
st.set_page_config(page_title="Occupancy & Security Intelligence | FacilityOPS", layout="wide")

st.markdown("""
<style>
    .kpi-card { 
        background-color: var(--secondary-background-color); 
        border-radius: 10px; 
        padding: 20px; 
        border: 1px solid var(--border-color); 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
    }
    .kpi-value { font-size: 28px; font-weight: 700; color: #212529; }
    .kpi-label { font-size: 13px; color: #495057; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }
    .alert-card { padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid; color: #212529; font-weight: 500; }
    .alert-high { border-left-color: #dc3545; background-color: #f8d7da; color: #721c24; }
    .alert-med { border-left-color: #fd7e14; background-color: #fff3cd; color: #856404; }
</style>
""", unsafe_allow_html=True)

# 1. Header
st.title("Occupancy & Security")
st.markdown(f"**Facility:** {st.session_state.get('occ_seed_target', 'FAC-001')} | **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
cols = st.columns(4)
cols[0].markdown(f'<div class="kpi-card"><div class="kpi-label">Total Occupants</div><div class="kpi-value">{summary.get("total_occupants", 0)} / {summary.get("total_capacity", 0)}</div></div>', unsafe_allow_html=True)
cols[1].markdown(f'<div class="kpi-card"><div class="kpi-label">Utilization</div><div class="kpi-value">{summary.get("utilization_percent", 0)}%</div></div>', unsafe_allow_html=True)
cols[2].markdown(f'<div class="kpi-card"><div class="kpi-label">Overcrowded Zones</div><div class="kpi-value" style="color: {"red" if summary.get("overcrowded_zones", 0) > 0 else "black"}">{summary.get("overcrowded_zones", 0)}</div></div>', unsafe_allow_html=True)
cols[3].markdown(f'<div class="kpi-card"><div class="kpi-label">Active Alerts</div><div class="kpi-value">{len(data.get("alerts", []))}</div></div>', unsafe_allow_html=True)
st.divider()


# 3. Primary Spatial Occupancy Map
st.markdown("### 🗺️ Live Occupancy Heatmap")
zones = data.get("zones", [])
if zones:
    df_zones = pd.DataFrame(zones)
    fig = px.scatter(df_zones, x="x_position", y="y_position", color="utilization_percent", 
                     size="capacity", hover_name="zone_name", color_continuous_scale="RdYlGn_r")
    fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
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

# 6. Occupancy Alerts
st.markdown("### ⚠️ Occupancy Alerts")
alerts = data.get("alerts", [])
if alerts:
    for al in alerts:
        css_class = "alert-high" if al['severity'] == 'High' else "alert-med"
        st.markdown(f'<div class="alert-card {css_class}"><strong>{al["severity"]} Alert</strong><br>{al["zone_name"]}: {al["message"]}</div>', unsafe_allow_html=True)
else:
    st.info("No active occupancy alerts.")

# 7. Security Operations
st.markdown("### 🔒 Security Operations")
sec_data = safe_get(f"/occupancy/security/{selected_facility}")
sec_events = sec_data.get("data", {}).get("events", [])
if sec_events:
    for event in sec_events:
        st.write(f"- {event.get('timestamp', 'N/A')} | {event.get('description', 'N/A')}")
else:
    st.info("No security events.")


# 5. AI Operations Desk
st.markdown("### 🤖 AI Operations Desk")
analysis = safe_get(f"/occupancy/analyze/{selected_facility}").get("data", {})
if analysis:
    col_ai1, col_ai2 = st.columns([1, 1])
    with col_ai1:
        st.markdown("#### Facility Status")
        st.write(f"Status: {analysis.get('status', 'N/A')}")
        st.write(f"Anomalies: {analysis.get('anomalies_detected', 0)}")
    with col_ai2:
        st.markdown("#### Recommended Actions")
        for rec in analysis.get('recommendations', []):
            st.write(f"- **{rec['priority']}**: {rec['action']}")
else:
    st.info("No AI analysis available.")

