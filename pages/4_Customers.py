import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.auth import require_auth
from utils.gsheet_manager import get_sheets_manager
from components.data_scanner_ui import DataScannerUI
import plotly.express as px
import plotly.graph_objects as go

@require_auth
def main():
    st.title("👥 Customer Management System")
    st.markdown("Comprehensive customer relationship management with Google Sheets integration")
    
    # Initialize sheets manager
    sheets_manager = get_sheets_manager()
    
    # Check for global credentials
    if not st.session_state.get("global_gsheets_creds"):
        st.error("🔑 Google Sheets credentials not found. Please upload your service account JSON in the sidebar.")
        st.info("💡 Use the sidebar to upload your service account JSON file for full functionality.")
        st.stop()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", "👥 Customer List", "📈 Analytics", "➕ Add Customer", "🔍 Data Scanner"
    ])
    
    with tab1:
        render_overview_tab(sheets_manager)
    
    with tab2:
        render_customer_list_tab(sheets_manager)
    
    with tab3:
        render_analytics_tab(sheets_manager)
    
    with tab4:
        render_add_customer_tab(sheets_manager)
    
    with tab5:
        render_data_scanner_tab()

def render_overview_tab(sheets_manager):
    """Render customer overview dashboard"""
    st.subheader("📊 Customer Overview")
    
    # Configuration section
    with st.expander("⚙️ Configure Customer Data Source", expanded=True):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            sheet_url = st.text_input(
                "Customer Sheet URL/ID",
                placeholder="https://docs.google.com/spreadsheets/d/your-sheet-id/edit",
                help="Enter your customer data Google Sheet URL or ID"
            )
            
            worksheet_name = st.text_input(
                "Worksheet Name (optional)",
                placeholder="Customers",
                help="Leave empty for first worksheet"
            )
        
        with col2:
            if st.button("🔄 Load Data", type="primary", use_container_width=True):
                if sheet_url:
                    load_customer_data(sheets_manager, sheet_url, worksheet_name)
                else:
                    st.error("Please enter a sheet URL or ID")
    
    # Display customer data if loaded
    if 'customer_data' in st.session_state and st.session_state.customer_data is not None:
        df = st.session_state.customer_data
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Total Customers", len(df))
        
        with col2:
            # Try to find revenue/value column
            value_cols = [col for col in df.columns if any(term in col.lower() for term in ['value', 'revenue', 'amount', 'total'])]
            if value_cols:
                total_value = pd.to_numeric(df[value_cols[0]], errors='coerce').sum()
                st.metric("💰 Total Value", f"${total_value:,.2f}")
            else:
                st.metric("💰 Total Value", "N/A")
        
        with col3:
            # Try to find status column
            status_cols = [col for col in df.columns if any(term in col.lower() for term in ['status', 'stage', 'type'])]
            if status_cols:
                active_customers = len(df[df[status_cols[0]].str.contains('active|customer|paid', case=False, na=False)])
                st.metric("✅ Active Customers", active_customers)
            else:
                st.metric("✅ Active Customers", "N/A")
        
        with col4:
            # Try to find date column for recent additions
            date_cols = [col for col in df.columns if any(term in col.lower() for term in ['date', 'created', 'added'])]
            if date_cols:
                try:
                    df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors='coerce')
                    recent = len(df[df[date_cols[0]] > datetime.now() - timedelta(days=30)])
                    st.metric("🆕 New (30 days)", recent)
                except:
                    st.metric("🆕 New (30 days)", "N/A")
            else:
                st.metric("🆕 New (30 days)", "N/A")
        
        # Recent customers preview
        st.subheader("👀 Recent Customers")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Analyze Data", use_container_width=True):
                st.session_state.show_customer_scanner = True
                st.rerun()
        
        with col2:
            if st.button("📤 Export Data", use_container_width=True):
                csv = df.to_csv(index=False)
                st.download_button(
                    "💾 Download CSV",
                    csv,
                    f"customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
        
        with col3:
            if st.button("🔄 Refresh Data", use_container_width=True):
                sheets_manager.clear_cache()
                st.rerun()
    
    else:
        st.info("📋 Configure your customer data source above to get started")

def render_customer_list_tab(sheets_manager):
    """Render detailed customer list with filtering"""
    st.subheader("👥 Customer Database")
    
    if 'customer_data' not in st.session_state or st.session_state.customer_data is None:
        st.warning("⚠️ No customer data loaded. Please configure data source in Overview tab.")
        return
    
    df = st.session_state.customer_data
    
    # Advanced filtering
    with st.expander("🔍 Advanced Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Text search
            search_term = st.text_input("🔍 Search customers", placeholder="Name, email, company...")
        
        with col2:
            # Column-based filters
            filter_column = st.selectbox("Filter by column", ["None"] + df.columns.tolist())
        
        with col3:
            filter_value = ""
            if filter_column != "None":
                unique_values = df[filter_column].dropna().unique()
                if len(unique_values) <= 50:  # Dropdown for small sets
                    filter_value = st.selectbox("Filter value", ["All"] + list(unique_values))
                else:  # Text input for large sets
                    filter_value = st.text_input("Filter value")
    
    # Apply filters
    filtered_df = df.copy()
    
    if search_term:
        # Search across all text columns
        text_cols = df.select_dtypes(include=['object']).columns
        mask = False
        for col in text_cols:
            mask |= df[col].astype(str).str.contains(search_term, case=False, na=False)
        filtered_df = df[mask]
    
    if filter_column != "None" and filter_value and filter_value != "All":
        filtered_df = filtered_df[filtered_df[filter_column].astype(str).str.contains(str(filter_value), case=False, na=False)]
    
    # Display results
    st.write(f"📊 Showing {len(filtered_df)} of {len(df)} customers")
    
    # Pagination
    page_size = st.selectbox("Rows per page", [10, 25, 50, 100], index=1)
    total_pages = (len(filtered_df) - 1) // page_size + 1
    
    if total_pages > 1:
        page = st.selectbox("Page", range(1, total_pages + 1))
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        display_df = filtered_df.iloc[start_idx:end_idx]
    else:
        display_df = filtered_df
    
    # Enhanced data display with editing capabilities
    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        num_rows="dynamic",
        key="customer_editor"
    )
    
    # Save changes button
    if st.button("💾 Save Changes to Sheet"):
        try:
            # Update the original dataframe with changes
            for idx in edited_df.index:
                if idx in df.index:
                    df.loc[idx] = edited_df.loc[idx]
            
            # Save back to Google Sheets
            sheet_url = st.session_state.get('customer_sheet_url', '')
            worksheet_name = st.session_state.get('customer_worksheet_name', '')
            
            if sheets_manager.update_sheet_data(sheet_url, df, worksheet_name):
                st.success("✅ Changes saved to Google Sheets!")
            else:
                st.error("❌ Failed to save changes")
        except Exception as e:
            st.error(f"❌ Error saving changes: {str(e)}")

def render_analytics_tab(sheets_manager):
    """Render customer analytics and insights"""
    st.subheader("📈 Customer Analytics")
    
    if 'customer_data' not in st.session_state or st.session_state.customer_data is None:
        st.warning("⚠️ No customer data loaded. Please configure data source in Overview tab.")
        return
    
    df = st.session_state.customer_data
    
    # Customer distribution charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Try to create status distribution
        status_cols = [col for col in df.columns if any(term in col.lower() for term in ['status', 'stage', 'type'])]
        if status_cols:
            status_counts = df[status_cols[0]].value_counts()
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title=f"Distribution by {status_cols[0]}",
                color_discrete_sequence=['#2E86AB', '#A23B72', '#F18F01', '#28a745', '#ffc107']
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status/type column found for distribution analysis")
    
    with col2:
        # Try to create value distribution
        value_cols = [col for col in df.columns if any(term in col.lower() for term in ['value', 'revenue', 'amount'])]
        if value_cols:
            numeric_values = pd.to_numeric(df[value_cols[0]], errors='coerce').dropna()
            if len(numeric_values) > 0:
                fig = px.histogram(
                    x=numeric_values,
                    nbins=20,
                    title=f"Distribution of {value_cols[0]}",
                    color_discrete_sequence=['#2E86AB']
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No numeric values found for distribution analysis")
        else:
            st.info("No value/revenue column found for analysis")
    
    # Time-based analysis
    date_cols = [col for col in df.columns if any(term in col.lower() for term in ['date', 'created', 'added', 'updated'])]
    if date_cols:
        st.subheader("📅 Time-based Analysis")
        
        selected_date_col = st.selectbox("Select date column", date_cols)
        
        try:
            df[selected_date_col] = pd.to_datetime(df[selected_date_col], errors='coerce')
            date_data = df[selected_date_col].dropna()
            
            if len(date_data) > 0:
                # Monthly trend
                monthly_counts = date_data.dt.to_period('M').value_counts().sort_index()
                
                fig = px.line(
                    x=monthly_counts.index.astype(str),
                    y=monthly_counts.values,
                    title=f"Monthly Trend - {selected_date_col}",
                    color_discrete_sequence=['#2E86AB']
                )
                fig.update_layout(xaxis_title="Month", yaxis_title="Count")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No valid dates found in selected column")
        except Exception as e:
            st.error(f"Error processing date column: {str(e)}")
    
    # Data quality insights
    st.subheader("🎯 Data Quality Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Completeness
        completeness = (1 - df.isnull().sum() / len(df)) * 100
        avg_completeness = completeness.mean()
        st.metric("📊 Avg Completeness", f"{avg_completeness:.1f}%")
    
    with col2:
        # Duplicates
        duplicates = df.duplicated().sum()
        st.metric("🔄 Duplicate Rows", duplicates)
    
    with col3:
        # Unique customers
        # Try to find name/email columns
        name_cols = [col for col in df.columns if any(term in col.lower() for term in ['name', 'customer', 'client'])]
        if name_cols:
            unique_customers = df[name_cols[0]].nunique()
            st.metric("👤 Unique Names", unique_customers)
        else:
            st.metric("👤 Unique Names", "N/A")

def render_add_customer_tab(sheets_manager):
    """Render add new customer form"""
    st.subheader("➕ Add New Customer")
    
    if 'customer_data' not in st.session_state or st.session_state.customer_data is None:
        st.warning("⚠️ No customer data loaded. Please configure data source in Overview tab first.")
        return
    
    df = st.session_state.customer_data
    
    # Dynamic form based on existing columns
    st.markdown("Fill in the customer information below:")
    
    with st.form("add_customer_form"):
        form_data = {}
        
        # Create input fields for each column
        for col in df.columns:
            col_lower = col.lower()
            
            # Determine input type based on column name and existing data
            if any(term in col_lower for term in ['email', 'mail']):
                form_data[col] = st.text_input(f"📧 {col}", placeholder="customer@example.com")
            elif any(term in col_lower for term in ['phone', 'mobile', 'tel']):
                form_data[col] = st.text_input(f"📞 {col}", placeholder="+1234567890")
            elif any(term in col_lower for term in ['date', 'created', 'added']):
                form_data[col] = st.date_input(f"📅 {col}", value=datetime.now().date())
            elif any(term in col_lower for term in ['value', 'revenue', 'amount', 'price']):
                form_data[col] = st.number_input(f"💰 {col}", min_value=0.0, step=0.01)
            elif any(term in col_lower for term in ['status', 'stage', 'type']):
                # Get unique values for dropdown
                unique_values = df[col].dropna().unique()
                if len(unique_values) > 0:
                    form_data[col] = st.selectbox(f"🏷️ {col}", [""] + list(unique_values))
                else:
                    form_data[col] = st.text_input(f"🏷️ {col}")
            elif any(term in col_lower for term in ['note', 'comment', 'description']):
                form_data[col] = st.text_area(f"📝 {col}")
            else:
                form_data[col] = st.text_input(f"📄 {col}")
        
        submitted = st.form_submit_button("➕ Add Customer", type="primary")
        
        if submitted:
            # Validate required fields (assume first few columns are required)
            required_fields = df.columns[:3]  # First 3 columns as required
            missing_fields = [field for field in required_fields if not form_data.get(field)]
            
            if missing_fields:
                st.error(f"❌ Please fill in required fields: {', '.join(missing_fields)}")
            else:
                try:
                    # Prepare new row data
                    new_row = []
                    for col in df.columns:
                        value = form_data.get(col, "")
                        if isinstance(value, datetime.date):
                            value = value.strftime("%Y-%m-%d")
                        new_row.append(value)
                    
                    # Add to Google Sheets
                    sheet_url = st.session_state.get('customer_sheet_url', '')
                    worksheet_name = st.session_state.get('customer_worksheet_name', '')
                    
                    if sheets_manager.append_row(sheet_url, new_row, worksheet_name):
                        st.success("✅ Customer added successfully!")
                        
                        # Clear cache and reload data
                        sheets_manager.clear_cache()
                        time.sleep(1)  # Brief delay for sheet update
                        
                        # Reload customer data
                        load_customer_data(sheets_manager, sheet_url, worksheet_name)
                        
                        st.rerun()
                    else:
                        st.error("❌ Failed to add customer to sheet")
                        
                except Exception as e:
                    st.error(f"❌ Error adding customer: {str(e)}")

def render_data_scanner_tab():
    """Render integrated data scanner for customer analysis"""
    st.subheader("🔍 Advanced Customer Data Analysis")
    
    if 'customer_data' not in st.session_state or st.session_state.customer_data is None:
        st.warning("⚠️ No customer data loaded. Please configure data source in Overview tab first.")
        return
    
    # Set the current dataframe for the scanner
    st.session_state.current_df = st.session_state.customer_data
    
    # Initialize and render data scanner
    scanner_ui = DataScannerUI()
    scanner_ui.scanner = scanner_ui.scanner or scanner_ui.scanner.__class__(st.session_state.customer_data)
    scanner_ui.viz_engine = scanner_ui.viz_engine or scanner_ui.viz_engine.__class__(st.session_state.customer_data)
    
    # Render analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Customer Overview", "🔍 Column Analysis", "📈 Visualizations", "💡 Insights"
    ])
    
    with tab1:
        scanner_ui._render_overview_tab()
    
    with tab2:
        scanner_ui._render_column_analysis_tab()
    
    with tab3:
        scanner_ui._render_visualizations_tab()
    
    with tab4:
        scanner_ui._render_insights_tab()

def load_customer_data(sheets_manager, sheet_url, worksheet_name):
    """Load customer data from Google Sheets"""
    try:
        with st.spinner("Loading customer data..."):
            df = sheets_manager.get_sheet_data(
                sheet_id=sheet_url,
                worksheet_name=worksheet_name if worksheet_name else None,
                use_cache=True
            )
            
            if df is not None and not df.empty:
                st.session_state.customer_data = df
                st.session_state.customer_sheet_url = sheet_url
                st.session_state.customer_worksheet_name = worksheet_name
                st.success(f"✅ Loaded {len(df):,} customer records")
            else:
                st.error("❌ No data found or sheet is empty")
                
    except Exception as e:
        st.error(f"❌ Error loading customer data: {str(e)}")

if __name__ == "__main__":
    main()
