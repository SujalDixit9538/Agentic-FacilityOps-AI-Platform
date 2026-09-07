import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Scenario Lab | FacilityOPS", page_icon="🧪", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp{background:#f4f7fb}.hero{background:linear-gradient(135deg,#0f172a,#312e81 55%,#0f766e);color:#fff;border-radius:20px;padding:25px 28px;margin-bottom:18px}.eyebrow{font-size:10px;font-weight:800;letter-spacing:.16em;color:#a5b4fc;text-transform:uppercase}.hero h1{font-size:30px;margin:4px 0}.hero p{color:#cbd5e1;margin:0;font-size:13px}.recommend{background:#fff;border:1px solid #e2e8f0;border-left:4px solid #2563eb;border-radius:12px;padding:14px;margin:8px 0;box-shadow:0 3px 10px rgba(15,23,42,.04)}
</style>
<div class="hero"><div class="eyebrow">FacilityOPS / Operational Simulation</div><h1>Scenario Lab</h1><p>Enter facility conditions and immediately see calculated results, operational risk, charts and recommended actions.</p></div>
""", unsafe_allow_html=True)

scenario = st.selectbox("Scenario type", ["Occupancy & Security", "Energy", "Maintenance", "Cost"])
st.markdown("### Scenario Inputs")

if scenario == "Occupancy & Security":
    a,b,c=st.columns(3)
    with a: capacity=st.number_input("Zone capacity",1,10000,100,1)
    with b: occupancy=st.number_input("Current occupancy",0,20000,120,1)
    with c: duration=st.number_input("Duration (minutes)",1,1440,45,5)
    d,e=st.columns(2)
    with d: floor=st.number_input("Floor",0,200,3,1)
    with e: security_events=st.number_input("Security events",0,1000,0,1)
    zone=st.text_input("Zone", "Conference Room A")
    utilization=(occupancy/capacity*100) if capacity else 0
    excess=max(0,occupancy-capacity)
    risk="HIGH" if utilization>100 or security_events>2 else ("MEDIUM" if utilization>=80 or security_events else "LOW")
    st.markdown("### Operational Result")
    x1,x2,x3,x4=st.columns(4)
    x1.metric("Occupancy",f"{occupancy:,}"); x2.metric("Capacity",f"{capacity:,}"); x3.metric("Utilization",f"{utilization:.0f}%"); x4.metric("Risk",risk)
    fig=go.Figure(go.Bar(x=["Capacity","Actual"],y=[capacity,occupancy],text=[capacity,occupancy],textposition="auto"))
    fig.update_layout(height=320,margin=dict(l=10,r=10,t=20,b=10),yaxis_title="People",showlegend=False)
    st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})
    if excess:
        st.error(f"Capacity exceeded by {excess} people. {zone} is operating at {utilization:.0f}% of configured capacity.")
    elif utilization>=80:
        st.warning(f"High utilization: {zone} is operating at {utilization:.0f}% capacity.")
    else:
        st.success(f"{zone} is operating within configured capacity.")
    if security_events: st.warning(f"{security_events} security event(s) included in this scenario.")
    st.markdown("### Recommended Actions")
    st.markdown(f'<div class="recommend"><b>Priority: {risk}</b><br>Review zone allocation and redirect incoming occupants when capacity is exceeded.</div>',unsafe_allow_html=True)
    st.markdown('<div class="recommend"><b>Capacity planning</b><br>Prepare alternate space when utilization approaches 100%.</div>',unsafe_allow_html=True)

elif scenario == "Energy":
    a,b,c=st.columns(3)
    with a: consumption=st.number_input("Current consumption (kWh)",0.0,10000000.0,48200.0,100.0)
    with b: baseline=st.number_input("Baseline consumption (kWh)",0.0,10000000.0,41000.0,100.0)
    with c: peak=st.number_input("Peak demand (kW)",0.0,100000.0,420.0,5.0)
    variance=((consumption-baseline)/baseline*100) if baseline else 0
    risk="HIGH" if variance>15 else ("MEDIUM" if variance>5 else "LOW")
    st.markdown("### Energy Result")
    x1,x2,x3=st.columns(3); x1.metric("Consumption",f"{consumption:,.0f} kWh"); x2.metric("Baseline variance",f"{variance:+.1f}%"); x3.metric("Peak demand",f"{peak:,.0f} kW")
    fig=go.Figure(go.Indicator(mode="gauge+number",value=variance,title={"text":"Variance vs baseline (%)"},gauge={"axis":{"range":[-30,50]}})); fig.update_layout(height=280,margin=dict(l=20,r=20,t=50,b=20)); st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})
    (st.error if risk=="HIGH" else st.warning if risk=="MEDIUM" else st.success)(f"Energy attention: {risk}. Current consumption is {variance:+.1f}% versus baseline.")
    st.markdown('<div class="recommend"><b>Recommended action</b><br>Review high-load equipment and operating schedules when consumption remains above baseline.</div>',unsafe_allow_html=True)

elif scenario == "Maintenance":
    a,b,c=st.columns(3)
    with a: temp=st.number_input("Process temperature",0.0,1000.0,315.0,1.0)
    with b: speed=st.number_input("Speed (RPM)",0.0,100000.0,1500.0,50.0)
    with c: wear=st.number_input("Wear index",0.0,100.0,45.0,1.0)
    risk_score=min(100,max(0,max(0,temp-290)*1.5+wear*.7)); health=max(0,100-risk_score)
    st.markdown("### Asset Health Result")
    x1,x2,x3=st.columns(3); x1.metric("Health score",f"{health:.0f}%"); x2.metric("Failure risk",f"{risk_score:.0f}%"); x3.metric("Assessment","HIGH" if risk_score>60 else ("MEDIUM" if risk_score>35 else "LOW"))
    st.progress(health/100)
    st.markdown('<div class="recommend"><b>Recommended action</b><br>Inspect the asset when thermal load and wear jointly indicate elevated failure exposure.</div>',unsafe_allow_html=True)

else:
    a,b,c=st.columns(3)
    with a: spend=st.number_input("Current spend",0.0,100000000.0,14800.0,100.0)
    with b: budget=st.number_input("Budget",0.0,100000000.0,12500.0,100.0)
    with c: previous=st.number_input("Previous period",0.0,100000000.0,13200.0,100.0)
    variance=spend-budget; growth=((spend-previous)/previous*100) if previous else 0
    st.markdown("### Cost Result")
    x1,x2,x3=st.columns(3); x1.metric("Spend",f"${spend:,.0f}"); x2.metric("Budget variance",f"${variance:+,.0f}"); x3.metric("Period growth",f"{growth:+.1f}%")
    st.bar_chart({"Budget":budget,"Current spend":spend})
    st.markdown('<div class="recommend"><b>Recommended action</b><br>Prioritize the largest cost drivers and investigate sustained budget variance before the next reporting period.</div>',unsafe_allow_html=True)
