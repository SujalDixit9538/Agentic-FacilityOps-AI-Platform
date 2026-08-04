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
st.set_page_config(page_title="Cost Optimization | FacilityOPS", layout="wide")

with st.sidebar:
    st.markdown("### ⚙️ Module Controls")
    st.info("Simulate facility financial records and historical expenses.")
    
    seed_facility = st.selectbox("Target Facility", ["FAC-001", "FAC-002"], key="cost_seed_target")
    
    if st.button("🔄 Trigger Finance Ingestion", use_container_width=True):
        with st.spinner("Provisioning financial ledgers..."):
            res = safe_post("/cost/seed", params={"facility_id": seed_facility, "months": 6})
            if res.get("success"):
                st.success(f"Ingested {res['data']['financial_records_seeded']} financial records.")
                st.rerun() 
            else:
                st.error("Ingestion pipeline failed.")


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
    st.success(f"Module Status: Operational")
    # st.success(f"Module Status: Operational | Intelligence Engine: {status_info.get('intelligence_engine', 'Pending')}")

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

# 4. Agentic Intelligence Section
st.markdown("### 🤖 Intelligence Engine: Cost Optimization Agent")
st.info("The Agent continuously analyzes historical ledgers to identify budget overruns and utility cost spikes.")

if st.button("🧠 Run Financial Analysis", type="primary", use_container_width=True):
    with st.spinner(f"Agent is evaluating financial health for {selected_facility}..."):
        analysis_response = safe_get(f"/cost/analyze/{selected_facility}")
        
        if analysis_response.get("success"):
            insights = analysis_response.get("data", {})
            alerts = insights.get("alerts", [])
            recommendations = insights.get("recommendations", [])  # <-- Extract new recommendations data
            analysis_data = insights.get("analysis", {})
            financial_status = analysis_data.get("financial_status", "Unknown")
            metrics = analysis_data.get("metrics", {})
            
            # Display Financial Status
            status_color = "green" if financial_status == "Optimized" else "orange" if financial_status == "Review Required" else "red"
            st.markdown(f"#### Overall Financial Status: :{status_color}[{financial_status}]")
            
            # Display Key Metrics
            if "latest_energy_variance" in metrics:
                variance = metrics["latest_energy_variance"]
                st.metric("Latest Energy Variance (MoM)", f"{variance}%", delta=f"{variance}%", delta_color="inverse")
            
            # Render Anomalies / Alerts
            if alerts:
                st.error(f"⚠️ Agent flagged {len(alerts)} financial anomalies.")
                for alert in alerts:
                    with st.expander(f"[{alert['severity'].upper()}] {alert['type']} (Click for details)"):
                        st.write(f"**Message:** {alert['message']}")
                        st.caption(f"Generated by: {alert['source']} | ID: {alert['alert_id']}")
            else:
                st.success("✅ No critical budget anomalies detected. Facility spending is optimized.")

            
            # Render Actionable Recommendations
            st.markdown("#### 📉 Recommended Cost Reductions")
            if recommendations:
                for rec in recommendations:
                    # Map priority to Streamlit text colors for quick scanning
                    priority_color = "red" if rec.get('priority') == "High" else "orange" if rec.get('priority') == "Medium" else "green"
                    
                    st.markdown(f"- **{rec.get('action')}** (Priority: :{priority_color}[{rec.get('priority', 'Low')}])")
                    if 'trigger' in rec:
                        st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;*Mitigates: {rec.get('trigger')}*")
            else:
                st.info("No specific cost reduction strategies required at this time.")
            

        else:
            st.error("Agent analysis failed to execute or backend is unreachable.")