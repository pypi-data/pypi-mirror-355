# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p06_correlations/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates interactive heatmaps and explanatory text for the
#          calculated correlation matrices.

import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, Optional, List

# Define consistent colors and templates for the dark theme
THEME_COLORS = {
    "background": "#0f0f1a",
    "plot_background": "#1e293b",
    "text": "#ffffff",
}

def _create_intro_details_html() -> str:
    """Generates an introductory HTML block explaining the correlation analyses."""
    html = "<div class='details-card-full'>"
    html += "<h4>Understanding Correlation Analysis</h4>"
    html += """
        <p>
            Correlation measures the statistical relationship between two variables. The following heatmaps visualize these relationships.
            Values range from -1 to +1, where +1 indicates a perfect positive correlation, -1 a perfect negative correlation, and 0 no correlation.
        </p>
        <ul>
            <li><strong>Pearson Correlation:</strong> Measures the <strong>linear</strong> relationship between two <strong>numeric</strong> variables. It's best at capturing simple, straight-line relationships.</li>
            <li><strong>Phik (φk) Correlation:</strong> A more advanced measure that captures both <strong>linear and non-linear</strong> relationships between variables of <strong>any type</strong> (numeric, categorical, etc.). It is generally more insightful for complex datasets.</li>
        </ul>
    """
    html += "</div>"
    return html

def _create_heatmap(corr_matrix: pd.DataFrame, title: str) -> go.Figure:
    """Helper function to create a standardized, themed heatmap."""
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale='RdBu',
        zmin=-1,
        zmax=1,
        hoverongaps=False,
        hovertemplate='Correlation between %{y} and %{x}: %{z:.3f}<extra></extra>'
    ))
    fig.update_layout(
        title_text=title,
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        yaxis_autorange='reversed',
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates Plotly heatmaps and explanatory text for the correlation matrices.

    Args:
        analysis_results (Dict[str, Any]): The results from p06_correlations/run_analysis.py.

    Returns:
        A dictionary containing the generated HTML and a list of Plotly figures.
    """
    print("     -> Generating details & visualizations for correlation analysis...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "Not enough suitable columns for correlation analysis."}

    all_visuals: List[go.Figure] = []

    try:
        # --- Create Pearson Correlation Heatmap ---
        if "pearson_correlation" in analysis_results:
            print("        - Creating Pearson correlation heatmap.")
            pearson_matrix = analysis_results["pearson_correlation"]
            fig_pearson = _create_heatmap(pearson_matrix, "Pearson Correlation (Linear, Numeric Only)")
            all_visuals.append(fig_pearson)

        # --- Create Phik (φk) Correlation Heatmap ---
        if "phik_correlation" in analysis_results:
            print("        - Creating Phik (φk) correlation heatmap.")
            phik_matrix = analysis_results["phik_correlation"]
            fig_phik = _create_heatmap(phik_matrix, "Phik (φk) Correlation (Non-linear, All Variable Types)")
            all_visuals.append(fig_phik)

        if not all_visuals:
            return {"message": "No correlation matrices found to visualize."}
            
        details_html = _create_intro_details_html()

        print("     ... Details and visualizations for correlation analysis complete.")
        return {
            "details_html": details_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during correlation visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}