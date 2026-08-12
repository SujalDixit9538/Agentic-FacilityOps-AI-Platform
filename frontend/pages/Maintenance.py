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
    """Injects styles for consistent, clean look."""
    st.markdown(f"""
    <style>
        .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['text_pri']}; }}
        h1, h2, h3, h4 {{ color: {COLORS['text_pri']} !important; font-weight: 600 !important; }}
        .stButton > button {{ border-radius: 8px; border: 1px solid {COLORS['border']}; background-color: {COLORS['surface']}; color: {COLORS['text_pri']}; }}
        .stSelectbox > div {{ background-color: {COLORS['surface']}; }}
        .stMarkdown {{ color: {COLORS['text_pri']}; }}
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
assets_response = safe_get(f"/maintenance/assets-analyzed/{selected_facility}")
assets = assets_response.get("data", {}).get("assets", []) if assets_response else []

if not assets:
    st.warning("No assets registered for this facility.")
else:
    df_assets = pd.DataFrame(assets)
    
    # Header: Fleet Health
    if 'health_score' in df_assets.columns:
        valid_health = df_assets['health_score'].dropna()
        if not valid_health.empty:
            avg_health = valid_health.mean()
            st.markdown(f"### Overall Fleet Health: {avg_health:.1f}%")
            health_gauge(avg_health, title="Facility Average Health Score", size="small")
    
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
            if pd.isna(score): 
                return "Unknown"
            if score >= 90: 
                return "Excellent"
            if score >= 70: 
                return "Good"
            if score >= 50: 
                return "Warning"
            return "Critical"
        
        df_assets['bucket'] = df_assets['health_score'].apply(get_bucket)
        counts = df_assets['bucket'].value_counts(normalize=True) * 100
        
        st.markdown("### Fleet Health Distribution")
        health_distribution_bar(counts.to_dict())
    
    # Sensor Simulator
    def run_prediction(inputs):
        res = safe_post("/maintenance/predict-manual", payload=inputs)
        data = res.get("data")
        # Map the response structure to the format expected by the UI
        if isinstance(data, dict) and "metrics" in data:
            return {
                "health_score": data["metrics"].get("asset_health_score", 0),
                "failure_probability": data["metrics"].get("failure_probability", 1.0 - (data["metrics"].get("asset_health_score", 100.0) / 100.0))
            }
        return {"health_score": 0, "failure_probability": 0}
        
    sensor_simulator_panel(run_prediction)
    
    # Assets Table
    st.markdown("### Asset Risk Overview")
    df_assets['temp_status'] = df_assets['process_temp'].apply(
        lambda x: "🔴 High" if pd.notna(x) and x > 315 else ("🟢 Normal" if pd.notna(x) else "N/A")
    )
    
    # Render table with action buttons
    for _, asset in df_assets.iterrows():
        cols = st.columns([4, 1])
        with cols[0]:
            st.write(f"**{asset['asset_id']}** ({asset['asset_type']}) - Status: {asset['status']}")
            st.caption(f"Issue: {asset['predicted_issue']} | Health: {asset['health_score']}%")
        with cols[1]:
            if st.button("Generate Order", key=f"btn_{asset['asset_id']}"):
            # if st.button("🛠️ AI Order", key=f"btn_{asset['asset_id']}"):
                with st.spinner("Generating..."):
                    res = safe_post(f"/maintenance/generate-workorder/{asset['asset_id']}")
                    if res.get("success"):
                        st.session_state[f"order_{asset['asset_id']}"] = res.get("data", {})
                        st.toast("Work order generated!")
                        st.rerun()
                    else:
                        st.error("Failed.")
        
        # Display stored order if exists
        order_data = st.session_state.get(f"order_{asset['asset_id']}")
        if order_data:
            with st.expander("Order Details", expanded=True):
                st.write(f"**Urgency:** {order_data.get('urgency')}")
                st.write(f"**Date:** {order_data.get('recommended_date')}")
                st.write(f"**Summary:** {order_data.get('work_order_summary')}")
                st.write(f"**Actions:** {', '.join(order_data.get('actions', []))}")
                if st.button("Clear", key=f"clr_{asset['asset_id']}"):
                    del st.session_state[f"order_{asset['asset_id']}"]
                    st.rerun()

    # Alerts
    st.markdown("### Active Alerts")
    
    # Filter assets for alerts (only those with valid health_score)
    df_alerts = df_assets[df_assets['health_score'].notna()].copy()
    
    alerts = []
    for _, row in df_alerts.iterrows():
        score = row['health_score']
        prob = row['failure_probability'] if pd.notna(row['failure_probability']) else 0
        
        if score < 50:
            alerts.append({
                "severity": "high",
                "title": f"{row['asset_id']} ({row['asset_type']}) - Critical Health",
                "description": f"Health score: {score:.1f}<br>Failure probability: {prob:.0%}",
                "facility": selected_facility
            })
        elif score < 70:
            alerts.append({
                "severity": "medium",
                "title": f"{row['asset_id']} ({row['asset_type']}) - Warning Health",
                "description": f"Health score: {score:.1f}<br>Failure probability: {prob:.0%}",
                "facility": selected_facility
            })
            
    if alerts:
        alert_feed(alerts)
    else:
        st.info("No active alerts. System status stable.")