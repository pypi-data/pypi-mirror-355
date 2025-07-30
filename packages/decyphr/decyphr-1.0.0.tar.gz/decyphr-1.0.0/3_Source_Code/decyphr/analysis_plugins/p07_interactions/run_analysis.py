# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p07_interactions/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin identifies and suggests potentially valuable feature
#          interactions for use in feature engineering.

import dask.dataframe as dd
from typing import Dict, Any, Optional, List
from itertools import combinations

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Identifies and suggests potential interaction features.

    It uses heuristics to suggest interactions between:
    1. The most variant numeric features.
    2. The most frequent categorical features.

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results from the p01_overview plugin.
        target_column (Optional[str]): The target column, currently ignored but could be
                                       used for more advanced suggestions in the future.

    Returns:
        A dictionary containing lists of suggested interaction features.
    """
    print("     -> Identifying potential feature interactions...")

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Feature interaction analysis requires 'column_details' from the overview plugin."}

    results: Dict[str, List[str]] = {
        "suggested_numeric_interactions": [],
        "suggested_categorical_interactions": [],
    }
    
    # Define how many top features to consider for interactions
    TOP_N_FEATURES = 5

    try:
        # --- 1. Suggest Interactions for Numeric Columns ---
        numeric_cols: List[str] = [
            col for col, details in column_details.items() if details['decyphr_type'] == 'Numeric'
        ]

        if len(numeric_cols) >= 2:
            print(f"     ... Analyzing {len(numeric_cols)} numeric columns for interactions.")
            # Heuristic: Find the most variant columns, as they often contain more information.
            # We calculate normalized variance (coefficient of variation) to compare columns on different scales.
            variances = (ddf[numeric_cols].std() / ddf[numeric_cols].mean()).abs().compute()
            top_numeric_cols = variances.nlargest(TOP_N_FEATURES).index.tolist()

            # Generate all pairs of the top N columns
            if len(top_numeric_cols) >= 2:
                numeric_pairs = combinations(top_numeric_cols, 2)
                results["suggested_numeric_interactions"] = [f"{p[0]} * {p[1]}" for p in numeric_pairs]

        # --- 2. Suggest Interactions for Categorical Columns ---
        categorical_cols: List[str] = [
            col for col, details in column_details.items() if details['decyphr_type'] in ['Categorical', 'Boolean']
        ]

        if len(categorical_cols) >= 2:
            print(f"     ... Analyzing {len(categorical_cols)} categorical columns for interactions.")
            # Heuristic: Interact columns with low cardinality, as high-cardinality
            # interactions can lead to an explosion of features.
            # We will use the top N with the fewest categories.
            n_uniques = ddf[categorical_cols].nunique().compute()
            top_categorical_cols = n_uniques.nsmallest(TOP_N_FEATURES).index.tolist()

            if len(top_categorical_cols) >= 2:
                categorical_pairs = combinations(top_categorical_cols, 2)
                results["suggested_categorical_interactions"] = [f"{p[0]} & {p[1]}" for p in categorical_pairs]

        # --- 3. (Future) Suggest Numeric-Categorical Interactions ---
        # This could involve suggesting group-by statistics.

        if not results["suggested_numeric_interactions"] and not results["suggested_categorical_interactions"]:
             print("     ... Not enough suitable columns to suggest interactions.")
             return {"message": "Not enough features to suggest interactions."}

        print("     ... Feature interaction analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during feature interaction analysis: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}