"""
Patient-trial ranking module.

Aggregates criterion-level matching predictions into overall relevance and
eligibility scores for ranking trials. Stateless implementation - no database
persistence.

This is adapted from the original TrialGPT ranking implementation:
https://github.com/microsoft/TrialGPT/blob/main/trialgpt_ranking/TrialGPT.py
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from polus.aithena.clinical_aithena.clients.llm import (
    LLMConfig,
    get_client,
    parse_json_response,
)
from polus.aithena.clinical_aithena.models import TrialGPTStudy

logger = logging.getLogger(__name__)


def convert_criteria_pred_to_string(
    prediction: Dict[str, Any],
    trial_info: Dict[str, Any],
) -> str:
    """
    Convert criterion-level predictions to a linear string format.
    
    This is an exact replication of TrialGPT's format (lines 20-63).
    
    Args:
        prediction: Dict with "inclusion" and "exclusion" keys,
                   each containing {criterion_id: [reasoning, [sentence_ids], label]}
        trial_info: Dict with trial metadata including criteria text
        
    Returns:
        Formatted string with criterion-level predictions
        
    Example format:
        inclusion criterion 0: Age >= 18
            Patient relevance: ...
            Evident sentences: [1, 5]
            Patient eligibility: included
    """
    output = ""
    
    for inc_exc in ["inclusion", "exclusion"]:
        # First get the idx2criterion dict
        idx2criterion = {}
        criteria = trial_info[inc_exc + "_criteria"].split("\n\n")
        
        idx = 0
        for criterion in criteria:
            criterion = criterion.strip()
            
            # Skip headers
            if "inclusion criteria" in criterion.lower() or "exclusion criteria" in criterion.lower():
                continue
            
            if len(criterion) < 5:
                continue
            
            idx2criterion[str(idx)] = criterion
            idx += 1
        
        # Process each prediction
        for idx, info in enumerate(prediction[inc_exc].items()):
            criterion_idx, preds = info
            
            if criterion_idx not in idx2criterion:
                continue
            
            criterion = idx2criterion[criterion_idx]
            
            if len(preds) != 3:
                continue
            
            output += f"{inc_exc} criterion {idx}: {criterion}\n"
            output += f"\tPatient relevance: {preds[0]}\n"
            if len(preds[1]) > 0:
                output += f"\tEvident sentences: {preds[1]}\n"
            output += f"\tPatient eligibility: {preds[2]}\n"
    
    return output


def convert_pred_to_prompt(
    patient: str,
    pred: Dict[str, Any],
    trial_info: Dict[str, Any],
) -> Tuple[str, str]:
    """
    Convert prediction to system and user prompts for ranking.
    
    Exact replication of TrialGPT's prompt construction (lines 66-96).
    
    Args:
        patient: Patient clinical note text
        pred: Criterion-level matching predictions
        trial_info: Trial metadata
        
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Get the trial string
    trial = f"Title: {trial_info['brief_title']}\n"
    trial += f"Target conditions: {', '.join(trial_info['diseases_list'])}\n"
    trial += f"Summary: {trial_info['brief_summary']}"
    
    # Get the prediction strings
    pred_str = convert_criteria_pred_to_string(pred, trial_info)
    
    # Construct the system prompt (exact from TrialGPT lines 81-85)
    system_prompt = "You are a helpful assistant for clinical trial recruitment. You will be given a patient note, a clinical trial, and the patient eligibility predictions for each criterion.\n"
    system_prompt += "Your task is to output two scores, a relevance score (R) and an eligibility score (E), between the patient and the clinical trial.\n"
    system_prompt += "First explain the consideration for determining patient-trial relevance. Predict the relevance score R (0~100), which represents the overall relevance between the patient and the clinical trial. R=0 denotes the patient is totally irrelevant to the clinical trial, and R=100 denotes the patient is exactly relevant to the clinical trial.\n"
    system_prompt += "Then explain the consideration for determining patient-trial eligibility. Predict the eligibility score E (-R~R), which represents the patient's eligibility to the clinical trial. Note that -R <= E <= R (the absolute value of eligibility cannot be higher than the relevance), where E=-R denotes that the patient is ineligible (not included by any inclusion criteria, or excluded by all exclusion criteria), E=R denotes that the patient is eligible (included by all inclusion criteria, and not excluded by any exclusion criteria), E=0 denotes the patient is neutral (i.e., no relevant information for all inclusion and exclusion criteria).\n"
    system_prompt += 'Please output a JSON dict formatted as Dict{"relevance_explanation": Str, "relevance_score_R": Float, "eligibility_explanation": Str, "eligibility_score_E": Float}.'
    
    # Construct the user prompt (exact from TrialGPT lines 88-94)
    user_prompt = "Here is the patient note:\n"
    user_prompt += patient + "\n\n"
    user_prompt += "Here is the clinical trial description:\n"
    user_prompt += trial + "\n\n"
    user_prompt += "Here are the criterion-level eligibility prediction:\n"
    user_prompt += pred_str + "\n\n"
    user_prompt += "Plain JSON output:"
    
    return system_prompt, user_prompt


def rank_trial(
    clinical_note: str,
    trial: TrialGPTStudy,
    matching_result: Dict[str, Any],
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate ranking scores for a single patient-trial pair (stateless).
    
    Takes criterion-level matching predictions and aggregates them into
    overall relevance (R) and eligibility (E) scores using LLM.
    
    Args:
        clinical_note: Patient clinical description text
        trial: TrialGPTStudy database record
        matching_result: Dict with "inclusion" and "exclusion" predictions
        model: LLM model to use (defaults to config value)
        
    Returns:
        Dict with structure: {
            "nct_id": str,
            "relevance_score": float (0-100),
            "relevance_explanation": str,
            "eligibility_score": float (-R to R),
            "eligibility_explanation": str
        }
        
    Raises:
        ValueError: If clinical note is empty or response is invalid
        Exception: If LLM call fails
        
    Example:
        >>> ranking = rank_trial(
        ...     clinical_note="Patient with melanoma...",
        ...     trial=trial_obj,
        ...     matching_result={"inclusion": {...}, "exclusion": {...}}
        ... )
        >>> print(f"R={ranking['relevance_score']}, E={ranking['eligibility_score']}")
    """
    if not clinical_note or not clinical_note.strip():
        raise ValueError("Clinical note cannot be empty")
    
    # Get LLM configuration
    config = LLMConfig()
    if model:
        config.model = model
    model_version = config.model
    
    # Prepare trial info dict
    trial_info = {
        "brief_title": trial.metadata_json.get("brief_title", ""),
        "diseases_list": trial.metadata_json.get("diseases_list", []),
        "brief_summary": trial.metadata_json.get("brief_summary", ""),
        "inclusion_criteria": trial.metadata_json.get("inclusion_criteria", ""),
        "exclusion_criteria": trial.metadata_json.get("exclusion_criteria", ""),
    }
    
    # Generate prompts
    system_prompt, user_prompt = convert_pred_to_prompt(
        clinical_note,
        matching_result,
        trial_info
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    # Call LLM
    logger.info(f"Generating ranking for trial {trial.nct_id}")
    
    client = get_client(config)
    response_text = client.chat.completions.create(
        model=config.model,
        messages=messages,
        temperature=config.temperature,
    ).choices[0].message.content.strip()
    
    # Parse JSON response
    result = parse_json_response(response_text)
    
    # Validate required fields
    required_fields = [
        "relevance_explanation",
        "relevance_score_R",
        "eligibility_explanation",
        "eligibility_score_E",
    ]
    for field in required_fields:
        if field not in result:
            raise ValueError(f"LLM response missing required field: {field}")
    
    # Extract scores
    relevance_score = float(result["relevance_score_R"])
    eligibility_score = float(result["eligibility_score_E"])
    
    # Validate score ranges
    if not (0 <= relevance_score <= 100):
        logger.warning(
            f"Relevance score {relevance_score} out of range [0, 100], clamping"
        )
        relevance_score = max(0, min(100, relevance_score))
    
    if not (-relevance_score <= eligibility_score <= relevance_score):
        logger.warning(
            f"Eligibility score {eligibility_score} out of range "
            f"[-{relevance_score}, {relevance_score}], clamping"
        )
        eligibility_score = max(-relevance_score, min(relevance_score, eligibility_score))
    
    logger.info(
        f"Generated ranking for {trial.nct_id}: R={relevance_score:.1f}, E={eligibility_score:.1f}"
    )
    
    return {
        "nct_id": trial.nct_id,
        "relevance_score": relevance_score,
        "relevance_explanation": result["relevance_explanation"],
        "eligibility_score": eligibility_score,
        "eligibility_explanation": result["eligibility_explanation"],
    }



