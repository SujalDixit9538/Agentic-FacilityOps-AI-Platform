import sys
from pathlib import Path
root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pandas as pd
import streamlit as st
from frontend.services.api_client import safe_get, safe_post
from frontend.components.ui import (
    kpi_card,
    health_gauge,
    health_distribution_bar,
    risk_table,
    sensor_simulator_panel,
    alert_feed
)
from frontend.utils.theme import COLORS

# Page Configuration
st.set_page_config(page_title="Maintenance | FacilityOPS", layout="wide")

def inject_theme():
    """Injects dark theme background."""
    st.markdown(f"""
    <style>
        .stApp {{ background-color: {COLORS['bg']}; }}
    </style>
    """, unsafe_allow_html=True)

inject_theme()

with st.sidebar:
    st.markdown("### ⚙️ Module Controls")
    
    # Fetch facilities from backend
    resp = safe_get("/maintenance/facilities")
    facilities = resp.get("data", {}).get("facilities", ["F-0000", "F-0001"])
    
    seed_facility = st.selectbox("Target Facility", facilities, key="maint_seed_target")

    if st.button("🔄 Trigger Mock Data Ingestion", use_container_width=True):
        with st.spinner("Provisioning assets..."):
            res = safe_post("/maintenance/seed", params={"facility_id": seed_facility})
            if res.get("success"):
                st.success(f"Ingested {res['data']['assets_seeded']} assets.")
                st.rerun() 
            else:
                st.error("Ingestion pipeline failed.")

st.title(f"🔧 Predictive Maintenance: {seed_facility}")

# Facility Selection
selected_facility = seed_facility

# Data Retrieval
assets_response = safe_get(f"/maintenance/assets/{selected_facility}")
assets = assets_response.get("data", {}).get("assets", [])

if not assets:
    st.warning("No assets registered for this facility.")
else:
    df_assets = pd.DataFrame(assets)
    
    # Compute Metrics
    num_assets = len(df_assets)
    open_tickets = len(df_assets[df_assets['status'] == 'Maintenance Required']) if 'status' in df_assets.columns else 0
    # Fix: use column selection syntax properly instead of dict-like get()
    crit_risk = len(df_assets[df_assets['failure_probability'] > 0.5]) if 'failure_probability' in df_assets.columns else 0
    avg_health = df_assets['health_score'].mean() if 'health_score' in df_assets.columns else 0.0
    
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Assets Monitored", str(num_assets), icon="🏢")
    with col2:
        kpi_card("Open Work Orders", str(open_tickets), status="warning" if open_tickets > 0 else "good")
    with col3:
        kpi_card("Critical Risks", str(crit_risk), status="critical" if crit_risk > 0 else "good")
    with col4:
        kpi_card("Avg Fleet Health", f"{avg_health:.1f}%", status="good" if avg_health >= 80 else "warning")
        
    # Health Distribution
    if 'health_score' in df_assets.columns:
        def get_bucket(score):
            if score >= 90: return "Excellent"
            if score >= 70: return "Good"
            if score >= 50: return "Warning"
            return "Critical"
        
        df_assets['bucket'] = df_assets['health_score'].apply(get_bucket)
        counts = df_assets['bucket'].value_counts(normalize=True) * 100
        
        st.markdown("### Fleet Health Distribution")
        health_distribution_bar(counts.to_dict())
    
    # Sensor Simulator
    def run_prediction(inputs):
        res = safe_post("/maintenance/predict-manual", payload=inputs)
        data = res.get("data")
        return data if isinstance(data, dict) else {"health_score": 0, "failure_probability": 0}
        
    sensor_simulator_panel(run_prediction)
    
    # Assets Table
    st.markdown("### Asset Risk Overview")
    risk_cols = ['asset_id', 'facility_id', 'asset_type']
    if 'health_score' in df_assets.columns:
        risk_cols.append('health_score')
    if 'failure_probability' in df_assets.columns:
        risk_cols.append('failure_probability')
    risk_table(df_assets[risk_cols])

    # Alerts (Dummy for now as alert data structure needs identification)
    st.markdown("### Active Alerts")
    alerts = [{
        "severity": "high", 
        "title": "Critical Asset Risk", 
        "description": "High failure risk detected on asset A-001",
        "facility_id": seed_facility
    }]
    alert_feed(alerts)