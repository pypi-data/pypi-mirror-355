# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p05_missing_values/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates visualizations and a detailed HTML table for the
#          missing values analysis.

import plotly.graph_objects as go
from typing import Dict, Any, Optional, List

# Define consistent colors and templates for the dark theme
THEME_COLORS = {
    "background": "#0f0f1a",
    "plot_background": "#1e293b",
    "text": "#ffffff",
    "grid": "#4a4a58",
    "primary_accent": "#d62728" # A distinct red for warnings/missing data
}

def _create_missing_details_html(analysis_results: Dict[str, Any]) -> str:
    """Generates a detailed HTML table for columns with missing values."""
    html = "<div class='details-card'><h4>Missing Values Summary</h4>"
    html += "<p>The following columns were found to have missing (null) values. This can impact data quality and model performance.</p>"
    html += "<table class='details-table'>"
    html += "<tr><th>Column Name</th><th>Missing Count</th><th>Missing Percentage</th></tr>"
    
    # Sort columns by percentage descending for the table
    sorted_columns = sorted(
        analysis_results.items(),
        key=lambda item: item[1]['missing_percentage'],
        reverse=True
    )

    for col_name, details in sorted_columns:
        html += f"<tr><td><code>{col_name}</code></td><td>{details['missing_count']:,}</td><td>{details['missing_percentage']:.2f}%</td></tr>"
    
    html += "</table></div>"
    return html


def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates a Plotly bar chart and a detailed HTML table for missing values.

    Args:
        analysis_results (Dict[str, Any]): The results from p05_missing_values/run_analysis.py.

    Returns:
        A dictionary containing the generated HTML and a list of Plotly figures.
    """
    print("     -> Generating details & visualizations for missing values analysis...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "No missing values found in the dataset."}

    all_visuals: List[go.Figure] = []

    try:
        # --- 1. Create the detailed HTML table ---
        details_html = _create_missing_details_html(analysis_results)

        # --- 2. Create the summary bar chart ---
        sorted_columns = sorted(
            analysis_results.items(),
            key=lambda item: item[1]['missing_percentage'],
            reverse=True
        )
        col_names = [item[0] for item in sorted_columns]
        percentages = [item[1]['missing_percentage'] for item in sorted_columns]

        fig = go.Figure(data=[go.Bar(
            x=percentages,
            y=col_names,
            orientation='h',
            marker_color=THEME_COLORS["primary_accent"]
        )])
        
        fig.update_layout(
            title_text='Percentage of Missing Values per Column',
            xaxis_title_text='Percentage Missing (%)',
            yaxis={'autorange': 'reversed'},
            margin=dict(l=20, r=20, t=40, b=20)
        )
        all_visuals.append(fig)

        print("     ... Details and visualizations for missing values complete.")
        return {
            "details_html": details_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during missing values visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}