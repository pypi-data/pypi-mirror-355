# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p09_pca/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs Principal Component Analysis (PCA) to provide
#          insights into dimensionality reduction possibilities.

import dask.dataframe as dd
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from typing import Dict, Any, Optional, List

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs PCA on the numeric columns of the dataset.

    The analysis is only triggered if there are 2 or more numeric columns.
    It standardizes the data before applying PCA to ensure fair contribution
    from all variables.

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results from the p01_overview plugin.
        target_column (Optional[str]): The target column, ignored here.

    Returns:
        A dictionary containing the PCA results, including explained variance ratios.
    """
    print("     -> Performing Principal Component Analysis (PCA)...")

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "PCA analysis requires 'column_details' from the overview plugin."}

    numeric_cols: List[str] = [
        col for col, details in column_details.items() if details['decyphr_type'] == 'Numeric'
    ]

    # PCA is only meaningful with at least 2 numeric columns
    if len(numeric_cols) < 2:
        message = "Skipping PCA, requires at least 2 numeric columns."
        print(f"     ... {message}")
        return {"message": message}

    results: Dict[str, Any] = {}

    try:
        print(f"     ... Analyzing {len(numeric_cols)} numeric columns for PCA.")
        
        # PCA requires computed data. We will work on the numeric subset.
        # We also need to handle missing values for PCA to work. We'll fill with the mean.
        numeric_df_computed = ddf[numeric_cols].fillna(ddf[numeric_cols].mean()).compute()

        # 1. Standardize the data (scaling to zero mean and unit variance)
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(numeric_df_computed)

        # 2. Apply PCA
        # We fit PCA with all possible components to analyze the variance explained by each.
        pca = PCA(n_components=len(numeric_cols))
        pca.fit(scaled_data)

        # 3. Extract results
        explained_variance_ratio = pca.explained_variance_ratio_.tolist()
        cumulative_variance = explained_variance_ratio.copy()
        for i in range(1, len(cumulative_variance)):
            cumulative_variance[i] += cumulative_variance[i-1]

        results = {
            "explained_variance_ratio": [round(x, 4) for x in explained_variance_ratio],
            "cumulative_variance_ratio": [round(x, 4) for x in cumulative_variance],
            "n_components": len(numeric_cols),
        }
        
        print("     ... PCA analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during PCA analysis: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}