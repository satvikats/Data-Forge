import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List

def detect_iqr_outliers(series: pd.Series) -> pd.Series:
    """
    Returns a boolean series where True indicates the value is an IQR outlier.
    """
    try:
        num_series = pd.to_numeric(series, errors='coerce')
        q1 = num_series.quantile(0.25)
        q3 = num_series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            # If IQR is 0, standard deviation check instead, or skip to avoid divide by zero/empty bands
            std = num_series.std()
            if std > 0:
                mean = num_series.mean()
                return (num_series - mean).abs() > 3 * std
            return pd.Series(False, index=series.index)
            
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Mark numeric non-nulls outside bounds as True
        return num_series.notnull() & ((num_series < lower_bound) | (num_series > upper_bound))
    except Exception:
        return pd.Series(False, index=series.index)

def detect_rare_categories(series: pd.Series, threshold: float = 0.01) -> List[Any]:
    """
    Finds unique values in a categorical column that occur with a relative frequency less than the threshold.
    Only applicable if the series has sufficient length (e.g. > 20 records) and unique values > 2.
    """
    non_null = series.dropna()
    if len(non_null) < 20:
        return []
        
    counts = non_null.value_counts(normalize=True)
    rare_vals = counts[counts < threshold].index.tolist()
    
    # Don't mark everything as rare if cardinality is extremely high
    if len(rare_vals) == len(counts):
        return []
        
    return rare_vals

def verify_regex_format(val: Any, pattern_str: str) -> bool:
    """
    Helper to test if a single value matches a regex pattern. Returns False if it fails.
    """
    if pd.isna(val) or val == "":
        return True  # Don't treat nulls as format anomalies, handle missingness separately
    try:
        return bool(re.match(pattern_str, str(val).strip()))
    except Exception:
        return False

def run_anomaly_detection(df: pd.DataFrame, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Scans a DataFrame and outputs a list of structural, numerical, or categorical anomalies.
    Returns:
        List[Dict[str, Any]]: List of anomaly records:
            - 'column': column name
            - 'row_index': row index (0-indexed) or None for column-level anomalies
            - 'value': problematic value or description
            - 'type': 'outlier' | 'rare_value' | 'format_error' | 'high_missingness'
            - 'message': user-friendly description
    """
    anomalies = []
    total_rows = len(df)
    
    if total_rows == 0:
        return []
        
    # Standard format regexes
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    phone_regex = r'^\+?1?\s*[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$' # basic US/international check
    
    for col, col_info in schema.items():
        if col not in df.columns:
            continue
            
        series = df[col]
        col_type = col_info.get("inferred_type")
        
        # 1. High Missingness Check
        null_pct = col_info.get("null_pct", 0.0)
        if null_pct > 0.5:
            anomalies.append({
                "column": col,
                "row_index": None,
                "value": f"{null_pct * 100:.1f}% missing",
                "type": "high_missingness",
                "message": f"Column '{col}' has a very high missing rate ({null_pct * 100:.1f}%)."
            })
            
        # 2. Numerical Outliers Check
        if col_type == "numeric":
            outlier_mask = detect_iqr_outliers(series)
            outlier_indices = outlier_mask[outlier_mask].index.tolist()
            # Cap anomalies to first 50 to avoid bloating reports
            for idx in outlier_indices[:50]:
                anomalies.append({
                    "column": col,
                    "row_index": int(idx),
                    "value": str(df.loc[idx, col]),
                    "type": "outlier",
                    "message": f"Numerical outlier detected in row {idx}: {df.loc[idx, col]}"
                })
            if len(outlier_indices) > 50:
                anomalies.append({
                    "column": col,
                    "row_index": None,
                    "value": f"{len(outlier_indices)} outliers",
                    "type": "outlier",
                    "message": f"Column '{col}' has {len(outlier_indices)} numerical outliers (first 50 shown above)."
                })
                
        # 3. Categorical Rare Values Check
        elif col_type == "categorical":
            rare_vals = detect_rare_categories(series)
            if rare_vals:
                # Find indices of rows with these rare values
                rare_mask = series.isin(rare_vals)
                rare_indices = rare_mask[rare_mask].index.tolist()
                for idx in rare_indices[:20]:
                    val = df.loc[idx, col]
                    anomalies.append({
                        "column": col,
                        "row_index": int(idx),
                        "value": str(val),
                        "type": "rare_value",
                        "message": f"Rare categorical value '{val}' (occurs < 1%) in row {idx}."
                    })
                    
        # 4. Format Anomalies Check (Semantic format heuristics)
        col_lower = col.lower()
        if "email" in col_lower:
            invalid_indices = [idx for idx, val in series.items() if not verify_regex_format(val, email_regex)]
            for idx in invalid_indices[:20]:
                anomalies.append({
                    "column": col,
                    "row_index": int(idx),
                    "value": str(df.loc[idx, col]),
                    "type": "format_error",
                    "message": f"Invalid email format in row {idx}: '{df.loc[idx, col]}'"
                })
        elif "phone" in col_lower or "tel" in col_lower:
            invalid_indices = [idx for idx, val in series.items() if not verify_regex_format(val, phone_regex)]
            for idx in invalid_indices[:20]:
                anomalies.append({
                    "column": col,
                    "row_index": int(idx),
                    "value": str(df.loc[idx, col]),
                    "type": "format_error",
                    "message": f"Invalid phone format in row {idx}: '{df.loc[idx, col]}'"
                })
                
    return anomalies
