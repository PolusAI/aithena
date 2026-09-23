# API

GARDIAN exposes a REST API built with FastAPI. The API provides endpoints for trial search, patient matching, database statistics, and health monitoring.

## Base URL

| Environment | URL |
|-------------|-----|
| Production | `https://polus1.ncats.nih.gov/apis/ctaithena/` |
| Local development | `http://localhost:8000/` |

## Endpoints

### Health

```
GET /health
```

Returns the service health status. Used by Kubernetes liveness and readiness probes to monitor the API's availability.

### Search

```
GET /search
```

Search the trial database. Supports text queries against trial titles, conditions, interventions, and summaries. Returns paginated results with trial metadata.

### Statistics

```
GET /stats
```

Returns aggregate statistics about the trial corpus:

- Total number of trials
- Number of distinct conditions
- Phase distribution
- Number of distinct interventions

These statistics are computed from the live database and reflect the most recent data sync.

### Patient Match

```
POST /match
```

The primary endpoint for patient matching. Accepts a patient clinical note and runs the full five-stage matching pipeline.

**Request body:**

- `patient_note` — Free-text clinical note describing the patient
- `session_id` — A unique session identifier for receiving real-time progress updates

**Response:**

- Ranked list of matched trials, each with:
    - NCT ID and trial title
    - Relevance score (0-100)
    - Eligibility score
    - Relevance explanation
    - Eligibility assessment with criterion-level detail

The matching process can take 2-5 minutes depending on the number of candidate trials found. During processing, status updates are streamed through the WebSocket endpoint.

### WebSocket — Status Updates

```
GET /ws/status/{session_id}
```

A WebSocket endpoint that streams real-time progress updates for an active matching session. The client connects with the same `session_id` used in the `/match` request and receives JSON messages indicating the current pipeline stage:

- `generating_keywords` — Extracting conditions from the clinical note
- `generating_embedding` — Computing query embeddings
- `retrieving_trials` — Running hybrid search
- `matching_criteria` / `matching_trial` — Evaluating eligibility criteria for each candidate
- `ranking_trials` — Computing final scores
- `responding` — Preparing the response

Each message includes a human-readable description (e.g., "Matching trial 3 of 8") and a timestamp.

## OpenAPI Documentation

The API includes auto-generated OpenAPI documentation with interactive request/response examples. When the service is running, visit:

- **Swagger UI**: `{base_url}/docs`
- **ReDoc**: `{base_url}/redoc`
