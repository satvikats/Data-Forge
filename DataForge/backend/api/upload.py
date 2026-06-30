import pandas as pd
import io
from typing import Union, BinaryIO

def load_file(file_content: Union[str, bytes, BinaryIO], file_extension: str) -> pd.DataFrame:
    """
    Parses CSV, XLSX, or JSON inputs into a Pandas DataFrame.
    """
    ext = str(file_extension).lower().strip().replace(".", "")
    
    if ext == "csv":
        # Handle bytes/buffers vs file paths
        if isinstance(file_content, bytes):
            # Try to decode
            try:
                decoded = file_content.decode("utf-8")
            except UnicodeDecodeError:
                decoded = file_content.decode("latin-1")
            buffer = io.StringIO(decoded)
            return pd.read_csv(buffer)
        elif isinstance(file_content, (io.StringIO, io.BytesIO)):
            return pd.read_csv(file_content)
        else:
            return pd.read_csv(file_content)
            
    elif ext in ("xlsx", "xls"):
        if isinstance(file_content, bytes):
            buffer = io.BytesIO(file_content)
            return pd.read_excel(buffer)
        else:
            return pd.read_excel(file_content)
            
    elif ext == "json":
        if isinstance(file_content, bytes):
            try:
                decoded = file_content.decode("utf-8")
            except UnicodeDecodeError:
                decoded = file_content.decode("latin-1")
            buffer = io.StringIO(decoded)
            return pd.read_json(buffer)
        elif isinstance(file_content, (io.StringIO, io.BytesIO)):
            return pd.read_json(file_content)
        else:
            return pd.read_json(file_content)
            
    else:
        raise ValueError(f"Unsupported file format: {file_extension}. Only CSV, Excel, and JSON are supported.")
