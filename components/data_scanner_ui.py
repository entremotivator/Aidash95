import streamlit as st
import pandas as pd
from utils.data_scanner import DataScanner, VisualizationEngine
from typing import Optional
import plotly.express as px
import time

class DataScannerUI:
    """User interface for the data scanner functionality"""
    
    def __init__(self, df: Optional[pd.DataFrame] = None):
        self.df = df
        self.scanner = DataScanner(df) if df is not None else None
        self.viz_engine = VisualizationEngine(df) if df is not None else None
        self.sheets_manager = None  # Placeholder for sheets_manager
    
    def render_main_interface(self):
        """Render the main data scanner interface"""
        st.title("🔍 Advanced Data Scanner & Analyzer")
        st.markdown("Comprehensive analysis of your Google Sheets data with AI-powered insights")
        
        # Check authentication
        if not st.session_state.get("global_gsheets_creds"):
            st.error("🔑 Google Sheets credentials not found. Please upload your service account JSON in the sidebar.")
            return
        
        # Data source selection
        self._render_data_source_selector()
        
        # Main analysis interface
        if self.df is not None and not self.df.empty:
            self._render_analysis_interface()
    
    def _render_data_source_selector(self):
        """Render data source selection interface"""
        st.subheader("📊 Data Source Selection")
        
        with st.expander("🔧 Configure Data Source", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Sheet URL/ID input
                sheet_input = st.text_input(
                    "Google Sheet URL or ID",
                    placeholder="https://docs.google.com/spreadsheets/d/your-sheet-id/edit",
                    help="Enter the full URL or just the sheet ID"
                )
                
                # Worksheet selection
                worksheet_name = st.text_input(
                    "Worksheet Name (optional)",
                    placeholder="Leave empty for first worksheet",
                    help="Specify worksheet name or leave empty for first sheet"
                )
            
            with col2:
                # Load data button
                if st.button("🔄 Load Data", type="primary", use_container_width=True):
                    if sheet_input:
                        self._load_data(sheet_input, worksheet_name)
                    else:
                        st.error("Please enter a Google Sheet URL or ID")
                
                # Cache management
                if st.button("🗑️ Clear Cache", use_container_width=True):
                    if self.sheets_manager:
                        self.sheets_manager.clear_cache()
                        st.success("Cache cleared!")
                    else:
                        st.error("Sheets manager not initialized")
        
        # Display current data info
        if self.df is not None and not self.df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📊 Rows", f"{len(self.df):,}")
            with col2:
                st.metric("📋 Columns", len(self.df.columns))
            with col3:
                st.metric("💾 Size", f"{self.df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
            with col4:
                st.metric("🕐 Last Updated", st.session_state.get('data_load_time', 'Unknown'))
    
    def _load_data(self, sheet_input: str, worksheet_name: str = None):
        """Load data from Google Sheets"""
        try:
            with st.spinner("Loading data from Google Sheets..."):
                # Extract sheet ID if URL provided
                if 'docs.google.com' in sheet_input:
                    sheet_id = sheet_input.split('/')[-2]
                else:
                    sheet_id = sheet_input
                
                # Initialize sheets manager if not already done
                if not self.sheets_manager:
                    self.sheets_manager = get_sheets_manager()
                
                # Load data
                df = self.sheets_manager.get_sheet_data(
                    sheet_id=sheet_id,
                    worksheet_name=worksheet_name if worksheet_name else None,
                    use_cache=True
                )
                
                if df is not None and not df.empty:
                    self.df = df
                    st.session_state.data_load_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.sheet_info = self.sheets_manager.get_sheet_info(sheet_id)
                    
                    # Initialize scanner and viz engine
                    self.scanner = DataScanner(df)
                    self.viz_engine = VisualizationEngine(df)
                    
                    st.success(f"✅ Successfully loaded {len(df):,} rows and {len(df.columns)} columns")
                    st.rerun()
                else:
                    st.error("❌ Failed to load data or sheet is empty")
                    
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
    
    def _render_analysis_interface(self):
        """Render the main analysis interface"""
        if self.df is None or self.df.empty:
            st.warning("⚠️ No data available for analysis")
            return
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview", "🔍 Column Analysis", "📈 Visualizations", "💡 Insights"
        ])
        
        with tab1:
            self._render_overview_tab()
        
        with tab2:
            self._render_column_analysis_tab()
        
        with tab3:
            self._render_visualizations_tab()
        
        with tab4:
            self._render_insights_tab()
    
    def _render_overview_tab(self):
        """Render the overview tab"""
        if not self.scanner:
            return
        
        overview = self.scanner.scan_overview()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Rows", f"{overview['shape'][0]:,}")
        
        with col2:
            st.metric("📋 Columns", f"{overview['shape'][1]:,}")
        
        with col3:
            st.metric("🎯 Data Quality", f"{overview['data_quality_score']:.1f}%")
        
        with col4:
            st.metric("💾 Memory Usage", f"{overview['memory_usage'] / 1024:.1f} KB")
        
        # Data types breakdown
        st.subheader("📊 Data Types")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Data types chart
            if self.viz_engine:
                charts = self.viz_engine.create_overview_charts()
                if "data_types" in charts:
                    st.plotly_chart(charts["data_types"], use_container_width=True)
        
        with col2:
            # Column information
            st.write("**Column Details:**")
            for col, dtype in overview['dtypes'].items():
                null_count = overview['null_counts'][col]
                null_pct = (null_count / overview['shape'][0] * 100) if overview['shape'][0] > 0 else 0
                st.write(f"• **{col}** ({dtype}) - {null_count} nulls ({null_pct:.1f}%)")
        
        # Missing data visualization
        if overview['null_counts'] and sum(overview['null_counts'].values()) > 0:
            st.subheader("❌ Missing Data Analysis")
            
            if self.viz_engine:
                charts = self.viz_engine.create_overview_charts()
                if "missing_data" in charts:
                    st.plotly_chart(charts["missing_data"], use_container_width=True)
        
        # Data sample
        st.subheader("👀 Data Sample")
        st.dataframe(self.df.head(10), use_container_width=True)
    
    def _render_column_analysis_tab(self):
        """Render the column analysis tab"""
        if not self.scanner:
            return
        
        st.subheader("🔍 Detailed Column Analysis")
        
        # Column selector
        selected_column = st.selectbox(
            "Select column to analyze",
            self.df.columns.tolist(),
            key="column_analysis_selector"
        )
        
        if selected_column:
            analysis = self.scanner.analyze_column(selected_column)
            
            # Basic info
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📊 Count", f"{analysis['count']:,}")
            
            with col2:
                st.metric("❌ Null Count", f"{analysis['null_count']:,}")
            
            with col3:
                st.metric("🎯 Unique Values", f"{analysis['unique_count']:,}")
            
            with col4:
                st.metric("📈 Uniqueness", f"{analysis['unique_percentage']:.1f}%")
            
            # Type-specific analysis
            if 'mean' in analysis:  # Numeric column
                st.subheader("📊 Statistical Summary")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Descriptive Statistics:**")
                    st.write(f"• **Mean:** {analysis['mean']:.2f}")
                    st.write(f"• **Median:** {analysis['median']:.2f}")
                    st.write(f"• **Std Dev:** {analysis['std']:.2f}")
                    st.write(f"• **Min:** {analysis['min']:.2f}")
                    st.write(f"• **Max:** {analysis['max']:.2f}")
                
                with col2:
                    st.write("**Quartiles:**")
                    st.write(f"• **Q1 (25%):** {analysis['q25']:.2f}")
                    st.write(f"• **Q3 (75%):** {analysis['q75']:.2f}")
                    st.write(f"• **IQR:** {analysis['q75'] - analysis['q25']:.2f}")
                
                # Outliers
                if analysis['outliers']['count'] > 0:
                    st.subheader("⚠️ Outliers Detected")
                    st.write(f"**Count:** {analysis['outliers']['count']} ({analysis['outliers']['percentage']:.1f}%)")
                    st.write(f"**Range:** {analysis['outliers']['lower_bound']:.2f} to {analysis['outliers']['upper_bound']:.2f}")
            
            elif 'top_values' in analysis:  # Categorical column
                st.subheader("📊 Value Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Top Values:**")
                    for value, count in list(analysis['top_values'].items())[:10]:
                        percentage = (count / analysis['count'] * 100) if analysis['count'] > 0 else 0
                        st.write(f"• **{value}:** {count} ({percentage:.1f}%)")
                
                with col2:
                    st.write("**Pattern Analysis:**")
                    st.write(f"• **Avg Length:** {analysis['avg_length']:.1f} characters")
                    st.write(f"• **Contains Emails:** {analysis['contains_emails']}")
                    st.write(f"• **Contains Phones:** {analysis['contains_phones']}")
                    st.write(f"• **Contains URLs:** {analysis['contains_urls']}")
            
            elif 'min_date' in analysis:  # DateTime column
                st.subheader("📅 Date Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Date Range:**")
                    st.write(f"• **From:** {analysis['min_date']}")
                    st.write(f"• **To:** {analysis['max_date']}")
                    st.write(f"• **Span:** {analysis['date_range_days']} days")
                
                with col2:
                    st.write("**Common Patterns:**")
                    if analysis['most_common_year']:
                        st.write(f"• **Most Common Year:** {analysis['most_common_year']}")
                    if analysis['most_common_month']:
                        st.write(f"• **Most Common Month:** {analysis['most_common_month']}")
            
            # Visualization
            if self.viz_engine:
                chart = self.viz_engine.create_column_analysis_chart(selected_column)
                if chart:
                    st.subheader("📈 Visualization")
                    st.plotly_chart(chart, use_container_width=True)
    
    def _render_visualizations_tab(self):
        """Render the visualizations tab"""
        if not self.viz_engine:
            return
        
        st.subheader("📈 Data Visualizations")
        
        # Visualization type selector
        viz_type = st.selectbox(
            "Select visualization type",
            ["Overview Charts", "Correlation Analysis", "Column Comparison", "Custom Analysis"],
            key="viz_type_selector"
        )
        
        if viz_type == "Overview Charts":
            charts = self.viz_engine.create_overview_charts()
            
            if "numeric_distributions" in charts:
                st.subheader("📊 Numeric Distributions")
                for col, chart in charts["numeric_distributions"].items():
                    st.plotly_chart(chart, use_container_width=True)
        
        elif viz_type == "Correlation Analysis":
            st.subheader("🔗 Correlation Analysis")
            
            numeric_cols = self.df.select_dtypes(include=['number']).columns
            if len(numeric_cols) >= 2:
                corr_chart = self.viz_engine.create_correlation_heatmap()
                if corr_chart:
                    st.plotly_chart(corr_chart, use_container_width=True)
                
                # Correlation insights
                correlations = self.scanner.find_correlations()
                if "strong_correlations" in correlations and correlations["strong_correlations"]:
                    st.subheader("💡 Strong Correlations")
                    for corr in correlations["strong_correlations"]:
                        st.write(f"• **{corr['column1']}** ↔ **{corr['column2']}**: {corr['correlation']:.3f} ({corr['strength']})")
            else:
                st.info("Need at least 2 numeric columns for correlation analysis")
        
        elif viz_type == "Column Comparison":
            st.subheader("⚖️ Column Comparison")
            
            col1, col2 = st.columns(2)
            
            with col1:
                x_column = st.selectbox("X-axis column", self.df.columns.tolist(), key="x_col_selector")
            
            with col2:
                y_column = st.selectbox("Y-axis column", self.df.columns.tolist(), key="y_col_selector")
            
            if x_column and y_column and x_column != y_column:
                comparison_chart = self.viz_engine.create_comparison_charts(x_column, y_column)
                if comparison_chart:
                    st.plotly_chart(comparison_chart, use_container_width=True)
        
        elif viz_type == "Custom Analysis":
            st.subheader("🎨 Custom Analysis")
            
            # Chart type selector
            chart_type = st.selectbox(
                "Select chart type",
                ["Histogram", "Box Plot", "Scatter Plot", "Bar Chart", "Line Chart"],
                key="custom_chart_type"
            )
            
            if chart_type == "Histogram":
                numeric_cols = self.df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    selected_col = st.selectbox("Select column", numeric_cols, key="hist_col")
                    bins = st.slider("Number of bins", 5, 50, 20)
                    
                    fig = px.histogram(self.df, x=selected_col, nbins=bins, title=f"Histogram of {selected_col}")
                    st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Box Plot":
                numeric_cols = self.df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    selected_col = st.selectbox("Select column", numeric_cols, key="box_col")
                    
                    fig = px.box(self.df, y=selected_col, title=f"Box Plot of {selected_col}")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Add more custom chart types as needed
    
    def _render_insights_tab(self):
        """Render the insights tab"""
        if not self.scanner:
            return
        
        st.subheader("💡 Data Insights & Recommendations")
        
        # Generate insights
        insights = self.scanner.generate_insights()
        
        if insights:
            st.write("**Automated Insights:**")
            for i, insight in enumerate(insights, 1):
                st.write(f"{i}. {insight}")
        else:
            st.info("No specific insights generated for this dataset.")
        
        # Pattern analysis
        st.subheader("🔍 Pattern Analysis")
        patterns = self.scanner.detect_patterns()
        
        # Missing data patterns
        if patterns["missing_data_patterns"]["total_missing_cells"] > 0:
            st.write("**Missing Data Patterns:**")
            missing_info = patterns["missing_data_patterns"]
            st.write(f"• Total missing cells: {missing_info['total_missing_cells']:,} ({missing_info['missing_percentage']:.1f}%)")
            st.write(f"• Rows with missing data: {missing_info['rows_with_missing']:,}")
            
            if missing_info["columns_with_missing"]:
                st.write("• Columns with most missing data:")
                for col, count in list(missing_info["columns_with_missing"].items())[:5]:
                    st.write(f"  - {col}: {count} missing values")
        
        # Duplicate patterns
        if patterns["duplicate_patterns"]["duplicate_rows"] > 0:
            st.write("**Duplicate Data Patterns:**")
            dup_info = patterns["duplicate_patterns"]
            st.write(f"• Duplicate rows: {dup_info['duplicate_rows']:,} ({dup_info['duplicate_percentage']:.1f}%)")
            
            if dup_info["potential_id_columns"]:
                st.write(f"• Potential ID columns: {', '.join(dup_info['potential_id_columns'])}")
        
        # Data quality recommendations
        st.subheader("🎯 Recommendations")
        
        recommendations = []
        
        overview = self.scanner.scan_overview()
        
        if overview["data_quality_score"] < 90:
            recommendations.append("🔧 **Data Cleaning**: Address missing values and duplicates to improve data quality")
        
        if overview["duplicate_rows"] > 0:
            recommendations.append("🔄 **Deduplication**: Remove duplicate rows to ensure data integrity")
        
        if len(overview["numeric_columns"]) > 1:
            recommendations.append("📊 **Correlation Analysis**: Explore relationships between numeric variables")
        
        if len(overview["categorical_columns"]) > 0:
            recommendations.append("🏷️ **Category Analysis**: Analyze categorical distributions for business insights")
        
        if len(overview["datetime_columns"]) > 0:
            recommendations.append("📅 **Time Series Analysis**: Explore temporal patterns in your data")
        
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")
        
        # Export options
        st.subheader("📤 Export Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export Summary Report", use_container_width=True):
                # Create summary report
                report = self._create_summary_report()
                st.download_button(
                    "💾 Download Report",
                    report,
                    f"data_analysis_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "text/plain"
                )
        
        with col2:
            if st.button("📈 Export Insights", use_container_width=True):
                insights_text = "\n".join([f"{i}. {insight}" for i, insight in enumerate(insights, 1)])
                st.download_button(
                    "💾 Download Insights",
                    insights_text,
                    f"data_insights_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "text/plain"
                )
    
    def _create_summary_report(self) -> str:
        """Create a comprehensive summary report"""
        if not self.scanner:
            return "No data available for report generation."
        
        overview = self.scanner.scan_overview()
        insights = self.scanner.generate_insights()
        
        report = f"""
DATA ANALYSIS SUMMARY REPORT
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

DATASET OVERVIEW
================
• Dimensions: {overview['shape'][0]:,} rows × {overview['shape'][1]:,} columns
• Data Quality Score: {overview['data_quality_score']:.1f}%
• Memory Usage: {overview['memory_usage'] / 1024:.1f} KB
• Duplicate Rows: {overview['duplicate_rows']:,}

COLUMN BREAKDOWN
================
• Numeric Columns: {len(overview['numeric_columns'])}
• Categorical Columns: {len(overview['categorical_columns'])}
• DateTime Columns: {len(overview['datetime_columns'])}

MISSING DATA
============
• Total Missing Cells: {sum(overview['null_counts'].values()):,}
• Columns with Missing Data:
"""
        
        for col, count in overview['null_counts'].items():
            if count > 0:
                pct = (count / overview['shape'][0] * 100) if overview['shape'][0] > 0 else 0
                report += f"  - {col}: {count} ({pct:.1f}%)\n"
        
        report += f"""
KEY INSIGHTS
============
"""
        
        for i, insight in enumerate(insights, 1):
            report += f"{i}. {insight}\n"
        
        return report
