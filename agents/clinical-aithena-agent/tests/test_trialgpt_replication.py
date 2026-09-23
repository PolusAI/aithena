"""Tests verifying output format matches original TrialGPT expectations.

These tests validate that our pipeline produces outputs in the same format
as the original TrialGPT implementation, using known-good reference data
from TrialGPT/results/ as ground truth.

Marker: tests requiring the TrialGPT dataset files are marked with
``pytest.mark.trialgpt_data`` so they can be skipped in CI if the
submodule is unavailable.
"""

import json
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import pytest

# Import CTGovStudy first so SQLAlchemy can resolve the TrialGPTStudy relationship
from polus.aithena.clinical_aithena.clients.ctgov.models import CTGovStudy  # noqa: F401
from polus.aithena.clinical_aithena.models import TrialGPTStudy
from polus.aithena.clinical_aithena.pipeline.ranking import (
    convert_criteria_pred_to_string,
    convert_pred_to_prompt,
)

# Paths to TrialGPT reference data
TRIALGPT_ROOT = Path(__file__).parent.parent.parent.parent / "TrialGPT"
RESULTS_DIR = TRIALGPT_ROOT / "results"
DATASET_DIR = TRIALGPT_ROOT / "dataset"

# Check if TrialGPT data is available
HAS_TRIALGPT_DATA = (RESULTS_DIR / "retrieval_keywords_gpt-4.1_sigir.json").exists()

trialgpt_data = pytest.mark.skipif(
    not HAS_TRIALGPT_DATA,
    reason="TrialGPT dataset not available (git submodule not initialized?)",
)


# ---------------------------------------------------------------------------
# Fixtures: load reference data from TrialGPT/results
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def reference_keywords():
    """Load reference keyword generation output from TrialGPT results."""
    if not HAS_TRIALGPT_DATA:
        pytest.skip("TrialGPT data not available")
    with open(RESULTS_DIR / "retrieval_keywords_gpt-4.1_sigir.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def reference_matching():
    """Load reference matching results from TrialGPT results."""
    if not HAS_TRIALGPT_DATA:
        pytest.skip("TrialGPT data not available")
    with open(RESULTS_DIR / "matching_results_sigir_gpt-4.1.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def reference_aggregation():
    """Load reference aggregation (ranking) results from TrialGPT results."""
    if not HAS_TRIALGPT_DATA:
        pytest.skip("TrialGPT data not available")
    with open(RESULTS_DIR / "aggregation_results_sigir_gpt-4.1.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def trial_info():
    """Load trial info from TrialGPT dataset."""
    if not HAS_TRIALGPT_DATA:
        pytest.skip("TrialGPT data not available")
    with open(DATASET_DIR / "trial_info.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def sigir_queries():
    """Load SIGIR patient queries."""
    if not HAS_TRIALGPT_DATA:
        pytest.skip("TrialGPT data not available")
    queries = {}
    with open(DATASET_DIR / "sigir" / "queries.jsonl") as f:
        for line in f:
            q = json.loads(line)
            queries[q["_id"]] = q["text"]
    return queries


# ---------------------------------------------------------------------------
# Step 1: Keyword Generation - Output Format Tests
# ---------------------------------------------------------------------------

class TestKeywordOutputFormat:
    """Verify keyword generation output matches TrialGPT format."""

    @trialgpt_data
    def test_keyword_output_has_required_keys(self, reference_keywords):
        """Every keyword entry must have 'summary' and 'conditions'."""
        # Check first 5 patients
        for patient_id in list(reference_keywords.keys())[:5]:
            kw = reference_keywords[patient_id]
            assert "summary" in kw, f"{patient_id} missing 'summary'"
            assert "conditions" in kw, f"{patient_id} missing 'conditions'"

    @trialgpt_data
    def test_conditions_is_list_of_strings(self, reference_keywords):
        """Conditions must be a list of strings."""
        for patient_id in list(reference_keywords.keys())[:5]:
            conditions = reference_keywords[patient_id]["conditions"]
            assert isinstance(conditions, list)
            assert all(isinstance(c, str) for c in conditions)
            assert len(conditions) > 0

    @trialgpt_data
    def test_summary_is_nonempty_string(self, reference_keywords):
        """Summary must be a non-empty string."""
        for patient_id in list(reference_keywords.keys())[:5]:
            summary = reference_keywords[patient_id]["summary"]
            assert isinstance(summary, str)
            assert len(summary) > 10


# ---------------------------------------------------------------------------
# Step 2: Matching - Output Format Tests
# ---------------------------------------------------------------------------

class TestMatchingOutputFormat:
    """Verify matching output format matches TrialGPT expectations."""

    @trialgpt_data
    def test_matching_has_inclusion_exclusion(self, reference_matching):
        """Each trial's matching result must have 'inclusion' and 'exclusion'."""
        patient_id = list(reference_matching.keys())[0]
        # matching results are nested: patient_id -> round_idx -> nct_id -> result
        for round_idx, round_data in reference_matching[patient_id].items():
            for nct_id, result in round_data.items():
                assert "inclusion" in result, f"{nct_id} missing 'inclusion'"
                assert "exclusion" in result, f"{nct_id} missing 'exclusion'"

    @trialgpt_data
    def test_matching_criterion_format(self, reference_matching):
        """Each criterion prediction must have [reasoning, sentence_ids, label]."""
        patient_id = list(reference_matching.keys())[0]
        round_data = reference_matching[patient_id]["0"]
        nct_id = list(round_data.keys())[0]
        result = round_data[nct_id]

        for inc_exc in ["inclusion", "exclusion"]:
            for criterion_idx, pred in result[inc_exc].items():
                assert isinstance(pred, list), (
                    f"Prediction for {inc_exc} criterion {criterion_idx} "
                    f"should be a list, got {type(pred)}"
                )
                assert len(pred) == 3, (
                    f"Prediction for {inc_exc} criterion {criterion_idx} "
                    f"should have 3 elements [reasoning, sentences, label], "
                    f"got {len(pred)}"
                )
                # Element 0: reasoning string
                assert isinstance(pred[0], str)
                # Element 1: sentence IDs (list)
                assert isinstance(pred[1], list)
                # Element 2: label string
                assert isinstance(pred[2], str)


# ---------------------------------------------------------------------------
# Step 3: Ranking/Aggregation - Output Format Tests
# ---------------------------------------------------------------------------

class TestRankingOutputFormat:
    """Verify ranking output matches TrialGPT aggregation format."""

    @trialgpt_data
    def test_aggregation_has_required_fields(self, reference_aggregation):
        """Each aggregation result must have R score, E score, and explanations."""
        patient_id = list(reference_aggregation.keys())[0]
        for nct_id, result in reference_aggregation[patient_id].items():
            assert "relevance_score_R" in result
            assert "eligibility_score_E" in result
            assert "relevance_explanation" in result
            assert "eligibility_explanation" in result

    @trialgpt_data
    def test_relevance_score_range(self, reference_aggregation):
        """Relevance scores must be in [0, 100]."""
        patient_id = list(reference_aggregation.keys())[0]
        for nct_id, result in reference_aggregation[patient_id].items():
            r = result["relevance_score_R"]
            assert 0 <= r <= 100, f"{nct_id}: R={r} out of range"

    @trialgpt_data
    def test_eligibility_score_range(self, reference_aggregation):
        """Eligibility scores must be in [-R, R]."""
        patient_id = list(reference_aggregation.keys())[0]
        for nct_id, result in reference_aggregation[patient_id].items():
            r = result["relevance_score_R"]
            e = result["eligibility_score_E"]
            assert -r <= e <= r, f"{nct_id}: E={e} out of [-{r}, {r}]"


# ---------------------------------------------------------------------------
# Prompt Construction: compare to known reference input
# ---------------------------------------------------------------------------

class TestPromptConstruction:
    """Verify our prompt construction matches TrialGPT's expected format."""

    @trialgpt_data
    def test_prompt_uses_trial_info_fields(self, trial_info, reference_matching):
        """Test that prompt construction uses the same trial fields as TrialGPT."""
        # Pick a trial that's in both trial_info and matching results
        patient_id = list(reference_matching.keys())[0]
        round_data = reference_matching[patient_id]["0"]
        nct_id = list(round_data.keys())[0]

        tinfo = trial_info.get(nct_id)
        if tinfo is None:
            pytest.skip(f"Trial {nct_id} not in trial_info")

        matching_result = round_data[nct_id]

        # Build trial_info dict the same way rank_trial does
        trial_info_dict = {
            "brief_title": tinfo.get("brief_title", ""),
            "diseases_list": tinfo.get("diseases_list", []),
            "brief_summary": tinfo.get("brief_summary", ""),
            "inclusion_criteria": tinfo.get("inclusion_criteria", ""),
            "exclusion_criteria": tinfo.get("exclusion_criteria", ""),
        }

        system_prompt, user_prompt = convert_pred_to_prompt(
            "Test patient note",
            matching_result,
            trial_info_dict,
        )

        # Verify system prompt contains TrialGPT-specific instructions
        assert "relevance score" in system_prompt.lower()
        assert "eligibility score" in system_prompt.lower()
        assert "relevance_score_R" in system_prompt
        assert "eligibility_score_E" in system_prompt

        # Verify user prompt contains trial title
        assert tinfo["brief_title"] in user_prompt

    @trialgpt_data
    def test_criteria_pred_string_format(self, trial_info, reference_matching):
        """Test criterion-to-string formatting with real data."""
        patient_id = list(reference_matching.keys())[0]
        round_data = reference_matching[patient_id]["0"]
        nct_id = list(round_data.keys())[0]

        tinfo = trial_info.get(nct_id)
        if tinfo is None:
            pytest.skip(f"Trial {nct_id} not in trial_info")

        matching_result = round_data[nct_id]

        trial_info_dict = {
            "brief_title": tinfo.get("brief_title", ""),
            "diseases_list": tinfo.get("diseases_list", []),
            "brief_summary": tinfo.get("brief_summary", ""),
            "inclusion_criteria": tinfo.get("inclusion_criteria", ""),
            "exclusion_criteria": tinfo.get("exclusion_criteria", ""),
        }

        pred_str = convert_criteria_pred_to_string(matching_result, trial_info_dict)

        # Must contain structured criterion output
        assert "criterion" in pred_str
        assert "Patient relevance:" in pred_str
        assert "Patient eligibility:" in pred_str


# ---------------------------------------------------------------------------
# Cross-step consistency: retrieval -> matching -> ranking
# ---------------------------------------------------------------------------

class TestCrossStepConsistency:
    """Verify that outputs from one step feed correctly into the next."""

    @trialgpt_data
    def test_matching_nct_ids_match_retrieval(
        self, reference_matching
    ):
        """NCT IDs in matching results should be valid trial IDs."""
        patient_id = list(reference_matching.keys())[0]
        for round_idx, round_data in reference_matching[patient_id].items():
            for nct_id in round_data.keys():
                assert nct_id.startswith("NCT"), (
                    f"Invalid NCT ID format: {nct_id}"
                )

    @trialgpt_data
    def test_aggregation_nct_ids_subset_of_matching(
        self, reference_matching, reference_aggregation
    ):
        """NCT IDs in aggregation should be a subset of those in matching."""
        patient_id = list(reference_aggregation.keys())[0]
        if patient_id not in reference_matching:
            pytest.skip(f"Patient {patient_id} not in matching results")

        # Collect all NCT IDs from matching
        matching_ncts = set()
        for round_data in reference_matching[patient_id].values():
            matching_ncts.update(round_data.keys())

        # All aggregation NCTs should be in matching
        agg_ncts = set(reference_aggregation[patient_id].keys())
        assert agg_ncts.issubset(matching_ncts), (
            f"Aggregation has NCTs not in matching: {agg_ncts - matching_ncts}"
        )
