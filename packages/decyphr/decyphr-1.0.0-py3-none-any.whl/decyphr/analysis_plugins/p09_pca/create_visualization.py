# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p09_pca/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates a detailed HTML summary and an interactive scree
#          plot to visualize the results of the Principal Component Analysis (PCA).

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, Optional, List

# Define consistent colors and templates for the dark theme
THEME_COLORS = {
    "background": "#0f0f1a",
    "plot_background": "#1e293b",
    "text": "#ffffff",
    "grid": "#4a4a58",
    "bar_color": "#1f77b4",
    "line_color": "#ff7f0e",
}

def _create_pca_details_html(analysis_results: Dict[str, Any]) -> str:
    """Generates an introductory text block and a summary table for PCA results."""
    
    explained_variance = analysis_results.get("explained_variance_ratio", [])
    cumulative_variance = analysis_results.get("cumulative_variance_ratio", [])

    intro_html = "<div class='details-card-full'>"
    intro_html += "<h4>Understanding Principal Component Analysis (PCA)</h4>"
    intro_html += """
        <p>
            PCA is a dimensionality reduction technique used to transform a large set of variables into a smaller set of new variables called "Principal Components" while preserving most of the original information. It's useful for visualization and for improving the performance of machine learning models on high-dimensional data.
        </p>
        <p>
            The <strong>scree plot</strong> below shows how much information (variance) each principal component captures. The "elbow point" of the orange cumulative line is often used to suggest how many components to keep.
        </p>
    """
    intro_html += "</div>"
    
    table_html = "<div class='details-card'><h4>Explained Variance Summary</h4>"
    table_html += "<table class='details-table'>"
    table_html += "<thead><tr><th>Principal Component</th><th>Individual Variance</th><th>Cumulative Variance</th></tr></thead>"
    table_html += "<tbody>"
    for i, (ind_var, cum_var) in enumerate(zip(explained_variance, cumulative_variance)):
        table_html += f"<tr><td>PC{i+1}</td><td>{ind_var:.2%}</td><td>{cum_var:.2%}</td></tr>"
    table_html += "</tbody></table></div>"

    return intro_html + table_html


def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates a Plotly scree plot and detailed HTML content for the PCA results.

    Args:
        analysis_results (Dict[str, Any]): The results from p09_pca/run_analysis.py.

    Returns:
        A dictionary containing the generated HTML and a list of Plotly figures.
    """
    print("     -> Generating details & visualizations for PCA results...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "Not enough numeric columns for PCA."}

    try:
        explained_variance = analysis_results.get("explained_variance_ratio", [])
        cumulative_variance = analysis_results.get("cumulative_variance_ratio", [])
        n_components = analysis_results.get("n_components", 0)

        if not explained_variance:
            return None

        # --- 1. Create the detailed HTML content ---
        details_html = _create_pca_details_html(analysis_results)

        # --- 2. Create the scree plot visualization ---
        component_labels = [f"PC{i+1}" for i in range(n_components)]
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Bar(
                x=component_labels, y=explained_variance, name='Individual Variance',
                marker_color=THEME_COLORS["bar_color"],
                hovertemplate='<b>%{x}</b><br>Explained Variance: %{y:.2%}<extra></extra>'
            ), secondary_y=False
        )
        fig.add_trace(
            go.Scatter(
                x=component_labels, y=cumulative_variance, name='Cumulative Variance',
                mode='lines+markers', line=dict(color=THEME_COLORS["line_color"], width=3),
                hovertemplate='<b>%{x}</b><br>Cumulative Variance: %{y:.2%}<extra></extra>'
            ), secondary_y=True
        )

        fig.update_layout(
            title_text='Explained Variance by Principal Component',
            xaxis_title="Principal Components",
            margin=dict(l=20, r=20, t=60, b=20),
            legend=dict(x=0.02, y=0.98, bgcolor='rgba(0,0,0,0.3)')
        )
        fig.update_yaxes(title_text="Explained Variance", secondary_y=False, tickformat=".0%")
        fig.update_yaxes(title_text="Cumulative Variance", secondary_y=True, tickformat=".0%", showgrid=False)
        
        print("     ... Details and visualizations for PCA complete.")
        
        return {
            "details_html": details_html,
            "visuals": [fig]
        }

    except Exception as e:
        error_message = f"Failed during PCA visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}
