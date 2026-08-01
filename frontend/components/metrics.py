import streamlit as st

def render_metric_card(title: str, value: str, delta: str = None, help_text: str = None):
    """
    Renders a standardized metric card for executive dashboards.
    Wraps Streamlit's native metric to ensure visual consistency.
    """
    st.metric(label=title, value=value, delta=delta, help=help_text)

def render_metric_row(metrics: list):
    """
    Renders a responsive row of multiple metric cards.
    Expects a list of dictionaries: [{'title': '...', 'value': '...', 'delta': '...'}]
    """
    cols = st.columns(len(metrics))
    for i, col in enumerate(cols):
        with col:
            metric_data = metrics[i]
            render_metric_card(
                title=metric_data.get("title"),
                value=metric_data.get("value"),
                delta=metric_data.get("delta"),
                help_text=metric_data.get("help_text")
            )