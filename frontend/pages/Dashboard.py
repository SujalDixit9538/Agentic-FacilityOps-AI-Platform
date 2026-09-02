import sys
from pathlib import Path

import streamlit as st

root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.components.status import render_empty_state, render_status_banner
from frontend.services.api_client import safe_get
from frontend.services.page_data import get_facilities, metadata, state_message

st.set_page_config(page_title="Dashboard | FacilityOPS", layout="wide")
st.title("Facility Operations Overview")
st.caption("A verified, cross-domain view of the facility state and the decisions waiting for attention.")

facilities, _ = get_facilities()
if not facilities:
    render_status_banner(False, "The canonical facility catalog is unavailable.")
    st.stop()
selected_facility = st.selectbox("Facility", facilities, key="dashboard_facility")

energy = safe_get(f"/energy/dashboard/{selected_facility}", fallback_data={})
cost = safe_get(f"/cost/dashboard/{selected_facility}", fallback_data={})
occupancy = safe_get(f"/occupancy/dashboard/{selected_facility}", fallback_data={})
responses = (("Energy", energy), ("Cost", cost), ("Occupancy & security", occupancy))
failures = [name for name, response in responses if not response.get("success")]
if failures:
    render_status_banner(False, f"Unavailable domains: {', '.join(failures)}. Showing only verified domain data.")
elif any(response.get("degraded") for _, response in responses):
    st.warning("Some domain data is degraded or incomplete. Review freshness and quality before acting.")

st.markdown(f"### {selected_facility}")
status_cols = st.columns(4)
energy_data = energy.get("data") or {}
cost_data = cost.get("data") or {}
occupancy_data = occupancy.get("data") or {}
occupancy_summary = occupancy_data.get("summary") or {}
status_cols[0].metric("Energy", f"{energy_data['total_kwh']:,.0f} kWh" if energy.get("success") and energy_data.get("total_kwh") is not None else "Unavailable")
status_cols[1].metric("Spend", f"${sum(float(item.get('total_amount', 0)) for item in cost_data.get('categories', [])):,.2f}" if cost.get("success") and cost_data.get("categories") else "Unavailable")
status_cols[2].metric("Utilization", f"{occupancy_summary['utilization_percent']:.1f}%" if occupancy.get("success") and occupancy_summary.get("utilization_percent") is not None else "Unavailable")
status_cols[3].metric("Health score", "Not reported", help="The current executive response does not expose a component-safe health score.")

st.subheader("Domain status and freshness")
domain_cols = st.columns(3)
for column, name, response in zip(domain_cols, ("Energy", "Cost", "Occupancy & security"), (energy, cost, occupancy)):
    with column:
        state = "Unavailable" if not response.get("success") else "Degraded" if response.get("degraded") else "Available"
        st.markdown(f"**{name}: {state}**")
        st.caption(state_message(response) or f"As of {metadata(response)['freshness'].get('as_of', 'not reported')}")
        for flag in metadata(response)["quality_flags"]:
            st.caption(flag.replace("_", " ").title())

st.divider()
st.subheader("Alerts and recommendations")
report_key = f"executive_report_{selected_facility}"
if st.button("Generate cross-domain report", type="primary", width="content"):
    with st.spinner("Compiling the latest verified domain findings..."):
        st.session_state[report_key] = safe_get(f"/executive/analyze/{selected_facility}")
report = st.session_state.get(report_key)
if not report:
    render_empty_state("Executive report", "No cross-domain report has been generated in this session.")
elif not report.get("success"):
    st.error(report.get("message", "Executive analysis is unavailable."))
else:
    report_data = report.get("data") or {}
    st.markdown(f"**Platform status:** {report_data.get('executive_status', 'Not reported')}")
    alerts = report_data.get("consolidated_alerts") or []
    recommendations = report_data.get("consolidated_recommendations") or []
    alert_col, recommendation_col = st.columns(2)
    with alert_col:
        st.markdown(f"**Active alerts: {len(alerts)}**")
        if alerts:
            for alert in alerts[:8]:
                st.warning(f"{alert.get('severity', 'Not reported')}: {alert.get('message', 'Alert details unavailable.')}")
        else:
            st.success("No active alerts were returned.")
    with recommendation_col:
        st.markdown(f"**Recommendation queue: {len(recommendations)}**")
        if recommendations:
            for recommendation in recommendations[:8]:
                st.info(f"{recommendation.get('priority', 'Not reported')}: {recommendation.get('action', 'Action details unavailable.')}")
        else:
            st.success("No recommendations were returned.")
    agent_status = report_data.get("agent_status") or {}
    if agent_status:
        st.subheader("Agent status")
        st.dataframe(
            [{"Agent": name, "Status": value.get("status", "Not reported"), "Latency (ms)": value.get("latency_ms", "Not reported")} for name, value in agent_status.items() if isinstance(value, dict)],
            width="stretch", hide_index=True,
        )
