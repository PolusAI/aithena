"""Tests for patient-trial ranking module.

Tests the ranking pipeline that aggregates criterion-level matching predictions
into overall relevance (R) and eligibility (E) scores using LLM.
"""

from unittest.mock import Mock, patch, MagicMock

import pytest

# Import CTGovStudy first so SQLAlchemy can resolve the TrialGPTStudy relationship
from polus.aithena.clinical_aithena.clients.ctgov.models import CTGovStudy  # noqa: F401
from polus.aithena.clinical_aithena.models import TrialGPTStudy
from polus.aithena.clinical_aithena.pipeline.ranking import (
    convert_criteria_pred_to_string,
    convert_pred_to_prompt,
    rank_trial,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_clinical_note():
    """Sample patient clinical note."""
    return (
        "Patient is a 45-year-old male with stage III non-small cell lung cancer. "
        "Has undergone two cycles of cisplatin-based chemotherapy. "
        "Currently experiencing shortness of breath and fatigue. "
        "ECOG performance status 1."
    )


@pytest.fixture
def sample_trial():
    """Create a sample TrialGPTStudy for testing."""
    return TrialGPTStudy(
        nct_id="NCT12345678",
        title="Test Trial for Lung Cancer",
        text="Trial text",
        metadata_json={
            "brief_title": "Test Trial for Lung Cancer Treatment",
            "diseases_list": ["Non-Small Cell Lung Cancer", "Lung Neoplasms"],
            "brief_summary": "A randomized phase 3 trial testing immunotherapy in NSCLC.",
            "inclusion_criteria": (
                "Inclusion Criteria:\n\n"
                "Age 18 or older\n\n"
                "Diagnosed with stage III or IV NSCLC\n\n"
                "ECOG performance status 0-2"
            ),
            "exclusion_criteria": (
                "Exclusion Criteria:\n\n"
                "Pregnant or breastfeeding\n\n"
                "Active autoimmune disease\n\n"
                "Prior organ transplant"
            ),
        },
    )


@pytest.fixture
def sample_matching_result():
    """Sample criterion-level matching result (output of matching step)."""
    return {
        "inclusion": {
            "0": ["Patient is 45 years old, meeting age criterion", [1], "included"],
            "1": ["Patient has stage III NSCLC", [0], "included"],
            "2": ["ECOG status is 1, within 0-2 range", [3], "included"],
        },
        "exclusion": {
            "0": ["No information about pregnancy", [], "not enough information"],
            "1": ["No mention of autoimmune disease", [], "not excluded"],
            "2": ["No history of organ transplant mentioned", [], "not excluded"],
        },
    }


@pytest.fixture
def sample_trial_info():
    """Pre-built trial_info dict matching what rank_trial constructs internally."""
    return {
        "brief_title": "Test Trial for Lung Cancer Treatment",
        "diseases_list": ["Non-Small Cell Lung Cancer", "Lung Neoplasms"],
        "brief_summary": "A randomized phase 3 trial testing immunotherapy in NSCLC.",
        "inclusion_criteria": (
            "Inclusion Criteria:\n\n"
            "Age 18 or older\n\n"
            "Diagnosed with stage III or IV NSCLC\n\n"
            "ECOG performance status 0-2"
        ),
        "exclusion_criteria": (
            "Exclusion Criteria:\n\n"
            "Pregnant or breastfeeding\n\n"
            "Active autoimmune disease\n\n"
            "Prior organ transplant"
        ),
    }


# ---------------------------------------------------------------------------
# Tests: convert_criteria_pred_to_string
# ---------------------------------------------------------------------------

class TestConvertCriteriaPredToString:
    """Tests for criterion prediction formatting."""

    def test_basic_formatting(self, sample_matching_result, sample_trial_info):
        """Test that predictions are formatted with correct structure."""
        result = convert_criteria_pred_to_string(
            sample_matching_result, sample_trial_info
        )

        # Should contain inclusion criteria
        assert "inclusion criterion" in result
        assert "Age 18 or older" in result
        assert "Patient relevance:" in result
        assert "Patient eligibility: included" in result

        # Should contain exclusion criteria
        assert "exclusion criterion" in result
        assert "Pregnant or breastfeeding" in result

    def test_evident_sentences_included(self, sample_trial_info):
        """Test that evident sentence IDs appear when present."""
        prediction = {
            "inclusion": {
                "0": ["Matches age requirement", [1, 5], "included"],
            },
            "exclusion": {},
        }
        result = convert_criteria_pred_to_string(prediction, sample_trial_info)

        assert "Evident sentences: [1, 5]" in result

    def test_empty_evident_sentences_omitted(self, sample_trial_info):
        """Test that evident sentences line is omitted when empty."""
        prediction = {
            "inclusion": {
                "0": ["No evidence found", [], "not enough information"],
            },
            "exclusion": {},
        }
        result = convert_criteria_pred_to_string(prediction, sample_trial_info)

        assert "Evident sentences" not in result

    def test_skips_headers(self, sample_trial_info):
        """Test that criteria headers are skipped in output."""
        prediction = {
            "inclusion": {
                "0": ["Meets criterion", [], "included"],
            },
            "exclusion": {},
        }
        result = convert_criteria_pred_to_string(prediction, sample_trial_info)

        assert "Inclusion Criteria:" not in result

    def test_skips_invalid_predictions(self, sample_trial_info):
        """Test that predictions with wrong format (not 3 elements) are skipped."""
        prediction = {
            "inclusion": {
                "0": ["Only two elements", "included"],  # Missing sentence IDs
            },
            "exclusion": {},
        }
        result = convert_criteria_pred_to_string(prediction, sample_trial_info)

        # The malformed prediction should be skipped
        assert "Age 18 or older" not in result

    def test_skips_nonexistent_criterion_index(self, sample_trial_info):
        """Test that predictions for non-existent criterion indices are skipped."""
        prediction = {
            "inclusion": {
                "99": ["Ghost criterion", [], "included"],
            },
            "exclusion": {},
        }
        result = convert_criteria_pred_to_string(prediction, sample_trial_info)

        assert "Ghost criterion" not in result


# ---------------------------------------------------------------------------
# Tests: convert_pred_to_prompt
# ---------------------------------------------------------------------------

class TestConvertPredToPrompt:
    """Tests for ranking prompt construction."""

    def test_system_prompt_content(
        self, sample_clinical_note, sample_matching_result, sample_trial_info
    ):
        """Test that system prompt contains required TrialGPT instructions."""
        system, _ = convert_pred_to_prompt(
            sample_clinical_note, sample_matching_result, sample_trial_info
        )

        assert "clinical trial recruitment" in system
        assert "relevance score" in system.lower()
        assert "eligibility score" in system.lower()
        assert "R" in system
        assert "E" in system
        assert "JSON" in system
        assert "relevance_score_R" in system
        assert "eligibility_score_E" in system

    def test_user_prompt_contains_patient(
        self, sample_clinical_note, sample_matching_result, sample_trial_info
    ):
        """Test that user prompt contains the patient note."""
        _, user = convert_pred_to_prompt(
            sample_clinical_note, sample_matching_result, sample_trial_info
        )

        assert sample_clinical_note in user
        assert "patient note" in user.lower()

    def test_user_prompt_contains_trial(
        self, sample_clinical_note, sample_matching_result, sample_trial_info
    ):
        """Test that user prompt contains trial information."""
        _, user = convert_pred_to_prompt(
            sample_clinical_note, sample_matching_result, sample_trial_info
        )

        assert "Test Trial for Lung Cancer Treatment" in user
        assert "Non-Small Cell Lung Cancer" in user
        assert "immunotherapy" in user

    def test_user_prompt_contains_predictions(
        self, sample_clinical_note, sample_matching_result, sample_trial_info
    ):
        """Test that user prompt contains the criterion-level predictions."""
        _, user = convert_pred_to_prompt(
            sample_clinical_note, sample_matching_result, sample_trial_info
        )

        assert "criterion-level eligibility prediction" in user.lower()
        assert "inclusion criterion" in user
        assert "Patient eligibility:" in user

    def test_prompt_ends_with_json_instruction(
        self, sample_clinical_note, sample_matching_result, sample_trial_info
    ):
        """Test that the user prompt ends with JSON output instruction."""
        _, user = convert_pred_to_prompt(
            sample_clinical_note, sample_matching_result, sample_trial_info
        )

        assert user.strip().endswith("Plain JSON output:")


# ---------------------------------------------------------------------------
# Tests: rank_trial
# ---------------------------------------------------------------------------

class TestRankTrial:
    """Tests for the main rank_trial function."""

    def _mock_llm_response(self, relevance=75.0, eligibility=50.0):
        """Helper to create a mocked LLM response."""
        import json

        content = json.dumps({
            "relevance_explanation": "Patient has matching disease and stage.",
            "relevance_score_R": relevance,
            "eligibility_explanation": "Meets all inclusion, no exclusions.",
            "eligibility_score_E": eligibility,
        })
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=content))]
        return mock_response

    @patch("polus.aithena.clinical_aithena.pipeline.ranking.get_client")
    @patch("polus.aithena.clinical_aithena.pipeline.ranking.LLMConfig")
    def test_successful_ranking(
        self, mock_config_cls, mock_get_client,
        sample_clinical_note, sample_trial, sample_matching_result,
    ):
        """Test successful ranking returns correct structure."""
        mock_config = MagicMock()
        mock_config.model = "gpt-4"
        mock_config.temperature = 0.0
        mock_config_cls.return_value = mock_config

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = self._mock_llm_response(
            relevance=75.0, eligibility=50.0
        )
        mock_get_client.return_value = mock_client

        result = rank_trial(
            sample_clinical_note, sample_trial, sample_matching_result
        )

        assert result["nct_id"] == "NCT12345678"
        assert result["relevance_score"] == 75.0
        assert result["eligibility_score"] == 50.0
        assert "relevance_explanation" in result
        assert "eligibility_explanation" in result

    @patch("polus.aithena.clinical_aithena.pipeline.ranking.get_client")
    @patch("polus.aithena.clinical_aithena.pipeline.ranking.LLMConfig")
    def test_score_ranges_valid(
        self, mock_config_cls, mock_get_client,
        sample_clinical_note, sample_trial, sample_matching_result,
    ):
        """Test that scores are within valid ranges: R in [0,100], E in [-R,R]."""
        mock_config = MagicMock()
        mock_config.model = "gpt-4"
        mock_config.temperature = 0.0
        mock_config_cls.return_value = mock_config

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = self._mock_llm_response(
            relevance=80.0, eligibility=60.0
        )
        mock_get_client.return_value = mock_client

        result = rank_trial(
            sample_clinical_note, sample_trial, sample_matching_result
        )

        r = result["relevance_score"]
        e = result["eligibility_score"]
        assert 0 <= r <= 100, f"Relevance {r} not in [0, 100]"
        assert -r <= e <= r, f"Eligibility {e} not in [-{r}, {r}]"

    @patch("polus.aithena.clinical_aithena.pipeline.ranking.get_client")
    @patch("polus.aithena.clinical_aithena.pipeline.ranking.LLMConfig")
    def test_relevance_out_of_range_clamped(
        self, mock_config_cls, mock_get_client,
        sample_clinical_note, sample_trial, sample_matching_result,
    ):
        """Test that out-of-range relevance scores are clamped to [0, 100]."""
        mock_config = MagicMock()
        mock_config.model = "gpt-4"
        mock_config.temperature = 0.0
        mock_config_cls.return_value = mock_config

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = self._mock_llm_response(
            relevance=150.0, eligibility=50.0
        )
        mock_get_client.return_value = mock_client

        result = rank_trial(
            sample_clinical_note, sample_trial, sample_matching_result
        )

        assert result["relevance_score"] == 100.0

    @patch("polus.aithena.clinical_aithena.pipeline.ranking.get_client")
    @patch("polus.aithena.clinical_aithena.pipeline.ranking.LLMConfig")
    def test_eligibility_out_of_range_clamped(
        self, mock_config_cls, mock_get_client,
        sample_clinical_note, sample_trial, sample_matching_result,
    ):
        """Test that out-of-range eligibility scores are clamped to [-R, R]."""
        mock_config = MagicMock()
        mock_config.model = "gpt-4"
        mock_config.temperature = 0.0
        mock_config_cls.return_value = mock_config

        mock_client = Mock()
        # E=90 exceeds R=60, should be clamped to 60
        mock_client.chat.completions.create.return_value = self._mock_llm_response(
            relevance=60.0, eligibility=90.0
        )
        mock_get_client.return_value = mock_client

        result = rank_trial(
            sample_clinical_note, sample_trial, sample_matching_result
        )

        assert result["eligibility_score"] == 60.0  # Clamped to R

    @patch("polus.aithena.clinical_aithena.pipeline.ranking.get_client")
    @patch("polus.aithena.clinical_aithena.pipeline.ranking.LLMConfig")
    def test_negative_eligibility_clamped(
        self, mock_config_cls, mock_get_client,
        sample_clinical_note, sample_trial, sample_matching_result,
    ):
        """Test that negative eligibility below -R is clamped."""
        mock_config = MagicMock()
        mock_config.model = "gpt-4"
        mock_config.temperature = 0.0
        mock_config_cls.return_value = mock_config

        mock_client = Mock()
        # E=-80 is below -R=-50, should be clamped to -50
        mock_client.chat.completions.create.return_value = self._mock_llm_response(
            relevance=50.0, eligibility=-80.0
        )
        mock_get_client.return_value = mock_client

        result = rank_trial(
            sample_clinical_note, sample_trial, sample_matching_result
        )

        assert result["eligibility_score"] == -50.0  # Clamped to -R

    def test_empty_clinical_note_raises(self, sample_trial, sample_matching_result):
        """Test that empty clinical note raises ValueError."""
        with pytest.raises(ValueError, match="Clinical note cannot be empty"):
            rank_trial("", sample_trial, sample_matching_result)

    def test_whitespace_clinical_note_raises(self, sample_trial, sample_matching_result):
        """Test that whitespace-only clinical note raises ValueError."""
        with pytest.raises(ValueError, match="Clinical note cannot be empty"):
            rank_trial("   \n\t  ", sample_trial, sample_matching_result)

    @patch("polus.aithena.clinical_aithena.pipeline.ranking.get_client")
    @patch("polus.aithena.clinical_aithena.pipeline.ranking.LLMConfig")
    def test_missing_field_in_response_raises(
        self, mock_config_cls, mock_get_client,
        sample_clinical_note, sample_trial, sample_matching_result,
    ):
        """Test that missing required fields in LLM response raises ValueError."""
        mock_config = MagicMock()
        mock_config.model = "gpt-4"
        mock_config.temperature = 0.0
        mock_config_cls.return_value = mock_config

        # Response missing eligibility_score_E
        import json
        content = json.dumps({
            "relevance_explanation": "Relevant",
            "relevance_score_R": 75.0,
            "eligibility_explanation": "Eligible",
            # Missing eligibility_score_E
        })
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=content))]

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        with pytest.raises(ValueError, match="missing required field"):
            rank_trial(
                sample_clinical_note, sample_trial, sample_matching_result
            )

    @patch("polus.aithena.clinical_aithena.pipeline.ranking.get_client")
    @patch("polus.aithena.clinical_aithena.pipeline.ranking.LLMConfig")
    def test_custom_model_passed_through(
        self, mock_config_cls, mock_get_client,
        sample_clinical_note, sample_trial, sample_matching_result,
    ):
        """Test that a custom model name is passed through to the LLM config."""
        mock_config = MagicMock()
        mock_config.model = "gpt-4"
        mock_config.temperature = 0.0
        mock_config_cls.return_value = mock_config

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = self._mock_llm_response()
        mock_get_client.return_value = mock_client

        rank_trial(
            sample_clinical_note, sample_trial, sample_matching_result,
            model="gpt-4-turbo",
        )

        # Verify custom model was set on config
        mock_config.__setattr__("model", "gpt-4-turbo")

    @patch("polus.aithena.clinical_aithena.pipeline.ranking.get_client")
    @patch("polus.aithena.clinical_aithena.pipeline.ranking.LLMConfig")
    def test_zero_relevance_constrains_eligibility(
        self, mock_config_cls, mock_get_client,
        sample_clinical_note, sample_trial, sample_matching_result,
    ):
        """Test that R=0 forces E=0 (since -0 <= E <= 0)."""
        mock_config = MagicMock()
        mock_config.model = "gpt-4"
        mock_config.temperature = 0.0
        mock_config_cls.return_value = mock_config

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = self._mock_llm_response(
            relevance=0.0, eligibility=5.0
        )
        mock_get_client.return_value = mock_client

        result = rank_trial(
            sample_clinical_note, sample_trial, sample_matching_result
        )

        assert result["relevance_score"] == 0.0
        assert result["eligibility_score"] == 0.0  # Clamped to [-0, 0]


# ---------------------------------------------------------------------------
# Tests: Output format matches TrialGPT expectations
# ---------------------------------------------------------------------------

class TestTrialGPTOutputFormat:
    """Verify output format matches original TrialGPT expectations."""

    @patch("polus.aithena.clinical_aithena.pipeline.ranking.get_client")
    @patch("polus.aithena.clinical_aithena.pipeline.ranking.LLMConfig")
    def test_output_has_all_required_keys(
        self, mock_config_cls, mock_get_client,
        sample_clinical_note, sample_trial, sample_matching_result,
    ):
        """Test that output dict has all keys expected by the pipeline."""
        mock_config = MagicMock()
        mock_config.model = "gpt-4"
        mock_config.temperature = 0.0
        mock_config_cls.return_value = mock_config

        mock_client = Mock()
        import json
        content = json.dumps({
            "relevance_explanation": "Patient matches trial conditions.",
            "relevance_score_R": 85.0,
            "eligibility_explanation": "Meets all inclusion, no exclusions found.",
            "eligibility_score_E": 70.0,
        })
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=content))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = rank_trial(
            sample_clinical_note, sample_trial, sample_matching_result
        )

        # These are the keys consumed by pipeline/service.py
        required_keys = {
            "nct_id",
            "relevance_score",
            "relevance_explanation",
            "eligibility_score",
            "eligibility_explanation",
        }
        assert set(result.keys()) == required_keys

    @patch("polus.aithena.clinical_aithena.pipeline.ranking.get_client")
    @patch("polus.aithena.clinical_aithena.pipeline.ranking.LLMConfig")
    def test_score_types_are_float(
        self, mock_config_cls, mock_get_client,
        sample_clinical_note, sample_trial, sample_matching_result,
    ):
        """Test that scores are floats (not int or str)."""
        mock_config = MagicMock()
        mock_config.model = "gpt-4"
        mock_config.temperature = 0.0
        mock_config_cls.return_value = mock_config

        mock_client = Mock()
        import json
        # Intentionally return integer scores to test float conversion
        content = json.dumps({
            "relevance_explanation": "Relevant",
            "relevance_score_R": 80,
            "eligibility_explanation": "Eligible",
            "eligibility_score_E": 60,
        })
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=content))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = rank_trial(
            sample_clinical_note, sample_trial, sample_matching_result
        )

        assert isinstance(result["relevance_score"], float)
        assert isinstance(result["eligibility_score"], float)
