# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p06_correlations/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin calculates correlation matrices to understand the
#          relationships between variables in the dataset. (VERSION 2.0: Perf. Upgrade)

import dask.dataframe as dd
import pandas as pd
from typing import Dict, Any, Optional, List
from phik import phik_matrix
import warnings

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculates Pearson (linear) and Phik (non-linear, all types) correlations.

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results from the p01_overview plugin.
        target_column (Optional[str]): The target column, ignored here.

    Returns:
        A dictionary containing the calculated correlation matrices as pandas DataFrames.
    """
    print("     -> Performing correlation analysis (Pearson, Phik)...")

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Correlation analysis requires 'column_details' from the overview plugin."}

    results: Dict[str, pd.DataFrame] = {}

    try:
        # --- 1. Pearson Correlation for Numeric Columns ---
        numeric_cols: List[str] = [
            col for col, details in column_details.items() if details['decyphr_type'] == 'Numeric'
        ]

        if len(numeric_cols) > 1:
            print(f"     ... Calculating Pearson correlation for {len(numeric_cols)} numeric columns.")
            pearson_corr = ddf[numeric_cols].corr().compute()
            results["pearson_correlation"] = pearson_corr
        else:
            print("     ... Skipping Pearson correlation, not enough numeric columns.")

        # --- 2. Phik (φk) Correlation with High Cardinality Exclusion ---
        total_rows = overview_results.get("dataset_stats", {}).get("Number of Rows", 0)
        SAMPLE_SIZE = 50000

        # CORRECTED: Intelligently select columns for Phik analysis
        # Exclude high-cardinality text and ID columns to prevent performance bottlenecks.
        cols_to_exclude = {
            col for col, details in column_details.items() 
            if details['decyphr_type'] in ["Unique ID", "Text (High Cardinality)"]
        }
        phik_cols = [col for col in ddf.columns if col not in cols_to_exclude]
        
        if len(cols_to_exclude) > 0:
            print(f"     ... Excluding {len(cols_to_exclude)} high-cardinality columns from Phik analysis for performance.")

        print(f"     ... Calculating Phik correlation on a sample of the data.")
        if total_rows > SAMPLE_SIZE:
            print(f"         (Dataset is large, using a random sample of {SAMPLE_SIZE} rows)")
            sampled_df = ddf[phik_cols].sample(frac=SAMPLE_SIZE/total_rows, random_state=42).compute()
        else:
            sampled_df = ddf[phik_cols].compute()

        interval_cols = [col for col in numeric_cols if col in phik_cols]
        
        # Suppress the UserWarnings from phik itself since we are now handling this logic
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            phik_corr = sampled_df.phik_matrix(interval_cols=interval_cols)
        
        results["phik_correlation"] = phik_corr

        print("     ... Correlation analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during correlation analysis: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}