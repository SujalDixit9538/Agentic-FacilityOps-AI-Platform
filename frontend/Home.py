import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

root_dir = str(Path(__file__).parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.components.kpi_cards import render_kpi_row
from frontend.components.status import render_status_banner
from frontend.services.api_client import safe_get
from frontend.utils.session import initialize_session, set_selected_facility


st.set_page_config(
    page_title="FacilityOPS AI",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_session()

st.title("FacilityOPS AI")
st.caption("Facility intelligence for energy, maintenance, occupancy & security, and cost operations.")

with st.spinner("Connecting to platform services..."):
    health_data = safe_get(
        "/health",
        fallback_data={"status": "unreachable", "database": "unreachable"},
    ) or {}
    facilities_data = safe_get("/maintenance/facilities", fallback_data={"facilities": [], "facility_options": []}) or {}
    health_checked_at = datetime.now(timezone.utc)

backend_online = health_data.get("success", False)
health_payload = health_data.get("data", {}) or {}

facilities_payload = facilities_data.get("data", {}) or {}
facility_ids = facilities_payload.get("facilities", []) or []
facility_options = facilities_payload.get("facility_options", []) or []
option_by_id = {item.get("facility_id"): item for item in facility_options if item.get("facility_id")}

# Backward-compatible fallback for older API responses that only return IDs.
if not facility_options:
    facility_options = [{"facility_id": facility_id, "name": facility_id} for facility_id in facility_ids]

if backend_online and health_payload.get("database") == "operational":
    st.success("Platform online · Data services connected")
else:
    render_status_banner(
        is_online=False,
        custom_message="Platform is running in degraded mode. Some services may be unavailable.",
    )

if facility_options:
    current = st.session_state.get("selected_facility_id")
    option_ids = [item["facility_id"] for item in facility_options]
    if current not in option_ids:
        current = option_ids[0]

    def format_facility(facility_id: str) -> str:
        item = option_by_id.get(facility_id, {})
        name = item.get("name") or facility_id
        facility_type = item.get("facility_type")
        return f"{name} · {facility_id}" if not facility_type else f"{name} · {facility_type} · {facility_id}"

    selected = st.selectbox(
        "Facility under analysis",
        option_ids,
        index=option_ids.index(current),
        format_func=format_facility,
        help="Choose the facility for the next intelligence workflow.",
    )
    set_selected_facility(selected)
    selected_meta = option_by_id.get(selected, {})
    meta = [selected]
    if selected_meta.get("total_area_sqft"):
        meta.append(f"{selected_meta['total_area_sqft']:,.0f} sqft")
    if selected_meta.get("total_floors"):
        meta.append(f"{selected_meta['total_floors']} floors")
    st.caption(" · ".join(meta) + f" · {len(option_ids):,} facilities in catalog")
else:
    selected = None
    st.warning("No facilities are available in the catalog yet. Load the canonical facility dataset before running analysis.")

st.divider()

st.markdown("### Platform status")
status_cards = [
    {
        "title": "Backend API",
        "value": "Operational" if backend_online else "Offline",
        "delta": "Online" if backend_online else "Degraded",
        "help": health_data.get("message", "Health endpoint unavailable."),
    },
    {
        "title": "Database",
        "value": "Operational" if health_payload.get("database") == "operational" else "Offline",
        "delta": "Connected" if health_payload.get("database") == "operational" else "Check required",
        "help": f"Database status: {health_payload.get('database', 'unreachable')}",
    },
    {
        "title": "Facilities",
        "value": f"{len(facility_options):,}",
        "delta": "Catalog loaded" if facility_options else "No catalog",
        "help": "Active facilities exposed by the canonical facility catalog.",
    },
    {
        "title": "Analysis context",
        "value": selected or "Not selected",
        "delta": "Ready" if selected else "Setup required",
        "help": "The facility shared across the Streamlit session.",
    },
    {
        "title": "Last checked",
        "value": health_payload.get("request_time")
        or health_payload.get("timestamp")
        or health_checked_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "delta": None,
        "help": "Captured from the current platform health check.",
    },
]
render_kpi_row(status_cards, columns=3)

st.markdown("### Intelligence workspace")
modules = [
    ("🌐", "Executive Intelligence", "Cross-agent facility health, priorities and recommendations.", "pages/Dashboard.py"),
    ("⚡", "Energy Intelligence", "Consumption trends, anomalies, forecasting and optimization.", "pages/Energy.py"),
    ("🔧", "Maintenance Intelligence", "Asset health, failure risk and maintenance priorities.", "pages/Maintenance.py"),
    ("🛡️", "Occupancy & Security", "Zone utilization, occupancy patterns and security anomalies.", "pages/Occupancy_and_Security.py"),
    ("💵", "Cost Intelligence", "Financial trends, drivers, optimization and savings opportunities.", "pages/Cost.py"),
]

for row_start in range(0, len(modules), 3):
    cols = st.columns(3)
    for column, module in zip(cols, modules[row_start:row_start + 3]):
        icon, name, summary, page = module
        with column:
            with st.container(border=True):
                st.subheader(f"{icon} {name}")
                st.caption(summary)
                st.page_link(page, label=f"Open {name}", icon=icon, width="stretch")

st.markdown("### Demo workflow")
st.info(
    "Choose a facility above, then open Executive Intelligence for the cross-agent view "
    "or jump directly into a domain agent. Dataset/test-case execution and report generation "
    "will be added to this workspace in the upcoming recovery fractions."
)

quick_cols = st.columns(4)
with quick_cols[0]:
    st.page_link("pages/Dashboard.py", label="Executive view", icon="🌐", width="stretch")
with quick_cols[1]:
    st.page_link("pages/Energy.py", label="Energy analysis", icon="⚡", width="stretch")
with quick_cols[2]:
    st.page_link("pages/Maintenance.py", label="Maintenance", icon="🔧", width="stretch")
with quick_cols[3]:
    if st.button("Refresh platform", icon="🔄", width="stretch"):
        st.rerun()
