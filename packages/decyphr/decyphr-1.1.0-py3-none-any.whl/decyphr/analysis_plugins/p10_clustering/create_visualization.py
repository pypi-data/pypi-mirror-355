# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p10_clustering/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates visualizations and detailed HTML content for the
#          K-Means clustering analysis results.

import plotly.graph_objects as go
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from typing import Dict, Any, Optional, List

# Define consistent colors and templates for the dark theme
THEME_COLORS = {
    "background": "#0f0f1a",
    "plot_background": "#1e293b",
    "text": "#ffffff",
    "grid": "#4a4a58",
    "primary_accent": "#ff7f0e",
}

def _create_clustering_details_html(analysis_results: Dict[str, Any]) -> str:
    """Generates an introductory text block and a summary table for clustering results."""
    
    inertia_scores = analysis_results.get("inertia_scores", {})
    suggested_k = analysis_results.get("suggested_k")

    intro_html = "<div class='details-card-full'>"
    intro_html += "<h4>Understanding Unsupervised Clustering (K-Means)</h4>"
    intro_html += """
        <p>
            Clustering is an unsupervised machine learning technique that groups similar data points together. K-Means attempts to partition the data into a specified number of clusters (k), where each data point belongs to the cluster with the nearest mean. It's useful for discovering hidden structures and segments in your data when you don't have a specific target variable.
        </p>
        <p>
            The <strong>Elbow Plot</strong> shows the model's inertia for different values of 'k'. Inertia measures how internally coherent the clusters are. The "elbow" in the plot—the point where the rate of decrease sharply slows—is a good heuristic for choosing the optimal number of clusters. Based on this, Decyphr has suggested <strong>k={}</strong> for the cluster visualization.
        </p>
    """.format(suggested_k)
    intro_html += "</div>"
    
    table_html = "<div class='details-card'><h4>Inertia Scores by Number of Clusters (k)</h4>"
    table_html += "<table class='details-table'>"
    table_html += "<thead><tr><th>Number of Clusters (k)</th><th>Inertia Score</th></tr></thead>"
    table_html += "<tbody>"
    for k, inertia in inertia_scores.items():
        table_html += f"<tr><td>{k}</td><td>{inertia:,.2f}</td></tr>"
    table_html += "</tbody></table></div>"

    return intro_html + table_html

def create_visuals(ddf, overview_results: Dict[str, Any], analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates Plotly visualizations and detailed HTML content for the clustering analysis.

    Args:
        ddf: The Dask DataFrame, needed for raw data access.
        overview_results: The results from the overview plugin to get column types.
        analysis_results (Dict[str, Any]): The results from p10_clustering/run_analysis.py.

    Returns:
        A dictionary containing the generated HTML and a list of Plotly figures.
    """
    print("     -> Generating details & visualizations for clustering analysis...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "Clustering analysis was not performed."}

    try:
        # --- 1. Create the detailed HTML content ---
        details_html = _create_clustering_details_html(analysis_results)
        
        all_visuals: List[go.Figure] = []

        # --- 2. Create the Elbow Plot ---
        inertia_scores = analysis_results.get("inertia_scores", {})
        if inertia_scores:
            fig_elbow = go.Figure(data=go.Scatter(
                x=list(inertia_scores.keys()), y=list(inertia_scores.values()),
                mode='lines+markers', marker=dict(size=10, color=THEME_COLORS["primary_accent"]),
                line=dict(width=3, color=THEME_COLORS["primary_accent"])
            ))
            fig_elbow.update_layout(
                title_text='Elbow Plot for K-Means Inertia',
                xaxis_title="Number of Clusters (k)", yaxis_title="Inertia",
                margin=dict(l=20, r=20, t=60, b=20)
            )
            all_visuals.append(fig_elbow)

        # --- 3. Create the 2D Cluster Scatter Plot ---
        cluster_labels = analysis_results.get("cluster_labels", {})
        if cluster_labels:
            numeric_cols = [col for col, details in overview_results.get("column_details", {}).items() if details['decyphr_type'] == 'Numeric']
            numeric_df_computed = ddf[numeric_cols].fillna(ddf[numeric_cols].mean()).compute()
            scaled_data = StandardScaler().fit_transform(numeric_df_computed)
            pca = PCA(n_components=2)
            principal_components = pca.fit_transform(scaled_data)
            pca_df = pd.DataFrame(data=principal_components, columns=['PC 1', 'PC 2'], index=numeric_df_computed.index)
            pca_df['Cluster'] = pd.Series(cluster_labels)

            fig_scatter = go.Figure()
            for cluster_num in sorted(pca_df['Cluster'].unique()):
                cluster_data = pca_df[pca_df['Cluster'] == cluster_num]
                fig_scatter.add_trace(go.Scatter(
                    x=cluster_data['PC 1'], y=cluster_data['PC 2'],
                    mode='markers', name=f'Cluster {cluster_num}',
                    marker=dict(size=8, opacity=0.7),
                    hovertemplate='<b>PC 1:</b> %{x:.2f}<br><b>PC 2:</b> %{y:.2f}<extra></extra>'
                ))
            fig_scatter.update_layout(
                title_text=f'2D Visualization of Clusters (k={analysis_results.get("suggested_k")})',
                xaxis_title="Principal Component 1", yaxis_title="Principal Component 2",
                legend_title_text='Clusters', margin=dict(l=20, r=20, t=60, b=20)
            )
            all_visuals.append(fig_scatter)

        print("     ... Details and visualizations for clustering complete.")
        return {
            "details_html": details_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during clustering visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}