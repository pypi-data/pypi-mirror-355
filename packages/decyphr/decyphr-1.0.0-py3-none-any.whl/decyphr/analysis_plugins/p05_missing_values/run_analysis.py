# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p05_missing_values/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin analyzes the entire dataset to identify and quantify
#          missing values in each column.

import dask.dataframe as dd
from typing import Dict, Any, Optional

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes each column in the dataframe for missing (null) values.

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results from the p01_overview plugin,
                                           used to get the total number of rows.
        target_column (Optional[str]): The target column, ignored here.

    Returns:
        A dictionary containing the count and percentage of missing values
        for each column that has at least one missing value.
    """
    print("     -> Performing missing values scan...")

    total_rows = overview_results.get("dataset_stats", {}).get("Number of Rows")
    if not total_rows:
        return {"error": "Missing values analysis requires 'dataset_stats' from the overview plugin."}

    results: Dict[str, Any] = {}

    try:
        # Calculate the sum of nulls for all columns in a single, efficient pass.
        # This returns a Dask Series.
        missing_counts_series = ddf.isnull().sum()
        
        # Now, compute the result.
        missing_counts = missing_counts_series.compute()

        # Filter to include only columns that have one or more missing values.
        columns_with_missing = missing_counts[missing_counts > 0]

        if columns_with_missing.empty:
            print("     ... No missing values found in the dataset. Excellent!")
            return {"message": "No missing values found."}

        print(f"     ... Found {len(columns_with_missing)} column(s) with missing values.")

        for col_name, count in columns_with_missing.items():
            count = int(count) # Ensure count is a standard Python int
            percentage = round(count / total_rows * 100, 2)
            results[col_name] = {
                "missing_count": count,
                "missing_percentage": percentage
            }

        print("     ... Missing values scan complete.")
        return results

    except Exception as e:
        error_message = f"Failed during missing values analysis: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}