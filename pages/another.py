import streamlit as st
import gspread
import pandas as pd
import json
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import time
import html
import re
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Advanced Email Campaign Dashboard",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for advanced styling
st.markdown("""
<style>
    /* Main container styles */
    .main-container {
        padding: 0 2rem;
    }
    
    /* Email card styles */
    .email-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .email-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
    }
    
    .email-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border-color: #3b82f6;
    }
    
    /* Header section styles */
    .email-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 20px;
        flex-wrap: wrap;
        gap: 12px;
    }
    
    .sender-info {
        display: flex;
        flex-direction: column;
        gap: 6px;
        flex: 1;
        min-width: 200px;
    }
    
    .sender-name {
        font-weight: 700;
        font-size: 18px;
        color: #1e293b;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .sender-email {
        color: #64748b;
        font-size: 14px;
        font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
        background: #f1f5f9;
        padding: 4px 8px;
        border-radius: 6px;
        display: inline-block;
    }
    
    .email-actions {
        display: flex;
        gap: 8px;
        align-items: center;
    }
    
    /* Subject and content styles */
    .subject {
        font-size: 20px;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 16px;
        line-height: 1.4;
        word-break: break-word;
    }
    
    .email-preview {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        font-size: 14px;
        color: #475569;
        line-height: 1.6;
        max-height: 120px;
        overflow: hidden;
        position: relative;
    }
    
    .email-preview::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 30px;
        background: linear-gradient(transparent, #f8fafc);
    }
    
    /* Metadata grid */
    .email-meta {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        padding: 20px;
        background: #f8fafc;
        border-radius: 12px;
        margin-top: 16px;
    }
    
    .meta-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    
    .meta-label {
        font-weight: 600;
        font-size: 12px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .meta-value {
        color: #1e293b;
        font-weight: 500;
        word-break: break-all;
        font-size: 14px;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .status-sent {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    
    .status-pending {
        background: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    
    .status-failed {
        background: #fecaca;
        color: #991b1b;
        border: 1px solid #fca5a5;
    }
    
    .status-draft {
        background: #e0e7ff;
        color: #3730a3;
        border: 1px solid #c7d2fe;
    }
    
    /* Priority badges */
    .priority-high {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    
    .priority-medium {
        background: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    
    .priority-low {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    
    /* Statistics cards */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-bottom: 32px;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 24px;
        border-radius: 16px;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: transform 0.3s ease;
    }
    
    .stat-card:hover {
        transform: scale(1.02);
    }
    
    .stat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        z-index: 0;
    }
    
    .stat-content {
        position: relative;
        z-index: 1;
    }
    
    .stat-number {
        font-size: 36px;
        font-weight: 800;
        margin-bottom: 8px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .stat-label {
        font-size: 14px;
        opacity: 0.9;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    .stat-change {
        font-size: 12px;
        margin-top: 8px;
        opacity: 0.8;
    }
    
    /* Email body display styles */
    .email-body-container {
        background: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        margin-top: 20px;
        overflow: hidden;
    }
    
    .email-body-header {
        background: #f8fafc;
        padding: 16px 20px;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .email-body-content {
        padding: 24px;
        max-height: 600px;
        overflow-y: auto;
    }
    
    .email-body-html {
        background: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        line-height: 1.6;
        color: #374151;
    }
    
    .email-body-raw {
        background: #0f172a;
        color: #e2e8f0;
        padding: 20px;
        font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', monospace;
        font-size: 13px;
        white-space: pre-wrap;
        overflow-x: auto;
        line-height: 1.5;
    }
    
    /* Action buttons */
    .action-button {
        background: #3b82f6;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 8px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    
    .action-button:hover {
        background: #2563eb;
        transform: translateY(-1px);
    }
    
    .action-button.secondary {
        background: #64748b;
    }
    
    .action-button.secondary:hover {
        background: #475569;
    }
    
    /* Filter and search styles */
    .filter-container {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 24px;
    }
    
    .filter-row {
        display: flex;
        gap: 16px;
        align-items: end;
        flex-wrap: wrap;
    }
    
    /* Performance metrics */
    .performance-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
        margin: 24px 0;
    }
    
    .performance-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .email-header {
            flex-direction: column;
            align-items: stretch;
        }
        
        .stats-container {
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
        }
        
        .stat-card {
            padding: 16px;
        }
        
        .stat-number {
            font-size: 28px;
        }
        
        .email-meta {
            grid-template-columns: 1fr;
        }
    }
    
    /* Loading animations */
    .loading-pulse {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: .5;
        }
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .email-card {
            background: linear-gradient(145deg, #1e293b 0%, #334155 100%);
            border-color: #475569;
            color: #e2e8f0;
        }
        
        .sender-name {
            color: #f1f5f9;
        }
        
        .subject {
            color: #f8fafc;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for expandable cards
if 'expanded_cards' not in st.session_state:
    st.session_state.expanded_cards = set()
if 'selected_emails' not in st.session_state:
    st.session_state.selected_emails = set()
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'cards'

def load_credentials_from_json(json_content):
    """Load Google Sheets credentials from JSON content"""
    try:
        credentials_dict = json.loads(json_content)
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
        ]
        credentials = Credentials.from_service_account_info(credentials_dict, scopes=scope)
        return credentials
    except Exception as e:
        st.error(f"🚫 Error loading credentials: {str(e)}")
        return None

def connect_to_gsheet(credentials, sheet_url):
    """Connect to Google Sheets and return the worksheet"""
    try:
        gc = gspread.authorize(credentials)
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        sheet = gc.open_by_key(sheet_id)
        worksheet = sheet.sheet1
        return worksheet, gc, sheet
    except Exception as e:
        st.error(f"🚫 Error connecting to Google Sheets: {str(e)}")
        return None, None, None

def load_data_from_gsheet(worksheet):
    """Load data from Google Sheets worksheet with enhanced error handling"""
    try:
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        
        # Clean and standardize column names
        df.columns = df.columns.str.strip()
        
        # Handle empty values
        df = df.fillna('')
        
        return df
    except Exception as e:
        st.error(f"🚫 Error loading data from Google Sheets: {str(e)}")
        return None

def create_comprehensive_sample_data():
    """Create comprehensive sample email campaign data"""
    sample_data = []
    
    # Generate diverse sample emails
    campaigns = [
        {
            "Name": "John Smith",
            "Email Address": "john.smith@techcorp.com",
            "Sender Email": "campaigns@ourcompany.com",
            "Email Subject": "🚀 Q4 Sales Report - Action Required",
            "Email Body": """
            <html>
            <head><style>
                body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
                .content { padding: 30px; }
                .highlight { background: #f0f8ff; padding: 20px; border-radius: 10px; margin: 20px 0; }
                .metrics { display: flex; justify-content: space-around; margin: 20px 0; }
                .metric { text-align: center; padding: 15px; }
                .cta { background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }
            </style></head>
            <body>
                <div class="header">
                    <h1>📊 Q4 Sales Performance Report</h1>
                    <p>Outstanding results this quarter!</p>
                </div>
                <div class="content">
                    <h2>Hello John,</h2>
                    <p>I'm excited to share our Q4 sales performance with you. The numbers are truly impressive!</p>
                    
                    <div class="highlight">
                        <h3>📈 Key Highlights</h3>
                        <div class="metrics">
                            <div class="metric">
                                <h4>$2.5M</h4>
                                <p>Total Revenue</p>
                            </div>
                            <div class="metric">
                                <h4>150</h4>
                                <p>New Customers</p>
                            </div>
                            <div class="metric">
                                <h4>92%</h4>
                                <p>Retention Rate</p>
                            </div>
                        </div>
                    </div>
                    
                    <p><strong>Action Required:</strong> Please review the attached detailed report and provide your feedback by Friday.</p>
                    
                    <a href="#" class="cta">📋 View Full Report</a>
                    
                    <p>Thanks for your continued partnership!</p>
                    <p><em>Best regards,<br>Sarah Wilson<br>Sales Director</em></p>
                </div>
            </body>
            </html>
            """,
            "Email Sent": "Yes",
            "Sent on": "2024-01-15 10:30:00",
            "Message Id": "msg_001_abc123"
        },
        {
            "Name": "Maria Garcia",
            "Email Address": "m.garcia@marketingpro.com",
            "Sender Email": "newsletters@ourcompany.com",
            "Email Subject": "🎯 December Campaign Results - 25% Increase!",
            "Email Body": """
            <html>
            <head><style>
                body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
                .container { background: white; max-width: 600px; margin: 0 auto; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(45deg, #FF6B6B, #4ECDC4); padding: 40px; text-align: center; color: white; }
                .content { padding: 30px; }
                .stats { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .stat-row { display: flex; justify-content: space-between; margin: 10px 0; }
                .achievement { background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin: 15px 0; }
            </style></head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Campaign Success!</h1>
                        <h2>December 2024 Results</h2>
                    </div>
                    <div class="content">
                        <p>Hi Maria,</p>
                        <p>I'm thrilled to share the results from our December marketing campaign - we've exceeded all expectations!</p>
                        
                        <div class="achievement">
                            <h3>🏆 Achievement Unlocked: 25% Engagement Increase!</h3>
                        </div>
                        
                        <div class="stats">
                            <h3>📊 Campaign Metrics</h3>
                            <div class="stat-row"><strong>Click-through Rate:</strong> <span style="color: #28a745;">8.2% (+2.1%)</span></div>
                            <div class="stat-row"><strong>New Leads Generated:</strong> <span style="color: #28a745;">324</span></div>
                            <div class="stat-row"><strong>Revenue Generated:</strong> <span style="color: #28a745;">$45,000</span></div>
                            <div class="stat-row"><strong>Cost per Lead:</strong> <span style="color: #28a745;">$12.50</span></div>
                            <div class="stat-row"><strong>ROI:</strong> <span style="color: #28a745;">285%</span></div>
                        </div>
                        
                        <p><strong>Top Performing Content:</strong></p>
                        <ul>
                            <li>"How to Boost Your Sales in 30 Days" - 15% CTR</li>
                            <li>"Customer Success Stories" - 12% CTR</li>
                            <li>"Free Marketing Toolkit" - 18% CTR</li>
                        </ul>
                        
                        <p>The detailed analytics report is attached. Your creative input was instrumental in this success!</p>
                        
                        <p>Looking forward to our Q1 planning session.</p>
                        <p><em>Cheers,<br>Mike Thompson<br>Digital Marketing Manager</em></p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "Email Sent": "Yes",
            "Sent on": "2024-01-14 14:20:00",
            "Message Id": "msg_002_def456"
        },
        {
            "Name": "David Chen",
            "Email Address": "d.chen@techsolutions.io",
            "Sender Email": "support@ourcompany.com",
            "Email Subject": "⚠️ Scheduled Maintenance - System Updates",
            "Email Body": """
            <html>
            <head><style>
                body { font-family: 'Roboto', sans-serif; color: #333; background: #f4f4f4; margin: 0; padding: 20px; }
                .alert { background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .maintenance-window { background: #e3f2fd; border-left: 4px solid #2196F3; padding: 20px; margin: 20px 0; }
                .schedule-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                .schedule-table th, .schedule-table td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                .schedule-table th { background: #f8f9fa; font-weight: bold; }
                .impact-list { background: #fff; padding: 20px; border-radius: 8px; }
            </style></head>
            <body>
                <div style="background: white; max-width: 650px; margin: 0 auto; border-radius: 10px; overflow: hidden;">
                    <div style="background: linear-gradient(135deg, #FF9800, #F57C00); padding: 30px; text-align: center; color: white;">
                        <h1>⚠️ System Maintenance Notice</h1>
                        <p>Scheduled Infrastructure Updates</p>
                    </div>
                    
                    <div style="padding: 30px;">
                        <p>Dear David,</p>
                        
                        <div class="alert">
                            <strong>🔧 Maintenance Alert:</strong> We have scheduled essential system maintenance to improve performance and security.
                        </div>
                        
                        <div class="maintenance-window">
                            <h3>📅 Maintenance Schedule</h3>
                            <table class="schedule-table">
                                <tr>
                                    <th>Date</th>
                                    <th>Start Time</th>
                                    <th>End Time</th>
                                    <th>Duration</th>
                                </tr>
                                <tr>
                                    <td>Saturday, Jan 20th</td>
                                    <td>11:00 PM EST</td>
                                    <td>3:00 AM EST</td>
                                    <td>4 hours</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div class="impact-list">
                            <h3>🎯 What to Expect</h3>
                            <ul>
                                <li><strong>API Services:</strong> Limited functionality during maintenance</li>
                                <li><strong>Dashboard Access:</strong> Temporarily unavailable</li>
                                <li><strong>Data Processing:</strong> Queued for post-maintenance</li>
                                <li><strong>Customer Support:</strong> Available via emergency hotline</li>
                            </ul>
                        </div>
                        
                        <h3>🚀 Improvements After Maintenance:</h3>
                        <ul>
                            <li>25% faster response times</li>
                            <li>Enhanced security protocols</li>
                            <li>New monitoring capabilities</li>
                            <li>Improved data backup systems</li>
                        </ul>
                        
                        <p><strong>Emergency Contact:</strong> If you encounter any critical issues, please call +1-800-SUPPORT</p>
                        
                        <p>Thank you for your patience as we work to improve our services.</p>
                        
                        <p><em>Best regards,<br>Infrastructure Team<br>TechSolutions Support</em></p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "Email Sent": "Yes",
            "Sent on": "2024-01-13 09:15:00",
            "Message Id": "msg_003_ghi789"
        },
        {
            "Name": "Lisa Rodriguez",
            "Email Address": "lisa.r@hr-dynamics.com",
            "Sender Email": "events@ourcompany.com",
            "Email Subject": "🎉 Annual Team Building Event - Save the Date!",
            "Email Body": """
            <html>
            <head><style>
                body { font-family: 'Helvetica Neue', Arial, sans-serif; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
                .container { background: white; max-width: 600px; margin: 40px auto; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
                .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 50px 30px; text-align: center; }
                .content { padding: 40px; }
                .event-details { background: #f8f9fa; padding: 25px; border-radius: 10px; margin: 25px 0; }
                .activity-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }
                .activity { background: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center; }
                .cta-button { background: #4f46e5; color: white; padding: 15px 40px; text-decoration: none; border-radius: 25px; display: inline-block; margin: 25px 0; font-weight: bold; }
            </style></head>
            <body>
                <div class="container">
                    <div class="hero">
                        <h1 style="font-size: 2.5em; margin: 0;">🎉</h1>
                        <h2 style="margin: 10px 0;">Annual Team Building Extravaganza!</h2>
                        <p style="font-size: 1.2em; opacity: 0.9;">Join us for a day of fun, collaboration, and team bonding</p>
                    </div>
                    
                    <div class="content">
                        <p>Dear Lisa,</p>
                        
                        <p>We're absolutely excited to announce our most anticipated event of the year - our Annual Team Building Extravaganza! 🎊</p>
                        
                        <div class="event-details">
                            <h3 style="color: #4f46e5; margin-top: 0;">📋 Event Details</h3>
                            <p><strong>📅 Date:</strong> Saturday, February 15th, 2024</p>
                            <p><strong>🕐 Time:</strong> 10:00 AM - 6:00 PM</p>
                            <p><strong>📍 Location:</strong> Riverside Park Pavilion & Adventure Center</p>
                            <p><strong>🎫 Cost:</strong> Completely FREE (company sponsored!)</p>
                        </div>
                        
                        <h3>🎯 Exciting Activities Planned:</h3>
                        <div class="activity-grid">
                            <div class="activity">
                                <h4>🧗‍♀️ Rock Climbing</h4>
                                <p>Challenge yourself!</p>
                            </div>
                            <div class="activity">
                                <h4>🚣‍♂️ Kayaking</h4>
                                <p>Team water adventure</p>
                            </div>
                            <div class="activity">
                                <h4>🏹 Archery Contest</h4>
                                <p>Bullseye competition</p>
                            </div>
                            <div class="activity">
                                <h4>🍖 BBQ & Games</h4>
                                <p>Delicious food & fun</p>
                            </div>
                        </div>
                        
                        <div style="background: #d4edda; border-left: 4px solid #28a745; padding: 20px; margin: 25px 0;">
                            <h3 style="margin-top: 0; color: #155724;">🍽️ Gourmet Catering Included</h3>
                            <ul style="margin: 10px 0;">
                                <li>🥩 Premium BBQ & Grilled Specialties</li>
                                <li>🥗 Fresh Salad Bar with Organic Options</li>
                                <li>🍰 Dessert Station & Ice Cream Bar</li>
                                <li>🥤 Unlimited Beverages & Refreshments</li>
                                <li>🌱 Vegetarian & Vegan Options Available</li>
                            </ul>
                        </div>
                        
                        <h3>🏆 Special Surprises:</h3>
                        <ul>
                            <li>🎁 Team challenge prizes and awards</li>
                            <li>📸 Professional photographer for memories</li>
                            <li>🎵 Live DJ and music entertainment</li>
                            <li>🎪 Fun photo booth with props</li>
                        </ul>
                        
                        <a href="#" class="cta-button">🎯 RSVP Now - Secure Your Spot!</a>
                        
                        <p><strong>Important:</strong> Please let us know about any dietary restrictions, allergies, or accessibility needs by February 1st.</p>
                        
                        <p>This is going to be our best team building event yet! Can't wait to see everyone there.</p>
                        
                        <p style="margin-top: 30px;"><em>With excitement,<br><strong>Jennifer Martinez</strong><br>Head of Human Resources</em></p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "Email Sent": "No",
            "Sent on": "",
            "Message Id": "msg_004_jkl012"
        },
        {
            "Name": "Robert Taylor",
            "Email Address": "r.taylor@finance-corp.com",
            "Sender Email": "finance@ourcompany.com",
            "Email Subject": "💰 Q1 2024 Budget Approval Request - Urgent Review",
            "Email Body": """
            <html>
            <head><style>
                body { font-family: 'Georgia', serif; background: #f8f9fa; margin: 0; padding: 20px; color: #343a40; }
                .document { background: white; max-width: 700px; margin: 0 auto; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
                .letterhead { background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 30px; text-align: center; }
                .content { padding: 40px; line-height: 1.8; }
                .financial-summary { background: #f8f9fa; border: 2px solid #dee2e6; padding: 25px; border-radius: 10px; margin: 30px 0; }
                .amount { font-size: 2em; color: #28a745; font-weight: bold; text-align: center; margin: 20px 0; }
                .breakdown-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                .breakdown-table th, .breakdown-table td { border: 1px solid #dee2e6; padding: 15px; }
                .breakdown-table th { background: #e9ecef; font-weight: bold; }
                .roi-highlight { background: linear-gradient(135deg, #17a2b8, #138496); color: white; padding: 20px; border-radius: 10px; text-align: center; margin: 25px 0; }
            </style></head>
            <body>
                <div class="document">
                    <div class="letterhead">
                        <h1>💼 Budget Approval Request</h1>
                        <h2>Q1 2024 Strategic Initiative</h2>
                        <p style="opacity: 0.9; margin: 0;">Confidential Financial Document</p>
                    </div>
                    
                    <div class="content">
                        <p>Dear Robert,</p>
                        
                        <p>I hope this message finds you well. I am writing to formally request your approval for additional budget allocation for our strategic Q1 2024 initiative - "Digital Transformation Acceleration Program".</p>
                        
                        <div class="financial-summary">
                            <h3 style="color: #495057; margin-top: 0; text-align: center;">💰 Financial Request Summary</h3>
                            <div class="amount">$125,000</div>
                            <p style="text-align: center; color: #6c757d; margin: 0;"><em>Total Investment Required</em></p>
                        </div>
                        
                        <h3>📊 Detailed Budget Breakdown</h3>
                        <table class="breakdown-table">
                            <tr>
                                <th>Category</th>
                                <th>Amount</th>
                                <th>Percentage</th>
                                <th>Purpose</th>
                            </tr>
                            <tr>
                                <td>Software Licenses</td>
                                <td>$45,000</td>
                                <td>36%</td>
                                <td>Advanced analytics tools</td>
                            </tr>
                            <tr>
                                <td>Training & Development</td>
                                <td>$30,000</td>
                                <td>24%</td>
                                <td>Team skill enhancement</td>
                            </tr>
                            <tr>
                                <td>Infrastructure Upgrade</td>
                                <td>$25,000</td>
                                <td>20%</td>
                                <td>Server and security improvements</td>
                            </tr>
                            <tr>
                                <td>Consulting Services</td>
                                <td>$20,000</td>
                                <td>16%</td>
                                <td>Expert implementation guidance</td>
                            </tr>
                            <tr>
                                <td>Contingency Fund</td>
                                <td>$5,000</td>
                                <td>4%</td>
                                <td>Risk mitigation</td>
                            </tr>
                        </table>
                        
                        <div class="roi-highlight">
                            <h3 style="margin-top: 0;">🚀 Expected Return on Investment</h3>
                            <p style="font-size: 1.3em; margin: 10px 0;"><strong>285% ROI</strong> within 12 months</p>
                            <p style="margin: 0; opacity: 0.9;">Projected savings: $356,250 annually</p>
                        </div>
                        
                        <h3>🎯 Key Benefits & Impact</h3>
                        <ul style="padding-left: 30px;">
                            <li><strong>Operational Efficiency:</strong> 45% reduction in manual processes</li>
                            <li><strong>Customer Satisfaction:</strong> Improved response time by 60%</li>
                            <li><strong>Data Analytics:</strong> Real-time insights and reporting capabilities</li>
                            <li><strong>Scalability:</strong> Foundation for future growth initiatives</li>
                            <li><strong>Competitive Advantage:</strong> Market leadership in digital capabilities</li>
                        </ul>
                        
                        <h3>📅 Implementation Timeline</h3>
                        <ul style="padding-left: 30px;">
                            <li><strong>Phase 1 (Weeks 1-4):</strong> Software procurement and setup</li>
                            <li><strong>Phase 2 (Weeks 5-8):</strong> Team training and onboarding</li>
                            <li><strong>Phase 3 (Weeks 9-12):</strong> Infrastructure deployment</li>
                            <li><strong>Phase 4 (Weeks 13-16):</strong> Testing and optimization</li>
                            <li><strong>Phase 5 (Weeks 17-20):</strong> Full deployment and monitoring</li>
                        </ul>
                        
                        <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 25px 0;">
                            <h4 style="color: #856404; margin-top: 0;">⏰ Time-Sensitive Request</h4>
                            <p style="color: #856404; margin: 0;">To take advantage of Q1 vendor discounts and ensure seamless implementation, we need approval by <strong>January 25th, 2024</strong>.</p>
                        </div>
                        
                        <p><strong>Supporting Documentation:</strong> Detailed financial projections, vendor proposals, and risk assessment matrices are attached for your comprehensive review.</p>
                        
                        <p>I would greatly appreciate the opportunity to discuss this proposal in detail at your earliest convenience. I am confident that this investment will deliver substantial value to our organization.</p>
                        
                        <p>Thank you for your time and consideration.</p>
                        
                        <p style="margin-top: 40px;"><em>Respectfully submitted,<br><strong>Amanda Foster</strong><br>Chief Financial Officer<br>Direct: (555) 123-4567<br>Email: a.foster@ourcompany.com</em></p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "Email Sent": "Yes",
            "Sent on": "2024-01-11 16:45:00",
            "Message Id": "msg_005_mno345"
        }
    ]
    
    # Add more sample entries to demonstrate variety
    for i in range(6, 25):
        sample_data.append({
            "Name": f"User {i}",
            "Email Address": f"user{i}@company{i%5}.com",
            "Sender Email": f"dept{i%3}@ourcompany.com",
            "Email Subject": f"Subject {i} - Important Update",
            "Email Body": f"<html><body><h2>Email {i}</h2><p>This is sample content for email {i}.</p></body></html>",
            "Email Sent": "Yes" if i % 3 == 0 else "No",
            "Sent on": f"2024-01-{10 + (i%15):02d} {9 + (i%12):02d}:30:00" if i % 3 == 0 else "",
            "Message Id": f"msg_{i:03d}_{chr(97+i%26)}{chr(97+(i+1)%26)}{chr(97+(i+2)%26)}{i*17%1000:03d}"
        })
    
    return pd.DataFrame(sample_data)

def get_status_badge(sent_status):
    """Generate status badge HTML with enhanced styling"""
    status = str(sent_status).lower()
    if status in ['yes', 'true', '1']:
        return '<span class="status-badge status-sent">✅ Sent</span>'
    elif status in ['no', 'false', '0', '']:
        return '<span class="status-badge status-pending">⏳ Pending</span>'
    else:
        return '<span class="status-badge status-failed">❌ Failed</span>'

def extract_text_preview(html_content, max_length=200):
    """Extract plain text preview from HTML content"""
    if not html_content:
        return "No content available"
    
    # Remove HTML tags
    text = re.sub('<.*?>', '', str(html_content))
    # Clean up whitespace
    text = ' '.join(text.split())
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text or "No content available"

def display_email_body_viewer(email_body, email_subject, email_index):
    """Enhanced email body viewer with multiple display options"""
    if not email_body:
        st.warning("📝 No email body content available for this message.")
        return
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📧 Email Preview", "🔍 HTML Source", "📊 Content Analysis"])
    
    with tab1:
        st.markdown("**📧 Email as it appears to recipients:**")
        try:
            # Custom CSS for email preview
            preview_css = """
            <style>
            .email-preview-frame {
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                background: white;
                max-height: 600px;
                overflow-y: auto;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .preview-toolbar {
                background: #f8fafc;
                padding: 12px 20px;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 14px;
                color: #64748b;
            }
            .preview-content {
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #374151;
            }
            </style>
            """
            
            st.markdown(preview_css, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="email-preview-frame">
                <div class="preview-toolbar">
                    <span>📧 Subject: {email_subject}</span>
                    <span>🖥️ Preview Mode</span>
                </div>
                <div class="preview-content">
                    {email_body}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"⚠️ Error rendering HTML preview: {str(e)}")
            st.text_area("📝 Plain text fallback:", value=extract_text_preview(email_body, 1000), height=300)
    
    with tab2:
        st.markdown("**🔍 Raw HTML source code:**")
        
        # HTML formatting options
        col1, col2 = st.columns([3, 1])
        with col2:
            word_wrap = st.checkbox("🔄 Word wrap", value=True, key=f"wrap_{email_index}")
            show_line_numbers = st.checkbox("📊 Line numbers", value=False, key=f"lines_{email_index}")
        
        # Display HTML with syntax highlighting
        html_display = html.escape(str(email_body))
        if show_line_numbers:
            lines = html_display.split('\n')
            html_display = '\n'.join(f"{i+1:3d} | {line}" for i, line in enumerate(lines))
        
        st.code(html_display, language='html', line_numbers=show_line_numbers)
        
        # Copy to clipboard button
        if st.button("📋 Copy HTML to Clipboard", key=f"copy_{email_index}"):
            st.success("✅ HTML copied to clipboard! (Feature simulated)")
    
    with tab3:
        st.markdown("**📊 Content Analysis & Metrics:**")
        
        # Analyze content
        html_content = str(email_body)
        plain_text = extract_text_preview(html_content, 10000)
        
        # Create analysis metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📝 Word Count", len(plain_text.split()))
            st.metric("🔤 Character Count", len(plain_text))
            
        with col2:
            html_tags = len(re.findall('<[^>]+>', html_content))
            st.metric("🏷️ HTML Tags", html_tags)
            links = len(re.findall(r'<a\s+[^>]*href', html_content, re.IGNORECASE))
            st.metric("🔗 Links Found", links)
            
        with col3:
            images = len(re.findall(r'<img\s+[^>]*src', html_content, re.IGNORECASE))
            st.metric("🖼️ Images", images)
            tables = len(re.findall(r'<table', html_content, re.IGNORECASE))
            st.metric("📊 Tables", tables)
        
        # Content readability analysis
        st.markdown("---")
        st.markdown("**📖 Content Structure Analysis:**")
        
        analysis_col1, analysis_col2 = st.columns(2)
        
        with analysis_col1:
            # Find headings
            headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', html_content, re.IGNORECASE | re.DOTALL)
            if headings:
                st.markdown("**📋 Headings Found:**")
                for i, heading in enumerate(headings[:5]):  # Show first 5
                    clean_heading = re.sub('<.*?>', '', heading).strip()
                    st.markdown(f"• {clean_heading}")
                if len(headings) > 5:
                    st.markdown(f"... and {len(headings) - 5} more")
            else:
                st.markdown("📋 **Headings:** None found")
        
        with analysis_col2:
            # Estimate reading time
            words = len(plain_text.split())
            reading_time = max(1, round(words / 200))  # Average 200 words per minute
            st.markdown(f"⏱️ **Estimated Reading Time:** {reading_time} minute(s)")
            
            # Content density
            if html_tags > 0:
                content_ratio = len(plain_text) / html_tags
                st.markdown(f"📊 **Content Density:** {content_ratio:.1f} chars per tag")
            
            # Mobile friendliness indicators
            viewport_meta = "viewport" in html_content.lower()
            responsive_images = "max-width" in html_content.lower()
            st.markdown(f"📱 **Mobile Indicators:**")
            st.markdown(f"• Viewport meta: {'✅' if viewport_meta else '❌'}")
            st.markdown(f"• Responsive elements: {'✅' if responsive_images else '❌'}")

def create_performance_charts(df):
    """Create performance visualization charts"""
    if df.empty:
        return
    
    # Email status distribution
    status_counts = df['Email Sent'].value_counts()
    
    fig_status = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="📊 Email Campaign Status Distribution",
        color_discrete_map={'Yes': '#10b981', 'No': '#f59e0b', 'Failed': '#ef4444'}
    )
    fig_status.update_layout(height=400)
    
    # Timeline analysis
    sent_emails = df[df['Email Sent'].str.lower().isin(['yes', 'true', '1'])].copy()
    if not sent_emails.empty and 'Sent on' in sent_emails.columns:
        try:
            sent_emails['Sent on'] = pd.to_datetime(sent_emails['Sent on'], errors='coerce')
            sent_emails = sent_emails.dropna(subset=['Sent on'])
            
            if not sent_emails.empty:
                # Daily email volume
                daily_counts = sent_emails.groupby(sent_emails['Sent on'].dt.date).size().reset_index()
                daily_counts.columns = ['Date', 'Count']
                
                fig_timeline = px.line(
                    daily_counts,
                    x='Date',
                    y='Count',
                    title='📈 Daily Email Volume Trend',
                    markers=True
                )
                fig_timeline.update_layout(height=400)
                
                return fig_status, fig_timeline
        except:
            pass
    
    return fig_status, None

def display_email_statistics(df):
    """Display comprehensive email statistics"""
    if df.empty:
        st.warning("📊 No data available for statistics.")
        return
    
    # Calculate key metrics
    total_emails = len(df)
    sent_emails = len(df[df['Email Sent'].str.lower().isin(['yes', 'true', '1'])])
    pending_emails = len(df[df['Email Sent'].str.lower().isin(['no', 'false', '0', ''])])
    
    # Success rate
    success_rate = (sent_emails / total_emails * 100) if total_emails > 0 else 0
    
    # Create statistics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-content">
                <div class="stat-number">{total_emails}</div>
                <div class="stat-label">Total Emails</div>
                <div class="stat-change">Campaign Overview</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-content">
                <div class="stat-number">{sent_emails}</div>
                <div class="stat-label">Emails Sent</div>
                <div class="stat-change">✅ Delivered</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-content">
                <div class="stat-number">{pending_emails}</div>
                <div class="stat-label">Pending</div>
                <div class="stat-change">⏳ Queued</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-content">
                <div class="stat-number">{success_rate:.1f}%</div>
                <div class="stat-label">Success Rate</div>
                <div class="stat-change">📊 Performance</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_email_card(row, index):
    """Display a single email card with enhanced styling"""
    # Generate card content
    card_id = f"card_{index}"
    is_expanded = card_id in st.session_state.expanded_cards
    
    # Email preview text
    preview_text = extract_text_preview(row.get('Email Body', ''), 150)
    
    # Status badge
    status_badge = get_status_badge(row.get('Email Sent', 'No'))
    
    # Format sent date
    sent_date = row.get('Sent on', '')
    if sent_date:
        try:
            sent_dt = pd.to_datetime(sent_date)
            sent_formatted = sent_dt.strftime('%B %d, %Y at %I:%M %p')
        except:
            sent_formatted = str(sent_date)
    else:
        sent_formatted = "Not sent"
    
    # Create the email card
    st.markdown(f"""
    <div class="email-card">
        <div class="email-header">
            <div class="sender-info">
                <div class="sender-name">
                    👤 {row.get('Name', 'Unknown Sender')}
                </div>
                <span class="sender-email">{row.get('Email Address', 'No email')}</span>
            </div>
            <div class="email-actions">
                {status_badge}
            </div>
        </div>
        
        <div class="subject">
            {row.get('Email Subject', 'No Subject')}
        </div>
        
        <div class="email-preview">
            {preview_text}
        </div>
        
        <div class="email-meta">
            <div class="meta-item">
                <div class="meta-label">From</div>
                <div class="meta-value">{row.get('Sender Email', 'Unknown')}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Sent Date</div>
                <div class="meta-value">{sent_formatted}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Message ID</div>
                <div class="meta-value">{row.get('Message Id', 'N/A')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📧 View Email", key=f"view_{index}"):
            st.session_state[f'show_body_{index}'] = True
    
    with col2:
        if st.button("📋 Copy Subject", key=f"copy_subject_{index}"):
            st.success("✅ Subject copied to clipboard!")
    
    # Show email body if requested
    if st.session_state.get(f'show_body_{index}', False):
        st.markdown("---")
        display_email_body_viewer(row.get('Email Body', ''), row.get('Email Subject', ''), index)
        
        if st.button("❌ Close Email Viewer", key=f"close_{index}"):
            st.session_state[f'show_body_{index}'] = False
            st.rerun()

def apply_filters(df, search_term, status_filter, sender_filter, date_range):
    """Apply various filters to the dataframe"""
    filtered_df = df.copy()
    
    # Search filter
    if search_term:
        search_columns = ['Name', 'Email Address', 'Email Subject', 'Email Body']
        mask = filtered_df[search_columns].astype(str).apply(
            lambda x: x.str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        filtered_df = filtered_df[mask]
    
    # Status filter
    if status_filter != "All":
        if status_filter == "Sent":
            filtered_df = filtered_df[filtered_df['Email Sent'].str.lower().isin(['yes', 'true', '1'])]
        elif status_filter == "Pending":
            filtered_df = filtered_df[filtered_df['Email Sent'].str.lower().isin(['no', 'false', '0', ''])]
    
    # Sender filter
    if sender_filter != "All":
        filtered_df = filtered_df[filtered_df['Sender Email'] == sender_filter]
    
    # Date range filter
    if date_range and len(date_range) == 2:
        try:
            filtered_df['Sent on'] = pd.to_datetime(filtered_df['Sent on'], errors='coerce')
            start_date, end_date = date_range
            mask = (
                (filtered_df['Sent on'].dt.date >= start_date) & 
                (filtered_df['Sent on'].dt.date <= end_date)
            )
            filtered_df = filtered_df[mask | filtered_df['Sent on'].isna()]
        except:
            pass
    
    return filtered_df

def main():
    """Main application function"""
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin: -1rem -1rem 2rem -1rem; border-radius: 0 0 20px 20px;">
        <h1 style="margin: 0; font-size: 3rem;">📧 Email Campaign Dashboard</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">Advanced Email Management & Analytics Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for data source selection
    with st.sidebar:
        st.markdown("## 🔧 Configuration")
        
        data_source = st.radio(
            "📊 Select Data Source",
            ["Sample Data", "Google Sheets"],
            help="Choose between sample data for demo or connect to your Google Sheets"
        )
        
        df = None
        
        if data_source == "Google Sheets":
            st.markdown("### 🔐 Google Sheets Connection")
            
            # Credentials upload
            credentials_file = st.file_uploader(
                "📄 Upload Service Account JSON",
                type=['json'],
                help="Upload your Google Service Account credentials file"
            )
            
            # Sheet URL input
            sheet_url = st.text_input(
                "🔗 Google Sheets URL",
                placeholder="https://docs.google.com/spreadsheets/d/your-sheet-id/...",
                help="Paste the full URL of your Google Sheet"
            )
            
            if credentials_file and sheet_url:
                try:
                    # Load credentials
                    credentials_content = credentials_file.read().decode('utf-8')
                    credentials = load_credentials_from_json(credentials_content)
                    
                    if credentials:
                        # Connect to sheet
                        with st.spinner("🔄 Connecting to Google Sheets..."):
                            worksheet, gc, sheet = connect_to_gsheet(credentials, sheet_url)
                        
                        if worksheet:
                            st.success("✅ Connected successfully!")
                            
                            # Load data
                            with st.spinner("📥 Loading email data..."):
                                df = load_data_from_gsheet(worksheet)
                            
                            if df is not None and not df.empty:
                                st.success(f"📊 Loaded {len(df)} email records")
                            else:
                                st.warning("⚠️ No data found in the sheet")
                        
                except Exception as e:
                    st.error(f"🚫 Connection error: {str(e)}")
                    
        else:
            # Use sample data
            with st.spinner("🔄 Loading sample data..."):
                df = create_comprehensive_sample_data()
            st.success(f"✅ Loaded {len(df)} sample email records")
    
    # Main content area
    if df is not None and not df.empty:
        
        # Display statistics
        st.markdown("## 📊 Campaign Overview")
        display_email_statistics(df)
        
        # Performance charts
        st.markdown("---")
        st.markdown("## 📈 Performance Analytics")
        
        # Create performance visualizations
        chart_col1, chart_col2 = st.columns(2)
        
        fig_status, fig_timeline = create_performance_charts(df)
        
        with chart_col1:
            if fig_status:
                st.plotly_chart(fig_status, use_container_width=True)
        
        with chart_col2:
            if fig_timeline:
                st.plotly_chart(fig_timeline, use_container_width=True)
            else:
                st.info("📅 Timeline data not available - ensure 'Sent on' dates are properly formatted")
        
        # Filters and search
        st.markdown("---")
        st.markdown("## 🔍 Email Campaign Browser")
        
        # Filter controls
        with st.container():
            st.markdown('<div class="filter-container">', unsafe_allow_html=True)
            
            filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 1, 1, 1])
            
            with filter_col1:
                search_term = st.text_input(
                    "🔍 Search emails",
                    placeholder="Search by name, subject, content...",
                    help="Search across all email fields"
                )
            
            with filter_col2:
                status_filter = st.selectbox(
                    "📧 Status",
                    ["All", "Sent", "Pending"],
                    help="Filter by email sending status"
                )
            
            with filter_col3:
                sender_options = ["All"] + list(df['Sender Email'].unique())
                sender_filter = st.selectbox(
                    "👤 Sender",
                    sender_options,
                    help="Filter by sender email address"
                )
            
            with filter_col4:
                # Date range filter
                try:
                    df_with_dates = df[df['Sent on'] != ''].copy()
                    if not df_with_dates.empty:
                        df_with_dates['Sent on'] = pd.to_datetime(df_with_dates['Sent on'], errors='coerce')
                        df_with_dates = df_with_dates.dropna(subset=['Sent on'])
                        
                        if not df_with_dates.empty:
                            min_date = df_with_dates['Sent on'].min().date()
                            max_date = df_with_dates['Sent on'].max().date()
                            
                            date_range = st.date_input(
                                "📅 Date Range",
                                value=(min_date, max_date),
                                min_value=min_date,
                                max_value=max_date,
                                help="Filter emails by send date"
                            )
                        else:
                            date_range = None
                    else:
                        date_range = None
                except:
                    date_range = None
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Apply filters
        filtered_df = apply_filters(df, search_term, status_filter, sender_filter, date_range)
        
        # Results summary
        st.markdown(f"**📊 Showing {len(filtered_df)} of {len(df)} emails**")
        
        # Display options
        display_col1, display_col2, display_col3 = st.columns([2, 1, 1])
        
        with display_col1:
            st.markdown("### 📧 Email List")
        
        with display_col2:
            view_mode = st.selectbox(
                "👁️ View Mode",
                ["Cards", "Table"],
                help="Choose how to display the emails"
            )
        
        with display_col3:
            sort_by = st.selectbox(
                "🔄 Sort By",
                ["Name", "Email Subject", "Sent on"],
                help="Sort emails by selected field"
            )
        
        # Sort the filtered dataframe
        if sort_by in filtered_df.columns:
            if sort_by == "Sent on":
                # Handle date sorting
                try:
                    filtered_df['sort_date'] = pd.to_datetime(filtered_df['Sent on'], errors='coerce')
                    filtered_df = filtered_df.sort_values('sort_date', ascending=False, na_position='last')
                    filtered_df = filtered_df.drop('sort_date', axis=1)
                except:
                    filtered_df = filtered_df.sort_values(sort_by, ascending=True, na_position='last')
            else:
                filtered_df = filtered_df.sort_values(sort_by, ascending=True, na_position='last')
        
        # Display emails based on view mode
        if view_mode == "Cards":
            # Card view
            if filtered_df.empty:
                st.info("🔍 No emails match your current filters. Try adjusting your search criteria.")
            else:
                # Pagination for better performance
                emails_per_page = 10
                total_pages = max(1, (len(filtered_df) - 1) // emails_per_page + 1)
                
                if total_pages > 1:
                    page = st.number_input(
                        f"📄 Page (1-{total_pages})",
                        min_value=1,
                        max_value=total_pages,
                        value=1,
                        help=f"Navigate through {len(filtered_df)} emails"
                    )
                    
                    start_idx = (page - 1) * emails_per_page
                    end_idx = start_idx + emails_per_page
                    page_df = filtered_df.iloc[start_idx:end_idx]
                else:
                    page_df = filtered_df
                
                # Display email cards
                for idx, row in page_df.iterrows():
                    display_email_card(row, idx)
                    st.markdown("---")
                
                # Pagination info
                if total_pages > 1:
                    st.markdown(f"**📄 Page {page} of {total_pages}** | Showing {len(page_df)} emails")
        
        else:
            # Table view
            if filtered_df.empty:
                st.info("🔍 No emails match your current filters.")
            else:
                # Prepare table data
                table_df = filtered_df.copy()
                
                # Add status column with styling
                table_df['Status'] = table_df['Email Sent'].apply(
                    lambda x: "✅ Sent" if str(x).lower() in ['yes', 'true', '1'] 
                    else "⏳ Pending"
                )
                
                # Format sent date
                try:
                    table_df['Formatted Date'] = pd.to_datetime(
                        table_df['Sent on'], errors='coerce'
                    ).dt.strftime('%Y-%m-%d %H:%M')
                except:
                    table_df['Formatted Date'] = table_df['Sent on']
                
                # Select columns for display
                display_columns = [
                    'Name', 'Email Address', 'Email Subject', 
                    'Status', 'Formatted Date', 'Sender Email'
                ]
                
                # Display table
                st.dataframe(
                    table_df[display_columns],
                    use_container_width=True,
                    height=600,
                    column_config={
                        'Name': st.column_config.TextColumn('👤 Recipient', width=150),
                        'Email Address': st.column_config.TextColumn('📧 Email', width=200),
                        'Email Subject': st.column_config.TextColumn('📝 Subject', width=300),
                        'Status': st.column_config.TextColumn('📊 Status', width=100),
                        'Formatted Date': st.column_config.TextColumn('📅 Sent Date', width=150),
                        'Sender Email': st.column_config.TextColumn('👤 From', width=200)
                    }
                )
                
                # Export options
                st.markdown("### 📤 Export Options")
                export_col1, export_col2, export_col3 = st.columns(3)
                
                with export_col1:
                    if st.button("📊 Download CSV"):
                        csv = filtered_df.to_csv(index=False)
                        st.download_button(
                            label="💾 Save CSV File",
                            data=csv,
                            file_name=f"email_campaign_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                
                with export_col2:
                    if st.button("📈 Generate Report"):
                        st.info("📊 Report generation feature coming soon!")
                
                with export_col3:
                    if st.button("📧 Bulk Actions"):
                        st.info("⚙️ Bulk action tools coming soon!")
        
        # Additional analytics section
        st.markdown("---")
        st.markdown("## 🔍 Advanced Analytics")
        
        analytics_tab1, analytics_tab2, analytics_tab3 = st.tabs(["📊 Content Analysis", "👥 Recipient Insights", "⏰ Timing Analysis"])
        
        with analytics_tab1:
            st.markdown("### 📝 Email Content Statistics")
            
            # Content analysis
            if not filtered_df.empty:
                # Word count analysis
                filtered_df['word_count'] = filtered_df['Email Body'].astype(str).apply(
                    lambda x: len(extract_text_preview(x, 10000).split())
                )
                
                content_col1, content_col2 = st.columns(2)
                
                with content_col1:
                    st.metric("📝 Average Word Count", f"{filtered_df['word_count'].mean():.0f}")
                    st.metric("📏 Longest Email", f"{filtered_df['word_count'].max()} words")
                    st.metric("📄 Shortest Email", f"{filtered_df['word_count'].min()} words")
                
                with content_col2:
                    # Subject line analysis
                    subject_lengths = filtered_df['Email Subject'].astype(str).str.len()
                    st.metric("📧 Avg Subject Length", f"{subject_lengths.mean():.0f} chars")
                    st.metric("📏 Longest Subject", f"{subject_lengths.max()} chars")
                    st.metric("📄 Shortest Subject", f"{subject_lengths.min()} chars")
                
                # Word count distribution
                if len(filtered_df) > 1:
                    fig_wordcount = px.histogram(
                        filtered_df,
                        x='word_count',
                        title='📊 Word Count Distribution',
                        nbins=20
                    )
                    fig_wordcount.update_layout(height=400)
                    st.plotly_chart(fig_wordcount, use_container_width=True)
        
        with analytics_tab2:
            st.markdown("### 👥 Recipient Analysis")
            
            if not filtered_df.empty:
                # Domain analysis
                filtered_df['email_domain'] = filtered_df['Email Address'].astype(str).apply(
                    lambda x: x.split('@')[1] if '@' in x else 'unknown'
                )
                
                domain_counts = filtered_df['email_domain'].value_counts().head(10)
                
                if len(domain_counts) > 0:
                    fig_domains = px.bar(
                        x=domain_counts.values,
                        y=domain_counts.index,
                        orientation='h',
                        title='🏢 Top Email Domains',
                        labels={'x': 'Count', 'y': 'Domain'}
                    )
                    fig_domains.update_layout(height=400)
                    st.plotly_chart(fig_domains, use_container_width=True)
                
                # Sender analysis
                sender_counts = filtered_df['Sender Email'].value_counts()
                if len(sender_counts) > 1:
                    fig_senders = px.pie(
                        values=sender_counts.values,
                        names=sender_counts.index,
                        title='📤 Email Volume by Sender'
                    )
                    fig_senders.update_layout(height=400)
                    st.plotly_chart(fig_senders, use_container_width=True)
        
        with analytics_tab3:
            st.markdown("### ⏰ Sending Time Analysis")
            
            # Time-based analysis for sent emails
            sent_emails = filtered_df[
                filtered_df['Email Sent'].str.lower().isin(['yes', 'true', '1'])
            ].copy()
            
            if not sent_emails.empty and 'Sent on' in sent_emails.columns:
                try:
                    sent_emails['Sent on'] = pd.to_datetime(sent_emails['Sent on'], errors='coerce')
                    sent_emails = sent_emails.dropna(subset=['Sent on'])
                    
                    if not sent_emails.empty:
                        # Hour of day analysis
                        sent_emails['hour'] = sent_emails['Sent on'].dt.hour
                        hour_counts = sent_emails['hour'].value_counts().sort_index()
                        
                        fig_hours = px.bar(
                            x=hour_counts.index,
                            y=hour_counts.values,
                            title='🕐 Email Sending by Hour of Day',
                            labels={'x': 'Hour (24h format)', 'y': 'Number of Emails'}
                        )
                        fig_hours.update_layout(height=400)
                        st.plotly_chart(fig_hours, use_container_width=True)
                        
                        # Day of week analysis
                        sent_emails['day_of_week'] = sent_emails['Sent on'].dt.day_name()
                        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        day_counts = sent_emails['day_of_week'].value_counts()
                        day_counts = day_counts.reindex([day for day in day_order if day in day_counts.index])
                        
                        fig_days = px.bar(
                            x=day_counts.index,
                            y=day_counts.values,
                            title='📅 Email Sending by Day of Week',
                            labels={'x': 'Day of Week', 'y': 'Number of Emails'}
                        )
                        fig_days.update_layout(height=400)
                        st.plotly_chart(fig_days, use_container_width=True)
                        
                        # Best sending times insight
                        peak_hour = hour_counts.idxmax()
                        peak_day = day_counts.idxmax()
                        
                        st.success(f"📊 **Insights:** Most emails are sent on {peak_day} at {peak_hour}:00")
                    
                except Exception as e:
                    st.warning("⚠️ Could not analyze timing data. Please ensure 'Sent on' dates are properly formatted.")
            else:
                st.info("📅 No sent email timing data available for analysis.")
        
    else:
        # No data available
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: #f8fafc; border-radius: 15px; border: 2px dashed #cbd5e0;">
            <h2 style="color: #64748b; margin-bottom: 1rem;">📭 No Data Available</h2>
            <p style="color: #64748b; font-size: 1.1rem; margin-bottom: 2rem;">
                Please configure a data source to get started with your email campaign dashboard.
            </p>
            <div style="background: white; padding: 2rem; border-radius: 10px; margin: 2rem auto; max-width: 500px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h3 style="color: #1e293b; margin-bottom: 1rem;">🚀 Quick Start Options</h3>
                <p><strong>📊 Sample Data:</strong> Select "Sample Data" in the sidebar to explore the dashboard with demonstration data.</p>
                <p><strong>🔗 Google Sheets:</strong> Connect your own email campaign data by selecting "Google Sheets" and providing your credentials.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: #f8fafc; border-radius: 10px; margin-top: 3rem;">
        <p style="color: #64748b; margin: 0;">
            📧 <strong>Advanced Email Campaign Dashboard</strong> | 
            Built with Streamlit & Plotly | 
            🔧 Customize for your workflow
        </p>
        <p style="color: #94a3b8; font-size: 0.9rem; margin: 0.5rem 0 0 0;">
            💡 Pro Tip: Use the search and filter features to quickly find specific campaigns or analyze performance trends.
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
