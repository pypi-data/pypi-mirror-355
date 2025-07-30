# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p13_data_drift/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates a detailed summary table and explanatory text to
#          visualize the results of the data drift analysis.

import plotly.graph_objects as go
from typing import Dict, Any, Optional, List

# Define consistent colors and templates for the dark theme
THEME_COLORS = {
    "drift_header": "#4B0082",  # Indigo for drift analysis header
}
P_VALUE_THRESHOLD = 0.05 # Standard alpha level for K-S test significance

def _create_drift_details_html() -> str:
    """Generates an introductory HTML block explaining data drift analysis."""
    
    intro_html = "<div class='details-card-full'>"
    intro_html += "<h4>Understanding Data Drift Analysis</h4>"
    intro_html += f"""
        <p>
            Data drift occurs when the statistical properties of the data change over time, which can degrade model performance. This analysis compares a "base" dataset to a "current" dataset to quantify these changes.
        </p>
        <ul>
            <li><strong>Kolmogorov-Smirnov (K-S) Test:</strong> Used for numeric features. It tests if the two samples are drawn from the same distribution. A low p-value (e.g., &lt; {P_VALUE_THRESHOLD}) indicates a significant drift.</li>
            <li><strong>Population Stability Index (PSI):</strong> Used for categorical features. It measures how much the distribution of categories has shifted.
                <ul>
                    <li>PSI &lt; 0.1: No significant change.</li>
                    <li>0.1 &le; PSI &lt; 0.25: Moderate shift.</li>
                    <li>PSI &ge; 0.25: Major shift.</li>
                </ul>
            </li>
        </ul>
        <p>The table below summarizes the drift detected for each feature common to both datasets.</p>
    """
    intro_html += "</div>"
    return intro_html

def _interpret_psi(psi: float) -> str:
    """Provides a human-readable interpretation of a PSI value."""
    if psi < 0.1:
        return "✅ No Significant Change"
    if psi < 0.25:
        return "⚠️ Moderate Drift"
    return "🚨 Major Drift Detected"

def _interpret_ks(p_value: float) -> str:
    """Provides a human-readable interpretation of a K-S test p-value."""
    if p_value >= P_VALUE_THRESHOLD:
        return "✅ No Significant Drift"
    return "🚨 Significant Drift Detected"

def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates a rich HTML summary for the data drift analysis results.

    Args:
        analysis_results (Dict[str, Any]): The results from p13_data_drift/run_analysis.py.

    Returns:
        A dictionary containing the generated HTML and an empty list for visuals.
    """
    print("     -> Generating details for data drift analysis...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "Data drift analysis was not performed."}

    try:
        # --- 1. Create the detailed introductory HTML ---
        details_html = _create_drift_details_html()
        
        # --- 2. Prepare data for the summary table ---
        columns = []
        drift_metrics = []
        interpretations = []

        # Sort results by column name for consistency
        sorted_results = sorted(analysis_results.items())

        for col_name, details in sorted_results:
            columns.append(f"<code>{col_name}</code>")
            if details.get("type") == "Numeric Drift (K-S Test)":
                p_value = details.get("p_value", 1.0)
                drift_metrics.append(f"K-S p-value: {p_value:.4f}")
                interpretations.append(_interpret_ks(p_value))
            elif details.get("type") == "Categorical Drift (PSI)":
                psi_value = details.get("psi_value", 0.0)
                drift_metrics.append(f"PSI: {psi_value:.4f}")
                interpretations.append(_interpret_psi(psi_value))

        # --- 3. Create the HTML table ---
        table_html = "<div class='details-card'><h4>Drift Analysis Summary</h4>"
        table_html += "<table class='details-table'>"
        table_html += "<thead><tr><th>Feature</th><th>Drift Metric & Value</th><th>Interpretation</th></tr></thead>"
        table_html += "<tbody>"
        for i in range(len(columns)):
            table_html += f"<tr><td>{columns[i]}</td><td>{drift_metrics[i]}</td><td>{interpretations[i]}</td></tr>"
        table_html += "</tbody></table></div>"

        final_html = details_html + table_html

        print("     ... Details for data drift analysis complete.")
        
        return {
            "details_html": final_html,
            "visuals": []  # This plugin's output is purely informational
        }

    except Exception as e:
        error_message = f"Failed during data drift visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}