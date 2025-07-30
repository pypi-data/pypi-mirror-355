# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p03_data_quality/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs a deep scan for common data quality issues, such
#          as constant columns, leading/trailing whitespace, and mixed data types.

import dask.dataframe as dd
from typing import Dict, Any, Optional, List

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes the dataframe for common data integrity and quality issues.

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results from the p01_overview plugin,
                                           used to identify column types.
        target_column (Optional[str]): The target column, ignored here.

    Returns:
        A dictionary summarizing the data quality issues found.
    """
    print("     -> Performing data quality scan (constants, whitespace)...")

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Data quality analysis requires 'column_details' from the overview plugin."}

    results: Dict[str, Any] = {
        "constant_columns": [],
        "whitespace_issues": [],
    }

    try:
        # --- 1. Identify Constant Columns ---
        # We can leverage the pre-computed analysis from the overview plugin for efficiency.
        constant_cols = [
            col for col, details in column_details.items() if details['decyphr_type'] == 'Constant'
        ]
        results["constant_columns"] = constant_cols
        if constant_cols:
            print(f"     ... Found {len(constant_cols)} constant column(s).")

        # --- 2. Check for Whitespace Issues in String-like Columns ---
        string_cols = [
            col for col, details in column_details.items() if details['decyphr_type'] in ['Categorical', 'Text (High Cardinality)']
        ]

        if string_cols:
            print(f"     ... Checking {len(string_cols)} text/categorical columns for whitespace.")
            for col_name in string_cols:
                # Check for leading whitespace
                leading_whitespace_count = ddf[col_name].str.startswith(' ').sum()
                # Check for trailing whitespace
                trailing_whitespace_count = ddf[col_name].str.endswith(' ').sum()

                # Compute both counts in a single pass for this column
                leading_count, trailing_count = dd.compute(leading_whitespace_count, trailing_whitespace_count)

                if leading_count > 0 or trailing_count > 0:
                    results["whitespace_issues"].append({
                        "column": col_name,
                        "leading_spaces": int(leading_count),
                        "trailing_spaces": int(trailing_count)
                    })
        
        # --- 3. (Future) Add checks for mixed data types, look-alikes etc. ---
        
        print("     ... Data quality scan complete.")
        return results

    except Exception as e:
        error_message = f"Failed during data quality analysis: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}