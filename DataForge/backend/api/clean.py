import pandas as pd
from typing import Dict, Any, List
from backend.core.cleaner import DataCleaner
from backend.core.fuzzy_matcher import apply_fuzzy_mapping

def run_cleaning_pipeline(df: pd.DataFrame, pipeline_config: Dict[str, Any]) -> pd.DataFrame:
    """
    Runs full cleaning transformations on the DataFrame.
    """
    cleaner = DataCleaner()
    return cleaner.apply_pipeline(df, pipeline_config)

def apply_fuzzy_replacements(df: pd.DataFrame, column: str, replacements: Dict[str, str]) -> pd.DataFrame:
    """
    Standardizes categorical text entries using custom replacements mapping.
    """
    return apply_fuzzy_mapping(df, column, replacements)
