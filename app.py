import streamlit as st
import os
from pathlib import Path
from login import show_login
from sidebar import show_sidebar
from utils.config import load_config, init_session_state
from utils.auth import check_session_validity

# Configure Streamlit page
st.set_page_config(
    page_title="Business Management Suite",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    css_file = Path("assets/style.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize app
def main():
    load_css()
    load_config()
    init_session_state()
    
    # Check if user is logged in and session is valid
    if not st.session_state.get("logged_in", False) or not check_session_validity():
        show_login()
    else:
        show_sidebar()
        # Default to dashboard if no page is selected
        if "current_page" not in st.session_state:
            st.session_state.current_page = "Dashboard"
        
        # Navigate to the selected page
        page_mapping = {
            "Dashboard": "pages/1_Dashboard.py",
            "Calendar": "pages/2_Calendar.py", 
            "Invoices": "pages/3_Invoices.py",
            "Customers": "pages/4_Customers.py",
            "Appointments": "pages/5_Appointments.py",
            "Pricing": "pages/6_Pricing.py",
            "AI Chat": "pages/7_Super_Chat.py",
            "Voice Calls": "pages/8_AI_Caller.py",
            "Call Center": "pages/9_Call_Center.py"
        }
        
        if st.session_state.current_page in page_mapping:
            st.switch_page(page_mapping[st.session_state.current_page])

if __name__ == "__main__":
    main()
