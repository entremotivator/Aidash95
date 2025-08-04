import streamlit as st
import pandas as pd
from datetime import datetime
from utils.auth import require_auth
from utils.gsheet_manager import get_sheets_manager
from components.data_scanner_ui import DataScannerUI
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from fpdf import FPDF

@require_auth
def main():
    st.title("💰 Pricing & Services Management")
    st.markdown("Comprehensive pricing management with Google Sheets integration and advanced analytics")
    
    # Initialize sheets manager
    sheets_manager = get_sheets_manager()
    
    # Check for global credentials
    if not st.session_state.get("global_gsheets_creds"):
        st.error("🔑 Google Sheets credentials not found. Please upload your service account JSON in the sidebar.")
        st.info("💡 Use the sidebar to upload your service account JSON file for full functionality.")
        st.stop()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview", "💰 Pricing List", "📈 Analytics", "➕ Add Service", "🔍 Data Scanner", "⚙️ Settings"
    ])
    
    with tab1:
        render_overview_tab(sheets_manager)
    
    with tab2:
        render_pricing_list_tab(sheets_manager)
    
    with tab3:
        render_analytics_tab(sheets_manager)
    
    with tab4:
        render_add_service_tab(sheets_manager)
    
    with tab5:
        render_data_scanner_tab()
    
    with tab6:
        render_settings_tab(sheets_manager)

def render_overview_tab(sheets_manager):
    """Render pricing overview dashboard"""
    st.subheader("📊 Pricing Overview")
    
    # Configuration section
    with st.expander("⚙️ Configure Pricing Data Source", expanded=True):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            sheet_url = st.text_input(
                "Pricing Sheet URL/ID",
                value="1WeDpcSNnfCrtx4F3bBC9osigPkzy3LXybRO6jpN7BXE",
                help="Enter your pricing data Google Sheet URL or ID"
            )
            
            worksheet_name = st.text_input(
                "Worksheet Name (optional)",
                placeholder="Pricing",
                help="Leave empty for first worksheet"
            )
        
        with col2:
            if st.button("🔄 Load Data", type="primary", use_container_width=True):
                load_pricing_data(sheets_manager, sheet_url, worksheet_name)
    
    # Display pricing data if loaded
    if 'pricing_data' in st.session_state and st.session_state.pricing_data is not None:
        df = st.session_state.pricing_data
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🛍️ Total Services", len(df))
        
        with col2:
            # Try to find price column
            price_cols = [col for col in df.columns if any(term in col.lower() for term in ['price', 'cost', 'rate', 'amount'])]
            if price_cols:
                prices = pd.to_numeric(df[price_cols[0]], errors='coerce').dropna()
                avg_price = prices.mean()
                st.metric("💰 Avg Price", f"${avg_price:,.2f}")
            else:
                st.metric("💰 Avg Price", "N/A")
        
        with col3:
            # Try to find category column
            category_cols = [col for col in df.columns if any(term in col.lower() for term in ['category', 'type', 'service'])]
            if category_cols:
                categories = df[category_cols[0]].nunique()
                st.metric("🏷️ Categories", categories)
            else:
                st.metric("🏷️ Categories", "N/A")
        
        with col4:
            # Price range
            if price_cols:
                prices = pd.to_numeric(df[price_cols[0]], errors='coerce').dropna()
                if len(prices) > 0:
                    price_range = f"${prices.min():,.0f} - ${prices.max():,.0f}"
                    st.metric("📊 Price Range", price_range)
                else:
                    st.metric("📊 Price Range", "N/A")
            else:
                st.metric("📊 Price Range", "N/A")
        
        # Service categories overview
        if category_cols and price_cols:
            st.subheader("📈 Services by Category")
            
            category_summary = df.groupby(category_cols[0]).agg({
                price_cols[0]: ['count', 'mean', 'sum']
            }).round(2)
            
            category_summary.columns = ['Count', 'Avg Price', 'Total Value']
            category_summary = category_summary.reset_index()
            
            # Create visualization
            fig = px.bar(
                category_summary,
                x=category_cols[0],
                y='Count',
                title="Number of Services by Category",
                color='Avg Price',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Display summary table
            st.dataframe(category_summary, use_container_width=True)
        
        # Recent services preview
        st.subheader("👀 Recent Services")
        display_cols = df.columns[:6]  # Show first 6 columns
        st.dataframe(df[display_cols].head(10), use_container_width=True)
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 Analyze Data", use_container_width=True):
                st.session_state.show_pricing_scanner = True
                st.rerun()
        
        with col2:
            if st.button("📤 Export CSV", use_container_width=True):
                csv = df.to_csv(index=False)
                st.download_button(
                    "💾 Download CSV",
                    csv,
                    f"pricing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
        
        with col3:
            if st.button("📄 Export PDF", use_container_width=True):
                pdf_bytes = create_pricing_pdf(df)
                st.download_button(
                    "💾 Download PDF",
                    pdf_bytes,
                    f"pricing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    "application/pdf"
                )
        
        with col4:
            if st.button("🔄 Refresh Data", use_container_width=True):
                sheets_manager.clear_cache()
                st.rerun()
    
    else:
        st.info("📋 Configure your pricing data source above to get started")

def render_pricing_list_tab(sheets_manager):
    """Render detailed pricing list with filtering and editing"""
    st.subheader("💰 Pricing Database")
    
    if 'pricing_data' not in st.session_state or st.session_state.pricing_data is None:
        st.warning("⚠️ No pricing data loaded. Please configure data source in Overview tab.")
        return
    
    df = st.session_state.pricing_data
    
    # Advanced filtering
    with st.expander("🔍 Advanced Filters", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Text search
            search_term = st.text_input("🔍 Search services", placeholder="Service name, description...")
        
        with col2:
            # Category filter
            category_cols = [col for col in df.columns if any(term in col.lower() for term in ['category', 'type', 'service'])]
            if category_cols:
                categories = ["All"] + sorted(df[category_cols[0]].dropna().unique().tolist())
                selected_category = st.selectbox("Filter by Category", categories)
            else:
                selected_category = "All"
        
        with col3:
            # Price range filter
            price_cols = [col for col in df.columns if any(term in col.lower() for term in ['price', 'cost', 'rate', 'amount'])]
            if price_cols:
                prices = pd.to_numeric(df[price_cols[0]], errors='coerce').dropna()
                if len(prices) > 0:
                    min_price, max_price = st.slider(
                        "Price Range",
                        min_value=float(prices.min()),
                        max_value=float(prices.max()),
                        value=(float(prices.min()), float(prices.max())),
                        step=1.0
                    )
                else:
                    min_price = max_price = 0
            else:
                min_price = max_price = 0
        
        with col4:
            # Sort options
            sort_column = st.selectbox("Sort by", df.columns.tolist())
            sort_order = st.radio("Order", ["Ascending", "Descending"], horizontal=True)
    
    # Apply filters
    filtered_df = df.copy()
    
    if search_term:
        # Search across all text columns
        text_cols = df.select_dtypes(include=['object']).columns
        mask = False
        for col in text_cols:
            mask |= df[col].astype(str).str.contains(search_term, case=False, na=False)
        filtered_df = df[mask]
    
    if selected_category != "All" and category_cols:
        filtered_df = filtered_df[filtered_df[category_cols[0]] == selected_category]
    
    if price_cols and min_price != max_price:
        prices = pd.to_numeric(filtered_df[price_cols[0]], errors='coerce')
        filtered_df = filtered_df[(prices >= min_price) & (prices <= max_price)]
    
    # Apply sorting
    if sort_column:
        ascending = sort_order == "Ascending"
        try:
            # Try numeric sort first
            filtered_df[sort_column] = pd.to_numeric(filtered_df[sort_column], errors='ignore')
            filtered_df = filtered_df.sort_values(sort_column, ascending=ascending)
        except:
            # Fall back to string sort
            filtered_df = filtered_df.sort_values(sort_column, ascending=ascending)
    
    # Display results
    st.write(f"📊 Showing {len(filtered_df)} of {len(df)} services")
    
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
        key="pricing_editor"
    )
    
    # Save changes button
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("💾 Save Changes", type="primary"):
            save_pricing_changes(sheets_manager, edited_df, display_df.index)
    
    with col2:
        if st.button("🗑️ Delete Selected"):
            st.warning("Delete functionality coming soon!")

def render_analytics_tab(sheets_manager):
    """Render pricing analytics and insights"""
    st.subheader("📈 Pricing Analytics")
    
    if 'pricing_data' not in st.session_state or st.session_state.pricing_data is None:
        st.warning("⚠️ No pricing data loaded. Please configure data source in Overview tab.")
        return
    
    df = st.session_state.pricing_data
    
    # Price analysis
    price_cols = [col for col in df.columns if any(term in col.lower() for term in ['price', 'cost', 'rate', 'amount'])]
    category_cols = [col for col in df.columns if any(term in col.lower() for term in ['category', 'type', 'service'])]
    
    if price_cols:
        prices = pd.to_numeric(df[price_cols[0]], errors='coerce').dropna()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Price distribution
            fig = px.histogram(
                x=prices,
                nbins=20,
                title="Price Distribution",
                color_discrete_sequence=['#2E86AB']
            )
            fig.update_layout(xaxis_title="Price ($)", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Price statistics
            st.subheader("📊 Price Statistics")
            stats = {
                "Mean": f"${prices.mean():.2f}",
                "Median": f"${prices.median():.2f}",
                "Std Dev": f"${prices.std():.2f}",
                "Min": f"${prices.min():.2f}",
                "Max": f"${prices.max():.2f}",
                "Range": f"${prices.max() - prices.min():.2f}"
            }
            
            for stat, value in stats.items():
                st.metric(stat, value)
        
        # Category analysis
        if category_cols:
            st.subheader("🏷️ Category Analysis")
            
            category_stats = df.groupby(category_cols[0])[price_cols[0]].agg([
                'count', 'mean', 'median', 'std', 'min', 'max'
            ]).round(2)
            
            category_stats.columns = ['Count', 'Mean', 'Median', 'Std Dev', 'Min', 'Max']
            
            # Visualization
            fig = px.box(
                df,
                x=category_cols[0],
                y=price_cols[0],
                title="Price Distribution by Category",
                color=category_cols[0]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistics table
            st.dataframe(category_stats, use_container_width=True)
    
    # Service analysis
    st.subheader("🛍️ Service Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Most expensive services
        if price_cols:
            top_expensive = df.nlargest(5, price_cols[0])
            st.write("**💰 Most Expensive Services**")
            for _, row in top_expensive.iterrows():
                service_name = row.iloc[0] if len(row) > 0 else "Unknown"
                price = row[price_cols[0]]
                st.write(f"• {service_name}: ${price}")
    
    with col2:
        # Most affordable services
        if price_cols:
            top_affordable = df.nsmallest(5, price_cols[0])
            st.write("**💸 Most Affordable Services**")
            for _, row in top_affordable.iterrows():
                service_name = row.iloc[0] if len(row) > 0 else "Unknown"
                price = row[price_cols[0]]
                st.write(f"• {service_name}: ${price}")
    
    with col3:
        # Category distribution
        if category_cols:
            category_counts = df[category_cols[0]].value_counts()
            st.write("**📊 Services by Category**")
            for category, count in category_counts.head(5).items():
                st.write(f"• {category}: {count}")
    
    # Competitive analysis
    st.subheader("🎯 Competitive Positioning")
    
    if price_cols:
        # Price percentiles
        percentiles = [10, 25, 50, 75, 90]
        price_percentiles = [prices.quantile(p/100) for p in percentiles]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=percentiles,
            y=price_percentiles,
            mode='lines+markers',
            name='Price Percentiles',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Price Percentiles",
            xaxis_title="Percentile",
            yaxis_title="Price ($)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_add_service_tab(sheets_manager):
    """Render add new service form"""
    st.subheader("➕ Add New Service")
    
    if 'pricing_data' not in st.session_state or st.session_state.pricing_data is None:
        st.warning("⚠️ No pricing data loaded. Please configure data source in Overview tab first.")
        return
    
    df = st.session_state.pricing_data
    
    # Dynamic form based on existing columns
    st.markdown("Fill in the service information below:")
    
    with st.form("add_service_form"):
        form_data = {}
        
        # Create input fields for each column
        col1, col2 = st.columns(2)
        
        for i, col in enumerate(df.columns):
            col_lower = col.lower()
            
            # Alternate between columns
            current_col = col1 if i % 2 == 0 else col2
            
            with current_col:
                # Determine input type based on column name and existing data
                if any(term in col_lower for term in ['price', 'cost', 'rate', 'amount']):
                    form_data[col] = st.number_input(f"💰 {col}", min_value=0.0, step=0.01)
                elif any(term in col_lower for term in ['category', 'type']):
                    # Get unique values for dropdown
                    unique_values = df[col].dropna().unique()
                    if len(unique_values) > 0:
                        form_data[col] = st.selectbox(f"🏷️ {col}", [""] + list(unique_values))
                    else:
                        form_data[col] = st.text_input(f"🏷️ {col}")
                elif any(term in col_lower for term in ['description', 'detail', 'note']):
                    form_data[col] = st.text_area(f"📝 {col}")
                elif any(term in col_lower for term in ['time', 'duration', 'turnaround']):
                    form_data[col] = st.text_input(f"⏱️ {col}", placeholder="e.g., 2-3 days")
                elif any(term in col_lower for term in ['url', 'link']):
                    form_data[col] = st.text_input(f"🔗 {col}", placeholder="https://...")
                else:
                    form_data[col] = st.text_input(f"📄 {col}")
        
        submitted = st.form_submit_button("➕ Add Service", type="primary")
        
        if submitted:
            # Validate required fields (assume first few columns are required)
            required_fields = df.columns[:2]  # First 2 columns as required
            missing_fields = [field for field in required_fields if not form_data.get(field)]
            
            if missing_fields:
                st.error(f"❌ Please fill in required fields: {', '.join(missing_fields)}")
            else:
                try:
                    # Prepare new row data
                    new_row = []
                    for col in df.columns:
                        value = form_data.get(col, "")
                        new_row.append(value)
                    
                    # Add to Google Sheets
                    sheet_url = st.session_state.get('pricing_sheet_url', '')
                    worksheet_name = st.session_state.get('pricing_worksheet_name', '')
                    
                    if sheets_manager.append_row(sheet_url, new_row, worksheet_name):
                        st.success("✅ Service added successfully!")
                        
                        # Clear cache and reload data
                        sheets_manager.clear_cache()
                        
                        # Reload pricing data
                        load_pricing_data(sheets_manager, sheet_url, worksheet_name)
                        
                        st.rerun()
                    else:
                        st.error("❌ Failed to add service to sheet")
                        
                except Exception as e:
                    st.error(f"❌ Error adding service: {str(e)}")

def render_data_scanner_tab():
    """Render integrated data scanner for pricing analysis"""
    st.subheader("🔍 Advanced Pricing Data Analysis")
    
    if 'pricing_data' not in st.session_state or st.session_state.pricing_data is None:
        st.warning("⚠️ No pricing data loaded. Please configure data source in Overview tab first.")
        return
    
    # Set the current dataframe for the scanner
    st.session_state.current_df = st.session_state.pricing_data
    
    # Initialize and render data scanner
    scanner_ui = DataScannerUI()
    scanner_ui.render_main_interface()

def render_settings_tab(sheets_manager):
    """Render settings and configuration"""
    st.subheader("⚙️ Settings & Configuration")
    
    # Sheet configuration
    st.subheader("📊 Sheet Configuration")
    
    with st.expander("🔧 Current Configuration", expanded=True):
        if 'pricing_sheet_url' in st.session_state:
            st.info(f"**Sheet URL:** {st.session_state.pricing_sheet_url}")
            st.info(f"**Worksheet:** {st.session_state.get('pricing_worksheet_name', 'Default')}")
        else:
            st.warning("No sheet configured")
    
    # Cache management
    st.subheader("🗄️ Cache Management")
    
    cache_info = sheets_manager.get_cache_info()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📦 Cached Sheets", cache_info['cached_sheets'])
    
    with col2:
        if cache_info['oldest_cache']:
            oldest = datetime.fromtimestamp(cache_info['oldest_cache'])
            st.metric("⏰ Oldest Cache", oldest.strftime("%H:%M:%S"))
        else:
            st.metric("⏰ Oldest Cache", "None")
    
    with col3:
        if st.button("🗑️ Clear Cache", use_container_width=True):
            sheets_manager.clear_cache()
            st.success("Cache cleared!")
            st.rerun()
    
    # Data validation rules
    st.subheader("✅ Data Validation")
    
    if 'pricing_data' in st.session_state and st.session_state.pricing_data is not None:
        df = st.session_state.pricing_data
        
        # Check for common issues
        issues = []
        
        # Check for missing prices
        price_cols = [col for col in df.columns if any(term in col.lower() for term in ['price', 'cost', 'rate', 'amount'])]
        if price_cols:
            missing_prices = df[price_cols[0]].isnull().sum()
            if missing_prices > 0:
                issues.append(f"❌ {missing_prices} services missing prices")
        
        # Check for duplicate services
        if len(df.columns) > 0:
            duplicates = df.duplicated(subset=[df.columns[0]]).sum()
            if duplicates > 0:
                issues.append(f"❌ {duplicates} duplicate service names")
        
        # Check for negative prices
        if price_cols:
            negative_prices = (pd.to_numeric(df[price_cols[0]], errors='coerce') < 0).sum()
            if negative_prices > 0:
                issues.append(f"❌ {negative_prices} services with negative prices")
        
        if issues:
            st.error("**Data Issues Found:**")
            for issue in issues:
                st.write(issue)
        else:
            st.success("✅ No data issues found!")
    
    # Export settings
    st.subheader("📤 Export Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Available Export Formats:**")
        st.write("• CSV (Comma Separated Values)")
        st.write("• PDF (Portable Document Format)")
        st.write("• Excel (Coming Soon)")
    
    with col2:
        st.write("**Export Options:**")
        include_charts = st.checkbox("Include charts in PDF", value=True)
        include_summary = st.checkbox("Include summary statistics", value=True)

def load_pricing_data(sheets_manager, sheet_url, worksheet_name):
    """Load pricing data from Google Sheets"""
    try:
        with st.spinner("Loading pricing data..."):
            df = sheets_manager.get_sheet_data(
                sheet_id=sheet_url,
                worksheet_name=worksheet_name if worksheet_name else None,
                use_cache=True
            )
            
            if df is not None and not df.empty:
                st.session_state.pricing_data = df
                st.session_state.pricing_sheet_url = sheet_url
                st.session_state.pricing_worksheet_name = worksheet_name
                st.success(f"✅ Loaded {len(df):,} pricing records")
            else:
                st.error("❌ No data found or sheet is empty")
                
    except Exception as e:
        st.error(f"❌ Error loading pricing data: {str(e)}")

def save_pricing_changes(sheets_manager, edited_df, original_indices):
    """Save changes back to Google Sheets"""
    try:
        # Get the full dataframe and update changed rows
        full_df = st.session_state.pricing_data.copy()
        
        for idx in edited_df.index:
            if idx in original_indices:
                full_df.loc[idx] = edited_df.loc[idx]
        
        # Save back to Google Sheets
        sheet_url = st.session_state.get('pricing_sheet_url', '')
        worksheet_name = st.session_state.get('pricing_worksheet_name', '')
        
        if sheets_manager.update_sheet_data(sheet_url, full_df, worksheet_name):
            st.session_state.pricing_data = full_df
            st.success("✅ Changes saved to Google Sheets!")
        else:
            st.error("❌ Failed to save changes")
            
    except Exception as e:
        st.error(f"❌ Error saving changes: {str(e)}")

def create_pricing_pdf(df):
    """Create PDF report of pricing data"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        elements.append(Paragraph("Pricing & Services Report", title_style))
        elements.append(Spacer(1, 20))
        
        # Summary
        summary_style = styles['Normal']
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", summary_style))
        elements.append(Paragraph(f"Total Services: {len(df)}", summary_style))
        elements.append(Spacer(1, 20))
        
        # Table data
        table_data = [df.columns.tolist()]  # Header
        for _, row in df.iterrows():
            table_data.append([str(cell)[:50] for cell in row.tolist()])  # Limit cell length
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        return buffer.getvalue()
        
    except Exception as e:
        st.error(f"Error creating PDF: {str(e)}")
        return None

if __name__ == "__main__":
    main()
