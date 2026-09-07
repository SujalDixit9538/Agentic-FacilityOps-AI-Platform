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

st.set_page_config(page_title="Energy | FacilityOPS", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp{background:#f4f7fb}.hero{background:linear-gradient(135deg,#082f49,#0369a1 60%,#0f766e);color:#fff;border-radius:20px;padding:25px 28px;margin-bottom:18px}.eyebrow{font-size:10px;font-weight:800;letter-spacing:.16em;color:#bae6fd;text-transform:uppercase}.hero h1{font-size:30px;margin:4px 0}.hero p{color:#dbeafe;margin:0;font-size:13px}.panel{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:17px;margin-bottom:15px;box-shadow:0 4px 14px rgba(15,23,42,.04)}
</style>
<div class="hero"><div class="eyebrow">FacilityOPS / Energy Intelligence</div><h1>Energy Intelligence Center</h1><p>Monitor consumption, demand and optimization opportunities for the selected facility.</p></div>
""", unsafe_allow_html=True)

facilities, _ = get_facilities()
if not facilities:
    render_status_banner(False, "No facilities are available from the facility catalog.")
    st.stop()

selected_facility = st.selectbox("Facility", facilities, key="energy_facility")
with st.sidebar:
    st.markdown("### Energy Operations")
    if st.button("Refresh telemetry", icon="🔄", width="stretch"):
        result = safe_post("/energy/seed", params={"facility_id": selected_facility, "days": 7})
        if result.get("success"):
            st.success("Latest telemetry loaded.")
            st.rerun()
        else:
            st.error(result.get("message", "Telemetry refresh could not be completed."))

dashboard = safe_get(f"/energy/dashboard/{selected_facility}", fallback_data={})
if message := state_message(dashboard):
    render_status_banner(dashboard.get("success", False), message)
if not dashboard.get("success"):
    st.stop()

data = dashboard.get("data") or {}
if not data.get("records_evaluated"):
    render_empty_state("Energy telemetry", "No energy telemetry is available for this facility yet.")
    st.stop()

freshness = metadata(dashboard)["freshness"]
st.caption(f"Facility: {selected_facility} · Latest verified telemetry: {freshness.get('as_of') or 'current reporting period'}")

cols = st.columns(4)
cols[0].metric("Energy consumption", f"{float(data['total_kwh']):,.0f} kWh")
cols[1].metric("Peak demand", f"{float(data['peak_kw']):,.1f} kW" if data.get("peak_kw") is not None else "—")
cols[2].metric("Telemetry records", f"{int(data['records_evaluated']):,}")
cols[3].metric("Facility status", "Monitored")

left, right = st.columns([1.55, 1])
with left:
    st.markdown("### Demand Profile")
    if data.get("peak_kw") is not None:
        figure = go.Figure(go.Indicator(mode="gauge+number", value=float(data["peak_kw"]), title={"text":"Peak demand (kW)"}, gauge={"axis":{"visible":True}}))
        figure.update_layout(height=300, margin=dict(l=20,r=20,t=55,b=10))
        st.plotly_chart(figure, width="stretch", config={"displayModeBar":False})
    else:
        st.info("Peak demand will appear when demand telemetry is available.")
with right:
    st.markdown("### Energy Snapshot")
    st.metric("Average per record", f"{float(data['total_kwh'])/max(int(data['records_evaluated']),1):,.2f} kWh")
    st.info("Use the analysis action below to turn the latest telemetry into operational findings and recommendations.")

st.markdown("### AI Energy Assessment")
if st.button("Run Energy Analysis", type="primary", icon="✨"):
    with st.spinner("Analyzing recent energy performance..."):
        st.session_state[f"energy_analysis_{selected_facility}"] = safe_get(f"/energy/analyze/{selected_facility}?days=7")
analysis_response = st.session_state.get(f"energy_analysis_{selected_facility}")
if not analysis_response:
    st.info("Run an analysis to generate alerts and recommended actions.")
elif not analysis_response.get("success"):
    st.error(analysis_response.get("message", "Energy analysis could not be completed."))
else:
    analysis_data = analysis_response.get("data") or {}
    alerts = analysis_data.get("alerts") or []
    recommendations = analysis_data.get("recommendations") or []
    a,b = st.columns(2)
    with a:
        st.markdown("**Key findings**")
        if alerts:
            for alert in alerts:
                st.warning(f"{str(alert.get('severity','Attention')).upper()} · {alert.get('message','Energy condition identified.')}")
        else:
            st.success("No priority energy alerts were identified.")
    with b:
        st.markdown("**Recommended actions**")
        if recommendations:
            for recommendation in recommendations:
                st.info(f"{str(recommendation.get('priority','Recommended')).upper()} · {recommendation.get('action','Review the identified energy opportunity.')}")
        else:
            st.info("No priority actions were identified from the current telemetry.")
