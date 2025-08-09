import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import plotly.express as px
from io import BytesIO
import base64

st.set_page_config(page_title="📑 Invoice CRM Dashboard", layout="wide")

st.sidebar.title("🔐 Authentication Status")

# Check for global credentials
if not st.session_state.get("global_gsheets_creds"):
    st.sidebar.error("❌ No global credentials found")
    st.sidebar.info("Please upload service account JSON in the main sidebar")
    st.error("🔑 Google Sheets credentials not found. Please upload your service account JSON in the sidebar.")
    st.stop()
else:
    st.sidebar.success("✅ Using global credentials")
    client_email = st.session_state.global_gsheets_creds.get('client_email', 'Unknown')
    st.sidebar.info(f"📧 {client_email[:30]}...")

GOOGLE_SHEET_ID = "11ryUchUIGvsnW6cVsuI1rXYAk06xP3dZWcbQ8vyLFN4"
VISIBLE_COLUMNS = [
    "Customer name", "Customer email", "Product", "Product Description",
    "Price", "Invoice Link", "Status", "Date Created"
]

def safe_number_input(label, min_value=0.0, max_value=None, value=0.0, step=0.01):
    """Safe wrapper for st.number_input to handle min/max value conflicts"""
    try:
        if max_value is not None and min_value >= max_value:
            max_value = min_value + 1000.0  # Add buffer
        return st.number_input(label, min_value=min_value, max_value=max_value, value=value, step=step)
    except Exception as e:
        st.warning(f"Input error for {label}: {e}")
        return st.text_input(f"{label} (manual entry)", value=str(value))

def load_and_process_data():
    """Load and process data from Google Sheets"""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.session_state.global_gsheets_creds, 
            scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        data = sheet.get_all_records()
        
        if not data:
            st.warning("📋 No data found in the sheet")
            return pd.DataFrame(), None
            
        df = pd.DataFrame(data)
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Check for missing columns
        missing = [col for col in VISIBLE_COLUMNS if col not in df.columns]
        if missing:
            st.error(f"❌ Missing columns in Google Sheet: {missing}")
            st.info("Available columns: " + ", ".join(df.columns.tolist()))
            return pd.DataFrame(), None
        
        # Select only visible columns
        df = df[VISIBLE_COLUMNS]
        
        # Process data types
        df["Date Created"] = pd.to_datetime(df["Date Created"], errors='coerce')
        
        # Convert Price to numeric, handle errors
        df["Price"] = pd.to_numeric(df["Price"], errors='coerce').fillna(0)
        
        # Calculate invoice age - ensure numeric
        df["Invoice Age (Days)"] = (datetime.today() - df["Date Created"]).dt.days
        df["Invoice Age (Days)"] = pd.to_numeric(df["Invoice Age (Days)"], errors='coerce').fillna(0)
        
        # Fill NaN values for string columns only
        string_columns = df.select_dtypes(include=['object']).columns
        df[string_columns] = df[string_columns].fillna('')
        
        return df, sheet
        
    except Exception as e:
        st.error(f"❌ Failed to load data from Google Sheets: {str(e)}")
        return pd.DataFrame(), None

def create_pdf(df):
    """Create PDF export of filtered data"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica", 10)
        c.drawString(30, 750, f"Invoice Summary Export - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        y = 720
        for _, row in df.iterrows():
            text = f"{row['Customer name']} - {row['Product']} - ${row['Price']:.2f} - {row['Status']}"
            if len(text) > 80:  # Truncate long text
                text = text[:77] + "..."
            c.drawString(30, y, text)
            y -= 15
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = 750
        
        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except ImportError:
        st.warning("📄 ReportLab not available for PDF export")
        return None
    except Exception as e:
        st.error(f"PDF creation error: {e}")
        return None

# Main application logic
if st.session_state.get("global_gsheets_creds"):
    df, sheet = load_and_process_data()
    
    if df.empty:
        st.warning("📊 No data available to display")
        st.stop()
    
    st.title("📊 Invoice CRM Dashboard")
    
    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filters & Controls")
        
        # Status filter
        all_statuses = df["Status"].unique().tolist()
        if all_statuses:
            status_filter = st.multiselect(
                "Filter by Status", 
                all_statuses, 
                default=all_statuses,
                key="status_filter"
            )
        else:
            status_filter = []
        
        # Product filter
        all_products = df["Product"].unique().tolist()
        if all_products:
            product_filter = st.multiselect(
                "Filter by Product", 
                all_products, 
                default=all_products,
                key="product_filter"
            )
        else:
            product_filter = []
        
        # Search functionality
        search_text = st.text_input("🔎 Search Customer name/email", key="search_input").lower()
        
        # Price range filter
        if not df["Price"].empty and df["Price"].max() > df["Price"].min():
            price_min = float(df["Price"].min())
            price_max = float(df["Price"].max())
            
            if price_min == price_max:
                price_range = [price_min, price_max]
                st.info(f"All invoices have the same price: ${price_min:.2f}")
            else:
                price_range = st.slider(
                    "💰 Price Range",
                    min_value=price_min,
                    max_value=price_max,
                    value=[price_min, price_max],
                    step=0.01
                )
        else:
            price_range = [0.0, 0.0]
    
    # Apply filters
    filtered_df = df.copy()
    
    if status_filter:
        filtered_df = filtered_df[filtered_df["Status"].isin(status_filter)]
    
    if product_filter:
        filtered_df = filtered_df[filtered_df["Product"].isin(product_filter)]
    
    if search_text:
        mask = (
            filtered_df["Customer name"].str.lower().str.contains(search_text, na=False) |
            filtered_df["Customer email"].str.lower().str.contains(search_text, na=False)
        )
        filtered_df = filtered_df[mask]
    
    # Apply price filter
    if len(price_range) == 2 and price_range[1] > price_range[0]:
        filtered_df = filtered_df[
            (filtered_df["Price"] >= price_range[0]) & 
            (filtered_df["Price"] <= price_range[1])
        ]
    
    # Display metrics in card-style layout
    st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    .metric-delta {
        font-size: 0.8rem;
        color: #28a745;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Calculate metrics safely
    total_invoices = len(filtered_df)
    total_revenue = float(filtered_df["Price"].sum()) if not filtered_df.empty else 0.0
    
    # Safe calculation of average age
    if not filtered_df.empty:
        numeric_ages = pd.to_numeric(filtered_df["Invoice Age (Days)"], errors='coerce')
        avg_age = numeric_ages.mean() if not numeric_ages.isna().all() else 0.0
    else:
        avg_age = 0.0
    
    unpaid_count = len(filtered_df[filtered_df["Status"] != "Paid"]) if not filtered_df.empty else 0
    
    # Display metrics in cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📊 Total Invoices</div>
            <div class="metric-value">{total_invoices:,}</div>
            <div class="metric-delta">Active records</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">💰 Total Revenue</div>
            <div class="metric-value">${total_revenue:,.2f}</div>
            <div class="metric-delta">Filtered total</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">⏰ Avg Invoice Age</div>
            <div class="metric-value">{avg_age:.1f}</div>
            <div class="metric-delta">days outstanding</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">❌ Unpaid Invoices</div>
            <div class="metric-value">{unpaid_count}</div>
            <div class="metric-delta">need attention</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Invoice aging analysis with enhanced cards
    if not filtered_df.empty:
        # Ensure numeric calculation for aging
        numeric_ages = pd.to_numeric(filtered_df["Invoice Age (Days)"], errors='coerce').fillna(0)
        overdue_30 = filtered_df[numeric_ages > 30]
        overdue_21 = filtered_df[(numeric_ages > 21) & (numeric_ages <= 30)]
        overdue_7 = filtered_df[(numeric_ages > 7) & (numeric_ages <= 21)]
        current_invoices = filtered_df[numeric_ages <= 7]
        
        with st.expander("📅 Invoice Aging Analysis", expanded=True):
            st.markdown("""
            <style>
            .aging-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.2rem;
                border-radius: 12px;
                color: white;
                text-align: center;
                margin: 0.5rem 0;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .aging-card.danger {
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            }
            .aging-card.warning {
                background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);
            }
            .aging-card.info {
                background: linear-gradient(135deg, #48cae4 0%, #023e8a 100%);
            }
            .aging-card.success {
                background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
            }
            .aging-number {
                font-size: 2.5rem;
                font-weight: bold;
                margin: 0;
            }
            .aging-label {
                font-size: 0.9rem;
                opacity: 0.9;
                margin-top: 0.5rem;
            }
            </style>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="aging-card danger">
                    <div class="aging-number">{len(overdue_30)}</div>
                    <div class="aging-label">🚨 Over 30 days</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="aging-card warning">
                    <div class="aging-number">{len(overdue_21)}</div>
                    <div class="aging-label">⚠️ 21–30 days</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="aging-card info">
                    <div class="aging-number">{len(overdue_7)}</div>
                    <div class="aging-label">ℹ️ 7–21 days</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="aging-card success">
                    <div class="aging-number">{len(current_invoices)}</div>
                    <div class="aging-label">✅ Current (≤7 days)</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Charts with enhanced styling
    if not filtered_df.empty and not filtered_df["Date Created"].isna().all():
        st.markdown("---")
        st.subheader("📈 Analytics Dashboard")
        
        # Add some spacing and styling
        st.markdown("""
        <style>
        .chart-container {
            background-color: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            # Monthly sales chart
            monthly_data = filtered_df.copy()
            monthly_data["Month"] = monthly_data["Date Created"].dt.to_period("M").astype(str)
            sales_summary = monthly_data.groupby("Month")["Price"].sum().reset_index()
            
            if not sales_summary.empty:
                fig1 = px.bar(
                    sales_summary, 
                    x="Month", 
                    y="Price", 
                    title="💰 Revenue by Month",
                    color="Price",
                    color_continuous_scale="Blues",
                    template="plotly_white"
                )
                fig1.update_layout(
                    title_font_size=16,
                    showlegend=False,
                    margin=dict(t=50, l=50, r=50, b=50)
                )
                st.plotly_chart(fig1, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            # Status distribution
            status_counts = filtered_df["Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            
            if not status_counts.empty:
                fig2 = px.pie(
                    status_counts, 
                    values="Count", 
                    names="Status", 
                    title="📊 Invoice Status Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set3,
                    template="plotly_white"
                )
                fig2.update_layout(
                    title_font_size=16,
                    margin=dict(t=50, l=50, r=50, b=50)
                )
                fig2.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Additional analytics row
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            # Product distribution
            product_revenue = filtered_df.groupby("Product")["Price"].sum().reset_index()
            if not product_revenue.empty:
                fig3 = px.horizontal_bar(
                    product_revenue.head(10), 
                    x="Price", 
                    y="Product", 
                    title="🛍️ Top Products by Revenue",
                    color="Price",
                    color_continuous_scale="Greens",
                    template="plotly_white"
                )
                fig3.update_layout(
                    title_font_size=16,
                    showlegend=False,
                    margin=dict(t=50, l=50, r=50, b=50)
                )
                st.plotly_chart(fig3, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            # Invoice age distribution
            if not filtered_df.empty:
                age_bins = pd.cut(
                    pd.to_numeric(filtered_df["Invoice Age (Days)"], errors='coerce').fillna(0),
                    bins=[-1, 7, 21, 30, 60, float('inf')],
                    labels=['0-7 days', '8-21 days', '22-30 days', '31-60 days', '60+ days']
                )
                age_dist = age_bins.value_counts().reset_index()
                age_dist.columns = ["Age Range", "Count"]
                
                if not age_dist.empty:
                    fig4 = px.bar(
                        age_dist,
                        x="Age Range",
                        y="Count",
                        title="⏰ Invoice Age Distribution",
                        color="Count",
                        color_continuous_scale="Reds",
                        template="plotly_white"
                    )
                    fig4.update_layout(
                        title_font_size=16,
                        showlegend=False,
                        margin=dict(t=50, l=50, r=50, b=50),
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig4, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Invoice Cards Display
    st.markdown("---")
    st.subheader("📄 Invoice Records")
    
    if not filtered_df.empty:
        # Display options
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            view_mode = st.radio("Display Mode", ["📋 Card View", "📊 Table View"], horizontal=True)
        with col2:
            page_size = st.selectbox("Items per page", [6, 12, 18, 24], index=1)
        with col3:
            sort_by = st.selectbox("Sort by", ["Date Created", "Price", "Invoice Age (Days)", "Customer name"])
        with col4:
            sort_order = st.selectbox("Order", ["Descending", "Ascending"])
        
        # Sort the data
        ascending = sort_order == "Ascending"
        if sort_by in filtered_df.columns:
            if sort_by in ["Price", "Invoice Age (Days)"]:
                filtered_df[sort_by] = pd.to_numeric(filtered_df[sort_by], errors='coerce').fillna(0)
            filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)
        
        # Pagination
        total_rows = len(filtered_df)
        total_pages = (total_rows - 1) // page_size + 1 if total_rows > 0 else 1
        
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                page = st.selectbox(f"Page (1 of {total_pages})", range(1, total_pages + 1), key="page_selector") - 1
        else:
            page = 0
        
        start_idx = page * page_size
        end_idx = min(start_idx + page_size, total_rows)
        display_df = filtered_df.iloc[start_idx:end_idx]
        
        st.write(f"Showing {start_idx + 1}-{end_idx} of {total_rows} records")
        
        if view_mode == "📋 Card View":
            # Clean Card View using Streamlit native components
            cols_per_row = 2
            for i in range(0, len(display_df), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(display_df):
                        row = display_df.iloc[i + j]
                        
                        # Get and clean data
                        customer_name = str(row.get('Customer name', 'N/A'))
                        customer_email = str(row.get('Customer email', 'N/A'))
                        product = str(row.get('Product', 'N/A'))
                        product_desc = str(row.get('Product Description', ''))
                        status = str(row.get('Status', 'Unknown'))
                        
                        # Handle price
                        price = pd.to_numeric(row.get('Price', 0), errors='coerce')
                        if pd.isna(price):
                            price = 0
                        
                        # Handle age
                        age = pd.to_numeric(row.get('Invoice Age (Days)', 0), errors='coerce')
                        if pd.isna(age):
                            age = 0
                        
                        # Format date
                        date_created = row.get('Date Created', '')
                        if pd.notna(date_created) and hasattr(date_created, 'strftime'):
                            formatted_date = date_created.strftime('%b %d, %Y')
                        else:
                            formatted_date = str(date_created) if date_created else 'N/A'
                        
                        invoice_link = str(row.get('Invoice Link', ''))
                        
                        # Age category
                        if age <= 7:
                            age_status = "🟢 Current"
                        elif age <= 21:
                            age_status = "🟡 Follow Up"
                        else:
                            age_status = "🔴 Overdue"
                        
                        # Status emoji
                        status_emoji = {
                            'paid': '✅',
                            'pending': '⏳',
                            'overdue': '❌',
                            'draft': '📝'
                        }.get(status.lower(), '❓')
                        
                        with col:
                            # Create card using container
                            with st.container():
                                # Header with customer name and status
                                st.markdown(f"### 👤 {customer_name}")
                                col_status, col_price = st.columns([1, 1])
                                with col_status:
                                    st.markdown(f"**Status:** {status_emoji} {status}")
                                with col_price:
                                    st.markdown(f"**Price:** 💰 ${price:,.2f}")
                                
                                st.markdown("---")
                                
                                # Customer details
                                st.markdown(f"**📧 Email:** {customer_email}")
                                st.markdown(f"**🛍️ Product:** {product}")
                                
                                if product_desc and product_desc.strip() and product_desc != 'nan':
                                    with st.expander("📝 Product Description"):
                                        st.write(product_desc)
                                
                                # Timeline information
                                col_date, col_age = st.columns([1, 1])
                                with col_date:
                                    st.markdown(f"**📅 Created:** {formatted_date}")
                                with col_age:
                                    st.markdown(f"**⏰ Age:** {int(age)} days")
                                
                                # Age status indicator
                                st.markdown(f"**Status:** {age_status}")
                                
                                # Action buttons
                                st.markdown("**Actions:**")
                                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
                                
                                with btn_col1:
                                    if st.button("📧", key=f"email_{i+j}_{page}", help="Send email"):
                                        st.success(f"📬 Email sent to {customer_email}")
                                
                                with btn_col2:
                                    if st.button("✏️", key=f"edit_{i+j}_{page}", help="Edit invoice"):
                                        st.info(f"Edit mode for {customer_name}")
                                
                                with btn_col3:
                                    if invoice_link and invoice_link.strip() and invoice_link != 'nan':
                                        st.link_button("🔗", invoice_link, help="View invoice")
                                    else:
                                        st.button("🔗", key=f"nolink_{i+j}_{page}", disabled=True, help="No link available")
                                
                                with btn_col4:
                                    if st.button("🗑️", key=f"delete_{i+j}_{page}", help="Delete invoice"):
                                        st.warning(f"Delete confirmation needed for {customer_name}")
                                
                                st.markdown("---")
        
        else:
            # Enhanced Table View
            display_columns = [
                "Customer name", "Customer email", "Product", "Product Description",
                "Price", "Status", "Date Created", "Invoice Age (Days)", "Invoice Link"
            ]
            
            # Format the dataframe for better display
            formatted_df = display_df.copy()
            if "Price" in formatted_df.columns:
                formatted_df["Price"] = formatted_df["Price"].apply(lambda x: f"${pd.to_numeric(x, errors='coerce'):.2f}" if pd.notna(x) else "$0.00")
            if "Date Created" in formatted_df.columns:
                formatted_df["Date Created"] = pd.to_datetime(formatted_df["Date Created"], errors='coerce').dt.strftime('%Y-%m-%d')
            if "Invoice Age (Days)" in formatted_df.columns:
                formatted_df["Invoice Age (Days)"] = formatted_df["Invoice Age (Days)"].apply(lambda x: f"{int(pd.to_numeric(x, errors='coerce'))} days" if pd.notna(x) else "0 days")
            
            available_cols = [col for col in display_columns if col in formatted_df.columns]
            
            # Display table with enhanced features
            st.dataframe(
                formatted_df[available_cols], 
                use_container_width=True,
                height=600,
                column_config={
                    "Customer name": st.column_config.TextColumn("👤 Customer", width="medium"),
                    "Customer email": st.column_config.TextColumn("📧 Email", width="medium"),
                    "Product": st.column_config.TextColumn("🛍️ Product", width="medium"),
                    "Product Description": st.column_config.TextColumn("📝 Description", width="large"),
                    "Price": st.column_config.TextColumn("💰 Price", width="small"),
                    "Status": st.column_config.TextColumn("📊 Status", width="small"),
                    "Date Created": st.column_config.TextColumn("📅 Date", width="medium"),
                    "Invoice Age (Days)": st.column_config.TextColumn("⏰ Age", width="small"),
                    "Invoice Link": st.column_config.LinkColumn("🔗 Link", width="medium")
                }
            )
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV download
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download CSV", 
                csv, 
                f"invoices_{datetime.now().strftime('%Y%m%d')}.csv", 
                "text/csv",
                key="download_csv"
            )
        
        with col2:
            # PDF download
            pdf_file = create_pdf(filtered_df)
            if pdf_file:
                st.download_button(
                    "📄 Export PDF", 
                    pdf_file, 
                    f"invoices_{datetime.now().strftime('%Y%m%d')}.pdf", 
                    "application/pdf",
                    key="download_pdf"
                )
    else:
        st.info("No invoices match your current filters.")
    
    # Add new invoice
    with st.expander("➕ Add New Invoice"):
        with st.form("new_invoice_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input("Customer Name*")
                new_email = st.text_input("Customer Email*")
                new_product = st.text_input("Product*")
                new_desc = st.text_area("Product Description")
            
            with col2:
                new_price = safe_number_input("Price*", min_value=0.0, value=0.0, step=0.01)
                new_link = st.text_input("Invoice Link")
                new_status = st.selectbox("Status", ["Pending", "Paid", "Overdue", "Draft"])
                new_date = st.date_input("Date Created", datetime.today().date())
            
            submitted = st.form_submit_button("💾 Add Invoice to Sheet")
            
            if submitted:
                # Validate required fields
                if not new_name or not new_email or not new_product:
                    st.error("❌ Please fill in all required fields marked with *")
                elif not isinstance(new_price, (int, float)) or new_price < 0:
                    st.error("❌ Please enter a valid price")
                else:
                    try:
                        sheet.append_row([
                            new_name, 
                            new_email, 
                            new_product, 
                            new_desc,
                            float(new_price), 
                            new_link, 
                            new_status, 
                            str(new_date)
                        ])
                        st.success("✅ New invoice added successfully!")
                        st.experimental_rerun()  # Refresh the data
                    except Exception as e:
                        st.error(f"❌ Failed to add invoice: {str(e)}")
    
    # Email simulation section
    with st.expander("✉️ Email Management (Demo)"):
        st.info("📧 This is a demonstration of email functionality. In production, integrate with SendGrid, SMTP, or similar service.")
        
        if not filtered_df.empty:
            unpaid_invoices = filtered_df[filtered_df["Status"] != "Paid"]
            
            if not unpaid_invoices.empty:
                st.subheader("Unpaid Invoices - Send Reminders")
                
                for idx, row in unpaid_invoices.head(5).iterrows():  # Limit to 5 for demo
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"**{row['Customer name']}** ({row['Customer email']})")
                        st.write(f"Product: {row['Product']} - ${row['Price']:.2f}")
                    
                    with col2:
                        st.write(f"Status: {row['Status']}")
                        st.write(f"Age: {row['Invoice Age (Days)']} days")
                    
                    with col3:
                        if st.button(f"📧 Send", key=f"email_{idx}"):
                            st.success(f"📬 Reminder sent to {row['Customer email']} (simulated)")
            else:
                st.success("🎉 All invoices are paid!")
        else:
            st.info("No invoices to display")

else:
    st.info("⬅️ Please upload your Google Sheets service account JSON file to get started.")
    st.markdown("""
    ### Setup Instructions:
    1. Go to Google Cloud Console
    2. Create a service account
    3. Download the JSON credentials
    4. Upload the file using the sidebar
    5. Share your Google Sheet with the service account email
    """)
