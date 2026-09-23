import pytest
from polus.aithena.clinical_aithena.clients.ctgov.models import (
    CTGovStudy, ProtocolSection, IdentificationModule, DesignModule, 
    ArmsInterventionsModule, ConditionsModule, DescriptionModule, 
    EligibilityModule, Phase, EnrollmentInfo, Intervention, InterventionType
)
from polus.aithena.clinical_aithena.services.transform import transform_study, extract_criteria

def test_extract_criteria_simple():
    text = "Inclusion Criteria:\n- Age > 18\n\nExclusion Criteria:\n- Pregnant"
    inc, exc = extract_criteria(text)
    assert inc == "- Age > 18"
    assert exc == "- Pregnant"

def test_extract_criteria_no_exclusion():
    text = "Inclusion Criteria:\n- Age > 18"
    inc, exc = extract_criteria(text)
    assert inc == "- Age > 18"
    assert exc is None

def test_extract_criteria_messy_headers():
    text = "  INCLUSION CRITERIA  \n- One\n\n  Exclusion Criteria: \n- Two"
    inc, exc = extract_criteria(text)
    assert inc == "- One"
    assert exc == "- Two"

def test_transform_study_basic():
    study = CTGovStudy(
        nct_id="NCT123",
        protocolSection=ProtocolSection(
            identificationModule=IdentificationModule(
                officialTitle="Official Title",
                briefTitle="Brief Title"
            ),
            designModule=DesignModule(
                phases=[Phase.PHASE1],
                enrollmentInfo=EnrollmentInfo(count=100)
            ),
            descriptionModule=DescriptionModule(
                briefSummary="A summary."
            ),
            eligibilityModule=EligibilityModule(
                eligibilityCriteria="Inclusion Criteria:\n- A\n\nExclusion Criteria:\n- B"
            ),
            conditionsModule=ConditionsModule(
                conditions=["Flu"]
            ),
            armsInterventionsModule=ArmsInterventionsModule(
                interventions=[
                    Intervention(type=InterventionType.DRUG, name="Aspirin"),
                    Intervention(type=InterventionType.DEVICE, name="Pacemaker")
                ]
            )
        )
    )
    
    result = transform_study(study)
    
    assert result is not None
    assert result.nct_id == "NCT123"
    assert result.title == "Official Title"
    assert result.metadata_json["brief_title"] == "Brief Title"
    assert result.metadata_json["phase"] == "Phase 1"
    assert result.metadata_json["enrollment"] == "100"
    assert result.metadata_json["brief_summary"] == "A summary."
    assert result.metadata_json["drugs"] == "Aspirin, Pacemaker"
    assert result.metadata_json["diseases"] == "Flu"
    assert result.metadata_json["inclusion_criteria"] == "- A"
    assert result.metadata_json["exclusion_criteria"] == "- B"
    
    expected_text = "Summary: A summary.\n\nInclusion criteria: - A\n\nExclusion criteria: - B"
    assert result.text == expected_text

def test_transform_study_missing_title():
    study = CTGovStudy(
        nct_id="NCT456",
        protocolSection=ProtocolSection(
             identificationModule=IdentificationModule(
                briefTitle="Brief Only"
            )
        )
    )
    result = transform_study(study)
    assert result is not None
    assert result.title == "Brief Only"

def test_transform_study_no_protocol():
    study = CTGovStudy(nct_id="NCT999")
    result = transform_study(study)
    assert result is None


