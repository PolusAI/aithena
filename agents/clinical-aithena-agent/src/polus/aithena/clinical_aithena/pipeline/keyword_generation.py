"""
Keyword generation for patient clinical trial search.

Generates LLM-based summaries and search keywords from patient clinical notes
for use in hybrid retrieval. Operates statelessly - no database persistence.

This is adapted from the original TrialGPT implementation for the stateless
GARDIAN pipeline.

Original TrialGPT implementation:
https://github.com/microsoft/TrialGPT/blob/main/trialgpt_retrieval/keyword_generation.py
"""

import logging
from typing import Any, Dict, Optional

from polus.aithena.clinical_aithena.clients.llm import (
    LLMConfig,
    get_client,
    parse_json_response,
)

logger = logging.getLogger(__name__)

# Exact prompts from original TrialGPT implementation
# (TrialGPT/trialgpt_retrieval/keyword_generation.py lines 20-23)
SYSTEM_PROMPT = (
    'You are a helpful assistant and your task is to help search '
    'relevant clinical trials for a given patient description. Please '
    'first summarize the main medical problems of the patient. Then '
    'generate up to 32 key conditions for searching relevant clinical '
    'trials for this patient. The key condition list should be ranked '
    'by priority. Please output only a JSON dict formatted as '
    'Dict{{"summary": Str(summary), "conditions": List[Str(condition)]}}.'
)

USER_PROMPT_TEMPLATE = (
    "Here is the patient description: \n{note}\n\nJSON output:"
)


def generate_keywords(
    clinical_note: str,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate search keywords for a patient using LLM (stateless).

    This function:
    1. Calls LLM with the exact TrialGPT prompt
    2. Parses and validates the JSON response
    3. Returns keywords dict directly (no database persistence)

    Args:
        clinical_note: Patient clinical description text
        model: LLM model to use (defaults to config value)

    Returns:
        Dict with structure: {"summary": str, "conditions": List[str]}

    Raises:
        ValueError: If clinical note is empty or response is invalid
        Exception: If LLM call fails

    Example:
        >>> from polus.aithena.clinical_aithena.pipeline import (
        ...     generate_keywords
        ... )
        >>> keywords = generate_keywords(
        ...     clinical_note="Patient with stage IV melanoma...",
        ...     model="gpt-4"
        ... )
        >>> print(keywords["summary"])
        >>> print(keywords["conditions"])
    """
    if not clinical_note or not clinical_note.strip():
        raise ValueError("Clinical note cannot be empty")

    # Get LLM configuration
    config = LLMConfig()
    if model:
        config.model = model

    model_version = config.model

    # Generate keywords using LLM
    logger.info("Generating keywords using %s", model_version)

    try:
        # Get configured LLM client
        client = get_client(config)

        # Prepare messages using exact TrialGPT prompts
        user_content = USER_PROMPT_TEMPLATE.format(note=clinical_note)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        # Call LLM
        response = client.chat.completions.create(
            model=model_version,
            messages=messages,
            temperature=0,
        )

        # Parse JSON response
        content = response.choices[0].message.content
        result = parse_json_response(content)

        # Validate response structure
        if "summary" not in result or "conditions" not in result:
            raise ValueError(
                f"Invalid LLM response: missing 'summary' or "
                f"'conditions'. Got: {result}"
            )

        if not isinstance(result["conditions"], list):
            raise ValueError(
                "Invalid LLM response: 'conditions' must be a list. "
                f"Got: {type(result['conditions'])}"
            )

        logger.info(
            "Successfully generated %d keywords",
            len(result["conditions"]),
        )

        return result

    except Exception as e:
        logger.error("Failed to generate keywords: %s", e)
        raise
