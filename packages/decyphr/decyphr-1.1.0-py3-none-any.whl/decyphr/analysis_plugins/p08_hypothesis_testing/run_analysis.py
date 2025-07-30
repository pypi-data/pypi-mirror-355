# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p08_hypothesis_testing/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs formal statistical hypothesis tests to uncover
#          significant relationships between variables.

import dask.dataframe as dd
import pandas as pd
from scipy import stats
from typing import Dict, Any, Optional, List
from itertools import combinations

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs hypothesis tests (Chi-Squared, T-Test/ANOVA) on the data.

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results from the p01_overview plugin.
        target_column (Optional[str]): The target column, currently ignored.

    Returns:
        A dictionary containing the results of the statistical tests performed.
    """
    print("     -> Performing hypothesis testing (Chi-Squared, T-Test, ANOVA)...")

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Hypothesis testing requires 'column_details' from the overview plugin."}

    results: Dict[str, List[Dict[str, Any]]] = {
        "chi_squared_tests": [],
        "mean_comparison_tests": [], # For T-Tests and ANOVA
    }
    
    # Statistical tests are often memory intensive and require computed data.
    # We will work on a computed sample for performance and compatibility.
    total_rows = overview_results.get("dataset_stats", {}).get("Number of Rows", 0)
    SAMPLE_SIZE = 20000
    
    print(f"     ... Using a sample of up to {SAMPLE_SIZE} rows for testing.")
    if total_rows > SAMPLE_SIZE:
        sampled_df = ddf.sample(frac=SAMPLE_SIZE/total_rows, random_state=42).compute()
    else:
        sampled_df = ddf.compute()

    try:
        # --- 1. Chi-Squared Test for Independence (Categorical vs. Categorical) ---
        categorical_cols: List[str] = [
            col for col, details in column_details.items() if details['decyphr_type'] in ['Categorical', 'Boolean']
        ]

        if len(categorical_cols) >= 2:
            print(f"     ... Running Chi-Squared tests on {len(categorical_cols)} categorical columns.")
            for col1, col2 in combinations(categorical_cols, 2):
                contingency_table = pd.crosstab(sampled_df[col1], sampled_df[col2])
                chi2, p, dof, ex = stats.chi2_contingency(contingency_table)
                results["chi_squared_tests"].append({
                    "variables": [col1, col2],
                    "statistic": round(chi2, 4),
                    "p_value": round(p, 4)
                })

        # --- 2. T-Test / ANOVA (Numeric vs. Categorical) ---
        numeric_cols: List[str] = [
            col for col, details in column_details.items() if details['decyphr_type'] == 'Numeric'
        ]

        if numeric_cols and categorical_cols:
            print(f"     ... Running T-Tests/ANOVA on numeric/categorical pairs.")
            for num_col in numeric_cols:
                for cat_col in categorical_cols:
                    groups = sampled_df.groupby(cat_col)[num_col].apply(list)
                    
                    if len(groups) == 2: # T-Test for 2 groups
                        stat, p = stats.ttest_ind(*groups)
                        test_type = "T-Test"
                    elif len(groups) > 2: # ANOVA for >2 groups
                        stat, p = stats.f_oneway(*groups)
                        test_type = "ANOVA"
                    else:
                        continue # Not enough groups to compare

                    results["mean_comparison_tests"].append({
                        "numeric_variable": num_col,
                        "categorical_variable": cat_col,
                        "test_type": test_type,
                        "statistic": round(stat, 4),
                        "p_value": round(p, 4)
                    })

        if not results["chi_squared_tests"] and not results["mean_comparison_tests"]:
             print("     ... Not enough suitable columns for hypothesis testing.")
             return {"message": "Not enough features for hypothesis testing."}
        
        print("     ... Hypothesis testing complete.")
        return results

    except Exception as e:
        error_message = f"Failed during hypothesis testing: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}