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
SHEET_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
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

# ---------- Session State Initialization (GLOBAL) ----------
def initialize_session_state():
    defaults = {
        "connection_status": "sample",
        "events_data": create_sample_data() if 'events_data' not in st.session_state else st.session_state.events_data,
        "error_message": None,
        "client": None,
        "spreadsheet": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# ---------- Custom CSS and Title ----------
st.markdown("""
<style>
    .metric-card { background: linear-gradient(90deg, #667eea, #764ba2); padding:1rem; border-radius:10px; color:white; text-align:center; margin:0.5rem 0; }
    .status-badge { padding:0.25rem 0.75rem; border-radius:20px; font-size:0.8rem; font-weight:bold; }
    .confirmed { background-color:#28a745; color:white; } .pending { background-color:#ffc107; color:black; }
    .cancelled { background-color:#dc3545; color:white; } .completed { background-color:#6c757d; color:white; }
    .success-box { padding:1rem; background-color:#d4edda; border:1px solid #c3e6cb; border-radius:0.375rem; color:#155724; margin:1rem 0; }
    .warning-box { padding:1rem; background-color:#fff3cd; border:1px solid #ffeaa7; border-radius:0.375rem; color:#856404; margin:1rem 0; }
</style>
""", unsafe_allow_html=True)
st.title("🚀 Event Management CRM")

# ---------- Check Global Credentials ----------
if not st.session_state.get("global_gsheets_creds"):
    st.error("🔑 Google Sheets credentials not found. Please upload your service account JSON in the sidebar.")
    st.info("💡 Use the sidebar to upload your service account JSON file. It will be used across all pages.")
    st.stop()

# ---------- Data Load Function ----------
def load_data_from_sheets(sheet_url):
    creds = st.session_state.global_gsheets_creds
    try:
        creds_obj = ServiceAccountCredentials.from_json_keyfile_dict(creds, SHEET_SCOPE)
        client = gspread.authorize(creds_obj)
    except Exception as e:
        return None, None, f"Authentication failed: {e}"
    try:
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        spreadsheet = client.open_by_key(sheet_id)
    except Exception as e:
        return None, None, f"Spreadsheet access failed: {e}"
    try:
        worksheet = spreadsheet.get_worksheet(0)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data).dropna(how='all') if data else pd.DataFrame(columns=SHEET_COLUMNS)
        return df, (client, spreadsheet), None
    except Exception as e:
        return None, None, f"Error reading sheet: {e}"

# ---------- Helper Functions ----------
def create_sample_data():
    return pd.DataFrame({
        'Name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'],
        'Email': ['john@e.com', 'jane@e.com', 'bob@e.com', 'alice@e.com'],
        'Guest Email': ['g1@e.com', 'g2@e.com', '', 'g4@e.com'],
        'Status': ['Confirmed','Pending','Cancelled','Completed'],
        'Event ID': ['EVT001','EVT002','EVT003','EVT004'],
        'Start Time (12hr)': ['10:00 AM','2:00 PM','11:00 AM','3:00 PM'],
        'Start Time (24hr)': ['10:00','14:00','11:00','15:00'],
        'Meet Link': ['https://meet...',]*4,
        'Description': ['Standup','Presentation','Review','Training'],
        'Host': ['John','Jane','Bob','Alice'],
        'Unique Code': ['UC001','UC002','UC003','UC004'],
        'Upload_Timestamp': ['2024‑01‑15 09:00:00','2024‑01‑16 13:00:00','2024‑01‑17 10:00:00','2024‑01‑18 14:00:00']
    })

def refresh_data():
    if st.session_state.spreadsheet:
        df, _, err = load_data_from_sheets(STATIC_SHEET_URL)
        if err:
            st.error(err)
            st.session_state.connection_status = "error"
            st.session_state.error_message = err
        else:
            st.session_state.events_data = df
            st.session_state.client, st.session_state.spreadsheet = _ , _
            st.session_state.connection_status = "connected"
            st.session_state.error_message = None

def append_to_sheet(data_dict):
    if not st.session_state.spreadsheet:
        return False, "No spreadsheet connection"
    worksheet = st.session_state.spreadsheet.get_worksheet(0)
    row = [data_dict.get(c, '') for c in SHEET_COLUMNS]
    try:
        worksheet.append_row(row)
        refresh_data()
        return True, "Data added successfully!"
    except Exception as e:
        return False, str(e)

# ---------- Sidebar & Navigation ----------
def sidebar_navigation():
    st.sidebar.header("🔐 Authentication")
    st.sidebar.success("✅ Using Global Credentials")
    email = st.session_state.global_gsheets_creds.get('client_email', 'Unknown')
    st.sidebar.info(email)
    st.sidebar.markdown("---")
    page = st.sidebar.selectbox("Choose Page", [
        "📋 Dashboard","📅 Events","👥 Contacts","📈 Analytics","➕ Add Event","⚙️ Settings"
    ])
    st.sidebar.markdown("---")
    st.sidebar.markdown("✅ **Data Source**")
    if st.session_state.connection_status == "connected":
        st.sidebar.success("🔗 Google Sheets")
    elif st.session_state.connection_status == "error":
        st.sidebar.error("❌ Connection Error")
    else:
        st.sidebar.info("💻 Sample Data")
    return page

# ---------- Page Functions ----------
def show_dashboard():
    st.header("📋 Dashboard")
    df = st.session_state.events_data
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Events", len(df))
    c2.metric("Confirmed", len(df[df['Status']=='Confirmed'])) if 'Status' in df else None
    c3.metric("Pending", len(df[df['Status']=='Pending'])) if 'Status' in df else None
    c4.metric("Unique Hosts", df['Host'].nunique() if 'Host' in df else 0)
    if st.session_state.connection_status == "connected":
        if st.button("🔄 Refresh"):
            refresh_data()
            st.experimental_rerun()
    st.subheader("Recent Events")
    st.dataframe(df.head(10)[['Name','Email','Status','Start Time (12hr)','Host','Event ID']])
    
def show_events():
    st.header("📅 Events")
    df = st.session_state.events_data.copy()
    if df.empty:
        st.info("No events")
        return
    status_opts = ['All'] + df['Status'].unique().tolist() if 'Status' in df else ['All']
    host_opts = ['All'] + df['Host'].unique().tolist() if 'Host' in df else ['All']
    status = st.selectbox("Status", status_opts)
    host = st.selectbox("Host", host_opts)
    term = st.text_input("Search")
    if status!='All':
        df = df[df['Status']==status]
    if host!='All':
        df = df[df['Host']==host]
    if term:
        mask = df.apply(lambda r: term.lower() in str(r[['Name','Email','Event ID','Description']].values).lower(), axis=1)
        df = df[mask]
    st.subheader(f"Found: {len(df)}")
    for _, r in df.iterrows():
        with st.expander(f"{r['Name']} — {r['Event ID']} ({r['Status']})"):
            cols = st.columns(2)
            for key in ['Name','Email','Guest Email','Status','Event ID','Host']:
                cols[0].write(f"**{key}:** {r.get(key,'')}")
            for key in ['Start Time (12hr)','Start Time (24hr)','Unique Code','Upload_Timestamp']:
                cols[1].write(f"**{key}:** {r.get(key,'')}")
            if r.get('Meet Link'):
                cols[1].write(f"**Meet Link:** [link]({r.get('Meet Link')})")
            if r.get('Description'):
                st.write(f"**Description:** {r.get('Description')}")

def show_contacts():
    st.header("👥 Contacts")
    df = st.session_state.events_data
    rows = []
    for _, r in df.iterrows():
        rows.append({'Name':r['Name'],'Email':r['Email'],'Type':'Primary'})
        if r.get('Guest Email'):
            rows.append({'Name':'Guest','Email':r['Guest Email'],'Type':'Guest'})
    cdf = pd.DataFrame(rows).groupby(['Name','Email','Type']).size().reset_index(name='Events')
    st.dataframe(cdf)
    st.subheader("All Entries")
    for _, r in df.iterrows():
        with st.expander(f"{r['Name']} ({r['Email']})"):
            cols = st.columns(2)
            cols[0].write(f"**Guest Email:** {r.get('Guest Email','')}")
            cols[1].write(f"**Status:** {r.get('Status','')}\n**Event ID:** {r.get('Event ID','')}")

def show_analytics():
    st.header("📈 Analytics")
    df = st.session_state.events_data
    if df.empty:
        st.info("No data")
        return
    c1,c2 = st.columns(2)
    if 'Status' in df:
        fig1 = px.pie(df, names='Status', title="Status Distribution")
        c1.plotly_chart(fig1, use_container_width=True)
    if 'Host' in df:
        fig2 = px.bar(df['Host'].value_counts().reset_index(), x='index', y='Host', orientation='h', title="Top Hosts")
        c2.plotly_chart(fig2, use_container_width=True)
    if 'Upload_Timestamp' in df:
        df['Upload_Date']=pd.to_datetime(df['Upload_Timestamp'], errors='coerce').dt.date
        timeline = df['Upload_Date'].value_counts().sort_index()
        if not timeline.empty:
            fig3 = px.line(x=timeline.index, y=timeline.values, title="Uploads Over Time")
            st.plotly_chart(fig3, use_container_width=True)
    c3,c4,c5 = st.columns(3)
    c3.metric("Total Events", len(df))
    c4.metric("Unique Hosts", df['Host'].nunique() if 'Host' in df else 0)
    c5.metric("Unique Emails", df['Email'].nunique() if 'Email' in df else 0)

def show_add_event():
    st.header("➕ Add Event")
    with st.form("form"):
        c1,c2 = st.columns(2)
        name = c1.text_input("Name*"); email = c1.text_input("Email*"); guest = c1.text_input("Guest Email")
        status = c1.selectbox("Status", ["Confirmed","Pending","Cancelled","Completed"])
        event_id = c1.text_input("Event ID*"); code = c1.text_input("Unique Code*")
        time12 = c2.text_input("Start Time (12hr)*"); time24 = c2.text_input("Start Time (24hr)*")
        meet = c2.text_input("Meet Link"); host = c2.text_input("Host*"); desc = c2.text_area("Description")
        ok = st.form_submit_button("Add")
        if ok:
            if all([name,email,event_id,time12,time24,host,code]):
                new = {'Name':name,'Email':email,'Guest Email':guest,'Status':status,
                       'Event ID':event_id,'Start Time (12hr)':time12,'Start Time (24hr)':time24,
                       'Meet Link':meet,'Description':desc,'Host':host,'Unique Code':code,
                       'Upload_Timestamp':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                if st.session_state.connection_status=="connected":
                    ok2,msg = append_to_sheet(new)
                    st.success(msg) if ok2 else st.error(msg)
                else:
                    st.warning("Sample only, appended locally")
                    st.session_state.events_data = pd.concat([st.session_state.events_data, pd.DataFrame([new])], ignore_index=True)
                    st.success("Added locally")
                st.experimental_rerun()
            else:
                st.error("Fill all * required")

def show_settings():
    st.header("⚙️ Settings")
    st.subheader("Expected Columns")
    for i,c in enumerate(SHEET_COLUMNS,1): st.write(f"{i}. {c}")
    st.subheader("Sheet URL")
    st.code(STATIC_SHEET_URL)
    st.subheader("Data Info")
    st.info(f"Source: {st.session_state.connection_status}")
    st.write(f"Records: {len(st.session_state.events_data)}")
    st.subheader("Columns Present")
    st.write(list(st.session_state.events_data.columns))
    st.subheader("Data Preview")
    st.dataframe(st.session_state.events_data.head(), use_container_width=True)

# ---------- Main Application ----------
def main():
    page = sidebar_navigation()
    if st.session_state.connection_status!="connected":
        refresh_data()
    if st.session_state.error_message and st.session_state.connection_status=="error":
        st.error("Google Sheets Connection Failed")
        st.expander("Error Details", expanded=True).write(st.session_state.error_message)
        st.stop()
    if page=="📋 Dashboard": show_dashboard()
    elif page=="📅 Events": show_events()
    elif page=="👥 Contacts": show_contacts()
    elif page=="📈 Analytics": show_analytics()
    elif page=="➕ Add Event": show_add_event()
    elif page=="⚙️ Settings": show_settings()

if __name__ == "__main__":
    main()
