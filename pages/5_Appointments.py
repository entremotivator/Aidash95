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
import random

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
        opacity: 0.3;
    }
    
    .main-header h1 {
        position: relative;
        z-index: 1;
        margin: 0;
        font-size: 3rem;
        font-weight: 700;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    .main-header p {
        position: relative;
        z-index: 1;
        margin: 1rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.95;
        font-weight: 400;
    }
    
    /* Appointment cards with enhanced design */
    .appointment-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        border: 1px solid rgba(255,255,255,0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .appointment-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 5px;
        height: 100%;
        background: linear-gradient(180deg, #667eea, #764ba2);
        transition: width 0.3s ease;
    }
    
    .appointment-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 60px rgba(0,0,0,0.15);
    }
    
    .appointment-card:hover::before {
        width: 8px;
    }
    
    /* Status badges with premium styling */
    .status-badge {
        padding: 0.6rem 1.5rem;
        border-radius: 30px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0.3rem;
        position: relative;
        overflow: hidden;
    }
    
    .status-badge::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.5s;
    }
    
    .status-badge:hover::before {
        left: 100%;
    }
    
    .status-confirmed { 
        background: linear-gradient(135deg, #28a745, #20c997, #17a2b8);
        color: white;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.4);
    }
    
    .status-pending { 
        background: linear-gradient(135deg, #ffc107, #fd7e14, #e83e8c);
        color: #212529;
        box-shadow: 0 4px 15px rgba(255, 193, 7, 0.4);
    }
    
    .status-cancelled { 
        background: linear-gradient(135deg, #dc3545, #e83e8c, #6f42c1);
        color: white;
        box-shadow: 0 4px 15px rgba(220, 53, 69, 0.4);
    }
    
    .status-completed { 
        background: linear-gradient(135deg, #6c757d, #495057, #343a40);
        color: white;
        box-shadow: 0 4px 15px rgba(108, 117, 125, 0.4);
    }
    
    /* Premium metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
        transition: transform 0.3s ease;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: shimmer 3s ease-in-out infinite;
    }
    
    @keyframes shimmer {
        0%, 100% { transform: rotate(0deg); }
        50% { transform: rotate(180deg); }
    }
    
    .metric-card:hover {
        transform: scale(1.05) rotateY(5deg);
    }
    
    .metric-value {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        position: relative;
        z-index: 1;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.95;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 500;
        position: relative;
        z-index: 1;
    }
    
    /* Enhanced live indicator */
    .live-indicator {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        padding: 0.8rem 1.5rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: 600;
        margin-left: 1rem;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
        position: relative;
        z-index: 1;
    }
    
    .live-dot {
        width: 10px;
        height: 10px;
        background: white;
        border-radius: 50%;
        margin-right: 0.8rem;
        animation: livePulse 2s infinite;
        box-shadow: 0 0 10px rgba(255,255,255,0.5);
    }
    
    @keyframes livePulse {
        0%, 100% { 
            opacity: 1; 
            transform: scale(1);
        }
        50% { 
            opacity: 0.6; 
            transform: scale(1.2);
        }
    }
    
    /* Enhanced filter container */
    .filter-container {
        background: linear-gradient(135deg, #f8f9fa, #ffffff);
        padding: 2rem;
        border-radius: 20px;
        margin: 2rem 0;
        border: 1px solid #e9ecef;
        box-shadow: 0 5px 20px rgba(0,0,0,0.05);
    }
    
    /* Special appointment highlights */
    .upcoming-appointment {
        background: linear-gradient(145deg, #fff3cd, #ffffff);
        border-left: 6px solid #ffc107;
        animation: upcomingGlow 3s ease-in-out infinite alternate;
    }
    
    @keyframes upcomingGlow {
        from { box-shadow: 0 8px 32px rgba(255, 193, 7, 0.2); }
        to { box-shadow: 0 12px 40px rgba(255, 193, 7, 0.4); }
    }
    
    .current-appointment {
        background: linear-gradient(145deg, #d4edda, #ffffff);
        border-left: 6px solid #28a745;
        animation: currentPulse 2s ease-in-out infinite alternate;
    }
    
    @keyframes currentPulse {
        from { 
            box-shadow: 0 8px 32px rgba(40, 167, 69, 0.3);
            transform: scale(1);
        }
        to { 
            box-shadow: 0 15px 50px rgba(40, 167, 69, 0.5);
            transform: scale(1.02);
        }
    }
    
    .priority-appointment {
        background: linear-gradient(145deg, #f8d7da, #ffffff);
        border-left: 6px solid #dc3545;
        position: relative;
    }
    
    .priority-appointment::after {
        content: '🔥';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
        animation: bounce 2s infinite;
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
        60% { transform: translateY(-5px); }
    }
    
    /* Enhanced footer */
    .dashboard-footer {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-top: 3rem;
        border: 1px solid #dee2e6;
    }
    
    /* Responsive design improvements */
    @media (max-width: 768px) {
        .main-header h1 { font-size: 2rem; }
        .appointment-card { padding: 1.5rem; margin: 1rem 0; }
        .metric-value { font-size: 2rem; }
    }
</style>
""", unsafe_allow_html=True)

# ---------- Helper Functions ----------
def create_sample_data():
    """Create comprehensive sample appointment data"""
    now = datetime.now()
    
    # Extended sample data with more variety
    names = [
        'John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Wilson', 
        'Diana Prince', 'Edward Norton', 'Fiona Green', 'George Miller', 'Helen Davis',
        'Ian Thompson', 'Julia Roberts', 'Kevin Hart', 'Lisa Anderson', 'Mike Chen',
        'Nancy Wilson', 'Oscar Martinez', 'Patricia Lee', 'Quincy Adams', 'Rachel Green'
    ]
    
    emails = [f"{name.lower().replace(' ', '.')}.{random.randint(100,999)}@company.com" for name in names]
    
    statuses = ['Confirmed', 'Pending', 'Cancelled', 'Completed']
    
    descriptions = [
        'Strategic Planning Session - Q4 Goals Review',
        'Client Presentation - New Product Launch',
        'Team Building Workshop - Communication Skills',
        'Performance Review - Annual Assessment',
        'Project Kickoff Meeting - Digital Transformation',
        'Training Session - Advanced Analytics',
        'Board Meeting - Financial Review',
        'Customer Success Review - Account Health',
        'Technical Architecture Discussion',
        'Marketing Campaign Planning Session',
        'Sales Pipeline Review Meeting',
        'Product Development Sync',
        'Quality Assurance Review',
        'Compliance Training Workshop',
        'Innovation Brainstorming Session',
        'Budget Planning Meeting',
        'Risk Assessment Review',
        'Partnership Discussion',
        'Vendor Evaluation Meeting',
        'Employee Onboarding Session'
    ]
    
    hosts = ['John Smith', 'Sarah Johnson', 'Mike Davis', 'Emily Chen', 'David Wilson', 'Lisa Brown']
    
    # Generate appointments for the next 7 days
    appointments = []
    for i in range(25):
        # Random date within next 7 days
        days_ahead = random.randint(0, 7)
        appointment_date = now + timedelta(days=days_ahead)
        
        # Random time between 9 AM and 6 PM
        hour = random.randint(9, 17)
        minute = random.choice([0, 15, 30, 45])
        appointment_date = appointment_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        name = names[i % len(names)]
        email = emails[i % len(emails)]
        status = random.choice(statuses)
        description = descriptions[i % len(descriptions)]
        host = random.choice(hosts)
        
        appointments.append({
            'Name': name,
            'Email': email,
            'Guest Email': f"guest{i+1}@external.com" if random.random() > 0.4 else '',
            'Status': status,
            'Event ID': f'EVT{str(i+1).zfill(3)}',
            'Start Time (12hr)': appointment_date.strftime('%I:%M %p'),
            'Start Time (24hr)': appointment_date.strftime('%H:%M'),
            'Meet Link': f'https://meet.google.com/abc-defg-{random.randint(100,999)}',
            'Description': description,
            'Host': host,
            'Unique Code': f'UC{str(i+1).zfill(3)}',
            'Upload_Timestamp': (now - timedelta(minutes=random.randint(5, 1440))).strftime('%Y-%m-%d %H:%M:%S'),
            'Date': appointment_date.strftime('%Y-%m-%d'),
            'Priority': random.choice(['High', 'Medium', 'Low']),
            'Duration': random.choice(['30 min', '45 min', '1 hour', '1.5 hours', '2 hours']),
            'Location': random.choice(['Conference Room A', 'Conference Room B', 'Virtual', 'Office 101', 'Meeting Hall'])
        })
    
    return pd.DataFrame(appointments)

def load_data_from_sheets(sheet_url):
    """Load data from Google Sheets with enhanced error handling"""
    if not st.session_state.get("global_gsheets_creds"):
        return None, None, "No global credentials found"
    
    creds = st.session_state.global_gsheets_creds
    try:
        creds_obj = ServiceAccountCredentials.from_json_keyfile_dict(creds, SHEET_SCOPE)
        client = gspread.authorize(creds_obj)
    except Exception as e:
        return None, None, f"Authentication failed: {str(e)}"
    
    try:
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        spreadsheet = client.open_by_key(sheet_id)
    except Exception as e:
        return None, None, f"Spreadsheet access failed: {str(e)}"
    
    try:
        worksheet = spreadsheet.get_worksheet(0)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data).dropna(how='all') if data else pd.DataFrame(columns=SHEET_COLUMNS)
        return df, (client, spreadsheet), None
    except Exception as e:
        return None, None, f"Error reading sheet: {str(e)}"

def refresh_data():
    """Refresh data with progress indication"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text('🔄 Connecting to Google Sheets...')
        progress_bar.progress(25)
        
        if st.session_state.get("global_gsheets_creds"):
            df, connection_info, err = load_data_from_sheets(STATIC_SHEET_URL)
            progress_bar.progress(75)
            
            if err:
                st.session_state.connection_status = "error"
                st.session_state.error_message = err
                status_text.text('❌ Connection failed, using sample data')
                st.session_state.events_data = create_sample_data()
            else:
                st.session_state.events_data = df
                if connection_info:
                    st.session_state.client, st.session_state.spreadsheet = connection_info
                st.session_state.connection_status = "connected"
                st.session_state.error_message = None
                status_text.text('✅ Data loaded successfully')
        else:
            st.session_state.events_data = create_sample_data()
            st.session_state.connection_status = "sample"
            status_text.text('💻 Using sample data')
        
        progress_bar.progress(100)
        st.session_state.last_refresh = datetime.now()
        
        # Clear progress indicators after a short delay
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Unexpected error: {str(e)}")

def get_appointment_priority_class(row):
    """Determine appointment card class based on various factors"""
    now = datetime.now()
    start_time = row.get('Start Time (24hr)', '')
    status = row.get('Status', '').lower()
    priority = row.get('Priority', 'Medium').lower()
    
    base_class = "appointment-card"
    
    try:
        # Parse appointment time
        hour, minute = map(int, start_time.split(':'))
        appointment_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        time_diff = (appointment_time - now).total_seconds() / 60
        
        # Determine special classes
        if -15 <= time_diff <= 15:  # Current appointment
            return f"{base_class} current-appointment"
        elif 0 < time_diff <= 60:  # Upcoming in next hour
            return f"{base_class} upcoming-appointment"
        elif priority == 'high':  # High priority
            return f"{base_class} priority-appointment"
    except:
        pass
    
    return base_class

def render_appointment_card_streamlit(row, index):
    """Render appointment card using pure Streamlit components"""
    card_class = get_appointment_priority_class(row)
    
    # Status styling
    status = row.get('Status', '').lower()
    status_class = f"status-badge status-{status}"
    
    # Priority indicator
    priority = row.get('Priority', 'Medium')
    priority_colors = {
        'High': '🔴',
        'Medium': '🟡', 
        'Low': '🟢'
    }
    priority_icon = priority_colors.get(priority, '⚪')
    
    # Time until appointment
    try:
        now = datetime.now()
        start_time = row.get('Start Time (24hr)', '')
        hour, minute = map(int, start_time.split(':'))
        appointment_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        time_diff = appointment_time - now
        
        if time_diff.total_seconds() > 0:
            hours = int(time_diff.total_seconds() // 3600)
            minutes = int((time_diff.total_seconds() % 3600) // 60)
            time_until = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            time_status = "⏰ Upcoming"
        else:
            time_until = "Now" if abs(time_diff.total_seconds()) <= 900 else "Past"
            time_status = "🔴 Current" if time_until == "Now" else "✅ Past"
    except:
        time_until = "Unknown"
        time_status = "❓ Unknown"
    
    # Create the card using Streamlit components
    with st.container():
        # Apply custom CSS class
        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
        
        # Header section with name, email, and status
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Host initials
            host_name = row.get('Host', 'Unknown')
            host_initials = ''.join([name[0].upper() for name in host_name.split()[:2]])
            
            st.markdown(f"### 👤 {host_initials} | {row.get('Name', 'N/A')}")
            st.markdown(f"**📧 Email:** {row.get('Email', 'N/A')}")
            st.markdown(f"**{priority_icon} Priority:** {priority}")
        
        with col2:
            # Status badge
            st.markdown(f'<span class="{status_class}">{row.get("Status", "N/A")}</span>', unsafe_allow_html=True)
            st.markdown(f"**🆔 ID:** {row.get('Event ID', 'N/A')}")
        
        st.markdown("---")
        
        # Time and duration section
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### ⏰ Start Time")
            st.markdown(f"**{row.get('Start Time (12hr)', 'N/A')}**")
            st.caption("Scheduled start")
        
        with col2:
            st.markdown("#### ⏱️ Duration")
            st.markdown(f"**{row.get('Duration', '1 hour')}**")
            st.caption("Meeting length")
        
        with col3:
            st.markdown("#### 🕐 Time Until")
            st.markdown(f"**{time_until}**")
            st.caption(time_status)
        
        st.markdown("---")
        
        # Information section
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📋 Meeting Details")
            st.markdown(f"**👤 Host:** {row.get('Host', 'N/A')}")
            st.markdown(f"**📍 Location:** {row.get('Location', 'Virtual')}")
            st.markdown(f"**🔑 Access Code:** `{row.get('Unique Code', 'N/A')}`")
            st.markdown(f"**📅 Date:** {row.get('Date', 'N/A')}")
        
        with col2:
            st.markdown("#### 👥 Participants")
            if row.get('Guest Email'):
                guest_initial = row.get('Guest Email', '').split('@')[0][0].upper() if row.get('Guest Email') else 'G'
                st.markdown(f"**👤 Guest:** {guest_initial} | {row.get('Guest Email', 'No guest')}")
            else:
                st.markdown("**👤 Guest:** No guest invited")
            
            st.markdown(f"**📊 Status:** {row.get('Status', 'N/A')}")
            st.markdown(f"**⚡ Priority:** {priority} {priority_icon}")
        
        # Description section
        if row.get('Description'):
            st.markdown("#### 📝 Description")
            st.info(row.get('Description', 'No description provided'))
        
        # Action buttons section
        st.markdown("#### 🎯 Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if row.get('Meet Link'):
                st.markdown(f"[🎥 Join Meeting]({row.get('Meet Link', '#')})")
            else:
                st.markdown("🎥 No meeting link")
        
        with col2:
            if st.button(f"📝 Edit", key=f"edit_{index}"):
                st.info(f"Edit functionality for {row.get('Event ID', 'N/A')}")
        
        with col3:
            if st.button(f"📧 Remind", key=f"remind_{index}"):
                st.success(f"Reminder sent for {row.get('Event ID', 'N/A')}")
        
        with col4:
            if st.button(f"📋 Details", key=f"details_{index}"):
                st.json({
                    "Event ID": row.get('Event ID', 'N/A'),
                    "Name": row.get('Name', 'N/A'),
                    "Status": row.get('Status', 'N/A'),
                    "Time": row.get('Start Time (12hr)', 'N/A'),
                    "Host": row.get('Host', 'N/A')
                })
        
        # Footer with timestamp
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.caption(f"🕐 Last updated: {row.get('Upload_Timestamp', 'N/A')}")
        
        with col2:
            st.caption(f"📊 Status: {time_status}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

# ---------- Session State Initialization ----------
def initialize_session_state():
    """Initialize session state with comprehensive defaults"""
    defaults = {
        "connection_status": "sample",
        "events_data": create_sample_data() if 'events_data' not in st.session_state else st.session_state.events_data,
        "error_message": None,
        "client": None,
        "spreadsheet": None,
        "auto_refresh": False,
        "last_refresh": datetime.now(),
        "filter_date_range": "all"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Initialize session state
initialize_session_state()

# ---------- Main Application ----------
def main():
    # Enhanced Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Live Appointments Dashboard</h1>
        <p>Advanced real-time appointment management and monitoring system</p>
        <span class="live-indicator">
            <span class="live-dot"></span>
            LIVE UPDATES ACTIVE
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Check for global credentials
    if not st.session_state.get("global_gsheets_creds"):
        st.error("🔑 Google Sheets credentials not found. Please upload your service account JSON in the main application.")
        st.info("💡 Navigate to the main dashboard to upload your service account JSON file for full functionality.")
        st.markdown("---")
        st.info("🎯 **Demo Mode Active** - Using sample data for demonstration purposes")
    
    # Enhanced Sidebar Controls
    with st.sidebar:
        st.markdown("# 🎛️ Dashboard Controls")
        
        # Auto-refresh controls
        st.markdown("### ⚡ Live Updates")
        auto_refresh = st.checkbox("Enable Auto-Refresh", value=st.session_state.auto_refresh, help="Automatically refresh data every 30 seconds")
        st.session_state.auto_refresh = auto_refresh
        
        refresh_interval = st.selectbox(
            "Refresh Interval",
            [15, 30, 60, 120],
            index=1,
            format_func=lambda x: f"{x} seconds"
        )
        
        # Manual refresh with progress
        if st.button("🔄 Refresh Data Now", use_container_width=True, type="primary"):
            refresh_data()
            st.rerun()
        
        st.markdown("---")
        
        # Date range filter
        date_filter = st.selectbox(
            "📅 Date Range",
            ["all", "today", "tomorrow", "this_week", "next_week"],
            format_func=lambda x: {
                "all": "📅 All Dates",
                "today": "📍 Today Only",
                "tomorrow": "➡️ Tomorrow Only",
                "this_week": "📆 This Week",
                "next_week": "📅 Next Week"
            }[x]
        )
        st.session_state.filter_date_range = date_filter
        
        st.markdown("---")
        
        # Connection status with enhanced display
        st.markdown("### 📡 System Status")
        status_container = st.container()
        
        with status_container:
            if st.session_state.connection_status == "connected":
                st.success("✅ Google Sheets Connected")
                st.caption("🔗 Live data synchronization active")
            elif st.session_state.connection_status == "error":
                st.error("❌ Connection Error")
                st.caption("⚠️ Using cached/sample data")
            else:
                st.info("💻 Demo Mode")
                st.caption("🎯 Using sample data for demonstration")
        
        # Last refresh time with countdown
        if st.session_state.last_refresh:
            time_since = (datetime.now() - st.session_state.last_refresh).seconds
            st.caption(f"🕐 Last updated: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
            if st.session_state.auto_refresh and time_since < refresh_interval:
                remaining = refresh_interval - time_since
                st.caption(f"⏱️ Next refresh in: {remaining}s")
        
        st.markdown("---")
        
        # Quick stats in sidebar
        df = st.session_state.events_data
        st.markdown("### 📈 Quick Stats")
        st.metric("Total Appointments", len(df))
        if 'Status' in df.columns:
            st.metric("Confirmed Today", len(df[(df['Status'] == 'Confirmed') & (df['Date'] == datetime.now().strftime('%Y-%m-%d'))]))
            st.metric("Pending Review", len(df[df['Status'] == 'Pending']))
    
    # Auto-refresh logic
    if st.session_state.auto_refresh:
        time_since_refresh = (datetime.now() - st.session_state.last_refresh).total_seconds()
        if time_since_refresh >= refresh_interval:
            refresh_data()
            st.rerun()
    
    # Load initial data
    if st.session_state.connection_status == "sample" and st.session_state.get("global_gsheets_creds"):
        refresh_data()
    
    # Error handling with detailed information
    if st.session_state.error_message and st.session_state.connection_status == "error":
        st.error("❌ Google Sheets Connection Failed")
        with st.expander("🔍 Error Details & Troubleshooting", expanded=False):
            st.code(st.session_state.error_message)
            st.markdown("""
            **Common Solutions:**
            - Verify your service account JSON file is valid
            - Check if the Google Sheet URL is accessible
            - Ensure the service account has proper permissions
            - Try refreshing the connection
            """)
        st.info("🔄 Automatically switched to demo mode with sample data")
        st.session_state.events_data = create_sample_data()
        st.session_state.connection_status = "sample"
    
    # Get and process data
    df = st.session_state.events_data.copy()
    
    # Apply date filtering
    if st.session_state.filter_date_range != "all":
        today = datetime.now().date()
        if st.session_state.filter_date_range == "today":
            df = df[df['Date'] == today.strftime('%Y-%m-%d')]
        elif st.session_state.filter_date_range == "tomorrow":
            tomorrow = today + timedelta(days=1)
            df = df[df['Date'] == tomorrow.strftime('%Y-%m-%d')]
        elif st.session_state.filter_date_range == "this_week":
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            df = df[(df['Date'] >= week_start.strftime('%Y-%m-%d')) & (df['Date'] <= week_end.strftime('%Y-%m-%d'))]
        elif st.session_state.filter_date_range == "next_week":
            next_week_start = today + timedelta(days=7-today.weekday())
            next_week_end = next_week_start + timedelta(days=6)
            df = df[(df['Date'] >= next_week_start.strftime('%Y-%m-%d')) & (df['Date'] <= next_week_end.strftime('%Y-%m-%d'))]
    
    # Enhanced Metrics Dashboard
    st.markdown("## 📊 Real-Time Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
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
    
    with col5:
        high_priority = len(df[df['Priority'] == 'High']) if 'Priority' in df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{high_priority}</div>
            <div class="metric-label">High Priority</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced Filters Section
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    st.markdown("## 🔍 Advanced Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_options = ['All'] + sorted(df['Status'].unique().tolist()) if 'Status' in df.columns else ['All']
        selected_status = st.selectbox("📊 Status Filter", status_options)
    
    with col2:
        host_options = ['All'] + sorted(df['Host'].unique().tolist()) if 'Host' in df.columns else ['All']
        selected_host = st.selectbox("👤 Host Filter", host_options)
    
    with col3:
        priority_options = ['All'] + sorted(df['Priority'].unique().tolist()) if 'Priority' in df.columns else ['All']
        selected_priority = st.selectbox("⚡ Priority Filter", priority_options)
    
    with col4:
        search_term = st.text_input("🔍 Search", placeholder="Search appointments...", help="Search by name, email, description, or event ID")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply all filters
    filtered_df = df.copy()
    
    if selected_status != 'All':
        filtered_df = filtered_df[filtered_df['Status'] == selected_status]
    
    if selected_host != 'All':
        filtered_df = filtered_df[filtered_df['Host'] == selected_host]
    
    if selected_priority != 'All':
        filtered_df = filtered_df[filtered_df['Priority'] == selected_priority]
    
    if search_term:
        search_columns = ['Name', 'Email', 'Description', 'Event ID', 'Location']
        mask = filtered_df[search_columns].astype(str).apply(
            lambda x: x.str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        filtered_df = filtered_df[mask]
    
    # Appointments Display Section
    st.markdown(f"""
    ## 📅 Live Appointments ({len(filtered_df)} found)
    """)
    
    if filtered_df.empty:
        st.warning("📭 No appointments found matching your criteria. Try adjusting your filters.")
    else:
        # Sort appointments by date and time
        if 'Date' in filtered_df.columns and 'Start Time (24hr)' in filtered_df.columns:
            filtered_df['datetime_sort'] = pd.to_datetime(filtered_df['Date'] + ' ' + filtered_df['Start Time (24hr)'])
            filtered_df = filtered_df.sort_values('datetime_sort')
        
        # Group appointments by date for better organization
        if 'Date' in filtered_df.columns:
            for date, group in filtered_df.groupby('Date'):
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                day_name = date_obj.strftime('%A')
                formatted_date = date_obj.strftime('%B %d, %Y')
                
                # Date header
                st.markdown(f"""
                ### 📅 {day_name} - {formatted_date}
                **{len(group)} appointments scheduled**
                """)
                
                # Render appointments for this date
                for index, row in group.iterrows():
                    render_appointment_card_streamlit(row, index)
        else:
            # Fallback: render all appointments without date grouping
            for index, row in filtered_df.iterrows():
                render_appointment_card_streamlit(row, index)
    
    # Enhanced Footer
    st.markdown(f"""
    <div class="dashboard-footer">
        <h3 style="margin: 0 0 1rem 0; color: #495057;">🚀 Live Appointments Dashboard</h3>
        <p style="margin: 0; color: #6c757d; font-size: 1rem;">
            Real-time appointment management • Advanced filtering • Live updates every {refresh_interval} seconds
        </p>
        <div style="margin-top: 1rem; display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
            <span style="color: #28a745;">● Connected</span>
            <span style="color: #17a2b8;">● {len(df)} Total Records</span>
            <span style="color: #6f42c1;">● Last Updated: {st.session_state.last_refresh.strftime('%H:%M:%S')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
