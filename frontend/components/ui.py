import html as html_lib

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import Callable, Optional, Dict, List, Any

# Import theme constants
from frontend.utils.theme import COLORS

def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Converts hex color (e.g. #F87171) to rgba(r, g, b, alpha)."""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"

def kpi_card(label: str, value: str, delta: Optional[str] = None, icon: Optional[str] = None, status: str = "neutral") -> None:
    """
    Renders a styled metric card with a colored left border based on status.
    Uses HTML/CSS injection to achieve the specific card surface and border tints.
    """
    status_colors = {
        "good": COLORS["success"],
        "warning": COLORS["warning"],
        "critical": COLORS["critical"],
        "neutral": COLORS["accent"]
    }
    accent_color = status_colors.get(status.lower(), COLORS["accent"])
    
    safe_label = html_lib.escape(str(label))
    safe_value = html_lib.escape(str(value))
    safe_icon = html_lib.escape(str(icon)) if icon else ""
    delta_html = ""
    if delta:
        delta_html = f'<div style="color: {accent_color}; margin-top: 8px; font-size: 14px; font-weight: 500;">{html_lib.escape(str(delta))}</div>'
    
    icon_str = f'<span style="margin-right: 8px;">{safe_icon}</span>' if icon else ""

    card_html = f"""
    <div style="
        background-color: {COLORS['surface']}; 
        padding: 20px; 
        border-radius: 12px; 
        border-left: 4px solid {accent_color}; 
        border-top: 1px solid {COLORS['border']}; 
        border-right: 1px solid {COLORS['border']}; 
        border-bottom: 1px solid {COLORS['border']}; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        margin-bottom: 16px;">
        <div style="color: {COLORS['text_sec']}; margin: 0; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
            {icon_str}{safe_label}
        </div>
        <div style="color: {COLORS['text_pri']}; margin: 12px 0 0 0; font-size: 32px; font-weight: 700; line-height: 1;">
            {safe_value}
        </div>
        {delta_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def health_gauge(score: float, title: str = "Health Score", size: str = "medium") -> None:
    """
    Renders a circular gauge indicator for health scores (0-100) using Plotly.
    Color coding: >=80 Green, 50-79 Amber, <50 Red.
    """
    if score >= 80:
        bar_color = COLORS["success"]
    elif score >= 50:
        bar_color = COLORS["warning"]
    else:
        bar_color = COLORS["critical"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': title, 'font': {'color': COLORS["text_sec"], 'size': 16}},
        number={'font': {'color': COLORS["text_pri"], 'size': 36}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': COLORS["border"]},
            'bar': {'color': bar_color},
            'bgcolor': COLORS["bg"],
            'borderwidth': 0,
            'steps': [
                {'range': [0, 50], 'color': hex_to_rgba(COLORS['critical'], 0.12)},
                {'range': [50, 80], 'color': hex_to_rgba(COLORS['warning'], 0.12)},
                {'range': [80, 100], 'color': hex_to_rgba(COLORS['success'], 0.12)}
            ]
        }
    ))
    
    height = 250 if size == "small" else 300 if size == "medium" else 400
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={'family': "sans-serif"}
    )
    st.plotly_chart(fig, width='stretch')

def health_distribution_bar(distribution: Dict[str, float]) -> None:
    """
    Renders a horizontal stacked bar chart showing the distribution of health states.
    Example input: {"Excellent (90-100)": 25, "Good (70-89)": 25, "Warning (50-69)": 25, "Critical (<50)": 25}
    """
    fig = go.Figure()
    
    color_map = {
        "excellent": COLORS["success"],
        "good": COLORS["accent"],
        "warning": COLORS["warning"],
        "critical": COLORS["critical"]
    }

    for label, val in distribution.items():
        # Heuristic to pick color based on label name
        color = COLORS["border"]
        label_lower = label.lower()
        for key, hex_code in color_map.items():
            if key in label_lower:
                color = hex_code
                break
                
        fig.add_trace(go.Bar(
            y=["Fleet Health"],
            x=[val],
            name=label,
            orientation='h',
            marker=dict(color=color, line=dict(color=COLORS["bg"], width=1)),
            text=f"{val}%",
            textposition="inside",
            insidetextfont=dict(color=COLORS["bg"] if color in [COLORS["success"], COLORS["accent"], COLORS["warning"]] else COLORS["text_pri"])
        ))

    fig.update_layout(
        barmode='stack',
        height=120,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0, sum(distribution.values())]),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color=COLORS["text_sec"]))
    )
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

def risk_table(df: pd.DataFrame) -> None:
    """
    Renders a styled dataframe where text color indicates risk level based on health_score.
    """
    def style_risk_rows(row):
        score = row.get('health_score')
        if pd.isna(score):
            color = COLORS["text_sec"]
        elif score >= 80:
            color = COLORS["success"]
        elif score >= 50:
            color = COLORS["warning"]
        else:
            color = COLORS["critical"]
        # Return CSS applied to all columns in the row
        return [f'color: {color}; font-weight: 500;'] * len(row)

    styled_df = df.style.apply(style_risk_rows, axis=1)
    
    # Configure generic styling for headers/background
    styled_df = styled_df.set_properties(**{
        'background-color': COLORS["surface"],
        'border-color': COLORS["border"],
        'text-align': 'left',
        'padding': '10px'
    })
    
    st.dataframe(styled_df, width="stretch", hide_index=True)

def sensor_simulator_panel(on_predict: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Renders an input form using standard AI4I dataset ranges.
    Triggers on_predict callback and displays results.
    """
    st.markdown(f"### <span style='color:{COLORS['text_pri']}'>Sensor Simulator</span>", unsafe_allow_html=True)
    
    with st.form("sensor_simulation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            asset_type = st.selectbox("Asset Type", ["L", "M", "H"], index=1)
            process_temp = st.number_input("Process Temperature [K]", min_value=290.0, max_value=330.0, value=310.0, step=0.1)
            torque = st.number_input("Torque [Nm]", min_value=10.0, max_value=80.0, value=40.0, step=0.5)
            
        with col2:
            air_temp = st.number_input("Air Temperature [K]", min_value=290.0, max_value=315.0, value=300.0, step=0.1)
            speed = st.number_input("Rotational Speed [rpm]", min_value=1000, max_value=3000, value=1500, step=10)
            wear = st.number_input("Tool Wear [min]", min_value=0, max_value=250, value=50, step=1)
            
        submitted = st.form_submit_button("Run Prediction", width='stretch')
        
        if submitted:
            inputs = {
                "type": asset_type,
                "air_temp": air_temp,
                "process_temp": process_temp,
                "speed": speed,
                "torque": torque,
                "wear": wear
            }
            
            result = on_predict(inputs)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            res_col1, res_col2 = st.columns([2, 1])
            
            with res_col1:
                health_gauge(result.get("health_score", 0), "Simulated Health Score", size="small")
            
            with res_col2:
                prob = result.get("failure_probability", 0.0)
                st.metric("Failure Probability", f"{prob:.1%}")
                
            return inputs
            
    return None

def alert_feed(alerts: List[Dict[str, str]]) -> None:
    """
    Renders a vertical feed of color-coded cards that collapse/expand natively.
    Using HTML <details> acts precisely as an st.expander but allows the requested
    custom left-border color tinting without external JS hacks.
    """
    for alert in alerts:
        severity = alert.get("severity", "low").lower()
        safe_title = html_lib.escape(str(alert.get("title", "Alert")))
        safe_description = html_lib.escape(str(alert.get("description", "Details unavailable.")))
        safe_severity = html_lib.escape(str(severity))
        
        if severity == "high" or severity == "critical":
            color = COLORS["critical"]
        elif severity == "medium":
            color = COLORS["warning"]
        else:
            color = COLORS["accent"]
            
        facility_html = f"<div style='margin-top: 8px; font-size: 12px; color: {COLORS['accent']}'>📍 {html_lib.escape(str(alert['facility']))}</div>" if "facility" in alert else ""
        
        # Using native HTML details/summary provides the perfect "collapsible card" 
        # interface while maintaining the strict design system requirements
        html = f"""
        <details style="
            background-color: {COLORS['surface']}; 
            margin-bottom: 12px; 
            border-radius: 8px; 
            border-left: 4px solid {color}; 
            border-top: 1px solid {COLORS['border']}; 
            border-right: 1px solid {COLORS['border']}; 
            border-bottom: 1px solid {COLORS['border']};">
            <summary style="
                padding: 16px; 
                cursor: pointer; 
                color: {COLORS['text_pri']}; 
                font-weight: 600; 
                list-style: none;
                display: flex;
                align-items: center;
                justify-content: space-between;">
                <span style="font-size: 16px; font-weight: 700; color: #FFFFFF;">{safe_title}</span>
                <span style="
                    font-size: 12px; 
                    font-weight: 700;
                    text-transform: uppercase; 
                    color: {color}; 
                    border: 1px solid {color}; 
                    padding: 2px 8px; 
                    border-radius: 12px;">
                    {safe_severity}
                </span>
            </summary>
            <div style="padding: 0 16px 16px 16px; color: #E5E7EB; font-size: 15px; font-weight: 500; line-height: 1.5;">
                {safe_description}
                {facility_html}
            </div>
        </details>
        """
        st.markdown(html, unsafe_allow_html=True)