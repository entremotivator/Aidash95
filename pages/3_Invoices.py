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
        
        # Calculate invoice age
        df["Invoice Age (Days)"] = (datetime.today() - df["Date Created"]).dt.days
        
        # Fill NaN values
        df = df.fillna('')
        
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
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Invoices", len(filtered_df))
    
    with col2:
        total_revenue = filtered_df["Price"].sum()
        st.metric("💰 Total Revenue", f"${total_revenue:,.2f}")
    
    with col3:
        if not filtered_df.empty and not filtered_df["Invoice Age (Days)"].isna().all():
            avg_age = filtered_df["Invoice Age (Days)"].mean()
            st.metric("⏰ Avg Invoice Age", f"{avg_age:.1f} days")
        else:
            st.metric("⏰ Avg Invoice Age", "N/A")
    
    with col4:
        unpaid_count = len(filtered_df[filtered_df["Status"] != "Paid"])
        st.metric("❌ Unpaid Invoices", unpaid_count)
    
    # Invoice aging analysis
    if not filtered_df.empty:
        overdue_30 = filtered_df[filtered_df["Invoice Age (Days)"] > 30]
        overdue_21 = filtered_df[(filtered_df["Invoice Age (Days)"] > 21) & (filtered_df["Invoice Age (Days)"] <= 30)]
        overdue_7 = filtered_df[(filtered_df["Invoice Age (Days)"] > 7) & (filtered_df["Invoice Age (Days)"] <= 21)]
        
        with st.expander("📅 Invoice Aging Analysis", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.error(f"🚨 Over 30 days: {len(overdue_30)}")
            with col2:
                st.warning(f"⚠️ 21–30 days: {len(overdue_21)}")
            with col3:
                st.info(f"ℹ️ 7–21 days: {len(overdue_7)}")
    
    # Charts
    if not filtered_df.empty and not filtered_df["Date Created"].isna().all():
        st.subheader("📈 Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
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
                    color_continuous_scale="Blues"
                )
                st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Status distribution
            status_counts = filtered_df["Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            
            if not status_counts.empty:
                fig2 = px.pie(
                    status_counts, 
                    values="Count", 
                    names="Status", 
                    title="📊 Invoice Status Distribution"
                )
                st.plotly_chart(fig2, use_container_width=True)
    
    # Data table
    st.subheader("📄 Invoice Data")
    
    if not filtered_df.empty:
        # Display options
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            show_all = st.checkbox("Show all columns", value=False)
        with col2:
            page_size = st.selectbox("Rows per page", [10, 25, 50, 100], index=1)
        with col3:
            st.write(f"Showing {len(filtered_df)} of {len(df)} total records")
        
        # Display dataframe
        display_df = filtered_df.copy()
        if not show_all:
            # Show only essential columns for better readability
            essential_cols = ["Customer name", "Product", "Price", "Status", "Invoice Age (Days)"]
            available_cols = [col for col in essential_cols if col in display_df.columns]
            display_df = display_df[available_cols]
        
        # Paginate results
        total_rows = len(display_df)
        total_pages = (total_rows - 1) // page_size + 1 if total_rows > 0 else 1
        
        if total_pages > 1:
            page = st.selectbox(f"Page (1-{total_pages})", range(1, total_pages + 1)) - 1
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, total_rows)
            display_df = display_df.iloc[start_idx:end_idx]
        
        st.dataframe(display_df, use_container_width=True)
        
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
