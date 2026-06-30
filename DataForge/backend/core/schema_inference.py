import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List

def detect_column_type(series: pd.Series) -> str:
    """
    Detect the likely semantic datatype of a pandas Series.
    Returns one of: 'boolean', 'numeric', 'datetime', 'categorical', 'text', 'empty'
    """
    # Drop nulls for checking
    non_null_series = series.dropna()
    if non_null_series.empty:
        return "empty"
    
    # Get series dtype
    dtype_name = str(series.dtype)
    
    # 1. Boolean check
    unique_vals = non_null_series.unique()
    if len(unique_vals) <= 2:
        # Check if values are boolean-like
        bool_indicators = {
            True, False, 1, 0, 1.0, 0.0, 
            'true', 'false', 't', 'f', 'yes', 'no', 'y', 'n', 
            '1', '0', '1.0', '0.0', 'active', 'inactive'
        }
        if all(str(val).lower() in bool_indicators for val in unique_vals):
            return "boolean"

    # 2. Numeric check (int, float)
    if pd.api.types.is_numeric_dtype(series) and not dtype_name.startswith('bool'):
        return "numeric"
    
    # Try converting to numeric to handle string-represented numbers
    try:
        # Check if it mostly contains numbers
        converted = pd.to_numeric(non_null_series, errors='coerce')
        if converted.notnull().mean() > 0.9:  # 90% or more are numeric
            return "numeric"
    except Exception:
        pass

    # 3. Datetime check
    # Avoid treating small integers or pure digit strings as timestamps
    has_date_format = False
    sample_strings = non_null_series.astype(str).head(10)
    
    # Simple regex to check if it looks like a date (e.g. YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY, etc.)
    date_patterns = [
        r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',  # 2026-06-30
        r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # 06/30/2026 or 30-06-26
        r'\d{4}\d{2}\d{2}',                # 20260630
        r'[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4}' # June 30, 2026
    ]
    for pattern in date_patterns:
        if any(re.search(pattern, s) for s in sample_strings):
            has_date_format = True
            break
            
    if has_date_format:
        try:
            converted_dates = pd.to_datetime(non_null_series, errors='coerce')
            if converted_dates.notnull().mean() > 0.8:  # 80% or more parse successfully
                return "datetime"
        except Exception:
            pass

    # 4. Categorical check (based on cardinality relative to length)
    n_unique = len(unique_vals)
    n_total = len(series)
    
    # If number of unique values is small (<= 15) or makes up less than 10% of values for larger datasets
    if n_unique <= 15 or (n_unique < 100 and n_unique / n_total < 0.15):
        return "categorical"
        
    return "text"

def infer_schema(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Profiles a DataFrame and infers the schema, generating statistics for each column.
    """
    schema = {}
    total_rows = len(df)
    
    for col in df.columns:
        series = df[col]
        inferred_type = detect_column_type(series)
        
        # Base stats
        null_count = int(series.isnull().sum())
        null_pct = float(null_count / total_rows) if total_rows > 0 else 0.0
        unique_vals = series.dropna().unique()
        unique_count = len(unique_vals)
        
        # Sample values (first 5 non-null)
        sample_vals = [str(x) for x in series.dropna().head(5).tolist()]
        
        # Top frequent values
        top_freq = []
        try:
            value_counts = series.dropna().value_counts().head(5)
            top_freq = [{"value": str(k), "count": int(v)} for k, v in value_counts.to_dict().items()]
        except Exception:
            pass
            
        col_stats = {
            "inferred_type": inferred_type,
            "pandas_type": str(series.dtype),
            "total_count": total_rows,
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": unique_count,
            "sample_values": sample_vals,
            "top_values": top_freq
        }
        
        # Add type-specific statistics
        if inferred_type == "numeric":
            try:
                num_series = pd.to_numeric(series, errors='coerce').dropna()
                if not num_series.empty:
                    col_stats.update({
                        "min": float(num_series.min()),
                        "max": float(num_series.max()),
                        "mean": float(num_series.mean()),
                        "std": float(num_series.std()) if len(num_series) > 1 else 0.0,
                        "median": float(num_series.median())
                    })
            except Exception:
                pass
        elif inferred_type == "datetime":
            try:
                date_series = pd.to_datetime(series, errors='coerce').dropna()
                if not date_series.empty:
                    col_stats.update({
                        "min": date_series.min().strftime('%Y-%m-%d %H:%M:%S'),
                        "max": date_series.max().strftime('%Y-%m-%d %H:%M:%S')
                    })
            except Exception:
                pass
                
        schema[str(col)] = col_stats
        
    return schema
