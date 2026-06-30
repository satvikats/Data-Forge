import pandas as pd
from typing import Dict, Any, List
from backend.validators.rules import DataForgeValidator, create_rule_from_dict

def validate_dataset(df: pd.DataFrame, rule_definitions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validates a dataset against a list of rule definitions.
    Returns:
        List[Dict[str, Any]]: List of validation failures.
    """
    validator = DataForgeValidator()
    
    for rdef in rule_definitions:
        try:
            rule_obj = create_rule_from_dict(rdef)
            validator.add_rule(rule_obj)
        except Exception:
            # Skip invalid rule formulations
            continue
            
    return validator.validate(df)
