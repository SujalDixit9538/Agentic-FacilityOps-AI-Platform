import sys
from pathlib import Path
import streamlit as st

root_dir = str(Path(__file__).parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.utils.session import initialize_session
from frontend.services.api_client import safe_get
from frontend.components.status import render_status_banner

# Must be the very first Streamlit command
st.set_page_config(
    page_title="FacilityOPS AI",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize global state
initialize_session()

st.title("🏢 Agentic FacilityOPS AI Platform")
st.markdown("### Executive Operations Center")

# Integration Test: Fetch backend health
with st.spinner("Connecting to platform services..."):
    health_data = safe_get("/health", fallback_data={"status": "unreachable", "database": "unreachable"})

# Evaluate platform status
backend_online = health_data.get("success", False)
db_operational = health_data.get("data", {}).get("database") == "operational"

if backend_online and db_operational:
    st.success("Platform connection established. All systems nominal.")
else:
    render_status_banner(
        is_online=False, 
        custom_message="Platform is running in degraded mode. Some services may be unavailable."
    )

st.markdown("### System Status")
st.markdown(f"""
* **Backend API:** {'🟢 Operational' if backend_online else '🔴 Offline'}
* **Database Layer:** {'🟢 Operational' if db_operational else '🔴 Offline'}
* **Frontend Interface:** 🟢 Operational
* **Active Agents:** Energy Agent
""")

st.info("Please select a module from the sidebar navigation to begin.")







# import sys
# from pathlib import Path
# import streamlit as st

# root_dir = str(Path(__file__).parent.parent.absolute())
# if root_dir not in sys.path:
#     sys.path.insert(0, root_dir)

# from frontend.utils.session import initialize_session
# from frontend.services.api_client import safe_get
# from frontend.components.status import render_status_banner

# # Must be the very first Streamlit command
# st.set_page_config(
#     page_title="FacilityOPS AI",
#     page_icon="🏢",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Initialize global state
# initialize_session()

# st.title("🏢 Agentic FacilityOPS AI Platform")
# st.markdown("### Executive Operations Center")
# st.markdown("Unified platform intelligence leveraging predictive ML and autonomous agent orchestration.")

# # Integration Test: Fetch backend health
# with st.spinner("Connecting to platform services..."):
#     health_data = safe_get("/health", fallback_data={"status": "unreachable", "database": "unreachable"}) or {}

# # Evaluate platform status
# backend_online = health_data.get("success", False)
# db_operational = health_data.get("data", {}).get("database") == "operational"

# if not (backend_online and db_operational):
#     render_status_banner(
#         is_online=False, 
#         custom_message="Platform is running in degraded mode. Core services may be unavailable."
#     )

# st.divider()

# # ==========================================
# # EXECUTIVE ML DIAGNOSTICS (Milestones 1 & 2)
# # ==========================================
# st.markdown("### 🧠 Live Platform Intelligence")
# st.info("Click below to trigger a concurrent, multi-agent ML diagnostic across the facility portfolio.")

# if st.button("Run Global AI Diagnostics", type="primary"):
#     with st.spinner("Orchestrating Energy and Maintenance AI Agents..."):
        
#         # 1. Trigger the AI Agents via API (Added "or {}" to prevent NoneType crashes)
#         energy_data = safe_get("/api/v1/energy/analyze/FAC-001") or {}
#         maint_data = safe_get("/api/v1/maintenance/analyze/AST-8BAA47") or {}

#         # 2. Extract standard JSON structures
#         e_analysis = energy_data.get("data", {}).get("analysis", {})
#         m_analysis = maint_data.get("data", {}).get("analysis", {})

#         # 3. Create a clean 2-column layout for the mentor presentation
#         col1, col2 = st.columns(2)

#         # --- MODULE 1: ENERGY ---
#         with col1:
#             st.subheader("⚡ Energy Analytics")
#             e_metrics = e_analysis.get("metrics", {})
#             e_source = e_analysis.get("intelligence_source", "Pending / Rules")
#             st.caption(f"**Engine:** {e_source}")
            
#             if e_metrics:
#                 st.metric("Predicted Usage", f"{e_metrics.get('predicted_usage_kwh', 0):.1f} kWh", 
#                           delta=f"{e_metrics.get('efficiency_delta_pct', 0):.1f}% vs baseline", delta_color="inverse")
                
#                 e_anomalies = e_analysis.get("anomalies", [])
#                 if e_anomalies:
#                     st.error(f"{len(e_anomalies)} Efficiency Anomalies Detected")
#                 else:
#                     st.success("Grid usage optimal.")
#             else:
#                 st.warning("Awaiting sensor data or backend is unreachable.")

#         # --- MODULE 2: MAINTENANCE ---
#         with col2:
#             st.subheader("🔧 Predictive Maintenance")
#             m_metrics = m_analysis.get("metrics", {})
#             m_source = m_analysis.get("intelligence_source", "Pending / Rules")
#             st.caption(f"**Engine:** {m_source}")
            
#             if m_metrics:
#                 health = m_metrics.get("asset_health_score", 0)
#                 st.metric("Asset Health Score (AST-8BAA47)", f"{health}%", 
#                           delta="Critical" if health < 50 else "Stable", delta_color="normal" if health >= 50 else "inverse")
                
#                 issue = m_metrics.get("predicted_issue", "None")
#                 if issue != "Normal Operation":
#                     st.error(f"Predicted Fault: {issue}")
#                 else:
#                     st.success("No imminent faults detected.")
#             else:
#                 st.warning("Awaiting telemetry or backend is unreachable.")