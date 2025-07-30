# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p02_univariate/run_analysis.py
# ==============================================================================
# PURPOSE: This file contains the logic for univariate analysis, calculating
#          detailed statistics for each individual column (variable) in the dataset.

import dask.dataframe as dd
import pandas as pd
from typing import Dict, Any, Optional, List

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs univariate analysis on each column of the dataframe.

    It uses the pre-computed column classifications from the 'overview' plugin
    to apply the correct statistical measures to each column type (numeric vs. categorical).

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results dictionary from the p01_overview plugin.
                                           This is crucial for identifying column types.
        target_column (Optional[str]): The target column, currently ignored but kept for
                                       a consistent function signature.

    Returns:
        A dictionary containing detailed univariate statistics for each column.
    """
    print("     -> Performing univariate analysis on numeric and categorical columns...")

    # Ensure the required 'column_details' from the overview plugin are present
    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Univariate analysis requires 'column_details' from the overview plugin."}

    # --- Segregate columns by their classified type ---
    numeric_cols: List[str] = [
        col for col, details in column_details.items() if details['decyphr_type'] == 'Numeric'
    ]
    categorical_cols: List[str] = [
        col for col, details in column_details.items() if details['decyphr_type'] in ['Categorical', 'Categorical (Numeric)', 'Boolean']
    ]

    results: Dict[str, Any] = {
        "numeric_stats": {},
        "categorical_stats": {}
    }

    try:
        # --- 1. Process Numeric Columns in Parallel ---
        if numeric_cols:
            print(f"     ... Analyzing {len(numeric_cols)} numeric columns.")
            # Define standard aggregations that Dask can compute efficiently
            aggs = {
                'mean': 'mean',
                'std': 'std',
                'min': 'min',
                '25%': lambda x: x.quantile(0.25),
                '50%': lambda x: x.quantile(0.50),
                '75%': lambda x: x.quantile(0.75),
                'max': 'max',
            }
            
            # Compute standard descriptive statistics
            desc_stats = ddf[numeric_cols].agg(aggs).compute()
            
            # Skew and Kurtosis are often computed separately
            skewness = ddf[numeric_cols].skew().compute()
            kurtosis = ddf[numeric_cols].kurt().compute()

            # Structure the results neatly
            for col in numeric_cols:
                stats = desc_stats[col].to_dict()
                stats['skew'] = round(skewness[col], 4)
                stats['kurtosis'] = round(kurtosis[col], 4)
                results["numeric_stats"][col] = stats

        # --- 2. Process Categorical Columns ---
        if categorical_cols:
            print(f"     ... Analyzing {len(categorical_cols)} categorical columns.")
            # For categorical data, we primarily want frequency counts.
            # It's often best to compute these one by one to manage memory if
            # one column has many categories.
            for col in categorical_cols:
                # Get the value counts and limit to the top 20 for reporting
                # to prevent excessively large result objects.
                value_counts = ddf[col].value_counts().compute().nlargest(20)
                results["categorical_stats"][col] = {
                    "value_counts": value_counts.to_dict(),
                    "total_unique": column_details[col].get('nunique', len(value_counts)) # Placeholder
                }
        
        print("     ... Univariate analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during univariate analysis: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}