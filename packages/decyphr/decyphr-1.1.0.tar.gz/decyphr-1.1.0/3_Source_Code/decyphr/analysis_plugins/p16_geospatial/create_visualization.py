# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p16_geospatial/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates an interactive map visualization and explanatory
#          text for the geospatial data identified in the analysis step. (V4: Final)

import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, Optional, List

# Define consistent colors and templates for the dark theme
THEME_COLORS = {
    "background": "#0f0f1a",
    "text": "#ffffff",
}

def _create_geospatial_details_html(lat_col: str, lon_col: str) -> str:
    """Generates an introductory HTML block explaining the map visualization."""
    
    intro_html = "<div class='details-card-full'>"
    intro_html += "<h4>Understanding Geospatial Analysis</h4>"
    intro_html += f"""
        <p>
            Geospatial analysis involves visualizing data points on a map to uncover geographic patterns, clusters, and distributions. Decyphr automatically detected latitude and longitude columns (<code>{lat_col}</code> and <code>{lon_col}</code>) and has plotted a sample of the data points on the interactive map below.
        </p>
        <p>
            You can pan, zoom, and hover over individual points to explore the data. If a target variable was provided, the points may be colored according to its value, which can help reveal how the target variable is distributed geographically.
        </p>
    """
    intro_html += "</div>"
    return intro_html


def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates an interactive Plotly Scattermapbox for the geospatial data.

    Args:
        analysis_results (Dict[str, Any]): The results from p16_geospatial/run_analysis.py.

    Returns:
        A dictionary containing the generated HTML and a list of Plotly figures.
    """
    print("     -> Generating details & visualizations for geospatial analysis...")

    if "error" in analysis_results or not analysis_results or "message" in analysis_results:
        return {"message": "Geospatial analysis was not performed."}

    try:
        geo_data_dict = analysis_results.get("geo_dataframe", {})
        if not geo_data_dict:
            return None

        geo_df = pd.DataFrame(geo_data_dict)
        lat_col = analysis_results.get("lat_col")
        lon_col = analysis_results.get("lon_col")
        target_col = analysis_results.get("target_col")

        geo_df[lat_col] = pd.to_numeric(geo_df[lat_col], errors='coerce')
        geo_df[lon_col] = pd.to_numeric(geo_df[lon_col], errors='coerce')
        geo_df.dropna(subset=[lat_col, lon_col], inplace=True)

        if geo_df.empty:
            return {"message": "No valid numeric lat/lon points found after cleaning."}

        details_html = _create_geospatial_details_html(lat_col, lon_col)
        print("        - Creating interactive map plot.")

        # --- FINAL ROBUST FIX: Handle potential formatting errors defensively ---
        hover_texts = []
        for lat, lon in zip(geo_df[lat_col], geo_df[lon_col]):
            try:
                # Attempt to format as a number
                text = f"Lat: {lat:.4f}<br>Lon: {lon:.4f}"
            except (ValueError, TypeError):
                # If formatting fails, fall back to string representation
                text = f"Lat: {lat}<br>Lon: {lon}"
            hover_texts.append(text)

        fig = go.Figure(go.Scattermapbox(
            lat=geo_df[lat_col],
            lon=geo_df[lon_col],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=9,
                color=geo_df[target_col] if target_col and pd.api.types.is_numeric_dtype(geo_df[target_col]) else '#1f77b4',
                colorscale='Viridis',
                showscale=True if target_col and pd.api.types.is_numeric_dtype(geo_df[target_col]) else False,
                colorbar_title_text=target_col if target_col else ""
            ),
            hoverinfo='text',
            text=hover_texts # Use the safely generated hover texts
        ))

        fig.update_layout(
            title_text='Geospatial Data Distribution',
            autosize=True,
            hovermode='closest',
            mapbox=dict(
                style='carto-darkmatter',
                center=dict(lat=geo_df[lat_col].mean(), lon=geo_df[lon_col].mean()),
                pitch=0,
                zoom=3
            ),
            margin={"r":0,"t":40,"l":0,"b":0}
        )
        
        print("     ... Details and visualization for geospatial analysis complete.")
        return {
            "details_html": details_html,
            "visuals": [fig]
        }

    except Exception as e:
        error_message = f"Failed during geospatial visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}
