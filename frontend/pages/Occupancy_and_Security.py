import sys
from pathlib import Path
import streamlit as st
import pandas as pd

root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.services.api_client import safe_get
from frontend.components.kpi_cards import render_kpi_row

st.set_page_config(page_title="Occupancy Intelligence | FacilityOPS", layout="wide")

with st.sidebar:
    st.markdown("### ⚙️ Facility Selection")
    facility_id = st.selectbox("Select Facility", ["FAC-001", "FAC-002"])

st.title("Occupancy Intelligence")
st.markdown("Real-time space utilization and occupancy monitoring")
st.divider()

# Main Dashboard
dashboard_data = safe_get(f"/v1/occupancy/dashboard/{facility_id}")

if not dashboard_data.get("success"):
    st.error("Occupancy data is currently unavailable.")
else:
    data = dashboard_data.get("data", {})
    summary = data.get("summary", {})
    
    # KPIs
    kpis = [
        {"title": "Total Occupants", "value": str(summary.get("total_occupants", 0))},
        {"title": "Overall Utilization", "value": f"{summary.get('utilization_percent', 0)}%"},
        {"title": "Overcrowded Zones", "value": str(summary.get("overcrowded_zones", 0))},
        {"title": "Highly Utilized", "value": str(summary.get("highly_utilized_zones", 0))},
    ]
    render_kpi_row(kpis)
    
    # Alerts
    alerts = data.get("alerts", [])
    if alerts:
        st.markdown("## Occupancy Alerts")
        for alert in alerts:
            st.error(f"**{alert.get('alert_type')}**\n\n{alert.get('message')}\n\nUtilization: {alert.get('utilization_percent')}%")
    
    # Heatmap
    st.markdown("## Occupancy Heatmap")
    zones = data.get("zones", [])
    if zones:
        cols = st.columns(4)
        for i, zone in enumerate(zones):
            util = zone.get("utilization_percent", 0)
            color = "green" if util < 40 else "orange" if util < 80 else "red"
            with cols[i % 4]:
                st.markdown(f"""
                <div style="border: 2px solid {color}; padding: 10px; border-radius: 5px; margin-bottom: 10px; text-align: center;">
                    <strong>{zone.get('zone_name')}</strong><br>
                    {zone.get('occupancy')} / {zone.get('capacity')}<br>
                    {util}%
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No occupancy zones found.")
