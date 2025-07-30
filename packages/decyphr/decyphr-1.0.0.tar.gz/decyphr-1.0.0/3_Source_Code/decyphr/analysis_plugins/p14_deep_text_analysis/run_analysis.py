# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p14_deep_text_analysis/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs deep Natural Language Processing (NLP) on text
#          columns to extract sentiment, topics, and named entities.

import dask.dataframe as dd
import pandas as pd
from typing import Dict, Any, Optional, List

# Import NLP libraries, but handle potential ImportError if not installed
try:
    import spacy
    from textblob import TextBlob
    from gensim.corpora.dictionary import Dictionary
    from gensim.models.ldamodel import LdaModel
    NLP_LIBRARIES_AVAILABLE = True
except ImportError:
    NLP_LIBRARIES_AVAILABLE = False


def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs deep text analysis on high-cardinality text columns.

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results from the p01_overview plugin.
        target_column (Optional[str]): The target column, ignored here.

    Returns:
        A dictionary containing NLP analysis results for each applicable column.
    """
    print("     -> Performing deep text analysis (Sentiment, NER, Topics)...")

    if not NLP_LIBRARIES_AVAILABLE:
        message = "Skipping text analysis. Install with 'pip install \"decyphr[text]\"' to enable."
        print(f"     ... {message}")
        return {"message": message}

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Text analysis requires 'column_details' from the overview plugin."}

    text_cols: List[str] = [
        col for col, details in column_details.items() if details['decyphr_type'] == 'Text (High Cardinality)'
    ]

    if not text_cols:
        return {"message": "No high-cardinality text columns found to analyze."}

    results: Dict[str, Any] = {}
    
    # Load Spacy model once
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        message = "Spacy model 'en_core_web_sm' not found. Run 'python -m spacy download en_core_web_sm'"
        print(f"     ... {message}")
        return {"error": message}

    try:
        for col_name in text_cols:
            print(f"     ... Analyzing text in column: '{col_name}'")
            # NLP is memory intensive, so we work on a computed sample.
            sampled_series = ddf[col_name].dropna().sample(frac=0.1, random_state=42).compute()
            if sampled_series.empty:
                continue

            col_results: Dict[str, Any] = {}

            # --- 1. Sentiment Analysis ---
            sentiments = sampled_series.apply(lambda text: TextBlob(str(text)).sentiment)
            col_results["sentiment_polarity"] = sentiments.apply(lambda s: s.polarity).mean()
            col_results["sentiment_subjectivity"] = sentiments.apply(lambda s: s.subjectivity).mean()

            # --- 2. Named Entity Recognition (NER) ---
            ner_counts = {}
            for doc in nlp.pipe(sampled_series.astype(str)):
                for ent in doc.ents:
                    label = ent.label_
                    ner_counts[label] = ner_counts.get(label, 0) + 1
            col_results["named_entities"] = ner_counts
            
            # --- 3. Topic Modeling (LDA) ---
            # Preprocess text for LDA: tokenize and remove stopwords
            texts = [
                [token.lemma_ for token in doc if not token.is_stop and not token.is_punct and not token.is_space]
                for doc in nlp.pipe(sampled_series.astype(str))
            ]
            dictionary = Dictionary(texts)
            corpus = [dictionary.doc2bow(text) for text in texts]
            
            if corpus:
                lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=3, random_state=42)
                topics = lda_model.print_topics(num_words=5)
                col_results["topics"] = {f"Topic {t[0]}": t[1] for t in topics}

            results[col_name] = col_results

        print("     ... Deep text analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during deep text analysis: {e}"
        print(f"     ... {error_message}")
        return {"error": error_message}