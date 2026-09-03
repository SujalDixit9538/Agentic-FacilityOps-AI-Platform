"""Reusable KPI card helpers for dashboard summary rows."""

from typing import Any, Mapping, Optional, Sequence

import streamlit as st


def render_kpi_row(
    kpis: Sequence[Mapping[str, Any] | object],
    columns: Optional[int] = None,
) -> None:
    """Render a responsive row of KPI cards from dictionaries or simple objects."""
    if not kpis:
        return

    cards_per_row = columns or len(kpis)
    cards_per_row = max(1, min(cards_per_row, len(kpis)))

    for row_start in range(0, len(kpis), cards_per_row):
        row_kpis = kpis[row_start:row_start + cards_per_row]
        for column, kpi in zip(st.columns(len(row_kpis)), row_kpis):
            if isinstance(kpi, Mapping):
                title = kpi.get("title") or kpi.get("label") or "KPI"
                value = kpi.get("value", "")
                delta = kpi.get("delta")
                help_text = kpi.get("help") or kpi.get("help_text")
                caption = kpi.get("caption")
            else:
                title = getattr(kpi, "title", getattr(kpi, "label", "KPI"))
                value = getattr(kpi, "value", "")
                delta = getattr(kpi, "delta", None)
                help_text = getattr(kpi, "help", getattr(kpi, "help_text", None))
                caption = getattr(kpi, "caption", None)

            with column:
                with st.container(border=True):
                    st.caption(str(title).upper())
                    st.markdown(f"### {value}")
                    if delta:
                        st.caption(str(delta))
                    if caption:
                        st.caption(str(caption))
                    if help_text:
                        with st.expander("Details", expanded=False):
                            st.caption(str(help_text))
