"""Tests for stateless patient-trial matching service."""

from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session, create_engine

from polus.aithena.clinical_aithena.models import TrialGPTStudy
from polus.aithena.clinical_aithena.pipeline.matching import (
    add_sentence_numbers,
    batch_match_patient_to_trials,
    format_trial,
    get_matching_prompts,
    match_patient_to_trial,
    parse_criteria,
)


@pytest.fixture
def sample_clinical_note():
    """Sample clinical note for testing."""
    return (
        "Patient is a 45-year-old male with stage III lung cancer. "
        "Has undergone chemotherapy and radiation. "
        "Currently experiencing shortness of breath and fatigue."
    )


@pytest.fixture
def sample_trial():
    """Create a sample trial for testing."""
    return TrialGPTStudy(
        nct_id="NCT12345678",
        title="Test Trial for Lung Cancer",
        text="Trial text",
        metadata_json={
            "brief_title": "Test Trial for Lung Cancer",
            "phase": "Phase 3",
            "drugs_list": ["Drug A", "Drug B"],
            "diseases_list": ["Lung Cancer"],
            "brief_summary": "A trial testing new treatments",
            "inclusion_criteria": (
                "Inclusion Criteria:\n\n"
                "Age 18 or older\n\n"
                "Diagnosed with stage III or IV lung cancer\n\n"
                "ECOG performance status 0-2"
            ),
            "exclusion_criteria": (
                "Exclusion Criteria:\n\n"
                "Pregnant or breastfeeding\n\n"
                "Active infection\n\n"
                "Prior organ transplant"
            ),
        },
    )


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_add_sentence_numbers(self):
        """Test sentence numbering."""
        text = "Patient has diabetes. Age is 45 years. No known allergies."
        result = add_sentence_numbers(text)
        
        lines = result.split("\n")
        assert len(lines) == 4  # 3 sentences + compliance
        assert lines[0].startswith("0. ")
        assert lines[1].startswith("1. ")
        assert lines[2].startswith("2. ")
        assert "informed consent" in lines[3].lower()

    def test_parse_criteria_simple(self):
        """Test parsing simple criteria."""
        criteria = "Age >= 18\n\nDiagnosed with cancer\n\nECOG 0-2"
        result = parse_criteria(criteria)
        
        lines = result.strip().split("\n")
        assert len(lines) == 3
        assert lines[0] == "0. Age >= 18"
        assert lines[1] == "1. Diagnosed with cancer"
        assert lines[2] == "2. ECOG 0-2"

    def test_parse_criteria_with_headers(self):
        """Test parsing criteria with headers."""
        criteria = (
            "Inclusion Criteria:\n\n"
            "Age >= 18\n\n"
            "Has disease\n\n"
            "Willing to participate"
        )
        result = parse_criteria(criteria)
        
        lines = result.strip().split("\n")
        assert len(lines) == 3  # Header should be skipped
        assert "Inclusion Criteria" not in result
        assert lines[0] == "0. Age >= 18"

    def test_parse_criteria_skip_short_lines(self):
        """Test that very short lines are skipped."""
        criteria = "Age >= 18\n\nA\n\nHas disease"
        result = parse_criteria(criteria)
        
        lines = result.strip().split("\n")
        assert len(lines) == 2  # "A" should be skipped
        assert lines[0] == "0. Age >= 18"
        assert lines[1] == "1. Has disease"

    def test_format_trial_inclusion(self, sample_trial):
        """Test trial formatting for inclusion criteria."""
        result = format_trial(sample_trial, "inclusion")
        
        assert "Title: Test Trial for Lung Cancer" in result
        assert "Target diseases: Lung Cancer" in result
        assert "Interventions: Drug A, Drug B" in result
        assert "Summary: A trial testing new treatments" in result
        assert "Inclusion criteria:" in result
        assert "0. Age 18 or older" in result
        assert "Exclusion criteria:" not in result

    def test_format_trial_exclusion(self, sample_trial):
        """Test trial formatting for exclusion criteria."""
        result = format_trial(sample_trial, "exclusion")
        
        assert "Title: Test Trial for Lung Cancer" in result
        assert "Exclusion criteria:" in result
        assert "0. Pregnant or breastfeeding" in result
        assert "Inclusion criteria:" not in result

    def test_get_matching_prompts_inclusion(self, sample_trial):
        """Test prompt generation for inclusion."""
        patient_text = "0. Patient has cancer.\n1. Age 45."
        system, user = get_matching_prompts(
            sample_trial, "inclusion", patient_text
        )
        
        assert "clinical trial recruitment" in system
        assert "inclusion criteria" in system
        assert "not applicable" in system
        assert "included" in system
        assert "not included" in system
        assert patient_text in user
        assert "Test Trial for Lung Cancer" in user

    def test_get_matching_prompts_exclusion(self, sample_trial):
        """Test prompt generation for exclusion."""
        patient_text = "0. Patient has cancer.\n1. Age 45."
        system, user = get_matching_prompts(
            sample_trial, "exclusion", patient_text
        )
        
        assert "clinical trial recruitment" in system
        assert "exclusion criteria" in system
        assert "excluded" in system
        assert "not excluded" in system
        assert patient_text in user


class TestMatchPatientToTrial:
    """Tests for stateless match_patient_to_trial function."""

    def test_match_success(self, sample_clinical_note, sample_trial):
        """Test successful matching."""
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=(
                        '{"0": ["Patient age meets criterion", [1], "included"], '
                        '"1": ["Has stage III lung cancer", [0], "included"], '
                        '"2": ["No ECOG data", [], "not enough information"]}'
                    )
                )
            )
        ]
        
        with patch(
            'polus.aithena.clinical_aithena.pipeline.matching.get_client'
        ) as mock_get_client:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = match_patient_to_trial(
                sample_clinical_note, sample_trial
            )
            
            # Verify result
            assert "inclusion" in result
            assert "exclusion" in result
            assert len(result["inclusion"]) == 3
            assert len(result["exclusion"]) == 3

    def test_match_empty_clinical_note(self, sample_trial):
        """Test error when clinical note is empty."""
        with pytest.raises(ValueError, match="Clinical note cannot be empty"):
            match_patient_to_trial("", sample_trial)

    def test_match_partial_failure(self, sample_clinical_note, sample_trial):
        """Test handling when one LLM call fails."""
        # First call succeeds, second fails
        responses = [
            Mock(
                choices=[
                    Mock(
                        message=Mock(content='{"0": ["success", [], "included"]}')
                    )
                ]
            ),
            Exception("LLM API error"),
        ]
        
        with patch(
            'polus.aithena.clinical_aithena.pipeline.matching.get_client'
        ) as mock_get_client:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = responses
            mock_get_client.return_value = mock_client
            
            result = match_patient_to_trial(sample_clinical_note, sample_trial)
            
            # Should have inclusion results but empty exclusion
            assert len(result["inclusion"]) == 1
            assert len(result["exclusion"]) == 0


class TestBatchMatching:
    """Tests for batch_match_patient_to_trials function."""

    @pytest.mark.asyncio
    async def test_batch_match(self, sample_clinical_note):
        """Test batch matching multiple trials."""
        # Create multiple trials
        trials = []
        for i in range(3):
            trial = TrialGPTStudy(
                nct_id=f"NCT0000000{i}",
                title=f"Trial {i}",
                text="text",
                metadata_json={
                    "brief_title": f"Trial {i}",
                    "diseases_list": ["Disease"],
                    "drugs_list": ["Drug"],
                    "brief_summary": "Summary",
                    "inclusion_criteria": "Age >= 18",
                    "exclusion_criteria": "Pregnant",
                },
            )
            trials.append(trial)
        
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content='{"0": ["test", [], "included"]}'))
        ]
        
        with patch(
            'polus.aithena.clinical_aithena.pipeline.matching.get_client'
        ) as mock_get_client:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            results = await batch_match_patient_to_trials(
                sample_clinical_note,
                trials,
                max_concurrent=2,
            )
            
            # Should have results for all 3 trials
            assert len(results) == 3
            assert all("inclusion" in r and "exclusion" in r for r in results)

