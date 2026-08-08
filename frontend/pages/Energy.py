import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from frontend.services.api_client import safe_get, safe_post
from frontend.components.metrics import render_metric_row
from frontend.components.status import render_status_banner, render_empty_state

# Page Configuration
st.set_page_config(page_title="Energy | FacilityOPS", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>

/******************************
GENERAL PAGE
******************************/

.stApp{
    background:#F4F6F9;
}

.block-container{
    padding-top:0.8rem;
    padding-bottom:0.8rem;
    padding-left:1.2rem;
    padding-right:1.2rem;
    max-width:100%;
}

/******************************
HEADINGS
******************************/

h1,h2,h3{
    color:#111827;
    font-weight:600;
}

h1{
    font-size:2rem;
}

h2{
    font-size:1.35rem;
}

h3{
    font-size:1rem;
}

/******************************
CONTAINERS
******************************/

div[data-testid="stVerticalBlockBorderWrapper"]{
    border-radius:16px;
    border:1px solid #E5E7EB;
    background:white;
}

/******************************
METRICS
******************************/

div[data-testid="metric-container"]{

    background:white;

    border:1px solid #E5E7EB;

    border-radius:14px;

    padding:18px;

    box-shadow:0 1px 3px rgba(0,0,0,.05);

    height:115px;

}

/******************************
BUTTONS
******************************/

.stButton>button{

    width:100%;

    border-radius:10px;

    height:42px;

    border:none;

    background:#2563EB;

    color:white;

    font-weight:600;

}

.stButton>button:hover{

    background:#1D4ED8;

}

/******************************
SELECTBOX
******************************/

div[data-baseweb="select"]{

    border-radius:10px;

}

/******************************
PLOTLY
******************************/

.js-plotly-plot{

    border:1px solid #E5E7EB;

    border-radius:14px;

    background:white;

    padding:8px;

}

/******************************
SIDEBAR
******************************/

section[data-testid="stSidebar"]{

    background:#FFFFFF;

    border-right:1px solid #E5E7EB;
}

/******************************
DATAFRAME
******************************/

div[data-testid="stDataFrame"]{

    border-radius:14px;

    border:1px solid #E5E7EB;

}

/******************************
ALERTS
******************************/

div[data-baseweb="notification"]{

    border-radius:12px;

}

/******************************
REMOVE EXTRA GAP
******************************/

hr{
    margin-top:.5rem;
    margin-bottom:.5rem;
}

/* KPI CARDS */

.kpi-card{

    background:white;

    border:1px solid #E5E7EB;

    border-radius:16px;

    padding:18px;

    min-height:120px;

    transition:.2s;

    box-shadow:0 2px 4px rgba(0,0,0,.04);

}

.kpi-card:hover{

    box-shadow:0 8px 20px rgba(0,0,0,.08);

}

.kpi-title{

    color:#64748B;

    font-size:12px;

    text-transform:uppercase;

    letter-spacing:.08em;

    font-weight:600;

}

.kpi-value{

    font-size:34px;

    font-weight:700;

    color:#111827;

    margin-top:12px;

}

.kpi-footer{

    margin-top:14px;

    font-size:13px;

    color:#6B7280;

}

.kpi-good{

    color:#16A34A;

    font-weight:600;

}

.kpi-bad{

    color:#DC2626;

    font-weight:600;

}

.kpi-neutral{

    color:#2563EB;

    font-weight:600;

}

</style>
""", unsafe_allow_html=True)

header_left, header_mid, header_right = st.columns([6,2,2])

with header_left:
    st.markdown("""
    <div class="page-title">
        <div class="eyebrow">FACILITY OPERATIONS</div>
        <div class="title">Energy Operations Center</div>
    </div>
    """, unsafe_allow_html=True)

with header_mid:
    st.metric("Facility", "FAC-001")

with header_right:
    st.metric("Status", "Operational")

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("## Control Center")
    
    # 1. LIVE AUTOREFRESH TOGGLE (NEW)
    st.markdown("**Live Telemetry**")
    live_mode = st.checkbox("🔴 Enable Live IoT Stream")
    if live_mode:
        st_autorefresh(interval=5000, key="iot_refresh")
        st.caption(f"🟢 **Live Telemetry Stream**")

    st.info("Simulate an influx of new IoT sensor data.")
    seed_facility = st.selectbox("Target Facility", ["FAC-001", "FAC-002", "FAC-003", "FAC-004"], key="seed_target")
    
    if st.button("🔄 Trigger Mock Data Ingestion", width='stretch'):
        with st.spinner("Generating time-series data..."):
            res = safe_post("/energy/seed", params={"facility_id": seed_facility, "days": 30})
            if res.get("success"):
                st.success(f"Ingested {res['data']['records_seeded']} new records.")
                st.rerun()
            else:
                st.error("Ingestion pipeline failed.")

# 1. Module Health Check Integration
health_data = safe_get("/energy/health")
is_online = health_data.get("success", False)

if not is_online:
    render_status_banner(is_online=False, custom_message="Energy API is unreachable.")
    st.stop()

st.info("Energy Module Operational")

# 2. Facility Selection
selected_facility = st.selectbox(
    "Select Target Facility", 
    ["FAC-001", "FAC-002", "FAC-003", "FAC-004"], 
    label_visibility="collapsed"
)

api_facility_id = selected_facility.split(" ")[0]

from datetime import datetime

st.markdown("""
<style>
.dashboard-header{ background:white; border:1px solid #E5E7EB; border-radius:18px; padding:22px; margin-bottom:15px;}
.dashboard-title{font-size:32px; font-weight:700; color:#111827;}
.dashboard-sub{color:#6B7280; font-size:15px; margin-top:4px;}
.header-card{background:#F8FAFC; border:1px solid #E5E7EB; border-radius:12px; padding:14px; text-align:center; height:90px;}
.header-label{font-size:12px;color:#64748B;text-transform:uppercase;letter-spacing:.08em;}
.header-value{margin-top:8px;font-size:22px;font-weight:700;color:#111827;}
.live-dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:#10B981;margin-right:8px;}
</style>
""", unsafe_allow_html=True)

title_col, status_col, refresh_col, facility_col = st.columns([6,2,2,2])

with title_col:
    st.markdown("""
    <div class="dashboard-header">
        <div class="dashboard-title">Energy Operations Center</div>
        <div class="dashboard-sub">Enterprise Energy Intelligence Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

with status_col:
    st.markdown(f"""
    <div class="header-card">
        <div class="header-label">Module</div>
        <div class="header-value"><span class="live-dot"></span>ONLINE</div>
    </div>
    """, unsafe_allow_html=True)

with refresh_col:
    st.markdown(f"""
    <div class="header-card"><div class="header-label">Updated</div>
        <div class="header-value">{datetime.now().strftime("%H:%M")}</div>
    </div>
    """, unsafe_allow_html=True)

with facility_col:
    st.markdown(f"""
    <div class="header-card">
        <div class="header-label">Facility</div>
        <div class="header-value">{selected_facility}</div>
    </div>
    """, unsafe_allow_html=True)

# 3. Data Retrieval & Visualization
with st.spinner(f"Fetching telemetry for {api_facility_id}..."):
    records_response = safe_get(f"/energy/records/{api_facility_id}?limit=1500")
    if records_response.get("success"):
        records = records_response.get("data", {}).get("records", [])
        if not records:
            render_empty_state("Energy Consumption", f"No data records found for {api_facility_id}. Awaiting initial IoT ingestion.")
        else:
            df = pd.DataFrame(records)
            # --- DATA PREP ---
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            if 'hvac_kwh' not in df.columns:
                df['hvac_kwh'] = df['energy_kwh'] * 0.45
                df['lighting_kwh'] = df['energy_kwh'] * 0.25
                df['equipment_kwh'] = df['energy_kwh'] * 0.30
            total_kwh = df['energy_kwh'].sum()
            peak_kw = df['peak_demand_kw'].max() if 'peak_demand_kw' in df.columns and df['peak_demand_kw'].notna().any() else 0.0
            total_cost = df['cost'].sum() if 'cost' in df.columns and df['cost'].notna().any() else total_kwh * 0.12

            k1, k2, k3, k4, k5, k6, k7 = st.columns(7)

            with k1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Total Energy</div>
                    <div class="kpi-value">{total_kwh:,.0f}</div>
                    <div class="kpi-footer"><span class="kpi-good">▼ 3.2%</span> vs previous month</div>
                </div>
                """, unsafe_allow_html=True)

            with k2:
                color = "kpi-good" if peak_kw < 300 else "kpi-bad"
                text = "Normal" if peak_kw < 300 else "Critical"
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Peak Demand</div>
                    <div class="kpi-value">{peak_kw:.1f} kW</div>
                    <div class="kpi-footer"><span class="{color}">{text}</span></div>
                </div>
                """, unsafe_allow_html=True)

            with k3:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Energy Cost</div>
                    <div class="kpi-value">${total_cost:,.0f}</div>
                    <div class="kpi-footer"><span class="kpi-good">Under Budget</span></div>
                </div>
                """, unsafe_allow_html=True)

            with k4:
                st.markdown("""
                <div class="kpi-card">
                    <div class="kpi-title">Efficiency</div>
                    <div class="kpi-value">94%</div>
                    <div class="kpi-footer"><span class="kpi-good">Excellent</span></div>
                </div>
                """, unsafe_allow_html=True)

            with k5:
                co2 = total_kwh * 0.38
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">CO₂ Emissions</div>
                    <div class="kpi-value">{co2:,.0f}</div>
                    <div class="kpi-footer">kg CO₂</div>
                </div>
                """, unsafe_allow_html=True)

            with k6:
                alerts = len(alerts) if "alerts" in locals() else 0
                colour = "kpi-good" if alerts == 0 else "kpi-bad"
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Active Alerts</div>
                    <div class="kpi-value">{alerts}</div>
                    <div class="kpi-footer"><span class="{colour}">Open Events</span></div>
                </div>
                """, unsafe_allow_html=True)

            with k7:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Avg Daily Usage</div>
                    <div class="kpi-value">{total_kwh/30:,.0f}</div>
                    <div class="kpi-footer">kWh / day</div>
                </div>
                """, unsafe_allow_html=True)

            left, right = st.columns([8, 4], gap="medium")

            with left:
                with st.container(border=True):
                    st.subheader("Energy Consumption Trend")
                    fig_area = go.Figure()
                    fig_area.add_trace(go.Scatter(x=df['timestamp'], y=df['equipment_kwh'], stackgroup='one', name='Equipment', line=dict(width=0), fillcolor='#cbd5e1'))
                    fig_area.add_trace(go.Scatter(x=df['timestamp'], y=df['lighting_kwh'], stackgroup='one', name='Lighting', line=dict(width=0), fillcolor='#10b981'))
                    fig_area.add_trace(go.Scatter(x=df['timestamp'], y=df['hvac_kwh'], stackgroup='one', name='HVAC', line=dict(width=0), fillcolor='#3b82f6'))
                    peak_idx = df['energy_kwh'].idxmax()
                    peak_row = df.loc[peak_idx]
                    if peak_row['energy_kwh'] > 100:
                        fig_area.add_trace(go.Scatter(
                            x=[peak_row['timestamp']],
                            y=[peak_row['energy_kwh']],
                            mode='markers',
                            name='Anomaly Spike',
                            marker=dict(color='red', size=14, symbol='x-open', line=dict(width=3, color='darkred'))
                        ))
                    fig_area.update_layout(
                        height=470,
                        showlegend=True,
                        legend=dict(orientation='h', y=1.05, x=0),
                        margin=dict(l=10, r=10, t=20, b=10)
                    )
                    fig_area.update_xaxes(showgrid=False, zeroline=False)
                    fig_area.update_yaxes(showgrid=True, gridcolor="#f8fafc", zeroline=False)
                    st.plotly_chart(fig_area, width='content', config={"displayModeBar":False})

            with right:
                with st.container(border=True):
                    st.subheader("Consumption Breakdown")
                    energy_split = pd.DataFrame({
                        "Category": ["HVAC", "Lighting", "Equipment"],
                        "Energy": [df["hvac_kwh"].sum(), df["lighting_kwh"].sum(), df["equipment_kwh"].sum()]
                    })
                    fig_bar = px.bar(
                        energy_split,
                        x="Energy",
                        y="Category",
                        orientation="h",
                        text_auto=".0f",
                        color="Category",
                        color_discrete_sequence=["#2563EB", "#10B981", "#94A3B8"]
                    )
                    fig_bar.update_layout(
                        height=240,
                        showlegend=False,
                        margin=dict(l=0, r=0, t=10, b=10),
                        paper_bgcolor="white",
                        plot_bgcolor="white"
                    )
                    st.plotly_chart(fig_bar, width='content', config={"displayModeBar":False})

            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Average Daily", f"{total_kwh/30:,.0f} kWh")
            with c2:
                st.metric("Peak Day", df["energy_kwh"].max())
            st.metric("Largest Consumer", "HVAC")

            row1, row2, row3 = st.columns([4, 4, 4], gap="medium")

            with row1:
                with st.container(border=True):
                    st.subheader("Demand Heatmap")
                    df["hour"] = df["timestamp"].dt.hour
                    df["day"] = df["timestamp"].dt.day_name()
                    heatmap_data = df.pivot_table(index="day", columns="hour", values="energy_kwh", aggfunc="mean")
                    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    heatmap_data = heatmap_data.reindex(index=days, columns=range(24), fill_value=0)
                    fig_heat = px.imshow(heatmap_data, aspect="auto", color_continuous_scale="Blues")
                    fig_heat.update_layout(
                        height=360,
                        margin=dict(l=5, r=5, t=5, b=5),
                        paper_bgcolor="white",
                        plot_bgcolor="white",
                        coloraxis_showscale=False
                    )
                    st.plotly_chart(fig_heat, width='content', config={"displayModeBar":False})

            with row2:
                with st.container(border=True):
                    st.subheader("Peak Demand")
                    demand = df.groupby(df["timestamp"].dt.hour)["peak_demand_kw"].mean().reset_index()
                    fig_peak = px.line(demand, x="timestamp", y="peak_demand_kw")
                    fig_peak.update_traces(line=dict(color="#2563EB", width=3))
                    fig_peak.update_layout(
                        height=360,
                        margin=dict(l=5, r=5, t=5, b=5),
                        paper_bgcolor="white",
                        plot_bgcolor="white"
                    )
                    st.plotly_chart(fig_peak, width='content', config={"displayModeBar":False})

            forecast = df.copy()
            forecast["date"] = forecast["timestamp"].dt.date
            forecast = forecast.groupby("date")["energy_kwh"].sum().reset_index()
            forecast["forecast"] = forecast["energy_kwh"].rolling(5).mean()

            with row3:
                with st.container(border=True):
                    st.subheader("7-Day Forecast")
                    fig_forecast = px.line(forecast, x="date", y=["energy_kwh", "forecast"])
                    fig_forecast.update_layout(
                        height=360,
                        margin=dict(l=5, r=5, t=5, b=5),
                        legend=dict(orientation="h", y=1.02),
                        paper_bgcolor="white",
                        plot_bgcolor="white"
                    )
                    st.plotly_chart(fig_forecast, width='content', config={"displayModeBar":False})

            # --- AGENTIC INTELLIGENCE ---
            st.markdown("### 🤖 Agentic Intelligence & Optimization")
            col_agent1, col_agent2 = st.columns([1.2, 1])

            with col_agent1:
                st.markdown("#### Agent Threat Analysis")
                st.info("The Energy Agent continuously monitors utility data for peak demand violations.")
                analysis_response = safe_get(f"/energy/analyze/{api_facility_id}?days=7")
                if analysis_response.get("success"):
                    insights = analysis_response.get("data", {})
                    alerts = insights.get("alerts", [])
                    recommendations = insights.get("recommendations", [])
                    if alerts:
                        st.error(f"⚠️ Agent detected {len(alerts)} anomalies requiring attention.")
                        for alert in alerts:
                            with st.expander(f"[{alert.get('severity', 'INFO').upper()}] {alert.get('type', 'Alert')}"):
                                st.write(f"**Timestamp:** {alert.get('timestamp', 'Just now')}")
                                st.write(f"**Message:** {alert.get('message', 'No details provided.')}")
                                st.caption(f"Source: {alert.get('source', 'Energy Agent')} | ID: {alert.get('alert_id', 'SYS-001')}")
                    else:
                        st.success("✅ Agent analysis complete. Consumption patterns are nominal.")
                    if recommendations:
                        st.markdown("**🛠️ Recommended Actions**")
                        for idx, rec in enumerate(recommendations):
                            priority_color = "red" if rec.get('priority') == "High" else "orange" if rec.get('priority') == "Medium" else "green"
                            rc1, rc2 = st.columns([3, 1])
                            with rc1:
                                st.markdown(f"- **{rec.get('action')}** (Priority: :{priority_color}[{rec.get('priority', 'Low')}])")
                            with rc2:
                                if st.button("Execute Action", key=f"resolve_{idx}", width='content'):
                                    st.toast(f"Agent executing: {rec.get('action')}", icon="⚙️")
                                    st.success("Resolved dynamically at the edge.")
                else:
                    st.error("Agent analysis failed to execute.")

            with col_agent2:
                st.markdown("#### 🎛️ What-If Control Simulator")
                st.markdown("<span style='color: #64748b; font-size: 0.9em;'>Forecast agent-driven optimizations before deployment.</span>", unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown("**1. Configure Parameters**")
                    slider_col1, slider_col2 = st.columns(2)
                    with slider_col1:
                        hvac_offset = st.slider("HVAC Offset (°C)", 0.0, 3.0, 1.0, 0.5)
                    with slider_col2:
                        light_dim = st.slider("Lighting Dimming (%)", 0, 50, 15, 5)
                    hvac_savings_kwh = hvac_offset * 0.06 * df['hvac_kwh'].sum()
                    light_savings_kwh = (light_dim / 100.0) * df['lighting_kwh'].sum()
                    total_saved = hvac_savings_kwh + light_savings_kwh
                    est_cost_saved = total_saved * 0.12
                    co2_saved_kg = total_saved * 0.38
                    st.markdown("**2. Projected 30-Day Impact**")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Energy Saved", f"{total_saved:,.0f} kWh", delta="Optimized")
                    m2.metric("Cost Avoided", f"${est_cost_saved:,.0f}", delta="Added to Budget", delta_color="normal")
                    m3.metric("CO2 Reduction", f"{co2_saved_kg:,.0f} kg", delta="ESG Goal", delta_color="normal")
                    fig_compare = go.Figure()
                    fig_compare.add_trace(go.Bar(y=['Est. Cost'], x=[total_cost], name='Current Baseline', orientation='h', marker=dict(color='#cbd5e1')))
                    fig_compare.add_trace(go.Bar(y=['Est. Cost'], x=[total_cost - est_cost_saved], name='Agent Optimized', orientation='h', marker=dict(color='#10b981')))
                    fig_compare.update_layout(
                        barmode='group', height=430, margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=False, visible=False),
                        showlegend=True, legend=dict(orientation='h', y=-0.2)
                    )
                    st.plotly_chart(fig_compare, width='content')
                    if st.button("🚀 Deploy to Edge Devices", width='content', type="secondary"):
                        st.toast("Success! Configurations pushed to HVAC and Lighting controllers via IoT gateway.", icon="✅")
    else:
        st.error("Failed to retrieve energy records from the database layer.")

# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from streamlit_autorefresh import st_autorefresh
# from frontend.services.api_client import safe_get, safe_post
# from frontend.components.metrics import render_metric_row
# from frontend.components.status import render_status_banner, render_empty_state

# # Page Configuration
# st.set_page_config(page_title="Energy | FacilityOPS", layout="wide", initial_sidebar_state="expanded")


# st.markdown("""
# <style>
# div[data-testid="metric-container"] {
#     background-color: #ffffff;
#     border: 1px solid #eef2f6;
#     padding: 15px 20px;
#     border-radius: 6px;
#     box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
#     border-left: 3px solid #3b82f6; 
# }
# div.stAlert {
#     border-radius: 6px;
#     border: none;
# }
# </style>
# """, unsafe_allow_html=True)

# st.title("⚡ Energy Intelligence & Monitoring")
# st.markdown("Monitor utility data, IoT sensor inputs, and agentic module health.")

# # --- SIDEBAR CONTROLS ---
# with st.sidebar:
#     st.markdown("### ⚙️ Module Controls")
    
#     # 1. LIVE AUTOREFRESH TOGGLE (NEW)
#     st.markdown("**Live Telemetry**")
#     live_mode = st.checkbox("🔴 Enable Live IoT Stream")
#     if live_mode:
#         st_autorefresh(interval=5000, key="iot_refresh")
#         st.caption(f"🟢 **Live Telemetry Stream**")

#     st.divider()

#     st.info("Simulate an influx of new IoT sensor data.")
#     seed_facility = st.selectbox("Target Facility", ["FAC-001", "FAC-002", "FAC-003", "FAC-004"], key="seed_target")
    
#     if st.button("🔄 Trigger Mock Data Ingestion", width='content'):
#         with st.spinner("Generating time-series data..."):
#             res = safe_post("/energy/seed", params={"facility_id": seed_facility, "days": 30})
#             if res.get("success"):
#                 st.success(f"Ingested {res['data']['records_seeded']} new records.")
#                 st.rerun()
#             else:
#                 st.error("Ingestion pipeline failed.")

# # 1. Module Health Check Integration
# health_data = safe_get("/energy/health")
# is_online = health_data.get("success", False)

# if not is_online:
#     render_status_banner(is_online=False, custom_message="Energy API is unreachable.")
#     st.stop()

# st.success(f"✅ Energy Module Status: Operational | Intelligence Engine: Active")
# st.divider()

# # 2. Facility Selection
# st.markdown("### 🏢 Dashboard")
# selected_facility = st.selectbox(
#     "Select Target Facility", 
#     ["FAC-001", "FAC-002", "FAC-003", "FAC-004"], 
#     label_visibility="collapsed"
# )

# api_facility_id = selected_facility.split(" ")[0]

# # 3. Data Retrieval & Visualization
# with st.spinner(f"Fetching telemetry for {api_facility_id}..."):
#     records_response = safe_get(f"/energy/records/{api_facility_id}?limit=1500")
    
#     if records_response.get("success"):
#         records = records_response.get("data", {}).get("records", [])
        
#         if not records:
#             render_empty_state("Energy Consumption", f"No data records found for {api_facility_id}. Awaiting initial IoT ingestion.")
#         else:
#             df = pd.DataFrame(records)
            
#             # --- DATA PREP ---
#             df['timestamp'] = pd.to_datetime(df['timestamp'])
#             df = df.sort_values('timestamp')
            
#             if 'hvac_kwh' not in df.columns:
#                 df['hvac_kwh'] = df['energy_kwh'] * 0.45
#                 df['lighting_kwh'] = df['energy_kwh'] * 0.25
#                 df['equipment_kwh'] = df['energy_kwh'] * 0.30

#             total_kwh = df['energy_kwh'].sum()
#             peak_kw = df['peak_demand_kw'].max() if df['peak_demand_kw'].notna().any() else 0.0
#             total_cost = df['cost'].sum() if df['cost'].notna().any() else total_kwh * 0.12

#             # --- KPI ROW ---
#             kpi1, kpi2, kpi3, kpi4 = st.columns(4)
#             kpi1.metric("Total 30-Day Energy", f"{total_kwh:,.0f} kWh", delta="-3.2% vs last month")
#             kpi2.metric("Peak Demand", f"{peak_kw:,.1f} kW", delta="Stable" if peak_kw < 300 else "Critical Spike", delta_color="off" if peak_kw < 300 else "inverse")
#             kpi3.metric("Est. Operational Cost", f"${total_cost:,.2f}", delta="-$142.50 vs budget", delta_color="inverse")
#             kpi4.metric("Agent Efficiency Score", "94 / 100", delta="+2 pts")

#             # --- CHARTS ROW ---
#             st.markdown("<br>", unsafe_allow_html=True)
#             col_chart1, col_chart2 = st.columns([1, 2.5])

#             with col_chart1:
#                 st.markdown("**Consumption by End-Use**")
#                 donut_data = {
#                     'Category': ['HVAC', 'Lighting', 'Equipment'],
#                     'Value': [df['hvac_kwh'].sum(), df['lighting_kwh'].sum(), df['equipment_kwh'].sum()]
#                 }
#                 fig_donut = px.pie(donut_data, values='Value', names='Category', hole=0.7,
#                                    color_discrete_sequence=['#3b82f6', '#10b981', '#cbd5e1'])
#                 fig_donut.update_layout(
#                     template="plotly_white", margin=dict(t=0, b=0, l=0, r=0), 
#                     showlegend=True, legend=dict(orientation="h", y=-0.2),
#                     paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
#                 )
#                 fig_donut.update_traces(textinfo='none')
#                 st.plotly_chart(fig_donut, width='content')

#             with col_chart2:
#                 st.markdown("**30-Day Telemetry Trend**")
#                 fig_area = go.Figure()
                
#                 # Base area charts
#                 fig_area.add_trace(go.Scatter(x=df['timestamp'], y=df['equipment_kwh'], stackgroup='one', name='Equipment', line=dict(width=0), fillcolor='#cbd5e1'))
#                 fig_area.add_trace(go.Scatter(x=df['timestamp'], y=df['lighting_kwh'], stackgroup='one', name='Lighting', line=dict(width=0), fillcolor='#10b981'))
#                 fig_area.add_trace(go.Scatter(x=df['timestamp'], y=df['hvac_kwh'], stackgroup='one', name='HVAC', line=dict(width=0), fillcolor='#3b82f6'))

#                 # --- VISUAL ANOMALY MARKER (NEW) ---
#                 # Find the highest peak to simulate an anomaly overlay
#                 peak_idx = df['energy_kwh'].idxmax()
#                 peak_row = df.loc[peak_idx]
                
#                 if peak_row['energy_kwh'] > 100: # Threshold for showing anomaly
#                     fig_area.add_trace(go.Scatter(
#                         x=[peak_row['timestamp']], 
#                         y=[peak_row['energy_kwh']], 
#                         mode='markers', 
#                         name='Anomaly Spike',
#                         marker=dict(color='red', size=14, symbol='x-open', line=dict(width=3, color='darkred'))
#                     ))

#                 fig_area.update_layout(
#                     template="plotly_white", margin=dict(t=10, b=10, l=0, r=0), 
#                     showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
#                 )
#                 fig_area.update_xaxes(showgrid=False, zeroline=False)
#                 fig_area.update_yaxes(showgrid=True, gridcolor="#f8fafc", zeroline=False)
#                 st.plotly_chart(fig_area, width='content')

#             st.markdown("<br>", unsafe_allow_html=True)
#             st.markdown("**Hourly Consumption Heatmap (Agent View)**")
            
#             df['hour'] = df['timestamp'].dt.hour
#             df['day'] = df['timestamp'].dt.day_name()
#             heatmap_data = df.pivot_table(index='day', columns='hour', values='energy_kwh', aggfunc='mean')
            
#             days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
#             heatmap_data = heatmap_data.reindex(index=days_order, columns=range(24), fill_value=0)

#             fig_heat = px.imshow(heatmap_data, text_auto=False, aspect="auto", color_continuous_scale="Blues", labels=dict(color="kWh", x="Hour of Day", y="Day of Week"))
#             fig_heat.update_layout(template="plotly_white", margin=dict(t=10, b=10, l=10, r=10), height=250, xaxis=dict(tickmode='linear', dtick=2), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
#             fig_heat.update_coloraxes(showscale=False)
#             st.plotly_chart(fig_heat, width='content')

#             st.divider()

#             # --- AGENTIC INTELLIGENCE ---
#             st.markdown("### 🤖 Agentic Intelligence & Optimization")
            
#             col_agent1, col_agent2 = st.columns([1.2, 1])
            
#             with col_agent1:
#                 st.markdown("#### Agent Threat Analysis")
#                 st.info("The Energy Agent continuously monitors utility data for peak demand violations.")
                
#                 # Fetch agent insights automatically for better flow
#                 analysis_response = safe_get(f"/energy/analyze/{api_facility_id}?days=7")
                
#                 if analysis_response.get("success"):
#                     insights = analysis_response.get("data", {})
#                     alerts = insights.get("alerts", [])
#                     recommendations = insights.get("recommendations", [])

#                     if alerts:
#                         st.error(f"⚠️ Agent detected {len(alerts)} anomalies requiring attention.")
#                         for alert in alerts:
#                             with st.expander(f"[{alert.get('severity', 'INFO').upper()}] {alert.get('type', 'Alert')}"):
#                                 st.write(f"**Timestamp:** {alert.get('timestamp', 'Just now')}")
#                                 st.write(f"**Message:** {alert.get('message', 'No details provided.')}")
#                                 st.caption(f"Source: {alert.get('source', 'Energy Agent')} | ID: {alert.get('alert_id', 'SYS-001')}")
#                     else:
#                         st.success("✅ Agent analysis complete. Consumption patterns are nominal.")

#                     if recommendations:
#                         st.markdown("**🛠️ Recommended Actions**")
#                         for idx, rec in enumerate(recommendations):
#                             priority_color = "red" if rec.get('priority') == "High" else "orange" if rec.get('priority') == "Medium" else "green"
                            
#                             # --- 1-CLICK AUTO-RESOLVE BUTTONS (NEW) ---
#                             rc1, rc2 = st.columns([3, 1])
#                             with rc1:
#                                 st.markdown(f"- **{rec.get('action')}** (Priority: :{priority_color}[{rec.get('priority', 'Low')}])")
#                             with rc2:
#                                 if st.button("Execute Action", key=f"resolve_{idx}", width='content'):
#                                     st.toast(f"Agent executing: {rec.get('action')}", icon="⚙️")
#                                     st.success("Resolved dynamically at the edge.")
#                 else:
#                     st.error("Agent analysis failed to execute.")

#             with col_agent2:
#                 st.markdown("#### 🎛️ What-If Control Simulator")
#                 st.markdown("<span style='color: #64748b; font-size: 0.9em;'>Forecast agent-driven optimizations before deployment.</span>", unsafe_allow_html=True)
                
#                 with st.container(border=True):
#                     st.markdown("**1. Configure Parameters**")
#                     slider_col1, slider_col2 = st.columns(2)
#                     with slider_col1:
#                         hvac_offset = st.slider("HVAC Offset (°C)", 0.0, 3.0, 1.0, 0.5)
#                     with slider_col2:
#                         light_dim = st.slider("Lighting Dimming (%)", 0, 50, 15, 5)
                    
#                     hvac_savings_kwh = hvac_offset * 0.06 * df['hvac_kwh'].sum()
#                     light_savings_kwh = (light_dim / 100.0) * df['lighting_kwh'].sum()
#                     total_saved = hvac_savings_kwh + light_savings_kwh
#                     est_cost_saved = total_saved * 0.12
#                     co2_saved_kg = total_saved * 0.38 

#                     st.divider()

#                     st.markdown("**2. Projected 30-Day Impact**")
#                     m1, m2, m3 = st.columns(3)
#                     m1.metric("Energy Saved", f"{total_saved:,.0f} kWh", delta="Optimized")
#                     m2.metric("Cost Avoided", f"${est_cost_saved:,.0f}", delta="Added to Budget", delta_color="normal")
#                     m3.metric("CO2 Reduction", f"{co2_saved_kg:,.0f} kg", delta="ESG Goal", delta_color="normal")

#                     fig_compare = go.Figure()
#                     fig_compare.add_trace(go.Bar(y=['Est. Cost'], x=[total_cost], name='Current Baseline', orientation='h', marker=dict(color='#cbd5e1')))
#                     fig_compare.add_trace(go.Bar(y=['Est. Cost'], x=[total_cost - est_cost_saved], name='Agent Optimized', orientation='h', marker=dict(color='#10b981')))
#                     fig_compare.update_layout(
#                         barmode='group', height=140, margin=dict(l=10, r=10, t=10, b=10),
#                         paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
#                         xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=False, visible=False),
#                         showlegend=True, legend=dict(orientation="h", y=-0.2)
#                     )
#                     st.plotly_chart(fig_compare, width='content')

#                     if st.button("🚀 Deploy to Edge Devices", width='content', type="secondary"):
#                         st.toast("Success! Configurations pushed to HVAC and Lighting controllers via IoT gateway.", icon="✅")

#     else:
#         st.error("Failed to retrieve energy records from the database layer.")
