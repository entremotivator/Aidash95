import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Enhanced Project Management System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for light blue theme
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #e3f2fd 0%, #f0f8ff 100%);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 15px;
        padding: 10px;
        backdrop-filter: blur(10px);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 10px;
        color: #1976d2;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2196f3, #1976d2);
        color: white;
        box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(33, 150, 243, 0.2);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(33, 150, 243, 0.2);
    }
    
    .task-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #2196f3;
        transition: all 0.3s ease;
    }
    
    .task-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 20px rgba(33, 150, 243, 0.2);
    }
    
    .priority-high {
        border-left-color: #f44336 !important;
    }
    
    .priority-medium {
        border-left-color: #ff9800 !important;
    }
    
    .priority-low {
        border-left-color: #4caf50 !important;
    }
    
    .status-done {
        background: linear-gradient(135deg, #e8f5e8, #f1f8e9);
        border-left-color: #4caf50 !important;
    }
    
    .status-doing {
        background: linear-gradient(135deg, #fff3e0, #fef7e0);
        border-left-color: #ff9800 !important;
    }
    
    .status-todo {
        background: linear-gradient(135deg, #ffebee, #fce4ec);
        border-left-color: #f44336 !important;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #e3f2fd 0%, #f0f8ff 100%);
    }
    
    .stSelectbox > div > div {
        background-color: white;
        border: 2px solid #e3f2fd;
        border-radius: 10px;
    }
    
    .stTextInput > div > div > input {
        background-color: white;
        border: 2px solid #e3f2fd;
        border-radius: 10px;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #2196f3, #1976d2);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(33, 150, 243, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Google Sheets integration
SHEET_ID = "1NOOKyz9iUzwcsV0EcNJdVNQgQVL9bu3qsn_9wg7e1lE"
SHEET_NAME = "Tasks"  # Tab name in the sheet
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data(ttl=60)  # Cache for 1 minute
def load_live_tasks():
    """Load tasks from Google Sheets live link"""
    try:
        df = pd.read_csv(CSV_URL)
        # Clean column names
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading live data: {str(e)}")
        # Fallback to sample data
        return pd.DataFrame({
            'Task ID': ['ID1', 'ID2', 'ID3'],
            'Executor': ['John Doe', 'Jane Smith', 'Bob Wilson'],
            'Date': ['2025-08-05', '2025-08-06', '2025-08-07'],
            'Reminder Time': ['09:00', '14:00', '10:30'],
            'Task Description': ['Sample Task 1', 'Sample Task 2', 'Sample Task 3'],
            'Object': ['Object 1', 'Object 2', 'Object 3'],
            'Section': ['Section A', 'Section B', 'Section C'],
            'Priority': ['High', 'Medium', 'Low'],
            'Executor ID': ['1001', '1002', '1003'],
            'Company': ['Company A', 'Company B', 'Company C'],
            'Reminder Sent': ['Yes', 'No', 'Yes'],
            'Reminder Sent Date': ['2025-08-05', '', '2025-08-07'],
            'Reminder Read': ['Yes', 'No', 'No'],
            'Read Time': ['09:15', '', ''],
            'Reminder Count': ['1', '0', '2'],
            'Reminder Interval if No Report': ['24h', '12h', '6h'],
            'Status': ['In Progress', 'Pending', 'Completed'],
            'Comment': ['On track', 'Waiting for approval', 'Done'],
            'Report Date': ['2025-08-05', '', '2025-08-07']
        })

# Load data
tasks_df = load_live_tasks()

# Sidebar
st.sidebar.title("🔧 System Controls")
st.sidebar.markdown("---")

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (60s)", value=True)
if auto_refresh:
    st.sidebar.success("✅ Live data enabled")
else:
    st.sidebar.info("⏸️ Auto-refresh disabled")

# Refresh button
if st.sidebar.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

# Filters
st.sidebar.markdown("### 🔍 Filters")
selected_executor = st.sidebar.multiselect(
    "Executor",
    options=tasks_df['Executor'].unique() if 'Executor' in tasks_df.columns else [],
    default=[]
)

selected_priority = st.sidebar.multiselect(
    "Priority",
    options=tasks_df['Priority'].unique() if 'Priority' in tasks_df.columns else [],
    default=[]
)

selected_status = st.sidebar.multiselect(
    "Status",
    options=tasks_df['Status'].unique() if 'Status' in tasks_df.columns else [],
    default=[]
)

selected_company = st.sidebar.multiselect(
    "Company",
    options=tasks_df['Company'].unique() if 'Company' in tasks_df.columns else [],
    default=[]
)

# Apply filters
filtered_df = tasks_df.copy()
if selected_executor:
    filtered_df = filtered_df[filtered_df['Executor'].isin(selected_executor)]
if selected_priority:
    filtered_df = filtered_df[filtered_df['Priority'].isin(selected_priority)]
if selected_status:
    filtered_df = filtered_df[filtered_df['Status'].isin(selected_status)]
if selected_company:
    filtered_df = filtered_df[filtered_df['Company'].isin(selected_company)]

# Main title
st.title("📊 Enhanced Project Management System")
st.markdown("### 🔗 Live Google Sheets Integration")
st.markdown("---")

# Navigation tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Dashboard", 
    "✅ Task Management", 
    "📊 Analytics", 
    "⏰ Reminders", 
    "📈 Reports",
    "⚙️ Settings"
])

with tab1:
    st.header("📋 Dashboard Overview")
    
    # Key metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_tasks = len(filtered_df)
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #1976d2; margin: 0;">📝 Total Tasks</h3>
            <h1 style="color: #2196f3; margin: 10px 0;">{total_tasks}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        completed_tasks = len(filtered_df[filtered_df['Status'].str.contains('Completed|Done', case=False, na=False)])
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #4caf50; margin: 0;">✅ Completed</h3>
            <h1 style="color: #4caf50; margin: 10px 0;">{completed_tasks}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        in_progress_tasks = len(filtered_df[filtered_df['Status'].str.contains('Progress|Doing', case=False, na=False)])
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #ff9800; margin: 0;">🔄 In Progress</h3>
            <h1 style="color: #ff9800; margin: 10px 0;">{in_progress_tasks}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        high_priority = len(filtered_df[filtered_df['Priority'].str.contains('High', case=False, na=False)])
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #f44336; margin: 0;">🔥 High Priority</h3>
            <h1 style="color: #f44336; margin: 10px 0;">{high_priority}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        unique_executors = filtered_df['Executor'].nunique() if 'Executor' in filtered_df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #9c27b0; margin: 0;">👥 Executors</h3>
            <h1 style="color: #9c27b0; margin: 10px 0;">{unique_executors}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Status Distribution")
        if 'Status' in filtered_df.columns:
            status_counts = filtered_df['Status'].value_counts()
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                color_discrete_sequence=['#2196f3', '#4caf50', '#ff9800', '#f44336']
            )
            fig_status.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Priority Distribution")
        if 'Priority' in filtered_df.columns:
            priority_counts = filtered_df['Priority'].value_counts()
            fig_priority = px.bar(
                x=priority_counts.index,
                y=priority_counts.values,
                color=priority_counts.index,
                color_discrete_map={'High': '#f44336', 'Medium': '#ff9800', 'Low': '#4caf50'}
            )
            fig_priority.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Priority",
                yaxis_title="Count"
            )
            st.plotly_chart(fig_priority, use_container_width=True)

with tab2:
    st.header("✅ Task Management")
    
    # Add new task section
    with st.expander("➕ Add New Task", expanded=False):
        with st.form("new_task_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                new_task_id = st.text_input("Task ID")
                new_executor = st.text_input("Executor")
                new_date = st.date_input("Date")
                new_reminder_time = st.time_input("Reminder Time")
                new_task_description = st.text_area("Task Description")
                new_object = st.text_input("Object")
            
            with col2:
                new_section = st.text_input("Section")
                new_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
                new_executor_id = st.text_input("Executor ID")
                new_company = st.text_input("Company")
                new_reminder_sent = st.selectbox("Reminder Sent", ["Yes", "No"])
                new_reminder_sent_date = st.date_input("Reminder Sent Date")
            
            with col3:
                new_reminder_read = st.selectbox("Reminder Read", ["Yes", "No"])
                new_read_time = st.time_input("Read Time")
                new_reminder_count = st.number_input("Reminder Count", min_value=0, value=0)
                new_reminder_interval = st.text_input("Reminder Interval if No Report")
                new_status = st.selectbox("Status", ["Pending", "In Progress", "Completed"])
                new_comment = st.text_area("Comment")
                new_report_date = st.date_input("Report Date")
            
            submitted = st.form_submit_button("Add Task", use_container_width=True)
            
            if submitted and new_task_id and new_executor:
                st.success(f"✅ Task '{new_task_id}' would be added to the system!")
                st.info("💡 Note: This is a demo. In production, this would update the Google Sheet.")
    
    # Task cards view
    st.subheader("📋 Current Tasks")
    
    # View options
    view_mode = st.radio("View Mode", ["Cards", "Table"], horizontal=True)

if view_mode == "Cards":
    # Display tasks as cards
    for idx, task in filtered_df.iterrows():
        # Safely handle missing values in Series
        priority = str(task['Priority']) if 'Priority' in task and pd.notna(task['Priority']) else 'medium'
        status = str(task['Status']) if 'Status' in task and pd.notna(task['Status']) else 'todo'

        priority_class = f"priority-{priority.lower()}"
        status_class = f"status-{status.lower().replace(' ', '')}"

        st.markdown(f"""
        <div class="task-card {priority_class} {status_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; color: #1976d2;">
                    🆔 {task.get('Task ID', 'N/A') if isinstance(task, dict) else task.get('Task ID', 'N/A') if 'Task ID' in task else 'N/A'} 
                    - {task.get('Task Description', 'No description') if isinstance(task, dict) else task['Task Description'] if 'Task Description' in task else 'No description'}
                </h4>
                <span style="background: #e3f2fd; padding: 5px 10px; border-radius: 15px; font-size: 12px; color: #1976d2;">
                    {priority}
                </span>
            </div>
            <p style="margin: 10px 0; color: #666;">
                <strong>👤 Executor:</strong> {task['Executor'] if 'Executor' in task and pd.notna(task['Executor']) else 'N/A'} | 
                <strong>🏢 Company:</strong> {task['Company'] if 'Company' in task and pd.notna(task['Company']) else 'N/A'} | 
                <strong>📅 Date:</strong> {task['Date'] if 'Date' in task and pd.notna(task['Date']) else 'N/A'}
            </p>
            <p style="margin: 10px 0; color: #666;">
                <strong>📍 Section:</strong> {task['Section'] if 'Section' in task and pd.notna(task['Section']) else 'N/A'} | 
                <strong>🎯 Object:</strong> {task['Object'] if 'Object' in task and pd.notna(task['Object']) else 'N/A'} | 
                <strong>📊 Status:</strong> {status}
            </p>
            <p style="margin: 10px 0; color: #666;">
                <strong>⏰ Reminder:</strong> {task['Reminder Time'] if 'Reminder Time' in task and pd.notna(task['Reminder Time']) else 'N/A'} | 
                <strong>📧 Sent:</strong> {task['Reminder Sent'] if 'Reminder Sent' in task and pd.notna(task['Reminder Sent']) else 'N/A'} | 
                <strong>👁️ Read:</strong> {task['Reminder Read'] if 'Reminder Read' in task and pd.notna(task['Reminder Read']) else 'N/A'}
            </p>
            <p style="margin: 10px 0; color: #666;">
                <strong>💬 Comment:</strong> {task['Comment'] if 'Comment' in task and pd.notna(task['Comment']) else 'No comment'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # Display as table
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=600
        )

with tab3:
    st.header("📊 Analytics & Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👥 Tasks by Executor")
        if 'Executor' in filtered_df.columns:
            executor_counts = filtered_df['Executor'].value_counts()
            fig_executor = px.bar(
                x=executor_counts.values,
                y=executor_counts.index,
                orientation='h',
                color=executor_counts.values,
                color_continuous_scale='Blues'
            )
            fig_executor.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Number of Tasks",
                yaxis_title="Executor"
            )
            st.plotly_chart(fig_executor, use_container_width=True)
    
    with col2:
        st.subheader("🏢 Tasks by Company")
        if 'Company' in filtered_df.columns:
            company_counts = filtered_df['Company'].value_counts()
            fig_company = px.pie(
                values=company_counts.values,
                names=company_counts.index,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_company.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig_company, use_container_width=True)
    
    # Timeline analysis
    st.subheader("📅 Task Timeline")
    if 'Date' in filtered_df.columns:
        try:
            filtered_df['Date'] = pd.to_datetime(filtered_df['Date'])
            daily_tasks = filtered_df.groupby(filtered_df['Date'].dt.date).size().reset_index()
            daily_tasks.columns = ['Date', 'Task Count']
            
            fig_timeline = px.line(
                daily_tasks,
                x='Date',
                y='Task Count',
                markers=True,
                color_discrete_sequence=['#2196f3']
            )
            fig_timeline.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Date",
                yaxis_title="Number of Tasks"
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
        except:
            st.info("📅 Date format not recognized for timeline analysis")

with tab4:
    st.header("⏰ Reminder Management")
    
    # Reminder statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        reminders_sent = len(filtered_df[filtered_df['Reminder Sent'].str.contains('Yes', case=False, na=False)])
        st.metric("📧 Reminders Sent", reminders_sent)
    
    with col2:
        reminders_read = len(filtered_df[filtered_df['Reminder Read'].str.contains('Yes', case=False, na=False)])
        st.metric("👁️ Reminders Read", reminders_read)
    
    with col3:
        avg_reminder_count = filtered_df['Reminder Count'].astype(str).str.extract(r'(\d+)').astype(float).mean().iloc[0] if 'Reminder Count' in filtered_df.columns else 0
        st.metric("📊 Avg Reminder Count", f"{avg_reminder_count:.1f}")
    
    with col4:
        pending_reminders = len(filtered_df[
            (filtered_df['Reminder Sent'].str.contains('No', case=False, na=False)) |
            (filtered_df['Reminder Read'].str.contains('No', case=False, na=False))
        ])
        st.metric("⏳ Pending Actions", pending_reminders)
    
    # Reminder details table
    st.subheader("📋 Reminder Details")
    reminder_columns = ['Task ID', 'Executor', 'Task Description', 'Reminder Time', 
                       'Reminder Sent', 'Reminder Sent Date', 'Reminder Read', 'Read Time']
    available_columns = [col for col in reminder_columns if col in filtered_df.columns]
    
    if available_columns:
        st.dataframe(
            filtered_df[available_columns],
            use_container_width=True,
            height=400
        )

with tab5:
    st.header("📈 Reports & Export")
    
    # Export options
    st.subheader("📥 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export to CSV", use_container_width=True):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"tasks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if st.button("📋 Export to Excel", use_container_width=True):
            st.info("📋 Excel export would be available in production version")
    
    with col3:
        if st.button("📄 Generate Report", use_container_width=True):
            st.info("📄 PDF report generation would be available in production version")
    
    # Summary statistics
    st.subheader("📊 Summary Statistics")
    
    if not filtered_df.empty:
        summary_data = {
            "Metric": [
                "Total Tasks",
                "Unique Executors", 
                "Unique Companies",
                "High Priority Tasks",
                "Completed Tasks",
                "Reminders Sent",
                "Reminders Read"
            ],
            "Value": [
                len(filtered_df),
                filtered_df['Executor'].nunique() if 'Executor' in filtered_df.columns else 0,
                filtered_df['Company'].nunique() if 'Company' in filtered_df.columns else 0,
                len(filtered_df[filtered_df['Priority'].str.contains('High', case=False, na=False)]),
                len(filtered_df[filtered_df['Status'].str.contains('Completed|Done', case=False, na=False)]),
                len(filtered_df[filtered_df['Reminder Sent'].str.contains('Yes', case=False, na=False)]),
                len(filtered_df[filtered_df['Reminder Read'].str.contains('Yes', case=False, na=False)])
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

with tab6:
    st.header("⚙️ System Settings")
    
    st.subheader("🔗 Data Source Configuration")
    st.info(f"📊 **Google Sheets ID:** {SHEET_ID}")
    st.info(f"📋 **Sheet Name:** {SHEET_NAME}")
    st.info(f"🔗 **CSV URL:** {CSV_URL}")
    
    st.subheader("🔄 Refresh Settings")
    st.info("⏱️ **Cache TTL:** 60 seconds")
    st.info("🔄 **Auto-refresh:** Enabled in sidebar")
    
    st.subheader("📊 Data Quality")
    if not tasks_df.empty:
        st.success(f"✅ **Data loaded successfully:** {len(tasks_df)} records")
        st.info(f"📅 **Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show column information
        st.subheader("📋 Available Columns")
        cols_info = pd.DataFrame({
            'Column': tasks_df.columns,
            'Type': [str(dtype) for dtype in tasks_df.dtypes],
            'Non-null Count': [tasks_df[col].count() for col in tasks_df.columns]
        })
        st.dataframe(cols_info, use_container_width=True, hide_index=True)
    else:
        st.error("❌ **No data available**")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #e3f2fd, #f0f8ff); border-radius: 15px; margin-top: 20px;">
    <h3 style="color: #1976d2; margin: 0;">🚀 Enhanced Project Management System</h3>
    <p style="color: #666; margin: 10px 0;">Live Google Sheets Integration • Real-time Data • Advanced Analytics</p>
    <p style="color: #999; margin: 0; font-size: 12px;">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh functionality
if auto_refresh:
    import time
    time.sleep(60)
    st.rerun()

