import sys
from pathlib import Path
root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path: sys.path.insert(0, root_dir)
import pandas as pd
import streamlit as st
from frontend.services.api_client import safe_get, safe_post
from frontend.services.page_data import get_facilities

st.set_page_config(page_title="Maintenance | FacilityOPS", page_icon="🛠️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#f7f9fc}[data-testid="stSidebar"]{background:#fff}.block-container{padding-top:1.5rem;padding-bottom:3rem}
.hero{padding:1.4rem 1.6rem;border:1px solid #e5eaf1;border-radius:18px;background:linear-gradient(135deg,#fff,#f3f7fb);margin-bottom:1.1rem}.eyebrow{font-size:.78rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;opacity:.62}.hero h1{margin:.15rem 0 .25rem;font-size:2.15rem}.hero p{margin:0;opacity:.68}.card{border:1px solid #e5eaf1;border-radius:16px;background:#fff;padding:1rem 1.1rem;min-height:105px;box-shadow:0 2px 10px rgba(20,35,55,.035)}.card-label{font-size:.78rem;opacity:.62;font-weight:600}.card-value{font-size:1.65rem;font-weight:750;margin-top:.3rem}.card-note{font-size:.78rem;opacity:.58;margin-top:.2rem}.section-title{font-size:1.15rem;font-weight:750;margin:1.3rem 0 .65rem}.insight{border-left:4px solid #4f6f8f;padding:.8rem 1rem;background:#fff;border-radius:0 12px 12px 0;border:1px solid #e5eaf1}
</style>""", unsafe_allow_html=True)
def card(label,value,note=""):
    st.markdown(f'<div class="card"><div class="card-label">{label}</div><div class="card-value">{value}</div><div class="card-note">{note}</div></div>',unsafe_allow_html=True)
with st.sidebar:
    st.markdown("## FacilityOPS"); st.caption("Predictive Maintenance")
    facilities,_=get_facilities()
    if not facilities: st.error("No facilities available."); st.stop()
    selected_facility=st.selectbox("Facility",facilities,key="maintenance_facility")
    st.divider()
    if st.button("Refresh asset intelligence",use_container_width=True): st.rerun()
st.markdown('<div class="hero"><div class="eyebrow">Asset Intelligence</div><h1>Predictive Maintenance</h1><p>Monitor equipment health, investigate risk and turn predictions into maintenance actions.</p></div>',unsafe_allow_html=True)
st.caption(f"Active facility: {selected_facility}")
assets_response=safe_get(f"/maintenance/assets-analyzed/{selected_facility}"); assets=assets_response.get("data",{}).get("assets",[]) if assets_response else []
if not assets: st.info("No asset records are currently available for this facility."); st.stop()
df=pd.DataFrame(assets)
for col in ["health_score","failure_probability","process_temp","air_temp","speed","torque","wear"]:
    if col in df: df[col]=pd.to_numeric(df[col],errors="coerce")
avg_health=float(df.health_score.dropna().mean()) if "health_score" in df and df.health_score.notna().any() else None
high_risk=int((df.failure_probability>=.5).sum()) if "failure_probability" in df else 0
needs_attention=int((df.health_score<70).sum()) if "health_score" in df else 0
cols=st.columns(4)
with cols[0]: card("Assets monitored",len(df),"Active asset intelligence")
with cols[1]: card("Fleet health",f"{avg_health:.1f}%" if avg_health is not None else "Awaiting model","Model-derived health")
with cols[2]: card("High-risk assets",high_risk,"Prioritize for review")
with cols[3]: card("Needs attention",needs_attention,"Health below 70%")
st.markdown('<div class="section-title">Fleet health overview</div>',unsafe_allow_html=True)
left,right=st.columns([1.35,1])
with left:
    if "health_score" in df and df.health_score.notna().any(): st.bar_chart(df.health_score.dropna().clip(0,100).reset_index(drop=True),height=230)
    else: st.info("Health predictions are not available for the current asset set.")
with right:
    if "failure_probability" in df and df.failure_probability.notna().any(): st.line_chart((df.failure_probability.dropna().clip(0,1)*100).reset_index(drop=True),height=230)
    else: st.info("Risk predictions are not available for the current asset set.")
st.markdown('<div class="section-title">Maintenance test case</div>',unsafe_allow_html=True); st.caption("Run the deployed maintenance ML models against a telemetry scenario.")
with st.expander("Open predictive test case",expanded=True):
    asset_type=st.selectbox("Asset class",["L","M","H"],index=1,format_func=lambda x:{"L":"Low load (L)","M":"Medium load (M)","H":"High load (H)"}[x])
    c1,c2,c3=st.columns(3)
    with c1: air_temp=st.number_input("Air temperature (K)",value=298.1,step=.1,format="%.1f"); process_temp=st.number_input("Process temperature (K)",value=308.6,step=.1,format="%.1f")
    with c2: speed=st.number_input("Rotational speed (rpm)",value=1500.0,step=10.0); torque=st.number_input("Torque (Nm)",value=40.0,step=1.0)
    with c3: wear=st.number_input("Tool/component wear (min)",value=100.0,step=1.0); st.caption("Increase temperature, torque or wear to explore model response.")
    if st.button("Run predictive analysis",type="primary",use_container_width=True):
        payload={"type":asset_type,"air_temp":air_temp,"process_temp":process_temp,"speed":speed,"torque":torque,"wear":wear}
        with st.spinner("Running maintenance models..."): result=safe_post("/maintenance/predict-manual",payload=payload)
        if result.get("success"): st.session_state["maintenance_scenario"]=result.get("data") or {}
        else: st.error("Predictive analysis could not be completed. Please try again.")
scenario=st.session_state.get("maintenance_scenario")
if scenario:
    metrics=scenario.get("metrics",scenario); health=float(metrics.get("asset_health_score",0) or 0); probability=float(metrics.get("failure_probability",0) or 0); issue=str(metrics.get("predicted_issue","Condition assessed"))
    st.markdown('<div class="section-title">Model assessment</div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    with c1: card("Predicted health",f"{health:.1f}%","Maintenance ML")
    with c2: card("Failure probability",f"{probability:.1%}","Model-estimated risk")
    with c3: card("Predicted condition",issue,"Fault classification")
    msg=(scenario.get("anomalies") or [{}])[0].get("message") or f"The selected telemetry scenario is assessed as {issue} with an estimated health of {health:.1f}% and failure probability of {probability:.1%}."
    st.markdown(f'<div class="insight"><b>Model insight</b><br>{msg}</div>',unsafe_allow_html=True)
st.markdown('<div class="section-title">Asset risk overview</div>',unsafe_allow_html=True)
show_cols=[c for c in ["asset_id","asset_type","status","health_score","failure_probability","predicted_issue","process_temp"] if c in df.columns]; view=df[show_cols].copy()
if "failure_probability" in view: view=view.sort_values("failure_probability",ascending=False,na_position="last")
st.dataframe(view,hide_index=True,use_container_width=True,height=320)
st.markdown('<div class="section-title">Recommended actions</div>',unsafe_allow_html=True)
if high_risk: st.markdown(f"- Prioritize inspection of **{high_risk}** high-risk asset(s).")
elif needs_attention: st.markdown(f"- Review **{needs_attention}** asset(s) below the attention threshold.")
else: st.markdown("- Continue routine monitoring and scheduled preventive maintenance.")
st.caption("FacilityOPS • Predictive asset intelligence")
