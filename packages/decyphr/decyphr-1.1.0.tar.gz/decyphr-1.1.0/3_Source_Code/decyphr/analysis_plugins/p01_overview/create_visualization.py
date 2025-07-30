# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p01_overview/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates rich HTML content, including detailed tables
#          and statistics for the main Overview section of the report.

import plotly.graph_objects as go
from typing import Dict, Any, Optional, List

def _create_html_table(title: str, data: Dict[str, Any]) -> str:
    """Helper function to generate a clean, styled HTML table from a dictionary."""
    html = f"<div class='details-card'><h4>{title}</h4>"
    html += "<table class='details-table'>"
    for key, value in data.items():
        html += f"<tr><td>{key}</td><td>{value}</td></tr>"
    html += "</table></div>"
    return html

def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates the rich HTML content for the overview section.

    This new version generates HTML directly for tables and stats,
    and prepares any Plotly visualizations separately.

    Args:
        analysis_results (Dict[str, Any]): The results from p01_overview/run_analysis.py.

    Returns:
        A dictionary containing two keys:
        'details_html': A string of combined HTML for all detailed tables.
        'visuals': A list of Plotly Figure objects (can be empty).
    """
    print("     -> Generating details & visualizations for overview...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if "message" in analysis_results:
        return {"details_html": f"<p>{analysis_results['message']}</p>", "visuals": []}

    try:
        # --- 1. Prepare Data for HTML Tables ---
        dataset_stats = analysis_results.get("dataset_stats", {})
        data_quality = analysis_results.get("data_quality", {})
        variable_types = analysis_results.get("variable_types", {})

        # Combine main stats and data quality into one table
        combined_stats = {**dataset_stats, **data_quality}

        # --- 2. Generate HTML for Each Component ---
        stats_html = _create_html_table("Dataset Statistics", combined_stats)
        
        # Filter variable types with zero count for a cleaner table
        filtered_variable_types = {k: v for k, v in variable_types.items() if v > 0}
        types_html = _create_html_table("Variable Types", filtered_variable_types)

        # --- 3. Assemble the Final Output ---
        # The 'details_html' is a grid containing both tables.
        # We use CSS grid within the HTML for a responsive two-column layout.
        final_html = f"<div class='details-grid'>{stats_html}{types_html}</div>"
        
        # This plugin doesn't have a primary visualization like a histogram,
        # as the details are in the tables. So, the 'visuals' list is empty.
        all_visuals = []
        
        print("     ... Details for overview complete.")
        
        return {
            "details_html": final_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during overview visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}