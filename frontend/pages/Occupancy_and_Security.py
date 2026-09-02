import html
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

root_dir = str(Path(__file__).parent.parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.services.api_client import safe_get
from frontend.services.page_data import get_facilities

st.set_page_config(
    page_title="Occupancy & Security Intelligence | FacilityOPS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    :root{--bg:#f4f7fb;--surface:#fff;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--blue:#2563eb;--green:#10b981;--amber:#f59e0b;--red:#ef4444}
    html,body,[class*="css"]{font-family:"Inter",-apple-system,BlinkMacSystemFont,sans-serif}
    .stApp{background:var(--bg);color:var(--ink)}
    #MainMenu,footer,header{visibility:hidden}
    .block-container{max-width:100%;padding:1.15rem 2rem 2.5rem 2rem}
    .hero{background:linear-gradient(135deg,#0f172a 0%,#172554 55%,#0f766e 100%);color:#fff;border-radius:18px;padding:22px 24px;margin-bottom:16px;box-shadow:0 12px 30px rgba(15,23,42,.12)}
    .eyebrow{color:#93c5fd;font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}
    .hero-title{font-size:28px;font-weight:800;margin:2px 0 4px}
    .hero-sub{color:#cbd5e1;font-size:13px;margin:0}
    .live-pill{display:inline-flex;align-items:center;gap:7px;padding:7px 11px;border-radius:999px;background:rgba(16,185,129,.14);border:1px solid rgba(110,231,183,.28);color:#a7f3d0;font-size:11px;font-weight:700}
    .live-dot{width:8px;height:8px;border-radius:50%;background:#34d399;box-shadow:0 0 0 4px rgba(52,211,153,.13)}
    .kpi-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:0 0 16px}
    .kpi{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 17px;min-height:96px;box-shadow:0 3px 10px rgba(15,23,42,.035)}
    .kpi-label{color:var(--muted);font-size:10px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
    .kpi-value{color:var(--ink);font-size:27px;font-weight:800;line-height:1.15;margin-top:8px}
    .kpi-meta{color:var(--muted);font-size:11px;margin-top:5px}
    .kpi-critical{border-top:3px solid var(--red)}.kpi-warning{border-top:3px solid var(--amber)}.kpi-good{border-top:3px solid var(--green)}.kpi-info{border-top:3px solid var(--blue)}
    .panel{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:17px;box-shadow:0 3px 12px rgba(15,23,42,.035);margin-bottom:14px}
    .panel-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px}
    .panel-title{color:var(--ink);font-size:14px;font-weight:800;margin:0}.panel-sub{color:var(--muted);font-size:11px;margin-top:3px}
    .section-label{color:#475569;font-size:10px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;margin:3px 0 9px}
    .legend{display:flex;flex-wrap:wrap;gap:10px;color:var(--muted);font-size:10px;margin:7px 0 0 2px}.legend-item{display:inline-flex;align-items:center;gap:5px}.legend-dot{width:9px;height:9px;border-radius:3px}
    .ai{background:linear-gradient(180deg,#0b1220 0%,#111827 100%);color:#f8fafc;border:1px solid #1e293b;border-radius:16px;padding:17px;min-height:100%;box-shadow:0 8px 24px rgba(15,23,42,.12)}
    .ai-head{display:flex;justify-content:space-between;align-items:center;padding-bottom:12px;border-bottom:1px solid #263244;margin-bottom:12px}.ai-title{font-weight:800;font-size:14px}.ai-sub{color:#94a3b8;font-size:10px;margin-top:2px}
    .ai-badge{color:#7dd3fc;border:1px solid #155e75;background:#0c2b3a;padding:5px 8px;border-radius:999px;font-size:9px;font-weight:800}
    .ai-status{display:flex;justify-content:space-between;align-items:center;padding:10px 11px;background:#111c2e;border-radius:10px;margin-bottom:11px}.ai-status-label{color:#94a3b8;font-size:9px;text-transform:uppercase;letter-spacing:.08em}.ai-status-value{font-size:16px;font-weight:800;margin-top:2px}.ai-metric{text-align:right}
    .ai-chip{background:#111c2e;border:1px solid #243244;border-left:3px solid #38bdf8;border-radius:9px;padding:10px 11px;margin-bottom:8px}.ai-chip.high{border-left-color:#ef4444}.ai-chip .tag{font-size:9px;font-weight:800;color:#7dd3fc;text-transform:uppercase}.ai-chip.high .tag{color:#fca5a5}.ai-chip .body{color:#e2e8f0;font-size:11px;line-height:1.45;margin-top:3px}.ai-note{color:#94a3b8;font-size:11px;line-height:1.5}
    .zone-card{border:1px solid var(--line);border-radius:11px;padding:10px 11px;margin-bottom:8px;background:#fff}.zone-top{display:flex;justify-content:space-between;gap:8px}.zone-name{font-weight:700;font-size:11px;color:var(--ink)}.zone-meta{color:var(--muted);font-size:9px;margin-top:2px}.bar{height:6px;border-radius:999px;background:#e2e8f0;overflow:hidden;margin-top:7px}.bar>div{height:100%;border-radius:999px}.status-pill{display:inline-block;padding:3px 6px;border-radius:999px;font-size:8px;font-weight:800;letter-spacing:.04em}
    .incident{border:1px solid var(--line);border-left:4px solid #94a3b8;border-radius:10px;padding:10px 11px;margin-bottom:8px;background:#fff}.incident.high{border-left-color:#ef4444;background:#fff7f7}.incident.medium{border-left-color:#f59e0b;background:#fffaf0}.incident.low{border-left-color:#10b981}.incident-head{display:flex;justify-content:space-between;gap:10px}.incident-title{font-size:11px;font-weight:800;color:var(--ink)}.incident-time{color:var(--muted);font-size:9px;white-space:nowrap}.incident-body{color:#475569;font-size:10px;line-height:1.45;margin-top:4px}.incident-foot{color:#64748b;font-size:9px;margin-top:5px}
    .detail-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-top:10px}.detail-cell{background:#f8fafc;border:1px solid #e2e8f0;border-radius:9px;padding:9px}.detail-key{color:#64748b;font-size:9px;text-transform:uppercase;letter-spacing:.06em;font-weight:700}.detail-val{color:#0f172a;font-size:13px;font-weight:800;margin-top:3px}
    @media(max-width:900px){.kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.block-container{padding-left:1rem;padding-right:1rem}}
    </style>
    """,
    unsafe_allow_html=True,
)


def esc(value):
    return html.escape(str(value if value is not None else ""))


def num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def status_for(util):
    util = num(util)
    if util > 100:
        return "OVERCROWDED", "#dc2626", "#fee2e2"
    if util >= 80:
        return "HIGH", "#ea580c", "#ffedd5"
    if util >= 40:
        return "MODERATE", "#d97706", "#fef3c7"
    return "LOW", "#059669", "#ecfdf5"


def safe_pct(util):
    return max(0.0, min(100.0, num(util)))


def format_time(value):
    if not value:
        return "—"
    try:
        return pd.to_datetime(value).strftime("%d %b · %H:%M")
    except Exception:
        return str(value)


def build_floorplan(zones):
    """Render a real-zone vector floorplan using the backend's zone set and x/y anchors."""
    fig = go.Figure()
    if not zones:
        return fig
    type_counts = {}
    layout_boxes = []
    for z in zones:
        ztype = str(z.get("zone_type", "common_area"))
        idx = type_counts.get(ztype, 0)
        type_counts[ztype] = idx + 1
        ax, ay = num(z.get("x_position"), .5), num(z.get("y_position"), .5)
        if ztype == "office_floor":
            x0, y0, w, h = .06, .16, .57, .62
        elif ztype == "meeting_room":
            x0, y0, w, h = .68, .16 + idx * .19, .25, .14
        elif ztype == "server_room":
            x0, y0, w, h = .68, .72, .25, .16
        elif ztype == "common_area":
            x0, y0, w, h = .33, .82, .28, .10
        elif ztype == "parking":
            x0, y0, w, h = .06, .82, .23, .10
        else:
            x0, y0, w, h = max(.03, min(.80, ax-.12)), max(.08, min(.82, ay-.08)), .22, .12
        layout_boxes.append((z, x0, y0, w, h))

    fig.add_shape(type="rect", x0=.02, y0=.04, x1=.97, y1=.95, line=dict(color="#cbd5e1", width=2), fillcolor="#f8fafc", layer="below")
    fig.add_shape(type="rect", x0=.63, y0=.10, x1=.65, y1=.86, line=dict(color="#e2e8f0", width=1), fillcolor="#eef2f7", layer="below")
    for z, x0, y0, w, h in layout_boxes:
        util = num(z.get("utilization_percent")); status = str(z.get("status", "NORMAL")).upper()
        if util > 100 or "OVERCROWDED" in status:
            fill, border = "#ef4444", "#991b1b"
        elif util >= 80:
            fill, border = "#f59e0b", "#b45309"
        elif util >= 40:
            fill, border = "#14b8a6", "#0f766e"
        else:
            fill, border = "#94a3b8", "#64748b"
        name = esc(z.get("zone_name", "Zone")); occ = int(num(z.get("occupancy"))); cap = int(num(z.get("capacity")))
        fig.add_shape(type="rect", x0=x0, y0=y0, x1=x0+w, y1=y0+h, line=dict(color=border, width=3 if util > 100 else 1.5), fillcolor=fill, opacity=.88, layer="above")
        fig.add_trace(go.Scatter(
            x=[x0+w/2], y=[y0+h/2], mode="text", text=[f"{name}<br>{occ}/{cap} · {util:.0f}%"],
            hovertemplate=f"<b>{name}</b><br>Type: {esc(z.get('zone_type','—'))}<br>Floor: {esc(z.get('floor','—'))}<br>Occupancy: {occ} / {cap}<br>Utilization: {util:.1f}%<br>Status: {esc(status)}<extra></extra>",
            textfont=dict(color="#fff", size=11, family="Inter"), showlegend=False))
    fig.update_layout(height=470, margin=dict(l=8,r=8,t=8,b=8), paper_bgcolor="#fff", plot_bgcolor="#f8fafc", xaxis=dict(range=[0,1],visible=False,fixedrange=True), yaxis=dict(range=[0,1],visible=False,fixedrange=True,scaleanchor="x",scaleratio=1), hoverlabel=dict(bgcolor="#0f172a",font=dict(color="white",size=11)))
    return fig


def aggregate_trend(records, horizon):
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    if df.empty or "timestamp" not in df:
        return pd.DataFrame()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["occupancy"] = pd.to_numeric(df.get("occupancy", 0), errors="coerce").fillna(0)
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
    if df.empty:
        return df
    cutoff = df["timestamp"].max() - ({"24H":pd.Timedelta(hours=24),"7D":pd.Timedelta(days=7),"30D":pd.Timedelta(days=30)}[horizon])
    return df[df["timestamp"] >= cutoff].copy()


now = datetime.utcnow()
st.markdown(f"""
<div class="hero"><div style="display:flex;justify-content:space-between;align-items:flex-start;gap:20px;"><div>
<div class="eyebrow">FacilityOPS / Occupancy + Security</div><div class="hero-title">Facility Operations Center</div>
<p class="hero-sub">Live spatial occupancy, utilization analytics, anomaly intelligence and physical-security telemetry.</p></div>
<div style="text-align:right;"><div class="live-pill"><span class="live-dot"></span> LIVE · {now.strftime('%H:%M:%S UTC')}</div><div style="color:#94a3b8;font-size:10px;margin-top:7px;">Operator monitoring console</div></div></div></div>
""", unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns([2.1,1.25,1.25,1.2])
facility_response = safe_get("/occupancy/facilities", fallback_data={"facilities": []})
facility_options, facility_response = get_facilities()
if not facility_options:
    st.warning("No facilities are available from the canonical catalog.")
    st.stop()
with c1:
    selected_facility = st.selectbox("Facility", facility_options, key="occ_facility")
with c2:
    floor_placeholder = st.empty()
with c3:
    timeframe = st.selectbox("Analytics window", ["24H","7D","30D"], index=0, key="occ_timeframe")
with c4:
    if st.button("↻ Refresh", width="stretch"):
        st.cache_data.clear(); st.rerun()

# Real backend endpoints: dashboard, zones, records, security and OccupancyAgent analysis.
dashboard_res = safe_get(f"/occupancy/dashboard/{selected_facility}", fallback_data={})
data = dashboard_res.get("data") or {}
summary = data.get("summary") or {}
all_zones = data.get("zones") or []
raw_alerts = data.get("alerts") or []
sec_res = safe_get(f"/occupancy/security/{selected_facility}?limit=50", fallback_data={"events":[]})
sec_events = (sec_res.get("data") or {}).get("events") or []
zone_meta_res = safe_get(f"/occupancy/zones/{selected_facility}", fallback_data={"zones":[]})
zone_meta = (zone_meta_res.get("data") or {}).get("zones") or []
zone_meta_by_id = {str(z.get("zone_id")): z for z in zone_meta}
records = data.get("trend") or []

floor_values = sorted({int(num(z.get("floor"),1)) for z in all_zones})
floor_options = ["All Floors"] + [f"Floor {f}" for f in floor_values]
with floor_placeholder.container():
    selected_floor = st.selectbox("Floor", floor_options, key="occ_floor")

zones=[]
for z in all_zones:
    merged=dict(z); meta=zone_meta_by_id.get(str(z.get("zone_id")),{})
    if meta.get("area_sqft") is not None: merged["area_sqft"]=meta.get("area_sqft")
    zones.append(merged)
if selected_floor != "All Floors":
    floor_no=int(selected_floor.split()[-1]); zones=[z for z in zones if int(num(z.get("floor"),1))==floor_no]

# KPI ribbon.
total_occ=int(num(summary.get("total_occupants"),sum(num(z.get("occupancy")) for z in zones)))
total_cap=int(num(summary.get("total_capacity"),sum(num(z.get("capacity")) for z in zones)))
utilization=num(summary.get("utilization_percent"),(total_occ/total_cap*100) if total_cap else 0)
overcrowded=int(num(summary.get("overcrowded_zones"),sum(num(z.get("utilization_percent"))>100 for z in zones)))
highly=int(num(summary.get("highly_utilized_zones"),sum(80<=num(z.get("utilization_percent"))<=100 for z in zones)))
active_security=sum(str(e.get("status","")).lower() in {"open","investigating"} for e in sec_events)
critical_security=sum(str(e.get("severity","")).lower() in {"high","critical"} for e in sec_events)
kpis=[
    ("TOTAL HEADCOUNT",f"{total_occ:,}",f"Capacity {total_cap:,}","kpi-info"),
    ("FACILITY UTILIZATION",f"{utilization:.1f}%",f"{highly} high-utilization zones","kpi-warning" if utilization>=70 else "kpi-good"),
    ("ZONES MONITORED",f"{len(zones)}",f"{len(floor_values)} floors in facility","kpi-info"),
    ("OVERCROWDED ZONES",f"{overcrowded}",f"{highly} highly utilized","kpi-critical" if overcrowded else "kpi-good"),
    ("ACTIVE SECURITY",f"{active_security}",f"{critical_security} high severity","kpi-critical" if critical_security else "kpi-good")]
html_kpi='<div class="kpi-grid">'
for label,value,meta,cls in kpis:
    html_kpi+=f'<div class="kpi {cls}"><div class="kpi-label">{esc(label)}</div><div class="kpi-value">{esc(value)}</div><div class="kpi-meta">{esc(meta)}</div></div>'
html_kpi+='</div>'; st.markdown(html_kpi,unsafe_allow_html=True)

# Spatial map + AI desk.
map_col,ai_col=st.columns([7,3],gap="large")
with map_col:
    st.markdown(f'<div class="panel"><div class="panel-head"><div><div class="panel-title">🗺️ Live Spatial Occupancy Heatmap</div><div class="panel-sub">{esc(selected_facility)} · {esc(selected_floor)} · current utilization by real zone</div></div></div>',unsafe_allow_html=True)
    if zones:
        if selected_floor=="All Floors" and floor_values:
            tabs=st.tabs([f"Floor {f}" for f in floor_values])
            for tab,floor_no in zip(tabs,floor_values):
                with tab:
                    floor_zones=[z for z in zones if int(num(z.get("floor"),1))==floor_no]
                    st.plotly_chart(build_floorplan(floor_zones),width="stretch",config={"displayModeBar":False},key=f"map_{selected_facility}_{floor_no}")
        else:
            st.plotly_chart(build_floorplan(zones),width="stretch",config={"displayModeBar":False},key=f"map_{selected_facility}_{selected_floor}")
        st.markdown('<div class="legend"><span class="legend-item"><span class="legend-dot" style="background:#94a3b8"></span>Low &lt;40%</span><span class="legend-item"><span class="legend-dot" style="background:#14b8a6"></span>Moderate 40–79%</span><span class="legend-item"><span class="legend-dot" style="background:#f59e0b"></span>High 80–100%</span><span class="legend-item"><span class="legend-dot" style="background:#ef4444"></span>Overcrowded &gt;100%</span></div>',unsafe_allow_html=True)
    else: st.warning("No occupancy zones are available for this facility/floor.")
    st.markdown('</div>',unsafe_allow_html=True)

with ai_col:
    ai_key=f"occ_ai_{selected_facility}"
    if st.button("⚡ Run Facility Analysis",width="stretch",key=f"run_{selected_facility}"):
        with st.spinner("Occupancy + security agents analyzing telemetry..."):
            analysis_res=safe_get(f"/occupancy/analyze/{selected_facility}",fallback_data={})
            st.session_state[ai_key]=analysis_res.get("data") if analysis_res.get("success") else {}
    ai_data=st.session_state.get(ai_key)
    if not ai_data:
        st.markdown('<div class="ai"><div class="ai-head"><div><div class="ai-title">AI Operations Desk</div><div class="ai-sub">Occupancy Agent · Security correlation</div></div><div class="ai-badge">READY</div></div><div class="ai-note">Run facility analysis to translate the agent response into operator-ready findings and actions. Raw JSON is intentionally hidden.</div><div style="height:180px"></div></div>',unsafe_allow_html=True)
    else:
        status=str(ai_data.get("status","Normal")); is_critical=status.lower()=="critical"; summary_ai=ai_data.get("summary") or {}; crowded_ids=set(summary_ai.get("overcrowded_zones") or []); ai_alerts=ai_data.get("alerts") or []; recommendations=ai_data.get("recommendations") or []
        crowded_names=[z.get("zone_name") for z in all_zones if z.get("zone_id") in crowded_ids and z.get("zone_name")]
        status_color="#ef4444" if is_critical else "#34d399"
        st.markdown(f'<div class="ai"><div class="ai-head"><div><div class="ai-title">AI Operations Desk</div><div class="ai-sub">Occupancy Agent · Security correlation</div></div><div class="ai-badge">ANALYSIS COMPLETE</div></div><div class="ai-status"><div><div class="ai-status-label">Facility assessment</div><div class="ai-status-value" style="color:{status_color}">{esc(status.upper())}</div></div><div class="ai-metric"><div class="ai-status-label">Anomalies</div><div class="ai-status-value">{int(num(ai_data.get("anomalies_detected")))}</div></div></div>',unsafe_allow_html=True)
        if crowded_names:
            st.markdown(f'<div class="ai-chip high"><div class="tag">OVERCROWDING</div><div class="body"><b>{esc(", ".join(crowded_names))}</b> exceeded configured capacity.</div></div>',unsafe_allow_html=True)
        elif not ai_alerts:
            st.markdown('<div class="ai-chip"><div class="tag">STATUS</div><div class="body">No current occupancy or security anomaly requires escalation.</div></div>',unsafe_allow_html=True)
        for alert in ai_alerts[:3]:
            sev=str(alert.get("severity","Medium")); high=sev.lower() in {"high","critical"}
            st.markdown(f'<div class="ai-chip {"high" if high else ""}"><div class="tag">{esc(sev)} · {esc(alert.get("type",alert.get("alert_type","Alert")))}</div><div class="body">{esc(alert.get("message","Operational alert detected."))}</div></div>',unsafe_allow_html=True)
        st.markdown('<div class="section-label" style="color:#94a3b8;margin-top:12px">Recommended directives</div>',unsafe_allow_html=True)
        if recommendations:
            for rec in recommendations[:4]:
                priority=str(rec.get("priority","Routine")); high=priority.lower() in {"high","critical"}
                st.markdown(f'<div class="ai-chip {"high" if high else ""}"><div class="tag">{esc(priority)} · {esc(rec.get("trigger","Operational signal"))}</div><div class="body">{esc(rec.get("action",""))}</div></div>',unsafe_allow_html=True)
        else: st.markdown('<div class="ai-note">No immediate action required.</div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

# Zone performance + security.
zone_col,sec_col=st.columns([6,4],gap="large")
with zone_col:
    st.markdown('<div class="panel"><div class="panel-head"><div><div class="panel-title">Zone Utilization & Capacity</div><div class="panel-sub">Current room/space telemetry with capacity pressure.</div></div></div>',unsafe_allow_html=True)
    if zones:
        zone_html=''
        for z in sorted(zones,key=lambda x:num(x.get("utilization_percent")),reverse=True):
            util=num(z.get("utilization_percent")); status,fg,bg=status_for(util); pct=safe_pct(util); area=int(num(z.get("area_sqft"))) if z.get("area_sqft") else "—"; occ=int(num(z.get("occupancy"))); cap=int(num(z.get("capacity")))
            zone_html+=f'<div class="zone-card"><div class="zone-top"><div><div class="zone-name">{esc(z.get("zone_name","Unknown zone"))}</div><div class="zone-meta">Floor {esc(z.get("floor","—"))} · {esc(z.get("zone_type","—"))} · {area} sqft</div></div><div style="text-align:right"><div style="font-size:14px;font-weight:800;color:{fg}">{util:.1f}%</div><span class="status-pill" style="background:{bg};color:{fg}">{status}</span></div></div><div class="bar"><div style="width:{pct:.1f}%;background:{fg}"></div></div><div class="zone-meta" style="margin-top:5px">Occupancy {occ}/{cap} · {"Capacity exceeded" if util>100 else f"{max(0,cap-occ)} places available"}</div></div>'
        st.markdown(zone_html,unsafe_allow_html=True)
    else: st.info("No zone telemetry available.")
    st.markdown('</div>',unsafe_allow_html=True)

with sec_col:
    st.markdown('<div class="panel"><div class="panel-head"><div><div class="panel-title">🔒 Security Operations</div><div class="panel-sub">Access-control and physical-security event stream.</div></div></div>',unsafe_allow_html=True)
    combined=[]
    for a in raw_alerts:
        combined.append({"severity":a.get("severity","High"),"title":a.get("alert_type","Occupancy Alert"),"body":a.get("message","Occupancy threshold exceeded."),"time":a.get("timestamp"),"foot":f'{a.get("zone_name","Zone")} · utilization {num(a.get("utilization_percent")):.1f}%'})
    for e in sec_events:
        combined.append({"severity":e.get("severity","Low"),"title":e.get("event_type","Security Event"),"body":f'Status: {e.get("status","—")} · Zone level: {e.get("zone_level","—")} · Failed attempts: {e.get("recent_failed_attempts","—")}',"time":e.get("event_time"),"foot":f'{selected_facility} · {e.get("event_id","Security event")}'})
    severity_rank={"critical":0,"high":1,"medium":2,"low":3}; combined.sort(key=lambda x:severity_rank.get(str(x["severity"]).lower(),4))
    if combined:
        for inc in combined[:8]:
            sev=str(inc["severity"]); sev_class="high" if sev.lower() in {"high","critical"} else "medium" if sev.lower()=="medium" else "low"
            st.markdown(f'<div class="incident {sev_class}"><div class="incident-head"><div class="incident-title">{esc(inc["title"])} <span style="color:#64748b">· {esc(sev.upper())}</span></div><div class="incident-time">{esc(format_time(inc["time"]))}</div></div><div class="incident-body">{esc(inc["body"])}</div><div class="incident-foot">{esc(inc["foot"])}</div></div>',unsafe_allow_html=True)
    else: st.markdown('<div style="padding:35px 10px;text-align:center;color:#64748b;font-size:11px">✓ No active incidents in the current telemetry window.</div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# Selected zone detail.
if zones:
    zone_names=[z.get("zone_name","Unknown") for z in zones]
    selected_zone_name=st.selectbox("Inspect zone detail",zone_names,key=f"zone_detail_{selected_facility}_{selected_floor}")
    selected_zone=next((z for z in zones if z.get("zone_name")==selected_zone_name),zones[0]); util=num(selected_zone.get("utilization_percent")); status,fg,bg=status_for(util); area=int(num(selected_zone.get("area_sqft"))) if selected_zone.get("area_sqft") else "—"
    st.markdown(f'<div class="panel"><div class="panel-head"><div><div class="panel-title">Selected Zone · {esc(selected_zone_name)}</div><div class="panel-sub">Detailed operator view for the selected space.</div></div><span class="status-pill" style="background:{bg};color:{fg};font-size:9px">{status}</span></div><div class="detail-grid"><div class="detail-cell"><div class="detail-key">Occupancy</div><div class="detail-val">{int(num(selected_zone.get("occupancy")))} / {int(num(selected_zone.get("capacity")))}</div></div><div class="detail-cell"><div class="detail-key">Utilization</div><div class="detail-val" style="color:{fg}">{util:.1f}%</div></div><div class="detail-cell"><div class="detail-key">Floor / Type</div><div class="detail-val">F{esc(selected_zone.get("floor"))} · {esc(selected_zone.get("zone_type"))}</div></div><div class="detail-cell"><div class="detail-key">Area</div><div class="detail-val">{area} sqft</div></div></div></div>',unsafe_allow_html=True)

# Historical utilization analytics.
st.markdown(f'<div class="panel"><div class="panel-head"><div><div class="panel-title">📈 Occupancy & Utilization Trend · {esc(timeframe)}</div><div class="panel-sub">Historical telemetry is aggregated from occupancy records; each window changes the visible range and time resolution.</div></div></div>',unsafe_allow_html=True)
df=aggregate_trend(records,timeframe)
if not df.empty:
    capacity_by_zone={str(z.get("zone_id")):num(z.get("capacity")) for z in all_zones}
    if "zone_id" in df.columns:
        df["capacity"]=df["zone_id"].astype(str).map(capacity_by_zone).fillna(0)
    else:
        df["capacity"]=0
    df["bucket"]=df["timestamp"].dt.floor("h" if timeframe=="24H" else "D")
    if "zone_id" in df.columns:
        grouped=df.drop_duplicates(subset=["bucket","zone_id"]).groupby("bucket").agg(occupancy=("occupancy","sum"),capacity=("capacity","sum")).reset_index()
    else:
        grouped=df.groupby("bucket").agg(occupancy=("occupancy","sum"),capacity=("capacity","sum")).reset_index()
    grouped["utilization"]=grouped.apply(lambda r:(r["occupancy"]/r["capacity"]*100) if r["capacity"] else 0,axis=1)
    fig=go.Figure(go.Scatter(x=grouped["bucket"],y=grouped["utilization"],mode="lines+markers",line=dict(color="#2563eb",width=3),marker=dict(size=6,color="#0ea5e9"),fill="tozeroy",fillcolor="rgba(37,99,235,.08)",hovertemplate="%{x|%d %b %H:%M}<br><b>%{y:.1f}%</b> utilization<extra></extra>",name="Utilization"))
    fig.add_hline(y=80,line_dash="dot",line_color="#f59e0b",annotation_text="High 80%",annotation_position="top left")
    fig.add_hline(y=100,line_dash="dot",line_color="#ef4444",annotation_text="Capacity 100%",annotation_position="top left")
    ymax=max(110,float(grouped["utilization"].max())+10) if not grouped.empty else 110
    fig.update_layout(height=320,margin=dict(l=5,r=5,t=8,b=5),paper_bgcolor="#fff",plot_bgcolor="#fff",showlegend=False,hovermode="x unified",xaxis=dict(showgrid=False,title=None),yaxis=dict(showgrid=True,gridcolor="#eef2f7",title="Utilization %",range=[0,ymax]))
    st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})
    peak=float(grouped["utilization"].max()) if not grouped.empty else 0; avg=float(grouped["utilization"].mean()) if not grouped.empty else 0; points=len(grouped)
    peak_color="#ef4444" if peak>100 else "#d97706" if peak>=80 else "#059669"
    st.markdown(f'<div class="detail-grid"><div class="detail-cell"><div class="detail-key">Window average</div><div class="detail-val">{avg:.1f}%</div></div><div class="detail-cell"><div class="detail-key">Peak utilization</div><div class="detail-val" style="color:{peak_color}">{peak:.1f}%</div></div><div class="detail-cell"><div class="detail-key">Telemetry points</div><div class="detail-val">{points}</div></div><div class="detail-cell"><div class="detail-key">Window</div><div class="detail-val">{esc(timeframe)}</div></div></div>',unsafe_allow_html=True)
else:
    st.info(f"No historical occupancy records are available for the {timeframe} window. Live zone telemetry remains available above.")
st.markdown('</div>',unsafe_allow_html=True)

st.markdown(f'<div style="color:#94a3b8;font-size:9px;text-align:right;margin-top:4px">Source: FacilityOPS occupancy dashboard, occupancy records, security telemetry and OccupancyAgent analysis · {esc(selected_facility)}</div>',unsafe_allow_html=True)