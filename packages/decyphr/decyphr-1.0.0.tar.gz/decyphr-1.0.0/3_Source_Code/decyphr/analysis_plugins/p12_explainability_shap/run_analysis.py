# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p12_explainability_shap/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin calculates SHAP values to provide deep, instance-level
#          explanations for the baseline model's predictions.

import dask.dataframe as dd
import pandas as pd
import lightgbm as lgb
import shap
from typing import Dict, Any, Optional, List

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculates SHAP values to explain the baseline model's predictions.

    This analysis is only triggered if a target column is specified. It requires
    retraining the baseline model from p11 to ensure data alignment.

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results from the p01_overview plugin.
        target_column (Optional[str]): The target column. Analysis is skipped if this is None.

    Returns:
        A dictionary containing the SHAP values and the feature data used.
    """
    print("     -> Performing explainability analysis (SHAP)...")

    if not target_column:
        message = "Skipping SHAP analysis, no target variable was provided."
        print(f"     ... {message}")
        return {"message": message}

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "SHAP analysis requires 'column_details' from the overview plugin."}

    try:
        print(f"     ... Preparing data and retraining baseline model for SHAP.")

        # --- 1. Prepare Data for Modeling (Consistent with p11) ---
        feature_cols = [col for col in ddf.columns if col != target_column]
        total_rows = overview_results.get("dataset_stats", {}).get("Number of Rows", 0)
        SAMPLE_SIZE = 10000  # SHAP can be slow, so a smaller sample is often better

        print(f"     ... Using a sample of up to {SAMPLE_SIZE} rows for SHAP calculation.")
        if total_rows > SAMPLE_SIZE:
            df_computed = ddf.sample(frac=SAMPLE_SIZE/total_rows, random_state=42).compute()
        else:
            df_computed = ddf.compute()

        X = df_computed[feature_cols]
        y = df_computed[target_column]

        X = pd.get_dummies(X, dummy_na=True)
        X = X.fillna(X.median())

        # --- 2. Determine Problem Type and Retrain Model ---
        problem_type = "Regression"
        if column_details[target_column]['decyphr_type'] in ['Categorical', 'Boolean']:
            problem_type = "Classification"

        if problem_type == "Classification":
            model = lgb.LGBMClassifier(random_state=42, n_estimators=100)
        else:
            model = lgb.LGBMRegressor(random_state=42, n_estimators=100)

        model.fit(X, y)

        # --- 3. Calculate SHAP Values ---
        print("     ... Calculating SHAP values. This may take a moment.")
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        # For classification, shap_values can be a list of arrays (one per class).
        # We'll typically visualize the explanations for the positive class (class 1).
        if problem_type == "Classification" and isinstance(shap_values, list):
            shap_values = shap_values[1]

        results = {
            "shap_values": shap_values,
            "feature_data": X.to_dict('list'), # Send feature data for plotting
            "feature_names": X.columns.tolist()
        }

        print("     ... SHAP analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during SHAP analysis: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}