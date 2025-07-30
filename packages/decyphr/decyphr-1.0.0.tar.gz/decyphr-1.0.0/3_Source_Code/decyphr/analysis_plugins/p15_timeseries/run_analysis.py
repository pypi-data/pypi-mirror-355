# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p15_timeseries/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs a deep analysis on time-series data, including
#          decomposition and stationarity testing.

import dask.dataframe as dd
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from typing import Dict, Any, Optional, List

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs time-series analysis on the primary datetime column.

    This analysis is only triggered if a single, clear datetime column is detected.

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results from the p01_overview plugin.
        target_column (Optional[str]): The target column, often used as the value
                                       for time-series analysis if numeric.

    Returns:
        A dictionary containing the time-series analysis results.
    """
    print("     -> Performing time-series analysis...")

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Time-series analysis requires 'column_details' from the overview plugin."}

    datetime_cols: List[str] = [
        col for col, details in column_details.items() if details['decyphr_type'] == 'Datetime'
    ]

    if len(datetime_cols) != 1:
        message = f"Skipping time-series analysis. Expected 1 datetime column, but found {len(datetime_cols)}."
        print(f"     ... {message}")
        return {"message": message}

    time_col = datetime_cols[0]
    
    # Use the target column as the value to analyze. If no target, use the first numeric column.
    if target_column and column_details.get(target_column, {}).get('decyphr_type') == 'Numeric':
        value_col = target_column
    else:
        # Find first numeric column as a fallback
        value_col = next((col for col, det in column_details.items() if det['decyphr_type'] == 'Numeric'), None)
    
    if not value_col:
        message = "Skipping time-series analysis. No suitable numeric column found to analyze."
        print(f"     ... {message}")
        return {"message": message}

    print(f"     ... Analyzing time-series for '{value_col}' against time column '{time_col}'.")
    
    results: Dict[str, Any] = {}
    
    try:
        # Time-series analysis requires a sorted pandas DataFrame with a DatetimeIndex
        ts_df = ddf[[time_col, value_col]].compute()
        ts_df[time_col] = pd.to_datetime(ts_df[time_col])
        ts_df = ts_df.set_index(time_col).sort_index()

        # Resample to a consistent frequency (daily), filling missing values
        # This is crucial for decomposition and other statsmodels functions.
        ts_resampled = ts_df[value_col].resample('D').mean().fillna(method='ffill').dropna()

        if len(ts_resampled) < 365 * 2: # Require at least two years of data for seasonal decomposition
             print("     ... Not enough data for seasonal decomposition, performing basic tests.")
        else:
            # --- 1. Time-Series Decomposition ---
            decomposition = seasonal_decompose(ts_resampled, model='additive', period=365)
            # Store components as dictionaries for JSON compatibility
            results["decomposition"] = {
                "trend": decomposition.trend.dropna().to_dict(),
                "seasonal": decomposition.seasonal.dropna().to_dict(),
                "residual": decomposition.resid.dropna().to_dict(),
            }

        # --- 2. Stationarity Test (Augmented Dickey-Fuller) ---
        adf_test_result = adfuller(ts_resampled)
        results["stationarity_test"] = {
            "test_statistic": round(adf_test_result[0], 4),
            "p_value": round(adf_test_result[1], 4),
            "is_stationary": adf_test_result[1] < 0.05
        }
        
        print("     ... Time-series analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during time-series analysis: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}