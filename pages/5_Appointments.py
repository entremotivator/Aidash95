import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# ---------- Configuration ----------
STATIC_SHEET_URL = "https://docs.google.com/spreadsheets/d/1mgToY7I10uwPrdPnjAO9gosgoaEKJCf7nv-E0-1UfVQ/edit"
SHEET_SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Expected sheet columns
SHEET_COLUMNS = [
    'Name', 'Email', 'Guest Email', 'Status', 'Event ID', 
    'Start Time (12hr)', 'Start Time (24hr)', 'Meet Link', 
    'Description', 'Host', 'Unique Code', 'Upload_Timestamp'
]

# ---------- Streamlit Page Settings ----------
st.set_page_config(
    page_title="🚀 Event Management CRM", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .confirmed { background-color: #28a745; color: white; }
    .pending { background-color: #ffc107; color: black; }
    .cancelled { background-color: #dc3545; color: white; }
    .completed { background-color: #6c757d; color: white; }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.375rem;
        color: #155724;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.375rem;
        color: #856404;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Event Management CRM")

# ---------- Helper Functions ----------
def append_to_sheet(data_dict):
    """Append new data to Google Sheet and refresh local data"""
    try:
        if st.session_state.get('spreadsheet') is None:
            return False, "No Google Sheets connection available"
        
        # Get the first worksheet (assuming single sheet)
        worksheet = st.session_state.spreadsheet.get_worksheet(0)
        
        # Convert dict to list in the order of expected columns
        row_data = [data_dict.get(col, '') for col in SHEET_COLUMNS]
        
        # Append the row
        worksheet.append_row(row_data)
        
        # Force refresh the data immediately
        refresh_data()
        
        return True, "Data added successfully!"
        
    except Exception as e:
        return False, str(e)

def refresh_data():
    """Refresh data from Google Sheets"""
    if st.session_state.get('spreadsheet') is not None:
        try:
            # Get the first worksheet
            worksheet = st.session_state.spreadsheet.get_worksheet(0)
            data = worksheet.get_all_records()
            
            if data:
                df = pd.DataFrame(data)
                # Clean up the data - remove empty rows
                df = df.dropna(how='all')
                st.session_state.events_data = df
            else:
                st.session_state.events_data = pd.DataFrame(columns=SHEET_COLUMNS)
                
        except Exception as e:
            st.error(f"Error refreshing data: {str(e)}")

def create_sample_data():
    """Create sample data matching the expected sheet structure"""
    return pd.DataFrame({
        'Name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'],
        'Email': ['john@email.com', 'jane@email.com', 'bob@email.com', 'alice@email.com'],
        'Guest Email': ['guest1@email.com', 'guest2@email.com', '', 'guest4@email.com'],
        'Status': ['Confirmed', 'Pending', 'Cancelled', 'Completed'],
        'Event ID': ['EVT001', 'EVT002', 'EVT003', 'EVT004'],
        'Start Time (12hr)': ['10:00 AM', '2:00 PM', '11:00 AM', '3:00 PM'],
        'Start Time (24hr)': ['10:00', '14:00', '11:00', '15:00'],
        'Meet Link': ['https://meet.google.com/abc-def-ghi', 'https://meet.google.com/jkl-mno-pqr', 
                     'https://meet.google.com/stu-vwx-yz1', 'https://meet.google.com/234-567-890'],
        'Description': ['Team standup meeting', 'Client presentation', 'Project review', 'Training session'],
        'Host': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'],
        'Unique Code': ['UC001', 'UC002', 'UC003', 'UC004'],
        'Upload_Timestamp': ['2024-01-15 09:00:00', '2024-01-16 13:00:00', '2024-01-17 10:00:00', '2024-01-18 14:00:00']
    })

# ---------- Initialize Session State ----------
def initialize_session_state():
    """Initialize session state variables"""
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'events_data' not in st.session_state:
        st.session_state.events_data = create_sample_data()
    if 'error_message' not in st.session_state:
        st.session_state.error_message = None
    if 'client' not in st.session_state:
        st.session_state.client = None
    if 'spreadsheet' not in st.session_state:
        st.session_state.spreadsheet = None
    if 'connection_status' not in st.session_state:
        st.session_state.connection_status = "sample"

# ---------- Sidebar Navigation ----------
def sidebar_navigation():
    st.sidebar.header("🔐 Authentication Status")
    
    if st.session_state.get("global_gsheets_creds"):
        st.sidebar.success("✅ Using Global Credentials")
        client_email = st.session_state.global_gsheets_creds.get('client_email', 'Unknown')
        st.sidebar.info(f"📧 {client_email[:30]}...")
    else:
        st.sidebar.error("❌ No global credentials")
        st.sidebar.info("Upload JSON in main sidebar")
    
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["📋 Dashboard", "📅 Events", "👥 Contacts", "📈 Analytics", "➕ Add Event", "⚙️ Settings"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("✅ **Data Source:**")
    
    if st.session_state.connection_status == "connected":
        st.sidebar.success("🔗 Google Sheets Connected")
        total_records = len(st.session_state.events_data)
        st.sidebar.info(f"📊 Total Records: {total_records}")
    elif st.session_state.connection_status == "error":
        st.sidebar.error("❌ Connection Error")
        st.sidebar.info("💻 Using Sample Data")
    else:
        st.sidebar.info("💻 Using Sample Data")
    
    return page

# Check for global credentials
if not st.session_state.get("global_gsheets_creds"):
    st.error("🔑 Google Sheets credentials not found. Please upload your service account JSON in the sidebar.")
    st.info("💡 Use the sidebar to upload your service account JSON file. It will be used across all pages.")
    st.stop()

def load_data_from_sheets(sheet_url):
    """Load data from Google Sheets with comprehensive error handling using global credentials"""
    try:
        creds_dict = st.session_state.global_gsheets_creds
        
        # Authenticate and connect
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SHEET_SCOPE)
            client = gspread.authorize(creds)
        except Exception as auth_error:
            return None, None, f"Authentication failed: {str(auth_error)}"
        
        # Extract sheet ID from URL and load data
        try:
            if '/d/' not in sheet_url:
                return None, None, "Invalid Google Sheets URL format."
            
            sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            if not sheet_id:
                return None, None, "Could not extract sheet ID from URL."
            
            spreadsheet = client.open_by_key(sheet_id)
        except gspread.SpreadsheetNotFound:
            return None, None, f"Spreadsheet not found. Please share with service account: {creds_dict.get('client_email', 'N/A')}"
        except Exception as sheet_error:
            return None, None, f"Error accessing spreadsheet: {str(sheet_error)}"
        
        # Load data from first worksheet
        try:
            worksheet = spreadsheet.get_worksheet(0)
            data = worksheet.get_all_records()
            
            if data:
                df = pd.DataFrame(data)
                df = df.dropna(how='all')
            else:
                df = pd.DataFrame(columns=SHEET_COLUMNS)
            
            return df, (client, spreadsheet), None
            
        except Exception as e:
            return None, None, f"Error loading worksheet data: {str(e)}"
    
    except Exception as e:
        return None, None, f"Unexpected error: {str(e)}"

# ---------- Page Functions ----------
def show_dashboard():
    st.header("📋 Dashboard Overview")
    
    events_data = st.session_state.events_data
    
    # Create metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_events = len(events_data)
        st.metric("📅 Total Events", total_events)
    
    with col2:
        if 'Status' in events_data.columns:
            confirmed_count = len(events_data[events_data['Status'] == 'Confirmed'])
            st.metric("✅ Confirmed", confirmed_count)
    
    with col3:
        if 'Status' in events_data.columns:
            pending_count = len(events_data[events_data['Status'] == 'Pending'])
            st.metric("⏳ Pending", pending_count)
    
    with col4:
        unique_hosts = events_data['Host'].nunique() if 'Host' in events_data.columns else 0
        st.metric("👤 Unique Hosts", unique_hosts)
    
    # Connection status
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.session_state.connection_status == "connected":
            st.success("🔗 Connected to Google Sheets - Data is live and synced")
        elif st.session_state.connection_status == "error":
            st.warning("⚠️ Using sample data - Google Sheets connection failed")
        else:
            st.info("💻 Using sample data - Upload service account JSON to connect")
    
    with col2:
        if st.session_state.connection_status == "connected":
            if st.button("🔄 Refresh Dashboard"):
                refresh_data()
                st.rerun()
    
    # Recent events
    st.subheader("📊 Recent Events")
    if len(events_data) > 0:
        # Show latest 10 events
        recent_events = events_data.head(10)
        
        # Display key columns
        display_cols = ['Name', 'Email', 'Status', 'Start Time (12hr)', 'Host', 'Event ID']
        available_cols = [col for col in display_cols if col in recent_events.columns]
        
        st.dataframe(recent_events[available_cols], use_container_width=True)
    else:
        st.info("No events data available")

def show_events():
    st.header("📅 Events Management")
    
    events_data = st.session_state.events_data
    
    if len(events_data) > 0:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'Status' in events_data.columns:
                status_options = ['All'] + list(events_data['Status'].unique())
                selected_status = st.selectbox("Filter by Status", status_options)
        
        with col2:
            if 'Host' in events_data.columns:
                host_options = ['All'] + list(events_data['Host'].unique())
                selected_host = st.selectbox("Filter by Host", host_options)
        
        with col3:
            search_term = st.text_input("Search Events", placeholder="Search by name, email, or event ID")
        
        # Apply filters
        filtered_data = events_data.copy()
        
        if 'Status' in events_data.columns and selected_status != 'All':
            filtered_data = filtered_data[filtered_data['Status'] == selected_status]
        
        if 'Host' in events_data.columns and selected_host != 'All':
            filtered_data = filtered_data[filtered_data['Host'] == selected_host]
        
        if search_term:
            # Search across multiple columns
            search_cols = ['Name', 'Email', 'Event ID', 'Description']
            mask = False
            for col in search_cols:
                if col in filtered_data.columns:
                    mask |= filtered_data[col].astype(str).str.contains(search_term, case=False, na=False)
            filtered_data = filtered_data[mask]
        
        st.subheader(f"📋 Events ({len(filtered_data)} found)")
        
        if len(filtered_data) > 0:
            # Display with expandable rows for full details
            for idx, row in filtered_data.iterrows():
                with st.expander(f"🎯 {row.get('Name', 'N/A')} - {row.get('Event ID', 'N/A')} ({row.get('Status', 'N/A')})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Name:** {row.get('Name', 'N/A')}")
                        st.write(f"**Email:** {row.get('Email', 'N/A')}")
                        st.write(f"**Guest Email:** {row.get('Guest Email', 'N/A')}")
                        st.write(f"**Status:** {row.get('Status', 'N/A')}")
                        st.write(f"**Event ID:** {row.get('Event ID', 'N/A')}")
                        st.write(f"**Host:** {row.get('Host', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Start Time (12hr):** {row.get('Start Time (12hr)', 'N/A')}")
                        st.write(f"**Start Time (24hr):** {row.get('Start Time (24hr)', 'N/A')}")
                        if row.get('Meet Link'):
                            st.write(f"**Meet Link:** [Join Meeting]({row.get('Meet Link')})")
                        st.write(f"**Unique Code:** {row.get('Unique Code', 'N/A')}")
                        st.write(f"**Upload Timestamp:** {row.get('Upload_Timestamp', 'N/A')}")
                        
                    if row.get('Description'):
                        st.write(f"**Description:** {row.get('Description', 'N/A')}")
        else:
            st.info("No events match the current filters")
    else:
        st.info("No events data available")

def show_contacts():
    st.header("👥 Contacts")
    
    events_data = st.session_state.events_data
    
    if len(events_data) > 0:
        # Extract unique contacts
        contacts = []
        for _, row in events_data.iterrows():
            # Main contact
            if row.get('Name') and row.get('Email'):
                contacts.append({
                    'Name': row.get('Name'),
                    'Email': row.get('Email'),
                    'Type': 'Primary',
                    'Events': 1
                })
            
            # Guest contact
            if row.get('Guest Email'):
                contacts.append({
                    'Name': 'Guest',
                    'Email': row.get('Guest Email'),
                    'Type': 'Guest',
                    'Events': 1
                })
        
        if contacts:
            contacts_df = pd.DataFrame(contacts)
            
            # Aggregate by email
            contacts_summary = contacts_df.groupby(['Name', 'Email', 'Type']).agg({
                'Events': 'sum'
            }).reset_index()
            
            st.subheader(f"📋 Contacts Summary ({len(contacts_summary)} unique contacts)")
            st.dataframe(contacts_summary, use_container_width=True)
            
            # Contact details
            st.subheader("📧 All Contact Entries")
            for _, row in events_data.iterrows():
                with st.expander(f"📧 {row.get('Name', 'N/A')} ({row.get('Email', 'N/A')})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Name:** {row.get('Name', 'N/A')}")
                        st.write(f"**Email:** {row.get('Email', 'N/A')}")
                        st.write(f"**Guest Email:** {row.get('Guest Email', 'N/A')}")
                    with col2:
                        st.write(f"**Event ID:** {row.get('Event ID', 'N/A')}")
                        st.write(f"**Status:** {row.get('Status', 'N/A')}")
                        st.write(f"**Host:** {row.get('Host', 'N/A')}")
        else:
            st.info("No contact information available")
    else:
        st.info("No contacts data available")

def show_analytics():
    st.header("📈 Analytics")
    
    events_data = st.session_state.events_data
    
    if len(events_data) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            # Status distribution
            if 'Status' in events_data.columns:
                status_counts = events_data['Status'].value_counts()
                fig = px.pie(values=status_counts.values, names=status_counts.index, 
                           title="Event Status Distribution")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Host distribution
            if 'Host' in events_data.columns:
                host_counts = events_data['Host'].value_counts().head(10)
                fig = px.bar(x=host_counts.values, y=host_counts.index, 
                           orientation='h', title="Top 10 Hosts by Event Count")
                st.plotly_chart(fig, use_container_width=True)
        
        # Timeline analysis
        if 'Upload_Timestamp' in events_data.columns:
            st.subheader("📅 Events Timeline")
            try:
                # Convert timestamp to datetime
                events_data['Upload_Date'] = pd.to_datetime(events_data['Upload_Timestamp'], errors='coerce')
                events_data['Upload_Date'] = events_data['Upload_Date'].dt.date
                
                timeline_counts = events_data['Upload_Date'].value_counts().sort_index()
                
                fig = px.line(x=timeline_counts.index, y=timeline_counts.values,
                            title="Events Created Over Time",
                            labels={'x': 'Date', 'y': 'Number of Events'})
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating timeline: {str(e)}")
        
        # Summary statistics
        st.subheader("📊 Summary Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Events", len(events_data))
        
        with col2:
            if 'Host' in events_data.columns:
                unique_hosts = events_data['Host'].nunique()
                st.metric("Unique Hosts", unique_hosts)
        
        with col3:
            if 'Email' in events_data.columns:
                unique_emails = events_data['Email'].nunique()
                st.metric("Unique Participants", unique_emails)
    else:
        st.info("No data available for analytics")

def show_add_event():
    st.header("➕ Add New Event")
    
    with st.form("add_event_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name*")
            email = st.text_input("Email*")
            guest_email = st.text_input("Guest Email (optional)")
            status = st.selectbox("Status", ["Confirmed", "Pending", "Cancelled", "Completed"])
            event_id = st.text_input("Event ID*")
            unique_code = st.text_input("Unique Code*")
        
        with col2:
            start_time_12hr = st.text_input("Start Time (12hr)*", placeholder="e.g., 10:00 AM")
            start_time_24hr = st.text_input("Start Time (24hr)*", placeholder="e.g., 10:00")
            meet_link = st.text_input("Meet Link (optional)")
            host = st.text_input("Host*")
            description = st.text_area("Description (optional)")
        
        submitted = st.form_submit_button("Add Event")
        
        if submitted:
            if name and email and event_id and start_time_12hr and start_time_24hr and host and unique_code:
                new_event = {
                    'Name': name,
                    'Email': email,
                    'Guest Email': guest_email,
                    'Status': status,
                    'Event ID': event_id,
                    'Start Time (12hr)': start_time_12hr,
                    'Start Time (24hr)': start_time_24hr,
                    'Meet Link': meet_link,
                    'Description': description,
                    'Host': host,
                    'Unique Code': unique_code,
                    'Upload_Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                if st.session_state.connection_status == "connected":
                    success, message = append_to_sheet(new_event)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(f"Error adding event: {message}")
                else:
                    st.warning("Google Sheets not connected. Event added to local data only.")
                    # Add to local data
                    new_row = pd.DataFrame([new_event])
                    st.session_state.events_data = pd.concat([st.session_state.events_data, new_row], ignore_index=True)
                    st.success("Event added to local data!")
                    st.rerun()
            else:
                st.error("Please fill in all required fields (marked with *)")

def show_settings():
    st.header("⚙️ Settings")
    
    st.subheader("📋 Expected Sheet Structure")
    st.write("Your Google Sheet should have the following columns in this exact order:")
    
    for i, col in enumerate(SHEET_COLUMNS, 1):
        st.write(f"{i}. **{col}**")
    
    st.subheader("🔗 Current Configuration")
    st.code(f"Sheet URL: {STATIC_SHEET_URL}")
    
    st.subheader("📊 Current Data Info")
    if st.session_state.connection_status == "connected":
        st.success("✅ Connected to Google Sheets")
        st.info(f"Records loaded: {len(st.session_state.events_data)}")
    else:
        st.info("💻 Using sample data")
    
    # Show current data columns
    if len(st.session_state.events_data) > 0:
        st.subheader("📋 Available Columns in Data")
        cols = list(st.session_state.events_data.columns)
        for col in cols:
            st.write(f"• {col}")
    
    # Data preview
    st.subheader("👀 Data Preview")
    if len(st.session_state.events_data) > 0:
        st.dataframe(st.session_state.events_data.head(), use_container_width=True)
    else:
        st.info("No data to preview")

# ---------- Main Application ----------
def main():
    # Get current page from sidebar
    current_page = sidebar_navigation()
    
    # Show error information if connection failed
    if st.session_state.error_message and st.session_state.connection_status == "error":
        st.error("🚫 **Google Sheets Connection Failed**")
        
        with st.expander("🔍 **Error Details**", expanded=False):
            st.error(f"**Error:** {st.session_state.error_message}")
            st.info("💡 **Don't worry!** You can still use the app with sample data while troubleshooting.")
        
        st.markdown("---")
    
    # Route to appropriate page
    if current_page == "📋 Dashboard":
        show_dashboard()
    elif current_page == "📅 Events":
        show_events()
    elif current_page == "👥 Contacts":
        show_contacts()
    elif current_page == "📈 Analytics":
        show_analytics()
    elif current_page == "➕ Add Event":
        show_add_event()
    elif current_page == "⚙️ Settings":
        show_settings()

# ---------- Run Application ----------
if __name__ == "__main__":
    main()
