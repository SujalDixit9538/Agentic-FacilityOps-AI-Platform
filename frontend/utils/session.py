import streamlit as st

def initialize_session():
    """
    Initializes global session variables required across multiple pages.
    Ensures state is preserved when users navigate between modules.
    """
    if "platform_initialized" not in st.session_state:
        st.session_state["platform_initialized"] = True
        st.session_state["active_alerts"] = []
        st.session_state["last_refresh"] = None
        # Future agent data caches will be registered here