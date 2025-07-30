# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p15_timeseries/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates visualizations and detailed HTML content for the
#          time-series analysis results.

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any, Optional, List

# Define consistent colors and templates for the dark theme
THEME_COLORS = {
    "background": "#0f0f1a",
    "plot_background": "#1e293b",
    "text": "#ffffff",
    "grid": "#4a4a58",
    "primary_accent": "#00D2FF",  # A cyan accent for time-series
}
P_VALUE_THRESHOLD = 0.05

def _create_timeseries_details_html(analysis_results: Dict[str, Any]) -> str:
    """Generates an intro text block and a stationarity results table."""
    
    stationarity_test = analysis_results.get("stationarity_test", {})
    p_value = stationarity_test.get("p_value", 1.0)
    is_stationary = p_value < P_VALUE_THRESHOLD

    intro_html = "<div class='details-card-full'>"
    intro_html += "<h4>Understanding Time-Series Analysis</h4>"
    intro_html += """
        <p>
            Time-series analysis involves examining data points collected over a period of time. This section decomposes the primary time-series into its core components and tests for stationarity.
        </p>
        <ul>
            <li><strong>Decomposition:</strong> Breaks the series down into Trend (the long-term direction), Seasonality (repeating short-term cycles), and Residuals (random noise).</li>
            <li><strong>Stationarity (ADF Test):</strong> A stationary series is one whose statistical properties (like mean and variance) do not change over time. Many advanced forecasting models require a series to be stationary. A low p-value (&lt; 0.05) from the Augmented Dickey-Fuller (ADF) test indicates the series is likely stationary.</li>
        </ul>
    """
    intro_html += "</div>"
    
    # Fix f-string nesting issue by extracting values first
    status_text = "STATIONARY" if is_stationary else "NON-STATIONARY"
    status_color = "#39FF14" if is_stationary else "#d62728"

    table_html = "<div class='details-card'><h4>Stationarity Test (ADF)</h4>"
    table_html += "<table class='details-table'>"
    table_html += "<thead><tr><th>Metric</th><th>Value</th><th>Interpretation</th></tr></thead>"
    table_html += "<tbody>"
    test_stat = stationarity_test.get('test_statistic', 'N/A')
    test_stat_str = f"{test_stat:.4f}" if isinstance(test_stat, (int, float)) else str(test_stat)
    table_html += f"<tr><td>Test Statistic</td><td>{test_stat_str}</td><td rowspan='2' style='vertical-align:middle; text-align:center; font-weight:bold; color: {status_color};'>{status_text}</td></tr>"
    table_html += f"<tr><td>P-Value</td><td>{p_value:.4f}</td></tr>"
    table_html += "</tbody></table></div>"

    return intro_html + table_html

def create_visuals(ddf, overview_results: Dict[str, Any], analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates Plotly visualizations and detailed HTML for time-series analysis.
    """
    print("     -> Generating details & visualizations for time-series analysis...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "Time-series analysis was not performed."}

    all_visuals: List[go.Figure] = []
    
    try:
        # --- 1. Create the detailed HTML content ---
        details_html = _create_timeseries_details_html(analysis_results)

        # --- 2. Create Time-Series Decomposition Plot ---
        if "decomposition" in analysis_results:
            print("        - Creating time-series decomposition plot.")
            decomp = analysis_results["decomposition"]
            
            trend = pd.Series(decomp["trend"]).rename("Trend")
            seasonal = pd.Series(decomp["seasonal"]).rename("Seasonal")
            resid = pd.Series(decomp["residual"]).rename("Residual")

            time_col = next((col for col, det in overview_results["column_details"].items() if det['decyphr_type'] == 'Datetime'), None)
            if time_col is None:
                 return {"error": "Could not find datetime column for plotting."}
            
            value_col = trend.name
            original_series = ddf[[time_col, value_col]].compute().set_index(pd.to_datetime(ddf[time_col].compute()))[value_col]

            fig = make_subplots(
                rows=4, cols=1, shared_xaxes=True,
                subplot_titles=("Original Series", "Trend Component", "Seasonal Component", "Residuals")
            )

            fig.add_trace(go.Scatter(x=original_series.index, y=original_series, mode='lines', name='Original', line=dict(color='grey')), row=1, col=1)
            fig.add_trace(go.Scatter(x=trend.index, y=trend, mode='lines', name='Trend', line=dict(color=THEME_COLORS["primary_accent"])), row=2, col=1)
            fig.add_trace(go.Scatter(x=seasonal.index, y=seasonal, mode='lines', name='Seasonal', line=dict(color='#2ca02c')), row=3, col=1)
            fig.add_trace(go.Scatter(x=resid.index, y=resid, mode='markers', name='Residuals', marker=dict(color='#d62728', size=3, opacity=0.6)), row=4, col=1)

            fig.update_layout(
                title_text='Time-Series Decomposition', showlegend=False,
                margin=dict(l=20, r=20, t=60, b=20)
            )
            all_visuals.append(fig)

        print("     ... Details and visualizations for time-series analysis complete.")
        return {
            "details_html": details_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during time-series visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}