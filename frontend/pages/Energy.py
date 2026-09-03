import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.components.status import render_empty_state, render_status_banner
from frontend.services.api_client import safe_get, safe_post
from frontend.services.page_data import get_facilities, metadata, state_message

st.set_page_config(page_title="Energy | FacilityOPS", layout="wide")
st.title("Energy Operations")
st.caption("Review verified consumption, demand, and energy intelligence for the selected facility.")

facilities, _ = get_facilities()
if not facilities:
    render_status_banner(False, "No facilities are available from the canonical catalog.")
    st.stop()
selected_facility = st.selectbox("Facility", facilities, key="energy_facility")

with st.sidebar:
    st.subheader("Data operations")
    if st.button("Ingest energy telemetry", icon="🔄", width="stretch"):
        result = safe_post("/energy/seed", params={"facility_id": selected_facility, "days": 7})
        if result.get("success"):
            st.success("Energy telemetry ingested.")
            st.rerun()
        else:
            st.error(result.get("message", "Energy ingestion failed."))

dashboard = safe_get(f"/energy/dashboard/{selected_facility}", fallback_data={})
if message := state_message(dashboard):
    render_status_banner(dashboard.get("success", False), message)
if not dashboard.get("success"):
    st.stop()

data = dashboard.get("data") or {}
dashboard_meta = metadata(dashboard)
st.markdown(f"### {selected_facility}")
st.caption(
    f"Data as of: {dashboard_meta['freshness'].get('as_of', 'not reported')} | "
    f"Source: {dashboard_meta['provenance'].get('source', 'not reported')}"
)
if not data.get("records_evaluated"):
    render_empty_state("Energy telemetry", "No verified energy telemetry has been received for this facility.")
    st.stop()

cols = st.columns(3)
cols[0].metric("Energy in reported period", f"{float(data['total_kwh']):,.0f} kWh")
cols[1].metric("Peak demand", f"{float(data['peak_kw']):,.1f} kW" if data.get("peak_kw") is not None else "Not reported")
cols[2].metric("Telemetry records", f"{int(data['records_evaluated']):,}")

st.subheader("Demand snapshot")
if data.get("peak_kw") is not None:
    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(data["peak_kw"]),
            title={"text": "Peak demand (kW)"},
            gauge={"axis": {"visible": True}},
        )
    )
    figure.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
else:
    st.info("Peak demand is not available in the verified telemetry.")

st.subheader("Energy intelligence")
if st.button("Run energy analysis", type="primary", width="content"):
    with st.spinner("Reviewing recent energy telemetry..."):
        st.session_state[f"energy_analysis_{selected_facility}"] = safe_get(
            f"/energy/analyze/{selected_facility}?days=7"
        )

analysis_response = st.session_state.get(f"energy_analysis_{selected_facility}")
if not analysis_response:
    st.info("Run an analysis to review current alerts and recommendations.")
elif not analysis_response.get("success"):
    st.error(analysis_response.get("message", "Energy analysis is unavailable."))
else:
    analysis_data = analysis_response.get("data") or {}
    analysis_meta = metadata(analysis_response)
    if analysis_response.get("degraded") or analysis_data.get("degraded"):
        st.warning("Energy analysis is degraded. Review its quality flags before acting.")

    summary_cols = st.columns(3)
    summary_cols[0].metric("Records evaluated", f"{int(analysis_meta['provenance'].get('records_evaluated', 0)):,}")
    summary_cols[1].metric("Intelligence source", analysis_data.get("intelligence_source", "Not reported"))
    summary_cols[2].metric("Data quality", "Degraded" if analysis_meta["degraded"] else "Good")

    if analysis_meta["quality_flags"]:
        st.caption("Quality flags: " + ", ".join(analysis_meta["quality_flags"]).replace("_", " "))

    alerts = analysis_data.get("alerts") or []
    recommendations = analysis_data.get("recommendations") or []
    if alerts:
        st.markdown("**Detected issues**")
        for alert in alerts:
            st.warning(f"{alert.get('severity', 'Not reported')}: {alert.get('message', 'Alert details unavailable.')}")
    else:
        st.success("No energy alerts were returned.")

    if recommendations:
        st.markdown("**Recommended actions**")
        for recommendation in recommendations:
            st.info(f"{recommendation.get('priority', 'Not reported')}: {recommendation.get('action', 'Action details unavailable.')}")
    else:
        st.info("No verified energy recommendations were returned.")
