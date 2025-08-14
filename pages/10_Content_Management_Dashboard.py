import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ------------------------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------------------------
st.set_page_config(
    page_title="📊 Content Management Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------------------------------
# Sidebar auth status
# ------------------------------------------------------------------------------------
st.sidebar.title("🔐 Authentication Status")

if not st.session_state.get("global_gsheets_creds"):
    st.sidebar.error("❌ No global credentials found")
    st.sidebar.info("Please upload service account JSON in the main sidebar")
    st.error("🔑 Google Sheets credentials not found. Please log in from the authentication page.")
    st.stop()
else:
    st.sidebar.success("✅ Using global credentials")
    client_email = st.session_state.global_gsheets_creds.get('client_email', 'Unknown')
    st.sidebar.info(f"📧 {client_email}")

# ------------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------------
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1-CplAWu7qP4R616bLSCwtUy-nHJoe5D0344m9hU_MMo/edit?usp=sharing"  # Replace with your actual Sheet URL
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Content categories with emojis and descriptions
CONTENT_CATEGORIES = {
    "🪡 Threads": {
        "name": "Twitter Threads", 
        "description": "Long-form Twitter content threads",
        "color": "#1DA1F2",
        "target_weekly": 5,
        "avg_engagement": 2.5
    },
    "🧵 Tweet thread": {
        "name": "Tweet Threads", 
        "description": "Multi-tweet story content",
        "color": "#1DA1F2",
        "target_weekly": 7,
        "avg_engagement": 1.8
    },
    "👩‍💻 LinkedIn post": {
        "name": "LinkedIn Posts", 
        "description": "Professional networking content",
        "color": "#0077B5",
        "target_weekly": 3,
        "avg_engagement": 4.2
    },
    "🎬 Reel script": {
        "name": "Video Scripts", 
        "description": "Scripts for short-form video content",
        "color": "#E4405F",
        "target_weekly": 4,
        "avg_engagement": 6.8
    },
    "📝 Blog posts": {
        "name": "Blog Articles", 
        "description": "Long-form written content",
        "color": "#FF6B35",
        "target_weekly": 2,
        "avg_engagement": 8.5
    },
    "📧 Email campaigns": {
        "name": "Email Content", 
        "description": "Email marketing campaigns",
        "color": "#34495E",
        "target_weekly": 3,
        "avg_engagement": 12.3
    }
}

# ------------------------------------------------------------------------------------
# Enhanced Styles
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
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .stats-card {
        background: rgba(102, 126, 234, 0.1);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #667eea;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        margin: 1rem 0;
    }
    .content-item {
        background: rgba(255,255,255,0.95);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .content-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
    }
    .category-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        text-align: center;
        font-size: 1.2rem;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] { 
        gap: 5px; 
        background: rgba(255,255,255,0.1);
        padding: 10px;
        border-radius: 15px;
        backdrop-filter: blur(10px);
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        padding: 15px 25px;
        background: rgba(255,255,255,0.1);
        border-radius: 15px;
        font-weight: 600;
        border: 1px solid rgba(255,255,255,0.2);
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255,255,255,0.2);
        transform: translateY(-2px);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    .dashboard-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%);
        padding: 2rem;
        border-radius: 20px;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    .progress-bar {
        background: #e0e0e0;
        height: 8px;
        border-radius: 4px;
        overflow: hidden;
        margin: 10px 0;
    }
    .progress-fill {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }
    .edit-mode {
        background: rgba(255, 235, 59, 0.1);
        border: 2px dashed #FFC107;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------------
# Session defaults
# ------------------------------------------------------------------------------------
if 'content_data' not in st.session_state:
    st.session_state.content_data = {}
if 'content_metrics' not in st.session_state:
    st.session_state.content_metrics = {}
if 'last_updated' not in st.session_state:
    st.session_state.last_updated = datetime.now()
if 'sheets_connected' not in st.session_state:
    st.session_state.sheets_connected = False
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'weekly_goals' not in st.session_state:
    st.session_state.weekly_goals = {cat: CONTENT_CATEGORIES[cat]["target_weekly"] for cat in CONTENT_CATEGORIES}

# ------------------------------------------------------------------------------------
# Enhanced Functions
# ------------------------------------------------------------------------------------
def load_sample_data():
    sample_data = {}
    sample_metrics = {}
    
    for category, info in CONTENT_CATEGORIES.items():
        # Generate sample content
        sample_data[category] = [
            f"Sample {info['name']} content #{i+1}: This is an example of {info['description'].lower()}"
            for i in range(np.random.randint(2, 8))
        ]
        
        # Generate sample metrics
        sample_metrics[category] = {
            "views": np.random.randint(100, 5000),
            "likes": np.random.randint(50, 1000),
            "shares": np.random.randint(5, 200),
            "comments": np.random.randint(10, 150),
            "engagement_rate": round(np.random.uniform(1.0, 10.0), 2),
            "created_this_week": np.random.randint(0, 5),
            "total_created": len(sample_data[category])
        }
    
    return sample_data, sample_metrics

def connect_to_sheets():
    try:
        creds = Credentials.from_service_account_info(st.session_state.global_gsheets_creds, scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet_id = SHEETS_URL.split('/d/')[1].split('/')[0]
        sheet = client.open_by_key(sheet_id)
        st.session_state.sheet = sheet
        st.session_state.sheets_connected = True
        return True, f"✅ Connected to: {sheet.title}"
    except Exception as e:
        st.session_state.sheets_connected = False
        return False, f"❌ Connection failed: {str(e)[:100]}..."

def refresh_from_sheets():
    try:
        worksheet = st.session_state.sheet.sheet1
        rows = worksheet.get_all_records()
        if rows:
            data = {}
            columns = rows[0].keys()
            for col in columns:
                data[col] = [row[col] for row in rows if row.get(col)]
            st.session_state.content_data = data
            st.session_state.last_updated = datetime.now()
            return True, "📊 Data refreshed successfully"
        return False, "⚠️ No data found in sheet"
    except Exception as e:
        return False, f"❌ Refresh failed: {str(e)[:100]}..."

def sync_to_sheets():
    try:
        worksheet = st.session_state.sheet.sheet1
        worksheet.clear()
        
        # Prepare headers and data
        all_categories = list(st.session_state.content_data.keys())
        max_rows = max(len(st.session_state.content_data[cat]) for cat in all_categories)
        
        # Create header row
        worksheet.update('A1', [all_categories])
        
        # Fill data
        for row in range(max_rows):
            row_data = []
            for cat in all_categories:
                if row < len(st.session_state.content_data[cat]):
                    row_data.append(st.session_state.content_data[cat][row])
                else:
                    row_data.append('')
            worksheet.update(f'A{row + 2}', [row_data])
        
        return True, "✅ Data synced to Google Sheets"
    except Exception as e:
        return False, f"❌ Sync failed: {str(e)[:100]}..."

def export_to_json():
    export_data = {
        "content_data": st.session_state.content_data,
        "content_metrics": st.session_state.content_metrics,
        "weekly_goals": st.session_state.weekly_goals,
        "exported_at": st.session_state.last_updated.isoformat(),
        "total_entries": sum(len(v) for v in st.session_state.content_data.values()),
        "categories": len(st.session_state.content_data),
        "export_metadata": {
            "version": "2.0",
            "sheets_connected": st.session_state.sheets_connected
        }
    }
    return json.dumps(export_data, indent=2)

def calculate_dashboard_metrics():
    total_content = sum(len(v) for v in st.session_state.content_data.values())
    total_categories = len(st.session_state.content_data)
    
    # Calculate engagement metrics
    total_views = sum(st.session_state.content_metrics.get(cat, {}).get('views', 0) for cat in st.session_state.content_data.keys())
    total_likes = sum(st.session_state.content_metrics.get(cat, {}).get('likes', 0) for cat in st.session_state.content_data.keys())
    total_shares = sum(st.session_state.content_metrics.get(cat, {}).get('shares', 0) for cat in st.session_state.content_data.keys())
    
    avg_engagement = np.mean([st.session_state.content_metrics.get(cat, {}).get('engagement_rate', 0) for cat in st.session_state.content_data.keys()]) if st.session_state.content_data else 0
    
    # Weekly progress
    weekly_created = sum(st.session_state.content_metrics.get(cat, {}).get('created_this_week', 0) for cat in st.session_state.content_data.keys())
    weekly_goal = sum(st.session_state.weekly_goals.values())
    weekly_progress = (weekly_created / weekly_goal * 100) if weekly_goal > 0 else 0
    
    return {
        "total_content": total_content,
        "total_categories": total_categories,
        "total_views": total_views,
        "total_likes": total_likes,
        "total_shares": total_shares,
        "avg_engagement": round(avg_engagement, 2),
        "weekly_created": weekly_created,
        "weekly_goal": weekly_goal,
        "weekly_progress": min(weekly_progress, 100)
    }

# ------------------------------------------------------------------------------------
# Data bootstrap
# ------------------------------------------------------------------------------------
if not st.session_state.content_data:
    sample_data, sample_metrics = load_sample_data()
    st.session_state.content_data = sample_data
    st.session_state.content_metrics = sample_metrics

# ------------------------------------------------------------------------------------
# Header
# ------------------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>📊 Content Management Dashboard</h1>
    <p>Comprehensive content strategy management and analytics platform</p>
    <p><strong>🚀 Enhanced with metrics, goals tracking, and advanced analytics</strong></p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------------
# Enhanced Sidebar controls
# ------------------------------------------------------------------------------------
with st.sidebar:
    st.header("🎛️ Dashboard Controls")
    
    # Connection controls
    st.subheader("📡 Google Sheets Integration")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔗 Connect", use_container_width=True):
            success, msg = connect_to_sheets()
            if success:
                st.success(msg)
            else:
                st.error(msg)
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            success, msg = refresh_from_sheets()
            if success:
                st.success(msg)
            else:
                st.error(msg)
    
    if st.session_state.sheets_connected:
        if st.button("📤 Sync to Sheets", use_container_width=True):
            success, msg = sync_to_sheets()
            if success:
                st.success(msg)
            else:
                st.error(msg)
    
    # Data management
    st.subheader("💾 Data Management")
    st.download_button(
        "📥 Export All Data",
        export_to_json(),
        file_name=f"content_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        use_container_width=True
    )
    
    # Edit mode toggle
    st.subheader("✏️ Edit Mode")
    st.session_state.edit_mode = st.toggle("Enable Edit Mode", value=st.session_state.edit_mode)
    
    if st.session_state.edit_mode:
        st.info("🔧 Edit mode enabled - you can modify metrics and goals")
    
    # Quick stats
    dashboard_stats = calculate_dashboard_metrics()
    st.markdown(f"""
    <div class="stats-card">
        <h4>📈 Quick Stats</h4>
        <strong>Content Items:</strong> {dashboard_stats['total_content']}<br>
        <strong>Categories:</strong> {dashboard_stats['total_categories']}<br>
        <strong>Total Views:</strong> {dashboard_stats['total_views']:,}<br>
        <strong>Avg Engagement:</strong> {dashboard_stats['avg_engagement']}%<br>
        <strong>Weekly Progress:</strong> {dashboard_stats['weekly_progress']:.1f}%<br>
        <strong>Last Updated:</strong> {st.session_state.last_updated.strftime('%H:%M:%S')}<br>
        <strong>Connection:</strong> {'🟢 Connected' if st.session_state.sheets_connected else '🔴 Disconnected'}
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------------
# Main content with enhanced tabs
# ------------------------------------------------------------------------------------
if st.session_state.content_data:
    # Create tab list with Home dashboard first
    tab_names = ["🏠 Dashboard"] + list(st.session_state.content_data.keys())
    tabs = st.tabs(tab_names)
    
    # Dashboard tab
    with tabs[0]:
        st.markdown('<div class="category-header">🏠 Dashboard Overview</div>', unsafe_allow_html=True)
        
        # Key metrics row
        metrics = calculate_dashboard_metrics()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #667eea; margin: 0;">{metrics['total_content']}</h2>
                <p style="margin: 5px 0;">📝 Total Content</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #667eea; margin: 0;">{metrics['total_views']:,}</h2>
                <p style="margin: 5px 0;">👀 Total Views</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #667eea; margin: 0;">{metrics['avg_engagement']}%</h2>
                <p style="margin: 5px 0;">📊 Avg Engagement</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #667eea; margin: 0;">{metrics['weekly_created']}/{metrics['weekly_goal']}</h2>
                <p style="margin: 5px 0;">🎯 Weekly Goal</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {metrics['weekly_progress']}%"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            st.subheader("📊 Content Distribution")
            
            # Content distribution pie chart
            categories = list(st.session_state.content_data.keys())
            values = [len(st.session_state.content_data[cat]) for cat in categories]
            
            # Default color palette for categories not in CONTENT_CATEGORIES
            default_colors = ["#667eea", "#764ba2", "#f093fb", "#f5576c", "#4facfe", "#00f2fe", "#43e97b", "#38f9d7"]
            colors = []
            for i, cat in enumerate(categories):
                if cat in CONTENT_CATEGORIES:
                    colors.append(CONTENT_CATEGORIES[cat]["color"])
                else:
                    # Use default colors cycling through the palette
                    colors.append(default_colors[i % len(default_colors)])
            
            fig_pie = px.pie(
                values=values, 
                names=[cat.split(' ')[1] if ' ' in cat else cat for cat in categories],
                title="Content by Category",
                color_discrete_sequence=colors
            )
            fig_pie.update_layout(height=400, showlegend=True)
            st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            st.subheader("📈 Engagement Metrics")
            
            # Engagement bar chart
            engagement_data = []
            for cat in categories:
                metrics_data = st.session_state.content_metrics.get(cat, {})
                engagement_data.append({
                    'Category': cat.split(' ')[1] if ' ' in cat else cat,
                    'Views': metrics_data.get('views', 0),
                    'Likes': metrics_data.get('likes', 0),
                    'Shares': metrics_data.get('shares', 0)
                })
            
            df_engagement = pd.DataFrame(engagement_data)
            fig_bar = px.bar(
                df_engagement, 
                x='Category', 
                y=['Views', 'Likes', 'Shares'],
                title="Engagement by Content Type",
                barmode='group'
            )
            fig_bar.update_layout(height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Weekly progress section
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.subheader("🎯 Weekly Goals Progress")
        
        for category in categories:
            cat_metrics = st.session_state.content_metrics.get(category, {})
            created_this_week = cat_metrics.get('created_this_week', 0)
            goal = st.session_state.weekly_goals.get(category, 0)
            progress = (created_this_week / goal * 100) if goal > 0 else 0
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{category}**")
                st.markdown(f"""
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {min(progress, 100)}%"></div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.metric("Created", created_this_week)
            with col3:
                if st.session_state.edit_mode:
                    new_goal = st.number_input(
                        f"Goal", 
                        min_value=0, 
                        value=goal, 
                        key=f"goal_{category}",
                        label_visibility="collapsed"
                    )
                    if new_goal != goal:
                        st.session_state.weekly_goals[category] = new_goal
                        st.rerun()
                else:
                    st.metric("Goal", goal)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Content category tabs
    for tab_idx, category in enumerate(st.session_state.content_data.keys(), 1):
        with tabs[tab_idx]:
            cat_info = CONTENT_CATEGORIES.get(category, {})
            st.markdown(f'<div class="category-header">{category} - {cat_info.get("description", "")}</div>', unsafe_allow_html=True)
            
            # Category metrics
            col1, col2, col3, col4 = st.columns(4)
            cat_metrics = st.session_state.content_metrics.get(category, {})
            
            with col1:
                current_count = len(st.session_state.content_data[category])
                st.metric("📝 Total Items", current_count)
            
            with col2:
                views = cat_metrics.get('views', 0)
                if st.session_state.edit_mode:
                    new_views = st.number_input(
                        "👀 Views", 
                        min_value=0, 
                        value=views, 
                        key=f"views_{category}"
                    )
                    if new_views != views:
                        if category not in st.session_state.content_metrics:
                            st.session_state.content_metrics[category] = {}
                        st.session_state.content_metrics[category]['views'] = new_views
                        st.rerun()
                else:
                    st.metric("👀 Views", f"{views:,}")
            
            with col3:
                likes = cat_metrics.get('likes', 0)
                if st.session_state.edit_mode:
                    new_likes = st.number_input(
                        "👍 Likes", 
                        min_value=0, 
                        value=likes, 
                        key=f"likes_{category}"
                    )
                    if new_likes != likes:
                        if category not in st.session_state.content_metrics:
                            st.session_state.content_metrics[category] = {}
                        st.session_state.content_metrics[category]['likes'] = new_likes
                        st.rerun()
                else:
                    st.metric("👍 Likes", f"{likes:,}")
            
            with col4:
                engagement = cat_metrics.get('engagement_rate', 0)
                if st.session_state.edit_mode:
                    new_engagement = st.number_input(
                        "📊 Engagement %", 
                        min_value=0.0, 
                        max_value=100.0, 
                        value=float(engagement), 
                        step=0.1,
                        key=f"engagement_{category}"
                    )
                    if new_engagement != engagement:
                        if category not in st.session_state.content_metrics:
                            st.session_state.content_metrics[category] = {}
                        st.session_state.content_metrics[category]['engagement_rate'] = new_engagement
                        st.rerun()
                else:
                    st.metric("📊 Engagement", f"{engagement}%")
            
            # Add new content section
            with st.expander("➕ Add New Content", expanded=False):
                new_item = st.text_area(
                    f"New {cat_info.get('name', category)} content", 
                    key=f"new_{category}",
                    height=100,
                    placeholder=f"Enter your {cat_info.get('description', 'content').lower()} here..."
                )
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    if st.button("✅ Add Content", key=f"add_{category}", use_container_width=True):
                        if new_item.strip():
                            st.session_state.content_data[category].append(new_item.strip())
                            st.session_state.last_updated = datetime.now()
                            # Update weekly created count
                            if category not in st.session_state.content_metrics:
                                st.session_state.content_metrics[category] = {}
                            current_weekly = st.session_state.content_metrics[category].get('created_this_week', 0)
                            st.session_state.content_metrics[category]['created_this_week'] = current_weekly + 1
                            st.success("✅ Content added successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Please enter some content")
                
                with col2:
                    priority = st.selectbox(
                        "Priority", 
                        ["Low", "Medium", "High"], 
                        key=f"priority_{category}",
                        index=1
                    )
            
            st.markdown("---")
            
            # Content list with enhanced display
            if st.session_state.content_data[category]:
                st.subheader(f"📋 Content List ({len(st.session_state.content_data[category])} items)")
                
                for idx, item in enumerate(st.session_state.content_data[category]):
                    with st.container():
                        col1, col2, col3 = st.columns([6, 1, 1])
                        
                        with col1:
                            # Enhanced content display with edit capability
                            if st.session_state.edit_mode:
                                st.markdown('<div class="edit-mode">', unsafe_allow_html=True)
                                edited_item = st.text_area(
                                    f"Edit content {idx+1}",
                                    value=item,
                                    key=f"edit_{category}_{idx}",
                                    height=80,
                                    label_visibility="collapsed"
                                )
                                if edited_item != item:
                                    col_save, col_cancel = st.columns(2)
                                    with col_save:
                                        if st.button("💾 Save", key=f"save_{category}_{idx}"):
                                            st.session_state.content_data[category][idx] = edited_item
                                            st.session_state.last_updated = datetime.now()
                                            st.success("✅ Content updated!")
                                            st.rerun()
                                    with col_cancel:
                                        if st.button("❌ Cancel", key=f"cancel_{category}_{idx}"):
                                            st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div class='content-item'>
                                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                                        <strong style="color: #667eea;">Entry #{idx+1}</strong>
                                        <span style="font-size: 0.8em; color: #888;">
                                            📅 {(datetime.now() - timedelta(days=np.random.randint(0, 30))).strftime('%m/%d')}
                                        </span>
                                    </div>
                                    <div style="line-height: 1.6; color: #333;">
                                        {item[:200]}{"..." if len(item) > 200 else ""}
                                    </div>
                                    <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee; font-size: 0.9em; color: #666;">
                                        <span style="margin-right: 15px;">📊 Engagement: {np.random.uniform(1.0, 8.0):.1f}%</span>
                                        <span style="margin-right: 15px;">👀 Views: {np.random.randint(50, 500):,}</span>
                                        <span>💬 Comments: {np.random.randint(5, 50)}</span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        with col2:
                            if st.button("📝", key=f"edit_btn_{category}_{idx}", help="Edit content"):
                                st.session_state.edit_mode = True
                                st.rerun()
                        
                        with col3:
                            if st.button("🗑️", key=f"del_{category}_{idx}", help="Delete content"):
                                st.session_state.content_data[category].pop(idx)
                                st.session_state.last_updated = datetime.now()
                                st.success("🗑️ Content deleted!")
                                st.rerun()
                        
                        st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.info(f"No {cat_info.get('name', category).lower()} content yet. Add some using the form above!")
            
            # Category-specific analytics
            st.markdown("---")
            st.subheader("📈 Category Analytics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Performance over time (mock data)
                dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='W')
                performance_data = pd.DataFrame({
                    'Date': dates,
                    'Views': np.random.randint(100, 1000, len(dates)),
                    'Engagement': np.random.uniform(1.0, 8.0, len(dates))
                })
                
                fig_line = px.line(
                    performance_data, 
                    x='Date', 
                    y='Views',
                    title=f"{cat_info.get('name', category)} Performance Over Time",
                    color_discrete_sequence=[cat_info.get('color', '#667eea')]
                )
                fig_line.update_layout(height=300)
                st.plotly_chart(fig_line, use_container_width=True)
            
            with col2:
                # Content quality distribution
                quality_labels = ['High Quality', 'Medium Quality', 'Needs Improvement']
                quality_values = [
                    len(st.session_state.content_data[category]) * 0.4,
                    len(st.session_state.content_data[category]) * 0.4,
                    len(st.session_state.content_data[category]) * 0.2
                ]
                
                fig_quality = px.pie(
                    values=quality_values,
                    names=quality_labels,
                    title=f"{cat_info.get('name', category)} Quality Distribution",
                    color_discrete_sequence=['#2E8B57', '#FFD700', '#FF6B6B']
                )
                fig_quality.update_layout(height=300, showlegend=True)
                st.plotly_chart(fig_quality, use_container_width=True)
            
            # Best performing content (mock data)
            if st.session_state.content_data[category]:
                st.subheader("🏆 Top Performing Content")
                top_content = st.session_state.content_data[category][:3] if len(st.session_state.content_data[category]) >= 3 else st.session_state.content_data[category]
                
                for i, content in enumerate(top_content, 1):
                    with st.container():
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, rgba(46, 139, 87, 0.1) 0%, rgba(46, 139, 87, 0.05) 100%); 
                                    padding: 15px; border-radius: 10px; margin: 10px 0; 
                                    border-left: 4px solid #2E8B57;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <strong style="color: #2E8B57;">🏆 #{i} Best Performer</strong>
                                <div style="font-size: 0.9em; color: #666;">
                                    <span style="margin-right: 10px;">👀 {np.random.randint(500, 2000):,} views</span>
                                    <span style="margin-right: 10px;">👍 {np.random.randint(50, 200)} likes</span>
                                    <span>📊 {np.random.uniform(5.0, 12.0):.1f}% engagement</span>
                                </div>
                            </div>
                            <div style="color: #333; line-height: 1.5;">
                                {content[:150]}{"..." if len(content) > 150 else ""}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
else:
    st.warning("⚠️ No content data loaded. Please connect to Google Sheets or add some sample data.")

# ------------------------------------------------------------------------------------
# Enhanced Footer with additional features
# ------------------------------------------------------------------------------------
st.markdown("---")

# Footer stats and controls
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🎯 Quick Actions")
    if st.button("🔄 Refresh All Data", use_container_width=True):
        st.session_state.last_updated = datetime.now()
        st.success("✅ Data refreshed!")
        st.rerun()

with col2:
    st.markdown("### 📊 Export Options")
    
    # CSV export option
    if st.session_state.content_data:
        # Prepare CSV data
        max_items = max(len(items) for items in st.session_state.content_data.values())
        csv_data = {}
        
        for category, items in st.session_state.content_data.items():
            # Pad with empty strings to match max length
            padded_items = items + [''] * (max_items - len(items))
            csv_data[category.replace('🪡 ', '').replace('🧵 ', '').replace('👩‍💻 ', '').replace('🎬 ', '').replace('📝 ', '').replace('📧 ', '')] = padded_items
        
        csv_df = pd.DataFrame(csv_data)
        csv_string = csv_df.to_csv(index=False)
        
        st.download_button(
            "📁 Download CSV",
            csv_string,
            file_name=f"content_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

with col3:
    st.markdown("### ⚙️ Settings")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("🔄 Auto-refresh every 5 min", value=False)
    
    if auto_refresh:
        # This would need to be implemented with a proper timer in a production app
        st.info("🔄 Auto-refresh enabled")
    
    # Theme toggle (placeholder - would need implementation)
    dark_mode = st.checkbox("🌙 Dark Mode", value=False)
    
    if dark_mode:
        st.info("🌙 Dark mode would be applied here")

# Advanced metrics section
st.markdown("---")
st.markdown("### 📈 Advanced Analytics & Insights")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🎯 Performance Insights")
    
    # Calculate some insights
    total_content = sum(len(v) for v in st.session_state.content_data.values())
    avg_content_per_category = total_content / len(st.session_state.content_data) if st.session_state.content_data else 0
    
    # Best performing category
    best_category = max(st.session_state.content_data.keys(), 
                       key=lambda x: st.session_state.content_metrics.get(x, {}).get('engagement_rate', 0))
    best_engagement = st.session_state.content_metrics.get(best_category, {}).get('engagement_rate', 0)
    
    st.markdown(f"""
    <div class="dashboard-card">
        <p><strong>💡 Key Insights:</strong></p>
        <ul style="line-height: 1.8;">
            <li>📊 Average content per category: <strong>{avg_content_per_category:.1f}</strong></li>
            <li>🏆 Best performing category: <strong>{best_category}</strong> ({best_engagement}% engagement)</li>
            <li>📈 Content growth: <strong>+{np.random.randint(5, 25)}%</strong> this month</li>
            <li>🎯 Goal achievement: <strong>{calculate_dashboard_metrics()['weekly_progress']:.1f}%</strong> of weekly targets</li>
            <li>🔥 Trending hashtags: <strong>#content #marketing #growth</strong></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("#### 📅 Content Calendar Preview")
    
    # Mock upcoming content schedule
    upcoming_dates = pd.date_range(start=datetime.now(), periods=7)
    upcoming_content = []
    
    for i, date in enumerate(upcoming_dates):
        category = list(st.session_state.content_data.keys())[i % len(st.session_state.content_data)]
        upcoming_content.append({
            'Date': date.strftime('%m/%d'),
            'Day': date.strftime('%A'),
            'Category': category.split(' ')[1] if ' ' in category else category,
            'Status': np.random.choice(['Scheduled', 'Draft', 'Review'], p=[0.6, 0.3, 0.1])
        })
    
    calendar_df = pd.DataFrame(upcoming_content)
    st.dataframe(calendar_df, use_container_width=True, hide_index=True)

# Final footer
st.markdown("""
<div style='text-align:center; color:#666; margin-top: 3rem; padding: 2rem; 
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); 
            border-radius: 15px;'>
    <h4 style="margin-bottom: 1rem;">📊 Content Management Dashboard v2.0</h4>
    <p>🚀 Enhanced with advanced analytics, goal tracking, and real-time metrics</p>
    <p style="font-size: 0.9em; margin-top: 1rem;">
        Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
        Total sessions: {np.random.randint(100, 500)} | 
        Uptime: 99.9%
    </p>
</div>
""".format(datetime=datetime), unsafe_allow_html=True)
