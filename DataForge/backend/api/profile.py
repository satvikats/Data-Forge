import pandas as pd
from typing import Dict, Any, List
from backend.core.schema_inference import infer_schema
from backend.core.anomaly_detector import run_anomaly_detection

def calculate_quality_score(df: pd.DataFrame, schema: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> float:
    """
    Computes a data quality score (0 to 100) based on missingness, outliers, and format anomalies.
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    total_cells = total_rows * total_cols
    
    if total_cells == 0:
        return 0.0
        
    # 1. Missingness penalty (up to 40 points)
    total_missing = sum(stats.get("null_count", 0) for stats in schema.values())
    missing_ratio = total_missing / total_cells
    missing_penalty = missing_ratio * 40.0
    
    # 2. Outlier penalty (up to 30 points)
    outlier_count = sum(1 for a in anomalies if a["type"] == "outlier")
    outlier_ratio = min(outlier_count / total_rows, 1.0) if total_rows > 0 else 0.0
    outlier_penalty = outlier_ratio * 30.0
    
    # 3. Format error penalty (up to 30 points)
    format_errors = sum(1 for a in anomalies if a["type"] == "format_error")
    format_ratio = min(format_errors / total_rows, 1.0) if total_rows > 0 else 0.0
    format_penalty = format_ratio * 30.0
    
    score = 100.0 - missing_penalty - outlier_penalty - format_penalty
    return max(0.0, min(100.0, round(score, 2)))

def generate_profile_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes DataFrame structure, infers types, identifies anomalies, and scores data quality.
    """
    if df.empty:
        return {
            "summary": {
                "row_count": 0,
                "column_count": len(df.columns),
                "total_cells": 0,
                "missing_cells": 0,
                "missing_pct": 0.0,
                "quality_score": 0.0
            },
            "columns": {},
            "anomalies": []
        }
        
    # Infer schema
    schema = infer_schema(df)
    
    # Detect anomalies
    anomalies = run_anomaly_detection(df, schema)
    
    # General metrics
    row_count = len(df)
    col_count = len(df.columns)
    total_cells = row_count * col_count
    missing_cells = sum(stats.get("null_count", 0) for stats in schema.values())
    missing_pct = float(missing_cells / total_cells) if total_cells > 0 else 0.0
    
    # Calculate quality score
    quality_score = calculate_quality_score(df, schema, anomalies)
    
    report = {
        "summary": {
            "row_count": row_count,
            "column_count": col_count,
            "total_cells": total_cells,
            "missing_cells": missing_cells,
            "missing_pct": round(missing_pct * 100, 2),
            "quality_score": quality_score
        },
        "columns": schema,
        "anomalies": anomalies
    }
    
    return report
