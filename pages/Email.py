import streamlit as st
import gspread
import pandas as pd
import json
from datetime import datetime
from google.oauth2.service_account import Credentials
import time

# Page configuration
st.set_page_config(
    page_title="Email Dashboard",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for email cards
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
    }
    
    .sender-name {
        font-weight: bold;
        font-size: 16px;
        color: #1f2937;
        margin-right: 10px;
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
    
    .summary {
        color: #4b5563;
        font-size: 14px;
        line-height: 1.5;
        margin-bottom: 15px;
    }
    
    .email-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12px;
        color: #9ca3af;
        border-top: 1px solid #f3f4f6;
        padding-top: 10px;
    }
    
    .date {
        font-weight: 500;
    }
    
    .attachment {
        background: #dbeafe;
        color: #1e40af;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 500;
    }
    
    .no-attachment {
        color: #9ca3af;
    }
    
    .stats-container {
        display: flex;
        gap: 20px;
        margin-bottom: 30px;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        flex: 1;
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
    """Create sample email data for demonstration"""
    sample_data = [
        {
            "sender name": "John Smith",
            "sender email": "john.smith@company.com",
            "subject": "Q4 Sales Report - Action Required",
            "summary": "Please review the attached Q4 sales report and provide feedback by end of week. The numbers show a 15% increase compared to Q3.",
            "Date": "2024-01-15",
            "Attachment": "Yes"
        },
        {
            "sender name": "Sarah Johnson",
            "sender email": "sarah.j@marketing.com",
            "subject": "Marketing Campaign Results",
            "summary": "The recent marketing campaign exceeded expectations with a 25% increase in engagement. Detailed analytics are included.",
            "Date": "2024-01-14",
            "Attachment": "No"
        },
        {
            "sender name": "Mike Chen",
            "sender email": "m.chen@tech.io",
            "subject": "System Maintenance Scheduled",
            "summary": "Scheduled maintenance window for our servers this weekend. Expected downtime: 2-4 hours on Saturday night.",
            "Date": "2024-01-13",
            "Attachment": "Yes"
        },
        {
            "sender name": "Lisa Rodriguez",
            "sender email": "lisa.r@hr.company.com",
            "subject": "Team Building Event - Save the Date",
            "summary": "Annual team building event scheduled for next month. Please confirm your attendance and dietary preferences.",
            "Date": "2024-01-12",
            "Attachment": "No"
        },
        {
            "sender name": "David Wilson",
            "sender email": "d.wilson@finance.com",
            "subject": "Budget Approval Request",
            "summary": "Requesting approval for additional budget allocation for the new project. ROI projections and detailed breakdown attached.",
            "Date": "2024-01-11",
            "Attachment": "Yes"
        }
    ]
    return pd.DataFrame(sample_data)

def display_email_card(email_data):
    """Display a single email as a card"""
    sender_name = email_data.get("sender name", "Unknown Sender")
    sender_email = email_data.get("sender email", "")
    subject = email_data.get("subject", "No Subject")
    summary = email_data.get("summary", "No summary available")
    date = email_data.get("Date", "")
    attachment = email_data.get("Attachment", "No")
    
    # Format date if it's a valid date string
    try:
        if date:
            date_obj = datetime.strptime(str(date), "%Y-%m-%d")
            formatted_date = date_obj.strftime("%B %d, %Y")
        else:
            formatted_date = "No date"
    except:
        formatted_date = str(date)
    
    attachment_display = "📎 Has Attachment" if str(attachment).lower() in ['yes', 'true', '1'] else "No Attachment"
    attachment_class = "attachment" if str(attachment).lower() in ['yes', 'true', '1'] else "no-attachment"
    
    card_html = f"""
    <div class="email-card">
        <div class="sender-info">
            <div class="sender-name">{sender_name}</div>
            <div class="sender-email">&lt;{sender_email}&gt;</div>
        </div>
        <div class="subject">{subject}</div>
        <div class="summary">{summary}</div>
        <div class="email-meta">
            <div class="date">{formatted_date}</div>
            <div class="{attachment_class}">{attachment_display}</div>
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def display_stats(df):
    """Display email statistics"""
    total_emails = len(df)
    emails_with_attachments = len(df[df["Attachment"].str.lower().isin(['yes', 'true', '1'])])
    unique_senders = df["sender name"].nunique()
    
    stats_html = f"""
    <div class="stats-container">
        <div class="stat-card">
            <div class="stat-number">{total_emails}</div>
            <div class="stat-label">Total Emails</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{unique_senders}</div>
            <div class="stat-label">Unique Senders</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{emails_with_attachments}</div>
            <div class="stat-label">With Attachments</div>
        </div>
    </div>
    """
    
    st.markdown(stats_html, unsafe_allow_html=True)

# Main application
def main():
    st.title("📧 Email Dashboard")
    st.markdown("Live email data from Google Sheets displayed as interactive cards")
    
    # Sidebar for Google Sheets configuration
    st.sidebar.header("🔐 Google Sheets Authentication")
    
    # JSON Service Account File Upload
    uploaded_file = st.sidebar.file_uploader(
        "Upload JSON Service Account File",
        type=['json'],
        help="Upload your Google Service Account JSON file for authentication"
    )
    
    # Google Sheets URL input
    sheet_url = st.sidebar.text_input(
        "Google Sheets URL",
        value="https://docs.google.com/spreadsheets/d/1DhqfIYM92gTdQ3yku233tLlkfIZsgcI9MVS_MvNg_Cc/edit?usp=sharing",
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
                    with st.spinner("Loading email data..."):
                        df = load_data_from_gsheet(worksheet)
                    
                    if df is not None and not df.empty:
                        st.sidebar.success(f"✅ Loaded {len(df)} emails")
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
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_term = st.text_input("🔍 Search emails", placeholder="Search by sender, subject, or summary...")
        
        with col2:
            attachment_filter = st.selectbox("📎 Filter by attachment", ["All", "With Attachments", "Without Attachments"])
        
        # Apply filters
        filtered_df = df.copy()
        
        if search_term:
            mask = (
                filtered_df["sender name"].str.contains(search_term, case=False, na=False) |
                filtered_df["subject"].str.contains(search_term, case=False, na=False) |
                filtered_df["summary"].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[mask]
        
        if attachment_filter == "With Attachments":
            filtered_df = filtered_df[filtered_df["Attachment"].str.lower().isin(['yes', 'true', '1'])]
        elif attachment_filter == "Without Attachments":
            filtered_df = filtered_df[~filtered_df["Attachment"].str.lower().isin(['yes', 'true', '1'])]
        
        # Display results count
        if len(filtered_df) != len(df):
            st.info(f"Showing {len(filtered_df)} of {len(df)} emails")
        
        # Display email cards
        if not filtered_df.empty:
            # Sort by date (newest first)
            try:
                filtered_df['Date'] = pd.to_datetime(filtered_df['Date'])
                filtered_df = filtered_df.sort_values('Date', ascending=False)
            except:
                pass  # If date parsing fails, keep original order
            
            for index, email in filtered_df.iterrows():
                display_email_card(email)
        else:
            st.warning("No emails match your search criteria.")
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()
