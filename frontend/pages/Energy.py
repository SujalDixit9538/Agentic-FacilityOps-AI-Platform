import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.components.status import render_empty_state, render_status_banner
from frontend.services.api_client import safe_get, safe_post
from frontend.services.page_data import get_facility_options, metadata, state_message

st.set_page_config(page_title="Energy | FacilityOPS", layout="wide")
st.title("Energy Operations")
st.caption("Review verified consumption, demand, forecasting, and operational recommendations.")

facility_options, _ = get_facility_options()
if not facility_options:
    render_status_banner(False, "No facilities are available from the canonical catalog.")
    st.stop()

facility_ids = [item["facility_id"] for item in facility_options]
selected_facility = st.selectbox("Facility", facility_ids, key="energy_facility")
selected = next(item for item in facility_options if item["facility_id"] == selected_facility)

context = st.columns(4)
context[0].metric("Facility", selected_facility)
context[1].metric("Type", selected.get("facility_type") or "Not reported")
context[2].metric("Area", f"{float(selected['total_area_sqft']):,.0f} ft²" if selected.get("total_area_sqft") else "Not reported")
context[3].metric("Floors", str(selected.get("total_floors") or "Not reported"))

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
    st.info("Run an analysis to review current alerts, forecast, and recommendations.")
elif not analysis_response.get("success"):
    st.error(analysis_response.get("message", "Energy analysis is unavailable."))
else:
    analysis_data = analysis_response.get("data") or {}
    analysis_meta = metadata(analysis_response)
    if analysis_response.get("degraded") or analysis_data.get("degraded"):
        st.warning("Energy analysis is degraded. Review its quality flags before acting.")

    metrics = analysis_data.get("analysis", {}).get("metrics", {})
    summary_cols = st.columns(3)
    summary_cols[0].metric("Records evaluated", f"{int(analysis_meta['provenance'].get('records_evaluated', 0)):,}")
    summary_cols[1].metric("Intelligence source", analysis_data.get("analysis", {}).get("intelligence_source", "Not reported"))
    summary_cols[2].metric("Average usage", f"{float(metrics['avg_kwh']):,.1f} kWh" if metrics.get("avg_kwh") is not None else "Not reported")

    if analysis_meta["quality_flags"]:
        st.caption("Quality flags: " + ", ".join(analysis_meta["quality_flags"]).replace("_", " "))

    alerts = analysis_data.get("alerts") or []
    recommendations = analysis_data.get("recommendations") or []
    forecast = analysis_data.get("forecast") or analysis_data.get("analysis", {}).get("forecast") or {}

    left, right = st.columns(2)
    with left:
        st.markdown("**Detected issues**")
        if alerts:
            for alert in alerts:
                st.warning(f"{alert.get('severity', 'Not reported')}: {alert.get('message', 'Alert details unavailable.')}")
        else:
            st.success("No energy alerts were returned.")
    with right:
        st.markdown("**Recommended actions**")
        if recommendations:
            for recommendation in recommendations:
                st.info(
                    f"{recommendation.get('priority', 'Not reported')}: "
                    f"{recommendation.get('action', 'Action details unavailable.') }"
                )
                if recommendation.get("reason"):
                    st.caption(recommendation["reason"])
        else:
            st.info("No verified energy recommendations were returned.")

    st.markdown("**24-hour baseline forecast**")
    points = forecast.get("points") or []
    if forecast.get("status") == "success" and points:
        forecast_fig = go.Figure(
            go.Scatter(
                x=[point["timestamp"] for point in points],
                y=[point["predicted_kwh"] for point in points],
                mode="lines+markers",
                name="Baseline forecast",
            )
        )
        forecast_fig.update_layout(
            height=320,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Time",
            yaxis_title="Predicted kWh",
        )
        st.plotly_chart(forecast_fig, width="stretch", config={"displayModeBar": False})
        st.caption("Forecast method: historical hourly baseline. This is a statistical baseline, not a trained ML forecast.")
    else:
        st.info("Not enough verified hourly history to produce a 24-hour baseline forecast.")
