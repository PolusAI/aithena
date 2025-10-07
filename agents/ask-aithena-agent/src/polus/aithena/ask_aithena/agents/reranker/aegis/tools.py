"""Tools for the Reranker Referee Agent. (ScoreGiver)"""

import spacy
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

nlp = spacy.load("en_core_web_md")


def robust_noun_phrase_overlap(query: str, abstract: str) -> float:
    """
    Calculate robust noun-phrase overlap using lemma tokens for more granular scoring.

    Args:
        query (str): User's query.
        abstract (str): Abstract text.

    Returns:
        float: Overlap ratio (0 to 1), granular scoring.
    """

    def extract_np_tokens(doc):
        tokens = set()
        for np in doc.noun_chunks:
            tokens.update(token.lemma_.lower() for token in np if token.is_alpha)
        return tokens

    query_tokens = extract_np_tokens(nlp(query))
    abstract_tokens = extract_np_tokens(nlp(abstract))

    intersection = query_tokens & abstract_tokens
    return len(intersection) / max(len(query_tokens), 1)


def simplified_ngram_overlap(query: str, abstract: str) -> float:
    """
    Calculate simplified N-Gram overlap similarity with consistent lemmatization.

    Args:
        query (str): Original user query.
        abstract (str): Scientific abstract content.

    Returns:
        float: N-Gram overlap similarity (0 to 1).
    """

    # Lemmatize and normalize terms
    query_doc = nlp(query.lower())
    abstract_doc = nlp(abstract.lower())

    query_lemmatized = " ".join(
        token.lemma_ for token in query_doc if not token.is_stop and token.is_alpha
    )
    abstract_lemmatized = " ".join(
        [
            token.lemma_
            for token in abstract_doc
            if not token.is_stop and not token.is_punct
        ]
    )
    # Vectorize the lemmatized texts
    vectorizer = CountVectorizer(ngram_range=(1, 3))
    vectors = vectorizer.fit_transform([query_lemmatized, abstract_lemmatized])

    # Compute similarity
    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]

    return similarity
