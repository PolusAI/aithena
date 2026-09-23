from typing import List, Optional, Literal, Dict, Any, Tuple, ClassVar
from datetime import datetime
from enum import Enum
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Index, text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.schema import Computed
from pydantic import model_validator, ConfigDict

# --- Enums from OpenAPI Spec ---


class Status(str, Enum):
    ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING"
    COMPLETED = "COMPLETED"
    ENROLLING_BY_INVITATION = "ENROLLING_BY_INVITATION"
    NOT_YET_RECRUITING = "NOT_YET_RECRUITING"
    RECRUITING = "RECRUITING"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"
    WITHDRAWN = "WITHDRAWN"
    AVAILABLE = "AVAILABLE"
    NO_LONGER_AVAILABLE = "NO_LONGER_AVAILABLE"
    TEMPORARILY_NOT_AVAILABLE = "TEMPORARILY_NOT_AVAILABLE"
    APPROVED_FOR_MARKETING = "APPROVED_FOR_MARKETING"
    WITHHELD = "WITHHELD"
    UNKNOWN = "UNKNOWN"


class StudyType(str, Enum):
    EXPANDED_ACCESS = "EXPANDED_ACCESS"
    INTERVENTIONAL = "INTERVENTIONAL"
    OBSERVATIONAL = "OBSERVATIONAL"


class Phase(str, Enum):
    NA = "NA"
    EARLY_PHASE1 = "EARLY_PHASE1"  # Spec has PHASE1, not PHASE_1
    PHASE1 = "PHASE1"
    PHASE2 = "PHASE2"
    PHASE3 = "PHASE3"
    PHASE4 = "PHASE4"


class Sex(str, Enum):
    FEMALE = "FEMALE"
    MALE = "MALE"
    ALL = "ALL"


class StandardAge(str, Enum):
    CHILD = "CHILD"
    ADULT = "ADULT"
    OLDER_ADULT = "OLDER_ADULT"


class SamplingMethod(str, Enum):
    PROBABILITY_SAMPLE = "PROBABILITY_SAMPLE"
    NON_PROBABILITY_SAMPLE = "NON_PROBABILITY_SAMPLE"


class IpdSharing(str, Enum):
    YES = "YES"
    NO = "NO"
    UNDECIDED = "UNDECIDED"


class IpdSharingInfoType(str, Enum):
    STUDY_PROTOCOL = "STUDY_PROTOCOL"
    SAP = "SAP"
    ICF = "ICF"
    CSR = "CSR"
    ANALYTIC_CODE = "ANALYTIC_CODE"


class OrgStudyIdType(str, Enum):
    NIH = "NIH"
    FDA = "FDA"
    VA = "VA"
    CDC = "CDC"
    AHRQ = "AHRQ"
    SAMHSA = "SAMHSA"


class SecondaryIdType(str, Enum):
    NIH = "NIH"
    FDA = "FDA"
    VA = "VA"
    CDC = "CDC"
    AHRQ = "AHRQ"
    SAMHSA = "SAMHSA"
    OTHER_GRANT = "OTHER_GRANT"
    EUDRACT_NUMBER = "EUDRACT_NUMBER"
    CTIS = "CTIS"
    REGISTRY = "REGISTRY"
    OTHER = "OTHER"


class AgencyClass(str, Enum):
    NIH = "NIH"
    FED = "FED"
    OTHER_GOV = "OTHER_GOV"
    INDIV = "INDIV"
    INDUSTRY = "INDUSTRY"
    NETWORK = "NETWORK"
    AMBIG = "AMBIG"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class ExpandedAccessStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    NO_LONGER_AVAILABLE = "NO_LONGER_AVAILABLE"
    TEMPORARILY_NOT_AVAILABLE = "TEMPORARILY_NOT_AVAILABLE"
    APPROVED_FOR_MARKETING = "APPROVED_FOR_MARKETING"


class DateType(str, Enum):
    ACTUAL = "ACTUAL"
    ESTIMATED = "ESTIMATED"


class ResponsiblePartyType(str, Enum):
    SPONSOR = "SPONSOR"
    PRINCIPAL_INVESTIGATOR = "PRINCIPAL_INVESTIGATOR"
    SPONSOR_INVESTIGATOR = "SPONSOR_INVESTIGATOR"


class DesignAllocation(str, Enum):
    RANDOMIZED = "RANDOMIZED"
    NON_RANDOMIZED = "NON_RANDOMIZED"
    NA = "NA"


class InterventionalAssignment(str, Enum):
    SINGLE_GROUP = "SINGLE_GROUP"
    PARALLEL = "PARALLEL"
    CROSSOVER = "CROSSOVER"
    FACTORIAL = "FACTORIAL"
    SEQUENTIAL = "SEQUENTIAL"


class PrimaryPurpose(str, Enum):
    TREATMENT = "TREATMENT"
    PREVENTION = "PREVENTION"
    DIAGNOSTIC = "DIAGNOSTIC"
    ECT = "ECT"
    SUPPORTIVE_CARE = "SUPPORTIVE_CARE"
    SCREENING = "SCREENING"
    HEALTH_SERVICES_RESEARCH = "HEALTH_SERVICES_RESEARCH"
    BASIC_SCIENCE = "BASIC_SCIENCE"
    DEVICE_FEASIBILITY = "DEVICE_FEASIBILITY"
    OTHER = "OTHER"


class ObservationalModel(str, Enum):
    COHORT = "COHORT"
    CASE_CONTROL = "CASE_CONTROL"
    CASE_ONLY = "CASE_ONLY"
    CASE_CROSSOVER = "CASE_CROSSOVER"
    ECOLOGIC_OR_COMMUNITY = "ECOLOGIC_OR_COMMUNITY"
    FAMILY_BASED = "FAMILY_BASED"
    DEFINED_POPULATION = "DEFINED_POPULATION"
    NATURAL_HISTORY = "NATURAL_HISTORY"
    OTHER = "OTHER"


class DesignTimePerspective(str, Enum):
    RETROSPECTIVE = "RETROSPECTIVE"
    PROSPECTIVE = "PROSPECTIVE"
    CROSS_SECTIONAL = "CROSS_SECTIONAL"
    OTHER = "OTHER"


class BioSpecRetention(str, Enum):
    NONE_RETAINED = "NONE_RETAINED"
    SAMPLES_WITH_DNA = "SAMPLES_WITH_DNA"
    SAMPLES_WITHOUT_DNA = "SAMPLES_WITHOUT_DNA"


class EnrollmentType(str, Enum):
    ACTUAL = "ACTUAL"
    ESTIMATED = "ESTIMATED"


class ArmGroupType(str, Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    ACTIVE_COMPARATOR = "ACTIVE_COMPARATOR"
    PLACEBO_COMPARATOR = "PLACEBO_COMPARATOR"
    SHAM_COMPARATOR = "SHAM_COMPARATOR"
    NO_INTERVENTION = "NO_INTERVENTION"
    OTHER = "OTHER"


class InterventionType(str, Enum):
    BEHAVIORAL = "BEHAVIORAL"
    BIOLOGICAL = "BIOLOGICAL"
    COMBINATION_PRODUCT = "COMBINATION_PRODUCT"
    DEVICE = "DEVICE"
    DIAGNOSTIC_TEST = "DIAGNOSTIC_TEST"
    DIETARY_SUPPLEMENT = "DIETARY_SUPPLEMENT"
    DRUG = "DRUG"
    GENETIC = "GENETIC"
    PROCEDURE = "PROCEDURE"
    RADIATION = "RADIATION"
    OTHER = "OTHER"


class ContactRole(str, Enum):
    STUDY_CHAIR = "STUDY_CHAIR"
    STUDY_DIRECTOR = "STUDY_DIRECTOR"
    PRINCIPAL_INVESTIGATOR = "PRINCIPAL_INVESTIGATOR"
    SUB_INVESTIGATOR = "SUB_INVESTIGATOR"
    CONTACT = "CONTACT"


class OfficialRole(str, Enum):
    STUDY_CHAIR = "STUDY_CHAIR"
    STUDY_DIRECTOR = "STUDY_DIRECTOR"
    PRINCIPAL_INVESTIGATOR = "PRINCIPAL_INVESTIGATOR"
    SUB_INVESTIGATOR = "SUB_INVESTIGATOR"


class RecruitmentStatus(str, Enum):
    ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING"
    COMPLETED = "COMPLETED"
    ENROLLING_BY_INVITATION = "ENROLLING_BY_INVITATION"
    NOT_YET_RECRUITING = "NOT_YET_RECRUITING"
    RECRUITING = "RECRUITING"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"
    WITHDRAWN = "WITHDRAWN"
    AVAILABLE = "AVAILABLE"
    # Note: Spec says RecruitmentStatus has subset of Status values, but doesn't include NO_LONGER_AVAILABLE etc.
    # However, Status enum in spec includes all. We'll keep separate if strict adherence desired, or reuse Status.
    # Spec definition:
    # "ACTIVE_NOT_RECRUITING", "COMPLETED", "ENROLLING_BY_INVITATION", "NOT_YET_RECRUITING",
    # "RECRUITING", "SUSPENDED", "TERMINATED", "WITHDRAWN", "AVAILABLE"


class ReferenceType(str, Enum):
    BACKGROUND = "BACKGROUND"
    RESULT = "RESULT"
    DERIVED = "DERIVED"


class MeasureParam(str, Enum):
    GEOMETRIC_MEAN = "GEOMETRIC_MEAN"
    GEOMETRIC_LEAST_SQUARES_MEAN = "GEOMETRIC_LEAST_SQUARES_MEAN"
    LEAST_SQUARES_MEAN = "LEAST_SQUARES_MEAN"
    LOG_MEAN = "LOG_MEAN"
    MEAN = "MEAN"
    MEDIAN = "MEDIAN"
    NUMBER = "NUMBER"
    COUNT_OF_PARTICIPANTS = "COUNT_OF_PARTICIPANTS"
    COUNT_OF_UNITS = "COUNT_OF_UNITS"


class MeasureDispersionType(str, Enum):
    NA = "NA"
    STANDARD_DEVIATION = "STANDARD_DEVIATION"
    STANDARD_ERROR = "STANDARD_ERROR"
    INTER_QUARTILE_RANGE = "INTER_QUARTILE_RANGE"
    FULL_RANGE = "FULL_RANGE"
    CONFIDENCE_80 = "CONFIDENCE_80"
    CONFIDENCE_90 = "CONFIDENCE_90"
    CONFIDENCE_95 = "CONFIDENCE_95"
    CONFIDENCE_975 = "CONFIDENCE_975"
    CONFIDENCE_99 = "CONFIDENCE_99"
    CONFIDENCE_OTHER = "CONFIDENCE_OTHER"
    GEOMETRIC_COEFFICIENT = "GEOMETRIC_COEFFICIENT"


class OutcomeMeasureType(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    OTHER_PRE_SPECIFIED = "OTHER_PRE_SPECIFIED"
    POST_HOC = "POST_HOC"


class ReportingStatus(str, Enum):
    NOT_POSTED = "NOT_POSTED"
    POSTED = "POSTED"


class EventAssessment(str, Enum):
    NON_SYSTEMATIC_ASSESSMENT = "NON_SYSTEMATIC_ASSESSMENT"
    SYSTEMATIC_ASSESSMENT = "SYSTEMATIC_ASSESSMENT"


class AgreementRestrictionType(str, Enum):
    LTE60 = "LTE60"
    GT60 = "GT60"
    OTHER = "OTHER"


class BrowseLeafRelevance(str, Enum):
    LOW = "LOW"
    HIGH = "HIGH"


class DesignMasking(str, Enum):
    NONE = "NONE"
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    TRIPLE = "TRIPLE"
    QUADRUPLE = "QUADRUPLE"


class WhoMasked(str, Enum):
    PARTICIPANT = "PARTICIPANT"
    CARE_PROVIDER = "CARE_PROVIDER"
    INVESTIGATOR = "INVESTIGATOR"
    OUTCOMES_ASSESSOR = "OUTCOMES_ASSESSOR"


class AnalysisDispersionType(str, Enum):
    STANDARD_DEVIATION = "STANDARD_DEVIATION"
    STANDARD_ERROR_OF_MEAN = "STANDARD_ERROR_OF_MEAN"


class ConfidenceIntervalNumSides(str, Enum):
    ONE_SIDED = "ONE_SIDED"
    TWO_SIDED = "TWO_SIDED"


class NonInferiorityType(str, Enum):
    SUPERIORITY = "SUPERIORITY"
    NON_INFERIORITY = "NON_INFERIORITY"
    EQUIVALENCE = "EQUIVALENCE"
    OTHER = "OTHER"
    NON_INFERIORITY_OR_EQUIVALENCE = "NON_INFERIORITY_OR_EQUIVALENCE"
    SUPERIORITY_OR_OTHER = "SUPERIORITY_OR_OTHER"
    NON_INFERIORITY_OR_EQUIVALENCE_LEGACY = "NON_INFERIORITY_OR_EQUIVALENCE_LEGACY"
    SUPERIORITY_OR_OTHER_LEGACY = "SUPERIORITY_OR_OTHER_LEGACY"


class UnpostedEventType(str, Enum):
    RESET = "RESET"
    RELEASE = "RELEASE"
    UNRELEASE = "UNRELEASE"


class ViolationEventType(str, Enum):
    VIOLATION_IDENTIFIED = "VIOLATION_IDENTIFIED"
    CORRECTION_CONFIRMED = "CORRECTION_CONFIRMED"
    PENALTY_IMPOSED = "PENALTY_IMPOSED"
    ISSUES_IN_LETTER_ADDRESSED_CONFIRMED = "ISSUES_IN_LETTER_ADDRESSED_CONFIRMED"


# --- Shared Models ---


class DateStruct(SQLModel):
    date: Optional[str] = None
    type: Optional[DateType] = None


class PartialDateStruct(SQLModel):
    date: Optional[str] = None
    type: Optional[DateType] = None


class OrgStudyIdInfo(SQLModel):
    id: Optional[str] = None
    type: Optional[OrgStudyIdType] = None
    link: Optional[str] = None


class SecondaryIdInfo(SQLModel):
    id: Optional[str] = None
    type: Optional[SecondaryIdType] = None
    domain: Optional[str] = None
    link: Optional[str] = None


class Organization(SQLModel):
    fullName: Optional[str] = None
    class_: Optional[AgencyClass] = Field(None, alias="class")


class GeoPoint(SQLModel):
    lat: float
    lon: float


class WebLink(SQLModel):
    label: str
    url: str


class MaskingBlock(SQLModel):
    masking: Optional[DesignMasking] = None
    maskingDescription: Optional[str] = None
    whoMasked: Optional[List[WhoMasked]] = None


class ExpandedAccessTypes(SQLModel):
    individual: Optional[bool] = None
    intermediate: Optional[bool] = None
    treatment: Optional[bool] = None


class ExpandedAccessInfo(SQLModel):
    hasExpandedAccess: Optional[bool] = None
    nctId: Optional[str] = None
    statusForNctId: Optional[ExpandedAccessStatus] = None


class Contact(SQLModel):
    name: Optional[str] = None
    role: Optional[ContactRole] = None
    phone: Optional[str] = None
    phoneExt: Optional[str] = None
    email: Optional[str] = None


class Official(SQLModel):
    name: Optional[str] = None
    affiliation: Optional[str] = None
    role: Optional[OfficialRole] = None


class Location(SQLModel):
    facility: Optional[str] = None
    status: Optional[RecruitmentStatus] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    contacts: Optional[List[Contact]] = None
    geoPoint: Optional[Dict[str, float]] = None  # Actually GeoPoint object


class Sponsor(SQLModel):
    name: Optional[str] = None
    class_: Optional[AgencyClass] = Field(None, alias="class")


class ResponsibleParty(SQLModel):
    type: Optional[ResponsiblePartyType] = None
    investigatorFullName: Optional[str] = None
    investigatorTitle: Optional[str] = None
    investigatorAffiliation: Optional[str] = None
    oldNameTitle: Optional[str] = None
    oldOrganization: Optional[str] = None


# --- Protocol Section Modules ---


class IdentificationModule(SQLModel):
    nctId: Optional[str] = None
    nctIdAliases: Optional[List[str]] = None
    orgStudyIdInfo: Optional[OrgStudyIdInfo] = None
    secondaryIdInfos: Optional[List[SecondaryIdInfo]] = None
    organization: Optional[Organization] = None
    briefTitle: Optional[str] = None
    officialTitle: Optional[str] = None
    acronym: Optional[str] = None


class StatusModule(SQLModel):
    statusVerifiedDate: Optional[str] = None
    overallStatus: Optional[Status] = None
    lastKnownStatus: Optional[Status] = None
    delayedPosting: Optional[bool] = None
    whyStopped: Optional[str] = None
    expandedAccessInfo: Optional[ExpandedAccessInfo] = None
    startDateStruct: Optional[PartialDateStruct] = None
    primaryCompletionDateStruct: Optional[PartialDateStruct] = None
    completionDateStruct: Optional[PartialDateStruct] = None
    studyFirstSubmitDate: Optional[str] = None
    studyFirstSubmitQcDate: Optional[str] = None
    studyFirstPostDateStruct: Optional[DateStruct] = None
    resultsWaived: Optional[bool] = None
    resultsFirstSubmitDate: Optional[str] = None
    resultsFirstSubmitQcDate: Optional[str] = None
    resultsFirstPostDateStruct: Optional[DateStruct] = None
    dispFirstSubmitDate: Optional[str] = None
    dispFirstSubmitQcDate: Optional[str] = None
    dispFirstPostDateStruct: Optional[DateStruct] = None
    lastUpdateSubmitDate: Optional[str] = None
    lastUpdatePostDateStruct: Optional[DateStruct] = None


class SponsorCollaboratorsModule(SQLModel):
    responsibleParty: Optional[ResponsibleParty] = None
    leadSponsor: Optional[Sponsor] = None
    collaborators: Optional[List[Sponsor]] = None


class OversightModule(SQLModel):
    oversightHasDmc: Optional[bool] = None
    isFdaRegulatedDrug: Optional[bool] = None
    isFdaRegulatedDevice: Optional[bool] = None
    isUnapprovedDevice: Optional[bool] = None
    isPpsd: Optional[bool] = None
    isUsExport: Optional[bool] = None
    fdaaa801Violation: Optional[bool] = None


class DescriptionModule(SQLModel):
    briefSummary: Optional[str] = None
    detailedDescription: Optional[str] = None


class ConditionsModule(SQLModel):
    conditions: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


class DesignInfo(SQLModel):
    allocation: Optional[DesignAllocation] = None
    interventionModel: Optional[InterventionalAssignment] = None
    interventionModelDescription: Optional[str] = None
    primaryPurpose: Optional[PrimaryPurpose] = None
    observationalModel: Optional[ObservationalModel] = None
    timePerspective: Optional[DesignTimePerspective] = None
    maskingInfo: Optional[MaskingBlock] = None


class BioSpec(SQLModel):
    retention: Optional[BioSpecRetention] = None
    description: Optional[str] = None


class EnrollmentInfo(SQLModel):
    count: Optional[int] = None
    type: Optional[EnrollmentType] = None


class DesignModule(SQLModel):
    studyType: Optional[StudyType] = None
    nPtrsToThisExpAccNctId: Optional[int] = None
    expandedAccessTypes: Optional[ExpandedAccessTypes] = None
    patientRegistry: Optional[bool] = None
    targetDuration: Optional[str] = None
    phases: Optional[List[Phase]] = None
    designInfo: Optional[DesignInfo] = None
    bioSpec: Optional[BioSpec] = None
    enrollmentInfo: Optional[EnrollmentInfo] = None


class ArmGroup(SQLModel):
    label: Optional[str] = None
    type: Optional[ArmGroupType] = None
    description: Optional[str] = None
    interventionNames: Optional[List[str]] = None


class Intervention(SQLModel):
    type: Optional[InterventionType] = None
    name: Optional[str] = None
    description: Optional[str] = None
    armGroupLabels: Optional[List[str]] = None
    otherNames: Optional[List[str]] = None


class ArmsInterventionsModule(SQLModel):
    armGroups: Optional[List[ArmGroup]] = None
    interventions: Optional[List[Intervention]] = None


class Outcome(SQLModel):
    measure: Optional[str] = None
    description: Optional[str] = None
    timeFrame: Optional[str] = None


class OutcomesModule(SQLModel):
    primaryOutcomes: Optional[List[Outcome]] = None
    secondaryOutcomes: Optional[List[Outcome]] = None
    otherOutcomes: Optional[List[Outcome]] = None


class EligibilityModule(SQLModel):
    eligibilityCriteria: Optional[str] = None
    healthyVolunteers: Optional[bool] = None
    sex: Optional[Sex] = None
    genderBased: Optional[bool] = None
    genderDescription: Optional[str] = None
    minimumAge: Optional[str] = None
    maximumAge: Optional[str] = None
    stdAges: Optional[List[StandardAge]] = None
    studyPopulation: Optional[str] = None
    samplingMethod: Optional[SamplingMethod] = None


class ContactsLocationsModule(SQLModel):
    centralContacts: Optional[List[Contact]] = None
    overallOfficials: Optional[List[Official]] = None
    locations: Optional[List[Location]] = None


class Retraction(SQLModel):
    pmid: Optional[str] = None
    source: Optional[str] = None


class Reference(SQLModel):
    pmid: Optional[str] = None
    type: Optional[ReferenceType] = None
    citation: Optional[str] = None
    retractions: Optional[List[Retraction]] = None


class SeeAlsoLink(SQLModel):
    label: Optional[str] = None
    url: Optional[str] = None


class AvailIpd(SQLModel):
    id: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None
    comment: Optional[str] = None


class ReferencesModule(SQLModel):
    references: Optional[List[Reference]] = None
    seeAlsoLinks: Optional[List[SeeAlsoLink]] = None
    availIpds: Optional[List[AvailIpd]] = None


class IpdSharingStatementModule(SQLModel):
    ipdSharing: Optional[IpdSharing] = None
    description: Optional[str] = None
    infoTypes: Optional[List[IpdSharingInfoType]] = None
    timeFrame: Optional[str] = None
    accessCriteria: Optional[str] = None
    url: Optional[str] = None


class ProtocolSection(SQLModel):
    identificationModule: Optional[IdentificationModule] = None
    statusModule: Optional[StatusModule] = None
    sponsorCollaboratorsModule: Optional[SponsorCollaboratorsModule] = None
    oversightModule: Optional[OversightModule] = None
    descriptionModule: Optional[DescriptionModule] = None
    conditionsModule: Optional[ConditionsModule] = None
    designModule: Optional[DesignModule] = None
    armsInterventionsModule: Optional[ArmsInterventionsModule] = None
    outcomesModule: Optional[OutcomesModule] = None
    eligibilityModule: Optional[EligibilityModule] = None
    contactsLocationsModule: Optional[ContactsLocationsModule] = None
    referencesModule: Optional[ReferencesModule] = None
    ipdSharingStatementModule: Optional[IpdSharingStatementModule] = None


# --- Results Section Models ---


class MeasureCategory(SQLModel):
    title: Optional[str] = None
    measurements: Optional[List[Dict[str, Any]]] = (
        None  # Recursive Measurement type simplified for now
    )


class MeasureClass(SQLModel):
    title: Optional[str] = None
    denoms: Optional[List[Dict[str, Any]]] = None  # Recursive Denom
    categories: Optional[List[MeasureCategory]] = None


class DenomCount(SQLModel):
    groupId: Optional[str] = None
    value: Optional[str] = None


class Denom(SQLModel):
    units: Optional[str] = None
    counts: Optional[List[DenomCount]] = None


class MeasureGroup(SQLModel):
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


class BaselineMeasure(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    populationDescription: Optional[str] = None
    paramType: Optional[MeasureParam] = None
    dispersionType: Optional[MeasureDispersionType] = None
    unitOfMeasure: Optional[str] = None
    calculatePct: Optional[bool] = None
    denomUnitsSelected: Optional[str] = None
    denoms: Optional[List[Denom]] = None
    classes: Optional[List[MeasureClass]] = None


class BaselineCharacteristicsModule(SQLModel):
    populationDescription: Optional[str] = None
    typeUnitsAnalyzed: Optional[str] = None
    groups: Optional[List[MeasureGroup]] = None
    denoms: Optional[List[Denom]] = None
    measures: Optional[List[BaselineMeasure]] = None


class FlowStats(SQLModel):
    groupId: Optional[str] = None
    comment: Optional[str] = None
    numSubjects: Optional[str] = None
    numUnits: Optional[str] = None


class FlowMilestone(SQLModel):
    type: Optional[str] = None
    comment: Optional[str] = None
    achievements: Optional[List[FlowStats]] = None


class DropWithdraw(SQLModel):
    type: Optional[str] = None
    comment: Optional[str] = None
    reasons: Optional[List[FlowStats]] = None


class FlowPeriod(SQLModel):
    title: Optional[str] = None
    milestones: Optional[List[FlowMilestone]] = None
    dropWithdraws: Optional[List[DropWithdraw]] = None


class FlowGroup(SQLModel):
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


class ParticipantFlowModule(SQLModel):
    preAssignmentDetails: Optional[str] = None
    recruitmentDetails: Optional[str] = None
    typeUnitsAnalyzed: Optional[str] = None
    groups: Optional[List[FlowGroup]] = None
    periods: Optional[List[FlowPeriod]] = None


class MeasureAnalysis(SQLModel):
    paramType: Optional[str] = None
    paramValue: Optional[str] = None
    dispersionType: Optional[AnalysisDispersionType] = None
    dispersionValue: Optional[str] = None
    statisticalMethod: Optional[str] = None
    statisticalComment: Optional[str] = None
    pValue: Optional[str] = None
    pValueComment: Optional[str] = None
    ciNumSides: Optional[ConfidenceIntervalNumSides] = None
    ciPctValue: Optional[str] = None
    ciLowerLimit: Optional[str] = None
    ciUpperLimit: Optional[str] = None
    ciLowerLimitComment: Optional[str] = None
    ciUpperLimitComment: Optional[str] = None
    estimateComment: Optional[str] = None
    testedNonInferiority: Optional[bool] = None
    nonInferiorityType: Optional[NonInferiorityType] = None
    nonInferiorityComment: Optional[str] = None
    otherAnalysisDescription: Optional[str] = None
    groupDescription: Optional[str] = None
    groupIds: Optional[List[str]] = None


class OutcomeMeasure(SQLModel):
    type: Optional[OutcomeMeasureType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    populationDescription: Optional[str] = None
    reportingStatus: Optional[ReportingStatus] = None
    anticipatedPostingDate: Optional[str] = None
    paramType: Optional[MeasureParam] = None
    dispersionType: Optional[str] = None
    unitOfMeasure: Optional[str] = None
    calculatePct: Optional[bool] = None
    timeFrame: Optional[str] = None
    typeUnitsAnalyzed: Optional[str] = None
    denomUnitsSelected: Optional[str] = None
    groups: Optional[List[MeasureGroup]] = None
    denoms: Optional[List[Denom]] = None
    classes: Optional[List[MeasureClass]] = None
    analyses: Optional[List[MeasureAnalysis]] = None


class OutcomeMeasuresModule(SQLModel):
    outcomeMeasures: Optional[List[OutcomeMeasure]] = None


class EventStats(SQLModel):
    groupId: Optional[str] = None
    numEvents: Optional[int] = None
    numAffected: Optional[int] = None
    numAtRisk: Optional[int] = None


class AdverseEvent(SQLModel):
    term: Optional[str] = None
    organSystem: Optional[str] = None
    sourceVocabulary: Optional[str] = None
    assessmentType: Optional[EventAssessment] = None
    notes: Optional[str] = None
    stats: Optional[List[EventStats]] = None


class EventGroup(SQLModel):
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    deathsNumAffected: Optional[int] = None
    deathsNumAtRisk: Optional[int] = None
    seriousNumAffected: Optional[int] = None
    seriousNumAtRisk: Optional[int] = None
    otherNumAffected: Optional[int] = None
    otherNumAtRisk: Optional[int] = None


class AdverseEventsModule(SQLModel):
    frequencyThreshold: Optional[str] = None
    timeFrame: Optional[str] = None
    description: Optional[str] = None
    allCauseMortalityComment: Optional[str] = None
    eventGroups: Optional[List[EventGroup]] = None
    seriousEvents: Optional[List[AdverseEvent]] = None
    otherEvents: Optional[List[AdverseEvent]] = None


class LimitationsAndCaveats(SQLModel):
    description: Optional[str] = None


class CertainAgreement(SQLModel):
    piSponsorEmployee: Optional[bool] = None
    restrictionType: Optional[AgreementRestrictionType] = None
    restrictiveAgreement: Optional[bool] = None
    otherDetails: Optional[str] = None


class PointOfContact(SQLModel):
    title: Optional[str] = None
    organization: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    phoneExt: Optional[str] = None


class MoreInfoModule(SQLModel):
    limitationsAndCaveats: Optional[LimitationsAndCaveats] = None
    certainAgreement: Optional[CertainAgreement] = None
    pointOfContact: Optional[PointOfContact] = None


class ResultsSection(SQLModel):
    participantFlowModule: Optional[ParticipantFlowModule] = None
    baselineCharacteristicsModule: Optional[BaselineCharacteristicsModule] = None
    outcomeMeasuresModule: Optional[OutcomeMeasuresModule] = None
    adverseEventsModule: Optional[AdverseEventsModule] = None
    moreInfoModule: Optional[MoreInfoModule] = None


# --- Annotation / Document / Derived Sections ---


class UnpostedEvent(SQLModel):
    type: Optional[UnpostedEventType] = None
    date: Optional[str] = None
    dateUnknown: Optional[bool] = None


class UnpostedAnnotation(SQLModel):
    unpostedResponsibleParty: Optional[str] = None
    unpostedEvents: Optional[List[UnpostedEvent]] = None


class ViolationEvent(SQLModel):
    type: Optional[ViolationEventType] = None
    description: Optional[str] = None
    creationDate: Optional[str] = None
    issuedDate: Optional[str] = None
    releaseDate: Optional[str] = None
    postedDate: Optional[str] = None


class ViolationAnnotation(SQLModel):
    violationEvents: Optional[List[ViolationEvent]] = None


class AnnotationModule(SQLModel):
    unpostedAnnotation: Optional[UnpostedAnnotation] = None
    violationAnnotation: Optional[ViolationAnnotation] = None


class AnnotationSection(SQLModel):
    annotationModule: Optional[AnnotationModule] = None


class LargeDoc(SQLModel):
    typeAbbrev: Optional[str] = None
    hasProtocol: Optional[bool] = None
    hasSap: Optional[bool] = None
    hasIcf: Optional[bool] = None
    label: Optional[str] = None
    date: Optional[str] = None
    uploadDate: Optional[str] = None
    filename: Optional[str] = None
    size: Optional[int] = None


class LargeDocumentModule(SQLModel):
    noSap: Optional[bool] = None
    largeDocs: Optional[List[LargeDoc]] = None


class DocumentSection(SQLModel):
    largeDocumentModule: Optional[LargeDocumentModule] = None


class FirstMcpInfo(SQLModel):
    postDateStruct: Optional[DateStruct] = None


class SubmissionInfo(SQLModel):
    releaseDate: Optional[str] = None
    unreleaseDate: Optional[str] = None
    unreleaseDateUnknown: Optional[bool] = None
    resetDate: Optional[str] = None
    mcpReleaseN: Optional[int] = None


class SubmissionTracking(SQLModel):
    estimatedResultsFirstSubmitDate: Optional[str] = None
    firstMcpInfo: Optional[FirstMcpInfo] = None
    submissionInfos: Optional[List[SubmissionInfo]] = None


class MiscInfoModule(SQLModel):
    versionHolder: Optional[str] = None
    removedCountries: Optional[List[str]] = None
    submissionTracking: Optional[SubmissionTracking] = None


class Mesh(SQLModel):
    id: Optional[str] = None
    term: Optional[str] = None


class BrowseLeaf(SQLModel):
    id: Optional[str] = None
    name: Optional[str] = None
    asFound: Optional[str] = None
    relevance: Optional[BrowseLeafRelevance] = None


class BrowseBranch(SQLModel):
    abbrev: Optional[str] = None
    name: Optional[str] = None


class BrowseModule(SQLModel):
    meshes: Optional[List[Mesh]] = None
    ancestors: Optional[List[Mesh]] = None
    browseLeaves: Optional[List[BrowseLeaf]] = None
    browseBranches: Optional[List[BrowseBranch]] = None


class DerivedSection(SQLModel):
    miscInfoModule: Optional[MiscInfoModule] = None
    conditionBrowseModule: Optional[BrowseModule] = None
    interventionBrowseModule: Optional[BrowseModule] = None


# --- Main Study Model ---


class CTGovStudy(SQLModel, table=True):
    """
    Model representing a study returned by ClinicalTrials.gov API.
    Also serves as the database model for storing studies.

    This model uses a document-oriented approach with JSON columns for the main data sections,
    combined with generated columns and indexes for optimal query performance.

    Version Tracking:
    - Uses append-only approach to maintain full history of study updates
    - Each record has a unique `id` (auto-increment primary key)
    - `nct_id` identifies the study across versions (indexed, not primary key)
    - `version_date` tracks when this version was created
    - `is_latest` flag marks the current version for fast queries

    Indexing Strategy:
    - GIN indexes on JSON columns (protocolSection, resultsSection, derivedSection) for flexible ad-hoc queries
    - Generated columns + B-tree indexes for frequently queried specific fields (faster than GIN)
    - Composite indexes for (nct_id, is_latest) and (nct_id, version_date) for version queries
    - pgvector indexes (HNSW) for semantic search on embeddings (when implemented)
    """

    # Primary key (auto-increment)
    id: Optional[int] = Field(default=None, primary_key=True)

    # Study identifier (not unique anymore - multiple versions per NCT ID)
    nct_id: Optional[str] = Field(
        default=None, index=True, description="ClinicalTrials.gov NCT identifier"
    )

    # Version tracking fields
    version_date: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), index=True),
        description="Date this version was created/fetched from API",
    )
    content_hash: Optional[str] = Field(
        default=None,
        index=True,
        description="Hash of the study content (SHA-256) to detect changes",
    )
    is_latest: bool = Field(
        default=True,
        index=True,
        description="Flag indicating if this is the most recent version of the study",
    )

    # JSONB columns for document storage (JSONB is required for GIN indexes)
    protocolSection: Optional[ProtocolSection] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Protocol section of the study",
    )
    resultsSection: Optional[ResultsSection] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Results section of the study",
    )
    derivedSection: Optional[DerivedSection] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Derived section of the study",
    )
    documentSection: Optional[DocumentSection] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Document section of the study",
    )
    annotationSection: Optional[AnnotationSection] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Annotation section of the study",
    )
    hasResults: Optional[bool] = Field(
        None, description="Indicates if the study has results"
    )

    # Generated columns for frequently queried fields (with B-tree indexes for fast equality/range queries)
    overall_status: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String,
            Computed("(\"protocolSection\"->>'statusModule')::jsonb->>'overallStatus'"),
            index=True,
        ),
        description="Generated: Overall status of the study (e.g., RECRUITING, COMPLETED)",
    )

    study_type: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String,
            Computed("(\"protocolSection\"->>'designModule')::jsonb->>'studyType'"),
            index=True,
        ),
        description="Generated: Type of study (e.g., INTERVENTIONAL, OBSERVATIONAL)",
    )

    brief_title: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String,
            Computed(
                "(\"protocolSection\"->>'identificationModule')::jsonb->>'briefTitle'"
            ),
            index=True,
        ),
        description="Generated: Brief title of the study for text search",
    )

    org_study_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String,
            Computed(
                "((\"protocolSection\"->>'identificationModule')::jsonb->>'orgStudyIdInfo')::jsonb->>'id'"
            ),
            index=True,
        ),
        description="Generated: Organization's unique study ID",
    )

    start_date: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String,
            Computed(
                "((\"protocolSection\"->>'statusModule')::jsonb->>'startDateStruct')::jsonb->>'date'"
            ),
            index=True,
        ),
        description="Generated: Study start date for range queries",
    )

    completion_date: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String,
            Computed(
                "((\"protocolSection\"->>'statusModule')::jsonb->>'completionDateStruct')::jsonb->>'date'"
            ),
            index=True,
        ),
        description="Generated: Study completion date for range queries",
    )

    enrollment_count: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String,
            Computed(
                "(\"protocolSection\"->>'designModule')::jsonb->>'enrollmentCount'"
            ),
            index=True,
        ),
        description="Generated: Enrollment count for filtering and sorting",
    )

    lead_sponsor_name: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String,
            Computed(
                "((\"protocolSection\"->>'sponsorCollaboratorsModule')::jsonb->>'leadSponsor')::jsonb->>'name'"
            ),
            index=True,
        ),
        description="Generated: Lead sponsor name for filtering",
    )

    # Table-level indexes
    __table_args__: ClassVar[Tuple[Index, ...]] = (
        # GIN indexes on JSON columns for flexible ad-hoc queries using @>, ?, ?|, ?& operators
        Index(
            "idx_ctgovstudy_protocol_gin",
            text('"protocolSection"'),
            postgresql_using="gin",
        ),
        Index(
            "idx_ctgovstudy_results_gin",
            text('"resultsSection"'),
            postgresql_using="gin",
        ),
        Index(
            "idx_ctgovstudy_derived_gin",
            text('"derivedSection"'),
            postgresql_using="gin",
        ),
        # Version tracking indexes
        Index("idx_ctgovstudy_nct_latest", "nct_id", "is_latest"),
        Index("idx_ctgovstudy_nct_version", "nct_id", "version_date"),
        # Composite indexes for common query patterns
        Index("idx_ctgovstudy_status_type", "overall_status", "study_type"),
        Index("idx_ctgovstudy_status_start", "overall_status", "start_date"),
    )

    @model_validator(mode="before")
    @classmethod
    def extract_nct_id_and_parse_sections(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Extract NCT ID
            if "nct_id" not in data or not data["nct_id"]:
                try:
                    ps = data.get("protocolSection")
                    if isinstance(ps, dict):
                        nct_id = ps.get("identificationModule", {}).get("nctId")
                        if nct_id:
                            data["nct_id"] = nct_id
                except (AttributeError, KeyError, TypeError):
                    pass

            # Parse nested sections if they are dicts
            # This is needed because sa_column=Column(JSON) doesn't auto-parse
            try:
                if "protocolSection" in data and isinstance(
                    data["protocolSection"], dict
                ):
                    data["protocolSection"] = ProtocolSection(**data["protocolSection"])
            except Exception:
                # If parsing fails, leave as dict
                pass

            try:
                if "resultsSection" in data and isinstance(
                    data["resultsSection"], dict
                ):
                    data["resultsSection"] = ResultsSection(**data["resultsSection"])
            except Exception:
                pass

            try:
                if "derivedSection" in data and isinstance(
                    data["derivedSection"], dict
                ):
                    data["derivedSection"] = DerivedSection(**data["derivedSection"])
            except Exception:
                pass

            try:
                if "documentSection" in data and isinstance(
                    data["documentSection"], dict
                ):
                    data["documentSection"] = DocumentSection(**data["documentSection"])
            except Exception:
                pass

            try:
                if "annotationSection" in data and isinstance(
                    data["annotationSection"], dict
                ):
                    data["annotationSection"] = AnnotationSection(
                        **data["annotationSection"]
                    )
            except Exception:
                pass

        return data


class StudiesParams(SQLModel):
    format: Literal["json", "csv"] = Field("json", description="Response format")
    markupFormat: Literal["markdown", "legacy"] = Field(
        "markdown", description="Markup format for text fields"
    )
    query_cond: Optional[str] = Field(
        None, description="Condition search query", alias="query.cond"
    )
    query_term: Optional[str] = Field(
        None, description="Term search query", alias="query.term"
    )
    query_locn: Optional[str] = Field(
        None, description="Location search query", alias="query.locn"
    )
    query_titles: Optional[str] = Field(
        None, description="Title search query", alias="query.titles"
    )
    query_intervention: Optional[str] = Field(
        None, description="Intervention search query", alias="query.intervention"
    )
    query_intr: Optional[str] = Field(
        None, description="Intervention / treatment query", alias="query.intr"
    )
    query_outc: Optional[str] = Field(
        None, description="Outcome measure query", alias="query.outc"
    )
    query_spons: Optional[str] = Field(
        None, description="Sponsor / collaborator query", alias="query.spons"
    )
    query_lead: Optional[str] = Field(
        None, description="Lead Sponsor Name query", alias="query.lead"
    )
    query_id: Optional[str] = Field(
        None, description="Study IDs query", alias="query.id"
    )
    query_patient: Optional[str] = Field(
        None, description="Patient search query", alias="query.patient"
    )
    filter_overallStatus: Optional[List[str]] = Field(
        None, description="Filter by overall status", alias="filter.overallStatus"
    )
    filter_geo: Optional[str] = Field(
        None, description="Filter by geography", alias="filter.geo"
    )
    filter_ids: Optional[List[str]] = Field(
        None, description="Filter by NCT IDs", alias="filter.ids"
    )
    filter_advanced: Optional[str] = Field(
        None, description="Advanced filter expression", alias="filter.advanced"
    )
    filter_synonyms: Optional[List[str]] = Field(
        None, description="Area to apply synonym search", alias="filter.synonyms"
    )
    postFilter_overallStatus: Optional[List[str]] = Field(
        None,
        description="Post-filter by overall status",
        alias="postFilter.overallStatus",
    )
    postFilter_geo: Optional[str] = Field(
        None, description="Post-filter by geography", alias="postFilter.geo"
    )
    postFilter_ids: Optional[List[str]] = Field(
        None, description="Post-filter by NCT IDs", alias="postFilter.ids"
    )
    postFilter_advanced: Optional[str] = Field(
        None, description="Post-filter advanced expression", alias="postFilter.advanced"
    )
    postFilter_synonyms: Optional[List[str]] = Field(
        None, description="Post-filter synonym search area", alias="postFilter.synonyms"
    )
    aggFilters: Optional[str] = Field(None, description="Aggregation filters")
    geoDecay: Optional[str] = Field(
        None, description="Set proximity factor by distance from filter.geo location"
    )
    geo: Optional[str] = Field(None, description="Geographic location filter")
    ids: Optional[List[str]] = Field(None, description="List of NCT IDs to filter by")
    titles: Optional[str] = Field(None, description="Title search string")
    intervention: Optional[str] = Field(None, description="Intervention search string")
    term: Optional[str] = Field(None, description="Term search string")
    cond: Optional[str] = Field(None, description="Condition search string")
    sort: Optional[List[str]] = Field(None, description="Sort fields")
    countTotal: Optional[bool] = Field(
        None, description="Include total count in response"
    )
    pageSize: int = Field(10, description="Number of results per page (max 1000)")
    pageToken: Optional[str] = Field(
        None, description="Token for the next page of results"
    )
    fields: Optional[List[str]] = Field(None, description="List of fields to return")

    model_config = ConfigDict(populate_by_name=True)


class StudiesResponse(SQLModel):
    studies: List[CTGovStudy] = Field(
        default_factory=list, description="List of studies returned"
    )
    nextPageToken: Optional[str] = Field(
        None, description="Token for the next page of results"
    )
    totalCount: Optional[int] = Field(
        None, description="Total number of studies matching the query (if requested)"
    )

