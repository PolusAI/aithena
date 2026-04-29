# GARDIAN Phase 2 + Phase 3 Statement of Work

**Date:** 2026-04-29
**Status:** Approved design, pre-implementation
**Timeframe:** 6 months
**Delivery bar:** Internal NCATS-staff alpha
**Deployment target:** DALI HPC at NCATS (existing K8s footprint), local development on Polus
**Team:** 1 supervisor at ~25% time + 1 hire at 100% time (~7.5 person-months total effort)

---

## 1. Background

GARDIAN (Clinical Aithena) is a real-time clinical-trial matching system for rare diseases, developed for the NCATS/NIH GARD program. It adapts the TrialGPT pipeline (NCBI/NLM) into a sub-30-second API that returns ranked clinical trials from ClinicalTrials.gov. Phase 1 (MVP using TrialGPT code) was completed in the prior development cycle and is currently deployed on Polus.

This SOW covers Phase 2 (agentic intake) and Phase 3 (RAG-based tailoring), with Phase 4 (feedback loop) as a stretch goal. IDP/Databricks application work is explicitly out of scope.

## 2. Goals

**Phase 2 — Agentic intake.** Replace ad-hoc free-text patient input with an agentic-AI conversation that elicits the fields TrialGPT requires, gates on a rare-disease being identified, and produces a patient summary formatted to match TrialGPT's training-data conventions.

**Phase 3 — RAG-based tailoring.** Use linked data (RDIP, where available; manual curation where not) to tailor three surfaces:

- **Tailored intake questions:** disease-aware question banks (e.g., neurologic-specific questions for spastic paraplegia, vs. metabolic-specific for urea cycle disorders).
- **Tailored outputs:** disease-aware ranking weights and inclusion guarantees (e.g., always include Urea Cycle Disorders Consortium trials when the disease is a urea cycle disorder).
- **Tailored UI mixins:** NCATS-funded trials surface at the top of result lists with distinct visual treatment.

## 3. Scope

### 3.1 In scope — six workstreams

| # | Workstream | Description | Skills |
|---|---|---|---|
| W1 | Agentic intake | State-machine agent that elicits required fields, drafts a TrialGPT-formatted patient summary, gates on rare-disease identification | Agentic-AI, prompt design |
| W2 | RDIP discovery + ingestion | Access negotiation, schema modeling, ingestion pipeline into Postgres, gap analysis with GARD staff | Data engineering, biomedical data |
| W3 | Tailoring policy engine | Disease → tailored question bank, output ranking weights, NCATS-funded-trial flag | Backend (Python/FastAPI), light ML |
| W4 | Frontend tailoring | Disease-aware question rendering, NCATS-funded badges/promoted slots, per-disease ordering | Next.js / React / TypeScript |
| W5 | Guardrails + monitoring | Jailbreak resistance, no-PII enforcement, prompt-injection screening, structured logging | Security-aware backend |
| W6 | Continuous DALI deployment | Per-component rollout on existing K8s footprint, no separate "port" milestone | DevOps / K8s / Helm |

### 3.2 Stretch — Phase 4 feedback capture (W7)

Thumbs-up / thumbs-down on results, admin export of feedback for downstream use. Only attempted if M5 ends with explicit buffer.

### 3.3 Out of scope

- IDP / Databricks application
- Public or external beta
- ATO / 508 / HIPAA compliance work
- Mobile or multilingual UI
- Phase 4 closed-loop retraining
- RDCRN PI tailored-question collection
- Migration to AWS (the prior `ARCHITECTURE.md` AWS plan)

## 4. Tech stance

LLM and embedding choices remain flexible per workstream. Off-the-shelf via LiteLLM / Bedrock is acceptable for fast iteration; internal Ollama / MedCPT via the Ask Aithena infrastructure is acceptable where data sensitivity, cost, or latency favor it. Each component pins its choice independently — no global mandate.

The intake agent (W1) and tailoring policy engine (W3) will use whichever framework the supervisor selects in M1. The TrialGPT git submodule's training examples are the canonical reference for the patient-summary output format.

## 5. Schedule

Each milestone ends with something deployed to DALI alpha. DALI deployment is continuous from M1 because the K8s footprint already exists from the Phase 1 pilot.

### 5.1 Pilot diseases (3, locked in M1)

Selection covers three categories to give the demo variety:
1. A neurologic / movement disorder (e.g., spastic paraplegia)
2. A metabolic disorder with an active NCATS-funded consortium (e.g., a urea cycle disorder)
3. A genetic disorder with a strong consortium presence

Selection happens in M1 with GARD staff input. The list may be revisited once at M3 if RDIP coverage discovered during M1–M2 forces a swap; after M3 the list is frozen.

### 5.2 Monthly milestones

| Month | DALI-deployed milestone | Workstream activity |
|---|---|---|
| **M1 — Foundations** | Skeleton intake agent (generic, untailored) live on DALI alpha. Interface contracts written for agent ↔ RDIP ↔ frontend. Pilot disease list locked. | W1: framework selection, intake state machine v0. W2: RDIP access request, schema discovery, gap inventory. W6: CI/CD for new components. |
| **M2 — Intake v1** | Working intake agent producing TrialGPT-formatted summaries; rare-disease gate enforced; baseline guardrails; end-to-end "type description → matched trials" works. | W1: prompt-drafting agent, field elicitation, summary formatter. W2: first RDIP ingestion (ontology + known disease–trial associations). W5: jailbreak guardrails v1, input PII redaction. |
| **M3 — Tailored intake** | Tailored question bank wired in for the 3 pilot diseases; intake adapts based on user's disease mention. | W3: tailoring policy engine v1, disease → question-bank mapping, generic fallback. W2: continued ingestion + curation for gaps. W1: integration with policy engine. |
| **M4 — Tailored outputs** | NCATS-funded-trial flag in results; per-disease ranking weights; frontend badges + promoted slots shipped. Default landing tab switched to "Match Patient." | W4: UI mixins, badges, custom ordering. W3: ranking weight rules, NCATS-funded source-of-truth integration. |
| **M5 — Hardening** | Full pipeline on DALI passes guardrail + monitoring tests; structured logs flowing; end-to-end test suite covers the 3 pilot diseases. | W5: prompt-injection screening, no-PII audit, monitoring dashboards. W6: per-component health checks. |
| **M6 — Alpha demo + stretch** | NCATS-staff-demoable alpha with 3 pilot diseases tailored and generic fallback for everything else. Demo script and internal user guide delivered. | Stretch W7 (Phase 4): feedback capture + admin export, only if buffer exists. |

### 5.3 Critical path

W1 (intake agent) → W3 (tailoring engine) → W4 (frontend tailoring). Slippage in W2 (RDIP) cascades into M3, so the M1 RDIP discovery sprint is the single highest-risk item and gets explicit supervisor attention.

## 6. Risks and mitigations

1. **RDIP gap exceeds expectations.** *Mitigation:* M1 discovery sprint produces a written gap report. If gaps block, scope tailoring to the available subset and supplement with manual curation for the 3 pilot diseases (supervisor + GARD staff).
2. **Hire ramp eats into M1.** *Mitigation:* M1 is intentionally weighted toward discovery and contracts (low pre-existing-context tasks); supervisor leads framework selection and interface design while hire ramps.
3. **TrialGPT prompt-format brittleness.** *Mitigation:* TrialGPT submodule training examples are canonical from day one; the summary formatter is built and tested against those.
4. **Pilot diseases produce unconvincing demo.** *Mitigation:* selection covers three disease categories with GARD staff input in M1; revisit at M3 when RDIP coverage is known.
5. **Guardrails added late produce brittle alpha.** *Mitigation:* W5 attaches throughout — every workstream merges with at least baseline jailbreak + no-PII coverage.

## 7. Deliverables

- Agentic intake service on DALI (W1) with state-machine spec doc
- RDIP ingestion pipeline + Postgres schema (W2) with gap report
- Tailoring policy engine + question bank for 3 pilot diseases (W3) with policy spec
- Frontend tailoring components (W4): disease-aware question UI, NCATS badges, promoted slots
- Guardrails configuration + monitoring dashboards (W5)
- Helm charts / K8s manifests for each component on DALI (W6)
- Internal user guide + NCATS-staff demo script (M6)
- *(Stretch)* Feedback capture endpoint + admin export (W7, Phase 4)

## 8. Definition of done

The alpha is considered delivered when all of the following are true:

- All six in-scope workstreams are live on DALI internal alpha.
- The 3 pilot rare diseases have working tailored intake and tailored output.
- Generic fallback path works for any other rare disease the user enters.
- Rare-disease gate verified: the agent refuses to draft a summary for non-rare-disease queries.
- No-PII redaction audit passes on a 50-prompt synthetic test set.
- Jailbreak red-team smoke test (10 adversarial prompts) passes.
- One end-to-end demo runs successfully with NCATS staff present.

## 9. Success metric

At end of M6, NCATS staff can paste a patient description for one of the 3 pilot diseases, watch the agent walk them through tailored questions, and receive a ranked clinical-trial list with NCATS-funded studies appropriately promoted — start to finish, on DALI, in under 60 seconds of interaction time excluding the user's own typing.
