import sys
import pandas as pd
import streamlit as st
from frontend.services.api_client import safe_get, safe_post
from pathlib import Path
from frontend.components.ui import (
    kpi_card,
    health_gauge,
    health_distribution_bar,
    risk_table,
    sensor_simulator_panel,
    alert_feed
)
from frontend.utils.theme import COLORS

root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

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
    facilities = resp.get("data", {}).get("facilities", ["FAC-001", "FAC-002"])
    
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
    open_tickets = len(df_assets[df_assets['status'] == 'Maintenance Required'])
    crit_risk = len(df_assets[df_assets.get('failure_probability', 0) > 0.5])
    avg_health = df_assets['health_score'].mean()
    
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
        # We need to find the asset id or just pass inputs to the analyzer
        # Actually the backend expects asset_id
        # Let's just pick the first asset for the mock-up logic or skip if not ideal
        res = safe_get(f"/maintenance/analyze/{df_assets.iloc[0]['asset_id']}")
        return res.get("data", {})
        
    sensor_simulator_panel(run_prediction)
    
    # Assets Table
    st.markdown("### Asset Risk Overview")
    risk_table(df_assets[['asset_id', 'facility_id', 'asset_type', 'health_score', 'failure_probability']])

    # Alerts (Dummy for now as alert data structure needs identification)
    st.markdown("### Active Alerts")
    alerts = [{"severity": "high", "message": "High failure risk detected on asset A-001"}]
    alert_feed(alerts)

                    # 5. Agentic Intelligence Section
                    st.markdown("### 🤖 Intelligence Engine: Maintenance Agent")
                    st.info("The Maintenance Agent analyzes asset age, expected lifespan, and historical repair logs to predict failure risks.")
                    
                    if st.button("🧠 Run Health Analysis", type="primary", use_container_width=True):
                        with st.spinner(f"Agent is analyzing {selected_asset}..."):
                            analysis_response = safe_get(f"/maintenance/analyze/{selected_asset}")
                            
                            if analysis_response.get("success"):
                                insights = analysis_response.get("data", {})
                                alerts = insights.get("alerts", [])
                                recommendations = insights.get("recommendations", []) # <-- Extract new recommendations data
                                health_status = insights.get("analysis", {}).get("health_status", "Unknown")
                                metrics = insights.get("analysis", {}).get("metrics", {})
                                
                                # Display Health Status
                                status_color = "green" if health_status == "Healthy" else "orange" if health_status == "Degraded" else "red"
                                st.markdown(f"#### Overall Health Status: :{status_color}[{health_status}]")
                                
                                # Display Metrics
                                col1, col2, col3 = st.columns(3)
                                col1.metric("Life Consumed", f"{metrics.get('life_consumed_pct', 0)}%")
                                col2.metric("Total Repair Cost", f"${metrics.get('total_repair_cost', 0):,.2f}")
                                col3.metric("Recent Repairs (365d)", metrics.get("recent_repairs", 0))
                                
                                # Render Anomalies / Alerts
                                if alerts:
                                    st.error(f"⚠️ Agent flagged {len(alerts)} risk factors.")
                                    for alert in alerts:
                                        with st.expander(f"[{alert['severity'].upper()}] {alert['type']} (Click for details)"):
                                            st.write(f"**Message:** {alert['message']}")
                                            st.caption(f"Generated by: {alert['source']} | ID: {alert['alert_id']}")
                                else:
                                    st.success("✅ No critical risk factors detected. Asset is operating within normal parameters.")

                                # --- NEW ETP-013 CODE BELOW ---
                                # Render Actionable Recommendations
                                st.markdown("#### 🛠️ Recommended Actions")
                                if recommendations:
                                    for rec in recommendations:
                                        # Map priority to Streamlit text colors for quick scanning
                                        priority_color = "red" if rec.get('priority') == "High" else "orange" if rec.get('priority') == "Medium" else "green"
                                        
                                        st.markdown(f"- **{rec.get('action')}** (Priority: :{priority_color}[{rec.get('priority', 'Low')}])")
                                        if 'trigger' in rec:
                                            st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;*Mitigates: {rec.get('trigger')}*")
                                else:
                                    st.info("No specific maintenance actions required at this time.")
                                # ------------------------------

                            else:
                                st.error("Agent analysis failed to execute or backend is unreachable.")
                else:
                    st.error("Failed to retrieve maintenance logs.")
    else:
        st.error("Failed to retrieve assets from the database layer.")