import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from datetime import datetime, timedelta
import json
import re
from typing import Optional, Dict, Any, List

class GoogleSheetsManager:
    """Centralized Google Sheets management with caching and error handling"""
    
    def __init__(self):
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        self.cache_duration = 300  # 5 minutes
        self.max_retries = 3
        
        # Initialize cache in session state
        if 'sheets_cache' not in st.session_state:
            st.session_state.sheets_cache = {}
        if 'sheets_client' not in st.session_state:
            st.session_state.sheets_client = None
    
    def get_client(self):
        """Get authenticated Google Sheets client"""
        try:
            if not st.session_state.get("global_gsheets_creds"):
                raise Exception("No Google Sheets credentials found")
            
            if st.session_state.sheets_client is None:
                creds = ServiceAccountCredentials.from_json_keyfile_dict(
                    st.session_state.global_gsheets_creds, 
                    self.scope
                )
                st.session_state.sheets_client = gspread.authorize(creds)
            
            return st.session_state.sheets_client
            
        except Exception as e:
            st.error(f"Failed to authenticate with Google Sheets: {str(e)}")
            return None
    
    def extract_sheet_id(self, sheet_url_or_id: str) -> str:
        """Extract sheet ID from URL or return ID if already provided"""
        if not sheet_url_or_id:
            return ""
        
        # If it's already a sheet ID (no slashes), return as is
        if '/' not in sheet_url_or_id:
            return sheet_url_or_id
        
        # Extract from URL
        if '/d/' in sheet_url_or_id:
            return sheet_url_or_id.split('/d/')[1].split('/')[0]
        
        return sheet_url_or_id
    
    def get_sheet_data(self, sheet_id: str, worksheet_name: Optional[str] = None, 
                      use_cache: bool = True) -> Optional[pd.DataFrame]:
        """Get data from Google Sheet with caching"""
        try:
            sheet_id = self.extract_sheet_id(sheet_id)
            cache_key = f"{sheet_id}_{worksheet_name or 'default'}"
            
            # Check cache first
            if use_cache and cache_key in st.session_state.sheets_cache:
                cache_entry = st.session_state.sheets_cache[cache_key]
                if time.time() - cache_entry['timestamp'] < self.cache_duration:
                    return cache_entry['data']
            
            # Get fresh data
            client = self.get_client()
            if not client:
                return None
            
            spreadsheet = client.open_by_key(sheet_id)
            
            if worksheet_name:
                worksheet = spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = spreadsheet.get_worksheet(0)
            
            # Get all records
            records = worksheet.get_all_records()
            
            if not records:
                return pd.DataFrame()
            
            df = pd.DataFrame(records)
            
            # Clean the data
            df = df.dropna(how='all')  # Remove completely empty rows
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove unnamed columns
            
            # Cache the result
            st.session_state.sheets_cache[cache_key] = {
                'data': df,
                'timestamp': time.time()
            }
            
            return df
            
        except gspread.SpreadsheetNotFound:
            st.error(f"Spreadsheet not found. Please check the sheet ID and sharing permissions.")
            return None
        except gspread.WorksheetNotFound:
            st.error(f"Worksheet '{worksheet_name}' not found.")
            return None
        except Exception as e:
            st.error(f"Error loading sheet data: {str(e)}")
            return None
    
    def append_row(self, sheet_id: str, row_data: List[Any], 
                   worksheet_name: Optional[str] = None) -> bool:
        """Append a row to Google Sheet"""
        try:
            sheet_id = self.extract_sheet_id(sheet_id)
            client = self.get_client()
            if not client:
                return False
            
            spreadsheet = client.open_by_key(sheet_id)
            
            if worksheet_name:
                worksheet = spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = spreadsheet.get_worksheet(0)
            
            worksheet.append_row(row_data)
            
            # Clear cache for this sheet
            cache_key = f"{sheet_id}_{worksheet_name or 'default'}"
            if cache_key in st.session_state.sheets_cache:
                del st.session_state.sheets_cache[cache_key]
            
            return True
            
        except Exception as e:
            st.error(f"Error appending row: {str(e)}")
            return False
    
    def update_sheet_data(self, sheet_id: str, df: pd.DataFrame, 
                         worksheet_name: Optional[str] = None) -> bool:
        """Update entire sheet with dataframe"""
        try:
            sheet_id = self.extract_sheet_id(sheet_id)
            client = self.get_client()
            if not client:
                return False
            
            spreadsheet = client.open_by_key(sheet_id)
            
            if worksheet_name:
                worksheet = spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = spreadsheet.get_worksheet(0)
            
            # Clear the worksheet
            worksheet.clear()
            
            # Update with new data
            worksheet.update([df.columns.values.tolist()] + df.values.tolist())
            
            # Clear cache for this sheet
            cache_key = f"{sheet_id}_{worksheet_name or 'default'}"
            if cache_key in st.session_state.sheets_cache:
                del st.session_state.sheets_cache[cache_key]
            
            return True
            
        except Exception as e:
            st.error(f"Error updating sheet: {str(e)}")
            return False
    
    def get_multiple_sheets_data(self, sheet_configs: List[Dict[str, str]]) -> Dict[str, pd.DataFrame]:
        """Get data from multiple sheets efficiently"""
        results = {}
        
        for config in sheet_configs:
            sheet_id = config.get('sheet_id', '')
            worksheet_name = config.get('worksheet_name')
            key = config.get('key', sheet_id)
            
            if sheet_id:
                df = self.get_sheet_data(sheet_id, worksheet_name)
                if df is not None:
                    results[key] = df
        
        return results
    
    def clear_cache(self, sheet_id: Optional[str] = None):
        """Clear cache for specific sheet or all sheets"""
        if sheet_id:
            sheet_id = self.extract_sheet_id(sheet_id)
            keys_to_remove = [k for k in st.session_state.sheets_cache.keys() if k.startswith(sheet_id)]
            for key in keys_to_remove:
                del st.session_state.sheets_cache[key]
        else:
            st.session_state.sheets_cache.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about current cache"""
        cache = st.session_state.sheets_cache
        
        if not cache:
            return {
                'cached_sheets': 0,
                'oldest_cache': None,
                'newest_cache': None,
                'total_size': 0
            }
        
        timestamps = [entry['timestamp'] for entry in cache.values()]
        
        return {
            'cached_sheets': len(cache),
            'oldest_cache': min(timestamps) if timestamps else None,
            'newest_cache': max(timestamps) if timestamps else None,
            'total_size': sum(len(entry['data']) for entry in cache.values())
        }
    
    def test_connection(self, sheet_id: str) -> Dict[str, Any]:
        """Test connection to a specific sheet"""
        try:
            sheet_id = self.extract_sheet_id(sheet_id)
            client = self.get_client()
            
            if not client:
                return {'success': False, 'error': 'Failed to get client'}
            
            start_time = time.time()
            spreadsheet = client.open_by_key(sheet_id)
            worksheets = spreadsheet.worksheets()
            end_time = time.time()
            
            return {
                'success': True,
                'response_time': round((end_time - start_time) * 1000, 2),
                'sheet_title': spreadsheet.title,
                'worksheet_count': len(worksheets),
                'worksheets': [ws.title for ws in worksheets]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Global instance
@st.cache_resource
def get_sheets_manager():
    """Get singleton instance of GoogleSheetsManager"""
    return GoogleSheetsManager()
