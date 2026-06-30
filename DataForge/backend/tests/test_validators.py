import pytest
import pandas as pd
from backend.validators.rules import (
    NonNullRule, UniqueRule, RangeRule, RegexRule, InSetRule,
    DataForgeValidator, suggest_validation_rules
)

def test_non_null_rule():
    rule = NonNullRule("name")
    
    assert rule.validate_value("John", 1) is None
    assert rule.validate_value("", 2) is not None
    assert rule.validate_value(None, 3) is not None

def test_range_rule():
    rule = RangeRule("age", min_val=0, max_val=120)
    
    assert rule.validate_value(25, 1) is None
    assert rule.validate_value(-5, 2) is not None
    assert rule.validate_value(150, 3) is not None
    assert rule.validate_value("abc", 4) is not None  # Not numeric

def test_unique_rule():
    rule = UniqueRule("id")
    series = pd.Series([1, 2, 3, 2, 4])
    
    failures = rule.validate_series(series)
    # Row 1 (value 2) and row 3 (value 2) are duplicates
    assert len(failures) == 2
    assert failures[0]["value"] == "2"

def test_regex_rule():
    rule = RegexRule("email", pattern=r'^\S+@\S+\.\S+$', description="simple email")
    
    assert rule.validate_value("test@corp.com", 1) is None
    assert rule.validate_value("invalid-email", 2) is not None

def test_inset_rule():
    rule = InSetRule("status", allowed_values=["active", "inactive"])
    
    assert rule.validate_value("Active", 1) is None  # Case insensitive
    assert rule.validate_value("pending", 2) is not None

def test_dataforge_validator():
    df = pd.DataFrame({
        "id": [1, 2, 2],
        "age": [30, -5, 45],
        "email": ["a@b.com", "b@c.com", "invalid"]
    })
    
    validator = DataForgeValidator([
        UniqueRule("id"),
        RangeRule("age", min_val=0),
        RegexRule("email", pattern=r'^\S+@\S+\.\S+$', description="email format")
    ])
    
    failures = validator.validate(df)
    # id duplicates: 2 failures
    # age outlier: 1 failure (-5)
    # email format error: 1 failure (invalid)
    assert len(failures) == 4
