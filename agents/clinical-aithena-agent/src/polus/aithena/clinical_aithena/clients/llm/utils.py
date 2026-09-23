"""Utility functions for working with LLM responses."""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def parse_json_response(response_text: str) -> Dict[str, Any]:
    """
    Parse JSON from LLM response, handling common formatting issues.
    
    LLMs often wrap JSON in markdown code blocks or add extra formatting.
    This function cleans up the response before parsing.
    
    Args:
        response_text: Raw text response from LLM
        
    Returns:
        Parsed JSON dict
        
    Raises:
        json.JSONDecodeError: If response cannot be parsed as JSON
        
    Example:
        >>> # Works with markdown
        >>> parse_json_response('```json\\n{"key": "value"}\\n```')
        {'key': 'value'}
        
        >>> # Works with plain JSON
        >>> parse_json_response('{"key": "value"}')
        {'key': 'value'}
    """
    cleaned = response_text.strip()
    
    # Remove markdown code fences (multiline)
    if cleaned.startswith("```") and "\n" in cleaned:
        lines = cleaned.split("\n")
        lines = lines[1:]  # Skip first line (```json or ```)
        
        # Remove closing fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        
        cleaned = "\n".join(lines).strip()
    
    # Strip backticks from beginning and end (inline code)
    cleaned = cleaned.strip("`").strip()
    
    # Remove "json" label if present at the start
    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()
    
    # Parse JSON
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {cleaned[:200]}...")
        raise

