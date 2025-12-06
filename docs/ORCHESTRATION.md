# Prefect Orchestration Guide

## Overview

This biomedical GraphRAG pipeline uses **Prefect** for workflow orchestration to handle:

- ✅ **Rate-limited API calls** with adaptive backoff
- ✅ **Weekly incremental updates** of biomedical data
- ✅ **Circuit breaker pattern** for handling API failures
- ✅ **Automatic retries** with exponential backoff
- ✅ **Data consistency validation**
- ✅ **Comprehensive monitoring** and reporting

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Prefect Server (UI)                      │
│                  http://localhost:4200                      │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Prefect Worker Pool                      │
│                  (Process-based workers)                    │
└────────────────────────────┬────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐  ┌─────────────┐  ┌──────────────┐
    │   PubMed    │  │    Gene     │  │    Graph     │
    │ Collection  │  │ Collection  │  │   Updates    │
    │(Rate Limited)│  │(Rate Limited)│  │ (Neo4j +    │
    │             │  │             │  │  Qdrant)     │
    └─────────────┘  └─────────────┘  └──────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
# Install Prefect and dependencies
uv sync --all-groups

# Or install just orchestration group
uv sync --group orchestration
```

### 2. Start Prefect Server (Docker)

```bash
# Start Prefect server with PostgreSQL backend
make prefect-server-start

# Access Prefect UI at http://localhost:4200
```

### 3. Deploy Flows

```bash
# Deploy all flows with schedules
make prefect-deploy
```

### 4. Start Worker

```bash
# Option A: Start worker with Docker (recommended)
# Worker is already running in docker-compose

# Option B: Start worker locally
make prefect-worker-start
```

## Scheduled Flows

### Weekly Incremental Update

**Schedule**: Every Sunday at 2 AM UTC
**Flow**: `incremental_update`
**Purpose**: Collect recent papers and update stores incrementally

```python
# Configuration
search_terms = [
    "CRISPR gene editing",
    "cancer immunotherapy",
    "genome sequencing",
    "CAR-T cell therapy",
    "mRNA vaccine",
]
max_results_per_term = 50
batch_size = 50
```

### Monthly Full Rebuild

**Schedule**: 1st of month at 3 AM UTC
**Flow**: `full_rebuild`
**Purpose**: Complete refresh of all data stores

```python
# Configuration
max_results_per_term = 200  # More comprehensive
recreate_vector_collection = True  # Clean slate
incremental_graph_update = False  # Full rebuild
```

### Daily Consistency Check

**Schedule**: Every day at 1 AM UTC
**Flow**: `consistency_check`
**Purpose**: Validate data consistency across JSON, Neo4j, and Qdrant

## Manual Execution

### Run Incremental Update Now

```bash
# Via Makefile
make prefect-run-incremental

# Via CLI
uv run prefect deployment run \
  biomedical-graphrag-incremental-update/adhoc-incremental-update
```

### Run Full Rebuild Now

```bash
# Via Makefile
make prefect-run-rebuild

# Via CLI
uv run prefect deployment run \
  biomedical-graphrag-full-rebuild/adhoc-full-rebuild
```

### Test Rate Limiting

```bash
# Test with small dataset
make prefect-test-rate-limit
```

## Rate Limiting Configuration

The pipeline includes an **adaptive rate limiter** with circuit breaker pattern:

```python
RateLimitConfig(
    requests_per_second=3.0,      # Max 3 requests/second
    requests_per_minute=100,      # Max 100 requests/minute
    burst_size=10,                # Allow bursts up to 10
    retry_attempts=5,             # Retry failed requests 5 times
    base_delay=1.0,               # Start with 1s delay
    max_delay=60.0,               # Max 60s delay
    circuit_failure_threshold=5,  # Open circuit after 5 failures
    circuit_timeout=300.0,        # Reset circuit after 5 minutes
)
```

### Circuit Breaker States

1. **CLOSED** (Normal): All requests processed normally
2. **OPEN** (Failing): Rejects requests after threshold failures
3. **HALF_OPEN** (Testing): Allows limited requests to test recovery

## Monitoring

### Prefect UI

Access the Prefect UI at **http://localhost:4200**:

- View flow runs and task status
- Inspect logs and artifacts
- Monitor execution times
- View rate limiter statistics

### Artifacts Generated

Each flow run creates markdown artifacts with:

1. **PubMed Collection Report**
   - Papers collected
   - Rate limiter stats
   - Circuit breaker state

2. **Gene Collection Report**
   - Genes collected
   - API performance metrics

3. **Neo4j Update Report**
   - Papers/genes ingested
   - Relationships created
   - Update mode (incremental vs full)

4. **Qdrant Update Report**
   - Vectors upserted
   - Batch processing stats

5. **Consistency Validation Report**
   - Paper counts across all stores
   - Inconsistencies detected

6. **Pipeline Execution Summary**
   - Total duration
   - Success/failure status
   - All sub-task statistics

### Viewing Artifacts

```bash
# Via UI: http://localhost:4200/artifacts

# Via CLI
prefect artifact list --flow-run-id <run-id>
```

## Error Handling

### Automatic Retries

Tasks automatically retry on failure with exponential backoff:

```python
@task(
    retries=3,
    retry_delay_seconds=300,  # 5 minutes between retries
)
```

### Circuit Breaker

When API calls fail repeatedly:

1. After 5 consecutive failures → Circuit opens
2. Requests blocked for 5 minutes
3. Circuit enters HALF_OPEN state
4. 3 successful requests → Circuit closes
5. Any failure in HALF_OPEN → Circuit reopens

### Rate Limit Exceeded

When rate limits are hit:

1. Automatic delay until rate limit window resets
2. Exponential backoff with jitter
3. Logs warnings with retry information

## Configuration

### Environment Variables

Ensure `.env` file contains:

```bash
# OpenAI (for embeddings)
OPENAI__API_KEY=sk-...

# Neo4j
NEO4J__URI=bolt://localhost:7687
NEO4J__USERNAME=neo4j
NEO4J__PASSWORD=your_password

# Qdrant
QDRANT__URL=http://localhost:6333
QDRANT__API_KEY=your_key

# PubMed
PUBMED__EMAIL=your@email.com
PUBMED__API_KEY=optional_ncbi_key
```

### Customize Schedules

Edit `src/biomedical_graphrag/orchestration/deployments.py`:

```python
schedule=CronSchedule(
    cron="0 2 * * 0",  # Change schedule here
    timezone="UTC",
)
```

### Customize Search Terms

Edit deployment parameters:

```python
parameters={
    "search_terms": [
        "your custom term",
        "another term",
    ],
    "max_results_per_term": 50,
}
```

## Troubleshooting

### Worker Not Picking Up Jobs

```bash
# Check worker status
docker-compose -f docker-compose.prefect.yml logs prefect-worker

# Restart worker
docker-compose -f docker-compose.prefect.yml restart prefect-worker

# Or start local worker
make prefect-worker-start
```

### Rate Limit Errors Persist

1. Check circuit breaker state in logs
2. Increase delays in `RateLimitConfig`
3. Reduce `max_results_per_term`
4. Add NCBI API key for higher limits

### Data Inconsistencies

```bash
# Run manual validation
uv run python -c "
import asyncio
from biomedical_graphrag.orchestration.flows import consistency_check
asyncio.run(consistency_check())
"

# Check logs for specific mismatches
# Rerun incremental update if needed
make prefect-run-incremental
```

### Docker Issues

```bash
# View all logs
make prefect-server-logs

# Restart entire stack
make prefect-server-stop
make prefect-server-start

# Clean rebuild
docker-compose -f docker-compose.prefect.yml down -v
docker-compose -f docker-compose.prefect.yml up --build -d
```

## Production Deployment

### Prefect Cloud (Recommended)

For production, use Prefect Cloud instead of self-hosted:

1. Sign up at [https://www.prefect.io/cloud](https://www.prefect.io/cloud)

2. Set API key:
```bash
export PREFECT_API_KEY=your_cloud_api_key
export PREFECT_API_URL=https://api.prefect.cloud/api/accounts/[ACCOUNT]/workspaces/[WORKSPACE]
```

3. Deploy flows:
```bash
make prefect-deploy
```

### Kubernetes Deployment

For Kubernetes, use Prefect Kubernetes workers:

```bash
# Install Prefect Kubernetes
pip install prefect-kubernetes

# Create work pool
prefect work-pool create --type kubernetes biomedical-k8s-pool

# Deploy to cluster
kubectl apply -f k8s/prefect-worker.yaml
```

## Monitoring & Alerts

### Set Up Alerts

Configure notifications in Prefect UI:

1. Go to Settings → Notifications
2. Add notification for:
   - Flow run failures
   - Flow run late starts
   - Work queue health

3. Integrate with:
   - Slack
   - Email
   - PagerDuty
   - Webhook

### Metrics Export

Export metrics to Prometheus:

```python
# Add to flows.py
from prefect.events import emit_event

await emit_event(
    event="graphrag.pipeline.complete",
    resource={"prefect.flow-run.id": flow_run_id},
    payload=pipeline_stats,
)
```

## Best Practices

1. **Start Small**: Test with `max_results_per_term=10` first
2. **Monitor Circuit Breaker**: Watch for OPEN state in logs
3. **Validate Consistency**: Run daily validation checks
4. **Use Incremental Updates**: Reserve full rebuilds for monthly maintenance
5. **Set Up Alerts**: Get notified of failures immediately
6. **Review Artifacts**: Check execution summaries after each run
7. **Adjust Rate Limits**: Tune based on API response times
8. **Use NCBI API Key**: Get higher rate limits for PubMed

## Advanced Usage

### Custom Flows

Create custom flows for specific use cases:

```python
from prefect import flow
from biomedical_graphrag.orchestration.tasks import (
    collect_pubmed_data,
    update_neo4j_graph,
)

@flow(name="custom-crispr-update")
async def crispr_only_update():
    await collect_pubmed_data(
        search_terms=["CRISPR-Cas9", "gene editing"],
        max_results=100,
    )
    await update_neo4j_graph(incremental=True)
```

### Parallel Execution

Run multiple searches in parallel:

```python
from prefect import flow
from prefect.task_runners import ConcurrentTaskRunner

@flow(task_runner=ConcurrentTaskRunner())
async def parallel_collection():
    await collect_pubmed_data.submit(["CRISPR"])
    await collect_pubmed_data.submit(["immunotherapy"])
    await collect_pubmed_data.submit(["mRNA vaccine"])
```

## Support

- **Documentation**: Check main README.md
- **Issues**: GitHub Issues
- **Prefect Docs**: [https://docs.prefect.io](https://docs.prefect.io)
- **Logs**: `make prefect-server-logs`
