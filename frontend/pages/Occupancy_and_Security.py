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
st.set_page_config(page_title="Occupancy & Security | FacilityOPS", layout="wide")

with st.sidebar:
    st.markdown("### ⚙️ Module Controls")
    st.info("Simulate facility headcounts and random security incidents.")
    
    seed_facility = st.selectbox("Target Facility", ["FAC-001", "FAC-002"], key="occ_seed_target")
    
    if st.button("🔄 Trigger Mock Data Ingestion", use_container_width=True):
        with st.spinner("Provisioning utilization and security logs..."):
            res = safe_post("/occupancy/seed", params={"facility_id": seed_facility, "days": 7})
            if res.get("success"):
                st.success(f"Ingested {res['data']['occupancy_records_seeded']} headcounts and {res['data']['security_events_seeded']} security events.")
                st.rerun() 
            else:
                st.error("Ingestion pipeline failed.")

st.title("🛡️ Occupancy & Security")
st.markdown("Monitor facility utilization, room headcount, and physical security events.")

# 1. Module Health Check Integration
health_data = safe_get("/occupancy/health")
is_online = health_data.get("success", False)

if not is_online:
    render_status_banner(
        is_online=False, 
        custom_message="Occupancy API is currently unreachable. Displaying cached layout."
    )
    st.stop() # Halts execution safely

status_info = health_data.get("data", {})
if status_info.get("status") == "operational":
    st.success(f"Module Status: Operational | Intelligence Engine: {status_info.get('intelligence_engine', 'Pending')}")

st.divider()

# 2. Facility Selection
selected_facility = st.selectbox("Select Target Facility", ["FAC-001", "FAC-002"])

# 3. Data Retrieval & Visualization Layout
col1, col2 = st.columns(2)

# --- Left Column: Occupancy ---
with col1:
    st.markdown("### 👥 Real-Time Occupancy")
    with st.spinner("Loading utilization data..."):
        occ_response = safe_get(f"/occupancy/records/{selected_facility}?limit=100")
        
        if occ_response.get("success"):
            records = occ_response.get("data", {}).get("records", [])
            if not records:
                render_empty_state("Utilization Tracking", "No occupancy data recorded. Awaiting IoT ingestion.")
            else:
                df_occ = pd.DataFrame(records)
                df_occ['timestamp'] = pd.to_datetime(df_occ['timestamp'])
                df_occ = df_occ.sort_values('timestamp')
                
                # Calculate and display current total headcount
                latest_headcount = df_occ.groupby('room')['occupancy_count'].last().sum()
                st.metric("Current Estimated Headcount", int(latest_headcount))
                
                # Format dates for cleaner UI
                df_display = df_occ[['timestamp', 'floor', 'room', 'occupancy_count']].copy()
                df_display['timestamp'] = df_display['timestamp'].dt.strftime('%m-%d %H:%M')
                st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.error("Failed to retrieve occupancy records.")

# --- Right Column: Security Logs ---
with col2:
    st.markdown("### 🚨 Security Events Log")
    with st.spinner("Loading security logs..."):
        sec_response = safe_get(f"/occupancy/security/{selected_facility}?limit=50")
        
        if sec_response.get("success"):
            events = sec_response.get("data", {}).get("events", [])
            if not events:
                render_empty_state("Security Monitoring", "No security incidents logged. Facility is secure.")
            else:
                df_sec = pd.DataFrame(events)
                df_sec['event_time'] = pd.to_datetime(df_sec['event_time']).dt.strftime('%m-%d %H:%M')
                
                st.dataframe(
                    df_sec[['event_id', 'event_type', 'severity', 'status', 'event_time']],
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.error("Failed to retrieve security events.")