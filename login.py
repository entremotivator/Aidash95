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

        # Google Sheets Service Account Upload Section
        st.markdown("### 📊 Google Sheets Configuration")
        st.info("Upload your Google Sheets service account JSON file to enable data synchronization across all pages.")

        if "global_gsheets_creds" in st.session_state:
            st.success("✅ Google Sheets service account already configured!")
            client_email = st.session_state.global_gsheets_creds.get('client_email', 'Unknown')
            st.info(f"📧 Service Account: `{client_email}`")

            col_test, col_remove = st.columns(2)
            with col_test:
                if st.button("🧪 Test Connection", use_container_width=True):
                    with st.spinner("Testing connection..."):
                        if test_gsheet_connection(st.session_state.global_gsheets_creds):
                            st.success("✅ Connection successful!")
                        else:
                            st.error("❌ Connection failed!")

            with col_remove:
                if st.button("🗑️ Remove", use_container_width=True):
                    # Clear all related session state
                    keys_to_clear = [
                        'global_gsheets_creds',
                        'gsheets_creds',
                        'sheets_cache',
                        'sheets_client',
                        'data_cache',
                        'sync_status',
                        'logged_in'
                    ]
                    for key in keys_to_clear:
                        st.session_state.pop(key, None)
                    st.success("Google Sheets configuration removed!")
                    st.rerun()
        else:
            # Upload JSON
            json_file = st.file_uploader(
                "Upload Service Account JSON",
                type="json",
                help="Used across all pages for Google Sheets access",
                key="login_gsheets_uploader"
            )

            if json_file:
                try:
                    creds_data = json.load(json_file)

                    # Basic field validation
                    required_fields = ["type", "project_id", "private_key", "client_email", "private_key_id"]
                    missing_fields = [field for field in required_fields if field not in creds_data]

                    if not missing_fields:
                        with st.spinner("Validating and testing connection..."):
                            time.sleep(1)
                            if test_gsheet_connection(creds_data):
                                # Store credentials
                                st.session_state.global_gsheets_creds = creds_data
                                st.session_state.gsheets_creds = creds_data  # optional alias
                                st.session_state.logged_in = True

                                # Setup empty cache structures
                                st.session_state.sheets_cache = {}
                                st.session_state.data_cache = {}
                                st.session_state.sync_status = {}

                                st.success("✅ Google Sheets connected successfully!")
                                st.info(f"📧 Service Account: `{creds_data.get('client_email', 'Unknown')}`")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Failed to connect to Google Sheets. Please check permissions.")
                    else:
                        st.error(f"❌ Invalid JSON. Missing fields: {', '.join(missing_fields)}")

                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON file format.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        st.divider()

        # Setup Instructions
        with st.expander("📋 Google Sheets Setup Instructions"):
            st.markdown("""
            **To set up Google Sheets integration:**

            1. **Create a Google Cloud Project** at [Google Cloud Console](https://console.cloud.google.com/)
            2. **Enable APIs:**
               - Google Sheets API
               - Google Drive API
            3. **Create Service Account** under "APIs & Services" > "Credentials"
            4. **Generate JSON Key** from service account (Choose JSON format)
            5. **Share Sheets** with the service account email as "Editor"
            6. **Upload JSON** above to connect

            > Make sure the service account has access to all necessary Sheets.
            """)

        # Footer
        st.markdown("""
        <div style="text-align: center; margin-top: 3rem; color: #666;">
            <small>© 2024 Business Management Suite. All rights reserved.</small>
        </div>
        """, unsafe_allow_html=True)
