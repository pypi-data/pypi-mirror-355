# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p03_data_quality/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates visual "warning cards" as rich HTML to display
#          the data quality issues identified by the analysis script.

from typing import Dict, Any, Optional, List

def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates rich HTML content to display data quality warnings.

    Args:
        analysis_results (Dict[str, Any]): The results from p03_data_quality/run_analysis.py.

    Returns:
        A dictionary containing the generated HTML and an empty list for visuals.
    """
    print("     -> Generating details for data quality issues...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}

    constant_columns = analysis_results.get("constant_columns", [])
    whitespace_issues = analysis_results.get("whitespace_issues", [])

    if not constant_columns and not whitespace_issues:
        return {"message": "No data quality issues found."}

    all_details_html: List[str] = []

    try:
        # --- Create HTML for Constant Columns Warning ---
        if constant_columns:
            html = "<div class='details-card-warning'>"
            html += "<h4>Constant Value Columns</h4>"
            html += "<p>These columns contain only a single, repeating value and provide no predictive power. They are strong candidates for removal.</p>"
            html += "<ul class='details-list'>"
            for col in constant_columns:
                html += f"<li><code>{col}</code></li>"
            html += "</ul></div>"
            all_details_html.append(html)

        # --- Create HTML for Whitespace Issues Warning ---
        if whitespace_issues:
            html = "<div class='details-card-warning'>"
            html += "<h4>Leading/Trailing Whitespace</h4>"
            html += "<p>These columns contain values with extra spaces at the beginning or end. This can cause issues with joins, grouping, and model performance.</p>"
            html += "<table class='details-table'>"
            html += "<tr><th>Column</th><th>Leading Spaces</th><th>Trailing Spaces</th></tr>"
            for issue in whitespace_issues:
                 html += f"<tr><td><code>{issue['column']}</code></td><td>{issue['leading_spaces']:,}</td><td>{issue['trailing_spaces']:,}</td></tr>"
            html += "</table></div>"
            all_details_html.append(html)
        
        # This plugin's output is purely informational tables, so 'visuals' is empty.
        # The HTML is combined into a grid for display.
        final_html = f"<div class='details-grid'>{''.join(all_details_html)}</div>"

        print("     ... Details for data quality complete.")
        return {
            "details_html": final_html,
            "visuals": [] 
        }

    except Exception as e:
        error_message = f"Failed during data quality visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}