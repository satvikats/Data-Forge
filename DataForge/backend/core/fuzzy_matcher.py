import pandas as pd
from typing import Dict, Any, List, Set, Tuple
import logging

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    import difflib
    HAS_RAPIDFUZZ = False
    logging.warning("rapidfuzz not installed, falling back to difflib SequenceMatcher")

def calculate_similarity(s1: str, s2: str) -> float:
    """
    Calculates similarity between two strings on a scale of 0 to 100.
    """
    s1_clean = str(s1).strip().lower()
    s2_clean = str(s2).strip().lower()
    if not s1_clean or not s2_clean:
        return 0.0
        
    if HAS_RAPIDFUZZ:
        return float(fuzz.ratio(s1_clean, s2_clean))
    else:
        return float(difflib.SequenceMatcher(None, s1_clean, s2_clean).ratio() * 100)

def find_fuzzy_groups(series: pd.Series, threshold: float = 80.0) -> List[Dict[str, Any]]:
    """
    Identifies clusters of similar text values in a Series.
    Returns:
        List[Dict[str, Any]]: List of groups, each containing:
            - 'canonical': the most frequent value in the cluster
            - 'members': list of all values in the cluster
            - 'frequencies': dictionary of members and their counts in the dataset
    """
    series_clean = series.dropna().astype(str)
    if series_clean.empty:
        return []
        
    # Get value counts
    val_counts = series_clean.value_counts().to_dict()
    unique_vals = list(val_counts.keys())
    
    # Sort by frequency descending (most frequent values should act as candidates for cluster centers)
    unique_vals.sort(key=lambda x: val_counts[x], reverse=True)
    
    visited: Set[str] = set()
    groups: List[Dict[str, Any]] = []
    
    for val in unique_vals:
        if val in visited:
            continue
            
        cluster_members = [val]
        visited.add(val)
        
        # Check similarity with other values
        for other in unique_vals:
            if other in visited:
                continue
                
            sim = calculate_similarity(val, other)
            if sim >= threshold:
                cluster_members.append(other)
                visited.add(other)
                
        # Only create a group if it has more than one member (it's actually a cluster of variants)
        # Or if the member is slightly different but we want to know about it.
        if len(cluster_members) > 1:
            groups.append({
                "canonical": val,  # Since unique_vals was sorted by frequency, 'val' is the most frequent
                "members": cluster_members,
                "frequencies": {m: val_counts[m] for m in cluster_members}
            })
            
    return groups

def apply_fuzzy_mapping(df: pd.DataFrame, column: str, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Applies a mapping to standardize fuzzy variations in a column.
    mapping: Dict of {original_value: standardized_value}
    """
    df = df.copy()
    if column not in df.columns:
        return df
        
    # Apply mapping
    df[column] = df[column].astype(str).map(lambda x: mapping.get(x, x))
    return df
