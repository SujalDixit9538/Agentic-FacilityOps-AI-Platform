import streamlit as st

def render_status_banner(is_online: bool = True, custom_message: str = None):
    """
    Implements Blueprint Rule 5.4: Graceful Degradation.
    Displays professional status indicators instead of technical stack traces.
    """
    if not is_online:
        message = custom_message or "Live data is temporarily unavailable. Displaying the most recent verified results."
        st.warning(f"⚠️ **System Degraded:** {message}")
    else:
        if custom_message:
            st.info(f"ℹ️ {custom_message}")
            
def render_empty_state(module_name: str, message: str = "No data available at this time."):
    """Renders a clean placeholder when a module has no data to display."""
    st.markdown(f"### {module_name}")
    st.caption(message)
    st.divider()