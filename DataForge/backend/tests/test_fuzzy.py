import pytest
import pandas as pd
from backend.core.fuzzy_matcher import find_fuzzy_groups, apply_fuzzy_mapping, calculate_similarity

def test_calculate_similarity():
    # Identical
    assert calculate_similarity("organic cotton", "organic cotton") == 100.0
    # Different
    assert calculate_similarity("organic cotton", "polyester") < 50.0
    # Inconsistent capitalization & spaces
    assert calculate_similarity("  Organic Cotton  ", "organic-cotton") > 80.0

def test_find_fuzzy_groups():
    series = pd.Series(["Organic Cotton", "Org. Cotton", "Organic-Cotton", "Polyester", "Poly", "Polyester"])
    groups = find_fuzzy_groups(series, threshold=75.0)
    
    # We expect a group for Cotton variants
    assert len(groups) >= 1
    cotton_group = next((g for g in groups if "Organic Cotton" in g["canonical"]), None)
    assert cotton_group is not None
    assert "Org. Cotton" in cotton_group["members"]
    assert "Organic-Cotton" in cotton_group["members"]

def test_apply_fuzzy_mapping():
    df = pd.DataFrame({"Material": ["Organic Cotton", "Org. Cotton", "Polyester"]})
    mapping = {"Org. Cotton": "Organic Cotton"}
    
    df_clean = apply_fuzzy_mapping(df, "Material", mapping)
    assert df_clean.loc[1, "Material"] == "Organic Cotton"
    assert df_clean.loc[2, "Material"] == "Polyester"
