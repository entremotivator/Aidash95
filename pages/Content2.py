# pages/Content_Management_Dashboard.py
import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials  # For compatibility if needed
import plotly.express as px
from io import BytesIO
import base64

# ------------------------------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------------------------------
st.set_page_config(
    page_title="📊 Content Management Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------------------------------
# Authentication Status (from your Invoice CRM format)
# ------------------------------------------------------------------------------------
st.sidebar.title("🔐 Authentication Status")

if not st.session_state.get("global_gsheets_creds"):
    st.sidebar.error("❌ No global credentials found")
    st.sidebar.info("Please upload service account JSON in the main sidebar")
    st.error("🔑 Google Sheets credentials not found. Please upload your service account JSON in the sidebar.")
    st.stop()
else:
    st.sidebar.success("✅ Using global credentials")
    client_email = st.session_state.global_gsheets_creds.get('client_email', 'Unknown')
    st.sidebar.info(f"📧 {client_email[:30]}...")

# ------------------------------------------------------------------------------------
# Constants / Config
# ------------------------------------------------------------------------------------
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1-CplAWu7qP4R616bLSCwtUy-nHJoe5D0344m9hU_MMo/edit?usp=sharing"
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
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .content-item {
        background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .success-message {
        background: #c6f6d5;
        color: #22543d;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border: 1px solid #9ae6b4;
        margin: 0.5rem 0;
    }
    .error-message {
        background: #fed7d7;
        color: #742a2a;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border: 1px solid #fc8181;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        padding: 10px 20px;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 10px 10px 0 0;
        color: #4a5568;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------------
# Session initialization
# ------------------------------------------------------------------------------------
if 'content_data' not in st.session_state:
    st.session_state.content_data = {}
if 'service_account_config' not in st.session_state:
    if "google_service_account" in st.secrets:
        st.session_state.service_account_config = json.loads(st.secrets["google_service_account"])
    else:
        st.session_state.service_account_config = None
if 'sheets_connected' not in st.session_state:
    st.session_state.sheets_connected = False
if 'last_updated' not in st.session_state:
    st.session_state.last_updated = datetime.now()

# ------------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------------
def load_sample_data():
    return {
        "🪡 Threads by Instagram": ["Example Instagram Thread 1", "Example Instagram Thread 2"],
        "🧵 Tweet thread": ["Example Tweet Thread 1", "Example Tweet Thread 2"],
        "👩‍💻 LinkedIn post": ["Example LinkedIn Post 1", "Example LinkedIn Post 2"],
        "🎬 Reel script": ["Example Reel Script 1", "Example Reel Script 2"],
        "🎞️ Clipfinder: Quotes, Hooks, & Timestamps": ["Example Clipfinder Content 1", "Example Clipfinder Content 2"],
        "❇️ Key topics and bullets": ["Example Key Topics 1", "Example Key Topics 2"],
        "❓ Questions": ["Example Question 1", "Example Question 2"],
        "intro": ["Example Introduction 1", "Example Introduction 2"],
        "FB Post": ["Example Facebook Post 1", "Example Facebook Post 2"],
        "💬 Keywords": ["Keyword1, Keyword2", "Keyword3, Keyword4"],
        "🔖 Titles": ["Title Example 1", "Title Example 2"]
    }

def connect_to_sheets():
    try:
        cfg = st.session_state.service_account_config
        if not cfg:
            return False, "No service account available. Please authenticate on the Login page."
        credentials = Credentials.from_service_account_info(cfg, scopes=SCOPES)
        client = gspread.authorize(credentials)
        sheet_id = SHEETS_URL.split('/d/')[1].split('/')[0]
        sheet = client.open_by_key(sheet_id)
        st.session_state.sheets_client = client
        st.session_state.sheet = sheet
        st.session_state.sheets_connected = True
        return True, f"Connected successfully to: {sheet.title}"
    except Exception as e:
        st.session_state.sheets_connected = False
        return False, f"Connection failed: {str(e)}"

def refresh_from_sheets():
    try:
        if not st.session_state.sheets_connected:
            return False, "Not connected to sheets"
        worksheet = st.session_state.sheet.sheet1
        data = worksheet.get_all_records()
        if data:
            new_data = {}
            columns = data[0].keys()
            for column in columns:
                new_data[column] = [row[column] for row in data if row.get(column)]
            st.session_state.content_data = new_data
            st.session_state.last_updated = datetime.now()
            return True, "Data refreshed successfully"
        return False, "No data found in sheet"
    except Exception as e:
        return False, f"Refresh failed: {str(e)}"

def export_to_json():
    json_data = {
        "data": st.session_state.content_data,
        "exported_at": st.session_state.last_updated.isoformat(),
        "total_entries": sum(len(items) for items in st.session_state.content_data.values())
    }
    return json.dumps(json_data, indent=2)

# ------------------------------------------------------------------------------------
# Auth check (extra layer)
# ------------------------------------------------------------------------------------
if not st.session_state.service_account_config:
    st.error("🔒 This page requires Google Service Account credentials from the Login page.")
    st.info("Go back to your Login/Authentication page to sign in. After login, return here.")
    st.stop()

# ------------------------------------------------------------------------------------
# Data bootstrapping
# ------------------------------------------------------------------------------------
if not st.session_state.content_data:
    st.session_state.content_data = load_sample_data()

# ------------------------------------------------------------------------------------
# Header
# ------------------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>📊 Content Management Dashboard</h1>
    <p>Manage and sync your content across multiple platforms</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------------
# Sidebar controls
# ------------------------------------------------------------------------------------
with st.sidebar:
    st.header("🔧 Dashboard Control")
    st.subheader("📡 Google Sheets")
    if st.button("🔗 Connect to Sheets", use_container_width=True):
        success, message = connect_to_sheets()
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    if st.button("🔄 Refresh Data", use_container_width=True):
        success, message = refresh_from_sheets()
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    json_export = export_to_json()
    st.download_button(
        label="💾 Export Data",
        data=json_export,
        file_name=f"content_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        use_container_width=True
    )

    st.divider()

    st.subheader("📈 Statistics")
    total_entries = sum(len(items) for items in st.session_state.content_data.values())
    st.markdown(f"""
    <div class="stats-card">
        <strong>Total Entries:</strong> {total_entries}<br>
        <strong>Categories:</strong> {len(st.session_state.content_data)}<br>
        <strong>Last Updated:</strong> {st.session_state.last_updated.strftime('%H:%M:%S')}<br>
        <strong>Connection:</strong> {'🟢 Connected' if st.session_state.sheets_connected else '🔴 Disconnected'}
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------------
# Main Content
# ------------------------------------------------------------------------------------
if st.session_state.content_data:
    tab_names = list(st.session_state.content_data.keys())
    tabs = st.tabs(tab_names)
    for tab, column_name in zip(tabs, tab_names):
        with tab:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"📝 {column_name}")
            with col2:
                st.metric("Items", len(st.session_state.content_data[column_name]))

            with st.expander("➕ Add New Content", expanded=False):
                new_content = st.text_area(
                    f"Enter new content for {column_name}:",
                    key=f"new_{column_name}",
                    height=100
                )
                col_a, col_b = st.columns([1, 3])
                with col_a:
                    if st.button("Add Content", key=f"add_{column_name}"):
                        if new_content.strip():
                            st.session_state.content_data.setdefault(column_name, [])
                            st.session_state.content_data[column_name].append(new_content.strip())
                            st.session_state.last_updated = datetime.now()
                            st.success("Content added successfully!")
                            st.rerun()
                        else:
                            st.error("Please enter some content")

            st.divider()
            items = st.session_state.content_data.get(column_name, [])
            if items:
                for idx, content in enumerate(items):
                    col_content, col_delete = st.columns([5, 1])
                    with col_content:
                        st.markdown(f"""
                        <div class="content-item">
                            <strong>Entry {idx + 1}:</strong><br>
                            {content}
                        </div>
                        """, unsafe_allow_html=True)
                    with col_delete:
                        if st.button("🗑️", key=f"delete_{column_name}_{idx}", help="Delete this item"):
                            st.session_state.content_data[column_name].pop(idx)
                            st.session_state.last_updated = datetime.now()
                            st.rerun()
            else:
                st.info(f"No content available for {column_name}. Add some content above!")
else:
    st.warning("No data loaded. Please check your configuration.")

# ------------------------------------------------------------------------------------
# Footer
# ------------------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>📊 Content Management Dashboard | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
