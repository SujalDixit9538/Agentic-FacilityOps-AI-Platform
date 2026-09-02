import sys
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st

root_dir = str(Path(__file__).parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.utils.session import initialize_session
from frontend.services.api_client import safe_get
from frontend.components.kpi_cards import render_kpi_row
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

st.title("**Agentic FacilityOPS AI Platform**")
st.markdown("### Executive Operations Center")

# Integration Test: Fetch backend health
with st.spinner("Connecting to platform services..."):
    health_data = safe_get("/health", fallback_data={"status": "unreachable", "database": "unreachable"}) or {}
    health_checked_at = datetime.now(timezone.utc)

# Evaluate platform status
backend_online = health_data.get("success", False)
health_payload = health_data.get("data", {}) or {}
db_operational = health_payload.get("database") == "operational"
health_timestamp = (
    health_payload.get("request_time")
    or health_payload.get("timestamp")
    or health_payload.get("checked_at")
    or health_checked_at.strftime("%Y-%m-%d %H:%M:%S UTC")
)

if backend_online and db_operational:
    st.success("Platform connection established. All systems nominal.")
else:
    render_status_banner(
        is_online=False, 
        custom_message="Platform is running in degraded mode. Some services may be unavailable."
    )

st.divider()

st.markdown("### System Status")
status_cards = [
    {
        "title": "Backend API",
        "value": "Operational" if backend_online else "Offline",
        "delta": "Online" if backend_online else "Degraded",
        "help": health_data.get("message", "Health endpoint unavailable."),
    },
    {
        "title": "Database Layer",
        "value": "Operational" if db_operational else "Offline",
        "delta": "Connected" if db_operational else "Check required",
        "help": f"Health payload: {health_payload.get('database', 'unreachable')}",
    },
    {
        "title": "Frontend Interface",
        "value": "Operational",
        "delta": "Available",
        "help": "Streamlit application is loaded.",
    },
    {
        "title": "Active Agents",
        "value": "Energy Agent",
        "delta": "Available",
        "help": "Configured agent surfaced on the home dashboard.",
    },
    {
        "title": "Last Checked",
        "value": health_timestamp,
        "delta": None,
        "help": "Captured from the current health check.",
    },
]
render_kpi_row(status_cards, columns=3)

st.markdown("### Available Modules")
modules = [
    {
        "name": "Executive Dashboard",
        "icon": "🌐",
        "page": "pages/Dashboard.py",
        "summary": "Cross-module intelligence and portfolio reporting.",
    },
    {
        "name": "Energy Analytics",
        "icon": "⚡",
        "page": "pages/Energy.py",
        "summary": "Energy records, diagnostics, and optimization workflows.",
    },
    {
        "name": "Predictive Maintenance",
        "icon": "🔧",
        "page": "pages/Maintenance.py",
        "summary": "Asset health review and maintenance intelligence.",
    },
    {
        "name": "Cost Intelligence",
        "icon": "💵",
        "page": "pages/Cost.py",
        "summary": "Facility cost records and financial analysis.",
    },
    {
        "name": "Occupancy & Security",
        "icon": "🛡️",
        "page": "pages/Occupancy_and_Security.py",
        "summary": "Occupancy signals and security event review.",
    },
]

for row_start in range(0, len(modules), 3):
    row_modules = modules[row_start:row_start + 3]
    for column, module in zip(st.columns(3), row_modules):
        with column:
            with st.container(border=True):
                st.subheader(f"{module['icon']} {module['name']}")
                st.caption(module["summary"])
                st.page_link(
                    module["page"],
                    label=f"Open {module['name']}",
                    icon=module["icon"],
                    width="stretch",
                )

st.markdown("### Quick Actions")
quick_cols = st.columns([1, 1, 1, 1])
with quick_cols[0]:
    st.page_link(
        "pages/Dashboard.py",
        label="Executive Report",
        icon="🌐",
        width="stretch",
    )
with quick_cols[1]:
    st.page_link(
        "pages/Energy.py",
        label="Energy Review",
        icon="⚡",
        width="stretch",
    )
with quick_cols[2]:
    st.page_link(
        "pages/Maintenance.py",
        label="Asset Review",
        icon="🔧",
        width="stretch",
    )
with quick_cols[3]:
    if st.button("Refresh Status", icon="🔄", width="stretch"):
        st.rerun()

placeholder_cols = st.columns(2)
with placeholder_cols[0]:
    st.button("Global Diagnostics", disabled=True, width="stretch")
with placeholder_cols[1]:
    st.button("Alert Inbox", disabled=True, width="stretch")
