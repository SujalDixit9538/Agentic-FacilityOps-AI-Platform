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

# Integration Test: Fetch backend health (ETP-005)
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
* **Active Agents:** Initialization Pending (Milestone 1)
""")

st.info("Please select a module from the sidebar navigation to begin.")