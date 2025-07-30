# Decyphr

An all-encompassing, automated toolkit for generating deep, professional, and interactive Exploratory Data Analysis (EDA) reports with a single line of code.

Decyphr is designed to accelerate the data science workflow by automating the tedious and time-consuming process of initial data exploration. It goes beyond basic profiling to provide deep statistical insights, advanced machine learning-driven analysis, and a stunning, presentation-ready report that is as beautiful as it is informative.

(Note: You will replace this with a screenshot of your final report)

## Key Features

Decyphr provides a comprehensive suite of analyses, intelligently triggered based on your data's characteristics:

Complete Overview: Instant summary of dataset shape, memory usage, variable types, and data quality warnings.

Deep Univariate Analysis: Detailed statistical profiles, histograms, and frequency charts for every variable.

Multivariate Analysis: Stunning, interactive heatmaps for both linear (Pearson) and non-linear (Phik) correlations.

Advanced Data Quality: Automatically detects constant columns, whitespace issues, and potential outliers using multiple methods (IQR, Isolation Forest).

Statistical Inference: Performs automated Hypothesis Testing (T-Tests, ANOVA, Chi-Squared) to uncover statistically significant relationships.

Machine Learning Insights:
PCA: Analyzes dimensionality reduction possibilities.
Clustering: Automatically finds hidden segments in your data using K-Means.
Feature Importance: Trains a baseline model to identify the most predictive features when a target is provided.
Explainable AI (XAI): Generates SHAP summary plots to explain how your features impact model predictions.

Specialized Analysis: Includes dedicated modules for Deep Text Analysis (Sentiment, NER, Topics), Time-Series Decomposition, and Geospatial Mapping.

Data Drift Detection: Compare two datasets to quantify changes in data distribution over time.

High-End Interactive Report: A beautiful, modern dashboard with a toggleable light/dark theme, responsive charts, and a professional UI/UX.

## Quick Start

1. Installation

Install Decyphr and its core dependencies from the root of the project directory:

# Navigate to the decyphr_project folder  
pip install -e .

To enable all features, including deep text and geospatial analysis, install the [all] optional dependencies:

pip install -e ".[all]"

For deep text analysis, you will also need to download the SpaCy language model:

python -m spacy download en_core_web_sm

2. Generate Your First Report

Create a Python script (analyze.py) and add the following code. Just point it to your dataset and let Decyphr do the rest.

# analyze.py  
import decyphr

# Generate a comprehensive report for a single dataset  
decyphr.analyze(filepath="path/to/your/data.csv")

# --- OR ---  

# Generate a report that includes target-driven analysis  
# decyphr.analyze(  
#     filepath="path/to/your/training_data.csv",  
#     target="column_to_predict"  
# )

Run the script from your terminal:

python analyze.py

Your professional, interactive HTML report will be automatically saved in a new decyphr_reports/ directory.

## Project Structure

This project uses a highly modular "plugin" architecture to ensure it is robust, maintainable, and easy to extend. All analysis and visualization logic is separated into self-contained modules located in the src/decyphr/analysis_plugins/ directory.

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated. Please feel free to fork the repo and create a pull request, or open an issue with suggestions.

## License

Distributed under the MIT License. See LICENSE file for more information.