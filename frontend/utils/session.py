import streamlit as st


def initialize_session():
    """Initialize state shared across FacilityOPS pages."""
    if "platform_initialized" not in st.session_state:
        st.session_state["platform_initialized"] = True
        st.session_state["active_alerts"] = []
        st.session_state["last_refresh"] = None
        st.session_state["selected_facility_id"] = None


def set_selected_facility(facility_id: str | None) -> None:
    """Persist the facility currently being analyzed across page navigation."""
    st.session_state["selected_facility_id"] = facility_id
