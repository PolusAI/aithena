"""
End-to-end TrialGPT service orchestration (stateless).

Provides unified pipeline execution from patient description to ranked trials,
including keyword generation, retrieval, matching, and ranking. All processing
is done in-memory with no patient data persistence.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional

from sqlmodel import Session

from polus.aithena.clinical_aithena.models import TrialGPTStudy
from polus.aithena.clinical_aithena.pipeline.keyword_generation import generate_keywords
from polus.aithena.clinical_aithena.pipeline.matching import match_patient_to_trial
from polus.aithena.clinical_aithena.pipeline.ranking import rank_trial
from polus.aithena.clinical_aithena.retrieval import HybridRetriever

logger = logging.getLogger(__name__)

# Type alias for the optional progress callback.
# Signature: async def callback(status: str, message: str) -> None
ProgressCallback = Optional[Callable[[str, str], Coroutine[Any, Any, None]]]


async def _notify(callback: ProgressCallback, status: str, message: str) -> None:
    """Fire the progress callback if one was provided."""
    if callback is not None:
        try:
            await callback(status, message)
        except Exception:
            logger.warning("Progress callback failed for status=%s", status, exc_info=True)


async def match_patient(
    session: Session,
    patient_data: Dict[str, Any],
    top_n: int = 20,
    retrieval_method: str = "hybrid",
    model: Optional[str] = None,
    progress_callback: ProgressCallback = None,
) -> Dict[str, Any]:
    """
    Execute the complete stateless TrialGPT pipeline for a patient.
    
    This function orchestrates the entire pipeline:
    1. Generate keywords from patient clinical note (LLM)
    2. Generate query embedding (MedCPT)
    3. Retrieve top N candidate trials from database (hybrid search)
    4. Match patient to each trial (LLM per trial)
    5. Rank all trials (LLM per trial)
    6. Return sorted results
    
    All processing is done in-memory. NO database writes for patient data.
    
    Args:
        session: SQLModel database session (only used to read trials)
        patient_data: Dict with structure:
            {
                "clinical_note": str (required),
                "demographics": {
                    "age": int,
                    "gender": str,
                    ... (optional fields)
                }
            }
        top_n: Number of top-ranked trials to return (default 20)
        retrieval_method: "bm25", "vector", or "hybrid" (default "hybrid")
        model: LLM model to use (defaults to config value)
        progress_callback: Optional async callable(status, message) invoked at
            each pipeline stage so callers can relay real-time progress.
        
    Returns:
        Dict with pipeline outputs::

            {
                "results": [
                    {
                        "nct_id": str,
                        "title": str,
                        "relevance_score": float (0-100),
                        "eligibility_score": float (-R to R),
                        "relevance_explanation": str,
                        "eligibility_explanation": str,
                        "rank": int
                    },
                    ...
                ],
                "keywords": {
                    "summary": str,
                    "conditions": [str, ...]
                }
            }
        
    Raises:
        ValueError: If clinical_note is missing or empty
        Exception: If any pipeline stage fails
        
    Example:
        >>> patient_data = {
        ...     "clinical_note": "65yo male with metastatic melanoma...",
        ...     "demographics": {"age": 65, "gender": "male"}
        ... }
        >>> output = await match_patient(session, patient_data, top_n=20)
        >>> results = output["results"]
        >>> print(f"Top trial: {results[0]['nct_id']} "
        ...       f"(R={results[0]['relevance_score']:.1f}, "
        ...       f"E={results[0]['eligibility_score']:.1f})")
    """
    start_time = time.time()
    
    # Validate input
    if "clinical_note" not in patient_data:
        raise ValueError("patient_data must contain 'clinical_note'")
    
    clinical_note = patient_data["clinical_note"]
    if not clinical_note or not clinical_note.strip():
        raise ValueError("clinical_note cannot be empty")
    
    logger.info("Starting stateless TrialGPT pipeline")
    
    # Step 1: Generate keywords (in-memory, no DB write)
    await _notify(progress_callback, "generating_keywords",
                  "Analyzing patient information and extracting key medical terms...")
    logger.info("Step 1/5: Generating keywords...")
    keywords = generate_keywords(clinical_note, model=model)
    logger.info(f"Generated {len(keywords['conditions'])} keywords")
    
    # Step 2: Retrieve candidate trials using hybrid search (BM25 + vector)
    # Use a deep retrieval pool (matching TrialGPT's N=2000) then
    # trim to top_n after RRF fusion.  This maximises recall while
    # still limiting expensive downstream LLM calls to top_n trials.
    retrieval_depth = 2000

    await _notify(progress_callback, "retrieving_trials",
                  "Searching database for relevant clinical trials...")
    logger.info(
        f"Step 2/5: Retrieving trials via {retrieval_method} "
        f"(depth={retrieval_depth}, top_n={top_n})..."
    )

    if retrieval_method == "hybrid":
        # Use hybrid retrieval (BM25 + vector with RRF)
        retriever = HybridRetriever(session)
        retrieval_results = retriever.search(
            keywords["conditions"],
            top_n=top_n,
            retrieval_depth=retrieval_depth,
        )
    elif retrieval_method == "bm25":
        # BM25 only (using pg_search with TrialGPT field weighting)
        from polus.aithena.clinical_aithena.retrieval import (
            PgSearchRetriever,
        )
        retriever = PgSearchRetriever(session)
        query_text = " ".join(keywords["conditions"])
        retrieval_results = retriever.search(
            query_text, top_n=retrieval_depth,
        )[:top_n]
    elif retrieval_method == "vector":
        # Vector only (using pgvector + MedCPT)
        from polus.aithena.clinical_aithena.retrieval import (
            VectorRetriever,
        )
        retriever = VectorRetriever(session)
        retrieval_results = retriever.search_multi_conditions(
            keywords["conditions"],
            top_k=retrieval_depth,
        )[:top_n]
    else:
        raise ValueError(f"Invalid retrieval_method: {retrieval_method}")
    
    candidate_nct_ids = [nct_id for nct_id, _ in retrieval_results]
    logger.info(f"Retrieved {len(candidate_nct_ids)} candidate trials")
    
    if not candidate_nct_ids:
        logger.warning("No candidate trials found")
        return {"results": [], "keywords": keywords}
    
    # Fetch trial objects
    trials = []
    for nct_id in candidate_nct_ids:
        trial = session.get(TrialGPTStudy, nct_id)
        if trial:
            trials.append(trial)
        else:
            logger.warning(f"Trial {nct_id} not found in database")
    
    if not trials:
        logger.warning("No valid trials retrieved")
        return {"results": [], "keywords": keywords}
    
    # Step 4: Match patient to each trial (in-memory, no DB write)
    await _notify(progress_callback, "matching_criteria",
                  f"Analyzing eligibility criteria for {len(trials)} candidate trials...")
    logger.info(f"Step 4/5: Matching patient to {len(trials)} trials...")
    
    # Parallelize matching with a concurrency limiter to avoid rate limits
    max_concurrent = 5
    semaphore = asyncio.Semaphore(max_concurrent)
    loop = asyncio.get_event_loop()
    
    async def _match_one(trial):
        async with semaphore:
            return await loop.run_in_executor(
                None, match_patient_to_trial, clinical_note, trial, model
            )
    
    match_tasks = [_match_one(t) for t in trials]
    raw_match_results = await asyncio.gather(*match_tasks, return_exceptions=True)
    
    matching_results = []
    for trial, result in zip(trials, raw_match_results):
        if isinstance(result, Exception):
            logger.error(f"Failed to match trial {trial.nct_id}: {result}")
            continue
        matching_results.append((trial, result))
    
    if not matching_results:
        logger.warning("No matching results generated")
        return {"results": [], "keywords": keywords}
    
    logger.info(f"Successfully matched {len(matching_results)} trials")
    
    # Step 5: Rank all matched trials (in-memory, no DB write)
    await _notify(progress_callback, "ranking_trials",
                  f"Calculating relevance and eligibility scores for {len(matching_results)} trials...")
    logger.info(f"Step 5/5: Ranking {len(matching_results)} trials...")
    
    async def _rank_one(trial, match_result):
        async with semaphore:
            return await loop.run_in_executor(
                None, rank_trial, clinical_note, trial, match_result, model
            )
    
    rank_tasks = [_rank_one(t, mr) for t, mr in matching_results]
    raw_rank_results = await asyncio.gather(*rank_tasks, return_exceptions=True)
    
    rankings = []
    for (trial, _), result in zip(matching_results, raw_rank_results):
        if isinstance(result, Exception):
            logger.error(f"Failed to rank trial {trial.nct_id}: {result}")
            continue
        result["title"] = trial.title  # Add title for convenience
        rankings.append(result)
    
    if not rankings:
        logger.warning("No rankings generated")
        return {"results": [], "keywords": keywords}
    
    # Sort by relevance (primary) and eligibility (secondary)
    rankings.sort(
        key=lambda r: (r["relevance_score"], r["eligibility_score"]),
        reverse=True
    )
    
    # Add rank position
    for rank_idx, ranking in enumerate(rankings, start=1):
        ranking["rank"] = rank_idx
    
    await _notify(progress_callback, "responding",
                  "Processing complete, presenting results...")

    elapsed = time.time() - start_time
    logger.info(
        f"Pipeline completed in {elapsed:.1f}s: {len(rankings)} ranked trials. "
        f"Top trial: {rankings[0]['nct_id']} "
        f"(R={rankings[0]['relevance_score']:.1f}, E={rankings[0]['eligibility_score']:.1f})"
    )
    
    return {"results": rankings, "keywords": keywords}



