import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px

# ------------------------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------------------------
st.set_page_config(
    page_title="📊 Content Management Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------------------------------
# Sidebar auth status
# ------------------------------------------------------------------------------------
st.sidebar.title("🔐 Authentication Status")

if not st.session_state.get("global_gsheets_creds"):
    st.sidebar.error("❌ No global credentials found")
    st.sidebar.info("Please upload service account JSON in the main sidebar")
    st.error("🔑 Google Sheets credentials not found. Please log in from the authentication page.")
    st.stop()
else:
    st.sidebar.success("✅ Using global credentials")
    client_email = st.session_state.global_gsheets_creds.get('client_email', 'Unknown')
    st.sidebar.info(f"📧 {client_email}")

# ------------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------------
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1-CplAWu7qP4R616bLSCwtUy-nHJoe5D0344m9hU_MMo/edit?usp=sharing"  # Replace with your actual Sheet URL
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ------------------------------------------------------------------------------------
# Styles
# ------------------------------------------------------------------------------------
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stats-card {
        background: rgba(102, 126, 234, 0.1);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .content-item {
        background: rgba(255,255,255,0.9);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 10px 20px;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 10px 10px 0 0;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------------
# Session defaults
# ------------------------------------------------------------------------------------
if 'content_data' not in st.session_state:
    st.session_state.content_data = {}
if 'last_updated' not in st.session_state:
    st.session_state.last_updated = datetime.now()
if 'sheets_connected' not in st.session_state:
    st.session_state.sheets_connected = False

# ------------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------------
def load_sample_data():
    return {
        "🪡 Threads": ["Example Thread 1", "Example Thread 2"],
        "🧵 Tweet thread": ["Example Tweet 1", "Example Tweet 2"],
        "👩‍💻 LinkedIn post": ["Example LinkedIn 1", "Example LinkedIn 2"],
        "🎬 Reel script": ["Example Reel Script 1", "Example Reel Script 2"]
    }

def connect_to_sheets():
    try:
        creds = Credentials.from_service_account_info(st.session_state.global_gsheets_creds, scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet_id = SHEETS_URL.split('/d/')[1].split('/')[0]
        sheet = client.open_by_key(sheet_id)
        st.session_state.sheet = sheet
        st.session_state.sheets_connected = True
        return True, f"Connected to: {sheet.title}"
    except Exception as e:
        st.session_state.sheets_connected = False
        return False, f"Connection failed: {e}"

def refresh_from_sheets():
    try:
        worksheet = st.session_state.sheet.sheet1
        rows = worksheet.get_all_records()
        if rows:
            data = {}
            columns = rows[0].keys()
            for col in columns:
                data[col] = [row[col] for row in rows if row.get(col)]
            st.session_state.content_data = data
            st.session_state.last_updated = datetime.now()
            return True, "Data refreshed"
        return False, "No data in sheet"
    except Exception as e:
        return False, f"Refresh failed: {e}"

def export_to_json():
    return json.dumps({
        "data": st.session_state.content_data,
        "exported_at": st.session_state.last_updated.isoformat(),
        "total_entries": sum(len(v) for v in st.session_state.content_data.values())
    }, indent=2)

# ------------------------------------------------------------------------------------
# Data bootstrap
# ------------------------------------------------------------------------------------
if not st.session_state.content_data:
    st.session_state.content_data = load_sample_data()

# ------------------------------------------------------------------------------------
# Header
# ------------------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>📊 Content Management Dashboard</h1>
    <p>Manage and sync your content from Google Sheets</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------------
# Sidebar controls
# ------------------------------------------------------------------------------------
with st.sidebar:
    st.header("📡 Google Sheets")
    if st.button("🔗 Connect to Sheets", use_container_width=True):
        success, msg = connect_to_sheets()
        st.success(msg) if success else st.error(msg)

    if st.button("🔄 Refresh Data", use_container_width=True):
        success, msg = refresh_from_sheets()
        st.success(msg) if success else st.error(msg)

    st.download_button(
        "💾 Export Data",
        export_to_json(),
        file_name=f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        use_container_width=True
    )

    total_entries = sum(len(v) for v in st.session_state.content_data.values())
    st.markdown(f"""
    <div class="stats-card">
        <b>Total Entries:</b> {total_entries}<br>
        <b>Categories:</b> {len(st.session_state.content_data)}<br>
        <b>Last Updated:</b> {st.session_state.last_updated.strftime('%H:%M:%S')}<br>
        <b>Connection:</b> {'🟢 Connected' if st.session_state.sheets_connected else '🔴 Disconnected'}
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------------
# Main content tabs
# ------------------------------------------------------------------------------------
if st.session_state.content_data:
    tabs = st.tabs(st.session_state.content_data.keys())
    for tab, category in zip(tabs, st.session_state.content_data.keys()):
        with tab:
            st.subheader(f"📝 {category}")
            st.metric("Items", len(st.session_state.content_data[category]))

            with st.expander("➕ Add New Content"):
                new_item = st.text_area(f"New {category} content", key=f"new_{category}")
                if st.button("Add", key=f"add_{category}"):
                    if new_item.strip():
                        st.session_state.content_data[category].append(new_item.strip())
                        st.session_state.last_updated = datetime.now()
                        st.success("Added successfully")
                        st.experimental_rerun()
                    else:
                        st.error("Please enter text")

            st.divider()
            for idx, item in enumerate(st.session_state.content_data[category]):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"<div class='content-item'><b>Entry {idx+1}:</b><br>{item}</div>", unsafe_allow_html=True)
                with col2:
                    if st.button("🗑️", key=f"del_{category}_{idx}"):
                        st.session_state.content_data[category].pop(idx)
                        st.session_state.last_updated = datetime.now()
                        st.experimental_rerun()
else:
    st.warning("No data loaded.")

# ------------------------------------------------------------------------------------
# Footer
# ------------------------------------------------------------------------------------
st.markdown("---")
st.markdown("<div style='text-align:center;color:#666;'>📊 Content Management Dashboard</div>", unsafe_allow_html=True)
