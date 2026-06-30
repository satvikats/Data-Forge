import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union

class DataCleaner:
    """
    Applies deterministic cleaning transformations on a Pandas DataFrame.
    """
    
    @staticmethod
    def standardize_headers(df: pd.DataFrame, style: str = "snake_case") -> pd.DataFrame:
        """
        Standardizes DataFrame column names.
        Supported styles: 'snake_case', 'camelCase', 'uppercase', 'lowercase', 'title_case'
        """
        df = df.copy()
        new_cols = []
        for col in df.columns:
            col_str = str(col).strip()
            
            if style == "snake_case":
                # Replace spaces and special characters with underscores, handle multiple underscores
                cleaned = col_str.replace(" ", "_")
                cleaned = "".join([c if c.isalnum() or c == '_' else '' for c in cleaned])
                cleaned = "_".join(filter(None, cleaned.split("_")))
                new_cols.append(cleaned.lower())
            
            elif style == "camelCase":
                # Split, make first word lower, rest capitalized
                parts = col_str.replace("_", " ").split()
                if not parts:
                    new_cols.append("")
                    continue
                first = parts[0].lower()
                rest = "".join(p.capitalize() for p in parts[1:])
                new_cols.append(first + rest)
                
            elif style == "uppercase":
                cleaned = col_str.replace(" ", "_")
                cleaned = "".join([c if c.isalnum() or c == '_' else '' for c in cleaned])
                new_cols.append(cleaned.upper())
                
            elif style == "lowercase":
                cleaned = col_str.replace(" ", "_")
                cleaned = "".join([c if c.isalnum() or c == '_' else '' for c in cleaned])
                new_cols.append(cleaned.lower())
                
            elif style == "title_case":
                parts = col_str.replace("_", " ").split()
                new_cols.append(" ".join(p.capitalize() for p in parts))
                
            else:
                new_cols.append(col_str)
                
        df.columns = new_cols
        return df

    @staticmethod
    def trim_whitespace(df: pd.DataFrame) -> pd.DataFrame:
        """
        Trims leading and trailing whitespace from all string columns.
        """
        df = df.copy()
        for col in df.columns:
            if df[col].dtype == object or isinstance(df[col].dtype, pd.StringDtype):
                df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        return df

    @staticmethod
    def remove_duplicates(df: pd.DataFrame, subset: List[str] = None) -> pd.DataFrame:
        """
        Removes duplicate rows.
        """
        return df.drop_duplicates(subset=subset).reset_index(drop=True)

    @staticmethod
    def handle_missing(
        df: pd.DataFrame, 
        column: str, 
        method: str, 
        fill_value: Any = None
    ) -> pd.DataFrame:
        """
        Handles missing values in a specific column.
        Methods: 'drop', 'mean', 'median', 'mode', 'constant'
        """
        df = df.copy()
        if column not in df.columns:
            return df
            
        if method == "drop":
            df = df.dropna(subset=[column]).reset_index(drop=True)
        elif method == "mean":
            # For numeric columns
            mean_val = pd.to_numeric(df[column], errors='coerce').mean()
            if not pd.isna(mean_val):
                df[column] = df[column].fillna(mean_val)
        elif method == "median":
            # For numeric columns
            med_val = pd.to_numeric(df[column], errors='coerce').median()
            if not pd.isna(med_val):
                df[column] = df[column].fillna(med_val)
        elif method == "mode":
            mode_series = df[column].dropna().mode()
            if not mode_series.empty:
                df[column] = df[column].fillna(mode_series[0])
        elif method == "constant":
            df[column] = df[column].fillna(fill_value if fill_value is not None else "")
            
        return df

    @staticmethod
    def convert_datatype(
        df: pd.DataFrame, 
        column: str, 
        target_type: str, 
        date_format: str = None
    ) -> pd.DataFrame:
        """
        Converts column to a target datatype.
        Types: 'int', 'float', 'str', 'datetime', 'boolean', 'category'
        """
        df = df.copy()
        if column not in df.columns:
            return df
            
        try:
            if target_type == "int":
                # Coerce to numeric, fill nulls with 0 or drop, and cast to int
                numeric_col = pd.to_numeric(df[column], errors='coerce')
                # If there are nulls, we use Int64 (nullable integer) to avoid float conversion
                df[column] = numeric_col.round().astype("Int64")
            elif target_type == "float":
                df[column] = pd.to_numeric(df[column], errors='coerce').astype(float)
            elif target_type == "str":
                # Convert nulls to empty string or keep as null
                df[column] = df[column].astype(str).replace("nan", "")
            elif target_type == "category":
                df[column] = df[column].astype("category")
            elif target_type == "datetime":
                if date_format:
                    df[column] = pd.to_datetime(df[column], format=date_format, errors='coerce')
                else:
                    df[column] = pd.to_datetime(df[column], errors='coerce')
            elif target_type == "boolean":
                # Convert standard indicators
                def parse_bool(val):
                    if pd.isna(val):
                        return None
                    s = str(val).strip().lower()
                    if s in ("true", "1", "1.0", "yes", "y", "t", "active"):
                        return True
                    if s in ("false", "0", "0.0", "no", "n", "f", "inactive"):
                        return False
                    return None
                df[column] = df[column].apply(parse_bool).astype("boolean")
        except Exception:
            # Let it fallback or stay unchanged on hard error
            pass
            
        return df

    def apply_pipeline(self, df: pd.DataFrame, pipeline: Dict[str, Any]) -> pd.DataFrame:
        """
        Applies a full sequence of cleaning steps defined in a pipeline dictionary.
        """
        cleaned_df = df.copy()
        
        # 1. Standardize Headers
        header_style = pipeline.get("standardize_headers")
        if header_style:
            cleaned_df = self.standardize_headers(cleaned_df, style=header_style)
            
        # 2. Trim Whitespace
        if pipeline.get("trim_whitespace", False):
            cleaned_df = self.trim_whitespace(cleaned_df)
            
        # 3. Handle Missing Values
        imputations = pipeline.get("imputations", [])
        for imp in imputations:
            col = imp.get("column")
            method = imp.get("method")
            val = imp.get("value")
            
            # Map column name to standardized if header styling was applied
            # In case the user is inputting pre-standardized column names, we check both
            if col not in cleaned_df.columns:
                # Attempt to find standard snake case or similar
                # Just skip if completely missing
                continue
            cleaned_df = self.handle_missing(cleaned_df, column=col, method=method, fill_value=val)
            
        # 4. Convert Datatypes
        conversions = pipeline.get("conversions", [])
        for conv in conversions:
            col = conv.get("column")
            target = conv.get("type")
            fmt = conv.get("format")
            if col in cleaned_df.columns:
                cleaned_df = self.convert_datatype(cleaned_df, column=col, target_type=target, date_format=fmt)
                
        # 5. Remove Duplicates
        if pipeline.get("remove_duplicates", False):
            dup_cols = pipeline.get("duplicate_columns")
            cleaned_df = self.remove_duplicates(cleaned_df, subset=dup_cols)
            
        # 6. Drop specified null rows
        drop_nulls = pipeline.get("drop_null_rows", [])
        for col in drop_nulls:
            if col in cleaned_df.columns:
                cleaned_df = self.handle_missing(cleaned_df, column=col, method="drop")
                
        return cleaned_df
