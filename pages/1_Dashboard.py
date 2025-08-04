import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from utils.auth import require_auth
from utils.gsheet_manager import get_sheets_manager
from components.data_scanner_ui import DataScannerUI

@require_auth
def main():
    st.title("📊 Business Dashboard")
    st.markdown("**Live Business Intelligence Dashboard** - Real-time metrics from all your Google Sheets")
    
    # Initialize sheets manager
    sheets_manager = get_sheets_manager()
    
    # Check for global credentials
    if not st.session_state.get("global_gsheets_creds"):
        st.error("🔑 Google Sheets credentials not found. Please upload your service account JSON in the sidebar.")
        st.info("💡 Use the sidebar to upload your service account JSON file for full functionality.")
        st.stop()
    
    # Load all data sources
    with st.spinner("🔄 Loading live data from all sources..."):
        all_data = load_all_business_data(sheets_manager)
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Executive Summary", "💰 Financial Overview", "👥 Customer Insights", "📈 Performance Analytics"
    ])
    
    with tab1:
        render_executive_summary(all_data)
    
    with tab2:
        render_financial_overview(all_data)
    
    with tab3:
        render_customer_insights(all_data)
    
    with tab4:
        render_performance_analytics(all_data)

def load_all_business_data(sheets_manager):
    """Load data from all business modules"""
    data_sources = {
        'customers': {
            'sheet_id': st.session_state.get('customer_sheet_url', ''),
            'worksheet_name': st.session_state.get('customer_worksheet_name', ''),
            'key': 'customers'
        },
        'pricing': {
            'sheet_id': '1WeDpcSNnfCrtx4F3bBC9osigPkzy3LXybRO6jpN7BXE',
            'worksheet_name': '',
            'key': 'pricing'
        },
        'appointments': {
            'sheet_id': '1mgToY7I10uwPrdPnjAO9gosgoaEKJCf7nv-E0-1UfVQ',
            'worksheet_name': '',
            'key': 'appointments'
        },
        'calls': {
            'sheet_id': '1LFfNwb9lRQpIosSEvV3O6zIwymUIWeG9L_k7cxw1jQs',
            'worksheet_name': '',
            'key': 'calls'
        },
        'invoices': {
            'sheet_id': st.session_state.get('invoice_sheet_url', ''),
            'worksheet_name': st.session_state.get('invoice_worksheet_name', ''),
            'key': 'invoices'
        }
    }
    
    # Load data from multiple sheets
    loaded_data = {}
    
    for source_name, config in data_sources.items():
        if config['sheet_id']:
            try:
                df = sheets_manager.get_sheet_data(
                    sheet_id=config['sheet_id'],
                    worksheet_name=config['worksheet_name'] if config['worksheet_name'] else None,
                    use_cache=True
                )
                if df is not None and not df.empty:
                    loaded_data[source_name] = df
                    st.success(f"✅ Loaded {len(df):,} records from {source_name}")
                else:
                    st.warning(f"⚠️ No data found for {source_name}")
            except Exception as e:
                st.error(f"❌ Error loading {source_name}: {str(e)}")
        else:
            # Create sample data for demo
            loaded_data[source_name] = create_sample_data(source_name)
    
    return loaded_data

def create_sample_data(data_type):
    """Create sample data for demonstration"""
    if data_type == 'customers':
        return pd.DataFrame({
            'Name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Wilson'],
            'Email': ['john@email.com', 'jane@email.com', 'bob@email.com', 'alice@email.com', 'charlie@email.com'],
            'Status': ['Active', 'Active', 'Inactive', 'Active', 'Pending'],
            'Value': [5000, 7500, 3000, 12000, 4500],
            'Date_Added': ['2024-01-15', '2024-01-20', '2024-02-01', '2024-02-15', '2024-03-01']
        })
    elif data_type == 'pricing':
        return pd.DataFrame({
            'Service': ['Consulting', 'Development', 'Support', 'Training', 'Audit'],
            'Price': [150, 200, 100, 120, 300],
            'Category': ['Professional', 'Technical', 'Support', 'Education', 'Professional'],
            'Duration': ['1 hour', '1 hour', '1 hour', '2 hours', '1 day']
        })
    elif data_type == 'appointments':
        return pd.DataFrame({
            'Name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'],
            'Status': ['Confirmed', 'Pending', 'Completed', 'Cancelled'],
            'Start Time (12hr)': ['10:00 AM', '2:00 PM', '11:00 AM', '3:00 PM'],
            'Date': ['2024-03-15', '2024-03-16', '2024-03-14', '2024-03-17']
        })
    elif data_type == 'calls':
        return pd.DataFrame({
            'customer_name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'],
            'call_success': ['Yes', 'Yes', 'No', 'Yes'],
            'call_duration_seconds': [300, 450, 120, 600],
            'sentiment_score': [0.8, 0.6, -0.2, 0.9],
            'cost': [15.50, 22.75, 6.00, 30.00]
        })
    else:
        return pd.DataFrame()

def render_executive_summary(all_data):
    """Render executive summary with key metrics"""
    st.subheader("📊 Executive Summary")
    st.markdown("**Real-time business overview across all departments**")
    
    # Key Performance Indicators
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Customer metrics
    customers_df = all_data.get('customers', pd.DataFrame())
    with col1:
        if not customers_df.empty:
            total_customers = len(customers_df)
            active_customers = len(customers_df[customers_df.get('Status', '') == 'Active']) if 'Status' in customers_df.columns else 0
            st.metric("👥 Total Customers", f"{total_customers:,}", delta=f"+{active_customers} active")
        else:
            st.metric("👥 Total Customers", "No data", delta="Configure source")
    
    # Revenue metrics
    with col2:
        total_revenue = 0
        if not customers_df.empty and 'Value' in customers_df.columns:
            total_revenue = pd.to_numeric(customers_df['Value'], errors='coerce').sum()
        
        pricing_df = all_data.get('pricing', pd.DataFrame())
        if not pricing_df.empty and 'Price' in pricing_df.columns:
            avg_service_price = pd.to_numeric(pricing_df['Price'], errors='coerce').mean()
            st.metric("💰 Total Revenue", f"${total_revenue:,.2f}", delta=f"Avg: ${avg_service_price:.0f}")
        else:
            st.metric("💰 Total Revenue", f"${total_revenue:,.2f}")
    
    # Appointments metrics
    appointments_df = all_data.get('appointments', pd.DataFrame())
    with col3:
        if not appointments_df.empty:
            total_appointments = len(appointments_df)
            confirmed_appointments = len(appointments_df[appointments_df.get('Status', '') == 'Confirmed']) if 'Status' in appointments_df.columns else 0
            st.metric("📅 Appointments", f"{total_appointments:,}", delta=f"{confirmed_appointments} confirmed")
        else:
            st.metric("📅 Appointments", "No data", delta="Configure source")
    
    # Calls metrics
    calls_df = all_data.get('calls', pd.DataFrame())
    with col4:
        if not calls_df.empty:
            total_calls = len(calls_df)
            successful_calls = len(calls_df[calls_df.get('call_success', '') == 'Yes']) if 'call_success' in calls_df.columns else 0
            success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
            st.metric("📞 Calls Made", f"{total_calls:,}", delta=f"{success_rate:.1f}% success")
        else:
            st.metric("📞 Calls Made", "No data", delta="Configure source")
    
    # Services metrics
    pricing_df = all_data.get('pricing', pd.DataFrame())
    with col5:
        if not pricing_df.empty:
            total_services = len(pricing_df)
            categories = pricing_df['Category'].nunique() if 'Category' in pricing_df.columns else 0
            st.metric("🛍️ Services", f"{total_services:,}", delta=f"{categories} categories")
        else:
            st.metric("🛍️ Services", "No data", delta="Configure source")
    
    st.divider()
    
    # Recent Activity Feed
    st.subheader("🕐 Recent Business Activity")
    
    recent_activities = []
    
    # Add recent customers
    if not customers_df.empty and 'Date_Added' in customers_df.columns:
        try:
            customers_df['Date_Added'] = pd.to_datetime(customers_df['Date_Added'], errors='coerce')
            recent_customers = customers_df.sort_values('Date_Added', ascending=False).head(3)
            for _, customer in recent_customers.iterrows():
                recent_activities.append({
                    'time': customer['Date_Added'].strftime('%Y-%m-%d') if pd.notna(customer['Date_Added']) else 'Recent',
                    'activity': f"New customer: {customer.get('Name', 'Unknown')}",
                    'type': 'customer',
                    'icon': '👥'
                })
        except:
            pass
    
    # Add recent appointments
    if not appointments_df.empty and 'Date' in appointments_df.columns:
        try:
            appointments_df['Date'] = pd.to_datetime(appointments_df['Date'], errors='coerce')
            recent_appointments = appointments_df.sort_values('Date', ascending=False).head(2)
            for _, appointment in recent_appointments.iterrows():
                recent_activities.append({
                    'time': appointment['Date'].strftime('%Y-%m-%d') if pd.notna(appointment['Date']) else 'Recent',
                    'activity': f"Appointment with {appointment.get('Name', 'Unknown')} - {appointment.get('Status', 'Unknown')}",
                    'type': 'appointment',
                    'icon': '📅'
                })
        except:
            pass
    
    # Display activities
    if recent_activities:
        for activity in recent_activities[:8]:  # Show last 8 activities
            if activity['type'] == 'customer':
                st.success(f"{activity['icon']} **{activity['time']}** - {activity['activity']}")
            elif activity['type'] == 'appointment':
                st.info(f"{activity['icon']} **{activity['time']}** - {activity['activity']}")
            else:
                st.write(f"{activity['icon']} **{activity['time']}** - {activity['activity']}")
    else:
        st.info("No recent activity data available. Configure your data sources to see live updates.")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("👥 View Customers", use_container_width=True):
            st.switch_page("pages/4_Customers.py")
    
    with col2:
        if st.button("💰 View Pricing", use_container_width=True):
            st.switch_page("pages/6_Pricing.py")
    
    with col3:
        if st.button("📅 View Appointments", use_container_width=True):
            st.switch_page("pages/5_Appointments.py")
    
    with col4:
        if st.button("📞 View Calls", use_container_width=True):
            st.switch_page("pages/9_Call_Center.py")

def render_financial_overview(all_data):
    """Render financial overview and metrics"""
    st.subheader("💰 Financial Overview")
    
    customers_df = all_data.get('customers', pd.DataFrame())
    pricing_df = all_data.get('pricing', pd.DataFrame())
    calls_df = all_data.get('calls', pd.DataFrame())
    
    # Financial metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Customer value
        if not customers_df.empty and 'Value' in customers_df.columns:
            customer_values = pd.to_numeric(customers_df['Value'], errors='coerce').dropna()
            total_customer_value = customer_values.sum()
            avg_customer_value = customer_values.mean()
            st.metric("💎 Customer Value", f"${total_customer_value:,.2f}", delta=f"Avg: ${avg_customer_value:,.2f}")
        else:
            st.metric("💎 Customer Value", "No data")
    
    with col2:
        # Service revenue potential
        if not pricing_df.empty and 'Price' in pricing_df.columns:
            service_prices = pd.to_numeric(pricing_df['Price'], errors='coerce').dropna()
            total_service_value = service_prices.sum()
            highest_service = service_prices.max()
            st.metric("🛍️ Service Portfolio", f"${total_service_value:,.2f}", delta=f"Max: ${highest_service:,.2f}")
        else:
            st.metric("🛍️ Service Portfolio", "No data")
    
    with col3:
        # Call costs
        if not calls_df.empty and 'cost' in calls_df.columns:
            call_costs = pd.to_numeric(calls_df['cost'], errors='coerce').dropna()
            total_call_costs = call_costs.sum()
            avg_call_cost = call_costs.mean()
            st.metric("📞 Call Costs", f"${total_call_costs:,.2f}", delta=f"Avg: ${avg_call_cost:.2f}")
        else:
            st.metric("📞 Call Costs", "No data")
    
    with col4:
        # ROI calculation
        revenue = 0
        costs = 0
        
        if not customers_df.empty and 'Value' in customers_df.columns:
            revenue += pd.to_numeric(customers_df['Value'], errors='coerce').sum()
        
        if not calls_df.empty and 'cost' in calls_df.columns:
            costs += pd.to_numeric(calls_df['cost'], errors='coerce').sum()
        
        roi = ((revenue - costs) / costs * 100) if costs > 0 else 0
        st.metric("📈 ROI", f"{roi:.1f}%", delta="Revenue vs Costs")
    
    # Financial charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Customer value distribution
        if not customers_df.empty and 'Value' in customers_df.columns:
            customer_values = pd.to_numeric(customers_df['Value'], errors='coerce').dropna()
            if len(customer_values) > 0:
                fig = px.histogram(
                    x=customer_values,
                    nbins=20,
                    title="Customer Value Distribution",
                    color_discrete_sequence=['#2E86AB']
                )
                fig.update_layout(xaxis_title="Customer Value ($)", yaxis_title="Count")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No customer value data available")
    
    with col2:
        # Service pricing by category
        if not pricing_df.empty and 'Price' in pricing_df.columns and 'Category' in pricing_df.columns:
            category_prices = pricing_df.groupby('Category')['Price'].agg(['mean', 'count']).reset_index()
            category_prices['mean'] = pd.to_numeric(category_prices['mean'], errors='coerce')
            
            fig = px.bar(
                category_prices,
                x='Category',
                y='mean',
                title="Average Service Price by Category",
                color='count',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(xaxis_title="Category", yaxis_title="Average Price ($)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No pricing category data available")
    
    # Financial insights
    st.subheader("💡 Financial Insights")
    
    insights = []
    
    # Customer value insights
    if not customers_df.empty and 'Value' in customers_df.columns:
        customer_values = pd.to_numeric(customers_df['Value'], errors='coerce').dropna()
        if len(customer_values) > 0:
            high_value_customers = len(customer_values[customer_values > customer_values.quantile(0.8)])
            insights.append(f"💎 You have {high_value_customers} high-value customers (top 20%)")
            
            if customer_values.std() > customer_values.mean():
                insights.append("📊 High variation in customer values - consider segmentation strategies")
    
    # Pricing insights
    if not pricing_df.empty and 'Price' in pricing_df.columns:
        service_prices = pd.to_numeric(pricing_df['Price'], errors='coerce').dropna()
        if len(service_prices) > 0:
            price_range = service_prices.max() - service_prices.min()
            insights.append(f"🛍️ Service price range: ${service_prices.min():.2f} - ${service_prices.max():.2f} (${price_range:.2f} spread)")
    
    # Call efficiency insights
    if not calls_df.empty and 'cost' in calls_df.columns and 'call_success' in calls_df.columns:
        successful_calls = calls_df[calls_df['call_success'] == 'Yes']
        if len(successful_calls) > 0:
            avg_successful_cost = pd.to_numeric(successful_calls['cost'], errors='coerce').mean()
            insights.append(f"📞 Average cost per successful call: ${avg_successful_cost:.2f}")
    
    for insight in insights:
        st.info(insight)

def render_customer_insights(all_data):
    """Render customer insights and analytics"""
    st.subheader("👥 Customer Insights")
    
    customers_df = all_data.get('customers', pd.DataFrame())
    appointments_df = all_data.get('appointments', pd.DataFrame())
    calls_df = all_data.get('calls', pd.DataFrame())
    
    if customers_df.empty:
        st.warning("⚠️ No customer data available. Configure your customer data source to see insights.")
        return
    
    # Customer metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_customers = len(customers_df)
        st.metric("👥 Total Customers", f"{total_customers:,}")
    
    with col2:
        if 'Status' in customers_df.columns:
            active_customers = len(customers_df[customers_df['Status'] == 'Active'])
            active_rate = (active_customers / total_customers * 100) if total_customers > 0 else 0
            st.metric("✅ Active Customers", f"{active_customers:,}", delta=f"{active_rate:.1f}%")
        else:
            st.metric("✅ Active Customers", "N/A")
    
    with col3:
        if 'Value' in customers_df.columns:
            customer_values = pd.to_numeric(customers_df['Value'], errors='coerce').dropna()
            avg_value = customer_values.mean() if len(customer_values) > 0 else 0
            st.metric("💰 Avg Customer Value", f"${avg_value:,.2f}")
        else:
            st.metric("💰 Avg Customer Value", "N/A")
    
    with col4:
        if 'Date_Added' in customers_df.columns:
            try:
                customers_df['Date_Added'] = pd.to_datetime(customers_df['Date_Added'], errors='coerce')
                recent_customers = len(customers_df[customers_df['Date_Added'] > datetime.now() - timedelta(days=30)])
                st.metric("🆕 New (30 days)", f"{recent_customers:,}")
            except:
                st.metric("🆕 New (30 days)", "N/A")
        else:
            st.metric("🆕 New (30 days)", "N/A")
    
    # Customer analytics charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Customer status distribution
        if 'Status' in customers_df.columns:
            status_counts = customers_df['Status'].value_counts()
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Customer Status Distribution",
                color_discrete_sequence=['#28a745', '#ffc107', '#dc3545', '#6c757d']
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No customer status data available")
    
    with col2:
        # Customer value segments
        if 'Value' in customers_df.columns:
            customer_values = pd.to_numeric(customers_df['Value'], errors='coerce').dropna()
            if len(customer_values) > 0:
                # Create value segments
                segments = []
                for value in customer_values:
                    if value >= customer_values.quantile(0.8):
                        segments.append('High Value')
                    elif value >= customer_values.quantile(0.5):
                        segments.append('Medium Value')
                    else:
                        segments.append('Low Value')
                
                segment_counts = pd.Series(segments).value_counts()
                fig = px.bar(
                    x=segment_counts.index,
                    y=segment_counts.values,
                    title="Customer Value Segments",
                    color_discrete_sequence=['#2E86AB', '#A23B72', '#F18F01']
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No customer value data available")
    
    # Customer engagement analysis
    if not appointments_df.empty or not calls_df.empty:
        st.subheader("📊 Customer Engagement")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Appointment engagement
            if not appointments_df.empty and 'Name' in appointments_df.columns:
                appointment_counts = appointments_df['Name'].value_counts().head(10)
                fig = px.bar(
                    x=appointment_counts.values,
                    y=appointment_counts.index,
                    orientation='h',
                    title="Top 10 Customers by Appointments",
                    color_discrete_sequence=['#2E86AB']
                )
                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No appointment data available")
        
        with col2:
            # Call engagement
            if not calls_df.empty and 'customer_name' in calls_df.columns:
                call_counts = calls_df['customer_name'].value_counts().head(10)
                fig = px.bar(
                    x=call_counts.values,
                    y=call_counts.index,
                    orientation='h',
                    title="Top 10 Customers by Calls",
                    color_discrete_sequence=['#A23B72']
                )
                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No call data available")

def render_performance_analytics(all_data):
    """Render performance analytics across all business areas"""
    st.subheader("📈 Performance Analytics")
    
    calls_df = all_data.get('calls', pd.DataFrame())
    appointments_df = all_data.get('appointments', pd.DataFrame())
    customers_df = all_data.get('customers', pd.DataFrame())
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Call success rate
        if not calls_df.empty and 'call_success' in calls_df.columns:
            total_calls = len(calls_df)
            successful_calls = len(calls_df[calls_df['call_success'] == 'Yes'])
            success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
            st.metric("📞 Call Success Rate", f"{success_rate:.1f}%", delta=f"{successful_calls}/{total_calls}")
        else:
            st.metric("📞 Call Success Rate", "No data")
    
    with col2:
        # Appointment confirmation rate
        if not appointments_df.empty and 'Status' in appointments_df.columns:
            total_appointments = len(appointments_df)
            confirmed_appointments = len(appointments_df[appointments_df['Status'] == 'Confirmed'])
            confirmation_rate = (confirmed_appointments / total_appointments * 100) if total_appointments > 0 else 0
            st.metric("📅 Confirmation Rate", f"{confirmation_rate:.1f}%", delta=f"{confirmed_appointments}/{total_appointments}")
        else:
            st.metric("📅 Confirmation Rate", "No data")
    
    with col3:
        # Customer retention (active vs total)
        if not customers_df.empty and 'Status' in customers_df.columns:
            total_customers = len(customers_df)
            active_customers = len(customers_df[customers_df['Status'] == 'Active'])
            retention_rate = (active_customers / total_customers * 100) if total_customers > 0 else 0
            st.metric("👥 Customer Retention", f"{retention_rate:.1f}%", delta=f"{active_customers}/{total_customers}")
        else:
            st.metric("👥 Customer Retention", "No data")
    
    with col4:
        # Average sentiment score
        if not calls_df.empty and 'sentiment_score' in calls_df.columns:
            sentiment_scores = pd.to_numeric(calls_df['sentiment_score'], errors='coerce').dropna()
            avg_sentiment = sentiment_scores.mean() if len(sentiment_scores) > 0 else 0
            sentiment_trend = "Positive" if avg_sentiment > 0.5 else "Neutral" if avg_sentiment > 0 else "Negative"
            st.metric("😊 Avg Sentiment", f"{avg_sentiment:.2f}", delta=sentiment_trend)
        else:
            st.metric("😊 Avg Sentiment", "No data")
    
    # Performance trends
    col1, col2 = st.columns(2)
    
    with col1:
        # Call performance over time
        if not calls_df.empty and 'call_duration_seconds' in calls_df.columns:
            durations = pd.to_numeric(calls_df['call_duration_seconds'], errors='coerce').dropna()
            if len(durations) > 0:
                # Create duration bins
                duration_bins = ['0-2 min', '2-5 min', '5-10 min', '10+ min']
                duration_categories = []
                
                for duration in durations:
                    if duration <= 120:
                        duration_categories.append('0-2 min')
                    elif duration <= 300:
                        duration_categories.append('2-5 min')
                    elif duration <= 600:
                        duration_categories.append('5-10 min')
                    else:
                        duration_categories.append('10+ min')
                
                duration_counts = pd.Series(duration_categories).value_counts()
                fig = px.bar(
                    x=duration_counts.index,
                    y=duration_counts.values,
                    title="Call Duration Distribution",
                    color_discrete_sequence=['#2E86AB']
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No call duration data available")
    
    with col2:
        # Sentiment analysis
        if not calls_df.empty and 'sentiment_score' in calls_df.columns:
            sentiment_scores = pd.to_numeric(calls_df['sentiment_score'], errors='coerce').dropna()
            if len(sentiment_scores) > 0:
                fig = px.histogram(
                    x=sentiment_scores,
                    nbins=20,
                    title="Customer Sentiment Distribution",
                    color_discrete_sequence=['#A23B72']
                )
                fig.update_layout(xaxis_title="Sentiment Score", yaxis_title="Count")
                fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Neutral")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sentiment data available")
    
    # Data Scanner Integration
    st.subheader("🔍 Advanced Data Analysis")
    
    with st.expander("📊 Launch Comprehensive Data Scanner", expanded=False):
        st.markdown("Analyze all your business data with advanced insights and visualizations")
        
        # Data source selector
        available_data = {k: v for k, v in all_data.items() if not v.empty}
        
        if available_data:
            selected_source = st.selectbox(
                "Select data source to analyze",
                list(available_data.keys()),
                format_func=lambda x: x.title()
            )
            
            if st.button("🚀 Launch Scanner", type="primary", use_container_width=True):
                st.session_state.scanner_data = available_data[selected_source]
                st.session_state.show_scanner = True
        else:
            st.warning("No data sources available for analysis")
    
    # Show scanner if requested
    if st.session_state.get('show_scanner', False) and 'scanner_data' in st.session_state:
        st.markdown("---")
        st.subheader(f"🔍 Data Scanner - {selected_source.title()}")
        
        scanner_ui = DataScannerUI(st.session_state.scanner_data)
        scanner_ui.render_main_interface()
        
        if st.button("❌ Close Scanner"):
            st.session_state.show_scanner = False
            if 'scanner_data' in st.session_state:
                del st.session_state.scanner_data
            st.rerun()
    
    # System health indicators
    st.subheader("🔧 System Health")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Data freshness
        cache_info = sheets_manager.get_cache_info()
        st.metric("📦 Cached Sheets", cache_info['cached_sheets'])
        
        if cache_info['oldest_cache']:
            oldest_time = datetime.fromtimestamp(cache_info['oldest_cache'])
            age_minutes = (datetime.now() - oldest_time).total_seconds() / 60
            st.metric("⏰ Cache Age", f"{age_minutes:.0f} min")
        else:
            st.metric("⏰ Cache Age", "No cache")
    
    with col2:
        # Data quality score
        total_records = sum(len(df) for df in all_data.values() if not df.empty)
        data_sources_count = len([df for df in all_data.values() if not df.empty])
        
        st.metric("📊 Total Records", f"{total_records:,}")
        st.metric("🔗 Data Sources", f"{data_sources_count}/5")
    
    with col3:
        # Connection status
        if st.session_state.get("global_gsheets_creds"):
            st.success("✅ Google Sheets Connected")
            client_email = st.session_state.global_gsheets_creds.get('client_email', 'Unknown')
            st.info(f"📧 {client_email[:25]}...")
        else:
            st.error("❌ No credentials")
        
        if st.button("🔄 Refresh All Data", use_container_width=True):
            sheets_manager.clear_cache()
            st.rerun()

if __name__ == "__main__":
    main()
