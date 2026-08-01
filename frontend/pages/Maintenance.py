import streamlit as st
import pandas as pd
from frontend.services.api_client import safe_get
from frontend.components.status import render_status_banner, render_empty_state

# Page Configuration
st.set_page_config(page_title="Maintenance | FacilityOPS", layout="wide")

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
                else:
                    st.error("Failed to retrieve maintenance logs.")
    else:
        st.error("Failed to retrieve assets from the database layer.")