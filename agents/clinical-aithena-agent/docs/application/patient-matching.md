# Patient Matching

The Match Patient tab is GARDIAN's primary feature — an AI-powered system that takes a patient's clinical note and finds the most relevant clinical trials, with detailed explanations of why each trial matches and whether the patient is likely eligible.

## Submitting a Clinical Note

To begin matching, the user enters a patient clinical note in the text input area. This should be a free-text description of the patient's medical history, including:

- Primary diagnosis and medical conditions
- Current medications and treatments
- Relevant lab results and biomarkers
- Symptoms and clinical observations
- Any prior treatments or procedures

The input area expands to fit the content, accommodating clinical notes of any length.

!!! tip "What makes a good clinical note?"
    The more specific the clinical note, the better the matching results. Include specific diagnoses (not just symptoms), lab values with units, medication names and dosages, and any relevant genetic or molecular findings. For rare diseases, mentioning the specific disease name and its manifestations helps the system find the most targeted trials.

## The Matching Process

After clicking **Find Matching Trials**, the system runs the full five-stage pipeline:

1. **Generating keywords** — The LLM analyzes the clinical note to extract conditions
2. **Retrieving trials** — Hybrid search finds candidate trials from the database
3. **Matching criteria** — Each candidate trial's eligibility criteria are evaluated
4. **Ranking trials** — Candidates are scored for relevance and eligibility
5. **Returning results** — Matched trials are displayed in ranked order

### Real-Time Progress

Throughout the matching process, live status updates appear in the interface showing exactly what stage the pipeline is in. Messages like "Matching trial 3 of 8" provide visibility into progress and an approximate sense of time remaining. The matching process typically takes 2-5 minutes depending on how many candidate trials are found.

## Reading Results

Results are displayed as a list of matched trials, ranked by relevance. Each trial card shows:

### Trial Overview

- **NCT ID** and **title** of the trial
- **Relevance score** (0-100) — How clinically relevant the trial is to the patient
- **Eligibility score** — Whether the patient appears to meet the trial's criteria (positive = likely eligible, negative = eligibility concerns)

### Why This Trial Matches

A summary explanation from the LLM describing why this particular trial is relevant to the patient. This section is initially collapsed to show just the first portion, with a "read more" link to expand the full explanation.

### Eligibility Assessment

A detailed criterion-by-criterion breakdown showing how the patient's clinical note maps to the trial's inclusion and exclusion criteria. Like the relevance explanation, this is initially collapsed with a "read more" option to see the full detail.

The criterion-level detail is what distinguishes GARDIAN from a simple search engine — rather than just saying "this trial might be relevant," it explains specifically which criteria the patient meets, which they don't, and which couldn't be assessed from the available information.

## Interpreting Scores

### Relevance Score (0-100)

| Range | Interpretation |
|-------|---------------|
| 80-100 | Highly relevant — the trial directly targets the patient's condition |
| 50-79 | Moderately relevant — the trial addresses related conditions or comorbidities |
| 20-49 | Somewhat relevant — tangential connection to the patient's situation |
| 0-19 | Low relevance — minimal connection to the patient's clinical profile |

### Eligibility Score

The eligibility score ranges from the negative of the relevance score to the positive of the relevance score. A trial with relevance 90 can have eligibility from -90 to +90:

- **Positive values** indicate the patient appears to meet most eligibility criteria
- **Near zero** indicates mixed results — some criteria met, some not
- **Negative values** indicate significant eligibility concerns based on the available information

!!! note "Scores are advisory"
    GARDIAN's assessments are based on the information in the clinical note and the LLM's interpretation. They should be treated as a screening tool to prioritize which trials to investigate further, not as a definitive eligibility determination. A clinician should always review the detailed criterion-level assessment before making decisions about trial enrollment.

For example clinical notes you can try, see the [Examples](../examples.md) page.
