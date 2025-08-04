import streamlit as st
from datetime import datetime, timedelta
import hashlib
import json

# Default users database (in production, this would be in a real database)
DEFAULT_USERS = {
    "admin@business.com": {
        "password": "admin123",
        "name": "Administrator",
        "role": "admin",
        "email": "admin@business.com"
    },
    "demo@business.com": {
        "password": "demo123", 
        "name": "Demo User",
        "role": "user",
        "email": "demo@business.com"
    },
    "user@business.com": {
        "password": "user123",
        "name": "Regular User", 
        "role": "user",
        "email": "user@business.com"
    }
}

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """Verify password against hash"""
    return hash_password(password) == hashed_password

def authenticate_user(email, password):
    """Authenticate user with email and password"""
    try:
        # Check against default users
        if email in DEFAULT_USERS:
            user_data = DEFAULT_USERS[email]
            if user_data["password"] == password:  # In production, use hashed passwords
                return {
                    "success": True,
                    "user": {
                        "email": email,
                        "name": user_data["name"],
                        "role": user_data["role"]
                    },
                    "message": "Authentication successful"
                }
        
        return {
            "success": False,
            "user": None,
            "message": "Invalid email or password"
        }
        
    except Exception as e:
        return {
            "success": False,
            "user": None,
            "message": f"Authentication error: {str(e)}"
        }

def create_user_session(user_data, remember_me=False):
    """Create user session in Streamlit session state"""
    try:
        # Set session data
        st.session_state.logged_in = True
        st.session_state.user_name = user_data["name"]
        st.session_state.user_email = user_data["email"]
        st.session_state.user_role = user_data["role"]
        st.session_state.login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.last_login = st.session_state.login_time
        st.session_state.last_activity = datetime.now()
        
        # Set session expiry
        if remember_me:
            expiry_time = datetime.now() + timedelta(days=30)
        else:
            expiry_time = datetime.now() + timedelta(hours=8)
        
        st.session_state.session_expiry = expiry_time
        
        # Preserve Google Sheets configuration if it exists
        from utils.config import preserve_gsheets_config
        preserve_gsheets_config()
        
        return True
        
    except Exception as e:
        st.error(f"Error creating session: {str(e)}")
        return False

def check_session_validity():
    """Check if current session is valid"""
    try:
        if not st.session_state.get("logged_in", False):
            return False
        
        # Check session expiry
        session_expiry = st.session_state.get("session_expiry")
        if session_expiry and datetime.now() > session_expiry:
            logout_user()
            return False
        
        # Update last activity
        st.session_state.last_activity = datetime.now()
        
        return True
        
    except Exception as e:
        st.error(f"Session validation error: {str(e)}")
        return False

def logout_user():
    """Logout user and clear session data"""
    try:
        # Preserve Google Sheets configuration
        gsheets_creds = st.session_state.get('global_gsheets_creds')
        sheets_cache = st.session_state.get('sheets_cache', {})
        data_cache = st.session_state.get('data_cache', {})
        
        # Clear user session data
        user_session_keys = [
            'logged_in', 'user_name', 'user_email', 'user_role',
            'login_time', 'last_login', 'last_activity', 'session_expiry'
        ]
        
        for key in user_session_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        # Reset to default values
        st.session_state.logged_in = False
        st.session_state.current_page = 'Dashboard'
        
        # Restore Google Sheets configuration
        if gsheets_creds:
            st.session_state.global_gsheets_creds = gsheets_creds
            st.session_state.gsheets_creds = gsheets_creds
            st.session_state.sheets_cache = sheets_cache
            st.session_state.data_cache = data_cache
        
        return True
        
    except Exception as e:
        st.error(f"Logout error: {str(e)}")
        return False

def get_user_role():
    """Get current user role"""
    return st.session_state.get('user_role', 'guest')

def is_admin():
    """Check if current user is admin"""
    return get_user_role() == 'admin'

def is_user():
    """Check if current user is regular user or admin"""
    role = get_user_role()
    return role in ['user', 'admin']

def require_auth(func):
    """Decorator to require authentication"""
    def wrapper(*args, **kwargs):
        if not st.session_state.get('logged_in', False):
            st.error("🔒 Please login to access this feature")
            return None
        return func(*args, **kwargs)
    return wrapper

def require_admin(func):
    """Decorator to require admin role"""
    def wrapper(*args, **kwargs):
        if not is_admin():
            st.error("🔒 Admin access required")
            return None
        return func(*args, **kwargs)
    return wrapper

def get_session_info():
    """Get current session information"""
    return {
        'logged_in': st.session_state.get('logged_in', False),
        'user_name': st.session_state.get('user_name', ''),
        'user_email': st.session_state.get('user_email', ''),
        'user_role': st.session_state.get('user_role', 'guest'),
        'login_time': st.session_state.get('login_time', ''),
        'session_expiry': st.session_state.get('session_expiry', ''),
        'last_activity': st.session_state.get('last_activity', '')
    }

def extend_session(hours=8):
    """Extend current session"""
    if st.session_state.get('logged_in', False):
        new_expiry = datetime.now() + timedelta(hours=hours)
        st.session_state.session_expiry = new_expiry
        return True
    return False

def create_user(email, password, name, role='user'):
    """Create new user (admin only)"""
    if not is_admin():
        return {"success": False, "message": "Admin access required"}
    
    try:
        # In production, this would save to database
        DEFAULT_USERS[email] = {
            "password": password,  # In production, hash this
            "name": name,
            "role": role,
            "email": email,
            "created_at": datetime.now().isoformat()
        }
        
        return {"success": True, "message": "User created successfully"}
        
    except Exception as e:
        return {"success": False, "message": f"Error creating user: {str(e)}"}

def get_all_users():
    """Get all users (admin only)"""
    if not is_admin():
        return []
    
    users = []
    for email, data in DEFAULT_USERS.items():
        users.append({
            "email": email,
            "name": data["name"],
            "role": data["role"]
        })
    
    return users

def update_user_profile(name=None, email=None):
    """Update current user profile"""
    try:
        current_email = st.session_state.get('user_email')
        if not current_email or current_email not in DEFAULT_USERS:
            return {"success": False, "message": "User not found"}
        
        if name:
            DEFAULT_USERS[current_email]["name"] = name
            st.session_state.user_name = name
        
        if email and email != current_email:
            # Move user data to new email key
            user_data = DEFAULT_USERS.pop(current_email)
            user_data["email"] = email
            DEFAULT_USERS[email] = user_data
            st.session_state.user_email = email
        
        return {"success": True, "message": "Profile updated successfully"}
        
    except Exception as e:
        return {"success": False, "message": f"Error updating profile: {str(e)}"}
