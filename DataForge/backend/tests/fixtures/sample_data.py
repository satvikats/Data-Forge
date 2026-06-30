import pandas as pd
import numpy as np

def generate_messy_dataset() -> pd.DataFrame:
    """
    Generates a DataFrame representing a realistic messy dataset with:
    - Missing values
    - Inconsistent header casings
    - Near-duplicate categoricals
    - Outliers
    - Mismatched date formats
    - Invalid emails and structure formats
    """
    data = {
        "Cust ID": ["C001", "C002", "C003", "C004", "C005", "C006", "C006", "C008"], # Duplicate rows
        "Cust Name": ["John Doe", "  Jane Smith  ", "Bob Johnson", np.nan, "Alice Williams", "Charlie Brown", "Charlie Brown", "David Green"], # Whitespace & Nulls
        "Eml": ["john.doe@gmail.com", "jane.smith@yahoo", "bob.johnson@outlook.com", "alice@corp.co", "alice@corp.co", "charlie@gmail.com", "charlie@gmail.com", "invalid-email"], # Invalid email formats, duplicates
        "Ctn Wgt": ["500", "1.2", "750", np.nan, "800", "1200", "1200", "xyz"], # Inconsistent values, non-numeric values
        "Material": ["Org. Cotton", "Organic Cotton", "Organic-Cotton", "Polyester", "Poly (recycled)", "Recycled Polyester", "Recycled Polyester", "Cotton"], # Fuzzy duplicates
        "Txn Amt": [10.5, 12.0, 15.75, 8.99, 10000.0, 14.5, 14.5, -50.0], # Outliers & Negative values
        "Dt Joined": ["2026-01-15", "16/01/2026", "2026/01/17", "2026-01-18", np.nan, "Jan 20, 2026", "Jan 20, 2026", "invalid-date"] # Mixed formats & invalid dates
    }
    
    return pd.DataFrame(data)
