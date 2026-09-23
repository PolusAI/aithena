"""
Tokenization utilities for BM25 retrieval.

Provides NLTK-based tokenization matching TrialGPT's original approach.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


def _ensure_nltk_data():
    """Ensure NLTK punkt tokenizer is downloaded."""
    import nltk
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        logger.info("Downloading NLTK punkt_tab tokenizer...")
        nltk.download('punkt_tab', quiet=True)


def tokenize(text: str) -> List[str]:
    """
    Tokenize text using NLTK word_tokenize and lowercase.

    This matches the original TrialGPT tokenization approach:
    - Uses NLTK's word_tokenize
    - Converts to lowercase

    Args:
        text: Text to tokenize

    Returns:
        List of lowercase tokens

    Example:
        >>> tokenize("Stage III Lung Cancer")
        ['stage', 'iii', 'lung', 'cancer']
    """
    _ensure_nltk_data()
    from nltk import word_tokenize

    if not text or not text.strip():
        return []

    return word_tokenize(text.lower())


def tokenize_trial_for_bm25(
    title: str,
    diseases_list: List[str],
    text: str
) -> List[str]:
    """
    Tokenize trial fields with weighting for BM25.

    This replicates the original TrialGPT weighting scheme
    (lines 37-41 of hybrid_fusion_retrieval.py):
    - Title: 3x weight
    - Diseases: 2x weight each
    - Text: 1x weight

    Args:
        title: Trial title
        diseases_list: List of disease/condition names
        text: Trial text (summary + criteria)

    Returns:
        List of weighted tokens

    Example:
        >>> tokenize_trial_for_bm25(
        ...     "Cancer Trial",
        ...     ["Lung Cancer"],
        ...     "A study of treatments"
        ... )
        ['cancer', 'trial', 'cancer', 'trial', 'cancer', 'trial',  # 3x title
         'lung', 'cancer', 'lung', 'cancer',  # 2x diseases
         'a', 'study', 'of', 'treatments']  # 1x text
    """
    tokens = []

    # Title: 3x weight
    title_tokens = tokenize(title)
    tokens.extend(title_tokens * 3)

    # Diseases: 2x weight each
    for disease in diseases_list:
        disease_tokens = tokenize(disease)
        tokens.extend(disease_tokens * 2)

    # Text: 1x weight
    text_tokens = tokenize(text)
    tokens.extend(text_tokens)

    return tokens
