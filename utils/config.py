import streamlit as st
import os
from datetime import datetime, timedelta

def load_config():
    """Load application configuration"""
    config = {
        'app_name': 'Business Management Suite',
        'version': '2.1.0',
        'debug': os.getenv('DEBUG', 'False').lower() == 'true',
        'session_timeout': 3600,  # 1 hour in seconds
        'max_file_size': 10 * 1024 * 1024,  # 10MB
        'allowed_file_types': ['json', 'csv', 'xlsx'],
        'theme': 'light'
    }
    
    # Store in session state
    if 'app_config' not in st.session_state:
        st.session_state.app_config = config
    
    return config

def get_config(key, default=None):
    """Get configuration value"""
    config = st.session_state.get('app_config', {})
    return config.get(key, default)

def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'logged_in': False,
        'user_name': '',
        'user_email': '',
        'user_role': 'guest',
        'login_time': None,
        'last_activity': datetime.now(),
        'session_expiry': None,
        'current_page': 'Dashboard',
        'theme': 'light',
        'data_cache': {},
        'sync_status': {},
        'sheets_cache': {},
        'sheets_client': None,
        'global_gsheets_creds': None,
        'gsheets_creds': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def update_last_activity():
    """Update last activity timestamp"""
    st.session_state.last_activity = datetime.now()

def is_session_expired():
    """Check if session has expired"""
    if not st.session_state.get('logged_in', False):
        return True
    
    if not st.session_state.get('session_expiry'):
        return True
    
    return datetime.now() > st.session_state.session_expiry

def extend_session():
    """Extend session expiry"""
    timeout = get_config('session_timeout', 3600)
    st.session_state.session_expiry = datetime.now() + timedelta(seconds=timeout)

def get_vapi_config():
    """Get VAPI configuration from Streamlit secrets or environment variables"""
    config = {}
    
    try:
        # Try to get from Streamlit secrets first
        if hasattr(st, 'secrets') and 'vapi' in st.secrets:
            config = {
                'api_key': st.secrets.vapi.get('api_key', ''),
                'phone_number_id': st.secrets.vapi.get('phone_number_id', ''),
                'base_url': st.secrets.vapi.get('base_url', 'https://api.vapi.ai'),
                'webhook_url': st.secrets.vapi.get('webhook_url', ''),
                'assistant_id': st.secrets.vapi.get('assistant_id', '')
            }
        else:
            # Fallback to environment variables
            config = {
                'api_key': os.getenv('VAPI_API_KEY', ''),
                'phone_number_id': os.getenv('VAPI_PHONE_NUMBER_ID', ''),
                'base_url': os.getenv('VAPI_BASE_URL', 'https://api.vapi.ai'),
                'webhook_url': os.getenv('VAPI_WEBHOOK_URL', ''),
                'assistant_id': os.getenv('VAPI_ASSISTANT_ID', '')
            }
    except Exception as e:
        st.error(f"Error loading VAPI config: {str(e)}")
        config = {
            'api_key': '',
            'phone_number_id': '',
            'base_url': 'https://api.vapi.ai',
            'webhook_url': '',
            'assistant_id': ''
        }
    
    return config

def validate_vapi_config(config):
    """Validate VAPI configuration"""
    required_fields = ['api_key', 'phone_number_id']
    missing_fields = [field for field in required_fields if not config.get(field)]
    
    if missing_fields:
        return False, f"Missing required VAPI configuration: {', '.join(missing_fields)}"
    
    return True, "VAPI configuration is valid"

def get_user_preferences():
    """Get user preferences"""
    return {
        'theme': st.session_state.get('theme', 'light'),
        'notifications': st.session_state.get('notifications', True),
        'auto_save': st.session_state.get('auto_save', True),
        'page_size': st.session_state.get('page_size', 50)
    }

def save_user_preferences(preferences):
    """Save user preferences"""
    for key, value in preferences.items():
        st.session_state[key] = value

def preserve_gsheets_config():
    """Preserve Google Sheets configuration across sessions"""
    if 'global_gsheets_creds' in st.session_state:
        # Ensure backward compatibility
        st.session_state.gsheets_creds = st.session_state.global_gsheets_creds
        
        # Initialize cache structures if they don't exist
        if 'sheets_cache' not in st.session_state:
            st.session_state.sheets_cache = {}
        if 'data_cache' not in st.session_state:
            st.session_state.data_cache = {}
        if 'sync_status' not in st.session_state:
            st.session_state.sync_status = {}

def get_gsheets_status():
    """Get Google Sheets connection status"""
    if 'global_gsheets_creds' not in st.session_state:
        return {
            'connected': False,
            'message': 'Google Sheets not configured',
            'client_email': None,
            'project_id': None
        }
    
    creds = st.session_state.global_gsheets_creds
    return {
        'connected': True,
        'message': 'Google Sheets connected',
        'client_email': creds.get('client_email', 'Unknown'),
        'project_id': creds.get('project_id', 'Unknown')
    }

def clear_all_caches():
    """Clear all application caches"""
    cache_keys = [
        'sheets_cache',
        'data_cache', 
        'sync_status',
        'sheets_client'
    ]
    
    for key in cache_keys:
        if key in st.session_state:
            if isinstance(st.session_state[key], dict):
                st.session_state[key] = {}
            else:
                st.session_state[key] = None

def get_session_info():
    """Get current session information"""
    return {
        'logged_in': st.session_state.get('logged_in', False),
        'user_name': st.session_state.get('user_name', ''),
        'user_email': st.session_state.get('user_email', ''),
        'user_role': st.session_state.get('user_role', 'guest'),
        'login_time': st.session_state.get('login_time', ''),
        'last_activity': st.session_state.get('last_activity', ''),
        'gsheets_connected': 'global_gsheets_creds' in st.session_state,
        'current_page': st.session_state.get('current_page', 'Dashboard')
    }
