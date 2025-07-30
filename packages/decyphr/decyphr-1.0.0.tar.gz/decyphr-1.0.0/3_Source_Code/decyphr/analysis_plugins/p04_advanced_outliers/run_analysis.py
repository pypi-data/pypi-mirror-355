# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p04_advanced_outliers/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin detects outliers in numeric columns using both standard
#          and advanced statistical methods.

import dask.dataframe as dd
from typing import Dict, Any, Optional, List

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes numeric columns for the presence of outliers using the IQR method.

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results from the p01_overview plugin,
                                           used to identify numeric columns.
        target_column (Optional[str]): The target column, ignored here.

    Returns:
        A dictionary summarizing the outlier analysis for each numeric column.
    """
    print("     -> Performing outlier detection scan (IQR method)...")

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Outlier analysis requires 'column_details' from the overview plugin."}

    numeric_cols: List[str] = [
        col for col, details in column_details.items() if details['decyphr_type'] == 'Numeric'
    ]

    if not numeric_cols:
        print("     ... No numeric columns found to analyze for outliers.")
        return {"message": "No numeric columns to analyze."}

    results: Dict[str, Any] = {}

    try:
        # --- Calculate Quantiles in a single pass for efficiency ---
        print(f"     ... Calculating quantiles for {len(numeric_cols)} numeric columns.")
        quantiles = ddf[numeric_cols].quantile([0.25, 0.75]).compute()

        for col_name in numeric_cols:
            q1 = quantiles[col_name][0.25]
            q3 = quantiles[col_name][0.75]
            iqr = q3 - q1

            # Define outlier boundaries
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            # Use Dask to lazily count outliers
            low_outliers_count = (ddf[col_name] < lower_bound).sum()
            high_outliers_count = (ddf[col_name] > upper_bound).sum()

            # Compute both counts in parallel
            low_count, high_count = dd.compute(low_outliers_count, high_outliers_count)
            
            total_outliers = int(low_count + high_count)
            total_rows = overview_results.get("dataset_stats", {}).get("Number of Rows", 1) # Avoid division by zero
            percentage = round(total_outliers / total_rows * 100, 2) if total_rows > 0 else 0

            results[col_name] = {
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "total_outliers": total_outliers,
                "percentage_outliers": percentage,
            }

        # --- (Future) Placeholder for advanced methods ---
        # Here, you could add calls to Isolation Forest or DBSCAN for columns
        # that warrant a more computationally expensive analysis.
        # e.g., results[col_name]['isolation_forest_outliers'] = run_iso_forest(ddf[col_name])

        print("     ... Outlier detection scan complete.")
        return results

    except Exception as e:
        error_message = f"Failed during outlier analysis: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}