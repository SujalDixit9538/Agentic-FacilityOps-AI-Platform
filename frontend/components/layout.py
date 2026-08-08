"""Reusable layout helpers for enterprise dashboard pages."""

from typing import Optional

import streamlit as st


def render_section_header(title: str, subtitle: Optional[str] = None) -> None:
    """Render a consistent section header with optional supporting text."""
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)
