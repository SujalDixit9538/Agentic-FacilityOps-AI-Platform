import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Ensure project root is on sys.path so `frontend` can be imported when
# running this file directly (e.g. `python frontend/pages/_test_design_system.py`).
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
from frontend.components.ui import (
    kpi_card,
    health_gauge,
    health_distribution_bar,
    risk_table,
    sensor_simulator_panel,
    alert_feed
)
from frontend.utils.theme import COLORS

def inject_theme():
    """Injects dark theme background."""
    st.markdown(f"""
    <style>
        .stApp {{ background-color: {COLORS['bg']}; }}
    </style>
    """, unsafe_allow_html=True)

def main():
    inject_theme()
    st.title("Design System Smoke Test")
    
    st.subheader("1. KPI Cards")
    kpi_card("Total Assets", "154", delta="+2", icon="🏢", status="good")
    
    st.subheader("2. Health Gauge")
    health_gauge(75, "Fleet Health Score")
    
    st.subheader("3. Health Distribution")
    health_distribution_bar({"Excellent": 40, "Good": 30, "Warning": 20, "Critical": 10})
    
    st.subheader("4. Risk Table")
    df = pd.DataFrame({
        "asset": ["Asset A", "Asset B"],
        "health_score": [85, 45]
    })
    risk_table(df)
    
    st.subheader("5. Sensor Panel")
    def mock_predict(inputs):
        return {"health_score": 60, "failure_probability": 0.15}
    sensor_simulator_panel(mock_predict)
    
    st.subheader("6. Alert Feed")
    alert_feed([{"severity": "high", "title": "Critical issue!", "description": "System failure detected."}])

if __name__ == "__main__":
    main()
