# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p02_univariate/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates all visual components AND detailed HTML tables
#          for the univariate analysis section.

import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, Optional, List

# Define consistent colors and templates for the dark theme
THEME_COLORS = {
    "background": "#0f0f1a",
    "plot_background": "#1e293b",
    "text": "#ffffff",
    "grid": "#4a4a58",
    "primary_accent": "#999999"  # changed to grey for monochrome
}

def _create_numeric_details_html(col_name: str, stats: Dict[str, float]) -> str:
    """Generates a detailed HTML statistics table for a numeric variable."""
    # Define the order and formatting for the stats table
    stat_order = {
        'count': ('Count', '{:,.0f}'), 'mean': ('Mean', '{:,.2f}'),
        'std': ('Std. Dev.', '{:,.2f}'), 'min': ('Minimum', '{:,.2f}'),
        '25%': ('25th Percentile', '{:,.2f}'), '50%': ('Median (50%)', '{:,.2f}'),
        '75%': ('75th Percentile', '{:,.2f}'), 'max': ('Maximum', '{:,.2f}'),
        'skew': ('Skewness', '{:,.3f}'), 'kurtosis': ('Kurtosis', '{:,.3f}')
    }
    html = f"<div class='details-card-columnar'><h4><code>{col_name}</code>: Statistics</h4>"
    html += "<table class='details-table'>"
    for key, (label, fmt) in stat_order.items():
        if key in stats:
            html += f"<tr><td>{label}</td><td>{fmt.format(stats[key])}</td></tr>"
    html += "</table></div>"
    return html

def _create_categorical_details_html(col_name: str, stats: Dict[str, Any]) -> str:
    """Generates a detailed HTML frequency table for a categorical variable."""
    value_counts = stats.get('value_counts', {})
    html = f"<div class='details-card-columnar'><h4><code>{col_name}</code>: Frequencies</h4>"
    html += "<table class='details-table'>"
    html += "<tr><th>Category</th><th>Count</th><th>Percentage</th></tr>"
    total_count = sum(value_counts.values())
    for category, count in value_counts.items():
        percentage = f"{(count / total_count * 100):.2f}%" if total_count > 0 else "0.00%"
        html += f"<tr><td>{category}</td><td>{count:,}</td><td>{percentage}</td></tr>"
    html += "</table></div>"
    return html


def create_visuals(ddf, analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates Plotly visualizations and detailed HTML tables for univariate analysis.

    Returns:
        A dictionary containing two keys:
        'details_html': A string of combined HTML for all detailed tables.
        'visuals': A list of Plotly Figure objects.
    """
    print("     -> Generating details & visualizations for univariate analysis...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}

    numeric_stats = analysis_results.get("numeric_stats", {})
    categorical_stats = analysis_results.get("categorical_stats", {})

    if not numeric_stats and not categorical_stats:
        return {"message": "No variables found for univariate analysis."}

    all_details_html: List[str] = []
    all_visuals: List[go.Figure] = []

    try:
        # --- Process Numeric Columns ---
        for col_name, stats in numeric_stats.items():
            print(f"        - Creating details & histogram for '{col_name}'")
            all_details_html.append(_create_numeric_details_html(col_name, stats))
            
            fig = go.Figure(data=[
                go.Histogram(
                    x=ddf[col_name].compute(),
                    marker=dict(color=THEME_COLORS["primary_accent"]),
                )
            ])
            fig.update_layout(
                title_text=f'Distribution of {col_name}',
                bargap=0.1,
                margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(color="black"),
                xaxis=dict(showgrid=True, gridcolor="#cccccc"),
                yaxis=dict(showgrid=True, gridcolor="#cccccc")
            )
            all_visuals.append(fig)

        # --- Process Categorical Columns ---
        for col_name, stats in categorical_stats.items():
            print(f"        - Creating details & bar chart for '{col_name}'")
            all_details_html.append(_create_categorical_details_html(col_name, stats))

            value_counts = stats.get("value_counts", {})
            fig = go.Figure(data=[
                go.Bar(
                    x=list(value_counts.keys()),
                    y=list(value_counts.values()),
                    marker=dict(color=THEME_COLORS["primary_accent"])
                )
            ])
            fig.update_layout(
                title_text=f'Frequency of Categories in {col_name}',
                xaxis={'tickangle': -45},
                margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(color="black"),
                xaxis_showgrid=True, yaxis_showgrid=True,
                xaxis_gridcolor="#cccccc", yaxis_gridcolor="#cccccc"
            )
            all_visuals.append(fig)

        print("     ... Details and visualizations for univariate analysis complete.")
        
        # Structure the final HTML to be a two-column grid
        final_html = f"<div class='details-grid-univariate'>{''.join(all_details_html)}</div>"
        
        return {
            "details_html": final_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during univariate visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}