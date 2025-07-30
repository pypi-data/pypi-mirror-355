# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p07_interactions/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates visual tables and explanatory text to display the
#          suggested feature interactions.

import plotly.graph_objects as go
from typing import Dict, Any, Optional, List

def _create_intro_details_html() -> str:
    """Generates an introductory HTML block explaining feature interactions."""
    html = "<div class='details-card-full'>"
    html += "<h4>Understanding Feature Interaction Suggestions</h4>"
    html += """
        <p>
            Feature interaction is a powerful feature engineering technique where two or more features are combined to create a new feature. 
            This new feature can sometimes capture more complex relationships and provide a stronger signal to machine learning models than the individual features alone.
        </p>
        <ul>
            <li><strong>Numeric Interactions (e.g., A * B):</strong> Multiplying two numeric features can capture synergistic effects.</li>
            <li><strong>Categorical Interactions (e.g., A & B):</strong> Combining two categorical features creates a new category that represents the intersection of the two, which can uncover specific group behaviors.</li>
        </ul>
        <p>The following are heuristic suggestions based on feature variance and cardinality. They are a starting point for more advanced feature engineering.</p>
    """
    html += "</div>"
    return html

def _create_suggestion_table_html(title: str, interactions: List[str]) -> str:
    """Helper function to create a styled HTML table for suggestions."""
    if not interactions:
        return ""
    html = f"<div class='details-card'><h4>{title}</h4>"
    html += "<ul class='details-list'>"
    for item in interactions:
        html += f"<li><code>{item}</code></li>"
    html += "</ul></div>"
    return html

def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates rich HTML content for the suggested feature interactions.

    Args:
        analysis_results (Dict[str, Any]): The results from p07_interactions/run_analysis.py.

    Returns:
        A dictionary containing the generated HTML and an empty list for visuals.
    """
    print("     -> Generating details for feature interaction suggestions...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "No feature interactions were suggested."}

    try:
        # --- Create introductory text ---
        intro_html = _create_intro_details_html()

        # --- Create suggestion tables ---
        numeric_interactions = analysis_results.get("suggested_numeric_interactions", [])
        categorical_interactions = analysis_results.get("suggested_categorical_interactions", [])
        
        numeric_html = _create_suggestion_table_html("Suggested Numeric Interactions", numeric_interactions)
        categorical_html = _create_suggestion_table_html("Suggested Categorical Interactions", categorical_interactions)

        # --- Assemble the final HTML content ---
        # The output is purely informational tables in a grid layout.
        final_html = intro_html + f"<div class='details-grid'>{numeric_html}{categorical_html}</div>"
        
        print("     ... Details for feature interactions complete.")
        return {
            "details_html": final_html,
            "visuals": []  # This plugin does not produce primary plot visualizations
        }

    except Exception as e:
        error_message = f"Failed during feature interaction visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}