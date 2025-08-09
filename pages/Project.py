import streamlit as st
import pandas as pd
import json
from data_manager import DataManager
import io
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import numpy as np
import uuid
from typing import Dict, List, Any
import base64
import hashlib

# Page configuration
st.set_page_config(
    page_title="Advanced Project Management System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS for premium UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
    }
    
    .main-header::before {
        content: \'\';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url("data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\"><defs><pattern id=\"grain\" width=\"100\" height=\"100\" patternUnits=\"userSpaceOnUse\"><circle cx=\"25\" cy=\"25\" r=\"1\" fill=\"white\" opacity=\"0.1\"/><circle cx=\"75\" cy=\"75\" r=\"1\" fill=\"white\" opacity=\"0.1\"/><circle cx=\"50\" cy=\"10\" r=\"0.5\" fill=\"white\" opacity=\"0.1\"/></pattern></defs><rect width=\"100\" height=\"100\" fill=\"url(%23grain)\"/></svg>");
        opacity: 0.1;
    }
    
    .main-header h1 {
        position: relative;
        z-index: 1;
        margin: 0;
        font-size: 3.5rem;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        position: relative;
        z-index: 1;
        margin: 1rem 0 0 0;
        font-size: 1.3rem;
        opacity: 0.95;
        font-weight: 300;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        border: 1px solid rgba(255,255,255,0.2);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 48px rgba(0,0,0,0.12);
    }
    
    .metric-card::before {
        content: \'\';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    
    .metric-value {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1;
    }
    
    .metric-label {
        color: #6c757d;
        font-size: 1rem;
        margin: 0.5rem 0 0 0;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-icon {
        position: absolute;
        top: 1.5rem;
        right: 1.5rem;
        font-size: 2rem;
        opacity: 0.1;
    }
    
    .status-badge {
        padding: 0.4rem 1rem;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 600;
        text-align: center;
        display: inline-block;
        margin: 0.2rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: none;
    }
    
    .status-active { 
        background: linear-gradient(135deg, #d4edda, #c3e6cb); 
        color: #155724; 
        box-shadow: 0 2px 8px rgba(21, 87, 36, 0.2);
    }
    .status-pending { 
        background: linear-gradient(135deg, #fff3cd, #ffeaa7); 
        color: #856404; 
        box-shadow: 0 2px 8px rgba(133, 100, 4, 0.2);
    }
    .status-completed { 
        background: linear-gradient(135deg, #cce5ff, #74b9ff); 
        color: #004085; 
        box-shadow: 0 2px 8px rgba(0, 64, 133, 0.2);
    }
    .status-overdue { 
        background: linear-gradient(135deg, #f8d7da, #ff7675); 
        color: #721c24; 
        box-shadow: 0 2px 8px rgba(114, 28, 36, 0.2);
    }
    
    .card-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
    }
    
    .project-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .project-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 48px rgba(102, 126, 234, 0.4);
    }
    
    .project-card::before {
        content: \'\';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url("data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\"><defs><pattern id=\"dots\" width=\"20\" height=\"20\" patternUnits=\"userSpaceOnUse\"><circle cx=\"10\" cy=\"10\" r=\"1\" fill=\"white\" opacity=\"0.1\"/></pattern></defs><rect width=\"100\" height=\"100\" fill=\"url(%23dots)\"/></svg>");
    }
    
    .task-card {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa500 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 6px 24px rgba(255, 107, 107, 0.3);
        transition: all 0.3s ease;
        position: relative;
    }
    
    .task-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(255, 107, 107, 0.4);
    }
    
    .client-card {
        background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 210, 255, 0.3);
        transition: all 0.3s ease;
    }
    
    .client-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 48px rgba(0, 210, 255, 0.4);
    }
    
    .team-card {
        background: linear-gradient(135deg, #8e44ad 0%, #3742fa 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(142, 68, 173, 0.3);
        transition: all 0.3s ease;
    }
    
    .team-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 48px rgba(142, 68, 173, 0.4);
    }
    
    .form-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2.5rem;
        border-radius: 20px;
        border: 2px dashed #dee2e6;
        margin-bottom: 2rem;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .integration-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
    }
    
    .integration-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 48px rgba(102, 126, 234, 0.4);
    }
    
    .priority-high { 
        border-left: 6px solid #dc3545 !important; 
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%) !important;
    }
    .priority-medium { 
        border-left: 6px solid #ffc107 !important; 
        background: linear-gradient(135deg, #ffa500 0%, #ff7675 100%) !important;
    }
    .priority-low { 
        border-left: 6px solid #28a745 !important; 
        background: linear-gradient(135deg, #00b894 0%, #00cec9 100%) !important;
    }
    
    .kanban-column {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 16px;
        margin: 0.5rem;
        min-height: 400px;
        box-shadow: 0 6px 24px rgba(0,0,0,0.08);
    }
    
    .kanban-header {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #dee2e6;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .progress-bar {
        background: #e9ecef;
        border-radius: 10px;
        height: 12px;
        overflow: hidden;
        margin: 1rem 0;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 10px;
        transition: width 0.6s ease;
        position: relative;
    }
    
    .progress-fill::after {
        content: \'\';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent 25%, rgba(255,255,255,0.2) 25%, rgba(255,255,255,0.2) 50%, transparent 50%, transparent 75%, rgba(255,255,255,0.2) 75%);
        background-size: 20px 20px;
        animation: progress-animation 1s linear infinite;
    }
    
    @keyframes progress-animation {
        0% { background-position: 0 0; }
        100% { background-position: 20px 0; }
    }
    
    .notification {
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid;
        backdrop-filter: blur(10px);
    }
       .notification-success {
        background: linear-gradient(135deg, rgba(212, 237, 218, 0.9), rgba(195, 230, 203, 0.9));
        border-left-color: #28a745;
        color: #155724;
       .notification-warning {
        background: linear-gradient(135deg, rgba(255, 243, 205, 0.9), rgba(255, 234, 167, 0.9));
        border-left-color: #ffc107;
        color: #856404;
    }
      .notification-info {
        background: linear-gradient(135deg, rgba(204, 229, 255, 0.9), rgba(116, 185, 255, 0.9));
        border-left-color: #007bff;
        color: #004085;
    }   
    .sidebar-metric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        text-align: center;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    }
    
    .sidebar-metric h3 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    .sidebar-metric p {
        margin: 0.25rem 0 0 0;
        font-size: 0.85rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .timeline-item {
        position: relative;
        padding-left: 2rem;
        margin-bottom: 1.5rem;
    }
    
    .timeline-item::before {
        content: \'\';
        position: absolute;
        left: 0;
        top: 0.5rem;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea, #764ba2);
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.2);
    }
    
    .timeline-content {
        background: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        border-left: 4px solid #667eea;
    }
    
    .chart-container {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
    }
    
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        margin-bottom: 2rem;
    }
    
    .feature-highlight {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 40px rgba(240, 147, 251, 0.3);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px 12px 0 0;
        padding: 1rem 2rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize data manager and session state
@st.cache_resource
def get_data_manager():
    return DataManager()

dm = get_data_manager()

# Initialize session state
if 'data_refresh' not in st.session_state:
    st.session_state.data_refresh = 0
if 'selected_project' not in st.session_state:
    st.session_state.selected_project = None
if 'current_user' not in st.session_state:
    st.session_state.current_user = "Admin"
if 'notifications' not in st.session_state:
    st.session_state.notifications = []
if 'theme' not in st.session_state:
    st.session_state.theme = "light"

# Sidebar Configuration
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem 1rem; border-radius: 16px; color: white; text-align: center; margin-bottom: 2rem;">
    <h2 style="margin: 0; font-size: 1.5rem; font-weight: 700;">⚙️ Control Center</h2>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.9rem;">Manage your workspace</p>
</div>
""", unsafe_allow_html=True)

# User Profile Section
st.sidebar.markdown("### 👤 User Profile")
current_user = st.sidebar.selectbox("Current User", ["Admin", "Project Manager", "Developer", "Designer"], index=0)
st.session_state.current_user = current_user

st.sidebar.markdown("### 🔐 Google Cloud Integration")
uploaded_file = st.sidebar.file_uploader(
    "Upload JSON Service Account Key",
    type=['json'],
    help="Upload your Google Cloud service account JSON file for Google Sheets integration"
)

if uploaded_file is not None:
    try:
        service_account_info = json.load(uploaded_file)
        st.sidebar.success("✅ Service account connected!")
        st.sidebar.json({"project_id": service_account_info.get("project_id", "N/A")})
    except Exception as e:
        st.sidebar.error(f"❌ Connection failed: {str(e)}")

# Quick Actions
st.sidebar.markdown("### ⚡ Quick Actions")
if st.sidebar.button("🔄 Refresh All Data", use_container_width=True):
    st.cache_resource.clear()
    st.session_state.data_refresh += 1
    st.success("Data refreshed successfully!")
    st.rerun()

if st.sidebar.button("📊 Generate Report", use_container_width=True):
    st.sidebar.info("Report generation feature coming soon!")

if st.sidebar.button("🔔 Clear Notifications", use_container_width=True):
    st.session_state.notifications = []
    st.sidebar.success("Notifications cleared!")

# Load all data
@st.cache_data
def load_all_data():
    return {
        'projects': dm.load_projects(),
        'tasks': dm.load_tasks(),
        'clients': dm.load_clients(),
        'teams': dm.load_teams()
    }

data = load_all_data()

# Add quick stats to sidebar
st.sidebar.markdown("### 📈 Quick Stats")
if len(data['projects']) > 0:
    completed_projects = len(data['projects'][data['projects']['Status'] == 'Completed'])
    active_projects = len(data['projects'][data['projects']['Status'] == 'In Progress'])
    
    st.sidebar.markdown(f"""
    <div class="sidebar-metric">
        <h3>{completed_projects}</h3>
        <p>Completed Projects</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown(f"""
    <div class="sidebar-metric">
        <h3>{active_projects}</h3>
        <p>Active Projects</p>
    </div>
    """, unsafe_allow_html=True)

if len(data['tasks']) > 0:
    completed_tasks = len(data['tasks'][data['tasks']['Status'] == 'Done'])
    st.sidebar.markdown(f"""
    <div class="sidebar-metric">
        <h3>{completed_tasks}</h3>
        <p>Completed Tasks</p>
    </div>
    """, unsafe_allow_html=True)

# Main Application Header
st.markdown("""
<div class="main-header">
    <h1>🚀 Advanced Project Management System</h1>
    <p>Streamline your workflow with intelligent project tracking and team collaboration</p>
</div>
""", unsafe_allow_html=True)

# Notification System
if st.session_state.notifications:
    st.markdown("### 🔔 Recent Notifications")
    for notification in st.session_state.notifications[-3:]:  # Show last 3 notifications
        st.markdown(f"""
        <div class="notification notification-{notification['type']}">
            <strong>{notification['title']}</strong><br>
            {notification['message']}
            <small style="opacity: 0.7; float: right;">{notification['timestamp']}</small>
        </div>
        """, unsafe_allow_html=True)

# Helper Functions
def add_notification(title: str, message: str, type: str = "info"):
    """Add a notification to the session state"""
    notification = {
        'id': str(uuid.uuid4()),
        'title': title,
        'message': message,
        'type': type,
        'timestamp': datetime.now().strftime("%H:%M:%S")
    }
    st.session_state.notifications.append(notification)

def get_enhanced_status_badge(status: str) -> str:
    """Generate enhanced status badges"""
    status_lower = status.lower().replace(" ", "-")
    if "progress" in status_lower or "doing" in status_lower:
        return f'<span class="status-badge status-pending">🔄 {status}</span>'
    elif "completed" in status_lower or "done" in status_lower:
        return f'<span class="status-badge status-completed">✅ {status}</span>'
    elif "active" in status_lower:
        return f'<span class="status-badge status-active">🟢 {status}</span>'
    else:
        return f'<span class="status-badge status-overdue">⏰ {status}</span>'

def calculate_project_progress(project_name: str, tasks_df: pd.DataFrame) -> int:
    """Calculate project completion percentage"""
    if project_name not in tasks_df['Project Name'].values:
        return 0
    project_tasks = tasks_df[tasks_df['Project Name'] == project_name]
    if len(project_tasks) == 0:
        return 0
    completed_tasks = len(project_tasks[project_tasks['Status'] == 'Done'])
    return int((completed_tasks / len(project_tasks)) * 100)

def get_overdue_items(df: pd.DataFrame, date_column: str) -> pd.DataFrame:
    """Get overdue items from a dataframe"""
    today = datetime.now().date()
    df[date_column] = pd.to_datetime(df[date_column]).dt.date
    return df[df[date_column] < today]

def generate_project_timeline(projects_df: pd.DataFrame) -> List[Dict]:
    """Generate timeline data for projects"""
    timeline = []
    for _, project in projects_df.iterrows():
        timeline.append({
            'name': project['Project Name'],
            'start': project.get('Start Date', project['Due Date']),
            'end': project['Due Date'],
            'status': project['Status'],
            'progress': calculate_project_progress(project['Project Name'], data['tasks'])
        })
    return timeline

# Navigation Tabs with Enhanced Styling
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Dashboard", 
    "🏗️ Projects", 
    "✅ Tasks", 
    "👥 Clients", 
    "🔧 Teams",
    "📈 Analytics",
    "🔗 Integrations"
])

# ================================
# DASHBOARD TAB
# ================================
with tab1:
    st.markdown("## 📊 Comprehensive Dashboard")
    
    # Enhanced Key Metrics
    st.markdown("### 🎯 Key Performance Indicators")
    
    # Calculate advanced metrics
    total_budget = data['projects'].get('Budget', pd.Series([0])).sum() if 'Budget' in data['projects'].columns else 0
    completed_projects = len(data['projects'][data['projects']['Status'] == 'Completed']) if len(data['projects']) > 0 else 0
    overdue_tasks = len(get_overdue_items(data['tasks'], 'Due Date')) if len(data['tasks']) > 0 else 0
    team_utilization = len(data['tasks'][data['tasks']['Status'] == 'In Progress']) if len(data['tasks']) > 0 else 0
    
    # Metrics Grid
    metrics_html = f"""
    <div class="dashboard-grid">
        <div class="metric-card">
            <div class="metric-icon">🏗️</div>
            <h3 class="metric-value">{len(data['projects'])}</h3>
            <p class="metric-label">Total Projects</p>
            <div style="margin-top: 1rem; font-size: 0.9rem; color: #6c757d;">
                <span style="color: #28a745;">✅ {completed_projects} Completed</span>
            </div>
        </div>
        <div class="metric-card">
            <div class="metric-icon">✅</div>
            <h3 class="metric-value">{len(data['tasks'])}</h3>
            <p class="metric-label">Total Tasks</p>
            <div style="margin-top: 1rem; font-size: 0.9rem; color: #6c757d;">
                <span style="color: #dc3545;">⏰ {overdue_tasks} Overdue</span>
            </div>
        </div>
        <div class="metric-card">
            <div class="metric-icon">💰</div>
            <h3 class="metric-value">${total_budget:,.0f}</h3>
            <p class="metric-label">Total Budget</p>
            <div style="margin-top: 1rem; font-size: 0.9rem; color: #6c757d;">
                <span style="color: #007bff;">📊 Active Projects</span>
            </div>
        </div>
        <div class="metric-card">
            <div class="metric-icon">👥</div>
            <h3 class="metric-value">{len(data['teams'])}</h3>
            <p class="metric-label">Team Members</p>
            <div style="margin-top: 1rem; font-size: 0.9rem; color: #6c757d;">
                <span style="color: #ffc107;">🔄 {team_utilization} Active Tasks</span>
            </div>
        </div>
    </div>
    """
    st.markdown(metrics_html, unsafe_allow_html=True)
    
    # Enhanced Visualizations
    if len(data['projects']) > 0:
        st.markdown("### 📊 Advanced Analytics Dashboard")
        
        # Create visualization columns
        viz_col1, viz_col2 = st.columns(2)
        
        with viz_col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown("#### 🎯 Project Status Distribution")
            
            project_status_counts = data['projects']['Status'].value_counts()
            fig_projects = px.pie(
                values=project_status_counts.values,
                names=project_status_counts.index,
                title="Project Status Breakdown",
                color_discrete_sequence=['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4ecdc4'],
                hole=0.4
            )
            fig_projects.update_layout(
                showlegend=True, 
                height=400,
                font=dict(size=12),
                title_font_size=16
            )
            fig_projects.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
            st.plotly_chart(fig_projects, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with viz_col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown("#### 📈 Task Progress Overview")
            
            task_status_counts = data['tasks']['Status'].value_counts()
            fig_tasks = px.bar(
                x=task_status_counts.values,
                y=task_status_counts.index,
                orientation='h',
                title="Task Status Distribution",
                color=task_status_counts.values,
                color_continuous_scale='Viridis',
                text=task_status_counts.values
            )
            fig_tasks.update_layout(
                showlegend=False, 
                height=400,
                yaxis_title="Status",
                xaxis_title="Number of Tasks",
                font=dict(size=12)
            )
            fig_tasks.update_traces(
                texttemplate='%{text}',
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Tasks: %{x}<extra></extra>'
            )
            st.plotly_chart(fig_tasks, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Project Timeline Visualization
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("#### 📅 Project Timeline & Progress")
        
        if len(data['projects']) > 0:
            timeline_data = []
            for _, project in data['projects'].iterrows():
                progress = calculate_project_progress(project['Project Name'], data['tasks'])
                timeline_data.append(dict(
                    Task=project['Project Name'],
                    Start=project['Start Date'],
                    Finish=project['Due Date'],
                    Resource=project['Team'],
                    Complete=progress,
                    Status=project['Status']
                ))
            
            df_timeline = pd.DataFrame(timeline_data)
            
            if not df_timeline.empty:
                fig_timeline = px.timeline(df_timeline, 
                                            x_start="Start", 
                                            x_end="Finish", 
                                            y="Task", 
                                            color="Status",
                                            color_discrete_map={
                                                'In Progress': '#667eea',
                                                'Completed': '#28a745',
                                                'Pending': '#ffc107',
                                                'On Hold': '#dc3545'
                                            },
                                            title="Project Timeline",
                                            hover_name="Task",
                                            hover_data={
                                                "Start": "|%Y-%m-%d",
                                                "Finish": "|%Y-%m-%d",
                                                "Complete": True,
                                                "Status": True,
                                                "Resource": True
                                            })
                fig_timeline.update_yaxes(autorange="reversed")
                fig_timeline.update_layout(height=500, font=dict(size=12))
                st.plotly_chart(fig_timeline, use_container_width=True)
            else:
                st.info("No project data available for timeline visualization.")
        else:
            st.info("No project data available for timeline visualization.")
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.info("No data available to display the dashboard. Please add some projects and tasks.")

# ================================
# PROJECTS TAB
# ================================
with tab2:
    st.markdown("## 🏗️ Project Management")
    
    st.markdown("### ➕ Add New Project")
    with st.form("new_project_form", clear_on_submit=True):
        project_name = st.text_input("Project Name", placeholder="e.g., Website Redesign")
        project_client = st.selectbox("Client", [c['Name'] for c in data['clients'].to_dict(orient='records')], index=0 if not data['clients'].empty else None, format_func=lambda x: x if x is not None else "")
        project_team = st.selectbox("Assigned Team", [t['Name'] for t in data['teams'].to_dict(orient='records')], index=0 if not data['teams'].empty else None, format_func=lambda x: x if x is not None else "")
        project_budget = st.number_input("Budget ($)", min_value=0.0, format="%.2f")
        project_start_date = st.date_input("Start Date", datetime.now().date())
        project_due_date = st.date_input("Due Date", datetime.now().date() + timedelta(days=30))
        project_description = st.text_area("Description", placeholder="Brief overview of the project goals and scope")
        
        submitted = st.form_submit_button("Add Project")
        if submitted:
            if project_name and project_client and project_team:
                dm.add_project({
                    'Project Name': project_name,
                    'Client': project_client,
                    'Team': project_team,
                    'Budget': project_budget,
                    'Start Date': project_start_date.strftime("%Y-%m-%d"),
                    'Due Date': project_due_date.strftime("%Y-%m-%d"),
                    'Description': project_description,
                    'Status': 'In Progress'
                })
                add_notification("Project Added", f"Project '{project_name}' has been added successfully.", "success")
                st.session_state.data_refresh += 1
                st.rerun()
            else:
                st.error("Please fill in all required project fields (Name, Client, Team).")

    st.markdown("### 📋 All Projects")
    if not data['projects'].empty:
        projects_display = data['projects'].copy()
        projects_display['Progress'] = projects_display['Project Name'].apply(lambda x: calculate_project_progress(x, data['tasks']))
        projects_display['Status'] = projects_display['Status'].apply(get_enhanced_status_badge)
        
        st.dataframe(
            projects_display[[
                'Project Name', 'Client', 'Team', 'Budget', 'Start Date', 'Due Date', 'Status', 'Progress'
            ]].to_html(escape=False),
            unsafe_allow_html=True,
            hide_index=True,
            use_container_width=True
        )
        
        st.markdown("### 🔍 Project Details")
        selected_project_name = st.selectbox(
            "Select a project to view/update details:",
            options=data['projects']['Project Name'].tolist(),
            index=0 if not data['projects'].empty else None,
            key="project_detail_select"
        )
        
        if selected_project_name:
            selected_project = data['projects'][data['projects']['Project Name'] == selected_project_name].iloc[0]
            st.session_state.selected_project = selected_project
            
            with st.expander(f"Details for {selected_project_name}", expanded=True):
                st.write(f"**Client:** {selected_project['Client']}")
                st.write(f"**Team:** {selected_project['Team']}")
                st.write(f"**Budget:** ${selected_project['Budget']:,}")
                st.write(f"**Start Date:** {selected_project['Start Date']}")
                st.write(f"**Due Date:** {selected_project['Due Date']}")
                st.write(f"**Description:** {selected_project['Description']}")
                st.markdown(f"**Status:** {get_enhanced_status_badge(selected_project['Status'])}")
                
                current_progress = calculate_project_progress(selected_project_name, data['tasks'])
                st.markdown(f"**Overall Progress:**")
                st.markdown(f"""
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {current_progress}%;"></div>
                </div>
                <p style="text-align: right; margin-top: -10px;">{current_progress}% Complete</p>
                """, unsafe_allow_html=True)
                
                st.markdown("#### Update Project Status")
                new_status = st.selectbox(
                    "Select new status:",
                    options=['In Progress', 'Completed', 'Pending', 'On Hold'],
                    index=['In Progress', 'Completed', 'Pending', 'On Hold'].index(selected_project['Status'])
                )
                if st.button("Update Status"):
                    dm.update_project_status(selected_project_name, new_status)
                    add_notification("Status Updated", f"Status for '{selected_project_name}' updated to {new_status}.", "info")
                    st.session_state.data_refresh += 1
                    st.rerun()

    else:
        st.info("No projects added yet. Use the form above to add your first project!")

# ================================
# TASKS TAB
# ================================
with tab3:
    st.markdown("## ✅ Task Management")
    
    st.markdown("### ➕ Add New Task")
    with st.form("new_task_form", clear_on_submit=True):
        task_name = st.text_input("Task Name", placeholder="e.g., Develop user authentication")
        task_project = st.selectbox("Project", [p['Project Name'] for p in data['projects'].to_dict(orient='records')], index=0 if not data['projects'].empty else None, format_func=lambda x: x if x is not None else "")
        task_assignee = st.selectbox("Assignee", [t['Name'] for t in data['teams'].to_dict(orient='records')], index=0 if not data['teams'].empty else None, format_func=lambda x: x if x is not None else "")
        task_due_date = st.date_input("Due Date", datetime.now().date() + timedelta(days=7))
        task_priority = st.selectbox("Priority", ['Low', 'Medium', 'High'], index=1)
        task_description = st.text_area("Description", placeholder="Detailed steps or requirements for the task")
        
        submitted_task = st.form_submit_button("Add Task")
        if submitted_task:
            if task_name and task_project and task_assignee:
                dm.add_task({
                    'Task Name': task_name,
                    'Project Name': task_project,
                    'Assignee': task_assignee,
                    'Due Date': task_due_date.strftime("%Y-%m-%d"),
                    'Priority': task_priority,
                    'Description': task_description,
                    'Status': 'To Do'
                })
                add_notification("Task Added", f"Task '{task_name}' has been added successfully.", "success")
                st.session_state.data_refresh += 1
                st.rerun()
            else:
                st.error("Please fill in all required task fields (Name, Project, Assignee).")

    st.markdown("### 📋 All Tasks")
    if not data['tasks'].empty:
        tasks_display = data['tasks'].copy()
        tasks_display['Status'] = tasks_display['Status'].apply(get_enhanced_status_badge)
        tasks_display['Priority_Class'] = tasks_display['Priority'].apply(lambda x: f"priority-{x.lower()}")
        
        # Custom HTML for tasks with priority highlighting
        task_html = """<div class="task-list">"""
        for _, row in tasks_display.iterrows():
            task_html += f"""<div class="task-card {row['Priority_Class']}">
                <strong>{row['Task Name']}</strong><br>
                <small>Project: {row['Project Name']} | Assignee: {row['Assignee']} | Due: {row['Due Date']}</small><br>
                {row['Status']}
            </div>"""
        task_html += "</div>"
        st.markdown(task_html, unsafe_allow_html=True)

        st.markdown("###  Kanban Board")
        kanban_cols = st.columns(3)
        statuses = ["To Do", "In Progress", "Done"]
        for i, status in enumerate(statuses):
            with kanban_cols[i]:
                st.markdown(f"<div class="kanban-column"><h3 class="kanban-header">{status}</h3>", unsafe_allow_html=True)
                tasks_in_status = data["tasks"][data["tasks"]["Status"] == status]
                for _, task in tasks_in_status.iterrows():
                    st.markdown(f"""<div class="task-card priority-{task['Priority'].lower()}">
                        <strong>{task['Task Name']}</strong><br>
                        <small>Project: {task['Project Name']}</small><br>
                        <small>Assignee: {task['Assignee']}</small><br>
                        <small>Due: {task['Due Date']}</small>
                    </div>""", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info("No tasks added yet. Use the form above to add your first task!")

# ================================
# CLIENTS TAB
# ================================
with tab4:
    st.markdown("## 👥 Client Management")
    
    st.markdown("### ➕ Add New Client")
    with st.form("new_client_form", clear_on_submit=True):
        client_name = st.text_input("Client Name", placeholder="e.g., Innovate Corp")
        client_contact = st.text_input("Contact Person", placeholder="e.g., Jane Doe")
        client_email = st.text_input("Email", placeholder="e.g., jane.doe@innovate.com")
        
        submitted_client = st.form_submit_button("Add Client")
        if submitted_client:
            if client_name and client_email:
                dm.add_client({
                    "Name": client_name,
                    "Contact Person": client_contact,
                    "Email": client_email,
                    "Phone": st.text_input("Phone", placeholder="e.g., (555) 123-4567"), # Moved inside if block
                })
                add_notification("Client Added", f"Client '{client_name}' has been added successfully.", "success")
                st.session_state.data_refresh += 1
                st.rerun()
            else:
                st.error("Please fill in all required client fields (Name, Email).")

    st.markdown("### 📇 All Clients")
    if not data['clients'].empty:
        for _, client in data['clients'].iterrows():
            st.markdown(f"""<div class="client-card">
                <h3>{client['Name']}</h3>
                <p><strong>Contact:</strong> {client['Contact Person']}</p>
                <p><strong>Email:</strong> {client['Email']}</p>
                <p><strong>Phone:</strong> {client['Phone']}</p>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No clients added yet. Use the form above to add your first client!")

# ================================
# TEAMS TAB
# ================================
with tab5:
    st.markdown("## 🔧 Team Management")
    
    st.markdown("### ➕ Add New Team Member")
    with st.form("new_team_form", clear_on_submit=True):
        member_name = st.text_input("Member Name", placeholder="e.g., John Smith")
        member_role = st.text_input("Role", placeholder="e.g., Lead Developer")
        member_email = st.text_input("Email", placeholder="e.g., john.smith@example.com")
        
        submitted_member = st.form_submit_button("Add Team Member")
        if submitted_member:
            if member_name and member_email:
                dm.add_team_member({
                    "Name": member_name,
                    "Role": member_role,
                    "Email": member_email,
                    "Phone": st.text_input("Phone", placeholder="e.g., (555) 987-6543"), # Moved inside if block
                    "Department": st.text_input("Department", placeholder="e.g., Engineering"), # Moved inside if block
                })
                add_notification("Team Member Added", f"Team member '{member_name}' has been added successfully.", "success")
                st.session_state.data_refresh += 1
                st.rerun()
            else:
                st.error("Please fill in all required team member fields (Name, Email).")

    st.markdown("### 🤝 All Team Members")
    if not data['teams'].empty:
        for _, member in data['teams'].iterrows():
            st.markdown(f"""<div class="team-card">
                <h3>{member['Name']}</h3>
                <p><strong>Role:</strong> {member['Role']}</p>
                <p><strong>Email:</strong> {member['Email']}</p>
                <p><strong>Phone:</strong> {member['Phone']}</p>
                <p><strong>Department:</strong> {member['Department']}</p>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No team members added yet. Use the form above to add your first team member!")

# ================================
# ANALYTICS TAB
# ================================
with tab6:
    st.markdown("## 📈 Advanced Analytics")
    st.markdown("This section is under development. Future features will include:")
    st.markdown("""- Resource Utilization Heatmaps
- Historical Performance Trends
- Predictive Analytics for project completion and risks""")
    st.image("https://via.placeholder.com/800x400.png?text=Analytics+Dashboard+Coming+Soon", use_container_width=True)

# ================================
# INTEGRATIONS TAB
# ================================
with tab7:
    st.markdown("## 🔗 Integrations")
    st.markdown("Connect your project management system with other tools.")
    
    integration_cols = st.columns(3)
    with integration_cols[0]:
        st.markdown("""<div class="integration-card">
            <h3>GitHub</h3>
            <p>Connect with your code repositories.</p>
            <button>Connect</button>
        </div>""", unsafe_allow_html=True)
    with integration_cols[1]:
        st.markdown("""<div class="integration-card">
            <h3>Slack</h3>
            <p>Get real-time notifications.</p>
            <button>Connect</button>
        </div>""", unsafe_allow_html=True)
    with integration_cols[2]:
        st.markdown("""<div class="integration-card">
            <h3>Google Drive</h3>
            <p>Link your project documents.</p>
            <button>Connect</button>
        </div>""", unsafe_allow_html=True)


