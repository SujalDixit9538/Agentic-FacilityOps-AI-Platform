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

st.set_page_config(page_title="Cost | FacilityOPS", layout="wide")
st.title("Cost Operations")
st.caption("Understand spend, budget pressure, and the next financial decisions for one facility.")

facilities, _ = get_facilities()
if not facilities:
    render_status_banner(False, "No facilities are available from the canonical catalog.")
    st.stop()

selected_facility = st.selectbox("Facility", facilities, key="cost_facility")
with st.sidebar:
    st.subheader("Data operations")
    if st.button("Ingest financial data", icon="🔄", width="stretch"):
        result = safe_post("/cost/seed", params={"facility_id": selected_facility, "months": 6})
        if result.get("success"):
            st.success("Financial data ingested.")
            st.rerun()
        else:
            st.error(result.get("message", "Financial ingestion failed."))

dashboard = safe_get(f"/cost/dashboard/{selected_facility}", fallback_data={})
if message := state_message(dashboard):
    render_status_banner(dashboard.get("success", False), message)
if not dashboard.get("success"):
    st.stop()

data = dashboard.get("data") or {}
categories = data.get("categories") or []
st.markdown(f"### {selected_facility}")
freshness = metadata(dashboard)["freshness"]
st.caption(
    f"Operational status: {'Degraded' if dashboard.get('degraded') else 'Available'} | "
    f"Data as of: {freshness.get('as_of') or 'not reported'} | "
    f"Source: {metadata(dashboard)['provenance'].get('source', 'not reported')}"
)

if not categories:
    render_empty_state("Financial tracking", "No verified cost data has been received for this facility.")
    st.info("Use the data operation in the sidebar when a demo ledger is required.")
    st.stop()

frame = pd.DataFrame(categories)
total = float(frame["total_amount"].sum())
record_count = int(frame["record_count"].sum())
largest = frame.loc[frame["total_amount"].idxmax(), "category"]
cols = st.columns(4)
cols[0].metric("Spend in reported period", f"${total:,.2f}")
cols[1].metric("Transactions", f"{record_count:,}")
cols[2].metric("Largest category", str(largest))
cols[3].metric("Budget variance", "Not reported", help="Budget data is not part of the current API contract.")

left, right = st.columns([3, 2])
with left:
    st.subheader("Spend by category")
    chart = px.bar(frame, x="category", y="total_amount", color="category", labels={"total_amount": "Amount"})
    chart.update_layout(showlegend=False, yaxis_tickprefix="$", margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})
with right:
    st.subheader("Data quality")
    if dashboard.get("degraded"):
        st.warning("This summary is degraded. Validate the quality flags before acting.")
    else:
        st.success("Summary is available from an aggregate query.")
    for flag in metadata(dashboard)["quality_flags"]:
        st.caption(flag.replace("_", " ").title())

st.divider()
st.subheader("Recommendations")
if st.button("Run cost analysis", type="primary", width="content"):
    with st.spinner("Preparing the latest cost recommendations..."):
        st.session_state[f"cost_analysis_{selected_facility}"] = safe_get(f"/cost/analyze/{selected_facility}")

analysis_response = st.session_state.get(f"cost_analysis_{selected_facility}")
if not analysis_response:
    st.info("Run an analysis when you are ready to review persisted recommendations.")
elif not analysis_response.get("success"):
    st.error(analysis_response.get("message", "Cost analysis is unavailable."))
else:
    analysis_data = analysis_response.get("data") or {}
    analysis = analysis_data.get("analysis") or {}
    metrics = analysis.get("metrics") or {}
    savings = metrics.get("predicted_savings_usd")
    if savings is not None:
        st.metric("Estimated savings", f"${float(savings):,.2f}")
    elif analysis_response.get("degraded"):
        st.warning("Savings cannot be responsibly estimated from the available data.")
    if reason := metrics.get("degradation_reason"):
        st.warning(f"Analysis degraded: {reason}")
    recommendations = analysis_data.get("recommendations") or []
    if not recommendations:
        st.info("No verified recommendations were returned.")
    for recommendation in recommendations:
        recommendation_id = recommendation.get("recommendation_id")
        with st.container(border=True):
            st.markdown(f"**{recommendation.get('action', 'Recommendation')}**")
            st.caption(f"Priority: {recommendation.get('priority', 'Not reported')} | Trigger: {recommendation.get('trigger', 'Not reported')}")
            if recommendation_id:
                status = st.selectbox("Status", ["proposed", "accepted", "completed", "dismissed"], key=f"rec_status_{recommendation_id}")
                if st.button("Save status", key=f"save_rec_{recommendation_id}", width="content"):
                    result = safe_patch(
                        f"/cost/recommendations/{recommendation_id}",
                        {"status": status},
                        params={"facility_id": selected_facility},
                    )
                    if result.get("success"):
                        st.success("Recommendation status saved.")
                    else:
                        st.error(result.get("message", "Recommendation update failed."))
            else:
                st.caption("This recommendation has no persisted identifier and cannot be updated.")
