import sys
from pathlib import Path
import streamlit as st

root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.services.api_client import safe_get

# Page Configuration
st.set_page_config(page_title="Executive Dashboard | FacilityOPS", layout="wide")

st.title("🏢 Executive Platform Summary")
st.markdown("Unified cross-domain intelligence and facility health orchestration.")
st.divider()

# 1. Facility Selection
selected_facility = st.selectbox("Select Target Facility", ["FAC-001", "FAC-002"])

# 2. Executive Intelligence Trigger
st.markdown("### 🧠 Platform-Wide Orchestration")
st.info("The Executive Agent polls the Energy, Maintenance, Occupancy, and Cost modules to synthesize a master facility report.")

if st.button("🌐 Generate Cross-Module Intelligence Report", type="primary", use_container_width=True):
    with st.spinner(f"Executive Agent is orchestrating analysis for {selected_facility}..."):
        response = safe_get(f"/executive/analyze/{selected_facility}")
        
        if response.get("success"):
            data = response.get("data", {})
            status = data.get("executive_status", "Unknown")
            insights = data.get("executive_insights", {})
            alerts = data.get("consolidated_alerts", [])
            recs = data.get("consolidated_recommendations", [])
            domains = data.get("domain_reports", {})
            
            st.divider()
            
            # --- 1. Master Platform Status ---
            status_color = "red" if status == "CRITICAL EMERGENCY" else "orange" if status == "ELEVATED RISK" else "blue" if status == "MODERATE WARNINGS" else "green"
            st.markdown(f"## Overall Platform Status: :{status_color}[{status}]")
            
            # --- 2. AI Executive Insights (GROQ LLM) ---
            if insights:
                st.markdown("### 🤖 Agentic AI Summary")
                st.info(f"**Executive Overview:** {insights.get('executive_summary', 'No summary available.')}")
                st.success(f"**Strategic Reasoning:** {insights.get('strategic_explanation', 'No explanation available.')}")
            
            st.divider()
            
            # --- 3. Domain Sub-Reports ---
            st.markdown("#### Domain Intelligence Metrics")
            col1, col2, col3 = st.columns(3)
            col1.metric("Energy Efficiency", f"{domains.get('energy_efficiency', 'N/A')}")
            col2.metric("Security Threat Level", domains.get('security_threat_level', 'Unknown'))
            col3.metric("Financial Status", domains.get('financial_status', 'Unknown'))
            
            st.divider()
            
            # --- 4. Consolidated Alerts Layout ---
            colA, colB = st.columns(2)
            
            with colA:
                st.markdown(f"#### ⚠️ Active Platform Alerts ({data.get('total_active_alerts', 0)})")
                if alerts:
                    for alert in alerts:
                        severity = alert.get("severity", "Low")
                        alert_color = "red" if severity == "High" else "orange" if severity == "Medium" else "green"
                        
                        # Show which sub-agent generated the alert
                        source_badge = alert.get("source", "Agent")
                        
                        with st.expander(f"[{severity.upper()}] {alert.get('type')} | Origin: {source_badge}"):
                            st.write(f"**Message:** {alert.get('message')}")
                            if 'alert_id' in alert:
                                st.caption(f"Alert ID: {alert.get('alert_id')}")
                else:
                    st.success("✅ No active alerts across any domains.")
            
            # --- 5. Master Action Plan Layout ---
            with colB:
                st.markdown("#### 🛠️ Master Action Plan")
                if recs:
                    for rec in recs:
                        priority = rec.get("priority", "Low")
                        p_color = "red" if priority == "High" else "orange" if priority == "Medium" else "green"
                        
                        st.markdown(f"- **{rec.get('action')}** (Priority: :{p_color}[{priority}])")
                        if 'trigger' in rec:
                            st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;*Addresses: {rec.get('trigger')}*")
                else:
                    st.info("No urgent actions required at this time.")
                    
        else:
            st.error("Failed to communicate with the Executive Agent or sub-systems are offline.")