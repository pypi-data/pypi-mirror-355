# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p01_overview/run_analysis.py
# ==============================================================================
# PURPOSE: This is the core logic for the Overview analysis plugin. It performs
#          the initial, high-level characterization of the entire dataset.

import dask.dataframe as dd
import pandas as pd
from typing import Dict, Any, Optional

def _classify_column(dtype: Any, nunique: int, col_size: int) -> str:
    """Helper function to classify a single column based on its properties."""
    CATEGORICAL_THRESHOLD = 50
    if nunique == 1:
        return "Constant"
    if nunique == 2:
        return "Boolean"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "Datetime"
    if pd.api.types.is_numeric_dtype(dtype):
        if nunique <= CATEGORICAL_THRESHOLD:
            return "Categorical (Numeric)"
        return "Numeric"
    if pd.api.types.is_string_dtype(dtype) or pd.api.types.is_categorical_dtype(dtype):
        if nunique == col_size:
             return "Unique ID"
        if nunique <= CATEGORICAL_THRESHOLD:
            return "Categorical"
        return "Text (High Cardinality)"
    return "Unsupported"

def analyze(ddf: dd.DataFrame, target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs the first-level overview and variable type analysis of the dataset.
    """
    print("     -> Calculating dataset shape, memory, duplicates, and variable types...")
    try:
        # --- Stage 1: Basic Computations ---
        (num_rows, mem_usage_bytes, total_missing_cells) = dd.compute(
            len(ddf),
            ddf.memory_usage(deep=True).sum(),
            ddf.isnull().sum().sum()
        )

        # --- Stage 2: More Complex Computations (Handled Separately for Robustness) ---
        # The .drop_duplicates() method in Dask can be complex. Computing it
        # separately makes the process more stable.
        num_unique_rows = len(ddf.drop_duplicates())
        
        duplicate_rows = num_rows - num_unique_rows
        num_cols = len(ddf.columns)
        total_cells = num_rows * num_cols
        missing_cells_pct = (total_missing_cells / total_cells * 100) if total_cells > 0 else 0

        dtypes = ddf.dtypes
        n_uniques = ddf.nunique().compute()

        variable_types = {
            "Numeric": 0, "Categorical (Numeric)": 0, "Categorical": 0,
            "Boolean": 0, "Datetime": 0, "Text (High Cardinality)": 0,
            "Constant": 0, "Unique ID": 0, "Unsupported": 0,
        }
        column_details = {}

        for col_name in ddf.columns:
            col_type = _classify_column(dtypes[col_name], n_uniques[col_name], num_rows)
            variable_types[col_type] += 1
            column_details[col_name] = {
                'dtype': str(dtypes[col_name]),
                'decyphr_type': col_type,
                'nunique': int(n_uniques[col_name])
            }

        mem_usage_mb = round(mem_usage_bytes / (1024 * 1024), 2)
        
        results = {
            "dataset_stats": {
                "Number of Rows": num_rows,
                "Number of Columns": num_cols,
                "Total Cells": total_cells,
                "Memory Usage (MB)": mem_usage_mb,
                "Missing Cells": int(total_missing_cells),
                "Missing Cells (%)": f"{missing_cells_pct:.2f}%",
            },
            "data_quality": {
                "Duplicate Rows": f"{duplicate_rows} ({round(duplicate_rows / num_rows * 100, 2) if num_rows > 0 else 0}%)",
            },
            "variable_types": variable_types,
            "column_details": column_details
        }
        print("     ... Overview analysis complete.")
        return results
    except Exception as e:
        # CORRECTED: Include the actual error message for better debugging.
        error_message = f"Failed during overview analysis. Original error: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}