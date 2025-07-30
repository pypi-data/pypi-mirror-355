# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p11_target_analysis/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs target-driven analysis, primarily by training a
#          baseline model to calculate feature importance scores.

import dask.dataframe as dd
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from typing import Dict, Any, Optional, List

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Trains a LightGBM model to determine feature importances relative to a target.

    This analysis is only triggered if a target column is specified. It automatically
    detects if the problem is classification or regression based on the target's type.

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results from the p01_overview plugin.
        target_column (Optional[str]): The target column. The analysis will not run if this is None.

    Returns:
        A dictionary containing the feature importances and the detected problem type.
    """
    print("     -> Performing target analysis (Feature Importance)...")

    if not target_column:
        message = "Skipping target analysis, no target variable was provided."
        print(f"     ... {message}")
        return {"message": message}

    column_details = overview_results.get("column_details")
    if not column_details or target_column not in column_details:
        return {"error": f"Target column '{target_column}' not found in dataset."}

    try:
        print(f"     ... Using '{target_column}' as the target variable.")

        # --- 1. Prepare Data for Modeling ---
        # Select features: use all columns except the target itself
        feature_cols = [col for col in ddf.columns if col != target_column]
        
        # For performance, compute a sample of the dataframe
        total_rows = overview_results.get("dataset_stats", {}).get("Number of Rows", 0)
        SAMPLE_SIZE = 75000
        print(f"     ... Using a sample of up to {SAMPLE_SIZE} rows for model training.")
        if total_rows > SAMPLE_SIZE:
            df_computed = ddf.sample(frac=SAMPLE_SIZE/total_rows, random_state=42).compute()
        else:
            df_computed = ddf.compute()
        
        # Basic preprocessing: one-hot encode categorical features and fill NaNs
        X = df_computed[feature_cols]
        y = df_computed[target_column]
        
        X = pd.get_dummies(X, dummy_na=True)
        # Fill any remaining NaNs (e.g., in numeric columns) with a simple median
        X = X.fillna(X.median())
        
        # --- 2. Determine Problem Type (Classification or Regression) ---
        target_details = column_details[target_column]
        problem_type = "Regression"
        if target_details['decyphr_type'] in ['Categorical', 'Categorical (Numeric)', 'Boolean']:
            problem_type = "Classification"
        
        print(f"     ... Detected problem type: {problem_type}")

        # --- 3. Train Baseline Model ---
        if problem_type == "Classification":
            model = lgb.LGBMClassifier(random_state=42, n_estimators=100)
        else: # Regression
            model = lgb.LGBMRegressor(random_state=42, n_estimators=100)
        
        model.fit(X, y)

        # --- 4. Extract Feature Importances ---
        importances = pd.Series(model.feature_importances_, index=X.columns)
        top_importances = importances.nlargest(25).sort_values(ascending=True)

        results = {
            "problem_type": problem_type,
            "feature_importances": top_importances.to_dict()
        }
        
        print("     ... Feature importance analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during target analysis: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}