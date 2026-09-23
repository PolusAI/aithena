#!/usr/bin/env python
"""
Validation script to compare our BM25 implementation with original TrialGPT.

This script:
1. Loads the cached BM25 corpus from original TrialGPT
2. Fetches corresponding trials from our database
3. Compares tokenization outputs
4. Compares BM25 search rankings for sample queries
5. Reports detailed statistics on differences

Usage:
    python validation/validate_bm25_retrieval.py [--corpus sigir|trec_2021|trec_2022] [--sample-size N]
"""

import argparse
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import orjson
from sqlmodel import Session, create_engine, select

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from polus.aithena.clinical_aithena.models import TrialGPTStudy
from polus.aithena.clinical_aithena.retrieval import BM25Retriever
from polus.aithena.clinical_aithena.retrieval.tokenizer import tokenize_trial_for_bm25

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_trialgpt_bm25_corpus(corpus_name: str) -> Tuple[List[str], List[List[str]]]:
    """
    Load the cached BM25 corpus from original TrialGPT.
    
    Args:
        corpus_name: One of 'sigir', 'trec_2021', 'trec_2022'
        
    Returns:
        Tuple of (nct_ids, tokenized_corpus)
    """
    trialgpt_path = Path(__file__).parent.parent.parent.parent / "TrialGPT"
    corpus_file = trialgpt_path / "trialgpt_retrieval" / f"bm25_corpus_{corpus_name}.json"
    
    if not corpus_file.exists():
        raise FileNotFoundError(f"TrialGPT corpus file not found: {corpus_file}")
    
    logger.info(f"Loading TrialGPT BM25 corpus from {corpus_file}")
    with open(corpus_file, "rb") as f:
        data = orjson.loads(f.read())
    
    nct_ids = data["corpus_nctids"]
    tokenized_corpus = data["tokenized_corpus"]
    
    logger.info(f"Loaded {len(nct_ids)} trials from TrialGPT corpus")
    return nct_ids, tokenized_corpus


def load_trialgpt_queries(corpus_name: str) -> Dict[str, Dict]:
    """
    Load patient queries/keywords from TrialGPT results.
    
    Args:
        corpus_name: One of 'sigir', 'trec_2021', 'trec_2022'
        
    Returns:
        Dictionary mapping query_id to {summary, conditions}
    """
    trialgpt_path = Path(__file__).parent.parent.parent.parent / "TrialGPT"
    keywords_file = trialgpt_path / "results" / f"retrieval_keywords_gpt-4.1_{corpus_name}.json"
    
    if not keywords_file.exists():
        raise FileNotFoundError(f"TrialGPT keywords file not found: {keywords_file}")
    
    logger.info(f"Loading TrialGPT queries from {keywords_file}")
    with open(keywords_file, "rb") as f:
        queries = orjson.loads(f.read())
    
    logger.info(f"Loaded {len(queries)} queries")
    return queries


def compare_tokenization(
    nct_id: str,
    trialgpt_tokens: List[str],
    our_tokens: List[str],
) -> Dict:
    """
    Compare tokenization between TrialGPT and our implementation.
    
    Returns:
        Dictionary with comparison metrics
    """
    trialgpt_set = set(trialgpt_tokens)
    our_set = set(our_tokens)
    
    return {
        "nct_id": nct_id,
        "trialgpt_token_count": len(trialgpt_tokens),
        "our_token_count": len(our_tokens),
        "token_count_diff": len(our_tokens) - len(trialgpt_tokens),
        "unique_tokens_trialgpt": len(trialgpt_set),
        "unique_tokens_ours": len(our_set),
        "tokens_only_in_trialgpt": len(trialgpt_set - our_set),
        "tokens_only_in_ours": len(our_set - trialgpt_set),
        "exact_match": trialgpt_tokens == our_tokens,
    }


def validate_tokenization(
    session: Session,
    trialgpt_nct_ids: List[str],
    trialgpt_tokenized: List[List[str]],
    sample_size: int = 100,
) -> Dict:
    """
    Validate our tokenization against TrialGPT's cached tokenization.
    
    Args:
        session: Database session
        trialgpt_nct_ids: NCT IDs from TrialGPT corpus
        trialgpt_tokenized: Tokenized corpus from TrialGPT
        sample_size: Number of trials to sample for validation
        
    Returns:
        Validation statistics
    """
    logger.info(f"Validating tokenization for {sample_size} trials...")
    
    # Sample trials
    sample_indices = list(range(0, len(trialgpt_nct_ids), len(trialgpt_nct_ids) // sample_size))[:sample_size]
    
    stats = {
        "total_compared": 0,
        "exact_matches": 0,
        "missing_in_db": 0,
        "token_count_diffs": [],
        "mismatches": [],
    }
    
    for idx in sample_indices:
        nct_id = trialgpt_nct_ids[idx]
        trialgpt_tokens = trialgpt_tokenized[idx]
        
        # Fetch trial from our database
        statement = select(
            TrialGPTStudy.nct_id,
            TrialGPTStudy.title,
            TrialGPTStudy.text,
            TrialGPTStudy.metadata_json,
        ).where(TrialGPTStudy.nct_id == nct_id)
        
        result = session.exec(statement).first()
        
        if not result:
            stats["missing_in_db"] += 1
            logger.warning(f"Trial {nct_id} not found in database")
            continue
        
        # Unpack result
        _, title, text, metadata_json = result
        
        # Parse metadata
        if isinstance(metadata_json, str):
            metadata = orjson.loads(metadata_json)
        else:
            metadata = metadata_json
        
        # Tokenize using our implementation
        our_tokens = tokenize_trial_for_bm25(
            title=title,
            diseases_list=metadata.get('diseases_list', []),
            text=text,
        )
        
        # Compare
        comparison = compare_tokenization(nct_id, trialgpt_tokens, our_tokens)
        stats["total_compared"] += 1
        
        if comparison["exact_match"]:
            stats["exact_matches"] += 1
        else:
            stats["mismatches"].append(comparison)
        
        stats["token_count_diffs"].append(comparison["token_count_diff"])
    
    # Calculate summary statistics
    if stats["token_count_diffs"]:
        import statistics
        stats["avg_token_count_diff"] = statistics.mean(stats["token_count_diffs"])
        stats["max_token_count_diff"] = max(stats["token_count_diffs"])
        stats["min_token_count_diff"] = min(stats["token_count_diffs"])
    
    return stats


def compare_rankings(
    ranking1: List[Tuple[str, float]],
    ranking2: List[Tuple[str, float]],
    k: int = 100,
) -> Dict:
    """
    Compare two ranked lists.
    
    Args:
        ranking1: First ranking (TrialGPT)
        ranking2: Second ranking (our implementation)
        k: Top-k to compare
        
    Returns:
        Comparison metrics including overlap, rank correlation, etc.
    """
    # Extract top-k NCT IDs
    top_k_1 = [nct_id for nct_id, _ in ranking1[:k]]
    top_k_2 = [nct_id for nct_id, _ in ranking2[:k]]
    
    # Calculate overlap
    overlap = len(set(top_k_1) & set(top_k_2))
    overlap_ratio = overlap / k if k > 0 else 0
    
    # Calculate rank correlation for overlapping items
    common_items = set(top_k_1) & set(top_k_2)
    if len(common_items) > 0:
        rank_1 = {nct_id: i for i, nct_id in enumerate(top_k_1)}
        rank_2 = {nct_id: i for i, nct_id in enumerate(top_k_2)}
        
        rank_diffs = [abs(rank_1.get(item, k) - rank_2.get(item, k)) for item in common_items]
        avg_rank_diff = sum(rank_diffs) / len(rank_diffs)
    else:
        avg_rank_diff = None
    
    return {
        "top_k": k,
        "overlap": overlap,
        "overlap_ratio": overlap_ratio,
        "avg_rank_diff": avg_rank_diff,
        "only_in_trialgpt": len(set(top_k_1) - set(top_k_2)),
        "only_in_ours": len(set(top_k_2) - set(top_k_1)),
    }


def validate_retrieval(
    session: Session,
    queries: Dict[str, Dict],
    sample_size: int = 10,
) -> Dict:
    """
    Validate BM25 retrieval by comparing rankings with TrialGPT.
    
    Note: We can't directly compare with TrialGPT's results since they
    used a hybrid retriever (BM25 + MedCPT). This validates that our
    BM25 component produces reasonable rankings.
    
    Args:
        session: Database session
        queries: Patient queries from TrialGPT
        sample_size: Number of queries to test
        
    Returns:
        Retrieval statistics
    """
    logger.info(f"Testing BM25 retrieval on {sample_size} sample queries...")
    
    retriever = BM25Retriever(session)
    
    stats = {
        "queries_tested": 0,
        "successful_retrievals": 0,
        "empty_results": 0,
        "avg_results_count": [],
        "sample_results": [],
    }
    
    # Sample queries
    query_ids = list(queries.keys())[:sample_size]
    
    for query_id in query_ids:
        query_data = queries[query_id]
        
        # Use conditions as query terms (this is what TrialGPT does for BM25)
        conditions = query_data.get("conditions", [])
        query_text = " ".join(conditions[:10])  # Use first 10 conditions
        
        if not query_text.strip():
            logger.warning(f"Empty query for {query_id}, skipping")
            continue
        
        stats["queries_tested"] += 1
        
        # Run our BM25 retrieval
        results = retriever.search(query_text, top_n=100)
        
        if results:
            stats["successful_retrievals"] += 1
            stats["avg_results_count"].append(len(results))
            
            # Store sample for inspection
            if len(stats["sample_results"]) < 3:
                stats["sample_results"].append({
                    "query_id": query_id,
                    "query_text": query_text[:200],
                    "top_5_results": [
                        {"nct_id": nct_id, "score": f"{score:.4f}"}
                        for nct_id, score in results[:5]
                    ],
                })
        else:
            stats["empty_results"] += 1
            logger.warning(f"No results for query {query_id}")
    
    # Calculate averages
    if stats["avg_results_count"]:
        import statistics
        stats["avg_results_count"] = statistics.mean(stats["avg_results_count"])
    else:
        stats["avg_results_count"] = 0
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Validate BM25 implementation against TrialGPT")
    parser.add_argument(
        "--corpus",
        choices=["sigir", "trec_2021", "trec_2022"],
        default="sigir",
        help="Which corpus to validate against",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=100,
        help="Number of trials to sample for tokenization validation",
    )
    parser.add_argument(
        "--query-sample-size",
        type=int,
        default=10,
        help="Number of queries to test for retrieval validation",
    )
    parser.add_argument(
        "--database-url",
        default="postgresql+psycopg://postgres:CHANGE_ME_POSTGRES_PASSWORD@localhost:5432/clinical_aithena",
        help="Database connection URL",
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("BM25 Implementation Validation")
    logger.info("=" * 80)
    logger.info(f"Corpus: {args.corpus}")
    logger.info(f"Sample size: {args.sample_size}")
    logger.info("")
    
    # Load TrialGPT data
    try:
        trialgpt_nct_ids, trialgpt_tokenized = load_trialgpt_bm25_corpus(args.corpus)
        trialgpt_queries = load_trialgpt_queries(args.corpus)
    except FileNotFoundError as e:
        logger.error(f"Failed to load TrialGPT data: {e}")
        logger.error("Make sure TrialGPT repository is available at ../../TrialGPT/")
        return 1
    
    # Connect to database
    logger.info(f"Connecting to database: {args.database_url.split('@')[1]}")
    engine = create_engine(args.database_url)
    
    # Validate tokenization
    logger.info("")
    logger.info("=" * 80)
    logger.info("TOKENIZATION VALIDATION")
    logger.info("=" * 80)
    
    with Session(engine) as session:
        tokenization_stats = validate_tokenization(
            session,
            trialgpt_nct_ids,
            trialgpt_tokenized,
            sample_size=args.sample_size,
        )
    
    logger.info("")
    logger.info("Tokenization Results:")
    logger.info(f"  Total compared: {tokenization_stats['total_compared']}")
    logger.info(f"  Exact matches: {tokenization_stats['exact_matches']}")
    logger.info(f"  Missing in DB: {tokenization_stats['missing_in_db']}")
    if tokenization_stats['total_compared'] > 0:
        match_rate = tokenization_stats['exact_matches'] / tokenization_stats['total_compared'] * 100
        logger.info(f"  Match rate: {match_rate:.2f}%")
    
    if 'avg_token_count_diff' in tokenization_stats:
        logger.info(f"  Avg token count diff: {tokenization_stats['avg_token_count_diff']:.2f}")
        logger.info(f"  Max token count diff: {tokenization_stats['max_token_count_diff']}")
        logger.info(f"  Min token count diff: {tokenization_stats['min_token_count_diff']}")
    
    # Show first few mismatches
    if tokenization_stats['mismatches']:
        logger.info("")
        logger.info(f"First 5 mismatches (out of {len(tokenization_stats['mismatches'])}):")
        for i, mismatch in enumerate(tokenization_stats['mismatches'][:5], 1):
            logger.info(f"  {i}. {mismatch['nct_id']}")
            logger.info(f"     TrialGPT tokens: {mismatch['trialgpt_token_count']}")
            logger.info(f"     Our tokens: {mismatch['our_token_count']}")
            logger.info(f"     Diff: {mismatch['token_count_diff']}")
            logger.info(f"     Unique tokens only in TrialGPT: {mismatch['tokens_only_in_trialgpt']}")
            logger.info(f"     Unique tokens only in ours: {mismatch['tokens_only_in_ours']}")
    
    # Validate retrieval
    logger.info("")
    logger.info("=" * 80)
    logger.info("RETRIEVAL VALIDATION")
    logger.info("=" * 80)
    
    with Session(engine) as session:
        retrieval_stats = validate_retrieval(
            session,
            trialgpt_queries,
            sample_size=args.query_sample_size,
        )
    
    logger.info("")
    logger.info("Retrieval Results:")
    logger.info(f"  Queries tested: {retrieval_stats['queries_tested']}")
    logger.info(f"  Successful retrievals: {retrieval_stats['successful_retrievals']}")
    logger.info(f"  Empty results: {retrieval_stats['empty_results']}")
    logger.info(f"  Avg results per query: {retrieval_stats['avg_results_count']:.1f}")
    
    if retrieval_stats['sample_results']:
        logger.info("")
        logger.info("Sample retrieval results:")
        for i, sample in enumerate(retrieval_stats['sample_results'], 1):
            logger.info(f"  {i}. Query: {sample['query_id']}")
            logger.info(f"     Text: {sample['query_text']}")
            logger.info(f"     Top 5 results:")
            for result in sample['top_5_results']:
                logger.info(f"       - {result['nct_id']}: {result['score']}")
    
    # Final summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    
    if tokenization_stats['total_compared'] > 0:
        match_rate = tokenization_stats['exact_matches'] / tokenization_stats['total_compared'] * 100
        if match_rate == 100:
            logger.info("✅ TOKENIZATION: Perfect match! All samples match TrialGPT exactly.")
        elif match_rate >= 95:
            logger.info(f"⚠️  TOKENIZATION: Mostly matching ({match_rate:.2f}%), investigate mismatches.")
        else:
            logger.info(f"❌ TOKENIZATION: Significant differences ({match_rate:.2f}%), needs investigation.")
    
    if retrieval_stats['queries_tested'] > 0:
        success_rate = retrieval_stats['successful_retrievals'] / retrieval_stats['queries_tested'] * 100
        if success_rate == 100:
            logger.info("✅ RETRIEVAL: All queries returned results successfully.")
        elif success_rate >= 95:
            logger.info(f"⚠️  RETRIEVAL: Most queries successful ({success_rate:.2f}%).")
        else:
            logger.info(f"❌ RETRIEVAL: Many failed queries ({success_rate:.2f}%), needs investigation.")
    
    logger.info("")
    logger.info("Validation complete!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

