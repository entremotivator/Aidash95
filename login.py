import streamlit as st
import time
import json
from utils.auth import authenticate_user, create_user_session
from utils.validators import validate_email
from utils.gsheet import test_gsheet_connection

def show_login():
    # Create centered login form
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
        
        # Check if already uploaded
        if "global_gsheets_creds" in st.session_state:
            st.success("✅ Google Sheets service account already configured!")
            client_email = st.session_state.global_gsheets_creds.get('client_email', 'Unknown')
            st.info(f"📧 Service Account: {client_email}")
            
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
                    # Clear all Google Sheets related session state
                    keys_to_clear = [
                        'global_gsheets_creds', 
                        'gsheets_creds', 
                        'sheets_cache', 
                        'sheets_client',
                        'data_cache',
                        'sync_status'
                    ]
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.success("Google Sheets configuration removed!")
                    st.rerun()
        else:
            # Upload new service account file
            json_file = st.file_uploader(
                "Upload Service Account JSON",
                type="json",
                help="This file will be used across all pages for Google Sheets access",
                key="login_gsheets_uploader"
            )
            
            if json_file:
                try:
                    creds_data = json.load(json_file)
                    
                    # Validate JSON structure
                    required_fields = ["type", "project_id", "private_key", "client_email", "private_key_id"]
                    missing_fields = [field for field in required_fields if field not in creds_data]
                    
                    if not missing_fields:
                        with st.spinner("Validating and testing connection..."):
                            time.sleep(1)  # Brief delay for UX
                            
                            # Test the connection
                            if test_gsheet_connection(creds_data):
                                # Store in session state for global access
                                st.session_state.global_gsheets_creds = creds_data
                                st.session_state.gsheets_creds = creds_data  # Backward compatibility
                                
                                # Initialize cache structures
                                st.session_state.sheets_cache = {}
                                st.session_state.data_cache = {}
                                st.session_state.sync_status = {}
                                
                                st.success("✅ Google Sheets connected successfully!")
                                st.info(f"📧 Service Account: {creds_data.get('client_email', 'Unknown')}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Failed to connect to Google Sheets. Please check your credentials and permissions.")
                    else:
                        st.error(f"❌ Invalid service account JSON. Missing fields: {', '.join(missing_fields)}")
                        
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON file format")
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
        
        st.divider()
        
        # Login form
        with st.form("login_form", clear_on_submit=False):
            st.markdown("### 🔐 Login to Your Account")
            
            email = st.text_input(
                "Email Address",
                placeholder="Enter your email",
                help="Use your registered email address"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                help="Minimum 6 characters required"
            )
            
            remember_me = st.checkbox("Remember me for 30 days")
            
            col_login, col_register = st.columns(2)
            
            with col_login:
                login_clicked = st.form_submit_button(
                    "🚀 Login",
                    use_container_width=True,
                    type="primary"
                )
            
            with col_register:
                register_clicked = st.form_submit_button(
                    "📝 Register",
                    use_container_width=True
                )
        
        # Handle login
        if login_clicked:
            if not email or not password:
                st.error("⚠️ Please fill in all fields")
            elif not validate_email(email):
                st.error("⚠️ Please enter a valid email address")
            else:
                with st.spinner("Authenticating..."):
                    time.sleep(1)  # Simulate authentication delay
                    
                    auth_result = authenticate_user(email, password)
                    
                    if auth_result["success"]:
                        create_user_session(auth_result["user"], remember_me)
                        
                        # Preserve Google Sheets configuration across login
                        if "global_gsheets_creds" in st.session_state:
                            st.info("✅ Google Sheets configuration preserved!")
                        
                        st.success("✅ Login successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {auth_result['message']}")
        
        # Handle registration
        if register_clicked:
            st.info("🚧 Registration feature coming soon! Contact admin for access.")
        
        # Demo credentials info
        with st.expander("🔍 Demo Credentials"):
            st.info("""
            **Demo Account:**
            - Email: demo@business.com
            - Password: demo123
            
            **Admin Account:**
            - Email: admin@business.com  
            - Password: admin123
            
            **User Account:**
            - Email: user@business.com
            - Password: user123
            """)
        
        # Google Sheets Setup Instructions
        with st.expander("📋 Google Sheets Setup Instructions"):
            st.markdown("""
            **To set up Google Sheets integration:**
            
            1. **Create a Google Cloud Project:**
               - Go to [Google Cloud Console](https://console.cloud.google.com/)
               - Create a new project or select existing one
            
            2. **Enable Google Sheets API:**
               - Navigate to "APIs & Services" > "Library"
               - Search for "Google Sheets API" and enable it
               - Also enable "Google Drive API"
            
            3. **Create Service Account:**
               - Go to "APIs & Services" > "Credentials"
               - Click "Create Credentials" > "Service Account"
               - Fill in the details and create
            
            4. **Generate JSON Key:**
               - Click on the created service account
               - Go to "Keys" tab > "Add Key" > "Create New Key"
               - Choose JSON format and download
            
            5. **Share Your Sheets:**
               - Open your Google Sheets
               - Click "Share" and add the service account email
               - Give "Editor" permissions
            
            6. **Upload JSON File:**
               - Use the file uploader above to upload your JSON key
               - The system will test the connection automatically
            """)
        
        # Footer
        st.markdown("""
        <div style="text-align: center; margin-top: 3rem; color: #666;">
            <small>© 2024 Business Management Suite. All rights reserved.</small>
        </div>
        """, unsafe_allow_html=True)
