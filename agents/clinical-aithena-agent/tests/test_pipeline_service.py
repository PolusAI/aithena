"""Tests for the end-to-end TrialGPT pipeline orchestration service.

Tests the stateless match_patient function in pipeline/service.py, which
orchestrates keyword generation, retrieval, matching, and ranking.
"""

from unittest.mock import AsyncMock, Mock, MagicMock, patch

import pytest

# Import CTGovStudy first so SQLAlchemy can resolve the TrialGPTStudy relationship
from polus.aithena.clinical_aithena.clients.ctgov.models import CTGovStudy  # noqa: F401
from polus.aithena.clinical_aithena.models import TrialGPTStudy
from polus.aithena.clinical_aithena.pipeline.service import match_patient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_patient_data():
    """Sample patient data dict."""
    return {
        "clinical_note": (
            "Patient is a 55-year-old female with metastatic melanoma. "
            "She has been treated with ipilimumab with disease progression. "
            "ECOG performance status 1. No prior organ transplant."
        ),
        "demographics": {"age": 55, "gender": "female"},
    }


@pytest.fixture
def sample_trials():
    """Create sample TrialGPTStudy objects for testing."""
    trials = []
    for i in range(3):
        trial = TrialGPTStudy(
            nct_id=f"NCT0000000{i}",
            title=f"Melanoma Trial {i}",
            text=f"A trial for melanoma treatment {i}",
            metadata_json={
                "brief_title": f"Melanoma Trial {i}",
                "diseases_list": ["Melanoma"],
                "drugs_list": [f"Drug{i}"],
                "brief_summary": f"Testing treatment {i} for melanoma",
                "inclusion_criteria": "Age >= 18\n\nMetastatic melanoma",
                "exclusion_criteria": "Pregnant\n\nPrior organ transplant",
            },
        )
        trials.append(trial)
    return trials


@pytest.fixture
def mock_session(sample_trials):
    """Create a mock SQLModel session that returns sample trials."""
    session = MagicMock()
    # Map nct_id to trial objects for session.get()
    trial_map = {t.nct_id: t for t in sample_trials}
    session.get.side_effect = lambda model, nct_id: trial_map.get(nct_id)
    return session


@pytest.fixture
def mock_keywords():
    """Sample keyword generation output."""
    return {
        "summary": "55-year-old female with metastatic melanoma, prior ipilimumab",
        "conditions": ["melanoma", "metastatic melanoma", "skin cancer"],
    }


@pytest.fixture
def mock_retrieval_results():
    """Retrieval results: list of (nct_id, score) tuples."""
    return [
        ("NCT00000000", 0.95),
        ("NCT00000001", 0.82),
        ("NCT00000002", 0.71),
    ]


@pytest.fixture
def mock_matching_result():
    """Per-trial matching result."""
    return {
        "inclusion": {
            "0": ["Meets age criterion", [0], "included"],
            "1": ["Has metastatic melanoma", [0], "included"],
        },
        "exclusion": {
            "0": ["Not pregnant", [], "not excluded"],
            "1": ["No organ transplant", [3], "not excluded"],
        },
    }


@pytest.fixture
def mock_ranking_result():
    """Factory for per-trial ranking result."""
    def _make(nct_id, r=75.0, e=50.0):
        return {
            "nct_id": nct_id,
            "relevance_score": r,
            "relevance_explanation": f"Patient relevant to {nct_id}",
            "eligibility_score": e,
            "eligibility_explanation": f"Patient eligible for {nct_id}",
        }
    return _make


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestMatchPatient:
    """Tests for the match_patient orchestration function."""

    @pytest.mark.asyncio
    @patch("polus.aithena.clinical_aithena.pipeline.service.rank_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.match_patient_to_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.HybridRetriever")
    @patch("polus.aithena.clinical_aithena.pipeline.service.generate_keywords")
    async def test_full_pipeline_success(
        self,
        mock_gen_keywords,
        mock_retriever_cls,
        mock_match,
        mock_rank,
        sample_patient_data,
        mock_session,
        mock_keywords,
        mock_retrieval_results,
        mock_matching_result,
        mock_ranking_result,
    ):
        """Test successful end-to-end pipeline execution."""
        # Setup mocks
        mock_gen_keywords.return_value = mock_keywords

        mock_retriever = MagicMock()
        mock_retriever.search.return_value = mock_retrieval_results
        mock_retriever_cls.return_value = mock_retriever

        mock_match.return_value = mock_matching_result

        # Return different scores for each trial to test sorting
        mock_rank.side_effect = [
            mock_ranking_result("NCT00000000", r=85.0, e=70.0),
            mock_ranking_result("NCT00000001", r=60.0, e=30.0),
            mock_ranking_result("NCT00000002", r=90.0, e=80.0),
        ]

        output = await match_patient(
            mock_session, sample_patient_data, top_n=20
        )
        results = output["results"]

        # Should return 3 ranked results
        assert len(results) == 3

        # Results should be sorted by relevance (descending)
        assert results[0]["relevance_score"] >= results[1]["relevance_score"]
        assert results[1]["relevance_score"] >= results[2]["relevance_score"]

        # Top result should be NCT00000002 (R=90)
        assert results[0]["nct_id"] == "NCT00000002"
        assert results[0]["rank"] == 1

        # Each result should have a rank
        assert [r["rank"] for r in results] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_missing_clinical_note_raises(self, mock_session):
        """Test that missing clinical_note key raises ValueError."""
        patient_data = {"demographics": {"age": 45}}

        with pytest.raises(ValueError, match="clinical_note"):
            await match_patient(mock_session, patient_data)

    @pytest.mark.asyncio
    async def test_empty_clinical_note_raises(self, mock_session):
        """Test that empty clinical note raises ValueError."""
        patient_data = {"clinical_note": ""}

        with pytest.raises(ValueError, match="cannot be empty"):
            await match_patient(mock_session, patient_data)

    @pytest.mark.asyncio
    @patch("polus.aithena.clinical_aithena.pipeline.service.rank_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.match_patient_to_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.HybridRetriever")
    @patch("polus.aithena.clinical_aithena.pipeline.service.generate_keywords")
    async def test_no_retrieval_results_returns_empty(
        self,
        mock_gen_keywords,
        mock_retriever_cls,
        mock_match,
        mock_rank,
        sample_patient_data,
        mock_session,
        mock_keywords,
    ):
        """Test that empty retrieval results return an empty list."""
        mock_gen_keywords.return_value = mock_keywords

        mock_retriever = MagicMock()
        mock_retriever.search.return_value = []  # No results
        mock_retriever_cls.return_value = mock_retriever

        output = await match_patient(
            mock_session, sample_patient_data, top_n=20
        )
        results = output["results"]

        assert results == []
        mock_match.assert_not_called()
        mock_rank.assert_not_called()

    @pytest.mark.asyncio
    @patch("polus.aithena.clinical_aithena.pipeline.service.rank_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.match_patient_to_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.HybridRetriever")
    @patch("polus.aithena.clinical_aithena.pipeline.service.generate_keywords")
    async def test_matching_failure_continues(
        self,
        mock_gen_keywords,
        mock_retriever_cls,
        mock_match,
        mock_rank,
        sample_patient_data,
        mock_session,
        mock_keywords,
        mock_retrieval_results,
        mock_ranking_result,
    ):
        """Test that matching failure for one trial doesn't abort the pipeline."""
        mock_gen_keywords.return_value = mock_keywords

        mock_retriever = MagicMock()
        mock_retriever.search.return_value = mock_retrieval_results
        mock_retriever_cls.return_value = mock_retriever

        # First call succeeds, second raises, third succeeds
        mock_match.side_effect = [
            {"inclusion": {"0": ["ok", [], "included"]}, "exclusion": {}},
            Exception("LLM timeout"),
            {"inclusion": {"0": ["ok", [], "included"]}, "exclusion": {}},
        ]

        mock_rank.side_effect = [
            mock_ranking_result("NCT00000000", r=80.0, e=60.0),
            mock_ranking_result("NCT00000002", r=70.0, e=40.0),
        ]

        output = await match_patient(
            mock_session, sample_patient_data, top_n=20
        )
        results = output["results"]

        # Should still get 2 results (the one that failed matching is skipped)
        assert len(results) == 2
        nct_ids = {r["nct_id"] for r in results}
        assert "NCT00000001" not in nct_ids  # The one that failed

    @pytest.mark.asyncio
    @patch("polus.aithena.clinical_aithena.pipeline.service.rank_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.match_patient_to_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.HybridRetriever")
    @patch("polus.aithena.clinical_aithena.pipeline.service.generate_keywords")
    async def test_ranking_failure_continues(
        self,
        mock_gen_keywords,
        mock_retriever_cls,
        mock_match,
        mock_rank,
        sample_patient_data,
        mock_session,
        mock_keywords,
        mock_retrieval_results,
        mock_matching_result,
        mock_ranking_result,
    ):
        """Test that ranking failure for one trial doesn't abort the pipeline."""
        mock_gen_keywords.return_value = mock_keywords

        mock_retriever = MagicMock()
        mock_retriever.search.return_value = mock_retrieval_results
        mock_retriever_cls.return_value = mock_retriever

        mock_match.return_value = mock_matching_result

        # First ranks ok, second fails, third ranks ok
        mock_rank.side_effect = [
            mock_ranking_result("NCT00000000", r=80.0, e=60.0),
            Exception("Malformed LLM output"),
            mock_ranking_result("NCT00000002", r=70.0, e=40.0),
        ]

        output = await match_patient(
            mock_session, sample_patient_data, top_n=20
        )
        results = output["results"]

        # Should still get 2 results (the one that failed ranking is skipped)
        assert len(results) == 2

    @pytest.mark.asyncio
    @patch("polus.aithena.clinical_aithena.pipeline.service.rank_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.match_patient_to_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.HybridRetriever")
    @patch("polus.aithena.clinical_aithena.pipeline.service.generate_keywords")
    async def test_invalid_retrieval_method_raises(
        self,
        mock_gen_keywords,
        mock_retriever_cls,
        mock_match,
        mock_rank,
        sample_patient_data,
        mock_session,
        mock_keywords,
    ):
        """Test that invalid retrieval method raises ValueError."""
        mock_gen_keywords.return_value = mock_keywords

        with pytest.raises(ValueError, match="Invalid retrieval_method"):
            await match_patient(
                mock_session,
                sample_patient_data,
                retrieval_method="nonexistent",
            )

    @pytest.mark.asyncio
    @patch("polus.aithena.clinical_aithena.pipeline.service.rank_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.match_patient_to_trial")
    @patch("polus.aithena.clinical_aithena.pipeline.service.HybridRetriever")
    @patch("polus.aithena.clinical_aithena.pipeline.service.generate_keywords")
    async def test_output_format_matches_pipeline_spec(
        self,
        mock_gen_keywords,
        mock_retriever_cls,
        mock_match,
        mock_rank,
        sample_patient_data,
        mock_session,
        mock_keywords,
        mock_retrieval_results,
        mock_matching_result,
        mock_ranking_result,
    ):
        """Test that output dicts have all fields expected by consumers."""
        mock_gen_keywords.return_value = mock_keywords

        mock_retriever = MagicMock()
        mock_retriever.search.return_value = mock_retrieval_results[:1]
        mock_retriever_cls.return_value = mock_retriever

        mock_match.return_value = mock_matching_result

        result_dict = mock_ranking_result("NCT00000000", r=85.0, e=70.0)
        mock_rank.return_value = result_dict

        output = await match_patient(
            mock_session, sample_patient_data, top_n=1
        )
        results = output["results"]

        assert len(results) == 1
        result = results[0]

        # Verify all expected keys
        expected_keys = {
            "nct_id",
            "title",
            "relevance_score",
            "eligibility_score",
            "relevance_explanation",
            "eligibility_explanation",
            "rank",
        }
        assert expected_keys.issubset(set(result.keys()))
        assert result["rank"] == 1
        assert isinstance(result["relevance_score"], float)
        assert isinstance(result["eligibility_score"], float)
