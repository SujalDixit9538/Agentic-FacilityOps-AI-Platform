import sys
import pandas as pd
import streamlit as st
from frontend.services.api_client import safe_get, safe_post
from pathlib import Path
from frontend.components.status import render_status_banner, render_empty_state

root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Page Configuration
st.set_page_config(page_title="Maintenance | FacilityOPS", layout="wide")

with st.sidebar:
    st.markdown("### ⚙️ Module Controls")
    st.info("Simulate asset registration and maintenance history ingestion.")
    
    seed_facility = st.selectbox("Target Facility", ["FAC-001", "FAC-002"], key="maint_seed_target")
    
    if st.button("🔄 Trigger Mock Data Ingestion", use_container_width=True):
        with st.spinner("Provisioning assets and repair logs..."):
            res = safe_post("/maintenance/seed", params={"facility_id": seed_facility})
            if res.get("success"):
                st.success(f"Ingested {res['data']['assets_seeded']} assets and {res['data']['logs_seeded']} logs.")
                st.rerun() 
            else:
                st.error("Ingestion pipeline failed.")

st.title("🔧 Predictive Maintenance")
st.markdown("Monitor facility assets, repair histories, and equipment health.")

# 1. Module Health Check Integration
health_data = safe_get("/maintenance/health")
is_online = health_data.get("success", False)

if not is_online:
    render_status_banner(
        is_online=False, 
        custom_message="Maintenance API is currently unreachable. Displaying cached layout."
    )
    st.stop() # Halts execution safely

status_info = health_data.get("data", {})
if status_info.get("status") == "operational":
    st.success(f"Maintenance Module Status: Operational | Intelligence Engine: {status_info.get('intelligence_engine', 'Pending')}")

st.divider()

# 2. Facility Selection
st.markdown("### Asset Management Dashboard")
selected_facility = st.selectbox("Select Target Facility", ["FAC-001", "FAC-002"])

# 3. Data Retrieval & Visualization
with st.spinner(f"Loading assets for {selected_facility}..."):
    assets_response = safe_get(f"/maintenance/assets/{selected_facility}")
    
    if assets_response.get("success"):
        assets = assets_response.get("data", {}).get("assets", [])
        
        if not assets:
            render_empty_state("Asset Inventory", "No assets registered for this facility. Awaiting data ingestion.")
        else:
            # Display Assets
            df_assets = pd.DataFrame(assets)
            
            # Format dates for cleaner UI
            df_assets['installation_date'] = pd.to_datetime(df_assets['installation_date']).dt.strftime('%Y-%m-%d')
            
            st.dataframe(
                df_assets[['asset_id', 'asset_type', 'status', 'installation_date']], 
                use_container_width=True,
                hide_index=True
            )
            
            st.divider()
            
            # 4. Maintenance Logs Sub-Dashboard
            st.markdown("### 📋 Maintenance History")
            selected_asset = st.selectbox("Select an Asset to view logs", df_assets['asset_id'].tolist())
            
            if selected_asset:
                logs_response = safe_get(f"/maintenance/logs/{selected_asset}?limit=20")
                if logs_response.get("success"):
                    logs = logs_response.get("data", {}).get("logs", [])
                    if not logs:
                        st.info(f"No maintenance history found for asset {selected_asset}.")
                    else:
                        df_logs = pd.DataFrame(logs)
                        df_logs['maintenance_date'] = pd.to_datetime(df_logs['maintenance_date']).dt.strftime('%Y-%m-%d')
                        st.dataframe(
                            df_logs[['log_id', 'issue', 'maintenance_date', 'technician', 'status', 'cost']],
                            use_container_width=True,
                            hide_index=True
                        )
                        
                    st.divider()
                    
                    # --- NEW ETP-012 CODE BELOW ---
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