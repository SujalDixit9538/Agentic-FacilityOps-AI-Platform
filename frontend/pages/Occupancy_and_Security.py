import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.services.api_client import safe_get, safe_post
# Utilizing your established UI components and theme
from frontend.components.ui import kpi_card, alert_feed
try:
    from frontend.utils.theme import COLORS
except ImportError:
    # Fallback in case theme dict is not universally exposed yet
    COLORS = {'bg': '#F9FAFB', 'text_pri': '#111827', 'surface': '#FFFFFF', 'border': '#E5E7EB'}

# Page Configuration
st.set_page_config(page_title="Occupancy & Security | FacilityOPS", layout="wide")

def inject_theme():
    """Injects styles for consistent, clean minimalist look."""
    st.markdown(f"""
    <style>
        .stApp {{ background-color: {COLORS.get('bg', '#F9FAFB')}; color: {COLORS.get('text_pri', '#111827')}; }}
        h1, h2, h3, h4 {{ color: {COLORS.get('text_pri', '#111827')} !important; font-weight: 600 !important; }}
        .stButton > button {{ border-radius: 8px; border: 1px solid {COLORS.get('border', '#E5E7EB')}; background-color: {COLORS.get('surface', '#FFFFFF')}; color: {COLORS.get('text_pri', '#111827')}; }}
        .stSelectbox > div {{ background-color: {COLORS.get('surface', '#FFFFFF')}; }}
        .stMarkdown {{ color: {COLORS.get('text_pri', '#111827')}; }}
        
        /* Enforce minimalist design standard */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        /* AI Desk UI */
        .ai-desk {{ background-color: #0F172A; padding: 20px; border-radius: 12px; color: #F8FAFC; border: 1px solid #1E293B; height: 100%; }}
        .ai-chip {{ background-color: #1E293B; border-left: 3px solid #38BDF8; padding: 10px; margin-bottom: 8px; border-radius: 6px; font-size: 0.85rem; }}
        .ai-chip-high {{ border-left-color: #EF4444; }}
    </style>
    """, unsafe_allow_html=True)

inject_theme()

# ---------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Module Controls")
    seed_facility = st.selectbox("Target Facility", ["FAC-001", "FAC-002"], key="occ_seed_target")
    
    if st.button("🔄 Refresh Data Ingestion", use_container_width=True):
        with st.spinner("Provisioning telemetry..."):
            safe_post("/occupancy/seed", params={"facility_id": seed_facility, "days": 7})
            st.rerun()

# ---------------------------------------------------------
# Header & API Retrieval
# ---------------------------------------------------------
st.title(f"Occupancy & Security Intelligence")
selected_facility = seed_facility

dashboard_res = safe_get(f"/occupancy/dashboard/{selected_facility}")
data = dashboard_res.get("data", {}) if dashboard_res.get("success") else {}

summary = data.get("summary", {})
zones = data.get("zones", [])
raw_alerts = data.get("alerts", [])

sec_res = safe_get(f"/occupancy/security/{selected_facility}")
sec_events = sec_res.get("data", {}).get("events", []) if sec_res.get("success") else []

# ---------------------------------------------------------
# KPI Ribbon
# ---------------------------------------------------------
total_occupants = summary.get("total_occupants", 0)
utilization_pct = summary.get("utilization_percent", 0)
overcrowded_count = summary.get("overcrowded_zones", 0)
active_alerts_count = len(raw_alerts)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    kpi_card("Total Occupants", str(total_occupants), icon="👥")
with kpi2:
    kpi_card("Facility Utilization", f"{utilization_pct}%", status="warning" if utilization_pct > 80 else "good")
with kpi3:
    kpi_card("Overcrowded Zones", str(overcrowded_count), status="critical" if overcrowded_count > 0 else "good")
with kpi4:
    kpi_card("Active Alerts", str(active_alerts_count), status="critical" if active_alerts_count > 0 else "good")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Main View: 70/30 Spatial & Operations Split
# ---------------------------------------------------------
col_map, col_desk = st.columns([7, 3])

# LEFT COLUMN: 2D Spatial Vector Heatmap
with col_map:
    st.markdown("### 🗺️ Live Spatial Occupancy Map")
    if zones:
        fig = go.Figure()

        for zone in zones:
            x = zone.get("x_position", 0)
            y = zone.get("y_position", 0)
            width = zone.get("width", 2)
            height = zone.get("height", 1.5)
            util = zone.get("utilization_percent", 0)
            name = zone.get("zone_name", "Unknown")
            status = zone.get("status", "Normal")

            # Semantic colors based on utilization
            if util > 90 or status.lower() == "overcrowded":
                fill_color = "rgba(239, 68, 68, 0.85)"
                border_color = "#991B1B"
            elif util > 60:
                fill_color = "rgba(245, 158, 11, 0.85)"
                border_color = "#B45309"
            else:
                fill_color = "rgba(16, 185, 129, 0.85)"
                border_color = "#047857"

            fig.add_shape(
                type="rect", x0=x, y0=y, x1=x + width, y1=y + height,
                line=dict(color=border_color, width=2),
                fillcolor=fill_color, layer="below"
            )

            hover_text = f"<b>{name}</b><br>Occupancy: {zone.get('occupancy', 0)} / {zone.get('capacity', 0)}<br>Utilization: {util}%"
            
            fig.add_trace(go.Scatter(
                x=[x + width / 2], y=[y + height / 2],
                text=[f"<b>{name}</b>"], mode="text",
                hoverinfo="text", hovertext=[hover_text],
                textfont=dict(color="#FFFFFF", size=11),
                showlegend=False
            ))

        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=400,
            plot_bgcolor=COLORS.get('surface', '#FFFFFF'),
            paper_bgcolor=COLORS.get('surface', '#FFFFFF'),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No spatial coordinates available to map.")

# RIGHT COLUMN: AI Operations Desk
with col_desk:
    st.markdown(
        """
        <div class="ai-desk">
            <div style="border-bottom: 1px solid #334155; padding-bottom: 10px; margin-bottom: 15px;">
                <span style="font-weight: 700; font-size: 1.1rem;">AI Operations Desk</span><br>
                <span style="font-size: 0.8rem; color: #94A3B8;">Occupancy Agent Telemetry</span>
            </div>
        """, unsafe_allow_html=True
    )
    
    if st.button("⚡ Run Facility Inference", use_container_width=True):
        with st.spinner("Analyzing..."):
            analysis = safe_get(f"/occupancy/analyze/{selected_facility}")
            if analysis.get("success"):
                st.session_state[f"occ_ai_{selected_facility}"] = analysis.get("data", {})

    ai_data = st.session_state.get(f"occ_ai_{selected_facility}")
    
    if ai_data:
        recs = ai_data.get("recommendations", [])
        if recs:
            for rec in recs:
                is_high = rec.get("priority", "").lower() == "high"
                chip_cls = "ai-chip ai-chip-high" if is_high else "ai-chip"
                st.markdown(
                    f"""
                    <div class="{chip_cls}">
                        <div style="font-weight: 600; color: {'#FCA5A5' if is_high else '#7DD3FC'};">
                            [{rec.get('priority', 'Routine').upper()}] {rec.get('trigger', 'Signal')}
                        </div>
                        <div style="margin-top: 4px;">{rec.get('action', '')}</div>
                    </div>
                    """, unsafe_allow_html=True
                )
        else:
            st.markdown("<div style='color: #94A3B8; font-size: 0.9rem;'>No immediate operational directives required.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color: #94A3B8; font-size: 0.85rem; padding-top: 20px;'>Trigger inference to map utilization and hand off restricted-zone risk.</div>", unsafe_allow_html=True)
        
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Secondary View: Temporal Analytics & Security Feed
# ---------------------------------------------------------
col_temporal, col_sec = st.columns([6, 4])

with col_temporal:
    st.markdown("### 📈 Utilization Trend")
    time_range = st.radio("Time Horizon", ["24H", "7D", "30D"], horizontal=True, label_visibility="collapsed")
    
    analytics = data.get("zone_analytics", [])
    if analytics:
        df_temporal = pd.DataFrame(analytics)
        if "timestamp" not in df_temporal.columns:
            df_temporal["timestamp"] = pd.date_range(end=pd.Timestamp.now(), periods=len(df_temporal), freq="h")

        fig_temp = px.area(
            df_temporal, 
            x="timestamp", 
            y="utilization_percent" if "utilization_percent" in df_temporal.columns else df_temporal.columns[1],
            template="plotly_white"
        )
        fig_temp.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=300,
            xaxis_title=None,
            yaxis_title="Avg Utilization (%)",
            plot_bgcolor=COLORS.get('surface', '#FFFFFF'),
            paper_bgcolor=COLORS.get('surface', '#FFFFFF'),
        )
        st.plotly_chart(fig_temp, use_container_width=True)
    else:
        st.info("No temporal history recorded.")

with col_sec:
    st.markdown("### 🔒 Prioritized Security Incidents")
    
    formatted_alerts = []
    
    # Process standard occupancy alerts
    for al in raw_alerts:
        formatted_alerts.append({
            "severity": al.get("severity", "medium").lower(),
            "title": f"Occupancy Alert - {al.get('zone_name', 'Unknown Zone')}",
            "description": al.get("message", "Threshold exceeded."),
            "facility": selected_facility
        })
        
    # Process physical security events
    for sec in sec_events:
        formatted_alerts.append({
            "severity": sec.get("severity", "high").lower(),
            "title": f"Security - {sec.get('event_type', 'Event')} in {sec.get('location', 'Facility')}",
            "description": sec.get("description", sec.get("message", "Security breach logged.")),
            "facility": selected_facility
        })
        
    if formatted_alerts:
        # Utilize your UI component to render the feed cleanly
        alert_feed(formatted_alerts)
    else:
        st.info("No active security incidents or alerts.")

































# import sys
# from datetime import datetime
# from pathlib import Path

# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# import streamlit as st

# # Setup Root Directory Path
# root_dir = str(Path(__file__).parent.parent.parent.absolute())
# if root_dir not in sys.path:
#     sys.path.insert(0, root_dir)

# from frontend.services.api_client import safe_get, safe_post
# from frontend.components.status import render_status_banner, render_empty_state

# # ---------------------------------------------------------
# # Page Configuration & Modern SOC Custom CSS
# # ---------------------------------------------------------
# st.set_page_config(
#     page_title="Occupancy & Security Intelligence | FacilityOPS",
#     layout="wide",
#     initial_sidebar_state="collapsed",
# )

# st.markdown(
#     """
#     <style>
#     /* Global Clean Font & Background */
#     @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
#     html, body, [class*="css"] {
#         font-family: 'Inter', sans-serif;
#     }
    
#     /* Remove default Streamlit padding and watermarks */
#     #MainMenu {visibility: hidden;}
#     footer {visibility: hidden;}
#     header {visibility: hidden;}
#     .block-container {
#         padding-top: 1.5rem;
#         padding-bottom: 2rem;
#         padding-left: 2rem;
#         padding-right: 2rem;
#         max-width: 100%;
#     }

#     /* Top Navigation Bar */
#     .top-navbar {
#         display: flex;
#         justify-content: space-between;
#         align-items: center;
#         background: #FFFFFF;
#         padding: 14px 24px;
#         border-radius: 12px;
#         border: 1px solid #E5E7EB;
#         margin-bottom: 1.25rem;
#         box-shadow: 0 1px 3px rgba(0,0,0,0.04);
#     }
#     .top-title {
#         font-size: 1.25rem;
#         font-weight: 700;
#         color: #111827;
#         margin: 0;
#     }
#     .top-subtitle {
#         font-size: 0.825rem;
#         color: #6B7280;
#         margin: 0;
#     }
#     .live-badge {
#         display: inline-flex;
#         align-items: center;
#         gap: 6px;
#         background: #ECFDF5;
#         color: #059669;
#         font-weight: 600;
#         font-size: 0.775rem;
#         padding: 4px 10px;
#         border-radius: 9999px;
#         border: 1px solid #A7F3D0;
#     }
#     .live-dot {
#         width: 8px;
#         height: 8px;
#         background-color: #10B981;
#         border-radius: 50%;
#         box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3);
#     }

#     /* Metric KPI Cards */
#     .kpi-container {
#         display: grid;
#         grid-template-columns: repeat(4, 1fr);
#         gap: 16px;
#         margin-bottom: 1.5rem;
#     }
#     .kpi-card {
#         background: #FFFFFF;
#         padding: 16px 20px;
#         border-radius: 12px;
#         border: 1px solid #E5E7EB;
#         box-shadow: 0 1px 3px rgba(0,0,0,0.03);
#     }
#     .kpi-label {
#         font-size: 0.8rem;
#         text-transform: uppercase;
#         letter-spacing: 0.05em;
#         font-weight: 600;
#         color: #6B7280;
#         margin-bottom: 6px;
#     }
#     .kpi-value {
#         font-size: 1.75rem;
#         font-weight: 700;
#         color: #111827;
#         line-height: 1.1;
#     }
#     .kpi-alert {
#         color: #DC2626 !important;
#     }

#     /* General Panel Container */
#     .ops-card {
#         background: #FFFFFF;
#         border-radius: 12px;
#         border: 1px solid #E5E7EB;
#         padding: 20px;
#         height: 100%;
#         box-shadow: 0 1px 3px rgba(0,0,0,0.03);
#     }
#     .ops-title {
#         font-size: 1rem;
#         font-weight: 600;
#         color: #111827;
#         margin-bottom: 12px;
#         display: flex;
#         align-items: center;
#         justify-content: space-between;
#     }

#     /* AI Desk Specific Styling */
#     .ai-desk-container {
#         background: #0F172A;
#         border-radius: 12px;
#         color: #F8FAFC;
#         padding: 20px;
#         height: 100%;
#         border: 1px solid #1E293B;
#     }
#     .ai-desk-header {
#         display: flex;
#         justify-content: space-between;
#         align-items: center;
#         border-bottom: 1px solid #334155;
#         padding-bottom: 12px;
#         margin-bottom: 14px;
#     }
#     .ai-desk-badge {
#         font-size: 0.75rem;
#         font-weight: 600;
#         padding: 2px 8px;
#         border-radius: 6px;
#         background: #1E293B;
#         color: #38BDF8;
#         border: 1px solid #0284C7;
#     }
#     .action-chip {
#         background: #1E293B;
#         border-left: 3px solid #38BDF8;
#         border-radius: 6px;
#         padding: 10px 12px;
#         font-size: 0.825rem;
#         margin-bottom: 8px;
#         color: #E2E8F0;
#     }
#     .action-chip-high {
#         border-left-color: #EF4444;
#     }

#     /* Incident Feed Cards */
#     .incident-item {
#         background: #FFFFFF;
#         border: 1px solid #E5E7EB;
#         border-left: 4px solid #3B82F6;
#         border-radius: 8px;
#         padding: 12px 14px;
#         margin-bottom: 8px;
#         transition: transform 0.1s ease;
#     }
#     .incident-high {
#         border-left-color: #DC2626;
#         background: #FEF2F2;
#     }
#     .incident-warn {
#         border-left-color: #F59E0B;
#         background: #FFFBEB;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# # ---------------------------------------------------------
# # Top Navigation & Header Controls
# # ---------------------------------------------------------
# header_col1, header_col2, header_col3 = st.columns([3.5, 1.2, 1.3])

# with header_col1:
#     st.markdown(
#         f"""
#         <div style="display: flex; align-items: center; gap: 14px;">
#             <div>
#                 <h1 class="top-title">Facility Operations Center</h1>
#                 <p class="top-subtitle">Real-time spatial occupancy intelligence & physical security telemetry</p>
#             </div>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )

# with header_col2:
#     selected_facility = st.selectbox(
#         "Facility",
#         ["FAC-001", "FAC-002"],
#         label_visibility="collapsed",
#         key="selected_facility_ctrl",
#     )

# with header_col3:
#     timestamp_str = datetime.utcnow().strftime("%H:%M:%S UTC")
#     st.markdown(
#         f"""
#         <div style="display: flex; justify-content: flex-end; align-items: center; height: 100%;">
#             <div class="live-badge">
#                 <div class="live-dot"></div>
#                 <span>LIVE • {timestamp_str}</span>
#             </div>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )

# # ---------------------------------------------------------
# # API Data Retrieval
# # ---------------------------------------------------------
# dashboard_res = safe_get(f"/occupancy/dashboard/{selected_facility}")
# data = dashboard_res.get("data", {}) if dashboard_res.get("success") else {}

# summary = data.get("summary", {})
# zones = data.get("zones", [])
# alerts = data.get("alerts", [])

# # Fetch Security Telemetry
# sec_res = safe_get(f"/occupancy/security/{selected_facility}")
# sec_events = sec_res.get("data", {}).get("events", []) if sec_res.get("success") else []

# # ---------------------------------------------------------
# # KPI Ribbon
# # ---------------------------------------------------------
# total_occupants = summary.get("total_occupants", 0)
# utilization_pct = summary.get("utilization_percent", 0)
# overcrowded_count = summary.get("overcrowded_zones", 0)
# active_alerts_count = len(alerts)

# overcrowded_cls = "kpi-alert" if overcrowded_count > 0 else ""
# alert_cls = "kpi-alert" if active_alerts_count > 0 else ""

# st.markdown(
#     f"""
#     <div class="kpi-container">
#         <div class="kpi-card">
#             <div class="kpi-label">Total Occupants</div>
#             <div class="kpi-value">{total_occupants:,}</div>
#         </div>
#         <div class="kpi-card">
#             <div class="kpi-label">Facility Utilization</div>
#             <div class="kpi-value">{utilization_pct}%</div>
#         </div>
#         <div class="kpi-card">
#             <div class="kpi-label">Overcrowded Zones</div>
#             <div class="kpi-value {overcrowded_cls}">{overcrowded_count}</div>
#         </div>
#         <div class="kpi-card">
#             <div class="kpi-label">Active Alerts</div>
#             <div class="kpi-value {alert_cls}">{active_alerts_count}</div>
#         </div>
#     </div>
#     """,
#     unsafe_allow_html=True,
# )

# # ---------------------------------------------------------
# # Main View: 70 / 30 Spatial & Operations Split
# # ---------------------------------------------------------
# col_map, col_desk = st.columns([7, 3])

# # LEFT COLUMN: 2D Spatial Vector Heatmap
# with col_map:
#     st.markdown('<div class="ops-card">', unsafe_allow_html=True)
#     map_head_left, map_head_right = st.columns([4, 2])
#     with map_head_left:
#         st.markdown(
#             '<div class="ops-title">Live 2D Spatial Occupancy</div>',
#             unsafe_allow_html=True,
#         )
#     with map_head_right:
#         floor_filter = st.selectbox(
#             "Floor Filter",
#             options=["All Floors"] + sorted(list({z.get("floor", 1) for z in zones})),
#             label_visibility="collapsed",
#             key="floor_filter_ctrl",
#         )

#     filtered_zones = zones
#     if floor_filter != "All Floors":
#         filtered_zones = [z for z in zones if z.get("floor") == floor_filter]

#     if filtered_zones:
#         fig = go.Figure()

#         # Build clean rectangle polygons using coordinates
#         for zone in filtered_zones:
#             x = zone.get("x_position", 0)
#             y = zone.get("y_position", 0)
#             width = zone.get("width", 1.8)
#             height = zone.get("height", 1.4)
#             util = zone.get("utilization_percent", 0)
#             occ = zone.get("occupancy", 0)
#             cap = zone.get("capacity", 0)
#             name = zone.get("zone_name", "Unknown Zone")
#             status = zone.get("status", "Normal")
#             z_type = zone.get("zone_type", "General")

#             # Determine semantic fill color based on utilization
#             # UNDERUTILIZED: < 40% (green)
#             # NORMAL: 40% <= utilization < 80% (neutral/blue)
#             # HIGHLY UTILIZED: 80% <= utilization < 100% (amber/orange)
#             # OVERCROWDED: >= 100% (red)
#             if util >= 100 or status.lower() == "overcrowded":
#                 fill_color = "rgba(239, 68, 68, 0.85)"  # Red
#                 border_color = "#991B1B"
#             elif util >= 80:
#                 fill_color = "rgba(245, 158, 11, 0.85)"  # Amber/Orange
#                 border_color = "#B45309"
#             elif util >= 40:
#                 fill_color = "rgba(59, 130, 246, 0.65)"  # Neutral/Blue
#                 border_color = "#1D4ED8"
#             else:
#                 fill_color = "rgba(16, 185, 129, 0.85)"  # Green
#                 border_color = "#047857"

#             border_width = 2


#             # Draw zone boundary
#             fig.add_shape(
#                 type="rect",
#                 x0=x,
#                 y0=y,
#                 x1=x + width,
#                 y1=y + height,
#                 line=dict(color=border_color, width=border_width),
#                 fillcolor=fill_color,
#                 layer="below",
#             )

#             # Zone Label & Hover Data
#             hover_text = (
#                 f"<b>{name}</b> ({z_type})<br>"
#                 f"Status: {status}<br>"
#                 f"Occupancy: {occ} / {cap}<br>"
#                 f"Utilization: {util}%"
#             )

#             fig.add_trace(
#                 go.Scatter(
#                     x=[x + width / 2],
#                     y=[y + height / 2],
#                     text=[f"<b>{name}</b><br>{util}%"],
#                     mode="text",
#                     hoverinfo="text",
#                     hovertext=[hover_text],
#                     textfont=dict(color="#FFFFFF", size=11, family="Inter"),
#                     showlegend=False,
#                 )
#             )

#         fig.update_layout(
#             margin=dict(l=10, r=10, t=10, b=10),
#             height=430,
#             plot_bgcolor="#F8FAFC",
#             paper_bgcolor="#FFFFFF",
#             xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
#             yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
#             hoverlabel=dict(bgcolor="#0F172A", font_size=12, font_family="Inter"),
#         )
#         st.plotly_chart(fig, use_container_width=True)
#     else:
#         render_empty_state("No spatial zone coordinates available for this facility.")

#     st.markdown("</div>", unsafe_allow_html=True)

# # RIGHT COLUMN: AI Operations Desk
# with col_desk:
#     st.markdown(
#         f"""
#         <div class="ai-desk-container">
#             <div class="ai-desk-header">
#                 <div>
#                     <div style="font-weight: 700; font-size: 0.95rem; color: #FFFFFF;">AI Operations Desk</div>
#                     <div style="font-size: 0.75rem; color: #94A3B8;">Autonomous Reasoning Agent</div>
#                 </div>
#                 <div class="ai-desk-badge">ACTIVE MONITORING</div>
#             </div>
#         """,
#         unsafe_allow_html=True,
#     )

#     if st.button("Run Facility Analysis", use_container_width=True):
#         with st.spinner("Invoking Occupancy Agent..."):
#             analysis = safe_get(f"/occupancy/analyze/{selected_facility}")
#             if analysis.get("success"):
#                 st.session_state[f"cached_ai_{selected_facility}"] = analysis.get("data", {})

#     ai_data = st.session_state.get(f"cached_ai_{selected_facility}")

#     if ai_data:
#         facility_status = ai_data.get("status", "Optimal")
#         status_color = "#EF4444" if facility_status.lower() == "critical" else "#10B981"

#         st.markdown(
#             f"""
#             <div style="margin-top: 10px; margin-bottom: 12px;">
#                 <div style="font-size: 0.775rem; color: #94A3B8; text-transform: uppercase;">Facility Assessment</div>
#                 <div style="font-size: 1.1rem; font-weight: 700; color: {status_color};">{facility_status.upper()}</div>
#             </div>
#             <div style="font-size: 0.775rem; color: #94A3B8; text-transform: uppercase; margin-bottom: 6px;">Recommended Directives</div>
#             """,
#             unsafe_allow_html=True,
#         )

#         recs = ai_data.get("recommendations", [])
#         if recs:
#             for rec in recs:
#                 is_high = rec.get("priority", "").lower() == "high"
#                 high_cls = "action-chip-high" if is_high else ""
#                 st.markdown(
#                     f"""
#                     <div class="action-chip {high_cls}">
#                         <div style="font-weight: 600; font-size: 0.75rem; color: {'#FCA5A5' if is_high else '#7DD3FC'};">
#                             [{rec.get('priority', 'Routine').upper()}] {rec.get('trigger', 'Operational Signal')}
#                         </div>
#                         <div style="margin-top: 2px;">{rec.get('action', '')}</div>
#                     </div>
#                     """,
#                     unsafe_allow_html=True,
#                 )
#         else:
#             st.markdown(
#                 '<div style="font-size: 0.8rem; color: #94A3B8;">All monitored zones within operational limits. No action required.</div>',
#                 unsafe_allow_html=True,
#             )
#     else:
#         st.markdown(
#             """
#             <div style="padding: 24px 0; text-align: center; color: #94A3B8; font-size: 0.825rem;">
#                 Click <b>Run Facility Analysis</b> to synthesize live zone telemetry into operational directives.
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )

#     st.markdown("</div>", unsafe_allow_html=True)

# st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

# # ---------------------------------------------------------
# # Secondary View: Temporal Analytics & Prioritized Security Feed
# # ---------------------------------------------------------
# col_temporal, col_sec = st.columns([6, 4])

# with col_temporal:
#     st.markdown('<div class="ops-card">', unsafe_allow_html=True)
#     temp_head_left, temp_head_right = st.columns([3, 3])
#     with temp_head_left:
#         st.markdown(
#             '<div class="ops-title">Occupancy & Utilization Trend</div>',
#             unsafe_allow_html=True,
#         )
#     with temp_head_right:
#         time_range = st.radio(
#             "Time Horizon",
#             options=["24H", "7D", "30D"],
#             horizontal=True,
#             index=0,
#             label_visibility="collapsed",
#             key="time_horizon_ctrl",
#         )

#     # Fetch zone analytics or generate temporal projection
#         # Temporal Analytics
#         # Filter trend data by selected range
#         trend_data = data.get("trend", [])
#         if trend_data:
#             df_temporal = pd.DataFrame(trend_data)
#             df_temporal["timestamp"] = pd.to_datetime(df_temporal["timestamp"]).dt.tz_localize(None)
            
#             now = pd.Timestamp.utcnow().tz_localize(None)
#             if time_range == "24H":
#                 start_date = now - pd.Timedelta(hours=24)
#             elif time_range == "7D":
#                 start_date = now - pd.Timedelta(days=7)
#             elif time_range == "30D":
#                 start_date = now - pd.Timedelta(days=30)
            
#             df_temporal = df_temporal[df_temporal["timestamp"] >= start_date]

#             if not df_temporal.empty:
#                 fig_temp = px.area(
#                     df_temporal,
#                     x="timestamp",
#                     y="utilization_percent",
#                     template="plotly_white",
#                     color_discrete_sequence=["#3B82F6"],
#                 )
#                 fig_temp.update_layout(
#                     margin=dict(l=10, r=10, t=10, b=10),
#                     height=260,
#                     xaxis_title=None,
#                     yaxis_title="Utilization (%)",
#                     plot_bgcolor="#FFFFFF",
#                     yaxis=dict(gridcolor="#F3F4F6", range=[0, 100]),
#                     xaxis=dict(gridcolor="#F3F4F6"),
#                 )
#                 st.plotly_chart(fig_temp, use_container_width=True)
#             else:
#                 render_empty_state("Insufficient historical data for selected range.")
#         else:
#             render_empty_state("No temporal history recorded for the selected facility.")


#     st.markdown("</div>", unsafe_allow_html=True)

# with col_sec:
#     st.markdown('<div class="ops-card">', unsafe_allow_html=True)
#     st.markdown(
#         '<div class="ops-title">Security Incident Feed</div>',
#         unsafe_allow_html=True,
#     )
#     if sec_events:
#         for event in sec_events[:5]:
#             severity = event.get("severity", "Low").lower()
#             event_type = event.get("event_type", "Security Event")
#             location = event.get("location", event.get("zone_name", "Perimeter"))
#             timestamp = event.get("timestamp", "Just now")
#             desc = event.get("description", event.get("message", "Signal logged."))

#             incident_cls = (
#                 "incident-high"
#                 if severity in ["high", "critical"]
#                 else "incident-warn"
#                 if severity in ["medium", "warning"]
#                 else ""
#             )

#             st.markdown(
#                 f"""
#                 <div class="incident-item {incident_cls}">
#                     <div style="display: flex; justify-content: space-between; font-size: 0.775rem; font-weight: 600;">
#                         <span>{event_type} • {location}</span>
#                         <span style="color: #6B7280;">{timestamp[-8:] if len(timestamp) >= 8 else timestamp}</span>
#                     </div>
#                     <div style="font-size: 0.8rem; color: #374151; margin-top: 3px;">
#                         {desc}
#                     </div>
#                 </div>
#                 """,
#                 unsafe_allow_html=True,
#             )
#     else:
#         render_empty_state("No active security incidents detected.")

#     st.markdown("</div>", unsafe_allow_html=True)
































# import sys
# from pathlib import Path
# import streamlit as st

# root_dir = str(Path(__file__).parent.parent.parent.absolute())
# if root_dir not in sys.path:
#     sys.path.insert(0, root_dir)

# import pandas as pd
# from frontend.services.api_client import safe_get, safe_post
# from frontend.components.status import render_status_banner, render_empty_state


# # Page Configuration
# st.set_page_config(page_title="Occupancy & Security Intelligence | FacilityOPS", layout="wide")

# # Sidebar
# with st.sidebar:
#     st.markdown("### ⚙️ Module Controls")
#     seed_facility = st.selectbox("Target Facility", ["FAC-001", "FAC-002"], key="occ_seed_target")
#     selected_facility = st.session_state.get('occ_seed_target', 'FAC-001')
#     if st.button("🔄 Refresh Data Ingestion", use_container_width=True):
#         with st.spinner("Provisioning data..."):
#             safe_post("/occupancy/seed", params={"facility_id": seed_facility, "days": 7})
#             st.rerun()

# from datetime import datetime
# import plotly.express as px
# from frontend.services.api_client import safe_get, safe_post
# from frontend.components.status import render_status_banner, render_empty_state

# # Professional Styling
# st.set_page_config(page_title="Occupancy & Security Intelligence | FacilityOPS", layout="wide")

# st.markdown("""
# <style>
#     .kpi-card { background-color: #ffffff; border-radius: 10px; padding: 20px; border: 1px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
#     .kpi-value { font-size: 28px; font-weight: 700; color: #212529; }
#     .kpi-label { font-size: 13px; color: #495057; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }
#     .alert-card { padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid; color: #212529; font-weight: 500; }
#     .alert-high { border-left-color: #dc3545; background-color: #f8d7da; color: #721c24; }
#     .alert-med { border-left-color: #fd7e14; background-color: #fff3cd; color: #856404; }
# </style>
# """, unsafe_allow_html=True)

# # 1. Header
# st.title("Occupancy & Security")
# st.markdown(f"**Facility:** {st.session_state.get('occ_seed_target', 'FAC-001')} | **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
# st.divider()

# # API Data Fetch
# dashboard_data = safe_get(f"/occupancy/dashboard/{selected_facility}")
# success = dashboard_data.get("success", False)
# data = dashboard_data.get("data", {})

# if not success:
#     st.error("Failed to load dashboard data.")
#     st.stop()

# summary = data.get("summary", {})

# # 2. Top KPI row
# cols = st.columns(4)
# cols[0].markdown(f'<div class="kpi-card"><div class="kpi-label">Total Occupants</div><div class="kpi-value">{summary.get("total_occupants", 0)} / {summary.get("total_capacity", 0)}</div></div>', unsafe_allow_html=True)
# cols[1].markdown(f'<div class="kpi-card"><div class="kpi-label">Utilization</div><div class="kpi-value">{summary.get("utilization_percent", 0)}%</div></div>', unsafe_allow_html=True)
# cols[2].markdown(f'<div class="kpi-card"><div class="kpi-label">Overcrowded Zones</div><div class="kpi-value" style="color: {"red" if summary.get("overcrowded_zones", 0) > 0 else "black"}">{summary.get("overcrowded_zones", 0)}</div></div>', unsafe_allow_html=True)
# cols[3].markdown(f'<div class="kpi-card"><div class="kpi-label">Active Alerts</div><div class="kpi-value">{len(data.get("alerts", []))}</div></div>', unsafe_allow_html=True)
# st.divider()


# # 3. Primary Spatial Occupancy Map
# st.markdown("### 🗺️ Live Occupancy Heatmap")
# zones = data.get("zones", [])
# if zones:
#     df_zones = pd.DataFrame(zones)
#     fig = px.scatter(df_zones, x="x_position", y="y_position", color="utilization_percent", 
#                      size="capacity", hover_name="zone_name", color_continuous_scale="RdYlGn_r")
#     fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
#     st.plotly_chart(fig, use_container_width=True)
# else:
#     st.info("No zone data available.")




# # 4. Space & Room Utilization
# c1, c2 = st.columns(2)
# with c1:
#     st.markdown("### 📊 Space Utilization Analytics")
#     analytics = data.get("zone_analytics", [])
#     if analytics:
#         df_an = pd.DataFrame(analytics)
#         st.dataframe(df_an, use_container_width=True)
#     else:
#         st.info("No analytics data.")
# with c2:
#     st.markdown("### 🚪 Room Utilization")
#     rooms = data.get("room_utilization", [])
#     if rooms:
#         df_rooms = pd.DataFrame(rooms)
#         st.dataframe(df_rooms, use_container_width=True)
#     else:
#         st.info("No room data.")

# # 6. Occupancy Alerts
# st.markdown("### ⚠️ Occupancy Alerts")
# alerts = data.get("alerts", [])
# if alerts:
#     for al in alerts:
#         css_class = "alert-high" if al['severity'] == 'High' else "alert-med"
#         st.markdown(f'<div class="alert-card {css_class}"><strong>{al["severity"]} Alert</strong><br>{al["zone_name"]}: {al["message"]}</div>', unsafe_allow_html=True)
# else:
#     st.info("No active occupancy alerts.")

# # 7. Security Operations
# st.markdown("### 🔒 Security Operations")
# sec_data = safe_get(f"/occupancy/security/{selected_facility}")
# sec_events = sec_data.get("data", {}).get("events", [])
# if sec_events:
#     for event in sec_events:
#         st.write(f"- {event.get('timestamp', 'N/A')} | {event.get('description', 'N/A')}")
# else:
#     st.info("No security events.")


# # 5. AI Operations Desk
# st.markdown("### 🤖 AI Operations Desk")
# analysis = safe_get(f"/occupancy/analyze/{selected_facility}").get("data", {})
# if analysis:
#     col_ai1, col_ai2 = st.columns([1, 1])
#     with col_ai1:
#         st.markdown("#### Facility Status")
#         st.write(f"Status: {analysis.get('status', 'N/A')}")
#         st.write(f"Anomalies: {analysis.get('anomalies_detected', 0)}")
#     with col_ai2:
#         st.markdown("#### Recommended Actions")
#         for rec in analysis.get('recommendations', []):
#             st.write(f"- **{rec['priority']}**: {rec['action']}")
# else:
#     st.info("No AI analysis available.")