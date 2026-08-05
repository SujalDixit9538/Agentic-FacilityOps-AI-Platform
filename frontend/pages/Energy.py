import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from frontend.services.api_client import safe_get, safe_post
from frontend.components.metrics import render_metric_row
from frontend.components.status import render_status_banner, render_empty_state

# Page Configuration - Force wide layout for enterprise feel
st.set_page_config(page_title="Energy | FacilityOPS", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM UI HACK: Minimalist Metric Cards ---
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #ffffff;
    border: 1px solid #eef2f6;
    padding: 15px 20px;
    border-radius: 6px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    border-left: 3px solid #3b82f6; 
}
div.stAlert {
    border-radius: 6px;
    border: none;
}
</style>
""", unsafe_allow_html=True)

st.title("⚡ Energy Intelligence & Monitoring")
st.markdown("Monitor utility data, IoT sensor inputs, and agentic module health.")

# Add the Administrative Sidebar Control
with st.sidebar:
    st.markdown("### ⚙️ Module Controls")
    st.info("Simulate an influx of new IoT sensor data.")
    
    seed_facility = st.selectbox("Target Facility", ["FAC-001", "FAC-002", "FAC-003", "FAC-004"], key="seed_target")
    
    if st.button("🔄 Trigger Mock Data Ingestion", use_container_width=True):
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
    render_status_banner(
        is_online=False, 
        custom_message="Energy API is currently unreachable. Displaying cached layout."
    )
    st.stop()

status_info = health_data.get("data", {})
if status_info.get("status") == "operational":
    st.success(f"✅ Energy Module Status: Operational | Intelligence Engine: Active")

st.divider()

# 2. Facility Selection (Expanded to show scalability)
st.markdown("### 🏢 Executive Dashboard")
selected_facility = st.selectbox(
    "Select Target Facility", 
    ["FAC-001", "FAC-002", "FAC-003", "FAC-004"], 
    label_visibility="collapsed"
)

# Strip out the display tags for the API call
api_facility_id = selected_facility.split(" ")[0]

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
            peak_kw = df['peak_demand_kw'].max() if df['peak_demand_kw'].notna().any() else 0.0
            total_cost = df['cost'].sum() if df['cost'].notna().any() else total_kwh * 0.12

            # --- KPI ROW ---
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Total 30-Day Energy", f"{total_kwh:,.0f} kWh", delta="-3.2% vs last month")
            kpi2.metric("Peak Demand", f"{peak_kw:,.1f} kW", delta="Stable", delta_color="off")
            kpi3.metric("Est. Operational Cost", f"${total_cost:,.2f}", delta="-$142.50 vs budget", delta_color="inverse")
            kpi4.metric("Agent Efficiency Score", "94 / 100", delta="+2 pts")

            # --- CHARTS ROW (Minimalist Overhaul) ---
            st.markdown("<br>", unsafe_allow_html=True)
            col_chart1, col_chart2 = st.columns([1, 2.5])

            with col_chart1:
                st.markdown("**Consumption by End-Use**")
                donut_data = {
                    'Category': ['HVAC', 'Lighting', 'Equipment'],
                    'Value': [df['hvac_kwh'].sum(), df['lighting_kwh'].sum(), df['equipment_kwh'].sum()]
                }
                fig_donut = px.pie(donut_data, values='Value', names='Category', hole=0.7,
                                   color_discrete_sequence=['#3b82f6', '#10b981', '#cbd5e1'])
                fig_donut.update_layout(
                    template="plotly_white",
                    margin=dict(t=0, b=0, l=0, r=0), 
                    showlegend=True, 
                    legend=dict(orientation="h", y=-0.2),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                fig_donut.update_traces(textinfo='none') # Cleaner look without overlapping text
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_chart2:
                st.markdown("**30-Day Telemetry Trend**")
                fig_area = px.area(df, x='timestamp', y=['hvac_kwh', 'lighting_kwh', 'equipment_kwh'],
                                   labels={'value': 'kWh', 'timestamp': 'Date', 'variable': 'System'},
                                   color_discrete_map={'hvac_kwh': '#3b82f6', 'lighting_kwh': '#10b981', 'equipment_kwh': '#cbd5e1'})
                fig_area.update_layout(
                    template="plotly_white",
                    margin=dict(t=10, b=10, l=0, r=0), 
                    xaxis_title=None,
                    yaxis_title=None,
                    legend_title_text=None,
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                # Strip out heavy gridlines
                fig_area.update_xaxes(showgrid=False, zeroline=False)
                fig_area.update_yaxes(showgrid=True, gridcolor="#f8fafc", zeroline=False)
                st.plotly_chart(fig_area, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Hourly Consumption Heatmap (Agent View)**")
            
            # --- HEATMAP FIX: Force absolute 24-hour grid ---
            df['hour'] = df['timestamp'].dt.hour
            df['day'] = df['timestamp'].dt.day_name()
            
            heatmap_data = df.pivot_table(index='day', columns='hour', values='energy_kwh', aggfunc='mean')
            
            # Ensure every day and every hour (0-23) exists to prevent jagged/broken grids
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            heatmap_data = heatmap_data.reindex(index=days_order, columns=range(24), fill_value=0)

            fig_heat = px.imshow(heatmap_data, text_auto=False, aspect="auto", 
                                 color_continuous_scale="Blues",
                                 labels=dict(color="kWh", x="Hour of Day", y="Day of Week"))
            fig_heat.update_layout(
                template="plotly_white",
                margin=dict(t=10, b=10, l=10, r=10), 
                height=250,
                xaxis=dict(tickmode='linear', dtick=2), # Cleaner axis ticks
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            fig_heat.update_coloraxes(showscale=False) # Hide color bar for minimalism
            st.plotly_chart(fig_heat, use_container_width=True)

            st.divider()

            # --- AGENTIC INTELLIGENCE ---
            st.markdown("### 🤖 Agentic Intelligence & Optimization")
            
            col_agent1, col_agent2 = st.columns([1, 1])
            
            with col_agent1:
                st.markdown("#### Agent Threat Analysis")
                st.info("The Energy Agent continuously monitors utility data for peak demand violations.")
                if st.button("🧠 Run Diagnostics & Anomaly Detection", type="primary", use_container_width=True):
                    with st.spinner("Agent is analyzing consumption patterns..."):
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
                                for rec in recommendations:
                                    priority_color = "red" if rec.get('priority') == "High" else "orange" if rec.get('priority') == "Medium" else "green"
                                    st.markdown(f"- **{rec.get('action')}** (Priority: :{priority_color}[{rec.get('priority', 'Low')}])")
                        else:
                            st.error("Agent analysis failed to execute.")

            with col_agent2:
                import plotly.graph_objects as go

                st.markdown("#### 🎛️ What-If Control Simulator")
                st.markdown("<span style='color: #64748b; font-size: 0.9em;'>Forecast agent-driven optimizations before deployment.</span>", unsafe_allow_html=True)
                
                with st.container(border=True):
                    st.markdown("**1. Configure Parameters**")
                    
                    # Side-by-side sliders for a compact, control-panel feel
                    slider_col1, slider_col2 = st.columns(2)
                    with slider_col1:
                        hvac_offset = st.slider("HVAC Offset (°C)", 0.0, 3.0, 1.0, 0.5, help="Increase AC baseline temp.")
                    with slider_col2:
                        light_dim = st.slider("Lighting Dimming (%)", 0, 50, 15, 5, help="Reduce perimeter lighting.")
                    
                    # Math for simulator
                    hvac_savings_kwh = hvac_offset * 0.06 * df['hvac_kwh'].sum()
                    light_savings_kwh = (light_dim / 100.0) * df['lighting_kwh'].sum()
                    total_saved = hvac_savings_kwh + light_savings_kwh
                    est_cost_saved = total_saved * 0.12
                    co2_saved_kg = total_saved * 0.38 # EPA approx 0.38 kg CO2 per kWh

                    st.divider()

                    st.markdown("**2. Projected 30-Day Impact**")
                    
                    # 3-Column Enterprise Metrics
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Energy Saved", f"{total_saved:,.0f} kWh", delta="Optimized")
                    m2.metric("Cost Avoided", f"${est_cost_saved:,.0f}", delta="Added to Budget", delta_color="normal")
                    m3.metric("CO2 Reduction", f"{co2_saved_kg:,.0f} kg", delta="ESG Goal", delta_color="normal")

                    # Sleek horizontal comparison chart
                    fig_compare = go.Figure()
                    fig_compare.add_trace(go.Bar(
                        y=['Est. Cost'], x=[total_cost], name='Current Baseline', orientation='h', marker=dict(color='#cbd5e1')
                    ))
                    fig_compare.add_trace(go.Bar(
                        y=['Est. Cost'], x=[total_cost - est_cost_saved], name='Agent Optimized', orientation='h', marker=dict(color='#10b981')
                    ))
                    fig_compare.update_layout(
                        barmode='group',
                        height=140,
                        margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(showgrid=False, visible=False),
                        yaxis=dict(showgrid=False, visible=False),
                        showlegend=True,
                        legend=dict(orientation="h", y=-0.2)
                    )
                    st.plotly_chart(fig_compare, use_container_width=True)

                    # Interactive Demo Button
                    if st.button("🚀 Deploy to Edge Devices", use_container_width=True, type="secondary"):
                        st.toast("Success! Configurations pushed to HVAC and Lighting controllers via IoT gateway.", icon="✅")

    else:
        st.error("Failed to retrieve energy records from the database layer.")


# import streamlit as st
# import pandas as pd
# import plotly.express as px
# from frontend.services.api_client import safe_get, safe_post
# from frontend.components.metrics import render_metric_row
# from frontend.components.status import render_status_banner, render_empty_state

# # Page Configuration - Force wide layout for enterprise feel
# st.set_page_config(page_title="Energy | FacilityOPS", layout="wide", initial_sidebar_state="expanded")

# # --- CUSTOM UI HACK: SaaS Metric Cards ---
# st.markdown("""
# <style>
# /* Style the metric containers to look like enterprise cards */
# div[data-testid="metric-container"] {
#     background-color: #ffffff;
#     border: 1px solid #e2e8f0;
#     padding: 15px 20px;
#     border-radius: 8px;
#     box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
#     border-left: 4px solid #3b82f6; /* Blue accent line */
# }
# /* Style the warning/info boxes */
# div.stAlert {
#     border-radius: 8px;
#     box-shadow: 0 1px 3px rgba(0,0,0,0.1);
# }
# </style>
# """, unsafe_allow_html=True)

# st.title("⚡ Energy Intelligence & Monitoring")
# st.markdown("Monitor utility data, IoT sensor inputs, and agentic module health.")

# # Add the Administrative Sidebar Control
# with st.sidebar:
#     st.markdown("### ⚙️ Module Controls")
#     st.info("Use this tool to simulate an influx of new IoT sensor data.")
    
#     seed_facility = st.selectbox("Target Facility", ["FAC-001", "FAC-002"], key="seed_target")
    
#     if st.button("🔄 Trigger Mock Data Ingestion", use_container_width=True):
#         with st.spinner("Generating time-series data..."):
#             res = safe_post("/energy/seed", params={"facility_id": seed_facility, "days": 7})
#             if res.get("success"):
#                 st.success(f"Ingested {res['data']['records_seeded']} new records.")
#                 st.rerun()
#             else:
#                 st.error("Ingestion pipeline failed.")

# # 1. Module Health Check Integration
# health_data = safe_get("/energy/health")
# is_online = health_data.get("success", False)

# if not is_online:
#     render_status_banner(
#         is_online=False, 
#         custom_message="Energy API is currently unreachable. Displaying cached layout."
#     )
#     st.stop()

# status_info = health_data.get("data", {})
# if status_info.get("status") == "operational":
#     st.success(f"✅ Energy Module Status: Operational | Intelligence Engine: Active")

# st.divider()

# # 2. Facility Selection
# st.markdown("### 🏢 Executive Dashboard")
# selected_facility = st.selectbox("Select Target Facility", ["FAC-001", "FAC-002"], label_visibility="collapsed")

# # 3. Data Retrieval & Visualization
# with st.spinner(f"Fetching telemetry for {selected_facility}..."):
#     records_response = safe_get(f"/energy/records/{selected_facility}?limit=30")
    
#     if records_response.get("success"):
#         records = records_response.get("data", {}).get("records", [])
        
#         if not records:
#             render_empty_state("Energy Consumption", "No data records found for this facility. Awaiting initial IoT ingestion.")
#         else:
#             df = pd.DataFrame(records)
            
#             # --- DATA PREP ---
#             df['timestamp'] = pd.to_datetime(df['timestamp'])
#             df = df.sort_values('timestamp')
            
#             # (Emergency Fix): If your backend doesn't split energy types, we calculate realistic splits 
#             # here in the frontend to make the charts look enterprise-grade for the demo.
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
#             kpi2.metric("Peak Demand", f"{peak_kw:,.1f} kW", delta="Stable", delta_color="off")
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
#                 fig_donut = px.pie(donut_data, values='Value', names='Category', hole=0.6,
#                                    color_discrete_sequence=['#3b82f6', '#10b981', '#f59e0b'])
#                 fig_donut.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=True, legend=dict(orientation="h", y=-0.1))
#                 st.plotly_chart(fig_donut, use_container_width=True)

#             with col_chart2:
#                 st.markdown("**30-Day Telemetry Trend**")
#                 fig_area = px.area(df, x='timestamp', y=['hvac_kwh', 'lighting_kwh', 'equipment_kwh'],
#                                    labels={'value': 'kWh', 'timestamp': 'Date', 'variable': 'System'},
#                                    color_discrete_map={'hvac_kwh': '#3b82f6', 'lighting_kwh': '#10b981', 'equipment_kwh': '#f59e0b'})
#                 fig_area.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title=None)
#                 st.plotly_chart(fig_area, use_container_width=True)

#             st.markdown("<br>", unsafe_allow_html=True)
#             st.markdown("**Hourly Consumption Heatmap (Agent View)**")
            
#             # Extract hour and day for the heatmap
#             df['hour'] = df['timestamp'].dt.hour
#             df['day'] = df['timestamp'].dt.day_name()
            
#             # Create a matrix of Day vs Hour
#             heatmap_data = df.pivot_table(index='day', columns='hour', values='energy_kwh', aggfunc='mean')
            
#             # Reorder days to look professional (Monday -> Sunday)
#             days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
#             heatmap_data = heatmap_data.reindex(days_order)

#             fig_heat = px.imshow(heatmap_data, text_auto=False, aspect="auto", 
#                                  color_continuous_scale="Blues",
#                                  labels=dict(color="kWh", x="Hour of Day", y="Day of Week"))
#             fig_heat.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=250)
#             st.plotly_chart(fig_heat, use_container_width=True)

#             st.divider()

#             # --- AGENTIC INTELLIGENCE (NEW: WHAT-IF SIMULATOR) ---
#             st.markdown("### 🤖 Agentic Intelligence & Optimization")
            
#             col_agent1, col_agent2 = st.columns([1, 1])
            
#             with col_agent1:
#                 st.markdown("#### Agent Threat Analysis")
#                 st.info("The Energy Agent continuously monitors utility data for peak demand violations and abnormal consumption spikes.")
#                 if st.button("🧠 Run Diagnostics & Anomaly Detection", type="primary", use_container_width=True):
#                     with st.spinner("Agent is analyzing consumption patterns..."):
#                         analysis_response = safe_get(f"/energy/analyze/{selected_facility}?days=7")
                        
#                         if analysis_response.get("success"):
#                             insights = analysis_response.get("data", {})
#                             alerts = insights.get("alerts", [])
#                             recommendations = insights.get("recommendations", [])

#                             # if alerts:
#                             #     st.error(f"⚠️ Agent detected {len(alerts)} anomalies requiring attention.")
#                             #     for alert in alerts:
#                             #         with st.expander(f"[{alert['severity'].upper()}] {alert['type']}"):
#                             #             st.write(f"**Timestamp:** {alert['timestamp']}")
#                             #             st.write(f"**Message:** {alert['message']}")
#                             #             st.caption(f"Source: {alert['source']} | ID: {alert['alert_id']}")
#                             if alerts:
#                                 st.error(f"⚠️ Agent detected {len(alerts)} anomalies requiring attention.")
#                                 for alert in alerts:
#                                     with st.expander(f"[{alert.get('severity', 'INFO').upper()}] {alert.get('type', 'Alert')}"):
#                                         st.write(f"**Timestamp:** {alert.get('timestamp', 'Just now')}")
#                                         st.write(f"**Message:** {alert.get('message', 'No details provided.')}")
#                                         st.caption(f"Source: {alert.get('source', 'Energy Agent')} | ID: {alert.get('alert_id', 'SYS-001')}")
#                             else:
#                                 st.success("✅ Agent analysis complete. Consumption patterns are nominal.")

#                             if recommendations:
#                                 st.markdown("**🛠️ Recommended Actions**")
#                                 for rec in recommendations:
#                                     priority_color = "red" if rec.get('priority') == "High" else "orange" if rec.get('priority') == "Medium" else "green"
#                                     st.markdown(f"- **{rec.get('action')}** (Priority: :{priority_color}[{rec.get('priority', 'Low')}])")
#                         else:
#                             st.error("Agent analysis failed to execute.")

#             # with col_agent2:
#             #     st.markdown("#### What-If Control Simulator")
#             #     st.markdown("Test the agent's proposed optimization parameters before deploying them to the facility.")
#             #     with st.container(border=True):
#             #         hvac_offset = st.slider("HVAC Target Temp Offset (°C)", 0.0, 3.0, 0.5, 0.5, help="Increase AC baseline temp.")
#             #         light_dim = st.slider("Smart Lighting Dimming (%)", 0, 50, 10, 5, help="Reduce perimeter lighting based on daylight.")
                    
#             #         # Math for simulator
#             #         hvac_savings_kwh = hvac_offset * 0.06 * df['hvac_kwh'].sum()
#             #         light_savings_kwh = (light_dim / 100.0) * df['lighting_kwh'].sum()
#             #         total_saved = hvac_savings_kwh + light_savings_kwh
                    
#             #         sc1, sc2 = st.columns(2)
#             #         sc1.metric("Projected 30-Day Savings", f"-{total_saved:,.0f} kWh", delta="Optimized")
#             #         sc2.metric("Est. Cost Avoidance", f"${total_saved * 0.12:,.2f}", delta="Added to Budget", delta_color="normal")

#             # ... (Inside your existing code, replace the col_agent2 block) ...
#             with col_agent2:
#                 import plotly.graph_objects as go

#                 st.markdown("#### 🎛️ What-If Control Simulator")
#                 st.markdown("<span style='color: #64748b; font-size: 0.9em;'>Adjust parameters to forecast agent-driven optimizations.</span>", unsafe_allow_html=True)
                
#                 with st.container(border=True):
#                     # Keep sliders clean
#                     st.markdown("**Simulate Setpoint Adjustments**")
#                     hvac_offset = st.slider("HVAC Target Temp Offset (°C)", 0.0, 3.0, 1.0, 0.5)
#                     light_dim = st.slider("Smart Lighting Dimming (%)", 0, 50, 15, 5)
                    
#                     # Math for simulator
#                     hvac_savings_kwh = hvac_offset * 0.06 * df['hvac_kwh'].sum()
#                     light_savings_kwh = (light_dim / 100.0) * df['lighting_kwh'].sum()
#                     total_saved = hvac_savings_kwh + light_savings_kwh
#                     est_cost_saved = total_saved * 0.12

#                     st.divider()

#                     # Render a highly visual Plotly Gauge Chart for the outcome
#                     fig_gauge = go.Figure(go.Indicator(
#                         mode = "gauge+number+delta",
#                         value = total_saved,
#                         domain = {'x': [0, 1], 'y': [0, 1]},
#                         title = {'text': "Projected 30-Day Savings (kWh)", 'font': {'size': 16, 'color': '#334155'}},
#                         delta = {'reference': 0, 'increasing': {'color': "#10b981"}},
#                         number = {'font': {'size': 40, 'color': '#10b981'}, 'valueformat': ",.0f"},
#                         gauge = {
#                             'axis': {'range': [None, total_kwh * 0.2], 'tickwidth': 1, 'tickcolor': "#cbd5e1"},
#                             'bar': {'color': "#10b981"},
#                             'bgcolor': "white",
#                             'borderwidth': 0,
#                             'steps': [
#                                 {'range': [0, (total_kwh * 0.2) * 0.5], 'color': '#f1f5f9'},
#                                 {'range': [(total_kwh * 0.2) * 0.5, total_kwh * 0.2], 'color': '#d1fae5'}],
#                         }
#                     ))
#                     fig_gauge.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=10))
#                     st.plotly_chart(fig_gauge, use_container_width=True)

#                     # High-impact summary text
#                     st.markdown(f"""
#                     <div style="background-color: #ecfdf5; padding: 10px; border-radius: 5px; text-align: center; border: 1px solid #34d399;">
#                         <span style="color: #065f46; font-weight: bold; font-size: 1.1em;">
#                             💰 Est. Financial Impact: ${est_cost_saved:,.2f}
#                         </span>
#                     </div>
#                     """, unsafe_allow_html=True)

#     else:
#         st.error("Failed to retrieve energy records from the database layer.")