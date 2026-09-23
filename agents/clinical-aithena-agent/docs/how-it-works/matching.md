# Patient Matching

Patient matching is the core of GARDIAN's value proposition. Rather than simply listing trials that share keywords with a patient's condition, GARDIAN evaluates each trial's eligibility criteria against the patient's specific clinical details — producing an assessment that explains *why* a trial is or isn't a good fit.

## From Clinical Note to Conditions

The matching pipeline starts when a user submits a patient's clinical note — a free-text description of the patient's medical history, current conditions, medications, lab results, and other relevant clinical information.

The LLM analyzes this note and produces:

- A **clinical summary** — a concise description of the patient's main medical problems
- Up to **32 search conditions** — ordered by clinical priority, these become the queries used to find candidate trials

For example, given a clinical note describing a patient with Fabry disease, the LLM might extract conditions like:

1. Fabry disease
2. Alpha-galactosidase A deficiency
3. Enzyme replacement therapy
4. Left ventricular hypertrophy
5. Chronic kidney disease stage 3
6. Neuropathic pain

The ordering reflects clinical significance — the primary rare disease diagnosis comes first, followed by specific manifestations and comorbidities.

## Criterion-Level Evaluation

Once candidate trials are retrieved, GARDIAN evaluates each trial at the **individual criterion level**. This means every inclusion criterion and every exclusion criterion is assessed separately against the patient's clinical note.

For each criterion, the LLM produces three outputs:

### 1. Reasoning

A natural language explanation of how the patient's clinical information relates to this specific criterion. For example:

> *"The patient has documented alpha-galactosidase A enzyme activity below 1.5 nmol/hr/mg, which meets the criterion requiring confirmed GLA gene mutation or enzyme deficiency."*

### 2. Evidence References

Specific sentences from the patient's clinical note that support the assessment. This provides traceability — users can verify which parts of the note informed each decision.

### 3. Classification Label

A categorical assessment:

- **Inclusion criteria**:
    - `included` — The patient meets this criterion based on the clinical note
    - `not included` — The patient does not appear to meet this criterion
    - `not applicable` — The criterion cannot be assessed from the available information

- **Exclusion criteria**:
    - `excluded` — The patient is excluded by this criterion
    - `not excluded` — The patient is not excluded by this criterion
    - `not applicable` — The criterion cannot be assessed from the available information

## Scoring and Ranking

After criterion-level matching, the LLM reviews the complete set of criterion assessments for each trial and assigns two scores:

### Relevance Score (R)

A score from **0 to 100** indicating how clinically relevant the trial is to the patient's condition. A trial studying the patient's exact rare disease with appropriate interventions would score near 100. A tangentially related trial might score 20–40.

### Eligibility Score (E)

A score from **-R to +R** indicating the patient's likely eligibility. A positive score means the patient appears to meet most criteria. A negative score means significant eligibility concerns were identified. The score is bounded by the relevance score — a highly relevant trial where the patient is clearly ineligible might have R=90 and E=-60.

### Final Ranking

Trials are sorted by relevance score first, then by eligibility score within the same relevance tier. Each result includes the LLM's written explanation of its scoring rationale, so users can understand and verify the reasoning.

## Handling Uncertainty

Clinical notes rarely contain complete information. A criterion about "adequate liver function" can't be assessed if no liver function tests are mentioned in the note. GARDIAN handles this gracefully through the `not applicable` label — clearly marking criteria that couldn't be evaluated rather than guessing.

This transparency is particularly important for rare diseases, where patients may have extensive but incomplete medical histories. The system surfaces what it can assess and clearly flags what it cannot, allowing clinicians to make informed decisions about which trials to pursue.
