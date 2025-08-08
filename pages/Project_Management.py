import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import numpy as np
from io import BytesIO
import base64
import re
from urllib.parse import urlparse
import requests
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Call Analysis CRM - Universal Audio", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.streamlit.io/',
        'Report a bug': None,
        'About': "Advanced Call Analysis CRM Dashboard with Live Google Sheets Integration"
    }
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .audio-player {
        background: #f1f3f4;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .filter-section {
        background: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Constants
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1LFfNwb9lRQpIosSEvV3O6zIwymUIWeG9L_k7cxw1jQs/edit?gid=0"

EXPECTED_COLUMNS = [
    "call_id", "customer_name", "email", "phone_number", "booking_status", "voice_agent_name",
    "call_date", "call_start_time", "call_end_time", "call_duration_seconds", "call_duration_hms",
    "cost", "call_success", "appointment_scheduled", "intent_detected", "sentiment_score",
    "confidence_score", "keyword_tags", "summary_word_count", "transcript", "summary",
    "action_items", "call_recording_url", "customer_satisfaction", "resolution_time_seconds",
    "escalation_required", "language_detected", "emotion_detected", "speech_rate_wpm",
    "silence_percentage", "interruption_count", "ai_accuracy_score", "follow_up_required",
    "customer_tier", "call_complexity", "agent_performance_score", "call_outcome",
    "revenue_impact", "lead_quality_score", "conversion_probability", "next_best_action",
    "customer_lifetime_value", "call_category", "upload_timestamp"
]

SUPPORTED_AUDIO_FORMATS = {
    "mp3": {"icon": "🎵", "mime": "audio/mpeg"},
    "wav": {"icon": "🔊", "mime": "audio/wav"},
    "ogg": {"icon": "🦉", "mime": "audio/ogg"},
    "flac": {"icon": "💠", "mime": "audio/flac"},
    "aac": {"icon": "🎼", "mime": "audio/aac"},
    "m4a": {"icon": "🎶", "mime": "audio/mp4"},
    "webm": {"icon": "🌐", "mime": "audio/webm"},
    "oga": {"icon": "📀", "mime": "audio/ogg"},
    "opus": {"icon": "🎯", "mime": "audio/opus"},
    "wma": {"icon": "🎪", "mime": "audio/x-ms-wma"}
}

CALL_OUTCOMES = ["Successful", "Failed", "Partial", "Scheduled", "Follow-up Required", "Escalated"]
CUSTOMER_TIERS = ["Bronze", "Silver", "Gold", "Platinum", "VIP"]
LANGUAGES = ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Chinese", "Japanese"]
EMOTIONS = ["Happy", "Neutral", "Frustrated", "Angry", "Confused", "Satisfied", "Excited"]

class ConnectionManager:
    """Manages Google Sheets connection with retry logic and error handling"""
    
    def __init__(self):
        self.client = None
        self.last_connection_time = None
        self.connection_timeout = 300  # 5 minutes
    
    def get_credentials(self) -> Optional[Dict]:
        """Get credentials from session state"""
        return st.session_state.get("global_gsheets_creds")
    
    def is_connection_valid(self) -> bool:
        """Check if current connection is still valid"""
        if not self.client or not self.last_connection_time:
            return False
        
        time_since_connection = time.time() - self.last_connection_time
        return time_since_connection < self.connection_timeout
    
    def connect(self) -> bool:
        """Establish connection to Google Sheets"""
        try:
            creds_dict = self.get_credentials()
            if not creds_dict:
                return False
            
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            self.client = gspread.authorize(creds)
            self.last_connection_time = time.time()
            
            # Test connection
            sheet = self.client.open_by_url(GSHEET_URL).sheet1
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.client = None
            self.last_connection_time = None
            return False
    
    def get_client(self):
        """Get authenticated client, reconnecting if necessary"""
        if not self.is_connection_valid():
            if not self.connect():
                return None
        return self.client

# Initialize connection manager
if 'connection_manager' not in st.session_state:
    st.session_state.connection_manager = ConnectionManager()

def load_data_with_retry(max_retries: int = 3) -> pd.DataFrame:
    """Load data from Google Sheets with retry logic"""
    connection_manager = st.session_state.connection_manager
    
    for attempt in range(max_retries):
        try:
            client = connection_manager.get_client()
            if not client:
                st.error("❌ No valid connection to Google Sheets")
                return pd.DataFrame(columns=EXPECTED_COLUMNS)
            
            sheet = client.open_by_url(GSHEET_URL).sheet1
            df = get_as_dataframe(sheet, evaluate_formulas=True).dropna(how="all")
            
            # Clean column names
            df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
            
            # Ensure all expected columns exist
            for col in EXPECTED_COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            
            # Data type conversions
            df = clean_and_convert_data(df)
            
            logger.info(f"Successfully loaded {len(df)} records from Google Sheets")
            return df[EXPECTED_COLUMNS]
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                st.error(f"❌ Failed to load data after {max_retries} attempts: {e}")
                return pd.DataFrame(columns=EXPECTED_COLUMNS)

def clean_and_convert_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and convert data types"""
    try:
        # Convert numeric columns
        numeric_columns = [
            'call_duration_seconds', 'cost', 'sentiment_score', 'confidence_score',
            'summary_word_count', 'customer_satisfaction', 'resolution_time_seconds',
            'speech_rate_wpm', 'silence_percentage', 'interruption_count',
            'ai_accuracy_score', 'agent_performance_score', 'revenue_impact',
            'lead_quality_score', 'conversion_probability', 'customer_lifetime_value'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Convert date columns
        date_columns = ['call_date', 'upload_timestamp']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert boolean columns
        boolean_columns = [
            'call_success', 'appointment_scheduled', 'escalation_required', 'follow_up_required'
        ]
        for col in boolean_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.lower().isin(['true', 'yes', '1', 'success'])
        
        return df
        
    except Exception as e:
        logger.error(f"Data cleaning failed: {e}")
        return df

def format_duration(seconds: float) -> str:
    """Convert seconds to readable format"""
    try:
        seconds = int(float(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    except:
        return "00:00"

def get_audio_file_info(url: str) -> Dict:
    """Extract audio file information from URL"""
    try:
        parsed_url = urlparse(url)
        filename = parsed_url.path.split('/')[-1] if parsed_url.path else "unknown"
        extension = filename.split('.')[-1].lower() if '.' in filename else "unknown"
        
        format_info = SUPPORTED_AUDIO_FORMATS.get(extension, {
            "icon": "🎧", 
            "mime": "audio/unknown"
        })
        
        return {
            "filename": filename,
            "extension": extension,
            "icon": format_info["icon"],
            "mime": format_info["mime"],
            "supported": extension in SUPPORTED_AUDIO_FORMATS
        }
    except:
        return {
            "filename": "unknown",
            "extension": "unknown", 
            "icon": "🎧",
            "mime": "audio/unknown",
            "supported": False
        }

def create_download_link(df: pd.DataFrame, filename: str) -> str:
    """Create download link for DataFrame"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 Download {filename}</a>'

def apply_filters(df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
    """Apply multiple filters to DataFrame"""
    filtered_df = df.copy()
    
    try:
        # Text filters
        if filters.get('customer_name'):
            filtered_df = filtered_df[
                filtered_df['customer_name'].str.contains(
                    filters['customer_name'], case=False, na=False
                )
            ]
        
        if filters.get('agent_name'):
            filtered_df = filtered_df[
                filtered_df['voice_agent_name'].str.contains(
                    filters['agent_name'], case=False, na=False
                )
            ]
        
        if filters.get('email'):
            filtered_df = filtered_df[
                filtered_df['email'].str.contains(
                    filters['email'], case=False, na=False
                )
            ]
        
        # Categorical filters
        if filters.get('call_success') and filters['call_success'] != "All":
            success_value = filters['call_success'] == "Yes"
            filtered_df = filtered_df[filtered_df['call_success'] == success_value]
        
        if filters.get('customer_tier') and filters['customer_tier'] != "All":
            filtered_df = filtered_df[filtered_df['customer_tier'] == filters['customer_tier']]
        
        if filters.get('call_outcome') and filters['call_outcome'] != "All":
            filtered_df = filtered_df[filtered_df['call_outcome'] == filters['call_outcome']]
        
        if filters.get('language') and filters['language'] != "All":
            filtered_df = filtered_df[filtered_df['language_detected'] == filters['language']]
        
        # Numeric range filters
        if filters.get('sentiment_range'):
            min_sent, max_sent = filters['sentiment_range']
            filtered_df = filtered_df[
                (filtered_df['sentiment_score'] >= min_sent) & 
                (filtered_df['sentiment_score'] <= max_sent)
            ]
        
        if filters.get('duration_range'):
            min_dur, max_dur = filters['duration_range']
            filtered_df = filtered_df[
                (filtered_df['call_duration_seconds'] >= min_dur) & 
                (filtered_df['call_duration_seconds'] <= max_dur)
            ]
        
        if filters.get('confidence_range'):
            min_conf, max_conf = filters['confidence_range']
            filtered_df = filtered_df[
                (filtered_df['confidence_score'] >= min_conf) & 
                (filtered_df['confidence_score'] <= max_conf)
            ]
        
        # Date filters
        if filters.get('date_range'):
            start_date, end_date = filters['date_range']
            filtered_df = filtered_df[
                (filtered_df['call_date'] >= pd.Timestamp(start_date)) &
                (filtered_df['call_date'] <= pd.Timestamp(end_date))
            ]
        
        # Boolean filters
        if filters.get('appointment_scheduled'):
            filtered_df = filtered_df[filtered_df['appointment_scheduled'] == True]
        
        if filters.get('escalation_required'):
            filtered_df = filtered_df[filtered_df['escalation_required'] == True]
        
        if filters.get('follow_up_required'):
            filtered_df = filtered_df[filtered_df['follow_up_required'] == True]
        
        return filtered_df
        
    except Exception as e:
        logger.error(f"Filter application failed: {e}")
        return df

# Main App Header
st.markdown("""
<div class="main-header">
    <h1>📞 Advanced Call Analysis CRM Dashboard</h1>
    <p>Real-time analytics from Google Sheets | Universal audio player | Advanced filtering & insights</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - Authentication and Filters
with st.sidebar:
    st.header("🔑 Authentication & Connection")
    
    # Connection status
    connection_manager = st.session_state.connection_manager
    
    if connection_manager.get_credentials():
        client_email = connection_manager.get_credentials().get('client_email', 'Unknown')
        st.markdown(f'<p class="status-success">✅ Connected</p>', unsafe_allow_html=True)
        st.info(f"📧 Service Account: {client_email[:30]}...")
        
        # Connection test and refresh
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧪 Test Connection"):
                if connection_manager.connect():
                    st.success("✅ Connection successful!")
                else:
                    st.error("❌ Connection failed!")
        
        with col2:
            if st.button("🔄 Refresh Data"):
                st.cache_data.clear()
                st.rerun()
    
    else:
        st.markdown('<p class="status-error">❌ Not Connected</p>', unsafe_allow_html=True)
        st.warning("Please upload service account JSON credentials")
        
        # File uploader for credentials
        uploaded_file = st.file_uploader(
            "Upload Service Account JSON", 
            type=['json'],
            help="Upload your Google Service Account JSON file"
        )
        
        if uploaded_file:
            try:
                credentials = json.load(uploaded_file)
                st.session_state.global_gsheets_creds = credentials
                st.success("✅ Credentials uploaded successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Invalid JSON file: {e}")
    
    st.divider()
    
    # Advanced Filters Section
    st.header("🔍 Advanced Filters")
    
    with st.expander("📝 Text Filters", expanded=True):
        customer_name = st.text_input("Customer Name", placeholder="Search by customer name...")
        agent_name = st.text_input("Voice Agent", placeholder="Search by agent name...")
        email_filter = st.text_input("Email", placeholder="Search by email...")
    
    with st.expander("📊 Categorical Filters"):
        call_success = st.selectbox("Call Success", ["All", "Yes", "No"])
        customer_tier = st.selectbox("Customer Tier", ["All"] + CUSTOMER_TIERS)
        call_outcome = st.selectbox("Call Outcome", ["All"] + CALL_OUTCOMES)
        language_filter = st.selectbox("Language", ["All"] + LANGUAGES)
    
    with st.expander("📈 Numeric Range Filters"):
        sentiment_range = st.slider("Sentiment Score", -1.0, 1.0, (-1.0, 1.0), step=0.1)
        duration_range = st.slider("Call Duration (seconds)", 0, 3600, (0, 3600), step=30)
        confidence_range = st.slider("Confidence Score", 0.0, 1.0, (0.0, 1.0), step=0.05)
    
    with st.expander("📅 Date & Time Filters"):
        date_range = st.date_input(
            "Call Date Range",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            help="Select date range for calls"
        )
    
    with st.expander("✅ Boolean Filters"):
        appointment_scheduled = st.checkbox("Appointment Scheduled")
        escalation_required = st.checkbox("Escalation Required")
        follow_up_required = st.checkbox("Follow-up Required")
    
    # Auto-refresh settings
    st.divider()
    st.header("🔄 Auto-Refresh")
    auto_refresh = st.checkbox("Enable Auto-Refresh")
    if auto_refresh:
        refresh_interval = st.selectbox(
            "Refresh Interval", 
            [30, 60, 120, 300], 
            format_func=lambda x: f"{x} seconds"
        )
        
        # Auto-refresh logic
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()
        
        if time.time() - st.session_state.last_refresh > refresh_interval:
            st.cache_data.clear()
            st.session_state.last_refresh = time.time()
            st.rerun()

# Load data
with st.spinner("🔄 Loading data from Google Sheets..."):
    df = load_data_with_retry()

# Apply filters
filters = {
    'customer_name': customer_name,
    'agent_name': agent_name,
    'email': email_filter,
    'call_success': call_success,
    'customer_tier': customer_tier,
    'call_outcome': call_outcome,
    'language': language_filter,
    'sentiment_range': sentiment_range,
    'duration_range': duration_range,
    'confidence_range': confidence_range,
    'date_range': date_range if len(date_range) == 2 else None,
    'appointment_scheduled': appointment_scheduled,
    'escalation_required': escalation_required,
    'follow_up_required': follow_up_required
}

filtered_df = apply_filters(df, filters)

# Main content tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Call Log", 
    "📊 Analytics Dashboard", 
    "🧠 AI Insights", 
    "🔊 Audio Center",
    "📈 Performance Metrics",
    "⚙️ Data Management"
])

with tab1:
    st.subheader("📋 Complete Call Log")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Filtered Results", len(filtered_df))
    with col2:
        st.metric("Total Records", len(df))
    with col3:
        success_rate = (filtered_df['call_success'].sum() / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    with col4:
        avg_duration = filtered_df['call_duration_seconds'].mean() / 60 if len(filtered_df) > 0 else 0
        st.metric("Avg Duration", f"{avg_duration:.1f} min")
    
    # Data table with enhanced display
    if not filtered_df.empty:
        # Format display columns
        display_df = filtered_df.copy()
        display_df['call_duration_formatted'] = display_df['call_duration_seconds'].apply(format_duration)
        display_df['sentiment_formatted'] = display_df['sentiment_score'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
        display_df['confidence_formatted'] = display_df['confidence_score'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
        
        # Select columns for display
        display_columns = [
            'call_id', 'customer_name', 'voice_agent_name', 'call_date',
            'call_duration_formatted', 'call_success', 'sentiment_formatted',
            'confidence_formatted', 'call_outcome', 'customer_tier'
        ]
        
        st.dataframe(
            display_df[display_columns],
            use_container_width=True,
            column_config={
                'call_id': 'Call ID',
                'customer_name': 'Customer',
                'voice_agent_name': 'Agent',
                'call_date': 'Date',
                'call_duration_formatted': 'Duration',
                'call_success': st.column_config.CheckboxColumn('Success'),
                'sentiment_formatted': 'Sentiment',
                'confidence_formatted': 'Confidence',
                'call_outcome': 'Outcome',
                'customer_tier': 'Tier'
            }
        )
        
        # Download options
        st.markdown("### 📥 Export Options")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(create_download_link(filtered_df, "filtered_calls.csv"), unsafe_allow_html=True)
        with col2:
            st.markdown(create_download_link(df, "all_calls.csv"), unsafe_allow_html=True)
        with col3:
            if st.button("📊 Generate Report"):
                st.info("Report generation feature coming soon!")
    
    else:
        st.info("No records match the current filters. Try adjusting your filter criteria.")

with tab2:
    st.subheader("📊 Advanced Analytics Dashboard")
    
    if not filtered_df.empty:
        # Key Performance Indicators
        st.markdown("#### 🎯 Key Performance Indicators")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_calls = len(filtered_df)
            st.metric("Total Calls", total_calls)
        
        with col2:
            unique_customers = filtered_df['customer_name'].nunique()
            st.metric("Unique Customers", unique_customers)
        
        with col3:
            success_rate = (filtered_df['call_success'].sum() / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col4:
            avg_sentiment = filtered_df['sentiment_score'].mean()
            st.metric("Avg Sentiment", f"{avg_sentiment:.2f}" if pd.notnull(avg_sentiment) else "N/A")
        
        with col5:
            total_revenue = filtered_df['revenue_impact'].sum()
            st.metric("Total Revenue Impact", f"${total_revenue:,.2f}" if pd.notnull(total_revenue) else "N/A")
        
        # Charts and visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 Calls by Agent Performance")
            agent_performance = filtered_df.groupby('voice_agent_name').agg({
                'call_success': 'sum',
                'call_id': 'count',
                'sentiment_score': 'mean'
            }).reset_index()
            agent_performance['success_rate'] = (agent_performance['call_success'] / agent_performance['call_id'] * 100)
            
            fig = px.bar(
                agent_performance, 
                x='voice_agent_name', 
                y='success_rate',
                title="Success Rate by Agent",
                color='sentiment_score',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 🎭 Sentiment Distribution")
            fig = px.histogram(
                filtered_df, 
                x='sentiment_score', 
                nbins=20,
                title="Sentiment Score Distribution",
                color_discrete_sequence=['#667eea']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Time series analysis
        st.markdown("#### 📅 Call Volume Over Time")
        if 'call_date' in filtered_df.columns and not filtered_df['call_date'].isna().all():
            daily_calls = filtered_df.groupby(filtered_df['call_date'].dt.date).size().reset_index()
            daily_calls.columns = ['date', 'call_count']
            
            fig = px.line(
                daily_calls, 
                x='date', 
                y='call_count',
                title="Daily Call Volume",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No valid date data available for time series analysis")
        
        # Customer tier analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👑 Customer Tier Distribution")
            tier_counts = filtered_df['customer_tier'].value_counts()
            if not tier_counts.empty:
                fig = px.pie(
                    values=tier_counts.values, 
                    names=tier_counts.index,
                    title="Calls by Customer Tier"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No customer tier data available")
        
        with col2:
            st.markdown("#### 🎯 Call Outcomes")
            outcome_counts = filtered_df['call_outcome'].value_counts()
            if not outcome_counts.empty:
                fig = px.bar(
                    x=outcome_counts.index, 
                    y=outcome_counts.values,
                    title="Call Outcomes Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No call outcome data available")
        
        # Advanced metrics
        st.markdown("#### 🔬 Advanced Performance Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_resolution_time = filtered_df['resolution_time_seconds'].mean() / 60
            st.metric(
                "Avg Resolution Time", 
                f"{avg_resolution_time:.1f} min" if pd.notnull(avg_resolution_time) else "N/A"
            )
        
        with col2:
            escalation_rate = (filtered_df['escalation_required'].sum() / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
            st.metric("Escalation Rate", f"{escalation_rate:.1f}%")
        
        with col3:
            avg_customer_satisfaction = filtered_df['customer_satisfaction'].mean()
            st.metric(
                "Avg Customer Satisfaction", 
                f"{avg_customer_satisfaction:.2f}" if pd.notnull(avg_customer_satisfaction) else "N/A"
            )
    
    else:
        st.info("No data available for analytics. Please adjust your filters.")

with tab3:
    st.subheader("🧠 AI-Powered Insights & Summaries")
    
    if not filtered_df.empty:
        # AI Summary Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_confidence = filtered_df['confidence_score'].mean()
            st.metric("Avg AI Confidence", f"{avg_confidence:.2f}" if pd.notnull(avg_confidence) else "N/A")
        
        with col2:
            avg_accuracy = filtered_df['ai_accuracy_score'].mean()
            st.metric("Avg AI Accuracy", f"{avg_accuracy:.2f}" if pd.notnull(avg_accuracy) else "N/A")
        
        with col3:
            intents_detected = filtered_df['intent_detected'].notna().sum()
            st.metric("Intents Detected", intents_detected)
        
        with col4:
            avg_word_count = filtered_df['summary_word_count'].mean()
            st.metric("Avg Summary Length", f"{avg_word_count:.0f} words" if pd.notnull(avg_word_count) else "N/A")
        
        # Search functionality
        st.markdown("#### 🔍 Search Transcripts & Summaries")
        search_term = st.text_input("Search in transcripts and summaries:", placeholder="Enter keywords...")
        
        if search_term:
            search_results = filtered_df[
                filtered_df['transcript'].str.contains(search_term, case=False, na=False) |
                filtered_df['summary'].str.contains(search_term, case=False, na=False)
            ]
            st.info(f"Found {len(search_results)} results for '{search_term}'")
            display_df = search_results
        else:
            display_df = filtered_df
        
        # Call details with AI insights
        st.markdown("#### 📞 Detailed Call Analysis")
        
        for idx, row in display_df.head(10).iterrows():  # Limit to first 10 for performance
            with st.expander(
                f"📞 {row['call_id']} - {row['customer_name']} ({row['call_date'].strftime('%Y-%m-%d') if pd.notnull(row['call_date']) else 'No date'})"
            ):
                # Call metadata
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Agent:** {row['voice_agent_name']}")
                    st.write(f"**Duration:** {format_duration(row['call_duration_seconds'])}")
                    st.write(f"**Success:** {'✅' if row['call_success'] else '❌'}")
                
                with col2:
                    st.write(f"**Sentiment:** {row['sentiment_score']:.2f}" if pd.notnull(row['sentiment_score']) else "**Sentiment:** N/A")
                    st.write(f"**Confidence:** {row['confidence_score']:.2f}" if pd.notnull(row['confidence_score']) else "**Confidence:** N/A")
                    st.write(f"**Language:** {row['language_detected']}")
                
                with col3:
                    st.write(f"**Outcome:** {row['call_outcome']}")
                    st.write(f"**Customer Tier:** {row['customer_tier']}")
                    st.write(f"**Emotion:** {row['emotion_detected']}")
                
                # AI-generated content
                if row['summary']:
                    st.markdown("**🤖 AI Summary:**")
                    st.markdown(row['summary'])
                
                if row['action_items']:
                    st.markdown("**📋 Action Items:**")
                    st.markdown(row['action_items'])
                
                if row['next_best_action']:
                    st.markdown("**🎯 Next Best Action:**")
                    st.markdown(row['next_best_action'])
                
                # Transcript preview
                if row['transcript']:
                    with st.expander("📝 Full Transcript"):
                        st.text_area(
                            "Transcript", 
                            row['transcript'], 
                            height=200, 
                            key=f"transcript_{idx}"
                        )
                
                # Keywords and tags
                if row['keyword_tags']:
                    st.markdown("**🏷️ Keywords:**")
                    keywords = row['keyword_tags'].split(',') if isinstance(row['keyword_tags'], str) else []
                    for keyword in keywords[:10]:  # Limit to first 10 keywords
                        st.badge(keyword.strip())
    
    else:
        st.info("No data available for AI insights. Please adjust your filters.")

with tab4:
    st.subheader("🔊 Universal Audio Center")
    st.caption("Advanced audio player supporting all major formats with enhanced controls")
    
    if not filtered_df.empty:
        # Audio statistics
        audio_calls = filtered_df[filtered_df['call_recording_url'].notna() & (filtered_df['call_recording_url'] != '')]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Recordings", len(audio_calls))
        with col2:
            st.metric("Available Formats", len(set(audio_calls['call_recording_url'].apply(get_audio_file_info).apply(lambda x: x['extension']))))
        with col3:
            avg_duration = audio_calls['call_duration_seconds'].mean() / 60 if len(audio_calls) > 0 else 0
            st.metric("Avg Recording Length", f"{avg_duration:.1f} min")
        with col4:
            total_duration = audio_calls['call_duration_seconds'].sum() / 3600 if len(audio_calls) > 0 else 0
            st.metric("Total Audio Hours", f"{total_duration:.1f} hrs")
        
        # Audio format breakdown
        if len(audio_calls) > 0:
            st.markdown("#### 🎵 Audio Format Distribution")
            format_counts = audio_calls['call_recording_url'].apply(
                lambda x: get_audio_file_info(x)['extension']
            ).value_counts()
            
            col1, col2 = st.columns([2, 1])
            with col1:
                fig = px.bar(
                    x=format_counts.index, 
                    y=format_counts.values,
                    title="Audio Formats in Dataset"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**Format Legend:**")
                for fmt, info in SUPPORTED_AUDIO_FORMATS.items():
                    if fmt in format_counts.index:
                        st.write(f"{info['icon']} {fmt.upper()}: {format_counts[fmt]} files")
        
        # Audio player section
        st.markdown("#### 🎧 Audio Recordings")
        
        # Filter for audio-only
        audio_filter = st.checkbox("Show only calls with recordings", value=True)
        if audio_filter:
            display_audio_df = audio_calls
        else:
            display_audio_df = filtered_df
        
        if len(display_audio_df) > 0:
            for idx, row in display_audio_df.head(20).iterrows():  # Limit for performance
                url = str(row['call_recording_url']).strip()
                
                if url and url != 'nan':
                    audio_info = get_audio_file_info(url)
                    
                    st.markdown("---")
                    
                    # Audio header
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{audio_info['icon']} {row['call_id']} — {row['customer_name']}**")
                        st.caption(f"Agent: {row['voice_agent_name']} | Duration: {format_duration(row['call_duration_seconds'])}")
                    
                    with col2:
                        st.markdown(f"**Format:** `{audio_info['extension'].upper()}`")
                        st.markdown(f"**File:** `{audio_info['filename'][:20]}...`" if len(audio_info['filename']) > 20 else f"**File:** `{audio_info['filename']}`")
                    
                    with col3:
                        success_icon = "✅" if row['call_success'] else "❌"
                        st.markdown(f"**Success:** {success_icon}")
                        sentiment_color = "🟢" if row['sentiment_score'] > 0.5 else "🟡" if row['sentiment_score'] > 0 else "🔴"
                        st.markdown(f"**Sentiment:** {sentiment_color} {row['sentiment_score']:.2f}" if pd.notnull(row['sentiment_score']) else "**Sentiment:** N/A")
                    
                    # Audio player
                    try:
                        if audio_info['supported']:
                            st.audio(url, format=audio_info['mime'])
                        else:
                            st.warning(f"Format `{audio_info['extension']}` may not be supported by your browser")
                            st.markdown(f"[🔗 Direct link to audio file]({url})")
                    
                    except Exception as e:
                        st.error(f"Could not load audio: {e}")
                        st.markdown(f"[🔗 Direct link to audio file]({url})")
                    
                    # Additional audio metadata
                    with st.expander("📊 Audio Analysis Details"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**Speech Rate:** {row['speech_rate_wpm']:.0f} WPM" if pd.notnull(row['speech_rate_wpm']) else "**Speech Rate:** N/A")
                            st.write(f"**Silence %:** {row['silence_percentage']:.1f}%" if pd.notnull(row['silence_percentage']) else "**Silence %:** N/A")
                        
                        with col2:
                            st.write(f"**Interruptions:** {row['interruption_count']:.0f}" if pd.notnull(row['interruption_count']) else "**Interruptions:** N/A")
                            st.write(f"**Emotion:** {row['emotion_detected']}")
                        
                        with col3:
                            st.write(f"**AI Accuracy:** {row['ai_accuracy_score']:.2f}" if pd.notnull(row['ai_accuracy_score']) else "**AI Accuracy:** N/A")
                            st.write(f"**Customer Satisfaction:** {row['customer_satisfaction']:.1f}/5" if pd.notnull(row['customer_satisfaction']) else "**Customer Satisfaction:** N/A")
                    
                    # Quick transcript preview
                    if row['transcript']:
                        with st.expander("📝 Quick Transcript Preview"):
                            preview_length = 300
                            preview_text = row['transcript'][:preview_length]
                            if len(row['transcript']) > preview_length:
                                preview_text += "..."
                            st.text(preview_text)
        
        else:
            st.info("No audio recordings found in the filtered results.")
    
    else:
        st.info("No data available. Please check your connection and filters.")

with tab5:
    st.subheader("📈 Performance Metrics & KPIs")
    
    if not filtered_df.empty:
        # Performance overview
        st.markdown("#### 🎯 Overall Performance Overview")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            conversion_rate = filtered_df['conversion_probability'].mean() * 100 if not filtered_df['conversion_probability'].isna().all() else 0
            st.metric("Avg Conversion Rate", f"{conversion_rate:.1f}%")
        
        with col2:
            lead_quality = filtered_df['lead_quality_score'].mean() if not filtered_df['lead_quality_score'].isna().all() else 0
            st.metric("Avg Lead Quality", f"{lead_quality:.2f}")
        
        with col3:
            agent_performance = filtered_df['agent_performance_score'].mean() if not filtered_df['agent_performance_score'].isna().all() else 0
            st.metric("Avg Agent Performance", f"{agent_performance:.2f}")
        
        with col4:
            customer_clv = filtered_df['customer_lifetime_value'].mean() if not filtered_df['customer_lifetime_value'].isna().all() else 0
            st.metric("Avg Customer CLV", f"${customer_clv:,.0f}")
        
        with col5:
            follow_up_rate = (filtered_df['follow_up_required'].sum() / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
            st.metric("Follow-up Rate", f"{follow_up_rate:.1f}%")
        
        # Agent performance comparison
        st.markdown("#### 👥 Agent Performance Comparison")
        
        agent_metrics = filtered_df.groupby('voice_agent_name').agg({
            'call_success': 'mean',
            'sentiment_score': 'mean',
            'agent_performance_score': 'mean',
            'conversion_probability': 'mean',
            'customer_satisfaction': 'mean',
            'call_id': 'count'
        }).reset_index()
        
        agent_metrics.columns = [
            'Agent', 'Success Rate', 'Avg Sentiment', 'Performance Score', 
            'Conversion Rate', 'Customer Satisfaction', 'Total Calls'
        ]
        
        # Convert rates to percentages
        agent_metrics['Success Rate'] *= 100
        agent_metrics['Conversion Rate'] *= 100
        
        st.dataframe(
            agent_metrics,
            use_container_width=True,
            column_config={
                'Success Rate': st.column_config.NumberColumn('Success Rate (%)', format="%.1f"),
                'Avg Sentiment': st.column_config.NumberColumn('Avg Sentiment', format="%.2f"),
                'Performance Score': st.column_config.NumberColumn('Performance Score', format="%.2f"),
                'Conversion Rate': st.column_config.NumberColumn('Conversion Rate (%)', format="%.1f"),
                'Customer Satisfaction': st.column_config.NumberColumn('Customer Satisfaction', format="%.2f"),
                'Total Calls': st.column_config.NumberColumn('Total Calls', format="%d")
            }
        )
        
        # Performance trends
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Agent Success Rate Comparison")
            if len(agent_metrics) > 0:
                fig = px.bar(
                    agent_metrics, 
                    x='Agent', 
                    y='Success Rate',
                    title="Success Rate by Agent (%)",
                    color='Success Rate',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 🎭 Sentiment vs Performance")
            if len(agent_metrics) > 0:
                fig = px.scatter(
                    agent_metrics,
                    x='Avg Sentiment',
                    y='Performance Score',
                    size='Total Calls',
                    hover_name='Agent',
                    title="Sentiment vs Performance Score"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Customer tier performance
        st.markdown("#### 👑 Performance by Customer Tier")
        
        tier_performance = filtered_df.groupby('customer_tier').agg({
            'call_success': 'mean',
            'revenue_impact': 'sum',
            'customer_lifetime_value': 'mean',
            'conversion_probability': 'mean',
            'call_id': 'count'
        }).reset_index()
        
        if len(tier_performance) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    tier_performance,
                    x='customer_tier',
                    y='call_success',
                    title="Success Rate by Customer Tier"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    tier_performance,
                    x='customer_tier',
                    y='revenue_impact',
                    title="Revenue Impact by Customer Tier"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Time-based performance analysis
        if 'call_date' in filtered_df.columns and not filtered_df['call_date'].isna().all():
            st.markdown("#### 📅 Performance Trends Over Time")
            
            # Daily performance metrics
            daily_performance = filtered_df.groupby(filtered_df['call_date'].dt.date).agg({
                'call_success': 'mean',
                'sentiment_score': 'mean',
                'conversion_probability': 'mean',
                'call_id': 'count'
            }).reset_index()
            
            daily_performance.columns = ['Date', 'Success Rate', 'Avg Sentiment', 'Conversion Rate', 'Call Count']
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.line(
                    daily_performance,
                    x='Date',
                    y='Success Rate',
                    title="Daily Success Rate Trend",
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.line(
                    daily_performance,
                    x='Date',
                    y='Avg Sentiment',
                    title="Daily Sentiment Trend",
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No data available for performance metrics.")

with tab6:
    st.subheader("⚙️ Data Management & System Health")
    
    # System status
    st.markdown("#### 🔧 System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        connection_status = "🟢 Connected" if st.session_state.connection_manager.get_credentials() else "🔴 Disconnected"
        st.metric("Connection Status", connection_status)
    
    with col2:
        data_freshness = "🟢 Fresh" if len(df) > 0 else "🔴 Stale"
        st.metric("Data Status", data_freshness)
    
    with col3:
        last_update = datetime.now().strftime("%H:%M:%S")
        st.metric("Last Update", last_update)
    
    with col4:
        cache_status = "🟢 Active" if st.cache_data else "🔴 Inactive"
        st.metric("Cache Status", cache_status)
    
    # Data quality metrics
    st.markdown("#### 📊 Data Quality Assessment")
    
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Completeness Analysis:**")
            completeness = {}
            for col in EXPECTED_COLUMNS[:10]:  # Check first 10 columns
                if col in df.columns:
                    non_null_pct = (df[col].notna().sum() / len(df)) * 100
                    completeness[col] = non_null_pct
            
            completeness_df = pd.DataFrame(list(completeness.items()), columns=['Column', 'Completeness %'])
            st.dataframe(completeness_df, use_container_width=True)
        
        with col2:
            st.markdown("**Data Type Validation:**")
            validation_results = []
            
            # Check numeric columns
            numeric_cols = ['sentiment_score', 'confidence_score', 'call_duration_seconds']
            for col in numeric_cols:
                if col in df.columns:
                    valid_pct = (pd.to_numeric(df[col], errors='coerce').notna().sum() / len(df)) * 100
                    validation_results.append({'Column': col, 'Valid %': valid_pct, 'Type': 'Numeric'})
            
            # Check date columns
            date_cols = ['call_date']
            for col in date_cols:
                if col in df.columns:
                    valid_pct = (pd.to_datetime(df[col], errors='coerce').notna().sum() / len(df)) * 100
                    validation_results.append({'Column': col, 'Valid %': valid_pct, 'Type': 'Date'})
            
            validation_df = pd.DataFrame(validation_results)
            if not validation_df.empty:
                st.dataframe(validation_df, use_container_width=True)
    
    # Data management tools
    st.markdown("#### 🛠️ Data Management Tools")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Force Refresh Data"):
            st.cache_data.clear()
            st.success("Cache cleared! Data will refresh on next load.")
            st.rerun()
    
    with col2:
        if st.button("🧹 Clean Data Cache"):
            st.cache_data.clear()
            st.success("All cached data cleared!")
    
    with col3:
        if st.button("📊 Generate Data Report"):
            st.info("Generating comprehensive data report...")
            
            # Create a simple data report
            report_data = {
                'Total Records': len(df),
                'Date Range': f"{df['call_date'].min()} to {df['call_date'].max()}" if 'call_date' in df.columns and not df['call_date'].isna().all() else "N/A",
                'Unique Customers': df['customer_name'].nunique() if 'customer_name' in df.columns else 0,
                'Unique Agents': df['voice_agent_name'].nunique() if 'voice_agent_name' in df.columns else 0,
                'Success Rate': f"{(df['call_success'].sum() / len(df) * 100):.1f}%" if 'call_success' in df.columns and len(df) > 0 else "N/A",
                'Avg Sentiment': f"{df['sentiment_score'].mean():.2f}" if 'sentiment_score' in df.columns and not df['sentiment_score'].isna().all() else "N/A"
            }
            
            st.json(report_data)
    
    # Configuration settings
    st.markdown("#### ⚙️ Configuration Settings")
    
    with st.expander("🔧 Advanced Settings"):
        st.markdown("**Google Sheets Configuration:**")
        st.code(f"Sheet URL: {GSHEET_URL}")
        
        st.markdown("**Supported Audio Formats:**")
        format_list = ", ".join([f"{info['icon']} {fmt.upper()}" for fmt, info in SUPPORTED_AUDIO_FORMATS.items()])
        st.write(format_list)
        
        st.markdown("**Expected Data Columns:**")
        st.write(f"Total columns expected: {len(EXPECTED_COLUMNS)}")
        
        if st.checkbox("Show all expected columns"):
            for i, col in enumerate(EXPECTED_COLUMNS, 1):
                st.write(f"{i}. {col}")
    
    # Troubleshooting
    st.markdown("#### 🔍 Troubleshooting")
    
    with st.expander("❓ Common Issues & Solutions"):
        st.markdown("""
        **Connection Issues:**
        - Ensure your service account JSON has proper permissions
        - Check that the Google Sheet is shared with the service account email
        - Verify the sheet URL is correct and accessible
        
        **Data Loading Issues:**
        - Try refreshing the data using the "Force Refresh" button
        - Check if the sheet has the expected column names
        - Ensure data types are consistent in the sheet
        
        **Audio Playback Issues:**
        - Verify audio URLs are publicly accessible
        - Check if the audio format is supported by your browser
        - Try using the direct download link if playback fails
        
        **Performance Issues:**
        - Enable auto-refresh with longer intervals
        - Use filters to reduce the dataset size
        - Clear cache regularly for better performance
        """)
    
    # Debug information
    if st.checkbox("🐛 Show Debug Information"):
        st.markdown("#### Debug Information")
        
        debug_info = {
            'Session State Keys': list(st.session_state.keys()),
            'DataFrame Shape': df.shape if not df.empty else (0, 0),
            'DataFrame Columns': list(df.columns) if not df.empty else [],
            'Memory Usage': f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB" if not df.empty else "0 MB",
            'Connection Manager Status': {
                'Has Credentials': bool(st.session_state.connection_manager.get_credentials()),
                'Last Connection Time': st.session_state.connection_manager.last_connection_time,
                'Connection Valid': st.session_state.connection_manager.is_connection_valid()
            }
        }
        
        st.json(debug_info)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <h6>📞 Advanced Call Analysis CRM Dashboard</h6>
    <p>
        ✨ Features: Live Google Sheets integration | Universal audio player | Advanced analytics | AI insights | Real-time filtering<br>
        🔧 Built with Streamlit | 📊 Powered by Plotly | 🎵 Universal audio support | 🤖 AI-enhanced analytics
    </p>
    <p><strong>Need help?</strong> Check the troubleshooting section in the Data Management tab</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh logic (if enabled)
if auto_refresh and 'last_refresh' in st.session_state:
    time_since_refresh = time.time() - st.session_state.last_refresh
    if time_since_refresh < refresh_interval:
        remaining_time = refresh_interval - time_since_refresh
        st.sidebar.info(f"⏱️ Next refresh in {remaining_time:.0f} seconds")
