import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.components.status import render_empty_state, render_status_banner
from frontend.services.api_client import safe_get, safe_patch, safe_post
from frontend.services.page_data import get_facilities, metadata, state_message

st.set_page_config(page_title="Cost | FacilityOPS", page_icon="💰", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp{background:#f4f7fb}.hero{background:linear-gradient(135deg,#111827,#312e81 60%,#0f766e);color:#fff;border-radius:20px;padding:25px 28px;margin-bottom:18px}.eyebrow{font-size:10px;font-weight:800;letter-spacing:.16em;color:#c4b5fd;text-transform:uppercase}.hero h1{font-size:30px;margin:4px 0}.hero p{color:#e0e7ff;margin:0;font-size:13px}.panel{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:17px;margin-bottom:15px;box-shadow:0 4px 14px rgba(15,23,42,.04)}
</style>
<div class="hero"><div class="eyebrow">FacilityOPS / Cost Intelligence</div><h1>Financial Intelligence Center</h1><p>Understand facility spend, cost drivers and actionable optimization opportunities.</p></div>
""", unsafe_allow_html=True)

facilities, _ = get_facilities()
if not facilities:
    render_status_banner(False, "No facilities are available from the facility catalog.")
    st.stop()
selected_facility = st.selectbox("Facility", facilities, key="cost_facility")
with st.sidebar:
    st.markdown("### Financial Operations")
    if st.button("Refresh financial data", icon="🔄", width="stretch"):
        result = safe_post("/cost/seed", params={"facility_id": selected_facility, "months": 6})
        if result.get("success"):
            st.success("Latest financial data loaded.")
            st.rerun()
        else:
            st.error(result.get("message", "Financial refresh could not be completed."))

dashboard = safe_get(f"/cost/dashboard/{selected_facility}", fallback_data={})
if message := state_message(dashboard):
    render_status_banner(dashboard.get("success", False), message)
if not dashboard.get("success"):
    st.stop()
data = dashboard.get("data") or {}
categories = data.get("categories") or []
if not categories:
    render_empty_state("Financial tracking", "No financial data is available for this facility yet.")
    st.stop()

frame = pd.DataFrame(categories)
total = float(frame["total_amount"].sum())
record_count = int(frame["record_count"].sum())
largest_row = frame.loc[frame["total_amount"].idxmax()]
freshness = metadata(dashboard)["freshness"]
st.caption(f"Facility: {selected_facility} · Latest verified financial reporting: {freshness.get('as_of') or 'current reporting period'}")

cols = st.columns(4)
cols[0].metric("Total spend", f"${total:,.0f}")
cols[1].metric("Transactions", f"{record_count:,}")
cols[2].metric("Largest cost driver", str(largest_row["category"]))
cols[3].metric("Top category spend", f"${float(largest_row['total_amount']):,.0f}")

left,right = st.columns([1.55,1])
with left:
    st.markdown("### Spend by Category")
    chart = px.bar(frame.sort_values("total_amount", ascending=False), x="category", y="total_amount", labels={"total_amount":"Amount","category":""})
    chart.update_layout(showlegend=False, yaxis_tickprefix="$", height=360, margin=dict(l=10,r=10,t=15,b=10))
    st.plotly_chart(chart, width="stretch", config={"displayModeBar":False})
with right:
    st.markdown("### Cost Profile")
    for _, row in frame.sort_values("total_amount", ascending=False).head(4).iterrows():
        st.metric(str(row["category"]), f"${float(row['total_amount']):,.0f}")

st.markdown("### AI Financial Assessment")
if st.button("Run Cost Analysis", type="primary", icon="✨"):
    with st.spinner("Analyzing facility spend and opportunities..."):
        st.session_state[f"cost_analysis_{selected_facility}"] = safe_get(f"/cost/analyze/{selected_facility}")
analysis_response = st.session_state.get(f"cost_analysis_{selected_facility}")
if not analysis_response:
    st.info("Run an analysis to generate financial recommendations.")
elif not analysis_response.get("success"):
    st.error(analysis_response.get("message", "Cost analysis could not be completed."))
else:
    analysis_data = analysis_response.get("data") or {}
    analysis = analysis_data.get("analysis") or {}
    metrics = analysis.get("metrics") or {}
    savings = metrics.get("predicted_savings_usd")
    if savings is not None:
        st.metric("Estimated optimization opportunity", f"${float(savings):,.0f}")
    recommendations = analysis_data.get("recommendations") or []
    if not recommendations:
        st.success("Current analysis did not identify a priority cost action.")
    for recommendation in recommendations:
        recommendation_id = recommendation.get("recommendation_id")
        with st.container(border=True):
            st.markdown(f"**{recommendation.get('action', 'Recommended action')}**")
            st.caption(f"Priority: {recommendation.get('priority', 'Recommended')} · Trigger: {recommendation.get('trigger', 'Cost opportunity')}")
            if recommendation_id:
                status = st.selectbox("Status", ["proposed", "accepted", "completed", "dismissed"], key=f"rec_status_{recommendation_id}")
                if st.button("Save status", key=f"save_rec_{recommendation_id}"):
                    result = safe_patch(f"/cost/recommendations/{recommendation_id}", {"status": status}, params={"facility_id": selected_facility})
                    if result.get("success"):
                        st.success("Recommendation status saved.")
                    else:
                        st.error(result.get("message", "Recommendation update failed."))
