import pandas as pd
import re
from typing import Dict, Any, List, Optional

class ValidationRule:
    """
    Base class representing a validation rule.
    """
    def __init__(self, column: str, rule_type: str, params: Dict[str, Any] = None):
        self.column = column
        self.rule_type = rule_type
        self.params = params or {}
        
    def validate_value(self, val: Any, row_idx: int) -> Optional[Dict[str, Any]]:
        """
        Validates a single cell value. Returns None if valid, or a dictionary log if invalid.
        """
        raise NotImplementedError
        
    def validate_series(self, series: pd.Series) -> List[Dict[str, Any]]:
        """
        Validates an entire pandas Series. Returns a list of validation logs for any failures.
        """
        failures = []
        for idx, val in series.items():
            result = self.validate_value(val, int(idx))
            if result:
                failures.append(result)
        return failures


class NonNullRule(ValidationRule):
    def __init__(self, column: str):
        super().__init__(column, "non_null")
        
    def validate_value(self, val: Any, row_idx: int) -> Optional[Dict[str, Any]]:
        if pd.isna(val) or val == "":
            return {
                "column": self.column,
                "row_index": row_idx,
                "value": str(val),
                "rule": "non_null",
                "message": f"Value is missing (null/empty) in row {row_idx}."
            }
        return None


class UniqueRule(ValidationRule):
    def __init__(self, column: str):
        super().__init__(column, "unique")
        self.seen = set()
        
    def validate_value(self, val: Any, row_idx: int) -> Optional[Dict[str, Any]]:
        # Usually, unique constraints are evaluated across the whole series.
        # But we can track state or evaluate on series level.
        return None
        
    def validate_series(self, series: pd.Series) -> List[Dict[str, Any]]:
        failures = []
        # Get duplicates indices
        non_null_series = series.dropna()
        dups = non_null_series[non_null_series.duplicated(keep=False)]
        
        for idx, val in dups.items():
            failures.append({
                "column": self.column,
                "row_index": int(idx),
                "value": str(val),
                "rule": "unique",
                "message": f"Duplicate value '{val}' in row {idx}."
            })
        return failures


class RangeRule(ValidationRule):
    def __init__(self, column: str, min_val: Optional[float] = None, max_val: Optional[float] = None):
        super().__init__(column, "range", {"min": min_val, "max": max_val})
        self.min_val = min_val
        self.max_val = max_val
        
    def validate_value(self, val: Any, row_idx: int) -> Optional[Dict[str, Any]]:
        if pd.isna(val) or val == "":
            return None  # Missing values are checked by NonNullRule
            
        try:
            num_val = float(val)
            if self.min_val is not None and num_val < self.min_val:
                return {
                    "column": self.column,
                    "row_index": row_idx,
                    "value": str(val),
                    "rule": "range",
                    "message": f"Value {val} is below minimum allowed ({self.min_val}) in row {row_idx}."
                }
            if self.max_val is not None and num_val > self.max_val:
                return {
                    "column": self.column,
                    "row_index": row_idx,
                    "value": str(val),
                    "rule": "range",
                    "message": f"Value {val} is above maximum allowed ({self.max_val}) in row {row_idx}."
                }
        except ValueError:
            return {
                "column": self.column,
                "row_index": row_idx,
                "value": str(val),
                "rule": "range",
                "message": f"Value '{val}' is not numeric in row {row_idx}."
            }
        return None


class RegexRule(ValidationRule):
    def __init__(self, column: str, pattern: str, description: str = "Regex pattern"):
        super().__init__(column, "regex", {"pattern": pattern, "description": description})
        self.pattern = pattern
        self.pattern_compiled = re.compile(pattern)
        self.description = description
        
    def validate_value(self, val: Any, row_idx: int) -> Optional[Dict[str, Any]]:
        if pd.isna(val) or val == "":
            return None
            
        if not self.pattern_compiled.match(str(val)):
            return {
                "column": self.column,
                "row_index": row_idx,
                "value": str(val),
                "rule": "regex",
                "message": f"Value '{val}' does not match pattern '{self.description}' in row {row_idx}."
            }
        return None


class InSetRule(ValidationRule):
    def __init__(self, column: str, allowed_values: List[Any]):
        super().__init__(column, "in_set", {"allowed": allowed_values})
        self.allowed_values = set(str(x).strip().lower() for x in allowed_values)
        self.raw_allowed = allowed_values
        
    def validate_value(self, val: Any, row_idx: int) -> Optional[Dict[str, Any]]:
        if pd.isna(val) or val == "":
            return None
            
        val_str = str(val).strip().lower()
        if val_str not in self.allowed_values:
            return {
                "column": self.column,
                "row_index": row_idx,
                "value": str(val),
                "rule": "in_set",
                "message": f"Value '{val}' is not in the allowed set {self.raw_allowed} in row {row_idx}."
            }
        return None


class DataForgeValidator:
    """
    Aggregates and executes multiple ValidationRules against a DataFrame.
    """
    def __init__(self, rules: List[ValidationRule] = None):
        self.rules = rules or []
        
    def add_rule(self, rule: ValidationRule):
        self.rules.append(rule)
        
    def validate(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Runs validation across the DataFrame and returns a list of error dictionaries.
        """
        all_failures = []
        for rule in self.rules:
            if rule.column not in df.columns:
                continue
            
            series = df[rule.column]
            # Use specific series validator (which optimizes whole-column checks like uniqueness)
            failures = rule.validate_series(series)
            all_failures.extend(failures)
            
        return all_failures

def suggest_validation_rules(schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analyzes inferred schema statistics and suggests a list of rule definitions.
    Returns:
        List[Dict[str, Any]]: Serialized rule structures (e.g. {'column': '...', 'type': '...', 'params': {...}})
    """
    suggested = []
    for col, stats in schema.items():
        inferred_type = stats.get("inferred_type")
        null_pct = stats.get("null_pct", 0.0)
        unique_pct = (stats.get("unique_count", 0) / stats.get("total_count", 1)) if stats.get("total_count", 0) > 0 else 0.0
        
        # 1. Non-null Suggestion
        if null_pct == 0.0:
            suggested.append({
                "column": col,
                "type": "non_null",
                "params": {}
            })
            
        # 2. Unique Suggestion (e.g. ID column)
        if unique_pct > 0.95 and stats.get("total_count", 0) > 10:
            suggested.append({
                "column": col,
                "type": "unique",
                "params": {}
            })
            
        # 3. Numeric Range Suggestion
        if inferred_type == "numeric":
            min_val = stats.get("min")
            max_val = stats.get("max")
            if min_val is not None and max_val is not None:
                # Round suggested ranges slightly for cleaner thresholds
                suggested.append({
                    "column": col,
                    "type": "range",
                    "params": {
                        "min": float(min_val),
                        "max": float(max_val)
                    }
                })
                
        # 4. Categorical Allowed Set Suggestion
        elif inferred_type == "categorical" and stats.get("unique_count", 0) <= 8:
            allowed_list = [v["value"] for v in stats.get("top_values", [])]
            if allowed_list:
                suggested.append({
                    "column": col,
                    "type": "in_set",
                    "params": {
                        "allowed": allowed_list
                    }
                })
                
        # 5. Format Suggestion
        col_lower = col.lower()
        if "email" in col_lower:
            suggested.append({
                "column": col,
                "type": "regex",
                "params": {
                    "pattern": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                    "description": "email format"
                }
            })
            
    return suggested

def create_rule_from_dict(d: Dict[str, Any]) -> ValidationRule:
    """
    Factory to construct a ValidationRule object from its dict serialized form.
    """
    col = d["column"]
    rtype = d["type"]
    params = d.get("params", {})
    
    if rtype == "non_null":
        return NonNullRule(col)
    elif rtype == "unique":
        return UniqueRule(col)
    elif rtype == "range":
        return RangeRule(col, min_val=params.get("min"), max_val=params.get("max"))
    elif rtype == "regex":
        return RegexRule(col, pattern=params.get("pattern"), description=params.get("description", "Regex pattern"))
    elif rtype == "in_set":
        return InSetRule(col, allowed_values=params.get("allowed", []))
    else:
        raise ValueError(f"Unknown validation rule type: {rtype}")
