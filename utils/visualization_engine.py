import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import seaborn as sns
import matplotlib.pyplot as plt

class VisualizationEngine:
    """Advanced visualization engine for data analysis"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.color_palette = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#28a745', '#ffc107', '#6f42c1', '#fd7e14']
    
    def create_overview_charts(self) -> Dict[str, go.Figure]:
        """Create overview charts for the dataset"""
        charts = {}
        
        # Data types distribution
        dtype_counts = self.df.dtypes.value_counts()
        charts['data_types'] = px.pie(
            values=dtype_counts.values,
            names=dtype_counts.index,
            title="Data Types Distribution",
            color_discrete_sequence=self.color_palette
        )
        
        # Missing data heatmap
        if self.df.isnull().sum().sum() > 0:
            missing_data = self.df.isnull().sum().sort_values(ascending=False)
            charts['missing_data'] = px.bar(
                x=missing_data.values,
                y=missing_data.index,
                orientation='h',
                title="Missing Data by Column",
                color_discrete_sequence=[self.color_palette[0]]
            )
            charts['missing_data'].update_layout(yaxis={'categoryorder': 'total ascending'})
        
        # Dataset size metrics
        metrics_data = {
            'Metric': ['Total Rows', 'Total Columns', 'Non-null Values', 'Unique Values'],
            'Count': [
                len(self.df),
                len(self.df.columns),
                self.df.count().sum(),
                sum(self.df.nunique())
            ]
        }
        charts['metrics'] = px.bar(
            x=metrics_data['Metric'],
            y=metrics_data['Count'],
            title="Dataset Metrics",
            color_discrete_sequence=[self.color_palette[1]]
        )
        
        return charts
    
    def create_column_chart(self, column_name: str, chart_type: str = 'auto') -> Optional[go.Figure]:
        """Create appropriate chart for a specific column"""
        if column_name not in self.df.columns:
            return None
        
        series = self.df[column_name].dropna()
        
        if len(series) == 0:
            return None
        
        # Auto-detect chart type if not specified
        if chart_type == 'auto':
            if pd.api.types.is_numeric_dtype(series):
                chart_type = 'histogram'
            elif series.nunique() <= 20:
                chart_type = 'bar'
            else:
                chart_type = 'histogram'
        
        try:
            if chart_type == 'histogram':
                return self._create_histogram(series, column_name)
            elif chart_type == 'bar':
                return self._create_bar_chart(series, column_name)
            elif chart_type == 'box':
                return self._create_box_plot(series, column_name)
            elif chart_type == 'line':
                return self._create_line_chart(series, column_name)
            elif chart_type == 'scatter':
                return self._create_scatter_plot(series, column_name)
            else:
                return self._create_histogram(series, column_name)
        except Exception as e:
            st.error(f"Error creating chart: {str(e)}")
            return None
    
    def _create_histogram(self, series: pd.Series, column_name: str) -> go.Figure:
        """Create histogram for numeric data"""
        if pd.api.types.is_numeric_dtype(series):
            fig = px.histogram(
                x=series,
                nbins=min(50, max(10, int(np.sqrt(len(series))))),
                title=f"Distribution of {column_name}",
                color_discrete_sequence=[self.color_palette[0]]
            )
        else:
            # For non-numeric data, create value counts
            value_counts = series.value_counts().head(20)
            fig = px.bar(
                x=value_counts.index,
                y=value_counts.values,
                title=f"Top Values in {column_name}",
                color_discrete_sequence=[self.color_palette[0]]
            )
        
        fig.update_layout(
            xaxis_title=column_name,
            yaxis_title="Count",
            showlegend=False
        )
        
        return fig
    
    def _create_bar_chart(self, series: pd.Series, column_name: str) -> go.Figure:
        """Create bar chart for categorical data"""
        value_counts = series.value_counts().head(20)
        
        fig = px.bar(
            x=value_counts.index,
            y=value_counts.values,
            title=f"Value Counts for {column_name}",
            color_discrete_sequence=[self.color_palette[1]]
        )
        
        fig.update_layout(
            xaxis_title=column_name,
            yaxis_title="Count",
            showlegend=False
        )
        
        return fig
    
    def _create_box_plot(self, series: pd.Series, column_name: str) -> go.Figure:
        """Create box plot for numeric data"""
        fig = px.box(
            y=series,
            title=f"Box Plot of {column_name}",
            color_discrete_sequence=[self.color_palette[2]]
        )
        
        fig.update_layout(
            yaxis_title=column_name,
            showlegend=False
        )
        
        return fig
    
    def _create_line_chart(self, series: pd.Series, column_name: str) -> go.Figure:
        """Create line chart (useful for time series)"""
        fig = px.line(
            x=series.index,
            y=series.values,
            title=f"Line Chart of {column_name}",
            color_discrete_sequence=[self.color_palette[3]]
        )
        
        fig.update_layout(
            xaxis_title="Index",
            yaxis_title=column_name,
            showlegend=False
        )
        
        return fig
    
    def _create_scatter_plot(self, series: pd.Series, column_name: str) -> go.Figure:
        """Create scatter plot against index"""
        fig = px.scatter(
            x=series.index,
            y=series.values,
            title=f"Scatter Plot of {column_name}",
            color_discrete_sequence=[self.color_palette[4]]
        )
        
        fig.update_layout(
            xaxis_title="Index",
            yaxis_title=column_name,
            showlegend=False
        )
        
        return fig
    
    def create_correlation_heatmap(self, correlation_matrix: pd.DataFrame) -> go.Figure:
        """Create correlation heatmap"""
        fig = px.imshow(
            correlation_matrix,
            text_auto=True,
            aspect="auto",
            title="Correlation Matrix",
            color_continuous_scale="RdBu_r"
        )
        
        fig.update_layout(
            width=600,
            height=600
        )
        
        return fig
    
    def create_comparison_chart(self, column1: str, column2: str, chart_type: str = 'scatter') -> Optional[go.Figure]:
        """Create comparison chart between two columns"""
        if column1 not in self.df.columns or column2 not in self.df.columns:
            return None
        
        df_clean = self.df[[column1, column2]].dropna()
        
        if len(df_clean) == 0:
            return None
        
        try:
            if chart_type == 'scatter':
                fig = px.scatter(
                    df_clean,
                    x=column1,
                    y=column2,
                    title=f"{column1} vs {column2}",
                    color_discrete_sequence=[self.color_palette[0]]
                )
            elif chart_type == 'line':
                fig = px.line(
                    df_clean,
                    x=column1,
                    y=column2,
                    title=f"{column1} vs {column2}",
                    color_discrete_sequence=[self.color_palette[1]]
                )
            else:
                fig = px.scatter(
                    df_clean,
                    x=column1,
                    y=column2,
                    title=f"{column1} vs {column2}",
                    color_discrete_sequence=[self.color_palette[0]]
                )
            
            return fig
            
        except Exception as e:
            st.error(f"Error creating comparison chart: {str(e)}")
            return None
    
    def create_time_series_chart(self, date_column: str, value_column: str) -> Optional[go.Figure]:
        """Create time series chart"""
        if date_column not in self.df.columns or value_column not in self.df.columns:
            return None
        
        try:
            df_ts = self.df[[date_column, value_column]].copy()
            df_ts[date_column] = pd.to_datetime(df_ts[date_column], errors='coerce')
            df_ts = df_ts.dropna().sort_values(date_column)
            
            if len(df_ts) == 0:
                return None
            
            fig = px.line(
                df_ts,
                x=date_column,
                y=value_column,
                title=f"{value_column} over Time",
                color_discrete_sequence=[self.color_palette[2]]
            )
            
            fig.update_layout(
                xaxis_title=date_column,
                yaxis_title=value_column
            )
            
            return fig
            
        except Exception as e:
            st.error(f"Error creating time series chart: {str(e)}")
            return None
    
    def create_multi_column_chart(self, columns: List[str], chart_type: str = 'line') -> Optional[go.Figure]:
        """Create chart with multiple columns"""
        valid_columns = [col for col in columns if col in self.df.columns]
        
        if len(valid_columns) < 2:
            return None
        
        try:
            df_subset = self.df[valid_columns].select_dtypes(include=[np.number])
            
            if df_subset.empty:
                return None
            
            if chart_type == 'line':
                fig = go.Figure()
                for i, col in enumerate(df_subset.columns):
                    fig.add_trace(go.Scatter(
                        x=df_subset.index,
                        y=df_subset[col],
                        mode='lines',
                        name=col,
                        line=dict(color=self.color_palette[i % len(self.color_palette)])
                    ))
                
                fig.update_layout(
                    title="Multi-Column Comparison",
                    xaxis_title="Index",
                    yaxis_title="Values"
                )
            
            elif chart_type == 'bar':
                # Create grouped bar chart with means
                means = df_subset.mean()
                fig = px.bar(
                    x=means.index,
                    y=means.values,
                    title="Column Means Comparison",
                    color_discrete_sequence=self.color_palette
                )
            
            else:
                # Default to line chart
                return self.create_multi_column_chart(columns, 'line')
            
            return fig
            
        except Exception as e:
            st.error(f"Error creating multi-column chart: {str(e)}")
            return None
    
    def create_quality_dashboard(self, quality_scores: Dict[str, float]) -> go.Figure:
        """Create data quality dashboard"""
        columns = list(quality_scores.keys())
        scores = list(quality_scores.values())
        
        # Color code based on quality score
        colors = []
        for score in scores:
            if score >= 80:
                colors.append('#28a745')  # Green
            elif score >= 60:
                colors.append('#ffc107')  # Yellow
            else:
                colors.append('#dc3545')  # Red
        
        fig = px.bar(
            x=columns,
            y=scores,
            title="Data Quality Scores by Column",
            color=scores,
            color_continuous_scale=['red', 'yellow', 'green']
        )
        
        fig.update_layout(
            xaxis_title="Columns",
            yaxis_title="Quality Score",
            yaxis=dict(range=[0, 100])
        )
        
        # Add quality threshold lines
        fig.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="Good Quality")
        fig.add_hline(y=60, line_dash="dash", line_color="orange", annotation_text="Fair Quality")
        
        return fig
    
    def create_overview_dashboard(self) -> Dict[str, go.Figure]:
        """Create comprehensive overview dashboard"""
        figures = {}
        
        # Data shape overview
        figures['data_shape'] = self._create_data_shape_chart()
        
        # Correlation heatmap (for numeric columns)
        numeric_df = self.df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            corr_matrix = numeric_df.corr()
            figures['correlation'] = self.create_correlation_heatmap(corr_matrix)
        
        return figures
    
    def _create_data_shape_chart(self) -> go.Figure:
        """Create data shape visualization"""
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=['Rows', 'Columns'],
            y=[self.df.shape[0], self.df.shape[1]],
            marker_color=['#2E86AB', '#A23B72'],
            text=[f'{self.df.shape[0]:,}', f'{self.df.shape[1]:,}'],
            textposition='auto'
        ))
        
        fig.update_layout(
            title="Dataset Shape",
            xaxis_title="Dimension",
            yaxis_title="Count",
            showlegend=False,
            height=400
        )
        
        return fig
    
    def create_column_analysis_charts(self, column: str) -> Dict[str, go.Figure]:
        """Create detailed analysis charts for a specific column"""
        figures = {}
        series = self.df[column].dropna()
        
        if pd.api.types.is_numeric_dtype(series):
            figures.update(self._create_numeric_column_charts(column, series))
        elif pd.api.types.is_datetime64_any_dtype(series):
            figures.update(self._create_datetime_column_charts(column, series))
        else:
            figures.update(self._create_categorical_column_charts(column, series))
        
        return figures
    
    def _create_numeric_column_charts(self, column: str, series: pd.Series) -> Dict[str, go.Figure]:
        """Create charts for numeric columns"""
        figures = {}
        
        # Distribution histogram
        fig_hist = self._create_histogram(series, column)
        figures['distribution'] = fig_hist
        
        # Box plot
        fig_box = self._create_box_plot(series, column)
        figures['boxplot'] = fig_box
        
        # Time series if index is datetime
        if pd.api.types.is_datetime64_any_dtype(self.df.index):
            fig_ts = self._create_line_chart(series, column)
            figures['timeseries'] = fig_ts
        
        return figures
    
    def _create_datetime_column_charts(self, column: str, series: pd.Series) -> Dict[str, go.Figure]:
        """Create charts for datetime columns"""
        figures = {}
        
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(series):
            series = pd.to_datetime(series, errors='coerce').dropna()
        
        # Time distribution
        fig_time = self._create_histogram(series, column)
        figures['time_distribution'] = fig_time
        
        # Day of week analysis
        dow_counts = series.dt.day_name().value_counts()
        fig_dow = go.Figure(data=[go.Bar(
            x=dow_counts.index,
            y=dow_counts.values,
            marker_color='#A23B72'
        )])
        fig_dow.update_layout(
            title=f"Day of Week Distribution - {column}",
            xaxis_title="Day of Week",
            yaxis_title="Count",
            height=400
        )
        figures['day_of_week'] = fig_dow
        
        return figures
    
    def _create_categorical_column_charts(self, column: str, series: pd.Series) -> Dict[str, go.Figure]:
        """Create charts for categorical columns"""
        figures = {}
        
        # Value counts
        value_counts = series.value_counts().head(20)  # Top 20 values
        
        fig_bar = go.Figure(data=[go.Bar(
            x=value_counts.values,
            y=value_counts.index,
            orientation='h',
            marker_color='#2E86AB'
        )])
        fig_bar.update_layout(
            title=f"Top Values in {column}",
            xaxis_title="Count",
            yaxis_title=column,
            height=max(400, len(value_counts) * 25)
        )
        figures['value_counts'] = fig_bar
        
        # Pie chart for top categories
        if len(value_counts) <= 10:
            fig_pie = go.Figure(data=[go.Pie(
                labels=value_counts.index,
                values=value_counts.values,
                hole=0.3,
                marker_colors=self.color_palette[:len(value_counts)]
            )])
            fig_pie.update_layout(
                title=f"Distribution of {column}",
                height=400
            )
            figures['pie_chart'] = fig_pie
        
        return figures
    
    def create_advanced_analytics_charts(self) -> Dict[str, go.Figure]:
        """Create advanced analytics visualizations"""
        figures = {}
        
        # Data quality overview
        figures['data_quality'] = self._create_data_quality_chart()
        
        # Column uniqueness
        figures['uniqueness'] = self._create_uniqueness_chart()
        
        # Memory usage
        figures['memory_usage'] = self._create_memory_usage_chart()
        
        return figures
    
    def _create_data_quality_chart(self) -> go.Figure:
        """Create data quality overview chart"""
        quality_scores = []
        columns = []
        
        for col in self.df.columns:
            # Calculate quality score based on completeness and consistency
            completeness = (1 - self.df[col].isnull().sum() / len(self.df)) * 100
            
            # Simple consistency check
            if pd.api.types.is_numeric_dtype(self.df[col]):
                consistency = 100  # Numeric columns are consistent
            else:
                # Check for mixed types or unusual patterns
                non_null = self.df[col].dropna()
                if len(non_null) > 0:
                    str_lengths = non_null.astype(str).str.len()
                    consistency = max(0, 100 - (str_lengths.std() / str_lengths.mean() * 100))
                else:
                    consistency = 0
            
            overall_score = (completeness + consistency) / 2
            quality_scores.append(overall_score)
            columns.append(col)
        
        fig = px.bar(
            x=columns,
            y=quality_scores,
            title="Data Quality Score by Column",
            color=quality_scores,
            color_continuous_scale='RdYlGn',
            text=[f'{score:.1f}%' for score in quality_scores],
            textposition='auto'
        )
        
        fig.update_layout(
            xaxis_title="Columns",
            yaxis_title="Quality Score (%)",
            height=max(400, len(columns) * 25)
        )
        
        return fig
    
    def _create_uniqueness_chart(self) -> go.Figure:
        """Create uniqueness analysis chart"""
        uniqueness_ratios = []
        columns = []
        
        for col in self.df.columns:
            ratio = self.df[col].nunique() / len(self.df) * 100
            uniqueness_ratios.append(ratio)
            columns.append(col)
        
        fig = go.Figure(data=[go.Bar(
            x=uniqueness_ratios,
            y=columns,
            orientation='h',
            marker_color='#F18F01',
            text=[f'{ratio:.1f}%' for ratio in uniqueness_ratios],
            textposition='auto'
        )])
        
        fig.update_layout(
            title="Uniqueness Ratio by Column",
            xaxis_title="Uniqueness (%)",
            yaxis_title="Columns",
            height=max(400, len(columns) * 25)
        )
        
        return fig
    
    def _create_memory_usage_chart(self) -> go.Figure:
        """Create memory usage chart"""
        memory_usage = self.df.memory_usage(deep=True)
        memory_mb = memory_usage / (1024 * 1024)  # Convert to MB
        
        fig = go.Figure(data=[go.Bar(
            x=memory_mb.values,
            y=memory_mb.index,
            orientation='h',
            marker_color='#A23B72',
            text=[f'{mb:.2f} MB' for mb in memory_mb.values],
            textposition='auto'
        )])
        
        fig.update_layout(
            title="Memory Usage by Column",
            xaxis_title="Memory Usage (MB)",
            yaxis_title="Columns",
            height=max(400, len(memory_mb) * 25)
        )
        
        return fig
