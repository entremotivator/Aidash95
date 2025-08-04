import streamlit as st
import json
import os
from datetime import datetime
from utils.auth import logout_user
from utils.gsheet import test_gsheet_connection

def show_sidebar():
    """Main sidebar function - this is the function that app.py imports"""
    with st.sidebar:
        # User info header
        st.markdown(f"""
        <div class="user-header">
            <h3>👋 Welcome, {st.session_state.get('user_name', 'User')}!</h3>
            <p><small>Last login: {st.session_state.get('last_login', 'N/A')}</small></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Google Sheets Status Display (Read-only in sidebar)
        st.markdown("### 📊 Google Sheets Status")
        
        if "global_gsheets_creds" in st.session_state:
            st.success("✅ Google Sheets Connected")
            client_email = st.session_state.global_gsheets_creds.get('client_email', 'Unknown')
            st.info(f"📧 {client_email[:35]}...")
            
            # Show project info
            project_id = st.session_state.global_gsheets_creds.get('project_id', 'Unknown')
            st.caption(f"🏗️ Project: {project_id}")
            
            # Quick connection test
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🧪 Test", help="Test connection", key="sidebar_test_connection"):
                    with st.spinner("Testing..."):
                        if test_gsheet_connection(st.session_state.global_gsheets_creds):
                            st.success("✅ OK")
                        else:
                            st.error("❌ Failed")
            
            with col2:
                if st.button("🔄 Refresh", help="Clear cache", key="sidebar_refresh_cache"):
                    # Clear cache
                    cache_keys = ['sheets_cache', 'data_cache', 'sync_status']
                    for key in cache_keys:
                        if key in st.session_state:
                            st.session_state[key] = {}
                    st.success("Cache cleared!")
        else:
            st.warning("⚠️ Google Sheets not configured")
            st.info("💡 Configure Google Sheets on the login page")
        
        st.divider()
        
        # Navigation Menu
        st.markdown("### 🧭 Navigation")
        
        pages = [
            {"name": "Dashboard", "icon": "📊", "desc": "Overview & Analytics"},
            {"name": "Calendar", "icon": "📅", "desc": "Schedule & Events"},
            {"name": "Invoices", "icon": "📄", "desc": "Billing & Payments"},
            {"name": "Customers", "icon": "👥", "desc": "Client Management"},
            {"name": "Appointments", "icon": "🕐", "desc": "Booking System"},
            {"name": "Pricing", "icon": "💰", "desc": "Service Rates"},
            {"name": "AI Chat", "icon": "🤖", "desc": "AI Assistant"},
            {"name": "Voice Calls", "icon": "📞", "desc": "Outbound Calling"},
            {"name": "Call Center", "icon": "🎧", "desc": "Support Center"}
        ]
        
        current_page = st.session_state.get('current_page', 'Dashboard')
        
        for page in pages:
            button_type = "primary" if current_page == page['name'] else "secondary"
            
            if st.button(
                f"{page['icon']} {page['name']}",
                help=page['desc'],
                use_container_width=True,
                type=button_type,
                key=f"nav_{page['name']}"
            ):
                st.session_state.current_page = page['name']
                st.rerun()
        
        st.divider()
        
        # System Status
        st.markdown("### ⚡ System Status")
        
        # Status indicators
        gsheets_status = "🟢" if "global_gsheets_creds" in st.session_state else "🔴"
        auth_status = "🟢" if st.session_state.get("logged_in") else "🔴"
        session_status = "🟢" if st.session_state.get("user_name") else "🔴"
        
        status_items = [
            ("Google Sheets", gsheets_status),
            ("Authentication", auth_status),
            ("Session Active", session_status),
        ]
        
        for item, status in status_items:
            st.markdown(f"{status} {item}")
        
        # Cache information
        if st.session_state.get('sheets_cache'):
            cache_count = len(st.session_state.sheets_cache)
            st.caption(f"📦 Cached sheets: {cache_count}")
        
        # Show connection details if available
        if "global_gsheets_creds" in st.session_state:
            with st.expander("🔍 Connection Details", expanded=False):
                creds = st.session_state.global_gsheets_creds
                st.write(f"**Project ID:** {creds.get('project_id', 'N/A')}")
                st.write(f"**Client Email:** {creds.get('client_email', 'N/A')}")
                st.write(f"**Type:** {creds.get('type', 'N/A')}")
                st.write(f"**Auth URI:** {creds.get('auth_uri', 'N/A')}")
        
        st.divider()
        
        # Quick Actions
        st.markdown("### ⚙️ Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Refresh App", use_container_width=True, help="Refresh the entire application"):
                # Clear non-essential caches but preserve auth and gsheets config
                cache_keys = ['data_cache', 'sync_status', 'sheets_cache']
                for key in cache_keys:
                    if key in st.session_state:
                        st.session_state[key] = {}
                st.success("App refreshed!")
                st.experimental_rerun()
        
        with col2:
            if st.button("🚪 Logout", use_container_width=True, help="Logout and return to login page"):
                # Preserve Google Sheets config across logout
                gsheets_creds = st.session_state.get('global_gsheets_creds')
                logout_user()
                if gsheets_creds:
                    st.session_state.global_gsheets_creds = gsheets_creds
                    st.session_state.gsheets_creds = gsheets_creds
                st.experimental_rerun()
        
        # Settings
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.current_page = "Settings"
            st.experimental_rerun()
        
        st.divider()
        
        # Session Information
        st.markdown("### 📋 Session Info")
        
        # User info
        user_name = st.session_state.get('user_name', 'Unknown')
        user_role = st.session_state.get('user_role', 'guest')
        login_time = st.session_state.get('login_time', 'N/A')
        
        st.caption(f"👤 User: {user_name}")
        st.caption(f"🎭 Role: {user_role.title()}")
        
        # Safe slicing for login_time
        if isinstance(login_time, str) and len(login_time) >= 16:
            st.caption(f"🕐 Login: {login_time[:16]}")
        elif isinstance(login_time, str):
            st.caption(f"🕐 Login: {login_time}")
        else:
            st.caption("🕐 Login: N/A")
        
        # Footer info
        st.markdown(f"""
        <div style="margin-top: 2rem; padding: 1rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 0.5rem; border: 1px solid #dee2e6;">
            <small>
                <strong>🏢 Business Suite</strong><br>
                <strong>Version:</strong> 2.1.0<br>
                <strong>Build:</strong> {datetime.now().strftime("%Y%m%d")}<br>
                <strong>User:</strong> {st.session_state.get('user_role', 'Guest').title()}<br>
                <strong>Support:</strong> help@business.com
            </small>
        </div>
        """, unsafe_allow_html=True)

def render_sidebar():
    """Alternative function name for compatibility"""
    show_sidebar()
