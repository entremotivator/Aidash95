import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import tempfile
import os
import json
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="CSV to Google Sheets Pro", 
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .upload-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>📊 CSV to Google Sheets Pro</h1>
    <p>Upload, process, and share your CSV files as Google Sheets with advanced features</p>
</div>
""", unsafe_allow_html=True)

# Sidebar configuration
st.sidebar.markdown("## 🔐 Configuration")

# Default email for sharing
default_email = "Entremotivator@gmail.com"

# Credentials upload section
st.sidebar.markdown("### Google Credentials")
cred_file = st.sidebar.file_uploader(
    "Upload your `credentials.json`", 
    type="json",
    help="Download this from your Google Cloud Console under Service Accounts"
)

# Email configuration
st.sidebar.markdown("### 📧 Sharing Settings")
share_email = st.sidebar.text_input(
    "Email to share sheets with:",
    value=default_email,
    help="Enter email address that will get edit access to the sheets"
)

permission_level = st.sidebar.selectbox(
    "Permission Level:",
    ["writer", "reader", "commenter"],
    index=0,
    help="Choose the access level for the shared email"
)

# Advanced options
st.sidebar.markdown("### ⚙️ Advanced Options")
auto_resize = st.sidebar.checkbox("Auto-resize columns", value=True)
freeze_header = st.sidebar.checkbox("Freeze header row", value=True)
add_timestamp = st.sidebar.checkbox("Add upload timestamp", value=True)

# Function to get authorized Google Sheets client
@st.cache_resource(show_spinner=False)
def get_gsheet_client(cred_path):
    """Get authorized Google Sheets client"""
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(cred_path, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Failed to authorize Google Sheets client: {str(e)}")
        return None

def validate_csv_data(df, filename):
    """Validate CSV data and provide warnings"""
    issues = []
    
    # Check for empty dataframe
    if df.empty:
        issues.append("⚠️ File is empty")
    
    # Check for missing column names
    if df.columns.isnull().any():
        issues.append("⚠️ Some columns have missing names")
    
    # Check for very large files
    if len(df) > 5000:
        issues.append(f"⚠️ Large file ({len(df):,} rows) - may take longer to upload")
    
    # Check for duplicate column names
    if len(df.columns) != len(set(df.columns)):
        issues.append("⚠️ Duplicate column names detected")
    
    return issues

def format_dataframe(df, add_timestamp_flag):
    """Format dataframe before uploading"""
    if add_timestamp_flag:
        # Add timestamp column
        df['Upload_Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Clean column names
    df.columns = [str(col).strip().replace('\n', ' ').replace('\r', '') for col in df.columns]
    
    # Convert all data to strings to avoid type issues
    for col in df.columns:
        df[col] = df[col].astype(str)
    
    return df

def create_and_upload_sheet(client, df, sheet_name, share_email, permission_level, 
                          auto_resize_flag, freeze_header_flag):
    """Create Google Sheet and upload data"""
    try:
        # Create new spreadsheet
        sh = client.create(sheet_name)
        worksheet = sh.get_worksheet(0)
        
        # Prepare data for upload
        data_to_upload = [df.columns.values.tolist()] + df.values.tolist()
        
        # Upload data
        worksheet.update(data_to_upload)
        
        # Apply formatting options
        if auto_resize_flag:
            # Auto-resize columns
            worksheet.columns_auto_resize(0, len(df.columns))
        
        if freeze_header_flag:
            # Freeze header row
            worksheet.freeze(rows=1)
        
        # Share with specified email
        if share_email:
            try:
                sh.share(share_email, perm_type='user', role=permission_level)
                share_status = f"✅ Shared with {share_email} ({permission_level} access)"
            except Exception as e:
                share_status = f"⚠️ Upload successful but sharing failed: {str(e)}"
        else:
            share_status = "ℹ️ No email sharing configured"
        
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sh.id}"
        
        return {
            'success': True,
            'url': sheet_url,
            'share_status': share_status,
            'sheet_id': sh.id
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Main application logic
if cred_file is not None:
    # Save credentials to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(cred_file.read())
        cred_path = tmp.name
    
    # Validate credentials
    try:
        with open(cred_path, 'r') as f:
            cred_data = json.load(f)
        st.sidebar.success("✅ Credentials loaded successfully")
        st.sidebar.info(f"Service Account: {cred_data.get('client_email', 'Unknown')}")
    except Exception as e:
        st.sidebar.error(f"❌ Invalid credentials file: {str(e)}")
        st.stop()
    
    # Get Google Sheets client
    client = get_gsheet_client(cred_path)
    
    if client is None:
        st.error("Failed to initialize Google Sheets client. Please check your credentials.")
        st.stop()
    
    # File upload section
    st.markdown("""
    <div class="feature-card">
        <h3>📁 Upload Your CSV Files</h3>
        <p>Select one or more CSV files to upload to Google Sheets. Each file will be converted to a separate spreadsheet.</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Choose CSV files",
        type=["csv"],
        accept_multiple_files=True,
        help="You can select multiple CSV files at once"
    )
    
    if uploaded_files:
        st.markdown("---")
        
        # File preview and configuration
        st.markdown("### 📋 File Preview & Configuration")
        
        file_configs = {}
        
        # Create tabs for each file
        if len(uploaded_files) > 1:
            tabs = st.tabs([f"📄 {file.name}" for file in uploaded_files])
        else:
            tabs = [st.container()]
        
        for i, (uploaded_file, tab) in enumerate(zip(uploaded_files, tabs)):
            with tab:
                try:
                    # Read and preview CSV
                    df = pd.read_csv(uploaded_file)
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**File:** {uploaded_file.name}")
                        st.markdown(f"**Rows:** {len(df):,} | **Columns:** {len(df.columns)}")
                        
                        # Show data preview
                        st.markdown("**Preview (first 5 rows):**")
                        st.dataframe(df.head(), use_container_width=True)
                    
                    with col2:
                        # Sheet naming
                        default_name = uploaded_file.name.replace(".csv", "").replace(" ", "_")
                        sheet_name = st.text_input(
                            f"Sheet name:",
                            value=default_name,
                            key=f"sheet_name_{i}"
                        )
                        
                        # Validate data
                        issues = validate_csv_data(df, uploaded_file.name)
                        if issues:
                            st.markdown("**Data Issues:**")
                            for issue in issues:
                                st.markdown(f"- {issue}")
                    
                    file_configs[uploaded_file.name] = {
                        'dataframe': df,
                        'sheet_name': sheet_name,
                        'issues': issues
                    }
                    
                except Exception as e:
                    st.error(f"❌ Error reading {uploaded_file.name}: {str(e)}")
        
        # Upload button and process
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🚀 Create Google Sheets", type="primary", use_container_width=True):
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results = []
                total_files = len(uploaded_files)
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processing {uploaded_file.name}...")
                    progress_bar.progress((i) / total_files)
                    
                    try:
                        config = file_configs[uploaded_file.name]
                        df = config['dataframe']
                        sheet_name = config['sheet_name']
                        
                        # Format dataframe
                        df_formatted = format_dataframe(df, add_timestamp)
                        
                        # Create and upload sheet
                        result = create_and_upload_sheet(
                            client, df_formatted, sheet_name, share_email, 
                            permission_level, auto_resize, freeze_header
                        )
                        
                        result['filename'] = uploaded_file.name
                        result['sheet_name'] = sheet_name
                        results.append(result)
                        
                        # Small delay to avoid rate limiting
                        time.sleep(0.5)
                        
                    except Exception as e:
                        results.append({
                            'success': False,
                            'filename': uploaded_file.name,
                            'sheet_name': config.get('sheet_name', 'Unknown'),
                            'error': str(e)
                        })
                
                progress_bar.progress(1.0)
                status_text.text("Upload complete!")
                
                # Display results
                st.markdown("---")
                st.markdown("### 📊 Upload Results")
                
                successful_uploads = [r for r in results if r['success']]
                failed_uploads = [r for r in results if not r['success']]
                
                if successful_uploads:
                    st.success(f"✅ Successfully uploaded {len(successful_uploads)} file(s)")
                    
                    # Create results table
                    results_data = []
                    for result in successful_uploads:
                        results_data.append({
                            'File': result['filename'],
                            'Sheet Name': result['sheet_name'],
                            'Share Status': result['share_status'],
                            'Link': f"[Open Sheet]({result['url']})"
                        })
                    
                    results_df = pd.DataFrame(results_data)
                    st.dataframe(results_df, use_container_width=True)
                    
                    # Quick access links
                    st.markdown("**Quick Access Links:**")
                    for result in successful_uploads:
                        st.markdown(f"• **{result['sheet_name']}** → [Open in Google Sheets]({result['url']})")
                
                if failed_uploads:
                    st.error(f"❌ Failed to upload {len(failed_uploads)} file(s)")
                    for result in failed_uploads:
                        st.error(f"**{result['filename']}**: {result['error']}")
                
                # Cleanup temporary credentials file
                try:
                    os.unlink(cred_path)
                except:
                    pass
    
    else:
        st.markdown("""
        <div class="info-box">
            <h4>🎯 Getting Started</h4>
            <p>Upload your CSV files above to begin. Each file will be converted to a separate Google Sheet with the following features:</p>
            <ul>
                <li><strong>Automatic sharing</strong> with your specified email</li>
                <li><strong>Column auto-resizing</strong> for better readability</li>
                <li><strong>Header row freezing</strong> for easier navigation</li>
                <li><strong>Upload timestamps</strong> for tracking</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

else:
    # Instructions for first-time users
    st.markdown("""
    <div class="feature-card">
        <h3>🔐 Setup Instructions</h3>
        <p>To use this application, you need a Google Service Account credentials file:</p>
        
        <h4>Step 1: Create a Google Cloud Project</h4>
        <ol>
            <li>Go to <a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a></li>
            <li>Create a new project or select an existing one</li>
        </ol>
        
        <h4>Step 2: Enable APIs</h4>
        <p>Enable these APIs in your project:</p>
        <ul>
            <li>Google Sheets API</li>
            <li>Google Drive API</li>
        </ul>
        
        <h4>Step 3: Create Service Account</h4>
        <ol>
            <li>Go to "IAM & Admin" → "Service Accounts"</li>
            <li>Click "Create Service Account"</li>
            <li>Fill in the details and create</li>
            <li>Create and download a JSON key file</li>
        </ol>
        
        <h4>Step 4: Upload Credentials</h4>
        <p>Upload your downloaded JSON credentials file in the sidebar to get started!</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h4>✨ Features</h4>
        <ul>
            <li><strong>Multi-file upload:</strong> Process multiple CSV files at once</li>
            <li><strong>Automatic sharing:</strong> Share sheets with specified email addresses</li>
            <li><strong>Data validation:</strong> Check for common issues before upload</li>
            <li><strong>Custom formatting:</strong> Auto-resize columns, freeze headers</li>
            <li><strong>Progress tracking:</strong> Real-time upload progress</li>
            <li><strong>Error handling:</strong> Detailed error messages and recovery</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
