# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p13_data_drift/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin quantifies data drift between two datasets by comparing
#          the distribution of each common feature.

import dask.dataframe as dd
import pandas as pd
import numpy as np
from scipy.stats import ks_2samp
from typing import Dict, Any, Optional, List

def _calculate_psi(expected: pd.Series, actual: pd.Series, buckets: int = 10) -> float:
    """Helper function to calculate the Population Stability Index (PSI)."""
    
    # For numeric data, create bins. For categorical, use categories as bins.
    if pd.api.types.is_numeric_dtype(expected):
        breakpoints = np.arange(0, buckets + 1) / (buckets) * 100
        breakpoints = np.percentile(expected, breakpoints)
        expected_bins = pd.cut(expected, bins=breakpoints, duplicates='drop')
        actual_bins = pd.cut(actual, bins=breakpoints, duplicates='drop')
    else:
        expected_bins = expected
        actual_bins = actual

    df_expected = pd.DataFrame({'expected': expected_bins.value_counts() / len(expected)})
    df_actual = pd.DataFrame({'actual': actual_bins.value_counts() / len(actual)})
    
    psi_df = df_expected.join(df_actual, how='outer').fillna(0.0001) # Avoid division by zero
    
    psi_df['psi'] = (psi_df['actual'] - psi_df['expected']) * np.log(psi_df['actual'] / psi_df['expected'])
    
    return psi_df['psi'].sum()

def analyze(
    ddf_base: dd.DataFrame, 
    ddf_current: dd.DataFrame, 
    overview_results_base: Dict[str, Any],
    overview_results_current: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyzes data drift between a base and a current dataframe.

    Args:
        ddf_base (dd.DataFrame): The baseline/reference Dask DataFrame.
        ddf_current (dd.DataFrame): The current Dask DataFrame to compare.
        overview_results_base (Dict[str, Any]): The overview results for the base dataframe.
        overview_results_current (Dict[str, Any]): The overview results for the current dataframe.

    Returns:
        A dictionary summarizing the drift analysis for each common column.
    """
    print("     -> Performing data drift analysis (K-S Test, PSI)...")

    base_cols = overview_results_base.get("column_details", {})
    current_cols = overview_results_current.get("column_details", {})
    
    common_cols = list(set(base_cols.keys()) & set(current_cols.keys()))
    if not common_cols:
        return {"error": "No common columns found between the two datasets."}
        
    results: Dict[str, Any] = {}
    
    try:
        # Drift analysis requires computed data.
        print("     ... Computing dataframes for drift analysis.")
        df_base_computed = ddf_base[common_cols].compute()
        df_current_computed = ddf_current[common_cols].compute()

        for col_name in common_cols:
            base_type = base_cols[col_name]['decyphr_type']
            
            # --- 1. Kolmogorov-Smirnov (K-S) Test for Numeric Drift ---
            if base_type == 'Numeric':
                ks_stat, p_value = ks_2samp(
                    df_base_computed[col_name].dropna(), 
                    df_current_computed[col_name].dropna()
                )
                results[col_name] = {
                    "type": "Numeric Drift (K-S Test)",
                    "statistic": round(ks_stat, 4),
                    "p_value": round(p_value, 4)
                }
            
            # --- 2. Population Stability Index (PSI) for Categorical Drift ---
            elif base_type in ['Categorical', 'Categorical (Numeric)', 'Boolean']:
                psi = _calculate_psi(
                    df_base_computed[col_name].dropna(), 
                    df_current_computed[col_name].dropna()
                )
                results[col_name] = {
                    "type": "Categorical Drift (PSI)",
                    "psi_value": round(psi, 4)
                }
        
        print("     ... Data drift analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during data drift analysis: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}