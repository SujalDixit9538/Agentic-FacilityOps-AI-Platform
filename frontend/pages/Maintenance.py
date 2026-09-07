import sys
from pathlib import Path

root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pandas as pd
import streamlit as st

from frontend.services.api_client import safe_get, safe_post
from frontend.services.page_data import get_facilities

st.set_page_config(page_title="Maintenance | FacilityOPS", page_icon="🛠️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f7f9fc; }
[data-testid="stSidebar"] { background: #ffffff; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
.hero { padding: 1.4rem 1.6rem; border: 1px solid #e5eaf1; border-radius: 18px; background: linear-gradient(135deg,#ffffff,#f3f7fb); margin-bottom: 1.1rem; }
.eyebrow { font-size:.78rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; opacity:.62; }
.hero h1 { margin:.15rem 0 .25rem; font-size:2.15rem; }
.hero p { margin:0; opacity:.68; font-size:1rem; }
.card { border:1px solid #e5eaf1; border-radius:16px; background:#fff; padding:1rem 1.1rem; min-height:105px; box-shadow:0 2px 10px rgba(20,35,55,.035); }
.card-label { font-size:.78rem; opacity:.62; font-weight:600; }
.card-value { font-size:1.65rem; font-weight:750; margin-top:.3rem; }
.card-note { font-size:.78rem; opacity:.58; margin-top:.2rem; }
.section-title { font-size:1.15rem; font-weight:750; margin:1.3rem 0 .65rem; }
.insight { border-left:4px solid #4f6f8f; padding:.8rem 1rem; background:#fff; border-radius:0 12px 12px 0; border-top:1px solid #e5eaf1; border-right:1px solid #e5eaf1; border-bottom:1px solid #e5eaf1; }
</style>
""", unsafe_allow_html=True)


def card(label, value, note=""):
    st.markdown(f'<div class="card"><div class="card-label">{label}</div><div class="card-value">{value}</div><div class="card-note">{note}</div></div>', unsafe_allow_html=True)


with st.sidebar:
    st.markdown("## FacilityOPS")
    st.caption("Predictive Maintenance")
    facilities, _ = get_facilities()
    if not facilities:
        st.error("No facilities available.")
        st.stop()
    selected_facility = st.selectbox("Facility", facilities, key="maintenance_facility")
    st.divider()
    st.caption("Operations")
    if st.button("Refresh asset intelligence", use_container_width=True):
        st.rerun()

st.markdown('''<div class="hero"><div class="eyebrow">Asset Intelligence</div><h1>Predictive Maintenance</h1><p>Monitor equipment health, investigate risk and turn predictions into maintenance actions.</p></div>''', unsafe_allow_html=True)
st.caption(f"Active facility: {selected_facility}")

assets_response = safe_get(f"/maintenance/assets-analyzed/{selected_facility}")
assets = assets_response.get("data", {}).get("assets", []) if assets_response else []

if not assets:
    st.info("No asset records are currently available for this facility. Use the maintenance data workflow to register assets.")
    st.stop()

df = pd.DataFrame(assets)
for col in ["health_score", "failure_probability", "process_temp", "air_temp", "speed", "torque", "wear"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

avg_health = float(df["health_score"].mean()) if "health_score" in df else 0.0
high_risk = int((df["failure_probability"] >= .5).sum()) if "failure_probability" in df else 0
needs_attention = int((df["health_score"] < 70).sum()) if "health_score" in df else 0
monitored = len(df)

cols = st.columns(4)
with cols[0]: card("Assets monitored", f"{monitored}", "Active asset intelligence")
with cols[1]: card("Fleet health", f"{avg_health:.1f}%", "Average predicted health")
with cols[2]: card("High-risk assets", f"{high_risk}", "Prioritize for review")
with cols[3]: card("Needs attention", f"{needs_attention}", "Health below 70%")

st.markdown('<div class="section-title">Fleet health overview</div>', unsafe_allow_html=True)
left, right = st.columns([1.35, 1])
with left:
    if "health_score" in df:
        hist = df["health_score"].dropna().clip(0, 100)
        st.bar_chart(hist.reset_index(drop=True), height=240)
with right:
    buckets = pd.cut(df["health_score"], bins=[-1,50,70,90,100], labels=["Critical","Attention","Good","Excellent"]) if "health_score" in df else pd.Series(dtype=str)
    distribution = buckets.value_counts().reindex(["Excellent","Good","Attention","Critical"], fill_value=0)
    st.dataframe(pd.DataFrame({"Health band": distribution.index, "Assets": distribution.values}), hide_index=True, use_container_width=True, height=240)

st.markdown('<div class="section-title">Maintenance test case</div>', unsafe_allow_html=True)
st.caption("Run the real maintenance prediction service against a telemetry scenario.")

with st.expander("Open predictive test case", expanded=False):
    asset_type = st.selectbox("Asset type", ["Pump", "Motor", "Compressor", "HVAC", "Fan"], key="maint_asset_type")
    c1, c2, c3 = st.columns(3)
    with c1:
        air_temp = st.number_input("Air temperature", value=298.1, step=.1, format="%.1f")
        process_temp = st.number_input("Process temperature", value=308.6, step=.1, format="%.1f")
    with c2:
        speed = st.number_input("Rotational speed", value=1500.0, step=10.0)
        torque = st.number_input("Torque", value=40.0, step=1.0)
    with c3:
        wear = st.number_input("Tool / component wear", value=100.0, step=1.0)
        st.caption("Adjust one variable to explore a different operating condition.")

    if st.button("Run maintenance analysis", type="primary", use_container_width=True):
        payload = {"asset_type": asset_type, "air_temperature": air_temp, "process_temperature": process_temp, "rotational_speed": speed, "torque": torque, "tool_wear": wear}
        with st.spinner("Analyzing asset condition..."):
            result = safe_post("/maintenance/predict-manual", payload=payload)
        if result.get("success"):
            data = result.get("data") or {}
            metrics = data.get("metrics", data)
            st.session_state["maintenance_scenario"] = metrics
        else:
            st.error("Maintenance analysis could not be completed. Check the API service and try again.")

scenario = st.session_state.get("maintenance_scenario")
if scenario:
    st.markdown('<div class="section-title">Scenario result</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    health = float(scenario.get("asset_health_score", scenario.get("health_score", 0)) or 0)
    probability = float(scenario.get("failure_probability", 0) or 0)
    issue = scenario.get("predicted_issue", scenario.get("issue", "Condition assessed"))
    with c1: card("Predicted health", f"{health:.1f}%", "Model assessment")
    with c2: card("Failure probability", f"{probability:.1%}", "Model-estimated risk")
    with c3: card("Condition", str(issue), "Predicted operating state")
    st.markdown(f'<div class="insight"><b>Maintenance insight</b><br>For the selected telemetry scenario, the maintenance model estimates <b>{health:.1f}%</b> asset health with a <b>{probability:.1%}</b> failure probability. Use this result to prioritize inspection and intervention.</div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">Asset risk overview</div>', unsafe_allow_html=True)
show_cols = [c for c in ["asset_id", "asset_type", "status", "health_score", "failure_probability", "predicted_issue", "process_temp"] if c in df.columns]
st.dataframe(df[show_cols].sort_values("failure_probability", ascending=False) if "failure_probability" in df else df[show_cols], hide_index=True, use_container_width=True, height=320)

st.markdown('<div class="section-title">Recommended actions</div>', unsafe_allow_html=True)
recommendations = []
if high_risk:
    recommendations.append(f"Prioritize inspection of {high_risk} high-risk asset(s).")
if needs_attention:
    recommendations.append(f"Review {needs_attention} asset(s) with health below the attention threshold.")
if not recommendations:
    recommendations.append("Fleet condition is stable; continue routine monitoring and scheduled maintenance.")
for item in recommendations:
    st.markdown(f"- {item}")

st.caption("FacilityOPS • Predictive asset intelligence")
