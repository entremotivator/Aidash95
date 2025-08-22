import streamlit as st
import gspread
import pandas as pd
import json
from datetime import datetime
from google.oauth2.service_account import Credentials
import time
import html

# Page configuration
st.set_page_config(
    page_title="Email Campaign Dashboard",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for email cards and body display
st.markdown("""
<style>
    .email-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s ease-in-out;
    }
    
    .email-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .sender-info {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        flex-wrap: wrap;
        gap: 10px;
    }
    
    .sender-name {
        font-weight: bold;
        font-size: 16px;
        color: #1f2937;
    }
    
    .sender-email {
        color: #6b7280;
        font-size: 14px;
    }
    
    .subject {
        font-size: 18px;
        font-weight: 600;
        color: #111827;
        margin-bottom: 10px;
        line-height: 1.4;
    }
    
    .email-meta {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 10px;
        font-size: 12px;
        color: #6b7280;
        border-top: 1px solid #f3f4f6;
        padding-top: 10px;
        margin-top: 15px;
    }
    
    .meta-item {
        display: flex;
        flex-direction: column;
    }
    
    .meta-label {
        font-weight: 600;
        color: #374151;
        margin-bottom: 2px;
    }
    
    .meta-value {
        color: #6b7280;
    }
    
    .date {
        font-weight: 500;
    }
    
    .stats-container {
        display: flex;
        gap: 20px;
        margin-bottom: 30px;
        flex-wrap: wrap;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        flex: 1;
        min-width: 150px;
    }
    
    .stat-number {
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .stat-label {
        font-size: 14px;
        opacity: 0.9;
    }
    
    .email-body-container {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        margin-top: 15px;
        max-height: 400px;
        overflow-y: auto;
    }
    
    .email-body-html {
        background: white;
        padding: 15px;
        border-radius: 6px;
        border: 1px solid #d1d5db;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        line-height: 1.6;
    }
    
    .email-body-raw {
        background: #1f2937;
        color: #f9fafb;
        padding: 15px;
        border-radius: 6px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        white-space: pre-wrap;
        overflow-x: auto;
    }
    
    .view-body-btn {
        background: #3b82f6;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 14px;
        margin-top: 10px;
    }
    
    .view-body-btn:hover {
        background: #2563eb;
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .status-sent {
        background: #dcfce7;
        color: #166534;
    }
    
    .status-pending {
        background: #fef3c7;
        color: #92400e;
    }
    
    .status-failed {
        background: #fecaca;
        color: #991b1b;
    }
</style>
""", unsafe_allow_html=True)

def load_credentials_from_json(json_content):
    """Load Google Sheets credentials from JSON content"""
    try:
        credentials_dict = json.loads(json_content)
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(credentials_dict, scopes=scope)
        return credentials
    except Exception as e:
        st.error(f"Error loading credentials: {str(e)}")
        return None

def connect_to_gsheet(credentials, sheet_url):
    """Connect to Google Sheets and return the worksheet"""
    try:
        gc = gspread.authorize(credentials)
        # Extract sheet ID from URL
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        sheet = gc.open_by_key(sheet_id)
        worksheet = sheet.sheet1  # Get the first worksheet
        return worksheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {str(e)}")
        return None

def load_data_from_gsheet(worksheet):
    """Load data from Google Sheets worksheet"""
    try:
        # Get all records as a list of dictionaries
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        return df
    except Exception as e:
        st.error(f"Error loading data from Google Sheets: {str(e)}")
        return None

def create_sample_data():
    """Create sample email campaign data for demonstration"""
    sample_data = [
        {
            "Name": "John Smith",
            "Email Address": "john.smith@company.com",
            "Sender Email": "campaigns@ourcompany.com",
            "Email Subject": "Q4 Sales Report - Action Required",
            "Email Body": """<html><body><h2>Q4 Sales Report</h2><p>Dear John,</p><p>Please review the attached Q4 sales report and provide feedback by end of week. The numbers show a <strong>15% increase</strong> compared to Q3.</p><ul><li>Total Revenue: $2.5M</li><li>New Customers: 150</li><li>Retention Rate: 92%</li></ul><p>Best regards,<br>Sales Team</p></body></html>""",
            "Email Sent": "Yes",
            "Sent on": "2024-01-15 10:30:00",
            "Message Id": "msg_001_abc123"
        },
        {
            "Name": "Sarah Johnson",
            "Email Address": "sarah.j@marketing.com",
            "Sender Email": "newsletters@ourcompany.com",
            "Email Subject": "Marketing Campaign Results - December 2024",
            "Email Body": """<html><body><h1>🎉 Amazing Campaign Results!</h1><p>Hi Sarah,</p><p>The recent marketing campaign exceeded expectations with a <em>25% increase in engagement</em>. Here are the highlights:</p><div style='background: #f0f8ff; padding: 15px; border-radius: 8px;'><h3>Key Metrics:</h3><p>📈 Click-through rate: 8.2%<br>👥 New leads: 324<br>💰 Revenue generated: $45,000</p></div><p>Detailed analytics are attached to this email.</p><p>Thanks for your great work!</p></body></html>""",
            "Email Sent": "Yes",
            "Sent on": "2024-01-14 14:20:00",
            "Message Id": "msg_002_def456"
        },
        {
            "Name": "Mike Chen",
            "Email Address": "m.chen@tech.io",
            "Sender Email": "support@ourcompany.com",
            "Email Subject": "System Maintenance Scheduled - Important Notice",
            "Email Body": """<html><body style='font-family: Arial, sans-serif;'><div style='background: #fee2e2; border: 1px solid #fecaca; padding: 15px; border-radius: 8px; margin-bottom: 20px;'><h2 style='color: #991b1b; margin: 0;'>⚠️ Maintenance Notice</h2></div><p>Dear Mike,</p><p>We have scheduled maintenance for our servers this weekend:</p><table border='1' style='border-collapse: collapse; width: 100%; margin: 15px 0;'><tr style='background: #f3f4f6;'><th style='padding: 10px;'>Date</th><th style='padding: 10px;'>Time</th><th style='padding: 10px;'>Duration</th></tr><tr><td style='padding: 10px;'>Saturday</td><td style='padding: 10px;'>11:00 PM - 3:00 AM</td><td style='padding: 10px;'>4 hours</td></tr></table><p>Expected impact: Limited functionality during maintenance window.</p><p>Thank you for your patience.</p></body></html>""",
            "Email Sent": "Yes",
            "Sent on": "2024-01-13 09:15:00",
            "Message Id": "msg_003_ghi789"
        },
        {
            "Name": "Lisa Rodriguez",
            "Email Address": "lisa.r@hr.company.com",
            "Sender Email": "events@ourcompany.com",
            "Email Subject": "Team Building Event - Save the Date! 🎉",
            "Email Body": """<html><body><div style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px;'><h1 style='margin: 0; font-size: 32px;'>🎉 Annual Team Building Event</h1><p style='font-size: 18px; margin: 10px 0 0 0;'>Join us for a day of fun and collaboration!</p></div><p>Hi Lisa,</p><p>We're excited to announce our annual team building event scheduled for <strong>February 15th, 2024</strong>.</p><h3>Event Details:</h3><ul><li>📅 Date: February 15th, 2024</li><li>🕐 Time: 10:00 AM - 4:00 PM</li><li>📍 Location: Riverside Park Pavilion</li><li>🍕 Lunch and refreshments provided</li></ul><p>Please confirm your attendance and let us know about any dietary restrictions.</p><a href='#' style='display: inline-block; background: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 15px 0;'>RSVP Now</a><p>Looking forward to seeing you there!</p></body></html>""",
            "Email Sent": "No",
            "Sent on": "",
            "Message Id": "msg_004_jkl012"
        },
        {
            "Name": "David Wilson",
            "Email Address": "d.wilson@finance.com",
            "Sender Email": "finance@ourcompany.com",
            "Email Subject": "Budget Approval Request - Q1 2024",
            "Email Body": """<html><body><h2 style='color: #059669;'>💼 Budget Approval Request</h2><p>Dear David,</p><p>I hope this email finds you well. I'm writing to request approval for additional budget allocation for our new project initiative.</p><div style='background: #f0fdf4; border: 1px solid #bbf7d0; padding: 20px; border-radius: 8px; margin: 20px 0;'><h3 style='color: #065f46; margin-top: 0;'>Financial Summary</h3><p><strong>Requested Amount:</strong> $85,000<br><strong>Project Duration:</strong> 6 months<br><strong>Expected ROI:</strong> 180%</p></div><p>The detailed breakdown and projections are attached to this email. Key benefits include:</p><ol><li>Increased operational efficiency by 35%</li><li>Cost reduction in long-term operations</li><li>Enhanced customer satisfaction metrics</li></ol><p>I would appreciate the opportunity to discuss this further at your convenience.</p><p>Best regards,<br><strong>Project Management Team</strong></p></body></html>""",
            "Email Sent": "Yes",
            "Sent on": "2024-01-11 16:45:00",
            "Message Id": "msg_005_mno345"
        }
    ]
    return pd.DataFrame(sample_data)

def get_status_badge(sent_status):
    """Generate status badge HTML"""
    if str(sent_status).lower() in ['yes', 'true', '1']:
        return '<span class="status-badge status-sent">Sent</span>'
    elif str(sent_status).lower() in ['no', 'false', '0']:
        return '<span class="status-badge status-pending">Pending</span>'
    else:
        return '<span class="status-badge status-failed">Failed</span>'

def display_email_body_modal(email_body, email_subject):
    """Display email body in a modal-like container"""
    if not email_body:
        st.warning("No email body content available.")
        return
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["📧 Rendered View", "🔍 HTML Source"])
    
    with tab1:
        st.markdown("**Email Preview:**")
        # Render the HTML content
        try:
            st.markdown(f"""
            <div class="email-body-container">
                <div class="email-body-html">
                    {email_body}
                </div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error rendering HTML: {str(e)}")
            st.text(email_body)
    
    with tab2:
        st.markdown("**HTML Source Code:**")
        st.markdown(f"""
        <div class="email-body-container">
            <div class="email-body-raw">{html.escape(str(email_body))}</div>
        </div>
        """, unsafe_allow_html=True)

def display_email_card(email_data, index):
    """Display a single email as a card with all columns"""
    name = email_data.get("Name", "Unknown")
    email_address = email_data.get("Email Address", "")
    sender_email = email_data.get("Sender Email", "")
    subject = email_data.get("Email Subject", "No Subject")
    email_body = email_data.get("Email Body", "")
    email_sent = email_data.get("Email Sent", "")
    sent_on = email_data.get("Sent on", "")
    message_id = email_data.get("Message Id", "")
    
    # Format date if available
    formatted_date = "Not sent"
    if sent_on and str(sent_on).strip():
        try:
            if isinstance(sent_on, str):
                date_obj = datetime.strptime(sent_on, "%Y-%m-%d %H:%M:%S")
                formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
            else:
                formatted_date = str(sent_on)
        except:
            formatted_date = str(sent_on)
    
    status_badge = get_status_badge(email_sent)
    
    # Create expandable card
    with st.expander(f"📧 {subject} - {name}", expanded=False):
        # Main card content
        card_html = f"""
        <div class="email-card">
            <div class="sender-info">
                <div class="sender-name">{name}</div>
                <div class="sender-email">&lt;{email_address}&gt;</div>
                <div>{status_badge}</div>
            </div>
            <div class="subject">{subject}</div>
            <div class="email-meta">
                <div class="meta-item">
                    <div class="meta-label">Sender Email</div>
                    <div class="meta-value">{sender_email}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Sent Date</div>
                    <div class="meta-value">{formatted_date}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Message ID</div>
                    <div class="meta-value">{message_id}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Status</div>
                    <div class="meta-value">{email_sent}</div>
                </div>
            </div>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Email body section
        if email_body and str(email_body).strip():
            st.markdown("---")
            st.markdown("**Email Content:**")
            display_email_body_modal(email_body, subject)
        else:
            st.info("No email body content available for this message.")

def display_stats(df):
    """Display email campaign statistics"""
    total_emails = len(df)
    emails_sent = len(df[df["Email Sent"].str.lower().isin(['yes', 'true', '1'])])
    emails_pending = len(df[df["Email Sent"].str.lower().isin(['no', 'false', '0'])])
    unique_recipients = df["Email Address"].nunique()
    unique_senders = df["Sender Email"].nunique()
    
    stats_html = f"""
    <div class="stats-container">
        <div class="stat-card">
            <div class="stat-number">{total_emails}</div>
            <div class="stat-label">Total Campaigns</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{emails_sent}</div>
            <div class="stat-label">Emails Sent</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{emails_pending}</div>
            <div class="stat-label">Pending</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{unique_recipients}</div>
            <div class="stat-label">Recipients</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{unique_senders}</div>
            <div class="stat-label">Sender Accounts</div>
        </div>
    </div>
    """
    
    st.markdown(stats_html, unsafe_allow_html=True)

# Main application
def main():
    st.title("📧 Email Campaign Dashboard")
    st.markdown("Live email campaign data from Google Sheets with interactive content preview")
    
    # Sidebar for Google Sheets configuration
    st.sidebar.header("🔐 Google Sheets Authentication")
    
    # JSON Service Account File Upload
    uploaded_file = st.sidebar.file_uploader(
        "Upload JSON Service Account File",
        type=['json'],
        help="Upload your Google Service Account JSON file for authentication"
    )
    
    # Google Sheets URL input with new default
    sheet_url = st.sidebar.text_input(
        "Google Sheets URL",
        value="https://docs.google.com/spreadsheets/d/10dHxl3qKV2aa2U3wqUmZ5fkxCLTBqH-j9MdkObIjPD8/edit?usp=drivesdk",
        help="Enter the full URL of your Google Sheets document"
    )
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("Auto-refresh data", value=False)
    refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 30, 300, 60)
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    # Data loading logic
    df = None
    
    if uploaded_file is not None and sheet_url:
        try:
            # Read the JSON file
            json_content = uploaded_file.read().decode('utf-8')
            credentials = load_credentials_from_json(json_content)
            
            if credentials:
                st.sidebar.success("✅ Credentials loaded successfully")
                
                # Connect to Google Sheets
                with st.spinner("Connecting to Google Sheets..."):
                    worksheet = connect_to_gsheet(credentials, sheet_url)
                
                if worksheet:
                    st.sidebar.success("✅ Connected to Google Sheets")
                    
                    # Load data
                    with st.spinner("Loading email campaign data..."):
                        df = load_data_from_gsheet(worksheet)
                    
                    if df is not None and not df.empty:
                        st.sidebar.success(f"✅ Loaded {len(df)} email records")
                    else:
                        st.sidebar.error("❌ No data found or error loading data")
                        df = None
        except Exception as e:
            st.sidebar.error(f"❌ Error: {str(e)}")
    
    # If no data from Google Sheets, use sample data
    if df is None or df.empty:
        st.info("📝 Using sample data. Upload your JSON service account file and enter your Google Sheets URL to load live data.")
        df = create_sample_data()
    
    # Display statistics
    if df is not None and not df.empty:
        display_stats(df)
        
        # Search and filter options
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input("🔍 Search emails", placeholder="Search by name, subject, or email address...")
        
        with col2:
            status_filter = st.selectbox("📊 Filter by status", ["All", "Sent", "Pending", "Failed"])
        
        with col3:
            sort_option = st.selectbox("📅 Sort by", ["Newest First", "Oldest First", "Name A-Z", "Name Z-A"])
        
        # Apply filters
        filtered_df = df.copy()
        
        if search_term:
            mask = (
                filtered_df["Name"].str.contains(search_term, case=False, na=False) |
                filtered_df["Email Address"].str.contains(search_term, case=False, na=False) |
                filtered_df["Email Subject"].str.contains(search_term, case=False, na=False) |
                filtered_df["Sender Email"].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[mask]
        
        if status_filter == "Sent":
            filtered_df = filtered_df[filtered_df["Email Sent"].str.lower().isin(['yes', 'true', '1'])]
        elif status_filter == "Pending":
            filtered_df = filtered_df[filtered_df["Email Sent"].str.lower().isin(['no', 'false', '0'])]
        elif status_filter == "Failed":
            filtered_df = filtered_df[~filtered_df["Email Sent"].str.lower().isin(['yes', 'true', '1', 'no', 'false', '0'])]
        
        # Apply sorting
        try:
            if sort_option == "Newest First":
                filtered_df['Sent on'] = pd.to_datetime(filtered_df['Sent on'], errors='coerce')
                filtered_df = filtered_df.sort_values('Sent on', ascending=False, na_position='last')
            elif sort_option == "Oldest First":
                filtered_df['Sent on'] = pd.to_datetime(filtered_df['Sent on'], errors='coerce')
                filtered_df = filtered_df.sort_values('Sent on', ascending=True, na_position='last')
            elif sort_option == "Name A-Z":
                filtered_df = filtered_df.sort_values('Name', ascending=True)
            elif sort_option == "Name Z-A":
                filtered_df = filtered_df.sort_values('Name', ascending=False)
        except Exception as e:
            st.warning(f"Sorting error: {str(e)}")
        
        # Display results count
        if len(filtered_df) != len(df):
            st.info(f"Showing {len(filtered_df)} of {len(df)} email campaigns")
        
        # Display email cards
        if not filtered_df.empty:
            st.markdown("---")
            for index, email in filtered_df.iterrows():
                display_email_card(email, index)
        else:
            st.warning("No emails match your search criteria.")
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()
