import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time
from datetime import datetime
import json

def get_gsheet_client():
    """Get authenticated Google Sheets client using global credentials"""
    try:
        if 'global_gsheets_creds' not in st.session_state:
            return None, "Google Sheets credentials not configured"
        
        # Check if client already exists and is valid
        if 'sheets_client' in st.session_state and st.session_state.sheets_client:
            return st.session_state.sheets_client, "Success"
        
        # Create new client
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.session_state.global_gsheets_creds, 
            scope
        )
        
        client = gspread.authorize(creds)
        st.session_state.sheets_client = client
        
        return client, "Success"
        
    except Exception as e:
        return None, f"Error creating client: {str(e)}"

def test_gsheet_connection(creds_data=None):
    """Test Google Sheets connection without requiring a specific file ID"""
    try:
        if creds_data:
            # Test with provided credentials
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_data, scope)
            client = gspread.authorize(creds)
        else:
            # Use stored client
            client, error = get_gsheet_client()
            if not client:
                return False
        
        # Try to list accessible spreadsheets as connection test
        # This requires Drive API permission
        spreadsheets = client.openall()
        # If no exception, connection is good
        return True
        
    except Exception as e:
        st.error(f"Connection test failed: {str(e)}")
        return False

def extract_sheet_id(url_or_id):
    """Extract sheet ID from URL or return ID if already provided"""
    if not url_or_id:
        return ""
    
    # If it's already a sheet ID (no slashes), return as is
    if '/' not in url_or_id:
        return url_or_id
    
    # Extract from URL
    if '/d/' in url_or_id:
        return url_or_id.split('/d/')[1].split('/')[0]
    
    return url_or_id

def get_sheet_data(sheet_id, worksheet_name=None, use_cache=True):
    """Get data from Google Sheet with caching"""
    try:
        sheet_id = extract_sheet_id(sheet_id)
        cache_key = f"{sheet_id}_{worksheet_name or 'default'}"
        
        # Check cache first
        if use_cache and 'sheets_cache' in st.session_state:
            cache = st.session_state.sheets_cache
            if cache_key in cache:
                cache_entry = cache[cache_key]
                # Check if cache is still valid (5 minutes)
                if time.time() - cache_entry.get('timestamp', 0) < 300:
                    return cache_entry['data'], "Success (cached)"
        
        # Get fresh data
        client, error = get_gsheet_client()
        if not client:
            return None, error
        
        # Open spreadsheet
        spreadsheet = client.open_by_key(sheet_id)
        
        # Get worksheet
        if worksheet_name:
            worksheet = spreadsheet.worksheet(worksheet_name)
        else:
            worksheet = spreadsheet.get_worksheet(0)
        
        # Get all records
        records = worksheet.get_all_records()
        
        if not records:
            return pd.DataFrame(), "Success (empty sheet)"
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Clean the data
        df = df.dropna(how='all')  # Remove completely empty rows
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove unnamed columns
        
        # Cache the result
        if 'sheets_cache' not in st.session_state:
            st.session_state.sheets_cache = {}
        
        st.session_state.sheets_cache[cache_key] = {
            'data': df,
            'timestamp': time.time(),
            'sheet_title': spreadsheet.title,
            'worksheet_title': worksheet.title
        }
        
        return df, "Success"
        
    except gspread.SpreadsheetNotFound:
        return None, "Spreadsheet not found. Check the sheet ID and sharing permissions."
    except gspread.WorksheetNotFound:
        return None, f"Worksheet '{worksheet_name}' not found."
    except Exception as e:
        return None, f"Error loading sheet data: {str(e)}"

def append_row_to_sheet(sheet_id, row_data, worksheet_name=None):
    """Append a row to Google Sheet"""
    try:
        sheet_id = extract_sheet_id(sheet_id)
        client, error = get_gsheet_client()
        if not client:
            return False, error
        
        spreadsheet = client.open_by_key(sheet_id)
        
        if worksheet_name:
            worksheet = spreadsheet.worksheet(worksheet_name)
        else:
            worksheet = spreadsheet.get_worksheet(0)
        
        worksheet.append_row(row_data)
        
        # Clear cache for this sheet
        cache_key = f"{sheet_id}_{worksheet_name or 'default'}"
        if 'sheets_cache' in st.session_state and cache_key in st.session_state.sheets_cache:
            del st.session_state.sheets_cache[cache_key]
        
        return True, "Row appended successfully"
        
    except Exception as e:
        return False, f"Error appending row: {str(e)}"

def update_sheet_data(sheet_id, df, worksheet_name=None):
    """Update entire sheet with DataFrame"""
    try:
        sheet_id = extract_sheet_id(sheet_id)
        client, error = get_gsheet_client()
        if not client:
            return False, error
        
        spreadsheet = client.open_by_key(sheet_id)
        
        if worksheet_name:
            worksheet = spreadsheet.worksheet(worksheet_name)
        else:
            worksheet = spreadsheet.get_worksheet(0)
        
        # Clear the worksheet
        worksheet.clear()
        
        # Update with new data
        data_to_update = [df.columns.values.tolist()] + df.values.tolist()
        worksheet.update(data_to_update)
        
        # Clear cache for this sheet
        cache_key = f"{sheet_id}_{worksheet_name or 'default'}"
        if 'sheets_cache' in st.session_state and cache_key in st.session_state.sheets_cache:
            del st.session_state.sheets_cache[cache_key]
        
        return True, "Sheet updated successfully"
        
    except Exception as e:
        return False, f"Error updating sheet: {str(e)}"

def get_sheet_info(sheet_id):
    """Get information about a Google Sheet"""
    try:
        sheet_id = extract_sheet_id(sheet_id)
        client, error = get_gsheet_client()
        if not client:
            return None, error
        
        spreadsheet = client.open_by_key(sheet_id)
        worksheets = spreadsheet.worksheets()
        
        info = {
            'title': spreadsheet.title,
            'id': spreadsheet.id,
            'url': spreadsheet.url,
            'worksheet_count': len(worksheets),
            'worksheets': [
                {
                    'title': ws.title,
                    'id': ws.id,
                    'row_count': ws.row_count,
                    'col_count': ws.col_count
                }
                for ws in worksheets
            ]
        }
        
        return info, "Success"
        
    except Exception as e:
        return None, f"Error getting sheet info: {str(e)}"

def create_new_worksheet(sheet_id, worksheet_name, rows=1000, cols=26):
    """Create a new worksheet in existing spreadsheet"""
    try:
        sheet_id = extract_sheet_id(sheet_id)
        client, error = get_gsheet_client()
        if not client:
            return False, error
        
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=rows,
            cols=cols
        )
        
        return True, f"Worksheet '{worksheet_name}' created successfully"
        
    except Exception as e:
        return False, f"Error creating worksheet: {str(e)}"

def delete_worksheet(sheet_id, worksheet_name):
    """Delete a worksheet from spreadsheet"""
    try:
        sheet_id = extract_sheet_id(sheet_id)
        client, error = get_gsheet_client()
        if not client:
            return False, error
        
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        spreadsheet.del_worksheet(worksheet)
        
        # Clear cache for this sheet
        cache_key = f"{sheet_id}_{worksheet_name}"
        if 'sheets_cache' in st.session_state and cache_key in st.session_state.sheets_cache:
            del st.session_state.sheets_cache[cache_key]
        
        return True, f"Worksheet '{worksheet_name}' deleted successfully"
        
    except Exception as e:
        return False, f"Error deleting worksheet: {str(e)}"

def get_cache_info():
    """Get information about current cache"""
    if 'sheets_cache' not in st.session_state:
        return {
            'cached_sheets': 0,
            'total_size': 0,
            'oldest_cache': None,
            'newest_cache': None
        }
    
    cache = st.session_state.sheets_cache
    
    if not cache:
        return {
            'cached_sheets': 0,
            'total_size': 0,
            'oldest_cache': None,
            'newest_cache': None
        }
    
    timestamps = [entry.get('timestamp', 0) for entry in cache.values()]
    total_rows = sum(len(entry.get('data', pd.DataFrame())) for entry in cache.values())
    
    return {
        'cached_sheets': len(cache),
        'total_size': total_rows,
        'oldest_cache': datetime.fromtimestamp(min(timestamps)) if timestamps else None,
        'newest_cache': datetime.fromtimestamp(max(timestamps)) if timestamps else None
    }

def clear_cache(sheet_id=None):
    """Clear cache for specific sheet or all sheets"""
    if 'sheets_cache' not in st.session_state:
        return
    
    if sheet_id:
        sheet_id = extract_sheet_id(sheet_id)
        keys_to_remove = [k for k in st.session_state.sheets_cache.keys() if k.startswith(sheet_id)]
        for key in keys_to_remove:
            del st.session_state.sheets_cache[key]
    else:
        st.session_state.sheets_cache = {}

def batch_get_sheets_data(sheet_configs):
    """Get data from multiple sheets efficiently"""
    results = {}
    
    for config in sheet_configs:
        sheet_id = config.get('sheet_id', '')
        worksheet_name = config.get('worksheet_name')
        key = config.get('key', sheet_id)
        
        if sheet_id:
            df, error = get_sheet_data(sheet_id, worksheet_name)
            if df is not None:
                results[key] = df
            else:
                st.warning(f"Failed to load {key}: {error}")
    
    return results

def export_sheet_data(df, format='csv'):
    """Export DataFrame to various formats"""
    try:
        if format.lower() == 'csv':
            return df.to_csv(index=False), 'text/csv'
        elif format.lower() == 'excel':
            return df.to_excel(index=False), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif format.lower() == 'json':
            return df.to_json(orient='records', indent=2), 'application/json'
        else:
            return None, None
    except Exception as e:
        st.error(f"Export error: {str(e)}")
        return None, None
