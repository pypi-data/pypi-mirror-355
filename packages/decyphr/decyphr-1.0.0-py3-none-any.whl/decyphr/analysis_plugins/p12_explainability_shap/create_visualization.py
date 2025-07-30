# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p12_explainability_shap/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates a SHAP summary plot and explanatory text to provide
#          deep, instance-level explanations for the model's predictions.

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List

# Define consistent colors and templates for the dark theme
THEME_COLORS = {
    "background": "#0f0f1a",
    "plot_background": "#1e293b",
    "text": "#ffffff",
    "grid": "#4a4a58",
}

def _create_shap_details_html() -> str:
    """Generates an introductory HTML block explaining SHAP values."""
    
    intro_html = "<div class='details-card-full'>"
    intro_html += "<h4>Understanding Explainable AI (SHAP Summary Plot)</h4>"
    intro_html += """
        <p>
            While Feature Importance shows <em>what</em> features are most predictive, SHAP (SHapley Additive exPlanations) values explain <em>how</em> they influence the model's predictions. This summary plot provides a powerful, high-level overview of this relationship.
        </p>
        <ul>
            <li><strong>Feature Importance:</strong> Features are ranked on the y-axis, with the most important at the top.</li>
            <li><strong>Impact on Prediction:</strong> The x-axis represents the SHAP value. A positive value pushes the prediction higher (e.g., towards "Churn"), while a negative value pushes it lower.</li>
            <li><strong>Original Feature Value:</strong> Each point on the plot is a single prediction for a single row. The color of the point represents the original value of that feature for that row (High values are red, low values are blue).</li>
        </ul>
        <p>For example, a cluster of red points on the right side of the plot for 'Age' would mean that high ages strongly push the model's prediction higher.</p>
    """
    intro_html += "</div>"
    return intro_html


def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates an interactive SHAP summary plot using Plotly.

    Args:
        analysis_results (Dict[str, Any]): The results from p12_explainability_shap/run_analysis.py.

    Returns:
        A dictionary containing the generated HTML and a list of Plotly figures.
    """
    print("     -> Generating details & visualizations for SHAP analysis...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "SHAP analysis was not performed."}

    try:
        shap_values = np.array(analysis_results.get("shap_values"))
        feature_data_dict = analysis_results.get("feature_data", {})
        feature_names = analysis_results.get("feature_names", [])

        if shap_values.size == 0 or not feature_data_dict:
            return {"message": "No SHAP values were calculated."}

        # --- 1. Create the detailed HTML content ---
        details_html = _create_shap_details_html()

        # --- 2. Create the SHAP summary plot ---
        feature_data = pd.DataFrame(feature_data_dict)
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': mean_abs_shap
        }).sort_values(by='importance', ascending=False).head(20)

        sorted_features = importance_df['feature'].tolist()
        
        fig = go.Figure()
        fig.add_shape(type='line', x0=0, y0=-0.5, x1=0, y1=len(sorted_features)-0.5, line=dict(color=THEME_COLORS["grid"], width=1))

        for i, feature in enumerate(sorted_features):
            feature_index = feature_names.index(feature)
            shap_for_feature = shap_values[:, feature_index]
            feature_values = feature_data[feature].values
            
            # Normalize feature values for coloring
            min_val, max_val = np.nanmin(feature_values), np.nanmax(feature_values)
            if min_val == max_val:
                color_values = 0.5 # Mid-point color if all values are the same
            else:
                color_values = (feature_values - min_val) / (max_val - min_val)

            fig.add_trace(go.Scatter(
                x=shap_for_feature, y=np.full(len(shap_for_feature), i),
                mode='markers',
                marker=dict(
                    color=color_values, colorscale='RdBu', showscale=(i == 0),
                    colorbar=dict(title='Feature Value<br>(High/Low)', x=1.02, y=0.5, len=0.8),
                    symbol='circle', size=6, opacity=0.7,
                ),
                customdata=feature_values,
                hovertemplate=f"<b>{feature}</b><br>SHAP value: %{{x:.3f}}<br>Feature value: %{{customdata:.3f}}<extra></extra>",
                name=''
            ))

        fig.update_layout(
            title_text='SHAP Summary Plot: Feature Impact on Model Output',
            xaxis_title="SHAP Value (impact on model output)",
            yaxis=dict(tickvals=list(range(len(sorted_features))), ticktext=sorted_features, autorange='reversed'),
            showlegend=False, margin=dict(l=40, r=40, t=60, b=40)
        )
        
        print("     ... Details and visualization for SHAP analysis complete.")
        
        return {
            "details_html": details_html,
            "visuals": [fig]
        }

    except Exception as e:
        error_message = f"Failed during SHAP visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}