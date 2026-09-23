"""Tests for stateless keyword generation service."""

from unittest.mock import Mock, patch

import pytest

from polus.aithena.clinical_aithena.pipeline.keyword_generation import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    generate_keywords,
)


@pytest.fixture
def sample_clinical_note():
    """Sample clinical note for testing."""
    return (
        "Patient is a 45-year-old male with stage III lung cancer. "
        "Has undergone chemotherapy and radiation. Currently experiencing "
        "shortness of breath and fatigue. No known drug allergies."
    )


class TestPromptPreservation:
    """Test that we use the exact TrialGPT prompts."""

    def test_system_prompt_matches_original(self):
        """Verify system prompt matches original TrialGPT implementation."""
        # Original from TrialGPT/trialgpt_retrieval/keyword_generation.py:21
        expected = (
            'You are a helpful assistant and your task is to help search relevant '
            'clinical trials for a given patient description. Please first summarize '
            'the main medical problems of the patient. Then generate up to 32 key '
            'conditions for searching relevant clinical trials for this patient. '
            'The key condition list should be ranked by priority. Please output only '
            'a JSON dict formatted as Dict{{"summary": Str(summary), '
            '"conditions": List[Str(condition)]}}.'
        )
        assert SYSTEM_PROMPT == expected

    def test_user_prompt_template_matches_original(self):
        """Verify user prompt template matches original."""
        # Original from TrialGPT/trialgpt_retrieval/keyword_generation.py:23
        expected = "Here is the patient description: \n{note}\n\nJSON output:"
        assert USER_PROMPT_TEMPLATE == expected


class TestGenerateKeywords:
    """Tests for stateless generate_keywords function."""

    def test_generate_keywords_success(self, sample_clinical_note):
        """Test successful keyword generation."""
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content='{"summary": "45yo male with stage III lung cancer", '
                    '"conditions": ["lung cancer", "stage III", "chemotherapy", '
                    '"radiation therapy", "shortness of breath"]}'
                )
            )
        ]
        
        with patch(
            'polus.aithena.clinical_aithena.pipeline.keyword_generation.get_client'
        ) as mock_get_client:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = generate_keywords(sample_clinical_note)
            
            # Verify result
            assert result["summary"] == "45yo male with stage III lung cancer"
            assert len(result["conditions"]) == 5
            assert "lung cancer" in result["conditions"]
            
            # Verify LLM was called
            mock_client.chat.completions.create.assert_called_once()

    def test_generate_keywords_empty_clinical_note(self):
        """Test error when clinical note is empty."""
        with pytest.raises(ValueError, match="Clinical note cannot be empty"):
            generate_keywords("")

    def test_generate_keywords_invalid_llm_response(self, sample_clinical_note):
        """Test handling of invalid LLM response."""
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content='{"invalid": "response"}'))
        ]
        
        with patch(
            'polus.aithena.clinical_aithena.pipeline.keyword_generation.get_client'
        ) as mock_get_client:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            with pytest.raises(ValueError, match="missing 'summary' or 'conditions'"):
                generate_keywords(sample_clinical_note)

    def test_generate_keywords_custom_model(self, sample_clinical_note):
        """Test keyword generation with custom model."""
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content='{"summary": "Test", "conditions": ["test"]}'
                )
            )
        ]
        
        with patch(
            'polus.aithena.clinical_aithena.pipeline.keyword_generation.get_client'
        ) as mock_get_client:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = generate_keywords(sample_clinical_note, model="gpt-4-turbo")
            
            # Verify result
            assert result["summary"] == "Test"
            assert result["conditions"] == ["test"]
            
            # Verify LLM was called with correct model
            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs["model"] == "gpt-4-turbo"

