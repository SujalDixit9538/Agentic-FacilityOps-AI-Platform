import sys
from pathlib import Path
import streamlit as st


root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)


import pandas as pd
from frontend.services.api_client import safe_get
from frontend.components.status import render_status_banner, render_empty_state

# Page Configuration
st.set_page_config(page_title="Cost Optimization | FacilityOPS", layout="wide")

st.title("💰 Cost Optimization")
st.markdown("Track, analyze, and optimize facility operating expenses.")

# 1. Module Health Check Integration
health_data = safe_get("/cost/health")
is_online = health_data.get("success", False)

if not is_online:
    render_status_banner(
        is_online=False, 
        custom_message="Cost API is currently unreachable. Displaying cached layout."
    )
    st.stop() # Halts execution safely

status_info = health_data.get("data", {})
if status_info.get("status") == "operational":
    st.success(f"Module Status: Operational | Intelligence Engine: {status_info.get('intelligence_engine', 'Pending')}")

st.divider()

# 2. Facility Selection
selected_facility = st.selectbox("Select Target Facility", ["FAC-001", "FAC-002"])

# 3. Data Retrieval & Visualization
st.markdown("### 📊 Expense Breakdown")
with st.spinner("Loading financial records..."):
    cost_response = safe_get(f"/cost/records/{selected_facility}?limit=100")
    
    if cost_response.get("success"):
        records = cost_response.get("data", {}).get("records", [])
        
        if not records:
            render_empty_state("Financial Tracking", "No cost data recorded for this facility yet. Awaiting ingestion.")
        else:
            df_costs = pd.DataFrame(records)
            df_costs['incurred_date'] = pd.to_datetime(df_costs['incurred_date']).dt.strftime('%Y-%m-%d')
            
            # Calculate High-Level Metrics
            total_cost = df_costs['amount'].sum()
            st.metric("Total Incurred Expenses", f"${total_cost:,.2f}")
            
            # Layout for charts and tables
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("#### Cost by Category")
                category_totals = df_costs.groupby('category')['amount'].sum().reset_index()
                # Format currency for display
                category_totals['amount'] = category_totals['amount'].apply(lambda x: f"${x:,.2f}")
                st.dataframe(category_totals, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("#### Recent Transactions")
                # Format currency for display
                df_display = df_costs[['record_id', 'category', 'description', 'amount', 'incurred_date']].copy()
                df_display['amount'] = df_display['amount'].apply(lambda x: f"${x:,.2f}")
                st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.error("Failed to retrieve cost records.")