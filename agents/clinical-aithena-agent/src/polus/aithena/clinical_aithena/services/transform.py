import logging
import re
from typing import Optional, Tuple

from polus.aithena.clinical_aithena.clients.ctgov.models import CTGovStudy
from polus.aithena.clinical_aithena.models import TrialGPTStudy, TrialMetadata

logger = logging.getLogger(__name__)


def extract_criteria(criteria_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract Inclusion and Exclusion criteria from the text block.

    Args:
        criteria_text: The full eligibility criteria text.

    Returns:
        A tuple of (inclusion_criteria, exclusion_criteria).
    """
    if not criteria_text:
        return None, None

    # Common patterns for headers
    # Inclusion Criteria: ... Exclusion Criteria: ...
    # Inclusion criteria: ... Exclusion criteria: ...
    # INCLUSION CRITERIA: ... EXCLUSION CRITERIA: ...
    
    # We'll use case-insensitive split
    # Note: Sometimes headers are formatted with newlines or bullets
    
    # Normalized search for split
    # Look for "Exclusion Criteria" as the delimiter
    split_pattern = re.compile(r"\n\s*(?:Exclusion Criteria|EXCLUSION CRITERIA)\s*:?\s*\n", re.IGNORECASE)
    
    parts = split_pattern.split(criteria_text)
    
    inclusion = parts[0].strip()
    exclusion = parts[1].strip() if len(parts) > 1 else None
    
    # Remove "Inclusion Criteria" header from the first part if present
    inclusion_header = re.compile(r"^\s*(?:Inclusion Criteria|INCLUSION CRITERIA)\s*:?\s*\n", re.IGNORECASE)
    inclusion = inclusion_header.sub("", inclusion).strip()

    return inclusion, exclusion


def transform_study(ctgov_study: CTGovStudy) -> Optional[TrialGPTStudy]:
    """
    Transform a CTGovStudy object into a TrialGPTStudy object.

    Args:
        ctgov_study: The source clinical trial object.

    Returns:
        A transformed TrialGPTStudy object, or None if critical data is missing.
    """
    if not ctgov_study.nct_id:
        logger.warning("Study missing NCT ID, skipping transformation.")
        return None

    # Access protocol section safely
    protocol = ctgov_study.protocolSection
    # If protocolSection is a dict (due to JSONB storage), parse it if possible, otherwise access as dict
    if isinstance(protocol, dict):
        # We can try to rely on dict access for now as the simplest fix
        # Or re-parse into object. Let's use dict access pattern for flexibility if we don't want to re-parse everything.
        # But our logic below uses dot notation.
        # Ideally, the ORM should have parsed it if we used the model correctly, but sometimes JSONB comes back as dict.
        pass
    
    if not protocol:
        logger.warning(f"Study {ctgov_study.nct_id} missing protocol section.")
        return None

    # Helper to get attr or dict item
    def get(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    # 1. Identification Module
    ident = get(protocol, "identificationModule")
    if not ident:
        logger.warning(f"Study {ctgov_study.nct_id} missing identification module.")
        return None

    # Title fallback: Official Title -> Brief Title
    official_title = get(ident, "officialTitle")
    brief_title = get(ident, "briefTitle")
    title = official_title or brief_title
    if not title:
        logger.warning(f"Study {ctgov_study.nct_id} missing title.")
        return None

    # 2. Design Module (Phase, Enrollment)
    design = get(protocol, "designModule")
    phases = None
    enrollment = None
    if design:
        design_phases = get(design, "phases")
        if design_phases:
            # phases might be strings or Enums if parsed
            phases_list = []
            for p in design_phases:
                val = p.value if hasattr(p, "value") else str(p)
                # Map enums to human readable if needed, or keep as is.
                # TrialGPT uses "Phase 3", we have "PHASE3".
                # Simple normalization map
                phase_map = {
                    "NA": "",
                    "EARLY_PHASE1": "Early Phase 1",
                    "PHASE1": "Phase 1",
                    "PHASE2": "Phase 2",
                    "PHASE3": "Phase 3",
                    "PHASE4": "Phase 4",
                }
                phases_list.append(phase_map.get(val, val))
                
            phases = ", ".join(phases_list)
        
        enrollment_info = get(design, "enrollmentInfo")
        if enrollment_info:
            count = get(enrollment_info, "count")
            if count is not None:
                enrollment = str(count)

    # 3. Arms/Interventions (Drugs)
    # TrialGPT often includes other intervention types in the 'drugs' list, not just DRUG type.
    # For example: 'Physical activity' (BEHAVIORAL), 'Magnetic resonance spectroscopy' (PROCEDURE/DEVICE).
    # We should probably include all interventions or broaden the filter.
    arms = get(protocol, "armsInterventionsModule")
    drugs_list = []
    if arms:
        interventions = get(arms, "interventions")
        if interventions:
            for intervention in interventions:
                # We'll include everything for now to match TrialGPT behavior better,
                # or maybe just specific types if strictly requested "drugs".
                # But TrialGPT dataset seems to use 'drugs' as a catch-all for interventions.
                name = get(intervention, "name")
                if name:
                    drugs_list.append(name)
    
    drugs_str = ", ".join(drugs_list) if drugs_list else None

    # 4. Conditions (Diseases)
    conditions_mod = get(protocol, "conditionsModule")
    diseases_list = []
    if conditions_mod:
        conds = get(conditions_mod, "conditions")
        if conds:
            diseases_list = conds
    
    diseases_str = ", ".join(diseases_list) if diseases_list else None

    # 5. Description (Brief Summary)
    desc = get(protocol, "descriptionModule")
    brief_summary = get(desc, "briefSummary") if desc else None

    # 6. Eligibility (Criteria)
    eligibility = get(protocol, "eligibilityModule")
    inclusion_criteria = None
    exclusion_criteria = None
    
    if eligibility:
        criteria = get(eligibility, "eligibilityCriteria")
        if criteria:
            inclusion_criteria, exclusion_criteria = extract_criteria(criteria)

    # 7. Construct Full Text
    # Combine pieces into a single text blob for embedding/search
    text_parts = []
    if brief_summary:
        text_parts.append(f"Summary: {brief_summary}")
    if inclusion_criteria:
        text_parts.append(f"\nInclusion criteria: {inclusion_criteria}")
    if exclusion_criteria:
        text_parts.append(f"\nExclusion criteria: {exclusion_criteria}")
    
    full_text = "\n".join(text_parts) if text_parts else "No description available."

    # Construct Metadata
    metadata = TrialMetadata(
        brief_title=brief_title,
        phase=phases,
        drugs=drugs_str,
        drugs_list=drugs_list,
        diseases=diseases_str,
        diseases_list=diseases_list,
        enrollment=enrollment,
        brief_summary=brief_summary,
        inclusion_criteria=inclusion_criteria,
        exclusion_criteria=exclusion_criteria
    )

    # Create TrialGPTStudy
    # Note: Embeddings are not generated here; they will be populated later.
    return TrialGPTStudy(
        nct_id=ctgov_study.nct_id,
        title=title,
        text=full_text,
        metadata_json=metadata.model_dump(),
        ctgov_study_id=ctgov_study.id
    )

