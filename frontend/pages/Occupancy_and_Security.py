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