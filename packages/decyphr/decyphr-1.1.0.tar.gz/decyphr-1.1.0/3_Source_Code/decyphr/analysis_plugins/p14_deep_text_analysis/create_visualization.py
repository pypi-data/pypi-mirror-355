# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p14_deep_text_analysis/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates visual components and detailed HTML for the deep
#          text analysis results.

import plotly.graph_objects as go
from typing import Dict, Any, Optional, List

# Define consistent colors and templates for the dark theme
THEME_COLORS = {
    "background": "#0f0f1a",
    "plot_background": "#1e293b",
    "text": "#ffffff",
    "grid": "#4a4a58",
    "primary_accent": "#9467bd",  # A purple accent for text analysis
}

def _create_text_analysis_details_html(col_name: str) -> str:
    """Generates an introductory HTML block explaining the NLP analyses for a column."""
    
    intro_html = f"<div class='details-card-full'><h4>Deep Text Analysis for: <code>{col_name}</code></h4>"
    intro_html += """
        <p>
            This section provides Natural Language Processing (NLP) insights for the selected text column.
        </p>
        <ul>
            <li><strong>Sentiment Analysis:</strong> Calculates the average polarity (positive/negative feel) and subjectivity (objective fact vs. subjective opinion) of the text.</li>
            <li><strong>Named Entity Recognition (NER):</strong> Identifies and counts real-world objects like Persons, Organizations, and Locations (GPE - Geo-Political Entity).</li>
            <li><strong>Topic Modeling (LDA):</strong> Attempts to discover abstract topics from the text. Each topic is represented by a set of its most important keywords.</li>
        </ul>
    """
    intro_html += "</div>"
    return intro_html

def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates Plotly visualizations and detailed HTML for the deep text analysis results.

    Args:
        analysis_results (Dict[str, Any]): The results from p14_deep_text_analysis/run_analysis.py.

    Returns:
        A dictionary containing the generated HTML and a list of Plotly figures.
    """
    print("     -> Generating details & visualizations for deep text analysis...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "Deep text analysis was not performed."}

    all_details_html: List[str] = []
    all_visuals: List[go.Figure] = []

    try:
        for col_name, col_results in analysis_results.items():
            print(f"        - Creating visuals for text column '{col_name}'")
            # --- 1. Create the detailed introductory HTML for this column ---
            all_details_html.append(_create_text_analysis_details_html(col_name))

            # --- 2. Sentiment Gauge ---
            if "sentiment_polarity" in col_results:
                polarity = col_results["sentiment_polarity"]
                fig_sentiment = go.Figure(go.Indicator(
                    mode="gauge+number", value=polarity,
                    title={'text': "Avg. Sentiment Polarity", 'font': {'size': 16}},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={'axis': {'range': [-1, 1]}, 'bar': {'color': THEME_COLORS["primary_accent"]}}
                ))
                fig_sentiment.update_layout(margin=dict(l=30, r=30, t=50, b=30))
                all_visuals.append(fig_sentiment)

            # --- 3. NER Bar Chart ---
            if "named_entities" in col_results and col_results["named_entities"]:
                ner_data = col_results["named_entities"]
                fig_ner = go.Figure(go.Bar(
                    x=list(ner_data.values()), y=list(ner_data.keys()),
                    orientation='h', marker_color=THEME_COLORS["primary_accent"]
                ))
                fig_ner.update_layout(
                    title_text='Named Entity Counts', xaxis_title='Count', yaxis={'autorange': 'reversed'},
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                all_visuals.append(fig_ner)
            
            # --- 4. Topics Table ---
            if "topics" in col_results and col_results["topics"]:
                # For topics, we will generate a clean HTML table instead of a plot
                topics_data = col_results["topics"]
                table_html = "<div class='details-card'><h4>Discovered Topics (LDA)</h4>"
                table_html += "<table class='details-table'>"
                table_html += "<thead><tr><th>Topic ID</th><th>Top 5 Keywords</th></tr></thead><tbody>"
                for topic_id, words in topics_data.items():
                    table_html += f"<tr><td>{topic_id}</td><td>{words}</td></tr>"
                table_html += "</tbody></table></div>"
                all_details_html.append(table_html)

        if not all_visuals and not all_details_html:
            return {"message": "No text analysis results to visualize."}

        print("     ... Details and visualizations for deep text analysis complete.")
        return {
            "details_html": "".join(all_details_html),
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during text analysis visualization: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}