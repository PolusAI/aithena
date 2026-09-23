// Enums from OpenAPI Spec / Pydantic Models

export enum Status {
  ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING",
  COMPLETED = "COMPLETED",
  ENROLLING_BY_INVITATION = "ENROLLING_BY_INVITATION",
  NOT_YET_RECRUITING = "NOT_YET_RECRUITING",
  RECRUITING = "RECRUITING",
  SUSPENDED = "SUSPENDED",
  TERMINATED = "TERMINATED",
  WITHDRAWN = "WITHDRAWN",
  AVAILABLE = "AVAILABLE",
  NO_LONGER_AVAILABLE = "NO_LONGER_AVAILABLE",
  TEMPORARILY_NOT_AVAILABLE = "TEMPORARILY_NOT_AVAILABLE",
  APPROVED_FOR_MARKETING = "APPROVED_FOR_MARKETING",
  WITHHELD = "WITHHELD",
  UNKNOWN = "UNKNOWN",
}

export enum StudyType {
  EXPANDED_ACCESS = "EXPANDED_ACCESS",
  INTERVENTIONAL = "INTERVENTIONAL",
  OBSERVATIONAL = "OBSERVATIONAL",
}

export enum Phase {
  NA = "NA",
  EARLY_PHASE1 = "EARLY_PHASE1",
  PHASE1 = "PHASE1",
  PHASE2 = "PHASE2",
  PHASE3 = "PHASE3",
  PHASE4 = "PHASE4",
}

export enum Sex {
  FEMALE = "FEMALE",
  MALE = "MALE",
  ALL = "ALL",
}

export enum StandardAge {
  CHILD = "CHILD",
  ADULT = "ADULT",
  OLDER_ADULT = "OLDER_ADULT",
}

export enum AgencyClass {
  NIH = "NIH",
  FED = "FED",
  OTHER_GOV = "OTHER_GOV",
  INDIV = "INDIV",
  INDUSTRY = "INDUSTRY",
  NETWORK = "NETWORK",
  AMBIG = "AMBIG",
  OTHER = "OTHER",
  UNKNOWN = "UNKNOWN",
}

// Shared Models

export interface Organization {
  fullName?: string;
  class?: AgencyClass;
}

export interface GeoPoint {
  lat: number;
  lon: number;
}

export interface Location {
  facility?: string;
  status?: Status;
  city?: string;
  state?: string;
  zip?: string;
  country?: string;
  geoPoint?: GeoPoint;
}

export interface Contact {
  name?: string;
  role?: string;
  phone?: string;
  phoneExt?: string;
  email?: string;
}

// Protocol Section Modules

export interface IdentificationModule {
  nctId?: string;
  nctIdAliases?: string[];
  briefTitle?: string;
  officialTitle?: string;
  acronym?: string;
  organization?: Organization;
}

export interface StatusModule {
  statusVerifiedDate?: string;
  overallStatus?: Status;
  lastKnownStatus?: Status;
  startDateStruct?: { date?: string; type?: string };
  completionDateStruct?: { date?: string; type?: string };
  studyFirstSubmitDate?: string;
  studyFirstPostDateStruct?: { date?: string; type?: string };
  lastUpdateSubmitDate?: string;
  lastUpdatePostDateStruct?: { date?: string; type?: string };
}

export interface Sponsor {
  name?: string;
  class?: AgencyClass;
}

export interface SponsorCollaboratorsModule {
  leadSponsor?: Sponsor;
  collaborators?: Sponsor[];
}

export interface DescriptionModule {
  briefSummary?: string;
  detailedDescription?: string;
}

export interface ConditionsModule {
  conditions?: string[];
  keywords?: string[];
}

export interface DesignInfo {
  allocation?: string;
  interventionModel?: string;
  primaryPurpose?: string;
  observationalModel?: string;
  timePerspective?: string;
  maskingInfo?: {
    masking?: string;
    maskingDescription?: string;
  };
}

export interface EnrollmentInfo {
  count?: number;
  type?: string;
}

export interface DesignModule {
  studyType?: StudyType;
  phases?: Phase[];
  designInfo?: DesignInfo;
  enrollmentInfo?: EnrollmentInfo;
}

export interface ArmGroup {
  label?: string;
  type?: string;
  description?: string;
  interventionNames?: string[];
}

export interface Intervention {
  type?: string;
  name?: string;
  description?: string;
  armGroupLabels?: string[];
  otherNames?: string[];
}

export interface ArmsInterventionsModule {
  armGroups?: ArmGroup[];
  interventions?: Intervention[];
}

export interface EligibilityModule {
  eligibilityCriteria?: string;
  healthyVolunteers?: boolean;
  sex?: Sex;
  minimumAge?: string;
  maximumAge?: string;
  stdAges?: StandardAge[];
  studyPopulation?: string;
  samplingMethod?: string;
}

export interface ContactsLocationsModule {
  centralContacts?: Contact[];
  overallOfficials?: unknown[];
  locations?: Location[];
}

// Main Sections

export interface ProtocolSection {
  identificationModule?: IdentificationModule;
  statusModule?: StatusModule;
  sponsorCollaboratorsModule?: SponsorCollaboratorsModule;
  oversightModule?: unknown;
  descriptionModule?: DescriptionModule;
  conditionsModule?: ConditionsModule;
  designModule?: DesignModule;
  armsInterventionsModule?: ArmsInterventionsModule;
  outcomesModule?: unknown;
  eligibilityModule?: EligibilityModule;
  contactsLocationsModule?: ContactsLocationsModule;
  referencesModule?: unknown;
}

export interface ResultsSection {
  // Add simplified results structure if needed later
  participantFlowModule?: unknown;
  baselineCharacteristicsModule?: unknown;
  outcomeMeasuresModule?: unknown;
  adverseEventsModule?: unknown;
  moreInfoModule?: unknown;
}

export interface DerivedSection {
  miscInfoModule?: unknown;
  conditionBrowseModule?: unknown;
  interventionBrowseModule?: unknown;
}

// Main Study Interface

export interface CTGovStudy {
  id?: number;
  nct_id?: string;
  version_date?: string; // datetime string
  is_latest?: boolean;
  
  protocolSection?: ProtocolSection;
  resultsSection?: ResultsSection;
  derivedSection?: DerivedSection;
  documentSection?: unknown;
  annotationSection?: unknown;
  
  hasResults?: boolean;
  
  // Generated fields
  overall_status?: string;
  study_type?: string;
  brief_title?: string;
  org_study_id?: string;
  start_date?: string;
  completion_date?: string;
  enrollment_count?: string;
  lead_sponsor_name?: string;
}

// API Responses
export interface StudiesResponse {
  studies: CTGovStudy[];
  nextPageToken?: string;
  totalCount?: number;
}

// API Parameters
export interface StudiesParams {
    format?: "json" | "csv";
    markupFormat?: "markdown" | "legacy";
    "query.cond"?: string;
    "query.term"?: string;
    "query.locn"?: string;
    "query.titles"?: string;
    "query.intervention"?: string;
    "query.intr"?: string;
    "query.outc"?: string;
    "query.spons"?: string;
    "query.lead"?: string;
    "query.id"?: string;
    "query.patient"?: string;
    "filter.overallStatus"?: string[];
    "filter.geo"?: string;
    "filter.ids"?: string[];
    "filter.advanced"?: string;
    "filter.synonyms"?: string[];
    "postFilter.overallStatus"?: string[];
    "postFilter.geo"?: string;
    "postFilter.ids"?: string[];
    "postFilter.advanced"?: string;
    "postFilter.synonyms"?: string[];
    aggFilters?: string;
    geoDecay?: string;
    geo?: string;
    ids?: string[];
    titles?: string;
    intervention?: string;
    term?: string;
    cond?: string;
    sort?: string[];
    countTotal?: boolean;
    pageSize?: number;
    pageToken?: string;
    fields?: string[];
}
