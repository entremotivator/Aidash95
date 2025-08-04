import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional, Any
import time
import base64
from io import BytesIO
import os
import sqlite3
import uuid
import plotly.express as px
import plotly.graph_objects as go
from utils.config import get_vapi_config

# Configure the page
st.set_page_config(
    page_title="Vapi Outbound Calling Pro Enhanced",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Utility functions for safe data handling
def safe_str(value: Any, default: str = "") -> str:
    """Safely convert any value to string, handling None values."""
    if value is None:
        return default
    try:
        return str(value)
    except:
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert any value to int, handling None values."""
    if value is None:
        return default
    try:
        return int(value)
    except:
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert any value to float, handling None values."""
    if value is None:
        return default
    try:
        return float(value)
    except:
        return default

def safe_format_customer_name(customer: Dict) -> str:
    """Safely format customer name for display."""
    name = safe_str(customer.get('name', 'Unknown'))
    company = safe_str(customer.get('company', 'No Company'))
    status = safe_str(customer.get('status', 'Unknown'))
    return f"👤 {name} - {company} ({status})"

def safe_format_phone(phone: Any) -> str:
    """Safely format phone number."""
    return safe_str(phone, "No Phone")

def safe_format_email(email: Any) -> str:
    """Safely format email address."""
    return safe_str(email, "No Email")

def safe_format_currency(amount: Any) -> str:
    """Safely format currency amount."""
    try:
        value = safe_float(amount, 0.0)
        return f"${value:,.2f}"
    except:
        return "$0.00"

def safe_format_date(date_str: Any) -> str:
    """Safely format date string."""
    date_val = safe_str(date_str, "")
    if not date_val:
        return "No Date"
    try:
        # Try to parse and format the date
        if len(date_val) >= 16:
            return date_val[:16]
        return date_val
    except:
        return "Invalid Date"

# Database setup
def init_database():
    """Initialize SQLite database for storing call data."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    # Create calls table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calls (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            type TEXT,
            assistant_name TEXT,
            assistant_id TEXT,
            customer_phone TEXT,
            customer_name TEXT,
            customer_email TEXT,
            call_id TEXT,
            status TEXT,
            notes TEXT,
            transcript TEXT,
            recording_url TEXT,
            recording_path TEXT,
            duration INTEGER,
            cost REAL,
            created_at TEXT
        )
    ''')
    
    # Create customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            company TEXT,
            position TEXT,
            lead_score INTEGER,
            status TEXT,
            last_contact TEXT,
            notes TEXT,
            total_value REAL,
            tags TEXT,
            created_at TEXT,
            updated_at TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            country TEXT,
            website TEXT,
            industry TEXT,
            company_size TEXT,
            annual_revenue REAL,
            source TEXT,
            assigned_to TEXT
        )
    ''')
    
    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            customer_id TEXT,
            order_date TEXT,
            amount REAL,
            status TEXT,
            product TEXT,
            quantity INTEGER,
            discount REAL,
            tax REAL,
            shipping REAL,
            total REAL,
            notes TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # Create customer interactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_interactions (
            id TEXT PRIMARY KEY,
            customer_id TEXT,
            interaction_type TEXT,
            interaction_date TEXT,
            notes TEXT,
            outcome TEXT,
            next_action TEXT,
            created_by TEXT,
            created_at TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_database()

# Get Vapi configuration
vapi_config = get_vapi_config()
STATIC_PHONE_NUMBER_ID = vapi_config['phone_number_id']

# Predefined assistants
ASSISTANTS = {
    "Agent CEO": "bf161516-6d88-490c-972e-274098a6b51a",
    "Agent Social": "bf161516-6d88-490c-972e-274098a6b51a",
    "Agent Mindset": "4fe7083e-2f28-4502-b6bf-4ae6ea71a8f4",
    "Agent Blogger": "f8ef1ad5-5281-42f1-ae69-f94ff7acb453",
    "Agent Grant": "7673e69d-170b-4319-bdf4-e74e5370e98a",
    "Agent Prayer Ai": "339cdad6-9989-4bb6-98ed-bd15521707d1",
    "Agent Metrics": "4820eab2-adaf-4f17-a8a0-30cab3e3f007",
    "Agent Researcher": "f05c182f-d3d1-4a17-9c79-52442a9171b8",
    "Agent Investor": "1008771d-86ca-472a-a125-7a7e10100297",
    "Agent Newsroom": "76f1d6e5-cab4-45b8-9aeb-d3e6f3c0c019",
    "STREAMLIT agent": "538258da-0dda-473d-8ef8-5427251f3ad5",
    "Html/ Css Agent": "14b94e2f-299b-4e75-a445-a4f5feacc522",
    "Businesses Plan": "87d59105-723b-427e-a18d-da99fbf28608",
    "Ecom Agent": "d56551f8-0447-468a-872b-eaa9f830993d",
    "Agent Health": "7b2b8b86-5caa-4f28-8c6b-e7d3d0404f06",
    "Cinch Closer": "232f3d9c-18b3-4963-bdd9-e7de3be156ae",
    "DISC Agent": "41fe59e1-829f-4936-8ee5-eef2bb1287fe",
    "Biz Plan Agent": "87d59105-723b-427e-a18d-da99fbf28608",
    "Invoice Agent": "88862739-c227-4bfc-b90a-5f450a823e23",
    "Agent Clone": "88862739-c227-4bfc-b90a-5f450a823e23",
    "Agent Doctor": "9d1cccc6-3193-4694-a9f7-853198ee4082",
    "Agent Multi Lig": "8f045bce-08bc-4477-8d3d-05f233a44df3",
    "Agent Real Estate": "d982667e-d931-477c-9708-c183ba0aa964",
    "Businesses Launcher": "dffb2e5c-7d59-462b-a8aa-48746ea70cb1"
}

# Order status options
ORDER_STATUSES = [
    "Pending", "Processing", "Shipped", "Delivered", "Completed", "Cancelled", "Refunded", "On Hold"
]

# Customer status options
CUSTOMER_STATUSES = [
    "Hot Lead", "Warm Lead", "Cold Lead", "Customer", "Inactive", "Churned"
]

# Demo customers data (25 customers)
DEMO_CUSTOMERS = [
    {
        "id": "cust_001", "name": "John Smith", "email": "john.smith@email.com", "phone": "+1234567890",
        "company": "Tech Solutions Inc", "position": "CEO", "lead_score": 85, "status": "Hot Lead",
        "last_contact": "2024-01-15", "notes": "Interested in enterprise solution",
        "orders": [
            {"id": "ORD-001", "date": "2024-01-10", "amount": 5000, "status": "Completed", "product": "Enterprise Package"},
            {"id": "ORD-002", "date": "2024-01-20", "amount": 2500, "status": "Processing", "product": "Add-on Services"}
        ],
        "total_value": 7500, "tags": ["Enterprise", "High Value", "Decision Maker"]
    },
    {
        "id": "cust_002", "name": "Sarah Johnson", "email": "sarah.j@businesscorp.com", "phone": "+1234567891",
        "company": "Business Corp", "position": "Marketing Director", "lead_score": 72, "status": "Warm Lead",
        "last_contact": "2024-01-12", "notes": "Needs marketing automation tools",
        "orders": [
            {"id": "ORD-003", "date": "2024-01-05", "amount": 1200, "status": "Completed", "product": "Marketing Suite"}
        ],
        "total_value": 1200, "tags": ["Marketing", "Mid-Market", "Repeat Customer"]
    },
    {
        "id": "cust_003", "name": "Michael Brown", "email": "m.brown@startup.io", "phone": "+1234567892",
        "company": "Startup Innovations", "position": "Founder", "lead_score": 90, "status": "Hot Lead",
        "last_contact": "2024-01-18", "notes": "Fast-growing startup, budget approved",
        "orders": [], "total_value": 0, "tags": ["Startup", "High Potential", "New Customer"]
    },
    {
        "id": "cust_004", "name": "Emily Davis", "email": "emily.davis@retailplus.com", "phone": "+1234567893",
        "company": "Retail Plus", "position": "Operations Manager", "lead_score": 65, "status": "Cold Lead",
        "last_contact": "2024-01-08", "notes": "Interested but budget constraints",
        "orders": [
            {"id": "ORD-004", "date": "2023-12-15", "amount": 800, "status": "Completed", "product": "Basic Package"}
        ],
        "total_value": 800, "tags": ["Retail", "Budget Conscious", "Small Business"]
    },
    {
        "id": "cust_005", "name": "David Wilson", "email": "d.wilson@manufacturing.com", "phone": "+1234567894",
        "company": "Wilson Manufacturing", "position": "Plant Manager", "lead_score": 78, "status": "Warm Lead",
        "last_contact": "2024-01-14", "notes": "Looking for automation solutions",
        "orders": [
            {"id": "ORD-005", "date": "2024-01-12", "amount": 3500, "status": "Shipped", "product": "Automation Tools"}
        ],
        "total_value": 3500, "tags": ["Manufacturing", "Automation", "Industrial"]
    }
] + [
    {
        "id": f"cust_{str(i).zfill(3)}", 
        "name": f"Customer {i}", 
        "email": f"customer{i}@example.com", 
        "phone": f"+123456{str(i).zfill(4)}",
        "company": f"Company {i}", 
        "position": "Manager", 
        "lead_score": 50 + (i % 50), 
        "status": CUSTOMER_STATUSES[i % len(CUSTOMER_STATUSES)],
        "last_contact": f"2024-01-{str((i % 28) + 1).zfill(2)}", 
        "notes": f"Demo customer {i}",
        "orders": [
            {"id": f"ORD-{str(i).zfill(3)}", "date": f"2024-01-{str((i % 28) + 1).zfill(2)}", 
             "amount": 1000 + (i * 100), "status": ORDER_STATUSES[i % len(ORDER_STATUSES)], 
             "product": f"Product {i}"}
        ],
        "total_value": 1000 + (i * 100), 
        "tags": [f"Tag{i}", "Demo"]
    } for i in range(6, 26)
]

# Initialize session state
def init_session_state():
    """Initialize all session state variables with unique identifiers."""
    session_vars = {
        'current_page': "📊 Dashboard",
        'api_key': vapi_config.get('api_key', ''),
        'selected_customer_for_call': None,
        'show_add_customer': False,
        'editing_customer': None,
        'viewing_customer_orders': None,
        'viewing_customer_interactions': None,
        'viewing_transcript': None,
        'viewing_recording': None,
        'call_monitoring': {},
        'call_results': []
    }
    
    for var, default_value in session_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default_value

# Utility functions
def save_call_to_db(call_data):
    """Save call data to database."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO calls 
        (id, timestamp, type, assistant_name, assistant_id, customer_phone, 
         customer_name, customer_email, call_id, status, notes, transcript, 
         recording_url, recording_path, duration, cost, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        safe_str(call_data.get('id', str(uuid.uuid4()))),
        safe_str(call_data.get('timestamp')),
        safe_str(call_data.get('type')),
        safe_str(call_data.get('assistant_name')),
        safe_str(call_data.get('assistant_id')),
        safe_str(call_data.get('customer_phone')),
        safe_str(call_data.get('customer_name')),
        safe_str(call_data.get('customer_email')),
        safe_str(call_data.get('call_id')),
        safe_str(call_data.get('status')),
        safe_str(call_data.get('notes')),
        safe_str(call_data.get('transcript')),
        safe_str(call_data.get('recording_url')),
        safe_str(call_data.get('recording_path')),
        safe_int(call_data.get('duration')),
        safe_float(call_data.get('cost')),
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()

def get_calls_from_db(limit=None):
    """Retrieve calls from database."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    query = 'SELECT * FROM calls ORDER BY created_at DESC'
    if limit:
        query += f' LIMIT {safe_int(limit)}'
    
    cursor.execute(query)
    calls = cursor.fetchall()
    conn.close()
    
    columns = ['id', 'timestamp', 'type', 'assistant_name', 'assistant_id', 
               'customer_phone', 'customer_name', 'customer_email', 'call_id', 
               'status', 'notes', 'transcript', 'recording_url', 'recording_path', 
               'duration', 'cost', 'created_at']
    
    return [dict(zip(columns, call)) for call in calls]

def get_customers_from_db(search_term=None, status_filter=None, limit=None):
    """Retrieve customers from database with optional filtering."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    query = 'SELECT * FROM customers'
    params = []
    conditions = []
    
    if search_term:
        search_term = safe_str(search_term)
        conditions.append('(name LIKE ? OR email LIKE ? OR company LIKE ? OR phone LIKE ?)')
        search_pattern = f'%{search_term}%'
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
    
    if status_filter and status_filter != "All":
        conditions.append('status = ?')
        params.append(safe_str(status_filter))
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' ORDER BY updated_at DESC'
    
    if limit:
        query += f' LIMIT {safe_int(limit)}'
    
    cursor.execute(query, params)
    customers = cursor.fetchall()
    conn.close()
    
    columns = ['id', 'name', 'email', 'phone', 'company', 'position', 'lead_score', 
               'status', 'last_contact', 'notes', 'total_value', 'tags', 'created_at', 
               'updated_at', 'address', 'city', 'state', 'zip_code', 'country', 
               'website', 'industry', 'company_size', 'annual_revenue', 'source', 'assigned_to']
    
    return [dict(zip(columns, customer)) for customer in customers]

def get_customer_orders(customer_id):
    """Get orders for a specific customer."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM orders WHERE customer_id = ? ORDER BY order_date DESC', (safe_str(customer_id),))
    orders = cursor.fetchall()
    conn.close()
    
    columns = ['id', 'customer_id', 'order_date', 'amount', 'status', 'product', 
               'quantity', 'discount', 'tax', 'shipping', 'total', 'notes', 
               'created_at', 'updated_at']
    
    return [dict(zip(columns, order)) for order in orders]

def load_demo_customers():
    """Load demo customers into the database."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    for customer in DEMO_CUSTOMERS:
        # Insert customer
        cursor.execute('''
            INSERT OR REPLACE INTO customers 
            (id, name, email, phone, company, position, lead_score, status, 
             last_contact, notes, total_value, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            safe_str(customer['id']),
            safe_str(customer['name']),
            safe_str(customer['email']),
            safe_str(customer['phone']),
            safe_str(customer['company']),
            safe_str(customer['position']),
            safe_int(customer['lead_score']),
            safe_str(customer['status']),
            safe_str(customer['last_contact']),
            safe_str(customer['notes']),
            safe_float(customer['total_value']),
            ','.join([safe_str(tag) for tag in customer.get('tags', [])]),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        # Insert orders
        for order in customer.get('orders', []):
            cursor.execute('''
                INSERT OR REPLACE INTO orders 
                (id, customer_id, order_date, amount, status, product, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                safe_str(order['id']),
                safe_str(customer['id']),
                safe_str(order['date']),
                safe_float(order['amount']),
                safe_str(order['status']),
                safe_str(order['product']),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
    
    conn.commit()
    conn.close()

def validate_phone_number(phone: str) -> bool:
    """Basic phone number validation."""
    try:
        phone_str = safe_str(phone).strip()
        phone_str = ''.join(char for char in phone_str if char.isprintable())
        
        clean_phone = phone_str.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace(".", "")
        
        if clean_phone.startswith("+") and len(clean_phone) >= 10 and len(clean_phone) <= 18:
            if clean_phone[1:].isdigit():
                return True
        return False
    except Exception:
        return False

def make_vapi_call(
    api_key: str,
    assistant_id: str,
    customers: List[Dict],
    schedule_plan: Optional[Dict] = None,
    base_url: str = None
) -> Dict:
    """Make a call to the Vapi API for outbound calling."""
    
    if base_url is None:
        base_url = vapi_config['base_url']
    
    url = f"{base_url}/call"
    
    try:
        api_key = safe_str(api_key).strip()
        assistant_id = safe_str(assistant_id).strip()
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        payload = {
            "assistantId": assistant_id,
            "phoneNumberId": STATIC_PHONE_NUMBER_ID,
        }
        
        # Clean customer phone numbers
        clean_customers = []
        for customer in customers:
            clean_customer = {}
            for key, value in customer.items():
                if isinstance(value, str):
                    clean_value = ''.join(char for char in value if char.isprintable()).strip()
                    clean_customer[key] = clean_value
                else:
                    clean_customer[key] = safe_str(value)
            clean_customers.append(clean_customer)
        
        # Add customers (single or multiple)
        if len(clean_customers) == 1:
            payload["customer"] = clean_customers[0]
        else:
            payload["customers"] = clean_customers
        
        # Add schedule plan if provided
        if schedule_plan:
            payload["schedulePlan"] = schedule_plan
        
        json_payload = json.dumps(payload, ensure_ascii=False)
        
        response = requests.post(
            url, 
            headers=headers, 
            data=json_payload.encode('utf-8'),
            timeout=30
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
        
    except Exception as e:
        return {"success": False, "error": safe_str(e)}

def test_api_connection(api_key: str) -> Dict:
    """Test the API connection by making a simple request."""
    try:
        url = f"{vapi_config['base_url']}/assistant"
        headers = {
            "Authorization": f"Bearer {safe_str(api_key).strip()}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_details = response.json()
                error_msg += f" - {safe_str(error_details.get('message', 'Unknown error'))}"
            except:
                error_msg += f" - {safe_str(response.text[:200])}"
            return {"success": False, "error": error_msg, "status_code": response.status_code}
        
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout", "status_code": None}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error", "status_code": None}
    except Exception as e:
        return {"success": False, "error": safe_str(e), "status_code": None}

# Navigation
def render_navigation():
    """Render the navigation sidebar with unique keys."""
    with st.sidebar:
        st.title("📞 Vapi Pro Enhanced")
        
        # API Key input with unique key
        api_key = st.text_input(
            "🔑 Vapi API Key", 
            type="password",
            value=safe_str(st.session_state.api_key),
            help="Your Vapi API key (from secrets or manual input)",
            key="nav_sidebar_api_key_input_robust_001"
        )
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
        
        # Show if using secrets
        if vapi_config.get('api_key'):
            st.success("✅ Using API key from secrets")
        
        # API Connection Status
        if api_key:
            if st.button("🔍 Test Connection", key="nav_sidebar_test_connection_btn_robust_002"):
                with st.spinner("Testing..."):
                    result = test_api_connection(api_key)
                    if result["success"]:
                        st.success("✅ Connected!")
                    else:
                        st.error(f"❌ {safe_str(result['error'])}")
        
        st.divider()
        
        # Navigation menu with unique key
        pages = [
            "📊 Dashboard",
            "📞 Make Calls", 
            "👥 CRM Dashboard",
            "👥 CRM Manager",
            "📋 Call History",
            "📝 Transcripts",
            "🎵 Recordings",
            "🤖 Assistant Manager",
            "📈 Analytics",
            "⚙️ Settings"
        ]
        
        selected_page = st.radio("Navigation", pages, key="nav_sidebar_page_radio_robust_003")
        
        # Update current page
        if selected_page != st.session_state.current_page:
            st.session_state.current_page = selected_page
        
        st.divider()
        
        # Quick stats
        if api_key:
            try:
                calls = get_calls_from_db(limit=10)
                customers = get_customers_from_db(limit=10)
                
                st.metric("Recent Calls", len(calls))
                st.metric("Total Customers", len(customers))
                
                if calls:
                    completed_calls = len([c for c in calls if safe_str(c.get('status')) == 'completed'])
                    if len(calls) > 0:
                        success_rate = (completed_calls/len(calls)*100)
                        st.metric("Success Rate", f"{success_rate:.1f}%")
            except Exception as e:
                st.error(f"Error loading stats: {safe_str(e)}")

def render_dashboard():
    """Render the dashboard page with unique keys."""
    st.title("📊 Dashboard")
    st.markdown("Welcome to your Vapi Outbound Calling dashboard")
    
    try:
        # Get analytics data
        calls = get_calls_from_db()
        customers = get_customers_from_db()
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Calls", len(calls))
        
        with col2:
            completed_calls = len([c for c in calls if safe_str(c.get('status')) == 'completed'])
            st.metric("Successful Calls", completed_calls)
        
        with col3:
            success_rate = (completed_calls / len(calls) * 100) if calls else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col4:
            st.metric("Total Customers", len(customers))
        
        # Recent calls
        st.subheader("📞 Recent Calls")
        recent_calls = get_calls_from_db(limit=5)
        
        if recent_calls:
            for i, call in enumerate(recent_calls):
                with st.expander(f"📞 {safe_format_phone(call.get('customer_phone'))} - {safe_str(call.get('status', 'Unknown')).upper()}", 
                               key=f"dashboard_call_expander_robust_{i}_004"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Assistant:** {safe_str(call.get('assistant_name', 'Unknown'))}")
                        st.write(f"**Customer:** {safe_format_phone(call.get('customer_phone'))}")
                        customer_name = safe_str(call.get('customer_name'))
                        if customer_name:
                            st.write(f"**Name:** {customer_name}")
                    with col2:
                        st.write(f"**Status:** {safe_str(call.get('status', 'Unknown'))}")
                        st.write(f"**Date:** {safe_format_date(call.get('timestamp'))}")
                        duration = safe_int(call.get('duration'))
                        if duration:
                            st.write(f"**Duration:** {duration}s")
        else:
            st.info("No calls made yet. Start by making your first call!")
        
        # Quick actions
        st.subheader("🚀 Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📞 Make Single Call", type="primary", key="dashboard_make_call_btn_robust_005"):
                st.session_state.current_page = "📞 Make Calls"
                st.rerun()
        
        with col2:
            if st.button("📋 View Call History", key="dashboard_call_history_btn_robust_006"):
                st.session_state.current_page = "📋 Call History"
                st.rerun()
        
        with col3:
            if st.button("👥 Manage CRM", key="dashboard_crm_btn_robust_007"):
                st.session_state.current_page = "👥 CRM Dashboard"
                st.rerun()
                
    except Exception as e:
        st.error(f"Error loading dashboard: {safe_str(e)}")

def render_make_calls():
    """Render the make calls page with unique keys."""
    st.title("📞 Make Calls")
    st.markdown("Enhanced outbound calling with CRM integration")
    
    try:
        # Check if customer was selected from CRM
        selected_customer = st.session_state.get('selected_customer_for_call')
        
        if selected_customer:
            customer_name = safe_str(selected_customer.get('name', 'Unknown'))
            customer_phone = safe_format_phone(selected_customer.get('phone'))
            st.info(f"📋 Selected customer: {customer_name} ({customer_phone})")
            if st.button("❌ Clear Selection", key="make_calls_clear_selection_btn_robust_008"):
                st.session_state.selected_customer_for_call = None
                st.rerun()
        
        # Call type selection
        col1, col2 = st.columns(2)
        
        with col1:
            call_type = st.radio(
                "Select calling mode:",
                ["Single Call", "Bulk Calls"],
                help="Choose your calling approach",
                key="make_calls_type_radio_robust_009"
            )
        
        with col2:
            # Assistant selection
            assistant_name = st.selectbox(
                "Choose Assistant",
                options=list(ASSISTANTS.keys()),
                help="Select from your pre-configured assistants",
                key="make_calls_assistant_select_robust_010"
            )
            assistant_id = ASSISTANTS[assistant_name]
        
        # Single Call
        if call_type == "Single Call":
            st.subheader("📱 Single Call")
            
            # Use selected customer or manual input
            if selected_customer:
                customer_number = safe_str(selected_customer.get('phone', ''))
                customer_name = safe_str(selected_customer.get('name', ''))
                customer_email = safe_str(selected_customer.get('email', ''))
                st.write(f"**Calling:** {customer_name} at {customer_number}")
            else:
                customer_number = st.text_input("Customer Phone Number", placeholder="+1234567890", key="make_calls_phone_input_robust_011")
                customer_name = st.text_input("Customer Name", placeholder="John Doe", key="make_calls_name_input_robust_012")
                customer_email = st.text_input("Customer Email", placeholder="john@example.com", key="make_calls_email_input_robust_013")
            
            customer_notes = st.text_area("Call Notes", placeholder="Purpose of call, talking points...", key="make_calls_notes_textarea_robust_014")
            
            if st.button("📞 Make Call", type="primary", disabled=not all([st.session_state.api_key, customer_number]), key="make_calls_submit_btn_robust_015"):
                if not validate_phone_number(customer_number):
                    st.error("Please enter a valid phone number with country code")
                else:
                    # Prepare customer data
                    customer_data = {"number": safe_str(customer_number)}
                    if customer_name:
                        customer_data["name"] = safe_str(customer_name)
                    if customer_email:
                        customer_data["email"] = safe_str(customer_email)
                    
                    customers = [customer_data]
                    
                    # Make the call
                    with st.spinner("Making call..."):
                        result = make_vapi_call(
                            api_key=st.session_state.api_key,
                            assistant_id=assistant_id,
                            customers=customers
                        )
                    
                    if result["success"]:
                        st.success("Call initiated successfully!")
                        call_data = result["data"]
                        
                        if isinstance(call_data, dict) and "id" in call_data:
                            call_id = safe_str(call_data["id"])
                            st.info(f"**Call ID:** `{call_id}`")
                            
                            # Save to database
                            call_record = {
                                'id': str(uuid.uuid4()),
                                'timestamp': datetime.now().isoformat(),
                                'type': 'Single Call',
                                'assistant_name': assistant_name,
                                'assistant_id': assistant_id,
                                'customer_phone': customer_number,
                                'customer_name': customer_name,
                                'customer_email': customer_email,
                                'call_id': call_id,
                                'status': 'initiated',
                                'notes': customer_notes
                            }
                            
                            save_call_to_db(call_record)
                            st.json(call_data)
                        else:
                            st.json(call_data)
                    else:
                        st.error(f"Call failed: {safe_str(result['error'])}")
        
        # Bulk Calls
        else:
            st.subheader("📞 Bulk Calls")
            
            bulk_input_method = st.radio(
                "Input method:",
                ["Text Input", "Upload CSV", "Select from CRM"],
                horizontal=True,
                key="make_calls_bulk_method_radio_robust_016"
            )
            
            customer_numbers = []
            
            if bulk_input_method == "Text Input":
                bulk_numbers_text = st.text_area(
                    "Phone Numbers (one per line)",
                    placeholder="+1234567890\n+0987654321\n+1122334455",
                    height=150,
                    key="make_calls_bulk_text_area_robust_017"
                )
                
                if bulk_numbers_text:
                    lines = bulk_numbers_text.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and validate_phone_number(line):
                            customer_numbers.append(line)
                    st.info(f"Found {len(customer_numbers)} valid phone numbers")
            
            elif bulk_input_method == "Upload CSV":
                uploaded_file = st.file_uploader("Upload CSV file", type=['csv'], key="make_calls_csv_upload_robust_018")
                
                if uploaded_file:
                    try:
                        df = pd.read_csv(uploaded_file)
                        st.write("Preview:")
                        st.dataframe(df.head())
                        
                        phone_column = None
                        for col in ['phone', 'number', 'phone_number', 'Phone', 'Number']:
                            if col in df.columns:
                                phone_column = col
                                break
                        
                        if phone_column:
                            for phone in df[phone_column].dropna():
                                phone_str = safe_str(phone).strip()
                                if validate_phone_number(phone_str):
                                    customer_numbers.append(phone_str)
                            
                            st.info(f"Found {len(customer_numbers)} valid phone numbers")
                        else:
                            st.error("No phone column found")
                    
                    except Exception as e:
                        st.error(f"Error reading CSV: {safe_str(e)}")
            
            elif bulk_input_method == "Select from CRM":
                customers = get_customers_from_db()
                
                if customers:
                    st.write("Select customers to call:")
                    
                    # Filter options
                    col1, col2 = st.columns(2)
                    with col1:
                        status_filter = st.multiselect("Filter by Status", CUSTOMER_STATUSES, key="make_calls_crm_status_filter_robust_019")
                    with col2:
                        min_score = st.slider("Minimum Lead Score", 0, 100, 0, key="make_calls_crm_score_slider_robust_020")
                    
                    # Filter customers
                    filtered_customers = customers
                    if status_filter:
                        filtered_customers = [c for c in filtered_customers if safe_str(c.get('status')) in status_filter]
                    if min_score > 0:
                        filtered_customers = [c for c in filtered_customers if safe_int(c.get('lead_score', 0)) >= min_score]
                    
                    # Customer selection
                    selected_customers = []
                    for i, customer in enumerate(filtered_customers[:20]):  # Limit to 20 for performance
                        customer_display = f"{safe_str(customer.get('name', 'Unknown'))} - {safe_format_phone(customer.get('phone'))} ({safe_str(customer.get('status', 'Unknown'))})"
                        if st.checkbox(customer_display, key=f"make_calls_crm_customer_checkbox_robust_{i}_021"):
                            selected_customers.append(customer)
                    
                    customer_numbers = [safe_str(c.get('phone', '')) for c in selected_customers if c.get('phone')]
                    st.info(f"Selected {len(customer_numbers)} customers")
                else:
                    st.warning("No customers found in CRM")
            
            # Bulk call execution
            if customer_numbers and st.button("📞 Make Bulk Calls", type="primary", key="make_calls_bulk_submit_btn_robust_022"):
                customers = [{"number": num} for num in customer_numbers]
                
                with st.spinner(f"Making {len(customers)} calls..."):
                    result = make_vapi_call(
                        api_key=st.session_state.api_key,
                        assistant_id=assistant_id,
                        customers=customers
                    )
                
                if result["success"]:
                    st.success(f"Bulk calls initiated for {len(customers)} numbers!")
                    call_data = result["data"]
                    
                    # Save bulk call record
                    call_record = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.now().isoformat(),
                        'type': 'Bulk Calls',
                        'assistant_name': assistant_name,
                        'assistant_id': assistant_id,
                        'customer_phone': f"{len(customers)} numbers",
                        'call_id': safe_str(call_data) if isinstance(call_data, list) else safe_str(call_data.get('id', '')),
                        'status': 'initiated',
                        'notes': f"Bulk call to {len(customers)} customers"
                    }
                    
                    save_call_to_db(call_record)
                    st.json(call_data)
                else:
                    st.error(f"Bulk calls failed: {safe_str(result['error'])}")
                    
    except Exception as e:
        st.error(f"Error in make calls page: {safe_str(e)}")

def render_crm_dashboard():
    """Render the CRM dashboard page with unique keys."""
    st.title("👥 CRM Dashboard")
    st.markdown("Manage your customers, orders, and relationships")
    
    try:
        # Load demo customers if database is empty
        customers = get_customers_from_db(limit=5)
        if not customers:
            if st.button("🎯 Load 25 Demo Customers", key="crm_dashboard_load_demo_btn_robust_023"):
                load_demo_customers()
                st.success("Demo customers loaded successfully!")
                st.rerun()
        
        # CRM Overview metrics
        all_customers = get_customers_from_db()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Customers", len(all_customers))
        
        with col2:
            hot_leads = len([c for c in all_customers if safe_str(c.get('status')) == 'Hot Lead'])
            st.metric("Hot Leads", hot_leads)
        
        with col3:
            total_value = sum([safe_float(c.get('total_value', 0)) for c in all_customers])
            st.metric("Total Customer Value", safe_format_currency(total_value))
        
        with col4:
            if all_customers:
                avg_score = sum([safe_int(c.get('lead_score', 0)) for c in all_customers]) / len(all_customers)
                st.metric("Avg Lead Score", f"{avg_score:.1f}")
            else:
                st.metric("Avg Lead Score", "0.0")
        
        # Customer status distribution
        if all_customers:
            st.subheader("📊 Customer Status Distribution")
            status_counts = {}
            for customer in all_customers:
                status = safe_str(customer.get('status', 'Unknown'))
                status_counts[status] = status_counts.get(status, 0) + 1
            
            try:
                fig = px.pie(
                    values=list(status_counts.values()),
                    names=list(status_counts.keys()),
                    title="Customer Status Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating chart: {safe_str(e)}")
        
        # Recent customers and quick actions
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🆕 Recent Customers")
            recent_customers = get_customers_from_db(limit=5)
            
            for i, customer in enumerate(recent_customers):
                customer_name = safe_str(customer.get('name', 'Unknown'))
                customer_company = safe_str(customer.get('company', 'No Company'))
                with st.expander(f"👤 {customer_name} - {customer_company}", key=f"crm_dashboard_customer_expander_robust_{i}_024"):
                    st.write(f"**Status:** {safe_str(customer.get('status', 'Unknown'))}")
                    st.write(f"**Lead Score:** {safe_int(customer.get('lead_score', 0))}/100")
                    st.write(f"**Phone:** {safe_format_phone(customer.get('phone'))}")
                    st.write(f"**Total Value:** {safe_format_currency(customer.get('total_value'))}")
                    
                    if st.button(f"📞 Call {customer_name}", key=f"crm_dashboard_call_customer_btn_robust_{i}_025"):
                        st.session_state.selected_customer_for_call = customer
                        st.session_state.current_page = "📞 Make Calls"
                        st.rerun()
        
        with col2:
            st.subheader("🚀 Quick Actions")
            
            if st.button("➕ Add New Customer", type="primary", key="crm_dashboard_add_customer_btn_robust_026"):
                st.session_state.show_add_customer = True
            
            if st.button("📋 View All Customers", key="crm_dashboard_view_all_btn_robust_027"):
                st.session_state.current_page = "👥 CRM Manager"
                st.rerun()
            
            if st.button("📊 Customer Analytics", key="crm_dashboard_analytics_btn_robust_028"):
                st.session_state.current_page = "📈 Analytics"
                st.rerun()
            
            if st.button("📤 Export Customers", key="crm_dashboard_export_btn_robust_029"):
                try:
                    customers_df = pd.DataFrame(all_customers)
                    csv_data = customers_df.to_csv(index=False)
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv_data,
                        file_name=f"customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="crm_dashboard_download_btn_robust_030"
                    )
                except Exception as e:
                    st.error(f"Error exporting data: {safe_str(e)}")
        
        # Add customer form
        if st.session_state.get('show_add_customer', False):
            st.subheader("➕ Add New Customer")
            
            with st.form("add_customer_form_robust_031"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("Customer Name*", key="add_customer_name_input_robust_032")
                    email = st.text_input("Email*", key="add_customer_email_input_robust_033")
                    phone = st.text_input("Phone*", key="add_customer_phone_input_robust_034")
                    company = st.text_input("Company", key="add_customer_company_input_robust_035")
                    position = st.text_input("Position", key="add_customer_position_input_robust_036")
                
                with col2:
                    status = st.selectbox("Status", CUSTOMER_STATUSES, key="add_customer_status_select_robust_037")
                    lead_score = st.slider("Lead Score", 0, 100, 50, key="add_customer_score_slider_robust_038")
                    tags = st.text_input("Tags (comma-separated)", key="add_customer_tags_input_robust_039")
                    notes = st.text_area("Notes", key="add_customer_notes_textarea_robust_040")
                
                submitted = st.form_submit_button("Add Customer", key="add_customer_submit_btn_robust_041")
                
                if submitted and name and email and phone:
                    try:
                        customer_data = {
                            'id': str(uuid.uuid4()),
                            'name': safe_str(name),
                            'email': safe_str(email),
                            'phone': safe_str(phone),
                            'company': safe_str(company),
                            'position': safe_str(position),
                            'lead_score': safe_int(lead_score),
                            'status': safe_str(status),
                            'notes': safe_str(notes),
                            'tags': safe_str(tags),
                            'total_value': 0,
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        # Save to database
                        conn = sqlite3.connect('vapi_calls.db')
                        cursor = conn.cursor()
                        
                        cursor.execute('''
                            INSERT INTO customers 
                            (id, name, email, phone, company, position, lead_score, status, 
                             notes, tags, total_value, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            customer_data['id'], customer_data['name'], customer_data['email'],
                            customer_data['phone'], customer_data['company'], customer_data['position'],
                            customer_data['lead_score'], customer_data['status'], customer_data['notes'],
                            customer_data['tags'], customer_data['total_value'], 
                            customer_data['created_at'], customer_data['updated_at']
                        ))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"Customer {name} added successfully!")
                        st.session_state.show_add_customer = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding customer: {safe_str(e)}")
                        
    except Exception as e:
        st.error(f"Error in CRM dashboard: {safe_str(e)}")

# Main function with proper routing
def main():
    """Main application function with complete routing and unique keys."""
    try:
        init_session_state()
        render_navigation()
        
        # Route to appropriate page
        page = safe_str(st.session_state.current_page)
        
        if "Dashboard" in page and "CRM" not in page:
            render_dashboard()
        elif "CRM Dashboard" in page:
            render_crm_dashboard()
        elif "Make Calls" in page:
            render_make_calls()
        else:
            st.error("Page not found!")
            
    except Exception as e:
        st.error(f"Application error: {safe_str(e)}")
        st.info("Please refresh the page or contact support if the error persists.")

if __name__ == "__main__":
    main()
