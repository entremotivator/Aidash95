import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import time

# ---------- Configuration ----------
STATIC_SHEET_URL = "https://docs.google.com/spreadsheets/d/1mgToY7I10uwPrdPnjAO9gosgoaEKJCf7nv-E0-1UfVQ/edit"
SHEET_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
SHEET_COLUMNS = [
    'Name', 'Email', 'Guest Email', 'Status', 'Event ID',
    'Start Time (12hr)', 'Start Time (24hr)', 'Meet Link',
    'Description', 'Host', 'Unique Code', 'Upload_Timestamp'
]

# ---------- Streamlit Page Settings ----------
st.set_page_config(
    page_title="🚀 Live Appointments Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Enhanced CSS Styling ----------
st.markdown("""
<style>
    /* Main container styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Appointment cards */
    .appointment-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 5px solid #667eea;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .appointment-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    
    /* Status badges with better styling */
    .status-badge {
        padding: 0.4rem 1rem;
        border-radius: 25px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .status-confirmed { 
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
    }
    
    .status-pending { 
        background: linear-gradient(45deg, #ffc107, #fd7e14);
        color: #212529;
        box-shadow: 0 2px 8px rgba(255, 193, 7, 0.3);
    }
    
    .status-cancelled { 
        background: linear-gradient(45deg, #dc3545, #e83e8c);
        color: white;
        box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
    }
    
    .status-completed { 
        background: linear-gradient(45deg, #6c757d, #495057);
        color: white;
        box-shadow: 0 2px 8px rgba(108, 117, 125, 0.3);
    }
    
    /* Time display */
    .time-display {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
        border: 2px solid #dee2e6;
    }
    
    .time-large {
        font-size: 1.5rem;
        font-weight: bold;
        color: #495057;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Live indicator */
    .live-indicator {
        display: inline-flex;
        align-items: center;
        background: #28a745;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 1rem;
    }
    
    .live-dot {
        width: 8px;
        height: 8px;
        background: white;
        border-radius: 50%;
        margin-right: 0.5rem;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    /* Search and filter styling */
    .filter-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    /* Upcoming appointments highlight */
    .upcoming-appointment {
        border-left-color: #ffc107 !important;
        background: linear-gradient(135deg, #fff3cd, #ffffff);
    }
    
    .current-appointment {
        border-left-color: #28a745 !important;
        background: linear-gradient(135deg, #d4edda, #ffffff);
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { box-shadow: 0 2px 10px rgba(40, 167, 69, 0.2); }
        to { box-shadow: 0 4px 20px rgba(40, 167, 69, 0.4); }
    }
    
    /* Host avatar */
    .host-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(45deg, #667eea, #764ba2);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Helper Functions (Define BEFORE session state) ----------
def create_sample_data():
    """Create sample appointment data"""
    now = datetime.now()
    return pd.DataFrame({
        'Name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Wilson', 'Diana Prince'],
        'Email': ['john@example.com', 'jane@example.com', 'bob@example.com', 'alice@example.com', 'charlie@example.com', 'diana@example.com'],
        'Guest Email': ['guest1@example.com', 'guest2@example.com', '', 'guest4@example.com', '', 'guest6@example.com'],
        'Status': ['Confirmed', 'Pending', 'Cancelled', 'Completed', 'Confirmed', 'Pending'],
        'Event ID': ['EVT001', 'EVT002', 'EVT003', 'EVT004', 'EVT005', 'EVT006'],
        'Start Time (12hr)': ['10:00 AM', '2:00 PM', '11:00 AM', '3:00 PM', '9:00 AM', '4:00 PM'],
        'Start Time (24hr)': ['10:00', '14:00', '11:00', '15:00', '09:00', '16:00'],
        'Meet Link': ['https://meet.google.com/abc-defg-hij'] * 6,
        'Description': ['Team Standup Meeting', 'Client Presentation', 'Code Review Session', 'Training Workshop', 'Project Planning', 'Performance Review'],
        'Host': ['John', 'Jane', 'Bob', 'Alice', 'Charlie', 'Diana'],
        'Unique Code': ['UC001', 'UC002', 'UC003', 'UC004', 'UC005', 'UC006'],
        'Upload_Timestamp': [
            (now - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
            (now - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
            (now - timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S'),
            (now - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S'),
            now.strftime('%Y-%m-%d %H:%M:%S')
        ]
    })

def load_data_from_sheets(sheet_url):
    """Load data from Google Sheets"""
    if not st.session_state.get("global_gsheets_creds"):
        return None, None, "No global credentials found"
    
    creds = st.session_state.global_gsheets_creds
    try:
        creds_obj = ServiceAccountCredentials.from_json_keyfile_dict(creds, SHEET_SCOPE)
        client = gspread.authorize(creds_obj)
    except Exception as e:
        return None, None, f"Authentication failed: {e}"
    
    try:
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        spreadsheet = client.open_by_key(sheet_id)
    except Exception as e:
        return None, None, f"Spreadsheet access failed: {e}"
    
    try:
        worksheet = spreadsheet.get_worksheet(0)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data).dropna(how='all') if data else pd.DataFrame(columns=SHEET_COLUMNS)
        return df, (client, spreadsheet), None
    except Exception as e:
        return None, None, f"Error reading sheet: {e}"

def refresh_data():
    """Refresh data from Google Sheets or use sample data"""
    if st.session_state.get("global_gsheets_creds"):
        df, connection_info, err = load_data_from_sheets(STATIC_SHEET_URL)
        if err:
            st.session_state.connection_status = "error"
            st.session_state.error_message = err
        else:
            st.session_state.events_data = df
            if connection_info:
                st.session_state.client, st.session_state.spreadsheet = connection_info
            st.session_state.connection_status = "connected"
            st.session_state.error_message = None
    else:
        # Use sample data if no credentials
        st.session_state.events_data = create_sample_data()
        st.session_state.connection_status = "sample"
    
    st.session_state.last_refresh = datetime.now()

def get_appointment_time_status(start_time_24hr):
    """Determine if appointment is upcoming, current, or past"""
    try:
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        
        # Simple time comparison (assumes same day)
        if start_time_24hr == current_time:
            return "current"
        elif start_time_24hr > current_time:
            return "upcoming"
        else:
            return "past"
    except:
        return "unknown"

def render_appointment_card(row, index):
    """Render a beautiful appointment card"""
    time_status = get_appointment_time_status(row.get('Start Time (24hr)', ''))
    
    # Determine card class based on time status
    card_class = "appointment-card"
    if time_status == "current":
        card_class += " current-appointment"
    elif time_status == "upcoming":
        card_class += " upcoming-appointment"
    
    # Status badge class
    status = row.get('Status', '').lower()
    status_class = f"status-badge status-{status}"
    
    # Host initials for avatar
    host_name = row.get('Host', 'Unknown')
    host_initials = ''.join([name[0].upper() for name in host_name.split()[:2]])
    
    st.markdown(f"""
    <div class="{card_class}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
            <div style="display: flex; align-items: center;">
                <div class="host-avatar">{host_initials}</div>
                <div>
                    <h3 style="margin: 0; color: #2c3e50; font-size: 1.2rem;">{row.get('Name', 'N/A')}</h3>
                    <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">{row.get('Email', 'N/A')}</p>
                </div>
            </div>
            <div style="text-align: right;">
                <span class="{status_class}">{row.get('Status', 'N/A')}</span>
                <br>
                <small style="color: #7f8c8d;">ID: {row.get('Event ID', 'N/A')}</small>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
            <div class="time-display">
                <div class="time-large">{row.get('Start Time (12hr)', 'N/A')}</div>
                <small style="color: #6c757d;">Start Time</small>
            </div>
            <div style="padding: 1rem; background: #f8f9fa; border-radius: 10px;">
                <strong style="color: #495057;">Host:</strong> {row.get('Host', 'N/A')}<br>
                <strong style="color: #495057;">Code:</strong> {row.get('Unique Code', 'N/A')}
            </div>
        </div>
        
        {f'<div style="margin-bottom: 1rem;"><strong>Description:</strong> {row.get("Description", "No description")}</div>' if row.get('Description') else ''}
        
        {f'<div style="margin-bottom: 1rem;"><strong>Guest:</strong> {row.get("Guest Email", "No guest")}</div>' if row.get('Guest Email') else ''}
        
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <small style="color: #7f8c8d;">Updated: {row.get('Upload_Timestamp', 'N/A')}</small>
            {f'<a href="{row.get("Meet Link", "#")}" target="_blank" style="background: #007bff; color: white; padding: 0.5rem 1rem; border-radius: 5px; text-decoration: none; font-size: 0.9rem;">Join Meeting</a>' if row.get('Meet Link') else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------- Session State Initialization (AFTER helper functions) ----------
def initialize_session_state():
    """Initialize session state with default values"""
    defaults = {
        "connection_status": "sample",
        "events_data": create_sample_data() if 'events_data' not in st.session_state else st.session_state.events_data,
        "error_message": None,
        "client": None,
        "spreadsheet": None,
        "auto_refresh": False,
        "last_refresh": datetime.now()
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Initialize session state
initialize_session_state()

# ---------- Main Application ----------
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🚀 Live Appointments Dashboard</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Real-time appointment management and monitoring</p>
        <span class="live-indicator">
            <span class="live-dot"></span>
            LIVE
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Check for global credentials
    if not st.session_state.get("global_gsheets_creds"):
        st.error("🔑 Google Sheets credentials not found. Please upload your service account JSON in the sidebar.")
        st.info("💡 Use the sidebar to upload your service account JSON file. It will be used across all pages.")
        st.stop()
    
    # Sidebar controls
    with st.sidebar:
        st.header("🔧 Controls")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto Refresh (30s)", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh
        
        # Manual refresh button
        if st.button("🔄 Refresh Now", use_container_width=True):
            refresh_data()
            st.rerun()
        
        # Connection status
        st.markdown("---")
        st.subheader("📡 Connection Status")
        if st.session_state.connection_status == "connected":
            st.success("✅ Connected to Google Sheets")
        elif st.session_state.connection_status == "error":
            st.error("❌ Connection Error")
        else:
            st.info("💻 Using Sample Data")
        
        # Last refresh time
        if st.session_state.last_refresh:
            st.caption(f"Last updated: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    # Auto-refresh logic (simplified to avoid blocking)
    if st.session_state.auto_refresh:
        # Check if 30 seconds have passed since last refresh
        time_since_refresh = (datetime.now() - st.session_state.last_refresh).total_seconds()
        if time_since_refresh >= 30:
            refresh_data()
            st.rerun()
    
    # Load data if needed
    if st.session_state.connection_status == "sample" and st.session_state.get("global_gsheets_creds"):
        refresh_data()
    
    # Error handling
    if st.session_state.error_message and st.session_state.connection_status == "error":
        st.error("❌ Google Sheets Connection Failed")
        with st.expander("Error Details", expanded=True):
            st.write(st.session_state.error_message)
        st.info("Using sample data instead...")
        st.session_state.events_data = create_sample_data()
        st.session_state.connection_status = "sample"
    
    # Get data
    df = st.session_state.events_data.copy()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(df)}</div>
            <div class="metric-label">Total Appointments</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        confirmed_count = len(df[df['Status'] == 'Confirmed']) if 'Status' in df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{confirmed_count}</div>
            <div class="metric-label">Confirmed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        pending_count = len(df[df['Status'] == 'Pending']) if 'Status' in df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{pending_count}</div>
            <div class="metric-label">Pending</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        unique_hosts = df['Host'].nunique() if 'Host' in df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{unique_hosts}</div>
            <div class="metric-label">Active Hosts</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Filters
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_options = ['All'] + sorted(df['Status'].unique().tolist()) if 'Status' in df.columns else ['All']
        selected_status = st.selectbox("📊 Filter by Status", status_options)
    
    with col2:
        host_options = ['All'] + sorted(df['Host'].unique().tolist()) if 'Host' in df.columns else ['All']
        selected_host = st.selectbox("👤 Filter by Host", host_options)
    
    with col3:
        search_term = st.text_input("🔍 Search appointments", placeholder="Search by name, email, or description...")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_status != 'All':
        filtered_df = filtered_df[filtered_df['Status'] == selected_status]
    
    if selected_host != 'All':
        filtered_df = filtered_df[filtered_df['Host'] == selected_host]
    
    if search_term:
        search_columns = ['Name', 'Email', 'Description', 'Event ID']
        mask = filtered_df[search_columns].astype(str).apply(
            lambda x: x.str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        filtered_df = filtered_df[mask]
    
    # Results header
    st.markdown(f"""
    <h2 style="color: #2c3e50; margin: 2rem 0 1rem 0;">
        📅 Appointments ({len(filtered_df)} found)
    </h2>
    """, unsafe_allow_html=True)
    
    # Display appointments
    if filtered_df.empty:
        st.info("No appointments found matching your criteria.")
    else:
        # Sort by time for better organization
        if 'Start Time (24hr)' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('Start Time (24hr)')
        
        for index, row in filtered_df.iterrows():
            render_appointment_card(row, index)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #7f8c8d; padding: 1rem;">
        <p>🚀 Live Appointments Dashboard | Real-time updates every 30 seconds</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
