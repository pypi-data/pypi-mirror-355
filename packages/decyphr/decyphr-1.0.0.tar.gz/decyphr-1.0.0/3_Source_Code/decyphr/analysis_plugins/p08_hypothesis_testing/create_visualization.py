# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p08_hypothesis_testing/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates visual "insight cards" as rich HTML to display
#          the results of the statistical hypothesis tests.

import plotly.graph_objects as go
from typing import Dict, Any, Optional, List

P_VALUE_THRESHOLD = 0.05 # Standard alpha level for significance

def _create_intro_details_html() -> str:
    """Generates an introductory HTML block explaining hypothesis testing."""
    html = "<div class='details-card-full'>"
    html += "<h4>Understanding Hypothesis Testing Results</h4>"
    html += f"""
        <p>
            Hypothesis tests are used to determine if there are statistically significant relationships between variables. The key metric is the <strong>p-value</strong>.
            A p-value less than a threshold (typically {P_VALUE_THRESHOLD}) suggests that the observed result is unlikely to be due to random chance, and we can infer a significant relationship exists.
        </p>
        <ul>
            <li><strong>Chi-Squared Test:</strong> Used to test for a significant association between two categorical variables.</li>
            <li><strong>T-Test / ANOVA:</strong> Used to test if there is a significant difference in the mean of a numeric variable across different categories.</li>
        </ul>
        <p>The tables below highlight the <strong>most statistically significant</strong> findings (lowest p-values) from the analysis.</p>
    """
    html += "</div>"
    return html

def _create_insight_table_html(title: str, headers: List[str], results: List[Dict]) -> str:
    """Helper function to create a styled HTML table for test results."""
    if not results:
        return ""
    
    html = f"<div class='details-card'><h4>{title}</h4>"
    html += "<table class='details-table'>"
    html += f"<thead><tr>{''.join(f'<th>{h}</th>' for h in headers)}</tr></thead>"
    html += "<tbody>"
    for res in results:
        row_html = "<tr>"
        for header in headers:
            key = header.lower().replace(" ", "_")
            value = res.get(key, 'N/A')
            if isinstance(value, float):
                value = f"{value:.4f}"
            row_html += f"<td>{value}</td>"
        row_html += "</tr>"
        html += row_html
    html += "</tbody></table></div>"
    return html


def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates rich HTML content summarizing the results of hypothesis tests.

    Args:
        analysis_results (Dict[str, Any]): The results from p08_hypothesis_testing/run_analysis.py.

    Returns:
        A dictionary containing the generated HTML and an empty list for visuals.
    """
    print("     -> Generating details for hypothesis testing results...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "Not enough suitable columns for hypothesis testing."}

    try:
        # --- Create introductory text ---
        intro_html = _create_intro_details_html()

        # --- Process Chi-Squared Test Results ---
        chi2_results = analysis_results.get("chi_squared_tests", [])
        significant_chi2 = sorted(
            [res for res in chi2_results if res['p_value'] <= P_VALUE_THRESHOLD],
            key=lambda x: x['p_value']
        )[:10] # Get top 10 significant
        
        chi2_table_data = [
            {
                "variable_pair": f"<code>{res['variables'][0]}</code> & <code>{res['variables'][1]}</code>",
                "p-value": res['p_value'],
                "interpretation": "Significant Association"
            } for res in significant_chi2
        ]
        chi2_html = _create_insight_table_html(
            "Significant Categorical Associations (Chi-Squared)",
            ["Variable Pair", "P-Value", "Interpretation"],
            chi2_table_data
        )

        # --- Process T-Test / ANOVA Results ---
        mean_comp_results = analysis_results.get("mean_comparison_tests", [])
        significant_mean_comp = sorted(
            [res for res in mean_comp_results if res['p_value'] <= P_VALUE_THRESHOLD],
            key=lambda x: x['p_value']
        )[:10] # Get top 10 significant

        mean_comp_table_data = [
            {
                "variables": f"<code>{res['numeric_variable']}</code> by <code>{res['categorical_variable']}</code>",
                "test_type": res['test_type'],
                "p-value": res['p_value'],
                "interpretation": "Means are Different"
            } for res in significant_mean_comp
        ]
        mean_comp_html = _create_insight_table_html(
            "Significant Differences in Means (T-Test/ANOVA)",
            ["Variables", "Test Type", "P-Value", "Interpretation"],
            mean_comp_table_data
        )
        
        # --- Assemble final HTML ---
        if not significant_chi2 and not significant_mean_comp:
            final_html = intro_html + "<div class='details-card'><p>No statistically significant relationships were found at the p < 0.05 level.</p></div>"
        else:
            final_html = intro_html + f"<div class='details-grid'>{chi2_html}{mean_comp_html}</div>"
        
        print("     ... Details for hypothesis testing complete.")
        return {
            "details_html": final_html,
            "visuals": []  # This plugin's output is primarily informational tables
        }

    except Exception as e:
        error_message = f"Failed during hypothesis testing visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}