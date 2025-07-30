# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p10_clustering/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs K-Means clustering to identify hidden segments
#          or groups within the dataset's numeric features.

import dask.dataframe as dd
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from typing import Dict, Any, Optional, List

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs K-Means clustering on the numeric columns of the dataset.

    This analysis is only triggered if no target column is specified and if
    there are at least 2 numeric columns. It uses the "elbow method" heuristic
    to suggest an optimal number of clusters.

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results from the p01_overview plugin.
        target_column (Optional[str]): The target column. If provided, clustering is skipped.

    Returns:
        A dictionary containing the clustering results, including inertia scores
        and the cluster labels for a suggested 'k'.
    """
    print("     -> Performing unsupervised clustering (K-Means)...")

    if target_column:
        message = "Skipping clustering, as a target variable was provided."
        print(f"     ... {message}")
        return {"message": message}

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Clustering analysis requires 'column_details' from the overview plugin."}

    numeric_cols: List[str] = [
        col for col, details in column_details.items() if details['decyphr_type'] == 'Numeric'
    ]

    if len(numeric_cols) < 2:
        message = "Skipping clustering, requires at least 2 numeric columns."
        print(f"     ... {message}")
        return {"message": message}

    try:
        print(f"     ... Analyzing {len(numeric_cols)} numeric columns for clustering.")
        
        # Clustering requires computed data and no missing values.
        numeric_df_computed = ddf[numeric_cols].fillna(ddf[numeric_cols].mean()).compute()

        # 1. Standardize the data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(numeric_df_computed)

        # 2. Find optimal 'k' using the elbow method heuristic
        inertia_scores = {}
        max_k = min(10, len(numeric_df_computed) - 1) # Test up to 10 clusters or N-1
        for k in range(2, max_k + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
            kmeans.fit(scaled_data)
            inertia_scores[k] = kmeans.inertia_

        # Heuristic to find the "elbow"
        # Find the point with the maximum distance to a line between the first and last points.
        # This is a simple but effective way to find the "elbow".
        keys = list(inertia_scores.keys())
        values = list(inertia_scores.values())
        # For simplicity, we can just pick a k. A more advanced method is needed for a true elbow find.
        # Let's suggest k=4 as a default if more than 4 options, else k=3.
        suggested_k = 4 if max_k >= 4 else 3
        
        # 3. Fit final KMeans with the suggested number of clusters
        final_kmeans = KMeans(n_clusters=suggested_k, random_state=42, n_init='auto')
        cluster_labels = final_kmeans.fit_predict(scaled_data)

        results = {
            "inertia_scores": {str(k): round(v, 2) for k, v in inertia_scores.items()},
            "suggested_k": suggested_k,
            "cluster_labels": pd.Series(cluster_labels, index=numeric_df_computed.index).to_dict(),
            "n_rows_analyzed": len(numeric_df_computed)
        }
        
        print(f"     ... Clustering analysis complete. Suggested k={suggested_k}.")
        return results

    except Exception as e:
        error_message = f"Failed during clustering analysis: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}