import pytest
import pandas as pd
import numpy as np
from backend.core.cleaner import DataCleaner
from backend.tests.fixtures.sample_data import generate_messy_dataset

def test_standardize_headers():
    df = generate_messy_dataset()
    cleaner = DataCleaner()
    
    # 1. Test Snake Case
    df_snake = cleaner.standardize_headers(df, style="snake_case")
    expected_cols = ["cust_id", "cust_name", "eml", "ctn_wgt", "material", "txn_amt", "dt_joined"]
    assert list(df_snake.columns) == expected_cols

    # 2. Test Camel Case
    df_camel = cleaner.standardize_headers(df, style="camelCase")
    assert "custId" in df_camel.columns
    assert "custName" in df_camel.columns

def test_trim_whitespace():
    df = generate_messy_dataset()
    cleaner = DataCleaner()
    
    df_trimmed = cleaner.trim_whitespace(df)
    assert df_trimmed.loc[1, "Cust Name"] == "Jane Smith"  # Original has spaces "  Jane Smith  "

def test_remove_duplicates():
    df = generate_messy_dataset()
    cleaner = DataCleaner()
    
    initial_len = len(df)
    df_dedup = cleaner.remove_duplicates(df)
    assert len(df_dedup) == initial_len - 1  # Row 5 and 6 are duplicates ("Charlie Brown")

def test_handle_missing():
    df = generate_messy_dataset()
    cleaner = DataCleaner()
    
    # Test constant fill
    df_filled = cleaner.handle_missing(df, column="Cust Name", method="constant", fill_value="Unknown")
    assert df_filled.loc[3, "Cust Name"] == "Unknown"
    
    # Test mean fill
    df_mean = cleaner.handle_missing(df, column="Txn Amt", method="mean")
    assert not df_mean["Txn Amt"].isnull().any()

def test_convert_datatype():
    df = generate_messy_dataset()
    cleaner = DataCleaner()
    
    # Convert numerical column represented as string
    df_int = cleaner.convert_datatype(df, column="Ctn Wgt", target_type="int")
    # 'xyz' becomes NaN, other integers cast cleanly
    assert pd.isna(df_int.loc[7, "Ctn Wgt"])
    assert df_int.loc[0, "Ctn Wgt"] == 500
