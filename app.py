import streamlit as st
from pathlib import Path
from login import show_login
from sidebar import show_sidebar
from utils.config import load_config, init_session_state

# ------------------------
# Configure Streamlit
# ------------------------
st.set_page_config(
    page_title="Business Management Suite",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------
# Load custom CSS
# ------------------------
def load_css():
    css_file = Path("assets/style.css")
    if css_file.exists():
        with open(css_file, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ CSS file not found — using default styling.")

# ------------------------
# Main app logic
# ------------------------
def main():
    load_css()
    load_config()
    init_session_state()

    # Debug marker
    st.write("🚀 App started")

    # Check login
    if not st.session_state.get("logged_in", False):
        st.write("🔐 Login required")
        show_login()
        return

    # User is logged in
    st.write("✅ Logged in")
    show_sidebar()

    # Set default page if missing
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    # Map page names to actual page paths
    base_dir = Path(__file__).parent
    page_mapping = {
        "Dashboard": base_dir / "pages" / "1_Dashboard.py",
        "Calendar": base_dir / "pages" / "2_Calendar.py",
        "Invoices": base_dir / "pages" / "3_Invoices.py",
        "Customers": base_dir / "pages" / "4_Customers.py",
        "Appointments": base_dir / "pages" / "5_Appointments.py",
        "Pricing": base_dir / "pages" / "6_Pricing.py",
        "AI Chat": base_dir / "pages" / "7_Super_Chat.py",
        "Voice Calls": base_dir / "pages" / "8_AI_Caller.py",
        "Call Center": base_dir / "pages" / "9_Call_Center.py",
        "Content Management": base_dir / "pages" / "10_Content_Management_Dashboard.py"
    }

    selected_page = st.session_state.get("current_page")
    st.write(f"📄 Current page: {selected_page}")

    # Switch to selected page if exists
    if selected_page in page_mapping:
        try:
            page_path = page_mapping[selected_page]
            if page_path.exists():
                st.switch_page(str(page_path))
            else:
                st.error(f"❌ Page file not found: {page_path}")
        except Exception as e:
            st.error(f"❌ Failed to switch page: {e}")
    else:
        st.warning("⚠️ Page not found. Showing fallback dashboard.")
        st.title("📊 Dashboard (Fallback)")
        st.info("Use the sidebar to select a valid page.")

if __name__ == "__main__":
    main()
