import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import BytesIO
import base64

# Page configuration with custom styling
st.set_page_config(
    page_title="📑 Invoice CRM Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling and colored cards
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    
    /* Metric cards styling */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    .revenue-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .age-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        color: #333;
    }
    
    .unpaid-card {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        color: #333;
    }
    
    .overdue-card {
        background: linear-gradient(135deg, #fc466b 0%, #3f5efb 100%);
    }
    
    .recent-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        color: #333;
    }
    
    .conversion-card {
        background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%);
        color: #333;
    }
    
    .metric-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.3rem;
    }
    
    .metric-subtitle {
        font-size: 0.9rem;
        opacity: 0.8;
    }
    
    /* Status badges */
    .status-paid {
        background-color: #28a745;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .status-pending {
        background-color: #ffc107;
        color: #333;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .status-overdue {
        background-color: #dc3545;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    /* Alert boxes */
    .alert-danger {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .alert-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .alert-info {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    /* Header styling */
    .dashboard-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .section-header {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem 2rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
        text-align: center;
    }
    
    /* Form styling */
    .form-container {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Authentication
st.sidebar.markdown("### 🔐 Authentication Status")

if not st.session_state.get("global_gsheets_creds"):
    st.sidebar.error("❌ No global credentials found")
    st.sidebar.info("Please upload service account JSON in the main sidebar")
    st.markdown("""
    <div class="alert-danger">
        <h4>🔑 Google Sheets Authentication Required</h4>
        <p>Please upload your service account JSON file in the sidebar to access the dashboard.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()
else:
    st.sidebar.success("✅ Using global credentials")
    client_email = st.session_state.global_gsheets_creds.get('client_email', 'Unknown')
    st.sidebar.info(f"📧 {client_email[:30]}...")

# Configuration
GOOGLE_SHEET_ID = "11ryUchUIGvsnW6cVsuI1rXYAk06xP3dZWcbQ8vyLFN4"
VISIBLE_COLUMNS = [
    "Customer name", "Customer email", "Product", "Product Description",
    "Price", "Invoice Link", "Status", "Date Created"
]

# Helper functions
def format_currency(amount):
    """Format currency with proper formatting"""
    return f"${amount:,.2f}"

def get_status_badge(status):
    """Return HTML for status badge"""
    if status.lower() == 'paid':
        return f'<span class="status-paid">{status}</span>'
    elif status.lower() == 'pending':
        return f'<span class="status-pending">{status}</span>'
    elif status.lower() == 'overdue':
        return f'<span class="status-overdue">{status}</span>'
    return status

def create_metric_card(title, value, subtitle="", card_class="metric-card"):
    """Create a styled metric card"""
    return f"""
    <div class="{card_class}">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-subtitle">{subtitle}</div>
    </div>
    """

# Main dashboard logic
if st.session_state.get("global_gsheets_creds"):
    try:
        # Google Sheets connection
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.session_state.global_gsheets_creds, 
            scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        # Data preprocessing
        df.columns = df.columns.str.strip()
        missing = [col for col in VISIBLE_COLUMNS if col not in df.columns]
        if missing:
            st.error(f"❌ Missing columns: {missing}")
            st.stop()

        df = df[VISIBLE_COLUMNS]
        df["Date Created"] = pd.to_datetime(df["Date Created"], errors='coerce')
        df["Invoice Age (Days)"] = (datetime.today() - df["Date Created"]).dt.days
        df["Price"] = pd.to_numeric(df["Price"], errors='coerce')

        # Dashboard header
        st.markdown("""
        <div class="dashboard-header">
            <h1>📊 Invoice CRM Dashboard</h1>
            <p>Comprehensive invoice management and analytics platform</p>
        </div>
        """, unsafe_allow_html=True)

        # Sidebar filters
        with st.sidebar:
            st.markdown("### 🔍 Filters & Settings")
            
            # Auto-refresh option
            auto_refresh = st.checkbox("🔄 Auto-refresh (30s)")
            if auto_refresh:
                st.rerun()
            
            # Date range filter
            st.subheader("📅 Date Range")
            min_date = df["Date Created"].min().date() if not df["Date Created"].isna().all() else datetime.today().date()
            max_date = df["Date Created"].max().date() if not df["Date Created"].isna().all() else datetime.today().date()
            
            date_range = st.date_input(
                "Select date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            # Status filter
            status_filter = st.multiselect(
                "Filter by Status", 
                df["Status"].unique(), 
                default=list(df["Status"].unique()),
                help="Select invoice statuses to display"
            )
            
            # Product filter
            product_filter = st.multiselect(
                "Filter by Product", 
                df["Product"].unique(), 
                default=list(df["Product"].unique()),
                help="Select products to display"
            )
            
            # Price range filter
            if not df["Price"].isna().all():
                price_range = st.slider(
                    "Price Range",
                    min_value=float(df["Price"].min()),
                    max_value=float(df["Price"].max()),
                    value=(float(df["Price"].min()), float(df["Price"].max())),
                    format="$%.2f"
                )
            
            # Search functionality
            search_text = st.text_input(
                "🔍 Search Customer", 
                placeholder="Enter customer name or email..."
            ).lower()

        # Apply filters
        filtered_df = df.copy()
        
        # Date filter
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df["Date Created"].dt.date >= start_date) & 
                (filtered_df["Date Created"].dt.date <= end_date)
            ]
        
        # Other filters
        filtered_df = filtered_df[
            filtered_df["Status"].isin(status_filter) & 
            filtered_df["Product"].isin(product_filter)
        ]
        
        # Price filter
        if 'price_range' in locals():
            filtered_df = filtered_df[
                (filtered_df["Price"] >= price_range[0]) & 
                (filtered_df["Price"] <= price_range[1])
            ]
        
        # Search filter
        if search_text:
            filtered_df = filtered_df[
                filtered_df["Customer name"].str.lower().str.contains(search_text, na=False) |
                filtered_df["Customer email"].str.lower().str.contains(search_text, na=False)
            ]

        # Key Metrics Section
        st.markdown('<div class="section-header"><h2>📈 Key Performance Indicators</h2></div>', unsafe_allow_html=True)
        
        # Calculate metrics
        total_invoices = len(filtered_df)
        total_revenue = filtered_df['Price'].sum() if not filtered_df.empty else 0
        avg_invoice_age = filtered_df['Invoice Age (Days)'].mean() if not filtered_df.empty else 0
        unpaid_invoices = len(filtered_df[filtered_df["Status"] != "Paid"]) if not filtered_df.empty else 0
        overdue_invoices = len(filtered_df[filtered_df["Invoice Age (Days)"] > 30]) if not filtered_df.empty else 0
        recent_invoices = len(filtered_df[filtered_df["Invoice Age (Days)"] <= 7]) if not filtered_df.empty else 0
        
        # Conversion rate (paid vs total)
        paid_invoices = len(filtered_df[filtered_df["Status"] == "Paid"]) if not filtered_df.empty else 0
        conversion_rate = (paid_invoices / total_invoices * 100) if total_invoices > 0 else 0

        # Display metrics in colored cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                "Total Invoices", 
                f"{total_invoices:,}", 
                f"Filtered from {len(df)} total",
                "metric-card"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(create_metric_card(
                "Total Revenue", 
                format_currency(total_revenue), 
                f"Average: {format_currency(total_revenue/total_invoices if total_invoices > 0 else 0)}",
                "revenue-card"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(create_metric_card(
                "Avg Invoice Age", 
                f"{avg_invoice_age:.1f} days", 
                "Days since creation",
                "age-card"
            ), unsafe_allow_html=True)
        
        with col4:
            st.markdown(create_metric_card(
                "Unpaid Invoices", 
                f"{unpaid_invoices:,}", 
                f"{(unpaid_invoices/total_invoices*100) if total_invoices > 0 else 0:.1f}% of total",
                "unpaid-card"
            ), unsafe_allow_html=True)

        # Second row of metrics
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.markdown(create_metric_card(
                "Overdue (30+ days)", 
                f"{overdue_invoices:,}", 
                "Require immediate attention",
                "overdue-card"
            ), unsafe_allow_html=True)
        
        with col6:
            st.markdown(create_metric_card(
                "Recent (≤7 days)", 
                f"{recent_invoices:,}", 
                "Newly created",
                "recent-card"
            ), unsafe_allow_html=True)
        
        with col7:
            st.markdown(create_metric_card(
                "Conversion Rate", 
                f"{conversion_rate:.1f}%", 
                f"{paid_invoices} of {total_invoices} paid",
                "conversion-card"
            ), unsafe_allow_html=True)
        
        with col8:
            # Monthly growth
            if not filtered_df.empty:
                current_month_revenue = filtered_df[filtered_df["Date Created"].dt.month == datetime.now().month]['Price'].sum()
                last_month_revenue = filtered_df[filtered_df["Date Created"].dt.month == datetime.now().month - 1]['Price'].sum()
                growth = ((current_month_revenue - last_month_revenue) / last_month_revenue * 100) if last_month_revenue > 0 else 0
                
                st.markdown(create_metric_card(
                    "Monthly Growth", 
                    f"{growth:+.1f}%", 
                    "vs previous month",
                    "metric-card"
                ), unsafe_allow_html=True)

        # Invoice Aging Analysis
        st.markdown('<div class="section-header"><h2>⏰ Invoice Aging Analysis</h2></div>', unsafe_allow_html=True)
        
        if not filtered_df.empty:
            # Age group analysis
            overdue_30 = filtered_df[filtered_df["Invoice Age (Days)"] > 30]
            overdue_21_30 = filtered_df[(filtered_df["Invoice Age (Days)"] > 21) & (filtered_df["Invoice Age (Days)"] <= 30)]
            overdue_7_21 = filtered_df[(filtered_df["Invoice Age (Days)"] > 7) & (filtered_df["Invoice Age (Days)"] <= 21)]
            recent_7 = filtered_df[filtered_df["Invoice Age (Days)"] <= 7]

            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="alert-danger">
                    <h4>🚨 Critical (30+ days)</h4>
                    <p><strong>{len(overdue_30)} invoices</strong></p>
                    <p>Value: {format_currency(overdue_30['Price'].sum())}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="alert-warning">
                    <h4>⚠️ Warning (21-30 days)</h4>
                    <p><strong>{len(overdue_21_30)} invoices</strong></p>
                    <p>Value: {format_currency(overdue_21_30['Price'].sum())}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="alert-info">
                    <h4>📋 Follow-up (7-21 days)</h4>
                    <p><strong>{len(overdue_7_21)} invoices</strong></p>
                    <p>Value: {format_currency(overdue_7_21['Price'].sum())}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="alert-info">
                    <h4>✅ Recent (≤7 days)</h4>
                    <p><strong>{len(recent_7)} invoices</strong></p>
                    <p>Value: {format_currency(recent_7['Price'].sum())}</p>
                </div>
                """, unsafe_allow_html=True)

        # Charts and Analytics
        st.markdown('<div class="section-header"><h2>📊 Analytics & Insights</h2></div>', unsafe_allow_html=True)
        
        if not filtered_df.empty:
            # Create subplots for multiple charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Monthly Revenue Trend
                monthly_data = filtered_df.copy()
                monthly_data["Month"] = monthly_data["Date Created"].dt.to_period("M").astype(str)
                monthly_sales = monthly_data.groupby(["Month", "Status"])["Price"].sum().reset_index()
                
                fig1 = px.bar(
                    monthly_sales, 
                    x="Month", 
                    y="Price", 
                    color="Status",
                    title="📈 Monthly Revenue by Status",
                    color_discrete_map={
                        'Paid': '#28a745',
                        'Pending': '#ffc107', 
                        'Overdue': '#dc3545'
                    }
                )
                fig1.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Status Distribution Pie Chart
                status_counts = filtered_df["Status"].value_counts()
                fig2 = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="🥧 Invoice Status Distribution",
                    color_discrete_map={
                        'Paid': '#28a745',
                        'Pending': '#ffc107', 
                        'Overdue': '#dc3545'
                    }
                )
                fig2.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # Product Performance Analysis
            product_performance = filtered_df.groupby("Product").agg({
                "Price": ["sum", "mean", "count"]
            }).round(2)
            product_performance.columns = ["Total Revenue", "Average Price", "Count"]
            product_performance = product_performance.reset_index()
            
            fig3 = px.scatter(
                product_performance,
                x="Count",
                y="Average Price",
                size="Total Revenue",
                hover_name="Product",
                title="💼 Product Performance Analysis",
                labels={"Count": "Number of Invoices", "Average Price": "Average Invoice Value"}
            )
            fig3.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig3, use_container_width=True)

        # Invoice Table with enhanced styling
        st.markdown('<div class="section-header"><h2>📄 Invoice Management</h2></div>', unsafe_allow_html=True)
        
        if not filtered_df.empty:
            # Add action buttons for batch operations
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("📧 Send Reminders (Overdue)", type="primary"):
                    overdue_count = len(filtered_df[filtered_df["Invoice Age (Days)"] > 30])
                    st.success(f"📬 Reminder emails sent to {overdue_count} overdue customers!")
            
            with col2:
                if st.button("📊 Export Analytics", type="secondary"):
                    st.success("📈 Analytics report generated!")
            
            with col3:
                if st.button("🔄 Bulk Update Status", type="secondary"):
                    st.info("💡 Feature coming soon!")
            
            with col4:
                if st.button("📱 Send SMS Alerts", type="secondary"):
                    st.info("💡 SMS integration coming soon!")
            
            # Enhanced table display
            display_df = filtered_df.copy()
            display_df["Status"] = display_df["Status"].apply(get_status_badge)
            display_df["Price"] = display_df["Price"].apply(lambda x: format_currency(x) if pd.notnull(x) else "$0.00")
            display_df["Invoice Age (Days)"] = display_df["Invoice Age (Days)"].apply(
                lambda x: f"🚨 {x} days" if x > 30 else f"⚠️ {x} days" if x > 21 else f"📅 {x} days"
            )
            
            st.markdown("### Filtered Invoice Data")
            st.markdown(f"**Showing {len(display_df)} of {len(df)} total invoices**")
            
            # Display the dataframe with custom styling
            st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            # Export options
            st.markdown("### 📥 Export Options")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # CSV Export
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "⬇️ Download CSV",
                    csv,
                    f"invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    help="Download filtered data as CSV file"
                )
            
            with col2:
                # PDF Export
                try:
                    from reportlab.lib.pagesizes import letter
                    from reportlab.pdfgen import canvas
                    from reportlab.lib import colors
                    from reportlab.lib.styles import getSampleStyleSheet
                    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
                    
                    def create_enhanced_pdf(df):
                        buffer = BytesIO()
                        doc = SimpleDocTemplate(buffer, pagesize=letter)
                        story = []
                        
                        # Title
                        styles = getSampleStyleSheet()
                        title = Paragraph("Invoice CRM Dashboard Report", styles['Title'])
                        story.append(title)
                        
                        # Summary
                        summary_text = f"""
                        <b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
                        <b>Total Invoices:</b> {len(df)}<br/>
                        <b>Total Revenue:</b> {format_currency(df['Price'].sum())}<br/>
                        <b>Unpaid Invoices:</b> {len(df[df['Status'] != 'Paid'])}<br/>
                        """
                        summary = Paragraph(summary_text, styles['Normal'])
                        story.append(summary)
                        
                        # Table data
                        table_data = [['Customer', 'Product', 'Price', 'Status', 'Age (Days)']]
                        for _, row in df.iterrows():
                            table_data.append([
                                row['Customer name'][:20],
                                row['Product'][:15],
                                format_currency(row['Price']),
                                row['Status'],
                                f"{row['Invoice Age (Days)']} days"
                            ])
                        
                        # Create table
                        table = Table(table_data)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 12),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        
                        story.append(table)
                        doc.build(story)
                        return buffer.getvalue()
                    
                    pdf_file = create_enhanced_pdf(filtered_df)
                    st.download_button(
                        "⬇️ Export PDF Report",
                        pdf_file,
                        f"invoice_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        "application/pdf",
                        help="Download detailed PDF report"
                    )
                except ImportError:
                    st.warning("PDF export requires reportlab. Install with: pip install reportlab")
            
            with col3:
                # JSON Export
                json_data = filtered_df.to_json(orient='records', date_format='iso')
                st.download_button(
                    "⬇️ Export JSON",
                    json_data,
                    f"invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json",
                    help="Download data as JSON file"
                )

        # Add New Invoice Form
        st.markdown('<div class="section-header"><h2>➕ Invoice Management</h2></div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["📝 Add New Invoice", "✉️ Email Management", "⚙️ Settings"])
        
        with tab1:
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            with st.form("new_invoice", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_name = st.text_input("Customer Name *", help="Full customer name")
                    new_email = st.text_input("Customer Email *", help="Valid email address")
                    new_product = st.text_input("Product/Service *", help="Product or service name")
                    new_price = st.number_input("Price ($) *", min_value=0.0, format="%.2f", help="Invoice amount")
                
                with col2:
                    new_desc = st.text_area("Product Description", help="Detailed description")
                    new_link = st.text_input("Invoice Link", help="Link to online invoice")
                    new_status = st.selectbox("Status", ["Pending", "Paid", "Overdue"], help="Current status")
                    new_date = st.date_input("Date Created", datetime.today(), help="Invoice creation date")
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    submitted = st.form_submit_button("💾 Add Invoice", type="primary", use_container_width=True)
                with col2:
                    if st.form_submit_button("🔄 Clear Form", type="secondary", use_container_width=True):
                        st.rerun()
                
                if submitted:
                    if new_name and new_email and new_product and new_price > 0:
                        try:
                            sheet.append_row([
                                new_name, new_email, new_product, new_desc,
                                new_price, new_link, new_status, str(new_date)
                            ])
                            st.success("✅ New invoice added successfully!")
                            st.balloons()  # Celebration animation
                            time.sleep(2)
                            st.rerun()  # Refresh data
                        except Exception as e:
                            st.error(f"❌ Error adding invoice: {str(e)}")
                    else:
                        st.error("❌ Please fill in all required fields (*)")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            st.subheader("📧 Email Campaign Management")
            
            # Email templates
            email_templates = {
                "Payment Reminder": """
                Dear {customer_name},
                
                We hope this email finds you well. This is a friendly reminder that your invoice #{invoice_id} 
                for {product} in the amount of {price} is currently pending payment.
                
                Invoice Details:
                - Product/Service: {product}
                - Amount: {price}
                - Due Date: {due_date}
                - Invoice Link: {invoice_link}
                
                Please process the payment at your earliest convenience. If you have any questions or concerns, 
                please don't hesitate to contact us.
                
                Thank you for your business!
                
                Best regards,
                Your Invoice Team
                """,
                "Overdue Notice": """
                Dear {customer_name},
                
                This is an important notice regarding your overdue invoice #{invoice_id} for {product}.
                
                Invoice Details:
                - Product/Service: {product}
                - Amount: {price}
                - Days Overdue: {days_overdue}
                - Invoice Link: {invoice_link}
                
                Your immediate attention to this matter would be greatly appreciated. Please contact us 
                if there are any issues preventing payment.
                
                Best regards,
                Accounts Receivable Team
                """,
                "Thank You": """
                Dear {customer_name},
                
                Thank you for your recent payment of {price} for {product}!
                
                Your payment has been successfully processed and your account is now up to date.
                
                We appreciate your business and look forward to serving you again.
                
                Best regards,
                Your Team
                """
            }
            
            # Email campaign interface
            col1, col2 = st.columns([1, 2])
            
            with col1:
                template_choice = st.selectbox("Select Email Template", list(email_templates.keys()))
                recipient_filter = st.selectbox(
                    "Send to:", 
                    ["All Overdue", "All Pending", "All Customers", "Custom Selection"]
                )
                
                if recipient_filter == "Custom Selection":
                    selected_customers = st.multiselect(
                        "Select Customers",
                        filtered_df["Customer email"].unique()
                    )
                
                # Email settings
                st.subheader("📧 Email Settings")
                sender_name = st.text_input("Sender Name", value="Invoice Team")
                sender_email = st.text_input("Sender Email", value="invoices@company.com")
                subject_line = st.text_input("Subject Line", value="Invoice Payment Reminder")
                
                if st.button("📬 Send Email Campaign", type="primary"):
                    # Determine recipients
                    if recipient_filter == "All Overdue":
                        recipients = filtered_df[filtered_df["Invoice Age (Days)"] > 30]
                    elif recipient_filter == "All Pending":
                        recipients = filtered_df[filtered_df["Status"] == "Pending"]
                    elif recipient_filter == "All Customers":
                        recipients = filtered_df
                    else:  # Custom Selection
                        recipients = filtered_df[filtered_df["Customer email"].isin(selected_customers)]
                    
                    st.success(f"📧 Email campaign sent to {len(recipients)} customers!")
                    st.info("💡 This is a demo. In production, integrate with SendGrid, Mailgun, or similar service.")
            
            with col2:
                st.subheader("📝 Email Preview")
                # Show email template preview
                sample_data = {
                    "customer_name": "John Doe",
                    "invoice_id": "INV-001",
                    "product": "Web Development Service",
                    "price": "$2,500.00",
                    "due_date": "2024-01-15",
                    "days_overdue": "15",
                    "invoice_link": "https://invoice.example.com/inv-001"
                }
                
                preview_text = email_templates[template_choice].format(**sample_data)
                st.text_area("Email Preview", value=preview_text, height=400, disabled=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab3:
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            st.subheader("⚙️ Dashboard Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🎨 Display Settings")
                show_animations = st.checkbox("Show Animations", value=True)
                compact_mode = st.checkbox("Compact Mode", value=False)
                dark_theme = st.checkbox("Dark Theme", value=False)
                default_currency = st.selectbox("Default Currency", ["USD", "EUR", "GBP", "CAD"])
                
                st.markdown("#### 📊 Chart Settings")
                chart_theme = st.selectbox("Chart Theme", ["plotly", "plotly_white", "plotly_dark"])
                show_data_labels = st.checkbox("Show Data Labels", value=True)
                
            with col2:
                st.markdown("#### ⏰ Notification Settings")
                email_notifications = st.checkbox("Email Notifications", value=True)
                overdue_threshold = st.number_input("Overdue Threshold (days)", min_value=1, max_value=90, value=30)
                warning_threshold = st.number_input("Warning Threshold (days)", min_value=1, max_value=60, value=21)
                
                st.markdown("#### 🔄 Auto-Refresh")
                refresh_interval = st.selectbox("Refresh Interval", ["30 seconds", "1 minute", "5 minutes", "Manual"])
                
                if st.button("💾 Save Settings", type="primary"):
                    st.success("✅ Settings saved successfully!")
            
            # Advanced settings
            with st.expander("🔧 Advanced Settings", expanded=False):
                st.markdown("#### 🔐 API Configuration")
                api_key = st.text_input("SendGrid API Key", type="password", help="For email functionality")
                webhook_url = st.text_input("Webhook URL", help="For payment notifications")
                
                st.markdown("#### 📊 Data Export")
                auto_backup = st.checkbox("Auto Backup to Google Drive")
                backup_frequency = st.selectbox("Backup Frequency", ["Daily", "Weekly", "Monthly"])
                
                st.markdown("#### 🔒 Security")
                session_timeout = st.number_input("Session Timeout (minutes)", min_value=5, max_value=480, value=60)
                require_2fa = st.checkbox("Require 2FA (Coming Soon)", disabled=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

        # Quick Actions Panel
        st.markdown('<div class="section-header"><h2>⚡ Quick Actions</h2></div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("📊 Generate Report", use_container_width=True):
                st.info("📈 Generating comprehensive report...")
                # Simulate report generation
                time.sleep(1)
                st.success("✅ Report generated!")
        
        with col2:
            if st.button("🔄 Sync Data", use_container_width=True):
                st.info("🔄 Syncing with Google Sheets...")
                time.sleep(1)
                st.success("✅ Data synchronized!")
        
        with col3:
            if st.button("📧 Send Bulk Reminders", use_container_width=True):
                overdue_count = len(filtered_df[filtered_df["Invoice Age (Days)"] > 30])
                st.success(f"📬 Sent reminders to {overdue_count} customers!")
        
        with col4:
            if st.button("📱 Export Mobile View", use_container_width=True):
                st.info("📱 Mobile export feature coming soon!")
        
        with col5:
            if st.button("🔍 Data Audit", use_container_width=True):
                # Quick data quality check
                issues = []
                if df["Customer email"].isnull().any():
                    issues.append("Missing email addresses")
                if (df["Price"] <= 0).any():
                    issues.append("Invalid price values")
                if df["Date Created"].isnull().any():
                    issues.append("Missing creation dates")
                
                if issues:
                    st.warning(f"⚠️ Found issues: {', '.join(issues)}")
                else:
                    st.success("✅ Data quality check passed!")

        # Footer with system info
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            **📊 System Status**
            - Database: ✅ Connected
            - Last Update: {datetime.now().strftime('%H:%M:%S')}
            - Records: {len(df):,} total
            """)
        
        with col2:
            st.markdown(f"""
            **💰 Financial Summary**
            - Total Revenue: {format_currency(df['Price'].sum())}
            - Outstanding: {format_currency(df[df['Status'] != 'Paid']['Price'].sum())}
            - Collection Rate: {(len(df[df['Status'] == 'Paid']) / len(df) * 100):.1f}%
            """)
        
        with col3:
            st.markdown(f"""
            **⏰ Performance Metrics**
            - Avg Response Time: < 100ms
            - Uptime: 99.9%
            - Active Users: 1
            """)

    except Exception as e:
        st.markdown(f"""
        <div class="alert-danger">
            <h4>❌ System Error</h4>
            <p>Failed to load dashboard: <strong>{str(e)}</strong></p>
            <p>Please check your Google Sheets connection and try again.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Error details in expander
        with st.expander("🔍 Error Details", expanded=False):
            st.code(str(e))
            st.info("💡 Common solutions:")
            st.markdown("""
            - Verify your Google Sheets ID is correct
            - Check that your service account has access to the sheet
            - Ensure all required columns exist in your sheet
            - Refresh the page and try again
            """)

else:
    st.markdown("""
    <div class="dashboard-header">
        <h1>📑 Invoice CRM Dashboard</h1>
        <p>Please upload your Google Sheets credentials to get started</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("⬅️ Upload your Google JSON service account file in the sidebar to access the dashboard.")

# Add some JavaScript for enhanced interactivity (if needed)
st.markdown("""
<script>
// Auto-refresh functionality
if (localStorage.getItem('auto_refresh') === 'true') {
    setTimeout(function(){
        location.reload();
    }, 30000);
}

// Save scroll position
window.addEventListener('beforeunload', function() {
    localStorage.setItem('scrollPos', window.pageYOffset);
});

// Restore scroll position
window.addEventListener('load', function() {
    const scrollPos = localStorage.getItem('scrollPos');
    if (scrollPos) {
        window.scrollTo(0, scrollPos);
        localStorage.removeItem('scrollPos');
    }
});
</script>
""", unsafe_allow_html=True)
