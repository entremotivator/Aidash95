import re
import streamlit as st
from datetime import datetime
import pandas as pd

def validate_email(email):
    """Validate email address format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return False
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (10-15 digits)
    return 10 <= len(digits_only) <= 15

def validate_url(url):
    """Validate URL format"""
    if not url:
        return False
    
    pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    return re.match(pattern, url) is not None

def validate_sheet_id(sheet_id):
    """Validate Google Sheets ID format"""
    if not sheet_id:
        return False
    
    # Google Sheets ID is typically 44 characters long
    # and contains letters, numbers, hyphens, and underscores
    if len(sheet_id) < 40:
        return False
    
    pattern = r'^[a-zA-Z0-9_-]+$'
    return re.match(pattern, sheet_id) is not None

def validate_sheet_url(url):
    """Validate Google Sheets URL and extract ID"""
    if not url:
        return False, None
    
    # Check if it's a Google Sheets URL
    if 'docs.google.com/spreadsheets' not in url:
        return False, None
    
    # Extract sheet ID
    if '/d/' in url:
        sheet_id = url.split('/d/')[1].split('/')[0]
        if validate_sheet_id(sheet_id):
            return True, sheet_id
    
    return False, None

def validate_json_structure(json_data, required_fields):
    """Validate JSON structure has required fields"""
    if not isinstance(json_data, dict):
        return False, "Invalid JSON format"
    
    missing_fields = [field for field in required_fields if field not in json_data]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, "Valid JSON structure"

def validate_service_account_json(json_data):
    """Validate Google Service Account JSON"""
    required_fields = [
        'type',
        'project_id', 
        'private_key_id',
        'private_key',
        'client_email',
        'client_id',
        'auth_uri',
        'token_uri'
    ]
    
    is_valid, message = validate_json_structure(json_data, required_fields)
    
    if not is_valid:
        return False, message
    
    # Additional validation
    if json_data.get('type') != 'service_account':
        return False, "JSON must be a service account type"
    
    if not validate_email(json_data.get('client_email', '')):
        return False, "Invalid client email format"
    
    return True, "Valid service account JSON"

def validate_dataframe(df):
    """Validate DataFrame structure"""
    if df is None:
        return False, "DataFrame is None"
    
    if not isinstance(df, pd.DataFrame):
        return False, "Not a valid DataFrame"
    
    if df.empty:
        return False, "DataFrame is empty"
    
    return True, "Valid DataFrame"

def validate_date_string(date_string, format='%Y-%m-%d'):
    """Validate date string format"""
    if not date_string:
        return False, "Date string is empty"
    
    try:
        datetime.strptime(date_string, format)
        return True, "Valid date format"
    except ValueError:
        return False, f"Invalid date format. Expected: {format}"

def validate_numeric_string(value):
    """Validate if string can be converted to number"""
    if not value:
        return False, "Value is empty"
    
    try:
        float(value)
        return True, "Valid numeric value"
    except ValueError:
        return False, "Not a valid numeric value"

def validate_required_fields(data, required_fields):
    """Validate that all required fields are present and not empty"""
    if not isinstance(data, dict):
        return False, "Data must be a dictionary"
    
    missing_fields = []
    empty_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
        elif not data[field] or str(data[field]).strip() == '':
            empty_fields.append(field)
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    if empty_fields:
        return False, f"Empty required fields: {', '.join(empty_fields)}"
    
    return True, "All required fields are valid"

def validate_file_upload(uploaded_file, allowed_types=None, max_size_mb=10):
    """Validate uploaded file"""
    if not uploaded_file:
        return False, "No file uploaded"
    
    # Check file size
    if uploaded_file.size > max_size_mb * 1024 * 1024:
        return False, f"File size exceeds {max_size_mb}MB limit"
    
    # Check file type
    if allowed_types:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension not in allowed_types:
            return False, f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
    
    return True, "Valid file upload"

def sanitize_input(input_string):
    """Sanitize user input to prevent injection attacks"""
    if not input_string:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\';]', '', str(input_string))
    
    # Limit length
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized.strip()

def validate_password_strength(password):
    """Validate password strength"""
    if not password:
        return False, "Password is required"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    # Check for at least one letter and one number
    has_letter = re.search(r'[a-zA-Z]', password)
    has_number = re.search(r'\d', password)
    
    if not has_letter:
        return False, "Password must contain at least one letter"
    
    if not has_number:
        return False, "Password must contain at least one number"
    
    return True, "Password meets strength requirements"

def validate_user_role(role):
    """Validate user role"""
    valid_roles = ['admin', 'user', 'guest', 'viewer']
    
    if not role:
        return False, "Role is required"
    
    if role.lower() not in valid_roles:
        return False, f"Invalid role. Valid roles: {', '.join(valid_roles)}"
    
    return True, "Valid user role"

def validate_api_key(api_key, min_length=20):
    """Validate API key format"""
    if not api_key:
        return False, "API key is required"
    
    if len(api_key) < min_length:
        return False, f"API key must be at least {min_length} characters long"
    
    # Check for valid characters (letters, numbers, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
        return False, "API key contains invalid characters"
    
    return True, "Valid API key format"

def validate_phone_number_format(phone):
    """Validate phone number for calling systems"""
    if not phone:
        return False, "Phone number is required"
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check length (US format: 10 digits, International: 10-15 digits)
    if len(digits_only) < 10 or len(digits_only) > 15:
        return False, "Phone number must be 10-15 digits long"
    
    # US format validation (optional)
    if len(digits_only) == 10:
        # US phone number format
        if digits_only[0] in ['0', '1']:
            return False, "US phone numbers cannot start with 0 or 1"
    
    return True, "Valid phone number format"

def validate_csv_structure(df, required_columns=None):
    """Validate CSV/DataFrame structure"""
    is_valid, message = validate_dataframe(df)
    if not is_valid:
        return False, message
    
    if required_columns:
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
    
    return True, "Valid CSV structure"

def format_validation_error(field_name, error_message):
    """Format validation error message for display"""
    return f"❌ {field_name}: {error_message}"

def format_validation_success(field_name, success_message="Valid"):
    """Format validation success message for display"""
    return f"✅ {field_name}: {success_message}"
