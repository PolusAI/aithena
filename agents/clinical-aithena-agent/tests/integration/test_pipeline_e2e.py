"""
End-to-end integration tests for the TrialGPT pipeline.

Tests the full pipeline (keyword generation → retrieval → matching → ranking)
against a real database. LLM calls are mocked with deterministic responses
so the tests are reproducible without a live LLM endpoint.
"""

import json
import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlmodel import Session, create_engine, select

from polus.aithena.clinical_aithena.models import TrialGPTStudy
from polus.aithena.clinical_aithena.pipeline.service import match_patient


# Skip entire module if no database
pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Pipeline E2E tests require TEST_DATABASE_URL",
)


# ---------------------------------------------------------------------------
# Helpers for mocking LLM responses
# ---------------------------------------------------------------------------

SAMPLE_PATIENT = {
    "clinical_note": (
        "A 65-year-old male presents with stage IIIA non-small cell lung cancer "
        "(NSCLC), ECOG performance status 1. The patient was diagnosed 3 months "
        "ago after presenting with persistent cough and hemoptysis. CT scan shows "
        "a 4.5 cm right upper lobe mass with ipsilateral mediastinal lymph node "
        "involvement. PET scan confirms FDG-avid disease limited to the thorax. "
        "No brain metastases on MRI. History of hypertension, well-controlled on "
        "lisinopril. Former smoker, quit 5 years ago."
    ),
    "demographics": {"age": 65, "gender": "male"},
}


def _mock_keyword_response():
    """Return a realistic keyword generation response."""
    return {
        "summary": (
            "65-year-old male with stage IIIA NSCLC, ECOG 1, "
            "right upper lobe mass with mediastinal lymph node involvement"
        ),
        "conditions": [
            "non-small cell lung cancer stage III",
            "NSCLC locally advanced",
            "lung cancer immunotherapy",
            "lung cancer chemotherapy",
            "thoracic radiation therapy",
        ],
    }


def _mock_matching_response():
    """Return a realistic matching result dict."""
    return {
        "inclusion": {
            "0": {
                "criterion": "Adults aged 18 and older",
                "prediction": "included",
                "confidence": 0.95,
                "evident_sentences": [0],
            },
            "1": {
                "criterion": "Histologically confirmed NSCLC",
                "prediction": "included",
                "confidence": 0.90,
                "evident_sentences": [0, 1],
            },
        },
        "exclusion": {
            "0": {
                "criterion": "Prior systemic therapy",
                "prediction": "not excluded",
                "confidence": 0.85,
                "evident_sentences": [],
            },
        },
    }


def _mock_ranking_response(nct_id, relevance=75.0, eligibility=50.0):
    """Return a realistic ranking result dict."""
    return {
        "nct_id": nct_id,
        "relevance_score": relevance,
        "eligibility_score": eligibility,
        "relevance_explanation": "Patient has matching disease and stage.",
        "eligibility_explanation": "Meets key inclusion criteria.",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPipelineEndToEnd:
    """Full pipeline integration tests with mocked LLM but real DB/retrieval."""

    @pytest.fixture()
    def pg_session(self):
        """Per-test PostgreSQL session."""
        url = os.getenv("TEST_DATABASE_URL")
        engine = create_engine(url, echo=False)
        with Session(engine) as session:
            yield session
        engine.dispose()

    @pytest.fixture()
    def trial_nct_ids(self, pg_session):
        """Get real NCT IDs from the database for mock responses."""
        statement = (
            select(TrialGPTStudy.nct_id)
            .where(TrialGPTStudy.text_embedding != None)  # noqa: E711
            .limit(5)
        )
        ids = pg_session.exec(statement).all()
        if len(ids) < 3:
            pytest.skip("Need at least 3 trials with embeddings")
        return ids

    @pytest.mark.asyncio
    @patch("polus.aithena.clinical_aithena.pipeline.service.rank_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.match_patient_to_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.generate_keywords")
    async def test_full_pipeline_hybrid(
        self,
        mock_gen_keywords,
        mock_match,
        mock_rank,
        pg_session,
        trial_nct_ids,
    ):
        """E2E: keyword gen → hybrid retrieval (real) → match → rank."""
        mock_gen_keywords.return_value = _mock_keyword_response()
        mock_match.return_value = _mock_matching_response()
        # rank_trial is called once per retrieved trial; return varying scores
        mock_rank.side_effect = lambda note, trial, match_result, model=None: (
            _mock_ranking_response(trial.nct_id, relevance=80.0, eligibility=60.0)
        )

        output = await match_patient(
            pg_session,
            SAMPLE_PATIENT,
            top_n=5,
            retrieval_method="hybrid",
        )
        results = output["results"]

        # Pipeline should return results
        assert len(results) > 0
        assert len(results) <= 5

        # Results should be properly formatted
        for r in results:
            assert "nct_id" in r
            assert "relevance_score" in r
            assert "eligibility_score" in r
            assert "rank" in r
            assert r["rank"] >= 1
            assert 0 <= r["relevance_score"] <= 100

        # Results should be sorted by rank
        ranks = [r["rank"] for r in results]
        assert ranks == sorted(ranks)

    @pytest.mark.asyncio
    @patch("polus.aithena.clinical_aithena.pipeline.service.rank_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.match_patient_to_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.generate_keywords")
    async def test_full_pipeline_bm25_only(
        self,
        mock_gen_keywords,
        mock_match,
        mock_rank,
        pg_session,
        trial_nct_ids,
    ):
        """E2E with BM25-only retrieval method.

        Note: BM25-only mode joins all conditions into a single query string
        which is used as a phrase_prefix search. With many conditions this may
        return 0 results (too specific). Use a short, single-condition keyword
        to exercise the BM25 path reliably.
        """
        mock_gen_keywords.return_value = {
            "summary": "Patient with lung cancer",
            "conditions": ["lung cancer"],
        }
        mock_match.return_value = _mock_matching_response()
        mock_rank.side_effect = lambda note, trial, match_result, model=None: (
            _mock_ranking_response(trial.nct_id, relevance=70.0, eligibility=40.0)
        )

        output = await match_patient(
            pg_session,
            SAMPLE_PATIENT,
            top_n=5,
            retrieval_method="bm25",
        )
        results = output["results"]

        assert len(results) > 0
        for r in results:
            assert "nct_id" in r

    @pytest.mark.asyncio
    @patch("polus.aithena.clinical_aithena.pipeline.service.rank_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.match_patient_to_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.generate_keywords")
    async def test_full_pipeline_vector_only(
        self,
        mock_gen_keywords,
        mock_match,
        mock_rank,
        pg_session,
        trial_nct_ids,
    ):
        """E2E with vector-only retrieval method."""
        mock_gen_keywords.return_value = _mock_keyword_response()
        mock_match.return_value = _mock_matching_response()
        mock_rank.side_effect = lambda note, trial, match_result, model=None: (
            _mock_ranking_response(trial.nct_id, relevance=65.0, eligibility=35.0)
        )

        output = await match_patient(
            pg_session,
            SAMPLE_PATIENT,
            top_n=5,
            retrieval_method="vector",
        )
        results = output["results"]

        assert len(results) > 0
        for r in results:
            assert "nct_id" in r

    @pytest.mark.asyncio
    @patch("polus.aithena.clinical_aithena.pipeline.service.rank_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.match_patient_to_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.generate_keywords")
    async def test_pipeline_matching_failure_resilience(
        self,
        mock_gen_keywords,
        mock_match,
        mock_rank,
        pg_session,
        trial_nct_ids,
    ):
        """Pipeline continues when matching fails for some trials."""
        mock_gen_keywords.return_value = _mock_keyword_response()

        call_count = 0

        def _flaky_match(note, trial, model=None):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise RuntimeError("Simulated LLM timeout")
            return _mock_matching_response()

        mock_match.side_effect = _flaky_match
        mock_rank.side_effect = lambda note, trial, match_result, model=None: (
            _mock_ranking_response(trial.nct_id)
        )

        output = await match_patient(
            pg_session,
            SAMPLE_PATIENT,
            top_n=5,
            retrieval_method="hybrid",
        )
        results = output["results"]

        # Should still return some results despite failures
        assert isinstance(results, list)

    @pytest.mark.asyncio
    @patch("polus.aithena.clinical_aithena.pipeline.service.rank_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.match_patient_to_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.generate_keywords")
    async def test_pipeline_ranking_failure_resilience(
        self,
        mock_gen_keywords,
        mock_match,
        mock_rank,
        pg_session,
        trial_nct_ids,
    ):
        """Pipeline continues when ranking fails for some trials."""
        mock_gen_keywords.return_value = _mock_keyword_response()
        mock_match.return_value = _mock_matching_response()

        call_count = 0

        def _flaky_rank(note, trial, match_result, model=None):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:
                raise RuntimeError("Simulated ranking failure")
            return _mock_ranking_response(trial.nct_id)

        mock_rank.side_effect = _flaky_rank

        output = await match_patient(
            pg_session,
            SAMPLE_PATIENT,
            top_n=5,
            retrieval_method="hybrid",
        )
        results = output["results"]

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_pipeline_missing_clinical_note(self, pg_session):
        """Pipeline raises ValueError for missing clinical note."""
        with pytest.raises(ValueError, match="clinical_note"):
            await match_patient(pg_session, {})

    @pytest.mark.asyncio
    async def test_pipeline_empty_clinical_note(self, pg_session):
        """Pipeline raises ValueError for empty clinical note."""
        with pytest.raises(ValueError, match="empty"):
            await match_patient(pg_session, {"clinical_note": "   "})

    @pytest.mark.asyncio
    @patch("polus.aithena.clinical_aithena.pipeline.service.generate_keywords")
    async def test_pipeline_invalid_retrieval_method(
        self, mock_gen_keywords, pg_session
    ):
        """Pipeline raises ValueError for invalid retrieval method."""
        mock_gen_keywords.return_value = _mock_keyword_response()
        with pytest.raises(ValueError, match="Invalid retrieval_method"):
            await match_patient(
                pg_session,
                SAMPLE_PATIENT,
                retrieval_method="unknown",
            )


class TestPipelineRetrieval:
    """Test that the pipeline's retrieval step returns real database trials."""

    @pytest.fixture()
    def pg_session(self):
        url = os.getenv("TEST_DATABASE_URL")
        engine = create_engine(url, echo=False)
        with Session(engine) as session:
            yield session
        engine.dispose()

    @pytest.mark.asyncio
    @patch("polus.aithena.clinical_aithena.pipeline.service.rank_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.match_patient_to_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.generate_keywords")
    async def test_retrieved_trials_exist_in_db(
        self,
        mock_gen_keywords,
        mock_match,
        mock_rank,
        pg_session,
    ):
        """All returned trial NCT IDs should exist in the database."""
        mock_gen_keywords.return_value = _mock_keyword_response()
        mock_match.return_value = _mock_matching_response()
        mock_rank.side_effect = lambda note, trial, match_result, model=None: (
            _mock_ranking_response(trial.nct_id)
        )

        output = await match_patient(
            pg_session,
            SAMPLE_PATIENT,
            top_n=10,
            retrieval_method="hybrid",
        )
        results = output["results"]

        for r in results:
            trial = pg_session.get(TrialGPTStudy, r["nct_id"])
            assert trial is not None, f"Trial {r['nct_id']} not in database"
            assert trial.title is not None

    @pytest.mark.asyncio
    @patch("polus.aithena.clinical_aithena.pipeline.service.rank_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.match_patient_to_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.generate_keywords")
    async def test_different_retrieval_methods_produce_results(
        self,
        mock_gen_keywords,
        mock_match,
        mock_rank,
        pg_session,
    ):
        """All three retrieval methods should return at least some results."""
        mock_gen_keywords.return_value = _mock_keyword_response()
        mock_match.return_value = _mock_matching_response()
        mock_rank.side_effect = lambda note, trial, match_result, model=None: (
            _mock_ranking_response(trial.nct_id)
        )

        for method in ("hybrid", "bm25", "vector"):
            # BM25-only mode joins conditions into a single phrase query,
            # so use a short keyword list that works for phrase_prefix.
            if method == "bm25":
                mock_gen_keywords.return_value = {
                    "summary": "Patient with lung cancer",
                    "conditions": ["lung cancer"],
                }
            else:
                mock_gen_keywords.return_value = _mock_keyword_response()

            output = await match_patient(
                pg_session,
                SAMPLE_PATIENT,
                top_n=5,
                retrieval_method=method,
            )
            results = output["results"]
            assert len(results) > 0, f"No results from {method} retrieval"
