"""
Patient-trial eligibility matching module.

Performs criterion-level matching analysis between patients and clinical
trials using LLM-based eligibility prediction. Stateless implementation -
no database persistence.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from polus.aithena.clinical_aithena.clients.llm import (
    LLMConfig,
    get_client,
    parse_json_response,
)
from polus.aithena.clinical_aithena.models import TrialGPTStudy

logger = logging.getLogger(__name__)

# Standard compliance sentence appended to all patient notes
# (exact from TrialGPT/trialgpt_matching/run_matching.py:33)
COMPLIANCE_SENTENCE = (
    "The patient will provide informed consent, and will comply with "
    "the trial protocol without any practical issues."
)


def _ensure_nltk_data():
    """Ensure NLTK punkt tokenizer is downloaded."""
    import nltk
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab', quiet=True)


def add_sentence_numbers(text: str) -> str:
    """
    Tokenize text into sentences and add numbering.
    
    Appends a standard compliance sentence at the end and numbers
    all sentences starting from 0.
    
    Args:
        text: Raw patient clinical note text
        
    Returns:
        Sentence-numbered text, one sentence per line
        
    Example:
        >>> text = "Patient has diabetes. Age is 45."
        >>> add_sentence_numbers(text)
        "0. Patient has diabetes.\n1. Age is 45.\n2. The patient will..."
    """
    _ensure_nltk_data()
    from nltk.tokenize import sent_tokenize
    
    sentences = sent_tokenize(text)
    sentences.append(COMPLIANCE_SENTENCE)
    
    numbered = [f"{idx}. {sent}" for idx, sent in enumerate(sentences)]
    return "\n".join(numbered)


def parse_criteria(criteria: str) -> str:
    """
    Parse and number criteria from text.
    
    This is an exact replication of the original TrialGPT
    parse_criteria() function (lines 20-37).
    
    Args:
        criteria: Raw criteria text from trial
        
    Returns:
        Numbered criteria text, one criterion per line
        
    Example:
        >>> criteria = "Inclusion Criteria:\\n\\nAge >= 18\\n\\nHas disease"
        >>> parse_criteria(criteria)
        "0. Age >= 18\n1. Has disease\n"
    """
    output = ""
    criteria_list = criteria.split("\n\n")
    
    idx = 0
    for criterion in criteria_list:
        criterion = criterion.strip()
        
        # Skip headers
        if (
            "inclusion criteria" in criterion.lower()
            or "exclusion criteria" in criterion.lower()
        ):
            continue
        
        # Skip very short lines
        if len(criterion) < 5:
            continue
        
        output += f"{idx}. {criterion}\n"
        idx += 1
    
    return output


def format_trial(trial: TrialGPTStudy, inc_exc: str) -> str:
    """
    Format trial for LLM prompt.
    
    This is an exact replication of the original TrialGPT
    print_trial() function (lines 40-56).
    
    Args:
        trial: TrialGPTStudy database record
        inc_exc: Either "inclusion" or "exclusion"
        
    Returns:
        Formatted trial text for prompt
    """
    # Extract metadata from JSONB
    metadata = trial.metadata_json
    
    formatted = f"Title: {metadata.get('brief_title', trial.title)}\n"
    
    diseases = metadata.get('diseases_list', [])
    formatted += f"Target diseases: {', '.join(diseases)}\n"
    
    drugs = metadata.get('drugs_list', [])
    formatted += f"Interventions: {', '.join(drugs)}\n"
    
    summary = metadata.get('brief_summary', '')
    formatted += f"Summary: {summary}\n"
    
    if inc_exc == "inclusion":
        inclusion = metadata.get('inclusion_criteria', '')
        formatted += f"Inclusion criteria:\n {parse_criteria(inclusion)}\n"
    elif inc_exc == "exclusion":
        exclusion = metadata.get('exclusion_criteria', '')
        formatted += f"Exclusion criteria:\n {parse_criteria(exclusion)}\n"
    
    return formatted


def get_matching_prompts(
    trial: TrialGPTStudy,
    inc_exc: str,
    patient_text: str,
) -> Tuple[str, str]:
    """
    Generate system and user prompts for matching.
    
    This is an exact replication of the original TrialGPT
    get_matching_prompt() function (lines 59-89).
    
    Args:
        trial: TrialGPTStudy database record
        inc_exc: Either "inclusion" or "exclusion"
        patient_text: Sentence-numbered patient clinical note
        
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = (
        f"You are a helpful assistant for clinical trial recruitment. "
        f"Your task is to compare a given patient note and the {inc_exc} "
        f"criteria of a clinical trial to determine the patient's "
        f"eligibility at the criterion level.\n"
    )
    
    if inc_exc == "inclusion":
        system_prompt += (
            "The factors that allow someone to participate in a clinical "
            "study are called inclusion criteria. They are based on "
            "characteristics such as age, gender, the type and stage of a "
            "disease, previous treatment history, and other medical "
            "conditions.\n"
        )
    elif inc_exc == "exclusion":
        system_prompt += (
            "The factors that disqualify someone from participating are "
            "called exclusion criteria. They are based on characteristics "
            "such as age, gender, the type and stage of a disease, previous "
            "treatment history, and other medical conditions.\n"
        )
    
    system_prompt += (
        f"You should check the {inc_exc} criteria one-by-one, and output "
        f"the following three elements for each criterion:\n"
        f"\tElement 1. For each {inc_exc} criterion, briefly generate your "
        f"reasoning process: First, judge whether the criterion is not "
        f"applicable (not very common), where the patient does not meet the "
        f"premise of the criterion. Then, check if the patient note contains "
        f"direct evidence. If so, judge whether the patient meets or does "
        f"not meet the criterion. If there is no direct evidence, try to "
        f"infer from existing evidence, and answer one question: If the "
        f"criterion is true, is it possible that a good patient note will "
        f"miss such information? If impossible, then you can assume that the "
        f"criterion is not true. Otherwise, there is not enough information.\n"
        f"\tElement 2. If there is relevant information, you must generate a "
        f"list of relevant sentence IDs in the patient note. If there is no "
        f"relevant information, you must annotate an empty list.\n"
        f"\tElement 3. Classify the patient eligibility for this specific "
        f"{inc_exc} criterion: "
    )
    
    if inc_exc == "inclusion":
        system_prompt += (
            'the label must be chosen from {"not applicable", '
            '"not enough information", "included", "not included"}. '
            '"not applicable" should only be used for criteria that are not '
            'applicable to the patient. "not enough information" should be '
            'used where the patient note does not contain sufficient '
            'information for making the classification. Try to use as less '
            '"not enough information" as possible because if the note does '
            'not mention a medically important fact, you can assume that the '
            'fact is not true for the patient. "included" denotes that the '
            'patient meets the inclusion criterion, while "not included" '
            'means the reverse.\n'
        )
    elif inc_exc == "exclusion":
        system_prompt += (
            'the label must be chosen from {"not applicable", '
            '"not enough information", "excluded", "not excluded"}. '
            '"not applicable" should only be used for criteria that are not '
            'applicable to the patient. "not enough information" should be '
            'used where the patient note does not contain sufficient '
            'information for making the classification. Try to use as less '
            '"not enough information" as possible because if the note does '
            'not mention a medically important fact, you can assume that the '
            'fact is not true for the patient. "excluded" denotes that the '
            'patient meets the exclusion criterion and should be excluded in '
            'the trial, while "not excluded" means the reverse.\n'
        )
    
    system_prompt += (
        "You should output only a JSON dict exactly formatted as: "
        "dict{str(criterion_number): list[str(element_1_brief_reasoning), "
        "list[int(element_2_sentence_id)], str(element_3_eligibility_label)]}."
    )
    
    user_prompt = (
        f"Here is the patient note, each sentence is led by a sentence_id:\n"
        f"{patient_text}\n\n"
        f"Here is the clinical trial:\n{format_trial(trial, inc_exc)}\n\n"
        f"Plain JSON output:"
    )
    
    return system_prompt, user_prompt


def match_patient_to_trial(
    clinical_note: str,
    trial: TrialGPTStudy,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Perform criterion-level matching for a patient-trial pair (stateless).
    
    This function:
    1. Numbers patient sentences
    2. Calls LLM twice (inclusion, then exclusion)
    3. Returns results directly (no database persistence)
    
    Args:
        clinical_note: Patient clinical description text
        trial: TrialGPTStudy database record
        model: LLM model to use (defaults to config value)
        
    Returns:
        Dict with structure: {
            "inclusion": {criterion_id: [reasoning, [sentence_ids], label]},
            "exclusion": {criterion_id: [reasoning, [sentence_ids], label]}
        }
        
    Raises:
        ValueError: If clinical note is empty
        Exception: If LLM calls fail
    """
    if not clinical_note or not clinical_note.strip():
        raise ValueError("Clinical note cannot be empty")
    
    # Get LLM configuration
    config = LLMConfig()
    if model:
        config.model = model
    
    model_version = config.model
    
    # Generate matching results
    logger.info(
        "Matching patient to trial %s using %s",
        trial.nct_id,
        model_version,
    )
    
    # Add sentence numbering to patient text
    patient_text = add_sentence_numbers(clinical_note)
    
    # Get LLM client
    client = get_client(config)
    
    # Results dict
    results = {"inclusion": {}, "exclusion": {}}
    
    # Process inclusion and exclusion separately
    for inc_exc in ["inclusion", "exclusion"]:
        try:
            system_prompt, user_prompt = get_matching_prompts(
                trial, inc_exc, patient_text
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            
            response = client.chat.completions.create(
                model=model_version,
                messages=messages,
                temperature=0,
            )
            
            content = response.choices[0].message.content
            parsed = parse_json_response(content)
            
            results[inc_exc] = parsed
            
        except Exception as e:
            logger.error(
                "Failed to get %s results for trial %s: %s",
                inc_exc,
                trial.nct_id,
                e,
            )
            # Store empty dict for failed criterion type
            results[inc_exc] = {}
    
    logger.info(
        "Successfully matched to trial %s "
        "(%d inclusion criteria, %d exclusion criteria)",
        trial.nct_id,
        len(results["inclusion"]),
        len(results["exclusion"]),
    )
    
    return results


async def batch_match_patient_to_trials(
    clinical_note: str,
    trials: List[TrialGPTStudy],
    model: Optional[str] = None,
    max_concurrent: int = 5,
) -> List[Dict[str, Any]]:
    """
    Batch match a patient to multiple trials concurrently (stateless).
    
    Uses asyncio.gather() with a semaphore to limit concurrent LLM calls
    and avoid rate limiting.
    
    Args:
        clinical_note: Patient clinical description text
        trials: List of TrialGPTStudy records to match against
        model: LLM model to use (defaults to config value)
        max_concurrent: Maximum number of concurrent LLM calls
        
    Returns:
        List of matching result dicts (same structure as match_patient_to_trial)
        
    Example:
        >>> results = await batch_match_patient_to_trials(
        ...     clinical_note="Patient with melanoma...",
        ...     trials=[trial1, trial2, trial3],
        ...     max_concurrent=3
        ... )
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def match_with_semaphore(trial: TrialGPTStudy) -> Dict[str, Any]:
        async with semaphore:
            # Run the synchronous match function in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                match_patient_to_trial,
                clinical_note,
                trial,
                model,
            )
    
    logger.info(
        "Batch matching to %d trials (max %d concurrent)",
        len(trials),
        max_concurrent,
    )
    
    results = await asyncio.gather(
        *[match_with_semaphore(trial) for trial in trials],
        return_exceptions=True,
    )
    
    # Filter out exceptions and log them
    valid_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(
                "Failed to match to trial %s: %s",
                trials[i].nct_id,
                result,
            )
        else:
            valid_results.append(result)
    
    logger.info(
        "Batch matching complete: %d/%d trials successfully matched",
        len(valid_results),
        len(trials),
    )
    
    return valid_results

