import streamlit as st
import time
import json
from utils.gsheet import test_gsheet_connection

def show_login():
    # Centered layout
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div class="login-container">
            <h1 style="text-align: center; color: #1f77b4; margin-bottom: 2rem;">
                🏢 Business Management Suite
            </h1>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📊 Google Sheets Configuration")
        st.info("Upload your Google Sheets service account JSON file to enable data synchronization across all pages.")

        # Check if already authenticated
        creds = st.session_state.get("global_gsheets_creds")

        if creds:
            st.success("✅ Google Sheets service account already configured!")
            client_email = creds.get('client_email', 'Unknown')
            st.info(f"📧 Service Account: `{client_email}`")

            col_test, col_remove = st.columns(2)

            with col_test:
                if st.button("🧪 Test Connection", use_container_width=True):
                    with st.spinner("Testing connection..."):
                        result = test_gsheet_connection(creds)
                        if result:
                            st.success("✅ Connection successful!")
                        else:
                            st.error("❌ Connection failed. Check API access and sharing.")

            with col_remove:
                if st.button("🗑️ Remove", use_container_width=True):
                    for key in [
                        'global_gsheets_creds', 'gsheets_creds', 'sheets_cache',
                        'sheets_client', 'data_cache', 'sync_status', 'logged_in'
                    ]:
                        st.session_state.pop(key, None)
                    st.success("🗑️ Configuration removed.")
                    st.rerun()

        else:
            # Upload Google Service JSON
            json_file = st.file_uploader(
                "Upload Service Account JSON",
                type="json",
                help="Used for Google Sheets access across all pages",
                key="login_gsheets_uploader"
            )

            if json_file:
                try:
                    creds_data = json.load(json_file)

                    # Validate required fields
                    required = ["type", "project_id", "private_key", "client_email", "private_key_id"]
                    missing = [f for f in required if f not in creds_data]

                    if missing:
                        st.error(f"❌ Missing required fields: {', '.join(missing)}")
                    else:
                        with st.spinner("Validating and testing connection..."):
                            if test_gsheet_connection(creds_data):
                                st.session_state.global_gsheets_creds = creds_data
                                st.session_state.gsheets_creds = creds_data  # Optional alias
                                st.session_state.logged_in = True
                                st.session_state.sheets_cache = {}
                                st.session_state.data_cache = {}
                                st.session_state.sync_status = {}
                                st.success("✅ Google Sheets connected successfully!")
                                st.info(f"📧 Service Account: `{creds_data.get('client_email')}`")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Connection failed. Check permissions and sheet access.")
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON file.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        st.divider()

        # Setup instructions
        with st.expander("📋 Google Sheets Setup Instructions"):
            st.markdown("""
            **Steps to connect Google Sheets:**

            1. Go to [Google Cloud Console](https://console.cloud.google.com/)
            2. Enable APIs:
               - Google Sheets API
               - Google Drive API
            3. Create a **Service Account** under Credentials
            4. Generate a JSON Key and download it
            5. Share the required Google Sheets with the **service account email**
            6. Upload the JSON above to log in
            """)

        # Footer
        st.markdown("""
        <div style="text-align: center; margin-top: 3rem; color: #888;">
            <small>© 2024 Business Management Suite. All rights reserved.</small>
        </div>
        """, unsafe_allow_html=True)
