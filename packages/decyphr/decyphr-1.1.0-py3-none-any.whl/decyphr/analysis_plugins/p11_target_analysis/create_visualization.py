# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p11_target_analysis/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates a feature importance plot and explanatory text
#          based on the results of the baseline model.

import plotly.graph_objects as go
from typing import Dict, Any, Optional, List

# Define consistent colors and templates for the dark theme
THEME_COLORS = {
    "background": "#0f0f1a",
    "plot_background": "#1e293b",
    "text": "#ffffff",
    "grid": "#4a4a58",
    "primary_accent": "#2ca02c", # A distinct green for importance
}

def _create_target_analysis_details_html(problem_type: str) -> str:
    """Generates an introductory HTML block explaining feature importance."""
    
    intro_html = "<div class='details-card-full'>"
    intro_html += "<h4>Understanding Feature Importance</h4>"
    intro_html += f"""
        <p>
            When a target variable is specified, Decyphr automatically trains a baseline LightGBM model to understand which features are most predictive. Feature importance scores estimate how valuable each feature is for making accurate predictions. A higher score indicates a stronger influence on the model's decisions.
        </p>
        <p>
            This analysis detected a <strong>{problem_type}</strong> problem. The chart below shows the top features ranked by their importance score. These features are likely the most influential drivers in your dataset and are excellent candidates for further investigation and model building.
        </p>
    """
    intro_html += "</div>"
    return intro_html


def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates a Plotly bar chart and detailed HTML for feature importances.

    Args:
        analysis_results (Dict[str, Any]): The results from p11_target_analysis/run_analysis.py.

    Returns:
        A dictionary containing the generated HTML and a list of Plotly figures.
    """
    print("     -> Generating details & visualizations for target analysis...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "Target analysis was not performed."}

    try:
        importances = analysis_results.get("feature_importances", {})
        problem_type = analysis_results.get("problem_type", "Target")

        if not importances:
            return {"message": "No feature importances were calculated."}

        # --- 1. Create the detailed HTML content ---
        details_html = _create_target_analysis_details_html(problem_type)

        # --- 2. Create the feature importance bar chart ---
        # The importances are already sorted ascendingly in the analysis step
        feature_names = list(importances.keys())
        importance_values = list(importances.values())

        fig = go.Figure(data=[go.Bar(
            y=feature_names,
            x=importance_values,
            orientation='h',
            marker_color=THEME_COLORS["primary_accent"],
            hovertemplate='<b>%{y}</b><br>Importance: %{x}<extra></extra>'
        )])
        
        fig.update_layout(
            title_text=f'Top Feature Importances for Predicting "{problem_type}"',
            xaxis_title_text='Importance Score (from LightGBM model)',
            yaxis_title_text='Feature',
            margin=dict(l=40, r=20, t=60, b=40)
        )
        
        print("     ... Details and visualization for feature importance complete.")
        
        return {
            "details_html": details_html,
            "visuals": [fig]
        }

    except Exception as e:
        error_message = f"Failed during feature importance visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}