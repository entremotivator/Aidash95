import streamlit as st
import pandas as pd
import numpy as np
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from datetime import timedelta, date
import re
from collections import Counter
import hashlib
import time

# Enhanced page configuration with mobile considerations
st.set_page_config(
    page_title="Call Analysis CRM - Universal Audio", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.streamlit.io/',
        'Report a bug': "https://github.com/streamlit/streamlit/issues",
        'About': "Call Analysis CRM Dashboard v2.0 - Enhanced Analytics & Mobile Support"
    }
)

# Custom CSS for better mobile experience and styling
st.markdown("""
<style>
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .metric-card {
            margin-bottom: 1rem;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }
        
        .stExpander {
            margin-bottom: 1rem;
        }
    }
    
    /* Custom styling for cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .success-metric {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    }
    
    .warning-metric {
        background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
    }
    
    .error-metric {
        background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
    }
    
    .audio-player {
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        background: #000000;
    }
    
    .call-summary {
        background: #f3f3f3; /* changed from white */
        border-left: 4px solid #2196F3;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Header branding colors */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 0;
        border-radius: 10px;
        color: white;
    }

    .header-container h1 {
        font-weight: 800;
        margin-bottom: 0.5rem;
    }

    .header-container h3 {
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .header-container p {
        font-size: 1.1em;
        margin-top: 0.5rem;
    }
</style>

<div class="header-container" style="text-align: center;">
    <h1>📞 Advanced Call CRM Dashboard</h1>
    <h3>🚀 Live Analytics | 🎯 Smart Filtering | 🔊 Universal Audio Player</h3>
    <p>Real-time insights from Google Sheets with advanced mobile support</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data
def example_cached_function(x):
    return x * 2
# Configuration constants
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1LFfNwb9lRQpIosSEvV3O6zIwymUIWeG9L_k7cxw1jQs/edit?gid=0"

# Enhanced column definitions with descriptions
EXPECTED_COLUMNS = [
    "call_id", "customer_name", "email", "phone number", "Booking Status", "voice_agent_name",
    "call_date", "call_start_time", "call_end_time", "call_duration_seconds", "call_duration_hms",
    "cost", "call_success", "appointment_scheduled", "intent_detected", "sentiment_score",
    "confidence_score", "keyword_tags", "summary_word_count", "transcript", "summary",
    "action_items", "call_recording_url", "customer_satisfaction", "resolution_time_seconds",
    "escalation_required", "language_detected", "emotion_detected", "speech_rate_wpm",
    "silence_percentage", "interruption_count", "ai_accuracy_score", "follow_up_required",
    "customer_tier", "call_complexity", "agent_performance_score", "call_outcome",
    "revenue_impact", "lead_quality_score", "conversion_probability", "next_best_action",
    "customer_lifetime_value", "call_category", "Upload_Timestamp"
]

# Enhanced audio format support
SUPPORTED_AUDIO_EXTS = [
    "mp3", "wav", "ogg", "flac", "aac", "m4a", "webm", "oga", "opus", "mp4", "3gp", "amr"
]

AUDIO_FORMAT_ICONS = {
    "mp3": "🎵", "wav": "🔊", "ogg": "🦉", "flac": "💠", "aac": "🎼", 
    "m4a": "🎶", "webm": "🌐", "oga": "📀", "opus": "🎭", "mp4": "🎬", 
    "3gp": "📱", "amr": "📞"
}

# Device detection for mobile optimization
def is_mobile():
    """Detect if user is on mobile device"""
    try:
        user_agent = st.experimental_get_query_params().get('user_agent', [''])[0]
        mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'tablet']
        return any(keyword in user_agent.lower() for keyword in mobile_keywords)
    except:
        # Fallback: assume mobile if screen width detection available
        return False

# Enhanced sidebar with mobile considerations
with st.sidebar:
    st.markdown("### 🔑 System Status")
    
    # Authentication section with enhanced feedback
    if st.session_state.get("global_gsheets_creds"):
        st.success("✅ Authenticated Successfully")
        client_email = st.session_state.global_gsheets_creds.get('client_email', 'Unknown')
        st.info(f"📧 Service Account:\n`{client_email[:35]}...`")
        
        # Connection testing with loading state
        if st.button("🧪 Test Live Connection", key="test_conn"):
            with st.spinner("Testing connection..."):
                try:
                    json_dict = st.session_state.global_gsheets_creds
                    scope = [
                        "https://spreadsheets.google.com/feeds",
                        "https://www.googleapis.com/auth/drive"
                    ]
                    creds = ServiceAccountCredentials.from_json_keyfile_dict(json_dict, scope)
                    client = gspread.authorize(creds)
                    sheet = client.open_by_url(GSHEET_URL).sheet1
                    row_count = len(sheet.get_all_values())
                    st.success(f"✅ Connected! Found {row_count} rows")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Connection failed:\n{str(e)[:100]}...")
    else:
        st.error("❌ No Authentication Found")
        st.markdown("""
        **Setup Instructions:**
        1. Upload service account JSON
        2. Ensure proper Google Sheets permissions
        3. Test connection before proceeding
        """)
    
    st.divider()
    
    # Enhanced filtering section
    st.markdown("### 🔍 Advanced Filters")
    
    # Smart search with regex support
    st.markdown("#### 🎯 Smart Search")
    search_term = st.text_input(
        "Global Search", 
        help="Search across customer names, summaries, transcripts, and more",
        placeholder="Enter search term..."
    )
    use_regex = st.checkbox("Use Regex Search", help="Enable regular expression matching")
    
    # Date range filtering
    st.markdown("#### 📅 Date Range")
    date_filter = st.selectbox(
        "Quick Date Filter",
        ["All Time", "Today", "Yesterday", "Last 7 Days", "Last 30 Days", "This Month", "Custom Range"]
    )
    
    if date_filter == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From")
        with col2:
            end_date = st.date_input("To")
    
    # Enhanced filters
    st.markdown("#### 👥 Customer & Agent")
    customer_name = st.text_input("Customer Name", placeholder="e.g., John Smith")
    agent_name = st.text_input("Voice Agent", placeholder="e.g., Agent Alex")
    
    st.markdown("#### 📊 Performance Metrics")
    call_success = st.selectbox("Call Success", ["All", "Yes", "No"])
    appointment_scheduled = st.selectbox("Appointment Scheduled", ["All", "Yes", "No"])
    
    # Enhanced sentiment analysis
    sentiment_range = st.slider(
        "Sentiment Score Range", 
        -1.0, 1.0, (-1.0, 1.0), 0.1,
        help="Filter by customer sentiment: -1 (very negative) to +1 (very positive)"
    )
    
    # Confidence and quality filters
    confidence_threshold = st.slider("Min Confidence Score", 0.0, 1.0, 0.0, 0.05)
    
    # Call complexity and tier filtering
    st.markdown("#### 🎯 Advanced Criteria")
    customer_tier = st.multiselect(
        "Customer Tier",
        ["Bronze", "Silver", "Gold", "Platinum", "VIP"],
        help="Filter by customer tier"
    )
    
    call_complexity = st.multiselect(
        "Call Complexity",
        ["Simple", "Medium", "Complex", "Very Complex"],
        help="Filter by call complexity level"
    )
    
    # Audio availability filter
    has_recording = st.selectbox("Has Audio Recording", ["All", "Yes", "No"])
    
    # Mobile optimization toggle
    mobile_mode = st.checkbox(
        "📱 Mobile Optimized View", 
        value=is_mobile(),
        help="Optimize layout for mobile devices"
    )
    
    st.divider()
    st.markdown("### 💡 Pro Tips")
    st.info("""
    **Search Tips:**
    • Use quotes for exact phrases
    • Combine multiple filters for precision
    • Enable regex for advanced patterns
    
    **Audio Support:**
    • 12+ audio formats supported
    • Auto-quality detection
    • Mobile-friendly playback
    """)

# Enhanced data loading with caching and error handling
@st.cache_data(ttl=300, show_spinner=True)  # 5-minute cache
def load_data():
    """Load data with enhanced error handling and performance optimization"""
    global_creds = st.session_state.get("global_gsheets_creds")
    if global_creds is None:
        st.warning("⚠️ Please upload Google Service Account credentials to access live data")
        return pd.DataFrame(columns=EXPECTED_COLUMNS), False
    
    try:
        with st.spinner("🔄 Loading live data from Google Sheets..."):
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(global_creds, scope)
            client = gspread.authorize(creds)
            sheet = client.open_by_url(GSHEET_URL).sheet1
            df = get_as_dataframe(sheet, evaluate_formulas=True).dropna(how="all")
            
            # Clean column names
            df.columns = [col.strip() for col in df.columns]
            
            # Data type optimization
            numeric_cols = ["sentiment_score", "confidence_score", "call_duration_seconds", 
                          "ai_accuracy_score", "conversion_probability", "lead_quality_score"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Date parsing
            if 'call_date' in df.columns:
                df['call_date'] = pd.to_datetime(df['call_date'], errors='coerce')
            
            return df, True
            
    except Exception as e:
        st.error(f"❌ Data loading failed: {str(e)}")
        return pd.DataFrame(columns=EXPECTED_COLUMNS), False

# Load data
df, data_loaded = load_data()

# Ensure all expected columns exist
for col in EXPECTED_COLUMNS:
    if col not in df.columns:
        df[col] = ""

df = df[EXPECTED_COLUMNS]

# Enhanced filtering logic
def apply_filters(df):
    """Apply all selected filters to the dataframe"""
    filtered_df = df.copy()
    
    # Global search with regex support
    if search_term:
        search_columns = ["customer_name", "summary", "transcript", "action_items", "voice_agent_name"]
        if use_regex:
            try:
                pattern = re.compile(search_term, re.IGNORECASE)
                mask = filtered_df[search_columns].apply(
                    lambda x: x.astype(str).str.contains(pattern, na=False)
                ).any(axis=1)
                filtered_df = filtered_df[mask]
            except re.error:
                st.error("Invalid regex pattern")
        else:
            mask = filtered_df[search_columns].apply(
                lambda x: x.astype(str).str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            filtered_df = filtered_df[mask]
    
    # Date filtering
    if date_filter != "All Time" and 'call_date' in filtered_df.columns:
        today = pd.Timestamp.today()
        if date_filter == "Today":
            filtered_df = filtered_df[filtered_df['call_date'].dt.date == today.date()]
        elif date_filter == "Yesterday":
            yesterday = today - pd.Timedelta(days=1)
            filtered_df = filtered_df[filtered_df['call_date'].dt.date == yesterday.date()]
        elif date_filter == "Last 7 Days":
            week_ago = today - pd.Timedelta(days=7)
            filtered_df = filtered_df[filtered_df['call_date'] >= week_ago]
        elif date_filter == "Last 30 Days":
            month_ago = today - pd.Timedelta(days=30)
            filtered_df = filtered_df[filtered_df['call_date'] >= month_ago]
        elif date_filter == "This Month":
            filtered_df = filtered_df[
                (filtered_df['call_date'].dt.year == today.year) &
                (filtered_df['call_date'].dt.month == today.month)
            ]
        elif date_filter == "Custom Range":
            if 'start_date' in locals() and 'end_date' in locals():
                filtered_df = filtered_df[
                    (filtered_df['call_date'].dt.date >= start_date) &
                    (filtered_df['call_date'].dt.date <= end_date)
                ]
    
    # Basic filters
    if customer_name:
        filtered_df = filtered_df[
            filtered_df["customer_name"].str.contains(customer_name, case=False, na=False)
        ]
    
    if agent_name:
        filtered_df = filtered_df[
            filtered_df["voice_agent_name"].str.contains(agent_name, case=False, na=False)
        ]
    
    if call_success != "All":
        filtered_df = filtered_df[
            filtered_df["call_success"].astype(str).str.lower() == call_success.lower()
        ]
    
    if appointment_scheduled != "All":
        filtered_df = filtered_df[
            filtered_df["appointment_scheduled"].astype(str).str.lower() == appointment_scheduled.lower()
        ]
    
    # Sentiment filtering
    if 'sentiment_score' in filtered_df.columns:
        sentiment_numeric = pd.to_numeric(filtered_df["sentiment_score"], errors='coerce').fillna(0)
        filtered_df = filtered_df[
            (sentiment_numeric >= sentiment_range[0]) &
            (sentiment_numeric <= sentiment_range[1])
        ]
    
    # Confidence filtering
    if confidence_threshold > 0 and 'confidence_score' in filtered_df.columns:
        confidence_numeric = pd.to_numeric(filtered_df["confidence_score"], errors='coerce').fillna(0)
        filtered_df = filtered_df[confidence_numeric >= confidence_threshold]
    
    # Customer tier filtering
    if customer_tier:
        filtered_df = filtered_df[filtered_df["customer_tier"].isin(customer_tier)]
    
    # Call complexity filtering
    if call_complexity:
        filtered_df = filtered_df[filtered_df["call_complexity"].isin(call_complexity)]
    
    # Audio recording filter
    if has_recording != "All":
        has_audio = filtered_df["call_recording_url"].astype(str).str.len() > 5
        if has_recording == "Yes":
            filtered_df = filtered_df[has_audio]
        else:
            filtered_df = filtered_df[~has_audio]
    
    return filtered_df

# Apply all filters
filtered_df = apply_filters(df)

# Enhanced utility functions
def readable_duration(seconds):
    """Convert seconds to readable duration format"""
    try:
        seconds = int(float(seconds))
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs}s"
    except (ValueError, TypeError):
        return str(seconds)

def get_sentiment_emoji(score):
    """Get emoji based on sentiment score"""
    try:
        score = float(score)
        if score >= 0.5:
            return "😊"
        elif score >= 0.1:
            return "🙂"
        elif score >= -0.1:
            return "😐"
        elif score >= -0.5:
            return "🙁"
        else:
            return "😠"
    except:
        return "😐"

def calculate_kpis(df):
    """Calculate key performance indicators"""
    total_calls = len(df)
    if total_calls == 0:
        return {}
    
    # Success metrics
    successful_calls = (df['call_success'].str.lower() == 'yes').sum()
    success_rate = (successful_calls / total_calls) * 100 if total_calls > 0 else 0
    
    # Appointment metrics
    appointments = (df['appointment_scheduled'].str.lower() == 'yes').sum()
    appointment_rate = (appointments / total_calls) * 100 if total_calls > 0 else 0
    
    # Duration metrics
    durations = pd.to_numeric(df['call_duration_seconds'], errors='coerce').dropna()
    avg_duration = durations.mean() if not durations.empty else 0
    
    # Sentiment metrics
    sentiments = pd.to_numeric(df['sentiment_score'], errors='coerce').dropna()
    avg_sentiment = sentiments.mean() if not sentiments.empty else 0
    
    # Conversion metrics
    conversions = pd.to_numeric(df['conversion_probability'], errors='coerce').dropna()
    avg_conversion = conversions.mean() if not conversions.empty else 0
    
    return {
        'total_calls': total_calls,
        'success_rate': success_rate,
        'appointment_rate': appointment_rate,
        'avg_duration': avg_duration,
        'avg_sentiment': avg_sentiment,
        'avg_conversion': avg_conversion * 100,  # Convert to percentage
        'unique_customers': df['customer_name'].nunique(),
        'unique_agents': df['voice_agent_name'].nunique()
    }

# Main dashboard content with mobile considerations
if mobile_mode:
    # Mobile-optimized layout
    st.markdown("### 📊 Quick Stats")
    kpis = calculate_kpis(filtered_df)
    
    # Display KPIs in mobile-friendly format
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Calls", kpis.get('total_calls', 0))
        st.metric("Success Rate", f"{kpis.get('success_rate', 0):.1f}%")
        st.metric("Avg Duration", f"{kpis.get('avg_duration', 0)/60:.1f}min")
    with col2:
        st.metric("Appointments", f"{kpis.get('appointment_rate', 0):.1f}%")
        st.metric("Avg Sentiment", f"{kpis.get('avg_sentiment', 0):.2f}")
        st.metric("Conversion", f"{kpis.get('avg_conversion', 0):.1f}%")
    
    # Compact tabs for mobile
    tab1, tab2, tab3 = st.tabs(["📋 Calls", "📊 Charts", "🔊 Audio"])
else:
    # Desktop layout with enhanced tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", "📋 Call Log", "🧠 AI Insights", 
        "🔊 Audio Center", "📈 Advanced Analytics", "⚙️ Settings"
    ])

# Enhanced Dashboard Tab
with (tab1 if not mobile_mode else st.container()):
    if not mobile_mode:
        st.markdown("## 📊 Executive Dashboard")
        
        # KPI Section with enhanced styling
        st.markdown("### 🎯 Key Performance Indicators")
        kpis = calculate_kpis(filtered_df)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{kpis.get('total_calls', 0)}</h3>
                <p>Total Calls</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            success_rate = kpis.get('success_rate', 0)
            card_class = "success-metric" if success_rate >= 70 else "warning-metric" if success_rate >= 50 else "error-metric"
            st.markdown(f"""
            <div class="metric-card {card_class}">
                <h3>{success_rate:.1f}%</h3>
                <p>Success Rate</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{kpis.get('appointment_rate', 0):.1f}%</h3>
                <p>Appointments</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{kpis.get('avg_duration', 0)/60:.1f}min</h3>
                <p>Avg Duration</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            sentiment = kpis.get('avg_sentiment', 0)
            sentiment_emoji = get_sentiment_emoji(sentiment)
            st.markdown(f"""
            <div class="metric-card">
                <h3>{sentiment_emoji} {sentiment:.2f}</h3>
                <p>Avg Sentiment</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Enhanced visualizations
        if len(filtered_df) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📈 Calls by Agent Performance")
                agent_stats = filtered_df.groupby('voice_agent_name').agg({
                    'call_id': 'count',
                    'call_success': lambda x: (x.str.lower() == 'yes').sum(),
                    'sentiment_score': lambda x: pd.to_numeric(x, errors='coerce').mean()
                }).round(2)
                agent_stats.columns = ['Total Calls', 'Successful Calls', 'Avg Sentiment']
                agent_stats['Success Rate %'] = (agent_stats['Successful Calls'] / agent_stats['Total Calls'] * 100).round(1)
                
                fig = px.bar(
                    agent_stats.reset_index(), 
                    x='voice_agent_name', 
                    y='Success Rate %',
                    color='Avg Sentiment',
                    title="Agent Performance Overview",
                    color_continuous_scale="RdYlGn"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### 🎯 Conversion Funnel")
                total_calls = len(filtered_df)
                successful_calls = (filtered_df['call_success'].str.lower() == 'yes').sum()
                appointments = (filtered_df['appointment_scheduled'].str.lower() == 'yes').sum()
                
                funnel_data = {
                    'Stage': ['Total Calls', 'Successful Calls', 'Appointments Scheduled'],
                    'Count': [total_calls, successful_calls, appointments],
                    'Percentage': [100, (successful_calls/total_calls*100) if total_calls > 0 else 0, 
                                 (appointments/total_calls*100) if total_calls > 0 else 0]
                }
                
                fig = go.Figure(go.Funnel(
                    y=funnel_data['Stage'],
                    x=funnel_data['Count'],
                    textinfo="value+percent initial"
                ))
                fig.update_layout(title="Conversion Funnel Analysis")
                st.plotly_chart(fig, use_container_width=True)
        
        # Time series analysis
        if 'call_date' in filtered_df.columns and len(filtered_df) > 0:
            st.markdown("#### 📅 Call Volume Trends")
            daily_stats = filtered_df.groupby(filtered_df['call_date'].dt.date).agg({
                'call_id': 'count',
                'call_success': lambda x: (x.str.lower() == 'yes').sum(),
                'sentiment_score': lambda x: pd.to_numeric(x, errors='coerce').mean()
            }).reset_index()
            daily_stats.columns = ['Date', 'Total Calls', 'Successful Calls', 'Avg Sentiment']
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Scatter(x=daily_stats['Date'], y=daily_stats['Total Calls'], 
                          name="Total Calls", line=dict(color='blue')),
                secondary_y=False,
            )
            
            fig.add_trace(
                go.Scatter(x=daily_stats['Date'], y=daily_stats['Successful Calls'], 
                          name="Successful Calls", line=dict(color='green')),
                secondary_y=False,
            )
            
            fig.add_trace(
                go.Scatter(x=daily_stats['Date'], y=daily_stats['Avg Sentiment'], 
                          name="Sentiment Score", line=dict(color='orange')),
                secondary_y=True,
            )
            
            fig.update_yaxes(title_text="Number of Calls", secondary_y=False)
            fig.update_yaxes(title_text="Sentiment Score", secondary_y=True)
            fig.update_layout(title="Daily Performance Trends")
            
            st.plotly_chart(fig, use_container_width=True)

# Enhanced Call Log Tab
with (tab2 if not mobile_mode else tab1):
    st.markdown("## 📋 Detailed Call Log")
    
    if len(filtered_df) == 0:
        st.warning("🔍 No calls match your current filters. Try adjusting the criteria.")
    else:
        # Enhanced table controls
        col1, col2, col3 = st.columns(3)
        with col1:
            show_full_transcript = st.checkbox("Show Full Transcripts")
        with col2:
            page_size = st.selectbox("Rows per page", [10, 25, 50, 100], index=1)
        with col3:
            export_format = st.selectbox("Export Format", ["CSV", "Excel", "JSON"])
        
        # Display options for mobile
        if mobile_mode:
            display_columns = st.multiselect(
                "Select Columns to Display",
                EXPECTED_COLUMNS,
                default=["call_id", "customer_name", "voice_agent_name", "call_success", "sentiment_score"]
            )
            display_df = filtered_df[display_columns] if display_columns else filtered_df
        else:
            display_df = filtered_df
        
        # Enhanced table display
        if not show_full_transcript:
            # Truncate long text fields for better display
            for col in ['transcript', 'summary', 'action_items']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].astype(str).apply(
                        lambda x: x[:100] + "..." if len(x) > 100 else x
                    )
        
        # Pagination
        total_rows = len(display_df)
        total_pages = (total_rows - 1) // page_size + 1 if total_rows > 0 else 1
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            current_page = st.selectbox(
                f"Page ({total_pages} total)", 
                range(1, total_pages + 1),
                format_func=lambda x: f"Page {x} of {total_pages}"
            )
        
        # Calculate pagination
        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_df = display_df.iloc[start_idx:end_idx]
        
        # Display the table with enhanced formatting
        st.dataframe(
            paginated_df,
            use_container_width=True,
            height=400 if not mobile_mode else 300
        )
        
        st.caption(f"Showing {len(paginated_df)} of {total_rows} calls | Page {current_page}/{total_pages}")
        
        # Export functionality
        if st.button(f"📥 Export as {export_format}"):
            if export_format == "CSV":
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"call_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            elif export_format == "JSON":
                json_str = filtered_df.to_json(orient='records', indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"call_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

# AI Insights Tab
with (tab3 if not mobile_mode else tab2):
    st.markdown("## 🧠 AI-Powered Insights & Analysis")
    
    if len(filtered_df) == 0:
        st.info("📊 No data available for AI analysis with current filters.")
    else:
        # AI Summary Statistics
        st.markdown("### 🎯 Intelligent Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Sentiment distribution
            sentiments = pd.to_numeric(filtered_df['sentiment_score'], errors='coerce').dropna()
            if not sentiments.empty:
                positive_count = (sentiments >= 0.1).sum()
                neutral_count = ((sentiments >= -0.1) & (sentiments < 0.1)).sum()
                negative_count = (sentiments < -0.1).sum()
                
                st.markdown("#### 😊 Sentiment Breakdown")
                st.success(f"😊 Positive: {positive_count} ({positive_count/len(sentiments)*100:.1f}%)")
                st.info(f"😐 Neutral: {neutral_count} ({neutral_count/len(sentiments)*100:.1f}%)")
                st.error(f"😠 Negative: {negative_count} ({negative_count/len(sentiments)*100:.1f}%)")
        
        with col2:
            # Call outcome analysis
            st.markdown("#### 📊 Outcome Analysis")
            outcomes = filtered_df['call_outcome'].value_counts()
            for outcome, count in outcomes.head(5).items():
                if outcome:  # Skip empty outcomes
                    percentage = (count / len(filtered_df)) * 100
                    st.write(f"• **{outcome}**: {count} ({percentage:.1f}%)")
        
        with col3:
            # Top performing agents
            st.markdown("#### 🌟 Top Performers")
            agent_performance = filtered_df.groupby('voice_agent_name').agg({
                'call_success': lambda x: (x.str.lower() == 'yes').sum(),
                'call_id': 'count'
            })
            agent_performance['success_rate'] = (
                agent_performance['call_success'] / agent_performance['call_id'] * 100
            ).round(1)
            
            top_agents = agent_performance.sort_values('success_rate', ascending=False).head(3)
            for agent, stats in top_agents.iterrows():
                if agent:  # Skip empty agent names
                    st.write(f"🥇 **{agent}**: {stats['success_rate']}% success")
        
        st.divider()
        
        # Keyword Analysis
        st.markdown("### 🔍 Keyword & Topic Analysis")
        
        # Extract keywords from summaries and transcripts
        all_text = " ".join(filtered_df['summary'].astype(str) + " " + filtered_df['transcript'].astype(str))
        if all_text.strip():
            # Simple keyword extraction (in a real app, you'd use NLP libraries)
            words = re.findall(r'\b\w{4,}\b', all_text.lower())
            common_words = Counter(words).most_common(10)
            
            if common_words:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📝 Most Common Keywords")
                    keyword_df = pd.DataFrame(common_words, columns=['Keyword', 'Frequency'])
                    fig = px.bar(
                        keyword_df, 
                        x='Frequency', 
                        y='Keyword', 
                        orientation='h',
                        title="Top Keywords in Conversations"
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("#### 🏷️ Keyword Tags Analysis")
                    all_tags = []
                    for tags in filtered_df['keyword_tags'].dropna():
                        if isinstance(tags, str) and tags.strip():
                            all_tags.extend([tag.strip() for tag in tags.split(',')])
                    
                    if all_tags:
                        tag_counts = Counter(all_tags).most_common(8)
                        tag_df = pd.DataFrame(tag_counts, columns=['Tag', 'Count'])
                        
                        fig = px.pie(
                            tag_df, 
                            values='Count', 
                            names='Tag', 
                            title="Distribution of Keyword Tags"
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Detailed Call Analysis
        st.markdown("### 📞 Detailed Call Analysis")
        
        # Call selection for detailed view
        call_options = [
            f"{row['call_id']} - {row['customer_name']} ({row['call_date']})"
            for _, row in filtered_df.iterrows()
            if row['call_id']
        ]
        
        if call_options:
            selected_call = st.selectbox("Select call for detailed analysis:", [""] + call_options)
            
            if selected_call:
                call_id = selected_call.split(" - ")[0]
                call_data = filtered_df[filtered_df['call_id'] == call_id].iloc[0]
                
                # Create detailed call analysis
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div class="call-summary">
                        <h4>📞 Call Details</h4>
                        <p><strong>Customer:</strong> {call_data['customer_name']}</p>
                        <p><strong>Agent:</strong> {call_data['voice_agent_name']}</p>
                        <p><strong>Date:</strong> {call_data['call_date']}</p>
                        <p><strong>Duration:</strong> {readable_duration(call_data['call_duration_seconds'])}</p>
                        <p><strong>Success:</strong> {'✅' if str(call_data['call_success']).lower() == 'yes' else '❌'}</p>
                        <p><strong>Sentiment:</strong> {get_sentiment_emoji(call_data['sentiment_score'])} {call_data['sentiment_score']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("#### 🎯 Performance Metrics")
                    metrics_data = {
                        'Metric': ['Confidence Score', 'AI Accuracy', 'Lead Quality', 'Conversion Probability'],
                        'Value': [
                            float(call_data['confidence_score'] or 0),
                            float(call_data['ai_accuracy_score'] or 0),
                            float(call_data['lead_quality_score'] or 0),
                            float(call_data['conversion_probability'] or 0)
                        ]
                    }
                    
                    fig = go.Figure(data=go.Scatterpolar(
                        r=metrics_data['Value'],
                        theta=metrics_data['Metric'],
                        fill='toself',
                        name='Call Performance'
                    ))
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 1]
                            )
                        ),
                        showlegend=False,
                        height=300
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Display summary and action items
                if call_data['summary']:
                    st.markdown("#### 📝 Call Summary")
                    st.write(call_data['summary'])
                
                if call_data['action_items']:
                    st.markdown("#### ✅ Action Items")
                    action_items = call_data['action_items'].split('\n') if '\n' in str(call_data['action_items']) else [call_data['action_items']]
                    for item in action_items:
                        if item.strip():
                            st.write(f"• {item.strip()}")
                
                if call_data['next_best_action']:
                    st.markdown("#### 🎯 Recommended Next Action")
                    st.info(call_data['next_best_action'])

# Audio Center Tab
with (tab4 if not mobile_mode else tab3):
    st.markdown("## 🔊 Universal Audio Center")
    st.caption("Advanced audio playback with support for 12+ formats and mobile optimization")
    
    # Audio format statistics
    if len(filtered_df) > 0:
        audio_calls = filtered_df[filtered_df['call_recording_url'].astype(str).str.len() > 5]
        
        if len(audio_calls) > 0:
            st.markdown("### 📊 Audio Availability Overview")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Calls with Audio", len(audio_calls))
            with col2:
                st.metric("Audio Coverage", f"{len(audio_calls)/len(filtered_df)*100:.1f}%")
            with col3:
                # Detect audio formats
                formats = []
                for url in audio_calls['call_recording_url']:
                    if isinstance(url, str) and '.' in url:
                        ext = url.split('.')[-1].lower()
                        formats.append(ext)
                
                unique_formats = len(set(formats)) if formats else 0
                st.metric("Audio Formats", unique_formats)
            
            # Format distribution
            if formats:
                format_counts = Counter(formats)
                st.markdown("#### 🎵 Audio Format Distribution")
                
                format_data = pd.DataFrame(
                    [(fmt, count, AUDIO_FORMAT_ICONS.get(fmt, '🎧')) 
                     for fmt, count in format_counts.most_common()],
                    columns=['Format', 'Count', 'Icon']
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.pie(format_data, values='Count', names='Format', 
                               title="Audio Formats Used")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("**Format Support:**")
                    for _, row in format_data.iterrows():
                        support_status = "✅ Native" if row['Format'] in ['mp3', 'wav', 'ogg'] else "🔄 Converted"
                        st.write(f"{row['Icon']} **{row['Format'].upper()}**: {row['Count']} files ({support_status})")
            
            st.divider()
            
            # Audio player section
            st.markdown("### 🎧 Audio Player")
            
            # Search and filter for audio
            audio_search = st.text_input("🔍 Search audio recordings", placeholder="Search by customer, agent, or call ID...")
            
            if audio_search:
                audio_filtered = audio_calls[
                    audio_calls[['customer_name', 'voice_agent_name', 'call_id']].astype(str).apply(
                        lambda x: x.str.contains(audio_search, case=False, na=False)
                    ).any(axis=1)
                ]
            else:
                audio_filtered = audio_calls
            
            # Sort options
            sort_by = st.selectbox(
                "Sort recordings by:",
                ["call_date", "customer_name", "voice_agent_name", "call_duration_seconds", "sentiment_score"]
            )
            audio_filtered = audio_filtered.sort_values(sort_by, ascending=False)
            
            # Display audio players
            audio_count = 0
            for idx, row in audio_filtered.iterrows():
                url = str(row["call_recording_url"]).strip()
                if url and len(url) > 5:
                    audio_count += 1
                    
                    # Extract file info
                    filename = url.split("/")[-1] if "/" in url else url
                    ext = filename.split(".")[-1].lower() if "." in filename else "unknown"
                    icon = AUDIO_FORMAT_ICONS.get(ext, "🎧")
                    
                    # Create audio player card
                    with st.container():
                        st.markdown(f"""
                        <div class="audio-player">
                            <h4>{icon} {row['call_id']} — {row['customer_name']}</h4>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                                <div>
                                    <strong>Agent:</strong> {row['voice_agent_name']}<br>
                                    <strong>Date:</strong> {row['call_date']}<br>
                                    <strong>Duration:</strong> {readable_duration(row['call_duration_seconds'])}<br>
                                    <strong>Format:</strong> {ext.upper()} | <strong>Sentiment:</strong> {get_sentiment_emoji(row['sentiment_score'])} {row['sentiment_score']}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Audio player
                        try:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.audio(url)
                            with col2:
                                st.link_button("📥 Download", url, help="Open/download audio file")
                        except Exception as e:
                            st.warning(f"⚠️ Cannot play audio inline. Error: {e}")
                            st.markdown(f"[🔗 Open Audio File]({url})")
                        
                        # Quick transcript preview
                        if row["transcript"]:
                            with st.expander("📝 Transcript Preview"):
                                transcript_preview = str(row["transcript"])[:800]
                                st.text(transcript_preview + ("..." if len(str(row["transcript"])) > 800 else ""))
                        
                        # Call metrics
                        if not mobile_mode:
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.caption(f"🎯 Success: {'✅' if str(row['call_success']).lower() == 'yes' else '❌'}")
                            with col2:
                                st.caption(f"📅 Appointment: {'✅' if str(row['appointment_scheduled']).lower() == 'yes' else '❌'}")
                            with col3:
                                if row['confidence_score']:
                                    st.caption(f"🎲 Confidence: {float(row['confidence_score']):.2f}")
                            with col4:
                                if row['conversion_probability']:
                                    st.caption(f"📈 Conversion: {float(row['conversion_probability'])*100:.1f}%")
                        
                        st.markdown("---")
            
            if audio_count == 0:
                st.info("🔍 No audio recordings found matching your criteria.")
            else:
                st.caption(f"📊 Showing {audio_count} audio recordings")
        else:
            st.info("🔇 No audio recordings available in the filtered results.")
    else:
        st.info("📊 No call data available for audio analysis.")

# Advanced Analytics Tab (Desktop only)
if not mobile_mode:
    with tab5:
        st.markdown("## 📈 Advanced Analytics & Business Intelligence")
        
        if len(filtered_df) > 0:
            # Advanced KPI Analysis
            st.markdown("### 🎯 Advanced KPI Dashboard")
            
            # Create advanced metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Revenue impact analysis
                revenue_data = pd.to_numeric(filtered_df['revenue_impact'], errors='coerce').dropna()
                total_revenue = revenue_data.sum() if not revenue_data.empty else 0
                st.metric("Total Revenue Impact", f"${total_revenue:,.2f}")
            
            with col2:
                # Customer lifetime value
                clv_data = pd.to_numeric(filtered_df['customer_lifetime_value'], errors='coerce').dropna()
                avg_clv = clv_data.mean() if not clv_data.empty else 0
                st.metric("Avg Customer LTV", f"${avg_clv:,.2f}")
            
            with col3:
                # Escalation rate
                escalations = (filtered_df['escalation_required'].str.lower() == 'yes').sum()
                escalation_rate = (escalations / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
                st.metric("Escalation Rate", f"{escalation_rate:.1f}%")
            
            with col4:
                # Follow-up required
                followups = (filtered_df['follow_up_required'].str.lower() == 'yes').sum()
                followup_rate = (followups / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
                st.metric("Follow-up Rate", f"{followup_rate:.1f}%")
            
            st.divider()
            
            # Correlation Analysis
            st.markdown("### 🔗 Correlation Analysis")
            
            numeric_columns = [
                'sentiment_score', 'confidence_score', 'ai_accuracy_score', 
                'lead_quality_score', 'conversion_probability', 'agent_performance_score'
            ]
            
            correlation_data = {}
            for col in numeric_columns:
                if col in filtered_df.columns:
                    correlation_data[col] = pd.to_numeric(filtered_df[col], errors='coerce')
            
            if len(correlation_data) > 1:
                corr_df = pd.DataFrame(correlation_data).corr()
                
                fig = px.imshow(
                    corr_df,
                    text_auto=True,
                    aspect="auto",
                    title="Correlation Matrix of Performance Metrics",
                    color_continuous_scale="RdBu_r"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Time-based Analysis
            if 'call_date' in filtered_df.columns:
                st.markdown("### 📅 Time-based Performance Analysis")
                
                # Prepare time-based data
                time_df = filtered_df.copy()
                
                # Convert safely
                time_df['call_date'] = pd.to_datetime(time_df['call_date'], errors='coerce')
                time_df['call_start_time'] = pd.to_datetime(time_df['call_start_time'], errors='coerce')
                
                # Extract hour + day of week
                time_df['hour'] = time_df['call_start_time'].dt.hour.fillna(0).astype(int)
                time_df['day_of_week'] = time_df['call_date'].dt.day_name()
                
                # Streamlit layout
                col1, col2 = st.columns(2)
                
                with col1:
                    # Performance by hour
                    hourly_performance = time_df.groupby('hour').agg({
                        'call_success': lambda x: (x.str.lower() == 'yes').mean() * 100,
                        'sentiment_score': lambda x: pd.to_numeric(x, errors='coerce').mean()
                    }).round(2)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=hourly_performance.index,
                        y=hourly_performance['call_success'],
                        mode='lines+markers',
                        name='Success Rate %',
                        line=dict(color='green')
                    ))
                    
                    fig.update_layout(
                        title="Success Rate by Hour of Day",
                        xaxis_title="Hour",
                        yaxis_title="Success Rate %"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Performance by day of week
                    daily_performance = time_df.groupby('day_of_week').agg({
                        'call_id': 'count',
                        'call_success': lambda x: (x.str.lower() == 'yes').sum()
                    })
                    daily_performance['success_rate'] = (
                        daily_performance['call_success'] / daily_performance['call_id'] * 100
                    )
                    
                    # Reorder days
                    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    daily_performance = daily_performance.reindex(
                        [day for day in day_order if day in daily_performance.index]
                    )
                    
                    fig = px.bar(
                        daily_performance.reset_index(),
                        x='day_of_week',
                        y='success_rate',
                        title="Success Rate by Day of Week",
                        color='success_rate',
                        color_continuous_scale="Viridis"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Agent Performance Deep Dive
            st.markdown("### 👥 Agent Performance Deep Dive")
            
            agent_analysis = filtered_df.groupby('voice_agent_name').agg({
                'call_id': 'count',
                'call_success': lambda x: (x.str.lower() == 'yes').sum(),
                'appointment_scheduled': lambda x: (x.str.lower() == 'yes').sum(),
                'sentiment_score': lambda x: pd.to_numeric(x, errors='coerce').mean(),
                'call_duration_seconds': lambda x: pd.to_numeric(x, errors='coerce').mean(),
                'ai_accuracy_score': lambda x: pd.to_numeric(x, errors='coerce').mean(),
                'conversion_probability': lambda x: pd.to_numeric(x, errors='coerce').mean()
            }).round(2)
            
            agent_analysis.columns = [
                'Total Calls', 'Successful Calls', 'Appointments', 'Avg Sentiment',
                'Avg Duration (sec)', 'AI Accuracy', 'Avg Conversion Prob'
            ]
            
            agent_analysis['Success Rate %'] = (
                agent_analysis['Successful Calls'] / agent_analysis['Total Calls'] * 100
            ).round(1)
            
            agent_analysis['Appointment Rate %'] = (
                agent_analysis['Appointments'] / agent_analysis['Total Calls'] * 100
            ).round(1)
            
            st.dataframe(agent_analysis, use_container_width=True)
            
            # Performance scatter plot
            if len(agent_analysis) > 1:
                fig = px.scatter(
                    agent_analysis.reset_index(),
                    x='Success Rate %',
                    y='Avg Sentiment',
                    size='Total Calls',
                    color='AI Accuracy',
                    hover_name='voice_agent_name',
                    title="Agent Performance: Success Rate vs Sentiment",
                    labels={'Avg Sentiment': 'Average Sentiment Score'}
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No data available for advanced analytics with current filters.")

# Settings Tab (Desktop only)
if not mobile_mode:
    with tab6:
        st.markdown("## ⚙️ Dashboard Settings & Configuration")
        
        # Data refresh settings
        st.markdown("### 🔄 Data Management")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Data Refresh")
            if st.button("🔄 Force Refresh Data", type="primary"):
                st.cache_data.clear()
                st.rerun()  # Use st.experimental_rerun() to refresh the app
            
            auto_refresh = st.checkbox("Auto-refresh every 5 minutes", value=False)
            if auto_refresh:
                st.info("⏰ Auto-refresh enabled. Data will update automatically.")
        
        with col2:
            st.markdown("#### 💾 Cache Management")
        
            
            cache_info = example_cached_function.cache_info()
            st.write(f"📈 Cache hits: {cache_info.hits}")
            st.write(f"❌ Cache misses: {cache_info.misses}")
            
            if st.button("🗑️ Clear All Cache"):
                st.cache_data.clear()
                st.success("✅ Cache cleared successfully!")
        
        st.divider()
        
        # Display settings
        st.markdown("### 🎨 Display Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 📱 Layout Options")
            theme_option = st.selectbox(
                "Dashboard Theme",
                ["Auto", "Light", "Dark"],
                help="Choose your preferred dashboard theme"
            )
            
            compact_mode = st.checkbox(
                "Compact Mode",
                help="Reduce spacing and use smaller elements"
            )
        
        with col2:
            st.markdown("#### 📊 Chart Settings")
            default_chart_height = st.slider("Default Chart Height", 200, 800, 400)
            show_data_labels = st.checkbox("Show Data Labels on Charts", value=True)
            
        with col3:
            st.markdown("#### 🔊 Audio Settings")
            audio_autoplay = st.checkbox("Enable Audio Autoplay", value=False)
            audio_quality = st.selectbox("Preferred Audio Quality", ["Auto", "High", "Medium", "Low"])
        
        st.divider()
        
        # System information
        st.markdown("### 📋 System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔧 Technical Details")
            st.write(f"**Streamlit Version:** {st.__version__}")
            st.write(f"**Python Version:** 3.8+")
            st.write(f"**Last Data Load:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"**Total Records:** {len(df)}")
            st.write(f"**Filtered Records:** {len(filtered_df)}")
        
        with col2:
            st.markdown("#### 📊 Performance Stats")
            if len(df) > 0:
                data_quality_score = (
                    (df['customer_name'].notna().sum() / len(df)) * 0.3 +
                    (df['call_recording_url'].astype(str).str.len().gt(5).sum() / len(df)) * 0.3 +
                    (pd.to_numeric(df['sentiment_score'], errors='coerce').notna().sum() / len(df)) * 0.4
                ) * 100
                
                st.metric("Data Quality Score", f"{data_quality_score:.1f}%")
                st.metric("Audio Coverage", f"{(df['call_recording_url'].astype(str).str.len() > 5).sum()}/{len(df)}")
                
                # Data completeness by column
                completeness = {}
                key_columns = ['customer_name', 'voice_agent_name', 'call_success', 'sentiment_score']
                for col in key_columns:
                    if col in df.columns:
                        completeness[col] = (df[col].notna().sum() / len(df)) * 100
                
                if completeness:
                    completeness_df = pd.DataFrame(list(completeness.items()), columns=['Column', 'Completeness %'])
                    fig = px.bar(
                        completeness_df,
                        x='Column',
                        y='Completeness %',
                        title="Data Completeness by Column"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Help and documentation
        st.markdown("### 📚 Help & Documentation")
        
        with st.expander("🚀 Getting Started Guide"):
            st.markdown("""
            **Welcome to the Enhanced Call Analysis CRM!**
            
            1. **Authentication**: Ensure your Google Service Account credentials are properly configured
            2. **Filtering**: Use the sidebar filters to narrow down your data
            3. **Navigation**: Explore different tabs for various insights:
               - 📊 **Dashboard**: Executive overview and KPIs
               - 📋 **Call Log**: Detailed call records with pagination
               - 🧠 **AI Insights**: Intelligent analysis and summaries
               - 🔊 **Audio Center**: Universal audio player for recordings
               - 📈 **Advanced Analytics**: Deep-dive business intelligence
               - ⚙️ **Settings**: Configuration and system management
            
            4. **Export**: Use the export functionality to download filtered data
            5. **Mobile**: Toggle mobile mode for optimized mobile experience
            """)
        
        with st.expander("🔊 Audio Format Support"):
            st.markdown("""
            **Supported Audio Formats:**
            
            ✅ **Natively Supported**: MP3, WAV, OGG
            🔄 **Browser Dependent**: FLAC, AAC, M4A, WEBM, OGA, OPUS
            📱 **Mobile Optimized**: MP4, 3GP, AMR
            
            **Troubleshooting Audio Issues:**
            - Ensure audio URLs are publicly accessible
            - For Google Drive links, set sharing to "Anyone with link"
            - Use direct file URLs when possible
            - Check browser compatibility for specific formats
            - Mobile devices may have limited format support
            """)
        
        with st.expander("📊 Analytics Explained"):
            st.markdown("""
            **Key Metrics Definitions:**
            
            - **Success Rate**: Percentage of calls marked as successful
            - **Sentiment Score**: AI-calculated customer sentiment (-1 to +1)
            - **Confidence Score**: AI confidence in call analysis (0 to 1)
            - **Conversion Probability**: Likelihood of customer conversion
            - **Lead Quality Score**: Assessment of lead potential
            - **Customer LTV**: Customer Lifetime Value estimation
            
            **Chart Interpretations:**
            - **Correlation Matrix**: Shows relationships between metrics
            - **Performance Radar**: Multi-dimensional agent assessment
            - **Time Series**: Trends over time periods
            - **Distribution Charts**: Data spread and patterns
            """)
        
        with st.expander("🛠️ Troubleshooting"):
            st.markdown("""
            **Common Issues & Solutions:**
            
            **Authentication Problems:**
            - Verify service account JSON is valid and complete
            - Check Google Sheets API permissions
            - Ensure spreadsheet is shared with service account email
            
            **Data Loading Issues:**
            - Clear cache and refresh data
            - Check internet connection
            - Verify spreadsheet URL is correct
            - Ensure all expected columns exist in the sheet
            
            **Performance Issues:**
            - Use filters to reduce data volume
            - Enable mobile mode for better performance
            - Clear browser cache if charts don't load
            - Reduce page size for large datasets
            
            **Audio Playback Problems:**
            - Check audio URL accessibility
            - Try different browser for format compatibility
            - Use manual download link as fallback
            - Verify audio file isn't corrupted
            """)

# Footer with enhanced information
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem 0; color: #666;">
    <h3>✨ Enhanced Call Analysis CRM Dashboard v2.0</h3>
    <p><strong>🚀 Features:</strong> Real-time Analytics | Universal Audio Support | Mobile Optimization | Advanced Filtering | AI Insights</p>
    <p><strong>🎵 Audio Formats:</strong> MP3, WAV, OGG, FLAC, AAC, M4A, WEBM, OGA, OPUS, MP4, 3GP, AMR</p>
    <p><strong>📱 Mobile Ready:</strong> Responsive design with mobile-optimized layouts and controls</p>
    <p><strong>🔄 Live Data:</strong> Direct Google Sheets integration with 5-minute caching for optimal performance</p>
</div>
""", unsafe_allow_html=True)

# Performance monitoring and optimization
if not mobile_mode:
    # Add performance metrics at the bottom for debugging
    with st.expander("🔧 Developer Information", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Data Statistics:**")
            st.write(f"• Total rows loaded: {len(df)}")
            st.write(f"• Filtered rows: {len(filtered_df)}")
            st.write(f"• Memory usage: ~{len(df) * len(EXPECTED_COLUMNS) * 50 // 1024}KB")
            st.write(f"• Columns: {len(EXPECTED_COLUMNS)}")
        
        with col2:
            st.markdown("**Performance Metrics:**")
            if 'load_start_time' not in st.session_state:
                st.session_state.load_start_time = time.time()
            
            load_time = time.time() - st.session_state.load_start_time
            st.write(f"• Page load time: {load_time:.2f}s")
            st.write(f"• Data source: {'Live' if data_loaded else 'Cached'}")
            st.write(f"• Mobile mode: {'✅' if mobile_mode else '❌'}")
            st.write(f"• Auto-refresh: {'✅' if 'auto_refresh' in locals() and auto_refresh else '❌'}")
        
        with col3:
            st.markdown("**System Resources:**")
            st.write(f"• Streamlit version: {st.__version__}")
            st.write(f"• Session state size: {len(st.session_state)} items")
            st.write(f"• Cache status: {'Active' if st.cache_data.get_stats() else 'Inactive'}")
            st.write(f"• Timestamp: {datetime.datetime.now().strftime('%H:%M:%S')}")

# Auto-refresh functionality
if 'auto_refresh' in locals() and auto_refresh:
    time.sleep(300)  # 5 minutes
    st.rerun()

# Success message
if data_loaded and len(filtered_df) > 0:
    st.success(f"✅ Dashboard loaded successfully! Showing {len(filtered_df)} calls with advanced analytics, universal audio support, and mobile optimization.")
elif not data_loaded:
    st.warning("⚠️ Using demo mode. Upload credentials to access live data.")
else:
    st.info("🔍 No data matches current filters. Try adjusting your search criteria.")
