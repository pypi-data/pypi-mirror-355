# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p04_advanced_outliers/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates visualizations and detailed HTML tables for the
#          outlier analysis results.

import plotly.graph_objects as go
from typing import Dict, Any, Optional, List

# Define consistent colors and templates for the dark theme
THEME_COLORS = {
    "background": "#0f0f1a",
    "plot_background": "#1e293b",
    "text": "#ffffff",
    "grid": "#4a4a58",
    "primary_accent": "#1f77b4"
}

def _create_outlier_details_html(col_name: str, stats: Dict[str, float]) -> str:
    """Generates a detailed HTML summary table for a column's outlier analysis."""
    html = f"<div class='details-card-columnar'><h4><code>{col_name}</code>: Outlier Summary (IQR)</h4>"
    html += "<table class='details-table'>"
    html += "<tr><th>Metric</th><th>Value</th></tr>"
    html += f"<tr><td>Lower Bound</td><td>{stats.get('lower_bound', 0):,.2f}</td></tr>"
    html += f"<tr><td>Upper Bound</td><td>{stats.get('upper_bound', 0):,.2f}</td></tr>"
    html += f"<tr><td>Total Outliers</td><td>{stats.get('total_outliers', 0):,}</td></tr>"
    html += f"<tr><td>Percentage</td><td>{stats.get('percentage_outliers', 0):.2f}%</td></tr>"
    html += "</table></div>"
    return html


def create_visuals(ddf, analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates Plotly box plots and detailed HTML tables for outlier analysis.

    Args:
        ddf: The Dask DataFrame, needed to get the raw data for plotting.
        analysis_results (Dict[str, Any]): The results from p04_advanced_outliers/run_analysis.py.

    Returns:
        A dictionary containing the generated HTML and a list of Plotly figures.
    """
    print("     -> Generating details & visualizations for outlier analysis...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "No numeric columns suitable for outlier analysis."}

    all_details_html: List[str] = []
    all_visuals: List[go.Figure] = []

    try:
        # Loop through each column that has outlier analysis results
        for col_name, stats in analysis_results.items():
            if not isinstance(stats, dict):
                continue

            print(f"        - Creating details & box plot for '{col_name}'")
            # 1. Create the detailed HTML table
            all_details_html.append(_create_outlier_details_html(col_name, stats))

            # 2. Create the box plot visualization
            fig = go.Figure(data=[go.Box(
                y=ddf[col_name].compute(),
                name=col_name,
                marker_color=THEME_COLORS["primary_accent"],
                boxpoints='outliers',
                jitter=0.3
            )])
            
            fig.update_layout(
                title_text=f'Outlier Analysis for {col_name}',
                margin=dict(l=20, r=20, t=40, b=20)
            )
            all_visuals.append(fig)

        if not all_visuals:
            return {"message": "No valid outlier results to visualize."}

        final_html = f"<div class='details-grid-univariate'>{''.join(all_details_html)}</div>"
            
        print("     ... Details and visualizations for outlier analysis complete.")
        return {
            "details_html": final_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during outlier visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}