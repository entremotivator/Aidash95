import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re

class DataScanner:
    """Advanced data analysis and scanning utility"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy() if df is not None else pd.DataFrame()
        self.analysis_results = {}
        self.insights = []
        
    def scan_overview(self) -> Dict[str, Any]:
        """Generate comprehensive data overview"""
        if self.df.empty:
            return {"error": "No data to analyze"}
        
        overview = {
            "shape": self.df.shape,
            "columns": list(self.df.columns),
            "dtypes": self.df.dtypes.to_dict(),
            "memory_usage": self.df.memory_usage(deep=True).sum(),
            "null_counts": self.df.isnull().sum().to_dict(),
            "duplicate_rows": self.df.duplicated().sum(),
            "numeric_columns": list(self.df.select_dtypes(include=[np.number]).columns),
            "categorical_columns": list(self.df.select_dtypes(include=['object']).columns),
            "datetime_columns": list(self.df.select_dtypes(include=['datetime64']).columns)
        }
        
        # Data quality score
        total_cells = self.df.shape[0] * self.df.shape[1]
        null_cells = self.df.isnull().sum().sum()
        overview["data_quality_score"] = ((total_cells - null_cells) / total_cells * 100) if total_cells > 0 else 0
        
        return overview
    
    def analyze_column(self, column: str) -> Dict[str, Any]:
        """Detailed analysis of a specific column"""
        if column not in self.df.columns:
            return {"error": f"Column '{column}' not found"}
        
        series = self.df[column]
        analysis = {
            "column_name": column,
            "dtype": str(series.dtype),
            "count": len(series),
            "null_count": series.isnull().sum(),
            "null_percentage": (series.isnull().sum() / len(series) * 100) if len(series) > 0 else 0,
            "unique_count": series.nunique(),
            "unique_percentage": (series.nunique() / len(series) * 100) if len(series) > 0 else 0
        }
        
        # Numeric analysis
        if pd.api.types.is_numeric_dtype(series):
            numeric_series = pd.to_numeric(series, errors='coerce').dropna()
            if len(numeric_series) > 0:
                analysis.update({
                    "min": numeric_series.min(),
                    "max": numeric_series.max(),
                    "mean": numeric_series.mean(),
                    "median": numeric_series.median(),
                    "std": numeric_series.std(),
                    "q25": numeric_series.quantile(0.25),
                    "q75": numeric_series.quantile(0.75),
                    "outliers": self._detect_outliers(numeric_series)
                })
        
        # Categorical analysis
        elif pd.api.types.is_object_dtype(series):
            value_counts = series.value_counts()
            analysis.update({
                "top_values": value_counts.head(10).to_dict(),
                "avg_length": series.astype(str).str.len().mean(),
                "contains_emails": series.astype(str).str.contains(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', regex=True).sum(),
                "contains_phones": series.astype(str).str.contains(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', regex=True).sum(),
                "contains_urls": series.astype(str).str.contains(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\$$\$$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', regex=True).sum()
            })
        
        # DateTime analysis
        elif pd.api.types.is_datetime64_any_dtype(series):
            dt_series = pd.to_datetime(series, errors='coerce').dropna()
            if len(dt_series) > 0:
                analysis.update({
                    "min_date": dt_series.min(),
                    "max_date": dt_series.max(),
                    "date_range_days": (dt_series.max() - dt_series.min()).days,
                    "most_common_year": dt_series.dt.year.mode().iloc[0] if len(dt_series.dt.year.mode()) > 0 else None,
                    "most_common_month": dt_series.dt.month.mode().iloc[0] if len(dt_series.dt.month.mode()) > 0 else None
                })
        
        return analysis
    
    def _detect_outliers(self, series: pd.Series) -> Dict[str, Any]:
        """Detect outliers using IQR method"""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        
        return {
            "count": len(outliers),
            "percentage": (len(outliers) / len(series) * 100) if len(series) > 0 else 0,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "outlier_values": outliers.tolist()[:20]  # Limit to first 20
        }
    
    def find_correlations(self, threshold: float = 0.5) -> Dict[str, Any]:
        """Find correlations between numeric columns"""
        numeric_df = self.df.select_dtypes(include=[np.number])
        
        if numeric_df.shape[1] < 2:
            return {"error": "Need at least 2 numeric columns for correlation analysis"}
        
        corr_matrix = numeric_df.corr()
        
        # Find strong correlations
        strong_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) >= threshold:
                    strong_correlations.append({
                        "column1": corr_matrix.columns[i],
                        "column2": corr_matrix.columns[j],
                        "correlation": corr_value,
                        "strength": self._correlation_strength(abs(corr_value))
                    })
        
        return {
            "correlation_matrix": corr_matrix.to_dict(),
            "strong_correlations": strong_correlations,
            "avg_correlation": corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()
        }
    
    def _correlation_strength(self, corr_value: float) -> str:
        """Classify correlation strength"""
        if corr_value >= 0.8:
            return "Very Strong"
        elif corr_value >= 0.6:
            return "Strong"
        elif corr_value >= 0.4:
            return "Moderate"
        elif corr_value >= 0.2:
            return "Weak"
        else:
            return "Very Weak"
    
    def detect_patterns(self) -> Dict[str, Any]:
        """Detect patterns and anomalies in the data"""
        patterns = {
            "missing_data_patterns": self._analyze_missing_patterns(),
            "duplicate_patterns": self._analyze_duplicate_patterns(),
            "value_patterns": self._analyze_value_patterns()
        }
        
        return patterns
    
    def _analyze_missing_patterns(self) -> Dict[str, Any]:
        """Analyze missing data patterns"""
        missing_data = self.df.isnull()
        
        # Columns with missing data
        missing_cols = missing_data.sum()
        missing_cols = missing_cols[missing_cols > 0].sort_values(ascending=False)
        
        # Rows with missing data
        missing_rows = missing_data.sum(axis=1)
        rows_with_missing = (missing_rows > 0).sum()
        
        return {
            "columns_with_missing": missing_cols.to_dict(),
            "rows_with_missing": int(rows_with_missing),
            "total_missing_cells": int(missing_data.sum().sum()),
            "missing_percentage": float(missing_data.sum().sum() / (self.df.shape[0] * self.df.shape[1]) * 100)
        }
    
    def _analyze_duplicate_patterns(self) -> Dict[str, Any]:
        """Analyze duplicate data patterns"""
        duplicates = self.df.duplicated()
        duplicate_count = duplicates.sum()
        
        # Find columns that might be unique identifiers
        potential_ids = []
        for col in self.df.columns:
            if self.df[col].nunique() == len(self.df) and not self.df[col].isnull().any():
                potential_ids.append(col)
        
        return {
            "duplicate_rows": int(duplicate_count),
            "duplicate_percentage": float(duplicate_count / len(self.df) * 100) if len(self.df) > 0 else 0,
            "potential_id_columns": potential_ids
        }
    
    def _analyze_value_patterns(self) -> Dict[str, Any]:
        """Analyze value patterns in categorical columns"""
        patterns = {}
        
        for col in self.df.select_dtypes(include=['object']).columns:
            series = self.df[col].dropna().astype(str)
            
            if len(series) > 0:
                patterns[col] = {
                    "common_prefixes": self._find_common_patterns(series, "prefix"),
                    "common_suffixes": self._find_common_patterns(series, "suffix"),
                    "avg_length": series.str.len().mean(),
                    "length_variation": series.str.len().std()
                }
        
        return patterns
    
    def _find_common_patterns(self, series: pd.Series, pattern_type: str) -> List[Dict[str, Any]]:
        """Find common prefixes or suffixes"""
        if pattern_type == "prefix":
            patterns = series.str[:3].value_counts().head(5)
        else:  # suffix
            patterns = series.str[-3:].value_counts().head(5)
        
        return [{"pattern": pattern, "count": count} for pattern, count in patterns.items()]
    
    def generate_insights(self) -> List[str]:
        """Generate actionable insights from the data"""
        insights = []
        
        if self.df.empty:
            return ["No data available for analysis"]
        
        overview = self.scan_overview()
        
        # Data quality insights
        if overview["data_quality_score"] < 80:
            insights.append(f"⚠️ Data quality score is {overview['data_quality_score']:.1f}% - consider cleaning missing values")
        
        if overview["duplicate_rows"] > 0:
            insights.append(f"🔄 Found {overview['duplicate_rows']} duplicate rows - consider deduplication")
        
        # Column insights
        for col in self.df.columns:
            col_analysis = self.analyze_column(col)
            
            if col_analysis["null_percentage"] > 50:
                insights.append(f"❌ Column '{col}' has {col_analysis['null_percentage']:.1f}% missing values")
            
            if col_analysis["unique_percentage"] > 95 and col_analysis["count"] > 10:
                insights.append(f"🔑 Column '{col}' might be a unique identifier")
            
            if "outliers" in col_analysis and col_analysis["outliers"]["percentage"] > 10:
                insights.append(f"📊 Column '{col}' has {col_analysis['outliers']['percentage']:.1f}% outliers")
        
        # Correlation insights
        if len(self.df.select_dtypes(include=[np.number]).columns) >= 2:
            correlations = self.find_correlations()
            if "strong_correlations" in correlations:
                for corr in correlations["strong_correlations"][:3]:  # Top 3
                    insights.append(f"🔗 Strong correlation ({corr['correlation']:.2f}) between '{corr['column1']}' and '{corr['column2']}'")
        
        return insights[:10]  # Limit to top 10 insights

class VisualizationEngine:
    """Advanced visualization engine for data analysis"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy() if df is not None else pd.DataFrame()
    
    def create_overview_charts(self) -> Dict[str, Any]:
        """Create overview visualization charts"""
        charts = {}
        
        if self.df.empty:
            return {"error": "No data to visualize"}
        
        # Data types distribution
        dtype_counts = self.df.dtypes.value_counts()
        charts["data_types"] = px.pie(
            values=dtype_counts.values,
            names=dtype_counts.index.astype(str),
            title="Data Types Distribution"
        )
        
        # Missing data heatmap
        if self.df.isnull().sum().sum() > 0:
            missing_data = self.df.isnull().astype(int)
            charts["missing_data"] = px.imshow(
                missing_data.T,
                title="Missing Data Pattern",
                color_continuous_scale="Reds",
                aspect="auto"
            )
        
        # Numeric columns distribution
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            charts["numeric_distributions"] = {}
            for col in numeric_cols[:4]:  # Limit to first 4
                charts["numeric_distributions"][col] = px.histogram(
                    self.df, x=col, title=f"Distribution of {col}"
                )
        
        return charts
    
    def create_correlation_heatmap(self) -> Optional[go.Figure]:
        """Create correlation heatmap for numeric columns"""
        numeric_df = self.df.select_dtypes(include=[np.number])
        
        if numeric_df.shape[1] < 2:
            return None
        
        corr_matrix = numeric_df.corr()
        
        fig = px.imshow(
            corr_matrix,
            title="Correlation Heatmap",
            color_continuous_scale="RdBu",
            aspect="auto"
        )
        
        return fig
    
    def create_column_analysis_chart(self, column: str) -> Optional[go.Figure]:
        """Create detailed chart for specific column"""
        if column not in self.df.columns:
            return None
        
        series = self.df[column]
        
        # Numeric column
        if pd.api.types.is_numeric_dtype(series):
            return px.box(y=series, title=f"Box Plot of {column}")
        
        # Categorical column
        elif pd.api.types.is_object_dtype(series):
            value_counts = series.value_counts().head(20)
            return px.bar(
                x=value_counts.index,
                y=value_counts.values,
                title=f"Top Values in {column}"
            )
        
        # DateTime column
        elif pd.api.types.is_datetime64_any_dtype(series):
            dt_series = pd.to_datetime(series, errors='coerce').dropna()
            if len(dt_series) > 0:
                monthly_counts = dt_series.dt.to_period('M').value_counts().sort_index()
                return px.line(
                    x=monthly_counts.index.astype(str),
                    y=monthly_counts.values,
                    title=f"Timeline of {column}"
                )
        
        return None
    
    def create_comparison_charts(self, x_col: str, y_col: str) -> Optional[go.Figure]:
        """Create comparison charts between two columns"""
        if x_col not in self.df.columns or y_col not in self.df.columns:
            return None
        
        # Both numeric
        if (pd.api.types.is_numeric_dtype(self.df[x_col]) and 
            pd.api.types.is_numeric_dtype(self.df[y_col])):
            return px.scatter(
                self.df, x=x_col, y=y_col,
                title=f"{x_col} vs {y_col}",
                trendline="ols"
            )
        
        # One categorical, one numeric
        elif (pd.api.types.is_object_dtype(self.df[x_col]) and 
              pd.api.types.is_numeric_dtype(self.df[y_col])):
            return px.box(
                self.df, x=x_col, y=y_col,
                title=f"{y_col} by {x_col}"
            )
        
        # Both categorical
        elif (pd.api.types.is_object_dtype(self.df[x_col]) and 
              pd.api.types.is_object_dtype(self.df[y_col])):
            crosstab = pd.crosstab(self.df[x_col], self.df[y_col])
            return px.imshow(
                crosstab,
                title=f"Cross-tabulation: {x_col} vs {y_col}",
                aspect="auto"
            )
        
        return None
