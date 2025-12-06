# Orchestration Quick Start

Get your biomedical GraphRAG pipeline running with Prefect in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- `.env` file configured with API keys
- Neo4j and Qdrant running (or configured externally)

## 1. Install Dependencies

```bash
uv sync --all-groups
```

## 2. Start Prefect Infrastructure

```bash
# Start Prefect server + PostgreSQL + Worker
make prefect-server-start
```

Wait ~30 seconds for services to start, then access Prefect UI:
**http://localhost:4200**

## 3. Deploy Workflows

```bash
# Deploy all flows with schedules
make prefect-deploy
```

You should see:
```
✅ Deployed: weekly-incremental-update
✅ Deployed: monthly-full-rebuild
✅ Deployed: daily-consistency-check
✅ Deployed: adhoc-incremental-update
✅ Deployed: adhoc-full-rebuild
```

## 4. Test the Pipeline

### Option A: Test Rate Limiting (Recommended First)

```bash
# Run with small dataset to test configuration
make prefect-test-rate-limit
```

This will:
- Fetch 10 CRISPR papers
- Test rate limiting
- Validate API connections
- Show circuit breaker status

### Option B: Run Full Incremental Update

```bash
# Trigger incremental update manually
make prefect-run-incremental
```

This will:
- Collect ~50 papers per search term
- Update Neo4j graph (incremental MERGE)
- Update Qdrant vectors
- Validate consistency

## 5. Monitor Execution

### Via Prefect UI

1. Open **http://localhost:4200**
2. Click **Flow Runs** in sidebar
3. Select your running flow
4. View:
   - Real-time logs
   - Task execution graph
   - Generated artifacts (reports)
   - Execution timeline

### Via Logs

```bash
# Follow all Prefect logs
make prefect-server-logs

# Or specific container
docker logs -f biomedical-prefect-worker
```

## 6. View Results

### Check Artifacts

In Prefect UI, navigate to:
**Flow Runs → [Your Run] → Artifacts**

You'll see:
- PubMed Collection Report
- Gene Collection Report
- Neo4j Update Report
- Qdrant Update Report
- Consistency Validation Report
- Pipeline Execution Summary

### Verify Data

```bash
# Check Neo4j
MATCH (p:Paper) RETURN count(p)

# Check Qdrant
curl http://localhost:6333/collections/biomedical_papers

# Check JSON files
ls -lh data/
```

## Scheduled Execution

The pipeline runs automatically:

- **Sunday 2 AM UTC**: Weekly incremental update
- **1st of month 3 AM UTC**: Monthly full rebuild
- **Daily 1 AM UTC**: Consistency validation

No manual intervention needed!

## Troubleshooting

### Worker Not Running

```bash
# Check status
docker-compose -f docker-compose.prefect.yml ps

# Restart worker
docker-compose -f docker-compose.prefect.yml restart prefect-worker
```

### Rate Limit Errors

1. Check if NCBI API key is set in `.env`
2. Reduce `max_results_per_term` in deployment config
3. Increase delays in rate limiter config

### Can't Access UI

```bash
# Check if server is running
curl http://localhost:4200/api/health

# Restart server
make prefect-server-stop
make prefect-server-start
```

## Next Steps

1. **Customize Search Terms**
   - Edit `src/biomedical_graphrag/orchestration/deployments.py`
   - Redeploy with `make prefect-deploy`

2. **Adjust Schedules**
   - Modify cron expressions in `deployments.py`
   - Redeploy flows

3. **Set Up Alerts**
   - Configure in Prefect UI → Settings → Notifications
   - Add Slack/Email integration

4. **Production Deployment**
   - Switch to Prefect Cloud
   - Deploy on Kubernetes
   - See `docs/ORCHESTRATION.md` for details

## Common Commands

```bash
# Start/stop Prefect
make prefect-server-start
make prefect-server-stop

# Deploy flows
make prefect-deploy

# Run manually
make prefect-run-incremental
make prefect-run-rebuild

# View logs
make prefect-server-logs

# Test rate limiting
make prefect-test-rate-limit
```

## Architecture Overview

```
┌──────────────┐
│ Prefect UI   │  ← http://localhost:4200
└──────┬───────┘
       │
┌──────▼────────┐
│ Prefect Server│  ← Orchestrates workflows
└──────┬────────┘
       │
┌──────▼────────┐
│ Prefect Worker│  ← Executes tasks
└──────┬────────┘
       │
       ├─→ PubMed API (rate limited)
       ├─→ Gene API (rate limited)
       ├─→ OpenAI API (embeddings)
       ├─→ Neo4j (graph storage)
       └─→ Qdrant (vector storage)
```

## Getting Help

- Full docs: `docs/ORCHESTRATION.md`
- Main README: `README.md`
- Prefect docs: https://docs.prefect.io
- View logs: `make prefect-server-logs`

Happy orchestrating! 🚀
