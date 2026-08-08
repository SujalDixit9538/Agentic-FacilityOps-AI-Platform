"""Reusable filter controls for dashboard pages."""

from typing import Optional, Sequence, TypeVar

import streamlit as st

T = TypeVar("T")


def render_select_filter(
    label: str,
    options: Sequence[T],
    default: Optional[T] = None,
    key: Optional[str] = None,
) -> T:
    """Render a select filter and return the selected option."""
    index = options.index(default) if default in options else 0
    return st.selectbox(label, options=options, index=index, key=key)
