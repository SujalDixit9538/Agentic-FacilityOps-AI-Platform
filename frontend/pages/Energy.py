import streamlit as st
import pandas as pd
from frontend.services.api_client import safe_get, safe_post
from frontend.components.metrics import render_metric_row
from frontend.components.status import render_status_banner, render_empty_state

# Page Configuration
st.set_page_config(page_title="Energy | FacilityOPS", layout="wide")

st.title("⚡ Energy Intelligence & Monitoring")
st.markdown("Monitor utility data, IoT sensor inputs, and module health.")

# Add the Administrative Sidebar Control
with st.sidebar:
    st.markdown("### ⚙️ Module Controls")
    st.info("Use this tool to simulate an influx of new IoT sensor data.")
    
    seed_facility = st.selectbox("Target Facility", ["FAC-001", "FAC-002"], key="seed_target")
    
    if st.button("🔄 Trigger Mock Data Ingestion", use_container_width=True):
        with st.spinner("Generating time-series data..."):
            # Call our POST endpoint
            res = safe_post("/energy/seed", params={"facility_id": seed_facility, "days": 7})
            if res.get("success"):
                st.success(f"Ingested {res['data']['records_seeded']} new records.")
                st.rerun() # Refresh the page to show new data
            else:
                st.error("Ingestion pipeline failed.")

# 1. Module Health Check Integration
health_data = safe_get("/energy/health")
is_online = health_data.get("success", False)

if not is_online:
    render_status_banner(
        is_online=False, 
        custom_message="Energy API is currently unreachable. Displaying cached layout."
    )
    st.stop() # Halts execution safely

status_info = health_data.get("data", {})
if status_info.get("status") == "operational":
    st.success(f"Energy Module Status: Operational | Intelligence Engine: {status_info.get('intelligence_engine', 'Pending')}")

st.divider()

# 2. Facility Selection
st.markdown("### Executive Dashboard")
selected_facility = st.selectbox("Select Target Facility", ["FAC-001", "FAC-002"])

# 3. Data Retrieval & Visualization
with st.spinner(f"Fetching energy data for {selected_facility}..."):
    records_response = safe_get(f"/energy/records/{selected_facility}?limit=30")
    
    if records_response.get("success"):
        records = records_response.get("data", {}).get("records", [])
        
        if not records:
            render_empty_state("Energy Consumption", "No data records found for this facility. Awaiting initial IoT ingestion.")
        else:
            # Load into Pandas for aggregation and charting
            df = pd.DataFrame(records)
            
            # Calculate basic KPIs
            total_kwh = df['energy_kwh'].sum()
            peak_kw = df['peak_demand_kw'].max() if df['peak_demand_kw'].notna().any() else 0.0
            total_cost = df['cost'].sum() if df['cost'].notna().any() else 0.0

            # Render Shared Metric Components
            metrics = [
                {"title": "Total Energy (Current Period)", "value": f"{total_kwh:,.2f} kWh"},
                {"title": "Peak Demand", "value": f"{peak_kw:,.2f} kW"},
                {"title": "Est. Cost", "value": f"${total_cost:,.2f}"}
            ]
            render_metric_row(metrics)

            # Render Chart
            st.markdown("#### Consumption Trend (kWh)")
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            st.line_chart(df[['energy_kwh']])
    else:
        st.error("Failed to retrieve energy records from the database layer.")