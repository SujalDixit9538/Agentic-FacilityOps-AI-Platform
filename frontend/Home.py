import sys
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st

root_dir = str(Path(__file__).parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.utils.session import initialize_session
from frontend.services.api_client import safe_get
from frontend.components.kpi_cards import render_kpi_row

st.set_page_config(page_title="FacilityOPS AI", page_icon="🏢", layout="wide", initial_sidebar_state="expanded")
initialize_session()

st.markdown("""
<style>
.stApp{background:#f4f7fb}.hero{background:linear-gradient(135deg,#0f172a,#1e3a8a 58%,#0f766e);color:#fff;border-radius:20px;padding:28px 30px;margin-bottom:18px;box-shadow:0 12px 30px rgba(15,23,42,.12)}.eyebrow{font-size:10px;font-weight:800;letter-spacing:.16em;color:#93c5fd;text-transform:uppercase}.hero h1{font-size:32px;margin:4px 0}.hero p{color:#cbd5e1;margin:0;font-size:14px}.module{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:18px;min-height:150px;box-shadow:0 4px 14px rgba(15,23,42,.04)}.module h3{margin:0 0 7px}.module p{color:#64748b;font-size:12px;min-height:36px}.brief{background:#fff;border:1px solid #e2e8f0;border-left:4px solid #2563eb;border-radius:15px;padding:18px;box-shadow:0 4px 14px rgba(15,23,42,.04)}
</style>
<div class="hero"><div class="eyebrow">FacilityOPS AI · Command Center</div><h1>Facility Operations Intelligence</h1><p>One operational view across energy, assets, occupancy, security and cost performance.</p></div>
""", unsafe_allow_html=True)

with st.spinner("Connecting to facility intelligence services..."):
    health_data = safe_get("/health", fallback_data={"status":"unavailable"}) or {}
health_payload = health_data.get("data", {}) or {}
backend_online = health_data.get("success", False)
db_operational = health_payload.get("database") == "operational"
checked = health_payload.get("request_time") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

if backend_online and db_operational:
    st.success("Facility intelligence services are connected and ready.")

st.markdown("### Platform Overview")
render_kpi_row([
    {"title":"Platform", "value":"Ready" if backend_online else "Checking", "delta":"Connected" if backend_online else "Pending"},
    {"title":"Data Services", "value":"Ready" if db_operational else "Checking", "delta":"Connected" if db_operational else "Pending"},
    {"title":"AI Modules", "value":"Multi-Agent", "delta":"Ready"},
    {"title":"Interface", "value":"Operator Ready", "delta":"Live"},
    {"title":"Last Checked", "value":checked, "delta":None},
], columns=3)

st.markdown("### Operations Suite")
modules = [
    ("🌐","Executive Intelligence","Cross-agent facility briefings, analytics and reporting.","pages/Dashboard.py"),
    ("⚡","Energy Intelligence","Consumption, demand and energy optimization workflows.","pages/Energy.py"),
    ("🔧","Predictive Maintenance","Asset health, condition assessment and maintenance actions.","pages/Maintenance.py"),
    ("💰","Cost Intelligence","Spend analysis, cost drivers and savings opportunities.","pages/Cost.py"),
    ("🛡️","Occupancy & Security","Zone utilization, incidents and physical-security intelligence.","pages/Occupancy_and_Security.py"),
    ("🧪","Scenario Lab","Test operational conditions and generate instant results and recommendations.","pages/Scenario_Lab.py"),
]
for start in range(0,len(modules),3):
    cols=st.columns(3)
    for col,(icon,name,summary,page) in zip(cols,modules[start:start+3]):
        with col:
            st.markdown(f'<div class="module"><h3>{icon} {name}</h3><p>{summary}</p></div>',unsafe_allow_html=True)
            st.page_link(page,label=f"Open {name}",icon=icon,width="stretch")

st.markdown("### Operator Brief")
st.markdown('<div class="brief"><b>Start with a live module</b><br><span style="color:#64748b;font-size:12px">Review current facility intelligence, then use Scenario Lab to test a specific operating condition and see how FacilityOPS responds.</span></div>',unsafe_allow_html=True)
