# Clinical Aithena (GARDIAN) - AWS Architecture

## System Overview

Clinical Aithena (GARDIAN) is a clinical trial matching system that uses AI to match patients with relevant clinical trials. The system implements the TrialGPT pipeline with keyword generation, hybrid retrieval (BM25 + vector search), criterion-level matching, and intelligent ranking.

## AWS Services & Cost Summary

| Service | Purpose | Configuration | Monthly Cost |
|---------|---------|---------------|--------------|
| **Compute & Application** | | | |
| ECS Fargate (Frontend) | Web UI | 2 tasks @ 0.5 vCPU, 1 GB | $30-50 |
| ECS Fargate (Backend) | API + TrialGPT Pipeline | 2 tasks @ 2 vCPU, 4 GB | $120-150 |
| ECS Fargate (LiteLLM Proxy) | AI Gateway | 2 tasks @ 1 vCPU, 2 GB | $60 |
| ECS Scheduled Task | Trial Ingestion (Daily) | 4 vCPU, 8 GB, 30 min/day | $80-150 |
| Application Load Balancer | Traffic Distribution | Internet-facing ALB | $25-40 |
| **AI/ML Services** | | | |
| AWS Bedrock | LLM Reasoning (Claude 3.5 Sonnet) | Pay-per-token | $50-200 |
| SageMaker Serverless | MedCPT Embeddings (2 models) | Pay-per-inference | $20-60 |
| **Data & Storage** | | | |
| RDS PostgreSQL | Database + pgvector | db.r6g.xlarge, Multi-AZ, 100 GB | $300-400 |
| S3 | Model artifacts, backups, raw data | Standard storage | $10-30 |
| **Networking** | | | |
| NAT Gateway | Outbound internet access | Single gateway, ~100 GB/mo | $35-50 |
| **Automation & Monitoring** | | | |
| EventBridge Scheduler | Daily cron trigger | Single schedule | $0-1 |
| CloudWatch | Logs, metrics, dashboards | Standard monitoring | $10-30 |
| SNS | Notifications & alerts | Email/SMS notifications | $0-1 |
| **Security & Registry** | | | |
| Secrets Manager | Credentials storage | ~10 secrets | $2-5 |
| ECR | Container registry | 3-4 images | $5-10 |
| **Total Estimated Cost** | | | **$747-1,177/month** |

**Cost Breakdown by Category:**
- **Compute & Application:** $315-350/month (42-47%)
- **Data & Storage:** $310-430/month (41-37%)
- **AI/ML Services:** $70-260/month (9-22%)
- **Networking & Other:** $52-137/month (7-12%)

**Notes:**
- Bedrock and SageMaker are usage-based; costs vary with query volume
- Development/staging environments would be additional
- Data transfer costs not included (typically $20-50/month additional)
- Costs can be reduced by ~30% using single-AZ RDS for non-production
- See [Cost Estimate (Monthly)](#cost-estimate-monthly) section below for detailed breakdown

## High-Level Architecture

```mermaid
graph TB
    subgraph "User Layer"
        USER[End Users]
    end

    subgraph "AWS Cloud"
        subgraph "Application Layer - ECS Fargate"
            ALB[Application Load Balancer]
            FE[Frontend Container<br/>Next.js]
            BE[Backend Container<br/>FastAPI + TrialGPT Pipeline]
            LITE[LiteLLM Proxy<br/>API Gateway]
        end

        subgraph "Batch Processing"
            EB[EventBridge Scheduler<br/>Daily Cron]
            INGEST[ECS Scheduled Task<br/>Trial Ingestion Job]
        end

        subgraph "AI/ML Services"
            BEDROCK[AWS Bedrock<br/>Claude 3.5 Sonnet<br/>LLM Reasoning]
            SAGE[SageMaker Serverless<br/>MedCPT Article Encoder<br/>MedCPT Query Encoder]
        end

        subgraph "Data Layer"
            RDS[(RDS PostgreSQL<br/>pgvector Extension<br/>Clinical Trial Data)]
            S3[S3 Bucket<br/>Model Artifacts<br/>Backups]
        end

        subgraph "External Data"
            CTGOV[ClinicalTrials.gov API]
        end

        subgraph "Supporting Services"
            SECRETS[AWS Secrets Manager<br/>API Keys & Credentials]
            CW[CloudWatch<br/>Logs & Metrics]
            ECR[ECR<br/>Container Registry]
        end
    end

    USER --> ALB
    ALB --> FE
    FE --> BE
    BE --> LITE
    BE --> RDS
    
    EB -->|Trigger Daily| INGEST
    INGEST --> CTGOV
    INGEST --> LITE
    LITE --> BEDROCK
    LITE --> SAGE
    INGEST --> RDS
    INGEST --> S3
    
    SAGE --> S3
    BE --> SECRETS
    INGEST --> SECRETS
    BE --> CW
    FE --> CW
    LITE --> CW
    INGEST --> CW
    ECR -.-> FE
    ECR -.-> BE
    ECR -.-> LITE
    ECR -.-> INGEST

    style BEDROCK fill:#FF9900
    style SAGE fill:#FF9900
    style RDS fill:#3B48CC
    style S3 fill:#569A31
    style ALB fill:#FF9900
    style FE fill:#4A90E2
    style BE fill:#4A90E2
    style LITE fill:#4A90E2
    style INGEST fill:#9B59B6
    style EB fill:#FF9900
    style CTGOV fill:#E74C3C
```

## Component Details

### 1. Frontend (Next.js Application)

**AWS Service:** Amazon ECS Fargate

**Configuration:**
- **Service:** Fargate service with auto-scaling (2-10 tasks)
- **Task Definition:**
  - CPU: 0.5 vCPU
  - Memory: 1 GB
  - Container: `clinical-aithena-frontend:latest`
- **Port:** 3000
- **Health Check:** `/health` endpoint

**Features:**
- Modern UI for clinical trial search
- Patient query interface
- Trial results visualization
- Real-time search with pagination

**Estimated Cost:** ~$30-50/month (2 tasks @ 0.5 vCPU)

---

### 2. Backend API (FastAPI + TrialGPT Pipeline)

**AWS Service:** Amazon ECS Fargate

**Configuration:**
- **Service:** Fargate service with auto-scaling (2-20 tasks)
- **Task Definition:**
  - CPU: 2 vCPU
  - Memory: 4 GB
  - Container: `clinical-aithena-backend:latest`
- **Port:** 8000
- **Health Check:** `/health` endpoint

**Responsibilities:**
- RESTful API endpoints
- TrialGPT pipeline orchestration:
  - Keyword generation
  - Hybrid retrieval (BM25 + vector)
  - Criterion-level matching
  - Trial ranking
- Database operations
- LLM/embedding service coordination

**Estimated Cost:** ~$120-150/month (2 tasks @ 2 vCPU)

---

### 3. Trial Ingestion Cron Job

**AWS Service:** Amazon ECS Scheduled Task (Fargate) + EventBridge Scheduler

**Configuration:**
- **Schedule:** Daily at 2:00 AM UTC (cron: `0 2 * * ? *`)
- **Task Definition:**
  - CPU: 4 vCPU (for parallel embedding generation)
  - Memory: 8 GB
  - Container: `clinical-aithena-backend:latest` (reuses backend image)
  - Command override: `["uv", "run", "ct-aithena", "ingest", "--incremental"]`
- **Timeout:** 2 hours
- **Retry:** Up to 3 retries with exponential backoff

**Responsibilities:**
- Fetch updates from ClinicalTrials.gov API
  - New trials (recently posted)
  - Updated trials (status changes, amendments)
  - Uses `last_update_posted` field for incremental sync
- Transform data to TrialGPT format
- Generate embeddings for new/updated trials (batch processing)
  - Title embeddings (768-dim)
  - Full text embeddings (768-dim)
  - Uses SageMaker Serverless via LiteLLM
- Update database (upsert operations)
- Archive raw data to S3 for audit trail
- Send completion notification (SNS topic)

**Execution Flow:**
```python
# Pseudocode for ingestion job
async def run_ingestion():
    # 1. Fetch last sync timestamp from DB
    last_sync = get_last_sync_time()
    
    # 2. Query ClinicalTrials.gov API
    trials = fetch_updated_trials(since=last_sync)
    logger.info(f"Found {len(trials)} updated trials")
    
    # 3. Transform to TrialGPT format
    transformed = [transform_trial(t) for t in trials]
    
    # 4. Generate embeddings in batches
    batch_size = 100
    for batch in chunks(transformed, batch_size):
        embeddings = await medcpt_service.encode_articles_batch(
            [t.title for t in batch],
            [t.text for t in batch]
        )
        for trial, emb in zip(batch, embeddings):
            trial.title_embedding = emb.title
            trial.text_embedding = emb.text
    
    # 5. Upsert to database
    db.bulk_upsert(transformed)
    
    # 6. Archive raw data to S3
    s3.put_object(
        Bucket="clinical-aithena-data",
        Key=f"raw-trials/{date}/{timestamp}.json",
        Body=json.dumps(trials)
    )
    
    # 7. Update sync timestamp
    update_last_sync_time(datetime.utcnow())
    
    # 8. Send notification
    sns.publish(
        TopicArn="arn:aws:sns:...:trial-ingestion",
        Message=f"Ingestion complete: {len(trials)} trials updated"
    )
```

**Performance Considerations:**
- **Incremental Sync:** Only fetch trials updated since last run
  - Average: ~500-1,000 trials/day updated
  - Full refresh: ~450,000 trials (quarterly)
- **Batch Embedding Generation:** 100 trials/batch
  - Reduces SageMaker cold starts
  - ~5-10 batches for daily incremental sync
- **Parallel Processing:** Process multiple batches concurrently
- **Execution Time:** 15-30 minutes for daily incremental sync

**Monitoring:**
- CloudWatch Logs for execution traces
- Custom metrics for trials processed, errors
- SNS alerts on failure or prolonged execution
- Dashboard showing:
  - Last successful sync time
  - Trials processed per run
  - Embedding generation latency
  - Database write performance

**Error Handling:**
- Transient errors: Automatic retry (up to 3 times)
- Partial failures: Continue processing remaining batches
- Dead letter queue for failed trial records
- Manual intervention triggers via SNS notification

**Cost Considerations:**
- **ECS Task:** ~$0.50-1.00 per run (30 minutes @ 4 vCPU)
- **SageMaker Embeddings:** ~$2-5 per run (1,000 trials × 2 encodings)
- **ClinicalTrials.gov API:** Free (rate-limited)
- **S3 Storage:** ~$1-2/month for raw data archives

**Monthly Estimated Cost:** ~$80-150/month
- Daily runs: 30 × ($0.75 + $3.50) = ~$127.50
- S3 storage: ~$1-2

**CLI Commands:**

The backend container includes a CLI for manual operations:

```bash
# Incremental sync (fetch only updated trials since last run)
uv run ct-aithena ingest --incremental

# Full refresh (re-import all trials - use sparingly)
uv run ct-aithena ingest --full

# Dry run (test without writing to database)
uv run ct-aithena ingest --incremental --dry-run

# Import specific NCT IDs
uv run ct-aithena ingest --nct-ids NCT00000001,NCT00000002

# Generate embeddings for existing trials (if missing)
uv run ct-aithena embed --resume
```

**Manual Trigger:**

To manually trigger the scheduled task (for testing or recovery):

```bash
aws ecs run-task \
  --cluster clinical-aithena-cluster \
  --task-definition clinical-aithena-ingestion:latest \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
```

**Alternative: AWS Batch**
For even longer-running jobs (e.g., full refresh), consider AWS Batch:
- Better cost optimization for long jobs
- Automatic spot instance usage
- More flexible compute allocation

---

### 4. LiteLLM Proxy (API Gateway)

**AWS Service:** Amazon ECS Fargate

**Configuration:**
- **Service:** Fargate service (2 tasks for HA)
- **Task Definition:**
  - CPU: 1 vCPU
  - Memory: 2 GB
  - Container: `litellm/litellm:latest`
- **Port:** 4000

**Purpose:**
- Unified OpenAI-compatible API gateway
- Routes requests to appropriate AI services
- Built-in retry logic, fallbacks, and caching
- Request/response logging and monitoring

**Configuration File (config.yaml):**
```yaml
model_list:
  # Bedrock LLM for reasoning tasks
  - model_name: claude-3-sonnet
    litellm_params:
      model: bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0
      aws_region_name: us-east-1
      
  # SageMaker MedCPT embeddings
  - model_name: medcpt-article
    litellm_params:
      model: sagemaker/medcpt-article-encoder
      aws_region_name: us-east-1
      
  - model_name: medcpt-query
    litellm_params:
      model: sagemaker/medcpt-query-encoder
      aws_region_name: us-east-1
```

**IAM Role Requirements:**
- `bedrock:InvokeModel` permission
- `sagemaker:InvokeEndpoint` permission

**Estimated Cost:** ~$60/month (2 tasks @ 1 vCPU)

---

### 5. AWS Bedrock (LLM Reasoning)

**Model:** Claude 3.5 Sonnet v2

**Use Cases:**
- **Keyword Generation:** Extract search conditions from patient notes
- **Criterion Matching:** Evaluate patient eligibility for each inclusion/exclusion criterion
- **Trial Ranking:** Aggregate criterion-level predictions into relevance and eligibility scores

**Pricing (Claude 3.5 Sonnet v2):**
- Input: $3 per million tokens
- Output: $15 per million tokens

**Configuration:**
- Model ID: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- Region: `us-east-1`
- Max tokens: 4096 (configurable)
- Temperature: 0.0 (deterministic for medical reasoning)

**Estimated Cost:** $50-200/month (depends on query volume)

**Note:** Bedrock doesn't currently support OpenAI's GPT models. If you specifically need GPT-4 Turbo, you would need to:
- Use OpenAI API directly through LiteLLM
- OR use Amazon Titan or other Bedrock models
- Claude 3.5 Sonnet is recommended as it performs exceptionally well on medical/reasoning tasks

---

### 6. AWS SageMaker Serverless (MedCPT Embeddings)

**Models:**
- **MedCPT Article Encoder:** Encodes clinical trials (title + text) → 768-dim vectors
- **MedCPT Query Encoder:** Encodes patient queries/keywords → 768-dim vectors

**Configuration:**
```python
# Article Encoder
serverless_inference_config = {
    "MemorySizeInMB": 4096,      # 4 GB
    "MaxConcurrency": 20,         # Max parallel requests
}

# Query Encoder (lighter load)
serverless_inference_config = {
    "MemorySizeInMB": 4096,
    "MaxConcurrency": 10,
}
```

**Pricing:**
- Compute: $0.000133 per second
- Memory: $0.00000667 per GB-second
- No charges when idle

**Cold Start Mitigation:**
- Periodic warmup Lambda (every 10 minutes)
- Provisioned concurrency for peak hours (optional)

**Estimated Cost:** $20-60/month (depends on embedding volume)

---

### 7. Amazon RDS for PostgreSQL (Database)

**Service:** Amazon RDS PostgreSQL with pgvector Extension

**Configuration:**
- **Instance Class:** db.r6g.xlarge (4 vCPU, 32 GB RAM)
  - Good for vector operations
  - ARM-based (Graviton2) for cost efficiency
- **Storage:** 100 GB GP3 SSD with auto-scaling to 200 GB
- **Multi-AZ:** Yes (for high availability)
- **Backup:** Automated daily backups, 7-day retention
- **PostgreSQL Version:** 15.x or higher
- **Extensions:**
  - `pgvector` (for vector similarity search)
  - `pg_trgm` (for full-text search/BM25)

**Database Schema:**
- `trialgpt_study` - Clinical trial data with embeddings
- `patient` - Patient information
- `patient_keywords` - Cached keyword generation results
- `matching_result` - Criterion-level matching predictions
- `trial_ranking` - Aggregated relevance/eligibility scores
- `pipeline_job` - Pipeline execution state tracking

**Performance Optimizations:**
- HNSW indexes for vector similarity search
- GIN indexes for full-text search
- B-tree indexes for common queries
- Connection pooling via pgBouncer (optional)

**Estimated Cost:** ~$300-400/month

**Note:** RDS fully supports pgvector extension. Enable it with:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

### 8. Amazon S3 (Object Storage)

**Buckets:**

**1. Model Artifacts Bucket:**
- MedCPT model weights (for SageMaker deployment)
- Model serving scripts
- Versioning enabled

**2. Data Bucket:**
- ClinicalTrials.gov data exports
- Processed trial datasets
- Backup exports from RDS

**3. Logs Bucket (optional):**
- Application logs archival
- CloudWatch Logs exports

**Lifecycle Policies:**
- Transition old logs to Glacier after 90 days
- Delete logs after 1 year

**Estimated Cost:** ~$10-30/month

---

### 9. Application Load Balancer (ALB)

**Configuration:**
- **Type:** Application Load Balancer
- **Scheme:** Internet-facing
- **Listeners:**
  - Port 443 (HTTPS) → Frontend + Backend
  - Port 80 (HTTP) → Redirect to 443
- **Target Groups:**
  - Frontend: Port 3000
  - Backend: Port 8000
- **Health Checks:** Enabled for both services
- **SSL/TLS:** AWS Certificate Manager (ACM) certificate

**Path Routing:**
- `/` → Frontend
- `/api/*` → Backend
- `/docs` → Backend API documentation

**Estimated Cost:** ~$25-40/month

---

### 10. Supporting AWS Services

#### AWS Secrets Manager
- Store database credentials
- Store API keys (LiteLLM, OpenAI fallback)
- Automatic rotation for RDS credentials
- **Cost:** ~$2-5/month

#### Amazon CloudWatch
- Application logs from all containers
- Metrics and dashboards
- Alarms for error rates, latency, costs
- **Cost:** ~$10-30/month (depends on log volume)

#### Amazon ECR (Elastic Container Registry)
- Private Docker registry for containers
- Stores: Frontend, Backend, LiteLLM images
- Image scanning for vulnerabilities
- **Cost:** ~$5-10/month

#### AWS IAM
- Task execution roles for ECS
- Service roles for Bedrock/SageMaker access
- Cross-service authentication

#### Amazon EventBridge (CloudWatch Events)
- Schedule trial ingestion job (daily cron)
- Cron expression: `cron(0 2 * * ? *)` (2 AM UTC daily)
- Target: ECS Scheduled Task
- **Cost:** ~$0-1/month (minimal for single schedule)

#### Amazon SNS (Simple Notification Service)
- Trial ingestion status notifications
- System alerts and alarms
- Email/SMS subscriptions for ops team
- Topics:
  - `trial-ingestion-success` - Daily completion notifications
  - `trial-ingestion-failure` - Alert on job failures
  - `system-alarms` - Critical system alerts
- **Cost:** ~$0-1/month (low volume)

---

## Data Flow

### 1. Patient Query Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant LiteLLM
    participant Bedrock
    participant SageMaker
    participant RDS

    User->>Frontend: Enter patient description
    Frontend->>Backend: POST /api/search
    
    Backend->>LiteLLM: Generate keywords (LLM)
    LiteLLM->>Bedrock: Claude 3.5 Sonnet request
    Bedrock-->>LiteLLM: Keywords + summary
    LiteLLM-->>Backend: Structured keywords
    
    Backend->>LiteLLM: Encode queries (embeddings)
    LiteLLM->>SageMaker: MedCPT Query Encoder
    SageMaker-->>LiteLLM: 768-dim vectors
    LiteLLM-->>Backend: Query embeddings
    
    Backend->>RDS: Hybrid search (BM25 + vector)
    RDS-->>Backend: Top-K candidate trials
    
    loop For each candidate trial
        Backend->>LiteLLM: Match patient to trial
        LiteLLM->>Bedrock: Claude criterion matching
        Bedrock-->>LiteLLM: Criterion predictions
        LiteLLM-->>Backend: Matching results
    end
    
    Backend->>LiteLLM: Rank matched trials
    LiteLLM->>Bedrock: Claude aggregation
    Bedrock-->>LiteLLM: Relevance + eligibility scores
    LiteLLM-->>Backend: Rankings
    
    Backend->>RDS: Store results
    Backend-->>Frontend: Ranked trial list
    Frontend-->>User: Display results
```

### 2. Trial Ingestion Flow (Scheduled Cron Job)

```mermaid
sequenceDiagram
    participant EB[EventBridge Scheduler]
    participant INGEST[ECS Scheduled Task]
    participant CTGov[ClinicalTrials.gov API]
    participant LiteLLM
    participant SageMaker
    participant RDS
    participant S3
    participant SNS[SNS Topic]

    Note over EB: Daily at 2:00 AM UTC
    EB->>INGEST: Trigger scheduled task
    
    INGEST->>RDS: Get last sync timestamp
    RDS-->>INGEST: last_sync = "2026-01-12"
    
    INGEST->>CTGov: Fetch trials updated since last_sync
    CTGov-->>INGEST: ~1,000 updated trials (JSON)
    
    INGEST->>INGEST: Transform to TrialGPT format
    
    loop For each batch (100 trials)
        INGEST->>LiteLLM: Generate embeddings (batch)
        LiteLLM->>SageMaker: MedCPT Article Encoder
        SageMaker-->>LiteLLM: 768-dim vectors (title + text)
        LiteLLM-->>INGEST: Embeddings
    end
    
    INGEST->>RDS: Bulk upsert trials + embeddings
    RDS-->>INGEST: Success
    
    INGEST->>RDS: Update last_sync = "2026-01-13"
    
    INGEST->>S3: Archive raw trial data
    S3-->>INGEST: Stored
    
    INGEST->>SNS: Send completion notification
    SNS-->>INGEST: Published
    
    Note over INGEST: Task completes (30 min)
```

---

## Network Architecture

```mermaid
graph TB
    subgraph "Public Subnets - us-east-1a/1b"
        ALB[Application Load Balancer]
        NAT[NAT Gateway]
    end
    
    subgraph "Private Subnets - us-east-1a/1b"
        FE[Frontend Tasks]
        BE[Backend Tasks]
        LITE[LiteLLM Tasks]
    end
    
    subgraph "Database Subnets - us-east-1a/1b"
        RDS[(RDS PostgreSQL)]
    end
    
    INTERNET((Internet)) --> ALB
    ALB --> FE
    ALB --> BE
    FE --> BE
    BE --> LITE
    BE --> RDS
    
    FE --> NAT
    BE --> NAT
    LITE --> NAT
    NAT --> INTERNET
    
    LITE --> BEDROCK[AWS Bedrock]
    LITE --> SAGE[SageMaker]
    
    style BEDROCK fill:#FF9900
    style SAGE fill:#FF9900
```

**VPC Configuration:**
- **CIDR:** 10.0.0.0/16
- **Public Subnets:** 10.0.1.0/24, 10.0.2.0/24 (2 AZs)
- **Private Subnets:** 10.0.10.0/24, 10.0.11.0/24 (2 AZs)
- **Database Subnets:** 10.0.20.0/24, 10.0.21.0/24 (2 AZs)

**Security Groups:**
- **ALB Security Group:** Allow 80, 443 from 0.0.0.0/0
- **Frontend Security Group:** Allow 3000 from ALB
- **Backend Security Group:** Allow 8000 from ALB and Frontend
- **LiteLLM Security Group:** Allow 4000 from Backend
- **RDS Security Group:** Allow 5432 from Backend only

---

## Deployment Strategy

### Infrastructure as Code

**Recommended Tool:** AWS CDK (Python) or Terraform

**Key Resources:**
1. **VPC and Networking**
   - VPC, subnets, route tables, NAT Gateway, Internet Gateway
   - Security groups

2. **ECS Cluster and Services**
   - Fargate cluster
   - Task definitions for Frontend, Backend, LiteLLM, Trial Ingestion
   - ECS services with auto-scaling policies

3. **Scheduled Tasks**
   - EventBridge Scheduler rule (cron expression)
   - ECS task definition for trial ingestion
   - IAM role for scheduled task execution

4. **Database**
   - RDS PostgreSQL instance with pgvector
   - Database security group
   - Secrets Manager integration

5. **AI/ML Services**
   - SageMaker serverless endpoints (deploy via Python SDK)
   - Bedrock access (no provisioning needed)

6. **Load Balancer**
   - ALB with target groups and listeners
   - ACM certificate for HTTPS

7. **Monitoring and Alerts**
   - CloudWatch log groups
   - CloudWatch alarms
   - SNS topics for alerts (ingestion failures, system health)

### CI/CD Pipeline

**Recommended:** AWS CodePipeline + CodeBuild

**Pipeline Stages:**
1. **Source:** GitHub repository
2. **Build:** 
   - Build Docker images for Frontend, Backend
   - Run tests
   - Push images to ECR
3. **Deploy:**
   - Update ECS task definitions
   - Rolling deployment to Fargate services
   - Health check validation

**Alternative:** GitHub Actions with AWS credentials

---

## Cost Estimate (Monthly)

| Component | Service | Configuration | Est. Cost |
|-----------|---------|---------------|-----------|
| Frontend | ECS Fargate | 2 tasks @ 0.5 vCPU, 1 GB | $30-50 |
| Backend | ECS Fargate | 2 tasks @ 2 vCPU, 4 GB | $120-150 |
| Trial Ingestion | ECS Scheduled Task | Daily @ 4 vCPU, 8 GB (30 min) | $80-150 |
| LiteLLM Proxy | ECS Fargate | 2 tasks @ 1 vCPU, 2 GB | $60 |
| Database | RDS PostgreSQL | db.r6g.xlarge, Multi-AZ | $300-400 |
| AI - LLM | AWS Bedrock | Claude 3.5 Sonnet (pay per use) | $50-200 |
| AI - Embeddings | SageMaker Serverless | MedCPT models (pay per use) | $20-60 |
| Load Balancer | ALB | Application Load Balancer | $25-40 |
| Storage | S3 | Model artifacts, backups, raw data | $10-30 |
| Networking | NAT Gateway | 1 gateway, ~100 GB transfer | $35-50 |
| Monitoring | CloudWatch | Logs and metrics | $10-30 |
| Secrets | Secrets Manager | ~10 secrets | $2-5 |
| Container Registry | ECR | 3 container images | $5-10 |
| Scheduler | EventBridge | Daily schedule trigger | $0-1 |
| Notifications | SNS | Ingestion status alerts | $0-1 |
| **TOTAL** | | | **$747-1,177/month** |

**Notes:**
- Bedrock and SageMaker costs are usage-based and will vary
- Data transfer costs not included (typically $20-50/month)
- Development/testing environments would be additional
- Can reduce costs by using smaller RDS instance or single-AZ during development

---

## Scaling Considerations

### Horizontal Scaling (Auto-scaling)

**ECS Services:**
- **Metric:** CPU/Memory utilization or request count
- **Target:** 70% CPU utilization
- **Scale-out:** Add tasks when load increases
- **Scale-in:** Remove tasks when load decreases

**Example Auto-scaling Policy:**
```python
# Backend service scaling
target_cpu_utilization = 70
min_tasks = 2
max_tasks = 20
scale_out_cooldown = 60  # seconds
scale_in_cooldown = 300  # seconds
```

### Database Scaling

**Read Scaling:**
- Add RDS read replicas for read-heavy workloads
- Direct read-only queries to replicas

**Vertical Scaling:**
- Start with db.r6g.xlarge
- Can upgrade to db.r6g.2xlarge or larger if needed
- Minimal downtime with Multi-AZ

### AI Service Scaling

**Bedrock:**
- Automatically scales (managed service)
- Request throttling limits (10-50 TPS by default)
- Can request limit increases

**SageMaker Serverless:**
- Auto-scales from 0 to MaxConcurrency
- Increase MaxConcurrency if needed
- Consider provisioned concurrency for consistent latency

---

## High Availability & Disaster Recovery

### High Availability

**Multi-AZ Deployment:**
- ECS tasks distributed across 2+ availability zones
- RDS Multi-AZ with automatic failover
- ALB distributes traffic across healthy targets

**Health Checks:**
- ECS service health checks on `/health` endpoint
- ALB target health checks with automatic deregistration
- CloudWatch alarms for service failures

**Failover Times:**
- ECS task replacement: ~60-90 seconds
- RDS Multi-AZ failover: ~60-120 seconds
- ALB automatic target failover: ~30 seconds

### Disaster Recovery

**Backup Strategy:**
- **Database:** Automated daily snapshots, 7-day retention
- **Models:** S3 versioning enabled for all artifacts
- **Configuration:** Infrastructure as Code in Git

**Recovery Time Objective (RTO):** ~2-4 hours
**Recovery Point Objective (RPO):** ~24 hours (daily backups)

**Recovery Procedures:**
1. Restore RDS from latest snapshot
2. Redeploy ECS services from latest images
3. Validate data integrity and service health

---

## Security Best Practices

### Network Security
- Private subnets for all application containers
- Database in isolated database subnets
- Security groups with least-privilege access
- NAT Gateway for outbound internet access only

### Data Encryption
- **At Rest:**
  - RDS encryption enabled (AWS KMS)
  - S3 bucket encryption enabled
  - EBS volumes encrypted
- **In Transit:**
  - HTTPS/TLS for all external connections
  - SSL/TLS for RDS connections
  - VPC internal traffic (already isolated)

### Access Control
- IAM roles for all services (no hardcoded credentials)
- Secrets Manager for sensitive configuration
- Task execution roles with minimal permissions
- CloudTrail for audit logging

### Compliance Considerations
- **HIPAA:** RDS can be HIPAA-compliant with BAA
- **PHI Data:** Encrypt all PHI data at rest and in transit
- **Audit Logging:** CloudTrail + CloudWatch Logs
- **Access Controls:** IAM policies and MFA for admin access

---

## Monitoring & Observability

### CloudWatch Dashboards

**Key Metrics to Monitor:**

**Application Metrics:**
- Request rate, latency (p50, p95, p99)
- Error rates (4xx, 5xx)
- ECS task CPU/Memory utilization
- Pipeline job status and duration

**Trial Ingestion Metrics:**
- Last successful ingestion time
- Trials processed per run (new, updated, failed)
- Ingestion job duration
- Embedding generation latency per batch
- ClinicalTrials.gov API response time
- Database write performance (trials/second)

**Database Metrics:**
- RDS CPU/Memory/Storage utilization
- Connection count
- Query performance (slow query log)
- Replication lag (if using read replicas)

**AI Service Metrics:**
- Bedrock request count, latency, errors
- SageMaker invocation count, latency, cold starts
- Token usage and costs

**Infrastructure Metrics:**
- ALB request count, target health
- NAT Gateway data transfer
- VPC flow logs for network analysis

### Alarms

**Critical Alarms:**
- RDS CPU > 80% for 5 minutes
- Backend error rate > 5% for 2 minutes
- Pipeline job failures
- **Trial ingestion job failure** (no successful run in 36 hours)
- **Trial ingestion timeout** (execution > 2 hours)
- SageMaker cold start duration > 30 seconds
- Database connection exhaustion

**Warning Alarms:**
- RDS storage < 20% free
- ECS task count at max for 10 minutes
- Bedrock throttling errors
- High request latency (p95 > 2 seconds)

### Logging Strategy

**Log Aggregation:**
- All ECS container logs → CloudWatch Logs
- Structured JSON logging for parsing
- Separate log groups per service

**Log Retention:**
- Application logs: 30 days
- Security/audit logs: 1 year
- Archive to S3 Glacier for long-term retention

---

## Development Workflow

### Local Development

**Docker Compose:**
- Run PostgreSQL + pgvector locally
- Run Frontend, Backend, LiteLLM containers
- Point to AWS Bedrock/SageMaker or use OpenAI for testing

**Environment Files:**
```bash
# .env.local
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/clinical_aithena
LITELLM_API_BASE=http://localhost:4000
LLM_MODEL=claude-3-sonnet
MEDCPT_ARTICLE_MODEL=medcpt-article
MEDCPT_QUERY_MODEL=medcpt-query
```

**Local Trial Ingestion:**
```bash
# Run ingestion locally for testing (small subset)
uv run ct-aithena ingest --nct-ids NCT00000001,NCT00000002 --dry-run

# Or use a small incremental sync
uv run ct-aithena ingest --incremental
```

### Testing Strategy

**Unit Tests:**
- Python pytest for backend logic
- Mock LLM/embedding responses
- Test database operations with in-memory SQLite

**Integration Tests:**
- Test full pipeline with real AWS services
- Use test database instance
- Validate end-to-end flows

**Performance Tests:**
- Load testing with locust or k6
- Test auto-scaling behavior
- Measure SageMaker cold start times

### Deployment Environments

**Development:**
- Single-AZ RDS (smaller instance)
- 1 task per service
- Use OpenAI or smaller models for cost savings

**Staging:**
- Multi-AZ RDS
- Production-like configuration
- Lower task counts

**Production:**
- Full HA configuration as described above
- Auto-scaling enabled
- Enhanced monitoring and alarms

---

## Migration Path from Current Setup

### Phase 1: Infrastructure Setup (Week 1-2)
1. Set up VPC, subnets, security groups
2. Deploy RDS PostgreSQL with pgvector
3. Migrate database schema and data
4. Set up S3 buckets for models/backups

### Phase 2: AI Services (Week 2-3)
1. Deploy MedCPT models to SageMaker Serverless
2. Configure AWS Bedrock access (Claude 3.5)
3. Set up LiteLLM proxy with AWS configuration
4. Test embedding and LLM endpoints

### Phase 3: Application Deployment (Week 3-4)
1. Build and push Docker images to ECR
2. Create ECS cluster and task definitions
3. Deploy Backend and Frontend services
4. Configure ALB with health checks
5. Set up EventBridge schedule for trial ingestion
6. Test ingestion job (manual trigger first)

### Phase 4: Testing & Optimization (Week 4-5)
1. Run integration tests
2. Performance testing and tuning
3. Configure auto-scaling policies
4. Set up monitoring and alarms

### Phase 5: Production Cutover (Week 5-6)
1. DNS cutover to ALB
2. Monitor for issues
3. Optimize costs and performance
4. Documentation and runbooks

---

## Operations & Maintenance

### Routine Operations

**Daily:**
- Check trial ingestion job status (automated via SNS notifications)
- Verify trials are being updated in database

**Weekly:**
- Review CloudWatch dashboards
- Check cost anomalies
- Review security group rules
- Verify trial data freshness (no stale data)

**Monthly:**
- Review and optimize RDS performance
- Analyze Bedrock/SageMaker usage patterns
- Update dependencies and security patches
- Review and adjust auto-scaling policies

**Quarterly:**
- Disaster recovery testing
- Cost optimization review
- Security audit
- Capacity planning

### Troubleshooting Guide

**Common Issues:**

1. **Trial Ingestion Job Failure**
   - Check CloudWatch Logs for error messages
   - Common causes:
     - ClinicalTrials.gov API timeout or rate limiting
     - Database connection issues
     - SageMaker endpoint not responding
   - Solution: Review logs, retry manually if transient error
   - Check SNS notifications for failure details

2. **Stale Trial Data**
   - Symptom: Last sync time > 36 hours ago
   - Check EventBridge schedule is enabled
   - Check ECS task execution role has proper permissions
   - Manually trigger task to test

3. **Slow Embedding Generation**
   - Check SageMaker cold start times
   - Solution: Reduce batch size or increase concurrency
   - Consider enabling provisioned concurrency for peak times

4. **SageMaker Cold Starts**
   - Solution: Implement warmup Lambda
   - Alternative: Enable provisioned concurrency

5. **RDS Connection Exhaustion**
   - Solution: Implement connection pooling (pgBouncer)
   - Check for connection leaks in application code

6. **Bedrock Throttling**
   - Solution: Implement exponential backoff
   - Request limit increase from AWS

7. **High Costs**
   - Check Bedrock token usage
   - Review RDS instance size
   - Optimize SageMaker invocations
   - Review trial ingestion frequency (daily vs weekly)

---

## Future Enhancements

### Short-term (3-6 months)
- Add patient data upload interface
- Implement result caching in ElastiCache
- Add user authentication (Cognito)
- Create admin dashboard for trial management
- Optimize trial ingestion with change detection (only re-embed modified fields)
- Add webhook for real-time ClinicalTrials.gov updates (instead of polling)

### Medium-term (6-12 months)
- Multi-region deployment for lower latency
- Advanced analytics and reporting
- Batch processing for large patient cohorts
- Integration with EHR systems

### Long-term (12+ months)
- Real-time trial matching notifications
- Mobile application (iOS/Android)
- Multi-language support
- Federated learning for privacy-preserving matching

---

## References

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS SageMaker Serverless](https://docs.aws.amazon.com/sagemaker/latest/dg/serverless-endpoints.html)
- [RDS PostgreSQL + pgvector](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Appendix.PostgreSQL.CommonDBATasks.Extensions.html)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [TrialGPT Paper](https://arxiv.org/abs/2305.11011)
- [MedCPT Repository](https://github.com/ncbi/MedCPT)

---

## Appendix: AWS Service Selection Rationale

### Why ECS Fargate?
- Serverless container orchestration (no EC2 management)
- Auto-scaling based on demand
- Pay only for resources used
- Easier than EKS for this use case

**Alternatives Considered:**
- **EKS (Kubernetes):** More complex, overkill for this scale
- **Lambda:** Not suitable for long-running API services
- **EC2:** Requires more operational overhead

### Why RDS vs Self-Managed PostgreSQL?
- Automated backups and patches
- Multi-AZ high availability
- Easy scaling (vertical and read replicas)
- Managed service reduces operational burden
- Full pgvector support

**Alternatives Considered:**
- **Aurora Serverless v2:** More expensive, pgvector support limited
- **Self-managed on EC2:** More operational overhead

### Why SageMaker Serverless vs Real-time?
- Pay only for inference time (not idle time)
- Auto-scales to zero when not in use
- Perfect for variable workload
- ~90% cost savings vs always-on endpoint

**Alternatives Considered:**
- **SageMaker Real-time:** Too expensive for variable workload
- **Lambda with containers:** Limited to 10 GB memory, 15-minute timeout

### Why Bedrock?
- No infrastructure management
- Pay per token (truly serverless)
- Access to latest Claude models
- Automatic scaling and availability

**Alternatives Considered:**
- **OpenAI API:** Works, but not AWS-native
- **Self-hosted LLM on EC2/SageMaker:** Too expensive and complex

### Why ECS Scheduled Tasks for Trial Ingestion?
- Can run for extended periods (hours vs 15-minute Lambda limit)
- Reuses the same container image as the backend
- No code duplication (same CLI commands)
- Better resource allocation for batch processing
- Can easily scale compute resources as needed

**Alternatives Considered:**
- **AWS Lambda:** 15-minute timeout not sufficient for large batches
- **Step Functions + Lambda:** More complex, harder to debug
- **AWS Batch:** Good option but adds another service to manage
- **Kubernetes CronJob:** Requires EKS, more operational overhead

---

**Document Version:** 1.0  
**Last Updated:** January 13, 2026  
**Author:** Clinical Aithena Team


