import streamlit as st
from frontend.utils.session import initialize_session

# Must be the very first Streamlit command
st.set_page_config(
    page_title="FacilityOPS AI",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize global state
initialize_session()

st.title("🏢 Agentic FacilityOPS AI Platform")
st.markdown("### Executive Operations Center")

st.info("Platform connection established. Please select a module from the sidebar navigation to begin.")

st.markdown("""
**Current Status:**
* **Backend:** Operational
* **Frontend:** Operational
* **Active Agents:** Initialization Pending (Milestone 1)
""")