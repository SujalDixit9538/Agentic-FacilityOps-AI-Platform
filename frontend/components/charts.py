"""Reusable chart presentation helpers for dashboard pages."""

from typing import Any

import streamlit as st


def render_chart_card(title: str, figure: Any) -> None:
    """Render a Plotly-compatible figure inside a bordered chart card."""
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.plotly_chart(figure, width="stretch")
